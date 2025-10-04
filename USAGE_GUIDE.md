# MCP AI Agent - Complete Usage Guide

## 📖 Table of Contents

- [Getting Started](#getting-started)
- [CLI Commands](#cli-commands)
- [Tool Reference](#tool-reference)
- [Usage Examples](#usage-examples)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)

## 🚀 Getting Started

### Starting the Agent

```bash
cd mcp-ai-agent
python -m src.agent.cli run
```

You'll see:
```
AI Agent started. Type 'exit' to quit.
Note: Tools require consent; confirm Y for each input.
Loaded 14 tools:
  - read-file (filesystem)
  - list-dir (filesystem)
  - search-code (search)
  - run-command (shell)
  - browse-url (browser)
  - browser-screenshot (browser)
  - browser-click (browser)
  - browser-fill (browser)
  - browser-extract (browser)
  - browser-get-links (browser)
  - get-time (time)
  - get-date (time)
  - get-day-info (time)
  - format-datetime (time)
You:
```

### Exiting the Agent

Type any of these to exit:
- `exit`
- `quit`

The agent will save your session and display: `Session saved. Goodbye!`

## 🛠️ CLI Commands

### Command 1: `run` - Start Interactive Session

**Purpose**: Launch an interactive AI agent session with all tools loaded.

**Usage**:
```bash
python -m src.agent.cli run
```

**What It Does**:
1. Loads all configured MCP tools
2. Initializes OpenRouter API connection
3. Loads previous session if available
4. Starts interactive chat interface
5. Automatically saves session after each interaction

**Options**: None (uses defaults from .env)

---

### Command 2: `add-tool` - Add New MCP Tool

**Purpose**: Add a new tool to the agent's configuration without editing JSON files.

**Syntax**:
```bash
python -m src.agent.cli add-tool <name> --server <server> --tool-name <tool> [--args-schema <json>]
```

**Parameters**:
- `name` (required): Friendly name for the tool (e.g., "read-file")
- `--server` (required): Server/category name (e.g., "filesystem", "browser", "time")
- `--tool-name` (required): Actual function name in the plugin (e.g., "read_file")
- `--args-schema` (optional): JSON schema for tool arguments

**Examples**:

```bash
# Add a simple tool without parameters
python -m src.agent.cli add-tool hello-world \
  --server greetings \
  --tool-name say_hello

# Add a tool with parameters
python -m src.agent.cli add-tool fetch-url \
  --server web \
  --tool-name http_get \
  --args-schema '{"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}'

# Add a file operation tool
python -m src.agent.cli add-tool write-file \
  --server filesystem \
  --tool-name write_file \
  --args-schema '{"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}'
```

**Result**: Tool is added to `config/mcp_tools.json` and will be available on next agent restart.

---

### Command 3: View Help

**View all commands**:
```bash
python -m src.agent.cli --help
```

**View command-specific help**:
```bash
python -m src.agent.cli run --help
python -m src.agent.cli add-tool --help
```

## 🔧 Tool Reference

### File Operation Tools

#### 1. read-file
**Purpose**: Read the contents of a file

**Usage in Chat**:
```
You: Read the file src/agent/cli.py
Agent: [Automatically uses read-file tool]
```

**Tool Format**:
```
USE TOOL: read-file
path: src/agent/cli.py
```

**Returns**: File contents as text

---

#### 2. list-dir
**Purpose**: List contents of a directory

**Usage in Chat**:
```
You: List files in the current directory
You: Show me what's in src/agent/
Agent: [Automatically uses list-dir tool]
```

**Tool Format**:
```
USE TOOL: list-dir
path: src/agent/
```

**Returns**: List of files and directories

---

### Code Search Tools

#### 3. search-code
**Purpose**: Search for code patterns using regex

**Usage in Chat**:
```
You: Search for 'def run' in Python files
You: Find all TODO comments in the codebase
Agent: [Automatically uses search-code tool]
```

**Tool Format**:
```
USE TOOL: search-code
query: def run
include_pattern: *.py
```

**Returns**: Matching lines with file paths

---

### Shell Tools

#### 4. run-command
**Purpose**: Execute shell commands

**Usage in Chat**:
```
You: Run 'ls -la' to see file permissions
You: Execute 'git status' to check repository state
Agent: [Automatically uses run-command tool]
```

**Tool Format**:
```
USE TOOL: run-command
command: ls -la
working_directory: .
```

**Returns**: Command output

---

### Browser Automation Tools

#### 5. browse-url
**Purpose**: Navigate to a website

**Usage in Chat**:
```
You: Visit https://example.com
You: Go to github.com
You: Look up atchimneys.com
Agent: [Automatically uses browse-url tool]
```

**Tool Format**:
```
USE TOOL: browse-url
url: https://example.com
```

**Returns**: 
```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "status": "success"
}
```

---

#### 6. browser-screenshot
**Purpose**: Capture a screenshot of the current page

**Usage in Chat**:
```
You: Take a screenshot and save it as homepage.png
You: Capture the current page
Agent: [Automatically uses browser-screenshot tool]
```

**Tool Format**:
```
USE TOOL: browser-screenshot
path: homepage.png
```

**Returns**:
```json
{
  "path": "homepage.png",
  "status": "saved"
}
```

---

#### 7. browser-click
**Purpose**: Click an element on the page

**Usage in Chat**:
```
You: Click the 'Login' button
You: Click the element with class 'submit-btn'
Agent: [Automatically uses browser-click tool]
```

**Tool Format**:
```
USE TOOL: browser-click
selector: .submit-btn
```

**Returns**:
```json
{
  "selector": ".submit-btn",
  "status": "clicked"
}
```

---

#### 8. browser-fill
**Purpose**: Fill a form field with text

**Usage in Chat**:
```
You: Fill the email field with test@example.com
You: Enter 'password123' in the password field
Agent: [Automatically uses browser-fill tool]
```

**Tool Format**:
```
USE TOOL: browser-fill
selector: #email
text: test@example.com
```

**Returns**:
```json
{
  "selector": "#email",
  "status": "filled"
}
```

---

#### 9. browser-extract
**Purpose**: Extract text from a page element

**Usage in Chat**:
```
You: Get the text from the main heading
You: Extract content from the body tag
Agent: [Automatically uses browser-extract tool]
```

**Tool Format**:
```
USE TOOL: browser-extract
selector: h1
```

**Returns**: Text content of the element

---

#### 10. browser-get-links
**Purpose**: Get all links from the current page

**Usage in Chat**:
```
You: Show me all links on this page
You: Get navigation links
Agent: [Automatically uses browser-get-links tool]
```

**Tool Format**:
```
USE TOOL: browser-get-links
```

**Returns**:
```json
[
  {"href": "https://example.com/about", "text": "About"},
  {"href": "https://example.com/contact", "text": "Contact"}
]
```

---

### Time & Date Tools (Eastern Time - Washington DC)

#### 11. get-time
**Purpose**: Get current time in Eastern timezone

**Usage in Chat**:
```
You: What time is it?
You: Tell me the current time
Agent: [Automatically uses get-time tool]
```

**Tool Format**:
```
USE TOOL: get-time
```

**Returns**:
```json
{
  "datetime": "2025-09-30T02:50:52.773034-04:00",
  "date": "2025-09-30",
  "time": "02:50:52",
  "time_12h": "02:50:52 AM",
  "day_of_week": "Tuesday",
  "timezone": "America/New_York",
  "timestamp": 1759215052
}
```

---

#### 12. get-date
**Purpose**: Get detailed date information

**Usage in Chat**:
```
You: What's today's date?
You: Tell me the current date
Agent: [Automatically uses get-date tool]
```

**Tool Format**:
```
USE TOOL: get-date
```

**Returns**:
```json
{
  "date": "2025-09-30",
  "day": 30,
  "month": 9,
  "year": 2025,
  "day_of_week": "Tuesday",
  "month_name": "September",
  "month_name_short": "Sep",
  "timezone": "America/New_York"
}
```

---

#### 13. get-day-info
**Purpose**: Get extended day information (week number, quarter, etc.)

**Usage in Chat**:
```
You: What week of the year is it?
You: Is today a weekend?
Agent: [Automatically uses get-day-info tool]
```

**Tool Format**:
```
USE TOOL: get-day-info
```

**Returns**:
```json
{
  "date": "2025-09-30",
  "day_of_week": "Tuesday",
  "day_of_month": 30,
  "day_of_year": 273,
  "week_number": 40,
  "is_weekend": false,
  "quarter": 3,
  "timezone": "America/New_York"
}
```

---

#### 14. format-datetime
**Purpose**: Format current datetime with custom format

**Usage in Chat**:
```
You: Format the current time as 'Monday, September 30, 2025 at 02:50 PM'
Agent: [Automatically uses format-datetime tool]
```

**Tool Format**:
```
USE TOOL: format-datetime
format_string: %A, %B %d, %Y at %I:%M %p
```

**Returns**: Formatted datetime string

**Common Format Codes**:
- `%Y`: Year (2025)
- `%m`: Month number (09)
- `%d`: Day (30)
- `%H`: Hour 24h (14)
- `%I`: Hour 12h (02)
- `%M`: Minute (50)
- `%S`: Second (30)
- `%p`: AM/PM
- `%A`: Full weekday (Monday)
- `%a`: Short weekday (Mon)
- `%B`: Full month (September)
- `%b`: Short month (Sep)

## 💡 Usage Examples

### Example 1: Time Queries

```
You: What time is it?
Agent: USE TOOL: get-time
Tool result: {
  "time_12h": "02:50:52 AM",
  "day_of_week": "Tuesday",
  "timezone": "America/New_York"
}
```

---

### Example 2: Website Research

```
You: Look up atchimneys.com
Agent: USE TOOL: browse-url
       url: https://atchimneys.com
Tool result: {
  "url": "https://atchimneysweeps.com/",
  "title": "A&T Chimney Sweeps NOVA",
  "status": "success"
}

You: Give me a summary
Agent: [Provides detailed summary of the website content]
```

---

### Example 3: Code Search

```
You: Search for 'def run' in Python files
Agent: USE TOOL: search-code
       query: def run
       include_pattern: *.py
Tool result: [List of matching files and lines]
```

---

### Example 4: File Operations

```
You: Read the contents of README.md
Agent: USE TOOL: read-file
       path: README.md
Tool result: [File contents]

You: List all files in src/agent/
Agent: USE TOOL: list-dir
       path: src/agent/
Tool result: [Directory listing]
```

---

### Example 5: Multi-Tool Workflow

```
You: Look up news on TechCrunch and show me the headlines
Agent: USE TOOL: browse-url
       url: https://techcrunch.com/

       USE TOOL: browser-get-links
       
Tool result 1: {
  "url": "https://techcrunch.com/",
  "title": "TechCrunch | Startup and Technology News",
  "status": "success"
}

Tool result 2: [
  {"href": "...", "text": "Apple Intelligence is now available..."},
  {"href": "...", "text": "xAI opens Grok-1.5V to researchers"},
  {"href": "...", "text": "Tesla Q3 deliveries..."}
]

Agent: [Provides formatted summary of headlines]
```

## 🎯 Advanced Features

### Natural Language Tool Usage

The agent automatically determines which tools to use based on your natural language queries:

**Time-related queries**:
- "What time is it?" → uses `get-time`
- "What's the date?" → uses `get-date`
- "Is today a weekend?" → uses `get-day-info`

**Web browsing queries**:
- "Visit example.com" → uses `browse-url`
- "Take a screenshot" → uses `browser-screenshot`
- "Click the login button" → uses `browser-click`

**File operations**:
- "Read config.json" → uses `read-file`
- "List files in src/" → uses `list-dir`

**Code search**:
- "Find all TODOs" → uses `search-code`
- "Search for function definitions" → uses `search-code`

### Session Memory

The agent remembers:
- Previous conversation history
- Tool execution results
- Context from earlier in the session

Example:
```
You: Look up atchimneys.com
Agent: [Visits site and returns info]

You: Give me a summary
Agent: [Provides summary based on previous tool result]
```

### Multi-Step Tasks

The agent can chain multiple tools together:

```
You: Research the latest AI news and save a screenshot
Agent: 
  1. USE TOOL: browse-url (visits news site)
  2. USE TOOL: browser-screenshot (captures page)
  3. Provides summary with screenshot path
```

## 📝 Best Practices

### 1. Be Specific with URLs

**Good**: `Look up https://example.com`
**Better**: `Visit https://example.com and extract the main heading`

### 2. Provide Context for File Operations

**Good**: `Read cli.py`
**Better**: `Read src/agent/cli.py`

### 3. Use Natural Language

The agent understands natural queries:
- ✅ "What time is it?" (natural)
- ✅ "Get current time" (direct)
- ✅ "Use get-time tool" (explicit)

### 4. Browser Tool Sequence

For browser operations, always:
1. Navigate first: `browse-url`
2. Then interact: `browser-click`, `browser-fill`, `browser-extract`, etc.

```
You: Go to example.com and click the About link
Agent: 
  1. browse-url → example.com
  2. browser-click → .about-link
```

### 5. CSS Selectors

When using browser tools, common selectors:
- **ID**: `#element-id`
- **Class**: `.class-name`
- **Tag**: `h1`, `body`, `a`
- **Attribute**: `[href="..."]`
- **Combination**: `div.header a.nav-link`

## 🔍 Tool Chaining Examples

### Example: Research Workflow

```
You: Research AI developments on TechCrunch, extract the top 3 headlines, and save a screenshot

Agent executes:
1. browse-url → https://techcrunch.com/
2. browser-get-links → extracts all links
3. browser-screenshot → saves page.png
4. Formats and presents top 3 headlines with screenshot path
```

### Example: Time-Stamped Report

```
You: Create a time-stamped report of the current system

Agent executes:
1. get-time → gets current time
2. get-date → gets current date
3. get-day-info → gets week/quarter info
4. list-dir → gets current directory listing
5. Compiles formatted report with timestamps
```

### Example: Web Form Automation

```
You: Fill out the contact form on example.com with name 'John Doe' and email 'john@example.com'

Agent executes:
1. browse-url → https://example.com
2. browser-fill → #name field with 'John Doe'
3. browser-fill → #email field with 'john@example.com'
4. browser-click → .submit-button
5. Confirms form submission
```

## 📊 Tool Categories Summary

| Category | Tools | Use Cases |
|----------|-------|-----------|
| **File Ops** | read-file, list-dir | Reading configs, exploring codebases |
| **Search** | search-code | Finding patterns, TODOs, function definitions |
| **Shell** | run-command | Git operations, system commands |
| **Browser** | 6 tools | Web research, testing, automation |
| **Time** | 4 tools | Timestamps, date info, formatting |

## 🎓 Learning Tips

### Start Simple
```
You: What time is it?
You: List files in this directory
You: Visit example.com
```

### Build Complexity
```
You: Find all Python files modified today
You: Research the latest news and provide a summary
You: Navigate to the site and extract the pricing information
```

### Combine Tools
```
You: Check the current time, then read config.json, then visit the API endpoint listed in it
```

## 🆘 Common Issues

### Tool Not Executing
- Check tool is listed in startup (14 tools should be shown)
- Verify tool name matches configuration
- Review debug output for parsing issues

### Browser Closed Error
- Browser state is maintained across calls
- If browser closes, agent will restart it automatically
- For new sessions, first call should be `browse-url`

### Time Zone Issues
- All times are in Eastern Time (America/New_York)
- Timestamps are Unix format (seconds since epoch)
- Use `format-datetime` for custom time zones if needed

## 📚 Additional Resources

- **README.md**: Installation and setup guide
- **.clinerules**: Custom agent instructions
- **config/mcp_tools.json**: Tool configuration reference
- **Test Scripts**: Examples in test_*.py files

---

**Need more help?** The agent is designed to be intuitive - just ask in natural language and it will use the appropriate tools!
