"""Interaction helpers for the browser plugin."""

from __future__ import annotations

from typing import Dict


class InteractionMixin:
    """Provide user interaction helpers such as click and fill."""

    async def click(self, selector: str) -> Dict[str, str]:
        """Click an element on the current page."""
        async with self._operation_span("click", selector=selector) as span:  # type: ignore[attr-defined]
            await self.ensure_browser_ready()  # type: ignore[attr-defined]
            await self.page.click(selector)  # type: ignore[attr-defined]
            span["status"] = "clicked"
            return {"selector": selector, "status": "clicked"}

    async def fill(self, selector: str, text: str) -> Dict[str, str]:
        """Fill an input element with text."""
        async with self._operation_span("fill", selector=selector) as span:  # type: ignore[attr-defined]
            await self.ensure_browser_ready()  # type: ignore[attr-defined]
            await self.page.fill(selector, text)  # type: ignore[attr-defined]
            span["status"] = "filled"
            return {"selector": selector, "status": "filled"}


__all__ = ["InteractionMixin"]
