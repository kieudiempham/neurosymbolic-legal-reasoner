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
from .questions import Question, answer
from .reason import Reasoner, render
from .trace import RUNS_DB, connect_runs, save_run

VERDICT = {"yes": "CÓ", "no": "KHÔNG", "unknown": "CHƯA ĐỦ THÔNG TIN"}


class Asker:
    def __init__(self, sample: bool = False, record: bool = True, verify: bool = True):
        from .sample_kb import PARAMETERS, SAMPLE_DB, SAMPLE_PL, build

        self.verify, self.last_mbd = verify, None

        if sample:
            build()
        self.db, self.kb = (SAMPLE_DB, SAMPLE_PL) if sample else (DB_FILE, PL_FILE)
        self.con = connect(self.db)
        self.reasoner = Reasoner(self.kb)
        self.parser = Parser(self.con)
        self.parameters = PARAMETERS if sample else []
        self.runs = connect_runs() if record else None

    def ask(self, text: str, batch: str | None = None, item_id: str | None = None, gold: str | None = None,
            session_id: str | None = None, turn: int | None = None) -> tuple[int | None, list[dict]]:
        """Answer one question; the run is stored even when a step fails (with the error and what was done)."""
        started = datetime.now().isoformat(timespec="seconds")
        facts, false_facts, raw, parts, error, parse_seconds, mbd_seconds = [], [], None, [], None, 0.0, 0.0
        self.last_mbd = None
        try:
            t0 = time.perf_counter()
            facts, false_facts, questions, raw = self.parser.parse(text)
            parse_seconds = time.perf_counter() - t0
            for q in questions:
                t1 = time.perf_counter()
                out = answer(q, self.parameters + facts, self.reasoner, self.con, false_facts)
                parts.append({"question": text, "facts": facts, "false_facts": false_facts, "parsed": q.__dict__,
                              "seconds": time.perf_counter() - t1, **out})
            if self.verify:  # step 4: diagnose the proofs before answering
                from .verify import verify

                t2 = time.perf_counter()
                self.last_mbd = verify(text, facts, parts, self.con, self.parser.ex.client)
                omitted = {c["item"] for c in self.last_mbd["components"]
                           if c["layer"] == "retrieval" and c["id"] in self.last_mbd["about"]}
                if self.last_mbd["action"] == "warn" and omitted:
                    # repair: step 2 left out norms about the goal; reason again with them, then diagnose again
                    first = self.last_mbd
                    parts = [{**p, **answer(Question(**p["parsed"]), self.parameters + facts, self.reasoner, self.con,
                                            false_facts, add=omitted)} if p["kind"] == "case" else p for p in parts]
                    self.last_mbd = verify(text, facts, parts, self.con, self.parser.ex.client)
                    self.last_mbd["repaired_from"] = {"action": first["action"], "added_norms": sorted(omitted),
                                                      "diagnoses": first["diagnoses"]}
                mbd_seconds = time.perf_counter() - t2
        except Exception as e:  # noqa: BLE001
            if "insufficient_quota" in str(e):
                raise
            error = f"{type(e).__name__}: {e}"[:2000]
        run = None
        if self.runs:
            run = save_run(self.runs, time=started, question=text, kb_program=str(self.kb), kb_database=str(self.db),
                           parser_model=self.parser.model, parser_output=raw, facts=facts, false_facts=false_facts,
                           parameters=self.parameters, parse_seconds=parse_seconds, parts=parts, batch=batch,
                           item_id=item_id, gold=gold, error=error, session_id=session_id, turn=turn,
                           mbd=self.last_mbd if self.verify and not error else None, mbd_seconds=mbd_seconds)
        if run and not error:
            from .answer_gen import generate

            try:  # step 5: the answer in words, from the stored run
                generate(self.runs, run)
            except Exception as e:  # noqa: BLE001
                if "insufficient_quota" in str(e):
                    raise
                self.runs.execute("UPDATE runs SET error=? WHERE run_id=?", (f"answer: {e}"[:2000], run))
                self.runs.commit()
        if error and not batch:
            raise RuntimeError(error)
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
            answer_text = a.runs.execute("SELECT final_answer FROM runs WHERE run_id=?", (run,)).fetchone()[0]
            print(f"\nCÂU TRẢ LỜI:\n{answer_text}\n(đã lưu: run {run} trong {RUNS_DB})")


if __name__ == "__main__":
    main()
