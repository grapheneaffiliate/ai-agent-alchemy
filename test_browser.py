#!/usr/bin/env python3
"""Test browser functionality."""

import asyncio
from src.plugins.browser import BrowserPlugin


async def test_browser():
    """Test basic browser operations."""
    print("=== Testing Browser Plugin ===\n")

    browser = BrowserPlugin(headless=False)

    try:
        # Test navigation
        print("1. Testing navigation to example.com...")
        result = await browser.navigate("https://example.com")
        print(f"✅ Navigated to: {result['title']}")
        print(f"   URL: {result['url']}\n")

        # Test screenshot
        print("2. Testing screenshot...")
        await browser.screenshot("test_screenshot.png")
        print("✅ Screenshot saved to test_screenshot.png\n")

        # Test content extraction
        print("3. Testing content extraction...")
        content = await browser.get_content()
        print(f"✅ Page content length: {len(content)} characters\n")

        # Test link extraction
        print("4. Testing link extraction...")
        links = await browser.get_links()
        print(f"✅ Found {len(links)} links")
        if links:
            print(f"   First link: {links[0]['text']} -> {links[0]['href']}\n")

        print("✅ All browser tests passed!")

    except Exception as e:
        print(f"❌ Browser test failed: {e}")

    finally:
        await browser.close()
        print("Browser closed.")


if __name__ == "__main__":
    asyncio.run(test_browser())
