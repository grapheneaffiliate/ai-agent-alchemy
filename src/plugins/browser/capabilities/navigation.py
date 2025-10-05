"""Navigation-related capabilities for the browser plugin."""

from __future__ import annotations

import asyncio
from typing import Any, Dict


class NavigationMixin:
    """Provide navigation helpers for Playwright pages."""

    async def navigate(self, url: str) -> Dict[str, Any]:  # type: ignore[override]
        """Navigate to the requested URL with retry and CAPTCHA detection."""
        async with self._operation_span("navigate", url=url) as span:  # type: ignore[attr-defined]
            await self.ensure_browser_ready()  # type: ignore[attr-defined]

            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"
                span["normalized_url"] = url

            for attempt in range(self.retry_count):  # type: ignore[attr-defined]
                span["attempt"] = attempt + 1
                try:
                    response = await self.page.goto(  # type: ignore[attr-defined]
                        url,
                        wait_until="domcontentloaded",
                        timeout=30000,
                    )

                    current_url = self.page.url.lower()  # type: ignore[attr-defined]
                    page_title = await self.page.title()  # type: ignore[attr-defined]

                    if any(token in current_url for token in ("sorry", "captcha", "challenge", "verify")):
                        span["status"] = "captcha_detected"
                        span["resolved_url"] = current_url
                        return {
                            "url": self.page.url,  # type: ignore[attr-defined]
                            "title": page_title,
                            "status": "captcha_detected",
                            "error": "CAPTCHA challenge detected. Try alternative sources or RSS feeds.",
                        }

                    span["status"] = "success"
                    span["status_code"] = response.status if response else None
                    span["resolved_url"] = self.page.url  # type: ignore[attr-defined]
                    return {
                        "url": self.page.url,  # type: ignore[attr-defined]
                        "title": page_title,
                        "status": "success",
                        "status_code": response.status if response else None,
                    }

                except Exception as exc:  # pragma: no cover - network dependent
                    self.logger.debug(  # type: ignore[attr-defined]
                        "browser.navigate.retry",
                        extra={"operation": "navigate", "attempt": attempt + 1, "error": str(exc)},
                    )
                    if attempt == self.retry_count - 1:  # type: ignore[attr-defined]
                        span["status"] = "error"
                        span["error"] = str(exc)
                        return {"url": url, "status": "error", "error": str(exc)}

                    await asyncio.sleep(2**attempt)
                    await self.close()  # type: ignore[attr-defined]
                    await self.start()  # type: ignore[attr-defined]

            return {"url": url, "status": "error", "error": "Navigation failed"}

    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> Dict[str, Any]:
        """Wait for a selector to appear on the page."""
        async with self._operation_span("wait_for_selector", selector=selector, timeout=timeout) as span:  # type: ignore[attr-defined]
            await self.ensure_browser_ready()  # type: ignore[attr-defined]
            await self.page.wait_for_selector(selector, timeout=timeout)  # type: ignore[attr-defined]
            span["status"] = "found"
            return {"selector": selector, "status": "found"}

    async def evaluate(self, script: str) -> Any:
        """Execute JavaScript within the active page context."""
        async with self._operation_span("evaluate") as span:  # type: ignore[attr-defined]
            await self.ensure_browser_ready()  # type: ignore[attr-defined]
            result = await self.page.evaluate(script)  # type: ignore[attr-defined]
            span["status"] = "success"
            return result


__all__ = ["NavigationMixin"]
