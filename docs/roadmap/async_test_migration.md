# Async Test Migration Plan

## Objective
Transition the slowest I/O-bound test suites to `pytest` async patterns so they execute on the event loop used by the agent runtime. The goal is to finish the first wave within one week and establish a repeatable pattern for the remaining suites.

## Target Scope (Wave 1)
- `tests/integration/test_session_start.py`
- `tests/integration/test_memory.py`
- `tests/integration/test_tool_execution.py`
- `tests/integration/test_news_integration.py`
- `tests/integration/test_browser_integration.py`
- `tests/contract/test_cli_run.py`
- `tests/contract/test_cli_add_tool.py`

These suites exercise disk and network abstractions, making them the highest-value move to asyncio.

## Delivery Steps
1. **Harness Enablement (Day 1)**
   - Introduce `pytest-asyncio` as a dev dependency.
   - Add `pytest.ini` config to set the default asyncio mode to `strict`.
   - Provide an `AsyncTestHelper` in `tests/helpers/async_tools.py` that wraps event-loop setup and common agent fixtures.

2. **Suite Migration (Days 2-4)**
   - Refactor test fixtures in the targeted modules to use `async_fixture` and `await` the agent APIs directly.
   - Replace synchronous CLI invocations with `typer.testing.CliRunner().invoke` run inside the loop via `anyio.from_thread.run` or direct async CLI hooks.
   - Extract shared mocks for `PluginExecutor` and `ArtifactGenerator` into `tests/helpers` to avoid duplicated patching logic.

3. **Stability & Parallelism (Days 4-5)**
   - Enable `pytest -n auto --dist loadscope` once async friendly to cut runtime.
   - Add health checks ensuring each migrated suite can run both with and without network access (mocking news/browser calls by default).

4. **Roll-forward Checklist (Day 6+)**
   - Document the conversion checklist in `docs/roadmap/async_test_migration.md` (this file).
   - Require that new integration/contract suites are async-first and call the shared helpers.
   - Track migration progress in `docs/roadmap/test_migration_tracker.md` (to be created) with a table of suites and status.

## Success Criteria
- All listed suites run with `pytest --asyncio-mode=strict` and rely on `await` for agent interactions.
- Runtime for the integration suite drops by =30% on CI (baseline to be captured before merge).
- No direct `asyncio.run` usage in migrated tests; everything awaits the shared event loop fixture.
- Smoke suite (see `tests/smoke/`) remains synchronous to guard CLI entrypoints.

## Dependencies & Risks
- Requires coordination with plugin owners to ensure fake implementations exist for browser/news plugins.
- Fixture refactors must keep backwards compatibility with manual scripts in `scripts/manual/*`.
- Asyncifying tests that shell out to CLI demands careful isolation of environment variables; ensure `.env` loading happens once per session fixture.
