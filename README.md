# MCP AI Agent

Autonomous MCP-enabled assistant that combines LEANN self-analysis, browser/crawl automation, and news aggregation. The project now ships with a streamlined repository layout, structured logging, and CI-friendly test suites.

## Overview
- **Core modules**: `src/agent/*` (agent orchestration, CLI, API, REPL loop)
- **Plugins**: `src/plugins/*` (browser, Crawl4AI, news, search, LEANN, time, TTS)
- **Manual scripts & utilities**: `scripts/maintenance/`, `scripts/manual/`, `scripts/debug/`
- **Automated tests**: `tests/unit`, `tests/integration`, `tests/contract`
- **Archived docs**: `docs/archive/` (legacy verification reports and guides)

## Quick Start
```powershell
# clone & install
git clone https://github.com/yourusername/mcp-ai-agent
cd mcp-ai-agent
pip install -r requirements.txt

# environment
Copy-Item .env.example .env
# edit .env to add OPENAI / OpenRouter credentials
```

### Run the agent
```powershell
# HTTP API / Web UI (FastAPI + WebSocket)
python -m uvicorn src.agent.server:app --host 0.0.0.0 --port 9000

# Custom UI helper (opens websocket/chat UI, HTML artifacts panel)
python scripts/manual/start_custom_ui.py

# CLI interface
python -m src.agent.cli run
```

### CLI tool management
```powershell
python -m src.agent.cli add-tool `
  --name "my-tool" `
  --server "browser" `
  --tool-name "navigate" `
  --args-schema "{\"url\": {\"type\": \"string\"}}"
```
Quotes are automatically stripped; `--args-schema` must decode to a JSON object. Errors surface as exit code 0 with a descriptive message so contract tests remain stable.

## Test Suites
| Suite | Command | Purpose |
|-------|---------|---------|
| Unit | `python -m pytest tests/unit -q` | 69 tests covering plugins, REPL helpers, LEANN utilities. |
| Integration | `python -m pytest tests/integration -q` | 6 workflow tests (news, browser, API). |
| Contract | `python -m pytest tests/contract -q` | Typer CLI contract checks (run / add-tool). |

Manual/legacy scripts previously living under `tests/` are now parked in `scripts/manual/`. They can be run directly when needed, but they are not part of the automated suites.

## Structured Logging & Compatibility
- `src/agent/react_loop.py`, `src/plugins/browser.py`, and `src/plugins/enhanced_news_components.py` emit structured log entries for tool spans.
- `TimeUtils` remains import-compatible (`src/plugins/time_utils.py` re-exports the legacy class name).
- Enhanced news orchestration lives in `src/plugins/enhanced_news.py`; heavy logic is in `src/plugins/enhanced_news_components.py`.

## Repository Layout
```
src/
  agent/               # core runtime, CLI, API, REPL loop
  plugins/             # browser, crawl4ai, news, search, leann, time, tts
scripts/
  manual/              # manual UI starters & legacy async tests
  maintenance/         # verification + cache/reset scripts
  debug/               # troubleshooting helpers
analysis/overrides/     # JSON overrides shared with maintenance scripts
tests/
  unit/                # pytest unit suite
  integration/         # pytest integration suite
  contract/            # CLI contract suite
```

## Documentation
- `docs/archive/` hosts historical reports (production readiness, LEANN success, etc.).
- Active guides: `docs/CRAWL4AI_GUIDE.md`, `docs/ARTIFACTS_GUIDE.md`, `CUSTOM_UI_GUIDE.md`, `docs/TROUBLESHOOTING.md`.
- `CHANGELOG.md` tracks refactors and testing milestones; update it when behaviour or layout changes.

## Windows PowerShell Notes
- Use `Get-Content`, `Select-String`, `Select-Object` instead of Unix commands.
- Prefix local scripts with `.\` when running directly, e.g. `.\restart_server.bat`.
- All examples above assume PowerShell.

## Contributing
Pull requests are welcome. Please:
1. Run the three automated pytest suites.
2. Update `CHANGELOG.md` when behaviour or layout shifts.
3. Keep documentation in sync with CLI/test changes.

MIT License – see `LICENSE` for details.
