# Agent Service Decomposition Plan

## Goals
Break up `src/agent/core.py` and `src/agent/server.py` into cohesive service modules so that:
- Each module stays under 200 lines of source (target <150 SLOC).
- Responsibilities are explicit (session, instructions, tool dispatch, HTTP surface).
- Unit tests can target services directly without creating full `Agent` or HTTP stacks.

## Proposed Structure
```
src/agent/
  services/
    instructions.py     # .clinerules loading and validation
    session_manager.py  # Session creation, persistence, memory bridging
    tool_dispatch.py    # Async tool execution + PluginExecutor integration
    tool_parsing.py     # Response parsing, arg extraction, context builders
    react_runner.py     # Async generators powering CLI & API flows
    http/
      dependencies.py   # Shared FastAPI dependencies/builders
      streaming.py      # Streaming response helpers
      artifacts.py      # Artifact routing utilities
```

`core.Agent` becomes a thin coordinator that wires these services together. `server.py` switches to importing from `agent.services.http.*` rather than embedding large helper functions.

## Incremental Refactor Steps
1. **Extract Instructions + Tool Parsing (Today)**
   - Move `_load_custom_instructions`, `_build_tool_context`, `parse_tool_call_from_response`, `parse_args_from_input` into dedicated modules.
   - Update `Agent` to depend on `CustomInstructionLoader`, `ToolContextBuilder`, and `ToolCallParser` classes.

2. **Introduce `ToolDispatcher` (Today)**
   - Wrap `PluginExecutor` usage in `ToolDispatcher.execute_many`/`execute_single`.
   - Ensure dispatcher emits session history entries via callbacks so responsibilities stay separated.

3. **Session Manager (Today)**
   - Extract session creation/persistence into `SessionManager`, leaving `Agent` responsible for orchestration only.

4. **FastAPI helpers (Today)**
   - Extract `execute_tools_if_needed`, streaming helpers, and request/response builders from `server.py` into `agent.services.http` package.
   - Ensure server module only wires routes.

5. **Follow-up (Next PR)**
   - Split remaining large FastAPI models into `schemas.py`.
   - Move CLI wrapper `run_sync` into `agent.services.cli` to reuse for smoky tests.

## Immediate Validation
- Update unit tests to target new services where practical.
- Add smoke tests in `tests/smoke/` that call the decomposed components through the public API to validate wiring.
- Ensure import graph shrinks (tracked in `docs/reports/repo_baseline.md`).

## Ownership
- Core Agent services: `@grapheneaffiliate`
- HTTP services: `@grapheneaffiliate`

## Metrics
- Track LOC per service (script in `scripts/reporting/generate_repo_baseline.py`).
- Run `pytest tests/smoke -q` in CI on every PR to ensure wiring integrity.
