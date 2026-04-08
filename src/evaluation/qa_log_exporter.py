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
