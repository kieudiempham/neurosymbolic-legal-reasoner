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
import time
from concurrent.futures import ThreadPoolExecutor

from .compile import write_and_check
from .db import DB_FILE, connect
from .normalize import document_relations, link_references, reference_predicates, repair_norms
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
            con.execute("INSERT OR REPLACE INTO units VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (u.unit_id, u.doc_number, u.chapter, u.article, u.clause, u.point, parent, u.title, u.text,
                         u.target_doc, u.valid_from, None))
            if u.target_doc:
                con.execute("INSERT OR IGNORE INTO doc_relations VALUES (?,?,?)", (u.doc_number, "amends", u.target_doc))
    # the old wording of an amended article stops applying when the new one takes effect
    for uid, frm in con.execute("SELECT unit_id, valid_from FROM units WHERE target_doc IS NOT NULL").fetchall():
        old = uid.split("@", 1)[0]
        con.execute("UPDATE units SET valid_to=? WHERE (unit_id=? OR unit_id LIKE ?) AND target_doc IS NULL "
                    "AND (valid_to IS NULL OR valid_to > ?)", (frm, old, old + ".%", frm))
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


def extract_document(con, ex, doc_id: str, articles: list[str], workers: int) -> None:
    """Extract the norms of a document, all articles in parallel (the ontology given to the model is the one in the
    DB when the document starts), then store them, re-ask for skipped units and align new predicates."""
    from .align import align
    from .extract import clear_units, store

    doc = dict(zip(["doc_id", "number", "title", "doc_type", "issuer", "rank", "domain", "issued", "effective_from",
                    "effective_to", "source_file"],
                   con.execute("SELECT doc_id, number, title, doc_type, issuer, rank, domain, issued, effective_from, "
                               "effective_to, source_file FROM documents WHERE doc_id=?", (doc_id,)).fetchone()))
    groups = {}
    for r in con.execute("SELECT unit_id, article, title, text, parent_id FROM units WHERE doc_number=? ORDER BY rowid",
                         (doc["number"],)):
        u = dict(zip(["unit_id", "article", "title", "text", "parent"], r))
        if not articles or u["article"] in articles:
            groups.setdefault(u["article"], []).append(u)
    names = lambda t: {n for (n,) in con.execute(f"SELECT name FROM {t}")}  # noqa: E731
    before = {k: names(t) for k, t in (("pred", "predicates"), ("type", "entity_types"), ("attr", "attributes"))}
    onto = ex.ontology_summary(con, doc["domain"])
    t0 = time.time()

    def run(jobs: dict[str, tuple[list[dict], str]]) -> dict:
        with ThreadPoolExecutor(workers) as pool:
            futs = {a: pool.submit(ex.extract_article, None, doc, us, extra, onto) for a, (us, extra) in jobs.items()}
            out = {}
            for a, f in futs.items():  # one failing article is reported and skipped (re-run the document later)
                try:
                    out[a] = f.result()
                except RuntimeError as e:
                    print(f"  skipped Điều {a}: {str(e)[:300]}", flush=True)
            return out

    for a, us in groups.items():
        clear_units(con, {u["unit_id"] for u in us})
    n = 0
    for a, out in run({a: (us, "") for a, us in groups.items()}).items():
        n += len(store(con, out, {u["unit_id"] for u in groups[a]}, doc["domain"]))
    missed = {a: m for a, us in groups.items() if (m := uncovered(con, us))}
    for _ in range(3):  # long articles: the model stops early, so re-ask for the skipped units while it helps
        if not missed:
            break
        jobs = {}
        for a, ms in missed.items():
            by_id = {u["unit_id"]: u for u in groups[a]}
            jobs[a] = ([{**u, "text": (f"(câu dẫn: {by_id[u['parent']]['text']}) " if u["parent"] in by_id else "")
                         + u["text"]} for u in ms], RETRY_NOTE)
        for a, out in run(jobs).items():
            n += len(store(con, out, {u["unit_id"] for u in missed[a]}, doc["domain"]))
        still = {a: m for a in missed if (m := uncovered(con, groups[a]))}
        if sum(map(len, still.values())) == sum(map(len, missed.values())):
            break
        missed = still
    new = {k: names(t) - before[k] for k, t in (("pred", "predicates"), ("type", "entity_types"),
                                                 ("attr", "attributes"))}
    links = align(con, ex.client, ex.model, new, doc["domain"], workers)
    con.commit()
    print(f"{doc['number']}: {len(groups)} articles, {n} norms, +{len(new['pred'])} predicates, "
          f"+{len(new['type'])} types, +{len(new['attr'])} attributes, {links} links to the vocabulary, "
          f"{sum(map(len, missed.values()))} units without norms, {time.time() - t0:.0f}s", flush=True)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--structure", action="store_true", help="(re)load documents and units for all documents")
    ap.add_argument("--doc", nargs="*", default=[], help="document ids (file stems) to extract norms from")
    ap.add_argument("--all", action="store_true", help="extract norms from every document")
    ap.add_argument("--vocab", action="store_true", help="draft the fixed vocabulary of each domain (before extraction)")
    ap.add_argument("--articles", nargs="*", default=[], help="article numbers (default: all of the document)")
    ap.add_argument("--model", default=None)
    ap.add_argument("--workers", type=int, default=16, help="parallel LLM requests")
    ap.add_argument("--canon", nargs="*", default=None, metavar="PASS",
                    help="map names onto the vocabulary corpus-wide (after extraction); passes: types attrs chains vocab")
    ap.add_argument("--canon-model", default=None)
    args = ap.parse_args()
    con = connect()
    if args.structure or not con.execute("SELECT 1 FROM documents LIMIT 1").fetchone():
        load_structure(con)
    if args.vocab:
        from .vocab import build_vocabularies

        build_vocabularies(con, [d for (d,) in con.execute("SELECT DISTINCT domain FROM documents ORDER BY domain")])
    docs = [d for (d,) in con.execute("SELECT doc_id FROM documents ORDER BY domain, rank, doc_id")] if args.all \
        else args.doc
    if docs:
        from .extract import MODEL, Extractor

        ex = Extractor(args.model or MODEL)
        for d in docs:
            extract_document(con, ex, d, args.articles, args.workers)
        print("linked references:", link_references(con))
        con.commit()
    print("repairs:", repair_norms(con), "condition refs:", reference_predicates(con))
    con.commit()
    if args.canon is not None:
        from .canon import CANON_MODEL, PASSES, canonicalise

        canonicalise(con, args.workers, tuple(args.canon) or PASSES, args.canon_model or CANON_MODEL)
    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in
              ("documents", "doc_relations", "units", "entity_types", "predicates", "predicate_links", "attributes", "norms",
               "norm_conditions", "norm_references", "norm_formulas", "norm_deadlines", "norm_sanctions")}
    report = write_and_check(con)
    print(json.dumps({"db": str(DB_FILE), "tables": counts, **report}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
