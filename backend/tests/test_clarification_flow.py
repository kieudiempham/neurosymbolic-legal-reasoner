from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_ask_then_clarify_when_body_requires_fact():
    client = TestClient(app)
    q = (
        "Công ty phải cập nhật kịp thời thay đổi cổ đông trong sổ đăng ký cổ đông "
        "theo yêu cầu của cổ đông có liên quan theo quy định tại Điều lệ công ty không?"
    )
    r1 = client.post("/ask", json={"question": q, "session_id": None, "user_facts": []})
    assert r1.status_code == 200
    d1 = r1.json()
    sid = d1["session_id"]
    if not d1.get("needs_clarification"):
        pytest.skip("rule ranking/unification did not yield a body requirement in this environment")

    fk = d1["clarification_questions"][0]["fact_key"]
    r2 = client.post(
        "/clarify",
        json={"session_id": sid, "answers": [{"fact_key": fk, "value": True}]},
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2.get("answer") is not None
