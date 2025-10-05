import asyncio

import pytest

from src.agent.models import MCPTool, Session
from src.agent.services.tool_dispatch import ToolDispatcher


class _DummyExecutor:
    async def execute(self, server_name: str, tool_name: str, args):
        return {"status": "success", "result": {"echo": args}}


@pytest.mark.asyncio
async def test_tool_dispatcher_executes_and_records_history():
    session = Session(id="demo", history=[])
    tool = MCPTool(name="echo", server="dummy", tool_name="echo_tool")
    session.loaded_tools = [tool]

    dispatcher = ToolDispatcher(_DummyExecutor())

    results = await dispatcher.execute_many(session, ["echo"], {"echo": {"value": 1}})

    assert results and "\"value\": 1" in results[0]
    assert session.history[-1]["role"] == "assistant"
