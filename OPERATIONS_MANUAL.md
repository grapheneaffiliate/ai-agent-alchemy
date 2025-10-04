# MCP AI Agent - Complete Operations Manual

**Last Updated:** October 1, 2025  
**Status:** Autonomous ReAct implementation complete, browser tools operational, news system enhanced

---

## Executive Summary

This MCP AI Agent uses a ReAct (Reasoning + Acting) architecture to autonomously select and execute tools based on user prompts in a custom web UI. The system integrates news fetching (RSS + web crawling), browser automation (Playwright Firefox), and artifact generation for visual display.

---

## Architecture Overview

### Core Components

```
User (Custom Web UI)
    ↓
WebSocket Handler (web_ui.py)
    ↓
ReAct Loop (react_loop.py) ← AUTONOMOUS DECISION MAKING
    ↓
Plugin Executor (plugin_executor.py)
    ↓
Plugins:
├── News Fetch (news_fetch.py) - RSS feeds
├── Browser (browser.py) - Playwright Firefox
├── Crawl4AI (crawl4ai_plugin.py) - Deep web scraping
├── Time Utils (time_utils.py) - Date/time
└── Kokoro TTS (kokoro_tts.py) - Text-to-speech
    ↓
Artifact Generator (artifacts.py)
    ↓
WebSocket → User (split-panel UI)
```

### Request Flow

```
1. USER PROMPT
   "show me news in Kansas City Missouri"
   
2. WEB_UI.PY
   - Receives via WebSocket
   - Calls execute_react_loop()
   
3. REACT_LOOP.PY (Autonomous Decision Making)
   Iteration 1:
   - LLM sees: system_prompt with tool descriptions
   - LLM decides: <tool>browse-url</tool><args>{"url": "https://www.kansascity.com"}</args>
   - Executes: Plugin Executor → Browser Plugin
   - Result: "Navigated to kansascity.com"
   
   Iteration 2:
   - LLM sees: tool results
   - LLM decides: Need better extraction, use <tool>crawl</tool>
   - Executes: Crawl4AI plugin
   - Result: Markdown content + facts summary
   - Generates: HTML artifact
   
   Iteration 3:
   - LLM sees: crawled content
   - LLM provides: Final summary using actual data
   - Returns: (response_text, artifact_html)
   
4. ARTIFACT DISPLAY
   - Chat panel: Summary text
   - Artifact panel: HTML with articles
```

---

## Plugin Ecosystem

### 1. News Fetch Plugin (`news_fetch.py`)

**Purpose:** Fast, reliable news from curated RSS feeds

**Supported Locations:**
- Seattle, Washington (The Seattle Times, KOMO, KING 5, Seattle PI, Crosscut)
- St. Louis, Missouri (Post-Dispatch, KSDK, KMOV, St. Louis American)
- Miami, Florida (Miami Herald, WSVN, WPLG, Miami New Times)
- New York, NY (NY Times, Gothamist, NY Post)
- Washington DC (Washington Post, DCist, WTOP)
- California (LA Times, SF Chronicle, CalMatters)

**Supported Topics:**
- Robotics (The Robot Report, IEEE Spectrum, Robotics.org, Robohub)
- AI (TechCrunch AI, VentureBeat AI, The Verge AI)
- Tech (TechCrunch, The Verge, Ars Technica)
- General (BBC News, Reuters)

**How It Works:**
1. Receives topic string (e.g., "seattle", "robotics", "miami")
2. Maps topic to feed category via keyword detection
3. Tries RSS feeds in order until one succeeds
4. Returns: `{articles: [{headline, url, summary, published}], topic, method}`

**Tool Call:**
```python
await plugin_executor.execute('news', 'get_news', {
    'topic': 'seattle',
    'max_articles': 10
})
```

**Issues & Mitigations:**
- ⚠️ **Issue:** Location ambiguity (Washington State vs DC)
- ✅ **Fix:** Order-based matching - check "seattle" before "washington"
- ⚠️ **Issue:** Topic list confusion (LLM copied full list in args)
- ✅ **Fix:** Removed list from prompt, show examples only

### 2. Browser Plugin (`browser.py`)

**Purpose:** Navigate to ANY website and extract content

**Technology:** Playwright with Firefox (anti-detection configured)

**Capabilities:**
- `navigate(url)`: Go to any URL
- `extract_content_smart()`: Remove nav/ads, get main content
- `click(selector)`, `fill(selector, text)`: Interact with pages
- `screenshot(path)`: Capture page images
- `get_links()`: Extract all links

**Configuration:**
```python
# Firefox with stealth settings
browser = await playwright.firefox.launch(
    headless=False,  # Set to True for background
    firefox_user_prefs={
        'dom.webdriver.enabled': False,  # Hide automation
        'useAutomationExtension': False,
        'general.useragent.override': 'Mozilla/5.0...'
    }
)
```

**Tool Call:**
```python
await plugin_executor.execute('browser', 'navigate', {
    'url': 'https://www.kansascity.com'
})
```

**Issues & Mitigations:**
- ⚠️ **Issue:** Missing Playwright executable
- ✅ **Fix:** Run `python fix_browser_permanently.py` (auto-installs)
- ⚠️ **Issue:** CAPTCHA challenges
- ✅ **Fix:** Firefox has better bypass than Chromium
- ⚠️ **Issue:** Bitdefender blocking browser launch
- ✅ **Fix:** See `docs/BITDEFENDER_CONFIGURATION.md`

### 3. Crawl4AI Plugin (`crawl4ai_plugin.py`)

**Purpose:** Deep web scraping with clean content extraction

**Advantages over browser:**
- Better content filtering (removes nav, ads, boilerplate)
- Markdown output
- Facts summary extraction
- No browser overhead

**Tool Call:**
```python
await plugin_executor.execute('crawl4ai', 'crawl_url', {
    'url': 'https://www.kansascity.com'
})
```

**Returns:**
```python
{
    'markdown': '# Full content...',
    'facts_summary': 'Key facts extracted...',
    'cleaned_html': '...'
}
```

**Issues & Mitigations:**
- ⚠️ **Issue:** Some sites block crawling
- ✅ **Fix:** Falls back to browser if crawl fails
- ⚠️ **Issue:** JavaScript-rendered content not captured
- ✅ **Fix:** Use browser for dynamic sites

### 4. Time Utils Plugin (`time_utils.py`)

**Purpose:** Date/time information

**Tools:**
- `get_current_time()`: Returns formatted time
- `get_current_date()`: Returns date
- `get_day_info()`: Day of week, etc.

### 5. Kokoro TTS Plugin (`kokoro_tts.py`)

**Purpose:** Text-to-speech for responses

**Endpoint:** http://localhost:8880 (must be running separately)

**Health Check:** `/tts/health` endpoint

---

## ReAct Loop Details

### System Prompt (Critical Component)

Located in `react_loop.py::build_system_prompt()`, this tells the LLM:

1. **Available Tools:**
   - fetch-news, browse-url, crawl, browser-extract-smart, get-time

2. **Tool Format:**
   ```xml
   <tool>tool-name</tool>
   <args>{"key": "value"}</args>
   ```

3. **Decision Logic:**
   - Curated locations → Use fetch-news
   - Other cities → Use browse-url
   - ONE topic string, not a list

4. **Critical Rules:**
   - ALWAYS use tools for current info
   - NO making up information
   - Keep tool calls simple

### Execution Flow

```python
async def execute_react_loop(user_message, agent_api, plugin_executor, max_iterations=5):
    conversation_history = [system_prompt, user_message]
    
    for iteration in range(max_iterations):
        # 1. Get LLM response
        response = await agent_api.generate_response(conversation)
        
        # 2. Parse for tool calls
        tool_calls = parse_tool_calls(response)  # <tool>...</tool><args>...</args>
        
        if not tool_calls:
            return response, artifact_html  # Final answer
        
        # 3. Execute tools
        for tool_name, tool_args in tool_calls:
            result = await plugin_executor.execute(server, func, args)
            format_and_store_result()
        
        # 4. Feed results back to LLM
        conversation_history.append(tool_results)
    
    # 5. Force final summary
    return final_answer_using_last_results()
```

### Tool Call Parsing

Supports 3 formats:

1. **XML-style (primary):**
   ```xml
   <tool>fetch-news</tool>
   <args>{"topic": "seattle", "max_articles": 10}</args>
   ```

2. **Action format:**
   ```
   Action: browse-url
   Args: {"url": "https://example.com"}
   ```

3. **Legacy USE_TOOL:**
   ```
   USE_TOOL: get-time
   ```

### Iteration Limit Handling

**Issue:** LLM kept requesting tools beyond limit
**Fix:** After max_iterations, force final answer:
```python
final_prompt = conversation + "\n\nIMPORTANT: You MUST provide a final answer now using the tool results. DO NOT request more tools."
```

---

## Artifact Generation

### News Artifacts (`generate_news_page`)

**Input:** `{articles: [{headline, url, summary, published}]}`

**Output:** HTML with:
- Grid layout (350px cards, auto-fill)
- Article cards with badge, headline, summary
- Gradient background (#667eea → #764ba2)
- Hover effects, responsive design

**Limit:** 10 articles max to prevent overwhelming UI

### Generic HTML (`generate_generic_html`)

**Purpose:** Format crawled content into clean articles

**Smart Parsing:**
1. Detect headlines (## or **text**)
2. Extract links with text
3. Group into articles
4. Limit to first link per article (prevents off-page spam)

**Key Fix:**
```python
# OLD: Showed ALL links, caused off-page mess
links: article.get('links', [])

# NEW: Show ONLY first link per article
if links:
    link_url = links[0].get('url')  # First link only
    html += f'<a href="{link_url}">Read article →</a>'
```

---

## Issues Encountered & Solutions

### Issue 1: OpenRouter Credit Exhaustion

**Symptom:**
```
Exception: API request failed: 402 - {"error":{"message":"Insufficient credits"}}
```

**Root Cause:** OpenRouter account out of credits

**Solution:** Switched to local Ollama model
```bash
# .env
OPENAI_BASE_URL=http://localhost:11434/v1
MODEL=gemma3:4b
```

**Status:** ✅ RESOLVED

### Issue 2: Location News Returned Wrong Region

**Symptom:** "News in St. Louis Missouri" returned AI news

**Root Cause:** Topic detection didn't map user query to feed category

**Solution:** Added intelligent keyword mapping
```python
location_mapping = {
    'st. louis': 'st_louis',
    'st louis': 'st_louis',
    'saint louis': 'st_louis',
    ...
}

# Check if any key in query
for key, feed in location_mapping.items():
    if key in normalized_query:
        use_feed = feed
        break
```

**Status:** ✅ RESOLVED

### Issue 3: Topic List Confusion

**Symptom:** LLM passed `{"topic": "dallas texas|general|ai|tech|robotics|..."}` 

**Root Cause:** System prompt showed: `"general|ai|tech|robotics|..."`

**Solution:** Changed to examples
```
# OLD
Args: {"topic": "general|ai|tech|robotics|seattle|miami|..."}

# NEW  
Args: {"topic": "STRING", "max_articles": 10}
Topic examples: "robotics", "ai", "seattle"
IMPORTANT: Use ONE topic string
```

**Status:** ✅ RESOLVED

### Issue 4: Washington State vs Washington DC Ambiguity

**Symptom:** "Seattle Washington" returned DC news

**Root Cause:** "washington" in query matched DC before Seattle check

**Solution:** Order-based matching in location_mapping
```python
# Check Seattle FIRST
if 'seattle' in query or ('washington' in query and 'state' in query):
    topic = 'seattle'
# Then check DC
elif 'washington dc' in query or 'dc' in query:
    topic = 'washington_dc'
```

**Status:** ✅ RESOLVED

### Issue 5: Browser Tool Missing Executable

**Symptom:**
```
Tool error: missing executable, which prevents me from retrieving current content
```

**Root Cause:** Playwright not installed or Firefox binary missing

**Solution:** Created `fix_browser_permanently.py`
```bash
cd mcp-ai-agent
python fix_browser_permanently.py
```

Installs:
1. Playwright package (pip install)
2. Firefox browser binary
3. System dependencies
4. Tests browser functionality

**Status:** ✅ RESOLVED (verified working)

### Issue 6: LLM Couldn't See News Headlines

**Symptom:** "I fetched 10 articles but can't show headlines"

**Root Cause:** Articles not formatted in LLM-readable structure

**Solution:** Explicit formatting in tool results
```python
formatted = f"Retrieved {len(articles)} articles:\n\n"
for i, article in enumerate(articles):
    formatted += f"{i+1}. **{article['headline']}**\n"
    formatted += f"   Summary: {article['summary']}\n"
    formatted += f"   URL: {article['url']}\n\n"

# Send to LLM with clear instruction
tool_context = f"""=== NEWS ARTICLES RETRIEVED ===
{formatted}
You MUST use the headlines above."""
```

**Status:** ✅ RESOLVED

### Issue 7: Artifacts Showed Messy Links

**Symptom:** "Links that go off the page, ridiculous"

**Root Cause:** `generate_generic_html()` displayed ALL extracted links

**Solution:** Limit to first link only per article
```python
# OLD: Loop through all links
for link in article['links']:
    html += f'<a href="{link}">{link}</a>'

# NEW: First link only, clean display
if links:
    link_url = links[0].get('url', '#')
    link_text = links[0].get('text', 'Read more')[:50]  # Truncate
    html += f'<a href="{link_url}">{link_text} →</a>'
```

**Status:** ✅ RESOLVED

### Issue 8: API Request Timeouts

**Symptom:**
```
Exception: API request timed out
httpx.ReadTimeout
```

**Root Cause:** Long news contexts (10 articles) + slow local model

**Solution:** Increased timeout
```python
# api.py
timeout=120.0  # Was 60.0
```

**Status:** ✅ RESOLVED

### Issue 9: Iteration Limit Without Summary

**Symptom:** "I've reached my iteration limit" with no answer

**Root Cause:** ReAct loop hit max iterations while agent still requesting tools

**Solution:** Force final summary
```python
# After max_iterations
final_prompt = conversation_history + "\n\nIMPORTANT: You MUST provide final answer now. DO NOT request more tools."
final_response = await agent_api.generate_response(final_prompt)
return final_response, artifact_html
```

**Status:** ✅ RESOLVED

---

## How The Agent SHOULD Function

### Ideal User Experience

**User enters:** "show me news in Kansas City Missouri"

**Expected behavior:**

1. **ReAct Iteration 1:**
   ```
   LLM Reasoning: "Kansas City doesn't have RSS feeds, I'll browse their news site"
   Tool Request: <tool>browse-url</tool><args>{"url": "https://www.kansascity.com"}</args>
   Execution: Browser navigates, extracts basic content
   Result: "Navigated successfully"
   ```

2. **ReAct Iteration 2:**
   ```
   LLM Reasoning: "I need better content extraction"
   Tool Request: <tool>browser-extract-smart</tool><args>{}</args>
   Execution: Extracts main content, filters nav/ads
   Result: {text: "...", headings: [...], links: [...]}
   ```

3. **ReAct Iteration 3:**
   ```
   LLM Reasoning: "I have content, let me provide summary"
   NO TOOL REQUEST
   Final Answer: "Here's the latest Kansas City news:\n1. [headline]\n2. [headline]..."
   Artifact: HTML with article cards
   ```

4. **Display:**
   - **Left panel:** Summary with headlines
   - **Right panel:** Beautiful HTML artifact with clickable articles

### Ideal Flow for Different Query Types

#### Curated Location (Seattle)
```
User: "show me news in seattle washington"
→ ReAct Iteration 1: fetch-news topic="seattle"
→ Gets: 10 rich articles from Seattle Times/KOMO
→ Generates: News artifact
→ Final answer: Lists headlines with summaries
→ Fast: 1 iteration, ~10 seconds
```

#### Topic Query (Robotics)
```
User: "latest robotics news"
→ ReAct Iteration 1: fetch-news topic="robotics"
→ Gets: Articles from The Robot Report, IEEE
→ Generates: News artifact
→ Final answer: Lists robotics headlines
→ Fast: 1 iteration, ~10 seconds
```

#### Uncurated Location (Kansas City)
```
User: "show me news in kansas city missouri"
→ ReAct Iteration 1: browse-url kansascity.com
→ Browser navigates
→ ReAct Iteration 2: browser-extract-smart OR crawl
→ Extracts content
→ Generates: Generic HTML artifact
→ Final answer: Summarizes extracted content
→ Slower: 2-3 iterations, ~30 seconds
```

#### Arbitrary Website
```
User: "show me news from cnn.com"
→ ReAct Iteration 1: browse-url cnn.com
→ Browser navigates
→ ReAct Iteration 2: browser-extract-smart
→ Extracts headlines
→ Generates: HTML artifact
→ Final answer: Lists CNN headlines
→ Medium: 2 iterations, ~20 seconds
```

---

## Configuration Files

### `.env`

```bash
# LLM Configuration
OPENAI_BASE_URL=http://localhost:11434/v1  # Ollama local
MODEL=gemma3:4b

# Alternative: OpenRouter (requires credits)
# OPENAI_API_KEY=sk-or-v1-...
# OPENAI_BASE_URL=https://openrouter.ai/api/v1
# MODEL=anthropic/claude-sonnet-4.5

# TTS (optional)
KOKORO_TTS_URL=http://localhost:8880
KOKORO_TTS_VOICE=af_sky
```

### `config/mcp_tools.json`

Defines available tools for CLI mode. **Note:** Web UI uses ReAct loop, not this config.

---

## Testing & Verification

### Quick Tests

**1. News RSS Feeds:**
```bash
cd mcp-ai-agent
python test_news_integration.py
```

Expected output:
```
✓ Fetched 5 articles for general
✓ Fetched 5 articles for robotics
✓ Fetched 5 articles for seattle
✓ Fetched 5 articles for miami
```

**2. Browser Functionality:**
```bash
python fix_browser_permanently.py
```

Expected:
```
✅ BROWSER IS WORKING!
✓ Browser started successfully
✓ Navigation test: success
✓ Content extraction: 189 chars
```

**3. End-to-End (Manual):**
```bash
python start_custom_ui.py
# Open http://localhost:9000
# Try: "show me news in seattle washington"
```

Expected:
- Chat shows: Headlines with summaries
- Artifact panel shows: Beautiful HTML cards
- Terminal shows: Debug output with topic detection

---

## Debugging

### Enable Debug Output

Terminal logs show:
```
============================================================
USER MESSAGE: show me news in Kansas City Missouri
============================================================

🎯 DETECTED TOPIC: 'kansas city' from query: '...'

============================================================
ReAct Iteration 1/5
============================================================
✓ Parsed XML tool call: browse-url with {'url': '...'}
🔧 Executing 1 tool(s)...
   ✓ Generated HTML artifact from crawled content

📰 NEWS CONTEXT SENT TO LLM:
   Topic: kansas city
   Articles: 10
   First headline: [actual headline]
```

### Common Issues

**No articles displayed:**
- Check: `📰 NEWS CONTEXT SENT TO LLM` in logs
- If missing: Topic detection failed
- If present: LLM ignoring results (check model quality)

**Browser errors:**
- Run: `python fix_browser_permanently.py`
- Check: Bitdefender not blocking
- Verify: Firefox installed via Playwright

**Slow responses:**
- Check: Model type (local models slower)
- Increase: max_iterations if hitting limit
- Reduce: max_articles to 5

**Artifacts not showing:**
- Check: `✓ Generated HTML artifact` in logs
- Verify: WebSocket sending artifact message
- Check: Browser console for JS errors

---

## Current State

### What's Working ✅

1. **ReAct Loop:** Autonomous tool selection
2. **News Fetch:** 6 locations + 4 topics via RSS
3. **Browser:** Firefox with anti-detection
4. **Crawl4AI:** Deep web scraping
5. **Artifacts:** Smart HTML generation
6. **Location Detection:** Disambiguates Seattle/DC
7. **API:** 120s timeout for long contexts

### What Needs Work ⚠️

1. **Limited Extraction:** Some news sites return few articles
   - **Why:** Anti-scraping, JavaScript rendering
   - **Mitigation:** Use RSS when available, accept limitations

2. **Iteration Efficiency:** Sometimes uses all 5 iterations
   - **Why:** LLM tries multiple approaches
   - **Mitigation:** Increased from 3 to 5, acceptable

3. **Model Quality:** Local model (gemma3:4b) sometimes struggles
   - **Why:** Smaller model, less capable than Claude/GPT-4
   - **Mitigation:** Consider cloud API for production

4. **Kansas City (and similar cities):** Limited content
   - **Why:** No dedicated RSS feeds, site anti-scraping
   - **Mitigation:** Could add KC RSS feeds to news_fetch.py

---

## Future Enhancements

### High Priority

1. **Add More City RSS Feeds:**
   ```python
   'kansas_city': [
       ('Kansas City Star', 'https://www.kansascity.com/feed/'),
       ('KSHB 41', 'https://www.kshb.com/news/feed'),
   ]
   ```

2. **Improve Crawl Content Parsing:**
   - Better headline extraction
   - Article segmentation
   - Image capture

3. **Add Social Media:**
   - Twitter/X API integration
   - Reddit news feeds
   - Hacker News API

### Medium Priority

1. **Multi-Tool Chaining:**
   - Browse → Extract → Summarize in one call
   - Parallel tool execution

2. **Caching:**
   - Cache RSS feed results (5-minute TTL)
   - Reduce API calls

3. **Streaming Responses:**
   - Show tool execution progress
   - Stream final answer

### Low Priority

1. **More LLM Providers:**
   - Anthropic Claude direct
   - Google Gemini
   - Azure OpenAI

2. **Advanced Filtering:**
   - Topic relevance scoring
   - Duplicate detection
   - Content quality assessment

---

## Quick Reference Commands

### Start Server
```bash
cd mcp-ai-agent
python start_custom_ui.py
# Open: http://localhost:9000
```

### Fix Browser
```bash
python fix_browser_permanently.py
```

### Test News
```bash
python test_news_integration.py
```

### Install Dependencies
```bash
pip install -r requirements.txt
python -m playwright install firefox
```

---

## Critical Files Reference

| File | Purpose | Key Functions |
|------|---------|---------------|
| `src/agent/web_ui.py` | WebSocket handler | `websocket_endpoint()` |
| `src/agent/react_loop.py` | Autonomous loop | `execute_react_loop()`, `parse_tool_calls()` |
| `src/agent/plugin_executor.py` | Tool dispatcher | `execute()`, `_execute_*_tool()` |
| `src/plugins/news_fetch.py` | RSS news | `get_news()`, location/topic mapping |
| `src/plugins/browser.py` | Web automation | `navigate()`, `extract_content_smart()` |
| `src/plugins/crawl4ai_plugin.py` | Web scraping | `crawl_url()` |
| `src/agent/artifacts.py` | HTML generation | `generate_news_page()`, `generate_generic_html()` |
| `src/agent/api.py` | LLM interface | `generate_response()` |

---

## Operating the Agent (Step-by-Step)

### For Next Agent/Developer

1. **Start the server:**
   ```bash
   cd mcp-ai-agent
   python start_custom_ui.py
   ```

2. **Open browser:** http://localhost:9000

3. **Test with curated location:**
   - Type: "show me news in seattle washington"
   - Expect: Fast response (1 iteration), rich articles, HTML artifact

4. **Test with topic:**
   - Type: "latest robotics news"
   - Expect: Robotics-specific articles from specialized sources

5. **Test with uncurated location:**
   - Type: "show me news in kansas city missouri"
   - Expect: 2-3 iterations, crawled content, HTML artifact

6. **Monitor terminal:**
   - Look for: `🎯 DETECTED TOPIC`
   - Look for: `📰 NEWS CONTEXT SENT TO LLM`
   - Look for: `✓ Generated HTML artifact`
   - Check: No error traces

7. **If issues arise:**
   - Browser errors → Run `fix_browser_permanently.py`
   - Slow responses → Check model in .env
   - No articles → Check RSS feeds still active
   - Bad artifacts → Review `artifacts.py` formatting

---

## Summary for Handoff

**The agent is FULLY OPERATIONAL with:**
- ✅ Autonomous ReAct loop (decides which tools to use)
- ✅ 6 location-specific news feeds
- ✅ 4 topic-specific news categories  
- ✅ Browser automation (Playwright Firefox)
- ✅ Web crawling (Crawl4AI)
- ✅ Smart artifact generation
- ✅ Proper error handling
- ✅ 120s API timeout
- ✅ Clean HTML output (first link only per article)

**Known Limitations:**
- Some news sites have anti-scraping (expected)
- Local models slower than cloud APIs (acceptable)
- Iteration limit at 5 (reasonable for most queries)

**The system works as designed. For cities without RSS feeds, it autonomously browses their news sites and extracts content. Restart the server and test!**
