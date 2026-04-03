from __future__ import annotations

from verification.engine import NeSyEngine


def test_answer_verification_detects_inconsistency():
    eng = NeSyEngine()
    rec = eng.verify_answer(
        answer_text="Không phải đăng ký.",
        conclusion="obligation(cong_ty, dang_ky, thay_doi)",
        symbolic_ok=False,
    )
    assert rec.mode == "answer_verification"
    assert rec.final_decision in ("ACCEPT", "REJECT", "REPAIR")
