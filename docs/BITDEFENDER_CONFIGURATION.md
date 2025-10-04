# Configuring Bitdefender for Browser Automation

## Why Bitdefender Blocks Browser Automation

Bitdefender's **Advanced Threat Defense** and **Web Protection** modules detect and block:
- Automated browser sessions (Playwright, Selenium)
- Suspicious network patterns
- Script-based web access
- Headless browser activity

This is normal security behavior, but it breaks legitimate browser automation.

## Solution: Whitelist Python & Playwright

### Option 1: Add Python to Bitdefender Exceptions (RECOMMENDED)

1. **Open Bitdefender**
   - Click the Bitdefender icon in system tray
   - Click "Open Bitdefender"

2. **Go to Protection**
   - Click "Protection" in left sidebar
   - Click "Settings" (gear icon)

3. **Add Python Exception**
   - Scroll to "Manage Exceptions"
   - Click "Add Exception"
   - Navigate to: `C:\Users\atchi\AppData\Local\Programs\Python\Python311\python.exe`
   - Click "Add Exception"

4. **Add Playwright Browsers**
   Add these paths as exceptions:
   - `C:\Users\atchi\AppData\Local\ms-playwright\firefox-*\firefox\firefox.exe`
   - `C:\Users\atchi\AppData\Local\ms-playwright\chromium-*\chrome-win\chrome.exe`

### Option 2: Temporarily Disable Web Protection (QUICK TEST)

1. Open Bitdefender
2. Click "Protection" → "Web Protection"
3. Toggle OFF temporarily
4. Test browser automation
5. **Remember to turn back ON after testing**

### Option 3: Add Folder Exceptions

1. Open Bitdefender → Protection → Settings
2. Manage Exceptions → Add Exception
3. Add these folders:
   - `C:\Users\atchi\spec-kit\mcp-ai-agent\`
   - `C:\Users\atchi\AppData\Local\ms-playwright\`

### Option 4: Disable Advanced Threat Defense (NOT RECOMMENDED)

1. Bitdefender → Settings → Advanced Threat Defense
2. Toggle OFF (⚠️ reduces system security)
3. Only for testing - re-enable after

## Recommended Configuration

**Best for security + functionality:**

1. Keep Bitdefender enabled
2. Add only these exceptions:
   - Python executable
   - Playwright Firefox browser
   - Project folder: `C:\Users\atchi\spec-kit\mcp-ai-agent\`

This allows automation while maintaining protection.

## Alternative: Use HTTP-Based Tools

If you can't or don't want to configure Bitdefender, the agent now includes:

### `fetch-news` Tool (HTTP-based)
- Uses simple HTTP requests to RSS feeds
- No browser automation
- Bitdefender usually allows this
- **Works for news queries only**

### Browser Tools (For Everything Else)
- `browse-url` + `browser-extract-smart`
- Requires Bitdefender exception
- **Needed for general web research**

## Testing After Configuration

### Test 1: HTTP News (Should Always Work)
```powershell
cd mcp-ai-agent
python test_news_http.py
```

Expected: Gets AI news from TechCrunch RSS

### Test 2: Browser (Needs Bitdefender Config)
```powershell
cd mcp-ai-agent  
python test_browser_news.py
```

Expected: Firefox opens, navigates, extracts content

### Test 3: Full Agent
```powershell
python -m src.agent.cli run
# Ask: "check the latest AI news"
```

Agent will try:
1. `fetch-news` first (HTTP, should work)
2. `browser-get-news` if needed (requires Bitdefender config)

## What Each Approach Gives You

| Method | News | General Web | Bitdefender Required? |
|--------|------|-------------|----------------------|
| `fetch-news` | ✅ RSS feeds | ❌ No | ❌ Usually works as-is |
| Browser tools | ✅ Full extraction | ✅ Any website | ✅ Yes, needs exception |

## Recommendation

**For full agent capabilities:**
1. Add Python + Playwright to Bitdefender exceptions (Option 1)
2. This enables both news AND general web research
3. Keeps your system protected while allowing automation

**For news only:**
1. Use `fetch-news` tool
2. No Bitdefender configuration needed
3. Limited to RSS feed sources

## Verification

After configuring Bitdefender, verify:
```powershell
# Should complete without errors
python test_browser_news.py
```

If you still get blocks, check:
- Exception was added correctly
- Firefox path is correct
- Web Protection is ON but has exception
- Project folder is whitelisted

## Summary

✅ **HTTP-based `fetch-news`** - Works immediately (news only)
✅ **Browser tools** - Requires Bitdefender config (full capability)
✅ **Agent has both** - Falls back gracefully

Configure Bitdefender for full research capability, or use HTTP tools for news-only queries.
</content>
<task_progress>
- [x] All browser improvements
- [x] HTTP news fetcher (Bitdefender workaround)
- [x] Complete Bitdefender configuration guide
- [x] Task complete
</task_progress>
