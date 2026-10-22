"""Validation and compilation of the relational KB into a first-order Prolog program.

Generated program (data/legalkb/legal_kb.pl):
  document/5, doc_relation/3, unit/5, subtype/2      metadata, structure, ontology
  norm/3, norm_valid/3, deadline/4, exception_of/2   per-norm metadata and links
  obligation(N, Bearer, Action), right(N, Holder, Action), prohibited(N, Bearer, Action), procedure(N, Subject, Action)
  holds(N, Conclusion) and the conclusion itself       for definitions / consequences
  sanction(N, Subject, Kind, Min, Max, Unit)
  applies(N, Subject)                                 the norm's conditions hold for its subject
  defeated(N, Subject)                                an exception of N applies to the same subject
Case facts use: instance_of(X, Type), attr(X, Name, Value), and the relation predicates of the ontology.
"""

from __future__ import annotations

import re
import subprocess
from collections import defaultdict
from pathlib import Path

from .db import ROOT
from .normalize import canon_unit

PL_FILE = ROOT / "data" / "legalkb" / "legal_kb.pl"
SWIPL = ROOT / ".tools" / "swipl" / "bin" / "swipl.exe"
_OPS = {"<": "<", "<=": "=<", "=": "=:=", ">=": ">=", ">": ">", "!=": "=\\="}


def q(atom: str | None) -> str:
    """Prolog constant (always quoted); missing values become none."""
    if atom is None:
        return "none"
    return "'" + str(atom).replace("\\", "\\\\").replace("'", "\\'") + "'"


def term(x: str, variables: set[str]) -> str:
    x = x.strip()
    if x in variables or re.fullmatch(r"[A-Z][A-Za-z0-9_]*", x):
        return x
    if re.fullmatch(r"-?\d+(\.\d+)?", x):
        return x
    return q(x)


_ALIAS: dict[str, str] = {}  # predicate -> canonical predicate (predicate_links rel 'same'), set by build_program


def atom(pred: str, args: str | None, variables: set[str]) -> str:
    pred = _ALIAS.get(pred, pred)
    a = [s for s in (args or "").split(",") if s.strip()]
    return f"{q(pred)}({', '.join(term(s, variables) for s in a)})" if a else q(pred)


def compile_norm(con, nid: str) -> tuple[list[str], list[str]]:
    """Clauses of one norm, and validation problems."""
    (unit, modality, subj, bearer, benef, apred, aargs, cpred, cargs, cneg) = con.execute(
        "SELECT unit_id, modality, subject_var, bearer_var, beneficiary_var, action_pred, action_args, conclusion_pred, "
        "conclusion_args, conclusion_negated FROM norms WHERE norm_id=?", (nid,)).fetchone()
    variables = {v: t for v, t in con.execute("SELECT var, type FROM norm_variables WHERE norm_id=?", (nid,))}
    vs = set(variables)
    problems = []
    body = [f"is_a({v}, {q(t)})" for v, t in variables.items()]
    groups: dict[int, dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))
    used = set(variables)
    for i, (g, o, kind, pred, args, neg, attr, of, op, num, txt, unit_c, vattr, vof) in enumerate(con.execute(
            "SELECT alt_group, alt_option, kind, pred, args, negated, attr, of_var, op, value_num, value_text, unit, "
            "value_attr, value_of FROM norm_conditions WHERE norm_id=? ORDER BY cond_id", (nid,))):
        if kind == "atom":
            if not pred:
                problems.append("atom condition without predicate")
                continue
            if not con.execute("SELECT 1 FROM predicates WHERE name=?", (pred,)).fetchone():
                problems.append(f"undeclared predicate {pred}")
            lit = atom(pred, args, vs)
            lit = f"\\+ {lit}" if neg else lit
            used |= {a.strip() for a in (args or "").split(",") if a.strip() in vs}
        else:
            attr = attr or (canon_unit(unit_c)[0] if unit_c in ("tuổi", "tuoi") else None)  # "từ đủ 15 tuổi" -> tuoi
            if not attr or not of or not op:
                problems.append("incomplete comparison")
                continue
            x, y = f"X{i}", f"Y{i}"  # fresh per condition: two comparisons must not share a value variable
            if vattr:  # attribute vs attribute (or a legal parameter: value_of = tham_so)
                if not vof:
                    problems.append("comparison with value_attr but no value_of")
                    continue
                f = 1 if num is None else num
                rhs = y if f == 1 else f"{f:g} * {y}"
                lit = (f"attr({term(of, vs)}, {q(attr)}, {x}), attr({term(vof, vs)}, {q(vattr)}, {y}), "
                       f"number({x}), number({y}), {x} {_OPS[op]} {rhs}")
            elif num is not None:
                lit = f"attr({term(of, vs)}, {q(attr)}, {x}), number({x}), {x} {_OPS[op]} {num:g}"
            else:
                rel = "==" if op == "=" else "\\=="
                lit = f"attr({term(of, vs)}, {q(attr)}, {x}), {x} {rel} {q(txt)}"
            lit = f"\\+ ({lit})" if neg else lit
        groups[g][o].append(lit)
    body += [lit for lits in groups.pop(0, {}).values() for lit in lits]  # mandatory conditions
    for g, options in sorted(groups.items()):
        body.append("(" + " ; ".join("(" + ", ".join(lits) + ")" for _, lits in sorted(options.items())) + ")")
    s = term(subj or next(iter(vs), "S"), vs)
    if subj and subj not in vs:
        problems.append(f"subject {subj} not declared")
    cond = ", ".join(body) or "true"
    clauses = [f"applies({q(nid)}, {s}) :- {cond}."]
    guard = f"\\+ defeated({q(nid)}, {s})"
    head_vars = set()
    if modality in ("obligation", "right", "prohibition", "procedure"):
        if not apred:
            problems.append(f"{modality} without action")
        else:
            act = atom(apred, aargs, vs)
            head_vars = {a.strip() for a in (aargs or "").split(",") if a.strip() in vs}
            holder = term(bearer or subj or "S", vs)
            name = {"obligation": "obligation", "right": "right", "prohibition": "prohibited", "procedure": "procedure"}[modality]
            clauses.append(f"{name}({q(nid)}, {holder}, {act}) :- applies({q(nid)}, {s}), {guard}.")
            head_vars |= {x for x in (bearer, subj) if x}
    elif modality in ("definition", "consequence"):
        if not cpred:
            problems.append(f"{modality} without conclusion")
        else:
            c = atom(cpred, cargs, vs)
            c = f"neg({c})" if cneg else c
            head_vars = {a.strip() for a in (cargs or "").split(",") if a.strip() in vs}
            clauses.append(f"holds({q(nid)}, {c}) :- applies({q(nid)}, {s}), {guard}.")
            clauses.append(f"{c} :- holds({q(nid)}, {c}).")
    elif modality == "sanction":
        row = con.execute("SELECT kind, min_amount, max_amount, unit FROM norm_sanctions WHERE norm_id=?", (nid,)).fetchone()
        if row:
            k, mn, mx, u = row
            clauses.append(f"sanction({q(nid)}, {s}, {q(k)}, {mn if mn is not None else 'none'}, "
                           f"{mx if mx is not None else 'none'}, {q(u)}) :- applies({q(nid)}, {s}), {guard}.")
        else:
            problems.append("sanction without amounts")
    for v in head_vars - vs:
        problems.append(f"head variable {v} not declared")
    for tgt, of, expr, u in con.execute("SELECT target_attr, of_var, expression, unit FROM norm_formulas WHERE norm_id=?", (nid,)):
        names = sorted(set(re.findall(r"[a-z_][a-z0-9_]*", expr)))
        reads = ", ".join(f"attr({term(of, vs)}, {q(n)}, V_{n})" for n in names)
        e = re.sub(r"[a-z_][a-z0-9_]*", lambda m: f"V_{m.group(0)}", expr)
        body_f = ", ".join(x for x in (f"applies({q(nid)}, {s})", reads, f"V is {e}") if x)
        clauses.append(f"computed({q(nid)}, {term(of, vs)}, {q(tgt)}, V) :- {body_f}.")
    return clauses, problems


def norm_dependencies(con, alias: dict[str, str]) -> dict[str, set[str]]:
    """Predicate dependency graph of the norms: condition predicate -> conclusion predicate, or -> 'mode:action'
    for a deontic norm (the node a bridge rule with that src_mode reads)."""
    edges: dict[str, set[str]] = defaultdict(set)
    heads = {}
    for nid, modality, apred, cpred, cneg in con.execute(
            "SELECT norm_id, modality, action_pred, conclusion_pred, conclusion_negated FROM norms"):
        if cpred:  # a negated conclusion is a neg/1 fact, a different node
            heads[nid] = ("neg:" if cneg else "") + alias.get(cpred, cpred)
        elif apred:
            heads[nid] = f"{modality}:{alias.get(apred, apred)}"
    for nid, pred in con.execute("SELECT norm_id, pred FROM norm_conditions WHERE kind='atom' AND pred IS NOT NULL"):
        if nid in heads:
            edges[alias.get(pred, pred)].add(heads[nid])
    return edges


def dependency_cycles(edges: dict[str, set[str]]) -> list[list[str]]:
    """Cycles of the dependency graph (one per strongly connected component), reported by validation:
    a cycle makes Prolog's depth-first search loop."""
    index, low, stack, on, out, n = {}, {}, [], set(), [], [0]

    def visit(v):
        index[v] = low[v] = n[0]
        n[0] += 1
        stack.append(v)
        on.add(v)
        for w in edges.get(v, ()):
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1 or v in edges.get(v, ()):
                out.append(sorted(comp))

    for v in list(edges):
        if v not in index:
            visit(v)
    return out


def predicate_links(con) -> tuple[dict[str, str], list[str], list[str]]:
    """Aliases (rel 'same', resolved transitively) and bridge clauses (rel 'implies'); implies-links that would close
    a cycle are skipped, so the program cannot loop through bridge rules."""
    parent: dict[str, str] = {}

    def find(x):
        while parent.get(x, x) != x:
            x = parent[x]
        return x

    for src, dst in con.execute("SELECT src, dst FROM predicate_links WHERE rel='same' ORDER BY rowid"):
        a, b = find(src), find(dst)
        if a != b:
            parent[a] = b  # dst is the earlier, already used predicate
    alias = {x: find(x) for x in parent}
    arity = dict(con.execute("SELECT name, arity FROM predicates"))
    edges = norm_dependencies(con, alias)

    def reaches(a, b):
        stack, seen = [a], {a}
        while stack:
            n = stack.pop()
            if n == b:
                return True
            for m in edges[n] - seen:
                seen.add(m)
                stack.append(m)
        return False

    clauses, problems = [], []
    for src, mode, dst, amap in con.execute(
            "SELECT src, src_mode, dst, arg_map FROM predicate_links WHERE rel='implies' ORDER BY rowid").fetchall():
        src, dst = alias.get(src, src), alias.get(dst, dst)
        if src not in arity or dst not in arity:
            problems.append(f"link {src}->{dst}: undeclared predicate")
            continue
        m = [int(i) for i in amap.split(",") if i.strip()] if amap else list(range(arity[dst]))
        if len(m) != arity[dst] or any(i >= arity[src] for i in m):
            problems.append(f"link {src}->{dst}: bad argument map {amap}")
            continue
        premise = src if mode == "holds" else f"{mode}:{src}"
        if reaches(dst, premise):
            problems.append(f"link {premise}->{dst}: skipped, would close a cycle with the norms")
            continue
        edges[premise].add(dst)
        a = [f"A{i}" if i in m else f"_A{i}" for i in range(arity[src])]
        src_atom = f"{q(src)}({', '.join(a)})" if a else q(src)
        dst_atom = f"{q(dst)}({', '.join(f'A{i}' for i in m)})" if m else q(dst)
        head = {"prohibition": "prohibited"}.get(mode, mode)
        body = src_atom if mode == "holds" else f"{head}(_, _, {src_atom})"
        clauses.append(f"{dst_atom} :- {body}.")
    problems += [f"dependency cycle: {' -> '.join(c)}" for c in dependency_cycles(edges)]
    return alias, clauses, problems


def build_program(con) -> tuple[str, dict]:
    alias, bridges, link_problems = predicate_links(con)
    _ALIAS.clear()
    _ALIAS.update(alias)
    out = [":- style_check(-discontiguous).",  # conclusion predicates are spread over many norms
           ":- dynamic instance_of/2, attr/3, neg/1.",
           "is_a(X, T) :- instance_of(X, T0), subtype_star(T0, T).",
           "subtype_star(T, T).", "subtype_star(A, C) :- subtype(A, B), subtype_star(B, C).",
           "defeated(N, S) :- exception_of(E, N), applies(E, S).", ""]
    for name, arity in con.execute("SELECT name, arity FROM predicates"):
        if name not in alias:
            out.append(f":- dynamic {q(name)}/{arity}.")
    out += bridges
    for row in con.execute("SELECT number, doc_type, rank, effective_from, domain FROM documents"):
        out.append(f"document({', '.join(q(x) if not isinstance(x, int) else str(x) for x in row)}).")
    for row in con.execute("SELECT src_number, rel_type, dst_number FROM doc_relations"):
        out.append(f"doc_relation({', '.join(q(x) for x in row)}).")
    for n, p in con.execute("SELECT name, parent FROM entity_types WHERE parent IS NOT NULL"):
        out.append(f"subtype({q(n)}, {q(p)}).")
    stats = defaultdict(int)
    problems = {}
    for (nid, unit, modality, vf, vt) in con.execute(
            "SELECT n.norm_id, n.unit_id, n.modality, COALESCE(n.valid_from, d.effective_from), n.valid_to "
            "FROM norms n JOIN units u ON u.unit_id = n.unit_id JOIN documents d ON d.number = u.doc_number").fetchall():
        out.append(f"norm({q(nid)}, {q(modality)}, {q(unit)}).")
        out.append(f"norm_valid({q(nid)}, {q(vf)}, {q(vt)}).")
        for amount, u, ev in con.execute("SELECT amount, unit, from_event FROM norm_deadlines WHERE norm_id=?", (nid,)):
            out.append(f"deadline({q(nid)}, {amount:g}, {q(u)}, {q(ev)}).")
        clauses, probs = compile_norm(con, nid)
        out += clauses
        if probs:
            problems[nid] = probs
        stats[modality] += 1
    pairs = set()  # (exception, norm); both directions of the link give the same fact
    for nid, kind, tgt in con.execute("SELECT norm_id, ref_kind, target_norm_id FROM norm_references "
                                      "WHERE target_norm_id IS NOT NULL AND ref_kind IN ('has_exception','exception_of')"):
        pairs.add((tgt, nid) if kind == "has_exception" else (nid, tgt))
    out += [f"exception_of({q(e)}, {q(n)})." for e, n in sorted(pairs)]
    out += ["exception_of(_, _) :- fail."]
    if link_problems:
        problems["predicate_links"] = link_problems
    return "\n".join(out) + "\n", {"norms_by_modality": dict(stats), "aliases": len(alias),
                                    "bridge_rules": len(bridges), "problems": problems}


def write_and_check(con, path: Path = PL_FILE) -> dict:
    program, report = build_program(con)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(program, encoding="utf-8")
    if SWIPL.exists():  # load the program in SWI-Prolog: syntax errors and singleton warnings are reported
        r = subprocess.run([str(SWIPL), "-q", "-g", f"consult('{path.as_posix()}'), halt", "-t", "halt(1)"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        errors = [ln for ln in (r.stderr or "").splitlines() if "ERROR" in ln]
        report["prolog_load_ok"] = r.returncode == 0 and not errors
        report["prolog_messages"] = errors[:20]
    return report
