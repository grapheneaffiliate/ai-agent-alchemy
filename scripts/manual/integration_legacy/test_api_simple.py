#!/usr/bin/env python3
"""Simple test script for API functionality."""

import asyncio
import os
from dotenv import load_dotenv
from src.agent.api import AgentAPI
from src.agent.models import Session

async def test_api():
    """Test API with a simple prompt."""
    print("=== Testing OpenRouter API ===")

    # Load environment
    load_dotenv()

    # Check configuration
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("MODEL", "x-ai/grok-code-fast-1")

    print(f"API Key: {'Set' if api_key else 'Not set'}")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print()

    if not api_key or not base_url:
        print("❌ Missing configuration")
        return

    if not api_key.startswith("sk-or-v1-"):
        print(f"❌ Invalid API key format. Expected 'sk-or-v1-', got '{api_key[:20]}...'")
        return

    print("✅ Configuration looks good!")

    try:
        # Create API instance
        session = Session(id="test-session")
        api = AgentAPI(session)

        print("🚀 Testing API call...")
        response = await api.generate_response("Hello! Please respond with a simple greeting.")

        print("✅ API call successful!")
        print(f"Response: {response[:200]}...")

    except Exception as e:
        print(f"❌ API call failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
