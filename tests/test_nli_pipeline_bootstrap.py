"""NLI bootstrap parity: Python pipeline vs backend ``resolve_nli_stack_bundle``."""

from __future__ import annotations

import pytest

from runtime.nli_bootstrap import (
    ensure_backend_importable,
    load_app_settings,
    resolve_nli_stack_bundle,
    resolve_pipeline_nesy_engine,
)
from verification.engine import NeSyEngine
from verification.nli_verifier import MockNLIVerifier
from verification.openai_compatible_nli import OpenAICompatibleNLIVerifier


@pytest.fixture(autouse=True)
def _disable_hf_nli_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid downloading HF models during bootstrap tests."""
    monkeypatch.setenv("LEGAL_QA_NLI_ENABLED", "false")


def test_resolve_nli_stack_bundle_matches_imported_function() -> None:
    ensure_backend_importable()
    from app.nli_stack import resolve_nli_stack_for_nesy

    s = load_app_settings()
    a = resolve_nli_stack_bundle(s)
    b = resolve_nli_stack_for_nesy(s)
    assert a[2] == b[2]
    assert (a[0] is None) == (b[0] is None)
    if a[0] is not None:
        assert type(a[0]) is type(b[0])


def test_resolve_pipeline_nesy_engine_explicit_nesy_no_override() -> None:
    s = load_app_settings()
    custom = NeSyEngine(nesy_nli_mock=True)
    eng, rt = resolve_pipeline_nesy_engine(nesy=custom, settings=s)
    assert eng is custom
    assert rt.get("nesy_nli_mock") is True


def test_resolve_pipeline_nesy_engine_injected_verifier() -> None:
    s = load_app_settings()
    mock_v = MockNLIVerifier()
    eng, rt = resolve_pipeline_nesy_engine(nli_verifier=mock_v, settings=s)
    assert eng._nli is mock_v
    assert rt.get("injected_verifier") is True
    assert rt.get("verifier_class") == "MockNLIVerifier"


def test_bootstrap_uses_api_verifier_when_build_returns_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """``resolve_nli_stack_bundle`` must use whatever ``app.nli_stack`` gets from ``build_nli_verifier``."""
    import app.nli_stack as nli_stack_mod

    from app.config import Settings

    api = OpenAICompatibleNLIVerifier(api_key="k", base_url="https://example.invalid/v1", model="m")

    def _build(_s: object) -> OpenAICompatibleNLIVerifier:
        return api

    monkeypatch.setattr(nli_stack_mod, "build_nli_verifier", _build)
    s = Settings(nesy_nli_mock=False, nli_policy="degraded")
    v, meta, deg = resolve_nli_stack_bundle(s)
    assert not deg
    assert v is api
    assert isinstance(v, OpenAICompatibleNLIVerifier)
    assert meta.get("nli_status") == "ok"


def test_bootstrap_mock_when_nesy_nli_mock_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEGAL_QA_NESY_NLI_MOCK", "true")
    from app.config import Settings

    s = Settings()
    v, meta, _ = resolve_nli_stack_bundle(s)
    assert v is not None
    assert meta.get("nli_status") == "mock_answer_only"


def test_run_qa_pipeline_includes_nli_runtime_meta(monkeypatch: pytest.MonkeyPatch) -> None:
    from pathlib import Path

    from retrieval.evidence_retriever import configure_evidence_path
    from retrieval.rulebase_loader import configure_rulebase_path
    from runtime.qa_pipeline import run_qa_pipeline

    repo = Path(__file__).resolve().parents[1]
    core = repo / "data" / "processed" / "rulebase" / "doanhnghiep" / "rulebase_reasoning_core.json"
    ev = repo / "data" / "corpus" / "evidence_chunks.json"
    if not core.is_file() or not ev.is_file():
        pytest.skip("fixtures missing")

    configure_rulebase_path(core)
    configure_evidence_path(ev)
    monkeypatch.setenv("LEGAL_QA_LAYER1_USE_LLM", "0")

    qa = run_qa_pipeline(
        "Công ty có nghĩa vụ cập nhật thông tin cổ đông?",
        debug=False,
        save_trace=False,
        nesy=NeSyEngine(nesy_nli_mock=True),
    )
    assert qa.meta.get("nli_runtime")
    assert qa.meta["nli_runtime"].get("verifier_class")
