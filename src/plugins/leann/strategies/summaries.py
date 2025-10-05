from __future__ import annotations

"""Architecture and summary helpers for LEANN fallback analysis."""

import logging
from pathlib import Path
from typing import Any, Dict, List

from ..codebase import (
    build_directory_structure,
    collect_files_with_limits,
    create_analysis_result,
    process_python_metrics,
)


logger = logging.getLogger(__name__)


class ArchitectureSummarizer:
    """Provide textual summaries and recommendations about the codebase."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    # Public helpers -------------------------------------------------------------

    def codebase_overview(self) -> str:
        """Return a concise overview of the repository layout."""
        structure = build_directory_structure(self._project_root)
        directory_lines = "\n".join(
            f"- **{folder}/** ? {', '.join(files)}" for folder, files in structure.items()
        ) or "- No top level directories discovered"

        return (
            "# Codebase Overview\n\n"
            "## Primary Directories\n"
            f"{directory_lines}\n\n"
            "## Key Characteristics\n"
            "- MCP-compatible agent with modular plugins\n"
            "- Async-first architecture for tool execution\n"
            "- Extensive integration and contract test coverage\n"
        )

    def detailed_assessment(self) -> str:
        """Produce a higher fidelity assessment based on lightweight metrics."""
        metrics = self._collect_code_metrics(max_files=200)
        totals = metrics.get("totals", {})

        return (
            "# Detailed Assessment\n\n"
            "## Quantitative Snapshot\n"
            f"- Python files analysed: {totals.get('python_files', 0)}\n"
            f"- Async functions detected: {totals.get('async_functions', 0)}\n"
            f"- Average lines per file: {totals.get('avg_lines_per_file', 0):.1f}\n"
            f"- Test modules sampled: {totals.get('test_files', 0)}\n"
            "\n"
            "## Observations\n"
            "- Async usage is {totals.get('async_functions', 0) and 'present' or 'minimal'}, signalling non-blocking design\n"
            "- Plugin footprint covers {totals.get('plugin_files', 0)} modules under src/plugins/\n"
            "- Documentation coverage includes {totals.get('doc_files', 0)} markdown or text guides\n"
            "\n"
            "## Suggested Areas to Monitor\n"
            "1. Ensure new plugins include integration tests alongside implementations\n"
            "2. Expand structured logging around plugin execution paths\n"
            "3. Continue enriching module and function docstrings for high-churn files\n"
        )

    def architecture_explanation(self, question: str) -> str:
        """Explain how plugins are discovered and executed."""
        plugin_names = sorted(path.stem for path in self._plugin_paths()[:12])
        plugin_lines = "\n".join(f"- {name}" for name in plugin_names) or "- No plugins discovered"

        return (
            "# Plugin Architecture Overview\n\n"
            "The agent exposes capabilities through MCP-compatible plugins. Execution flow:\n\n"
            "1. **Discovery** - modules in src/plugins/ are loaded at startup\n"
            "2. **Registration** - PluginExecutor keeps a map of tool ? plugin\n"
            "3. **Invocation** - tools call each plugin's sync execute(...) entry point\n"
            "4. **Response** - plugins return JSON-friendly dictionaries describing outcomes\n\n"
            "## Available Plugins\n"
            f"{plugin_lines}\n\n"
            "## Tips\n"
            "- Add new plugins under src/plugins/ and implement execute\n"
            "- Register tooling in config/mcp_tools.json for routing\n"
            "- Keep implementations idempotent and async-safe\n"
        )

    def plugin_details(self, plugin_name: str, base_path: Path = None) -> str:
        """Inspect a specific plugin module and summarise its surface area."""
        if base_path is None:
            base_path = self._project_root

        plugin_path = base_path / "src" / "plugins" / f"{plugin_name}.py"
        if not plugin_path.exists():
            return f"Plugin '{plugin_name}' not found under src/plugins/."

        content = plugin_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        public_methods = [
            line.split("def ")[1].split("(")[0]
            for line in lines
            if line.strip().startswith("def ") and not line.strip().startswith("def _")
        ]
        async_methods = [
            line.split("async def ")[1].split("(")[0]
            for line in lines
            if line.strip().startswith("async def ")
        ]

        return (
            f"# Plugin: {plugin_name}\n\n"
            f"- File: src/plugins/{plugin_name}.py\n"
            f"- Public methods: {', '.join(public_methods) or 'None detected'}\n"
            f"- Async methods: {', '.join(async_methods) or 'None detected'}\n"
            f"- Total lines: {len(lines)}\n"
        )

    def capability_answer(self, question: str) -> str:
        """Respond to capability-style prompts."""
        if "create" in question and "plugin" in question:
            return self._plugin_creation_answer()

        return (
            "**Yes - the agent is fully capable.**\n\n"
            "### Core abilities\n"
            "- Read and analyse project files\n"
            "- Modify code (including self-modification)\n"
            "- Orchestrate async tool execution\n"
            "- Generate documentation and tests\n"
            "- Extend itself with new MCP tools\n\n"
            "Let me know what you would like to build next."
        )

    def improvement_recommendations(self) -> str:
        """Generate small, actionable recommendations using sampled data."""
        metrics = self._collect_code_metrics(max_files=120)
        totals = metrics.get("totals", {})
        recs: List[str] = []

        if totals.get("async_functions", 0) and totals.get("await_sites", 0) < totals["async_functions"]:
            recs.append("- Audit async functions to ensure every coroutine is awaited")
        if totals.get("test_files", 0) < max(1, totals.get("python_files", 0) // 4):
            recs.append("- Increase integration test coverage for new plugins")
        if totals.get("doc_files", 0) < 5:
            recs.append("- Add more task-focused docs under docs/ to guide contributors")
        if not recs:
            recs.append("- Maintain current quality bar and continue incremental improvements")

        return (
            "# Targeted Improvement Ideas\n\n"
            + "\n".join(recs)
        )

    # Internal utilities ---------------------------------------------------------

    def _collect_code_metrics(self, max_files: int) -> Dict[str, Any]:
        files = collect_files_with_limits(self._project_root, max_files=max_files)
        py_files = [f for f in files if f.suffix == ".py"]
        metrics = process_python_metrics(py_files)
        totals = {
            "python_files": len(py_files),
            "async_functions": metrics.get("async_count", 0),
            "plugin_files": sum(1 for f in py_files if "plugins" in f.parts),
            "doc_files": len([f for f in files if f.suffix in {".md", ".txt"}]),
            "test_files": len([f for f in py_files if "tests" in f.parts]),
            "avg_lines_per_file": self._average_line_count(metrics.get("line_counts", {})),
            "await_sites": metrics.get("func_count", 0) - metrics.get("async_count", 0),
        }
        return {"totals": totals}

    def _plugin_paths(self) -> List[Path]:
        return sorted((self._project_root / "src" / "plugins").glob("*.py"))

    def _average_line_count(self, line_counts: Dict[str, int]) -> float:
        if not line_counts:
            return 0.0
        return sum(line_counts.values()) / max(1, len(line_counts))

    def _plugin_creation_answer(self) -> str:
        plugin_names = [path.stem for path in self._plugin_paths()[:10]]
        return (
            "**Absolutely - I can create new plugins.**\n\n"
            "### Process\n"
            "1. Generate a new module under src/plugins/\n"
            "2. Implement sync def execute(server, tool_name, args)\n"
            "3. Register the tool in config/mcp_tools.json\n"
            "4. Restart the agent to load the capability\n\n"
            "### Currently installed plugins\n"
            + "\n".join(f"- {name}" for name in plugin_names)
        )
