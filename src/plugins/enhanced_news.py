"""Orchestrator for the enhanced news plugin."""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Dict, Optional

from .enhanced_news_components import NewsAggregator

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Global instance
_enhanced_news_instance: Optional[NewsAggregator] = None


async def get_enhanced_news() -> NewsAggregator:
    """Get or create enhanced news instance."""
    global _enhanced_news_instance
    if not _enhanced_news_instance:
        _enhanced_news_instance = NewsAggregator()
        await _enhanced_news_instance.initialize()
        logger.info('enhanced_news.instance.initialized')
    return _enhanced_news_instance


class EnhancedNewsPlugin:
    """MCP Plugin interface for enhanced news functionality."""

    def __init__(self):
        self._aggregator: Optional[NewsAggregator] = None

    async def _get_aggregator(self) -> NewsAggregator:
        """Get or create the aggregator instance."""
        if self._aggregator is None:
            self._aggregator = NewsAggregator()
            await self._aggregator.initialize()
        return self._aggregator

    async def get_enhanced_news(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get enhanced news with semantic analysis."""
        aggregator = await self._get_aggregator()
        return await aggregator.get_enhanced_news(
            topic=args.get('topic', 'ai'),
            max_articles=args.get('max_articles', 10)
        )

    async def discover_sources(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Discover news sources for a topic."""
        aggregator = await self._get_aggregator()
        sources = await aggregator.source_discovery.discover_sources(
            topic=args.get('topic', 'ai'),
            max_sources=args.get('max_sources', 10)
        )
        return {
            "sources": [asdict(source) for source in sources],
            "count": len(sources)
        }


# MCP Plugin Interface
async def execute(server: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute enhanced news plugin commands via MCP interface."""
    try:
        logger.info('enhanced_news.execute', extra={'tool': tool_name})
        enhanced_news = await get_enhanced_news()

        if tool_name == 'get_enhanced_news':
            return await enhanced_news.get_enhanced_news(
                topic=args.get('topic', 'ai'),
                max_articles=args.get('max_articles', 10)
            )

        elif tool_name == 'discover_sources':
            sources = await enhanced_news.source_discovery.discover_sources(
                topic=args.get('topic', 'ai'),
                max_sources=args.get('max_sources', 10)
            )
            return {
                "sources": [asdict(source) for source in sources],
                "count": len(sources)
            }

        else:
            return {"status": "error", "error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        logger.exception('enhanced_news.execute_error', extra={'tool': tool_name})
        return {"status": "error", "error": str(e)}
