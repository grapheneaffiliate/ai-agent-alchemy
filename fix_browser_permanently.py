#!/usr/bin/env python3
"""
Permanent fix for browser automation issues.
Installs Playwright, configures Firefox, and tests functionality.
"""

import subprocess
import sys
import asyncio
from pathlib import Path


async def test_browser():
    """Test if browser works."""
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'src'))
        from plugins.browser import get_browser
        
        print("\n🔧 Testing browser...")
        browser = await get_browser(headless=True)
        await browser.start()
        
        print("✓ Browser started successfully")
        
        # Test navigation
        result = await browser.navigate('https://example.com')
        print(f"✓ Navigation test: {result.get('status')}")
        
        # Test content extraction
        content = await browser.extract_content_smart()
        print(f"✓ Content extraction: {len(content.get('text', ''))} chars")
        
        await browser.close()
        print("✓ Browser closed successfully")
        
        return True
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        return False


def install_playwright():
    """Install Playwright and browsers."""
    print("\n📦 Installing Playwright...")
    
    # Install playwright package
    subprocess.run([sys.executable, "-m", "pip", "install", "-U", "playwright"], check=True)
    print("✓ Playwright package installed")
    
    # Install Firefox browser
    print("\n🦊 Installing Firefox...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "firefox"], check=True)
    print("✓ Firefox installed")
    
    # Install system dependencies
    print("\n📦 Installing system dependencies...")
    subprocess.run([sys.executable, "-m", "playwright", "install-deps", "firefox"], check=False)
    print("✓ Dependencies installed (errors may be normal on Windows)")


async def main():
    """Main execution."""
    print("="*60)
    print("BROWSER AUTOMATION - PERMANENT FIX")
    print("="*60)
    
    # Step 1: Install
    try:
        install_playwright()
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        print("Try running manually: python -m playwright install firefox")
        return
    
    # Step 2: Test
    print("\n" + "="*60)
    print("TESTING BROWSER")
    print("="*60)
    
    success = await test_browser()
    
    if success:
        print("\n" + "="*60)
        print("✅ BROWSER IS WORKING!")
        print("="*60)
        print("\nYou can now:")
        print("1. Restart your MCP AI Agent server")
        print("2. Try: 'show me news from CNN.com'")
        print("3. Browser will extract content and create artifacts")
    else:
        print("\n" + "="*60)
        print("❌ BROWSER STILL HAS ISSUES")
        print("="*60)
        print("\nManual fix:")
        print("1. Run: python -m playwright install firefox")
        print("2. Check if Bitdefender is blocking")
        print("3. See docs/BITDEFENDER_CONFIGURATION.md")


if __name__ == "__main__":
    asyncio.run(main())
