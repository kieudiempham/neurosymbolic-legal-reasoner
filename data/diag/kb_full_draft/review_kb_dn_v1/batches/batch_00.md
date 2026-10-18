

######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 113. Thanh toán cổ phần đã đăng ký mua khi đăng ký thành lập doanh nghiệp
[NGUYÊN VĂN]
Điều 113. Thanh toán cổ phần đã đăng ký mua khi đăng ký thành lập doanh nghiệp 
1. Các cổ đông phải thanh toán đủ số cổ phần đã đăng ký mua trong thời hạn 90 ngày kể từ ngày 
được cấp Giấy chứng nhận đăng ký doanh nghiệp, trừ trường hợp Điều lệ công ty hoặc hợp đồng 
đăng ký mua cổ phần quy định một thời hạn khác ngắn hơn. Trường hợp cổ đông góp vốn bằng 
tài sản thì thời gian vận chuyển nhập khẩu, thực hiện thủ tục hành chính để chuyển quyền sở hữu 
tài sản đó không tính vào thời hạn góp vốn này. Hội đồng quản trị chịu trách nhiệm giám sát, đôn 
đốc cổ đông thanh toán đủ và đúng hạn các cổ phần đã đăng ký mua. 
2. Trong thời hạn từ ngày công ty được cấp Giấy chứng nhận đăng ký doanh nghiệp đến ngày 
cuối cùng phải thanh toán đủ số cổ phần đã đăng ký mua quy định tại khoản 1 Điều này, số phiếu 
biểu quyết của các cổ đông được tính theo số cổ phần phổ thông đã được đăng ký mua, trừ 
trường hợp Điều lệ công ty có quy định khác. 
3. Trường hợp sau thời hạn quy định tại khoản 1 Điều này, cổ đông chưa thanh toán hoặc chỉ 
thanh toán được một phần số cổ phần đã đăng ký mua thì thực hiện theo quy định sau đây: 
a) Cổ đông chưa thanh toán số cổ phần đã đăng ký mua đương nhiên không còn là cổ đông của 
công ty và không được chuyển nhượng quyền mua cổ phần đó cho người khác; 
b) Cổ đông chỉ thanh toán một phần số cổ phần đã đăng ký mua có quyền biểu quyết, nhận lợi 
tức và các quyền khác tương ứng với số cổ phần đã thanh toán; không được chuyển nhượng 
quyền mua số cổ phần chưa thanh toán cho người khác; 
c) Cổ phần chưa thanh toán được coi là cổ phần chưa bán và Hội đồng quản trị được quyền bán; 
d) Trong thời hạn 30 ngày kể từ ngày kết thúc thời hạn phải thanh toán đủ số cổ phần đã đăng ký 
mua theo quy định tại khoản 1 Điều này, công ty phải đăng ký điều chỉnh vốn điều lệ bằng mệnh 
giá số cổ phần đã được thanh toán đủ, trừ trường hợp số cổ phần chưa thanh toán đã được bán 
hết trong thời hạn này; đăng ký thay đổi cổ đông sáng lập. 
4. Cổ đông chưa thanh toán hoặc chưa thanh toán đủ số cổ phần đã đăng ký mua phải chịu trách 
nhiệm tương ứng với tổng mệnh giá cổ phần đã đăng ký mua đối với các nghĩa vụ tài chính của 
công ty phát sinh trong thời hạn trước ngày công ty đăng ký điều chỉnh vốn điều lệ theo quy định 
tại điểm d khoản 3 Điều này. Thành viên Hội đồng quản trị, người đại diện theo pháp luật phải 
chịu trách nhiệm liên đới về các thiệt hại phát sinh do không thực hiện hoặc không thực hiện 
đúng quy định tại khoản 1 và điểm d khoản 3 Điều này. 
5. Trừ trường hợp quy định tại khoản 2 Điều này, người góp vốn trở thành cổ đông của công ty 
kể từ thời điểm đã thanh toán việc mua cổ phần và những thông tin về cổ đông quy định tại các 
điểm b, c, d và đ khoản 2 Điều 122 của Luật này được ghi vào sổ đăng ký cổ đông.

[RULES]
{"id": "ENT-01-D113-000", "type": "condition", "premises": ["must_complete_capital_contribution", "is_registered_enterprise"], "conclusion": "must_pay_if_debts_fulfilled", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 113 khoản 1", "exception_to": "", "quote": "Các cổ đông phải thanh toán đủ số cổ phần đã đăng ký mua trong thời hạn 90 ngày kể từ ngày được cấp Giấy chứng nhận đăng ký doanh nghiệp"}
{"id": "ENT-01-D113-001", "type": "condition", "premises": ["must_complete_capital_contribution", "is_registered_enterprise", "~must_not_increase_salary_if_debts_due"], "conclusion": "must_fulfill_other_legal_obligations", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 113 khoản 1", "exception_to": "", "quote": "trừ trường hợp Điều lệ công ty hoặc hợp đồng đăng ký mua cổ phần quy định một thời hạn khác ngắn hơn"}
{"id": "ENT-01-D113-002", "type": "condition", "premises": ["is_member_not_fully_paid_capital"], "conclusion": "must_not_transfer_property_ownership", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 113 khoản 3 điểm a", "exception_to": "", "quote": "Cổ đông chưa thanh toán số cổ phần đã đăng ký mua đương nhiên không còn là cổ đông của công ty và không được chuyển nhượng quyền mua cổ phần đó cho người khác"}
{"id": "ENT-01-D113-003", "type": "condition", "premises": ["is_member_not_fully_paid_capital"], "conclusion": "can_receive_profit", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 113 khoản 3 điểm b", "exception_to": "", "quote": "Cổ đông chỉ thanh toán một phần số cổ phần đã đăng ký mua có quyền biểu quyết, nhận lợi tức và các quyền khác tương ứng với số cổ phần đã thanh toán"}
{"id": "ENT-01-D113-004", "type": "condition", "premises": ["is_member_not_fully_paid_capital"], "conclusion": "can_transfer_capital", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 113 khoản 3 điểm c", "exception_to": "", "quote": "Cổ phần chưa thanh toán được coi là cổ phần chưa bán và Hội đồng quản trị được quyền bán"}
{"id": "ENT-01-D113-005", "type": "condition", "premises": ["is_member_not_fully_paid_capital"], "conclusion": "is_responsible_for_enterprise_damage", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 113 khoản 4", "exception_to": "", "quote": "Cổ đông chưa thanh toán hoặc chưa thanh toán đủ số cổ phần đã đăng ký mua phải chịu trách nhiệm tương ứng với tổng mệnh giá cổ phần đã đăng ký mua đối với các nghĩa vụ tài chính của công ty"}
{"id": "ENT-01-D113-006", "type": "condition", "premises": ["must_complete_capital_contribution"], "conclusion": "company_member", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 113 khoản 5", "exception_to": "", "quote": "Người góp vốn trở thành cổ đông của công ty kể từ thời điểm đã thanh toán việc mua cổ phần"}


######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 120. Cổ phần phổ thông của cổ đông sáng lập
[NGUYÊN VĂN]
Điều 120. Cổ phần phổ thông của cổ đông sáng lập 
1. Công ty cổ phần mới thành lập phải có ít nhất 03 cổ đông sáng lập. Công ty cổ phần được 
chuyển đổi từ doanh nghiệp nhà nước hoặc từ công ty trách nhiệm hữu hạn hoặc được chia, tách, 
hợp nhất, sáp nhập từ công ty cổ phần khác không nhất thiết phải có cổ đông sáng lập; trường 
hợp này, Điều lệ công ty trong hồ sơ đăng ký doanh nghiệp phải có chữ ký của người đại diện 
theo pháp luật hoặc các cổ đông phổ thông của công ty đó. 
2. Các cổ đông sáng lập phải cùng nhau đăng ký mua ít nhất 20% tổng số cổ phần phổ thông 
được quyền chào bán khi đăng ký thành lập doanh nghiệp. 
3. Trong thời hạn 03 năm kể từ ngày công ty được cấp Giấy chứng nhận đăng ký doanh nghiệp, 
cổ phần phổ thông của cổ đông sáng lập được tự do chuyển nhượng cho cổ đông sáng lập khác 
và chỉ được chuyển nhượng cho người không phải là cổ đông sáng lập nếu được sự chấp thuận 
của Đại hội đồng cổ đông. Trường hợp này, cổ đông sáng lập dự định chuyển nhượng cổ phần 
phổ thông thì không có quyền biểu quyết về việc chuyển nhượng cổ phần đó. 
4. Các hạn chế quy định tại khoản 3 Điều này không áp dụng đối với cổ phần phổ thông sau đây: 
a) Cổ phần mà cổ đông sáng lập có thêm sau khi đăng ký thành lập doanh nghiệp; 
b) Cổ phần đã được chuyển nhượng cho người khác không phải là cổ đông sáng lập.

[RULES]
{"id": "ENT-01-D120-000", "type": "condition", "premises": ["has_minimum_3_shareholders"], "conclusion": "must_include_signatures_of_founders", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 120 khoản 1", "exception_to": "", "quote": "Công ty cổ phần mới thành lập phải có ít nhất 03 cổ đông sáng lập."}
{"id": "ENT-01-D120-001", "type": "condition", "premises": ["is_company_reorganization_decision"], "conclusion": "must_include_signature_of_owner_or_representative", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 120 khoản 1", "exception_to": "", "quote": "Công ty cổ phần được chuyển đổi từ doanh nghiệp nhà nước hoặc từ công ty trách nhiệm hữu hạn hoặc được chia, tách, hợp nhất, sáp nhập từ công ty cổ phần khác không nhất thiết phải có cổ đông sáng lập; trường hợp này, Điều lệ công ty trong hồ sơ đăng ký doanh nghiệp phải có chữ ký của người đại diện theo pháp luật hoặc các cổ đông phổ thông của công ty đó."}
{"id": "ENT-01-D120-002", "type": "condition", "premises": ["has_minimum_20_percent_shares"], "conclusion": "must_include_signatures_of_founders", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 120 khoản 2", "exception_to": "", "quote": "Các cổ đông sáng lập phải cùng nhau đăng ký mua ít nhất 20% tổng số cổ phần phổ thông được quyền chào bán khi đăng ký thành lập doanh nghiệp."}
{"id": "ENT-01-D120-003", "type": "condition", "premises": ["is_shareholder", "must_pass_resolution"], "conclusion": "can_transfer_to_non_members_after_offer", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 120 khoản 3", "exception_to": "", "quote": "Trong thời hạn 03 năm kể từ ngày công ty được cấp Giấy chứng nhận đăng ký doanh nghiệp, cổ phần phổ thông của cổ đông sáng lập được tự do chuyển nhượng cho cổ đông sáng lập khác và chỉ được chuyển nhượng cho người không phải là cổ đông sáng lập nếu được sự chấp thuận của Đại hội đồng cổ đông."}
{"id": "ENT-01-D120-004", "type": "condition", "premises": ["is_shareholder", "~can_vote_on_company_matters"], "conclusion": "must_not_vote_on_transfer", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 120 khoản 3", "exception_to": "", "quote": "Trường hợp này, cổ đông sáng lập dự định chuyển nhượng cổ phần phổ thông thì không có quyền biểu quyết về việc chuyển nhượng cổ phần đó."}
{"id": "ENT-01-D120-005", "type": "condition", "premises": ["is_shareholder", "~is_shareholder"], "conclusion": "must_not_apply_transfer_restrictions", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 120 khoản 4 điểm a", "exception_to": "Điều 120 khoản 3", "quote": "Các hạn chế quy định tại khoản 3 Điều này không áp dụng đối với cổ phần phổ thông sau đây: Cổ phần mà cổ đông sáng lập có thêm sau khi đăng ký thành lập doanh nghiệp."}
{"id": "ENT-01-D120-006", "type": "condition", "premises": ["~is_shareholder"], "conclusion": "must_not_apply_transfer_restrictions", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 120 khoản 4 điểm b", "exception_to": "Điều 120 khoản 3", "quote": "Các hạn chế quy định tại khoản 3 Điều này không áp dụng đối với cổ phần phổ thông sau đây: Cổ phần đã được chuyển nhượng cho người khác không phải là cổ đông sáng lập."}


######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 127. Chuyển nhượng cổ phần
[NGUYÊN VĂN]
Điều 127. Chuyển nhượng cổ phần 
1. Cổ phần được tự do chuyển nhượng, trừ trường hợp quy định tại khoản 3 Điều 120 của Luật 
này và Điều lệ công ty có quy định hạn chế chuyển nhượng cổ phần. Trường hợp Điều lệ công ty 
có quy định hạn chế về chuyển nhượng cổ phần thì các quy định này chỉ có hiệu lực khi được 
nêu rõ trong cổ phiếu của cổ phần tương ứng. 
2. Việc chuyển nhượng được thực hiện bằng hợp đồng hoặc giao dịch trên thị trường chứng 
khoán. Trường hợp chuyển nhượng bằng hợp đồng thì giấy tờ chuyển nhượng phải được bên 
chuyển nhượng và bên nhận chuyển nhượng hoặc người đại diện theo ủy quyền của họ ký. 
Trường hợp giao dịch trên thị trường chứng khoán thì trình tự, thủ tục chuyển nhượng được thực 
hiện theo quy định của pháp luật về chứng khoán. 
3. Trường hợp cổ đông là cá nhân chết thì người thừa kế theo di chúc hoặc theo pháp luật của cổ 
đông đó trở thành cổ đông của công ty. 
4. Trường hợp cổ đông là cá nhân chết mà không có người thừa kế, người thừa kế từ chối nhận 
thừa kế hoặc bị truất quyền thừa kế thì số cổ phần của cổ đông đó được giải quyết theo quy định 
của pháp luật về dân sự. 
5. Cổ đông có quyền tặng cho một phần hoặc toàn bộ cổ phần của mình tại công ty cho cá nhân, 
tổ chức khác; sử dụng cổ phần để trả nợ. Cá nhân, tổ chức được tặng cho hoặc nhận trả nợ bằng 
cổ phần sẽ trở thành cổ đông của công ty. 
6. Cá nhân, tổ chức nhận cổ phần trong các trường hợp quy định tại Điều này chỉ trở thành cổ 
đông công ty từ thời điểm các thông tin của họ quy định tại khoản 2 Điều 122 của Luật này được 
ghi đầy đủ vào sổ đăng ký cổ đông. 
7. Công ty phải đăng ký thay đổi cổ đông trong sổ đăng ký cổ đông theo yêu cầu của cổ đông có 
liên quan trong thời hạn 24 giờ kể từ khi nhận được yêu cầu theo quy định tại Điều lệ công ty.

[RULES]
{"id": "ENT-01-D127-000", "type": "condition", "premises": ["can_transfer_shares", "must_not_use_enterprise_info_for_personal_gain"], "conclusion": "can_transfer_capital", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 127 khoản 1", "exception_to": "", "quote": "Cổ phần được tự do chuyển nhượng, trừ trường hợp quy định tại khoản 3 Điều 120 của Luật này và Điều lệ công ty có quy định hạn chế chuyển nhượng cổ phần."}
{"id": "ENT-01-D127-001", "type": "condition", "premises": ["must_include_signature_of_owner_or_representative", "must_keep_rights_until_registration"], "conclusion": "must_register_change_if_one_member_left", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 127 khoản 1", "exception_to": "", "quote": "Trường hợp Điều lệ công ty có quy định hạn chế về chuyển nhượng cổ phần thì các quy định này chỉ có hiệu lực khi được nêu rõ trong cổ phiếu của cổ phần tương ứng."}
{"id": "ENT-01-D127-002", "type": "condition", "premises": ["can_transfer_shares", "must_include_signature_of_owner_or_representative"], "conclusion": "must_complete_capital_contribution", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 127 khoản 2", "exception_to": "", "quote": "Việc chuyển nhượng được thực hiện bằng hợp đồng hoặc giao dịch trên thị trường chứng khoán."}
{"id": "ENT-01-D127-003", "type": "condition", "premises": ["is_deceased_without_heir"], "conclusion": "must_follow_company_rules", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 127 khoản 3", "exception_to": "", "quote": "Trường hợp cổ đông là cá nhân chết thì người thừa kế theo di chúc hoặc theo pháp luật của cổ đông đó trở thành cổ đông của công ty."}
{"id": "ENT-01-D127-004", "type": "condition", "premises": ["is_deceased_without_heir"], "conclusion": "must_follow_company_rules", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 127 khoản 4", "exception_to": "", "quote": "Trường hợp cổ đông là cá nhân chết mà không có người thừa kế, người thừa kế từ chối nhận thừa kế hoặc bị truất quyền thừa kế thì số cổ phần của cổ đông đó được giải quyết theo quy định của pháp luật về dân sự."}
{"id": "ENT-01-D127-005", "type": "condition", "premises": ["can_transfer_shares"], "conclusion": "can_receive_profit", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 127 khoản 5", "exception_to": "", "quote": "Cổ đông có quyền tặng cho một phần hoặc toàn bộ cổ phần của mình tại công ty cho cá nhân, tổ chức khác; sử dụng cổ phần để trả nợ."}
{"id": "ENT-01-D127-006", "type": "condition", "premises": ["can_transfer_shares"], "conclusion": "must_keep_rights_until_registration", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 127 khoản 6", "exception_to": "", "quote": "Cá nhân, tổ chức nhận cổ phần trong các trường hợp quy định tại Điều này chỉ trở thành cổ đông công ty từ thời điểm các thông tin của họ quy định tại khoản 2 Điều 122 của Luật này được ghi đầy đủ vào sổ đăng ký cổ đông."}
{"id": "ENT-01-D127-007", "type": "condition", "premises": ["must_notify_enterprise_about_related_business"], "conclusion": "must_register_change_if_one_member_left", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 127 khoản 7", "exception_to": "", "quote": "Công ty phải đăng ký thay đổi cổ đông trong sổ đăng ký cổ đông theo yêu cầu của cổ đông có liên quan trong thời hạn 24 giờ kể từ khi nhận được yêu cầu theo quy định tại Điều lệ công ty."}


######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 188. Doanh nghiệp tư nhân
[NGUYÊN VĂN]
Điều 188. Doanh nghiệp tư nhân 
1. Doanh nghiệp tư nhân là doanh nghiệp do một cá nhân làm chủ và tự chịu trách nhiệm bằng 
toàn bộ tài sản của mình về mọi hoạt động của doanh nghiệp. 
2. Doanh nghiệp tư nhân không được phát hành bất kỳ loại chứng khoán nào. 
3. Mỗi cá nhân chỉ được quyền thành lập một doanh nghiệp tư nhân. Chủ doanh nghiệp tư nhân 
không được đồng thời là chủ hộ kinh doanh, thành viên hợp danh của công ty hợp danh. 
4. Doanh nghiệp tư nhân không được quyền góp vốn thành lập hoặc mua cổ phần, phần vốn góp 
trong công ty hợp danh, công ty trách nhiệm hữu hạn hoặc công ty cổ phần.

[RULES]
{"id": "ENT-01-D188-000", "type": "condition", "premises": ["is_individual_owner"], "conclusion": "must_be_fully_responsible", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 188 khoản 1", "exception_to": "", "quote": "Doanh nghiệp tư nhân là doanh nghiệp do một cá nhân làm chủ và tự chịu trách nhiệm bằng toàn bộ tài sản của mình về mọi hoạt động của doanh nghiệp."}
{"id": "ENT-01-D188-001", "type": "condition", "premises": [], "conclusion": "must_not_issue_securities", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 188 khoản 2", "exception_to": "", "quote": "Doanh nghiệp tư nhân không được phát hành bất kỳ loại chứng khoán nào."}
{"id": "ENT-01-D188-002", "type": "condition", "premises": ["is_individual_owner"], "conclusion": "must_not_have_multiple_private_enterprises", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 188 khoản 3", "exception_to": "", "quote": "Mỗi cá nhân chỉ được quyền thành lập một doanh nghiệp tư nhân."}
{"id": "ENT-01-D188-003", "type": "condition", "premises": ["is_private_enterprise_owner"], "conclusion": "must_not_be_business_household_owner", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 188 khoản 3", "exception_to": "", "quote": "Chủ doanh nghiệp tư nhân không được đồng thời là chủ hộ kinh doanh, thành viên hợp danh của công ty hợp danh."}
{"id": "ENT-01-D188-004", "type": "condition", "premises": ["is_private_enterprise"], "conclusion": "must_not_invest_in_partnership_or_limited_liability_company", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 188 khoản 4", "exception_to": "", "quote": "Doanh nghiệp tư nhân không được quyền góp vốn thành lập hoặc mua cổ phần, phần vốn góp trong công ty hợp danh, công ty trách nhiệm hữu hạn hoặc công ty cổ phần."}


######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 207. Các trường hợp và điều kiện giải thể doanh nghiệp
[NGUYÊN VĂN]
Điều 207. Các trường hợp và điều kiện giải thể doanh nghiệp 
1. Doanh nghiệp bị giải thể trong trường hợp sau đây: 
a) Kết thúc thời hạn hoạt động đã ghi trong Điều lệ công ty mà không có quyết định gia hạn; 
b) Theo nghị quyết, quyết định của chủ doanh nghiệp đối với doanh nghiệp tư nhân, của Hội 
đồng thành viên đối với công ty hợp danh, của Hội đồng thành viên, chủ sở hữu công ty đối với 
công ty trách nhiệm hữu hạn, của Đại hội đồng cổ đông đối với công ty cổ phần; 
c)[46] Công ty không còn đủ số lượng thành viên, cổ đông tối thiểu theo quy định của Luật này 
trong thời hạn 06 tháng liên tục mà không làm thủ tục chuyển đổi loại hình doanh nghiệp; 
d) Bị thu hồi Giấy chứng nhận đăng ký doanh nghiệp, trừ trường hợp Luật Quản lý thuế có quy 
định khác. 
2. Doanh nghiệp chỉ được giải thể khi bảo đảm thanh toán hết các khoản nợ, nghĩa vụ tài sản 
khác và không trong quá trình giải quyết tranh chấp tại Tòa án hoặc Trọng tài. Người quản lý có 
liên quan và doanh nghiệp quy định tại điểm d khoản 1 Điều này cùng liên đới chịu trách nhiệm 
về các khoản nợ của doanh nghiệp.

[RULES]
{"id": "ENT-01-D207-000", "type": "condition", "premises": ["~must_not_have_active_contracts", "~must_not_have_disputes"], "conclusion": "can_dissolve_company", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 207 khoản 1 điểm a", "exception_to": "", "quote": "Doanh nghiệp chỉ được giải thể khi bảo đảm thanh toán hết các khoản nợ, nghĩa vụ tài sản khác và không trong quá trình giải quyết tranh chấp tại Tòa án hoặc Trọng tài."}
{"id": "ENT-01-D207-001", "type": "condition", "premises": ["has_resolution_from_members_or_shareholders"], "conclusion": "can_dissolve_company", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 207 khoản 1 điểm b", "exception_to": "", "quote": "Theo nghị quyết, quyết định của chủ doanh nghiệp đối với doanh nghiệp tư nhân, của Hội đồng thành viên đối với công ty hợp danh, của Hội đồng thành viên, chủ sở hữu công ty đối với công ty trách nhiệm hữu hạn, của Đại hội đồng cổ đông đối với công ty cổ phần."}
{"id": "ENT-01-D207-002", "type": "condition", "premises": ["~must_not_have_minimum_members"], "conclusion": "can_dissolve_company", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 207 khoản 1 điểm c", "exception_to": "", "quote": "Công ty không còn đủ số lượng thành viên, cổ đông tối thiểu theo quy định của Luật này trong thời hạn 06 tháng liên tục mà không làm thủ tục chuyển đổi loại hình doanh nghiệp."}
{"id": "ENT-01-D207-003", "type": "condition", "premises": ["is_business_license_revoked"], "conclusion": "can_dissolve_company", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 207 khoản 1 điểm d", "exception_to": "Luật Quản lý thuế có quy định khác", "quote": "Bị thu hồi Giấy chứng nhận đăng ký doanh nghiệp, trừ trường hợp Luật Quản lý thuế có quy định khác."}


######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 27. Cấp Giấy chứng nhận đăng ký doanh nghiệp
[NGUYÊN VĂN]
Điều 27. Cấp Giấy chứng nhận đăng ký doanh nghiệp 
1. Doanh nghiệp được cấp Giấy chứng nhận đăng ký doanh nghiệp khi có đủ các điều kiện sau 
đây: 
a) Ngành, nghề đăng ký kinh doanh không bị cấm đầu tư kinh doanh; 
b) Tên của doanh nghiệp được đặt theo đúng quy định tại các điều 37, 38, 39 và 41 của Luật này; 
c) Có hồ sơ đăng ký doanh nghiệp hợp lệ; 
d) Nộp đủ lệ phí đăng ký doanh nghiệp theo quy định của pháp luật về phí và lệ phí. 
2. Trường hợp Giấy chứng nhận đăng ký doanh nghiệp bị mất, bị hư hỏng hoặc bị hủy hoại dưới 
hình thức khác, doanh nghiệp được cấp lại Giấy chứng nhận đăng ký doanh nghiệp và phải nộp 
lệ phí theo quy định của pháp luật.

[RULES]
{"id": "ENT-01-D27-000", "type": "condition", "premises": ["meets_investment_conditions", "must_provide_application_documents", "valid_application", "must_pay_taxes"], "conclusion": "is_registered_enterprise", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 27 khoản 1", "exception_to": "", "quote": "Doanh nghiệp được cấp Giấy chứng nhận đăng ký doanh nghiệp khi có đủ các điều kiện sau đây"}
{"id": "ENT-01-D27-001", "type": "condition", "premises": ["meets_investment_conditions"], "conclusion": "must_not_use_enterprise_info_for_personal_gain", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 27 khoản 1 điểm a", "exception_to": "", "quote": "Ngành, nghề đăng ký kinh doanh không bị cấm đầu tư kinh doanh"}
{"id": "ENT-01-D27-002", "type": "condition", "premises": ["must_provide_application_documents"], "conclusion": "must_define_representative_roles_in_charter", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 27 khoản 1 điểm b", "exception_to": "", "quote": "Tên của doanh nghiệp được đặt theo đúng quy định tại các điều 37, 38, 39 và 41 của Luật này"}
{"id": "ENT-01-D27-003", "type": "condition", "premises": ["valid_application"], "conclusion": "must_provide_application_documents", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 27 khoản 1 điểm c", "exception_to": "", "quote": "Có hồ sơ đăng ký doanh nghiệp hợp lệ"}
{"id": "ENT-01-D27-004", "type": "condition", "premises": ["must_pay_taxes"], "conclusion": "must_pay_taxes", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 27 khoản 1 điểm d", "exception_to": "", "quote": "Nộp đủ lệ phí đăng ký doanh nghiệp theo quy định của pháp luật về phí và lệ phí"}
{"id": "ENT-01-D27-005", "type": "condition", "premises": ["~is_registered_enterprise"], "conclusion": "is_registered_enterprise", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 27 khoản 2", "exception_to": "", "quote": "Trường hợp Giấy chứng nhận đăng ký doanh nghiệp bị mất, bị hư hỏng hoặc bị hủy hoại dưới hình thức khác, doanh nghiệp được cấp lại Giấy chứng nhận đăng ký doanh nghiệp"}


######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 30. Đăng ký thay đổi nội dung Giấy chứng nhận đăng ký doanh nghiệp
[NGUYÊN VĂN]
Điều 30. Đăng ký thay đổi nội dung Giấy chứng nhận đăng ký doanh nghiệp 
1. Doanh nghiệp phải đăng ký với Cơ quan đăng ký kinh doanh khi thay đổi nội dung Giấy 
chứng nhận đăng ký doanh nghiệp quy định tại Điều 28 của Luật này. 
2. Doanh nghiệp chịu trách nhiệm đăng ký thay đổi nội dung Giấy chứng nhận đăng ký doanh 
nghiệp trong thời hạn 10 ngày kể từ ngày có thay đổi. 
3. Trong thời hạn 03 ngày làm việc kể từ ngày nhận hồ sơ, Cơ quan đăng ký kinh doanh có trách 
nhiệm xem xét tính hợp lệ của hồ sơ và cấp Giấy chứng nhận đăng ký doanh nghiệp mới; trường 
hợp hồ sơ chưa hợp lệ, Cơ quan đăng ký kinh doanh phải thông báo bằng văn bản nội dung cần 
sửa đổi, bổ sung cho doanh nghiệp. Trường hợp từ chối cấp Giấy chứng nhận đăng ký doanh 
nghiệp mới thì phải thông báo bằng văn bản cho doanh nghiệp và nêu rõ lý do. 
4. Đăng ký thay đổi nội dung Giấy chứng nhận đăng ký doanh nghiệp theo quyết định của Tòa 
án hoặc Trọng tài thực hiện theo trình tự, thủ tục sau đây: 
a) Người đề nghị đăng ký thay đổi nội dung Giấy chứng nhận đăng ký doanh nghiệp gửi đề nghị 
đăng ký thay đổi đến Cơ quan đăng ký kinh doanh có thẩm quyền trong thời hạn 15 ngày kể từ 
ngày bản án, quyết định của Tòa án có hiệu lực pháp luật hoặc phán quyết của Trọng tài có hiệu 
lực. Kèm theo hồ sơ đăng ký phải gồm bản sao bản án, quyết định của Tòa án đã có hiệu lực 
pháp luật hoặc phán quyết của Trọng tài có hiệu lực; 
b) Trong thời hạn 03 ngày làm việc kể từ ngày nhận được đề nghị đăng ký quy định tại điểm a 
khoản này, Cơ quan đăng ký kinh doanh có trách nhiệm xem xét và cấp Giấy chứng nhận đăng 
ký doanh nghiệp mới theo nội dung bản án, quyết định của Tòa án đã có hiệu lực pháp luật hoặc 
phán quyết của Trọng tài có hiệu lực; trường hợp hồ sơ chưa hợp lệ, Cơ quan đăng ký kinh 
doanh phải thông báo bằng văn bản nội dung cần sửa đổi, bổ sung cho người đề nghị đăng ký 
thay đổi. Trường hợp từ chối cấp Giấy chứng nhận đăng ký doanh nghiệp mới thì phải thông báo 
bằng văn bản cho người đề nghị đăng ký thay đổi và nêu rõ lý do. 
5. Chính phủ quy định về hồ sơ, trình tự, thủ tục đăng ký thay đổi nội dung Giấy chứng nhận 
đăng ký doanh nghiệp.

[RULES]
{"id": "ENT-01-D30-000", "type": "condition", "premises": ["is_registered_enterprise", "~must_notify_authorities_on_goal_change"], "conclusion": "must_register_business", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 30 khoản 1", "exception_to": "", "quote": "Doanh nghiệp phải đăng ký với Cơ quan đăng ký kinh doanh khi thay đổi nội dung Giấy chứng nhận đăng ký doanh nghiệp."}
{"id": "ENT-01-D30-001", "type": "condition", "premises": ["must_register_business"], "conclusion": "must_submit_registration_within_10_days", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 30 khoản 2", "exception_to": "", "quote": "Doanh nghiệp chịu trách nhiệm đăng ký thay đổi nội dung Giấy chứng nhận đăng ký doanh nghiệp trong thời hạn 10 ngày kể từ ngày có thay đổi."}
{"id": "ENT-01-D30-002", "type": "condition", "premises": ["received_registration_documents"], "conclusion": "valid_application", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 30 khoản 3", "exception_to": "", "quote": "Trong thời hạn 03 ngày làm việc kể từ ngày nhận hồ sơ, Cơ quan đăng ký kinh doanh có trách nhiệm xem xét tính hợp lệ của hồ sơ."}
{"id": "ENT-01-D30-003", "type": "condition", "premises": ["~valid_application"], "conclusion": "must_notify_enterprise_about_related_business", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 30 khoản 3", "exception_to": "", "quote": "trường hợp hồ sơ chưa hợp lệ, Cơ quan đăng ký kinh doanh phải thông báo bằng văn bản nội dung cần sửa đổi, bổ sung cho doanh nghiệp."}
{"id": "ENT-01-D30-004", "type": "condition", "premises": ["must_register_business", "must_provide_documents_for_change_of_representative"], "conclusion": "must_submit_application_for_change", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 30 khoản 4 điểm a", "exception_to": "", "quote": "Người đề nghị đăng ký thay đổi nội dung Giấy chứng nhận đăng ký doanh nghiệp gửi đề nghị đăng ký thay đổi đến Cơ quan đăng ký kinh doanh có thẩm quyền trong thời hạn 15 ngày kể từ ngày bản án, quyết định của Tòa án có hiệu lực pháp luật hoặc phán quyết của Trọng tài có hiệu lực."}
{"id": "ENT-01-D30-005", "type": "condition", "premises": ["must_submit_application_for_change"], "conclusion": "valid_application", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 30 khoản 4 điểm b", "exception_to": "", "quote": "Trong thời hạn 03 ngày làm việc kể từ ngày nhận được đề nghị đăng ký quy định tại điểm a khoản này, Cơ quan đăng ký kinh doanh có trách nhiệm xem xét và cấp Giấy chứng nhận đăng ký doanh nghiệp mới."}


######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 35. Chuyển quyền sở hữu tài sản góp vốn
[NGUYÊN VĂN]
Điều 35. Chuyển quyền sở hữu tài sản góp vốn 
1. Thành viên công ty trách nhiệm hữu hạn, công ty hợp danh và cổ đông công ty cổ phần phải 
chuyển quyền sở hữu tài sản góp vốn cho công ty theo quy định sau đây: 
a) Đối với tài sản có đăng ký quyền sở hữu hoặc quyền sử dụng đất thì người góp vốn phải làm 
thủ tục chuyển quyền sở hữu tài sản đó hoặc quyền sử dụng đất cho công ty theo quy định của 
pháp luật. Việc chuyển quyền sở hữu, chuyển quyền sử dụng đất đối với tài sản góp vốn không 
phải chịu lệ phí trước bạ; 
b) Đối với tài sản không đăng ký quyền sở hữu, việc góp vốn phải được thực hiện bằng việc giao 
nhận tài sản góp vốn có xác nhận bằng biên bản, trừ trường hợp được thực hiện thông qua tài 
khoản. 
2. Biên bản giao nhận tài sản góp vốn phải bao gồm các nội dung chủ yếu sau đây: 
a) Tên, địa chỉ trụ sở chính của công ty; 
b) Họ, tên, địa chỉ liên lạc, số giấy tờ pháp lý của cá nhân, số giấy tờ pháp lý của tổ chức của 
người góp vốn; 
c) Loại tài sản và số đơn vị tài sản góp vốn; tổng giá trị tài sản góp vốn và tỷ lệ của tổng giá trị 
tài sản đó trong vốn điều lệ của công ty; 
d) Ngày giao nhận; chữ ký của người góp vốn hoặc người đại diện theo ủy quyền của người góp 
vốn và người đại diện theo pháp luật của công ty. 
3. Việc góp vốn chỉ được coi là thanh toán xong khi quyền sở hữu hợp pháp đối với tài sản góp 
vốn đã chuyển sang công ty. 
4. Tài sản được sử dụng vào hoạt động kinh doanh của chủ doanh nghiệp tư nhân không phải làm 
thủ tục chuyển quyền sở hữu cho doanh nghiệp. 
5. Việc thanh toán đối với mọi hoạt động mua, bán, chuyển nhượng cổ phần và phần vốn góp, 
nhận cổ tức và chuyển lợi nhuận ra nước ngoài của nhà đầu tư nước ngoài đều phải được thực 
hiện thông qua tài khoản theo quy định của pháp luật về quản lý ngoại hối, trừ trường hợp thanh 
toán bằng tài sản và hình thức khác không bằng tiền mặt.

[RULES]
{"id": "ENT-01-D35-000", "type": "condition", "premises": ["is_registered_capital"], "conclusion": "must_transfer_property_ownership", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 35 khoản 1 điểm a", "exception_to": "", "quote": "Đối với tài sản có đăng ký quyền sở hữu hoặc quyền sử dụng đất thì người góp vốn phải làm thủ tục chuyển quyền sở hữu tài sản đó hoặc quyền sử dụng đất cho công ty theo quy định của pháp luật."}
{"id": "ENT-01-D35-001", "type": "condition", "premises": ["~is_registered_capital"], "conclusion": "must_transfer_property_by_hand_over", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 35 khoản 1 điểm a", "exception_to": "", "quote": "Đối với tài sản không đăng ký quyền sở hữu, việc góp vốn phải được thực hiện bằng việc giao nhận tài sản góp vốn có xác nhận bằng biên bản, trừ trường hợp được thực hiện thông qua tài khoản."}
{"id": "ENT-01-D35-002", "type": "condition", "premises": ["must_include_headquarters_address", "must_include_member_info", "must_include_capital_contribution_info", "must_include_share_info", "must_include_representative_info"], "conclusion": "must_include_property_transfer_document_info", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 35 khoản 2", "exception_to": "", "quote": "Biên bản giao nhận tài sản góp vốn phải bao gồm các nội dung chủ yếu sau đây: tên, địa chỉ trụ sở chính của công ty; họ, tên, địa chỉ liên lạc, số giấy tờ pháp lý của cá nhân, số giấy tờ pháp lý của tổ chức của người góp vốn; loại tài sản và số đơn vị tài sản góp vốn; tổng giá trị tài sản góp vốn và tỷ lệ của tổng giá trị tài sản đó trong vốn điều lệ của công ty; ngày giao nhận; chữ ký của người g"}
{"id": "ENT-01-D35-003", "type": "condition", "premises": ["must_transfer_property_ownership"], "conclusion": "must_complete_capital_contribution", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 35 khoản 3", "exception_to": "", "quote": "Việc góp vốn chỉ được coi là thanh toán xong khi quyền sở hữu hợp pháp đối với tài sản góp vốn đã chuyển sang công ty."}
{"id": "ENT-01-D35-004", "type": "condition", "premises": ["is_state_owned_member"], "conclusion": "must_not_transfer_property_ownership", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 35 khoản 4", "exception_to": "", "quote": "Tài sản được sử dụng vào hoạt động kinh doanh của chủ doanh nghiệp tư nhân không phải làm thủ tục chuyển quyền sở hữu cho doanh nghiệp."}
{"id": "ENT-01-D35-005", "type": "condition", "premises": [], "conclusion": "must_use_account_for_investor_transactions", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 35 khoản 5", "exception_to": "", "quote": "Việc thanh toán đối với mọi hoạt động mua, bán, chuyển nhượng cổ phần và phần vốn góp, nhận cổ tức và chuyển lợi nhuận ra nước ngoài của nhà đầu tư nước ngoài đều phải được thực hiện thông qua tài khoản theo quy định của pháp luật về quản lý ngoại hối, trừ trường hợp thanh toán bằng tài sản và hình thức khác không bằng tiền mặt."}


######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 38. Những điều cấm trong đặt tên doanh nghiệp
[NGUYÊN VĂN]
Điều 38. Những điều cấm trong đặt tên doanh nghiệp 
1. Đặt tên trùng hoặc tên gây nhầm lẫn với tên của doanh nghiệp đã đăng ký được quy định tại 
Điều 41 của Luật này. 
2. Sử dụng tên cơ quan nhà nước, đơn vị lực lượng vũ trang nhân dân, tên của tổ chức chính trị, 
tổ chức chính trị - xã hội, tổ chức chính trị xã hội - nghề nghiệp, tổ chức xã hội, tổ chức xã hội - 
nghề nghiệp để làm toàn bộ hoặc một phần tên riêng của doanh nghiệp, trừ trường hợp có sự 
chấp thuận của cơ quan, đơn vị hoặc tổ chức đó. 
3. Sử dụng từ ngữ, ký hiệu vi phạm truyền thống lịch sử, văn hóa, đạo đức và thuần phong mỹ 
tục của dân tộc.

[RULES]
{"id": "ENT-01-D38-000", "type": "condition", "premises": ["must_not_use_duplicate_or_confusing_name"], "conclusion": "is_invalid_enterprise_name", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 38 khoản 1", "exception_to": "", "quote": "Đặt tên trùng hoặc tên gây nhầm lẫn với tên của doanh nghiệp đã đăng ký"}
{"id": "ENT-01-D38-001", "type": "condition", "premises": ["must_not_use_state_agency_name"], "conclusion": "is_invalid_enterprise_name", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 38 khoản 2", "exception_to": "", "quote": "Sử dụng tên cơ quan nhà nước, đơn vị lực lượng vũ trang nhân dân, tên của tổ chức chính trị... để làm toàn bộ hoặc một phần tên riêng của doanh nghiệp"}
{"id": "ENT-01-D38-002", "type": "condition", "premises": ["must_not_use_offensive_language"], "conclusion": "is_invalid_enterprise_name", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 38 khoản 3", "exception_to": "", "quote": "Sử dụng từ ngữ, ký hiệu vi phạm truyền thống lịch sử, văn hóa, đạo đức và thuần phong mỹ tục của dân tộc"}


######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 46. Công ty trách nhiệm hữu hạn hai thành viên trở lên
[NGUYÊN VĂN]
Điều 46. Công ty trách nhiệm hữu hạn hai thành viên trở lên 
1. Công ty trách nhiệm hữu hạn hai thành viên trở lên là doanh nghiệp có từ 02 đến 50 thành viên 
là tổ chức, cá nhân. Thành viên chịu trách nhiệm về các khoản nợ và nghĩa vụ tài sản khác của 
doanh nghiệp trong phạm vi số vốn đã góp vào doanh nghiệp, trừ trường hợp quy định tại khoản 
4 Điều 47 của Luật này. Phần vốn góp của thành viên chỉ được chuyển nhượng theo quy định tại 
các điều 51, 52 và 53 của Luật này. 
2. Công ty trách nhiệm hữu hạn hai thành viên trở lên có tư cách pháp nhân kể từ ngày được cấp 
Giấy chứng nhận đăng ký doanh nghiệp. 
3. Công ty trách nhiệm hữu hạn hai thành viên trở lên không được phát hành cổ phần, trừ trường 
hợp để chuyển đổi thành công ty cổ phần. 
4. Công ty trách nhiệm hữu hạn hai thành viên trở lên được phát hành trái phiếu theo quy định 
của Luật này và quy định khác của pháp luật có liên quan; việc phát hành trái phiếu riêng lẻ phải 
tuân thủ quy định tại Điều 128 và Điều 129 của Luật này.

[RULES]
{"id": "ENT-01-D46-000", "type": "condition", "premises": ["is_llc_member", "~must_not_transfer_property_ownership"], "conclusion": "must_complete_capital_contribution", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 46 khoản 1", "exception_to": "", "quote": "Thành viên chịu trách nhiệm về các khoản nợ và nghĩa vụ tài sản khác của doanh nghiệp trong phạm vi số vốn đã góp vào doanh nghiệp."}
{"id": "ENT-01-D46-001", "type": "condition", "premises": ["is_llc_member", "is_registered_enterprise"], "conclusion": "is_responsible_for_enterprise_damage", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 46 khoản 1", "exception_to": "", "quote": "Thành viên chịu trách nhiệm về các khoản nợ và nghĩa vụ tài sản khác của doanh nghiệp."}
{"id": "ENT-01-D46-002", "type": "condition", "premises": ["is_registered_enterprise"], "conclusion": "can_hire_workers", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 46 khoản 2", "exception_to": "", "quote": "Công ty trách nhiệm hữu hạn hai thành viên trở lên có tư cách pháp nhân kể từ ngày được cấp Giấy chứng nhận đăng ký doanh nghiệp."}
{"id": "ENT-01-D46-003", "type": "condition", "premises": ["is_llc_member"], "conclusion": "must_not_transfer_property_ownership", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 46 khoản 3", "exception_to": "", "quote": "Công ty trách nhiệm hữu hạn hai thành viên trở lên không được phát hành cổ phần."}
{"id": "ENT-01-D46-004", "type": "condition", "premises": ["is_llc_member"], "conclusion": "can_export_import_business", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 46 khoản 4", "exception_to": "", "quote": "Công ty trách nhiệm hữu hạn hai thành viên trở lên được phát hành trái phiếu theo quy định của Luật này."}


######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 47. Góp vốn thành lập công ty và cấp giấy chứng nhận phần vốn góp
[NGUYÊN VĂN]
Điều 47. Góp vốn thành lập công ty và cấp giấy chứng nhận phần vốn góp 
1. Vốn điều lệ của công ty trách nhiệm hữu hạn hai thành viên trở lên khi đăng ký thành lập 
doanh nghiệp là tổng giá trị phần vốn góp của các thành viên cam kết góp và ghi trong Điều lệ 
công ty. 
2. Thành viên phải góp vốn cho công ty đủ và đúng loại tài sản đã cam kết khi đăng ký thành lập 
doanh nghiệp trong thời hạn 90 ngày kể từ ngày được cấp Giấy chứng nhận đăng ký doanh 
nghiệp, không kể thời gian vận chuyển, nhập khẩu tài sản góp vốn, thực hiện thủ tục hành chính 
để chuyển quyền sở hữu tài sản. Trong thời hạn này, thành viên có các quyền và nghĩa vụ tương 
ứng với tỷ lệ phần vốn góp đã cam kết. Thành viên công ty chỉ được góp vốn cho công ty bằng 
loại tài sản khác với tài sản đã cam kết nếu được sự tán thành của trên 50% số thành viên còn lại. 
3. Sau thời hạn quy định tại khoản 2 Điều này mà vẫn có thành viên chưa góp vốn hoặc chưa góp 
đủ phần vốn góp đã cam kết thì được xử lý như sau: 
a) Thành viên chưa góp vốn theo cam kết đương nhiên không còn là thành viên của công ty; 
b) Thành viên chưa góp đủ phần vốn góp đã cam kết có các quyền tương ứng với phần vốn góp 
đã góp; 
c) Phần vốn góp chưa góp của các thành viên được chào bán theo nghị quyết, quyết định của Hội 
đồng thành viên. 
4. Trường hợp có thành viên chưa góp vốn hoặc chưa góp đủ số vốn đã cam kết, công ty phải 
đăng ký thay đổi vốn điều lệ, tỷ lệ phần vốn góp của các thành viên bằng số vốn đã góp trong 
thời hạn 30 ngày kể từ ngày cuối cùng phải góp đủ phần vốn góp theo quy định tại khoản 2 Điều 
này. Các thành viên chưa góp vốn hoặc chưa góp đủ số vốn đã cam kết phải chịu trách nhiệm 
tương ứng với tỷ lệ phần vốn góp đã cam kết đối với các nghĩa vụ tài chính của công ty phát sinh 
trong thời gian trước ngày công ty đăng ký thay đổi vốn điều lệ và tỷ lệ phần vốn góp của thành 
viên. 
5. Trừ trường hợp quy định tại khoản 2 Điều này, người góp vốn trở thành thành viên của công 
ty kể từ thời điểm đã thanh toán phần vốn góp và những thông tin về người góp vốn quy định tại 
các điểm b, c và đ khoản 2 Điều 48 của Luật này được ghi đầy đủ vào sổ đăng ký thành viên. Tại 
thời điểm góp đủ phần vốn góp, công ty phải cấp giấy chứng nhận phần vốn góp cho thành viên 
tương ứng với giá trị phần vốn đã góp. 
6. Giấy chứng nhận phần vốn góp phải bao gồm các nội dung chủ yếu sau đây: 
a) Tên, mã số doanh nghiệp, địa chỉ trụ sở chính của công ty; 
b) Vốn điều lệ của công ty; 
c) Họ, tên, địa chỉ liên lạc, quốc tịch, số giấy tờ pháp lý của cá nhân đối với thành viên là cá 
nhân; tên, mã số doanh nghiệp hoặc số giấy tờ pháp lý của tổ chức, địa chỉ trụ sở chính đối với 
thành viên là tổ chức; 
d) Phần vốn góp, tỷ lệ phần vốn góp của thành viên; 
đ) Số và ngày cấp giấy chứng nhận phần vốn góp; 
e) Họ, tên, chữ ký của người đại diện theo pháp luật của công ty. 
7. Trường hợp giấy chứng nhận phần vốn góp bị mất, bị hư hỏng hoặc bị hủy hoại dưới hình 
thức khác, thành viên được công ty cấp lại giấy chứng nhận phần vốn góp theo trình tự, thủ tục 
quy định tại Điều lệ công ty.

[RULES]
{"id": "ENT-01-D47-000", "type": "condition", "premises": ["is_registered_capital", "capital_contribution"], "conclusion": "must_include_charter_capital", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 47 khoản 1", "exception_to": "", "quote": "Vốn điều lệ của công ty trách nhiệm hữu hạn hai thành viên trở lên khi đăng ký thành lập doanh nghiệp là tổng giá trị phần vốn góp của các thành viên cam kết góp và ghi trong Điều lệ công ty."}
{"id": "ENT-01-D47-001", "type": "condition", "premises": ["must_complete_capital_contribution", "is_registered_enterprise"], "conclusion": "must_fulfill_other_legal_obligations", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 47 khoản 2", "exception_to": "", "quote": "Thành viên phải góp vốn cho công ty đủ và đúng loại tài sản đã cam kết khi đăng ký thành lập doanh nghiệp trong thời hạn 90 ngày kể từ ngày được cấp Giấy chứng nhận đăng ký doanh nghiệp."}
{"id": "ENT-01-D47-002", "type": "condition", "premises": ["is_registered_enterprise", "must_get_approval_from_members"], "conclusion": "must_transfer_property_ownership", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 47 khoản 2", "exception_to": "", "quote": "Thành viên công ty chỉ được góp vốn cho công ty bằng loại tài sản khác với tài sản đã cam kết nếu được sự tán thành của trên 50% số thành viên còn lại."}
{"id": "ENT-01-D47-003", "type": "condition", "premises": ["~must_complete_capital_contribution"], "conclusion": "must_notify_enterprise_about_related_business", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 47 khoản 3", "exception_to": "", "quote": "Sau thời hạn quy định tại khoản 2 Điều này mà vẫn có thành viên chưa góp vốn hoặc chưa góp đủ phần vốn góp đã cam kết thì được xử lý như sau: Thành viên chưa góp vốn theo cam kết đương nhiên không còn là thành viên của công ty."}
{"id": "ENT-01-D47-004", "type": "condition", "premises": ["~must_complete_capital_contribution"], "conclusion": "must_register_business", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 47 khoản 4", "exception_to": "", "quote": "Trường hợp có thành viên chưa góp vốn hoặc chưa góp đủ số vốn đã cam kết, công ty phải đăng ký thay đổi vốn điều lệ."}
{"id": "ENT-01-D47-005", "type": "condition", "premises": ["must_complete_capital_contribution"], "conclusion": "must_provide_capital_info", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 47 khoản 5", "exception_to": "", "quote": "Người góp vốn trở thành thành viên của công ty kể từ thời điểm đã thanh toán phần vốn góp."}
{"id": "ENT-01-D47-006", "type": "condition", "premises": ["must_complete_capital_contribution"], "conclusion": "must_include_property_transfer_document_info", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 47 khoản 6", "exception_to": "", "quote": "Giấy chứng nhận phần vốn góp phải bao gồm các nội dung chủ yếu sau đây: Tên, mã số doanh nghiệp, địa chỉ trụ sở chính của công ty."}
{"id": "ENT-01-D47-007", "type": "condition", "premises": ["~must_complete_capital_contribution"], "conclusion": "must_provide_capital_info", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 47 khoản 7", "exception_to": "", "quote": "Trường hợp giấy chứng nhận phần vốn góp bị mất, bị hư hỏng hoặc bị hủy hoại dưới hình thức khác, thành viên được công ty cấp lại giấy chứng nhận phần vốn góp."}


######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 74. Công ty trách nhiệm hữu hạn một thành viên
[NGUYÊN VĂN]
Điều 74. Công ty trách nhiệm hữu hạn một thành viên 
1. Công ty trách nhiệm hữu hạn một thành viên là doanh nghiệp do một tổ chức hoặc một cá 
nhân làm chủ sở hữu (sau đây gọi là chủ sở hữu công ty). Chủ sở hữu công ty chịu trách nhiệm 
về các khoản nợ và nghĩa vụ tài sản khác của công ty trong phạm vi số vốn điều lệ của công ty. 
2. Công ty trách nhiệm hữu hạn một thành viên có tư cách pháp nhân kể từ ngày được cấp Giấy 
chứng nhận đăng ký doanh nghiệp. 
3. Công ty trách nhiệm hữu hạn một thành viên không được phát hành cổ phần, trừ trường hợp 
để chuyển đổi thành công ty cổ phần. 
4. Công ty trách nhiệm hữu hạn một thành viên được phát hành trái phiếu theo quy định của Luật 
này và quy định khác của pháp luật có liên quan; việc phát hành trái phiếu riêng lẻ theo quy định 
tại Điều 128 và Điều 129 của Luật này.

[RULES]
{"id": "ENT-01-D74-000", "type": "condition", "premises": ["is_llc_member"], "conclusion": "enterprise_definition", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 74 khoản 1", "exception_to": "", "quote": "Công ty trách nhiệm hữu hạn một thành viên là doanh nghiệp do một tổ chức hoặc một cá nhân làm chủ sở hữu."}
{"id": "ENT-01-D74-001", "type": "condition", "premises": ["is_llc_member"], "conclusion": "must_include_signature_of_owner_or_representative", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 74 khoản 1", "exception_to": "", "quote": "Chủ sở hữu công ty chịu trách nhiệm về các khoản nợ và nghĩa vụ tài sản khác của công ty trong phạm vi số vốn điều lệ của công ty."}
{"id": "ENT-01-D74-002", "type": "condition", "premises": ["is_llc_member"], "conclusion": "is_registered_capital", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 74 khoản 2", "exception_to": "", "quote": "Công ty trách nhiệm hữu hạn một thành viên có tư cách pháp nhân kể từ ngày được cấp Giấy chứng nhận đăng ký doanh nghiệp."}
{"id": "ENT-01-D74-003", "type": "condition", "premises": ["is_llc_member"], "conclusion": "~must_not_transfer_property_ownership", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 74 khoản 3", "exception_to": "", "quote": "Công ty trách nhiệm hữu hạn một thành viên không được phát hành cổ phần, trừ trường hợp để chuyển đổi thành công ty cổ phần."}
{"id": "ENT-01-D74-004", "type": "condition", "premises": ["is_llc_member"], "conclusion": "can_issue_bonds", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 74 khoản 4", "exception_to": "", "quote": "Công ty trách nhiệm hữu hạn một thành viên được phát hành trái phiếu theo quy định của Luật này và quy định khác của pháp luật có liên quan."}


######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 75. Góp vốn thành lập công ty
[NGUYÊN VĂN]
Điều 75. Góp vốn thành lập công ty 
1. Vốn điều lệ của công ty trách nhiệm hữu hạn một thành viên khi đăng ký thành lập doanh 
nghiệp là tổng giá trị tài sản do chủ sở hữu công ty cam kết góp và ghi trong Điều lệ công ty. 
2. Chủ sở hữu công ty phải góp vốn cho công ty đủ và đúng loại tài sản đã cam kết khi đăng ký 
thành lập doanh nghiệp trong thời hạn 90 ngày kể từ ngày được cấp Giấy chứng nhận đăng ký 
doanh nghiệp, không kể thời gian vận chuyển, nhập khẩu tài sản góp vốn, thực hiện thủ tục hành 
chính để chuyển quyền sở hữu tài sản. Trong thời hạn này, chủ sở hữu công ty có các quyền và 
nghĩa vụ tương ứng với phần vốn góp đã cam kết. 
3. Trường hợp không góp đủ vốn điều lệ trong thời hạn quy định tại khoản 2 Điều này, chủ sở 
hữu công ty phải đăng ký thay đổi vốn điều lệ bằng giá trị số vốn đã góp trong thời hạn 30 ngày 
kể từ ngày cuối cùng phải góp đủ vốn điều lệ. Trường hợp này, chủ sở hữu phải chịu trách nhiệm 
tương ứng với phần vốn góp đã cam kết đối với các nghĩa vụ tài chính của công ty phát sinh 
trong thời gian trước ngày cuối cùng công ty đăng ký thay đổi vốn điều lệ theo quy định tại 
khoản này. 
4. Chủ sở hữu công ty chịu trách nhiệm bằng toàn bộ tài sản của mình đối với các nghĩa vụ tài 
chính của công ty, thiệt hại xảy ra do không góp, không góp đủ, không góp đúng hạn vốn điều lệ 
theo quy định tại Điều này.

[RULES]
{"id": "ENT-01-D75-000", "type": "condition", "premises": ["is_registered_capital"], "conclusion": "must_include_signature_of_owner_or_representative", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 75 khoản 1", "exception_to": "", "quote": "Vốn điều lệ của công ty trách nhiệm hữu hạn một thành viên khi đăng ký thành lập doanh nghiệp là tổng giá trị tài sản do chủ sở hữu công ty cam kết góp và ghi trong Điều lệ công ty."}
{"id": "ENT-01-D75-001", "type": "condition", "premises": ["is_registered_capital", "must_complete_capital_contribution"], "conclusion": "must_transfer_property_ownership", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 75 khoản 2", "exception_to": "", "quote": "Chủ sở hữu công ty phải góp vốn cho công ty đủ và đúng loại tài sản đã cam kết khi đăng ký thành lập doanh nghiệp trong thời hạn 90 ngày kể từ ngày được cấp Giấy chứng nhận đăng ký doanh nghiệp."}
{"id": "ENT-01-D75-002", "type": "condition", "premises": ["~must_complete_capital_contribution"], "conclusion": "must_contribute_difference", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 75 khoản 3", "exception_to": "", "quote": "Trường hợp không góp đủ vốn điều lệ trong thời hạn quy định tại khoản 2 Điều này, chủ sở hữu công ty phải đăng ký thay đổi vốn điều lệ bằng giá trị số vốn đã góp trong thời hạn 30 ngày kể từ ngày cuối cùng phải góp đủ vốn điều lệ."}
{"id": "ENT-01-D75-003", "type": "condition", "premises": ["~must_complete_capital_contribution"], "conclusion": "is_responsible_for_enterprise_damage", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 75 khoản 4", "exception_to": "", "quote": "Chủ sở hữu công ty chịu trách nhiệm bằng toàn bộ tài sản của mình đối với các nghĩa vụ tài chính của công ty, thiệt hại xảy ra do không góp, không góp đủ, không góp đúng hạn vốn điều lệ theo quy định tại Điều này."}
