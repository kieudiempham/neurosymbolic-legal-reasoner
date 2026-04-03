"""Tests for rulebase_seed post-processing."""

from __future__ import annotations

from law_side.rulebase_seed_refiner import infer_threshold_fields


def test_infer_at_least_percent_share() -> None:
    s = "Các cổ đông sáng lập phải cùng nhau đăng ký mua ít nhất 20% tổng số cổ phần phổ thông được quyền chào bán."
    got = infer_threshold_fields(s)
    assert got.get("gia_tri_nguong") == "20"
    assert got.get("don_vi_nguong") == "phan_tram"
    assert got.get("toan_tu_so_sanh") == ">="


def test_infer_member_range() -> None:
    s = "Từ 02 đến 50 thành viên góp vốn thành lập công ty."
    got = infer_threshold_fields(s)
    assert got.get("gia_tri_tu") == "2"
    assert got.get("gia_tri_den") == "50"
    assert got.get("kieu_khoang") == "dong"
