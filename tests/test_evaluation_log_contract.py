from __future__ import annotations

import json

from evaluation.qa_log_exporter import export_logs_csv, export_logs_jsonl, load_jsonl_records
from schemas.evaluation_log import QA_EVAL_LOG_FIELDS, QAEvaluationLogArtifact
from schemas.http_response import AskResponse


def test_ask_response_auto_populates_evaluation_log_with_stable_fields() -> None:
    resp = AskResponse(session_id="sess_001", debug_trace={"query_text": "abc"})
    assert resp.evaluation_log is not None
    payload = resp.evaluation_log.model_dump(mode="json")
    assert list(payload.keys()) == QA_EVAL_LOG_FIELDS
    assert payload["sample_id"] == "sess_001"
    assert payload["query_text"] == "abc"
    assert payload["parsed_layer1"] is None
    assert payload["proof"] is None


def test_evaluation_log_schema_keeps_all_fields_even_when_null() -> None:
    log = QAEvaluationLogArtifact(sample_id="s1")
    dumped = log.model_dump(mode="json")
    assert list(dumped.keys()) == QA_EVAL_LOG_FIELDS
    assert dumped["sample_id"] == "s1"
    for key in QA_EVAL_LOG_FIELDS:
        if key == "sample_id":
            continue
        assert key in dumped


def test_exporter_normalizes_records_and_writes_jsonl_csv(tmp_path) -> None:
    in_path = tmp_path / "input.jsonl"
    out_jsonl = tmp_path / "eval_logs.jsonl"
    out_csv = tmp_path / "eval_logs.csv"

    records = [
        {"session_id": "sess_a", "evaluation_log": {"sample_id": "sess_a", "query_text": "q1"}},
        {"sample_id": "sess_b", "query_text": "q2"},
    ]
    with in_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    loaded = load_jsonl_records(in_path)
    n1 = export_logs_jsonl(loaded, out_jsonl)
    n2 = export_logs_csv(loaded, out_csv)

    assert n1 == 2
    assert n2 == 2

    lines = out_jsonl.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    row0 = json.loads(lines[0])
    assert list(row0.keys()) == QA_EVAL_LOG_FIELDS
    assert row0["sample_id"] == "sess_a"

    csv_lines = out_csv.read_text(encoding="utf-8").strip().splitlines()
    assert csv_lines[0].split(",") == QA_EVAL_LOG_FIELDS
    assert len(csv_lines) == 3
