#!/usr/bin/env python3
"""Post-process `legal_units_review.xlsx`: fill empty deontic_signal, widen thin action_hint, drop bad object_hint.

Does not modify `text`. Only touches: deontic_signal, action_hint, object_hint, notes.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

# --- A. deontic backfill (first match wins, order matters) ---
_DEONTIC_RULES: list[tuple[str, str]] = [
    (
        r"\b(có\s+quyền|được\s+quyền|được\s+phép|từ\s+chối)\b",
        "quyen",
    ),
    (
        r"\b(phải|có\s+nghĩa\s+vụ|thực\s+hiện\s+nghĩa\s+vụ)\b",
        "nghia_vu",
    ),
    (
        r"\b(có\s+trách\s+nhiệm|chịu\s+trách\s+nhiệm|giám\s+sát|bảo\s+đảm)\b",
        "co_trach_nhiem",
    ),
    (
        r"\b(trong\s+thời\s+hạn|kể\s+từ\s+ngày)\b",
        "thoi_han",
    ),
    (
        r"\b(hồ\s+sơ\s+bao\s+gồm|kèm\s+theo)\b",
        "ho_so",
    ),
]


def _is_empty_cell(v) -> bool:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return True
    s = str(v).strip()
    return s == "" or s.lower() == "nan"


def _norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _clip(s: str, max_chars: int) -> str:
    s = _norm_space(s)
    if len(s) <= max_chars:
        return s
    cut = s[:max_chars].rsplit(" ", 1)[0]
    return cut if cut else s[:max_chars]


def _fill_deontic(text: str) -> str | None:
    if not text or not text.strip():
        return None
    compact = _norm_space(text)
    for pat, label in _DEONTIC_RULES:
        if re.search(pat, compact, flags=re.I | re.U):
            return label
    return None


# --- B. action_hint expansion ---
_ACTION_BLACKLIST = frozenset(
    {
        "từ chối",
        "góp vốn",
        "giải thể",
        "ban hành",
        "xem xét",
        "quyết định",
    }
)


def _expand_action_hint(text: str, current: str) -> str | None:
    cur = _norm_space(current)
    low_t = text.lower()
    key = cur.lower()
    if key not in _ACTION_BLACKLIST:
        return None
    idx = low_t.find(key)
    if idx < 0:
        return None
    segment = text[idx:]
    segment = re.split(r"[.;]", segment, maxsplit=1)[0].strip()
    cpos = segment.find(",")
    if cpos > len(cur) + 8:
        segment = segment[:cpos].strip()
    segment = _norm_space(segment)
    if len(segment) <= len(cur) + 3:
        return None
    return _clip(segment, 72)


# --- C. object_hint fragments & recovery ---
_OBJECT_BLACKLIST = frozenset(
    {
        "là thành",
        "giấy tờ pháp",
        "quyết định",
        "nghĩa",
        "đáp ứng",
        "áp dụng",
        "có ít",
    }
)

_OBJECT_RECOVERY: list[tuple[str, str]] = [
    # fragment key (normalized lower) -> regex with one capture group = full NP
    (
        "là thành",
        r"\b(là\s+thành\s+viên(?:\s+hội\s+đồng[^.;]{0,35}?)?)\b",
    ),
    (
        "giấy tờ pháp",
        r"\b(giấy\s+tờ\s+pháp\s+lý[^.;]{0,35}?)(?=\s*[.;,]|$)",
    ),
    (
        "quyết định",
        r"\b(quyết\s+định(?:\s+[\wÀ-ỹ,-]+){0,6})\b",
    ),
    (
        "đáp ứng",
        r"\b(đáp\s+ứng(?:\s+[\wÀ-ỹ,-]+){0,6})\b",
    ),
    (
        "áp dụng",
        r"\b(áp\s+dụng(?:\s+[\wÀ-ỹ,-]+){0,6})\b",
    ),
    (
        "có ít",
        r"\b(có\s+ít\s+nhất[^.;]{3,50}?)(?=\s*[.;,]|$)",
    ),
    (
        "nghĩa",
        r"\b((?:đồng\s+)?nghĩa\s+(?:là|với)\s+[^.;]{3,45}?)(?=\s*[.;,]|$)",
    ),
]


def _recover_object_hint(text: str, frag_key: str) -> str | None:
    compact = _norm_space(text)
    want = frag_key.lower().strip()
    for fk, pat in _OBJECT_RECOVERY:
        if fk != want:
            continue
        m = re.search(pat, compact, flags=re.I | re.U)
        if not m:
            continue
        got = _norm_space(m.group(1))
        if len(got) >= 8 and _object_fragment_key(got) is None:
            return _clip(got, 90)
    return None


def _object_fragment_key(phrase: str) -> str | None:
    """Match only exact blacklisted fragments, so legitimate longer NPs are left unchanged."""
    p = _norm_space(phrase).lower().rstrip(".")
    return p if p in _OBJECT_BLACKLIST else None


def _append_note(existing, tag: str) -> str:
    if _is_empty_cell(existing):
        e = ""
    else:
        e = _norm_space(str(existing))
    if not e:
        return tag
    parts = [x.strip() for x in re.split(r"[;|,]+", e) if x.strip()]
    if tag not in parts:
        parts.append(tag)
    return "; ".join(parts)


def run_cleanup(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    stats = {"A_deontic": 0, "B_action": 0, "C_object": 0}
    required = {"text", "deontic_signal", "action_hint", "object_hint", "notes"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    df_out = df.copy(deep=True)

    for i in df_out.index:
        text = str(df_out.at[i, "text"])

        # A
        if _is_empty_cell(df_out.at[i, "deontic_signal"]):
            d = _fill_deontic(text)
            if d:
                df_out.at[i, "deontic_signal"] = d
                df_out.at[i, "notes"] = _append_note(df_out.at[i, "notes"], "cleanup_deontic_signal")
                stats["A_deontic"] += 1

        # B
        if not _is_empty_cell(df_out.at[i, "action_hint"]):
            cur = str(df_out.at[i, "action_hint"]).strip()
            expanded = _expand_action_hint(text, cur)
            if expanded:
                df_out.at[i, "action_hint"] = expanded
                df_out.at[i, "notes"] = _append_note(df_out.at[i, "notes"], "cleanup_action_hint")
                stats["B_action"] += 1

        # C
        if not _is_empty_cell(df_out.at[i, "object_hint"]):
            obj = str(df_out.at[i, "object_hint"]).strip()
            fk = _object_fragment_key(obj)
            if fk:
                recovered = _recover_object_hint(text, fk)
                if recovered:
                    df_out.at[i, "object_hint"] = recovered
                    df_out.at[i, "notes"] = _append_note(df_out.at[i, "notes"], "cleanup_object_hint_np")
                else:
                    df_out.at[i, "object_hint"] = ""
                    df_out.at[i, "notes"] = _append_note(df_out.at[i, "notes"], "cleanup_object_hint_clear")
                stats["C_object"] += 1

    return df_out, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    default_in = root / "data/interim/law_parsing/legal_units_review.xlsx"
    parser.add_argument("--input", type=Path, default=default_in, help="Input xlsx path")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output xlsx (default: overwrite --input)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print stats only; do not write file",
    )
    args = parser.parse_args()
    inp = args.input.resolve()
    if not inp.is_file():
        print(f"Not found: {inp}", file=sys.stderr)
        return 1

    df = pd.read_excel(inp)
    df_out, stats = run_cleanup(df)

    print("cleanup_legal_units_review:", stats)
    if args.dry_run:
        return 0

    out = args.output.resolve() if args.output else inp
    out.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_excel(out, index=False)
    print(f"Wrote: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
