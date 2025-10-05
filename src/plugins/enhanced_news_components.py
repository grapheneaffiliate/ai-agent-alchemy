from __future__ import annotations

"""Enhanced News System with Dynamic Discovery, Intelligent Processing, and Rich Artifacts"""

import asyncio
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from dataclasses import asdict

from .browser import get_browser
from .news import (
    ContentIntelligence,
    DynamicSourceDiscovery,
    NewsArticle,
    NewsRenderer,
    NewsSource,
)
from .news_fetch import get_news_fetch
from .search import get_search_plugin


logger = logging.getLogger(__name__)


logger.addHandler(logging.NullHandler())








class NewsAggregator:


    """Multi-source news aggregation with intelligent processing.





    This is a component class used by other plugins, not an MCP plugin itself.


    It does not need to implement async execute() as it's not directly callable via MCP.


    """





    def __init__(self) -> None:
        self.news_fetch = None
        self.browser = None
        self.search = None
        self.source_discovery: Optional[DynamicSourceDiscovery] | None = None
        self.content_intelligence = ContentIntelligence()
        self.renderer = NewsRenderer()
    async def execute(self, server: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:


        """Stub execute method for analyzer compatibility.





        This component is not a standalone MCP plugin and should not be called directly.


        Use the enhanced_news plugin instead for news aggregation functionality.


        """


        return {


            "status": "error",


            "error": "NewsAggregator is a component class, not a standalone MCP plugin. Use the enhanced_news plugin instead."


        }





    async def initialize(self) -> None:
        """Initialize external helpers required for aggregation."""
        self.news_fetch = get_news_fetch()
        self.browser = await get_browser(headless=True)
        self.search = await get_search_plugin()
        self.source_discovery = DynamicSourceDiscovery(self.search)
    async def get_enhanced_news(self, topic: str, max_articles: int = 10) -> Dict[str, Any]:


        """Get enhanced news with dynamic discovery and intelligent processing."""





        logger.info('enhanced_news.aggregation.start', extra={'topic': topic, 'max_articles': max_articles})





        if not self.news_fetch:


            await self.initialize()





        sources = await self.source_discovery.discover_sources(topic, max_sources=8)


        logger.info('enhanced_news.aggregation.sources', extra={'topic': topic, 'count': len(sources)})





        # Step 2: Fetch articles from multiple sources


        all_articles = []


        source_results = []





        for source in sources:


            logger.debug('enhanced_news.aggregation.fetch_source', extra={'topic': topic, 'source': source.name})


            try:


                # Try RSS first (more reliable)


                if hasattr(self.news_fetch, 'get_news'):


                    rss_results = await self.news_fetch.get_news(topic, max_articles=3)





                    for article in rss_results.get('articles', [])[:2]:


                        enhanced_article = await self._process_article(article, source, topic)


                        if enhanced_article:


                            all_articles.append(enhanced_article)





                # Try browser extraction as backup


                if len(all_articles) < max_articles and self.browser:


                    try:


                        browser_results = await self.browser.get_news_smart(topic, max_articles=2)





                        for result in browser_results.get('results', []):


                            for article_data in result.get('top_articles', []):


                                article = {


                                    'headline': article_data.get('headline', ''),


                                    'url': article_data.get('url', ''),


                                    'summary': result.get('summary', ''),


                                    'published': datetime.now().isoformat()


                                }





                                enhanced_article = await self._process_article(article, source, topic)


                                if enhanced_article:


                                    all_articles.append(enhanced_article)


                    except Exception as e:


                        logger.warning('enhanced_news.browser_extract_failed', extra={'source': source.name, 'error': str(e)})





            except Exception as e:


                logger.warning('enhanced_news.fetch_failed', extra={'source': source.name, 'error': str(e)})


                continue





        # Step 3: Process and enhance articles


        enhanced_articles = []


        for article in all_articles[:max_articles]:


            processed = await self._enhance_article(article, topic)


            if processed:


                enhanced_articles.append(processed)





        dashboard_html = self.renderer.render_dashboard(enhanced_articles, topic, sources)


        logger.info('enhanced_news.aggregation.completed', extra={'topic': topic, 'articles': len(enhanced_articles)})





        return {


            "topic": topic,


            "articles": [asdict(article) for article in enhanced_articles],


            "sources_used": len(sources),


            "articles_found": len(enhanced_articles),


            "dashboard_html": dashboard_html,


            "generated_at": datetime.now().isoformat(),


            "method": "enhanced_multi_source"


        }





    async def _process_article(self, article_data: Dict, source: NewsSource, topic: str) -> Optional[NewsArticle]:


        """Process a single article into enhanced format."""


        try:


            headline = article_data.get('headline', '').strip()


            url = article_data.get('url', '').strip()


            summary = article_data.get('summary', '').strip()





            if not headline or not url:


                return None





            # Parse published date


            published_date = None


            if article_data.get('published'):


                try:


                    published_date = datetime.fromisoformat(article_data['published'].replace('Z', '+00:00'))


                except:


                    published_date = datetime.now()





            # Combine summary with additional content if needed


            full_text = summary


            if len(full_text) < 100 and self.browser:


                try:


                    # Try to get more content from the article URL


                    nav_result = await self.browser.navigate(url)


                    if nav_result.get('status') == 'success':


                        extracted = await self.browser.extract_content_smart()


                        if extracted.get('text'):


                            full_text = extracted['text'][:1000]


                except:


                    pass





            # Apply content intelligence


            key_points = self.content_intelligence.extract_key_points(full_text)


            entities = self.content_intelligence.extract_entities(full_text)


            sentiment_score = self.content_intelligence.assess_sentiment(full_text)





            # Generate content hash for deduplication


            content_hash = hashlib.md5(f"{headline}{url}{summary}".encode()).hexdigest()





            return NewsArticle(


                headline=headline,


                url=url,


                summary=summary,


                published_date=published_date,


                source=source,


                key_points=key_points,


                entities=entities,


                sentiment_score=sentiment_score,


                credibility_score=source.credibility_score,


                content_hash=content_hash


            )





        except Exception as e:


            logger.exception('enhanced_news.article_processing_error', extra={'url': article_data.get('url'), 'error': str(e)})


            return None





    async def _enhance_article(self, article: NewsArticle, topic: str) -> Optional[NewsArticle]:


        """Further enhance article with additional processing."""


        try:


            # Generate smart summary if original is too short


            if len(article.summary) < 100:


                article.summary = self.content_intelligence.generate_summary(


                    f"{article.headline}. {article.summary}",


                    max_length=150


                )





            return article





        except Exception as e:


            logger.exception('enhanced_news.article_enhancement_error', extra={'url': article.url, 'error': str(e)})


            return article





