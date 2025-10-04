import json
from pathlib import Path
from threading import Lock
from typing import List, Optional, Dict
from .models import MemoryStore, Session

class MemoryStoreFileImpl(MemoryStore):
    def __init__(self, path: str = "memory/sessions.json"):
        super().__init__()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
        self.load_all()

    def load_all(self) -> None:
        """Load all sessions from JSON file."""
        if self.path.exists():
            with self.lock:
                try:
                    with open(self.path, 'r') as f:
                        data = json.load(f)
                    self.sessions = {k: Session.model_validate(v) for k, v in data.items()}
                except (json.JSONDecodeError, KeyError, ValueError):
                    self.sessions = {}

    def save_all(self) -> None:
        """Save all sessions to JSON file."""
        with self.lock:
            try:
                with open(self.path, 'w') as f:
                    json.dump({sid: s.model_dump() for sid, s in self.sessions.items()}, f, indent=2)
            except OSError as e:
                print(f"Memory persistence error: {e}")

    def save_session(self, session: Session) -> None:
        super().save_session(session)
        self.save_all()

    def load_session(self, session_id: str) -> Optional[Session]:
        session = super().load_session(session_id)
        if session:
            self.save_all()  # Update access time or just persist
        return session

    def list_sessions(self) -> List[str]:
        return super().list_sessions()

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.save_all()
            return True
        return False

    def search_sessions(self, keywords: List[str]) -> List[Session]:
        """Search sessions by keywords in conversation history."""
        results = []
        for session in self.sessions.values():
            if session.history:
                content = ' '.join([msg.get('content', '') for msg in session.history])
                if any(kw.lower() in content.lower() for kw in keywords):
                    results.append(session)
        return results

    def get_recent_sessions(self, after: Optional[str] = None, before: Optional[str] = None, n: int = 20, sort_order: str = 'desc') -> List[Session]:
        """Get recent sessions with optional time filters."""
        from datetime import datetime

        def parse_time(t: str) -> datetime:
            return datetime.fromisoformat(t.replace('Z', '+00:00')) if t else datetime.min

        sorted_sessions = sorted(
            self.sessions.values(),
            key=lambda s: parse_time(s.updated_at or s.created_at),
            reverse=(sort_order == 'desc')
        )

        if after:
            after_dt = datetime.fromisoformat(after.replace('Z', '+00:00'))
            sorted_sessions = [s for s in sorted_sessions if parse_time(s.updated_at or s.created_at) > after_dt]

        if before:
            before_dt = datetime.fromisoformat(before.replace('Z', '+00:00'))
            sorted_sessions = [s for s in sorted_sessions if parse_time(s.updated_at or s.created_at) < before_dt]

        return sorted_sessions[:n]
