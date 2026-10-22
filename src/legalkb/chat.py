"""Conversation on top of the pipeline: ask, get an answer or a request for more information, reply, get the answer.

When the last answer of a session was "not enough information", the next message is taken as the missing
information: it is appended to the question and the whole pipeline runs again (a new turn of the same session).
Otherwise a message starts a new question. Every turn is a run in data/legalkb/runs.sqlite (session_id, turn).

    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.chat --sample          # terminal
    commands: /moi (new question)   /trace (proof of the last turn)   /thoat (quit)
"""

from __future__ import annotations

import argparse
import sys
import uuid

from .ask import Asker
from .trace import show_run

VERDICT = {"yes": "CÓ", "no": "KHÔNG", "unknown": "CHƯA ĐỦ THÔNG TIN"}


def _brief(part: dict) -> dict:
    """What a client needs from one sub-question: verdict, what to ask, proofs and legal basis."""
    if part["kind"] == "law":
        return {"type": part["type"], "kind": "law", "norms": part["norms"]}
    missing = sorted({m for a in part["answers"] + part.get("contrary", []) for m in a["missing"]})
    presumed = sorted({m for a in part["answers"] for m in a["presumed_absent"]})
    return {"type": part["type"], "kind": "case", "goal": part["goal"], "verdict": part["verdict"],
            "verdict_vi": VERDICT[part["verdict"]], "missing": missing, "presumed_absent": presumed,
            "answers": part["answers"], "contrary": part.get("contrary", [])}


class Dialogue:
    def __init__(self, asker: Asker):
        self.asker = asker
        self.sessions: dict[str, dict] = {}  # id -> {"question", "additions", "turn", "needs_more"}

    def new_session(self) -> str:
        sid = uuid.uuid4().hex[:12]
        self.sessions[sid] = {"question": None, "additions": [], "turn": 0, "needs_more": False}
        return sid

    def say(self, sid: str | None, message: str) -> dict:
        if not sid or sid not in self.sessions:
            sid = self.new_session()
        s = self.sessions[sid]
        if s["needs_more"] and s["question"]:  # a reply to "please tell me more"
            s["additions"].append(message.strip())
        else:  # a new question
            s["question"], s["additions"] = message.strip(), []
        text = s["question"] + ("".join(f"\nThông tin bổ sung: {a}" for a in s["additions"]))
        s["turn"] += 1
        run, parts = self.asker.ask(text, session_id=sid, turn=s["turn"])
        row = self.asker.runs.execute("SELECT final_answer, error FROM runs WHERE run_id=?", (run,)).fetchone()
        briefs = [_brief(p) for p in parts]
        s["needs_more"] = any(b.get("verdict") == "unknown" for b in briefs)
        return {"session_id": sid, "turn": s["turn"], "run_id": run, "question": text, "answer": row[0],
                "error": row[1], "needs_more": s["needs_more"], "facts": parts[0]["facts"] if parts else [],
                "false_facts": parts[0]["false_facts"] if parts else [], "parts": briefs}

    def reset(self, sid: str) -> None:
        if sid in self.sessions:
            self.sessions[sid].update(question=None, additions=[], needs_more=False)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="use the hand-encoded sample KB")
    args = ap.parse_args()
    d = Dialogue(Asker(args.sample))
    sid, last = d.new_session(), None
    print("Hỏi đáp pháp luật. Lệnh: /moi (câu hỏi mới), /trace (cây chứng minh lượt vừa rồi), /thoat\n")
    while True:
        try:
            msg = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg:
            continue
        if msg == "/thoat":
            break
        if msg == "/moi":
            d.reset(sid)
            print("(câu hỏi mới)\n")
            continue
        if msg == "/trace":
            print(show_run(d.asker.runs, last) if last else "(chưa có lượt nào)", "\n")
            continue
        out = d.say(sid, msg)
        last = out["run_id"]
        verdicts = ", ".join(p["verdict_vi"] for p in out["parts"] if p["kind"] == "case")
        print(f"\nHệ thống [{verdicts or 'tra luật'}]:\n{out['answer'] or out['error']}")
        if out["needs_more"]:
            print("\n(Hãy trả lời để bổ sung thông tin; gõ /moi để hỏi câu khác.)")
        print(f"(run {last}, lượt {out['turn']})\n")


if __name__ == "__main__":
    main()
