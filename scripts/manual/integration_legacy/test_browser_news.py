"""Test browser news functionality"""
import asyncio
from src.plugins.browser import BrowserPlugin

async def test_news():
    browser = BrowserPlugin(headless=False)
    
    print("Testing browser-get-news...")
    print("-" * 50)
    
    result = await browser.get_news_smart(topic='ai', max_articles=5)
    
    print(f"\nTopic: {result['topic']}")
    print(f"Sources tried: {result['sources_tried']}")
    print(f"Successful: {result['successful']}")
    print(f"Method: {result['method']}")
    
    if result['errors']:
        print("\nErrors encountered:")
        for error in result['errors']:
            print(f"  - {error}")
    
    if result['results']:
        print("\n✓ SUCCESS! Got news content:")
        for idx, res in enumerate(result['results'], 1):
            print(f"\n=== Result {idx} ===")
            print(f"Source: {res['source']}")
            print(f"Title: {res['title']}")
            print(f"\nTop articles:")
            for i, article in enumerate(res['top_articles'][:3], 1):
                print(f"  {i}. {article['headline']}")
                print(f"     {article['url'][:80]}...")
            print(f"\nSummary: {res['summary'][:200]}...")
    else:
        print("\n✗ FAILED: No results returned")
    
    await browser.close()
    print("\n" + "=" * 50)
    print("Test complete")

if __name__ == "__main__":
    asyncio.run(test_news())
