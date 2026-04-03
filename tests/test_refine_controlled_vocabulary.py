"""Tests for controlled vocabulary refinement."""

from pathlib import Path

import pytest

from law_side.refine_controlled_vocabulary import (
    is_action_obligation_effect_slug,
    refine_controlled_vocabulary_workbook,
    should_drop_object_row,
    split_effect_exception_condition,
)


def test_split_tru_truong_hop_with_underscore() -> None:
    s = (
        "duoc_cap_giay_chung_nhan_dang_ky_doanh_nghiep_tru_truong_hop_dieu_le_"
        "cong_ty_hoac_hop_dong"
    )
    base, frags = split_effect_exception_condition(s)
    assert frags
    assert base == "duoc_cap_giay_chung_nhan_dang_ky_doanh_nghiep"
    assert frags[0][0] == "exception"


def test_split_chap_thuan_tru_truong_hop() -> None:
    s = "chap_thuan_tru_truong_hop_hoi_dong_thanh_vien_quyet_dinh_thoi_han_khac"
    base, frags = split_effect_exception_condition(s)
    assert frags
    assert base == "chap_thuan"
    assert "tru_truong_hop" in frags[0][1]


def test_action_cong_ty_not_split_as_condition() -> None:
    s = "cong_ty_cap_nhat_kip_thoi_thay_doi_co_dong_trong_so_dang_ky_co_dong_theo_yeu_cau_cua_co_dong_co_lien_quan"
    assert is_action_obligation_effect_slug(s) is True


def test_drop_object_cue() -> None:
    assert should_drop_object_row("khi_dang_ky_thanh_lap_doanh_nghiep") is True
    assert should_drop_object_row("giay_chung_nhan_dang_ky_doanh_nghiep") is False


def test_refine_workbook_smoke(tmp_path: Path) -> None:
    seed = Path("data/processed/rulebase/rulebase_seed.xlsx")
    draft = Path("data/processed/ontology/controlled_vocabulary.xlsx")
    if not seed.exists() or not draft.exists():
        pytest.skip("seed or vocabulary missing")
    out = tmp_path / "cv_refined.xlsx"
    refine_controlled_vocabulary_workbook(draft, seed, out_path=out)
    import pandas as pd

    assert "modifier_fragments" in pd.ExcelFile(out).sheet_names
