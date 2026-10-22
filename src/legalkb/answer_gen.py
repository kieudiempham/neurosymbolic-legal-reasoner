"""Step 5: the final answer in words, written from a stored run (verdicts, proofs, legal basis), never from the
model's own knowledge. Stored in runs.final_answer.

    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.answer_gen            # write the answers runs are missing
    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.answer_gen 24         # (re)write the answer of run 24
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time

from .extract import CACHE, Extractor

ANSWER_MODEL = os.environ.get("LEGALKB_ANSWER_MODEL", "gpt-4.1-mini")
ANSWER_VERSION = "answer-v2"
VERDICT = {"yes": "CÓ", "no": "KHÔNG", "unknown": "CHƯA ĐỦ THÔNG TIN"}

PROMPT = """Bạn viết câu trả lời cuối cùng cho người hỏi về pháp luật Việt Nam, bằng tiếng Việt, dễ hiểu.
CHỈ dùng kết quả suy luận dưới đây (kết luận, căn cứ kèm nguyên văn, điều còn thiếu, ngoại lệ đang giả định không
có). KHÔNG thêm căn cứ, con số hay điều kiện nào khác; KHÔNG đổi kết luận.

Trình bày ngắn gọn (tối đa khoảng 150 chữ) theo thứ tự:
1. Trả lời thẳng câu hỏi (có / không / chưa đủ thông tin; con số nếu có).
2. Căn cứ: điều, khoản, điểm, văn bản (viết như "điểm a khoản 1 Điều 2 Luật số 41/2024/QH15").
3. Áp dụng: vì sao tình huống thỏa (hoặc không thỏa) điều kiện của căn cứ.
4. Nếu CHƯA ĐỦ THÔNG TIN: nêu cụ thể cần người hỏi cho biết thêm điều gì.
5. Lưu ý: kết luận chỉ đúng nếu không rơi vào các ngoại lệ đang giả định không có (chỉ khi có).
Làm theo phần KIỂM TRA (chẩn đoán) ở cuối: nếu nó đề nghị hỏi lại, xác nhận hay cảnh báo thì câu trả lời phải làm
đúng như vậy.

CÂU HỎI: {question}

DỮ KIỆN HỆ THỐNG ĐỌC ĐƯỢC TỪ CÂU HỎI:
{facts}

KẾT QUẢ SUY LUẬN:
{results}
"""


def cite(unit: str | None) -> str:
    """41/2024/QH15:D2.K1.a -> điểm a khoản 1 Điều 2 văn bản số 41/2024/QH15 (versions: @ amending document)."""
    if not unit or ":" not in unit:
        return unit or ""
    doc, rest = unit.split(":", 1)
    m = re.match(r"D(\d+[a-zđ]?)(?:@([^.]+))?(?:\.K(\d+))?(?:\.([a-zđ]))?", rest)
    if not m:
        return unit
    art, amend, clause, point = m.groups()
    parts = ([f"điểm {point}"] if point else []) + ([f"khoản {clause}"] if clause else []) + [f"Điều {art}"]
    return " ".join(parts) + f" văn bản số {doc}" + (f" (sửa đổi bởi văn bản số {amend})" if amend else "")


def context(runs, run: int) -> tuple[str, str, str]:
    question, = runs.execute("SELECT question FROM runs WHERE run_id=?", (run,)).fetchone()
    facts = "\n".join(f"- {'KHÔNG: ' if k == 'false_fact' else ''}{f}" for k, f in runs.execute(
        "SELECT kind, fact FROM run_facts WHERE run_id=? AND kind != 'parameter'", (run,)))
    res = []
    for q_no, typ, kind, verdict in runs.execute(
            "SELECT q_no, type, kind, verdict FROM run_questions WHERE run_id=? ORDER BY q_no", (run,)).fetchall():
        if kind == "law":
            res.append(f"Ý {q_no} ({typ}, tra luật):")
            for unit, mod, holder, conds, head, exc, text in runs.execute(
                    "SELECT unit, modality, holder, conditions, head, exceptions, text FROM run_law_norms "
                    "WHERE run_id=? AND q_no=?", (run, q_no)):
                res.append(f"  - {cite(unit)} ({mod}): nếu {conds or '-'} thì {head}"
                           + (f"; ngoại lệ: {exc}" if exc else "") + f"\n    nguyên văn: «{text}»")
            continue
        res.append(f"Ý {q_no} ({typ}): KẾT LUẬN {VERDICT.get(verdict, verdict)}")
        for aid, role, status, goal, missing, presumed in runs.execute(
                "SELECT answer_id, role, status, goal, missing, presumed_absent FROM run_answers WHERE run_id=? AND "
                "q_no=? ORDER BY role, answer_no", (run, q_no)).fetchall():
            label = "chứng minh điều ngược lại" if role == "contrary" else "con đường"
            res.append(f"  - {label} ({'chắc chắn' if status == 'certain' else 'có điều kiện'}): {goal}"
                       + (f"\n    còn thiếu: {missing}" if missing else "")
                       + (f"\n    giả định không có ngoại lệ: {presumed}" if presumed else ""))
            res += [f"    căn cứ {cite(u)}: «{t}»" for u, t in runs.execute(
                "SELECT unit, text FROM run_basis WHERE answer_id=?", (aid,))]
        if verdict == "no" and not runs.execute(
                "SELECT 1 FROM run_answers WHERE run_id=? AND q_no=?", (run, q_no)).fetchone():
            res.append("  - không có quy phạm nào trong cơ sở tri thức dẫn tới điều được hỏi")
    action = runs.execute("SELECT action, action_about FROM runs WHERE run_id=?", (run,)).fetchone()
    if action and action[0]:
        comps = {c: (layer, item, st) for c, layer, item, st in runs.execute(
            "SELECT comp_id, layer, item, statement FROM run_mbd_components WHERE run_id=?", (run,))}

        def name(c):  # a fact by its statement; a rule / a norm left out by its source unit
            layer, item, st = comps.get(c, ("", c, c))
            if layer == "kb":
                return f"luật theo {cite(item.split('#')[0])}: {st}"
            if layer == "retrieval":
                return f"quy định {cite(item.split('#')[0])} (có thể đã bị bỏ sót khi chọn luật)"
            return st

        about = [name(c) for c in json.loads(action[1] or "[]")]
        res.append("\nKIỂM TRA (chẩn đoán) TRƯỚC KHI TRẢ LỜI: " + {
            "answer": "không phát hiện lỗi; trả lời bình thường.",
            "ask": "thiếu thông tin trong câu hỏi; hỏi người dùng về: " + "; ".join(about),
            "confirm": "có thể hệ thống đã hiểu sai câu hỏi ở các điểm sau; KHÔNG kết luận chắc chắn, hãy nêu cách "
                       "hiểu này và đề nghị người dùng xác nhận hoặc sửa: " + "; ".join(about),
            "warn": "luật được dùng có thể sai hoặc có quy định bị bỏ sót; KHÔNG kết luận chắc chắn, nói rõ kết luận "
                    "có thể sai và nêu các điểm: "
                    + "; ".join(about),
            "unresolved": "hệ thống phát hiện điểm bất thường nhưng không xác định được nguyên nhân; KHÔNG kết luận "
                          "chắc chắn, nêu rằng cần người hỏi kiểm tra lại các điểm: " + "; ".join(about)}[action[0]])
    return question, facts or "(không có)", "\n".join(res) or "(không có kết quả)"


def generate(runs, run: int, model: str = ANSWER_MODEL) -> str:
    question, facts, results = context(runs, run)
    prompt = PROMPT.format(question=question, facts=facts, results=results)
    key = hashlib.sha1(f"{ANSWER_VERSION}|{model}|{prompt}".encode("utf-8")).hexdigest()
    f = CACHE / f"answer_{key}.txt"
    if f.exists():
        text = f.read_text(encoding="utf-8")
    else:
        client = Extractor(model).client
        for attempt in range(6):
            try:
                r = client.chat.completions.create(model=model, temperature=0,
                                                   messages=[{"role": "user", "content": prompt}])
                text = r.choices[0].message.content.strip()
                f.write_text(text, encoding="utf-8")
                break
            except Exception as e:  # noqa: BLE001
                if "insufficient_quota" in str(e):
                    raise
                time.sleep(min(60, 3 * 2 ** attempt))
        else:
            raise RuntimeError("answer generation failed")
    runs.execute("UPDATE runs SET final_answer=?, answer_model=? WHERE run_id=?", (text, model, run))
    runs.commit()
    return text


def main() -> None:
    from .trace import connect_runs

    sys.stdout.reconfigure(encoding="utf-8")
    runs = connect_runs()
    ids = [int(a) for a in sys.argv[1:]] or [r for (r,) in runs.execute(
        "SELECT run_id FROM runs WHERE final_answer IS NULL AND error IS NULL ORDER BY run_id")]
    for r in ids:
        print(f"\n=== run {r}\n{generate(runs, r)}")


if __name__ == "__main__":
    main()
