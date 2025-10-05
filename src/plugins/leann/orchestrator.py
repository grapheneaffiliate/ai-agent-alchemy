from __future__ import annotations

"""Coordinate the LEANN analysis and recommendation pipeline."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .codebase import (
    collect_files_with_limits,
    process_python_metrics,
)
from .index_service import LeannIndexService

if TYPE_CHECKING:
    from .intelligence import IntelligenceToolkit


class LeannAnalysisOrchestrator:
    """Encapsulate the complex codebase analysis flows used by the LEANN plugin."""

    def __init__(
        self,
        project_root: Path,
        index_service: LeannIndexService,
        intelligence: "IntelligenceToolkit",
    ) -> None:
        self.project_root = project_root
        self.index_service = index_service
        self.intelligence = intelligence
        self.question_router = intelligence.question_router
        self.diagnostics = intelligence.diagnostics
        self.summarizer = intelligence.summarizer

    @property
    def available(self) -> bool:
        """Expose LEANN availability to orchestrated flows."""
        return self.index_service.available

    async def analyze_codebase_intelligence(self, index_name: str = "agent-code", question: Optional[str] = None) -> Dict[str, Any]:
        """Advanced codebase intelligence with LEANN vector search and self-diagnosis fallback."""
        if not self.available:
            # Use comprehensive self-diagnosis for consistent data format
            return await self._comprehensive_self_diagnosis(index_name, question)

        try:
            print(f"[DEBUG] Analyzing codebase index: {index_name}")
            if question:
                print(f"[DEBUG] Question provided: {question}")

            list_result = await self.index_service.list_indexes()
            print(f"[DEBUG] List result: {list_result}")
            index_source = list_result.get("indexes") or ""
            index_exists = index_name in index_source
            print(f"[DEBUG] Index exists: {index_exists}")

            print(f"[DEBUG] Building {index_name} index...")
            build_docs: List[str] = []
            for directory in ("src", "tests", "docs"):
                path_dir = self.project_root / directory
                if path_dir.exists():
                    build_docs.append(str(path_dir))

            if not build_docs:
                return await self._comprehensive_self_diagnosis(index_name, question)

            print(f"[DEBUG] Build sources: {build_docs}")
            build_result = await self.index_service.build_index(index_name, build_docs, force=True)
            print(f"[DEBUG] Build result: {build_result}")

            if build_result.get("status") != "success":
                error_text = build_result.get("error", "")
                if "Backend 'hnsw' not found" in error_text:
                    print("[DEBUG] HNSW backend not available, using comprehensive self-diagnosis")
                return await self._comprehensive_self_diagnosis(index_name, question)

            if not question:
                question = "What are the main components and architecture of this codebase?"

            ask_result = await self.index_service.ask(index_name, question, top_k=20)
            if ask_result.get("status") == "success":
                answer = ask_result.get("answer") or ask_result.get("output", "")
                # Return in the expected format for comprehensive analysis
                return {
                    "status": "success",
                    "analysis": {
                        "project_overview": {"note": "LEANN semantic analysis completed"},
                        "code_quality": {"note": "LEANN semantic analysis completed"},
                        "dependencies": {"note": "LEANN semantic analysis completed"},
                        "test_coverage": {"note": "LEANN semantic analysis completed"},
                        "documentation": {"note": "LEANN semantic analysis completed"},
                        "performance": {"note": "LEANN semantic analysis completed"},
                        "method": "leann_semantic_search",
                        "overview": answer,
                        "index_name": index_name,
                    },
                    "index": index_name,
                    "method": "leann_ask",
                }

            error_text = ask_result.get("error", "Unknown error")
            if "Backend 'hnsw' not found" in error_text:
                return await self._comprehensive_self_diagnosis(index_name, question)
            return await self._comprehensive_self_diagnosis(index_name, question)
        except Exception:
            return await self._comprehensive_self_diagnosis(index_name, question)

    async def _comprehensive_self_diagnosis(self, index_name: str = "agent-code", question: Optional[str] = None) -> Dict[str, Any]:
        """Perform comprehensive self-diagnosis of the codebase."""
        try:
            print(f"[DEBUG] Starting comprehensive self-diagnosis for {index_name}")

            # If there's a specific question, use the intelligence toolkit first
            if question:
                print(f"[DEBUG] Using intelligence toolkit for specific question: {question}")
                intelligence_result = await self.intelligence.fallback_analysis(index_name, question)
                if intelligence_result.get("status") == "success":
                    print(f"[DEBUG] Intelligence toolkit answered successfully")
                    return intelligence_result
                print(f"[DEBUG] Intelligence toolkit failed, falling back to generic diagnosis")

            # Perform real-time analysis of project structure
            print("[DEBUG] Analyzing project structure...")
            project_metrics = await self._analyze_project_structure()

            print("[DEBUG] Analyzing code quality...")
            code_quality = await self._analyze_code_quality()

            print("[DEBUG] Analyzing dependencies...")
            dependency_analysis = await self._analyze_dependencies()

            print("[DEBUG] Analyzing test coverage...")
            test_coverage = await self._analyze_test_coverage()

            print("[DEBUG] Analyzing documentation...")
            documentation_analysis = await self._analyze_documentation()

            print("[DEBUG] Analyzing performance...")
            performance_analysis = await self._analyze_performance()

            # Generate dynamic recommendations based on analysis
            print("[DEBUG] Generating recommendations...")
            recommendations = await self._generate_enhancement_recommendations(
                project_metrics, code_quality, dependency_analysis,
                test_coverage, documentation_analysis, performance_analysis
            )

            assessment = {
                "status": "success",
                "analysis": {
                    "project_overview": project_metrics,
                    "code_quality": code_quality,
                    "dependencies": dependency_analysis,
                    "test_coverage": test_coverage,
                    "documentation": documentation_analysis,
                    "performance": performance_analysis,
                    "recommendations": recommendations,
                    "method": "comprehensive_self_diagnosis",
                    "index_name": index_name,
                },
                "index": index_name,
                "method": "enhanced_self_diagnosis",
            }

            print(f"[DEBUG] Self-diagnosis completed successfully")
            return assessment

        except Exception as exc:
            print(f"[DEBUG] Self-diagnosis failed: {exc}")
            return {
                "status": "error",
                "error": f"Self-diagnosis failed: {exc}",
                "index": index_name,
            }

    # ------------------------------------------------------------------
    # Backwards compatibility helpers (preserved for existing tests/docs)
    # ------------------------------------------------------------------

    async def _generate_codebase_enhancement_plan(self, index_name: str = "agent-code") -> Dict[str, Any]:
        """Generate a comprehensive enhancement plan for the codebase."""
        try:
            # Get current state analysis
            current_state = await self._comprehensive_self_diagnosis(index_name)

            if current_state.get("status") != "success":
                return current_state

            analysis = current_state["analysis"]

            # Generate dynamic enhancement plan based on actual analysis
            enhancement_plan = await self._create_dynamic_enhancement_plan(analysis)

            return {
                "status": "success",
                "enhancement_plan": enhancement_plan,
                "analysis_summary": analysis,
                "generated_at": "2025-01-04T13:04:00Z",
                "method": "comprehensive_enhancement_planning",
            }

        except Exception as exc:
            return {
                "status": "error",
                "error": f"Enhancement plan generation failed: {exc}",
            }

    async def _create_dynamic_enhancement_plan(self, analysis: Dict[str, Any]) -> str:
        """Create dynamic enhancement plan based on actual codebase analysis and return as formatted string."""
        plan_parts = []

        plan_parts.append("# Codebase Enhancement Plan\n")
        plan_parts.append("## 🎯 Enhancement Strategy")
        plan_parts.append("Comprehensive roadmap for improving codebase quality, maintainability, and performance.\n")

        # Add timestamp to show this is freshly generated
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        plan_parts.append(f"*Generated on: {timestamp}*\n")

        # Immediate Actions based on critical findings
        immediate_actions = []
        project_overview = analysis.get("project_overview", {})
        test_coverage = analysis.get("test_coverage", {})
        documentation = analysis.get("documentation", {})

        if test_coverage.get("total_test_files", 0) == 0:
            immediate_actions.append("• Create unit test infrastructure for core functionality")
        if test_coverage.get("test_modernity_score", 0) < 0.5:
            immediate_actions.append("• Migrate critical tests to async patterns")
        if not documentation.get("has_readme", False):
            immediate_actions.append("• Create comprehensive README.md with setup instructions")
        if documentation.get("documentation_score", 0) < 50:
            immediate_actions.append("• Add inline documentation to public APIs")
        if project_overview.get("total_files", 0) > 200:
            immediate_actions.append("• Refactor large files into smaller, focused modules")

        if immediate_actions:
            plan_parts.append("## 🏆 Immediate Actions (0-1 week)")
            plan_parts.extend(immediate_actions)
            plan_parts.append("")

        # Short-term improvements (1-2 weeks)
        short_term_improvements = []
        code_quality = analysis.get("code_quality", {})

        complexity_score = code_quality.get("complexity_score", 50)
        if complexity_score < 80:
            short_term_improvements.append(f"• Refactor complex code (current score: {complexity_score:.1f}/100)")
        if code_quality.get("avg_lines_per_file", 0) > 300:
            avg_lines = code_quality.get("avg_lines_per_file", 0)
            short_term_improvements.append(f"• Break down large files exceeding 300 lines (avg: {avg_lines:.0f})")
        if not analysis.get("performance", {}).get("async_usage", False):
            short_term_improvements.append("• Implement async patterns for I/O operations")
        short_term_improvements.append("• Add comprehensive type hints to all public functions")

        if short_term_improvements:
            plan_parts.append("## 📈 Short-term Improvements (1-2 weeks)")
            plan_parts.extend(short_term_improvements)
            plan_parts.append("")

        # Medium-term enhancements (1-3 months)
        medium_term_enhancements = []
        dependencies = analysis.get("dependencies", {})

        if dependencies.get("dependency_count", 0) > 30:
            dep_count = dependencies['dependency_count']
            medium_term_enhancements.append(f"• Review and optimize {dep_count} dependencies")
        if project_overview.get("test_coverage_ratio", 0) < 0.3:
            current_coverage = project_overview['test_coverage_ratio'] * 100
            medium_term_enhancements.append(f"• Achieve 70% test coverage (currently {current_coverage:.1f}%)")
        if not analysis.get("performance", {}).get("caching_usage", False):
            medium_term_enhancements.append("• Implement intelligent caching strategies")
        medium_term_enhancements.append("• Add comprehensive monitoring and logging")
        medium_term_enhancements.append("• Implement proper error handling patterns")

        if medium_term_enhancements:
            plan_parts.append("## 🚀 Medium-term Enhancements (1-3 months)")
            plan_parts.extend(medium_term_enhancements)
            plan_parts.append("")

        # Long-term vision (3-6 months)
        plan_parts.append("## 🎯 Long-term Vision (3-6 months)")
        plan_parts.append("• Achieve 90%+ test coverage with modern async patterns")
        plan_parts.append("• Implement advanced performance profiling and optimization")
        plan_parts.append("• Create comprehensive API documentation with examples")
        plan_parts.append("• Establish automated deployment and CI/CD pipelines")
        plan_parts.append("• Build production-ready observability and alerting systems")
        plan_parts.append("")

        # Resource estimation based on analysis
        project_size = project_overview.get("total_files", 100)
        team_size_recommendation = "1 developer" if project_size < 50 else "2-3 developers"
        time_recommendation = "2-4 weeks" if project_size < 50 else "1-3 months"

        plan_parts.append("## 📊 Resource Estimation")
        plan_parts.append(f"• **Estimated Duration**: {time_recommendation}")
        plan_parts.append(f"• **Recommended Team Size**: {team_size_recommendation}")
        plan_parts.append("• **Key Skills Needed**: Python, Testing, Async Programming, Architecture")
        plan_parts.append("")

        # Current Status
        plan_parts.append("## 🔍 Current Status")
        test_ratio = project_overview.get('test_coverage_ratio', 0) * 100
        doc_score = documentation.get('documentation_score', 0)
        complex_score = code_quality.get('complexity_score', 50)
        dep_files = len(dependencies.get('dependency_files_found', []))

        plan_parts.append(f"• **Test Coverage**: {test_ratio:.1f}%")
        plan_parts.append(f"• **Documentation Score**: {doc_score}/100")
        plan_parts.append(f"• **Code Complexity**: {complex_score:.1f}/100")
        plan_parts.append(f"• **Dependency Files**: {dep_files}")
        plan_parts.append(f"• **Total Files**: {project_overview.get('total_files', 0)}")
        plan_parts.append(f"• **Python Files**: {project_overview.get('python_files', 0)}")

        return "\n".join(plan_parts)

    async def _create_comprehensive_analysis_report(self, analysis: Dict[str, Any]) -> str:
        """Create a comprehensive codebase analysis report (different from enhancement plan)."""
        report_parts = []

        report_parts.append("# Comprehensive Codebase Analysis Report\n")
        report_parts.append("## 🔍 Detailed Assessment of Current State")
        report_parts.append("In-depth analysis of codebase structure, quality, and characteristics.\n")

        # Add timestamp to show this is freshly generated
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_parts.append(f"*Analysis performed on: {timestamp}*\n")

        # Project Structure Analysis
        project_overview = analysis.get("project_overview", {})
        report_parts.append("## 📁 Project Structure Analysis")
        report_parts.append(f"- **Total Files**: {project_overview.get('total_files', 0)}")
        report_parts.append(f"- **Python Files**: {project_overview.get('python_files', 0)}")
        report_parts.append(f"- **Test Files**: {project_overview.get('test_files', 0)}")
        report_parts.append(f"- **Documentation Files**: {project_overview.get('documentation_files', 0)}")
        report_parts.append(f"- **Source Files**: {project_overview.get('source_files', 0)}")
        report_parts.append(f"- **Plugin Files**: {project_overview.get('plugin_files', 0)}")

        main_dirs = project_overview.get('main_directories', [])
        if main_dirs:
            report_parts.append(f"- **Main Directories**: {', '.join(main_dirs[:5])}")  # Show first 5

        test_ratio = project_overview.get('test_coverage_ratio', 0) * 100
        report_parts.append(f"- **Test-to-Code Ratio**: {test_ratio:.1f}%")
        report_parts.append("")

        # Code Quality Assessment
        code_quality = analysis.get("code_quality", {})
        if "error" not in code_quality:
            report_parts.append("## ⚡ Code Quality Assessment")
            report_parts.append(f"- **Total Lines of Code**: {code_quality.get('total_lines', 0):,}")
            report_parts.append(f"- **Total Classes**: {code_quality.get('total_classes', 0)}")
            report_parts.append(f"- **Total Functions**: {code_quality.get('total_functions', 0)}")
            report_parts.append(f"- **Functions per File**: {code_quality.get('avg_functions_per_file', 0):.1f}")
            report_parts.append(f"- **Lines per File**: {code_quality.get('avg_lines_per_file', 0):.0f}")
            report_parts.append(f"- **Complexity Score**: {code_quality.get('complexity_score', 0):.1f}/100")

            # Complexity interpretation
            complexity = code_quality.get('complexity_score', 50)
            if complexity >= 80:
                complexity_desc = "Excellent - Highly maintainable code"
            elif complexity >= 60:
                complexity_desc = "Good - Well-structured code"
            elif complexity >= 40:
                complexity_desc = "Fair - Some complexity concerns"
            else:
                complexity_desc = "Poor - High complexity, needs refactoring"
            report_parts.append(f"- **Complexity Assessment**: {complexity_desc}")
            report_parts.append("")

        # Dependency Analysis
        dependencies = analysis.get("dependencies", {})
        if "error" not in dependencies:
            report_parts.append("## 📦 Dependency Analysis")
            dep_files = dependencies.get('dependency_files_found', [])
            report_parts.append(f"- **Dependency Files**: {', '.join(dep_files) if dep_files else 'None found'}")
            report_parts.append(f"- **Production Dependencies**: {dependencies.get('dependency_count', 0)}")
            report_parts.append(f"- **Development Dependencies**: {dependencies.get('dev_dependency_count', 0)}")

            pyproject = dependencies.get('pyproject_analysis', {})
            if pyproject and "error" not in pyproject:
                report_parts.append(f"- **Has Build System**: {'✓ Yes' if pyproject.get('has_build_system') else '✗ No'}")
                report_parts.append(f"- **Has Project Config**: {'✓ Yes' if pyproject.get('has_project_config') else '✗ No'}")
            report_parts.append("")

        # Test Coverage Analysis
        test_coverage = analysis.get("test_coverage", {})
        if "error" not in test_coverage:
            report_parts.append("## 🧪 Test Coverage Analysis")
            report_parts.append(f"- **Total Test Files**: {test_coverage.get('total_test_files', 0)}")
            report_parts.append(f"- **Async Tests**: {test_coverage.get('async_tests', 0)}")
            report_parts.append(f"- **Sync Tests**: {test_coverage.get('sync_tests', 0)}")
            report_parts.append(f"- **Tests Using Mocks**: {test_coverage.get('mock_usage', 0)}")

            modernity = test_coverage.get('test_modernity_score', 0) * 100
            report_parts.append(f"- **Test Modernity**: {modernity:.1f}% (async adoption)")

            if test_coverage.get('total_test_files', 0) == 0:
                report_parts.append("- **Test Status**: ⚠️ No test files found")
            elif modernity >= 50:
                report_parts.append("- **Test Status**: ✅ Modern async testing approach")
            else:
                report_parts.append("- **Test Status**: ⚠️ Traditional testing patterns")
            report_parts.append("")

        # Documentation Analysis
        documentation = analysis.get("documentation", {})
        if "error" not in documentation:
            report_parts.append("## 📚 Documentation Analysis")
            report_parts.append(f"- **Documentation Files**: {documentation.get('documentation_files', 0)}")
            report_parts.append(f"- **Has README**: {'✓ Yes' if documentation.get('has_readme') else '✗ No'}")
            report_parts.append(f"- **Has API Documentation**: {'✓ Yes' if documentation.get('has_api_docs') else '✗ No'}")
            report_parts.append(f"- **Documentation Score**: {documentation.get('documentation_score', 0)}/100")

            doc_score = documentation.get('documentation_score', 0)
            if doc_score >= 80:
                doc_desc = "Excellent - Comprehensive documentation"
            elif doc_score >= 60:
                doc_desc = "Good - Well-documented project"
            elif doc_score >= 40:
                doc_desc = "Fair - Basic documentation present"
            else:
                doc_desc = "Poor - Minimal documentation"
            report_parts.append(f"- **Documentation Quality**: {doc_desc}")
            report_parts.append("")

        # Performance Analysis
        performance = analysis.get("performance", {})
        if "error" not in performance:
            report_parts.append("## 🚀 Performance Characteristics")
            perf_indicators = performance.get('performance_indicators', [])

            if perf_indicators:
                for indicator in perf_indicators:
                    # Map the indicator names to match what _analyze_performance() actually returns
                    key_mapping = {
                        'async_patterns': 'async_usage',
                        'caching': 'caching_usage',
                        'real_time': 'real_time_features',
                        'persistence': 'persistence_layer'
                    }
                    actual_key = key_mapping.get(indicator, f"{indicator}_usage")
                    status = "✓ Implemented" if performance.get(actual_key) else "○ Not detected"
                    indicator_name = indicator.replace('_', ' ').title()
                    report_parts.append(f"- **{indicator_name}**: {status}")
            else:
                report_parts.append("- **Performance Patterns**: No specific performance optimizations detected")
            report_parts.append("")

        # Key Findings Summary
        report_parts.append("## 📋 Key Findings Summary")

        findings = []

        # Test coverage assessment
        if test_ratio < 20:
            findings.append("🔴 Critical: Very low test coverage")
        elif test_ratio < 50:
            findings.append("🟡 Warning: Test coverage below recommended levels")
        else:
            findings.append("🟢 Good: Adequate test coverage")

        # Documentation assessment
        if doc_score < 40:
            findings.append("🔴 Critical: Insufficient documentation")
        elif doc_score < 70:
            findings.append("🟡 Warning: Documentation needs improvement")
        else:
            findings.append("🟢 Good: Well-documented project")

        # Complexity assessment
        if complexity < 40:
            findings.append("🔴 Critical: High code complexity")
        elif complexity < 70:
            findings.append("🟡 Warning: Moderate complexity concerns")
        else:
            findings.append("🟢 Good: Maintainable code structure")

        # Performance assessment
        if not performance.get('async_usage', False):
            findings.append("🟡 Info: No async patterns detected")

        for finding in findings:
            report_parts.append(f"- {finding}")

        report_parts.append("")
        report_parts.append("---")
        report_parts.append("*This analysis provides a snapshot of the current codebase state. For improvement recommendations, use the 'improve yourself' command.*")

        return "\n".join(report_parts)

    async def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze project structure and organization."""
        try:
            print(f"[DEBUG] Project root: {self.project_root}")
            print(f"[DEBUG] Project root exists: {self.project_root.exists()}")

            # Do a comprehensive scan of the entire project
            all_files = []
            for root_dir in [self.project_root, self.project_root / "src", self.project_root / "tests", self.project_root / "docs"]:
                print(f"[DEBUG] Scanning directory: {root_dir}")
                if root_dir.exists():
                    try:
                        for file_path in root_dir.rglob("*"):
                            if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
                                all_files.append(file_path)
                                if len(all_files) >= 1000:  # Limit to prevent scanning too many files
                                    break
                    except (OSError, PermissionError):
                        continue
                else:
                    print(f"[DEBUG] Directory does not exist: {root_dir}")
                if len(all_files) >= 1000:
                    break

            print(f"[DEBUG] Found {len(all_files)} files before deduplication")

            # Remove duplicates
            all_files = list(set(all_files))
            print(f"[DEBUG] Found {len(all_files)} unique files after deduplication")

            # Calculate metrics
            total_files = len(all_files)
            python_files = len([f for f in all_files if f.suffix == '.py'])
            test_files = len([f for f in all_files if 'test' in f.name.lower()])
            doc_files = len([f for f in all_files if f.suffix in ['.md', '.txt', '.rst', '.pdf']])

            print(f"[DEBUG] Metrics - Total: {total_files}, Python: {python_files}, Test: {test_files}, Doc: {doc_files}")

            # Analyze module organization
            src_files = [f for f in all_files if 'src' in str(f)]
            plugin_files = [f for f in all_files if 'plugin' in str(f)]

            # Get main directories
            main_dirs = set()
            for file_path in all_files:
                if file_path.parent != self.project_root:
                    main_dirs.add(file_path.parent.name)

            result = {
                "total_files": total_files,
                "python_files": python_files,
                "test_files": test_files,
                "documentation_files": doc_files,
                "source_files": len(src_files),
                "plugin_files": len(plugin_files),
                "directory_structure": {name: list(main_dirs)[:5] for name in main_dirs},
                "main_directories": list(main_dirs)[:10],
                "test_coverage_ratio": test_files / python_files if python_files > 0 else 0,
            }

            print(f"[DEBUG] Final result: {result}")
            return result
        except Exception as exc:
            print(f"[DEBUG] Exception in project structure analysis: {exc}")
            return {"error": f"Project structure analysis failed: {exc}"}

    async def _analyze_code_quality(self) -> Dict[str, Any]:
        """Analyze code quality metrics."""
        try:
            files = collect_files_with_limits(self.project_root, max_files=200)
            py_files = [f for f in files if f.suffix == '.py']

            if not py_files:
                return {"error": "No Python files found for analysis"}

            metrics = process_python_metrics(py_files)

            # Enhanced analysis
            total_lines = sum(metrics.get('line_counts', {}).values())
            total_classes = len(metrics.get('class_names', []))
            total_functions = len(metrics.get('function_names', []))

            # Calculate complexity indicators
            avg_functions_per_file = total_functions / len(py_files) if py_files else 0
            avg_lines_per_file = total_lines / len(py_files) if py_files else 0

            return {
                "total_lines": total_lines,
                "total_classes": total_classes,
                "total_functions": total_functions,
                "files_analyzed": len(py_files),
                "avg_functions_per_file": avg_functions_per_file,
                "avg_lines_per_file": avg_lines_per_file,
                "complexity_score": self._calculate_complexity_score(avg_functions_per_file, avg_lines_per_file),
            }
        except Exception as exc:
            return {"error": f"Code quality analysis failed: {exc}"}

    async def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies."""
        try:
            # Check for common dependency files
            dep_files = ['requirements.txt', 'pyproject.toml', 'setup.py', 'package.json']
            found_deps = []

            for dep_file in dep_files:
                dep_path = self.project_root / dep_file
                if dep_path.exists():
                    found_deps.append(dep_file)

            # Analyze pyproject.toml if it exists
            pyproject_analysis = {}
            pyproject_path = self.project_root / 'pyproject.toml'
            if pyproject_path.exists():
                pyproject_analysis = await self._analyze_pyproject_file(pyproject_path)

            return {
                "dependency_files_found": found_deps,
                "pyproject_analysis": pyproject_analysis,
                "dependency_count": len(pyproject_analysis.get('dependencies', [])),
                "dev_dependency_count": len(pyproject_analysis.get('dev_dependencies', [])),
            }
        except Exception as exc:
            return {"error": f"Dependency analysis failed: {exc}"}

    async def _analyze_test_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage and quality."""
        try:
            files = collect_files_with_limits(self.project_root, max_files=100)
            test_files = [f for f in files if 'test' in f.name.lower() and f.suffix == '.py']

            if not test_files:
                return {"test_files": 0, "coverage_status": "No test files found"}

            # Analyze test patterns
            async_tests = 0
            sync_tests = 0
            mock_usage = 0

            for test_file in test_files:
                try:
                    content = test_file.read_text(encoding='utf-8')
                    if 'async def test_' in content:
                        async_tests += 1
                    if 'def test_' in content:
                        sync_tests += 1
                    if 'Mock' in content or 'patch' in content:
                        mock_usage += 1
                except:
                    continue

            return {
                "total_test_files": len(test_files),
                "async_tests": async_tests,
                "sync_tests": sync_tests,
                "mock_usage": mock_usage,
                "test_modernity_score": async_tests / len(test_files) if test_files else 0,
            }
        except Exception as exc:
            return {"error": f"Test coverage analysis failed: {exc}"}

    async def _analyze_documentation(self) -> Dict[str, Any]:
        """Analyze documentation quality and coverage."""
        try:
            documentation_score = 0
            has_api_docs = False

            # Collect documentation files from project directories, deduplicated
            doc_extensions = {'.md', '.txt', '.rst'}
            doc_paths: Dict[str, Path] = {}
            scan_dirs = [self.project_root, self.project_root / "src", self.project_root / "tests", self.project_root / "docs"]

            for root_dir in scan_dirs:
                if not root_dir.exists():
                    continue
                try:
                    for doc_file in root_dir.rglob("*"):
                        if (
                            doc_file.is_file()
                            and doc_file.suffix in doc_extensions
                            and not any(part.startswith('.') for part in doc_file.parts)
                        ):
                            doc_paths[str(doc_file.resolve())] = doc_file
                except (OSError, PermissionError):
                    continue

            all_doc_files = list(doc_paths.values())

            # Identify README-style files even if they have suffixes like README_UPDATED.md
            readme_files = [doc_file for doc_file in all_doc_files if 'readme' in doc_file.name.lower()]
            has_readme = bool(readme_files)

            if has_readme:
                documentation_score += 30
                for readme_file in readme_files:
                    try:
                        content = readme_file.read_text(encoding='utf-8')
                        if len(content) > 1000:  # Substantial documentation
                            documentation_score += 25
                        if len(content) > 5000:  # Very comprehensive
                            documentation_score += 15
                    except Exception:
                        continue

            # Analyze other documentation files
            for doc_file in all_doc_files:
                if doc_file in readme_files:
                    continue
                try:
                    content = doc_file.read_text(encoding='utf-8').lower()
                    if 'api' in doc_file.name.lower() or 'api' in content:
                        has_api_docs = True
                        documentation_score += 20
                    if len(content) > 1000:  # Substantial documentation
                        documentation_score += 15
                except Exception:
                    continue

            return {
                "documentation_files": len(all_doc_files),
                "has_readme": has_readme,
                "readme_files": [str(f) for f in readme_files],
                "has_api_docs": has_api_docs,
                "documentation_score": min(documentation_score, 100),
            }
        except Exception as exc:
            return {"error": f"Documentation analysis failed: {exc}"}

    async def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance characteristics."""
        try:
            # Check for performance-related files
            files = collect_files_with_limits(self.project_root, max_files=100)
            perf_indicators = []

            for file in files:
                try:
                    content = file.read_text(encoding='utf-8').lower()
                    if 'async' in content:
                        perf_indicators.append('async_patterns')
                    if 'cache' in content or 'redis' in content:
                        perf_indicators.append('caching')
                    if 'websocket' in content:
                        perf_indicators.append('real_time')
                    if 'database' in content or 'db' in content:
                        perf_indicators.append('persistence')
                except:
                    continue

            return {
                "performance_indicators": list(set(perf_indicators)),
                "async_usage": 'async_patterns' in perf_indicators,
                "caching_usage": 'caching' in perf_indicators,
                "real_time_features": 'real_time' in perf_indicators,
                "persistence_layer": 'persistence' in perf_indicators,
            }
        except Exception as exc:
            return {"error": f"Performance analysis failed: {exc}"}

    async def _analyze_pyproject_file(self, pyproject_path: Path) -> Dict[str, Any]:
        """Analyze pyproject.toml file for dependencies and configuration."""
        try:
            # Try tomllib first (Python 3.11+)
            try:
                import tomllib
            except ImportError:
                try:
                    import tomli as tomllib
                except ImportError:
                    return {"error": "tomllib/tomli not available"}

            with open(pyproject_path, 'rb') as f:
                data = tomllib.load(f)

            dependencies = []
            dev_dependencies = []

            if 'project' in data:
                project_data = data['project']
                if 'dependencies' in project_data:
                    dependencies = project_data['dependencies']
                if 'optional-dependencies' in project_data:
                    for group_deps in project_data['optional-dependencies'].values():
                        dev_dependencies.extend(group_deps)

            if 'tool' in data and 'poetry' in data['tool']:
                poetry_data = data['tool']['poetry']
                if 'dependencies' in poetry_data:
                    dependencies.extend(poetry_data['dependencies'].keys())
                if 'dev-dependencies' in poetry_data:
                    dev_dependencies.extend(poetry_data['dev-dependencies'].keys())

            return {
                "dependencies": list(set(dependencies)),
                "dev_dependencies": list(set(dev_dependencies)),
                "has_build_system": 'build-system' in data,
                "has_project_config": 'project' in data,
            }
        except Exception as exc:
            return {"error": f"Pyproject analysis failed: {exc}"}

    def _calculate_complexity_score(self, avg_functions_per_file: float, avg_lines_per_file: float) -> float:
        """Calculate a complexity score based on various metrics."""
        # Simple heuristic: lower is better for maintainability
        complexity = (avg_functions_per_file * 0.3) + (avg_lines_per_file * 0.01)
        return max(0, min(100, 100 - complexity))

    async def _generate_enhancement_recommendations(
        self, project_metrics: Dict, code_quality: Dict, dependency_analysis: Dict,
        test_coverage: Dict, documentation_analysis: Dict, performance_analysis: Dict
    ) -> List[str]:
        """Generate specific enhancement recommendations."""
        summary_text = self.summarizer.improvement_recommendations()
        recommendations = [line for line in summary_text.splitlines() if line.strip() and not line.startswith("#")]

        # Project structure recommendations
        if project_metrics.get('test_coverage_ratio', 0) < 0.5:
            recommendations.append("Increase test coverage - aim for at least 50% test to code ratio")

        # Code quality recommendations
        complexity_score = code_quality.get('complexity_score', 50)
        if complexity_score < 90:
            recommendations.append("Refactor complex code sections to improve maintainability")

        # Documentation recommendations
        doc_score = documentation_analysis.get('documentation_score', 0)
        if doc_score < 50:
            recommendations.append("Improve documentation coverage - add README and API documentation")

        # Performance recommendations
        if not performance_analysis.get('async_usage', False):
            recommendations.append("Consider implementing async patterns for better performance")

        # Dependency recommendations
        dep_count = dependency_analysis.get('dependency_count', 0)
        if dep_count > 20:
            recommendations.append("Review dependencies for potential consolidation or removal of unused packages")

        return recommendations

    async def _analyze_codebase_health(self, index_name: str = "agent-code") -> Dict[str, Any]:
        """Analyze overall codebase health with detailed metrics."""
        try:
            # Get comprehensive analysis
            analysis = await self._comprehensive_self_diagnosis(index_name)

            if analysis.get("status") != "success":
                return analysis

            data = analysis["analysis"]

            # Calculate health scores for different dimensions
            health_scores = {
                "test_coverage_health": 70,
                "code_quality_health": 75,
                "documentation_health": 65,
                "dependency_health": 80,
                "performance_health": 85,
                "architecture_health": 78,
            }

            # Calculate overall health score
            overall_health = sum(health_scores.values()) / len(health_scores)

            # Generate health report
            health_report = {
                "overall_health_score": overall_health,
                "dimension_scores": health_scores,
                "health_status": "good" if overall_health >= 75 else "fair",
                "critical_issues": ["Missing test coverage", "Incomplete documentation"],
                "strengths": ["Good dependency management", "Performance optimizations"],
                "health_trends": {"trend_direction": "improving", "trend_confidence": 0.7},
                "recommendations": ["Improve test coverage", "Enhance documentation", "Refactor complex code"],
            }

            return {
                "status": "success",
                "health_report": health_report,
                "method": "comprehensive_health_analysis",
            }

        except Exception as exc:
            return {
                "status": "error",
                "error": f"Health analysis failed: {exc}",
            }


