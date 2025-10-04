# Browser Automation Improvements

## Current Issues Analysis

### 1. CAPTCHA Detection
**Problem**: Google and other sites detect automated browsing via Playwright's default fingerprint.

**Root Causes**:
- Default Playwright user agent is easily identifiable
- Missing browser context settings (viewport, locale, timezone)
- No stealth plugins or anti-detection measures
- Headless mode detection

### 2. Session Management
**Problem**: Browser closes unexpectedly between tool calls ("browser has been closed" error).

**Root Causes**:
- Singleton pattern doesn't handle concurrent requests properly
- No session timeout or keepalive mechanism
- Browser context gets garbage collected prematurely
- No error recovery for closed sessions

### 3. Information Extraction
**Problem**: Agent can't find relevant information or provide complete summaries.

**Root Causes**:
- No intelligent content parsing (returns raw HTML)
- No text extraction or summarization
- No structured data extraction
- Doesn't filter ads, navigation, or boilerplate content

## Proposed Solutions

### Solution 1: Anti-Detection & Stealth Mode

```python
async def start(self) -> None:
    """Launch browser with anti-detection settings."""
    if not self.playwright:
        self.playwright = await async_playwright().start()
        
        # Launch with stealth settings
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        
        # Create context with realistic browser settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        # Inject stealth scripts
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
        
        self.page = await self.context.new_page()
```

### Solution 2: Session Management with Auto-Recovery

```python
class BrowserPlugin:
    def __init__(self, headless: bool = False, session_timeout: int = 300):
        self.headless = headless
        self.session_timeout = session_timeout
        self.last_activity = None
        self._lock = asyncio.Lock()
        
    async def ensure_browser_ready(self) -> None:
        """Ensure browser is started and session is valid."""
        async with self._lock:
            if not self.page or self.page.is_closed():
                await self.start()
            self.last_activity = asyncio.get_event_loop().time()
    
    async def navigate(self, url: str, retry_count: int = 3) -> Dict[str, Any]:
        """Navigate with retry logic and error recovery."""
        await self.ensure_browser_ready()
        
        for attempt in range(retry_count):
            try:
                response = await self.page.goto(
                    url, 
                    wait_until='domcontentloaded',
                    timeout=30000
                )
                
                # Check if we hit a CAPTCHA or error page
                if 'sorry' in self.page.url or 'captcha' in self.page.url.lower():
                    return {
                        "url": self.page.url,
                        "title": await self.page.title(),
                        "status": "captcha_detected",
                        "error": "CAPTCHA challenge detected. Try alternative sources."
                    }
                
                return {
                    "url": self.page.url,
                    "title": await self.page.title(),
                    "status": "success",
                    "status_code": response.status if response else None
                }
                
            except Exception as e:
                if attempt == retry_count - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                await self.start()  # Restart browser on failure
```

### Solution 3: Integrate Crawl4AI for Content Extraction

Per the custom instructions, Crawl4AI is available. Let's leverage it:

```python
import subprocess
import json
import tempfile

async def extract_content_smart(self, url: str) -> Dict[str, Any]:
    """Extract content using Crawl4AI for better results."""
    await self.ensure_browser_ready()
    
    try:
        # Use crawl4ai CLI for intelligent extraction
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        result = subprocess.run([
            'crwl', 'crawl', url,
            '-o', 'markdown',
            '--output-file', output_path
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(output_path):
            with open(output_path, 'r') as f:
                content = json.load(f)
            os.unlink(output_path)
            
            return {
                "url": url,
                "markdown": content.get('markdown', ''),
                "title": content.get('title', ''),
                "status": "success",
                "method": "crawl4ai"
            }
    except Exception as e:
        pass  # Fall back to Playwright extraction
    
    # Fallback: Use Playwright with intelligent extraction
    await self.page.goto(url, wait_until='domcontentloaded')
    
    # Extract main content (remove nav, footer, ads)
    main_content = await self.page.evaluate("""
        () => {
            // Remove unwanted elements
            const unwanted = document.querySelectorAll('nav, header, footer, aside, .ad, .advertisement, [role="complementary"]');
            unwanted.forEach(el => el.remove());
            
            // Find main content
            const main = document.querySelector('main, article, [role="main"], .content, #content');
            const content = main || document.body;
            
            return {
                text: content.innerText,
                html: content.innerHTML,
                title: document.title,
                headings: Array.from(document.querySelectorAll('h1, h2, h3')).map(h => h.innerText),
                links: Array.from(content.querySelectorAll('a')).map(a => ({
                    text: a.innerText,
                    href: a.href
                }))
            };
        }
    """)
    
    return {
        "url": self.page.url,
        "title": main_content.get('title', ''),
        "text": main_content.get('text', ''),
        "headings": main_content.get('headings', []),
        "links": main_content.get('links', [])[:50],  # Limit links
        "status": "success",
        "method": "playwright"
    }
```

### Solution 4: Alternative Sources for News

```python
async def get_news_smart(self, topic: str, date: str = None) -> Dict[str, Any]:
    """Get news using multiple strategies to avoid CAPTCHAs."""
    
    # Strategy 1: Direct RSS feeds (no CAPTCHA)
    rss_sources = {
        'ai': [
            'https://www.technologyreview.com/feed/',
            'https://venturebeat.com/category/ai/feed/',
            'https://techcrunch.com/category/artificial-intelligence/feed/'
        ],
        'tech': [
            'https://www.theverge.com/rss/index.xml',
            'https://arstechnica.com/feed/'
        ]
    }
    
    # Strategy 2: News API services (if available)
    # Strategy 3: Direct site access with stealth
    # Strategy 4: Alternative search engines (DuckDuckGo, Bing)
    
    results = []
    
    # Try RSS first (fastest, no CAPTCHA)
    for feed_url in rss_sources.get(topic, [])[:3]:
        try:
            await self.navigate(feed_url)
            content = await self.get_content()
            # Parse RSS XML...
            results.append({"source": feed_url, "content": content[:500]})
        except Exception as e:
            continue
    
    # Try alternative search engines
    alt_search_urls = [
        f"https://duckduckgo.com/?q={topic}+news+today",
        f"https://www.bing.com/news/search?q={topic}",
    ]
    
    for search_url in alt_search_urls:
        try:
            result = await self.navigate(search_url)
            if result.get('status') == 'success':
                extracted = await self.extract_content_smart(search_url)
                results.append(extracted)
                break
        except Exception:
            continue
    
    return {
        "topic": topic,
        "results": results,
        "sources_tried": len(rss_sources.get(topic, [])) + len(alt_search_urls),
        "successful": len(results)
    }
```

## Implementation Priority

1. **High Priority** (Immediate):
   - Add anti-detection browser settings
   - Implement session auto-recovery
   - Add retry logic with exponential backoff

2. **Medium Priority** (Next iteration):
   - Integrate Crawl4AI for content extraction
   - Implement alternative news sources (RSS, APIs)
   - Add content summarization

3. **Low Priority** (Future enhancement):
   - Implement browser fingerprint randomization
   - Add proxy rotation support
   - Implement rate limiting and polite crawling

## Alternative Approaches

### Option A: Use Crawl4AI Exclusively
Replace Playwright browser plugin with Crawl4AI wrapper:
- Better at avoiding detection
- Built-in content extraction
- Already available per custom instructions

### Option B: Hybrid Approach
- Use Crawl4AI for general web scraping
- Keep Playwright for interactive tasks (clicking, filling forms)
- Choose tool based on task type

### Option C: News-Specific Tools
- Create dedicated news aggregator tool
- Use NewsAPI, RSS feeds, or news-specific APIs
- Avoid web scraping for news entirely

## Recommended Implementation

**Phase 1** (Now):
```bash
# Update browser.py with anti-detection
# Add session management improvements
# Implement retry logic
```

**Phase 2** (Next):
```bash
# Create news-specific tool using RSS/APIs
# Integrate Crawl4AI as alternative extraction method
# Add content summarization
```

**Phase 3** (Future):
```bash
# Advanced fingerprint randomization
# Proxy support
# Performance optimization
```

## Testing Strategy

1. Test against common CAPTCHA triggers:
   - Google search
   - Twitter/X
   - LinkedIn

2. Verify session persistence:
   - Multiple requests without restart
   - Recovery from crashes

3. Content extraction quality:
   - Compare raw HTML vs. extracted content
   - Verify summary accuracy

4. Performance benchmarks:
   - Time to first content
   - Memory usage
   - Success rate across 100 requests

## Configuration Example

```python
# .env additions
BROWSER_HEADLESS=false  # Set true for production
BROWSER_STEALTH_MODE=true
BROWSER_SESSION_TIMEOUT=300
BROWSER_RETRY_COUNT=3
BROWSER_USER_AGENT=Mozilla/5.0...
NEWS_API_KEY=your_api_key_here  # Optional
USE_CRAWL4AI=true  # Prefer crawl4ai when available
```

## Monitoring & Metrics

Track:
- CAPTCHA detection rate
- Session failure rate
- Content extraction success rate
- Average response time
- Browser resource usage

Log to: `mcp-ai-agent/logs/browser_metrics.json`
