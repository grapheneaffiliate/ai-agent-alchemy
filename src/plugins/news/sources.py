from __future__ import annotations

"""Source discovery utilities for the enhanced news system."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass
class NewsSource:
    """Represents a news source with credibility metrics."""

    name: str
    url: str
    rss_url: Optional[str]
    domain: str
    credibility_score: float
    last_updated: datetime
    article_count: int = 0
    topics: List[str] | None = None

    def __post_init__(self) -> None:
        if self.topics is None:
            self.topics = []


class DynamicSourceDiscovery:
    """Dynamically discover relevant news sources using the search plugin."""

    def __init__(self, search_plugin) -> None:
        self._search = search_plugin
        self._cache: dict[str, tuple[datetime, List[NewsSource]]] = {}
        self._cache_ttl = timedelta(hours=1)

    async def discover_sources(self, topic: str, max_sources: int = 10) -> List[NewsSource]:
        cache_key = f"sources_{topic}"
        cached = self._cache.get(cache_key)
        if cached:
            cached_time, sources = cached
            if datetime.now() - cached_time < self._cache_ttl:
                logger.info(
                    "enhanced_news.source_discovery.cached",
                    extra={"topic": topic, "count": len(sources)},
                )
                return sources

        logger.info(
            "enhanced_news.source_discovery.start",
            extra={"topic": topic, "max_sources": max_sources},
        )

        queries = [
            f'"{topic}" news site',
            f'"{topic}" official source',
            f'"{topic}" authoritative news',
            f'"{topic}" reputable source',
        ]

        discovered_domains: set[str] = set()
        collected: List[NewsSource] = []

        for query in queries:
            try:
                results = await self._search.web_search(query, num_results=20)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "enhanced_news.source_search_failed",
                    extra={"query": query, "error": str(exc)},
                )
                continue

            for result in results.get("results", [])[:10]:
                url = result.get("url") or ""
                domain = urlparse(url).netloc.lower()
                if not domain or domain in discovered_domains:
                    continue

                credibility = await self._assess_domain_credibility(domain, topic)
                if credibility <= 0.3:
                    continue

                discovered_domains.add(domain)
                collected.append(
                    NewsSource(
                        name=self._extract_site_name(domain),
                        url=f"https://{domain}",
                        rss_url=None,
                        domain=domain,
                        credibility_score=credibility,
                        last_updated=datetime.now(),
                        topics=[topic],
                    )
                )

                if len(collected) >= max_sources:
                    break
            if len(collected) >= max_sources:
                break

        collected.sort(key=lambda src: src.credibility_score, reverse=True)
        self._cache[cache_key] = (datetime.now(), collected[:max_sources])
        logger.info(
            "enhanced_news.source_discovery.completed",
            extra={"topic": topic, "count": len(collected[:max_sources])},
        )
        return collected[:max_sources]

    async def _assess_domain_credibility(self, domain: str, topic: str) -> float:
        score = 0.0
        reputable_domains = {
            "nytimes.com": 0.95,
            "washingtonpost.com": 0.95,
            "wsj.com": 0.95,
            "bbc.com": 0.95,
            "reuters.com": 0.95,
            "apnews.com": 0.95,
            "cnn.com": 0.85,
            "nbcnews.com": 0.85,
            "abcnews.go.com": 0.85,
            "cbsnews.com": 0.85,
            "usatoday.com": 0.80,
            "latimes.com": 0.80,
            "chicagotribune.com": 0.80,
            "bostonglobe.com": 0.80,
            "theguardian.com": 0.90,
            "aljazeera.com": 0.85,
            "dw.com": 0.85,
            "france24.com": 0.85,
            "techcrunch.com": 0.85,
            "arstechnica.com": 0.85,
            "theverge.com": 0.85,
            "venturebeat.com": 0.80,
            "axios.com": 0.80,
            "politico.com": 0.85,
            "bloomberg.com": 0.90,
            "economist.com": 0.90,
            "forbes.com": 0.80,
            "fortune.com": 0.80,
            "time.com": 0.85,
            "newsweek.com": 0.75,
            "npr.org": 0.90,
            "pbs.org": 0.90,
            "propublica.org": 0.90,
            "motherjones.com": 0.80,
            "slate.com": 0.80,
            "vox.com": 0.80,
            "buzzfeednews.com": 0.75,
            "huffpost.com": 0.75,
            "vice.com": 0.75,
            "qz.com": 0.75,
            "fastcompany.com": 0.75,
            "mashable.com": 0.70,
            "gizmodo.com": 0.70,
            "engadget.com": 0.75,
            "cnet.com": 0.75,
            "zdnet.com": 0.75,
            "pcmag.com": 0.75,
            "wired.com": 0.85,
            "technologyreview.com": 0.85,
            "spectrum.ieee.org": 0.85,
            "nature.com": 0.95,
            "science.org": 0.95,
            "scientificamerican.com": 0.85,
            "popsci.com": 0.75,
            "discovermagazine.com": 0.75,
        }

        if domain in reputable_domains:
            return reputable_domains[domain]

        if domain.endswith(".edu"):
            score += 0.8
        elif domain.endswith(".gov"):
            score += 0.9
        elif domain.endswith(".org"):
            score += 0.6

        if len(domain) > 10:
            score += 0.1

        fake_indicators = ("fake", "hoax", "satire", "joke", "meme")
        if any(indicator in domain for indicator in fake_indicators):
            score -= 0.5

        return min(score, 0.7)

    def _extract_site_name(self, domain: str) -> str:
        name = domain.replace("www.", "").split(".")[0]
        return name.title()
