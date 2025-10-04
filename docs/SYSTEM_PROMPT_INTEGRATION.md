# System Prompt Integration Guide

## Overview

The agent now includes a comprehensive model-agnostic system prompt that enables advanced features like tool use, artifact creation, web search, citations, and proper tone/formatting. This guide explains how the system prompt works and how to customize it.

## Architecture

### System Prompt Module (`src/agent/system_prompt.py`)

The system prompt module provides three main functions:

1. **`get_system_prompt()`** - Generates the complete system prompt with dynamic context
2. **`get_mcp_tool_info()`** - Extracts tool metadata for prompt injection
3. **`format_environment_details()`** - Formats environment context for the agent

### Integration with API (`src/agent/api.py`)

The `AgentAPI` class now:
- Accepts MCP tools during initialization
- Generates a customized system prompt with available tools
- Injects the system prompt as the first message in every conversation
- Includes environment details in user messages for context

## Configuration

### Environment Variables

Add these optional variables to your `.env` file to customize the system prompt:

```bash
# Model Configuration (for prompt customization)
COMPANY_NAME=OpenAI
MODEL_NAME=GPT
MODEL_FAMILY=GPT

# User Context
USER_LOCATION=New York, NY

# API Configuration (existing)
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL=gpt-4
```

### Default Values

If not specified, the system uses these defaults:
- **COMPANY_NAME**: OpenAI
- **MODEL_NAME**: GPT
- **MODEL_FAMILY**: GPT
- **USER_LOCATION**: Unknown

## Features Enabled by System Prompt

### 1. Tool Use

The agent can now use tools following the MCP (Model Context Protocol) standard:

```python
# Tools are automatically listed in the system prompt
# Agent can call them using structured function calls
{
  "tool": "use_mcp_tool",
  "server_name": "example-server",
  "tool_name": "example_tool",
  "arguments": {"param": "value"}
}
```

### 2. Artifact Creation

The agent creates artifacts for:
- Code snippets (>20 lines)
- Documents and reports
- HTML/CSS/JS applications
- React components
- SVG graphics
- Mermaid diagrams

Artifact types:
- `application/vnd.ant.code` - Code in any language
- `text/markdown` - Markdown documents
- `text/html` - HTML/CSS/JS
- `image/svg+xml` - SVG graphics
- `application/vnd.ant.mermaid` - Mermaid diagrams
- `application/vnd.ant.react` - React components

### 3. Web Search Integration

The agent knows when to search:
- **Never Search**: Timeless facts, fundamental concepts
- **Single Search**: Current events, recent data
- **Research**: Complex multi-source queries (5-20 searches)

Search categories help the agent balance efficiency with thoroughness.

### 4. Citation Handling

When using web search results, the agent:
- Wraps claims in `<citation>` tags with source indices
- Paraphrases content (never quotes directly)
- Provides minimum necessary citations
- Respects copyright (never reproduces copyrighted material)

### 5. Analysis Tool (REPL)

The agent can execute JavaScript for:
- Complex mathematical calculations
- Data file analysis (.xlsx, .csv, .json)
- Data visualizations
- Algorithm testing

**Note**: Only used when truly necessary (adds latency).

### 6. Tone and Formatting

The agent follows these guidelines:
- Natural, warm tone for casual conversations
- Concise for simple questions, thorough for complex ones
- Minimal formatting (no excessive bullets/headers)
- Direct (no "Great", "Certainly", etc.)
- Professional but approachable

### 7. Safety and Refusal

The agent:
- Refuses harmful content (weapons, malware, child exploitation)
- Protects user wellbeing (no self-destructive encouragement)
- Identifies mental health concerns
- Maintains ethical boundaries

## Usage Examples

### Basic Usage with System Prompt

```python
from src.agent.api import AgentAPI
from src.agent.models import Session

# Create session
session = Session(history=[])

# Initialize API with MCP tools
mcp_tools = [
    {
        "server": "example-server",
        "tool_name": "search_web",
        "args_schema": {"query": "string"},
        "description": "Search the web for information"
    }
]

api = AgentAPI(session, mcp_tools=mcp_tools)

# Generate response with environment context
response = await api.generate_response(
    prompt="What's the weather in Seattle?",
    environment_details=format_environment_details(
        working_directory="/home/user/project",
        visible_files=["main.py", "README.md"],
        open_tabs=["main.py"],
        time="Monday, September 29, 2025 7:00 PM",
        mode="ACT MODE"
    )
)
```

### Customizing System Prompt

```python
from src.agent.system_prompt import get_system_prompt

# Generate custom prompt
custom_prompt = get_system_prompt(
    company_name="Anthropic",
    model_name="Claude",
    model_family="Claude 3",
    model_string="claude-3-opus-20240229",
    user_location="San Francisco, CA",
    available_mcp_tools=[
        {
            "name": "search_web",
            "description": "Search the web",
            "parameters": {"query": "string"}
        }
    ]
)
```

## MCP Tool Integration

### Automatic Tool Discovery

When you initialize `AgentAPI` with MCP tools, they're automatically:
1. Formatted for the system prompt
2. Listed in the **AVAILABLE MCP TOOLS** section
3. Made available for the agent to use

### Tool Information Format

```python
{
    "name": "tool_name",
    "description": "What the tool does",
    "parameters": {
        "param1": "type1",
        "param2": "type2"
    }
}
```

### Loading from Config

```python
import json
from src.agent.mcp_loader import load_mcp_tools

# Load tools from config/mcp_tools.json
with open("config/mcp_tools.json") as f:
    mcp_config = json.load(f)

# Pass to API
api = AgentAPI(session, mcp_tools=mcp_config)
```

## Environment Details Injection

The `format_environment_details()` function creates context about:
- Current working directory
- Visible files in IDE
- Open tabs
- Current time
- Mode (PLAN/ACT)

This helps the agent understand the development environment.

### Example Output

```xml
<environment_details>
# VSCode Visible Files
src/main.py
README.md

# VSCode Open Tabs
src/main.py
src/utils.py

# Current Time
Monday, September 29, 2025 7:00 PM

# Current Working Directory
/home/user/project

# Current Mode
ACT MODE
</environment_details>
```

## Best Practices

### 1. Keep System Prompt Updated

When adding new tools or capabilities:
1. Update MCP tool configurations
2. Reinitialize `AgentAPI` with new tools
3. Test tool usage in conversation

### 2. Provide Environment Context

Always include environment details for better context:
```python
response = await api.generate_response(
    prompt=user_input,
    environment_details=format_environment_details(...)
)
```

### 3. Monitor Token Usage

The system prompt is large (~2000-3000 tokens). Monitor:
- Total tokens per request
- Context window limits
- Cost implications

### 4. Customize for Your Use Case

Adjust environment variables to match your setup:
- Set accurate `USER_LOCATION`
- Use correct `COMPANY_NAME` and `MODEL_FAMILY`
- Update as you switch models

### 5. Handle Long Conversations

For long conversations:
- System prompt is included in every request
- Consider truncating old history
- Monitor total message count

## Troubleshooting

### Issue: Agent doesn't use tools

**Solution**: Ensure MCP tools are passed to `AgentAPI`:
```python
api = AgentAPI(session, mcp_tools=tools_list)
```

### Issue: System prompt not appearing

**Solution**: Check `_initialize_system_prompt()` is called in `__init__`:
```python
def __init__(self, session: Session, mcp_tools=None):
    # ...
    self._initialize_system_prompt()
```

### Issue: Environment variables not loading

**Solution**: Ensure `.env` file exists and contains:
```bash
COMPANY_NAME=YourCompany
MODEL_NAME=YourModel
USER_LOCATION=Your City
```

### Issue: Token limit exceeded

**Solution**: 
1. Reduce history length
2. Trim old messages
3. Use smaller max_tokens
4. Consider message summarization

## Advanced Customization

### Adding New Sections

To add custom sections to the system prompt:

```python
# In system_prompt.py, modify get_system_prompt()
prompt = f"""
...existing sections...

**CUSTOM SECTION**
Your custom instructions here...
{custom_variable}

...rest of prompt...
"""
```

### Dynamic Tool Descriptions

Update tool descriptions dynamically:

```python
def get_mcp_tool_info(tool_config: Dict) -> Dict:
    # Add custom formatting
    description = tool_config.get('description', '')
    if tool_config.get('experimental'):
        description += " [EXPERIMENTAL]"
    
    return {
        'name': tool_config.get('tool_name'),
        'description': description,
        'parameters': tool_config.get('args_schema', {})
    }
```

### Context-Aware Prompts

Generate different prompts based on context:

```python
def get_context_aware_prompt(context_type: str, **kwargs):
    if context_type == "coding":
        # Emphasize code quality
        return get_system_prompt(
            **kwargs,
            additional_instructions="Focus on writing clean, maintainable code."
        )
    elif context_type == "research":
        # Emphasize thoroughness
        return get_system_prompt(
            **kwargs,
            additional_instructions="Provide comprehensive research with multiple sources."
        )
```

## Testing

### Unit Tests

Test system prompt generation:

```python
def test_system_prompt_generation():
    prompt = get_system_prompt(
        company_name="Test",
        model_name="TestModel"
    )
    assert "Test" in prompt
    assert "TestModel" in prompt
    assert "**ASSISTANT INFO**" in prompt
```

### Integration Tests

Test with API:

```python
async def test_api_with_system_prompt():
    session = Session(history=[])
    api = AgentAPI(session, mcp_tools=[])
    
    response = await api.generate_response("Hello")
    assert response is not None
    assert len(session.history) > 0
```

## Migration Guide

If upgrading from a previous version without system prompt:

1. **Update imports**:
   ```python
   from src.agent.system_prompt import get_system_prompt
   ```

2. **Modify API initialization**:
   ```python
   # Old
   api = AgentAPI(session)
   
   # New
   api = AgentAPI(session, mcp_tools=tools)
   ```

3. **Add environment variables**:
   Create or update `.env` with new variables

4. **Update generate_response calls**:
   ```python
   # Old
   response = await api.generate_response(prompt)
   
   # New
   response = await api.generate_response(
       prompt,
       environment_details=format_environment_details(...)
   )
   ```

5. **Test thoroughly**:
   - Verify tool usage works
   - Check artifact creation
   - Test search integration
   - Validate citations

## Performance Considerations

### Token Usage

- System prompt: ~2500-3500 tokens
- Per message overhead: +50-100 tokens
- Budget accordingly for long conversations

### Latency

- System prompt adds minimal latency (<50ms)
- Environment details add ~10-20ms
- Overall impact: <100ms per request

### Caching

Consider caching the system prompt:

```python
class AgentAPI:
    _cached_system_prompt = None
    
    def _initialize_system_prompt(self):
        if AgentAPI._cached_system_prompt is None:
            AgentAPI._cached_system_prompt = get_system_prompt(...)
        self.system_prompt = AgentAPI._cached_system_prompt
```

## Security Considerations

### API Key Protection

- Never include API keys in system prompt
- Load from environment variables only
- Use secure key management

### User Data Privacy

- Don't include sensitive data in environment details
- Sanitize file paths if needed
- Be careful with location data

### Refusal Handling

The system prompt includes refusal guidelines:
- Harmful content detection
- Child safety protection
- Malware/exploit prevention
- Ethical boundaries

Monitor agent responses for proper refusal handling.

## Future Enhancements

Planned improvements:
1. Dynamic prompt optimization based on conversation
2. Tool usage analytics and optimization
3. Automatic environment detection
4. Enhanced artifact rendering
5. Multi-modal support (images, audio)
6. Prompt versioning and A/B testing

## Support and Resources

- **Documentation**: See `/docs` directory
- **Examples**: Check `/examples` for usage patterns
- **Issues**: Report bugs via GitHub issues
- **Contributing**: See CONTRIBUTING.md

## Changelog

### Version 1.0.0 (2025-09-29)
- Initial system prompt integration
- MCP tool support
- Environment details injection
- Artifact creation support
- Search and citation handling
- Safety and refusal guidelines
