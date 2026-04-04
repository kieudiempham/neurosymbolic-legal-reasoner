"""Layer 2 — normalized logical sketch from Layer 1 (v5 + condition + entity registry)."""

from __future__ import annotations

import re
from typing import Any

from question_side.ambiguity import make_ambiguity
from question_side.condition_normalizer import normalize_condition_text
from question_side.entity_registry import resolve_subject_entity
from schemas.question_parse import AssertionStatus, Layer1Parse, Layer2Parse
from utils.text import slug_token


def _lower_blob(l1: Layer1Parse) -> str:
    return (l1.subject_text + " " + l1.action_text + " " + l1.condition_text).lower()


def _detect_change_legal_rep(low: str) -> bool:
    return bool(
        re.search(
            r"(đổi|thay đổi).*(đại diện|người đại diện).*(pháp luật|theo pháp luật)",
            low,
        )
    )


def _detect_register_change(low: str) -> bool:
    return "đăng ký" in low and ("thay đổi" in low or "đổi" in low)


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


def build_layer2(
    layer1: Layer1Parse,
    user_facts: list[str],
    *,
    forced_condition_atoms: list[str] | None = None,
) -> Layer2Parse:
    """Build goal, atoms, facts; uses entity registry + condition normalization."""
    full_blob = f"{layer1.subject_text} {layer1.action_text} {layer1.condition_text}"
    subj, subj_type, registry, mentions = resolve_subject_entity(full_blob)
    low = _lower_blob(layer1).replace("’", "'")

    ast = _assertion_status_normalized(layer1.assertion_status)
    cn = normalize_condition_text(
        layer1.condition_text,
        actor_entity_id=subj,
        actor_role=subj_type,
        assertion_status=ast,
    )

    condition_atoms: list[str] = []
    ambiguities: list[dict[str, Any]] = []

    if forced_condition_atoms:
        condition_atoms = list(forced_condition_atoms)
    else:
        if cn.primary_atom:
            condition_atoms.append(cn.primary_atom)
        for a in cn.alternative_atoms:
            if a not in condition_atoms:
                condition_atoms.append(a)
        if _detect_change_legal_rep(low) and not any(
            "thay_doi_nguoi_dai_dien" in a or "change_legal_representative" in a for a in condition_atoms
        ):
            condition_atoms.insert(0, f"thay_doi_nguoi_dai_dien_theo_phap_luat({subj})")

        if cn.confidence < 0.72 or cn.ambiguity_reason:
            gap = 0.1
            ambiguities.append(
                make_ambiguity(
                    kind="ambiguous_condition",
                    field="condition_text",
                    source_text=layer1.condition_text or cn.frame.source_text,
                    candidates=[cn.primary_atom] + cn.alternative_atoms,
                    confidence_gap=gap,
                    blocking=cn.confidence < 0.55,
                    priority=1 if cn.confidence < 0.55 else 8,
                    blocking_reason="condition_canonical_mapping_uncertain",
                )
            )

    if ast == "ambiguous":
        ambiguities.append(
            make_ambiguity(
                kind="ambiguous_goal",
                field="assertion_status",
                source_text=layer1.action_text or "",
                candidates=["asserted", "hypothetical"],
                confidence_gap=0.2,
                blocking=False,
                priority=10,
                blocking_reason="assertion_not_fixed",
            )
        )

    if len(mentions) > 1 and len({m.role_guess for m in mentions}) > 1:
        ambiguities.append(
            make_ambiguity(
                kind="ambiguous_subject",
                field="subject_text",
                source_text=full_blob[:200],
                candidates=[m.surface[:80] for m in mentions[:3]],
                confidence_gap=0.15,
                blocking=False,
                priority=6,
                blocking_reason="multiple_entity_mentions",
            )
        )

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
    atoms_sig = "|".join(condition_atoms[:8]) if condition_atoms else "_"
    qrc = (
        f"ut={ut}|subj={subj}|role={subj_type}|focus={focus}|pred={goal.get('predicate')}"
        f"|atoms={atoms_sig}|goal={goal.get('predicate')}:{','.join(str(a) for a in goal.get('args', []))}"
    )

    diag: dict[str, Any] = {
        "normalizer": "v3_registry_condition",
        "focus": focus,
        "assertion_status_normalized": ast,
        "hypothetical_condition_refs": hypothetical_refs,
        "condition_normalization": cn.model_dump(mode="json"),
        "ambiguities": ambiguities,
        "entity_registry": {
            "primary_subject_id": registry.primary_subject_id,
            "records": {k: v.model_dump(mode="json") for k, v in registry.records.items()},
            "mentions": [m.model_dump(mode="json") for m in mentions],
        },
    }
    if ast == "ambiguous":
        diag["assertion_ambiguous"] = True

    if forced_condition_atoms:
        diag["applied_forced_condition_atoms"] = True

    return Layer2Parse(
        subject_normalized=subj,
        subject_type_guess=subj_type,
        condition_atoms=condition_atoms,
        facts=facts,
        goal=goal,
        query_rule_candidate=qrc,
        diagnostics=diag,
    )
