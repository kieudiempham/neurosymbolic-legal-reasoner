"""Apply rubric scoring to existing rule-base review spreadsheets.

This is a *post-processing* step for paper research:
it reads:
- data/interim/law_parsing/candidate_normative_sentences.xlsx
- data/interim/law_parsing/legal_frames_review.xlsx

and appends rubric columns for human review.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from law_side.rubric_scoring import apply_candidate_rubric, apply_frame_rubric
from pipelines._paths import legal_qa_nesy_root


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(description="Apply rubric scoring to review Excel files.")
    p.add_argument(
        "--candidate_excel",
        type=Path,
        default=root / "data/interim/law_parsing/candidate_normative_sentences.xlsx",
    )
    p.add_argument(
        "--frames_excel",
        type=Path,
        default=root / "data/interim/law_parsing/legal_frames_review.xlsx",
    )
    p.add_argument("--inplace", action="store_true", default=True)
    args = p.parse_args()

    candidate_path: Path = args.candidate_excel
    frames_path: Path = args.frames_excel

    df_candidates = pd.read_excel(candidate_path)
    df_frames = pd.read_excel(frames_path)

    df_candidates_scored = apply_candidate_rubric(df_candidates)
    df_frames_scored = apply_frame_rubric(df_frames, df_candidates_scored)

    # Write back.
    if args.inplace:
        df_candidates_scored.to_excel(candidate_path, index=False)
        df_frames_scored.to_excel(frames_path, index=False)
        print("Rubrics applied (in-place).")
    else:
        out_candidate = candidate_path.with_name(candidate_path.stem + "_scored.xlsx")
        out_frames = frames_path.with_name(frames_path.stem + "_scored.xlsx")
        df_candidates_scored.to_excel(out_candidate, index=False)
        df_frames_scored.to_excel(out_frames, index=False)
        print("Rubrics applied (new files).")


if __name__ == "__main__":
    main()

