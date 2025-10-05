"""Async adoption tracking and KPI monitoring for the MCP AI Agent."""

from __future__ import annotations

import asyncio
import inspect
import ast
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from datetime import datetime, timedelta

from .logging_utils import get_logger, LogComponent
from .metrics import metrics, MetricType

logger = get_logger("async_tracker", LogComponent.AGENT)


@dataclass
class FunctionInfo:
    """Information about a function definition."""
    name: str
    is_async: bool
    is_method: bool
    class_name: Optional[str] = None
    file_path: Optional[str] = None
    line_number: int = 0
    decorators: List[str] = field(default_factory=list)
    is_eligible_for_async: bool = True
    reason_not_eligible: Optional[str] = None


@dataclass
class AsyncAdoptionReport:
    """Report on async adoption progress."""
    timestamp: datetime
    total_functions: int
    async_functions: int
    sync_functions: int
    async_percentage: float
    eligible_functions: int
    eligible_async_functions: int
    eligible_async_percentage: float

    # Breakdown by category
    by_file: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_module: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_class: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # Trend data
    previous_percentage: Optional[float] = None
    trend_direction: Optional[str] = None  # "up", "down", "stable"

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_functions": self.total_functions,
            "async_functions": self.async_functions,
            "sync_functions": self.sync_functions,
            "async_percentage": self.async_percentage,
            "eligible_functions": self.eligible_functions,
            "eligible_async_functions": self.eligible_async_functions,
            "eligible_async_percentage": self.eligible_async_percentage,
            "by_file": self.by_file,
            "by_module": self.by_module,
            "by_class": self.by_class,
            "previous_percentage": self.previous_percentage,
            "trend_direction": self.trend_direction,
        }


class AsyncCodeAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze async function definitions."""

    def __init__(self):
        self.functions: List[FunctionInfo] = []
        self.current_class: Optional[str] = None
        self.current_file: Optional[str] = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions."""
        # Check if function is async
        is_async = isinstance(node, ast.AsyncFunctionDef) or any(
            isinstance(decorator, ast.Name) and decorator.id in ('async', 'asyncio')
            for decorator in node.decorator_list
        )

        # Check if function is eligible for async (not a CLI entry point, sync wrapper, etc.)
        is_eligible, reason = self._check_async_eligibility(node)

        function_info = FunctionInfo(
            name=node.name,
            is_async=is_async,
            is_method=self.current_class is not None,
            class_name=self.current_class,
            file_path=self.current_file,
            line_number=node.lineno,
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            is_eligible_for_async=is_eligible,
            reason_not_eligible=reason,
        )

        self.functions.append(function_info)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions."""
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def _check_async_eligibility(self, node: ast.FunctionDef) -> Tuple[bool, Optional[str]]:
        """Check if a function is eligible for async conversion."""
        # Skip private functions (starting with _)
        if node.name.startswith('_'):
            return False, "private_function"

        # Skip CLI entry points and main functions
        cli_indicators = ['main', 'cli', 'entry', 'run_sync', 'sync_wrapper']
        if any(indicator in node.name.lower() for indicator in cli_indicators):
            return False, "cli_entry_point"

        # Skip test functions
        if node.name.startswith('test_'):
            return False, "test_function"

        # Skip functions with sync-only decorators
        sync_decorators = ['staticmethod', 'classmethod', 'property']
        for decorator in node.decorator_list:
            decorator_name = self._get_decorator_name(decorator)
            if decorator_name in sync_decorators:
                return False, f"sync_decorator_{decorator_name}"

        # Skip very simple functions (likely getters/setters)
        if self._is_simple_function(node):
            return False, "simple_function"

        return True, None

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return "unknown"

    def _is_simple_function(self, node: ast.FunctionDef) -> bool:
        """Check if function is simple (likely not worth making async)."""
        # Simple getter/setter patterns
        if len(node.body) == 1:
            statement = node.body[0]
            if isinstance(statement, ast.Return):
                return True
            elif isinstance(statement, (ast.Assign, ast.AugAssign)):
                return True

        return False


class AsyncAdoptionTracker:
    """Tracks async adoption progress across the codebase."""

    def __init__(self, source_paths: Optional[List[Union[str, Path]]] = None):
        self.source_paths = source_paths or ["src"]
        self._cache: Optional[AsyncAdoptionReport] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes

    async def analyze_codebase(self, force_refresh: bool = False) -> AsyncAdoptionReport:
        """Analyze the codebase for async adoption metrics."""
        # Check cache
        if (not force_refresh and self._cache and self._cache_timestamp and
            datetime.now() - self._cache_timestamp < self._cache_ttl):
            return self._cache

        logger.info("Analyzing codebase for async adoption metrics", operation="analyze_codebase")

        all_functions = []
        file_reports = {}
        module_reports = {}
        class_reports = {}

        # Analyze each source path
        for source_path in self.source_paths:
            path_functions, path_reports = await self._analyze_path(Path(source_path))
            all_functions.extend(path_functions)

            # Merge reports
            for file_path, counts in path_reports.items():
                file_reports[file_path] = counts

            for module_name, counts in path_reports.items():
                if module_name not in module_reports:
                    module_reports[module_name] = {"async": 0, "sync": 0, "total": 0}
                module_reports[module_name]["async"] += counts.get("async", 0)
                module_reports[module_name]["sync"] += counts.get("sync", 0)
                module_reports[module_name]["total"] += counts.get("total", 0)

        # Calculate totals
        total_functions = len(all_functions)
        async_functions = sum(1 for f in all_functions if f.is_async)
        sync_functions = total_functions - async_functions

        # Calculate eligible functions
        eligible_functions = sum(1 for f in all_functions if f.is_eligible_for_async)
        eligible_async_functions = sum(
            1 for f in all_functions
            if f.is_async and f.is_eligible_for_async
        )

        # Calculate percentages
        async_percentage = (async_functions / total_functions * 100) if total_functions > 0 else 0
        eligible_async_percentage = (
            eligible_async_functions / eligible_functions * 100
        ) if eligible_functions > 0 else 0

        # Create report
        report = AsyncAdoptionReport(
            timestamp=datetime.now(),
            total_functions=total_functions,
            async_functions=async_functions,
            sync_functions=sync_functions,
            async_percentage=async_percentage,
            eligible_functions=eligible_functions,
            eligible_async_functions=eligible_async_functions,
            eligible_async_percentage=eligible_async_percentage,
            by_file=file_reports,
            by_module=module_reports,
            by_class=class_reports,
        )

        # Calculate trend if we have previous data
        if self._cache:
            report.previous_percentage = self._cache.eligible_async_percentage
            if report.eligible_async_percentage > self._cache.eligible_async_percentage:
                report.trend_direction = "up"
            elif report.eligible_async_percentage < self._cache.eligible_async_percentage:
                report.trend_direction = "down"
            else:
                report.trend_direction = "stable"

        # Update cache
        self._cache = report
        self._cache_timestamp = datetime.now()

        # Record metrics
        self._record_metrics(report)

        logger.info(
            f"Async adoption analysis complete: {eligible_async_percentage:.1f}% eligible functions are async",
            operation="analyze_codebase",
            extra_fields={
                "total_functions": total_functions,
                "async_functions": async_functions,
                "eligible_async_percentage": eligible_async_percentage,
                "trend": report.trend_direction,
            }
        )

        return report

    async def _analyze_path(self, path: Path) -> Tuple[List[FunctionInfo], Dict[str, Dict[str, int]]]:
        """Analyze a single path for async functions."""
        functions = []
        file_reports = {}

        if not path.exists():
            return functions, file_reports

        # Analyze Python files
        python_files = list(path.rglob("*.py"))
        for py_file in python_files:
            # Skip test files, __pycache__, etc.
            if self._should_skip_file(py_file):
                continue

            try:
                file_functions = self._analyze_file(py_file)
                functions.extend(file_functions)

                # Generate file report
                async_count = sum(1 for f in file_functions if f.is_async)
                sync_count = len(file_functions) - async_count
                file_reports[str(py_file)] = {
                    "async": async_count,
                    "sync": sync_count,
                    "total": len(file_functions),
                }

            except Exception as e:
                logger.warning(
                    f"Failed to analyze file {py_file}: {e}",
                    operation="analyze_file",
                    extra_fields={"file_path": str(py_file)},
                )

        return functions, file_reports

    def _analyze_file(self, file_path: Path) -> List[FunctionInfo]:
        """Analyze a single Python file for async functions."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return []

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return []

        analyzer = AsyncCodeAnalyzer()
        analyzer.current_file = str(file_path)
        analyzer.visit(tree)

        return analyzer.functions

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped in analysis."""
        # Skip test files
        if "test" in file_path.name.lower() or "test" in str(file_path):
            return True

        # Skip cache and build files
        if "__pycache__" in str(file_path) or ".pyc" in file_path.name:
            return True

        # Skip certain directories
        skip_dirs = {"__pycache__", ".git", ".pytest_cache", "node_modules", ".mypy_cache"}
        for part in file_path.parts:
            if part in skip_dirs:
                return True

        return False

    def _record_metrics(self, report: AsyncAdoptionReport) -> None:
        """Record async adoption metrics."""
        # Overall async percentage
        metrics.gauge("async_adoption_percentage", report.async_percentage)
        metrics.gauge("async_adoption_eligible_percentage", report.eligible_async_percentage)

        # Function counts
        metrics.gauge("async_functions_total", report.async_functions)
        metrics.gauge("sync_functions_total", report.sync_functions)
        metrics.gauge("eligible_functions_total", report.eligible_functions)

        # Trend tracking
        if report.trend_direction:
            trend_value = {"up": 1, "stable": 0, "down": -1}.get(report.trend_direction, 0)
            metrics.gauge("async_adoption_trend", trend_value)

    def get_functions_needing_async(self, limit: Optional[int] = None) -> List[FunctionInfo]:
        """Get list of functions that should be converted to async."""
        report = self.analyze_codebase()

        # Find sync functions that are eligible for async
        candidates = [
            f for f in []  # We'll need to store functions from analysis
            if not f.is_async and f.is_eligible_for_async
        ]

        if limit:
            candidates = candidates[:limit]

        return candidates

    def generate_migration_plan(self) -> Dict[str, Any]:
        """Generate a plan for async migration."""
        report = self.analyze_codebase()

        # Group functions by file for easier migration
        by_file = defaultdict(list)
        for func in []:  # We'll need to store functions from analysis
            if not func.is_async and func.is_eligible_for_async:
                by_file[func.file_path or "unknown"].append(func)

        # Sort files by number of functions needing conversion
        file_priority = [
            (file_path, len(functions))
            for file_path, functions in by_file.items()
        ]
        file_priority.sort(key=lambda x: x[1], reverse=True)

        return {
            "current_percentage": report.eligible_async_percentage,
            "target_percentage": 90.0,
            "functions_to_convert": sum(len(funcs) for funcs in by_file.values()),
            "priority_files": file_priority[:10],  # Top 10 files
            "estimated_effort": self._estimate_migration_effort(by_file),
        }

    def _estimate_migration_effort(self, by_file: Dict[str, List[FunctionInfo]]) -> str:
        """Estimate effort required for migration."""
        total_functions = sum(len(funcs) for funcs in by_file.values())

        if total_functions == 0:
            return "No migration needed"
        elif total_functions < 10:
            return "Low effort (1-2 days)"
        elif total_functions < 30:
            return "Medium effort (3-5 days)"
        else:
            return "High effort (1-2 weeks)"


# Global async tracker instance
async_tracker = AsyncAdoptionTracker()


async def track_async_adoption_kpi() -> None:
    """Track async adoption KPI metrics."""
    try:
        report = async_tracker.analyze_codebase()

        # Log key metrics
        logger.info(
            "Async adoption KPI update",
            operation="track_kpi",
            extra_fields={
                "async_percentage": report.async_percentage,
                "eligible_async_percentage": report.eligible_async_percentage,
                "total_functions": report.total_functions,
                "async_functions": report.async_functions,
                "trend": report.trend_direction,
            }
        )

        # Check if we've reached the 90% target
        if report.eligible_async_percentage >= 90.0:
            logger.info(
                "🎉 Async adoption target reached! 90%+ eligible functions are now async",
                operation="target_reached"
            )
        else:
            remaining = 90.0 - report.eligible_async_percentage
            logger.info(
            f"Async adoption progress: {report.eligible_async_percentage:.1f}% "
            f"({remaining:.1f}% remaining to reach 90% target)",
                operation="progress_update"
            )

    except Exception as e:
        logger.error(
            f"Failed to track async adoption KPI: {e}",
            operation="track_kpi"
        )


async def get_async_adoption_status() -> Dict[str, Any]:
    """Get current async adoption status."""
    report = await async_tracker.analyze_codebase()

    status = {
        "current_percentage": report.eligible_async_percentage,
        "target_percentage": 90.0,
        "is_target_reached": report.eligible_async_percentage >= 90.0,
        "total_functions": report.total_functions,
        "async_functions": report.async_functions,
        "functions_needing_async": report.eligible_functions - report.eligible_async_functions,
        "trend": report.trend_direction,
    }

    # Add file breakdown
    status["files_by_async_percentage"] = []
    for file_path, counts in report.by_file.items():
        if counts["total"] > 0:
            async_pct = (counts["async"] / counts["total"]) * 100
            status["files_by_async_percentage"].append({
                "file": file_path,
                "async_percentage": async_pct,
                "total_functions": counts["total"],
                "async_functions": counts["async"],
            })

    # Sort by async percentage (ascending) to show files needing most work first
    status["files_by_async_percentage"].sort(key=lambda x: x["async_percentage"])

    return status


# CLI command for checking async adoption
async def print_async_adoption_report(force_refresh: bool = False) -> None:
    """Print a human-readable async adoption report."""
    report = await async_tracker.analyze_codebase(force_refresh=force_refresh)

    print("🚀 Async Adoption Report")
    print("=" * 50)
    print(f"Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    print("📊 Overall Statistics:")
    print(f"  Total functions: {report.total_functions}")
    print(f"  Async functions: {report.async_functions}")
    print(f"  Sync functions: {report.sync_functions}")
    print(f"  Overall async percentage: {report.async_percentage:.1f}%")
    print()

    print("🎯 Eligible Functions (excluding CLI, tests, simple functions):")
    print(f"  Eligible functions: {report.eligible_functions}")
    print(f"  Eligible async functions: {report.eligible_async_functions}")
    print(f"  Eligible async percentage: {report.eligible_async_percentage:.1f}%")
    print()

    if report.trend_direction:
        trend_symbol = {"up": "📈", "down": "📉", "stable": "➡️"}.get(report.trend_direction, "❓")
        print(f"📈 Trend: {trend_symbol} {report.trend_direction.title()}")
        if report.previous_percentage is not None:
            diff = report.eligible_async_percentage - report.previous_percentage
            print(f"  Change since last check: {diff:+.1f}%")
        print()

    # Target status
    if report.eligible_async_percentage >= 90.0:
        print("✅ TARGET REACHED: 90%+ eligible functions are async!")
    else:
        remaining = 90.0 - report.eligible_async_percentage
        print(f"🎯 Progress to 90% target: {remaining:.1f}% remaining")

    print()

    # File breakdown (top 10 files needing work)
    if report.by_file:
        print("📁 Files by async percentage (lowest first):")
        sorted_files = sorted(
            report.by_file.items(),
            key=lambda x: (x[1]["async"] / x[1]["total"] * 100) if x[1]["total"] > 0 else 0
        )

        for file_path, counts in sorted_files[:10]:
            if counts["total"] > 0:
                async_pct = (counts["async"] / counts["total"]) * 100
                print(f"  {async_pct:5.1f}% - {Path(file_path).name} ({counts['async']}/{counts['total']})")

        print()


if __name__ == "__main__":
    print_async_adoption_report(force_refresh=True)
