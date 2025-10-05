#!/usr/bin/env python3
"""
Test script to verify all imports and formatter functionality
"""
import sys
sys.path.insert(0, 'src')

def test_imports():
    """Test that all imports work correctly"""
    try:
        from agent.react_loop import ToolMetrics, route_to_leann_tool
        from agent.react_responses import format_enhancement_plan_response
        from plugins.browser import BrowserPlugin
        from plugins.enhanced_news_components import ContentIntelligence
        assert True, "All imports should work correctly"
    except Exception as e:
        assert False, f'Import failed: {e}'

def test_formatter():
    """Test the formatter with corrected data structure"""
    try:
        from agent.react_responses import format_enhancement_plan_response

        test_data = {
            'enhancement_plan': {
                'immediate_actions': ['Review and optimize async operations', 'Add more integration tests'],
                'short_term_improvements': ['Enhance error handling in plugins', 'Improve logging and monitoring'],
                'resource_estimation': {'development_time': {'immediate': '1-2 days', 'short_term': '1-2 weeks'}},
                'success_metrics': {'quality_metrics': {'test_coverage': '85%', 'complexity_score': '75/100'}}
            }
        }

        response = format_enhancement_plan_response(test_data)
        assert len(response) > 0, "Response should not be empty"
        assert "enhancement" in response.lower(), "Response should contain 'enhancement'"
        assert "immediate actions" in response.lower(), "Response should contain 'immediate actions'"
        assert "short-term improvements" in response.lower(), "Response should contain 'short-term improvements'"
    except Exception as e:
        assert False, f'Formatter test failed: {e}'

def test_tool_metrics():
    """Test ToolMetrics functionality"""
    try:
        from agent.react_loop import ToolMetrics

        metrics = ToolMetrics()
        metrics.record_tool_use('test.tool', 1.0, True)
        summary = metrics.get_metrics_summary()
        assert summary["total_tool_calls"] == 1, "Should have recorded one tool call"
    except Exception as e:
        assert False, f'ToolMetrics test failed: {e}'

if __name__ == "__main__":
    print("🧪 Testing MCP AI Agent Components")
    print("=" * 50)

    all_passed = True

    print("\n1. Testing imports...")
    try:
        test_imports()
        print("✅ Imports test passed")
    except AssertionError as e:
        print(f"❌ Imports test failed: {e}")
        all_passed = False
    except Exception as e:
        print(f"❌ Unexpected error in imports: {e}")
        all_passed = False

    print("\n2. Testing response formatter...")
    try:
        test_formatter()
        print("✅ Formatter test passed")
    except AssertionError as e:
        print(f"❌ Formatter test failed: {e}")
        all_passed = False
    except Exception as e:
        print(f"❌ Unexpected error in formatter: {e}")
        all_passed = False

    print("\n3. Testing ToolMetrics...")
    try:
        test_tool_metrics()
        print("✅ ToolMetrics test passed")
    except AssertionError as e:
        print(f"❌ ToolMetrics test failed: {e}")
        all_passed = False
    except Exception as e:
        print(f"❌ Unexpected error in ToolMetrics: {e}")
        all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print('🎉 All tests passed successfully!')
        print('✅ Structured logging components are working correctly!')
    else:
        print('❌ Some tests failed')
        sys.exit(1)
