"""Unit tests for khoảng ngưỡng regex in scripts/refine_rulebase_seed_round.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from refine_rulebase_seed_round import _parse_range_from_text  # noqa: E402


@pytest.mark.parametrize(
    ("text", "expected_tu", "expected_den", "kieu", "don_vi"),
    [
        ("trên 10% đến dưới 35%", 10.0, 35.0, "mo_hai_dau", "phan_tram"),
        ("Trên 10 % đến dưới 35 %", 10.0, 35.0, "mo_hai_dau", "phan_tram"),
        ("từ 10% đến 35%", 10.0, 35.0, "dong", "phan_tram"),
        ("từ 02 đến 50 thành viên", 2.0, 50.0, "dong", "thanh_vien"),
        ("trong khoảng từ 30 đến 90 ngày", 30.0, 90.0, "dong", "ngay"),
        ("trong thời hạn từ 30 đến 90 ngày", 30.0, 90.0, "dong", "ngay"),
        ("từ 5 đến không quá 20 %", 5.0, 20.0, "mo_phai", "phan_tram"),
    ],
)
def test_parse_range_examples(
    text: str,
    expected_tu: float,
    expected_den: float,
    kieu: str,
    don_vi: str,
) -> None:
    out = _parse_range_from_text(text)
    assert out is not None, f"no match for: {text!r}"
    assert out["gia_tri_tu"] == expected_tu
    assert out["gia_tri_den"] == expected_den
    assert out["kieu_khoang"] == kieu
    assert out["don_vi_nguong"] == don_vi


def test_tu_den_toi_alias() -> None:
    out = _parse_range_from_text("từ 1 tới 5 ngày")
    assert out is not None
    assert out["gia_tri_tu"] == 1.0
    assert out["gia_tri_den"] == 5.0
    assert out["don_vi_nguong"] == "ngay"


def test_no_match_single_deadline() -> None:
    """Một ngưỡng một phía (không phải khoảng) — không khớp mẫu khoảng."""
    assert _parse_range_from_text("trong thời hạn 90 ngày kể từ ngày được cấp GCN") is None


def test_den_typo_still_matches() -> None:
    """đến viết tắt / thiếu dấu (đen) vẫn khớp."""
    out = _parse_range_from_text("từ 10% đen 35%")
    assert out is not None
    assert out["gia_tri_tu"] == 10.0
    assert out["gia_tri_den"] == 35.0
