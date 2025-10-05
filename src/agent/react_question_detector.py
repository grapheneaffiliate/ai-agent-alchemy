"""Question type detection for intelligent routing in ReAct loop."""

from typing import Dict, Any, Tuple


def is_time_question(user_input: str) -> bool:
    """
    Determine if the user is asking for the current time.

    Returns True for questions like:
    - "what time is it"
    - "current time"
    - "what's the time"
    """
    input_lower = user_input.lower()

    time_keywords = [
        'what time',
        "what's the time",
        'current time',
        'time is it',
        'tell me the time'
    ]

    return any(keyword in input_lower for keyword in time_keywords)


def is_news_question(user_input: str) -> bool:
    """
    Determine if the user is asking for current news or information that should be fetched from the web.

    Returns True for questions like:
    - "show me the latest news about"
    - "what's happening with"
    - "tell me about current events"
    - "show me news about"
    - "latest updates on"
    """
    input_lower = user_input.lower()

    news_keywords = [
        'latest news',
        'current news',
        'show me news',
        'tell me about current',
        'what\'s happening',
        'latest updates',
        'current situation',
        'breaking news',
        'what\'s new with',
        'recent developments on'
    ]

    # Check for news keywords OR explicit news question patterns
    has_news_keywords = any(keyword in input_lower for keyword in news_keywords)
    has_news_pattern = ('news' in input_lower or 'latest' in input_lower) and 'about' in input_lower

    return has_news_keywords or has_news_pattern


def extract_news_topic(user_input: str) -> str:
    """
    Extract the news topic from user input.

    Examples:
    - "show me news about US government shutdown" -> "US government shutdown"
    - "what's happening with climate change" -> "climate change"
    - "latest updates on artificial intelligence" -> "artificial intelligence"
    """
    input_lower = user_input.lower()

    # Remove common news question prefixes
    prefixes = [
        'show me news about',
        'show me the latest news about',
        'tell me about',
        'what\'s happening with',
        'what\'s new with',
        'latest updates on',
        'current news about',
        'news about',
        'about',
        'on'
    ]

    topic = user_input
    for prefix in prefixes:
        if input_lower.startswith(prefix):
            topic = user_input[len(prefix):].strip()
            break

    # Clean up the topic
    topic = topic.strip('.,!?')
    return topic if topic else 'general'


def is_codebase_question(user_input: str) -> bool:
    """
    Determine if the user question is about the agent's codebase or requires LEANN analysis.

    Returns True for questions like:
    - "tell me about your codebase"
    - "what code do you have"
    - "show me the implementation"
    - "how is your code structured"
    - "how is the plugin system implemented"
    - "assess your codebase"
    - "health check"
    - "analyze your health"
    - "improve yourself"
    - "self improvement"
    - "what plugins do you have"
    - "what capabilities do you have"
    - "what tools do you have"
    """
    input_lower = user_input.lower()

    codebase_keywords = [
        'codebase', 'code base', 'source code', 'sourcecode',
        'implementation', 'implemented', 'code structure', 'architecture',
        'modules', 'functions', 'classes', 'plugin', 'plugins',
        'how are you built', 'how do you work', 'how is', 'how does',
        'what code', 'your code', 'internal code',
        'assess', 'analyze', 'review', 'evaluate',
        'design pattern', 'system design', 'file structure',
        # Plugin and capability related keywords
        'what plugins', 'plugin list', 'plugins do you have', 'what plugins do you have',
        'how many plugins', 'what plugins', 'plugins are available', 'available plugins',
        'what tools do you have', 'what capabilities', 'what can you do', 'list your plugins',
        'show me your plugins', 'what plugins do', 'plugins you have', 'your plugins',
        'what tools are available', 'what capabilities do you have', 'what can you',
        'plugin capabilities', 'tool capabilities', 'available tools', 'plugin features'
    ]

    # Health and improvement keywords
    health_keywords = [
        'health check', 'health', 'status', 'diagnose', 'diagnosis',
        'improve yourself', 'self improvement', 'enhancement plan',
        'analysis', 'comprehensive analysis', 'improve your'
    ]

    return any(keyword in input_lower for keyword in codebase_keywords) or \
           any(keyword in input_lower for keyword in health_keywords)


def route_to_leann_tool(user_input: str) -> Tuple[str, Dict[str, Any]]:
    """
    Route user input to the appropriate LEANN tool based on question intent.

    Returns (tool_name, tool_args) tuple.

    Routing logic:
    - health check, analyze health -> analyze_codebase_health
    - improve yourself, enhancement plan -> generate_codebase_enhancement_plan
    - analyze code, intelligence -> analyze_codebase_intelligence
    - assess codebase, comprehensive -> comprehensive_self_improvement_analysis
    - ALL plugin-related questions -> analyze_codebase_intelligence (with specific question)
    """
    input_lower = user_input.lower()

    # Plugin-specific questions - route to intelligence with specific question
    plugin_keywords = [
        'what plugins', 'plugin list', 'plugins do you have', 'what plugins do you have',
        'how many plugins', 'what plugins', 'plugins are available', 'available plugins',
        'what tools do you have', 'what capabilities', 'what can you do', 'list your plugins',
        'show me your plugins', 'what plugins do', 'plugins you have', 'your plugins',
        'what tools are available', 'what capabilities do you have', 'what can you',
        'plugin capabilities', 'tool capabilities', 'available tools', 'plugin features'
    ]
    if any(word in input_lower for word in plugin_keywords):
        return 'analyze_codebase_intelligence', {'index_name': 'agent-code', 'question': 'What plugins are available in this codebase?'}

    # Health-specific questions
    if any(word in input_lower for word in ['health check', 'health', 'analyze your health', 'system health', 'diagnose health']):
        return 'analyze_codebase_health', {'index_name': 'agent-code'}

    # Enhancement plan questions
    if any(word in input_lower for word in ['enhancement plan', 'generate_codebase_enhancement_plan', 'improve yourself', 'self improvement']):
        return 'generate_codebase_enhancement_plan', {'index_name': 'agent-code'}

    # Intelligence/analysis questions
    if any(word in input_lower for word in ['analyze your code', 'analyze_codebase_intelligence', 'architectural analysis', 'code intelligence']):
        return 'analyze_codebase_intelligence', {'index_name': 'agent-code'}

    # Default to comprehensive self-improvement analysis
    return 'comprehensive_self_improvement_analysis', {'index_name': 'agent-code', 'question': user_input}
