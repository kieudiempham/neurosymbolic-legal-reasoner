"""Step 4: first-order cross-layer model-based diagnosis of a run, before the answer is written.

Components are read off the proofs of the run (verify):
  checked    case facts a proof uses                  (parser output: pos)
  required   facts a conditional answer still needs   (parser output: none)
  presumed   exceptions presumed absent               (parser output: none)
  rule       norms used by a certain proof; competing pairs of norms proving opposite conclusions
  near_miss  norms step 2 did not select whose text is closest to the question (embeddings): their text is
             checked against the goal of the question (retrieval layer: a normal selection leaves out only
             norms that are not about it)
When no proof exists, the exploring proofs (more missing facts allowed) give the components, and every parsed
fact is checked, so a parser error that kills every proof is not silent.
Each is rendered in Vietnamese from the KB's fixed templates (templates.py: a positive and a negative sentence
for a fact, one sentence for a rule and for the goal), so the sentences are deterministic and auditable. They are
measured by NLI as in the paper: the mean of mDeBERTa (local) and an LLM (NLI_MODEL, by default gpt-4.1, not the
parser's model); a fact against the question (prompt v4), a rule against the lead-ins and text of its unit (law
prompt), a norm left out against the goal (about prompt, LLM only). A fact's label is accepted when the positive
sentence is confident (>= TAU) and the negative one agrees (rule pos_neg); otherwise it stays unobserved and the
reason is recorded. mbd.pl returns the minimal diagnoses, from which the action follows:
  answer   the empty diagnosis is consistent
  ask      some minimal diagnosis has only user faults (facts the question does not give): ask for them
  confirm  otherwise, some minimal diagnosis has user / parser faults only: ask the user to confirm the facts
           the parser may have read wrongly
  warn     every minimal diagnosis blames the KB: answer with a warning naming the rules
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .runtime import swipl
from .extract import CACHE
from .offline import extractor, require_online

CLIENT_MODEL = "gpt-4.1-mini"
# gpt-4.1 rather than the paper's gpt-4o-mini: on this pipeline's verbalisations gpt-4o-mini took
# "tôi ký hợp đồng lao động" to entail "the contract has no fixed term"; it is also not the parser's model
NLI_MODEL = os.environ.get("LEGALKB_NLI_MODEL", "gpt-4.1")
# calibrated on the dev split of the fault-injection benchmark (experiments/legalkb/inject_calibration.json):
# tau 0.4 and 0.5 give the same results, higher thresholds lose observations (action accuracy 0.77 -> 0.48);
# pos_neg is slightly better than pos_only (fault F1 0.471 vs 0.461)
TAU = float(os.environ.get("LEGALKB_NLI_TAU", 0.5))
ACCEPT_RULE = os.environ.get("LEGALKB_NLI_RULE", "pos_neg")   # pos_neg | pos_only
ENSEMBLE = os.environ.get("LEGALKB_NLI_ENSEMBLE", "1") == "1"  # mean with mDeBERTa (local) where it applies
MDEBERTA = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
MAX_K = 6  # bound on the size of a diagnosis (the search starts at the number of symptoms needed)
MBD_PL = Path(__file__).with_name("mbd.pl")
LAYER = {"missing": "user", "omission": "parser", "misinterp": "parser", "unsupported": "parser",
         "misencoded": "kb", "kbconflict": "kb", "omitted": "retrieval"}


# NLI prompt for a rule against its source text (the paper's v4 is written for a user question as premise)
LAW_PROMPT = (
    "Đoạn văn là một quy định pháp luật (kèm câu dẫn của khoản / điều chứa nó). Mệnh đề là một luật \"nếu ... thì "
    "...\" được mã hóa từ quy định đó.\n\nĐoạn văn:\n{premise}\n\nMệnh đề:\n{hypothesis}\n\n"
    "Mệnh đề có đúng với quy định không? Chỉ xét điều kiện, ngưỡng, đối tượng và kết luận; được diễn đạt khác "
    "cùng nghĩa; mệnh đề có thể chỉ nêu một trường hợp mà quy định áp dụng.\n"
    "A. Đúng — quy định nêu (hoặc suy ra trực tiếp) đúng như mệnh đề\n"
    "B. Không xác định — quy định không đề cập đến nội dung của mệnh đề\n"
    "C. Sai — mệnh đề khác quy định (điều kiện, ngưỡng, đối tượng hoặc kết luận khác)\n"
    "Trả lời A, B hoặc C.")


# NLI-style prompt for the retrieval layer: is a norm left out ABOUT what the question asks?
ABOUT_PROMPT = (
    "Đoạn văn là một quy định pháp luật (kèm câu dẫn của khoản / điều chứa nó). Mệnh đề nêu điều mà người hỏi muốn "
    "biết.\n\nĐoạn văn:\n{premise}\n\nMệnh đề:\n{hypothesis}\n\n"
    "Quy định này có quyết định nội dung của mệnh đề không?\n"
    "A. Có — quy định nêu khi nào (với ai, điều kiện gì) nội dung của mệnh đề là đúng\n"
    "B. Không — quy định nói về việc khác (kể cả khi chỉ dùng nội dung của mệnh đề làm điều kiện cho một việc khác)\n"
    "C. Có — quy định nêu khi nào (với ai, trường hợp nào) nội dung của mệnh đề là không đúng (loại trừ, ngoại lệ)\n"
    "Trả lời A, B hoặc C.")


def law_premise(con, unit: str) -> str:
    """The text a rule is checked against: the lead-ins of the enclosing units, then the unit itself."""
    chain, u = [], unit
    while u:
        row = con.execute("SELECT text, parent_id FROM units WHERE unit_id=?", (u,)).fetchone()
        if not row:
            break
        chain.append(" ".join((row[0] or "").split()))
        u = row[1]
    return "\n".join(reversed(chain))


def _leaves(node: dict):
    yield node
    for c in node.get("children", []):
        yield from _leaves(c)


def components(parts: list[dict], facts: list[str]) -> dict:
    """Keep parser output, proof dependencies and alternative paths as separate evidence.

    Checking only surviving proof leaves hides wrong values/polarities that killed a
    branch. Conversely, missing leaves on unused alternatives must not force an ask.
    """
    key = lambda s: s.replace(" ", "")
    atoms, rules, competing, goals, supports = {}, {}, [], [], []

    def atom_id(text, kind, polarity="pos"):
        for cid, row in atoms.items():
            if key(row["atom"]) == key(text):
                if kind == "checked":
                    row.update(kind=kind, polarity=polarity)
                return cid
        cid = f"c{len(atoms) + 1}"
        atoms[cid] = {"atom": text, "kind": kind, "polarity": polarity}
        return cid

    def rule_id(norm):
        for rid, row in rules.items():
            if row["norm"] == norm:
                return rid
        rid = f"n{len(rules) + 1}"
        rules[rid] = {"norm": norm}
        return rid

    case_parts = [p for p in parts if p["kind"] == "case"]
    if case_parts:
        for f in facts:
            if not f.startswith("attr(tham_so"):
                atom_id(f, "checked")
        for p in case_parts:
            for f in p.get("false_facts", []):
                atom_id(f, "checked", "neg")
    for p in case_parts:
        goals.append({"id": f"g{len(goals) + 1}", "question": p["parsed"], "goal": p["goal"],
                      "retrieved": p.get("retrieved", {})})
        certain = [a for role in ("answers", "contrary") for a in p.get(role, []) if a["status"] == "certain"]
        paths = certain or [a for role in ("answers", "contrary", "explore") for a in p.get(role, [])]
        # Only the shortest conditional paths are needed; keep all equal alternatives.
        if paths and not certain:
            cost = min(len(a["missing"]) for a in paths)
            paths = [a for a in paths if len(a["missing"]) == cost]
        needed_paths, heads = [], {"answers": [], "contrary": []}
        for a in paths:
            used = set()
            for m in a["missing"]:
                used.add(atom_id(m, "required"))
            for m in a["presumed_absent"]:
                atom_id(m, "presumed")
            rids = set()
            for n in _leaves(a["proof"]):
                if n.get("kind") == "fact" and not n["goal"].startswith("attr(tham_so"):
                    used.add(atom_id(n["goal"], "checked"))
                if n.get("kind") == "rule" and n.get("norm") not in (None, "derived"):
                    rids.add(rule_id(n["norm"]))
            needed_paths.append(used)
            if a["status"] == "certain":
                role = "answers" if a in p.get("answers", []) else "contrary"
                heads[role].append((rids, used))
        # A fact common to every proof is needed even if the parser invented it.
        for cid in set.intersection(*needed_paths) if needed_paths else set():
            atoms[cid]["needed"] = True
        # Explain a conflicting proof pair through its case AND rule dependencies.
        for left, lc in heads["answers"]:
            for right, rc in heads["contrary"]:
                for x in sorted(left):
                    for y in sorted(right):
                        if x != y:
                            competing.append((x, y))
                            supports.extend((x, y, c) for c in sorted(lc | rc))
    return {"atoms": atoms, "rules": rules, "competing": sorted(set(competing)),
            "supports": sorted(set(supports)), "goals": goals, "near": {}}


def near_misses(con, client, question: str, comps: dict) -> None:
    """Audit candidate closure for each goal, including dependencies and exceptions.

    Semantic similarity alone is not evidence that a norm should have been selected.
    The independent closure audit supplies that structural evidence, without an API.
    """
    from .questions import Question
    from .retrieve import candidates
    for g in comps["goals"]:
        expected = candidates(con, Question(**g["question"]))
        for n in sorted(set(expected) - set(g["retrieved"])):
            unit = con.execute("SELECT unit_id FROM norms WHERE norm_id=?", (n,)).fetchone()[0]
            comps["near"][f"r{len(comps['near']) + 1}"] = {
                "norm": n, "unit": unit, "text": law_premise(con, unit), "goal": g["id"],
                "expected": True, "selection_reason": expected[n]}


def _cached_call(name: str, payload: str, fn):
    f = CACHE / f"{name}_{hashlib.sha1(payload.encode('utf-8')).hexdigest()}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    require_online(name)
    out = fn()
    f.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def render(con, facts: list[str], comps: dict) -> dict[str, tuple[str, str]]:
    """component / goal id -> (positive sentence, negative sentence), from the templates of the KB."""
    from .templates import Renderer

    R = Renderer(con, facts)
    subj_type = R.entity_type.get("toi")
    out = {cid: R.atom(a["atom"]) for cid, a in comps["atoms"].items()}
    for nid, r in comps["rules"].items():
        unit = con.execute("SELECT unit_id FROM norms WHERE norm_id=?", (r["norm"],)).fetchone()[0]
        r.update(unit=unit, text=law_premise(con, unit))
        out[nid] = (R.rule(r["norm"]), "")
    for g in comps["goals"]:
        out[g["id"]] = (R.goal(g["question"], subj_type), "")
    return out


_MD = {}


def mdeberta(pairs: list[tuple[str, str]]) -> list[dict]:
    """mDeBERTa three-way NLI on CPU (the paper's local measurement), cached per pair."""
    out, todo = [None] * len(pairs), []
    for k, (p, h) in enumerate(pairs):
        f = CACHE / f"mdeberta_{hashlib.sha1(f'{p}|{h}'.encode('utf-8')).hexdigest()}.json"
        if f.exists():
            out[k] = json.loads(f.read_text(encoding="utf-8"))
        else:
            todo.append(k)
    if todo:
        require_online("uncached local NLI model/measurement")
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        if not _MD:
            _MD["tok"] = AutoTokenizer.from_pretrained(MDEBERTA)
            _MD["model"] = AutoModelForSequenceClassification.from_pretrained(MDEBERTA).eval()
        tok, model = _MD["tok"], _MD["model"]
        names = {"entailment": "entail", "neutral": "neutral", "contradiction": "contra"}
        for i in range(0, len(todo), 16):
            chunk = todo[i: i + 16]
            enc = tok([pairs[k][0] for k in chunk], [pairs[k][1] for k in chunk], return_tensors="pt",
                      truncation=True, max_length=512, padding=True)
            with torch.inference_mode():
                probs = torch.softmax(model(**enc).logits, dim=-1).tolist()
            for k, row in zip(chunk, probs):
                out[k] = {names[model.config.id2label[j].lower()]: v for j, v in enumerate(row)}
                f = CACHE / f"mdeberta_{hashlib.sha1(f'{pairs[k][0]}|{pairs[k][1]}'.encode('utf-8')).hexdigest()}.json"
                f.write_text(json.dumps(out[k]), encoding="utf-8")
    return out


def nli(client, pairs: list[tuple[str, str, str]]) -> list[dict]:
    """pairs: (premise, hypothesis, prompt): 'v4' (a fact against the question), 'law' (a rule against its source
    text) or 'about' (does the text of a norm left out decide the goal: entail / contra = yes, neutral = no).
    Returns {"entail", "neutral", "contra", "llm": {...}, "mdeberta": {...} | None} per pair."""
    from diagnosis import nli_openai

    nli_openai.PROMPTS.setdefault("law", LAW_PROMPT)
    nli_openai.PROMPTS.setdefault("about", ABOUT_PROMPT)

    def one(pair):
        p, h, pr = pair
        return _cached_call("nli", f"{NLI_MODEL}|{pr}|{p}|{h}",
                            lambda: nli_openai.score_pair(client, NLI_MODEL, p, h, pr))

    with ThreadPoolExecutor(8) as pool:
        llm = list(pool.map(one, pairs))
    use_md = [ENSEMBLE and pr != "about" and h for _, h, pr in pairs]
    md_idx = [k for k, u in enumerate(use_md) if u]
    md = dict(zip(md_idx, mdeberta([pairs[k][:2] for k in md_idx]))) if md_idx else {}
    out = []
    for k, sc in enumerate(llm):
        m = md.get(k)
        mean = {lab: (sc[lab] + m[lab]) / 2 for lab in sc} if m else dict(sc)
        out.append({**mean, "llm": sc, "mdeberta": m})
    return out


def diagnose(obs: list[str], atoms: list[str], k: int = MAX_K) -> tuple[list[list[str]], list[str]]:
    """Subset-minimal diagnoses (fault atoms over component ids) and the symptoms (components inconsistent with
    everything working normally)."""
    req = f"diag([{', '.join(obs)}], [{', '.join(atoms)}], {k}).\n"
    r = subprocess.run([str(swipl()), "-q", "-f", "none", "-g", "serve", "-t", "halt", str(MBD_PL)], input=req,
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    if r.returncode or "ERROR" in r.stderr:
        raise RuntimeError(f"MBD failed: {r.stderr}")
    lines = r.stdout.splitlines()
    if "END" not in lines:
        raise RuntimeError("MBD returned an incomplete response")
    if any(ln.startswith("ERROR") for ln in lines):
        raise RuntimeError(next(ln for ln in lines if ln.startswith("ERROR")))
    out, symptoms = [], []
    for ln in lines:
        if ln.startswith("SYMPTOM "):
            symptoms.append(ln[8:].strip())
        elif ln.startswith("["):
            inner = ln.strip()[1:-1]
            out.append([x.strip() for x in _split_terms(inner)] if inner else [])
    return out, symptoms


def _split_terms(s: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
            continue
        depth += ch in "(["
        depth -= ch in ")]"
        cur += ch
    return parts + ([cur] if cur else [])


# No prior over fault modes: every minimal diagnosis starts equally likely and is ranked only by the measured
# NLI scores (maximum likelihood). EPS is a numerical floor, so a score of 0 never rules a diagnosis out alone.
EPS = 1e-3
CASE_MODES = ("missing", "omission", "misinterp", "unsupported")


def _cid(f: str) -> list[str]:
    return [c.strip() for c in f[f.index("(") + 1:-1].split(",")]


def _mode_of(d: list[str], comp: str, modes: tuple) -> str:
    for f in d:
        m = f.split("(")[0]
        if m in modes and comp in _cid(f):
            return m
    return "ok"


def _modes(row: dict) -> tuple:
    """The fault modes a component can be in."""
    if row["layer"] == "kb":
        return ("misencoded",)
    if row["layer"] == "retrieval":
        return ("omitted",)
    return {"checked": ("misinterp", "unsupported"), "required": ("missing", "omission"),
            "presumed": ("omission",)}[row["kind"]]


def likelihood(row: dict, mode: str) -> float:
    """P(the NLI scores of a component | its mode), from the raw scores, including those below the acceptance
    threshold: a measurement too weak to be an observation still tells which diagnosis is likelier."""
    e, n, c = row["p_entail"], row["p_neutral"], row["p_contra"]
    if row["layer"] == "case":
        kind, pos = row["kind"], row.get("polarity", "pos") == "pos"
        if kind == "checked":
            v = {"ok": e if pos else c, "misinterp": c if pos else e, "unsupported": n}.get(mode, EPS)
        elif kind == "required":
            v = {"missing": n, "omission": e + c}.get(mode, EPS)
        else:  # presumed absent
            v = {"ok": n + c, "omission": e}.get(mode, EPS)
    elif row["layer"] == "kb":
        v = e if mode == "ok" else 1 - e
    else:
        v = n if mode == "ok" else 1 - n
    return max(v, EPS)


def rank(diagnoses: list[list[str]], table: list[dict]) -> list[float]:
    """Probability of each diagnosis given the measurements, with all diagnoses equally likely beforehand:
    proportional to the product, over the components any diagnosis blames, of P(scores | mode of the component
    in that diagnosis). An unresolved conflict has no measurement of its own; it is weighed through the rules of
    the pair (normal in that diagnosis, misencoded in the other)."""
    if not diagnoses:
        return []
    rows = {r["id"]: r for r in table}
    blamed = {c for d in diagnoses for f in d if not f.startswith("kbconflict") for c in _cid(f)}
    weights = []
    for d in diagnoses:
        w = 1.0
        for cid in blamed:
            row = rows[cid]
            w *= likelihood(row, _mode_of(d, cid, _modes(row)))
        weights.append(w)
    z = sum(weights) or 1.0
    return [w / z for w in weights]


def answer_dist(row: dict, mode: str) -> dict[str, float]:
    """What the user would answer to "is <component> true in your case?" if the component is in this mode.
    Taken from the NLI scores of the component against the question; where the question says nothing about it
    (missing, unsupported) the answer is unknown: yes and no equally likely."""
    e, c = row["p_entail"], row["p_contra"]
    stated = {"yes": e / (e + c), "no": c / (e + c)} if e + c > 0 else {"yes": 0.5, "no": 0.5}
    unknown = {"yes": 0.5, "no": 0.5}
    if row["kind"] == "checked":
        said, other = ("yes", "no") if row.get("polarity", "pos") == "pos" else ("no", "yes")
        return {"ok": {said: 1.0, other: 0.0}, "misinterp": {said: 0.0, other: 1.0}}.get(mode, unknown)
    if row["kind"] == "required":  # stated in the question and dropped, or not stated at all
        return stated if mode == "omission" else unknown
    if mode == "omission":  # presumed absent, but the question states the exception
        return {"yes": 1.0, "no": 0.0}
    n = row["p_neutral"]  # normal: the question denies the exception (contra) or says nothing (neutral)
    return {"yes": 0.5 * n / (n + c), "no": (c + 0.5 * n) / (n + c)} if n + c > 0 else unknown


def _entropy(ps) -> float:
    import math

    return -sum(p * math.log2(p) for p in ps if p > 0)


def next_questions(diagnoses: list[list[str]], post: list[float], table: list[dict]) -> list[dict]:
    """Sequential diagnosis: the case components the user can be asked about ("is this true in your case?"),
    ranked by the expected information gain of the answer over the diagnoses (entropy of the posterior before,
    minus its expected entropy after the answer), then by the posterior mass that blames them."""
    rows = {r["id"]: r for r in table}
    cands = sorted({c for d in diagnoses for f in d if f.split("(")[0] in CASE_MODES for c in _cid(f)})
    h0, out = _entropy(post), []
    for cid in cands:
        row = rows[cid]
        dists = [answer_dist(row, _mode_of(d, cid, CASE_MODES)) for d in diagnoses]
        gain = h0
        for a in ("yes", "no"):
            joint = [p * dd[a] for p, dd in zip(post, dists)]
            pa = sum(joint)
            if pa > 0:
                gain -= pa * _entropy([j / pa for j in joint])
        fault_mass = sum(p for d, p in zip(diagnoses, post) if _mode_of(d, cid, CASE_MODES) != "ok")
        out.append({"id": cid, "statement": row["statement"], "gain": round(gain, 4),
                    "fault_mass": round(fault_mass, 4)})
    return sorted(out, key=lambda q: (-q["gain"], -q["fault_mass"]))


def update(diagnoses: list[list[str]], post: list[float], table: list[dict], cid: str, ans: str) -> list[float]:
    """Posterior after the user answers ans (yes / no) about component cid (Bayes rule with answer_dist)."""
    row = {r["id"]: r for r in table}[cid]
    w = [p * max(answer_dist(row, _mode_of(d, cid, CASE_MODES))[ans], EPS) for d, p in zip(diagnoses, post)]
    z = sum(w) or 1.0
    return [x / z for x in w]


def _kind(d: list[str]) -> str:
    layers = {LAYER[f.split("(")[0]] for f in d}
    invented_missing = any(f.startswith("unsupported(") and f.replace("unsupported(", "missing(") in d for f in d)
    only_inventions = all(f.split("(")[0] in ("missing", "unsupported") for f in d)
    return "ask" if layers == {"user"} or (invented_missing and only_inventions) else "confirm" if not layers & {"kb", "retrieval"} else "warn"


def choose(diagnoses: list[list[str]], symptoms: list[str], post: list[float] | None = None,
           questions: list[dict] | None = None) -> tuple[str, list[str]]:
    """Action and the components it is about, from the posterior mass of three kinds of diagnosis: only facts the
    question does not state (ask), faults of the reading of the case (confirm), faults of the KB or of step 2
    (warn). confirm asks about the single most informative component (sequential diagnosis: the next turn
    diagnoses again with the answer); ask names the facts those diagnoses miss, which the answer needs.
    No diagnosis within the bound: the symptoms stay unexplained, which is never a reason to answer."""
    if [] in diagnoses:
        return "answer", []
    if not diagnoses:
        return "unresolved", symptoms
    post = post or [1 / len(diagnoses)] * len(diagnoses)
    mass = {}
    for d, p in zip(diagnoses, post):
        mass[_kind(d)] = mass.get(_kind(d), 0.0) + p
    action = max(mass, key=mass.get)
    mine = [(d, p) for d, p in zip(diagnoses, post) if _kind(d) == action]
    if action == "ask":
        return "ask", sorted({c for d, _ in mine for f in d for c in _cid(f)})
    if action == "confirm":
        parser = {c for d, _ in mine for f in d if LAYER[f.split("(")[0]] == "parser" for c in _cid(f)}
        asked = [q["id"] for q in questions or [] if q["id"] in parser]
        return "confirm", asked[:1] or sorted(parser)
    return "warn", sorted({c for d, _ in mine for f in d if LAYER[f.split("(")[0]] in ("kb", "retrieval")
                           for c in _cid(f)})


def verify(question: str, facts: list[str], parts: list[dict], con, client=None) -> dict:
    """Diagnose a run. Returns the components with their statements and NLI labels, the minimal diagnoses
    (fault atoms over component ids) and the chosen action with the components it is about."""
    from .policy import OPTIONS
    options = OPTIONS.get()
    if options.get("system") in ("symbolic", "no_mbd"):
        return decide([], [], **options)
    comps = components(parts, facts)
    client = client or extractor(CLIENT_MODEL).client
    near_misses(con, client, question, comps)
    if not comps["atoms"] and not comps["rules"] and not comps["near"]:
        return {"components": [], "observations": [], "candidates": [], "symptoms": [], "diagnoses": [[]],
                "action": "answer", "about": []}
    sent = render(con, facts, comps)
    stmt = {k: v[0] for k, v in sent.items()}
    ids = list(comps["atoms"]) + list(comps["rules"]) + list(comps["near"])

    def pair(i):
        if i in comps["atoms"]:
            return question, stmt[i], "v4"
        if i in comps["rules"]:
            return comps["rules"][i]["text"], stmt[i], "law"
        r = comps["near"][i]  # does the text of a norm left out say anything about what is asked?
        return r["text"], stmt[r["goal"]], "about"

    pairs = [pair(i) for i in ids]
    neg_ids = [i for i in ids if i in comps["atoms"]]
    scored = nli(client, pairs + [(question, sent[i][1], "v4") for i in neg_ids])
    scores, neg_scores = scored[: len(ids)], dict(zip(neg_ids, scored[len(ids):]))
    table = []
    for i, sc in zip(ids, scores):
        raw = {"p_llm": sc["llm"], "p_mdeberta": sc["mdeberta"],
               **{f"p_{k}": round(sc[k], 4) for k in ("entail", "neutral", "contra")}}
        if i in comps["atoms"]:
            a = comps["atoms"][i]
            ns = neg_scores[i]
            table.append({"id": i, "layer": "case", "kind": a["kind"], "polarity": a.get("polarity", "pos"),
                          "item": a["atom"], "needed": a.get("needed", False), "statement": stmt[i], "neg_statement": sent[i][1], "premise": "question",
                          **raw, **{f"n_{k}": round(ns[k], 4) for k in ("entail", "neutral", "contra")}})
        elif i in comps["near"]:
            r = comps["near"][i]
            table.append({"id": i, "layer": "retrieval", "kind": "near_miss", "item": r["norm"],
                          "statement": stmt[r["goal"]], "neg_statement": "", "premise": r["unit"],
                          "expected": r["expected"], **raw})
        else:
            r = comps["rules"][i]
            table.append({"id": i, "layer": "kb", "kind": "rule", "item": r["norm"], "statement": stmt[i],
                          "neg_statement": "", "premise": r["unit"], **raw})
    # A parser invention implies missing user information only when removing it
    # actually destroys all certain conclusions. An unsupported exception may
    # instead hide a perfectly supported answer and needs confirmation/repair.
    necessary = [r for r in table if r.get("needed") and r["kind"] == "checked"]
    for row in necessary:
        row["needed"] = False
        from .reason import Reasoner
        from .questions import Question, answer
        programs = {p.get("program") for p in parts if p["kind"] == "case"}
        if None in programs:
            continue
        for program in programs:
            rr = Reasoner(Path(program))
            try:
                reduced = [f for f in facts if f.replace(" ", "") != row["item"].replace(" ", "")]
                for p in parts:
                    if p["kind"] != "case" or p.get("program") != program:
                        continue
                    ff = [f for f in p.get("false_facts", []) if f.replace(" ", "") != row["item"].replace(" ", "")]
                    after = answer(Question(**p["parsed"]), p.get("parameters", []) + reduced, rr, con, ff)
                    if after["verdict"] == "unknown":
                        row["needed"] = True
            finally:
                rr.close()
    return decide(table, comps["competing"], supports=comps["supports"], **options)


def label_of(row: dict, tau: float, rule: str) -> tuple[str | None, str | None, str]:
    """(accepted label, label of the negative sentence, reason it was not accepted) for a component's scores."""
    sc = {k: row[f"p_{k}"] for k in ("entail", "neutral", "contra")}
    best = max(sc, key=sc.get)
    if sc[best] < tau:
        return None, None, "low_confidence"
    if rule == "pos_neg" and "n_entail" in row:
        ns = {k: row[f"n_{k}"] for k in ("entail", "neutral", "contra")}
        neg = max(ns, key=ns.get)
        expected = {"entail": "contra", "contra": "entail", "neutral": "neutral"}[best]
        if not (neg == expected or (best != "neutral" and neg == "neutral")):
            return None, neg, "template_disagreement"
        return best, neg, ""
    return best, None, ""


def decide(table: list[dict], competing: list, tau: float | None = None, rule: str | None = None,
           supports: list = (), system: str = "mbd", budget: int | None = None) -> dict:
    """Observations from the measured components (acceptance threshold tau, rule pos_neg / pos_only), minimal
    diagnoses, symptoms and the action. Separate from the measurements so tau can be calibrated on stored
    scores without measuring again."""
    tau = TAU if tau is None else tau
    rule = ACCEPT_RULE if rule is None else rule
    if system == "no_acceptance":
        tau, rule = 0.0, "pos_only"
    obs, faults = [], []
    for row in table:
        i = row["id"]
        label, neg_label, reason = label_of(row, tau, rule)
        row.update(label=label, neg_label=neg_label, reject_reason=reason)
        if row["layer"] == "case":
            obs.append(f"{row['kind']}({i})")
            if row["kind"] == "checked":
                obs.append(f"parsed({i}, {row.get('polarity', 'pos')})")
                faults += [f"misinterp({i})", f"unsupported({i})"]
                if row.get("needed"):
                    obs.append(f"needed({i})")
                    faults.append(f"missing({i})")
            elif row["kind"] == "required":
                faults += [f"missing({i})", f"omission({i})"]
            else:
                faults.append(f"omission({i})")
            if label:
                obs.append(f"q({i}, {label})")
        elif row["layer"] == "retrieval":
            obs.append(f"near_miss({i})")
            faults.append(f"omitted({i})")
            if row.get("expected"):
                obs.append(f"selection_gap({i})")
            elif label:
                obs.append(f"rettext({i}, {label})")
        else:
            obs.append(f"rule_used({i})")
            faults.append(f"misencoded({i})")
            if label:
                obs.append(f"kbtext({i}, {label})")
    for a, b in competing:
        obs.append(f"competing({a}, {b})")
        faults.append(f"kbconflict({a}, {b})")
    for a, b, c in supports:
        obs.append(f"supports({a}, {b}, {c})")
    from .policy import SYSTEMS, local_faults, limit_questions
    if system not in SYSTEMS:
        raise ValueError(f"Unknown system: {system}")
    if system in ("symbolic", "no_mbd"):
        diagnoses, symptoms = [[]], []
    elif system in ("heuristic", "direct", "no_diagnosis_repair"):
        local = local_faults(table, direct=system == "direct")
        diagnoses = [local]
        symptoms = sorted({c for f in local for c in _cid(f)})
    else:
        diagnoses, symptoms = diagnose(obs, faults, min(MAX_K, len(faults))) if faults else ([[]], [])
    for row in table:
        row["symptom"] = row["id"] in symptoms or any(row["id"] in s.split("-") for s in symptoms)
    post = rank(diagnoses, table)
    order = sorted(range(len(diagnoses)), key=lambda i: -post[i])  # likeliest diagnosis first
    diagnoses, post = [diagnoses[i] for i in order], [round(post[i], 4) for i in order]
    questions = next_questions(diagnoses, post, table) if [] not in diagnoses else []
    action, about = choose(diagnoses, symptoms, post, questions)
    if system == "no_diagnosis_repair" and symptoms:
        # Detect anomalies, but neither isolate their causes nor repair retrieval.
        action, about, diagnoses, post, questions = "warn", [], [], [], []
    result = {"system": system, "tau": tau, "accept_rule": rule, "components": table, "competing": competing, "supports": list(supports), "observations": obs, "candidates": faults,
            "symptoms": symptoms, "diagnoses": diagnoses, "posterior": post, "questions": questions,
            "explanations": [[explain(f, table) for f in d] for d in diagnoses], "action": action, "about": about}
    return limit_questions(result, budget)


FAULT_VI = {"missing": "câu hỏi không nêu", "omission": "bộ đọc câu hỏi bỏ sót (câu hỏi có nêu)",
            "misinterp": "bộ đọc câu hỏi đọc sai (câu hỏi nói điều ngược lại / giá trị khác)",
            "unsupported": "bộ đọc câu hỏi tự thêm (câu hỏi không nêu)",
            "misencoded": "luật mã hoá không khớp nguyên văn", "kbconflict": "hai luật mâu thuẫn chưa được giải quyết",
         "omitted": "bước chọn luật bỏ sót một quy định nói về điều được hỏi"}
ACTIONS = ("answer", "ask", "confirm", "warn", "unresolved")


def explain(fault: str, comps: list[dict]) -> str:
    """'misinterp(c3)' -> what it means, with the component it is about."""
    mode, arg = fault.split("(", 1)
    items = {c["id"]: c for c in comps}
    about = "; ".join(f"{i} = {items[i]['item']} («{items[i]['statement']}»)" if i in items else i
                      for i in arg[:-1].replace(" ", "").split(","))
    return f"{FAULT_VI.get(mode, mode)}: {about}"
