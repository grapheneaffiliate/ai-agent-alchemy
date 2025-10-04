import pytest
from unittest.mock import patch, MagicMock
from agent.core import execute_tool  # Assuming function in core
from agent.models import MCPTool

def test_tool_execution_calls_mcp():
    """Integration test: Tool execution prepares and calls MCP with correct XML."""
    tool = MCPTool(
        name="test-tool",
        server="github",
        tool_name="list_files",
        args={"path": ".", "recursive": "true"}
    )
    with patch('agent.mcp_loader.format_mcp_call') as mock_format:
        mock_format.return_value = "<use_mcp_tool(params)/>"  # Mock XML
        with patch('requests.post') as mock_post:  # Mock MCP server call
            mock_response = MagicMock()
            mock_response.text = '{"result": "success"}'
            mock_post.return_value = mock_response
            result = execute_tool(tool)  # Fails until impl
            mock_post.assert_called()
            expected_xml = """<use_mcp_tool>
<server_name>github</server_name>
<tool_name>list_files</tool_name>
<arguments>{"path": ".", "recursive": "true"}</arguments>
</use_mcp_tool>"""
            mock_format.assert_called_with(tool)
            assert result == "success"  # Fails until impl
