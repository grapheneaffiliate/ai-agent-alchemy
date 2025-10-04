"""Test the search plugin directly."""

import asyncio
from src.plugins.search import SearchPlugin

async def test_search():
    plugin = SearchPlugin()
    
    # Test web_search
    print("Testing web_search with 'US news'...")
    result = await plugin.web_search('US news', 5)
    print(f"\nResult status: {result.get('status')}")
    print(f"Result keys: {list(result.keys())}")
    
    if result.get('status') == 'success':
        result_data = result.get('result', {})
        print(f"\nResult data keys: {list(result_data.keys())}")
        print(f"Query: {result_data.get('query')}")
        print(f"Total results: {result_data.get('total')}")
        print(f"Type: {result_data.get('type')}")
        
        results = result_data.get('results', [])
        print(f"\nNumber of results: {len(results)}")
        
        if results:
            print("\nFirst result:")
            print(f"  Title: {results[0].get('title')}")
            print(f"  URL: {results[0].get('url')}")
            print(f"  Snippet: {results[0].get('snippet')[:100]}...")
        else:
            print("\nNo results found - checking raw HTML response...")
    else:
        print(f"\nError: {result.get('result', {}).get('error')}")

if __name__ == '__main__':
    asyncio.run(test_search())
