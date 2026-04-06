"""Post-retrieval phase 3: temporal filter, conflict prune, bridge facts, collision warnings."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from pydantic import BaseModel

from rulebase.rule_identity import global_rule_key, warn_on_rule_id_collision
from rulebase.rulebase_registry import RulebaseRegistry
from rulebase.bridge_inference import (
    BridgeEmittedFact,
    apply_bridge_facts_to_session,
    run_bridge_inference,
)
from runtime.conflict_resolution_policy import prune_conflicting_candidates
from runtime.temporal_policy import (
    filter_ranked_by_temporal,
    resolve_question_time,
    temporal_snapshot_for_proof,
)
from schemas.domain_routing import DomainRoutingPlan
from schemas.rule import RuleRecord
from schemas.session import SessionState


class Phase3PostRetrieveResult(BaseModel):
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]]
    question_time_iso: str
    temporal_rejected: list[dict[str, Any]]
    conflict_rejected: list[dict[str, Any]]
    bridge_emitted: list[BridgeEmittedFact]
    bridge_diag: list[dict[str, Any]]
    rule_id_collision_warnings: list[dict[str, Any]]
    proof_phase3_context: dict[str, Any]


def _collect_rule_id_collisions(
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
) -> list[dict[str, Any]]:
    by_rid: dict[str, list[RuleRecord]] = defaultdict(list)
    for r, _, _ in ranked:
        by_rid[r.rule_id].append(r)
    out: list[dict[str, Any]] = []
    for rid, rules in by_rid.items():
        if len(rules) < 2:
            continue
        keys = [global_rule_key(x) for x in rules]
        if len(set(keys)) <= 1:
            continue
        for i in range(len(rules)):
            for j in range(i + 1, len(rules)):
                warn_on_rule_id_collision(rules[i], rules[j])
        out.append({"rule_id": rid, "global_keys": list(dict.fromkeys(keys))})
    return out


def apply_phase3_post_retrieve(
    *,
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    session: SessionState,
    question: str,
    routing: DomainRoutingPlan,
    rulebase_registry: RulebaseRegistry | None,
    question_time_explicit: str | None,
    trace: dict[str, Any],
) -> Phase3PostRetrieveResult:
    qt = resolve_question_time(question_time_explicit, trace=trace)
    qt_iso = qt.isoformat()
    trace["resolved_question_time_utc"] = qt_iso

    ranked_t, temporal_rejected = filter_ranked_by_temporal(ranked, qt)
    ranked_c, conflict_rejected = prune_conflicting_candidates(ranked_t)
    collision_warnings = _collect_rule_id_collisions(ranked_c)

    emitted, bridge_diag = run_bridge_inference(
        session,
        question,
        triggered_bridge_ids=list(routing.triggered_bridges),
        registry=rulebase_registry,
    )
    apply_bridge_facts_to_session(session, emitted)

    proof_ctx: dict[str, Any] = {
        "temporal": temporal_snapshot_for_proof(qt),
        "bridge_facts": [e.model_dump(mode="json") for e in emitted],
        "temporal_rejected_count": len(temporal_rejected),
        "conflict_rejected_count": len(conflict_rejected),
        "rule_id_collision_warnings": collision_warnings,
    }

    return Phase3PostRetrieveResult(
        ranked=ranked_c,
        question_time_iso=qt_iso,
        temporal_rejected=temporal_rejected,
        conflict_rejected=conflict_rejected,
        bridge_emitted=emitted,
        bridge_diag=bridge_diag,
        rule_id_collision_warnings=collision_warnings,
        proof_phase3_context=proof_ctx,
    )
