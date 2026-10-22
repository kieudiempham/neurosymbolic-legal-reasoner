"""Fixed vocabulary per legal domain, drafted by an LLM before norm extraction.

For each domain, document by document (laws first), the model reads the title and the opening of every article and
adds to the domain's controlled vocabulary only the names still missing: entity types (with is-a parents), predicates (relations, properties, actions, legal
statuses, with typed role arguments) and attributes (with value type and unit). It is stored in entity_types /
predicates / predicate_args / attributes with origin='vocab'; extraction must then use these names, and any name it
still has to add is stored with origin='extracted' (so the two can be counted apart).
"""

from __future__ import annotations

import hashlib
import json
import re
import time

from .extract import CACHE, Extractor, _obj, _opt, _s
from .normalize import canon_name, canon_unit

VOCAB_VERSION = "vocab-v2"
VOCAB_MODEL = "gpt-4.1"
DOMAIN_VI = {"labor": "lao động, bảo hiểm xã hội", "enterprise": "doanh nghiệp", "tax": "thuế, hóa đơn"}

RESPONSE = _obj({
    "entity_types": {"type": "array", "items": _obj({"name": _s, "parent": _opt(_s), "description_vi": _s})},
    "predicates": {"type": "array", "items": _obj({
        "name": _s, "kind": {"type": "string", "enum": ["relation", "property", "action", "status"]},
        "description_vi": _s, "args": {"type": "array", "items": _obj({"role": _s, "type": _s})}})},
    "attributes": {"type": "array", "items": _obj({
        "name": _s, "of_type": _s, "value_type": {"type": "string", "enum": ["number", "date", "enum", "text", "boolean"]},
        "unit": _opt(_s), "description_vi": _s})}})

PROMPT = """Bạn thiết kế BỘ TỪ VỰNG CỐ ĐỊNH (ontology) cho cơ sở tri thức pháp luật Việt Nam lĩnh vực {domain_vi}.
Từ vựng này sẽ được dùng để mã hóa MỌI quy phạm của các văn bản dưới đây thành luật logic bậc nhất, nên phải
đủ phủ, không trùng nghĩa, và ổn định.

TỪ VỰNG ĐÃ CÓ CỦA LĨNH VỰC (dùng lại; KHÔNG khai báo lại, KHÔNG tạo tên mới trùng nghĩa với tên đã có):
{existing}

VĂN BẢN CẦN BỔ SUNG TỪ VỰNG (tên Điều — đoạn đầu):
{articles}

CHỈ trả các tên MỚI cần thêm để mã hóa văn bản này. Phải có đủ cả ba phần: entity_types, predicates, attributes.

YÊU CẦU:
1. entity_types: các loại chủ thể và đối tượng pháp lý (người, tổ chức, cơ quan, hợp đồng, quỹ, hồ sơ, hóa đơn,
   khoản thu nhập, chế độ, giấy tờ...), mỗi loại có parent (loại cha) để tạo cây phân cấp; gốc là ca_nhan, to_chuc,
   co_quan_nha_nuoc, giay_to, tai_san, khoan_tien, su_kien hoặc loại chung đã có. Loại chủ thể KHÔNG được khai báo lại
   thành vị từ một ngôi (dùng loại cho "là người lao động", không tạo vị từ la_nguoi_lao_dong).
2. predicates:
   - relation: quan hệ giữa ≥2 thực thể (vd lam_viec_theo_hop_dong(nguoi_lao_dong, nguoi_su_dung_lao_dong, hop_dong)).
   - property: tình trạng của một thực thể không phải loại (vd lam_viec_khong_tron_thoi_gian(nguoi_lao_dong)).
   - action: hành vi có chủ thể thực hiện; đối số đầu là người thực hiện, sau đó đối tượng, người nhận
     (vd dong_bao_hiem_xa_hoi(nguoi_dong, nguoi_duoc_dong, quy)). Ưu tiên MỘT hành vi tổng quát có đối số hơn nhiều
     hành vi chi tiết (không tách dong_bhxh_vao_quy_huu_tri / dong_bhxh_vao_quy_om_dau: dùng đối số quy).
   - status: tư cách / hệ quả pháp lý được kết luận (vd thuoc_dien_tham_gia_bhxh_bat_buoc(nguoi_lao_dong),
     duoc_mien_thue(nguoi_nop_thue, khoan_thu_nhap)).
   Mỗi đối số có role (vai trò) và type (một entity_type).
3. attributes: thuộc tính số / ngày / danh mục của một loại, có đơn vị (vd tien_luong của nguoi_lao_dong: number, đồng;
   thoi_han của hop_dong: number, tháng; loai_hop_dong: enum). Ngưỡng do pháp luật quy định không gắn chủ thể
   (lương cơ sở, mức lương tối thiểu...) là thuộc tính của loại tham_so.
4. Tên: tiếng Việt không dấu, snake_case, ngắn mà rõ; viết tắt thống nhất (bhxh, bhyt, bhtn, gtgt, tndn, tncn).
   KHÔNG có hai tên cùng nghĩa. description_vi: một câu.
5. Quy mô cho MỘT văn bản: thường 10–60 loại, 30–150 vị từ, 20–100 thuộc tính mới (ít hơn nếu từ vựng đã đủ);
   vị từ là phần quan trọng nhất: mọi quan hệ, hành vi, tình trạng, tư cách pháp lý trong các Điều đều phải có tên.
"""


def _articles(con, domain: str, number_only: str | None = None, per_article: int = 300) -> str:
    lines = []
    for number, title in con.execute("SELECT number, title FROM documents WHERE domain=? ORDER BY rank, number",
                                     (domain,)).fetchall():
        if number_only and number != number_only:
            continue
        lines.append(f"\n## {title} ({number})")
        for art, atitle, text in con.execute(
                "SELECT article, title, group_concat(text, ' ') FROM (SELECT article, title, text FROM units "
                "WHERE doc_number=? ORDER BY rowid) GROUP BY article ORDER BY CAST(article AS INTEGER)", (number,)):
            lines.append(f"Điều {art}. {atitle} — {' '.join((text or '').split())[:per_article]}")
    return "\n".join(lines)


def _existing(con, domain: str) -> str:
    """Only the domain's own vocabulary, so a domain's prompts (and their cache keys) do not depend on the order in
    which the domains are drafted."""
    w = "origin='vocab' AND domain IN (?, 'chung')"  # names shared with another domain stay visible
    types = ", ".join(n + (f"⊂{p}" if p else "") for n, p in con.execute(
        f"SELECT name, parent FROM entity_types WHERE {w} ORDER BY name", (domain,)))
    preds = ", ".join(f"{n}/{a}" for n, a in con.execute(
        f"SELECT name, arity FROM predicates WHERE {w} ORDER BY name", (domain,)))
    attrs = ", ".join(n for (n,) in con.execute(f"SELECT name FROM attributes WHERE {w} ORDER BY name", (domain,)))
    return f"- loại: {types or '(chưa có)'}\n- vị từ: {preds or '(chưa có)'}\n- thuộc tính: {attrs or '(chưa có)'}"


def draft(con, domain: str, number: str, model: str = VOCAB_MODEL) -> dict:
    prompt = PROMPT.format(domain_vi=DOMAIN_VI.get(domain, domain), existing=_existing(con, domain),
                           articles=_articles(con, domain, number))
    key = hashlib.sha1(f"{VOCAB_VERSION}|{model}|{prompt}".encode("utf-8")).hexdigest()
    f = CACHE / f"vocab_{domain}_{key}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    client = Extractor(model).client
    penalty = 0.0
    for attempt in range(6):
        try:
            r = client.chat.completions.create(
                model=model, temperature=0, max_completion_tokens=32000, frequency_penalty=penalty,
                response_format={"type": "json_schema", "json_schema": {"name": "vocabulary", "strict": True,
                                                                        "schema": RESPONSE}},
                messages=[{"role": "user", "content": prompt}])
            out = json.loads(r.choices[0].message.content)
            if degenerate(out) and penalty == 0.0:  # the model fell into a numbered list: ask again, penalising repeats
                penalty = 0.4
                continue
            f.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
            return out
        except Exception as e:  # noqa: BLE001
            if "insufficient_quota" in str(e):
                raise
            time.sleep(min(60, 3 * 2 ** attempt))
    raise RuntimeError("vocabulary drafting failed")


_NUMBERED = re.compile(r"_\d+$")


def degenerate(out: dict) -> bool:
    """A response that degenerated into a numbered list (noi_lam_viec_bi_xu_ly_khac_208, _209, ...)."""
    return sum(bool(_NUMBERED.search(x["name"])) for k in ("entity_types", "predicates", "attributes")
               for x in out[k]) >= 5


def store_vocab(con, out: dict, domain: str) -> dict:
    """Insert vocabulary of a domain (origin='vocab'); a name already in another domain becomes shared ('chung').
    Numbered names (residue of a degenerate response) are dropped."""
    out = {k: [x for x in v if not _NUMBERED.search(x["name"])] for k, v in out.items()}
    def put(table, name, row):
        dom = con.execute(f"SELECT domain FROM {table} WHERE name=?", (name,)).fetchone()
        if dom:
            if dom[0] not in (domain, "chung"):
                con.execute(f"UPDATE {table} SET domain='chung' WHERE name=?", (name,))
            return False
        con.execute(f"INSERT INTO {table} VALUES ({','.join('?' * len(row))})", row)
        return True

    n = {"types": 0, "predicates": 0, "attributes": 0}
    for t in out["entity_types"]:
        name = canon_name(t["name"])
        n["types"] += put("entity_types", name, (name, canon_name(t["parent"]) if t["parent"] else None,
                                                 t["description_vi"], domain, "vocab"))
    for p in out["predicates"]:
        name = canon_name(p["name"])
        if put("predicates", name, (name, len(p["args"]), p["kind"], p["description_vi"], domain, "vocab")):
            n["predicates"] += 1
            for i, a in enumerate(p["args"]):
                con.execute("INSERT OR REPLACE INTO predicate_args VALUES (?,?,?,?)",
                            (name, i, a["role"], canon_name(a["type"])))
    for a in out["attributes"]:
        name = canon_name(a["name"])
        n["attributes"] += put("attributes", name, (name, canon_name(a["of_type"]), a["value_type"],
                                                    canon_unit(a["unit"])[0], a["description_vi"], domain, "vocab"))
    con.commit()
    return n


def build_domain(domain: str) -> None:
    from .db import connect

    con = connect()  # one connection per thread
    for (number,) in con.execute("SELECT number FROM documents WHERE domain=? ORDER BY rank, number",
                                 (domain,)).fetchall():
        t0 = time.time()
        n = store_vocab(con, draft(con, domain, number), domain)
        print(f"vocabulary {domain} {number}: +{n['types']} types, +{n['predicates']} predicates, "
              f"+{n['attributes']} attributes, {time.time() - t0:.0f}s", flush=True)


def build_vocabularies(con, domains: list[str]) -> None:
    """Domains one after the other in a fixed order, so the prompts (and their cache keys) are reproducible."""

    for t in ("predicate_args", "predicates", "entity_types", "attributes"):  # redraft from scratch (cached)
        if t == "predicate_args":
            con.execute("DELETE FROM predicate_args WHERE pred IN (SELECT name FROM predicates WHERE origin='vocab')")
        else:
            con.execute(f"DELETE FROM {t} WHERE origin='vocab'")
    con.commit()
    for d in domains:
        build_domain(d)
