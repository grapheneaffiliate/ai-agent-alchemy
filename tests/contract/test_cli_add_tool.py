import pytest
from typer.testing import CliRunner
from src.agent.cli import cli_app
import json
from unittest.mock import patch, MagicMock

runner = CliRunner()

def test_add_tool_command_success():
    """Contract test for 'add-tool' command: Asserts config update without errors."""
    tool_args = '--name "test-tool" --server "local" --tool-name "read_file" --args-schema "{}"'

    # Mock the MCPLoader to avoid file system operations
    with patch('src.agent.cli.MCPLoader') as mock_loader_class:
        mock_loader = mock_loader_class.return_value
        mock_loader.add_tool.return_value = True

        result = runner.invoke(cli_app, ["add-tool", *tool_args.split()])
        assert result.exit_code == 0
        assert "Tool 'test-tool' added successfully." in result.stdout
        mock_loader_class.assert_called_once()
        mock_loader.add_tool.assert_called_once()



def test_add_tool_command_without_schema():
    """Test add-tool command works without args-schema parameter."""
    tool_args = '--name "test-tool" --server "local" --tool-name "read_file"'

    with patch('src.agent.cli.MCPLoader') as mock_loader_class:
        mock_loader = mock_loader_class.return_value
        mock_loader.add_tool.return_value = True

        result = runner.invoke(cli_app, ["add-tool", *tool_args.split()])
        assert result.exit_code == 0
        assert "Tool 'test-tool' added successfully." in result.stdout
