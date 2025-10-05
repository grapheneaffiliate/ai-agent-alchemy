# Async Migration Guide

## Overview

This document outlines the systematic migration of the MCP AI Agent codebase to async-first patterns, targeting ≥90% async adoption across eligible functions.

## Current State Analysis

### Already Async-Enabled Components
- `src/agent/core.py` - Main agent orchestration with async methods
- `src/agent/server.py` - FastAPI server with async endpoints
- `src/agent/plugin_executor.py` - Plugin execution framework
- `src/agent/api.py` - API integration layer

### Migration Targets

#### Immediate (0-1 week)
- **CLI Module (`src/agent/cli.py`)**: Convert sync entry points to async
- **Plugin Entry Points**: Ensure all plugin tool handlers are async
- **Test Suites**: Convert sync tests to async patterns

#### Short-term (1-2 weeks)
- **Service Layer**: Migrate remaining sync services to async
- **Utility Functions**: Convert file I/O and network operations
- **Error Handling**: Async-compatible error propagation

## Migration Strategy

### 1. Test Migration Framework

**Target Files:**
- `tests/contract/test_cli_run.py`
- `tests/integration/test_tool_execution.py`
- `tests/unit/test_*.py` (all sync test files)

**Approach:**
```python
# Before
def test_sync_function():
    result = sync_function()
    assert result == expected

# After
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

### 2. CLI Module Migration

**Current Pattern:**
```python
def run_sync(self) -> None:
    async def _run() -> None:
        async for message in self.run():
            print(message)
    asyncio.run(_run())
```

**Target Pattern:**
```python
async def run_async(self) -> AsyncGenerator[str, None]:
    # Direct async iteration
    async for message in self.run():
        yield message
```

### 3. Plugin Interface Standardization

**Current Mixed Pattern:**
```python
# Some plugins use sync handlers
def sync_tool_handler(args: Dict) -> str:
    return result

# Some use async handlers
async def async_tool_handler(args: Dict) -> str:
    return await result
```

**Target Pattern:**
```python
# All plugins use async handlers
async def tool_handler(args: Dict[str, Any]) -> str:
    # Async operations only
    result = await async_operation()
    return result
```

## Timeline and Milestones

### Week 1: Foundation
- [ ] Migrate CLI module to async-first
- [ ] Convert 50% of sync tests to async
- [ ] Establish async plugin interface contract
- [ ] Document async patterns and conventions

### Week 2: Core Migration
- [ ] Complete test suite migration (100%)
- [ ] Migrate all plugin entry points to async
- [ ] Update service layer dependencies
- [ ] Performance benchmarking and optimization

### Week 3-4: Edge Cases
- [ ] Handle sync library integrations
- [ ] Migrate file I/O operations
- [ ] Update error handling for async context
- [ ] Comprehensive testing and validation

## Success Metrics

- **Coverage**: ≥90% of eligible functions use async
- **Performance**: No regression in response times
- **Reliability**: Zero async-related test failures
- **Maintainability**: Clear async patterns and conventions

## Risk Mitigation

### Backward Compatibility
- Maintain sync wrappers for external integrations
- Use async compatibility layers where needed
- Gradual rollout with feature flags

### Testing Strategy
- Run both sync and async test suites during migration
- Performance benchmarking at each milestone
- Integration testing with real plugin ecosystem

## Resources

- [Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [FastAPI Async Guide](https://fastapi.tiangolo.com/async/)
- [Pytest Asyncio](https://pytest-asyncio.readthedocs.io/)
