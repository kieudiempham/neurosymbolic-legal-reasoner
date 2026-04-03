"""Tests for high-precision rules_reasoning_core selection."""

from __future__ import annotations

from law_side.rulebase_reasoning_core import select_reasoning_core_records


def _base_rule(**overrides):
    r = {
        "rule_id": "R1",
        "selected_for_reasoning": True,
        "reasoning_partition": "exportable_clean",
        "logic_readiness": "reasoning_ready",
        "fallback_kind": None,
        "logic_form": "obligation",
        "head": {"predicate": "obligation", "args": ["cong_ty", "nop_ho_so_da_day_du", "ket_qua"]},
        "body": [],
        "auxiliary_clauses": [],
        "head_cleanup_notes": [],
        "body_cleanup_notes": [],
        "metadata": {
            "problog_exportable": True,
            "export_blockers": [],
            "duplicate_role": "unique_variant",
            "normalization_status": "full",
            "canonical_status": "exact_vocab_match",
            "reasoning_safe_partial": False,
            "canonical_predicate": "nop_ho_so_da_day_du",
        },
    }
    r.update(overrides)
    return r


def test_unique_exportable_clean_included():
    core, excluded, rep = select_reasoning_core_records([_base_rule()])
    assert len(core) == 1
    assert core[0]["core_selection_decision"] == "included"
    assert "stable_for_unification" in core[0]["core_selection_reason"]
    assert rep["core_rule_count"] == 1


def test_redundant_variant_excluded():
    br = _base_rule()
    meta = dict(br["metadata"])
    meta["duplicate_role"] = "redundant_variant"
    r = _base_rule(metadata=meta)
    core, excluded, _ = select_reasoning_core_records([r])
    assert len(core) == 0
    assert any("redundant_variant" in x["reason"] for x in excluded)


def test_unresolved_atom_excluded():
    r = _base_rule(
        head={"predicate": "obligation", "args": ["cong_ty", "unresolved_action", "x"]},
    )
    core, excluded, _ = select_reasoning_core_records([r])
    assert len(core) == 0
    assert any("unresolved_semantic_role" in x["reason"] for x in excluded)


def test_generic_action_excluded():
    r = _base_rule(
        head={"predicate": "obligation", "args": ["cong_ty", "chuan_bi_ho_so", "x"]},
    )
    core, excluded, _ = select_reasoning_core_records([r])
    assert len(core) == 0
    assert any("generic_predicate_not_canonical" in x["reason"] for x in excluded)
