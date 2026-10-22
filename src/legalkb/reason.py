"""Python side of the first-order reasoner: one persistent SWI-Prolog process with the compiled KB and reasoner.pl.

    r = Reasoner()                      # data/legalkb/legal_kb.pl by default
    out = r.query(facts=["instance_of(an, nguoi_lao_dong)", ...], goal="obligation(N, an, A)")
    for a in out["answers"]: a["status"], a["goal"], a["missing"], a["presumed_absent"], a["proof"]

Facts and the goal are Prolog terms written as text (the semantic parser produces them); variables in the goal
are what the question asks for.
"""

from __future__ import annotations

import atexit
import json
import subprocess
import threading
from pathlib import Path

from .compile import PL_FILE, SWIPL

REASONER_PL = Path(__file__).with_name("reasoner.pl")


class ReasonerError(RuntimeError):
    pass


class Reasoner:
    def __init__(self, kb: Path = PL_FILE) -> None:
        self.proc = subprocess.Popen(
            [str(SWIPL), "-q", "-f", "none", "-g", f"consult('{Path(kb).as_posix()}')", "-g", "serve", "-t", "halt",
             str(REASONER_PL)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", bufsize=1)
        self.lock = threading.Lock()
        atexit.register(self.close)

    def query(self, facts: list[str], goal: str, false_facts: list[str] = (), max_missing: int = 2,
              limit: int = 50, allowed: list[str] | None = None) -> dict:
        """allowed: the norms the proofs may use (step 2 candidates); None: every norm of the KB."""
        allow = "all" if allowed is None else "[" + ", ".join("'" + n.replace("'", "\\'") + "'" for n in allowed) + "]"
        req = f"q([{', '.join(facts)}], [{', '.join(false_facts)}], ({goal}), {max_missing}, {limit}, {allow}).\n"
        with self.lock:
            self.proc.stdin.write(req)
            self.proc.stdin.flush()
            out, err = None, None
            while True:
                ln = self.proc.stdout.readline()
                if not ln:
                    raise ReasonerError("SWI-Prolog terminated (syntax error in a fact or the goal?)")
                ln = ln.strip()
                if ln == "END":
                    break
                if ln.startswith("ERROR"):
                    err = ln
                elif ln.startswith("{"):
                    out = json.loads(ln)
        if err:
            raise ReasonerError(err)
        return out

    def close(self) -> None:
        try:
            if self.proc.poll() is None:
                self.proc.stdin.close()
                self.proc.wait(timeout=5)
        except Exception:  # noqa: BLE001
            self.proc.kill()


def render(answer: dict, indent: int = 0) -> str:
    """Proof tree as indented text: rule steps with their norm, facts, missing facts, presumptions."""
    def walk(n, d):
        mark = {"rule": f"[{n.get('norm')}]", "fact": "[sự kiện]", "missing": "[THIẾU – cần hỏi]",
                "presumed_absent": "[giả định không có]"}.get(n.get("kind"), "")
        yield "  " * d + f"{n['goal']} {mark}"
        for c in n.get("children", []):
            yield from walk(c, d + 1)
    head = f"{answer['status'].upper()}: {answer['goal']}"
    if answer["missing"]:
        head += f"\n  cần biết thêm: {', '.join(answer['missing'])}"
    if answer["presumed_absent"]:
        head += f"\n  với điều kiện không có: {', '.join(answer['presumed_absent'])}"
    return head + "\n" + "\n".join(walk(answer["proof"], indent + 1))
