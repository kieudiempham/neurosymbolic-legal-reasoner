"""Heuristic Layer-1 parser (fallback / benchmark) — no LLM."""

from __future__ import annotations

import re
from typing import Any

from schemas.question_parse import AssertionStatus, Layer1Parse, QuestionFocus, UtteranceType
from utils.text import lower_fold, normalize_ws

# Permission-style "được" without overlapping "có được quyền / bằng / bổ nhiệm" regression cases.
_RE_CO_DUOC_GUI = re.compile(r"\bcó được\s+gửi\b", re.IGNORECASE)

_DISCOURSE_SPLIT = re.compile(
    r"^(khi|nếu|neu|trong thời gian|trong thoi gian|sau khi|trường hợp|trong trường hợp|truong hop)\s+(.+?)(?:\s+thì\s+|\s*,\s*)(.+)$",
    re.IGNORECASE,
)

_THI_SPLIT = re.compile(r"^(.+?)\s+thì\s+(.+)$", re.IGNORECASE)

_TEMPORAL_PREFIX = re.compile(
    r"^(trong thời gian|trong thoi gian|khi|sau khi)\b",
    re.IGNORECASE,
)

_ACTOR_PATTERNS: tuple[str, ...] = (
    "người lao động",
    "nguoi lao dong",
    "người sử dụng lao động",
    "nguoi su dung lao dong",
    "doanh nghiệp",
    "doanh nghiep",
    "công ty",
    "cong ty",
    "bên sử dụng lao động",
    "ben su dung lao dong",
)


def _score_focus(low: str, modality_text: str) -> tuple[QuestionFocus, list[str], float]:
    scores: dict[str, int] = {
        "obligation": 0,
        "permission": 0,
        "prohibition": 0,
        "deadline": 0,
        "threshold": 0,
        "exception": 0,
        "applicability": 0,
        "procedure": 0,
        "legal_effect": 0,
        "legal_consequence": 0,
        "compensation_rule": 0,
        "entitlement_rule": 0,
        "refund_eligibility": 0,
        "payment_obligation_explanation": 0,
    }

    prohibition_cue = any(x in low for x in ("khong duoc", "bi cam", "cam "))
    permission_cue = any(x in low for x in ("co duoc", "duoc phep", "co quyen", "co the"))
    obligation_cue = any(x in low for x in ("co phai", "phai ", "bat buoc", "nghia vu"))
    grounds_cue = any(
        x in low
        for x in (
            "truong hop nao",
            "trong nhung truong hop nao",
            "trong truong hop nao",
            "truong hop gi",
            "ap dung cho truong hop nao",
            "can cu nao",
        )
    )
    eligibility_cue = any(
        x in low
        for x in (
            "dieu kien nao",
            "dieu kien gi",
            "can dieu kien gi",
            "duoc tinh vao",
        )
    )
    legal_effect_cue = any(
        x in low
        for x in (
            "nhu the nao",
            "ra sao",
            "theo cach nao",
            "co che xu ly",
            "muc huong",
            "bi xu ly nhu the nao",
            "hau qua gi",
            "he qua gi",
            "duoc tra luong nhu the nao",
            "muc huong nhu the nao",
            "muc tra nhu the nao",
            "cach tinh",
        )
    )
    sanction_cue = any(
        x in low
        for x in (
            "bi xu ly",
            "xu phat",
            "che tai",
            "hau qua phap ly",
            "hau qua gi",
            "he qua gi",
        )
    )
    compensation_cue = any(
        x in low
        for x in (
            "duoc tra luong nhu the nao",
            "muc huong",
            "muc tra",
            "cach tinh luong",
            "lam them gio",
            "boi thuong",
            "thanh toan nhu the nao",
        )
    )
    entitlement_cue = any(
        x in low
        for x in (
            "duoc tinh vao",
            "duoc huong",
            "quyen loi nao",
            "duoc hoan",
            "hoan thue",
            "duoc tru",
        )
    )
    refund_cue = any(
        x in low
        for x in (
            "hoan thue",
            "duoc hoan thue",
            "hoan thue gia tri gia tang",
        )
    )
    payment_explain_cue = any(
        x in low
        for x in (
            "duoc tra luong",
            "muc huong",
            "muc tra",
            "cach tinh",
            "thanh toan nhu the nao",
        )
    )
    has_bao_lau = "bao lau" in low
    has_bao_nhieu = "bao nhieu" in low
    threshold_core_cue = any(
        x in low
        for x in (
            "tu bao nhieu",
            "tu muc nao",
            "muc nao",
            "bao nhieu phan tram",
            "it nhat bao nhieu",
            "toi thieu bao nhieu",
            "toi da bao nhieu",
            "tuong ung bao nhieu phan tram",
        )
    )
    threshold_metric_hint = any(
        x in low
        for x in (
            "von dieu le",
            "muc von",
            "so lao dong",
            "doanh thu",
            "ty le so huu",
            "phan tram",
            "muc luong toi thieu",
            "luong thu viec",
        )
    )
    duration_limit_cue = any(
        x in low
        for x in (
            "toi da bao lau",
            "toi thieu bao lau",
            "it nhat bao lau",
            "bao lau toi da",
            "bao lau toi thieu",
        )
    ) or (("toi da" in low or "toi thieu" in low or "it nhat" in low) and has_bao_lau)
    when_cue = "khi nao" in low
    deadline_anchor_cue = any(x in low for x in ("ke tu", "trong vong", "thoi han", "truoc bao lau", "sau bao lau")) or bool(
        re.search(r"\bhan\b", low)
    )
    deadline_cue = when_cue or deadline_anchor_cue or (has_bao_lau and not duration_limit_cue)
    threshold_cue = any(x in low for x in ("toi thieu", "it nhat", "bao nhieu", "phan tram", "%"))
    exception_cue = any(x in low for x in ("tru truong hop", "ngoai le", "ngoai tru", "tru khi"))
    procedure_cue = any(x in low for x in ("thu tuc", "ho so", "nop ho so"))

    if prohibition_cue or modality_text == "không được":
        scores["prohibition"] += 6
    if permission_cue or modality_text in ("được", "có quyền"):
        scores["permission"] += 5
    if obligation_cue or modality_text in ("phải", "có phải ... không"):
        scores["obligation"] += 5
    if grounds_cue or eligibility_cue:
        scores["applicability"] += 6
    if legal_effect_cue:
        scores["legal_effect"] += 5
    if sanction_cue:
        scores["legal_consequence"] += 7
    if compensation_cue:
        scores["compensation_rule"] += 7
    if entitlement_cue:
        scores["entitlement_rule"] += 6
    if refund_cue:
        scores["refund_eligibility"] += 8
    if payment_explain_cue:
        scores["payment_obligation_explanation"] += 6
    if duration_limit_cue:
        scores["threshold"] += 6
        scores["deadline"] = max(0, scores["deadline"] - 3)
    elif deadline_cue:
        scores["deadline"] += 4
    if threshold_cue:
        scores["threshold"] += 3
    if threshold_core_cue:
        scores["threshold"] += 5
    if threshold_metric_hint and (threshold_core_cue or has_bao_nhieu):
        scores["threshold"] += 3
    if exception_cue:
        scores["exception"] += 5
    if procedure_cue:
        scores["procedure"] += 3
    if any(x in low for x in ("xu phat", "che tai", "trach nhiem phap ly", "hau qua")):
        scores["legal_consequence"] += 5

    # High-priority overrides to avoid common legal intent drifts.
    if grounds_cue:
        scores["applicability"] += 4
        scores["deadline"] = max(0, scores["deadline"] - 4)
        scores["obligation"] = max(0, scores["obligation"] - 2)
    if legal_effect_cue:
        scores["legal_effect"] += 4
        scores["obligation"] = max(0, scores["obligation"] - 4)
        scores["permission"] = max(0, scores["permission"] - 2)
    if "duoc tinh vao" in low and any(x in low for x in ("dieu kien gi", "dieu kien nao", "truong hop nao")):
        scores["applicability"] += 4
    if "hoan thue" in low and any(x in low for x in ("truong hop nao", "dieu kien nao")):
        scores["refund_eligibility"] += 2
    if refund_cue and grounds_cue:
        scores["refund_eligibility"] += 4
        scores["applicability"] += 1
    if sanction_cue or compensation_cue or entitlement_cue or refund_cue or payment_explain_cue:
        scores["obligation"] = max(0, scores["obligation"] - 5)
        scores["permission"] = max(0, scores["permission"] - 3)
    if permission_cue:
        scores["permission"] += 1
        scores["obligation"] = max(0, scores["obligation"] - 1)
    if threshold_core_cue or threshold_metric_hint:
        # Do not let modal words "phải/được/có quyền" dominate threshold questions.
        scores["obligation"] = max(0, scores["obligation"] - 4)
        scores["permission"] = max(0, scores["permission"] - 3)
        scores["deadline"] = max(0, scores["deadline"] - 3)

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_name, top_score = ranked[0]
    second_name, second_score = ranked[1]

    if top_score <= 0:
        return "unknown", [], 0.0

    confidence = min(0.95, 0.5 + (top_score - second_score) * 0.1 + top_score * 0.03)
    candidates = [top_name]
    if second_score > 0 and (top_score - second_score) <= 1:
        candidates.append(second_name)
        return "unknown", candidates, max(0.45, confidence - 0.2)
    # Low-confidence archetype should remain explicit ambiguous rather than silently defaulting.
    if confidence < 0.6 and second_score > 0:
        candidates.append(second_name)
        return "unknown", candidates, confidence
    return top_name, candidates, confidence


def _snippet_focus(low: str) -> QuestionFocus:
    if any(x in low for x in ("neu co thi can dieu kien gi", "neu co can dieu kien gi", "can dieu kien gi")):
        return "applicability"
    if any(x in low for x in ("toi thieu", "it nhat", "tu bao nhieu", "bao nhieu phan tram", "bao nhiêu", "%")):
        return "threshold"
    if any(x in low for x in ("truong hop nao", "trong truong hop nao", "dieu kien nao")):
        return "applicability"
    if any(x in low for x in ("bi xu ly nhu the nao", "xu phat", "che tai", "hau qua gi", "he qua gi")):
        return "legal_consequence"
    if any(x in low for x in ("hoan thue", "duoc hoan thue")):
        return "refund_eligibility"
    if any(x in low for x in ("duoc tra luong nhu the nao", "muc huong", "muc tra", "cach tinh", "boi thuong")):
        return "compensation_rule"
    if any(x in low for x in ("duoc tinh vao", "duoc huong", "duoc tru")):
        return "entitlement_rule"
    if any(x in low for x in ("nhu the nao", "ra sao", "theo cach nao")):
        return "legal_effect"
    if any(x in low for x in ("co duoc", "duoc phep", "co quyen")):
        return "permission"
    if any(x in low for x in ("co phai", "phai", "bat buoc")):
        return "obligation"
    return "unknown"


def _decompose_intents(question: str) -> tuple[list[dict[str, Any]], bool]:
    q = normalize_ws(question)
    low = lower_fold(q)
    units: list[dict[str, Any]] = []

    if any(x in low for x in ("neu co thi", "nếu có thì")):
        parts = re.split(r"(?:nếu có thì|neu co thi)", q, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) == 2:
            left = normalize_ws(parts[0].strip(" ,"))
            right = normalize_ws(parts[1].strip(" ,"))
            if left:
                units.append({"text": left, "focus": _snippet_focus(lower_fold(left)), "cue": "conditional_if_yes"})
            if right:
                units.append({"text": right, "focus": _snippet_focus(lower_fold(right)), "cue": "conditional_if_yes"})

    if not units and re.search(r"như thế nào\s+và\s+trong\s+trường\s+hợp\s+nào", low, flags=re.IGNORECASE):
        left = re.split(r"\s+và\s+", q, maxsplit=1, flags=re.IGNORECASE)[0]
        right = q[len(left):].lstrip(" ,")
        units = [
            {"text": normalize_ws(left), "focus": "legal_effect", "cue": "how_and_when"},
            {"text": normalize_ws(right), "focus": "applicability", "cue": "how_and_when"},
        ]

    if not units and re.search(r"\bcó\s+được\b.+\bkhông\b\s*,?\s*(và|va)\s+", low, flags=re.IGNORECASE):
        split = re.split(r"\s*,?\s*(?:và|va)\s+", q, maxsplit=1, flags=re.IGNORECASE)
        if len(split) == 2:
            left = normalize_ws(split[0])
            right = normalize_ws(split[1])
            units = [
                {"text": left, "focus": "permission", "cue": "permission_and_threshold"},
                {"text": right, "focus": _snippet_focus(lower_fold(right)), "cue": "permission_and_threshold"},
            ]

    if not units and re.search(r"\s*,?\s*(và|va)\s+", low, flags=re.IGNORECASE):
        split = re.split(r"\s*,?\s*(?:và|va)\s+", q, maxsplit=1, flags=re.IGNORECASE)
        if len(split) == 2:
            left = normalize_ws(split[0])
            right = normalize_ws(split[1])
            lf = _snippet_focus(lower_fold(left))
            rf = _snippet_focus(lower_fold(right))
            if lf != "unknown" and rf != "unknown" and lf != rf:
                units = [
                    {"text": left, "focus": lf, "cue": "coordinated_intents"},
                    {"text": right, "focus": rf, "cue": "coordinated_intents"},
                ]

    has_multi = len(units) > 1
    if has_multi:
        cleaned: list[dict[str, Any]] = []
        for idx, u in enumerate(units):
            cleaned.append(
                {
                    "index": idx,
                    "text": normalize_ws(str(u.get("text") or ""))[:180],
                    "focus": str(u.get("focus") or "unknown"),
                    "cue": str(u.get("cue") or ""),
                }
            )
        return cleaned, True
    return [], False


def _split_condition_and_main(q: str) -> tuple[str, str]:
    text = normalize_ws(q)
    m = _DISCOURSE_SPLIT.search(text)
    if m:
        cond = normalize_ws(m.group(2))
        main = normalize_ws(m.group(3))
        return cond, main

    m2 = _THI_SPLIT.search(text)
    if m2:
        cond = normalize_ws(m2.group(1))
        main = normalize_ws(m2.group(2))
        if len(cond.split()) >= 2:
            return cond, main

    m3 = re.search(r"^(.+?),\s*(.+)$", text)
    if m3:
        left = normalize_ws(m3.group(1))
        right = normalize_ws(m3.group(2))
        if _TEMPORAL_PREFIX.search(left) or any(k in lower_fold(left) for k in ("nếu", "neu", "trường hợp", "truong hop")):
            return left, right

    return "", text


def _extract_actor_and_predicate(main_clause: str) -> tuple[str, str]:
    text = normalize_ws(main_clause)
    low = lower_fold(text)
    for actor in _ACTOR_PATTERNS:
        if low.startswith(actor):
            subject = text[: len(actor)].strip(" ,")
            predicate = text[len(actor) :].strip(" ,")
            return subject, predicate

    for actor in _ACTOR_PATTERNS:
        idx = low.find(actor)
        if idx >= 0:
            subject = text[idx : idx + len(actor)].strip(" ,")
            predicate = (text[:idx] + " " + text[idx + len(actor) :]).strip(" ,")
            return subject, normalize_ws(predicate)

    # Fallback: keep a short nominal prefix instead of swallowing the whole clause.
    short = " ".join(text.split()[:5]).strip(" ,")
    return short, text


def _extract_actor_only(text: str) -> str:
    q = normalize_ws(text)
    low = lower_fold(q)
    for actor in _ACTOR_PATTERNS:
        idx = low.find(actor)
        if idx >= 0:
            return q[idx : idx + len(actor)].strip(" ,")
    return ""


def _clean_action(predicate: str) -> str:
    text = normalize_ws(predicate)
    # Keep main clause before a coordinated question tail.
    text = re.split(r",\s*(?:và|hay|hoặc)\s+", text, maxsplit=1, flags=re.IGNORECASE)[0]
    text = re.sub(
        r"^(?:có\s+được|co\s+duoc|có\s+quyền|co\s+quyen|được\s+phép|duoc\s+phep|có\s+phải|co\s+phai|phải|phai|cần|can|được|duoc)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\b(bao nhiêu|bao nhieu|bao lâu|bao lau|như thế nào|nhu the nao|điều kiện gì|dieu kien gi|trường hợp nào|truong hop nao|không|khong)\b.*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\?+$", "", text).strip(" ,")
    return normalize_ws(text)


def parse_question_layer1_heuristic(question: str) -> Layer1Parse:
    q = normalize_ws(question)
    low = lower_fold(q)

    condition_text, main_clause = _split_condition_and_main(q)
    subject_text, predicate = _extract_actor_and_predicate(main_clause)
    actor_from_condition = _extract_actor_only(condition_text) if condition_text else ""
    if subject_text and lower_fold(subject_text).startswith(("phai", "có", "co", "duoc", "được", "can", "cần", "bao")) and actor_from_condition:
        subject_text = actor_from_condition
    elif (not subject_text or len(subject_text.split()) <= 2) and actor_from_condition:
        subject_text = actor_from_condition

    action_candidate = _clean_action(predicate)

    # Utterance type (v5-oriented)
    utterance_type: UtteranceType = "direct_question"
    if re.search(r"\bnếu\b|\bneu\b", low) or "trong truong hop" in low or "trong trường hợp" in q.lower():
        utterance_type = "conditional_legal_question"
    if "gia su" in low or "giả sử" in q.lower() or re.search(r"\bneu\s+.*\s+thi\b", low):
        utterance_type = "hypothetical_question"
    if utterance_type == "direct_question" and (
        low.count("hay") > 1 or ("co the" in low and "hay la" in low)
    ):
        utterance_type = "ambiguous_question"

    modality_text = ""
    if any(x in low for x in ("khong duoc", "cấm", "cam", "bi cam")):
        modality_text = "không được"
    elif "co quyen" in low or "có quyền" in q.lower():
        modality_text = "có quyền"
    elif "co duoc" in low or "có được" in q.lower():
        modality_text = "được"
    elif _RE_CO_DUOC_GUI.search(q) or "co duoc gui" in low:
        modality_text = "được"
    elif "duoc phep" in low or "được phép" in q.lower() or ("co the" in low and "duoc" in low):
        modality_text = "được"
    elif any(x in low for x in ("co phai", "phai khong", "bat buoc", "nghia vu")):
        modality_text = "phải"
    elif "co phai" in low or "phải không" in q.lower():
        modality_text = "có phải ... không"

    question_focus, focus_candidates, focus_confidence = _score_focus(low, modality_text)
    intent_units, has_multi_intent = _decompose_intents(q)
    if has_multi_intent and intent_units:
        first_focus = str(intent_units[0].get("focus") or "unknown")
        if first_focus != "unknown":
            question_focus = first_focus
        if question_focus not in focus_candidates:
            focus_candidates = [question_focus, *[c for c in focus_candidates if c != question_focus]]

    action_text = action_candidate or normalize_ws(predicate) or normalize_ws(main_clause)

    # Guardrail: do not let subject/action silently become near-full-question blobs.
    if len(subject_text) > int(len(q) * 0.85):
        subject_text = " ".join(subject_text.split()[:5]).strip(" ,")
    if len(action_text) > int(len(q) * 0.9):
        action_text = _clean_action(main_clause) or action_text

    time_text = ""
    deadline_text = ""
    if condition_text and _TEMPORAL_PREFIX.search(condition_text):
        time_text = condition_text
        deadline_text = condition_text

    tm = re.search(
        r"(trong vòng|trong vo|trong thời hạn|trong thoi han|thời hạn|thoi han|trong\s+\d+[\s,]*ngày|"
        r"\d+\s*ngày|khi nào|bao lâu|hết hạn|het han|deadline)",
        q,
        flags=re.IGNORECASE,
    )
    if tm:
        span = tm.group(0)
        time_text = span
        deadline_text = span
    dm = re.search(r"(\d+[\s,.]*(?:ngày|tháng|năm|nam)\b[^?.]*)", q, flags=re.IGNORECASE)
    if dm and not deadline_text:
        deadline_text = normalize_ws(dm.group(1))

    exception_text = ""
    if any(x in low for x in ("tru truong hop", "ngoai le", "ngoại trừ", "tru khi", "trừ khi")):
        parts = re.split(r"(?:trừ trường hợp|ngoại lệ|ngoại trừ|trừ khi|ngoại trừ)", q, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) >= 2:
            exception_text = normalize_ws(parts[-1])

    assertion_status: AssertionStatus = "ambiguous"
    if any(x in low for x in ("toi da", "chung toi da", "đã đăng ký", "da dang ky", "thực tế", "thuc te")):
        assertion_status = "asserted"
    elif utterance_type in ("hypothetical_question", "conditional_legal_question"):
        assertion_status = "hypothetical"
    elif "gia su" in low or "giả sử" in q.lower():
        assertion_status = "hypothetical"

    notes = ["heuristic_layer1_v3"]
    if focus_candidates:
        notes.append("focus_candidates:" + ",".join(focus_candidates))
    if has_multi_intent:
        notes.append("multi_intent_detected")

    meta = {
        "parser_backend": "heuristic",
        "parser_model": "",
        "parse_mode": "heuristic_native",
        "fallback_used": False,
        "parser_fallback_mode": None,
        "archetype_confidence": focus_confidence,
        "archetype_candidates": focus_candidates,
        "has_multi_intent": has_multi_intent,
        "intent_units": intent_units,
        "primary_intent": intent_units[0] if intent_units else {"focus": question_focus, "text": q[:180]},
        "secondary_intents": intent_units[1:] if len(intent_units) > 1 else [],
    }

    return Layer1Parse(
        utterance_type=utterance_type,
        subject_text=subject_text or "đối tượng liên quan",
        condition_text=condition_text,
        action_text=action_text,
        modality_text=modality_text,
        time_text=time_text,
        deadline_text=deadline_text,
        exception_text=exception_text,
        question_focus=question_focus,
        assertion_status=assertion_status,
        raw_notes=notes,
        parse_metadata=meta,
    )
