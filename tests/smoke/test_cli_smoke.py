from typer.testing import CliRunner

from src.agent.cli import cli_app


class _DummyLoader:
    def __init__(self) -> None:
        self.added = None

    def add_tool(self, tool_data):
        self.added = tool_data
        return True


def test_cli_add_tool_smoke(monkeypatch):
    loader = _DummyLoader()
    monkeypatch.setattr("src.agent.cli.MCPLoader", lambda: loader)
    runner = CliRunner()
    result = runner.invoke(
        cli_app,
        [
            "add-tool",
            "--name",
            "demo-tool",
            "--server",
            "filesystem",
            "--tool-name",
            "read_file",
        ],
    )
    assert result.exit_code == 0
    assert "added successfully" in result.stdout.lower()
    assert loader.added["name"] == "demo-tool"
