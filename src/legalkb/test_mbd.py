"""Fault-injection checks of step 4 (first-order MBD) on the sample KB: the parser is bypassed and the case facts
are written by hand, one fault per case, so each check knows which diagnosis and action are right. Every case is
stored as a run (batch "test_mbd") with its MBD trace.

    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.test_mbd
"""

from __future__ import annotations

import shutil
import sys

from .compile import write_and_check
from .db import connect
from .questions import Question, answer
from .reason import Reasoner
from .sample_kb import PARAMETERS, SAMPLE_DB, SAMPLE_PL, build
from .trace import connect_runs, save_run
from .verify import verify

STATUS = Question("status", "toi", pred="thuoc_dien_bhxh_bat_buoc")
BASE = ["instance_of(toi, nguoi_lao_dong)", "instance_of(cong_ty, nguoi_su_dung_lao_dong)",
        "instance_of(hd1, hop_dong_lao_dong)", "lam_viec_theo_hop_dong(toi, cong_ty, hd1)"]
INDEFINITE = "attr(hd1, loai_hop_dong, khong_xac_dinh_thoi_han)"
PENSION = "dang_huong_luong_huu_hoac_tro_cap_hang_thang(toi)"

# name, question, facts, false facts, KB variant, expected action, expected fault mode[, norms dropped by step 2]
CASES = [
    ("normal", "Tôi làm việc cho công ty theo hợp đồng lao động không xác định thời hạn và không hưởng lương hưu. "
               "Tôi có thuộc diện bảo hiểm xã hội bắt buộc không?",
     BASE + [INDEFINITE], [PENSION], "ok", "answer", None),
    ("missing", "Tôi ký hợp đồng lao động với công ty. Tôi có thuộc diện bảo hiểm xã hội bắt buộc không?",
     BASE, [], "ok", "ask", "missing"),
    ("misinterp", "Tôi ký hợp đồng lao động xác định thời hạn 12 tháng với công ty. "
                  "Tôi có thuộc diện bảo hiểm xã hội bắt buộc không?",
     BASE + [INDEFINITE], [], "ok", "confirm", "misinterp"),
    ("unsupported", "Tôi làm việc cho công ty theo hợp đồng lao động không xác định thời hạn. "
                    "Tôi có thuộc diện bảo hiểm xã hội bắt buộc không?",
     BASE + [INDEFINITE, PENSION], [], "ok", "confirm", "unsupported"),
    ("omission", "Tôi đang hưởng lương hưu và vẫn làm việc cho công ty theo hợp đồng lao động không xác định thời "
                 "hạn. Tôi có thuộc diện bảo hiểm xã hội bắt buộc không?",
     BASE + [INDEFINITE], [], "ok", "confirm", "omission"),
    ("misencoded", "Tôi ký hợp đồng lao động xác định thời hạn 3 tháng với công ty và không hưởng lương hưu. "
                   "Tôi có thuộc diện bảo hiểm xã hội bắt buộc không?",
     BASE + ["attr(hd1, thoi_han, 3)"], [PENSION], "half_month", "warn", "misencoded"),
    ("retrieval", "Tôi đang hưởng lương hưu và vẫn làm việc cho công ty theo hợp đồng lao động không xác định thời "
                  "hạn. Tôi có thuộc diện bảo hiểm xã hội bắt buộc không?",
     BASE + [INDEFINITE, PENSION], [], "ok", "warn", "omitted", {"41/2024/QH15:D2.K7.a#2"}),
    ("no_proof", "Tôi làm việc cho công ty theo hợp đồng lao động không xác định thời hạn và không hưởng lương hưu. "
                 "Tôi có thuộc diện bảo hiểm xã hội bắt buộc không?",
     ["instance_of(toi, nguoi_su_dung_lao_dong)"] + BASE[1:] + [INDEFINITE], [PENSION], "ok", "confirm",
     "misinterp"),
]


def variant_half_month():
    """The sample KB with Điều 2.1.a encoded as "from half a month" (the source text says 1 month), so the rule
    still fires on a 3-month contract and the fault is in a rule the proof uses."""
    path = SAMPLE_DB.with_name("sample_bhxh_halfmonth.sqlite")
    path.unlink(missing_ok=True)
    shutil.copy(SAMPLE_DB, path)
    con = connect(path)
    con.execute("UPDATE norm_conditions SET value_num = 0.5 WHERE norm_id LIKE '%D2.K1.a#%' AND attr = 'thoi_han'")
    con.commit()
    pl = path.with_suffix(".pl")
    write_and_check(con, pl)
    return con, pl


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    build()
    kbs = {"ok": (connect(SAMPLE_DB), SAMPLE_PL), "half_month": variant_half_month()}
    reasoners = {k: Reasoner(pl) for k, (_, pl) in kbs.items()}
    runs = connect_runs()
    ok = True
    for name, question, facts, false_facts, kb, want_action, want_mode, *drop in CASES:
        con, pl = kbs[kb]
        part = answer(STATUS, PARAMETERS + facts, reasoners[kb], con, false_facts, drop=drop[0] if drop else set())
        part.update(question=question, facts=facts, false_facts=false_facts, parsed=STATUS.__dict__, seconds=0)
        mbd = verify(question, facts, [part], con)
        run = save_run(runs, time="test", question=question, kb_program=str(pl), kb_database="", parser_model="(hand)",
                       parser_output=None, facts=facts, false_facts=false_facts, parameters=PARAMETERS,
                       parse_seconds=0, parts=[part], batch="test_mbd", item_id=name, gold=want_action, mbd=mbd)
        modes = {f.split("(")[0] for d in mbd["diagnoses"] for f in d}
        good = mbd["action"] == want_action and (want_mode is None or want_mode in modes)
        ok &= good
        print(f"{'PASS' if good else 'FAIL'} {name:12s} verdict {part['verdict']:8s} action {mbd['action']:10s} "
              f"(want {want_action}) diagnoses {mbd['diagnoses']}  run {run}")
    for r in reasoners.values():
        r.close()
    print("\nall passed" if ok else "\nSOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
