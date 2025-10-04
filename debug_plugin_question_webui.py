#!/usr/bin/env python3
"""Debug the web UI plugin question behavior"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from plugins.leann_plugin import LeannPlugin

async def debug_web_ui_behavior():
    """Debug what happens when web UI asks about plugins"""
    
    print("🔍 Debugging Web UI Plugin Question Behavior")
    print("=" * 60)
    
    # Initialize LEANN plugin
    plugin = LeannPlugin()
    
    # Test the exact same call as web UI
    print("📝 Testing: 'what plugins do you have?' (web UI style)")
    
    result = await plugin.execute(
        server="leann",
        tool_name="analyze_codebase_intelligence", 
        args={
            "index_name": "agent-code",
            "question": "what plugins do you have?"
        }
    )
    
    print(f"Status: {result.get('status')}")
    
    if result.get('status') == 'success':
        analysis = result.get('analysis', {})
        
        print(f"\n🔍 Analysis structure:")
        for key, value in analysis.items():
            if isinstance(value, str):
                print(f"  {key}: {value[:100]}...")
            else:
                print(f"  {key}: {type(value)}")
        
        # Check if it contains plugin-specific information
        overview = analysis.get('overview', '')
        if overview:
            print(f"\n📋 Overview Preview (first 500 chars):")
            print(f"'{overview[:500]}...'")
            
            # Check if it contains plugin-specific information
            plugin_keywords = ['plugin', 'browser', 'search', 'leann', 'analysis', 'news', 'artifacts']
            has_plugin_info = any(keyword.lower() in overview.lower() for keyword in plugin_keywords)
            
            if has_plugin_info:
                print("\n✅ SUCCESS: Response contains plugin-specific information!")
            else:
                print("\n❌ ISSUE: Response doesn't contain plugin-specific information")
                print("🔧 This explains the web UI behavior")
        else:
            print("\n❌ No overview found in analysis")
            
        print(f"\n📊 Method used: {analysis.get('method', 'unknown')}")
        
        # Check if this is the comprehensive analysis report
        if 'Comprehensive Codebase Analysis Report' in overview:
            print("\n🚨 IDENTIFIED: This is the generic comprehensive analysis report!")
            print("🔧 The intelligence toolkit is not being used properly")
        
    else:
        print(f"❌ ERROR: {result.get('error', 'Unknown error')}")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(debug_web_ui_behavior())
    print(f"\n{'='*60}")
    print("Debug complete")
