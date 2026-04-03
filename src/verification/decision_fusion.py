"""Fuse symbolic + NLI signals into ACCEPT / REJECT / REPAIR."""

from __future__ import annotations

from schemas.verification import FusionDecision, NLIResult


def fuse(
    *,
    symbolic_ok: bool,
    nli: NLIResult | None,
    prefer_symbolic: bool = True,
) -> tuple[FusionDecision, list[str]]:
    diag: list[str] = []
    if not symbolic_ok:
        diag.append("symbolic_failed")
        return "REJECT", diag
    if nli is None:
        diag.append("nli_skipped")
        return ("ACCEPT" if prefer_symbolic else "REPAIR"), diag
    if nli.label == "contradiction":
        diag.append("nli_contradiction")
        return "REJECT", diag
    if nli.label == "entailment" and nli.score >= 0.45:
        diag.append("nli_entailment")
        return "ACCEPT", diag
    if nli.label == "neutral":
        diag.append("nli_neutral")
        return ("REPAIR" if not prefer_symbolic else "ACCEPT"), diag
    diag.append("nli_weak")
    return "REPAIR", diag
