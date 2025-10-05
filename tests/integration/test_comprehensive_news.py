"""Test comprehensive news coverage across all supported cities."""

import asyncio
from src.plugins.news_fetch import get_news_fetch

async def test_all_locations():
    """Test news fetching for all supported locations."""
    news_fetcher = get_news_fetch()
    
    test_queries = [
        # Original locations
        ("Seattle Washington", "seattle"),
        ("St. Louis Missouri", "st_louis"),
        ("Miami Florida", "miami"),
        ("Washington DC", "washington_dc"),
        ("New York", "new_york"),
        ("California", "california"),
        # New major cities
        ("Kansas City", "kansas_city"),
        ("Dallas Texas", "dallas"),
        ("Houston", "houston"),
        ("Chicago Illinois", "chicago"),
        ("Boston", "boston"),
        ("Philadelphia", "philadelphia"),
        ("Atlanta", "atlanta"),
        ("Phoenix", "phoenix"),
        ("Denver", "denver"),
        ("Portland Oregon", "portland"),
        ("Detroit", "detroit"),
        ("Minneapolis", "minneapolis"),
        ("Nashville", "nashville"),
        ("Las Vegas", "las_vegas"),
        # Topics
        ("robotics", "robotics"),
        ("AI", "ai"),
        ("tech", "tech"),
        ("general", "general")
    ]
    
    print("\n" + "="*80)
    print("COMPREHENSIVE NEWS COVERAGE TEST")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for query, expected_key in test_queries:
        try:
            result = await news_fetcher.get_news(topic=query, max_articles=5)
            
            articles = result.get('articles', [])
            article_count = len(articles)
            
            if article_count > 0:
                print(f"✅ {query:30s} → {article_count} articles")
                print(f"   First: {articles[0]['headline'][:60]}...")
                passed += 1
            else:
                print(f"⚠️  {query:30s} → 0 articles (feeds may be down)")
                print(f"   Errors: {result.get('errors', [])}")
                failed += 1
                
        except Exception as e:
            print(f"❌ {query:30s} → ERROR: {str(e)}")
            failed += 1
    
    print("\n" + "="*80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_queries)} tests")
    print("="*80)
    
    if failed > 0:
        print(f"\n⚠️  {failed} locations had issues (may be temporary feed problems)")
    else:
        print("\n✅ ALL LOCATIONS WORKING PERFECTLY!")
    
    return passed, failed

if __name__ == "__main__":
    passed, failed = asyncio.run(test_all_locations())
    exit(0 if failed == 0 else 1)
