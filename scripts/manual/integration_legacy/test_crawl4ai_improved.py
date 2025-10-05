"""Test script for improved Crawl4AI functionality."""

import asyncio
import sys
from src.plugins.crawl4ai_plugin import get_crawl4ai


async def test_basic_crawl():
    """Test basic crawling with clean output."""
    print("=" * 60)
    print("Testing Improved Crawl4AI Plugin")
    print("=" * 60)
    
    # Get crawler instance
    crawler = await get_crawl4ai()
    
    # Test URL
    test_url = "https://atchimneys.com"
    
    print(f"\n📍 Crawling: {test_url}")
    print("-" * 60)
    
    # Perform crawl
    result = await crawler.crawl_url(test_url)
    
    # Check for errors
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        if 'traceback' in result:
            print(f"\nTraceback:\n{result['traceback']}")
        return False
    
    # Display results
    print(f"✅ Success: {result.get('success', False)}")
    print(f"📄 Title: {result.get('title', 'N/A')}")
    print(f"📊 Status Code: {result.get('status_code', 'N/A')}")
    print(f"🔢 Word Count: {result.get('word_count', 0)}")
    print(f"🧹 Cleaned: {result.get('cleaned', False)}")
    
    # Get markdown content
    markdown = result.get('markdown', '')
    
    print(f"\n📝 Markdown Length: {len(markdown)} characters")
    print("-" * 60)
    
    # Show first 500 characters of markdown
    print("\n📖 Markdown Preview (first 500 chars):")
    print("-" * 60)
    print(markdown[:500])
    if len(markdown) > 500:
        print("...")
    print("-" * 60)
    
    # Quality checks
    print("\n🔍 Quality Checks:")
    print("-" * 60)
    
    checks = {
        "Has title": bool(result.get('title') and result['title'] != 'Untitled'),
        "Has content": len(markdown) > 100,
        "Used filtering": result.get('cleaned', False),
        "No 'Skip to content'": "Skip to content" not in markdown,
        "No excessive links": markdown.count('[') < 50,  # Reasonable link count
        "Clean formatting": not ("```" in markdown[:100]),  # No code blocks at start
        "Proper structure": markdown.startswith('#') or markdown.strip().startswith('##'),
    }
    
    for check, passed in checks.items():
        status = "✅" if passed else "⚠️"
        print(f"{status} {check}: {passed}")
    
    # Summary
    print("\n" + "=" * 60)
    passed_checks = sum(checks.values())
    total_checks = len(checks)
    
    print(f"Quality Score: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.0f}%)")
    
    if passed_checks >= total_checks * 0.8:  # 80% pass rate
        print("✅ CRAWL QUALITY: EXCELLENT")
    elif passed_checks >= total_checks * 0.6:  # 60% pass rate
        print("⚠️  CRAWL QUALITY: GOOD (some issues)")
    else:
        print("❌ CRAWL QUALITY: NEEDS IMPROVEMENT")
    
    print("=" * 60)
    
    # Save full markdown to file for inspection
    output_file = "test_crawl_output.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Crawl Test Results\n\n")
        f.write(f"**URL:** {test_url}\n\n")
        f.write(f"**Title:** {result.get('title', 'N/A')}\n\n")
        f.write(f"**Word Count:** {result.get('word_count', 0)}\n\n")
        f.write(f"---\n\n")
        f.write(markdown)
    
    print(f"\n💾 Full markdown saved to: {output_file}")
    
    # Cleanup
    await crawler.close()
    
    return passed_checks >= total_checks * 0.8


async def test_error_handling():
    """Test error handling with invalid URL."""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    crawler = await get_crawl4ai()
    
    # Invalid URL
    result = await crawler.crawl_url("https://this-site-definitely-does-not-exist-12345.com")
    
    if result.get('error'):
        print("✅ Error handling works correctly")
        print(f"   Error message: {result['error'][:100]}...")
        return True
    else:
        print("⚠️  Expected error but got success (or site exists!)")
        return False


async def main():
    """Run all tests."""
    print("\n🧪 Crawl4AI Improvement Test Suite\n")
    
    try:
        # Test 1: Basic crawl with quality checks
        test1_passed = await test_basic_crawl()
        
        # Test 2: Error handling
        test2_passed = await test_error_handling()
        
        # Final summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Basic Crawl Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"Error Handling Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
        
        all_passed = test1_passed and test2_passed
        
        if all_passed:
            print("\n🎉 All tests PASSED!")
            print("\n📋 Next Steps:")
            print("1. Review test_crawl_output.md for content quality")
            print("2. Compare with original unfiltered output")
            print("3. Test with Open WebUI integration")
            print("4. Verify artifact generation works")
            return 0
        else:
            print("\n⚠️  Some tests failed. Review output above.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
