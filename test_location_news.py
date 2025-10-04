#!/usr/bin/env python3
"""
Test script to verify location-based news fetching works correctly.
This tests the fix for the issue where "news in Washington DC" was returning AI news.
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from plugins.news_fetch import get_news_fetch


async def test_news_topics():
    """Test different news topics to verify they return appropriate content."""

    news_fetcher = get_news_fetch()
    topics_to_test = ['ai', 'tech', 'washington_dc', 'new_york', 'california', 'st. louis', 'miami florida']

    print("Testing location-based news fetching...\n")

    for topic in topics_to_test:
        print(f"🔍 Testing topic: {topic}")
        try:
            result = await news_fetcher.get_news(topic=topic, max_articles=3)
            articles = result.get('articles', [])

            print(f"   found {len(articles)} articles")

            if articles:
                for i, article in enumerate(articles[:2], 1):
                    headline = article.get('headline', 'No headline')
                    summary = article.get('summary', 'No summary')[:100]
                    url = article.get('url', 'No URL')
                    print(f"      {i}. {headline}")
                    print(f"         {summary}...")
                    print(f"         URL: {url}")

                # Verify topic-specific content
                if topic == 'washington_dc' and articles:
                    content_check = ' '.join([a['headline'] + a['summary'] for a in articles]).lower()
                    dc_keywords = ['washington', 'dc', 'baltimore', 'maryland', 'virginia', 'capitol', 'congress', 'senate']
                    if any(kw in content_check for kw in dc_keywords):
                        print(f"   ✅ Contains DC-relevant keywords")
                    else:
                        print(f"   ❌ No DC-relevant keywords found")
                
                # Verify St. Louis content
                elif 'st. louis' in topic.lower() and articles:
                    content_check = ' '.join([a['headline'] + a['summary'] for a in articles]).lower()
                    stl_keywords = ['st. louis', 'st louis', 'saint louis', 'missouri', 'mo', 'kansas city', 'arch']
                    if any(kw in content_check for kw in stl_keywords):
                        print(f"   ✅ Contains St. Louis-relevant keywords")
                    else:
                        print(f"   ❌ No St. Louis-relevant keywords found")
                
                # Verify Miami content
                elif 'miami' in topic.lower() and articles:
                    content_check = ' '.join([a['headline'] + a['summary'] for a in articles]).lower()
                    miami_keywords = ['miami', 'florida', 'fl', 'miami-dade', 'south florida', 'keys', 'cuba']
                    if any(kw in content_check for kw in miami_keywords):
                        print(f"   ✅ Contains Miami-relevant keywords")
                    else:
                        print(f"   ❌ No Miami-relevant keywords found")

                print(f"   Topic in result: {result.get('topic')}")
                print(f"   Sources tried: {result.get('sources_tried')}")

            if result.get('errors'):
                print(f"   ⚠️  Errors: {len(result['errors'])}")

        except Exception as e:
            print(f"   ❌ Error testing {topic}: {e}")

        print()


async def main():
    """Main test function."""
    print("=" * 60)
    print("NEWS FETCHING VERIFICATION TEST")
    print("=" * 60)

    await test_news_topics()

    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(main())
