"""Storage abstraction — swap in Redis/Postgres later."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from schemas.session import SessionState


class SessionStore(ABC):
    @abstractmethod
    def get(self, session_id: str) -> SessionState | None:
        raise NotImplementedError

    @abstractmethod
    def put(self, state: SessionState) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, session_id: str) -> None:
        raise NotImplementedError


class InMemorySessionStore(SessionStore):
    def __init__(self) -> None:
        self._data: dict[str, SessionState] = {}

    def get(self, session_id: str) -> SessionState | None:
        return self._data.get(session_id)

    def put(self, state: SessionState) -> None:
        self._data[state.session_id] = state

    def delete(self, session_id: str) -> None:
        self._data.pop(session_id, None)

    def dump(self) -> dict[str, Any]:
        return {k: v.model_dump(mode="json") for k, v in self._data.items()}
