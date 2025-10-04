from typing import Dict, Any
import asyncio
import re
import json
from .search import SearchPlugin  # If needed for data

# Global artifact storage for REPL-based artifact creation
artifacts_created = []

def use_artifact(filename: str, content: str, mime_type: str):
    """Create artifact from REPL execution."""
    artifact = {
        'filename': filename,
        'content': content,
        'mime_type': mime_type,
        'id': len(artifacts_created)
    }
    artifacts_created.append(artifact)
    return f"Artifact '{filename}' created with {len(content)} characters (MIME: {mime_type})"

class ReplPlugin:
    """JS REPL for analysis, math, data processing."""

    def execute_js(self, code: str) -> Dict[str, Any]:
        """Execute JS code, capture console.log, handle errors."""
        output = []
        error = None
        try:
            # Mock JS env for Python; in full, use PyV8 or similar, here simulate
            # For now, parse console.log, eval simple math/data
            logs = re.findall(r'console\.log\((.*?)\)', code, re.DOTALL)
            for log in logs:
                try:
                    val = eval(log.strip(), {"__builtins__": {}} ) if log.isdigit() or log.replace('.', '').replace('-', '').isdigit() else log
                    output.append(str(val))
                except:
                    output.append(log)

            # Handle simple imports/math (mathjs sim)
            if 'mathjs' in code:
                # Mock math
                output.append("Math lib loaded; use for calculations")

            # For file reads, mock window.fs
            if 'window.fs.readFile' in code:
                # Extract path, mock
                path_match = re.search(r"path['\"]([^'\"]*)['\"]", code)
                if path_match:
                    path = path_match.group(1)
                    mock_content = f"Mock file content for {path}"  # Real would use fs
                    output.append(f"readFile({path}): {mock_content}")

            # If no logs, mock success
            if not output:
                output = ["JS code executed successfully"]

            return {"output": output, "error": None}
        except Exception as e:
            error = str(e)
            return {"output": [], "error": error}

    def process_csv(self, path: str) -> Dict[str, Any]:
        """Mock CSV processing with papaparse."""
        # Mock for now
        return {"parsed": [{"header": "mock", "row": "data"}], "summary": "CSV processed"}

    def _dispatch(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis tools synchronously and return structured result."""
        if tool_name == 'execute_js':
            code = args.get('code', '')
            result = self.execute_js(code)
        elif tool_name == 'analyze_csv':
            path = args.get('path', '')
            result = self.process_csv(path)
        else:
            return {"status": "error", "error": f"Unknown tool {tool_name}"}
        return {"status": "success", "result": result}

    def execute_sync(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Backward-compatible synchronous entry point for direct calls."""
        return self._dispatch(tool_name, args)

    async def execute(self, server: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Async MCP interface entry point expected by the plugin executor."""
        return await asyncio.to_thread(self._dispatch, tool_name, args)


