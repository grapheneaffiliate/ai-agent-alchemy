"""Dispatch helpers that wrap PluginExecutor interactions."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Iterable, List

from ..models import MCPTool, Session
from ..plugin_executor import PluginExecutor


class ToolDispatcher:
    """Executes MCP tools and records results on the session."""

    def __init__(self, executor: PluginExecutor):
        self._executor = executor

    async def execute_many(
        self,
        session: Session,
        tool_names: Iterable[str],
        args_dict: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        tasks = []
        for tool_name in tool_names:
            print(f"DEBUG: Looking for tool '{tool_name}'")
            print(f"DEBUG: Available tools: {[t.name for t in session.loaded_tools]}")
            tool = self._find_tool(session, tool_name)
            if tool is None:
                print(f"DEBUG: Tool '{tool_name}' not found")
                continue
            print(f"DEBUG: Found tool: {tool.name}")
            tool_args = args_dict.get(tool_name, {})
            tasks.append(self.execute_single(session, tool, tool_args))

        if not tasks:
            return ["No matching tools found."]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        output: List[str] = []
        for result in results:
            if isinstance(result, BaseException):
                output.append(f"Error: {result}")
            else:
                output.append(str(result))
        return output

    async def execute_single(
        self,
        session: Session,
        tool: MCPTool,
        args: Dict[str, Any],
    ) -> str:
        try:
            result = await self._executor.execute(tool.server, tool.tool_name, args)
        except Exception as exc:  # noqa: BLE001 - surface plugin errors
            error = {"error": str(exc)}
            session.history.append({"role": "assistant", "content": f"Tool execution error: {exc}"})
            return json.dumps(error)

        if result.get("status") == "success":
            payload = result.get("result", {})
            session.history.append(
                {"role": "assistant", "content": f"Tool {tool.name}: {json.dumps(payload)}"}
            )
            return json.dumps(payload, indent=2)

        error_message = result.get("error", "Unknown error")
        session.history.append(
            {"role": "assistant", "content": f"Tool {tool.name} error: {error_message}"}
        )
        return f"Tool error: {error_message}"

    @staticmethod
    def _find_tool(session: Session, tool_name: str) -> MCPTool | None:
        return next((tool for tool in session.loaded_tools if tool.name == tool_name), None)
