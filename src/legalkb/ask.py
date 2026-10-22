"""Ask a question end to end: parse -> reason / look up -> print the answer with its proof and legal basis.

    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.ask --sample "Tôi làm việc theo hợp đồng ... có phải đóng BHXH không?"
"""

from __future__ import annotations

import argparse
import sys

from .compile import PL_FILE
from .db import DB_FILE, connect
from .parse import Parser
from .questions import answer
from .reason import Reasoner, render

VERDICT = {"yes": "CÓ", "no": "KHÔNG", "unknown": "CHƯA ĐỦ THÔNG TIN"}


class Asker:
    def __init__(self, sample: bool = False):
        from .sample_kb import PARAMETERS, SAMPLE_DB, SAMPLE_PL, build

        if sample:
            build()
        self.con = connect(SAMPLE_DB if sample else DB_FILE)
        self.reasoner = Reasoner(SAMPLE_PL if sample else PL_FILE)
        self.parser = Parser(self.con)
        self.parameters = PARAMETERS if sample else []

    def ask(self, text: str) -> list[dict]:
        facts, false_facts, questions, raw = self.parser.parse(text)
        return [{"question": text, "facts": facts, "false_facts": false_facts, "parsed": q.__dict__,
                 **answer(q, self.parameters + facts, self.reasoner, self.con, false_facts)} for q in questions]


def show(res: dict) -> str:
    lines = [f"\n### {res['question']}", f"loại: {res['type']}   câu hỏi: {res['parsed']}",
             "dữ kiện: " + "; ".join(res["facts"])]
    if res["false_facts"]:
        lines.append("dữ kiện phủ định: " + "; ".join(res["false_facts"]))
    if res["kind"] == "law":
        for n in res["norms"]:
            lines.append(f"- {n['unit']} ({n['modality']}) {n['holder']}: nếu {' VÀ '.join(n['conditions']) or '-'} "
                         f"thì {n['head']}" + (f"; ngoại lệ: {', '.join(n['exceptions'])}" if n["exceptions"] else ""))
            lines.append(f"    «{n['text'][:200]}»")
        return "\n".join(lines)
    lines.append(f"TRẢ LỜI: {VERDICT[res['verdict']]}   (truy vấn {res['goal']})")
    for a in res["answers"] + res.get("contrary", []):
        lines.append(render(a))
        for b in a["basis"]:
            lines.append(f"    căn cứ {b['unit']}: «{b['text'][:160]}»")
    return "\n".join(lines)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("questions", nargs="+")
    ap.add_argument("--sample", action="store_true", help="use the hand-encoded sample KB")
    args = ap.parse_args()
    a = Asker(args.sample)
    for q in args.questions:
        for part in a.ask(q):
            print(show(part))


if __name__ == "__main__":
    main()
