"""Unit tests: condition normalizer, entity registry, ambiguity → clarification."""

from __future__ import annotations

import json
from pathlib import Path

from question_side.condition_normalizer import normalize_condition_text
from question_side.entity_registry import resolve_subject_entity
from reasoning.clarification_manager import build_parse_ambiguity_prompts, merge_clarification_prompts_unified
from schemas.question_parse import Layer1Parse


def test_normalize_condition_maps_canonical() -> None:
    r = normalize_condition_text(
        "thay đổi người đại diện theo pháp luật",
        actor_entity_id="company_x",
        actor_role="company",
        assertion_status="hypothetical",
    )
    assert "thay_doi_nguoi_dai_dien" in r.primary_atom
    assert r.confidence >= 0.5


def test_entity_registry_shareholder() -> None:
    eid, role, reg, m = resolve_subject_entity("Cổ đông A muốn chuyển nhượng cổ phần")
    assert role == "shareholder"
    assert "shareholder" in eid


def test_ambiguity_prompts_merge_priority() -> None:
    ambs = [
        {
            "type": "ambiguous_condition",
            "field": "condition_text",
            "source_text": "x",
            "candidates": ["a(company_x)", "b(company_x)"],
            "confidence_gap": 0.05,
            "blocking": False,
            "priority": 5,
            "blocking_reason": "test",
        }
    ]
    pp = build_parse_ambiguity_prompts(ambs)
    bw = [{"fact_key": "k1", "question_text": "q1", "priority": 50}]
    merged = merge_clarification_prompts_unified(pp, bw)
    assert merged[0]["priority"] <= merged[-1]["priority"]


def test_contract_json_layer1_shape() -> None:
    raw = json.loads((Path(__file__).parent / "fixtures" / "llm_layer1_contract.json").read_text(encoding="utf-8"))
    data = json.loads(raw["raw_llm_response"])
    assert data["question_focus"] == "obligation"
    assert "subject_text" in data


def test_layer1_for_ambiguous_assertion_adds_goal_ambiguity_diag() -> None:
    l1 = Layer1Parse(
        subject_text="Công ty",
        action_text="nộp",
        question_focus="obligation",
        assertion_status="ambiguous",
    )
    from question_side.question_normalizer import build_layer2

    l2 = build_layer2(l1, user_facts=[])
    amb = l2.diagnostics.get("ambiguities") or []
    kinds = [a.get("type") for a in amb]
    assert "ambiguous_goal" in kinds or l2.diagnostics.get("assertion_ambiguous")
