#!/usr/bin/env python3
"""Debug script for LEANN enhanced analysis."""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from plugins.leann_plugin import LeannPlugin

async def debug_enhanced_analysis():
    """Debug the enhanced LEANN analysis step by step."""
    print('🔍 Debugging enhanced LEANN analysis...')

    try:
        plugin = LeannPlugin()
        print(f'✅ LEANN plugin initialized: {plugin.available}')

        # Test 1: Project structure analysis
        print('\n1. Testing project structure analysis...')
        try:
            project_result = await plugin._analyze_project_structure()
            print(f'   ✅ Project analysis completed')
            print(f'   📁 Total files: {project_result.get("total_files", 0)}')
            print(f'   🐍 Python files: {project_result.get("python_files", 0)}')
            print(f'   🧪 Test files: {project_result.get("test_files", 0)}')
        except Exception as e:
            print(f'   ❌ Project analysis failed: {e}')
            return

        # Test 2: Code quality analysis
        print('\n2. Testing code quality analysis...')
        try:
            code_result = await plugin._analyze_code_quality()
            print(f'   ✅ Code quality completed')
            print(f'   📊 Complexity score: {code_result.get("complexity_score", 0)}')
            print(f'   🔢 Total functions: {code_result.get("total_functions", 0)}')
        except Exception as e:
            print(f'   ❌ Code quality failed: {e}')
            return

        # Test 3: Full self-improvement analysis
        print('\n3. Testing comprehensive self-improvement analysis...')
        try:
            full_result = await plugin._comprehensive_self_improvement_analysis()
            print(f'   Status: {full_result.get("status")}')

            if full_result.get('status') == 'success':
                analysis = full_result.get('analysis', {})
                score = analysis.get('self_improvement_score', 0)
                print(f'   ✅ Self-improvement score: {score}/100')

                # Show recommendations
                recommendations = analysis.get('recommendations', [])
                if recommendations:
                    print(f'   💡 Recommendations ({len(recommendations)}):')
                    for i, rec in enumerate(recommendations[:3], 1):
                        print(f'      {i}. {rec}')
            else:
                print(f'   ❌ Failed: {full_result.get("error")}')

        except Exception as e:
            print(f'   ❌ Self-improvement analysis failed: {e}')
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f'❌ LEANN plugin initialization failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_enhanced_analysis())
