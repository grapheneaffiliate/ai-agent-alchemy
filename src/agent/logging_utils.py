"""Enhanced structured logging with context propagation and performance tracking."""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional, Union

_CONTEXT_ID: ContextVar[Optional[str]] = ContextVar("agent_context_id", default=None)
_SESSION_ID: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
_REQUEST_ID: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class LogLevel(str, Enum):
    """Structured log levels."""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"


class LogComponent(str, Enum):
    """System components for structured logging."""
    AGENT = "agent"
    PLUGIN = "plugin"
    SERVER = "server"
    MEMORY = "memory"
    API = "api"
    CLI = "cli"
    EXECUTOR = "executor"
    LOADER = "loader"


@dataclass
class LogContext:
    """Structured logging context."""
    context_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    component: Optional[LogComponent] = None
    operation: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging."""
        result = {}
        if self.context_id:
            result["context_id"] = self.context_id
        if self.session_id:
            result["session_id"] = self.session_id
        if self.request_id:
            result["request_id"] = self.request_id
        if self.component:
            result["component"] = self.component.value
        if self.operation:
            result["operation"] = self.operation
        if self.user_id:
            result["user_id"] = self.user_id
        result.update(self.metadata)
        return result


class StructuredFormatter(logging.Formatter):
    """Enhanced log formatter with comprehensive structured output."""

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context information
        context_dict = {}
        if (context_id := _CONTEXT_ID.get()):
            context_dict["context_id"] = context_id
        if (session_id := _SESSION_ID.get()):
            context_dict["session_id"] = session_id
        if (request_id := _REQUEST_ID.get()):
            context_dict["request_id"] = request_id

        if context_dict:
            payload["context"] = context_dict

        # Add extra fields from record
        if self.include_extra:
            extra_fields = getattr(record, "extra_fields", None)
            if isinstance(extra_fields, dict):
                payload.update(extra_fields)

        # Add exception info if present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Add performance metrics if available
        duration = getattr(record, "duration", None)
        if duration is not None:
            payload["duration_ms"] = duration

        return json.dumps(payload, ensure_ascii=False, default=str)


class AgentLogger:
    """Enhanced logger with context management and performance tracking."""

    def __init__(self, name: str, component: LogComponent = LogComponent.AGENT):
        self.logger = logging.getLogger(f"agent.{component.value}.{name}")
        self.component = component
        if not self.logger.handlers:
            handler = logging.StreamHandler(stream=sys.stdout)
            handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

    def _log(
        self,
        level: LogLevel,
        message: str,
        operation: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """Internal logging method with context."""
        extra_fields = kwargs.pop("extra_fields", {})

        # Add component and operation context
        context_extra = {
            "component": self.component.value,
            **({"operation": operation} if operation else {}),
            **extra_fields
        }

        # Merge with any existing extra fields
        if "extra_fields" not in kwargs:
            kwargs["extra_fields"] = context_extra

        self.logger.log(getattr(logging, level.value), message, extra=kwargs)

    def debug(self, message: str, operation: Optional[str] = None, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, operation, **kwargs)

    def info(self, message: str, operation: Optional[str] = None, **kwargs: Any) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, operation, **kwargs)

    def warning(self, message: str, operation: Optional[str] = None, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(LogLevel.WARNING, message, operation, **kwargs)

    def error(self, message: str, operation: Optional[str] = None, **kwargs: Any) -> None:
        """Log error message."""
        self._log(LogLevel.ERROR, message, operation, **kwargs)

    def critical(self, message: str, operation: Optional[str] = None, **kwargs: Any) -> None:
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, operation, **kwargs)

    @contextmanager
    def performance_context(
        self,
        operation: str,
        extra_fields: Optional[Dict[str, Any]] = None
    ) -> Generator[None, None, None]:
        """Context manager for performance logging."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            self.info(
                f"Operation completed: {operation}",
                operation=operation,
                extra_fields={
                    "duration_ms": duration,
                    **(extra_fields or {})
                }
            )

    @asynccontextmanager
    async def async_performance_context(
        self,
        operation: str,
        extra_fields: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[None, None]:
        """Async context manager for performance logging."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            self.info(
                f"Async operation completed: {operation}",
                operation=operation,
                extra_fields={
                    "duration_ms": duration,
                    **(extra_fields or {})
                }
            )


def get_logger(name: str, component: LogComponent = LogComponent.AGENT) -> AgentLogger:
    """Get an enhanced logger instance."""
    return AgentLogger(name, component)


def generate_context_id() -> str:
    """Generate a new context identifier."""
    return uuid.uuid4().hex


def set_context_id(context_id: Optional[str]) -> None:
    """Set the current context identifier."""
    _CONTEXT_ID.set(context_id)


def get_context_id() -> Optional[str]:
    """Get the current context identifier."""
    return _CONTEXT_ID.get()


def set_session_id(session_id: Optional[str]) -> None:
    """Set the current session identifier."""
    _SESSION_ID.set(session_id)


def get_session_id() -> Optional[str]:
    """Get the current session identifier."""
    return _SESSION_ID.get()


def set_request_id(request_id: Optional[str]) -> None:
    """Set the current request identifier."""
    _REQUEST_ID.set(request_id)


def get_request_id() -> Optional[str]:
    """Get the current request identifier."""
    return _REQUEST_ID.get()


@contextmanager
def logging_context(
    context_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    component: Optional[LogComponent] = None,
    operation: Optional[str] = None,
    **metadata: Any
) -> Generator[LogContext, None, None]:
    """Context manager for setting logging context."""
    # Store previous values
    prev_context_id = get_context_id()
    prev_session_id = get_session_id()
    prev_request_id = get_request_id()

    # Set new values
    if context_id is not None:
        set_context_id(context_id)
    if session_id is not None:
        set_session_id(session_id)
    if request_id is not None:
        set_request_id(request_id)

    context = LogContext(
        context_id=get_context_id(),
        session_id=get_session_id(),
        request_id=get_request_id(),
        component=component,
        operation=operation,
        metadata=metadata
    )

    try:
        yield context
    finally:
        # Restore previous values
        set_context_id(prev_context_id)
        set_session_id(prev_session_id)
        set_request_id(prev_request_id)


@asynccontextmanager
async def async_logging_context(
    context_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    component: Optional[LogComponent] = None,
    operation: Optional[str] = None,
    **metadata: Any
) -> AsyncGenerator[LogContext, None]:
    """Async context manager for setting logging context."""
    # Store previous values
    prev_context_id = get_context_id()
    prev_session_id = get_session_id()
    prev_request_id = get_request_id()

    # Set new values
    if context_id is not None:
        set_context_id(context_id)
    if session_id is not None:
        set_session_id(session_id)
    if request_id is not None:
        set_request_id(request_id)

    context = LogContext(
        context_id=get_context_id(),
        session_id=get_session_id(),
        request_id=get_request_id(),
        component=component,
        operation=operation,
        metadata=metadata
    )

    try:
        yield context
    finally:
        # Restore previous values
        set_context_id(prev_context_id)
        set_session_id(prev_session_id)
        set_request_id(prev_request_id)


def with_fields(**fields: Any) -> Dict[str, Any]:
    """Helper for passing structured extras to logging calls."""
    return {"extra_fields": fields}


# Convenience functions for common logging patterns
def log_tool_execution(
    tool_name: str,
    success: bool,
    duration_ms: Optional[float] = None,
    error_message: Optional[str] = None,
    **kwargs: Any
) -> None:
    """Log tool execution with standardized fields."""
    logger = get_logger("tool_execution", LogComponent.PLUGIN)
    message = f"Tool {tool_name} executed successfully" if success else f"Tool {tool_name} failed"

    extra_fields = {
        "tool_name": tool_name,
        "success": success,
        **kwargs
    }

    if duration_ms is not None:
        extra_fields["duration_ms"] = duration_ms

    if error_message is not None:
        extra_fields["error_message"] = error_message

    if success:
        logger.info(message, extra_fields=extra_fields)
    else:
        logger.error(message, extra_fields=extra_fields)


def log_plugin_event(
    plugin_name: str,
    event: str,
    level: LogLevel = LogLevel.INFO,
    **kwargs: Any
) -> None:
    """Log plugin-related events."""
    logger = get_logger(f"plugin.{plugin_name}", LogComponent.PLUGIN)
    logger._log(level, f"Plugin {plugin_name}: {event}", extra_fields=kwargs)
