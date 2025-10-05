"""Tool orchestration helpers for the HTTP service."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import AsyncIterator, List, Optional, Tuple

from ...artifacts import ArtifactGenerator
from ...plugin_executor import PluginExecutor
from .models import ChatCompletionChunk, Message


async def execute_tools_if_needed(
    message: str,
    agent: "AgentAPI",
    plugin_executor: PluginExecutor,
) -> Tuple[str, Optional[str]]:
    """Check message for tool or artifact triggers and execute accordingly."""
    artifact_type = ArtifactGenerator.detect_artifact_request(message)
    artifact_html = None

    tool_keywords = {
        "browse": "browser",
        "navigate": "browser",
        "screenshot": "browser",
        "news": "news",
        "time": "time",
        "date": "time",
        "read file": "filesystem",
        "list directory": "filesystem",
    }

    message_lower = message.lower()
    tool_context = ""

    for keyword, server in tool_keywords.items():
        if keyword not in message_lower:
            continue

        if keyword in {"browse", "navigate"}:
            url = next((word for word in message.split() if word.startswith("http")), None)
            if not url:
                continue
            result = await plugin_executor.execute(server, "navigate", {"url": url})
            tool_context += f"\n[Browser Navigation Result: {json.dumps(result)}]\n"

        elif keyword == "news":
            result = await plugin_executor.execute("news", "get_news", {"topic": "ai", "max_articles": 10})
            if result.get("status") == "success":
                news_result = result.get("result")
            else:
                news_result = None

            if news_result and (
                artifact_type == "html" or "show" in message_lower or "display" in message_lower
            ):
                artifact_html = ArtifactGenerator.generate_news_page(news_result)
                count = len(news_result.get("articles", []))
                tool_context += f"\n[News fetched: {count} articles - displaying as HTML artifact]\n"
            else:
                tool_context += f"\n[News Results: {json.dumps(result, indent=2)[:1000]}...]\n"

        elif keyword in {"time", "date"}:
            result = await plugin_executor.execute("time", "get_current_time", {})
            tool_context += f"\n[Current Time: {result}]\n"

    if artifact_type == "visualization" and not artifact_html:
        artifact_html = ArtifactGenerator.generate_data_visualization({"title": "Sample Data Visualization"})
        tool_context += "\n[Generated interactive D3.js visualization]\n"
    elif artifact_type == "svg" and not artifact_html:
        content = "SVG Graphic"
        if "with text" in message_lower:
            parts = message_lower.split("with text")
            if len(parts) > 1:
                content = parts[1].strip(' "\'').title()
        artifact_html = ArtifactGenerator.generate_simple_svg(content)
        tool_context += "\n[Generated SVG graphic]\n"

    return tool_context, artifact_html


async def stream_response(
    messages: List[Message],
    agent: "AgentAPI",
    plugin_executor: PluginExecutor,
    model: str,
    request_id: str,
) -> AsyncIterator[str]:
    """Stream response chunks in OpenAI format."""
    prompt = messages[-1].content if messages else ""
    context = "\n".join(f"{message.role}: {message.content}" for message in messages[:-1])

    tool_context, artifact_html = await execute_tools_if_needed(prompt, agent, plugin_executor)
    full_prompt = f"{context}\n{tool_context}\n{prompt}" if tool_context else f"{context}\n{prompt}"

    response = await agent.generate_response(full_prompt, "")
    if artifact_html:
        response = f"{response}\n\n{artifact_html}"

    words = response.split()
    for index, word in enumerate(words):
        chunk = ChatCompletionChunk(
            id=request_id,
            created=int(datetime.now().timestamp()),
            model=model,
            choices=[
                {
                    "index": 0,
                    "delta": {"content": word + " " if index < len(words) - 1 else word},
                    "finish_reason": None if index < len(words) - 1 else "stop",
                }
            ],
        )
        yield f"data: {chunk.model_dump_json()}\n\n"
        await asyncio.sleep(0.05)

    yield "data: [DONE]\n\n"
