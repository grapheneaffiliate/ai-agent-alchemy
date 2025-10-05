"""Parsing helpers for tool calls and argument extraction."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


_TOOL_CALL_PATTERN = re.compile(r"USE TOOL: ([\\w-]+)(.*?)(?=USE TOOL:|$)", re.DOTALL)
_ARG_PATTERN = re.compile(r"^(\\w+):\\s*(.+)$", re.MULTILINE)
_PATH_PATTERN = re.compile(r"path:\s*(\\S+)")


def parse_tool_calls(response: str) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    """Extract tool names and argument dictionaries from an LLM response."""
    tool_names: List[str] = []
    args_dict: Dict[str, Dict[str, str]] = {}

    for tool_name, section in _TOOL_CALL_PATTERN.findall(response):
        tool_names.append(tool_name)
        matches = _ARG_PATTERN.findall(section)
        if matches:
            args_dict[tool_name] = {key.strip(): value.strip() for key, value in matches}
        else:
            args_dict[tool_name] = {}

    return tool_names, args_dict


def parse_args_from_input(user_input: str, tool_name: str | None = None) -> Dict[str, str]:
    """Fallback parser that looks for simple `path: ...` style hints in raw input."""
    match = _PATH_PATTERN.search(user_input)
    if match:
        return {"path": match.group(1)}
    return {}
