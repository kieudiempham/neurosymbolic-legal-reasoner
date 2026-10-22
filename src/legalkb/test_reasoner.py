"""Reasoner checks on the hand-encoded sample KB (legalkb.sample_kb).

    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.test_reasoner
"""

from __future__ import annotations

import sys

from .reason import Reasoner, render
from .sample_kb import SAMPLE_PL, build

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
    check("binh: no obligation (exception 2.7.a)", not res["binh"]["obl"])
    check("chi: certain through Điều 2.1.l", any(a["status"] == "certain" for a in res["chi"]["obl"]))
    check("chi: 480,000 a month", any("480000" in a["goal"] for a in res["chi"]["amount"]))
    dung = res["dung"]["obl"]
    check("dung: not certain", not any(a["status"] == "certain" for a in dung))
    check("dung: conditional on the contract term (Điều 2.1.a)",
          any(a["status"] == "conditional" and any("thoi_han" in m for m in a["missing"]) for a in dung))
    r.close()
    print("\nall passed" if ok else "\nSOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
