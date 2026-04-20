import json
import urllib.request

URL = "http://127.0.0.1:8001/ask"
QUESTIONS = [
    (
        "Q1_legal_consequence",
        "Nếu nộp tiền thuế trễ hạn thì doanh nghiệp có thể bị áp dụng những hậu quả pháp lý gì?",
    ),
    (
        "Q2_conditional_obligation",
        "Nếu chưa đăng ký thay đổi thì có phải bổ sung hồ sơ không?",
    ),
    (
        "Q3_multi_intent",
        "Bán hàng tạp hóa có cần đăng ký kinh doanh không? Có phải đóng thuế không?",
    ),
    (
        "Q4_permission_condition",
        "Chủ tịch HĐQT bị tạm giam thì có điều hành công ty được không?",
    ),
    (
        "Q5_dossier",
        "Hồ sơ thành lập chi nhánh công ty gồm những gì?",
    ),
    (
        "Q6_status_identity",
        "Người đại diện theo pháp luật của doanh nghiệp tư nhân là ai?",
    ),
]


def ask(question: str) -> dict:
    payload = json.dumps({"question": question, "domain": None}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


for tag, q in QUESTIONS:
    data = ask(q)
    l1 = data.get("layer1") or {}
    meta = l1.get("parse_metadata") or {}

    core = {k: str(l1.get(k) or "").strip() for k in ["question_focus", "action_text", "subject_text", "condition_text"]}
    core_non_empty = {k: (v != "") for k, v in core.items()}

    family = {
        k: meta.get(k)
        for k in [
            "macro_family",
            "question_family",
            "family_confidence",
            "family_reason",
            "primary_intent_family",
            "secondary_intent_families",
            "parse_policy_applied",
        ]
    }
    family_populated = all(
        meta.get(k) not in (None, "", [])
        for k in [
            "macro_family",
            "question_family",
            "family_confidence",
            "family_reason",
            "primary_intent_family",
            "parse_policy_applied",
        ]
    )

    confidence = {
        k: meta.get(k)
        for k in [
            "question_focus_confidence",
            "action_confidence",
            "subject_confidence",
            "parse_rationale",
            "used_fallback_label",
        ]
    }
    confidence_present = (
        all(meta.get(k) is not None for k in ["question_focus_confidence", "action_confidence", "subject_confidence"])
        and str(meta.get("parse_rationale") or "").strip() != ""
    )

    legal_consequence_action_ok = True
    if tag == "Q1_legal_consequence":
        legal_consequence_action_ok = str(l1.get("action_text") or "").strip() != ""

    status_not_unknown_ok = True
    if tag == "Q6_status_identity":
        status_not_unknown_ok = (
            str(l1.get("question_focus") or "").strip().lower() != "unknown"
            and str(meta.get("question_family") or "").strip() != ""
        )

    print(f"--- {tag} ---")
    print("core_slots:", core)
    print("family_fields:", family)
    print("confidence_fields:", confidence)
    print(
        "checks:",
        {
            "core_slots_no_empty_without_reason": all(core_non_empty.values()),
            "family_fields_populated": family_populated,
            "confidence_rationale_present": confidence_present,
            "legal_consequence_action_non_empty": legal_consequence_action_ok,
            "status_not_collapsed_unknown": status_not_unknown_ok,
        },
    )
