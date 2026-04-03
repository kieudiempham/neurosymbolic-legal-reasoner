"""Refine thanh_phan_ho_so only for frame_type=khung_ho_so in legal_frames_review.xlsx."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT / "data" / "interim" / "law_parsing" / "legal_frames_review.xlsx"

TAG_BO_SUNG = "bo_sung_thanh_phan_ho_so_tu_source_text"
TAG_CHUA_PHUC_HOI = "chua_phuc_hoi_duoc_thanh_phan_ho_so"


def _append_note(cur: str, tag: str) -> str:
    tag = tag.strip()
    if not tag:
        return cur or ""
    parts = [p.strip() for p in (str(cur) or "").split(";") if p.strip()]
    if tag not in parts:
        parts.append(tag)
    return ";".join(parts)


def main() -> None:
    df = pd.read_excel(FRAMES)
    is_khung_hs = df["frame_type"].astype(str).str.strip().eq("khung_ho_so")
    idxs = df.index[is_khung_hs].tolist()

    # candidate_id -> thanh_phan_ho_so (None = leave unchanged; "" = clear)
    by_cand: dict[str, str | None] = {
        "CAND_DOC_D12_K1_HO_SO": "văn bản ủy quyền cho cá nhân thực hiện thủ tục đăng ký doanh nghiệp",
        "CAND_DOC_D12_K2_HO_SO": (
            "bản sao hợp đồng ủy quyền cho tổ chức thực hiện thủ tục đăng ký doanh nghiệp; "
            "giấy giới thiệu hoặc văn bản phân công nhiệm vụ cho cá nhân trực tiếp thực hiện thủ tục"
        ),
        "CAND_DOC_D28_K7_HO_SO": (
            "quyết định cho phép chuyển đổi thành doanh nghiệp xã hội; "
            "giấy chứng nhận đăng ký thành lập cơ sở bảo trợ xã hội hoặc giấy phép thành lập và công nhận điều lệ quỹ; "
            "bản sao Giấy chứng nhận đăng ký thuế; "
            "bản sao văn bản cơ quan đăng ký đầu tư về góp vốn, mua cổ phần của nhà đầu tư nước ngoài (khi thuộc diện Luật Đầu tư)"
        ),
        "CAND_UNIT_LUATDN_D57_K5_S1_SS1_HO_SO": (
            "chương trình và tài liệu họp; tài liệu về sửa đổi, bổ sung Điều lệ công ty, thông qua chiến lược phát triển, "
            "báo cáo tài chính hằng năm, tổ chức lại hoặc giải thể công ty (theo quy định gửi thành viên)"
        ),
        "CAND_UNIT_LUATDN_D61_K4_S1_SS1_HO_SO": (
            "báo cáo kết quả kiểm phiếu; nghị quyết và quyết định được thông qua (thông báo cho các thành viên)"
        ),
        "CAND_UNIT_168_2025_N_CP_D15_K3_S1_SS1_HO_SO": (
            "bản sao văn bản kết luận của cơ quan có thẩm quyền về việc tên doanh nghiệp xâm phạm quyền sở hữu công nghiệp; "
            "bản sao hợp đồng sử dụng đối tượng sở hữu công nghiệp (khi người yêu cầu là bên được chuyển quyền sử dụng)"
        ),
        "CAND_UNIT_168_2025_N_CP_D15_K4_S1_SS1_HO_SO": (
            "các giấy tờ quy định tại khoản 3 Điều 15 (kèm theo thông báo của cơ quan đăng ký kinh doanh)"
        ),
        "CAND_UNIT_168_2025_N_CP_D31_K3_S1_SS1_HO_SO": "",
        "CAND_UNIT_168_2025_N_CP_D31_K6_S1_SS1_HO_SO": (
            "văn bản đề nghị dừng thực hiện thủ tục đăng ký doanh nghiệp"
        ),
        "CAND_UNIT_168_2025_N_CP_D41_K2_S1_SS1_HO_SO": "",
        "CAND_UNIT_168_2025_N_CP_D42_K2_S1_SS1_HO_SO": "",
        "CAND_UNIT_168_2025_N_CP_D43_K5_S1_SS1_HO_SO": "",
        "CAND_UNIT_168_2025_N_CP_D44_K5_S1_SS1_HO_SO": "",
    }

    procedural_empty = [
        "CAND_UNIT_168_2025_N_CP_D45_K9_S1_SS1_HO_SO",
        "CAND_UNIT_168_2025_N_CP_D46_K7_S1_SS1_HO_SO",
        "CAND_UNIT_168_2025_N_CP_D47_K2_S1_SS1_HO_SO",
        "CAND_UNIT_168_2025_N_CP_D48_K2_S1_SS1_HO_SO",
        "CAND_UNIT_168_2025_N_CP_D49_K2_S1_SS1_HO_SO",
        "CAND_UNIT_168_2025_N_CP_D50_K4_S1_SS1_HO_SO",
        "CAND_UNIT_168_2025_N_CP_D51_K2_S1_SS1_HO_SO",
        "CAND_UNIT_168_2025_N_CP_D54_K4_S1_SS1_HO_SO",
        "CAND_UNIT_168_2025_N_CP_D55_K3_S1_SS1_HO_SO",
        "CAND_UNIT_168_2025_N_CP_D69_K8_S1_SS1_HO_SO",
        "CAND_UNIT_168_2025_N_CP_D107_K8_S1_SS1_HO_SO",
    ]
    for c in procedural_empty:
        by_cand[c] = ""

    by_cand["CAND_UNIT_168_2025_N_CP_D54_K4_S1_SS1_HO_SO"] = (
        "hồ sơ đăng ký doanh nghiệp theo khoản 1, khoản 2 và khoản 3 Điều 54"
    )

    by_cand["CAND_UNIT_168_2025_N_CP_D59_K2_B_S1_SS1_HO_SO"] = (
        "văn bản giải trình của doanh nghiệp về lý do đăng ký thay đổi (kèm hồ sơ đăng ký thay đổi khi đăng ký phục vụ giải thể)"
    )

    changed = 0
    for i in idxs:
        cand = str(df.at[i, "candidate_id"]).strip()
        if cand not in by_cand:
            continue
        new_val = by_cand[cand]
        if new_val is None:
            continue
        old = df.at[i, "thanh_phan_ho_so"]
        old_s = "" if pd.isna(old) else str(old).strip()
        if old_s.lower() == "nan":
            old_s = ""
        note_col = "ghi_chu_giai_thich" if "ghi_chu_giai_thich" in df.columns else None
        if new_val == "":
            touched = False
            if old_s != "":
                df.at[i, "thanh_phan_ho_so"] = ""
                touched = True
            if str(df.at[i, "muc_do_day_du"] or "").strip() != "thieu_vai_slot":
                df.at[i, "muc_do_day_du"] = "thieu_vai_slot"
                touched = True
            if note_col:
                n0 = str(df.at[i, note_col] or "")
                n2 = _append_note(_append_note(n0, TAG_CHUA_PHUC_HOI), "source_khong_mo_ta_thanh_phan_ho_so_nop")
                if n2 != n0:
                    df.at[i, note_col] = n2
                    touched = True
            if touched:
                changed += 1
            continue
        if old_s != new_val.strip():
            df.at[i, "thanh_phan_ho_so"] = new_val
            if note_col:
                df.at[i, note_col] = _append_note(str(df.at[i, note_col] or ""), TAG_BO_SUNG)
            changed += 1

    tmp = FRAMES.with_suffix(".tmp.xlsx")
    df.to_excel(tmp, index=False)
    tmp.replace(FRAMES)
    print(f"Patched khung_ho_so rows touched: {changed}, file={FRAMES}")


if __name__ == "__main__":
    main()
