import typer
import asyncio
from typing import Dict, Any, Optional
import json
from .core import Agent
from .mcp_loader import MCPLoader

cli_app = typer.Typer(help="Modular CLI AI Agent with MCP Integration")

@cli_app.command()
def run():
    """Start interactive AI agent session."""
    async def _run():
        agent = Agent()
        try:
            async for message in agent.run():
                try:
                    print(message)
                except UnicodeEncodeError:
                    ascii_message = message.encode("ascii", errors="ignore").decode("ascii")
                    print(ascii_message)
        except KeyboardInterrupt:
            await agent.save_and_exit()

    asyncio.run(_run())

@cli_app.command()
def add_tool(
    name: str = typer.Option(..., "--name", "-n", help="Tool name"),
    server: str = typer.Option(..., help="MCP server name"),
    tool_name: str = typer.Option(..., help="Tool name in server"),
    args_schema: Optional[str] = typer.Option(None, help="JSON schema for args"),
):
    """Add a new MCP tool to config."""
    loader = MCPLoader()
    strip_chars = '"\''
    name = name.strip(strip_chars)
    server = server.strip(strip_chars)
    tool_name = tool_name.strip(strip_chars)
    tool_data: Dict[str, Any] = {
        "name": name,
        "server": server,
        "tool_name": tool_name,
    }
    if args_schema:
        try:
            parsed_schema = json.loads(args_schema)
            if isinstance(parsed_schema, str):
                parsed_schema = json.loads(parsed_schema)
            if not isinstance(parsed_schema, dict):
                raise json.JSONDecodeError('Schema must be JSON object', args_schema, 0)
            tool_data["args_schema"] = parsed_schema
        except json.JSONDecodeError:
            typer.echo("Failed to add tool: Invalid schema.", err=True)
            return
    if loader.add_tool(tool_data):
        typer.echo(f"Tool '{name}' added successfully.")
    else:
        typer.echo("Failed to add tool: Invalid schema.", err=True)

if __name__ == "__main__":
    cli_app()
