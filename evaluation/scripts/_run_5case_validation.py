"""
5-case validation run for rescued-fallback verification-policy patch.
Runs n11, n13, n17, n19, n21 through the patched backend (port 8001)
and saves individual JSON outputs plus a comparison summary.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from urllib import request, error

BASE_URL = "http://127.0.0.1:8001"
TIMEOUT = 120.0
OUTPUT_DIR = Path("tests/output/validation_5case")
RAW_BASELINE_DIR = Path("tests/output/raw")
PLACEHOLDER_CLARIFY = "Co, theo thong tin toi cung cap."

CASES = [
    {"id": "n11", "domain_hint": "tax",        "intent_hint": "obligation",             "question": "Công ty mới thành lập thì nghĩa vụ đăng ký thuế phát sinh vào thời điểm nào?"},
    {"id": "n13", "domain_hint": "tax",        "intent_hint": "deadline_requirement",   "question": "Tờ khai thuế theo tháng phải nộp chậm nhất vào ngày nào của kỳ tiếp theo?"},
    {"id": "n17", "domain_hint": "tax",        "intent_hint": "obligation",             "question": "Hiện nay doanh nghiệp có bắt buộc phải lập và sử dụng hóa đơn điện tử không?"},
    {"id": "n19", "domain_hint": "tax",        "intent_hint": "applicability_condition","question": "Khoản chi tiền lương muốn được tính là chi phí được trừ khi xác định thu nhập chịu thuế thì phải thỏa mãn điều kiện gì?"},
    {"id": "n21", "domain_hint": "labor",      "intent_hint": "obligation",             "question": "Người sử dụng lao động có luôn phải ký hợp đồng lao động bằng văn bản với người lao động không?"},
]


def post_json(url: str, payload: dict, timeout: float):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(url=url, data=body,
                          headers={"Content-Type": "application/json; charset=utf-8"},
                          method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return int(getattr(resp, "status", 200)), json.loads(resp.read().decode("utf-8", errors="replace"))
    except error.HTTPError as exc:
        text = ""
        try:
            text = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return int(exc.code), json.loads(text) if text.strip() else {}


def build_clarify_answers(questions):
    return [{"fact_key": q["fact_key"], "value": PLACEHOLDER_CLARIFY}
            for q in questions if isinstance(q, dict) and q.get("fact_key")]


def extract_fields(data: dict, cid: str) -> dict:
    dbg = data.get("debug_trace") or {}
    sr = data.get("selected_rule")
    proof = data.get("proof")

    # flags from trace events
    rescued_flow = False
    backward_rescue_relaxation = False
    answer_verification_rescue = bool(dbg.get("answer_verification_rescued_relaxation"))
    has_forward_gate = bool(dbg.get("forward_gate"))

    backward_gate_decision = None
    backward_gate_level = None
    backward_gate_reasons = []

    for bucket in ("rule_backward_gate", "rule_backward_gate_rerun"):
        for t in (dbg.get(bucket) or []):
            if not isinstance(t, dict):
                continue
            stage = t.get("stage")
            if stage == "backward_gate":
                backward_gate_decision = t.get("relaxed_final_decision") or t.get("final_decision")
                backward_gate_level = t.get("verification_level")
                backward_gate_reasons = t.get("rejection_reason") or []
                if t.get("backward_rescue_relaxation_triggered"):
                    backward_rescue_relaxation = True
            if stage == "backward_repair_promoted_for_rescued_fallback":
                rescued_flow = True

    return {
        "qid": cid,
        "selected_rule": sr,
        "proof_is_null": proof is None,
        "has_forward_gate": has_forward_gate,
        "error": dbg.get("error"),
        "rescued_fallback_flow": rescued_flow,
        "backward_rescue_relaxation_triggered": backward_rescue_relaxation,
        "answer_verification_rescued_relaxation": answer_verification_rescue,
        "backward_gate_decision": backward_gate_decision,
        "backward_gate_level": backward_gate_level,
        "backward_gate_reasons": backward_gate_reasons,
    }


def load_baseline(cid: str) -> dict:
    p = RAW_BASELINE_DIR / f"{cid}.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    dbg = data.get("debug_trace") or {}
    return {
        "selected_rule": data.get("selected_rule"),
        "proof_is_null": data.get("proof") is None,
        "has_forward_gate": bool(dbg.get("forward_gate")),
        "error": dbg.get("error"),
    }


OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
results = []

for case in CASES:
    cid = case["id"]
    print(f"\n{'='*60}")
    print(f"Running {cid}: {case['question'][:70]}")

    # Step 1: /ask
    ask_payload = {
        "question": case["question"],
        "domain_hint": case["domain_hint"],
        "intent_hint": case["intent_hint"],
        "session_id": f"val5_{cid}_{int(time.time())}",
    }
    t0 = time.time()
    status, ask_resp = post_json(f"{BASE_URL}/ask", ask_payload, TIMEOUT)
    elapsed = time.time() - t0
    print(f"  /ask => HTTP {status}, {elapsed:.1f}s")

    final_resp = ask_resp

    # Step 2: /clarify if needed
    if status == 200 and ask_resp.get("needs_clarification"):
        cqs = ask_resp.get("clarification_questions") or []
        answers = build_clarify_answers(cqs)
        if answers:
            session_id = ask_resp.get("session_id") or ask_payload["session_id"]
            clarify_payload = {"session_id": session_id, "answers": answers}
            status2, clarify_resp = post_json(f"{BASE_URL}/clarify", clarify_payload, TIMEOUT)
            print(f"  /clarify => HTTP {status2}")
            if status2 == 200:
                final_resp = clarify_resp

    # Save raw output
    out_path = OUTPUT_DIR / f"{cid}_after.json"
    out_path.write_text(json.dumps(final_resp, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Saved: {out_path}")

    # Extract fields
    after = extract_fields(final_resp, cid)
    before = load_baseline(cid)

    result = {"cid": cid, "before": before, "after": after}
    results.append(result)

    print(f"  BEFORE: rule={'Y' if before.get('selected_rule') else 'N'} proof={'N' if before.get('proof_is_null', True) else 'Y'} err={before.get('error')}")
    print(f"  AFTER:  rule={'Y' if after['selected_rule'] else 'N'} proof={'N' if after['proof_is_null'] else 'Y'} err={after['error']}")
    print(f"  rescued_flow={after['rescued_fallback_flow']} bk_relax={after['backward_rescue_relaxation_triggered']} fwd={after['has_forward_gate']}")

# Save summary
summary_path = OUTPUT_DIR / "summary.json"
summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n\nSaved summary to {summary_path}")

# Print aggregate
rule_after = sum(1 for r in results if r["after"]["selected_rule"])
proof_after = sum(1 for r in results if not r["after"]["proof_is_null"])
fwd_after = sum(1 for r in results if r["after"]["has_forward_gate"])
rescued = sum(1 for r in results if r["after"]["rescued_fallback_flow"])
bk_relax = sum(1 for r in results if r["after"]["backward_rescue_relaxation_triggered"])

print("\n=== AGGREGATE ===")
print(f"  selected_rule after:   {rule_after}/5")
print(f"  proof after:           {proof_after}/5")
print(f"  forward gate reached:  {fwd_after}/5")
print(f"  rescued_flow triggered: {rescued}/5")
print(f"  bk_relax triggered:    {bk_relax}/5")
