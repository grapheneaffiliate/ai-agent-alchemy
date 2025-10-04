#!/usr/bin/env python3
"""
Simple test for Enhanced News System
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test():
    print("🧪 Testing Enhanced News System...")

    try:
        from plugins.enhanced_news import get_enhanced_news

        # Test 1: Initialize the system
        print("\n1️⃣ Testing initialization...")
        enhanced_news = await get_enhanced_news()
        print("   ✅ System initialized successfully")

        # Test 2: Source Discovery
        print("\n2️⃣ Testing source discovery...")
        sources = await enhanced_news.source_discovery.discover_sources('artificial intelligence', max_sources=3)
        print(f"   ✅ Found {len(sources)} sources:")
        for source in sources:
            print(f"      - {source.name}: {source.credibility_score:.2f}")

        # Test 3: Content Intelligence
        print("\n3️⃣ Testing content intelligence...")
        test_text = "Microsoft announced a major AI breakthrough that will change healthcare forever according to scientists."
        key_points = enhanced_news.content_intelligence.extract_key_points(test_text)
        entities = enhanced_news.content_intelligence.extract_entities(test_text)
        sentiment = enhanced_news.content_intelligence.assess_sentiment(test_text)
        summary = enhanced_news.content_intelligence.generate_summary(test_text)

        print(f"   ✅ Key points: {len(key_points)} extracted")
        print(f"   ✅ Entities: {len(entities)} extracted")
        print(f"   ✅ Sentiment: {sentiment:.2f}")
        print(f"   ✅ Summary generated: {len(summary)} characters")

        print("\n🎉 All tests passed! Enhanced news system is working correctly.")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
