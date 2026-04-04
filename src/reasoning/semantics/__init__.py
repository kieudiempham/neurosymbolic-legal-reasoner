"""Semantic reasoning layer: internal schema as source of truth."""

from reasoning.semantics.backward_plan import build_backward_plan, pick_best_rule_record
from reasoning.semantics.boundary_facts import atom_truth_status, known_atoms_from_facts
from reasoning.semantics.constraint_eval import (
    evaluate_constraint,
    evaluate_deadline_constraint,
    evaluate_dossier_constraint,
    evaluate_threshold_constraint,
    evaluate_threshold_note_constraint,
)
from reasoning.semantics.forward_engine import (
    forward_agenda_fixed_point,
    run_forward_best_path,
    run_forward_path,
)
from reasoning.semantics.failed_path_hints import (
    build_user_message_hint,
    clarification_priority_for_failure,
    failed_path_record_from_result,
)
from reasoning.semantics.numeric_lookup import (
    NumericLookupResult,
    resolve_numeric_value_for_threshold,
)
from reasoning.semantics.plan_models import (
    BackwardCandidate,
    BackwardPlan,
    ClarificationRequest,
    FailedPathRecord,
    ForwardPathResult,
    MissingAtom,
    MissingConstraintInput,
    MissingExceptionInput,
)
from reasoning.semantics.proof_validate import validate_proof_chain, validate_proof_step
from reasoning.semantics.unification import (
    Substitution,
    apply_substitution_to_atom,
    apply_substitution_to_reasoning_rule,
    is_variable,
    unify_atoms,
    unify_goal_dict_with_goal_atom,
)

__all__ = [
    "BackwardCandidate",
    "BackwardPlan",
    "ClarificationRequest",
    "FailedPathRecord",
    "ForwardPathResult",
    "NumericLookupResult",
    "build_user_message_hint",
    "clarification_priority_for_failure",
    "failed_path_record_from_result",
    "resolve_numeric_value_for_threshold",
    "MissingAtom",
    "MissingConstraintInput",
    "MissingExceptionInput",
    "Substitution",
    "apply_substitution_to_atom",
    "apply_substitution_to_reasoning_rule",
    "atom_truth_status",
    "build_backward_plan",
    "evaluate_constraint",
    "evaluate_deadline_constraint",
    "evaluate_dossier_constraint",
    "evaluate_threshold_constraint",
    "evaluate_threshold_note_constraint",
    "forward_agenda_fixed_point",
    "is_variable",
    "known_atoms_from_facts",
    "pick_best_rule_record",
    "run_forward_best_path",
    "run_forward_path",
    "unify_atoms",
    "unify_goal_dict_with_goal_atom",
    "validate_proof_chain",
    "validate_proof_step",
]
