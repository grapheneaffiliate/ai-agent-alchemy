from __future__ import annotations

"""Shared news components used by the enhanced news plugin."""

from .sources import DynamicSourceDiscovery, NewsSource
from .intelligence import ContentIntelligence, NewsArticle
from .renderer import NewsRenderer

__all__ = [
    "ContentIntelligence",
    "DynamicSourceDiscovery",
    "NewsArticle",
    "NewsRenderer",
    "NewsSource",
]
