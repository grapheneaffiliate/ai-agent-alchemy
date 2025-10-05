# MCP AI Agent

A sophisticated AI agent system built on the Model Context Protocol (MCP) with advanced plugin architecture, web UI capabilities, and comprehensive tooling for autonomous task execution.

## Features

- **MCP Integration**: Full Model Context Protocol support with 28+ integrated tools
- **Plugin Architecture**: Extensible plugin system for custom functionality
- **Web UI**: Custom web interface with real-time chat, artifact display, and code execution
- **LEANN Integration**: Advanced semantic search and RAG capabilities
- **Multi-modal Support**: Text, code, and structured data processing
- **Comprehensive Testing**: 78.4% test coverage with async and sync test suites

## Project Structure

```
mcp-ai-agent/
├── src/                    # Core agent implementation
│   ├── agent/             # Core agent modules
│   └── plugins/           # Plugin implementations
├── tests/                 # Test suites (unit, integration, contract)
├── docs/                  # Documentation and guides
├── scripts/               # Utility and automation scripts
└── config/                # Configuration files
```

## Quick Start

1. **Installation**
   ```bash
   pip install -e .
   ```

2. **Start the Web UI**
   ```bash
   python scripts/manual/start_custom_ui.py
   ```

3. **Access the interface**
   Open http://localhost:9000 in your browser

## Key Components

### Core Agent (`src/agent/`)
- **Server**: FastAPI-based web server with WebSocket support
- **Plugin Executor**: Dynamic plugin loading and execution
- **Memory System**: Session and artifact management
- **React Loop**: Autonomous task planning and execution

### Plugins (`src/plugins/`)
- **LEANN**: Semantic search and intelligence analysis
- **Browser**: Web automation and scraping
- **News**: Real-time news fetching and processing
- **TTS**: Text-to-speech integration
- **Search**: Enhanced search capabilities

### Testing Framework
- **Unit Tests**: Individual component testing
- **Integration Tests**: Cross-component interaction testing
- **Contract Tests**: API and behavior contract validation

## Configuration

The agent uses several configuration files:
- `pyproject.toml`: Python project configuration and dependencies
- `config/mcp_tools.json`: MCP tool definitions
- `.env`: Environment variables and secrets

## Development

### Setup Tooling
```bash
pip install -e .[dev]
```
Includes async test support, Ruff linting, and MyPy type checks.

Run tooling locally:
```bash
ruff check .
mypy src
```

### Running Tests
```bash
pytest tests/ -v
```

### Code Quality
- **Lines of Code**: 8,748 across 172 files
- **Complexity Score**: 97.1/100 (Excellent)
- **Documentation**: 32 documentation files with comprehensive coverage

### Key Metrics
- **Total Files**: 172
- **Python Files**: 74
- **Test Files**: 58
- **Documentation Files**: 32
- **Test Coverage**: 78.4%

## Architecture

The system follows a modular architecture with:
- **Plugin-based extensibility**
- **Event-driven communication**
- **Async-first design patterns**
- **Comprehensive error handling**

## Contributing

1. Follow the development guidelines in `docs/`
2. Ensure test coverage for new features
3. Update documentation as needed
4. Use the established plugin architecture for extensions

## License

See LICENSE file for details.
