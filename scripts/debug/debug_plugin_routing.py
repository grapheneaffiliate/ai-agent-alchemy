#!/usr/bin/env python3
"""Debug script to test plugin question routing"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agent.react_loop import is_codebase_question, route_to_leann_tool

def test_plugin_questions():
    """Test various plugin-related questions"""
    
    test_questions = [
        "what plugins do you have?",
        "what plugins are available?",
        "how many plugins do you have?",
        "what capabilities do you have?",
        "what tools do you have?",
        "list your plugins",
        "show me your plugins"
    ]
    
    print("🔍 Testing Plugin Question Routing")
    print("=" * 50)
    
    for question in test_questions:
        print(f"\n📝 Question: '{question}'")
        
        # Test if it's detected as a codebase question
        is_codebase = is_codebase_question(question)
        print(f"   is_codebase_question: {is_codebase}")
        
        if is_codebase:
            # Test which tool it routes to
            tool, args = route_to_leann_tool(question)
            print(f"   Routes to: {tool}")
            print(f"   Args: {args}")
        else:
            print("   ❌ Not detected as codebase question!")

if __name__ == "__main__":
    test_plugin_questions()
