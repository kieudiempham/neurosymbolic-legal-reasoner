"""Build the legal KB database end to end.

    # structure only (all 18 documents, rule-based, no API)
    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.build --structure
    # + norm extraction for selected articles (LLM), linking, compilation
    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.build --doc 10_bao_hiem_xa_hoi_41_2024_QH15 --articles 2 3
    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.build --doc 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh --articles 47
"""

from __future__ import annotations

import argparse
import json
import sys

from .compile import write_and_check
from .db import DB_FILE, connect
from .normalize import document_relations, link_references
from .structure import load_documents, read_document


def load_structure(con, only=None) -> None:
    from diagnosis.kbx.corpus import CORPUS

    for doc, units in load_documents(only):
        con.execute("INSERT OR REPLACE INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (doc.doc_id, doc.number, doc.title, doc.doc_type, doc.issuer, doc.rank, doc.domain, doc.issued,
                     doc.effective_from, None, doc.source_file))
        _, text = read_document(CORPUS / doc.domain / doc.doc_id, doc.domain)
        document_relations(con, doc.number, text, doc.replaces)
        for u in units:
            parent = u.unit_id.rsplit(".", 1)[0] if "." in u.unit_id.split(":", 1)[1] else None
            con.execute("INSERT OR REPLACE INTO units VALUES (?,?,?,?,?,?,?,?,?)",
                        (u.unit_id, u.doc_number, u.chapter, u.article, u.clause, u.point, parent, u.title, u.text))
    con.commit()


RETRY_NOTE = """
LƯỢT BỔ SUNG: các đơn vị trên CHƯA có quy phạm nào trong cơ sở tri thức. Với MỖI đơn vị có nội dung quy phạm
(nghĩa vụ, quyền, cấm, định nghĩa, hệ quả, loại trừ, quy tắc ưu tiên khi thuộc nhiều đối tượng, thủ tục) phải trả ít
nhất một norm với đúng unit_id của đơn vị đó; chỉ bỏ qua đơn vị thuần giao quyền quy định chi tiết cho cơ quan khác.
Một Điểm là trường hợp loại trừ của câu dẫn thì mã hoá thành norm riêng và ghi "ngoai_le_cua: <câu dẫn>" trong other_refs.
"""


def uncovered(con, units: list[dict]) -> list[dict]:
    """Leaf units with real content and no norm on themselves or on any enclosing unit."""
    with_norms = {u for (u,) in con.execute("SELECT DISTINCT unit_id FROM norms")}
    parents = {u["parent"] for u in units}
    out = []
    for u in units:
        if u["unit_id"] in parents or len(u["text"] or "") < 40:
            continue
        chain, x = [], u["unit_id"]
        while x:
            chain.append(x)
            x = next((v["parent"] for v in units if v["unit_id"] == x), None)
        if not with_norms & set(chain):
            out.append(u)
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--structure", action="store_true", help="(re)load documents and units for all documents")
    ap.add_argument("--doc", help="document id (file stem) to extract norms from")
    ap.add_argument("--articles", nargs="*", default=[], help="article numbers (default: all of the document)")
    ap.add_argument("--model", default=None)
    args = ap.parse_args()
    con = connect()
    if args.structure or not con.execute("SELECT 1 FROM documents LIMIT 1").fetchone():
        load_structure(con)
    if args.doc:
        from .align import align
        from .extract import MODEL, Extractor, clear_units, store

        ex = Extractor(args.model or MODEL)
        doc = dict(zip(["doc_id", "number", "title", "doc_type", "issuer", "rank", "domain", "issued", "effective_from",
                        "effective_to", "source_file"],
                       con.execute("SELECT * FROM documents WHERE doc_id=?", (args.doc,)).fetchone()))
        arts = args.articles or [a for (a,) in con.execute(
            "SELECT DISTINCT article FROM units WHERE doc_number=? ORDER BY CAST(article AS INTEGER)", (doc["number"],))]
        for a in arts:
            units = [dict(zip(["unit_id", "article", "title", "text", "parent"], r)) for r in con.execute(
                "SELECT unit_id, article, title, text, parent_id FROM units WHERE doc_number=? AND article=? ORDER BY rowid",
                (doc["number"], a))]
            if not units:
                print("no units for article", a)
                continue
            before = {p for (p,) in con.execute("SELECT name FROM predicates")}
            clear_units(con, {u["unit_id"] for u in units})
            out = ex.extract_article(con, doc, units)
            ids = store(con, out, ex.model, {u["unit_id"] for u in units})
            missed = uncovered(con, units)
            by_id = {u["unit_id"]: u for u in units}
            for _ in range(3):  # long articles: the model stops early, so re-ask for the skipped units while it helps
                if not missed:
                    break
                retry = [{**u, "text": (f"(câu dẫn: {by_id[u['parent']]['text']}) " if u["parent"] in by_id else "")
                          + u["text"]} for u in missed]
                ids += store(con, ex.extract_article(con, doc, retry, RETRY_NOTE), ex.model,
                             {u["unit_id"] for u in missed})
                still = uncovered(con, units)
                if len(still) == len(missed):
                    break
                missed = still
            new = {p for (p,) in con.execute("SELECT name FROM predicates")} - before
            links = align(con, ex.client, ex.model, new)
            con.commit()
            print(f"Điều {a}: {len(ids)} norms, +{len(new)} predicates, {links} predicate links, "
                  f"units without norms: {[u['unit_id'] for u in missed]}")
        print("linked references:", link_references(con))
        con.commit()
    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in
              ("documents", "doc_relations", "units", "entity_types", "predicates", "predicate_links", "attributes", "norms",
               "norm_conditions", "norm_references", "norm_formulas", "norm_deadlines", "norm_sanctions")}
    report = write_and_check(con)
    print(json.dumps({"db": str(DB_FILE), "tables": counts, **report}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
