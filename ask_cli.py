from __future__ import annotations

import sys
from typing import Any

import requests

API_URL = "http://127.0.0.1:8001/ask"
TIMEOUT_SECONDS = 30
EXIT_WORDS = {"exit", "quit"}


def _get_attr(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _get_path(obj: Any, *keys: str) -> Any:
    cur = obj
    for key in keys:
        cur = _get_attr(cur, key)
        if cur is None:
            return None
    return cur


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text


def _extract_clarification_questions(data: Any) -> list[str]:
    items = _get_attr(data, "clarification_questions")
    if not isinstance(items, list):
        return []
    out: list[str] = []
    for item in items:
        q = _as_text(_get_attr(item, "question_text"))
        if q:
            out.append(q)
    return out


def _print_response(data: dict[str, Any]) -> None:
    printed = False

    answer_text = _as_text(_get_path(data, "answer", "answer_text"))
    if answer_text:
        print("\n=== TRA LOI ===")
        print(answer_text)
        printed = True

    needs_clarification = bool(_get_attr(data, "needs_clarification"))
    if needs_clarification:
        questions = _extract_clarification_questions(data)
        if questions:
            print("\n=== CAN LAM RO ===")
            for i, q in enumerate(questions, 1):
                print(f"{i}. {q}")
            printed = True

    rule_id = _as_text(_get_path(data, "selected_rule", "rule_id"))
    if rule_id:
        print("\n=== SELECTED RULE ===")
        print(rule_id)
        printed = True

    debug_error = _as_text(_get_path(data, "debug_trace", "error"))
    if debug_error:
        print("\n=== ERROR ===")
        print(debug_error)
        printed = True

    debug_warning = _as_text(_get_path(data, "debug_trace", "warning"))
    if debug_warning:
        print("\n=== WARNING ===")
        print(debug_warning)
        printed = True

    if not printed:
        print("\nKhong co cau tra loi huu ich.")


def main() -> int:
    print("Nhap cau hoi phap luat (go 'exit' de thoat):")

    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThoat.")
            return 0

        if not question:
            continue

        if question.lower() in EXIT_WORDS:
            print("Thoat.")
            return 0

        payload = {
            "question": question,
            "domain": None,
        }

        try:
            response = requests.post(API_URL, json=payload, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                print("\nPhan hoi khong hop le tu backend.")
                continue
            _print_response(data)
        except requests.exceptions.RequestException as exc:
            print(f"\nLoi ket noi backend: {exc}")
        except ValueError:
            print("\nKhong doc duoc JSON tu backend.")


if __name__ == "__main__":
    sys.exit(main())
