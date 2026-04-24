import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "backend"))

from app.path_setup import ensure_src_paths

ensure_src_paths()

from app.config import settings
from runtime.nli_bootstrap import resolve_nli_stack_bundle
from runtime.qa_runtime import configure_qa_orchestrator, get_qa_orchestrator
from runtime.qa_orchestrator import run_ask

OUT_DIR = Path("tests/output/validation_rescued_missingfacts")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CASES = [
    {
        "id": "n19",
        "question": "Khoản chi tiền lương muốn được tính là chi phí được trừ khi xác định thu nhập chịu thuế thì phải thỏa mãn điều kiện gì?",
    },
    {
        "id": "n21",
        "question": "Người sử dụng lao động có luôn phải ký hợp đồng lao động bằng văn bản với người lao động không?",
    },
]

# Batch-like mode: no clarification turn.
RUN_CONFIG = {
    "profile_name": "batch_no_clarify",
    "enable_clarification": False,
}

nli_verifier, nli_meta, nli_degraded = resolve_nli_stack_bundle(settings)
configure_qa_orchestrator(
    rulebase_core_path=settings.resolved_rulebase_core(),
    evidence_chunks_path=settings.resolved_evidence_chunks(),
    rule_retrieval_top_k=settings.rule_retrieval_top_k,
    nesy_nli_mock=settings.nesy_nli_mock,
    nli_verifier=nli_verifier,
    nli_degraded=nli_degraded,
    nli_meta=nli_meta,
    entailment_threshold=settings.nli_entailment_threshold,
    contradiction_threshold=settings.nli_contradiction_threshold,
    answer_reject_allow_fallback=settings.answer_reject_allow_fallback,
    settings=settings,
)
orch = get_qa_orchestrator()

summary = []
for item in CASES:
    cid = item["id"]
    resp = run_ask(
        question=item["question"],
        session_id=f"batch_rescued_{cid}",
        user_facts=[],
        session_svc=orch._session(),
        nesy=orch._nesy(),
        rulebase_registry=orch._bundle.rulebase_registry,
        domain_retriever=orch._bundle.domain_retriever,
        domain_selector=orch._bundle.domain_selector,
        retriever_advanced=orch._bundle.retriever_advanced,
        evidence_retriever=orch._evidence_retriever(),
        top_k=orch._top_k,
        max_repair_attempts_parse=orch._max_repair_attempts_parse,
        max_repair_attempts_answer=orch._max_repair_attempts_answer,
        max_repair_attempts_rule=orch._max_repair_attempts_rule,
        max_repair_attempts_backward=orch._max_repair_attempts_backward,
        max_repair_attempts_forward=orch._max_repair_attempts_forward,
        answer_reject_allow_fallback=orch._answer_reject_allow_fallback,
        settings=orch._settings,
        domain_hint=("tax" if cid == "n19" else "labor"),
        run_config=RUN_CONFIG,
    )
    payload = resp.model_dump(mode="json")
    out_path = OUT_DIR / f"{cid}_after_batch_no_clarify.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    dbg = payload.get("debug_trace") or {}
    ans = payload.get("answer") or {}
    answer_text = ans.get("answer_text") or ""

    summary.append(
        {
            "qid": cid,
            "needs_clarification": payload.get("needs_clarification"),
            "selected_rule_present": bool(payload.get("selected_rule")),
            "proof_present": payload.get("proof") is not None,
            "error": dbg.get("error"),
            "answer_present": bool(answer_text.strip()),
            "answer_generation_mode": ans.get("generation_mode"),
            "answer_has_missing_facts_list": "Thông tin còn thiếu cần xác minh" in answer_text,
            "answer_has_if_then_disclaimer": "Nếu các dữ kiện còn thiếu" in answer_text,
            "answer_has_non_final_disclaimer": "không phải kết luận khẳng định cuối cùng" in answer_text,
            "rescued_fallback_flow": dbg.get("rescued_fallback_flow"),
            "missing_facts": dbg.get("missing_facts"),
            "debug_trace_keys": list(dbg.keys()),
        }
    )

summary_path = OUT_DIR / "summary_n19_n21.json"
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print(f"saved={summary_path}")
