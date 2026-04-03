"""Refine rulebase_seed.xlsx: content dedup, threshold structure, enrich he_qua / thanh_phan."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from law_side.rulebase_seed_refiner import refine_rulebase_dataframe
from pipelines.run_rulebase_seed_only import RULEBASE_SEED_COLUMNS


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "data" / "processed" / "rulebase" / "rulebase_seed.xlsx"
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_excel(path)
    n0 = len(df)
    refined = refine_rulebase_dataframe(df)
    for c in RULEBASE_SEED_COLUMNS:
        if c not in refined.columns:
            refined[c] = ""
    refined = refined[RULEBASE_SEED_COLUMNS]
    tmp = path.with_suffix(".tmp.xlsx")
    refined.to_excel(tmp, index=False)
    tmp.replace(path)
    print(f"rulebase_seed refined: {n0} -> {len(refined)} rows -> {path}")


if __name__ == "__main__":
    main()
