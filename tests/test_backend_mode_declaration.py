from __future__ import annotations

from schemas.http_response import AskResponse
from schemas.verification import VerificationRecord
from runtime.backend_modes import (
    apply_answer_backend,
    apply_parse_backend,
    apply_retrieval_backend,
    derive_verifier_backend,
    init_backend_modes,
)


class _Engine:
    def __init__(self, *, mock: bool, degraded: bool, provider: str = "openai", model: str = "gpt-x") -> None:
        self._nesy_nli_mock = mock
        self._nli_degraded = degraded
        self._nli_meta = {"nli_provider": provider, "nli_model_name": model}


class _L1:
    def __init__(self, meta: dict):
        self.parse_metadata = meta


class _Ans:
    def __init__(self, mode: str):
        self.generation_mode = mode


def test_backend_modes_real_fallback_combo() -> None:
    eng = _Engine(mock=False, degraded=False)
    modes = init_backend_modes(verifier_engine=eng)
    apply_parse_backend(modes, _L1({"parser_backend": "heuristic", "parser_model": "v2", "fallback_used": True}))
    apply_retrieval_backend(modes, backend="hybrid_bm25_structured", retrieved_count=3)
    apply_answer_backend(modes, _Ans("template_grounded"))

    assert modes["parse_backend"]["mode"] == "fallback"
    assert modes["retrieval_backend"]["mode"] == "real"
    assert modes["answer_backend"]["mode"] == "fallback"
    assert modes["verifier_backend"]["mode"] == "real"


def test_backend_modes_mock_and_degraded() -> None:
    mock_modes = init_backend_modes(verifier_engine=_Engine(mock=True, degraded=False))
    assert mock_modes["verifier_backend"]["mode"] == "mock"

    degraded_modes = init_backend_modes(verifier_engine=_Engine(mock=False, degraded=True))
    assert degraded_modes["verifier_backend"]["mode"] == "degraded"


def test_evaluation_log_uses_backend_modes_from_trace() -> None:
    resp = AskResponse(
        session_id="sess_backend_modes",
        debug_trace={
            "query_text": "q",
            "backend_modes": {
                "parse_backend": {"provider": "heuristic", "model": "v2", "mode": "fallback"},
                "answer_backend": {"provider": "template", "model": "template_grounded", "mode": "fallback"},
                "verifier_backend": {"provider": "openai", "model": "nli", "mode": "degraded"},
                "retrieval_backend": {"provider": "internal", "model": "hybrid_bm25_structured", "mode": "real"},
            },
        },
        verification_trace=[VerificationRecord(mode="parse_verification", final_decision="ACCEPT")],
    )
    assert resp.evaluation_log is not None
    bm = resp.evaluation_log.backend_modes or {}
    assert bm.get("parse_backend", {}).get("mode") == "fallback"
    assert bm.get("verifier_backend", {}).get("mode") == "degraded"


def test_derive_verifier_backend_none_engine() -> None:
    out = derive_verifier_backend(None)
    assert out["mode"] == "none"
