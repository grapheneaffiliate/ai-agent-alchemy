from __future__ import annotations

"""Question routing helper for LEANN fallback flows."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, Optional


class QuestionIntent(Enum):
    """Describe the high level intent behind a natural language question."""

    VISIBILITY = auto()
    VERIFY_FIX = auto()
    DIAGNOSTIC = auto()
    IMPROVEMENT = auto()
    ASSESSMENT = auto()
    CAPABILITY = auto()
    PLUGIN_SPECIFIC = auto()
    ARCHITECTURE = auto()
    OVERVIEW = auto()


@dataclass
class QuestionRoute:
    """Structured output describing the detected question intent."""

    intent: QuestionIntent
    plugin_name: Optional[str] = None


class QuestionRouter:
    """Apply lightweight heuristics to map questions to downstream handlers."""

    def __init__(self, plugin_patterns: Optional[Iterable[str]] = None) -> None:
        self._plugin_patterns = tuple(
            plugin_patterns
            or (
                "crawl4ai",
                "leann",
                "browser",
                "search",
                "analysis",
                "news_fetch",
                "time_utils",
                "kokoro_tts",
                "kokoro",
            )
        )

    def classify(self, question: str) -> QuestionRoute:
        """Return a structured description of how the toolkit should respond."""
        normalized = question.lower().strip()

        if self._matches_any(normalized, ("can you see", "do you have access", "do you know")):
            return QuestionRoute(QuestionIntent.VISIBILITY)
        if self._matches_any(normalized, ("check again", "verify", "confirm", "did it work", "is it fixed", "validate")):
            return QuestionRoute(QuestionIntent.VERIFY_FIX)
        if self._matches_any(normalized, ("diagnostic", "diagnose", "debug", "not working", "broken", "fix")):
            return QuestionRoute(QuestionIntent.DIAGNOSTIC)
        if self._matches_any(normalized, ("what changes", "what would you change", "improve", "recommend")):
            return QuestionRoute(QuestionIntent.IMPROVEMENT)
        if self._matches_any(normalized, ("assess", "evaluate", "analysis")):
            return QuestionRoute(QuestionIntent.ASSESSMENT)

        if self._is_capability_question(normalized):
            return QuestionRoute(QuestionIntent.CAPABILITY)

        plugin_name = self._extract_plugin_name(normalized)
        if plugin_name:
            return QuestionRoute(QuestionIntent.PLUGIN_SPECIFIC, plugin_name=plugin_name)

        if "plugin" in normalized or "tool" in normalized:
            return QuestionRoute(QuestionIntent.ARCHITECTURE)

        return QuestionRoute(QuestionIntent.OVERVIEW)

    def _matches_any(self, question: str, keywords: Iterable[str]) -> bool:
        return any(keyword in question for keyword in keywords)

    def _is_capability_question(self, question: str) -> bool:
        keywords = (
            "can you",
            "ability",
            "capable",
            "capability",
            "create plugin",
            "able to",
            "could you",
            "are you able",
            "would you be able",
            "extend yourself",
        )
        return any(keyword in question for keyword in keywords)

    def _extract_plugin_name(self, question: str) -> Optional[str]:
        for pattern in self._plugin_patterns:
            if pattern in question:
                if pattern in {"crawl4ai", "leann", "kokoro"}:
                    return f"{pattern}_plugin"
                return pattern
        return None
