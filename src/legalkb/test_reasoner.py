"""Reasoner checks on the hand-encoded sample KB (legalkb.sample_kb), and on variants of it with a norm added
that concludes the opposite of Điều 2.1 (step 3: conflicts resolved by priority), and on a cyclic program.
The added norms and documents are test fixtures, not real law.

    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.test_reasoner
"""

from __future__ import annotations

import shutil
import sys

from .runtime import compile_sample as write_and_check
from .db import connect
from .extract import store
from .questions import Question, answer
from .reason import Reasoner, render
from .sample_kb import LAW, PARAMETERS, SAMPLE_DB, SAMPLE_PL, _c, _norm, build

EMPLOYER = ["instance_of(cty, nguoi_su_dung_lao_dong)", "attr(tham_so, tien_luong_can_cu_dong_thap_nhat, 4960000)"]


def worker(x, extra=()):
    return [f"instance_of({x}, nguoi_lao_dong)", f"instance_of(hd_{x}, hop_dong_lao_dong)",
            f"lam_viec_theo_hop_dong({x}, cty, hd_{x})", *extra]


CASES = {
    # An: indefinite-term contract, 10 million -> must contribute, 800,000 a month (unless receiving a pension)
    "an": worker("an", ["attr(hd_an, loai_hop_dong, khong_xac_dinh_thoi_han)", "attr(an, tien_luong, 10000000)"]),
    # Binh: as An, but receives a pension -> Điều 2.7.a defeats 2.1.a: no obligation
    "binh": worker("binh", ["attr(hd_binh, loai_hop_dong, khong_xac_dinh_thoi_han)", "attr(binh, tien_luong, 10000000)",
                            "dang_huong_luong_huu_hoac_tro_cap_hang_thang(binh)"]),
    # Chi: part-time, 6 million >= threshold, contract term not given -> certain through 2.1.l
    "chi": worker("chi", ["lam_viec_khong_tron_thoi_gian(chi)", "attr(chi, tien_luong, 6000000)"]),
    # Dung: part-time, 3 million < threshold, contract term not given -> only conditional through 2.1.a
    "dung": worker("dung", ["lam_viec_khong_tron_thoi_gian(dung)", "attr(dung, tien_luong, 3000000)"]),
}


STATUS = Question("status", "chi", pred="thuoc_dien_bhxh_bat_buoc")
PART_TIME = [*PARAMETERS, "instance_of(cty, nguoi_su_dung_lao_dong)", *worker("chi", [
    "lam_viec_khong_tron_thoi_gian(chi)", "attr(chi, tien_luong, 6000000)"])]
FOREIGN = "la_nguoi_nuoc_ngoai(chi)"
NOT_IN_SCOPE = {"pred": "thuoc_dien_bhxh_bat_buoc", "args": ["P"], "negated": True}
EMPLOYMENT = [("P", "nguoi_lao_dong"), ("E", "nguoi_su_dung_lao_dong"), ("H", "hop_dong_lao_dong")]
L_CONDITIONS = [_c("atom", "lam_viec_theo_hop_dong", ["P", "E", "H"]), _c("atom", "lam_viec_khong_tron_thoi_gian", ["P"]),
                _c("compare", attr="tien_luong", of="P", op=">=", num=1, vattr="tien_luong_can_cu_dong_thap_nhat",
                   vof="tham_so")]

# variant -> (document of the added norm: number, type, issuer, rank, issued), its variables and conditions
VARIANTS = {
    # a decree (lower legal force) says part-time workers are not in scope: the law prevails
    "superior": (("99/2026/NĐ-CP", "Nghị định", "Chính phủ", 3, "2026-01-01"), [("P", "nguoi_lao_dong")],
                 [_c("atom", "lam_viec_khong_tron_thoi_gian", ["P"])]),
    # a later law of the same body says the same: it prevails
    "posterior": (("99/2026/QH15", "Luật", "Quốc hội", 2, "2026-01-01"), [("P", "nguoi_lao_dong")],
                  [_c("atom", "lam_viec_khong_tron_thoi_gian", ["P"])]),
    # the same law, with the conditions of 2.1.l plus one more (foreign workers): the more specific norm prevails
    "specialis": (None, EMPLOYMENT, L_CONDITIONS + [_c("atom", "la_nguoi_nuoc_ngoai", ["P"])]),
    # the same law, conditions neither inside nor around those of 2.1.l: no principle decides
    "unresolved": (None, [("P", "nguoi_lao_dong")],
                   [_c("atom", "lam_viec_khong_tron_thoi_gian", ["P"]), _c("atom", "la_nguoi_nuoc_ngoai", ["P"])]),
}


def conflict_variant(name: str):
    doc, variables, conditions = VARIANTS[name]
    path = SAMPLE_DB.with_name(f"sample_bhxh_conflict_{name}.sqlite")
    path.unlink(missing_ok=True)
    shutil.copy(SAMPLE_DB, path)
    con = connect(path)
    number = doc[0] if doc else LAW
    if doc:
        con.execute("INSERT INTO documents (doc_id, number, title, doc_type, issuer, rank, domain, issued, "
                    "effective_from) VALUES (?,?,?,?,?,?,?,?,?)",
                    (number, number, "văn bản thử nghiệm", doc[1], doc[2], doc[3], "labor", doc[4], doc[4]))
    unit = f"{number}:D99.K1"
    con.execute("INSERT INTO units (unit_id, doc_number, article, clause, text) VALUES (?,?,?,?,?)",
                (unit, number, "99", "1", "(quy định thử nghiệm) người lao động làm việc không trọn thời gian "
                                          "không thuộc đối tượng tham gia bảo hiểm xã hội bắt buộc"))
    store(con, {"entity_types": [], "predicates": [], "attributes": [], "norms": [
        _norm(unit, "consequence", variables, "P", conditions, conclusion=NOT_IN_SCOPE)]}, {unit}, "labor")
    con.commit()
    pl = path.with_suffix(".pl")
    report = write_and_check(con, pl)
    return con, pl, report


def cyclic_program() -> Path:
    """p and q defined through each other (a dependency cycle), and q also from a fact."""
    path = SAMPLE_DB.with_name("cycle_test.pl")
    path.write_text(":- dynamic r/1, s/1.\np(X) :- q(X).\nq(X) :- p(X).\nq(X) :- r(X).\nq(X) :- s(X), p(X).\n",
                    encoding="utf-8")
    return path


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    build()
    r = Reasoner(SAMPLE_PL)
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name)
        ok &= bool(cond)

    res = {}
    for who, facts in CASES.items():
        res[who] = {
            "obl": r.query(EMPLOYER + facts, f"obligation(N, {who}, A)")["answers"],
            "amount": r.query(EMPLOYER + facts, f"computed(N, {who}, so_tien_dong_hang_thang, V)")["answers"],
        }
        print(f"\n=== {who}")
        for a in res[who]["obl"] + res[who]["amount"]:
            print(render(a))

    an = res["an"]
    check("an: certain obligation to contribute (Điều 33.1.a)",
          any(a["status"] == "certain" and "D33.K1.a" in a["goal"] for a in an["obl"]))
    check("an: 800,000 a month", any(a["status"] == "certain" and "800000" in a["goal"] for a in an["amount"]))
    check("an: pension exception presumed absent",
          any("dang_huong_luong_huu" in p for a in an["obl"] for p in a["presumed_absent"]))
    check("binh: no obligation (exception 2.7.a)", not any("41/2024" in a["goal"] for a in res["binh"]["obl"]))
    check("chi: certain through Điều 2.1.l", any(a["status"] == "certain" for a in res["chi"]["obl"]))
    check("chi: 480,000 a month", any("480000" in a["goal"] for a in res["chi"]["amount"]))
    dung = res["dung"]["obl"]
    check("dung: not certain", not any(a["status"] == "certain" for a in dung))
    check("dung: conditional on the contract term (Điều 2.1.a)",
          any(a["status"] == "conditional" and any("thoi_han" in m for m in a["missing"]) for a in dung))
    r.close()

    # ---- step 3: conflicts between norms resolved by priority (data: legal_force, priority_principles,
    # documents; result: norm_conflicts)
    print("\n=== conflicts")
    l_norm = f"{LAW}:D2.K1.l#1"
    for name, facts, want_verdict, want in (
            ("superior", PART_TIME, "yes", "lex_superior"),
            ("posterior", PART_TIME, "no", "lex_posterior"),
            ("specialis", PART_TIME + [FOREIGN], "no", "lex_specialis"),
            ("specialis", PART_TIME, "yes", "lex_specialis"),
            ("unresolved", PART_TIME + [FOREIGN], "yes", None)):
        con, pl, report = conflict_variant(name)
        rows = con.execute("SELECT norm_a, norm_b, winner, principle, detail FROM norm_conflicts").fetchall()
        rv = Reasoner(pl)
        part = answer(STATUS, facts, rv, con)
        rv.close()
        certain_both = any(a["status"] == "certain" for a in part["answers"]) and \
            any(a["status"] == "certain" for a in part["contrary"])
        print(f"  {name}: load ok {report.get('prolog_load_ok')}, norm_conflicts {rows}")
        print(f"    verdict {part['verdict']}, fired {[(c['winner'], c['principle'], c['status']) for c in part['conflicts']]}")
        tag = f"{name}{' + foreign' if FOREIGN in facts else ''}"
        check(f"{tag}: KB loads", report.get("prolog_load_ok"))
        check(f"{tag}: verdict {want_verdict}", part["verdict"] == want_verdict)
        if want:
            check(f"{tag}: pair with 2.1.l decided by {want}",
                  any(l_norm in (a, b) and p == want for a, b, w, p, _ in rows))
            if FOREIGN in facts or name != "specialis":
                check(f"{tag}: the deciding norm applies and is recorded",
                      any(c["principle"] == want for c in part["conflicts"]))
        else:
            check(f"{tag}: stored as unresolved", any(w is None for _, _, w, _, _ in rows))
            check(f"{tag}: both conclusions proved (a KB conflict for the diagnosis)", certain_both)
        con.close()

    # ---- termination on a dependency cycle (a goal met again in its own proof is cut)
    rc = Reasoner(cyclic_program())
    got = rc.query(["r(a)"], "p(a)")["answers"]
    check("cycle: p(a) proved through q(a) <- r(a), no loop", any(a["status"] == "certain" for a in got))
    got = rc.query([], "p(b)", max_missing=1)["answers"]
    check("cycle: p(b) only conditional on r(b) or s(b)", got and not any(a["status"] == "certain" for a in got))
    rc.close()
    print("\nall passed" if ok else "\nSOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())


def test_deadline_and_sanction(tmp_path, monkeypatch):
    """Real store -> compile -> retrieve -> Prolog, without a model/network."""
    from . import sample_kb
    db, pl = tmp_path / 'sample.sqlite', tmp_path / 'sample.pl'
    monkeypatch.setattr(sample_kb, 'SAMPLE_DB', db)
    monkeypatch.setattr(sample_kb, 'SAMPLE_PL', pl)
    sample_kb.build()
    con, reasoner = connect(db), Reasoner(pl)
    facts = ['instance_of(toi, nguoi_lao_dong)', 'nhan_thong_bao_mau(toi)', 'nhan_yeu_cau_mau(toi)',
             'vi_pham_mau(toi)']
    try:
        for pred, modality, amount, unit, event in [
            ('nop_ho_so_mau', 'obligation', '30', 'ngay', 'nhan_thong_bao_mau'),
            ('bo_sung_ho_so_mau', 'procedure', '5', 'ngay_lam_viec', 'nhan_yeu_cau_mau')]:
            got = answer(Question('deadline', 'toi', modality=modality, pred=pred), facts, reasoner, con)
            assert got['verdict'] == 'yes'
            certain = [a['goal'] for a in got['answers'] if a['status'] == 'certain']
            assert any(amount in x and unit in x and event in x for x in certain)
            blocked = answer(Question('deadline', 'toi', modality=modality, pred=pred),
                             facts, reasoner, con, drop=set(got['retrieved']))
            assert not blocked['answers']
        sanction = answer(Question('sanction', 'toi'), facts, reasoner, con)
        import re
        ranges = [re.search(r",phat_tien,([^,]+),([^,]+),dong\)", a['goal'].replace(' ', ''))
                  for a in sanction['answers'] if a['status'] == 'certain']
        assert any(m and (float(m[1]), float(m[2])) == (1000000, 2000000) for m in ranges)
        warning = answer(Question('sanction', 'toi'), ['instance_of(toi, nguoi_lao_dong)', 'vi_pham_nhe_mau(toi)'],
                         reasoner, con)
        assert any(a['status'] == 'certain' and 'canh_cao,none,none' in a['goal'].replace(' ', '')
                   for a in warning['answers'])
        absent = answer(Question('deadline', 'toi', modality='obligation', pred='nop_ho_so_mau'),
                        ['instance_of(toi, nguoi_lao_dong)'], reasoner, con)
        assert absent['verdict'] == 'unknown'
        assert any('nhan_thong_bao_mau' in m for a in absent['answers'] for m in a['missing'])
        no_deadline = answer(Question('deadline', 'an', modality='obligation', pred='dong_bhxh',
                                      args=['quy_huu_tri_tu_tuat']), EMPLOYER + CASES['an'], reasoner, con)
        assert not no_deadline['answers']
    finally:
        reasoner.close()
        con.close()
