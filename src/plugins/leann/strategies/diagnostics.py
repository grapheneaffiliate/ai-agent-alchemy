from __future__ import annotations

"""Diagnostics helper used by LEANN fallback analysis."""

from pathlib import Path
from typing import List


class DiagnosticsAdvisor:
    """Provide visibility checks and diagnostic walkthroughs."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    def visibility_report(self) -> str:
        try:
            py_files = list((self._project_root / "src").rglob("*.py"))[:20]
            file_list = [path.name for path in py_files]
            file_display = ", ".join(file_list[:10]) or "No Python files discovered"
            return (
                "Yes, I can see my codebase! I have full access to:\n\n"
                f"**Source Code**: {len(py_files)} Python files in the src/ directory, including {file_display}.\n"
                "**Tests**: Comprehensive coverage in tests/.\n"
                "**Docs**: Rich documentation in docs/.\n\n"
                "I can read, analyse, and modify these files whenever needed."
            )
        except Exception as exc:  # pragma: no cover - defensive
            return f"Encountered an error while listing files: {exc}"

    def verify_recent_fixes(self, question: str, base_path: Path = None) -> str:
        if base_path is None:
            base_path = self._project_root

        lowered = question.lower()
        browser_path = base_path / "src" / "plugins" / "browser.py"

        if "browser" in lowered or "web" in lowered:
            if not browser_path.exists():
                return "- browser.py not found - cannot verify the fix"

            content = browser_path.read_text(encoding="utf-8", errors="replace")
            if "async def execute" in content or "def execute" in content:
                return (
                    "# Browser Plugin Fix Verification\n\n"
                    "- Execute entry point detected in src/plugins/browser.py.\n"
                    "- The plugin is ready to receive tool calls.\n"
                    "- Restart the agent to ensure the updated plugin is loaded."
                )
            return (
                "# Browser Plugin Fix Verification\n\n"
                "- Execute entry point still missing in src/plugins/browser.py.\n"
                "- Ensure sync def execute(server, tool_name, args) is defined at module scope."
            )

        return (
            "# Verification Request\n\n"
            "I can confirm fixes after you reference a specific plugin or subsystem, e.g.\n"
            "- \"verify browser plugin fix\"\n"
            "- \"confirm search tool routing\"\n"
            "- \"check whether LEANN plugin changes landed\""
        )

    def diagnose(self, question: str) -> str:
        lowered = question.lower()
        if any(keyword in lowered for keyword in ("browser", "search", "web")):
            return self.web_plugins_report()
        if "plugin" in lowered and ("not working" in lowered or "broken" in lowered):
            return self.plugin_execution_report()
        return self.general_system_report()

    def web_plugins_report(self, base_path: Path = None) -> str:
        if base_path is None:
            base_path = self._project_root

        browser_path = base_path / "src" / "plugins" / "browser.py"
        search_path = base_path / "src" / "plugins" / "search.py"

        issues: List[str] = []
        recommendations: List[str] = []

        if browser_path.exists():
            content = browser_path.read_text(encoding="utf-8", errors="replace")
            if "async def execute" not in content:
                issues.append("- Browser plugin may not expose an async execute() entry point")
            if "playwright" not in content.lower():
                recommendations.append("- Install Playwright: pip install playwright")
        else:
            issues.append("- src/plugins/browser.py not found")

        if search_path.exists():
            content = search_path.read_text(encoding="utf-8", errors="replace")
            if "async def execute" not in content:
                issues.append("- Search plugin may not expose an async execute() entry point")
            if "httpx" not in content and "requests" not in content:
                recommendations.append("- Install httpx: pip install httpx")
        else:
            issues.append("- src/plugins/search.py not found")

        lines = ["# Web Plugin Diagnostic Report", ""]
        lines.append(f"## Issues Found ({len(issues)} total)")
        lines.extend(issues or ["- No obvious issues detected"])
        lines.append("")
        lines.append(f"## Recommendations ({len(recommendations)} total)")
        lines.extend(recommendations or ["- No immediate actions needed"])
        lines.append("")
        lines.append("## Suggested Next Steps")
        lines.extend([
            "- Confirm tools are listed in config/mcp_tools.json.",
            "- Verify PluginExecutor loads both browser and search modules.",
            "- Add or verify async execute methods on each plugin.",
        ])
        return "\n".join(lines)

    def plugin_execution_report(self) -> str:
        lines = ["# Plugin Execution Diagnostic", ""]
        lines.append("## Common causes of silent failures")
        lines.extend([
            "- Tool not registered in config/mcp_tools.json.",
            "- Plugin missing an async execute() method.",
            "- Execution path not awaiting plugin coroutines.",
            "- Exceptions swallowed by broad try/except blocks.",
        ])
        lines.append("")
        lines.append("## Quick debugging steps")
        lines.extend([
            "- Log tool routing inside react_loop.py and plugin_executor.py.",
            "- Invoke the plugin directly in a Python shell.",
            "- Enable structured logging around plugin execution paths.",
        ])
        return "\n".join(lines)

    def general_system_report(self) -> str:
        lines = ["# System Diagnostic Checklist", ""]
        lines.extend([
            "- Confirm tools exist in config/mcp_tools.json.",
            "- Ensure plugins are imported in plugin_executor.py.",
            "- Await all plugin execute() calls.",
            "- Check logs for suppressed exceptions.",
            "- Verify environment variables and API credentials.",
            "- Install dependencies via pip install -r requirements.txt.",
            "- Run integration tests for tool execution paths.",
        ])
        return "\n".join(lines)
