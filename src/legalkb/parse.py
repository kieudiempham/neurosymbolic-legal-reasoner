"""Semantic parsing: a Vietnamese question -> case facts + typed questions (questions.Question), one per part.

The vocabulary offered to the model is the names the compiled rules actually use (a fact only matters if a rule
can read it), each with argument types read off the rules; on a large KB only the names closest to the question
(embeddings) are offered. The answer schema restricts every name to that list, so the facts match the rules.

    from legalkb.parse import Parser
    facts, false_facts, questions, raw = Parser(con).parse("Tôi làm việc theo hợp đồng ... có phải đóng BHXH không?")
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time

import numpy as np

from .extract import CACHE, Extractor, _obj, _opt, _s
from .normalize import canon_name, canon_unit
from .questions import QUESTION_TYPES, Question

PARSER_MODEL = os.environ.get("LEGALKB_PARSER_MODEL", "gpt-4.1-mini")
PARSER_VERSION = "parse-v4"
SHORTLIST = {"type": 40, "pred": 80, "attr": 40}

PROMPT = """Bạn chuyển câu hỏi pháp luật tiếng Việt thành dữ kiện logic cho một hệ suy luận.

TỪ VỰNG (chỉ được dùng các tên này):
- Loại chủ thể/đối tượng: {types}
- Vị từ (tên(loại đối số, ...)): {preds}
- Thuộc tính (tên của loại: đơn vị): {attrs}

LOẠI CÂU HỎI:
{qtypes}

YÊU CẦU:
1. entities: mỗi người / tổ chức / hợp đồng / khoản tiền... được nhắc tới (kể cả người hỏi, "tôi" -> id "toi"):
   id chữ thường không dấu (toi, cong_ty, hd1), type là một loại trong từ vựng (loại cụ thể nhất phù hợp).
   Thêm cả thực thể ngầm cần cho vị từ (vd làm việc theo hợp đồng thì có người sử dụng lao động và hợp đồng).
2. facts: MỌI tình tiết được nói rõ trong câu hỏi mà có vị từ cùng nghĩa trong từ vựng phải thành một fact (quan
   hệ giữa các thực thể, tình trạng của một thực thể: cách làm việc, đang hưởng chế độ gì, có hành vi gì...), đối số
   là các id. Điều câu hỏi khẳng định là KHÔNG đúng -> false_facts. Không suy đoán điều không được nói.
3. attributes: giá trị số / danh mục được nói rõ. value_number là con số đúng như trong câu, unit là đơn vị đúng như
   trong câu (vd 10 và "triệu đồng"; 12 và "tháng"). Thuộc tính danh mục: chọn một giá trị ghi sau tên thuộc tính
   trong từ vựng CHỈ KHI đúng nghĩa với câu hỏi; nếu không có giá trị nào đúng nghĩa thì ghi giá trị theo câu hỏi.
4. questions: MỖI ý được hỏi là một mục (câu hỏi gộp "có phải ... không, bao nhiêu" -> 2 mục); type (một loại ở trên); subject = id của chủ thể được hỏi; modality (obligation / right / prohibition /
   procedure) nếu hỏi phải / được / bị cấm / thủ tục; pred = vị từ của hành vi / tình trạng / khái niệm được hỏi;
   hỏi "có thuộc diện / có được hưởng / có là ... không" là status (pred là vị từ tình trạng), hỏi "có phải / được
   / bị cấm LÀM ... không" là yes_no (pred là vị từ hành vi);
   args = các đối số của pred SAU đối số chủ thể, theo thứ tự (id, hằng, hoặc null nếu là điều được hỏi); attr = thuộc tính cần
   tính (câu hỏi "bao nhiêu"); negated = true nếu hỏi "có KHÔNG thuộc diện..."; document = số văn bản (validity).

CÂU HỎI: {question}
"""


ARG_TYPES: dict[str, list[str | None]] = {}  # predicate -> type of each argument (from the rules), filled by _sig


def _sig(con, kind: str) -> dict[str, str]:
    """name -> readable signature, for the names the rules use (attributes: with the values rules compare to)."""
    if kind == "type":
        names = {t for (t,) in con.execute("SELECT DISTINCT type FROM norm_variables WHERE type IS NOT NULL")}
        parent = dict(con.execute("SELECT name, parent FROM entity_types"))
        names |= {p for n in list(names) if (p := parent.get(n))}
        return {n: n + (f" ⊂ {parent[n]}" if parent.get(n) else "") for n in names}
    var_type = {}
    for nid, v, t in con.execute("SELECT norm_id, var, type FROM norm_variables"):
        var_type[(nid, v)] = t
    out = {}
    if kind == "pred":
        rows = con.execute("SELECT norm_id, pred, args FROM norm_conditions WHERE kind='atom' AND pred IS NOT NULL "
                           "UNION ALL SELECT norm_id, action_pred, action_args FROM norms WHERE action_pred IS NOT NULL "
                           "UNION ALL SELECT norm_id, conclusion_pred, conclusion_args FROM norms "
                           "WHERE conclusion_pred IS NOT NULL")
        for nid, p, args in rows:
            if p not in out:
                a = [x.strip() for x in (args or "").split(",") if x.strip()]
                out[p] = f"{p}({', '.join(var_type.get((nid, x), x) for x in a)})"
                ARG_TYPES[p] = [var_type.get((nid, x)) for x in a]
    else:
        rows = con.execute("SELECT norm_id, attr, of_var, unit FROM norm_conditions WHERE attr IS NOT NULL "
                           "UNION ALL SELECT norm_id, value_attr, value_of, NULL FROM norm_conditions "
                           "WHERE value_attr IS NOT NULL "
                           "UNION ALL SELECT norm_id, target_attr, of_var, unit FROM norm_formulas")
        for nid, a, of, unit in rows:
            if a and a not in out:
                out[a] = f"{a} của {var_type.get((nid, of), of)}" + (f": {unit}" if unit else "")
        values = {}
        for a, v in con.execute("SELECT DISTINCT attr, value_text FROM norm_conditions WHERE value_text IS NOT NULL"):
            values.setdefault(a, []).append(v)
        for a, vs in values.items():
            if a in out:
                out[a] += f" (giá trị: {' | '.join(sorted(vs))})"
        for nid, of, expr in con.execute("SELECT norm_id, of_var, expression FROM norm_formulas"):
            for a in re.findall(r"[a-z_][a-z0-9_]*", expr):
                if a not in out and a not in ("min", "max", "round", "abs"):
                    out[a] = f"{a} của {var_type.get((nid, of), of)}"
    return out


class Parser:
    def __init__(self, con, model: str = PARSER_MODEL):
        self.con, self.model = con, model
        self.ex = Extractor(model)
        self.sig = {k: _sig(con, k) for k in ("type", "pred", "attr")}
        self.arity = {p: sig.count(",") + 1 if "()" not in sig else 0 for p, sig in self.sig["pred"].items()}
        self.actions = {p for (p,) in con.execute("SELECT DISTINCT action_pred FROM norms WHERE action_pred IS NOT NULL")}

    def _shortlist(self, question: str) -> dict[str, list[str]]:
        out = {}
        for kind, sig in self.sig.items():
            names = sorted(sig)
            if len(names) <= SHORTLIST[kind]:
                out[kind] = names
                continue
            from .canon import embed

            q = embed(self.con, self.ex.client, [question])[0]
            v = embed(self.con, self.ex.client, [n.replace("_", " ") for n in names])
            out[kind] = [names[i] for i in np.argsort(-(v @ q))[: SHORTLIST[kind]]]
        return out

    def _schema(self, names: dict[str, list[str]]) -> dict:
        enum = lambda xs: {"type": "string", "enum": xs or ["_"]}  # noqa: E731
        ident = {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"}
        atom = _obj({"pred": enum(names["pred"]), "args": {"type": "array", "items": _s}})
        return _obj({
            "entities": {"type": "array", "items": _obj({"id": ident, "type": enum(names["type"]), "mention": _s})},
            "facts": {"type": "array", "items": atom},
            "false_facts": {"type": "array", "items": atom},
            "attributes": {"type": "array", "items": _obj({
                "entity": ident, "attr": enum(names["attr"]), "value_number": _opt({"type": "number"}),
                "value_text": _opt(_s), "unit": _opt(_s)})},
            "questions": {"type": "array", "items": _obj({
                "type": {"type": "string", "enum": list(QUESTION_TYPES)}, "subject": _opt(_s),
                "modality": _opt({"type": "string", "enum": ["obligation", "right", "prohibition", "procedure"]}),
                "pred": _opt(enum(names["pred"])), "args": {"type": "array", "items": _opt(_s)},
                "attr": _opt(enum(names["attr"])), "negated": {"type": "boolean"}, "document": _opt(_s)})}})

    def _call(self, prompt: str, schema: dict) -> dict:
        key = hashlib.sha1(f"{PARSER_VERSION}|{self.model}|{prompt}".encode("utf-8")).hexdigest()
        f = CACHE / f"parse_{key}.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))
        for attempt in range(6):
            try:
                r = self.ex.client.chat.completions.create(
                    model=self.model, temperature=0,
                    response_format={"type": "json_schema", "json_schema": {"name": "parse", "strict": True,
                                                                            "schema": schema}},
                    messages=[{"role": "user", "content": prompt}])
                out = json.loads(r.choices[0].message.content)
                f.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
                return out
            except Exception as e:  # noqa: BLE001
                if "insufficient_quota" in str(e):
                    raise
                time.sleep(min(60, 3 * 2 ** attempt))
        raise RuntimeError("parsing failed")

    def parse(self, question: str) -> tuple[list[str], list[str], list[Question], dict]:
        names = self._shortlist(question)
        prompt = PROMPT.format(
            types=", ".join(self.sig["type"][n] for n in names["type"]),
            preds="; ".join(self.sig["pred"][n] for n in names["pred"]),
            attrs="; ".join(self.sig["attr"][n] for n in names["attr"]),
            qtypes="\n".join(f"- {k}: {v}" for k, v in QUESTION_TYPES.items()), question=question)
        out = self._call(prompt, self._schema(names))
        q = lambda x: x if re.fullmatch(r"[a-z][a-z0-9_]*|-?\d+(\.\d+)?", x) else "'" + x.replace("'", "\\'") + "'"  # noqa: E731
        facts = [f"instance_of({e['id']}, {e['type']})" for e in out["entities"]]
        implicit: dict[str, str] = {}
        ids = {e["id"] for e in out["entities"]}

        def atom(a: dict) -> str:
            """A fact; an argument the question leaves unnamed (the employer of "tôi ký hợp đồng") becomes an
            implicit entity of the type the predicate expects there."""
            args, types = [], ARG_TYPES.get(a["pred"]) or []
            for i, x in enumerate(a["args"]):
                t = types[i] if i < len(types) else None
                # a place the rules fill with a typed entity, but the question names none ("null", "_", a type name)
                if x not in ids and (t or x in (None, "", "null", "none", "_")):
                    x = implicit.setdefault(t or "thuc_the", f"{t or 'thuc_the'}_an_danh")
                args.append(q(x))
            return f"{a['pred']}({', '.join(args)})"

        false_facts = [atom(a) for a in out["false_facts"]]
        # a fact also stated as false: the negation is the explicit one ("tôi không hưởng lương hưu")
        facts += [x for x in (atom(a) for a in out["facts"]) if x not in false_facts]
        facts += [f"instance_of({e}, {t})" for t, e in implicit.items() if t != "thuc_the"]
        for a in out["attributes"]:
            if a["value_number"] is not None:
                unit, factor = canon_unit(a["unit"])
                v = a["value_number"] * factor
                facts.append(f"attr({a['entity']}, {a['attr']}, {int(v) if float(v).is_integer() else v})")
            elif a["value_text"]:
                facts.append(f"attr({a['entity']}, {a['attr']}, {q(canon_name(a['value_text']))})")
        questions = [self._normalise(Question(
            type=qq["type"], subject=qq["subject"], modality=qq["modality"], pred=qq["pred"], args=list(qq["args"]),
            attr=qq["attr"], negated=qq["negated"], document=qq["document"])) for qq in out["questions"]]
        return facts, false_facts, questions, out

    def _normalise(self, q: Question) -> Question:
        """Arguments after the subject, as many as the predicate has; a yes/no question about a predicate that is
        no norm's action asks for a status."""
        if q.args and q.args[0] == q.subject:
            q.args = q.args[1:]
        if q.pred in self.arity:
            n = max(self.arity[q.pred] - 1, 0)
            q.args = (q.args + [None] * n)[:n]
        if q.type == "yes_no" and q.pred and q.pred not in self.actions:
            q.type, q.modality = "status", None
        return q
