"""Entry point for MCP AI Agent server with modular API components."""

import os
from dotenv import load_dotenv
import uvicorn

from .api import app, router

load_dotenv(override=True)

# Include API routes in the app
app.include_router(router)

if __name__ == "__main__":
    port = int(os.getenv("SERVER_PORT", "8000"))
    host = os.getenv("SERVER_HOST", "0.0.0.0")

    banner = (
        "==============================\n"
        "  MCP AI Agent API Server\n"
        "  OpenAI-compatible API for Open WebUI\n"
        "=============================="
    )
    print(banner)
    print(f"Server starting on http://{host}:{port}")
    print(f"API documentation: http://{host}:{port}/docs")
    print(f"OpenWebUI base URL: http://localhost:{port}/v1")
    print("Endpoints: POST /v1/chat/completions, GET /v1/models, GET /health")

    uvicorn.run(app, host=host, port=port)
