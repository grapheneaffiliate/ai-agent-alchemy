"""Playwright-based browser automation plugin for MCP AI Agent with anti-detection."""

import asyncio
import os
import json
import tempfile
import subprocess
import warnings
import logging
import sys
import signal
import threading
import time
from contextlib import contextmanager, redirect_stderr, redirect_stdout, asynccontextmanager
from io import StringIO
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

# Suppress ALL Playwright subprocess cleanup warnings and errors
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Configure logging to suppress subprocess warnings
logging.getLogger('asyncio').setLevel(logging.CRITICAL)
logging.getLogger('playwright').setLevel(logging.CRITICAL)
logging.getLogger('websockets').setLevel(logging.CRITICAL)

# More comprehensive warning suppression
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Suppress ALL subprocess and asyncio warnings
warnings.filterwarnings("ignore", message=".*BaseSubprocessTransport.*")
warnings.filterwarnings("ignore", message=".*Event loop is closed.*")
warnings.filterwarnings("ignore", message=".*I/O operation on closed pipe.*")
warnings.filterwarnings("ignore", message=".*EPIPE.*")
warnings.filterwarnings("ignore", message=".*broken pipe.*")
warnings.filterwarnings("ignore", message=".*Node.js.*")
warnings.filterwarnings("ignore", message=".*RuntimeError.*")

# Set logging to suppress all warnings
for logger_name in ['asyncio', 'playwright', 'websockets', 'urllib3', 'selenium']:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Global flag to track if we're in cleanup phase
_in_cleanup = False

# Suppress stderr warnings during browser operations
@contextmanager
def suppress_browser_warnings():
    """Context manager to suppress browser cleanup warnings."""
    old_stderr = sys.stderr
    old_stdout = sys.stdout

    class DevNull:
        def write(self, text):
            # Filter out all browser-related warnings and errors
            if not any(warning in text for warning in [
                "BaseSubprocessTransport",
                "Event loop is closed",
                "EPIPE: broken pipe",
                "I/O operation on closed pipe",
                "RuntimeError: Event loop is closed",
                "Node.js",
                "throw er",
                "Error: EPIPE",
                "broken pipe",
                "write EPIPE",
                "PipeTransport",
                "dispatcherConnection",
                "Emitted 'error' event",
                "fileno",
                "call_soon",
                "_check_closed",
                "proactor_events",
                "windows_utils"
            ]):
                old_stderr.write(text)

        def flush(self):
            old_stderr.flush()

    # Redirect both stdout and stderr to suppress warnings
    with redirect_stderr(DevNull()), redirect_stdout(DevNull()):
        try:
            yield
        finally:
            pass

    # Restore original streams
    sys.stderr = old_stderr
    sys.stdout = old_stdout


@contextmanager
def suppress_all_warnings():
    """Context manager to suppress ALL browser and subprocess warnings."""
    global _in_cleanup

    # Set cleanup flag
    _in_cleanup = True

    # Save original stderr/stdout
    old_stderr = sys.stderr
    old_stdout = sys.stdout

    class WarningFilter:
        def __init__(self, original_stream):
            self.original_stream = original_stream
            self.buffer = []

        def write(self, text):
            # Filter out ALL browser, subprocess, and Node.js related warnings
            suppressed_patterns = [
                'BaseSubprocessTransport', 'Event loop is closed', 'I/O operation on closed pipe',
                'EPIPE', 'broken pipe', 'Node.js', 'RuntimeError', 'throw er', 'Error: EPIPE',
                'PipeTransport', 'dispatcherConnection', 'Emitted \'error\' event', 'fileno',
                'call_soon', '_check_closed', 'proactor_events', 'windows_utils',
                'Exception ignored in', 'ValueError', 'RuntimeWarning', 'ResourceWarning',
                'DeprecationWarning', 'PendingDeprecationWarning', 'FutureWarning',
                'asyncio', 'playwright', 'websockets', 'selenium', 'urllib3'
            ]

            # Only write if text doesn't contain suppressed patterns
            if not any(pattern.lower() in text.lower() for pattern in suppressed_patterns):
                self.original_stream.write(text)
                self.original_stream.flush()

        def flush(self):
            self.original_stream.flush()

    # Apply warning filter
    sys.stderr = WarningFilter(old_stderr)
    sys.stdout = WarningFilter(old_stdout)

    try:
        yield
    finally:
        # Restore original streams
        sys.stderr = old_stderr
        sys.stdout = old_stdout
        _in_cleanup = False


class BrowserCleanupManager:
    """Enhanced cleanup manager for browser processes."""

    def __init__(self):
        self.cleanup_lock = threading.Lock()
        self.processes_cleaned = set()

    def cleanup_subprocess(self, pid):
        """Safely cleanup subprocess by PID."""
        with self.cleanup_lock:
            if pid in self.processes_cleaned:
                return
            self.processes_cleaned.add(pid)

        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['taskkill', '/F', '/PID', str(pid)],
                             capture_output=True, timeout=5)
            else:  # Unix-like
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        except (subprocess.TimeoutExpired, ProcessLookupError, OSError):
            pass  # Process already gone or can't be killed

    def force_cleanup_all(self):
        """Force cleanup all browser-related processes."""
        try:
            if os.name == 'nt':  # Windows
                # Find and kill browser processes
                result = subprocess.run(['tasklist'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if any(proc in line.lower() for proc in ['firefox', 'chrome', 'msedge']):
                            try:
                                pid = int(line.strip().split()[1])
                                self.cleanup_subprocess(pid)
                            except (ValueError, IndexError):
                                pass
            else:  # Unix-like
                # Find and kill browser processes
                result = subprocess.run(['pgrep', '-f', 'firefox|chrome'],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for pid in result.stdout.strip().split('\n'):
                        if pid:
                            try:
                                self.cleanup_subprocess(int(pid))
                            except ValueError:
                                pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass


# Global cleanup manager
_cleanup_manager = BrowserCleanupManager()


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
        self._cleanup_registered = False

    @asynccontextmanager
    async def _operation_span(self, operation: str, **details: Any):
        start = time.perf_counter()
        log_details = {'operation': operation, **details}
        logger.info('browser.%s.start', operation, extra=log_details)
        result_metadata: Dict[str, Any] = {'status': 'success'}
        try:
            yield result_metadata
        except Exception:
            duration = time.perf_counter() - start
            logger.exception(
                'browser.%s.error',
                operation,
                extra={**log_details, 'status': 'error', 'duration': round(duration, 3)}
            )
            raise
        else:
            duration = time.perf_counter() - start
            status = result_metadata.get('status', 'success')
            level = logging.INFO if status == 'success' else logging.WARNING
            logger.log(
                level,
                'browser.%s.%s',
                operation,
                status,
                extra={**log_details, 'status': status, 'duration': round(duration, 3)}
            )

    async def start(self) -> None:
        """Launch Firefox browser with anti-detection settings."""
        async with self._operation_span('start', headless=self.headless) as span:
            if self.playwright:
                span['status'] = 'noop'
                return

            if not self._cleanup_registered:
                import atexit
                atexit.register(self._emergency_cleanup)
                self._cleanup_registered = True

            self.playwright = await async_playwright().start()

            self.browser = await self.playwright.firefox.launch(
                headless=self.headless,
                firefox_user_prefs={
                    'dom.webdriver.enabled': False,
                    'useAutomationExtension': False,
                    'general.platform.override': 'Win32',
                    'general.useragent.override': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
                }
            )

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
        """Close browser instance with comprehensive cleanup."""
        async with self._operation_span('close') as span:
            with suppress_all_warnings():
                try:
                    if self.page:
                        try:
                            await self.page.close()
                        except Exception:
                            pass
                    if self.context:
                        try:
                            await self.context.close()
                        except Exception:
                            pass
                    if self.browser:
                        try:
                            await self.browser.close()
                        except Exception:
                            pass

                    if self.playwright:
                        try:
                            await self.playwright.stop()
                        except Exception:
                            pass

                    _cleanup_manager.force_cleanup_all()

                    import gc
                    gc.collect()

                except Exception:
                    span['status'] = 'partial'

            if not any([self.page, self.context, self.browser, self.playwright]):
                span['status'] = 'noop'

            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

    def _emergency_cleanup(self):
        """Emergency cleanup called on program exit."""
        try:
            # Force cleanup all browser processes
            _cleanup_manager.force_cleanup_all()
        except Exception:
            pass

    async def ensure_browser_ready(self) -> None:
        """Ensure browser is started and session is valid."""
        async with self._lock:
            if not self.page or self.page.is_closed():
                await self.start()
            self.last_activity = asyncio.get_event_loop().time()

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL with retry logic and CAPTCHA detection."""
        async with self._operation_span('navigate', url=url) as span:
            await self.ensure_browser_ready()

            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                span['normalized_url'] = url

            for attempt in range(self.retry_count):
                span['attempt'] = attempt + 1
                try:
                    response = await self.page.goto(
                        url,
                        wait_until='domcontentloaded',
                        timeout=30000
                    )

                    current_url = self.page.url.lower()
                    page_title = await self.page.title()

                    if any(x in current_url for x in ['sorry', 'captcha', 'challenge', 'verify']):
                        span['status'] = 'captcha_detected'
                        span['resolved_url'] = current_url
                        return {
                            "url": self.page.url,
                            "title": page_title,
                            "status": "captcha_detected",
                            "error": "CAPTCHA challenge detected. Try alternative sources or RSS feeds."
                        }

                    span['status'] = 'success'
                    span['status_code'] = response.status if response else None
                    span['resolved_url'] = self.page.url
                    return {
                        "url": self.page.url,
                        "title": page_title,
                        "status": "success",
                        "status_code": response.status if response else None
                    }

                except Exception as exc:
                    logger.debug('browser.navigate.retry', extra={'operation': 'navigate', 'attempt': attempt + 1, 'error': str(exc)})
                    if attempt == self.retry_count - 1:
                        span['status'] = 'error'
                        span['error'] = str(exc)
                        return {
                            "url": url,
                            "status": "error",
                            "error": str(exc)
                        }
                    await asyncio.sleep(2 ** attempt)
                    await self.close()
                    await self.start()

    async def screenshot(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Take a screenshot of current page."""
        async with self._operation_span('screenshot', path=path) as span:
            await self.ensure_browser_ready()

            screenshot_bytes = await self.page.screenshot(full_page=True)
            span['bytes'] = len(screenshot_bytes)

            if path:
                with open(path, 'wb') as file_handle:
                    file_handle.write(screenshot_bytes)
                span['status'] = 'saved'
                return {"path": path, "status": "saved"}

            span['status'] = 'captured'
            return {"data": screenshot_bytes.hex(), "status": "captured"}

    async def get_content(self) -> str:
        """Get page content as text."""
        async with self._operation_span('get_content') as span:
            await self.ensure_browser_ready()
            content = await self.page.content()
            span['status'] = 'success' if content else 'empty'
            span['length'] = len(content) if content else 0
            return content

    async def extract_content_smart(self) -> Dict[str, Any]:
        """Extract main content intelligently, filtering ads and boilerplate."""
        async with self._operation_span('extract_content') as span:
            await self.ensure_browser_ready()

            main_content = await self.page.evaluate("""
                () => {
                    // Remove unwanted elements
                    const unwanted = document.querySelectorAll(
                        'nav, header, footer, aside, .ad, .advertisement, ' +
                        '[role="complementary"], .sidebar, .menu, .navigation, ' +
                        '[class*="ad-"], [class*="banner"], [id*="ad-"]'
                    );
                    unwanted.forEach(el => el.remove());

                    const main = document.querySelector(
                        'main, article, [role="main"], .content, #content, .main-content, ' +
                        '[class*="article"], [class*="post-content"]'
                    );
                    const content = main || document.body;

                    const links = Array.from(content.querySelectorAll('a')).map(a => ({
                        text: (a.innerText || '').trim(),
                        href: a.href
                    })).filter(link => link.text && link.href && !link.href.startsWith('javascript:'));

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

            text_value = main_content.get('text', '') if isinstance(main_content, dict) else ''
            links = main_content.get('links', []) if isinstance(main_content, dict) else []
            span['status'] = 'success' if text_value else 'empty'
            span['links'] = len(links) if isinstance(links, list) else 0

            return {
                "url": self.page.url,
                "title": main_content.get('title', '') if isinstance(main_content, dict) else '',
                "text": text_value[:5000],
                "headings": main_content.get('headings', [])[:20] if isinstance(main_content, dict) else [],
                "links": links[:50] if isinstance(links, list) else [],
                "status": "success" if text_value else "empty",
                "method": "playwright"
            }

    async def get_news_smart(self, topic: str = 'ai', max_articles: int = 5) -> Dict[str, Any]:
        """Get news using multiple strategies to avoid CAPTCHAs."""
        async with self._operation_span('get_news', topic=topic, max_articles=max_articles) as span:
            results = []
            errors = []

            url_safe_topic = topic.lower().replace(' ', '-')

            gov_keywords = ['government', 'shutdown', 'federal', 'congress', 'president', 'politics', 'policy', 'trump', 'biden', 'white house']
            if any(kw in topic.lower() for kw in gov_keywords):
                direct_sites = [
                    'https://www.cnn.com/politics/',
                    'https://www.foxnews.com/politics/',
                    'https://www.nbcnews.com/politics/',
                    f'https://www.nytimes.com/search?query={topic.replace(" ", "%20")}',
                    'https://www.washingtonpost.com/politics/',
                    'https://apnews.com/hub/politics',
                    'https://www.reuters.com/world/us/',
                ]
            else:
                direct_sites = [
                    f'https://techcrunch.com/tag/{url_safe_topic}/',
                    f'https://arstechnica.com/{topic}/',
                    f'https://www.theverge.com/search?q={topic}',
                ]

            span['candidate_sources'] = len(direct_sites)

            for site_url in direct_sites:
                try:
                    nav_result = await self.navigate(site_url)

                    if nav_result.get('status') == 'captcha_detected':
                        errors.append(f'{site_url}: CAPTCHA detected')
                        continue

                    if nav_result.get('status') != 'success':
                        errors.append(f'{site_url}: Navigation failed')
                        continue

                    extracted = await self.extract_content_smart()

                    if extracted.get('status') == 'success' and extracted.get('links'):
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
                        break
                    errors.append(f'{site_url}: No content extracted')

                except Exception as exc:
                    errors.append(f'{site_url}: {exc}')
                    continue

            span['status'] = 'success' if results else 'empty'
            span['sources'] = len(results)
            span['errors'] = len(errors)

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
        async with self._operation_span('click', selector=selector) as span:
            await self.ensure_browser_ready()
            await self.page.click(selector)
            span['status'] = 'clicked'
            return {"selector": selector, "status": "clicked"}

    async def fill(self, selector: str, text: str) -> Dict[str, Any]:
        """Fill a form field."""
        async with self._operation_span('fill', selector=selector) as span:
            await self.ensure_browser_ready()
            await self.page.fill(selector, text)
            span['status'] = 'filled'
            return {"selector": selector, "status": "filled"}

    async def evaluate(self, script: str) -> Any:
        """Execute JavaScript in browser context."""
        async with self._operation_span('evaluate') as span:
            await self.ensure_browser_ready()
            result = await self.page.evaluate(script)
            span['status'] = 'success'
            return result

    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> Dict[str, Any]:
        """Wait for an element to appear."""
        async with self._operation_span('wait_for_selector', selector=selector, timeout=timeout) as span:
            await self.ensure_browser_ready()
            await self.page.wait_for_selector(selector, timeout=timeout)
            span['status'] = 'found'
            return {"selector": selector, "status": "found"}

    async def extract_text(self, selector: str) -> str:
        """Extract text content from an element."""
        async with self._operation_span('extract_text', selector=selector) as span:
            await self.ensure_browser_ready()
            element = await self.page.query_selector(selector)
            if element:
                text_value = await element.text_content()
                span['status'] = 'success' if text_value else 'empty'
                span['length'] = len(text_value) if text_value else 0
                return text_value or ''
            span['status'] = 'not_found'
            return ''

    async def get_links(self) -> List[Dict[str, str]]:
        """Get all links on the current page."""
        async with self._operation_span('get_links') as span:
            await self.ensure_browser_ready()
            links = await self.page.query_selector_all("a")
            result = []
            for link in links:
                href = await link.get_attribute("href")
                text = await link.text_content()
                if href:
                    result.append({"href": href, "text": text.strip() if text else ""})
            span['status'] = 'success'
            span['count'] = len(result)
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
        logger.info('browser.execute.start', extra={'tool': tool_name})
        browser = await get_browser(headless=args.get('headless', True))

        # Handle MCP-configured tool names
        if tool_name == 'navigate':
            return await browser.navigate(args.get('url', ''))

        elif tool_name == 'screenshot':
            return await browser.screenshot(args.get('path'))

        elif tool_name == 'click':
            return await browser.click(args.get('selector', ''))

        elif tool_name == 'fill':
            return await browser.fill(
                args.get('selector', ''),
                args.get('text', '')
            )

        elif tool_name == 'extract-text':
            selector = args.get('selector', '')
            text = await browser.extract_text(selector)
            return {"status": "success", "text": text, "selector": selector}

        elif tool_name == 'get-links':
            links = await browser.get_links()
            return {"status": "success", "links": links}

        elif tool_name == 'get-news-smart':
            return await browser.get_news_smart(
                topic=args.get('topic', 'ai'),
                max_articles=args.get('max_articles', 5)
            )

        # Legacy/backward compatibility tool names
        elif tool_name == 'browser_navigate':
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
        logger.exception('browser.execute.error', extra={'tool': tool_name})
        return {"status": "error", "error": str(e)}
