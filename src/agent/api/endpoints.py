"""API endpoint definitions."""

from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    Message,
    Model,
    ModelList,
)
from ..artifacts import ArtifactGenerator
from ..services.http.dependencies import get_agent, get_plugin_executor
from ..services.http.tooling import execute_tools_if_needed, stream_response

router = APIRouter()


@router.get("/")
async def root() -> dict[str, object]:
    """Root endpoint with API information."""
    return {
        "name": "MCP AI Agent API",
        "version": "1.0.0",
        "endpoints": {"chat": "/v1/chat/completions", "models": "/v1/models"},
        "openwebui_compatible": True,
        "tools_available": ["browser", "news", "time", "filesystem"],
    }


@router.get("/health")
async def health() -> dict[str, object]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@router.get("/v1/models")
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


@router.get("/v1/models/{model_id}")
async def get_model(model_id: str) -> Model:
    """Get specific model information."""
    if model_id not in {"mcp-agent", "mcp-agent-tools"}:
        raise HTTPException(status_code=404, detail="Model not found")
    return Model(id=model_id, created=int(datetime.now().timestamp()), owned_by="mcp-agent")


@router.post("/v1/chat/completions")
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
