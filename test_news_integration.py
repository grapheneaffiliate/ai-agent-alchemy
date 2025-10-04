#!/usr/bin/env python3
"""
Test to verify news fetching integration works end-to-end.
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from plugins.news_fetch import get_news_fetch


async def test_news_integration():
    """Test different news queries."""
    news_fetcher = get_news_fetch()
    
    test_queries = [
        ('general news', 'general'),
        ('robotics news', 'robotics'),
        ('st. louis news', 'st. louis'),
        ('miami news', 'miami')
    ]
    
    print("=" * 70)
    print("NEWS INTEGRATION TEST")
    print("=" * 70)
    
    for query_desc, topic in test_queries:
        print(f"\n📰 Testing: {query_desc}")
        print("-" * 70)
        
        try:
            result = await news_fetcher.get_news(topic=topic, max_articles=5)
            articles = result.get('articles', [])
            
            print(f"✓ Fetched {len(articles)} articles")
            print(f"  Topic: {result.get('topic')}")
            print(f"  Method: {result.get('method')}")
            
            if articles:
                print(f"\n  Headlines:")
                for i, article in enumerate(articles[:3], 1):
                    headline = article.get('headline', 'No headline')
                    print(f"    {i}. {headline}")
                    print(f"       URL: {article.get('url', 'N/A')[:60]}...")
            else:
                print(f"  ⚠️ No articles returned")
                if result.get('errors'):
                    print(f"  Errors: {result['errors']}")
                    
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_news_integration())
