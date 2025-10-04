"""Plugin for LEANN vector database integration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import functools

from .leann import (
    ChangeImpactAnalyzer,
    IntelligenceToolkit,
    LeannCommandRunner,
    RelationshipAnalyzer,
    TextFallbackSearcher,
    detect_environment,
)
from .leann.codebase import (
    build_directory_structure,
    collect_files_with_limits,
    create_analysis_result,
    discover_project_root,
    _extract_class_function_names as codebase_extract_class_function_names,
    process_python_metrics,
)


class LeannPluginError(Exception):
    """Base exception for LEANN plugin errors."""


class LeannBackendNotAvailableError(LeannPluginError):
    """Raised when LEANN backend is not available."""


class LeannCommandTimeoutError(LeannPluginError):
    """Raised when LEANN commands exceed timeout limits."""


class LeannCommandFailedError(LeannPluginError):
    """Raised when LEANN commands fail with error exit codes."""


class CodebaseAnalysisError(LeannPluginError):
    """Raised when codebase analysis operations fail."""


class LeannPlugin:
    """LEANN vector database plugin using CLI interface."""

    def __init__(self) -> None:
        self.environment = detect_environment()
        self.leann_command = self.environment.leann_command
        self.wsl_available = self.environment.wsl_available
        self.wsl_leann_available = self.environment.wsl_leann_available
        self.windows_leann_available = self.environment.windows_leann_available
        self.wsl_leann_path = self.environment.wsl_leann_path
        self.available = self.environment.available

        self.project_root = discover_project_root()
        self.command_runner = LeannCommandRunner(self.environment)
        self.text_fallback = TextFallbackSearcher(self.project_root)
        self.intelligence = IntelligenceToolkit(self.project_root)
        self.relationship_analyzer = RelationshipAnalyzer(self.project_root, self.leann_search)
        self.change_impact = ChangeImpactAnalyzer(self.leann_search)

    @property
    def is_available(self) -> bool:
        """Check if LEANN is available on this system."""
        return self.available

    @property
    def preferred_backend(self) -> str:
        """Get the preferred backend for LEANN operations."""
        if self.environment.wsl_available and (self.environment.wsl_leann_available or self.environment.wsl_leann_path):
            return "wsl"
        if self.environment.windows_leann_available:
            return "windows"
        return "none"

    @functools.cached_property
    def leann_version_info(self) -> Optional[Dict[str, Any]]:
        """Get LEANN version information with caching."""
        result = self.command_runner.run(["--version"])
        if result.get("status") == "success":
            return {"output": result.get("output"), "using_wsl": result.get("using_wsl", False)}
        return None

    @functools.cached_property
    def supported_backends(self) -> List[str]:
        """Get list of supported vector backends."""
        result = self.command_runner.run(["backends", "--list"])
        if result.get("status") == "success":
            backends: List[str] = []
            for line in result.get("output", "").splitlines():
                if line.strip() and not line.startswith(("Available", "Supported")):
                    token = line.strip().split()[0]
                    if token and token.lower() not in backends:
                        backends.append(token.lower())
            if backends:
                return backends
        return ["faiss", "hnsw"]

    async def leann_build_index(self, index_name: str, docs: List[str]) -> Dict[str, Any]:
        """Build a LEANN vector index from a collection of documents."""
        if not self.available:
            return {
                "status": "error",
                "error": "LEANN is not installed or not available on this system",
                "note": "LEANN backend may not support Windows. Consider using WSL2 for full functionality.",
            }

        args = ["build", index_name]
        for doc_path in docs:
            args.extend(["--docs", doc_path])

        result = self.command_runner.run(args)
        if result.get("status") == "success":
            return {
                "status": "success",
                "message": f"Index '{index_name}' build completed",
                "details": result.get("output") or "Index built successfully",
                "docs_count": len(docs),
            }

        error_message = result.get("error", "Unknown LEANN build error")
        if "Backend 'hnsw' not found" in error_message:
            return {
                "status": "error",
                "error": "LEANN vector backend not available on Windows",
                "suggestion": "Use WSL2 for full LEANN functionality, or build index on Linux/macOS",
                "workaround": "The CLI search interface still works for text-based searching",
            }

        return {
            "status": "error",
            "error": error_message,
            "command_used": result.get("command", ""),
            "details": result.get("output") or error_message,
        }

    async def leann_search(self, index_name: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Search through LEANN-indexed documents using semantic search with text fallback."""
        if not self.available:
            return await self.text_fallback.search(index_name, query, top_k)

        args = ["search", index_name, query, "--top-k", str(top_k)]
        result = self.command_runner.run(args)
        if result.get("status") == "success":
            return {
                "status": "success",
                "query": query,
                "results": result.get("output", ""),
                "top_k": top_k,
                "index": index_name,
            }

        return await self.text_fallback.search(index_name, query, top_k)

    async def leann_ask(self, index_name: str, question: str, top_k: int = 3) -> Dict[str, Any]:
        """Ask questions about indexed documents with AI-generated responses."""
        if not self.available:
            return {
                "status": "error",
                "error": "LEANN is not installed or not available on this system",
                "note": "LEANN requires LLM configuration for question answering.",
            }

        args = ["ask", index_name, "--interactive", "--top-k", str(top_k)]
        result = self.command_runner.run(args, input_data=question)
        if result.get("status") == "success":
            return {
                "status": "success",
                "question": question,
                "answer": result.get("output", ""),
                "top_k": top_k,
                "index": index_name,
            }
        return result

    async def leann_list(self) -> Dict[str, Any]:
        """List all available LEANN indexes."""
        result = self.command_runner.run(["list"])
        if result.get("status") == "success":
            return {
                "status": "success",
                "indexes": result.get("output", ""),
                "available": self.available,
            }
        return {
            "status": "success",
            "indexes": "No indexes found or LEANN not fully available",
            "available": self.available,
        }

    async def analyze_code_relationships(self, index_name: str = "agent-code") -> Dict[str, Any]:
        """Analyze code relationships and dependencies using semantic vector similarity."""
        try:
            return await self.relationship_analyzer.analyze(index_name, self.available)
        except Exception as exc:  # pragma: no cover - defensive
            return {
                "status": "error",
                "error": f"Failed to analyze code relationships: {exc}",
                "method": "error_fallback",
            }

    async def predict_change_impact(self, modified_files: List[str], index_name: str = "agent-code") -> Dict[str, Any]:
        """Predict cascade effects of code modifications using LEANN similarity."""
        try:
            if not modified_files:
                return {
                    "status": "success",
                    "method": "semantic_impact_analysis",
                    "impact": {
                        "affected_functions": [],
                        "affected_classes": [],
                        "breaking_changes": [],
                        "suggestion_score": 0,
                    },
                    "risk_level": "low",
                }
            return await self.change_impact.predict(modified_files, index_name)
        except Exception as exc:
            return {
                "status": "error",
                "error": f"Failed to predict change impact: {exc}",
                "method": "impact_analysis_error",
            }

    async def analyze_codebase_intelligence(self, index_name: str = "agent-code", question: Optional[str] = None) -> Dict[str, Any]:
        """Advanced codebase intelligence with LEANN vector search and self-diagnosis fallback."""
        if not self.available:
            return await self.intelligence.fallback_analysis(index_name, question)

        try:
            print(f"[DEBUG] Analyzing codebase index: {index_name}")
            if question:
                print(f"[DEBUG] Question provided: {question}")

            list_result = self.command_runner.run(["list"])
            print(f"[DEBUG] List result: {list_result}")
            index_exists = index_name in (list_result.get("output") or "")
            print(f"[DEBUG] Index exists: {index_exists}")

            print(f"[DEBUG] Building {index_name} index...")
            build_args = ["build", index_name, "--force"]
            for directory in ["src", "tests", "docs"]:
                path = self.project_root / directory
                if path.exists():
                    build_args.extend(["--docs", str(path)])

            if len(build_args) == 3:
                return {
                    "status": "error",
                    "error": "No src/, tests/, or docs/ directories found to index",
                    "index": index_name,
                }

            print(f"[DEBUG] Build command args: {build_args}")
            build_result = self.command_runner.run(build_args)
            print(f"[DEBUG] Build result: {build_result}")

            if build_result.get("status") != "success":
                error_text = build_result.get("error", "")
                if "Backend 'hnsw' not found" in error_text:
                    print("[DEBUG] HNSW backend not available, using fallback text analysis")
                    return await self.intelligence.fallback_analysis(index_name, question)
                return {
                    "status": "error",
                    "error": f"Failed to build index: {error_text or 'Unknown error'}",
                    "index": index_name,
                    "build_output": build_result.get("output", ""),
                }

            if not question:
                question = "What are the main components and architecture of this codebase?"

            ask_result = self.command_runner.run(["ask", index_name, "--interactive", "--top-k", "20"], input_data=question)
            if ask_result.get("status") == "success":
                answer = ask_result.get("output", "")
                return {
                    "status": "success",
                    "analysis": {
                        "overview": answer,
                        "method": "leann_semantic_search",
                        "index_name": index_name,
                    },
                    "index": index_name,
                    "method": "leann_ask",
                }

            error_text = ask_result.get("error", "Unknown error")
            if "Backend 'hnsw' not found" in error_text:
                return await self.intelligence.fallback_analysis(index_name, question)
            return {
                "status": "error",
                "error": f"LEANN ask failed: {error_text}",
                "index": index_name,
            }
        except Exception as exc:
            return {
                "status": "error",
                "error": f"Failed to analyze codebase: {exc}",
                "index": index_name,
            }

    # ------------------------------------------------------------------
    # Backwards compatibility helpers (preserved for existing tests/docs)
    # ------------------------------------------------------------------

    async def _answer_question_with_text_analysis(self, index_name: str, question: str) -> Dict[str, Any]:
        return await self.intelligence.answer_question(index_name, question)

    def _generate_improvement_recommendations(self, base_path: Path) -> str:
        return self.intelligence._generate_improvement_recommendations(base_path)

    def _diagnose_system_issues(self, base_path: Path, question: str) -> str:
        return self.intelligence._diagnose_system_issues(base_path, question)

    def _diagnose_web_plugins(self, base_path: Path) -> str:
        return self.intelligence._diagnose_web_plugins(base_path)

    def _diagnose_general_issues(self, base_path: Path) -> str:
        return self.intelligence._diagnose_general_issues(base_path)

    def _verify_recent_fixes(self, base_path: Path, question: str) -> str:
        return self.intelligence._verify_recent_fixes(base_path, question)

    def _answer_visibility_question(self, base_path: Path) -> str:
        return self.intelligence._answer_visibility_question(base_path)

    def _explain_specific_plugin(self, base_path: Path, plugin_name: str) -> str:
        return self.intelligence._explain_specific_plugin(base_path, plugin_name)

    def _extract_plugin_name(self, question: str) -> Optional[str]:
        return self.intelligence._extract_plugin_name(question.lower())

    def _is_capability_question(self, question: str) -> bool:
        return self.intelligence._is_capability_question(question.lower())

    def _generate_codebase_overview(self, base_path: Path) -> str:
        return self.intelligence._generate_codebase_overview(base_path)

    def _find_codebase_path(self) -> Path:
        return discover_project_root()

    def _collect_files_with_limits(self, base_path: Path, max_files: int = 200):
        return collect_files_with_limits(base_path, max_files)

    def _process_files_for_metrics(self, py_files: List[Path], max_content_mb: float = 0.5) -> Dict[str, Any]:
        return process_python_metrics(py_files, max_content_mb)

    def _build_directory_structure(self, base_path: Path) -> Dict[str, List[str]]:
        return build_directory_structure(base_path)

    def _create_analysis_result(
        self,
        files: List[Path],
        metrics: Dict[str, Any],
        dir_structure: Dict[str, List[str]],
        index_name: str,
    ) -> Dict[str, Any]:
        return create_analysis_result(files, metrics, dir_structure, index_name)

    def _extract_class_function_names(
        self,
        content: str,
        class_names: List[str],
        function_names: List[str],
    ) -> None:
        codebase_extract_class_function_names(content, class_names, function_names)

    def _extract_import_patterns(self, search_results: str) -> Dict[str, Any]:
        return self.relationship_analyzer._extract_import_patterns(search_results)

    def _extract_class_relationships(self, search_results: str) -> Dict[str, Any]:
        return self.relationship_analyzer._extract_class_relationships(search_results)

    def _calculate_change_risk(self, impact: Dict[str, Any]) -> str:
        return self.change_impact._calculate_change_risk(impact)

    def _get_command_runner(self, args: List[str]) -> tuple[List[str], bool]:
        """Maintain compatibility with legacy tests for command selection."""
        runner = getattr(self, "command_runner", None)
        if runner is None:
            use_wsl = bool(getattr(self, "wsl_available", False)) or (
                bool(getattr(self, "wsl_leann_available", False))
                and not bool(getattr(self, "windows_leann_available", False))
            )
            if use_wsl:
                leann_exec = getattr(self, "wsl_leann_path", None) or "/home/username/.local/bin/leann"
                return ["wsl", leann_exec, *args], True
            return [self.leann_command, *args], False

        use_wsl = runner._should_use_wsl()
        if use_wsl:
            return runner._build_wsl_command(args, self.project_root), True
        return [self.leann_command, *args], False


    async def execute(self, server: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LEANN plugin tool commands with a standardized MCP-compatible interface."""
        if server != "leann":
            return {"status": "error", "error": "Unknown server"}

        if tool_name == "leann_build_index":
            return await self.leann_build_index(args.get("index_name", ""), args.get("docs", []))
        if tool_name == "leann_search":
            return await self.leann_search(args.get("index_name", ""), args.get("query", ""), args.get("top_k", 5))
        if tool_name == "leann_ask":
            return await self.leann_ask(args.get("index_name", ""), args.get("question", ""), args.get("top_k", 3))
        if tool_name == "leann_list":
            return await self.leann_list()
        if tool_name == "analyze_codebase_intelligence":
            return await self.analyze_codebase_intelligence(args.get("index_name", "agent-code"), args.get("question"))
        if tool_name == "analyze_code_relationships":
            return await self.analyze_code_relationships(args.get("index_name", "agent-code"))
        if tool_name == "predict_change_impact":
            return await self.predict_change_impact(args.get("modified_files", []), args.get("index_name", "agent-code"))

        return {"status": "error", "error": f"Unknown tool {tool_name}"}
