"""Run traces in SQLite (data/legalkb/runs.sqlite, separate from the KB): every question asked leaves its whole
reasoning, step by step, so it can be read again or compared across runs.

Tables
  runs              one row per question asked: time, text, KB used, parser model, the parser's raw output;
                    for a dataset run (batch.py) also the batch name, the item id, its gold answer and any error;
                    final_answer: the answer in words written from the run (answer_gen.py, step 5);
                    session_id / turn: the conversation a run belongs to (chat.py: a reply to a request for
                    more information is a new turn of the same session)
  run_facts         case facts read from the question (fact / false_fact) and the KB parameters used (parameter)
  run_steps         the pipeline steps of the run in order: parse, then per sub-question reason (case question)
                    or lookup (law question), with a short summary and the time each took
  run_questions     the sub-questions: type, slots, Prolog goal, verdict
  run_answers       answers of a case question (role answer / contrary: proof of the opposite) with status,
                    missing facts to ask and exceptions presumed absent
  run_proof_nodes   the proof tree of each answer, one row per node (parent_id links a node to its parent)
  run_basis         the legal basis of each answer: the units its proof uses, with their text
  run_law_norms     norms returned by a law question (who / conditions / exceptions / definition)
  run_candidates    the candidate norms step 2 selected for each case sub-question, with the reason
  MBD (step 4, verify.py), so the diagnosis can be followed step by step:
  run_mbd_components   each component: layer, kind (checked / required / presumed / rule), the atom or norm, its
                       Vietnamese statement, the premise it was measured against (question / unit of the norm),
                       the NLI label (null: below the threshold, unobserved), the three probabilities, and whether
                       it is a symptom (inconsistent with everything working normally); the negative sentence and
                       its label (pos_neg acceptance), why a label was not accepted, and the distributions of the two
                       measurements (LLM, mDeBERTa) whose mean is p_*
  run_mbd_facts        the observations and the candidate fault atoms given to mbd.pl
  run_mbd_diagnoses    every minimal diagnosis, with each fault explained in words
  runs.action / action_about   the action chosen from the diagnoses (answer / ask / confirm / warn) and the
                       components it is about
  run_answer_checks    step 5: every sentence of the answer (each attempt) labelled against the run: entail
                       (supported), neutral (not grounded), contra (contradicted), request (asks the user)
  runs.answer_faithful 1 when every checked sentence of the final answer is supported

    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.trace            # list the runs
    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.trace 12         # print run 12
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

from .db import DB_FILE

RUNS_DB = DB_FILE.with_name("runs.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  run_id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, question TEXT, kb_program TEXT, kb_database TEXT,
  parser_model TEXT, parser_output TEXT, batch TEXT, item_id TEXT, gold TEXT, error TEXT, final_answer TEXT,
  answer_model TEXT, session_id TEXT, turn INTEGER, action TEXT, action_about TEXT, answer_faithful INTEGER);
CREATE TABLE IF NOT EXISTS run_facts (
  run_id INTEGER NOT NULL REFERENCES runs(run_id), kind TEXT CHECK (kind IN ('fact','false_fact','parameter')),
  fact TEXT);
CREATE TABLE IF NOT EXISTS run_steps (
  run_id INTEGER NOT NULL REFERENCES runs(run_id), step_no INTEGER, stage TEXT CHECK (stage IN ('parse','reason','lookup','verify')),
  q_no INTEGER, summary TEXT, seconds REAL, PRIMARY KEY (run_id, step_no));
CREATE TABLE IF NOT EXISTS run_questions (
  run_id INTEGER NOT NULL REFERENCES runs(run_id), q_no INTEGER, type TEXT, kind TEXT, slots TEXT, goal TEXT,
  verdict TEXT, PRIMARY KEY (run_id, q_no));
CREATE TABLE IF NOT EXISTS run_answers (
  answer_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER NOT NULL REFERENCES runs(run_id), q_no INTEGER,
  role TEXT CHECK (role IN ('answer','contrary')), answer_no INTEGER, status TEXT, goal TEXT, missing TEXT,
  presumed_absent TEXT);
CREATE TABLE IF NOT EXISTS run_proof_nodes (
  answer_id INTEGER NOT NULL REFERENCES run_answers(answer_id), node_id INTEGER, parent_id INTEGER, depth INTEGER,
  goal TEXT, kind TEXT, norm TEXT, PRIMARY KEY (answer_id, node_id));
CREATE TABLE IF NOT EXISTS run_basis (
  answer_id INTEGER NOT NULL REFERENCES run_answers(answer_id), unit TEXT, norm TEXT, text TEXT);
CREATE TABLE IF NOT EXISTS run_candidates (
  run_id INTEGER NOT NULL REFERENCES runs(run_id), q_no INTEGER, norm TEXT, reason TEXT);
CREATE TABLE IF NOT EXISTS run_mbd_components (
  run_id INTEGER NOT NULL REFERENCES runs(run_id), comp_id TEXT, layer TEXT, kind TEXT, item TEXT, statement TEXT,
  premise TEXT, label TEXT, p_entail REAL, p_neutral REAL, p_contra REAL, symptom INTEGER, neg_statement TEXT,
  neg_label TEXT, reject_reason TEXT, p_llm TEXT, p_mdeberta TEXT, PRIMARY KEY (run_id, comp_id));
CREATE TABLE IF NOT EXISTS run_mbd_facts (
  run_id INTEGER NOT NULL REFERENCES runs(run_id), kind TEXT CHECK (kind IN ('observation','candidate')), term TEXT);
CREATE TABLE IF NOT EXISTS run_mbd_diagnoses (
  run_id INTEGER NOT NULL REFERENCES runs(run_id), diag_no INTEGER, size INTEGER, faults TEXT, explanation TEXT,
  PRIMARY KEY (run_id, diag_no));
CREATE TABLE IF NOT EXISTS run_answer_checks (
  run_id INTEGER NOT NULL REFERENCES runs(run_id), attempt INTEGER, sent_no INTEGER, sentence TEXT, label TEXT,
  p_entail REAL, p_neutral REAL, p_contra REAL);
CREATE TABLE IF NOT EXISTS run_law_norms (
  run_id INTEGER NOT NULL REFERENCES runs(run_id), q_no INTEGER, norm TEXT, unit TEXT, modality TEXT, holder TEXT,
  conditions TEXT, head TEXT, exceptions TEXT, text TEXT);
"""


def connect_runs(path: Path = RUNS_DB) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    have = {r[1] for r in con.execute("PRAGMA table_info(runs)")}
    for col in ("batch", "item_id", "gold", "error", "final_answer", "answer_model", "session_id", "turn",
                "action", "action_about", "answer_faithful"):
        if col not in have:
            con.execute(f"ALTER TABLE runs ADD COLUMN {col} TEXT")
    sql = con.execute("SELECT sql FROM sqlite_master WHERE name='run_steps'").fetchone()[0]
    if "'verify'" not in sql:  # older databases: allow the verify step (SQLite cannot alter a CHECK in place)
        con.executescript("ALTER TABLE run_steps RENAME TO run_steps_old;" + SCHEMA +
                          "INSERT INTO run_steps SELECT * FROM run_steps_old; DROP TABLE run_steps_old;")
    have = {r[1] for r in con.execute("PRAGMA table_info(run_mbd_components)")}
    for col in ("neg_statement", "neg_label", "reject_reason", "p_llm", "p_mdeberta"):
        if col not in have:
            con.execute(f"ALTER TABLE run_mbd_components ADD COLUMN {col} TEXT")
    con.execute("CREATE INDEX IF NOT EXISTS ix_runs_batch ON runs(batch, item_id)")
    return con


def save_run(con, *, time: str, question: str, kb_program: str, kb_database: str, parser_model: str,
             parser_output: dict, facts: list[str], false_facts: list[str], parameters: list[str],
             parse_seconds: float, parts: list[dict], batch: str | None = None, item_id: str | None = None,
             gold: str | None = None, error: str | None = None, session_id: str | None = None,
             turn: int | None = None, mbd: dict | None = None, mbd_seconds: float = 0.0) -> int:
    """parts: one per sub-question, as returned by questions.answer plus 'parsed' (slots) and 'seconds'."""
    cur = con.execute("INSERT INTO runs (time, question, kb_program, kb_database, parser_model, parser_output, batch, "
                      "item_id, gold, error, session_id, turn) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                      (time, question, kb_program, kb_database, parser_model,
                       json.dumps(parser_output, ensure_ascii=False), batch, item_id, gold, error, session_id, turn))
    run = cur.lastrowid
    con.executemany("INSERT INTO run_facts VALUES (?,?,?)",
                    [(run, "fact", f) for f in facts] + [(run, "false_fact", f) for f in false_facts]
                    + [(run, "parameter", p) for p in parameters])
    if parser_output is not None:
        con.execute("INSERT INTO run_steps VALUES (?,?,?,?,?,?)",
                    (run, 1, "parse", None, f"{len(facts)} facts, {len(false_facts)} false facts, {len(parts)} "
                                           f"sub-questions", round(parse_seconds, 3)))
    for q_no, p in enumerate(parts, 1):
        law = p["kind"] == "law"
        con.execute("INSERT INTO run_questions VALUES (?,?,?,?,?,?,?)",
                    (run, q_no, p["type"], p["kind"], json.dumps(p["parsed"], ensure_ascii=False), p.get("goal"),
                     p.get("verdict")))
        summary = (f"{len(p['norms'])} norms" if law else
                   f"verdict {p['verdict']}, {len(p['answers'])} answers, {len(p.get('contrary', []))} contrary")
        con.execute("INSERT INTO run_steps VALUES (?,?,?,?,?,?)",
                    (run, q_no + 1, "lookup" if law else "reason", q_no, summary, round(p.get("seconds", 0), 3)))
        if law:
            con.executemany("INSERT INTO run_law_norms VALUES (?,?,?,?,?,?,?,?,?,?)", [
                (run, q_no, n["norm"], n["unit"], n["modality"], n["holder"], " AND ".join(n["conditions"]),
                 n["head"], ", ".join(n["exceptions"]), n["text"]) for n in p["norms"]])
            continue
        con.executemany("INSERT INTO run_candidates VALUES (?,?,?,?)",
                        [(run, q_no, n, why) for n, why in p.get("retrieved", {}).items()])
        for role, answers in (("answer", p["answers"]), ("contrary", p.get("contrary", []))):
            for a_no, a in enumerate(answers, 1):
                aid = con.execute(
                    "INSERT INTO run_answers (run_id, q_no, role, answer_no, status, goal, missing, presumed_absent) "
                    "VALUES (?,?,?,?,?,?,?,?)", (run, q_no, role, a_no, a["status"], a["goal"],
                                                 "; ".join(a["missing"]), "; ".join(a["presumed_absent"]))).lastrowid
                nodes, stack = [], [(a["proof"], None, 0)]
                while stack:  # depth-first, children in order
                    n, parent, depth = stack.pop()
                    nid = len(nodes) + 1
                    nodes.append((aid, nid, parent, depth, n["goal"], n.get("kind"), n.get("norm")))
                    stack += [(c, nid, depth + 1) for c in reversed(n.get("children", []))]
                con.executemany("INSERT INTO run_proof_nodes VALUES (?,?,?,?,?,?,?)", nodes)
                con.executemany("INSERT INTO run_basis VALUES (?,?,?,?)",
                                [(aid, b["unit"], b["norm"], b["text"]) for b in a["basis"]])
    if mbd is not None:
        from .verify import explain

        step = 2 + len(parts)
        con.execute("INSERT INTO run_steps VALUES (?,?,?,?,?,?)",
                    (run, step, "verify", None, f"{len(mbd['components'])} components, {len(mbd['symptoms'])} "
                                               f"symptoms, {len(mbd['diagnoses'])} minimal diagnoses, action "
                                               f"{mbd['action']}", round(mbd_seconds, 3)))
        con.executemany(
            "INSERT INTO run_mbd_components (run_id, comp_id, layer, kind, item, statement, premise, label, p_entail, "
            "p_neutral, p_contra, symptom, neg_statement, neg_label, reject_reason, p_llm, p_mdeberta) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
                (run, c["id"], c["layer"], c["kind"], c["item"], c["statement"], c["premise"], c["label"],
                 c.get("p_entail"), c.get("p_neutral"), c.get("p_contra"), int(bool(c.get("symptom"))),
                 c.get("neg_statement"), c.get("neg_label"), c.get("reject_reason"),
                 json.dumps(c.get("p_llm")), json.dumps(c.get("p_mdeberta"))) for c in mbd["components"]])
        con.executemany("INSERT INTO run_mbd_facts VALUES (?,?,?)",
                        [(run, "observation", o) for o in mbd["observations"]]
                        + [(run, "candidate", f) for f in mbd["candidates"]])
        con.executemany("INSERT INTO run_mbd_diagnoses VALUES (?,?,?,?,?)", [
            (run, i, len(d), "[" + ", ".join(d) + "]",
             "; ".join(explain(f, mbd["components"]) for f in d) or "không có lỗi (mọi thành phần bình thường)")
            for i, d in enumerate(mbd["diagnoses"], 1)])
        if mbd.get("repaired_from"):
            r = mbd["repaired_from"]
            con.execute("INSERT INTO run_steps VALUES (?,?,?,?,?,?)",
                        (run, step + 1, "verify", None, f"repair: first diagnosis {r['diagnoses']} (action "
                                                        f"{r['action']}), norms added to the candidates "
                                                        f"{r['added_norms']}, reasoned and diagnosed again", 0))
        con.execute("UPDATE runs SET action=?, action_about=? WHERE run_id=?",
                    (mbd["action"], json.dumps(mbd["about"]), run))
    con.commit()
    return run


def show_run(con, run: int) -> str:
    """A run read back from the database, as indented text."""
    r = con.execute("SELECT time, question, kb_program, parser_model, batch, item_id, gold, error, final_answer "
                    "FROM runs WHERE run_id=?", (run,)).fetchone()
    if not r:
        return f"no run {run}"
    out = [f"run {run}  {r[0]}  KB {r[2]}  parser {r[3]}"
           + (f"  batch {r[4]} câu {r[5]} (đáp án đúng: {r[6]})" if r[4] else ""), f"CÂU HỎI: {r[1]}"]
    if r[7]:
        out.append(f"LỖI: {r[7]}")
    out += ["", "TRẢ LỜI:", r[8] or "(chưa sinh: python -m legalkb.answer_gen)"]
    out += ["", "bước:"]
    out += [f"  {s}. {st}{'' if q is None else f' (câu hỏi con {q})'}: {sm}  [{sec}s]" for s, st, q, sm, sec in
            con.execute("SELECT step_no, stage, q_no, summary, seconds FROM run_steps WHERE run_id=? ORDER BY step_no",
                        (run,))]
    out += ["", "dữ kiện:"] + [f"  [{k}] {f}" for k, f in con.execute(
        "SELECT kind, fact FROM run_facts WHERE run_id=? ORDER BY rowid", (run,))]
    for q_no, typ, kind, slots, goal, verdict in con.execute(
            "SELECT q_no, type, kind, slots, goal, verdict FROM run_questions WHERE run_id=? ORDER BY q_no", (run,)):
        out += ["", f"câu hỏi con {q_no}: {typ} {slots}"]
        if kind == "law":
            out += [f"  {u} ({m}) {h}: nếu {c or '-'} thì {hd}" + (f"; ngoại lệ {e}" if e else "")
                    for u, m, h, c, hd, e in con.execute(
                        "SELECT unit, modality, holder, conditions, head, exceptions FROM run_law_norms "
                        "WHERE run_id=? AND q_no=?", (run, q_no))]
            continue
        cands = con.execute("SELECT norm, reason FROM run_candidates WHERE run_id=? AND q_no=?", (run, q_no)).fetchall()
        if cands:
            out.append(f"  luật ứng viên (bước 2): " + "; ".join(f"{n} ({w})" for n, w in cands))
        out.append(f"  truy vấn {goal}  ->  {verdict}")
        for aid, role, status, g, missing, presumed in con.execute(
                "SELECT answer_id, role, status, goal, missing, presumed_absent FROM run_answers WHERE run_id=? AND "
                "q_no=? ORDER BY role, answer_no", (run, q_no)).fetchall():
            out.append(f"  [{role} {status}] {g}" + (f"  | hỏi thêm: {missing}" if missing else "")
                       + (f"  | giả định không có: {presumed}" if presumed else ""))
            out += ["      " + "    " * d + f"{gl}" + (f"   <- {norm}" if norm and norm != "derived" else f"   ({k})")
                    for d, gl, k, norm in con.execute(
                        "SELECT depth, goal, kind, norm FROM run_proof_nodes WHERE answer_id=? ORDER BY node_id",
                        (aid,))]
            out += [f"      căn cứ {u}: «{t}»" for u, t in con.execute(
                "SELECT unit, text FROM run_basis WHERE answer_id=?", (aid,))]
    comps = con.execute("SELECT comp_id, layer, kind, item, statement, premise, label, p_entail, p_neutral, "
                        "p_contra, symptom, neg_statement, neg_label, reject_reason FROM run_mbd_components "
                        "WHERE run_id=? ORDER BY rowid", (run,)).fetchall()
    if comps:
        action = con.execute("SELECT action, action_about FROM runs WHERE run_id=?", (run,)).fetchone()
        out += ["", "KIỂM TRA (MBD):", "  thành phần (nhãn NLI: entail / neutral / contra; '-' = dưới ngưỡng, "
                "không dùng làm quan sát):"]
        for cid, layer, kind, item, st, prem, lab, pe, pn, pc, sym, nst, nlab, why in comps:
            out.append(f"  {cid:4s} [{layer}/{kind}] {item}")
            out.append(f"       «{st}»  so với {'câu hỏi' if prem == 'question' else prem}: {lab or '-'} "
                       f"(e={pe:.2f} n={pn:.2f} c={pc:.2f})" + (f" [không nhận: {why}]" if why else "")
                       + ("   <- TRIỆU CHỨNG" if sym else ""))
            if nst:
                out.append(f"       phủ định «{nst}»: {nlab or '-'}")
        out.append("  quan sát đưa vào mbd.pl: " + "; ".join(t for (t,) in con.execute(
            "SELECT term FROM run_mbd_facts WHERE run_id=? AND kind='observation'", (run,))))
        out.append("  giả thuyết lỗi được xét: " + "; ".join(t for (t,) in con.execute(
            "SELECT term FROM run_mbd_facts WHERE run_id=? AND kind='candidate'", (run,))))
        out.append("  chẩn đoán tối thiểu:")
        out += [f"    {n}. {f}  ->  {e}" for n, f, e in con.execute(
            "SELECT diag_no, faults, explanation FROM run_mbd_diagnoses WHERE run_id=? ORDER BY diag_no", (run,))]
        out.append(f"  HÀNH ĐỘNG: {action[0]}  (về: {action[1]})")
    checks = con.execute("SELECT attempt, sent_no, sentence, label FROM run_answer_checks WHERE run_id=? "
                         "ORDER BY attempt, sent_no", (run,)).fetchall()
    if checks:
        out += ["", "KIỂM TRA CÂU TRẢ LỜI (bước 5):"]
        out += [f"  lần {a}, câu {k}: [{lab}] {s}" for a, k, s, lab in checks]
    return "\n".join(out)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    con = connect_runs()
    if len(sys.argv) > 1:
        print(show_run(con, int(sys.argv[1])))
        return
    for run, time, batch, item, q in con.execute(
            "SELECT run_id, time, batch, item_id, question FROM runs ORDER BY run_id"):
        print(f"{run:5d}  {time}  {(batch or '-'):12s} {(item or '-'):10s}  {q[:90]}")


if __name__ == "__main__":
    main()
