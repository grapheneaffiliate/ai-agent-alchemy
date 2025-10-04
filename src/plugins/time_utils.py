"""Time and date utilities for MCP AI Agent."""

from datetime import datetime
from typing import Dict, Any
import pytz


class TimePlugin:
    """Time and date utility plugin."""

    def __init__(self, timezone: str = "America/New_York"):
        """Initialize with timezone (default: Eastern Time)."""
        self.timezone = pytz.timezone(timezone)

    def get_current_time(self) -> Dict[str, Any]:
        """Get current time in configured timezone."""
        now = datetime.now(self.timezone)
        return {
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "time_12h": now.strftime("%I:%M:%S %p"),
            "day_of_week": now.strftime("%A"),
            "timezone": str(self.timezone),
            "timestamp": int(now.timestamp())
        }

    def get_current_date(self) -> Dict[str, Any]:
        """Get current date in configured timezone."""
        now = datetime.now(self.timezone)
        return {
            "date": now.strftime("%Y-%m-%d"),
            "day": now.day,
            "month": now.month,
            "year": now.year,
            "day_of_week": now.strftime("%A"),
            "day_of_week_short": now.strftime("%a"),
            "month_name": now.strftime("%B"),
            "month_name_short": now.strftime("%b"),
            "timezone": str(self.timezone)
        }

    def format_datetime(self, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format current datetime with custom format string."""
        now = datetime.now(self.timezone)
        return now.strftime(format_string)

    def get_timestamp(self) -> int:
        """Get current Unix timestamp."""
        return int(datetime.now(self.timezone).timestamp())

    def from_timestamp(self, timestamp: int) -> Dict[str, Any]:
        """Convert Unix timestamp to datetime in configured timezone."""
        dt = datetime.fromtimestamp(timestamp, self.timezone)
        return {
            "datetime": dt.isoformat(),
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M:%S"),
            "day_of_week": dt.strftime("%A"),
            "timezone": str(self.timezone)
        }

    def get_day_info(self) -> Dict[str, Any]:
        """Get detailed information about the current day."""
        now = datetime.now(self.timezone)
        return {
            "date": now.strftime("%Y-%m-%d"),
            "day_of_week": now.strftime("%A"),
            "day_of_month": now.day,
            "day_of_year": now.timetuple().tm_yday,
            "week_number": now.isocalendar()[1],
            "is_weekend": now.weekday() >= 5,
            "quarter": (now.month - 1) // 3 + 1,
            "timezone": str(self.timezone)
        }


# Singleton instance for Eastern Time (Washington DC)
_time_instance: TimePlugin = None


def get_time_plugin(timezone: str = "America/New_York") -> TimePlugin:
    """Get or create time plugin instance."""
    global _time_instance
    if not _time_instance:
        _time_instance = TimePlugin(timezone)
    return _time_instance


# MCP Plugin Interface
async def execute(server: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute time plugin commands via MCP interface."""
    try:
        time_plugin = get_time_plugin()

        # Handle MCP-configured tool names
        if tool_name == 'get-current-time':
            result = time_plugin.get_current_time()
            return {"status": "success", "result": result}

        elif tool_name == 'get-current-date':
            result = time_plugin.get_current_date()
            return {"status": "success", "result": result}

        elif tool_name == 'get-day-info':
            result = time_plugin.get_day_info()
            return {"status": "success", "result": result}

        elif tool_name == 'format-datetime':
            format_string = args.get('format_string', '%Y-%m-%d %H:%M:%S')
            result = time_plugin.format_datetime(format_string)
            return {"status": "success", "result": result}

        else:
            return {"status": "error", "error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        return {"status": "error", "error": str(e)}
