"""Runtime utilities for the modular browser plugin."""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import threading
import time
import warnings
from contextlib import (
    asynccontextmanager,
    contextmanager,
    redirect_stderr,
    redirect_stdout,
)
from typing import Any, AsyncIterator, Dict, Iterator

# Apply the same aggressive warning suppression used by the legacy module
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*BaseSubprocessTransport.*")
warnings.filterwarnings("ignore", message=".*Event loop is closed.*")
warnings.filterwarnings("ignore", message=".*I/O operation on closed pipe.*")
warnings.filterwarnings("ignore", message=".*EPIPE.*")
warnings.filterwarnings("ignore", message=".*broken pipe.*")
warnings.filterwarnings("ignore", message=".*Node.js.*")
warnings.filterwarnings("ignore", message=".*RuntimeError.*")

for logger_name in ["asyncio", "playwright", "websockets", "urllib3", "selenium"]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class BrowserCleanupManager:
    """Cleanup helper responsible for terminating stray browser processes."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cleaned: set[int] = set()

    def cleanup_subprocess(self, pid: int) -> None:
        """Attempt to terminate a browser subprocess by PID."""
        with self._lock:
            if pid in self._cleaned:
                return
            self._cleaned.add(pid)

        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True,
                    timeout=5,
                )
            else:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        except (subprocess.TimeoutExpired, ProcessLookupError, OSError):
            # Process is already gone or cannot be terminated; ignore silently
            pass

    def force_cleanup_all(self) -> None:
        """Force cleanup of any browser-related processes still running."""
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["tasklist"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        lowered = line.lower()
                        if any(proc in lowered for proc in ("firefox", "chrome", "msedge")):
                            parts = line.strip().split()
                            if len(parts) > 1 and parts[1].isdigit():
                                self.cleanup_subprocess(int(parts[1]))
            else:
                result = subprocess.run(
                    ["pgrep", "-f", "firefox|chrome"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    for pid in result.stdout.strip().splitlines():
                        if pid.isdigit():
                            self.cleanup_subprocess(int(pid))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass


cleanup_manager = BrowserCleanupManager()


@contextmanager
def suppress_browser_warnings() -> Iterator[None]:
    """Context manager that filters noisy browser warnings from stdout/stderr."""

    old_stderr = sys.stderr
    old_stdout = sys.stdout

    class DevNull:
        def write(self, text: str) -> None:
            suppressed_tokens = (
                "BaseSubprocessTransport",
                "Event loop is closed",
                "EPIPE: broken pipe",
                "I/O operation on closed pipe",
                "RuntimeError: Event loop is closed",
                "Node.js",
                "throw er",
                "Error: EPIPE",
                "broken pipe",
                "write EPIPE",
                "PipeTransport",
                "dispatcherConnection",
                "Emitted 'error' event",
                "fileno",
                "call_soon",
                "_check_closed",
                "proactor_events",
                "windows_utils",
            )
            if not any(token in text for token in suppressed_tokens):
                old_stderr.write(text)

        def flush(self) -> None:  # pragma: no cover - passthrough flush
            old_stderr.flush()

    with redirect_stderr(DevNull()), redirect_stdout(DevNull()):
        yield

    sys.stderr = old_stderr
    sys.stdout = old_stdout


@contextmanager
def suppress_all_warnings() -> Iterator[None]:
    """Suppress all noisy warnings during teardown/cleanup."""

    old_stderr = sys.stderr
    old_stdout = sys.stdout

    class WarningFilter:
        def __init__(self, stream):
            self._stream = stream

        def write(self, text: str) -> None:
            suppressed_patterns = (
                "BaseSubprocessTransport",
                "Event loop is closed",
                "I/O operation on closed pipe",
                "EPIPE",
                "broken pipe",
                "Node.js",
                "RuntimeError",
                "throw er",
                "Error: EPIPE",
                "PipeTransport",
                "dispatcherConnection",
                "Emitted 'error' event",
                "fileno",
                "call_soon",
                "_check_closed",
                "proactor_events",
                "windows_utils",
                "Exception ignored in",
                "ValueError",
                "RuntimeWarning",
                "ResourceWarning",
                "DeprecationWarning",
                "PendingDeprecationWarning",
                "FutureWarning",
                "asyncio",
                "playwright",
                "websockets",
                "selenium",
                "urllib3",
            )
            lowered = text.lower()
            if not any(pattern.lower() in lowered for pattern in suppressed_patterns):
                self._stream.write(text)
                self._stream.flush()

        def flush(self) -> None:  # pragma: no cover - passthrough flush
            self._stream.flush()

    sys.stderr = WarningFilter(old_stderr)
    sys.stdout = WarningFilter(old_stdout)

    try:
        yield
    finally:
        sys.stderr = old_stderr
        sys.stdout = old_stdout


@asynccontextmanager
async def operation_span(
    operation_logger: logging.Logger,
    operation: str,
    **details: Any,
) -> AsyncIterator[Dict[str, Any]]:
    """Emit structured logs around an async operation and capture metadata."""

    start = time.perf_counter()
    metadata: Dict[str, Any] = {"status": "success"}
    log_details = {"operation": operation, **details}
    operation_logger.info("browser.%s.start", operation, extra=log_details)

    try:
        yield metadata
    except Exception:
        duration = time.perf_counter() - start
        operation_logger.exception(
            "browser.%s.error",
            operation,
            extra={**log_details, "status": "error", "duration": round(duration, 3)},
        )
        raise
    else:
        duration = time.perf_counter() - start
        status = metadata.get("status", "success")
        level = logging.INFO if status == "success" else logging.WARNING
        operation_logger.log(
            level,
            "browser.%s.%s",
            operation,
            status,
            extra={**log_details, "status": status, "duration": round(duration, 3)},
        )
