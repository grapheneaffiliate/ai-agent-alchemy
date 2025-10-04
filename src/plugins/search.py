"""Plugin for web search using Google News RSS feed."""

import httpx
from typing import Dict, Any, List
import re
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

class SearchPlugin:
    """Web search using Google News RSS feed."""

    def __init__(self):
        self.rss_url = "https://news.google.com/rss/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.timeout = 15

    async def web_search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """Search using Google News RSS feed.
        
        Args:
            query: Search query string
            num_results: Maximum number of results to return (default: 10)
            
        Returns:
            Dict containing search results with titles, URLs, snippets, and sources
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                # Google News RSS search URL
                params = {
                    'q': query,
                    'hl': 'en-US',
                    'gl': 'US',
                    'ceid': 'US:en'
                }
                response = await client.get(self.rss_url, params=params)
                response.raise_for_status()

                # Parse RSS/XML
                root = ET.fromstring(response.content)
                search_results = []

                # Find all item elements in the RSS feed
                for idx, item in enumerate(root.findall('.//item')[:num_results]):
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    desc_elem = item.find('description')
                    pub_date_elem = item.find('pubDate')
                    source_elem = item.find('source')
                    
                    if title_elem is not None and title_elem.text:
                        title = title_elem.text.strip()
                        url = link_elem.text.strip() if link_elem is not None and link_elem.text else ''
                        
                        # Extract clean snippet from description
                        description = ''
                        if desc_elem is not None and desc_elem.text:
                            # Remove HTML tags from description
                            soup = BeautifulSoup(desc_elem.text, 'html.parser')
                            description = soup.get_text().strip()
                        
                        pub_date = pub_date_elem.text.strip() if pub_date_elem is not None and pub_date_elem.text else ''
                        source = source_elem.text.strip() if source_elem is not None and source_elem.text else 'Google News'
                        
                        search_results.append({
                            "doc_index": idx,
                            "title": title,
                            "url": url,
                            "snippet": description[:300] if description else title,
                            "source": source,
                            "published": pub_date
                        })

                return {
                    "result": {
                        "query": query,
                        "results": search_results,
                        "total": len(search_results),
                        "type": "google_news_rss"
                    },
                    "status": "success"
                }
        except Exception as e:
            return {"result": {"error": str(e), "query": query}, "status": "error"}

    @staticmethod
    def parse_citation(response: str, results: List[Dict]) -> str:
        """Handle citations in response.
        
        Args:
            response: Text response to add citations to
            results: List of search result dictionaries
            
        Returns:
            Response string with embedded citation tags
        """
        cited_response = response
        for doc_idx, doc in enumerate(results):
            snippet = doc.get('snippet', '')
            # Simple string replacement for citation (avoid regex issues with special chars)
            snippet_excerpt = snippet[:100]
            citation_tag = f"<citation index=\"{doc_idx},0\">{snippet_excerpt}</citation>"
            # Use simple string replace instead of regex to avoid escape issues
            cited_response = cited_response.replace(snippet_excerpt, citation_tag, 1)
        return cited_response

    async def execute(self, server: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search plugin commands via MCP interface.
        
        Args:
            server: Server name (should be 'search')
            tool_name: Name of the tool to execute
            args: Tool arguments including query and num_results
            
        Returns:
            Search results or error message
        """
        if server == 'search':
            if tool_name == 'web_search':
                return await self.web_search(args.get('query', ''), args.get('num_results', 10))
            else:
                return {"status": "error", "error": f"Unknown tool {tool_name}"}
        return {"status": "error", "error": "Unknown server"}


# Global instance
_search_instance: SearchPlugin = None


async def get_search_plugin() -> SearchPlugin:
    """Get or create search plugin instance."""
    global _search_instance
    if not _search_instance:
        _search_instance = SearchPlugin()
    return _search_instance
