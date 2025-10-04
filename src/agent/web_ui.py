"""Custom Web UI for MCP AI Agent - Built for perfect compatibility."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import re
from typing import Optional, List, Tuple
from pathlib import Path
from .models import Session
from .plugin_executor import PluginExecutor
from .api import AgentAPI
from .artifacts import ArtifactGenerator
from .mcp_loader import MCPLoader

app = FastAPI(title="MCP AI Agent Web UI")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent_instance: Optional[AgentAPI] = None
plugin_executor: Optional[PluginExecutor] = None

def get_agent() -> AgentAPI:
    """Get or create agent instance with MCP tools loaded."""
    global agent_instance, plugin_executor
    if agent_instance is None:
        # Load MCP tools from config
        loader = MCPLoader()
        tools = loader.load_tools()
        
        # Convert to dict format for API
        mcp_tools = [tool.model_dump() for tool in tools]
        
        # Create session and agent with system prompt
        session = Session(id="webui", history=[])
        agent_instance = AgentAPI(session, mcp_tools=mcp_tools)
        plugin_executor = PluginExecutor()
        
        print(f"✓ Loaded {len(mcp_tools)} MCP tools for web UI")
    return agent_instance

@app.get("/")
async def get_ui():
    """Serve the custom web UI."""
    ui_path = Path(__file__).parent.parent.parent / "ui.html"
    return FileResponse(ui_path)

@app.post("/tts")
async def text_to_speech(request: dict):
    """Generate speech from text using Kokoro TTS."""
    try:
        # Import here to avoid module-level import issues
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from plugins.kokoro_tts import get_tts
        
        text = request.get('text', '')
        voice = request.get('voice', 'af_sky')
        
        if not text:
            return {"error": "No text provided"}
        
        tts = get_tts("http://localhost:8880")
        audio_bytes = await tts.generate_speech(text, voice)
        
        if audio_bytes:
            # Return base64 encoded audio
            import base64
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            return {
                "audio": audio_b64,
                "format": "mp3"
            }
        else:
            return {"error": "TTS generation failed"}
            
    except Exception as e:
        return {"error": str(e)}

@app.get("/tts/health")
async def tts_health():
    """Check if TTS service is available."""
    # Import here to avoid module-level import issues
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from plugins.kokoro_tts import get_tts
    
    tts = get_tts("http://localhost:8880")
    is_healthy = await tts.health_check()
    return {"available": is_healthy}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat with ReAct loop."""
    await websocket.accept()
    agent = get_agent()
    global plugin_executor
    
    # Import ReAct loop
    from .react_loop import execute_react_loop
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data['type'] == 'message':
                user_message = message_data['content']
                
                print(f"\n{'='*60}")
                print(f"USER MESSAGE: {user_message}")
                print(f"{'='*60}")
                print("✨ Delegating to autonomous ReAct loop...")
                
                # Execute ReAct loop for FULL autonomous tool usage
                # ReAct loop will decide which tools to use based on user request
                response, artifact_html = await execute_react_loop(
                    user_message,
                    agent,
                    plugin_executor,
                    max_iterations=5
                )
                
                # Extract artifacts from response
                # Check for Claude-style artifact format first (from system prompt)
                print(f"🔍 DEBUG: Received artifact_html: {artifact_html is not None} (length: {len(artifact_html) if artifact_html else 0})")
                print(f"🔍 DEBUG: Analyzing response for artifacts (length: {len(response)})")
                print(f"🔍 DEBUG: Response preview: {response[:500]}...")

                # Only do additional artifact detection if ReAct loop didn't generate one
                if not artifact_html:
                    # Pattern 1: Claude-style artifact with MIME type (HTML)
                    if 'application/vnd.ant.html' in response or 'text/html' in response:
                        print("🔍 DEBUG: Found Claude-style artifact marker")
                        # Look for HTML content after the MIME type declaration

                        # Find MIME type line
                        mime_pattern = r'(application/vnd\.ant\.html|text/html)\s*\n'
                        mime_match = re.search(mime_pattern, response)

                        if mime_match:
                            content_start = mime_match.end()

                            # Look for <!DOCTYPE html> or <html
                            html_match = re.search(r'<!DOCTYPE html>|<html', response[content_start:], re.IGNORECASE)
                            if html_match:
                                html_start = content_start + html_match.start()

                                # Find the end - look for closing </html> tag
                                html_end_match = re.search(r'</html>\s*', response[html_start:], re.IGNORECASE)
                                if html_end_match:
                                    html_end = html_start + html_end_match.end()
                                    artifact_html = response[html_start:html_end].strip()
                                    print(f"✅ Extracted Claude-style HTML artifact (length: {len(artifact_html)})")

                                    # Remove artifact from response
                                    response = response[:mime_match.start()] + '\n✅ HTML artifact generated - see right panel! 🎨\n' + response[html_end:]

                    # Pattern 2: Traditional ```html code blocks (fallback)
                    if not artifact_html and '```html' in response:
                        print("🔍 DEBUG: Found ```html marker")
                        # Extract everything between ```html and the next ```
                        start_marker = response.find('```html')
                        if start_marker != -1:
                            content_start = start_marker + len('```html')

                            # Look for closing ```
                            end_marker = response.find('```', content_start)
                            if end_marker == -1:
                                end_marker = len(response)

                            artifact_html = response[content_start:end_marker].strip()
                            print(f"✅ Extracted HTML from code block (length: {len(artifact_html)})")

                            # Replace in response
                            response = response[:start_marker] + '\n✅ HTML artifact generated - see right panel! 🎨\n' + response[end_marker+3 if end_marker < len(response)-3 else end_marker:]

                    # Pattern 3: Markdown artifacts (convert to HTML for display)
                    if not artifact_html and ('text/markdown' in response or 'application/vnd.ant.code' in response):
                        print("🔍 DEBUG: Found Markdown artifact marker")
                        # Look for markdown content after MIME type or in code block
                        if 'text/markdown' in response:
                            mime_match = re.search(r'text/markdown\s*\n', response)
                            if mime_match:
                                content_start = mime_match.end()
                                # Find next # heading or take rest of content
                                markdown_content = response[content_start:].strip()
                                # Convert markdown to simple HTML
                                artifact_html = f"""
                                <!DOCTYPE html>
                                <html>
                                <head>
                                    <style>
                                        body {{ font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; }}
                                        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
                                        h2 {{ color: #555; margin-top: 20px; }}
                                        ul {{ margin-left: 20px; }}
                                        li {{ margin-bottom: 8px; }}
                                    </style>
                                </head>
                                <body>
                                    <pre style="white-space: pre-wrap; font-family: inherit;">{markdown_content}</pre>
                                </body>
                                </html>
                                """
                                print(f"✅ Converted Markdown artifact to HTML (length: {len(artifact_html)})")
                                response = response[:mime_match.start()] + '\n✅ Markdown artifact generated - see right panel! 📝\n'
                
                response = ArtifactGenerator.format_text_response(response)
                
                # Send response
                await websocket.send_json({
                    "type": "message",
                    "content": response
                })
                
                # Send artifact if generated
                if artifact_html:
                    await websocket.send_json({
                        "type": "artifact",
                        "content": artifact_html
                    })
                
    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  MCP AI Agent - Custom Web UI                            ║
    ╚══════════════════════════════════════════════════════════╝
    
    🚀 Server starting on http://localhost:9000
    🌐 Open your browser to: http://localhost:9000
    
    Features:
    ✓ HTML artifacts (split-panel view)
    ✓ MermaidJS diagrams (auto-rendered inline)
    ✓ Python code execution (Pyodide with Run buttons)
    ✓ Proper markdown rendering
    ✓ Syntax highlighting
    ✓ Real-time chat
    
    Try these:
    • "Show me AI news" → HTML artifact in right panel
    • "Create a flowchart for login" → Mermaid diagram inline
    • "Write Python to analyze data" → Code with Run button
    
    Press Ctrl+C to stop
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="info")
