from typing import Any, Protocol


class NewsFetcher(Protocol):
    async def get_news(self, topic: str, max_articles: int) -> Any: ...


def get_news_fetch() -> NewsFetcher: ...
