"""Smoke tests for controlled vocabulary builder output."""

from pathlib import Path

import pandas as pd
import pytest

from law_side.controlled_vocabulary_builder import write_controlled_vocabulary_excel


def test_build_controlled_vocabulary_columns_and_sheets(tmp_path: Path) -> None:
    seed = Path("data/processed/rulebase/rulebase_seed.xlsx")
    if not seed.exists():
        pytest.skip("rulebase_seed.xlsx not present")
    out = tmp_path / "cv.xlsx"
    write_controlled_vocabulary_excel(seed, out, predicate_lexicon_path=None)
    xl = pd.ExcelFile(out)
    assert set(xl.sheet_names) == {
        "predicate_vocabulary",
        "object_vocabulary",
        "effect_vocabulary",
        "subject_authority_scope",
        "metric_vocabulary",
    }
    pred = pd.read_excel(out, sheet_name="predicate_vocabulary")
    assert "predicate_family" in pred.columns
    assert "predicate_canonical" in pred.columns
    assert "predicate_typed" in pred.columns
    assert "can_ra_soat" in pred.columns
    assert "do_tin_cay" in pred.columns
    assert set(pred["can_ra_soat"].dropna().unique()).issubset({"co", "khong"})
    assert set(pred["do_tin_cay"].dropna().unique()).issubset({"cao", "trung_binh", "thap"})
    assert len(pred) > 0

    for sheet in ("object_vocabulary", "effect_vocabulary", "subject_authority_scope", "metric_vocabulary"):
        t = pd.read_excel(out, sheet_name=sheet)
        assert "can_ra_soat" in t.columns
        assert "do_tin_cay" in t.columns
        if len(t):
            assert set(t["can_ra_soat"].dropna().unique()).issubset({"co", "khong"})
            assert set(t["do_tin_cay"].dropna().unique()).issubset({"cao", "trung_binh", "thap"})
