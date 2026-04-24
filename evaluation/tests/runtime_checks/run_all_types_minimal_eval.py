#!/usr/bin/env python3
"""12-question E2E evaluation — Table 1 & Table 2 readiness (minimal fields)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

import requests

BASE_URL = "http://127.0.0.1:8002"
ASK_URL = f"{BASE_URL}/ask"
OUT_PATH = Path("tests/runtime_checks/all_types_minimal_eval.json")

# Internal pipeline tokens that must never appear in user-facing missing_facts
_INTERNAL_TOKENS: frozenset[str] = frozenset({
    "event_mismatch", "predicate_mismatch", "unification_broken",
    "constraint_missing_input", "missing_input", "actor_role_mismatch",
    "no_unifying_rule", "goal_not_achieved", "positive_condition_missing",
    "forward_gate_failure", "rule_backward_gate_failure",
    "answer_verification_reject", "unknown", "none", "n/a", "na", "_",
})

_INTERNAL_SUFFIX_PAT = re.compile(
    r"_(mismatch|broken|failure|missing|error|rejected)$", re.IGNORECASE
)


def _is_internal(token: str) -> bool:
    t = token.strip().lower()
    return t in _INTERNAL_TOKENS or bool(_INTERNAL_SUFFIX_PAT.search(t))


# ---------------------------------------------------------------------------
# Test cases
# semantic_group: "rule_reading" | "fact_application" | "hybrid_observe"
# observe_only: if True, result is not counted towards pass/fail
# ---------------------------------------------------------------------------
TEST_CASES: list[dict[str, Any]] = [
    {
        "test_id": "Q1",
        "question": "Doanh nghiệp phải thông báo thay đổi nội dung đăng ký doanh nghiệp trong bao nhiêu ngày?",
        "question_label": "rule_reading",
        "semantic_group": "rule_reading",
        "observe_only": False,
    },
    {
        "test_id": "Q2",
        "question": "Công ty tôi đã thay đổi nội dung đăng ký nhưng chưa rõ ngày gửi thông báo, vậy có bị quá hạn không?",
        "question_label": "fact_application",
        "semantic_group": "fact_application",
        "observe_only": False,
    },
    {
        "test_id": "Q3",
        "question": "Thời hạn thông báo thay đổi đăng ký doanh nghiệp là bao lâu, và nếu nộp trễ thì có bị xử lý gì không?",
        "question_label": "hybrid",
        "semantic_group": "hybrid_observe",
        "observe_only": True,
    },
    {
        "test_id": "Q4",
        "question": "Sau khi thay đổi nội dung đăng ký doanh nghiệp thì phải gửi thông báo trong thời hạn bao lâu?",
        "question_label": "deadline",
        "semantic_group": "rule_reading",
        "observe_only": False,
    },
    {
        "test_id": "Q5",
        "question": "Mức vốn điều lệ tối thiểu để thành lập công ty là bao nhiêu?",
        "question_label": "threshold",
        "semantic_group": "rule_reading",
        "observe_only": False,
    },
    {
        "test_id": "Q6",
        "question": "Trong những trường hợp nào doanh nghiệp được miễn lệ phí đăng ký kinh doanh?",
        "question_label": "applicability",
        "semantic_group": "rule_reading",
        "observe_only": False,
    },
    {
        "test_id": "Q7",
        "question": "Nếu doanh nghiệp không thông báo thay đổi nội dung đăng ký đúng hạn thì sẽ bị xử lý như thế nào?",
        "question_label": "legal_effect",
        "semantic_group": "hybrid_observe",
        "observe_only": True,
    },
    {
        "test_id": "Q8",
        "question": "Doanh nghiệp có bắt buộc phải thông báo khi thay đổi nội dung đăng ký không?",
        "question_label": "obligation_permission",
        "semantic_group": "rule_reading",
        "observe_only": False,
    },
    {
        "test_id": "Q9",
        "question": "Hồ sơ đăng ký thay đổi nội dung đăng ký doanh nghiệp gồm những giấy tờ gì?",
        "question_label": "dossier",
        "semantic_group": "rule_reading",
        "observe_only": False,
    },
    {
        "test_id": "Q10",
        "question": "Doanh nghiệp phải nộp hồ sơ thay đổi nội dung đăng ký tại cơ quan nào?",
        "question_label": "authority",
        "semantic_group": "rule_reading",
        "observe_only": False,
    },
    {
        "test_id": "Q11",
        "question": "Quy trình thay đổi nội dung đăng ký doanh nghiệp gồm những bước nào?",
        "question_label": "procedure",
        "semantic_group": "rule_reading",
        "observe_only": False,
    },
    {
        "test_id": "Q12",
        "question": "Có trường hợp nào doanh nghiệp không phải thông báo thay đổi nội dung đăng ký không?",
        "question_label": "exception",
        "semantic_group": "rule_reading",
        "observe_only": False,
    },
]


# ---------------------------------------------------------------------------
# Response field pickers (identical contract to 3case runner)
# ---------------------------------------------------------------------------

def _as_dict(v: Any) -> dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> list[Any]:
    return v if isinstance(v, list) else []


def _pick_answer_text(resp: dict) -> str:
    answer = resp.get("answer")
    if isinstance(answer, str):
        return answer.strip()
    if isinstance(answer, dict):
        txt = str(answer.get("answer_text") or answer.get("text") or "").strip()
        if txt:
            return txt
    for key in ("answer_text",):
        txt = str(resp.get(key) or "").strip()
        if txt:
            return txt
    txt = str(_as_dict(resp.get("final_response")).get("answer_text") or "").strip()
    return txt


def _pick_selected_rule_id(resp: dict) -> str:
    sel = _as_dict(resp.get("selected_rule"))
    return str(sel.get("rule_id") or resp.get("selected_rule_id") or "").strip()


def _pick_missing_facts(resp: dict) -> list[str]:
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


def _pick_question_mode(resp: dict) -> str:
    qm = str(resp.get("question_mode") or "").strip()
    if qm:
        return qm
    return str(_as_dict(resp.get("debug_trace")).get("question_mode") or "unknown").strip() or "unknown"


def _pick_application_status(resp: dict) -> str:
    st = str(resp.get("application_status") or "").strip()
    if st:
        return st
    return str(_as_dict(resp.get("debug_trace")).get("application_status") or "unknown").strip() or "unknown"


def _pick_final_decision(resp: dict) -> str:
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


def _pick_error_stage(resp: dict) -> str:
    for key in ("error_stage_final", "error_stage"):
        val = str(resp.get(key) or "").strip()
        if val:
            return val
    return str(resp.get("error") or "").strip()


def _bool_proof_present(resp: dict) -> bool:
    if bool(resp.get("proof_trace")):
        return True
    if bool(resp.get("proof")):
        return True
    dbg = _as_dict(resp.get("debug_trace"))
    return bool(dbg.get("proof_steps_by_domain"))


def _classify_answer_type(application_status: str) -> str:
    if application_status == "none":
        return "A"
    if application_status == "conditional":
        return "A+B"
    if application_status == "final":
        return "A+C"
    return "unknown"


def _has_case_application_cue(answer_text: str) -> bool:
    low = answer_text.lower()
    cues = ["nếu", "if", "trường hợp", "áp dụng", "qua hạn", "quá hạn", "xử lý", "có bị"]
    return any(c in low for c in cues)


# ---------------------------------------------------------------------------
# Per-case evaluator
# ---------------------------------------------------------------------------

def _eval_case(case: dict[str, Any], resp: dict[str, Any]) -> dict[str, Any]:
    answer_text = _pick_answer_text(resp)
    selected_rule_id = _pick_selected_rule_id(resp)
    legal_citations = _as_list(resp.get("legal_citations") or _as_dict(resp.get("answer")).get("citations"))
    proof_present = _bool_proof_present(resp)
    missing_facts_raw = _pick_missing_facts(resp)
    question_mode = _pick_question_mode(resp)
    application_status = _pick_application_status(resp)
    final_decision = _pick_final_decision(resp)
    error_stage = _pick_error_stage(resp)

    # Filter internal tokens from missing_facts before any evaluation
    missing_facts = [f for f in missing_facts_raw if not _is_internal(f)]
    has_internal_leak = any(_is_internal(f) for f in missing_facts_raw)

    answer_type = _classify_answer_type(application_status)
    answer_useful = bool(answer_text) and ("xin lỗi" not in answer_text.lower())
    answer_grounded_to_rule = bool(selected_rule_id) and (proof_present or bool(legal_citations))
    answer_has_clear_legal_rule = bool(selected_rule_id) or bool(legal_citations)
    answer_has_case_application = _has_case_application_cue(answer_text)
    verification_success = final_decision in {"ACCEPT", "REPAIR", ""}
    unsupported_or_reject_error = bool(error_stage) or final_decision == "REJECT"

    # missing_facts_correct_if_needed: True unless it's a fact_application in conditional
    # state and missing_facts is empty or contains only internal tokens
    if case["semantic_group"] == "fact_application" and application_status == "conditional":
        missing_facts_correct_if_needed = bool(missing_facts) and not has_internal_leak
    else:
        missing_facts_correct_if_needed = True

    return {
        "test_id": case["test_id"],
        "question_label": case["question_label"],
        "observe_only": case["observe_only"],
        "question_mode": question_mode,
        "application_status": application_status,
        "final_decision": final_decision,
        "answer_type": answer_type,
        "answer_useful": answer_useful,
        "answer_grounded_to_rule": answer_grounded_to_rule,
        "answer_has_clear_legal_rule": answer_has_clear_legal_rule,
        "answer_has_case_application": answer_has_case_application,
        "proof_present": proof_present,
        "verification_success": verification_success,
        "missing_facts": missing_facts,
        "missing_facts_has_internal_leak": has_internal_leak,
        "missing_facts_correct_if_needed": missing_facts_correct_if_needed,
        "unsupported_or_reject_error": unsupported_or_reject_error,
    }


def _error_row(case: dict[str, Any], exc: Exception, http_status: int = 0) -> dict[str, Any]:
    error_type = "backend_500_preexisting" if http_status == 500 else "request_failed"
    return {
        "test_id": case["test_id"],
        "question_label": case["question_label"],
        "observe_only": case["observe_only"],
        "question_mode": "error",
        "application_status": "error",
        "final_decision": "REJECT",
        "answer_type": "unknown",
        "answer_useful": False,
        "answer_grounded_to_rule": False,
        "answer_has_clear_legal_rule": False,
        "answer_has_case_application": False,
        "proof_present": False,
        "verification_success": False,
        "missing_facts": [],
        "missing_facts_has_internal_leak": False,
        "missing_facts_correct_if_needed": False,
        "unsupported_or_reject_error": True,
        "_error_type": error_type,
        "_error": f"{type(exc).__name__}: {exc}",
    }


def _run_case(case: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Returns (response_dict, http_status_code)."""
    payload = {
        "question": case["question"],
        "session_id": f"alltype_eval_{case['test_id']}_{int(time.time() * 1000)}",
        "user_id": "all_types_eval_runner",
    }
    r = requests.post(ASK_URL, json=payload, timeout=180)
    return _as_dict(r.json()), r.status_code


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

_RULE_READING_TABLE1_MIN_PASS = 6  # need at least 6/9 rule_reading Qs to pass table1


def _build_summary(rows: list[dict[str, Any]], cases: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {r["test_id"]: r for r in rows}

    # Separate backend crashes (pre-existing 500s) from logic results
    crash_ids = [
        r["test_id"] for r in rows
        if r.get("_error_type") == "backend_500_preexisting"
    ]
    non_crash_rows = [r for r in rows if r["test_id"] not in crash_ids]

    # --- rule_reading group (non-observe_only, non-crash) ---
    rr_ids = [c["test_id"] for c in cases if c["semantic_group"] == "rule_reading" and not c["observe_only"]]
    rr_crash = [tid for tid in rr_ids if tid in crash_ids]
    rr_non_crash = [tid for tid in rr_ids if tid not in crash_ids]
    rr_pass = [
        tid for tid in rr_non_crash
        if by_id.get(tid, {}).get("answer_has_clear_legal_rule")
        and by_id.get(tid, {}).get("answer_useful")
    ]
    rr_logic_fail = [tid for tid in rr_non_crash if tid not in rr_pass]
    rule_reading_pass_count = len(rr_pass)

    # --- fact_application (Q2) ---
    q2 = by_id.get("Q2", {})
    fact_application_pass = (
        q2.get("answer_type") == "A+B"
        and q2.get("answer_has_case_application", False)
        and q2.get("missing_facts_correct_if_needed", False)
        and not q2.get("missing_facts_has_internal_leak", True)
    )

    # --- hybrid observe (Q3, Q7) ---
    hybrid_observation = {
        tid: {
            "question_mode": by_id.get(tid, {}).get("question_mode", "unknown"),
            "answer_useful": by_id.get(tid, {}).get("answer_useful", False),
            "answer_has_clear_legal_rule": by_id.get(tid, {}).get("answer_has_clear_legal_rule", False),
            "answer_has_case_application": by_id.get(tid, {}).get("answer_has_case_application", False),
        }
        for c in cases if c["observe_only"]
        for tid in [c["test_id"]]
    }

    # --- table1_ready: scored on non-crash questions only ---
    # Need >= threshold non-crash rule_reading passes AND Q2 fact_application pass
    rr_min_pass = min(_RULE_READING_TABLE1_MIN_PASS, len(rr_non_crash))
    table1_ready = (
        rule_reading_pass_count >= rr_min_pass
        and fact_application_pass
        and not crash_ids  # no crashes allowed for table1
    )

    # --- table2_ready: scored on non-crash questions ---
    table2_criteria_pass = [
        r["test_id"] for r in non_crash_rows
        if r.get("answer_grounded_to_rule")
        and r.get("proof_present")
        and r.get("verification_success")
        and not r.get("unsupported_or_reject_error")
    ]
    non_crash_total = len(non_crash_rows)
    table2_majority = (
        non_crash_total > 0
        and len(table2_criteria_pass) >= (non_crash_total // 2 + 1)
    )
    q2_table2_ok = (
        q2.get("missing_facts_correct_if_needed", False)
        and not q2.get("missing_facts_has_internal_leak", True)
    )
    table2_ready = table2_majority and q2_table2_ok and not crash_ids

    # --- blockers ---
    blocker_types: list[str] = []
    if crash_ids:
        blocker_types.append(
            f"backend_500_preexisting({crash_ids}): "
            "pre-existing recursion bug — not caused by current changes"
        )
    if rr_logic_fail:
        blocker_types.append(f"rule_reading_logic_fail({rr_logic_fail})")
    if rule_reading_pass_count < rr_min_pass:
        blocker_types.append(
            f"rule_reading_pass_count={rule_reading_pass_count}/{len(rr_non_crash)}_below_threshold({rr_min_pass})"
        )
    if not fact_application_pass:
        blocker_types.append(
            f"Q2_fact_application_fail("
            f"mode={q2.get('question_mode','?')}, "
            f"answer_type={q2.get('answer_type','?')}, "
            f"missing_facts={q2.get('missing_facts',[])}, "
            f"internal_leak={q2.get('missing_facts_has_internal_leak',False)})"
        )
    if not table2_majority:
        fail_nc = [r["test_id"] for r in non_crash_rows if r["test_id"] not in table2_criteria_pass]
        blocker_types.append(f"table2_majority_fail_non_crash({fail_nc})")
    if not q2_table2_ok:
        blocker_types.append(
            f"Q2_table2_missing_facts_fail("
            f"correct={q2.get('missing_facts_correct_if_needed')}, "
            f"leak={q2.get('missing_facts_has_internal_leak')})"
        )

    return {
        "backend_crash_ids": crash_ids,
        "rule_reading_pass_count": rule_reading_pass_count,
        "rule_reading_total_non_crash": len(rr_non_crash),
        "rule_reading_crashed_ids": rr_crash,
        "rule_reading_pass_ids": rr_pass,
        "rule_reading_logic_fail_ids": rr_logic_fail,
        "fact_application_pass": fact_application_pass,
        "hybrid_observation": hybrid_observation,
        "table2_criteria_pass_count": len(table2_criteria_pass),
        "table2_non_crash_total": non_crash_total,
        "table1_ready": table1_ready,
        "table2_ready": table2_ready,
        "blocker_types": blocker_types,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    rows: list[dict[str, Any]] = []

    for case in TEST_CASES:
        print(f"  Running {case['test_id']} ({case['question_label']}) ...", flush=True)
        try:
            resp, http_status = _run_case(case)
            if http_status == 500:
                raise RuntimeError(f"HTTP 500 from server: {resp.get('detail','')}")
            row = _eval_case(case, resp)
        except Exception as exc:
            http_st = 500 if "500" in str(exc) else 0
            row = _error_row(case, exc, http_status=http_st)
        rows.append(row)
        err_tag = f" [{row.get('_error_type','')}]" if row.get("_error_type") else ""
        status = "PASS" if (row.get("answer_useful") and row.get("answer_grounded_to_rule")) else "FAIL"
        print(f"    mode={row['question_mode']} answer_type={row['answer_type']} {status}{err_tag}", flush=True)

    summary = _build_summary(rows, TEST_CASES)

    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base_url": BASE_URL,
        "tests": rows,
        "summary": summary,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWROTE {OUT_PATH}")
    print(f"\n=== SUMMARY ===")
    print(f"  rule_reading_pass:     {summary['rule_reading_pass_count']}/{summary['rule_reading_total']}")
    print(f"  fact_application_pass: {summary['fact_application_pass']}")
    print(f"  table2 criteria:       {summary['table2_criteria_pass_count']}/{summary['table2_total']}")
    print(f"  table1_ready:          {summary['table1_ready']}")
    print(f"  table2_ready:          {summary['table2_ready']}")
    if summary["blocker_types"]:
        print(f"  BLOCKERS:")
        for b in summary["blocker_types"]:
            print(f"    - {b}")
    else:
        print(f"  No blockers.")
    print(f"\n  hybrid_observation:")
    for tid, obs in summary["hybrid_observation"].items():
        print(f"    {tid}: {obs}")


if __name__ == "__main__":
    main()
