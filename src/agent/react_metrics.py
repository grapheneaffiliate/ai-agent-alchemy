"""Tool metrics tracking for ReAct loop monitoring and optimization."""

import time
import logging
from typing import Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class ToolMetrics:
    """Track tool usage metrics for monitoring and optimization."""

    def __init__(self):
        self.tool_usage = defaultdict(int)
        self.tool_times = defaultdict(list)
        self.tool_errors = defaultdict(int)
        self.session_start = time.time()

    def record_tool_use(self, tool_name: str, execution_time: float, success: bool):
        """Record tool usage statistics."""
        self.tool_usage[tool_name] += 1
        self.tool_times[tool_name].append(execution_time)
        if not success:
            self.tool_errors[tool_name] += 1

        logger.debug(
            'tool_usage_recorded',
            extra={'tool': tool_name, 'execution_time': round(execution_time, 3), 'success': success}
        )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        total_tools = sum(self.tool_usage.values())
        total_time = time.time() - self.session_start

        return {
            "session_duration": round(total_time, 2),
            "total_tool_calls": total_tools,
            "tool_breakdown": dict(self.tool_usage),
            "average_response_times": {
                tool: round(sum(times) / len(times), 2) if times else 0
                for tool, times in self.tool_times.items()
            },
            "error_rates": {
                tool: round(errors / count, 3) if count > 0 else 0
                for tool, (count, errors) in [
                    (tool, (self.tool_usage[tool], self.tool_errors[tool]))
                    for tool in self.tool_usage.keys()
                ]
            },
            "most_used_tools": sorted(
                self.tool_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }

    @staticmethod
    def get_logger():
        """Get logger instance for this module."""
        return logging.getLogger(__name__)
