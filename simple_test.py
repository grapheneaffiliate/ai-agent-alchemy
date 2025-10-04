#!/usr/bin/env python3
"""Simple test to check if LEANN recommendations work."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from plugins.leann_plugin import LeannPlugin

async def simple_test():
    """Test recommendation generation specifically."""
    print("🔍 Testing recommendation generation...")

    try:
        plugin = LeannPlugin()

        # Create mock analysis data that SHOULD trigger recommendations
        project_metrics = {
            'total_files': 40,
            'python_files': 30,
            'test_files': 9,
            'test_coverage_ratio': 0.2  # Less than 0.3 to trigger recommendation
        }

        code_quality = {
            'complexity_score': 50,  # Less than 60 to trigger recommendation
            'total_functions': 41
        }

        dependency_analysis = {
            'dependency_count': 5
        }

        test_coverage = {
            'total_test_files': 9,
            'test_modernity_score': 0.7
        }

        documentation_analysis = {}
        performance_analysis = {}

        print("📊 Testing recommendation generation with mock data...")

        # Test the recommendation generation directly
        recommendations = await plugin._generate_enhancement_recommendations(
            project_metrics, code_quality, dependency_analysis,
            test_coverage, documentation_analysis, performance_analysis
        )

        print(f"✅ Generated {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")

        if not recommendations:
            print("❌ No recommendations generated - there may be an issue with the logic")
            print("🔍 Checking conditions...")

            # Debug the conditions
            test_ratio = project_metrics.get('test_coverage_ratio', 0)
            print(f"Test coverage ratio: {test_ratio}")
            if test_ratio < 0.3:
                print("✓ Should trigger test coverage recommendation")

            complexity = code_quality.get('complexity_score', 50)
            print(f"Complexity score: {complexity}")
            if complexity < 60:
                print("✓ Should trigger complexity recommendation")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())
