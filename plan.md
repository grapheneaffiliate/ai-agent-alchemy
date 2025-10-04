---
description: "Implementation plan for modular CLI AI agent with MCP integration"
scripts:
  ps: ../ai-agent-spec-kit/scripts/powershell/update-agent-context.ps1 -AgentType claude
---

# Implementation Plan: Modular CLI AI Agent

**Branch**: `001-modular-ai-agent` | **Date**: 2025-09-30 | **Spec**: spec.md

## Summary
Primary requirement: Terminal-based AI agent with interactive sessions, AI reasoning via API, dynamic MCP tool execution from config, and local memory persistence. Technical approach: Python CLI using Typer for UI, OpenAI SDK for model calls, JSON config for MCP tools, file-based memory store for modularity and simplicity.

## Technical Context
**Language/Version**: Python 3.11+  
**Primary Dependencies**: typer (CLI), openai (API), pydantic (configs), asyncio (async ops)  
**Storage**: Local JSON files for memory (session/state)  
**Testing**: pytest for unit/integration  
**Target Platform**: Cross-platform terminal (Windows/Linux/macOS)  
**Project Type**: Single CLI application  
**Performance Goals**: <2s response latency, handle 100+ tool calls/session  
**Constraints**: Offline memory read/write, no external DB, API rate limits respected  
**Scale/Scope**: Single-user tool, 10-20 MCP tools max, extensible via config/plugins

## Constitution Check
*Based on memory/constitution.md - All principles satisfied: Simple (core loop + configs), Modular (plugins for loaders/backends), Reliable (error handling, fallbacks), Ethical (no secrets in memory, user consent for tools). No violations.

**Initial Constitution Check: PASS**

## Project Structure

### Documentation (this feature)
```
specs/001-modular-ai-agent/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1 (CLI cmd contracts)
└── tasks.md             # Phase 2
```

### Source Code (repository root)
```
mcp-ai-agent/
├── src/
│   ├── agent/
│       ├── cli.py          # Typer app entrypoint
│       ├── core.py         # Main agent loop (reason, tool call, memory)
│       ├── api.py          # OpenAI client with Grok model
│       ├── mcp_loader.py   # Dynamic tool loading from config
│       └── memory.py       # JSON-based state persistence
│   └── plugins/            # Modular extensions (e.g., custom loaders)
├── config/
│   └── mcp_tools.json      # MCP tool definitions
├── memory/                 # Local JSON stores (sessions.json)
├── tests/
│   ├── unit/               # Core logic tests
│   ├── integration/        # API/MCP mocks
│   └── cli/                # End-to-end session tests
├── pyproject.toml          # Dependencies/setup
└── README.md               # Usage/quickstart
```

**Structure Decision**: Single project layout for CLI tool, with src/agent for core modules and plugins for extensibility.

## Phase 0: Outline & Research
1. **Extract unknowns**: Research OpenAI-compatible API usage for custom models (Grok via OpenRouter), MCP tool schema parsing for use_mcp_tool calls, best practices for async CLI tools, JSON memory patterns for agent state.
2. **Generate and dispatch research agents**:
   - Task: "Research OpenAI Python SDK for custom base URL and model integration"
   - Task: "Find patterns for dynamic tool loading in CLI apps using JSON configs"
   - Task: "Best practices for local memory in AI agents (conversation persistence)"
3. **Consolidate findings** in research.md: e.g., Use OpenAI client with base_url from env, validate MCP schemas with Pydantic, use threading locks for memory writes.

**Output**: research.md resolving all technical gaps.

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities**: Session (history list, current_task str, loaded_tools list), MCP Tool (name str, server str, tool_name str, args dict), Memory Store (sessions dict{str: Session}).
   - Validation: Tool args match MCP schema, sessions timestamped.
   - Output: data-model.md with Pydantic models.

2. **Generate API contracts**: CLI commands - 'run' (interactive session), 'add-tool' (config update), 'load-memory' (session resume).
   - Contracts as JSON schemas in /contracts/cmd_run.json etc. for validation.

3. **Generate contract tests**: One pytest file per command asserting input/output schemas.
   - Tests fail initially (no impl yet).

4. **Extract test scenarios**: From user stories - e.g., session start loads env, tool use calls MCP correctly.
   - Quickstart test: 'python -m agent run' launches interactive loop.

5. **Update agent file incrementally**: Run PowerShell script to add AI instructions for MCP integration and memory handling (keep under 150 lines).

**Output**: data-model.md, /contracts/*, failing tests in tests/, quickstart.md, updated AGENTS.md.

**Post-Design Constitution Check: PASS**

## Phase 2: Task Planning Approach
**Task Generation Strategy**:
- Base: tasks-template.md
- From contracts: Test creation tasks [P] (parallel for units)
- From data model: Model impl tasks [P]
- From user stories: Integration tests (session flow, tool execution, memory persistence)
- Impl tasks: Follow TDD to pass tests (core loop, loader, API calls)

**Ordering Strategy**:
- Tests first: unit tests [P1] before impl
- Dependencies: Models before loaders before CLI
- Mark [P] for independents (e.g., memory and tool loader parallel)

**Estimated Output**: 15-20 tasks in tasks.md

## Complexity Tracking
No violations; all choices align with simplicity/modularity. Simpler alternatives (no async) rejected for sophistication (concurrent tools).

## Progress Tracking
**Phase Status**:
- [x] Phase 0: Research complete (manual equivalent)
- [x] Phase 1: Design complete
- [x] Phase 2: Task planning complete (described)
- [ ] Phase 3: Tasks generated
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All unknowns resolved
- [x] Complexity documented

---
*Based on Constitution v2.1.1 - See ../ai-agent-spec-kit/memory/constitution.md*
