"""Kokoro TTS integration plugin."""

import httpx
from typing import Optional, Dict, Any


class KokoroTTS:
    """Kokoro Text-to-Speech client."""
    
    def __init__(self, base_url: str = "http://localhost:8880"):
        self.base_url = base_url.rstrip('/')
        
    async def generate_speech(self, text: str, voice: str = "af_sky") -> Optional[bytes]:
        """
        Generate speech from text using Kokoro TTS.
        
        Args:
            text: Text to convert to speech
            voice: Voice model to use
            
        Returns:
            Audio bytes (MP3 format) or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Kokoro OpenAI-compatible endpoint
                response = await client.post(
                    f"{self.base_url}/v1/audio/speech",
                    json={
                        "model": "kokoro",
                        "input": text,
                        "voice": voice,
                        "response_format": "mp3"
                    }
                )
                
                if response.status_code == 200:
                    return response.content
                else:
                    print(f"TTS error: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"TTS error: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check if Kokoro TTS service is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False
    
    async def execute(self, server: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Kokoro TTS commands via MCP interface."""
        try:
            if tool_name == 'generate-speech':
                text = args.get('text', '')
                voice = args.get('voice', 'af_sky')
                result = await self.generate_speech(text, voice)
                if result:
                    return {"status": "success", "result": {"audio": result.hex(), "format": "mp3"}}
                else:
                    return {"status": "error", "error": "TTS generation failed"}
            elif tool_name == 'health-check':
                is_healthy = await self.health_check()
                return {"status": "success", "result": {"healthy": is_healthy}}
            else:
                return {"status": "error", "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Singleton instance
_tts_instance: Optional[KokoroTTS] = None


def get_tts(base_url: str = "http://localhost:8880") -> KokoroTTS:
    """Get or create TTS instance."""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = KokoroTTS(base_url)
    return _tts_instance


# MCP Plugin Interface
async def execute(server: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Kokoro TTS plugin commands via MCP interface."""
    tts = get_tts()
    return await tts.execute(server, tool_name, args)
