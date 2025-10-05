# Agent Core API Reference

## Overview

The Agent Core provides the main orchestration layer for the MCP AI Agent, coordinating all services and managing the overall agent lifecycle.

## Agent Class

::: agent.core.Agent
    handler: python
    options:
      show_root_heading: true
      show_root_toc_entry: true
      show_category_heading: true
      show_bases: true
      show_docstring_attributes: true
      show_docstring_functions: true

## Key Methods

### Initialization

```python
from agent.core import Agent

# Create agent with default configuration
agent = Agent(
    config_path="config/mcp_tools.json",
    memory_path="memory/sessions.json"
)
```

**Parameters:**
- `config_path` (str): Path to MCP tools configuration file
- `memory_path` (str): Path to session memory file

### Tool Execution

#### execute_tools

Execute multiple tools concurrently with automatic error handling and retry logic.

```python
tool_names = ["news_fetch", "analysis"]
args_dict = {
    "news_fetch": {"topic": "technology", "max_articles": 5},
    "analysis": {"data": "article_content", "analysis_type": "sentiment"}
}

results = await agent.execute_tools(tool_names, args_dict)
```

**Parameters:**
- `tool_names` (List[str]): Names of tools to execute
- `args_dict` (Dict[str, Dict[str, Any]]): Arguments for each tool

**Returns:**
- List[str]: Results from each tool execution

#### execute_single_tool

Execute a single tool (compatibility wrapper).

```python
from agent.models import MCPTool

tool = MCPTool(
    name="web_search",
    description="Search the web",
    inputSchema={"query": "string"}
)

result = await agent.execute_single_tool(tool, {"query": "Python async"})
```

**Parameters:**
- `tool` (MCPTool): Tool definition
- `args` (Dict[str, Any]): Tool arguments

**Returns:**
- str: Tool execution result

### Session Management

#### Context Building

```python
# Get memory context for prompts
context = agent.get_context()

# Get tool context for AI
tool_context = agent._build_tool_context()
```

#### Session Operations

```python
# Save current session
await agent.save_and_exit()

# Parse tool calls from AI response
tool_calls = agent.parse_tool_call_from_response(ai_response)
```

## Integration Examples

### Basic Usage Pattern

```python
import asyncio
from agent.core import Agent

async def main():
    # Initialize agent
    agent = Agent()

    # Execute tools
    results = await agent.execute_tools(
        ["news_fetch", "analysis"],
        {
            "news_fetch": {"topic": "AI", "max_articles": 3},
            "analysis": {"data": "news_content"}
        }
    )

    # Process results
    for result in results:
        print(f"Tool result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Error Handling

```python
from agent.errors import PluginExecutionError, ErrorContext
from agent.logging_utils import get_logger

logger = get_logger("agent_usage", LogComponent.AGENT)

async def robust_tool_execution(agent, tool_name, args):
    try:
        async with ErrorContext(f"execute_{tool_name}"):
            result = await agent.execute_tools([tool_name], {tool_name: args})
            return result[0]
    except PluginExecutionError as e:
        logger.error(
            f"Tool execution failed: {e}",
            operation="tool_execution",
            extra_fields={"tool": tool_name, "error": str(e)}
        )
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error: {e}",
            operation="tool_execution",
            extra_fields={"tool": tool_name}
        )
        return None
```

### Performance Monitoring

```python
from agent.metrics import track_performance, timer_context

class MonitoredAgent:
    def __init__(self):
        self.agent = Agent()

    @track_performance("agent_session", component="core")
    async def monitored_execute(self, tools, args):
        async with timer_context("agent_execution"):
            return await self.agent.execute_tools(tools, args)
```

## Configuration

### Default Configuration

The agent uses the following default paths:

- **Config**: `config/mcp_tools.json`
- **Memory**: `memory/sessions.json`

### Custom Configuration

```python
# Custom paths
agent = Agent(
    config_path="custom/mcp_config.json",
    memory_path="custom/agent_memory.json"
)
```

## Best Practices

### 1. Error Handling

Always wrap agent operations in appropriate error handling:

```python
from agent.errors import AgentError

try:
    results = await agent.execute_tools(tool_names, args_dict)
except AgentError as e:
    logger.error(f"Agent operation failed: {e}", operation="agent_execute")
    # Handle specific error types
    if isinstance(e, PluginExecutionError):
        # Handle plugin-specific errors
        pass
```

### 2. Resource Management

Use context managers for proper resource cleanup:

```python
async def managed_agent_session():
    agent = Agent()
    try:
        # Agent operations
        results = await agent.execute_tools(...)
        return results
    finally:
        # Cleanup
        await agent.save_and_exit()
```

### 3. Performance Optimization

For high-throughput scenarios:

```python
# Pre-initialize agent for reuse
agent = Agent()

# Batch similar operations
batch_tools = ["tool1", "tool2", "tool3"]
batch_args = {tool: args for tool in batch_tools}

results = await agent.execute_tools(batch_tools, batch_args)
```

## Troubleshooting

### Common Issues

#### Configuration Errors

```python
# Check configuration file exists and is valid
import json

try:
    with open("config/mcp_tools.json", "r") as f:
        config = json.load(f)
except FileNotFoundError:
    print("Configuration file not found")
except json.JSONDecodeError as e:
    print(f"Invalid JSON in config: {e}")
```

#### Memory Issues

```python
# Check memory file permissions and size
import os

memory_path = "memory/sessions.json"
if os.path.exists(memory_path):
    size_mb = os.path.getsize(memory_path) / (1024 * 1024)
    print(f"Memory file size: {size_mb:.2f} MB")
```

#### Plugin Loading Issues

```python
# Debug plugin loading
from agent.mcp_loader import MCPLoader

loader = MCPLoader()
try:
    tools = loader.load_tools()
    print(f"Loaded {len(tools)} tools")
except Exception as e:
    print(f"Plugin loading failed: {e}")
```

## Performance Characteristics

### Benchmarks

| Operation | Average Latency | P95 Latency | Success Rate |
|-----------|----------------|-------------|--------------|
| Tool Execution | 150ms | 400ms | 99.2% |
| Session Save | 25ms | 80ms | 99.9% |
| Memory Load | 15ms | 45ms | 99.8% |

### Resource Usage

- **Memory**: ~50MB base + ~10MB per active session
- **CPU**: Minimal for orchestration, depends on plugin workload
- **Network**: Varies by plugin requirements

## Related Components

- **[Plugin Executor](./plugin-system.md)**: Tool execution engine
- **[Session Manager](../development/session-management.md)**: Session lifecycle management
- **[Memory Store](./memory-store.md)**: Persistent storage
- **[Error Handling](./errors.md)**: Error classification and handling
