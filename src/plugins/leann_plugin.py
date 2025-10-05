"""Plugin for LEANN vector database integration."""

from __future__ import annotations

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
from .leann.codebase import discover_project_root
from .leann.index_service import LeannIndexService
from .leann.orchestrator import LeannAnalysisOrchestrator


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
        self._available = self.environment.available
        self.project_root = discover_project_root()
        self.command_runner = LeannCommandRunner(self.environment)
        self.text_fallback = TextFallbackSearcher(self.project_root)
        self.intelligence = IntelligenceToolkit(self.project_root)
        self.relationship_analyzer = RelationshipAnalyzer(self.project_root, self.leann_search)
        self.change_impact = ChangeImpactAnalyzer(self.leann_search)

        self.index_service = LeannIndexService(
            self.environment,
            self.command_runner,
            self.text_fallback,
        )
        self.index_service.set_availability_override(self._available)
        self.analysis_orchestrator = LeannAnalysisOrchestrator(
            self.project_root,
            self.index_service,
            self.intelligence,
        )

    @property
    def available(self) -> bool:
        """Expose current LEANN availability."""
        return getattr(self, "_available", True)

    @available.setter
    def available(self, value: bool) -> None:
        """Allow callers to toggle availability for service fallbacks."""
        self._available = value
        if hasattr(self, "index_service"):
            self.index_service.set_availability_override(value)

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
        return self.index_service.supported_backends

    async def leann_build_index(self, index_name: str, docs: List[str]) -> Dict[str, Any]:
        """Build a LEANN vector index from a collection of documents."""
        return await self.index_service.build_index(index_name, docs)

    async def leann_search(self, index_name: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Search through LEANN-indexed documents using semantic search with text fallback."""
        return await self.index_service.search(index_name, query, top_k)

    async def leann_ask(self, index_name: str, question: str, top_k: int = 3) -> Dict[str, Any]:
        """Ask questions about indexed documents with AI-generated responses."""
        return await self.index_service.ask(index_name, question, top_k)

    async def leann_list(self) -> Dict[str, Any]:
        """List all available LEANN indexes."""
        return await self.index_service.list_indexes()

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
        return await self.analysis_orchestrator.analyze_codebase_intelligence(index_name, question)

    # ------------------------------------------------------------------
    # Self-diagnosis and enhancement methods
    # ------------------------------------------------------------------

    async def _comprehensive_self_diagnosis(self, index_name: str = "agent-code", question: Optional[str] = None) -> Dict[str, Any]:
        """Perform comprehensive self-diagnosis of the codebase."""
        return await self.analysis_orchestrator._comprehensive_self_diagnosis(index_name, question)

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

    def _extract_import_patterns(self, search_results: str) -> Dict[str, Any]:
        return self.relationship_analyzer._extract_import_patterns(search_results)

    def _extract_class_relationships(self, search_results: str) -> Dict[str, Any]:
        return self.relationship_analyzer._extract_class_relationships(search_results)

    def _calculate_change_risk(self, impact: Dict[str, Any]) -> str:
        return self.change_impact._calculate_change_risk(impact)

    async def _generate_codebase_enhancement_plan(self, index_name: str = "agent-code") -> Dict[str, Any]:
        """Generate a comprehensive enhancement plan for the codebase."""
        return await self.analysis_orchestrator._generate_codebase_enhancement_plan(index_name)

    async def _create_dynamic_enhancement_plan(self, analysis: Dict[str, Any]) -> str:
        """Create dynamic enhancement plan based on actual codebase analysis."""
        return await self.analysis_orchestrator._create_dynamic_enhancement_plan(analysis)

    async def _create_comprehensive_analysis_report(self, analysis: Dict[str, Any]) -> str:
        """Create a comprehensive codebase analysis report."""
        return await self.analysis_orchestrator._create_comprehensive_analysis_report(analysis)

    async def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze project structure and organization."""
        return await self.analysis_orchestrator._analyze_project_structure()

    async def _analyze_code_quality(self) -> Dict[str, Any]:
        """Analyze code quality metrics."""
        return await self.analysis_orchestrator._analyze_code_quality()

    async def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies."""
        return await self.analysis_orchestrator._analyze_dependencies()

    async def _analyze_test_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage and quality."""
        return await self.analysis_orchestrator._analyze_test_coverage()

    async def _analyze_documentation(self) -> Dict[str, Any]:
        """Analyze documentation quality and coverage."""
        return await self.analysis_orchestrator._analyze_documentation()

    async def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance characteristics."""
        return await self.analysis_orchestrator._analyze_performance()

    async def _analyze_pyproject_file(self, pyproject_path: Path) -> Dict[str, Any]:
        """Analyze pyproject.toml file for dependencies and configuration."""
        return await self.analysis_orchestrator._analyze_pyproject_file(pyproject_path)

    def _calculate_complexity_score(self, avg_functions_per_file: float, avg_lines_per_file: float) -> float:
        """Calculate a complexity score based on various metrics."""
        return self.analysis_orchestrator._calculate_complexity_score(avg_functions_per_file, avg_lines_per_file)

    async def _generate_enhancement_recommendations(
        self,
        project_metrics: Dict[str, Any],
        code_quality: Dict[str, Any],
        dependency_analysis: Dict[str, Any],
        test_coverage: Dict[str, Any],
        documentation_analysis: Dict[str, Any],
        performance_analysis: Dict[str, Any],
    ) -> List[str]:
        """Generate specific enhancement recommendations."""
        return await self.analysis_orchestrator._generate_enhancement_recommendations(
            project_metrics,
            code_quality,
            dependency_analysis,
            test_coverage,
            documentation_analysis,
            performance_analysis,
        )

    async def _analyze_codebase_health(self, index_name: str = "agent-code") -> Dict[str, Any]:
        """Analyze overall codebase health with detailed metrics."""
        return await self.analysis_orchestrator._analyze_codebase_health(index_name)

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

        if tool_name == "generate_codebase_enhancement_plan":
            index_name = args.get("index_name", "agent-code")
            # Prefer orchestrator-driven plan for richer insights
            try:
                plan_result = await self._generate_codebase_enhancement_plan(index_name)
            except Exception as orchestrator_error:
                plan_result = {"status": "error", "error": str(orchestrator_error)}

            if plan_result.get("status") == "success" and plan_result.get("enhancement_plan"):
                # Optionally enrich with intelligence insights
                overview = None
                try:
                    intelligence_result = await self.intelligence.answer_question(
                        index_name,
                        "what would you change to improve this codebase and what specific recommendations do you have?"
                    )
                except Exception:
                    intelligence_result = None

                if intelligence_result and intelligence_result.get("status") == "success":
                    overview = intelligence_result.get("analysis", {}).get("overview")

                if overview:
                    plan_text = plan_result["enhancement_plan"].rstrip()
                    if plan_text:
                        plan_text += "\n\n## Intelligence Insights\n"
                    plan_result["enhancement_plan"] = plan_text + overview.strip()

                return plan_result

            # Orchestrator fallback to legacy behaviour
            try:
                enhancement_result = await self.intelligence.answer_question(
                    index_name,
                    "what would you change to improve this codebase and what specific recommendations do you have?"
                )
                if enhancement_result.get("status") == "success":
                    overview = enhancement_result.get("analysis", {}).get("overview", "")
                    return {"status": "success", "enhancement_plan": overview}

                diagnosis = await self._comprehensive_self_diagnosis(index_name)
                if diagnosis.get("status") == "success":
                    enhancement_plan = await self._create_dynamic_enhancement_plan(diagnosis["analysis"])
                    return {"status": "success", "enhancement_plan": enhancement_plan}

                return {"status": "error", "error": diagnosis.get("error", "Diagnosis failed")}
            except Exception as exc:
                return {"status": "error", "error": f"Enhancement plan generation failed: {exc}"}

        if tool_name == "comprehensive_self_improvement_analysis":
            # Return a comprehensive codebase analysis instead of enhancement plan
            try:
                diagnosis = await self._comprehensive_self_diagnosis(args.get("index_name", "agent-code"))
                if diagnosis.get("status") == "success":
                    analysis_report = await self._create_comprehensive_analysis_report(diagnosis["analysis"])
                    return {"status": "success", "enhancement_plan": analysis_report}
                else:
                    return {"status": "error", "error": diagnosis.get("error", "Diagnosis failed")}
            except Exception as e:
                return {"status": "error", "error": f"Analysis failed: {str(e)}"}
        if tool_name == "analyze_codebase_health":
            return await self._analyze_codebase_health(args.get("index_name", "agent-code"))

        return {"status": "error", "error": f"Unknown tool {tool_name}"}
