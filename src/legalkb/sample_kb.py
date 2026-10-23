"""A small hand-encoded KB (Luật BHXH 41/2024: Điều 2.1.a, 2.1.l, 2.7.a, 33.1.a) for testing the reasoner and the
parser independently of extraction quality. The norms are written in the extraction answer format and go through
the same store / link / compile path as the extracted KB; unit texts are copied from the main database.

    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.sample_kb      # builds data/legalkb/sample_bhxh.{sqlite,pl}
"""

from __future__ import annotations

from .compile import write_and_check
from .db import DB_FILE, connect
from .extract import store
from .normalize import link_references

SAMPLE_DB = DB_FILE.with_name("sample_bhxh.sqlite")
SAMPLE_PL = DB_FILE.with_name("sample_bhxh.pl")
LAW = "41/2024/QH15"
UNITS = [f"{LAW}:D2.K1", f"{LAW}:D2.K1.a", f"{LAW}:D2.K1.l", f"{LAW}:D2.K7", f"{LAW}:D2.K7.a", f"{LAW}:D33.K1",
         f"{LAW}:D33.K1.a"]


def _c(kind, pred=None, args=(), negated=False, attr=None, of=None, op=None, num=None, text=None, unit=None,
       vattr=None, vof=None, group=0, option=0):
    return {"kind": kind, "alt_group": group, "alt_option": option, "pred": pred, "args": list(args),
            "negated": negated, "attr": attr, "of": of, "op": op, "value_number": num, "value_text": text,
            "unit": unit, "value_attr": vattr, "value_of": vof}


def _norm(unit, modality, variables, subject, conditions, action=None, conclusion=None, formulas=(), other_refs=(),
          quote=""):
    return {"unit_id": unit, "modality": modality, "variables": [{"name": v, "type": t} for v, t in variables],
            "subject": subject, "bearer": None, "beneficiary": None, "conditions": conditions,
            "action": action, "conclusion": conclusion, "formulas": list(formulas), "deadline": None,
            "sanction": None, "exception_refs": [], "other_refs": list(other_refs), "valid_from": None,
            "valid_to": None, "validity_note": "", "quote": quote}


EMPLOYMENT = [("P", "nguoi_lao_dong"), ("E", "nguoi_su_dung_lao_dong"), ("H", "hop_dong_lao_dong")]
IN_SCOPE = {"pred": "thuoc_dien_bhxh_bat_buoc", "args": ["P"], "negated": False}

NORMS = [
    # 2.1.a: hợp đồng lao động không xác định thời hạn, hoặc xác định thời hạn từ đủ 01 tháng trở lên
    _norm(f"{LAW}:D2.K1.a", "consequence", EMPLOYMENT, "P", [
        _c("atom", "lam_viec_theo_hop_dong", ["P", "E", "H"]),
        _c("compare", attr="loai_hop_dong", of="H", op="=", text="khong_xac_dinh_thoi_han", group=1, option=1),
        _c("compare", attr="thoi_han", of="H", op=">=", num=1, unit="tháng", group=1, option=2),
    ], conclusion=IN_SCOPE, quote="Người làm việc theo hợp đồng lao động không xác định thời hạn, hợp đồng lao "
                                  "động xác định thời hạn từ đủ 01 tháng trở lên"),
    # 2.1.l: đối tượng tại điểm a làm việc không trọn thời gian, tiền lương >= tiền lương làm căn cứ đóng thấp nhất
    _norm(f"{LAW}:D2.K1.l", "consequence", EMPLOYMENT, "P", [
        _c("atom", "lam_viec_theo_hop_dong", ["P", "E", "H"]),
        _c("atom", "lam_viec_khong_tron_thoi_gian", ["P"]),
        _c("compare", attr="tien_luong", of="P", op=">=", num=1, vattr="tien_luong_can_cu_dong_thap_nhat",
           vof="tham_so"),
    ], conclusion=IN_SCOPE, quote="làm việc không trọn thời gian, có tiền lương trong tháng bằng hoặc cao hơn "
                                  "tiền lương làm căn cứ đóng bảo hiểm xã hội bắt buộc thấp nhất"),
    # 2.7.a: người đang hưởng lương hưu, trợ cấp BHXH, trợ cấp hằng tháng không thuộc đối tượng (ngoại lệ của khoản 1)
    _norm(f"{LAW}:D2.K7.a", "consequence", [("P", "nguoi_lao_dong")], "P", [
        _c("atom", "dang_huong_luong_huu_hoac_tro_cap_hang_thang", ["P"]),
    ], conclusion={**IN_SCOPE, "negated": True}, other_refs=["ngoai_le_cua: khoản 1 Điều này"],
        quote="Người đang hưởng lương hưu, trợ cấp bảo hiểm xã hội, trợ cấp hằng tháng"),
    # 33.1.a: người lao động thuộc diện đóng 8% tiền lương vào quỹ hưu trí và tử tuất
    _norm(f"{LAW}:D33.K1.a", "obligation", [("P", "nguoi_lao_dong")], "P", [
        _c("atom", "thuoc_dien_bhxh_bat_buoc", ["P"]),
    ], action={"pred": "dong_bhxh", "args": ["P", "quy_huu_tri_tu_tuat"]},
        formulas=[{"target_attr": "so_tien_dong_hang_thang", "of": "P", "expression": "0.08 * tien_luong",
                   "unit": "đồng"}],
        quote="Mức đóng hằng tháng bằng 8% tiền lương làm căn cứ đóng bảo hiểm xã hội vào quỹ hưu trí và tử tuất"),
]

# legal parameters are KB facts, not case facts (illustrative value)
PARAMETERS = ["attr(tham_so, tien_luong_can_cu_dong_thap_nhat, 4960000)"]

TYPES = [("nguoi_lao_dong", "ca_nhan"), ("nguoi_su_dung_lao_dong", None), ("hop_dong_lao_dong", "giay_to"),
         ("ca_nhan", None), ("giay_to", None)]


def build() -> dict:
    src = connect()
    SAMPLE_DB.unlink(missing_ok=True)
    con = connect(SAMPLE_DB)
    cols = "doc_id, number, title, doc_type, issuer, rank, domain, issued, effective_from, effective_to, source_file"
    con.execute(f"INSERT INTO documents ({cols}) VALUES ({','.join('?' * 11)})",
                src.execute(f"SELECT {cols} FROM documents WHERE number=?", (LAW,)).fetchone())
    ucols = "unit_id, doc_number, chapter, article, clause, point, parent_id, title, text"
    for u in UNITS:
        con.execute(f"INSERT INTO units ({ucols}) VALUES ({','.join('?' * 9)})",
                    src.execute(f"SELECT {ucols} FROM units WHERE unit_id=?", (u,)).fetchone())
    for name, parent in TYPES:
        con.execute("INSERT INTO entity_types VALUES (?,?,?,?,?)", (name, parent, "", "labor", "vocab"))
    out = {"entity_types": [], "predicates": [], "attributes": [], "norms": NORMS}
    store(con, out, set(UNITS), "labor")
    link_references(con)
    con.commit()
    from .templates import build as build_templates

    build_templates(con)  # sentences for the MBD observations (cached)
    return write_and_check(con, SAMPLE_PL)


if __name__ == "__main__":
    import json

    print(json.dumps(build(), ensure_ascii=False, indent=1))
