"""Fuse symbolic + NLI signals into ACCEPT / REJECT / REPAIR."""

from __future__ import annotations

from schemas.verification import FusionDecision, NLIResult


def _nli_class_probs(nli: NLIResult) -> tuple[float, float, float]:
    """Returns (entailment, neutral, contradiction) probabilities."""
    if nli.scores:
        s = nli.scores
        return (
            float(s.get("entailment", 0.0)),
            float(s.get("neutral", 0.0)),
            float(s.get("contradiction", 0.0)),
        )
    if nli.label == "entailment":
        return nli.score, 0.0, 0.0
    if nli.label == "contradiction":
        return 0.0, 0.0, nli.score
    return 0.0, nli.score, 0.0


def fuse(
    *,
    symbolic_ok: bool,
    nli: NLIResult | None,
    prefer_symbolic: bool = True,
    entailment_threshold: float = 0.70,
    contradiction_threshold: float = 0.70,
) -> tuple[FusionDecision, list[str]]:
    diag: list[str] = []
    if not symbolic_ok:
        diag.append("symbolic_failed")
        return "REJECT", diag
    if nli is None:
        diag.append("nli_skipped")
        return ("ACCEPT" if prefer_symbolic else "REPAIR"), diag

    e, neu, c = _nli_class_probs(nli)

    if c >= contradiction_threshold:
        diag.append("nli_contradiction")
        return "REJECT", diag
    if e >= entailment_threshold:
        diag.append("nli_entailment")
        return "ACCEPT", diag

    if neu >= max(e, c) and neu >= 0.5:
        diag.append("nli_neutral")
        return ("REPAIR" if not prefer_symbolic else "ACCEPT"), diag

    if nli.label == "contradiction":
        diag.append("nli_contradiction_label")
        return "REJECT", diag
    if nli.label == "entailment" and nli.score >= 0.45:
        diag.append("nli_entailment_weak")
        return "ACCEPT", diag
    if nli.label == "neutral":
        diag.append("nli_neutral")
        return ("REPAIR" if not prefer_symbolic else "ACCEPT"), diag
    diag.append("nli_weak")
    return "REPAIR", diag


def fuse_ne_sy_v5(
    *,
    symbolic_ok: bool,
    nli: NLIResult | None,
    entailment_threshold: float = 0.70,
    contradiction_threshold: float = 0.70,
    moderate_contradiction: float = 0.35,
) -> tuple[FusionDecision, list[str]]:
    """
    v5 fusion matrix:
    - NLI contradiction (high) → REJECT even if symbolic passed
    - symbolic fail + NLI entailment → REPAIR (semantics align, structure wrong)
    - symbolic fail + otherwise → REJECT
    - symbolic pass + entailment → ACCEPT
    - symbolic pass + moderate contradiction → REJECT
    - neutral / weak → REPAIR
    """
    diag: list[str] = []
    if nli is None:
        diag.append("nli_skipped")
        return ("ACCEPT" if symbolic_ok else "REJECT"), diag

    e, neu, c = _nli_class_probs(nli)

    if c >= contradiction_threshold:
        diag.append("nli_contradiction_high")
        if symbolic_ok:
            diag.append("overrides_symbolic_pass")
        return "REJECT", diag

    if not symbolic_ok:
        diag.append("symbolic_failed")
        if e >= entailment_threshold:
            diag.append("nli_entailment_despite_symbolic_fail")
            return "REPAIR", diag
        if c >= moderate_contradiction:
            diag.append("nli_contradiction_moderate_with_symbolic_fail")
            return "REJECT", diag
        return "REJECT", diag

    if e >= entailment_threshold:
        diag.append("nli_entailment_aligned")
        return "ACCEPT", diag

    if c >= moderate_contradiction:
        diag.append("nli_contradiction_moderate")
        return "REJECT", diag

    if neu >= max(e, c, 0.45):
        diag.append("nli_neutral")
        return "REPAIR", diag

    diag.append("nli_uncertain")
    return "REPAIR", diag
