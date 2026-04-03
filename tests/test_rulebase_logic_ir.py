"""Logic IR cleaning (rulebase_logic.json layer)."""

from __future__ import annotations

import pandas as pd

from law_side.rulebase_logic_ir import build_logic_ir_record
from law_side.rulebase_vocab_index import NormalizedVocab


def test_body_has_no_raw_text_dict_shape() -> None:
    row = pd.Series(
        {
            "rule_id": "R1",
            "rule_type": "quy_tac_ket_qua_phap_ly",
            "chu_the": "công ty",
            "he_qua_phap_ly": "được cấp giấy",
            "dieu_kien_ap_dung": None,
            "ngoai_le": None,
        }
    )
    norm = NormalizedVocab(
        subject_canonical="cong_ty",
        effect_canonical="duoc_cap_giay",
        predicate_canonical="cap_giay",
        normalization_status="full",
    )
    lr = build_logic_ir_record(row, norm)
    for b in lr.get("body") or []:
        assert "type" not in b or b.get("type") != "raw_text"
        assert "predicate" in b


def test_logic_record_has_rule_type_source_and_readiness() -> None:
    row = pd.Series({"rule_id": "R2", "rule_type": "quy_tac_nghia_vu"})
    norm = NormalizedVocab()
    lr = build_logic_ir_record(row, norm)
    assert lr.get("rule_type_source") == "quy_tac_nghia_vu"
    assert lr.get("logic_readiness") in (
        "reasoning_ready",
        "reasoning_partial",
        "reasoning_fallback",
    )
