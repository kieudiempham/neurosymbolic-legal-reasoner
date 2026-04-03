"""Retype frames that were labeled khung_ho_so but describe authority procedure only."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT / "data" / "interim" / "law_parsing" / "legal_frames_review.xlsx"

# Candidates previously cleared of thanh_phan_ho_so: Cơ quan ĐKKD là chủ thể hành vi.
_PROCEDURE_AS_AUTHORITY = [
    "CAND_UNIT_168_2025_N_CP_D31_K3_S1_SS1_HO_SO",
    "CAND_UNIT_168_2025_N_CP_D41_K2_S1_SS1_HO_SO",
    "CAND_UNIT_168_2025_N_CP_D42_K2_S1_SS1_HO_SO",
    "CAND_UNIT_168_2025_N_CP_D43_K5_S1_SS1_HO_SO",
    "CAND_UNIT_168_2025_N_CP_D44_K5_S1_SS1_HO_SO",
    "CAND_UNIT_168_2025_N_CP_D45_K9_S1_SS1_HO_SO",
    "CAND_UNIT_168_2025_N_CP_D46_K7_S1_SS1_HO_SO",
    "CAND_UNIT_168_2025_N_CP_D47_K2_S1_SS1_HO_SO",
    "CAND_UNIT_168_2025_N_CP_D48_K2_S1_SS1_HO_SO",
    "CAND_UNIT_168_2025_N_CP_D49_K2_S1_SS1_HO_SO",
    "CAND_UNIT_168_2025_N_CP_D50_K4_S1_SS1_HO_SO",
    "CAND_UNIT_168_2025_N_CP_D51_K2_S1_SS1_HO_SO",
    "CAND_UNIT_168_2025_N_CP_D55_K3_S1_SS1_HO_SO",
    "CAND_UNIT_168_2025_N_CP_D69_K8_S1_SS1_HO_SO",
    "CAND_UNIT_168_2025_N_CP_D107_K8_S1_SS1_HO_SO",
]

NEW_TYPE = "khung_hanh_dong_co_quan"
TAG = "doi_nhan_khung_tu_ho_so_sang_hanh_dong_co_quan"


def _append_note(cur: str, tag: str) -> str:
    parts = [p.strip() for p in (str(cur) or "").split(";") if p.strip()]
    if tag not in parts:
        parts.append(tag)
    return ";".join(parts)


def main() -> None:
    df = pd.read_excel(FRAMES)
    m = df["candidate_id"].astype(str).str.strip().isin(_PROCEDURE_AS_AUTHORITY) & (
        df["frame_type"].astype(str).str.strip() == "khung_ho_so"
    )
    n = int(m.sum())
    if not n:
        print("No matching rows; nothing to do.")
        return

    df.loc[m, "frame_type"] = NEW_TYPE
    df.loc[m, "tinh_chat_phap_ly"] = "co_trach_nhiem"
    fix_muc = m & (df["muc_do_day_du"].astype(str).str.strip() == "thieu_vai_slot")
    df.loc[fix_muc, "muc_do_day_du"] = "kha_day_du"
    if "ghi_chu_giai_thich" in df.columns:
        for i in df.index[m]:
            df.at[i, "ghi_chu_giai_thich"] = _append_note(str(df.at[i, "ghi_chu_giai_thich"] or ""), TAG)

    tmp = FRAMES.with_suffix(".tmp.xlsx")
    df.to_excel(tmp, index=False)
    tmp.replace(FRAMES)
    print(f"Retyped {n} row(s) to {NEW_TYPE}; updated notes and muc_do_day_du where needed.")


if __name__ == "__main__":
    main()
