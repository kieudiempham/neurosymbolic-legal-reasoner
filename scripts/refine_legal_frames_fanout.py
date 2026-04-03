"""Enrich legal_frames_review.xlsx slots for rule fan-out (in-place xlsx).

Does not modify candidates or frame source_text.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from law_side.export_to_excel import _LEGAL_FRAMES_COLUMNS, _sanitize_for_excel
from law_side.legal_frame_fanout_enricher import blank, build_grounding_text, enrich_frame_row
from pipelines._paths import legal_qa_nesy_root


def _unit_index(units_path: Path) -> dict[str, dict[str, str]]:
    if not units_path.exists():
        return {}
    df = pd.read_excel(units_path)
    if "unit_id" not in df.columns:
        return {}
    idx: dict[str, dict[str, str]] = {}
    for r in df.to_dict(orient="records"):
        uid = str(r.get("unit_id") or "").strip()
        if not uid:
            continue
        idx[uid] = {
            "text": str(r.get("text") or "").strip(),
            "heading": str(r.get("heading") or "").strip(),
            "parent_context": str(r.get("parent_context") or "").strip(),
        }
    return idx


def main() -> None:
    root = legal_qa_nesy_root()
    ap = argparse.ArgumentParser(description="Enrich legal frames for rulebase fan-out.")
    ap.add_argument(
        "--frames",
        type=Path,
        default=root / "data/interim/law_parsing/legal_frames_review.xlsx",
    )
    ap.add_argument(
        "--units",
        type=Path,
        default=root / "data/interim/law_parsing/legal_units_review.xlsx",
    )
    args = ap.parse_args()

    frames_path = args.frames if args.frames.is_absolute() else root / args.frames
    units_path = args.units if args.units.is_absolute() else root / args.units

    df = pd.read_excel(frames_path)
    units = _unit_index(units_path)

    patches = 0
    for i in df.index.tolist():
        row = df.loc[i].to_dict()
        uid = str(row.get("source_unit_id") or "").strip()
        utext = ""
        if uid and uid in units:
            utext = units[uid].get("text", "")
        g = build_grounding_text(
            source_text=str(row.get("source_text") or ""),
            heading=str(row.get("heading") or ""),
            parent_context=str(row.get("parent_context") or ""),
            unit_ref_full=str(row.get("unit_ref_full") or ""),
            unit_text_fallback=utext,
        )
        patch = enrich_frame_row(row, grounding_text=g)
        if not patch:
            continue
        patches += 1
        for k, v in patch.items():
            if k not in df.columns:
                df[k] = ""
            df.at[i, k] = v

    # Write back same columns order + any extras
    cols = [c for c in _LEGAL_FRAMES_COLUMNS if c in df.columns]
    rest = [c for c in df.columns if c not in cols]
    df_out = df[cols + rest].copy()
    for col in df_out.columns:
        df_out[col] = df_out[col].map(_sanitize_for_excel)

    out_path = frames_path
    tmp = out_path.with_suffix(".fanout_tmp.xlsx")
    df_out.to_excel(tmp, index=False)
    tmp.replace(out_path)

    print(f"Patched rows: {patches}/{len(df)} -> {out_path}")


if __name__ == "__main__":
    main()
