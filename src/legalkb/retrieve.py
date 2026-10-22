"""Step 2: candidate norms of a question, read from the database (no LLM).

Starting from the norms whose head is what the question asks (the action of an obligation / right / prohibition,
a status, a computed attribute, a sanction), the set is closed over
  - the norms concluding a predicate some candidate's condition uses (through aliases and bridge links),
  - the norms a candidate's condition refers to ("đối tượng tại khoản 1 Điều 2", condition_refs),
  - the exceptions of the candidates (they can defeat them),
and norms not in force on the date of the question are dropped (the unit was replaced by an amending document,
or the document / norm is not yet in force). Each candidate keeps the reason it was selected.
The reasoner is then restricted to the candidates, so the selection is a component MBD can blame (verify.py).
"""

from __future__ import annotations

from datetime import date

from .compile import predicate_links

MODALITY = {"obligation": "obligation", "right": "right", "prohibition": "prohibition", "procedure": "procedure"}


def _names(alias: dict[str, str], pred: str) -> set[str]:
    canon = alias.get(pred, pred)
    return {pred, canon} | {a for a, b in alias.items() if b == canon}


def in_force(con, nid: str, on: str) -> bool:
    row = con.execute(
        "SELECT n.valid_from, n.valid_to, u.valid_from, u.valid_to, d.effective_from FROM norms n "
        "JOIN units u ON u.unit_id = n.unit_id JOIN documents d ON d.number = u.doc_number WHERE n.norm_id=?",
        (nid,)).fetchone()
    if not row:
        return False
    nf, nt, uf, ut, df = row
    start = max(x for x in (nf, uf, df, "0000") if x)
    end = min(x for x in (nt, ut, "9999") if x)
    return start <= on < end


def candidates(con, q, on: str | None = None) -> dict[str, str]:
    """norm id -> why it was selected, for a questions.Question."""
    on = on or date.today().isoformat()
    alias, _, _ = predicate_links(con)
    seeds: dict[str, str] = {}

    def add_heads(sql: str, args: tuple, why: str):
        for (n,) in con.execute(sql, args):
            seeds.setdefault(n, why)

    if q.type in ("yes_no", "list_norms", "deadline", "who"):
        mods = [MODALITY[q.modality]] if q.modality else list(MODALITY.values())
        marks = ",".join("?" * len(mods))
        if q.pred:
            names = sorted(_names(alias, q.pred))
            add_heads(f"SELECT norm_id FROM norms WHERE modality IN ({marks}) AND action_pred IN "
                      f"({','.join('?' * len(names))})", (*mods, *names), f"hành vi được hỏi: {q.pred}")
        else:
            add_heads(f"SELECT norm_id FROM norms WHERE modality IN ({marks})", tuple(mods), "nghĩa vụ / quyền được hỏi")
    elif q.type in ("status", "conditions", "definition", "exceptions"):
        names = sorted(_names(alias, q.pred or ""))
        add_heads(f"SELECT norm_id FROM norms WHERE conclusion_pred IN ({','.join('?' * len(names))})",
                  tuple(names), f"kết luận được hỏi: {q.pred}")
    elif q.type == "amount":
        if q.attr:
            add_heads("SELECT norm_id FROM norm_formulas WHERE target_attr=?", (q.attr,), f"khoản tính: {q.attr}")
        else:
            add_heads("SELECT norm_id FROM norm_formulas", (), "khoản tính được hỏi")
    elif q.type == "sanction":
        add_heads("SELECT norm_id FROM norms WHERE modality='sanction'", (), "chế tài được hỏi")

    concluding: dict[str, list[str]] = {}
    for n, p in con.execute("SELECT norm_id, conclusion_pred FROM norms WHERE conclusion_pred IS NOT NULL"):
        concluding.setdefault(alias.get(p, p), []).append(n)
    bridges = {}  # dst predicate -> src predicates (bridge rule src => dst)
    for s, d in con.execute("SELECT src, dst FROM predicate_links WHERE rel='implies'"):
        bridges.setdefault(alias.get(d, d), []).append(alias.get(s, s))

    out, todo = dict(seeds), list(seeds)
    while todo:
        n = todo.pop()
        found: list[tuple[str, str]] = []
        for (p,) in con.execute("SELECT pred FROM norm_conditions WHERE norm_id=? AND kind='atom' AND pred IS NOT NULL",
                                (n,)):
            p = alias.get(p, p)
            for m in concluding.get(p, []):
                found.append((m, f"kết luận {p}, điều kiện của {n}"))
            for src in bridges.get(p, []):
                for m in concluding.get(src, []):
                    found.append((m, f"kết luận {src} (suy ra {p}), điều kiện của {n}"))
        for (m,) in con.execute("SELECT r.target_norm_id FROM condition_refs r JOIN norm_conditions k "
                                "ON k.cond_id = r.cond_id WHERE k.norm_id=?", (n,)):
            found.append((m, f"được dẫn chiếu trong điều kiện của {n}"))
        for (e,) in con.execute("SELECT norm_id FROM norm_references WHERE ref_kind='exception_of' AND target_norm_id=? "
                                "UNION SELECT target_norm_id FROM norm_references WHERE ref_kind='has_exception' "
                                "AND norm_id=? AND target_norm_id IS NOT NULL", (n, n)):
            found.append((e, f"ngoại lệ của {n}"))
        for m, why in found:
            if m and m not in out:
                out[m] = why
                todo.append(m)
    return {n: why for n, why in out.items() if in_force(con, n, on)}
