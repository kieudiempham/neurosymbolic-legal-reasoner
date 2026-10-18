

######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 66. Mức lương hưu hằng tháng
[NGUYÊN VĂN]
Điều 66. Mức lương hưu hằng tháng 
1. Mức lương hưu hằng tháng của đối tượng đủ điều kiện quy định tại Điều 64 của Luật này 
được tính như sau: 
a) Đối với lao động nữ bằng 45% mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội 
quy định tại Điều 72 của Luật này tương ứng 15 năm đóng bảo hiểm xã hội, sau đó cứ thêm mỗi 
năm đóng thì tính thêm 2%, mức tối đa bằng 75%; 
b) Đối với lao động nam bằng 45% mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội 
quy định tại Điều 72 của Luật này tương ứng 20 năm đóng bảo hiểm xã hội, sau đó cứ thêm mỗi 
năm đóng thì tính thêm 2%, mức tối đa bằng 75%. 
Trường hợp lao động nam có thời gian đóng bảo hiểm xã hội từ đủ 15 năm đến dưới 20 năm, 
mức lương hưu hằng tháng bằng 40% mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã 
hội quy định tại Điều 72 của Luật này tương ứng 15 năm đóng bảo hiểm xã hội, sau đó cứ thêm 
mỗi năm đóng thì tính thêm 1%. 
2. Mức lương hưu hằng tháng của đối tượng là người lao động thuộc một số nghề, công việc đặc 
biệt đặc thù trong lực lượng vũ trang nhân dân do Chính phủ quy định. Nguồn kinh phí thực hiện 
từ ngân sách nhà nước. 
3. Mức lương hưu hằng tháng của đối tượng đủ điều kiện quy định tại Điều 65 của Luật này 
được tính như quy định tại khoản 1 Điều này, sau đó cứ mỗi năm nghỉ hưu trước tuổi quy định 
thì giảm 2%. 
Trường hợp thời gian nghỉ hưu trước tuổi dưới 06 tháng thì không giảm tỷ lệ phần trăm hưởng 
lương hưu, từ đủ 06 tháng đến dưới 12 tháng thì giảm 1%. 
4. Việc tính mức lương hưu hằng tháng của người lao động đủ điều kiện hưởng lương hưu mà có 
thời gian đóng bảo hiểm xã hội theo quy định của điều ước quốc tế mà nước Cộng hòa xã hội 
chủ nghĩa Việt Nam là thành viên nhưng có thời gian đóng bảo hiểm xã hội ở Việt Nam dưới 15 
năm thì mỗi năm đóng trong thời gian này được tính bằng 2,25% mức bình quân tiền lương làm 
căn cứ đóng bảo hiểm xã hội quy định tại Điều 72 của Luật này. 
5. Chính phủ quy định chi tiết về mức hưởng và điều kiện hưởng lương hưu.

[RULES]
{"id": "LAB-10-D66-000", "type": "condition", "premises": ["contribution_15_years", "covered_point_a"], "conclusion": "pension_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 66 khoản 1", "exception_to": "", "quote": "Mức lương hưu hằng tháng của đối tượng đủ điều kiện quy định tại Điều 64 của Luật này được tính như sau: Đối với lao động nữ bằng 45% mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội..."}
{"id": "LAB-10-D66-001", "type": "condition", "premises": ["contribution_15_years", "covered_point_b"], "conclusion": "pension_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 66 khoản 1", "exception_to": "", "quote": "Mức lương hưu hằng tháng của đối tượng đủ điều kiện quy định tại Điều 64 của Luật này được tính như sau: Đối với lao động nam bằng 45% mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội..."}
{"id": "LAB-10-D66-002", "type": "condition", "premises": ["contribution_15_years", "covered_point_b", "~contribution_30_years"], "conclusion": "pension_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 66 khoản 1", "exception_to": "", "quote": "Trường hợp lao động nam có thời gian đóng bảo hiểm xã hội từ đủ 15 năm đến dưới 20 năm, mức lương hưu hằng tháng bằng 40% mức bình quân tiền lương..."}
{"id": "LAB-10-D66-003", "type": "condition", "premises": ["entitled_pension", "~retirement_age_at_signing"], "conclusion": "pension_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 66 khoản 3", "exception_to": "", "quote": "Mức lương hưu hằng tháng của đối tượng đủ điều kiện quy định tại Điều 65 của Luật này được tính như quy định tại khoản 1 Điều này, sau đó cứ mỗi năm nghỉ hưu trước tuổi quy định thì giảm 2%."}
{"id": "LAB-10-D66-004", "type": "condition", "premises": ["is_member_international_agreement", "~contribution_15_years"], "conclusion": "pension_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 66 khoản 4", "exception_to": "", "quote": "Việc tính mức lương hưu hằng tháng của người lao động đủ điều kiện hưởng lương hưu mà có thời gian đóng bảo hiểm xã hội theo quy định của điều ước quốc tế mà nước Cộng hòa xã hội chủ nghĩa Việt Nam là thành viên..."}
{"id": "LAB-10-D66-005", "type": "lookup", "premises": [], "conclusion": "government_regulates_si_calculation", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 66 khoản 5", "exception_to": "", "quote": "Chính phủ quy định chi tiết về mức hưởng và điều kiện hưởng lương hưu."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 67. Điều chỉnh lương hưu
[NGUYÊN VĂN]
Điều 67. Điều chỉnh lương hưu 
1. Lương hưu được điều chỉnh trên cơ sở mức tăng của chỉ số giá tiêu dùng phù hợp với khả 
năng của ngân sách nhà nước và quỹ bảo hiểm xã hội. 
2. Điều chỉnh mức tăng lương hưu thỏa đáng đối với đối tượng có mức lương hưu thấp và nghỉ 
hưu trước năm 1995 bảo đảm thu hẹp khoảng cách chênh lệch lương hưu giữa người nghỉ hưu ở 
các thời kỳ. 
3. Chính phủ quy định thời điểm, đối tượng, mức điều chỉnh lương hưu quy định tại Điều này.

[RULES]
{"id": "LAB-10-D67-000", "type": "condition", "premises": [], "conclusion": "adjusted_pension_based_on_cpi", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 67 khoản 1", "exception_to": "", "quote": "Lương hưu được điều chỉnh trên cơ sở mức tăng của chỉ số giá tiêu dùng phù hợp với khả năng của ngân sách nhà nước và quỹ bảo hiểm xã hội."}
{"id": "LAB-10-D67-001", "type": "condition", "premises": ["low_pension", "retired_before_1995"], "conclusion": "adjusted_pension_for_low_income", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 67 khoản 2", "exception_to": "", "quote": "Điều chỉnh mức tăng lương hưu thỏa đáng đối với đối tượng có mức lương hưu thấp và nghỉ hưu trước năm 1995 bảo đảm thu hẹp khoảng cách chênh lệch lương hưu giữa người nghỉ hưu ở các thời kỳ."}
{"id": "LAB-10-D67-002", "type": "condition", "premises": [], "conclusion": "government_regulates_pension_adjustment", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 67 khoản 3", "exception_to": "", "quote": "Chính phủ quy định thời điểm, đối tượng, mức điều chỉnh lương hưu quy định tại Điều này."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 68. Trợ cấp một lần khi nghỉ hưu
[NGUYÊN VĂN]
Điều 68. Trợ cấp một lần khi nghỉ hưu 
1. Lao động nam có thời gian đóng bảo hiểm xã hội cao hơn 35 năm, lao động nữ có thời gian 
đóng bảo hiểm xã hội cao hơn 30 năm thì khi nghỉ hưu, ngoài lương hưu còn được hưởng trợ cấp 
một lần. 
2. Mức hưởng trợ cấp một lần cho mỗi năm đóng cao hơn quy định tại khoản 1 Điều này bằng 
0,5 lần của mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội quy định tại Điều 72 của 
Luật này cho mỗi năm đóng cao hơn đến tuổi nghỉ hưu theo quy định của pháp luật. 
Trường hợp người lao động đã đủ điều kiện hưởng lương hưu theo quy định tại Điều 64 và Điều 
65 của Luật này mà tiếp tục đóng bảo hiểm xã hội thì mức trợ cấp bằng 02 lần của mức bình 
quân tiền lương làm căn cứ đóng bảo hiểm xã hội quy định tại Điều 72 của Luật này cho mỗi 
năm đóng cao hơn số năm quy định tại khoản 1 Điều này kể từ sau thời điểm đủ tuổi nghỉ hưu 
theo quy định của pháp luật đến thời điểm nghỉ hưu.

[RULES]
{"id": "LAB-10-D68-000", "type": "condition", "premises": ["contribution_30_years", "is_female_worker"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 68 khoản 1", "exception_to": "", "quote": "Lao động nữ có thời gian đóng bảo hiểm xã hội cao hơn 30 năm thì khi nghỉ hưu, ngoài lương hưu còn được hưởng trợ cấp một lần."}
{"id": "LAB-10-D68-001", "type": "condition", "premises": ["contribution_30_years", "is_male_worker"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 68 khoản 1", "exception_to": "", "quote": "Lao động nam có thời gian đóng bảo hiểm xã hội cao hơn 35 năm thì khi nghỉ hưu, ngoài lương hưu còn được hưởng trợ cấp một lần."}
{"id": "LAB-10-D68-002", "type": "condition", "premises": ["entitled_lump_sum", "time_of_contribution"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 68 khoản 2", "exception_to": "", "quote": "Mức hưởng trợ cấp một lần cho mỗi năm đóng cao hơn quy định tại khoản 1 Điều này bằng 0,5 lần của mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội."}
{"id": "LAB-10-D68-003", "type": "condition", "premises": ["entitled_pension", "agreed_contribution"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 68 khoản 2", "exception_to": "", "quote": "Trường hợp người lao động đã đủ điều kiện hưởng lương hưu mà tiếp tục đóng bảo hiểm xã hội thì mức trợ cấp bằng 02 lần của mức bình quân tiền lương."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 69. Thời điểm hưởng lương hưu
[NGUYÊN VĂN]
Điều 69. Thời điểm hưởng lương hưu 
1. Thời điểm hưởng lương hưu đối với đối tượng quy định tại các điểm a, b, c, d, đ, e, i, k và l 
khoản 1 và khoản 2 Điều 2 của Luật này đang tham gia bảo hiểm xã hội bắt buộc là thời điểm đủ 
điều kiện hưởng lương hưu theo quy định và được ghi trong văn bản của người sử dụng lao động 
xác định việc chấm dứt hợp đồng lao động hoặc xác định việc chấm dứt làm việc. 
2. Thời điểm hưởng lương hưu đối với đối tượng quy định tại các điểm g, h, m và n khoản 1 
Điều 2 của Luật này và người đang bảo lưu thời gian đóng bảo hiểm xã hội là thời điểm đủ điều 
kiện hưởng lương hưu theo quy định và được ghi trong văn bản đề nghị của người lao động. 
3. Bộ trưởng Bộ Lao động - Thương binh và Xã hội quy định chi tiết Điều này; quy định thời 
điểm hưởng lương hưu đối với trường hợp quy định tại khoản 7 Điều 33 của Luật này; quy định 
về việc tính, việc xác định điều kiện đối với từng trường hợp để giải quyết chế độ hưu trí.

[RULES]
{"id": "LAB-10-D69-000", "type": "condition", "premises": ["covered_point_a", "compulsory_si"], "conclusion": "entitled_pension", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 69 khoản 1", "exception_to": "", "quote": "Thời điểm hưởng lương hưu đối với đối tượng quy định tại các điểm a, b, c, d, đ, e, i, k và l khoản 1 và khoản 2 Điều 2 của Luật này đang tham gia bảo hiểm xã hội bắt buộc là thời điểm đủ điều kiện hưởng lương hưu theo quy định."}
{"id": "LAB-10-D69-001", "type": "condition", "premises": ["covered_point_b", "compulsory_si"], "conclusion": "entitled_pension", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 69 khoản 1", "exception_to": "", "quote": "Thời điểm hưởng lương hưu đối với đối tượng quy định tại các điểm a, b, c, d, đ, e, i, k và l khoản 1 và khoản 2 Điều 2 của Luật này đang tham gia bảo hiểm xã hội bắt buộc là thời điểm đủ điều kiện hưởng lương hưu theo quy định."}
{"id": "LAB-10-D69-002", "type": "condition", "premises": ["covered_point_d", "compulsory_si"], "conclusion": "entitled_pension", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 69 khoản 1", "exception_to": "", "quote": "Thời điểm hưởng lương hưu đối với đối tượng quy định tại các điểm a, b, c, d, đ, e, i, k và l khoản 1 và khoản 2 Điều 2 của Luật này đang tham gia bảo hiểm xã hội bắt buộc là thời điểm đủ điều kiện hưởng lương hưu theo quy định."}
{"id": "LAB-10-D69-003", "type": "condition", "premises": ["covered_point_g", "compulsory_si"], "conclusion": "entitled_pension", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 69 khoản 2", "exception_to": "", "quote": "Thời điểm hưởng lương hưu đối với đối tượng quy định tại các điểm g, h, m và n khoản 1 Điều 2 của Luật này và người đang bảo lưu thời gian đóng bảo hiểm xã hội là thời điểm đủ điều kiện hưởng lương hưu theo quy định."}
{"id": "LAB-10-D69-004", "type": "condition", "premises": ["covered_point_h", "compulsory_si"], "conclusion": "entitled_pension", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 69 khoản 2", "exception_to": "", "quote": "Thời điểm hưởng lương hưu đối với đối tượng quy định tại các điểm g, h, m và n khoản 1 Điều 2 của Luật này và người đang bảo lưu thời gian đóng bảo hiểm xã hội là thời điểm đủ điều kiện hưởng lương hưu theo quy định."}
{"id": "LAB-10-D69-005", "type": "condition", "premises": ["covered_point_m", "compulsory_si"], "conclusion": "entitled_pension", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 69 khoản 2", "exception_to": "", "quote": "Thời điểm hưởng lương hưu đối với đối tượng quy định tại các điểm g, h, m và n khoản 1 Điều 2 của Luật này và người đang bảo lưu thời gian đóng bảo hiểm xã hội là thời điểm đủ điều kiện hưởng lương hưu theo quy định."}
{"id": "LAB-10-D69-006", "type": "condition", "premises": ["covered_point_n", "compulsory_si"], "conclusion": "entitled_pension", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 69 khoản 2", "exception_to": "", "quote": "Thời điểm hưởng lương hưu đối với đối tượng quy định tại các điểm g, h, m và n khoản 1 Điều 2 của Luật này và người đang bảo lưu thời gian đóng bảo hiểm xã hội là thời điểm đủ điều kiện hưởng lương hưu theo quy định."}
{"id": "LAB-10-D69-007", "type": "lookup", "premises": [], "conclusion": "government_regulates_si_calculation", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 69 khoản 3", "exception_to": "", "quote": "Bộ trưởng Bộ Lao động - Thương binh và Xã hội quy định chi tiết Điều này; quy định thời điểm hưởng lương hưu đối với trường hợp quy định tại khoản 7 Điều 33 của Luật này; quy định về việc tính, việc xác định điều kiện đối với từng trường hợp để giải quyết chế độ hưu trí."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 70. Hưởng bảo hiểm xã hội một lần
[NGUYÊN VĂN]
Điều 70. Hưởng bảo hiểm xã hội một lần 
1. Đối tượng quy định tại khoản 1 Điều 2 của Luật này đã chấm dứt tham gia bảo hiểm xã hội mà 
có đề nghị thì được hưởng bảo hiểm xã hội một lần nếu thuộc một trong các trường hợp sau đây: 
a) Đủ tuổi hưởng lương hưu mà chưa đủ 15 năm đóng bảo hiểm xã hội. 
Trường hợp người lao động không hưởng bảo hiểm xã hội một lần thì có thể lựa chọn hưởng trợ 
cấp hằng tháng theo quy định tại Điều 23 của Luật này; 
b) Ra nước ngoài để định cư; 
c) Người đang mắc một trong những bệnh ung thư, bại liệt, xơ gan mất bù, lao nặng, AIDS; 
d) Người có mức suy giảm khả năng lao động từ 81% trở lên; người khuyết tật đặc biệt nặng; 
đ) Người lao động có thời gian đóng bảo hiểm xã hội trước ngày Luật này có hiệu lực thi hành, 
sau 12 tháng không thuộc đối tượng tham gia bảo hiểm xã hội bắt buộc mà cũng không tham gia 
bảo hiểm xã hội tự nguyện và có thời gian đóng bảo hiểm xã hội chưa đủ 20 năm; 
e) Trường hợp quy định tại các điểm d, đ và e khoản 1 Điều 2 của Luật này khi phục viên, xuất 
ngũ, thôi việc không thuộc đối tượng tham gia bảo hiểm xã hội bắt buộc mà cũng không tham 
gia bảo hiểm xã hội tự nguyện và không đủ điều kiện để hưởng lương hưu. 
2. Đối tượng quy định tại khoản 2 Điều 2 của Luật này đã chấm dứt tham gia bảo hiểm xã hội mà 
có đề nghị thì được hưởng bảo hiểm xã hội một lần nếu thuộc một trong các trường hợp sau đây: 
a) Đủ tuổi hưởng lương hưu mà chưa đủ 15 năm đóng bảo hiểm xã hội; 
b) Người đang mắc một trong những bệnh ung thư, bại liệt, xơ gan mất bù, lao nặng, AIDS; 
c) Người có mức suy giảm khả năng lao động từ 81% trở lên; người khuyết tật đặc biệt nặng; 
d) Người lao động đủ điều kiện hưởng lương hưu theo quy định nhưng không tiếp tục cư trú tại 
Việt Nam; 
đ) Người lao động khi chấm dứt hợp đồng lao động hoặc giấy phép lao động, chứng chỉ hành 
nghề, giấy phép hành nghề hết hiệu lực mà không được gia hạn. 
3. Mức hưởng bảo hiểm xã hội một lần được tính theo số năm đã đóng và căn cứ đóng bảo hiểm 
xã hội nhưng không bao gồm số tiền ngân sách nhà nước hỗ trợ đóng bảo hiểm xã hội tự nguyện, 
cứ mỗi năm được tính như sau: 
a) Bằng 1,5 tháng mức bình quân tiền lương tháng đóng bảo hiểm xã hội đối với năm đóng trước 
năm 2014. 
Trường hợp có thời gian đóng bảo hiểm xã hội trước và sau năm 2014 mà thời gian đóng trước 
năm 2014 có tháng lẻ thì những tháng lẻ đó được chuyển sang giai đoạn đóng bảo hiểm xã hội từ 
năm 2014 trở đi để tính mức hưởng bảo hiểm xã hội một lần; 
b) Bằng 02 tháng mức bình quân tiền lương tháng đóng bảo hiểm xã hội đối với năm đóng từ 
năm 2014 trở đi; 
c) Trường hợp thời gian đóng bảo hiểm xã hội chưa đủ một năm thì mức hưởng bằng số tiền đã 
đóng nhưng không quá 02 tháng mức bình quân tiền lương tháng đóng bảo hiểm xã hội. 
4. Trường hợp quy định tại điểm c và điểm d khoản 1 Điều này thì mức hưởng bảo hiểm xã hội 
một lần được tính theo số năm đã đóng và căn cứ đóng bảo hiểm xã hội bao gồm số tiền ngân 
sách nhà nước hỗ trợ đóng bảo hiểm xã hội tự nguyện; việc tính mức hưởng mỗi năm thực hiện 
theo quy định tại các điểm a, b và c khoản 3 Điều này. 
5. Thời điểm tính hưởng bảo hiểm xã hội một lần là thời điểm cơ quan bảo hiểm xã hội ban hành 
quyết định hưởng bảo hiểm xã hội một lần. 
6. Trường hợp người lao động quy định tại các điểm b, c và d khoản 1 và các điểm b, c và đ 
khoản 2 Điều này vừa đủ điều kiện hưởng lương hưu vừa đủ điều kiện hưởng bảo hiểm xã hội 
một lần thì người lao động được lựa chọn hưởng lương hưu hằng tháng hoặc hưởng bảo hiểm xã 
hội một lần. 
7. Chính phủ quy định chi tiết Điều này.

[RULES]
{"id": "LAB-10-D70-000", "type": "condition", "premises": ["terminated_participation", "requested_lump_sum", "retirement_age_at_signing", "~contribution_15_years"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 70 khoản 1 điểm a", "exception_to": "", "quote": "Đủ tuổi hưởng lương hưu mà chưa đủ 15 năm đóng bảo hiểm xã hội."}
{"id": "LAB-10-D70-001", "type": "condition", "premises": ["terminated_participation", "requested_lump_sum", "emigrating"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 70 khoản 1 điểm b", "exception_to": "", "quote": "Ra nước ngoài để định cư."}
{"id": "LAB-10-D70-002", "type": "condition", "premises": ["terminated_participation", "requested_lump_sum", "serious_illness"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 70 khoản 1 điểm c", "exception_to": "", "quote": "Người đang mắc một trong những bệnh ung thư, bại liệt, xơ gan mất bù, lao nặng, AIDS."}
{"id": "LAB-10-D70-003", "type": "condition", "premises": ["terminated_participation", "requested_lump_sum", "~contribution_30_years", "~contribution_15_years"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 70 khoản 1 điểm d", "exception_to": "", "quote": "Người có mức suy giảm khả năng lao động từ 81% trở lên; người khuyết tật đặc biệt nặng."}
{"id": "LAB-10-D70-004", "type": "condition", "premises": ["terminated_participation", "requested_lump_sum", "~contribution_15_years"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 70 khoản 1 điểm đ", "exception_to": "", "quote": "Người lao động có thời gian đóng bảo hiểm xã hội trước ngày Luật này có hiệu lực thi hành, sau 12 tháng không thuộc đối tượng tham gia bảo hiểm xã hội bắt buộc mà cũng không tham gia bảo hiểm xã hội tự nguyện và có thời gian đóng bảo hiểm xã hội chưa đủ 20 năm."}
{"id": "LAB-10-D70-005", "type": "condition", "premises": ["terminated_participation", "requested_lump_sum", "~contribution_15_years"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 70 khoản 1 điểm e", "exception_to": "", "quote": "Trường hợp quy định tại các điểm d, đ và e khoản 1 Điều 2 của Luật này khi phục viên, xuất ngũ, thôi việc không thuộc đối tượng tham gia bảo hiểm xã hội bắt buộc mà cũng không tham gia bảo hiểm xã hội tự nguyện và không đủ điều kiện để hưởng lương hưu."}
{"id": "LAB-10-D70-006", "type": "condition", "premises": ["terminated_participation", "requested_lump_sum", "retirement_age_at_signing", "~contribution_15_years"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 70 khoản 2 điểm a", "exception_to": "", "quote": "Đủ tuổi hưởng lương hưu mà chưa đủ 15 năm đóng bảo hiểm xã hội."}
{"id": "LAB-10-D70-007", "type": "condition", "premises": ["terminated_participation", "requested_lump_sum", "serious_illness"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 70 khoản 2 điểm b", "exception_to": "", "quote": "Người đang mắc một trong những bệnh ung thư, bại liệt, xơ gan mất bù, lao nặng, AIDS."}
{"id": "LAB-10-D70-008", "type": "condition", "premises": ["terminated_participation", "requested_lump_sum", "~contribution_30_years"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 70 khoản 2 điểm c", "exception_to": "", "quote": "Người có mức suy giảm khả năng lao động từ 81% trở lên; người khuyết tật đặc biệt nặng."}
{"id": "LAB-10-D70-009", "type": "condition", "premises": ["terminated_participation", "requested_lump_sum", "~not_paid_si_after_60_days"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 70 khoản 2 điểm d", "exception_to": "", "quote": "Người lao động đủ điều kiện hưởng lương hưu theo quy định nhưng không tiếp tục cư trú tại Việt Nam."}
{"id": "LAB-10-D70-010", "type": "condition", "premises": ["terminated_participation", "requested_lump_sum", "not_paid_si_after_60_days"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 70 khoản 2 điểm đ", "exception_to": "", "quote": "Người lao động khi chấm dứt hợp đồng lao động hoặc giấy phép lao động, chứng chỉ hành nghề, giấy phép hành nghề hết hiệu lực mà không được gia hạn."}
{"id": "LAB-10-D70-011", "type": "lookup", "premises": [], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 70 khoản 3", "exception_to": "", "quote": "Mức hưởng bảo hiểm xã hội một lần được tính theo số năm đã đóng và căn cứ đóng bảo hiểm xã hội nhưng không bao gồm số tiền ngân sách nhà nước hỗ trợ đóng bảo hiểm xã hội tự nguyện."}
{"id": "LAB-10-D70-012", "type": "condition", "premises": ["terminated_participation", "requested_lump_sum", "serious_illness"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 70 khoản 4", "exception_to": "", "quote": "Trường hợp quy định tại điểm c và điểm d khoản 1 Điều này thì mức hưởng bảo hiểm xã hội một lần được tính theo số năm đã đóng và căn cứ đóng bảo hiểm xã hội bao gồm số tiền ngân sách nhà nước hỗ trợ đóng bảo hiểm xã hội tự nguyện."}
{"id": "LAB-10-D70-013", "type": "condition", "premises": ["terminated_participation", "requested_lump_sum", "entitled_pension"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 70 khoản 6", "exception_to": "", "quote": "Trường hợp người lao động quy định tại các điểm b, c và d khoản 1 và các điểm b, c và đ khoản 2 Điều này vừa đủ điều kiện hưởng lương hưu vừa đủ điều kiện hưởng bảo hiểm xã hội một lần thì người lao động được lựa chọn hưởng lương hưu hằng tháng hoặc hưởng bảo hiểm xã hội một lần."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 71. Bảo lưu thời gian đóng bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 71. Bảo lưu thời gian đóng bảo hiểm xã hội 
Người lao động khi nghỉ việc mà chưa đủ điều kiện để hưởng lương hưu theo quy định tại Điều 
64, Điều 65 của Luật này hoặc chưa hưởng bảo hiểm xã hội một lần theo quy định tại Điều 70 
của Luật này hoặc chưa hưởng trợ cấp hằng tháng theo quy định tại Điều 23 của Luật này thì 
được bảo lưu thời gian đóng bảo hiểm xã hội.

[RULES]
{"id": "LAB-10-D71-000", "type": "condition", "premises": ["not_entitled_pension", "not_entitled_lump_sum", "not_entitled_monthly_allowance"], "conclusion": "can_preserve_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 71 khoản 1", "exception_to": "", "quote": "Người lao động khi nghỉ việc mà chưa đủ điều kiện để hưởng lương hưu... thì được bảo lưu thời gian đóng bảo hiểm xã hội."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 72. Mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội để tính lương hưu, trợ
[NGUYÊN VĂN]
Điều 72. Mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội để tính lương hưu, trợ 
cấp một lần 
1. Người lao động thuộc đối tượng thực hiện chế độ tiền lương do Nhà nước quy định có toàn bộ 
thời gian đóng bảo hiểm xã hội theo chế độ tiền lương này thì tính bình quân tiền lương làm căn 
cứ đóng bảo hiểm xã hội của số năm đóng bảo hiểm xã hội trước khi nghỉ hưu như sau: 
a) Bắt đầu tham gia bảo hiểm xã hội trước ngày 01 tháng 01 năm 1995 thì tính bình quân tiền 
lương làm căn cứ đóng bảo hiểm xã hội của 05 năm cuối trước khi nghỉ hưu; 
b) Bắt đầu tham gia bảo hiểm xã hội trong khoảng thời gian từ ngày 01 tháng 01 năm 1995 đến 
ngày 31 tháng 12 năm 2000 thì tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội của 
06 năm cuối trước khi nghỉ hưu; 
c) Bắt đầu tham gia bảo hiểm xã hội trong khoảng thời gian từ ngày 01 tháng 01 năm 2001 đến 
ngày 31 tháng 12 năm 2006 thì tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội của 
08 năm cuối trước khi nghỉ hưu; 
d) Bắt đầu tham gia bảo hiểm xã hội trong khoảng thời gian từ ngày 01 tháng 01 năm 2007 đến 
ngày 31 tháng 12 năm 2015 thì tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội của 
10 năm cuối trước khi nghỉ hưu; 
đ) Bắt đầu tham gia bảo hiểm xã hội từ ngày 01 tháng 01 năm 2016 đến ngày 31 tháng 12 năm 
2019 thì tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội của 15 năm cuối trước khi 
nghỉ hưu; 
e) Bắt đầu tham gia bảo hiểm xã hội từ ngày 01 tháng 01 năm 2020 đến ngày 31 tháng 12 năm 
2024 thì tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội của 20 năm cuối trước khi 
nghỉ hưu; 
g) Bắt đầu tham gia bảo hiểm xã hội từ ngày 01 tháng 01 năm 2025 trở đi thì tính bình quân tiền 
lương làm căn cứ đóng bảo hiểm xã hội của toàn bộ thời gian đóng bảo hiểm xã hội. 
2. Người lao động có toàn bộ thời gian đóng bảo hiểm xã hội theo chế độ tiền lương do người sử 
dụng lao động quyết định thì tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội của 
toàn bộ thời gian. 
3. Người lao động vừa có thời gian đóng bảo hiểm xã hội thuộc đối tượng thực hiện chế độ tiền 
lương do Nhà nước quy định, vừa có thời gian đóng bảo hiểm xã hội theo chế độ tiền lương do 
người sử dụng lao động quyết định thì tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã 
hội chung của các thời gian, trong đó thời gian đóng theo chế độ tiền lương do Nhà nước quy 
định được tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội theo quy định tại khoản 1 
Điều này. 
4. Chính phủ quy định chi tiết Điều này và quy định mức bình quân tiền lương làm căn cứ đóng 
bảo hiểm xã hội đối với người lao động thực hiện chế độ tiền lương do Nhà nước quy định trong 
một số trường hợp đặc biệt.

[RULES]
{"id": "LAB-10-D72-000", "type": "condition", "premises": ["started_si_before_1995", "has_full_contribution_time"], "conclusion": "calculate_average_wage_based_on_5_years", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 72 khoản 1 điểm a", "exception_to": "", "quote": "tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội của 05 năm cuối trước khi nghỉ hưu"}
{"id": "LAB-10-D72-001", "type": "condition", "premises": ["started_si_between_1995_and_2000", "has_full_contribution_time"], "conclusion": "calculate_average_wage_based_on_6_years", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 72 khoản 1 điểm b", "exception_to": "", "quote": "tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội của 06 năm cuối trước khi nghỉ hưu"}
{"id": "LAB-10-D72-002", "type": "condition", "premises": ["started_si_between_2001_and_2006", "has_full_contribution_time"], "conclusion": "calculate_average_wage_based_on_8_years", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 72 khoản 1 điểm c", "exception_to": "", "quote": "tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội của 08 năm cuối trước khi nghỉ hưu"}
{"id": "LAB-10-D72-003", "type": "condition", "premises": ["started_si_between_2007_and_2015", "has_full_contribution_time"], "conclusion": "calculate_average_wage_based_on_10_years", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 72 khoản 1 điểm d", "exception_to": "", "quote": "tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội của 10 năm cuối trước khi nghỉ hưu"}
{"id": "LAB-10-D72-004", "type": "condition", "premises": ["started_si_between_2016_and_2019", "has_full_contribution_time"], "conclusion": "calculate_average_wage_based_on_15_years", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 72 khoản 1 điểm đ", "exception_to": "", "quote": "tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội của 15 năm cuối trước khi nghỉ hưu"}
{"id": "LAB-10-D72-005", "type": "condition", "premises": ["started_si_between_2020_and_2024", "has_full_contribution_time"], "conclusion": "calculate_average_wage_based_on_20_years", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 72 khoản 1 điểm e", "exception_to": "", "quote": "tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội của 20 năm cuối trước khi nghỉ hưu"}
{"id": "LAB-10-D72-006", "type": "condition", "premises": ["started_si_after_2025", "has_full_contribution_time"], "conclusion": "calculate_average_wage_based_on_full_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 72 khoản 1 điểm g", "exception_to": "", "quote": "tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội của toàn bộ thời gian đóng bảo hiểm xã hội"}
{"id": "LAB-10-D72-007", "type": "condition", "premises": ["has_full_contribution_time_by_employer"], "conclusion": "calculate_average_wage_based_on_full_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 72 khoản 2", "exception_to": "", "quote": "tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội của toàn bộ thời gian"}
{"id": "LAB-10-D72-008", "type": "condition", "premises": ["has_full_contribution_time_by_state", "has_full_contribution_time_by_employer"], "conclusion": "calculate_average_wage_based_on_combined_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 72 khoản 3", "exception_to": "", "quote": "tính bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội chung của các thời gian"}
{"id": "LAB-10-D72-009", "type": "lookup", "premises": [], "conclusion": "government_regulates_si_calculation", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 72 khoản 4", "exception_to": "", "quote": "Chính phủ quy định chi tiết Điều này và quy định mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội đối với người lao động thực hiện chế độ tiền lương do Nhà nước quy định trong một số trường hợp đặc biệt."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 73. Điều chỉnh tiền lương làm căn cứ đóng bảo hiểm xã hội bắt buộc
[NGUYÊN VĂN]
Điều 73. Điều chỉnh tiền lương làm căn cứ đóng bảo hiểm xã hội bắt buộc 
1. Tiền lương làm căn cứ đóng bảo hiểm xã hội bắt buộc để tính mức bình quân quy định tại 
Điều 72 của Luật này của người lao động thuộc đối tượng thực hiện chế độ tiền lương do Nhà 
nước quy định được điều chỉnh như sau: 
a) Đối với người lao động bắt đầu tham gia bảo hiểm xã hội trước ngày 01 tháng 01 năm 2016, 
được điều chỉnh theo mức tham chiếu tại thời điểm hưởng chế độ hưu trí; 
b) Đối với người lao động bắt đầu tham gia bảo hiểm xã hội từ ngày 01 tháng 01 năm 2016 trở 
đi, được điều chỉnh như quy định tại khoản 2 Điều này. 
2. Tiền lương làm căn cứ đóng bảo hiểm xã hội bắt buộc để tính mức bình quân quy định tại 
Điều 72 của Luật này của người lao động thuộc đối tượng thực hiện chế độ tiền lương do người 
sử dụng lao động quyết định được điều chỉnh trên cơ sở chỉ số giá tiêu dùng của từng thời kỳ 
theo quy định của Chính phủ.

[RULES]
{"id": "LAB-10-D73-000", "type": "condition", "premises": ["compulsory_si", "covered_point_a"], "conclusion": "adjusted_reference_amount", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 73 khoản 1 điểm a", "exception_to": "", "quote": "Đối với người lao động bắt đầu tham gia bảo hiểm xã hội trước ngày 01 tháng 01 năm 2016, được điều chỉnh theo mức tham chiếu tại thời điểm hưởng chế độ hưu trí."}
{"id": "LAB-10-D73-001", "type": "condition", "premises": ["compulsory_si", "covered_point_b"], "conclusion": "adjusted_reference_amount", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 73 khoản 1 điểm b", "exception_to": "", "quote": "Đối với người lao động bắt đầu tham gia bảo hiểm xã hội từ ngày 01 tháng 01 năm 2016 trở đi, được điều chỉnh như quy định tại khoản 2 Điều này."}
{"id": "LAB-10-D73-002", "type": "condition", "premises": ["compulsory_si", "covered_point_b"], "conclusion": "adjusted_pension_based_on_cpi", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 73 khoản 2", "exception_to": "", "quote": "Tiền lương làm căn cứ đóng bảo hiểm xã hội bắt buộc để tính mức bình quân quy định tại Điều 72 của Luật này của người lao động thuộc đối tượng thực hiện chế độ tiền lương do người sử dụng lao động quyết định được điều chỉnh trên cơ sở chỉ số giá tiêu dùng của từng thời kỳ theo quy định của Chính phủ."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 74. Thực hiện bảo hiểm xã hội khi áp dụng chế độ tiền lương theo vị trí việc làm, chức
[NGUYÊN VĂN]
Điều 74. Thực hiện bảo hiểm xã hội khi áp dụng chế độ tiền lương theo vị trí việc làm, chức 
danh và chức vụ lãnh đạo thay thế cho hệ thống bảng lương hiện hành 
Trường hợp Nhà nước áp dụng chế độ tiền lương theo vị trí việc làm, chức danh và chức vụ lãnh 
đạo thay thế cho hệ thống bảng lương hiện hành thì Chính phủ báo cáo Quốc hội xem xét, quyết 
định việc điều chỉnh căn cứ đóng bảo hiểm xã hội bắt buộc, cách tính mức bình quân tiền lương 
làm căn cứ tính lương hưu, trợ cấp bảo hiểm xã hội, điều chỉnh tiền lương làm căn cứ đóng bảo 
hiểm xã hội bắt buộc và những nội dung cần thiết khác.

[RULES]
{"id": "LAB-10-D74-000", "type": "condition", "premises": ["government_review_pension_amount", "wage_at_least_min_base"], "conclusion": "government_regulates_si_calculation", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 74", "exception_to": "", "quote": "Chính phủ báo cáo Quốc hội xem xét, quyết định việc điều chỉnh căn cứ đóng bảo hiểm xã hội bắt buộc."}
{"id": "LAB-10-D74-001", "type": "condition", "premises": ["government_review_pension_amount", "wage_at_least_min_base"], "conclusion": "government_regulates_pension_adjustment", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 74", "exception_to": "", "quote": "Chính phủ báo cáo Quốc hội xem xét, quyết định việc điều chỉnh cách tính mức bình quân tiền lương làm căn cứ tính lương hưu."}
{"id": "LAB-10-D74-002", "type": "condition", "premises": ["government_review_pension_amount", "wage_at_least_min_base"], "conclusion": "government_regulates_si_calculation", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 74", "exception_to": "", "quote": "Chính phủ báo cáo Quốc hội xem xét, quyết định việc điều chỉnh tiền lương làm căn cứ đóng bảo hiểm xã hội bắt buộc."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 75. Tạm dừng, chấm dứt, tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng
[NGUYÊN VĂN]
Điều 75. Tạm dừng, chấm dứt, tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng 
tháng 
1. Tạm dừng việc hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng đối với người đang 
hưởng khi thuộc một trong các trường hợp sau đây: 
a) Xuất cảnh trái phép; 
b) Bị Tòa án tuyên bố mất tích; 
c) Khi không xác minh được thông tin người thụ hưởng theo quy định tại điểm c khoản 2 Điều 
11 của Luật này. 
2. Chấm dứt việc hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng đối với người đang 
hưởng khi thuộc một trong các trường hợp sau đây: 
a) Chết hoặc bị Tòa án tuyên bố là đã chết; 
b) Từ chối hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng bằng văn bản; 
c) Kết luận của cơ quan có thẩm quyền về hưởng bảo hiểm xã hội không đúng quy định của pháp 
luật. 
3. Lương hưu, trợ cấp bảo hiểm xã hội hằng tháng của đối tượng quy định tại khoản 1 và điểm a 
khoản 2 Điều này được tiếp tục chi trả bao gồm cả tiền lương hưu, trợ cấp bảo hiểm xã hội hằng 
tháng của thời gian chưa nhận khi thuộc một trong các trường hợp sau đây: 
a) Người xuất cảnh trái phép trở về; 
b) Có quyết định của Tòa án hủy bỏ quyết định tuyên bố mất tích hoặc quyết định tuyên bố là đã 
chết; 
c) Đối tượng quy định tại điểm c khoản 1 Điều này đã xác minh được thông tin theo quy định tại 
điểm c khoản 2 Điều 11 của Luật này. 
4. Lương hưu, trợ cấp bảo hiểm xã hội hằng tháng của đối tượng quy định tại điểm b khoản 2 
Điều này được tiếp tục chi trả kể từ thời điểm cơ quan bảo hiểm xã hội nhận văn bản đề nghị 
được hưởng lại lương hưu, trợ cấp bảo hiểm xã hội hằng tháng và không bao gồm tiền lương 
hưu, trợ cấp bảo hiểm xã hội hằng tháng của thời gian chưa nhận do từ chối nhận. 
5. Người hưởng lương hưu hoặc trợ cấp bảo hiểm xã hội hằng tháng có thời gian chưa nhận 
lương hưu, trợ cấp trước khi chết thì thân nhân của người đó được nhận lương hưu, trợ cấp của 
những tháng chưa nhận. 
6. Người bị tạm dừng hưởng lương hưu hoặc trợ cấp bảo hiểm xã hội hằng tháng khi có quyết 
định của Tòa án tuyên bố mất tích, sau đó có quyết định của Tòa án tuyên bố là đã chết thì thân 
nhân của người đó không được nhận lương hưu, trợ cấp trong thời gian tạm dừng hưởng. 
7. Các trường hợp tạm dừng, chấm dứt, hưởng tiếp lương hưu, trợ cấp bảo hiểm xã hội hằng 
tháng khác theo quy định của Chính phủ.

[RULES]
{"id": "LAB-10-D75-000", "type": "condition", "premises": ["illegal_emigration"], "conclusion": "suspend_pension_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 75 khoản 1 điểm a", "exception_to": "", "quote": "Tạm dừng việc hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng đối với người đang hưởng khi thuộc một trong các trường hợp sau đây: a) Xuất cảnh trái phép;"}
{"id": "LAB-10-D75-001", "type": "condition", "premises": ["declared_missing_by_court"], "conclusion": "suspend_pension_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 75 khoản 1 điểm b", "exception_to": "", "quote": "Tạm dừng việc hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng đối với người đang hưởng khi thuộc một trong các trường hợp sau đây: b) Bị Tòa án tuyên bố mất tích;"}
{"id": "LAB-10-D75-002", "type": "condition", "premises": ["cannot_verify_beneficiary_info"], "conclusion": "suspend_pension_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 75 khoản 1 điểm c", "exception_to": "", "quote": "Tạm dừng việc hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng đối với người đang hưởng khi thuộc một trong các trường hợp sau đây: c) Khi không xác minh được thông tin người thụ hưởng theo quy định tại điểm c khoản 2 Điều 11 của Luật này."}
{"id": "LAB-10-D75-003", "type": "condition", "premises": ["deceased"], "conclusion": "terminate_pension_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 75 khoản 2 điểm a", "exception_to": "", "quote": "Chấm dứt việc hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng đối với người đang hưởng khi thuộc một trong các trường hợp sau đây: a) Chết hoặc bị Tòa án tuyên bố là đã chết;"}
{"id": "LAB-10-D75-004", "type": "condition", "premises": ["refuse_benefits_in_writing"], "conclusion": "terminate_pension_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 75 khoản 2 điểm b", "exception_to": "", "quote": "Chấm dứt việc hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng đối với người đang hưởng khi thuộc một trong các trường hợp sau đây: b) Từ chối hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng bằng văn bản;"}
{"id": "LAB-10-D75-005", "type": "condition", "premises": ["incorrect_benefit_decision"], "conclusion": "terminate_pension_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 75 khoản 2 điểm c", "exception_to": "", "quote": "Chấm dứt việc hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng đối với người đang hưởng khi thuộc một trong các trường hợp sau đây: c) Kết luận của cơ quan có thẩm quyền về hưởng bảo hiểm xã hội không đúng quy định của pháp luật."}
{"id": "LAB-10-D75-006", "type": "condition", "premises": ["returned_after_illegal_emigration"], "conclusion": "resume_pension_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 75 khoản 3 điểm a", "exception_to": "", "quote": "Lương hưu, trợ cấp bảo hiểm xã hội hằng tháng của đối tượng quy định tại khoản 1 và điểm a khoản 2 Điều này được tiếp tục chi trả bao gồm cả tiền lương hưu, trợ cấp bảo hiểm xã hội hằng tháng của thời gian chưa nhận khi thuộc một trong các trường hợp sau đây: a) Người xuất cảnh trái phép trở về;"}
{"id": "LAB-10-D75-007", "type": "condition", "premises": ["court_decision_cancel_missing_declaration"], "conclusion": "resume_pension_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 75 khoản 3 điểm b", "exception_to": "", "quote": "Lương hưu, trợ cấp bảo hiểm xã hội hằng tháng của đối tượng quy định tại khoản 1 và điểm a khoản 2 Điều này được tiếp tục chi trả bao gồm cả tiền lương hưu, trợ cấp bảo hiểm xã hội hằng tháng của thời gian chưa nhận khi thuộc một trong các trường hợp sau đây: b) Có quyết định của Tòa án hủy bỏ quyết định tuyên bố mất tích hoặc quyết định tuyên bố là đã chết;"}
{"id": "LAB-10-D75-008", "type": "condition", "premises": ["verified_beneficiary_info"], "conclusion": "resume_pension_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 75 khoản 3 điểm c", "exception_to": "", "quote": "Lương hưu, trợ cấp bảo hiểm xã hội hằng tháng của đối tượng quy định tại khoản 1 và điểm a khoản 2 Điều này được tiếp tục chi trả bao gồm cả tiền lương hưu, trợ cấp bảo hiểm xã hội hằng tháng của thời gian chưa nhận khi thuộc một trong các trường hợp sau đây: c) Đối tượng quy định tại điểm c khoản 1 Điều này đã xác minh được thông tin theo quy định tại điểm c khoản 2 Điều 11 của Luật này."}
{"id": "LAB-10-D75-009", "type": "condition", "premises": ["refused_benefits_in_writing"], "conclusion": "resume_pension_benefits_from_request_date", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 75 khoản 4", "exception_to": "", "quote": "Lương hưu, trợ cấp bảo hiểm xã hội hằng tháng của đối tượng quy định tại điểm b khoản 2 Điều này được tiếp tục chi trả kể từ thời điểm cơ quan bảo hiểm xã hội nhận văn bản đề nghị được hưởng lại lương hưu, trợ cấp bảo hiểm xã hội hằng tháng và không bao gồm tiền lương hưu, trợ cấp bảo hiểm xã hội hằng tháng của thời gian chưa nhận do từ chối nhận."}
{"id": "LAB-10-D75-010", "type": "condition", "premises": ["deceased_beneficiary"], "conclusion": "survivors_receive_unpaid_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 75 khoản 5", "exception_to": "", "quote": "Người hưởng lương hưu hoặc trợ cấp bảo hiểm xã hội hằng tháng có thời gian chưa nhận lương hưu, trợ cấp trước khi chết thì thân nhân của người đó được nhận lương hưu, trợ cấp của những tháng chưa nhận."}
{"id": "LAB-10-D75-011", "type": "condition", "premises": ["court_declared_missing_then_dead"], "conclusion": "survivors_cannot_receive_suspended_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 75 khoản 6", "exception_to": "", "quote": "Người bị tạm dừng hưởng lương hưu hoặc trợ cấp bảo hiểm xã hội hằng tháng khi có quyết định của Tòa án tuyên bố mất tích, sau đó có quyết định của Tòa án tuyên bố là đã chết thì thân nhân của người đó không được nhận lương hưu, trợ cấp trong thời gian tạm dừng hưởng."}
{"id": "LAB-10-D75-012", "type": "lookup", "premises": [], "conclusion": "other_cases_of_suspend_terminate_benefits", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 75 khoản 7", "exception_to": "", "quote": "Các trường hợp tạm dừng, chấm dứt, hưởng tiếp lương hưu, trợ cấp bảo hiểm xã hội hằng tháng khác theo quy định của Chính phủ."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 76. Trợ cấp một lần đối với người đang hưởng lương hưu, trợ cấp bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 76. Trợ cấp một lần đối với người đang hưởng lương hưu, trợ cấp bảo hiểm xã hội 
hằng tháng ra nước ngoài để định cư 
1. Người đang hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng ra nước ngoài để định cư 
nếu có nguyện vọng thì được giải quyết hưởng trợ cấp một lần. 
2. Mức trợ cấp một lần đối với người đang hưởng lương hưu được tính theo thời gian đã đóng 
bảo hiểm xã hội trong đó mỗi năm đóng bảo hiểm xã hội trước năm 2014 được tính bằng 1,5 
tháng lương hưu đang hưởng, mỗi năm đóng bảo hiểm xã hội từ năm 2014 trở đi được tính bằng 
02 tháng lương hưu đang hưởng; sau đó mỗi tháng đã hưởng lương hưu thì mức trợ cấp một lần 
trừ 0,5 tháng lương hưu. Mức thấp nhất bằng 03 tháng lương hưu đang hưởng. 
3. Mức trợ cấp một lần đối với người đang hưởng trợ cấp bảo hiểm xã hội hằng tháng bằng 03 
tháng trợ cấp đang hưởng. 
4. Hồ sơ đề nghị hưởng trợ cấp một lần bao gồm văn bản đề nghị hưởng trợ cấp một lần kèm 
theo bản sao giấy xác nhận của cơ quan có thẩm quyền về việc thôi quốc tịch Việt Nam hoặc bản 
dịch tiếng Việt được chứng thực hoặc công chứng một trong các giấy tờ quy định tại các điểm a, 
b, c và d khoản 2 Điều 78 của Luật này. 
5. Trong thời hạn 07 ngày làm việc kể từ ngày nhận đủ hồ sơ theo quy định, cơ quan bảo hiểm xã 
hội có trách nhiệm giải quyết; trường hợp không giải quyết thì phải trả lời bằng văn bản và nêu 
rõ lý do.

[RULES]
{"id": "LAB-10-D76-000", "type": "condition", "premises": ["receiving_pension", "emigrating"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 76 khoản 1", "exception_to": "", "quote": "Người đang hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng ra nước ngoài để định cư nếu có nguyện vọng thì được giải quyết hưởng trợ cấp một lần."}
{"id": "LAB-10-D76-001", "type": "condition", "premises": ["receiving_pension", "time_of_contribution"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 76 khoản 2", "exception_to": "", "quote": "Mức trợ cấp một lần đối với người đang hưởng lương hưu được tính theo thời gian đã đóng bảo hiểm xã hội."}
{"id": "LAB-10-D76-002", "type": "condition", "premises": ["time_of_contribution", "received_adjustment_documents"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 76 khoản 2", "exception_to": "", "quote": "Mỗi năm đóng bảo hiểm xã hội trước năm 2014 được tính bằng 1,5 tháng lương hưu đang hưởng, mỗi năm đóng bảo hiểm xã hội từ năm 2014 trở đi được tính bằng 02 tháng lương hưu đang hưởng."}
{"id": "LAB-10-D76-003", "type": "condition", "premises": ["receiving_pension"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 76 khoản 2", "exception_to": "", "quote": "Sau đó mỗi tháng đã hưởng lương hưu thì mức trợ cấp một lần trừ 0,5 tháng lương hưu."}
{"id": "LAB-10-D76-004", "type": "condition", "premises": ["receiving_pension"], "conclusion": "wage_at_least_min_base", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 76 khoản 2", "exception_to": "", "quote": "Mức thấp nhất bằng 03 tháng lương hưu đang hưởng."}
{"id": "LAB-10-D76-005", "type": "condition", "premises": ["submitted_request_for_monthly_allowance"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 76 khoản 3", "exception_to": "", "quote": "Mức trợ cấp một lần đối với người đang hưởng trợ cấp bảo hiểm xã hội hằng tháng bằng 03 tháng trợ cấp đang hưởng."}
{"id": "LAB-10-D76-006", "type": "lookup", "premises": [], "conclusion": "document_copy", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 76 khoản 4", "exception_to": "", "quote": "Hồ sơ đề nghị hưởng trợ cấp một lần bao gồm văn bản đề nghị hưởng trợ cấp một lần kèm theo bản sao giấy xác nhận của cơ quan có thẩm quyền về việc thôi quốc tịch Việt Nam."}
{"id": "LAB-10-D76-007", "type": "condition", "premises": ["submitted_application"], "conclusion": "must_respond_in_writing_if_not_approved", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 76 khoản 5", "exception_to": "", "quote": "Trong thời hạn 07 ngày làm việc kể từ ngày nhận đủ hồ sơ theo quy định, cơ quan bảo hiểm xã hội có trách nhiệm giải quyết."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 77. Hồ sơ đề nghị hưởng lương hưu đối với người tham gia bảo hiểm xã hội bắt buộc
[NGUYÊN VĂN]
Điều 77. Hồ sơ đề nghị hưởng lương hưu đối với người tham gia bảo hiểm xã hội bắt buộc 
1. Hồ sơ đề nghị hưởng lương hưu đối với người đang tham gia bảo hiểm xã hội bắt buộc bao 
gồm: 
a) Sổ bảo hiểm xã hội; 
b) Bản chính hoặc bản sao văn bản xác định việc chấm dứt hợp đồng lao động hoặc văn bản 
chấm dứt làm việc hoặc văn bản đề nghị của đối tượng quy định tại các điểm g, h, m và n khoản 
1 Điều 2 của Luật này. 
2. Hồ sơ đề nghị hưởng lương hưu đối với người đang bảo lưu thời gian đóng bảo hiểm xã hội 
bắt buộc bao gồm: 
a) Sổ bảo hiểm xã hội; 
b) Văn bản đề nghị của người đang bảo lưu thời gian đóng bảo hiểm xã hội bắt buộc. 
3. Trường hợp quy định tại Điều 65 của Luật này, ngoài hồ sơ quy định tại khoản 1 Điều này thì 
có thêm biên bản giám định mức suy giảm khả năng lao động của Hội đồng giám định y khoa 
hoặc bản sao giấy xác nhận mức độ khuyết tật nặng, đặc biệt nặng có thể hiện kết luận của Hội 
đồng giám định y khoa ghi rõ tỷ lệ phần trăm suy giảm khả năng lao động. 
4. Trường hợp quy định tại điểm d khoản 1 và điểm c khoản 2 Điều 64 của Luật này, ngoài hồ sơ 
quy định tại khoản 1 Điều này thì có thêm bản sao giấy chứng nhận bị nhiễm HIV do tai nạn rủi 
ro nghề nghiệp.

[RULES]
{"id": "LAB-10-D77-000", "type": "condition", "premises": ["has_social_insurance_book", "document_copy"], "conclusion": "entitled_pension", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 77 khoản 1", "exception_to": "", "quote": "Hồ sơ đề nghị hưởng lương hưu đối với người đang tham gia bảo hiểm xã hội bắt buộc bao gồm: a) Sổ bảo hiểm xã hội; b) Bản chính hoặc bản sao văn bản xác định việc chấm dứt hợp đồng lao động..."}
{"id": "LAB-10-D77-001", "type": "condition", "premises": ["has_social_insurance_book", "document_copy"], "conclusion": "can_preserve_contribution_time", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 77 khoản 2", "exception_to": "", "quote": "Hồ sơ đề nghị hưởng lương hưu đối với người đang bảo lưu thời gian đóng bảo hiểm xã hội bắt buộc bao gồm: a) Sổ bảo hiểm xã hội; b) Văn bản đề nghị của người đang bảo lưu thời gian đóng bảo hiểm xã hội bắt buộc."}
{"id": "LAB-10-D77-002", "type": "condition", "premises": ["has_social_insurance_book", "document_copy"], "conclusion": "entitled_pension", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 77 khoản 3", "exception_to": "Điều 65 của Luật này", "quote": "Trường hợp quy định tại Điều 65 của Luật này, ngoài hồ sơ quy định tại khoản 1 Điều này thì có thêm biên bản giám định mức suy giảm khả năng lao động..."}
{"id": "LAB-10-D77-003", "type": "condition", "premises": ["has_social_insurance_book", "document_copy"], "conclusion": "entitled_pension", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 77 khoản 4", "exception_to": "Điều 64 của Luật này", "quote": "Trường hợp quy định tại điểm d khoản 1 và điểm c khoản 2 Điều 64 của Luật này, ngoài hồ sơ quy định tại khoản 1 Điều này thì có thêm bản sao giấy chứng nhận bị nhiễm HIV..."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 78. Hồ sơ đề nghị hưởng bảo hiểm xã hội một lần
[NGUYÊN VĂN]
Điều 78. Hồ sơ đề nghị hưởng bảo hiểm xã hội một lần 
1. Hồ sơ đề nghị hưởng bảo hiểm xã hội một lần bao gồm: 
a) Sổ bảo hiểm xã hội; 
b) Văn bản đề nghị hưởng bảo hiểm xã hội một lần của người lao động. 
2. Trường hợp quy định tại điểm b khoản 1 Điều 70 của Luật này, ngoài hồ sơ quy định tại khoản 
1 Điều này thì có thêm bản sao giấy xác nhận của cơ quan có thẩm quyền về việc thôi quốc tịch 
Việt Nam hoặc bản dịch tiếng Việt được chứng thực hoặc công chứng một trong các giấy tờ sau 
đây: 
a) Hộ chiếu do nước ngoài cấp; 
b) Thị thực của cơ quan nước ngoài có thẩm quyền cấp có xác nhận việc cho phép nhập cảnh để 
định cư ở nước ngoài; 
c) Thẻ thường trú dài hạn ở nước ngoài của cơ quan nước ngoài có thẩm quyền cấp; 
d) Giấy tờ hợp pháp khác thể hiện việc định cư ở nước ngoài theo quy định của Chính phủ. 
3. Trường hợp quy định tại điểm c khoản 1 và điểm b khoản 2 Điều 70 của Luật này, ngoài hồ sơ 
quy định tại khoản 1 Điều này thì có thêm bản tóm tắt hồ sơ bệnh án hoặc bản chính hoặc bản 
sao giấy ra viện. 
4. Trường hợp quy định tại điểm d khoản 1 và điểm c khoản 2 Điều 70 của Luật này, ngoài hồ sơ 
quy định tại khoản 1 Điều này thì có thêm biên bản giám định mức suy giảm khả năng lao động 
của Hội đồng giám định y khoa hoặc bản sao giấy xác nhận mức độ khuyết tật đặc biệt nặng.

[RULES]
{"id": "LAB-10-D78-000", "type": "condition", "premises": ["has_social_insurance_book", "has_request_document"], "conclusion": "entitled_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 78 khoản 1", "exception_to": "", "quote": "Hồ sơ đề nghị hưởng bảo hiểm xã hội một lần bao gồm: Sổ bảo hiểm xã hội; Văn bản đề nghị hưởng bảo hiểm xã hội một lần của người lao động."}
{"id": "LAB-10-D78-001", "type": "condition", "premises": ["has_request_document", "emigrating"], "conclusion": "document_copy", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 78 khoản 2", "exception_to": "Điểm b khoản 1 Điều 70", "quote": "Ngoài hồ sơ quy định tại khoản 1 Điều này thì có thêm bản sao giấy xác nhận của cơ quan có thẩm quyền về việc thôi quốc tịch Việt Nam hoặc bản dịch tiếng Việt được chứng thực hoặc công chứng một trong các giấy tờ sau đây."}
{"id": "LAB-10-D78-002", "type": "condition", "premises": ["has_request_document", "special_job_15_years"], "conclusion": "document_copy", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 78 khoản 3", "exception_to": "Điểm c khoản 1 và điểm b khoản 2 Điều 70", "quote": "Ngoài hồ sơ quy định tại khoản 1 Điều này thì có thêm bản tóm tắt hồ sơ bệnh án hoặc bản chính hoặc bản sao giấy ra viện."}
{"id": "LAB-10-D78-003", "type": "condition", "premises": ["has_request_document", "special_job_15_years"], "conclusion": "document_copy", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 78 khoản 4", "exception_to": "Điểm d khoản 1 và điểm c khoản 2 Điều 70", "quote": "Ngoài hồ sơ quy định tại khoản 1 Điều này thì có thêm biên bản giám định mức suy giảm khả năng lao động của Hội đồng giám định y khoa hoặc bản sao giấy xác nhận mức độ khuyết tật đặc biệt nặng."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 79. Giải quyết hưởng lương hưu, hưởng bảo hiểm xã hội một lần
[NGUYÊN VĂN]
Điều 79. Giải quyết hưởng lương hưu, hưởng bảo hiểm xã hội một lần 
1. Trong thời hạn 20 ngày trước thời điểm người lao động đủ điều kiện hưởng lương hưu, người 
sử dụng lao động nộp hồ sơ quy định tại Điều 77 của Luật này cho cơ quan bảo hiểm xã hội. 
Trong thời hạn 20 ngày trước thời điểm đủ điều kiện hưởng lương hưu, người đang bảo lưu thời 
gian đóng bảo hiểm xã hội bắt buộc nộp hồ sơ quy định tại Điều 77 của Luật này cho cơ quan 
bảo hiểm xã hội. 
2. Người lao động khi đủ điều kiện hưởng bảo hiểm xã hội một lần nộp hồ sơ quy định tại Điều 
78 của Luật này cho cơ quan bảo hiểm xã hội. 
3. Trong thời hạn 20 ngày, không bao gồm ngày nghỉ lễ, tết, kể từ ngày nhận đủ hồ sơ theo quy 
định đối với người đề nghị hưởng lương hưu hoặc trong thời hạn 07 ngày làm việc kể từ ngày 
nhận đủ hồ sơ theo quy định đối với người đề nghị hưởng bảo hiểm xã hội một lần, cơ quan bảo 
hiểm xã hội có trách nhiệm giải quyết; trường hợp không giải quyết thì phải trả lời bằng văn bản 
và nêu rõ lý do.

[RULES]
{"id": "LAB-10-D79-000", "type": "condition", "premises": ["must_submit_application_within_20_days", "is_employed"], "conclusion": "must_submit_application_for_pension", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 79 khoản 1", "exception_to": "", "quote": "Trong thời hạn 20 ngày trước thời điểm người lao động đủ điều kiện hưởng lương hưu, người sử dụng lao động nộp hồ sơ quy định tại Điều 77 của Luật này cho cơ quan bảo hiểm xã hội."}
{"id": "LAB-10-D79-001", "type": "condition", "premises": ["must_submit_application_within_20_days", "can_preserve_contribution_time"], "conclusion": "must_submit_application_for_pension", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 79 khoản 1", "exception_to": "", "quote": "Trong thời hạn 20 ngày trước thời điểm đủ điều kiện hưởng lương hưu, người đang bảo lưu thời gian đóng bảo hiểm xã hội bắt buộc nộp hồ sơ quy định tại Điều 77 của Luật này cho cơ quan bảo hiểm xã hội."}
{"id": "LAB-10-D79-002", "type": "condition", "premises": ["requested_lump_sum"], "conclusion": "must_submit_application_for_lump_sum", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 79 khoản 2", "exception_to": "", "quote": "Người lao động khi đủ điều kiện hưởng bảo hiểm xã hội một lần nộp hồ sơ quy định tại Điều 78 của Luật này cho cơ quan bảo hiểm xã hội."}
{"id": "LAB-10-D79-003", "type": "condition", "premises": ["submitted_application", "is_employed"], "conclusion": "must_resolve_pension_application", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 79 khoản 3", "exception_to": "", "quote": "Trong thời hạn 20 ngày, không bao gồm ngày nghỉ lễ, tết, kể từ ngày nhận đủ hồ sơ theo quy định đối với người đề nghị hưởng lương hưu hoặc trong thời hạn 07 ngày làm việc kể từ ngày nhận đủ hồ sơ theo quy định đối với người đề nghị hưởng bảo hiểm xã hội một lần, cơ quan bảo hiểm xã hội có trách nhiệm giải quyết."}
{"id": "LAB-10-D79-004", "type": "condition", "premises": ["submitted_application"], "conclusion": "must_respond_in_writing_if_not_approved", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 79 khoản 3", "exception_to": "", "quote": "trường hợp không giải quyết thì phải trả lời bằng văn bản và nêu rõ lý do."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 80. Hồ sơ đề nghị tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng trong
[NGUYÊN VĂN]
Điều 80. Hồ sơ đề nghị tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng trong 
trường hợp đã bị tạm dừng hoặc chấm dứt hưởng 
Hồ sơ đề nghị tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng đối với các trường 
hợp quy định tại điểm a và điểm b khoản 3 và khoản 4 Điều 75 của Luật này bao gồm văn bản đề 
nghị tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng và giấy tờ khác tùy theo từng 
trường hợp sau đây: 
1. Văn bản của cơ quan nhà nước có thẩm quyền về việc trở về nước đối với trường hợp quy 
định điểm a khoản 3 Điều 75 của Luật này; 
2. Quyết định của Tòa án hủy bỏ quyết định tuyên bố mất tích hoặc hủy bỏ quyết định tuyên bố 
là đã chết đối với trường hợp quy định điểm b khoản 3 Điều 75 của Luật này.

[RULES]
{"id": "LAB-10-D80-000", "type": "condition", "premises": ["submitted_request_for_monthly_allowance", "has_request_document", "government_regulates_agency_structure"], "conclusion": "must_resolve_sick_leave_application", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 80 khoản 1", "exception_to": "", "quote": "Hồ sơ đề nghị tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng đối với các trường hợp quy định tại điểm a và điểm b khoản 3 và khoản 4 Điều 75 của Luật này bao gồm văn bản đề nghị tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng và giấy tờ khác tùy theo từng trường hợp sau đây"}
{"id": "LAB-10-D80-001", "type": "condition", "premises": ["submitted_request_for_monthly_allowance", "has_request_document", "government_regulates_agency_structure", "document_copy"], "conclusion": "must_resolve_sick_leave_application", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 80 khoản 1", "exception_to": "", "quote": "Hồ sơ đề nghị tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng đối với các trường hợp quy định tại điểm a và điểm b khoản 3 và khoản 4 Điều 75 của Luật này bao gồm văn bản đề nghị tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng và giấy tờ khác tùy theo từng trường hợp sau đây"}
{"id": "LAB-10-D80-002", "type": "condition", "premises": ["submitted_request_for_monthly_allowance", "has_request_document", "government_regulates_agency_structure"], "conclusion": "must_resolve_sick_leave_application", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 80 khoản 2", "exception_to": "", "quote": "Hồ sơ đề nghị tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng đối với các trường hợp quy định tại điểm a và điểm b khoản 3 và khoản 4 Điều 75 của Luật này bao gồm văn bản đề nghị tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng và giấy tờ khác tùy theo từng trường hợp sau đây"}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 81. Giải quyết tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng trong
[NGUYÊN VĂN]
Điều 81. Giải quyết tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng trong 
trường hợp đã bị tạm dừng hoặc chấm dứt hưởng 
1. Người đề nghị tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng nộp hồ sơ quy 
định tại Điều 80 của Luật này cho cơ quan bảo hiểm xã hội. 
2. Trong thời hạn 10 ngày làm việc kể từ ngày nhận đủ hồ sơ theo quy định, cơ quan bảo hiểm xã 
hội có trách nhiệm giải quyết; trường hợp không giải quyết thì phải trả lời bằng văn bản và nêu 
rõ lý do.

[RULES]
{"id": "LAB-10-D81-000", "type": "condition", "premises": ["submitted_request_for_monthly_allowance", "received_adjustment_documents"], "conclusion": "must_resolve_sick_leave_application", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 81 khoản 1", "exception_to": "", "quote": "Người đề nghị tiếp tục hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng nộp hồ sơ quy định tại Điều 80 của Luật này cho cơ quan bảo hiểm xã hội."}
{"id": "LAB-10-D81-001", "type": "condition", "premises": ["received_adjustment_documents"], "conclusion": "must_respond_in_writing_if_not_approved", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 81 khoản 2", "exception_to": "", "quote": "Trong thời hạn 10 ngày làm việc kể từ ngày nhận đủ hồ sơ theo quy định, cơ quan bảo hiểm xã hội có trách nhiệm giải quyết; trường hợp không giải quyết thì phải trả lời bằng văn bản và nêu rõ lý do."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 82. Thay đổi hình thức nhận, nơi nhận lương hưu, trợ cấp bảo hiểm xã hội hằng
[NGUYÊN VĂN]
Điều 82. Thay đổi hình thức nhận, nơi nhận lương hưu, trợ cấp bảo hiểm xã hội hằng 
tháng 
1. Người đang hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng có nguyện vọng thay đổi 
hình thức nhận hoặc thay đổi nơi nhận do chuyển nơi cư trú trong nước thì có văn bản gửi cơ 
quan bảo hiểm xã hội nơi đang chi trả. 
2. Trong thời hạn 05 ngày làm việc kể từ ngày nhận được văn bản quy định tại khoản 1 Điều này, 
cơ quan bảo hiểm xã hội có trách nhiệm giải quyết; trường hợp không giải quyết thì phải trả lời 
bằng văn bản và nêu rõ lý do.

[RULES]
{"id": "LAB-10-D82-000", "type": "condition", "premises": ["receiving_pension", "has_request_document"], "conclusion": "must_submit_application_for_change", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 82 khoản 1", "exception_to": "", "quote": "Người đang hưởng lương hưu, trợ cấp bảo hiểm xã hội hằng tháng có nguyện vọng thay đổi hình thức nhận hoặc thay đổi nơi nhận do chuyển nơi cư trú trong nước thì có văn bản gửi cơ quan bảo hiểm xã hội nơi đang chi trả."}
{"id": "LAB-10-D82-001", "type": "condition", "premises": ["received_request_document"], "conclusion": "must_resolve_change_request", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 82 khoản 2", "exception_to": "", "quote": "Trong thời hạn 05 ngày làm việc kể từ ngày nhận được văn bản quy định tại khoản 1 Điều này, cơ quan bảo hiểm xã hội có trách nhiệm giải quyết."}
{"id": "LAB-10-D82-002", "type": "condition", "premises": ["received_request_document", "~must_resolve_change_request"], "conclusion": "must_respond_in_writing_if_not_approved", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 82 khoản 2", "exception_to": "", "quote": "trường hợp không giải quyết thì phải trả lời bằng văn bản và nêu rõ lý do."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 83. Hồ sơ, trình tự khám giám định mức suy giảm khả năng lao động để giải quyết
[NGUYÊN VĂN]
Điều 83. Hồ sơ, trình tự khám giám định mức suy giảm khả năng lao động để giải quyết 
chế độ bảo hiểm xã hội 
1. Hồ sơ, trình tự khám giám định mức suy giảm khả năng lao động để giải quyết chế độ bảo 
hiểm xã hội do Bộ trưởng Bộ Y tế quy định. 
2. Việc khám giám định mức suy giảm khả năng lao động phải bảo đảm chính xác, công khai, 
minh bạch. Hội đồng giám định y khoa chịu trách nhiệm về tính chính xác của kết quả giám 
định. 
Mục 4. CHẾ ĐỘ TỬ TUẤT

[RULES]
{"id": "LAB-10-D83-000", "type": "lookup", "premises": [], "conclusion": "medical_exam_procedure", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 83 khoản 1", "exception_to": "", "quote": "Hồ sơ, trình tự khám giám định mức suy giảm khả năng lao động để giải quyết chế độ bảo hiểm xã hội do Bộ trưởng Bộ Y tế quy định."}
{"id": "LAB-10-D83-001", "type": "condition", "premises": ["must_ensure_conditions_for_medical_exam"], "conclusion": "responsible_for_exam_accuracy", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 83 khoản 2", "exception_to": "", "quote": "Việc khám giám định mức suy giảm khả năng lao động phải bảo đảm chính xác, công khai, minh bạch. Hội đồng giám định y khoa chịu trách nhiệm về tính chính xác của kết quả giám định."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 84. Đối tượng hưởng chế độ tử tuất
[NGUYÊN VĂN]
Điều 84. Đối tượng hưởng chế độ tử tuất 
Đối tượng hưởng chế độ tử tuất của người tham gia bảo hiểm xã hội bị chết là thân nhân quy 
định khoản 2 Điều 86, các điểm a, b và c khoản 2 Điều 88 của Luật này; người thừa kế quy định 
tại điểm d khoản 2 Điều 88 của Luật này; tổ chức, cá nhân lo mai táng quy định khoản 1 Điều 85 
của Luật này và thân nhân quy định tại khoản 3 Điều 85 của Luật này.

[RULES]
{"id": "LAB-10-D84-000", "type": "condition", "premises": ["covered_point_a", "covered_point_b", "covered_point_d"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 84 khoản 1", "exception_to": "", "quote": "Đối tượng hưởng chế độ tử tuất của người tham gia bảo hiểm xã hội bị chết là thân nhân quy định khoản 2 Điều 86, các điểm a, b và c khoản 2 Điều 88 của Luật này."}
{"id": "LAB-10-D84-001", "type": "condition", "premises": ["covered_point_d"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 84 khoản 1", "exception_to": "", "quote": "Đối tượng hưởng chế độ tử tuất của người tham gia bảo hiểm xã hội bị chết là thân nhân quy định khoản 2 Điều 86, các điểm a, b và c khoản 2 Điều 88 của Luật này."}
{"id": "LAB-10-D84-002", "type": "condition", "premises": ["covered_point_d"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 84 khoản 1", "exception_to": "", "quote": "Đối tượng hưởng chế độ tử tuất của người tham gia bảo hiểm xã hội bị chết là thân nhân quy định khoản 2 Điều 86, các điểm a, b và c khoản 2 Điều 88 của Luật này."}
{"id": "LAB-10-D84-003", "type": "condition", "premises": ["covered_point_d"], "conclusion": "funeral_support", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 84 khoản 1", "exception_to": "", "quote": "Đối tượng hưởng chế độ tử tuất của người tham gia bảo hiểm xã hội bị chết là tổ chức, cá nhân lo mai táng quy định khoản 1 Điều 85 của Luật này."}
{"id": "LAB-10-D84-004", "type": "condition", "premises": ["covered_point_d"], "conclusion": "funeral_support", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 84 khoản 1", "exception_to": "", "quote": "Đối tượng hưởng chế độ tử tuất của người tham gia bảo hiểm xã hội bị chết là thân nhân quy định tại khoản 3 Điều 85 của Luật này."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 85. Trợ cấp mai táng
[NGUYÊN VĂN]
Điều 85. Trợ cấp mai táng 
1. Người sau đây khi chết thì tổ chức, cá nhân lo mai táng được nhận một lần trợ cấp mai táng: 
a) Đối tượng quy định tại khoản 1 và khoản 2 Điều 2 của Luật này có thời gian đóng bảo hiểm xã 
hội bắt buộc từ đủ 12 tháng trở lên; 
b) Chết do tai nạn lao động, bệnh nghề nghiệp theo quy định của pháp luật về an toàn, vệ sinh 
lao động; 
c) Người đang hưởng hoặc đang tạm dừng hưởng lương hưu; người đang hưởng hoặc đang tạm 
dừng hưởng trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng tháng đã nghỉ việc. 
2. Mức trợ cấp mai táng bằng 10 lần mức tham chiếu tại tháng mà người quy định tại khoản 1 
Điều này chết. 
3. Trường hợp đối tượng quy định tại các điểm a, b và c khoản 1 Điều này bị Tòa án tuyên bố là 
đã chết thì thân nhân được hưởng trợ cấp mai táng quy định tại khoản 2 Điều này.

[RULES]
{"id": "LAB-10-D85-000", "type": "condition", "premises": ["covered_point_a", "has_full_contribution_time"], "conclusion": "funeral_support", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 85 khoản 1", "exception_to": "", "quote": "Người sau đây khi chết thì tổ chức, cá nhân lo mai táng được nhận một lần trợ cấp mai táng: a) Đối tượng quy định tại khoản 1 và khoản 2 Điều 2 của Luật này có thời gian đóng bảo hiểm xã hội bắt buộc từ đủ 12 tháng trở lên;"}
{"id": "LAB-10-D85-001", "type": "condition", "premises": ["covered_point_b"], "conclusion": "funeral_support", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 85 khoản 1", "exception_to": "", "quote": "Người sau đây khi chết thì tổ chức, cá nhân lo mai táng được nhận một lần trợ cấp mai táng: b) Chết do tai nạn lao động, bệnh nghề nghiệp theo quy định của pháp luật về an toàn, vệ sinh lao động;"}
{"id": "LAB-10-D85-002", "type": "condition", "premises": ["covered_point_c"], "conclusion": "funeral_support", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 85 khoản 1", "exception_to": "", "quote": "Người sau đây khi chết thì tổ chức, cá nhân lo mai táng được nhận một lần trợ cấp mai táng: c) Người đang hưởng hoặc đang tạm dừng hưởng lương hưu; người đang hưởng hoặc đang tạm dừng hưởng trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng tháng đã nghỉ việc."}
{"id": "LAB-10-D85-003", "type": "condition", "premises": [], "conclusion": "reference_amount", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 85 khoản 2", "exception_to": "", "quote": "Mức trợ cấp mai táng bằng 10 lần mức tham chiếu tại tháng mà người quy định tại khoản 1 Điều này chết."}
{"id": "LAB-10-D85-004", "type": "condition", "premises": ["covered_point_a", "covered_point_b", "covered_point_c"], "conclusion": "funeral_support", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 85 khoản 3", "exception_to": "", "quote": "Trường hợp đối tượng quy định tại các điểm a, b và c khoản 1 Điều này bị Tòa án tuyên bố là đã chết thì thân nhân được hưởng trợ cấp mai táng quy định tại khoản 2 Điều này."}


######## 10_bao_hiem_xa_hoi_41_2024_QH15 — Điều 86. Các trường hợp hưởng trợ cấp tuất hằng tháng
[NGUYÊN VĂN]
Điều 86. Các trường hợp hưởng trợ cấp tuất hằng tháng 
1. Đối tượng quy định tại khoản 1 Điều 2 của Luật này khi chết hoặc bị Tòa án tuyên bố là đã 
chết thuộc một trong các trường hợp sau đây thì thân nhân quy định tại khoản 2 Điều này được 
hưởng tiền tuất hằng tháng: 
a) Có thời gian đóng bảo hiểm xã hội bắt buộc từ đủ 15 năm trở lên; 
b) Đang hưởng lương hưu hoặc đang tạm dừng hưởng lương hưu; 
c) Chết do tai nạn lao động, bệnh nghề nghiệp theo quy định của pháp luật về an toàn, vệ sinh lao 
động; 
d) Đang hưởng hoặc đang tạm dừng hưởng trợ cấp tai nạn lao động, bệnh nghề nghiệp hằng 
tháng với mức suy giảm khả năng lao động từ 61% trở lên. 
2. Thân nhân của đối tượng quy định tại khoản 1 Điều này được hưởng trợ cấp tuất hằng tháng, 
bao gồm: 
a) Các con bao gồm cả con khi người mẹ đang mang thai mà người cha chết, con khi lao động nữ 
mang thai hộ đang mang thai mà người cha hoặc người mẹ nhờ mang thai hộ chết thì được 
hưởng đến khi đủ 18 tuổi; 
b) Con bị suy giảm khả năng lao động từ 81% trở lên; 
c) Vợ, chồng đủ tuổi theo quy định tại khoản 2 Điều 169 của Bộ luật Lao động. Vợ, chồng chưa 
đủ tuổi theo quy định tại khoản 2 Điều 169 của Bộ luật Lao động mà bị suy giảm khả năng lao 
động từ 81% trở lên; 
d) Cha đẻ, mẹ đẻ; cha đẻ, mẹ đẻ của vợ hoặc của chồng; thành viên khác của gia đình đủ tuổi 
theo quy định tại khoản 2 Điều 169 của Bộ luật Lao động mà người quy định tại khoản 1 Điều 
này đang có nghĩa vụ nuôi dưỡng theo quy định của pháp luật về hôn nhân và gia đình; 
đ) Cha đẻ, mẹ đẻ; cha đẻ, mẹ đẻ của vợ hoặc của chồng; thành viên khác của gia đình chưa đủ 
tuổi theo quy định tại khoản 2 Điều 169 của Bộ luật Lao động bị suy giảm khả năng lao động từ 
81% trở lên mà người tham gia bảo hiểm xã hội đang có nghĩa vụ nuôi dưỡng theo quy định của 
pháp luật về hôn nhân và gia đình. 
3. Không áp dụng trợ cấp tuất hằng tháng đối với thân nhân quy định tại các điểm b, c, d và đ 
khoản 2 Điều này là người đang hưởng tiền lương và tham gia bảo hiểm xã hội bắt buộc hoặc 
đang hưởng lương hưu, trợ cấp mất sức lao động hằng tháng, trợ cấp hằng tháng mà mức hưởng 
bằng hoặc cao hơn mức tham chiếu, không bao gồm khoản trợ cấp theo quy định của pháp luật 
về ưu đãi người có công với cách mạng. 
4. Kết quả khám giám định mức suy giảm khả năng lao động để hưởng trợ cấp tuất hằng tháng 
phải được xác định chậm nhất 06 tháng kể từ ngày người tham gia bảo hiểm xã hội chết hoặc kể 
từ ngày thân nhân quy định tại điểm a khoản 2 Điều này hết thời hạn hưởng trợ cấp theo quy 
định. 
5. Bộ trưởng Bộ Lao động - Thương binh và Xã hội quy định về việc tính, việc xác định điều 
kiện đối với từng trường hợp để giải quyết chế độ tử tuất.

[RULES]
{"id": "LAB-10-D86-000", "type": "condition", "premises": ["covered_point_a", "has_full_contribution_time"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 86 khoản 1", "exception_to": "", "quote": "thì thân nhân quy định tại khoản 2 Điều này được hưởng tiền tuất hằng tháng"}
{"id": "LAB-10-D86-001", "type": "condition", "premises": ["covered_point_a", "receiving_pension"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 86 khoản 1", "exception_to": "", "quote": "thì thân nhân quy định tại khoản 2 Điều này được hưởng tiền tuất hằng tháng"}
{"id": "LAB-10-D86-002", "type": "condition", "premises": ["covered_point_a", "health_not_recovered_above_81"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 86 khoản 1", "exception_to": "", "quote": "thì thân nhân quy định tại khoản 2 Điều này được hưởng tiền tuất hằng tháng"}
{"id": "LAB-10-D86-003", "type": "condition", "premises": ["covered_point_a", "health_not_recovered_between_61_and_81"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 86 khoản 1", "exception_to": "", "quote": "thì thân nhân quy định tại khoản 2 Điều này được hưởng tiền tuất hằng tháng"}
{"id": "LAB-10-D86-004", "type": "condition", "premises": ["covered_point_a"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 86 khoản 2", "exception_to": "", "quote": "Thân nhân của đối tượng quy định tại khoản 1 Điều này được hưởng trợ cấp tuất hằng tháng, bao gồm: Các con bao gồm cả con khi người mẹ đang mang thai mà người cha chết"}
{"id": "LAB-10-D86-005", "type": "condition", "premises": ["covered_point_a"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 86 khoản 2", "exception_to": "", "quote": "Thân nhân của đối tượng quy định tại khoản 1 Điều này được hưởng trợ cấp tuất hằng tháng, bao gồm: Con bị suy giảm khả năng lao động từ 81% trở lên"}
{"id": "LAB-10-D86-006", "type": "condition", "premises": ["covered_point_a"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 86 khoản 2", "exception_to": "", "quote": "Thân nhân của đối tượng quy định tại khoản 1 Điều này được hưởng trợ cấp tuất hằng tháng, bao gồm: Vợ, chồng đủ tuổi theo quy định tại khoản 2 Điều 169 của Bộ luật Lao động"}
{"id": "LAB-10-D86-007", "type": "condition", "premises": ["covered_point_a"], "conclusion": "survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 86 khoản 2", "exception_to": "", "quote": "Thân nhân của đối tượng quy định tại khoản 1 Điều này được hưởng trợ cấp tuất hằng tháng, bao gồm: Cha đẻ, mẹ đẻ; cha đẻ, mẹ đẻ của vợ hoặc của chồng"}
{"id": "LAB-10-D86-008", "type": "condition", "premises": ["covered_point_b"], "conclusion": "~survivor_benefit", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 86 khoản 3", "exception_to": "khoản 2 Điều này", "quote": "Không áp dụng trợ cấp tuất hằng tháng đối với thân nhân quy định tại các điểm b, c, d và đ khoản 2 Điều này là người đang hưởng tiền lương và tham gia bảo hiểm xã hội bắt buộc"}
{"id": "LAB-10-D86-009", "type": "lookup", "premises": [], "conclusion": "must_resolve_pension_application", "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 86 khoản 4", "exception_to": "", "quote": "Kết quả khám giám định mức suy giảm khả năng lao động để hưởng trợ cấp tuất hằng tháng phải được xác định chậm nhất 06 tháng kể từ ngày người tham gia bảo hiểm xã hội chết"}
