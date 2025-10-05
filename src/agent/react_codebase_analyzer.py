"""Codebase analysis functions for ReAct loop."""

import asyncio
import json
import logging
from typing import List

logger = logging.getLogger(__name__)


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
