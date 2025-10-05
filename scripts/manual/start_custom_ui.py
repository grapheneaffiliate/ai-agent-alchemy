"""Launch custom web UI for MCP AI Agent."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

if __name__ == "__main__":
    import uvicorn
    from agent.web_ui import app

    print("""
>>> MCP AI Agent - Custom Web UI <<<

Server starting on http://localhost:9000
Open your browser to: http://localhost:9000

Features:
- HTML artifacts (split-panel view)
- MermaidJS diagrams (auto-rendered inline)
- Python code execution (Pyodide with Run buttons)
- Proper markdown rendering
- Syntax highlighting
- Real-time chat

Try these:
- "Show me AI news" -> HTML artifact in right panel
- "Create a flowchart for login" -> Mermaid diagram inline
- "Write Python to analyze data" -> Code with Run button

Press Ctrl+C to stop
""")

    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="info")
