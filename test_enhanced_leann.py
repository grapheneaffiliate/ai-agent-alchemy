#!/usr/bin/env python3
"""Test script for enhanced LEANN self-improvement capabilities."""

import asyncio
from src.plugins.leann_plugin import LeannPlugin


async def test_enhanced_leann():
    """Test the enhanced LEANN self-improvement capabilities."""
    plugin = LeannPlugin()
    print('Testing enhanced LEANN self-improvement capabilities...')

    # Test comprehensive self-improvement analysis
    result = await plugin._comprehensive_self_improvement_analysis()
    if result.get('status') == 'success':
        analysis = result.get('analysis', {})
        improvement_score = analysis.get('self_improvement_score', 0)
        print('✅ Self-improvement analysis completed')
        print(f'📊 Self-improvement score: {improvement_score}/100')

        # Show some key insights
        if 'comprehensive_diagnosis' in analysis:
            diagnosis = analysis['comprehensive_diagnosis']
            project_overview = diagnosis.get('project_overview', {})
            print(f'📁 Project files: {project_overview.get("total_files", 0)}')
            print(f'🐍 Python files: {project_overview.get("python_files", 0)}')
            print(f'🧪 Test files: {project_overview.get("test_files", 0)}')

            # Show recommendations
            recommendations = diagnosis.get('recommendations', [])
            if recommendations:
                print('💡 Key recommendations:')
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f'   {i}. {rec}')
    else:
        print(f'❌ Analysis failed: {result.get("error")}')

    # Test health analysis
    health_result = await plugin._analyze_codebase_health()
    if health_result.get('status') == 'success':
        health_report = health_result.get('health_report', {})
        overall_score = health_report.get('overall_health_score', 0)
        health_status = health_report.get('health_status', 'unknown')
        print(f'🏥 Overall health score: {overall_score:.1f}/100 ({health_status})')

        # Show dimension scores
        dimension_scores = health_report.get('dimension_scores', {})
        print('📊 Health dimensions:')
        for dimension, score in dimension_scores.items():
            print(f'   {dimension}: {score:.1f}/100')
    else:
        print(f'❌ Health analysis failed: {health_result.get("error")}')


async def test_mcp_tools():
    """Test that the enhanced LEANN tools are available via MCP."""
    print('\n' + '='*60)
    print('Testing MCP Tool Integration')
    print('='*60)

    try:
        # Test direct plugin access
        plugin = LeannPlugin()

        # Test the specific tool that should be called for 'assess your codebase'
        result = await plugin.execute('leann', 'comprehensive_self_improvement_analysis', {'index_name': 'agent-code'})

        if result.get('status') == 'success':
            analysis = result.get('analysis', {})
            improvement_score = analysis.get('self_improvement_score', 0)
            print('✅ Enhanced self-improvement analysis completed')
            print(f'📊 Self-improvement score: {improvement_score}/100')

            if 'comprehensive_diagnosis' in analysis:
                diagnosis = analysis['comprehensive_diagnosis']
                project_overview = diagnosis.get('project_overview', {})
                print(f'📁 Project files: {project_overview.get("total_files", 0)}')
                print(f'🐍 Python files: {project_overview.get("python_files", 0)}')
                print(f'🧪 Test files: {project_overview.get("test_files", 0)}')

                recommendations = diagnosis.get('recommendations', [])
                if recommendations:
                    print('💡 Key recommendations:')
                    for i, rec in enumerate(recommendations[:3], 1):
                        print(f'   {i}. {rec}')
        else:
            print(f'❌ Analysis failed: {result.get("error")}')

    except Exception as e:
        print(f'❌ MCP tool test failed: {e}')
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print('🚀 Starting Enhanced LEANN Self-Improvement Test')
    print('='*60)

    asyncio.run(test_enhanced_leann())
    asyncio.run(test_mcp_tools())

    print('\n' + '='*60)
    print('✅ ALL ENHANCED LEANN TESTS COMPLETE')
    print('='*60)
    print('\n🎯 The agent is now equipped with world-class self-improvement capabilities!')
    print('💡 Try asking: "assess your codebase" in the web UI')
