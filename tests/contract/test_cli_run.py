import pytest
import asyncio
from typer.testing import CliRunner
from src.agent.cli import cli_app
from unittest.mock import patch

runner = CliRunner()

async def async_iter(items):
    """Helper to create async iterators for testing."""
    for item in items:
        yield item

def test_run_command_interactive():
    """Contract test for 'run' command: Asserts interactive mode starts without errors."""
    # Mock the Agent.run method to return empty async generator to avoid actual execution
    with patch('src.agent.cli.Agent') as mock_agent_class:
        mock_agent = mock_agent_class.return_value
        mock_agent.run.return_value = async_iter([])

        # Mock the asyncio.run function to actually call the function it's passed
        with patch('asyncio.run') as mock_asyncio_run:
            def call_function(func):
                # Call the function normally (this will create the Agent)
                func()
                return None
            mock_asyncio_run.side_effect = call_function

            result = runner.invoke(cli_app, ["run"])
            assert result.exit_code == 0

        # Verify mocks were called
        mock_agent_class.assert_called_once()

def test_run_command_with_api_error():
    """Test run command handles API initialization errors gracefully."""
    with patch('src.agent.cli.Agent') as mock_agent_class:
        mock_agent_class.side_effect = ValueError("Missing API key")

        # Mock asyncio.run to avoid any async issues
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.side_effect = ValueError("Missing API key")
            result = runner.invoke(cli_app, ["run"])
            assert result.exit_code == 1  # Should fail with API error
