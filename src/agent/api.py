import os
import json
import httpx
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Optional
from .models import Session
from .system_prompt import get_system_prompt, get_mcp_tool_info, format_environment_details

load_dotenv(override=True)

class AgentAPI:
    def __init__(self, session: Session, mcp_tools: Optional[List[Dict]] = None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.model = os.getenv("MODEL", "x-ai/grok-code-fast-1")
        if not self.api_key or not self.base_url:
            raise ValueError("Missing OPENAI_API_KEY or OPENAI_BASE_URL in .env")
        self.session = session
        self.mcp_tools = mcp_tools or []
        self.system_prompt = None
        self._initialize_system_prompt()
    
    def _initialize_system_prompt(self):
        """Initialize the system prompt with available MCP tools."""
        # Format MCP tools for prompt injection
        tool_info = [get_mcp_tool_info(tool) for tool in self.mcp_tools]
        
        # Get model configuration from environment
        company_name = os.getenv("COMPANY_NAME", "OpenAI")
        model_name = os.getenv("MODEL_NAME", "GPT")
        model_family = os.getenv("MODEL_FAMILY", "GPT")
        
        self.system_prompt = get_system_prompt(
            company_name=company_name,
            model_name=model_name,
            model_family=model_family,
            model_string=self.model,
            available_mcp_tools=tool_info,
            user_location=os.getenv("USER_LOCATION", "Unknown")
        )

    async def generate_response(
        self, 
        prompt: str, 
        context: str = "",
        environment_details: Optional[str] = None
    ) -> str:
        """
        Generate a response from the AI model with system prompt injection.
        
        Args:
            prompt: User's input prompt
            context: Additional context to prepend to prompt
            environment_details: Optional environment context (working dir, files, etc.)
            
        Returns:
            AI-generated response text
        """
        messages = []
        
        # Inject system prompt as first message
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        # Add conversation history
        if self.session and self.session.history:
            messages.extend(self.session.history)
        
        # Build user message with context and environment details
        user_content = ""
        if context:
            user_content += f"{context}\n\n"
        user_content += prompt
        if environment_details:
            user_content += f"\n\n{environment_details}"
            
        messages.append({"role": "user", "content": user_content})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 8000  # Increased for HTML games and long content
        }
        
        # Ensure proper JSON serialization by pre-encoding
        # This prevents issues with special characters in the system prompt
        payload_json = json.dumps(payload, ensure_ascii=False)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Add OpenRouter-specific headers if using OpenRouter
        if "openrouter.ai" in self.base_url:
            headers.update({
                "X-Requested-With": "XMLHttpRequest"
            })

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    content=payload_json,
                    headers=headers,
                    timeout=120.0  # Increased timeout for long responses with news context
                )

                if response.status_code != 200:
                    error_text = response.text
                    raise Exception(f"API request failed: {response.status_code} - {error_text}")

                data = response.json()

                if "choices" not in data or len(data["choices"]) == 0:
                    raise Exception(f"Invalid API response format: {data}")

                response_text = data["choices"][0]["message"]["content"]

                if self.session:
                    self.session.history.append({"role": "assistant", "content": response_text})
                return response_text

            except httpx.TimeoutException:
                raise Exception("API request timed out")
            except httpx.NetworkError as e:
                raise Exception(f"Network error: {str(e)}")
