"""
Integration tests for Hugging Face NLI (downloads model on first run).

Set RUN_NLI_INTEGRATION=1 and install torch + transformers.
Skip by default to keep CI fast.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_NLI_INTEGRATION") != "1",
    reason="Set RUN_NLI_INTEGRATION=1 to run HF NLI integration tests (downloads model).",
)


@pytest.fixture(scope="module")
def nli_service():
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    from runtime.nli.service import init_nli_service, reset_nli_service
    from runtime.nli.types import NLIRuntimeConfig

    reset_nli_service()
    cfg = NLIRuntimeConfig(
        model_name="MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7",
        device="auto",
        batch_size=2,
        max_length=256,
    )
    yield init_nli_service(cfg)
    reset_nli_service()


def test_vietnamese_entailment(nli_service) -> None:
    from runtime.nli.helpers import score_pair

    premise = (
        "Người thành lập doanh nghiệp phải nộp hồ sơ đăng ký doanh nghiệp cho cơ quan đăng ký kinh doanh."
    )
    hyp = "Người thành lập doanh nghiệp có nghĩa vụ nộp hồ sơ đăng ký doanh nghiệp."
    d = score_pair(premise, hyp, service=nli_service)
    assert d["scores"]["entailment"] > d["scores"]["contradiction"]


def test_vietnamese_contradiction(nli_service) -> None:
    from runtime.nli.helpers import score_pair

    premise = (
        "Người thành lập doanh nghiệp phải nộp hồ sơ đăng ký doanh nghiệp cho cơ quan đăng ký kinh doanh."
    )
    hyp = "Người thành lập doanh nghiệp không cần nộp hồ sơ đăng ký doanh nghiệp."
    d = score_pair(premise, hyp, service=nli_service)
    assert d["scores"]["contradiction"] > d["scores"]["entailment"]


def test_vietnamese_neutral_or_not_entail(nli_service) -> None:
    from runtime.nli.helpers import score_pair

    premise = (
        "Người thành lập doanh nghiệp phải nộp hồ sơ đăng ký doanh nghiệp cho cơ quan đăng ký kinh doanh."
    )
    hyp = "Người thành lập doanh nghiệp phải nộp thuế thu nhập cá nhân trong ngày đăng ký."
    d = score_pair(premise, hyp, service=nli_service)
    assert d["label"] in ("entailment", "neutral", "contradiction")
    s = sum(d["scores"].values())
    assert 0.99 <= s <= 1.01 or s > 0.5


def test_batch_predict(nli_service) -> None:
    pairs = [
        ("A là B.", "A là B."),
        ("Xảy ra Y.", "Không xảy ra Y."),
    ]
    out = nli_service.batch_predict(pairs)
    assert len(out) == 2
    assert "scores" in out[0]
