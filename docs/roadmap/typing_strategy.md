# Typing Enforcement Strategy

## Tooling Decision
- **Type checker:** `mypy` (already present in `pyproject.toml` dev extras).
- **Scope:** Initial enforcement covers `src/agent/services`, `src/agent/core.py`, and `src/agent/server.py`. These modules host public orchestration APIs.
- **Configuration:** See `[tool.mypy]` in `pyproject.toml` – enforces `disallow_untyped_defs` and `check_untyped_defs` on `src.agent.*` modules while ignoring the dynamically loaded plugin surface (`src.plugins.*`). Namespace packages run via `explicit_package_bases` with `mypy_path = ["src"]`.

## CI Gate
- Workflow: `.github/workflows/typecheck.yml` runs `mypy src/agent/services src/agent/core.py src/agent/server.py --ignore-missing-imports` on every push/PR.
- Failure of the type check blocks merges, ensuring new public methods stay typed.

## Stubs & Typed Packages
- Added protocol-style stubs (`*.pyi`) for plugin entry points (`time_utils`, `browser`, `news_fetch`, `crawl4ai_plugin`, `search`, `enhanced_news`, `leann_plugin`, `analysis`) providing structural types consumed by the executor.
- Marked `src/agent` as typed via `py.typed`; introduced `__init__.py` for `agent` and `plugins` packages to give mypy concrete package roots.

## Rollout Plan
1. **Phase 1 (current):** Enforce on services/core/server modules and backfill annotations for newly extracted services.
2. **Phase 2:** Expand coverage to `src/agent/api.py`, `plugin_executor.py`, and `web_ui.py` once their dependencies gain annotations.
3. **Phase 3:** Require plugin authors to provide `.pyi` stubs or inline annotations before registering new tools (documented in contributor checklist).

## Developer Guidance
- Run `python -m mypy src/agent/services src/agent/core.py src/agent/server.py --ignore-missing-imports` locally before commits touching orchestrator code.
- Prefer returning concrete dictionaries or dataclasses from plugins to keep executor signatures precise.
- Add new stubs in `src/plugins/*.pyi` when introducing plugin entry points.
