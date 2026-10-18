"""Question-driven KB builder: keep only the articles a dataset actually relies on.

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.kbx.build_kb "data/dataset/*.jsonl" [--name kb_dataset]

Steps
1. collect (document, article) pairs from each item's legal_basis and reasoning_chain;
2. add articles referenced by exception_to of the selected rules (one hop, same document);
3. take reviewed rules where available (BHXH), draft condition rules otherwise;
4. write data/diag/<name>.yaml + data/diag/<name>_vocabulary.yaml (loadable by kb.load_kb),
   data/diag/<name>_scope.json, and review batches for the draft rules
   (data/diag/kb_full_draft/review_<name>/batches/*.md, same format as the BHXH review).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from ..dataset import load_items
from .corpus import ROOT, load_corpus

DRAFT = ROOT / "data" / "diag" / "kb_full_draft"
DIAG = ROOT / "data" / "diag"

# (pattern found in a free-text document name, doc_id prefix in the corpus)
DOC_ALIASES = [
    (r"41\s*/\s*2024", "10_bao_hiem_xa_hoi"),
    (r"158\s*/\s*2025", "11_nghi_dinh_158"),
    (r"45\s*/\s*2019|bộ luật lao động|blld", "08_luat_lao_dong"),
    (r"145\s*/\s*2020", "09_nghi_dinh_145"),
    (r"vbhn|luật doanh nghiệp|59\s*/\s*2020", "01_luat_doanh_nghiep"),
    (r"168\s*/\s*2025", "02_nghi_dinh_dang_ky_doanh_nghiep"),
    (r"sửa đổi.*doanh nghiệp|76\s*/\s*2025", "03_sua_doi"),
    (r"108\s*/\s*2025|quản lý thuế", "01_luat_quan_ly_thue"),
    (r"126\s*/\s*2020", "02_nghi_dinh_126"),
    (r"123\s*/\s*2020", "03_nghi_dinh_123"),
    (r"48\s*/\s*2024|thuế giá trị gia tăng|gtgt", "04_luat_thue_GTGT"),
    (r"181\s*/\s*2025", "05_nghi_dinh_181"),
    (r"67\s*/\s*2025|thu nhập doanh nghiệp|tndn", "06_luat_TNDN"),
    (r"320\s*/\s*2025", "07_nghi_dinh_320"),
    (r"70\s*/\s*2025", "08_70_2025"),
    (r"32\s*/\s*2025", "09_32_2025"),
    (r"69\s*/\s*2025", "10_69_2025"),
    (r"71\s*/\s*2014", "11_ 71_2014"),
]
_ART = re.compile(r"Điều\s+(\d+[a-zđ]?)", re.I)


def resolve_doc(name: str, doc_ids: list[str]) -> str | None:
    low = name.lower()
    for pat, prefix in DOC_ALIASES:
        if re.search(pat, low):
            for d in doc_ids:
                if d.startswith(prefix):
                    return d
    return None


def wanted_articles(items: list[dict], doc_ids: list[str]) -> tuple[set[tuple[str, str]], list[str]]:
    want, unresolved = set(), []
    for it in items:
        for lb in it.get("legal_basis") or []:
            d = resolve_doc(str(lb.get("doc", "")), doc_ids)
            art = str(lb.get("article", "")).strip()
            m = _ART.search(art) if not art.isdigit() else None
            art = m.group(1) if m else art
            if d and art:
                want.add((d, art))
            elif lb.get("doc"):
                unresolved.append(str(lb.get("doc")))
        for step in it.get("reasoning_chain") or []:
            # "... [Điều 2 khoản 1 điểm a, Luật BHXH 41/2024]"
            for br in re.findall(r"\[([^\]]+)\]", step):
                m = _ART.search(br)
                d = resolve_doc(br, doc_ids)
                if m and d:
                    want.add((d, m.group(1)))
    return want, unresolved


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--name", default="kb_dataset")
    args = ap.parse_args()

    items = load_items(args.paths)
    arts = {(a.doc_id, a.number): a for a in load_corpus()}
    doc_ids = sorted({d for d, _ in arts})
    want, unresolved = wanted_articles(items, doc_ids)

    draft = [json.loads(l) for l in (DRAFT / "rules.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    reviewed_path = DRAFT / "rules_bhxh_reviewed.jsonl"
    reviewed = [json.loads(l) for l in reviewed_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    # reviewed rules may lack location fields: recover them from the draft rule (or the split parent)
    loc = {r["id"]: (r["doc_id"], r["article"]) for r in draft}
    for r in reviewed:
        if not r.get("doc_id") or not r.get("article"):
            src = loc.get(r["id"]) or loc.get(r.get("split_from", ""))
            if src:
                r["doc_id"], r["article"] = src
    reviewed = [r for r in reviewed if r.get("doc_id")]
    reviewed_docs = {r["doc_id"] for r in reviewed}

    # one hop along exception_to references inside the same document
    by_art = defaultdict(list)
    for r in draft:
        by_art[(r["doc_id"], r["article"])].append(r)
    for d, a in list(want):
        for r in by_art.get((d, a), []):
            m = _ART.search(r.get("exception_to") or "")
            if m and (d, m.group(1)) in arts:
                want.add((d, m.group(1)))

    selected, from_reviewed, to_review = [], 0, defaultdict(list)
    for d, a in sorted(want):
        if d in reviewed_docs:
            rs = [r for r in reviewed if r["doc_id"] == d and r["article"] == a]
            from_reviewed += len(rs)
        else:
            rs = [dict(r, review_status="draft") for r in by_art.get((d, a), []) if r["type"] == "condition"]
            if rs:
                to_review[(d, a)] = rs
        selected += rs

    # vocabulary: curated BHXH < draft vocabulary < dataset declarations (later sources only fill gaps)
    vocab = dict(yaml.safe_load((DIAG / "vocabulary.yaml").read_text(encoding="utf-8"))["predicates"])
    draft_vocab = yaml.safe_load((DRAFT / "vocabulary.yaml").read_text(encoding="utf-8"))["predicates"]
    for it in items:
        for np in it.get("new_predicates") or []:
            vocab.setdefault(np["pred"], {k: np.get(k, "") for k in ("kind", "template_pos", "template_neg", "ask")})
    used = {p.lstrip("~") for r in selected for p in [*r["premises"], r["conclusion"]]}
    undeclared = []
    for p in sorted(used - set(vocab)):
        v = draft_vocab.get(p)
        if v and v.get("template_pos"):
            vocab[p] = {k: v.get(k, "") for k in ("kind", "template_pos", "template_neg", "ask")}
        else:
            undeclared.append(p)
    concluded = {r["conclusion"].lstrip("~") for r in selected}
    for p in used:
        if p in vocab and not vocab[p].get("kind"):
            vocab[p]["kind"] = "derived" if p in concluded else "input"
    for p in undeclared:  # keep the KB loadable; flagged in the scope report for the reviewer
        vocab[p] = {"kind": "derived" if p in concluded else "input", "template_pos": p.replace("_", " "),
                    "template_neg": "không " + p.replace("_", " "), "ask": "", "origin": "auto_placeholder"}

    ids = {r["id"] for r in selected}
    exc = []
    rel = yaml.safe_load((DRAFT / "relations.yaml").read_text(encoding="utf-8")) or {}
    for a, b in rel.get("exception_of") or []:
        if a in ids and b in ids:
            exc.append([a, b])
    kb_yaml = {
        "rules": [{"id": r["id"], "premises": r["premises"], "conclusion": r["conclusion"],
                   "source": r["source"], "basis": r.get("review_status", "draft")} for r in selected],
        "exception_of": exc,
        "priority_over": [],
    }
    (DIAG / f"{args.name}.yaml").write_text(yaml.safe_dump(kb_yaml, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (DIAG / f"{args.name}_vocabulary.yaml").write_text(
        yaml.safe_dump({"predicates": vocab}, allow_unicode=True, sort_keys=True), encoding="utf-8")

    rev_dir = DRAFT / f"review_{args.name}" / "batches"
    rev_dir.mkdir(parents=True, exist_ok=True)
    batch, n, k = [], 0, 0
    keys = sorted(to_review)

    def flush():
        nonlocal batch, n, k
        if not batch:
            return
        with open(rev_dir / f"batch_{k:02d}.md", "w", encoding="utf-8") as fh:
            for key in batch:
                art = arts[key]
                fh.write(f"\n\n######## {art.doc_id} — Điều {art.number}. {art.title}\n[NGUYÊN VĂN]\n{art.text}\n\n[RULES]\n")
                for r in to_review[key]:
                    fh.write(json.dumps({x: r[x] for x in ("id", "type", "premises", "conclusion", "source",
                                                           "exception_to", "quote")}, ensure_ascii=False) + "\n")
        batch, n, k = [], 0, k + 1

    for key in keys:
        batch.append(key)
        n += len(to_review[key])
        if n >= 110:
            flush()
    flush()

    scope = {
        "items": len(items), "articles": len(want),
        "articles_by_doc": dict(Counter(d for d, _ in want)),
        "rules_selected": len(selected), "rules_from_reviewed_kb": from_reviewed,
        "rules_needing_review": sum(len(v) for v in to_review.values()), "review_batches": k,
        "exception_of": len(exc), "predicates": len(vocab), "undeclared_predicates_placeholder": len(undeclared),
        "unresolved_document_names": dict(Counter(unresolved)),
        "outputs": {"kb": f"data/diag/{args.name}.yaml", "vocabulary": f"data/diag/{args.name}_vocabulary.yaml",
                    "review_batches": str(rev_dir.relative_to(ROOT))},
    }
    (DIAG / f"{args.name}_scope.json").write_text(json.dumps(scope, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(scope, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
