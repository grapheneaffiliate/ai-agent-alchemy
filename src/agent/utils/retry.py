"""Retry/backoff helpers."""

from __future__ import annotations

import asyncio
import random
from typing import Awaitable, Callable, Iterable, Tuple, TypeVar

T = TypeVar("T")


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    jitter: float = 0.1,
    exceptions: Tuple[type[BaseException], ...] = (Exception,),
) -> T:
    """Retry an async operation with exponential backoff."""
    attempt = 0
    while True:
        try:
            return await operation()
        except exceptions as exc:
            attempt += 1
            if attempt > retries:
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            if jitter:
                delay += random.uniform(0, jitter)
            await asyncio.sleep(delay)
