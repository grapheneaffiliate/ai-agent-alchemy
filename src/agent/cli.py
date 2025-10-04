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
    agent = Agent()
    asyncio.run(agent.run_sync())

@cli_app.command()
def add_tool(
    name: str = typer.Argument(..., help="Tool name"),
    server: str = typer.Option(..., help="MCP server name"),
    tool_name: str = typer.Option(..., help="Tool name in server"),
    args_schema: Optional[str] = typer.Option(None, help="JSON schema for args"),
):
    """Add a new MCP tool to config."""
    loader = MCPLoader()
    tool_data: Dict[str, Any] = {
        "name": name,
        "server": server,
        "tool_name": tool_name,
    }
    if args_schema:
        tool_data["args_schema"] = json.loads(args_schema)
    if loader.add_tool(tool_data):
        print(f"Tool '{name}' added successfully.")
    else:
        typer.echo("Failed to add tool: Invalid schema.", err=True)

if __name__ == "__main__":
    cli_app()
