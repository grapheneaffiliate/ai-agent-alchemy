"""Context assembly utilities for the agent."""

from __future__ import annotations

from typing import Iterable, List

from ..models import MCPTool, Session
from ..memory import MemoryStoreFileImpl


def build_tool_context(loaded_tools: Iterable[MCPTool], custom_instructions: str) -> str:
    """Render custom instructions and available tools into a prompt fragment."""
    context_parts: List[str] = []

    if custom_instructions:
        context_parts.append("# CUSTOM BEHAVIOR INSTRUCTIONS")
        context_parts.append(custom_instructions)
        context_parts.append("\n---\n")

    tools = list(loaded_tools)
    if not tools:
        return "\n".join(context_parts) if context_parts else ""

    tool_lines: List[str] = []
    for tool in tools:
        description = f"- {tool.name} ({tool.server}.{tool.tool_name})"
        args_schema = getattr(tool, "args_schema", None)
        if args_schema and isinstance(args_schema, dict) and "properties" in args_schema:
            params = ", ".join(args_schema["properties"].keys())
            description += f": {params}"
        tool_lines.append(description)

    context_parts.append(
        """# AVAILABLE TOOLS

You have access to the following tools. Use them when appropriate to answer user queries:

{tools_list}

To use a tool, include 'USE TOOL: tool-name' followed by parameters in your response.
For time queries, use get-time or get-date tools.
For file operations, use read-file or list-dir tools.
For web browsing, use browse-url and related browser tools.""".format(tools_list="\n".join(tool_lines))
    )

    return "\n".join(context_parts)


def build_memory_context(session: Session, memory_store: MemoryStoreFileImpl | None) -> str:
    """Compose recent memory context, including past-session references when detected."""
    recent_history = "\n".join(item.get("content", "") for item in session.history[-5:]) if session.history else ""

    if not session.history:
        return recent_history

    last_message = session.history[-1]
    user_input = last_message.get("content", "") if isinstance(last_message, dict) else getattr(last_message, "content", "")

    past_keywords = ["previous", "last", "before", "discussed", "remember", "past", "earlier", "yesterday"]
    if not any(keyword in user_input.lower() for keyword in past_keywords):
        return recent_history

    if not memory_store:
        return recent_history

    import re

    words = re.findall(r"\b(\w+\s*\w*)\b", user_input.lower())
    keywords = list(
        {word for word in words if len(word) > 3 and any(anchor in word for anchor in past_keywords[:2])}
    )

    if keywords:
        memory_store.load_all()
        past_sessions = memory_store.search_sessions(keywords[:3])
        if past_sessions:
            summary_lines = ["\nPast conversations:"]
            for session_item in past_sessions[:3]:
                snippets = [message.get("content", "")[:50] + "..." for message in session_item.history[:2]]
                summary_lines.append(f"- Session {session_item.id[:8]}: {', '.join(snippets)}")
            recent_history += "\n" + "\n".join(summary_lines)
    else:
        recent = memory_store.get_recent_sessions(n=5)
        if recent:
            summary_lines = ["\nRecent sessions:"]
            for session_item in recent[:3]:
                summary_lines.append(f"- Session {session_item.id[:8]}: Recent activity")
            recent_history += "\n" + "\n".join(summary_lines)

    return recent_history
