from __future__ import annotations

"""Fallback intelligence helpers for the LEANN plugin."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import logging

from .codebase import (
    build_directory_structure,
    collect_files_with_limits,
    create_analysis_result,
    process_python_metrics,
)
from .strategies import (
    ArchitectureSummarizer,
    DiagnosticsAdvisor,
    QuestionIntent,
    QuestionRouter,
)


logger = logging.getLogger(__name__)


class IntelligenceToolkit:
    """Provides text-based analysis and question answering when LEANN is unavailable."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root
        self._question_router = QuestionRouter()
        self._diagnostics = DiagnosticsAdvisor(project_root)
        self._summaries = ArchitectureSummarizer(project_root)

    @property
    def question_router(self) -> QuestionRouter:
        """Expose the shared question router."""
        return self._question_router

    @property
    def diagnostics(self) -> DiagnosticsAdvisor:
        """Expose the diagnostics helper for orchestrator reuse."""
        return self._diagnostics

    @property
    def summarizer(self) -> ArchitectureSummarizer:
        """Expose the architecture summariser."""
        return self._summaries

    async def fallback_analysis(self, index_name: str, question: Optional[str]) -> Dict[str, Any]:
        logger.debug(f"[DEBUG] Fallback called with question: {repr(question)}")
        if question:
            logger.debug(f"[DEBUG] Fallback answering specific question: {question}")
            return await self.answer_question(index_name, question)

        logger.debug("[DEBUG] No question provided, using generic analysis")
        if index_name != "agent-code":
            return {
                "status": "success",
                "analysis": {"overview": "Fallback analysis currently focuses on agent-code index."},
                "index": index_name,
                "method": "minimal_fallback_analysis",
                "note": "Index not fully supported for fallback analysis",
            }

        base_path = self._project_root
        logger.debug(f"[DEBUG] Analyzing codebase at: {base_path}")

        # Use comprehensive file scanning instead of limited collect_files_with_limits
        all_files = []
        for root_dir in [base_path, base_path / "src", base_path / "tests", base_path / "docs"]:
            logger.debug(f"[DEBUG] Scanning directory: {root_dir}")
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
                logger.debug(f"[DEBUG] Directory does not exist: {root_dir}")
            if len(all_files) >= 1000:
                break

        # Remove duplicates
        all_files = list(set(all_files))
        logger.debug(f"[DEBUG] Found {len(all_files)} unique files to analyze")

        py_files = [path for path in all_files if path.suffix == ".py"]
        metrics = process_python_metrics(py_files)
        dir_structure = build_directory_structure(base_path)
        return create_analysis_result(all_files, metrics, dir_structure, index_name)

    async def answer_question(self, index_name: str, question: str, base_path: Path = None) -> Dict[str, Any]:
        try:
            route = self._question_router.classify(question)

            if route.intent is QuestionIntent.VISIBILITY:
                answer = self._diagnostics.visibility_report()
            elif route.intent is QuestionIntent.VERIFY_FIX:
                answer = self._diagnostics.verify_recent_fixes(question)
            elif route.intent is QuestionIntent.DIAGNOSTIC:
                answer = self._diagnostics.diagnose(question)
            elif route.intent is QuestionIntent.IMPROVEMENT:
                answer = self._summaries.improvement_recommendations()
            elif route.intent is QuestionIntent.ASSESSMENT:
                answer = self._summaries.detailed_assessment()
            elif route.intent is QuestionIntent.CAPABILITY:
                answer = self._summaries.capability_answer(question)
            elif route.intent is QuestionIntent.PLUGIN_SPECIFIC and route.plugin_name:
                answer = self._summaries.plugin_details(route.plugin_name, base_path)
            elif route.intent is QuestionIntent.ARCHITECTURE:
                answer = self._summaries.architecture_explanation(question)
            else:
                answer = self._summaries.codebase_overview()

            return {
                "status": "success",
                "analysis": {
                    "overview": answer,
                    "method": "text_analysis_question_specific",
                    "index_name": index_name,
                },
                "index": index_name,
                "method": "text_fallback_smart",
            }
        except Exception as exc:
            logger.debug(f"Question answering error: {exc}")
            return await self.fallback_analysis(index_name, question=None)

    def _answer_visibility_question(self, base_path: Path) -> str:
        return self._diagnostics.visibility_report()



    def _verify_recent_fixes(self, base_path: Path, question: str) -> str:
        return self._diagnostics.verify_recent_fixes(question, base_path)



    def _diagnose_system_issues(self, base_path: Path, question: str) -> str:
        return self._diagnostics.diagnose(question)



    def _diagnose_web_plugins(self, base_path: Path) -> str:
        return self._diagnostics.web_plugins_report(base_path)



    def _diagnose_plugin_execution(self, base_path: Path) -> str:
        return self._diagnostics.plugin_execution_report()



    def _diagnose_general_issues(self, base_path: Path) -> str:
        return self._diagnostics.general_system_report()



    def _generate_improvement_recommendations(self, base_path: Path) -> str:
        return self._summaries.improvement_recommendations()



    def _generate_codebase_overview(self, base_path: Path) -> str:
        src_files = list((base_path / "src").rglob("*.py"))
        test_files = list((base_path / "tests").rglob("*.py"))
        doc_files = list((base_path / "docs").rglob("*.md"))
        return (
            "# Codebase Overview\n\n"
            "## Structure\n"
            "```\n"
            "mcp-ai-agent/\n"
            f"|-- src/ ({len(src_files)} Python files)\n"
            "|   |-- agent/ (core functionality)\n"
            "|   `-- plugins/ (tool plugins)\n"
            f"|-- tests/ ({len(test_files)} test files)\n"
            f"`-- docs/ ({len(doc_files)} documentation files)\n"
            "```\n\n"
            "## Main Directories\n\n"
            "**src/agent/**: Core agent implementation\n"
            "- Agent class, API integration, memory management\n"
            "- ReAct loop for autonomous behavior\n"
            "- Web UI and server implementations\n\n"
            "**src/plugins/**: Extensible tool plugins\n"
            "- Search, browser, analysis, LEANN, etc.\n"
            "- Each plugin provides specific capabilities\n"
            "- MCP-compatible tool interfaces\n\n"
            "**tests/**: Test suite\n"
            "- Integration tests, contract tests\n"
            "- Validates core functionality\n\n"
            "## Technology Stack\n"
            "- **Language**: Python (async/await)\n"
            "- **Architecture**: Plugin-based modular design\n"
            "- **Protocol**: Model Context Protocol (MCP)\n"
            "- **UI**: WebSocket-based real-time interface\n"
            "- **AI**: OpenRouter LLM integration"
        )
