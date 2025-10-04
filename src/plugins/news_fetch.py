"""Simple HTTP-based news fetcher that bypasses browser automation."""

import httpx
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from datetime import datetime


class NewsFetchPlugin:
    """Fetch news using simple HTTP requests (no browser needed)."""
    
    def __init__(self):
        self.timeout = 30
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
    async def fetch_rss_feed(self, url: str) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers={'User-Agent': self.user_agent},
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    return []
                
                # Parse RSS XML
                root = ET.fromstring(response.text)
                items = []
                
                # Try RSS 2.0 format
                for item in root.findall('.//item')[:10]:
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')
                    pub_date = item.find('pubDate')
                    
                    items.append({
                        'title': title.text if title is not None else '',
                        'url': link.text if link is not None else '',
                        'description': description.text if description is not None else '',
                        'published': pub_date.text if pub_date is not None else ''
                    })
                
                return items
                
        except Exception as e:
            return []
    
    async def get_news(self, topic: str = 'ai', max_articles: int = 5) -> Dict[str, Any]:
        """Fetch news from RSS feeds without browser."""
        
        # RSS feeds by topic (no browser automation needed!)
        feeds = {
            'ai': [
                ('TechCrunch AI', 'https://techcrunch.com/category/artificial-intelligence/feed/'),
                ('VentureBeat AI', 'https://venturebeat.com/category/ai/feed/'),
                ('The Verge AI', 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml')
            ],
            'tech': [
                ('TechCrunch', 'https://techcrunch.com/feed/'),
                ('The Verge', 'https://www.theverge.com/rss/index.xml'),
                ('Ars Technica', 'https://arstechnica.com/feed/')
            ],
            'general': [
                ('BBC News', 'https://feeds.bbci.co.uk/news/rss.xml'),
                ('Reuters', 'https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best')
            ],
            'robotics': [
                ('Robotics Business Review', 'https://www.roboticsbusinessreview.com/feed/'),
                ('IEEE Spectrum Robotics', 'https://spectrum.ieee.org/rss/topic/robotics'),
                ('Robotics.org', 'https://www.robotics.org/rss/news'),
                ('The Robot Report', 'https://www.therobotreport.com/feed/'),
                ('Robohub', 'https://robohub.org/feed/')
            ],
            'washington_dc': [
                ('Washington Post', 'https://feeds.washingtonpost.com/rss/local'),
                ('DCist', 'https://dcist.com/feed/'),
                ('WTOP News', 'https://wtop.com/feed/')
            ],
            'new_york': [
                ('NY Times', 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml'),
                ('Gothamist', 'https://gothamist.com/feed'),
                ('NY Post', 'https://nypost.com/feed/')
            ],
            'california': [
                ('LA Times', 'https://www.latimes.com/local/rss2.0.xml'),
                ('SF Chronicle', 'https://www.sfchronicle.com/rss/'),
                ('CalMatters', 'https://calmatters.org/feed/')
            ],
            'st_louis': [
                ('St. Louis Post-Dispatch', 'https://www.stltoday.com/news/feed/'),
                ('STL Today', 'https://www.stltoday.com/sports/feed/'),
                ('KSDK News', 'https://www.ksdk.com/news/feed/'),
                ('KMOV News', 'https://www.kmov.com/news/feed/'),
                ('St. Louis American', 'https://www.stlamerican.com/feed/')
            ],
            'miami': [
                ('Miami Herald', 'https://www.miamiherald.com/news/feed/'),
                ('WPLG Local 10', 'https://www.local10.com/feed/'),
                ('WSVN News', 'https://www.wsvn.com/feed/'),
                ('Miami New Times', 'https://www.miaminewtimes.com/rss.xml'),
                ('WFOR News', 'https://www.cbsnews.com/miami/')
            ],
            'seattle': [
                ('The Seattle Times', 'https://www.seattletimes.com/feed/'),
                ('KOMO News', 'https://komonews.com/feed'),
                ('KING 5', 'https://www.king5.com/feeds/syndication/rss/news'),
                ('Seattle PI', 'https://www.seattlepi.com/rss/feed/'),
                ('Crosscut', 'https://crosscut.com/rss.xml')
            ],
            'kansas_city': [
                ('Kansas City Star', 'https://www.kansascity.com/news/feed/'),
                ('KSHB 41', 'https://www.kshb.com/news/feed'),
                ('FOX 4 KC', 'https://fox4kc.com/feed/')
            ],
            'dallas': [
                ('Dallas Morning News', 'https://www.dallasnews.com/feed/'),
                ('WFAA', 'https://www.wfaa.com/feeds/syndication/rss/news/local'),
                ('Dallas Observer', 'https://www.dallasobserver.com/rss.xml')
            ],
            'houston': [
                ('Houston Chronicle', 'https://www.houstonchronicle.com/rss/feed/'),
                ('KHOU 11', 'https://www.khou.com/feeds/syndication/rss/news/local'),
                ('Houston Press', 'https://www.houstonpress.com/rss.xml')
            ],
            'chicago': [
                ('Chicago Tribune', 'https://www.chicagotribune.com/feed/'),
                ('Chicago Sun-Times', 'https://chicago.suntimes.com/feeds/rss/homepage'),
                ('Block Club Chicago', 'https://blockclubchicago.org/feed/')
            ],
            'boston': [
                ('Boston Globe', 'https://www.bostonglobe.com/rss/'),
                ('Boston Herald', 'https://www.bostonherald.com/feed/'),
                ('WBUR', 'https://www.wbur.org/feed/')
            ],
            'philadelphia': [
                ('Philadelphia Inquirer', 'https://www.inquirer.com/arc/outboundfeeds/news/?outputType=xml'),
                ('Billy Penn', 'https://billypenn.com/feed/'),
                ('WHYY', 'https://whyy.org/feed/')
            ],
            'atlanta': [
                ('Atlanta Journal-Constitution', 'https://www.ajc.com/feed/'),
                ('11Alive', 'https://www.11alive.com/feeds/syndication/rss/news/local'),
                ('Atlanta Magazine', 'https://www.atlantamagazine.com/feed/')
            ],
            'phoenix': [
                ('Arizona Republic', 'https://www.azcentral.com/feed/'),
                ('12 News', 'https://www.12news.com/feeds/syndication/rss/news/local'),
                ('Phoenix New Times', 'https://www.phoenixnewtimes.com/rss.xml')
            ],
            'denver': [
                ('Denver Post', 'https://www.denverpost.com/feed/'),
                ('9News', 'https://www.9news.com/feeds/syndication/rss/news/local'),
                ('Denverite', 'https://denverite.com/feed/')
            ],
            'portland': [
                ('The Oregonian', 'https://www.oregonlive.com/arc/outboundfeeds/rss/'),
                ('Portland Tribune', 'https://pamplinmedia.com/portland-tribune/feed'),
                ('OPB', 'https://www.opb.org/news/feed/')
            ],
            'detroit': [
                ('Detroit Free Press', 'https://www.freep.com/feed/'),
                ('Detroit News', 'https://www.detroitnews.com/rss/'),
                ('WDIV', 'https://www.clickondetroit.com/feeds/syndication/rss/news/local')
            ],
            'minneapolis': [
                ('Star Tribune', 'https://www.startribune.com/local/index.rss2'),
                ('MPR News', 'https://www.mprnews.org/rss/news'),
                ('KARE 11', 'https://www.kare11.com/feeds/syndication/rss/news/local')
            ],
            'nashville': [
                ('Tennessean', 'https://www.tennessean.com/feed/'),
                ('WSMV', 'https://www.wsmv.com/news/feed/'),
                ('Nashville Scene', 'https://www.nashvillescene.com/feed/')
            ],
            'las_vegas': [
                ('Las Vegas Review-Journal', 'https://www.reviewjournal.com/feed/'),
                ('KTNV', 'https://www.ktnv.com/news/feed'),
                ('Las Vegas Sun', 'https://lasvegassun.com/feeds/rss/')
            ]
        }
        
        # Location mapping for better city/state detection
        # Order matters! More specific matches first
        location_mapping = {
            # Seattle/Washington State (must come before general "washington")
            'seattle': 'seattle',
            'seattle washington': 'seattle',
            'washington state': 'seattle',
            # St. Louis
            'st. louis': 'st_louis',
            'st louis': 'st_louis',
            'saint louis': 'st_louis',
            # Miami
            'miami': 'miami',
            'miami florida': 'miami',
            'florida miami': 'miami',
            # Washington DC (after Seattle checks)
            'washington dc': 'washington_dc',
            'washington d.c.': 'washington_dc',
            'dc': 'washington_dc',
            # New York
            'new york': 'new_york',
            'nyc': 'new_york',
            'newyork': 'new_york',
            # California
            'california': 'california',
            'cali': 'california',
            'los angeles': 'california',
            'la': 'california',
            'sf': 'california',
            'san francisco': 'california',
            # Kansas City
            'kansas city': 'kansas_city',
            'kc': 'kansas_city',
            # Dallas
            'dallas': 'dallas',
            'dallas texas': 'dallas',
            # Houston
            'houston': 'houston',
            'houston texas': 'houston',
            # Chicago
            'chicago': 'chicago',
            'chicago illinois': 'chicago',
            # Boston
            'boston': 'boston',
            'boston massachusetts': 'boston',
            # Philadelphia
            'philadelphia': 'philadelphia',
            'philly': 'philadelphia',
            # Atlanta
            'atlanta': 'atlanta',
            'atlanta georgia': 'atlanta',
            # Phoenix
            'phoenix': 'phoenix',
            'phoenix arizona': 'phoenix',
            # Denver
            'denver': 'denver',
            'denver colorado': 'denver',
            # Portland
            'portland': 'portland',
            'portland oregon': 'portland',
            # Detroit
            'detroit': 'detroit',
            'detroit michigan': 'detroit',
            # Minneapolis
            'minneapolis': 'minneapolis',
            'twin cities': 'minneapolis',
            # Nashville
            'nashville': 'nashville',
            'nashville tennessee': 'nashville',
            # Las Vegas
            'las vegas': 'las_vegas',
            'vegas': 'las_vegas'
        }
        
        # Topic mapping for general topics
        topic_mapping = {
            'robotics': 'robotics',
            'robot': 'robotics',
            'ai': 'ai',
            'artificial intelligence': 'ai',
            'machine learning': 'ai',
            'tech': 'tech',
            'technology': 'tech',
            'general': 'general',
            'news': 'general'
        }
        
        # Normalize topic and detect mappings
        normalized_topic = topic.lower().strip()
        detected_feed = None
        
        # Check for location or topic matches
        for key, feed_key in {**location_mapping, **topic_mapping}.items():
            if key in normalized_topic:
                detected_feed = feed_key
                break
        
        # Use detected feed or fallback
        if detected_feed:
            topic_feeds = feeds.get(detected_feed, feeds['general'])
        else:
            topic_feeds = feeds.get('general', feeds['tech'])
        
        results = []
        errors = []
        
        for source_name, feed_url in topic_feeds:
            try:
                articles = await self.fetch_rss_feed(feed_url)
                
                if articles:
                    results.append({
                        'source': source_name,
                        'feed_url': feed_url,
                        'articles': articles[:max_articles],
                        'count': len(articles)
                    })
                    break  # Got results, stop trying
                    
            except Exception as e:
                errors.append(f"{source_name}: {str(e)}")
                continue
        
        # Format results for easy reading
        formatted_articles = []
        if results:
            for result in results:
                for article in result['articles']:
                    formatted_articles.append({
                        'headline': article['title'],
                        'url': article['url'],
                        'summary': article['description'][:200] if article['description'] else '',
                        'published': article['published']
                    })
        
        return {
            "topic": topic,
            "articles": formatted_articles,
            "sources_tried": len(topic_feeds),
            "successful": len(results),
            "errors": errors if not results else [],
            "method": "rss_feed",
            "note": "Using RSS feeds to bypass browser automation blocks"
        }


# Singleton instance
_news_instance: Optional['NewsFetchPlugin'] = None


def get_news_fetch() -> NewsFetchPlugin:
    """Get or create news fetch instance."""
    global _news_instance
    if not _news_instance:
        _news_instance = NewsFetchPlugin()
    return _news_instance


# MCP Plugin Interface
async def execute(server: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute news fetch plugin commands via MCP interface."""
    try:
        news_fetch = get_news_fetch()

        # Handle MCP-configured tool names
        if tool_name == 'get-news':
            return await news_fetch.get_news(
                topic=args.get('topic', 'general'),
                max_articles=args.get('max_articles', 5)
            )

        # Legacy/backward compatibility
        elif tool_name == 'fetch_topic_news':
            return await news_fetch.get_news(
                topic=args.get('topic', 'general'),
                max_articles=args.get('limit', 5)
            )

        else:
            return {"status": "error", "error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        return {"status": "error", "error": str(e)}
