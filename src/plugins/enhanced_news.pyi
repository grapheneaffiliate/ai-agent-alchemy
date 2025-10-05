"""Enhanced type stubs for enhanced news plugin."""

from typing import Any, Dict, List, Optional, Protocol, TypedDict
from agent.models import MCPTool
from agent.errors import PluginExecutionError


class NewsArticle(TypedDict):
    """Structured news article data."""
    title: str
    content: str
    url: str
    published_at: str
    source: str
    summary: Optional[str]
    image_url: Optional[str]
    tags: List[str]


class NewsSource(TypedDict):
    """News source information."""
    name: str
    url: str
    reliability_score: float
    last_checked: str
    article_count: int


class SourceDiscovery(Protocol):
    """Protocol for discovering news sources."""

    async def discover_sources(
        self,
        topic: str,
        max_sources: int = 10,
        min_reliability: float = 0.7
    ) -> List[NewsSource]: ...


class NewsProcessor(Protocol):
    """Protocol for processing news content."""

    async def process_article(
        self,
        url: str,
        extract_images: bool = False
    ) -> NewsArticle: ...

    async def generate_summary(
        self,
        content: str,
        max_length: int = 200
    ) -> str: ...


class EnhancedNewsClient(Protocol):
    """Main news client protocol."""

    source_discovery: SourceDiscovery
    processor: NewsProcessor

    async def get_enhanced_news(
        self,
        topic: str,
        max_articles: int = 10,
        include_summaries: bool = True,
        include_images: bool = False
    ) -> List[NewsArticle]: ...

    async def discover_sources(
        self,
        topic: str,
        max_sources: int = 10
    ) -> List[NewsSource]: ...


class NewsAggregator:
    """News aggregation and processing."""

    def __init__(self, client: EnhancedNewsClient): ...

    async def aggregate_by_topic(
        self,
        topics: List[str],
        articles_per_topic: int = 5
    ) -> Dict[str, List[NewsArticle]]: ...

    async def generate_dashboard(
        self,
        articles: List[NewsArticle],
        include_charts: bool = True
    ) -> str: ...


def register_tools() -> List[MCPTool]: ...


async def get_enhanced_news(
    topic: str,
    max_articles: int = 10,
    include_summaries: bool = True
) -> List[NewsArticle]: ...


async def discover_sources(
    topic: str,
    max_sources: int = 10
) -> List[NewsSource]: ...


async def generate_news_dashboard(
    topic: str,
    max_articles: int = 15,
    include_charts: bool = True
) -> str: ...
