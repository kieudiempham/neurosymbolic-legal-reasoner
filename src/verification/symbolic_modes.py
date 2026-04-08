"""Per-mode symbolic validation — structured checks (pass/fail/skip + field + message)."""

from __future__ import annotations

from typing import Any

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord
from verification.symbolic_check_types import SymbolicCheckResult
from verification.symbolic_validator import check_parse_consistency, goal_matches_rule_head

_VALID_GOAL_PREDS = frozenset(
    {
        "obligation",
        "permission",
        "prohibition",
        "deadline",
        "threshold",
        "unknown",
        "applies_if",
        "dossier",
        "must",
    }
)

_FOCUS_TO_PRED = {
    "obligation": "obligation",
    "permission": "permission",
    "prohibition": "prohibition",
    "deadline": "deadline",
    "threshold": "threshold",
    "exception": "exception",
    "applicability": "applies_if",
    "dossier": "dossier",
    "legal_effect": "unknown",
    "authority": "unknown",
    "procedure": "obligation",
    "legal_consequence": "obligation",
    "unknown": "unknown",
}


def _dedupe_codes(codes: list[str]) -> list[str]:
    return list(dict.fromkeys(codes))


def symbolic_parse(question_text: str, layer1: Layer1Parse, layer2: Layer2Parse) -> SymbolicCheckResult:
    r = SymbolicCheckResult(ok=True)
    sym_ok, parse_issues = check_parse_consistency(layer1, layer2)
    for issue in parse_issues:
        r.add("layer1_layer2_consistency", "fail", issue, "layer1/layer2", code="layer1_layer2_misalignment")

    qt = (question_text or "").strip()
    if len(qt) < 4:
        r.add("question_text_length", "fail", "question_text quá ngắn", "question_text", code="parse_slot_error")
    else:
        r.add("question_text_length", "pass", "", "question_text")

    subj_ok = bool((layer1.subject_text or "").strip() or (layer2.subject_normalized or "").strip())
    if not subj_ok:
        r.add("subject_presence", "fail", "Thiếu subject ở layer1/layer2", "subject", code="parse_slot_error")
    else:
        r.add("subject_presence", "pass", "", "subject")

    act_ok = bool((layer1.action_text or "").strip())
    if not act_ok and layer1.question_focus not in ("unknown", "exception"):
        r.add("action_presence", "fail", "Thiếu action_text khi focus không phải unknown", "action_text", code="parse_slot_error")
    else:
        r.add("action_presence", "pass" if act_ok or layer1.question_focus == "unknown" else "skip", "", "action_text")

    mod_ok = bool((layer1.modality_text or "").strip())
    if mod_ok:
        r.add("modality_presence", "pass", "", "modality_text")
    else:
        r.add("modality_presence", "skip", "Không có modality_text (có thể chấp nhận)", "modality_text")

    g = layer2.goal or {}
    gpred = str(g.get("predicate") or "unknown")
    if gpred not in _VALID_GOAL_PREDS and gpred != "unknown":
        r.add("goal_predicate_schema", "fail", f"predicate không hợp lệ: {gpred}", "layer2.goal", code="goal_construction_error")
    else:
        r.add("goal_predicate_schema", "pass", "", "layer2.goal.predicate")

    args = g.get("args") or []
    if gpred != "unknown" and len(args) < 1:
        r.add("goal_arity", "fail", "goal thiếu args tối thiểu", "layer2.goal.args", code="goal_construction_error")
    else:
        r.add("goal_arity", "pass" if gpred == "unknown" or len(args) >= 1 else "fail", "", "layer2.goal.args")

    focus = layer1.question_focus
    if focus != "unknown" and gpred == "unknown":
        r.add("focus_vs_goal", "fail", "layer1 có focus nhưng goal predicate unknown", "layer2.goal", code="goal_construction_error")
    elif focus != "unknown" and gpred != "unknown":
        exp = _FOCUS_TO_PRED.get(focus, "unknown")
        if exp not in ("unknown",) and gpred != exp and not (
            focus == "applicability" and gpred in ("obligation", "permission")
        ):
            r.add(
                "focus_goal_alignment",
                "fail",
                f"focus={focus} vs goal.predicate={gpred}",
                "layer1.question_focus",
                code="layer1_layer2_misalignment",
            )
        else:
            r.add("focus_goal_alignment", "pass", "", "layer1.question_focus")

    if layer2.facts and not isinstance(layer2.facts, list):
        r.add("facts_shape", "fail", "facts phải là list", "layer2.facts", code="fact_extraction_error")
    else:
        r.add("facts_shape", "pass", "", "layer2.facts")

    for i, atom in enumerate(layer2.condition_atoms or []):
        if not isinstance(atom, str) or "(" not in atom:
            r.add(
                f"condition_atom_{i}",
                "fail",
                "condition atom không đúng dạng chuỗi predicate(args)",
                f"layer2.condition_atoms[{i}]",
                code="fact_extraction_error",
            )
        else:
            r.add(f"condition_atom_{i}", "pass", "", f"layer2.condition_atoms[{i}]")

    if layer1.assertion_status == "hypothetical" and "không" not in qt.lower() and "neu" not in qt.lower():
        r.add("assertion_marker", "skip", "hypothetical nhưng câu hỏi không có dấu hiệu giả định rõ", "layer1.assertion_status")

    if not sym_ok:
        r.add("parse_consistency_legacy", "fail", "check_parse_consistency failed", "layer1/layer2", code="layer1_layer2_misalignment")

    failed = [c for c in r.checks if c.get("status") == "fail"]
    r.ok = len(failed) == 0
    r.error_codes = _dedupe_codes(r.error_codes)
    return r


def symbolic_rule(
    layer2_goal: dict[str, Any],
    rule_candidate: RuleRecord | None,
    *,
    _legal_frame: str | None = None,
) -> SymbolicCheckResult:
    r = SymbolicCheckResult(ok=True)
    if rule_candidate is None:
        r.add("rule_presence", "fail", "Không có rule", "rule_candidate", code="rule_extraction_error")
        r.ok = False
        r.error_codes = _dedupe_codes(r.error_codes)
        return r

    r.add("rule_presence", "pass", "", "rule_candidate.rule_id")

    ok, head_issues = goal_matches_rule_head(layer2_goal, rule_candidate)
    for hi in head_issues:
        r.add("head_vs_goal", "fail", hi, "rule.head", code="rule_schema_error")
    if ok:
        r.add("head_vs_goal", "pass", "", "rule.head")

    lf = rule_candidate.logic_form or ""
    hp = rule_candidate.head.predicate if rule_candidate.head else ""
    if not lf:
        r.add("logic_form_present", "fail", "Thiếu logic_form", "rule.logic_form", code="rule_schema_error")
    else:
        r.add("logic_form_present", "pass", "", "rule.logic_form")

    if lf and hp and lf not in hp and hp not in lf:
        r.add("head_logic_form_modality", "skip", "head vs logic_form khác namespace (có thể ok)", "rule")

    body_preds = [c.get("predicate") for c in (rule_candidate.body or []) if isinstance(c, dict)]
    if "exception_applies" in body_preds:
        r.add("body_exception", "pass", "Có exception_applies trong body", "rule.body")
    if lf == "threshold" and not any(x in ("threshold",) for x in [hp] + body_preds):
        r.add("threshold_structure", "fail", "logic_form threshold nhưng head/body không phản ánh", "rule", code="rule_threshold_error")
    else:
        r.add("threshold_structure", "pass" if lf != "threshold" else "pass", "", "rule")

    if lf == "deadline":
        has_deadline = "deadline" in body_preds or (rule_candidate.head.args and len(rule_candidate.head.args or []) >= 2)
        if not has_deadline:
            r.add("deadline_structure", "fail", "logic_form deadline thiếu thành phần deadline rõ", "rule", code="rule_deadline_error")
        else:
            r.add("deadline_structure", "pass", "", "rule")

    failed = [c for c in r.checks if c.get("status") == "fail"]
    r.ok = len(failed) == 0
    r.error_codes = _dedupe_codes(r.error_codes)
    return r


def symbolic_backward(
    goal: dict[str, Any],
    selected_rule_id: str | None,
    backward_plan: dict[str, Any] | None,
    *,
    requirements_ok: bool,
    missing_facts: list[str] | None,
    requirement_keys: list[str] | None = None,
    requirement_artifact: dict[str, Any] | None = None,
) -> SymbolicCheckResult:
    r = SymbolicCheckResult(ok=True)
    if not selected_rule_id:
        r.add("selected_rule", "fail", "Không có rule được chọn", "selected_rule_id", code="backward_rule_selection_error")
        r.ok = False
        r.error_codes = _dedupe_codes(r.error_codes)
        return r

    cands = (backward_plan or {}).get("candidates") or []
    ids = [c.get("rule_id") for c in cands if isinstance(c, dict)]
    if ids and selected_rule_id not in ids:
        r.add("plan_membership", "fail", "selected không nằm trong candidates", "backward_plan", code="backward_unification_error")
    else:
        r.add("plan_membership", "pass", "", "backward_plan.candidates")

    for c in cands:
        if isinstance(c, dict) and c.get("rule_id") == selected_rule_id and c.get("unification_failure"):
            r.add("unification", "fail", "candidate chọn có unification_failure", "backward_plan", code="backward_unification_error")

    rk = set(requirement_keys or [])
    mk = set(missing_facts or [])
    if rk and mk and not mk.issubset(rk):
        r.add("missing_subset", "fail", "missing_facts có khóa ngoài requirement_set", "missing_facts", code="requirement_construction_error")
    else:
        r.add("missing_subset", "pass", "", "missing_facts")

    if not requirements_ok and not mk and selected_rule_id:
        r.add(
            "requirements_path",
            "skip",
            "requirements_ok=false và không có missing_facts (kiểm tra heuristic)",
            "backward",
        )
    else:
        r.add("requirements_path", "pass", "", "can_continue_forward")

    art = requirement_artifact or {}
    if art:
        art_rule_id = str(art.get("rule_id") or "")
        if art_rule_id and art_rule_id != selected_rule_id:
            r.add(
                "artifact_rule_alignment",
                "fail",
                "requirement artifact rule_id lệch selected_rule_id",
                "requirement_artifact.rule_id",
                code="requirement_construction_error",
            )
        else:
            r.add("artifact_rule_alignment", "pass", "", "requirement_artifact.rule_id")

        mk_art = set((art.get("unmet_required") or []) + (art.get("unmet_optional") or []))
        if mk and mk_art and mk != mk_art:
            r.add(
                "missing_vs_artifact",
                "fail",
                "missing_facts không khớp unmet_* trong requirement artifact",
                "requirement_artifact",
                code="requirement_construction_error",
            )
        else:
            r.add("missing_vs_artifact", "pass", "", "requirement_artifact.unmet_*")

    gpred = str(goal.get("predicate") or "")
    cand0 = cands[0] if cands else {}
    if isinstance(cand0, dict) and cand0.get("goal_atom"):
        ga = cand0["goal_atom"]
        if isinstance(ga, list) and len(ga) > 0 and str(ga[0]) != gpred:
            r.add("goal_vs_plan_atom", "fail", "goal predicate khác goal_atom đầu trong plan", "goal", code="backward_unification_error")
        else:
            r.add("goal_vs_plan_atom", "pass", "", "goal")

    failed = [c for c in r.checks if c.get("status") == "fail"]
    r.ok = len(failed) == 0
    r.error_codes = _dedupe_codes(r.error_codes)
    return r


def symbolic_forward(
    *,
    goal_achieved: bool,
    forward_result: dict[str, Any] | None,
    proof: dict[str, Any] | None,
    conclusion: str,
    goal: dict[str, Any] | None = None,
    requirement_artifact: dict[str, Any] | None = None,
    selected_rule_id: str | None = None,
) -> SymbolicCheckResult:
    r = SymbolicCheckResult(ok=True)
    fr = forward_result or {}
    gr = bool(fr.get("goal_reached"))
    if goal_achieved != gr:
        r.add("flag_consistency", "fail", "goal_achieved không khớp forward_result.goal_reached", "forward", code="forward_conclusion_error")
    else:
        r.add("flag_consistency", "pass", "", "forward_result")

    if goal_achieved:
        steps = (proof or {}).get("proof_steps") or []
        if not steps:
            r.add("proof_steps", "fail", "Thành công nhưng không có proof_steps", "proof", code="forward_proof_error")
        else:
            r.add("proof_steps", "pass", f"{len(steps)} bước", "proof.proof_steps")
            for i, st in enumerate(steps[:8]):
                desc = (st or {}).get("description") if isinstance(st, dict) else ""
                if isinstance(st, dict) and not (desc or "").strip():
                    r.add(f"proof_step_{i}_description", "fail", "Bước chứng minh thiếu mô tả", f"proof_steps[{i}]", code="forward_proof_error")

    fr_reason = str(fr.get("failure_reason") or "none")
    if fr_reason not in ("none", "") and goal_achieved:
        r.add("failure_vs_success", "fail", "Có failure_reason nhưng goal_achieved", "forward_result", code="forward_conclusion_error")
    else:
        r.add("failure_vs_success", "pass", "", "forward_result.failure_reason")

    if fr_reason in ("constraint_failed", "constraint_missing_input", "constraint_unknown"):
        if goal_achieved:
            r.add("constraint_trace", "fail", fr_reason + " nhưng goal_achieved", "forward", code="forward_constraint_error")
        else:
            r.add("constraint_trace", "pass", fr_reason, "forward_result.failure_reason")
    if fr_reason in ("exception_triggered",):
        if goal_achieved:
            r.add("exception_trace", "fail", fr_reason + " nhưng goal_achieved", "forward", code="forward_exception_error")
        else:
            r.add("exception_trace", "pass", fr_reason, "forward_result.failure_reason")
    if fr_reason == "negative_condition_blocked":
        if goal_achieved:
            r.add("negative_trace", "fail", fr_reason + " nhưng goal_achieved", "forward", code="forward_exception_error")
        else:
            r.add("negative_trace", "pass", fr_reason, "forward_result.failure_reason")

    if goal_achieved and not (conclusion or "").strip():
        r.add("conclusion_nonempty", "fail", "Rỗng conclusion khi thành công", "conclusion", code="forward_conclusion_error")
    else:
        r.add("conclusion_nonempty", "pass", "", "conclusion")

    art = requirement_artifact or {}
    if art:
        proof_steps = (proof or {}).get("proof_steps") or []
        rule_ids = {
            str(st.get("rule_id") or "")
            for st in proof_steps
            if isinstance(st, dict)
        }
        if selected_rule_id and rule_ids and selected_rule_id not in rule_ids:
            r.add(
                "proof_rule_alignment",
                "fail",
                "proof_steps không chứa selected_rule_id",
                "proof.proof_steps",
                code="forward_proof_error",
            )
        else:
            r.add("proof_rule_alignment", "pass", "", "proof.proof_steps")

        required_preds = {str(x) for x in (art.get("required_predicates") or []) if str(x)}
        supported_preds = {
            str(a.get("predicate") or "")
            for st in proof_steps
            if isinstance(st, dict)
            for a in (st.get("supporting_atoms") or [])
            if isinstance(a, dict)
        }
        if required_preds and not (required_preds & supported_preds):
            r.add(
                "requirement_proof_skeleton",
                "fail",
                "required_predicates không xuất hiện trong proof supporting_atoms",
                "requirement_artifact.required_predicates",
                code="forward_proof_error",
            )
        else:
            r.add("requirement_proof_skeleton", "pass", "", "proof.proof_steps.supporting_atoms")

    if goal and goal_achieved:
        gp = str(goal.get("predicate") or "")
        if gp and gp not in conclusion.lower():
            r.add("conclusion_goal_predicate", "skip", "conclusion không chứa predicate goal (heuristic)", "conclusion")

    failed = [c for c in r.checks if c.get("status") == "fail"]
    r.ok = len(failed) == 0
    r.error_codes = _dedupe_codes(r.error_codes)
    return r


def symbolic_answer_checks(
    *,
    symbolic_ok: bool,
    diag_from_validator: list[str],
    answer_text: str = "",
    conclusion: str = "",
    proof: dict[str, Any] | None = None,
) -> SymbolicCheckResult:
    r = SymbolicCheckResult(ok=symbolic_ok, issues=list(diag_from_validator))
    for d in diag_from_validator:
        if "action" in d:
            r.add("action_vs_goal", "fail", d, "answer", code="answer_subject_action_mismatch")
        if "modality" in d:
            r.add("modality_vs_expected", "fail", d, "answer", code="answer_time_quantity_mismatch")

    if conclusion and conclusion.strip() and conclusion.strip() not in answer_text and answer_text:
        r.add("answer_entails_conclusion", "fail", "answer không nhắc kết luận chính", "answer_text", code="answer_semantic_drift")
    elif conclusion:
        r.add("answer_entails_conclusion", "pass", "", "answer_text")

    ps = (proof or {}).get("proof_steps") or []
    if len(ps) > 3 and len(answer_text) < 40:
        r.add("answer_vs_proof_depth", "fail", "answer quá ngắn so với proof phức tạp", "answer_text", code="answer_overclaim")

    if not symbolic_ok and not r.error_codes:
        r.add("answer_generic", "fail", "symbolic check_answer_vs_goal failed", "answer", code="answer_semantic_drift")

    failed = [c for c in r.checks if c.get("status") == "fail"]
    r.ok = len(failed) == 0
    if not symbolic_ok:
        for d in diag_from_validator:
            if "action" in d:
                r.error_codes.append("answer_subject_action_mismatch")
            if "modality" in d:
                r.error_codes.append("answer_time_quantity_mismatch")
        if not r.error_codes:
            r.error_codes.append("answer_semantic_drift")
    r.error_codes = _dedupe_codes(r.error_codes)
    return r
