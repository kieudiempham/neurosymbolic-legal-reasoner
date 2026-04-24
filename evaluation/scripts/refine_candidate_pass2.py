from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CAND_PATH = ROOT / "data/interim/law_parsing/candidate_normative_sentences.v2.xlsx"
UNITS_PATH = ROOT / "data/interim/law_parsing/legal_units_review.xlsx"


def norm(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def blank(s) -> bool:
    t = norm(s)
    return t == "" or t.lower() == "nan"


EXC_RE = re.compile(r"((?:trừ\s+trường\s+hợp|ngoại\s+trừ|trừ\s+khi|nếu\s+không|không\s+áp\s+dụng\s+đối\s+với|không\s+bao\s+gồm\s+trường\s+hợp)[^.;]{0,240})", re.I | re.U)
THR_RE = re.compile(
    r"((?:không\s+quá|ít\s+nhất|trở\s+lên|trên)\s+[^.;]{0,120}|"
    r"\btừ\s+\d{1,4}\s+đến\s+\d{1,4}\s+[^.;]{0,80}|"
    r"\b\d{1,3}\s*%\s*(?:vốn\s+điều\s+lệ)?[^.;]{0,80}|"
    r"\bít\s+nhất\s+\d{1,4}\s+[^.;]{0,80})",
    re.I | re.U,
)
EFF_RE = re.compile(
    r"\b(được\s+cấp[^.;]{0,170}|cấp\s+Giấy\s+chứng\s+nhận[^.;]{0,170}|bị\s+thu\s+hồi[^.;]{0,170}|"
    r"thu\s+hồi\s+Giấy\s+chứng\s+nhận[^.;]{0,170}|được\s+công\s+bố[^.;]{0,170}|"
    r"phải\s+đăng\s+ký\s+điều\s+chỉnh[^.;]{0,170}|có\s+hiệu\s+lực[^.;]{0,170}|"
    r"bị\s+chấm\s+dứt[^.;]{0,170}|bị\s+giải\s+thể[^.;]{0,170}|chuyển\s+đổi\s+thành[^.;]{0,170}|"
    r"chấm\s+dứt\s+hoạt\s+động[^.;]{0,170}|được\s+cập\s+nhật[^.;]{0,170}|được\s+ghi\s+nhận[^.;]{0,170})",
    re.I | re.U,
)
DOC_RE = re.compile(
    r"(hồ\s+sơ\s+bao\s+gồm[^.;]{0,260}|kèm\s+theo[^.;]{0,240}|"
    r"(?:gửi|nộp|lưu\s+giữ|thông\s+báo|công\s+bố)\s+[^.;]{0,60}?(?:hồ\s+sơ|tài\s+liệu|giấy\s+tờ|danh\s+sách|nghị\s+quyết|quyết\s+định|biên\s+bản)[^.;]{0,180})",
    re.I | re.U,
)
COND_RE = re.compile(r"((?:khi|nếu|trường\s+hợp|đối\s+với|sau\s+khi|trước\s+khi)[^.;]{0,180})", re.I | re.U)
DDL_RE = re.compile(r"((?:trong\s+thời\s+hạn|chậm\s+nhất|kể\s+từ\s+ngày|trong\s+vòng)[^.;]{0,180})", re.I | re.U)
AUTH_RE = re.compile(r"\b(cơ\s+quan\s+đăng\s+ký\s+kinh\s+doanh(?:\s+cấp\s+tỉnh)?|phòng\s+đăng\s+ký\s+kinh\s+doanh|ủy\s+ban\s+nhân\s+dân(?:\s+cấp\s+\w+)?|cơ\s+quan\s+nhà\s+nước\s+có\s+thẩm\s+quyền)\b", re.I | re.U)

OBJ_BAD = {
    "cầu của",
    "đông có",
    "gửi về",
    "hộ kinh",
    "là thành",
    "giấy tờ pháp",
    "quyết định",
    "nghĩa",
    "áp dụng",
    "đáp ứng",
    "nộp đủ",
    "cấp xã",
    "có ít",
    "loại đã",
}

OBJ_PATTERNS = [
    r"\b(Giấy\s+chứng\s+nhận\s+đăng\s+ký\s+doanh\s+nghiệp)\b",
    r"\b(nội\s+dung\s+đăng\s+ký\s+doanh\s+nghiệp)\b",
    r"\b(hồ\s+sơ\s+đăng\s+ký\s+hoạt\s+động\s+chi\s+nhánh)\b",
    r"\b(hồ\s+sơ\s+đăng\s+ký\s+doanh\s+nghiệp)\b",
    r"\b(yêu\s+cầu\s+cung\s+cấp\s+nguồn\s+lực)\b",
    r"\b(phần\s+vốn\s+góp)\b",
    r"\b(vốn\s+điều\s+lệ)\b",
    r"\b(cổ\s+đông\s+sáng\s+lập)\b",
    r"\b(Điều\s+lệ\s+công\s+ty)\b",
    r"\b(người\s+đại\s+diện\s+theo\s+pháp\s+luật)\b",
    r"\b(thông\s+tin\s+về\s+chủ\s+sở\s+hữu\s+hưởng\s+lợi)\b",
    r"\b(sổ\s+đăng\s+ký\s+cổ\s+đông)\b",
    r"\b(sổ\s+sách\s+kế\s+toán)\b",
]


def first_group(rx: re.Pattern[str], text: str) -> str | None:
    m = rx.search(norm(text))
    return norm(m.group(1)) if m else None


def recover_object(text: str, action_text: str) -> str | None:
    t = norm(text)
    for pat in OBJ_PATTERNS:
        m = re.search(pat, t, flags=re.I | re.U)
        if m:
            return norm(m.group(1))
    a = norm(action_text)
    if a:
        m = re.search(re.escape(a) + r"\s+([^.;]{5,120}?)(?=,|;|\.|$)", t, flags=re.I | re.U)
        if m:
            c = norm(re.sub(r"^(theo|trong|khi|nếu|đối\s+với)\s+", "", m.group(1), flags=re.I | re.U))
            if len(c) >= 5:
                return c
    return None


def append_note(old: str, tag: str) -> str:
    parts = [x.strip() for x in re.split(r"[;|,]+", norm(old)) if x.strip()]
    if tag not in parts:
        parts.append(tag)
    return "; ".join(parts)


def clean_actor_action_object(df: pd.DataFrame) -> None:
    for i in df.index:
        actor = norm(df.at[i, "actor_text"])
        action = norm(df.at[i, "action_text"])
        obj = norm(df.at[i, "object_text"])
        sent = norm(df.at[i, "sentence_text"])
        changed = False

        # actor cleanup
        actor = re.sub(r"\b(không|phải|được)$", "", actor, flags=re.I | re.U).strip()
        if "," in actor and len(actor) > 40:
            actor = actor.split(",", 1)[0].strip()

        # action cleanup
        if len(action) > 90:
            action = action.split(",", 1)[0].strip()
            changed = True
        if len(action.split()) <= 1:
            m = re.search(
                r"\b(đăng\s*ký(?:\s+điều\s+chỉnh)?|thông\s+báo(?:\s+thay\s+đổi)?|cấp\s+Giấy\s+chứng\s+nhận\s+đăng\s+ký\s+doanh\s+nghiệp|"
                r"thu\s+hồi\s+Giấy\s+chứng\s+nhận\s+đăng\s+ký\s+doanh\s+nghiệp|góp\s+đủ\s+vốn\s+điều\s+lệ|"
                r"quyết\s+định\s+giải\s+thể\s+công\s+ty|tạm\s+ngừng\s+kinh\s+doanh|lưu\s+giữ\s+tài\s+liệu\s+của\s+doanh\s+nghiệp)\b",
                sent,
                flags=re.I | re.U,
            )
            if m:
                action = norm(m.group(1))
                changed = True

        # object cleanup
        low_obj = obj.lower()
        if low_obj in OBJ_BAD or (len(obj) <= 10 and low_obj in {"quyết định", "nghĩa", "áp dụng", "đáp ứng"}):
            new_obj = recover_object(sent, action)
            if new_obj:
                obj = new_obj
                df.at[i, "notes"] = append_note(df.at[i, "notes"], "sua_object_text_tu_fragment_thanh_noun_phrase")
            else:
                obj = ""
                df.at[i, "notes"] = append_note(df.at[i, "notes"], "bo_object_text_fragment")
            changed = True

        if changed:
            df.at[i, "actor_text"] = actor
            df.at[i, "action_text"] = action
            df.at[i, "object_text"] = obj
            if action:
                df.at[i, "notes"] = append_note(df.at[i, "notes"], "sua_action_text_cho_ngan_gon")
            if actor:
                df.at[i, "notes"] = append_note(df.at[i, "notes"], "sua_actor_text_cat_sai")


def fill_slots(df: pd.DataFrame) -> None:
    for i in df.index:
        ctype = norm(df.at[i, "candidate_type"])
        sent = norm(df.at[i, "sentence_text"])
        notes = norm(df.at[i, "notes"])

        if blank(df.at[i, "condition_text"]) and COND_RE.search(sent):
            df.at[i, "condition_text"] = first_group(COND_RE, sent) or ""
        if blank(df.at[i, "deadline_text"]) and ctype == "thoi_han":
            df.at[i, "deadline_text"] = first_group(DDL_RE, sent) or ""
        if blank(df.at[i, "authority_text"]) and ctype == "hanh_dong_co_quan":
            m = AUTH_RE.search(sent)
            if m:
                df.at[i, "authority_text"] = norm(m.group(1))
        if blank(df.at[i, "document_text"]) and ctype in {"thanh_phan_ho_so", "thu_tuc"}:
            df.at[i, "document_text"] = first_group(DOC_RE, sent) or ""
        if blank(df.at[i, "exception_text"]) and (ctype == "ngoai_le" or EXC_RE.search(sent)):
            got = first_group(EXC_RE, sent)
            if got:
                df.at[i, "exception_text"] = got
                notes = append_note(notes, "bo_sung_ngoai_le_tu_legal_units")
        if blank(df.at[i, "threshold_text"]) and ctype == "nguong_so_luong":
            df.at[i, "threshold_text"] = first_group(THR_RE, sent) or ""
        if blank(df.at[i, "legal_effect_text"]) and (ctype == "ket_qua_phap_ly" or EFF_RE.search(sent)):
            got = first_group(EFF_RE, sent)
            if got:
                df.at[i, "legal_effect_text"] = got
                notes = append_note(notes, "bo_sung_legal_effect_tu_legal_units")

        # type-slot mismatch strict fixes
        if ctype == "ngoai_le" and blank(df.at[i, "exception_text"]):
            got = first_group(EXC_RE, sent)
            if got:
                df.at[i, "exception_text"] = got
            else:
                df.at[i, "should_extract_rule"] = "can_nhac"
        if ctype == "nguong_so_luong" and blank(df.at[i, "threshold_text"]):
            got = first_group(THR_RE, sent)
            if got:
                df.at[i, "threshold_text"] = got
            else:
                df.at[i, "should_extract_rule"] = "can_nhac"
        if ctype == "ket_qua_phap_ly" and blank(df.at[i, "legal_effect_text"]):
            got = first_group(EFF_RE, sent)
            if got:
                df.at[i, "legal_effect_text"] = got
            else:
                df.at[i, "should_extract_rule"] = "can_nhac"
        if ctype == "thanh_phan_ho_so" and blank(df.at[i, "document_text"]):
            got = first_group(DOC_RE, sent)
            if got:
                df.at[i, "document_text"] = got
            else:
                df.at[i, "should_extract_rule"] = "can_nhac"
        if ctype == "thoi_han" and blank(df.at[i, "deadline_text"]):
            got = first_group(DDL_RE, sent)
            if got:
                df.at[i, "deadline_text"] = got
            else:
                df.at[i, "should_extract_rule"] = "can_nhac"
        if ctype == "hanh_dong_co_quan" and blank(df.at[i, "authority_text"]):
            m = AUTH_RE.search(sent)
            if m:
                df.at[i, "authority_text"] = norm(m.group(1))
            else:
                df.at[i, "should_extract_rule"] = "can_nhac"

        df.at[i, "notes"] = notes


def make_candidate_from_unit(u: pd.Series, ctype: str, span: str, suffix: str, note: str) -> dict:
    uid = norm(u["unit_id"])
    cand_id = f"CAND_{uid}_{suffix}"
    row = {
        "candidate_id": cand_id,
        "unit_id": uid,
        "doc_id": norm(u.get("doc_id")),
        "doc_code": norm(u.get("doc_code")),
        "unit_ref_full": norm(u.get("unit_ref_full")),
        "source_ref": norm(u.get("source_ref")),
        "heading": norm(u.get("heading")),
        "parent_context": norm(u.get("parent_context")),
        "source_text": norm(u.get("text")),
        "sentence_text": span,
        "candidate_type": ctype,
        "candidate_subtype": "",
        "candidate_score": "cao",
        "trigger_patterns": "",
        "actor_text": "",
        "action_text": "",
        "object_text": "",
        "condition_text": first_group(COND_RE, span) or "",
        "deadline_text": first_group(DDL_RE, span) or "",
        "authority_text": (AUTH_RE.search(span).group(1) if AUTH_RE.search(span) else ""),
        "document_text": first_group(DOC_RE, span) or "",
        "exception_text": first_group(EXC_RE, span) or "",
        "threshold_text": first_group(THR_RE, span) or "",
        "legal_effect_text": first_group(EFF_RE, span) or "",
        "should_extract_rule": "co",
        "extraction_priority": "cao",
        "sentence_type": norm(u.get("unit_type")) or "clause",
        "normative_pattern": ctype,
        "subject_span": "",
        "action_span": "",
        "modality_span": "",
        "condition_span": first_group(COND_RE, span) or "",
        "time_span": first_group(DDL_RE, span) or "",
        "document_span": first_group(DOC_RE, span) or "",
        "authority_span": (AUTH_RE.search(span).group(1) if AUTH_RE.search(span) else ""),
        "candidate_rule_type": ctype,
        "confidence_manual": "medium",
        "ns_id": f"ns_{cand_id.lower()}"[:64],
        "notes": note,
    }
    return row


def add_missing_from_units(df: pd.DataFrame, units: pd.DataFrame) -> pd.DataFrame:
    existing = set(zip(df["unit_id"].astype(str), df["candidate_type"].astype(str)))
    units_in_cand = set(df["unit_id"].astype(str))
    new_rows: list[dict] = []
    target_types = ["thanh_phan_ho_so", "ngoai_le", "nguong_so_luong", "ket_qua_phap_ly"]

    for _, u in units.iterrows():
        text = norm(u.get("text"))
        if not text:
            continue
        uid = norm(u.get("unit_id"))

        # Controlled recall: only enrich units that already have at least one candidate.
        if uid not in units_in_cand:
            continue

        for ctype in target_types:
            if (uid, ctype) in existing:
                continue
            span = ""
            note = ""
            suffix = ""
            if ctype == "ngoai_le":
                # Must be explicit exception in unit text or marker.
                if not (str(u.get("has_exception_marker", "")).lower() in {"true", "1", "co", "có"} or EXC_RE.search(text)):
                    continue
                span = first_group(EXC_RE, text) or ""
                note = "bo_sung_candidate_thieu_cho_ngoai_le"
                suffix = "NGOAI_LE"
            elif ctype == "nguong_so_luong":
                if not (str(u.get("has_threshold_marker", "")).lower() in {"true", "1", "co", "có"} or THR_RE.search(text)):
                    continue
                span = first_group(THR_RE, text) or ""
                note = "bo_sung_candidate_thieu_cho_nguong"
                suffix = "NGUONG"
            elif ctype == "ket_qua_phap_ly":
                if not EFF_RE.search(text):
                    continue
                span = first_group(EFF_RE, text) or ""
                note = "bo_sung_candidate_thieu_cho_ket_qua"
                suffix = "KET_QUA"
            elif ctype == "thanh_phan_ho_so":
                if not (str(u.get("has_document_marker", "")).lower() in {"true", "1", "co", "có"} or DOC_RE.search(text)):
                    continue
                span = first_group(DOC_RE, text) or ""
                note = "bo_sung_candidate_thieu_cho_ho_so"
                suffix = "HO_SO"

            if not span:
                continue
            row = make_candidate_from_unit(u, ctype, span, suffix, note)
            if ctype == "ngoai_le" and blank(row["exception_text"]):
                continue
            if ctype == "nguong_so_luong" and blank(row["threshold_text"]):
                continue
            if ctype == "ket_qua_phap_ly" and blank(row["legal_effect_text"]):
                continue
            if ctype == "thanh_phan_ho_so" and blank(row["document_text"]):
                continue
            # Conservative quality for derived rows.
            row["candidate_score"] = "trung_binh"
            row["should_extract_rule"] = "can_nhac"
            new_rows.append(row)
            existing.add((uid, ctype))
            if len(new_rows) >= 160:
                break
        if len(new_rows) >= 160:
            break

    if not new_rows:
        return df
    new_df = pd.DataFrame(new_rows, columns=df.columns)
    return pd.concat([df, new_df], ignore_index=True)


def main() -> None:
    cand = pd.read_excel(CAND_PATH)
    units = pd.read_excel(UNITS_PATH)

    clean_actor_action_object(cand)
    fill_slots(cand)
    cand = add_missing_from_units(cand, units)

    # final normalization + conservative decision
    for i in cand.index:
        if blank(cand.at[i, "candidate_score"]):
            cand.at[i, "candidate_score"] = "trung_binh"
        if blank(cand.at[i, "should_extract_rule"]):
            cand.at[i, "should_extract_rule"] = "can_nhac"
        cand.at[i, "notes"] = norm(cand.at[i, "notes"])

    out_path = ROOT / "data/interim/law_parsing/candidate_normative_sentences.xlsx"
    cand.to_excel(out_path, index=False)

    print("refine_candidate_pass2 done")
    print("rows", len(cand))
    print(cand["candidate_type"].value_counts().to_string())
    for col in ["document_text", "exception_text", "threshold_text", "legal_effect_text", "condition_text", "object_text"]:
        b = cand[col].isna() | cand[col].astype(str).str.strip().isin(["", "nan"])
        print(col, "nonblank", int((~b).sum()), "blank", int(b.sum()))


if __name__ == "__main__":
    main()

