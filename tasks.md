# Tasks: Modular CLI AI Agent

**Input**: Design documents from spec.md and plan.md
**Prerequisites**: plan.md, spec.md

## Phase 3.1: Setup
- [ ] T001 Create project structure: mkdir -p src/agent src/plugins config memory tests/unit tests/integration tests/cli
- [ ] T002 [P] Initialize pyproject.toml with dependencies: typer, openai, pydantic, pytest, asyncio
- [ ] T003 [P] Create README.md with quickstart: pip install -e .; python -m agent run
- [ ] T004 Create config/mcp_tools.json skeleton: empty list [] for tool defs

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T005 [P] Contract test for 'run' command in tests/contract/test_cli_run.py (asserts interactive mode starts)
- [ ] T006 [P] Contract test for 'add-tool' command in tests/contract/test_cli_add_tool.py (asserts config update)
- [ ] T007 [P] Integration test session start loads env in tests/integration/test_session_start.py
- [ ] T008 [P] Integration test tool execution calls MCP in tests/integration/test_tool_execution.py (mock use_mcp_tool)
- [ ] T009 [P] Integration test memory persistence saves/loads in tests/integration/test_memory.py (mock JSON file)

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T010 [P] Pydantic models (Session, MCPTool, MemoryStore) in src/agent/models.py
- [ ] T011 [P] OpenAI API client with env base_url/model in src/agent/api.py
- [ ] T012 [P] Dynamic MCP loader from JSON config in src/agent/mcp_loader.py (parse and prepare calls)
- [ ] T013 [P] JSON memory store with lock for concurrency in src/agent/memory.py
- [ ] T014 Main agent core loop (reasoning, tool decision, execution) in src/agent/core.py
- [ ] T015 Typer CLI entrypoint with 'run', 'add-tool' cmds in src/agent/cli.py
- [ ] T016 Input validation and error handling in core.py (API failures, invalid tools)
- [ ] T017 Async handling for concurrent tool calls in core.py

## Phase 3.4: Integration
- [ ] T018 Load .env vars for API key/base/model in api.py and integrate with core
- [ ] T019 Config parsing and tool registration in mcp_loader.py with core
- [ ] T020 Session management with memory integration in core.py
- [ ] T021 User consent prompts for tool execution in cli.py

## Phase 3.5: Polish
- [ ] T022 [P] Unit tests for models validation in tests/unit/test_models.py
- [ ] T023 [P] Unit tests for memory locking in tests/unit/test_memory.py
- [ ] T024 [P] Unit tests for MCP loader parsing in tests/unit/test_mcp_loader.py
- [ ] T025 Performance test for latency <2s in tests/performance/test_latency.py
- [ ] T026 [P] Update quickstart.md with full usage examples
- [ ] T027 [P] Add error fallbacks and logging in core.py
- [ ] T028 Run full integration tests and ensure all pass
- [ ] T029 Manual testing: Run 'python -m agent run' and simulate tool memory

## Dependencies
- Tests (T005-T009) before implementation (T010-T021)
- T010 (models) blocks T014 (core), T020 (session)
- T011 (api) blocks T014
- T012 (loader) blocks T014
- T013 (memory) blocks T020
- T015 (cli) blocks T021
- Impl before polish (T022-T029)

## Parallel Example
```
# Launch T002-T004 together (setup independents):
Task: "Initialize pyproject.toml with dependencies"
Task: "Create README.md with quickstart"
Task: "Create config/mcp_tools.json skeleton"

# Launch T005-T009 together (tests parallel):
Task: "Contract test for 'run' in tests/contract/test_cli_run.py"
Task: "Contract test for 'add-tool' in tests/contract/test_cli_add_tool.py"
Task: "Integration test session start in tests/integration/test_session_start.py"
Task: "Integration test tool execution in tests/integration/test_tool_execution.py"
Task: "Integration test memory in tests/integration/test_memory.py"

# Launch T010-T013 together (core modules independent):
Task: "Pydantic models in src/agent/models.py"
Task: "OpenAI API client in src/agent/api.py"
Task: "Dynamic MCP loader in src/agent/mcp_loader.py"
Task: "JSON memory store in src/agent/memory.py"
```

## Notes
- [P] tasks for different files/no deps
- Verify tests fail before impl (TDD)
- Commit per task/group
- Avoid vague tasks; specify files
- Modular: Plugins dir for future extensions

## Task Generation Rules
1. **From Contracts**: CLI cmd tests [P], impl tasks
2. **From Data Model**: Model creation [P], integration
3. **From User Stories**: Session/tool/memory integration tests
4. **Ordering**: Setup → Tests → Core → Integration → Polish

## Validation Checklist
- [x] All contracts have corresponding tests
- [x] All entities have model tasks
- [x] All tests before implementation
- [x] Parallel tasks independent
- [x] Each task specifies file path
- [x] No same-file conflicts for [P]
