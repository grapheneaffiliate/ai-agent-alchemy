#!/usr/bin/env python3
"""
Comprehensive MCP Tools Testing Suite
Tests all MCP-configured tools and identifies bugs for fixing.
"""

import asyncio
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, 'src')
sys.path.insert(0, '.')

# Import plugins directly
from src.plugins.time_utils import TimeUtils
from src.plugins.browser import BrowserPlugin
from src.plugins.news_fetch import NewsFetchPlugin
from src.plugins.crawl4ai_plugin import Crawl4AIPlugin
from src.plugins.search import SearchPlugin
from src.plugins.leann_plugin import LEANNPlugin
from src.plugins.enhanced_news import EnhancedNewsPlugin

class MCPToolsTester:
    """Comprehensive MCP tools tester."""

    def __init__(self):
        self.results = {
            "filesystem": {},
            "shell": {},
            "time": {},
            "browser": {},
            "news": {},
            "crawl4ai": {},
            "search": {},
            "leann": {},
            "enhanced-news": {}
        }
        self.session_state = {}

    async def run_all_tests(self):
        """Run comprehensive tests across all MCP tool servers."""
        print("🧪 MCP Tools Comprehensive Test Suite")
        print("=" * 50)

        # Test each server
        await self.test_filesystem_server()
        await self.test_shell_server()
        await self.test_time_server()
        await self.test_browser_server()
        await self.test_news_server()
        await self.test_crawl4ai_server()
        await self.test_search_server()
        await self.test_leann_server()
        await self.test_enhanced_news_server()

        # Print results
        self.print_final_report()

    async def test_filesystem_server(self):
        """Test filesystem tools: read-file and list-dir."""
        print("\n📁 Testing Filesystem Server...")
        try:
            # Test listing current directory
            await self.test_tool("filesystem", "list_dir", {"path": "."})

            # Test reading a file
            await self.test_tool("filesystem", "read_file", {"path": "README.md"})

        except Exception as e:
            self.results["filesystem"]["error"] = f"filesystem server error: {str(e)}"

    async def test_shell_server(self):
        """Test shell tools: run-command."""
        print("\n💻 Testing Shell Server...")
        try:
            # Test a simple command
            await self.test_tool("shell", "run_command", {"command": "echo hello", "requires_approval": False})

        except Exception as e:
            self.results["shell"]["error"] = f"shell server error: {str(e)}"

    async def test_time_server(self):
        """Test time tools: all time utilities."""
        print("\n⏰ Testing Time Server...")

        plugin = TimeUtils()

        try:
            # Test get-current-time
            result = plugin.get_current_time()
            self.results["time"]["get_current_time"] = {
                "status": "PASS" if result else "FAIL",
                "output": result
            }
        except Exception as e:
            self.results["time"]["get_current_time"] = {
                "status": "ERROR",
                "error": str(e)
            }

        try:
            # Test get-current-date
            result = plugin.get_current_date()
            self.results["time"]["get_current_date"] = {
                "status": "PASS" if result else "FAIL",
                "output": result
            }
        except Exception as e:
            self.results["time"]["get_current_date"] = {
                "status": "ERROR",
                "error": str(e)
            }

        try:
            # Test get-day-info
            result = plugin.get_day_info()
            self.results["time"]["get_day_info"] = {
                "status": "PASS" if result else "FAIL",
                "output": result
            }
        except Exception as e:
            self.results["time"]["get_day_info"] = {
                "status": "ERROR",
                "error": str(e)
            }

        try:
            # Test format-datetime
            result = plugin.format_datetime("%Y-%m-%d %H:%M:%S")
            self.results["time"]["format_datetime"] = {
                "status": "PASS" if result else "FAIL",
                "output": result
            }
        except Exception as e:
            self.results["time"]["format_datetime"] = {
                "status": "ERROR",
                "error": str(e)
            }

    async def test_browser_server(self):
        """Test browser tools: navigate, screenshot, extract-text etc."""
        print("\n🌐 Testing Browser Server...")

        plugin = BrowserPlugin()

        try:
            # Test navigate (to a simple HTML page)
            result = await plugin.navigate({"url": "https://httpbin.org/html"})
            self.results["browser"]["navigate"] = {
                "status": "PASS" if "success" in str(result).lower() else "FAIL",
                "output": result
            }
        except Exception as e:
            self.results["browser"]["navigate"] = {
                "status": "ERROR",
                "error": str(e)
            }

        try:
            # Test get_links
            result = await plugin.get_links({})
            self.results["browser"]["get_links"] = {
                "status": "PASS" if result else "FAIL",
                "output": result
            }
        except Exception as e:
            self.results["browser"]["get_links"] = {
                "status": "ERROR",
                "error": str(e)
            }

        try:
            # Test get_news_smart
            result = await plugin.get_news_smart({"topic": "ai"})
            self.results["browser"]["get_news_smart"] = {
                "status": "PASS" if result else "FAIL",
                "output": result
            }
        except Exception as e:
            self.results["browser"]["get_news_smart"] = {
                "status": "ERROR",
                "error": str(e)
            }

    async def test_news_server(self):
        """Test news tools."""
        print("\n📰 Testing News Server...")

        plugin = NewsFetchPlugin()

        try:
            # Test get-news
            result = await plugin.get_news({"topic": "technology", "max_articles": 3})
            self.results["news"]["get_news"] = {
                "status": "PASS" if result else "FAIL",
                "output": result
            }
        except Exception as e:
            self.results["news"]["get_news"] = {
                "status": "ERROR",
                "error": str(e)
            }

    async def test_crawl4ai_server(self):
        """Test crawl4ai tools."""
        print("\n🕷️ Testing Crawl4AI Server...")

        try:
            # Test crawl-url
            plugin = Crawl4AIPlugin()
            result = await plugin.crawl_url({"url": "https://news.ycombinator.com", "css_selector": ".titleline"})
            self.results["crawl4ai"]["crawl_url"] = {
                "status": "PASS" if result else "UNKNOWN",  # Unknown when crawl4ai not installed
                "output": "crawl4ai returned data" if result else "check if crawl4ai installed"
            }
        except Exception as e:
            self.results["crawl4ai"]["crawl_url"] = {
                "status": "ERROR",
                "error": str(e)
            }

    async def test_search_server(self):
        """Test search tools."""
        print("\n🔍 Testing Search Server...")

        try:
            plugin = SearchPlugin()
            # Test web_search
            result = await plugin.web_search({"query": "artificial intelligence", "num_results": 3})
            self.results["search"]["web_search"] = {
                "status": "PASS" if result else "FAIL",
                "output": result
            }
        except Exception as e:
            self.results["search"]["web_search"] = {
                "status": "ERROR",
                "error": str(e)
            }

    async def test_leann_server(self):
        """Test LEANN tools."""
        print("\n🧠 Testing LEANN Server...")

        try:
            plugin = LEANNPlugin()
            # Test analyze_codebase_intelligence
            result = await plugin.analyze_codebase_intelligence({
                "index_name": "agent-code"
            })
            self.results["leann"]["analyze_codebase_intelligence"] = {
                "status": "PASS" if result else "FAIL",
                "output": result
            }
        except Exception as e:
            self.results["leann"]["analyze_codebase_intelligence"] = {
                "status": "ERROR",
                "error": str(e)
            }

    async def test_enhanced_news_server(self):
        """Test enhanced-news tools."""
        print("\n📰 Testing Enhanced-News Server...")

        try:
            plugin = EnhancedNewsPlugin()
            # Test get-enhanced-news
            result = await plugin.get_enhanced_news({"topic": "python", "max_articles": 2})
            self.results["enhanced-news"]["get_enhanced_news"] = {
                "status": "PASS" if result else "FAIL",
                "output": result
            }
        except Exception as e:
            self.results["enhanced-news"]["get_enhanced_news"] = {
                "status": "ERROR",
                "error": str(e)
            }

        try:
            # Test discover-sources
            result = await plugin.discover_sources({"topic": "programming"})
            self.results["enhanced-news"]["discover_sources"] = {
                "status": "PASS" if result else "FAIL",
                "output": result
            }
        except Exception as e:
            self.results["enhanced-news"]["discover_sources"] = {
                "status": "ERROR",
                "error": str(e)
            }

    async def test_tool(self, server: str, tool_name: str, args: Dict[str, Any] = None):
        """Test a specific MCP tool."""
        if not args:
            args = {}

        self.results[server][tool_name] = {
            "status": "PENDING",
            "args": args
        }

        try:
            # For now, just simulate tool calls
            result = f"Simulated {server}:{tool_name} call with args {json.dumps(args)}"
            self.results[server][tool_name]["status"] = "SIMULATED"
            self.results[server][tool_name]["result"] = result
        except Exception as e:
            self.results[server][tool_name]["status"] = "ERROR"
            self.results[server][tool_name]["error"] = str(e)

    def print_final_report(self):
        """Print comprehensive test results."""
        print("\n" + "=" * 60)
        print("📊 MCP TOOLS TEST RESULTS SUMMARY")
        print("=" * 60)

        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0

        for server, tools in self.results.items():
            print(f"\n🏗️  {server.upper()} SERVER:")
            print("-" * 30)

            for tool_names in tools.items():
                if isinstance(tool_names, tuple):  # Handle dict items properly
                    tool_name, tool_data = tool_names

                    if isinstance(tool_data, dict):
                        status = tool_data.get("status", "UNKNOWN")
                        total_tests += 1

                        print(f"  {tool_name}: {status}")

                        if status == "PASS":
                            passed_tests += 1
                        elif status == "FAIL":
                            failed_tests += 1
                        elif status in ["ERROR", "UNKNOWN"]:
                            error_tests += 1

                        if "error" in tool_data:
                            print(f"    ❌ Error: {tool_data['error']}")

        print("\n" + "=" * 60)
        print(f"🎯 FINAL SCORE: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - System is fully functional!")
        else:
            print("⚠️  ISSUES FOUND - Need to fix bugs in failed tests")

        print(f"🔍 PASS: {passed_tests}, FAIL: {failed_tests}, ERROR: {error_tests}")


async def main():
    """Main test runner."""
    try:
        tester = MCPToolsTester()
        await tester.run_all_tests()
    except Exception as e:
        print(f"❌ Test suite failed with error: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
