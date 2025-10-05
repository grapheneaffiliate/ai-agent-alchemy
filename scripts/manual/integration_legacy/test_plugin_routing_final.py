#!/usr/bin/env python3
"""Final test to verify plugin routing is working in the actual system"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agent.react_loop import is_codebase_question, route_to_leann_tool

def test_all_plugin_questions():
    """Test all plugin-related questions to ensure they route correctly"""
    
    test_questions = [
        "what plugins do you have?",
        "what plugins are available?", 
        "how many plugins do you have?",
        "what capabilities do you have?",
        "what tools do you have?",
        "list your plugins",
        "show me your plugins",
        "what plugins do",
        "plugins you have",
        "your plugins",
        "what tools are available",
        "what capabilities do you have",
        "what can you",
        "plugin capabilities",
        "tool capabilities",
        "available tools",
        "plugin features"
    ]
    
    print("🧪 FINAL PLUGIN ROUTING TEST")
    print("=" * 60)
    
    all_passed = True
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Test {i:2d}: '{question}'")
        
        # Test if it's detected as a codebase question
        is_codebase = is_codebase_question(question)
        print(f"   is_codebase_question: {is_codebase}")
        
        if is_codebase:
            # Test which tool it routes to
            tool, args = route_to_leann_tool(question)
            print(f"   Routes to: {tool}")
            
            # Verify it routes to the correct tool
            if tool == 'analyze_codebase_intelligence':
                print(f"   ✅ CORRECT: Routes to intelligence tool")
                # Verify it has the right question
                expected_question = 'What plugins are available in this codebase?'
                actual_question = args.get('question', '')
                if actual_question == expected_question:
                    print(f"   ✅ CORRECT: Has right question: '{expected_question}'")
                else:
                    print(f"   ❌ WRONG QUESTION: Expected '{expected_question}', got '{actual_question}'")
                    all_passed = False
            else:
                print(f"   ❌ WRONG TOOL: Expected 'analyze_codebase_intelligence', got '{tool}'")
                all_passed = False
        else:
            print("   ❌ NOT detected as codebase question!")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 SUCCESS: All plugin questions route correctly!")
        print("✅ The LEANN system will now properly answer plugin-related questions")
    else:
        print("❌ FAILURE: Some questions are not routing correctly")
    
    return all_passed

if __name__ == "__main__":
    success = test_all_plugin_questions()
    sys.exit(0 if success else 1)
