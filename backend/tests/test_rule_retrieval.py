from __future__ import annotations

from app.config import settings
from question_side.question_normalizer import build_layer2
from question_side.question_parser import parse_question_layer1
from retrieval.rule_retriever import retrieve_rules
from retrieval.rulebase_loader import configure_rulebase_path, get_rulebase_index


def setup_module() -> None:
    configure_rulebase_path(settings.resolved_rulebase_core())


def test_rulebase_non_empty():
    idx = get_rulebase_index()
    assert len(idx.rules) > 0


def test_retrieve_returns_ranked_list():
    q = "Cổ đông có thể gửi phiếu lấy ý kiến đã trả lời đến công ty bằng thư điện tử không?"
    l1 = parse_question_layer1(q)
    l2 = build_layer2(l1, user_facts=[])
    ranked = retrieve_rules(layer1=l1, layer2=l2, top_k=5)
    assert len(ranked) >= 1
    assert ranked[0][1] >= 0
