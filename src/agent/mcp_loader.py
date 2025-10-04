import json
from pathlib import Path
from typing import List, Dict, Any
from .models import MCPTool

class MCPLoader:
    def __init__(self, config_path: str = "config/mcp_tools.json"):
        self.config_path = Path(config_path)
        self.tools: List[MCPTool] = []

    def load_tools(self) -> List[MCPTool]:
        """Load and validate tools from config JSON."""
        if not self.config_path.exists():
            self.tools = []
            return self.tools
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Handle both flat list and nested "servers" structure
            if isinstance(config, dict) and "servers" in config:
                # Nested structure: {"servers": [{"name": "...", "tools": [...]}]}
                all_tools = []
                for server in config["servers"]:
                    server_name = server.get("name", "unknown")
                    for tool in server.get("tools", []):
                        # Convert to flat MCPTool structure
                        tool_dict = {
                            "name": tool.get("name", tool.get("tool_name", "unnamed")),
                            "server": server_name,
                            "tool_name": tool.get("tool_name", tool.get("name")),
                            "args_schema": tool.get("args_schema", tool.get("parameters"))
                        }
                        all_tools.append(tool_dict)
                self.tools = [MCPTool.model_validate(d) for d in all_tools]
            else:
                # Flat list structure (legacy)
                self.tools = [MCPTool.model_validate(d) for d in config]
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Config validation error: {e}")
            self.tools = []
        return self.tools

    def list_available_tools(self) -> List[str]:
        """List names of available tools."""
        return [tool.name for tool in self.tools]

    def add_tool(self, tool_data: Dict[str, Any]) -> bool:
        """Add a new tool to config and save."""
        try:
            new_tool = MCPTool.model_validate(tool_data)
            self.tools.append(new_tool)
            with open(self.config_path, 'w') as f:
                json.dump([tool.model_dump() for tool in self.tools], f, indent=2)
            return True
        except (KeyError, ValueError) as e:
            print(f"Tool validation error: {e}")
            return False

    def format_mcp_call(self, tool: MCPTool, args: Dict[str, Any]) -> str:
        """Format tool call to XML string for MCP."""
        return f"""
<use_mcp_tool>
<server_name>{tool.server}</server_name>
<tool_name>{tool.tool_name}</tool_name>
<arguments>
{json.dumps(args)}
</arguments>
</use_mcp_tool>"""
