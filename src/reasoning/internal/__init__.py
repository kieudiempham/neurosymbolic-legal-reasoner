"""Internal reasoning layer on top of `RuleRecord` (no change to raw rulebase JSON)."""

from reasoning.internal.codec import (
    atom_from_dict,
    atoms_equal,
    canonicalize_atom,
    deserialize_atom,
    goal_dict_to_tuple,
    serialize_atom,
    tuple_to_goal_dict,
)
from reasoning.internal.mapper import map_rule_record_to_reasoning_rule
from reasoning.internal.models import (
    Atom,
    AuxiliaryRecord,
    DeadlineConstraint,
    DossierConstraint,
    ReasoningRule,
    ThresholdConstraint,
    ThresholdNoteConstraint,
)

__all__ = [
    "Atom",
    "AuxiliaryRecord",
    "DeadlineConstraint",
    "DossierConstraint",
    "ReasoningRule",
    "ThresholdConstraint",
    "ThresholdNoteConstraint",
    "map_rule_record_to_reasoning_rule",
    "canonicalize_atom",
    "serialize_atom",
    "deserialize_atom",
    "atoms_equal",
    "atom_from_dict",
    "goal_dict_to_tuple",
    "tuple_to_goal_dict",
]
