"""Ask a question end to end: parse -> reason / look up -> print the answer with its proof and legal basis.

Every question asked is stored as a run in data/legalkb/runs.sqlite (see trace.py): its steps, the case facts,
each sub-question and its Prolog goal, every answer with its proof tree, missing facts, presumptions and legal basis.

    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.ask --sample "Tôi làm việc theo hợp đồng ... có phải đóng BHXH không?"
    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.trace 3          # read run 3 again
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime

from .compile import PL_FILE
from .db import DB_FILE, connect
from .parse import Parser
from .questions import answer
from .reason import Reasoner, render
from .trace import RUNS_DB, connect_runs, save_run

VERDICT = {"yes": "CÓ", "no": "KHÔNG", "unknown": "CHƯA ĐỦ THÔNG TIN"}


class Asker:
    def __init__(self, sample: bool = False, record: bool = True):
        from .sample_kb import PARAMETERS, SAMPLE_DB, SAMPLE_PL, build

        if sample:
            build()
        self.db, self.kb = (SAMPLE_DB, SAMPLE_PL) if sample else (DB_FILE, PL_FILE)
        self.con = connect(self.db)
        self.reasoner = Reasoner(self.kb)
        self.parser = Parser(self.con)
        self.parameters = PARAMETERS if sample else []
        self.runs = connect_runs() if record else None

    def ask(self, text: str) -> tuple[int | None, list[dict]]:
        started = datetime.now().isoformat(timespec="seconds")
        t0 = time.perf_counter()
        facts, false_facts, questions, raw = self.parser.parse(text)
        parse_seconds = time.perf_counter() - t0
        parts = []
        for q in questions:
            t1 = time.perf_counter()
            out = answer(q, self.parameters + facts, self.reasoner, self.con, false_facts)
            parts.append({"question": text, "facts": facts, "false_facts": false_facts, "parsed": q.__dict__,
                          "seconds": time.perf_counter() - t1, **out})
        run = None
        if self.runs:
            run = save_run(self.runs, time=started, question=text, kb_program=str(self.kb), kb_database=str(self.db),
                           parser_model=self.parser.model, parser_output=raw, facts=facts, false_facts=false_facts,
                           parameters=self.parameters, parse_seconds=parse_seconds, parts=parts)
        return run, parts


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
    ap.add_argument("--no-record", action="store_true", help="do not store the run in data/legalkb/runs.sqlite")
    args = ap.parse_args()
    a = Asker(args.sample, not args.no_record)
    for q in args.questions:
        run, parts = a.ask(q)
        for part in parts:
            print(show(part))
        if run:
            print(f"(đã lưu: run {run} trong {RUNS_DB})")


if __name__ == "__main__":
    main()
