

######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 111. Công ty cổ phần
[NGUYÊN VĂN]
Điều 111. Công ty cổ phần 
1. Công ty cổ phần là doanh nghiệp, trong đó: 
a) Vốn điều lệ được chia thành nhiều phần bằng nhau gọi là cổ phần; 
b) Cổ đông có thể là tổ chức, cá nhân; số lượng cổ đông tối thiểu là 03 và không hạn chế số 
lượng tối đa; 
c) Cổ đông chỉ chịu trách nhiệm về các khoản nợ và nghĩa vụ tài sản khác của doanh nghiệp 
trong phạm vi số vốn đã góp vào doanh nghiệp; 
d) Cổ đông có quyền tự do chuyển nhượng cổ phần của mình cho người khác, trừ trường hợp 
quy định tại khoản 3 Điều 120 và khoản 1 Điều 127 của Luật này. 
2. Công ty cổ phần có tư cách pháp nhân kể từ ngày được cấp Giấy chứng nhận đăng ký doanh 
nghiệp. 
3. Công ty cổ phần có quyền phát hành cổ phần, trái phiếu và các loại chứng khoán khác của 
công ty.

[RULES]
{"id": "ENT-01-D111-000", "type": "condition", "premises": ["is_registered_enterprise", "is_shareholder"], "conclusion": "can_issue_bonds", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 111 khoản 1 điểm a", "exception_to": "", "quote": "Công ty cổ phần có quyền phát hành cổ phần, trái phiếu và các loại chứng khoán khác của công ty."}
{"id": "ENT-01-D111-001", "type": "condition", "premises": ["is_registered_enterprise", "is_shareholder", "has_minimum_3_shareholders"], "conclusion": "can_transfer_shares", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 111 khoản 1 điểm b", "exception_to": "", "quote": "Cổ đông có thể là tổ chức, cá nhân; số lượng cổ đông tối thiểu là 03 và không hạn chế số lượng tối đa."}
{"id": "ENT-01-D111-002", "type": "condition", "premises": ["is_registered_enterprise", "is_shareholder"], "conclusion": "is_responsible_for_enterprise_damage", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 111 khoản 1 điểm c", "exception_to": "", "quote": "Cổ đông chỉ chịu trách nhiệm về các khoản nợ và nghĩa vụ tài sản khác của doanh nghiệp trong phạm vi số vốn đã góp vào doanh nghiệp."}
{"id": "ENT-01-D111-003", "type": "condition", "premises": ["is_registered_enterprise", "is_shareholder"], "conclusion": "can_transfer_capital", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 111 khoản 1 điểm d", "exception_to": "khoản 3 Điều 120 và khoản 1 Điều 127 của Luật này", "quote": "Cổ đông có quyền tự do chuyển nhượng cổ phần của mình, trừ trường hợp quy định tại khoản 3 Điều 120 và khoản 1 Điều 127 của Luật này."}
{"id": "ENT-01-D111-004", "type": "condition", "premises": ["is_registered_enterprise"], "conclusion": "has_legal_status", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 111 khoản 2", "exception_to": "", "quote": "Công ty cổ phần có tư cách pháp nhân kể từ ngày được cấp Giấy chứng nhận đăng ký doanh nghiệp."}


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


######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 4. Giải thích từ ngữ
[NGUYÊN VĂN]
Điều 4. Giải thích từ ngữ 
Trong Luật này, các từ ngữ dưới đây được hiểu như sau: 
1. Bản sao là giấy tờ được sao từ sổ gốc hoặc được chứng thực từ bản chính bởi cơ quan, tổ chức 
có thẩm quyền hoặc đã được đối chiếu với bản chính. 
2. Cá nhân nước ngoài là người mang giấy tờ xác định quốc tịch nước ngoài. 
3. Cổ đông là cá nhân, tổ chức sở hữu ít nhất một cổ phần của công ty cổ phần. 
4. Cổ đông sáng lập là cổ đông sở hữu ít nhất một cổ phần phổ thông và ký tên trong danh sách 
cổ đông sáng lập công ty cổ phần. 
5.[2] Cổ tức là khoản lợi nhuận sau thuế được trả cho mỗi cổ phần bằng tiền hoặc bằng tài sản 
khác. 
6. Công ty bao gồm công ty trách nhiệm hữu hạn, công ty cổ phần và công ty hợp danh. 
7. Công ty trách nhiệm hữu hạn bao gồm công ty trách nhiệm hữu hạn một thành viên và công ty 
trách nhiệm hữu hạn hai thành viên trở lên. 
8. Cổng thông tin quốc gia về đăng ký doanh nghiệp là cổng thông tin điện tử được sử dụng để 
đăng ký doanh nghiệp qua mạng thông tin điện tử, công bố thông tin về đăng ký doanh nghiệp và 
truy cập thông tin về đăng ký doanh nghiệp. 
9. Cơ sở dữ liệu quốc gia về đăng ký doanh nghiệp là tập hợp dữ liệu về đăng ký doanh nghiệp 
trên phạm vi toàn quốc. 
10. Doanh nghiệp là tổ chức có tên riêng, có tài sản, có trụ sở giao dịch, được thành lập hoặc 
đăng ký thành lập theo quy định của pháp luật nhằm mục đích kinh doanh. 
11. Doanh nghiệp nhà nước bao gồm các doanh nghiệp do Nhà nước nắm giữ trên 50% vốn điều 
lệ, tổng số cổ phần có quyền biểu quyết theo quy định tại Điều 88 của Luật này. 
12. Doanh nghiệp Việt Nam là doanh nghiệp được thành lập hoặc đăng ký thành lập theo quy 
định của pháp luật Việt Nam và có trụ sở chính tại Việt Nam. 
13. Địa chỉ liên lạc là địa chỉ đăng ký trụ sở chính đối với tổ chức; địa chỉ thường trú hoặc nơi 
làm việc hoặc địa chỉ khác của cá nhân mà người đó đăng ký với doanh nghiệp để làm địa chỉ 
liên lạc. 
14.[3] Giá thị trường của phần vốn góp hoặc cổ phần là: 
a) Giá giao dịch bình quân trong vòng 30 ngày liền kề trước ngày xác định giá hoặc giá thỏa 
thuận giữa người bán và người mua hoặc giá do một tổ chức thẩm định giá xác định đối với cổ 
phiếu niêm yết, đăng ký giao dịch trên hệ thống giao dịch chứng khoán; 
b) Giá giao dịch trên thị trường tại thời điểm liền kề trước đó hoặc giá thỏa thuận giữa người bán 
và người mua hoặc giá do một tổ chức thẩm định giá xác định đối với phần vốn góp hoặc cổ 
phần không thuộc điểm a khoản này. 
15. Giấy chứng nhận đăng ký doanh nghiệp là văn bản bằng bản giấy hoặc bản điện tử ghi lại 
những thông tin về đăng ký doanh nghiệp mà Cơ quan đăng ký kinh doanh cấp cho doanh 
nghiệp. 
16.[4] Giấy tờ pháp lý của cá nhân là một trong các loại giấy tờ sau đây: thẻ Căn cước, thẻ Căn 
cước công dân, Hộ chiếu, giấy tờ chứng thực cá nhân hợp pháp khác. 
17. Giấy tờ pháp lý của tổ chức là một trong các loại giấy tờ sau đây: Quyết định thành lập, Giấy 
chứng nhận đăng ký doanh nghiệp, tài liệu tương đương khác. 
18. Góp vốn là việc góp tài sản để tạo thành vốn điều lệ của công ty, bao gồm góp vốn để thành 
lập công ty hoặc góp thêm vốn điều lệ của công ty đã được thành lập. 
19. Hệ thống thông tin quốc gia về đăng ký doanh nghiệp bao gồm Cổng thông tin quốc gia về 
đăng ký doanh nghiệp, Cơ sở dữ liệu quốc gia về đăng ký doanh nghiệp, cơ sở dữ liệu liên quan 
và hạ tầng kỹ thuật hệ thống. 
20. Hồ sơ hợp lệ là hồ sơ có đầy đủ giấy tờ theo quy định của Luật này và nội dung các giấy tờ 
đó được kê khai đầy đủ theo quy định của pháp luật. 
21. Kinh doanh là việc thực hiện liên tục một, một số hoặc tất cả công đoạn của quá trình từ đầu 
tư, sản xuất đến tiêu thụ sản phẩm hoặc cung ứng dịch vụ trên thị trường nhằm mục đích tìm 
kiếm lợi nhuận. 
22. Người có quan hệ gia đình bao gồm: vợ, chồng, bố đẻ, mẹ đẻ, bố nuôi, mẹ nuôi, bố chồng, 
mẹ chồng, bố vợ, mẹ vợ, con đẻ, con nuôi, con rể, con dâu, anh ruột, chị ruột, em ruột, anh rể, 
em rể, chị dâu, em dâu, anh ruột của vợ, anh ruột của chồng, chị ruột của vợ, chị ruột của chồng, 
em ruột của vợ, em ruột của chồng. 
23. Người có liên quan là cá nhân, tổ chức có quan hệ trực tiếp hoặc gián tiếp với doanh nghiệp 
trong các trường hợp sau đây: 
a) Công ty mẹ, người quản lý và người đại diện theo pháp luật của công ty mẹ và người có thẩm 
quyền bổ nhiệm người quản lý của công ty mẹ; 
b) Công ty con, người quản lý và người đại diện theo pháp luật của công ty con; 
c) Cá nhân, tổ chức hoặc nhóm cá nhân, tổ chức có khả năng chi phối hoạt động của doanh 
nghiệp đó thông qua sở hữu, thâu tóm cổ phần, phần vốn góp hoặc thông qua việc ra quyết định 
của công ty; 
d) Người quản lý doanh nghiệp, người đại diện theo pháp luật, Kiểm soát viên; 
đ) Vợ, chồng, bố đẻ, mẹ đẻ, bố nuôi, mẹ nuôi, bố chồng, mẹ chồng, bố vợ, mẹ vợ, con đẻ, con 
nuôi, con rể, con dâu, anh ruột, chị ruột, em ruột, anh rể, em rể, chị dâu, em dâu của người quản 
lý công ty, người đại diện theo pháp luật, Kiểm soát viên, thành viên và cổ đông sở hữu phần vốn 
góp hay cổ phần chi phối; 
e) Cá nhân là người đại diện theo ủy quyền của công ty, tổ chức quy định tại các điểm a, b và c 
khoản này; 
g) Doanh nghiệp trong đó cá nhân, công ty, tổ chức quy định tại các điểm a, b, c, d, đ và e khoản 
này có sở hữu đến mức chi phối việc ra quyết định của công ty. 
24. Người quản lý doanh nghiệp là người quản lý doanh nghiệp tư nhân và người quản lý công 
ty, bao gồm chủ doanh nghiệp tư nhân, thành viên hợp danh, Chủ tịch Hội đồng thành viên, 
thành viên Hội đồng thành viên, Chủ tịch công ty, Chủ tịch Hội đồng quản trị, thành viên Hội 
đồng quản trị, Giám đốc hoặc Tổng giám đốc và cá nhân giữ chức danh quản lý khác theo quy 
định tại Điều lệ công ty. 
25. Người thành lập doanh nghiệp là cá nhân, tổ chức thành lập hoặc góp vốn để thành lập doanh 
nghiệp. 
26. Nhà đầu tư nước ngoài là cá nhân, tổ chức theo quy định của Luật Đầu tư. 
27. Phần vốn góp là tổng giá trị tài sản của một thành viên đã góp hoặc cam kết góp vào công ty 
trách nhiệm hữu hạn, công ty hợp danh. Tỷ lệ phần vốn góp là tỷ lệ giữa phần vốn góp của một 
thành viên và vốn điều lệ của công ty trách nhiệm hữu hạn, công ty hợp danh. 
28. Sản phẩm, dịch vụ công ích là sản phẩm, dịch vụ thiết yếu đối với đời sống kinh tế - xã hội 
của đất nước, địa phương hoặc cộng đồng dân cư mà Nhà nước cần bảo đảm vì lợi ích chung 
hoặc bảo đảm quốc phòng, an ninh và việc sản xuất, cung ứng sản phẩm, dịch vụ này theo cơ chế 
thị trường khó có khả năng bù đắp chi phí. 
29. Thành viên công ty là cá nhân, tổ chức sở hữu một phần hoặc toàn bộ vốn điều lệ của công ty 
trách nhiệm hữu hạn hoặc công ty hợp danh. 
30. Thành viên công ty hợp danh bao gồm thành viên hợp danh và thành viên góp vốn. 
31. Tổ chức lại doanh nghiệp là việc chia, tách, hợp nhất, sáp nhập hoặc chuyển đổi loại hình 
doanh nghiệp. 
32. Tổ chức nước ngoài là tổ chức được thành lập ở nước ngoài theo pháp luật nước ngoài. 
33. Vốn có quyền biểu quyết là phần vốn góp hoặc cổ phần, theo đó người sở hữu có quyền biểu 
quyết về những vấn đề thuộc thẩm quyền quyết định của Hội đồng thành viên hoặc Đại hội đồng 
cổ đông. 
34. Vốn điều lệ là tổng giá trị tài sản do các thành viên công ty, chủ sở hữu công ty đã góp hoặc 
cam kết góp khi thành lập công ty trách nhiệm hữu hạn, công ty hợp danh; là tổng mệnh giá cổ 
phần đã bán hoặc được đăng ký mua khi thành lập công ty cổ phần. 
35.[5] Chủ sở hữu hưởng lợi của doanh nghiệp có tư cách pháp nhân (sau đây gọi là chủ sở hữu 
hưởng lợi của doanh nghiệp) là cá nhân có quyền sở hữu trên thực tế vốn điều lệ hoặc có quyền 
chi phối đối với doanh nghiệp đó, trừ trường hợp người đại diện chủ sở hữu trực tiếp tại doanh 
nghiệp do Nhà nước nắm giữ 100% vốn điều lệ và người đại diện phần vốn nhà nước tại công ty 
cổ phần, công ty trách nhiệm hữu hạn hai thành viên trở lên theo quy định của pháp luật về quản 
lý và đầu tư vốn nhà nước tại doanh nghiệp.

[RULES]
{"id": "ENT-01-D4-000", "type": "condition", "premises": [], "conclusion": "enterprise_definition", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 4 khoản 10", "exception_to": "", "quote": "Doanh nghiệp là tổ chức có tên riêng, có tài sản, có trụ sở giao dịch, được thành lập hoặc đăng ký thành lập theo quy định của pháp luật nhằm mục đích kinh doanh."}
{"id": "ENT-01-D4-001", "type": "condition", "premises": [], "conclusion": "state_owned_enterprise", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 4 khoản 11", "exception_to": "", "quote": "Doanh nghiệp nhà nước bao gồm các doanh nghiệp do Nhà nước nắm giữ trên 50% vốn điều lệ, tổng số cổ phần có quyền biểu quyết theo quy định tại Điều 88 của Luật này."}
{"id": "ENT-01-D4-002", "type": "condition", "premises": [], "conclusion": "vietnamese_enterprise", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 4 khoản 12", "exception_to": "", "quote": "Doanh nghiệp Việt Nam là doanh nghiệp được thành lập hoặc đăng ký thành lập theo quy định của pháp luật Việt Nam và có trụ sở chính tại Việt Nam."}
{"id": "ENT-01-D4-003", "type": "condition", "premises": [], "conclusion": "capital_contribution", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 4 khoản 18", "exception_to": "", "quote": "Góp vốn là việc góp tài sản để tạo thành vốn điều lệ của công ty, bao gồm góp vốn để thành lập công ty hoặc góp thêm vốn điều lệ của công ty đã được thành lập."}
{"id": "ENT-01-D4-004", "type": "condition", "premises": [], "conclusion": "valid_application", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 4 khoản 20", "exception_to": "", "quote": "Hồ sơ hợp lệ là hồ sơ có đầy đủ giấy tờ theo quy định của Luật này và nội dung các giấy tờ đó được kê khai đầy đủ theo quy định của pháp luật."}
{"id": "ENT-01-D4-005", "type": "condition", "premises": [], "conclusion": "business_activity", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 4 khoản 21", "exception_to": "", "quote": "Kinh doanh là việc thực hiện liên tục một, một số hoặc tất cả công đoạn của quá trình từ đầu tư, sản xuất đến tiêu thụ sản phẩm hoặc cung ứng dịch vụ trên thị trường nhằm mục đích tìm kiếm lợi nhuận."}
{"id": "ENT-01-D4-006", "type": "condition", "premises": [], "conclusion": "business_manager", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 4 khoản 24", "exception_to": "", "quote": "Người quản lý doanh nghiệp là người quản lý doanh nghiệp tư nhân và người quản lý công ty, bao gồm chủ doanh nghiệp tư nhân, thành viên hợp danh, Chủ tịch Hội đồng thành viên, thành viên Hội đồng thành viên, Chủ tịch công ty, Chủ tịch Hội đồng quản trị, thành viên Hội đồng quản trị, Giám đốc hoặc Tổng giám đốc và cá nhân giữ chức danh quản lý khác theo quy định tại Điều lệ công ty."}
{"id": "ENT-01-D4-007", "type": "condition", "premises": [], "conclusion": "company_member", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 4 khoản 29", "exception_to": "", "quote": "Thành viên công ty là cá nhân, tổ chức sở hữu một phần hoặc toàn bộ vốn điều lệ của công ty trách nhiệm hữu hạn hoặc công ty hợp danh."}
{"id": "ENT-01-D4-008", "type": "condition", "premises": [], "conclusion": "foreign_organization", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 4 khoản 32", "exception_to": "", "quote": "Tổ chức nước ngoài là tổ chức được thành lập ở nước ngoài theo pháp luật nước ngoài."}
{"id": "ENT-01-D4-100", "type": "condition", "premises": ["is_company_member"], "conclusion": "can_vote_on_company_matters", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 4 khoản 33", "exception_to": "", "quote": "Vốn có quyền biểu quyết là phần vốn góp hoặc cổ phần, theo đó người sở hữu có quyền biểu quyết về những vấn đề thuộc thẩm quyền quyết định của Hội đồng thành viên hoặc Đại hội đồng cổ đông."}
{"id": "ENT-01-D4-101", "type": "condition", "premises": [], "conclusion": "is_registered_capital", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 4 khoản 34", "exception_to": "", "quote": "Vốn điều lệ là tổng giá trị tài sản do các thành viên công ty, chủ sở hữu công ty đã góp hoặc cam kết góp khi thành lập công ty trách nhiệm hữu hạn, công ty hợp danh; là tổng mệnh giá cổ phần đã bán hoặc được đăng ký mua khi thành lập công ty cổ phần."}
{"id": "ENT-01-D4-102", "type": "condition", "premises": ["is_company_member", "not_state_owned_enterprise"], "conclusion": "is_beneficial_owner", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 4 khoản 35", "exception_to": "", "quote": "Chủ sở hữu hưởng lợi của doanh nghiệp có tư cách pháp nhân (sau đây gọi là chủ sở hữu hưởng lợi của doanh nghiệp) là cá nhân có quyền sở hữu trên thực tế vốn điều lệ hoặc có quyền chi phối đối với doanh nghiệp đó, trừ trường hợp người đại diện chủ sở hữu trực tiếp tại doanh nghiệp do Nhà nước nắm giữ 100% vốn điều lệ."}


######## 01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh — Điều 44. Chi nhánh, văn phòng đại diện và địa điểm kinh doanh của doanh nghiệp
[NGUYÊN VĂN]
Điều 44. Chi nhánh, văn phòng đại diện và địa điểm kinh doanh của doanh nghiệp 
1. Chi nhánh là đơn vị phụ thuộc của doanh nghiệp, có nhiệm vụ thực hiện toàn bộ hoặc một 
phần chức năng của doanh nghiệp, bao gồm cả chức năng đại diện theo ủy quyền. Ngành, nghề 
kinh doanh của chi nhánh phải đúng với ngành, nghề kinh doanh của doanh nghiệp. 
2. Văn phòng đại diện là đơn vị phụ thuộc của doanh nghiệp, có nhiệm vụ đại diện theo ủy quyền 
cho lợi ích của doanh nghiệp và bảo vệ các lợi ích đó. Văn phòng đại diện không thực hiện chức 
năng kinh doanh của doanh nghiệp. 
3. Địa điểm kinh doanh là nơi doanh nghiệp tiến hành hoạt động kinh doanh cụ thể.

[RULES]
{"id": "ENT-01-D44-000", "type": "condition", "premises": ["is_branch", "must_perform_duties_honestly", "must_perform_duties_carefully", "must_perform_duties_in_best_way", "must_include_business_field"], "conclusion": "must_perform_branch_functions", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 44 khoản 1", "exception_to": "", "quote": "Chi nhánh là đơn vị phụ thuộc của doanh nghiệp, có nhiệm vụ thực hiện toàn bộ hoặc một phần chức năng của doanh nghiệp."}
{"id": "ENT-01-D44-001", "type": "condition", "premises": ["is_representative_office", "must_perform_duties_honestly", "must_perform_duties_carefully", "must_perform_duties_in_best_way"], "conclusion": "must_represent_enterprise_interests", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 44 khoản 2", "exception_to": "", "quote": "Văn phòng đại diện là đơn vị phụ thuộc của doanh nghiệp, có nhiệm vụ đại diện theo ủy quyền cho lợi ích của doanh nghiệp."}
{"id": "ENT-01-D44-002", "type": "condition", "premises": ["is_representative_office"], "conclusion": "must_not_perform_business_functions", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 44 khoản 2", "exception_to": "", "quote": "Văn phòng đại diện không thực hiện chức năng kinh doanh của doanh nghiệp."}
{"id": "ENT-01-D44-003", "type": "condition", "premises": ["is_business_location"], "conclusion": "must_conduct_business_activities", "source": "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh, Điều 44 khoản 3", "exception_to": "", "quote": "Địa điểm kinh doanh là nơi doanh nghiệp tiến hành hoạt động kinh doanh cụ thể."}


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


######## 04_luat_thue_GTGT_48_2024_QH15 — Điều 3. Đối tượng chịu thuế
[NGUYÊN VĂN]
Điều 3. Đối tượng chịu thuế 
Hàng hóa, dịch vụ sử dụng cho sản xuất, kinh doanh và tiêu dùng ở Việt Nam là đối tượng chịu 
thuế giá trị gia tăng, trừ các đối tượng quy định tại Điều 5 của Luật này.

[RULES]
{"id": "TAX-04-D3-000", "type": "condition", "premises": ["is_selling_goods_or_services_in_domestic"], "conclusion": "goods_subject_to_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 3 khoản 1", "exception_to": "", "quote": "Hàng hóa, dịch vụ sử dụng cho sản xuất, kinh doanh và tiêu dùng ở Việt Nam là đối tượng chịu thuế giá trị gia tăng"}
{"id": "TAX-04-D3-001", "type": "condition", "premises": ["is_selling_goods_or_services_in_domestic", "~not_use_market_value"], "conclusion": "goods_subject_to_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 3 khoản 1", "exception_to": "", "quote": "Hàng hóa, dịch vụ sử dụng cho sản xuất, kinh doanh và tiêu dùng ở Việt Nam là đối tượng chịu thuế giá trị gia tăng"}
{"id": "TAX-04-D3-002", "type": "condition", "premises": ["is_selling_goods_or_services_in_domestic", "is_taxpayer_using_direct_tax_method"], "conclusion": "goods_subject_to_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 3 khoản 1", "exception_to": "", "quote": "Hàng hóa, dịch vụ sử dụng cho sản xuất, kinh doanh và tiêu dùng ở Việt Nam là đối tượng chịu thuế giá trị gia tăng"}
{"id": "TAX-04-D3-003", "type": "condition", "premises": ["is_taxpayer_authorized_to_use_invoice"], "conclusion": "goods_subject_to_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 3 khoản 1", "exception_to": "", "quote": "Hàng hóa, dịch vụ sử dụng cho sản xuất, kinh doanh và tiêu dùng ở Việt Nam là đối tượng chịu thuế giá trị gia tăng"}
{"id": "TAX-04-D3-004", "type": "condition", "premises": ["is_taxpayer_using_direct_tax_method", "is_taxpayer_is_monthly_vat_filer"], "conclusion": "goods_subject_to_vat", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 3 khoản 1", "exception_to": "", "quote": "Hàng hóa, dịch vụ sử dụng cho sản xuất, kinh doanh và tiêu dùng ở Việt Nam là đối tượng chịu thuế giá trị gia tăng"}


######## 04_luat_thue_GTGT_48_2024_QH15 — Điều 4. Người nộp thuế
[NGUYÊN VĂN]
Điều 4. Người nộp thuế 
1. Tổ chức, hộ, cá nhân sản xuất, kinh doanh hàng hóa, dịch vụ chịu thuế giá trị gia tăng (sau đây 
gọi là cơ sở kinh doanh). 
2. Tổ chức, cá nhân nhập khẩu hàng hóa chịu thuế giá trị gia tăng (sau đây gọi là người nhập 
khẩu). 
3. Tổ chức, cá nhân sản xuất, kinh doanh tại Việt Nam mua dịch vụ (kể cả trường hợp mua dịch 
vụ gắn với hàng hóa) của tổ chức nước ngoài không có cơ sở thường trú tại Việt Nam, cá nhân ở 
nước ngoài là đối tượng không cư trú tại Việt Nam, trừ trường hợp quy định tại khoản 4 và 
khoản 5 Điều này; tổ chức sản xuất, kinh doanh tại Việt Nam mua hàng hóa, dịch vụ để tiến hành 
hoạt động tìm kiếm thăm dò, phát triển mỏ dầu khí và khai thác dầu khí của tổ chức nước ngoài 
không có cơ sở thường trú tại Việt Nam, cá nhân ở nước ngoài là đối tượng không cư trú tại Việt 
Nam. 
4. Nhà cung cấp nước ngoài không có cơ sở thường trú tại Việt Nam có hoạt động kinh doanh 
thương mại điện tử, kinh doanh dựa trên nền tảng số với tổ chức, cá nhân tại Việt Nam (sau đây 
gọi là nhà cung cấp nước ngoài); tổ chức là nhà quản lý nền tảng số nước ngoài thực hiện khấu 
trừ, nộp thay nghĩa vụ thuế phải nộp của nhà cung cấp nước ngoài; tổ chức kinh doanh tại Việt 
Nam áp dụng phương pháp tính thuế giá trị gia tăng là phương pháp khấu trừ thuế mua dịch vụ 
của nhà cung cấp nước ngoài không có cơ sở thường trú tại Việt Nam thông qua kênh thương 
mại điện tử hoặc các nền tảng số thực hiện khấu trừ, nộp thay nghĩa vụ thuế phải nộp của nhà 
cung cấp nước ngoài. 
5. Tổ chức là nhà quản lý sàn giao dịch thương mại điện tử, nhà quản lý nền tảng số có chức 
năng thanh toán thực hiện khấu trừ, nộp thuế thay, kê khai số thuế đã khấu trừ cho hộ kinh 
doanh, cá nhân kinh doanh trên sàn thương mại điện tử, nền tảng số. 
6. Chính phủ quy định chi tiết các khoản 1, 4 và 5 Điều này; quy định về người nộp thuế trong 
trường hợp nhà cung cấp nước ngoài cung cấp dịch vụ cho người mua là tổ chức kinh doanh tại 
Việt Nam áp dụng phương pháp khấu trừ thuế quy định tại khoản 4 Điều này.

[RULES]
{"id": "TAX-04-D4-000", "type": "condition", "premises": ["is_legal_entity_or_non_legal_entity_taxpayer"], "conclusion": "taxpayer_includes_foreign_entities", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 4 khoản 1", "exception_to": "", "quote": "Tổ chức, hộ, cá nhân sản xuất, kinh doanh hàng hóa, dịch vụ chịu thuế giá trị gia tăng."}
{"id": "TAX-04-D4-001", "type": "condition", "premises": ["is_legal_entity_or_non_legal_entity_taxpayer"], "conclusion": "taxpayer_includes_foreign_entities", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 4 khoản 2", "exception_to": "", "quote": "Tổ chức, cá nhân nhập khẩu hàng hóa chịu thuế giá trị gia tăng."}
{"id": "TAX-04-D4-002", "type": "condition", "premises": ["is_legal_entity_or_non_legal_entity_taxpayer", "~is_foreign_individual"], "conclusion": "taxpayer_includes_foreign_entities_ecommerce", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 4 khoản 3", "exception_to": "", "quote": "Tổ chức, cá nhân sản xuất, kinh doanh tại Việt Nam mua dịch vụ của tổ chức nước ngoài không có cơ sở thường trú tại Việt Nam."}
{"id": "TAX-04-D4-003", "type": "condition", "premises": ["is_legal_entity_or_non_legal_entity_taxpayer"], "conclusion": "must_withhold_tax_for_foreign_suppliers", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 4 khoản 4", "exception_to": "", "quote": "Nhà cung cấp nước ngoài không có cơ sở thường trú tại Việt Nam có hoạt động kinh doanh thương mại điện tử."}
{"id": "TAX-04-D4-004", "type": "condition", "premises": ["is_legal_entity_or_non_legal_entity_taxpayer"], "conclusion": "must_withhold_tax_for_foreign_suppliers", "source": "04_luat_thue_GTGT_48_2024_QH15, Điều 4 khoản 5", "exception_to": "", "quote": "Tổ chức là nhà quản lý sàn giao dịch thương mại điện tử thực hiện khấu trừ, nộp thuế thay."}


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


######## 06_luat_TNDN_67_2025_QH15 — Điều 2. Người nộp thuế
[NGUYÊN VĂN]
Điều 2. Người nộp thuế 
1. Người nộp thuế thu nhập doanh nghiệp là tổ chức hoạt động sản xuất, kinh doanh hàng hóa, 
dịch vụ có thu nhập chịu thuế theo quy định của Luật này (sau đây gọi là doanh nghiệp), bao 
gồm: 
a) Doanh nghiệp được thành lập theo quy định của pháp luật Việt Nam; 
b) Doanh nghiệp được thành lập theo quy định của pháp luật nước ngoài (sau đây gọi là doanh 
nghiệp nước ngoài) có cơ sở thường trú hoặc không có cơ sở thường trú tại Việt Nam; 
c) Hợp tác xã, liên hiệp hợp tác xã được thành lập theo quy định của Luật Hợp tác xã; 
d) Đơn vị sự nghiệp được thành lập theo quy định của pháp luật Việt Nam; 
đ) Tổ chức khác có hoạt động sản xuất, kinh doanh có thu nhập. 
2. Doanh nghiệp có thu nhập chịu thuế quy định tại Điều 3 của Luật này phải nộp thuế thu nhập 
doanh nghiệp như sau: 
a) Doanh nghiệp được thành lập theo quy định của pháp luật Việt Nam nộp thuế đối với thu nhập 
chịu thuế phát sinh tại Việt Nam và thu nhập chịu thuế phát sinh ngoài Việt Nam; 
b) Doanh nghiệp nước ngoài có cơ sở thường trú tại Việt Nam nộp thuế đối với thu nhập chịu 
thuế phát sinh tại Việt Nam và thu nhập chịu thuế phát sinh ngoài Việt Nam liên quan đến hoạt 
động của cơ sở thường trú đó; 
c) Doanh nghiệp nước ngoài có cơ sở thường trú tại Việt Nam nộp thuế đối với thu nhập chịu 
thuế phát sinh tại Việt Nam mà khoản thu nhập này không liên quan đến hoạt động của cơ sở 
thường trú; 
d) Doanh nghiệp nước ngoài không có cơ sở thường trú tại Việt Nam, bao gồm cả các doanh 
nghiệp kinh doanh thương mại điện tử, kinh doanh dựa trên nền tảng số, nộp thuế đối với thu 
nhập chịu thuế phát sinh tại Việt Nam. 
3. Cơ sở thường trú của doanh nghiệp nước ngoài là cơ sở sản xuất, kinh doanh mà thông qua cơ 
sở này, doanh nghiệp nước ngoài tiến hành một phần hoặc toàn bộ hoạt động sản xuất, kinh 
doanh tại Việt Nam, bao gồm: 
a) Chi nhánh, văn phòng điều hành, nhà máy, công xưởng, phương tiện vận tải, mỏ dầu, mỏ khí, 
mỏ hoặc địa điểm khai thác tài nguyên thiên nhiên khác tại Việt Nam; 
b) Địa điểm xây dựng, công trình xây dựng, lắp đặt, lắp ráp; 
c) Cơ sở cung cấp dịch vụ, bao gồm cả dịch vụ tư vấn thông qua người làm công hoặc tổ chức, 
cá nhân khác; 
d) Đại lý cho doanh nghiệp nước ngoài; 
đ) Đại diện tại Việt Nam trong trường hợp là đại diện có thẩm quyền ký kết hợp đồng đứng tên 
doanh nghiệp nước ngoài hoặc đại diện không có thẩm quyền ký kết hợp đồng đứng tên doanh 
nghiệp nước ngoài nhưng thường xuyên thực hiện việc giao hàng hóa hoặc cung ứng dịch vụ tại 
Việt Nam; 
e) Nền tảng thương mại điện tử, nền tảng số mà thông qua đó doanh nghiệp nước ngoài tiến hành 
cung cấp hàng hóa, dịch vụ tại Việt Nam. 
4. Chính phủ quy định chi tiết Điều này.

[RULES]
{"id": "TAX-06-D2-000", "type": "condition", "premises": ["is_legal_entity_or_non_legal_entity_taxpayer", "is_business_in_ecommerce"], "conclusion": "taxpayer_includes_foreign_entities_ecommerce", "source": "06_luat_TNDN_67_2025_QH15, Điều 2 khoản 1", "exception_to": "", "quote": "Người nộp thuế bao gồm tổ chức và cá nhân nước ngoài có hoạt động kinh doanh trên nền tảng thương mại điện tử."}
{"id": "TAX-06-D2-001", "type": "condition", "premises": ["is_legal_entity_or_non_legal_entity_taxpayer", "is_foreign_entity_with_income_in_vietnam"], "conclusion": "taxpayer_includes_foreign_entities", "source": "06_luat_TNDN_67_2025_QH15, Điều 2 khoản 1", "exception_to": "", "quote": "Người nộp thuế bao gồm tổ chức và cá nhân nước ngoài."}
{"id": "TAX-06-D2-002", "type": "condition", "premises": ["is_legal_entity_or_non_legal_entity_taxpayer", "is_taxpayer_with_business_activity_in_different_location"], "conclusion": "taxpayer_includes_legal_entities", "source": "06_luat_TNDN_67_2025_QH15, Điều 2 khoản 1", "exception_to": "", "quote": "Người nộp thuế bao gồm các tổ chức được thành lập và đăng ký kinh doanh theo Luật Doanh nghiệp, Luật Hợp tác xã và pháp luật chuyên ngành khác."}
{"id": "TAX-06-D2-003", "type": "condition", "premises": ["is_legal_entity_or_non_legal_entity_taxpayer", "is_foreign_entity_with_income_in_vietnam"], "conclusion": "must_pay_tax_on_business_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 2 khoản 2", "exception_to": "", "quote": "Doanh nghiệp có thu nhập chịu thuế quy định tại Điều 3 của Luật này phải nộp thuế thu nhập doanh nghiệp."}
{"id": "TAX-06-D2-004", "type": "condition", "premises": ["is_foreign_entity_with_income_in_vietnam", "not_have_permanent_establishment_in_vietnam"], "conclusion": "must_pay_tax_on_business_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 2 khoản 3", "exception_to": "", "quote": "Doanh nghiệp nước ngoài không có cơ sở thường trú tại Việt Nam, bao gồm cả các doanh nghiệp kinh doanh thương mại điện tử, kinh doanh dựa trên nền tảng số, nộp thuế đối với thu nhập chịu thuế phát sinh tại Việt Nam."}


######## 06_luat_TNDN_67_2025_QH15 — Điều 3. Thu nhập chịu thuế
[NGUYÊN VĂN]
Điều 3. Thu nhập chịu thuế 
1. Thu nhập chịu thuế thu nhập doanh nghiệp bao gồm thu nhập từ hoạt động sản xuất, kinh 
doanh hàng hóa, dịch vụ và thu nhập khác quy định tại khoản 2 Điều này. 
2. Thu nhập khác bao gồm: 
a) Thu nhập từ chuyển nhượng vốn, chuyển nhượng quyền góp vốn, chuyển nhượng chứng 
khoán; 
b) Thu nhập từ chuyển nhượng bất động sản, trừ thu nhập từ chuyển nhượng bất động sản của 
doanh nghiệp kinh doanh bất động sản; 
c) Thu nhập từ chuyển nhượng dự án đầu tư, chuyển nhượng quyền tham gia dự án đầu tư, 
chuyển nhượng quyền thăm dò, khai thác, chế biến khoáng sản; 
d) Thu nhập từ chuyển nhượng, cho thuê, thanh lý tài sản, trong đó có các loại giấy tờ có giá, trừ 
bất động sản; 
đ) Thu nhập từ quyền sử dụng, quyền sở hữu tài sản, bao gồm cả thu nhập từ quyền sở hữu trí 
tuệ, chuyển giao công nghệ; 
e) Thu nhập từ lãi tiền gửi, lãi cho vay vốn, bán ngoại tệ, trừ thu nhập từ hoạt động tín dụng của 
tổ chức tín dụng; 
g) Khoản trích trước vào chi phí nhưng không sử dụng hoặc sử dụng không hết mà doanh nghiệp 
không hạch toán điều chỉnh giảm chi phí được trừ; khoản nợ khó đòi đã xóa nay đòi được; khoản 
nợ phải trả không xác định được chủ nợ; khoản thu nhập từ kinh doanh của những năm trước bị 
bỏ sót nay phát hiện ra; 
h) Chênh lệch giữa thu về tiền phạt, tiền bồi thường do vi phạm hợp đồng kinh tế hoặc thưởng do 
thực hiện tốt cam kết theo hợp đồng; 
i) Các khoản tài trợ, tặng cho bằng tiền hoặc hiện vật nhận được; 
k) Chênh lệch do đánh giá lại tài sản theo quy định của pháp luật để góp vốn, điều chuyển khi 
sáp nhập, hợp nhất, chia, tách, chuyển đổi chủ sở hữu, chuyển đổi loại hình doanh nghiệp; 
l) Thu nhập từ hợp đồng hợp tác kinh doanh; 
m) Thu nhập từ hoạt động sản xuất, kinh doanh ở nước ngoài; 
n) Thu nhập của đơn vị sự nghiệp công lập đối với các hoạt động cho thuê tài sản công; 
o) Các khoản thu nhập khác, trừ các khoản thu nhập được miễn thuế quy định tại Điều 4 của 
Luật này. 
3. Thu nhập chịu thuế phát sinh tại Việt Nam của doanh nghiệp nước ngoài quy định tại điểm c, 
điểm d khoản 2 Điều 2 của Luật này là thu nhập nhận được có nguồn gốc từ Việt Nam, không 
phụ thuộc vào địa điểm tiến hành kinh doanh. 
4. Doanh nghiệp Việt Nam đầu tư ở nước ngoài có phát sinh thu nhập từ hoạt động sản xuất, 
kinh doanh tại nước ngoài trong kỳ tính thuế được trừ số thuế thu nhập doanh nghiệp phải nộp 
theo quy định của nước tiếp nhận đầu tư vào số thuế thu nhập doanh nghiệp phải nộp ở Việt 
Nam, nhưng không được vượt quá số thuế thu nhập doanh nghiệp tính theo quy định của pháp 
luật về thuế thu nhập doanh nghiệp của Việt Nam. 
5. Doanh nghiệp phải nộp thuế thu nhập doanh nghiệp bổ sung về tổng hợp thu nhập chịu thuế 
tối thiểu (IIR) theo quy định của pháp luật thì thuế thu nhập doanh nghiệp bổ sung phải nộp được 
trừ vào số thuế thu nhập doanh nghiệp phải nộp tại Việt Nam theo quy định của Luật này. 
6. Chính phủ quy định chi tiết Điều này.

[RULES]
{"id": "TAX-06-D3-000", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_business_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 1", "exception_to": "", "quote": "Thu nhập chịu thuế thu nhập doanh nghiệp bao gồm thu nhập từ hoạt động sản xuất, kinh doanh hàng hóa, dịch vụ và thu nhập khác quy định tại khoản 2 Điều này."}
{"id": "TAX-06-D3-001", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_capital_transfer_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 2 điểm a", "exception_to": "", "quote": "Thu nhập khác bao gồm: a) Thu nhập từ chuyển nhượng vốn, chuyển nhượng quyền góp vốn, chuyển nhượng chứng khoán;"}
{"id": "TAX-06-D3-002", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_real_estate_transfer_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 2 điểm b", "exception_to": "", "quote": "b) Thu nhập từ chuyển nhượng bất động sản, trừ thu nhập từ chuyển nhượng bất động sản của doanh nghiệp kinh doanh bất động sản;"}
{"id": "TAX-06-D3-003", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_investment_project_transfer_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 2 điểm c", "exception_to": "", "quote": "c) Thu nhập từ chuyển nhượng dự án đầu tư, chuyển nhượng quyền tham gia dự án đầu tư, chuyển nhượng quyền thăm dò, khai thác, chế biến khoáng sản;"}
{"id": "TAX-06-D3-004", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_asset_transfer_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 2 điểm d", "exception_to": "", "quote": "d) Thu nhập từ chuyển nhượng, cho thuê, thanh lý tài sản, trong đó có các loại giấy tờ có giá, trừ bất động sản;"}
{"id": "TAX-06-D3-005", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_property_right_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 2 điểm đ", "exception_to": "", "quote": "đ) Thu nhập từ quyền sử dụng, quyền sở hữu tài sản, bao gồm cả thu nhập từ quyền sở hữu trí tuệ, chuyển giao công nghệ;"}
{"id": "TAX-06-D3-006", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_interest_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 2 điểm e", "exception_to": "", "quote": "e) Thu nhập từ lãi tiền gửi, lãi cho vay vốn, bán ngoại tệ, trừ thu nhập từ hoạt động tín dụng của tổ chức tín dụng;"}
{"id": "TAX-06-D3-007", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_other_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 2 điểm g", "exception_to": "", "quote": "g) Khoản trích trước vào chi phí nhưng không sử dụng hoặc sử dụng không hết mà doanh nghiệp không hạch toán điều chỉnh giảm chi phí được trừ; khoản nợ khó đòi đã xóa nay đòi được; khoản nợ phải trả không xác định được chủ nợ; khoản thu nhập từ kinh doanh của những năm trước bị bỏ sót nay phát hiện ra;"}
{"id": "TAX-06-D3-008", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_penalty_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 2 điểm h", "exception_to": "", "quote": "h) Chênh lệch giữa thu về tiền phạt, tiền bồi thường do vi phạm hợp đồng kinh tế hoặc thưởng do thực hiện tốt cam kết theo hợp đồng;"}
{"id": "TAX-06-D3-009", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_donations", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 2 điểm i", "exception_to": "", "quote": "i) Các khoản tài trợ, tặng cho bằng tiền hoặc hiện vật nhận được;"}
{"id": "TAX-06-D3-010", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_asset_revaluation_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 2 điểm k", "exception_to": "", "quote": "k) Chênh lệch do đánh giá lại tài sản theo quy định của pháp luật để góp vốn, điều chuyển khi sáp nhập, hợp nhất, chia, tách, chuyển đổi chủ sở hữu, chuyển đổi loại hình doanh nghiệp;"}
{"id": "TAX-06-D3-011", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_business_cooperation_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 2 điểm l", "exception_to": "", "quote": "l) Thu nhập từ hợp đồng hợp tác kinh doanh;"}
{"id": "TAX-06-D3-012", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_foreign_business_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 2 điểm m", "exception_to": "", "quote": "m) Thu nhập từ hoạt động sản xuất, kinh doanh ở nước ngoài;"}
{"id": "TAX-06-D3-013", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_public_service_income", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 2 điểm n", "exception_to": "", "quote": "n) Thu nhập của đơn vị sự nghiệp công lập đối với các hoạt động cho thuê tài sản công;"}
{"id": "TAX-06-D3-014", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_other_income_excluding_exempt", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 2 điểm o", "exception_to": "", "quote": "o) Các khoản thu nhập khác, trừ các khoản thu nhập được miễn thuế quy định tại Điều 4 của Luật này."}
{"id": "TAX-06-D3-015", "type": "condition", "premises": [], "conclusion": "taxpayer_includes_foreign_income_from_vietnam", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 3", "exception_to": "", "quote": "Thu nhập chịu thuế phát sinh tại Việt Nam của doanh nghiệp nước ngoài quy định tại điểm c, điểm d khoản 2 Điều 2 của Luật này là thu nhập nhận được có nguồn gốc từ Việt Nam, không phụ thuộc vào địa điểm tiến hành kinh doanh."}
{"id": "TAX-06-D3-016", "type": "condition", "premises": [], "conclusion": "taxpayer_can_deduct_foreign_tax", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 4", "exception_to": "", "quote": "Doanh nghiệp Việt Nam đầu tư ở nước ngoài có phát sinh thu nhập từ hoạt động sản xuất, kinh doanh tại nước ngoài trong kỳ tính thuế được trừ số thuế thu nhập doanh nghiệp phải nộp theo quy định của nước tiếp nhận đầu tư vào số thuế thu nhập doanh nghiệp phải nộp ở Việt Nam, nhưng không được vượt quá số thuế thu nhập doanh nghiệp tính theo quy định của pháp luật về thuế thu nhập doanh nghiệp của Vi"}
{"id": "TAX-06-D3-017", "type": "condition", "premises": [], "conclusion": "taxpayer_can_deduct_additional_tax", "source": "06_luat_TNDN_67_2025_QH15, Điều 3 khoản 5", "exception_to": "", "quote": "Doanh nghiệp phải nộp thuế thu nhập doanh nghiệp bổ sung về tổng hợp thu nhập chịu thuế tối thiểu (IIR) theo quy định của pháp luật thì thuế thu nhập doanh nghiệp bổ sung phải nộp được trừ vào số thuế thu nhập doanh nghiệp phải nộp tại Việt Nam theo quy định của Luật này."}


######## 06_luat_TNDN_67_2025_QH15 — Điều 9. Các khoản chi được trừ và không được trừ khi xác định thu nhập chịu thuế
[NGUYÊN VĂN]
Điều 9. Các khoản chi được trừ và không được trừ khi xác định thu nhập chịu thuế 
1. Trừ các khoản chi quy định tại khoản 2 Điều này, doanh nghiệp được trừ các khoản chi khi 
xác định thu nhập chịu thuế nếu đáp ứng đủ các điều kiện sau đây: 
a) Khoản chi thực tế phát sinh liên quan đến hoạt động sản xuất, kinh doanh của doanh nghiệp, 
bao gồm cả khoản chi phí bổ sung được trừ theo tỷ lệ phần trăm tính trên chi phí thực tế phát 
sinh trong kỳ tính thuế liên quan đến hoạt động nghiên cứu và phát triển của doanh nghiệp; 
b) Khoản chi thực tế phát sinh khác, bao gồm: 
b1) Khoản chi cho thực hiện nhiệm vụ giáo dục quốc phòng và an ninh, huấn luyện, hoạt động 
của lực lượng dân quân tự vệ và phục vụ các nhiệm vụ quốc phòng, an ninh khác theo quy định 
của pháp luật; 
b2) Khoản chi hỗ trợ phục vụ cho hoạt động của tổ chức đảng, tổ chức chính trị - xã hội trong 
doanh nghiệp; 
b3) Khoản chi cho hoạt động giáo dục nghề nghiệp, đào tạo nghề nghiệp cho người lao động 
theo quy định của pháp luật; 
b4) Khoản chi thực tế cho hoạt động phòng, chống HIV/AIDS nơi làm việc của doanh nghiệp; 
b5) Khoản tài trợ cho giáo dục, y tế, văn hóa; khoản tài trợ cho phòng, chống, khắc phục hậu quả 
thiên tai, dịch bệnh, làm nhà đại đoàn kết, nhà tình nghĩa, nhà cho các đối tượng chính sách theo 
quy định của pháp luật; khoản tài trợ theo quy định của Chính phủ, Thủ tướng Chính phủ dành 
cho các địa phương thuộc địa bàn có điều kiện kinh tế - xã hội đặc biệt khó khăn; khoản tài trợ 
cho nghiên cứu khoa học, phát triển công nghệ và đổi mới sáng tạo, chuyển đổi số; 
b6) Khoản chi cho nghiên cứu khoa học, phát triển công nghệ và đổi mới sáng tạo, chuyển đổi 
số; 
b7) Phần giá trị tổn thất do thiên tai, dịch bệnh và trường hợp bất khả kháng khác không được 
bồi thường; 
b8) Khoản chi thực tế cho người được biệt phái tham gia quản trị, điều hành, kiểm soát tổ chức 
tín dụng được kiểm soát đặc biệt, ngân hàng thương mại được chuyển giao bắt buộc theo quy 
định của Luật Các tổ chức tín dụng; 
b9) Một số khoản chi phục vụ sản xuất, kinh doanh của doanh nghiệp nhưng chưa tương ứng với 
doanh thu phát sinh trong kỳ theo quy định của Chính phủ; 
b10) Một số khoản chi hỗ trợ xây dựng công trình công cộng, đồng thời phục vụ hoạt động sản 
xuất, kinh doanh của doanh nghiệp; 
b11) Chi phí liên quan đến việc giảm phát thải khí nhà kính nhằm trung hòa các-bon và net zero, 
giảm ô nhiễm môi trường, đồng thời liên quan đến hoạt động sản xuất, kinh doanh của doanh 
nghiệp; 
b12) Một số khoản đóng góp vào các quỹ được thành lập theo quyết định của Thủ tướng Chính 
phủ và quy định của Chính phủ; 
c) Các khoản chi có đủ hoá đơn, chứng từ thanh toán không dùng tiền mặt theo quy định của 
pháp luật, trừ các trường hợp đặc thù theo quy định của Chính phủ. 
2. Các khoản chi không được trừ khi xác định thu nhập chịu thuế bao gồm: 
a) Khoản chi không đáp ứng đủ các điều kiện quy định tại khoản 1 Điều này; 
b) Khoản tiền phạt do vi phạm hành chính; 
c) Khoản chi được bù đắp bằng nguồn kinh phí khác; 
d) Phần chi vượt mức do Chính phủ quy định đối với: chi phí quản lý kinh doanh do doanh 
nghiệp nước ngoài phân bổ cho cơ sở thường trú tại Việt Nam; chi phí thuê quản lý hoạt động 
kinh doanh trò chơi điện tử có thưởng, kinh doanh casino; chi trả lãi tiền vay của doanh nghiệp 
có giao dịch liên kết; chi có tính chất phúc lợi trực tiếp cho người lao động; khoản đóng góp 
tham gia bảo hiểm hưu trí bổ sung theo quy định của Luật Bảo hiểm xã hội hoặc quỹ có tính chất 
an sinh xã hội, mua bảo hiểm hưu trí tự nguyện, bảo hiểm nhân thọ cho người lao động; 
đ) Phần trích lập không đúng hoặc vượt mức theo quy định của pháp luật về trích lập dự phòng; 
e) Khoản trích khấu hao tài sản cố định không đúng hoặc vượt mức quy định của pháp luật; 
g) Khoản trích trước vào chi phí không đúng quy định của pháp luật; 
h) Tiền lương, tiền công của chủ doanh nghiệp tư nhân, chủ công ty trách nhiệm hữu hạn một 
thành viên do cá nhân làm chủ; thù lao trả cho sáng lập viên doanh nghiệp không trực tiếp tham 
gia điều hành sản xuất, kinh doanh; tiền lương, tiền công, các khoản hạch toán chi khác để chi trả 
cho người lao động nhưng thực tế không chi trả hoặc không có hoá đơn, chứng từ theo quy định 
của pháp luật; 
i) Phần chi trả lãi tiền vay tương ứng với phần vốn điều lệ còn thiếu; lãi tiền vay trong quá trình 
đầu tư đã được ghi nhận vào giá trị đầu tư; lãi vay để triển khai thực hiện các hợp đồng tìm kiếm, 
thăm dò và khai thác dầu khí; phần chi trả lãi tiền vay vốn sản xuất, kinh doanh của đối tượng 
không phải là tổ chức tín dụng vượt mức theo quy định của Bộ luật Dân sự; 
k) Phần chi phí được phép thu hồi vượt quá tỷ lệ quy định tại hợp đồng dầu khí được duyệt; 
trường hợp hợp đồng dầu khí không quy định về tỷ lệ thu hồi chi phí thì phần chi phí vượt trên 
mức do Chính phủ quy định không được tính vào chi phí được trừ; 
l) Phần thuế giá trị gia tăng đầu vào đã được khấu trừ; thuế giá trị gia tăng nộp theo phương pháp 
khấu trừ; thuế giá trị gia tăng đầu vào của phần giá trị xe ô tô chở người từ 09 chỗ ngồi trở xuống 
vượt mức do Chính phủ quy định; thuế thu nhập doanh nghiệp; các khoản thuế, phí, lệ phí, thu 
khác không được tính vào chi phí theo quy định của pháp luật và tiền chậm nộp theo quy định 
của pháp luật về quản lý thuế. 
Phần thuế giá trị gia tăng nộp theo phương pháp khấu trừ quy định tại điểm này không bao gồm 
phần thuế giá trị gia tăng của hàng hóa, dịch vụ đầu vào có liên quan trực tiếp đến sản xuất, kinh 
doanh của doanh nghiệp chưa được khấu trừ hết nhưng không thuộc trường hợp hoàn thuế. 
Số thuế giá trị gia tăng đầu vào khi đã được tính vào chi phí được trừ thì không được khấu trừ 
với số thuế giá trị gia tăng đầu ra; 
m) Khoản chi không tương ứng với doanh thu tính thuế, trừ các khoản chi quy định tại điểm b 
khoản 1 Điều này; khoản chi không đáp ứng điều kiện chi, nội dung chi theo quy định của pháp 
luật chuyên ngành; 
n) Khoản tài trợ, trừ khoản tài trợ quy định tại tiểu điểm b5 điểm b khoản 1 Điều này; 
o) Chi về đầu tư xây dựng cơ bản trong giai đoạn đầu tư để hình thành tài sản cố định; chi liên 
quan trực tiếp đến việc tăng, giảm vốn chủ sở hữu của doanh nghiệp; 
p) Các khoản chi của hoạt động kinh doanh: ngân hàng, bảo hiểm, xổ số, chứng khoán, hợp đồng 
BT, BOT, BTO không đúng hoặc vượt mức quy định của pháp luật; 
q) Các khoản chi khác. 
3. Chính phủ quy định chi tiết Điều này, bao gồm cả mức chi bổ sung, điều kiện, thời gian và 
phạm vi áp dụng đối với khoản chi cho hoạt động nghiên cứu và phát triển của doanh nghiệp quy 
định tại điểm a khoản 1 Điều này. 
Bộ Tài chính quy định hồ sơ của khoản chi được tính vào chi phí được trừ quy định tại điểm b, 
điểm c khoản 1 Điều này.

[RULES]
{"id": "TAX-06-D9-000", "type": "condition", "premises": ["is_actual_expense_related_to_business", "has_invoice_payment_non_cash"], "conclusion": "is_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 1", "exception_to": "", "quote": "doanh nghiệp được trừ các khoản chi khi xác định thu nhập chịu thuế nếu đáp ứng đủ các điều kiện sau đây"}
{"id": "TAX-06-D9-001", "type": "condition", "premises": ["is_actual_expense_related_to_production_business"], "conclusion": "is_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 1 điểm a", "exception_to": "", "quote": "Khoản chi thực tế phát sinh liên quan đến hoạt động sản xuất, kinh doanh của doanh nghiệp"}
{"id": "TAX-06-D9-002", "type": "condition", "premises": ["is_expense_for_national_defense_education"], "conclusion": "is_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 1 điểm b1", "exception_to": "", "quote": "Khoản chi cho thực hiện nhiệm vụ giáo dục quốc phòng và an ninh"}
{"id": "TAX-06-D9-003", "type": "condition", "premises": ["is_expense_for_party_organization"], "conclusion": "is_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 1 điểm b2", "exception_to": "", "quote": "Khoản chi hỗ trợ phục vụ cho hoạt động của tổ chức đảng"}
{"id": "TAX-06-D9-004", "type": "condition", "premises": ["is_expense_for_vocational_training"], "conclusion": "is_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 1 điểm b3", "exception_to": "", "quote": "Khoản chi cho hoạt động giáo dục nghề nghiệp, đào tạo nghề nghiệp cho người lao động"}
{"id": "TAX-06-D9-005", "type": "condition", "premises": ["is_expense_for_hiv_prevention_at_workplace"], "conclusion": "is_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 1 điểm b4", "exception_to": "", "quote": "Khoản chi thực tế cho hoạt động phòng, chống HIV/AIDS nơi làm việc của doanh nghiệp"}
{"id": "TAX-06-D9-006", "type": "condition", "premises": ["is_expense_for_education_health_culture_support"], "conclusion": "is_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 1 điểm b5", "exception_to": "", "quote": "Khoản tài trợ cho giáo dục, y tế, văn hóa"}
{"id": "TAX-06-D9-007", "type": "condition", "premises": ["is_expense_for_research_innovation"], "conclusion": "is_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 1 điểm b6", "exception_to": "", "quote": "Khoản chi cho nghiên cứu khoa học, phát triển công nghệ và đổi mới sáng tạo"}
{"id": "TAX-06-D9-008", "type": "condition", "premises": ["is_loss_due_to_force_majeure"], "conclusion": "is_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 1 điểm b7", "exception_to": "", "quote": "Phần giá trị tổn thất do thiên tai, dịch bệnh và trường hợp bất khả kháng khác không được bồi thường"}
{"id": "TAX-06-D9-009", "type": "condition", "premises": ["is_expense_for_special_controlled_credit_institution"], "conclusion": "is_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 1 điểm b8", "exception_to": "", "quote": "Khoản chi thực tế cho người được biệt phái tham gia quản trị, điều hành, kiểm soát tổ chức tín dụng được kiểm soát đặc biệt"}
{"id": "TAX-06-D9-010", "type": "condition", "premises": ["is_expense_not_corresponding_to_revenue"], "conclusion": "is_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 1 điểm b9", "exception_to": "", "quote": "Một số khoản chi phục vụ sản xuất, kinh doanh của doanh nghiệp nhưng chưa tương ứng với doanh thu phát sinh trong kỳ"}
{"id": "TAX-06-D9-011", "type": "condition", "premises": ["is_expense_for_public_infrastructure"], "conclusion": "is_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 1 điểm b10", "exception_to": "", "quote": "Một số khoản chi hỗ trợ xây dựng công trình công cộng, đồng thời phục vụ hoạt động sản xuất, kinh doanh của doanh nghiệp"}
{"id": "TAX-06-D9-012", "type": "condition", "premises": ["is_expense_for_environmental_protection"], "conclusion": "is_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 1 điểm b11", "exception_to": "", "quote": "Chi phí liên quan đến việc giảm phát thải khí nhà kính nhằm trung hòa các-bon và net zero"}
{"id": "TAX-06-D9-013", "type": "condition", "premises": ["is_expense_for_government_funds"], "conclusion": "is_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 1 điểm b12", "exception_to": "", "quote": "Một số khoản đóng góp vào các quỹ được thành lập theo quyết định của Thủ tướng Chính phủ"}
{"id": "TAX-06-D9-014", "type": "condition", "premises": ["is_expense_not_meeting_conditions"], "conclusion": "is_not_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 2", "exception_to": "", "quote": "Các khoản chi không được trừ khi xác định thu nhập chịu thuế bao gồm: Khoản chi không đáp ứng đủ các điều kiện quy định tại khoản 1"}
{"id": "TAX-06-D9-015", "type": "condition", "premises": ["is_fine_for_administrative_violation"], "conclusion": "is_not_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 2 điểm b", "exception_to": "", "quote": "Khoản tiền phạt do vi phạm hành chính"}
{"id": "TAX-06-D9-016", "type": "condition", "premises": ["is_expense_compensated_by_other_funds"], "conclusion": "is_not_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 2 điểm c", "exception_to": "", "quote": "Khoản chi được bù đắp bằng nguồn kinh phí khác"}
{"id": "TAX-06-D9-017", "type": "condition", "premises": ["is_expense_exceeding_government_limit"], "conclusion": "is_not_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 2 điểm d", "exception_to": "", "quote": "Phần chi vượt mức do Chính phủ quy định đối với chi phí quản lý kinh doanh"}
{"id": "TAX-06-D9-018", "type": "condition", "premises": ["is_incorrect_depreciation_expense"], "conclusion": "is_not_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 2 điểm e", "exception_to": "", "quote": "Khoản trích khấu hao tài sản cố định không đúng hoặc vượt mức quy định của pháp luật"}
{"id": "TAX-06-D9-019", "type": "condition", "premises": ["is_incorrect_provision_expense"], "conclusion": "is_not_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 2 điểm f", "exception_to": "", "quote": "Khoản trích trước vào chi phí không đúng quy định của pháp luật"}
{"id": "TAX-06-D9-020", "type": "condition", "premises": ["is_wage_of_private_business_owner"], "conclusion": "is_not_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 2 điểm g", "exception_to": "", "quote": "Tiền lương, tiền công của chủ doanh nghiệp tư nhân, chủ công ty trách nhiệm hữu hạn một thành viên"}
{"id": "TAX-06-D9-021", "type": "condition", "premises": ["is_interest_payment_exceeding_limit"], "conclusion": "is_not_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 2 điểm h", "exception_to": "", "quote": "Phần chi trả lãi tiền vay tương ứng với phần vốn điều lệ còn thiếu"}
{"id": "TAX-06-D9-022", "type": "condition", "premises": ["is_vat_input_not_deducted"], "conclusion": "is_not_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 2 điểm i", "exception_to": "", "quote": "Phần thuế giá trị gia tăng đầu vào đã được khấu trừ"}
{"id": "TAX-06-D9-023", "type": "condition", "premises": ["is_expense_not_corresponding_to_taxable_revenue"], "conclusion": "is_not_tax_deduction", "source": "06_luat_TNDN_67_2025_QH15, Điều 9 khoản 2 điểm j", "exception_to": "", "quote": "Khoản chi không tương ứng với doanh thu tính thuế"}
