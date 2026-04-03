"""Tests for ProbLog export from rules_reasoning_core."""

from __future__ import annotations

from pathlib import Path

from law_side.rulebase_reasoning_core_problog import (
    export_reasoning_core_problog,
    normalize_threshold_op,
    sanitize_atom,
)


def test_normalize_threshold_op():
    assert normalize_threshold_op(">=") == "ge"
    assert normalize_threshold_op("eq") == "eq"


def test_sanitize_atom_digit_prefix():
    a = sanitize_atom("123abc")
    assert a is not None
    assert a.startswith("x_")


def test_minimal_export(tmp_path: Path):
    pkg = {
        "rules_reasoning_core": [
            {
                "rule_id": "R1",
                "logic_form": "threshold",
                "head": {"predicate": "threshold", "args": ["m", ">=", 20.0, "pct"]},
                "body": [],
                "metadata": {"provenance": {"source_ref_full": "A", "source_ref": "b"}},
                "selected_for_reasoning": True,
            }
        ]
    }
    r = export_reasoning_core_problog(pkg)
    assert "threshold(m, ge, 20, pct)." in r["main_pl"]
    assert r["report"]["export_summary"]["rules_exported_ok"] == 1

