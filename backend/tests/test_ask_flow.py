from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_ask_permission_happy_path():
    client = TestClient(app)
    r = client.post(
        "/ask",
        json={
            "question": "Cổ đông có thể gửi phiếu lấy ý kiến đã trả lời đến công ty bằng thư điện tử không?",
            "session_id": None,
            "user_facts": [],
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("session_id")
    assert data.get("needs_clarification") is False
    assert data.get("answer") is not None
    assert data["answer"].get("answer_text")


def test_ask_creates_session_retrievable():
    client = TestClient(app)
    r = client.post(
        "/ask",
        json={"question": "Câu hỏi demo?", "session_id": None, "user_facts": []},
    )
    assert r.status_code == 200
    sid = r.json()["session_id"]
    g = client.get(f"/session/{sid}")
    assert g.status_code == 200
    assert g.json()["session_id"] == sid
