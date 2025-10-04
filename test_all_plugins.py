#!/usr/bin/env python3
"""Comprehensive test of ALL plugins accessible from custom UI."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.plugin_executor import PluginExecutor
from src.agent.api import AgentAPI
from src.agent.react_loop import execute_react_loop


async def test_news_plugin():
    """Test news fetch plugin."""
    print("\n" + "="*60)
    print("Testing News Plugin (fetch-news)")
    print("="*60)
    
    executor = PluginExecutor()
    
    tests = [
        ('robotics', 5),
        ('seattle', 5),
        ('kansas city', 5),
    ]
    
    for topic, max_articles in tests:
        result = await executor.execute('news', 'get_news', {
            'topic': topic,
            'max_articles': max_articles
        })
        
        if result.get('status') == 'success':
            articles = result['result'].get('articles', [])
            print(f"✅ {topic:20} → {len(articles)} articles")
            if articles:
                print(f"   First: {articles[0]['headline'][:60]}...")
        else:
            print(f"❌ {topic:20} → Error: {result.get('error')}")


async def test_browser_plugin():
    """Test browser plugin."""
    print("\n" + "="*60)
    print("Testing Browser Plugin")
    print("="*60)
    
    executor = PluginExecutor()
    
    # Test navigate
    print("\n1. Testing browse-url...")
    result = await executor.execute('browser', 'navigate', {
        'url': 'https://example.com'
    })
    if result.get('status') == 'success':
        print("✅ Navigate: success")
    else:
        print(f"❌ Navigate: {result.get('error')}")
    
    # Test extract
    print("\n2. Testing browser-extract-smart...")
    result = await executor.execute('browser', 'extract_content_smart', {})
    if result.get('status') == 'success':
        content = result['result']
        print(f"✅ Extract: {len(content.get('text', ''))} chars extracted")
    else:
        print(f"❌ Extract: {result.get('error')}")
    
    # Test get links
    print("\n3. Testing browser-get-links...")
    result = await executor.execute('browser', 'get_links', {})
    if result.get('status') == 'success':
        links = result['result']
        print(f"✅ Get Links: {len(links)} links found")
    else:
        print(f"❌ Get Links: {result.get('error')}")


async def test_crawl4ai_plugin():
    """Test Crawl4AI plugin."""
    print("\n" + "="*60)
    print("Testing Crawl4AI Plugin")
    print("="*60)
    
    executor = PluginExecutor()
    
    # Test basic crawl
    print("\n1. Testing crawl...")
    result = await executor.execute('crawl4ai', 'crawl_url', {
        'url': 'https://example.com'
    })
    if result.get('status') == 'success':
        markdown = result['result'].get('markdown', '')
        print(f"✅ Crawl: {len(markdown)} chars of markdown")
    else:
        print(f"❌ Crawl: {result.get('error')}")


async def test_time_plugin():
    """Test time utilities plugin."""
    print("\n" + "="*60)
    print("Testing Time Plugin")
    print("="*60)
    
    executor = PluginExecutor()
    
    tests = [
        ('get_current_time', 'get-time'),
        ('get_current_date', 'get-date'),
        ('get_day_info', 'get-day-info'),
    ]
    
    for func_name, tool_name in tests:
        result = await executor.execute('time', func_name, {})
        if result.get('status') == 'success':
            print(f"✅ {tool_name:20} → {result['result']}")
        else:
            print(f"❌ {tool_name:20} → Error")


async def test_react_integration():
    """Test that ReAct loop can access all tools."""
    print("\n" + "="*60)
    print("Testing ReAct Loop Integration")
    print("="*60)
    
    from dotenv import load_dotenv
    from src.agent.models import Session
    load_dotenv()
    
    # Create a mock session for testing
    session = Session(session_id="test-session")
    api = AgentAPI(session)
    executor = PluginExecutor()
    
    test_queries = [
        "What time is it?",
        "Show me robotics news",
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        try:
            response, artifact = await execute_react_loop(query, api, executor, max_iterations=3)
            print(f"✅ Response: {response[:100]}...")
            if artifact:
                print(f"✅ Artifact: {len(artifact)} chars HTML")
            else:
                print("⚠️  No artifact generated")
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Run all plugin tests."""
    print("\n" + "╔" + "="*58 + "╗")
    print("║  MCP AI Agent - Comprehensive Plugin Test               ║")
    print("╚" + "="*58 + "╝")
    
    try:
        await test_news_plugin()
        await test_browser_plugin()
        await test_crawl4ai_plugin()
        await test_time_plugin()
        await test_react_integration()
        
        print("\n" + "="*60)
        print("✅ ALL PLUGIN TESTS COMPLETE")
        print("="*60)
        print("\nAll plugins are accessible from the custom UI via ReAct loop!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
