from fastapi.testclient import TestClient

from src.agent import server


class _DummyAgent:
    async def generate_response(self, prompt: str, context: str = "") -> str:
        return "assistant response"


class _DummyExecutor:
    async def execute(self, server_name: str, tool_name: str, args):
        return {"status": "success", "result": {}}


async def _noop_execute_tools(prompt, agent, executor):
    return "", None


def test_health_endpoint_smoke():
    client = TestClient(server.app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"


def test_chat_completion_smoke(monkeypatch):
    client = TestClient(server.app)
    monkeypatch.setattr(server, "get_agent", lambda: _DummyAgent())
    monkeypatch.setattr(server, "get_plugin_executor", lambda: _DummyExecutor())
    monkeypatch.setattr(server, "execute_tools_if_needed", _noop_execute_tools)

    body = {
        "model": "mcp-agent",
        "messages": [{"role": "user", "content": "hello"}],
        "stream": False,
    }

    response = client.post("/v1/chat/completions", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["choices"][0]["message"]["content"] == "assistant response"
