"""Tool call extraction and parsing for ReAct loop."""

import re
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def extract_tool_calls(response: str) -> List[Dict[str, Any]]:
    """
    Extract tool calls from LLM response.

    Looks for patterns like:
    TOOL_CALL: {"server": "browser", "tool": "extract_text", "args": {"selector": ".content"}}

    Also handles XML format: <invoke name="use_mcp_tool">...</invoke>
    """
    tool_calls = []

    # Look for TOOL_CALL JSON patterns
    json_patterns = [
        r'TOOL_CALL:\s*(\{.*?\})',
        r'tool_call:\s*(\{.*?\})',
        r'Tool Call:\s*(\{.*?\})'
    ]

    for pattern in json_patterns:
        matches = re.finditer(pattern, response, re.DOTALL)
        for match in matches:
            try:
                tool_json = match.group(1)
                tool_call = json.loads(tool_json)
                tool_calls.append(tool_call)
            except json.JSONDecodeError:
                logger.warning(f"⚠️  Could not parse tool JSON: {tool_json[:100]}...")
                continue

    # Look for XML tool call patterns
    xml_pattern = r'<invoke name="use_mcp_tool">.*?<parameter name="server_name">([^<]+)</parameter>.*?<parameter name="tool_name">([^<]+)</parameter>.*?<parameter name="arguments">([^<]+)</parameter>.*?</invoke>'
    xml_matches = re.finditer(xml_pattern, response, re.DOTALL)
    for match in xml_matches:
        try:
            server_name = match.group(1)
            tool_name = match.group(2)
            arguments_str = match.group(3)

            # Parse the arguments JSON
            args_dict = json.loads(arguments_str)

            tool_call = {
                "server": server_name,
                "tool": tool_name,
                "args": args_dict
            }
            tool_calls.append(tool_call)
            logger.info(f"✅ Parsed XML tool call: {server_name}.{tool_name}")
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"⚠️  Could not parse XML tool call: {str(e)}")
            continue

    return tool_calls
