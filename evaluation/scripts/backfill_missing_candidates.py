"""Append candidate rows for legal units flagged as candidates but missing from the sheet.

Run after tightening the detector / taxonomy so regenerated rows align with frames.
Does not change dedup fingerprints in the refiner — use this upstream of seed refine.

Example:
  python scripts/backfill_missing_candidates.py --write
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from law_side.candidate_postprocessor import postprocess_candidates
from law_side.export_to_excel import (
    _CANDIDATE_NS_COLUMNS,
    _apply_grounded_meta_mappings,
    _sanitize_for_excel,
)
from law_side.normative_sentence_detector import NormativeSentenceDetector
from pipelines.run_candidate_normative_sentences_only import _load_units_from_review_xlsx
from utils.io import read_yaml


def _truthy_candidate_flag(v) -> bool:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return False
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in {"1", "true", "yes", "co", "có"}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description="Backfill candidate_normative_sentences for flagged units with zero rows.")
    p.add_argument("--config", type=Path, default=root / "configs" / "law_rulebase_pipeline.yaml")
    p.add_argument(
        "--legal-units-review",
        type=Path,
        default=root / "data" / "interim" / "law_parsing" / "legal_units_review.xlsx",
    )
    p.add_argument(
        "--candidates",
        type=Path,
        default=root / "data" / "interim" / "law_parsing" / "candidate_normative_sentences.xlsx",
    )
    p.add_argument("--output", type=Path, default=None, help="Defaults to --candidates when --write is set.")
    p.add_argument("--write", action="store_true", help="Write merged workbook; default is dry-run summary only.")
    args = p.parse_args()

    cfg = read_yaml(args.config)
    units_path = args.legal_units_review if args.legal_units_review.is_absolute() else root / args.legal_units_review
    cand_path = args.candidates if args.candidates.is_absolute() else root / args.candidates

    units = _load_units_from_review_xlsx(units_path)
    df_existing = pd.read_excel(cand_path) if cand_path.is_file() else pd.DataFrame(columns=_CANDIDATE_NS_COLUMNS)

    covered: set[str] = set()
    if "unit_id" in df_existing.columns:
        covered = {str(x).strip() for x in df_existing["unit_id"].dropna() if str(x).strip()}

    def unit_priority(u) -> tuple:
        score = 0
        for attr in (
            "has_document_marker",
            "has_condition_marker",
            "has_deadline_marker",
            "has_authority_marker",
        ):
            if getattr(u, attr, False):
                score += 1
        return (-score, u.unit_id)

    gap_units = [
        u
        for u in units
        if _truthy_candidate_flag(getattr(u, "is_candidate_rule_sentence", False))
        and (u.unit_id or "").strip()
        and (u.unit_id or "").strip() not in covered
    ]
    gap_units.sort(key=unit_priority)

    print(f"Units flagged candidate: {sum(1 for u in units if _truthy_candidate_flag(getattr(u, 'is_candidate_rule_sentence', False)))}")
    print(f"Units already in candidate sheet: {len(covered)}")
    print(f"Gap units (flagged but no row): {len(gap_units)}")

    if not gap_units:
        return

    detector = NormativeSentenceDetector(config=cfg.get("normative_detection", {}))
    new_ns = postprocess_candidates(detector.detect(gap_units))
    print(f"New candidates emitted for gap: {len(new_ns)}")

    if not args.write:
        return

    out_path = args.output or cand_path
    if not out_path.is_absolute():
        out_path = root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df_new = pd.DataFrame(
        [{k: _sanitize_for_excel(getattr(ns, k)) for k in _CANDIDATE_NS_COLUMNS} for ns in new_ns],
        columns=_CANDIDATE_NS_COLUMNS,
    )
    _apply_grounded_meta_mappings(df_ns=df_new)

    for col in _CANDIDATE_NS_COLUMNS:
        if col not in df_existing.columns:
            df_existing[col] = None
    df_merged = pd.concat([df_existing, df_new], ignore_index=True)
    df_merged.to_excel(out_path, index=False)
    print(f"Wrote {len(df_merged)} rows to {out_path}")


if __name__ == "__main__":
    main()
