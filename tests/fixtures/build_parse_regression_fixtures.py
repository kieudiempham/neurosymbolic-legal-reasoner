"""Regenerate parse regression JSON from current heuristic + Layer2 (baseline lock-in).

Run: PYTHONPATH=src python tests/fixtures/build_parse_regression_fixtures.py

Edit CASES_CORE / CASES_AMBIGUITY / CASES_ROLES below, then regenerate.
"""

from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
import sys

if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from question_side.heuristic_layer1 import parse_question_layer1_heuristic
from question_side.question_normalizer import build_layer2


def _snapshot_expected(question_text: str) -> dict:
    l1 = parse_question_layer1_heuristic(question_text)
    l2 = build_layer2(l1, user_facts=[])
    cn = (l2.diagnostics or {}).get("condition_normalization") or {}
    atoms = " ".join(l2.condition_atoms or [])
    toks: list[str] = []
    for a in l2.condition_atoms or []:
        if "(" in a:
            toks.append(a.split("(", 1)[0])
    toks = list(dict.fromkeys(toks))[:8]
    return {
        "layer1": {
            "question_focus": l1.question_focus,
            "utterance_type": l1.utterance_type,
            "assertion_status": l1.assertion_status,
        },
        "layer2_min": {
            "subject_type_guess": l2.subject_type_guess,
            "subject_normalized": l2.subject_normalized,
            "goal_predicate": (l2.goal or {}).get("predicate"),
        },
        "condition_atoms_substrings": [],
        "canonical_snapshot": (cn.get("canonical_predicate") or "") if isinstance(cn, dict) else "",
        "allow_stated_condition": True,
        "condition_predicate_tokens": toks,
    }


def _case(qid: str, text: str, tags: list[str], notes: str = "") -> dict:
    return {"qid": qid, "question_text": text, "tags": tags, "notes": notes}


# --- Case definitions (questions + tags); expected{} filled by snapshot.
CASES_CORE = [
    _case(
        "core-obl-01",
        "Công ty có phải nộp báo cáo tài chính đúng hạn không?",
        ["obligation", "direct_question", "company", "asserted_ambiguous"],
    ),
    _case(
        "core-obl-02",
        "Doanh nghiệp có bắt buộc đăng ký thay đổi nội dung đăng ký doanh nghiệp không?",
        ["obligation", "company", "registration_change"],
    ),
    _case(
        "core-perm-01",
        "Cổ đông có được phép chuyển nhượng cổ phần cho nhà đầu tư nước ngoài không?",
        ["permission", "shareholder", "transfer"],
    ),
    _case(
        "core-proh-01",
        "Công ty có bị cấm cạnh tranh không lành mạnh với đối thủ không?",
        ["prohibition", "company"],
    ),
    _case(
        "core-dl-01",
        "Trong thời hạn 30 ngày kể từ khi nhận được thông báo, doanh nghiệp phải làm gì?",
        ["deadline", "company", "procedure"],
    ),
    _case(
        "core-proc-01",
        "Thủ tục đăng ký thay đổi người đại diện theo pháp luật gồm những bước nào?",
        ["procedure", "legal_rep"],
    ),
    _case(
        "core-lc-01",
        "Nếu vi phạm nghĩa vụ công bố thông tin, công ty chịu hậu quả pháp lý gì?",
        ["legal_consequence", "conditional", "company"],
    ),
    _case(
        "core-exc-01",
        "Trừ trường hợp được miễn, cổ đông có được quyền ưu tiên mua cổ phần không?",
        ["exception", "permission", "shareholder"],
    ),
    _case(
        "core-cond-01",
        "Nếu chưa đăng ký thay đổi thì có phải bổ sung hồ sơ không?",
        ["conditional", "obligation", "dossier"],
        notes="Heuristic: neu...thi → hypothetical_question.",
    ),
    _case(
        "core-cond-02",
        "Nếu thay đổi người đại diện theo pháp luật thì công ty phải nộp hồ sơ gì?",
        ["conditional", "obligation", "legal_rep"],
    ),
    _case(
        "core-hyp-01",
        "Giả sử công ty giải thể, cổ đông còn phải góp vốn thêm không?",
        ["hypothetical", "shareholder", "dissolution"],
    ),
    _case(
        "core-amb-01",
        "Công ty hay nhà đầu tư: ai phải chịu trách nhiệm về khoản vay?",
        ["ambiguous_question", "obligation"],
    ),
    _case(
        "core-name-01",
        "Thay đổi tên doanh nghiệp có cần thông báo không?",
        ["obligation", "registration_change", "name"],
    ),
    _case(
        "core-addr-01",
        "Thay đổi địa chỉ trụ sở chính có phải đăng ký không?",
        ["obligation", "address"],
    ),
    _case(
        "core-sector-01",
        "Khi thay đổi ngành nghề kinh doanh, hồ sơ gồm những gì?",
        ["procedure", "sector"],
    ),
    _case(
        "core-capital-01",
        "Tăng vốn điều lệ có cần nghị quyết của cổ đông không?",
        ["obligation", "capital", "shareholder"],
    ),
    _case(
        "core-member-01",
        "Thay đổi danh sách cổ đông phải thực hiện trong bao lâu?",
        ["deadline", "shareholder"],
    ),
    _case(
        "core-found-01",
        "Thành lập doanh nghiệp trách nhiệm hữu hạn cần điều kiện gì?",
        ["procedure", "incorporation"],
    ),
    _case(
        "core-reg-01",
        "Đăng ký doanh nghiệp lần đầu nộp ở đâu?",
        ["procedure", "registration"],
    ),
    _case(
        "core-suspend-01",
        "Tạm ngừng kinh doanh có phải thông báo không?",
        ["obligation", "suspension"],
    ),
    _case(
        "core-resume-01",
        "Tiếp tục kinh doanh trước thời hạn đã thông báo thì sao?",
        ["hypothetical", "resume"],
    ),
    _case(
        "core-diss-01",
        "Giải thể doanh nghiệp có phải họp đại hội đồng cổ đông không?",
        ["obligation", "dissolution", "governance"],
    ),
    _case(
        "core-branch-01",
        "Chấm dứt hoạt động chi nhánh cần quyết định nào?",
        ["procedure", "branch"],
    ),
    _case(
        "core-hdv-01",
        "Họp hội đồng thành viên có thể lấy ý kiến bằng văn bản không?",
        ["permission", "governance"],
    ),
    _case(
        "core-dossier-01",
        "Nộp hồ sơ đăng ký thay đổi quá thời hạn thì bị xử lý thế nào?",
        ["legal_consequence", "deadline"],
    ),
    _case(
        "core-except-01",
        "Ngoại lệ miễn giấy phép có áp dụng cho công ty con không?",
        ["exception", "applicability"],
    ),
    _case(
        "core-assert-01",
        "Chúng tôi đã đăng ký thay đổi tên, có cần nộp lại hồ sơ không?",
        ["asserted", "obligation"],
    ),
    _case(
        "core-vc-01",
        "Góp vốn khi thành lập công ty cổ phần có được bằng tài sản không?",
        ["permission", "incorporation", "capital"],
    ),
    _case(
        "core-share-01",
        "Đăng ký mua cổ phần chào bán ra công chúng thực hiện thế nào?",
        ["procedure", "shares"],
    ),
    _case(
        "core-proc-02",
        "Quy trình thông báo thay đổi nội dung đăng ký doanh nghiệp ra sao?",
        ["procedure", "registration_change"],
    ),
    _case(
        "core-time-01",
        "Trong thời hạn 10 ngày phải nộp hồ sơ bổ sung đúng không?",
        ["deadline", "dossier"],
    ),
    _case(
        "core-threshold-01",
        "Tỷ lệ biểu quyết tối thiểu là bao nhiêu phần trăm?",
        ["threshold"],
    ),
]

CASES_AMBIGUITY = [
    _case("amb-subj-01", "Họ có phải nộp phí không?", ["ambiguous_subject", "obligation"]),
    _case(
        "amb-cond-01",
        "Nếu điều kiện đó xảy ra thì có phải đăng ký không?",
        ["ambiguous_condition", "conditional"],
    ),
    _case(
        "amb-mod-01",
        "Công ty được hay không được tự ý phát hành cổ phiếu?",
        ["ambiguous_modality", "permission", "prohibition"],
    ),
    _case(
        "amb-goal-01",
        "Công ty đã thay đổi địa chỉ nhưng chưa rõ có bắt buộc thông báo hay chỉ nên thông báo?",
        ["ambiguous_goal", "assertion_mixed"],
    ),
    _case(
        "amb-time-01",
        "Trước hay sau ngày này phải nộp: quy định có mâu thuẫn không?",
        ["ambiguous_time", "deadline"],
    ),
    _case(
        "amb-exc-01",
        "Trừ khi được hưởng ưu đãi, doanh nghiệp có phải nộp thuế suất thông thường không?",
        ["exception", "obligation", "company"],
    ),
    _case(
        "amb-parse-02",
        "Hay là cổ đông sáng lập, hay là nhà đầu tư mới phải ký biên bản góp vốn?",
        ["ambiguous_question", "founder"],
    ),
    _case(
        "amb-cond-02",
        "Khi có tranh chấp nội bộ và đồng thời thay đổi đại diện pháp luật, ưu tiên thủ tục nào?",
        ["ambiguous_condition", "legal_rep"],
    ),
    _case(
        "amb-mod-02",
        "Người đại diện có thể hay không thể từ chức ngay lập tức?",
        ["ambiguous_modality", "legal_rep"],
    ),
    _case(
        "amb-goal-02",
        "Chúng tôi muốn biết có phải làm không hay chỉ nên làm?",
        ["ambiguous_goal", "obligation"],
    ),
    _case(
        "amb-subj-02",
        "Cổ đông và công ty cùng ký: ai chịu trách nhiệm trước pháp luật?",
        ["ambiguous_subject", "shareholder", "company"],
    ),
    _case(
        "amb-lex-01",
        "Thay đổi vốn và thay đổi tỷ lệ cổ phần cùng lúc: một hay hai thủ tục?",
        ["ambiguous_condition", "capital"],
    ),
    _case(
        "amb-lex-02",
        "Góp vốn mới và chuyển nhượng cổ phần: điều kiện khác nhau thế nào?",
        ["ambiguous_condition", "shareholder"],
    ),
    _case(
        "amb-assert-01",
        "Có thể coi là đã hoàn tất thủ tục chưa?",
        ["ambiguous", "assertion_status"],
    ),
    _case(
        "amb-proc-01",
        "Thủ tục A hay thủ tục B áp dụng khi vừa đổi tên vừa đổi địa chỉ?",
        ["ambiguous_question", "procedure"],
    ),
    _case(
        "amb-exc-02",
        "Ngoại lệ theo điều khoản đặc biệt có phủ nhận nghĩa vụ chung không?",
        ["exception", "obligation"],
    ),
    _case(
        "amb-hyp-01",
        "Giả sử không ai dự họp, quyết định có hiệu lực không?",
        ["hypothetical", "governance"],
    ),
    _case(
        "amb-dl-01",
        "Hạn 15 ngày hay 30 ngày: cái nào đúng với trường hợp của tôi?",
        ["ambiguous_time", "deadline"],
    ),
    _case(
        "amb-cond-03",
        "Nếu hồ sơ thiếu và đồng thời quá hạn thì xử phạt ra sao?",
        ["conditional", "legal_consequence"],
    ),
    _case(
        "amb-perm-01",
        "Có được quyền ưu tiên hay không nếu không công bố đúng hạn?",
        ["permission", "exception"],
    ),
    _case(
        "amb-company-01",
        "Doanh nghiệp có nghĩa vụ gì nếu không rõ chủ thể nào ký?",
        ["ambiguous_subject", "obligation"],
    ),
    _case(
        "amb-focus-01",
        "Có phải nộp hay chỉ cần lưu nội bộ?",
        ["ambiguous_goal", "dossier"],
    ),
]

CASES_ROLES = [
    _case(
        "role-co-01",
        "Công ty TNHH có phải công bố báo cáo tài chính hàng năm không?",
        ["company", "obligation"],
    ),
    _case(
        "role-sh-01",
        "Cổ đông sở hữu trên 51% có được bổ nhiệm giám đốc không?",
        ["shareholder", "permission"],
    ),
    _case(
        "role-lr-01",
        "Người đại diện theo pháp luật ký hợp đồng vượt quyền thì ai chịu trách nhiệm?",
        ["legal_representative", "legal_consequence"],
    ),
    _case(
        "role-founder-01",
        "Nhà sáng lập có phải góp đủ vốn cam kết trước khi cấp giấy chứng nhận không?",
        ["founder", "obligation"],
    ),
    _case(
        "role-hkd-01",
        "Hộ kinh doanh có phải lập sổ kế toán đầy đủ như công ty không?",
        ["business_household", "obligation"],
    ),
    _case(
        "role-auth-01",
        "Cơ quan đăng ký kinh doanh từ chối hồ sơ thì khiếu nại thế nào?",
        ["authority", "procedure"],
    ),
    _case(
        "role-sh-02",
        "Cổ đông phổ thông có quyền xem sổ biên bản họp không?",
        ["shareholder", "permission"],
    ),
    _case(
        "role-co-02",
        "Doanh nghiệp có thể tự quyết định phát hành trái phiếu không?",
        ["company", "permission"],
    ),
    _case(
        "role-lr-02",
        "Đại diện pháp luật có được đồng thời làm giám đốc điều hành không?",
        ["legal_representative", "permission"],
    ),
    _case(
        "role-founder-02",
        "Sáng lập viên rút vốn trước thời hạn có vi phạm không?",
        ["founder", "prohibition"],
    ),
    _case(
        "role-hkd-02",
        "Chủ hộ kinh doanh có phải chịu trách nhiệm vô hạn như doanh nghiệp tư nhân không?",
        ["business_household", "legal_consequence"],
    ),
    _case(
        "role-auth-02",
        "Sở Kế hoạch và Đầu tư có quyền yêu cầu bổ sung hồ sơ trong bao lâu?",
        ["authority", "deadline"],
    ),
    _case(
        "role-sh-03",
        "Cổ đông tối thiểu phải góp bao nhiêu phần trăm vốn điều lệ?",
        ["shareholder", "threshold"],
    ),
    _case(
        "role-co-03",
        "Công ty mẹ có phải chịu trách nhiệm về nợ của công ty con không?",
        ["company", "legal_consequence"],
    ),
    _case(
        "role-lr-03",
        "Người đại diện theo pháp luật có phải cư trú tại Việt Nam không?",
        ["legal_representative", "obligation"],
    ),
    _case(
        "role-founder-03",
        "Founder và cổ đông sáng lập: quyền biểu quyết khác nhau thế nào?",
        ["founder", "ambiguous_subject"],
    ),
    _case(
        "role-hkd-03",
        "Đăng ký hộ kinh doanh có cần vốn tối thiểu không?",
        ["business_household", "registration"],
    ),
    _case(
        "role-mixed-01",
        "Cổ đông là người đại diện pháp luật: có được tự quyết định chuyển nhượng cổ phần không?",
        ["shareholder", "legal_representative", "permission"],
    ),
]

ROOT = Path(__file__).resolve().parent


def main() -> None:
    def emit(rows: list[dict], name: str) -> None:
        out = []
        for row in rows:
            d = dict(row)
            d["expected"] = _snapshot_expected(str(d["question_text"]))
            out.append(d)
        (ROOT / name).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    emit(CASES_CORE, "parse_regression_questions_core.json")
    emit(CASES_AMBIGUITY, "parse_regression_questions_ambiguity.json")
    emit(CASES_ROLES, "parse_regression_questions_roles.json")
    n = len(CASES_CORE) + len(CASES_AMBIGUITY) + len(CASES_ROLES)
    print(f"wrote {n} cases (core={len(CASES_CORE)}, ambiguity={len(CASES_AMBIGUITY)}, roles={len(CASES_ROLES)})")


if __name__ == "__main__":
    main()
