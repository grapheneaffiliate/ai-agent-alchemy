"""Playwright-based browser automation plugin for MCP AI Agent with anti-detection."""

import asyncio
import os
import json
import tempfile
import subprocess
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page, BrowserContext


class BrowserPlugin:
    """Enhanced browser automation plugin using Playwright with Firefox and anti-detection."""

    def __init__(
        self, 
        headless: bool = False, 
        session_timeout: int = 300,
        retry_count: int = 3
    ):
        self.headless = headless
        self.session_timeout = session_timeout
        self.retry_count = retry_count
        self.last_activity = None
        self._lock = asyncio.Lock()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self) -> None:
        """Launch Firefox browser with anti-detection settings."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            
            # Launch Firefox with stealth settings (better CAPTCHA avoidance than Chromium)
            self.browser = await self.playwright.firefox.launch(
                headless=self.headless,
                firefox_user_prefs={
                    'dom.webdriver.enabled': False,
                    'useAutomationExtension': False,
                    'general.platform.override': 'Win32',
                    'general.useragent.override': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
                }
            )
            
            # Create context with realistic browser settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                }
            )
            
            # Inject anti-detection scripts
            await self.context.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Mock plugins to appear more real
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                        {name: 'Native Client', filename: 'internal-nacl-plugin'}
                    ]
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                // Mock platform
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32'
                });
                
                // Add realistic properties
                window.chrome = {
                    runtime: {}
                };
                
                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            self.page = await self.context.new_page()
            self.last_activity = asyncio.get_event_loop().time()

    async def close(self) -> None:
        """Close browser instance."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    async def ensure_browser_ready(self) -> None:
        """Ensure browser is started and session is valid."""
        async with self._lock:
            if not self.page or self.page.is_closed():
                await self.start()
            self.last_activity = asyncio.get_event_loop().time()

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL with retry logic and CAPTCHA detection."""
        await self.ensure_browser_ready()
        
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        for attempt in range(self.retry_count):
            try:
                response = await self.page.goto(
                    url, 
                    wait_until='domcontentloaded',
                    timeout=30000
                )
                
                # Check if we hit a CAPTCHA or error page
                current_url = self.page.url.lower()
                page_title = await self.page.title()
                
                if any(x in current_url for x in ['sorry', 'captcha', 'challenge', 'verify']):
                    return {
                        "url": self.page.url,
                        "title": page_title,
                        "status": "captcha_detected",
                        "error": "CAPTCHA challenge detected. Try alternative sources or RSS feeds."
                    }
                
                return {
                    "url": self.page.url,
                    "title": page_title,
                    "status": "success",
                    "status_code": response.status if response else None
                }
                
            except Exception as e:
                if attempt == self.retry_count - 1:
                    return {
                        "url": url,
                        "status": "error",
                        "error": str(e)
                    }
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                await self.close()
                await self.start()

    async def screenshot(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Take a screenshot of current page."""
        await self.ensure_browser_ready()

        screenshot_bytes = await self.page.screenshot(full_page=True)
        if path:
            with open(path, 'wb') as f:
                f.write(screenshot_bytes)
            return {"path": path, "status": "saved"}
        return {"data": screenshot_bytes.hex(), "status": "captured"}

    async def get_content(self) -> str:
        """Get page content as text."""
        await self.ensure_browser_ready()
        return await self.page.content()

    async def extract_content_smart(self) -> Dict[str, Any]:
        """Extract main content intelligently, filtering ads and boilerplate."""
        await self.ensure_browser_ready()
        
        # Extract main content (remove nav, footer, ads)
        main_content = await self.page.evaluate("""
            () => {
                // Remove unwanted elements
                const unwanted = document.querySelectorAll(
                    'nav, header, footer, aside, .ad, .advertisement, ' +
                    '[role="complementary"], .sidebar, .menu, .navigation, ' +
                    '[class*="ad-"], [class*="banner"], [id*="ad-"]'
                );
                unwanted.forEach(el => el.remove());
                
                // Find main content
                const main = document.querySelector(
                    'main, article, [role="main"], .content, #content, .main-content, ' +
                    '[class*="article"], [class*="post-content"]'
                );
                const content = main || document.body;
                
                // Get all links
                const links = Array.from(content.querySelectorAll('a')).map(a => ({
                    text: (a.innerText || '').trim(),
                    href: a.href
                })).filter(link => link.text && link.href && !link.href.startsWith('javascript:'));
                
                // Get all headings
                const headings = Array.from(document.querySelectorAll('h1, h2, h3')).map(h => ({
                    level: h.tagName.toLowerCase(),
                    text: h.innerText.trim()
                })).filter(h => h.text);
                
                return {
                    text: content.innerText.trim(),
                    html: content.innerHTML,
                    title: document.title,
                    headings: headings,
                    links: links
                };
            }
        """)
        
        return {
            "url": self.page.url,
            "title": main_content.get('title', ''),
            "text": main_content.get('text', '')[:5000],  # Limit to 5000 chars
            "headings": main_content.get('headings', [])[:20],  # Limit headings
            "links": main_content.get('links', [])[:50],  # Limit links
            "status": "success",
            "method": "playwright"
        }

    async def get_news_smart(self, topic: str = 'ai', max_articles: int = 5) -> Dict[str, Any]:
        """Get news using multiple strategies to avoid CAPTCHAs."""

        results = []
        errors = []

        # URL-safe topic (replace spaces with hyphens for tags)
        url_safe_topic = topic.lower().replace(' ', '-')

        # Try direct news sites without search based on topic
        direct_sites = []

        # Check if government/politics related
        gov_keywords = ['government', 'shutdown', 'federal', 'congress', 'president', 'politics', 'policy', 'trump', 'biden', 'white house']
        if any(kw in topic.lower() for kw in gov_keywords):
            # Government/Politics news sites
            direct_sites = [
                'https://www.cnn.com/politics/',
                'https://www.foxnews.com/politics/',
                'https://www.nbcnews.com/politics/',
                f'https://www.nytimes.com/search?query={topic.replace(" ", "%20")}',
                'https://www.washingtonpost.com/politics/',
                f'https://apnews.com/hub/politics',
                'https://www.reuters.com/world/us/',
            ]
        else:
            # Default to AI/Tech sites for other topics
            direct_sites = [
                f'https://techcrunch.com/tag/{url_safe_topic}/',
                f'https://arstechnica.com/{topic}/',
                f'https://www.theverge.com/search?q={topic}',
            ]
        
        for site_url in direct_sites:
            try:
                # Navigate to site
                nav_result = await self.navigate(site_url)
                
                if nav_result.get('status') == 'captcha_detected':
                    errors.append(f"{site_url}: CAPTCHA detected")
                    continue
                    
                if nav_result.get('status') != 'success':
                    errors.append(f"{site_url}: Navigation failed")
                    continue
                
                # Extract content
                extracted = await self.extract_content_smart()
                
                if extracted.get('status') == 'success' and extracted.get('links'):
                    # Got valid content
                    results.append({
                        'source': site_url,
                        'title': extracted.get('title', ''),
                        'top_articles': [
                            {
                                'headline': link.get('text', '')[:100],
                                'url': link.get('href', '')
                            }
                            for link in extracted['links'][:max_articles]
                            if link.get('text') and len(link.get('text', '')) > 10
                        ],
                        'summary': extracted.get('text', '')[:800],
                        'all_headings': extracted.get('headings', [])[:10]
                    })
                    break  # Success, stop trying other sites
                else:
                    errors.append(f"{site_url}: No content extracted")
                    
            except Exception as e:
                errors.append(f"{site_url}: {str(e)}")
                continue
        
        return {
            "topic": topic,
            "results": results,
            "sources_tried": len(direct_sites),
            "successful": len(results),
            "errors": errors if not results else [],
            "method": "direct_site_with_extraction"
        }

    async def click(self, selector: str) -> Dict[str, Any]:
        """Click an element on the page."""
        await self.ensure_browser_ready()
        await self.page.click(selector)
        return {"selector": selector, "status": "clicked"}

    async def fill(self, selector: str, text: str) -> Dict[str, Any]:
        """Fill a form field."""
        await self.ensure_browser_ready()
        await self.page.fill(selector, text)
        return {"selector": selector, "status": "filled"}

    async def evaluate(self, script: str) -> Any:
        """Execute JavaScript in browser context."""
        await self.ensure_browser_ready()
        return await self.page.evaluate(script)

    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> Dict[str, Any]:
        """Wait for an element to appear."""
        await self.ensure_browser_ready()
        await self.page.wait_for_selector(selector, timeout=timeout)
        return {"selector": selector, "status": "found"}

    async def extract_text(self, selector: str) -> str:
        """Extract text content from an element."""
        await self.ensure_browser_ready()
        element = await self.page.query_selector(selector)
        if element:
            return await element.text_content()
        return ""

    async def get_links(self) -> List[Dict[str, str]]:
        """Get all links on the current page."""
        await self.ensure_browser_ready()
        links = await self.page.query_selector_all("a")
        result = []
        for link in links:
            href = await link.get_attribute("href")
            text = await link.text_content()
            if href:
                result.append({"href": href, "text": text.strip() if text else ""})
        return result


# Singleton instance for reuse across sessions
_browser_instance: Optional[BrowserPlugin] = None


async def get_browser(headless: bool = False) -> BrowserPlugin:
    """Get or create browser instance."""
    global _browser_instance
    if not _browser_instance:
        _browser_instance = BrowserPlugin(headless=headless)
    return _browser_instance


async def close_browser() -> None:
    """Close global browser instance."""
    global _browser_instance
    if _browser_instance:
        await _browser_instance.close()
        _browser_instance = None


# MCP Plugin Interface
async def execute(server: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute browser plugin commands via MCP interface."""
    try:
        browser = await get_browser(headless=args.get('headless', True))
        
        if tool_name == 'browser_navigate':
            return await browser.navigate(args.get('url', ''))
        
        elif tool_name == 'browser_screenshot':
            return await browser.screenshot(args.get('path'))
        
        elif tool_name == 'browser_get_content':
            content = await browser.get_content()
            return {"status": "success", "content": content}
        
        elif tool_name == 'browser_extract_content':
            return await browser.extract_content_smart()
        
        elif tool_name == 'browser_get_news':
            return await browser.get_news_smart(
                topic=args.get('topic', 'ai'),
                max_articles=args.get('max_articles', 5)
            )
        
        elif tool_name == 'browser_click':
            return await browser.click(args.get('selector', ''))
        
        elif tool_name == 'browser_fill':
            return await browser.fill(
                args.get('selector', ''),
                args.get('text', '')
            )
        
        elif tool_name == 'browser_close':
            await close_browser()
            return {"status": "success", "message": "Browser closed"}
        
        else:
            return {"status": "error", "error": f"Unknown tool: {tool_name}"}
            
    except Exception as e:
        return {"status": "error", "error": str(e)}
