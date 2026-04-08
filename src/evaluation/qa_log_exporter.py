"""Export QA evaluation log artifacts to JSONL/CSV for batch analysis."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from schemas.evaluation_log import (
    QA_EVAL_LOG_FIELDS,
    QAEvaluationLogArtifact,
    flatten_evaluation_log_for_csv,
)


def _normalize_record(item: dict[str, Any] | QAEvaluationLogArtifact) -> QAEvaluationLogArtifact:
    if isinstance(item, QAEvaluationLogArtifact):
        return item
    if "evaluation_log" in item and isinstance(item.get("evaluation_log"), dict):
        return QAEvaluationLogArtifact.model_validate(item["evaluation_log"])
    return QAEvaluationLogArtifact.model_validate(item)


def load_jsonl_records(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    rows: list[dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for ln in f:
            s = ln.strip()
            if not s:
                continue
            rows.append(json.loads(s))
    return rows


def export_logs_jsonl(
    records: Iterable[dict[str, Any] | QAEvaluationLogArtifact],
    output_path: str | Path,
) -> int:
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with p.open("w", encoding="utf-8") as f:
        for item in records:
            log = _normalize_record(item)
            f.write(json.dumps(log.model_dump(mode="json"), ensure_ascii=False) + "\n")
            n += 1
    return n


def export_logs_csv(
    records: Iterable[dict[str, Any] | QAEvaluationLogArtifact],
    output_path: str | Path,
) -> int:
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=QA_EVAL_LOG_FIELDS)
        writer.writeheader()
        for item in records:
            log = _normalize_record(item)
            writer.writerow(flatten_evaluation_log_for_csv(log))
            n += 1
    return n


def summarize_cross_domain_metrics(
    records: Iterable[dict[str, Any] | QAEvaluationLogArtifact],
) -> dict[str, Any]:
    """Build batch-ready summary metrics for shared-layer / cross-domain contribution analysis."""
    total = 0
    with_activated_domains = 0
    with_bridge_rules = 0
    with_shared_layer_signal = 0
    jump_attempted_sum = 0
    jump_success_sum = 0
    jump_blocked_sum = 0
    proof_with_domains = 0
    final_statute_grounded = 0

    domain_counter: dict[str, int] = {}
    proof_domain_counter: dict[str, int] = {}
    bridge_counter: dict[str, int] = {}
    domain_pair_counter: dict[str, int] = {}
    domain_pair_bridge_counter: dict[str, int] = {}

    for item in records:
        log = _normalize_record(item)
        total += 1

        activated = list(log.activated_domains or [])
        if activated:
            with_activated_domains += 1
            if "shared" in {d.strip().lower() for d in activated}:
                with_shared_layer_signal += 1
            for d in activated:
                dd = str(d).strip()
                if not dd:
                    continue
                domain_counter[dd] = domain_counter.get(dd, 0) + 1

        bridges = list(log.bridge_rules_used or [])
        if bridges:
            with_bridge_rules += 1
            for b in bridges:
                bb = str(b).strip()
                if not bb:
                    continue
                bridge_counter[bb] = bridge_counter.get(bb, 0) + 1

        proof_domains = list(log.proof_domains or [])
        if proof_domains:
            proof_with_domains += 1
            for d in proof_domains:
                dd = str(d).strip()
                if not dd:
                    continue
                proof_domain_counter[dd] = proof_domain_counter.get(dd, 0) + 1

        jump_attempted_sum += int(log.cross_domain_jumps_attempted or 0)
        jump_success_sum += int(log.cross_domain_jumps_success or 0)
        jump_blocked_sum += int(log.cross_domain_jumps_blocked or 0)

        if (log.final_statute_grounding or "").strip():
            final_statute_grounded += 1

        proof = log.proof or {}
        if isinstance(proof, dict):
            provenance = proof.get("provenance") or {}
            if isinstance(provenance, dict):
                trace = provenance.get("cross_domain_trace") or {}
                if isinstance(trace, dict):
                    transitions = trace.get("domain_transitions") or []
                    if isinstance(transitions, list):
                        for transition in transitions:
                            if not isinstance(transition, dict):
                                continue
                            from_domain = str(transition.get("from_domain") or "").strip()
                            to_domain = str(transition.get("to_domain") or "").strip()
                            if not from_domain or not to_domain:
                                continue
                            pair = f"{from_domain}->{to_domain}"
                            domain_pair_counter[pair] = domain_pair_counter.get(pair, 0) + 1
                            bridge_id = str(transition.get("bridge_rule_id") or "").strip()
                            if bridge_id:
                                pair_bridge = f"{pair}::{bridge_id}"
                                domain_pair_bridge_counter[pair_bridge] = domain_pair_bridge_counter.get(pair_bridge, 0) + 1

    denom = total if total > 0 else 1
    jump_success_rate = (jump_success_sum / jump_attempted_sum) if jump_attempted_sum > 0 else 0.0

    return {
        "rows_total": total,
        "rows_with_activated_domains": with_activated_domains,
        "rows_with_bridge_rules": with_bridge_rules,
        "rows_with_shared_layer_signal": with_shared_layer_signal,
        "rows_with_proof_domains": proof_with_domains,
        "rows_with_final_statute_grounding": final_statute_grounded,
        "cross_domain_jumps_attempted_total": jump_attempted_sum,
        "cross_domain_jumps_success_total": jump_success_sum,
        "cross_domain_jumps_blocked_total": jump_blocked_sum,
        "cross_domain_jump_success_rate": jump_success_rate,
        "coverage": {
            "activated_domains": with_activated_domains / denom,
            "bridge_rules_used": with_bridge_rules / denom,
            "proof_domains": proof_with_domains / denom,
            "final_statute_grounding": final_statute_grounded / denom,
        },
        "domain_pair_transition_frequency": dict(sorted(domain_pair_counter.items(), key=lambda kv: kv[1], reverse=True)),
        "domain_pair_bridge_frequency": dict(sorted(domain_pair_bridge_counter.items(), key=lambda kv: kv[1], reverse=True)),
        "activated_domains_frequency": dict(sorted(domain_counter.items(), key=lambda kv: kv[1], reverse=True)),
        "proof_domains_frequency": dict(sorted(proof_domain_counter.items(), key=lambda kv: kv[1], reverse=True)),
        "bridge_rules_frequency": dict(sorted(bridge_counter.items(), key=lambda kv: kv[1], reverse=True)),
    }
