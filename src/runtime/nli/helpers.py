"""High-level legal-QA helpers: premise = evidence/source, hypothesis = claim/answer/goal."""

from __future__ import annotations

from typing import Any

from runtime.nli.service import NLIService, get_nli_service


def score_pair(premise: str, hypothesis: str, *, service: NLIService | None = None) -> dict[str, Any]:
    """Full prediction dict (label, scores, premise, hypothesis)."""
    svc = service or get_nli_service()
    return svc.predict(premise, hypothesis)


def support_score(premise: str, hypothesis: str, *, service: NLIService | None = None) -> float:
    """entailment_prob - contradiction_prob in [ -1, 1 ]."""
    d = score_pair(premise, hypothesis, service=service)
    scores: dict[str, float] = d["scores"]
    return float(scores.get("entailment", 0.0) - scores.get("contradiction", 0.0))


def check_entailment(
    premise: str,
    hypothesis: str,
    *,
    threshold: float = 0.70,
    service: NLIService | None = None,
) -> bool:
    """True if entailment probability meets threshold."""
    d = score_pair(premise, hypothesis, service=service)
    return float(d["scores"].get("entailment", 0.0)) >= threshold


def check_contradiction(
    premise: str,
    hypothesis: str,
    *,
    threshold: float = 0.70,
    service: NLIService | None = None,
) -> bool:
    """True if contradiction probability meets threshold (strong conflict)."""
    d = score_pair(premise, hypothesis, service=service)
    return float(d["scores"].get("contradiction", 0.0)) >= threshold


def is_semantically_consistent(
    premise: str,
    hypothesis: str,
    *,
    entailment_threshold: float = 0.70,
    contradiction_threshold: float = 0.70,
    service: NLIService | None = None,
) -> bool:
    """
    Consistent if entailment is high and contradiction is not high.
    Useful for answer vs evidence checks.
    """
    d = score_pair(premise, hypothesis, service=service)
    scores: dict[str, float] = d["scores"]
    e = float(scores.get("entailment", 0.0))
    c = float(scores.get("contradiction", 0.0))
    return e >= entailment_threshold and c < contradiction_threshold


def verify_claim_against_evidence(claim: str, evidence: str, *, service: NLIService | None = None) -> dict[str, Any]:
    """
    Map claim vs evidence to NLI: evidence is premise, claim is hypothesis.
    Returns the same structure as `predict` plus `support_score`.
    """
    d = score_pair(evidence, claim, service=service)
    scores: dict[str, float] = d["scores"]
    ss = float(scores.get("entailment", 0.0) - scores.get("contradiction", 0.0))
    out = dict(d)
    out["support_score"] = ss
    out["evidence"] = evidence
    out["claim"] = claim
    return out
