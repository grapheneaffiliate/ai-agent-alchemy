"""Streaming interaction loop helpers."""

from __future__ import annotations

from typing import AsyncGenerator, Awaitable, Callable

from ..mcp_loader import MCPLoader
from ..memory import MemoryStoreFileImpl
from ..plugin_executor import PluginExecutor
from ..models import Session
from ..api import AgentAPI


ExitCallback = Callable[[], Awaitable[None]]


class ReactLoopRunner:
    """Coordinates the interactive REACT loop for the CLI interface."""

    def __init__(
        self,
        api: AgentAPI,
        plugin_executor: PluginExecutor,
        loader: MCPLoader,
        memory_store: MemoryStoreFileImpl,
        session: Session,
        on_exit: ExitCallback | None = None,
    ) -> None:
        self._api = api
        self._plugin_executor = plugin_executor
        self._loader = loader
        self._memory_store = memory_store
        self._session = session
        self._on_exit = on_exit

    async def stream(self) -> AsyncGenerator[str, None]:
        from ..react_loop import execute_react_loop

        self._session.loaded_tools = self._loader.load_tools()
        print("AI Agent started. Type 'exit' to quit.")
        print("Note: Tools require consent; confirm Y for each input.")

        if self._session.loaded_tools:
            print(f"Loaded {len(self._session.loaded_tools)} tools:")
            for tool in self._session.loaded_tools:
                print(f"  - {tool.name} ({tool.server})")

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                if self._on_exit:
                    await self._on_exit()
                break

            if not user_input.strip():
                yield "Please provide a valid input."
                continue

            try:
                result, _ = await execute_react_loop(user_input, self._api, self._plugin_executor)
                yield f"Agent: {result}"
            except Exception as exc:  # noqa: BLE001 - surface runtime errors
                yield f"Error during processing: {exc}. Please try again."
                continue

            self._memory_store.save_session(self._session)
