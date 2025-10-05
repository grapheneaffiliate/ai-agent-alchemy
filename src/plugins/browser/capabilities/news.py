"""News-specific helpers for the browser plugin."""

from __future__ import annotations

from typing import Any, Dict, List


class NewsMixin:
    """Provide higher-level helpers tailored to news aggregation."""

    async def get_news_smart(self, topic: str = "ai", max_articles: int = 5) -> Dict[str, Any]:
        """Gather news articles using direct navigation and smart extraction."""
        async with self._operation_span("get_news", topic=topic, max_articles=max_articles) as span:  # type: ignore[attr-defined]
            results: List[Dict[str, Any]] = []
            errors: List[str] = []

            url_safe_topic = topic.lower().replace(" ", "-")
            gov_keywords = [
                "government",
                "shutdown",
                "federal",
                "congress",
                "president",
                "politics",
                "policy",
                "trump",
                "biden",
                "white house",
            ]

            if any(keyword in topic.lower() for keyword in gov_keywords):
                direct_sites = [
                    "https://www.cnn.com/politics/",
                    "https://www.foxnews.com/politics/",
                    "https://www.nbcnews.com/politics/",
                    f"https://www.nytimes.com/search?query={topic.replace(' ', '%20')}",
                    "https://www.washingtonpost.com/politics/",
                    "https://apnews.com/hub/politics",
                    "https://www.reuters.com/world/us/",
                ]
            else:
                direct_sites = [
                    f"https://techcrunch.com/tag/{url_safe_topic}/",
                    f"https://arstechnica.com/{topic}/",
                    f"https://www.theverge.com/search?q={topic}",
                ]

            span["candidate_sources"] = len(direct_sites)

            for site_url in direct_sites:
                try:
                    nav_result = await self.navigate(site_url)  # type: ignore[attr-defined]

                    if nav_result.get("status") == "captcha_detected":
                        errors.append(f"{site_url}: CAPTCHA detected")
                        continue

                    if nav_result.get("status") != "success":
                        errors.append(f"{site_url}: Navigation failed")
                        continue

                    extracted = await self.extract_content_smart()  # type: ignore[attr-defined]

                    if extracted.get("status") == "success" and extracted.get("links"):
                        results.append(
                            {
                                "source": site_url,
                                "title": extracted.get("title", ""),
                                "top_articles": [
                                    {
                                        "headline": link.get("text", "")[:100],
                                        "url": link.get("href", ""),
                                    }
                                    for link in extracted["links"][:max_articles]
                                    if link.get("text") and len(link.get("text", "")) > 10
                                ],
                                "summary": extracted.get("text", "")[:800],
                                "all_headings": extracted.get("headings", [])[:10],
                            }
                        )
                        break

                    errors.append(f"{site_url}: No content extracted")

                except Exception as exc:  # pragma: no cover - network dependent
                    errors.append(f"{site_url}: {exc}")
                    continue

            span["status"] = "success" if results else "empty"
            span["sources"] = len(results)
            span["errors"] = len(errors)

            return {
                "topic": topic,
                "results": results,
                "sources_tried": len(direct_sites),
                "successful": len(results),
                "errors": errors if not results else [],
                "method": "direct_site_with_extraction",
            }


__all__ = ["NewsMixin"]
