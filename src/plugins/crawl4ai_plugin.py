"""Crawl4AI integration plugin for advanced web scraping with clean output."""

import asyncio
from typing import Optional, Dict, Any, List


class Crawl4AIPlugin:
    """Crawl4AI web crawler with optimized markdown extraction."""
    
    def __init__(self):
        self.crawler = None
        
    async def initialize(self):
        """Initialize the async crawler."""
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig
            if self.crawler is None:
                # Configure browser for clean crawling
                browser_config = BrowserConfig(
                    headless=True,
                    viewport_width=1280,
                    viewport_height=720,
                    text_mode=True,  # Faster, text-focused
                    verbose=False
                )
                self.crawler = AsyncWebCrawler(config=browser_config)
                await self.crawler.__aenter__()
            return True
        except ImportError:
            print("crawl4ai not installed. Install with: pip install -U crawl4ai")
            return False
        except Exception as e:
            print(f"Error initializing Crawl4AI: {e}")
            return False
    
    async def crawl_url(
        self, 
        url: str,
        extract_markdown: bool = True,
        css_selector: Optional[str] = None,
        wait_for: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crawl a URL and extract clean, formatted content.
        
        Args:
            url: URL to crawl
            extract_markdown: Whether to extract markdown (always True for quality)
            css_selector: Optional CSS selector for specific content
            wait_for: Optional selector to wait for before crawling
            
        Returns:
            Dictionary with clean markdown, title, and metadata
        """
        if not await self.initialize():
            return {"error": "Crawl4AI not available"}
        
        try:
            from crawl4ai import CrawlerRunConfig, CacheMode
            from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
            from crawl4ai.content_filter_strategy import PruningContentFilter
            
            # Configure pruning filter for clean content
            prune_filter = PruningContentFilter(
                threshold=0.48,  # Balanced filtering
                threshold_type="dynamic",
                min_word_threshold=10  # Skip very short blocks
            )
            
            # Configure markdown generator with content filter
            md_generator = DefaultMarkdownGenerator(
                content_filter=prune_filter,
                options={
                    "ignore_links": False,  # Keep links but will be filtered
                    "body_width": 0,  # No wrapping
                    "skip_internal_links": True,  # Skip anchor links
                }
            )
            
            # Crawler configuration for clean output
            config = CrawlerRunConfig(
                # Content filtering
                word_count_threshold=15,
                excluded_tags=['nav', 'header', 'footer', 'aside', 'form', 'script', 'style'],
                
                # Link filtering
                exclude_external_links=False,  # Keep external but filter via markdown
                exclude_social_media_links=True,
                
                # Image filtering
                exclude_external_images=True,
                
                # Markdown generation
                markdown_generator=md_generator,
                
                # Performance
                cache_mode=CacheMode.BYPASS,
                page_timeout=30000,
                
                # CSS selector if provided
                css_selector=css_selector,
                wait_for=wait_for,
                
                verbose=False
            )
            
            result = await self.crawler.arun(url=url, config=config)
            
            if not result.success:
                return {
                    "error": result.error_message or "Crawl failed",
                    "url": url
                }
            
            # Extract clean markdown - prefer fit_markdown if available
            markdown_content = ""
            if hasattr(result, 'markdown') and result.markdown:
                # Result.markdown is MarkdownGenerationResult object
                if hasattr(result.markdown, 'fit_markdown') and result.markdown.fit_markdown:
                    # Use filtered markdown (cleanest)
                    markdown_content = result.markdown.fit_markdown
                elif hasattr(result.markdown, 'raw_markdown'):
                    # Fallback to raw markdown
                    markdown_content = result.markdown.raw_markdown
                else:
                    # Last fallback - convert to string
                    markdown_content = str(result.markdown)
            
            # Extract title from metadata
            title = "Untitled"
            if hasattr(result, 'metadata') and result.metadata:
                title = result.metadata.get('title', 'Untitled')
            
            # Clean up the markdown - remove excessive blank lines
            lines = markdown_content.split('\n')
            cleaned_lines = []
            blank_count = 0
            for line in lines:
                if not line.strip():
                    blank_count += 1
                    if blank_count <= 2:  # Max 2 consecutive blank lines
                        cleaned_lines.append(line)
                else:
                    blank_count = 0
                    cleaned_lines.append(line)
            
            markdown_content = '\n'.join(cleaned_lines).strip()
            
            # CRITICAL: Extract key facts from content to prevent hallucination
            extracted_facts = self._extract_key_facts(markdown_content)
            
            # Format extracted facts into a clear summary that LLM MUST read
            facts_summary = self._format_facts_summary(extracted_facts)
            
            return {
                "url": url,
                "title": title,
                "markdown": markdown_content,
                "extracted_facts": extracted_facts,  # Structured data
                "facts_summary": facts_summary,  # Human-readable format LLM must use
                "success": True,
                "status_code": result.status_code if hasattr(result, 'status_code') else 200,
                "word_count": len(markdown_content.split()),
                "cleaned": True  # Indicates this used content filtering
            }
            
        except Exception as e:
            import traceback
            return {
                "error": str(e),
                "url": url,
                "traceback": traceback.format_exc()
            }
    
    async def extract_structured(
        self,
        url: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract structured data from URL using schema.
        
        Args:
            url: URL to crawl
            schema: JSON schema for extraction
            
        Returns:
            Extracted structured data
        """
        if not await self.initialize():
            return {"error": "Crawl4AI not available"}
        
        try:
            from crawl4ai import CrawlerRunConfig, CacheMode
            from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
            
            extraction_strategy = JsonCssExtractionStrategy(schema)
            config = CrawlerRunConfig(
                extraction_strategy=extraction_strategy,
                cache_mode=CacheMode.BYPASS
            )
            
            result = await self.crawler.arun(url=url, config=config)
            
            return {
                "url": url,
                "data": result.extracted_content if hasattr(result, 'extracted_content') else {},
                "success": result.success if hasattr(result, 'success') else False
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "url": url
            }
    
    async def ask_question(
        self,
        url: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Ask a question about content at URL.
        
        Args:
            url: URL to analyze
            question: Question to ask about the content
            
        Returns:
            Answer and relevant context
        """
        # First crawl the URL with clean extraction
        crawl_result = await self.crawl_url(url)
        
        if crawl_result.get('error'):
            return crawl_result
        
        # Return the clean markdown for the AI to analyze
        return {
            "url": url,
            "question": question,
            "content": crawl_result.get('markdown', ''),
            "title": crawl_result.get('title', ''),
            "context": f"Content from {crawl_result.get('title', url)} for question: {question}"
        }
    
    def _extract_key_facts(self, markdown: str) -> Dict[str, Any]:
        """
        Extract key facts from markdown to prevent LLM hallucination.
        Returns structured data that must be used in the summary.
        """
        import re
        
        facts = {
            "location": None,
            "service_areas": [],
            "phone": None,
            "services": [],
            "company_name": None
        }
        
        # Extract company name from title or first heading
        title_match = re.search(r'^#+ (.+)$', markdown, re.MULTILINE)
        if title_match:
            facts["company_name"] = title_match.group(1).strip()
        
        # Extract location - look for city/state patterns
        # Northern Virginia pattern
        if "Northern Virginia" in markdown or "Northern VA" in markdown:
            facts["location"] = "Northern Virginia"
        # Specific cities
        elif "Greater Toronto Area" in markdown or "GTA" in markdown:
            facts["location"] = "Greater Toronto Area" 
        elif "Atlanta" in markdown and "metro" in markdown.lower():
            facts["location"] = "Atlanta metro area"
        
        # Extract service areas (cities/counties mentioned)
        area_patterns = [
            r'(?:Arlington|Alexandria|Fairfax|McLean|Centreville|Manassas|Vienna|Reston|Leesburg)\s+(?:VA|County)',
            r'(?:serving|serve|serves)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*)'
        ]
        for pattern in area_patterns:
            matches = re.findall(pattern, markdown)
            facts["service_areas"].extend(matches)
        
        # Extract phone number
        phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', markdown)
        if phone_match:
            facts["phone"] = phone_match.group(0)
        
        # Extract services - look for common patterns
        service_keywords = [
            "chimney sweep", "chimney clean", "chimney repair", "chimney inspection",
            "fireplace", "dryer vent", "masonry", "waterproofing", "crown repair",
            "damper repair", "chimney cap", "wood stove", "pellet stove"
        ]
        for keyword in service_keywords:
            if keyword.lower() in markdown.lower():
                # Capitalize first letter of each word
                service_name = keyword.title()
                if service_name not in facts["services"]:
                    facts["services"].append(service_name)
        
        return facts
    
    def _format_facts_summary(self, facts: Dict[str, Any]) -> str:
        """
        Format extracted facts into a clear text summary.
        This makes it harder for the LLM to ignore the actual data.
        """
        lines = ["=== EXTRACTED FACTS FROM WEBSITE (USE THESE EXACTLY) ==="]
        
        if facts.get("company_name"):
            lines.append(f"Company Name: {facts['company_name']}")
        
        if facts.get("location"):
            lines.append(f"Location: {facts['location']}")
            lines.append(f"⚠️ DO NOT say 'Toronto' or 'Atlanta' - the location is {facts['location']}")
        
        if facts.get("phone"):
            lines.append(f"Phone: {facts['phone']}")
        
        if facts.get("service_areas"):
            areas = ", ".join(facts['service_areas'][:5])  # First 5 areas
            lines.append(f"Service Areas: {areas}")
        
        if facts.get("services"):
            lines.append(f"Services Found: {', '.join(facts['services'][:10])}")
        
        lines.append("=== USE ONLY THE INFORMATION ABOVE IN YOUR SUMMARY ===")
        
        return "\n".join(lines)
    
    async def close(self):
        """Close the crawler."""
        if self.crawler:
            try:
                await self.crawler.__aexit__(None, None, None)
            except:
                pass
            self.crawler = None


# Singleton instance
_crawl4ai_instance: Optional[Crawl4AIPlugin] = None


async def get_crawl4ai() -> Crawl4AIPlugin:
    """Get or create Crawl4AI instance."""
    global _crawl4ai_instance
    if _crawl4ai_instance is None:
        _crawl4ai_instance = Crawl4AIPlugin()
    return _crawl4ai_instance


# MCP Plugin Interface
async def execute(server: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Crawl4AI plugin commands via MCP interface."""
    try:
        crawl4ai = await get_crawl4ai()

        # Handle MCP-configured tool names
        if tool_name == 'crawl-url':
            return await crawl4ai.crawl_url(
                url=args.get('url', ''),
                css_selector=args.get('css_selector'),
                extract_markdown=True
            )

        elif tool_name == 'ask-question':
            return await crawl4ai.ask_question(
                url=args.get('url', ''),
                question=args.get('question', '')
            )

        else:
            return {"status": "error", "error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        return {"status": "error", "error": str(e)}
