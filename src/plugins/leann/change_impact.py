from __future__ import annotations

"""Change impact analysis helpers for the LEANN plugin."""

from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List
import re

SearchFn = Callable[[str, str, int], Awaitable[Dict[str, Any]]]


class ChangeImpactAnalyzer:
    """Estimates downstream effects of modifications using LEANN search."""

    def __init__(self, search: SearchFn) -> None:
        self._search = search

    async def predict(self, modified_files: List[str], index_name: str) -> Dict[str, Any]:
        analysis = {"affected_functions": [], "affected_classes": [], "breaking_changes": [], "suggestion_score": 0}

        for file_path in modified_files:
            entities = await self._extract_entities_from_file(file_path)
            entity_usage = await self._analyze_entity_usage(entities, index_name)
            analysis["affected_functions"].extend(entity_usage.get("affected_functions", []))
            analysis["affected_classes"].extend(entity_usage.get("affected_classes", []))
            analysis["suggestion_score"] += entity_usage.get("usage_count", 0)

        return {
            "status": "success",
            "method": "semantic_impact_analysis",
            "impact": analysis,
            "risk_level": self._calculate_change_risk(analysis),
        }

    async def _extract_entities_from_file(self, file_path: str) -> List[str]:
        entities: List[str] = []
        try:
            content = Path(file_path).read_text(encoding="utf-8")
        except OSError:
            return entities

        entities.extend(re.findall(r"class\s+(\w+)", content))
        entities.extend(re.findall(r"def\s+(\w+)", content))
        return entities

    async def _analyze_entity_usage(self, entities: List[str], index_name: str) -> Dict[str, Any]:
        usage = {"affected_functions": [], "affected_classes": [], "usage_count": 0}
        for entity in entities:
            query = f"usage of {entity}, calls to {entity}, references to {entity}"
            result = await self._search(index_name, query, 5)
            if result.get("status") != "success":
                continue

            answer = result.get("results", "")
            usage["usage_count"] += len(answer)
            if "def " in answer or "function" in answer.lower():
                usage["affected_functions"].append(entity)
            if "class " in answer:
                usage["affected_classes"].append(entity)
        return usage

    def _calculate_change_risk(self, impact: Dict[str, Any]) -> str:
        total_affected = len(impact.get("affected_functions", [])) + len(impact.get("affected_classes", []))
        usage_count = impact.get("usage_count", 0)

        if total_affected > 10 or usage_count > 20:
            return "high"
        if total_affected > 5 or usage_count > 10:
            return "medium"
        return "low"
