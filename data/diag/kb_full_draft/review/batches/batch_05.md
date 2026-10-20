

######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 87. Mức trợ cấp tuất hằng tháng
[NGUYÊN VĂN]
Điều 87. Mức trợ cấp tuất hằng tháng 
1. Mức trợ cấp tuất hằng tháng đối với mỗi thân nhân bằng 50% mức tham chiếu; trường hợp 
thân nhân không có người trực tiếp nuôi dưỡng thì mức trợ cấp tuất hằng tháng bằng 70% mức 
tham chiếu. 
Bộ trưởng Bộ Lao động - Thương binh và Xã hội quy định việc xác định thân nhân không có 
người trực tiếp nuôi dưỡng. 
2. Trường hợp một người chết hoặc bị Tòa án tuyên bố là đã chết thuộc đối tượng quy định tại 
khoản 1 Điều 86 của Luật này thì số thân nhân được hưởng trợ cấp tuất hằng tháng tối đa 04 
người; trường hợp có từ 02 người chết hoặc bị Tòa án tuyên bố là đã chết trở lên thì thân nhân 
được hưởng 02 lần mức trợ cấp quy định tại khoản 1 Điều này. 
3. Thời điểm hưởng trợ cấp tuất hằng tháng được tính kể từ ngày đầu tiên của tháng liền kề sau 
tháng mà đối tượng quy định tại khoản 1 Điều 86 của Luật này chết hoặc bị Tòa án tuyên bố là 
đã chết. Trường hợp con được sinh sau thời điểm người cha, người cha là chồng của người mẹ 
nhờ mang thai hộ hoặc người mẹ nhờ mang thai hộ chết thì thời điểm hưởng trợ cấp tuất hằng 
tháng của con tính từ tháng con được sinh.

[RULES]
{"id": "LAB-10-D87-000", "type": "condition", "premises": ["has_no_direct_caregiver"], "conclusion": "monthly_allowance_amount", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 87 khoản 1", "exception_to": "", "quote": "trường hợp thân nhân không có người trực tiếp nuôi dưỡng thì mức trợ cấp tuất hằng tháng bằng 70% mức tham chiếu."}
{"id": "LAB-10-D87-001", "type": "condition", "premises": ["has_direct_caregiver"], "conclusion": "monthly_allowance_amount", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 87 khoản 1", "exception_to": "", "quote": "Mức trợ cấp tuất hằng tháng đối với mỗi thân nhân bằng 50% mức tham chiếu."}
{"id": "LAB-10-D87-002", "type": "condition", "premises": ["deceased_person_count"], "conclusion": "max_survivors", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 87 khoản 2", "exception_to": "", "quote": "số thân nhân được hưởng trợ cấp tuất hằng tháng tối đa 04 người;"}
{"id": "LAB-10-D87-003", "type": "condition", "premises": ["deceased_person_count"], "conclusion": "monthly_allowance_multiplier", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 87 khoản 2", "exception_to": "", "quote": "trường hợp có từ 02 người chết hoặc bị Tòa án tuyên bố là đã chết trở lên thì thân nhân được hưởng 02 lần mức trợ cấp quy định tại khoản 1 Điều này."}
{"id": "LAB-10-D87-004", "type": "condition", "premises": ["deceased_person_date"], "conclusion": "allowance_start_date", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 87 khoản 3", "exception_to": "", "quote": "Thời điểm hưởng trợ cấp tuất hằng tháng được tính kể từ ngày đầu tiên của tháng liền kề sau tháng mà đối tượng quy định tại khoản 1 Điều 86 của Luật này chết hoặc bị Tòa án tuyên bố là đã chết."}
{"id": "LAB-10-D87-005", "type": "condition", "premises": ["child_born_after_death"], "conclusion": "allowance_start_date_for_child", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 87 khoản 3", "exception_to": "", "quote": "thời điểm hưởng trợ cấp tuất hằng tháng của con tính từ tháng con được sinh."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 88. Các trường hợp hưởng trợ cấp tuất một lần
[NGUYÊN VĂN]
Điều 88. Các trường hợp hưởng trợ cấp tuất một lần 
1. Các đối tượng sau đây chết hoặc bị Tòa án tuyên bố là đã chết thì thân nhân được xét hưởng 
trợ cấp tuất một lần: 
a) Người đang tham gia bảo hiểm xã hội hoặc đang bảo lưu thời gian đóng bảo hiểm xã hội; 
b) Người đang hưởng hoặc đang tạm dừng hưởng lương hưu; người đang hưởng hoặc đang tạm 
dừng hưởng trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng tháng đã nghỉ việc. 
2. Đối tượng quy định tại khoản 1 Điều này khi chết thì thân nhân được hưởng tiền tuất một lần 
trong các trường hợp sau đây: 
a) Không đủ điều kiện quy định tại điểm a khoản 1 Điều 86 của Luật này; 
b) Thuộc một trong các trường hợp quy định tại khoản 1 Điều 86 của Luật này nhưng không có 
thân nhân hưởng tiền tuất hằng tháng quy định tại khoản 2 Điều 86 của Luật này; 
c) Thân nhân thuộc diện hưởng trợ cấp tuất hằng tháng theo quy định tại khoản 2 Điều 86 của 
Luật này nhưng có nguyện vọng hưởng trợ cấp tuất một lần; 
d) Trường hợp không có thân nhân quy định tại khoản 7 Điều 3 của Luật này thì trợ cấp tuất một 
lần được thực hiện theo quy định của pháp luật về thừa kế.

[RULES]
{"id": "LAB-10-D88-000", "type": "condition", "premises": ["has_full_contribution_time_by_state"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 88 khoản 1 điểm a", "exception_to": "", "quote": "Người đang tham gia bảo hiểm xã hội hoặc đang bảo lưu thời gian đóng bảo hiểm xã hội;"}
{"id": "LAB-10-D88-001", "type": "condition", "premises": ["entitled_pension"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 88 khoản 1 điểm b", "exception_to": "", "quote": "Người đang hưởng hoặc đang tạm dừng hưởng lương hưu;"}
{"id": "LAB-10-D88-002", "type": "condition", "premises": ["~not_entitled_lump_sum"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 88 khoản 1 điểm b", "exception_to": "", "quote": "Người đang hưởng hoặc đang tạm dừng hưởng trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng tháng đã nghỉ việc."}
{"id": "LAB-10-D88-003", "type": "condition", "premises": ["not_entitled_lump_sum"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 88 khoản 2 điểm a", "exception_to": "", "quote": "Không đủ điều kiện quy định tại điểm a khoản 1 Điều 86 của Luật này;"}
{"id": "LAB-10-D88-004", "type": "condition", "premises": ["covered_point_a", "not_entitled_monthly_allowance"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 88 khoản 2 điểm b", "exception_to": "", "quote": "Thuộc một trong các trường hợp quy định tại khoản 1 Điều 86 của Luật này nhưng không có thân nhân hưởng tiền tuất hằng tháng quy định tại khoản 2 Điều 86 của Luật này;"}
{"id": "LAB-10-D88-005", "type": "condition", "premises": ["covered_point_a", "~not_entitled_monthly_allowance"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 88 khoản 2 điểm c", "exception_to": "", "quote": "Thân nhân thuộc diện hưởng trợ cấp tuất hằng tháng theo quy định tại khoản 2 Điều 86 của Luật này nhưng có nguyện vọng hưởng trợ cấp tuất một lần;"}
{"id": "LAB-10-D88-006", "type": "condition", "premises": ["not_entitled_lump_sum"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 88 khoản 2 điểm d", "exception_to": "", "quote": "Trường hợp không có thân nhân quy định tại khoản 7 Điều 3 của Luật này thì trợ cấp tuất một lần được thực hiện theo quy định của pháp luật về thừa kế."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 89. Mức trợ cấp tuất một lần
[NGUYÊN VĂN]
Điều 89. Mức trợ cấp tuất một lần 
1. Mức trợ cấp tuất một lần đối với thân nhân của đối tượng quy định tại điểm a khoản 1 Điều 88 
của Luật này bằng mức trợ cấp tuất cho mỗi năm đóng bảo hiểm xã hội nhân với số năm đóng 
bảo hiểm xã hội nhưng không thấp hơn 03 tháng mức bình quân tiền lương làm căn cứ đóng bảo 
hiểm xã hội. Mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội để tính trợ cấp tuất một 
lần thực hiện theo quy định tại Điều 72 của Luật này tính đến thời điểm dừng đóng. Mức trợ cấp 
tuất cho mỗi năm đóng bảo hiểm xã hội được quy định như sau: 
a) Bằng 1,5 tháng mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội cho những năm 
đóng bảo hiểm xã hội trước năm 2014. 
Trường hợp thời gian đóng bảo hiểm xã hội có cả trước và sau năm 2014 mà thời gian đóng 
trước năm 2014 có tháng lẻ thì những tháng lẻ đó được chuyển sang giai đoạn đóng bảo hiểm xã 
hội từ năm 2014 trở đi; 
b) Bằng 02 tháng mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội cho các năm đóng 
bảo hiểm xã hội từ năm 2014 trở đi. 
2. Mức trợ cấp tuất một lần đối với thân nhân của người đang hưởng lương hưu hoặc đang tạm 
dừng hưởng lương hưu chết được tính theo thời gian đã hưởng lương hưu và được quy định như 
sau: 
a) Trường hợp chết trong 02 tháng đầu thì mức trợ cấp tuất một lần bằng 48 tháng lương hưu của 
tháng đang hưởng; 
b) Trường hợp chết từ tháng thứ ba trở đi thì cứ mỗi tháng mức trợ cấp tuất một lần giảm 0,5 
tháng lương hưu so với mức trợ cấp quy định tại điểm a khoản này nhưng không thấp hơn 03 
tháng lương hưu của tháng đang hưởng. 
3. Mức trợ cấp tuất một lần đối với thân nhân của người đang hưởng trợ cấp tai nạn lao động, 
bệnh nghề nghiệp hằng tháng đã nghỉ việc hưởng bảo hiểm xã hội một lần trước khi chết bằng 03 
tháng trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng tháng của tháng đang hưởng. 
4. Mức tham chiếu dùng để tính trợ cấp tuất một lần là mức tham chiếu tại tháng mà đối tượng 
quy định tại điểm a khoản 1 Điều 88 của Luật này chết. 
5. Chính phủ quy định việc giải quyết chế độ tử tuất đối với trường hợp người đang hưởng trợ 
cấp tai nạn lao động, bệnh nghề nghiệp hằng tháng chưa nghỉ việc hoặc còn bảo lưu thời gian 
đóng bảo hiểm xã hội và người đang hưởng trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng 
tháng đồng thời là người đang hưởng lương hưu.

[RULES]
{"id": "LAB-10-D89-000", "type": "condition", "premises": ["covered_point_a", "has_full_contribution_time"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 89 khoản 1", "exception_to": "", "quote": "Mức trợ cấp tuất một lần đối với thân nhân của đối tượng quy định tại điểm a khoản 1 Điều 88 của Luật này bằng mức trợ cấp tuất cho mỗi năm đóng bảo hiểm xã hội nhân với số năm đóng bảo hiểm xã hội nhưng không thấp hơn 03 tháng mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội."}
{"id": "LAB-10-D89-001", "type": "condition", "premises": ["started_si_before_2014"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 89 khoản 1 điểm a", "exception_to": "", "quote": "Mức trợ cấp tuất cho mỗi năm đóng bảo hiểm xã hội được quy định như sau: Bằng 1,5 tháng mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội cho những năm đóng bảo hiểm xã hội trước năm 2014."}
{"id": "LAB-10-D89-002", "type": "condition", "premises": ["started_si_after_2014"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 89 khoản 1 điểm b", "exception_to": "", "quote": "Bằng 02 tháng mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội cho các năm đóng bảo hiểm xã hội từ năm 2014 trở đi."}
{"id": "LAB-10-D89-003", "type": "condition", "premises": ["receiving_pension", "~not_entitled_lump_sum"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 89 khoản 2 điểm a", "exception_to": "", "quote": "Trường hợp chết trong 02 tháng đầu thì mức trợ cấp tuất một lần bằng 48 tháng lương hưu của tháng đang hưởng."}
{"id": "LAB-10-D89-004", "type": "condition", "premises": ["receiving_pension", "~not_entitled_lump_sum"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 89 khoản 2 điểm b", "exception_to": "", "quote": "Trường hợp chết từ tháng thứ ba trở đi thì cứ mỗi tháng mức trợ cấp tuất một lần giảm 0,5 tháng lương hưu so với mức trợ cấp quy định tại điểm a khoản này nhưng không thấp hơn 03 tháng lương hưu của tháng đang hưởng."}
{"id": "LAB-10-D89-005", "type": "condition", "premises": ["not_entitled_lump_sum"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 89 khoản 3", "exception_to": "", "quote": "Mức trợ cấp tuất một lần đối với thân nhân của người đang hưởng trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng tháng đã nghỉ việc hưởng bảo hiểm xã hội một lần trước khi chết bằng 03 tháng trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng tháng của tháng đang hưởng."}
{"id": "LAB-10-D89-006", "type": "condition", "premises": [], "conclusion": "reference_amount", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 89 khoản 4", "exception_to": "", "quote": "Mức tham chiếu dùng để tính trợ cấp tuất một lần là mức tham chiếu tại tháng mà đối tượng quy định tại điểm a khoản 1 Điều 88 của Luật này chết."}
{"id": "LAB-10-D89-007", "type": "lookup", "premises": [], "conclusion": "government_regulates_si_calculation", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 89 khoản 5", "exception_to": "", "quote": "Chính phủ quy định việc giải quyết chế độ tử tuất đối với trường hợp người đang hưởng trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng tháng chưa nghỉ việc hoặc còn bảo lưu thời gian đóng bảo hiểm xã hội và người đang hưởng trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng tháng đồng thời là người đang hưởng lương hưu."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 90. Hồ sơ đề nghị hưởng chế độ tử tuất
[NGUYÊN VĂN]
Điều 90. Hồ sơ đề nghị hưởng chế độ tử tuất 
1. Hồ sơ đề nghị hưởng chế độ tử tuất đối với thân nhân của người đang tham gia bảo hiểm xã 
hội hoặc đang bảo lưu thời gian đóng bảo hiểm xã hội bao gồm: 
a) Sổ bảo hiểm xã hội; 
b) Bản sao giấy chứng tử hoặc trích lục khai tử hoặc bản sao giấy báo tử hoặc bản sao quyết định 
của Tòa án tuyên bố là đã chết; 
c) Tờ khai của thân nhân; 
d) Bản chính hoặc bản sao biên bản điều tra tai nạn lao động đối với trường hợp chết do tai nạn 
lao động; bản sao bệnh án điều trị bệnh nghề nghiệp đối với trường hợp chết do bệnh nghề 
nghiệp; 
đ) Biên bản giám định mức suy giảm khả năng lao động của Hội đồng giám định y khoa hoặc 
bản sao giấy xác nhận mức độ khuyết tật đặc biệt nặng có thể hiện kết luận của Hội đồng giám 
định y khoa ghi rõ tỷ lệ phần trăm suy giảm khả năng lao động đối với thân nhân bị suy giảm khả 
năng lao động từ 81% trở lên. 
2. Hồ sơ đề nghị hưởng chế độ tử tuất đối với thân nhân của người đang hưởng lương hưu hoặc 
đang tạm dừng hưởng lương hưu hoặc trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng tháng đã 
nghỉ việc bao gồm: 
a) Bản sao giấy chứng tử hoặc trích lục khai tử hoặc bản sao giấy báo tử hoặc bản sao quyết định 
của Toà án tuyên bố là đã chết; 
b) Tờ khai của thân nhân; 
c) Biên bản giám định mức suy giảm khả năng lao động của Hội đồng giám định y khoa hoặc 
bản sao giấy xác nhận mức độ khuyết tật đặc biệt nặng có thể hiện kết luận của Hội đồng giám 
định y khoa ghi rõ tỷ lệ phần trăm suy giảm khả năng lao động đối với thân nhân bị suy giảm khả 
năng lao động từ 81% trở lên. 
3. Hồ sơ đề nghị hưởng trợ cấp mai táng đối với trường hợp chỉ hưởng trợ cấp mai táng bao 
gồm: 
a) Sổ bảo hiểm xã hội, trừ trường hợp người đang hưởng lương hưu, trợ cấp hằng tháng; 
b) Bản sao giấy chứng tử hoặc trích lục khai tử hoặc bản sao giấy báo tử hoặc bản sao quyết định 
của Tòa án tuyên bố là đã chết; 
c) Tờ khai của tổ chức, cá nhân lo mai táng. 
4. Việc giải quyết hưởng chế độ tử tuất đối với người nước ngoài do Chính phủ quy định.

[RULES]
{"id": "LAB-10-D90-000", "type": "condition", "premises": ["has_social_insurance_book", "document_copy", "submitted_request_document", "medical_exam_procedure", "health_not_recovered_above_81"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 90 khoản 1", "exception_to": "", "quote": "Hồ sơ đề nghị hưởng chế độ tử tuất đối với thân nhân của người đang tham gia bảo hiểm xã hội hoặc đang bảo lưu thời gian đóng bảo hiểm xã hội bao gồm..."}
{"id": "LAB-10-D90-001", "type": "condition", "premises": ["document_copy", "submitted_request_document", "medical_exam_procedure", "health_not_recovered_above_81"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 90 khoản 2", "exception_to": "", "quote": "Hồ sơ đề nghị hưởng chế độ tử tuất đối với thân nhân của người đang hưởng lương hưu hoặc đang tạm dừng hưởng lương hưu hoặc trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng tháng đã nghỉ việc bao gồm..."}
{"id": "LAB-10-D90-002", "type": "condition", "premises": ["has_social_insurance_book", "document_copy", "submitted_request_document"], "conclusion": "funeral_support", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 90 khoản 3", "exception_to": "", "quote": "Hồ sơ đề nghị hưởng trợ cấp mai táng đối với trường hợp chỉ hưởng trợ cấp mai táng bao gồm..."}
{"id": "LAB-10-D90-003", "type": "lookup", "premises": [], "conclusion": "government_regulates_foreign_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 90 khoản 4", "exception_to": "", "quote": "Việc giải quyết hưởng chế độ tử tuất đối với người nước ngoài do Chính phủ quy định."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 91. Giải quyết hưởng chế độ tử tuất
[NGUYÊN VĂN]
Điều 91. Giải quyết hưởng chế độ tử tuất 
1. Trong thời hạn 90 ngày kể từ ngày người đang bảo lưu thời gian đóng bảo hiểm xã hội, người 
đang hưởng hoặc đang tạm dừng hưởng lương hưu, trợ cấp tai nạn lao động, bệnh nghề nghiệp 
hằng tháng chết thì thân nhân hoặc tổ chức, cá nhân lo mai táng nộp hồ sơ quy định tại Điều 90 
của Luật này cho cơ quan bảo hiểm xã hội. 
2. Trong thời hạn 90 ngày kể từ ngày người lao động đang tham gia bảo hiểm xã hội bắt buộc 
chết thì thân nhân hoặc tổ chức, cá nhân lo mai táng nộp hồ sơ quy định tại Điều 90 của Luật này 
cho người sử dụng lao động. 
Trong thời hạn 30 ngày kể từ ngày nhận đủ hồ sơ từ thân nhân của người lao động, người sử 
dụng lao động có trách nhiệm nộp hồ sơ cho cơ quan bảo hiểm xã hội. 
3. Trong thời hạn 10 ngày làm việc kể từ ngày nhận đủ hồ sơ theo quy định, cơ quan bảo hiểm xã 
hội có trách nhiệm giải quyết; trường hợp không giải quyết thì phải trả lời bằng văn bản và nêu 
rõ lý do.

[RULES]
{"id": "LAB-10-D91-000", "type": "condition", "premises": ["has_full_contribution_time_by_employer", "submitted_request_document"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 91 khoản 1", "exception_to": "", "quote": "thân nhân hoặc tổ chức, cá nhân lo mai táng nộp hồ sơ quy định tại Điều 90 của Luật này cho cơ quan bảo hiểm xã hội."}
{"id": "LAB-10-D91-001", "type": "condition", "premises": ["is_employed", "submitted_request_document"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 91 khoản 2", "exception_to": "", "quote": "thân nhân hoặc tổ chức, cá nhân lo mai táng nộp hồ sơ quy định tại Điều 90 của Luật này cho người sử dụng lao động."}
{"id": "LAB-10-D91-002", "type": "condition", "premises": ["submitted_request_document", "received_request_document"], "conclusion": "must_submit_application_within_7_days", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 91 khoản 2", "exception_to": "", "quote": "người sử dụng lao động có trách nhiệm nộp hồ sơ cho cơ quan bảo hiểm xã hội."}
{"id": "LAB-10-D91-003", "type": "condition", "premises": ["received_request_document"], "conclusion": "must_resolve_sick_leave_application", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 91 khoản 3", "exception_to": "", "quote": "cơ quan bảo hiểm xã hội có trách nhiệm giải quyết."}
{"id": "LAB-10-D91-004", "type": "condition", "premises": ["received_request_document"], "conclusion": "must_respond_in_writing_if_not_approved", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 91 khoản 3", "exception_to": "", "quote": "trường hợp không giải quyết thì phải trả lời bằng văn bản và nêu rõ lý do."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 92. Giải quyết hưởng chế độ bảo hiểm xã hội bắt buộc chậm so với thời hạn quy định
[NGUYÊN VĂN]
Điều 92. Giải quyết hưởng chế độ bảo hiểm xã hội bắt buộc chậm so với thời hạn quy định 
1. Trường hợp nộp hồ sơ quá thời hạn quy định tại khoản 1 và khoản 2 Điều 48, khoản 1 Điều 
49, khoản 1 Điều 62, khoản 1 Điều 63, khoản 1 Điều 79, khoản 1 và khoản 2 Điều 91 của Luật 
này thì phải giải trình bằng văn bản và gửi cho cơ quan bảo hiểm xã hội khi nộp hồ sơ. 
2. Trường hợp nộp hồ sơ quá thời hạn quy định hoặc giải quyết hưởng chế độ bảo hiểm xã hội 
bắt buộc chậm so với thời hạn quy định, gây thiệt hại đến quyền, lợi ích hợp pháp của người thụ 
hưởng thì phải bồi thường theo quy định của pháp luật, trừ trường hợp do lỗi của người thụ 
hưởng chế độ bảo hiểm xã hội.

[RULES]
{"id": "LAB-10-D92-000", "type": "condition", "premises": ["submitted_request_for_monthly_allowance", "~not_registered_si", "~not_paid_si_after_60_days"], "conclusion": "must_respond_in_writing_if_not_approved", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 92 khoản 1", "exception_to": "", "quote": "phải giải trình bằng văn bản và gửi cho cơ quan bảo hiểm xã hội khi nộp hồ sơ."}
{"id": "LAB-10-D92-001", "type": "condition", "premises": ["submitted_request_for_monthly_allowance", "~not_registered_si", "~not_paid_si_after_60_days", "~has_full_contribution_time"], "conclusion": "must_compensate_for_delayed_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 92 khoản 2", "exception_to": "", "quote": "phải bồi thường theo quy định của pháp luật, trừ trường hợp do lỗi của người thụ hưởng chế độ bảo hiểm xã hội."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 93. Hình thức chi trả lương hưu và chế độ bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 93. Hình thức chi trả lương hưu và chế độ bảo hiểm xã hội 
1. Thông qua tài khoản của người thụ hưởng mở tại ngân hàng thương mại, chi nhánh ngân hàng 
nước ngoài được thành lập và hoạt động tại Việt Nam. 
2. Trực tiếp từ cơ quan bảo hiểm xã hội hoặc tổ chức dịch vụ được cơ quan bảo hiểm xã hội ủy 
quyền. 
3. Thông qua người sử dụng lao động. 
Chương VI 
BẢO HIỂM XÃ HỘI TỰ NGUYỆN 
Mục 1. TRỢ CẤP THAI SẢN

[RULES]
{"id": "LAB-10-D93-000", "type": "condition", "premises": ["receive_pension_at_residence"], "conclusion": "receive_pension_through_bank_account", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 93 khoản 1", "exception_to": "", "quote": "Thông qua tài khoản của người thụ hưởng mở tại ngân hàng thương mại..."}
{"id": "LAB-10-D93-001", "type": "condition", "premises": ["receive_pension_at_residence"], "conclusion": "receive_pension_directly_from_agency", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 93 khoản 2", "exception_to": "", "quote": "Trực tiếp từ cơ quan bảo hiểm xã hội hoặc tổ chức dịch vụ..."}
{"id": "LAB-10-D93-002", "type": "condition", "premises": ["receive_pension_at_residence"], "conclusion": "receive_pension_through_employer", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 93 khoản 3", "exception_to": "", "quote": "Thông qua người sử dụng lao động."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 94. Đối tượng và điều kiện hưởng trợ cấp thai sản
[NGUYÊN VĂN]
Điều 94. Đối tượng và điều kiện hưởng trợ cấp thai sản 
1. Đối tượng có thời gian đóng bảo hiểm xã hội tự nguyện hoặc vừa có thời gian đóng bảo hiểm 
xã hội bắt buộc vừa có thời gian đóng bảo hiểm xã hội tự nguyện từ đủ 06 tháng trở lên trong 
thời gian 12 tháng trước khi sinh con được hưởng trợ cấp thai sản khi thuộc một trong các trường 
hợp sau đây: 
a) Lao động nữ sinh con; 
b) Lao động nam có vợ sinh con. 
2. Trường hợp chỉ có mẹ tham gia bảo hiểm xã hội mà mẹ chết sau khi sinh con thì cha hoặc 
người trực tiếp nuôi dưỡng được hưởng trợ cấp thai sản. 
3. Trường hợp cả cha và mẹ cùng tham gia bảo hiểm xã hội đủ điều kiện hưởng trợ cấp thai sản 
quy định tại khoản 1 Điều này thì chỉ cha hoặc mẹ được hưởng trợ cấp thai sản. 
4. Trường hợp người quy định tại khoản 1 Điều này vừa có đủ điều kiện hưởng trợ cấp thai sản 
trong bảo hiểm xã hội tự nguyện và vừa có đủ điều kiện hưởng chế độ thai sản trong bảo hiểm xã 
hội bắt buộc thì chỉ được hưởng chế độ thai sản trong bảo hiểm xã hội bắt buộc. 
5. Trường hợp mẹ đủ điều kiện hưởng chế độ thai sản trong bảo hiểm xã hội bắt buộc, cha đủ 
điều kiện hưởng trợ cấp thai sản trong bảo hiểm xã hội tự nguyện thì mẹ được hưởng chế độ thai 
sản trong bảo hiểm xã hội bắt buộc và cha được hưởng trợ cấp thai sản trong bảo hiểm xã hội tự 
nguyện. 
6. Trường hợp cha đủ điều kiện hưởng chế độ thai sản trong bảo hiểm xã hội bắt buộc, mẹ đủ 
điều kiện hưởng trợ cấp thai sản trong bảo hiểm xã hội tự nguyện thì cha được hưởng chế độ thai 
sản trong bảo hiểm xã hội bắt buộc và mẹ được hưởng trợ cấp thai sản trong bảo hiểm xã hội tự 
nguyện.

[RULES]
{"id": "LAB-10-D94-000", "type": "condition", "premises": ["has_full_contribution_time", "term_at_least_6_months", "term_at_most_12_months"], "conclusion": "maternity_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 94 khoản 1", "exception_to": "", "quote": "Đối tượng có thời gian đóng bảo hiểm xã hội tự nguyện hoặc vừa có thời gian đóng bảo hiểm xã hội bắt buộc vừa có thời gian đóng bảo hiểm xã hội tự nguyện từ đủ 06 tháng trở lên trong thời gian 12 tháng trước khi sinh con được hưởng trợ cấp thai sản khi thuộc một trong các trường hợp sau đây"}
{"id": "LAB-10-D94-001", "type": "condition", "premises": ["female_worker_pregnant"], "conclusion": "maternity_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 94 khoản 1 điểm a", "exception_to": "", "quote": "Lao động nữ sinh con"}
{"id": "LAB-10-D94-002", "type": "condition", "premises": ["is_male_worker", "spouse_has_child_birth"], "conclusion": "maternity_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 94 khoản 1 điểm b", "exception_to": "", "quote": "Lao động nam có vợ sinh con"}
{"id": "LAB-10-D94-003", "type": "condition", "premises": ["female_worker_pregnant", "mother_dies_after_birth"], "conclusion": "maternity_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 94 khoản 2", "exception_to": "", "quote": "Trường hợp chỉ có mẹ tham gia bảo hiểm xã hội mà mẹ chết sau khi sinh con thì cha hoặc người trực tiếp nuôi dưỡng được hưởng trợ cấp thai sản"}
{"id": "LAB-10-D94-004", "type": "condition", "premises": ["both_parents_insured"], "conclusion": "maternity_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 94 khoản 3", "exception_to": "", "quote": "Trường hợp cả cha và mẹ cùng tham gia bảo hiểm xã hội đủ điều kiện hưởng trợ cấp thai sản quy định tại khoản 1 Điều này thì chỉ cha hoặc mẹ được hưởng trợ cấp thai sản"}
{"id": "LAB-10-D94-005", "type": "condition", "premises": ["voluntary_si_eligible", "compulsory_si"], "conclusion": "maternity_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 94 khoản 4", "exception_to": "", "quote": "Trường hợp người quy định tại khoản 1 Điều này vừa có đủ điều kiện hưởng trợ cấp thai sản trong bảo hiểm xã hội tự nguyện và vừa có đủ điều kiện hưởng chế độ thai sản trong bảo hiểm xã hội bắt buộc thì chỉ được hưởng chế độ thai sản trong bảo hiểm xã hội bắt buộc"}
{"id": "LAB-10-D94-006", "type": "condition", "premises": ["compulsory_si", "voluntary_si_eligible"], "conclusion": "maternity_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 94 khoản 5", "exception_to": "", "quote": "Trường hợp mẹ đủ điều kiện hưởng chế độ thai sản trong bảo hiểm xã hội bắt buộc, cha đủ điều kiện hưởng trợ cấp thai sản trong bảo hiểm xã hội tự nguyện thì mẹ được hưởng chế độ thai sản trong bảo hiểm xã hội bắt buộc và cha được hưởng trợ cấp thai sản trong bảo hiểm xã hội tự nguyện"}
{"id": "LAB-10-D94-007", "type": "condition", "premises": ["compulsory_si", "voluntary_si_eligible"], "conclusion": "maternity_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 94 khoản 6", "exception_to": "", "quote": "Trường hợp cha đủ điều kiện hưởng chế độ thai sản trong bảo hiểm xã hội bắt buộc, mẹ đủ điều kiện hưởng trợ cấp thai sản trong bảo hiểm xã hội tự nguyện thì cha được hưởng chế độ thai sản trong bảo hiểm xã hội bắt buộc và mẹ được hưởng trợ cấp thai sản trong bảo hiểm xã hội tự nguyện"}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 95. Trợ cấp thai sản
[NGUYÊN VĂN]
Điều 95. Trợ cấp thai sản 
1. Mức trợ cấp thai sản là 2.000.000 đồng cho mỗi con được sinh ra và mỗi thai từ 22 tuần tuổi 
trở lên chết trong tử cung, thai chết trong khi chuyển dạ. 
Lao động nữ là người dân tộc thiểu số hoặc lao động nữ là người dân tộc Kinh có chồng là người 
dân tộc thiểu số thuộc hộ nghèo khi sinh con còn được hưởng chính sách hỗ trợ khác theo quy 
định của Chính phủ. 
2. Ngân sách nhà nước bảo đảm thực hiện quy định tại khoản 1 Điều này. Chính phủ quyết định 
điều chỉnh mức trợ cấp thai sản phù hợp với điều kiện phát triển kinh tế - xã hội và khả năng của 
ngân sách nhà nước từng thời kỳ.

[RULES]
{"id": "LAB-10-D95-000", "type": "condition", "premises": ["has_given_birth", "has_full_contribution_time_by_state"], "conclusion": "maternity_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 95 khoản 1", "exception_to": "", "quote": "Mức trợ cấp thai sản là 2.000.000 đồng cho mỗi con được sinh ra..."}
{"id": "LAB-10-D95-001", "type": "condition", "premises": ["has_child_birth", "is_poor_household"], "conclusion": "maternity_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 95 khoản 1", "exception_to": "", "quote": "Lao động nữ là người dân tộc thiểu số hoặc lao động nữ là người dân tộc Kinh có chồng là người dân tộc thiểu số thuộc hộ nghèo khi sinh con còn được hưởng chính sách hỗ trợ khác..."}
{"id": "LAB-10-D95-002", "type": "lookup", "premises": [], "conclusion": "government_regulates_si_calculation", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 95 khoản 2", "exception_to": "", "quote": "Chính phủ quyết định điều chỉnh mức trợ cấp thai sản phù hợp với điều kiện phát triển kinh tế - xã hội và khả năng của ngân sách nhà nước từng thời kỳ."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 96. Hồ sơ đề nghị hưởng trợ cấp thai sản
[NGUYÊN VĂN]
Điều 96. Hồ sơ đề nghị hưởng trợ cấp thai sản 
Hồ sơ đề nghị hưởng trợ cấp thai sản là một trong các giấy tờ sau đây: 
1. Bản sao giấy khai sinh hoặc trích lục khai sinh hoặc bản sao giấy chứng sinh của con; 
2. Trường hợp thai chết trong tử cung, thai chết trong khi chuyển dạ hoặc con chết sau khi sinh 
mà chưa được cấp giấy chứng sinh thì hồ sơ là một trong các giấy tờ sau đây: 
a) Bản chính hoặc bản sao bản tóm tắt hồ sơ bệnh án có thể hiện thông tin con chết; 
b) Bản chính hoặc bản sao giấy ra viện của lao động nữ sinh con có thể hiện thông tin con chết; 
c) Bản sao giấy báo tử của con; 
d) Văn bản xác nhận của Ủy ban nhân dân cấp xã đối với trường hợp con chết trong vòng 24 giờ 
sau khi sinh.

[RULES]
{"id": "LAB-10-D96-000", "type": "condition", "premises": ["submitted_document_copy"], "conclusion": "has_request_document", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 96 khoản 1", "exception_to": "", "quote": "Hồ sơ đề nghị hưởng trợ cấp thai sản là một trong các giấy tờ sau đây: Bản sao giấy khai sinh hoặc trích lục khai sinh hoặc bản sao giấy chứng sinh của con;"}
{"id": "LAB-10-D96-001", "type": "condition", "premises": ["has_request_document", "has_child_died_before_hand_over"], "conclusion": "has_request_document", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 96 khoản 2", "exception_to": "", "quote": "Trường hợp thai chết trong tử cung, thai chết trong khi chuyển dạ hoặc con chết sau khi sinh mà chưa được cấp giấy chứng sinh thì hồ sơ là một trong các giấy tờ sau đây:"}
{"id": "LAB-10-D96-002", "type": "condition", "premises": ["submitted_document_copy"], "conclusion": "has_request_document", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 96 khoản 2 điểm a", "exception_to": "", "quote": "Bản chính hoặc bản sao bản tóm tắt hồ sơ bệnh án có thể hiện thông tin con chết;"}
{"id": "LAB-10-D96-003", "type": "condition", "premises": ["submitted_document_copy"], "conclusion": "has_request_document", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 96 khoản 2 điểm b", "exception_to": "", "quote": "Bản chính hoặc bản sao giấy ra viện của lao động nữ sinh con có thể hiện thông tin con chết;"}
{"id": "LAB-10-D96-004", "type": "condition", "premises": ["submitted_document_copy"], "conclusion": "has_request_document", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 96 khoản 2 điểm c", "exception_to": "", "quote": "Bản sao giấy báo tử của con;"}
{"id": "LAB-10-D96-005", "type": "condition", "premises": ["submitted_document_copy"], "conclusion": "has_request_document", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 96 khoản 2 điểm d", "exception_to": "", "quote": "Văn bản xác nhận của Ủy ban nhân dân cấp xã đối với trường hợp con chết trong vòng 24 giờ sau khi sinh."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 97. Giải quyết hưởng trợ cấp thai sản
[NGUYÊN VĂN]
Điều 97. Giải quyết hưởng trợ cấp thai sản 
1. Trong thời hạn 60 ngày kể từ ngày sinh con, người lao động có trách nhiệm nộp hồ sơ quy 
định tại Điều 96 của Luật này cho cơ quan bảo hiểm xã hội. 
2. Trong thời hạn 05 ngày làm việc kể từ ngày nhận đủ hồ sơ theo quy định, cơ quan bảo hiểm xã 
hội có trách nhiệm giải quyết; trường hợp không giải quyết thì phải trả lời bằng văn bản và nêu 
rõ lý do. 
Mục 2. CHẾ ĐỘ HƯU TRÍ

[RULES]
{"id": "LAB-10-D97-000", "type": "condition", "premises": ["has_given_birth", "leave_within_60_days_after_birth"], "conclusion": "must_submit_application_for_maternity_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 97 khoản 1", "exception_to": "", "quote": "Trong thời hạn 60 ngày kể từ ngày sinh con, người lao động có trách nhiệm nộp hồ sơ quy định tại Điều 96 của Luật này cho cơ quan bảo hiểm xã hội."}
{"id": "LAB-10-D97-001", "type": "condition", "premises": ["received_request_document"], "conclusion": "must_resolve_maternity_benefit_application", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 97 khoản 2", "exception_to": "", "quote": "Trong thời hạn 05 ngày làm việc kể từ ngày nhận đủ hồ sơ theo quy định, cơ quan bảo hiểm xã hội có trách nhiệm giải quyết."}
{"id": "LAB-10-D97-002", "type": "condition", "premises": ["received_request_document", "~must_resolve_maternity_benefit_application"], "conclusion": "must_respond_in_writing_if_not_approved", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 97 khoản 2", "exception_to": "", "quote": "trường hợp không giải quyết thì phải trả lời bằng văn bản và nêu rõ lý do."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 98. Đối tượng và điều kiện hưởng lương hưu
[NGUYÊN VĂN]
Điều 98. Đối tượng và điều kiện hưởng lương hưu 
Người tham gia bảo hiểm xã hội tự nguyện được hưởng lương hưu khi đủ tuổi nghỉ hưu theo quy 
định tại khoản 2 Điều 169 của Bộ luật Lao động và có thời gian đóng bảo hiểm xã hội từ đủ 15 
năm trở lên.

[RULES]
{"id": "LAB-10-D98-000", "type": "condition", "premises": ["voluntary_si_eligible", "retirement_age_at_signing", "contribution_15_years"], "conclusion": "entitled_pension", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 98 khoản 1", "exception_to": "", "quote": "Người tham gia bảo hiểm xã hội tự nguyện được hưởng lương hưu khi đủ tuổi nghỉ hưu... và có thời gian đóng bảo hiểm xã hội từ đủ 15 năm trở lên."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 99. Mức lương hưu hằng tháng
[NGUYÊN VĂN]
Điều 99. Mức lương hưu hằng tháng 
1. Mức lương hưu hằng tháng của đối tượng đủ điều kiện quy định tại Điều 98 của Luật này 
được tính như sau: 
a) Đối với lao động nữ bằng 45% mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội quy 
định tại Điều 104 của Luật này tương ứng 15 năm đóng bảo hiểm xã hội, sau đó cứ thêm mỗi 
năm đóng thì tính thêm 2%, mức tối đa bằng 75%; 
b) Đối với lao động nam bằng 45% mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội 
quy định tại Điều 104 của Luật này tương ứng 20 năm đóng bảo hiểm xã hội, sau đó cứ thêm 
mỗi năm đóng thì tính thêm 2%, mức tối đa bằng 75%. 
Trường hợp lao động nam có thời gian đóng bảo hiểm xã hội từ đủ 15 năm đến dưới 20 năm, 
mức lương hưu hằng tháng bằng 40% mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội 
quy định tại Điều 104 của Luật này tương ứng 15 năm đóng bảo hiểm xã hội, sau đó cứ thêm 
mỗi năm đóng thì tính thêm 1%. 
2. Việc điều chỉnh lương hưu được thực hiện theo quy định tại Điều 67 của Luật này. 
3. Việc tính mức lương hưu hằng tháng của người lao động đủ điều kiện hưởng lương hưu mà có 
thời gian đóng bảo hiểm xã hội theo quy định của điều ước quốc tế mà nước Cộng hòa xã hội 
chủ nghĩa Việt Nam là thành viên nhưng có thời gian đóng bảo hiểm xã hội ở Việt Nam dưới 15 
năm thì mỗi năm đóng trong thời gian này được tính bằng 2,25% mức bình quân thu nhập làm 
căn cứ đóng bảo hiểm xã hội quy định tại Điều 104 của Luật này.

[RULES]
{"id": "LAB-10-D99-000", "type": "condition", "premises": ["is_female_worker", "contribution_15_years"], "conclusion": "pension_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 99 khoản 1", "exception_to": "", "quote": "Mức lương hưu hằng tháng của đối tượng đủ điều kiện quy định tại Điều 98 của Luật này được tính như sau: Đối với lao động nữ bằng 45% mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội quy định tại Điều 104 của Luật này tương ứng 15 năm đóng bảo hiểm xã hội."}
{"id": "LAB-10-D99-001", "type": "condition", "premises": ["is_female_worker", "contribution_15_years", "has_full_contribution_time"], "conclusion": "pension_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 99 khoản 1", "exception_to": "", "quote": "sau đó cứ thêm mỗi năm đóng thì tính thêm 2%, mức tối đa bằng 75%."}
{"id": "LAB-10-D99-002", "type": "condition", "premises": ["is_male_worker", "contribution_20_years"], "conclusion": "pension_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 99 khoản 1", "exception_to": "", "quote": "Đối với lao động nam bằng 45% mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội quy định tại Điều 104 của Luật này tương ứng 20 năm đóng bảo hiểm xã hội."}
{"id": "LAB-10-D99-003", "type": "condition", "premises": ["is_male_worker", "contribution_15_years", "~contribution_20_years"], "conclusion": "pension_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 99 khoản 1", "exception_to": "", "quote": "Trường hợp lao động nam có thời gian đóng bảo hiểm xã hội từ đủ 15 năm đến dưới 20 năm, mức lương hưu hằng tháng bằng 40% mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội."}
{"id": "LAB-10-D99-004", "type": "condition", "premises": ["is_male_worker", "contribution_15_years", "~contribution_20_years", "has_full_contribution_time"], "conclusion": "pension_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 99 khoản 1", "exception_to": "", "quote": "sau đó cứ thêm mỗi năm đóng thì tính thêm 1%."}
{"id": "LAB-10-D99-005", "type": "condition", "premises": ["is_member_international_agreement", "~contribution_15_years"], "conclusion": "pension_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 99 khoản 3", "exception_to": "", "quote": "mỗi năm đóng trong thời gian này được tính bằng 2,25% mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội quy định tại Điều 104 của Luật này."}
{"id": "LAB-10-D99-006", "type": "lookup", "premises": [], "conclusion": "government_regulates_pension_adjustment", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 99 khoản 2", "exception_to": "", "quote": "Việc điều chỉnh lương hưu được thực hiện theo quy định tại Điều 67 của Luật này."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 100. Trợ cấp một lần khi nghỉ hưu
[NGUYÊN VĂN]
Điều 100. Trợ cấp một lần khi nghỉ hưu 
1. Lao động nam có thời gian đóng bảo hiểm xã hội cao hơn 35 năm, lao động nữ có thời gian 
đóng bảo hiểm xã hội cao hơn 30 năm thì khi nghỉ hưu, ngoài lương hưu còn được hưởng trợ cấp 
một lần. 
2. Mức hưởng trợ cấp một lần cho mỗi năm đóng cao hơn quy định tại khoản 1 Điều này bằng 
0,5 lần của mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội quy định tại Điều 104 của 
Luật này cho mỗi năm đóng cao hơn đến tuổi nghỉ hưu theo quy định của pháp luật. 
Trường hợp người lao động đã đủ điều kiện hưởng lương hưu theo quy định tại Điều 98 của Luật 
này mà tiếp tục đóng bảo hiểm xã hội thì mức trợ cấp bằng 02 lần của mức bình quân thu nhập 
làm căn cứ đóng bảo hiểm xã hội quy định tại Điều 104 của Luật này cho mỗi năm đóng cao hơn 
số năm quy định tại khoản 1 Điều này kể từ sau thời điểm đủ tuổi nghỉ hưu theo quy định của 
pháp luật đến thời điểm nghỉ hưu.

[RULES]
{"id": "LAB-10-D100-000", "type": "condition", "premises": ["contribution_30_years", "is_female_worker"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 100 khoản 1", "exception_to": "", "quote": "Lao động nữ có thời gian đóng bảo hiểm xã hội cao hơn 30 năm thì khi nghỉ hưu, ngoài lương hưu còn được hưởng trợ cấp một lần."}
{"id": "LAB-10-D100-001", "type": "condition", "premises": ["has_full_contribution_time", "is_male_worker"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 100 khoản 1", "exception_to": "", "quote": "Lao động nam có thời gian đóng bảo hiểm xã hội cao hơn 35 năm thì khi nghỉ hưu, ngoài lương hưu còn được hưởng trợ cấp một lần."}
{"id": "LAB-10-D100-002", "type": "condition", "premises": ["entitled_lump_sum", "time_of_contribution"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 100 khoản 2", "exception_to": "", "quote": "Mức hưởng trợ cấp một lần cho mỗi năm đóng cao hơn quy định tại khoản 1 Điều này bằng 0,5 lần của mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội."}
{"id": "LAB-10-D100-003", "type": "condition", "premises": ["entitled_lump_sum", "reached_retirement_age"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 100 khoản 2", "exception_to": "", "quote": "Trường hợp người lao động đã đủ điều kiện hưởng lương hưu theo quy định tại Điều 98 của Luật này mà tiếp tục đóng bảo hiểm xã hội thì mức trợ cấp bằng 02 lần của mức bình quân thu nhập."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 101. Thời điểm hưởng lương hưu
[NGUYÊN VĂN]
Điều 101. Thời điểm hưởng lương hưu 
1. Thời điểm hưởng lương hưu đối với đối tượng quy định tại Điều 98 của Luật này được tính từ 
ngày đầu tiên của tháng liền kề sau tháng đủ điều kiện hưởng lương hưu theo quy định tại Điều 
98 của Luật này. 
2. Trường hợp người tham gia bảo hiểm xã hội tiếp tục đóng bảo hiểm xã hội tự nguyện sau khi 
đã đủ điều kiện hưởng lương hưu thì thời điểm hưởng lương hưu là ngày đầu tiên của tháng liền 
kề sau tháng dừng đóng và có yêu cầu hưởng lương hưu. 
3. Trường hợp người tham gia bảo hiểm xã hội tự nguyện đóng một lần cho những năm còn thiếu 
theo quy định tại điểm e khoản 2 Điều 36 của Luật này thì thời điểm hưởng lương hưu là ngày 
đầu tiên của tháng liền kề sau tháng đóng đủ số tiền cho những năm còn thiếu. 
4. Bộ trưởng Bộ Lao động - Thương binh và Xã hội quy định chi tiết Điều này; quy định về việc 
tính, việc xác định điều kiện đối với từng trường hợp để giải quyết chế độ hưu trí.

[RULES]
{"id": "LAB-10-D101-000", "type": "condition", "premises": ["has_full_contribution_time"], "conclusion": "receive_pension_directly_from_agency", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 101 khoản 1", "exception_to": "", "quote": "Thời điểm hưởng lương hưu đối với đối tượng quy định tại Điều 98 của Luật này được tính từ ngày đầu tiên của tháng liền kề sau tháng đủ điều kiện hưởng lương hưu theo quy định tại Điều 98 của Luật này."}
{"id": "LAB-10-D101-001", "type": "condition", "premises": ["voluntary_si_eligible", "~has_full_contribution_time"], "conclusion": "receive_pension_directly_from_agency", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 101 khoản 2", "exception_to": "", "quote": "Trường hợp người tham gia bảo hiểm xã hội tiếp tục đóng bảo hiểm xã hội tự nguyện sau khi đã đủ điều kiện hưởng lương hưu thì thời điểm hưởng lương hưu là ngày đầu tiên của tháng liền kề sau tháng dừng đóng và có yêu cầu hưởng lương hưu."}
{"id": "LAB-10-D101-002", "type": "condition", "premises": ["voluntary_si_eligible", "contribute_at_first_contract"], "conclusion": "receive_pension_directly_from_agency", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 101 khoản 3", "exception_to": "", "quote": "Trường hợp người tham gia bảo hiểm xã hội tự nguyện đóng một lần cho những năm còn thiếu theo quy định tại điểm e khoản 2 Điều 36 của Luật này thì thời điểm hưởng lương hưu là ngày đầu tiên của tháng liền kề sau tháng đóng đủ số tiền cho những năm còn thiếu."}
{"id": "LAB-10-D101-003", "type": "lookup", "premises": [], "conclusion": "government_regulates_si_calculation", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 101 khoản 4", "exception_to": "", "quote": "Bộ trưởng Bộ Lao động - Thương binh và Xã hội quy định chi tiết Điều này; quy định về việc tính, việc xác định điều kiện đối với từng trường hợp để giải quyết chế độ hưu trí."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 102. Hưởng bảo hiểm xã hội một lần
[NGUYÊN VĂN]
Điều 102. Hưởng bảo hiểm xã hội một lần 
1. Đối tượng quy định tại khoản 4 Điều 2 của Luật này mà có yêu cầu thì được hưởng bảo hiểm 
xã hội một lần nếu thuộc một trong các trường hợp sau đây: 
a) Đủ tuổi nghỉ hưu theo quy định tại khoản 2 Điều 169 của Bộ luật Lao động nhưng có thời gian 
đóng bảo hiểm xã hội chưa đủ 15 năm mà không tiếp tục tham gia bảo hiểm xã hội. 
Trường hợp người lao động không hưởng bảo hiểm xã hội một lần thì có thể lựa chọn hưởng trợ 
cấp hằng tháng theo quy định tại Điều 23 của Luật này; 
b) Ra nước ngoài để định cư; 
c) Người đang mắc một trong những bệnh ung thư, bại liệt, xơ gan mất bù, lao nặng, AIDS; 
d) Người có mức suy giảm khả năng lao động từ 81% trở lên; người khuyết tật đặc biệt nặng; 
đ) Người lao động có thời gian đóng bảo hiểm xã hội trước ngày Luật này có hiệu lực thi hành, 
sau 12 tháng không tiếp tục đóng bảo hiểm xã hội mà chưa đủ 20 năm đóng bảo hiểm xã hội. 
2. Mức hưởng bảo hiểm xã hội một lần được tính theo số năm đã đóng và căn cứ đóng bảo hiểm 
xã hội, cứ mỗi năm được tính như sau: 
a) Bằng 1,5 lần của mức bình quân thu nhập tháng đóng bảo hiểm xã hội đối với năm đóng trước 
năm 2014. 
Trường hợp thời gian đóng bảo hiểm xã hội có cả trước và sau năm 2014 mà thời gian đóng 
trước năm 2014 có tháng lẻ thì những tháng lẻ đó được chuyển sang giai đoạn đóng bảo hiểm xã 
hội từ năm 2014 trở đi để tính mức hưởng bảo hiểm xã hội một lần; 
b) Bằng 02 lần của mức bình quân thu nhập tháng đóng bảo hiểm xã hội đối với năm đóng từ 
năm 2014 trở đi; 
c) Trường hợp thời gian đóng bảo hiểm xã hội chưa đủ một năm thì mức hưởng bằng số tiền đã 
đóng nhưng không quá 02 lần của mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội. 
3. Mức hưởng bảo hiểm xã hội một lần của đối tượng được Nhà nước hỗ trợ thực hiện theo quy 
định tại khoản 2 Điều này không bao gồm số tiền ngân sách nhà nước hỗ trợ đóng bảo hiểm xã 
hội tự nguyện, trừ trường hợp quy định tại điểm c và điểm d khoản 1 Điều này. 
4. Thời điểm tính hưởng bảo hiểm xã hội một lần là thời điểm ghi trong quyết định của cơ quan 
bảo hiểm xã hội. 
5. Trường hợp người lao động quy định tại các điểm b, c và d khoản 1 Điều này vừa đủ điều kiện 
hưởng lương hưu vừa đủ điều kiện hưởng bảo hiểm xã hội một lần thì người lao động được lựa 
chọn hưởng lương hưu hoặc bảo hiểm xã hội một lần. 
6. Chính phủ quy định chi tiết Điều này.

[RULES]
{"id": "LAB-10-D102-000", "type": "condition", "premises": ["covered_point_a", "retirement_age_at_signing", "~contribution_15_years"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 102 khoản 1 điểm a", "exception_to": "", "quote": "Đủ tuổi nghỉ hưu theo quy định tại khoản 2 Điều 169 của Bộ luật Lao động nhưng có thời gian đóng bảo hiểm xã hội chưa đủ 15 năm mà không tiếp tục tham gia bảo hiểm xã hội."}
{"id": "LAB-10-D102-001", "type": "condition", "premises": ["covered_point_b"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 102 khoản 1 điểm b", "exception_to": "", "quote": "Ra nước ngoài để định cư."}
{"id": "LAB-10-D102-002", "type": "condition", "premises": ["serious_illness"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 102 khoản 1 điểm c", "exception_to": "", "quote": "Người đang mắc một trong những bệnh ung thư, bại liệt, xơ gan mất bù, lao nặng, AIDS."}
{"id": "LAB-10-D102-003", "type": "condition", "premises": ["health_not_recovered_above_81"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 102 khoản 1 điểm d", "exception_to": "", "quote": "Người có mức suy giảm khả năng lao động từ 81% trở lên; người khuyết tật đặc biệt nặng."}
{"id": "LAB-10-D102-004", "type": "condition", "premises": ["~covered_point_a", "~contribution_15_years"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 102 khoản 1 điểm đ", "exception_to": "", "quote": "Người lao động có thời gian đóng bảo hiểm xã hội trước ngày Luật này có hiệu lực thi hành, sau 12 tháng không tiếp tục đóng bảo hiểm xã hội mà chưa đủ 20 năm đóng bảo hiểm xã hội."}
{"id": "LAB-10-D102-005", "type": "condition", "premises": ["started_si_before_2014"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 102 khoản 2 điểm a", "exception_to": "", "quote": "Bằng 1,5 lần của mức bình quân thu nhập tháng đóng bảo hiểm xã hội đối với năm đóng trước năm 2014."}
{"id": "LAB-10-D102-006", "type": "condition", "premises": ["started_si_after_2014"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 102 khoản 2 điểm b", "exception_to": "", "quote": "Bằng 02 lần của mức bình quân thu nhập tháng đóng bảo hiểm xã hội đối với năm đóng từ năm 2014 trở đi."}
{"id": "LAB-10-D102-007", "type": "condition", "premises": ["~contribution_15_years"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 102 khoản 2 điểm c", "exception_to": "", "quote": "Trường hợp thời gian đóng bảo hiểm xã hội chưa đủ một năm thì mức hưởng bằng số tiền đã đóng nhưng không quá 02 lần của mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội."}
{"id": "LAB-10-D102-008", "type": "condition", "premises": ["covered_point_c", "covered_point_d"], "conclusion": "~benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 102 khoản 3", "exception_to": "", "quote": "Mức hưởng bảo hiểm xã hội một lần của đối tượng được Nhà nước hỗ trợ thực hiện theo quy định tại khoản 2 Điều này không bao gồm số tiền ngân sách nhà nước hỗ trợ đóng bảo hiểm xã hội tự nguyện, trừ trường hợp quy định tại điểm c và điểm d khoản 1 Điều này."}
{"id": "LAB-10-D102-009", "type": "condition", "premises": ["covered_point_b", "covered_point_c", "covered_point_d"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 102 khoản 5", "exception_to": "", "quote": "Trường hợp người lao động quy định tại các điểm b, c và d khoản 1 Điều này vừa đủ điều kiện hưởng lương hưu vừa đủ điều kiện hưởng bảo hiểm xã hội một lần thì người lao động được lựa chọn hưởng lương hưu hoặc bảo hiểm xã hội một lần."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 103. Bảo lưu thời gian đóng bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 103. Bảo lưu thời gian đóng bảo hiểm xã hội 
Người lao động dừng đóng bảo hiểm xã hội tự nguyện mà chưa đủ điều kiện để hưởng lương 
hưu theo quy định tại Điều 98 hoặc chưa nhận bảo hiểm xã hội một lần theo quy định tại Điều 
102 của Luật này hoặc chưa hưởng trợ cấp hằng tháng theo quy định tại Điều 23 của Luật này thì 
được bảo lưu thời gian đóng bảo hiểm xã hội.

[RULES]
{"id": "LAB-10-D103-000", "type": "condition", "premises": ["not_entitled_lump_sum", "not_entitled_monthly_allowance", "~not_registered_si"], "conclusion": "can_preserve_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 103 khoản 1", "exception_to": "", "quote": "Người lao động dừng đóng bảo hiểm xã hội tự nguyện mà chưa đủ điều kiện để hưởng lương hưu theo quy định tại Điều 98 hoặc chưa nhận bảo hiểm xã hội một lần theo quy định tại Điều 102 của Luật này hoặc chưa hưởng trợ cấp hằng tháng theo quy định tại Điều 23 của Luật này thì được bảo lưu thời gian đóng bảo hiểm xã hội."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 104. Mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội tự nguyện
[NGUYÊN VĂN]
Điều 104. Mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội tự nguyện 
1. Mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội tự nguyện được tính bằng bình 
quân các mức thu nhập làm căn cứ đóng bảo hiểm xã hội của toàn bộ thời gian đóng. 
2. Thu nhập tháng đã đóng bảo hiểm xã hội để làm căn cứ tính mức bình quân thu nhập làm căn 
cứ đóng bảo hiểm xã hội của người lao động được điều chỉnh trên cơ sở chỉ số giá tiêu dùng của 
từng thời kỳ theo quy định của Chính phủ.

[RULES]
{"id": "LAB-10-D104-000", "type": "condition", "premises": [], "conclusion": "average_income_for_voluntary_si", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 104 khoản 1", "exception_to": "", "quote": "Mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội tự nguyện được tính bằng bình quân các mức thu nhập làm căn cứ đóng bảo hiểm xã hội của toàn bộ thời gian đóng."}
{"id": "LAB-10-D104-001", "type": "condition", "premises": ["monthly_income_contributed", "cpi_adjustment"], "conclusion": "adjusted_average_income_for_voluntary_si", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 104 khoản 2", "exception_to": "", "quote": "Thu nhập tháng đã đóng bảo hiểm xã hội để làm căn cứ tính mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội của người lao động được điều chỉnh trên cơ sở chỉ số giá tiêu dùng của từng thời kỳ theo quy định của Chính phủ."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 105. Hồ sơ đề nghị hưởng lương hưu đối với người tham gia bảo hiểm xã hội tự
[NGUYÊN VĂN]
Điều 105. Hồ sơ đề nghị hưởng lương hưu đối với người tham gia bảo hiểm xã hội tự 
nguyện 
Hồ sơ đề nghị hưởng lương hưu đối với người tham gia bảo hiểm xã hội tự nguyện bao gồm sổ 
bảo hiểm xã hội và văn bản đề nghị hưởng lương hưu.

[RULES]
{"id": "LAB-10-D105-000", "type": "condition", "premises": ["has_social_insurance_book", "has_request_document"], "conclusion": "must_submit_application_for_pension", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 105", "exception_to": "", "quote": "Hồ sơ đề nghị hưởng lương hưu đối với người tham gia bảo hiểm xã hội tự nguyện bao gồm sổ bảo hiểm xã hội và văn bản đề nghị hưởng lương hưu."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 106. Hồ sơ đề nghị hưởng bảo hiểm xã hội một lần
[NGUYÊN VĂN]
Điều 106. Hồ sơ đề nghị hưởng bảo hiểm xã hội một lần 
1. Hồ sơ đề nghị hưởng bảo hiểm xã hội một lần bao gồm: 
a) Sổ bảo hiểm xã hội; 
b) Văn bản đề nghị hưởng bảo hiểm xã hội một lần của người lao động. 
2. Trường hợp quy định tại điểm b khoản 1 Điều 102 của Luật này, ngoài hồ sơ quy định tại 
khoản 1 Điều này thì có thêm bản sao giấy xác nhận của cơ quan có thẩm quyền về việc thôi 
quốc tịch Việt Nam hoặc bản dịch tiếng Việt được chứng thực hoặc công chứng một trong các 
giấy tờ sau đây: 
a) Hộ chiếu do nước ngoài cấp; 
b) Thị thực của cơ quan nước ngoài có thẩm quyền cấp có xác nhận việc cho phép nhập cảnh để 
định cư ở nước ngoài; 
c) Thẻ thường trú dài hạn ở nước ngoài của cơ quan nước ngoài có thẩm quyền cấp; 
d) Giấy tờ hợp pháp khác thể hiện việc định cư ở nước ngoài theo quy định của Chính phủ. 
3. Trường hợp quy định tại điểm c khoản 1 Điều 102 của Luật này, ngoài hồ sơ quy định tại 
khoản 1 Điều này thì có thêm bản tóm tắt hồ sơ bệnh án hoặc bản chính hoặc bản sao giấy ra 
viện. 
4. Trường hợp quy định tại điểm d khoản 1 Điều 102 của Luật này, ngoài hồ sơ quy định tại 
khoản 1 Điều này thì có thêm biên bản giám định mức suy giảm khả năng lao động của Hội đồng 
giám định y khoa hoặc bản sao giấy xác nhận mức độ khuyết tật đặc biệt nặng.

[RULES]
{"id": "LAB-10-D106-000", "type": "condition", "premises": ["has_social_insurance_book", "has_request_document"], "conclusion": "must_submit_application_for_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 106 khoản 1", "exception_to": "", "quote": "Hồ sơ đề nghị hưởng bảo hiểm xã hội một lần bao gồm: Sổ bảo hiểm xã hội; Văn bản đề nghị hưởng bảo hiểm xã hội một lần của người lao động."}
{"id": "LAB-10-D106-001", "type": "condition", "premises": ["has_social_insurance_book", "has_request_document", "emigrating"], "conclusion": "must_submit_application_for_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 106 khoản 2", "exception_to": "khoản 1 Điều 102", "quote": "Trường hợp quy định tại điểm b khoản 1 Điều 102 của Luật này, ngoài hồ sơ quy định tại khoản 1 Điều này thì có thêm bản sao giấy xác nhận của cơ quan có thẩm quyền về việc thôi quốc tịch Việt Nam..."}
{"id": "LAB-10-D106-002", "type": "condition", "premises": ["has_social_insurance_book", "has_request_document", "health_not_recovered_other_cases"], "conclusion": "must_submit_application_for_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 106 khoản 3", "exception_to": "khoản 1 Điều 102", "quote": "Trường hợp quy định tại điểm c khoản 1 Điều 102 của Luật này, ngoài hồ sơ quy định tại khoản 1 Điều này thì có thêm bản tóm tắt hồ sơ bệnh án hoặc bản chính hoặc bản sao giấy ra viện."}
{"id": "LAB-10-D106-003", "type": "condition", "premises": ["has_social_insurance_book", "has_request_document", "health_not_recovered_above_81"], "conclusion": "must_submit_application_for_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 106 khoản 4", "exception_to": "khoản 1 Điều 102", "quote": "Trường hợp quy định tại điểm d khoản 1 Điều 102 của Luật này, ngoài hồ sơ quy định tại khoản 1 Điều này thì có thêm biên bản giám định mức suy giảm khả năng lao động của Hội đồng giám định y khoa..."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 107. Giải quyết hưởng lương hưu, bảo hiểm xã hội một lần đối với người đang bảo lưu
[NGUYÊN VĂN]
Điều 107. Giải quyết hưởng lương hưu, bảo hiểm xã hội một lần đối với người đang bảo lưu 
thời gian đóng bảo hiểm xã hội, người tham gia bảo hiểm xã hội tự nguyện 
1. Trong thời hạn 20 ngày trước thời điểm đủ điều kiện hưởng lương hưu, người đang bảo lưu 
thời gian đóng bảo hiểm xã hội, người tham gia bảo hiểm xã hội tự nguyện nộp hồ sơ quy định 
tại Điều 105 của Luật này cho cơ quan bảo hiểm xã hội. 
2. Người lao động khi đủ điều kiện và có yêu cầu hưởng bảo hiểm xã hội một lần nộp hồ sơ quy 
định tại Điều 106 của Luật này cho cơ quan bảo hiểm xã hội. 
Thời điểm kết thúc ngày cuối cùng của tháng dừng đóng bảo hiểm xã hội hoặc tháng chấm dứt 
hợp đồng lao động là căn cứ để xác định thời điểm đủ điều kiện giải quyết hưởng bảo hiểm xã 
hội một lần đối với trường hợp người hưởng bảo hiểm xã hội theo quy định tại điểm đ khoản 1 
Điều 102 của Luật này. 
3. Trong thời hạn 20 ngày, không bao gồm ngày nghỉ lễ, tết, kể từ ngày nhận đủ hồ sơ theo quy 
định đối với người đề nghị hưởng lương hưu hoặc trong thời hạn 07 ngày làm việc kể từ ngày 
nhận đủ hồ sơ theo quy định đối với người đề nghị hưởng bảo hiểm xã hội một lần, cơ quan bảo 
hiểm xã hội có trách nhiệm giải quyết; trường hợp không giải quyết thì phải trả lời bằng văn bản 
và nêu rõ lý do. 
Mục 3. CHẾ ĐỘ TỬ TUẤT

[RULES]
{"id": "LAB-10-D107-000", "type": "condition", "premises": ["has_full_contribution_time", "received_request_document"], "conclusion": "must_submit_application_for_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 107 khoản 1", "exception_to": "", "quote": "người đang bảo lưu thời gian đóng bảo hiểm xã hội, người tham gia bảo hiểm xã hội tự nguyện nộp hồ sơ quy định"}
{"id": "LAB-10-D107-001", "type": "condition", "premises": ["entitled_lump_sum", "received_request_document"], "conclusion": "must_submit_application_for_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 107 khoản 2", "exception_to": "", "quote": "Người lao động khi đủ điều kiện và có yêu cầu hưởng bảo hiểm xã hội một lần nộp hồ sơ"}
{"id": "LAB-10-D107-002", "type": "condition", "premises": ["received_request_document"], "conclusion": "must_resolve_pension_application", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 107 khoản 3", "exception_to": "", "quote": "cơ quan bảo hiểm xã hội có trách nhiệm giải quyết"}
{"id": "LAB-10-D107-003", "type": "condition", "premises": ["received_request_document"], "conclusion": "must_respond_in_writing_if_not_approved", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 107 khoản 3", "exception_to": "", "quote": "trường hợp không giải quyết thì phải trả lời bằng văn bản và nêu rõ lý do"}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 108. Đối tượng hưởng chế độ tử tuất
[NGUYÊN VĂN]
Điều 108. Đối tượng hưởng chế độ tử tuất 
Đối tượng hưởng chế độ tử tuất của người tham gia bảo hiểm xã hội tự nguyện bị chết là tổ chức, 
cá nhân lo mai táng quy định tại khoản 1 Điều 109 của Luật này; thân nhân quy định khoản 3 
Điều 109 của Luật này và khoản 1 Điều 110 của Luật này.

[RULES]
{"id": "LAB-10-D108-000", "type": "condition", "premises": ["deceased", "has_direct_caregiver"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 108", "exception_to": "", "quote": "Đối tượng hưởng chế độ tử tuất của người tham gia bảo hiểm xã hội tự nguyện bị chết là tổ chức, cá nhân lo mai táng..."}
{"id": "LAB-10-D108-001", "type": "condition", "premises": ["deceased", "has_no_direct_caregiver"], "conclusion": "funeral_support", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 108", "exception_to": "", "quote": "Đối tượng hưởng chế độ tử tuất của người tham gia bảo hiểm xã hội tự nguyện bị chết là tổ chức, cá nhân lo mai táng..."}
{"id": "LAB-10-D108-002", "type": "condition", "premises": ["deceased", "foreign_citizen"], "conclusion": "government_regulates_foreign_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 108", "exception_to": "", "quote": "Đối tượng hưởng chế độ tử tuất của người tham gia bảo hiểm xã hội tự nguyện bị chết là tổ chức, cá nhân lo mai táng..."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 109. Trợ cấp mai táng
[NGUYÊN VĂN]
Điều 109. Trợ cấp mai táng 
1. Những người sau đây khi chết thì tổ chức, cá nhân lo mai táng được nhận một lần trợ cấp mai 
táng: 
a) Người có thời gian đóng bảo hiểm xã hội từ đủ 60 tháng trở lên; 
b) Người đang hưởng lương hưu, tạm dừng hưởng lương hưu. 
2. Mức trợ cấp mai táng bằng 10 lần mức tham chiếu tại tháng mà người quy định tại khoản 1 
Điều này chết. 
3. Trường hợp người quy định tại khoản 1 Điều này bị Tòa án tuyên bố là đã chết thì thân nhân 
được hưởng trợ cấp quy định tại khoản 2 Điều này.

[RULES]
{"id": "LAB-10-D109-000", "type": "condition", "premises": ["term_at_least_60_months"], "conclusion": "funeral_support", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 109 khoản 1", "exception_to": "", "quote": "Những người sau đây khi chết thì tổ chức, cá nhân lo mai táng được nhận một lần trợ cấp mai táng: a) Người có thời gian đóng bảo hiểm xã hội từ đủ 60 tháng trở lên;"}
{"id": "LAB-10-D109-001", "type": "condition", "premises": ["receiving_pension"], "conclusion": "funeral_support", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 109 khoản 1", "exception_to": "", "quote": "Những người sau đây khi chết thì tổ chức, cá nhân lo mai táng được nhận một lần trợ cấp mai táng: b) Người đang hưởng lương hưu, tạm dừng hưởng lương hưu."}
{"id": "LAB-10-D109-002", "type": "condition", "premises": ["funeral_support"], "conclusion": "reference_amount", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 109 khoản 2", "exception_to": "", "quote": "Mức trợ cấp mai táng bằng 10 lần mức tham chiếu tại tháng mà người quy định tại khoản 1 Điều này chết."}
{"id": "LAB-10-D109-003", "type": "condition", "premises": ["court_declared_missing_then_dead"], "conclusion": "funeral_support", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 109 khoản 3", "exception_to": "", "quote": "Trường hợp người quy định tại khoản 1 Điều này bị Tòa án tuyên bố là đã chết thì thân nhân được hưởng trợ cấp quy định tại khoản 2 Điều này."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 110. Trợ cấp tuất một lần
[NGUYÊN VĂN]
Điều 110. Trợ cấp tuất một lần 
1. Người đang tham gia bảo hiểm xã hội tự nguyện hoặc đang bảo lưu thời gian đóng bảo hiểm 
xã hội hoặc đang hưởng lương hưu hoặc đang tạm dừng hưởng lương hưu khi chết thì thân nhân 
được hưởng trợ cấp tuất một lần. 
2. Mức trợ cấp tuất một lần đối với thân nhân của người đang tham gia bảo hiểm xã hội tự 
nguyện hoặc đang bảo lưu thời gian đóng bảo hiểm xã hội được tính theo số năm đã đóng bảo 
hiểm xã hội, cứ mỗi năm tính như sau: 
a) Bằng 1,5 lần của mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội cho những năm 
đóng bảo hiểm xã hội trước năm 2014. 
Trường hợp thời gian đóng bảo hiểm xã hội có cả trước và sau năm 2014 mà thời gian đóng 
trước năm 2014 có tháng lẻ thì những tháng lẻ đó được chuyển sang giai đoạn đóng bảo hiểm xã 
hội từ năm 2014 trở đi; 
b) Bằng 02 lần của mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội cho các năm đóng 
bảo hiểm xã hội từ năm 2014 trở đi; 
c) Bằng số tiền đã đóng đối với trường hợp người lao động có thời gian đóng chưa đủ 60 tháng. 
3. Trường hợp người có cả thời gian đóng bảo hiểm xã hội bắt buộc và bảo hiểm xã hội tự 
nguyện thì mức hưởng trợ cấp tuất một lần tối thiểu bằng 03 lần của mức bình quân tiền lương 
và thu nhập làm căn cứ đóng bảo hiểm xã hội. 
4. Mức trợ cấp tuất một lần đối với thân nhân của người đang hưởng lương hưu hoặc đang tạm 
dừng hưởng lương hưu chết được tính theo thời gian đã hưởng lương hưu và được quy định như 
sau: 
a) Trường hợp chết trong 02 tháng đầu thì mức trợ cấp tuất một lần bằng 48 tháng lương hưu của 
tháng đang hưởng; 
b) Trường hợp chết từ tháng thứ ba trở đi thì cứ mỗi tháng mức trợ cấp tuất một lần giảm 0,5 
tháng lương hưu so với mức trợ cấp quy định tại điểm a khoản này nhưng không thấp hơn 03 
tháng lương hưu của tháng đang hưởng.

[RULES]
{"id": "LAB-10-D110-000", "type": "condition", "premises": ["voluntary_si_eligible", "~has_full_contribution_time", "deceased"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 110 khoản 1", "exception_to": "", "quote": "thân nhân được hưởng trợ cấp tuất một lần."}
{"id": "LAB-10-D110-001", "type": "condition", "premises": ["voluntary_si_eligible", "term_at_least_6_months", "started_si_before_2014"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 110 khoản 2", "exception_to": "", "quote": "Mức trợ cấp tuất một lần đối với thân nhân của người đang tham gia bảo hiểm xã hội tự nguyện... Bằng 1,5 lần của mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội cho những năm đóng bảo hiểm xã hội trước năm 2014."}
{"id": "LAB-10-D110-002", "type": "condition", "premises": ["voluntary_si_eligible", "term_at_least_6_months", "started_si_after_2014"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 110 khoản 2", "exception_to": "", "quote": "Bằng 02 lần của mức bình quân thu nhập làm căn cứ đóng bảo hiểm xã hội cho các năm đóng bảo hiểm xã hội từ năm 2014 trở đi."}
{"id": "LAB-10-D110-003", "type": "condition", "premises": ["voluntary_si_eligible", "~term_at_least_6_months"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 110 khoản 2", "exception_to": "", "quote": "Bằng số tiền đã đóng đối với trường hợp người lao động có thời gian đóng chưa đủ 60 tháng."}
{"id": "LAB-10-D110-004", "type": "condition", "premises": ["voluntary_si_eligible", "has_full_contribution_time", "deceased"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 110 khoản 3", "exception_to": "", "quote": "mức hưởng trợ cấp tuất một lần tối thiểu bằng 03 lần của mức bình quân tiền lương và thu nhập làm căn cứ đóng bảo hiểm xã hội."}
{"id": "LAB-10-D110-005", "type": "condition", "premises": ["receiving_pension", "deceased"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 110 khoản 4", "exception_to": "", "quote": "Mức trợ cấp tuất một lần đối với thân nhân của người đang hưởng lương hưu hoặc đang tạm dừng hưởng lương hưu chết được tính theo thời gian đã hưởng lương hưu."}
{"id": "LAB-10-D110-006", "type": "condition", "premises": ["receiving_pension", "deceased", "term_at_least_1_month"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 110 khoản 4", "exception_to": "", "quote": "Trường hợp chết trong 02 tháng đầu thì mức trợ cấp tuất một lần bằng 48 tháng lương hưu của tháng đang hưởng."}
{"id": "LAB-10-D110-007", "type": "condition", "premises": ["receiving_pension", "deceased", "~term_at_least_1_month"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 110 khoản 4", "exception_to": "", "quote": "Trường hợp chết từ tháng thứ ba trở đi thì cứ mỗi tháng mức trợ cấp tuất một lần giảm 0,5 tháng lương hưu."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 111. Chế độ hưu trí và chế độ tử tuất đối với người vừa có thời gian đóng bảo hiểm xã
[NGUYÊN VĂN]
Điều 111. Chế độ hưu trí và chế độ tử tuất đối với người vừa có thời gian đóng bảo hiểm xã 
hội bắt buộc vừa có thời gian đóng bảo hiểm xã hội tự nguyện 
1. Chế độ hưu trí và chế độ tử tuất đối với người vừa có thời gian đóng bảo hiểm xã hội bắt buộc 
vừa có thời gian đóng bảo hiểm xã hội tự nguyện được quy định như sau: 
a) Có từ đủ 15 năm đóng bảo hiểm xã hội bắt buộc trở lên nếu thuộc đối tượng quy định tại Điều 
64 của Luật này, có từ đủ 20 năm đóng bảo hiểm xã hội bắt buộc trở lên nếu thuộc đối tượng quy 
định tại Điều 65 của Luật này thì điều kiện, mức hưởng lương hưu thực hiện theo chính sách bảo 
hiểm xã hội bắt buộc; 
b) Có từ đủ 15 năm đóng bảo hiểm xã hội bắt buộc trở lên thì được hưởng trợ cấp tuất hằng 
tháng theo chính sách bảo hiểm xã hội bắt buộc; 
c) Có từ đủ 12 tháng đóng bảo hiểm xã hội bắt buộc trở lên thì được hưởng trợ cấp mai táng theo 
chính sách bảo hiểm xã hội bắt buộc. 
2. Chính phủ quy định chi tiết Điều này.

[RULES]
{"id": "LAB-10-D111-000", "type": "condition", "premises": ["contribution_15_years", "covered_point_a"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 111 khoản 1 điểm a", "exception_to": "", "quote": "Có từ đủ 15 năm đóng bảo hiểm xã hội bắt buộc trở lên nếu thuộc đối tượng quy định tại Điều 64 của Luật này..."}
{"id": "LAB-10-D111-001", "type": "condition", "premises": ["contribution_20_years", "covered_point_b"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 111 khoản 1 điểm a", "exception_to": "", "quote": "Có từ đủ 20 năm đóng bảo hiểm xã hội bắt buộc trở lên nếu thuộc đối tượng quy định tại Điều 65 của Luật này..."}
{"id": "LAB-10-D111-002", "type": "condition", "premises": ["contribution_15_years"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 111 khoản 1 điểm b", "exception_to": "", "quote": "Có từ đủ 15 năm đóng bảo hiểm xã hội bắt buộc trở lên thì được hưởng trợ cấp tuất hằng tháng theo chính sách bảo hiểm xã hội bắt buộc."}
{"id": "LAB-10-D111-003", "type": "condition", "premises": ["term_at_least_12_months"], "conclusion": "funeral_support", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 111 khoản 1 điểm c", "exception_to": "", "quote": "Có từ đủ 12 tháng đóng bảo hiểm xã hội bắt buộc trở lên thì được hưởng trợ cấp mai táng theo chính sách bảo hiểm xã hội bắt buộc."}
{"id": "LAB-10-D111-004", "type": "lookup", "premises": [], "conclusion": "government_regulates_pension_procedures", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 111 khoản 2", "exception_to": "", "quote": "Chính phủ quy định chi tiết Điều này."}
