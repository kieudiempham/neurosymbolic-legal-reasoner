"""GET /session/{session_id}"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.path_setup import ensure_src_paths

ensure_src_paths()

from session.session_service import get_session_service

router = APIRouter(tags=["session"])


@router.get("/session/{session_id}")
def get_session(session_id: str) -> dict:
    svc = get_session_service()
    st = svc.get(session_id)
    if not st:
        raise HTTPException(status_code=404, detail="session_not_found")
    return st.model_dump(mode="json")
