"""Generate only legal_frames_review.xlsx for configured law docs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from law_side.doc_loader import DocLoader
from law_side.export_to_excel import export_legal_frames_review
from law_side.legal_frame_extractor import LegalFrameExtractor
from law_side.legal_segmenter import LegalSegmenter
from law_side.law_rulebase_models import LegalUnit, NormativeSentence
from law_side.normative_sentence_detector import NormativeSentenceDetector
from pipelines._paths import legal_qa_nesy_root
from utils.ids import stable_hash
from utils.io import read_yaml


def _cell_str(v, default: str = "") -> str:
    if v is None:
        return default
    if isinstance(v, float) and pd.isna(v):
        return default
    s = str(v).strip()
    return s if s else default


def _merge_unit_context(ns: NormativeSentence, units_by_id: dict[str, dict[str, str]]) -> None:
    uid = (ns.unit_id or "").strip()
    if not uid:
        return
    meta = units_by_id.get(uid)
    if not meta:
        return
    if not (getattr(ns, "heading", None) or "").strip():
        ns.heading = meta.get("heading", "") or ""
    if not (getattr(ns, "parent_context", None) or "").strip():
        ns.parent_context = meta.get("parent_context", "") or ""


def load_normative_sentences_from_candidate_xlsx(path: Path) -> list[NormativeSentence]:
    df = pd.read_excel(path)
    required = {"unit_id", "doc_id", "source_text"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"candidate_normative_sentences missing columns: {sorted(missing)}")

    out: list[NormativeSentence] = []
    for r in df.to_dict(orient="records"):
        cid = _cell_str(r.get("candidate_id")) or _cell_str(r.get("ns_id"))
        if not cid:
            cid = stable_hash(_cell_str(r.get("source_text")) + _cell_str(r.get("unit_id")), n=12)
        sent = _cell_str(r.get("sentence_text")) or _cell_str(r.get("source_text"))
        out.append(
            NormativeSentence(
                ns_id=cid,
                unit_id=_cell_str(r.get("unit_id")),
                doc_id=_cell_str(r.get("doc_id")),
                source_ref=_cell_str(r.get("source_ref")),
                sentence_text=sent,
                sentence_type=_cell_str(r.get("sentence_type"), "candidate"),
                normative_pattern=_cell_str(r.get("normative_pattern")),
                subject_span=_cell_str(r.get("actor_text")) or None,
                action_span=_cell_str(r.get("action_text")) or None,
                modality_span=None,
                condition_span=_cell_str(r.get("condition_text")) or None,
                time_span=_cell_str(r.get("deadline_text")) or None,
                document_span=_cell_str(r.get("document_text")) or None,
                authority_span=_cell_str(r.get("authority_text")) or None,
                candidate_rule_type=_cell_str(r.get("candidate_rule_type")),
                confidence_manual=_cell_str(r.get("confidence_manual"), "medium"),
                candidate_id=cid,
                doc_code=_cell_str(r.get("doc_code")),
                unit_ref_full=_cell_str(r.get("unit_ref_full")),
                source_text=_cell_str(r.get("source_text")) or sent,
                candidate_type=_cell_str(r.get("candidate_type")),
                candidate_subtype=_cell_str(r.get("candidate_subtype")),
                candidate_score=_cell_str(r.get("candidate_score")),
                trigger_patterns=_cell_str(r.get("trigger_patterns")),
                actor_text=_cell_str(r.get("actor_text")) or None,
                action_text=_cell_str(r.get("action_text")) or None,
                object_text=_cell_str(r.get("object_text")) or None,
                condition_text=_cell_str(r.get("condition_text")) or None,
                deadline_text=_cell_str(r.get("deadline_text")) or None,
                authority_text=_cell_str(r.get("authority_text")) or None,
                document_text=_cell_str(r.get("document_text")) or None,
                exception_text=_cell_str(r.get("exception_text")) or None,
                threshold_text=_cell_str(r.get("threshold_text")) or None,
                legal_effect_text=_cell_str(r.get("legal_effect_text")) or None,
                should_extract_rule=_cell_str(r.get("should_extract_rule")),
                extraction_priority=_cell_str(r.get("extraction_priority")),
                notes=_cell_str(r.get("notes")),
                heading=_cell_str(r.get("heading")),
                parent_context=_cell_str(r.get("parent_context")),
            )
        )
    return out


def _load_units_review_index(path: Path) -> dict[str, dict[str, str]]:
    df = pd.read_excel(path)
    if "unit_id" not in df.columns:
        return {}
    idx: dict[str, dict[str, str]] = {}
    for r in df.to_dict(orient="records"):
        uid = _cell_str(r.get("unit_id"))
        if not uid:
            continue
        idx[uid] = {
            "heading": _cell_str(r.get("heading")),
            "parent_context": _cell_str(r.get("parent_context")),
            "text": _cell_str(r.get("text")),
        }
    return idx


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(description="Generate only legal frames review Excel.")
    p.add_argument(
        "--config",
        type=Path,
        default=root / "configs" / "law_rulebase_pipeline.yaml",
        help="YAML config with input_dir and doc_files.",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=root / "data/interim/law_parsing/legal_frames_review.xlsx",
        help="Output legal frames xlsx path.",
    )
    p.add_argument(
        "--from-candidates",
        action="store_true",
        help="Build frames from candidate_normative_sentences.xlsx (grounded on source_text).",
    )
    p.add_argument(
        "--candidates-xlsx",
        type=Path,
        default=root / "data/interim/law_parsing/candidate_normative_sentences.xlsx",
    )
    p.add_argument(
        "--legal-units-review",
        type=Path,
        default=root / "data/interim/law_parsing/legal_units_review.xlsx",
        help="Optional context fallback when loading from --from-candidates.",
    )
    args = p.parse_args()

    cfg = read_yaml(args.config)
    frame_extractor = LegalFrameExtractor(config=cfg.get("frame_extractor", {}))

    if args.from_candidates:
        cpath = args.candidates_xlsx
        if not cpath.is_absolute():
            cpath = root / cpath
        if not cpath.exists():
            raise FileNotFoundError(f"Missing candidates sheet: {cpath}")
        normative_sentences = load_normative_sentences_from_candidate_xlsx(cpath)
        upath = args.legal_units_review
        if not upath.is_absolute():
            upath = root / upath
        units_by_id = _load_units_review_index(upath) if upath.exists() else {}
        for ns in normative_sentences:
            _merge_unit_context(ns, units_by_id)
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
        legal_units: list[LegalUnit] = []
        for doc in docs:
            legal_units.extend(segmenter.segment(doc))

        detector = NormativeSentenceDetector(config=cfg.get("normative_detection", {}))
        normative_sentences = detector.detect(legal_units)

    legal_frames = frame_extractor.extract(normative_sentences)

    out_path = args.output
    if not out_path.is_absolute():
        out_path = root / out_path
    export_legal_frames_review(
        legal_frames=legal_frames,
        out_legal_frames=out_path,
        autosize=bool(cfg.get("autosize", False)),
    )
    print(f"Legal frames review generated: {out_path}")


if __name__ == "__main__":
    main()
