"""Fixed Vietnamese templates for the names the rules use, and deterministic rendering of atoms, rules and goals.

The MBD observations need every component as a sentence. Writing those sentences with an LLM at run time adds a
component nobody checks (it once rendered instance_of(hd1, hop_dong_lao_dong) as "hợp đồng lao động hd1 là một hợp
đồng lao động"). Instead each name gets templates once per KB (TEMPLATE_MODEL), stored in the templates table
where they can be read and corrected, and every sentence is assembled from them:
  pred   pos / neg with slots {0}, {1}, ... for the arguments ("{0} làm việc cho {1} theo {2}")
  attr   label and unit ("thời hạn", "tháng")
  type   label ("người lao động")
  value  label of an enumerated value ("không xác định thời hạn")
A template whose slots do not match the arity is rejected (the name is then rendered as it is).

    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.templates [--sample]     # build / complete the templates
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time

from .extract import CACHE, Extractor, _obj, _s

TEMPLATE_MODEL = "gpt-4.1"
OP_POS = {">=": "từ {v} trở lên", ">": "trên {v}", "=<": "không quá {v}", "<=": "không quá {v}", "<": "dưới {v}",
          "=:=": "bằng {v}", "==": "là {v}", "=": "là {v}", "\\==": "khác {v}", "!=": "khác {v}"}
OP_NEG = {">=": "dưới {v}", ">": "không quá {v}", "=<": "trên {v}", "<=": "trên {v}", "<": "từ {v} trở lên",
          "=:=": "khác {v}", "==": "không phải là {v}", "=": "không phải là {v}", "\\==": "là {v}", "!=": "là {v}"}

PROMPT = """Viết mẫu câu tiếng Việt (có dấu, tự nhiên, ngắn) cho các tên dùng trong một cơ sở tri thức pháp luật.
- pred (vị từ): "pos" là câu khẳng định, "neg" là câu phủ định tương ứng; dùng chỗ trống {{0}}, {{1}}, ... đúng
  thứ tự và đủ số đối số ghi bên cạnh (loại của mỗi đối số trong ngoặc). Ví dụ lam_viec_theo_hop_dong(nguoi_lao_dong,
  nguoi_su_dung_lao_dong, hop_dong_lao_dong): pos "{{0}} làm việc cho {{1}} theo {{2}}", neg "{{0}} không làm việc
  cho {{1}} theo {{2}}".
- attr (thuộc tính): "label" là tên thuộc tính ("thời hạn", "tiền lương"), "unit" là đơn vị đọc được ("tháng",
  "đồng") hoặc chuỗi rỗng; pos / neg để trống.
- type (loại): "label" là tên loại ("người lao động"); value (giá trị danh mục): "label" là cách đọc
  ("không xác định thời hạn").
Trả đúng mỗi tên một mục, giữ nguyên kind và name.

{items}
"""

RESPONSE = _obj({"templates": {"type": "array", "items": _obj({
    "kind": {"type": "string", "enum": ["pred", "attr", "type", "value"]}, "name": _s, "label": _s, "unit": _s,
    "pos": _s, "neg": _s})}})

SCHEMA = """CREATE TABLE IF NOT EXISTS templates (
  kind TEXT NOT NULL CHECK (kind IN ('pred','attr','type','value')), name TEXT NOT NULL, label TEXT, unit TEXT,
  pos TEXT, neg TEXT, arity INTEGER, PRIMARY KEY (kind, name));"""


def names_used(con) -> dict[str, dict]:
    """kind -> name -> details (arity and argument types for predicates), for the names the rules use."""
    con.executescript(SCHEMA)
    var_type = {(n, v): t for n, v, t in con.execute("SELECT norm_id, var, type FROM norm_variables")}
    out = {"pred": {}, "attr": {}, "type": {}, "value": {}}
    rows = con.execute("SELECT norm_id, pred, args FROM norm_conditions WHERE kind='atom' AND pred IS NOT NULL "
                       "UNION ALL SELECT norm_id, action_pred, action_args FROM norms WHERE action_pred IS NOT NULL "
                       "UNION ALL SELECT norm_id, conclusion_pred, conclusion_args FROM norms "
                       "WHERE conclusion_pred IS NOT NULL").fetchall()
    for nid, p, args in rows:
        a = [x.strip() for x in (args or "").split(",") if x.strip()]
        out["pred"].setdefault(p, {"arity": len(a), "types": [var_type.get((nid, x), x) for x in a]})
    for (a,) in con.execute("SELECT attr FROM norm_conditions WHERE attr IS NOT NULL UNION SELECT value_attr FROM "
                            "norm_conditions WHERE value_attr IS NOT NULL UNION SELECT target_attr FROM norm_formulas"):
        out["attr"][a] = {}
    for nid, expr in con.execute("SELECT norm_id, expression FROM norm_formulas"):
        for a in re.findall(r"[a-z_][a-z0-9_]*", expr):
            if a not in ("min", "max", "round", "abs"):
                out["attr"][a] = {}
    for (t,) in con.execute("SELECT DISTINCT type FROM norm_variables UNION SELECT name FROM entity_types"):
        if t:
            out["type"][t] = {}
    for (v,) in con.execute("SELECT DISTINCT value_text FROM norm_conditions WHERE value_text IS NOT NULL"):
        out["value"][v] = {}
    variables = {v for (v,) in con.execute("SELECT DISTINCT var FROM norm_variables")}
    for _, _, args in rows:  # constants in arguments (quy_huu_tri_tu_tuat) are read as values
        for x in (args or "").split(","):
            x = x.strip()
            if re.fullmatch(r"[a-z][a-z0-9_]*", x) and x not in variables:
                out["value"][x] = {}
    return out


def cap(s: str) -> str:
    """Upper-case the first letter only (str.capitalize would turn BHXH into bhxh)."""
    return s[:1].upper() + s[1:]


def _clean_label(lab: str) -> str:
    first = lab.split(" ", 1)[0]
    return lab if first.isupper() and len(first) > 1 else lab[:1].lower() + lab[1:]


def build(con, model: str = TEMPLATE_MODEL, batch: int = 60) -> int:
    """Create the templates the KB still lacks. Returns how many were stored."""
    used = names_used(con)
    have = {(k, n) for k, n in con.execute("SELECT kind, name FROM templates")}
    todo = [(k, n, d) for k, names in used.items() for n, d in names.items() if (k, n) not in have]
    client = Extractor(model).client
    stored = 0
    for i in range(0, len(todo), batch):
        chunk = todo[i: i + batch]
        items = "\n".join(f"- {k} {n}" + (f" ({d['arity']} đối số: {', '.join(map(str, d['types']))})" if k == "pred"
                                          else "") for k, n, d in chunk)
        prompt = PROMPT.format(items=items)
        f = CACHE / f"templates_{hashlib.sha1(f'{model}|{prompt}'.encode('utf-8')).hexdigest()}.json"
        out = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
        for attempt in range(6 if out is None else 0):
            try:
                r = client.chat.completions.create(
                    model=model, temperature=0,
                    response_format={"type": "json_schema", "json_schema": {"name": "templates", "strict": True,
                                                                            "schema": RESPONSE}},
                    messages=[{"role": "user", "content": prompt}])
                out = json.loads(r.choices[0].message.content)["templates"]
                f.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
                break
            except Exception as e:  # noqa: BLE001
                if "insufficient_quota" in str(e):
                    raise
                time.sleep(min(60, 3 * 2 ** attempt))
        if out is None:
            raise RuntimeError("template generation failed")
        want = {(k, n): d for k, n, d in chunk}
        for t in out:
            d = want.get((t["kind"], t["name"]))
            if d is None:
                continue
            if t["kind"] == "pred":
                slots = {f"{{{j}}}" for j in range(d["arity"])}
                if not all(x in t["pos"] and x in t["neg"] for x in slots):
                    continue  # slots do not match the arity: rejected
            con.execute("INSERT OR REPLACE INTO templates VALUES (?,?,?,?,?,?,?)",
                        (t["kind"], t["name"], _clean_label(t["label"]), t["unit"], t["pos"].rstrip(" ."),
                         t["neg"].rstrip(" ."),
                         d.get("arity") if t["kind"] == "pred" else None))
            stored += 1
        con.commit()
    return stored


class Renderer:
    """Sentences for atoms (pos, neg), rules and goals from the templates of a KB."""

    def __init__(self, con, facts: list[str] = ()):
        con.executescript(SCHEMA)
        self.t = {(k, n): (lab, unit, pos, neg) for k, n, lab, unit, pos, neg in con.execute(
            "SELECT kind, name, label, unit, pos, neg FROM templates")}
        self.con = con
        self.entity_type = {}
        for f in facts:
            m = re.fullmatch(r"instance_of\(\s*([^,]+?)\s*,\s*([^)]+?)\s*\)", f)
            if m:
                self.entity_type[m.group(1)] = m.group(2)

    def label(self, kind: str, name: str) -> str:
        t = self.t.get((kind, name))
        return t[0] if t and t[0] else name.replace("_", " ")

    def entity(self, x: str) -> str:
        x = x.strip().strip("'")
        if x == "toi":
            return "người hỏi"
        if x.endswith("_an_danh"):
            return self.label("type", x[: -len("_an_danh")])
        if x in self.entity_type:
            return self.label("type", self.entity_type[x])
        if re.fullmatch(r"-?\d+(\.\d+)?", x):
            return x
        return self.label("value", x) if ("value", x) in self.t else x.replace("_", " ")

    def value(self, attr: str, v: str) -> str:
        v = v.strip().strip("'")
        unit = (self.t.get(("attr", attr)) or ("", "", "", ""))[1]
        if re.fullmatch(r"-?\d+(\.\d+)?", v):
            n = float(v)
            s = f"{int(n):,}".replace(",", ".") if n.is_integer() else str(n).replace(".", ",")
            return f"{s} {unit}".strip()
        return self.label("value", v)

    def pred(self, name: str, args: list[str], negated: bool = False) -> str:
        t = self.t.get(("pred", name))
        if not t:
            return f"{'không ' if negated else ''}{name.replace('_', ' ')}({', '.join(args)})"
        tpl = t[3] if negated else t[2]
        try:
            return tpl.format(*args)
        except (IndexError, KeyError):
            return tpl

    def atom(self, text: str) -> tuple[str, str]:
        """An atom as printed by the reasoner or the parser -> (positive sentence, negative sentence)."""
        s = text.strip()
        m = re.fullmatch(r"attr\(\s*([^,]+?)\s*,\s*([^,()]+?)\s*\)\s*(>=|=<|<=|>|<|=:=|==|\\==|!=)\s*(.+)", s)
        if m:  # a comparison a proof still needs: attr(x, a) >= v
            x, a, op, v = m.groups()
            subj = f"{self.label('attr', a)} của {self.entity(x)}"
            return (cap(f"{subj} {OP_POS[op].format(v=self.value(a, v))}"),
                    cap(f"{subj} {OP_NEG[op].format(v=self.value(a, v))}"))
        m = re.fullmatch(r"attr\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*(.+)\)", s)
        if m:
            x, a, v = m.groups()
            subj = f"{self.label('attr', a)} của {self.entity(x)}"
            return cap(f"{subj} là {self.value(a, v)}"), cap(f"{subj} không phải là {self.value(a, v)}")
        m = re.fullmatch(r"instance_of\(\s*([^,]+?)\s*,\s*([^)]+?)\s*\)", s)
        if m:
            x, t = m.groups()
            if x.strip() == "toi" or self.label("type", t).split()[0] in ("người", "tổ", "cơ", "doanh", "công"):
                e = "Người hỏi" if x.strip() == "toi" else cap(self.entity(x))
                if x.strip() != "toi":
                    return (f"Trong tình huống có {self.label('type', t)}",
                            f"Trong tình huống không có {self.label('type', t)}")
                return f"{e} là {self.label('type', t)}", f"{e} không phải là {self.label('type', t)}"
            return f"Người hỏi có {self.label('type', t)}", f"Người hỏi không có {self.label('type', t)}"
        m = re.fullmatch(r"([a-z_][a-z0-9_]*)\((.*)\)", s)
        if m:
            name, args = m.group(1), [self.entity(a) for a in _split(m.group(2))]
            return cap(self.pred(name, args)), cap(self.pred(name, args, True))
        return s, f"không {s}"

    def rule(self, nid: str) -> str:
        """Nếu <conditions> thì <head>, from the norm's rows (variables read as their types)."""
        c = self.con
        modality, subj, bearer, apred, aargs, cpred, cargs, cneg = c.execute(
            "SELECT modality, subject_var, bearer_var, action_pred, action_args, conclusion_pred, conclusion_args, "
            "conclusion_negated FROM norms WHERE norm_id=?", (nid,)).fetchone()
        vt = dict(c.execute("SELECT var, type FROM norm_variables WHERE norm_id=?", (nid,)))
        var = lambda x: self.label("type", vt[x.strip()]) if x.strip() in vt else self.entity(x)  # noqa: E731
        groups: dict[int, dict[int, list[str]]] = {}
        for g, o, kind, pred, args, neg, attr, of, op, num, txt, unit, vattr, vof in c.execute(
                "SELECT alt_group, alt_option, kind, pred, args, negated, attr, of_var, op, value_num, value_text, "
                "unit, value_attr, value_of FROM norm_conditions WHERE norm_id=? ORDER BY cond_id", (nid,)):
            if kind == "atom" and pred:
                a = [x for x in (args or "").split(",") if x.strip()]
                if len(a) == 1 and pred in {t for (t,) in c.execute("SELECT name FROM entity_types")}:
                    s = f"{var(a[0])} là {self.label('type', pred)}"
                else:
                    s = self.pred(pred, [var(x) for x in a], bool(neg))
            elif kind == "compare" and attr:
                if vattr:
                    other = self.label("attr", vattr) + ("" if vof == "tham_so" else f" của {var(vof)}")
                    rhs = other if num in (None, 1) else f"{num:g} lần {other}"
                    s = f"{self.label('attr', attr)} của {var(of)} {OP_POS.get(op, op + ' {v}').format(v=rhs)}"
                else:
                    v = self.value(attr, str(num if num is not None else txt))
                    if num is not None and float(num).is_integer():
                        v = self.value(attr, str(int(num)))
                    s = f"{self.label('attr', attr)} của {var(of)} {OP_POS.get(op, op + ' {v}').format(v=v)}"
                s = f"không phải {s}" if neg else s
            else:
                continue
            groups.setdefault(g, {}).setdefault(o, []).append(s)
        parts = [" và ".join(x for lits in groups.get(0, {}).values() for x in lits)] if 0 in groups else []
        for g, opts in sorted(groups.items()):
            if g:
                parts.append("(" + " hoặc ".join(" và ".join(lits) for _, lits in sorted(opts.items())) + ")")
        holder = var(bearer or subj or "")
        if apred:
            act = self.pred(apred, [var(x) for x in (aargs or "").split(",") if x.strip()])
            head = {"obligation": f"{holder} bắt buộc phải thực hiện: {act}", "right": f"{holder} được quyền: {act}",
                    "prohibition": f"{holder} bị cấm: {act}", "procedure": f"phải thực hiện thủ tục: {act}"}.get(
                modality, act)
        elif cpred:
            head = self.pred(cpred, [var(x) for x in (cargs or "").split(",") if x.strip()], bool(cneg))
        else:
            head = "(không có kết luận)"
        for tgt, of, expr in c.execute("SELECT target_attr, of_var, expression FROM norm_formulas WHERE norm_id=?",
                                       (nid,)):
            e = re.sub(r"[a-z_][a-z0-9_]*", lambda m: m.group(0) if m.group(0) in ("min", "max", "round", "abs")
                       else self.label("attr", m.group(0)), expr).replace("*", "×")
            head += f"; {self.label('attr', tgt)} = {e}"
        cond = " và ".join(p for p in parts if p)
        return f"Nếu {cond} thì {head}" if cond else cap(head)

    def goal(self, q: dict, subject_type: str | None) -> str:
        """What a case question asks, with a generic subject (its type), as one sentence."""
        who = self.label("type", subject_type) if subject_type else "người hỏi"
        if q["type"] == "status" and q.get("pred"):
            args = [who] + [self.entity(a) if a else "..." for a in q.get("args") or []]
            return cap(self.pred(q["pred"], args, bool(q.get("negated"))))
        if q["type"] in ("yes_no", "list_norms", "deadline") and q.get("pred"):
            args = [who] + [self.entity(a) if a else "..." for a in q.get("args") or []]
            mod = {"obligation": "phải", "right": "được", "prohibition": "bị cấm"}.get(q.get("modality"), "phải")
            return f"{cap(who)} {mod} thực hiện: {self.pred(q['pred'], args)}"
        if q["type"] == "amount":
            return f"Mức {self.label('attr', q['attr']) if q.get('attr') else 'tiền'} của {who}"
        if q["type"] == "sanction":
            return f"Mức xử phạt đối với {who}"
        return f"Nghĩa vụ và quyền của {who}"


def _split(s: str) -> list[str]:
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
            continue
        depth += ch == "("
        depth -= ch == ")"
        cur += ch
    return out + ([cur] if cur.strip() else [])


def main() -> None:
    from .db import connect
    from .sample_kb import SAMPLE_DB

    sys.stdout.reconfigure(encoding="utf-8")
    con = connect(SAMPLE_DB) if "--sample" in sys.argv else connect()
    print("stored", build(con))
    for row in con.execute("SELECT kind, name, label, unit, pos, neg FROM templates ORDER BY kind, name"):
        print(row)


if __name__ == "__main__":
    main()
