"""Generate only candidate_normative_sentences.xlsx for configured law docs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from law_side.doc_loader import DocLoader
from law_side.candidate_postprocessor import postprocess_candidates
from law_side.export_to_excel import export_candidate_normative_sentences
from law_side.legal_segmenter import LegalSegmenter
from law_side.law_rulebase_models import LegalUnit
from law_side.normative_sentence_detector import NormativeSentenceDetector
from pipelines._paths import legal_qa_nesy_root
from utils.io import read_yaml


def _load_units_from_review_xlsx(path: Path) -> list[LegalUnit]:
    df = pd.read_excel(path)
    required = {
        "unit_id",
        "doc_id",
        "doc_code",
        "chapter",
        "section",
        "article",
        "clause",
        "point",
        "unit_type",
        "heading",
        "text",
        "parent_context",
        "source_ref",
        "unit_ref_full",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"legal_units_review missing columns: {sorted(missing)}")

    def b(v) -> bool:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return False
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        return s in {"1", "true", "yes", "co", "có"}

    units: list[LegalUnit] = []
    for r in df.to_dict(orient="records"):
        units.append(
            LegalUnit(
                unit_id=str(r.get("unit_id", "") or ""),
                doc_id=str(r.get("doc_id", "") or ""),
                doc_code=str(r.get("doc_code", "") or ""),
                chapter=r.get("chapter", None),
                section=r.get("section", None),
                article=r.get("article", None),
                clause=r.get("clause", None),
                point=r.get("point", None),
                unit_type=str(r.get("unit_type", "") or ""),
                heading=str(r.get("heading", "") or ""),
                text=str(r.get("text", "") or ""),
                parent_context=str(r.get("parent_context", "") or ""),
                topic_tag=r.get("topic_tag", None),
                normative_signal=r.get("normative_signal", None),
                is_candidate_rule_sentence=b(r.get("is_candidate_rule_sentence", False)),
                source_ref=str(r.get("source_ref", "") or ""),
                unit_ref_full=str(r.get("unit_ref_full", "") or ""),
                sentence_index=int(r.get("sentence_index", 1) or 1),
                subsentence_index=int(r.get("subsentence_index", 1) or 1),
                list_item_marker=r.get("list_item_marker", None),
                deontic_signal=r.get("deontic_signal", None),
                has_condition_marker=b(r.get("has_condition_marker", False)),
                has_deadline_marker=b(r.get("has_deadline_marker", False)),
                has_document_marker=b(r.get("has_document_marker", False)),
                has_authority_marker=b(r.get("has_authority_marker", False)),
                has_exception_marker=b(r.get("has_exception_marker", False)),
                has_threshold_marker=b(r.get("has_threshold_marker", False)),
                has_cross_reference=b(r.get("has_cross_reference", False)),
                cross_reference_text=r.get("cross_reference_text", None),
                actor_hint=r.get("actor_hint", None),
                action_hint=r.get("action_hint", None),
                object_hint=r.get("object_hint", None),
                rule_density_estimate=str(r.get("rule_density_estimate", "thap") or "thap"),
                needs_split=str(r.get("needs_split", "khong") or "khong"),
                split_reason=r.get("split_reason", None),
                notes=str(r.get("notes", "") or ""),
            )
        )
    return units


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(description="Generate only candidate normative sentences Excel.")
    p.add_argument(
        "--config",
        type=Path,
        default=root / "configs" / "law_rulebase_pipeline.yaml",
        help="YAML config with input_dir and doc_files.",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=root / "data/interim/law_parsing/candidate_normative_sentences.xlsx",
        help="Output candidate normative sentences xlsx path.",
    )
    p.add_argument(
        "--from-review",
        action="store_true",
        help="Read `legal_units_review.xlsx` instead of re-segmenting docs.",
    )
    p.add_argument(
        "--legal-units-review",
        type=Path,
        default=root / "data/interim/law_parsing/legal_units_review.xlsx",
        help="Path to legal_units_review.xlsx (used with --from-review).",
    )
    args = p.parse_args()

    cfg = read_yaml(args.config)

    if args.from_review:
        in_units = args.legal_units_review
        if not in_units.is_absolute():
            in_units = root / in_units
        legal_units = _load_units_from_review_xlsx(in_units)
    else:
        input_dir = Path(cfg.get("input_dir", "data/raw/legal_corpus/doc"))
        if not input_dir.is_absolute():
            input_dir = root / input_dir

        doc_files = list(cfg.get("doc_files", []))
        if not doc_files:
            raise ValueError("Config `doc_files` is empty. Please provide input .doc files.")

        loader = DocLoader(config=cfg.get("doc_loader", {}))
        docs = loader.load_documents(input_dir, doc_files)

        segmenter = LegalSegmenter(config=cfg.get("segmentation", {}))
        legal_units = []
        for doc in docs:
            legal_units.extend(segmenter.segment(doc))

    detector = NormativeSentenceDetector(config=cfg.get("normative_detection", {}))
    normative_sentences = detector.detect(legal_units)
    normative_sentences = postprocess_candidates(normative_sentences)

    out_path = args.output
    if not out_path.is_absolute():
        out_path = root / out_path
    export_candidate_normative_sentences(
        normative_sentences=normative_sentences,
        out_candidate_sentences=out_path,
        autosize=bool(cfg.get("autosize", False)),
    )
    print(f"Candidate normative sentences generated: {out_path}")


if __name__ == "__main__":
    main()
