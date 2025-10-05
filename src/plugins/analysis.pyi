"""Enhanced type stubs for analysis plugin."""

from typing import Any, Dict, List, Optional, Union
from agent.models import MCPTool
from agent.errors import PluginExecutionError


class ReplPlugin:
    """Plugin for executing code in various languages."""

    async def execute(
        self,
        code: str,
        language: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]: ...


class AnalysisPlugin:
    """Plugin for data analysis and visualization."""

    async def analyze_data(
        self,
        data: Union[str, List[Dict[str, Any]], Dict[str, Any]],
        analysis_type: str,
        **kwargs: Any
    ) -> Dict[str, Any]: ...

    async def create_visualization(
        self,
        data: Union[str, List[Dict[str, Any]], Dict[str, Any]],
        chart_type: str,
        **kwargs: Any
    ) -> str: ...


def register_tools() -> List[MCPTool]: ...


async def execute_code(
    code: str,
    language: str = "python",
    timeout: int = 30
) -> Dict[str, Any]: ...


async def analyze_dataset(
    data_path: str,
    analysis_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]: ...
