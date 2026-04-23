"""End-to-end QA orchestration: parse → verify → retrieve → backward → clarify → forward → proof → evidence → answer."""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
from generation.answer_generator import (
    apply_answer_text_and_refresh_citations,
    generate_answer,
    generate_honest_degraded_answer,
    safe_regenerate_final_answer,
)
from reasoning.clarification_manager import (
    build_clarification_prompts_from_requirements,
    build_parse_ambiguity_prompts,
    filter_clarification_targets,
    merge_clarification_prompts_unified,
)
from question_side.parse_clarify_apply import (
    extract_resolved_condition_atoms_from_known_facts,
    known_facts_for_reasoning,
    normalize_clarification_answers_with_diagnostics,
    structured_facts_for_reasoning,
)
from question_side.question_normalizer import build_layer2 as _build_layer2
from question_side.question_parser import (
    ParserUnavailableError,
    parse_question_layer1 as _parse_question_layer1,
)
from question_side.query_parser_v5 import parse as parse_query_v5
from retrieval.evidence_retriever import (
    EvidenceRetriever,
    configure_evidence_path,
    get_evidence_retriever,
)
from retrieval.advanced_domain_retriever import AdvancedDomainRetriever
from retrieval.domain_scoped_retriever import DomainScopedRuleRetriever, enrich_ranked_with_retrieval_meta
from retrieval.rule_retriever import retrieve_rules
from retrieval.rulebase_loader import RulebaseIndex, configure_rulebase_path, get_rulebase_index
from rulebase.rule_identity import global_rule_key
from rulebase.rulebase_registry import RulebaseRegistry
from runtime.cross_domain_policy import (
    default_policy_for_routing,
    filter_ranked_for_primary_phase,
    merge_secondary_with_policy,
)
from runtime.domain_selector import SimpleDomainSelector
from runtime.qa_runtime_bundle import QARuntimeBundle
from runtime.phase3_pipeline import apply_phase3_post_retrieve
from runtime.backend_modes import (
    apply_answer_backend,
    apply_parse_backend,
    apply_retrieval_backend,
    init_backend_modes,
)
from runtime.evidence_stage import build_evidence_bundle
from runtime.experiment_run_config import ExperimentRunConfig, resolve_experiment_run_config
from runtime.reasoning_context import ReasoningContext
from schemas.domain_routing import DomainRoutingPlan
from schemas.rule_metadata import collect_rulebase_ids_from_index
from schemas.http_response import AskResponse, ClarificationPrompt, ClarifyResponse
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord
from schemas.reasoning import ReasoningState
from schemas.proof import ProofObject
from schemas.reasoning_result import ReasoningResult
from schemas.session import SessionState
from schemas.verification import VerificationRecord
from session.session_service import SessionService, get_session_service
from verification.engine import NeSyEngine
from verification.nli_verifier import NLIVerifier
from verification.repair_loop import run_answer_repair_loop, run_parse_repair_loop, run_retrieval_repair_loop, run_forward_repair_loop
from runtime.verification_gates import gate_forward_reasoning, gate_rule_and_backward
from runtime.pipeline_tracing import (
    TraceCollector,
    summarize_answer_trace,
    summarize_evidence_trace,
    summarize_layer1_trace,
    summarize_layer2_trace,
    summarize_verification_trace,
)
from utils.text import detect_mojibake

parse_question_layer1 = _parse_question_layer1
build_layer2 = _build_layer2


def _collect_plan_retry_condition_atoms(layer2: Layer2Parse) -> list[str]:
    current_atoms = [str(atom) for atom in (layer2.condition_atoms or []) if str(atom or "").strip()]
    non_generic = [atom for atom in current_atoms if not atom.startswith("stated_condition(")]
    if non_generic:
        return list(dict.fromkeys(non_generic))

    diagnostics = dict(getattr(layer2, "diagnostics", None) or {})
    cond_norm = dict(diagnostics.get("condition_normalization") or {})
    alt_atoms = [str(atom) for atom in (cond_norm.get("alternative_atoms") or []) if str(atom or "").strip()]
    if alt_atoms:
        return list(dict.fromkeys(alt_atoms))

    for ambiguity in diagnostics.get("ambiguities") or []:
        if str((ambiguity or {}).get("field") or "") != "condition_text":
            continue
        candidates = [
            str(atom)
            for atom in ((ambiguity or {}).get("candidates") or [])
            if str(atom or "").strip() and not str(atom).startswith("stated_condition(")
        ]
        if candidates:
            return list(dict.fromkeys(candidates))
    return []


def _compute_primary_parse_confidence(layer2: Layer2Parse | None) -> float:
    if layer2 is None:
        return 0.0
    diag = dict(getattr(layer2, "diagnostics", None) or {})
    cond_norm = dict(diag.get("condition_normalization") or {})
    conf = float(cond_norm.get("confidence") or 0.0)
    if conf > 0:
        return round(max(0.0, min(1.0, conf)), 3)
    return 0.6 if _layer2_has_usable_primary_parse(layer2) else 0.35


def _has_parse_alternatives(layer2: Layer2Parse | None) -> bool:
    if layer2 is None:
        return False
    diag = dict(getattr(layer2, "diagnostics", None) or {})
    cond_norm = dict(diag.get("condition_normalization") or {})
    alt_atoms = [str(a) for a in (cond_norm.get("alternative_atoms") or []) if str(a or "").strip()]
    if alt_atoms:
        return True
    ambs = list(diag.get("ambiguities") or [])
    for a in ambs:
        cands = [str(x) for x in ((a or {}).get("candidates") or []) if str(x or "").strip()]
        if len(cands) > 1:
            return True
    return False


def _layer2_has_usable_primary_parse(layer2: Layer2Parse | None) -> bool:
    if layer2 is None:
        return False

    goal = dict(getattr(layer2, "goal", None) or {})
    goal_pred = str(goal.get("predicate") or "").strip().lower()
    goal_args = list(goal.get("args") or []) if isinstance(goal.get("args"), list) else []
    has_goal = goal_pred not in {"", "unknown"}
    has_goal_args_signal = any(str(x or "").strip() for x in goal_args)

    diag = dict(getattr(layer2, "diagnostics", None) or {})
    cond_norm = dict(diag.get("condition_normalization") or {})
    cn_pred = str(cond_norm.get("canonical_predicate") or "").strip().lower()
    cn_conf = float(cond_norm.get("confidence") or 0.0)
    has_usable_condition_norm = cn_pred not in {"", "unknown", "stated_condition"} and cn_conf >= 0.5

    subj = str(getattr(layer2, "subject_normalized", "") or "").strip().lower()
    has_subject = bool(subj and not subj.startswith("unknown_subject"))

    return has_goal and has_goal_args_signal and (has_usable_condition_norm or has_subject)


def _build_parse_uncertainty_signal(layer2: Layer2Parse | None, *, clarification_enabled: bool) -> dict[str, Any]:
    diag = dict(getattr(layer2, "diagnostics", None) or {}) if layer2 is not None else {}
    ambs = list(diag.get("ambiguities") or [])
    blocking_count = sum(1 for a in ambs if bool((a or {}).get("blocking")))
    usable_primary = _layer2_has_usable_primary_parse(layer2)
    alternatives = _has_parse_alternatives(layer2)

    return {
        "parse_ambiguity_as_confidence_signal": bool(ambs),
        "primary_parse_confidence": _compute_primary_parse_confidence(layer2),
        "batch_bypassable_ambiguity": (not clarification_enabled) and blocking_count > 0 and usable_primary,
        "alternatives_preserved": alternatives,
        "usable_primary_parse": usable_primary,
        "ambiguity_count": len(ambs),
        "blocking_ambiguity_count": blocking_count,
    }


def _attach_parse_uncertainty_to_layer2(layer2: Layer2Parse, signal: dict[str, Any]) -> Layer2Parse:
    diag = dict(getattr(layer2, "diagnostics", None) or {})
    diag["parse_uncertainty"] = dict(signal)
    return layer2.model_copy(update={"diagnostics": diag})


def _parse_uncertainty_signal_from_layer2(layer2: Layer2Parse | None) -> dict[str, Any]:
    if layer2 is None:
        return {}
    diag = dict(getattr(layer2, "diagnostics", None) or {})
    signal = dict(diag.get("parse_uncertainty") or {})
    if signal:
        return signal
    return _build_parse_uncertainty_signal(layer2, clarification_enabled=True)


def _parse_uncertainty_interpretation_hint(layer2: Layer2Parse | None) -> str:
    if layer2 is None:
        return ""
    ambs = list((dict(getattr(layer2, "diagnostics", None) or {})).get("ambiguities") or [])
    for a in ambs:
        cands = [str(x) for x in ((a or {}).get("candidates") or []) if str(x or "").strip()]
        if len(cands) > 1:
            return " / ".join(cands[:2])
    return ""


def _apply_parse_uncertainty_answer_policy(
    *,
    ans: Any | None,
    layer2: Layer2Parse | None,
    trace: dict[str, Any],
    context_tag: str,
) -> Any | None:
    if ans is None:
        return ans

    signal = _parse_uncertainty_signal_from_layer2(layer2)
    if not signal:
        return ans

    parse_ambiguity = bool(signal.get("parse_ambiguity_as_confidence_signal"))
    if not parse_ambiguity:
        return ans

    conf = float(signal.get("primary_parse_confidence") or 0.0)
    best_effort = bool(signal.get("usable_primary_parse"))
    alternatives = bool(signal.get("alternatives_preserved"))
    blocking_count = int(signal.get("blocking_ambiguity_count") or 0)
    low_conf = conf < 0.72
    material_uncertainty = low_conf or blocking_count > 0 or bool(signal.get("batch_bypassable_ambiguity"))
    if not material_uncertainty:
        return ans

    trace["answer_based_on_best_effort_parse"] = best_effort
    trace["parse_uncertainty_disclosed"] = True
    trace["alternative_interpretations_preserved"] = alternatives
    trace["conditional_answer_due_to_parse_uncertainty"] = True

    if not isinstance(getattr(ans, "extra", None), dict):
        ans.extra = {}
    ans.extra.update(
        {
            "answer_based_on_best_effort_parse": best_effort,
            "parse_uncertainty_disclosed": True,
            "alternative_interpretations_preserved": alternatives,
            "conditional_answer_due_to_parse_uncertainty": True,
            "primary_parse_confidence": conf,
            "parse_uncertainty_context": context_tag,
        }
    )

    vs = str(getattr(ans, "verification_summary", "") or "")
    tail = f"parse_uncertainty_disclosed=1;primary_parse_confidence={round(conf, 3)}"
    if tail not in vs:
        ans.verification_summary = f"{vs};{tail}" if vs else tail

    note = "Luu y: cau tra loi duoi day dua tren dien giai chinh (best-effort) cua cau hoi do con ton tai bat dinh khi parse."
    unresolved = _parse_uncertainty_interpretation_hint(layer2)
    if unresolved:
        note += f" Dien giai con mo tieu bieu: {unresolved}."
    existing = str(getattr(ans, "answer_text", "") or "")
    if note not in existing:
        ans.answer_text = f"{existing}\n\n{note}".strip()

    try:
        cur_conf = float(getattr(ans, "confidence", 0.0) or 0.0)
        if best_effort:
            ans.confidence = min(cur_conf if cur_conf > 0 else 1.0, 0.68)
    except Exception:
        pass

    return ans


def _layer1_parse_unavailable(parse_meta: dict[str, Any]) -> Layer1Parse:
    meta = dict(parse_meta or {})
    meta.setdefault("requested_mode", "llm_real")
    meta.setdefault("actual_mode", "parse_unavailable")
    meta.setdefault("provider", meta.get("parser_provider"))
    meta.setdefault("model", meta.get("parser_model"))
    meta.setdefault("parser_available", False)
    meta.setdefault("parser_error", "parse_unavailable")
    meta.setdefault("parser_backend", "unavailable")
    meta.setdefault("parser_backend_mode", "parse_unavailable")
    meta.setdefault("fallback_used", False)
    return Layer1Parse(
        utterance_type="unknown",
        subject_text="",
        condition_text="",
        action_text="",
        modality_text="",
        time_text="",
        deadline_text="",
        exception_text="",
        question_focus="unknown",
        assertion_status="unknown",
        raw_notes=["parse_unavailable"],
        parse_metadata=meta,
    )


def _parse_query_for_runtime(
    question: str,
    *,
    user_facts: list[str],
    forced_condition_atoms: list[str] | None = None,
    settings: Any | None = None,
) -> tuple[Layer1Parse, Layer2Parse, dict[str, Any]]:
    encoding_diag = detect_mojibake(question)
    encoding_suspect = bool(encoding_diag.get("is_mojibake", False))

    if parse_question_layer1 is _parse_question_layer1 and build_layer2 is _build_layer2:
        layer1, layer2, meta = parse_query_v5(
            question,
            user_facts=user_facts,
            forced_condition_atoms=forced_condition_atoms,
            settings=settings,
        )
    else:
        layer1 = parse_question_layer1(question, settings=settings)
        layer2 = build_layer2(
            layer1,
            user_facts=user_facts,
            forced_condition_atoms=forced_condition_atoms,
        )
        meta = dict(getattr(layer1, "parse_metadata", None) or {})

    if encoding_suspect:
        l1_meta = dict(getattr(layer1, "parse_metadata", None) or {})
        l1_meta["input_encoding_suspect"] = True
        l1_meta["input_encoding_diag"] = encoding_diag
        l1_meta.setdefault("parser_error", "input_mojibake_suspected")
        layer1 = layer1.model_copy(update={"parse_metadata": l1_meta})

        l2_diag = dict(getattr(layer2, "diagnostics", None) or {})
        l2_diag["encoding_hygiene"] = {
            "input_encoding_suspect": True,
            "input_encoding_diag": encoding_diag,
            "classification": "invalid_input_encoding",
        }
        layer2 = layer2.model_copy(update={"diagnostics": l2_diag})

        meta = dict(meta or {})
        meta["input_encoding_suspect"] = True
        meta["input_encoding_diag"] = encoding_diag
        meta.setdefault("parser_error", "input_mojibake_suspected")

    return layer1, layer2, meta

def _merge_pipeline_trace_dict(trace: dict[str, Any], tc: TraceCollector) -> None:
    if not tc._noop:
        d = tc.to_dict()
        m = dict(d.get("meta") or {})
        block = {k: trace[k] for k in (
            "domain_routing",
            "reasoning_context",
            "retrieved_rules_by_domain",
            "proof_steps_by_domain",
            "final_grounding_docs",
            "reasoning_result",
            "phase3",
        ) if k in trace}
        if block:
            m["multi_rulebase_v1"] = block
        d["meta"] = m
        trace["pipeline_trace"] = d


def _rule_dump(r: RuleRecord) -> dict[str, Any]:
    return r.model_dump(mode="json")


def _merge_verification(sess: SessionState, rec: VerificationRecord) -> None:
    sess.verification_logs.append(rec)


def _user_fact_keys(session: SessionState) -> list[str]:
    return list(known_facts_for_reasoning(session).keys())


def _proof_summary_for_evidence(proof: Any) -> str:
    if not proof:
        return ""
    summary = " ".join((s.description or "") for s in (getattr(proof, "proof_steps", None) or [])[:8]).strip()
    if summary:
        return summary
    return str(getattr(proof, "conclusion", "") or getattr(proof, "derived_conclusion", ""))


def _strip_internal_runtime_debug_text(text: str) -> str:
    if not text:
        return ""
    cleaned = str(text).strip()
    replacements: list[tuple[str, str]] = [
        (r"Forward\s+reasoning\s+did\s+not\s+complete[^\n\.]*", "Hệ thống chưa hoàn tất được toàn bộ bước đối chiếu kỹ thuật."),
        (r"Forward\s+blocked\s+by\s+runtime\s+quality\s+gate\s*\([^\)]*\)", "Cần đối chiếu thêm dữ kiện để kết luận chắc chắn."),
        (r"Forward\s+blocked\s+by\s+runtime\s+quality\s+gate", "Cần đối chiếu thêm dữ kiện để kết luận chắc chắn."),
        (r"predicate_family_mismatch", ""),
        (r"unification_gate", ""),
        (r"runtime\s+quality\s+gate", ""),
    ]
    for pat, rep in replacements:
        cleaned = re.sub(pat, rep, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+([,.;:])", r"\1", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ ]{2,}", " ", cleaned)
    return cleaned.strip()


def _sanitize_user_visible_answer_fields(ans: Any) -> Any:
    ans.answer_text = _strip_internal_runtime_debug_text(str(getattr(ans, "answer_text", "") or ""))
    ans.conclusion = _strip_internal_runtime_debug_text(str(getattr(ans, "conclusion", "") or ""))
    ans.proof_summary = _strip_internal_runtime_debug_text(str(getattr(ans, "proof_summary", "") or ""))
    sections = dict(getattr(ans, "answer_sections", None) or {})
    if sections:
        ans.answer_sections = {
            str(k): _strip_internal_runtime_debug_text(str(v or ""))
            for k, v in sections.items()
        }
    return ans


def _extract_primary_citation_label(ans: Any) -> str:
    for c in list(getattr(ans, "legal_citations", None) or []):
        label = str(getattr(c, "display_label", None) or getattr(c, "label", None) or "").strip()
        if label:
            return label
    return ""


def _extract_deadline_days_hint(ans: Any, selected_rule: RuleRecord | None) -> str:
    candidate_texts: list[str] = []
    for c in list(getattr(ans, "legal_citations", None) or []):
        candidate_texts.extend(
            [
                str(getattr(c, "excerpt", "") or ""),
                str(getattr(c, "tooltip_excerpt", "") or ""),
                str(getattr(c, "source_ref", "") or ""),
                str(getattr(c, "label", "") or ""),
            ]
        )
    for e in list(getattr(ans, "evidence_snippets", None) or []):
        candidate_texts.append(str(getattr(e, "text", "") or ""))
    candidate_texts.append(str(getattr(ans, "conclusion", "") or ""))
    if selected_rule is not None:
        prov = dict((selected_rule.metadata or {}).get("provenance") or {})
        candidate_texts.append(str(prov.get("source_ref_full") or ""))
    for txt in candidate_texts:
        m = re.search(r"\b(\d{1,3})\s*ng[aàáảãạăắằẳẵặâấầẩẫậ]y\b", txt, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


def _normalize_subject_wording_for_enterprise_citation(
    subject_text: str,
    ans: Any,
    selected_rule: RuleRecord | None,
) -> str:
    subj = str(subject_text or "").strip().lower()
    if not subj:
        subj = "doanh nghiệp"

    def _fold_vn(text: str) -> str:
        s = str(text or "")
        s = s.replace("đ", "d").replace("Đ", "D")
        s = unicodedata.normalize("NFKD", s)
        return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()

    subj_fold = _fold_vn(subj)

    # If legal grounding points to enterprise decree/rules, prefer neutral legal noun.
    ctx_parts: list[str] = []
    for c in list(getattr(ans, "legal_citations", None) or []):
        ctx_parts.extend(
            [
                str(getattr(c, "display_label", "") or ""),
                str(getattr(c, "label", "") or ""),
                str(getattr(c, "source_ref", "") or ""),
                str(getattr(c, "doc_id", "") or ""),
            ]
        )
    if selected_rule is not None:
        meta = dict(selected_rule.metadata or {})
        prov = dict(meta.get("provenance") or {})
        ctx_parts.extend(
            [
                str(meta.get("source_doc") or ""),
                str(meta.get("domain") or ""),
                str(prov.get("source_ref_full") or ""),
            ]
        )

    ctx = " | ".join(ctx_parts).lower()
    enterprise_signal = (
        "doanh nghiệp" in ctx
        or "nđ-" in ctx
        or "nd-" in ctx
        or "168/2025" in ctx
        or "luatdn" in ctx
        or "enterprise" in ctx
    )

    subj_company_like = (
        "cong ty" in subj_fold
        or "company" in subj_fold
        or subj_fold.strip() == "company_x"
    )
    if enterprise_signal and subj_company_like:
        return "doanh nghiệp"
    return subject_text.strip() if str(subject_text or "").strip() else "doanh nghiệp"


def _is_parse_focus_clear(layer1: Layer1Parse | None) -> bool:
    if layer1 is None:
        return False
    focus = str(getattr(layer1, "question_focus", "") or "").strip().lower()
    if focus in {"deadline", "obligation", "procedure_or_dossier"}:
        return True
    meta = dict(getattr(layer1, "parse_metadata", None) or {})
    q_conf = float(meta.get("question_focus_confidence") or 0.0)
    a_conf = float(meta.get("action_confidence") or 0.0)
    return q_conf >= 0.75 and a_conf >= 0.75


def _apply_user_facing_forward_failure_policy(
    ans: Any,
    *,
    selected_rule: RuleRecord | None,
    forward_failed: bool,
    trace: dict[str, Any],
    layer1: Layer1Parse | None = None,
) -> Any:
    ans = _sanitize_user_visible_answer_fields(ans)

    citations = list(getattr(ans, "legal_citations", None) or [])
    evidence = list(getattr(ans, "evidence_snippets", None) or [])
    has_selected_rule = selected_rule is not None
    has_citation = bool(citations)
    top_evidence_score = max((float(getattr(e, "score", 0.0) or 0.0) for e in evidence), default=0.0)
    has_strong_evidence = top_evidence_score >= 0.55
    focus_clear = _is_parse_focus_clear(layer1)

    failure_markers = (
        "predicate_family_mismatch",
        "unification_gate",
        "runtime quality gate",
        "forward reasoning did not complete",
        "forward blocked by runtime quality gate",
    )
    answer_blob = "\n".join(
        [
            str(getattr(ans, "answer_text", "") or ""),
            str(getattr(ans, "conclusion", "") or ""),
            str(getattr(ans, "proof_summary", "") or ""),
        ]
    ).lower()
    effective_forward_failure = bool(forward_failed) or any(m in answer_blob for m in failure_markers)

    if effective_forward_failure and has_selected_rule and has_citation and has_strong_evidence and focus_clear:
        citation_label = _extract_primary_citation_label(ans)
        days_hint = _extract_deadline_days_hint(ans, selected_rule)
        prov = dict((selected_rule.metadata or {}).get("provenance") or {}) if selected_rule else {}
        source_ref = str(prov.get("source_ref_full") or (selected_rule.metadata or {}).get("source_doc") or "").strip() if selected_rule else ""
        subject_text = str(getattr(layer1, "subject_text", "") or "doanh nghiệp").strip()
        subject_text = _normalize_subject_wording_for_enterprise_citation(subject_text, ans, selected_rule)
        action_text = str(getattr(layer1, "action_text", "") or "thông báo").strip()
        condition_text = str(getattr(layer1, "condition_text", "") or "").strip()
        subject_text = subject_text or "doanh nghiệp"
        action_text = action_text or "thông báo"

        condition_suffix = ""
        if condition_text:
            condition_suffix = f" khi {condition_text}"

        if citation_label and days_hint:
            legal_line = (
                f"Theo [{citation_label}], {subject_text} phải {action_text} trong thời hạn {days_hint} ngày"
                f"{condition_suffix}."
            )
        elif citation_label:
            legal_line = (
                f"Theo [{citation_label}], {subject_text} phải {action_text} theo đúng thời hạn áp dụng"
                f"{condition_suffix}."
            )
        else:
            legal_line = (
                f"Theo căn cứ pháp lý đã trích dẫn, {subject_text} phải {action_text} trong thời hạn theo quy định"
                f"{condition_suffix}."
            )

        if source_ref:
            legal_line += f" Quy định tham chiếu chính: {source_ref}."

        caveat = (
            "Tuy nhiên, cần xác định đúng trường hợp pháp lý cụ thể để tránh nhầm với quy định "
            "về đăng ký thay đổi hoặc thông báo trong trường hợp khác."
        )

        ans.answer_text = (
            "Kính gửi Quý khách hàng,\n\n"
            "1) Căn cứ pháp lý\n"
            f"{legal_line}\n\n"
            "2) Áp dụng sơ bộ\n"
            "Kết luận ở mức định hướng được rút ra từ quy tắc đã chọn và các chứng cứ liên quan.\n\n"
            "3) Lưu ý khi áp dụng\n"
            f"{caveat}\n\n"
            "Trân trọng."
        )
        ans.conclusion = _strip_internal_runtime_debug_text(str(getattr(ans, "conclusion", "") or ""))
        ans.proof_summary = ""
        current_conf = float(getattr(ans, "confidence", 0.0) or 0.0)
        ans.confidence = min(current_conf if current_conf > 0 else 0.55, 0.55)
        ans.answer_sections = {
            "opening": "Kính gửi Quý khách hàng,",
            "legal_rule": legal_line,
            "application": "Kết luận ở mức định hướng được rút ra từ quy tắc đã chọn và các chứng cứ liên quan.",
            "conclusion": caveat,
            "closing": "Trân trọng.",
        }
        ans.verification_summary = (
            f"{ans.verification_summary};user_safe_forward_failure_masked"
            if getattr(ans, "verification_summary", "")
            else "user_safe_forward_failure_masked"
        )
        ans.extra.update(
            {
                "user_facing_runtime_failure_hidden": True,
                "forward_failure_fallback_policy_applied": True,
                "has_selected_rule": has_selected_rule,
                "has_strong_evidence": has_strong_evidence,
                "has_citation": has_citation,
                "parse_focus_clear": focus_clear,
                "top_evidence_score": top_evidence_score,
                "fallback_answer_confidence": ans.confidence,
            }
        )
        trace["user_facing_forward_failure_masked"] = {
            "enabled": True,
            "effective_forward_failure": effective_forward_failure,
            "has_selected_rule": has_selected_rule,
            "has_strong_evidence": has_strong_evidence,
            "has_citation": has_citation,
            "parse_focus_clear": focus_clear,
            "top_evidence_score": top_evidence_score,
        }
    return ans


def _group_retrieved_by_domain(
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    by_dom: dict[str, list[dict[str, Any]]] = {}
    for r, s, d in ranked:
        dom = str(d.get("domain") or "unknown")
        by_dom.setdefault(dom, []).append(
            {
                "rule_id": r.rule_id,
                "rulebase_id": d.get("rulebase_id"),
                "domain": dom,
                "layer": d.get("layer"),
                "score": float(s),
                "source_doc": d.get("source_doc"),
                "source_article": d.get("source_article"),
            }
        )
    return by_dom


def _proof_steps_by_domain(proof: Any) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for s in getattr(proof, "proof_steps", None) or []:
        dom = str(getattr(s, "domain", None) or "unknown")
        out.setdefault(dom, []).append(
            {
                "step_id": getattr(s, "step_id", None),
                "rule_id": getattr(s, "rule_id", None),
                "rulebase_id": getattr(s, "rulebase_id", None),
                "domain": getattr(s, "domain", None),
                "layer": getattr(s, "layer", None),
                "source_doc": getattr(s, "source_doc", None),
                "source_article": getattr(s, "source_article", None),
            }
        )
    return out


def _clarification_gain_summary(
    *,
    pre_missing: list[str],
    post_missing: list[str],
    pre_status: str,
    post_status: str,
    pre_proof: Any | None,
    post_proof: Any | None,
) -> dict[str, Any]:
    pre_set = {str(x) for x in pre_missing if str(x).strip()}
    post_set = {str(x) for x in post_missing if str(x).strip()}
    newly = sorted(pre_set - post_set)
    pre_steps = len(getattr(pre_proof, "proof_steps", None) or []) if pre_proof is not None else 0
    post_steps = len(getattr(post_proof, "proof_steps", None) or []) if post_proof is not None else 0
    return {
        "pre_clarification_status": pre_status,
        "post_clarification_status": post_status,
        "newly_satisfied_requirements": newly,
        "proof_delta": {
            "proof_before_steps": pre_steps,
            "proof_after_steps": post_steps,
            "step_delta": post_steps - pre_steps,
            "had_proof_before": pre_proof is not None,
            "has_proof_after": post_proof is not None,
        },
    }


def _grounding_docs_from_evidence(ev: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for e in ev or []:
        rows.append(
            {
                "chunk_id": getattr(e, "chunk_id", None),
                "article_clause": getattr(e, "article_clause", None),
                "score": round(float(getattr(e, "score", 0.0)), 5),
            }
        )
    return rows


def _is_grounded_rule_usable(selected: RuleRecord | None, goal: dict[str, Any] | None) -> bool:
    if selected is None:
        return False
    rid = str(selected.rule_id or "").strip().lower()
    if not rid:
        return False
    if rid.startswith("shared_motif_"):
        return False
    if str(selected.head.predicate or "").strip().lower() in {"", "unknown"}:
        return False
    goal_pred = str((goal or {}).get("predicate") or "").strip().lower()
    if goal_pred in {"", "unknown"}:
        return False
    return True


def _is_grounded_proof_usable(proof: Any | None) -> bool:
    if proof is None:
        return False
    steps = list(getattr(proof, "proof_steps", None) or [])
    if not steps:
        return False
    fail_stage = str(getattr(proof, "fail_stage", "") or "").strip().lower()
    if fail_stage:
        return False
    return True


def _should_use_honest_degraded_answer(
    *,
    selected: RuleRecord | None,
    goal: dict[str, Any] | None,
    proof: Any | None,
    failure_reason: str | None,
) -> bool:
    low = str(failure_reason or "").strip().lower()
    if low in {
        "no_grounded_rule_found",
        "forward_unification_fail",
        "reasoning_blocked_by_rule_verification",
        "forward_verification_failed",
    }:
        return True
    if not _is_grounded_rule_usable(selected, goal):
        return True
    if not _is_grounded_proof_usable(proof):
        return True
    return False


def _finalize_reasoning_result_dict(
    base: dict[str, Any],
    *,
    proof: Any | None,
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    bstate: Any | None,
    fstate: Any | None,
    selected: RuleRecord | None,
    phase3_result: Any | None = None,
) -> dict[str, Any]:
    out = dict(base)
    
    # Phase 3 data
    if phase3_result is not None:
        out["bridge_rules_used"] = [
            str(x.provenance.bridge_rule_id) 
            for x in phase3_result.bridge_emitted
        ]
        out["bridge_generated_facts"] = [
            x.model_dump(mode="json") 
            for x in phase3_result.bridge_emitted
        ]
        out["rejected_candidates_temporal"] = phase3_result.temporal_rejected
        out["rejected_candidates_conflict"] = phase3_result.conflict_rejected
        out["rule_id_collision_warnings"] = phase3_result.rule_id_collision_warnings
        out["namespacing_mode"] = "global_rule_key_v1"
    
    if proof is not None:
        dom_summary = _proof_steps_by_domain(proof)
        out["proof_summary_by_domain"] = {
            k: [str(s.get("rule_id") or "") for s in v[:16]] for k, v in dom_summary.items()
        }
    if bstate is not None:
        out["subgoals_unresolved"] = list(getattr(bstate, "missing_facts", None) or [])
        out["subgoals_satisfied"] = list(getattr(bstate, "covered_requirements", None) or [])
        out["unresolved_subgoals_domain"] = list(getattr(bstate, "missing_facts", None) or [])
        bp = getattr(bstate, "backward_plan", None) or {}
        if isinstance(bp, dict):
            ev = bp.get("evaluation") or {}
            ltd = ev.get("logic_layer_decisions") or []
            if ltd:
                out["logic_layer_policy_decisions"] = list(ltd)
    if selected is not None:
        out["final_winning_rule_ids"] = [selected.rule_id]
    rt = out.get("rejected_candidates_temporal") or []
    rc = out.get("rejected_candidates_conflict") or []
    out["rejected_candidates"] = list(rt) + list(rc)
    bridge_ids: list[str] = []
    if phase3_result is not None:
        bridge_ids = [str(x.fact_id) for x in phase3_result.bridge_emitted if getattr(x, "fact_id", None)]
    out["bridge_facts_consumed"] = bridge_ids
    out["diagnostics"] = {
        "candidate_rule_count": len(ranked),
        "forward_trace": bool(fstate and getattr(fstate, "forward_result", None)),
        "logic_layer": bool(out.get("logic_layer_policy_decisions")),
    }
    try:
        return ReasoningResult.model_validate(out).model_dump(mode="json")
    except Exception:
        return out


def _build_rescued_conditional_missing_facts_answer(
    *,
    question: str,
    selected_rule: RuleRecord | None,
    goal: dict[str, Any],
    missing_facts: list[str],
    retrieved_rules: list[RuleRecord],
) -> Any:
    """Produce a guarded conditional legal answer when rescued flow is blocked only by missing facts."""
    ans = generate_honest_degraded_answer(
        question=question,
        reason="rescued_missing_facts_conditional",
        selected_rule=selected_rule,
        goal=goal,
        retrieved_rules=retrieved_rules,
    )

    facts = [str(f).strip() for f in (missing_facts or []) if str(f).strip()]
    facts = list(dict.fromkeys(facts))
    if not facts:
        facts = ["du_kien_thuc_te_then_chot_chua_duoc_cung_cap"]

    listed_facts = "\n".join([f"- {f}" for f in facts])
    conditional_line = (
        "Nếu các dữ kiện còn thiếu ở trên là đúng, thì kết luận pháp lý theo quy tắc đã chọn "
        "nhiều khả năng sẽ được áp dụng; nếu không đúng, kết luận có thể thay đổi."
    )

    ans.answer_text = (
        f"{ans.answer_text}\n\n"
        "Thông tin còn thiếu cần xác minh:\n"
        f"{listed_facts}\n\n"
        f"{conditional_line}\n"
        "Đây là kết luận có điều kiện, không phải kết luận khẳng định cuối cùng."
    )
    ans.conclusion = "ket_luan_co_dieu_kien_can_xac_minh_them"
    ans.proof_summary = ""
    ans.verification_summary = (
        f"{ans.verification_summary};mode=rescued_missing_facts_conditional"
        if ans.verification_summary
        else "mode=rescued_missing_facts_conditional"
    )
    ans.extra.update(
        {
            "rescued_fallback_flow": True,
            "conditional_answer": True,
            "missing_facts": facts,
            "non_final_disclaimer": True,
        }
    )
    return ans


def _apply_missing_facts_conditional_answer(
    ans: Any,
    *,
    missing_facts: list[str],
    selected_rule: RuleRecord | None = None,
    known_fact_keys: list[str] | None = None,
    mode_tag: str = "missing_facts_conditional",
) -> Any:
    """Convert current answer into a conditional legal answer using unresolved facts as hypotheses."""
    facts = [str(f).strip() for f in (missing_facts or []) if str(f).strip()]
    facts = list(dict.fromkeys(facts))
    if not facts:
        return ans

    listed_facts = "\n".join([f"- {f}" for f in facts])

    base_text = str(getattr(ans, "answer_text", "") or "").strip()
    for bad_pattern in (
        r"insufficient\s+information",
        r"kh[oô]ng\s+đ[uủ]\s+th[oô]ng\s+tin",
        r"khong\s+du\s+thong\s+tin",
        r"kh[oô]ng\s+th[eể]\s+k[eế]t\s+lu[aậ]n",
        r"khong\s+the\s+ket\s+luan",
    ):
        base_text = re.sub(
            bad_pattern,
            "chưa đủ điều kiện khẳng định tuyệt đối",
            base_text,
            flags=re.IGNORECASE,
        )

    known_facts = [str(f).strip() for f in (known_fact_keys or []) if str(f).strip()]
    known_facts = list(dict.fromkeys(known_facts))[:5]
    known_facts_text = "\n".join([f"- {f}" for f in known_facts]) if known_facts else "- (chưa có dữ kiện tường minh bổ sung)"

    if selected_rule is not None:
        prov = dict((selected_rule.metadata or {}).get("provenance") or {})
        source_ref = str(prov.get("source_ref_full") or (selected_rule.metadata or {}).get("source_doc") or selected_rule.rule_id)
        rule_line = (
            f"Quy tắc được dùng: {source_ref} "
            f"(rule_id={selected_rule.rule_id}, predicate={selected_rule.head.predicate})."
        )
    else:
        rule_line = "Quy tắc được dùng: quy tắc pháp lý gần nhất theo kết quả retrieval hiện tại."

    conditional_branches = []
    for f in facts:
        conditional_branches.append(f"- Nếu {f} là đúng -> Outcome A: áp dụng kết luận pháp lý theo quy tắc đã chọn.")
        conditional_branches.append(f"- Nếu {f} là sai -> Outcome B: không đủ điều kiện áp dụng trực tiếp quy tắc đã chọn, cần loại trừ hoặc điều chỉnh kết luận.")
    conditional_block = "\n".join(conditional_branches)

    ans.answer_text = (
        "1. Quy tắc pháp lý đã biết\n"
        f"{rule_line}\n\n"
        "2. Áp dụng quy tắc vào dữ kiện đã biết\n"
        f"{base_text}\n"
        "Dữ kiện đã biết:\n"
        f"{known_facts_text}\n\n"
        "3. Điều kiện cho dữ kiện còn thiếu (dùng như biến giả định)\n"
        "Các dữ kiện còn thiếu:\n"
        f"{listed_facts}\n"
        f"{conditional_block}"
    ).strip()
    ans.conclusion = "ket_luan_co_dieu_kien_theo_missing_facts"
    ans.verification_summary = (
        f"{ans.verification_summary};mode={mode_tag}" if ans.verification_summary else f"mode={mode_tag}"
    )
    ans.extra.update(
        {
            "conditional_answer": True,
            "missing_facts": facts,
            "hypothetical_conditions_used": True,
            "answer_structure": [
                "known_legal_rule",
                "apply_to_known_facts",
                "if_true_false_for_missing_facts",
            ],
            "non_final_disclaimer": True,
        }
    )
    return ans


def _apply_application_answer_policy(
    *,
    ans: Any,
    trace: dict[str, Any],
    session: SessionState,
    question_mode: str,
    selected_rule: RuleRecord | None,
    known_fact_keys: list[str],
    missing_facts: list[str],
    has_missing_signal: bool = False,
    mode_tag: str,
) -> tuple[Any, str]:
    facts = [str(f).strip() for f in (missing_facts or []) if str(f).strip()]
    facts = list(dict.fromkeys(facts))

    if question_mode in {"fact_application", "hybrid"} and (facts or has_missing_signal):
        if not facts:
            facts = ["du_kien_thuc_te_then_chot_chua_duoc_cung_cap"]
        ans = _apply_missing_facts_conditional_answer(
            ans,
            missing_facts=facts,
            selected_rule=selected_rule,
            known_fact_keys=known_fact_keys,
            mode_tag=mode_tag,
        )
        trace["conditional_answer_due_to_missing_facts"] = {
            "enabled": True,
            "missing_facts": facts,
            "missing_signal_without_explicit_keys": bool(has_missing_signal and facts == ["du_kien_thuc_te_then_chot_chua_duoc_cung_cap"]),
            "policy": "continue_reasoning_with_hypothetical_conditions",
            "question_mode": question_mode,
        }
        session.clarification_questions = []
        trace["clarification_suppressed_answered_with_hypotheticals"] = True
        trace["application_status"] = "conditional"
        return ans, "conditional"

    if question_mode == "rule_reading":
        trace["question_mode_answer_policy"] = {"mode": question_mode, "policy": "A_only"}
        trace["application_status"] = "none"
        return ans, "none"

    trace["question_mode_answer_policy"] = {"mode": question_mode, "policy": "A_plus_C_grounded_final"}
    trace["application_status"] = "final"
    return ans, "final"


def _collect_application_policy_missing_facts(
    *,
    bstate: ReasoningState | None,
    fstate: ReasoningState | None,
) -> tuple[list[str], bool]:
    facts: list[str] = []

    def _add(values: list[Any] | None) -> None:
        for raw in list(values or []):
            key = str(raw or "").strip()
            if key and key not in facts:
                facts.append(key)

    def _artifact_values(st: ReasoningState | None) -> tuple[list[str], list[str]]:
        if st is None:
            return [], []
        art = getattr(st, "requirement_artifact", None)
        if art is None:
            return [], []
        if isinstance(art, dict):
            return list(art.get("unmet_required") or []), list(art.get("unmet_optional") or [])
        return list(getattr(art, "unmet_required", None) or []), list(getattr(art, "unmet_optional", None) or [])

    _add(list(getattr(bstate, "missing_facts", None) or []) if bstate is not None else [])
    _add(list(getattr(fstate, "missing_facts", None) or []) if fstate is not None else [])
    b_req, b_opt = _artifact_values(bstate)
    f_req, f_opt = _artifact_values(fstate)
    _add([*b_req, *b_opt, *f_req, *f_opt])

    fr = dict(getattr(fstate, "forward_result", None) or {}) if fstate is not None else {}
    fail_key = str(fr.get("failure_reason") or "").strip().lower()
    has_missing_signal = fail_key in {
        "constraint_missing_input",
        "missing_input",
        "positive_condition_missing",
    }
    if fail_key in {"unification_broken", "actor_role_mismatch"} and bool(facts):
        has_missing_signal = True

    detail = str(fr.get("failure_detail") or "").strip()
    if has_missing_signal and detail and detail not in {"unknown", "none", "n/a", "na", "_"}:
        if detail not in facts:
            facts.append(detail)

    for tr in list(fr.get("constraint_traces") or []):
        if not isinstance(tr, dict):
            continue
        if str(tr.get("status") or "").strip().lower() != "missing_input":
            continue
        sk = str(tr.get("session_key") or "").strip()
        if sk and sk not in facts:
            facts.append(sk)

    return facts, bool(has_missing_signal)


def _infer_question_mode(layer1: Layer1Parse | None, layer2: Layer2Parse | None) -> str:
    if layer1 is None and layer2 is None:
        return "hybrid"

    focus = str(getattr(layer1, "question_focus", "") or "").strip().lower() if layer1 is not None else ""
    utterance_type = str(getattr(layer1, "utterance_type", "") or "").strip().lower() if layer1 is not None else ""
    cond_atoms = [str(a) for a in (getattr(layer2, "condition_atoms", None) or []) if str(a or "").strip()]
    facts = list(getattr(layer2, "facts", None) or []) if layer2 is not None else []
    has_fact_signal = bool(cond_atoms or facts)

    # HIGH PRIORITY: missing-fact + application-outcome override.
    # "chưa rõ / không rõ / chưa biết" phrases are dropped by the LLM parser, so we
    # use their surviving proxies in Layer1 structured fields:
    #   - missing-fact proxy: assertion_status==hypothetical OR utterance_type==conditional_legal_question
    #   - application-outcome proxy: modality_text contains an application modal ("có bị", "có phải", …)
    # Both must be present to avoid reclassifying pure rule-reading deadline questions.
    if layer1 is not None:
        _modality = str(getattr(layer1, "modality_text", "") or "").lower()
        _application_modals = [
            "có bị", "có được", "có hợp lệ", "có vi phạm",
            "có quá hạn", "có phải", "có cần",
        ]
        _has_application_modal = any(m in _modality for m in _application_modals)
        _assertion = str(getattr(layer1, "assertion_status", "") or "").lower()
        _utype = str(getattr(layer1, "utterance_type", "") or "").lower()
        _has_missing_fact_proxy = (
            _assertion == "hypothetical"
            or _utype == "conditional_legal_question"
        )
        if _has_application_modal and _has_missing_fact_proxy:
            return "fact_application"
        if _has_application_modal and utterance_type in {"yes_no", "yes_no_question", "fact_check", "application", "specific_case"}:
            return "fact_application"

    pure_rule_focuses = {
        "deadline",
        "obligation",
        "procedure_or_dossier",
        "authority",
        "legal_effect",
        "legal_consequence",
    }
    # Utterance types that signal specific-case application intent, overriding a rule-reading focus
    application_utterance_types = {"yes_no", "yes_no_question", "fact_check", "application", "specific_case"}

    # PRIMARY: question_focus is authoritative, but app intent signals can override.
    if focus in pure_rule_focuses:
        if utterance_type in application_utterance_types or has_fact_signal:
            return "hybrid"
        return "rule_reading"

    # SECONDARY: generic/unknown focus should not be forced to pure rule reading.
    if focus in {"", "unknown"}:
        return "hybrid"
    if utterance_type in application_utterance_types:
        return "fact_application"
    if has_fact_signal:
        return "fact_application"
    return "hybrid"


def _build_missing_facts_stage_trace(
    *,
    question_mode: str,
    bstate: ReasoningState | None,
    fstate: ReasoningState | None,
    fg_ok: bool,
    v_ans_decision: str,
) -> dict[str, Any]:
    b_missing = list(getattr(bstate, "missing_facts", None) or []) if bstate is not None else []
    f_missing = list(getattr(fstate, "missing_facts", None) or []) if fstate is not None else []
    missing_now = list(dict.fromkeys([*b_missing, *f_missing]))
    fr = dict(getattr(fstate, "forward_result", None) or {}) if fstate is not None else {}
    fr_reason = str(fr.get("failure_reason") or "")
    has_constraint_presence = bool(fr.get("applied_constraints") or fr.get("constraint_traces"))

    stages = [
        {
            "stage": "parse",
            "missing_facts_introduced": False,
            "missing_facts_blocking": False,
            "missing_facts_to_reject": False,
        },
        {
            "stage": "retrieval",
            "missing_facts_introduced": False,
            "missing_facts_blocking": False,
            "missing_facts_to_reject": False,
        },
        {
            "stage": "constraint_eval",
            "missing_facts_introduced": fr_reason == "constraint_missing_input",
            "missing_facts_blocking": fr_reason == "constraint_missing_input",
            "missing_facts_to_reject": v_ans_decision == "REJECT" and fr_reason == "constraint_missing_input",
        },
        {
            "stage": "forward_engine",
            "missing_facts_introduced": bool(missing_now),
            "missing_facts_blocking": bool((not fg_ok) and missing_now),
            "missing_facts_to_reject": bool(v_ans_decision == "REJECT" and missing_now),
        },
        {
            "stage": "verifier",
            "missing_facts_introduced": False,
            "missing_facts_blocking": False,
            "missing_facts_to_reject": bool(v_ans_decision == "REJECT" and missing_now),
        },
        {
            "stage": "answer",
            "missing_facts_introduced": False,
            "missing_facts_blocking": False,
            "missing_facts_to_reject": bool(v_ans_decision == "REJECT" and missing_now),
        },
    ]

    return {
        "question_mode": str(question_mode),
        "ordered_stages": ["parse", "retrieval", "constraint_eval", "forward_engine", "verifier", "answer"],
        "stages": stages,
        "mismatch_highlights": {
            "missing_input_used_as_hard_failure_instead_of_conditional": bool(
                v_ans_decision == "REJECT" and (fr_reason == "constraint_missing_input" or bool(missing_now))
            ),
            "constraint_presence_automatically_triggering_fact_check": bool(
                has_constraint_presence and (fr_reason == "constraint_missing_input" or bool(missing_now))
            ),
        },
    }


def _is_completely_unanswerable(
    *,
    selected: RuleRecord | None,
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    layer2: Layer2Parse,
) -> bool:
    goal = dict(getattr(layer2, "goal", None) or {})
    goal_pred = str(goal.get("predicate") or "").strip().lower()
    has_goal_signal = goal_pred not in {"", "unknown"}
    has_condition_signal = bool([a for a in (getattr(layer2, "condition_atoms", None) or []) if str(a or "").strip()])
    has_ranked = bool(ranked)
    has_selected = bool(selected and str(getattr(selected, "rule_id", "") or "") != "RULE_FALLBACK_UNKNOWN")
    return not (has_goal_signal or has_condition_signal or has_ranked or has_selected)


def _is_selected_rule_missing(selected: RuleRecord | None) -> bool:
    if selected is None:
        return True
    rid = str(getattr(selected, "rule_id", "") or "").strip().lower()
    return rid in {"", "rule_fallback_unknown"}


def _is_conflict_too_large(
    *,
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    phase3_result: Any | None,
) -> bool:
    if phase3_result is None:
        return False
    conflict_rejected = list(getattr(phase3_result, "conflict_rejected", None) or [])
    conflict_count = len(conflict_rejected)
    survived_count = len(ranked or [])
    total_considered = conflict_count + survived_count
    if total_considered <= 0:
        return False
    if survived_count == 0 and conflict_count >= 3:
        return True
    return conflict_count >= 5 and total_considered >= 6 and (conflict_count / total_considered) >= 0.85 and survived_count <= 1


def _collect_answer_hard_stop_reasons(
    *,
    layer2: Layer2Parse | None,
    selected: RuleRecord | None,
    goal: dict[str, Any] | None,
    evidence: list[Any],
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    phase3_result: Any | None,
) -> list[str]:
    reasons: list[str] = []
    if not _layer2_has_usable_primary_parse(layer2):
        reasons.append("parse_unusable")
    if _is_selected_rule_missing(selected) or not _is_grounded_rule_usable(selected, goal):
        reasons.append("no_rule")
    if not list(evidence or []):
        reasons.append("no_evidence")
    if _is_conflict_too_large(ranked=ranked, phase3_result=phase3_result):
        reasons.append("conflict_too_large")
    return reasons


def _enforce_reasoning_failure_answer_policy(
    ans: Any | None,
    *,
    question: str,
    layer2: Layer2Parse | None,
    selected: RuleRecord | None,
    goal: dict[str, Any] | None,
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    evidence: list[Any],
    phase3_result: Any | None,
    forward_failed: bool,
    answer_rejected: bool,
    trace: dict[str, Any],
) -> Any | None:
    hard_stop_reasons = _collect_answer_hard_stop_reasons(
        layer2=layer2,
        selected=selected,
        goal=goal,
        evidence=evidence,
        ranked=ranked,
        phase3_result=phase3_result,
    )
    if hard_stop_reasons:
        trace.setdefault("hard_gates_hit", []).append("answer_null_by_hard_stop_policy")
        trace["answer_null_policy"] = {
            "enabled": True,
            "rule": "null_only_parse_unusable_or_no_rule_or_no_evidence_or_conflict_too_large",
            "reasons": hard_stop_reasons,
        }
        return None

    if ans is None or not str(getattr(ans, "answer_text", "") or "").strip():
        ans = generate_honest_degraded_answer(
            question=question,
            reason="degraded_useful_after_reasoning_failure",
            selected_rule=selected,
            goal=dict(goal or {}),
            retrieved_rules=[r for r, _s, _d in ranked[:3]],
        )
        ans.verification_summary = (
            f"{ans.verification_summary};degraded_useful_after_reasoning_failure"
            if getattr(ans, "verification_summary", "")
            else "degraded_useful_after_reasoning_failure"
        )

    if answer_rejected:
        ans.verification_summary = (
            f"{ans.verification_summary};answer_reject_degraded_useful"
            if getattr(ans, "verification_summary", "")
            else "answer_reject_degraded_useful"
        )
        if not isinstance(getattr(ans, "extra", None), dict):
            ans.extra = {}
        ans.extra["answer_reject_degraded_useful"] = True
        trace["answer_reject_degraded_useful"] = True

    if forward_failed:
        try:
            cur_conf = float(getattr(ans, "confidence", 0.0) or 0.0)
        except Exception:
            cur_conf = 0.0
        new_conf = min(cur_conf if cur_conf > 0 else 0.58, 0.58)
        ans.confidence = new_conf
        ans.verification_summary = (
            f"{ans.verification_summary};forward_failure_confidence_degraded"
            if getattr(ans, "verification_summary", "")
            else "forward_failure_confidence_degraded"
        )
        if not isinstance(getattr(ans, "extra", None), dict):
            ans.extra = {}
        ans.extra["forward_failure_not_answer_failure"] = True
        ans.extra["forward_failure_confidence_cap"] = new_conf
        trace["forward_failure_confidence_degraded"] = {
            "enabled": True,
            "confidence_cap": new_conf,
        }

    return ans


def _resolve_run_config(
    run_config: ExperimentRunConfig | dict[str, Any] | str | Path | None,
) -> ExperimentRunConfig:
    return resolve_experiment_run_config(run_config)


class QAOrchestrator:
    """Central business orchestrator for ask / clarify flows."""

    def __init__(
        self,
        *,
        rulebase_core_path: Path,
        evidence_chunks_path: Path,
        rule_retrieval_top_k: int = 8,
        nesy_nli_mock: bool = False,
        nli_verifier: NLIVerifier | None = None,
        nli_degraded: bool = False,
        nli_meta: dict[str, Any] | None = None,
        entailment_threshold: float = 0.70,
        contradiction_threshold: float = 0.70,
        max_repair_attempts_parse: int = 2,
        max_repair_attempts_answer: int = 2,
        max_repair_attempts_rule: int = 2,
        max_repair_attempts_backward: int = 1,
        max_repair_attempts_forward: int = 1,
        answer_reject_allow_fallback: bool = False,
        session_svc: SessionService | None = None,
        qa_runtime_bundle: QARuntimeBundle | None = None,
        settings: Any | None = None,
    ) -> None:
        self._rulebase_core_path = rulebase_core_path
        self._evidence_chunks_path = evidence_chunks_path
        self._top_k = rule_retrieval_top_k
        self._nesy_nli_mock = nesy_nli_mock
        self._nli_verifier = nli_verifier
        self._nli_degraded = nli_degraded
        self._nli_meta = dict(nli_meta or {})
        self._entailment_threshold = entailment_threshold
        self._contradiction_threshold = contradiction_threshold
        self._max_repair_attempts_parse = max_repair_attempts_parse
        self._max_repair_attempts_answer = max_repair_attempts_answer
        self._max_repair_attempts_rule = max_repair_attempts_rule
        self._max_repair_attempts_backward = max_repair_attempts_backward
        self._max_repair_attempts_forward = max_repair_attempts_forward
        self._answer_reject_allow_fallback = answer_reject_allow_fallback
        self._session_svc = session_svc
        self._settings = settings
        self._evidence: EvidenceRetriever | None = None
        self._bundle: QARuntimeBundle = qa_runtime_bundle or QARuntimeBundle.from_legacy_rulebase_path(
            str(self._rulebase_core_path),
            domain="enterprise",
        )

    @property
    def runtime_bundle(self) -> QARuntimeBundle:
        return self._bundle

    def _session(self) -> SessionService:
        return self._session_svc or get_session_service()

    def _evidence_retriever(self) -> EvidenceRetriever:
        if self._evidence is None:
            configure_evidence_path(self._evidence_chunks_path)
            self._evidence = EvidenceRetriever(self._evidence_chunks_path)
        return self._evidence

    def _nesy(self) -> NeSyEngine:
        kw = dict(
            nesy_nli_mock=self._nesy_nli_mock,
            nli_degraded=self._nli_degraded,
            nli_meta=self._nli_meta,
            entailment_threshold=self._entailment_threshold,
            contradiction_threshold=self._contradiction_threshold,
        )
        return NeSyEngine(nli=self._nli_verifier, **kw)

    def ask(
        self,
        question: str,
        session_id: str | None,
        user_facts: list[str] | None,
        trace_collector: TraceCollector | None = None,
        question_time: str | None = None,
        run_config: ExperimentRunConfig | dict[str, Any] | str | Path | None = None,
    ) -> AskResponse:
        return run_ask(
            question=question,
            session_id=session_id,
            user_facts=user_facts or [],
            session_svc=self._session(),
            nesy=self._nesy(),
            rulebase_registry=self._bundle.rulebase_registry,
            domain_retriever=self._bundle.domain_retriever,
            domain_selector=self._bundle.domain_selector,
            retriever_advanced=self._bundle.retriever_advanced,
            evidence_retriever=self._evidence_retriever(),
            top_k=self._top_k,
            max_repair_attempts_parse=self._max_repair_attempts_parse,
            max_repair_attempts_answer=self._max_repair_attempts_answer,
            max_repair_attempts_rule=self._max_repair_attempts_rule,
            max_repair_attempts_backward=self._max_repair_attempts_backward,
            max_repair_attempts_forward=self._max_repair_attempts_forward,
            answer_reject_allow_fallback=self._answer_reject_allow_fallback,
            settings=self._settings,
            trace_collector=trace_collector,
            question_time=question_time,
            run_config=run_config,
        )

    def clarify(
        self,
        session_id: str,
        answers: list[dict[str, Any]],
        trace_collector: TraceCollector | None = None,
        run_config: ExperimentRunConfig | dict[str, Any] | str | Path | None = None,
    ) -> ClarifyResponse:
        return run_clarify(
            session_id=session_id,
            answers=answers,
            session_svc=self._session(),
            nesy=self._nesy(),
            rulebase_registry=self._bundle.rulebase_registry,
            domain_retriever=self._bundle.domain_retriever,
            domain_selector=self._bundle.domain_selector,
            retriever_advanced=self._bundle.retriever_advanced,
            evidence_retriever=self._evidence_retriever(),
            top_k=self._top_k,
            max_repair_attempts_parse=self._max_repair_attempts_parse,
            max_repair_attempts_answer=self._max_repair_attempts_answer,
            max_repair_attempts_rule=self._max_repair_attempts_rule,
            max_repair_attempts_backward=self._max_repair_attempts_backward,
            max_repair_attempts_forward=self._max_repair_attempts_forward,
            answer_reject_allow_fallback=self._answer_reject_allow_fallback,
            settings=self._settings,
            trace_collector=trace_collector,
            run_config=run_config,
        )


def run_ask(
    *,
    question: str,
    session_id: str | None,
    user_facts: list[str],
    session_svc: SessionService | None = None,
    nesy: NeSyEngine | None = None,
    rule_index: RulebaseIndex | None = None,
    rulebase_registry: RulebaseRegistry | None = None,
    domain_retriever: DomainScopedRuleRetriever | None = None,
    retriever_advanced: AdvancedDomainRetriever | None = None,
    domain_selector: SimpleDomainSelector | None = None,
    evidence_retriever: EvidenceRetriever | None = None,
    top_k: int = 8,
    max_repair_attempts_parse: int = 2,
    max_repair_attempts_answer: int = 2,
    max_repair_attempts_rule: int = 2,
    max_repair_attempts_backward: int = 1,
    max_repair_attempts_forward: int = 1,
    answer_reject_allow_fallback: bool = False,
    settings: Any | None = None,
    trace_collector: TraceCollector | None = None,
    question_time: str | None = None,
    domain_hint: str | None = None,
    run_config: ExperimentRunConfig | dict[str, Any] | str | Path | None = None,
) -> AskResponse:
    svc = session_svc or get_session_service()
    engine = nesy or NeSyEngine(nesy_nli_mock=True)
    tc = trace_collector or TraceCollector.noop()
    resolved_run_config = _resolve_run_config(run_config)

    if session_id and (st := svc.get(session_id)):
        session = st
        session.original_question = question or session.original_question
        for f in user_facts:
            session.known_facts[f] = True
    else:
        session = svc.create_session(
            question,
            user_facts,
            preferred_session_id=session_id,
        )
    if not tc._noop:
        tc.session_id = session.session_id

    trace: dict[str, Any] = {
        "stage": [],
        "query_text": question,
        "backend_modes": init_backend_modes(verifier_engine=engine),
        "run_config": resolved_run_config.to_trace_dict(),
        "clarification_enabled": bool(resolved_run_config.enable_clarification),
        "hard_gates_hit": [],
    }

    parse_unavailable_meta: dict[str, Any] | None = None
    with tc.span("parse_layer1") as sp_l1:
        try:
            layer1, layer2, _parse_meta = _parse_query_for_runtime(
                question,
                user_facts=_user_fact_keys(session),
                settings=settings,
            )
            sp_l1.output_summary = summarize_layer1_trace(layer1)
        except ParserUnavailableError as e:
            parse_unavailable_meta = dict(e.parse_metadata or {})
            parse_unavailable_meta.setdefault("requested_mode", "llm_real")
            parse_unavailable_meta.setdefault("actual_mode", "parse_unavailable")
            parse_unavailable_meta.setdefault("parser_available", False)
            parse_unavailable_meta.setdefault("parser_error", e.parser_error or "parse_unavailable")
            sp_l1.output_summary = {
                "requested_mode": parse_unavailable_meta.get("requested_mode"),
                "actual_mode": parse_unavailable_meta.get("actual_mode"),
                "provider": parse_unavailable_meta.get("provider") or parse_unavailable_meta.get("parser_provider"),
                "model": parse_unavailable_meta.get("model") or parse_unavailable_meta.get("parser_model"),
                "parser_available": parse_unavailable_meta.get("parser_available"),
                "parser_error": parse_unavailable_meta.get("parser_error"),
            }
            sp_l1.decision = "parse_unavailable"

    if parse_unavailable_meta is not None:
        trace.setdefault("hard_gates_hit", []).append("parse_unavailable")
        layer1 = _layer1_parse_unavailable(parse_unavailable_meta)
        layer2 = build_layer2(layer1, user_facts=_user_fact_keys(session))
        session.layer1 = layer1
        session.layer2 = layer2
        apply_parse_backend(trace["backend_modes"], layer1)
        trace["parser_status"] = dict(layer1.parse_metadata or {})
        trace["stage"].append("parse_unavailable")

    with tc.span("parse_layer2") as sp_l2:
        sp_l2.output_summary = summarize_layer2_trace(layer2)
    session.layer1 = layer1
    session.layer2 = layer2
    apply_parse_backend(trace["backend_modes"], layer1)
    trace["parser_status"] = dict(getattr(layer1, "parse_metadata", None) or {})
    trace["stage"].append("parse_done")
    question_mode = _infer_question_mode(layer1, layer2)
    trace["question_mode"] = question_mode

    with tc.span("parse_repair") as sp_pr:
        layer1, layer2, v_parse, parse_repair_trace = run_parse_repair_loop(
            engine,
            layer1=layer1,
            layer2=layer2,
            question_text=question,
            user_facts=_user_fact_keys(session),
            max_repair_attempts_parse=max_repair_attempts_parse,
        )
        sp_pr.output_summary = {
            "verify_parse": summarize_verification_trace(v_parse),
            "repair_trace_len": len(parse_repair_trace),
            "repair_trace_tail": parse_repair_trace[-3:] if parse_repair_trace else [],
        }
        sp_pr.decision = v_parse.final_decision
    session.layer1 = layer1
    session.layer2 = layer2
    trace["parse_repair"] = parse_repair_trace
    _merge_verification(session, v_parse)
    parse_uncertainty = _build_parse_uncertainty_signal(layer2, clarification_enabled=bool(resolved_run_config.enable_clarification))
    layer2 = _attach_parse_uncertainty_to_layer2(layer2, parse_uncertainty)
    session.layer2 = layer2
    trace["parse_ambiguity_as_confidence_signal"] = bool(parse_uncertainty.get("parse_ambiguity_as_confidence_signal"))
    trace["primary_parse_confidence"] = float(parse_uncertainty.get("primary_parse_confidence") or 0.0)
    trace["batch_bypassable_ambiguity"] = bool(parse_uncertainty.get("batch_bypassable_ambiguity"))
    trace["alternatives_preserved"] = bool(parse_uncertainty.get("alternatives_preserved"))
    ambs = (layer2.diagnostics or {}).get("ambiguities") or []
    if any(a.get("blocking") for a in ambs):
        trace.setdefault("hard_gates_hit", []).append("parse_ambiguity_blocking")
        clarification_enabled = bool(resolved_run_config.enable_clarification)
        usable_primary = _layer2_has_usable_primary_parse(layer2)
        with tc.span("parse_ambiguity_policy") as sp_cl:
            prompts = merge_clarification_prompts_unified(build_parse_ambiguity_prompts(ambs), [])
            sp_cl.output_summary = {
                "blocking_parse_ambiguity": True,
                "clarification_enabled": clarification_enabled,
                "usable_primary_parse": usable_primary,
                "prompt_count": len(prompts),
                "target_kinds": [str((p if isinstance(p, dict) else {}).get("target_kind", "")) for p in prompts[:8]],
            }
        session.clarification_questions = prompts
        trace["clarification_targets_non_blocking"] = prompts[:16]
        trace["parse_ambiguity_non_blocking"] = {
            "clarification_enabled": clarification_enabled,
            "usable_primary_parse": usable_primary,
            "prompt_count": len(prompts),
        }
        trace["stage"].append("parse_ambiguity_non_blocking_continue")

        if usable_primary:
            trace["parse_ambiguity_blocking_bypassed_for_batch"] = True
            trace["parse_best_effort_primary_used"] = True
            trace["parse_alternatives_preserved_in_diagnostics"] = bool(ambs)
            trace["stage"].append("parse_ambiguity_blocking_bypassed")
        else:
            goal_now = dict(getattr(layer2, "goal", None) or {})
            goal_pred_now = str(goal_now.get("predicate") or "").strip().lower()
            goal_args_now = list(goal_now.get("args") or []) if isinstance(goal_now.get("args"), list) else []
            goal_args_signal_now = any(str(x or "").strip() for x in goal_args_now)
            cond_atoms_now = [str(a) for a in (getattr(layer2, "condition_atoms", None) or []) if str(a or "").strip()]
            has_non_generic_condition_now = any(not a.startswith("stated_condition(") for a in cond_atoms_now)
            diag_now = dict(getattr(layer2, "diagnostics", None) or {})
            cond_norm_now = dict(diag_now.get("condition_normalization") or {})
            cn_pred_now = str(cond_norm_now.get("canonical_predicate") or "").strip().lower()
            cn_conf_now = float(cond_norm_now.get("confidence") or 0.0)
            cond_norm_usable_now = cn_pred_now not in {"", "unknown", "stated_condition"} and cn_conf_now >= 0.5
            subj_now = str(getattr(layer2, "subject_normalized", "") or "").strip().lower()
            subj_usable_now = bool(subj_now and not subj_now.startswith("unknown_subject"))
            blocking_count = sum(1 for a in ambs if bool((a or {}).get("blocking")))
            parse_usability_summary = {
                "goal_predicate": goal_pred_now or "unknown",
                "goal_args_has_signal": goal_args_signal_now,
                "has_non_generic_condition_atom": has_non_generic_condition_now,
                "condition_normalization_usable": cond_norm_usable_now,
                "subject_usable": subj_usable_now,
                "ambiguity_count": len(ambs),
                "blocking_ambiguity_count": blocking_count,
            }
            trace["parse_ambiguity_blocking_bypassed_for_batch"] = False
            trace["parse_best_effort_primary_used"] = False
            trace["parse_alternatives_preserved_in_diagnostics"] = bool(ambs)
            trace["parse_ambiguity_blocking_no_usable_primary_batch"] = True
            trace["parse_non_usable_summary"] = parse_usability_summary
            trace["stage"].append("parse_ambiguity_blocking_no_usable_primary_batch")
            trace["parse_non_usable_non_blocking_continue"] = True
    if v_parse.final_decision == "REJECT":
        trace.setdefault("hard_gates_hit", []).append("parse_verification_reject")
        with tc.span("parse_reject_policy") as spx:
            spx.output_summary = {"reason": "parse_rejected_non_blocking_continue"}
        trace["parse_rejected_non_blocking"] = True
        trace["stage"].append("parse_rejected_non_blocking_continue")

    selector = domain_selector or SimpleDomainSelector()
    routing_dict = {"layer1": layer1, "layer2": layer2, "question": question}
    trace["domain_hint_ignored"] = True
    routing = selector.select(
        routing_dict,
        registry=rulebase_registry,
    )
    if not isinstance(routing, DomainRoutingPlan):
        routing = DomainRoutingPlan.model_validate(routing)
    policy = default_policy_for_routing(
        allow_cross_domain_expansion=routing.allow_cross_domain_expansion,
        triggered_bridges=list(routing.triggered_bridges),
    )
    routing = resolved_run_config.apply_routing_plan(routing)
    policy = resolved_run_config.apply_cross_domain_policy(policy)
    trace["domain_routing"] = routing.model_dump(mode="json")

    with tc.span("retrieve_rules") as sp_rr:
        ranked: list[tuple[RuleRecord, float, dict[str, Any]]]
        merged_index: RulebaseIndex
        if rulebase_registry is not None and retriever_advanced is not None:
            ret_res, ranked_all, ri_full = retriever_advanced.retrieve(
                layer1, layer2, routing, top_k_final=top_k
            )
            trace["retrieval_result"] = ret_res.model_dump(mode="json")
            ranked_primary, rejected_pf = filter_ranked_for_primary_phase(
                ranked_all,
                primary_domains=list(routing.primary_domains),
                include_shared=routing.include_shared,
            )
            ranked, _exp, _used_dom = merge_secondary_with_policy(
                ranked_primary,
                ranked_all,
                secondary_domains=list(routing.secondary_domains),
                policy=policy,
                triggered_bridges=list(routing.triggered_bridges),
            )
            trace["rejected_candidates_domain_filter"] = rejected_pf[:32]
            ri = ri_full
            merged_index = ri_full
        elif rulebase_registry is not None and domain_retriever is not None:
            ranked_all, merged_index = domain_retriever.retrieve(
                layer1,
                layer2,
                list(routing.primary_domains),
                include_shared=routing.include_shared,
                top_k=top_k,
            )
            ranked_primary, rejected_pf = filter_ranked_for_primary_phase(
                ranked_all,
                primary_domains=list(routing.primary_domains),
                include_shared=routing.include_shared,
            )
            ranked, _exp, _used_dom = merge_secondary_with_policy(
                ranked_primary,
                ranked_all,
                secondary_domains=list(routing.secondary_domains),
                policy=policy,
                triggered_bridges=list(routing.triggered_bridges),
            )
            trace["rejected_candidates_domain_filter"] = rejected_pf[:32]
            ri = merged_index
        else:
            ri = rule_index or get_rulebase_index()
            ranked_all = retrieve_rules(layer1=layer1, layer2=layer2, top_k=top_k, index=ri)
            ranked_all = enrich_ranked_with_retrieval_meta(ranked_all)
            ranked_primary, rejected_pf = filter_ranked_for_primary_phase(
                ranked_all,
                primary_domains=list(routing.primary_domains),
                include_shared=routing.include_shared,
            )
            ranked, _exp, _used_dom = merge_secondary_with_policy(
                ranked_primary,
                ranked_all,
                secondary_domains=list(routing.secondary_domains),
                policy=policy,
                triggered_bridges=list(routing.triggered_bridges),
            )
            trace["rejected_candidates_domain_filter"] = rejected_pf[:32]
            merged_index = ri
        session.retrieved_rules = [r for r, _, _ in ranked]
        top_limit = min(10, len(ranked))
        top_rows = [
            {
                "rule_id": r.rule_id,
                "score_total": s,
                "matched_features": (d.get("matched_features") or [])[:12],
                "score_components": d.get("score_components") or {},
                "rulebase_id": d.get("rulebase_id"),
                "domain": d.get("domain"),
                "layer": d.get("layer"),
                "source_doc": d.get("source_doc"),
                "source_article": d.get("source_article"),
                "retrieval_scope": d.get("retrieval_scope"),
            }
            for r, s, d in ranked[:top_limit]
        ]
        sp_rr.output_summary = {
            "domain_routing": routing.model_dump(mode="json"),
            "top_rule_ids": [r.rule_id for r, _, _ in ranked[:8]],
            "top": top_rows,
            "final_top10_score_breakdown": top_rows,
        }
    trace["stage"].append("retrieve_done")
    trace["rule_retrieval"] = {
        "backend": "advanced_domain_per_scope" if retriever_advanced is not None else "hybrid_bm25_structured",
        "top": (sp_rr.output_summary or {}).get("top", []),
        "final_top10_score_breakdown": (sp_rr.output_summary or {}).get("final_top10_score_breakdown", []),
        "domain_hint_ignored": True,
    }
    apply_retrieval_backend(
        trace["backend_modes"],
        backend=trace["rule_retrieval"].get("backend"),
        retrieved_count=len(ranked),
    )
    trace["retrieved_rules_by_domain"] = _group_retrieved_by_domain(ranked)

    # Phase 3: Apply temporal, conflict, and bridge filtering post-retrieval
    with tc.span("phase3_post_retrieve") as sp_p3:
        p3_result = apply_phase3_post_retrieve(
            ranked=ranked,
            session=session,
            question=question,
            routing=routing,
            rulebase_registry=rulebase_registry,
            question_time_explicit=question_time,
            trace=trace,
        )
        ranked = p3_result.ranked
        trace["phase3"] = {
            "question_time_utc": p3_result.question_time_iso,
            "temporal_rejected": p3_result.temporal_rejected[:16],
            "conflict_rejected": p3_result.conflict_rejected[:16],
            "bridge_emitted": [x.model_dump(mode="json") for x in p3_result.bridge_emitted],
            "rule_id_collision_warnings": p3_result.rule_id_collision_warnings,
        }
        sp_p3.output_summary = {
            "question_time": p3_result.question_time_iso,
            "temporal_rejected_count": len(p3_result.temporal_rejected),
            "conflict_rejected_count": len(p3_result.conflict_rejected),
            "bridge_emitted_count": len(p3_result.bridge_emitted),
            "final_ranked_count": len(ranked),
        }

    ctx = ReasoningContext(
        primary_domains=list(routing.primary_domains),
        secondary_domains=list(routing.secondary_domains),
        active_rulebases=collect_rulebase_ids_from_index(merged_index.rules),
        include_shared=routing.include_shared,
        question_time=question_time or p3_result.question_time_iso,
        statute_ids=[],
        cross_domain_policy=policy,
        triggered_bridges=list(routing.triggered_bridges),
    )
    trace["reasoning_context"] = ctx.to_trace_dict()

    goal = layer2.goal

    selected: RuleRecord | None = None
    bstate: ReasoningState | None = None
    rescued_fallback_flow = False

    if not resolved_run_config.enable_backward_chaining:
        trace.setdefault("hard_gates_hit", []).append("backward_disabled_by_run_config")
        with tc.span("pipeline_exit") as spx:
            spx.output_summary = {"reason": "backward_disabled_by_run_config"}
        selected = ranked[0][0] if ranked else None
        bstate = ReasoningState(
            requirement_set=[],
            missing_facts=[],
            selected_rule_ids=[selected.rule_id] if selected else [],
            goal_status="failed",
            trace=["backward_disabled_non_blocking_continue"],
        )
    else:
        with tc.span("rule_backward_gate") as sp_b:
            pass
        rg = gate_rule_and_backward(
            engine,
            goal=goal,
            layer2=layer2,
            ranked=ranked,
            known_facts=known_facts_for_reasoning(session),
            rule_index=ri,
            max_rule_repair=max_repair_attempts_rule,
            max_backward_repair=max_repair_attempts_backward,
            reasoning_context=ctx,
            cross_domain_policy=policy,
            structured_facts=structured_facts_for_reasoning(session),
            question_mode=question_mode,
        )

        trace["rule_backward_gate"] = rg.trace
        trace["verification_diagnostics"] = list(rg.candidate_verdicts.values())

        if not rg.ok and rg.error == "no_grounded_rule_found":
            forced_atoms = _collect_plan_retry_condition_atoms(layer2)
            if forced_atoms:
                retry_layer2 = build_layer2(
                    layer1,
                    user_facts=_user_fact_keys(session),
                    forced_condition_atoms=forced_atoms,
                )
                retried = retrieve_rules(layer1=layer1, layer2=retry_layer2, top_k=max(top_k, 12), index=merged_index)
                retried = enrich_ranked_with_retrieval_meta(retried)
                retried_primary, _ = filter_ranked_for_primary_phase(
                    retried,
                    primary_domains=list(routing.primary_domains),
                    include_shared=routing.include_shared,
                )
                retried_final, _exp, _used_dom = merge_secondary_with_policy(
                    retried_primary,
                    retried,
                    secondary_domains=list(routing.secondary_domains),
                    policy=policy,
                    triggered_bridges=list(routing.triggered_bridges),
                )
                trace["plan_empty_condition_retry"] = {
                    "forced_condition_atoms": forced_atoms,
                    "retry_goal": retry_layer2.goal,
                    "retry_condition_atoms": retry_layer2.condition_atoms,
                    "retrieved_rule_ids": [r.rule_id for r, _s, _d in retried_final[:8]],
                }
                if retried_final:
                    ranked = retried_final
                    layer2 = retry_layer2
                    session.layer2 = retry_layer2
                    goal = retry_layer2.goal
                    rg = gate_rule_and_backward(
                        engine,
                        goal=goal,
                        layer2=layer2,
                        ranked=ranked,
                        known_facts=known_facts_for_reasoning(session),
                        rule_index=ri,
                        max_rule_repair=max_repair_attempts_rule,
                        max_backward_repair=max_repair_attempts_backward,
                        reasoning_context=ctx,
                        cross_domain_policy=policy,
                        structured_facts=structured_facts_for_reasoning(session),
                        question_mode=question_mode,
                    )
                    trace["rule_backward_gate_condition_retry"] = rg.trace
                    trace["verification_diagnostics_condition_retry"] = list(rg.candidate_verdicts.values())

        if not rg.ok and ranked:
            def _retry_retrieval(attempt: int) -> list[tuple[RuleRecord, float, dict[str, Any]]]:
                widened_top_k = max(top_k * (attempt + 1), len(ranked) + 4)
                retried = retrieve_rules(layer1=layer1, layer2=layer2, top_k=widened_top_k, index=merged_index)
                retried = enrich_ranked_with_retrieval_meta(retried)
                retried_primary, _ = filter_ranked_for_primary_phase(
                    retried,
                    primary_domains=list(routing.primary_domains),
                    include_shared=routing.include_shared,
                )
                retried_final, _exp, _used_dom = merge_secondary_with_policy(
                    retried_primary,
                    retried,
                    secondary_domains=list(routing.secondary_domains),
                    policy=policy,
                    triggered_bridges=list(routing.triggered_bridges),
                )
                return retried_final

            repaired_ranked, retrieval_repair_trace, retrieval_repair_summary = run_retrieval_repair_loop(
                ranked=ranked,
                top_k_before=top_k,
                repair_reason=rg.error or "rule_backward_gate_failed",
                retrieve_retry_fn=_retry_retrieval,
                max_attempts=1,
            )
            trace["retrieval_ranking_repair"] = retrieval_repair_trace
            trace["retrieval_ranking_repair_summary"] = retrieval_repair_summary

            if repaired_ranked:
                ranked = repaired_ranked
                session.retrieved_rules = [r for r, _, _ in ranked]
                rg = gate_rule_and_backward(
                    engine,
                    goal=goal,
                    layer2=layer2,
                    ranked=ranked,
                    known_facts=known_facts_for_reasoning(session),
                    rule_index=ri,
                    max_rule_repair=max_repair_attempts_rule,
                    max_backward_repair=max_repair_attempts_backward,
                    reasoning_context=ctx,
                    cross_domain_policy=policy,
                    structured_facts=structured_facts_for_reasoning(session),
                    question_mode=question_mode,
                )
                trace["rule_backward_gate_rerun"] = rg.trace
                trace["verification_diagnostics_after_repair"] = list(rg.candidate_verdicts.values())

        if rg.v_rule:
            _merge_verification(session, rg.v_rule)
        if rg.v_back:
            _merge_verification(session, rg.v_back)
        sp_b.output_summary = {
            "gate_ok": rg.ok,
            "clarification_needed": rg.clarification_needed,
            "tried_rule_ids": rg.tried_rule_ids,
            "error": rg.error,
            "verify_rule": summarize_verification_trace(rg.v_rule) if rg.v_rule else {},
            "verify_backward": summarize_verification_trace(rg.v_back) if rg.v_back else {},
        }
        sp_b.decision = rg.v_back.final_decision if rg.v_back else (rg.v_rule.final_decision if rg.v_rule else "none")
        if not rg.ok:
            trace.setdefault("hard_gates_hit", []).append("rule_backward_gate_failure")
            with tc.span("pipeline_exit") as spx:
                spx.output_summary = {"reason": rg.error or "rule_backward_gate_failed_non_blocking_continue"}
            selected = rg.selected or (ranked[0][0] if ranked else None)
            bstate = rg.bstate or ReasoningState(
                requirement_set=[],
                missing_facts=[],
                selected_rule_ids=[selected.rule_id] if selected else [],
                goal_status="failed",
                trace=["rule_backward_gate_failed_non_blocking_continue"],
            )
            trace["rule_backward_gate_non_blocking"] = {
                "error": rg.error,
                "tried_rule_ids": list(rg.tried_rule_ids or []),
            }
        else:
            selected = rg.selected
            bstate = rg.bstate
            rescued_fallback_flow = bool(getattr(rg, "rescued_fallback_flow", False))

    session.reasoning = bstate
    session.selected_rule = selected

    if rg.clarification_needed and bstate and question_mode not in {"rule_reading"}:
        trace.setdefault("hard_gates_hit", []).append("needs_clarification")
        with tc.span("clarification_non_blocking") as sp_cl:
            parse_ambs = (layer2.diagnostics or {}).get("ambiguities") or []
            parse_prompts = build_parse_ambiguity_prompts([a for a in parse_ambs if not a.get("blocking")])
            filtered_missing = filter_clarification_targets(
                bstate.missing_facts,
                known_facts=session.known_facts,
                parse_layer2=layer2,
            )
            backward_prompts = build_clarification_prompts_from_requirements(
                filtered_missing,
                bstate.requirement_set,
                backward_plan=bstate.backward_plan,
                related_rule_id=selected.rule_id if selected else None,
            )
            prompts = merge_clarification_prompts_unified(parse_prompts, backward_prompts)
            sp_cl.output_summary = {
                "backward_missing_facts": bool(bstate.missing_facts),
                "prompt_count": len(prompts),
                "missing_facts": bstate.missing_facts,
                "non_blocking_continue": True,
            }
        session.missing_facts = bstate.missing_facts
        session.clarification_questions = prompts
        trace["clarification_non_blocking"] = {
            "clarification_enabled": bool(resolved_run_config.enable_clarification),
            "prompt_count": len(prompts),
            "missing_facts": list(getattr(bstate, "missing_facts", []) or []),
            "rescued_fallback_flow": rescued_fallback_flow,
        }
        if rescued_fallback_flow and bool(getattr(rg, "rescued_missing_facts_materiality_hold", False)):
            trace["rescued_missing_facts_conditional_answer_non_blocking"] = True
        trace["stage"].append("clarification_non_blocking_continue")

    if bstate is None:
        trace.setdefault("hard_gates_hit", []).append("no_reasoning_state")
        bstate = ReasoningState(
            requirement_set=[],
            missing_facts=[],
            selected_rule_ids=[selected.rule_id] if selected else [],
            goal_status="failed",
            trace=["missing_reasoning_state_non_blocking_continue"],
        )
        session.reasoning = bstate

    if selected is None:
        trace.setdefault("hard_gates_hit", []).append("no_selected_rule")
        selected = RuleRecord(
            rule_id="RULE_FALLBACK_UNKNOWN",
            logic_form="fallback_rule",
            head={"predicate": "unknown", "args": []},
            body=[],
            metadata={"fallback": True, "reason": "no_selected_rule_non_blocking_continue"},
        )
        session.selected_rule = selected

    selected_semantic_ctx = dict((rg.candidate_verdicts or {}).get(str(selected.rule_id), {}) or {}) if rg else {}

    with tc.span("forward_gate") as sp_f:
        fg = gate_forward_reasoning(
            engine,
            goal=goal,
            selected=selected,
            ranked=ranked,
            session=session,
            known_facts=known_facts_for_reasoning(session),
            backward_plan_dict=bstate.backward_plan,
            backward_state=bstate,
            max_forward_repair=max_repair_attempts_forward,
            reasoning_context=ctx,
            cross_domain_policy=policy,
            phase3_proof_context=p3_result.proof_phase3_context,
            rescued_fallback_flow=rescued_fallback_flow,
            semantic_match_context={
                "semantic_family_match_tier": selected_semantic_ctx.get("semantic_family_match_tier"),
                "semantic_soft_match_triggered": selected_semantic_ctx.get("semantic_family_soft_match_triggered"),
                "semantic_soft_match_reason": selected_semantic_ctx.get("semantic_family_soft_match_reason"),
            },
            question_mode=question_mode,
        )
        trace["forward_gate"] = fg.trace
        if fg.v_fwd:
            _merge_verification(session, fg.v_fwd)
        sp_f.output_summary = {
            "gate_ok": fg.ok,
            "verify_forward": summarize_verification_trace(fg.v_fwd) if fg.v_fwd else {},
            "error": fg.error,
        }
        sp_f.decision = fg.v_fwd.final_decision if fg.v_fwd else "none"

    if not fg.ok:
        trace.setdefault("hard_gates_hit", []).append("forward_gate_failure")
        with tc.span("pipeline_exit") as spx:
            spx.output_summary = {"reason": fg.error or "forward_verification_failed_non_blocking_continue"}

    conclusion = fg.conclusion or (proof := fg.proof_obj) and (proof.conclusion or proof.derived_conclusion) or "Kết luận chưa đủ điều kiện xác minh đầy đủ."
    goal_ok = bool(fg.goal_achieved)
    fstate = fg.fstate or bstate
    proof = fg.proof_obj
    if proof is None:
        trace.setdefault("hard_gates_hit", []).append("no_proof")
        proof = ProofObject(
            proof_id=f"proof_fallback_{session.session_id}",
            selected_rule=selected.rule_id if selected else None,
            conclusion=conclusion,
            derived_conclusion=conclusion,
            fail_stage="forward_gate",
        )
        trace["no_proof_non_blocking_fallback"] = True
    session.reasoning = fstate
    session.proof = proof
    if fstate and fstate.forward_result and fstate.forward_result.get("rule_id"):
        forward_rule_id = str(fstate.forward_result.get("rule_id") or "")
        selected_rule_id = str(selected.rule_id) if selected else ""
        if selected_rule_id and forward_rule_id and forward_rule_id != selected_rule_id:
            logger.warning(
                "forward_rule_mismatch_with_selected_rule session_id=%s selected_rule_id=%s forward_rule_id=%s",
                session.session_id,
                selected_rule_id,
                forward_rule_id,
            )
            trace["forward_rule_mismatch_with_selected_rule"] = {
                "selected_rule_id": selected_rule_id,
                "forward_rule_id": forward_rule_id,
                "overwrite_blocked": True,
            }
            trace["forward_low_confidence_due_to_rule_mismatch"] = True
    session.selected_rule = selected

    with tc.span("proof") as sp_p:
        sp_p.output_summary = {
            "proof_id": proof.proof_id,
            "step_count": len(proof.proof_steps or []),
            "derived_conclusion_excerpt": (proof.derived_conclusion or "")[:300],
        }
    trace["proof_steps_by_domain"] = _proof_steps_by_domain(proof)

    with tc.span("retrieve_evidence") as sp_ev:
        ev = (evidence_retriever or get_evidence_retriever()).retrieve(
            question=question,
            rule=selected,
            conclusion=conclusion,
            top_k=5,
            proof_summary=_proof_summary_for_evidence(proof),
            goal=goal,
            modality_text=layer1.modality_text or "",
            layer1=layer1,
            layer2=layer2,
        )
        evidence_bundle = build_evidence_bundle(
            query=question,
            selected_rule=selected,
            requirement_set=list(bstate.requirement_set or []),
            proof=proof,
            snippets=ev,
        )
        trace["evidence_stage"] = {
            "bundle_id": evidence_bundle.bundle_id,
            "selected_rule_id": evidence_bundle.selected_rule_id,
            "linkage_map": evidence_bundle.linkage_map,
            "items": [x.model_dump(mode="json") for x in evidence_bundle.items],
        }
        sp_ev.output_summary = summarize_evidence_trace(ev)
    trace["final_grounding_docs"] = _grounding_docs_from_evidence(ev)

    with tc.span("generate_answer") as sp_ga:
        ans = generate_answer(
            question=question,
            conclusion=conclusion,
            proof=proof,
            evidence=ev,
            evidence_bundle=evidence_bundle,
            goal_achieved=goal_ok,
            rule=selected,
        )
        apply_answer_backend(trace["backend_modes"], ans)
        sp_ga.output_summary = summarize_answer_trace(ans)

    # Apply conditional answer BEFORE repair so verifier validates the final form (policy A+B)
    missing_facts_now, has_missing_signal = _collect_application_policy_missing_facts(
        bstate=bstate,
        fstate=fstate,
    )
    ans, _ = _apply_application_answer_policy(
        ans=ans,
        trace=trace,
        session=session,
        question_mode=question_mode,
        selected_rule=selected,
        known_fact_keys=list(known_facts_for_reasoning(session).keys()),
        missing_facts=missing_facts_now,
        has_missing_signal=has_missing_signal,
        mode_tag="ask_missing_facts_conditional",
    )

    with tc.span("answer_repair") as sp_ar:
        ans_text, v_ans, answer_repair_trace = run_answer_repair_loop(
            engine,
            answer_text=ans.answer_text,
            conclusion=conclusion,
            proof=proof.model_dump(mode="json"),
            evidence_bundle=evidence_bundle.model_dump(mode="json"),
            modality_expected=layer1.modality_text or "",
            goal_action=str(goal.get("args", ["", "", ""])[1] if len(goal.get("args", [])) > 1 else ""),
            action_token_in_answer=ans.answer_text,
            question_mode=question_mode,
            missing_facts=missing_facts_now,
            max_repair_attempts_answer=max_repair_attempts_answer,
        )
        apply_answer_text_and_refresh_citations(ans, ans_text)
        ans.verification_summary += f";answer_repair_attempts={answer_repair_trace[-1].get('attempts_used', 0)}"
        trace["answer_repair"] = answer_repair_trace
        _merge_verification(session, v_ans)
        sp_ar.output_summary = {
            "verify_answer": summarize_verification_trace(v_ans),
            "attempts_used": answer_repair_trace[-1].get("attempts_used", 0) if answer_repair_trace else 0,
            "trace_tail": answer_repair_trace[-2:] if answer_repair_trace else [],
        }
        sp_ar.decision = v_ans.final_decision

    if v_ans.final_decision == "REJECT" and (answer_reject_allow_fallback or rescued_fallback_flow):
        if _should_use_honest_degraded_answer(
            selected=selected,
            goal=goal,
            proof=proof,
            failure_reason="answer_verification_reject",
        ):
            reg = generate_honest_degraded_answer(
                question=question,
                reason="answer_verification_reject",
                selected_rule=selected,
                goal=goal,
                retrieved_rules=[r for r, _s, _d in ranked[:3]],
            )
            reg.verification_summary = ans.verification_summary + ";answer_fallback_honest_degraded"
        else:
            reg = safe_regenerate_final_answer(
                conclusion,
                proof=proof,
                evidence=ev,
                rule=selected,
                goal_achieved=goal_ok,
            )
            reg.verification_summary = ans.verification_summary + (
                ";answer_fallback_regenerate_on_reject_rescued_flow"
                if rescued_fallback_flow
                else ";answer_fallback_regenerate_on_reject"
            )
        ans = reg
        if rescued_fallback_flow:
            trace["answer_verification_rescued_relaxation"] = {
                "triggered": True,
                "original_final_decision": "REJECT",
                "relaxed_action": "allow_fallback_regeneration",
                "reason": "rescued_fallback_answer_verification_relaxation",
            }
    elif v_ans.final_decision == "REJECT":
        trace.setdefault("hard_gates_hit", []).append("answer_verification_reject_no_fallback")
        ans.verification_summary += ";answer_verification_rejected_no_fallback"
        trace["answer_verification"] = {"final_decision": "REJECT", "note": "no_fallback_per_policy"}

    ans = _apply_parse_uncertainty_answer_policy(
        ans=ans,
        layer2=layer2,
        trace=trace,
        context_tag="ask.final_answer",
    )

    ans = _apply_user_facing_forward_failure_policy(
        ans,
        selected_rule=selected,
        forward_failed=bool(not fg.ok),
        trace=trace,
        layer1=layer1,
    )

    ans = _enforce_reasoning_failure_answer_policy(
        ans,
        question=question,
        layer2=layer2,
        selected=selected,
        goal=goal,
        ranked=ranked,
        evidence=ev,
        phase3_result=None,
        forward_failed=bool(not fg.ok),
        answer_rejected=bool(v_ans.final_decision == "REJECT"),
        trace=trace,
    )

    trace["flow_trace"] = _build_missing_facts_stage_trace(
        question_mode=question_mode,
        bstate=bstate,
        fstate=fstate,
        fg_ok=bool(fg.ok),
        v_ans_decision=str(v_ans.final_decision),
    )

    session.answer = ans
    
    # Build ReasoningResult as first-class artifact
    reasoning_result_dict: dict[str, Any] = {
        "active_domains_used": list(ctx.primary_domains),
    }
    reasoning_result_data = _finalize_reasoning_result_dict(
        reasoning_result_dict,
        proof=proof,
        ranked=ranked,
        bstate=bstate,
        fstate=fstate,
        selected=selected,
        phase3_result=None,
    )
    trace["reasoning_result"] = reasoning_result_data
    
    trace["stage"].append("complete")
    session.pipeline_trace = trace
    _merge_pipeline_trace_dict(trace, tc)
    svc.save(session)

    return AskResponse(
        session_id=session.session_id,
        needs_clarification=False,
        layer1=layer1,
        layer2=layer2,
        verification_trace=session.verification_logs,
        retrieved_rules=[_rule_dump(r) for r, s, d in ranked[:8]],
        selected_rule=_rule_dump(selected),
        reasoning=fstate,
        proof=proof,
        evidence_bundle=evidence_bundle,
        answer=ans,
        reasoning_result=reasoning_result_data,
        debug_trace=trace,
    )


def run_clarify(
    *,
    session_id: str,
    answers: list[dict[str, Any]],
    session_svc: SessionService | None = None,
    nesy: NeSyEngine | None = None,
    rule_index: RulebaseIndex | None = None,
    rulebase_registry: RulebaseRegistry | None = None,
    domain_retriever: DomainScopedRuleRetriever | None = None,
    retriever_advanced: AdvancedDomainRetriever | None = None,
    domain_selector: SimpleDomainSelector | None = None,
    evidence_retriever: EvidenceRetriever | None = None,
    top_k: int = 8,
    max_repair_attempts_parse: int = 2,
    max_repair_attempts_answer: int = 2,
    max_repair_attempts_rule: int = 2,
    max_repair_attempts_backward: int = 1,
    max_repair_attempts_forward: int = 1,
    answer_reject_allow_fallback: bool = False,
    settings: Any | None = None,
    trace_collector: TraceCollector | None = None,
    run_config: ExperimentRunConfig | dict[str, Any] | str | Path | None = None,
) -> ClarifyResponse:
    svc = session_svc or get_session_service()
    engine = nesy or NeSyEngine(nesy_nli_mock=True)
    tc = trace_collector or TraceCollector.noop()
    resolved_run_config = _resolve_run_config(run_config)
    session = svc.get(session_id)
    if not session:
        raise KeyError("session_not_found")

    pre_missing = list((session.reasoning.missing_facts if session.reasoning else session.missing_facts) or [])
    pre_status = "needs_clarification" if bool(pre_missing or session.clarification_questions) else "open"
    pre_proof = session.proof

    normalized_answers, invalid_clarification_answers = normalize_clarification_answers_with_diagnostics(
        answers,
        list(session.clarification_questions or []),
    )
    svc.merge_fact_answers(session, normalized_answers)
    question = session.original_question
    if not tc._noop:
        tc.question_text = question or ""
        tc.session_id = session_id

    forced = extract_resolved_condition_atoms_from_known_facts(session.known_facts)

    trace: dict[str, Any] = {
        "stage": ["clarify_resume"],
        "query_text": question,
        "clarification_answers": list(normalized_answers or []),
        "invalid_clarification_answers": list(invalid_clarification_answers or []),
        "invalid_clarification_answer": bool(invalid_clarification_answers),
        "backend_modes": init_backend_modes(verifier_engine=engine),
        "run_config": resolved_run_config.to_trace_dict(),
        "clarification_enabled": bool(resolved_run_config.enable_clarification),
        "hard_gates_hit": [],
    }

    parse_unavailable_meta: dict[str, Any] | None = None
    with tc.span("parse_layer1") as sp_l1:
        try:
            if session.layer1 is not None and session.layer2 is not None:
                layer1 = session.layer1
                layer2 = session.layer2
            else:
                layer1, layer2, _parse_meta = _parse_query_for_runtime(
                    question,
                    user_facts=_user_fact_keys(session),
                    forced_condition_atoms=forced if forced else None,
                    settings=settings,
                )
            sp_l1.output_summary = summarize_layer1_trace(layer1)
        except ParserUnavailableError as e:
            parse_unavailable_meta = dict(e.parse_metadata or {})
            parse_unavailable_meta.setdefault("requested_mode", "llm_real")
            parse_unavailable_meta.setdefault("actual_mode", "parse_unavailable")
            parse_unavailable_meta.setdefault("parser_available", False)
            parse_unavailable_meta.setdefault("parser_error", e.parser_error or "parse_unavailable")
            sp_l1.output_summary = {
                "requested_mode": parse_unavailable_meta.get("requested_mode"),
                "actual_mode": parse_unavailable_meta.get("actual_mode"),
                "provider": parse_unavailable_meta.get("provider") or parse_unavailable_meta.get("parser_provider"),
                "model": parse_unavailable_meta.get("model") or parse_unavailable_meta.get("parser_model"),
                "parser_available": parse_unavailable_meta.get("parser_available"),
                "parser_error": parse_unavailable_meta.get("parser_error"),
            }
            sp_l1.decision = "parse_unavailable"

    if parse_unavailable_meta is not None:
        trace.setdefault("hard_gates_hit", []).append("parse_unavailable")
        layer1 = _layer1_parse_unavailable(parse_unavailable_meta)
        layer2 = build_layer2(layer1, user_facts=_user_fact_keys(session))
        session.layer1 = layer1
        session.layer2 = layer2
        apply_parse_backend(trace["backend_modes"], layer1)
        trace["parser_status"] = dict(layer1.parse_metadata or {})
        trace["stage"].append("parse_unavailable")

    with tc.span("parse_layer2") as sp_l2:
        sp_l2.output_summary = summarize_layer2_trace(layer2)
    session.layer1 = layer1
    session.layer2 = layer2
    trace["parser_status"] = dict(getattr(layer1, "parse_metadata", None) or {})
    question_mode = _infer_question_mode(layer1, layer2)
    trace["question_mode"] = question_mode

    with tc.span("parse_repair") as sp_pr:
        layer1, layer2, _v_parse_cl, parse_repair_trace = run_parse_repair_loop(
            engine,
            layer1=layer1,
            layer2=layer2,
            question_text=question,
            user_facts=_user_fact_keys(session),
            max_repair_attempts_parse=max_repair_attempts_parse,
        )
        sp_pr.output_summary = {
            "verify_parse": summarize_verification_trace(_v_parse_cl),
            "repair_trace_len": len(parse_repair_trace),
        }
        sp_pr.decision = _v_parse_cl.final_decision
    session.layer1 = layer1
    session.layer2 = layer2
    apply_parse_backend(trace["backend_modes"], layer1)
    trace["parse_repair"] = parse_repair_trace
    _merge_verification(session, _v_parse_cl)
    parse_uncertainty = _build_parse_uncertainty_signal(
        layer2,
        clarification_enabled=bool(resolved_run_config.enable_clarification),
    )
    layer2 = _attach_parse_uncertainty_to_layer2(layer2, parse_uncertainty)
    session.layer2 = layer2
    trace["parse_ambiguity_as_confidence_signal"] = bool(parse_uncertainty.get("parse_ambiguity_as_confidence_signal"))
    trace["primary_parse_confidence"] = float(parse_uncertainty.get("primary_parse_confidence") or 0.0)
    trace["batch_bypassable_ambiguity"] = bool(parse_uncertainty.get("batch_bypassable_ambiguity"))
    trace["alternatives_preserved"] = bool(parse_uncertainty.get("alternatives_preserved"))
    parse_ambs = (layer2.diagnostics or {}).get("ambiguities") or []
    if any(a.get("blocking") for a in parse_ambs):
        trace.setdefault("hard_gates_hit", []).append("parse_ambiguity_blocking")
        clarification_enabled = bool(resolved_run_config.enable_clarification)
        usable_primary = _layer2_has_usable_primary_parse(layer2)
        with tc.span("parse_ambiguity_policy") as sp_cl:
            prompts = merge_clarification_prompts_unified(build_parse_ambiguity_prompts(parse_ambs), [])
            sp_cl.output_summary = {
                "blocking_parse_ambiguity": True,
                "clarification_enabled": clarification_enabled,
                "usable_primary_parse": usable_primary,
                "prompt_count": len(prompts),
                "target_kinds": [str((p if isinstance(p, dict) else {}).get("target_kind", "")) for p in prompts[:8]],
            }
        session.clarification_questions = prompts
        trace["clarification_targets_non_blocking"] = prompts[:16]
        trace["parse_ambiguity_non_blocking"] = {
            "clarification_enabled": clarification_enabled,
            "usable_primary_parse": usable_primary,
            "prompt_count": len(prompts),
        }
        trace["stage"].append("parse_ambiguity_non_blocking_continue")

        if usable_primary:
            trace["parse_ambiguity_blocking_bypassed_for_batch"] = True
            trace["parse_best_effort_primary_used"] = True
            trace["parse_alternatives_preserved_in_diagnostics"] = bool(parse_ambs)
            trace["stage"].append("parse_ambiguity_blocking_bypassed")
        else:
            goal_now = dict(getattr(layer2, "goal", None) or {})
            goal_pred_now = str(goal_now.get("predicate") or "").strip().lower()
            goal_args_now = list(goal_now.get("args") or []) if isinstance(goal_now.get("args"), list) else []
            goal_args_signal_now = any(str(x or "").strip() for x in goal_args_now)
            cond_atoms_now = [str(a) for a in (getattr(layer2, "condition_atoms", None) or []) if str(a or "").strip()]
            has_non_generic_condition_now = any(not a.startswith("stated_condition(") for a in cond_atoms_now)
            diag_now = dict(getattr(layer2, "diagnostics", None) or {})
            cond_norm_now = dict(diag_now.get("condition_normalization") or {})
            cn_pred_now = str(cond_norm_now.get("canonical_predicate") or "").strip().lower()
            cn_conf_now = float(cond_norm_now.get("confidence") or 0.0)
            cond_norm_usable_now = cn_pred_now not in {"", "unknown", "stated_condition"} and cn_conf_now >= 0.5
            subj_now = str(getattr(layer2, "subject_normalized", "") or "").strip().lower()
            subj_usable_now = bool(subj_now and not subj_now.startswith("unknown_subject"))
            blocking_count = sum(1 for a in parse_ambs if bool((a or {}).get("blocking")))
            parse_usability_summary = {
                "goal_predicate": goal_pred_now or "unknown",
                "goal_args_has_signal": goal_args_signal_now,
                "has_non_generic_condition_atom": has_non_generic_condition_now,
                "condition_normalization_usable": cond_norm_usable_now,
                "subject_usable": subj_usable_now,
                "ambiguity_count": len(parse_ambs),
                "blocking_ambiguity_count": blocking_count,
            }
            trace["parse_ambiguity_blocking_bypassed_for_batch"] = False
            trace["parse_best_effort_primary_used"] = False
            trace["parse_alternatives_preserved_in_diagnostics"] = bool(parse_ambs)
            trace["parse_ambiguity_blocking_no_usable_primary_batch"] = True
            trace["parse_non_usable_summary"] = parse_usability_summary
            trace["stage"].append("parse_ambiguity_blocking_no_usable_primary_batch")
            trace["parse_non_usable_non_blocking_continue"] = True

    if _v_parse_cl.final_decision == "REJECT":
        trace.setdefault("hard_gates_hit", []).append("parse_verification_reject")
        with tc.span("parse_reject_policy") as spx:
            spx.output_summary = {"reason": "parse_rejected_non_blocking_continue"}
        trace["parse_rejected_non_blocking"] = True
        trace["stage"].append("parse_rejected_non_blocking_continue")

    selector = domain_selector or SimpleDomainSelector()
    routing = selector.select(
        {"layer1": layer1, "layer2": layer2, "question": question},
        registry=rulebase_registry,
    )
    if not isinstance(routing, DomainRoutingPlan):
        routing = DomainRoutingPlan.model_validate(routing)
    policy = default_policy_for_routing(
        allow_cross_domain_expansion=routing.allow_cross_domain_expansion,
        triggered_bridges=list(routing.triggered_bridges),
    )
    routing = resolved_run_config.apply_routing_plan(routing)
    policy = resolved_run_config.apply_cross_domain_policy(policy)
    trace["domain_routing"] = routing.model_dump(mode="json")

    with tc.span("retrieve_rules") as sp_rr:
        ranked: list[tuple[RuleRecord, float, dict[str, Any]]]
        merged_index: RulebaseIndex
        if rulebase_registry is not None and retriever_advanced is not None:
            ret_res, ranked_all, ri_full = retriever_advanced.retrieve(
                layer1, layer2, routing, top_k_final=top_k
            )
            trace["retrieval_result"] = ret_res.model_dump(mode="json")
            ranked_primary, rejected_pf = filter_ranked_for_primary_phase(
                ranked_all,
                primary_domains=list(routing.primary_domains),
                include_shared=routing.include_shared,
            )
            ranked, _exp, _used_dom = merge_secondary_with_policy(
                ranked_primary,
                ranked_all,
                secondary_domains=list(routing.secondary_domains),
                policy=policy,
                triggered_bridges=list(routing.triggered_bridges),
            )
            trace["rejected_candidates_domain_filter"] = rejected_pf[:32]
            ri = ri_full
            merged_index = ri_full
        elif rulebase_registry is not None and domain_retriever is not None:
            ranked_all, merged_index = domain_retriever.retrieve(
                layer1,
                layer2,
                list(routing.primary_domains),
                include_shared=routing.include_shared,
                top_k=top_k,
            )
            ranked_primary, rejected_pf = filter_ranked_for_primary_phase(
                ranked_all,
                primary_domains=list(routing.primary_domains),
                include_shared=routing.include_shared,
            )
            ranked, _exp, _used_dom = merge_secondary_with_policy(
                ranked_primary,
                ranked_all,
                secondary_domains=list(routing.secondary_domains),
                policy=policy,
                triggered_bridges=list(routing.triggered_bridges),
            )
            trace["rejected_candidates_domain_filter"] = rejected_pf[:32]
            ri = merged_index
        else:
            ri = rule_index or get_rulebase_index()
            ranked_all = retrieve_rules(layer1=layer1, layer2=layer2, top_k=top_k, index=ri)
            ranked_all = enrich_ranked_with_retrieval_meta(ranked_all)
            ranked_primary, rejected_pf = filter_ranked_for_primary_phase(
                ranked_all,
                primary_domains=list(routing.primary_domains),
                include_shared=routing.include_shared,
            )
            ranked, _exp, _used_dom = merge_secondary_with_policy(
                ranked_primary,
                ranked_all,
                secondary_domains=list(routing.secondary_domains),
                policy=policy,
                triggered_bridges=list(routing.triggered_bridges),
            )
            trace["rejected_candidates_domain_filter"] = rejected_pf[:32]
            merged_index = ri
        session.retrieved_rules = [r for r, _, _ in ranked]
        sp_rr.output_summary = {
            "domain_routing": routing.model_dump(mode="json"),
            "top_rule_ids": [r.rule_id for r, _, _ in ranked[:8]],
            "top": [
                {
                    "rule_id": r.rule_id,
                    "score_total": s,
                    "matched_features": (d.get("matched_features") or [])[:12],
                    "score_components": d.get("score_components") or {},
                    "rulebase_id": d.get("rulebase_id"),
                    "domain": d.get("domain"),
                    "layer": d.get("layer"),
                    "source_doc": d.get("source_doc"),
                    "source_article": d.get("source_article"),
                    "retrieval_scope": d.get("retrieval_scope"),
                }
                for r, s, d in ranked[: min(8, len(ranked))]
            ],
        }
    trace["rule_retrieval"] = {
        "backend": "advanced_domain_per_scope" if retriever_advanced is not None else "hybrid_bm25_structured",
        "top": (sp_rr.output_summary or {}).get("top", []),
    }
    apply_retrieval_backend(
        trace["backend_modes"],
        backend=trace["rule_retrieval"].get("backend"),
        retrieved_count=len(ranked),
    )
    trace["retrieved_rules_by_domain"] = _group_retrieved_by_domain(ranked)

    ctx = ReasoningContext(
        primary_domains=list(routing.primary_domains),
        secondary_domains=list(routing.secondary_domains),
        active_rulebases=collect_rulebase_ids_from_index(merged_index.rules),
        include_shared=routing.include_shared,
        question_time=None,
        statute_ids=[],
        cross_domain_policy=policy,
        triggered_bridges=list(routing.triggered_bridges),
    )
    trace["reasoning_context"] = ctx.to_trace_dict()

    goal = layer2.goal

    selected: RuleRecord | None = None
    bstate: ReasoningState | None = None

    if not resolved_run_config.enable_backward_chaining:
        trace.setdefault("hard_gates_hit", []).append("backward_disabled_by_run_config")
        with tc.span("pipeline_exit") as spx:
            spx.output_summary = {"reason": "backward_disabled_by_run_config"}
        selected = ranked[0][0] if ranked else None
        bstate = ReasoningState(
            requirement_set=[],
            missing_facts=[],
            selected_rule_ids=[selected.rule_id] if selected else [],
            goal_status="failed",
            trace=["backward_disabled_non_blocking_continue"],
        )
    else:
        with tc.span("rule_backward_gate") as sp_b:
            pass
        rg = gate_rule_and_backward(
            engine,
            goal=goal,
            layer2=layer2,
            ranked=ranked,
            known_facts=known_facts_for_reasoning(session),
            rule_index=ri,
            max_rule_repair=max_repair_attempts_rule,
            max_backward_repair=max_repair_attempts_backward,
            reasoning_context=ctx,
            cross_domain_policy=policy,
            structured_facts=structured_facts_for_reasoning(session),
            question_mode=question_mode,
        )
        trace["rule_backward_gate"] = rg.trace
        if rg.v_rule:
            _merge_verification(session, rg.v_rule)
        if rg.v_back:
            _merge_verification(session, rg.v_back)
        sp_b.output_summary = {
            "gate_ok": rg.ok,
            "clarification_needed": rg.clarification_needed,
            "tried_rule_ids": rg.tried_rule_ids,
            "error": rg.error,
            "verify_rule": summarize_verification_trace(rg.v_rule) if rg.v_rule else {},
            "verify_backward": summarize_verification_trace(rg.v_back) if rg.v_back else {},
        }
        sp_b.decision = rg.v_back.final_decision if rg.v_back else "none"
        if not rg.ok:
            trace.setdefault("hard_gates_hit", []).append("rule_backward_gate_failure")
            with tc.span("pipeline_exit") as spx:
                spx.output_summary = {"reason": rg.error or "rule_backward_gate_failed_non_blocking_continue"}
            selected = rg.selected or (ranked[0][0] if ranked else None)
            bstate = rg.bstate or ReasoningState(
                requirement_set=[],
                missing_facts=[],
                selected_rule_ids=[selected.rule_id] if selected else [],
                goal_status="failed",
                trace=["rule_backward_gate_failed_non_blocking_continue"],
            )
        else:
            selected = rg.selected
            bstate = rg.bstate

    session.reasoning = bstate
    session.selected_rule = selected

    if rg.clarification_needed and bstate and question_mode not in {"rule_reading"}:
        trace.setdefault("hard_gates_hit", []).append("needs_clarification")
        with tc.span("clarification_non_blocking") as sp_cl:
            parse_ambs = (layer2.diagnostics or {}).get("ambiguities") or []
            parse_prompts = build_parse_ambiguity_prompts([a for a in parse_ambs if not a.get("blocking")])
            filtered_missing = filter_clarification_targets(
                bstate.missing_facts,
                known_facts=session.known_facts,
                parse_layer2=layer2,
            )
            backward_prompts = build_clarification_prompts_from_requirements(
                filtered_missing,
                bstate.requirement_set,
                backward_plan=bstate.backward_plan,
                related_rule_id=selected.rule_id if selected else None,
            )
            prompts = merge_clarification_prompts_unified(parse_prompts, backward_prompts)
            sp_cl.output_summary = {
                "prompt_count": len(prompts),
                "missing_facts": bstate.missing_facts,
                "non_blocking_continue": True,
                "clarification_enabled": bool(resolved_run_config.enable_clarification),
            }
        trace["clarification_gain"] = _clarification_gain_summary(
            pre_missing=pre_missing,
            post_missing=list(bstate.missing_facts or []),
            pre_status=pre_status,
            post_status="answered",
            pre_proof=pre_proof,
            post_proof=None,
        )
        session.missing_facts = bstate.missing_facts
        session.clarification_questions = prompts
        trace["clarification_non_blocking"] = {
            "prompt_count": len(prompts),
            "missing_facts": list(bstate.missing_facts or []),
            "clarification_enabled": bool(resolved_run_config.enable_clarification),
        }
        trace["stage"].append("clarification_non_blocking_continue")

    # If batch mode bypassed clarification, continue with conditional answer logic
    # Otherwise we have selected+bstate from backward
    if bstate is None:
        trace.setdefault("hard_gates_hit", []).append("no_reasoning_state")
        bstate = ReasoningState(
            requirement_set=[],
            missing_facts=[],
            selected_rule_ids=[selected.rule_id] if selected else [],
            goal_status="failed",
            trace=["missing_reasoning_state_non_blocking_continue"],
        )
        session.reasoning = bstate
    if selected is None:
        trace.setdefault("hard_gates_hit", []).append("no_selected_rule")
        selected = RuleRecord(
            rule_id="RULE_FALLBACK_UNKNOWN",
            logic_form="fallback_rule",
            head={"predicate": "unknown", "args": []},
            body=[],
            metadata={"fallback": True, "reason": "no_selected_rule_non_blocking_continue"},
        )
        session.selected_rule = selected

    selected_semantic_ctx = dict((rg.candidate_verdicts or {}).get(str(selected.rule_id), {}) or {}) if rg else {}

    with tc.span("forward_gate") as sp_f:
        fg = gate_forward_reasoning(
            engine,
            goal=goal,
            selected=selected,
            ranked=ranked,
            session=session,
            known_facts=known_facts_for_reasoning(session),
            backward_plan_dict=bstate.backward_plan,
            backward_state=bstate,
            max_forward_repair=max_repair_attempts_forward,
            reasoning_context=ctx,
            cross_domain_policy=policy,
            semantic_match_context={
                "semantic_family_match_tier": selected_semantic_ctx.get("semantic_family_match_tier"),
                "semantic_soft_match_triggered": selected_semantic_ctx.get("semantic_family_soft_match_triggered"),
                "semantic_soft_match_reason": selected_semantic_ctx.get("semantic_family_soft_match_reason"),
            },
            question_mode=question_mode,
        )
        trace["forward_gate"] = fg.trace
        if fg.v_fwd:
            _merge_verification(session, fg.v_fwd)
        sp_f.output_summary = {
            "gate_ok": fg.ok,
            "verify_forward": summarize_verification_trace(fg.v_fwd) if fg.v_fwd else {},
            "error": fg.error,
        }
        sp_f.decision = fg.v_fwd.final_decision if fg.v_fwd else "none"

    if not fg.ok:
        trace.setdefault("hard_gates_hit", []).append("forward_gate_failure")
        with tc.span("pipeline_exit") as spx:
            spx.output_summary = {"reason": fg.error or "forward_verification_failed_non_blocking_continue"}

    conclusion = fg.conclusion or (proof := fg.proof_obj) and (proof.conclusion or proof.derived_conclusion) or "Kết luận chưa đủ điều kiện xác minh đầy đủ."
    goal_ok = bool(fg.goal_achieved)
    fstate = fg.fstate or bstate
    proof = fg.proof_obj
    if proof is None:
        trace.setdefault("hard_gates_hit", []).append("no_proof")
        proof = ProofObject(
            proof_id=f"proof_fallback_{session.session_id}",
            selected_rule=selected.rule_id if selected else None,
            conclusion=conclusion,
            derived_conclusion=conclusion,
            fail_stage="forward_gate",
        )
        trace["no_proof_non_blocking_fallback"] = True
    session.reasoning = fstate
    session.proof = proof
    if fstate and fstate.forward_result and fstate.forward_result.get("rule_id"):
        forward_rule_id = str(fstate.forward_result.get("rule_id") or "")
        selected_rule_id = str(selected.rule_id) if selected else ""
        if selected_rule_id and forward_rule_id and forward_rule_id != selected_rule_id:
            logger.warning(
                "forward_rule_mismatch_with_selected_rule session_id=%s selected_rule_id=%s forward_rule_id=%s",
                session.session_id,
                selected_rule_id,
                forward_rule_id,
            )
            trace["forward_rule_mismatch_with_selected_rule"] = {
                "selected_rule_id": selected_rule_id,
                "forward_rule_id": forward_rule_id,
                "overwrite_blocked": True,
            }
            trace["forward_low_confidence_due_to_rule_mismatch"] = True
    session.selected_rule = selected

    with tc.span("proof") as sp_p:
        sp_p.output_summary = {
            "proof_id": proof.proof_id,
            "step_count": len(proof.proof_steps or []),
        }
    trace["proof_steps_by_domain"] = _proof_steps_by_domain(proof)

    with tc.span("retrieve_evidence") as sp_ev:
        ev = (evidence_retriever or get_evidence_retriever()).retrieve(
            question=question,
            rule=selected,
            conclusion=conclusion,
            top_k=5,
            proof_summary=_proof_summary_for_evidence(proof),
            goal=goal,
            modality_text=layer1.modality_text or "",
            layer1=layer1,
            layer2=layer2,
        )
        evidence_bundle = build_evidence_bundle(
            query=question,
            selected_rule=selected,
            requirement_set=list(bstate.requirement_set or []),
            proof=proof,
            snippets=ev,
        )
        trace["evidence_stage"] = {
            "bundle_id": evidence_bundle.bundle_id,
            "selected_rule_id": evidence_bundle.selected_rule_id,
            "linkage_map": evidence_bundle.linkage_map,
            "items": [x.model_dump(mode="json") for x in evidence_bundle.items],
        }
        sp_ev.output_summary = summarize_evidence_trace(ev)
    trace["final_grounding_docs"] = _grounding_docs_from_evidence(ev)

    with tc.span("generate_answer") as sp_ga:
        ans = generate_answer(
            question=question,
            conclusion=conclusion,
            proof=proof,
            evidence=ev,
            evidence_bundle=evidence_bundle,
            goal_achieved=goal_ok,
            rule=selected,
            missing_facts=bstate.missing_facts if bstate else None,
        )
        apply_answer_backend(trace["backend_modes"], ans)
        sp_ga.output_summary = summarize_answer_trace(ans)

    # Apply conditional answer BEFORE repair so verifier validates the final form (policy A+B)
    missing_facts_now, has_missing_signal = _collect_application_policy_missing_facts(
        bstate=bstate,
        fstate=fstate,
    )
    ans, _ = _apply_application_answer_policy(
        ans=ans,
        trace=trace,
        session=session,
        question_mode=question_mode,
        selected_rule=selected,
        known_fact_keys=list(known_facts_for_reasoning(session).keys()),
        missing_facts=missing_facts_now,
        has_missing_signal=has_missing_signal,
        mode_tag="clarify_missing_facts_conditional",
    )

    with tc.span("answer_repair") as sp_ar:
        ans_text, v_ans, answer_repair_trace = run_answer_repair_loop(
            engine,
            answer_text=ans.answer_text,
            conclusion=conclusion,
            proof=proof.model_dump(mode="json"),
            evidence_bundle=evidence_bundle.model_dump(mode="json"),
            modality_expected=layer1.modality_text or "",
            goal_action=str(goal.get("args", ["", "", ""])[1] if len(goal.get("args", [])) > 1 else ""),
            action_token_in_answer=ans.answer_text,
            question_mode=question_mode,
            missing_facts=missing_facts_now,
            max_repair_attempts_answer=max_repair_attempts_answer,
        )
        apply_answer_text_and_refresh_citations(ans, ans_text)
        ans.verification_summary += f";answer_repair_attempts={answer_repair_trace[-1].get('attempts_used', 0)}"
        trace["answer_repair"] = answer_repair_trace
        _merge_verification(session, v_ans)
        sp_ar.output_summary = {
            "verify_answer": summarize_verification_trace(v_ans),
            "attempts_used": answer_repair_trace[-1].get("attempts_used", 0) if answer_repair_trace else 0,
        }
        sp_ar.decision = v_ans.final_decision

    if v_ans.final_decision == "REJECT" and answer_reject_allow_fallback:
        if _should_use_honest_degraded_answer(
            selected=selected,
            goal=goal,
            proof=proof,
            failure_reason="answer_verification_reject",
        ):
            reg = generate_honest_degraded_answer(
                question=question,
                reason="answer_verification_reject",
                selected_rule=selected,
                goal=goal,
                retrieved_rules=[r for r, _s, _d in ranked[:3]],
            )
            reg.verification_summary = ans.verification_summary + ";answer_fallback_honest_degraded"
        else:
            reg = safe_regenerate_final_answer(
                conclusion,
                proof=proof,
                evidence=ev,
                rule=selected,
                goal_achieved=goal_ok,
            )
            reg.verification_summary = ans.verification_summary + ";answer_fallback_regenerate_on_reject"
        ans = reg
    elif v_ans.final_decision == "REJECT":
        trace.setdefault("hard_gates_hit", []).append("answer_verification_reject_no_fallback")
        ans.verification_summary += ";answer_verification_rejected_no_fallback"
        trace["answer_verification"] = {"final_decision": "REJECT", "note": "no_fallback_per_policy"}

    ans = _apply_parse_uncertainty_answer_policy(
        ans=ans,
        layer2=layer2,
        trace=trace,
        context_tag="clarify.final_answer",
    )

    ans = _apply_user_facing_forward_failure_policy(
        ans,
        selected_rule=selected,
        forward_failed=bool(not fg.ok),
        trace=trace,
        layer1=layer1,
    )

    ans = _enforce_reasoning_failure_answer_policy(
        ans,
        question=question,
        layer2=layer2,
        selected=selected,
        goal=goal,
        ranked=ranked,
        evidence=ev,
        phase3_result=None,
        forward_failed=bool(not fg.ok),
        answer_rejected=bool(v_ans.final_decision == "REJECT"),
        trace=trace,
    )

    trace["flow_trace"] = _build_missing_facts_stage_trace(
        question_mode=question_mode,
        bstate=bstate,
        fstate=fstate,
        fg_ok=bool(fg.ok),
        v_ans_decision=str(v_ans.final_decision),
    )

    session.answer = ans
    trace["clarification_gain"] = _clarification_gain_summary(
        pre_missing=pre_missing,
        post_missing=list((fstate.missing_facts if fstate else []) or []),
        pre_status=pre_status,
        post_status="resolved_after_clarification",
        pre_proof=pre_proof,
        post_proof=proof,
    )
    session.pipeline_trace = trace
    _merge_pipeline_trace_dict(trace, tc)
    svc.save(session)

    return ClarifyResponse(
        session_id=session.session_id,
        needs_clarification=False,
        layer1=layer1,
        layer2=layer2,
        verification_trace=session.verification_logs,
        retrieved_rules=[_rule_dump(r) for r, s, d in ranked[:8]],
        selected_rule=_rule_dump(selected),
        reasoning=fstate,
        proof=proof,
        evidence_bundle=evidence_bundle,
        answer=ans,
        debug_trace=trace,
    )
