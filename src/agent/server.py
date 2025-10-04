"""FastAPI server providing OpenAI-compatible API for Open WebUI integration."""

import os
import json
import asyncio
from typing import Optional, List, Dict, Any, AsyncIterator
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .core import Agent
from .models import Session
from .plugin_executor import PluginExecutor
from .api import AgentAPI
from .artifacts import ArtifactGenerator

load_dotenv(override=True)

# FastAPI app
app = FastAPI(
    title="MCP AI Agent API",
    description="OpenAI-compatible API for MCP AI Agent with tool execution",
    version="1.0.0"
)

# CORS configuration for Open WebUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "*"  # Allow all for development - restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for OpenAI compatibility
class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="mcp-agent")
    messages: List[Message]
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=1000, ge=1)
    stream: Optional[bool] = False
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1)
    n: Optional[int] = Field(default=1, ge=1)
    stop: Optional[List[str]] = None

class ChatCompletionChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Dict[str, int]

class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]

class Model(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "mcp-agent"

class ModelList(BaseModel):
    object: str = "list"
    data: List[Model]

# Global agent instance
agent_instance: Optional[AgentAPI] = None
plugin_executor: Optional[PluginExecutor] = None

def get_agent() -> AgentAPI:
    """Get or create agent API instance."""
    global agent_instance, plugin_executor
    if agent_instance is None:
        session = Session(id="openwebui", history=[])
        agent_instance = AgentAPI(session)
        plugin_executor = PluginExecutor()
    return agent_instance

async def execute_tools_if_needed(message: str, agent: AgentAPI) -> tuple[str, Optional[str]]:
    """
    Check if message requires tool execution and execute if needed.
    Returns tuple of (tool_context, artifact_html)
    """
    global plugin_executor
    
    # Check for artifact requests
    artifact_type = ArtifactGenerator.detect_artifact_request(message)
    artifact_html = None
    
    # Simple heuristic to detect tool requests
    tool_keywords = {
        'browse': 'browser',
        'navigate': 'browser',
        'screenshot': 'browser',
        'news': 'news',
        'time': 'time',
        'date': 'time',
        'read file': 'filesystem',
        'list directory': 'filesystem'
    }
    
    message_lower = message.lower()
    tool_context = ""
    news_result = None
    
    for keyword, server in tool_keywords.items():
        if keyword in message_lower:
            # Extract parameters based on keyword
            if keyword in ['browse', 'navigate']:
                # Try to extract URL
                words = message.split()
                for word in words:
                    if word.startswith('http'):
                        result = await plugin_executor.execute(
                            'browser', 'navigate', {'url': word}
                        )
                        tool_context += f"\n[Browser Navigation Result: {json.dumps(result)}]\n"
                        break
            
            elif keyword in ['news']:
                # Get news
                result = await plugin_executor.execute(
                    'news', 'get_news', {'topic': 'ai', 'max_articles': 10}
                )
                news_result = result.get('result') if result.get('status') == 'success' else None
                
                # Generate artifact if requested or if it's a news request
                if news_result and (artifact_type == 'html' or 'show' in message_lower or 'display' in message_lower):
                    artifact_html = ArtifactGenerator.generate_news_page(news_result)
                    tool_context += f"\n[News fetched: {len(news_result.get('articles', []))} articles - displaying as HTML artifact]\n"
                else:
                    tool_context += f"\n[News Results: {json.dumps(result, indent=2)[:1000]}...]\n"
            
            elif keyword in ['time', 'date']:
                # Get time/date
                result = await plugin_executor.execute(
                    'time', 'get_current_time', {}
                )
                tool_context += f"\n[Current Time: {result}]\n"
    
    # Handle visualization requests
    if artifact_type == 'visualization' and not artifact_html:
        artifact_html = ArtifactGenerator.generate_data_visualization(
            {'title': 'Sample Data Visualization'}
        )
        tool_context += "\n[Generated interactive D3.js visualization]\n"
    
    # Handle SVG requests
    elif artifact_type == 'svg' and not artifact_html:
        # Extract content from message
        content = "SVG Graphic"
        if 'with text' in message_lower:
            words = message.lower().split('with text')
            if len(words) > 1:
                content = words[1].strip(' "\'').title()
        artifact_html = ArtifactGenerator.generate_simple_svg(content)
        tool_context += "\n[Generated SVG graphic]\n"
    
    return tool_context, artifact_html

async def stream_response(
    messages: List[Message],
    agent: AgentAPI,
    model: str,
    request_id: str
) -> AsyncIterator[str]:
    """Stream response chunks in OpenAI format."""
    # Build prompt from messages
    prompt = messages[-1].content if messages else ""
    context = "\n".join([f"{m.role}: {m.content}" for m in messages[:-1]])
    
    # Check for tool execution
    tool_context, artifact_html = await execute_tools_if_needed(prompt, agent)
    full_prompt = f"{context}\n{tool_context}\n{prompt}" if tool_context else f"{context}\n{prompt}"
    
    # Get response from agent
    response = await agent.generate_response(full_prompt, "")
    
    # If artifact, append it
    if artifact_html:
        response = f"{response}\n\n{artifact_html}"
    
    # Stream response word by word
    words = response.split()
    for i, word in enumerate(words):
        chunk = ChatCompletionChunk(
            id=request_id,
            created=int(datetime.now().timestamp()),
            model=model,
            choices=[{
                "index": 0,
                "delta": {"content": word + " " if i < len(words) - 1 else word},
                "finish_reason": None if i < len(words) - 1 else "stop"
            }]
        )
        yield f"data: {chunk.model_dump_json()}\n\n"
        await asyncio.sleep(0.05)  # Small delay for streaming effect
    
    yield "data: [DONE]\n\n"

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "MCP AI Agent API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "models": "/v1/models"
        },
        "openwebui_compatible": True,
        "tools_available": ["browser", "news", "time", "filesystem"]
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/v1/models")
async def list_models() -> ModelList:
    """List available models (OpenAI compatible)."""
    return ModelList(
        object="list",
        data=[
            Model(
                id="mcp-agent",
                created=int(datetime.now().timestamp()),
                owned_by="mcp-agent"
            ),
            Model(
                id="mcp-agent-tools",
                created=int(datetime.now().timestamp()),
                owned_by="mcp-agent"
            )
        ]
    )

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.
    Supports both streaming and non-streaming responses.
    """
    try:
        agent = get_agent()
        request_id = f"chatcmpl-{datetime.now().timestamp()}"
        
        # Build system message with tool and artifact awareness
        system_message = """You are an AI agent with direct tool execution and visual content generation capabilities.

IMPORTANT INSTRUCTIONS:
1. When user asks for news, ALWAYS acknowledge you are fetching it (don't just describe the process)
2. When user says "show" or "display" with news, you will receive the HTML in the response - acknowledge it's being displayed
3. For diagrams/flowcharts, generate MermaidJS code in ```mermaid blocks
4. For code requests, generate Python in ```python blocks  
5. Provide concise, well-formatted responses with proper paragraphs

Your responses will be enhanced with:
- Automatic news fetching when you mention news
- HTML artifacts when user says "show" or "display"
- MermaidJS auto-rendering for diagrams
- Python code execution for analysis

Be direct and actionable. When tools execute, acknowledge the results briefly."""

        # Add system message if not present
        messages_with_system = request.messages
        if not any(m.role == "system" for m in request.messages):
            messages_with_system = [
                Message(role="system", content=system_message)
            ] + request.messages
        
        # Handle streaming response
        if request.stream:
            return StreamingResponse(
                stream_response(messages_with_system, agent, request.model, request_id),
                media_type="text/event-stream"
            )
        
        # Non-streaming response
        prompt = messages_with_system[-1].content if messages_with_system else ""
        context = "\n".join([f"{m.role}: {m.content}" for m in messages_with_system[:-1]])
        
        # Check for tool execution and artifact generation
        tool_context, artifact_html = await execute_tools_if_needed(prompt, agent)
        
        # Build full context and response
        if tool_context:
            full_prompt = f"{context}\n{tool_context}\n{prompt}"
        else:
            full_prompt = f"{context}\n{prompt}"
        
        # Get AI response
        response_text = await agent.generate_response(full_prompt, "")
        
        # Format the response properly
        response_text = ArtifactGenerator.format_text_response(response_text)
        
        # If we have an artifact, wrap it in HTML code block for Open WebUI detection
        if artifact_html:
            response_text = f"{response_text}\n\n```html\n{artifact_html}\n```"
        
        # Build OpenAI-compatible response
        response = ChatCompletionResponse(
            id=request_id,
            created=int(datetime.now().timestamp()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=Message(role="assistant", content=response_text),
                    finish_reason="stop"
                )
            ],
            usage={
                "prompt_tokens": len(full_prompt.split()) if 'full_prompt' in locals() else 0,
                "completion_tokens": len(response_text.split()),
                "total_tokens": (len(full_prompt.split()) if 'full_prompt' in locals() else 0) + len(response_text.split())
            }
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str) -> Model:
    """Get specific model information."""
    if model_id not in ["mcp-agent", "mcp-agent-tools"]:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return Model(
        id=model_id,
        created=int(datetime.now().timestamp()),
        owned_by="mcp-agent"
    )

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("SERVER_PORT", "8000"))
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║  MCP AI Agent API Server                                 ║
    ║  OpenAI-compatible API for Open WebUI                    ║
    ╚══════════════════════════════════════════════════════════╝
    
    🚀 Server starting on http://{host}:{port}
    📝 API documentation: http://{host}:{port}/docs
    🔧 OpenWebUI base URL: http://localhost:{port}/v1
    
    Available endpoints:
    • POST /v1/chat/completions  - Chat completions (streaming/non-streaming)
    • GET  /v1/models            - List available models
    • GET  /health               - Health check
    
    Tools available:
    ✓ Browser automation (navigate, screenshot, extract)
    ✓ News fetching (RSS feeds)
    ✓ Time/date utilities
    ✓ File operations
    
    Artifacts enabled:
    ✓ HTML news pages (say "show me news")
    ✓ D3.js visualizations (say "create chart")
    ✓ SVG graphics (say "create svg")
    ✓ MermaidJS diagrams (say "create flowchart")
    ✓ Python code execution (say "write python code")
    
    Press Ctrl+C to stop
    """)
    
    uvicorn.run(app, host=host, port=port)
