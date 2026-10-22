"""Layer 3-4: LLM extraction of first-order norms from one Điều (all its Khoản / Điểm), into the relational store.

The model (default gpt-4.1) answers with OpenAI Structured Outputs under a strict JSON schema, so every response
has exactly the fields of the normative schema. The current ontology (entity types, predicates, attributes) is
given in the prompt so names are reused; new ones are declared in the same response and inserted first.
Responses are cached on disk (data/legalkb/cache) by (model, article text, prompt version).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .db import ROOT
from .normalize import canon_name, canon_unit

CACHE = ROOT / "data" / "legalkb" / "cache"
PROMPT_VERSION = "norm-v3"
MODEL = os.environ.get("LEGALKB_MODEL", "gpt-4.1-mini")

_s = {"type": "string"}
_n = {"type": "number"}
_null = {"type": "null"}
_strs = {"type": "array", "items": _s}


def _obj(props: dict) -> dict:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def _opt(schema: dict) -> dict:
    return {"anyOf": [schema, _null]}


CONDITION = _obj({
    "kind": {"type": "string", "enum": ["atom", "compare"]},
    "alt_group": {"type": "integer"}, "alt_option": {"type": "integer"},
    "pred": _opt(_s), "args": _strs, "negated": {"type": "boolean"},
    "attr": _opt(_s), "of": _opt(_s), "op": _opt({"type": "string", "enum": ["<", "<=", "=", ">=", ">", "!="]}),
    "value_number": _opt(_n), "value_text": _opt(_s), "unit": _opt(_s), "value_attr": _opt(_s), "value_of": _opt(_s)})
NORM = _obj({
    "unit_id": _s,
    "modality": {"type": "string", "enum": ["obligation", "right", "prohibition", "definition", "consequence",
                                            "procedure", "sanction"]},
    "variables": {"type": "array", "items": _obj({"name": _s, "type": _s})},
    "subject": _s, "bearer": _opt(_s), "beneficiary": _opt(_s),
    "conditions": {"type": "array", "items": CONDITION},
    "action": _opt(_obj({"pred": _s, "args": _strs})),
    "conclusion": _opt(_obj({"pred": _s, "args": _strs, "negated": {"type": "boolean"}})),
    "formulas": {"type": "array", "items": _obj({"target_attr": _s, "of": _s, "expression": _s, "unit": _opt(_s)})},
    "deadline": _opt(_obj({"amount": _n, "unit": _s, "from_event": _s})),
    "sanction": _opt(_obj({"kind": _s, "min_amount": _opt(_n), "max_amount": _opt(_n), "unit": _opt(_s), "text": _s})),
    "exception_refs": _strs, "other_refs": _strs,
    "valid_from": _opt(_s), "valid_to": _opt(_s), "validity_note": _s, "quote": _s})
RESPONSE = _obj({
    "entity_types": {"type": "array", "items": _obj({"name": _s, "parent": _opt(_s), "description_vi": _s})},
    "predicates": {"type": "array", "items": _obj({
        "name": _s, "kind": {"type": "string", "enum": ["relation", "property", "action", "status"]},
        "description_vi": _s, "args": {"type": "array", "items": _obj({"role": _s, "type": _s})}})},
    "attributes": {"type": "array", "items": _obj({
        "name": _s, "of_type": _s, "value_type": {"type": "string", "enum": ["number", "date", "enum", "text", "boolean"]},
        "unit": _opt(_s), "description_vi": _s})},
    "norms": {"type": "array", "items": NORM}})



PROMPT = """Bạn là chuyên gia mã hóa văn bản quy phạm pháp luật Việt Nam thành quy phạm logic bậc nhất (có biến).

TỪ VỰNG CỐ ĐỊNH CỦA LĨNH VỰC (BẮT BUỘC dùng đúng các tên này; chỉ khai báo tên mới khi thật sự không có tên nào
cùng nghĩa, và khai báo nó trong entity_types / predicates / attributes):
- Loại chủ thể/đối tượng (loại⊂loại cha): {types}
- Vị từ (tên/số đối số(vai trò:loại)): {preds}
- Thuộc tính (tên của loại: kiểu, đơn vị): {attrs}
Loại chủ thể dùng qua "variables" (biến P loại nguoi_lao_dong), KHÔNG viết thành điều kiện vị từ một ngôi.

YÊU CẦU — mỗi quy phạm (norm) trong các đơn vị trên thành MỘT mục trong "norms":
1. unit_id: mã đơn vị chứa quy phạm (Khoản/Điểm cụ thể nhất).
2. modality: obligation (phải), right (được/có quyền), prohibition (không được/cấm), definition (là/được hiểu là/được
   coi là), consequence (hệ quả pháp lý: thuộc diện, được miễn, vô hiệu...), procedure (hồ sơ, trình tự, cơ quan),
   sanction (chế tài, mức phạt).
3. variables: MỌI biến dùng trong quy phạm, viết HOA (P, E, C, Y...), mỗi biến một loại trong ontology.
   subject = biến chủ thể chính; bearer = biến người mang nghĩa vụ/quyền (nếu có); beneficiary = người được hưởng (nếu có).
4. conditions: điều kiện áp dụng (phần giả định).
   - kind "atom": quan hệ/thuộc tính dạng vị từ trên biến, args là tên biến hoặc hằng chữ thường; negated=true nếu phủ định.
   - kind "compare": ràng buộc số/thời gian/danh mục: attr của biến `of`, op, value_number (hoặc value_text), unit
     (ngày, tháng, năm, giờ, %, đồng, triệu đồng, tỷ đồng, người...). Ví dụ "từ đủ 01 tháng trở lên" → attr thoi_han, op >=, 1, tháng.
   - So sánh với một thuộc tính/ngưỡng khác (không phải hằng số): value_attr = tên thuộc tính đem so, value_of = biến
     mang nó, hoặc "tham_so" nếu là ngưỡng do pháp luật quy định không gắn chủ thể (lương cơ sở, mức tối thiểu...);
     value_number = hệ số nhân (mặc định 1). Ví dụ "tiền lương bằng hoặc cao hơn tiền lương làm căn cứ đóng thấp nhất"
     → attr tien_luong, of P, op >=, value_attr tien_luong_can_cu_dong_thap_nhat, value_of tham_so, value_number 1.
     KHÔNG rút gọn thành "có tiền lương" hay so với value_text.
   - Điều kiện bắt buộc: alt_group = 0. Điều kiện thay thế nhau ("hoặc", "một trong các trường hợp"): cùng alt_group > 0,
     mỗi phương án một alt_option khác nhau (các điều kiện cùng alt_option là AND, các alt_option là OR).
   - KHÔNG bịa điều kiện không có trong văn bản. Điều kiện nêu ở câu dẫn của Khoản áp dụng cho các Điểm của Khoản đó.
   - Khi một đơn vị viết "đối tượng quy định tại điểm a ... + điều kiện riêng", chép lại các điều kiện của điểm a
     VÀ thêm đủ mọi điều kiện riêng (vd "làm việc không trọn thời gian" là một điều kiện atom).
   - Dùng lại vị từ đã có trong ontology khi cùng nghĩa, kể cả khi văn bản diễn đạt khác.
5. action (cho obligation/right/prohibition/procedure): hành vi {{pred, args}}; conclusion (cho definition/consequence):
   kết luận pháp lý {{pred, args, negated}}. Mọi biến trong action/conclusion phải xuất hiện trong variables.
6. formulas: thuộc tính tính toán, expression dùng tên thuộc tính và số, ví dụ "0.08 * tien_luong".
7. deadline: thời hạn thực hiện hành vi (amount, unit, from_event), ví dụ 90 ngày kể từ ngay_cap_gcn.
8. sanction: chế tài nếu có. exception_refs: tham chiếu NGUYÊN VĂN tới các quy định LOẠI TRỪ khỏi quy phạm này
   ("trừ trường hợp quy định tại khoản 7 Điều này", "không áp dụng đối với ... tại khoản 2" → "khoản 7 Điều này");
   nếu chính quy phạm này là ngoại lệ của một quy định khác thì ghi tham chiếu đó vào other_refs với tiền tố
   "ngoai_le_cua: " (vd "ngoai_le_cua: khoản 1 Điều này"); other_refs: các dẫn chiếu khác.
9. valid_from/valid_to: chỉ khi quy phạm có hiệu lực riêng khác văn bản (điều khoản chuyển tiếp), dạng YYYY-MM-DD.
10. quote: trích nguyên văn ngắn. Bỏ qua phạm vi điều chỉnh, giải thích chung chung không có quy phạm, hiệu lực thi hành.
11. Tên vị từ, loại, thuộc tính: tiếng Việt không dấu, snake_case. Tên biến: chữ HOA không dấu (P, E, NLD).
    Công thức chỉ dùng + - * / và min, max, round; thuộc tính của biến khác viết ten_thuoc_tinh(BIEN).

VĂN BẢN: {doc_title} — số {doc_number} ({doc_type}, hiệu lực từ {effective})
ĐIỀU {article}. {title}
Các đơn vị (mã đơn vị | nội dung):
{units}
"""


class Extractor:
    def __init__(self, model: str = MODEL):
        load_dotenv(ROOT / ".env")
        self.client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ.get("LLM_BASE_URL") or None)
        self.model = model
        CACHE.mkdir(parents=True, exist_ok=True)

    def ontology_summary(self, con, domain: str | None = None) -> tuple[str, str, str]:
        """The vocabulary given to the model: the domain's fixed vocabulary and shared names. Names added by earlier
        extractions are left out, otherwise every prompt would grow with the KB."""
        where = "WHERE origin='vocab' AND domain IN (?, 'chung')" if domain else ""
        arg = (domain,) if domain else ()
        types = ", ".join(f"{n}" + (f"⊂{p}" if p else "") for n, p in con.execute(
            f"SELECT name, parent FROM entity_types {where} ORDER BY name", arg))
        preds = []
        for name, arity in con.execute(f"SELECT name, arity FROM predicates {where} ORDER BY name", arg):
            args = ", ".join(f"{r}:{t}" for r, t in con.execute(
                "SELECT role, type FROM predicate_args WHERE pred=? ORDER BY position", (name,)))
            preds.append(f"{name}/{arity}({args})")
        attrs = ", ".join(f"{n} của {o}: {v}" + (f", {u}" if u else "") for n, o, v, u in con.execute(
            f"SELECT name, of_type, value_type, unit FROM attributes {where} ORDER BY name", arg))
        return types or "(chưa có)", "; ".join(preds) or "(chưa có)", attrs or "(chưa có)"

    def extract_article(self, con, doc: dict, units: list[dict], extra: str = "", onto: tuple | None = None) -> dict:
        """Norms of one article. If the answer does not fit in the output limit, the units are split in two halves
        (recursively) and the halves' answers merged."""
        types, preds, attrs = onto or self.ontology_summary(con)  # onto: precomputed, for calls from worker threads
        text = "\n".join(f"{u['unit_id']} | {u['text']}" for u in units)
        prompt = PROMPT.format(doc_title=doc["title"], doc_number=doc["number"], doc_type=doc["doc_type"],
                               effective=doc["effective_from"] or "?", article=units[0]["article"],
                               title=units[0]["title"], units=text, types=types, preds=preds, attrs=attrs) + extra
        key = hashlib.sha1(f"{PROMPT_VERSION}|{self.model}|{text}|{extra}".encode("utf-8")).hexdigest()
        f = CACHE / f"{key}.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))
        last = None
        for attempt in range(10):
            try:
                r = self.client.chat.completions.create(
                    model=self.model, temperature=0,
                    response_format={"type": "json_schema", "json_schema": {"name": "legal_norms", "strict": True,
                                                                            "schema": RESPONSE}},
                    messages=[{"role": "user", "content": prompt}])
                if r.choices[0].finish_reason == "length" and len(units) > 1:
                    half = len(units) // 2
                    parts = [self.extract_article(con, doc, units[:half], extra, onto),
                             self.extract_article(con, doc, units[half:], extra, onto)]
                    return {k: parts[0][k] + parts[1][k] for k in parts[0]}
                out = json.loads(r.choices[0].message.content)
                f.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
                return out
            except Exception as e:  # noqa: BLE001
                if "insufficient_quota" in str(e):
                    raise
                last = e
                time.sleep(min(60, 5 * 2 ** attempt))  # rate limits (tokens per minute) clear within a minute
        raise RuntimeError(f"extraction failed for {units[0]['unit_id']}: {last}")


def clear_units(con, unit_ids: set[str]) -> None:
    """Remove the norms of these units (before re-extracting their article)."""
    for (nid,) in con.execute(f"SELECT norm_id FROM norms WHERE unit_id IN ({','.join('?' * len(unit_ids))})",
                              sorted(unit_ids)).fetchall():
        for t in ("norm_variables", "norm_conditions", "norm_formulas", "norm_deadlines", "norm_sanctions",
                  "norm_references", "norms"):
            con.execute(f"DELETE FROM {t} WHERE norm_id=?", (nid,))
        con.execute("UPDATE norm_references SET target_norm_id=NULL WHERE target_norm_id=?", (nid,))


def store(con, out: dict, unit_ids: set[str], domain: str | None = None) -> list[str]:
    """Insert ontology additions (origin='extracted') and norms of one article response. Returns the new norm ids."""
    for t in out["entity_types"]:
        con.execute("INSERT OR IGNORE INTO entity_types VALUES (?,?,?,?,?)",
                    (canon_name(t["name"]), canon_name(t["parent"]) if t["parent"] else None, t["description_vi"],
                     domain, "extracted"))
    for p in out["predicates"]:
        name = canon_name(p["name"])
        if con.execute("SELECT 1 FROM predicates WHERE name=?", (name,)).fetchone():
            continue
        con.execute("INSERT INTO predicates VALUES (?,?,?,?,?,?)",
                    (name, len(p["args"]), p["kind"], p["description_vi"], domain, "extracted"))
        for i, a in enumerate(p["args"]):
            con.execute("INSERT INTO predicate_args VALUES (?,?,?,?)", (name, i, a["role"], canon_name(a["type"])))
    for a in out["attributes"]:
        con.execute("INSERT OR IGNORE INTO attributes VALUES (?,?,?,?,?,?,?)",
                    (canon_name(a["name"]), canon_name(a["of_type"]), a["value_type"], canon_unit(a["unit"])[0],
                     a["description_vi"], domain, "extracted"))
    def declare(pred, args, kind):  # a predicate used in a norm but not declared: arity from the use
        if pred and not con.execute("SELECT 1 FROM predicates WHERE name=?", (pred,)).fetchone():
            con.execute("INSERT INTO predicates VALUES (?,?,?,?,?,?)",
                        (pred, len(args), kind, "(tự khai báo từ cách dùng)", domain, "extracted"))

    ids = []
    for k, n in enumerate(out["norms"]):
        if not (n["action"] or n["conclusion"] or n["sanction"]):
            continue  # delegation ("... quy định chi tiết") or a statement without legal effect
        for c in n["conditions"]:
            if c["kind"] == "atom" and not c["pred"] and c["attr"]:  # comparison mislabelled as atom
                c["kind"] = "compare"
            if c["kind"] == "compare":
                c["of"] = c["of"] or n["subject"]
                c["attr"] = c["attr"] or ("tuoi" if canon_unit(c["unit"])[0] == "tuoi" else None)
                if not c["op"] and c["value_number"] is None and not c["value_text"] and not c["value_attr"]:
                    c.update(op="=", value_text="true")  # bare attribute: a boolean property
            if c["kind"] == "compare" and c["value_number"] is None and c["value_text"] in ("true", "false"):
                holds = (c["value_text"] == "true") == (c["op"] != "!=")  # boolean property: an atom on the variable
                c.update(kind="atom", pred=c["attr"], args=[c["of"]], negated=c["negated"] == holds, value_text=None)
            if c["kind"] == "atom":
                declare(canon_name(c["pred"]), c["args"], "property")
        if n["action"]:
            declare(canon_name(n["action"]["pred"]), n["action"]["args"], "action")
        if n["conclusion"]:
            declare(canon_name(n["conclusion"]["pred"]), n["conclusion"]["args"], "status")
        unit = n["unit_id"] if n["unit_id"] in unit_ids else sorted(unit_ids)[0]
        nid = f"{unit}#{k}"
        act, concl = n["action"], n["conclusion"]
        for t in ("norm_variables", "norm_conditions", "norm_formulas", "norm_deadlines", "norm_sanctions",
                  "norm_references", "norms"):  # re-running an article replaces its norms
            con.execute(f"DELETE FROM {t} WHERE norm_id=?", (nid,))
        con.execute("""INSERT INTO norms (norm_id, unit_id, modality, subject_var, bearer_var, beneficiary_var, action_pred,
                       action_args, conclusion_pred, conclusion_args, conclusion_negated, valid_from, valid_to,
                       validity_note, quote) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (nid, unit, n["modality"], n["subject"], n["bearer"], n["beneficiary"],
                     canon_name(act["pred"]) if act else None, ",".join(act["args"]) if act else None,
                     canon_name(concl["pred"]) if concl else None, ",".join(concl["args"]) if concl else None,
                     int(concl["negated"]) if concl else None, n["valid_from"], n["valid_to"], n["validity_note"],
                     n["quote"]))
        for v in n["variables"]:
            con.execute("INSERT OR IGNORE INTO norm_variables VALUES (?,?,?)", (nid, v["name"], canon_name(v["type"])))
        for c in n["conditions"]:
            unit_c, factor = canon_unit(c["unit"])
            if c["value_attr"]:  # attribute vs attribute: value_number is a multiplier, no unit conversion
                factor = 1.0
            val = c["value_number"] * factor if c["value_number"] is not None else None
            con.execute("""INSERT INTO norm_conditions (norm_id, alt_group, alt_option, kind, pred, args, negated, attr,
                           of_var, op, value_num, value_text, unit, value_attr, value_of)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (nid, c["alt_group"], c["alt_option"], c["kind"], canon_name(c["pred"]) if c["pred"] else None,
                         ",".join(c["args"]), int(c["negated"]), canon_name(c["attr"]) if c["attr"] else None, c["of"],
                         c["op"], val, c["value_text"], unit_c, canon_name(c["value_attr"]),
                         c["value_of"] if c["value_of"] in {v["name"] for v in n["variables"]} else canon_name(c["value_of"])))
        for fm in n["formulas"]:
            con.execute("INSERT INTO norm_formulas VALUES (?,?,?,?,?)",
                        (nid, canon_name(fm["target_attr"]), fm["of"], fm["expression"], canon_unit(fm["unit"])[0]))
        if n["deadline"]:
            u, factor = canon_unit(n["deadline"]["unit"])
            con.execute("INSERT INTO norm_deadlines VALUES (?,?,?,?)",
                        (nid, n["deadline"]["amount"] * factor, u, canon_name(n["deadline"]["from_event"])))
        if n["sanction"]:
            s = n["sanction"]
            u, factor = canon_unit(s["unit"])
            con.execute("INSERT INTO norm_sanctions VALUES (?,?,?,?,?,?)",
                        (nid, s["kind"], s["min_amount"] * factor if s["min_amount"] is not None else None,
                         s["max_amount"] * factor if s["max_amount"] is not None else None, u, s["text"]))
        for r in n["exception_refs"]:
            con.execute("INSERT INTO norm_references (norm_id, ref_kind, ref_text) VALUES (?,?,?)", (nid, "has_exception", r))
        for r in n["other_refs"]:
            kind = "exception_of" if r.lower().startswith("ngoai_le_cua:") else "refers_to"
            con.execute("INSERT INTO norm_references (norm_id, ref_kind, ref_text) VALUES (?,?,?)",
                        (nid, kind, r.split(":", 1)[1].strip() if kind == "exception_of" else r))
        ids.append(nid)
    return ids
