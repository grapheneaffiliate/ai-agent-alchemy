"""Test HTTP-based news fetcher (no browser)"""
import asyncio
from src.plugins.news_fetch import NewsFetchPlugin

async def test():
    news = NewsFetchPlugin()
    
    print("Testing HTTP-based news fetcher (bypasses Bitdefender)...")
    print("=" * 60)
    
    result = await news.get_news(topic='ai', max_articles=5)
    
    print(f"\nTopic: {result['topic']}")
    print(f"Method: {result['method']}")
    print(f"Sources tried: {result['sources_tried']}")
    print(f"Successful: {result['successful']}")
    print(f"Note: {result.get('note', '')}")
    
    if result['errors']:
        print("\nErrors:")
        for err in result['errors']:
            print(f"  - {err}")
    
    if result['articles']:
        print(f"\n✓ Got {len(result['articles'])} articles:")
        print("-" * 60)
        for i, article in enumerate(result['articles'], 1):
            print(f"\n{i}. {article['headline']}")
            print(f"   URL: {article['url']}")
            if article['summary']:
                print(f"   Summary: {article['summary'][:150]}...")
            if article['published']:
                print(f"   Published: {article['published']}")
    else:
        print("\n✗ No articles retrieved")
    
    print("\n" + "=" * 60)
    print("Test complete")

if __name__ == "__main__":
    asyncio.run(test())
