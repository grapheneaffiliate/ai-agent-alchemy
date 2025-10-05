"""Data models for MCP agent system.

This module defines the core data structures used throughout the agent system,
including MCP tool representations, session management, and memory storage.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class MCPServerTool:
    """Represents a tool call to an MCP server.
    
    This class encapsulates the information needed to invoke a specific tool
    on an MCP server, including the server name, tool name, and arguments.
    
    Attributes:
        server_name: Name of the MCP server hosting the tool
        tool_name: Name of the tool to invoke
        arguments: Dictionary of arguments to pass to the tool
    """
    
    def __init__(self, server_name: str, tool_name: str, arguments: Dict[str, Any]):
        """Initialize an MCP server tool call.
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool
            arguments: Tool arguments as key-value pairs
        """
        self.server_name = server_name
        self.tool_name = tool_name
        self.arguments = arguments


class MCPTool:
    """Represents an MCP tool definition.
    
    This class defines a tool that can be used by the agent, including its
    name, the server it belongs to, and its argument schema.
    
    Attributes:
        name: Friendly name for the tool
        server: MCP server name
        tool_name: Actual tool name on the server
        args_schema: JSON schema for tool arguments (optional)
    """
    
    def __init__(self, name: str, server: str, tool_name: str, args_schema: Optional[Dict[str, Any]] = None):
        """Initialize an MCP tool definition.
        
        Args:
            name: User-friendly tool name
            server: MCP server hosting this tool
            tool_name: Tool's name on the server
            args_schema: Optional JSON schema defining tool arguments
        """
        self.name = name
        self.server = server
        self.tool_name = tool_name
        self.args_schema = args_schema

    def to_call(self, args: Dict[str, Any]) -> MCPServerTool:
        """Create a server tool call from this tool definition.
        
        Args:
            args: Arguments for the tool call
            
        Returns:
            MCPServerTool instance ready for execution
        """
        return MCPServerTool(
            server_name=self.server,
            tool_name=self.tool_name,
            arguments=args
        )

    def model_dump(self) -> Dict[str, Any]:
        """Serialize tool to dictionary format.
        
        Returns:
            Dictionary representation of the tool
        """
        return {
            "name": self.name,
            "server": self.server,
            "tool_name": self.tool_name,
            "args_schema": self.args_schema
        }

    @classmethod
    def model_validate(cls, data: Dict[str, Any]) -> 'MCPTool':
        """Create tool instance from dictionary data.
        
        Args:
            data: Dictionary containing tool data
            
        Returns:
            New MCPTool instance
        """
        return cls(
            name=data["name"],
            server=data["server"],
            tool_name=data["tool_name"],
            args_schema=data.get("args_schema")
        )


class Session:
    """Represents an agent session with conversation history.
    
    A session tracks the conversation history, current task, loaded tools,
    and metadata for a single agent interaction session.
    
    Attributes:
        id: Unique session identifier
        history: List of conversation messages
        current_task: Currently active task description
        loaded_tools: Tools available in this session
        created_at: Session creation timestamp
    """
    
    def __init__(self, id: str, history: Optional[List[Dict[str, str]]] = None,
                 current_task: Optional[str] = None, loaded_tools: Optional[List[MCPTool]] = None,
                 created_at: Optional[datetime] = None, updated_at: Optional[datetime] = None):
        """Initialize a new session.

        Args:
            id: Unique session identifier
            history: Optional conversation history
            current_task: Optional current task description
            loaded_tools: Optional list of available tools
            created_at: Optional creation timestamp (defaults to now)
            updated_at: Optional update timestamp (defaults to now)
        """
        self.id = id
        self.history = history or []
        self.current_task = current_task
        self.loaded_tools = loaded_tools or []
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def model_dump(self) -> Dict[str, Any]:
        """Serialize session to dictionary format.

        Returns:
            Dictionary representation of the session
        """
        return {
            "id": self.id,
            "history": self.history,
            "current_task": self.current_task,
            "loaded_tools": [tool.model_dump() for tool in self.loaded_tools],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def model_validate(cls, data: Dict[str, Any]) -> 'Session':
        """Create session instance from dictionary data.

        Args:
            data: Dictionary containing session data

        Returns:
            New Session instance
        """
        loaded_tools = [MCPTool.model_validate(tool_data) for tool_data in data.get("loaded_tools", [])]
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        updated_at = datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        return cls(
            id=data["id"],
            history=data.get("history", []),
            current_task=data.get("current_task"),
            loaded_tools=loaded_tools,
            created_at=created_at,
            updated_at=updated_at
        )


class MemoryStore:
    """In-memory storage for agent sessions.
    
    Provides simple session persistence and retrieval during runtime.
    Sessions are stored in memory and lost when the process terminates.
    
    Attributes:
        sessions: Dictionary mapping session IDs to Session objects
    """
    
    def __init__(self, sessions: Optional[Dict[str, Session]] = None):
        """Initialize memory store.
        
        Args:
            sessions: Optional pre-existing sessions dictionary
        """
        self.sessions = sessions or {}

    def save_session(self, session: Session) -> None:
        """Save a session to memory.
        
        Args:
            session: Session instance to save
        """
        self.sessions[session.id] = session

    def load_session(self, session_id: str) -> Optional[Session]:
        """Load a session from memory.
        
        Args:
            session_id: ID of session to retrieve
            
        Returns:
            Session if found, None otherwise
        """
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[str]:
        """Get list of all session IDs.
        
        Returns:
            List of session ID strings
        """
        return list(self.sessions.keys())
