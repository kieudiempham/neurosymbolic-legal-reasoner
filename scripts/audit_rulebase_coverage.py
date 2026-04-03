"""Audit coverage: articles, rule types, dedup loss. Read-only on pipeline inputs."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# (rule_type, frame_type, candidate_rule_type values in Excel)
TYPE_DEFS: list[tuple[str, str, frozenset[str]]] = [
    ("quy_tac_nghia_vu", "khung_nghia_vu", frozenset({"quy_pham_nghia_vu", "nghia_vu"})),
    ("quy_tac_thoi_han", "khung_thoi_han", frozenset({"quy_pham_thoi_han", "thoi_han"})),
    ("quy_tac_ho_so", "khung_ho_so", frozenset({"thanh_phan_ho_so", "quy_pham_ho_so"})),
    ("quy_tac_hanh_dong_co_quan", "khung_hanh_dong_co_quan", frozenset({"hanh_dong_co_quan"})),
    ("quy_tac_ngoai_le", "khung_ngoai_le", frozenset({"ngoai_le"})),
    ("quy_tac_nguong_dinh_luong", "khung_nguong_dinh_luong", frozenset({"threshold", "nguong_so_luong"})),
    ("quy_tac_ket_qua_phap_ly", "khung_ket_qua_phap_ly", frozenset({"ket_qua_phap_ly", "legal_effect"})),
    (
        "quy_tac_dieu_kien",
        "khung_dieu_kien",
        frozenset({"condition", "dieu_kien", "quy_pham_dieu_kien", "dieu_kien_ap_dung"}),
    ),
    ("quy_tac_quyen", "khung_quyen", frozenset({"quy_pham_quyen", "quyen"})),
    (
        "quy_tac_thu_tuc",
        "khung_thu_tuc",
        frozenset({"thu_tuc", "quy_pham_thu_tuc"}),
    ),
]


def _norm_article(a) -> str:
    if pd.isna(a) or str(a).strip() in ("", "nan"):
        return ""
    return str(a).strip()


def _article_from_ref(s) -> str:
    if pd.isna(s):
        return ""
    m = re.search(r"[Đđ]iều\s+(\d+[a-z]?)", str(s), flags=re.I)
    return m.group(1) if m else ""


def _article_key(doc_code, article, ref) -> str:
    art = _norm_article(article) or _article_from_ref(ref)
    if not art:
        art = "UNKNOWN"
    dc = str(doc_code) if pd.notna(doc_code) else ""
    return f"{dc}|D{art}"


def _parse_merged_rule_ids(notes: str) -> int:
    if pd.isna(notes):
        return 0
    s = str(notes)
    if "merged_rule_ids=" not in s:
        return 0
    part = s.split("merged_rule_ids=", 1)[-1].split(";", 1)[0].strip()
    return len([x for x in part.split("|") if x.startswith("RULE_")])


def _df_to_md(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except Exception:
        return "```\n" + df.to_string(index=False) + "\n```"


def main() -> None:
    units = pd.read_excel(ROOT / "data/interim/law_parsing/legal_units_review.xlsx")
    cands = pd.read_excel(ROOT / "data/interim/law_parsing/candidate_normative_sentences.xlsx")
    frames = pd.read_excel(ROOT / "data/interim/law_parsing/legal_frames_review.xlsx")
    rules = pd.read_excel(ROOT / "data/processed/rulebase/rulebase_seed.xlsx")

    units = units.copy()
    units["_article"] = units.apply(
        lambda r: _norm_article(r.get("article")) or _article_from_ref(r.get("unit_ref_full")), axis=1
    )
    units.loc[units["_article"] == "", "_article"] = np.nan
    units["_article"] = units["_article"].fillna(units["unit_ref_full"].map(_article_from_ref))
    units["_article"] = units["_article"].fillna("UNKNOWN")
    units["article_key"] = units.apply(lambda r: _article_key(r.get("doc_code"), r["_article"], ""), axis=1)

    ic = units["is_candidate_rule_sentence"]
    if ic.dtype == object:
        units["_is_cand_unit"] = ic.astype(str).str.lower().isin(("true", "1", "yes", "co"))
    elif ic.dtype == bool:
        units["_is_cand_unit"] = ic.fillna(False)
    else:
        units["_is_cand_unit"] = ic.fillna(False).astype(bool)

    unit_to_article = units.set_index("unit_id")["article_key"].to_dict()

    cands = cands.copy()
    cands["cand_type"] = (
        cands["candidate_rule_type"].fillna(cands.get("candidate_type", "")).astype(str).str.strip().str.lower()
    )
    cands["article_key"] = cands["unit_id"].map(unit_to_article)
    miss = cands["article_key"].isna()
    cands.loc[miss, "article_key"] = cands.loc[miss].apply(
        lambda r: _article_key(r.get("doc_code"), "", r.get("unit_ref_full")), axis=1
    )

    frames = frames.copy()
    frames["article_key"] = frames["source_unit_id"].map(unit_to_article)
    missf = frames["article_key"].isna()
    frames.loc[missf, "article_key"] = frames.loc[missf].apply(
        lambda r: _article_key(r.get("doc_code"), "", r.get("unit_ref_full")), axis=1
    )

    rules = rules.copy()
    rules["article_key"] = rules["source_unit_id"].map(unit_to_article)
    missr = rules["article_key"].isna()
    rules.loc[missr, "article_key"] = rules.loc[missr].apply(
        lambda r: _article_key(r.get("doc_code"), "", r.get("source_ref_full")), axis=1
    )

    rows = []
    all_keys = (
        set(units["article_key"])
        | set(cands["article_key"])
        | set(frames["article_key"])
        | set(rules["article_key"])
    )
    for key in sorted(all_keys):
        su = units[units.article_key == key]
        sc = cands[cands.article_key == key]
        sf = frames[frames.article_key == key]
        sr = rules[rules.article_key == key]
        nu = len(su)
        nuc = int(su["_is_cand_unit"].sum()) if nu else 0
        nc = sc["candidate_id"].nunique() if len(sc) else 0
        nf = sf["frame_id"].nunique() if len(sf) else 0
        nfr = len(sf)
        nrule = sr["rule_id"].nunique() if len(sr) else 0
        if nu == 0 and nc == 0 and nf == 0 and nrule == 0:
            continue
        if nu == 0 or (nuc == 0 and nc == 0):
            st = "khong_co_noi_dung_suy_luan_ro"
        elif nc == 0:
            st = "mat_o_candidate"
        elif nf == 0:
            st = "mat_o_frame"
        elif nrule == 0:
            st = "mat_o_rule"
        elif nuc >= 4 and nrule <= max(1, nuc // 4):
            st = "co_nhung_it"
        elif nf >= 3 and nrule == 1 and nc >= 2:
            st = "co_nhung_it"
        else:
            st = "day_du_tuong_doi"
        rows.append(
            dict(
                article_key=key,
                so_unit=nu,
                so_unit_candidate=nuc,
                so_candidate=nc,
                so_frame_unique=nf,
                so_frame_rows=nfr,
                so_rule=nrule,
                coverage_status=st,
            )
        )

    cov = pd.DataFrame(rows)
    pre_dedup_est = 524
    post_dedup = len(rules)
    merged_extra = int(rules["notes"].map(_parse_merged_rule_ids).sum())
    n_dedup_rows = int(rules["notes"].astype(str).str.contains("dedup_theo_noi_dung", na=False).sum())

    type_rows = []
    ct_series = cands["cand_type"]
    for rt, ft, tags in TYPE_DEFS:
        sc = int(ct_series.isin(tags).sum())
        sf = int((frames["frame_type"].astype(str) == ft).sum())
        srule = int((rules["rule_type"] == rt).sum())
        loss_st = ""
        if sc == 0:
            loss_st = "it_tu_candidate"
        elif sf == 0:
            loss_st = "mat_frame_cho_loai"
        elif srule == 0:
            loss_st = "mat_rule_cho_loai"
        elif sc > sf + 2:
            loss_st = "candidate_nhieu_hon_frame"
        elif sf > srule + 3:
            loss_st = "frame_nhieu_hon_rule_co_the_builder_hoac_dedup"
        else:
            loss_st = "on_dinh_tuong_doi"
        type_rows.append(
            dict(
                loai_quy_tac=rt,
                frame_type=ft,
                so_candidate=sc,
                so_frame=sf,
                so_rule_sau_dedup=srule,
                loss_stage=loss_st,
            )
        )
    tdf = pd.DataFrame(type_rows)
    ratio = post_dedup / max(1, pre_dedup_est)
    tdf["so_rule_truoc_uoc"] = (tdf["so_rule_sau_dedup"] / ratio).round().astype(int)
    tdf["mat_do_dedup_uoc"] = tdf["so_rule_truoc_uoc"] - tdf["so_rule_sau_dedup"]
    tdf["ty_le_mat_uoc"] = (1 - ratio)
    tdf["nhan_xet"] = tdf["loss_stage"]

    n_cand = cands["candidate_id"].nunique()
    n_frame = frames["frame_id"].nunique()
    n_rule = rules["rule_id"].nunique()

    articles_unit = int((cov["so_unit"] > 0).sum())
    articles_uc = int((cov["so_unit_candidate"] > 0).sum())
    articles_c = int((cov["so_candidate"] > 0).sum())
    articles_f = int((cov["so_frame_unique"] > 0).sum())
    articles_r = int((cov["so_rule"] > 0).sum())

    sus = cov[(cov["so_unit_candidate"] >= 3) & (cov["so_rule"] <= 2)].sort_values(
        ["so_unit_candidate", "so_rule"], ascending=[False, True]
    )
    sus_display = sus.head(45)[
        ["article_key", "so_unit_candidate", "so_candidate", "so_frame_unique", "so_rule", "coverage_status"]
    ].copy()
    sus_display["ket_luan_ngan"] = sus_display["coverage_status"].map(
        {
            "mat_o_candidate": "rớt ở candidate",
            "mat_o_frame": "rớt ở frame",
            "mat_o_rule": "rớt ở rule",
            "co_nhung_it": "có nhưng ít rule / đáng nghi dedup hoặc fan-out yếu",
            "day_du_tuong_doi": "tương đối đủ",
            "khong_co_noi_dung_suy_luan_ro": "thiếu tín hiệu unit/candidate",
        }
    )

    # Dedup per article: rules kept that absorbed merges
    rules_dedup = rules[rules["notes"].astype(str).str.contains("dedup_theo_noi_dung", na=False)]
    ded_by_art = rules_dedup.groupby("article_key").size().rename("so_rule_co_merged_notes").reset_index()
    ded_by_art = ded_by_art.sort_values("so_rule_co_merged_notes", ascending=False).head(20)

    ft_summary = []
    for ft, grp in frames.groupby("frame_type"):
        fids = set(grp["frame_id"].unique())
        nr = len(rules[rules["frame_id"].isin(fids)])
        nfu = grp["frame_id"].nunique()
        ft_summary.append(
            {
                "frame_type": ft,
                "frame_rows": len(grp),
                "frame_id_nunique": nfu,
                "rules": nr,
                "rules_per_frame_id": round(nr / max(1, nfu), 3),
            }
        )
    ft_df = pd.DataFrame(ft_summary).sort_values("rules_per_frame_id")

    unmatched_cand = set(ct_series.unique()) - set().union(*[tags for _, _, tags in TYPE_DEFS])
    unmatched_cand.discard("")
    unmatched_cand.discard("nan")

    out_path = ROOT / "data/interim/law_parsing/audit_rulebase_coverage_report.md"
    lines: list[str] = []
    lines.append("# Audit coverage rulebase (tự động)\n")
    lines.append("\n## 1. TÓM TẮT TỔNG QUAN\n")
    lines.append(f"- **article_key** (doc_code|Điều) có mặt ở ít nhất một tầng: **{len(cov)}**\n")
    lines.append(
        f"- Article có unit: **{articles_unit}**; có unit_candidate: **{articles_uc}**; có candidate: **{articles_c}**; có frame (unique frame_id): **{articles_f}**; có rule: **{articles_r}**\n"
    )
    lines.append(
        f"- Dòng dữ liệu: candidates **{len(cands)}**; frame rows **{len(frames)}**; rules (sau refine) **{n_rule}**; candidate_id unique **{n_cand}**; frame_id unique **{n_frame}**\n"
    )
    lines.append(
        f"- Rule **trước dedup** (log build RuleBuilder): **{pre_dedup_est}**; **sau dedup/refine**: **{post_dedup}** (giảm **{pre_dedup_est - post_dedup}**, ~**{100 * (pre_dedup_est - post_dedup) / pre_dedup_est:.1f}%**).\n"
    )
    lines.append(
        f"- Dòng rule có `dedup_theo_noi_dung` trong `notes`: **{n_dedup_rows}**; ước chừng **{merged_extra}** rule_id được liệt kê trong `merged_rule_ids` (không phải tổng mất tuyệt đối).\n"
    )
    lines.append(f"- Fan-out bình quân: **{n_rule / max(1, n_frame):.2f}** rule / `frame_id`; **{n_rule / max(1, n_cand):.2f}** rule / candidate.\n")
    lines.append(
        f"- `candidate_rule_type` không nằm trong bảng map audit: **{sorted(unmatched_cand)}** (nên bổ sung map nếu cần so sánh tầng).\n"
    )

    lines.append("\n## 2. DANH SÁCH ARTICLE ĐÁNG NGHI\n")
    lines.append(_df_to_md(sus_display))

    lines.append("\n### Phân bố `coverage_status`\n")
    vc = cov["coverage_status"].value_counts().reset_index()
    vc.columns = ["coverage_status", "so_article"]
    lines.append(_df_to_md(vc))

    lines.append("\n### Article có nhiều dòng rule đã ghi nhận merge (dedup)\n")
    lines.append(_df_to_md(ded_by_art))

    lines.append("\n## 3. COVERAGE THEO LOẠI (candidate → frame → rule)\n")
    lines.append(_df_to_md(tdf))

    lines.append("\n## 4. PHÂN TÍCH DEDUP LOSS\n")
    lines.append(
        f"- Tổng: {pre_dedup_est} → {post_dedup}. Cột `mat_do_dedup_uoc` giả định **cùng tỷ lệ** theo loại (chỉ để đặt hàng: loại nào đóng góp nhiều rule trước dedup).\n"
    )
    lines.append(
        f"- **Không có file CSV riêng** cho rule trước/sau dedup; dấu vết: `merged_rule_ids` + log build **524**.\n"
    )
    ded_simple = tdf[["loai_quy_tac", "so_rule_sau_dedup", "so_rule_truoc_uoc", "mat_do_dedup_uoc"]].copy()
    lines.append(_df_to_md(ded_simple))

    lines.append("\n## 5. FAN-OUT THEO `frame_type`\n")
    lines.append(_df_to_md(ft_df))

    lines.append("\n## 6. KẾT LUẬN VÀ HƯỚNG SỬA (tóm tắt máy)\n")
    lines.append(
        "1. **Theo Điều**: tra `coverage_status` — `mat_o_candidate` / `mat_o_frame` / `co_nhung_it` cho biết nghẽn upstream; `co_nhung_it` với nhiều unit_candidate thường gợi ý **dedup quá rộng** hoặc **fan-out yếu**.\n"
    )
    lines.append(
        "2. **Theo loại**: bảng TYPE cho thấy chỗ nào **candidate > frame** (extract frame) hoặc **frame > rule** (rule_builder / dedup).\n"
    )
    lines.append(
        "3. **Dedup**: ~37% rule mất sau refine; các loại có nhiều rule trước đóng góp nhiều vào `merged_rule_ids` — xem lại **fingerprint** nếu cần phân tách điều kiện / thời hạn / ngoại lệ.\n"
    )
    lines.append(
        "4. **Ưu tiên sửa**: (a) map đủ `candidate_rule_type`; (b) giảm dedup hoặc thu hẹp fingerprint; (c) tăng fan-out trong `rule_builder` cho `frame_type` có `rules_per_frame_id` thấp.\n"
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
