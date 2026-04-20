import json
import traceback
import urllib.error
import urllib.request

URL = "http://127.0.0.1:8001/ask"
QUESTIONS = [
    ("Q1_legal_consequence", "Nếu nộp tiền thuế trễ hạn thì doanh nghiệp có thể bị áp dụng những hậu quả pháp lý gì?"),
    ("Q2_conditional_obligation", "Nếu chưa đăng ký thay đổi thì có phải bổ sung hồ sơ không?"),
    ("Q3_multi_intent", "Bán hàng tạp hóa có cần đăng ký kinh doanh không? Có phải đóng thuế không?"),
    ("Q4_permission_condition", "Chủ tịch HĐQT bị tạm giam thì có điều hành công ty được không?"),
    ("Q5_dossier", "Hồ sơ thành lập chi nhánh công ty gồm những gì?"),
    ("Q6_status_identity", "Người đại diện theo pháp luật của doanh nghiệp tư nhân là ai?"),
]


def call_backend(question: str, timeout_sec: int = 90) -> dict:
    payload = json.dumps({"question": question, "domain": None}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        return json.loads(resp.read().decode("utf-8"))


for tag, q in QUESTIONS:
    print(f"--- {tag} ---")
    try:
        data = call_backend(q)
        l1 = data.get("layer1") or {}
        meta = l1.get("parse_metadata") or {}

        core = {k: str(l1.get(k) or "").strip() for k in ["question_focus", "action_text", "subject_text", "condition_text"]}
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
        conf = {
            k: meta.get(k)
            for k in [
                "question_focus_confidence",
                "action_confidence",
                "subject_confidence",
                "used_fallback_label",
                "parse_rationale",
            ]
        }

        checks = {
            "core_slots_no_empty_without_reason": all(core.values()),
            "family_fields_populated_meaningfully": all(
                meta.get(k) not in (None, "", [])
                for k in [
                    "macro_family",
                    "question_family",
                    "family_confidence",
                    "family_reason",
                    "primary_intent_family",
                    "parse_policy_applied",
                ]
            ),
            "confidence_fields_exist": all(
                meta.get(k) is not None
                for k in ["question_focus_confidence", "action_confidence", "subject_confidence"]
            ),
            "rationale_present_when_needed": str(meta.get("parse_rationale") or "").strip() != "",
            "legal_consequence_action_non_empty": True,
            "status_not_collapsed_to_unknown": True,
        }

        if tag == "Q1_legal_consequence":
            checks["legal_consequence_action_non_empty"] = core["action_text"] != ""

        if tag == "Q6_status_identity":
            checks["status_not_collapsed_to_unknown"] = (
                core["question_focus"].lower() != "unknown"
                and str(meta.get("question_family") or "").strip() not in ("", "other")
            )

        print("core:", core)
        print("family:", family)
        print("confidence:", conf)
        print("checks:", checks)

    except urllib.error.URLError as exc:
        print("ERROR: backend call failed:", exc)
    except Exception as exc:
        print("ERROR:", exc)
        traceback.print_exc()
