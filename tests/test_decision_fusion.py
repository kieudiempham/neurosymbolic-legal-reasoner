"""Unit tests for NLI + symbolic fusion (no Hugging Face download)."""

from __future__ import annotations

from verification.decision_fusion import fuse
from schemas.verification import NLIResult


def test_fusion_rejects_on_contradiction_threshold() -> None:
    nli = NLIResult(
        label="contradiction",
        score=0.75,
        scores={"entailment": 0.05, "neutral": 0.10, "contradiction": 0.85},
    )
    dec, diag = fuse(
        symbolic_ok=True,
        nli=nli,
        prefer_symbolic=True,
        entailment_threshold=0.70,
        contradiction_threshold=0.70,
    )
    assert dec == "REJECT"
    assert "nli_contradiction" in diag


def test_fusion_accepts_on_entailment_threshold() -> None:
    nli = NLIResult(
        label="entailment",
        score=0.88,
        scores={"entailment": 0.88, "neutral": 0.08, "contradiction": 0.04},
    )
    dec, diag = fuse(
        symbolic_ok=True,
        nli=nli,
        prefer_symbolic=True,
        entailment_threshold=0.70,
        contradiction_threshold=0.70,
    )
    assert dec == "ACCEPT"
    assert "nli_entailment" in diag


def test_fusion_symbolic_fail() -> None:
    nli = NLIResult(label="entailment", score=0.99, scores={"entailment": 0.99, "neutral": 0.01, "contradiction": 0.0})
    dec, _ = fuse(symbolic_ok=False, nli=nli, prefer_symbolic=True)
    assert dec == "REJECT"
