"""Session lifecycle."""

from __future__ import annotations

from typing import Any

from schemas.session import SessionState
from session.storage import InMemorySessionStore, SessionStore
from utils.ids import new_session_id


class SessionService:
    def __init__(self, store: SessionStore | None = None) -> None:
        self._store = store or InMemorySessionStore()

    @property
    def store(self) -> SessionStore:
        return self._store

    def create_session(self, question: str, user_facts: list[str]) -> SessionState:
        sid = new_session_id()
        st = SessionState(
            session_id=sid,
            original_question=question,
            user_facts=list(user_facts),
            known_facts={},
        )
        for f in user_facts:
            st.known_facts[f] = True
        self._store.put(st)
        return st

    def get(self, session_id: str) -> SessionState | None:
        return self._store.get(session_id)

    def save(self, state: SessionState) -> None:
        self._store.put(state)

    def merge_fact_answers(self, state: SessionState, answers: list[dict[str, Any]]) -> None:
        for a in answers:
            k = a.get("fact_key")
            if not k:
                continue
            state.known_facts[str(k)] = a.get("value", True)


_session_service: SessionService | None = None


def get_session_service() -> SessionService:
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
