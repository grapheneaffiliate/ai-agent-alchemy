"""Modular browser plugin exposing the MCP-compatible interface."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .capabilities import (
    ContentExtractionMixin,
    InteractionMixin,
    NavigationMixin,
    NewsMixin,
)
from .session import BrowserSession

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class BrowserPlugin(
    NewsMixin,
    ContentExtractionMixin,
    InteractionMixin,
    NavigationMixin,
    BrowserSession,
):
    """Compose session management with capability mixins."""

    def __init__(
        self,
        headless: bool = False,
        session_timeout: int = 300,
        retry_count: int = 3,
        plugin_logger: Optional[logging.Logger] = None,
    ) -> None:
        resolved_logger = plugin_logger or logger
        super().__init__(
            headless=headless,
            session_timeout=session_timeout,
            retry_count=retry_count,
            logger=resolved_logger,
        )


_browser_instance: Optional[BrowserPlugin] = None


async def get_browser(headless: bool = False) -> BrowserPlugin:
    """Return a singleton browser instance."""
    global _browser_instance
    if not _browser_instance:
        _browser_instance = BrowserPlugin(headless=headless)
    return _browser_instance


async def close_browser() -> None:
    """Dispose of the singleton browser instance."""
    global _browser_instance
    if _browser_instance:
        await _browser_instance.close()
        _browser_instance = None


async def execute(server: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute browser commands via the MCP tool interface."""
    try:
        logger.info("browser.execute.start", extra={"tool": tool_name})
        browser = await get_browser(headless=args.get("headless", True))

        if tool_name == "navigate":
            return await browser.navigate(args.get("url", ""))
        if tool_name == "screenshot":
            return await browser.screenshot(args.get("path"))
        if tool_name == "click":
            return await browser.click(args.get("selector", ""))
        if tool_name == "fill":
            return await browser.fill(args.get("selector", ""), args.get("text", ""))
        if tool_name == "extract-text":
            selector = args.get("selector", "")
            text = await browser.extract_text(selector)
            return {"status": "success", "text": text, "selector": selector}
        if tool_name == "get-links":
            links = await browser.get_links()
            return {"status": "success", "links": links}
        if tool_name == "get-news-smart":
            return await browser.get_news_smart(
                topic=args.get("topic", "ai"),
                max_articles=args.get("max_articles", 5),
            )

        if tool_name == "browser_navigate":
            return await browser.navigate(args.get("url", ""))
        if tool_name == "browser_screenshot":
            return await browser.screenshot(args.get("path"))
        if tool_name == "browser_get_content":
            content = await browser.get_content()
            return {"status": "success", "content": content}
        if tool_name == "browser_extract_content":
            return await browser.extract_content_smart()
        if tool_name == "browser_get_news":
            return await browser.get_news_smart(
                topic=args.get("topic", "ai"),
                max_articles=args.get("max_articles", 5),
            )
        if tool_name == "browser_click":
            return await browser.click(args.get("selector", ""))
        if tool_name == "browser_fill":
            return await browser.fill(args.get("selector", ""), args.get("text", ""))
        if tool_name == "browser_close":
            await close_browser()
            return {"status": "success", "message": "Browser closed"}

        return {"status": "error", "error": f"Unknown tool: {tool_name}"}

    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("browser.execute.error", extra={"tool": tool_name})
        return {"status": "error", "error": str(exc)}


__all__ = ["BrowserPlugin", "get_browser", "close_browser", "execute"]
