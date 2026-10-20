

######## 08_luat_lao_dong_45_2019_QH14 — Điều 13. Hợp đồng lao động
[NGUYÊN VĂN]
Điều 13. Hợp đồng lao động 
1. Hợp đồng lao động là sự thỏa thuận giữa người lao động và người sử dụng lao động về việc 
làm có trả công, tiền lương, điều kiện lao động, quyền và nghĩa vụ của mỗi bên trong quan hệ lao 
động. 
Trường hợp hai bên thỏa thuận bằng tên gọi khác nhưng có nội dung thể hiện về việc làm có trả 
công, tiền lương và sự quản lý, điều hành, giám sát của một bên thì được coi là hợp đồng lao 
động. 
2. Trước khi nhận người lao động vào làm việc thì người sử dụng lao động phải giao kết hợp 
đồng lao động với người lao động.

[RULES]
{"id": "LAB-08-D13-000", "type": "condition", "premises": ["signed_labor_contract", "paid_wage", "under_management"], "conclusion": "labor_relation", "source": "08_luat_lao_dong_45_2019_QH14, Điều 13 khoản 1", "exception_to": "", "quote": "Hợp đồng lao động là sự thỏa thuận giữa người lao động và người sử dụng lao động về việc làm có trả công, tiền lương, điều kiện lao động, quyền và nghĩa vụ của mỗi bên trong quan hệ lao động."}
{"id": "LAB-08-D13-001", "type": "condition", "premises": ["signed_labor_contract", "paid_wage", "employer_involvement"], "conclusion": "labor_relation", "source": "08_luat_lao_dong_45_2019_QH14, Điều 13 khoản 1", "exception_to": "", "quote": "Trường hợp hai bên thỏa thuận bằng tên gọi khác nhưng có nội dung thể hiện về việc làm có trả công, tiền lương và sự quản lý, điều hành, giám sát của một bên thì được coi là hợp đồng lao động."}
{"id": "LAB-08-D13-002", "type": "condition", "premises": ["employer_involvement", "~signed_labor_contract"], "conclusion": "must_contribute_month", "source": "08_luat_lao_dong_45_2019_QH14, Điều 13 khoản 2", "exception_to": "", "quote": "Trước khi nhận người lao động vào làm việc thì người sử dụng lao động phải giao kết hợp đồng lao động với người lao động."}


######## 08_luat_lao_dong_45_2019_QH14 — Điều 149. Sử dụng người lao động cao tuổi
[NGUYÊN VĂN]
Điều 149. Sử dụng người lao động cao tuổi 
1. Khi sử dụng người lao động cao tuổi, hai bên có thể thỏa thuận giao kết nhiều lần hợp đồng 
lao động xác định thời hạn. 
2. Khi người lao động cao tuổi đang hưởng lương hưu theo quy định của Luật Bảo hiểm xã hội 
mà làm việc theo hợp đồng lao động mới thì ngoài quyền lợi đang hưởng theo chế độ hưu trí, 
người lao động cao tuổi được hưởng tiền lương và các quyền lợi khác theo quy định của pháp 
luật, hợp đồng lao động. 
3. Không được sử dụng người lao động cao tuổi làm nghề, công việc nặng nhọc, độc hại, nguy 
hiểm hoặc đặc biệt nặng nhọc, độc hại, nguy hiểm có ảnh hưởng xấu tới sức khỏe người lao động 
cao tuổi, trừ trường hợp bảo đảm các điều kiện làm việc an toàn. 
4. Người sử dụng lao động có trách nhiệm quan tâm chăm sóc sức khỏe của người lao động cao 
tuổi tại nơi làm việc. 
Mục 3. NGƯỜI LAO ĐỘNG VIỆT NAM ĐI LÀM VIỆC Ở NƯỚC NGOÀI, LAO ĐỘNG 
CHO CÁC TỔ CHỨC, CÁ NHÂN NƯỚC NGOÀI TẠI VIỆT NAM, LAO ĐỘNG LÀ 
NGƯỜI NƯỚC NGOÀI LÀM VIỆC TẠI VIỆT NAM

[RULES]
{"id": "LAB-08-D149-000", "type": "condition", "premises": ["retirement_age_at_signing", "new_contract_fixed_term"], "conclusion": "multiple_contracts", "source": "08_luat_lao_dong_45_2019_QH14, Điều 149 khoản 1", "exception_to": "", "quote": "Khi sử dụng người lao động cao tuổi, hai bên có thể thỏa thuận giao kết nhiều lần hợp đồng lao động xác định thời hạn."}
{"id": "LAB-08-D149-001", "type": "condition", "premises": ["receiving_pension", "new_contract_fixed_term"], "conclusion": "must_pay_wages_and_benefits", "source": "08_luat_lao_dong_45_2019_QH14, Điều 149 khoản 2", "exception_to": "", "quote": "Khi người lao động cao tuổi đang hưởng lương hưu theo quy định của Luật Bảo hiểm xã hội mà làm việc theo hợp đồng lao động mới thì ngoài quyền lợi đang hưởng theo chế độ hưu trí, người lao động cao tuổi được hưởng tiền lương và các quyền lợi khác theo quy định của pháp luật, hợp đồng lao động."}
{"id": "LAB-08-D149-002", "type": "condition", "premises": ["worker_heavy_dangerous_job"], "conclusion": "not_use_workers", "source": "08_luat_lao_dong_45_2019_QH14, Điều 149 khoản 3", "exception_to": "", "quote": "Không được sử dụng người lao động cao tuổi làm nghề, công việc nặng nhọc, độc hại, nguy hiểm hoặc đặc biệt nặng nhọc, độc hại, nguy hiểm có ảnh hưởng xấu tới sức khỏe người lao động cao tuổi, trừ trường hợp bảo đảm các điều kiện làm việc an toàn."}
{"id": "LAB-08-D149-003", "type": "condition", "premises": ["retirement_age_at_signing"], "conclusion": "must_provide_health_care", "source": "08_luat_lao_dong_45_2019_QH14, Điều 149 khoản 4", "exception_to": "", "quote": "Người sử dụng lao động có trách nhiệm quan tâm chăm sóc sức khỏe của người lao động cao tuổi tại nơi làm việc."}


######## 08_luat_lao_dong_45_2019_QH14 — Điều 20. Loại hợp đồng lao động
[NGUYÊN VĂN]
Điều 20. Loại hợp đồng lao động 
1. Hợp đồng lao động phải được giao kết theo một trong các loại sau đây: 
a) Hợp đồng lao động không xác định thời hạn là hợp đồng mà trong đó hai bên không xác định 
thời hạn, thời điểm chấm dứt hiệu lực của hợp đồng; 
b) Hợp đồng lao động xác định thời hạn là hợp đồng mà trong đó hai bên xác định thời hạn, thời 
điểm chấm dứt hiệu lực của hợp đồng trong thời gian không quá 36 tháng kể từ thời điểm có hiệu 
lực của hợp đồng. 
2. Khi hợp đồng lao động quy định tại điểm b khoản 1 Điều này hết hạn mà người lao động vẫn 
tiếp tục làm việc thì thực hiện như sau: 
a) Trong thời hạn 30 ngày kể từ ngày hợp đồng lao động hết hạn, hai bên phải ký kết hợp đồng 
lao động mới; trong thời gian chưa ký kết hợp đồng lao động mới thì quyền, nghĩa vụ và lợi ích 
của hai bên được thực hiện theo hợp đồng đã giao kết; 
b) Nếu hết thời hạn 30 ngày kể từ ngày hợp đồng lao động hết hạn mà hai bên không ký kết hợp 
đồng lao động mới thì hợp đồng đã giao kết theo quy định tại điểm b khoản 1 Điều này trở thành 
hợp đồng lao động không xác định thời hạn; 
c) Trường hợp hai bên ký kết hợp đồng lao động mới là hợp đồng lao động xác định thời hạn thì 
cũng chỉ được ký thêm 01 lần, sau đó nếu người lao động vẫn tiếp tục làm việc thì phải ký kết 
hợp đồng lao động không xác định thời hạn, trừ hợp đồng lao động đối với người được thuê làm 
giám đốc trong doanh nghiệp có vốn nhà nước và trường hợp quy định tại khoản 1 Điều 149, 
khoản 2 Điều 151 và khoản 4 Điều 177 của Bộ luật này.

[RULES]
{"id": "LAB-08-D20-000", "type": "condition", "premises": [], "conclusion": "contract_type_indefinite", "source": "08_luat_lao_dong_45_2019_QH14, Điều 20 khoản 1 điểm a", "exception_to": "", "quote": "Hợp đồng lao động không xác định thời hạn là hợp đồng mà trong đó hai bên không xác định thời hạn, thời điểm chấm dứt hiệu lực của hợp đồng."}
{"id": "LAB-08-D20-001", "type": "condition", "premises": [], "conclusion": "contract_type_fixed_term", "source": "08_luat_lao_dong_45_2019_QH14, Điều 20 khoản 1 điểm b", "exception_to": "", "quote": "Hợp đồng lao động xác định thời hạn là hợp đồng mà trong đó hai bên xác định thời hạn, thời điểm chấm dứt hiệu lực của hợp đồng trong thời gian không quá 36 tháng kể từ thời điểm có hiệu lực của hợp đồng."}
{"id": "LAB-08-D20-002", "type": "condition", "premises": ["contract_type_fixed_term", "worker_continue_working"], "conclusion": "must_sign_new_contract", "source": "08_luat_lao_dong_45_2019_QH14, Điều 20 khoản 2 điểm a", "exception_to": "", "quote": "Trong thời hạn 30 ngày kể từ ngày hợp đồng lao động hết hạn, hai bên phải ký kết hợp đồng lao động mới."}
{"id": "LAB-08-D20-003", "type": "condition", "premises": ["contract_type_fixed_term", "contract_expired", "no_new_contract_signed"], "conclusion": "contract_type_indefinite", "source": "08_luat_lao_dong_45_2019_QH14, Điều 20 khoản 2 điểm b", "exception_to": "", "quote": "Nếu hết thời hạn 30 ngày kể từ ngày hợp đồng lao động hết hạn mà hai bên không ký kết hợp đồng lao động mới thì hợp đồng đã giao kết theo quy định tại điểm b khoản 1 Điều này trở thành hợp đồng lao động không xác định thời hạn."}
{"id": "LAB-08-D20-004", "type": "condition", "premises": ["new_contract_fixed_term", "worker_continue_working"], "conclusion": "must_sign_indefinite_contract", "source": "08_luat_lao_dong_45_2019_QH14, Điều 20 khoản 2 điểm c", "exception_to": "khoản 1 Điều 149, khoản 2 Điều 151 và khoản 4 Điều 177", "quote": "Trường hợp hai bên ký kết hợp đồng lao động mới là hợp đồng lao động xác định thời hạn thì cũng chỉ được ký thêm 01 lần, sau đó nếu người lao động vẫn tiếp tục làm việc thì phải ký kết hợp đồng lao động không xác định thời hạn."}


######## 08_luat_lao_dong_45_2019_QH14 — Điều 30. Tạm hoãn thực hiện hợp đồng lao động
[NGUYÊN VĂN]
Điều 30. Tạm hoãn thực hiện hợp đồng lao động 
1. Các trường hợp tạm hoãn thực hiện hợp đồng lao động bao gồm: 
a) Người lao động thực hiện nghĩa vụ quân sự, nghĩa vụ tham gia Dân quân tự vệ; 
b) Người lao động bị tạm giữ, tạm giam theo quy định của pháp luật về tố tụng hình sự; 
c) Người lao động phải chấp hành quyết định áp dụng biện pháp đưa vào trường giáo dưỡng, cơ 
sở cai nghiện bắt buộc hoặc cơ sở giáo dục bắt buộc; 
d) Lao động nữ mang thai theo quy định tại Điều 138 của Bộ luật này; 
đ) Người lao động được bổ nhiệm làm người quản lý doanh nghiệp của công ty trách nhiệm hữu 
hạn một thành viên do Nhà nước nắm giữ 100% vốn điều lệ; 
e) Người lao động được ủy quyền để thực hiện quyền, trách nhiệm của đại diện chủ sở hữu nhà 
nước đối với phần vốn nhà nước tại doanh nghiệp; 
g) Người lao động được ủy quyền để thực hiện quyền, trách nhiệm của doanh nghiệp đối với 
phần vốn của doanh nghiệp đầu tư tại doanh nghiệp khác; 
h) Trường hợp khác do hai bên thỏa thuận. 
2. Trong thời gian tạm hoãn thực hiện hợp đồng lao động, người lao động không được hưởng 
lương và quyền, lợi ích đã giao kết trong hợp đồng lao động, trừ trường hợp hai bên có thỏa 
thuận hoặc pháp luật có quy định khác.

[RULES]
{"id": "LAB-08-D30-000", "type": "condition", "premises": ["covered_point_a"], "conclusion": "contract_suspended", "source": "08_luat_lao_dong_45_2019_QH14, Điều 30 khoản 1 điểm a", "exception_to": "", "quote": "Người lao động thực hiện nghĩa vụ quân sự, nghĩa vụ tham gia Dân quân tự vệ."}
{"id": "LAB-08-D30-001", "type": "condition", "premises": ["not_hold_id_documents"], "conclusion": "contract_suspended", "source": "08_luat_lao_dong_45_2019_QH14, Điều 30 khoản 1 điểm b", "exception_to": "", "quote": "Người lao động bị tạm giữ, tạm giam theo quy định của pháp luật về tố tụng hình sự."}
{"id": "LAB-08-D30-002", "type": "condition", "premises": ["must_follow_labor_law"], "conclusion": "contract_suspended", "source": "08_luat_lao_dong_45_2019_QH14, Điều 30 khoản 1 điểm c", "exception_to": "", "quote": "Người lao động phải chấp hành quyết định áp dụng biện pháp đưa vào trường giáo dưỡng, cơ sở cai nghiện bắt buộc hoặc cơ sở giáo dục bắt buộc."}
{"id": "LAB-08-D30-003", "type": "condition", "premises": ["must_follow_labor_law"], "conclusion": "contract_suspended", "source": "08_luat_lao_dong_45_2019_QH14, Điều 30 khoản 1 điểm d", "exception_to": "", "quote": "Lao động nữ mang thai theo quy định tại Điều 138 của Bộ luật này."}
{"id": "LAB-08-D30-004", "type": "condition", "premises": ["under_management"], "conclusion": "contract_suspended", "source": "08_luat_lao_dong_45_2019_QH14, Điều 30 khoản 1 điểm đ", "exception_to": "", "quote": "Người lao động được bổ nhiệm làm người quản lý doanh nghiệp của công ty trách nhiệm hữu hạn một thành viên do Nhà nước nắm giữ 100% vốn điều lệ."}
{"id": "LAB-08-D30-005", "type": "condition", "premises": ["under_management"], "conclusion": "contract_suspended", "source": "08_luat_lao_dong_45_2019_QH14, Điều 30 khoản 1 điểm e", "exception_to": "", "quote": "Người lao động được ủy quyền để thực hiện quyền, trách nhiệm của đại diện chủ sở hữu nhà nước đối với phần vốn nhà nước tại doanh nghiệp."}
{"id": "LAB-08-D30-006", "type": "condition", "premises": ["under_management"], "conclusion": "contract_suspended", "source": "08_luat_lao_dong_45_2019_QH14, Điều 30 khoản 1 điểm g", "exception_to": "", "quote": "Người lao động được ủy quyền để thực hiện quyền, trách nhiệm của doanh nghiệp đối với phần vốn của doanh nghiệp đầu tư tại doanh nghiệp khác."}
{"id": "LAB-08-D30-007", "type": "condition", "premises": [], "conclusion": "contract_suspended", "source": "08_luat_lao_dong_45_2019_QH14, Điều 30 khoản 1 điểm h", "exception_to": "", "quote": "Trường hợp khác do hai bên thỏa thuận."}
{"id": "LAB-08-D30-008", "type": "condition", "premises": ["contract_suspended"], "conclusion": "not_require_security_deposit", "source": "08_luat_lao_dong_45_2019_QH14, Điều 30 khoản 2", "exception_to": "", "quote": "Trong thời gian tạm hoãn thực hiện hợp đồng lao động, người lao động không được hưởng lương và quyền, lợi ích đã giao kết trong hợp đồng lao động, trừ trường hợp hai bên có thỏa thuận hoặc pháp luật có quy định khác."}


######## 08_luat_lao_dong_45_2019_QH14 — Điều 90. Tiền lương
[NGUYÊN VĂN]
Điều 90. Tiền lương 
1. Tiền lương là số tiền mà người sử dụng lao động trả cho người lao động theo thỏa thuận để 
thực hiện công việc, bao gồm mức lương theo công việc hoặc chức danh, phụ cấp lương và các 
khoản bổ sung khác. 
2. Mức lương theo công việc hoặc chức danh không được thấp hơn mức lương tối thiểu. 
3. Người sử dụng lao động phải bảo đảm trả lương bình đẳng, không phân biệt giới tính đối với 
người lao động làm công việc có giá trị như nhau.

[RULES]
{"id": "LAB-08-D90-000", "type": "condition", "premises": ["paid_wage"], "conclusion": "must_pay_wages_and_benefits", "source": "08_luat_lao_dong_45_2019_QH14, Điều 90 khoản 1", "exception_to": "", "quote": "Tiền lương là số tiền mà người sử dụng lao động trả cho người lao động theo thỏa thuận để thực hiện công việc."}
{"id": "LAB-08-D90-001", "type": "condition", "premises": ["paid_wage", "wage_at_least_min_base"], "conclusion": "not_lower_worker_rights", "source": "08_luat_lao_dong_45_2019_QH14, Điều 90 khoản 2", "exception_to": "", "quote": "Mức lương theo công việc hoặc chức danh không được thấp hơn mức lương tối thiểu."}
{"id": "LAB-08-D90-002", "type": "condition", "premises": ["paid_wage", "gender_equality_assured"], "conclusion": "must_pay_wages_and_benefits", "source": "08_luat_lao_dong_45_2019_QH14, Điều 90 khoản 3", "exception_to": "", "quote": "Người sử dụng lao động phải bảo đảm trả lương bình đẳng, không phân biệt giới tính đối với người lao động làm công việc có giá trị như nhau."}
