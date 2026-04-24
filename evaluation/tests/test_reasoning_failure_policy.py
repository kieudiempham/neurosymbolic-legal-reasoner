from __future__ import annotations

from types import SimpleNamespace

import pytest

from runtime.qa_orchestrator import _enforce_reasoning_failure_answer_policy
from schemas.answer import FinalAnswer
from schemas.evidence import EvidenceSnippet
from schemas.question_parse import Layer2Parse
from schemas.rule import RuleHead, RuleRecord


def _usable_layer2() -> Layer2Parse:
    return Layer2Parse(
        subject_normalized="doanh_nghiep_x",
        condition_atoms=["tax_delay(enterprise_x)"],
        goal={"predicate": "obligation", "args": ["enterprise_x", "notify", "tax_authority"]},
        diagnostics={},
    )


def _usable_rule() -> RuleRecord:
    return RuleRecord(
        rule_id="TAX_RULE_001",
        logic_form="obligation(enterprise_x, notify, tax_authority)",
        head=RuleHead(predicate="obligation", args=["enterprise_x", "notify", "tax_authority"]),
        body=[{"predicate": "tax_delay", "args": ["enterprise_x"]}],
        metadata={"provenance": {"source_ref_full": "Dieu 30 ND 168/2025"}},
    )


def _evidence_rows() -> list[EvidenceSnippet]:
    return [
        EvidenceSnippet(
            chunk_id="ev_1",
            text="Doanh nghiep phai gui thong bao trong thoi han theo quy dinh.",
            score=0.82,
            source_ref="Dieu 30 ND 168/2025",
        )
    ]


def test_forward_fail_with_evidence_keeps_answer_and_caps_confidence() -> None:
    ans = FinalAnswer(
        answer_text="Co nghia vu thong bao.",
        conclusion="ap_dung_quy_tac",
        confidence=0.93,
        verification_summary="baseline",
    )

    out = _enforce_reasoning_failure_answer_policy(
        ans,
        question="Cham nop ho so thue thi sao?",
        layer2=_usable_layer2(),
        selected=_usable_rule(),
        goal={"predicate": "obligation", "args": ["enterprise_x", "notify", "tax_authority"]},
        ranked=[(_usable_rule(), 0.9, {"domain": "tax"})],
        evidence=_evidence_rows(),
        phase3_result=SimpleNamespace(conflict_rejected=[]),
        forward_failed=True,
        answer_rejected=False,
        trace={},
    )

    assert out is not None
    assert out.answer_text.strip() != ""
    assert out.confidence <= 0.58
    assert out.extra.get("forward_failure_not_answer_failure") is True


@pytest.mark.parametrize(
    "reason,layer2,selected,evidence,ranked,phase3_result,expected",
    [
        (
            "parse_unusable",
            Layer2Parse(
                subject_normalized="unknown_subject",
                condition_atoms=[],
                goal={"predicate": "unknown", "args": []},
                diagnostics={},
            ),
            _usable_rule(),
            _evidence_rows(),
            [(_usable_rule(), 0.9, {"domain": "tax"})],
            SimpleNamespace(conflict_rejected=[]),
            "parse_unusable",
        ),
        (
            "no_rule",
            _usable_layer2(),
            None,
            _evidence_rows(),
            [(_usable_rule(), 0.9, {"domain": "tax"})],
            SimpleNamespace(conflict_rejected=[]),
            "no_rule",
        ),
        (
            "no_evidence",
            _usable_layer2(),
            _usable_rule(),
            [],
            [(_usable_rule(), 0.9, {"domain": "tax"})],
            SimpleNamespace(conflict_rejected=[]),
            "no_evidence",
        ),
        (
            "conflict_too_large",
            _usable_layer2(),
            _usable_rule(),
            _evidence_rows(),
            [],
            SimpleNamespace(conflict_rejected=[{"id": "c1"}, {"id": "c2"}, {"id": "c3"}]),
            "conflict_too_large",
        ),
    ],
)
def test_null_answer_only_for_hard_stop_reasons(
    reason: str,
    layer2: Layer2Parse,
    selected: RuleRecord | None,
    evidence: list[EvidenceSnippet],
    ranked: list[tuple[RuleRecord, float, dict[str, str]]],
    phase3_result: SimpleNamespace,
    expected: str,
) -> None:
    trace: dict[str, object] = {"hard_gates_hit": []}

    out = _enforce_reasoning_failure_answer_policy(
        FinalAnswer(answer_text="seed", confidence=0.7),
        question=f"hard stop check: {reason}",
        layer2=layer2,
        selected=selected,
        goal={"predicate": "obligation", "args": ["enterprise_x", "notify", "tax_authority"]},
        ranked=ranked,
        evidence=evidence,
        phase3_result=phase3_result,
        forward_failed=False,
        answer_rejected=False,
        trace=trace,
    )

    assert out is None
    assert "answer_null_policy" in trace
    null_reasons = (trace.get("answer_null_policy") or {}).get("reasons") or []
    assert expected in null_reasons
