"""Layer 2 — normalized logical sketch from Layer 1 (v5 mapping)."""

from __future__ import annotations

import re
from typing import Any

from schemas.question_parse import AssertionStatus, Layer1Parse, Layer2Parse
from utils.text import slug_token


def _lower_blob(l1: Layer1Parse) -> str:
    return (l1.subject_text + " " + l1.action_text + " " + l1.condition_text).lower()


def _infer_subject_type_and_slug(l1: Layer1Parse) -> tuple[str, str]:
    """Returns (subject_normalized_slug, subject_type_guess)."""
    blob = _lower_blob(l1)
    if any(x in blob for x in ("hộ kinh doanh", "ho kinh doanh")):
        return "business_household_x", "business_household"
    if any(x in blob for x in ("cổ đông", "co dong", "cổ phần")):
        return "shareholder_x", "shareholder"
    if any(x in blob for x in ("người đại diện", "dai dien phap luat", "đại diện pháp luật")):
        return "legal_representative_x", "legal_representative"
    if any(x in blob for x in ("thành lập", "thanh lap", "sáng lập")):
        return "founder_x", "founder"
    if any(x in blob for x in ("doanh nghiệp", "doanh nghiep", "công ty", "cong ty")):
        return "enterprise_x", "enterprise"
    return "company_x", "company"


def _detect_change_legal_rep(low: str) -> bool:
    return bool(
        re.search(
            r"(đổi|thay đổi).*(đại diện|người đại diện).*(pháp luật|theo pháp luật)",
            low,
        )
    )


def _detect_register_change(low: str) -> bool:
    return "đăng ký" in low and ("thay đổi" in low or "đổi" in low)


def _condition_text_to_atoms(condition_text: str, subj: str) -> list[str]:
    if not (condition_text or "").strip():
        return []
    low = condition_text.lower()
    atoms: list[str] = []
    if _detect_change_legal_rep(low):
        atoms.append(f"change_legal_representative({subj})")
    if "đăng ký" in low and ("thay đổi" in low or "thay doi" in low):
        atoms.append(f"registration_change({subj})")
    if re.search(r"cổ đông|co dong|góp vốn", low):
        atoms.append(f"shareholder_context({subj})")
    if re.search(r"nếu|neu|khi|trường hợp", condition_text, re.IGNORECASE):
        atoms.append(f"conditional_clause({slug_token(condition_text)[:40] or 'cond'})")
    if not atoms:
        atoms.append(f"stated_condition({slug_token(condition_text)[:56] or 'cond'})")
    return atoms


def _modality_to_goal_predicate(
    focus: str,
    modality_text: str,
) -> str:
    mt = (modality_text or "").lower()
    if focus == "prohibition" or any(x in mt for x in ("không được", "cấm")):
        return "prohibition"
    if focus in ("permission",) or any(x in mt for x in ("được", "có quyền", "phép")):
        return "permission"
    if focus == "deadline":
        return "deadline"
    if focus == "threshold":
        return "threshold"
    if focus in ("procedure", "legal_consequence"):
        return "obligation"
    return "obligation"


def _assertion_status_normalized(st: AssertionStatus | str) -> str:
    s = str(st)
    if s == "factual":
        return "asserted"
    return s


def build_layer2(layer1: Layer1Parse, user_facts: list[str]) -> Layer2Parse:
    """Build goal, atoms, facts (assertion-aware), query_rule_candidate."""
    subj, subj_type = _infer_subject_type_and_slug(layer1)
    low = _lower_blob(layer1).replace("’", "'")

    condition_atoms: list[str] = []
    condition_atoms.extend(_condition_text_to_atoms(layer1.condition_text, subj))
    if _detect_change_legal_rep(low):
        if not any("change_legal_representative" in a for a in condition_atoms):
            condition_atoms.insert(0, f"change_legal_representative({subj})")

    focus = layer1.question_focus
    pred = _modality_to_goal_predicate(focus, layer1.modality_text)
    act = slug_token(layer1.action_text)[:48] or "hanh_vi"
    goal: dict[str, Any] = {"predicate": "unknown", "args": []}

    if (
        focus == "obligation"
        and ("cập nhật" in layer1.action_text.lower() or "cap nhat" in low.replace(" ", ""))
        and ("cổ đông" in layer1.action_text.lower() or "co dong" in low)
    ):
        goal = {
            "predicate": "obligation",
            "args": [subj, "cap_nhat_thong_tin", "quy_dinh_tai_dieu_le_cong_ty"],
        }
    elif pred == "permission" or focus == "permission":
        if "phieu_lay_y_kien" in low or "phiếu lấy ý kiến" in layer1.action_text.lower():
            act = "gui_phieu_lay_y_kien"
        goal = {"predicate": "permission", "args": [subj, act, "phieu_lay_y_kien"]}
    elif focus == "obligation" and _detect_register_change(low):
        goal = {
            "predicate": "obligation",
            "args": [subj, "dang_ky_thay_doi", "thay_doi_dang_ky"],
        }
    elif pred == "prohibition":
        goal = {"predicate": "prohibition", "args": [subj, act, "doi_tuong"]}
    elif focus == "deadline":
        dl = layer1.deadline_text or layer1.time_text or "moc_thoi_gian"
        goal = {
            "predicate": "deadline",
            "args": [slug_token(layer1.action_text) or "hanh_dong", 0, "ngay", slug_token(dl)[:32] or "moc"],
        }
    elif focus == "threshold":
        goal = {"predicate": "threshold", "args": ["metric", "ge", 0, "don_vi"]}
    elif focus in ("procedure", "legal_consequence"):
        goal = {
            "predicate": "obligation",
            "args": [subj, act, "procedure_or_consequence"],
        }
    elif pred == "obligation" or focus == "obligation":
        goal = {"predicate": "obligation", "args": [subj, act, "doi_tuong"]}
    else:
        goal = {"predicate": pred, "args": [subj, act, "doi_tuong"]}

    ast = _assertion_status_normalized(layer1.assertion_status)
    base_facts = list(user_facts)
    hypothetical_refs: list[str] = []
    if ast == "asserted" and layer1.condition_text.strip():
        facts = base_facts + [f"asserted:{slug_token(layer1.condition_text)[:56]}"]
    elif ast == "hypothetical":
        facts = base_facts
        if layer1.condition_text.strip():
            hypothetical_refs = [f"hypothetical:{slug_token(layer1.condition_text)[:56]}"]
    else:
        facts = base_facts

    ut = layer1.utterance_type
    atoms_sig = "|".join(condition_atoms[:6]) if condition_atoms else "_"
    qrc = f"ut={ut}|focus={focus}|pred={goal.get('predicate')}|atoms={atoms_sig}|goal={goal.get('predicate')}:{','.join(str(a) for a in goal.get('args', []))}"

    diag: dict[str, Any] = {
        "normalizer": "v2",
        "focus": focus,
        "assertion_status_normalized": ast,
        "hypothetical_condition_refs": hypothetical_refs,
    }
    if ast == "ambiguous":
        diag["assertion_ambiguous"] = True

    return Layer2Parse(
        subject_normalized=subj,
        subject_type_guess=subj_type,
        condition_atoms=condition_atoms,
        facts=facts,
        goal=goal,
        query_rule_candidate=qrc,
        diagnostics=diag,
    )
