from __future__ import annotations

"""Content intelligence helpers for enhanced news articles."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .sources import NewsSource

@dataclass
class NewsArticle:
    """Enhanced news article with intelligent processing."""

    headline: str
    url: str
    summary: str
    published_date: Optional[datetime]
    source: "NewsSource"
    key_points: List[str]
    entities: List[str]
    sentiment_score: float
    credibility_score: float
    content_hash: str


class ContentIntelligence:
    """Lightweight NLP helper for extracting structure from article text."""

    def __init__(self) -> None:
        self._entity_patterns = {
            "organizations": re.compile(r"\b([A-Z][a-z]+ (?:Inc|Corp|Ltd|LLC|Corporation|Company|University|Institute|Foundation|Center|Lab|Laboratory))\b"),
            "people": re.compile(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b"),
            "locations": re.compile(r"\b([A-Z][a-z]+, [A-Z]{2}|[A-Z][a-z]+ (?:City|State|County|Country))\b"),
        }

    def extract_key_points(self, text: str) -> List[str]:
        if not text:
            return []

        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        scored: List[tuple[str, int]] = []
        for sentence in sentences[:20]:
            score = 0
            if 50 < len(sentence) < 200:
                score += 1

            key_phrases = [
                "announced",
                "revealed",
                "discovered",
                "found that",
                "according to",
                "research shows",
                "study finds",
                "new study",
                "researchers",
                "scientists",
                "experts",
                "important",
                "significant",
                "major",
                "breakthrough",
                "according to a new",
                "has been",
                "will be",
            ]
            for phrase in key_phrases:
                if phrase.lower() in sentence.lower():
                    score += 2

            if '"' in sentence or "'" in sentence:
                score += 1

            if re.search(r"\d+%|\d+ million|\d+ billion|\$[\d,]+", sentence):
                score += 2

            scored.append((sentence, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [sentence for sentence, score in scored[:5] if score > 0]

    def extract_entities(self, text: str) -> List[str]:
        entities: set[str] = set()
        for pattern in self._entity_patterns.values():
            entities.update(pattern.findall(text))
        return list(entities)[:10]

    def assess_sentiment(self, text: str) -> float:
        if not text:
            return 0.0

        lowered = text.lower()
        positive_words = [
            "good",
            "great",
            "excellent",
            "amazing",
            "wonderful",
            "fantastic",
            "positive",
            "success",
            "successful",
            "achievement",
            "progress",
            "breakthrough",
            "advance",
            "improvement",
            "benefit",
            "win",
            "triumph",
            "victory",
            "hope",
            "optimistic",
            "promising",
        ]
        negative_words = [
            "bad",
            "terrible",
            "awful",
            "horrible",
            "disaster",
            "failure",
            "negative",
            "problem",
            "issue",
            "concern",
            "worry",
            "fear",
            "danger",
            "risk",
            "threat",
            "loss",
            "defeat",
            "crisis",
            "disappointing",
            "unfortunately",
            "sadly",
            "regrettably",
        ]

        positive_count = sum(1 for word in positive_words if word in lowered)
        negative_count = sum(1 for word in negative_words if word in lowered)
        total_words = len(text.split()) or 1
        return (positive_count - negative_count) / total_words * 10

    def generate_summary(self, text: str, max_length: int = 200) -> str:
        if not text:
            return ""

        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        if not sentences:
            return text[:max_length]

        scored: List[tuple[str, int]] = []
        for sentence in sentences[:10]:
            score = 0
            if any(word in sentence.lower() for word in ("is", "are", "was", "were", "has", "have", "had")):
                score += 1
            if len(sentence) > 50:
                score += 1
            if '"' in sentence or re.search(r"\d", sentence):
                score += 1
            scored.append((sentence, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        summary_sentences = [sentence for sentence, score in scored[:3] if score > 0]
        summary = ". ".join(summary_sentences)
        if len(summary) > max_length:
            summary = summary[: max_length - 3] + "..."
        return summary
