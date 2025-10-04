"""
Integration tests for tool execution with refactored response helpers.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from agent.react_loop import ToolMetrics, route_to_leann_tool
from agent.react_responses import (
    format_health_analysis_response,
    format_comprehensive_analysis_response,
    format_enhancement_plan_response,
    format_intelligence_analysis_response,
)


class TestToolExecutionIntegration:
    """Integration tests for tool execution pipeline."""

    def test_tool_metrics_integration(self):
        """Test ToolMetrics integration with real tool calls."""
        metrics = ToolMetrics()

        # Simulate real tool usage pattern
        metrics.record_tool_use("browser.navigate", 1.2, True)
        metrics.record_tool_use("browser.screenshot", 0.8, True)
        metrics.record_tool_use("leann.analyze_codebase_health", 5.1, True)
        metrics.record_tool_use("news.get_enhanced_news", 2.3, False)

        summary = metrics.get_metrics_summary()

        assert summary['total_tool_calls'] == 4
        assert 'browser.navigate' in summary['tool_breakdown']
        assert 'leann.analyze_codebase_health' in summary['tool_breakdown']
        assert summary['tool_breakdown']['browser.navigate'] == 1
        assert summary['tool_breakdown']['leann.analyze_codebase_health'] == 1
        assert summary['error_rates']['news.get_enhanced_news'] == 1.0  # Failed tool

    def test_leann_tool_routing(self):
        """Test LEANN tool routing logic."""
        # Test plugin-specific questions
        plugin_question = "what plugins do you have"
        tool, args = route_to_leann_tool(plugin_question)
        assert tool == 'analyze_codebase_intelligence'
        assert 'question' in args
        assert 'plugin' in args['question'].lower()

        # Test health questions
        health_question = "analyze your health"
        tool, args = route_to_leann_tool(health_question)
        assert tool == 'analyze_codebase_health'

        # Test enhancement questions
        enhancement_question = "improve yourself"
        tool, args = route_to_leann_tool(enhancement_question)
        assert tool == 'generate_codebase_enhancement_plan'

    def test_response_formatters_with_real_data(self):
        """Test response formatters with realistic analysis data."""
        # Realistic test data based on actual codebase
        test_data = {
            'enhancement_plan': {
                'immediate_actions': [
                    'Review and optimize async operations',
                    'Add more integration tests'
                ],
                'short_term_improvements': [
                    'Enhance error handling in plugins',
                    'Improve logging and monitoring'
                ],
                'resource_estimation': {
                    'development_time': {
                        'immediate': '1-2 days',
                        'short_term': '1-2 weeks'
                    }
                },
                'success_metrics': {
                    'quality_metrics': {
                        'test_coverage': '85%',
                        'complexity_score': '75/100'
                    }
                }
            },
            'health_report': {
                'overall_health_score': 82.5,
                'health_status': 'good',
                'dimension_scores': {
                    'code_quality': 85.0,
                    'test_coverage': 78.0,
                    'documentation': 85.0,
                    'performance': 80.0
                },
                'strengths': [
                    'Good test coverage with comprehensive unit tests',
                    'Well-structured plugin architecture',
                    'Excellent logging and error handling'
                ],
                'critical_issues': [],
                'recommendations': [
                    'Consider adding more integration tests',
                    'Review and optimize async operations'
                ]
            },
            'project_overview': {
                'total_files': 147,
                'python_files': 89,
                'test_files': 23,
                'main_directories': ['src', 'tests', 'docs', 'config']
            },
            'code_quality': {
                'complexity_score': 72.0,
                'total_functions': 342,
                'avg_functions_per_file': 3.8
            }
        }

        # Test all formatters
        health_response = format_health_analysis_response(test_data)
        assert "82.5/100" in health_response
        assert "Good" in health_response
        assert "test coverage" in health_response.lower()

        comprehensive_response = format_comprehensive_analysis_response(test_data)
        assert "147" in comprehensive_response  # total files
        assert "342" in comprehensive_response  # total functions
        assert "test coverage" in comprehensive_response.lower()

        enhancement_response = format_enhancement_plan_response(test_data)
        assert "enhancement" in enhancement_response.lower()
        assert "immediate actions" in enhancement_response.lower()
        assert "short-term improvements" in enhancement_response.lower()

        intelligence_response = format_intelligence_analysis_response(test_data)
        assert "intelligence" in intelligence_response.lower()
        assert "architectural" in intelligence_response.lower()

    @pytest.mark.asyncio
    async def test_browser_operation_spans_integration(self):
        """Test browser operation spans in realistic scenarios."""
        from plugins.browser import BrowserPlugin

        browser = BrowserPlugin(headless=True)

        # Test that operation spans work correctly
        async with browser._operation_span('test_navigate', url='https://example.com') as span:
            span['status'] = 'success'
            span['response_code'] = 200

        # Verify span metadata is captured
        assert span['status'] == 'success'
        assert span['response_code'] == 200

    def test_enhanced_news_components_integration(self):
        """Test enhanced news components work together."""
        from plugins.enhanced_news_components import NewsAggregator, ContentIntelligence

        # Test content intelligence
        content_intel = ContentIntelligence()

        test_text = """
        Artificial intelligence researchers at Stanford University have made a breakthrough
        in machine learning algorithms. According to Dr. Jane Smith, the new approach
        improves performance by 40% while reducing computational costs.
        """

        key_points = content_intel.extract_key_points(test_text)
        entities = content_intel.extract_entities(test_text)
        sentiment = content_intel.assess_sentiment(test_text)

        assert len(key_points) > 0
        assert len(entities) > 0
        assert isinstance(sentiment, float)
        assert sentiment > 0  # Should be positive for this text

    def test_react_loop_imports(self):
        """Test that react loop can import all required components."""
        # This tests that all the imports in react_loop.py work correctly
        from agent.react_loop import (
            ToolMetrics,
            execute_react_loop,
            extract_tool_calls,
            is_time_question,
            is_news_question,
            is_codebase_question,
            route_to_leann_tool
        )

        from agent.react_responses import (
            format_health_analysis_response,
            format_comprehensive_analysis_response,
            format_enhancement_plan_response,
            format_intelligence_analysis_response,
        )

        # Verify all functions are callable
        assert callable(format_health_analysis_response)
        assert callable(format_comprehensive_analysis_response)
        assert callable(format_enhancement_plan_response)
        assert callable(format_intelligence_analysis_response)

        # Test basic functionality
        metrics = ToolMetrics()
        assert metrics.get_metrics_summary()['total_tool_calls'] == 0

        tool, args = route_to_leann_tool("test question")
        assert tool == 'comprehensive_self_improvement_analysis'
        assert 'question' in args


if __name__ == "__main__":
    # Run tests manually if called directly
    import asyncio

    async def run_tests():
        test_instance = TestToolExecutionIntegration()

        print("🧪 Running integration tests...")

        # Run sync tests
        test_instance.test_tool_metrics_integration()
        print("✅ Tool metrics integration test passed")

        test_instance.test_leann_tool_routing()
        print("✅ LEANN tool routing test passed")

        test_instance.test_response_formatters_with_real_data()
        print("✅ Response formatters test passed")

        test_instance.test_enhanced_news_components_integration()
        print("✅ Enhanced news components test passed")

        test_instance.test_react_loop_imports()
        print("✅ React loop imports test passed")

        await test_instance.test_browser_operation_spans_integration()
        print("✅ Browser operation spans test passed")

        print("\n🎉 All integration tests passed!")

    asyncio.run(run_tests())
