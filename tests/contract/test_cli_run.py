import pytest
from typer.testing import CliRunner
from src.agent.cli import cli_app
from unittest.mock import patch

runner = CliRunner()

def test_run_command_interactive():
    """Contract test for 'run' command: Asserts interactive mode starts without errors."""
    # Mock the Agent.run_sync method to avoid actual execution
    with patch('src.agent.cli.Agent') as mock_agent_class:
        mock_agent = mock_agent_class.return_value
        mock_agent.run_sync.return_value = None

        result = runner.invoke(cli_app, ["run"])
        assert result.exit_code == 0
        mock_agent_class.assert_called_once()
        mock_agent.run_sync.assert_called_once()

def test_run_command_with_api_error():
    """Test run command handles API initialization errors gracefully."""
    with patch('src.agent.cli.Agent') as mock_agent_class:
        mock_agent_class.side_effect = ValueError("Missing API key")

        result = runner.invoke(cli_app, ["run"])
        assert result.exit_code == 1  # Should fail with API error
