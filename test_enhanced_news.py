#!/usr/bin/env python3
"""
Test script for the Enhanced News System
"""

import asyncio
import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from plugins.enhanced_news import get_enhanced_news, execute


async def test_dynamic_source_discovery():
    """Test the dynamic source discovery functionality."""
    print("🧪 Testing Dynamic Source Discovery...")

    try:
        enhanced_news = await get_enhanced_news()

        # Test source discovery for AI topic
        sources = await enhanced_news.source_discovery.discover_sources("artificial intelligence", max_sources=5)

        print(f"✅ Discovered {len(sources)} sources for 'artificial intelligence':")
        for source in sources:
            print(f"  - {source.name} (Credibility: {source.credibility_score:.2f}) - {source.domain}")

        return len(sources) > 0

    except Exception as e:
        print(f"❌ Source discovery test failed: {e}")
        return False


async def test_content_intelligence():
    """Test the content intelligence features."""
    print("\n🧠 Testing Content Intelligence...")

    try:
        enhanced_news = await get_enhanced_news()

        # Test text with known entities and sentiment
        test_text = """
        Google announced a major breakthrough in artificial intelligence research.
        According to scientists at DeepMind, the new AI system can solve complex problems
        50% faster than previous models. This represents a significant advancement
        in machine learning technology that could benefit various industries.
        """

        # Test key point extraction
        key_points = enhanced_news.content_intelligence.extract_key_points(test_text)
        print(f"✅ Extracted {len(key_points)} key points:")
        for point in key_points:
            print(f"  - {point}")

        # Test entity extraction
        entities = enhanced_news.content_intelligence.extract_entities(test_text)
        print(f"✅ Extracted {len(entities)} entities:")
        for entity in entities:
            print(f"  - {entity}")

        # Test sentiment analysis
        sentiment = enhanced_news.content_intelligence.assess_sentiment(test_text)
        print(f"✅ Sentiment score: {sentiment:.2f} (should be positive)")

        # Test summarization
        summary = enhanced_news.content_intelligence.generate_summary(test_text, max_length=100)
        print(f"✅ Generated summary: {summary}")

        return len(key_points) > 0 and len(entities) > 0

    except Exception as e:
        print(f"❌ Content intelligence test failed: {e}")
        return False


async def test_enhanced_news_aggregation():
    """Test the full enhanced news aggregation."""
    print("\n📰 Testing Enhanced News Aggregation...")

    try:
        # Test with a simple topic first
        result = await execute("test", "get_enhanced_news", {
            "topic": "artificial intelligence",
            "max_articles": 5
        })

        if result.get("status") == "error":
            print(f"❌ Enhanced news test failed: {result.get('error')}")
            return False

        print("✅ Enhanced news aggregation successful!"        print(f"  - Topic: {result.get('topic')}")
        print(f"  - Articles found: {result.get('articles_found')}")
        print(f"  - Sources used: {result.get('sources_used')}")
        print(f"  - Method: {result.get('method')}")

        # Show sample articles
        articles = result.get("articles", [])
        if articles:
            print("
📄 Sample articles:"            for i, article in enumerate(articles[:3]):
                print(f"  {i+1}. {article.get('headline', 'No title')}")
                print(f"     Source: {article.get('source', {}).get('name', 'Unknown')}")
                print(f"     Credibility: {article.get('credibility_score', 0):.2f}")
                print(f"     Key points: {len(article.get('key_points', []))}")

        # Test dashboard generation
        dashboard_html = result.get("dashboard_html", "")
        if dashboard_html:
            print(f"\n🎨 Dashboard HTML generated ({len(dashboard_html)} characters)")
            # Save dashboard for inspection
            with open("test_enhanced_news_dashboard.html", "w", encoding="utf-8") as f:
                f.write(dashboard_html)
            print("💾 Dashboard saved to test_enhanced_news_dashboard.html")

        return result.get("articles_found", 0) > 0

    except Exception as e:
        print(f"❌ Enhanced news aggregation test failed: {e}")
        return False


async def test_source_discovery_only():
    """Test just the source discovery tool."""
    print("\n🔍 Testing Source Discovery Tool...")

    try:
        result = await execute("test", "discover_sources", {
            "topic": "climate change",
            "max_sources": 8
        })

        if result.get("status") == "error":
            print(f"❌ Source discovery tool test failed: {result.get('error')}")
            return False

        sources = result.get("sources", [])
        print(f"✅ Source discovery tool successful! Found {len(sources)} sources:")

        for source in sources:
            print(f"  - {source.get('name')} ({source.get('domain')}) - Credibility: {source.get('credibility_score', 0):.2f}")

        return len(sources) > 0

    except Exception as e:
        print(f"❌ Source discovery tool test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Enhanced News System Tests...\n")

    # Run tests
    test_results = []

    # Test individual components
    test_results.append(await test_dynamic_source_discovery())
    test_results.append(await test_content_intelligence())

    # Test full integration
    test_results.append(await test_enhanced_news_aggregation())
    test_results.append(await test_source_discovery_only())

    # Summary
    passed = sum(test_results)
    total = len(test_results)

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Enhanced news system is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
