"""
Smoke tests to guard against refactoring regressions.

These tests ensure core functionality remains intact during
async migration and module restructuring.
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Core imports - these should work regardless of refactoring
from agent.core import Agent
from agent.server import app
from agent.mcp_loader import MCPLoader
from agent.memory import MemoryStoreFileImpl
from agent.plugin_executor import PluginExecutor


class TestCoreFunctionality:
    """Test core agent functionality remains intact."""

    def test_agent_initialization(self):
        """Test Agent can be initialized with default config."""
        agent = Agent()
        assert agent is not None
        assert hasattr(agent, 'loader')
        assert hasattr(agent, 'memory')
        assert hasattr(agent, 'plugin_executor')
        assert hasattr(agent, 'api')

    def test_mcp_loader_initialization(self):
        """Test MCP loader can initialize."""
        loader = MCPLoader()
        assert loader is not None
        assert hasattr(loader, 'config_path')

    def test_memory_store_initialization(self):
        """Test memory store can initialize."""
        memory = MemoryStoreFileImpl()
        assert memory is not None
        assert hasattr(memory, 'file_path')

    def test_plugin_executor_initialization(self):
        """Test plugin executor can initialize."""
        executor = PluginExecutor()
        assert executor is not None

    @pytest.mark.asyncio
    async def test_agent_tool_execution_interface(self):
        """Test agent has required async tool execution methods."""
        agent = Agent()

        # Should have execute_tools method
        assert hasattr(agent, 'execute_tools')
        assert asyncio.iscoroutinefunction(agent.execute_tools)

        # Should have execute_single_tool method
        assert hasattr(agent, 'execute_single_tool')
        assert asyncio.iscoroutinefunction(agent.execute_single_tool)

    def test_server_initialization(self):
        """Test FastAPI server initializes correctly."""
        assert app is not None
        assert hasattr(app, 'routes')

        # Should have expected endpoints
        routes = [route.path for route in app.routes]
        assert "/" in routes
        assert "/health" in routes
        assert "/v1/models" in routes
        assert "/v1/chat/completions" in routes


class TestAsyncMigrationGuards:
    """Guard against async migration regressions."""

    @pytest.mark.asyncio
    async def test_core_async_methods_exist(self):
        """Ensure core methods are properly async."""
        agent = Agent()

        # These should be coroutine functions
        assert asyncio.iscoroutinefunction(agent.execute_tools)
        assert asyncio.iscoroutinefunction(agent.execute_single_tool)

        # Should be able to call without errors (even if mocked)
        with patch.object(agent.tool_dispatcher, 'execute_many', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = ["mock response"]
            result = await agent.execute_tools(["test_tool"], {"test_tool": {"arg": "value"}})
            assert result == ["mock response"]

    def test_config_file_accessibility(self):
        """Test config file is accessible."""
        config_path = Path("config/mcp_tools.json")
        assert config_path.exists()

        loader = MCPLoader()
        # Should not raise an exception
        assert loader.config_path == "config/mcp_tools.json"


class TestModuleStructureGuards:
    """Guard against module structure regressions."""

    def test_agent_module_exports(self):
        """Test expected classes are exportable from agent module."""
        # These imports should work regardless of internal structure
        from agent.core import Agent
        from agent.server import app
        from agent.mcp_loader import MCPLoader
        from agent.memory import MemoryStoreFileImpl
        from agent.plugin_executor import PluginExecutor

        # Should be able to instantiate all
        Agent()
        MCPLoader()
        MemoryStoreFileImpl()
        PluginExecutor()

        # App should be accessible
        assert app

    def test_plugin_interface_compatibility(self):
        """Test plugin interfaces remain compatible."""
        from agent.models import MCPTool

        # Should be able to create MCPTool instances
        tool = MCPTool(
            name="test_tool",
            description="Test tool",
            inputSchema={}
        )
        assert tool.name == "test_tool"


class TestIntegrationSmokeTests:
    """High-level integration smoke tests."""

    def test_cli_import_compatibility(self):
        """Test CLI module can be imported."""
        from agent.cli import cli_app
        assert cli_app is not None

    def test_api_import_compatibility(self):
        """Test API module can be imported."""
        from agent.api import AgentAPI
        assert AgentAPI is not None

    @pytest.mark.asyncio
    async def test_end_to_end_import_flow(self):
        """Test complete import and initialization flow."""
        # This should work regardless of internal refactoring
        agent = Agent()
        loader = MCPLoader()
        memory = MemoryStoreFileImpl()
        executor = PluginExecutor()

        # Should be able to access core attributes
        assert hasattr(agent, 'session_id')
        assert hasattr(agent, 'session')
        assert agent.loader is loader
        assert agent.memory is memory
        assert agent.plugin_executor is executor


if __name__ == "__main__":
    # Can be run directly for quick smoke testing
    pytest.main([__file__, "-v"])
