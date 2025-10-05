# MCP AI Agent

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

**MCP AI Agent** is an intelligent AI assistant built on the Model Context Protocol (MCP) that demonstrates autonomous tool use through a ReAct loop architecture. The agent can autonomously assess and improve its own codebase while providing both CLI and Web UI interfaces.

## Quick Start

### Installation
```bash
# Install dependencies
pip install -e ".dev]"  # Includes development dependencies

# Verify installation
python -c "from src.agent.cli import cli_app; print('CLI imports work!')"
```

### Basic Usage
```bash
# Start web UI
python scripts/manual/start_custom_ui.py

# Test CLI import
python -c "from src.agent.cli import cli_app; print('SUCCESS!')"

# Test API functionality
python -c "from src.agent.api import AgentAPI; print('API ready!')""
```

## Architecture

The agent is organized into key components:

- **Agent Core**: Main orchestration logic
- **Plugin System**: 9 MCP-based plugins (crawling, news, search, etc.)
- **ReAct Loop**: Autonomous reasoning and tool execution
- **Web UI**: Real-time chat with HTML artifact generation
- **CLI Interface**: Command-line session management
- **Self-Analysis**: Can assess its own codebase quality

## Plugins

Available MCP plugins include:
- **Browser**: Web automation and scraping
- **Crawl4AI**: AI-powered web crawling
- **Leann**: Semantic search and RAG
- **Enhanced News**: Dynamic news aggregation
- **Analysis**: Data analysis and visualization
- **Search**: Enhanced search capabilities

## Key Features Resolved

This v1.5 release resolves critical architectural issues:

✅ **Circular Import Fix**: Eliminated complex import cycles between agent modules  
✅ **Async Testing**: Fixed pytest-asyncio event loop conflicts  
✅ **Web UI Stability**: Restored full WebSocket functionality  
✅ **CLI Operations**: All import paths working correctly  

The agent is now fully functional with 28 MCP tools loaded and demonstrates autonomous codebase analysis capabilities.

## Test Results

v1.5 successfully loads 28 MCP tools with full Web UI and CLI functionality verified through extensive testing:

```bash
✅ Web UI: Server starts, WebSocket connections work
✅ MCP Tools: 28 tools loaded successfully (browser, crawling, news, search, etc.)
✅ ReAct Loop: Autonomous reasoning and tool execution functional
✅ CLI: Import system stable, no circular dependencies
✅ Self-Analysis: Can assess and improve its own codebase quality
```

## Changelog

### v1.5 - Critical Import Fixes & Enhanced Stability
**Release Date:** October 5, 2025

- 🐛 **FIXED**: Critical circular import dependencies between agent modules
- 🧪 **FIXED**: Asyncio event loop conflicts in pytest tests
- 🌐 **FIXED**: Web UI WebSocket functionality restored
- 📦 **MIGRATED**: AgentAPI class consolidated into api/__init__.py
- 📝 **ENHANCED**: Comprehensive architecture with ReAct loop, MCP plugins, and self-analysis
- 📊 **VERIFIED**: 28 MCP tools loaded successfully with full functionality

## Contributing

This project demonstrates self-improving AI agents. The agent can assess its own codebase quality through its MCP plugins and provide improvement suggestions.

For technical details, see the extensive documentation in the `docs/` directory.

## License

MIT License
