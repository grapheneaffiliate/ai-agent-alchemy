"""
Core agent functionality and orchestration.

Manages the main agent lifecycle including tool loading, session management,
memory operations, and the primary execution loop for user interactions.
This module serves as the central coordinator for all agent operations,
integrating MCP tools, memory systems, and API interactions.

Key Features:
- Tool loading and management from MCP configuration
- Session lifecycle management with persistence
- Memory integration for conversation history and context
- Plugin execution orchestration
- Custom instruction loading from .clinerules
- Interactive and programmatic execution modes
- Tool call parsing and execution coordination
"""

import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional
from .models import Session, MCPTool
from .api import AgentAPI
from .memory import MemoryStoreFileImpl
from .mcp_loader import MCPLoader
from .plugin_executor import PluginExecutor
from pathlib import Path
import re
import uuid
import json

class Agent:
    def __init__(self, config_path: str = "config/mcp_tools.json", memory_path: str = "memory/sessions.json"):
        self.loader = MCPLoader(config_path)  # Loads tools from JSON
        self.memory = MemoryStoreFileImpl(memory_path)
        self.plugin_executor = PluginExecutor()  # Initialize plugin executor
        self.api = AgentAPI(None)  # Session set later
        self.session_id = str(uuid.uuid4())
        self.session = self.memory.load_session(self.session_id) or Session(id=self.session_id)
        if self.api:
            self.api.session = self.session  # Link session to API
        
        # Load custom instructions from .clinerules
        self.custom_instructions = self._load_custom_instructions()
    
    def _load_custom_instructions(self) -> str:
        """Load custom behavior rules from .clinerules file."""
        rules_path = Path(".clinerules")
        if rules_path.exists():
            try:
                with open(rules_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Warning: Could not load .clinerules: {e}")
        return ""

    async def execute_tools(self, tool_names: List[str], args_dict: Dict[str, Dict[str, Any]]) -> List[str]:
        """Async execute multiple tools concurrently."""
        tasks = []
        for tool_name in tool_names:
            print(f"DEBUG: Looking for tool '{tool_name}'")
            print(f"DEBUG: Available tools: {[t.name for t in self.session.loaded_tools]}")
            tool = next((t for t in self.session.loaded_tools if t.name == tool_name), None)
            if tool:
                print(f"DEBUG: Found tool: {tool.name}")
                tool_args = args_dict.get(tool_name, {})
                tasks.append(self.execute_single_tool(tool, tool_args))
            else:
                print(f"DEBUG: Tool '{tool_name}' not found")
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r if not isinstance(r, Exception) else f"Error: {r}" for r in results]
        return ["No matching tools found."]

    async def execute_single_tool(self, tool: MCPTool, args: Dict[str, Any]) -> str:
        """Execute single tool using plugin executor."""
        try:
            # Execute tool through plugin executor
            result = await self.plugin_executor.execute(tool.server, tool.tool_name, args)
            
            # Format result for display
            if result.get("status") == "success":
                tool_result = result.get("result", {})
                # Use 'assistant' role instead of 'tool' for compatibility
                self.session.history.append({"role": "assistant", "content": f"Tool {tool.name}: {json.dumps(tool_result)}"})
                return json.dumps(tool_result, indent=2)
            else:
                error_msg = result.get("error", "Unknown error")
                # Use 'assistant' role for errors too
                self.session.history.append({"role": "assistant", "content": f"Tool {tool.name} error: {error_msg}"})
                return f"Tool error: {error_msg}"
                
        except Exception as e:
            error = {"error": str(e)}
            self.session.history.append({"role": "assistant", "content": f"Tool execution error: {str(e)}"})
            return json.dumps(error)

    def parse_tool_call_from_response(self, response: str) -> tuple[List[str], Dict[str, Dict[str, Any]]]:
        """Parse AI response for tool calls (simple regex for tool name and args)."""
        # Match tool names with hyphens: get-time, read-file, etc.
        tool_matches = re.findall(r'USE TOOL: ([\w-]+)(.*?)(?=USE TOOL:|$)', response, re.DOTALL)
        
        tool_names = []
        args_dict = {}
        
        for tool_name, tool_section in tool_matches:
            tool_names.append(tool_name)
            print(f"DEBUG: Parsing tool '{tool_name}' with section: {repr(tool_section[:100])}")
            
            # Parse arguments from the section after the tool name
            # Look for "key: value" patterns on separate lines
            arg_matches = re.findall(r'^(\w+):\s*(.+)$', tool_section, re.MULTILINE)
            print(f"DEBUG: Found {len(arg_matches)} arg matches: {arg_matches}")
            
            if arg_matches:
                args_dict[tool_name] = {key.strip(): value.strip() for key, value in arg_matches}
            else:
                args_dict[tool_name] = {}
                
        print(f"DEBUG: Final args_dict: {args_dict}")
        return tool_names, args_dict

    async def run(self) -> AsyncGenerator[str, None]:
        """Main interactive loop: Prompt user, generate response, execute tools if needed."""
        from .react_loop import execute_react_loop
        self.session.loaded_tools = self.loader.load_tools()  # Load configured tools
        print("AI Agent started. Type 'exit' to quit.")
        print("Note: Tools require consent; confirm Y for each input.")
        
        # Show available tools
        if self.session.loaded_tools:
            print(f"Loaded {len(self.session.loaded_tools)} tools:")
            for tool in self.session.loaded_tools:
                print(f"  - {tool.name} ({tool.server})")
        
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                await self.save_and_exit()
                break
    
            try:
                if not user_input.strip():  # Validate input
                    yield "Please provide a valid input."
                    continue
    
                result, _ = await execute_react_loop(user_input, self.api, self.plugin_executor)
                yield f"Agent: {result}"
            except Exception as e:
                yield f"Error during processing: {str(e)}. Please try again."
    
            # Save session async
            if self.memory:
                self.memory.save_session(self.session)

    def run_sync(self) -> None:
        """Synchronous wrapper for CLI compatibility."""
        async def _run():
            async for message in self.run():
                try:
                    print(message)
                except UnicodeEncodeError:
                    # Windows console can't handle some Unicode chars (emojis)
                    # Strip them and print ASCII-safe version
                    ascii_message = message.encode('ascii', errors='ignore').decode('ascii')
                    print(ascii_message)

        asyncio.run(_run())

    def _build_tool_context(self) -> str:
        """Build context about available tools for AI."""
        context_parts = []
        
        # Add custom instructions first if available
        if self.custom_instructions:
            context_parts.append("# CUSTOM BEHAVIOR INSTRUCTIONS")
            context_parts.append(self.custom_instructions)
            context_parts.append("\n---\n")
        
        if not self.session.loaded_tools:
            return "\n".join(context_parts) if context_parts else ""

        tool_list = []
        for tool in self.session.loaded_tools:
            tool_desc = f"- {tool.name} ({tool.server}.{tool.tool_name})"
            if tool.args_schema and "properties" in tool.args_schema:
                params = ", ".join(tool.args_schema["properties"].keys())
                tool_desc += f": {params}"
            tool_list.append(tool_desc)

        context_parts.append(f"""# AVAILABLE TOOLS

You have access to the following tools. Use them when appropriate to answer user queries:

{chr(10).join(tool_list)}

To use a tool, include 'USE TOOL: tool-name' followed by parameters in your response.
For time queries, use get-time or get-date tools.
For file operations, use read-file or list-dir tools.
For web browsing, use browse-url and related browser tools.""")
        
        return "\n".join(context_parts)

    def get_context(self) -> str:
        """Get memory context for prompt, including past chats if referenced."""
        recent_history = "\n".join([msg["content"] for msg in self.session.history[-5:]]) if self.session.history else ""
        
        # Detect past chat references (simple keyword check)
        user_input = getattr(self.session.history[-1], 'content', '') if self.session.history else ""  # Last user msg
        past_keywords = ['previous', 'last', 'before', 'discussed', 'remember', 'past', 'earlier', 'yesterday']
        if any(keyword in user_input.lower() for keyword in past_keywords):
            # Extract keywords for search
            import re
            words = re.findall(r'\b(\w+\s*\w*)\b', user_input.lower())
            keywords = list(set([w for w in words if len(w) > 3 and any(k in w for k in past_keywords[:2])]))  # Top 2 for seed
            if keywords:
                self.memory.load_all()  # Ensure fresh
                past_sessions = self.memory.search_sessions(keywords[:3])  # Limit to 3 keywords
                if past_sessions:
                    # Summarize relevant past context
                    past_summary = "\nPast conversations:\n"
                    for ses in past_sessions[:3]:  # Limit to 3 sessions
                        past_summary += f"- Session {ses.id[:8]}: {', '.join([m.get('content', '')[:50] + '...' for m in ses.history[:2]])}"
                    recent_history += f"\n{past_summary}"
            else:
                # Fallback to recent sessions
                recent = self.memory.get_recent_sessions(n=5)
                if recent:
                    recent_summary = "\nRecent sessions:\n"
                    for ses in recent[:3]:
                        recent_summary += f"- Session {ses.id[:8]}: Recent activity"
                    recent_history += f"\n{recent_summary}"
        
        return recent_history

    async def save_and_exit(self) -> None:
        if self.memory:
            self.memory.save_session(self.session)
        print("Session saved. Goodbye!")

    @staticmethod
    def parse_args_from_input(user_input: str, tool_name: str) -> Optional[Dict[str, Any]]:
        """Simple arg parsing from input string (improve with LLM or parser)."""
        # Stub: Extract args, e.g., "read file path: ./"
        match = re.search(r'path:\s*(\S+)', user_input)
        if match:
            return {"path": match.group(1)}
        return {}
