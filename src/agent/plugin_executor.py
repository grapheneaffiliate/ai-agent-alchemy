"""Plugin executor for calling actual tool implementations."""

from typing import Any, Dict
import json
from dataclasses import asdict

from .errors import PluginExecutionError
from .logging_utils import get_context_id, get_logger, with_fields
from .utils.retry import retry_async

logger = get_logger(__name__)
_RETRYABLE_SERVERS = {"browser", "news", "crawl4ai", "search", "enhanced-news"}


class PluginExecutor:
    """Execute tools by dispatching to plugin implementations."""

    def __init__(self):
        self.plugins = {}
        self._init_plugins()

    def _init_plugins(self):
        """Initialize available plugins."""
        # Time plugin
        try:
            from src.plugins.time_utils import get_time_plugin
            time_plugin = get_time_plugin()
            self.plugins['time'] = time_plugin
        except ImportError:
            pass

        # Browser plugin  
        try:
            from src.plugins.browser import get_browser
            self.plugins['browser'] = get_browser
        except ImportError:
            pass
        
        # News fetch plugin (HTTP-based, no browser)
        try:
            from src.plugins.news_fetch import get_news_fetch
            self.plugins['news'] = get_news_fetch
        except ImportError:
            pass
        
        # Crawl4AI plugin (advanced web scraping)
        try:
            from src.plugins.crawl4ai_plugin import get_crawl4ai
            self.plugins['crawl4ai'] = get_crawl4ai
        except ImportError:
            pass
        
        # Search plugin
        try:
            from src.plugins.search import SearchPlugin
            self.plugins['search'] = SearchPlugin
        except ImportError:
            pass

        # Enhanced news plugin (intelligent news aggregation)
        try:
            from src.plugins.enhanced_news import get_enhanced_news
            self.plugins['enhanced-news'] = get_enhanced_news
        except ImportError:
            pass

        # LEANN vector database plugin
        try:
            from src.plugins.leann_plugin import LeannPlugin
            self.plugins['leann'] = LeannPlugin()
        except ImportError:
            pass

        # Analysis plugin (JS REPL)
        try:
            from src.plugins.analysis import ReplPlugin
            self.plugins['analysis'] = ReplPlugin
        except ImportError:
            pass

    async def execute(self, server: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by server and tool name."""
        context_id = get_context_id()

        async def dispatch() -> Dict[str, Any]:
            if server == 'time':
                return await self._execute_time_tool(tool_name, args)
            if server == 'browser':
                return await self._execute_browser_tool(tool_name, args)
            if server == 'news':
                return await self._execute_news_tool(tool_name, args)
            if server == 'crawl4ai':
                return await self._execute_crawl4ai_tool(tool_name, args)
            if server == 'search':
                return await self._execute_search_tool(tool_name, args)
            if server == 'enhanced-news':
                return await self._execute_enhanced_news_tool(tool_name, args)
            if server == 'leann':
                return await self._execute_leann_tool(tool_name, args)
            reason = f"Server '{server}' not implemented"
            self._fail(server, tool_name, reason)

        try:
            if server in _RETRYABLE_SERVERS:
                result = await retry_async(dispatch)
            else:
                result = await dispatch()
        except PluginExecutionError:
            raise
        except Exception as exc:
            logger.exception(
                "plugin execution failed",
                extra=with_fields(server=server, tool=tool_name, context_id=context_id),
            )
            raise PluginExecutionError(server=server, tool=tool_name, reason=str(exc), context_id=context_id) from exc

        status = result.get("status")
        if status != "success":
            reason = result.get("error", str(status))
            logger.warning(
                "plugin returned non-success status",
                extra=with_fields(server=server, tool=tool_name, context_id=context_id, status=status, reason=reason),
            )
            raise PluginExecutionError(server=server, tool=tool_name, reason=reason, context_id=context_id)

        logger.info(
            "plugin executed",
            extra=with_fields(server=server, tool=tool_name, context_id=context_id),
        )
        return result

    def _fail(self, server: str, tool_name: str, reason: str) -> None:
        """Normalize plugin failures."""
        context_id = get_context_id()
        logger.error(
            "plugin execution error",
            extra=with_fields(server=server, tool=tool_name, context_id=context_id, reason=reason),
        )
        raise PluginExecutionError(server=server, tool=tool_name, reason=reason)

    async def _execute_time_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute time-related tools."""
        time_plugin = self.plugins.get('time')
        if not time_plugin:
            self._fail('time', tool_name, "Time plugin not available")

        # Handle both hyphen and underscore naming conventions
        tool_name = tool_name.replace('-', '_')

        if tool_name == 'get_current_time':
            result = time_plugin.get_current_time()
            return {"result": result, "status": "success"}
        elif tool_name == 'get_current_date':
            result = time_plugin.get_current_date()
            return {"result": result, "status": "success"}
        elif tool_name == 'get_day_info':
            result = time_plugin.get_day_info()
            return {"result": result, "status": "success"}
        elif tool_name == 'format_datetime':
            format_string = args.get('format_string', '%Y-%m-%d %H:%M:%S')
            result = time_plugin.format_datetime(format_string)
            return {"result": result, "status": "success"}
        else:
            self._fail('time', tool_name, f"Unknown time tool: {tool_name}")

    async def _execute_browser_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute browser-related tools."""
        browser_getter = self.plugins.get('browser')
        if not browser_getter:
            self._fail('browser', tool_name, "Browser plugin not available")

        browser = await browser_getter()

        if tool_name == 'navigate':
            url = args.get('url')
            if not url:
                self._fail('browser', tool_name, "URL required for navigate")
            result = await browser.navigate(url)
            return {"result": result, "status": "success"}
        elif tool_name == 'screenshot':
            path = args.get('path')
            result = await browser.screenshot(path)
            return {"result": result, "status": "success"}
        elif tool_name == 'click':
            selector = args.get('selector')
            if not selector:
                self._fail('browser', tool_name, "Selector required for click")
            result = await browser.click(selector)
            return {"result": result, "status": "success"}
        elif tool_name == 'fill':
            selector = args.get('selector')
            text = args.get('text')
            if not selector or not text:
                self._fail('browser', tool_name, "Selector and text required for fill")
            result = await browser.fill(selector, text)
            return {"result": result, "status": "success"}
        elif tool_name == 'extract-text':
            selector = args.get('selector')
            if not selector:
                self._fail('browser', tool_name, "Selector required for extract")
            result = await browser.extract_text(selector)
            return {"result": result, "status": "success"}
        elif tool_name == 'get-links':
            result = await browser.get_links()
            return {"result": result, "status": "success"}
        elif tool_name == 'extract-content-smart':
            result = await browser.extract_content_smart()
            return {"result": result, "status": "success"}
        elif tool_name == 'get-news-smart':
            topic = args.get('topic', 'ai')
            max_articles = int(args.get('max_articles', 5))
            result = await browser.get_news_smart(topic, max_articles)
            return {"result": result, "status": "success"}
        else:
            return {"error": f"Unknown browser tool: {tool_name}"}
    
    async def _execute_news_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute news-related tools (HTTP-based, no browser)."""
        news_getter = self.plugins.get('news')
        if not news_getter:
            return {"error": "News plugin not available"}
        
        news = news_getter()
        
        if tool_name == 'get-news':
            topic = args.get('topic', 'ai')
            max_articles = int(args.get('max_articles', 5))
            result = await news.get_news(topic, max_articles)
            return {"result": result, "status": "success"}
        else:
            return {"error": f"Unknown news tool: {tool_name}"}
    
    async def _execute_crawl4ai_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Crawl4AI advanced web scraping tools."""
        crawl4ai_getter = self.plugins.get('crawl4ai')
        if not crawl4ai_getter:
            return {"error": "Crawl4AI plugin not available"}
        
        crawler = await crawl4ai_getter()
        
        if tool_name == 'crawl_url':
            url = args.get('url')
            if not url:
                return {"error": "URL required for crawl_url"}
            css_selector = args.get('css_selector')
            result = await crawler.crawl_url(url, css_selector=css_selector)
            return {"result": result, "status": "success"}
        elif tool_name == 'ask_question':
            url = args.get('url')
            question = args.get('question')
            if not url or not question:
                return {"error": "URL and question required"}
            result = await crawler.ask_question(url, question)
            return {"result": result, "status": "success"}
        else:
            return {"error": f"Unknown crawl4ai tool: {tool_name}"}
    
    async def _execute_search_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search-related tools."""
        search_plugin_class = self.plugins.get('search')
        if not search_plugin_class:
            return {"error": "Search plugin not available"}
        
        # Instantiate SearchPlugin
        search = search_plugin_class()
        
        if tool_name == 'web_search':
            query = args.get('query', '')
            num_results = int(args.get('num_results', 10))
            result = await search.web_search(query, num_results)
            return result
        else:
            return {"error": f"Unknown search tool: {tool_name}"}

    async def _execute_enhanced_news_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute enhanced news tools (intelligent news aggregation)."""
        enhanced_news_getter = self.plugins.get('enhanced-news')
        if not enhanced_news_getter:
            return {"error": "Enhanced news plugin not available"}

        # Get the enhanced news instance
        enhanced_news = await enhanced_news_getter()

        if tool_name == 'get_enhanced_news':
            topic = args.get('topic', 'ai')
            max_articles = int(args.get('max_articles', 10))
            result = await enhanced_news.get_enhanced_news(topic, max_articles)
            return {"result": result, "status": "success"}
        elif tool_name == 'discover_sources':
            topic = args.get('topic', 'ai')
            max_sources = int(args.get('max_sources', 10))
            sources = await enhanced_news.source_discovery.discover_sources(topic, max_sources)
            return {"result": {"sources": [asdict(source) for source in sources], "count": len(sources)}, "status": "success"}
        else:
            return {"error": f"Unknown enhanced news tool: {tool_name}"}

    async def _execute_leann_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LEANN vector database tools."""
        leann_plugin = self.plugins.get('leann')
        if not leann_plugin:
            return {"error": "LEANN plugin not available"}

        # Call the plugin's execute method directly
        result = await leann_plugin.execute('leann', tool_name, args)
        return result
