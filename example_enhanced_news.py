#!/usr/bin/env python3
"""
Enhanced News System Integration Example

This example demonstrates how to use the new enhanced news system
with dynamic source discovery, intelligent content processing, and
rich dashboard generation.
"""

import asyncio
import json
import sys
import os
import webbrowser
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from plugins.enhanced_news import get_enhanced_news, execute


async def example_basic_news_fetch():
    """Example 1: Basic enhanced news fetch for AI topic."""
    print("📰 Example 1: Basic Enhanced News Fetch")
    print("=" * 50)

    try:
        # Get enhanced news for artificial intelligence
        result = await execute("enhanced-news", "get-enhanced-news", {
            "topic": "artificial intelligence",
            "max_articles": 8
        })

        if result.get("status") == "error":
            print(f"❌ Error: {result.get('error')}")
            return

        print("✅ Enhanced news fetch successful!")
        print(f"📊 Topic: {result.get('topic')}")
        print(f"📰 Articles found: {result.get('articles_found')}")
        print(f"🔍 Sources used: {result.get('sources_used')}")
        print(f"⚡ Method: {result.get('method')}")

        # Show sample articles
        articles = result.get("articles", [])
        print("\n📄 Top Articles:")
        for i, article in enumerate(articles[:3]):
            print(f"\n  {i+1}. {article.get('headline', 'No title')}")
            print(f"     📌 Source: {article.get('source', {}).get('name', 'Unknown')}")
            print(f"     ⭐ Credibility: {article.get('credibility_score', 0):.2f}")
            print(f"     😊 Sentiment: {article.get('sentiment_score', 0):.2f}")
            print(f"     📝 Summary: {article.get('summary', '')[:100]}...")

            # Show key points if available
            key_points = article.get('key_points', [])
            if key_points:
                print(f"     🔑 Key points: {len(key_points)} extracted")

        # Save dashboard for viewing
        dashboard_html = result.get("dashboard_html", "")
        if dashboard_html:
            with open("example_ai_news_dashboard.html", "w", encoding="utf-8") as f:
                f.write(dashboard_html)
            print("\n💾 Dashboard saved to 'example_ai_news_dashboard.html'")
        return True

    except Exception as e:
        print(f"❌ Example failed: {e}")
        return False


async def example_source_discovery():
    """Example 2: Dynamic source discovery for climate change."""
    print("\n\n🔍 Example 2: Dynamic Source Discovery")
    print("=" * 50)

    try:
        # Discover sources for climate change
        result = await execute("enhanced-news", "discover-sources", {
            "topic": "climate change",
            "max_sources": 10
        })

        if result.get("status") == "error":
            print(f"❌ Error: {result.get('error')}")
            return

        sources = result.get("sources", [])
        print(f"✅ Discovered {len(sources)} authoritative sources for 'climate change':")

        # Group by credibility tiers
        high_cred = [s for s in sources if s.get('credibility_score', 0) > 0.8]
        medium_cred = [s for s in sources if 0.6 < s.get('credibility_score', 0) <= 0.8]
        low_cred = [s for s in sources if s.get('credibility_score', 0) <= 0.6]

        if high_cred:
            print("\n🏆 High Credibility Sources (>0.8):")
            for source in high_cred:
                print(f"  • {source.get('name')} ({source.get('domain')}) - {source.get('credibility_score', 0):.2f}")

        if medium_cred:
            print("\n👍 Medium Credibility Sources (0.6-0.8):")
            for source in medium_cred:
                print(f"  • {source.get('name')} ({source.get('domain')}) - {source.get('credibility_score', 0):.2f}")

        if low_cred:
            print("\n📊 Other Sources (≤0.6):")
            for source in low_cred:
                print(f"  • {source.get('name')} ({source.get('domain')}) - {source.get('credibility_score', 0):.2f}")

        return len(sources) > 0

    except Exception as e:
        print(f"❌ Example failed: {e}")
        return False


async def example_content_intelligence():
    """Example 3: Content intelligence processing."""
    print("\n\n🧠 Example 3: Content Intelligence Processing")
    print("=" * 50)

    try:
        enhanced_news = await get_enhanced_news()

        # Sample article text for processing
        sample_text = """
        Microsoft announced today that it will invest $10 billion in artificial intelligence
        research and development over the next five years. The company said this investment
        will focus on making AI more accessible, safe, and beneficial to society.

        According to CEO Satya Nadella, 'AI has the potential to solve some of humanity's
        biggest challenges, from climate change to healthcare.' The announcement comes
        as tech companies race to dominate the AI market.

        Microsoft's investment will include new research labs in Seattle, Washington
        and Cambridge, Massachusetts, creating over 1,000 new jobs in AI research.
        """

        print("📝 Processing sample article text...")
        print(f"Length: {len(sample_text)} characters")

        # Extract key points
        key_points = enhanced_news.content_intelligence.extract_key_points(sample_text)
        print(f"\n🔑 Key Points ({len(key_points)} extracted):")
        for i, point in enumerate(key_points, 1):
            print(f"  {i}. {point}")

        # Extract entities
        entities = enhanced_news.content_intelligence.extract_entities(sample_text)
        print(f"\n🏷️  Entities ({len(entities)} extracted):")
        for entity in entities:
            print(f"  • {entity}")

        # Analyze sentiment
        sentiment = enhanced_news.content_intelligence.assess_sentiment(sample_text)
        sentiment_desc = "Positive" if sentiment > 0.1 else "Negative" if sentiment < -0.1 else "Neutral"
        print(f"\n😊 Sentiment Analysis: {sentiment:.3f} ({sentiment_desc})")

        # Generate summary
        summary = enhanced_news.content_intelligence.generate_summary(sample_text, max_length=100)
        print(f"\n📋 Generated Summary: {summary}")

        return True

    except Exception as e:
        print(f"❌ Example failed: {e}")
        return False


async def example_full_dashboard():
    """Example 4: Generate a complete dashboard for renewable energy."""
    print("\n\n🎨 Example 4: Full Dashboard Generation")
    print("=" * 50)

    try:
        # Get comprehensive news for renewable energy
        result = await execute("enhanced-news", "get-enhanced-news", {
            "topic": "renewable energy",
            "max_articles": 12
        })

        if result.get("status") == "error":
            print(f"❌ Error: {result.get('error')}")
            return

        print("✅ Full dashboard generation successful!")
        print(f"📊 Topic: {result.get('topic')}")
        print(f"📰 Articles found: {result.get('articles_found')}")
        print(f"🔍 Sources used: {result.get('sources_used')}")

        # Analyze the results
        articles = result.get("articles", [])
        if articles:
            # Calculate average credibility
            avg_credibility = sum(a.get('credibility_score', 0) for a in articles) / len(articles)
            print(f"⭐ Average credibility: {avg_credibility:.2f}")

            # Analyze sentiment distribution
            positive = sum(1 for a in articles if a.get('sentiment_score', 0) > 0.1)
            negative = sum(1 for a in articles if a.get('sentiment_score', 0) < -0.1)
            neutral = len(articles) - positive - negative
            print(f"😊 Sentiment: {positive} positive, {neutral} neutral, {negative} negative")

            # Show source diversity
            sources = {}
            for article in articles:
                source_name = article.get('source', {}).get('name', 'Unknown')
                sources[source_name] = sources.get(source_name, 0) + 1

            print(f"📡 Source diversity: {len(sources)} different sources")
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    • {source}: {count} articles")

        # Save the complete dashboard
        dashboard_html = result.get("dashboard_html", "")
        if dashboard_html:
            filename = "example_renewable_energy_dashboard.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(dashboard_html)
            print(f"\n💾 Complete dashboard saved to '{filename}'")

            # Optionally open in browser
            try:
                webbrowser.open(f"file://{os.path.abspath(filename)}")
                print("🌐 Dashboard opened in browser")
            except:
                print("💡 Open the dashboard file in your browser to see the interactive features")

        return True

    except Exception as e:
        print(f"❌ Example failed: {e}")
        return False


async def example_comparison_with_old_system():
    """Example 5: Compare with old hardcoded system."""
    print("\n\n⚖️  Example 5: Comparison with Old System")
    print("=" * 50)

    try:
        # Test old system (if available)
        try:
            from plugins.news_fetch import get_news_fetch
            old_news = get_news_fetch()

            print("📊 Testing OLD system (RSS feeds only):")
            old_result = await old_news.get_news("artificial intelligence", max_articles=5)
            old_articles = old_result.get('articles', [])
            print(f"  • Found {len(old_articles)} articles")
            print(f"  • Sources tried: {old_result.get('sources_tried', 0)}")
            print(f"  • Method: {old_result.get('method', 'unknown')}")

            if old_articles:
                print(f"  • Sample: {old_articles[0].get('headline', 'No title')[:60]}...")

        except Exception as e:
            print(f"  • Old system test failed: {e}")

        print("\n🚀 Testing NEW enhanced system:")
        new_result = await execute("enhanced-news", "get-enhanced-news", {
            "topic": "artificial intelligence",
            "max_articles": 5
        })

        if new_result.get("status") == "error":
            print(f"  • Error: {new_result.get('error')}")
        else:
            new_articles = new_result.get("articles", [])
            print(f"  • Found {len(new_articles)} articles")
            print(f"  • Sources used: {new_result.get('sources_used', 0)}")
            print(f"  • Method: {new_result.get('method', 'unknown')}")

            if new_articles:
                article = new_articles[0]
                print(f"  • Sample: {article.get('headline', 'No title')[:60]}...")
                print(f"  • Credibility: {article.get('credibility_score', 0):.2f}")
                print(f"  • Key points: {len(article.get('key_points', []))}")

                # Save comparison dashboard
                dashboard_html = new_result.get("dashboard_html", "")
                if dashboard_html:
                    with open("example_system_comparison.html", "w", encoding="utf-8") as f:
                        f.write(dashboard_html)
                    print("  • Dashboard saved to 'example_system_comparison.html'"
        return True

    except Exception as e:
        print(f"❌ Example failed: {e}")
        return False


async def main():
    """Run all examples."""
    print("🚀 Enhanced News System - Integration Examples")
    print("=" * 60)
    print("This demonstrates the new enhanced news capabilities:")
    print("• Dynamic source discovery (no hardcoded sites)")
    print("• Intelligent content processing")
    print("• Rich interactive dashboards")
    print("• Multi-source aggregation")
    print()

    # Run examples
    examples = [
        example_basic_news_fetch,
        example_source_discovery,
        example_content_intelligence,
        example_full_dashboard,
        example_comparison_with_old_system
    ]

    results = []
    for example in examples:
        try:
            result = await example()
            results.append(result)
        except KeyboardInterrupt:
            print("\n⏹️  Stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Example error: {e}")
            results.append(False)

    # Summary
    passed = sum(results)
    total = len(results)

    print(f"\n📊 Examples Summary: {passed}/{total} successful")

    if passed == total:
        print("🎉 All examples completed successfully!")
        print("\n💡 Key files generated:")
        print("  • example_ai_news_dashboard.html")
        print("  • example_renewable_energy_dashboard.html")
        print("  • example_system_comparison.html")
        print("\n🔗 Open these files in your browser to see the interactive dashboards!")
    else:
        print("⚠️  Some examples failed. Check the output above for details.")

    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        print(f"\n{'✅' if success else '❌'} Examples {'PASSED' if success else 'FAILED'}")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)
