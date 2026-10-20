

######## 01_luat_quan_ly_thue_108_2025_QH15 — Điều 48. Trường hợp bị cưỡng chế thi hành quyết định hành chính về quản lý thuế
[NGUYÊN VĂN]
Điều 48. Trường hợp bị cưỡng chế thi hành quyết định hành chính về quản lý thuế 
1. Người nộp thuế có tiền thuế nợ quá 90 ngày kể từ ngày hết thời hạn nộp theo quy định. 
2. Người nộp thuế có tiền thuế nợ khi hết thời hạn gia hạn nộp tiền thuế. 
3. Người nộp thuế có tiền thuế nợ nhưng không hoạt động tại địa chỉ đã đăng ký hoặc có hành vi 
phát tán tài sản. 
4. Người nộp thuế không chấp hành quyết định xử phạt vi phạm hành chính về quản lý thuế theo 
thời hạn ghi trên quyết định xử phạt vi phạm hành chính về quản lý thuế, trừ trường hợp được 
hoãn hoặc tạm đình chỉ thi hành quyết định xử phạt. 
5. Người nộp thuế đã bị xử phạt hành chính về hành vi không chấp hành quyết định kiểm tra thuế 
nhưng tiếp tục không chấp hành quyết định kiểm tra thuế. 
6. Chưa thực hiện biện pháp cưỡng chế thuế đối với khoản nợ của người nộp thuế được cơ quan 
quản lý thuế không tính tiền chậm nộp theo quy định; được nộp dần tiền thuế nợ trong thời hạn 
không quá 12 tháng kể từ ngày cơ quan có thẩm quyền ban hành văn bản chấp nhận nộp dần tiền 
thuế nợ và trong thời gian thư bảo lãnh có hiệu lực. Việc nộp dần tiền thuế nợ được thủ trưởng 
cơ quan quản lý thuế xem xét trên cơ sở đề nghị của người nộp thuế và phải có bảo lãnh của tổ 
chức tín dụng. 
7. Không thực hiện biện pháp cưỡng chế đối với người nộp thuế có nợ phí hải quan và lệ phí 
hàng hóa, phương tiện vận tải quá cảnh. 
8. Cơ quan thuế không thực hiện biện pháp cưỡng chế đối với số tiền thuế nợ được bù trừ qua 
hoàn thuế mà cơ quan thuế đang làm thủ tục bù trừ cho người nộp thuế. 
9. Thủ trưởng cơ quan quản lý thuế căn cứ tình hình thực tế để quyết định trường hợp thực hiện 
cưỡng chế thi hành quyết định hành chính về quản lý thuế. 
10. Chính phủ quy định chi tiết Điều này.

[RULES]
{"id": "TAX-01-D48-000", "type": "condition", "premises": ["taxpayer_has_tax_debt", "taxpayer_cannot_meet_tax_obligation_on_time"], "conclusion": "is_enforcement_case", "source": "01_luat_quan_ly_thue_108_2025_QH15, Điều 48 khoản 1", "exception_to": "", "quote": "Người nộp thuế có tiền thuế nợ quá 90 ngày kể từ ngày hết thời hạn nộp theo quy định."}
{"id": "TAX-01-D48-001", "type": "condition", "premises": ["taxpayer_has_tax_debt", "taxpayer_cannot_meet_tax_obligation_on_time"], "conclusion": "is_enforcement_case", "source": "01_luat_quan_ly_thue_108_2025_QH15, Điều 48 khoản 2", "exception_to": "", "quote": "Người nộp thuế có tiền thuế nợ khi hết thời hạn gia hạn nộp tiền thuế."}
{"id": "TAX-01-D48-002", "type": "condition", "premises": ["taxpayer_has_tax_debt", "is_non_compliance_with_tax_authority"], "conclusion": "is_enforcement_case", "source": "01_luat_quan_ly_thue_108_2025_QH15, Điều 48 khoản 3", "exception_to": "", "quote": "Người nộp thuế có tiền thuế nợ nhưng không hoạt động tại địa chỉ đã đăng ký hoặc có hành vi phát tán tài sản."}
{"id": "TAX-01-D48-003", "type": "condition", "premises": ["is_non_compliance_with_tax_authority"], "conclusion": "is_enforcement_case", "source": "01_luat_quan_ly_thue_108_2025_QH15, Điều 48 khoản 4", "exception_to": "", "quote": "Người nộp thuế không chấp hành quyết định xử phạt vi phạm hành chính về quản lý thuế theo thời hạn ghi trên quyết định xử phạt vi phạm hành chính về quản lý thuế, trừ trường hợp được hoãn hoặc tạm đình chỉ thi hành quyết định xử phạt."}
{"id": "TAX-01-D48-004", "type": "condition", "premises": ["is_non_compliance_with_tax_authority"], "conclusion": "is_enforcement_case", "source": "01_luat_quan_ly_thue_108_2025_QH15, Điều 48 khoản 5", "exception_to": "", "quote": "Người nộp thuế đã bị xử phạt hành chính về hành vi không chấp hành quyết định kiểm tra thuế nhưng tiếp tục không chấp hành quyết định kiểm tra thuế."}
{"id": "TAX-01-D48-005", "type": "condition", "premises": ["taxpayer_has_tax_debt", "~not_exists_tax_debt"], "conclusion": "is_enforcement_case", "source": "01_luat_quan_ly_thue_108_2025_QH15, Điều 48 khoản 6", "exception_to": "", "quote": "Chưa thực hiện biện pháp cưỡng chế thuế đối với khoản nợ của người nộp thuế được cơ quan quản lý thuế không tính tiền chậm nộp theo quy định."}
{"id": "TAX-01-D48-006", "type": "condition", "premises": ["taxpayer_has_tax_debt"], "conclusion": "~is_enforcement_case", "source": "01_luat_quan_ly_thue_108_2025_QH15, Điều 48 khoản 7", "exception_to": "", "quote": "Không thực hiện biện pháp cưỡng chế đối với người nộp thuế có nợ phí hải quan và lệ phí hàng hóa, phương tiện vận tải quá cảnh."}
{"id": "TAX-01-D48-007", "type": "condition", "premises": ["taxpayer_has_tax_debt"], "conclusion": "~is_enforcement_case", "source": "01_luat_quan_ly_thue_108_2025_QH15, Điều 48 khoản 8", "exception_to": "", "quote": "Cơ quan thuế không thực hiện biện pháp cưỡng chế đối với số tiền thuế nợ được bù trừ qua hoàn thuế mà cơ quan thuế đang làm thủ tục bù trừ cho người nộp thuế."}
{"id": "TAX-01-D48-008", "type": "condition", "premises": [], "conclusion": "is_enforcement_case", "source": "01_luat_quan_ly_thue_108_2025_QH15, Điều 48 khoản 9", "exception_to": "", "quote": "Thủ trưởng cơ quan quản lý thuế căn cứ tình hình thực tế để quyết định trường hợp thực hiện cưỡng chế thi hành quyết định hành chính về quản lý thuế."}


######## 04_luat_thue_GTGT_48_2024_QH15 — Điều 14. Khấu trừ thuế giá trị gia tăng đầu vào
[NGUYÊN VĂN]
Điều 14. Khấu trừ thuế giá trị gia tăng đầu vào 
1. Cơ sở kinh doanh nộp thuế giá trị gia tăng theo phương pháp khấu trừ thuế được khấu trừ thuế 
giá trị gia tăng đầu vào như sau: 
a) Thuế giá trị gia tăng đầu vào của hàng hóa, dịch vụ sử dụng cho sản xuất, kinh doanh hàng 
hóa, dịch vụ chịu thuế giá trị gia tăng được khấu trừ toàn bộ, kể cả thuế giá trị gia tăng đầu vào 
không được bồi thường của hàng hóa, dịch vụ chịu thuế giá trị gia tăng bị tổn thất, hàng hóa bị 
hao hụt tự nhiên do tính chất lý hóa trong quá trình vận chuyển; 
b) Thuế giá trị gia tăng đầu vào của hàng hóa, dịch vụ sử dụng đồng thời cho sản xuất, kinh 
doanh hàng hóa, dịch vụ chịu thuế và không chịu thuế thì chỉ được khấu trừ số thuế giá trị gia 
tăng đầu vào của hàng hóa, dịch vụ sử dụng cho sản xuất, kinh doanh hàng hóa, dịch vụ chịu 
thuế giá trị gia tăng. Cơ sở kinh doanh phải hạch toán riêng thuế giá trị gia tăng đầu vào được 
khấu trừ và không được khấu trừ; trường hợp không hạch toán riêng được thì số thuế giá trị gia 
tăng đầu vào được khấu trừ tính theo tỷ lệ % giữa doanh thu của hàng hóa, dịch vụ chịu thuế giá 
trị gia tăng so với tổng doanh thu hàng hóa, dịch vụ bán ra; 
c) Thuế giá trị gia tăng đầu vào của hàng hóa, dịch vụ bán cho tổ chức, cá nhân sử dụng vốn viện 
trợ nhân đạo, viện trợ không hoàn lại được khấu trừ toàn bộ; 
d) Thuế giá trị gia tăng đầu vào của hàng hóa, dịch vụ sử dụng cho hoạt động tìm kiếm thăm dò, 
phát triển mỏ dầu khí được khấu trừ toàn bộ; 
đ) Thuế giá trị gia tăng đầu vào phát sinh trong tháng, quý nào được kê khai, khấu trừ khi xác 
định số thuế phải nộp của tháng, quý đó. Số thuế giá trị gia tăng đầu vào chưa được khấu trừ hết 
trong tháng, quý thì được khấu trừ vào tháng, quý tiếp theo. 
Trường hợp cơ sở kinh doanh phát hiện số thuế giá trị gia tăng đầu vào khi kê khai, 
khấu trừ bị sai, sót thì được khai thuế trước khi cơ quan thuế, cơ quan có thẩm quyền 
công bố quyết định kiểm tra thuế, thanh tra thuế như sau: 
Người nộp thuế thực hiện khai bổ sung vào tháng, quý phát sinh số thuế giá trị gia tăng 
đầu vào bị sai, sót nếu việc khai thuế vào tháng, quý phát sinh số thuế giá trị gia tăng 
đầu vào bị sai, sót làm tăng số thuế phải nộp hoặc giảm số thuế được hoàn; người nộp 
thuế phải nộp đủ số tiền thuế phải nộp tăng thêm hoặc bị thu hồi số tiền thuế đã được 
hoàn tương ứng và nộp tiền chậm nộp vào ngân sách nhà nước (nếu có). 
Người nộp thuế thực hiện khai vào tháng, quý phát hiện sai, sót nếu việc khai thuế 
vào tháng, quý phát sinh số thuế giá trị gia tăng đầu vào bị sai, sót làm giảm số tiền 
thuế phải nộp hoặc chỉ làm tăng hoặc giảm số thuế giá trị gia tăng còn được khấu trừ 
chuyển sang tháng, quý sau; 
e) Đối với số thuế giá trị gia tăng đầu vào không được khấu trừ, cơ sở kinh doanh được tính vào 
chi phí để tính thuế thu nhập doanh nghiệp hoặc tính vào nguyên giá của tài sản cố định theo quy 
định của pháp luật về thuế thu nhập doanh nghiệp, trừ số thuế giá trị gia tăng của hàng hóa, dịch 
vụ mua vào không có chứng từ thanh toán không dùng tiền mặt theo quy định của Chính phủ; 
g) Chính phủ quy định chi tiết việc khấu trừ thuế giá trị gia tăng đầu vào đối với: hàng hóa, dịch 
vụ hình thành tài sản cố định phục vụ cho người lao động; trường hợp góp vốn bằng tài sản; hàng 
hóa, dịch vụ mua vào dưới hình thức ủy quyền cho tổ chức, cá nhân khác mà hóa đơn mang tên 
tổ chức, cá nhân được ủy quyền; tài sản cố định là ô tô chở người từ 09 chỗ ngồi trở xuống; cơ sở 
sản xuất, kinh doanh tổ chức sản xuất khép kín, hạch toán tập trung. 
2. Điều kiện khấu trừ thuế giá trị gia tăng đầu vào được quy định như sau: 
a) Có hóa đơn giá trị gia tăng mua hàng hóa, dịch vụ hoặc chứng từ nộp thuế giá trị gia tăng ở 
khâu nhập khẩu hoặc chứng từ nộp thuế giá trị gia tăng thay cho phía nước ngoài quy định tại 
khoản 3 và khoản 4 Điều 4 của Luật này. Bộ trưởng Bộ Tài chính quy định chứng từ nộp thuế 
giá trị gia tăng thay cho phía nước ngoài; 
b) Có chứng từ thanh toán không dùng tiền mặt đối với hàng hóa, dịch vụ mua vào, trừ một số 
trường hợp đặc thù theo quy định của Chính phủ; 
c) Đối với hàng hóa, dịch vụ xuất khẩu, ngoài các điều kiện quy định tại điểm a và điểm b khoản 
này còn phải có: hợp đồng ký kết với bên nước ngoài về việc bán, gia công hàng hóa, cung cấp 
dịch vụ; hóa đơn bán hàng hóa, cung cấp dịch vụ; chứng từ thanh toán không dùng tiền mặt; tờ 
khai hải quan đối với hàng hóa xuất khẩu; phiếu đóng gói, vận đơn, chứng từ bảo hiểm hàng hóa 
(nếu có). Chính phủ quy định về điều kiện khấu trừ đối với trường hợp xuất khẩu hàng hóa qua 
sàn thương mại điện tử ở nước ngoài và một số trường hợp đặc thù khác. 
3. Cơ sở kinh doanh không đáp ứng quy định về khấu trừ thuế tại khoản 1 và khoản 2 Điều này 
và các hóa đơn, chứng từ được lập từ các hành vi bị nghiêm cấm tại Luật này thì không được 
khấu trừ thuế giá trị gia tăng. 
4. Chính phủ quy định chi tiết Điều này.

[RULES]
{"id": "TAX-04-D14-000", "type": "condition", "premises": ["is_taxpayer_using_direct_tax_method", "goods_subject_to_vat"], "conclusion": "must_deduct_input_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 14 khoản 1 điểm a", "exception_to": "", "quote": "Thuế giá trị gia tăng đầu vào của hàng hóa, dịch vụ sử dụng cho sản xuất, kinh doanh hàng hóa, dịch vụ chịu thuế giá trị gia tăng được khấu trừ toàn bộ."}
{"id": "TAX-04-D14-001", "type": "condition", "premises": ["is_taxpayer_using_direct_tax_method", "goods_subject_to_vat", "~not_goods_subject_to_vat"], "conclusion": "must_deduct_input_vat_proportionally", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 14 khoản 1 điểm b", "exception_to": "", "quote": "Cơ sở kinh doanh phải hạch toán riêng thuế giá trị gia tăng đầu vào được khấu trừ và không được khấu trừ."}
{"id": "TAX-04-D14-002", "type": "condition", "premises": ["is_taxpayer_using_direct_tax_method", "is_selling_goods_to_foreign_entities"], "conclusion": "must_deduct_input_vat_full", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 14 khoản 1 điểm c", "exception_to": "", "quote": "Thuế giá trị gia tăng đầu vào của hàng hóa, dịch vụ bán cho tổ chức, cá nhân sử dụng vốn viện trợ nhân đạo, viện trợ không hoàn lại được khấu trừ toàn bộ."}
{"id": "TAX-04-D14-003", "type": "condition", "premises": ["is_taxpayer_using_direct_tax_method", "is_using_goods_for_oil_exploration"], "conclusion": "must_deduct_input_vat_full", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 14 khoản 1 điểm d", "exception_to": "", "quote": "Thuế giá trị gia tăng đầu vào của hàng hóa, dịch vụ sử dụng cho hoạt động tìm kiếm thăm dò, phát triển mỏ dầu khí được khấu trừ toàn bộ."}
{"id": "TAX-04-D14-004", "type": "condition", "premises": ["is_taxpayer_using_direct_tax_method"], "conclusion": "must_deduct_input_vat_in_next_period", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 14 khoản 1 điểm đ", "exception_to": "", "quote": "Số thuế giá trị gia tăng đầu vào chưa được khấu trừ hết trong tháng, quý thì được khấu trừ vào tháng, quý tiếp theo."}
{"id": "TAX-04-D14-005", "type": "condition", "premises": ["has_valid_invoice"], "conclusion": "must_have_invoice_for_deduction", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 14 khoản 2 điểm a", "exception_to": "", "quote": "Có hóa đơn giá trị gia tăng mua hàng hóa, dịch vụ hoặc chứng từ nộp thuế giá trị gia tăng ở khâu nhập khẩu."}
{"id": "TAX-04-D14-006", "type": "condition", "premises": ["has_payment_receipt"], "conclusion": "must_use_non_cash_payment_receipt", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 14 khoản 2 điểm b", "exception_to": "", "quote": "Có chứng từ thanh toán không dùng tiền mặt đối với hàng hóa, dịch vụ mua vào."}
{"id": "TAX-04-D14-007", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad"], "conclusion": "must_have_export_contract", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 14 khoản 2 điểm c", "exception_to": "", "quote": "Đối với hàng hóa, dịch vụ xuất khẩu, ngoài các điều kiện quy định tại điểm a và điểm b khoản này còn phải có: hợp đồng ký kết với bên nước ngoài về việc bán, gia công hàng hóa, cung cấp dịch vụ."}
{"id": "TAX-04-D14-008", "type": "condition", "premises": ["not_meeting_deduction_conditions"], "conclusion": "must_not_deduct_input_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 14 khoản 3", "exception_to": "", "quote": "Cơ sở kinh doanh không đáp ứng quy định về khấu trừ thuế tại khoản 1 và khoản 2 Điều này thì không được khấu trừ thuế giá trị gia tăng."}


######## 04_luat_thue_GTGT_48_2024_QH15 — Điều 5. Đối tượng không chịu thuế
[NGUYÊN VĂN]
Điều 5. Đối tượng không chịu thuế 
1. Sản phẩm cây trồng, rừng trồng, chăn nuôi, thủy sản nuôi trồng, đánh bắt chưa chế biến thành 
các sản phẩm khác hoặc chỉ qua sơ chế thông thường của tổ chức, cá nhân tự sản xuất, đánh bắt 
bán ra và ở khâu nhập khẩu. 
2. Sản phẩm giống vật nuôi theo quy định của pháp luật về chăn nuôi, vật liệu nhân giống cây 
trồng theo quy định của pháp luật về trồng trọt. 
3. Thức ăn chăn nuôi theo quy định của pháp luật về chăn nuôi; thức ăn thủy sản theo quy định 
của pháp luật về thủy sản. 
4. Sản phẩm muối được sản xuất từ nước biển, muối mỏ tự nhiên, muối tinh, muối i-ốt mà thành 
phần chính là Na-tri-clo-rua (NaCl). 
5. Nhà ở thuộc tài sản công do Nhà nước bán cho người đang thuê. 
6. Tưới, tiêu nước; cày, bừa đất; nạo vét kênh, mương nội đồng phục vụ sản xuất nông nghiệp; 
dịch vụ thu hoạch sản phẩm nông nghiệp. 
7. Chuyển quyền sử dụng đất. 
8. Bảo hiểm nhân thọ, bảo hiểm sức khỏe, bảo hiểm người học, các dịch vụ bảo hiểm khác liên 
quan đến con người; bảo hiểm vật nuôi, bảo hiểm cây trồng, các dịch vụ bảo hiểm nông nghiệp 
khác; bảo hiểm tàu, thuyền, trang thiết bị và các dụng cụ cần thiết khác phục vụ trực tiếp đánh 
bắt thủy sản; tái bảo hiểm; bảo hiểm các công trình, thiết bị dầu khí, tàu chứa dầu mang quốc tịch 
nước ngoài do nhà thầu dầu khí hoặc nhà thầu phụ nước ngoài thuê để hoạt động tại vùng biển 
Việt Nam, vùng biển chồng lấn mà Việt Nam và các quốc gia có bờ biển tiếp liền hay đối diện đã 
thỏa thuận đặt dưới chế độ khai thác chung. 
9. Các dịch vụ tài chính, ngân hàng, kinh doanh chứng khoán, thương mại sau đây: 
a) Dịch vụ cấp tín dụng theo quy định của pháp luật về các tổ chức tín dụng và các khoản phí 
được nêu cụ thể tại Hợp đồng vay vốn của Chính phủ Việt Nam với Bên cho vay nước ngoài; 
b) Dịch vụ cho vay của người nộp thuế không phải là tổ chức tín dụng; 
c) Kinh doanh chứng khoán bao gồm môi giới chứng khoán, tự doanh chứng khoán, bảo lãnh 
phát hành chứng khoán, tư vấn đầu tư chứng khoán, quản lý quỹ đầu tư chứng khoán, quản lý 
danh mục đầu tư chứng khoán theo quy định của pháp luật về chứng khoán; 
d) Chuyển nhượng vốn bao gồm chuyển nhượng một phần hoặc toàn bộ số vốn đã đầu tư vào tổ 
chức kinh tế khác (không phân biệt có thành lập hay không thành lập pháp nhân mới), chuyển 
nhượng chứng khoán, chuyển nhượng quyền góp vốn và các hình thức chuyển nhượng vốn khác 
theo quy định của pháp luật, kể cả trường hợp bán doanh nghiệp cho doanh nghiệp khác để sản 
xuất, kinh doanh và doanh nghiệp mua kế thừa toàn bộ quyền và nghĩa vụ của doanh nghiệp bán 
theo quy định của pháp luật. Chuyển nhượng vốn quy định tại điểm này không bao gồm chuyển 
nhượng dự án đầu tư, bán tài sản; 
đ) Bán nợ bao gồm bán khoản phải trả và khoản phải thu; 
e) Kinh doanh ngoại tệ; 
g) Sản phẩm phái sinh theo quy định của pháp luật về các tổ chức tín dụng, pháp luật về chứng 
khoán và pháp luật về thương mại, bao gồm: hoán đổi lãi suất; hợp đồng kỳ hạn; hợp đồng tương 
lai; hợp đồng quyền chọn mua, chọn bán và sản phẩm phái sinh khác; 
h) Bán tài sản bảo đảm của khoản nợ của tổ chức mà Nhà nước sở hữu 100% vốn điều lệ do 
Chính phủ thành lập có chức năng mua, bán nợ để xử lý nợ xấu của các tổ chức tín dụng Việt 
Nam. 
10. Các dịch vụ y tế, dịch vụ thú y sau đây: 
a) Dịch vụ y tế bao gồm: dịch vụ khám bệnh, chữa bệnh, phòng bệnh cho người, dịch vụ sinh đẻ 
có kế hoạch, dịch vụ điều dưỡng sức khoẻ, phục hồi chức năng cho người bệnh; dịch vụ chăm 
sóc người cao tuổi, người khuyết tật; vận chuyển người bệnh, dịch vụ cho thuê phòng bệnh, 
giường bệnh của các cơ sở y tế; xét nghiệm, chiếu, chụp; máu và chế phẩm máu dùng cho người 
bệnh. 
Dịch vụ chăm sóc người cao tuổi, người khuyết tật bao gồm cả chăm sóc về y tế, dinh dưỡng và 
tổ chức các hoạt động văn hóa, thể thao, giải trí, vật lý trị liệu, phục hồi chức năng cho người cao 
tuổi, người khuyết tật. 
Trường hợp trong gói dịch vụ chữa bệnh theo quy định của Bộ Y tế bao gồm cả sử dụng thuốc 
chữa bệnh thì khoản thu từ tiền thuốc chữa bệnh nằm trong gói dịch vụ chữa bệnh cũng thuộc đối 
tượng không chịu thuế giá trị gia tăng; 
b) Dịch vụ thú y bao gồm: dịch vụ khám bệnh, chữa bệnh, phòng bệnh cho vật nuôi. 
11. Dịch vụ tang lễ. 
12. Hoạt động duy tu, sửa chữa, xây dựng bằng nguồn vốn đóng góp của nhân dân, vốn viện trợ 
nhân đạo (chiếm từ 50% tổng số vốn sử dụng cho công trình trở lên) đối với các di tích lịch sử - 
văn hóa, danh lam thắng cảnh, các công trình văn hóa, nghệ thuật, công trình phục vụ công cộng, 
cơ sở hạ tầng và nhà ở cho đối tượng chính sách xã hội. 
13. Hoạt động dạy học, dạy nghề theo quy định của pháp luật về giáo dục, giáo dục nghề nghiệp. 
14. Phát sóng truyền thanh, truyền hình bằng nguồn vốn ngân sách nhà nước. 
15. Xuất bản, nhập khẩu, phát hành báo, tạp chí, bản tin, đặc san, sách chính trị, sách giáo khoa, 
giáo trình, sách văn bản pháp luật, sách khoa học - kỹ thuật, sách phục vụ thông tin đối ngoại, 
sách in bằng chữ dân tộc thiểu số và tranh, ảnh, áp phích tuyên truyền cổ động, kể cả dưới dạng 
băng hoặc đĩa ghi tiếng, ghi hình, dữ liệu điện tử; tiền, in tiền. 
16. Vận chuyển hành khách công cộng bằng xe buýt, tàu điện, phương tiện thủy nội địa. 
17. Máy móc, thiết bị, phụ tùng, vật tư thuộc loại trong nước chưa sản xuất được cần nhập khẩu 
để sử dụng trực tiếp cho hoạt động nghiên cứu khoa học, phát triển công nghệ; máy móc, thiết bị, 
phụ tùng thay thế, phương tiện vận tải chuyên dùng và vật tư thuộc loại trong nước chưa sản xuất 
được cần nhập khẩu để tiến hành hoạt động tìm kiếm thăm dò, phát triển mỏ dầu khí; máy bay, 
trực thăng, tàu lượn, giàn khoan, tàu thuyền thuộc loại trong nước chưa sản xuất được cần nhập 
khẩu để tạo tài sản cố định của doanh nghiệp hoặc thuê của nước ngoài để sử dụng cho sản xuất, 
kinh doanh, cho thuê. 
18. Sản phẩm quốc phòng, an ninh theo danh mục do Bộ trưởng Bộ Quốc phòng, Bộ trưởng Bộ 
Công an ban hành; sản phẩm, dịch vụ nhập khẩu phục vụ công nghiệp quốc phòng, an ninh theo 
danh mục do Thủ tướng Chính phủ ban hành. 
19. Hàng hóa nhập khẩu trong trường hợp viện trợ nhân đạo, viện trợ không hoàn lại. Hàng hóa, 
dịch vụ bán cho tổ chức, cá nhân nước ngoài, tổ chức quốc tế để viện trợ nhân đạo, viện trợ 
không hoàn lại cho Việt Nam. 
20. Hàng hóa chuyển khẩu, quá cảnh qua lãnh thổ Việt Nam; hàng tạm nhập khẩu, tái xuất khẩu; 
hàng tạm xuất khẩu, tái nhập khẩu; nguyên liệu nhập khẩu để sản xuất, gia công hàng hóa xuất 
khẩu theo hợp đồng sản xuất, gia công xuất khẩu ký kết với bên nước ngoài; hàng hóa, dịch vụ 
được mua bán giữa nước ngoài với các khu phi thuế quan và giữa các khu phi thuế quan với 
nhau. 
Hàng hóa nhập khẩu từ nước ngoài của công ty cho thuê tài chính được vận chuyển thẳng vào 
khu phi thuế quan để cho doanh nghiệp trong khu phi thuế quan thuê tài chính. 
21. Chuyển giao công nghệ theo quy định của Luật Chuyển giao công nghệ; chuyển nhượng 
quyền sở hữu trí tuệ theo quy định của Luật Sở hữu trí tuệ; sản phẩm phần mềm và dịch vụ phần 
mềm theo quy định của pháp luật. 
22. Vàng dạng thỏi, miếng chưa được chế tác thành sản phẩm mỹ nghệ, đồ trang sức hay sản 
phẩm khác ở khâu nhập khẩu. 
23. Sản phẩm xuất khẩu là tài nguyên, khoáng sản khai thác chưa chế biến thành sản phẩm khác 
và sản phẩm xuất khẩu là tài nguyên, khoáng sản khai thác đã chế biến thành sản phẩm khác theo 
Danh mục do Chính phủ quy định phù hợp với định hướng của nhà nước về không khuyến khích 
xuất khẩu, hạn chế xuất khẩu các tài nguyên, khoáng sản thô. 
24. Sản phẩm nhân tạo dùng để thay thế cho bộ phận cơ thể của người bệnh, bao gồm cả sản 
phẩm là bộ phận cấy ghép lâu dài trong cơ thể người; nạng, xe lăn và dụng cụ chuyên dùng khác 
cho người khuyết tật. 
25. Hàng hóa, dịch vụ của hộ, cá nhân sản xuất, kinh doanh có mức doanh thu hằng năm từ 200 
triệu đồng trở xuống; tài sản của tổ chức, cá nhân không kinh doanh, không phải là người nộp 
thuế giá trị gia tăng bán ra; hàng dự trữ quốc gia do cơ quan dự trữ quốc gia bán ra; các khoản 
thu phí, lệ phí theo quy định của pháp luật về phí và lệ phí. 
26. Hàng hóa nhập khẩu trong trường hợp sau đây: 
a) Quà tặng cho cơ quan nhà nước, tổ chức chính trị, tổ chức chính trị - xã hội, tổ chức chính trị 
xã hội - nghề nghiệp, tổ chức xã hội, tổ chức xã hội - nghề nghiệp, đơn vị vũ trang nhân dân 
trong định mức miễn thuế nhập khẩu theo quy định của pháp luật về thuế xuất khẩu, thuế nhập 
khẩu; 
b) Quà biếu, quà tặng trong định mức miễn thuế nhập khẩu theo quy định của pháp luật về thuế 
xuất khẩu, thuế nhập khẩu của tổ chức, cá nhân nước ngoài cho cá nhân Việt Nam; đồ dùng của 
tổ chức, cá nhân nước ngoài theo tiêu chuẩn miễn trừ ngoại giao và tài sản di chuyển trong định 
mức miễn thuế nhập khẩu theo quy định của pháp luật về thuế xuất khẩu, thuế nhập khẩu; 
c) Hàng hoá trong tiêu chuẩn hành lý miễn thuế nhập khẩu theo quy định của pháp luật về thuế 
xuất khẩu, thuế nhập khẩu; 
d) Hàng hóa nhập khẩu ủng hộ, tài trợ cho phòng, chống, khắc phục hậu quả thảm họa, thiên tai, 
dịch bệnh, chiến tranh theo quy định của Chính phủ; 
đ) Hàng hóa mua bán, trao đổi qua biên giới để phục vụ cho sản xuất, tiêu dùng của cư dân biên 
giới thuộc Danh mục hàng hóa mua bán, trao đổi của cư dân biên giới theo quy định của pháp 
luật và trong định mức miễn thuế nhập khẩu theo quy định của pháp luật về thuế xuất khẩu, thuế 
nhập khẩu; 
e) Di vật, cổ vật, bảo vật quốc gia theo quy định của pháp luật về di sản văn hóa do cơ quan nhà 
nước có thẩm quyền nhập khẩu. 
27. Cơ sở kinh doanh hàng hóa, dịch vụ không chịu thuế giá trị gia tăng quy định tại Điều này 
không được khấu trừ, không được hoàn thuế giá trị gia tăng đầu vào, trừ trường hợp được áp 
dụng mức thuế suất 0% quy định tại khoản 1 Điều 9 của Luật này. 
28. Chính phủ quy định chi tiết Điều này. Bộ trưởng Bộ Tài chính quy định hồ sơ, thủ tục xác 
định đối tượng không chịu thuế giá trị gia tăng quy định tại Điều này. 
Chương II 
CĂN CỨ VÀ PHƯƠNG PHÁP TÍNH THUẾ

[RULES]
{"id": "TAX-04-D5-000", "type": "condition", "premises": ["is_agriculture_product", "is_not_processed"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 1", "exception_to": "", "quote": "Sản phẩm cây trồng, rừng trồng, chăn nuôi, thủy sản nuôi trồng, đánh bắt chưa chế biến thành các sản phẩm khác hoặc chỉ qua sơ chế thông thường."}
{"id": "TAX-04-D5-001", "type": "condition", "premises": ["is_breeding_material"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 2", "exception_to": "", "quote": "Sản phẩm giống vật nuôi theo quy định của pháp luật về chăn nuôi, vật liệu nhân giống cây trồng theo quy định của pháp luật về trồng trọt."}
{"id": "TAX-04-D5-002", "type": "condition", "premises": ["is_feed"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 3", "exception_to": "", "quote": "Thức ăn chăn nuôi theo quy định của pháp luật về chăn nuôi; thức ăn thủy sản theo quy định của pháp luật về thủy sản."}
{"id": "TAX-04-D5-003", "type": "condition", "premises": ["is_salt_product"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 4", "exception_to": "", "quote": "Sản phẩm muối được sản xuất từ nước biển, muối mỏ tự nhiên, muối tinh, muối i-ốt mà thành phần chính là Na-tri-clo-rua (NaCl)."}
{"id": "TAX-04-D5-004", "type": "condition", "premises": ["is_public_housing"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 5", "exception_to": "", "quote": "Nhà ở thuộc tài sản công do Nhà nước bán cho người đang thuê."}
{"id": "TAX-04-D5-005", "type": "condition", "premises": ["is_agricultural_service"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 6", "exception_to": "", "quote": "Tưới, tiêu nước; cày, bừa đất; nạo vét kênh, mương nội đồng phục vụ sản xuất nông nghiệp; dịch vụ thu hoạch sản phẩm nông nghiệp."}
{"id": "TAX-04-D5-006", "type": "condition", "premises": ["is_land_use_transfer"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 7", "exception_to": "", "quote": "Chuyển quyền sử dụng đất."}
{"id": "TAX-04-D5-007", "type": "condition", "premises": ["is_life_insurance"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 8", "exception_to": "", "quote": "Bảo hiểm nhân thọ, bảo hiểm sức khỏe, bảo hiểm người học, các dịch vụ bảo hiểm khác liên quan đến con người."}
{"id": "TAX-04-D5-008", "type": "condition", "premises": ["is_financial_service"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 9", "exception_to": "", "quote": "Các dịch vụ tài chính, ngân hàng, kinh doanh chứng khoán."}
{"id": "TAX-04-D5-009", "type": "condition", "premises": ["is_health_service"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 10", "exception_to": "", "quote": "Các dịch vụ y tế, dịch vụ thú y."}
{"id": "TAX-04-D5-010", "type": "condition", "premises": ["is_funeral_service"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 11", "exception_to": "", "quote": "Dịch vụ tang lễ."}
{"id": "TAX-04-D5-011", "type": "condition", "premises": ["is_maintenance_construction"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 12", "exception_to": "", "quote": "Hoạt động duy tu, sửa chữa, xây dựng bằng nguồn vốn đóng góp của nhân dân."}
{"id": "TAX-04-D5-012", "type": "condition", "premises": ["is_education_service"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 13", "exception_to": "", "quote": "Hoạt động dạy học, dạy nghề theo quy định của pháp luật về giáo dục."}
{"id": "TAX-04-D5-013", "type": "condition", "premises": ["is_broadcasting_service"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 14", "exception_to": "", "quote": "Phát sóng truyền thanh, truyền hình bằng nguồn vốn ngân sách nhà nước."}
{"id": "TAX-04-D5-014", "type": "condition", "premises": ["is_publication_service"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 15", "exception_to": "", "quote": "Xuất bản, nhập khẩu, phát hành báo, tạp chí, sách."}
{"id": "TAX-04-D5-015", "type": "condition", "premises": ["is_public_transport_service"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 16", "exception_to": "", "quote": "Vận chuyển hành khách công cộng bằng xe buýt, tàu điện."}
{"id": "TAX-04-D5-016", "type": "condition", "premises": ["is_imported_equipment_for_research"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 17", "exception_to": "", "quote": "Máy móc, thiết bị, phụ tùng thuộc loại trong nước chưa sản xuất được cần nhập khẩu."}
{"id": "TAX-04-D5-017", "type": "condition", "premises": ["is_defense_security_product"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 18", "exception_to": "", "quote": "Sản phẩm quốc phòng, an ninh theo danh mục do Bộ trưởng Bộ Quốc phòng, Bộ trưởng Bộ Công an ban hành."}
{"id": "TAX-04-D5-018", "type": "condition", "premises": ["is_humanitarian_aid"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 19", "exception_to": "", "quote": "Hàng hóa nhập khẩu trong trường hợp viện trợ nhân đạo."}
{"id": "TAX-04-D5-019", "type": "condition", "premises": ["is_transit_goods"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 20", "exception_to": "", "quote": "Hàng hóa chuyển khẩu, quá cảnh qua lãnh thổ Việt Nam."}
{"id": "TAX-04-D5-020", "type": "condition", "premises": ["is_technology_transfer"], "conclusion": "is_exempt_from_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 21", "exception_to": "", "quote": "Chuyển giao công nghệ theo quy định của Luật Chuyển giao công nghệ."}
{"id": "TAX-04-D5-100", "type": "condition", "premises": ["is_importing_gold_in_raw_form"], "conclusion": "not_subject_to_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 22", "exception_to": "", "quote": "Vàng dạng thỏi, miếng chưa được chế tác thành sản phẩm mỹ nghệ, đồ trang sức hay sản phẩm khác ở khâu nhập khẩu."}
{"id": "TAX-04-D5-101", "type": "condition", "premises": ["is_exporting_raw_resources"], "conclusion": "not_subject_to_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 23", "exception_to": "", "quote": "Sản phẩm xuất khẩu là tài nguyên, khoáng sản khai thác chưa chế biến thành sản phẩm khác."}
{"id": "TAX-04-D5-102", "type": "condition", "premises": ["is_exporting_processed_resources"], "conclusion": "not_subject_to_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 23", "exception_to": "", "quote": "Sản phẩm xuất khẩu là tài nguyên, khoáng sản khai thác đã chế biến thành sản phẩm khác theo Danh mục do Chính phủ quy định."}
{"id": "TAX-04-D5-103", "type": "condition", "premises": ["is_using_medical_artificial_products"], "conclusion": "not_subject_to_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 24", "exception_to": "", "quote": "Sản phẩm nhân tạo dùng để thay thế cho bộ phận cơ thể của người bệnh."}
{"id": "TAX-04-D5-104", "type": "condition", "premises": ["is_business_with_revenue_below_200_million"], "conclusion": "not_subject_to_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 25", "exception_to": "", "quote": "Hàng hóa, dịch vụ của hộ, cá nhân sản xuất, kinh doanh có mức doanh thu hằng năm từ 200 triệu đồng trở xuống."}
{"id": "TAX-04-D5-105", "type": "condition", "premises": ["is_importing_gifts_to_government_entities"], "conclusion": "not_subject_to_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 26", "exception_to": "", "quote": "Quà tặng cho cơ quan nhà nước, tổ chức chính trị, tổ chức chính trị - xã hội, tổ chức chính trị xã hội - nghề nghiệp."}
{"id": "TAX-04-D5-106", "type": "condition", "premises": ["is_importing_gifts_from_foreign_entities"], "conclusion": "not_subject_to_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 26", "exception_to": "", "quote": "Quà biếu, quà tặng trong định mức miễn thuế nhập khẩu theo quy định của pháp luật."}
{"id": "TAX-04-D5-107", "type": "condition", "premises": ["is_importing_goods_for_disaster_relief"], "conclusion": "not_subject_to_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 26", "exception_to": "", "quote": "Hàng hóa nhập khẩu ủng hộ, tài trợ cho phòng, chống, khắc phục hậu quả thảm họa."}
{"id": "TAX-04-D5-108", "type": "condition", "premises": ["is_business_not_subject_to_vat"], "conclusion": "not_deduct_input_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 5 khoản 27", "exception_to": "", "quote": "Cơ sở kinh doanh hàng hóa, dịch vụ không chịu thuế giá trị gia tăng quy định tại Điều này không được khấu trừ."}


######## 04_luat_thue_GTGT_48_2024_QH15 — Điều 9. Thuế suất
[NGUYÊN VĂN]
Điều 9. Thuế suất 
1. Mức thuế suất 0% áp dụng đối với hàng hóa, dịch vụ sau đây: 
a) Hàng hóa xuất khẩu bao gồm: hàng hóa từ Việt Nam bán cho tổ chức, cá nhân ở nước ngoài 
và được tiêu dùng ở ngoài Việt Nam; hàng hóa từ nội địa Việt Nam bán cho tổ chức trong khu 
phi thuế quan và được tiêu dùng trong khu phi thuế quan phục vụ trực tiếp cho hoạt động sản 
xuất xuất khẩu; hàng hóa đã bán tại khu vực cách ly cho cá nhân (người nước ngoài hoặc người 
Việt Nam) đã làm thủ tục xuất cảnh; hàng hóa đã bán tại cửa hàng miễn thuế; 
b) Dịch vụ xuất khẩu bao gồm: dịch vụ cung cấp trực tiếp cho tổ chức, cá nhân ở nước ngoài và 
được tiêu dùng ở ngoài Việt Nam; dịch vụ cung cấp trực tiếp cho tổ chức ở trong khu phi thuế 
quan và được tiêu dùng trong khu phi thuế quan phục vụ trực tiếp cho hoạt động sản xuất xuất 
khẩu; 
c) Hàng hóa, dịch vụ xuất khẩu khác bao gồm: vận tải quốc tế; dịch vụ cho thuê phương tiện vận 
tải được sử dụng ngoài phạm vi lãnh thổ Việt Nam; dịch vụ của ngành hàng không, hàng hải 
cung cấp trực tiếp hoặc thông qua đại lý cho vận tải quốc tế; hoạt động xây dựng, lắp đặt công 
trình ở nước ngoài hoặc ở trong khu phi thuế quan; sản phẩm nội dung thông tin số cung cấp cho 
bên nước ngoài và có hồ sơ, tài liệu chứng minh tiêu dùng ở ngoài Việt Nam theo quy định của 
Chính phủ; phụ tùng, vật tư thay thế để sửa chữa, bảo dưỡng phương tiện, máy móc, thiết bị cho 
bên nước ngoài và tiêu dùng ở ngoài Việt Nam; hàng hóa gia công chuyển tiếp để xuất khẩu theo 
quy định của pháp luật; hàng hóa, dịch vụ thuộc đối tượng không chịu thuế giá trị gia tăng khi 
xuất khẩu, trừ các trường hợp không áp dụng mức thuế suất 0% quy định tại điểm d khoản này; 
d) Các trường hợp không áp dụng thuế suất 0% bao gồm: chuyển giao công nghệ, chuyển 
nhượng quyền sở hữu trí tuệ ra nước ngoài; dịch vụ tái bảo hiểm ra nước ngoài; dịch vụ cấp tín 
dụng; chuyển nhượng vốn; sản phẩm phái sinh; dịch vụ bưu chính, viễn thông; sản phẩm xuất 
khẩu quy định tại khoản 23 Điều 5 của Luật này; thuốc lá, rượu, bia nhập khẩu sau đó xuất khẩu; 
xăng, dầu mua tại nội địa bán cho cơ sở kinh doanh trong khu phi thuế quan; xe ô tô bán cho tổ 
chức, cá nhân trong khu phi thuế quan. 
2. Mức thuế suất 5% áp dụng đối với hàng hóa, dịch vụ sau đây: 
a) Nước sạch phục vụ sản xuất và sinh hoạt không bao gồm các loại nước uống đóng chai, đóng 
bình và các loại nước giải khát khác; 
b) Phân bón, quặng để sản xuất phân bón, thuốc bảo vệ thực vật và chất kích thích tăng trưởng 
vật nuôi theo quy định của pháp luật; 
c) Dịch vụ đào đắp, nạo vét kênh, mương, ao hồ phục vụ sản xuất nông nghiệp; nuôi trồng, chăm 
sóc, phòng trừ sâu bệnh cho cây trồng; sơ chế, bảo quản sản phẩm nông nghiệp; 
d) Sản phẩm cây trồng, rừng trồng (trừ gỗ, măng), chăn nuôi, thuỷ sản nuôi trồng, đánh bắt chưa 
chế biến thành các sản phẩm khác hoặc chỉ qua sơ chế thông thường, trừ sản phẩm quy định tại 
khoản 1 Điều 5 của Luật này; 
đ) Mủ cao su dạng mủ cờ rếp, mủ tờ, mủ bún, mủ cốm; lưới, dây giềng và sợi để đan lưới đánh 
cá; 
e) Sản phẩm bằng đay, cói, tre, nứa, lá, rơm, vỏ dừa, sọ dừa, bèo tây và các sản phẩm thủ công 
khác sản xuất bằng nguyên liệu tận dụng từ nông nghiệp; xơ bông đã qua chải thô, chải kỹ; giấy 
in báo; 
g) Tàu khai thác thủy sản tại vùng biển; máy móc, thiết bị chuyên dùng phục vụ cho sản xuất 
nông nghiệp theo quy định của Chính phủ; 
h) Thiết bị y tế theo quy định của pháp luật về quản lý thiết bị y tế; thuốc phòng bệnh, chữa 
bệnh; dược chất, dược liệu là nguyên liệu sản xuất thuốc chữa bệnh, thuốc phòng bệnh; 
i) Thiết bị dùng để giảng dạy và học tập bao gồm: các loại mô hình, hình vẽ, bảng, phấn, thước, 
com-pa; 
k) Hoạt động nghệ thuật biểu diễn truyền thống, dân gian; 
l) Đồ chơi cho trẻ em; sách các loại, trừ sách quy định tại khoản 15 Điều 5 của Luật này; 
m) Dịch vụ khoa học, công nghệ theo quy định của Luật Khoa học và công nghệ; 
n) Bán, cho thuê, cho thuê mua nhà ở xã hội theo quy định của Luật Nhà ở. 
3. Mức thuế suất 10% áp dụng đối với hàng hóa, dịch vụ không quy định tại khoản 1 và khoản 2 
Điều này, bao gồm cả dịch vụ được các nhà cung cấp nước ngoài không có cơ sở thường trú tại 
Việt Nam cung cấp cho tổ chức, cá nhân tại Việt Nam qua kênh thương mại điện tử và các nền 
tảng số. 
4. Cơ sở kinh doanh nhiều loại hàng hóa, dịch vụ có mức thuế suất thuế giá trị gia tăng khác 
nhau (bao gồm cả đối tượng không chịu thuế giá trị gia tăng) phải khai thuế giá trị gia tăng theo 
từng mức thuế suất quy định đối với từng loại hàng hóa, dịch vụ; nếu cơ sở kinh doanh không 
xác định theo từng mức thuế suất thì phải tính và nộp thuế theo mức thuế suất cao nhất của hàng 
hóa, dịch vụ mà cơ sở sản xuất, kinh doanh. 
5. Sản phẩm cây trồng, rừng trồng, chăn nuôi, thủy sản nuôi trồng, đánh bắt chưa chế biến thành 
các sản phẩm khác hoặc chỉ qua sơ chế thông thường được sử dụng làm thức ăn chăn nuôi, dược 
liệu thì áp dụng thuế suất giá trị gia tăng theo mức thuế suất quy định cho sản phẩm cây trồng, 
rừng trồng, chăn nuôi, thủy sản. 
Phế phẩm, phụ phẩm, phế liệu được thu hồi để tái chế, sử dụng lại khi bán ra áp dụng mức thuế 
suất theo thuế suất của mặt hàng phế phẩm, phụ phẩm, phế liệu bán ra. 
6. Chính phủ quy định chi tiết khoản 1 và khoản 2 Điều này. Bộ trưởng Bộ Tài chính quy định 
hồ sơ, thủ tục áp dụng thuế suất thuế giá trị gia tăng 0% tại khoản 1 Điều này.

[RULES]
{"id": "TAX-04-D9-000", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad"], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 9 khoản 1 điểm a", "exception_to": "", "quote": "Mức thuế suất 0% áp dụng đối với hàng hóa, dịch vụ sau đây: Hàng hóa xuất khẩu bao gồm: hàng hóa từ Việt Nam bán cho tổ chức, cá nhân ở nước ngoài và được tiêu dùng ở ngoài Việt Nam."}
{"id": "TAX-04-D9-001", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad"], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 9 khoản 1 điểm b", "exception_to": "", "quote": "Mức thuế suất 0% áp dụng đối với hàng hóa, dịch vụ sau đây: Dịch vụ xuất khẩu bao gồm: dịch vụ cung cấp trực tiếp cho tổ chức, cá nhân ở nước ngoài và được tiêu dùng ở ngoài Việt Nam."}
{"id": "TAX-04-D9-002", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad"], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 9 khoản 1 điểm c", "exception_to": "", "quote": "Mức thuế suất 0% áp dụng đối với hàng hóa, dịch vụ sau đây: Hàng hóa, dịch vụ xuất khẩu khác bao gồm: vận tải quốc tế; dịch vụ cho thuê phương tiện vận tải được sử dụng ngoài phạm vi lãnh thổ Việt Nam."}
{"id": "TAX-04-D9-003", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad"], "conclusion": "~must_use_e_invoice_for_exported_goods_or_services", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 9 khoản 1 điểm d", "exception_to": "", "quote": "Các trường hợp không áp dụng thuế suất 0% bao gồm: chuyển giao công nghệ, chuyển nhượng quyền sở hữu trí tuệ ra nước ngoài."}
{"id": "TAX-04-D9-004", "type": "condition", "premises": [], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 9 khoản 2 điểm a", "exception_to": "", "quote": "Mức thuế suất 5% áp dụng đối với hàng hóa, dịch vụ sau đây: Nước sạch phục vụ sản xuất và sinh hoạt không bao gồm các loại nước uống đóng chai, đóng bình và các loại nước giải khát khác."}
{"id": "TAX-04-D9-005", "type": "condition", "premises": [], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 9 khoản 2 điểm b", "exception_to": "", "quote": "Mức thuế suất 5% áp dụng đối với hàng hóa, dịch vụ sau đây: Phân bón, quặng để sản xuất phân bón, thuốc bảo vệ thực vật và chất kích thích tăng trưởng vật nuôi theo quy định của pháp luật."}
{"id": "TAX-04-D9-006", "type": "condition", "premises": [], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 9 khoản 2 điểm c", "exception_to": "", "quote": "Mức thuế suất 5% áp dụng đối với hàng hóa, dịch vụ sau đây: Dịch vụ đào đắp, nạo vét kênh, mương, ao hồ phục vụ sản xuất nông nghiệp."}
{"id": "TAX-04-D9-007", "type": "condition", "premises": [], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 9 khoản 2 điểm d", "exception_to": "", "quote": "Mức thuế suất 5% áp dụng đối với hàng hóa, dịch vụ sau đây: Sản phẩm cây trồng, rừng trồng (trừ gỗ, măng), chăn nuôi, thủy sản nuôi trồng, đánh bắt chưa chế biến thành các sản phẩm khác hoặc chỉ qua sơ chế thông thường."}
{"id": "TAX-04-D9-008", "type": "condition", "premises": [], "conclusion": "~must_use_e_invoice_for_exported_goods_or_services", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 9 khoản 3", "exception_to": "", "quote": "Mức thuế suất 10% áp dụng đối với hàng hóa, dịch vụ không quy định tại khoản 1 và khoản 2 Điều này."}


######## 05_nghi_dinh_181_2025_ND-CP — Điều 17. Mức thuế suất 0%
[NGUYÊN VĂN]
Điều 17. Mức thuế suất 0% 
Mức thuế suất 0% áp dụng đối với hàng hóa, dịch vụ quy định tại khoản 1 Điều 9 Luật Thuế giá 
trị gia tăng. Trong đó: 
1. Hàng hóa xuất khẩu bao gồm: 
a) Hàng hóa từ Việt Nam bán cho tổ chức, cá nhân ở nước ngoài và được tiêu dùng ở ngoài Việt 
Nam. 
b) Hàng hóa từ nội địa Việt Nam bán cho tổ chức trong khu phi thuế quan và được tiêu dùng 
trong khu phi thuế quan phục vụ trực tiếp cho hoạt động sản xuất xuất khẩu. 
c) Hàng hóa đã bán tại khu vực cách ly cho cá nhân (người nước ngoài hoặc người Việt Nam) đã 
làm thủ tục xuất cảnh; hàng hóa đã bán tại cửa hàng miễn thuế. Khu vực cách ly, cửa hàng miễn 
thuế xác định theo quy định tại Nghị định số 68/2016/NĐ-CP ngày 01 tháng 7 năm 2016 của 
Chính phủ quy định về điều kiện kinh doanh hàng miễn thuế, kho bãi, địa điểm làm thủ tục hải 
quan, tập kết, kiểm tra, giám sát hải quan (đã được sửa đổi, bổ sung bởi Nghị định số 
67/2020/NĐ-CP ngày 15 tháng 6 năm 2020 của Chính phủ). 
2. Dịch vụ xuất khẩu bao gồm: 
a) Dịch vụ cung cấp trực tiếp cho tổ chức, cá nhân ở nước ngoài và được tiêu dùng ở ngoài Việt 
Nam. Trong đó, cá nhân ở nước ngoài đáp ứng điều kiện ở ngoài Việt Nam trong thời gian diễn 
ra việc cung cấp dịch vụ. 
b) Dịch vụ cung cấp trực tiếp cho tổ chức ở trong khu phi thuế quan và được tiêu dùng trong khu 
phi thuế quan phục vụ trực tiếp cho hoạt động sản xuất xuất khẩu, bao gồm: dịch vụ cung cấp 
trực tiếp cho tổ chức ở trong khu phi thuế quan và được tiêu dùng trong khu phi thuế quan phục 
vụ trực tiếp cho hoạt động sản xuất xuất khẩu; dịch vụ vận chuyển, dịch vụ cung cấp cho doanh 
nghiệp chế xuất (dịch vụ nâng hạ container tại cảng, nhà máy, kho hàng; dịch vụ xếp dỡ, bốc xếp 
tại nhà máy, cảng, sân bay và các chi phí phát sinh có liên quan như: phí chứng từ, phí điện giao 
hàng, phí niêm chì, phí làm hàng, phí đóng gói). Tổ chức trong khu phi thuế quan là tổ chức có 
đăng ký kinh doanh. 
3. Hàng hóa, dịch vụ xuất khẩu khác bao gồm: vận tải quốc tế; dịch vụ cho thuê phương tiện vận 
tải được sử dụng ngoài phạm vi lãnh thổ Việt Nam; dịch vụ của ngành hàng không, hàng hải 
cung cấp trực tiếp hoặc thông qua đại lý cho vận tải quốc tế; hoạt động xây dựng, lắp đặt công 
trình ở nước ngoài hoặc ở trong khu phi thuế quan; sản phẩm nội dung thông tin số cung cấp cho 
bên nước ngoài và có hồ sơ, tài liệu chứng minh tiêu dùng ở ngoài Việt Nam; phụ tùng, vật tư 
thay thế để sửa chữa, bảo dưỡng phương tiện, máy móc, thiết bị cho bên nước ngoài và tiêu dùng 
ở ngoài Việt Nam; hàng hóa gia công chuyển tiếp để xuất khẩu theo quy định của pháp luật; 
hàng hóa, dịch vụ thuộc đối tượng không chịu thuế giá trị gia tăng khi xuất khẩu, trừ các trường 
hợp không áp dụng mức thuế suất 0% quy định tại khoản 4 Điều này. Trong đó: 
a) Vận tải quốc tế bao gồm vận tải hành khách, hành lý, hàng hóa theo chặng quốc tế từ Việt 
Nam ra nước ngoài hoặc từ nước ngoài đến Việt Nam, hoặc cả điểm đi và đến ở nước ngoài, 
không phân biệt có phương tiện trực tiếp vận tải hay không có phương tiện. Trường hợp, hợp 
đồng vận tải quốc tế bao gồm cả chặng vận tải nội địa thì vận tải quốc tế bao gồm cả chặng nội 
địa. 
b) Dịch vụ của ngành hàng không gồm: dịch vụ cung cấp suất ăn hàng không; dịch vụ cất hạ 
cánh tàu bay; dịch vụ sân đậu tàu bay; dịch vụ an ninh bảo vệ tàu bay; soi chiếu an ninh hành 
khách, hành lý và hàng hóa; dịch vụ băng chuyền hành lý tại nhà ga; dịch vụ phục vụ kỹ thuật 
thương mại mặt đất; dịch vụ bảo vệ tàu bay; dịch vụ kéo đẩy tàu bay; dịch vụ dẫn tàu bay; dịch 
vụ thuê cầu dẫn khách lên, xuống máy bay; dịch vụ điều hành bay đi, đến; dịch vụ vận chuyển tổ 
lái, tiếp viên và hành khách trong khu vực sân đậu tàu bay; chất xếp, kiểm đếm hàng hóa; dịch 
vụ phục vụ hành khách đi chuyến bay quốc tế từ cảng hàng không Việt Nam; dịch vụ sửa chữa 
tàu bay; dịch vụ tra nạp ngầm nhiên liệu cho các chuyến bay quốc tế. Dịch vụ của ngành hàng 
không áp dụng thuế suất 0% là những dịch vụ được thực hiện trong khu vực cảng hàng không 
quốc tế, sân bay, nhà ga hàng hóa hàng không quốc tế. 
c) Dịch vụ của ngành hàng hải gồm: dịch vụ lai dắt tàu biển; hoa tiêu hàng hải; cứu hộ hàng hải; 
cầu cảng, bến phao; bốc xếp; buộc cởi dây; đóng mở nắp hầm hàng; vệ sinh hầm tàu; kiểm đếm, 
giao nhận; đăng kiểm; dịch vụ sửa chữa tàu biển. Dịch vụ của ngành hàng hải áp dụng thuế suất 
0% là những dịch vụ được thực hiện tại khu vực cảng. 
d) Sản phẩm nội dung thông tin số cung cấp cho bên nước ngoài là sản phẩm nội dung, thông tin 
bao gồm văn bản, dữ liệu, hình ảnh, âm thanh được thể hiện dưới dạng số, được lưu giữ, truyền 
đưa trên môi trường mạng xác định theo quy định của pháp luật về công nghệ thông tin. Cơ sở 
kinh doanh cung cấp sản phẩm nội dung thông tin số phải có hồ sơ, tài liệu chứng minh tiêu dùng 
ở ngoài Việt Nam, như: thông tin về tình trạng cư trú của bên nước ngoài (tổ chức, cá nhân) ở 
nước ngoài (thông tin địa chỉ thanh toán, địa chỉ giao hàng, địa chỉ trụ sở, địa chỉ nhà hoặc các 
thông tin tương tự mà tổ chức, cá nhân mua hàng khai báo với cơ sở kinh doanh cung cấp dịch 
vụ ở Việt Nam); thông tin về truy cập của tổ chức, cá nhân ở nước ngoài, như thông tin về mã 
vùng điện thoại quốc gia của thẻ SIM, địa chỉ IP, vị trí đường dây điện thoại cố định hoặc các 
thông tin tương tự của tổ chức, cá nhân mua hàng hóa, dịch vụ. 
4. Các trường hợp không áp dụng thuế suất 0% quy định tại điểm b và d khoản 1 Điều 9 Luật 
Thuế giá trị gia tăng bao gồm: 
a) Chuyển giao công nghệ, chuyển nhượng quyền sở hữu trí tuệ ra nước ngoài. 
b) Dịch vụ tái bảo hiểm ra nước ngoài. 
c) Dịch vụ cấp tín dụng. 
d) Chuyển nhượng vốn. 
đ) Sản phẩm phái sinh. 
e) Dịch vụ bưu chính, viễn thông. 
g) Sản phẩm xuất khẩu quy định tại khoản 14 Điều 4 của Nghị định này. 
h) Thuốc lá, rượu, bia nhập khẩu sau đó xuất khẩu. 
i) Xăng, dầu mua tại nội địa bán cho cơ sở kinh doanh trong khu phi thuế quan; xe ô tô bán cho 
tổ chức, cá nhân trong khu phi thuế quan. 
k) Các dịch vụ cung cấp tại Việt Nam cho tổ chức, cá nhân ở nước ngoài như sau: thi đấu thể 
thao, biểu diễn nghệ thuật, văn hóa, giải trí, hội nghị, khách sạn, đào tạo, quảng cáo, du lịch lữ 
hành; dịch vụ cung cấp gắn với việc bán, phân phối, tiêu thụ sản phẩm, hàng hóa tại Việt Nam; 
dịch vụ thanh toán không dùng tiền mặt. 
l) Các dịch vụ do cơ sở kinh doanh cung cấp cho tổ chức, cá nhân ở trong khu phi thuế quan bao 
gồm: cho thuê nhà, hội trường, văn phòng, khách sạn, kho bãi; dịch vụ vận chuyển đưa đón 
người lao động; dịch vụ ăn uống (trừ dịch vụ cung cấp suất ăn công nghiệp, dịch vụ ăn uống 
trong khu phi thuế quan). 
5. Hàng hóa, dịch vụ bán, cung cấp cho tổ chức trong khu phi thuế quan và được tiêu dùng trong 
khu phi thuế quan phục vụ trực tiếp cho hoạt động sản xuất xuất khẩu quy định tại khoản 1, 
khoản 2 Điều này là hàng hóa, dịch vụ được tiêu dùng trong khu phi thuế quan phục vụ cho hoạt 
động sản xuất xuất khẩu của tổ chức trong khu phi thuế quan và không phục vụ cho hoạt động 
khác không phải hoạt động sản xuất xuất khẩu, trừ các hàng hóa, dịch vụ quy định tại khoản 4 
Điều này. 
6. Bộ Tài chính quy định chi tiết Điều này trong trường hợp cần thiết để thực hiện chức năng 
quản lý nhà nước.

[RULES]
{"id": "TAX-05-D17-000", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad"], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 17 khoản 1", "exception_to": "", "quote": "Mức thuế suất 0% áp dụng đối với hàng hóa, dịch vụ quy định tại khoản 1 Điều 9 Luật Thuế giá trị gia tăng."}
{"id": "TAX-05-D17-001", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad", "~is_selling_goods_or_services_in_domestic"], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 17 khoản 1 điểm a", "exception_to": "", "quote": "Hàng hóa xuất khẩu bao gồm: Hàng hóa từ Việt Nam bán cho tổ chức, cá nhân ở nước ngoài và được tiêu dùng ở ngoài Việt Nam."}
{"id": "TAX-05-D17-002", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad", "~is_selling_goods_or_services_in_domestic"], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 17 khoản 1 điểm b", "exception_to": "", "quote": "Hàng hóa từ nội địa Việt Nam bán cho tổ chức trong khu phi thuế quan và được tiêu dùng trong khu phi thuế quan phục vụ trực tiếp cho hoạt động sản xuất xuất khẩu."}
{"id": "TAX-05-D17-003", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad", "~is_selling_goods_or_services_in_domestic"], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 17 khoản 1 điểm c", "exception_to": "", "quote": "Hàng hóa đã bán tại khu vực cách ly cho cá nhân (người nước ngoài hoặc người Việt Nam) đã làm thủ tục xuất cảnh; hàng hóa đã bán tại cửa hàng miễn thuế."}
{"id": "TAX-05-D17-004", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad"], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 17 khoản 2", "exception_to": "", "quote": "Dịch vụ xuất khẩu bao gồm: Dịch vụ cung cấp trực tiếp cho tổ chức, cá nhân ở nước ngoài và được tiêu dùng ở ngoài Việt Nam."}
{"id": "TAX-05-D17-005", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad"], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 17 khoản 2 điểm a", "exception_to": "", "quote": "Dịch vụ cung cấp trực tiếp cho tổ chức, cá nhân ở nước ngoài và được tiêu dùng ở ngoài Việt Nam."}
{"id": "TAX-05-D17-006", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad"], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 17 khoản 2 điểm b", "exception_to": "", "quote": "Dịch vụ cung cấp trực tiếp cho tổ chức ở trong khu phi thuế quan và được tiêu dùng trong khu phi thuế quan phục vụ trực tiếp cho hoạt động sản xuất xuất khẩu."}
{"id": "TAX-05-D17-007", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad"], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 17 khoản 3", "exception_to": "", "quote": "Hàng hóa, dịch vụ xuất khẩu khác bao gồm: vận tải quốc tế; dịch vụ cho thuê phương tiện vận tải được sử dụng ngoài phạm vi lãnh thổ Việt Nam."}
{"id": "TAX-05-D17-008", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad"], "conclusion": "must_use_e_invoice_for_exported_goods_or_services", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 17 khoản 4", "exception_to": "khoản 4 Điều 9", "quote": "Các trường hợp không áp dụng thuế suất 0% quy định tại điểm b và d khoản 1 Điều 9 Luật Thuế giá trị gia tăng bao gồm: Chuyển giao công nghệ, chuyển nhượng quyền sở hữu trí tuệ ra nước ngoài."}
{"id": "TAX-05-D17-100", "type": "condition", "premises": [], "conclusion": "government_regulates_tax_management_details", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 17 khoản 6", "exception_to": "", "quote": "Bộ Tài chính quy định chi tiết Điều này trong trường hợp cần thiết để thực hiện chức năng quản lý nhà nước."}


######## 05_nghi_dinh_181_2025_ND-CP — Điều 18. Điều kiện áp dụng thuế suất 0%
[NGUYÊN VĂN]
Điều 18. Điều kiện áp dụng thuế suất 0% 
Hàng hóa, dịch vụ xuất khẩu áp dụng thuế suất 0% quy định tại Điều 17 Nghị định này (trừ một 
số trường hợp đặc thù quy định tại Điều 27, Điều 28 Nghị định này) phải đáp ứng quy định sau: 
1. Đối với hàng hóa xuất khẩu, phải có: 
a) Hợp đồng bán, gia công hàng hóa xuất khẩu (đối với trường hợp bán, gia công); hợp đồng ủy 
thác xuất khẩu (đối với trường hợp ủy thác xuất khẩu). 
b) Chứng từ thanh toán không dùng tiền mặt đối với hàng hóa xuất khẩu. 
c) Tờ khai hải quan theo quy định. 
2. Đối với dịch vụ xuất khẩu, trừ quy định tại khoản 3, 4, 5 Điều này, phải có: 
a) Hợp đồng cung cấp dịch vụ với tổ chức, cá nhân ở nước ngoài hoặc ở trong khu phi thuế quan. 
b) Chứng từ thanh toán không dùng tiền mặt đối với dịch vụ xuất khẩu. 
3. Đối với vận tải quốc tế, phải có: 
a) Hợp đồng vận chuyển hành khách, hành lý, hàng hóa giữa người vận chuyển và người thuê 
vận chuyển theo chặng quốc tế từ Việt Nam ra nước ngoài hoặc từ nước ngoài đến Việt Nam 
hoặc cả điểm đi và điểm đến ở nước ngoài theo các hình thức phù hợp với quy định của pháp 
luật. Đối với vận chuyển hành khách, hợp đồng vận chuyển là vé. Cơ sở kinh doanh vận tải quốc 
tế thực hiện theo các quy định của pháp luật về vận tải. 
b) Chứng từ thanh toán không dùng tiền mặt. Đối với trường hợp vận chuyển hành khách là cá 
nhân, có chứng từ thanh toán trực tiếp. 
4. Đối với dịch vụ của ngành hàng không, phải có: 
a) Hợp đồng cung cấp dịch vụ với tổ chức ở nước ngoài, hãng hàng không nước ngoài hoặc yêu 
cầu cung cấp dịch vụ của tổ chức ở nước ngoài, hãng hàng không nước ngoài. 
b) Chứng từ thanh toán không dùng tiền mặt. Trường hợp các dịch vụ cung cấp cho tổ chức nước 
ngoài, hãng hàng không nước ngoài phát sinh không thường xuyên, không theo lịch trình và 
không có hợp đồng, phải có chứng từ thanh toán trực tiếp của tổ chức nước ngoài, hãng hàng 
không nước ngoài. 
Các quy định về hợp đồng và chứng từ thanh toán nêu tại khoản này không áp dụng đối với dịch 
vụ phục vụ hành khách đi chuyến bay quốc tế từ cảng hàng không Việt Nam (passenger service 
charges). 
Riêng đối với dịch vụ sửa chữa tàu bay cung cấp cho tổ chức, cá nhân nước ngoài, để được áp 
dụng thuế suất 0%, tàu bay đưa vào Việt Nam phải làm thủ tục tạm nhập khẩu, tái xuất khẩu theo 
quy định. 
5. Đối với dịch vụ của ngành hàng hải, phải có: 
a) Hợp đồng cung cấp dịch vụ với tổ chức ở nước ngoài, người đại lý tàu biển hoặc yêu cầu cung 
cấp dịch vụ của tổ chức ở nước ngoài hoặc người đại lý tàu biển. 
b) Chứng từ thanh toán không dùng tiền mặt của tổ chức ở nước ngoài hoặc có chứng từ thanh 
toán không dùng tiền mặt của người đại lý tàu biển cho cơ sở kinh doanh cung cấp dịch vụ. 
Riêng đối với dịch vụ sửa chữa tàu biển cung cấp cho tổ chức, cá nhân nước ngoài, để được áp 
dụng thuế suất 0%, tàu biển đưa vào Việt Nam phải làm thủ tục tạm nhập khẩu, tái xuất khẩu 
theo quy định.

[RULES]
{"id": "TAX-05-D18-000", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad", "must_have_export_contract"], "conclusion": "must_use_e_invoice_for_exported_goods", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 18 khoản 1 điểm a", "exception_to": "", "quote": "Hàng hóa, dịch vụ xuất khẩu áp dụng thuế suất 0% phải có hợp đồng bán, gia công hàng hóa xuất khẩu."}
{"id": "TAX-05-D18-001", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad", "must_use_non_cash_payment_receipt"], "conclusion": "must_use_e_invoice_for_exported_goods", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 18 khoản 1 điểm b", "exception_to": "", "quote": "Hàng hóa, dịch vụ xuất khẩu áp dụng thuế suất 0% phải có chứng từ thanh toán không dùng tiền mặt."}
{"id": "TAX-05-D18-002", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad", "must_use_invoice_from_tax_authority"], "conclusion": "must_use_e_invoice_for_exported_goods", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 18 khoản 1 điểm c", "exception_to": "", "quote": "Hàng hóa, dịch vụ xuất khẩu áp dụng thuế suất 0% phải có tờ khai hải quan theo quy định."}
{"id": "TAX-05-D18-003", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad", "must_have_service_contract_with_foreign_entity"], "conclusion": "must_use_e_invoice_for_exported_goods", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 18 khoản 2 điểm a", "exception_to": "", "quote": "Dịch vụ xuất khẩu phải có hợp đồng cung cấp dịch vụ với tổ chức, cá nhân ở nước ngoài."}
{"id": "TAX-05-D18-004", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad", "must_use_non_cash_payment_receipt"], "conclusion": "must_use_e_invoice_for_exported_goods", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 18 khoản 2 điểm b", "exception_to": "", "quote": "Dịch vụ xuất khẩu phải có chứng từ thanh toán không dùng tiền mặt."}
{"id": "TAX-05-D18-005", "type": "condition", "premises": ["is_international_transport_activity", "must_have_transport_contract"], "conclusion": "must_use_e_invoice_for_exported_goods", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 18 khoản 3 điểm a", "exception_to": "", "quote": "Đối với vận tải quốc tế, phải có hợp đồng vận chuyển hành khách, hành lý, hàng hóa."}
{"id": "TAX-05-D18-006", "type": "condition", "premises": ["is_international_transport_activity", "must_use_non_cash_payment_receipt"], "conclusion": "must_use_e_invoice_for_exported_goods", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 18 khoản 3 điểm b", "exception_to": "", "quote": "Đối với vận tải quốc tế, phải có chứng từ thanh toán không dùng tiền mặt."}
{"id": "TAX-05-D18-007", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad", "must_have_service_contract_with_foreign_airline"], "conclusion": "must_use_e_invoice_for_exported_goods", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 18 khoản 4 điểm a", "exception_to": "", "quote": "Đối với dịch vụ của ngành hàng không, phải có hợp đồng cung cấp dịch vụ với tổ chức ở nước ngoài."}
{"id": "TAX-05-D18-008", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad", "must_use_non_cash_payment_receipt"], "conclusion": "must_use_e_invoice_for_exported_goods", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 18 khoản 4 điểm b", "exception_to": "", "quote": "Đối với dịch vụ của ngành hàng không, phải có chứng từ thanh toán không dùng tiền mặt."}
{"id": "TAX-05-D18-009", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad", "must_have_service_contract_with_foreign_shipping_agent"], "conclusion": "must_use_e_invoice_for_exported_goods", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 18 khoản 5 điểm a", "exception_to": "", "quote": "Đối với dịch vụ của ngành hàng hải, phải có hợp đồng cung cấp dịch vụ với tổ chức ở nước ngoài."}
{"id": "TAX-05-D18-010", "type": "condition", "premises": ["is_exporting_goods_or_services_abroad", "must_use_non_cash_payment_receipt"], "conclusion": "must_use_e_invoice_for_exported_goods", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 18 khoản 5 điểm b", "exception_to": "", "quote": "Đối với dịch vụ của ngành hàng hải, phải có chứng từ thanh toán không dùng tiền mặt."}


######## 05_nghi_dinh_181_2025_ND-CP — Điều 26. Chứng từ thanh toán không dùng tiền mặt
[NGUYÊN VĂN]
Điều 26. Chứng từ thanh toán không dùng tiền mặt 
Cơ sở kinh doanh phải có chứng từ thanh toán không dùng tiền mặt đối với hàng hóa, dịch vụ 
mua vào (bao gồm cả hàng hóa nhập khẩu) từ 05 triệu đồng trở lên đã bao gồm thuế giá trị gia 
tăng. Trong đó: 
1. Chứng từ thanh toán không dùng tiền mặt là chứng từ chứng minh việc thanh toán không dùng 
tiền mặt theo quy định của Nghị định số 52/2024/NĐ-CP ngày 15 tháng 5 năm 2024 của Chính 
phủ về thanh toán không dùng tiền mặt, trừ các chứng từ bên mua nộp tiền mặt vào tài khoản của 
bên bán. 
2. Một số trường hợp đặc thù theo quy định tại điểm b khoản 2 Điều 14 Luật Thuế giá trị gia 
tăng bao gồm: 
a) Trường hợp hàng hóa, dịch vụ mua vào theo phương thức thanh toán bù trừ giữa giá trị hàng 
hóa, dịch vụ mua vào với giá trị hàng hóa, dịch vụ bán ra, vay mượn hàng mà phương thức thanh 
toán này được quy định cụ thể trong hợp đồng thì phải có biên bản đối chiếu số liệu và xác nhận 
giữa hai bên về việc thanh toán bù trừ giữa hàng hóa, dịch vụ mua vào với hàng hóa, dịch vụ bán 
ra, vay mượn hàng. Trường hợp bù trừ công nợ qua bên thứ ba phải có biên bản bù trừ công nợ 
của ba bên làm căn cứ khấu trừ thuế. 
b) Trường hợp hàng hóa, dịch vụ mua vào theo phương thức bù trừ công nợ như vay, mượn tiền; 
cấn trừ công nợ qua bên thứ ba mà phương thức thanh toán này được quy định cụ thể trong hợp 
đồng thì phải có hợp đồng vay, mượn tiền dưới hình thức văn bản được lập trước đó và có chứng 
từ chuyển tiền từ tài khoản của bên cho vay, cho mượn sang tài khoản của bên đi vay, đi mượn 
đối với khoản vay, mượn bằng tiền bao gồm cả trường hợp bù trừ giữa giá trị hàng hóa, dịch vụ 
mua vào với khoản tiền mà bên bán hỗ trợ cho bên mua, hoặc nhờ bên mua chi hộ. 
c) Trường hợp hàng hóa, dịch vụ mua vào được thanh toán ủy quyền qua bên thứ ba thanh toán 
không dùng tiền mặt (bao gồm cả trường hợp bên bán yêu cầu bên mua thanh toán không dùng 
tiền mặt cho bên thứ ba do bên bán chỉ định) thì việc thanh toán theo ủy quyền hoặc thanh toán 
cho bên thứ ba theo chỉ định của bên bán phải được quy định cụ thể trong hợp đồng dưới hình 
thức văn bản và bên thứ ba là một tổ chức hoặc thể nhân đang hoạt động theo quy định của pháp 
luật. 
d) Trường hợp hàng hóa, dịch vụ mua vào theo phương thức thanh toán tiền hàng hóa, dịch vụ 
bằng cổ phiếu, trái phiếu mà phương thức thanh toán này được quy định cụ thể trong hợp đồng 
thì phải có hợp đồng mua bán dưới hình thức văn bản được lập trước đó. 
đ) Trường hợp sau khi thực hiện các hình thức thanh toán nêu tại điểm a, b, c và d khoản này mà 
phần giá trị còn lại được thanh toán bằng tiền có giá trị từ 05 triệu đồng trở lên thì chỉ được khấu 
trừ thuế đối với trường hợp có chứng từ thanh toán không dùng tiền mặt. 
e) Trường hợp hàng hóa, dịch vụ mua vào được thanh toán không dùng tiền mặt vào tài khoản 
của bên thứ ba mở tại Kho bạc Nhà nước để thực hiện cưỡng chế bằng biện pháp thu tiền, tài sản 
do tổ chức, cá nhân khác đang nắm giữ (theo Quyết định của cơ quan nhà nước có thẩm quyền) 
thì được khấu trừ thuế giá trị gia tăng đầu vào xác định tương ứng với số tiền chuyển vào tài 
khoản của bên thứ ba mở tại Kho bạc Nhà nước. 
g) Đối với hàng hóa, dịch vụ mua trả chậm, trả góp có giá trị hàng hóa, dịch vụ mua từ 05 triệu 
đồng trở lên, cơ sở kinh doanh căn cứ vào hợp đồng mua hàng hóa, dịch vụ bằng văn bản, hóa 
đơn giá trị gia tăng và chứng từ thanh toán không dùng tiền mặt của hàng hóa, dịch vụ mua trả 
chậm, trả góp để khấu trừ thuế giá trị gia tăng đầu vào. Trường hợp chưa có chứng từ thanh toán 
không dùng tiền mặt do chưa đến thời điểm thanh toán theo hợp đồng, phụ lục hợp đồng thì cơ 
sở kinh doanh vẫn được khấu trừ thuế giá trị gia tăng đầu vào. Trường hợp đến thời điểm thanh 
toán theo hợp đồng, phụ lục hợp đồng, cơ sở kinh doanh không có chứng từ thanh toán không 
dùng tiền mặt thì cơ sở kinh doanh phải kê khai, điều chỉnh giảm số thuế giá trị gia tăng đầu vào 
được khấu trừ đối với phần giá trị hàng hóa, dịch vụ không có chứng từ thanh toán không dùng 
tiền mặt vào kỳ tính thuế phát sinh nghĩa vụ thanh toán theo hợp đồng, phụ lục hợp đồng. 
h) Trường hợp giá trị hàng hóa, dịch vụ nhập khẩu từng lần có giá trị dưới 05 triệu đồng, hàng 
hóa, dịch vụ mua vào từng lần theo hóa đơn dưới 05 triệu đồng theo giá đã có thuế giá trị gia 
tăng và trường hợp cơ sở kinh doanh nhập khẩu hàng hóa là quà biếu, quà tặng, hàng mẫu không 
phải trả tiền của tổ chức, cá nhân ở nước ngoài thì không cần chứng từ thanh toán không dùng 
tiền mặt đối với hàng hóa, dịch vụ mua vào. 
i) Trường hợp hàng hóa, dịch vụ mua vào phục vụ cho hoạt động sản xuất, kinh doanh hàng hóa, 
dịch vụ chịu thuế giá trị gia tăng được ủy quyền cho cá nhân là người lao động của cơ sở kinh 
doanh thanh toán không dùng tiền mặt theo quy chế tài chính hoặc quy chế nội bộ của cơ sở kinh 
doanh, sau đó cơ sở kinh doanh thanh toán lại cho người lao động bằng hình thức thanh toán 
không dùng tiền mặt thì được khấu trừ thuế giá trị gia tăng đầu vào. 
3. Trường hợp mua hàng hóa, dịch vụ của một người nộp thuế có giá trị dưới 05 triệu đồng 
nhưng mua nhiều lần trong cùng một ngày có tổng giá trị từ 05 triệu đồng trở lên thì chỉ được 
khấu trừ thuế đối với trường hợp có chứng từ thanh toán không dùng tiền mặt.

[RULES]
{"id": "TAX-05-D26-000", "type": "condition", "premises": ["must_use_non_cash_payment_receipt", "total_value_at_least_5_million"], "conclusion": "must_have_invoice_for_deduction", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 26 khoản 1", "exception_to": "", "quote": "Cơ sở kinh doanh phải có chứng từ thanh toán không dùng tiền mặt đối với hàng hóa, dịch vụ mua vào từ 05 triệu đồng trở lên."}
{"id": "TAX-05-D26-001", "type": "condition", "premises": ["must_use_non_cash_payment_receipt", "payment_method_is_offset"], "conclusion": "must_have_invoice_for_deduction", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 26 khoản 2 điểm a", "exception_to": "", "quote": "Trường hợp hàng hóa, dịch vụ mua vào theo phương thức thanh toán bù trừ... thì phải có biên bản đối chiếu số liệu."}
{"id": "TAX-05-D26-002", "type": "condition", "premises": ["must_use_non_cash_payment_receipt", "payment_method_is_debt_offset"], "conclusion": "must_have_invoice_for_deduction", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 26 khoản 2 điểm b", "exception_to": "", "quote": "Trường hợp hàng hóa, dịch vụ mua vào theo phương thức bù trừ công nợ như vay, mượn tiền... thì phải có hợp đồng vay, mượn tiền."}
{"id": "TAX-05-D26-003", "type": "condition", "premises": ["must_use_non_cash_payment_receipt", "payment_method_is_third_party_authorization"], "conclusion": "must_have_invoice_for_deduction", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 26 khoản 2 điểm c", "exception_to": "", "quote": "Trường hợp hàng hóa, dịch vụ mua vào được thanh toán ủy quyền qua bên thứ ba thanh toán không dùng tiền mặt... thì việc thanh toán theo ủy quyền... phải được quy định cụ thể trong hợp đồng."}
{"id": "TAX-05-D26-004", "type": "condition", "premises": ["must_use_non_cash_payment_receipt", "payment_method_is_equity"], "conclusion": "must_have_invoice_for_deduction", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 26 khoản 2 điểm d", "exception_to": "", "quote": "Trường hợp hàng hóa, dịch vụ mua vào theo phương thức thanh toán tiền hàng hóa, dịch vụ bằng cổ phiếu, trái phiếu... thì phải có hợp đồng mua bán."}
{"id": "TAX-05-D26-005", "type": "condition", "premises": ["must_use_non_cash_payment_receipt", "remaining_value_at_least_5_million"], "conclusion": "must_have_invoice_for_deduction", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 26 khoản 2 điểm đ", "exception_to": "", "quote": "Trường hợp sau khi thực hiện các hình thức thanh toán... mà phần giá trị còn lại được thanh toán bằng tiền có giá trị từ 05 triệu đồng trở lên thì chỉ được khấu trừ thuế đối với trường hợp có chứng từ thanh toán không dùng tiền mặt."}
{"id": "TAX-05-D26-006", "type": "condition", "premises": ["must_use_non_cash_payment_receipt", "payment_to_third_party_account"], "conclusion": "must_have_invoice_for_deduction", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 26 khoản 2 điểm e", "exception_to": "", "quote": "Trường hợp hàng hóa, dịch vụ mua vào được thanh toán không dùng tiền mặt vào tài khoản của bên thứ ba mở tại Kho bạc Nhà nước... thì được khấu trừ thuế giá trị gia tăng đầu vào."}
{"id": "TAX-05-D26-007", "type": "condition", "premises": ["must_use_non_cash_payment_receipt", "payment_method_is_installment"], "conclusion": "must_have_invoice_for_deduction", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 26 khoản 2 điểm g", "exception_to": "", "quote": "Đối với hàng hóa, dịch vụ mua trả chậm, trả góp có giá trị hàng hóa, dịch vụ mua từ 05 triệu đồng trở lên... cơ sở kinh doanh vẫn được khấu trừ thuế giá trị gia tăng đầu vào."}
{"id": "TAX-05-D26-008", "type": "condition", "premises": ["total_value_below_5_million"], "conclusion": "must_not_use_non_cash_payment_receipt", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 26 khoản 2 điểm h", "exception_to": "", "quote": "Trường hợp giá trị hàng hóa, dịch vụ nhập khẩu từng lần có giá trị dưới 05 triệu đồng... thì không cần chứng từ thanh toán không dùng tiền mặt."}
{"id": "TAX-05-D26-009", "type": "condition", "premises": ["must_use_non_cash_payment_receipt", "multiple_purchases_same_day_total_at_least_5_million"], "conclusion": "must_have_invoice_for_deduction", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 26 khoản 3", "exception_to": "", "quote": "Trường hợp mua hàng hóa, dịch vụ của một người nộp thuế có giá trị dưới 05 triệu đồng nhưng mua nhiều lần trong cùng một ngày có tổng giá trị từ 05 triệu đồng trở lên thì chỉ được khấu trừ thuế đối với trường hợp có chứng từ thanh toán không dùng tiền mặt."}


######## 05_nghi_dinh_181_2025_ND-CP — Điều 9. Giá tính thuế đối với hoạt động đại lý, môi giới mua bán hàng hóa, dịch vụ hưởng
[NGUYÊN VĂN]
Điều 9. Giá tính thuế đối với hoạt động đại lý, môi giới mua bán hàng hóa, dịch vụ hưởng 
hoa hồng và hàng hóa, dịch vụ được sử dụng hóa đơn thanh toán ghi giá thanh toán 
1. Đối với hoạt động đại lý, môi giới mua bán hàng hóa và dịch vụ hưởng hoa hồng là tiền hoa 
hồng thu được từ các hoạt động này chưa có thuế giá trị gia tăng, trừ trường hợp không phải tính 
thuế giá trị gia tăng gồm: 
a) Doanh thu hàng hóa, dịch vụ nhận bán đại lý và doanh thu hoa hồng được hưởng từ hoạt động 
đại lý bán đúng giá quy định của bên giao đại lý hưởng hoa hồng của dịch vụ: bưu chính, viễn 
thông, bán vé xổ số, vé máy bay, ô tô, tàu hỏa, tàu thủy; đại lý vận tải quốc tế; đại lý của các dịch 
vụ ngành hàng không, hàng hải mà được áp dụng thuế suất thuế giá trị gia tăng 0%; đại lý bán 
bảo hiểm. 
b) Doanh thu hàng hóa, dịch vụ và doanh thu hoa hồng đại lý được hưởng từ hoạt động đại lý 
bán hàng hóa, dịch vụ thuộc diện không chịu thuế giá trị gia tăng. 
2. Đối với hàng hóa, dịch vụ được sử dụng hóa đơn thanh toán ghi giá thanh toán là giá đã có 
thuế giá trị gia tăng thì giá tính thuế được xác định theo công thức sau: 
Giá chưa có thuế giá trị gia tăng 
= 
Giá thanh toán 
1 + thuế suất của hàng hóa, dịch vụ (%)

[RULES]
{"id": "TAX-05-D9-000", "type": "condition", "premises": ["is_business_in_postal_services", "~goods_subject_to_vat"], "conclusion": "must_use_commission_excluding_vat", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 9 khoản 1 điểm a", "exception_to": "", "quote": "Doanh thu hàng hóa, dịch vụ nhận bán đại lý và doanh thu hoa hồng được hưởng từ hoạt động đại lý bán đúng giá quy định của bên giao đại lý hưởng hoa hồng của dịch vụ: bưu chính, viễn thông..."}
{"id": "TAX-05-D9-001", "type": "condition", "premises": ["is_business_in_air_transport", "~goods_subject_to_vat"], "conclusion": "must_use_commission_excluding_vat", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 9 khoản 1 điểm a", "exception_to": "", "quote": "Doanh thu hàng hóa, dịch vụ nhận bán đại lý và doanh thu hoa hồng được hưởng từ hoạt động đại lý bán đúng giá quy định của bên giao đại lý hưởng hoa hồng của dịch vụ: bưu chính, viễn thông..."}
{"id": "TAX-05-D9-002", "type": "condition", "premises": ["is_business_in_air_transport", "goods_subject_to_vat"], "conclusion": "must_use_price_excluding_vat", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 9 khoản 1 điểm a", "exception_to": "", "quote": "Doanh thu hàng hóa, dịch vụ nhận bán đại lý và doanh thu hoa hồng được hưởng từ hoạt động đại lý bán đúng giá quy định của bên giao đại lý hưởng hoa hồng của dịch vụ: bưu chính, viễn thông..."}
{"id": "TAX-05-D9-003", "type": "condition", "premises": ["~goods_subject_to_vat"], "conclusion": "must_use_commission_excluding_vat", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 9 khoản 1 điểm b", "exception_to": "", "quote": "Doanh thu hàng hóa, dịch vụ và doanh thu hoa hồng đại lý được hưởng từ hoạt động đại lý bán hàng hóa, dịch vụ thuộc diện không chịu thuế giá trị gia tăng."}
{"id": "TAX-05-D9-004", "type": "condition", "premises": ["must_include_total_amount_including_tax", "must_include_tax_rate"], "conclusion": "must_calculate_price_excluding_vat", "source": "05_nghi_dinh_181_2025_ND-CP, Điều 9 khoản 2", "exception_to": "", "quote": "Đối với hàng hóa, dịch vụ được sử dụng hóa đơn thanh toán ghi giá thanh toán là giá đã có thuế giá trị gia tăng thì giá tính thuế được xác định theo công thức sau..."}


######## 06_luat_TNDN_67_2025_QH15 — Điều 10. Thuế suất
[NGUYÊN VĂN]
Điều 10. Thuế suất 
1. Thuế suất thuế thu nhập doanh nghiệp là 20%, trừ trường hợp quy định tại các khoản 2, 3 và 4 
Điều này và đối tượng được ưu đãi về thuế suất quy định tại Điều 13 của Luật này. 
2. Thuế suất 15% áp dụng đối với doanh nghiệp có tổng doanh thu năm không quá 03 tỷ đồng. 
3. Thuế suất 17% áp dụng đối với doanh nghiệp có tổng doanh thu năm từ trên 03 tỷ đồng đến 
không quá 50 tỷ đồng. 
Doanh thu làm căn cứ xác định doanh nghiệp thuộc đối tượng được áp dụng thuế suất 15% và 
17% quy định tại khoản 2, khoản 3 Điều này là tổng doanh thu của kỳ tính thuế thu nhập doanh 
nghiệp trước liền kề. Việc xác định tổng doanh thu làm căn cứ áp dụng thực hiện theo quy định 
của Chính phủ. 
4. Thuế suất thuế thu nhập doanh nghiệp đối với một số trường hợp khác được quy định như sau: 
a) Đối với hoạt động tìm kiếm, thăm dò và khai thác dầu khí từ 25% đến 50%. Căn cứ vào vị trí, 
điều kiện khai thác và trữ lượng mỏ, Thủ tướng Chính phủ quyết định mức thuế suất cụ thể phù 
hợp với từng hợp đồng dầu khí; 
b) Đối với hoạt động thăm dò, khai thác tài nguyên quý hiếm (bao gồm: bạch kim, vàng, bạc, 
thiếc, wonfram, antimoan, đá quý, đất hiếm và tài nguyên quý hiếm khác theo quy định của pháp 
luật) là 50%. Trường hợp các mỏ có từ 70% diện tích được giao trở lên ở địa bàn có điều kiện 
kinh tế - xã hội đặc biệt khó khăn, thuế suất là 40%.

[RULES]
{"id": "TAX-06-D10-000", "type": "condition", "premises": [], "conclusion": "tax_rate_20_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 10 khoản 1", "exception_to": "", "quote": "Thuế suất thuế thu nhập doanh nghiệp là 20%"}
{"id": "TAX-06-D10-001", "type": "condition", "premises": ["total_revenue_previous_year_at_most_3_billion"], "conclusion": "tax_rate_15_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 10 khoản 2", "exception_to": "", "quote": "Thuế suất 15% áp dụng đối với doanh nghiệp có tổng doanh thu năm không quá 03 tỷ đồng"}
{"id": "TAX-06-D10-002", "type": "condition", "premises": ["total_revenue_previous_year_above_3_billion_and_at_most_50_billion"], "conclusion": "tax_rate_17_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 10 khoản 3", "exception_to": "", "quote": "Thuế suất 17% áp dụng đối với doanh nghiệp có tổng doanh thu năm từ trên 03 tỷ đồng đến không quá 50 tỷ đồng"}
{"id": "TAX-06-D10-003", "type": "condition", "premises": ["is_using_oil_exploration"], "conclusion": "tax_rate_oil_exploration", "source": "06_luat_TNDN_67_2025_QH15, Điều 10 khoản 4 điểm a", "exception_to": "Điều 13 của Luật này", "quote": "Đối với hoạt động tìm kiếm, thăm dò và khai thác dầu khí từ 25% đến 50%"}
{"id": "TAX-06-D10-004", "type": "condition", "premises": ["is_in_difficult_economic_area"], "conclusion": "tax_rate_40_percent_for_rare_resources", "source": "06_luat_TNDN_67_2025_QH15, Điều 10 khoản 4 điểm b", "exception_to": "", "quote": "Trường hợp các mỏ có từ 70% diện tích được giao trở lên ở địa bàn có điều kiện kinh tế - xã hội đặc biệt khó khăn, thuế suất là 40%"}
{"id": "TAX-06-D10-005", "type": "condition", "premises": [], "conclusion": "tax_rate_50_percent_for_rare_resources", "source": "06_luat_TNDN_67_2025_QH15, Điều 10 khoản 4 điểm b", "exception_to": "", "quote": "Đối với hoạt động thăm dò, khai thác tài nguyên quý hiếm là 50%"}


######## 06_luat_TNDN_67_2025_QH15 — Điều 13. Thuế suất ưu đãi
[NGUYÊN VĂN]
Điều 13. Thuế suất ưu đãi 
1. Áp dụng thuế suất 10% trong 15 năm đối với: 
a) Thu nhập của doanh nghiệp từ thực hiện dự án đầu tư mới quy định tại các điểm a, b, c, d và đ 
khoản 2 Điều 12 của Luật này; thu nhập của doanh nghiệp quy định tại điểm e khoản 2 Điều 12 
của Luật này; 
b) Thu nhập của doanh nghiệp từ thực hiện dự án đầu tư quy định tại điểm g, điểm h khoản 2 
Điều 12 của Luật này; 
c) Thu nhập của doanh nghiệp từ thực hiện dự án đầu tư mới thuộc địa bàn quy định tại điểm a 
khoản 3 Điều 12 của Luật này; 
d) Thu nhập của doanh nghiệp từ thực hiện dự án đầu tư mới tại khu công nghệ cao, khu nông 
nghiệp ứng dụng công nghệ cao, khu công nghệ số tập trung; dự án đầu tư mới tại khu kinh tế 
nằm trên địa bàn ưu đãi thuế quy định tại điểm a, điểm b khoản 3 Điều 12 của Luật này. Trường 
hợp dự án đầu tư tại khu kinh tế mà vị trí thực hiện dự án nằm trên cả địa bàn thuộc địa bàn ưu 
đãi thuế và địa bàn không thuộc địa bàn ưu đãi thuế thì việc xác định ưu đãi thuế của dự án do 
Chính phủ quy định. 
2. Áp dụng thuế suất 10% đối với: 
a) Thu nhập của doanh nghiệp từ hoạt động thuộc ngành, nghề quy định tại điểm k, điểm l khoản 
2 Điều 12 của Luật này tại địa bàn ưu đãi thuế quy định tại điểm b khoản 3 Điều 12 của Luật 
này; 
b) Thu nhập của doanh nghiệp từ hoạt động thuộc ngành, nghề quy định tại các điểm i, r và s 
khoản 2 Điều 12 của Luật này; 
c) Thu nhập của nhà xuất bản từ hoạt động thuộc ngành, nghề quy định tại điểm t khoản 2 Điều 
12 của Luật này; 
d) Thu nhập của hợp tác xã, liên hiệp hợp tác xã quy định tại điểm q khoản 2 Điều 12 của Luật 
này không thuộc địa bàn quy định tại khoản 3 Điều 12 của Luật này; 
đ) Thu nhập của cơ quan báo chí thuộc ngành, nghề quy định tại điểm u khoản 2 Điều 12 của 
Luật này. 
3. Áp dụng thuế suất 15% đối với thu nhập của doanh nghiệp từ hoạt động thuộc ngành, nghề 
quy định tại điểm l khoản 2 Điều 12 của Luật này không thuộc địa bàn quy định tại khoản 3 Điều 
12 của Luật này. 
4. Áp dụng thuế suất 17% trong thời gian 10 năm đối với: 
a) Dự án đầu tư mới thuộc ngành, nghề ưu đãi quy định tại các điểm m, n và o khoản 2 Điều 12 
của Luật này; 
b) Dự án đầu tư mới thực hiện tại địa bàn quy định tại điểm b khoản 3 Điều 12 của Luật này; 
c) Dự án đầu tư mới tại khu kinh tế không nằm trên địa bàn quy định tại điểm a, điểm b khoản 3 
Điều 12 của Luật này. 
5. Áp dụng thuế suất 17% đối với thu nhập của doanh nghiệp tại điểm p khoản 2 Điều 12 của 
Luật này. 
6. Việc kéo dài thời gian và áp dụng thuế suất ưu đãi được quy định như sau: 
a) Thủ tướng Chính phủ quyết định việc kéo dài thêm thời gian áp dụng thuế suất ưu đãi tối đa 
không quá 15 năm đối với các dự án sau đây: 
a1) Dự án đầu tư mới quy định tại các điểm a, b, d và đ khoản 2 Điều 12 của Luật này, có quy 
mô vốn đầu tư tối thiểu 6.000 tỷ đồng, có ảnh hưởng lớn về kinh tế - xã hội cần đặc biệt khuyến 
khích; 
a2) Dự án đầu tư quy định tại điểm g khoản 2 Điều 12 của Luật này đáp ứng một trong các tiêu 
chí sau đây: 
- Sản xuất sản phẩm hàng hóa có khả năng cạnh tranh toàn cầu, doanh thu đạt trên 20.000 tỷ 
đồng/năm chậm nhất sau 05 năm kể từ khi có doanh thu từ dự án đầu tư; 
- Sử dụng thường xuyên trên 6.000 lao động được xác định theo quy định của pháp luật về lao 
động; 
- Dự án đầu tư thuộc lĩnh vực hạ tầng kinh tế kỹ thuật, bao gồm: Đầu tư phát triển nhà máy nước, 
nhà máy điện, hệ thống cấp thoát nước, cầu, đường bộ, đường sắt, cảng hàng không, cảng biển, 
cảng sông, sân bay, nhà ga, năng lượng mới, năng lượng sạch, công nghiệp tiết kiệm năng lượng, 
dự án lọc hóa dầu; 
b) Đối với dự án đầu tư mới quy định tại điểm h khoản 2 Điều 12 của Luật này, Thủ tướng Chính 
phủ quyết định việc áp dụng thuế suất giảm không quá 50% mức thuế suất quy định tại khoản 1 
Điều này; thời gian áp dụng thuế suất ưu đãi không quá 1,5 lần so với thời gian áp dụng thuế suất 
ưu đãi quy định tại khoản 1 Điều này và được kéo dài thêm không quá 15 năm nhưng không 
vượt quá thời hạn của dự án đầu tư. 
7. Thời gian áp dụng thuế suất ưu đãi đối với thu nhập từ thực hiện dự án đầu tư mới của doanh 
nghiệp quy định tại Điều này (bao gồm cả dự án quy định tại điểm g khoản 2 Điều 12 của Luật 
này) được tính từ năm đầu tiên dự án đầu tư mới của doanh nghiệp có doanh thu. 
Trường hợp doanh nghiệp được cấp Giấy chứng nhận doanh nghiệp công nghệ cao, Giấy chứng 
nhận doanh nghiệp nông nghiệp ứng dụng công nghệ cao, Giấy chứng nhận doanh nghiệp khoa 
học và công nghệ, Giấy chứng nhận dự án ứng dụng công nghệ cao, Giấy xác nhận ưu đãi dự án 
sản xuất sản phẩm công nghiệp hỗ trợ sau thời điểm phát sinh doanh thu thì thời gian áp dụng 
thuế suất ưu đãi được tính kể từ năm được cấp Giấy chứng nhận, Giấy xác nhận ưu đãi.

[RULES]
{"id": "TAX-06-D13-000", "type": "condition", "premises": ["taxpayer_includes_legal_entities", "~is_in_special_economic_zone"], "conclusion": "tax_rate_10_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 1 điểm a", "exception_to": "", "quote": "Áp dụng thuế suất 10% trong 15 năm đối với: Thu nhập của doanh nghiệp từ thực hiện dự án đầu tư mới quy định tại các điểm a, b, c, d và đ khoản 2 Điều 12 của Luật này."}
{"id": "TAX-06-D13-001", "type": "condition", "premises": ["taxpayer_includes_legal_entities", "~is_in_special_economic_zone"], "conclusion": "tax_rate_10_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 1 điểm b", "exception_to": "", "quote": "Áp dụng thuế suất 10% trong 15 năm đối với: Thu nhập của doanh nghiệp từ thực hiện dự án đầu tư quy định tại điểm g, điểm h khoản 2 Điều 12 của Luật này."}
{"id": "TAX-06-D13-002", "type": "condition", "premises": ["taxpayer_includes_legal_entities", "~is_in_special_economic_zone"], "conclusion": "tax_rate_10_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 1 điểm c", "exception_to": "", "quote": "Áp dụng thuế suất 10% trong 15 năm đối với: Thu nhập của doanh nghiệp từ thực hiện dự án đầu tư mới thuộc địa bàn quy định tại điểm a khoản 3 Điều 12 của Luật này."}
{"id": "TAX-06-D13-003", "type": "condition", "premises": ["taxpayer_includes_legal_entities", "~is_in_special_economic_zone"], "conclusion": "tax_rate_10_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 1 điểm d", "exception_to": "", "quote": "Áp dụng thuế suất 10% trong 15 năm đối với: Thu nhập của doanh nghiệp từ thực hiện dự án đầu tư mới tại khu công nghệ cao, khu nông nghiệp ứng dụng công nghệ cao, khu công nghệ số tập trung."}
{"id": "TAX-06-D13-004", "type": "condition", "premises": ["taxpayer_includes_legal_entities", "is_in_special_economic_zone"], "conclusion": "tax_rate_10_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 2 điểm a", "exception_to": "", "quote": "Áp dụng thuế suất 10% đối với: Thu nhập của doanh nghiệp từ hoạt động thuộc ngành, nghề quy định tại điểm k, điểm l khoản 2 Điều 12 của Luật này tại địa bàn ưu đãi thuế quy định tại điểm b khoản 3 Điều 12 của Luật này."}
{"id": "TAX-06-D13-005", "type": "condition", "premises": ["taxpayer_includes_legal_entities"], "conclusion": "tax_rate_10_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 2 điểm b", "exception_to": "", "quote": "Áp dụng thuế suất 10% đối với: Thu nhập của doanh nghiệp từ hoạt động thuộc ngành, nghề quy định tại các điểm i, r và s khoản 2 Điều 12 của Luật này."}
{"id": "TAX-06-D13-006", "type": "condition", "premises": ["taxpayer_includes_legal_entities"], "conclusion": "tax_rate_10_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 2 điểm c", "exception_to": "", "quote": "Áp dụng thuế suất 10% đối với: Thu nhập của nhà xuất bản từ hoạt động thuộc ngành, nghề quy định tại điểm t khoản 2 Điều 12 của Luật này."}
{"id": "TAX-06-D13-007", "type": "condition", "premises": ["taxpayer_includes_legal_entities", "~is_in_special_economic_zone"], "conclusion": "tax_rate_10_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 2 điểm d", "exception_to": "", "quote": "Áp dụng thuế suất 10% đối với: Thu nhập của hợp tác xã, liên hiệp hợp tác xã quy định tại điểm q khoản 2 Điều 12 của Luật này không thuộc địa bàn quy định tại khoản 3 Điều 12 của Luật này."}
{"id": "TAX-06-D13-008", "type": "condition", "premises": ["taxpayer_includes_legal_entities"], "conclusion": "tax_rate_10_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 2 điểm đ", "exception_to": "", "quote": "Áp dụng thuế suất 10% đối với: Thu nhập của cơ quan báo chí thuộc ngành, nghề quy định tại điểm u khoản 2 Điều 12 của Luật này."}
{"id": "TAX-06-D13-009", "type": "condition", "premises": ["taxpayer_includes_legal_entities", "~is_in_special_economic_zone"], "conclusion": "tax_rate_15_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 3", "exception_to": "", "quote": "Áp dụng thuế suất 15% đối với thu nhập của doanh nghiệp từ hoạt động thuộc ngành, nghề quy định tại điểm l khoản 2 Điều 12 của Luật này không thuộc địa bàn quy định tại khoản 3 Điều 12 của Luật này."}
{"id": "TAX-06-D13-010", "type": "condition", "premises": ["taxpayer_includes_legal_entities"], "conclusion": "tax_rate_17_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 4 điểm a", "exception_to": "", "quote": "Áp dụng thuế suất 17% trong thời gian 10 năm đối với: Dự án đầu tư mới thuộc ngành, nghề ưu đãi quy định tại các điểm m, n và o khoản 2 Điều 12 của Luật này."}
{"id": "TAX-06-D13-011", "type": "condition", "premises": ["taxpayer_includes_legal_entities"], "conclusion": "tax_rate_17_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 4 điểm b", "exception_to": "", "quote": "Áp dụng thuế suất 17% trong thời gian 10 năm đối với: Dự án đầu tư mới thực hiện tại địa bàn quy định tại điểm b khoản 3 Điều 12 của Luật này."}
{"id": "TAX-06-D13-012", "type": "condition", "premises": ["taxpayer_includes_legal_entities"], "conclusion": "tax_rate_17_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 4 điểm c", "exception_to": "", "quote": "Áp dụng thuế suất 17% trong thời gian 10 năm đối với: Dự án đầu tư mới tại khu kinh tế không nằm trên địa bàn quy định tại điểm a, điểm b khoản 3 Điều 12 của Luật này."}
{"id": "TAX-06-D13-013", "type": "condition", "premises": ["taxpayer_includes_legal_entities"], "conclusion": "tax_rate_17_percent", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 5", "exception_to": "", "quote": "Áp dụng thuế suất 17% đối với thu nhập của doanh nghiệp tại điểm p khoản 2 Điều 12 của Luật này."}
{"id": "TAX-06-D13-014", "type": "condition", "premises": ["taxpayer_includes_legal_entities", "~total_revenue_previous_year_at_most_50_billion"], "conclusion": "tax_rate_extension", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 6 điểm a1", "exception_to": "", "quote": "Thủ tướng Chính phủ quyết định việc kéo dài thêm thời gian áp dụng thuế suất ưu đãi tối đa không quá 15 năm đối với các dự án sau đây: Dự án đầu tư mới quy định tại các điểm a, b, d và đ khoản 2 Điều 12 của Luật này, có quy mô vốn đầu tư tối thiểu 6.000 tỷ đồng."}
{"id": "TAX-06-D13-015", "type": "condition", "premises": ["taxpayer_includes_legal_entities"], "conclusion": "tax_rate_extension", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 6 điểm a2", "exception_to": "", "quote": "Thủ tướng Chính phủ quyết định việc kéo dài thêm thời gian áp dụng thuế suất ưu đãi tối đa không quá 15 năm đối với các dự án sau đây: Dự án đầu tư quy định tại điểm g khoản 2 Điều 12 của Luật này đáp ứng một trong các tiêu chí sau đây."}
{"id": "TAX-06-D13-016", "type": "condition", "premises": ["taxpayer_includes_legal_entities"], "conclusion": "tax_rate_start_year", "source": "06_luat_TNDN_67_2025_QH15, Điều 13 khoản 7", "exception_to": "", "quote": "Thời gian áp dụng thuế suất ưu đãi đối với thu nhập từ thực hiện dự án đầu tư mới của doanh nghiệp quy định tại Điều này được tính từ năm đầu tiên dự án đầu tư mới của doanh nghiệp có doanh thu."}
