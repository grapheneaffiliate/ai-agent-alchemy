#!/usr/bin/env python3
"""
Test script to verify all improvements have been successfully implemented.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def _verify_kokoro_tts_plugin() -> None:
    """Ensure the kokoro_tts plugin exposes the expected interface."""
    print('Testing kokoro_tts plugin interface...')
    from plugins.kokoro_tts import KokoroTTS

    tts = KokoroTTS()
    assert hasattr(tts, 'execute'), 'KokoroTTS class missing execute method'
    assert callable(tts.execute), 'execute method is not callable'
    print('Kokoro TTS plugin interface test passed')


def test_kokoro_tts_plugin() -> None:
    _verify_kokoro_tts_plugin()


def _verify_analysis_plugin() -> None:
    """Ensure the analysis plugin supports async and sync execution."""
    import asyncio
    import inspect

    print('Testing analysis plugin async interface...')
    from plugins.analysis import ReplPlugin

    plugin = ReplPlugin()
    execute_method = getattr(plugin, 'execute')
    assert inspect.iscoroutinefunction(execute_method), 'execute method should be asynchronous'

    async_result = asyncio.run(plugin.execute('analysis', 'execute_js', {'code': 'console.log("test")'}))
    assert async_result.get('status') == 'success', 'async execute should return success status'

    sync_result = plugin.execute_sync('execute_js', {'code': 'console.log("test")'})
    assert sync_result.get('status') == 'success', 'execute_sync should return success status'
    print('Analysis plugin async interface test passed')


def test_analysis_plugin() -> None:
    _verify_analysis_plugin()


def _verify_module_documentation() -> None:
    """Ensure that key modules expose documentation strings."""
    print('Testing module documentation...')
    import agent.api
    import agent.core

    assert getattr(agent.api, '__doc__', None), 'api module missing docstring'
    assert getattr(agent.core, '__doc__', None), 'core module missing docstring'
    print('Module documentation test passed')


def test_module_documentation() -> None:
    _verify_module_documentation()


def _verify_type_hints() -> None:
    """Ensure important functions include return type hints."""
    print('Testing type hints...')
    import inspect

    import agent.api
    import agent.server

    api_source = inspect.getsource(agent.api.AgentAPI.generate_response)
    assert '-> str:' in api_source, 'generate_response missing return type hint'

    server_functions = [
        agent.server.execute_tools_if_needed,
        agent.server.stream_response,
        agent.server.chat_completions,
    ]

    for func in server_functions:
        source = inspect.getsource(func)
        assert '->' in source, f'{func.__name__} missing return type hint'
    print('Type hints test passed')


def test_type_hints() -> None:
    _verify_type_hints()


def main() -> int:
    """Run all verification checks when executed as a script."""
    print('Starting MCP AI Agent improvement verification...\n')

    checks = [
        ('Kokoro TTS plugin interface', _verify_kokoro_tts_plugin),
        ('Analysis plugin interface', _verify_analysis_plugin),
        ('Module documentation', _verify_module_documentation),
        ('Type hints', _verify_type_hints),
    ]

    passed = 0
    total = len(checks)

    for label, check in checks:
        try:
            check()
        except AssertionError as err:
            print(f'{label} test failed: {err}')
        except Exception as err:  # pragma: no cover - defensive guard for script mode
            print(f'{label} test encountered unexpected error: {err}')
        else:
            passed += 1
        print()

    print(f'Results: {passed}/{total} tests passed')

    if passed == total:
        print('All improvements verified successfully!')
        return 0

    print('Some tests failed')
    return 1


if __name__ == '__main__':
    sys.exit(main())
