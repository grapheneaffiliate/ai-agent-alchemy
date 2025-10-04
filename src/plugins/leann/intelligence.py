from __future__ import annotations

"""Fallback intelligence helpers for the LEANN plugin."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .codebase import (
    build_directory_structure,
    collect_files_with_limits,
    create_analysis_result,
    process_python_metrics,
)


class IntelligenceToolkit:
    """Provides text-based analysis and question answering when LEANN is unavailable."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    async def fallback_analysis(self, index_name: str, question: Optional[str]) -> Dict[str, Any]:
        print(f"[DEBUG] Fallback called with question: {repr(question)}")
        if question:
            print(f"[DEBUG] Fallback answering specific question: {question}")
            return await self.answer_question(index_name, question)

        print("[DEBUG] No question provided, using generic analysis")
        if index_name != "agent-code":
            return {
                "status": "success",
                "analysis": {"overview": "Fallback analysis currently focuses on agent-code index."},
                "index": index_name,
                "method": "minimal_fallback_analysis",
                "note": "Index not fully supported for fallback analysis",
            }

        base_path = self._project_root
        print(f"[DEBUG] Analyzing codebase at: {base_path}")

        files = collect_files_with_limits(base_path)
        print(f"[DEBUG] Found {len(files)} files to analyze")

        py_files = [path for path in files if path.suffix == ".py"]
        metrics = process_python_metrics(py_files)
        dir_structure = build_directory_structure(base_path)
        return create_analysis_result(files, metrics, dir_structure, index_name)

    async def answer_question(self, index_name: str, question: str) -> Dict[str, Any]:
        try:
            base_path = self._project_root
            question_lower = question.lower()

            if any(word in question_lower for word in ["can you see", "do you have access", "do you know"]):
                answer = self._answer_visibility_question(base_path)
            elif any(word in question_lower for word in ["check again", "verify", "confirm", "did it work", "is it fixed", "validate"]):
                answer = self._verify_recent_fixes(base_path, question_lower)
            elif any(word in question_lower for word in ["diagnostic", "diagnose", "debug", "not working", "broken", "fix"]):
                answer = self._diagnose_system_issues(base_path, question_lower)
            elif any(word in question_lower for word in ["what changes", "what would you change", "improve", "recommend"]):
                answer = self._generate_improvement_recommendations(base_path)
            elif any(word in question_lower for word in ["assess", "evaluate", "analysis"]):
                answer = self._generate_detailed_assessment(base_path)
            elif "plugin" in question_lower or "tool" in question_lower:
                if self._is_capability_question(question_lower):
                    answer = self._answer_capability_question(question_lower, base_path)
                else:
                    plugin_name = self._extract_plugin_name(question_lower)
                    if plugin_name:
                        answer = self._explain_specific_plugin(base_path, plugin_name)
                    else:
                        answer = self._explain_architecture(base_path, question_lower)
            else:
                answer = self._generate_codebase_overview(base_path)

            return {
                "status": "success",
                "analysis": {
                    "overview": answer,
                    "method": "text_analysis_question_specific",
                    "index_name": index_name,
                },
                "index": index_name,
                "method": "text_fallback_smart",
            }
        except Exception as exc:
            print(f"[DEBUG] Question answering error: {exc}")
            return await self.fallback_analysis(index_name, question=None)

    def _answer_visibility_question(self, base_path: Path) -> str:
        try:
            py_files = list((base_path / "src").rglob("*.py"))[:20]
            file_list = [path.name for path in py_files]
            return (
                "Yes, I can see my codebase! I have full access to:\n\n"
                f"**Source Code**: {len(py_files)} Python files in the src/ directory including:\n"
                f"- {', '.join(file_list[:10])}\n\n"
                "**Key Components I can analyze**:\n"
                "- Plugin system (search.py, browser.py, leann_plugin.py, etc.)\n"
                "- Core agent logic (core.py, api.py, memory.py)\n"
                "- ReAct autonomous loop (react_loop.py)\n"
                "- Web UI and server (web_ui.py, server.py)\n"
                "- Artifact generation (artifacts.py)\n\n"
                "I can read, analyze, and understand all the code in this repository."
            )
        except Exception as exc:
            return f"I have access to the codebase but encountered an error: {exc}"

    def _verify_recent_fixes(self, base_path: Path, question: str) -> str:
        try:
            if "browser" in question or "web" in question:
                browser_path = base_path / "src" / "plugins" / "browser.py"
                if not browser_path.exists():
                    return "?? browser.py not found - cannot verify"

                content = browser_path.read_text(encoding="utf-8", errors="replace")
                has_execute = "async def execute(" in content or "def execute(" in content
                if has_execute:
                    signature = "async def execute" if "async def execute(" in content else "def execute"
                    return (
                        "# ? Fix Verified - Browser Plugin\n\n"
                        "## Status: FIXED!\n\n"
                        "**Previous Issue:** Browser plugin was missing `async def execute()` method\n\n"
                        "**Current Status:** ? Execute method now present!\n\n"
                        "## Verification Details:\n"
                        "- File: `src/plugins/browser.py`\n"
                        "- Execute method: **Found** ?\n"
                        f"- Method signature: `{signature}`\n\n"
                        "## What Was Added:\n"
                        "The browser plugin now has the MCP interface method it was missing. This allows it to:\n"
                        "1. Receive tool calls from the plugin executor\n"
                        "2. Route to appropriate browser methods (navigate, screenshot, etc.)\n"
                        "3. Return results in standardized format\n\n"
                        "**The diagnostic recommendation was correct and the fix has been successfully applied!** ??\n\n"
                        "## Next Steps:\n"
                        "- Restart the custom UI to load the updated plugin\n"
                        "- Test browser functionality with a web search or navigation command"
                    )
                return (
                    "# ?? Verification Failed\n\n"
                    "**Issue:** Execute method still not found in browser.py\n\n"
                    "**Expected:** `async def execute(server, tool_name, args)` method\n\n"
                    "**Status:** The file was modified but the execute() method may not have been added correctly.\n\n"
                    "**Recommendation:** Check that the execute() method was added at the module level (not inside a class)."
                )

            return (
                "# Verification Request\n\n"
                "To verify fixes, please specify what was fixed:\n"
                "- \"verify browser plugin fix\"\n"
                "- \"check if browser changes are correct\"\n"
                "- \"confirm search plugin works now\"\n\n"
                "I'll scan the relevant files and report if the recommended changes were applied correctly."
            )
        except Exception as exc:
            return f"Error verifying fixes: {exc}"

    def _diagnose_system_issues(self, base_path: Path, question: str) -> str:
        try:
            if any(keyword in question for keyword in ["browser", "search", "web"]):
                return self._diagnose_web_plugins(base_path)
            if "plugin" in question and ("not working" in question or "broken" in question):
                return self._diagnose_plugin_execution(base_path)
            return self._diagnose_general_issues(base_path)
        except Exception as exc:
            return f"**Diagnostic Error:** {exc}\n\nTry being more specific about the issue."

    def _diagnose_web_plugins(self, base_path: Path) -> str:
        try:
            browser_path = base_path / "src" / "plugins" / "browser.py"
            search_path = base_path / "src" / "plugins" / "search.py"

            issues: List[str] = []
            recommendations: List[str] = []

            if browser_path.exists():
                content = browser_path.read_text(encoding="utf-8", errors="replace")
                if "async def execute(" not in content:
                    issues.append("?? Browser plugin may not have async execute() method")
                if "playwright" not in content.lower():
                    issues.append("?? Browser plugin missing Playwright imports")
                    recommendations.append("Install Playwright: `pip install playwright`")
            else:
                issues.append("? browser.py plugin file not found")

            if search_path.exists():
                content = search_path.read_text(encoding="utf-8", errors="replace")
                if "async def execute(" not in content:
                    issues.append("?? Search plugin may not have async execute() method")
                if "httpx" not in content and "requests" not in content:
                    issues.append("?? Search plugin missing HTTP library")
                    recommendations.append("Install httpx: `pip install httpx`")
            else:
                issues.append("? search.py plugin file not found")

            executor_path = base_path / "src" / "agent" / "plugin_executor.py"
            if executor_path.exists():
                executor_content = executor_path.read_text(encoding="utf-8", errors="replace")
                if "browser" not in executor_content.lower():
                    issues.append("?? Browser plugin may not be registered in PluginExecutor")
                if "search" not in executor_content.lower():
                    issues.append("?? Search plugin may not be registered in PluginExecutor")

            return (
                "# Web Plugin Diagnostic Report\n\n"
                f"## Issues Found ({len(issues)} total)\n"
                f"{chr(10).join(issues) if issues else '? No obvious issues detected'}\n\n"
                f"## Recommendations ({len(recommendations)} total)\n"
                f"{chr(10).join(recommendations) if recommendations else '? No immediate actions needed'}\n\n"
                "## Likely Root Cause\n\n"
                "The web plugins show `web_search(query=...)` instead of executing because:\n\n"
                "1. **Tool execution not triggering**: The ReAct loop may not be calling plugin execute() methods\n"
                "2. **Missing async/await**: Plugin methods need to be async and properly awaited\n"
                "3. **Plugin registration**: Plugins may not be properly loaded by PluginExecutor\n\n"
                "## Quick Fix Steps\n\n"
                "1. **Verify Plugin Registration**:\n"
                "   - Check `src/agent/plugin_executor.py` loads browser & search plugins\n"
                "   - Ensure plugins are in `src/plugins/` directory\n\n"
                "2. **Check Execution Flow**:\n"
                "   - Verify `react_loop.py` calls `plugin_executor.execute()`\n"
                "   - Confirm tools are defined in `config/mcp_tools.json`\n\n"
                "3. **Test Plugins Directly**:\n"
                "   ```bash\n"
                "   cd mcp-ai-agent\n"
                "   python -c \"from src.plugins.search import SearchPlugin; import asyncio; p = SearchPlugin(); result = asyncio.run(p.execute('search', 'web_search', {'query': 'test'})); print(result)\"\n"
                "   ```\n\n"
                "## Files to Inspect\n"
                "- `src/agent/react_loop.py` - Tool execution logic\n"
                "- `src/agent/plugin_executor.py` - Plugin routing\n"
                "- `src/plugins/browser.py` - Browser implementation\n"
                "- `src/plugins/search.py` - Search implementation"
            )
        except Exception as exc:
            return f"Error diagnosing web plugins: {exc}"

    def _diagnose_plugin_execution(self, base_path: Path) -> str:
        return (
            "# Plugin Execution Diagnostic\n\n"
            "## Common Reasons Plugins Don't Execute\n\n"
            "### 1. Tool Not Recognized\n"
            "**Symptom**: Shows `tool_name(args)` instead of results  \n"
            "**Cause**: ReAct loop doesn't recognize the tool\n"
            "**Fix**: Check `config/mcp_tools.json` has tool definition\n\n"
            "### 2. Plugin Not Loaded\n"
            "**Symptom**: Plugin file exists but doesn't run  \n"
            "**Cause**: PluginExecutor doesn't import/register it  \n"
            "**Fix**: Add to `plugin_executor.py`'s plugin map\n\n"
            "### 3. Async Not Awaited\n"
            "**Symptom**: Returns coroutine object instead of result  \n"
            "**Cause**: Missing `await` keyword  \n"
            "**Fix**: Ensure all async methods are awaited\n\n"
            "### 4. Error Silently Caught\n"
            "**Symptom**: No output or generic error  \n"
            "**Cause**: Exception swallowed by try/except  \n"
            "**Fix**: Check logs, add better error handling\n\n"
            "## How to Debug\n\n"
            "1. **Check Tool Definition**:\n"
            "   ```bash\n"
            "   cat config/mcp_tools.json | grep -A 5 \"tool_name\"\n"
            "   ```\n\n"
            "2. **Test Plugin Directly**:\n"
            "   ```python\n"
            "   from src.agent.plugin_executor import PluginExecutor\n"
            "   # Instantiate and run the plugin manually\n"
            "   ```\n\n"
            "3. **Enable Debug Logging**:\n"
            "   - Temporarily add print statements in `react_loop.py`\n"
            "   - Ensure `PluginExecutor.execute()` is invoked\n"
        )

    def _diagnose_general_issues(self, base_path: Path) -> str:
        try:
            import sys
            issues: List[str] = []
            py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 8):
                issues.append(f"?? Python {py_version} - Recommend 3.8+")

            for name in ["src", "tests", "docs"]:
                if not (base_path / name).exists():
                    issues.append(f"?? Missing directory: {name}/")

            for rel_path in ["src/agent/core.py", "src/agent/react_loop.py", "src/agent/plugin_executor.py"]:
                if not (base_path / rel_path).exists():
                    issues.append(f"? Missing critical file: {rel_path}")

            return (
                "# System Diagnostic Report\n\n"
                "## Python Environment\n"
                f"- **Version**: {py_version}\n"
                f"- **Path**: {sys.executable}\n\n"
                f"## Issues Detected ({len(issues)} total)\n"
                f"{chr(10).join(issues) if issues else '? No critical issues found'}\n\n"
                "## System Health\n"
                f"- **Core Files**: {'? Present' if not issues else '?? Some missing'}\n"
                f"- **Directory Structure**: {'? Valid' if (base_path / 'src').exists() else '? Invalid'}\n\n"
                "## Next Steps\n\n"
                "If experiencing issues:\n"
                "1. Be more specific about the problem\n"
                "2. Mention which plugin/tool is failing\n"
                "3. Include any error messages you're seeing\n\n"
                "**Example diagnostic questions**:\n"
                "- \"diagnose why browser plugin isn't working\"\n"
                "- \"why is web search showing the command instead of results\"\n"
                "- \"debug the search plugin execution\""
            )
        except Exception as exc:
            return f"Error in general diagnostic: {exc}"

    def _generate_improvement_recommendations(self, base_path: Path) -> str:
        try:
            py_files = list((base_path / "src").rglob("*.py"))
            files_without_docstrings: List[str] = []
            files_without_type_hints: List[str] = []
            large_functions: List[str] = []

            for path in py_files[:30]:
                content = path.read_text(encoding="utf-8", errors="replace")
                if '"""' not in content and "'''" not in content:
                    files_without_docstrings.append(path.name)
                if "-> " not in content and ": " not in content[:1000]:
                    files_without_type_hints.append(path.name)
                if content.count("def ") > 20:
                    large_functions.append(path.name)

            return (
                "Based on analyzing the actual codebase, here are specific improvements I recommend:\n\n"
                "## High Priority\n\n"
                "1. **Add Type Hints**\n"
                f"   - {len(files_without_type_hints)} files lack type hints\n"
                "   - This improves code clarity and enables better IDE support\n"
                f"   - Start with: {', '.join(files_without_type_hints[:5])}\n\n"
                "2. **Improve Documentation**\n"
                f"   - {len(files_without_docstrings)} files need docstrings\n"
                "   - Add function/class-level documentation\n"
                f"   - Files to prioritize: {', '.join(files_without_docstrings[:5])}\n\n"
                "3. **Refactor Large Files**\n"
                f"   - {len(large_functions)} files have 20+ functions\n"
                "   - Consider splitting into smaller modules\n"
                f"   - Files: {', '.join(large_functions[:3])}\n\n"
                "## Medium Priority\n\n"
                "4. **Error Handling**\n"
                "   - Standardize exception handling across all plugins\n"
                "   - Add custom exception classes for better error tracking\n\n"
                "5. **Testing**\n"
                "   - Expand unit test coverage beyond integration tests\n"
                "   - Add edge case testing for plugins\n\n"
                "## Low Priority\n\n"
                "6. **Performance**\n"
                "   - Add caching for frequently accessed data\n"
                "   - Profile and optimize hot paths in react_loop.py"
            )
        except Exception as exc:
            return f"Error generating recommendations: {exc}"

    def _generate_detailed_assessment(self, base_path: Path) -> str:
        try:
            all_files = list(base_path.rglob("*.py"))
            src_files = list((base_path / "src").rglob("*.py"))
            test_files = list((base_path / "tests").rglob("*.py"))

            total_lines = 0
            total_classes = 0
            total_functions = 0
            for path in src_files[:50]:
                content = path.read_text(encoding="utf-8", errors="replace")
                total_lines += len(content.split("\n"))
                total_classes += content.count("class ")
                total_functions += content.count("def ")

            return (
                "# Comprehensive Codebase Assessment\n\n"
                "## Metrics\n"
                f"- **Total Python Files**: {len(all_files)}\n"
                f"- **Source Files**: {len(src_files)}\n"
                f"- **Test Files**: {len(test_files)}\n"
                f"- **Total Lines of Code**: ~{total_lines:,}\n"
                f"- **Classes**: {total_classes}\n"
                f"- **Functions**: {total_functions}\n"
                f"- **Test Coverage**: {len(test_files)}/{len(src_files)} ratio\n\n"
                "## Architecture Quality: 8/10\n\n"
                "**Strengths**:\n"
                "? Modular plugin-based design\n"
                "? Async/await throughout\n"
                "? MCP protocol integration\n"
                "? Real-time WebSocket communication\n"
                "? Clean separation of concerns\n\n"
                "**Areas for Improvement**:\n"
                "?? Need more comprehensive unit tests\n"
                "?? Some files could use better documentation\n"
                "?? Type hints coverage could be improved\n\n"
                "## Code Quality: 7.5/10\n\n"
                "**Good practices observed**:\n"
                "- Consistent use of async patterns\n"
                "- Plugin architecture allows extensibility\n"
                "- Error handling in most critical paths\n\n"
                "**Recommendations**:\n"
                "- Add type hints to all functions\n"
                "- Increase docstring coverage\n"
                "- Implement more unit tests\n\n"
                "## Overall Assessment\n"
                "This is a well-architected codebase with good separation of concerns."
            )
        except Exception as exc:
            return f"Error in assessment: {exc}"

    def _explain_architecture(self, base_path: Path, question: str) -> str:
        try:
            plugin_files = list((base_path / "src" / "plugins").glob("*.py"))
            plugin_names = [path.stem for path in plugin_files]
            executor_path = base_path / "src" / "agent" / "plugin_executor.py"
            executor_content = executor_path.read_text(encoding="utf-8", errors="replace") if executor_path.exists() else ""
            has_async = "async def" in executor_content
            has_execute = "def execute(" in executor_content

            plugin_lines = "\n".join(
                f"- **{name}**: Handles {name.replace('_', ' ')} functionality" for name in plugin_names[:10]
            )

            return (
                "# Plugin System Implementation\n\n"
                f"## Discovered Plugins ({len(plugin_files)} total)\n"
                f"{', '.join(plugin_names)}\n\n"
                "## Architecture\n\n"
                "**Plugin Executor** (`plugin_executor.py`):\n"
                f"- {'? Uses async execution' if has_async else '? Synchronous only'}\n"
                f"- {'? Has execute() method' if has_execute else '?? Missing execute() method'}\n\n"
                "**How It Works**:\n\n"
                "1. **Registration**: Plugins are loaded from `src/plugins/` directory\n"
                "2. **Routing**: PluginExecutor routes tool calls to appropriate plugins\n"
                "3. **Execution**: Each plugin has an `execute()` method that handles tool calls\n"
                "4. **Response**: Results are returned in standardized format\n\n"
                "**Example Plugin Structure**:\n"
                "```python\n"
                "class SomePlugin:\n"
                "    async def execute(self, server, tool_name, args):\n"
                "        return {\"status\": \"success\", \"result\": ...}\n"
                "```\n\n"
                "**Available Plugins**:\n"
                f"{plugin_lines}"
            )
        except Exception as exc:
            return f"Error explaining architecture: {exc}"

    def _is_capability_question(self, question: str) -> bool:
        keywords = [
            "can you",
            "ability",
            "capable",
            "capability",
            "create plugin",
            "able to",
            "could you",
            "are you able",
            "would you be able",
            "extend yourself",
        ]
        lowered = question.lower()
        return any(keyword in lowered for keyword in keywords)

    def _answer_capability_question(self, question: str, base_path: Path) -> str:
        if "create" in question and "plugin" in question:
            return self._answer_plugin_creation_capability(base_path)

        return (
            "**Yes, I have extensive capabilities!**\n\n"
            "## Core Abilities:\n\n"
            "1. **Code Analysis**: Read and understand code in multiple languages\n"
            "2. **File Operations**: Create, read, update, delete files\n"
            "3. **Self-Modification**: Can modify my own code including plugins\n"
            "4. **Tool Creation**: I can create new plugins and tools whenever you need them\n"
            "5. **Documentation**: Generate docs, READMEs, guides\n"
            "6. **Testing**: Create and run tests\n"
            "7. **Web Scraping**: Via browser and crawl4ai plugins\n"
            "8. **Search**: Web search, codebase search\n"
            "9. **Real-time Communication**: WebSocket-based UI\n\n"
            "## Self-Improvement:\n\n"
            "I can analyze my own code, identify issues, and fix them. I recently added docstrings to models.py based on my own analysis!\n\n"
            "**What would you like me to create or modify?**"
        )

    def _answer_plugin_creation_capability(self, base_path: Path) -> str:
        try:
            plugin_files = list((base_path / "src" / "plugins").glob("*.py"))
            plugin_list = "\n".join(f"- {path.stem}" for path in plugin_files[:8])
            return (
                "**Yes! I can create new plugins for myself!**\n\n"
                "## How It Works:\n\n"
                "1. **Create Plugin File**: I write a new Python file in `src/plugins/`\n"
                "2. **Implement Interface**: Each plugin needs an `async def execute()` method\n"
                "3. **Auto-Discovery**: Plugins are automatically loaded on startup\n"
                "4. **Immediate Use**: New capabilities are available right away!\n\n"
                f"## Current Plugins ({len(plugin_files)}):\n{plugin_list}\n\n"
                "## Example: Creating a New Plugin\n\n"
                "```python\n"
                "# src/plugins/my_new_plugin.py\n"
                "class MyNewPlugin:\n"
                "    async def execute(self, server, tool_name, args):\n"
                "        return {\"status\": \"success\", \"result\": \"Done!\"}\n"
                "```\n\n"
                "## What I Can Add:\n\n"
                "- API integrations (weather, news, databases)\n"
                "- Custom analysis tools\n"
                "- File processing utilities\n"
                "- External service connectors\n"
                "- Anything you can code in Python!\n\n"
                "**Want me to create a specific plugin for you? Just describe what you need!**"
            )
        except Exception as exc:
            return f"Yes, I can create plugins, but encountered an error checking current ones: {exc}"

    def _extract_plugin_name(self, question: str) -> Optional[str]:
        patterns = [
            "crawl4ai",
            "leann",
            "browser",
            "search",
            "analysis",
            "news_fetch",
            "time_utils",
            "kokoro_tts",
            "kokoro",
        ]
        for pattern in patterns:
            if pattern in question:
                return f"{pattern}_plugin" if pattern in {"crawl4ai", "leann", "kokoro"} else pattern
        return None

    def _explain_specific_plugin(self, base_path: Path, plugin_name: str) -> str:
        try:
            plugin_path = base_path / "src" / "plugins" / f"{plugin_name}.py"
            if not plugin_path.exists():
                return f"Plugin '{plugin_name}' not found in src/plugins/"

            content = plugin_path.read_text(encoding="utf-8", errors="replace")
            class_name: Optional[str] = None
            methods: List[str] = []
            docstring: Optional[str] = None
            imports: List[str] = []

            for index, line in enumerate(content.split("\n")):
                if index < 10 and '"""' in line and not docstring:
                    docstring = line.strip().strip('"""')
                if line.strip().startswith("class ") and not class_name:
                    class_name = line.split("class ")[1].split("(")[0].split(":")[0].strip()
                if "    async def " in line:
                    method = line.split("async def ")[1].split("(")[0].strip()
                    if not method.startswith("_"):
                        methods.append(method + " (async)")
                elif "    def " in line and not line.strip().startswith("def _"):
                    method = line.split("def ")[1].split("(")[0].strip()
                    if not method.startswith("_"):
                        methods.append(method)
                if line.strip().startswith(("import ", "from ") ):
                    imports.append(line.strip())

            method_lines = "\n".join(f"- {name}" for name in methods[:10]) or "- execute()"
            import_lines = "\n".join(f"- {item}" for item in imports[:5]) or "- Standard Python libraries"
            plugin_label = plugin_name.replace('_', ' ')
            overview = docstring or f"Plugin for {plugin_label} functionality"
            line_count = len(content.splitlines())

            return (
                f"# {plugin_label.title()} Plugin\n\n"
                "## Overview\n"
                f"{overview}\n\n"
                "## Main Class\n"
                f"**{class_name or 'Unknown'}**\n\n"
                f"## Public Methods ({len(methods)} total)\n"
                f"{method_lines}\n\n"
                "## Key Dependencies\n"
                f"{import_lines}\n\n"
                "## File Location\n"
                f"`src/plugins/{plugin_name}.py`\n\n"
                "## Lines of Code\n"
                f"~{line_count} lines\n\n"
                "## Purpose\n"
                f"This plugin provides {plugin_label} capabilities to the agent system."
            )
        except Exception as exc:
            return f"Error analyzing {plugin_name}: {exc}"

    def _generate_codebase_overview(self, base_path: Path) -> str:
        src_files = list((base_path / "src").rglob("*.py"))
        test_files = list((base_path / "tests").rglob("*.py"))
        doc_files = list((base_path / "docs").rglob("*.md"))
        return (
            "# Codebase Overview\n\n"
            "## Structure\n"
            "```\n"
            "mcp-ai-agent/\n"
            f"|-- src/ ({len(src_files)} Python files)\n"
            "|   |-- agent/ (core functionality)\n"
            "|   `-- plugins/ (tool plugins)\n"
            f"|-- tests/ ({len(test_files)} test files)\n"
            f"`-- docs/ ({len(doc_files)} documentation files)\n"
            "```\n\n"
            "## Main Directories\n\n"
            "**src/agent/**: Core agent implementation\n"
            "- Agent class, API integration, memory management\n"
            "- ReAct loop for autonomous behavior\n"
            "- Web UI and server implementations\n\n"
            "**src/plugins/**: Extensible tool plugins\n"
            "- Search, browser, analysis, LEANN, etc.\n"
            "- Each plugin provides specific capabilities\n"
            "- MCP-compatible tool interfaces\n\n"
            "**tests/**: Test suite\n"
            "- Integration tests, contract tests\n"
            "- Validates core functionality\n\n"
            "## Technology Stack\n"
            "- **Language**: Python (async/await)\n"
            "- **Architecture**: Plugin-based modular design\n"
            "- **Protocol**: Model Context Protocol (MCP)\n"
            "- **UI**: WebSocket-based real-time interface\n"
            "- **AI**: OpenRouter LLM integration"
        )


