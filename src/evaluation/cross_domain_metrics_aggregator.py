"""Cross-domain/shared-layer metrics aggregator for offline analysis scripts."""

from __future__ import annotations

from typing import Any, Iterable

from schemas.evaluation_log import QAEvaluationLogArtifact
from evaluation.qa_log_exporter import summarize_cross_domain_metrics


def aggregate_contribution_metrics(
    records: Iterable[dict[str, Any] | QAEvaluationLogArtifact],
) -> dict[str, Any]:
    """Aggregate contribution metrics for multi-rulebases/shared-layer reasoning."""
    base = summarize_cross_domain_metrics(records)

    attempted = int(base.get("cross_domain_jumps_attempted_total") or 0)
    success = int(base.get("cross_domain_jumps_success_total") or 0)
    blocked = int(base.get("cross_domain_jumps_blocked_total") or 0)

    rows_total = int(base.get("rows_total") or 0)
    rows_with_bridge = int(base.get("rows_with_bridge_rules") or 0)
    rows_with_shared = int(base.get("rows_with_shared_layer_signal") or 0)

    contribution = {
        "shared_layer_activation_rate": (rows_with_shared / rows_total) if rows_total else 0.0,
        "bridge_usage_rate": (rows_with_bridge / rows_total) if rows_total else 0.0,
        "jump_block_rate": (blocked / attempted) if attempted else 0.0,
        "jump_success_rate": (success / attempted) if attempted else 0.0,
    }

    return {
        **base,
        "contribution_metrics": contribution,
    }
