#!/usr/bin/env python3
"""
Test script to verify all improvements have been successfully implemented.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_kokoro_tts_plugin():
    """Test that kokoro_tts plugin has the required execute method."""
    print('Testing kokoro_tts plugin interface...')
    try:
        from plugins.kokoro_tts import execute, KokoroTTS

        # Check if the class has the execute method
        tts = KokoroTTS()
        assert hasattr(tts, 'execute'), "KokoroTTS class missing execute method"
        assert callable(tts.execute), "execute method is not callable"

        print('Kokoro TTS plugin interface test passed')
        return True
    except Exception as e:
        print(f'Kokoro TTS plugin test failed: {e}')
        return False

def test_analysis_plugin():
    """Test that analysis plugin exposes async and sync interfaces."""
    import inspect
    import asyncio
    print('Testing analysis plugin async interface...')
    try:
        from plugins.analysis import ReplPlugin

        plugin = ReplPlugin()
        execute_method = getattr(plugin, 'execute')

        # Check that it's an async method (coroutine function)
        assert inspect.iscoroutinefunction(execute_method), "execute method should be asynchronous"

        async_result = asyncio.run(plugin.execute('analysis', 'execute_js', {'code': 'console.log("test")'}))
        assert async_result.get('status') == 'success', "async execute should return success status"

        # Synchronous helper should still work for compatibility
        sync_result = plugin.execute_sync('execute_js', {'code': 'console.log("test")'})
        assert sync_result.get('status') == 'success', "execute_sync should return success status"

        print('Analysis plugin async interface test passed')
        return True
    except Exception as e:
        print(f'Analysis plugin test failed: {e}')
        return False

def test_module_documentation():
    """Test that modules have proper documentation."""
    print('Testing module documentation...')
    try:
        import agent.api
        import agent.core

        # Check that modules have docstrings
        assert hasattr(agent.api, '__doc__'), "api module missing docstring"
        assert hasattr(agent.core, '__doc__'), "core module missing docstring"
        assert agent.api.__doc__ is not None, "api module docstring is None"
        assert agent.core.__doc__ is not None, "core module docstring is None"

        print('Module documentation test passed')
        return True
    except Exception as e:
        print(f'Module documentation test failed: {e}')
        return False

def test_type_hints():
    """Test that async functions have proper type hints."""
    print('Testing type hints...')
    try:
        import inspect

        # Import modules first
        import agent.api
        import agent.server

        # Check api.py
        api_source = inspect.getsource(agent.api.AgentAPI.generate_response)
        assert '-> str:' in api_source, "generate_response missing return type hint"

        # Check server.py functions have type hints
        server_functions = [
            agent.server.execute_tools_if_needed,
            agent.server.stream_response,
            agent.server.chat_completions
        ]

        for func in server_functions:
            source = inspect.getsource(func)
            assert '->' in source, f"{func.__name__} missing return type hint"

        print('Type hints test passed')
        return True
    except Exception as e:
        print(f'Type hints test failed: {e}')
        return False

def main():
    """Run all tests."""
    print('Starting MCP AI Agent improvement verification...\n')

    tests = [
        test_kokoro_tts_plugin,
        test_analysis_plugin,
        test_module_documentation,
        test_type_hints
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f'Results: {passed}/{total} tests passed')

    if passed == total:
        print('All improvements verified successfully!')
        return 0
    else:
        print('Some tests failed')
        return 1

if __name__ == '__main__':
    exit(main())
