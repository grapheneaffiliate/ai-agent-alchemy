# Module Split Proposal: core.py and server.py Refactoring

## Current State Analysis

### core.py (247 lines)
**Current Responsibilities:**
- Agent class with high-level orchestration
- Tool execution coordination
- Session management integration
- Memory operations
- CLI interaction loop

**Issues:**
- Mixed concerns (orchestration + CLI + session management)
- Large class with multiple responsibilities
- Tightly coupled dependencies

### server.py (167 lines)
**Current Responsibilities:**
- FastAPI application setup
- OpenAI-compatible API endpoints
- CORS middleware configuration
- Request/response handling

**Issues:**
- Server logic mixed with business logic
- HTTP concerns embedded in core agent logic

## Proposed Architecture

### 1. Core Module Split (`src/agent/`)

#### `src/agent/orchestrator.py` (New)
**Responsibilities:**
- Agent class coordination
- Service wiring and dependency injection
- High-level execution flow
- Cross-cutting concerns

```python
class AgentOrchestrator:
    """Coordinates agent services and execution."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.services = self._initialize_services()

    async def execute_tools(self, tool_calls: List[ToolCall]) -> List[str]:
        """Execute tools via service layer."""
        return await self.services.tool_dispatcher.execute(tool_calls)
```

#### `src/agent/session/` (New Directory)
**Files:**
- `session_manager.py` - Session lifecycle management
- `session_state.py` - Session data structures
- `session_config.py` - Session configuration

#### `src/agent/services/` (Enhanced)
**Enhanced Services:**
- `execution_service.py` - Tool execution coordination
- `memory_service.py` - Memory operations
- `context_service.py` - Context building and management

### 2. Server Module Split (`src/agent/`)

#### `src/agent/api/` (New Directory)
**Files:**
- `server.py` - Pure FastAPI application setup
- `endpoints.py` - Route definitions
- `middleware.py` - CORS and authentication
- `models.py` - Request/response models

#### `src/agent/handlers/` (New Directory)
**Files:**
- `chat_handler.py` - Chat completion logic
- `model_handler.py` - Model listing and info
- `health_handler.py` - Health checks

## Migration Strategy

### Phase 1: Extract Services (Week 1)
1. **Create service abstractions**
   - Extract session management to `session/` module
   - Extract tool execution to `services/execution_service.py`
   - Extract memory operations to `services/memory_service.py`

2. **Update core.py**
   - Reduce to orchestration only
   - Remove direct service implementations
   - Use dependency injection pattern

### Phase 2: Server Separation (Week 2)
1. **Extract API layer**
   - Move FastAPI setup to `api/server.py`
   - Move endpoints to `api/endpoints.py`
   - Move models to `api/models.py`

2. **Create handler layer**
   - Extract business logic to `handlers/`
   - Separate HTTP concerns from business logic
   - Create clean interfaces between layers

### Phase 3: Integration (Week 3)
1. **Update imports across codebase**
   - Update all import statements
   - Ensure backward compatibility
   - Update tests to use new structure

2. **Add integration tests**
   - Test service interactions
   - Test API endpoint behavior
   - Test error handling across layers

## Benefits

### Maintainability
- **Single Responsibility**: Each module has one clear purpose
- **Testability**: Easier to unit test individual components
- **Readability**: Smaller, focused modules are easier to understand

### Scalability
- **Independent Deployment**: Services can be scaled independently
- **Technology Flexibility**: Easier to swap implementations
- **Team Development**: Multiple developers can work on different modules

### Reliability
- **Error Isolation**: Failures contained within modules
- **Monitoring**: Better observability per component
- **Debugging**: Easier to trace issues to specific modules

## Migration Checklist

### Pre-Migration
- [ ] Create backup of current core.py and server.py
- [ ] Set up new directory structure
- [ ] Create __init__.py files with proper imports
- [ ] Update pyproject.toml if needed

### During Migration
- [ ] Extract session management (Day 1-2)
- [ ] Extract tool execution services (Day 3-4)
- [ ] Extract memory services (Day 5)
- [ ] Refactor server.py to api/ structure (Day 6-7)
- [ ] Create handler layer (Day 8-9)
- [ ] Update all imports (Day 10)

### Post-Migration
- [ ] Run full test suite
- [ ] Performance testing
- [ ] Integration testing
- [ ] Update documentation
- [ ] Team training on new structure

## Risk Mitigation

### Backward Compatibility
- Maintain public APIs during transition
- Use deprecation warnings for old patterns
- Gradual rollout with feature flags

### Testing Strategy
- Unit tests for each new module
- Integration tests for module interactions
- End-to-end tests for complete workflows
- Performance benchmarks before/after

## Success Metrics

- **Code Reduction**: core.py < 150 lines, server.py < 100 lines
- **Test Coverage**: >90% for all new modules
- **Import Clarity**: Clear dependency graph with no circular imports
- **Performance**: No regression in response times or memory usage
