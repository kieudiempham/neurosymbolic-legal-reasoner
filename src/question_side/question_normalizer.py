"""Layer 2 — normalized logical sketch from Layer 1."""

from __future__ import annotations

import re
from typing import Any

from schemas.question_parse import Layer1Parse, Layer2Parse
from utils.text import slug_token


def _detect_change_legal_rep(low: str) -> bool:
    return bool(
        re.search(
            r"(đổi|thay đổi).*(đại diện|người đại diện).*(pháp luật|theo pháp luật)",
            low,
        )
    )


def _detect_register_change(low: str) -> bool:
    return "đăng ký" in low and ("thay đổi" in low or "đổi" in low)


def build_layer2(layer1: Layer1Parse, user_facts: list[str]) -> Layer2Parse:
    """Build a goal + atoms. Uses curated slugs compatible with rulebase."""
    subj = "company_x"
    low = layer1.subject_text.lower() + " " + layer1.action_text.lower()
    low = low.replace("’", "'")

    condition_atoms: list[str] = []
    if _detect_change_legal_rep(low):
        condition_atoms.append(f"change_legal_representative({subj})")

    focus = layer1.question_focus
    goal: dict[str, Any] = {"predicate": "unknown", "args": []}

    if (
        focus == "obligation"
        and (
            "cập nhật" in layer1.action_text.lower()
            or "cap nhat" in low.replace(" ", "")
        )
        and ("cổ đông" in layer1.action_text.lower() or "co dong" in low)
    ):
        goal = {
            "predicate": "obligation",
            "args": [subj, "cap_nhat_thong_tin", "quy_dinh_tai_dieu_le_cong_ty"],
        }
    elif focus == "permission":
        act = slug_token(layer1.action_text)[:48] or "hanh_vi"
        if "phieu_lay_y_kien" in low or "phiếu lấy ý kiến" in layer1.action_text.lower():
            act = "gui_phieu_lay_y_kien"
        goal = {"predicate": "permission", "args": [subj, act, "phieu_lay_y_kien"]}
    elif focus == "obligation" and _detect_register_change(low):
        goal = {
            "predicate": "obligation",
            "args": [subj, "dang_ky_thay_doi", "thay_doi_dang_ky"],
        }
    elif focus == "obligation":
        act = slug_token(layer1.action_text)[:48] or "hanh_vi"
        goal = {"predicate": "obligation", "args": [subj, act, "doi_tuong"]}
    elif focus == "deadline":
        goal = {
            "predicate": "deadline",
            "args": [slug_token(layer1.action_text) or "hanh_dong", 0, "ngay", "moc_thoi_gian"],
        }
    elif focus == "threshold":
        goal = {"predicate": "threshold", "args": ["metric", "ge", 0, "don_vi"]}
    else:
        goal = {"predicate": "obligation", "args": [subj, "hanh_vi", "doi_tuong"]}

    facts = list(user_facts)
    qrc = f"{goal['predicate']}:{','.join(str(a) for a in goal.get('args', []))}"

    return Layer2Parse(
        subject_normalized=subj,
        condition_atoms=condition_atoms,
        facts=facts,
        goal=goal,
        query_rule_candidate=qrc,
        diagnostics={"normalizer": "v1", "focus": focus},
    )
