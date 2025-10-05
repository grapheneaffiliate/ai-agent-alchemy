"""Content extraction and inspection helpers for the browser plugin."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ContentExtractionMixin:
    """Provide helpers for working with page content."""

    async def screenshot(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Capture a screenshot of the current page."""
        async with self._operation_span("screenshot", path=path) as span:  # type: ignore[attr-defined]
            await self.ensure_browser_ready()  # type: ignore[attr-defined]
            screenshot_bytes = await self.page.screenshot(full_page=True)  # type: ignore[attr-defined]
            span["bytes"] = len(screenshot_bytes)

            if path:
                with open(path, "wb") as file_handle:
                    file_handle.write(screenshot_bytes)
                span["status"] = "saved"
                return {"path": path, "status": "saved"}

            span["status"] = "captured"
            return {"data": screenshot_bytes.hex(), "status": "captured"}

    async def get_content(self) -> str:
        """Return the page content as text."""
        async with self._operation_span("get_content") as span:  # type: ignore[attr-defined]
            await self.ensure_browser_ready()  # type: ignore[attr-defined]
            content = await self.page.content()  # type: ignore[attr-defined]
            span["status"] = "success" if content else "empty"
            span["length"] = len(content) if content else 0
            return content

    async def extract_content_smart(self) -> Dict[str, Any]:
        """Extract the main content of the page, filtering boilerplate."""
        async with self._operation_span("extract_content") as span:  # type: ignore[attr-defined]
            await self.ensure_browser_ready()  # type: ignore[attr-defined]

            main_content = await self.page.evaluate(  # type: ignore[attr-defined]
                """
                () => {
                    const unwanted = document.querySelectorAll(
                        'nav, header, footer, aside, .ad, .advertisement,' +
                        '[role="complementary"], .sidebar, .menu, .navigation,' +
                        '[class*="ad-"], [class*="banner"], [id*="ad-"]'
                    );
                    unwanted.forEach(el => el.remove());

                    const main = document.querySelector(
                        'main, article, [role="main"], .content, #content, .main-content,' +
                        '[class*="article"], [class*="post-content"]'
                    );
                    const content = main || document.body;

                    const links = Array.from(content.querySelectorAll('a')).map(a => ({
                        text: (a.innerText || '').trim(),
                        href: a.href
                    })).filter(link => link.text && link.href && !link.href.startsWith('javascript:'));

                    const headings = Array.from(content.querySelectorAll('h1, h2, h3, h4, h5, h6')).map(h => ({
                        tag: h.tagName,
                        text: (h.innerText || '').trim()
                    })).filter(h => h.text);

                    const paragraphs = Array.from(content.querySelectorAll('p')).map(p => (p.innerText || '').trim());

                    const title = (document.querySelector('title') || {}).innerText || document.title || '';

                    return {
                        title,
                        text: paragraphs.join('\n\n'),
                        headings,
                        links
                    };
                }
                """
            )

            text_value = main_content.get("text", "") if isinstance(main_content, dict) else ""
            links = main_content.get("links", []) if isinstance(main_content, dict) else []
            span["status"] = "success" if text_value else "empty"
            span["links"] = len(links) if isinstance(links, list) else 0

            return {
                "url": self.page.url,  # type: ignore[attr-defined]
                "title": main_content.get("title", "") if isinstance(main_content, dict) else "",
                "text": text_value[:5000],
                "headings": (main_content.get("headings", [])[:20] if isinstance(main_content, dict) else []),
                "links": links[:50] if isinstance(links, list) else [],
                "status": "success" if text_value else "empty",
                "method": "playwright",
            }

    async def extract_text(self, selector: str) -> str:
        """Extract the text for a specific selector."""
        async with self._operation_span("extract_text", selector=selector) as span:  # type: ignore[attr-defined]
            await self.ensure_browser_ready()  # type: ignore[attr-defined]
            element = await self.page.query_selector(selector)  # type: ignore[attr-defined]
            if element:
                text_value = await element.text_content()
                span["status"] = "success" if text_value else "empty"
                span["length"] = len(text_value) if text_value else 0
                return text_value or ""
            span["status"] = "not_found"
            return ""

    async def get_links(self) -> List[Dict[str, str]]:
        """Return all anchors from the current page."""
        async with self._operation_span("get_links") as span:  # type: ignore[attr-defined]
            await self.ensure_browser_ready()  # type: ignore[attr-defined]
            links = await self.page.query_selector_all("a")  # type: ignore[attr-defined]
            result: List[Dict[str, str]] = []
            for link in links:
                href = await link.get_attribute("href")
                text = await link.text_content()
                if href:
                    result.append({"href": href, "text": text.strip() if text else ""})
            span["status"] = "success"
            span["count"] = len(result)
            return result


__all__ = ["ContentExtractionMixin"]
