from __future__ import annotations

"""Relationship analysis helpers for the LEANN plugin."""

from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List
import re

SearchFn = Callable[[str, str, int], Awaitable[Dict[str, Any]]]


class RelationshipAnalyzer:
    """Derives relationships between modules using semantic or text analysis."""

    def __init__(self, project_root: Path, search: SearchFn) -> None:
        self._project_root = project_root
        self._search = search

    async def analyze(self, index_name: str, semantic_available: bool) -> Dict[str, Any]:
        if semantic_available:
            relationships = {
                "imports": await self._analyze_import_relationships(index_name),
                "class_hierarchy": await self._analyze_class_hierarchy(index_name),
                "function_calls": await self._analyze_function_dependencies(index_name),
                "design_patterns": await self._extract_design_patterns(index_name),
            }
            return {"status": "success", "method": "semantic_analysis", "relationships": relationships}

        return await self._analyze_relationships_fallback()

    async def _analyze_import_relationships(self, index_name: str) -> Dict[str, Any]:
        query = "import statements, from statements, module dependencies, package imports"
        result = await self._search(index_name, query, 20)
        if result.get("status") == "success":
            return self._extract_import_patterns(result.get("results", ""))
        return {"modules": [], "import_statements": [], "circular_dependencies": []}

    async def _analyze_class_hierarchy(self, index_name: str) -> Dict[str, Any]:
        query = "class inheritance, base classes, parent classes, class relationships"
        result = await self._search(index_name, query, 15)
        if result.get("status") == "success":
            return self._extract_class_relationships(result.get("results", ""))
        return {"hierarchy": {}, "inheritance_count": 0, "classes_with_inheritance": [], "depth": 0}

    async def _analyze_function_dependencies(self, index_name: str) -> Dict[str, Any]:
        query = "function calls, method calls, function dependencies, call chains"
        result = await self._search(index_name, query, 20)
        if result.get("status") == "success":
            return self._extract_function_calls(result.get("results", ""))
        return {"total_calls": 0, "internal_calls": [], "external_calls": [], "call_patterns": []}

    async def _extract_design_patterns(self, index_name: str) -> List[str]:
        patterns = []
        queries = [
            "factory pattern implementation",
            "observer pattern implementation",
            "singleton pattern implementation",
            "strategy pattern implementation",
            "decorator pattern implementation",
            "command pattern implementation",
            "mediator pattern implementation",
        ]
        for query in queries:
            result = await self._search(index_name, query, 3)
            output = result.get("results", "") if result.get("status") == "success" else ""
            if len(output) > 20:
                patterns.append(query.split()[0].title())
        return patterns

    def _extract_import_patterns(self, results: str) -> Dict[str, Any]:
        modules: List[str] = []
        import_statements: List[str] = []
        for line in results.split("\n"):
            line_clean = line.strip()
            if "import " in line_clean or "from " in line_clean:
                import_statements.append(line_clean)
                if "import " in line_clean:
                    parts = line_clean.split("import ")
                    if len(parts) > 1:
                        module_part = parts[1].split()[0] if " as " in parts[1] else parts[1].split(",")[0]
                        module_part = module_part.strip("() ")
                        if module_part:
                            modules.append(module_part.strip())
        unique_modules = list(dict.fromkeys(modules))[:20]
        return {
            "modules": unique_modules,
            "import_statements": import_statements[:15],
            "circular_dependencies": [],
        }

    def _extract_class_relationships(self, results: str) -> Dict[str, Any]:
        inheritance_links: List[str] = []
        for line in results.split("\n"):
            line_clean = line.strip()
            if "class " in line_clean and ("(" in line_clean or "inherits" in line_clean.lower()):
                if "(" in line_clean:
                    class_name = line_clean.split("class ")[1].split("(")[0].strip()
                    if class_name:
                        inheritance_links.append(class_name)
        return {
            "hierarchy": {},
            "inheritance_count": len(inheritance_links),
            "classes_with_inheritance": inheritance_links[:10],
            "depth": 1,
        }

    def _extract_function_calls(self, results: str) -> Dict[str, Any]:
        calls: List[str] = []
        internal_calls: List[str] = []
        external_calls: List[str] = []
        for line in results.split("\n"):
            line_clean = line.strip()
            if "(" in line_clean and "def " not in line_clean and "class " not in line_clean:
                call_name = line_clean.split("(")[0].strip()
                if "." in call_name:
                    calls.append(call_name)
                if "self." in line_clean:
                    internal_calls.append(call_name)
                elif "import" not in line_clean:
                    external_calls.append(call_name)
        return {
            "total_calls": len(calls),
            "internal_calls": internal_calls[:15],
            "external_calls": external_calls[:15],
            "call_patterns": calls[:20],
        }

    async def _analyze_relationships_fallback(self) -> Dict[str, Any]:
        try:
            if not (self._project_root / "src").exists():
                return {"status": "error", "error": "Could not locate codebase"}

            relationships = {
                "imports": {"modules": [], "import_statements": []},
                "class_hierarchy": {"classes_with_inheritance": [], "depth": 1},
                "function_calls": {"total_calls": 0, "internal_calls": [], "external_calls": []},
                "design_patterns": [],
            }

            python_files = list(self._project_root.rglob("*.py"))
            for file_path in python_files[:50]:
                try:
                    content = file_path.read_text(encoding="utf-8")
                except OSError:
                    continue

                import_lines = [line.strip() for line in content.split("\n") if line.strip().startswith(("import ", "from "))]
                relationships["imports"]["import_statements"].extend(import_lines[:10])

                for line in import_lines:
                    if line.startswith("from "):
                        module = line.split("from ")[1].split(" import ")[0].strip()
                        if module and "." not in module:
                            relationships["imports"]["modules"].append(module)

                call_matches = len(re.findall(r"\w+\s*\([^)]*\)", content))
                relationships["function_calls"]["total_calls"] += call_matches

                class_matches = re.findall(r"class\s+(\w+)\s*\(([^)]+)\)", content)
                for class_name, bases in class_matches:
                    relationships["class_hierarchy"]["classes_with_inheritance"].append(f"{class_name} -> {bases}")

            modules = list(dict.fromkeys(relationships["imports"]["modules"]))[:15]
            relationships["imports"]["modules"] = modules
            relationships["function_calls"]["internal_calls"] = len(relationships["function_calls"].get("internal_calls", []))
            relationships["function_calls"]["external_calls"] = (
                relationships["function_calls"]["total_calls"] - relationships["function_calls"]["internal_calls"]
            )

            return {"status": "success", "method": "text_relationship_analysis", "relationships": relationships}
        except Exception as exc:  # pragma: no cover - defensive
            return {"status": "error", "error": f"Fallback relationship analysis failed: {exc}"}
