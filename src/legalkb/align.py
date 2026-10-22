"""Mapping of the names an extraction adds onto the fixed vocabulary (after each document is stored).

The model extracts freely (the vocabulary is in its prompt as guidance), so some notions get names outside the
vocabulary, or two names in two articles. For every new name (predicate, entity type, attribute), candidates are
short-listed by token overlap (with acronyms: bao_hiem_xa_hoi ~ bhxh), preferring vocabulary names; the LLM labels
each pair and the result is stored:
  predicate_links  same (alias, renamed at compile time) or implies (bridge rule; src_mode says whether the premise is
                   the predicate holding or a subject having an obligation / right / prohibition to perform it)
  name_links       same (type / attribute alias) or subtype (a new entity type below a vocabulary type)
Batches of new names are labelled in parallel.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor

from .extract import CACHE, _obj, _s
from .normalize import canon_name

ALIGN_VERSION = "align-v3"
SHORTLIST = 8
BATCH = 20

LINK = _obj({
    "new": _s, "other": _s,
    "relation": {"type": "string", "enum": ["same", "new_implies_other", "other_implies_new", "new_subtype_of_other",
                                            "unrelated"]},
    "premise_mode": {"type": "string", "enum": ["holds", "obligation", "right", "prohibition"]},
    "arg_map": {"type": "array", "items": {"type": "integer"}},
    "reason": _s})
RESPONSE = _obj({"links": {"type": "array", "items": LINK}})

KIND_VI = {"pred": "VỊ TỪ", "type": "LOẠI CHỦ THỂ / ĐỐI TƯỢNG", "attr": "THUỘC TÍNH"}

PROMPT = """Bạn chuẩn hoá ontology của một cơ sở tri thức pháp luật Việt Nam được mã hoá thành logic bậc nhất.
Mỗi Điều luật được mã hoá riêng nên cùng một khái niệm có thể mang tên khác với tên trong bộ từ vựng chuẩn.

{kind_vi} MỚI:
{new}

ỨNG VIÊN ĐÃ CÓ ([từ vựng] = tên chuẩn, ưu tiên ánh xạ về các tên này):
{old}

Với mỗi tên mới, xét các ứng viên và trả các mục CÓ liên hệ trong "links" (new = tên mới, other = ứng viên):
- "same": cùng nghĩa (chỉ khác cách đặt tên, viết tắt, mức chi tiết của tên){same_note}.
{kind_rules}- reason: một câu ngắn.
Mỗi liên kết là một LUẬT PHỔ QUÁT, đúng với MỌI trường hợp: chỉ ghi khi luôn đúng. Hai khái niệm loại trừ nhau
(bắt buộc / tự nguyện, được / không được) không bao giờ là same hay suy ra nhau. Ghi tên KHÔNG kèm "/số đối số".
Không liệt kê cặp không liên hệ. Không đoán khi không chắc. Các trường không dùng: premise_mode "holds", arg_map [].
"""

PRED_RULES = """- "new_implies_other" / "other_implies_new": vế này suy ra vế kia (vd "phải đóng BHXH bắt buộc" ⇒ "thuộc diện
  tham gia BHXH bắt buộc"). premise_mode: "holds" nếu vế giả thiết là vị từ đúng; "obligation" / "right" /
  "prohibition" nếu vế giả thiết là HÀNH VI và điều suy ra là "chủ thể có nghĩa vụ / có quyền / bị cấm làm hành vi đó".
- arg_map: với mỗi đối số của vế KẾT LUẬN (với same: của ứng viên), chỉ số (từ 0) của đối số tương ứng ở vế kia.
"""
TYPE_RULES = """- "new_subtype_of_other": loại mới là một trường hợp riêng của ứng viên (vd can_bo_xa ⊂ nguoi_lao_dong).
"""


def _tokens(name: str) -> set[str]:
    t = [x for x in name.split("_") if x]
    out = set(t)
    for i in range(len(t)):  # acronyms of runs: bao_hiem_xa_hoi -> bh, bhxh, ...
        for j in range(i + 2, min(len(t), i + 5) + 1):
            out.add("".join(w[0] for w in t[i:j]))
    return out


_TABLE = {"pred": "predicates", "type": "entity_types", "attr": "attributes"}


def _describe(con, kind: str, name: str) -> str:
    if kind == "pred":
        arity, k, desc, origin = con.execute(
            "SELECT arity, kind, description_vi, origin FROM predicates WHERE name=?", (name,)).fetchone()
        args = ", ".join(f"{r}:{t}" for r, t in con.execute(
            "SELECT role, type FROM predicate_args WHERE pred=? ORDER BY position", (name,)))
        head = f"{name}/{arity}({args}) [{k}]"
    elif kind == "type":
        parent, desc, origin = con.execute(
            "SELECT parent, description_vi, origin FROM entity_types WHERE name=?", (name,)).fetchone()
        head = name + (f" ⊂ {parent}" if parent else "")
    else:
        of, vt, unit, desc, origin = con.execute(
            "SELECT of_type, value_type, unit, description_vi, origin FROM attributes WHERE name=?", (name,)).fetchone()
        head = f"{name} (của {of}: {vt}{', ' + unit if unit else ''})"
    return f"- {head}{' [từ vựng]' if origin == 'vocab' else ''} — {desc}"


def shortlist(con, kind: str, name: str, exclude: set[str], domain: str) -> list[str]:
    mine = _tokens(name)
    scored = []
    for other, origin in con.execute(f"SELECT name, origin FROM {_TABLE[kind]} WHERE domain IN (?, 'chung') "
                                     "OR origin='vocab'", (domain,)):
        if other in exclude:
            continue
        theirs = _tokens(other)
        score = len(mine & theirs) / len(mine | theirs) + (0.1 if origin == "vocab" else 0)
        if score > 0.1:
            scored.append((score, other))
    return [o for _, o in sorted(scored, reverse=True)[:SHORTLIST]]


def _call(client, model: str, prompt: str) -> dict:
    key = hashlib.sha1(f"{ALIGN_VERSION}|{model}|{prompt}".encode("utf-8")).hexdigest()
    f = CACHE / f"align_{key}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    for attempt in range(6):
        try:
            r = client.chat.completions.create(
                model=model, temperature=0,
                response_format={"type": "json_schema", "json_schema": {"name": "name_links", "strict": True,
                                                                        "schema": RESPONSE}},
                messages=[{"role": "user", "content": prompt}])
            out = json.loads(r.choices[0].message.content)
            f.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
            return out
        except Exception as e:  # noqa: BLE001
            if "insufficient_quota" in str(e):
                raise
            time.sleep(min(60, 3 * 2 ** attempt))
    raise RuntimeError("alignment failed")


def align(con, client, model: str, new: dict[str, set[str]], domain: str, workers: int = 16) -> int:
    """new: kind ('pred' / 'type' / 'attr') -> names added by the document. Returns the number of links stored."""
    jobs = []  # (kind, batch, candidates, prompt), built in this thread (database reads)
    for kind, names in new.items():
        names = sorted(n for n in names if con.execute(f"SELECT 1 FROM {_TABLE[kind]} WHERE name=?", (n,)).fetchone())
        for i in range(0, len(names), BATCH):
            batch = names[i: i + BATCH]
            cands = sorted({c for n in batch for c in shortlist(con, kind, n, set(names), domain)})
            if not cands:
                continue
            prompt = PROMPT.format(
                kind_vi=KIND_VI[kind], new="\n".join(_describe(con, kind, n) for n in batch),
                old="\n".join(_describe(con, kind, c) for c in cands),
                same_note=" và cùng số đối số" if kind == "pred" else "",
                kind_rules=PRED_RULES if kind == "pred" else TYPE_RULES if kind == "type" else "")
            jobs.append((kind, set(batch), set(cands), prompt))
    with ThreadPoolExecutor(workers) as pool:
        outs = list(pool.map(lambda j: _call(client, model, j[3]), jobs))
    arity = dict(con.execute("SELECT name, arity FROM predicates"))
    n = 0
    for (kind, batch, cands, _), out in zip(jobs, outs):
        for link in out["links"]:
            a, b = (canon_name(re.sub(r"[/(].*$", "", link[k])) for k in ("new", "other"))
            rel = link["relation"]
            if a not in batch or b not in cands or a == b or rel == "unrelated":
                continue
            if kind == "pred":
                amap = ",".join(str(i) for i in link["arg_map"])
                if rel == "same" and arity[a] == arity[b]:
                    row = (a, "holds", "same", b, amap)
                elif rel == "new_implies_other":
                    row = (a, link["premise_mode"], "implies", b, amap)
                elif rel == "other_implies_new":
                    row = (b, link["premise_mode"], "implies", a, amap)
                else:
                    continue
                con.execute("INSERT OR REPLACE INTO predicate_links VALUES (?,?,?,?,?,?,?)", (*row, link["reason"], model))
            elif rel in ("same", "new_subtype_of_other") and (kind == "type" or rel == "same"):
                r = "same" if rel == "same" else "subtype"
                con.execute("INSERT OR REPLACE INTO name_links VALUES (?,?,?,?,?,?)", (kind, a, r, b, link["reason"], model))
                if r == "subtype":
                    con.execute("UPDATE entity_types SET parent=? WHERE name=?", (b, a))
            else:
                continue
            n += 1
    return n
