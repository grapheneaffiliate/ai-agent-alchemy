# Typing Toolchain Decision: mypy

## Decision Summary

**Selected Toolchain**: mypy
**Rationale**: Already implemented and configured in the project
**Status**: Active (configured in pyproject.toml)

## Current State Analysis

### Existing mypy Configuration

```toml
[tool.mypy]
python_version = "3.11"
warn_unused_ignores = true
warn_return_any = true
warn_redundant_casts = true
mypy_path = ["src"]
namespace_packages = true
explicit_package_bases = true
exclude = ["^src/plugins"]

[[tool.mypy.overrides]]
module = "src.agent.*"
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true

[[tool.mypy.overrides]]
module = "src.plugins.*"
ignore_missing_imports = true
```

### Evidence of Active Usage
- ✅ `py.typed` file present in `src/agent/`
- ✅ Type stub files (`.pyi`) exist for all plugins
- ✅ Strict typing enforced for agent modules
- ✅ Plugin modules excluded from strict checking (appropriate for external code)

## Decision Rationale

### Why mypy (vs pyright)
1. **Already Integrated**: Project already uses mypy with established configuration
2. **Maturity**: mypy is the reference implementation for Python type checking
3. **Community Adoption**: Widely used in Python ecosystem
4. **IDE Support**: Excellent support across major Python IDEs
5. **CI/CD Integration**: Well-established patterns for CI integration

### Why Not pyright
1. **Switching Cost**: Unnecessary migration from working solution
2. **Configuration Overhead**: Would require duplicate configuration
3. **Team Familiarity**: Team already knows mypy patterns and practices

## Enhancement Plan

### Immediate (Week 1-2)
- [ ] **CI Integration**: Add mypy to GitHub Actions with failure on new untyped defs
- [ ] **Plugin Typing**: Create typing stubs for all plugin entry points
- [ ] **Gradual Strictness**: Increase plugin module strictness over time

### Short-term (Week 3-4)
- [ ] **Type Coverage Metrics**: Track typing coverage percentage
- [ ] **Contributor Guide**: Document typing expectations and patterns
- [ ] **Pre-commit Hooks**: Add mypy to pre-commit checks

### Medium-term (Week 5-8)
- [ ] **Complete Coverage**: Achieve 100% type coverage for agent modules
- [ ] **Plugin Interface Typing**: Strongly type plugin interfaces
- [ ] **Performance Optimization**: Optimize mypy run times

## Implementation Strategy

### 1. CI/CD Integration

**GitHub Actions Enhancement:**
```yaml
- name: Type check with mypy
  run: |
    python -m mypy src/agent/
    python -m mypy src/plugins/ --ignore-missing-imports

- name: Check for new untyped definitions
  run: |
    python -m mypy src/agent/ --disallow-untyped-defs
```

### 2. Plugin Typing Stubs

**Current Pattern:**
```python
# src/plugins/example.pyi
from typing import Any, Dict
from agent.models import MCPTool

def register_tools() -> list[MCPTool]: ...
async def tool_handler(args: Dict[str, Any]) -> str: ...
```

**Target Pattern:**
```python
# Enhanced with better typing
from typing import Any, Dict, List, Optional
from agent.models import MCPTool
from agent.errors import PluginExecutionError

def register_tools() -> List[MCPTool]: ...
async def tool_handler(
    args: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> str: ...
```

### 3. Contributor Guidelines

**Documentation**: `docs/CONTRIBUTING_TYPING.md`
- Type annotation standards
- mypy configuration explanations
- Common typing patterns
- Migration guide for existing code

## Success Metrics

### Typing Coverage
- **Agent Modules**: 100% type coverage
- **Plugin Interfaces**: 90% type coverage
- **Test Files**: 80% type coverage

### Quality Metrics
- **Zero mypy errors** in CI for agent modules
- **Reduced type: ignore** comments over time
- **Improved IDE support** and autocomplete

### Performance Metrics
- **CI runtime**: <30 seconds for mypy checks
- **Local development**: <5 seconds for incremental checks
- **Memory usage**: Stable during type checking

## Migration Path

### Phase 1: Foundation (Current)
- ✅ mypy configured and running
- ✅ `py.typed` marker file present
- ✅ Plugin stubs exist

### Phase 2: Enforcement (Week 1-2)
- [ ] CI failure on new untyped definitions
- [ ] Pre-commit hooks integration
- [ ] Documentation updates

### Phase 3: Enhancement (Week 3-4)
- [ ] Improve plugin interface typing
- [ ] Add type coverage reporting
- [ ] Performance optimization

## Risk Mitigation

### Backward Compatibility
- Plugin modules remain with `ignore_missing_imports`
- Gradual rollout of stricter settings
- Clear deprecation path for old patterns

### Performance Considerations
- Use mypy's incremental checking
- Cache compilation results
- Parallel execution where possible

### Team Adoption
- Clear documentation and examples
- Gradual onboarding process
- Pair programming for complex typing scenarios
