#!/usr/bin/env python3
"""Manual test script for CLI functionality."""

from typer.testing import CliRunner
from src.agent.cli import cli_app
import os
from dotenv import load_dotenv

def test_cli_basic():
    """Test basic CLI functionality."""
    runner = CliRunner()

    # Test help
    result = runner.invoke(cli_app, ['--help'])
    print("=== CLI Help Test ===")
    print(f"Exit code: {result.exit_code}")
    print("Output:")
    print(result.stdout)
    print()

    # Test run command help
    result = runner.invoke(cli_app, ['run', '--help'])
    print("=== Run Command Help ===")
    print(f"Exit code: {result.exit_code}")
    print("Output:")
    print(result.stdout)
    print()

    # Test add-tool command help
    result = runner.invoke(cli_app, ['add-tool', '--help'])
    print("=== Add-Tool Command Help ===")
    print(f"Exit code: {result.exit_code}")
    print("Output:")
    print(result.stdout)
    print()

    # Test add-tool with mock
    try:
        from unittest.mock import patch
        with patch('src.agent.cli.MCPLoader') as mock_loader_class:
            mock_loader = mock_loader_class.return_value
            mock_loader.add_tool.return_value = True

            result = runner.invoke(cli_app, [
                'add-tool',
                'test-tool',
                '--server', 'local',
                '--tool-name', 'read_file'
            ])
            print("=== Add-Tool Command Test ===")
            print(f"Exit code: {result.exit_code}")
            print("Output:")
            print(result.stdout)
            print()
    except Exception as e:
        print(f"Error testing add-tool: {e}")

def test_api_configuration():
    """Test API configuration with OpenRouter settings."""
    print("=== API Configuration Test ===")

    # Load environment variables
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("MODEL", "x-ai/grok-code-fast-1")

    print(f"API Key: {'Set' if api_key else 'Not set'}")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print()

    if api_key and base_url:
        print("✅ OpenRouter configuration looks good!")
        print(f"   - Using model: {model}")
        print(f"   - Base URL: {base_url}")
    else:
        print("❌ Missing OpenRouter configuration in .env file")

if __name__ == "__main__":
    test_cli_basic()
    test_api_configuration()
