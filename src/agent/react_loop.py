"""ReAct (Reasoning + Acting) loop for autonomous tool usage."""

import re
import json
import asyncio
import time
import logging
from typing import List, Tuple, Dict, Any, Optional
from collections import defaultdict
from .artifacts import ArtifactGenerator
try:
    from ..plugins.search import SearchPlugin  # For citation post-processing
except ImportError:
    # Fallback for when running as a module
    from src.plugins.search import SearchPlugin
from .react_responses import (
    format_health_analysis_response,
    format_comprehensive_analysis_response,
    format_enhancement_plan_response,
    format_intelligence_analysis_response,
)

logger = logging.getLogger(__name__)

class ToolMetrics:
    """Track tool usage metrics for monitoring and optimization."""

    def __init__(self):
        self.tool_usage = defaultdict(int)
        self.tool_times = defaultdict(list)
        self.tool_errors = defaultdict(int)
        self.session_start = time.time()

    def record_tool_use(self, tool_name: str, execution_time: float, success: bool):
        """Record tool usage statistics."""
        self.tool_usage[tool_name] += 1
        self.tool_times[tool_name].append(execution_time)
        if not success:
            self.tool_errors[tool_name] += 1

        logger.debug(
            'tool_usage_recorded',
            extra={'tool': tool_name, 'execution_time': round(execution_time, 3), 'success': success}
        )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        total_tools = sum(self.tool_usage.values())
        total_time = time.time() - self.session_start

        return {
            "session_duration": round(total_time, 2),
            "total_tool_calls": total_tools,
            "tool_breakdown": dict(self.tool_usage),
            "average_response_times": {
                tool: round(sum(times) / len(times), 2) if times else 0
                for tool, times in self.tool_times.items()
            },
            "error_rates": {
                tool: round(errors / count, 3) if count > 0 else 0
                for tool, (count, errors) in [
                    (tool, (self.tool_usage[tool], self.tool_errors[tool]))
                    for tool in self.tool_usage.keys()
                ]
            },
            "most_used_tools": sorted(
                self.tool_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }


async def execute_react_loop(
    user_input: str,
    agent: 'AgentAPI',
    plugin_executor: 'PluginExecutor',
    max_iterations: int = 3,  # Reduced from 5 for faster responses
    timeout: float = 30.0  # Overall timeout to prevent hanging
) -> Tuple[str, Optional[str]]:
    """
    Execute ReAct (Reasoning + Acting) loop with special handling for codebase queries.

    For codebase-related questions, proactively use LEANN tools instead of relying on LLM tool calls.
    """
    """
    Execute ReAct (Reasoning + Acting) loop for autonomous tool usage with timeout.

    Args:
        user_input: The user's query/message
        agent: AgentAPI instance for LLM calls
        plugin_executor: PluginExecutor for tool execution
        max_iterations: Maximum number of ReAct iterations (default: 3, faster than 5)
        timeout: Overall timeout in seconds to prevent hanging (default: 30s)

    Returns:
        Tuple of (final_response, artifact_html)
    """
    start_time = time.time()
    metrics = ToolMetrics()
    iteration = 0
    current_input = user_input
    final_response = None
    artifact_html = None

    logger.info(f"🔄 Starting ReAct loop (30s timeout) for: {user_input[:50]}...")

    while iteration < max_iterations:
        iteration += 1
        elapsed = time.time() - start_time

        # Check overall timeout
        if elapsed > timeout:
            logger.warning(f"⏰ ReAct loop timeout reached after {elapsed:.1f}s")
            if final_response is None:
                final_response = "Response timed out. Please try a simpler question."
            break

        logger.info(f"🔁 Iteration {iteration}/{max_iterations} ({elapsed:.1f}s elapsed)")

        try:
            # First iteration: special handling for time questions
            if iteration == 1 and is_time_question(user_input):
                logger.info("🕐 Time question detected - getting current time")
                try:
                    time_result = await asyncio.wait_for(
                        plugin_executor.execute('time', 'get_current_time', {}),
                        timeout=5.0
                    )
                    
                    if time_result.get('status') == 'success':
                        time_data = time_result.get('result', {})
                        final_response = f"The current time in Eastern Time (EST/EDT) is {time_data.get('time_12h', 'N/A')} on {time_data.get('day_of_week', '')} {time_data.get('date', '')}"
                        logger.info("✅ Time retrieved successfully")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ Time retrieval error: {str(e)}")
                    # Fall through to normal LLM response
            
            # First iteration: special handling for codebase questions with enhanced LEANN
            if iteration == 1 and is_codebase_question(user_input):
                logger.info("📚 Codebase question detected - routing to appropriate LEANN tool")
                try:
                    # Intelligent routing: determine which LEANN tool to use based on question
                    leann_tool, leann_args = route_to_leann_tool(user_input)

                    logger.info(f"🔧 Using LEANN tool: {leann_tool}")

                    # Execute the appropriate LEANN tool
                    codebase_analysis = await asyncio.wait_for(
                        plugin_executor.execute('leann', leann_tool, leann_args),
                        timeout=120.0  # Enhanced analysis needs time to build index on first run
                    )
                    
                    if codebase_analysis.get('status') == 'success':
                        analysis_data = codebase_analysis.get('analysis', {})

                        # Route response formatting based on which LEANN tool was used
                        if leann_tool == 'analyze_codebase_health':
                            final_response = format_health_analysis_response(analysis_data)
                            logger.info("✅ LEANN health analysis completed successfully")
                            break
                        elif leann_tool == 'generate_codebase_enhancement_plan':
                            # Extract the enhancement plan string directly
                            enhancement_plan = codebase_analysis.get('enhancement_plan', '')
                            if enhancement_plan:
                                final_response = enhancement_plan
                                logger.info("✅ LEANN enhancement plan completed successfully")
                            else:
                                final_response = format_enhancement_plan_response(analysis_data)
                                logger.info("✅ LEANN enhancement plan completed successfully (fallback)")
                            break
                        elif leann_tool == 'analyze_codebase_intelligence':
                            # Check if we got a specific answer from the intelligence toolkit
                            if 'overview' in analysis_data and analysis_data.get('method') == 'text_analysis_question_specific':
                                # Use the specific plugin answer directly
                                final_response = analysis_data['overview']
                                logger.info("✅ LEANN intelligence analysis completed successfully with specific answer")
                            else:
                                # Fall back to comprehensive analysis
                                final_response = format_comprehensive_analysis_response(analysis_data)
                                logger.info("✅ LEANN intelligence analysis completed successfully with comprehensive analysis")
                            break
                        elif leann_tool == 'comprehensive_self_improvement_analysis':
                            # Extract the enhancement plan string directly for comprehensive analysis too
                            enhancement_plan = codebase_analysis.get('enhancement_plan', '')
                            if enhancement_plan:
                                final_response = enhancement_plan
                                logger.info("✅ LEANN comprehensive analysis completed successfully")
                            else:
                                # Fallback to building comprehensive response from analysis data
                                diagnosis = analysis_data.get('comprehensive_diagnosis', {})
                                project_overview = diagnosis.get('project_overview', {}) if isinstance(diagnosis, dict) else {}
                                code_quality = diagnosis.get('code_quality', {}) if isinstance(diagnosis, dict) else {}
                                performance_analysis = diagnosis.get('performance', {}) if isinstance(diagnosis, dict) else {}
                                recommendations = diagnosis.get('recommendations', []) if isinstance(diagnosis, dict) else []

                                # Build comprehensive response
                                response_parts = ["# Enhanced Codebase Self-Improvement Analysis\n"]

                                # Project Overview
                                response_parts.append("## 📁 Project Overview")
                                response_parts.append(f"- **Total Files**: {project_overview.get('total_files', 0)}")
                                response_parts.append(f"- **Python Files**: {project_overview.get('python_files', 0)}")
                                response_parts.append(f"- **Test Files**: {project_overview.get('test_files', 0)}")
                                response_parts.append(f"- **Test Coverage**: {project_overview.get('test_coverage_ratio', 0):.1%}")
                                response_parts.append("")

                                # Code Quality
                                response_parts.append("## ⚡ Code Quality Metrics")
                                response_parts.append(f"- **Complexity Score**: {code_quality.get('complexity_score', 0):.1f}/100")
                                response_parts.append(f"- **Total Functions**: {code_quality.get('total_functions', 0)}")
                                response_parts.append(f"- **Functions/FILE**: {code_quality.get('avg_functions_per_file', 0):.1f}")
                                response_parts.append(f"- **Lines/FILE**: {code_quality.get('avg_lines_per_file', 0):.1f}")
                                response_parts.append("")

                                # Performance
                                response_parts.append("## 🚀 Performance Indicators")
                                perf_indicators = performance_analysis.get('performance_indicators', [])
                                if perf_indicators:
                                    for indicator in perf_indicators:
                                        response_parts.append(f"- ✓ {indicator}")
                                else:
                                    response_parts.append("- No specific performance indicators detected")
                                response_parts.append("")

                                # Recommendations
                                if recommendations:
                                    response_parts.append("## 💡 Enhancement Recommendations")
                                    for i, rec in enumerate(recommendations, 1):
                                        response_parts.append(f"{i}. {rec}")
                                    response_parts.append("")

                                # Self-Improvement Score
                                self_improvement_score = analysis_data.get('self_improvement_score', 0)
                                response_parts.append(f"## 🎖️ Self-Improvement Score: **{self_improvement_score}/100**")

                                # Provide insights based on score
                                if self_improvement_score >= 80:
                                    response_parts.append("**Excellent!** This codebase demonstrates world-class quality and practices.")
                                elif self_improvement_score >= 60:
                                    response_parts.append("**Good!** The codebase is well-structured with room for some improvements.")
                                elif self_improvement_score >= 40:
                                    response_parts.append("**Fair.** There are opportunities for significant improvement.")
                                else:
                                    response_parts.append("**Needs Attention.** Critical improvements are recommended.")

                                final_response = "\n".join(response_parts)
                                logger.info("✅ Enhanced LEANN self-improvement analysis completed successfully (fallback)")
                            break

                        # Check if we got LEANN's actual answer (new format)
                        if 'overview' in analysis_data:
                            final_response = analysis_data['overview']
                            logger.info("✅ LEANN codebase analysis completed successfully (semantic search)")
                            break

                        # Otherwise fallback format (old text analysis)
                        response_parts = ["# Agent Codebase Analysis\n"]

                        if 'architecture' in analysis_data:
                            arch = analysis_data['architecture']
                            response_parts.append(f"## Architecture")
                            response_parts.append(f"- Total files: {arch.get('total_files', 'N/A')}")
                            response_parts.append(f"- Python files: {arch.get('python_files', 'N/A')}")
                            response_parts.append(f"- Directories: {', '.join(arch.get('directories', []))}")
                            response_parts.append("")

                        if 'functions' in analysis_data:
                            funcs = analysis_data['functions']
                            if isinstance(funcs, dict):
                                response_parts.append(f"## Functions")
                                response_parts.append(f"- Total: {funcs.get('total', 'N/A')}")
                                response_parts.append(f"- Async: {funcs.get('async_functions', 'N/A')}")
                                response_parts.append(f"- {funcs.get('main_functions', '')}")
                                response_parts.append("")

                        if 'classes' in analysis_data:
                            classes = analysis_data['classes']
                            if isinstance(classes, dict):
                                response_parts.append(f"## Classes")
                                response_parts.append(f"- Total: {classes.get('total', 'N/A')}")
                                response_parts.append(f"- Main classes: {classes.get('main_classes', '')}")
                                response_parts.append("")

                        if 'patterns' in analysis_data and isinstance(analysis_data['patterns'], list):
                            response_parts.append(f"## Design Patterns")
                            for pattern in analysis_data['patterns']:
                                response_parts.append(f"- {pattern}")
                            response_parts.append("")

                        final_response = "\n".join(response_parts)
                        logger.info("✅ LEANN codebase analysis completed successfully (fallback)")
                        break
                    else:
                        logger.warning(f"⚠️ LEANN analysis failed: {codebase_analysis.get('error', 'Unknown error')}")
                        # Fall through to normal LLM response
                        
                except asyncio.TimeoutError:
                    logger.warning("⏰ LEANN analysis timed out, falling back to LLM")
                    # Fall through to normal LLM response
                except Exception as e:
                    logger.error(f"❌ LEANN analysis error: {str(e)}, falling back to LLM")
                    # Fall through to normal LLM response

            # First iteration: special handling for news questions
            if iteration == 1 and is_news_question(user_input):
                logger.info("📰 News question detected - fetching current news")
                try:
                    # Extract topic from user input
                    topic = extract_news_topic(user_input)
                    logger.info(f"📝 Topic extracted: '{topic}'")

                    # Try browser plugin as fallback for basic news
                    try:
                        basic_news_result = await asyncio.wait_for(
                            plugin_executor.execute('browser', 'get-news-smart', {
                                'topic': topic,
                                'max_articles': 5
                            }),
                            timeout=15.0
                        )

                        if basic_news_result.get('status') == 'success':
                            basic_news_data = basic_news_result.get('result', {})

                            articles = []
                            if basic_news_data.get('results'):
                                for result in basic_news_data['results']:
                                    articles.extend([
                                        {"headline": article['headline'], "url": article['url'], "summary": result.get('summary', '')}
                                        for article in result.get('top_articles', [])[:3]
                                    ])

                            if articles:
                                response = f"# Latest News About {topic.title()}\n\n"
                                for i, article in enumerate(articles[:5], 1):
                                    headline = article.get('headline', 'No headline')
                                    url = article.get('url', '#')
                                    summary = article.get('summary', '')
                                    response += f"## {i}. {headline}\n"
                                    if summary:
                                        response += f"{summary[:200]}...\n"
                                    if url and url != '#':
                                        response += f"[Read more]({url})\n"
                                    response += "\n"

                                final_response = response
                                logger.info("✅ Browser news retrieved successfully")
                                break
                            else:
                                logger.warning("⚠️ No news found in browser results")
                        else:
                            logger.warning(f"⚠️ Browser news failed: {basic_news_result.get('result', 'Unknown error')}")

                    except Exception as browser_e:
                        logger.warning(f"⚠️ Browser news failed: {str(browser_e)}")

                    # If no articles found, try backup news fetch
                    if not final_response:
                        try:
                            backup_news_result = await asyncio.wait_for(
                                plugin_executor.execute('news', 'get-news', {
                                    'topic': topic,
                                    'max_articles': 3
                                }),
                                timeout=10.0
                            )

                            if backup_news_result.get('status') == 'success':
                                backup_data = backup_news_result.get('result', {})

                                if backup_data.get('articles'):
                                    response = f"# Latest News About {topic.title()}\n\n"
                                    for i, article in enumerate(backup_data['articles'][:5], 1):
                                        headline = article.get('headline', 'No headline')
                                        url = article.get('url', '#')
                                        summary = article.get('summary', '')
                                        response += f"## {i}. {headline}\n"
                                        if summary:
                                            response += f"{summary[:200]}...\n"
                                        if url and url != '#':
                                            response += f"[Read more]({url})\n"
                                        response += "\n"

                                    final_response = response
                                    logger.info("✅ Backup news retrieved successfully")
                                    break
                                else:
                                    logger.warning("⚠️ No articles found in backup news")
                            else:
                                logger.warning(f"⚠️ Backup news failed: {backup_news_result.get('result', 'Unknown error')}")

                        except Exception as backup_e:
                            logger.warning(f"⚠️ Backup news failed: {str(backup_e)}")

                    # If still no news, provide basic message
                    if not final_response:
                        final_response = f"# Latest News About {topic.title()}\n\nNo news found for this topic. Try a different topic or check back later."
                        logger.warning("⚠️ No news retrieved from any source")
                        break

                except asyncio.TimeoutError:
                    logger.warning("⏰ News retrieval timed out, falling back to LLM")
                    final_response = f"I couldn't fetch current news about '{topic}'. Let me try to help with general information instead."
                    break
                except Exception as e:
                    logger.error(f"❌ News retrieval error: {str(e)}, falling back to LLM")
                    # Fall through to LLM response

            # Normal question processing
            if iteration == 1:
                try:
                    response = await asyncio.wait_for(
                        agent.generate_response(prompt=user_input),
                        timeout=15.0  # First attempt gets 15 seconds
                    )
                    final_response = response

                    # Check if response indicates tool usage needed (JSON or XML format)
                    has_tool_keywords = any(keyword in response.lower() for keyword in ['tool_call:', 'tool call:', 'TOOL_CALL:'])
                    has_xml_tools = '<invoke name="use_mcp_tool">' in response
                    
                    if has_tool_keywords or has_xml_tools:
                        tool_calls = extract_tool_calls(response)
                        if tool_calls:
                            logger.info(f"🔧 Found {len(tool_calls)} tool calls in first response, continuing to execute")
                            # Don't break - continue to tool execution
                        else:
                            logger.info(f"✅ First response sufficient, returning")
                            break
                    else:
                        # Response doesn't mention tools, return directly
                        logger.info(f"✅ First response sufficient, returning")
                        break

                except asyncio.TimeoutError:
                    logger.warning("⏰ First iteration timed out, continuing with tool-focused approach...")
                    current_input = f"{user_input}\n\nPlease use tools ONLY if absolutely necessary and keep your response concise."

            # Subsequent iterations with tools
            try:
                response = await asyncio.wait_for(
                    agent.generate_response(
                        prompt=current_input,
                        context=f"Quick response needed. Iteration {iteration}/{max_iterations}. Use tools only if required."
                    ),
                    timeout=10.0  # Subsequent calls get 10 seconds each
                )

                logger.info(f"📝 LLM Response (length: {len(response)})")
                final_response = response

                # Look for tool calls
                tool_calls = extract_tool_calls(response)

                if not tool_calls:
                    logger.info(f"✅ No tool calls found - finalizing response")
                    break

                logger.info(f"🔧 Found {len(tool_calls)} tool calls")

                # Execute tools with timeout
                tool_results = []
                for tool_call in tool_calls:
                    elapsed_after_call = time.time() - start_time
                    if elapsed_after_call > timeout:
                        logger.warning(f"⏰ Tool execution timeout reached")
                        break

                    logger.info(f"🔧 Executing: {tool_call['server']}.{tool_call['tool']}")

                    try:
                        result = await asyncio.wait_for(
                            plugin_executor.execute(tool_call['server'], tool_call['tool'], tool_call['args']),
                            timeout=5.0  # Tools get 5 seconds each
                        )
                        success = result.get('status') == 'success'
                        metrics.record_tool_use(f"{tool_call['server']}.{tool_call['tool']}", 0, success)

                        if success:
                            tool_results.append(result['result'])
                            logger.info(f"✅ Tool executed successfully")
                        else:
                            tool_results.append(f"Tool failed: {result.get('error', 'Unknown error')}")
                            logger.error(f"❌ Tool failed: {result.get('error', 'Unknown error')}")

                    except asyncio.TimeoutError:
                        tool_results.append("Tool execution timed out")
                        metrics.record_tool_use(f"{tool_call['server']}.{tool_call['tool']}", 0, False)
                        logger.warning(f"⏰ Tool timed out")
                    except Exception as e:
                        tool_results.append(f"Tool error: {str(e)}")
                        metrics.record_tool_use(f"{tool_call['server']}.{tool_call['tool']}", 0, False)
                        logger.error(f"❌ Tool exec exception: {str(e)}")

                if elapsed_after_call > timeout:
                    break

                # Build next iteration input
                current_input = f"User query: {user_input}\n\nTool results:\n" + "\n".join(tool_results) + "\n\nProvide final concise answer:"

            except asyncio.TimeoutError:
                logger.warning(f"⏰ Iteration {iteration} LLM call timed out")
                if final_response is None:
                    final_response = "I'm thinking too long. Please try asking a more specific question."
                break

        except Exception as e:
            logger.error(f"❌ ReAct iteration {iteration} failed: {str(e)}")
            if final_response is None:
                final_response = f"I encountered an error: {str(e)}"
            break

    # Print final metrics
    final_metrics = metrics.get_metrics_summary()
    total_time = time.time() - start_time
    logger.info(f"📊 Final metrics: {final_metrics['total_tool_calls']} tools used, {total_time:.1f}s total time")

    # Extract artifact from final response if present
    if final_response:
        artifact_html = ArtifactGenerator.extract_artifact(final_response)

    return final_response or "", artifact_html


def extract_tool_calls(response: str) -> List[Dict[str, Any]]:
    """
    Extract tool calls from LLM response.

    Looks for patterns like:
    TOOL_CALL: {"server": "browser", "tool": "extract_text", "args": {"selector": ".content"}}

    Also handles XML format: <invoke name="use_mcp_tool">...</invoke>
    """
    tool_calls = []

    # Look for TOOL_CALL JSON patterns
    json_patterns = [
        r'TOOL_CALL:\s*(\{.*?\})',
        r'tool_call:\s*(\{.*?\})',
        r'Tool Call:\s*(\{.*?\})'
    ]

    for pattern in json_patterns:
        matches = re.finditer(pattern, response, re.DOTALL)
        for match in matches:
            try:
                tool_json = match.group(1)
                tool_call = json.loads(tool_json)
                tool_calls.append(tool_call)
            except json.JSONDecodeError:
                logger.warning(f"⚠️  Could not parse tool JSON: {tool_json[:100]}...")
                continue

    # Look for XML tool call patterns
    xml_pattern = r'<invoke name="use_mcp_tool">.*?<parameter name="server_name">([^<]+)</parameter>.*?<parameter name="tool_name">([^<]+)</parameter>.*?<parameter name="arguments">([^<]+)</parameter>.*?</invoke>'
    xml_matches = re.finditer(xml_pattern, response, re.DOTALL)
    for match in xml_matches:
        try:
            server_name = match.group(1)
            tool_name = match.group(2)
            arguments_str = match.group(3)

            # Parse the arguments JSON
            args_dict = json.loads(arguments_str)

            tool_call = {
                "server": server_name,
                "tool": tool_name,
                "args": args_dict
            }
            tool_calls.append(tool_call)
            logger.info(f"✅ Parsed XML tool call: {server_name}.{tool_name}")
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"⚠️  Could not parse XML tool call: {str(e)}")
            continue

    return tool_calls


def is_time_question(user_input: str) -> bool:
    """
    Determine if the user is asking for the current time.

    Returns True for questions like:
    - "what time is it"
    - "current time"
    - "what's the time"
    """
    input_lower = user_input.lower()

    time_keywords = [
        'what time',
        "what's the time",
        'current time',
        'time is it',
        'tell me the time'
    ]

    return any(keyword in input_lower for keyword in time_keywords)


def is_news_question(user_input: str) -> bool:
    """
    Determine if the user is asking for current news or information that should be fetched from the web.

    Returns True for questions like:
    - "show me the latest news about"
    - "what's happening with"
    - "tell me about current events"
    - "show me news about"
    - "latest updates on"
    """
    input_lower = user_input.lower()

    news_keywords = [
        'latest news',
        'current news',
        'show me news',
        'tell me about current',
        'what\'s happening',
        'latest updates',
        'current situation',
        'breaking news',
        'what\'s new with',
        'recent developments on'
    ]

    # Check for news keywords OR explicit news question patterns
    has_news_keywords = any(keyword in input_lower for keyword in news_keywords)
    has_news_pattern = ('news' in input_lower or 'latest' in input_lower) and 'about' in input_lower

    return has_news_keywords or has_news_pattern


def extract_news_topic(user_input: str) -> str:
    """
    Extract the news topic from user input.

    Examples:
    - "show me news about US government shutdown" -> "US government shutdown"
    - "what's happening with climate change" -> "climate change"
    - "latest updates on artificial intelligence" -> "artificial intelligence"
    """
    input_lower = user_input.lower()

    # Remove common news question prefixes
    prefixes = [
        'show me news about',
        'show me the latest news about',
        'tell me about',
        'what\'s happening with',
        'what\'s new with',
        'latest updates on',
        'current news about',
        'news about',
        'about',
        'on'
    ]

    topic = user_input
    for prefix in prefixes:
        if input_lower.startswith(prefix):
            topic = user_input[len(prefix):].strip()
            break

    # Clean up the topic
    topic = topic.strip('.,!?')
    return topic if topic else 'general'


def is_codebase_question(user_input: str) -> bool:
    """
    Determine if the user question is about the agent's codebase or requires LEANN analysis.

    Returns True for questions like:
    - "tell me about your codebase"
    - "what code do you have"
    - "show me the implementation"
    - "how is your code structured"
    - "how is the plugin system implemented"
    - "assess your codebase"
    - "health check"
    - "analyze your health"
    - "improve yourself"
    - "self improvement"
    - "what plugins do you have"
    - "what capabilities do you have"
    - "what tools do you have"
    """
    input_lower = user_input.lower()

    codebase_keywords = [
        'codebase', 'code base', 'source code', 'sourcecode',
        'implementation', 'implemented', 'code structure', 'architecture',
        'modules', 'functions', 'classes', 'plugin', 'plugins',
        'how are you built', 'how do you work', 'how is', 'how does',
        'what code', 'your code', 'internal code',
        'assess', 'analyze', 'review', 'evaluate',
        'design pattern', 'system design', 'file structure',
        # Plugin and capability related keywords
        'what plugins', 'plugin list', 'plugins do you have', 'what plugins do you have',
        'how many plugins', 'what plugins', 'plugins are available', 'available plugins',
        'what tools do you have', 'what capabilities', 'what can you do', 'list your plugins',
        'show me your plugins', 'what plugins do', 'plugins you have', 'your plugins',
        'what tools are available', 'what capabilities do you have', 'what can you',
        'plugin capabilities', 'tool capabilities', 'available tools', 'plugin features'
    ]

    # Health and improvement keywords
    health_keywords = [
        'health check', 'health', 'status', 'diagnose', 'diagnosis',
        'improve yourself', 'self improvement', 'enhancement plan',
        'analysis', 'comprehensive analysis', 'improve your'
    ]

    return any(keyword in input_lower for keyword in codebase_keywords) or \
           any(keyword in input_lower for keyword in health_keywords)


def route_to_leann_tool(user_input: str) -> Tuple[str, Dict[str, Any]]:
    """
    Route user input to the appropriate LEANN tool based on question intent.

    Returns (tool_name, tool_args) tuple.

    Routing logic:
    - health check, analyze health -> analyze_codebase_health
    - improve yourself, enhancement plan -> generate_codebase_enhancement_plan
    - analyze code, intelligence -> analyze_codebase_intelligence
    - assess codebase, comprehensive -> comprehensive_self_improvement_analysis
    - ALL plugin-related questions -> analyze_codebase_intelligence (with specific question)
    """
    input_lower = user_input.lower()

    # Plugin-specific questions - route to intelligence with specific question
    plugin_keywords = [
        'what plugins', 'plugin list', 'plugins do you have', 'what plugins do you have',
        'how many plugins', 'what plugins', 'plugins are available', 'available plugins',
        'what tools do you have', 'what capabilities', 'what can you do', 'list your plugins',
        'show me your plugins', 'what plugins do', 'plugins you have', 'your plugins',
        'what tools are available', 'what capabilities do you have', 'what can you',
        'plugin capabilities', 'tool capabilities', 'available tools', 'plugin features'
    ]
    if any(word in input_lower for word in plugin_keywords):
        return 'analyze_codebase_intelligence', {'index_name': 'agent-code', 'question': 'What plugins are available in this codebase?'}

    # Health-specific questions
    if any(word in input_lower for word in ['health check', 'health', 'analyze your health', 'system health', 'diagnose health']):
        return 'analyze_codebase_health', {'index_name': 'agent-code'}

    # Enhancement plan questions
    if any(word in input_lower for word in ['enhancement plan', 'generate_codebase_enhancement_plan', 'improve yourself', 'self improvement']):
        return 'generate_codebase_enhancement_plan', {'index_name': 'agent-code'}

    # Intelligence/analysis questions
    if any(word in input_lower for word in ['analyze your code', 'analyze_codebase_intelligence', 'architectural analysis', 'code intelligence']):
        return 'analyze_codebase_intelligence', {'index_name': 'agent-code'}

    # Default to comprehensive self-improvement analysis
    return 'comprehensive_self_improvement_analysis', {'index_name': 'agent-code', 'question': user_input}


async def execute_codebase_analysis(user_input: str, plugin_executor: 'PluginExecutor') -> List[str]:
    """
    Execute LEANN tools to analyze the agent's codebase.

    Performs multiple LEANN operations to gather comprehensive codebase information.
    Uses shorter timeouts and better error handling to prevent hanging.
    """
    results = []

    try:
        # Advanced codebase analysis - reduce timeout from 10.0 to 8.0 seconds
        logger.info("🔍 Running LEANN codebase intelligence analysis...")
        analysis_result = await asyncio.wait_for(
            plugin_executor.execute('leann', 'analyze_codebase_intelligence', {}),
            timeout=8.0  # Reduced from 10.0 to allow time for other operations
        )
        if analysis_result.get('status') == 'success':
            # LEANN returns the full result object, not a nested 'result' field
            analysis_data = json.dumps(analysis_result, indent=2)
            results.append(f"Advanced Codebase Analysis:\n{analysis_data}")
        else:
            error_msg = analysis_result.get('error', 'Unknown error')
            logger.warning(f"⚠️ LEANN analysis failed with: {error_msg}")
            results.append(f"Advanced analysis failed: {error_msg}")

    except asyncio.TimeoutError:
        logger.warning("⚠️ LEANN analysis timed out")
        results.append("Advanced codebase analysis timed out (try simpler question)")
    except Exception as e:
        error_detail = f"{type(e).__name__}: {str(e)}"
        logger.warning(f"⚠️ LEANN analysis error: {error_detail}")
        results.append(f"Advanced codebase analysis error: {error_detail}")

    try:
        # Search for class definitions - reduce timeout from 5.0 to 3.0 seconds
        logger.info("🔍 Searching for class definitions...")
        classes_result = await asyncio.wait_for(
            plugin_executor.execute('leann', 'leann_search', {'query': 'class definitions', 'top_k': 5}),  # Reduced top_k
            timeout=3.0
        )
        if classes_result.get('status') == 'success':
            results.append(f"Class Definitions Found:\n{classes_result.get('results', 'No results found')}")
        else:
            results.append(f"Class search failed: {classes_result.get('error', 'Unknown error')}")

    except asyncio.TimeoutError:
        results.append("Class definitions search timed out")
    except Exception as e:
        results.append(f"Class definitions search error: {str(e)}")

    try:
        # Search for API endpoints - reduce timeout from 5.0 to 3.0 seconds
        logger.info("🔍 Searching for API endpoints...")
        api_result = await asyncio.wait_for(
            plugin_executor.execute('leann', 'leann_search', {'query': 'API endpoints def ', 'top_k': 5}),  # Reduced top_k, more specific query
            timeout=3.0
        )
        if api_result.get('status') == 'success':
            results.append(f"API Endpoints Found:\n{api_result.get('results', 'No results found')}")
        else:
            results.append(f"API search failed: {api_result.get('error', 'Unknown error')}")

    except asyncio.TimeoutError:
        results.append("API endpoints search timed out")
    except Exception as e:
        results.append(f"API endpoints search error: {str(e)}")

    try:
        # Search for configuration and setup - reduce timeout from 5.0 to 3.0 seconds
        logger.info("🔍 Searching for configuration and setup...")
        config_result = await asyncio.wait_for(
            plugin_executor.execute('leann', 'leann_search', {'query': 'configuration setup', 'top_k': 5}),  # Reduced top_k
            timeout=3.0
        )
        if config_result.get('status') == 'success':
            results.append(f"Configuration & Setup:\n{config_result.get('results', 'No results found')}")
        else:
            results.append(f"Configuration search failed: {config_result.get('error', 'Unknown error')}")

    except asyncio.TimeoutError:
        results.append("Configuration search timed out")
    except Exception as e:
        results.append(f"Configuration search error: {str(e)}")

    if not results:
        results.append("No codebase information could be retrieved using LEANN tools.")

    return results
