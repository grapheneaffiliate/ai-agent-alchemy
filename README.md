# MCP AI Agent

A sophisticated, modular AI agent with MCP (Model Context Protocol) integration, browser automation, and **Custom Web UI** with artifact generation support.

## ✨ Features

- **Interactive Web UI**: Beautiful browser-based interface with real-time chat
- **Browser Automation**: Full Playwright-based web browsing with anti-detection
- **Artifact Generation**: HTML news pages, D3.js charts, SVG graphics
- **MermaidJS Support**: Flowcharts, sequence diagrams, pie charts
- **Python Code Execution**: Pyodide integration for data analysis
- **Advanced Web Crawling**: Crawl4AI integration with clean markdown extraction
- **News Fetching**: Multi-source RSS/HTTP news aggregation
- **TTS Integration**: Kokoro TTS for voice responses
- **Improved Text Formatting**: Auto-formatted responses with proper structure

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-ai-agent
cd mcp-ai-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your OpenRouter API key
```

### Usage

**Custom Web UI (Recommended):**
```bash
python start_custom_ui.py
# Open browser to http://localhost:9000
```

**Alternative Server Start:**
```bash
python -m uvicorn src.agent.server:app --host 0.0.0.0 --port 9000
```

**Terminal CLI:**
```bash
python -m src.agent.cli
```

### Fixed Import Issues
- Changed relative imports to absolute imports in `src/agent/react_loop.py` to prevent "attempted relative import beyond top-level package" errors
- Import path: `from src.plugins.search import SearchPlugin` (instead of `..plugins.search`)

## 🎯 Example Interactions

### In the Custom Web UI

```
You: Show me the latest AI news
Agent: [Fetches news and generates beautiful HTML page]
       [Displays interactive news grid in artifact panel]
```

```
You: crawl https://example.com
Agent: [Extracts clean content, provides brief summary]
       [Full markdown saved to artifact]
```

```
You: Create a flowchart for user authentication
Agent: [Generates MermaidJS diagram]
       ```mermaid
       flowchart TD
           Start --> Login
           Login --> Auth{Valid?}
           Auth -->|Yes| Dashboard
           Auth -->|No| Error
       ```
```

### Native Custom UI Features

**Artifacts (HTML/SVG):**
```
→ Trigger: "show", "display", "create"
→ Result: Interactive content in artifact panel
```

**MermaidJS Diagrams:**
````
→ Code fence: ```mermaid
→ Custom Web UI renders beautiful diagram
````

**Python Execution:**
````
→ Code fence: ```python
→ Run button executes code with Pyodide
````

## 🔧 Requirements

- Python 3.11+
- OpenRouter API key ([get one](https://openrouter.ai/keys))
- Playwright (for browser automation)
- Optional: Kokoro TTS server

## 📁 Project Structure

```
mcp-ai-agent/
├── .clinerules               # Persistent operational knowledge
├── .env                      # API keys and configuration
├── start_custom_ui.py        # Custom Web UI launcher
├── ui.html                   # Custom Web UI interface
├── pyproject.toml            # Project metadata
├── README.md                 # This file
├── config/
│   └── mcp_tools.json        # MCP tool configurations
├── docs/
│   ├── ARTIFACTS_GUIDE.md           # Complete artifact guide
│   ├── CRAWL4AI_GUIDE.md            # Web crawling documentation
│   ├── CUSTOM_UI_GUIDE.md           # Custom UI documentation
│   ├── BROWSER_IMPROVEMENTS.md      # Browser automation guide
│   └── TROUBLESHOOTING.md           # Common issues
├── src/
│   ├── agent/
│   │   ├── core.py                  # Agent orchestration
│   │   ├── api.py                   # OpenRouter integration
│   │   ├── web_ui.py                # Custom Web UI WebSocket server
│   │   ├── artifacts.py             # HTML/SVG/vis generation
│   │   ├── plugin_executor.py       # Plugin system
│   │   └── memory.py                # Session persistence
│   └── plugins/
│       ├── browser.py               # Playwright automation
│       ├── crawl4ai_plugin.py       # Advanced web crawling
│       ├── news_fetch.py            # News aggregation
│       ├── kokoro_tts.py            # Text-to-speech
│       └── time_utils.py            # Time/date utilities
└── tests/                    # Test suite
```

## 🎨 Features in Detail

### Artifact Generation

Create interactive visual content with simple commands:

| Trigger | Result | Example |
|---------|--------|---------|
| `show`, `display` | HTML artifact | "Show me AI news" |
| `create chart` | D3.js visualization | "Create chart of sales" |
| `create svg` | SVG graphic | "Create SVG with text Hello" |

### Browser Automation

| Feature | Status | Notes |
|---------|--------|-------|
| Page Navigation | ✅ Working | Full Playwright support |
| Smart Extraction | ✅ Working | Clean content extraction |
| Anti-Detection | ✅ Working | Stealth mode enabled |
| Screenshot Capture | ✅ Working | PNG format |

### Crawl4AI Integration

Advanced web scraping with clean markdown extraction:

- **Content Filtering**: Removes navigation, ads, boilerplate
- **Fact Extraction**: Automatically extracts location, phone, services
- **Clean Output**: Professional summaries + full markdown in artifacts
- **Anti-Hallucination**: Forces LLM to use actual crawled data

## 🐛 Troubleshooting

### Artifacts Not Showing

1. Make sure you use trigger words: "show", "display", "create"
2. Check server logs for errors
3. Verify HTML syntax in server logs

### Browser Issues

1. Install Playwright browsers: `python -m playwright install`
2. Check Bitdefender isn't blocking
3. See `docs/BITDEFENDER_CONFIGURATION.md`

### Crawl Results Inaccurate

1. Restart server: `python start_custom_ui.py`
2. Check terminal logs for DEBUG output showing facts_summary
3. Verify crawled content in artifact panel
4. See `docs/CRAWL4AI_GUIDE.md`

## 🛠️ Custom UI Features

The Custom Web UI provides:

- ✅ Split-panel layout (chat + artifacts)
- ✅ Real-time WebSocket communication
- ✅ MermaidJS auto-rendering
- ✅ Python code execution (Pyodide)
- ✅ Syntax highlighting
- ✅ Markdown formatting
- ✅ Text-to-speech (if Kokoro TTS running)

## 📚 Documentation

### User Guides

- **[Custom UI Guide](CUSTOM_UI_GUIDE.md)** - Complete Custom Web UI documentation
- **[Artifacts Guide](docs/ARTIFACTS_GUIDE.md)** - HTML/SVG/visualization guide
- **[Crawl4AI Guide](docs/CRAWL4AI_GUIDE.md)** - Web scraping documentation
- **[Usage Guide](USAGE_GUIDE.md)** - Comprehensive usage patterns

### Technical Documentation

- **[Browser Improvements](docs/BROWSER_IMPROVEMENTS.md)** - Browser automation details
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Documentation Index](DOCUMENTATION_INDEX.md)** - Complete doc navigation

## 🎮 Usage Modes

### Custom Web UI (Primary)

```bash
python start_custom_ui.py
```

Features:
- ✅ HTML artifacts in side panel
- ✅ MermaidJS diagrams inline  
- ✅ Python code execution
- ✅ Real-time chat
- ✅ Text-to-speech

### CLI Interactive (Alternative)

```bash
python -m src.agent.cli
```

Features:
- ✅ CLI interface
- ✅ Session persistence
- ✅ Tool execution
- ❌ No artifacts
- ❌ No visual content

## 🔑 Configuration

Edit `.env`:

```bash
# Required
OPENAI_API_KEY=your-openrouter-key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
MODEL=anthropic/claude-sonnet-4.5

# Optional TTS
KOKORO_TTS_URL=http://localhost:8880
KOKORO_TTS_VOICE=af_sky
```

## 🧪 Testing

```bash
# Test browser
python test_browser.py

# Test crawl
python test_crawl4ai_improved.py

# Test time utils
python test_time.py
```

## 📖 Learn More

1. **[README.md](README.md)** - Project overview, features, quick start
2. **[.clinerules](.clinerules)** - **CRITICAL**: Auto-loaded operational knowledge  
3. **[CUSTOM_UI_GUIDE.md](CUSTOM_UI_GUIDE.md)** - Detailed UI documentation
4. **[docs/CRAWL4AI_GUIDE.md](docs/CRAWL4AI_GUIDE.md)** - Web crawling guide

## 🤝 Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Crawl4AI for excellent web scraping
- Playwright for browser automation
- FastAPI for the web framework
- Kokoro TTS for voice synthesis
