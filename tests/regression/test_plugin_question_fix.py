#!/usr/bin/env python3
"""Test the complete plugin question fix"""

import asyncio
import sys
import os
import pytest
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from plugins.leann_plugin import LeannPlugin

@pytest.mark.asyncio
async def test_plugin_question():
    """Test that plugin questions are properly answered"""
    
    print("🧪 Testing Complete Plugin Question Fix")
    print("=" * 50)
    
    # Initialize LEANN plugin
    plugin = LeannPlugin()
    
    # Test the specific plugin question
    print("📝 Testing: 'What plugins are available in this codebase?'")
    
    result = await plugin.execute(
        server="leann",
        tool_name="analyze_codebase_intelligence", 
        args={
            "index_name": "agent-code",
            "question": "What plugins are available in this codebase?"
        }
    )
    
    print(f"Status: {result.get('status')}")
    
    if result.get('status') == 'success':
        analysis = result.get('analysis', {})
        overview = analysis.get('overview', '')
        
        print(f"\n📋 Answer Preview (first 300 chars):")
        print(f"'{overview[:300]}...'")
        
        # Check if it contains plugin-specific information
        plugin_keywords = ['plugin', 'browser', 'search', 'leann', 'analysis', 'news', 'artifacts']
        has_plugin_info = any(keyword.lower() in overview.lower() for keyword in plugin_keywords)
        
        if has_plugin_info:
            print("\n✅ SUCCESS: Response contains plugin-specific information!")
            print("🎉 The fix is working - plugin questions are now properly answered!")
        else:
            print("\n❌ ISSUE: Response doesn't contain plugin-specific information")
            print("🔧 The fix needs more work")
            
        print(f"\n📊 Method used: {analysis.get('method', 'unknown')}")
        
    else:
        print(f"❌ ERROR: {result.get('error', 'Unknown error')}")
    
    return result.get('status') == 'success'

if __name__ == "__main__":
    success = asyncio.run(test_plugin_question())
    print(f"\n{'='*50}")
    print(f"Test Result: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
