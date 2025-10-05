"""API request and response models."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel


class Message(BaseModel):
    """Chat message model."""

    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    """Chat completion request model."""

    model: str
    messages: List[Message]
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class ChatCompletionChoice(BaseModel):
    """Single completion choice."""

    index: int
    message: Message
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    """Chat completion response model."""

    id: str
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Dict[str, int]


class Model(BaseModel):
    """Model information."""

    id: str
    created: int
    owned_by: str


class ModelList(BaseModel):
    """List of available models."""

    object: str
    data: List[Model]
