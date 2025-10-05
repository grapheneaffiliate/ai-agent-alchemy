"""Unit tests for LEANN plugin's self-diagnostic capabilities."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from plugins.leann_plugin import LeannPlugin


class TestSelfDiagnostic:
    """Test the agent's self-diagnostic capabilities."""
    
    @pytest.fixture
    def plugin(self):
        """Create LeannPlugin instance."""
        return LeannPlugin()
    
    @pytest.fixture
    def mock_base_path(self, tmp_path):
        """Create mock codebase structure."""
        # Create directory structure
        (tmp_path / "src" / "plugins").mkdir(parents=True)
        (tmp_path / "src" / "agent").mkdir(parents=True)
        (tmp_path / "tests").mkdir()
        
        return tmp_path
    
    def test_extract_plugin_name_crawl4ai(self, plugin):
        """Test extracting crawl4ai plugin name from question."""
        question = "what is the crawl4ai plugin?"
        result = plugin.intelligence.question_router._extract_plugin_name(question)
        assert result == "crawl4ai_plugin"

    def test_extract_plugin_name_browser(self, plugin):
        """Test extracting browser plugin name."""
        question = "tell me about the browser plugin"
        result = plugin.intelligence.question_router._extract_plugin_name(question)
        assert result == "browser"

    def test_extract_plugin_name_none(self, plugin):
        """Test when no plugin name in question."""
        question = "what is the weather today?"
        result = plugin.intelligence.question_router._extract_plugin_name(question)
        assert result is None
    
    def test_is_capability_question_true(self, plugin):
        """Test capability question detection - positive."""
        assert plugin.intelligence.question_router._is_capability_question("can you add plugins?") == True
        assert plugin.intelligence.question_router._is_capability_question("are you able to create tools?") == True
        assert plugin.intelligence.question_router._is_capability_question("could you extend yourself?") == True

    def test_is_capability_question_false(self, plugin):
        """Test capability question detection - negative."""
        assert plugin.intelligence.question_router._is_capability_question("what is the browser plugin?") == False
        assert plugin.intelligence.question_router._is_capability_question("assess your codebase") == False
    
    def test_diagnose_web_plugins_no_execute(self, plugin, mock_base_path):
        """Test diagnosing browser plugin missing execute method."""
        # Create browser.py without execute()
        browser_file = mock_base_path / "src" / "plugins" / "browser.py"
        browser_file.write_text("""
class BrowserPlugin:
    async def navigate(self, url):
        pass
""")

        result = plugin._diagnose_web_plugins(mock_base_path)

        assert "Browser plugin may not expose an async execute() entry point" in result
        assert "Issues Found" in result

    def test_diagnose_web_plugins_has_execute(self, plugin, mock_base_path):
        """Test diagnosing browser plugin WITH execute method."""
        # Create browser.py with execute()
        browser_file = mock_base_path / "src" / "plugins" / "browser.py"
        browser_file.write_text("""
from playwright.async_api import async_playwright

class BrowserPlugin:
    async def execute(self, server, tool_name, args):
        return {"status": "success"}
""")

        # Create search.py with execute()
        search_file = mock_base_path / "src" / "plugins" / "search.py"
        search_file.write_text("""
import httpx

class SearchPlugin:
    async def execute(self, server, tool_name, args):
        return {"status": "success"}
""")

        result = plugin._diagnose_web_plugins(mock_base_path)

        # Should report no issues since both files exist and have execute methods
        assert "Issues Found (0 total)" in result

    def test_verify_browser_fix_found(self, plugin, mock_base_path):
        """Test verification when execute() method is present."""
        # Create browser.py WITH execute()
        browser_file = mock_base_path / "src" / "plugins" / "browser.py"
        browser_file.write_text("""
async def execute(server, tool_name, args):
    return {"status": "success"}
""")

        result = plugin._verify_recent_fixes(mock_base_path, "verify browser fix")

        assert "Execute entry point detected" in result

    def test_verify_browser_fix_not_found(self, plugin, mock_base_path):
        """Test verification when execute() method is missing."""
        # Create browser.py WITHOUT execute()
        browser_file = mock_base_path / "src" / "plugins" / "browser.py"
        browser_file.write_text("""
class BrowserPlugin:
    async def navigate(self, url):
        pass
""")

        result = plugin._verify_recent_fixes(mock_base_path, "verify browser fix")

        assert "Execute entry point still missing" in result
    
    def test_diagnose_general_issues_healthy(self, plugin, mock_base_path):
        """Test general diagnostic with healthy system."""
        # Create required files
        (mock_base_path / "src" / "agent" / "core.py").touch()
        (mock_base_path / "src" / "agent" / "react_loop.py").touch()
        (mock_base_path / "src" / "agent" / "plugin_executor.py").touch()
        (mock_base_path / "tests").mkdir(exist_ok=True)
        (mock_base_path / "docs").mkdir(exist_ok=True)
        
        result = plugin._diagnose_general_issues(mock_base_path)

        assert "System Diagnostic Checklist" in result
        assert "tools exist in config/mcp_tools.json" in result
    
    def test_explain_specific_plugin_exists(self, plugin, mock_base_path):
        """Test explaining a specific plugin that exists."""
        # Create a sample plugin
        plugin_file = mock_base_path / "src" / "plugins" / "test_plugin.py"
        plugin_file.write_text('''"""Test plugin for testing."""

class TestPlugin:
    async def execute(self, server, tool_name, args):
        """Execute test commands."""
        return {"status": "success"}
    
    async def test_method(self):
        """Test method."""
        pass
''')
        
        result = plugin.intelligence.summarizer.plugin_details("test_plugin", mock_base_path)
        
        assert "Plugin: test_plugin" in result
        assert "test_method" in result
        assert "execute" in result
    
    def test_explain_specific_plugin_not_found(self, plugin, mock_base_path):
        """Test explaining a plugin that doesn't exist."""
        result = plugin.intelligence.summarizer.plugin_details("nonexistent_plugin")

        assert "not found" in result.lower()


class TestCodebaseAnalysis:
    """Test codebase analysis features."""
    
    @pytest.fixture
    def plugin(self):
        """Create LeannPlugin instance."""
        return LeannPlugin()
    
    @pytest.fixture
    def mock_codebase(self, tmp_path):
        """Create realistic mock codebase."""
        # Create Python files with various patterns
        src = tmp_path / "src"
        src.mkdir()
        
        # File with no docstrings
        (src / "no_docs.py").write_text("""
def function_without_docs():
    pass

class ClassWithoutDocs:
    pass
""")
        
        # File with docstrings
        (src / "with_docs.py").write_text('''
"""Module with documentation."""

def function_with_docs():
    """This function has docs."""
    pass

class ClassWithDocs:
    """This class has docs."""
    pass
''')
        
        # File with type hints
        (src / "typed.py").write_text("""
def typed_function(x: int) -> str:
    return str(x)
""")
        
        return tmp_path
    
    def test_answer_visibility_question(self, plugin, mock_codebase):
        """Test visibility question answering."""
        result = plugin._answer_visibility_question(mock_codebase)
        
        assert "Yes, I can see my codebase" in result
        assert "Python files" in result
    
    def test_generate_codebase_overview(self, plugin, mock_codebase):
        """Test codebase overview generation."""
        result = plugin._generate_codebase_overview(mock_codebase)
        
        assert "Codebase Overview" in result
        assert "Structure" in result
        assert "Technology Stack" in result


class TestQuestionRouting:
    """Test smart question routing."""
    
    @pytest.fixture
    def plugin(self):
        return LeannPlugin()
    
    @pytest.fixture  
    def mock_base(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        return tmp_path
    
    @pytest.mark.asyncio
    async def test_routing_visibility_question(self, plugin, mock_base):
        """Test routing 'can you see' questions."""
        result = await plugin._answer_question_with_text_analysis("test", "can you see your codebase?")
        
        assert result["status"] == "success"
        assert "can see my codebase" in result["analysis"]["overview"].lower()
    
    @pytest.mark.asyncio
    async def test_routing_capability_question(self, plugin, mock_base):
        """Test routing 'can you' capability questions."""
        result = await plugin._answer_question_with_text_analysis("test", "can you add plugins?")

        assert result["status"] == "success"
        assert "agent is fully capable" in result["analysis"]["overview"].lower()
    
    @pytest.mark.asyncio
    async def test_routing_diagnostic_question(self, plugin, mock_base):
        """Test routing diagnostic questions."""
        result = await plugin._answer_question_with_text_analysis("test", "diagnose browser plugin")
        
        assert result["status"] == "success"
        assert "diagnostic" in result["analysis"]["overview"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
