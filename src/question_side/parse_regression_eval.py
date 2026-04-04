"""Evaluate parse regression cases (heuristic Layer1 + Layer2) — field-level checks + lexicon gap hints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from question_side.heuristic_layer1 import parse_question_layer1_heuristic
from question_side.question_normalizer import build_layer2
from schemas.question_parse import Layer1Parse, Layer2Parse


@dataclass
class ParseEvalResult:
    qid: str
    question_text: str
    layer1: dict[str, Any]
    layer2: dict[str, Any]
    parser_backend: str
    field_checks: dict[str, bool] = field(default_factory=dict)
    failed_fields: list[str] = field(default_factory=list)
    lexicon_gap_label: str = ""
    stated_condition_used: bool = False
    canonical_predicate: str = ""


def _atoms_blob(l2: Layer2Parse) -> str:
    return " ".join(l2.condition_atoms or [])


def _ambiguity_kinds(l2: Layer2Parse) -> list[str]:
    ambs = (l2.diagnostics or {}).get("ambiguities") or []
    return [str(a.get("type") or "") for a in ambs if isinstance(a, dict)]


def run_parse_pipeline(question_text: str) -> tuple[Layer1Parse, Layer2Parse]:
    l1 = parse_question_layer1_heuristic(question_text)
    l2 = build_layer2(l1, user_facts=[])
    return l1, l2


def classify_lexicon_gap(
    *,
    expected: dict[str, Any],
    canonical_predicate: str,
    stated_condition_used: bool,
    confidence: float,
    ambiguity_reason: str,
) -> str:
    snap = str(expected.get("canonical_snapshot") or "").strip()
    if snap and canonical_predicate == snap:
        return ""
    if expected.get("allow_stated_condition") and stated_condition_used:
        return ""
    want = expected.get("canonical_condition_predicate")
    if want and canonical_predicate and canonical_predicate != "stated_condition":
        if canonical_predicate != want:
            return "wrong_predicate"
    if want and canonical_predicate == "stated_condition":
        return "missing_trigger"
    if stated_condition_used and not expected.get("allow_stated_condition"):
        if confidence >= 0.55:
            return "too_generic"
        return "missing_trigger"
    if ambiguity_reason in ("close_lexicon_alternatives", "score_tie") or (
        confidence < 0.72 and confidence > 0.4
    ):
        return "ambiguous_condition"
    return ""


def evaluate_case(case: dict[str, Any]) -> ParseEvalResult:
    qid = str(case.get("qid") or "")
    qtext = str(case.get("question_text") or "")
    exp = case.get("expected") or {}
    if not isinstance(exp, dict):
        exp = {}

    l1, l2 = run_parse_pipeline(qtext)
    cn = (l2.diagnostics or {}).get("condition_normalization") or {}
    canonical_predicate = str(cn.get("canonical_predicate") or "")
    conf = float(cn.get("confidence") or 0.0)
    amb_reason = str(cn.get("ambiguity_reason") or "")
    atoms = _atoms_blob(l2)
    stated = "stated_condition(" in atoms or canonical_predicate == "stated_condition"

    backend = str((l1.parse_metadata or {}).get("parser_backend") or "heuristic")

    checks: dict[str, bool] = {}
    failed: list[str] = []

    def _fail(name: str, ok: bool) -> None:
        checks[name] = ok
        if not ok:
            failed.append(name)

    l1e = exp.get("layer1") or {}
    if isinstance(l1e, dict):
        if "question_focus" in l1e:
            _fail("question_focus", l1.question_focus == l1e["question_focus"])
        if "question_focus_any" in l1e and isinstance(l1e["question_focus_any"], list):
            _fail("question_focus_any", l1.question_focus in l1e["question_focus_any"])
        if "utterance_type" in l1e:
            _fail("utterance_type", l1.utterance_type == l1e["utterance_type"])
        if "assertion_status" in l1e:
            _fail("assertion_status", l1.assertion_status == l1e["assertion_status"])

    l2m = exp.get("layer2_min") or {}
    if isinstance(l2m, dict):
        if "subject_type_guess" in l2m:
            _fail("subject_type_guess", l2.subject_type_guess == l2m["subject_type_guess"])
        if "subject_normalized" in l2m:
            _fail("subject_normalized", l2.subject_normalized == l2m["subject_normalized"])
        if "goal_predicate" in l2m:
            _fail("goal_predicate", (l2.goal or {}).get("predicate") == l2m["goal_predicate"])

    subs = exp.get("condition_atoms_substrings")
    if isinstance(subs, list) and subs:
        ok = all(substr in atoms for substr in subs if isinstance(substr, str) and substr)
        _fail("condition_atoms_substrings", ok)

    want_pred = exp.get("canonical_condition_predicate")
    if isinstance(want_pred, str) and want_pred:
        _fail("canonical_condition_predicate", canonical_predicate == want_pred)

    snap = exp.get("canonical_snapshot")
    if isinstance(snap, str) and snap.strip():
        _fail("canonical_snapshot", canonical_predicate == snap.strip())

    toks = exp.get("condition_predicate_tokens")
    if isinstance(toks, list) and toks:
        ok = all(t in atoms for t in toks if isinstance(t, str) and t)
        _fail("condition_predicate_tokens", ok)

    amb_exp = exp.get("ambiguity_types")
    optional_amb = bool(exp.get("ambiguity_optional"))
    if isinstance(amb_exp, list) and amb_exp and not optional_amb:
        kinds = set(_ambiguity_kinds(l2))
        ok = all(x in kinds for x in amb_exp if x)
        _fail("ambiguity_types", ok)

    allow_st = bool(exp.get("allow_stated_condition"))
    if exp.get("expect_stated_condition") is True:
        _fail("expect_stated_condition", stated)

    gap = classify_lexicon_gap(
        expected=exp,
        canonical_predicate=canonical_predicate,
        stated_condition_used=stated,
        confidence=conf,
        ambiguity_reason=amb_reason,
    )

    return ParseEvalResult(
        qid=qid,
        question_text=qtext,
        layer1=l1.model_dump(mode="json"),
        layer2=l2.model_dump(mode="json"),
        parser_backend=backend,
        field_checks=checks,
        failed_fields=failed,
        lexicon_gap_label=gap,
        stated_condition_used=stated,
        canonical_predicate=canonical_predicate,
    )


def aggregate_stats(results: list[ParseEvalResult]) -> dict[str, Any]:
    n = len(results)
    if not n:
        return {"total": 0}

    field_totals: dict[str, int] = {}
    field_pass: dict[str, int] = {}

    for r in results:
        for k, ok in r.field_checks.items():
            field_totals[k] = field_totals.get(k, 0) + 1
            if ok:
                field_pass[k] = field_pass.get(k, 0) + 1

    stated_n = sum(1 for r in results if r.stated_condition_used)
    gap_counts: dict[str, int] = {}
    for r in results:
        if r.lexicon_gap_label:
            gap_counts[r.lexicon_gap_label] = gap_counts.get(r.lexicon_gap_label, 0) + 1

    amb_detect = 0
    for r in results:
        ambs = (r.layer2.get("diagnostics") or {}).get("ambiguities") or []
        if ambs:
            amb_detect += 1

    return {
        "total": n,
        "parser_backend": results[0].parser_backend if results else "",
        "field_level_accuracy": {
            k: round(field_pass.get(k, 0) / field_totals[k], 4) for k in sorted(field_totals)
        },
        "field_counts": field_totals,
        "stated_condition_rate": round(stated_n / n, 4),
        "stated_condition_count": stated_n,
        "ambiguity_cases_flagged_layer2": amb_detect,
        "lexicon_gap_counts": gap_counts,
    }
