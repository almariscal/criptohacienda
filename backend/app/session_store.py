import threading
from typing import Dict

from .models import SessionData


class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, SessionData] = {}
        self._lock = threading.Lock()

    def set(self, session_id: str, data: SessionData) -> None:
        with self._lock:
            self._sessions[session_id] = data

    def get(self, session_id: str) -> SessionData:
        with self._lock:
            return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
        return False

    def exists(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._sessions


session_store = SessionStore()
