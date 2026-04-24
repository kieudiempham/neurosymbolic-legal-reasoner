from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from urllib import error, request


PLACEHOLDER_CLARIFY_VALUE = "Co, theo thong tin toi cung cap."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run 30-case backend audit via live ask->clarify flow and export normalized outputs.",
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Backend base URL, e.g. http://127.0.0.1:8000",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("tests/fixtures/30_tests.json"),
        help="Input JSON file containing test cases.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tests/output"),
        help="Directory for result files.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP timeout (seconds) for each request.",
    )
    return parser.parse_args()


def _json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_cases(input_path: Path) -> list[dict[str, Any]]:
    payload = _json_load(input_path)
    if isinstance(payload, list):
        return [c for c in payload if isinstance(c, dict)]
    if isinstance(payload, dict):
        for key in ("cases", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [c for c in value if isinstance(c, dict)]
    raise ValueError("Input JSON must be a list of objects or an object containing cases/items/data list")


def post_json(url: str, payload: dict[str, Any], timeout: float) -> tuple[int | None, dict[str, Any] | None, str | None]:
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
    except Exception as exc:  # pragma: no cover - defensive fallback
        return None, None, f"Unexpected request error: {exc}"


def build_clarify_answers(clarification_questions: list[Any]) -> list[dict[str, Any]]:
    answers: list[dict[str, Any]] = []
    for q in clarification_questions:
        if not isinstance(q, dict):
            continue
        fact_key = str(q.get("fact_key") or "").strip()
        if not fact_key:
            continue
        # Deterministic placeholder so reruns are stable and comparable.
        answers.append({"fact_key": fact_key, "value": PLACEHOLDER_CLARIFY_VALUE})
    return answers


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, dict):
        return len(value) > 0
    if isinstance(value, (list, tuple, set)):
        return len(value) > 0
    if isinstance(value, str):
        return bool(value.strip())
    return True


def extract_answer_snippet(final_response: dict[str, Any]) -> str | None:
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
    if not text:
        return None
    compact = " ".join(text.split())
    return compact[:280]


def extract_warning_codes(final_response: dict[str, Any]) -> list[str]:
    warnings = final_response.get("warnings")
    if not isinstance(warnings, list):
        return []
    out: list[str] = []
    for item in warnings:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or "").strip()
        if code:
            out.append(code)
    return out


def extract_final_status(final_response: dict[str, Any]) -> str | None:
    evaluation_log = final_response.get("evaluation_log")
    if isinstance(evaluation_log, dict):
        status = str(evaluation_log.get("final_status") or "").strip()
        if status:
            return status
    status = str(final_response.get("final_status") or "").strip()
    return status or None


def extract_error_stage_final(final_response: dict[str, Any]) -> str | None:
    evaluation_log = final_response.get("evaluation_log")
    if isinstance(evaluation_log, dict):
        stage = str(evaluation_log.get("error_stage_final") or "").strip()
        if stage:
            return stage
    return None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _top_counter(items: list[str], limit: int = 10) -> list[dict[str, Any]]:
    counter = Counter(x for x in items if x)
    ranked = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    return [{"value": value, "count": count} for value, count in ranked[:limit]]


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    answered = 0
    answered_final = 0
    answered_partial = 0
    degraded = 0
    failed_or_open = 0
    with_proof = 0
    with_selected_rule = 0
    needs_clarification = 0

    warning_codes: list[str] = []
    quality_reasons: list[str] = []
    error_stages: list[str] = []

    for row in results:
        final_status = str(row.get("final_status") or "").strip().lower()
        answer_quality = str(row.get("answer_quality") or "").strip().lower()

        if bool(row.get("needs_clarification")):
            needs_clarification += 1
        if bool(row.get("proof_present")):
            with_proof += 1
        if row.get("selected_rule_id"):
            with_selected_rule += 1

        if final_status == "answered":
            answered += 1
            if answer_quality == "final":
                answered_final += 1
            if answer_quality == "partial":
                answered_partial += 1

        if answer_quality == "degraded":
            degraded += 1

        if row.get("error") or final_status in {"failed", "open"}:
            failed_or_open += 1

        warning_codes.extend([str(x) for x in row.get("warning_codes") or [] if str(x).strip()])
        reason = str(row.get("answer_quality_reason") or "").strip()
        if reason:
            quality_reasons.append(reason)
        stage = str(row.get("error_stage_final") or "").strip()
        if stage:
            error_stages.append(stage)

    return {
        "total_cases": len(results),
        "answered": answered,
        "answered_final": answered_final,
        "answered_partial": answered_partial,
        "degraded": degraded,
        "failed_or_open": failed_or_open,
        "with_proof": with_proof,
        "with_selected_rule": with_selected_rule,
        "needs_clarification": needs_clarification,
        "top_warning_codes": _top_counter(warning_codes),
        "top_answer_quality_reason": _top_counter(quality_reasons),
        "top_error_stage_final": _top_counter(error_stages),
    }


def process_case(case: dict[str, Any], base_url: str, timeout: float, raw_dir: Path) -> dict[str, Any]:
    case_id = str(case.get("id") or "").strip() or "unknown"
    question = str(case.get("question") or "").strip()
    domain_hint = str(case.get("domain_hint") or "").strip() or None
    intent_hint = str(case.get("intent_hint") or "").strip() or None

    ask_status: int | None = None
    clarify_status: int | None = None
    needs_clarification = False
    error_msg: str | None = None

    ask_payload: dict[str, Any] = {
        "question": question,
    }
    if domain_hint:
        ask_payload["domain"] = domain_hint

    ask_url = f"{base_url.rstrip('/')}/ask"
    clarify_url = f"{base_url.rstrip('/')}/clarify"

    ask_status, ask_data, ask_err = post_json(ask_url, ask_payload, timeout)
    if ask_err:
        error_msg = f"ask_failed: {ask_err}"

    final_response: dict[str, Any] = ask_data if isinstance(ask_data, dict) else {}

    if isinstance(ask_data, dict):
        needs_clarification = bool(ask_data.get("needs_clarification"))
        if needs_clarification:
            session_id = str(ask_data.get("session_id") or "").strip()
            clar_q = ask_data.get("clarification_questions")
            clar_q_list = clar_q if isinstance(clar_q, list) else []
            clarify_payload = {
                "session_id": session_id,
                "answers": build_clarify_answers(clar_q_list),
            }
            clarify_status, clarify_data, clarify_err = post_json(clarify_url, clarify_payload, timeout)
            if isinstance(clarify_data, dict):
                final_response = clarify_data
            else:
                final_response = {"ask_response": ask_data}
            if clarify_err:
                error_msg = f"clarify_failed: {clarify_err}"

    raw_path = raw_dir / f"{case_id}.json"
    write_json(raw_path, final_response)

    selected_rule = final_response.get("selected_rule")
    selected_rule_id = None
    if isinstance(selected_rule, dict):
        rid = str(selected_rule.get("rule_id") or "").strip()
        selected_rule_id = rid or None

    answer_quality = final_response.get("answer_quality")
    answer_quality = str(answer_quality).strip() if answer_quality is not None else None
    answer_quality_reason = final_response.get("answer_quality_reason")
    answer_quality_reason = str(answer_quality_reason).strip() if answer_quality_reason is not None else None

    result = {
        "id": case_id,
        "question": question,
        "domain_hint": domain_hint,
        "intent_hint": intent_hint,
        "ask_http_status": ask_status,
        "clarify_http_status": clarify_status,
        "needs_clarification": needs_clarification,
        "final_status": extract_final_status(final_response),
        "answer_quality": answer_quality,
        "answer_quality_reason": answer_quality_reason,
        "warning_codes": extract_warning_codes(final_response),
        "error_stage_final": extract_error_stage_final(final_response),
        "selected_rule_id": selected_rule_id,
        "proof_present": _nonempty(final_response.get("proof")),
        "answer_present": _nonempty(final_response.get("answer")),
        "answer_snippet": extract_answer_snippet(final_response),
        "raw_result_path": raw_path.as_posix(),
        "error": error_msg,
    }
    return result


def main() -> None:
    args = parse_args()

    cases = load_cases(args.input)
    output_dir = args.output_dir
    raw_dir = output_dir / "raw"
    results_path = output_dir / "30_case_audit_results.json"
    summary_path = output_dir / "30_case_audit_summary.json"

    results: list[dict[str, Any]] = []
    for case in cases:
        result = process_case(case, base_url=args.base_url, timeout=args.timeout, raw_dir=raw_dir)
        results.append(result)

    summary = build_summary(results)
    write_json(results_path, results)
    write_json(summary_path, summary)

    print(f"results_path={results_path.as_posix()}")
    print(f"summary_path={summary_path.as_posix()}")
    print(f"raw_dir={raw_dir.as_posix()}")
    print(f"total_cases_loaded={len(cases)}")
    print(f"total_cases_processed={len(results)}")


if __name__ == "__main__":
    main()