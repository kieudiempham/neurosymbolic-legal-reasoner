#!/usr/bin/env python3
"""Run 3 targeted E2E checks and export Table-readiness JSON."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

BASE_URL = "http://127.0.0.1:8002"
ASK_URL = f"{BASE_URL}/ask"
OUT_PATH = Path("tests/runtime_checks/3case_table_readiness.json")

TEST_CASES = [
    {
        "test_id": "Q1",
        "question": "Thời hạn thông báo thay đổi nội dung đăng ký doanh nghiệp là bao nhiêu ngày?",
        "expected_type": "rule_reading",
    },
    {
        "test_id": "Q2",
        "question": "Công ty tôi thay đổi nội dung đăng ký nhưng chưa rõ thời điểm gửi thông báo, vậy có bị quá hạn không?",
        "expected_type": "fact_application",
    },
    {
        "test_id": "Q3",
        "question": "Trong trường hợp công ty thay đổi nội dung đăng ký doanh nghiệp thì thời hạn thông báo là bao lâu, và nếu nộp sau thời hạn đó thì có bị xử lý gì không?",
        "expected_type": "hybrid",
    },
]


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _pick_answer_text(resp: dict[str, Any]) -> str:
    answer = resp.get("answer")
    if isinstance(answer, str):
        return answer.strip()
    if isinstance(answer, dict):
        txt = str(answer.get("answer_text") or answer.get("text") or "").strip()
        if txt:
            return txt
    alt = [
        resp.get("answer_text"),
        _as_dict(resp.get("final_response")).get("answer_text"),
    ]
    for item in alt:
        txt = str(item or "").strip()
        if txt:
            return txt
    return ""


def _pick_selected_rule_id(resp: dict[str, Any]) -> str:
    sel = _as_dict(resp.get("selected_rule"))
    rid = str(sel.get("rule_id") or resp.get("selected_rule_id") or "").strip()
    return rid


def _pick_legal_citations(resp: dict[str, Any]) -> list[Any]:
    cites = _as_list(resp.get("legal_citations"))
    if cites:
        return cites
    ans = _as_dict(resp.get("answer"))
    if isinstance(ans.get("citations"), list):
        return ans["citations"]
    return []


def _pick_missing_facts(resp: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for src in (
        _as_list(resp.get("missing_facts")),
        _as_list(_as_dict(resp.get("debug_trace")).get("missing_facts")),
    ):
        for raw in src:
            key = str(raw or "").strip()
            if key and key not in out:
                out.append(key)
    return out


def _pick_hard_gates_hit(resp: dict[str, Any]) -> list[str]:
    dbg = _as_dict(resp.get("debug_trace"))
    return [str(x) for x in _as_list(dbg.get("hard_gates_hit")) if str(x).strip()]


def _pick_forward_failure_reason(resp: dict[str, Any]) -> str:
    direct = str(resp.get("forward_failure_reason") or "").strip()
    if direct:
        return direct
    dbg = _as_dict(resp.get("debug_trace"))
    fg = _as_dict(dbg.get("forward_gate"))
    fr = str(fg.get("failure_reason") or "").strip()
    if fr:
        return fr
    for row in _as_list(dbg.get("forward_gate")):
        if not isinstance(row, dict):
            continue
        fr2 = str(row.get("failure_reason") or "").strip()
        if fr2:
            return fr2
    return ""


def _pick_verification_summary(resp: dict[str, Any]) -> str:
    v = str(resp.get("verification_summary") or "").strip()
    if v:
        return v
    ans = _as_dict(resp.get("answer"))
    return str(ans.get("verification_summary") or "").strip()


def _pick_question_mode(resp: dict[str, Any]) -> str:
    qmode = str(resp.get("question_mode") or "").strip()
    if qmode:
        return qmode
    dbg = _as_dict(resp.get("debug_trace"))
    return str(dbg.get("question_mode") or "unknown").strip() or "unknown"


def _pick_application_status(resp: dict[str, Any]) -> str:
    status = str(resp.get("application_status") or "").strip()
    if status:
        return status
    dbg = _as_dict(resp.get("debug_trace"))
    return str(dbg.get("application_status") or "unknown").strip() or "unknown"


def _pick_final_decision(resp: dict[str, Any]) -> str:
    dec = str(resp.get("final_decision") or "").strip()
    if dec:
        return dec
    dbg = _as_dict(resp.get("debug_trace"))
    arep = _as_list(dbg.get("answer_repair"))
    if arep and isinstance(arep[-1], dict):
        out = str(arep[-1].get("final_decision") or arep[-1].get("decision") or "").strip()
        if out:
            return out
    return ""


def _pick_error_stage(resp: dict[str, Any]) -> str:
    for key in ("error_stage_final", "error_stage"):
        val = str(resp.get(key) or "").strip()
        if val:
            return val
    return str(resp.get("error") or "").strip()


def _bool_proof_present(resp: dict[str, Any]) -> bool:
    if bool(resp.get("proof_trace")):
        return True
    if bool(resp.get("proof")):
        return True
    dbg = _as_dict(resp.get("debug_trace"))
    if bool(dbg.get("proof_steps_by_domain")):
        return True
    return False


def _answer_has_case_application(answer_text: str) -> bool:
    low = answer_text.lower()
    cues = ["nếu", "nếu ", "if", "trường hợp", "áp dụng", "qua hạn", "quá hạn", "xử lý"]
    return any(c in low for c in cues)


def _classify_answer_type(application_status: str) -> str:
    if application_status == "none":
        return "A"
    if application_status == "conditional":
        return "A+B"
    if application_status == "final":
        return "A+C"
    return "unknown"


def _eval_case(case: dict[str, Any], resp: dict[str, Any]) -> dict[str, Any]:
    answer_text = _pick_answer_text(resp)
    selected_rule_id = _pick_selected_rule_id(resp)
    legal_citations = _pick_legal_citations(resp)
    proof_present = _bool_proof_present(resp)
    missing_facts = _pick_missing_facts(resp)
    needs_clarification = bool(resp.get("needs_clarification", False))
    question_mode = _pick_question_mode(resp)
    application_status = _pick_application_status(resp)
    final_decision = _pick_final_decision(resp)
    verification_summary = _pick_verification_summary(resp)
    hard_gates_hit = _pick_hard_gates_hit(resp)
    error_stage_final = _pick_error_stage(resp)
    forward_failure_reason = _pick_forward_failure_reason(resp)

    answer_type = _classify_answer_type(application_status)
    answer_has_clear_legal_rule = bool(selected_rule_id) or bool(legal_citations)
    answer_has_case_application = _answer_has_case_application(answer_text)
    answer_grounded_to_rule = bool(selected_rule_id) and (proof_present or bool(legal_citations))
    answer_useful = bool(answer_text) and ("xin lỗi" not in answer_text.lower())

    verification_success = final_decision in {"ACCEPT", "REPAIR", ""}
    proof_or_partial_proof_present = proof_present
    missing_facts_correct_if_needed = True
    if case["expected_type"] == "fact_application" and application_status == "conditional":
        missing_facts_correct_if_needed = bool(missing_facts)

    unsupported_or_reject_error = bool(error_stage_final) or final_decision == "REJECT"

    fail_reasons: list[str] = []

    if case["expected_type"] == "rule_reading":
        if question_mode != "rule_reading":
            fail_reasons.append("question_mode_not_rule_reading")
        if application_status != "none":
            fail_reasons.append("application_status_not_A")
    elif case["expected_type"] == "fact_application":
        if question_mode != "fact_application":
            fail_reasons.append("question_mode_not_fact_application")
        if missing_facts and application_status != "conditional":
            fail_reasons.append("missing_facts_but_not_A_plus_B")
    elif case["expected_type"] == "hybrid":
        if question_mode != "hybrid":
            fail_reasons.append("question_mode_not_hybrid")
        if not answer_has_clear_legal_rule:
            fail_reasons.append("hybrid_missing_legal_rule_anchor")
        if not answer_has_case_application:
            fail_reasons.append("hybrid_missing_case_application")

    if not answer_useful:
        fail_reasons.append("answer_not_useful")
    if unsupported_or_reject_error:
        fail_reasons.append("unsupported_or_reject_error")

    answer_quality_note = "ok" if not fail_reasons else f"needs_review: {','.join(fail_reasons)}"
    table2_note = "ready" if (answer_grounded_to_rule and answer_useful) else "needs_quality_fix"

    return {
        "test_id": case["test_id"],
        "question": case["question"],
        "expected_type": case["expected_type"],
        "question_mode": question_mode,
        "application_status": application_status,
        "final_decision": final_decision,
        "answer_text": answer_text,
        "selected_rule_id": selected_rule_id,
        "legal_citations": legal_citations,
        "proof_present": proof_present,
        "missing_facts": missing_facts,
        "needs_clarification": needs_clarification,
        "hard_gates_hit": hard_gates_hit,
        "error_stage_final": error_stage_final,
        "forward_failure_reason": forward_failure_reason,
        "verification_summary": verification_summary,
        "answer_useful": answer_useful,
        "answer_type": answer_type,
        "answer_grounded_to_rule": answer_grounded_to_rule,
        "answer_has_clear_legal_rule": answer_has_clear_legal_rule,
        "answer_has_case_application": answer_has_case_application,
        "answer_quality_note": answer_quality_note,
        "verification_success": verification_success,
        "proof_or_partial_proof_present": proof_or_partial_proof_present,
        "missing_facts_correct_if_needed": missing_facts_correct_if_needed,
        "unsupported_or_reject_error": unsupported_or_reject_error,
        "table2_note": table2_note,
        "fail_reason": "" if not fail_reasons else ";".join(fail_reasons),
    }


def _run_case(case: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "question": case["question"],
        "session_id": f"table_ready_{case['test_id']}_{int(time.time() * 1000)}",
        "user_id": "table_readiness_runner",
    }
    r = requests.post(ASK_URL, json=payload, timeout=180)
    r.raise_for_status()
    return _as_dict(r.json())


def _build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["test_id"]: row for row in rows}

    q1 = by_id.get("Q1", {})
    q2 = by_id.get("Q2", {})
    q3 = by_id.get("Q3", {})

    rule_reading_pass = (
        q1.get("question_mode") == "rule_reading"
        and q1.get("application_status") == "none"
        and not q1.get("unsupported_or_reject_error", True)
    )
    fact_application_pass = (
        q2.get("question_mode") == "fact_application"
        and (
            (not q2.get("missing_facts"))
            or q2.get("application_status") == "conditional"
        )
        and not q2.get("unsupported_or_reject_error", True)
    )
    hybrid_pass = (
        q3.get("question_mode") == "hybrid"
        and bool(q3.get("answer_has_clear_legal_rule"))
        and bool(q3.get("answer_has_case_application"))
        and not q3.get("unsupported_or_reject_error", True)
    )

    backend_ready_for_table1 = rule_reading_pass and fact_application_pass and hybrid_pass
    backend_ready_for_table2 = all(
        bool(r.get("answer_useful"))
        and bool(r.get("answer_grounded_to_rule"))
        and not bool(r.get("unsupported_or_reject_error"))
        for r in rows
    )

    blocker_reasons: list[str] = []
    if not rule_reading_pass:
        blocker_reasons.append("Q1_rule_reading_policy_not_met")
    if not fact_application_pass:
        blocker_reasons.append("Q2_fact_application_policy_not_met")
    if not hybrid_pass:
        blocker_reasons.append("Q3_hybrid_policy_not_met")
    if not backend_ready_for_table2:
        blocker_reasons.append("table2_quality_or_grounding_not_met")

    stop_backend_and_move_to_real_exp = backend_ready_for_table1 and backend_ready_for_table2

    return {
        "rule_reading_pass": rule_reading_pass,
        "fact_application_pass": fact_application_pass,
        "hybrid_pass": hybrid_pass,
        "backend_ready_for_table1": backend_ready_for_table1,
        "backend_ready_for_table2": backend_ready_for_table2,
        "stop_backend_and_move_to_real_exp": stop_backend_and_move_to_real_exp,
        "blocker_reasons": blocker_reasons,
    }


def main() -> None:
    rows: list[dict[str, Any]] = []

    for case in TEST_CASES:
        try:
            resp = _run_case(case)
            rows.append(_eval_case(case, resp))
        except Exception as exc:
            rows.append(
                {
                    "test_id": case["test_id"],
                    "question": case["question"],
                    "expected_type": case["expected_type"],
                    "question_mode": "error",
                    "application_status": "error",
                    "final_decision": "REJECT",
                    "answer_text": "",
                    "selected_rule_id": "",
                    "legal_citations": [],
                    "proof_present": False,
                    "missing_facts": [],
                    "needs_clarification": False,
                    "hard_gates_hit": [],
                    "error_stage_final": "request_failed",
                    "forward_failure_reason": "",
                    "verification_summary": "",
                    "answer_useful": False,
                    "answer_type": "unknown",
                    "answer_grounded_to_rule": False,
                    "answer_has_clear_legal_rule": False,
                    "answer_has_case_application": False,
                    "answer_quality_note": f"request_error:{type(exc).__name__}",
                    "verification_success": False,
                    "proof_or_partial_proof_present": False,
                    "missing_facts_correct_if_needed": False,
                    "unsupported_or_reject_error": True,
                    "table2_note": "request_failed",
                    "fail_reason": f"request_failed:{type(exc).__name__}:{exc}",
                }
            )

    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base_url": BASE_URL,
        "tests": rows,
        "summary": _build_summary(rows),
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"WROTE {OUT_PATH}")


if __name__ == "__main__":
    main()
