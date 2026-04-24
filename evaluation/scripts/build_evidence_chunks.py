"""Build data/corpus/evidence_chunks.json from existing runtime rulebases and optional text files.

Usage:
  python scripts/build_evidence_chunks.py
  python scripts/build_evidence_chunks.py --add-text-file labor_text.txt
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_rulebase_paths(repo: Path) -> list[Path]:
    candidates: list[Path] = []
    legacy = repo / "data" / "processed" / "rulebase" / "rulebase_reasoning_core.json"
    if legacy.is_file():
        candidates.append(legacy)

    domain_dir = repo / "data" / "processed" / "rulebase"
    for p in sorted(domain_dir.glob("*/runtime/rulebase_reasoning_core.json")):
        if p.is_file():
            candidates.append(p)

    # Keep insertion order but dedupe.
    seen: set[str] = set()
    result: list[Path] = []
    for p in candidates:
        k = str(p.resolve())
        if k not in seen:
            seen.add(k)
            result.append(p)
    return result


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _extract_acp_from_source_ref(source_ref: str) -> tuple[str | None, str | None, str | None]:
    if not source_ref:
        return None, None, None

    art_m = re.search(r"(?:article|dieu|điều)=?(\d+)", source_ref, flags=re.IGNORECASE)
    cl_m = re.search(r"(?:clause|khoan|khoản)=?([\w\d]+)", source_ref, flags=re.IGNORECASE)
    pt_m = re.search(r"(?:point|diem|điểm)=?([\w\d]+)", source_ref, flags=re.IGNORECASE)

    article = f"Điều {art_m.group(1)}" if art_m else None
    clause = f"khoản {cl_m.group(1)}" if cl_m else None
    point = f"điểm {pt_m.group(1)}" if pt_m else None
    return article, clause, point


def _compose_article_clause(article: str | None, clause: str | None, point: str | None) -> str | None:
    parts = [x for x in [article, clause, point] if x]
    if not parts:
        return None
    return " ".join(parts)


def _build_text_from_rule(rule: dict[str, Any], prov: dict[str, Any]) -> str:
    surface = _clean_text(prov.get("surface_text"))
    if surface:
        return surface

    head = rule.get("head") or {}
    body = rule.get("body") or []
    pred = _clean_text(head.get("predicate")) or "unknown"
    args = ", ".join(str(x) for x in (head.get("args") or []))
    head_text = f"{pred}({args})" if args else pred

    cond_parts: list[str] = []
    if isinstance(body, list):
        for item in body:
            if not isinstance(item, dict):
                continue
            bp = _clean_text(item.get("predicate"))
            bt = _clean_text(item.get("text"))
            if bt:
                cond_parts.append(f"{bp}: {bt}" if bp else bt)
            elif bp:
                cond_parts.append(bp)

    if cond_parts:
        return f"Quy tắc {head_text}. Điều kiện: " + "; ".join(cond_parts)
    return f"Quy tắc {head_text}."


def _iter_rule_chunks(rulebase_paths: Iterable[Path]) -> Iterable[dict[str, Any]]:
    for path in rulebase_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rules = payload.get("rules_reasoning_core") or []
        domain_guess = path.parent.parent.name

        for rule in rules:
            if not isinstance(rule, dict):
                continue
            rid = _clean_text(rule.get("rule_id"))
            if not rid:
                continue

            metadata = rule.get("metadata") or {}
            prov = metadata.get("provenance") or {}
            if not isinstance(prov, dict):
                prov = {}

            source_doc = _clean_text(prov.get("source_doc") or prov.get("doc_code"))
            source_ref_full = _clean_text(prov.get("source_ref_full"))
            source_ref_raw = _clean_text(prov.get("source_ref"))
            source_ref = source_ref_full or source_ref_raw
            domain = _clean_text(prov.get("domain") or domain_guess)

            article, clause, point = _extract_acp_from_source_ref(source_ref_raw or source_ref_full)
            article_clause = source_ref_full or _compose_article_clause(article, clause, point)
            text = _build_text_from_rule(rule, prov)

            rule_ids = prov.get("rule_ids") if isinstance(prov.get("rule_ids"), list) else []
            if not rule_ids:
                rule_ids = [rid]
            elif rid not in rule_ids:
                rule_ids = [rid, *[x for x in rule_ids if x != rid]]

            yield {
                "chunk_id": f"rb:{domain}:{rid}",
                "text": text,
                "source_doc": source_doc or None,
                "article_clause": article_clause,
                "article": article,
                "clause": clause,
                "point": point,
                "source_ref": source_ref or None,
                "rule_ids": rule_ids,
                "domain": domain or None,
                "rulebase_id": _clean_text(prov.get("rulebase_id")) or None,
                "origin": "rulebase_runtime",
            }


def _iter_text_chunks(text_files: Iterable[Path], *, min_text_len: int) -> Iterable[dict[str, Any]]:
    for text_file in text_files:
        if not text_file.is_file():
            continue
        raw = text_file.read_text(encoding="utf-8", errors="ignore")
        blocks = [b.strip() for b in re.split(r"\n\s*\n", raw) if b.strip()]
        idx = 0
        for block in blocks:
            if len(block) < min_text_len:
                continue
            idx += 1
            yield {
                "chunk_id": f"txt:{text_file.stem}:{idx:05d}",
                "text": block,
                "source_doc": text_file.name,
                "article_clause": None,
                "article": None,
                "clause": None,
                "point": None,
                "source_ref": text_file.name,
                "rule_ids": [],
                "domain": None,
                "rulebase_id": None,
                "origin": "text_file",
            }


def _dedupe_chunks(chunks: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for chunk in chunks:
        cid = _clean_text(chunk.get("chunk_id"))
        if not cid:
            continue
        if cid not in by_id:
            by_id[cid] = chunk
            continue

        # Merge rule ids if duplicate ids occur.
        existing = by_id[cid]
        merged = list(dict.fromkeys([*(existing.get("rule_ids") or []), *(chunk.get("rule_ids") or [])]))
        existing["rule_ids"] = merged
    return list(by_id.values())


def _parse_args() -> argparse.Namespace:
    repo = _repo_root()
    parser = argparse.ArgumentParser(description="Build evidence_chunks.json from runtime rulebase and optional text files")
    parser.add_argument(
        "--output",
        type=Path,
        default=repo / "data" / "corpus" / "evidence_chunks.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "--rulebase",
        dest="rulebases",
        action="append",
        type=Path,
        default=None,
        help="Path to a rulebase_reasoning_core.json (repeatable)",
    )
    parser.add_argument(
        "--add-text-file",
        dest="text_files",
        action="append",
        type=Path,
        default=None,
        help="Optional extra text source; split by blank lines into chunks",
    )
    parser.add_argument(
        "--min-text-len",
        type=int,
        default=80,
        help="Minimum paragraph length for --add-text-file chunks",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo = _repo_root()

    rulebases = args.rulebases if args.rulebases else _default_rulebase_paths(repo)
    rulebases = [p if p.is_absolute() else (repo / p) for p in rulebases]
    rulebases = [p for p in rulebases if p.is_file()]

    if not rulebases:
        raise FileNotFoundError("No rulebase_reasoning_core.json files found. Pass --rulebase explicitly.")

    text_files = args.text_files or []
    text_files = [p if p.is_absolute() else (repo / p) for p in text_files]

    chunks = list(_iter_rule_chunks(rulebases))
    if text_files:
        chunks.extend(_iter_text_chunks(text_files, min_text_len=max(1, args.min_text_len)))
    chunks = _dedupe_chunks(chunks)

    output = args.output if args.output.is_absolute() else (repo / args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "chunks": chunks,
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "scripts/build_evidence_chunks.py",
            "rulebase_files": [str(p) for p in rulebases],
            "text_files": [str(p) for p in text_files if p.is_file()],
            "chunk_count": len(chunks),
        },
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    rulebase_count = sum(1 for c in chunks if c.get("origin") == "rulebase_runtime")
    text_count = sum(1 for c in chunks if c.get("origin") == "text_file")
    print(f"Wrote {len(chunks)} chunks -> {output}")
    print(f"  from rulebase: {rulebase_count}")
    print(f"  from text: {text_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
