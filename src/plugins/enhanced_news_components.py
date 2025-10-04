"""
Enhanced News System with Dynamic Discovery, Intelligent Processing, and Rich Artifacts
"""

import asyncio
import json
import re
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import html

from .news_fetch import get_news_fetch
from .browser import get_browser
from .search import get_search_plugin

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass
class NewsSource:
    """Represents a news source with credibility metrics."""
    name: str
    url: str
    rss_url: Optional[str]
    domain: str
    credibility_score: float
    last_updated: datetime
    article_count: int = 0
    topics: List[str] = None

    def __post_init__(self):
        if self.topics is None:
            self.topics = []


@dataclass
class NewsArticle:
    """Enhanced news article with intelligent processing."""
    headline: str
    url: str
    summary: str
    published_date: Optional[datetime]
    source: NewsSource
    key_points: List[str]
    entities: List[str]
    sentiment_score: float
    credibility_score: float
    content_hash: str


class DynamicSourceDiscovery:
    """Dynamically discover relevant news sources using search."""

    def __init__(self, search_plugin):
        self.search = search_plugin
        self.discovered_sources = {}
        self.source_cache_ttl = 3600  # 1 hour cache

    async def discover_sources(self, topic: str, max_sources: int = 10) -> List[NewsSource]:
        """Discover relevant news sources for a topic using search."""

        # Check cache first
        cache_key = f"sources_{topic}"
        if cache_key in self.discovered_sources:
            cached_time, sources = self.discovered_sources[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self.source_cache_ttl):
                logger.info('enhanced_news.source_discovery.cached', extra={'topic': topic, 'count': len(sources)})
                return sources

        logger.info('enhanced_news.source_discovery.start', extra={'topic': topic, 'max_sources': max_sources})

        # Search for authoritative sources
        search_queries = [
            f'"{topic}" news site',
            f'"{topic}" official source',
            f'"{topic}" authoritative news',
            f'"{topic}" reputable source'
        ]

        discovered_domains = set()
        potential_sources = []

        for query in search_queries:
            try:
                search_results = await self.search.web_search(query, num_results=20)

                for result in search_results.get('results', [])[:10]:
                    url = result.get('url', '')
                    if not url:
                        continue

                    domain = urlparse(url).netloc.lower()
                    if domain in discovered_domains:
                        continue

                    discovered_domains.add(domain)

                    # Assess domain credibility
                    credibility = await self._assess_domain_credibility(domain, topic)

                    if credibility > 0.3:  # Minimum credibility threshold
                        source = NewsSource(
                            name=self._extract_site_name(domain),
                            url=f"https://{domain}",
                            domain=domain,
                            credibility_score=credibility,
                            last_updated=datetime.now(),
                            topics=[topic]
                        )

                        potential_sources.append(source)

                        if len(potential_sources) >= max_sources:
                            break

                if len(potential_sources) >= max_sources:
                    break

            except Exception as e:
                logger.warning('enhanced_news.source_search_failed', extra={'query': query, 'error': str(e)})
                continue

        # Sort by credibility and cache
        potential_sources.sort(key=lambda x: x.credibility_score, reverse=True)
        selected = potential_sources[:max_sources]
        self.discovered_sources[cache_key] = (datetime.now(), selected)

        logger.info('enhanced_news.source_discovery.completed', extra={'topic': topic, 'count': len(selected)})
        return selected

    async def _assess_domain_credibility(self, domain: str, topic: str) -> float:
        """Assess domain credibility based on various factors."""
        score = 0.0

        # Known reputable domains
        reputable_domains = {
            'nytimes.com': 0.95,
            'washingtonpost.com': 0.95,
            'wsj.com': 0.95,
            'bbc.com': 0.95,
            'reuters.com': 0.95,
            'apnews.com': 0.95,
            'cnn.com': 0.85,
            'nbcnews.com': 0.85,
            'abcnews.go.com': 0.85,
            'cbsnews.com': 0.85,
            'usatoday.com': 0.80,
            'latimes.com': 0.80,
            'chicagotribune.com': 0.80,
            'bostonglobe.com': 0.80,
            'theguardian.com': 0.90,
            'aljazeera.com': 0.85,
            'dw.com': 0.85,
            'france24.com': 0.85,
            'techcrunch.com': 0.85,
            'arstechnica.com': 0.85,
            'theverge.com': 0.85,
            'venturebeat.com': 0.80,
            'axios.com': 0.80,
            'politico.com': 0.85,
            'bloomberg.com': 0.90,
            'economist.com': 0.90,
            'forbes.com': 0.80,
            'fortune.com': 0.80,
            'time.com': 0.85,
            'newsweek.com': 0.75,
            'npr.org': 0.90,
            'pbs.org': 0.90,
            'propublica.org': 0.90,
            'motherjones.com': 0.80,
            'slate.com': 0.80,
            'vox.com': 0.80,
            'buzzfeednews.com': 0.75,
            'huffpost.com': 0.75,
            'vice.com': 0.75,
            'qz.com': 0.75,
            'fastcompany.com': 0.75,
            'mashable.com': 0.70,
            'gizmodo.com': 0.70,
            'engadget.com': 0.75,
            'cnet.com': 0.75,
            'zdnet.com': 0.75,
            'pcmag.com': 0.75,
            'wired.com': 0.85,
            'technologyreview.com': 0.85,
            'spectrum.ieee.org': 0.85,
            'nature.com': 0.95,
            'science.org': 0.95,
            'scientificamerican.com': 0.85,
            'popsci.com': 0.75,
            'discovermagazine.com': 0.75
        }

        if domain in reputable_domains:
            return reputable_domains[domain]

        # Generic credibility assessment
        if domain.endswith('.edu'):
            score += 0.8
        elif domain.endswith('.gov'):
            score += 0.9
        elif domain.endswith('.org'):
            score += 0.6

        # Length indicates seriousness
        if len(domain) > 10:
            score += 0.1

        # Avoid obviously fake domains
        fake_indicators = ['fake', 'hoax', 'satire', 'joke', 'meme']
        if any(indicator in domain for indicator in fake_indicators):
            score -= 0.5

        return min(score, 0.7)  # Cap at 0.7 for unknown domains

    def _extract_site_name(self, domain: str) -> str:
        """Extract a readable site name from domain."""
        # Remove www and common TLDs
        name = domain.replace('www.', '').split('.')[0]
        return name.title()


class ContentIntelligence:
    """Intelligent content processing and analysis."""

    def __init__(self):
        # Simple patterns for entity extraction (can be enhanced with NLP libraries)
        self.entity_patterns = {
            'organizations': re.compile(r'\b([A-Z][a-z]+ (?:Inc|Corp|Ltd|LLC|Corporation|Company|University|Institute|Foundation|Center|Lab|Laboratory))\b'),
            'people': re.compile(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b'),
            'locations': re.compile(r'\b([A-Z][a-z]+, [A-Z]{2}|[A-Z][a-z]+ (?:City|State|County|Country))\b')
        }

    def extract_key_points(self, text: str) -> List[str]:
        """Extract key points from article text."""
        if not text:
            return []

        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        # Score sentences by importance indicators
        scored_sentences = []
        for sentence in sentences[:20]:  # Limit to first 20 sentences
            score = 0

            # Length bonus (not too short, not too long)
            if 50 < len(sentence) < 200:
                score += 1

            # Key phrase indicators
            key_phrases = [
                'announced', 'revealed', 'discovered', 'found that',
                'according to', 'research shows', 'study finds',
                'new study', 'researchers', 'scientists', 'experts',
                'important', 'significant', 'major', 'breakthrough',
                'according to a new', 'has been', 'will be'
            ]

            for phrase in key_phrases:
                if phrase.lower() in sentence.lower():
                    score += 2

            # Quote indicators
            if '"' in sentence or "'" in sentence:
                score += 1

            # Number indicators (statistics)
            if re.search(r'\d+%|\d+ million|\d+ billion|\$[\d,]+', sentence):
                score += 2

            scored_sentences.append((sentence, score))

        # Return top sentences by score
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        return [sentence for sentence, score in scored_sentences[:5] if score > 0]

    def extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text."""
        entities = set()

        for entity_type, pattern in self.entity_patterns.items():
            matches = pattern.findall(text)
            entities.update(matches)

        return list(entities)[:10]  # Limit to top 10

    def assess_sentiment(self, text: str) -> float:
        """Simple sentiment analysis (-1 to 1)."""
        if not text:
            return 0.0

        text_lower = text.lower()
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'positive', 'success', 'successful', 'achievement', 'progress',
            'breakthrough', 'advance', 'improvement', 'benefit', 'win',
            'triumph', 'victory', 'hope', 'optimistic', 'promising'
        ]

        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'disaster', 'failure',
            'negative', 'problem', 'issue', 'concern', 'worry', 'fear',
            'danger', 'risk', 'threat', 'loss', 'defeat', 'crisis',
            'disappointing', 'unfortunately', 'sadly', 'regrettably'
        ]

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        total_words = len(text.split())
        if total_words == 0:
            return 0.0

        # Normalize by text length
        positive_score = positive_count / total_words
        negative_score = negative_count / total_words

        return (positive_score - negative_score) * 10  # Scale up

    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate a concise summary."""
        if not text:
            return ""

        # Simple extractive summarization
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]

        if not sentences:
            return text[:max_length]

        # Score sentences for summary inclusion
        scored_sentences = []
        for sentence in sentences[:10]:  # First 10 sentences
            score = 0

            # Prefer sentences with key information
            if any(word in sentence.lower() for word in ['is', 'are', 'was', 'were', 'has', 'have', 'had']):
                score += 1

            # Prefer longer sentences (more content)
            if len(sentence) > 50:
                score += 1

            # Prefer sentences with quotes or numbers
            if '"' in sentence or re.search(r'\d', sentence):
                score += 1

            scored_sentences.append((sentence, score))

        # Select top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        summary_sentences = [sentence for sentence, score in scored_sentences[:3] if score > 0]

        summary = '. '.join(summary_sentences)
        if len(summary) > max_length:
            summary = summary[:max_length-3] + '...'

        return summary


class NewsAggregator:
    """Multi-source news aggregation with intelligent processing."""

    def __init__(self):
        self.news_fetch = None
        self.browser = None
        self.search = None
        self.source_discovery = None
        self.content_intelligence = None

    async def initialize(self):
        """Initialize all components."""
        self.news_fetch = get_news_fetch()
        self.browser = await get_browser(headless=True)
        self.search = await get_search_plugin()
        self.source_discovery = DynamicSourceDiscovery(self.search)
        self.content_intelligence = ContentIntelligence()

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

        dashboard_html = self._generate_news_dashboard(enhanced_articles, topic, sources)
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

    async def _enhance_article(self, article: NewsArticle, topic: str) -> Optional[Dict]:
        """Further enhance article with additional processing."""
        try:
            # Generate smart summary if original is too short
            if len(article.summary) < 100:
                article.summary = self.content_intelligence.generate_summary(
                    f"{article.headline}. {article.summary}",
                    max_length=150
                )

            return asdict(article)

        except Exception as e:
            logger.exception('enhanced_news.article_enhancement_error', extra={'url': article.url, 'error': str(e)})
            return asdict(article)

    def _generate_news_dashboard(self, articles: List[NewsArticle], topic: str, sources: List[NewsSource]) -> str:
        """Generate rich HTML dashboard for news articles."""

        # Convert articles to dict for easier processing
        article_dicts = [asdict(article) for article in articles]

        # Sort articles by credibility and recency
        article_dicts.sort(key=lambda x: (
            x['credibility_score'],
            x['published_date'] if x['published_date'] else ''
        ), reverse=True)

        # Generate source credibility indicators
        source_badges = []
        for source in sources[:8]:  # Top 8 sources
            credibility_level = "high" if source.credibility_score > 0.8 else "medium" if source.credibility_score > 0.6 else "low"
            source_badges.append(f"""
                <span class="source-badge credibility-{credibility_level}" title="{source.name} (Credibility: {source.credibility_score:.2f})">
                    {source.name}
                </span>
            """)

        # Generate articles HTML
        articles_html = []
        for i, article in enumerate(article_dicts):
            # Format date
            date_str = "Recently"
            if article['published_date']:
                try:
                    date_obj = datetime.fromisoformat(article['published_date'].replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%B %d, %Y at %I:%M %p")
                except:
                    pass

            # Key points
            key_points_html = ""
            if article['key_points']:
                key_points_html = """
                    <div class="key-points">
                        <h4>Key Points:</h4>
                        <ul>
                """
                for point in article['key_points'][:3]:
                    key_points_html += f"<li>{html.escape(point)}</li>"
                key_points_html += "</ul></div>"

            # Entities
            entities_html = ""
            if article['entities']:
                entities_html = """
                    <div class="entities">
                        <h4>Entities:</h4>
                        <div class="entity-tags">
                """
                for entity in article['entities'][:5]:
                    entities_html += f'<span class="entity-tag">{html.escape(entity)}</span>'
                entities_html += "</div></div>"

            # Sentiment indicator
            sentiment_class = "positive" if article['sentiment_score'] > 0.1 else "negative" if article['sentiment_score'] < -0.1 else "neutral"
            sentiment_text = f"{article['sentiment_score']:.2f}"

            articles_html.append(f"""
                <div class="news-article" data-credibility="{article['credibility_score']}" data-sentiment="{article['sentiment_score']}">
                    <div class="article-header">
                        <h3><a href="{article['url']}" target="_blank">{html.escape(article['headline'])}</a></h3>
                        <div class="article-meta">
                            <span class="source">{html.escape(article['source']['name'])}</span>
                            <span class="date">{date_str}</span>
                            <span class="credibility-badge">Credibility: {article['credibility_score']:.2f}</span>
                            <span class="sentiment-badge sentiment-{sentiment_class}">Sentiment: {sentiment_text}</span>
                        </div>
                    </div>
                    <div class="article-content">
                        <p class="summary">{html.escape(article['summary'])}</p>
                        {key_points_html}
                        {entities_html}
                    </div>
                    <div class="article-footer">
                        <a href="{article['url']}" target="_blank" class="read-more">Read Full Article →</a>
                    </div>
                </div>
            """)

        # Generate complete HTML dashboard
        html_dashboard = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Enhanced News Dashboard - {html.escape(topic.title())}</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: #f5f5f5;
                }}

                .dashboard-header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 2rem;
                    text-align: center;
                }}

                .dashboard-header h1 {{
                    font-size: 2.5rem;
                    margin-bottom: 0.5rem;
                }}

                .dashboard-header .subtitle {{
                    opacity: 0.9;
                    font-size: 1.1rem;
                }}

                .sources-section {{
                    background: white;
                    padding: 1.5rem;
                    margin: 2rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}

                .sources-section h2 {{
                    color: #333;
                    margin-bottom: 1rem;
                }}

                .source-badges {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                }}

                .source-badge {{
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.85rem;
                    font-weight: 500;
                }}

                .credibility-high {{ background: #d4edda; color: #155724; }}
                .credibility-medium {{ background: #fff3cd; color: #856404; }}
                .credibility-low {{ background: #f8d7da; color: #721c24; }}

                .controls-section {{
                    background: white;
                    padding: 1.5rem;
                    margin: 0 2rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}

                .controls {{
                    display: flex;
                    gap: 1rem;
                    align-items: center;
                    flex-wrap: wrap;
                }}

                .control-group {{
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }}

                .control-group label {{
                    font-weight: 500;
                    color: #555;
                }}

                .control-group select {{
                    padding: 0.5rem;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    font-size: 0.9rem;
                }}

                .articles-section {{
                    padding: 2rem;
                }}

                .articles-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 2rem;
                    margin-top: 1rem;
                }}

                .news-article {{
                    background: white;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    transition: transform 0.2s, box-shadow 0.2s;
                }}

                .news-article:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                }}

                .article-header {{
                    padding: 1.5rem;
                    border-bottom: 1px solid #eee;
                }}

                .article-header h3 {{
                    margin-bottom: 0.75rem;
                }}

                .article-header h3 a {{
                    color: #2c3e50;
                    text-decoration: none;
                }}

                .article-header h3 a:hover {{
                    color: #3498db;
                }}

                .article-meta {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 1rem;
                    font-size: 0.85rem;
                    color: #666;
                }}

                .credibility-badge, .sentiment-badge {{
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    font-weight: 500;
                }}

                .sentiment-positive {{ background: #d4edda; color: #155724; }}
                .sentiment-negative {{ background: #f8d7da; color: #721c24; }}
                .sentiment-neutral {{ background: #e2e3e5; color: #383d41; }}

                .article-content {{
                    padding: 1.5rem;
                }}

                .summary {{
                    margin-bottom: 1rem;
                    color: #555;
                }}

                .key-points, .entities {{
                    margin-top: 1rem;
                }}

                .key-points h4, .entities h4 {{
                    font-size: 0.9rem;
                    color: #333;
                    margin-bottom: 0.5rem;
                }}

                .key-points ul {{
                    list-style: none;
                    padding-left: 0;
                }}

                .key-points li {{
                    padding: 0.25rem 0;
                    padding-left: 1rem;
                    position: relative;
                }}

                .key-points li:before {{
                    content: "•";
                    color: #667eea;
                    font-weight: bold;
                    position: absolute;
                    left: 0;
                }}

                .entity-tags {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                }}

                .entity-tag {{
                    background: #e3f2fd;
                    color: #1976d2;
                    padding: 0.25rem 0.5rem;
                    border-radius: 12px;
                    font-size: 0.8rem;
                }}

                .article-footer {{
                    padding: 1rem 1.5rem;
                    background: #f8f9fa;
                    border-top: 1px solid #eee;
                }}

                .read-more {{
                    color: #667eea;
                    text-decoration: none;
                    font-weight: 500;
                }}

                .read-more:hover {{
                    color: #5a6fd8;
                }}

                .export-controls {{
                    text-align: center;
                    margin: 2rem 0;
                }}

                .export-btn {{
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 0.75rem 1.5rem;
                    border-radius: 6px;
                    cursor: pointer;
                    margin: 0 0.5rem;
                    font-size: 0.9rem;
                    transition: background 0.2s;
                }}

                .export-btn:hover {{
                    background: #5a6fd8;
                }}

                @media (max-width: 768px) {{
                    .dashboard-header h1 {{ font-size: 2rem; }}
                    .articles-grid {{ grid-template-columns: 1fr; }}
                    .controls {{ flex-direction: column; align-items: stretch; }}
                    .source-badges {{ justify-content: center; }}
                }}
            </style>
        </head>
        <body>
            <div class="dashboard-header" data-topic="{html.escape(topic)}">
                <h1>📰 Enhanced News Dashboard</h1>
                <div class="subtitle">Intelligent news aggregation for "{html.escape(topic)}"</div>
                <div class="subtitle">Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</div>
            </div>

            <div class="sources-section">
                <h2>🔍 Sources Used ({len(sources)} authoritative sources)</h2>
                <div class="source-badges">
                    {"".join(source_badges)}
                </div>
            </div>

            <div class="controls-section">
                <h2>⚙️ Filter & Sort Options</h2>
                <div class="controls">
                    <div class="control-group">
                        <label for="sort-by">Sort by:</label>
                        <select id="sort-by">
                            <option value="credibility">Credibility Score</option>
                            <option value="date">Publication Date</option>
                            <option value="sentiment">Sentiment</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label for="filter-sentiment">Filter by sentiment:</label>
                        <select id="filter-sentiment">
                            <option value="all">All Articles</option>
                            <option value="positive">Positive Only</option>
                            <option value="negative">Negative Only</option>
                            <option value="neutral">Neutral Only</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label for="min-credibility">Min. credibility:</label>
                        <select id="min-credibility">
                            <option value="0">All Sources</option>
                            <option value="0.7">High Credibility (0.7+)</option>
                            <option value="0.8">Very High (0.8+)</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="articles-section">
                <h2>🗞️ Latest Articles ({len(article_dicts)} found)</h2>
                <div class="articles-grid" id="articles-container">
                    {"".join(articles_html)}
                </div>
            </div>

            <div class="export-controls">
                <button class="export-btn" onclick="exportToJSON()">📄 Export to JSON</button>
                <button class="export-btn" onclick="exportToCSV()">📊 Export to CSV</button>
                <button class="export-btn" onclick="printDashboard()">🖨️ Print Dashboard</button>
                <button class="export-btn" onclick="shareDashboard()">📤 Share Dashboard</button>
            </div>

            <script>
                // Simple filtering and sorting functionality
                const articlesContainer = document.getElementById('articles-container');
                const articles = Array.from(articlesContainer.children);

                function applyFilters() {{
                    const sortBy = document.getElementById('sort-by').value;
                    const filterSentiment = document.getElementById('filter-sentiment').value;
                    const minCredibility = parseFloat(document.getElementById('min-credibility').value);

                    const filteredArticles = articles.filter(article => {{
                        const credibility = parseFloat(article.dataset.credibility);
                        const sentiment = parseFloat(article.dataset.sentiment);

                        if (credibility < minCredibility) return false;

                        if (filterSentiment !== 'all') {{
                            if (filterSentiment === 'positive' && sentiment <= 0) return false;
                            if (filterSentiment === 'negative' && sentiment >= 0) return false;
                            if (filterSentiment === 'neutral' && Math.abs(sentiment) > 0.1) return false;
                        }}

                        return true;
                    }});

                    // Sort articles
                    filteredArticles.sort((a, b) => {{
                        const aCred = parseFloat(a.dataset.credibility);
                        const bCred = parseFloat(b.dataset.credibility);
                        const aSent = parseFloat(a.dataset.sentiment);
                        const bSent = parseFloat(b.dataset.sentiment);

                        switch (sortBy) {{
                            case 'credibility':
                                return bCred - aCred;
                            case 'sentiment':
                                return bSent - aSent;
                            default:
                                return 0;
                        }}
                    }});

                    // Update display
                    articlesContainer.innerHTML = '';
                    filteredArticles.forEach(article => articlesContainer.appendChild(article));
                }}

                // Add event listeners
                document.getElementById('sort-by').addEventListener('change', applyFilters);
                document.getElementById('filter-sentiment').addEventListener('change', applyFilters);
                document.getElementById('min-credibility').addEventListener('change', applyFilters);

                // Export functions
                function exportToJSON() {{
                    const articlesData = {json.dumps(article_dicts)};
                    const data = {{topic: "{html.escape(topic)}", articles: articlesData}};
                    const blob = new Blob([JSON.stringify(data, null, 2)], {{"type": "application/json"}});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'news-dashboard-{html.escape(topic.lower().replace(" ","-"))}.json';
                    a.click();
                    URL.revokeObjectURL(url);
                }}

                function exportToCSV() {{
                    let csv = 'Headline,URL,Source,Summary,Credibility,Sentiment\\n';
                    const articlesData = {json.dumps(article_dicts)};
                    articlesData.forEach(article => {{
                        csv += `"${{article.headline.replace(/"/g, '""')}}","${{article.url}}","${{article.source.name}}","${{article.summary.replace(/"/g, '""')}}",${{article.credibility_score}},${{article.sentiment_score}}\\n`;
                    }});
                    const blob = new Blob([csv], {{"type": "text/csv"}});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'news-dashboard-{html.escape(topic.lower().replace(" ","-"))}.csv';
                    a.click();
                    URL.revokeObjectURL(url);
                }}

                function printDashboard() {{
                    window.print();
                }}

                function shareDashboard() {{
                    const dashboardTitle = 'Enhanced News Dashboard - {html.escape(topic)}';
                    const dashboardText = 'Check out this intelligent news aggregation for {html.escape(topic)}';
                    if (navigator.share) {{
                        navigator.share({{
                            title: dashboardTitle,
                            text: dashboardText,
                            url: window.location.href
                        }});
                    }} else {{
                        // Fallback: copy URL to clipboard
                        navigator.clipboard.writeText(window.location.href);
                        alert('Dashboard URL copied to clipboard!');
                    }}
                }}

                // Apply initial filters
                applyFilters();
            </script>
        </body>
        </html>
        """

        return html_dashboard

