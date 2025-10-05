"""Comprehensive error hierarchy for the MCP AI Agent."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    CONFIGURATION = "configuration"
    NETWORK = "network"
    PLUGIN = "plugin"
    MEMORY = "memory"
    API = "api"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    SECURITY = "security"
    UNKNOWN = "unknown"


class AgentError(Exception):
    """Base exception for all agent-related failures."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context_id = context_id
        self.session_id = session_id
        self.request_id = request_id
        self.metadata = metadata or {}
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "context_id": self.context_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "metadata": self.metadata,
            "cause": str(self.cause) if self.cause else None,
        }


# Configuration Errors
class ConfigurationError(AgentError):
    """Raised when configuration is missing or invalid."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_file: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, category=ErrorCategory.CONFIGURATION, **kwargs)
        self.config_key = config_key
        self.config_file = config_file


class MissingConfigError(ConfigurationError):
    """Raised when required configuration is missing."""

    def __init__(self, config_key: str, config_file: Optional[str] = None, **kwargs: Any):
        message = f"Missing required configuration: {config_key}"
        super().__init__(message, config_key, config_file, **kwargs)


class InvalidConfigError(ConfigurationError):
    """Raised when configuration value is invalid."""

    def __init__(
        self,
        config_key: str,
        config_value: Any,
        expected_type: Optional[str] = None,
        **kwargs: Any
    ):
        if expected_type:
            message = f"Invalid configuration for {config_key}: expected {expected_type}, got {type(config_value).__name__}"
        else:
            message = f"Invalid configuration for {config_key}: {config_value}"
        super().__init__(message, config_key, **kwargs)
        self.config_value = config_value
        self.expected_type = expected_type


# Plugin Errors
class PluginError(AgentError):
    """Base class for plugin-related errors."""

    def __init__(
        self,
        message: str,
        plugin_name: str,
        **kwargs: Any
    ):
        super().__init__(message, category=ErrorCategory.PLUGIN, **kwargs)
        self.plugin_name = plugin_name


@dataclass
class PluginExecutionError(PluginError):
    """Raised when a plugin execution fails."""

    server: str
    tool: str
    reason: str
    plugin_name: str
    input_data: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.message:
            self.message = f"Plugin execution failed: {self.reason}"

    def __str__(self) -> str:
        base = f"[{self.server}.{self.tool}] {self.reason}"
        if self.context_id:
            return f"{base} (context_id={self.context_id})"
        return base


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""

    def __init__(
        self,
        plugin_name: str,
        load_error: Exception,
        **kwargs: Any
    ):
        message = f"Failed to load plugin {plugin_name}: {str(load_error)}"
        super().__init__(message, plugin_name, **kwargs)
        self.load_error = load_error


class PluginTimeoutError(PluginError):
    """Raised when a plugin execution times out."""

    def __init__(
        self,
        plugin_name: str,
        timeout_seconds: float,
        **kwargs: Any
    ):
        message = f"Plugin {plugin_name} timed out after {timeout_seconds}s"
        super().__init__(message, plugin_name, **kwargs)
        self.timeout_seconds = timeout_seconds


# Network and API Errors
class NetworkError(AgentError):
    """Base class for network-related errors."""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs: Any
    ):
        super().__init__(message, category=ErrorCategory.NETWORK, **kwargs)
        self.url = url
        self.status_code = status_code


class UpstreamAPIError(NetworkError):
    """Raised when upstream API calls fail."""

    def __init__(
        self,
        message: str,
        provider: str,
        endpoint: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, **kwargs)
        self.provider = provider
        self.endpoint = endpoint


class TimeoutError(NetworkError):
    """Raised when network operations timeout."""

    def __init__(
        self,
        message: str,
        timeout_seconds: float,
        **kwargs: Any
    ):
        super().__init__(message, **kwargs)
        self.timeout_seconds = timeout_seconds


# Memory and Storage Errors
class MemoryError(AgentError):
    """Base class for memory-related errors."""

    def __init__(
        self,
        message: str,
        memory_path: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, category=ErrorCategory.MEMORY, **kwargs)
        self.memory_path = memory_path


class SessionError(MemoryError):
    """Raised when session operations fail."""

    def __init__(
        self,
        message: str,
        session_id: str,
        **kwargs: Any
    ):
        super().__init__(message, **kwargs)
        self.session_id = session_id


class MemoryStorageError(MemoryError):
    """Raised when memory storage operations fail."""

    def __init__(
        self,
        message: str,
        operation: str,
        **kwargs: Any
    ):
        super().__init__(message, **kwargs)
        self.operation = operation


# Validation Errors
class ValidationError(AgentError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Any = None,
        **kwargs: Any
    ):
        super().__init__(message, category=ErrorCategory.VALIDATION, **kwargs)
        self.field_name = field_name
        self.field_value = field_value


class ToolValidationError(ValidationError):
    """Raised when tool input validation fails."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        parameter_name: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, **kwargs)
        self.tool_name = tool_name
        self.parameter_name = parameter_name


# Resource Errors
class ResourceError(AgentError):
    """Raised when resource constraints are exceeded."""

    def __init__(
        self,
        message: str,
        resource_type: str,
        limit_value: Optional[Union[int, float]] = None,
        current_value: Optional[Union[int, float]] = None,
        **kwargs: Any
    ):
        super().__init__(message, category=ErrorCategory.RESOURCE, **kwargs)
        self.resource_type = resource_type
        self.limit_value = limit_value
        self.current_value = current_value


class RateLimitError(ResourceError):
    """Raised when rate limits are exceeded."""

    def __init__(
        self,
        message: str,
        retry_after_seconds: Optional[float] = None,
        **kwargs: Any
    ):
        super().__init__(message, "rate_limit", **kwargs)
        self.retry_after_seconds = retry_after_seconds


# Security Errors
class SecurityError(AgentError):
    """Raised when security violations are detected."""

    def __init__(
        self,
        message: str,
        violation_type: str,
        **kwargs: Any
    ):
        super().__init__(message, category=ErrorCategory.SECURITY, severity=ErrorSeverity.HIGH, **kwargs)
        self.violation_type = violation_type


# Async-specific Errors
class AsyncOperationError(AgentError):
    """Raised when async operations fail."""

    def __init__(
        self,
        message: str,
        operation_name: str,
        **kwargs: Any
    ):
        super().__init__(message, **kwargs)
        self.operation_name = operation_name


class TaskCancellationError(AsyncOperationError):
    """Raised when async tasks are cancelled."""

    def __init__(
        self,
        operation_name: str,
        cancelled_by: Optional[str] = None,
        **kwargs: Any
    ):
        message = f"Operation {operation_name} was cancelled"
        if cancelled_by:
            message += f" by {cancelled_by}"
        super().__init__(message, operation_name, **kwargs)
        self.cancelled_by = cancelled_by


# Error Factory Functions
async def create_error_from_exception(
    exception: Exception,
    context: Optional[str] = None,
    **kwargs: Any
) -> AgentError:
    """Create appropriate AgentError from generic exception."""
    if isinstance(exception, AgentError):
        return exception

    if isinstance(exception, asyncio.TimeoutError):
        return TimeoutError(
            f"Operation timed out: {str(exception)}",
            timeout_seconds=30.0,
            **kwargs
        )

    if isinstance(exception, ConnectionError):
        return NetworkError(
            f"Connection failed: {str(exception)}",
            **kwargs
        )

    if isinstance(exception, FileNotFoundError):
        return ConfigurationError(
            f"File not found: {str(exception)}",
            **kwargs
        )

    if isinstance(exception, PermissionError):
        return SecurityError(
            f"Permission denied: {str(exception)}",
            "file_access",
            **kwargs
        )

    if isinstance(exception, ValueError):
        return ValidationError(
            f"Invalid value: {str(exception)}",
            **kwargs
        )

    # Default to generic AgentError
    return AgentError(
        f"Unexpected error: {str(exception)}",
        cause=exception,
        **kwargs
    )


# Error Context Manager for structured error handling
class ErrorContext:
    """Context manager for consistent error handling and logging."""

    def __init__(
        self,
        operation: str,
        context_id: Optional[str] = None,
        **metadata: Any
    ):
        self.operation = operation
        self.context_id = context_id
        self.metadata = metadata
        self.start_time = None

    def __enter__(self):
        self.start_time = asyncio.get_event_loop().time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            # Convert to appropriate AgentError if needed
            if not isinstance(exc_val, AgentError):
                exc_val = create_error_from_exception(
                    exc_val,
                    context_id=self.context_id,
                    operation=self.operation,
                    **self.metadata
                )

            # Add timing information if available
            if self.start_time is not None:
                duration = asyncio.get_event_loop().time() - self.start_time
                exc_val.metadata["operation_duration_ms"] = duration * 1000

            # Re-raise the (possibly converted) exception
            raise exc_val
