"""Retry and backoff utilities for resilient async operations."""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type, TypeVar, Union

from .errors import AgentError, ErrorCategory, NetworkError, TimeoutError
from .logging_utils import get_logger, LogComponent

T = TypeVar('T')

logger = get_logger("retry_utils", LogComponent.AGENT)


class BackoffStrategy(str, Enum):
    """Backoff strategies for retry delays."""
    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    EXPONENTIAL_JITTER = "exponential_jitter"
    FIBONACCI = "fibonacci"


class RetryMode(str, Enum):
    """Retry modes for different scenarios."""
    FAIL_FAST = "fail_fast"  # No retries
    CONSERVATIVE = "conservative"  # Few retries, long delays
    AGGRESSIVE = "aggressive"  # Many retries, short delays
    ADAPTIVE = "adaptive"  # Adjust based on error types


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL_JITTER
    mode: RetryMode = RetryMode.CONSERVATIVE

    # Error-specific configurations
    retryable_errors: List[Type[Exception]] = field(default_factory=list)
    non_retryable_errors: List[Type[Exception]] = field(default_factory=list)

    # Jitter configuration
    jitter: bool = True
    jitter_max: float = 0.1

    # Timeout configuration
    timeout_per_attempt: Optional[float] = None
    total_timeout: Optional[float] = None

    def __post_init__(self) -> None:
        """Set default retryable errors if none specified."""
        if not self.retryable_errors:
            self.retryable_errors = [
                NetworkError,
                TimeoutError,
                asyncio.TimeoutError,
                ConnectionError,
                OSError,  # Covers various I/O errors
            ]


@dataclass
class RetryState:
    """State tracking for retry operations."""
    attempt: int = 0
    total_delay: float = 0.0
    last_error: Optional[Exception] = None
    start_time: float = field(default_factory=time.time)

    def should_retry(self, config: RetryConfig, error: Exception) -> bool:
        """Determine if operation should be retried."""
        # Check attempt limit
        if self.attempt >= config.max_attempts:
            return False

        # Check non-retryable errors
        for non_retryable in config.non_retryable_errors:
            if isinstance(error, non_retryable):
                return False

        # Check retryable errors (if specified)
        if config.retryable_errors:
            for retryable in config.retryable_errors:
                if isinstance(error, retryable):
                    return True
            return False

        # Default: retry on most exceptions except AgentError with high severity
        if isinstance(error, AgentError):
            return error.severity.value not in ['critical', 'high']

        return True

    def calculate_delay(self, config: RetryConfig) -> float:
        """Calculate delay for next retry attempt."""
        if config.strategy == BackoffStrategy.FIXED:
            delay = config.base_delay

        elif config.strategy == BackoffStrategy.LINEAR:
            delay = config.base_delay * (self.attempt + 1)

        elif config.strategy == BackoffStrategy.EXPONENTIAL:
            delay = config.base_delay * (2 ** self.attempt)

        elif config.strategy == BackoffStrategy.EXPONENTIAL_JITTER:
            base_delay = config.base_delay * (2 ** self.attempt)
            if config.jitter:
                jitter_amount = base_delay * config.jitter_max * random.random()
                delay = base_delay + jitter_amount
            else:
                delay = base_delay

        elif config.strategy == BackoffStrategy.FIBONACCI:
            # Fibonacci sequence: 1, 1, 2, 3, 5, 8, 13...
            fib_values = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
            index = min(self.attempt, len(fib_values) - 1)
            delay = config.base_delay * fib_values[index]

        else:
            delay = config.base_delay

        # Apply maximum delay cap
        delay = min(delay, config.max_delay)

        # Check total timeout
        if config.total_timeout:
            remaining_time = config.total_timeout - (time.time() - self.start_time)
            delay = min(delay, max(0, remaining_time))

        return delay


def is_retryable_error(error: Exception, config: RetryConfig) -> bool:
    """Check if an error should be retried based on configuration."""
    state = RetryState()

    # Check non-retryable errors first
    for non_retryable in config.non_retryable_errors:
        if isinstance(error, non_retryable):
            return False

    # Check retryable errors (if specified)
    if config.retryable_errors:
        for retryable in config.retryable_errors:
            if isinstance(error, retryable):
                return True
        return False

    # Default retry logic
    if isinstance(error, AgentError):
        return error.severity.value not in ['critical', 'high']

    return True


async def retry_async(
    func: Callable[..., Awaitable[T]],
    config: Optional[RetryConfig] = None,
    *args: Any,
    **kwargs: Any
) -> T:
    """Execute async function with retry logic."""
    if config is None:
        config = RetryConfig()

    state = RetryState()

    while True:
        try:
            # Check total timeout
            if config.total_timeout:
                elapsed = time.time() - state.start_time
                if elapsed >= config.total_timeout:
                    logger.warning(
                        "Total timeout exceeded, aborting retries",
                        operation="retry_async",
                        extra_fields={"total_timeout": config.total_timeout}
                    )
                    if state.last_error:
                        raise state.last_error
                    raise TimeoutError(
                        f"Operation timed out after {config.total_timeout}s",
                        timeout_seconds=config.total_timeout,
                    )

            # Execute the function with per-attempt timeout if configured
            if config.timeout_per_attempt:
                try:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=config.timeout_per_attempt
                    )
                    return result
                except asyncio.TimeoutError as e:
                    state.last_error = TimeoutError(
                        f"Attempt {state.attempt + 1} timed out after {config.timeout_per_attempt}s",
                        timeout_seconds=config.timeout_per_attempt
                    )
                    if not state.should_retry(config, state.last_error):
                        raise state.last_error
            else:
                result = await func(*args, **kwargs)
                return result

        except Exception as e:
            state.attempt += 1
            state.last_error = e

            # Check if we should retry
            if not state.should_retry(config, e):
                logger.error(
                    f"Non-retryable error after {state.attempt} attempts",
                    operation="retry_async",
                    extra_fields={
                        "error_type": type(e).__name__,
                        "attempts": state.attempt
                    }
                )
                raise e

            # Calculate delay and wait
            delay = state.calculate_delay(config)
            state.total_delay += delay

            logger.warning(
                f"Attempt {state.attempt} failed, retrying in {delay".2f"}s",
                operation="retry_async",
                extra_fields={
                    "error_type": type(e).__name__,
                    "attempt": state.attempt,
                    "max_attempts": config.max_attempts,
                    "delay_seconds": delay,
                    "total_delay": state.total_delay
                }
            )

            await asyncio.sleep(delay)


def retry_sync(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None,
    *args: Any,
    **kwargs: Any
) -> T:
    """Execute sync function with retry logic."""
    if config is None:
        config = RetryConfig()

    state = RetryState()

    while True:
        try:
            # Check total timeout
            if config.total_timeout:
                elapsed = time.time() - state.start_time
                if elapsed >= config.total_timeout:
                    logger.warning(
                        "Total timeout exceeded, aborting retries",
                        operation="retry_sync",
                        extra_fields={"total_timeout": config.total_timeout}
                    )
                    if state.last_error:
                        raise state.last_error
                    raise TimeoutError(
                        f"Operation timed out after {config.total_timeout}s",
                        timeout_seconds=config.total_timeout
                    )

            # Execute with timeout if configured
            if config.timeout_per_attempt:
                result = asyncio.run(
                    asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, func, *args, **kwargs
                        ),
                        timeout=config.timeout_per_attempt
                    )
                )
                return result
            else:
                # Run in thread pool for sync functions
                result = asyncio.run(
                    asyncio.get_event_loop().run_in_executor(
                        None, func, *args, **kwargs
                    )
                )
                return result

        except Exception as e:
            state.attempt += 1
            state.last_error = e

            # Check if we should retry
            if not state.should_retry(config, e):
                logger.error(
                    f"Non-retryable error after {state.attempt} attempts",
                    operation="retry_sync",
                    extra_fields={
                        "error_type": type(e).__name__,
                        "attempts": state.attempt
                    }
                )
                raise e

            # Calculate delay and wait
            delay = state.calculate_delay(config)
            state.total_delay += delay

            logger.warning(
                f"Attempt {state.attempt} failed, retrying in {delay".2f"}s",
                operation="retry_sync",
                extra_fields={
                    "error_type": type(e).__name__,
                    "attempt": state.attempt,
                    "max_attempts": config.max_attempts,
                    "delay_seconds": delay,
                    "total_delay": state.total_delay
                }
            )

            time.sleep(delay)


# Decorator versions
def with_retry_async(config: Optional[RetryConfig] = None):
    """Decorator for async functions with retry logic."""
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_async(func, config, *args, **kwargs)
        return wrapper
    return decorator


def with_retry_sync(config: Optional[RetryConfig] = None):
    """Decorator for sync functions with retry logic."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return retry_sync(func, config, *args, **kwargs)
        return wrapper
    return decorator


# Pre-configured retry strategies for common scenarios
def network_retry_config() -> RetryConfig:
    """Retry config optimized for network operations."""
    return RetryConfig(
        max_attempts=5,
        base_delay=1.0,
        max_delay=30.0,
        strategy=BackoffStrategy.EXPONENTIAL_JITTER,
        mode=RetryMode.CONSERVATIVE,
        retryable_errors=[
            NetworkError,
            TimeoutError,
            asyncio.TimeoutError,
            ConnectionError,
            OSError,
        ],
        total_timeout=300.0,  # 5 minutes max
    )


def plugin_retry_config() -> RetryConfig:
    """Retry config optimized for plugin operations."""
    return RetryConfig(
        max_attempts=3,
        base_delay=2.0,
        max_delay=20.0,
        strategy=BackoffStrategy.EXPONENTIAL_JITTER,
        mode=RetryMode.CONSERVATIVE,
        retryable_errors=[
            NetworkError,
            TimeoutError,
            ConnectionError,
        ],
        total_timeout=60.0,  # 1 minute max
    )


def fast_retry_config() -> RetryConfig:
    """Retry config for fast, lightweight operations."""
    return RetryConfig(
        max_attempts=2,
        base_delay=0.1,
        max_delay=1.0,
        strategy=BackoffStrategy.FIXED,
        mode=RetryMode.FAIL_FAST,
        total_timeout=5.0,
    )


# Circuit breaker pattern for repeated failures
class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: Type[Exception] = Exception


class CircuitBreaker:
    """Circuit breaker for preventing cascade failures."""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitBreakerState.CLOSED

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        if self.state != CircuitBreakerState.OPEN:
            return False

        if self.last_failure_time is None:
            return True

        return (time.time() - self.last_failure_time) >= self.config.recovery_timeout

    def _record_success(self) -> None:
        """Record successful operation."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0

    def _record_failure(self) -> None:
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN

    async def call(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        """Execute function through circuit breaker."""
        # Check if we should attempt reset
        if self._should_attempt_reset():
            self.state = CircuitBreakerState.HALF_OPEN

        # Reject if circuit is open
        if self.state == CircuitBreakerState.OPEN:
            raise RuntimeError("Circuit breaker is OPEN - service unavailable")

        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except self.config.expected_exception as e:
            self._record_failure()
            raise e


# Convenience function for creating circuit breaker with retry
async def retry_with_circuit_breaker(
    func: Callable[..., Awaitable[T]],
    retry_config: Optional[RetryConfig] = None,
    circuit_config: Optional[CircuitBreakerConfig] = None,
    *args: Any,
    **kwargs: Any
) -> T:
    """Execute function with both retry and circuit breaker protection."""
    if retry_config is None:
        retry_config = RetryConfig()
    if circuit_config is None:
        circuit_config = CircuitBreakerConfig()

    circuit_breaker = CircuitBreaker(circuit_config)

    async def _protected_call() -> T:
        return await circuit_breaker.call(func, *args, **kwargs)

    return await retry_async(_protected_call, retry_config)
