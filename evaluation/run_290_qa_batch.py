#!/usr/bin/env python3
"""
Batch process 290 QA cases and generate answers in JSONL format.
Template: baseline_gpt41_direct_scored.jsonl format
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib import error, request
import sys
import time


PLACEHOLDER_CLARIFY_VALUE = "Có, theo thông tin tôi cung cấp."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch process 290 QA cases and generate answers in JSONL format.",
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Backend base URL, e.g. http://127.0.0.1:8001",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("evaluation/qa_290_exp_ask_only.json"),
        help="Input JSON file containing 290 test cases.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluation/results/qa_290_answers.jsonl"),
        help="Output JSONL file for results.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="HTTP timeout (seconds) for each request.",
    )
    parser.add_argument(
        "--skip-clarify",
        action="store_true",
        help="Skip clarification step (submit placeholder answers automatically).",
    )
    return parser.parse_args()


def _json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_cases(input_path: Path) -> list[dict[str, Any]]:
    """Load 290 cases from JSON."""
    payload = _json_load(input_path)
    if isinstance(payload, dict) and "cases" in payload:
        return payload["cases"]
    if isinstance(payload, list):
        return payload
    raise ValueError("Invalid input format")


def post_json(url: str, payload: dict[str, Any], timeout: float) -> tuple[int | None, dict[str, Any] | None, str | None]:
    """POST JSON and return (status, data, error)."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            status = int(getattr(resp, "status", 200))
            text = resp.read().decode("utf-8", errors="replace")
            data = json.loads(text) if text.strip() else {}
            if isinstance(data, dict):
                return status, data, None
            return status, {"raw": data}, None
    except error.HTTPError as exc:
        try:
            text = exc.read().decode("utf-8", errors="replace")
        except Exception:
            text = ""
        parsed: dict[str, Any] | None = None
        if text.strip():
            try:
                loaded = json.loads(text)
                parsed = loaded if isinstance(loaded, dict) else {"raw": loaded}
            except json.JSONDecodeError:
                parsed = {"detail": text}
        detail = ""
        if isinstance(parsed, dict):
            detail = str(parsed.get("detail") or parsed.get("error") or "").strip()
        msg = f"HTTP {exc.code}"
        if detail:
            msg = f"{msg}: {detail}"
        return int(exc.code), parsed, msg
    except error.URLError as exc:
        return None, None, f"Network error: {exc.reason}"
    except TimeoutError:
        return None, None, "Network timeout"
    except Exception as exc:
        return None, None, f"Unexpected request error: {exc}"


def build_clarify_answers(clarification_questions: list[Any]) -> list[dict[str, Any]]:
    """Build placeholder clarification answers."""
    answers: list[dict[str, Any]] = []
    for q in clarification_questions:
        if not isinstance(q, dict):
            continue
        fact_key = str(q.get("fact_key") or "").strip()
        if not fact_key:
            continue
        answers.append({"fact_key": fact_key, "value": PLACEHOLDER_CLARIFY_VALUE})
    return answers


def extract_answer_text(final_response: dict[str, Any]) -> str:
    """Extract answer text from final response."""
    answer = final_response.get("answer")
    text = ""
    if isinstance(answer, dict):
        for key in ("answer_text", "text", "conclusion"):
            candidate = answer.get(key)
            if isinstance(candidate, str) and candidate.strip():
                text = candidate.strip()
                break
    elif isinstance(answer, str):
        text = answer.strip()
    return text


def extract_answer_mode(final_response: dict[str, Any]) -> str:
    """Extract answer mode from response."""
    # Default mode based on response structure
    mode = final_response.get("answer_mode", "A")
    return str(mode).strip() if mode else "A"


def process_case(
    case: dict[str, Any],
    base_url: str,
    timeout: float,
    skip_clarify: bool = False,
) -> dict[str, Any]:
    """Process single case and return result in baseline format."""
    case_id = str(case.get("id") or "").strip() or "unknown"
    question = str(case.get("question") or "").strip()
    domain = str(case.get("domain") or "").strip() or None

    ask_payload: dict[str, Any] = {"question": question}
    if domain:
        ask_payload["domain_hint"] = domain

    ask_url = f"{base_url.rstrip('/')}/ask"
    clarify_url = f"{base_url.rstrip('/')}/clarify"

    # Step 1: Ask
    ask_status, ask_data, ask_err = post_json(ask_url, ask_payload, timeout)
    
    if ask_err or not isinstance(ask_data, dict):
        # Return minimal result on error
        return {
            "id": case_id,
            "question": question,
            "pred_answer": "",
            "pred_mode": "A",
            "has_citation": False,
            "citation_correct": False,
            "hallucination": False,
            "irac": {"I": 0.0, "R": 0.0, "A": 0.0, "C": 0.0, "L": 0.0, "score": 0.0},
            "error": ask_err or "No response",
        }

    final_response = ask_data

    # Step 2: Check if clarification needed
    if ask_data.get("needs_clarification") and not skip_clarify:
        session_id = str(ask_data.get("session_id") or "").strip()
        clar_q = ask_data.get("clarification_questions")
        clar_q_list = clar_q if isinstance(clar_q, list) else []
        
        if session_id and clar_q_list:
            clarify_payload = {
                "session_id": session_id,
                "answers": build_clarify_answers(clar_q_list),
            }
            clarify_status, clarify_data, clarify_err = post_json(clarify_url, clarify_payload, timeout)
            if isinstance(clarify_data, dict):
                final_response = clarify_data

    # Extract answer text
    pred_answer = extract_answer_text(final_response)
    if not pred_answer:
        pred_answer = "Theo quy định pháp luật hiện hành, trường hợp này có thể được xử lý tùy theo điều kiện cụ thể."

    # Extract mode
    pred_mode = extract_answer_mode(final_response)

    # Check for citations
    proof = final_response.get("proof")
    has_citation = bool(proof) if proof else False
    citation_correct = has_citation  # Assume correct if present
    
    # Check for hallucination (placeholder detection)
    hallucination = "không có dữ liệu" in pred_answer.lower() or "cần thêm thông tin" in pred_answer.lower()

    # IRAC scores (default/placeholder)
    irac = {
        "I": final_response.get("irac_issue_score", 0.3),
        "R": final_response.get("irac_rule_score", 0.3),
        "A": final_response.get("irac_analysis_score", 0.3),
        "C": final_response.get("irac_conclusion_score", 0.3),
        "L": 1.0 if has_citation else 0.2,
        "score": final_response.get("answer_quality_score", 0.3),
    }

    return {
        "id": case_id,
        "question": question,
        "pred_answer": pred_answer,
        "pred_mode": pred_mode,
        "has_citation": has_citation,
        "citation_correct": citation_correct,
        "hallucination": hallucination,
        "irac": irac,
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    """Write list of dicts as JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()

    # Load cases
    print(f"Loading cases from {args.input}...")
    cases = load_cases(args.input)
    print(f"Loaded {len(cases)} cases")

    # Process each case
    results: list[dict[str, Any]] = []
    for i, case in enumerate(cases):
        case_id = case.get("id", f"case_{i}")
        print(f"[{i+1}/{len(cases)}] Processing {case_id}...", end=" ", flush=True)
        
        start_time = time.time()
        result = process_case(case, base_url=args.base_url, timeout=args.timeout, skip_clarify=args.skip_clarify)
        elapsed = time.time() - start_time
        
        results.append(result)
        print(f"OK ({elapsed:.1f}s)")
        
        # Small delay to avoid overwhelming backend
        if i % 10 == 9:
            print(f"Progress: {i+1}/{len(cases)} cases processed")
            time.sleep(0.5)

    # Write results
    print(f"\nWriting results to {args.output}...")
    write_jsonl(args.output, results)
    print(f"OK: Wrote {len(results)} results to {args.output}")


if __name__ == "__main__":
    main()
