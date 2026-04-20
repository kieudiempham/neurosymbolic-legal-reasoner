from __future__ import annotations

from question_side.condition_lexicon import entry_by_predicate
from question_side.condition_normalizer import _candidate_family


def test_family_exception_from_entry_signals() -> None:
    entry = entry_by_predicate("truong_hop_ngoai_le")
    assert entry is not None
    assert _candidate_family(entry) == "exception"


def test_family_deadline_from_entry_signals() -> None:
    entry = entry_by_predicate("qua_thoi_han")
    assert entry is not None
    assert _candidate_family(entry) == "deadline"


def test_family_tax_deductibility_style_maps_to_eligibility() -> None:
    synthetic = {
        "canonical_predicate": "dieu_kien_khau_tru_thue_gtgt",
        "domain": "tax",
        "trigger_patterns": ["duoc khau tru thue", "khau tru thue gtgt"],
        "synonyms": ["du dieu kien khau tru"],
    }
    assert _candidate_family(synthetic) == "eligibility"


def test_family_obligation_trigger_style_and_legal_effect_style() -> None:
    entry_obligation = entry_by_predicate("phat_sinh_nghia_vu")
    entry_effect = entry_by_predicate("xu_phat_hanh_chinh")
    assert entry_obligation is not None
    assert entry_effect is not None
    assert _candidate_family(entry_obligation) == "obligation_trigger"
    assert _candidate_family(entry_effect) == "legal_effect_trigger"
