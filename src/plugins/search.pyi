from typing import Any


class SearchPlugin:
    async def web_search(self, query: str, num_results: int) -> Any: ...
