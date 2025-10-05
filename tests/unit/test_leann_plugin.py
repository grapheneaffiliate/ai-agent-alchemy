"""Unit tests for LEANN plugin functionality."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import subprocess

from src.plugins.leann_plugin import LeannPlugin
from src.plugins.leann.index_service import LeannIndexService
from src.plugins.leann.orchestrator import LeannAnalysisOrchestrator


class TestLeannPlugin:
    """Test suite for LeannPlugin class."""

    @pytest.fixture
    def plugin(self):
        """Create a LeannPlugin instance for testing."""
        return LeannPlugin()

    def test_plugin_initialization(self, plugin):
        """Test that plugin initializes correctly."""
        assert isinstance(plugin, LeannPlugin)
        assert hasattr(plugin, 'leann_command')
        assert plugin.leann_command == "leann"
        assert hasattr(plugin, 'available')
        assert isinstance(plugin.index_service, LeannIndexService)
        assert isinstance(plugin.analysis_orchestrator, LeannAnalysisOrchestrator)

    def test_plugin_availability_detection(self, plugin):
        """Test plugin availability detection."""
        # The availability should be a boolean
        assert isinstance(plugin.available, bool)
        assert isinstance(plugin.wsl_available, bool)
        assert isinstance(plugin.wsl_leann_available, bool)
        assert isinstance(plugin.windows_leann_available, bool)

    def test_get_command_runner_windows_only(self):
        """Test command runner when only Windows LEANN is available."""
        plugin = LeannPlugin.__new__(LeannPlugin)  # Create without __init__
        plugin.wsl_available = False
        plugin.wsl_leann_available = False
        plugin.windows_leann_available = True
        plugin.leann_command = "leann"

        cmd, using_wsl = plugin._get_command_runner(["search", "test"])

        assert not using_wsl  # Should use Windows version
        assert cmd[0] == "leann"

    @pytest.mark.asyncio
    async def test_leann_search_fallback_when_unavailable(self, plugin):
        """Test that search falls back to text search when LEANN unavailable."""
        # Force plugin to be unavailable
        plugin.available = False

        result = await plugin.leann_search("test_index", "test query")

        assert result["status"] == "success"
        assert "fallback" in result.get("method", "")
        # Should return results even when vector search unavailable

    def test_extract_import_patterns(self, plugin):
        """Test import pattern extraction from search results."""
        search_results = """
        File: src/agent/core.py
        import json
        from pathlib import Path
        import asyncio
        from typing import Dict, Any
        File: src/agent/api.py
        from .core import SomeClass
        """

        patterns = plugin._extract_import_patterns(search_results)

        assert "modules" in patterns
        assert "import_statements" in patterns
        assert isinstance(patterns["modules"], list)
        assert isinstance(patterns["import_statements"], list)

    def test_extract_class_relationships(self, plugin):
        """Test class hierarchy extraction."""
        search_results = """
        class AgentCore:
            pass

        class PluginExecutor(AgentCore):
            pass

        class AsyncPluginExecutor(PluginExecutor):
            pass
        """

        hierarchies = plugin._extract_class_relationships(search_results)

        assert "hierarchy" in hierarchies
        assert "inheritance_count" in hierarchies
        assert hierarchies["inheritance_count"] > 0

    def test_calculate_change_risk(self, plugin):
        """Test risk assessment for code changes."""
        # Low risk scenario
        impact_low = {
            "affected_functions": ["update_config"],
            "affected_classes": [],
            "usage_count": 2
        }
        assert plugin._calculate_change_risk(impact_low) == "low"

        # High risk scenario
        impact_high = {
            "affected_functions": ["execute", "search", "analyze", "save", "load", "connect"],
            "affected_classes": ["CoreAgent", "PluginManager"],
            "usage_count": 25
        }
        assert plugin._calculate_change_risk(impact_high) == "high"

    @pytest.mark.asyncio
    async def test_plugin_execute_method_routing(self, plugin):
        """Test that execute method properly routes to specific tools."""
        # Mock a method to test routing
        with patch.object(plugin, 'leann_list') as mock_list:
            mock_list.return_value = {"status": "success", "indexes": []}

            result = await plugin.execute('leann', 'leann_list', {})

            mock_list.assert_called_once()
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_plugin_execute_unknown_tool(self, plugin):
        """Test error handling for unknown tools."""
        result = await plugin.execute('leann', 'unknown_tool', {})

        assert result["status"] == "error"
        assert "Unknown tool" in result["error"]

    @pytest.mark.asyncio
    async def test_plugin_execute_wrong_server(self, plugin):
        """Test error handling for wrong server identifier."""
        result = await plugin.execute('wrong_server', 'some_tool', {})

        assert result["status"] == "error"
        assert "Unknown server" in result["error"]

    def test_plugin_docstrings_present(self, plugin):
        """Test that key methods have comprehensive docstrings."""
        # Check that critical methods have docstrings
        assert plugin.leann_build_index.__doc__ is not None
        assert len(plugin.leann_build_index.__doc__) > 50

        assert plugin.leann_search.__doc__ is not None
        assert len(plugin.leann_search.__doc__) > 50

        assert plugin.analyze_codebase_intelligence.__doc__ is not None
        assert "self-diagnosis" in plugin.analyze_codebase_intelligence.__doc__

        assert plugin.execute.__doc__ is not None
        assert "MCP-compatible interface" in plugin.execute.__doc__

    def test_plugin_properties(self, plugin):
        """Test that new properties work correctly."""
        # Test is_available property
        assert isinstance(plugin.is_available, bool)
        assert plugin.is_available == plugin.available

        # Test preferred_backend property
        backend = plugin.preferred_backend
        assert backend in ["wsl", "windows", "none"]

    def test_custom_exceptions(self):
        """Test that custom exception classes are properly defined."""
        from src.plugins.leann_plugin import (
            LeannPluginError,
            LeannBackendNotAvailableError,
            LeannCommandTimeoutError,
            LeannCommandFailedError,
            CodebaseAnalysisError
        )

        # Test that exceptions can be instantiated
        base_error = LeannPluginError("Test message")
        assert str(base_error) == "Test message"

        backend_error = LeannBackendNotAvailableError("Backend unavailable")
        assert isinstance(backend_error, LeannPluginError)

        timeout_error = LeannCommandTimeoutError("Command timed out")
        assert isinstance(timeout_error, LeannPluginError)

        failed_error = LeannCommandFailedError("Command failed")
        assert isinstance(failed_error, LeannPluginError)

        analysis_error = CodebaseAnalysisError("Analysis failed")
        assert isinstance(analysis_error, LeannPluginError)

    def test_cached_properties(self, plugin):
        """Test that cached properties work and cache properly."""
        # Test version info caching (may be None in test environment)
        version_info = plugin.leann_version_info
        assert version_info is None or isinstance(version_info, dict)

        # Call again to test caching
        version_info2 = plugin.leann_version_info
        assert version_info2 is version_info  # Should be same cached object

        # Test backend caching
        backends = plugin.supported_backends
        assert isinstance(backends, list)
        assert all(isinstance(b, str) for b in backends)

        # Test caching again
        backends2 = plugin.supported_backends
        assert backends2 is backends  # Should be same cached object

    @pytest.mark.asyncio
    async def test_analysis_orchestrator_delegation(self, plugin):
        """Ensure plugin methods delegate to the analysis orchestrator."""
        plugin.analysis_orchestrator._analyze_project_structure = AsyncMock(return_value={'status': 'ok'})

        result = await plugin._analyze_project_structure()

        assert result == {'status': 'ok'}
        plugin.analysis_orchestrator._analyze_project_structure.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_index_service_delegation(self, plugin):
        """Ensure plugin index operations delegate to the service wrapper."""
        with patch.object(plugin.index_service, 'build_index', new_callable=AsyncMock) as mock_build:
            mock_build.return_value = {'status': 'success'}

            result = await plugin.leann_build_index('demo-index', ['doc.txt'])

        assert result == {'status': 'success'}
        mock_build.assert_awaited_once_with('demo-index', ['doc.txt'])

    def test_service_layer_exposed(self, plugin):
        """The plugin should expose the new service objects and drop old helpers."""
        assert isinstance(plugin.index_service, LeannIndexService)
        assert isinstance(plugin.analysis_orchestrator, LeannAnalysisOrchestrator)
        assert not hasattr(plugin, '_collect_files_with_limits')
        assert not hasattr(plugin, '_process_files_for_metrics')

if __name__ == "__main__":
    pytest.main([__file__])
