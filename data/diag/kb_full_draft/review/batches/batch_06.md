

######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 112. Hồ sơ đề nghị và giải quyết hưởng chế độ tử tuất
[NGUYÊN VĂN]
Điều 112. Hồ sơ đề nghị và giải quyết hưởng chế độ tử tuất 
1. Hồ sơ đề nghị hưởng chế độ tử tuất được quy định như sau: 
a) Hồ sơ đề nghị hưởng chế độ tử tuất đối với thân nhân của người đang tham gia bảo hiểm xã 
hội hoặc đang bảo lưu thời gian đóng bảo hiểm xã hội được thực hiện theo quy định tại các điểm 
a, b và c khoản 1 Điều 90 của Luật này; 
b) Hồ sơ đề nghị hưởng chế độ tử tuất đối với thân nhân của người đang hưởng hoặc đang tạm 
dừng hưởng lương hưu thực hiện theo quy định tại điểm a và điểm b khoản 2 Điều 90 của Luật 
này; 
c) Hồ sơ đối với trường hợp chỉ hưởng trợ cấp mai táng thực hiện theo quy định tại khoản 3 Điều 
90 của Luật này. 
2. Việc giải quyết hưởng chế độ tử tuất thực hiện như sau: 
a) Trong thời hạn 90 ngày kể từ ngày người đang bảo lưu thời gian đóng bảo hiểm xã hội, người 
tham gia bảo hiểm xã hội tự nguyện, người đang hưởng lương hưu hoặc đang tạm dừng hưởng 
lương hưu chết thì thân nhân nộp hồ sơ cho cơ quan bảo hiểm xã hội; 
b) Trong thời hạn 10 ngày làm việc kể từ ngày nhận đủ hồ sơ theo quy định, cơ quan bảo hiểm 
xã hội có trách nhiệm giải quyết; trường hợp không giải quyết thì phải trả lời bằng văn bản và 
nêu rõ lý do.

[RULES]
{"id": "LAB-10-D112-000", "type": "condition", "premises": ["has_full_contribution_time_by_state", "has_request_document"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 112 khoản 1 điểm a", "exception_to": "", "quote": "Hồ sơ đề nghị hưởng chế độ tử tuất đối với thân nhân của người đang tham gia bảo hiểm xã hội hoặc đang bảo lưu thời gian đóng bảo hiểm xã hội được thực hiện theo quy định tại các điểm a, b và c khoản 1 Điều 90 của Luật này."}
{"id": "LAB-10-D112-001", "type": "condition", "premises": ["receiving_pension", "has_request_document"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 112 khoản 1 điểm b", "exception_to": "", "quote": "Hồ sơ đề nghị hưởng chế độ tử tuất đối với thân nhân của người đang hưởng hoặc đang tạm dừng hưởng lương hưu thực hiện theo quy định tại điểm a và điểm b khoản 2 Điều 90 của Luật này."}
{"id": "LAB-10-D112-002", "type": "condition", "premises": ["has_request_document"], "conclusion": "funeral_support", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 112 khoản 1 điểm c", "exception_to": "", "quote": "Hồ sơ đối với trường hợp chỉ hưởng trợ cấp mai táng thực hiện theo quy định tại khoản 3 Điều 90 của Luật này."}
{"id": "LAB-10-D112-003", "type": "condition", "premises": ["has_request_document", "deceased_person_date"], "conclusion": "must_submit_application_within_90_days", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 112 khoản 2 điểm a", "exception_to": "", "quote": "Trong thời hạn 90 ngày kể từ ngày người đang bảo lưu thời gian đóng bảo hiểm xã hội, người tham gia bảo hiểm xã hội tự nguyện, người đang hưởng lương hưu hoặc đang tạm dừng hưởng lương hưu chết thì thân nhân nộp hồ sơ cho cơ quan bảo hiểm xã hội."}
{"id": "LAB-10-D112-004", "type": "condition", "premises": ["received_request_document"], "conclusion": "must_resolve_maternity_benefit_application", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 112 khoản 2 điểm b", "exception_to": "", "quote": "Trong thời hạn 10 ngày làm việc kể từ ngày nhận đủ hồ sơ theo quy định, cơ quan bảo hiểm xã hội có trách nhiệm giải quyết."}
{"id": "LAB-10-D112-005", "type": "lookup", "premises": [], "conclusion": "application_requirements_for_survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 112 khoản 1", "exception_to": "", "quote": "Hồ sơ đề nghị hưởng chế độ tử tuất được quy định như sau:"}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 113. Giải quyết hưởng chế độ bảo hiểm xã hội tự nguyện chậm so với thời hạn quy
[NGUYÊN VĂN]
Điều 113. Giải quyết hưởng chế độ bảo hiểm xã hội tự nguyện chậm so với thời hạn quy 
định 
1. Trường hợp nộp hồ sơ quá thời hạn quy định tại khoản 1 Điều 97, khoản 1 Điều 107, điểm a 
khoản 2 Điều 112 của Luật này thì phải giải trình bằng văn bản và gửi cho cơ quan bảo hiểm xã 
hội khi nộp hồ sơ. 
2. Trường hợp nộp hồ sơ quá thời hạn quy định hoặc giải quyết hưởng chế độ bảo hiểm xã hội tự 
nguyện chậm so với thời hạn quy định, gây thiệt hại đến quyền, lợi ích hợp pháp của người thụ 
hưởng thì phải bồi thường theo quy định của pháp luật, trừ trường hợp do lỗi của người thụ 
hưởng chế độ bảo hiểm xã hội.

[RULES]
{"id": "LAB-10-D113-000", "type": "condition", "premises": ["submitted_request_for_monthly_allowance", "not_paid_si_after_60_days"], "conclusion": "must_respond_in_writing_if_not_approved", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 113 khoản 1", "exception_to": "", "quote": "phải giải trình bằng văn bản và gửi cho cơ quan bảo hiểm xã hội khi nộp hồ sơ."}
{"id": "LAB-10-D113-001", "type": "condition", "premises": ["submitted_request_for_monthly_allowance", "cham_dong_bhxh"], "conclusion": "must_compensate_for_delayed_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 113 khoản 2", "exception_to": "", "quote": "thì phải bồi thường theo quy định của pháp luật, trừ trường hợp do lỗi của người thụ hưởng chế độ bảo hiểm xã hội."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 114. Hình thức chi trả lương hưu và chế độ bảo hiểm xã hội tự nguyện
[NGUYÊN VĂN]
Điều 114. Hình thức chi trả lương hưu và chế độ bảo hiểm xã hội tự nguyện 
1. Thông qua tài khoản của người thụ hưởng mở tại ngân hàng thương mại, chi nhánh ngân hàng 
nước ngoài được thành lập và hoạt động tại Việt Nam. 
2. Trực tiếp từ cơ quan bảo hiểm xã hội hoặc tổ chức dịch vụ được cơ quan bảo hiểm xã hội ủy 
quyền.

[RULES]
{"id": "LAB-10-D114-000", "type": "condition", "premises": ["receive_pension_through_bank_account"], "conclusion": "receive_pension_through_bank_account", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 114 khoản 1", "exception_to": "", "quote": "Thông qua tài khoản của người thụ hưởng mở tại ngân hàng thương mại, chi nhánh ngân hàng nước ngoài được thành lập và hoạt động tại Việt Nam."}
{"id": "LAB-10-D114-001", "type": "condition", "premises": ["receive_pension_directly_from_agency"], "conclusion": "receive_pension_directly_from_agency", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 114 khoản 2", "exception_to": "", "quote": "Trực tiếp từ cơ quan bảo hiểm xã hội hoặc tổ chức dịch vụ được cơ quan bảo hiểm xã hội ủy quyền."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 115. Trợ cấp một lần đối với người đang hưởng lương hưu ra nước ngoài để định cư;
[NGUYÊN VĂN]
Điều 115. Trợ cấp một lần đối với người đang hưởng lương hưu ra nước ngoài để định cư; 
chuyển nơi hưởng lương hưu; tạm dừng, chấm dứt, tiếp tục hưởng lương hưu 
1. Người tham gia bảo hiểm xã hội tự nguyện đang hưởng lương hưu ra nước ngoài để định cư 
nếu có nguyện vọng thì được giải quyết hưởng trợ cấp một lần và việc giải quyết hưởng trợ cấp 
một lần thực hiện như sau: 
a) Mức trợ cấp một lần đối với người đang hưởng lương hưu được tính theo thời gian đã đóng 
bảo hiểm xã hội trong đó mỗi năm đóng bảo hiểm xã hội trước năm 2014 được tính bằng 1,5 
tháng lương hưu đang hưởng, mỗi năm đóng bảo hiểm xã hội từ năm 2014 trở đi được tính bằng 
02 tháng lương hưu đang hưởng; sau đó mỗi tháng đã hưởng lương hưu thì mức trợ cấp một lần 
trừ 0,5 tháng lương hưu. Mức thấp nhất bằng 03 tháng lương hưu đang hưởng; 
b) Mức trợ cấp một lần đối với người đang hưởng trợ cấp bảo hiểm xã hội hằng tháng bằng 03 
tháng trợ cấp đang hưởng; 
c) Hồ sơ đề nghị hưởng trợ cấp một lần bao gồm văn bản đề nghị hưởng trợ cấp một lần kèm 
theo bản sao giấy xác nhận của cơ quan có thẩm quyền về việc thôi quốc tịch Việt Nam hoặc bản 
dịch tiếng Việt được chứng thực hoặc công chứng một trong các giấy tờ quy định tại các điểm a, 
b, c và d khoản 2 Điều 106 của Luật này; 
d) Trong thời hạn 07 ngày làm việc kể từ ngày nhận đủ hồ sơ theo quy định, cơ quan bảo hiểm 
xã hội có trách nhiệm giải quyết; trường hợp không giải quyết thì phải trả lời bằng văn bản và 
nêu rõ lý do. 
2. Người đang hưởng lương hưu chuyển đến nơi ở khác trong nước và có nguyện vọng hưởng 
bảo hiểm xã hội ở nơi cư trú mới được thực hiện như sau: 
a) Người đang hưởng lương hưu có nguyện vọng thay đổi hình thức nhận hoặc thay đổi nơi nhận 
do chuyển nơi cư trú trong nước thì có văn bản gửi cơ quan bảo hiểm xã hội nơi đang chi trả; 
b) Trong thời hạn 05 ngày làm việc kể từ ngày nhận được văn bản quy định tại điểm a khoản 
này, cơ quan bảo hiểm xã hội có trách nhiệm giải quyết; trường hợp không giải quyết thì phải trả 
lời bằng văn bản và nêu rõ lý do. 
3. Việc tạm dừng, chấm dứt, tiếp tục hưởng lương hưu được thực hiện theo quy định tại các Điều 
75, 80 và 81 của Luật này. 
Chương VII 
QUỸ BẢO HIỂM XÃ HỘI 
Mục 1. HÌNH THÀNH VÀ SỬ DỤNG QUỸ BẢO HIỂM XÃ HỘI

[RULES]
{"id": "LAB-10-D115-000", "type": "condition", "premises": ["receiving_pension", "emigrating"], "conclusion": "must_submit_application_for_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 115 khoản 1 điểm a", "exception_to": "", "quote": "Người tham gia bảo hiểm xã hội tự nguyện đang hưởng lương hưu ra nước ngoài để định cư nếu có nguyện vọng thì được giải quyết hưởng trợ cấp một lần."}
{"id": "LAB-10-D115-001", "type": "condition", "premises": ["receiving_pension", "emigrating", "started_si_before_2014"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 115 khoản 1 điểm a", "exception_to": "", "quote": "Mỗi năm đóng bảo hiểm xã hội trước năm 2014 được tính bằng 1,5 tháng lương hưu đang hưởng."}
{"id": "LAB-10-D115-002", "type": "condition", "premises": ["receiving_pension", "emigrating", "started_si_after_2014"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 115 khoản 1 điểm a", "exception_to": "", "quote": "Mỗi năm đóng bảo hiểm xã hội từ năm 2014 trở đi được tính bằng 02 tháng lương hưu đang hưởng."}
{"id": "LAB-10-D115-003", "type": "condition", "premises": ["receiving_pension", "emigrating"], "conclusion": "must_respond_in_writing_if_not_approved", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 115 khoản 1 điểm a", "exception_to": "", "quote": "trường hợp không giải quyết thì phải trả lời bằng văn bản và nêu rõ lý do."}
{"id": "LAB-10-D115-004", "type": "condition", "premises": ["receiving_pension", "emigrating"], "conclusion": "must_submit_application_for_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 115 khoản 1 điểm a", "exception_to": "", "quote": "Mức thấp nhất bằng 03 tháng lương hưu đang hưởng."}
{"id": "LAB-10-D115-005", "type": "condition", "premises": ["receiving_pension"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 115 khoản 1 điểm b", "exception_to": "", "quote": "Mức trợ cấp một lần đối với người đang hưởng trợ cấp bảo hiểm xã hội hằng tháng bằng 03 tháng trợ cấp đang hưởng."}
{"id": "LAB-10-D115-006", "type": "condition", "premises": ["receiving_pension"], "conclusion": "must_submit_application_for_change", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 115 khoản 2 điểm a", "exception_to": "", "quote": "Người đang hưởng lương hưu có nguyện vọng thay đổi hình thức nhận hoặc thay đổi nơi nhận do chuyển nơi cư trú trong nước thì có văn bản gửi cơ quan bảo hiểm xã hội nơi đang chi trả."}
{"id": "LAB-10-D115-007", "type": "condition", "premises": ["must_submit_application_for_change"], "conclusion": "must_respond_in_writing_if_not_approved", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 115 khoản 2 điểm b", "exception_to": "", "quote": "trường hợp không giải quyết thì phải trả lời bằng văn bản và nêu rõ lý do."}
{"id": "LAB-10-D115-008", "type": "lookup", "premises": [], "conclusion": "document_copy", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 115 khoản 1", "exception_to": "", "quote": "Hồ sơ đề nghị hưởng trợ cấp một lần bao gồm văn bản đề nghị hưởng trợ cấp một lần kèm theo bản sao giấy xác nhận của cơ quan có thẩm quyền về việc thôi quốc tịch Việt Nam."}
{"id": "LAB-10-D115-009", "type": "condition", "premises": ["receiving_pension"], "conclusion": "other_cases_of_suspend_terminate_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 115 khoản 3", "exception_to": "Điều 75, 80 và 81 của Luật này", "quote": "Việc tạm dừng, chấm dứt, tiếp tục hưởng lương hưu được thực hiện theo quy định tại các Điều 75, 80 và 81 của Luật này."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 116. Quỹ bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 116. Quỹ bảo hiểm xã hội 
1. Quỹ bảo hiểm xã hội là quỹ tài chính độc lập với ngân sách nhà nước; được hạch toán, kế 
toán, lập báo cáo tài chính, kiểm toán nội bộ theo quy định của pháp luật về kế toán và các quy 
định khác của pháp luật có liên quan. 
2. Định kỳ 03 năm, Kiểm toán nhà nước thực hiện kiểm toán quỹ bảo hiểm xã hội, hoạt động đầu 
tư quỹ và báo cáo kết quả với Quốc hội. Theo yêu cầu của Quốc hội, Ủy ban Thường vụ Quốc 
hội và Chính phủ, quỹ bảo hiểm xã hội được kiểm toán đột xuất. 
Trường hợp tiến hành hoạt động thanh tra, hoạt động kiểm toán nhà nước về bảo hiểm xã hội, 
nếu phát hiện chồng chéo, trùng lặp, cơ quan thanh tra phối hợp với cơ quan kiểm toán nhà nước 
xử lý theo quy định của Luật Thanh tra và Luật Kiểm toán nhà nước, bảo đảm một nội dung hoạt 
động của tổ chức, cá nhân chỉ là đối tượng của một cơ quan thanh tra hoặc một cơ quan kiểm 
toán nhà nước; bảo đảm phòng ngừa, phát hiện và xử lý hành vi vi phạm pháp luật về bảo hiểm 
xã hội.

[RULES]
{"id": "LAB-10-D116-000", "type": "condition", "premises": [], "conclusion": "social_insurance_fund_is_independent", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 116 khoản 1", "exception_to": "", "quote": "Quỹ bảo hiểm xã hội là quỹ tài chính độc lập với ngân sách nhà nước."}
{"id": "LAB-10-D116-001", "type": "condition", "premises": [], "conclusion": "social_insurance_fund_is_accounted", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 116 khoản 1", "exception_to": "", "quote": "được hạch toán, kế toán, lập báo cáo tài chính, kiểm toán nội bộ theo quy định của pháp luật về kế toán và các quy định khác của pháp luật có liên quan."}
{"id": "LAB-10-D116-002", "type": "condition", "premises": [], "conclusion": "state_audit_social_insurance_fund_every_3_years", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 116 khoản 2", "exception_to": "", "quote": "Định kỳ 03 năm, Kiểm toán nhà nước thực hiện kiểm toán quỹ bảo hiểm xã hội."}
{"id": "LAB-10-D116-003", "type": "condition", "premises": [], "conclusion": "social_insurance_fund_can_be_audited_unexpectedly", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 116 khoản 2", "exception_to": "", "quote": "quỹ bảo hiểm xã hội được kiểm toán đột xuất."}
{"id": "LAB-10-D116-004", "type": "condition", "premises": ["state_audit_detects_overlap"], "conclusion": "audit_and_inspection_agencies_must_coordinate", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 116 khoản 2", "exception_to": "", "quote": "cơ quan thanh tra phối hợp với cơ quan kiểm toán nhà nước xử lý theo quy định của Luật Thanh tra và Luật Kiểm toán nhà nước."}
{"id": "LAB-10-D116-005", "type": "condition", "premises": ["audit_and_inspection_agencies_must_ensure_single_audit"], "conclusion": "one_activity_only_subject_to_one_agency", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 116 khoản 2", "exception_to": "", "quote": "bảo đảm một nội dung hoạt động của tổ chức, cá nhân chỉ là đối tượng của một cơ quan thanh tra hoặc một cơ quan kiểm toán nhà nước."}
{"id": "LAB-10-D116-006", "type": "condition", "premises": ["audit_and_inspection_agencies_must_prevent_violations"], "conclusion": "ensure_detection_and_handling_of_violations", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 116 khoản 2", "exception_to": "", "quote": "bảo đảm phòng ngừa, phát hiện và xử lý hành vi vi phạm pháp luật về bảo hiểm xã hội."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 117. Các nguồn hình thành quỹ bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 117. Các nguồn hình thành quỹ bảo hiểm xã hội 
1. Người sử dụng lao động đóng theo quy định. 
2. Người lao động đóng theo quy định. 
3. Tiền sinh lời của hoạt động đầu tư quỹ. 
4. Ngân sách nhà nước. 
5. Các nguồn thu hợp pháp khác.

[RULES]
{"id": "LAB-10-D117-000", "type": "condition", "premises": ["~not_registered_si"], "conclusion": "has_full_contribution_time_by_employer", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 117 khoản 1", "exception_to": "", "quote": "Người sử dụng lao động đóng theo quy định."}
{"id": "LAB-10-D117-001", "type": "condition", "premises": ["~not_registered_si"], "conclusion": "has_full_contribution_time_by_state", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 117 khoản 2", "exception_to": "", "quote": "Người lao động đóng theo quy định."}
{"id": "LAB-10-D117-002", "type": "condition", "premises": [], "conclusion": "has_full_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 117 khoản 3", "exception_to": "", "quote": "Tiền sinh lời của hoạt động đầu tư quỹ."}
{"id": "LAB-10-D117-003", "type": "condition", "premises": [], "conclusion": "has_full_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 117 khoản 4", "exception_to": "", "quote": "Ngân sách nhà nước."}
{"id": "LAB-10-D117-004", "type": "condition", "premises": [], "conclusion": "has_full_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 117 khoản 5", "exception_to": "", "quote": "Các nguồn thu hợp pháp khác."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 118. Các quỹ thành phần của quỹ bảo hiểm xã hội, quỹ bảo hiểm thất nghiệp
[NGUYÊN VĂN]
Điều 118. Các quỹ thành phần của quỹ bảo hiểm xã hội, quỹ bảo hiểm thất nghiệp 
1. Quỹ bảo hiểm xã hội bao gồm các quỹ thành phần sau đây: 
a) Quỹ ốm đau và thai sản; 
b) Quỹ hưu trí và tử tuất; 
c) Quỹ bảo hiểm tai nạn lao động - bệnh nghề nghiệp theo quy định của Luật An toàn, vệ sinh 
lao động. 
2. Quỹ bảo hiểm thất nghiệp theo quy định của Luật Việc làm.

[RULES]
{"id": "LAB-10-D118-000", "type": "condition", "premises": [], "conclusion": "social_insurance_funds_includes", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 118 khoản 1", "exception_to": "", "quote": "Quỹ bảo hiểm xã hội bao gồm các quỹ thành phần sau đây"}
{"id": "LAB-10-D118-001", "type": "condition", "premises": [], "conclusion": "includes_sickness_and_maternity_fund", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 118 khoản 1", "exception_to": "", "quote": "Quỹ ốm đau và thai sản"}
{"id": "LAB-10-D118-002", "type": "condition", "premises": [], "conclusion": "includes_pension_and_survivor_fund", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 118 khoản 1", "exception_to": "", "quote": "Quỹ hưu trí và tử tuất"}
{"id": "LAB-10-D118-003", "type": "condition", "premises": [], "conclusion": "includes_accident_insurance_fund", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 118 khoản 1", "exception_to": "", "quote": "Quỹ bảo hiểm tai nạn lao động - bệnh nghề nghiệp theo quy định của Luật An toàn, vệ sinh lao động"}
{"id": "LAB-10-D118-004", "type": "condition", "premises": [], "conclusion": "unemployment_insurance_fund_defined_by_law", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 118 khoản 2", "exception_to": "", "quote": "Quỹ bảo hiểm thất nghiệp theo quy định của Luật Việc làm"}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 119. Sử dụng quỹ bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 119. Sử dụng quỹ bảo hiểm xã hội 
1. Chi trả các chế độ bảo hiểm xã hội bắt buộc và bảo hiểm xã hội tự nguyện cho đối tượng theo 
quy định tại Chương V, Chương VI của Luật này và trợ cấp hằng tháng quy định tại Điều 23 của 
Luật này. 
2. Chi đóng bảo hiểm y tế cho các đối tượng sau đây: 
a) Người đang hưởng lương hưu; 
b) Người nghỉ việc hưởng trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng tháng; 
c) Người nghỉ việc hưởng chế độ thai sản từ 14 ngày làm việc trở lên trong tháng; 
d) Nghỉ việc hưởng trợ cấp ốm đau đối với người lao động bị mắc bệnh thuộc danh mục bệnh 
cần chữa trị dài ngày do Bộ trưởng Bộ Y tế ban hành; 
đ) Người lao động nghỉ việc hưởng chế độ ốm đau từ 14 ngày làm việc trở lên trong tháng. 
3. Chi trả phí khám giám định mức suy giảm khả năng lao động đối với trường hợp không do 
người sử dụng lao động giới thiệu đi khám giám định mức suy giảm khả năng lao động mà kết 
quả giám định đủ điều kiện hưởng chế độ bảo hiểm xã hội. 
4. Chi tổ chức và hoạt động bảo hiểm xã hội theo quy định tại Điều 120 của Luật này. 
5. Đầu tư để bảo toàn và tăng trưởng quỹ theo quy định tại Mục 2 Chương này.

[RULES]
{"id": "LAB-10-D119-000", "type": "condition", "premises": ["compulsory_si", "voluntary_si_eligible"], "conclusion": "receive_full_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 119 khoản 1", "exception_to": "", "quote": "Chi trả các chế độ bảo hiểm xã hội bắt buộc và bảo hiểm xã hội tự nguyện cho đối tượng theo quy định tại Chương V, Chương VI của Luật này."}
{"id": "LAB-10-D119-001", "type": "condition", "premises": ["receiving_pension"], "conclusion": "receive_health_insurance", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 119 khoản 2 điểm a", "exception_to": "", "quote": "Chi đóng bảo hiểm y tế cho các đối tượng sau đây: a) Người đang hưởng lương hưu;"}
{"id": "LAB-10-D119-002", "type": "condition", "premises": ["unpaid_14_days"], "conclusion": "receive_health_insurance", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 119 khoản 2 điểm b", "exception_to": "", "quote": "b) Người nghỉ việc hưởng trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng tháng;"}
{"id": "LAB-10-D119-003", "type": "condition", "premises": ["unpaid_14_days"], "conclusion": "receive_health_insurance", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 119 khoản 2 điểm c", "exception_to": "", "quote": "c) Người nghỉ việc hưởng chế độ thai sản từ 14 ngày làm việc trở lên trong tháng;"}
{"id": "LAB-10-D119-004", "type": "condition", "premises": ["health_not_recovered_after_long_illness"], "conclusion": "receive_health_insurance", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 119 khoản 2 điểm d", "exception_to": "", "quote": "d) Nghỉ việc hưởng trợ cấp ốm đau đối với người lao động bị mắc bệnh thuộc danh mục bệnh cần chữa trị dài ngày do Bộ trưởng Bộ Y tế ban hành;"}
{"id": "LAB-10-D119-005", "type": "condition", "premises": ["unpaid_14_days"], "conclusion": "receive_health_insurance", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 119 khoản 2 điểm đ", "exception_to": "", "quote": "đ) Người lao động nghỉ việc hưởng chế độ ốm đau từ 14 ngày làm việc trở lên trong tháng."}
{"id": "LAB-10-D119-006", "type": "condition", "premises": ["medical_exam_procedure", "~not_paid_si_after_60_days"], "conclusion": "medical_exam_payment", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 119 khoản 3", "exception_to": "", "quote": "Chi trả phí khám giám định mức suy giảm khả năng lao động đối với trường hợp không do người sử dụng lao động giới thiệu đi khám giám định mức suy giảm khả năng lao động mà kết quả giám định đủ điều kiện hưởng chế độ bảo hiểm xã hội."}
{"id": "LAB-10-D119-007", "type": "condition", "premises": [], "conclusion": "manage_social_insurance_funds", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 119 khoản 4", "exception_to": "", "quote": "Chi tổ chức và hoạt động bảo hiểm xã hội theo quy định tại Điều 120 của Luật này."}
{"id": "LAB-10-D119-008", "type": "condition", "premises": [], "conclusion": "invest_social_insurance_funds", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 119 khoản 5", "exception_to": "", "quote": "Đầu tư để bảo toàn và tăng trưởng quỹ theo quy định tại Mục 2 Chương này."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 120. Chi tổ chức và hoạt động bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 120. Chi tổ chức và hoạt động bảo hiểm xã hội 
1. Chi tổ chức và hoạt động bảo hiểm xã hội được sử dụng để thực hiện các nhiệm vụ sau đây: 
a) Tuyên truyền, phổ biến, giải đáp, tư vấn chính sách, pháp luật về bảo hiểm xã hội; tập huấn, 
bồi dưỡng chuyên môn, nghiệp vụ về bảo hiểm xã hội; 
b) Cải cách hành chính bảo hiểm xã hội; phát triển, quản lý người tham gia, người thụ hưởng chế 
độ bảo hiểm xã hội; 
c) Đầu tư, nâng cấp, cải tạo, mở rộng, bảo dưỡng, sửa chữa tài sản, thuê, mua sắm tài sản, hàng 
hóa, dịch vụ liên quan đến quản lý và hoạt động bảo hiểm xã hội; 
d) Tổ chức thu, chi trả bảo hiểm xã hội và hoạt động bộ máy của cơ quan bảo hiểm xã hội các 
cấp, Hội đồng quản lý bảo hiểm xã hội. 
2. Mức chi tổ chức và hoạt động bảo hiểm xã hội được tính trên cơ sở số phần trăm của dự toán 
thu, chi bảo hiểm xã hội, không bao gồm số chi đóng bảo hiểm y tế cho người hưởng các chế độ 
bảo hiểm xã hội và được trích từ tiền sinh lời của hoạt động đầu tư quỹ bảo hiểm xã hội. 
3. Định kỳ 03 năm, Chính phủ báo cáo Ủy ban Thường vụ Quốc hội quyết định về mức chi tổ 
chức và hoạt động bảo hiểm xã hội. 
4. Kiểm toán nhà nước thực hiện kiểm toán hằng năm đối với báo cáo quyết toán chi tổ chức và 
hoạt động bảo hiểm xã hội. 
5. Chính phủ quy định chi tiết khoản 1 và khoản 2 Điều này. 
Mục 2. ĐẦU TƯ QUỸ BẢO HIỂM XÃ HỘI

[RULES]
{"id": "LAB-10-D120-000", "type": "condition", "premises": [], "conclusion": "promote_social_insurance_law", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 120 khoản 1 điểm a", "exception_to": "", "quote": "Tuyên truyền, phổ biến, giải đáp, tư vấn chính sách, pháp luật về bảo hiểm xã hội"}
{"id": "LAB-10-D120-001", "type": "condition", "premises": [], "conclusion": "government_regulates_agency_structure", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 120 khoản 1 điểm b", "exception_to": "", "quote": "Cải cách hành chính bảo hiểm xã hội; phát triển, quản lý người tham gia, người thụ hưởng chế độ bảo hiểm xã hội"}
{"id": "LAB-10-D120-002", "type": "condition", "premises": [], "conclusion": "manage_social_insurance_funds", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 120 khoản 1 điểm c", "exception_to": "", "quote": "Đầu tư, nâng cấp, cải tạo, mở rộng, bảo dưỡng, sửa chữa tài sản, thuê, mua sắm tài sản, hàng hóa, dịch vụ liên quan đến quản lý và hoạt động bảo hiểm xã hội"}
{"id": "LAB-10-D120-003", "type": "condition", "premises": [], "conclusion": "social_insurance_agency", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 120 khoản 1 điểm d", "exception_to": "", "quote": "Tổ chức thu, chi trả bảo hiểm xã hội và hoạt động bộ máy của cơ quan bảo hiểm xã hội các cấp, Hội đồng quản lý bảo hiểm xã hội"}
{"id": "LAB-10-D120-004", "type": "condition", "premises": [], "conclusion": "government_regulates_si_calculation", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 120 khoản 2", "exception_to": "", "quote": "Mức chi tổ chức và hoạt động bảo hiểm xã hội được tính trên cơ sở số phần trăm của dự toán thu, chi bảo hiểm xã hội"}
{"id": "LAB-10-D120-005", "type": "condition", "premises": [], "conclusion": "government_regulates_si_calculation", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 120 khoản 3", "exception_to": "", "quote": "Định kỳ 03 năm, Chính phủ báo cáo Ủy ban Thường vụ Quốc hội quyết định về mức chi tổ chức và hoạt động bảo hiểm xã hội"}
{"id": "LAB-10-D120-006", "type": "condition", "premises": [], "conclusion": "conduct_specialized_inspection", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 120 khoản 4", "exception_to": "", "quote": "Kiểm toán nhà nước thực hiện kiểm toán hằng năm đối với báo cáo quyết toán chi tổ chức và hoạt động bảo hiểm xã hội"}
{"id": "LAB-10-D120-007", "type": "condition", "premises": [], "conclusion": "government_regulates_si_calculation", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 120 khoản 5", "exception_to": "", "quote": "Chính phủ quy định chi tiết khoản 1 và khoản 2 Điều này"}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 121. Nguyên tắc đầu tư
[NGUYÊN VĂN]
Điều 121. Nguyên tắc đầu tư 
1. Hoạt động đầu tư quỹ bảo hiểm xã hội phải bảo đảm an toàn, bền vững và hiệu quả. 
2. Đa dạng hóa danh mục đầu tư, cơ cấu và phương thức đầu tư phù hợp với năng lực và cơ sở 
vật chất của tổ chức đầu tư quỹ bảo hiểm xã hội; ưu tiên đầu tư vào trái phiếu Chính phủ, nhất là 
trái phiếu Chính phủ dài hạn. 
3. Hoạt động đầu tư quỹ bảo hiểm xã hội thực hiện theo chiến lược đầu tư dài hạn và phương án 
đầu tư hằng năm.

[RULES]
{"id": "LAB-10-D121-000", "type": "condition", "premises": [], "conclusion": "must_ensure_investment_safety", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 121 khoản 1", "exception_to": "", "quote": "Hoạt động đầu tư quỹ bảo hiểm xã hội phải bảo đảm an toàn, bền vững và hiệu quả."}
{"id": "LAB-10-D121-001", "type": "condition", "premises": [], "conclusion": "must_diversify_investment_portfolio", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 121 khoản 2", "exception_to": "", "quote": "Đa dạng hóa danh mục đầu tư, cơ cấu và phương thức đầu tư phù hợp với năng lực và cơ sở vật chất của tổ chức đầu tư quỹ bảo hiểm xã hội."}
{"id": "LAB-10-D121-002", "type": "condition", "premises": [], "conclusion": "prioritize_government_bonds", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 121 khoản 2", "exception_to": "", "quote": "ưu tiên đầu tư vào trái phiếu Chính phủ, nhất là trái phiếu Chính phủ dài hạn."}
{"id": "LAB-10-D121-003", "type": "condition", "premises": [], "conclusion": "must_follow_long_term_investment_strategy", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 121 khoản 3", "exception_to": "", "quote": "Hoạt động đầu tư quỹ bảo hiểm xã hội thực hiện theo chiến lược đầu tư dài hạn và phương án đầu tư hằng năm."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 122. Danh mục đầu tư và phương thức đầu tư
[NGUYÊN VĂN]
Điều 122. Danh mục đầu tư và phương thức đầu tư 
1. Danh mục đầu tư quỹ bảo hiểm xã hội tại thị trường trong nước bao gồm: 
a) Công cụ nợ của Chính phủ, bao gồm trái phiếu Chính phủ, tín phiếu Kho bạc Nhà nước, công 
trái xây dựng Tổ quốc; 
b) Trái phiếu chính quyền địa phương, trái phiếu được Chính phủ bảo lãnh; 
c) Tiền gửi tại các ngân hàng thương mại nhà nước và ngân hàng thương mại cổ phần có vốn nhà 
nước trên 50% vốn điều lệ; không thực hiện đầu tư quỹ bảo hiểm xã hội tại các ngân hàng 
thương mại đang được kiểm soát đặc biệt; 
d) Trái phiếu, chứng chỉ tiền gửi của các ngân hàng thương mại nhà nước và ngân hàng thương 
mại cổ phần có vốn nhà nước trên 50% vốn điều lệ; không thực hiện đầu tư quỹ bảo hiểm xã hội 
tại các ngân hàng thương mại đang được kiểm soát đặc biệt. 
2. Đầu tư quỹ bảo hiểm xã hội tại thị trường quốc tế là trái phiếu Chính phủ. 
3. Phương thức đầu tư quỹ bảo hiểm xã hội bao gồm tự đầu tư, ủy thác đầu tư tại thị trường trong 
nước, thị trường quốc tế. 
4. Chính phủ quy định lộ trình đa dạng hóa, tiêu chí danh mục đầu tư, cơ cấu đầu tư và phương 
thức đầu tư quỹ bảo hiểm xã hội, bảo đảm nguyên tắc quy định tại Điều 121 của Luật này.

[RULES]
{"id": "LAB-10-D122-000", "type": "condition", "premises": ["is_government_debt_investment"], "conclusion": "social_insurance_investment_includes_government_debt", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 122 khoản 1 điểm a", "exception_to": "", "quote": "Danh mục đầu tư quỹ bảo hiểm xã hội tại thị trường trong nước bao gồm: Công cụ nợ của Chính phủ, bao gồm trái phiếu Chính phủ..."}
{"id": "LAB-10-D122-001", "type": "condition", "premises": ["is_local_government_bond_investment"], "conclusion": "social_insurance_investment_includes_local_government_bonds", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 122 khoản 1 điểm b", "exception_to": "", "quote": "Danh mục đầu tư quỹ bảo hiểm xã hội tại thị trường trong nước bao gồm: Trái phiếu chính quyền địa phương..."}
{"id": "LAB-10-D122-002", "type": "condition", "premises": ["is_state_bank_investment", "not_invest_in_special_control_bank"], "conclusion": "social_insurance_investment_includes_state_banks", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 122 khoản 1 điểm c", "exception_to": "", "quote": "Tiền gửi tại các ngân hàng thương mại nhà nước và ngân hàng thương mại cổ phần có vốn nhà nước trên 50% vốn điều lệ; không thực hiện đầu tư quỹ bảo hiểm xã hội tại các ngân hàng thương mại đang được kiểm soát đặc biệt."}
{"id": "LAB-10-D122-003", "type": "condition", "premises": ["is_state_bank_investment", "not_invest_in_special_control_bank"], "conclusion": "social_insurance_investment_includes_state_bank_bonds", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 122 khoản 1 điểm d", "exception_to": "", "quote": "Trái phiếu, chứng chỉ tiền gửi của các ngân hàng thương mại nhà nước và ngân hàng thương mại cổ phần có vốn nhà nước trên 50% vốn điều lệ; không thực hiện đầu tư quỹ bảo hiểm xã hội tại các ngân hàng thương mại đang được kiểm soát đặc biệt."}
{"id": "LAB-10-D122-004", "type": "condition", "premises": [], "conclusion": "social_insurance_investment_includes_international_government_bonds", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 122 khoản 2", "exception_to": "", "quote": "Đầu tư quỹ bảo hiểm xã hội tại thị trường quốc tế là trái phiếu Chính phủ."}
{"id": "LAB-10-D122-005", "type": "condition", "premises": [], "conclusion": "social_insurance_investment_methods_includes_self_and_trust_investment", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 122 khoản 3", "exception_to": "", "quote": "Phương thức đầu tư quỹ bảo hiểm xã hội bao gồm tự đầu tư, ủy thác đầu tư tại thị trường trong nước, thị trường quốc tế."}
{"id": "LAB-10-D122-006", "type": "condition", "premises": [], "conclusion": "government_regulates_investment_diversification", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 122 khoản 4", "exception_to": "", "quote": "Chính phủ quy định lộ trình đa dạng hóa, tiêu chí danh mục đầu tư, cơ cấu đầu tư và phương thức đầu tư quỹ bảo hiểm xã hội..."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 123. Quản lý hoạt động đầu tư quỹ bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 123. Quản lý hoạt động đầu tư quỹ bảo hiểm xã hội 
1. Quỹ bảo hiểm xã hội được đầu tư và hạch toán độc lập theo từng quỹ thành phần. 
2. Hoạt động đầu tư quỹ phải được kiểm soát, quản lý rủi ro và trích lập dự phòng rủi ro. 
3. Chính phủ quy định quy trình kiểm soát, quản lý rủi ro đầu tư, trích lập và sử dụng dự phòng 
rủi ro. 
Chương VIII 
BẢO HIỂM HƯU TRÍ BỔ SUNG

[RULES]
{"id": "LAB-10-D123-000", "type": "condition", "premises": [], "conclusion": "social_insurance_funds_includes", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 123 khoản 1", "exception_to": "", "quote": "Quỹ bảo hiểm xã hội được đầu tư và hạch toán độc lập theo từng quỹ thành phần."}
{"id": "LAB-10-D123-001", "type": "condition", "premises": [], "conclusion": "must_ensure_conditions_for_electronic_transaction_by_2027", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 123 khoản 2", "exception_to": "", "quote": "Hoạt động đầu tư quỹ phải được kiểm soát, quản lý rủi ro và trích lập dự phòng rủi ro."}
{"id": "LAB-10-D123-002", "type": "condition", "premises": [], "conclusion": "government_regulates_risk_management_process", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 123 khoản 3", "exception_to": "", "quote": "Chính phủ quy định quy trình kiểm soát, quản lý rủi ro đầu tư, trích lập và sử dụng dự phòng rủi ro."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 124. Đối tượng tham gia bảo hiểm hưu trí bổ sung
[NGUYÊN VĂN]
Điều 124. Đối tượng tham gia bảo hiểm hưu trí bổ sung 
Đối tượng tham gia bảo hiểm hưu trí bổ sung là người sử dụng lao động và người lao động.

[RULES]
{"id": "LAB-10-D124-000", "type": "condition", "premises": ["employer_participant", "employee_participant"], "conclusion": "supplementary_pension_insurance", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 124", "exception_to": "", "quote": "Đối tượng tham gia bảo hiểm hưu trí bổ sung là người sử dụng lao động và người lao động."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 125. Nguyên tắc bảo hiểm hưu trí bổ sung
[NGUYÊN VĂN]
Điều 125. Nguyên tắc bảo hiểm hưu trí bổ sung 
1. Mức đóng bảo hiểm hưu trí bổ sung do người sử dụng lao động và người lao động tự nguyện 
thỏa thuận. 
2. Khoản đóng góp vào quỹ bảo hiểm hưu trí bổ sung được quản lý theo từng tài khoản hưu trí cá 
nhân. 
3. Hoạt động quản lý quỹ bảo hiểm hưu trí bổ sung thực hiện theo nguyên tắc công khai, minh 
bạch và phải bảo đảm đầu tư theo đúng quy định của pháp luật. 
4. Mức chi trả bảo hiểm hưu trí bổ sung được xác định trên cơ sở số dư tài khoản hưu trí cá nhân 
tại thời điểm chi trả, được tích lũy thông qua hoạt động đầu tư quỹ bảo hiểm hưu trí bổ sung theo 
nguyên tắc thị trường.

[RULES]
{"id": "LAB-10-D125-000", "type": "condition", "premises": ["agreed_contribution"], "conclusion": "supplementary_pension_insurance", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 125 khoản 1", "exception_to": "", "quote": "Mức đóng bảo hiểm hưu trí bổ sung do người sử dụng lao động và người lao động tự nguyện thỏa thuận."}
{"id": "LAB-10-D125-001", "type": "condition", "premises": [], "conclusion": "under_management", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 125 khoản 2", "exception_to": "", "quote": "Khoản đóng góp vào quỹ bảo hiểm hưu trí bổ sung được quản lý theo từng tài khoản hưu trí cá nhân."}
{"id": "LAB-10-D125-002", "type": "condition", "premises": [], "conclusion": "must_follow_long_term_investment_strategy", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 125 khoản 3", "exception_to": "", "quote": "Hoạt động quản lý quỹ bảo hiểm hưu trí bổ sung thực hiện theo nguyên tắc công khai, minh bạch và phải bảo đảm đầu tư theo đúng quy định của pháp luật."}
{"id": "LAB-10-D125-003", "type": "condition", "premises": ["time_of_contribution"], "conclusion": "receive_pension_through_employer", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 125 khoản 4", "exception_to": "", "quote": "Mức chi trả bảo hiểm hưu trí bổ sung được xác định trên cơ sở số dư tài khoản hưu trí cá nhân tại thời điểm chi trả."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 126. Quỹ bảo hiểm hưu trí bổ sung
[NGUYÊN VĂN]
Điều 126. Quỹ bảo hiểm hưu trí bổ sung 
1. Quỹ bảo hiểm hưu trí bổ sung là quỹ tài chính độc lập với ngân sách nhà nước; được hạch 
toán, kế toán, lập báo cáo tài chính, kiểm toán theo quy định của pháp luật về kế toán và pháp 
luật về kiểm toán. 
2. Nguồn hình thành quỹ bảo hiểm hưu trí bổ sung bao gồm đóng góp của người sử dụng lao 
động, người lao động và tiền sinh lời của hoạt động đầu tư của quỹ. 
3. Quỹ bảo hiểm hưu trí bổ sung được sử dụng để chi trả chế độ hưu trí bổ sung cho người lao 
động, chi phí tổ chức và hoạt động quản lý.

[RULES]
{"id": "LAB-10-D126-000", "type": "condition", "premises": ["social_insurance_fund_is_independent"], "conclusion": "social_insurance_fund_is_accounted", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 126 khoản 1", "exception_to": "", "quote": "Quỹ bảo hiểm hưu trí bổ sung là quỹ tài chính độc lập với ngân sách nhà nước; được hạch toán, kế toán, lập báo cáo tài chính, kiểm toán theo quy định của pháp luật về kế toán và pháp luật về kiểm toán."}
{"id": "LAB-10-D126-001", "type": "condition", "premises": ["has_full_contribution_time", "has_full_contribution_time_by_employer"], "conclusion": "supplementary_pension_insurance", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 126 khoản 2", "exception_to": "", "quote": "Nguồn hình thành quỹ bảo hiểm hưu trí bổ sung bao gồm đóng góp của người sử dụng lao động, người lao động và tiền sinh lời của hoạt động đầu tư của quỹ."}
{"id": "LAB-10-D126-002", "type": "condition", "premises": [], "conclusion": "supplementary_pension_insurance", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 126 khoản 3", "exception_to": "", "quote": "Quỹ bảo hiểm hưu trí bổ sung được sử dụng để chi trả chế độ hưu trí bổ sung cho người lao động, chi phí tổ chức và hoạt động quản lý."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 127. Chính sách của Nhà nước đối với bảo hiểm hưu trí bổ sung
[NGUYÊN VĂN]
Điều 127. Chính sách của Nhà nước đối với bảo hiểm hưu trí bổ sung 
1. Khuyến khích phát triển bảo hiểm hưu trí bổ sung thông qua các chính sách ưu đãi theo quy 
định của pháp luật về thuế. 
2. Hoàn thiện pháp luật và chính sách về bảo hiểm hưu trí bổ sung, tổ chức thực hiện chính sách 
bảo hiểm hưu trí bổ sung chuyên nghiệp, hiện đại, minh bạch; tạo điều kiện cho người sử dụng 
lao động và người lao động có thêm sự lựa chọn tham gia đóng góp để được hưởng mức lương 
hưu cao hơn. 
3. Chính phủ quy định về bảo hiểm hưu trí bổ sung. 
Chương IX 
KHIẾU NẠI, TỐ CÁO VÀ XỬ LÝ VI PHẠM VỀ BẢO HIỂM XÃ HỘI

[RULES]
{"id": "LAB-10-D127-000", "type": "condition", "premises": [], "conclusion": "encourage_compliance_with_law", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 127 khoản 1", "exception_to": "", "quote": "Khuyến khích phát triển bảo hiểm hưu trí bổ sung thông qua các chính sách ưu đãi theo quy định của pháp luật về thuế."}
{"id": "LAB-10-D127-001", "type": "condition", "premises": ["has_full_contribution_time_by_state"], "conclusion": "supplementary_pension_insurance", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 127 khoản 2", "exception_to": "", "quote": "Hoàn thiện pháp luật và chính sách về bảo hiểm hưu trí bổ sung, tổ chức thực hiện chính sách bảo hiểm hưu trí bổ sung chuyên nghiệp, hiện đại, minh bạch; tạo điều kiện cho người sử dụng lao động và người lao động có thêm sự lựa chọn tham gia đóng góp để được hưởng mức lương hưu cao hơn."}
{"id": "LAB-10-D127-002", "type": "condition", "premises": [], "conclusion": "government_regulates_agency_structure", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 127 khoản 3", "exception_to": "", "quote": "Chính phủ quy định về bảo hiểm hưu trí bổ sung."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 128. Quyền khiếu nại về bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 128. Quyền khiếu nại về bảo hiểm xã hội 
Cá nhân, cơ quan, tổ chức có quyền đề nghị cơ quan, tổ chức, cá nhân có thẩm quyền xem xét lại 
quyết định, hành vi của cơ quan, tổ chức, cá nhân khi có căn cứ cho rằng quyết định, hành vi đó 
là trái pháp luật về bảo hiểm xã hội, xâm phạm đến quyền và lợi ích hợp pháp của mình.

[RULES]
{"id": "LAB-10-D128-000", "type": "condition", "premises": ["has_request_document", "received_request_document"], "conclusion": "can_file_complaint_si", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 128 khoản 1", "exception_to": "", "quote": "Cá nhân, cơ quan, tổ chức có quyền đề nghị cơ quan, tổ chức, cá nhân có thẩm quyền xem xét lại quyết định, hành vi của cơ quan, tổ chức, cá nhân khi có căn cứ cho rằng quyết định, hành vi đó là trái pháp luật về bảo hiểm xã hội, xâm phạm đến quyền và lợi ích hợp pháp của mình."}
{"id": "LAB-10-D128-001", "type": "condition", "premises": ["has_request_document", "received_request_document", "is_defense_worker"], "conclusion": "can_file_complaint_si", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 128 khoản 1", "exception_to": "", "quote": "Cá nhân, cơ quan, tổ chức có quyền đề nghị cơ quan, tổ chức, cá nhân có thẩm quyền xem xét lại quyết định, hành vi của cơ quan, tổ chức, cá nhân khi có căn cứ cho rằng quyết định, hành vi đó là trái pháp luật về bảo hiểm xã hội, xâm phạm đến quyền và lợi ích hợp pháp của mình."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 129. Khiếu nại và giải quyết khiếu nại đối với quyết định hành chính, hành vi hành
[NGUYÊN VĂN]
Điều 129. Khiếu nại và giải quyết khiếu nại đối với quyết định hành chính, hành vi hành 
chính về bảo hiểm xã hội của cơ quan hành chính nhà nước, cơ quan bảo hiểm xã hội và 
người có thẩm quyền trong cơ quan hành chính nhà nước, cơ quan bảo hiểm xã hội 
1. Việc khiếu nại và giải quyết khiếu nại đối với quyết định hành chính, hành vi hành chính về 
bảo hiểm xã hội của cơ quan hành chính nhà nước, người có thẩm quyền trong cơ quan hành 
chính nhà nước; việc khiếu nại và giải quyết khiếu nại đối với quyết định xử phạt vi phạm hành 
chính của cơ quan bảo hiểm xã hội, người có thẩm quyền trong cơ quan bảo hiểm xã hội được 
thực hiện theo quy định của pháp luật về khiếu nại, trừ trường hợp quy định tại khoản 2 Điều 
này. 
2. Việc khiếu nại và giải quyết khiếu nại đối với quyết định, hành vi trong hoạt động thanh tra về 
bảo hiểm xã hội được thực hiện theo quy định của pháp luật về thanh tra.

[RULES]
{"id": "LAB-10-D129-000", "type": "condition", "premises": ["social_insurance_agency", "is_responsible_for_decisions"], "conclusion": "can_file_complaint_si", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 129 khoản 1", "exception_to": "", "quote": "Việc khiếu nại và giải quyết khiếu nại đối với quyết định hành chính, hành vi hành chính về bảo hiểm xã hội của cơ quan hành chính nhà nước, người có thẩm quyền trong cơ quan hành chính nhà nước..."}
{"id": "LAB-10-D129-001", "type": "condition", "premises": ["social_insurance_agency", "is_responsible_for_decisions"], "conclusion": "can_file_complaint_si", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 129 khoản 1", "exception_to": "", "quote": "Việc khiếu nại và giải quyết khiếu nại đối với quyết định xử phạt vi phạm hành chính của cơ quan bảo hiểm xã hội, người có thẩm quyền trong cơ quan bảo hiểm xã hội..."}
{"id": "LAB-10-D129-002", "type": "condition", "premises": ["social_insurance_agency"], "conclusion": "must_follow_long_term_investment_strategy", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 129 khoản 2", "exception_to": "", "quote": "Việc khiếu nại và giải quyết khiếu nại đối với quyết định, hành vi trong hoạt động thanh tra về bảo hiểm xã hội được thực hiện theo quy định của pháp luật về thanh tra."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 130. Khiếu nại và giải quyết khiếu nại đối với quyết định, hành vi về bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 130. Khiếu nại và giải quyết khiếu nại đối với quyết định, hành vi về bảo hiểm xã hội 
1. Quyết định về bảo hiểm xã hội là văn bản do cơ quan bảo hiểm xã hội, người có thẩm quyền 
trong cơ quan bảo hiểm xã hội ban hành để thực hiện quy định của pháp luật về bảo hiểm xã hội. 
2. Hành vi về bảo hiểm xã hội là hành vi của cơ quan bảo hiểm xã hội, người có thẩm quyền 
trong cơ quan bảo hiểm xã hội thực hiện hoặc không thực hiện trách nhiệm theo quy định của 
pháp luật về bảo hiểm xã hội. 
3. Trình tự khiếu nại đối với quyết định, hành vi về bảo hiểm xã hội được thực hiện như sau, trừ 
trường hợp quy định tại khoản 5 Điều này: 
a) Khi có căn cứ cho rằng quyết định, hành vi về bảo hiểm xã hội là trái pháp luật, xâm phạm 
quyền, lợi ích hợp pháp của mình thì người khiếu nại khiếu nại lần đầu đến người đã ra quyết 
định hoặc cơ quan bảo hiểm xã hội nơi người có hành vi về bảo hiểm xã hội hoặc khởi kiện tại 
Tòa án theo quy định của pháp luật; 
b) Trường hợp người khiếu nại không đồng ý với quyết định giải quyết khiếu nại lần đầu hoặc 
hết thời hạn quy định mà khiếu nại không được giải quyết thì có quyền khiếu nại lần hai đến Thủ 
trưởng cơ quan bảo hiểm xã hội cấp trên trực tiếp của người có thẩm quyền giải quyết khiếu nại 
lần đầu hoặc khởi kiện tại Tòa án theo quy định của pháp luật. 
Trường hợp người khiếu nại không đồng ý với quyết định giải quyết khiếu nại lần đầu của Thủ 
trưởng cơ quan Bảo hiểm xã hội Việt Nam hoặc hết thời hạn quy định mà khiếu nại không được 
giải quyết thì có quyền khởi kiện tại Tòa án theo quy định của pháp luật; 
c) Trường hợp người khiếu nại không đồng ý với quyết định giải quyết khiếu nại lần hai hoặc hết 
thời hạn quy định mà khiếu nại không được giải quyết thì có quyền khởi kiện tại Tòa án theo quy 
định của pháp luật. 
4. Thẩm quyền giải quyết khiếu nại đối với quyết định, hành vi về bảo hiểm xã hội của cơ quan 
bảo hiểm xã hội được quy định như sau, trừ trường hợp quy định tại khoản 5 Điều này: 
a) Thủ trưởng cơ quan bảo hiểm xã hội có thẩm quyền giải quyết khiếu nại lần đầu đối với quyết 
định, hành vi về bảo hiểm xã hội của mình, của người có thẩm quyền do mình quản lý trực tiếp; 
b) Thủ trưởng cơ quan bảo hiểm xã hội cấp trên trực tiếp có thẩm quyền giải quyết khiếu nại lần 
hai đối với quyết định, hành vi về bảo hiểm xã hội đã được Thủ trưởng cơ quan bảo hiểm xã hội 
cấp dưới giải quyết lần đầu nhưng còn khiếu nại hoặc khiếu nại lần đầu đã hết thời hạn nhưng 
chưa được giải quyết. 
5. Việc giải quyết khiếu nại đối với quyết định, hành vi có liên quan đến việc thụ hưởng các chế 
độ bảo hiểm xã hội hoặc tính thời gian công tác trong khu vực nhà nước để hưởng bảo hiểm xã 
hội trước ngày 01 tháng 01 năm 1995 mà không đủ hồ sơ gốc, không còn hồ sơ gốc hoặc không 
còn cơ quan, đơn vị trực tiếp quản lý người lao động được thực hiện như sau: 
a) Thủ trưởng cơ quan bảo hiểm xã hội cấp tỉnh giải quyết khiếu nại lần đầu; 
b) Trường hợp người khiếu nại không đồng ý với việc giải quyết khiếu nại lần đầu của Thủ 
trưởng cơ quan bảo hiểm xã hội cấp tỉnh hoặc hết thời hạn quy định mà khiếu nại không được 
giải quyết thì có quyền khiếu nại đến Chủ tịch Ủy ban nhân dân cấp tỉnh hoặc khởi kiện tại Tòa 
án theo quy định của pháp luật; 
c) Trường hợp người khiếu nại không đồng ý với việc giải quyết khiếu nại lần hai của Chủ tịch 
Ủy ban nhân dân cấp tỉnh hoặc hết thời hạn quy định mà khiếu nại không được giải quyết thì có 
quyền khởi kiện tại Tòa án theo quy định của pháp luật. 
6. Thời hiệu khiếu nại, trình tự, thủ tục giải quyết khiếu nại về bảo hiểm xã hội được thực hiện 
theo quy định của pháp luật về khiếu nại. 
7. Chính phủ quy định chi tiết Điều này.

[RULES]
{"id": "LAB-10-D130-000", "type": "condition", "premises": ["decision_is_illegal", "has_legal_interest"], "conclusion": "can_file_complaint_first_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 130 khoản 3 điểm a", "exception_to": "", "quote": "Khi có căn cứ cho rằng quyết định, hành vi về bảo hiểm xã hội là trái pháp luật, xâm phạm quyền, lợi ích hợp pháp của mình thì người khiếu nại khiếu nại lần đầu..."}
{"id": "LAB-10-D130-001", "type": "condition", "premises": ["disagree_with_first_decision", "complaint_not_resolved_in_time"], "conclusion": "can_file_complaint_second_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 130 khoản 3 điểm b", "exception_to": "", "quote": "Trường hợp người khiếu nại không đồng ý với quyết định giải quyết khiếu nại lần đầu hoặc hết thời hạn quy định mà khiếu nại không được giải quyết thì có quyền khiếu nại lần hai..."}
{"id": "LAB-10-D130-002", "type": "condition", "premises": ["disagree_with_second_decision", "complaint_not_resolved_in_time"], "conclusion": "can_file_lawsuit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 130 khoản 3 điểm c", "exception_to": "", "quote": "Trường hợp người khiếu nại không đồng ý với quyết định giải quyết khiếu nại lần hai hoặc hết thời hạn quy định mà khiếu nại không được giải quyết thì có quyền khởi kiện tại Tòa án theo quy định của pháp luật."}
{"id": "LAB-10-D130-003", "type": "condition", "premises": ["is_head_of_agency", "is_first_time_complaint"], "conclusion": "has_authority_to_resolve_first_complaint", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 130 khoản 4 điểm a", "exception_to": "", "quote": "Thủ trưởng cơ quan bảo hiểm xã hội có thẩm quyền giải quyết khiếu nại lần đầu đối với quyết định, hành vi về bảo hiểm xã hội của mình..."}
{"id": "LAB-10-D130-004", "type": "condition", "premises": ["is_superior_head", "is_second_time_complaint"], "conclusion": "has_authority_to_resolve_second_complaint", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 130 khoản 4 điểm b", "exception_to": "", "quote": "Thủ trưởng cơ quan bảo hiểm xã hội cấp trên trực tiếp có thẩm quyền giải quyết khiếu nại lần hai đối với quyết định, hành vi về bảo hiểm xã hội đã được Thủ trưởng cơ quan bảo hiểm xã hội cấp dưới giải quyết lần đầu..."}
{"id": "LAB-10-D130-005", "type": "condition", "premises": ["is_head_of_provincial_agency", "is_first_time_complaint_for_old_cases"], "conclusion": "has_authority_to_resolve_first_complaint_old_cases", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 130 khoản 5 điểm a", "exception_to": "", "quote": "Thủ trưởng cơ quan bảo hiểm xã hội cấp tỉnh giải quyết khiếu nại lần đầu..."}
{"id": "LAB-10-D130-006", "type": "condition", "premises": ["disagree_with_provincial_decision", "complaint_not_resolved_in_time"], "conclusion": "can_file_complaint_to_provincial_chairman", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 130 khoản 5 điểm b", "exception_to": "", "quote": "Trường hợp người khiếu nại không đồng ý với việc giải quyết khiếu nại lần đầu của Thủ trưởng cơ quan bảo hiểm xã hội cấp tỉnh hoặc hết thời hạn quy định mà khiếu nại không được giải quyết thì có quyền khiếu nại đến Chủ tịch Ủy ban nhân dân cấp tỉnh..."}
{"id": "LAB-10-D130-007", "type": "condition", "premises": ["disagree_with_provincial_chairman_decision", "complaint_not_resolved_in_time"], "conclusion": "can_file_lawsuit_after_provincial_chairman_decision", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 130 khoản 5 điểm c", "exception_to": "", "quote": "Trường hợp người khiếu nại không đồng ý với việc giải quyết khiếu nại lần hai của Chủ tịch Ủy ban nhân dân cấp tỉnh hoặc hết thời hạn quy định mà khiếu nại không được giải quyết thì có quyền khởi kiện tại Tòa án theo quy định của pháp luật."}
{"id": "LAB-10-D130-008", "type": "lookup", "premises": [], "conclusion": "complaint_procedure_regulations", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 130 khoản 6", "exception_to": "", "quote": "Thời hiệu khiếu nại, trình tự, thủ tục giải quyết khiếu nại về bảo hiểm xã hội được thực hiện theo quy định của pháp luật về khiếu nại."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 131. Tố cáo, giải quyết tố cáo về bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 131. Tố cáo, giải quyết tố cáo về bảo hiểm xã hội 
1. Việc tố cáo, giải quyết tố cáo đối với hành vi vi phạm pháp luật trong việc thực hiện nhiệm vụ, 
công vụ về bảo hiểm xã hội và hành vi vi phạm pháp luật về quản lý nhà nước trong lĩnh vực bảo 
hiểm xã hội được thực hiện theo quy định của pháp luật về tố cáo. 
2. Cơ quan bảo hiểm xã hội có trách nhiệm giải quyết tố cáo đối với hành vi vi phạm pháp luật 
trong việc chấp hành quy định của pháp luật về bảo hiểm xã hội, trừ trường hợp quy định tại 
khoản 3 Điều này. 
3. Chủ tịch Ủy ban nhân dân cấp tỉnh có trách nhiệm giải quyết tố cáo đối với hành vi vi phạm 
pháp luật của cơ quan, tổ chức, cá nhân trong việc chấp hành quy định của pháp luật về bảo hiểm 
xã hội trước năm 1995. 
4. Trình tự, thủ tục tố cáo, giải quyết tố cáo về hành vi vi phạm pháp luật quy định tại khoản 2 và 
khoản 3 Điều này được thực hiện theo quy định của pháp luật về tố cáo. 
5. Chính phủ quy định chi tiết Điều này.

[RULES]
{"id": "LAB-10-D131-000", "type": "condition", "premises": ["violation_of_law", "social_insurance_management"], "conclusion": "must_report_violation", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 131 khoản 1", "exception_to": "", "quote": "Việc tố cáo, giải quyết tố cáo đối với hành vi vi phạm pháp luật trong việc thực hiện nhiệm vụ, công vụ về bảo hiểm xã hội..."}
{"id": "LAB-10-D131-001", "type": "condition", "premises": ["violation_of_law", "social_insurance_agency"], "conclusion": "must_resolve_complaint", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 131 khoản 2", "exception_to": "", "quote": "Cơ quan bảo hiểm xã hội có trách nhiệm giải quyết tố cáo đối với hành vi vi phạm pháp luật..."}
{"id": "LAB-10-D131-002", "type": "condition", "premises": ["violation_of_law", "local_government"], "conclusion": "must_resolve_complaint", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 131 khoản 3", "exception_to": "", "quote": "Chủ tịch Ủy ban nhân dân cấp tỉnh có trách nhiệm giải quyết tố cáo đối với hành vi vi phạm pháp luật..."}
{"id": "LAB-10-D131-003", "type": "condition", "premises": ["must_resolve_complaint"], "conclusion": "must_follow_complaint_procedure", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 131 khoản 4", "exception_to": "", "quote": "Trình tự, thủ tục tố cáo, giải quyết tố cáo về hành vi vi phạm pháp luật quy định tại khoản 2 và khoản 3..."}
{"id": "LAB-10-D131-004", "type": "lookup", "premises": [], "conclusion": "government_regulates_complaint_procedure", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 131 khoản 5", "exception_to": "", "quote": "Chính phủ quy định chi tiết Điều này."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 132. Xử lý vi phạm pháp luật về bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 132. Xử lý vi phạm pháp luật về bảo hiểm xã hội 
1. Cơ quan, tổ chức có hành vi vi phạm quy định của Luật này, tùy theo tính chất, mức độ vi 
phạm mà bị xử phạt vi phạm hành chính hoặc bị truy cứu trách nhiệm hình sự; nếu gây thiệt hại 
thì phải bồi thường theo quy định của pháp luật. 
2. Cá nhân có hành vi vi phạm quy định của Luật này, tùy theo tính chất, mức độ vi phạm mà bị 
xử phạt vi phạm hành chính, xử lý kỷ luật hoặc bị truy cứu trách nhiệm hình sự; nếu gây thiệt hại 
thì phải bồi thường theo quy định của pháp luật. 
Chương X 
QUẢN LÝ NHÀ NƯỚC VỀ BẢO HIỂM XÃ HỘI

[RULES]
{"id": "LAB-10-D132-000", "type": "condition", "premises": ["social_insurance_agency", "su_dung_quy_bhxh_trai_phap_luat"], "conclusion": "must_compensate_for_delayed_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 132 khoản 1", "exception_to": "", "quote": "Cơ quan, tổ chức có hành vi vi phạm quy định của Luật này... nếu gây thiệt hại thì phải bồi thường theo quy định của pháp luật."}
{"id": "LAB-10-D132-001", "type": "condition", "premises": ["social_insurance_agency", "su_dung_quy_bhxh_trai_phap_luat"], "conclusion": "recommend_violation_handling", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 132 khoản 1", "exception_to": "", "quote": "Cơ quan, tổ chức có hành vi vi phạm quy định của Luật này... tùy theo tính chất, mức độ vi phạm mà bị xử phạt vi phạm hành chính hoặc bị truy cứu trách nhiệm hình sự."}
{"id": "LAB-10-D132-002", "type": "condition", "premises": ["has_full_contribution_time", "su_dung_quy_bhxh_trai_phap_luat"], "conclusion": "must_compensate_for_delayed_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 132 khoản 2", "exception_to": "", "quote": "Cá nhân có hành vi vi phạm quy định của Luật này... nếu gây thiệt hại thì phải bồi thường theo quy định của pháp luật."}
{"id": "LAB-10-D132-003", "type": "condition", "premises": ["has_full_contribution_time", "su_dung_quy_bhxh_trai_phap_luat"], "conclusion": "recommend_violation_handling", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 132 khoản 2", "exception_to": "", "quote": "Cá nhân có hành vi vi phạm quy định của Luật này... tùy theo tính chất, mức độ vi phạm mà bị xử phạt vi phạm hành chính, xử lý kỷ luật hoặc bị truy cứu trách nhiệm hình sự."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 133. Nội dung quản lý nhà nước về bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 133. Nội dung quản lý nhà nước về bảo hiểm xã hội 
1. Ban hành, trình cấp có thẩm quyền ban hành và tổ chức thực hiện chiến lược, chính sách, pháp 
luật về bảo hiểm xã hội. 
2. Tuyên truyền, phổ biến, giáo dục pháp luật về bảo hiểm xã hội. 
3. Thực hiện công tác thống kê nhà nước về bảo hiểm xã hội. 
4. Đào tạo, bồi dưỡng và phát triển nguồn nhân lực về bảo hiểm xã hội. 
5. Tổ chức bộ máy thực hiện bảo hiểm xã hội. 
6. Cơ chế tài chính, tài chính quỹ bảo hiểm xã hội. 
7. Kiểm tra, thanh tra, giải quyết khiếu nại, tố cáo và xử lý vi phạm pháp luật về bảo hiểm xã hội. 
8. Sơ kết, tổng kết, khen thưởng về bảo hiểm xã hội. 
9. Hợp tác quốc tế về bảo hiểm xã hội.

[RULES]
{"id": "LAB-10-D133-000", "type": "condition", "premises": [], "conclusion": "manage_social_insurance_funds", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 133 khoản 1", "exception_to": "", "quote": "Ban hành, trình cấp có thẩm quyền ban hành và tổ chức thực hiện chiến lược, chính sách, pháp luật về bảo hiểm xã hội."}
{"id": "LAB-10-D133-001", "type": "condition", "premises": [], "conclusion": "promote_social_insurance_law", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 133 khoản 2", "exception_to": "", "quote": "Tuyên truyền, phổ biến, giáo dục pháp luật về bảo hiểm xã hội."}
{"id": "LAB-10-D133-002", "type": "condition", "premises": [], "conclusion": "participate_in_monitoring", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 133 khoản 3", "exception_to": "", "quote": "Thực hiện công tác thống kê nhà nước về bảo hiểm xã hội."}
{"id": "LAB-10-D133-003", "type": "condition", "premises": [], "conclusion": "train_social_insurance_personnel", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 133 khoản 4", "exception_to": "", "quote": "Đào tạo, bồi dưỡng và phát triển nguồn nhân lực về bảo hiểm xã hội."}
{"id": "LAB-10-D133-004", "type": "condition", "premises": [], "conclusion": "organize_social_insurance_agency", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 133 khoản 5", "exception_to": "", "quote": "Tổ chức bộ máy thực hiện bảo hiểm xã hội."}
{"id": "LAB-10-D133-005", "type": "condition", "premises": [], "conclusion": "financial_mechanism_social_insurance", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 133 khoản 6", "exception_to": "", "quote": "Cơ chế tài chính, tài chính quỹ bảo hiểm xã hội."}
{"id": "LAB-10-D133-006", "type": "condition", "premises": [], "conclusion": "ensure_detection_and_handling_of_violations", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 133 khoản 7", "exception_to": "", "quote": "Kiểm tra, thanh tra, giải quyết khiếu nại, tố cáo và xử lý vi phạm pháp luật về bảo hiểm xã hội."}
{"id": "LAB-10-D133-007", "type": "condition", "premises": [], "conclusion": "conduct_evaluation_and_awards", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 133 khoản 8", "exception_to": "", "quote": "Sơ kết, tổng kết, khen thưởng về bảo hiểm xã hội."}
{"id": "LAB-10-D133-008", "type": "condition", "premises": [], "conclusion": "international_cooperation_social_insurance", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 133 khoản 9", "exception_to": "", "quote": "Hợp tác quốc tế về bảo hiểm xã hội."}
