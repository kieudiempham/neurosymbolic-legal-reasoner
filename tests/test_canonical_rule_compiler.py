import json
from pathlib import Path

from law_side.rulebase_reasoning_core import (
    build_reasoning_core_package_from_canonical,
    load_canonical_jsonl,
)


def test_build_reasoning_core_from_canonical(tmp_path: Path) -> None:
    canonical_data = [
        {
            "rule_id": "ENT_001",
            "domain": "enterprise",
            "layer": "statute",
            "rulebase_id": "enterprise_67_vbhn-vpqh",
            "source_doc": "DOC_LUAT_DOANH_NGHIEP_67",
            "source_article": "10",
            "source_clause": "1",
            "source_point": None,
            "source_ref": "Luật DN, Điều 10, Khoản 1",
            "source_ref_full": "Luật Doanh Nghiệp 67/VBHN-VPQH, Điều 10 Khoản 1",
            "surface_text": "Doanh nghiệp phải đăng ký thay đổi nội dung đăng ký trong 15 ngày",
            "logic_form": "obligation",
            "canonical_head": {"predicate": "dang_ky_thay_doi", "args": ["X"]},
            "canonical_body": [
                {"predicate": "la_doanh_nghiep", "args": ["X"]},
                {"predicate": "co_chang_doi_noi_dung", "args": ["X"]},
            ],
            "doc_type": "law",
            "doc_code": "67/VBHN-VPQH",
            "issuing_body": "Văn phòng Quốc hội",
        }
    ]
    path = tmp_path / "canonical_rules.jsonl"
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in canonical_data), encoding="utf-8")

    loaded = load_canonical_jsonl(path)
    assert len(loaded) == 1
    assert loaded[0]["rule_id"] == "ENT_001"

    pkg = build_reasoning_core_package_from_canonical(
        canonical_rules=loaded,
        source_path=path,
    )
    assert pkg["core_rule_count"] == 1
    rule = pkg["rules_reasoning_core"][0]
    assert rule["rule_id"] == "ENT_001"
    assert rule["metadata"]["provenance"]["domain"] == "enterprise"
    assert rule["metadata"]["provenance"]["source_ref"] == "Luật DN, Điều 10, Khoản 1"
    assert rule["selected_for_reasoning"] is True
