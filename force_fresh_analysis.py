#!/usr/bin/env python3
"""
Force Fresh LEANN Analysis Script

This script clears any cached LEANN analysis data and runs a fresh analysis
to ensure the custom UI shows up-to-date statistics and recommendations.
"""

import os
import sys
import shutil
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def clear_leann_cache():
    """Clear LEANN cache directories to force fresh analysis."""
    leann_dir = Path(".leann")
    if leann_dir.exists():
        print(f"🗑️  Clearing LEANN cache directory: {leann_dir}")
        shutil.rmtree(leann_dir)
        print("✅ LEANN cache cleared")
    else:
        print("ℹ️  No LEANN cache directory found")

def run_fresh_analysis():
    """Run a fresh LEANN codebase analysis."""
    try:
        print("🔍 Running fresh LEANN codebase analysis...")

        # Import and run the LEANN intelligence analysis
        from plugins.leann.intelligence import analyze_codebase_intelligence

        # Run analysis with current codebase
        result = analyze_codebase_intelligence('agent-code')

        print("✅ Fresh analysis completed successfully")
        print(f"📊 Analysis result: {result}")

        return True

    except Exception as e:
        print(f"❌ Error running fresh analysis: {e}")
        return False

def main():
    """Main function to force fresh analysis."""
    print("🚀 Starting fresh LEANN analysis process...")

    # Clear existing cache
    clear_leann_cache()

    # Run fresh analysis
    success = run_fresh_analysis()

    if success:
        print("\n🎉 Fresh analysis completed successfully!")
        print("💡 The custom UI should now show updated statistics and recommendations.")
        print("   Try asking: 'analyze your codebase' in the custom UI")
    else:
        print("\n⚠️  Fresh analysis completed with errors.")
        print("   The cache has been cleared, so next analysis should be fresh.")

    return success

if __name__ == "__main__":
    main()
