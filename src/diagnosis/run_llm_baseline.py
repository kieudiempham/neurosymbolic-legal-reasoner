"""Neural LLM baseline: answer each diagnostic instance from the question plus the relevant legal text.

Reads LLM_API_KEY / LLM_BASE_URL / LLM_MODEL from .env (OpenAI-compatible endpoint). Merges its row
into experiments/diag/results.json under "neural_llm".
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .inject import build_instances
from .kb import DATA_DIR, load_cases, load_kb
from .run_eval import OUT_DIR

ROOT = Path(__file__).resolve().parents[2]
GOAL_TEXT = {
    "compulsory_si": "Người lao động có thuộc đối tượng tham gia bảo hiểm xã hội bắt buộc không?",
    "must_contribute_month": "Người lao động có phải đóng bảo hiểm xã hội bắt buộc trong tháng đó không?",
    "contribute_at_first_contract": "Người lao động có tham gia BHXH bắt buộc theo hợp đồng lao động giao kết đầu tiên không?",
    "entitled_pension": "Người lao động có đủ điều kiện hưởng lương hưu không?",
    "entitled_lump_sum": "Người lao động có được hưởng bảo hiểm xã hội một lần không?",
    "labor_relation": "Giữa hai bên có quan hệ lao động không?",
}
PROMPT = """Bạn là trợ lý pháp lý. Dựa vào trích dẫn pháp luật dưới đây và câu hỏi của người dùng, hãy trả lời câu hỏi pháp lý.

[TRÍCH DẪN PHÁP LUẬT]
{context}

[CÂU HỎI CỦA NGƯỜI DÙNG]
{question}

[CÂU HỎI PHÁP LÝ CẦN KẾT LUẬN]
{goal}

Chỉ trả về JSON: {{"answer": "yes" | "no" | "insufficient" | "conflict", "reason": "<ngắn gọn>"}}
- "insufficient": câu hỏi thiếu dữ kiện cần thiết để kết luận.
- "conflict": các quy định áp dụng mâu thuẫn và không thể xác định quy định nào ưu tiên."""


def main() -> None:
    load_dotenv(ROOT / ".env")
    key = os.environ.get("LLM_API_KEY")
    if not key:
        raise SystemExit("LLM_API_KEY is empty in .env")
    client = OpenAI(api_key=key, base_url=os.environ.get("LLM_BASE_URL") or None)
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    context = (DATA_DIR / "legal_context_bhxh.txt").read_text(encoding="utf-8")
    kb = load_kb()
    insts = build_instances(kb, load_cases(kb=kb))
    cache_f = OUT_DIR / f"llm_cache_{model.replace('/', '_')}.json"
    cache = json.loads(cache_f.read_text(encoding="utf-8")) if cache_f.exists() else {}
    rows = []
    for inst in insts:
        k = inst.goal + "␞" + inst.question
        if k not in cache:
            for attempt in range(5):
                try:
                    resp = client.chat.completions.create(
                        model=model,
                        temperature=0.0,
                        top_p=1.0,
                        response_format={"type": "json_object"},
                        messages=[{"role": "user", "content": PROMPT.format(
                            context=context, question=inst.question, goal=GOAL_TEXT[inst.goal])}],
                    )
                    cache[k] = json.loads(resp.choices[0].message.content)
                    break
                except Exception as e:  # rate limits / malformed JSON
                    print("retry", attempt, type(e).__name__, str(e)[:120])
                    time.sleep(5 * (attempt + 1))
            cache_f.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        a = str(cache.get(k, {}).get("answer", "insufficient")).lower()
        ans = {"yes": "true", "no": "false", "conflict": "abstain"}.get(a, "insufficient")
        rows.append({"iid": inst.iid, "gold_category": inst.category, "answer": ans,
                     "expected": inst.expected_answer, "answer_ok": ans == inst.expected_answer})
    n = len(rows)
    faulty = [r for r in rows if r["gold_category"] != "Normal"]
    summary = {
        "model": model,
        "final_answer_acc": sum(r["answer_ok"] for r in rows) / n,
        "final_answer_acc_faulty": sum(r["answer_ok"] for r in faulty) / max(1, len(faulty)),
        "measurements_per_query": 0.0,
    }
    out = {"summary": summary, "rows": rows}
    (OUT_DIR / "results_llm.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
