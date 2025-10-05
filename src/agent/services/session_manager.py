"""Utilities for managing agent sessions."""

from __future__ import annotations

import uuid
from typing import Optional

from ..memory import MemoryStoreFileImpl
from ..models import Session


class SessionManager:
    """Handle session lifecycle and persistence for the agent."""

    def __init__(self, memory_store: MemoryStoreFileImpl):
        self._memory_store = memory_store

    def new_session_id(self) -> str:
        return str(uuid.uuid4())

    def load(self, session_id: str) -> Session:
        existing = self._memory_store.load_session(session_id)
        return existing or Session(id=session_id)

    def save(self, session: Session) -> None:
        self._memory_store.save_session(session)

    def load_recent(self, limit: int = 5) -> list[Session]:
        try:
            return self._memory_store.get_recent_sessions(n=limit)
        except AttributeError:
            return []

    def search(self, keywords: list[str]) -> list[Session]:
        try:
            return self._memory_store.search_sessions(keywords)
        except AttributeError:
            return []

    def load_all(self) -> None:
        try:
            self._memory_store.load_all()
        except AttributeError:
            pass
