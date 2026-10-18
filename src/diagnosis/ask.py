"""Interactive CLI: ask a BHXH question, get a diagnosed, proof-grounded answer in IRAC form.

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.ask "Tôi ký hợp đồng lao động 6 tháng..."
    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.ask            (interactive loop)
"""

from __future__ import annotations

import argparse
import json
import sys

from .controller import Diagnoser, RunConfig
from .kb import KB, load_kb
from .llm_parser import LLMParser
from .nli import NLIModel
from .reasoner import ReasoningState
from .run_llm_baseline import GOAL_TEXT

GOAL_PROMPT = """Phân loại câu hỏi pháp luật bảo hiểm xã hội sau vào đúng MỘT câu hỏi pháp lý mà hệ thống hỗ trợ.

Các lựa chọn:
{options}
- out_of_scope: câu hỏi không thuộc các lựa chọn trên (ví dụ hỏi thủ tục, hồ sơ, định nghĩa, mức đóng).

Hướng dẫn: chọn câu hỏi pháp lý mà người dùng cuối cùng muốn biết, không chọn bước trung gian.
- Hỏi có phải/được/bắt buộc đóng hay tham gia BHXH (nói chung) -> compulsory_si.
- Chỉ chọn labor_relation khi người dùng hỏi trực tiếp có phải là quan hệ lao động hay không.
- Chỉ chọn must_contribute_month khi hỏi về việc đóng trong một tháng cụ thể (nghỉ không lương, tạm hoãn...).

Câu hỏi: {question}

Chỉ trả về JSON: {{"goal": "<một mã ở trên>"}}"""

ANSWER_PROMPT = """Bạn viết câu trả lời pháp lý cho người dùng theo cấu trúc IRAC, CHỈ dựa trên kết quả suy luận đã kiểm chứng dưới đây.
Không được thay đổi kết luận, không thêm căn cứ pháp lý ngoài danh sách đã cho.

Câu hỏi của người dùng: {question}
Câu hỏi pháp lý: {goal}
Kết luận đã kiểm chứng: {verdict}
Dữ kiện được sử dụng:
{facts}
Quy tắc pháp lý đã áp dụng (theo thứ tự suy luận):
{rules}
{extra}
Trả về JSON: {{"issue": "...", "rule": "...", "application": "...", "conclusion": "..."}}"""

VERDICT = {
    "true": "CÓ",
    "false": "KHÔNG",
    "abstain": "KHÔNG KẾT LUẬN (các quy định trong cơ sở tri thức xung đột và chưa có quan hệ ưu tiên/ngoại lệ được mã hóa)",
    "insufficient": "CHƯA ĐỦ DỮ KIỆN",
    "clarification_requested": "CHƯA ĐỦ DỮ KIỆN (cần người dùng bổ sung thông tin)",
}


def proof_rules(kb: KB, state: ReasoningState) -> list[str]:
    """Rules on the derivation of the goal (or, when it was not derived, the rules that were ruled out)."""
    order: list[str] = []

    def down(pred: str) -> None:
        f = state.facts.get(pred)
        if f is None or f.origin != "derived":
            return
        for p in state.proof_dependencies.get(pred, []):
            down(p)
        if f.rule not in order:
            order.append(f.rule)

    down(state.goal)
    if not order:
        order = [r.id for r in kb.rules_concluding(state.goal) if state.rule_status.get(r.id) in ("not_applicable", "blocked")]
    for a, b, _ in state.competing_pairs:
        order += [x for x in (a, b) if x not in order]
    return order


def describe_rule(kb: KB, rid: str, state: ReasoningState) -> str:
    r = kb.rules[rid]
    prem = "; ".join(
        f"{'' if p.value else 'KHÔNG: '}{kb.vocab[p.pred]['template_pos']} [{state.premise_status[rid][str(p)]}]"
        for p in r.premises
    )
    concl = kb.vocab[r.conclusion.pred]["template_pos" if r.conclusion.value else "template_neg"]
    return f"- {rid} ({r.source}): NẾU {prem} THÌ {concl} — trạng thái: {state.rule_status[rid]}"


def ask_once(question: str, kb: KB, parser: LLMParser, nli: NLIModel, interactive: bool, verbose: bool) -> dict:
    options = "\n".join(f"- {g}: {t}" for g, t in GOAL_TEXT.items())
    goal = parser._chat(f"goal|{parser.model}|{question}", GOAL_PROMPT.format(options=options, question=question)).get("goal")
    if goal not in GOAL_TEXT:
        return {"question": question, "goal": "out_of_scope",
                "answer": "Câu hỏi nằm ngoài phạm vi của cơ sở tri thức chẩn đoán hiện tại (BHXH: đối tượng tham gia, "
                          "nghĩa vụ đóng trong tháng, nơi đóng khi nhiều hợp đồng, lương hưu, BHXH một lần)."}

    parsed = parser.parse(question)

    def user(c: str):
        if not interactive:
            return None
        ans = input(f"\n[Hỏi lại] {kb.vocab[c]['ask']} (c = có / k = không / Enter = không rõ): ").strip().lower()
        return {"c": True, "co": True, "có": True, "y": True, "k": False, "khong": False, "không": False, "n": False}.get(ans)

    res = Diagnoser(kb, nli, RunConfig(), reparse=parser.reparse).run(question, goal, parsed, user)
    nli.save()
    state = res.final_state
    rules = proof_rules(kb, state)
    facts = "\n".join(
        f"- {kb.vocab[p]['template_pos' if f.value else 'template_neg']} (nguồn: {f.origin}{', \"' + f.span + '\"' if f.span else ''})"
        for p, f in state.facts.items() if f.origin != "derived" and kb.vocab[p].get("kind") == "input"
        and f.origin != "default"
    ) or "- (không có)"
    extra = ""
    if res.answer in ("insufficient", "clarification_requested"):
        from .reasoner import backward_trace_required

        missing = backward_trace_required(kb, state)
        extra = "Thông tin còn thiếu cần người dùng bổ sung:\n" + "\n".join(f"- {kb.vocab[c]['ask']}" for c in missing)
    irac = parser._chat(
        f"answer|{parser.model}|{question}|{res.answer}|{'|'.join(rules)}|{facts}",
        ANSWER_PROMPT.format(question=question, goal=GOAL_TEXT[goal], verdict=VERDICT[res.answer], facts=facts,
                             rules="\n".join(describe_rule(kb, r, state) for r in rules) or "- (không có)", extra=extra),
    )
    parser.save()
    out = {
        "question": question,
        "goal": goal,
        "parsed_facts": {p: f.value for p, f in parsed.items()},
        "diagnosis": res.first_diagnosis or ["(không phát hiện lỗi)"],
        "recovery": res.recovery,
        "verdict": res.answer,
        "rules_used": [f"{r}: {kb.rules[r].source}" for r in rules],
        "measurements": {"nli": res.nli_calls, "kb_checks": res.kb_checks},
        "irac": irac,
    }
    if verbose:
        out["nli_log"] = res.nli_log
    return out


def show(out: dict) -> None:
    if "irac" not in out:
        print("\n" + out["answer"])
        return
    print("\n=== Kết quả suy luận ===")
    print("Câu hỏi pháp lý :", GOAL_TEXT[out["goal"]])
    print("Fact từ parser  :", out["parsed_facts"])
    print("Chẩn đoán       :", ", ".join(out["diagnosis"]))
    if out["recovery"]:
        print("Đã xử lý        :", ", ".join(out["recovery"]))
    print("Kết luận        :", VERDICT[out["verdict"]])
    print("Căn cứ          :")
    for r in out["rules_used"]:
        print("   ", r)
    print("Số phép đo      :", out["measurements"])
    i = out["irac"]
    print("\n=== Trả lời (IRAC) ===")
    for k, lab in (("issue", "Vấn đề"), ("rule", "Quy định"), ("application", "Áp dụng"), ("conclusion", "Kết luận")):
        print(f"[{lab}] {i.get(k, '')}\n")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?")
    ap.add_argument("--no-clarify", action="store_true", help="do not ask follow-up questions")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    kb = load_kb()
    parser, nli = LLMParser(kb), NLIModel()
    questions = [args.question] if args.question else None
    while True:
        q = questions.pop(0) if questions else (None if args.question else input("\nCâu hỏi (Enter để thoát): ").strip())
        if not q:
            break
        out = ask_once(q, kb, parser, nli, interactive=not args.no_clarify, verbose=args.verbose)
        print(json.dumps(out, ensure_ascii=False, indent=1)) if args.json else show(out)
        if args.question:
            break


if __name__ == "__main__":
    main()
