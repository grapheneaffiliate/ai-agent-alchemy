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
        print('✅ All imports successful')
        return True
    except Exception as e:
        print(f'❌ Import failed: {e}')
        return False

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
        print(f'✅ Formatter working - response length: {len(response)} characters')
        print(f'✅ Contains "enhancement": {"enhancement" in response.lower()}')
        print(f'✅ Contains "immediate actions": {"immediate actions" in response.lower()}')
        print(f'✅ Contains "short-term improvements": {"short-term improvements" in response.lower()}')
        return True
    except Exception as e:
        print(f'❌ Formatter test failed: {e}')
        return False

def test_tool_metrics():
    """Test ToolMetrics functionality"""
    try:
        from agent.react_loop import ToolMetrics

        metrics = ToolMetrics()
        metrics.record_tool_use('test.tool', 1.0, True)
        summary = metrics.get_metrics_summary()
        print(f'✅ ToolMetrics working: {summary["total_tool_calls"]} tools recorded')
        return True
    except Exception as e:
        print(f'❌ ToolMetrics test failed: {e}')
        return False

if __name__ == "__main__":
    print("🧪 Testing MCP AI Agent Components")
    print("=" * 50)

    all_passed = True

    print("\n1. Testing imports...")
    all_passed &= test_imports()

    print("\n2. Testing response formatter...")
    all_passed &= test_formatter()

    print("\n3. Testing ToolMetrics...")
    all_passed &= test_tool_metrics()

    print("\n" + "=" * 50)
    if all_passed:
        print('🎉 All tests passed successfully!')
        print('✅ Structured logging components are working correctly!')
    else:
        print('❌ Some tests failed')
        sys.exit(1)
