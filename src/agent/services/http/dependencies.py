"""Shared dependency helpers for the HTTP service."""

from __future__ import annotations

from typing import Optional

from ...models import Session
from ...plugin_executor import PluginExecutor
import sys
import os
# Ensure the src directory is in the path for correct module resolution
src_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from ..api import AgentAPI as api_module


_agent_instance: Optional["api_module.AgentAPI"] = None
_plugin_executor: Optional[PluginExecutor] = None


def get_agent():
    """Return a singleton AgentAPI instance for HTTP handlers."""
    global _agent_instance, _plugin_executor
    if _agent_instance is None:
        session = Session(id="openwebui", history=[])
        _agent_instance = api_module.AgentAPI(session)
        _plugin_executor = PluginExecutor()
    return _agent_instance


def get_plugin_executor() -> PluginExecutor:
    """Return the plugin executor paired with the agent instance."""
    global _plugin_executor
    if _plugin_executor is None:
        get_agent()
    assert _plugin_executor is not None  # Narrow type
    return _plugin_executor
