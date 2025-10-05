"""
Core agent functionality and orchestration.

Manages the main agent lifecycle including tool loading, session management,
memory operations, and the primary execution loop for user interactions.
This module coordinates MCP tools, memory systems, and API interactions while
delegating specialised behavior to services under ``src/agent/services``.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Dict, Any, List

import sys
import os
# Ensure the src directory is in the path for correct module resolution
src_dir = os.path.join(os.path.dirname(__file__), '..', '..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from agent.api import AgentAPI as api_module
from .memory import MemoryStoreFileImpl
from .mcp_loader import MCPLoader
from .models import MCPTool
from .plugin_executor import PluginExecutor
from .services.context import build_memory_context, build_tool_context
from .services.instructions import load_custom_instructions
from .services.react_runner import ReactLoopRunner
from .services.session_manager import SessionManager
from .services.tool_dispatch import ToolDispatcher
from .services.tool_parsing import parse_tool_calls, parse_args_from_input as parse_args_from_text


class Agent:
    """High-level coordinator that wires together agent services."""

    def __init__(
        self,
        config_path: str = "config/mcp_tools.json",
        memory_path: str = "memory/sessions.json",
    ) -> None:
        self.loader = MCPLoader(config_path)
        self.memory = MemoryStoreFileImpl(memory_path)
        self.session_manager = SessionManager(self.memory)
        self.plugin_executor = PluginExecutor()
        self.tool_dispatcher = ToolDispatcher(self.plugin_executor)

        self.session_id = self.session_manager.new_session_id()
        self.session = self.session_manager.load(self.session_id)

        self.api = api_module.AgentAPI(self.session)
        self.custom_instructions = load_custom_instructions()

    async def execute_tools(
        self,
        tool_names: List[str],
        args_dict: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        """Execute multiple tools concurrently and capture their responses."""
        return await self.tool_dispatcher.execute_many(self.session, tool_names, args_dict)

    async def execute_single_tool(self, tool: MCPTool, args: Dict[str, Any]) -> str:
        """Execute a single tool via the dispatcher (compatibility wrapper)."""
        return await self.tool_dispatcher.execute_single(self.session, tool, args)

    def parse_tool_call_from_response(
        self, response: str
    ) -> tuple[List[str], Dict[str, Dict[str, str]]]:
        """Delegate tool-call parsing to the dedicated parsing service."""
        return parse_tool_calls(response)

    async def run(self) -> AsyncGenerator[str, None]:
        """Main interactive loop for CLI usage."""
        runner = ReactLoopRunner(
            api=self.api,
            plugin_executor=self.plugin_executor,
            loader=self.loader,
            memory_store=self.memory,
            session=self.session,
            on_exit=self.save_and_exit,
        )
        async for message in runner.stream():
            yield message

    def run_sync(self) -> None:
        """Synchronous wrapper for CLI compatibility."""
        async def _run() -> None:
            async for message in self.run():
                try:
                    print(message)
                except UnicodeEncodeError:
                    ascii_message = message.encode("ascii", errors="ignore").decode("ascii")
                    print(ascii_message)

        asyncio.run(_run())

    def _build_tool_context(self) -> str:
        """Build context about available tools for AI."""
        return build_tool_context(self.session.loaded_tools, self.custom_instructions)

    def get_context(self) -> str:
        """Get memory context for prompt, including past chats if referenced."""
        return build_memory_context(self.session, self.memory)

    async def save_and_exit(self) -> None:
        self.session_manager.save(self.session)
        print("Session saved. Goodbye!")

    @staticmethod
    def parse_args_from_input(user_input: str, tool_name: str) -> Dict[str, str]:
        """Simple arg parsing from input string (improve with parser as needed)."""
        return parse_args_from_text(user_input, tool_name)
