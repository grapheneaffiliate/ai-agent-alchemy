# Troubleshooting Guide

## Common Issues and Solutions

### 1. Pydantic Core Installation Error

**Error Message:**
```
error: uninstall-no-record-file
× Cannot uninstall pydantic_core 2.16.3
╰─> The package's contents are unknown: no RECORD file was found for pydantic_core.
```

**What It Means:**
This error occurs when pip's metadata for pydantic_core is corrupted or missing. It's typically caused by:
- Interrupted installation
- Multiple pip versions
- Package installed via different methods

**Is It Serious?**
Not immediately critical, but it prevents Crawl4AI and other packages from installing/upgrading properly.

**Solution:**
```bash
# Force reinstall the corrupted package
cd mcp-ai-agent
pip install --force-reinstall --no-deps pydantic_core==2.16.3

# Then reinstall dependent packages
pip install pydantic crawl4ai[all]
```

**Alternative Solution (if above fails):**
```bash
# Uninstall all pydantic packages
pip uninstall pydantic pydantic-core -y

# Reinstall fresh
pip install pydantic==2.9.0 pydantic-core==2.16.3
```

### 2. Pip Update Notice

**Message:**
```
[notice] A new release of pip is available: 25.1 -> 25.2
[notice] To update, run: python.exe -m pip install --upgrade pip
```

**What It Means:**
Your pip version is outdated. This is informational, not an error.

**Should You Update?**
Optional but recommended for:
- Security fixes
- Performance improvements
- Bug fixes

**How to Update:**
```bash
python -m pip install --upgrade pip
```

### 3. Browser "Target page, context or browser has been closed"

**Error Message:**
```
Tool error: Page.goto: Target page, context or browser has been closed
```

**Cause:**
Browser session terminated unexpectedly between tool calls.

**Solution (Implemented):**
The enhanced browser plugin now includes:
- Auto-recovery with `ensure_browser_ready()`
- Retry logic with exponential backoff
- Session persistence across requests

**Manual Workaround (if still occurring):**
```bash
# Restart the agent
python -m src.agent.cli run
```

### 4. CAPTCHA Detection

**Message:**
```
{
  "status": "captcha_detected",
  "error": "CAPTCHA challenge detected. Try alternative sources."
}
```

**What It Means:**
Website detected automation and showed CAPTCHA.

**Solutions:**
1. Use `browser-get-news` tool instead of direct Google search
2. Try different news sources
3. Wait a few minutes before retrying
4. Ensure Firefox is being used (not Chromium)

**Verify Firefox:**
```python
python -c "from src.plugins.browser import BrowserPlugin; import asyncio; async def test(): b = BrowserPlugin(); await b.start(); print('Browser:', b.browser.browser_type.name); await b.close(); asyncio.run(test())"
```

### 5. Crawl4AI Import Error

**Error Message:**
```
ImportError: cannot import name 'validate_core_schema' from 'pydantic_core'
```

**Cause:**
Version mismatch between pydantic and pydantic-core.

**Solution:**
```bash
# Install specific compatible versions
pip install pydantic==2.9.0 pydantic-core==2.16.3 --force-reinstall

# Then reinstall crawl4ai
pip install "crawl4ai[all]"
```

### 6. Playwright Browser Not Found

**Error Message:**
```
playwright._impl._errors.Error: Executable doesn't exist
```

**Cause:**
Playwright browsers not installed.

**Solution:**
```bash
# Install Firefox for Playwright
playwright install firefox

# Or install all browsers
playwright install
```

**Verify Installation:**
```bash
playwright --version
playwright list
```

### 7. Memory/Session Issues

**Error Message:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'memory/sessions.json'
```

**Cause:**
Memory directory or file doesn't exist.

**Solution:**
```bash
# Create memory directory
mkdir -p mcp-ai-agent/memory

# Create empty sessions file
echo '{}' > mcp-ai-agent/memory/sessions.json

# Or let the agent create it
python -m src.agent.cli run
```

### 8. OpenRouter API Errors

**Error Message:**
```
API request failed: 401 - Unauthorized
```

**Cause:**
Missing or invalid OpenRouter API key.

**Solution:**
```bash
# Check .env file exists
cat mcp-ai-agent/.env

# Verify API key format
echo $OPENAI_API_KEY  # Should start with sk-or-v1-

# If missing, create .env
cat > mcp-ai-agent/.env << EOF
OPENAI_API_KEY=sk-or-v1-your-key-here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
MODEL=x-ai/grok-code-fast-1
EOF
```

### 9. Tool Not Found

**Error Message:**
```
No matching tools found.
```

**Cause:**
Tool not properly registered in config.

**Solution:**
```bash
# Verify tool configuration
cat mcp-ai-agent/config/mcp_tools.json

# Check JSON syntax
python -c "import json; json.load(open('mcp-ai-agent/config/mcp_tools.json'))"

# Restart agent to reload tools
python -m src.agent.cli run
```

### 10. Import Errors

**Error Message:**
```
ModuleNotFoundError: No module named 'src'
```

**Cause:**
Running from wrong directory or package not installed.

**Solution:**
```bash
# Ensure you're in the right directory
cd mcp-ai-agent

# Install in development mode
pip install -e .

# Run from project root
python -m src.agent.cli run
```

## Debugging Tips

### Enable Verbose Logging

Add debug prints to `src/agent/api.py`:
```python
print(f"DEBUG: Request to {self.base_url}")
print(f"DEBUG: Model: {self.model}")
print(f"DEBUG: Messages count: {len(messages)}")
```

### Test Components Individually

```bash
# Test browser plugin
python -c "from src.plugins.browser import get_browser; print('✓')"

# Test time plugin
python -c "from src.plugins.time_utils import get_time_plugin; print('✓')"

# Test MCP loader
python -c "from src.agent.mcp_loader import MCPLoader; print('✓')"

# Test plugin executor
python -c "from src.agent.plugin_executor import PluginExecutor; print('✓')"
```

### Check Dependencies

```bash
# List installed packages
pip list | grep -E '(playwright|pydantic|crawl4ai)'

# Verify versions
python -c "import pydantic; print('Pydantic:', pydantic.__version__)"
python -c "import playwright; print('Playwright:', playwright.__version__)"
```

### Test Browser Manually

```python
# test_browser_manual.py
import asyncio
from src.plugins.browser import BrowserPlugin

async def test():
    browser = BrowserPlugin(headless=False)
    await browser.start()
    print("✓ Browser started")
    
    result = await browser.navigate("https://example.com")
    print(f"✓ Navigated: {result}")
    
    content = await browser.extract_content_smart()
    print(f"✓ Extracted: {content['title']}")
    
    await browser.close()
    print("✓ Browser closed")

asyncio.run(test())
```

## Getting Help

If problems persist:

1. **Check logs** for detailed error messages
2. **Run tests** to isolate the issue:
   ```bash
   pytest tests/ -v
   ```
3. **Verify environment**:
   ```bash
   python --version  # Should be 3.11+
   pip --version
   playwright --version
   ```
4. **Clean install**:
   ```bash
   pip uninstall -y mcp-ai-agent
   pip install -e .
   playwright install firefox
   ```

## Quick Reference

| Issue | Command |
|-------|---------|
| Fix pydantic | `pip install --force-reinstall pydantic-core==2.16.3` |
| Update pip | `python -m pip install --upgrade pip` |
| Install browsers | `playwright install firefox` |
| Reset memory | `rm memory/sessions.json && echo '{}' > memory/sessions.json` |
| Reload tools | Restart agent |
| Clean install | `pip uninstall -y mcp-ai-agent && pip install -e .` |

## Prevention

To avoid common issues:

1. **Use virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

2. **Keep dependencies updated**:
   ```bash
   pip install --upgrade pip
   pip install -e . --upgrade
   ```

3. **Regular cleanup**:
   ```bash
   pip cache purge
   playwright install firefox
   ```

4. **Backup config files**:
   ```bash
   cp config/mcp_tools.json config/mcp_tools.json.backup
   cp .env .env.backup
