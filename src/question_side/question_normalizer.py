"""Layer 2 — normalized logical sketch from Layer 1 (v5 + condition + entity registry)."""

from __future__ import annotations

import re
from typing import Any

from question_side.ambiguity import make_ambiguity
from question_side.condition_normalizer import normalize_condition_text
from question_side.entity_registry import resolve_subject_entity
from schemas.question_parse import AssertionStatus, Layer1Parse, Layer2Parse
from utils.text import lower_fold
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


def _has_strong_register_change_action_evidence(
    *,
    action_text: str,
    action_canonical_hint: str,
    rescued_action: str,
    low_blob: str,
) -> bool:
    act_blob = lower_fold(action_text or "")
    hint_blob = lower_fold((action_canonical_hint or "").replace("_", " "))
    rescued_blob = lower_fold((rescued_action or "").replace("_", " "))
    full = f"{act_blob} {hint_blob} {rescued_blob} {low_blob}"

    if any(x in full for x in ("bo sung ho so", "bổ sung hồ sơ", "nop ho so", "nộp hồ sơ")):
        if not any(x in full for x in ("dang ky thay doi", "đăng ký thay đổi")):
            return False

    explicit_register_change = any(
        x in full
        for x in (
            "dang ky thay doi",
            "đăng ký thay đổi",
            "thay doi dang ky",
            "thay đổi đăng ký",
        )
    )
    return explicit_register_change


def _is_locked_action_from_layer1(action_text: str, action_hint: str) -> bool:
    blob = lower_fold(f"{action_text or ''} {(action_hint or '').replace('_', ' ')}")
    return any(
        x in blob
        for x in (
            "bo sung ho so",
            "bo_sung_ho_so",
            "hau qua phap ly",
            "hau_qua_phap_ly",
            "che tai ap dung",
            "che_tai_ap_dung",
            "gia tri phap ly",
            "gia_tri_phap_ly",
        )
    )


def _usable_legal_effect_action(action: str) -> bool:
    a = _norm_hint_token(action)
    if not a or a in {"unknown", "hanh_vi"}:
        return False
    return a in {
        "hau_qua_phap_ly",
        "che_tai_ap_dung",
        "gia_tri_phap_ly",
        "bi_xu_ly",
        "xu_phat",
        "vo_hieu",
    }


def _modality_to_goal_predicate(
    focus: str,
    modality_text: str,
) -> str:
    if focus == "unknown":
        return "unknown"
    if focus == "applicability":
        return "applies_if"
    if focus == "legal_effect":
        return "legal_effect"
    if focus == "legal_consequence":
        return "legal_effect"
    if focus in ("compensation_rule", "entitlement_rule", "payment_obligation_explanation"):
        return "legal_effect"
    if focus == "refund_eligibility":
        return "applies_if"
    if focus == "deadline":
        return "deadline"
    if focus == "threshold":
        return "threshold"
    if focus == "procedure":
        return "obligation"

    mt = (modality_text or "").lower()
    if focus == "prohibition" or any(x in mt for x in ("không được", "cấm")):
        return "prohibition"
    if focus in ("permission",) or any(x in mt for x in ("được", "có quyền", "phép")):
        return "permission"
    return "obligation"


_VALID_FOCUS: set[str] = {
    "obligation",
    "permission",
    "prohibition",
    "deadline",
    "threshold",
    "exception",
    "applicability",
    "dossier",
    "legal_effect",
    "authority",
    "procedure",
    "legal_consequence",
    "compensation_rule",
    "entitlement_rule",
    "refund_eligibility",
    "payment_obligation_explanation",
    "unknown",
}


def _norm_hint_token(s: Any) -> str:
    return str(s or "").strip().lower()


def _focus_from_condition_family_hint(condition_family_hint: str) -> str:
    fam = _norm_hint_token(condition_family_hint)
    if fam == "deadline":
        return "deadline"
    if fam == "threshold":
        return "threshold"
    if fam == "exception":
        return "exception"
    if fam == "legal_consequence":
        return "legal_effect"
    if fam == "legal_effect_trigger":
        return "legal_effect"
    if fam == "prohibition_trigger":
        return "prohibition"
    if fam == "obligation_trigger":
        return "obligation"
    if fam in ("eligibility", "applicability"):
        return "applicability"
    return "unknown"


def _choose_effective_focus(
    *,
    focus: str,
    modality_text: str,
    question_focus_hint: str,
    condition_family_hint: str,
) -> str:
    cur = _norm_hint_token(focus)
    if cur == "legal_consequence":
        cur = "legal_effect"
    qhint = _norm_hint_token(question_focus_hint)
    fam_focus = _focus_from_condition_family_hint(condition_family_hint)
    mod = lower_fold(modality_text or "")
    hard_obligation = any(x in mod for x in ("phai", "bat buoc", "nghia vu"))

    if cur == "unknown":
        if qhint in _VALID_FOCUS and qhint != "unknown":
            return qhint
        if fam_focus != "unknown":
            return fam_focus
        return cur

    if cur == "obligation" and not hard_obligation:
        if qhint in _VALID_FOCUS and qhint not in ("unknown", "obligation"):
            return qhint
        if fam_focus not in ("unknown", "obligation"):
            return fam_focus
    return cur


def _rescue_subject_type(subj_type: str, subject_type_hint: str) -> str:
    current = _norm_hint_token(subj_type)
    hint = _norm_hint_token(subject_type_hint)
    compat = {"unknown", "employer", "employee", "taxpayer", "business_household"}
    if current in compat and current != "unknown":
        return current
    mapping = {
        "company": "unknown",
        "employer": "employer",
        "employee": "employee",
        "taxpayer": "taxpayer",
        "business_household": "business_household",
        "individual": "unknown",
        "authority": "unknown",
    }
    rescued = mapping.get(hint, "unknown")
    if rescued in compat:
        return rescued
    return "unknown"


def _rescue_subject_normalized(
    subj: str,
    *,
    subject_type_guess: str,
    subject_type_hint: str,
    domain_hint: str,
    subject_text: str = "",
) -> str:
    cur = str(subj or "").strip() or "unknown_subject_x"
    if cur != "unknown_subject_x" and not cur.startswith("unknown_subject"):
        return cur

    st = _norm_hint_token(subject_type_guess)
    sh = _norm_hint_token(subject_type_hint)
    dh = _norm_hint_token(domain_hint)
    subj_text = lower_fold(subject_text or "")

    if st in ("employee", "employer", "taxpayer", "business_household"):
        return f"{st}_x"
    if sh in ("employee", "employer", "taxpayer", "business_household"):
        return f"{sh}_x"
    if dh == "tax":
        return "taxpayer_x"
    if sh == "company" or dh in ("enterprise", "registration"):
        return "company_x"
    if sh == "authority" or any(x in subj_text for x in ("co quan", "uy ban", "so ke hoach", "bo ")):
        return "authority_x"
    if sh == "individual" or any(x in subj_text for x in ("ca nhan", "nguoi dan", "nguoi nop")):
        return "individual_x"
    return cur


def _object_from_action_hint(action_hint: str) -> str:
    ah = _norm_hint_token(action_hint)
    if not ah:
        return "doi_tuong"
    if "ho_so" in ah:
        return "ho_so"
    if "dang_ky" in ah:
        return "dang_ky"
    if "khai_thue" in ah or "thue" in ah:
        return "nghia_vu_thue"
    if "thanh_toan" in ah:
        return "khoan_thanh_toan"
    if "thong_bao" in ah:
        return "thong_bao"
    return "doi_tuong"


def _prefer_action_hint_over_compact(compact: str, action_hint: str) -> bool:
    ah = _norm_hint_token(action_hint)
    c = _norm_hint_token(compact)
    if not ah or ah in ("unknown", "hanh_vi"):
        return False
    if not c:
        return True
    weak_tokens = {
        "hanh_vi",
        "thuc_hien",
        "xu_ly",
        "thao_tac",
        "thuc_hien_viec",
        "quy_dinh",
        "thu_tuc",
        "van_de",
    }

    def _action_quality_score(token: str) -> float:
        t = _norm_hint_token(token)
        if not t:
            return 0.0
        parts = [p for p in t.split("_") if p]
        score = min(0.5, len(parts) * 0.08)
        legal_specific = (
            "dang_ky",
            "nop_ho_so",
            "thong_bao",
            "khai_thue",
            "thanh_toan",
            "bao_truoc",
            "cham_dut",
            "xu_phat",
            "hoan_thue",
        )
        if any(k in t for k in legal_specific):
            score += 0.38
        if t in weak_tokens or any(x in t for x in ("hanh_vi", "doi_tuong", "thu_tuc", "thuc_hien")):
            score -= 0.28
        if len(parts) <= 2:
            score -= 0.1
        return max(0.0, min(1.0, score))

    compact_score = _action_quality_score(c)
    hint_score = _action_quality_score(ah)

    if hint_score >= 0.58 and compact_score <= 0.45:
        return True
    if hint_score - compact_score >= 0.16:
        return True
    return False


def _canonical_action_and_object(action_text: str, low_blob: str, action_hint: str = "") -> tuple[str, str, float]:
    low_action = (action_text or "").lower()
    action_slug = slug_token(action_text)

    patterns: list[tuple[tuple[str, ...], str, str]] = [
        (("đơn phương chấm dứt hợp đồng lao động", "don phuong cham dut hop dong lao dong"), "don_phuong_cham_dut_hop_dong_lao_dong", "hop_dong_lao_dong"),
        (("xử lý kỷ luật sa thải", "xu ly ky luat sa thai"), "xu_ly_ky_luat_sa_thai", "ky_luat_sa_thai"),
        (("trả lương", "tra luong"), "tra_luong", "tien_luong"),
        (("làm thêm giờ", "lam them gio"), "tra_luong_lam_them", "tien_luong_lam_them"),
        (("hoàn thuế", "hoan thue"), "hoan_thue", "thue_gia_tri_gia_tang"),
        (("được tính vào", "duoc tinh vao"), "duoc_tinh_vao_chi_phi_duoc_tru", "chi_phi_duoc_tru"),
        (("bị xử lý", "bi xu ly"), "bi_xu_ly", "che_tai"),
        (("tham gia bảo hiểm xã hội", "tham gia bao hiem xa hoi"), "tham_gia_bao_hiem_xa_hoi", "bao_hiem_xa_hoi"),
        (("báo trước", "bao truoc"), "bao_truoc", "thong_bao"),
        (("thanh toán", "thanh toan"), "thanh_toan_quyen_loi", "quyen_loi_lien_quan"),
        (("thử việc", "thu viec"), "xac_dinh_thoi_gian_thu_viec", "thoi_gian_thu_viec"),
        (("trường hợp", "truong hop"), "xac_dinh_truong_hop_ap_dung", "truong_hop_ap_dung"),
    ]

    for cues, act, obj in patterns:
        if any(c in low_action or c in low_blob for c in cues):
            return act, obj, 0.88

    compact = re.sub(
        r"\b(co duoc|co quyen|duoc phep|co phai|phai|bat buoc|nghia vu|nhu the nao|bao lau|bao nhieu|khi nao)\b",
        "",
        action_slug,
    )
    compact = re.sub(r"_+", "_", compact).strip("_")
    if compact:
        compact = "_".join(compact.split("_")[:6])
    if compact and _prefer_action_hint_over_compact(compact, action_hint):
        ah = _norm_hint_token(action_hint)
        return ah, _object_from_action_hint(ah), 0.76
    if compact:
        return compact, "doi_tuong", 0.52

    ah = _norm_hint_token(action_hint)
    if ah and ah not in ("unknown", "hanh_vi"):
        return ah, _object_from_action_hint(ah), 0.74

    return "hanh_vi", "doi_tuong", 0.52


def _goal_from_focus(
    *,
    focus: str,
    pred: str,
    subj: str,
    act: str,
    obj: str,
    cue_blob: str,
    has_toi_da_bao_lau: bool,
    threshold_core_cue: bool,
    threshold_metric_hint: bool,
    has_bao_nhieu: bool,
    has_khi_nao: bool,
    has_bao_lau: bool,
    has_deadline_anchor: bool,
) -> dict[str, Any]:
    if focus == "deadline":
        return {
            "predicate": "deadline",
            "args": [act or "hanh_dong", 0, "ngay", "moc_thoi_gian"],
        }
    if focus == "threshold":
        return _canonical_threshold_goal(cue_blob)
    if focus in ("applicability", "refund_eligibility"):
        return {"predicate": "applies_if", "args": [subj, act, obj]}
    if focus in (
        "legal_effect",
        "legal_consequence",
        "compensation_rule",
        "entitlement_rule",
        "payment_obligation_explanation",
    ):
        return {
            "predicate": "legal_effect",
            "args": [subj, act, obj],
        }
    if focus in ("procedure",):
        return {
            "predicate": "obligation",
            "args": [subj, act, "procedure_or_consequence"],
        }
    if pred == "permission" or focus == "permission":
        return {"predicate": "permission", "args": [subj, act, obj]}
    if pred == "prohibition":
        return {"predicate": "prohibition", "args": [subj, act, obj]}
    if pred == "obligation" or focus == "obligation":
        return {"predicate": "obligation", "args": [subj, act, obj]}
    if focus == "unknown":
        if has_toi_da_bao_lau:
            return _canonical_threshold_goal(cue_blob)
        if threshold_core_cue or (threshold_metric_hint and has_bao_nhieu):
            return _canonical_threshold_goal(cue_blob)
        if has_khi_nao or (has_bao_lau and has_deadline_anchor):
            return {"predicate": "deadline", "args": [act or "hanh_dong", 0, "ngay", "moc_thoi_gian"]}
        return {"predicate": "unknown", "args": []}
    if pred == "unknown":
        return {"predicate": "unknown", "args": []}
    return {"predicate": pred, "args": [subj, act, obj]}


def _assertion_status_normalized(st: AssertionStatus | str) -> str:
    s = str(st)
    if s == "factual":
        return "asserted"
    return s


def _should_ask_assertion_ambiguity(layer1: Layer1Parse, condition_conf: float) -> bool:
    """Ask asserted/hypothetical only when it can materially alter reasoning path."""
    if _assertion_status_normalized(layer1.assertion_status) != "ambiguous":
        return False

    cond = lower_fold(layer1.condition_text or "")
    if not cond.strip():
        return False

    if layer1.utterance_type in ("conditional_legal_question", "hypothetical_question"):
        return True

    hypo_markers = (
        "neu ",
        "nếu ",
        "gia su",
        "giả sử",
        "truong hop",
        "trường hợp",
        "se ",
        "sẽ ",
    )
    factual_markers = (
        "da ",
        "đã ",
        "dang ",
        "đang ",
        "vua ",
        "vừa ",
        "hien tai",
        "hiện tại",
    )
    has_hypo = any(m in cond for m in hypo_markers)
    has_factual = any(m in cond for m in factual_markers)

    if has_hypo and has_factual:
        return True
    if has_hypo and condition_conf >= 0.55:
        return True
    return False


def _canonical_threshold_goal(cue_blob: str) -> dict[str, Any]:
    blob = cue_blob or ""

    has_duration = "bao lau" in blob and any(x in blob for x in ("toi da", "toi thieu", "it nhat", "thu viec", "thoi gian"))
    if has_duration:
        metric = "duration_limit"
        if "thu viec" in blob:
            metric = "duration_limit_thoi_gian_thu_viec"
        op = "le" if "toi da" in blob else "ge"
        return {"predicate": "threshold", "args": [metric, op, "gioi_han_thoi_luong", "don_vi_thoi_gian"]}

    if "von dieu le" in blob or "muc von" in blob:
        op = "ge" if any(x in blob for x in ("toi thieu", "it nhat", "tu bao nhieu", "tu muc nao", "muc nao")) else "ge"
        return {"predicate": "threshold", "args": ["von_dieu_le", op, "nguong_von", "vnd"]}

    if ("luong" in blob and ("phan tram" in blob or "%" in blob)) or (
        "thu viec" in blob and any(x in blob for x in ("it nhat", "toi thieu", "duoc tra"))
    ):
        op = "ge" if any(x in blob for x in ("it nhat", "toi thieu")) else "le"
        return {"predicate": "threshold", "args": ["ty_le_luong_thu_viec", op, "nguong_ty_le", "phan_tram"]}

    if "doanh thu" in blob:
        op = "ge" if any(x in blob for x in ("tu bao nhieu", "tu muc nao", "muc nao", "toi thieu", "it nhat")) else "ge"
        return {"predicate": "threshold", "args": ["doanh_thu", op, "nguong_doanh_thu", "vnd"]}

    if any(x in blob for x in ("so lao dong", "bao nhieu lao dong", "tu bao nhieu lao dong", "tu muc lao dong")):
        op = "ge" if any(x in blob for x in ("tu bao nhieu", "it nhat", "toi thieu", "tu muc nao", "muc nao")) else "ge"
        return {"predicate": "threshold", "args": ["so_lao_dong", op, "nguong_so_luong", "nguoi"]}

    if "muc luong toi thieu" in blob:
        return {"predicate": "threshold", "args": ["muc_luong_toi_thieu", "ge", "nguong_luong", "vnd"]}

    if "ty le so huu" in blob or ("phan tram" in blob or "%" in blob):
        op = "ge" if any(x in blob for x in ("tu bao nhieu", "it nhat", "toi thieu", "muc nao")) else "ge"
        metric = "ty_le_so_huu" if "so huu" in blob else "ty_le_phan_tram"
        return {"predicate": "threshold", "args": [metric, op, "nguong_ty_le", "phan_tram"]}

    # Fallback still stays in threshold family (avoid drifting to other families).
    op = "ge" if any(x in blob for x in ("tu bao nhieu", "tu muc nao", "muc nao", "it nhat", "toi thieu")) else "ge"
    return {"predicate": "threshold", "args": ["threshold_value", op, "nguong_gia_tri", "don_vi"]}


def build_layer2(
    layer1: Layer1Parse,
    user_facts: list[str],
    *,
    forced_condition_atoms: list[str] | None = None,
) -> Layer2Parse:
    """Build goal, atoms, facts; uses entity registry + condition normalization."""
    l1_meta = dict(layer1.parse_metadata or {})
    question_focus_hint = _norm_hint_token(l1_meta.get("question_focus_hint"))
    action_canonical_hint = _norm_hint_token(l1_meta.get("action_canonical_hint"))
    used_fallback_label = _norm_hint_token(l1_meta.get("used_fallback_label"))
    if not action_canonical_hint and used_fallback_label and used_fallback_label != "unknown":
        action_canonical_hint = used_fallback_label
    subject_type_hint = _norm_hint_token(l1_meta.get("subject_type_hint"))
    domain_hint = _norm_hint_token(l1_meta.get("domain_hint"))
    condition_family_hint = _norm_hint_token(l1_meta.get("condition_family_hint"))

    full_blob = f"{layer1.subject_text} {layer1.action_text} {layer1.condition_text}"
    subj, subj_type, registry, mentions = resolve_subject_entity(full_blob)
    subj_type = _rescue_subject_type(subj_type, subject_type_hint)
    subj = _rescue_subject_normalized(
        subj,
        subject_type_guess=subj_type,
        subject_type_hint=subject_type_hint,
        domain_hint=domain_hint,
        subject_text=layer1.subject_text,
    )
    low = _lower_blob(layer1).replace("’", "'")

    ast = _assertion_status_normalized(layer1.assertion_status)
    effective_focus = _choose_effective_focus(
        focus=str(layer1.question_focus),
        modality_text=layer1.modality_text,
        question_focus_hint=question_focus_hint,
        condition_family_hint=condition_family_hint,
    )
    cn = normalize_condition_text(
        layer1.condition_text,
        actor_entity_id=subj,
        actor_role=subj_type,
        assertion_status=ast,
        question_focus=effective_focus,
        action_text=layer1.action_text or action_canonical_hint.replace("_", " "),
        subject_type=subject_type_hint,
        domain_hint=domain_hint,
        condition_family_hint=condition_family_hint,
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

        usable_primary_condition = bool(cn.primary_atom) and not cn.primary_atom.startswith("stated_condition(")
        if cn.confidence < 0.72 or cn.ambiguity_reason:
            should_block = (cn.confidence < 0.55) and not usable_primary_condition
            should_emit = True
            if usable_primary_condition and cn.confidence >= 0.56 and not cn.ambiguity_reason:
                should_emit = False
            gap = 0.1
            if should_emit:
                ambiguities.append(
                    make_ambiguity(
                        kind="ambiguous_condition",
                        field="condition_text",
                        source_text=layer1.condition_text or cn.frame.source_text,
                        candidates=[cn.primary_atom] + cn.alternative_atoms,
                        confidence_gap=gap,
                        blocking=should_block,
                        priority=2 if should_block else 8,
                        blocking_reason="condition_canonical_mapping_uncertain",
                    )
                )

    assertion_ambiguous_suppressed = False
    if ast == "ambiguous" and _should_ask_assertion_ambiguity(layer1, cn.confidence):
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
    elif ast == "ambiguous":
        assertion_ambiguous_suppressed = True

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

    focus = effective_focus
    pred = _modality_to_goal_predicate(focus, layer1.modality_text)
    act, obj, action_conf = _canonical_action_and_object(layer1.action_text, low, action_canonical_hint)

    # Keep Layer2 aligned with rescued Layer1 semantics for legal consequence/effect.
    if focus in {"legal_consequence", "legal_effect"}:
        hinted_action = _norm_hint_token(action_canonical_hint)
        if _usable_legal_effect_action(hinted_action):
            act = hinted_action
            obj = "doi_tuong"
            action_conf = max(action_conf, 0.76)
        elif _usable_legal_effect_action(_norm_hint_token(layer1.action_text)):
            act = _norm_hint_token(layer1.action_text)
            obj = "doi_tuong"
            action_conf = max(action_conf, 0.72)

    archetype_conf = float((layer1.parse_metadata or {}).get("archetype_confidence") or 0.0)
    archetype_candidates = list((layer1.parse_metadata or {}).get("archetype_candidates") or [])
    goal: dict[str, Any] = {"predicate": "unknown", "args": []}

    rescued_action_blob = lower_fold((act or "").replace("_", " "))
    action_hint_blob = lower_fold((action_canonical_hint or "").replace("_", " "))
    cue_blob = (
        f"{lower_fold(layer1.subject_text)} {lower_fold(layer1.action_text)} {rescued_action_blob} {action_hint_blob} "
        f"{lower_fold(layer1.condition_text)} {lower_fold(layer1.time_text)} {lower_fold(layer1.deadline_text)}"
    )
    has_bao_lau = "bao lau" in cue_blob
    has_bao_nhieu = "bao nhieu" in cue_blob
    has_toi_da_bao_lau = any(x in cue_blob for x in ("toi da bao lau", "bao lau toi da")) or (("toi da" in cue_blob) and has_bao_lau)
    has_khi_nao = "khi nao" in cue_blob
    threshold_core_cue = any(
        x in cue_blob
        for x in (
            "tu bao nhieu",
            "tu muc nao",
            "muc nao",
            "bao nhieu phan tram",
            "it nhat bao nhieu",
            "toi thieu bao nhieu",
            "toi da bao nhieu",
            "phan tram",
            "%",
        )
    )
    threshold_metric_hint = any(
        x in cue_blob
        for x in (
            "von dieu le",
            "muc von",
            "so lao dong",
            "doanh thu",
            "ty le so huu",
            "muc luong toi thieu",
            "luong thu viec",
            "thu viec",
        )
    )
    has_deadline_anchor = any(
        x in cue_blob
        for x in (
            "thoi han",
            "ke tu",
            "trong vong",
            "truoc bao lau",
            "sau bao lau",
        )
    )

    intent_units = [u for u in (l1_meta.get("intent_units") or []) if isinstance(u, dict)]
    has_multi_intent = bool(l1_meta.get("has_multi_intent", False) and len(intent_units) > 1)
    if has_multi_intent:
        primary_focus = str((intent_units[0] or {}).get("focus") or focus)
        if primary_focus and primary_focus != "unknown":
            focus = primary_focus
            pred = _modality_to_goal_predicate(focus, layer1.modality_text)

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
            obj = "phieu_lay_y_kien"
        goal = {"predicate": "permission", "args": [subj, act, obj]}
    elif (
        focus == "obligation"
        and _detect_register_change(low)
        and not _is_locked_action_from_layer1(layer1.action_text, action_canonical_hint)
        and _has_strong_register_change_action_evidence(
            action_text=layer1.action_text,
            action_canonical_hint=action_canonical_hint,
            rescued_action=act,
            low_blob=low,
        )
    ):
        goal = {
            "predicate": "obligation",
            "args": [subj, "dang_ky_thay_doi", "thay_doi_dang_ky"],
        }
    elif pred == "prohibition":
        goal = {"predicate": "prohibition", "args": [subj, act, obj]}
    else:
        goal = _goal_from_focus(
            focus=focus,
            pred=pred,
            subj=subj,
            act=act,
            obj=obj,
            cue_blob=cue_blob,
            has_toi_da_bao_lau=has_toi_da_bao_lau,
            threshold_core_cue=threshold_core_cue,
            threshold_metric_hint=threshold_metric_hint,
            has_bao_nhieu=has_bao_nhieu,
            has_khi_nao=has_khi_nao,
            has_bao_lau=has_bao_lau,
            has_deadline_anchor=has_deadline_anchor,
        )

    sub_goals: list[dict[str, Any]] = []
    if has_multi_intent:
        for idx, unit in enumerate(intent_units):
            unit_text = str(unit.get("text") or "")
            unit_focus_raw = str(unit.get("focus") or "unknown")
            unit_focus = _choose_effective_focus(
                focus=unit_focus_raw,
                modality_text=layer1.modality_text,
                question_focus_hint=question_focus_hint,
                condition_family_hint=condition_family_hint,
            )
            unit_blob = lower_fold(unit_text)
            u_act, u_obj, u_conf = _canonical_action_and_object(unit_text, low, action_canonical_hint)
            u_pred = _modality_to_goal_predicate(unit_focus, layer1.modality_text)
            u_goal = _goal_from_focus(
                focus=unit_focus,
                pred=u_pred,
                subj=subj,
                act=u_act,
                obj=u_obj,
                cue_blob=unit_blob,
                has_toi_da_bao_lau=("toi da" in unit_blob and "bao lau" in unit_blob),
                threshold_core_cue=any(x in unit_blob for x in ("tu bao nhieu", "toi thieu", "it nhat", "phan tram")),
                threshold_metric_hint=any(x in unit_blob for x in ("thu viec", "luong", "doanh thu", "so lao dong", "von")),
                has_bao_nhieu=("bao nhieu" in unit_blob),
                has_khi_nao=("khi nao" in unit_blob),
                has_bao_lau=("bao lau" in unit_blob),
                has_deadline_anchor=any(x in unit_blob for x in ("thoi han", "trong vong", "ke tu")),
            )
            sub_goals.append(
                {
                    "index": idx,
                    "focus": unit_focus,
                    "predicate": str(u_goal.get("predicate") or "unknown"),
                    "goal": u_goal,
                    "text": unit_text[:180],
                    "action_confidence": u_conf,
                    "is_primary": idx == 0,
                }
            )
        if sub_goals:
            goal = dict(sub_goals[0].get("goal") or goal)

    if focus == "unknown" and archetype_candidates:
        ambiguities.append(
            make_ambiguity(
                kind="ambiguous_archetype",
                field="question_focus",
                source_text=(layer1.action_text or "")[:160],
                candidates=archetype_candidates,
                confidence_gap=max(0.05, round(1.0 - archetype_conf, 3)),
                blocking=archetype_conf < 0.55,
                priority=3,
                blocking_reason="archetype_canonical_mapping_uncertain",
            )
        )
    if action_conf < 0.6:
        ambiguities.append(
            make_ambiguity(
                kind="ambiguous_action",
                field="action_text",
                source_text=(layer1.action_text or "")[:160],
                candidates=[act, "hanh_vi"],
                confidence_gap=0.12,
                blocking=False,
                priority=7,
                blocking_reason="action_canonical_mapping_low_confidence",
            )
        )

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
        "goal_canonicalization": {
            "action_canonical": act,
            "object_canonical": obj,
            "action_confidence": action_conf,
            "effective_focus": focus,
            "focus_hint": question_focus_hint,
            "action_canonical_hint": action_canonical_hint,
            "subject_type_hint": subject_type_hint,
            "domain_hint": domain_hint,
            "condition_family_hint": condition_family_hint,
            "archetype_confidence": archetype_conf,
            "archetype_candidates": archetype_candidates,
        },
        "intent_structure": {
            "has_multi_intent": has_multi_intent,
            "intent_units": intent_units,
            "sub_goals": sub_goals,
            "primary_intent": (intent_units[0] if intent_units else {"focus": focus}),
            "secondary_intents": (intent_units[1:] if len(intent_units) > 1 else []),
            "selection_policy": "primary_for_reasoning_secondary_preserved",
        },
    }
    if ast == "ambiguous":
        diag["assertion_ambiguous"] = True
        diag["assertion_ambiguity_suppressed"] = assertion_ambiguous_suppressed

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
