"""Session management for the modular browser plugin."""

from __future__ import annotations

import asyncio
import atexit
import gc
import logging
from typing import Any, Dict, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .runtime import cleanup_manager, operation_span, suppress_all_warnings


class BrowserSession:
    """Manage the lifecycle of a Playwright browser session."""

    def __init__(
        self,
        headless: bool = False,
        session_timeout: int = 300,
        retry_count: int = 3,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.headless = headless
        self.session_timeout = session_timeout
        self.retry_count = retry_count
        self.last_activity: Optional[float] = None

        self._lock = asyncio.Lock()
        self._logger = logger or logging.getLogger(__name__)

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._cleanup_registered = False

    @property
    def logger(self) -> logging.Logger:
        """Expose the logger used for structured browser logging."""
        return self._logger

    def _operation_span(self, operation: str, **details: Any):
        """Delegate to the runtime operation span helper."""
        return operation_span(self.logger, operation, **details)

    async def start(self) -> None:
        """Launch the browser with the configured anti-detection settings."""
        async with self._operation_span("start", headless=self.headless) as span:
            if self.playwright:
                span["status"] = "noop"
                return

            if not self._cleanup_registered:
                atexit.register(self._emergency_cleanup)
                self._cleanup_registered = True

            self.playwright = await async_playwright().start()

            self.browser = await self.playwright.firefox.launch(
                headless=self.headless,
                firefox_user_prefs={
                    "dom.webdriver.enabled": False,
                    "useAutomationExtension": False,
                    "general.platform.override": "Win32",
                    "general.useragent.override": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) "
                        "Gecko/20100101 Firefox/120.0"
                    ),
                },
            )

            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) "
                    "Gecko/20100101 Firefox/120.0"
                ),
                locale="en-US",
                timezone_id="America/New_York",
                permissions=["geolocation"],
                geolocation={"latitude": 40.7128, "longitude": -74.0060},
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": (
                        "text/html,application/xhtml+xml,application/xml;q=0.9,"  # noqa: E501
                        "image/webp,*/*;q=0.8"
                    ),
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Cache-Control": "max-age=0",
                },
            )

            await self.context.add_init_script(
                """
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin' }
                    ]
                });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
                window.chrome = { runtime: {} };
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications'
                        ? Promise.resolve({ state: Notification.permission })
                        : originalQuery(parameters)
                );
                """
            )

            self.page = await self.context.new_page()
            self.last_activity = asyncio.get_event_loop().time()

    async def close(self) -> None:
        """Close the browser and tear down associated resources."""
        async with self._operation_span("close") as span:
            with suppress_all_warnings():
                try:
                    if self.page:
                        try:
                            await self.page.close()
                        except Exception:
                            pass
                    if self.context:
                        try:
                            await self.context.close()
                        except Exception:
                            pass
                    if self.browser:
                        try:
                            await self.browser.close()
                        except Exception:
                            pass
                    if self.playwright:
                        try:
                            await self.playwright.stop()
                        except Exception:
                            pass

                    cleanup_manager.force_cleanup_all()
                    gc.collect()
                except Exception:
                    span["status"] = "partial"

            if not any([self.page, self.context, self.browser, self.playwright]):
                span["status"] = "noop"

            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

    def _emergency_cleanup(self) -> None:
        """Emergency cleanup hook invoked at process exit."""
        try:
            cleanup_manager.force_cleanup_all()
        except Exception:
            pass

    async def ensure_browser_ready(self) -> None:
        """Start the browser if needed and refresh activity timestamp."""
        async with self._lock:
            if not self.page or self.page.is_closed():
                await self.start()
            loop = asyncio.get_event_loop()
            self.last_activity = loop.time()


__all__ = ["BrowserSession"]
