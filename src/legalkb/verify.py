"""Step 4: first-order cross-layer model-based diagnosis of a run, before the answer is written.

Components are read off the proofs of the run (verify):
  checked    case facts a proof uses                  (parser output: pos)
  required   facts a conditional answer still needs   (parser output: none)
  presumed   exceptions presumed absent               (parser output: none)
  rule       norms used by a certain proof; competing pairs of norms proving opposite conclusions
Each is verbalised in Vietnamese (one call, VERBALISE_MODEL) and measured by NLI with a different model
(NLI_MODEL, prompt v4 of the paper, by default gpt-4.1): a fact against the question, a rule against the
source text of its unit. A label below the acceptance threshold TAU is left unobserved. mbd.pl returns the
minimal diagnoses, from which the action follows:
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

from .compile import SWIPL
from .extract import CACHE, Extractor, _obj, _s

VERBALISE_MODEL = os.environ.get("LEGALKB_VERBALISE_MODEL", "gpt-4.1-mini")
# gpt-4.1 rather than the paper's gpt-4o-mini: on this pipeline's verbalisations gpt-4o-mini took
# "tôi ký hợp đồng lao động" to entail "the contract has no fixed term"; it is also not the parser's model
NLI_MODEL = os.environ.get("LEGALKB_NLI_MODEL", "gpt-4.1")
TAU = float(os.environ.get("LEGALKB_NLI_TAU", 0.5))
MAX_K = 6  # bound on the size of a diagnosis (the search starts at the number of symptoms needed)
MBD_PL = Path(__file__).with_name("mbd.pl")
LAYER = {"missing": "user", "omission": "parser", "misinterp": "parser", "unsupported": "parser",
         "misencoded": "kb", "kbconflict": "kb"}

VERBALISE = """Diễn đạt mỗi mục dưới đây thành MỘT câu tiếng Việt tự nhiên, khẳng định, đúng nghĩa của mục,
không thêm và không bớt điều kiện. Gọi thực thể theo cách câu hỏi gọi nó ("toi" là "người hỏi"; "công ty";
"hợp đồng lao động của người hỏi"; thực thể có hậu tố _an_danh: theo loại, vd "người sử dụng lao động"), KHÔNG
dùng mã như hd1, cong_ty.
- instance_of(X, loai): nếu X là người hỏi hoặc một người / tổ chức: "X là <loại>"; nếu X là một đối tượng (hợp
  đồng, hồ sơ, khoản tiền...): nói rằng đối tượng đó có trong tình huống, vd "Người hỏi có một hợp đồng lao động".
- Mục loại "fact": một sự kiện của tình huống. attr(X, thuoc_tinh, gia_tri) là "thuộc tính của X là giá trị";
  so sánh như attr(X, thoi_han) >= 1 là "thời hạn của X từ 1 trở lên" (đơn vị theo ngữ cảnh: tháng, đồng).
- Mục loại "rule": một luật "nếu ... thì ...": viết "Nếu <các điều kiện> thì <kết luận / nghĩa vụ>".

Câu hỏi (để biết các thực thể là ai): {question}
Loại của các thực thể: {types}

Các mục:
{items}
"""

RESPONSE = _obj({"statements": {"type": "array", "items": _obj({"id": _s, "statement": _s})}})

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
    """Components of a run, keyed c1.. (atoms) and n1.. (norms)."""
    key = lambda s: s.replace(" ", "")  # noqa: E731  proof goals are printed without spaces
    fact_text = {key(f): f for f in facts}
    atoms, rules, competing = {}, {}, []

    def atom_id(text: str, kind: str) -> str:
        for cid, a in atoms.items():
            if key(a["atom"]) == key(text):
                return cid
        cid = f"c{len(atoms) + 1}"
        atoms[cid] = {"atom": text, "kind": kind}
        return cid

    for p in parts:
        if p["kind"] != "case":
            continue
        heads = {"answer": set(), "contrary": set()}
        for role in ("answers", "contrary"):
            for a in p.get(role, []):
                for m in a["missing"]:
                    atom_id(m, "required")
                for m in a["presumed_absent"]:
                    atom_id(m, "presumed")
                for n in _leaves(a["proof"]):
                    if n.get("kind") == "fact" and not n["goal"].startswith("attr(tham_so"):
                        atom_id(fact_text.get(key(n["goal"]), n["goal"]), "checked")
                    if a["status"] == "certain" and n.get("kind") == "rule" and n.get("norm") not in (None, "derived"):
                        if n["norm"] not in {r["norm"] for r in rules.values()}:
                            rules[f"n{len(rules) + 1}"] = {"norm": n["norm"]}
                        heads["answer" if role == "answers" else "contrary"].add(n["norm"])
        if any(a["status"] == "certain" for a in p.get("answers", [])) and \
                any(a["status"] == "certain" for a in p.get("contrary", [])):
            rid = {r["norm"]: k for k, r in rules.items()}
            competing += [(rid[x], rid[y]) for x in sorted(heads["answer"]) for y in sorted(heads["contrary"])]
    # the types of the entities the checked facts are about are facts the parser read too
    for f in facts:
        if f.startswith("instance_of(") and any(f[12:].split(",")[0] in a["atom"] for a in list(atoms.values())
                                                if a["kind"] != "presumed"):
            atom_id(f, "checked")
    return {"atoms": atoms, "rules": rules, "competing": competing}


def _cached_call(name: str, payload: str, fn):
    f = CACHE / f"{name}_{hashlib.sha1(payload.encode('utf-8')).hexdigest()}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    out = fn()
    f.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def verbalise(client, question: str, facts: list[str], comps: dict, con) -> dict[str, str]:
    from .questions import describe_norm

    items = [f"- {cid} (fact): {a['atom']}" for cid, a in comps["atoms"].items()]
    for nid, r in comps["rules"].items():
        d = describe_norm(con, r["norm"])
        r.update(unit=d["unit"], text=law_premise(con, d["unit"]))
        items.append(f"- {nid} (rule): nếu {' VÀ '.join(d['conditions']) or '(không điều kiện)'} thì {d['head']} "
                     f"(chủ thể {d['holder']})")
    types = ", ".join(f[12:-1] for f in facts if f.startswith("instance_of("))
    prompt = VERBALISE.format(question=question, types=types, items="\n".join(items))

    def call():
        for attempt in range(6):
            try:
                r = client.chat.completions.create(
                    model=VERBALISE_MODEL, temperature=0,
                    response_format={"type": "json_schema", "json_schema": {"name": "statements", "strict": True,
                                                                            "schema": RESPONSE}},
                    messages=[{"role": "user", "content": prompt}])
                return json.loads(r.choices[0].message.content)
            except Exception as e:  # noqa: BLE001
                if "insufficient_quota" in str(e):
                    raise
                time.sleep(min(60, 3 * 2 ** attempt))
        raise RuntimeError("verbalisation failed")

    out = _cached_call("verbalise", f"{VERBALISE_MODEL}|{prompt}", call) if items else {"statements": []}
    return {s["id"]: s["statement"] for s in out["statements"]}


def nli(client, pairs: list[tuple[str, str, str]]) -> list[dict]:
    """pairs: (premise, hypothesis, prompt) with prompt 'v4' (question premise) or 'law' (source text premise)."""
    from diagnosis import nli_openai

    nli_openai.PROMPTS.setdefault("law", LAW_PROMPT)

    def one(pair):
        p, h, pr = pair
        return _cached_call("nli", f"{NLI_MODEL}|{pr}|{p}|{h}",
                            lambda: nli_openai.score_pair(client, NLI_MODEL, p, h, pr))

    with ThreadPoolExecutor(8) as pool:
        return list(pool.map(one, pairs))


def diagnose(obs: list[str], atoms: list[str], k: int = MAX_K) -> tuple[list[list[str]], list[str]]:
    """Minimal diagnoses (fault atoms over component ids) and the symptoms (components inconsistent with
    everything working normally)."""
    req = f"diag([{', '.join(obs)}], [{', '.join(atoms)}], {k}).\n"
    r = subprocess.run([str(SWIPL), "-q", "-f", "none", "-g", "serve", "-t", "halt", str(MBD_PL)], input=req,
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    lines = r.stdout.splitlines()
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


def choose(diagnoses: list[list[str]], symptoms: list[str]) -> tuple[str, list[str]]:
    """Action and the components it is about. No diagnosis within the bound: the symptoms stay unexplained,
    which is never a reason to answer."""
    if [] in diagnoses:
        return "answer", []
    if not diagnoses:
        return "unresolved", symptoms
    m = min(len(d) for d in diagnoses)
    mins = [d for d in diagnoses if len(d) == m]
    layers = lambda d: {LAYER[f.split("(")[0]] for f in d}  # noqa: E731
    comp = lambda f: f[f.index("(") + 1:-1]  # noqa: E731
    user_only = [d for d in mins if layers(d) == {"user"}]
    if user_only:
        return "ask", sorted({comp(f) for d in user_only for f in d})
    case_only = [d for d in mins if "kb" not in layers(d)]
    if case_only:
        return "confirm", sorted({comp(f) for d in case_only for f in d if LAYER[f.split("(")[0]] == "parser"})
    return "warn", sorted({c for d in mins for f in d if LAYER[f.split("(")[0]] == "kb" for c in comp(f).split(",")})


def verify(question: str, facts: list[str], parts: list[dict], con, client=None) -> dict:
    """Diagnose a run. Returns the components with their statements and NLI labels, the minimal diagnoses
    (fault atoms over component ids) and the chosen action with the components it is about."""
    comps = components(parts, facts)
    if not comps["atoms"] and not comps["rules"]:
        return {"components": [], "observations": [], "candidates": [], "symptoms": [], "diagnoses": [[]],
                "action": "answer", "about": []}
    client = client or Extractor(VERBALISE_MODEL).client
    stmt = verbalise(client, question, facts, comps, con)
    ids = list(comps["atoms"]) + list(comps["rules"])
    premises = [question if i in comps["atoms"] else comps["rules"][i]["text"] for i in ids]
    scores = nli(client, [(p, stmt.get(i, ""), "v4" if i in comps["atoms"] else "law")
                          for p, i in zip(premises, ids)])
    obs, faults, table = [], [], []
    for i, sc in zip(ids, scores):
        best = max(sc, key=sc.get)
        label = best if sc[best] >= TAU else None
        if i in comps["atoms"]:
            a = comps["atoms"][i]
            obs.append({"required": f"required({i})", "presumed": f"presumed({i})",
                        "checked": f"checked({i})"}[a["kind"]])
            if a["kind"] == "checked":
                obs.append(f"parsed({i}, pos)")
                faults += [f"misinterp({i})", f"unsupported({i})"]
            elif a["kind"] == "required":
                faults += [f"missing({i})", f"omission({i})"]
            else:
                faults.append(f"omission({i})")
            if label:
                obs.append(f"q({i}, {label})")
            table.append({"id": i, "layer": "case", "kind": a["kind"], "item": a["atom"], "statement": stmt.get(i, ""),
                          "premise": "question", "label": label, **{f"p_{k}": round(v, 4) for k, v in sc.items()}})
        else:
            r = comps["rules"][i]
            obs.append(f"rule_used({i})")
            faults.append(f"misencoded({i})")
            if label:
                obs.append(f"kbtext({i}, {label})")
            table.append({"id": i, "layer": "kb", "kind": "rule", "item": r["norm"], "statement": stmt.get(i, ""),
                          "premise": r["unit"], "label": label, **{f"p_{k}": round(v, 4) for k, v in sc.items()}})
    for a, b in comps["competing"]:
        obs.append(f"competing({a}, {b})")
        faults.append(f"kbconflict({a}, {b})")
    diagnoses, symptoms = diagnose(obs, faults, min(MAX_K, len(faults)))
    for row in table:
        row["symptom"] = row["id"] in symptoms or any(row["id"] in s.split("-") for s in symptoms)
    action, about = choose(diagnoses, symptoms)
    return {"components": table, "observations": obs, "candidates": faults, "symptoms": symptoms,
            "diagnoses": diagnoses, "explanations": [[explain(f, table) for f in d] for d in diagnoses],
            "action": action, "about": about}


FAULT_VI = {"missing": "câu hỏi không nêu", "omission": "bộ đọc câu hỏi bỏ sót (câu hỏi có nêu)",
            "misinterp": "bộ đọc câu hỏi đọc sai (câu hỏi nói điều ngược lại / giá trị khác)",
            "unsupported": "bộ đọc câu hỏi tự thêm (câu hỏi không nêu)",
            "misencoded": "luật mã hoá không khớp nguyên văn", "kbconflict": "hai luật mâu thuẫn chưa được giải quyết"}
ACTIONS = ("answer", "ask", "confirm", "warn", "unresolved")


def explain(fault: str, comps: list[dict]) -> str:
    """'misinterp(c3)' -> what it means, with the component it is about."""
    mode, arg = fault.split("(", 1)
    items = {c["id"]: c for c in comps}
    about = "; ".join(f"{i} = {items[i]['item']} («{items[i]['statement']}»)" if i in items else i
                      for i in arg[:-1].replace(" ", "").split(","))
    return f"{FAULT_VI.get(mode, mode)}: {about}"
