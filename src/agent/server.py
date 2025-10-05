"""FastAPI server providing OpenAI-compatible API for Open WebUI integration."""

from __future__ import annotations

import os
from datetime import datetime
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .artifacts import ArtifactGenerator
from .services.http.dependencies import get_agent, get_plugin_executor
from .services.http.models import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    Message,
    Model,
    ModelList,
)
from .services.http.tooling import execute_tools_if_needed, stream_response

load_dotenv(override=True)

app = FastAPI(
    title="MCP AI Agent API",
    description="OpenAI-compatible API for MCP AI Agent with tool execution",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, object]:
    """Root endpoint with API information."""
    return {
        "name": "MCP AI Agent API",
        "version": "1.0.0",
        "endpoints": {"chat": "/v1/chat/completions", "models": "/v1/models"},
        "openwebui_compatible": True,
        "tools_available": ["browser", "news", "time", "filesystem"],
    }


@app.get("/health")
async def health() -> dict[str, object]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/v1/models")
async def list_models() -> ModelList:
    """List available models (OpenAI compatible)."""
    timestamp = int(datetime.now().timestamp())
    return ModelList(
        object="list",
        data=[
            Model(id="mcp-agent", created=timestamp, owned_by="mcp-agent"),
            Model(id="mcp-agent-tools", created=timestamp, owned_by="mcp-agent"),
        ],
    )


@app.get("/v1/models/{model_id}")
async def get_model(model_id: str) -> Model:
    """Get specific model information."""
    if model_id not in {"mcp-agent", "mcp-agent-tools"}:
        raise HTTPException(status_code=404, detail="Model not found")
    return Model(id=model_id, created=int(datetime.now().timestamp()), owned_by="mcp-agent")


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint (streaming and batch)."""
    agent = get_agent()
    executor = get_plugin_executor()
    request_id = f"chatcmpl-{datetime.now().timestamp()}"

    system_message = """You are an AI agent with direct tool execution and visual content generation capabilities.

IMPORTANT INSTRUCTIONS:
1. When user asks for news, ALWAYS acknowledge you are fetching it (do not just describe the process)
2. When user says "show" or "display" with news, you will receive the HTML in the response - acknowledge it is being displayed
3. For diagrams or flowcharts, generate MermaidJS code in ```mermaid blocks
4. For code requests, generate Python in ```python blocks
5. Provide concise, well-formatted responses with proper paragraphs

Your responses will be enhanced with:
- Automatic news fetching when you mention news
- HTML artifacts when user says "show" or "display"
- MermaidJS auto-rendering for diagrams
- Python code execution for analysis

Be direct and actionable. When tools execute, acknowledge the results briefly."""

    messages_with_system: List[Message] = request.messages
    if not any(message.role == "system" for message in request.messages):
        messages_with_system = [Message(role="system", content=system_message)] + request.messages

    if request.stream:
        return StreamingResponse(
            stream_response(messages_with_system, agent, executor, request.model, request_id),
            media_type="text/event-stream",
        )

    prompt = messages_with_system[-1].content if messages_with_system else ""
    context = "\n".join(f"{message.role}: {message.content}" for message in messages_with_system[:-1])

    tool_context, artifact_html = await execute_tools_if_needed(prompt, agent, executor)
    full_prompt = f"{context}\n{tool_context}\n{prompt}" if tool_context else f"{context}\n{prompt}"

    response_text = await agent.generate_response(full_prompt, "")
    response_text = ArtifactGenerator.format_text_response(response_text)

    if artifact_html:
        response_text = f"{response_text}\n\n```html\n{artifact_html}\n```"

    usage_prompt_tokens = len(full_prompt.split()) if full_prompt else 0
    usage_completion_tokens = len(response_text.split())

    response = ChatCompletionResponse(
        id=request_id,
        created=int(datetime.now().timestamp()),
        model=request.model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=Message(role="assistant", content=response_text),
                finish_reason="stop",
            )
        ],
        usage={
            "prompt_tokens": usage_prompt_tokens,
            "completion_tokens": usage_completion_tokens,
            "total_tokens": usage_prompt_tokens + usage_completion_tokens,
        },
    )

    return response


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("SERVER_PORT", "8000"))
    host = os.getenv("SERVER_HOST", "0.0.0.0")

    banner = (
        "==============================\n"
        "  MCP AI Agent API Server\n"
        "  OpenAI-compatible API for Open WebUI\n"
        "=============================="
    )
    print(banner)
    print(f"Server starting on http://{host}:{port}")
    print(f"API documentation: http://{host}:{port}/docs")
    print(f"OpenWebUI base URL: http://localhost:{port}/v1")
    print("Endpoints: POST /v1/chat/completions, GET /v1/models, GET /health")

    uvicorn.run(app, host=host, port=port)
