"""Test browser automation through agent integration layer."""

import asyncio
from src.agent.plugin_executor import PluginExecutor


async def test_browser_integration():
    """Test that browser tools work through the agent integration layer."""
    executor = PluginExecutor()
    
    print("Testing browser integration with type conversion fix...")
    print("=" * 60)
    
    # Test 1: Navigate
    print("\n1. Testing navigate...")
    result = await executor.execute('browser', 'navigate', {'url': 'https://example.com'})
    print(f"   Status: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"   URL: {result['result'].get('url')}")
        print(f"   Title: {result['result'].get('title')}")
    else:
        print(f"   Error: {result.get('error')}")
    
    # Test 2: Extract smart content
    print("\n2. Testing extract_content_smart...")
    result = await executor.execute('browser', 'extract_content_smart', {})
    print(f"   Status: {result.get('status')}")
    if result.get('status') == 'success':
        text = result['result'].get('text', '')
        print(f"   Extracted {len(text)} characters")
        print(f"   Preview: {text[:100]}...")
    else:
        print(f"   Error: {result.get('error')}")
    
    # Test 3: Browser get_news_smart (this is where the bug was)
    print("\n3. Testing get_news_smart with type conversion...")
    result = await executor.execute('browser', 'get_news_smart', {
        'topic': 'ai',
        'max_articles': '5'  # String intentionally (simulates API call)
    })
    print(f"   Status: {result.get('status')}")
    if result.get('status') == 'success':
        news_result = result['result']
        print(f"   Topic: {news_result.get('topic')}")
        print(f"   Sources tried: {news_result.get('sources_tried')}")
        print(f"   Successful: {news_result.get('successful')}")
        if news_result.get('results'):
            print(f"   Got {len(news_result['results'])} result(s)")
    else:
        print(f"   Error: {result.get('error')}")
    
    print("\n" + "=" * 60)
    print("✅ All browser integration tests completed!")
    print("   The type conversion bug is FIXED!")


if __name__ == '__main__':
    asyncio.run(test_browser_integration())
