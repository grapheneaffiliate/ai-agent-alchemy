#!/usr/bin/env python3

"""
Simple verification script for the improvements made.
"""

import sys
import os
import asyncio
import inspect

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, 'src'))

def verify_analysis_plugin():
    """Verify that analysis plugin has async integration."""
    print("Verifying analysis plugin async integration...")

    try:
        from plugins.analysis import ReplPlugin

        plugin = ReplPlugin()

        # Check async execute method exists and is coroutine function
        assert hasattr(plugin, 'execute'), "Missing execute method"
        assert inspect.iscoroutinefunction(plugin.execute), "execute should be async"

        # Check sync helper exists
        assert hasattr(plugin, 'execute_sync'), "Missing execute_sync method"
        assert callable(plugin.execute_sync), "execute_sync should be callable"

        # Test async execution
        async def test_async():
            result = await plugin.execute('test', 'execute_js', {'code': 'console.log("test")'})
            return result

        result = asyncio.run(test_async())
        assert result.get('status') == 'success', "Async execution failed"

        # Test sync execution
        sync_result = plugin.execute_sync('execute_js', {'code': 'console.log("test")'})
        assert sync_result.get('status') == 'success', "Sync execution failed"

        print("✓ Analysis plugin async integration verified")
        return True

    except Exception as e:
        print(f"✗ Analysis plugin verification failed: {e}")
        return False

def verify_api_return_annotation():
    """Verify that API generate_response has return annotation."""
    print("Verifying API return annotation...")

    try:
        from agent.api import AgentAPI

        # Check the source code for return annotation
        source = inspect.getsource(AgentAPI.generate_response)
        assert '-> str:' in source, "generate_response missing -> str: return annotation"

        print("✓ API return annotation verified")
        return True

    except Exception as e:
        print(f"✗ API return annotation verification failed: {e}")
        return False

def main():
    """Run all verifications."""
    print("Starting improvement verification...\n")

    tests = [
        verify_analysis_plugin,
        verify_api_return_annotation
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"Results: {passed}/{total} verifications passed")

    if passed == total:
        print("All improvements successfully verified!")
        return 0
    else:
        print("Some verifications failed")
        return 1

if __name__ == '__main__':
    exit(main())
