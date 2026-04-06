"""End-to-end rule-base first-pass pipeline for Vietnamese legal text.

Phase 1 Multi-rule Ready Enhancement:
- Stages 0-5: Unchanged (review artifacts)
- NEW: Canonical rule artifact emission (JSONL) as source of truth for backend
- Configurable domain patterns (enterprise.yaml, labor.yaml, tax.yaml)
- Parameterized output paths and namespace support

Pipeline stages:
0. Document ingest -> document_manifest.xlsx
1. Structural segmentation -> legal_units_review.xlsx
2. Normative sentence detection -> candidate_normative_sentences.xlsx
3. Legal frame extraction -> legal_frames_review.xlsx
4. Predicate normalization -> predicate_lexicon.xlsx
5. Rule seed construction -> rulebase_seed.xlsx (review) + canonical_rules.jsonl (NEW: backend source)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from law_side.canonical_rule_exporter import export_canonical_rules_jsonl, export_statute_rule_packs
from law_side.domain_rule_deriver import derive_domain_rulebase
from law_side.shared_registry_builder import (
    build_shared_entities_registry,
    build_shared_predicates_registry,
    build_shared_rule_pack,
)
from law_side.doc_loader import DocLoader
from law_side.export_to_excel import export_all_to_excel
from law_side.legal_frame_extractor import LegalFrameExtractor
from law_side.legal_segmenter import LegalSegmenter
from law_side.law_rulebase_models import LegalDocument, LegalFrame, LegalUnit, NormativeSentence, PredicateLexiconEntry, RuleSeed
from law_side.normative_sentence_detector import NormativeSentenceDetector
from law_side.predicate_normalizer import PredicateNormalizer
from law_side.rule_builder import RuleBuilder
from pipelines._paths import legal_qa_nesy_root
from pipelines.domain_config import load_domain_config
from utils.io import read_yaml
from utils.logger import get_logger


@dataclass(slots=True)
class LawRulebasePipelineConfig:
    input_dir: Path
    doc_files: list[str]
    domain: str = "enterprise"  # NEW: domain scope (enterprise, labor, tax)
    output_dir: Path | None = None  # NEW: parameterized output directory
    autosize: bool = False
    emit_canonical_artifacts: bool = True  # NEW: emit canonical_rules.jsonl for backend
    segmentation: dict[str, Any] = None  # type: ignore[assignment]
    normative_detection: dict[str, Any] = None  # type: ignore[assignment]
    rule_builder: dict[str, Any] = None  # type: ignore[assignment]
    frame_extractor: dict[str, Any] = None  # type: ignore[assignment]
    predicate_normalizer: dict[str, Any] = None  # type: ignore[assignment]
    doc_loader: dict[str, Any] = None  # type: ignore[assignment]


class LawRulebasePipeline:
    """Orchestrate stages: review artifacts (Excel) + canonical artifacts (JSONL)."""

    def __init__(self, config: LawRulebasePipelineConfig) -> None:
        self._config = config
        self._log = get_logger(self.__class__.__name__)
        
        # Load domain config if specified
        try:
            self._domain_config = load_domain_config(config.domain)
            self._log.info(f"Loaded domain config: {config.domain}")
        except Exception as e:
            self._domain_config = None
            self._log.warning(f"Could not load domain config for '{config.domain}': {e}")

    @classmethod
    def from_yaml(cls, config_path: Path) -> "LawRulebasePipeline":
        cfg = read_yaml(config_path)
        root = legal_qa_nesy_root()

        input_dir = Path(cfg.get("input_dir", "data/raw/legal_corpus/doc"))
        if not input_dir.is_absolute():
            input_dir = root / input_dir

        # NEW: domain scope from config
        domain = cfg.get("domain", "enterprise")
        
        # NEW: output directory from config or parameterized
        output_dir = cfg.get("output_dir")
        if output_dir:
            output_dir = Path(output_dir)
            if not output_dir.is_absolute():
                output_dir = root / output_dir

        doc_files = cfg.get("doc_files", [])
        if not doc_files:
            # Default two documents for enterprise domain
            doc_files = ["67_VBHN-VPQH_671127.doc", "168_2025_ND-CP_623074.doc"]

        return cls(
            LawRulebasePipelineConfig(
                input_dir=input_dir,
                doc_files=list(doc_files),
                domain=domain,
                output_dir=output_dir,
                autosize=bool(cfg.get("autosize", False)),
                emit_canonical_artifacts=bool(cfg.get("emit_canonical_artifacts", True)),
                segmentation=cfg.get("segmentation", {}),
                normative_detection=cfg.get("normative_detection", {}),
                rule_builder=cfg.get("rule_builder", {}),
                frame_extractor=cfg.get("frame_extractor", {}),
                predicate_normalizer=cfg.get("predicate_normalizer", {}),
                doc_loader=cfg.get("doc_loader", {}),
            )
        )

    def run(self) -> dict[str, Path]:
        root = legal_qa_nesy_root()
        
        # NEW: Support parameterized output directory with domain namespace
        output_root = self._config.output_dir or root / "data"
        domain_ns = self._config.domain

        # Review artifacts (Excel) - organized by domain
        out_document_manifest = output_root / f"raw/legal_corpus/manifest/{domain_ns}/document_manifest.xlsx"
        out_legal_units = output_root / f"interim/law_parsing/{domain_ns}/legal_units_review.xlsx"
        out_candidate_sentences = output_root / f"interim/law_parsing/{domain_ns}/candidate_normative_sentences.xlsx"
        out_legal_frames = output_root / f"interim/law_parsing/{domain_ns}/legal_frames_review.xlsx"
        out_predicate_lexicon = output_root / f"processed/ontology/{domain_ns}/predicate_lexicon.xlsx"
        out_rulebase_seed = output_root / f"processed/rulebase/{domain_ns}/rulebase_seed.xlsx"
        
        # NEW: Canonical artifacts (JSONL) - backend source of truth
        out_canonical_rules = output_root / f"processed/rulebase/{domain_ns}/canonical_rules.jsonl"

        # Stage 0: Ingest documents.
        loader = DocLoader(config=self._config.doc_loader or {})
        documents: list[LegalDocument] = loader.load_documents(
            self._config.input_dir,
            self._config.doc_files,
        )
        self._log.info("Loaded %d documents", len(documents))

        # Stage 1: Structural segmentation.
        segmenter = LegalSegmenter(config=self._config.segmentation or {})
        legal_units: list[LegalUnit] = []
        for doc in documents:
            legal_units.extend(segmenter.segment(doc))

        # Stage 2: Normative sentence detection.
        detector = NormativeSentenceDetector(config=self._config.normative_detection or {})
        normative_sentences: list[NormativeSentence] = detector.detect(legal_units)

        # Update units for review fields using candidate info.
        units_by_id = {u.unit_id: u for u in legal_units}
        for ns in normative_sentences:
            u = units_by_id.get(ns.unit_id)
            if not u:
                continue
            u.is_candidate_rule_sentence = True
            u.topic_tag = ns.candidate_rule_type
            u.normative_signal = ns.normative_pattern

        # Stage 3: Legal frame extraction.
        frame_extractor = LegalFrameExtractor(config=self._config.frame_extractor or {}, domain_config=self._domain_config)
        legal_frames: list[LegalFrame] = frame_extractor.extract(normative_sentences)

        # Stage 4: Predicate normalization.
        pred_norm = PredicateNormalizer(config=self._config.predicate_normalizer or {})
        predicate_lexicon, action_surface_to_normalized = pred_norm.build_predicate_lexicon(legal_frames)

        # Stage 5: Rule construction (seed).
        rule_builder = RuleBuilder(config=self._config.rule_builder or {})
        rule_seeds: list[RuleSeed] = rule_builder.build(
            legal_frames,
            action_surface_to_normalized=action_surface_to_normalized,
        )

        # Stage 6: Excel export (review artifacts)
        export_all_to_excel(
            documents=documents,
            legal_units=legal_units,
            normative_sentences=normative_sentences,
            legal_frames=legal_frames,
            predicate_lexicon=predicate_lexicon,
            rule_seeds=rule_seeds,
            out_document_manifest=out_document_manifest,
            out_legal_units=out_legal_units,
            out_candidate_sentences=out_candidate_sentences,
            out_legal_frames=out_legal_frames,
            out_predicate_lexicon=out_predicate_lexicon,
            out_rulebase_seed=out_rulebase_seed,
            autosize=self._config.autosize,
        )

        # NEW: Export canonical rule artifacts for backend
        statute_packs_dir = None
        domain_rb_path = None
        shared_entities_path = None
        shared_predicates_path = None
        shared_pack_path = None
        runtime_core_path = None

        if self._config.emit_canonical_artifacts and rule_seeds:
            # Legacy flat format
            count = export_canonical_rules_jsonl(
                rule_seeds=rule_seeds,
                output_path=out_canonical_rules,
                domain=self._config.domain,
            )
            self._log.info(
                f"Exported {count} canonical rules to {out_canonical_rules} "
                f"(domain={self._config.domain})"
            )
            
            # Phase 3: Multi-layer artifacts
            domain_ns = self._config.domain
            canonical_dir = output_root / f"processed/rulebase/{domain_ns}/canonical"
            canonical_dir.mkdir(parents=True, exist_ok=True)
            
            # Statute-specific packs
            statute_packs_dir = canonical_dir / "statute_packs"
            statute_packs_dir.mkdir(exist_ok=True)
            pack_results = export_statute_rule_packs(
                rule_seeds=rule_seeds,
                output_dir=statute_packs_dir,
                domain=self._config.domain,
            )
            self._log.info(f"Exported {len(pack_results)} statute packs")
            
            # Domain rulebase (derived from statute packs)
            domain_rb_path = canonical_dir / f"{domain_ns}_core.jsonl"
            domain_summary = derive_domain_rulebase(
                statute_packs_dir=statute_packs_dir,
                domain=self._config.domain,
                output_path=domain_rb_path,
            )
            self._log.info(f"Derived domain rulebase: {domain_summary['total_rules']} rules")
            
            # Shared layer (placeholder for multi-domain)
            shared_dir = canonical_dir / "shared"
            shared_dir.mkdir(exist_ok=True)
            shared_entities_path = shared_dir / "shared_entities.json"
            shared_predicates_path = shared_dir / "shared_predicates.json"
            shared_pack_path = shared_dir / "shared_rule_pack.jsonl"
            
            # For now, build from single domain (will expand in Phase 4)
            domain_rb_paths = [domain_rb_path]
            build_shared_entities_registry(domain_rb_paths, shared_entities_path)
            build_shared_predicates_registry(domain_rb_paths, shared_predicates_path)
            build_shared_rule_pack(domain_rb_paths, {}, {}, shared_pack_path)
            
            # Runtime artifacts: compile domain rulebase to reasoning core
            runtime_dir = output_root / f"processed/rulebase/{domain_ns}/runtime"
            runtime_dir.mkdir(parents=True, exist_ok=True)
            runtime_core_path = runtime_dir / "rulebase_reasoning_core.json"
            
            # Use existing compiler with high-precision runtime selection
            from law_side.rulebase_reasoning_core import build_reasoning_core_package_from_canonical, load_canonical_jsonl, write_reasoning_core_json
            canonical_rules = load_canonical_jsonl(domain_rb_path)
            pkg = build_reasoning_core_package_from_canonical(
                canonical_rules=canonical_rules,
                source_path=domain_rb_path,
            )
            write_reasoning_core_json(pkg, runtime_core_path)
            self._log.info(
                f"Compiled runtime core: {pkg['core_rule_count']} reasoning-ready rules to {runtime_core_path}; "
                f"exportable_clean={pkg['report']['exportable_clean_rules']} "
                f"traceability_only={len(pkg.get('traceability_only', []))} "
                f"excluded={len(pkg.get('excluded_from_core', []))}"
            )

            procedure_step_path = runtime_dir / "procedure_step_traceability.jsonl"
            procedure_step_rules = [
                rule for rule in canonical_rules if rule.get("logic_form") == "procedure_step"
            ]
            procedure_step_path.parent.mkdir(parents=True, exist_ok=True)
            with open(procedure_step_path, "w", encoding="utf-8") as f:
                for rule in procedure_step_rules:
                    f.write(json.dumps(rule, ensure_ascii=False) + "\n")
            self._log.info(
                f"Exported {len(procedure_step_rules)} procedure_step traceability rules to {procedure_step_path}"
            )

        self._log.info("Pipeline done.")
        results = {
            "document_manifest": out_document_manifest,
            "legal_units": out_legal_units,
            "candidate_normative_sentences": out_candidate_sentences,
            "legal_frames": out_legal_frames,
            "predicate_lexicon": out_predicate_lexicon,
            "rulebase_seed": out_rulebase_seed,
        }
        
        if self._config.emit_canonical_artifacts and rule_seeds:
            results["canonical_rules"] = out_canonical_rules
            results["statute_packs_dir"] = statute_packs_dir
            results["domain_rulebase"] = domain_rb_path
            results["shared_entities"] = shared_entities_path
            results["shared_predicates"] = shared_predicates_path
            results["shared_rule_pack"] = shared_pack_path
            results["runtime_core"] = runtime_core_path
        
        return results


__all__ = ["LawRulebasePipeline", "LawRulebasePipelineConfig"]

