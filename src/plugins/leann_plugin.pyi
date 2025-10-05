from typing import Any


class LeannPlugin:
    async def execute(self, server: str, tool_name: str, args: dict[str, Any]) -> Any: ...
