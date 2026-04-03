"""Tests for rulebase_seed -> JSONL / logic export."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(
    not (REPO / "data/processed/rulebase/rulebase_seed.xlsx").exists(),
    reason="rulebase_seed.xlsx not present",
)
def test_export_produces_matching_counts() -> None:
    from law_side.rulebase_export_formats import export_rulebase_formats

    xlsx = REPO / "data/processed/rulebase/rulebase_seed.xlsx"
    out_j = REPO / "data/processed/rulebase/_test_rulebase.jsonl"
    out_l = REPO / "data/processed/rulebase/_test_rulebase_logic.json"
    try:
        n, m, _stats = export_rulebase_formats(xlsx, out_j, out_l)
        df = pd.read_excel(xlsx)
        assert n == len(df) == m
        lines = out_j.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == n
        payload = json.loads(out_l.read_text(encoding="utf-8"))
        assert payload["rule_count"] == n
        assert len(payload["rules"]) == n
    finally:
        out_j.unlink(missing_ok=True)
        out_l.unlink(missing_ok=True)


def test_row_to_jsonl_has_all_blocks() -> None:
    from law_side.rulebase_export_formats import JSONL_BLOCKS, row_to_jsonl_object

    row = pd.Series({k: None for block in JSONL_BLOCKS for k in JSONL_BLOCKS[block]})
    row["rule_id"] = "R1"
    obj = row_to_jsonl_object(row)
    assert set(obj.keys()) == set(JSONL_BLOCKS.keys())


def test_rich_jsonl_has_normalized_vocab_block() -> None:
    from law_side.rulebase_export_formats import build_rich_jsonl_object
    from law_side.rulebase_vocab_index import NormalizedVocab

    row = pd.Series({"rule_id": "R1", "chu_the": "công ty"})
    norm = NormalizedVocab(predicate_canonical="test_pred", normalization_status="full")
    obj = build_rich_jsonl_object(row, norm)
    assert "normalized_vocab" in obj
    assert obj["normalized_vocab"]["predicate_canonical"] == "test_pred"
