

######## 08_luat_lao_dong_45_2019_QH14 — Điều 97. Kỳ hạn trả lương
[NGUYÊN VĂN]
Điều 97. Kỳ hạn trả lương 
1. Người lao động hưởng lương theo giờ, ngày, tuần thì được trả lương sau giờ, ngày, tuần làm 
việc hoặc được trả gộp do hai bên thỏa thuận nhưng không quá 15 ngày phải được trả gộp một 
lần. 
2. Người lao động hưởng lương theo tháng được trả một tháng một lần hoặc nửa tháng một lần. 
Thời điểm trả lương do hai bên thỏa thuận và phải được ấn định vào một thời điểm có tính chu 
kỳ. 
3. Người lao động hưởng lương theo sản phẩm, theo khoán được trả lương theo thỏa thuận của 
hai bên; nếu công việc phải làm trong nhiều tháng thì hằng tháng được tạm ứng tiền lương theo 
khối lượng công việc đã làm trong tháng. 
4. Trường hợp vì lý do bất khả kháng mà người sử dụng lao động đã tìm mọi biện pháp khắc 
phục nhưng không thể trả lương đúng hạn thì không được chậm quá 30 ngày; nếu trả lương chậm 
từ 15 ngày trở lên thì người sử dụng lao động phải đền bù cho người lao động một khoản tiền ít 
nhất bằng số tiền lãi của số tiền trả chậm tính theo lãi suất huy động tiền gửi có kỳ hạn 01 tháng 
do ngân hàng nơi người sử dụng lao động mở tài khoản trả lương cho người lao động công bố tại 
thời điểm trả lương.

[RULES]
{"id": "LAB-08-D97-000", "type": "condition", "premises": ["wage_at_least_min_base", "~unpaid_14_days"], "conclusion": "must_pay_wages_and_benefits", "source": "08_luat_lao_dong_45_2019_QH14, Điều 97 khoản 1", "exception_to": "", "quote": "Người lao động hưởng lương theo giờ, ngày, tuần thì được trả lương sau giờ, ngày, tuần làm việc hoặc được trả gộp do hai bên thỏa thuận nhưng không quá 15 ngày phải được trả gộp một lần."}
{"id": "LAB-08-D97-001", "type": "condition", "premises": ["wage_at_least_min_base"], "conclusion": "must_pay_wages_and_benefits", "source": "08_luat_lao_dong_45_2019_QH14, Điều 97 khoản 2", "exception_to": "", "quote": "Người lao động hưởng lương theo tháng được trả một tháng một lần hoặc nửa tháng một lần."}
{"id": "LAB-08-D97-002", "type": "condition", "premises": ["wage_at_least_min_base"], "conclusion": "must_pay_wages_and_benefits", "source": "08_luat_lao_dong_45_2019_QH14, Điều 97 khoản 3", "exception_to": "", "quote": "Người lao động hưởng lương theo sản phẩm, theo khoán được trả lương theo thỏa thuận của hai bên."}
{"id": "LAB-08-D97-003", "type": "condition", "premises": ["unpaid_14_days"], "conclusion": "must_pay_compensation_for_notice", "source": "08_luat_lao_dong_45_2019_QH14, Điều 97 khoản 4", "exception_to": "", "quote": "Nếu trả lương chậm từ 15 ngày trở lên thì người sử dụng lao động phải đền bù cho người lao động một khoản tiền ít nhất bằng số tiền lãi của số tiền trả chậm."}


######## 08_luat_lao_dong_45_2019_QH14 — Điều 98. Tiền lương làm thêm giờ, làm việc vào ban đêm
[NGUYÊN VĂN]
Điều 98. Tiền lương làm thêm giờ, làm việc vào ban đêm 
1. Người lao động làm thêm giờ được trả lương tính theo đơn giá tiền lương hoặc tiền lương thực 
trả theo công việc đang làm như sau: 
a) Vào ngày thường, ít nhất bằng 150%; 
b) Vào ngày nghỉ hằng tuần, ít nhất bằng 200%; 
c) Vào ngày nghỉ lễ, tết, ngày nghỉ có hưởng lương, ít nhất bằng 300% chưa kể tiền lương ngày 
lễ, tết, ngày nghỉ có hưởng lương đối với người lao động hưởng lương ngày. 
2. Người lao động làm việc vào ban đêm thì được trả thêm ít nhất bằng 30% tiền lương tính theo 
đơn giá tiền lương hoặc tiền lương thực trả theo công việc của ngày làm việc bình thường. 
3. Người lao động làm thêm giờ vào ban đêm thì ngoài việc trả lương theo quy định tại khoản 1 
và khoản 2 Điều này, người lao động còn được trả thêm 20% tiền lương tính theo đơn giá tiền 
lương hoặc tiền lương theo công việc làm vào ban ngày của ngày làm việc bình thường hoặc của 
ngày nghỉ hằng tuần hoặc của ngày nghỉ lễ, tết. 
4. Chính phủ quy định chi tiết Điều này.

[RULES]
{"id": "LAB-08-D98-000", "type": "condition", "premises": ["paid_wage", "~not_paid_salary"], "conclusion": "must_pay_additional_compensation", "source": "08_luat_lao_dong_45_2019_QH14, Điều 98 khoản 1 điểm a", "exception_to": "", "quote": "Vào ngày thường, ít nhất bằng 150%;"}
{"id": "LAB-08-D98-001", "type": "condition", "premises": ["paid_wage", "~not_paid_salary"], "conclusion": "must_pay_additional_compensation", "source": "08_luat_lao_dong_45_2019_QH14, Điều 98 khoản 1 điểm b", "exception_to": "", "quote": "Vào ngày nghỉ hằng tuần, ít nhất bằng 200%;"}
{"id": "LAB-08-D98-002", "type": "condition", "premises": ["paid_wage", "~not_paid_salary"], "conclusion": "must_pay_additional_compensation", "source": "08_luat_lao_dong_45_2019_QH14, Điều 98 khoản 1 điểm c", "exception_to": "", "quote": "Vào ngày nghỉ lễ, tết, ngày nghỉ có hưởng lương, ít nhất bằng 300%..."}
{"id": "LAB-08-D98-003", "type": "condition", "premises": ["paid_wage", "~not_paid_salary"], "conclusion": "must_pay_additional_compensation", "source": "08_luat_lao_dong_45_2019_QH14, Điều 98 khoản 2", "exception_to": "", "quote": "Người lao động làm việc vào ban đêm thì được trả thêm ít nhất bằng 30%..."}
{"id": "LAB-08-D98-004", "type": "condition", "premises": ["paid_wage", "~not_paid_salary"], "conclusion": "must_pay_additional_compensation", "source": "08_luat_lao_dong_45_2019_QH14, Điều 98 khoản 3", "exception_to": "", "quote": "Người lao động làm thêm giờ vào ban đêm thì ngoài việc trả lương theo quy định tại khoản 1 và khoản 2..."}


######## 09_nghi_dinh_145_2020_ND-CP — Điều 108. Giải quyết tranh chấp liên quan đến quyền thương lượng tập thể tại nơi sử dụng lao
[NGUYÊN VĂN]
Điều 108. Giải quyết tranh chấp liên quan đến quyền thương lượng tập thể tại nơi sử dụng lao 
động không được đình công 
Tranh chấp giữa các bên liên quan đến quyền thương lượng tập thể tại nơi sử dụng lao động không 
được đình công được thực hiện theo quy định của Chính phủ về giải quyết tranh chấp giữa các bên 
liên quan đến quyền thương lượng tập thể theo quy định tại khoản 4 Điều 68 của Bộ luật Lao động. 
 
Mục 4. HOÃN, NGỪNG ĐÌNH CÔNG VÀ GIẢI QUYẾT QUYỀN LỢI CỦA NGƯỜI LAO ĐỘNG

[RULES]
{"id": "LAB-09-D108-000", "type": "condition", "premises": ["can_negotiation_dispute_resolution", "~not_allowed_to_strike_in_areas_affecting_national_security", "~not_use_workers_during_strike"], "conclusion": "can_resolve_collective_labor_disputes", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 108 khoản 1", "exception_to": "", "quote": "Tranh chấp giữa các bên liên quan đến quyền thương lượng tập thể tại nơi sử dụng lao động không được đình công được thực hiện theo quy định của Chính phủ."}
{"id": "LAB-09-D108-001", "type": "condition", "premises": ["not_allowed_to_strike_in_areas_affecting_national_security"], "conclusion": "must_follow_law_for_decision", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 108 khoản 1", "exception_to": "", "quote": "Tranh chấp giữa các bên liên quan đến quyền thương lượng tập thể tại nơi sử dụng lao động không được đình công."}


######## 09_nghi_dinh_145_2020_ND-CP — Điều 55. Tiền lương làm thêm giờ
[NGUYÊN VĂN]
Điều 55. Tiền lương làm thêm giờ 
Tiền lương làm thêm giờ theo khoản 1 Điều 98 của Bộ luật Lao động được quy định như sau: 
1. Đối với người lao động hưởng lương theo thời gian, được trả lương làm thêm giờ khi làm việc 
ngoài thời giờ làm việc bình thường do người sử dụng lao động quy định theo Điều 105 của Bộ luật 
Lao động và được tính theo công thức sau: 
Tiền lương 
làm thêm giờ 
= 
Tiền lương giờ thực trả của công 
việc đang làm vào ngày làm việc 
bình thường 
x Mức ít nhất 150% hoặc 
200% hoặc 300% 
x 
Số giờ làm 
thêm 
Trong đó: 
a) Tiền lương giờ thực trả của công việc đang làm vào ngày làm việc bình thường, được xác định 
bằng tiền lương thực trả của công việc đang làm của tháng hoặc tuần hoặc ngày mà người lao động 
làm thêm giờ (không bao gồm tiền lương làm thêm giờ, tiền lương trả thêm khi làm việc vào ban đêm, 
tiền lương của ngày nghỉ lễ, tết, ngày nghỉ có hưởng lương theo quy định của Bộ luật Lao động; tiền 
thưởng theo quy định tại Điều 104 của Bộ luật Lao động, tiền thưởng sáng kiến; tiền ăn giữa ca, các 
 
khoản hỗ trợ xăng xe, điện thoại, đi lại, tiền nhà ở, tiền giữ trẻ, nuôi con nhỏ; hỗ trợ khi có thân nhân 
bị chết, người lao động có người thân kết hôn, sinh nhật của người lao động, bệnh nghề nghiệp và 
các khoản hỗ trợ, trợ cấp khác không liên quan đến thực hiện công việc hoặc chức danh trong hợp 
đồng lao động) chia cho tổng số giờ thực tế làm việc tương ứng trong tháng hoặc tuần hoặc ngày 
người lao động làm thêm giờ (không quá số ngày làm việc bình thường trong tháng và số giờ làm việc 
bình thường trong 01 ngày, 01 tuần theo quy định của pháp luật mà doanh nghiệp lựa chọn và không 
kể số giờ làm thêm); 
b) Mức ít nhất bằng 150% so với tiền lương giờ thực trả của công việc đang làm vào ngày làm việc 
bình thường, áp dụng đối với giờ làm thêm vào ngày thường; mức ít nhất bằng 200% so với tiền 
lương giờ thực trả của công việc đang làm vào ngày làm việc bình thường, áp dụng đối với giờ làm 
thêm vào ngày nghỉ hằng tuần; mức ít nhất bằng 300% so với tiền lương giờ thực trả của công việc 
đang làm vào ngày làm việc bình thường, áp dụng đối với giờ làm thêm vào ngày nghỉ lễ, tết, ngày 
nghỉ có hưởng lương, chưa kể tiền lương của ngày nghỉ lễ, tết, ngày nghỉ có hưởng lương đối với 
người lao động hưởng lương ngày. 
2. Đối với người lao động hưởng lương theo sản phẩm, được trả lương làm thêm giờ khi làm việc 
ngoài thời giờ làm việc bình thường để làm thêm số lượng, khối lượng sản phẩm ngoài số lượng, khối 
lượng sản phẩm theo định mức lao động theo thỏa thuận với người sử dụng lao động và được tính 
theo công thức sau: 
Tiền lương 
làm thêm giờ = 
Đơn giá tiền lương sản phẩm của 
ngày làm việc bình thường 
x Mức ít nhất 150% hoặc 
200% hoặc 300% 
x Số sản phẩm 
làm thêm 
Trong đó: 
Mức ít nhất bằng 150% so với đơn giá tiền lương sản phẩm của ngày làm việc bình thường, áp dụng 
đối với sản phẩm làm thêm vào ngày thường; mức ít nhất bằng 200% so với đơn giá tiền lương sản 
phẩm của ngày làm việc bình thường, áp dụng đối với sản phẩm làm thêm vào ngày nghỉ hằng tuần; 
mức ít nhất bằng 300% so với đơn giá tiền lương sản phẩm của ngày làm việc bình thường, áp dụng 
đối với sản phẩm làm thêm vào ngày nghỉ lễ, tết, ngày nghỉ có hưởng lương. 
3. Người lao động làm thêm giờ vào ngày lễ, tết trùng vào ngày nghỉ hằng tuần thì được trả lương làm 
thêm giờ vào ngày nghỉ lễ, tết. Trường hợp làm thêm giờ vào ngày nghỉ bù khi ngày lễ, tết trùng vào 
ngày nghỉ hằng tuần thì người lao động được trả lương làm thêm giờ vào ngày nghỉ hằng tuần.

[RULES]
{"id": "LAB-09-D55-000", "type": "condition", "premises": ["worker_paid_by_time", "worked_overtime", "normal_working_hours_defined"], "conclusion": "must_pay_overtime_salary", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 55 khoản 1", "exception_to": "", "quote": "Đối với người lao động hưởng lương theo thời gian, được trả lương làm thêm giờ khi làm việc ngoài thời giờ làm việc bình thường..."}
{"id": "LAB-09-D55-001", "type": "condition", "premises": ["worker_paid_by_time", "worked_overtime", "normal_working_hours_defined", "overtime_hours_within_limit"], "conclusion": "overtime_salary_calculation", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 55 khoản 1", "exception_to": "", "quote": "Tiền lương làm thêm giờ = Tiền lương giờ thực trả của công việc đang làm vào ngày làm việc bình thường x Mức ít nhất 150% hoặc 200% hoặc 300% x Số giờ làm thêm"}
{"id": "LAB-09-D55-002", "type": "condition", "premises": ["worker_paid_by_time", "worked_overtime", "normal_working_hours_defined"], "conclusion": "overtime_rate_for_normal_days", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 55 khoản 1 điểm a", "exception_to": "", "quote": "Mức ít nhất bằng 150% so với tiền lương giờ thực trả của công việc đang làm vào ngày làm việc bình thường, áp dụng đối với giờ làm thêm vào ngày thường"}
{"id": "LAB-09-D55-003", "type": "condition", "premises": ["worker_paid_by_time", "worked_overtime", "normal_working_hours_defined"], "conclusion": "overtime_rate_for_weekend", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 55 khoản 1 điểm b", "exception_to": "", "quote": "Mức ít nhất bằng 200% so với tiền lương giờ thực trả của công việc đang làm vào ngày làm việc bình thường, áp dụng đối với giờ làm thêm vào ngày nghỉ hằng tuần"}
{"id": "LAB-09-D55-004", "type": "condition", "premises": ["worker_paid_by_time", "worked_overtime", "normal_working_hours_defined"], "conclusion": "overtime_rate_for_holidays", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 55 khoản 1 điểm c", "exception_to": "", "quote": "Mức ít nhất bằng 300% so với tiền lương giờ thực trả của công việc đang làm vào ngày làm việc bình thường, áp dụng đối với giờ làm thêm vào ngày nghỉ lễ, tết, ngày nghỉ có hưởng lương"}
{"id": "LAB-09-D55-005", "type": "condition", "premises": ["worker_paid_by_product", "worked_overtime"], "conclusion": "must_pay_overtime_salary_for_product", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 55 khoản 2", "exception_to": "", "quote": "Đối với người lao động hưởng lương theo sản phẩm, được trả lương làm thêm giờ khi làm việc ngoài thời giờ làm việc bình thường..."}
{"id": "LAB-09-D55-006", "type": "condition", "premises": ["worker_paid_by_product", "worked_overtime"], "conclusion": "overtime_salary_calculation_for_product", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 55 khoản 2", "exception_to": "", "quote": "Tiền lương làm thêm giờ = Đơn giá tiền lương sản phẩm của ngày làm việc bình thường x Mức ít nhất 150% hoặc 200% hoặc 300% x Số sản phẩm làm thêm"}
{"id": "LAB-09-D55-007", "type": "condition", "premises": ["worker_paid_by_product", "worked_overtime"], "conclusion": "overtime_rate_for_product_normal_days", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 55 khoản 2 điểm a", "exception_to": "", "quote": "Mức ít nhất bằng 150% so với đơn giá tiền lương sản phẩm của ngày làm việc bình thường, áp dụng đối với sản phẩm làm thêm vào ngày thường"}
{"id": "LAB-09-D55-008", "type": "condition", "premises": ["worker_paid_by_product", "worked_overtime"], "conclusion": "overtime_rate_for_product_weekend", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 55 khoản 2 điểm b", "exception_to": "", "quote": "Mức ít nhất bằng 200% so với đơn giá tiền lương sản phẩm của ngày làm việc bình thường, áp dụng đối với sản phẩm làm thêm vào ngày nghỉ hằng tuần"}
{"id": "LAB-09-D55-009", "type": "condition", "premises": ["worker_paid_by_product", "worked_overtime"], "conclusion": "overtime_rate_for_product_holidays", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 55 khoản 2 điểm c", "exception_to": "", "quote": "Mức ít nhất bằng 300% so với đơn giá tiền lương sản phẩm của ngày làm việc bình thường, áp dụng đối với sản phẩm làm thêm vào ngày nghỉ lễ, tết, ngày nghỉ có hưởng lương."}
{"id": "LAB-09-D55-010", "type": "condition", "premises": ["worked_overtime_on_holiday", "worked_overtime_on_weekend"], "conclusion": "must_pay_overtime_salary_for_holiday", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 55 khoản 3", "exception_to": "", "quote": "Người lao động làm thêm giờ vào ngày lễ, tết trùng vào ngày nghỉ hằng tuần thì được trả lương làm thêm giờ vào ngày nghỉ lễ, tết."}


######## 09_nghi_dinh_145_2020_ND-CP — Điều 59. Sự đồng ý của người lao động khi làm thêm giờ
[NGUYÊN VĂN]
Điều 59. Sự đồng ý của người lao động khi làm thêm giờ 
1. Trừ các trường hợp quy định tại Điều 108 của Bộ luật Lao động, các trường hợp khác khi tổ chức 
làm thêm giờ, người sử dụng lao động phải được sự đồng ý của người lao động tham gia làm thêm 
về các nội dung sau đây: 
a) Thời gian làm thêm; 
b) Địa điểm làm thêm; 
c) Công việc làm thêm. 
2. Trường hợp sự đồng ý của người lao động được ký thành văn bản riêng thì tham khảo Mẫu số 
01/PLIV Phụ lục IV ban hành kèm theo Nghị định này.

[RULES]
{"id": "LAB-09-D59-000", "type": "condition", "premises": ["employer_representation_present", "worker_representation_present", "must_follow_labor_law"], "conclusion": "must_get_worker_consent_for_overtime", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 59 khoản 1", "exception_to": "Điều 108 của Bộ luật Lao động", "quote": "người sử dụng lao động phải được sự đồng ý của người lao động tham gia làm thêm"}
{"id": "LAB-09-D59-001", "type": "condition", "premises": ["must_get_worker_consent_for_overtime"], "conclusion": "must_specify_overtime_time", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 59 khoản 1 điểm a", "exception_to": "", "quote": "Thời gian làm thêm"}
{"id": "LAB-09-D59-002", "type": "condition", "premises": ["must_get_worker_consent_for_overtime"], "conclusion": "must_specify_overtime_location", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 59 khoản 1 điểm b", "exception_to": "", "quote": "Địa điểm làm thêm"}
{"id": "LAB-09-D59-003", "type": "condition", "premises": ["must_get_worker_consent_for_overtime"], "conclusion": "must_specify_overtime_job", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 59 khoản 1 điểm c", "exception_to": "", "quote": "Công việc làm thêm"}


######## 09_nghi_dinh_145_2020_ND-CP — Điều 64. Nghỉ trong giờ làm việc
[NGUYÊN VĂN]
Điều 64. Nghỉ trong giờ làm việc 
1. Thời gian nghỉ giữa giờ ít nhất 45 phút liên tục theo quy định tại khoản 1 Điều 109 của Bộ luật Lao 
động được áp dụng đối với người lao động làm việc từ 06 giờ trở lên trong một ngày, trong đó có ít 
nhất 03 giờ làm việc trong khung giờ làm việc ban đêm quy định tại Điều 106 của Bộ luật Lao động. 
2. Thời gian nghỉ giữa giờ được tính vào giờ làm việc đối với trường hợp làm việc theo ca liên tục quy 
định tại khoản 3 Điều 63 Nghị định này ít nhất 30 phút, riêng trường hợp làm việc ban đêm thì được 
tính ít nhất 45 phút. 
3. Người sử dụng lao động quyết định thời điểm nghỉ trong giờ làm việc, nhưng không được bố trí 
thời gian nghỉ này vào thời điểm bắt đầu hoặc kết thúc ca làm việc. 
4. Ngoài trường hợp làm việc theo ca liên tục quy định tại khoản 3 Điều 63 Nghị định này, khuyến 
khích các bên thương lượng thời gian nghỉ giữa giờ tính vào giờ làm việc.

[RULES]
{"id": "LAB-09-D64-000", "type": "condition", "premises": ["worked_5_hours", "worked_night_hours"], "conclusion": "must_provide_break_time_night", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 64 khoản 1", "exception_to": "", "quote": "Người lao động được nghỉ giữa giờ ít nhất 45 phút liên tục khi làm việc ban đêm."}
{"id": "LAB-09-D64-001", "type": "condition", "premises": ["worked_in_shifts", "~worked_night_hours"], "conclusion": "must_provide_break_time", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 64 khoản 2", "exception_to": "", "quote": "Thời gian nghỉ giữa giờ được tính vào giờ làm việc đối với trường hợp làm việc theo ca liên tục quy định tại khoản 3 Điều 63 Nghị định này ít nhất 30 phút."}
{"id": "LAB-09-D64-002", "type": "condition", "premises": ["worked_in_shifts", "worked_night_hours"], "conclusion": "break_time_counted_as_working_time", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 64 khoản 2", "exception_to": "", "quote": "Riêng trường hợp làm việc ban đêm thì được tính ít nhất 45 phút."}
{"id": "LAB-09-D64-003", "type": "condition", "premises": ["employer_decides_break_time"], "conclusion": "must_not_schedule_break_at_shift_start_end", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 64 khoản 3", "exception_to": "", "quote": "Người sử dụng lao động quyết định thời điểm nghỉ trong giờ làm việc, nhưng không được bố trí thời gian nghỉ này vào thời điểm bắt đầu hoặc kết thúc ca làm việc."}
{"id": "LAB-09-D64-004", "type": "condition", "premises": [], "conclusion": "must_provide_conditions_for_negotiation", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 64 khoản 4", "exception_to": "", "quote": "Khuyến khích các bên thương lượng thời gian nghỉ giữa giờ tính vào giờ làm việc."}


######## 09_nghi_dinh_145_2020_ND-CP — Điều 69. Nội quy lao động
[NGUYÊN VĂN]
Điều 69. Nội quy lao động 
Nội quy lao động tại Điều 118 của Bộ luật Lao động được quy định như sau: 
1. Người sử dụng lao động phải ban hành nội quy lao động, nếu sử dụng từ 10 người lao động trở lên 
thì nội quy lao động phải bằng văn bản, nếu sử dụng dưới 10 người lao động thì không bắt buộc ban 
hành nội quy lao động bằng văn bản nhưng phải thỏa thuận nội dung về kỷ luật lao động, trách nhiệm 
vật chất trong hợp đồng lao động. 
2. Nội dung nội quy lao động không được trái với pháp luật về lao động và quy định của pháp luật có 
liên quan. Nội quy lao động gồm những nội dung chủ yếu sau: 
a) Thời giờ làm việc, thời giờ nghỉ ngơi: quy định thời giờ làm việc bình thường trong 01 ngày, trong 
01 tuần; ca làm việc; thời điểm bắt đầu, thời điểm kết thúc ca làm việc; làm thêm giờ (nếu có); làm 
thêm giờ trong các trường hợp đặc biệt; thời điểm các đợt nghỉ giải lao ngoài thời gian nghỉ giữa giờ; 
nghỉ chuyển ca; ngày nghỉ hằng tuần; nghỉ hằng năm, nghỉ việc riêng, nghỉ không hưởng lương; 
b) Trật tự tại nơi làm việc: quy định phạm vi làm việc, đi lại trong thời giờ làm việc; văn hóa ứng xử, 
trang phục; tuân thủ phân công, điều động của người sử dụng lao động; 
c) An toàn, vệ sinh lao động tại nơi làm việc: trách nhiệm chấp hành các quy định, nội quy, quy trình, 
biện pháp bảo đảm về an toàn, vệ sinh lao động, phòng chống cháy nổ; sử dụng và bảo quản các 
phương tiện bảo vệ cá nhân, các thiết bị bảo đảm an toàn, vệ sinh lao động tại nơi làm việc; vệ sinh, 
khử độc, khử trùng tại nơi làm việc; 
d) Phòng, chống quấy rối tình dục tại nơi làm việc; trình tự, thủ tục xử lý hành vi quấy rối tình dục tại 
nơi làm việc: người sử dụng lao động quy định về phòng, chống quấy rối tình dục theo quy định tại 
Điều 85 Nghị định này; 
đ) Bảo vệ tài sản và bí mật kinh doanh, bí mật công nghệ, sở hữu trí tuệ của người sử dụng lao động: 
quy định danh mục tài sản, tài liệu, bí mật công nghệ, bí mật kinh doanh, sở hữu trí tuệ; trách nhiệm, 
biện pháp được áp dụng để bảo vệ tài sản, bí mật; hành vi xâm phạm tài sản và bí mật; 
 
e) Trường hợp được tạm thời chuyển người lao động làm việc khác so với hợp đồng lao động: quy 
định cụ thể các trường hợp do nhu cầu sản xuất, kinh doanh được tạm thời chuyển người lao động 
làm việc khác so với hợp đồng lao động theo quy định tại khoản 1 Điều 29 của Bộ luật Lao động; 
g) Các hành vi vi phạm kỷ luật lao động của người lao động và các hình thức xử lý kỷ luật lao động: 
quy định cụ thể hành vi vi phạm kỷ luật lao động; hình thức xử lý kỷ luật lao động tương ứng với hành 
vi vi phạm; 
h) Trách nhiệm vật chất: quy định các trường hợp phải bồi thường thiệt hại do làm hư hỏng dụng cụ, 
thiết bị hoặc có hành vi gây thiệt hại tài sản; do làm mất dụng cụ, thiết bị, tài sản hoặc tiêu hao vật tư 
quá định mức; mức bồi thường thiệt hại tương ứng mức độ thiệt hại; người có thẩm quyền xử lý bồi 
thường thiệt hại; 
i) Người có thẩm quyền xử lý kỷ luật lao động: người có thẩm quyền giao kết hợp đồng lao động bên 
phía người sử dụng lao động quy định tại khoản 3 Điều 18 của Bộ luật Lao động hoặc người được 
quy định cụ thể trong nội quy lao động. 
 3. Trước khi ban hành nội quy lao động hoặc sửa đổi, bổ sung nội quy lao động, người sử dụng lao 
động phải tham khảo ý kiến của tổ chức đại diện người lao động tại cơ sở đối với nơi có tổ chức đại 
diện người lao động tại cơ sở. Việc tham khảo ý kiến tổ chức đại diện người lao động tại cơ sở thực 
hiện theo quy định tại khoản 1 Điều 41 Nghị định này. 
4. Nội quy lao động sau khi ban hành phải được gửi đến từng tổ chức đại diện người lao động tại cơ 
sở (nếu có) và thông báo đến toàn bộ người lao động, đồng thời niêm yết nội dung chính ở những nơi 
cần thiết tại nơi làm việc.

[RULES]
{"id": "LAB-09-D69-000", "type": "condition", "premises": ["employer_issues_internal_rules_in_written_form", "~not_use_workers_without_agreement"], "conclusion": "must_provide_conditions_for_negotiation", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 69 khoản 1", "exception_to": "", "quote": "nếu sử dụng từ 10 người lao động trở lên thì nội quy lao động phải bằng văn bản"}
{"id": "LAB-09-D69-001", "type": "condition", "premises": ["~employer_issues_internal_rules_in_written_form", "not_use_workers_without_agreement"], "conclusion": "must_provide_conditions_for_negotiation", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 69 khoản 1", "exception_to": "", "quote": "nếu sử dụng dưới 10 người lao động thì không bắt buộc ban hành nội quy lao động bằng văn bản nhưng phải thỏa thuận nội dung về kỷ luật lao động"}
{"id": "LAB-09-D69-002", "type": "condition", "premises": ["not_conflict_with_law"], "conclusion": "must_correct_internal_rules_if_invalid", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 69 khoản 2", "exception_to": "", "quote": "Nội dung nội quy lao động không được trái với pháp luật về lao động và quy định của pháp luật có liên quan"}
{"id": "LAB-09-D69-003", "type": "condition", "premises": [], "conclusion": "must_define_job_list_for_trained_workers", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 69 khoản 2 điểm a", "exception_to": "", "quote": "Nội quy lao động gồm những nội dung chủ yếu sau: Thời giờ làm việc, thời giờ nghỉ ngơi"}
{"id": "LAB-09-D69-004", "type": "condition", "premises": [], "conclusion": "must_follow_management", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 69 khoản 2 điểm b", "exception_to": "", "quote": "Trật tự tại nơi làm việc: quy định phạm vi làm việc, đi lại trong thời giờ làm việc"}
{"id": "LAB-09-D69-005", "type": "condition", "premises": [], "conclusion": "must_follow_safety_health_regulations", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 69 khoản 2 điểm c", "exception_to": "", "quote": "An toàn, vệ sinh lao động tại nơi làm việc: trách nhiệm chấp hành các quy định, nội quy, quy trình, biện pháp bảo đảm về an toàn, vệ sinh lao động"}
{"id": "LAB-09-D69-006", "type": "condition", "premises": [], "conclusion": "must_not_interfere_with_strike", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 69 khoản 2 điểm d", "exception_to": "", "quote": "Phòng, chống quấy rối tình dục tại nơi làm việc"}
{"id": "LAB-09-D69-007", "type": "condition", "premises": [], "conclusion": "must_provide_work_conditions", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 69 khoản 2 điểm e", "exception_to": "", "quote": "Trường hợp được tạm thời chuyển người lao động làm việc khác so với hợp đồng lao động"}
{"id": "LAB-09-D69-008", "type": "condition", "premises": [], "conclusion": "must_not_interfere_with_discussion", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 69 khoản 2 điểm g", "exception_to": "", "quote": "Các hành vi vi phạm kỷ luật lao động của người lao động và các hình thức xử lý kỷ luật lao động"}
{"id": "LAB-09-D69-009", "type": "condition", "premises": [], "conclusion": "must_pay_compensation_for_damage", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 69 khoản 2 điểm h", "exception_to": "", "quote": "Trách nhiệm vật chất: quy định các trường hợp phải bồi thường thiệt hại do làm hư hỏng dụng cụ, thiết bị hoặc có hành vi gây thiệt hại tài sản"}
{"id": "LAB-09-D69-010", "type": "condition", "premises": [], "conclusion": "must_provide_documents_for_change_of_representative", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 69 khoản 2 điểm i", "exception_to": "", "quote": "Người có thẩm quyền xử lý kỷ luật lao động"}
{"id": "LAB-09-D69-011", "type": "condition", "premises": ["must_provide_conditions_for_negotiation"], "conclusion": "must_consult_workers_representative", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 69 khoản 3", "exception_to": "", "quote": "người sử dụng lao động phải tham khảo ý kiến của tổ chức đại diện người lao động tại cơ sở"}
{"id": "LAB-09-D69-012", "type": "condition", "premises": [], "conclusion": "must_publish_labor_regulations", "source": "09_nghi_dinh_145_2020_ND-CP, Điều 69 khoản 4", "exception_to": "", "quote": "Nội quy lao động sau khi ban hành phải được gửi đến từng tổ chức đại diện người lao động tại cơ sở"}
