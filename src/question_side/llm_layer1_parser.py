"""Layer-1 semantic slots via OpenAI-compatible JSON (structured, no free-form answer)."""

from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
from time import perf_counter
from urllib.parse import urlparse
from typing import Any

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - exercised in environments without optional LLM deps
    OpenAI = None  # type: ignore[assignment]
from pydantic import BaseModel, Field, field_validator

from schemas.question_parse import (
    AssertionStatus,
    Layer1Parse,
    QuestionFocus,
    UtteranceType,
)
from utils.semantic_families import CANONICAL_FAMILIES, normalize_family

logger = logging.getLogger(__name__)

_PROMPT_VERSION = "v8_layer1_family_aware_anti_null"

_SYSTEM = """Bạn là bộ phân tích ngữ nghĩa pháp lý (legal semantic parser) cho câu hỏi pháp luật tiếng Việt.
Bạn KHÔNG phải là bộ trích xuất slot đơn thuần. Nhiệm vụ:
  1. Suy ra dạng câu hỏi pháp lý (question family) trước.
  2. Áp dụng chính sách parse phù hợp cho dạng đó.
  3. Trả về parse best-effort có cấu trúc, kể cả khi câu hỏi mơ hồ.
Chỉ trả về MỘT object JSON duy nhất, không markdown, không giải thích.

═══ HỢP ĐỒNG BEST-EFFORT (BẮT BUỘC) ═══
• Layer1 LUÔN trả về parse best-effort — không trả object rỗng, không nil.
• Bộ tứ cốt lõi (question_focus, action_text, subject_text, condition_text) PHẢI được điền
  nếu câu hỏi còn BẤT KỲ tín hiệu ngôn ngữ khả dụng nào.
• A2 anti-null cho core slots:
    question_focus, action_text, subject_text, condition_text không được để rỗng khi còn tín hiệu có thể khôi phục.
    Empty string chỉ được phép khi thực sự KHÔNG còn recoverable signal trong câu hỏi cho slot đó.
• TUYỆT ĐỐI KHÔNG encode uncertainty bằng chuỗi rỗng cho slot cốt lõi.
  Sai: action_text=""  khi câu hỏi vẫn còn nội dung.
  Đúng: action_text="hau_qua_phap_ly" + action_confidence=0.72 + used_fallback_label="hau_qua_phap_ly".
• Uncertainty PHẢI được encode bằng:
    question_focus_confidence, action_confidence, subject_confidence ∈ [0.0, 1.0]
    used_fallback_label — nhãn fallback snake_case ngắn gọn khi không có verb tự nhiên từ câu hỏi.
    parse_rationale — giải thích ngắn quyết định parse khi mơ hồ (≤ 512 ký tự).
• Chỉ để trống slot khi HOÀN TOÀN không có tín hiệu ngôn ngữ nào trong câu hỏi cho slot đó.
• Thà điền nhãn fallback có nghĩa pháp lý còn hơn để trống.
• A3 best-effort over silence:
    Luôn chọn diễn giải pháp lý-ngữ nghĩa khả dĩ nhất (most plausible legal-semantic interpretation).
    Không yêu cầu chắc chắn tuyệt đối trước khi điền slot.
    Khi thiếu chắc chắn, vẫn điền slot theo best-effort + fallback label phù hợp + confidence/rationale.

═══ BƯỚC 1: SUY RA MACRO FAMILY (SOFT ROUTING) ═══
Không dùng taxonomy cứng. Family là soft routing hint để định hướng parse, không phải nhãn đóng.
Family là best-effort semantic routing hint, không phải nhãn phân loại tuyệt đối.
Nếu câu hỏi không fit sạch vào một family, dùng:
    macro_family = mixed_or_other
    question_family = other
Không ép gán family kém phù hợp khi case là hybrid hoặc giao thoa nhiều family.
Suy luận macro family trước (chọn 1 nhãn gần nhất):
    obligation_like
    permission_like
    effect_like
    procedure_like
    applicability_like
    mixed_or_other

═══ BƯỚC 2: SUY RA FINE QUESTION FAMILY (SOFT ROUTING) ═══
Sau macro family, suy ra fine family gần nhất (chọn 1 nhãn):
    legal_consequence_or_legal_effect
    eligibility_or_applicability
    procedure_or_dossier
    permission
    obligation
    tax_obligation_or_tax_effect
    status_or_identity_or_explanatory
    long_conditional
    multi_intent
    condition_ambiguity_risk
    other

Gợi ý định tuyến (không đóng, chỉ ưu tiên):
    - effect_like thường map vào legal_consequence_or_legal_effect hoặc tax_obligation_or_tax_effect.
    - applicability_like thường map vào eligibility_or_applicability hoặc condition_ambiguity_risk.
    - procedure_like thường map vào procedure_or_dossier hoặc long_conditional.
    - mixed_or_other thường map vào multi_intent, status_or_identity_or_explanatory, hoặc other.

═══ BƯỚC 3: ÁP DỤNG PARSE POLICY THEO FAMILY (KHÔNG TRÍCH XUẤT MÙ) ═══
Slot extraction phải được dẫn dắt bởi family ở Bước 1 và Bước 2, không được tách slot mù theo pattern bề mặt.
Nếu tín hiệu lexical mâu thuẫn, ưu tiên family policy rồi hạ confidence + ghi rationale.

Parse policy theo fine family:
  - legal_consequence_or_legal_effect:  [C1]
      Typical signals: "hậu quả pháp lý gì", "bị xử lý thế nào", "bị áp dụng gì",
      "có bị vô hiệu không", "có giá trị pháp lý không".
      Policy:
        ưu tiên question_focus = legal_effect;
        không cho phép action_text rỗng;
        nếu không có legal verb trực tiếp, dùng fallback có nghĩa pháp lý:
        hau_qua_phap_ly | che_tai_ap_dung | gia_tri_phap_ly.
  - eligibility_or_applicability:  [C2]
      Typical signals: "điều kiện gì", "trường hợp nào", "đủ điều kiện không", "có được công nhận không".
      Policy:
        ưu tiên question_focus = applicability;
        action_text phải phản ánh legal point at issue, ví dụ:
        dieu_kien_ap_dung | cong_nhan_tu_cach | thanh_lap_doanh_nghiep.
  - procedure_or_dossier:  [C3]
      Typical signals: "thủ tục", "quy trình", "hồ sơ gồm gì", "cần giấy tờ gì", "cách thực hiện".
      Policy:
        nếu hỏi steps/how-to/process -> ưu tiên procedure;
        nếu hỏi documents/hồ sơ/giấy tờ -> ưu tiên dossier;
        không drift sang obligation trừ khi câu hỏi thực sự hỏi tính bắt buộc.
  - permission:  [C4]
      Typical signals: "có được không", "có quyền không", "được phép không", "có thể ... không".
      Policy:
        ưu tiên question_focus = permission;
        action_text phải bám sát cụm động từ chính trong câu hỏi.
  - obligation:  [C5]
      Typical signals: "có phải", "có cần", "có bắt buộc", "phải làm gì".
      Policy:
        ưu tiên question_focus = obligation;
        không để action drift nếu hành vi được hỏi đã explicit.
      - tax_obligation_or_tax_effect:  [C6]
          Typical signals: "có phải đóng thuế không", "nghĩa vụ thuế", "thuế phát sinh",
          "cách xác định thuế", "truy thu", "xử phạt thuế".
          Policy:
            nếu hỏi có phải nộp/đóng thuế không -> ưu tiên question_focus = obligation;
            nếu hỏi hậu quả/chế tài/truy thu -> ưu tiên question_focus = legal_effect;
            nếu hỏi cách tính/xác định thuế -> ưu tiên procedure hoặc applicability tùy wording;
            cho phép fallback action đặc thù thuế:
            nghia_vu_thue | dong_thue | xac_dinh_thue | hau_qua_thue.
      - status_or_identity_or_explanatory:  [C7]
          Typical signals: "là ai", "ai có quyền", "ý nghĩa là gì", "loại hình nào phù hợp", "được xem là gì".
          Policy:
            không collapse về unknown chỉ vì thiếu procedural verb;
            dùng fallback action có nghĩa pháp lý khi cần:
            xac_dinh_tu_cach | y_nghia_phap_ly | lua_chon_loai_hinh.
      - long_conditional:  [C8]
          Typical signals: nhiều mệnh đề, có "nếu/khi/trong trường hợp", có nhiều legal actors.
          Policy:
            xác định main question clause trước;
            giữ điều kiện ở condition_text;
            không để condition nuốt mất main action.
      - multi_intent:  [C9]
          Typical signals: >1 câu hỏi trong một lượt; một ý hỏi nghĩa vụ và ý khác hỏi thuế/quyền/thủ tục.
          Policy:
            chọn primary_intent_family;
            ghi secondary_intent_families;
            tạo một parse chính cho downstream reasoning;
            nêu ý phụ trong parse_rationale.
      - condition_ambiguity_risk:  [C10]
          Typical signals: condition ngắn/mơ hồ, overlap từ vựng dễ map nhầm dossier/procedure,
          wording quá generic.
          Policy:
            nếu chưa chắc, giữ diễn giải condition theo hướng bảo thủ;
            không over-canonicalize quá tay ở Layer1;
            không ép action không liên quan chỉ vì lexical overlap yếu.
    - other:
            vẫn phải best-effort parse theo tín hiệu gần nhất, không im lặng.

═══ BƯỚC 4: QUY TẮC ĐIỀN SLOT SAU KHI ĐÃ XÁC ĐỊNH FAMILY ═══

question_focus:
  Chọn theo family ở Bước 1. Nếu không chắc giữa 2 focus, chọn focus gần nhất
  với cụm hỏi chính và hạ confidence (không để "unknown" khi còn tín hiệu).

subject_text:
  Chủ thể pháp lý: ai thực hiện / bị tác động bởi nghĩa vụ/quyền/chế tài.
  Ví dụ hợp lệ: "doanh nghiệp", "người lao động", "hộ kinh doanh", "cá nhân cư trú".
  Nếu câu không nêu rõ: điền nhãn mô tả ngắn ("đối tượng phải thực hiện nghĩa vụ",
  "bên liên quan trong giao dịch"). KHÔNG để trống nếu còn tín hiệu chủ thể.

condition_text:
  Điều kiện pháp lý kích hoạt: "khi", "nếu", "trong trường hợp", "đủ điều kiện".
  Ví dụ hợp lệ: "nộp thuế trễ hạn", "chưa đăng ký thay đổi", "có thu nhập từ tiền lương".
  KHÔNG ghi chủ đề chung như "về thuế", "liên quan lao động".
  Để trống chỉ khi không có điều kiện nào trong câu.

action_text:
  Hành vi pháp lý cụ thể: nộp hồ sơ, đăng ký, kê khai, báo cáo, thanh toán…
  KHÔNG để trống nếu câu thuộc Family B, C, D, E, G — dùng fallback label phù hợp.
  Fallback labels theo family:
    Family B: hau_qua_phap_ly | che_tai_ap_dung | gia_tri_phap_ly
    Family C: xac_dinh_dieu_kien | xac_dinh_nguong | xac_nhan_ap_dung
    Family D: thu_tuc_thuc_hien | nop_ho_so | bo_sung_ho_so
    Family E: thuc_hien_trong_thoi_han
    Family G: nghia_vu_thue | khai_thue | nop_thue | hoan_thue

modality_text:
  Giữ dấu hiệu chuẩn tắc: "phải", "được phép", "không được", "có thể", "bị cấm", "cần".

used_fallback_label:
  Điền khi action_text là nhãn fallback (không phải verb tự nhiên từ câu hỏi).
  Dùng snake_case ≤ 64 ký tự. Điền "unknown" chỉ khi action đã rõ từ câu hỏi và không dùng fallback.

parse_rationale:
  Bắt buộc khi: dùng fallback, câu mơ hồ, đa ý định, hoặc bất kỳ confidence nào < 0.75.
  Ngắn gọn ≤ 512 ký tự, nêu rõ family đã chọn và lý do quyết định parse.

question_focus_confidence, action_confidence, subject_confidence:
  Bắt buộc điền giá trị numeric ∈ [0.0, 1.0] cho cả ba.
  Hạ confidence khi: slot dùng fallback, câu mơ hồ, nhiều ý định, thiếu tín hiệu rõ.

═══ CHÍNH SÁCH CHỐNG DRIFT ═══
• Nếu câu hỏi đã nêu verb hành vi tương đối rõ, giữ đúng verb đó.
  Hỏi "bổ sung hồ sơ" → action_text="bo_sung_ho_so", không remap sang dang_ky_thay_doi.
• Chỉ dùng fallback khi không có verb hành vi trực tiếp nào trong câu hỏi.
• Không tự thay thế action bằng nhãn abstract nếu câu đã rõ.

═══ CHÍNH SÁCH ĐA Ý ĐỊNH ═══
• Câu có ≥ 2 mệnh đề hỏi rõ ràng: chọn 1 primary intent cho parse chính.
• Secondary intents ghi tóm tắt trong parse_rationale.
• Không collapse toàn bộ câu về 1 intent nếu các ý không liên quan nhau.

═══ CÁC KEY BẮT BUỘC TRONG JSON ═══
utterance_type, subject_text, condition_text, action_text, modality_text,
time_text, deadline_text, exception_text, question_focus, assertion_status,
question_focus_confidence, action_confidence, subject_confidence,
used_fallback_label, parse_rationale

═══ CÁC KEY GỢI Ý (optional) ═══
question_focus_hint, action_canonical_hint, subject_type_hint, domain_hint, condition_family_hint,
macro_family, question_family, family_confidence, family_reason,
primary_intent_family, secondary_intent_families, parse_policy_applied
Ràng buộc:
  question_focus_hint: một trong các giá trị question_focus, hoặc unknown.
  domain_hint: enterprise | tax | labor | registration | procedure | unknown.
  subject_type_hint: company | employer | employee | taxpayer | business_household | individual | authority | unknown.
    condition_family_hint: applicability | threshold | deadline | exception | obligation | prohibition | legal_effect | unknown.
    macro_family: obligation_like | permission_like | effect_like | procedure_like | applicability_like | mixed_or_other.
    question_family: legal_consequence_or_legal_effect | eligibility_or_applicability | procedure_or_dossier | permission | obligation | tax_obligation_or_tax_effect | status_or_identity_or_explanatory | long_conditional | multi_intent | condition_ambiguity_risk | other.
    family_confidence: số trong [0,1].
    family_reason: giải thích ngắn lý do chọn family.
    primary_intent_family: ưu tiên cùng taxonomy question_family, hoặc other.
    secondary_intent_families: list family phụ theo taxonomy question_family.
    parse_policy_applied: mô tả ngắn policy đã áp dụng theo family.
  action_canonical_hint: cụm chuẩn hóa snake_case ngắn gọn (nop_ho_so, dang_ky, khai_thue…); không viết câu dài.
  Không bịa thêm taxonomy mới. Nếu không chắc → unknown + hạ confidence.

═══ FEW-SHOT EXAMPLES ═══

[Example 1 — legal consequence]
Q: "Nếu nộp tiền thuế trễ hạn thì doanh nghiệp có thể bị áp dụng những hậu quả pháp lý gì?"
{"utterance_type":"conditional_legal_question","subject_text":"doanh nghiệp","condition_text":"nộp tiền thuế trễ hạn","action_text":"hau_qua_phap_ly","modality_text":"có thể bị áp dụng","time_text":"","deadline_text":"","exception_text":"","question_focus":"legal_effect","assertion_status":"hypothetical","question_focus_confidence":0.90,"action_confidence":0.83,"subject_confidence":0.95,"used_fallback_label":"hau_qua_phap_ly","parse_rationale":"Family legal_consequence_or_legal_effect: hỏi hậu quả pháp lý; dùng fallback action hợp lệ.","macro_family":"effect_like","question_family":"legal_consequence_or_legal_effect","family_confidence":0.92,"family_reason":"Cụm hỏi hậu quả pháp lý và bị áp dụng.","primary_intent_family":"legal_consequence_or_legal_effect","secondary_intent_families":[],"parse_policy_applied":"C1_no_empty_action_use_effect_fallback"}

[Example 2 — conditional obligation]
Q: "Nếu chưa đăng ký thay đổi thì có phải bổ sung hồ sơ không?"
{"utterance_type":"conditional_legal_question","subject_text":"đối tượng phải đăng ký thay đổi","condition_text":"chưa đăng ký thay đổi","action_text":"bo_sung_ho_so","modality_text":"có phải","time_text":"","deadline_text":"","exception_text":"","question_focus":"obligation","assertion_status":"hypothetical","question_focus_confidence":0.91,"action_confidence":0.90,"subject_confidence":0.76,"used_fallback_label":"unknown","parse_rationale":"Family obligation: giữ action bo_sung_ho_so theo ý hỏi chính, không drift sang action không liên quan.","macro_family":"obligation_like","question_family":"obligation","family_confidence":0.89,"family_reason":"Cấu trúc có phải ... không với action rõ.","primary_intent_family":"obligation","secondary_intent_families":[],"parse_policy_applied":"C5_keep_explicit_action_no_drift"}

[Example 3 — multi-intent]
Q: "Bán hàng tạp hóa có cần đăng ký kinh doanh không? Có phải đóng thuế không?"
{"utterance_type":"direct_question","subject_text":"hộ/cá nhân bán hàng tạp hóa","condition_text":"bán hàng tạp hóa","action_text":"dang_ky_kinh_doanh","modality_text":"có cần","time_text":"","deadline_text":"","exception_text":"","question_focus":"obligation","assertion_status":"ambiguous","question_focus_confidence":0.85,"action_confidence":0.87,"subject_confidence":0.79,"used_fallback_label":"dang_ky_kinh_doanh","parse_rationale":"Primary intent là nghĩa vụ đăng ký kinh doanh; secondary intent là nghĩa vụ thuế.","macro_family":"mixed_or_other","question_family":"multi_intent","family_confidence":0.88,"family_reason":"Hai câu hỏi nghĩa vụ khác nhau trong cùng input.","primary_intent_family":"obligation","secondary_intent_families":["tax_obligation_or_tax_effect"],"parse_policy_applied":"C9_primary_parse_with_secondary_recorded"}

[Example 4 — permission with condition]
Q: "Chủ tịch HĐQT bị tạm giam thì có điều hành công ty được không?"
{"utterance_type":"conditional_legal_question","subject_text":"chủ tịch hội đồng quản trị","condition_text":"bị tạm giam","action_text":"dieu_hanh_cong_ty","modality_text":"có ... được không","time_text":"","deadline_text":"","exception_text":"","question_focus":"permission","assertion_status":"hypothetical","question_focus_confidence":0.88,"action_confidence":0.89,"subject_confidence":0.93,"used_fallback_label":"unknown","parse_rationale":"Family permission: action bám sát cụm hỏi chính điều hành công ty.","macro_family":"permission_like","question_family":"permission","family_confidence":0.90,"family_reason":"Mẫu có được không dưới điều kiện bị tạm giam.","primary_intent_family":"permission","secondary_intent_families":[],"parse_policy_applied":"C4_permission_keep_main_verb"}

[Example 5 — procedure/dossier]
Q: "Hồ sơ thành lập chi nhánh công ty gồm những gì?"
{"utterance_type":"direct_question","subject_text":"doanh nghiệp thành lập chi nhánh","condition_text":"thành lập chi nhánh công ty","action_text":"nop_ho_so","modality_text":"","time_text":"","deadline_text":"","exception_text":"","question_focus":"dossier","assertion_status":"ambiguous","question_focus_confidence":0.92,"action_confidence":0.85,"subject_confidence":0.81,"used_fallback_label":"nop_ho_so","parse_rationale":"Family procedure_or_dossier: câu hỏi thành phần hồ sơ nên ưu tiên dossier và action không rỗng.","macro_family":"procedure_like","question_family":"procedure_or_dossier","family_confidence":0.93,"family_reason":"Cụm hồ sơ gồm những gì.","primary_intent_family":"procedure_or_dossier","secondary_intent_families":[],"parse_policy_applied":"C3_dossier_when_documents_asked"}

[Example 6 — explanatory/identity]
Q: "Người đại diện theo pháp luật của doanh nghiệp tư nhân là ai?"
{"utterance_type":"direct_question","subject_text":"doanh nghiệp tư nhân","condition_text":"đại diện theo pháp luật","action_text":"xac_dinh_tu_cach","modality_text":"","time_text":"","deadline_text":"","exception_text":"","question_focus":"authority","assertion_status":"ambiguous","question_focus_confidence":0.69,"action_confidence":0.72,"subject_confidence":0.90,"used_fallback_label":"xac_dinh_tu_cach","parse_rationale":"Family status_or_identity_or_explanatory: câu hỏi định danh pháp lý, không collapse về unknown dù thiếu procedural verb.","macro_family":"mixed_or_other","question_family":"status_or_identity_or_explanatory","family_confidence":0.86,"family_reason":"Mẫu là ai/được xem là gì thiên về định danh.","primary_intent_family":"status_or_identity_or_explanatory","secondary_intent_families":[],"parse_policy_applied":"C7_identity_explanatory_use_meaningful_fallback"}

═══ GIÁ TRỊ HỢP LỆ ═══

utterance_type (chọn một):
  direct_question | conditional_legal_question | hypothetical_question | ambiguous_question

question_focus (chọn một):
  obligation | permission | prohibition | deadline | threshold | exception | procedure
    | legal_effect | applicability | dossier | authority | unknown

assertion_status (chọn một):
  asserted | hypothetical | ambiguous
"""


class _LLMJsonLayer1(BaseModel):
    utterance_type: str = ""
    subject_text: str = ""
    condition_text: str = ""
    action_text: str = ""
    modality_text: str = ""
    time_text: str = ""
    deadline_text: str = ""
    exception_text: str = ""
    question_focus: str = "unknown"
    assertion_status: str = "ambiguous"
    question_focus_confidence: float | None = None
    action_confidence: float | None = None
    subject_confidence: float | None = None
    used_fallback_label: str | None = None
    parse_rationale: str | None = None
    question_focus_hint: str | None = None
    action_canonical_hint: str | None = None
    subject_type_hint: str | None = None
    domain_hint: str | None = None
    condition_family_hint: str | None = None
    macro_family: str | None = None
    question_family: str | None = None
    family_confidence: float | None = None
    family_reason: str | None = None
    primary_intent_family: str | None = None
    secondary_intent_families: list[str] | None = None
    parse_policy_applied: str | None = None

    @field_validator(
        "question_focus_confidence",
        "action_confidence",
        "subject_confidence",
        "family_confidence",
        mode="before",
    )
    @classmethod
    def _coerce_confidence(cls, value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            num = float(value)
        else:
            text = _norm_ws(str(value))
            if not text:
                return None
            if _norm_hint_key(text) in _NOISY_HINT_TOKENS:
                return None
            text = text.replace("%", "")
            try:
                num = float(text)
            except ValueError:
                return None
        if num > 1.0 and num <= 100.0:
            num = num / 100.0
        return max(0.0, min(1.0, num))

    @field_validator("used_fallback_label", mode="before")
    @classmethod
    def _coerce_used_fallback_label(cls, value: Any) -> str | None:
        key = _norm_hint_key(str(value or ""))
        if key in _NOISY_HINT_TOKENS:
            return None
        if len(key) > 64 or key.count("_") > 6:
            return None
        return key or None

    @field_validator("parse_rationale", mode="before")
    @classmethod
    def _coerce_parse_rationale(cls, value: Any) -> str | None:
        text = _norm_ws(str(value or ""))
        if not text:
            return None
        return text[:512]

    @field_validator("family_reason", "parse_policy_applied", mode="before")
    @classmethod
    def _coerce_family_text(cls, value: Any) -> str | None:
        text = _norm_ws(str(value or ""))
        if not text:
            return None
        return text[:512]

    @field_validator("secondary_intent_families", mode="before")
    @classmethod
    def _coerce_secondary_intent_families(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            raw_items = [x for x in re.split(r"[,;|]+", value) if _norm_ws(x)]
        elif isinstance(value, list):
            raw_items = [str(x) for x in value if _norm_ws(str(x))]
        else:
            return None
        normalized = []
        for item in raw_items:
            key = _norm_hint_key(item)
            if key in _NOISY_HINT_TOKENS:
                continue
            if key not in normalized:
                normalized.append(key)
        return normalized[:8] or None


_UTTERANCE: tuple[str, ...] = (
    "direct_question",
    "conditional_legal_question",
    "hypothetical_question",
    "ambiguous_question",
    "question",
    "command",
    "assertion",
    "unknown",
)
_FOCUS: tuple[str, ...] = (
    "obligation",
    "permission",
    "prohibition",
    "deadline",
    "threshold",
    "exception",
    "applicability",
    "dossier",
    "legal_effect",
    "authority",
    "procedure",
    "legal_consequence",
    "unknown",
)
_ASSERT: tuple[str, ...] = ("asserted", "hypothetical", "ambiguous", "factual", "unknown")
_ACTION_VERBS: tuple[str, ...] = (
    "nộp",
    "gửi",
    "đăng ký",
    "thanh toán",
    "thông báo",
    "kê khai",
    "công khai",
    "hoàn tất",
    "báo",
)
_DOMAIN_HINTS: tuple[str, ...] = ("enterprise", "tax", "labor", "registration", "procedure", "unknown")
_SUBJECT_TYPE_HINTS: tuple[str, ...] = (
    "company",
    "employer",
    "employee",
    "taxpayer",
    "business_household",
    "individual",
    "authority",
    "unknown",
)
_CONDITION_FAMILY_HINTS: tuple[str, ...] = (
    *CANONICAL_FAMILIES,
    "unknown",
)
_MACRO_FAMILIES: tuple[str, ...] = (
    "obligation_like",
    "permission_like",
    "effect_like",
    "procedure_like",
    "applicability_like",
    "mixed_or_other",
)
_QUESTION_FAMILIES: tuple[str, ...] = (
    "legal_consequence_or_legal_effect",
    "eligibility_or_applicability",
    "procedure_or_dossier",
    "permission",
    "obligation",
    "tax_obligation_or_tax_effect",
    "status_or_identity_or_explanatory",
    "long_conditional",
    "multi_intent",
    "condition_ambiguity_risk",
    "other",
)
_NOISY_HINT_TOKENS: frozenset[str] = frozenset(
    {
        "",
        "unknown",
        "none",
        "null",
        "n_a",
        "na",
        "khong",
        "khong_ro",
        "khong_biet",
        "khong_xac_dinh",
        "khong_chac",
    }
)
_DOMAIN_HINT_ALIASES: dict[str, str] = {
    "enterprise": "enterprise",
    "business": "enterprise",
    "company": "enterprise",
    "doanh_nghiep": "enterprise",
    "tax": "tax",
    "taxation": "tax",
    "thue": "tax",
    "labor": "labor",
    "labour": "labor",
    "employment": "labor",
    "lao_dong": "labor",
    "nhan_su": "labor",
    "registration": "registration",
    "dang_ky": "registration",
    "registry": "registration",
    "procedure": "procedure",
    "procedural": "procedure",
    "thu_tuc": "procedure",
    "administrative_procedure": "procedure",
}
_SUBJECT_TYPE_HINT_ALIASES: dict[str, str] = {
    "company": "company",
    "cong_ty": "company",
    "doanh_nghiep": "company",
    "business": "company",
    "employer": "employer",
    "nguoi_su_dung_lao_dong": "employer",
    "employee": "employee",
    "worker": "employee",
    "laborer": "employee",
    "nguoi_lao_dong": "employee",
    "taxpayer": "taxpayer",
    "nguoi_nop_thue": "taxpayer",
    "business_household": "business_household",
    "household_business": "business_household",
    "ho_kinh_doanh": "business_household",
    "individual": "individual",
    "person": "individual",
    "ca_nhan": "individual",
    "authority": "authority",
    "agency": "authority",
    "co_quan": "authority",
    "co_quan_nha_nuoc": "authority",
}
_CONDITION_FAMILY_HINT_ALIASES: dict[str, str] = {
    "applicability": "applicability",
    "ap_dung": "applicability",
    "pham_vi_ap_dung": "applicability",
    "threshold": "threshold",
    "nguong": "threshold",
    "muc_nguong": "threshold",
    "deadline": "deadline",
    "thoi_han": "deadline",
    "han": "deadline",
    "exception": "exception",
    "ngoai_le": "exception",
    "mien_tru": "exception",
    "eligibility": "applicability",
    "du_dieu_kien": "applicability",
    "dieu_kien_huong": "applicability",
    "obligation_trigger": "obligation",
    "dieu_kien_phat_sinh_nghia_vu": "obligation",
    "kich_hoat_nghia_vu": "obligation",
    "prohibition_trigger": "prohibition",
    "dieu_kien_cam": "prohibition",
    "kich_hoat_cam_doan": "prohibition",
    "legal_effect_trigger": "legal_effect",
    "dieu_kien_phat_sinh_hieu_luc": "legal_effect",
    "hau_qua_phap_ly": "legal_effect",
    "legal_consequence": "legal_effect",
    "legal_consequence_or_legal_effect": "legal_effect",
    "condition_based": "applicability",
    "applicability_condition": "applicability",
}
_QUESTION_FOCUS_HINT_ALIASES: dict[str, str] = {
    "obligation": "obligation",
    "nghia_vu": "obligation",
    "permission": "permission",
    "duoc_phep": "permission",
    "quyen": "permission",
    "prohibition": "prohibition",
    "cam": "prohibition",
    "bi_cam": "prohibition",
    "deadline": "deadline",
    "thoi_han": "deadline",
    "threshold": "threshold",
    "nguong": "threshold",
    "exception": "exception",
    "ngoai_le": "exception",
    "procedure": "procedure",
    "thu_tuc": "procedure",
    "legal_consequence": "legal_effect",
    "hau_qua_phap_ly": "legal_effect",
    "applicability": "applicability",
    "ap_dung": "applicability",
    "dossier": "dossier",
    "ho_so": "dossier",
    "legal_effect": "legal_effect",
    "hieu_luc": "legal_effect",
    "authority": "authority",
    "tham_quyen": "authority",
    "co_quan": "authority",
}


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _fold_text(s: str) -> str:
    normalized = unicodedata.normalize("NFKD", s or "")
    folded = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return folded.replace("đ", "d").replace("Đ", "D")


def _norm_hint_key(s: str | None) -> str:
    text = _fold_text(_norm_ws(s or "")).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def _semantic_fallback_action(question: str, focus: str) -> tuple[str, str | None, str | None]:
    q = _norm_ws(question)
    low = _fold_text(q).lower()
    focus_key = (focus or "").strip().lower()

    def has_any(*patterns: str) -> bool:
        return any(re.search(p, low, flags=re.IGNORECASE) for p in patterns)

    # Legal consequence / sanction style questions.
    if has_any(r"hau\s*qua\s*phap\s*ly", r"bi\s*ap\s*dung", r"bi\s*xu\s*ly\s*the\s*nao") or (
        focus_key == "legal_effect" and has_any(r"phat", r"che\s*tai")
    ):
        if has_any(r"phat", r"xu\s*phat", r"che\s*tai"):
            return (
                "che_tai_ap_dung",
                "che_tai_ap_dung",
                "Backfill action từ tín hiệu chế tài/xử lý trong câu hỏi legal consequence.",
            )
        return (
            "hau_qua_phap_ly",
            "hau_qua_phap_ly",
            "Backfill action từ cụm hỏi hậu quả pháp lý/bị áp dụng.",
        )

    # Legal effect validity/value questions.
    if has_any(r"vo\s*hieu", r"gia\s*tri\s*phap\s*ly") or focus_key == "legal_effect":
        return (
            "gia_tri_phap_ly",
            "gia_tri_phap_ly",
            "Backfill action từ cụm hỏi vô hiệu/giá trị pháp lý.",
        )

    # Procedure / dossier questions.
    if has_any(r"bo\s*sung\s*ho\s*so"):
        return (
            "bo_sung_ho_so",
            "bo_sung_ho_so",
            "Backfill action từ cụm bổ sung hồ sơ.",
        )
    if focus_key in {"dossier", "procedure"}:
        return (
            "thuc_hien_hanh_vi",
            "thuc_hien_hanh_vi",
            "Backfill action theo question_focus thủ tục/hồ sơ.",
        )

    # Common obligation/permission anchors.
    if has_any(r"dang\s*ky\s*kinh\s*doanh"):
        return (
            "dang_ky_kinh_doanh",
            "dang_ky_kinh_doanh",
            "Backfill action từ cụm đăng ký kinh doanh.",
        )
    if has_any(r"dang\s*ky\s*thay\s*doi", r"thay\s*doi\s*dang\s*ky"):
        return (
            "thay_doi_dang_ky",
            "thay_doi_dang_ky",
            "Backfill action từ cụm thay đổi đăng ký.",
        )
    if focus_key in {"obligation", "permission"} and has_any(r"thue", r"nop\s*thue", r"dong\s*thue"):
        return (
            "nghia_vu_thue",
            "nghia_vu_thue",
            "Backfill action theo nghĩa vụ/quyền liên quan thuế.",
        )

    # Explicit focus but weak lexical action: keep parser usable with a stable fallback.
    if focus_key == "obligation":
        return (
            "nghia_vu_thuc_hien",
            "nghia_vu_thuc_hien",
            "Backfill action mặc định cho câu hỏi nghĩa vụ có tín hiệu ngữ nghĩa nhưng thiếu verb rõ.",
        )
    if focus_key == "permission":
        return (
            "hanh_vi_duoc_phep",
            "hanh_vi_duoc_phep",
            "Backfill action mặc định cho câu hỏi quyền/được phép có tín hiệu ngữ nghĩa.",
        )
    if focus_key == "prohibition":
        return (
            "hanh_vi_bi_cam",
            "hanh_vi_bi_cam",
            "Backfill action mặc định cho câu hỏi cấm đoán có tín hiệu ngữ nghĩa.",
        )
    if focus_key == "legal_effect":
        return (
            "hau_qua_phap_ly",
            "hau_qua_phap_ly",
            "Backfill action mặc định cho câu hỏi hậu quả/pháp lý có tín hiệu ngữ nghĩa.",
        )
    if focus_key == "deadline":
        return (
            "thuc_hien_hanh_vi",
            "thuc_hien_hanh_vi",
            "Backfill action mặc định cho câu hỏi thời hạn.",
        )

    return "", None, None


def _clean_action_candidate(text: str) -> str:
    cand = _norm_ws(text)
    if not cand:
        return ""
    cand = re.sub(r"^(?:thi|thì)\s+", "", cand, flags=re.IGNORECASE)
    cand = re.sub(
        r"\b(khong|không|gi|gì|gi\?|gì\?|the nao|thế nào|bao nhieu|bao nhiêu|khi nao|khi nào)\b[\s?.!,;:]*$",
        "",
        cand,
        flags=re.IGNORECASE,
    )
    cand = _norm_ws(cand)
    if len(cand) > 96:
        return ""
    return cand


def _backfill_action_text(
    question: str,
    action_text: str,
    focus: str,
    *,
    return_meta: bool = False,
) -> str | tuple[str, str | None, str | None, bool]:
    cur = _norm_ws(action_text)
    if cur:
        if return_meta:
            return cur, None, None, False
        return cur

    q = _norm_ws(question)
    low = q.lower()

    semantic_action, semantic_label, semantic_rationale = _semantic_fallback_action(question, focus)
    if semantic_action:
        if return_meta:
            return semantic_action, semantic_label, semantic_rationale, True
        return semantic_action

    m = re.search(
        r"(?:phải|cần|được|phải được|có phải|co phai|co duoc|có được)\s+([^?.;,:]+)",
        low,
        flags=re.IGNORECASE,
    )
    if m:
        cand = _clean_action_candidate(m.group(1))
        cand = re.sub(r"\b(trong bao nhiêu|bao nhiêu|mấy|khi nào|thời điểm nào)\b.*$", "", cand, flags=re.IGNORECASE)
        cand = _norm_ws(cand)
        if cand:
            if return_meta:
                return cand, None, "Backfill action từ cụm nghĩa vụ/quyền trong câu hỏi.", True
            return cand

    verb_pattern = "|".join(re.escape(v) for v in _ACTION_VERBS)
    m2 = re.search(rf"\b({verb_pattern})\b([^?.;,:]*)", low, flags=re.IGNORECASE)
    if m2:
        head = _clean_action_candidate(m2.group(1) + " " + m2.group(2))
        head = re.sub(r"\b(trong bao nhiêu|bao nhiêu|mấy|khi nào|thời điểm nào)\b.*$", "", head, flags=re.IGNORECASE)
        head = _norm_ws(head)
        if head:
            if return_meta:
                return head, None, "Backfill action từ cụm động từ pháp lý trong câu hỏi.", True
            return head

    if (focus or "").strip().lower() == "deadline":
        if return_meta:
            return "thực hiện nghĩa vụ theo thời hạn", "thuc_hien_hanh_vi", "Backfill action theo focus deadline.", True
        return "thực hiện nghĩa vụ theo thời hạn"
    if return_meta:
        return "", None, None, False
    return ""


def _coerce_ut(s: str) -> UtteranceType:
    t = (s or "").strip().lower().replace(" ", "_")
    if t in _UTTERANCE:
        return t  # type: ignore[return-value]
    return "direct_question"


def _coerce_focus(s: str) -> QuestionFocus:
    t = (s or "").strip().lower().replace(" ", "_")
    if t == "legal_consequence":
        t = "legal_effect"
    if t in _FOCUS:
        return t  # type: ignore[return-value]
    return "unknown"


def _coerce_assert(s: str) -> AssertionStatus:
    t = (s or "").strip().lower()
    if t == "factual":
        return "asserted"
    if t in _ASSERT:
        return t  # type: ignore[return-value]
    return "ambiguous"


def _extract_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if "```" in text:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
        if m:
            text = m.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise
        data = json.loads(m.group(0))
    if not isinstance(data, dict):
        raise ValueError("layer1_llm_not_object")
    return data


def _norm_hint(s: str | None) -> str | None:
    text = _norm_ws(s or "")
    return text or None


def _normalize_vocab_hint(
    raw: str | None,
    *,
    allowed: tuple[str, ...],
    aliases: dict[str, str],
) -> str | None:
    key = _norm_hint_key(raw)
    if key in _NOISY_HINT_TOKENS:
        return None
    if key in aliases:
        return aliases[key]
    if key in allowed:
        return key
    return None


def _normalize_question_focus_hint(raw: str | None) -> str | None:
    key = _norm_hint_key(raw)
    if key in _NOISY_HINT_TOKENS:
        return None
    if key in _QUESTION_FOCUS_HINT_ALIASES:
        key = _QUESTION_FOCUS_HINT_ALIASES[key]
    focus = _coerce_focus(key)
    return focus if focus != "unknown" or key == "unknown" else None


def _normalize_action_canonical_hint(raw: str | None) -> str | None:
    key = _norm_hint_key(raw)
    if key in _NOISY_HINT_TOKENS:
        return None
    if not key or len(key) > 64:
        return None
    if key.count("_") > 4:
        return None
    return key


def _normalize_condition_family_hint(raw: str | None) -> str | None:
    key = _norm_hint_key(raw)
    if key in _NOISY_HINT_TOKENS:
        return None
    mapped = _CONDITION_FAMILY_HINT_ALIASES.get(key, key)
    fam = normalize_family(mapped)
    if fam:
        return fam
    if mapped == "unknown":
        return "unknown"
    return None


def _build_normalized_hints(parsed: _LLMJsonLayer1) -> dict[str, str | None]:
    return {
        "question_focus_hint": _normalize_question_focus_hint(parsed.question_focus_hint),
        "action_canonical_hint": _normalize_action_canonical_hint(parsed.action_canonical_hint),
        "subject_type_hint": _normalize_vocab_hint(
            parsed.subject_type_hint,
            allowed=_SUBJECT_TYPE_HINTS,
            aliases=_SUBJECT_TYPE_HINT_ALIASES,
        ),
        "domain_hint": _normalize_vocab_hint(
            parsed.domain_hint,
            allowed=_DOMAIN_HINTS,
            aliases=_DOMAIN_HINT_ALIASES,
        ),
        "condition_family_hint": _normalize_vocab_hint(
            _normalize_condition_family_hint(parsed.condition_family_hint),
            allowed=_CONDITION_FAMILY_HINTS,
            aliases={},
        ),
    }


def _normalize_macro_family(raw: str | None) -> str | None:
    key = _norm_hint_key(raw)
    if key in _NOISY_HINT_TOKENS:
        return None
    return key if key in _MACRO_FAMILIES else None


def _normalize_question_family(raw: str | None) -> str | None:
    key = _norm_hint_key(raw)
    if key in _NOISY_HINT_TOKENS:
        return None
    return key if key in _QUESTION_FAMILIES else None


def _build_family_fields(parsed: _LLMJsonLayer1) -> dict[str, Any]:
    primary = _normalize_question_family(parsed.primary_intent_family)
    secondary_raw = parsed.secondary_intent_families or []
    secondary = [
        fam
        for fam in (_normalize_question_family(x) for x in secondary_raw)
        if fam and fam != primary
    ]
    dedup_secondary: list[str] = []
    for fam in secondary:
        if fam not in dedup_secondary:
            dedup_secondary.append(fam)

    return {
        "macro_family": _normalize_macro_family(parsed.macro_family),
        "question_family": _normalize_question_family(parsed.question_family),
        "family_confidence": parsed.family_confidence,
        "family_reason": parsed.family_reason,
        "primary_intent_family": primary,
        "secondary_intent_families": dedup_secondary,
        "parse_policy_applied": parsed.parse_policy_applied,
    }


def _build_best_effort_fields(parsed: _LLMJsonLayer1) -> dict[str, Any]:
    return {
        "question_focus_confidence": parsed.question_focus_confidence,
        "action_confidence": parsed.action_confidence,
        "subject_confidence": parsed.subject_confidence,
        "used_fallback_label": parsed.used_fallback_label,
        "parse_rationale": parsed.parse_rationale,
    }


def _merge_best_effort_fields(
    parsed: _LLMJsonLayer1,
    *,
    derived_fallback_label: str | None,
    derived_parse_rationale: str | None,
    action_backfilled: bool,
) -> dict[str, Any]:
    out = _build_best_effort_fields(parsed)
    if not out.get("used_fallback_label") and derived_fallback_label:
        out["used_fallback_label"] = derived_fallback_label
    if not out.get("parse_rationale") and derived_parse_rationale:
        out["parse_rationale"] = derived_parse_rationale
    if out.get("action_confidence") is None and action_backfilled:
        out["action_confidence"] = 0.55
    if action_backfilled:
        out["action_fallback_used"] = True
        out["action_fallback_label"] = out.get("used_fallback_label") or derived_fallback_label
        out["action_fallback_rationale"] = derived_parse_rationale
    return out


def parse_layer1_llm(
    question: str,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> tuple[Layer1Parse, dict[str, Any]]:
    """
    Returns (Layer1Parse, trace dict with raw_llm_output, parser_backend, parser_model).
    Raises on hard failure.
    """
    key = (api_key or os.environ.get("LEGAL_QA_LLM_API_KEY") or os.environ.get("LLM_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("layer1_llm_no_api_key")
    if OpenAI is None:
        raise RuntimeError("layer1_llm_openai_missing")

    base = (base_url or os.environ.get("LEGAL_QA_LLM_BASE_URL") or os.environ.get("LLM_BASE_URL") or "").strip()
    if not base:
        base = "https://api.groq.com/openai/v1"
    mdl = (model or os.environ.get("LEGAL_QA_LLM_MODEL") or os.environ.get("LLM_MODEL") or "").strip()
    if not mdl:
        mdl = "llama-3.1-8b-instant"

    parsed_base = urlparse(base)
    provider = (parsed_base.netloc or parsed_base.path or "openai_compatible").strip() or "openai_compatible"

    t0 = perf_counter()
    client = OpenAI(api_key=key, base_url=base.rstrip("/"), timeout=90.0)
    user = f"Câu hỏi:\n{question.strip()}"
    resp = client.chat.completions.create(
        model=mdl,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.0,
        max_tokens=512,
    )
    raw = (resp.choices[0].message.content or "").strip()
    latency_ms = round((perf_counter() - t0) * 1000.0, 3)
    data = _extract_json(raw)
    parsed = _LLMJsonLayer1.model_validate(data)
    resolved_action_text, derived_fallback_label, derived_parse_rationale, action_backfilled = _backfill_action_text(
        question,
        parsed.action_text.strip(),
        parsed.question_focus,
        return_meta=True,
    )
    if action_backfilled and not parsed.action_text.strip() and parsed.used_fallback_label:
        resolved_action_text = parsed.used_fallback_label
        derived_fallback_label = parsed.used_fallback_label
        if not derived_parse_rationale:
            derived_parse_rationale = "Ưu tiên dùng used_fallback_label do model cung cấp cho primary intent."
    normalized_hints = _build_normalized_hints(parsed)
    family_fields = _build_family_fields(parsed)
    best_effort_fields = _merge_best_effort_fields(
        parsed,
        derived_fallback_label=derived_fallback_label,
        derived_parse_rationale=derived_parse_rationale,
        action_backfilled=action_backfilled,
    )

    l1 = Layer1Parse(
        utterance_type=_coerce_ut(parsed.utterance_type),
        subject_text=parsed.subject_text.strip(),
        condition_text=parsed.condition_text.strip(),
        action_text=resolved_action_text,
        modality_text=parsed.modality_text.strip(),
        time_text=parsed.time_text.strip(),
        deadline_text=parsed.deadline_text.strip() or parsed.time_text.strip(),
        exception_text=parsed.exception_text.strip(),
        question_focus=_coerce_focus(parsed.question_focus),
        assertion_status=_coerce_assert(parsed.assertion_status),
        raw_notes=["llm_layer1_json"],
        parse_metadata={
            "parser_backend": "llm",
            "parser_provider": provider,
            "parser_model": mdl,
            "requested_mode": "llm_real",
            "actual_mode": "llm_real",
            "parse_mode": "llm_real",
            "provider": provider,
            "model": mdl,
            "parser_available": True,
            "parser_error": None,
            "parser_prompt_version": _PROMPT_VERSION,
            "parser_latency_ms": latency_ms,
            "parser_backend_mode": "llm_real",
            "fallback_used": action_backfilled,
            "raw_llm_output": raw[:8000],
            **best_effort_fields,
            **normalized_hints,
            **family_fields,
        },
    )
    trace = dict(l1.parse_metadata)
    return l1, trace


def repair_layer1_slots_llm(
    question: str,
    previous: Layer1Parse,
    *,
    hint: str,
    diagnostic_codes: list[str],
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> tuple[Layer1Parse, dict[str, Any]]:
    """Re-ask LLM to fix slots given verification errors."""
    key = (api_key or os.environ.get("LEGAL_QA_LLM_API_KEY") or os.environ.get("LLM_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("layer1_llm_no_api_key")
    if OpenAI is None:
        raise RuntimeError("layer1_llm_openai_missing")

    base = (base_url or os.environ.get("LEGAL_QA_LLM_BASE_URL") or "").strip() or "https://api.groq.com/openai/v1"
    mdl = (model or os.environ.get("LEGAL_QA_LLM_MODEL") or "").strip() or "llama-3.1-8b-instant"
    parsed_base = urlparse(base)
    provider = (parsed_base.netloc or parsed_base.path or "openai_compatible").strip() or "openai_compatible"
    t0 = perf_counter()
    client = OpenAI(api_key=key, base_url=base.rstrip("/"), timeout=90.0)

    prev_json = previous.model_dump(mode="json", exclude={"parse_metadata", "raw_notes"})
    repair_sys = _SYSTEM + (
        "\nBạn đang SỬA parse trước đó. Giữ đúng schema JSON. "
        "Chỉ sửa các trường cần thiết theo gợi ý lỗi. "
        f"Lỗi: {diagnostic_codes}. Gợi ý: {hint}."
    )
    user = f"Câu hỏi gốc:\n{question.strip()}\n\nParse trước (JSON):\n{json.dumps(prev_json, ensure_ascii=False)}"
    resp = client.chat.completions.create(
        model=mdl,
        messages=[
            {"role": "system", "content": repair_sys},
            {"role": "user", "content": user},
        ],
        temperature=0.0,
        max_tokens=512,
    )
    raw = (resp.choices[0].message.content or "").strip()
    latency_ms = round((perf_counter() - t0) * 1000.0, 3)
    data = _extract_json(raw)
    parsed = _LLMJsonLayer1.model_validate(data)
    resolved_action_text, derived_fallback_label, derived_parse_rationale, action_backfilled = _backfill_action_text(
        question,
        parsed.action_text.strip(),
        parsed.question_focus,
        return_meta=True,
    )
    if action_backfilled and not parsed.action_text.strip() and parsed.used_fallback_label:
        resolved_action_text = parsed.used_fallback_label
        derived_fallback_label = parsed.used_fallback_label
        if not derived_parse_rationale:
            derived_parse_rationale = "Ưu tiên dùng used_fallback_label do model cung cấp cho primary intent."
    normalized_hints = _build_normalized_hints(parsed)
    family_fields = _build_family_fields(parsed)
    best_effort_fields = _merge_best_effort_fields(
        parsed,
        derived_fallback_label=derived_fallback_label,
        derived_parse_rationale=derived_parse_rationale,
        action_backfilled=action_backfilled,
    )

    l1 = Layer1Parse(
        utterance_type=_coerce_ut(parsed.utterance_type),
        subject_text=parsed.subject_text.strip(),
        condition_text=parsed.condition_text.strip(),
        action_text=resolved_action_text,
        modality_text=parsed.modality_text.strip(),
        time_text=parsed.time_text.strip(),
        deadline_text=parsed.deadline_text.strip() or parsed.time_text.strip(),
        exception_text=parsed.exception_text.strip(),
        question_focus=_coerce_focus(parsed.question_focus),
        assertion_status=_coerce_assert(parsed.assertion_status),
        raw_notes=list(previous.raw_notes) + ["llm_layer1_slot_repair"],
        parse_metadata={
            "parser_backend": "llm_repair",
            "parser_provider": provider,
            "parser_model": mdl,
            "requested_mode": "llm_real",
            "actual_mode": "llm_real",
            "parse_mode": "llm_real",
            "provider": provider,
            "model": mdl,
            "parser_available": True,
            "parser_error": None,
            "parser_prompt_version": _PROMPT_VERSION,
            "parser_latency_ms": latency_ms,
            "parser_backend_mode": "llm_real",
            "fallback_used": action_backfilled,
            "raw_llm_output": raw[:8000],
            **best_effort_fields,
            **normalized_hints,
            **family_fields,
            "repair_hint": hint,
            "diagnostic_codes": diagnostic_codes,
        },
    )
    return l1, dict(l1.parse_metadata)
