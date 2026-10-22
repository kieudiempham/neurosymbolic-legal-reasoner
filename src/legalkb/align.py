"""Alignment of predicates across articles (after each article is stored).

Each article is extracted separately, so the same notion can get two names (tham_gia_bao_hiem_xa_hoi_bat_buoc in
Điều 2, thuoc_dien_tham_gia_bhxh_bat_buoc in Điều 33). For every newly declared predicate, candidate predicates
already in the KB are short-listed by token overlap (with acronyms: bao_hiem_xa_hoi ~ bhxh); the LLM then labels
each pair, and the result goes to predicate_links:
  same      the two names mean the same thing (same arity); the new one is renamed at compile time
  implies   one implies the other (bridge rule); src_mode says whether the premise is the predicate holding or
            a subject having an obligation / right / prohibition to perform it (an action predicate)
"""

from __future__ import annotations

import hashlib
import json
import re
import time

from .extract import CACHE, _obj, _s
from .normalize import canon_name

ALIGN_VERSION = "align-v2"
SHORTLIST = 12

LINK = _obj({
    "new_pred": _s, "other_pred": _s,
    "relation": {"type": "string", "enum": ["same", "new_implies_other", "other_implies_new", "unrelated"]},
    "premise_mode": {"type": "string", "enum": ["holds", "obligation", "right", "prohibition"]},
    "arg_map": {"type": "array", "items": {"type": "integer"}},
    "reason": _s})
RESPONSE = _obj({"links": {"type": "array", "items": LINK}})

PROMPT = """Bạn chuẩn hoá ontology của một cơ sở tri thức pháp luật Việt Nam được mã hoá thành logic bậc nhất.
Mỗi Điều luật được mã hoá riêng nên cùng một khái niệm có thể mang hai tên khác nhau.

VỊ TỪ MỚI (tên/số đối số(vai trò:loại) [loại vị từ] — mô tả):
{new}

VỊ TỪ ĐÃ CÓ (ứng viên):
{old}

Với mỗi cặp (vị từ mới, vị từ đã có) CÓ liên hệ, trả một mục trong "links":
- relation "same": cùng nghĩa và cùng số đối số (chỉ khác cách đặt tên/viết tắt).
- relation "new_implies_other" / "other_implies_new": vế này suy ra vế kia theo quy định pháp luật hoặc theo nghĩa
  (vd "phải tham gia BHXH bắt buộc" ⇒ "thuộc diện tham gia BHXH bắt buộc"; "là cán bộ công chức" ⇒ "là người lao động").
- premise_mode: vế giả thiết (vế suy ra) được hiểu thế nào: "holds" nếu vị từ đó đúng; "obligation" / "right" /
  "prohibition" nếu vế giả thiết là một HÀNH VI (vị từ loại action) và điều suy ra là "chủ thể có nghĩa vụ / có quyền /
  bị cấm thực hiện hành vi đó".
- arg_map: với mỗi đối số của vế KẾT LUẬN theo thứ tự, chỉ số (từ 0) của đối số tương ứng ở vế GIẢ THIẾT.
  Với "same", arg_map là ánh xạ đối số của vị từ đã có theo vị từ mới (thường [0, 1, ...]).
- reason: một câu ngắn.
Mỗi liên kết là một LUẬT PHỔ QUÁT, đúng với MỌI chủ thể: chỉ ghi khi luôn đúng, không ghi khi chỉ đúng "trong một số
trường hợp". Hai khái niệm loại trừ nhau (bắt buộc / tự nguyện) không bao giờ suy ra nhau.
Ghi tên vị từ KHÔNG kèm "/số đối số". Không liệt kê cặp không liên hệ. Không đoán khi không chắc.
"""


def _tokens(name: str) -> set[str]:
    t = [x for x in name.split("_") if x]
    out = set(t)
    for i in range(len(t)):  # acronyms of runs: bao_hiem_xa_hoi -> bh, bhxh, ...
        for j in range(i + 2, min(len(t), i + 5) + 1):
            out.add("".join(w[0] for w in t[i:j]))
    return out


def _describe(con, name: str) -> str:
    arity, kind, desc = con.execute("SELECT arity, kind, description_vi FROM predicates WHERE name=?", (name,)).fetchone()
    args = ", ".join(f"{r}:{t}" for r, t in con.execute(
        "SELECT role, type FROM predicate_args WHERE pred=? ORDER BY position", (name,)))
    return f"- {name}/{arity}({args}) [{kind}] — {desc}"


def shortlist(con, name: str, exclude: set[str]) -> list[str]:
    mine = _tokens(name)
    scored = []
    for (other,) in con.execute("SELECT name FROM predicates"):
        if other in exclude:
            continue
        theirs = _tokens(other)
        score = len(mine & theirs) / len(mine | theirs)
        if score > 0:
            scored.append((score, other))
    return [o for _, o in sorted(scored, reverse=True)[:SHORTLIST]]


def align(con, client, model: str, new_preds: set[str]) -> int:
    """Label new predicates against existing ones; insert predicate_links. Returns the number of links."""
    new_preds = {p for p in new_preds if con.execute("SELECT 1 FROM predicates WHERE name=?", (p,)).fetchone()}
    cands = sorted({c for p in new_preds for c in shortlist(con, p, new_preds)})
    if not new_preds or not cands:
        return 0
    prompt = PROMPT.format(new="\n".join(_describe(con, p) for p in sorted(new_preds)),
                           old="\n".join(_describe(con, c) for c in cands))
    key = hashlib.sha1(f"{ALIGN_VERSION}|{model}|{prompt}".encode("utf-8")).hexdigest()
    f = CACHE / f"align_{key}.json"
    if f.exists():
        out = json.loads(f.read_text(encoding="utf-8"))
    else:
        for attempt in range(6):
            try:
                r = client.chat.completions.create(
                    model=model, temperature=0,
                    response_format={"type": "json_schema", "json_schema": {"name": "predicate_links", "strict": True,
                                                                            "schema": RESPONSE}},
                    messages=[{"role": "user", "content": prompt}])
                out = json.loads(r.choices[0].message.content)
                f.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
                break
            except Exception as e:  # noqa: BLE001
                if "insufficient_quota" in str(e):
                    raise
                time.sleep(min(60, 3 * 2 ** attempt))
        else:
            raise RuntimeError("alignment failed")
    arity = dict(con.execute("SELECT name, arity FROM predicates"))
    n = 0
    for link in out["links"]:
        new, other = (canon_name(re.sub(r"[/(].*$", "", link[k])) for k in ("new_pred", "other_pred"))
        if new not in new_preds or other not in cands or link["relation"] == "unrelated":
            continue
        amap = ",".join(str(i) for i in link["arg_map"])
        if link["relation"] == "same":
            if arity[new] != arity[other]:
                continue
            row = (new, "holds", "same", other, amap)
        elif link["relation"] == "new_implies_other":
            row = (new, link["premise_mode"], "implies", other, amap)
        else:
            row = (other, link["premise_mode"], "implies", new, amap)
        con.execute("INSERT OR REPLACE INTO predicate_links VALUES (?,?,?,?,?,?,?)", (*row, link["reason"], model))
        n += 1
    return n
