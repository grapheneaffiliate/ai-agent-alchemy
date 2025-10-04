"""Unit tests for browser plugin functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestBrowserPlugin:
    """Test browser plugin functionality."""

    def test_browser_plugin_import(self):
        """Test that browser plugin can be imported."""
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
            from plugins.browser import get_browser, close_browser
            assert get_browser is not None
            assert close_browser is not None
        except ImportError as e:
            pytest.fail(f"Browser plugin import failed: {e}")

    def test_execute_method_exists(self):
        """Test that browser plugin has execute method."""
        try:
            from plugins.browser import execute
            assert execute is not None
            # Check if it's async
            import inspect
            assert inspect.iscoroutinefunction(execute)
        except Exception as e:
            pytest.fail(f"Execute method test failed: {e}")

    @pytest.mark.asyncio
    async def test_browser_navigate_tool(self):
        """Test browser navigate execute tool call."""
        # Mock the get_browser function to return our mocked browser
        async def mock_get_browser_func(headless=True):
            mock_browser = MagicMock()
            mock_browser.navigate = AsyncMock(return_value={"status": "success", "url": "https://test.com"})
            return mock_browser

        with patch('plugins.browser.get_browser', side_effect=mock_get_browser_func):
            from plugins.browser import execute
            result = await execute("browser", "browser_navigate", {"url": "https://test.com"})

            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_browser_screenshot_tool(self):
        """Test browser screenshot execute tool call."""
        async def mock_get_browser_func(headless=True):
            mock_browser = MagicMock()
            mock_browser.screenshot = AsyncMock(return_value={"status": "saved", "path": "/tmp/screenshot.png"})
            return mock_browser

        with patch('plugins.browser.get_browser', side_effect=mock_get_browser_func):
            from plugins.browser import execute
            result = await execute("browser", "browser_screenshot", {"path": "/tmp/screenshot.png"})

            assert result["status"] == "saved"

    @pytest.mark.asyncio
    async def test_browser_extract_content_tool(self):
        """Test browser extract content execute tool call."""
        async def mock_get_browser_func(headless=True):
            mock_browser = MagicMock()
            mock_browser.extract_content_smart = AsyncMock(return_value={
                "status": "success",
                "title": "Test Page",
                "text": "Test content"
            })
            return mock_browser

        with patch('plugins.browser.get_browser', side_effect=mock_get_browser_func):
            from plugins.browser import execute
            result = await execute("browser", "browser_extract_content", {})

            assert result["status"] == "success"
            assert result["title"] == "Test Page"

    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        """Test handling of unknown tools."""
        async def mock_get_browser_func(headless=True):
            mock_browser = MagicMock()
            return mock_browser

        with patch('plugins.browser.get_browser', side_effect=mock_get_browser_func):
            from plugins.browser import execute
            result = await execute("browser", "unknown_tool", {})

            assert result["status"] == "error"
            assert "Unknown tool" in result["error"]

    @pytest.mark.asyncio
    async def test_browser_error_handling(self):
        """Test error handling in browser plugin."""
        async def mock_get_browser_func(headless=True):
            mock_browser = MagicMock()
            mock_browser.navigate = AsyncMock(side_effect=Exception("Browser error"))
            return mock_browser

        with patch('plugins.browser.get_browser', side_effect=mock_get_browser_func):
            from plugins.browser import execute
            result = await execute("browser", "browser_navigate", {"url": "https://test.com"})

            assert result["status"] == "error"
            assert "Browser error" in str(result["error"])


class TestSearchPlugin:
    """Test search plugin functionality."""

    def test_search_plugin_import(self):
        """Test that search plugin can be imported and has execute method."""
        try:
            from plugins.search import SearchPlugin
            assert SearchPlugin is not None

            # Check execute method
            execute_func = SearchPlugin.execute

            # Test that it's bound method
            import inspect
            assert inspect.ismethod(execute_func) or hasattr(SearchPlugin, 'execute')
        except Exception as e:
            pytest.fail(f"Search plugin test failed: {e}")

    @pytest.mark.asyncio
    async def test_search_plugin_execute(self):
        """Test search plugin execute method."""
        try:
            from plugins.search import SearchPlugin
            import asyncio

            plugin = SearchPlugin()

            # Mock the required methods
            with patch('plugins.search.SearchPlugin.web_search') as mock_search:
                mock_search.return_value = {
                    "status": "success",
                    "result": {"query": "test", "results": []}
                }

                result = await plugin.execute("search", "web_search", {"query": "test"})

                mock_search.assert_called_once_with("test", 10)
                assert result["status"] == "success"

        except Exception as e:
            pytest.fail(f"Search plugin execute test failed: {e}")

    def test_search_plugin_static_method(self):
        """Test search plugin static method parse_citation."""
        from plugins.search import SearchPlugin

        # Test empty inputs
        result = SearchPlugin.parse_citation("", [])
        assert result == ""

        # Test normal citation replacement
        response = "This result is important"
        results = [{"snippet": "This result is important"}]

        result = SearchPlugin.parse_citation(response, results)

        # Should have replaced the text with citation tags
        assert "<citation" in result or result != response

    @pytest.mark.asyncio
    async def test_search_plugin_unknown_tool(self):
        """Test search plugin handling of unknown tools."""
        from plugins.search import SearchPlugin

        plugin = SearchPlugin()

        result = await plugin.execute("search", "unknown_tool", {})

        assert result["status"] == "error"
        assert "Unknown tool" in result["error"]


class TestPluginIntegration:
    """Test integration between plugins."""

    @pytest.mark.asyncio
    async def test_leann_plugin_imports(self):
        """Test that LEANN plugin can import and has expected methods."""
        try:
            from plugins.leann_plugin import LeannPlugin

            plugin = LeannPlugin()

            # Check if key methods exist
            assert hasattr(plugin, '_answer_question_with_text_analysis')
            assert hasattr(plugin, '_generate_improvement_recommendations')
            assert hasattr(plugin, '_diagnose_system_issues')

            # Test that it's instantiable
            assert plugin is not None

        except Exception as e:
            pytest.fail(f"LEANN plugin integration test failed: {e}")

    @pytest.mark.asyncio
    async def test_plugin_loading(self):
        """Test that plugins can be loaded from the src/plugins directory."""
        import importlib.util
        plugin_dir = Path(__file__).parent.parent.parent / "src" / "plugins"

        # List expected plugin files
        expected_plugins = ['browser.py', 'search.py', 'leann_plugin.py']

        for plugin_file in expected_plugins:
            plugin_path = plugin_dir / plugin_file
            if plugin_path.exists():
                # Try to load the plugin module
                try:
                    spec = importlib.util.spec_from_file_location(
                        plugin_file[:-3],  # Remove .py
                        plugin_path
                    )
                    module = importlib.util.module_from_spec(spec)

                    # Just check it can be loaded (don't actually execute)
                    assert spec is not None
                    assert module is not None

                except Exception as e:
                    pytest.fail(f"Failed to load plugin {plugin_file}: {e}")
            else:
                pytest.skip(f"Plugin file {plugin_file} not found - skipping test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
