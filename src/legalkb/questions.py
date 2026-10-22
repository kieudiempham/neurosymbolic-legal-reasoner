"""Question types and how each is answered.

Case questions are goals for the reasoner (an answer is certain, conditional with the facts to ask for, or absent);
law questions read the norms themselves from the database (who must do something, under which conditions, with
which exceptions, what a term means, which documents are in force). The semantic parser chooses a type and fills
its slots; `answer` does the rest.

slots: subject (case entity), pred (predicate of the action / status / term), args (its other arguments, None for
unknown), attr (computed attribute), negated (status questions: "không thuộc diện ...").
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .compile import predicate_links

MODAL = {"obligation": "obligation", "right": "right", "prohibition": "prohibited", "procedure": "procedure"}

QUESTION_TYPES = {
    # case questions (reasoner)
    "yes_no": "X có phải / được / bị cấm làm A không?",
    "status": "X có thuộc diện / được hưởng / được miễn ... không?",
    "list_norms": "X phải / được / bị cấm làm những gì?",
    "amount": "X phải đóng / được hưởng bao nhiêu?",
    "deadline": "X phải làm A trong thời hạn nào?",
    "sanction": "X vi phạm thì bị xử lý thế nào?",
    # law questions (database)
    "who": "Ai phải / được / bị cấm làm A?",
    "conditions": "Điều kiện để thuộc diện / được hưởng C là gì?",
    "exceptions": "Trường hợp nào không phải làm A / không thuộc diện C?",
    "definition": "C là gì / được hiểu thế nào?",
    "validity": "Văn bản nào thay thế / sửa đổi / hướng dẫn văn bản D?",
}


@dataclass
class Question:
    type: str
    subject: str | None = None
    modality: str | None = None          # obligation / right / prohibition / procedure (yes_no, list_norms, who)
    pred: str | None = None
    args: list[str | None] = field(default_factory=list)
    attr: str | None = None
    negated: bool = False
    document: str | None = None          # validity


def _term(x: str | None, var: str) -> str:
    return var if x is None else (x if x[:1].isupper() else f"'{x}'")


def goal(q: Question) -> str:
    """Prolog goal of a case question (variables are what the question asks for)."""
    s = q.subject
    if q.type in ("yes_no", "list_norms", "deadline"):
        modals = [MODAL[q.modality]] if q.modality else ["obligation", "right", "prohibited"]
        act = f"'{q.pred}'({', '.join([s] + [_term(a, f'A{i}') for i, a in enumerate(q.args)])})" if q.pred else "Act"
        g = " ; ".join(f"{m}(N, {s}, {act})" for m in modals)
        return f"({g}), deadline(N, Amount, Unit, From)" if q.type == "deadline" else g
    if q.type == "status":
        atom = f"'{q.pred}'({', '.join([s] + [_term(a, f'A{i}') for i, a in enumerate(q.args)])})"
        return f"neg({atom})" if q.negated else atom
    if q.type == "amount":
        return f"computed(N, {s}, {_term(q.attr, 'Attr')}, Value)"
    if q.type == "sanction":
        return f"sanction(N, {s}, Kind, Min, Max, Unit)"
    raise ValueError(f"not a case question: {q.type}")


def describe_norm(con, nid: str) -> dict:
    """A norm in readable form: source text, holder, conditions, head, exceptions."""
    unit, modality, subj, bearer, apred, aargs, cpred, cargs, cneg, quote = con.execute(
        "SELECT unit_id, modality, subject_var, bearer_var, action_pred, action_args, conclusion_pred, "
        "conclusion_args, conclusion_negated, quote FROM norms WHERE norm_id=?", (nid,)).fetchone()
    types = dict(con.execute("SELECT var, type FROM norm_variables WHERE norm_id=?", (nid,)))
    conds = []
    for g, o, kind, pred, args, neg, attr, of, op, num, txt, unit_c, vattr, vof in con.execute(
            "SELECT alt_group, alt_option, kind, pred, args, negated, attr, of_var, op, value_num, value_text, unit, "
            "value_attr, value_of FROM norm_conditions WHERE norm_id=? ORDER BY cond_id", (nid,)):
        if kind == "atom":
            c = f"{'không ' if neg else ''}{pred}({args})"
        else:
            rhs = f"{vattr}({vof})" if vattr else (f"{num:g} {unit_c or ''}".strip() if num is not None else txt)
            c = f"{attr}({of}) {op} {rhs}"
        conds.append(c if not g else f"[hoặc nhóm {g}, phương án {o}] {c}")
    text = con.execute("SELECT text FROM units WHERE unit_id=?", (unit,)).fetchone()
    exceptions = [e for (e,) in con.execute(
        "SELECT norm_id FROM norm_references WHERE ref_kind='exception_of' AND target_norm_id=? UNION "
        "SELECT target_norm_id FROM norm_references WHERE ref_kind='has_exception' AND norm_id=? "
        "AND target_norm_id IS NOT NULL", (nid, nid))]
    holder = bearer or subj
    head = f"{apred}({aargs})" if apred else f"{'không ' if cneg else ''}{cpred}({cargs})"
    return {"norm": nid, "unit": unit, "modality": modality, "holder": f"{holder}: {types.get(holder, '?')}",
            "conditions": conds, "head": head, "exceptions": exceptions, "text": " ".join((text or [""])[0].split()),
            "quote": quote}


def law_answer(con, q: Question) -> list[dict]:
    if q.type == "validity":
        rows = con.execute("SELECT src_number, rel_type, dst_number FROM doc_relations WHERE src_number=? OR "
                           "dst_number=?", (q.document, q.document)).fetchall()
        return [{"from": a, "relation": r, "to": b} for a, r, b in rows]
    alias, _, _ = predicate_links(con)
    canon = alias.get(q.pred, q.pred)
    names = [n for n in {q.pred, canon, *[a for a, b in alias.items() if b == canon]} if n]
    marks = ",".join("?" * len(names))
    if q.type in ("who", "conditions"):
        modal = f" AND modality='{q.modality}'" if q.modality and q.type == "who" else ""
        ids = [n for (n,) in con.execute(
            f"SELECT norm_id FROM norms WHERE (action_pred IN ({marks}) OR (conclusion_pred IN ({marks}) "
            f"AND COALESCE(conclusion_negated, 0) = 0)){modal}", names + names)]
    elif q.type == "exceptions":
        ids = [n for (n,) in con.execute(  # norms concluding the negation, and exceptions of the norms about it
            f"SELECT norm_id FROM norms WHERE conclusion_pred IN ({marks}) AND conclusion_negated = 1", names)]
        for (n,) in con.execute(f"SELECT norm_id FROM norms WHERE action_pred IN ({marks}) OR conclusion_pred "
                                f"IN ({marks})", names + names).fetchall():
            ids += [e for (e,) in con.execute("SELECT norm_id FROM norm_references WHERE ref_kind='exception_of' "
                                              "AND target_norm_id=?", (n,))]
        ids = sorted(set(ids))
    elif q.type == "definition":
        ids = [n for (n,) in con.execute(
            f"SELECT norm_id FROM norms WHERE modality='definition' AND conclusion_pred IN ({marks})", names)]
    else:
        raise ValueError(f"not a law question: {q.type}")
    return [describe_norm(con, n) for n in ids]


EXPLORE_MISSING = 4  # when no proof exists: how many missing facts the exploring proofs may assume


def answer(q: Question, facts: list[str], reasoner, con, false_facts: list[str] = (), on: str | None = None,
           retrieval: bool = True, drop: set[str] = frozenset(), add: set[str] = frozenset()) -> dict:
    """on: the date the question is about (ISO); norms not in force then are not candidates.
    drop: norms removed from the candidates (fault injection of a retrieval omission); add: norms added to them
    (repair after the diagnosis blamed step 2)."""
    from .retrieve import candidates

    if q.type in ("who", "conditions", "exceptions", "definition", "validity"):
        return {"type": q.type, "kind": "law", "norms": law_answer(con, q)}
    retrieved = {n: w for n, w in candidates(con, q, on).items() if n not in drop} if retrieval else {}
    retrieved.update({n: "thêm lại sau chẩn đoán (bước chọn luật đã bỏ sót)" for n in add})
    allowed = list(retrieved) if retrieval else None
    answers = reasoner.query(facts, goal(q), list(false_facts), allowed=allowed)["answers"]
    contrary = []
    if q.type == "status" and not any(a["status"] == "certain" for a in answers):
        # "is X in scope?" -> also look for a proof of the opposite (an exclusion), which makes the answer "no"
        flipped = Question(**{**q.__dict__, "negated": not q.negated})
        contrary = reasoner.query(facts, goal(flipped), list(false_facts), allowed=allowed)["answers"]
    explore = []
    if not answers and not contrary:
        # no proof at all: proofs that may assume more missing facts show what the answer would have needed,
        # so the diagnosis still has components (a parser error that kills every proof is not silent)
        explore = reasoner.query(facts, goal(q), list(false_facts), max_missing=EXPLORE_MISSING,
                                 allowed=allowed)["answers"]
    for a in answers + contrary + explore:  # the norms a proof uses, with their text, are the legal basis
        used, stack = [], [a["proof"]]
        while stack:
            n = stack.pop()
            if n.get("norm") and n["norm"] != "derived" and n["norm"] not in used:
                used.append(n["norm"])
            stack += n.get("children", [])
        a["basis"] = [describe_norm(con, u) for u in used if con.execute(
            "SELECT 1 FROM norms WHERE norm_id=?", (u,)).fetchone()]
    if any(a["status"] == "certain" for a in answers):
        verdict = "yes"
    elif any(a["status"] == "certain" for a in contrary):
        verdict = "no"           # the opposite is proved
    elif answers or contrary:
        verdict = "unknown"      # provable only with facts the case does not give: ask
    else:
        verdict = "no"           # no norm leads to it
    return {"type": q.type, "kind": "case", "goal": goal(q), "verdict": verdict, "answers": answers,
            "contrary": contrary, "explore": explore, "retrieved": retrieved}
