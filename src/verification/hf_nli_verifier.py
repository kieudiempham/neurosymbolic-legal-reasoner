"""NLIVerifier backed by Hugging Face `NLIService` (mDeBERTa XNLI-style)."""

from __future__ import annotations

from typing import cast

from schemas.verification import NLILabel, NLIResult
from runtime.nli.service import NLIService
from verification.nli_verifier import NLIVerifier


class HuggingFaceNLIVerifier(NLIVerifier):
    """Maps `NLIService.predict` output to pipeline `NLIResult` (with full score vector)."""

    def __init__(self, service: NLIService) -> None:
        self._service = service

    def verify(self, premise: str, hypothesis: str) -> NLIResult:
        d = self._service.predict(premise, hypothesis)
        scores: dict[str, float] = d["scores"]
        label_raw = str(d["label"])
        label_s = label_raw if label_raw in ("entailment", "neutral", "contradiction") else "neutral"
        conf = float(scores.get(label_s, 0.0))
        return NLIResult(
            label=cast(NLILabel, label_s),
            score=conf,
            scores=scores,
        )
