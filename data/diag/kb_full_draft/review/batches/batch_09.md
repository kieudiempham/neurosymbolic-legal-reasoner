

######## 11_nghi_dinh_158_2025_ND-CP — Điều 33. Chế độ tử tuất đối với thân nhân người đang hưởng trợ cấp mất sức lao động, đang
[NGUYÊN VĂN]
Điều 33. Chế độ tử tuất đối với thân nhân người đang hưởng trợ cấp mất sức lao động, đang 
hưởng trợ cấp hằng tháng sau khi đã hết thời hạn hưởng trợ cấp mất sức lao động, đang 
hưởng trợ cấp hằng tháng đối với công nhân cao su, đang hưởng trợ cấp hằng tháng đối với 
cán bộ xã, phường, thị trấn đã nghỉ việc chết 
1. Người đang hưởng trợ cấp mất sức lao động hằng tháng trước ngày 01 tháng 7 năm 2025 mà chết 
từ ngày 01 tháng 7 năm 2025 trở đi thì: 
a) Tổ chức, cá nhân lo mai táng được nhận một lần trợ cấp mai táng quy định tại khoản 2 Điều 85 của 
Luật Bảo hiểm xã hội; 
b) Thân nhân đủ điều kiện quy định tại khoản 2 và khoản 3 Điều 86 của Luật Bảo hiểm xã hội được 
hưởng trợ cấp tuất hằng tháng quy định tại Điều 87 của Luật Bảo hiểm xã hội; 
c) Trường hợp không có thân nhân đủ điều kiện quy định tại khoản 2 và khoản 3 Điều 86 của Luật 
Bảo hiểm xã hội hoặc có thân nhân đủ điều kiện nhưng có nguyện vọng hưởng trợ cấp tuất một lần 
thì thân nhân được hưởng trợ cấp tuất một lần bằng 3 tháng trợ cấp mất sức lao động hằng tháng 
đang hưởng trước khi chết. 
2. Người đang hưởng trợ cấp hằng tháng theo Nghị định số 09/1998/NĐ-CP trước ngày 01 tháng 7 
năm 2025 mà chết từ ngày 01 tháng 7 năm 2025 trở đi thì: 
a) Tổ chức, cá nhân lo mai táng được nhận một lần trợ cấp mai táng quy định tại khoản 2 Điều 85 của 
Luật Bảo hiểm xã hội; 
b) Thân nhân đủ điều kiện quy định tại khoản 2 và khoản 3 Điều 86 của Luật Bảo hiểm xã hội được 
hưởng trợ cấp tuất hằng tháng quy định tại Điều 87 của Luật Bảo hiểm xã hội; 
c) Trường hợp không có thân nhân đủ điều kiện quy định tại khoản 2 và khoản 3 Điều 86 của Luật 
Bảo hiểm xã hội hoặc có thân nhân đủ điều kiện nhưng có nguyện vọng hưởng trợ cấp tuất một lần 
thì thân nhân được hưởng trợ cấp tuất một lần được tính như quy định tại khoản 2 Điều 89 của Luật 
Bảo hiểm xã hội. 
3. Người đang hưởng trợ cấp hằng tháng sau khi đã hết thời hạn hưởng trợ cấp mất sức lao động, 
đang hưởng trợ cấp hằng tháng đối với công nhân cao su trước ngày 01 tháng 7 năm 2025 mà chết 
từ ngày 01 tháng 7 năm 2025 trở đi thì: 
a) Tổ chức, cá nhân lo mai táng được nhận một lần trợ cấp mai táng quy định tại khoản 2 Điều 85 của 
Luật Bảo hiểm xã hội; 
b) Thân nhân được hưởng trợ cấp tuất một lần bằng 3 tháng trợ cấp hằng tháng đang hưởng trước 
khi chết.

[RULES]
{"id": "LAB-11-D33-000", "type": "condition", "premises": ["is_survivor", "started_si_before_2025", "died_after_2025"], "conclusion": "survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 33 khoản 1", "exception_to": "", "quote": "Người đang hưởng trợ cấp mất sức lao động hằng tháng trước ngày 01 tháng 7 năm 2025 mà chết từ ngày 01 tháng 7 năm 2025 trở đi thì..."}
{"id": "LAB-11-D33-001", "type": "condition", "premises": ["is_survivor", "started_si_before_2025", "died_after_2025"], "conclusion": "lump_sum_benefit_for_burial", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 33 khoản 1 điểm a", "exception_to": "", "quote": "Tổ chức, cá nhân lo mai táng được nhận một lần trợ cấp mai táng quy định tại khoản 2 Điều 85 của Luật Bảo hiểm xã hội;"}
{"id": "LAB-11-D33-002", "type": "condition", "premises": ["is_survivor", "started_si_before_2025", "died_after_2025", "has_full_contribution_time"], "conclusion": "monthly_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 33 khoản 1 điểm b", "exception_to": "", "quote": "Thân nhân đủ điều kiện quy định tại khoản 2 và khoản 3 Điều 86 của Luật Bảo hiểm xã hội được hưởng trợ cấp tuất hằng tháng quy định tại Điều 87 của Luật Bảo hiểm xã hội;"}
{"id": "LAB-11-D33-003", "type": "condition", "premises": ["is_survivor", "started_si_before_2025", "died_after_2025", "not_has_full_contribution_time"], "conclusion": "lump_sum_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 33 khoản 1 điểm c", "exception_to": "", "quote": "Trường hợp không có thân nhân đủ điều kiện quy định tại khoản 2 và khoản 3 Điều 86 của Luật Bảo hiểm xã hội hoặc có thân nhân đủ điều kiện nhưng có nguyện vọng hưởng trợ cấp tuất một lần thì thân nhân được hưởng trợ cấp tuất một lần bằng 3 tháng trợ cấp mất sức lao động hằng tháng đang hưởng trước khi chết."}
{"id": "LAB-11-D33-004", "type": "condition", "premises": ["is_survivor", "started_si_before_2025", "died_after_2025"], "conclusion": "survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 33 khoản 2", "exception_to": "", "quote": "Người đang hưởng trợ cấp hằng tháng theo Nghị định số 09/1998/NĐ-CP trước ngày 01 tháng 7 năm 2025 mà chết từ ngày 01 tháng 7 năm 2025 trở đi thì..."}
{"id": "LAB-11-D33-005", "type": "condition", "premises": ["is_survivor", "started_si_before_2025", "died_after_2025"], "conclusion": "lump_sum_benefit_for_burial", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 33 khoản 2 điểm a", "exception_to": "", "quote": "Tổ chức, cá nhân lo mai táng được nhận một lần trợ cấp mai táng quy định tại khoản 2 Điều 85 của Luật Bảo hiểm xã hội;"}
{"id": "LAB-11-D33-006", "type": "condition", "premises": ["is_survivor", "started_si_before_2025", "died_after_2025", "has_full_contribution_time"], "conclusion": "monthly_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 33 khoản 2 điểm b", "exception_to": "", "quote": "Thân nhân đủ điều kiện quy định tại khoản 2 và khoản 3 Điều 86 của Luật Bảo hiểm xã hội được hưởng trợ cấp tuất hằng tháng quy định tại Điều 87 của Luật Bảo hiểm xã hội;"}
{"id": "LAB-11-D33-007", "type": "condition", "premises": ["is_survivor", "started_si_before_2025", "died_after_2025", "not_has_full_contribution_time"], "conclusion": "lump_sum_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 33 khoản 2 điểm c", "exception_to": "", "quote": "Trường hợp không có thân nhân đủ điều kiện quy định tại khoản 2 và khoản 3 Điều 86 của Luật Bảo hiểm xã hội hoặc có thân nhân đủ điều kiện nhưng có nguyện vọng hưởng trợ cấp tuất một lần thì thân nhân được hưởng trợ cấp tuất một lần được tính như quy định tại khoản 2 Điều 89 của Luật Bảo hiểm xã hội."}
{"id": "LAB-11-D33-008", "type": "condition", "premises": ["is_survivor", "started_si_before_2025", "died_after_2025"], "conclusion": "survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 33 khoản 3", "exception_to": "", "quote": "Người đang hưởng trợ cấp hằng tháng sau khi đã hết thời hạn hưởng trợ cấp mất sức lao động, đang hưởng trợ cấp hằng tháng đối với công nhân cao su trước ngày 01 tháng 7 năm 2025 mà chết từ ngày 01 tháng 7 năm 2025 trở đi thì..."}
{"id": "LAB-11-D33-009", "type": "condition", "premises": ["is_survivor", "started_si_before_2025", "died_after_2025"], "conclusion": "lump_sum_benefit_for_burial", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 33 khoản 3 điểm a", "exception_to": "", "quote": "Tổ chức, cá nhân lo mai táng được nhận một lần trợ cấp mai táng quy định tại khoản 2 Điều 85 của Luật Bảo hiểm xã hội;"}
{"id": "LAB-11-D33-010", "type": "condition", "premises": ["is_survivor", "started_si_before_2025", "died_after_2025"], "conclusion": "lump_sum_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 33 khoản 3 điểm b", "exception_to": "", "quote": "Thân nhân được hưởng trợ cấp tuất một lần bằng 3 tháng trợ cấp hằng tháng đang hưởng trước khi chết."}


######## 11_nghi_dinh_158_2025_ND-CP — Điều 34. Tính thời gian công tác trước ngày 01 tháng 01 năm 1995 để hưởng bảo hiểm xã hội
[NGUYÊN VĂN]
Điều 34. Tính thời gian công tác trước ngày 01 tháng 01 năm 1995 để hưởng bảo hiểm xã hội 
1. Người lao động có thời gian làm việc trong khu vực nhà nước trước ngày 01 tháng 01 năm 1995 
mà được tính là thời gian công tác liên tục, thời gian công tác thực tế nhưng chưa được giải quyết trợ 
cấp thôi việc hoặc trợ cấp một lần, bảo hiểm xã hội một lần thì thời gian đó được tính là thời gian đã 
đóng bảo hiểm xã hội, cụ thể như sau: 
a) Người lao động làm việc trong khu vực nhà nước liên tục công tác đến ngày 01 tháng 01 năm 1995 
mà chưa được giải quyết trợ cấp thôi việc hoặc trợ cấp một lần, bảo hiểm xã hội một lần thì thời gian 
làm việc trước ngày 01 tháng 01 năm 1995 đó được tính là thời gian đã đóng bảo hiểm xã hội; 
b) Người lao động có thời gian công tác gián đoạn hoặc đã nghỉ việc trước ngày 01 tháng 01 năm 
1995 thì việc xác định thời gian công tác liên tục, thời gian công tác thực tế để tính hưởng bảo hiểm 
xã hội được thực hiện theo các văn bản quy định trước đây về tính thời gian công tác trước ngày 01 
tháng 01 năm 1995 để hưởng bảo hiểm xã hội, trừ quy định tại Điều 3 của Nghị định số 66/CP ngày 
30 tháng 9 năm 1993 của Chính phủ quy định tạm thời chế độ bảo hiểm xã hội đối với lực lượng vũ 
trang; Điều 3 của Nghị định số 43/CP ngày 22 tháng 6 năm 1993 của Chính phủ quy định tạm thời chế 
độ bảo hiểm xã hội; Điều 54 của Điều lệ bảo hiểm xã hội ban hành kèm theo Nghị định số 12/CP ngày 
26 tháng 01 năm 1995 của Chính phủ; Điều 49 Điều lệ Bảo hiểm xã hội đối với sỹ quan, quân nhân 
chuyên nghiệp, hạ sỹ quan, binh sỹ Quân đội nhân dân và Công an nhân dân ban hành kèm theo 
Nghị định số 45/CP ngày 15 tháng 7 năm 1995 của Chính phủ; khoản 4 Điều 139 của Luật Bảo hiểm 
xã hội năm 2006; khoản 6 Điều 123 của Luật Bảo hiểm xã hội năm 2014; Điều 23 của Nghị định số 
115/2015/NĐ-CP ngày 11 tháng 11 năm 2015 của Chính phủ quy định chi tiết một số điều của Luật 
Bảo hiểm xã hội về bảo hiểm xã hội bắt buộc; các khoản 7, 8 và 9 Điều 38 của Nghị định số 
33/2023/NĐ-CP ngày 10 tháng 6 năm 2023 của Chính phủ quy định về cán bộ, công chức cấp xã và 
người hoạt động không chuyên trách ở cấp xã, ở thôn, tổ dân phố; khoản 2 và khoản 3 Điều 16 của 
Nghị định số 92/2009/NĐ-CP ngày 22 tháng 10 năm 2009 của Chính phủ về chức danh, số lượng, 
một số chế độ, chính sách đối với cán bộ, công chức ở xã, phường, thị trấn và những người hoạt 
động không chuyên trách ở cấp xã; khoản 2 Điều 1 của Nghị định số 29/2013/NĐ-CP ngày 08 tháng 4 
năm 2013 của Chính phủ sửa đổi, bổ sung một số điều của Nghị định số 92/2009/NĐ-CP ngày 22 
tháng 10 năm 2009 của Chính phủ về chức danh, số lượng, một số chế độ, chính sách đối với cán bộ, 
công chức xã, phường, thị trấn và những người hoạt động không chuyên trách ở cấp xã; khoản 8 
Điều 2 của Nghị định số 34/2019/NĐ-CP ngày 24 tháng 4 năm 2019 về việc sửa đổi, bổ sung một số 
quy định về cán bộ, công chức cấp xã và người hoạt động không chuyên trách ở cấp xã, ở thôn, tổ 
dân phố; 
c) Người đang hưởng trợ cấp bệnh binh, sau đó có thời gian tham gia công tác và đóng bảo hiểm xã 
hội thì ngoài chế độ bệnh binh còn được hưởng chế độ bảo hiểm xã hội. Thời gian tính hưởng bảo 
hiểm xã hội là thời gian đã đóng bảo hiểm xã hội theo quy định của pháp luật về bảo hiểm xã hội; thời 
gian công tác tính hưởng chế độ bệnh binh không được tính để hưởng bảo hiểm xã hội. 
2. Người lao động có thời gian công tác là quân nhân, công an nhân dân đã phục viên, xuất ngũ, thôi 
việc trước ngày 15 tháng 12 năm 1993, sau đó làm việc có tham gia bảo hiểm xã hội bắt buộc tại các 
cơ quan, đơn vị, doanh nghiệp thuộc các thành phần kinh tế (bao gồm cả người làm việc tại y tế xã, 
phường, thị trấn, giáo viên mầm non hoặc người giữ các chức danh ở xã, phường, thị trấn trước ngày 
01 tháng 01 năm 1995 đã được tính là thời gian đã đóng bảo hiểm xã hội) và cá nhân có thuê mướn, 
sử dụng lao động thì thời gian công tác thực tế trong quân đội, công an nhân dân trước đó được cộng 
với thời gian công tác có đóng bảo hiểm xã hội sau này để tính hưởng bảo hiểm xã hội, trừ trường 
hợp đã hưởng chế độ trợ cấp theo quy định dưới đây: 
a) Quyết định số 47/2002/QĐ-TTg ngày 11 tháng 4 năm 2002 của Thủ tướng Chính phủ về chế độ đối 
với quân nhân, công nhân viên quốc phòng tham gia kháng chiến chống Pháp đã phục viên (giải ngũ, 
thôi việc) từ ngày 31 tháng 12 năm 1960 trở về trước; 
b) Điểm a khoản 1 Điều 1 của Quyết định số 290/2005/QĐ-TTg ngày 08 tháng 11 năm 2005 của Thủ 
tướng Chính phủ về chế độ, chính sách đối với một số đối tượng trực tiếp tham gia kháng chiến 
chống Mỹ cứu nước nhưng chưa được hưởng chế độ, chính sách của Đảng và Nhà nước; 
c) Quyết định số 92/2005/QĐ-TTg ngày 29 tháng 4 năm 2005 của Thủ tướng Chính phủ về thực hiện 
chế độ đối với quân nhân là người dân tộc ít người thuộc Quân khu 7, Quân khu 9, tham gia kháng 
chiến chống Mỹ, về địa phương trước ngày 10 tháng 01 năm 1982; 
d) Quyết định số 142/2008/QĐ-TTg ngày 27 tháng 10 năm 2008 của Thủ tướng Chính phủ về thực 
hiện chế độ đối với quân nhân tham gia kháng chiến chống Mỹ cứu nước có dưới 20 năm công tác 
trong quân đội đã phục viên, xuất ngũ về địa phương; 
đ) Quyết định số 38/2010/QĐ-TTg ngày 06 tháng 5 năm 2010 của Thủ tướng Chính phủ về việc sửa 
đổi, bổ sung Quyết định số 142/2008/QĐ-TTg ngày 27 tháng 10 năm 2008 của Thủ tướng Chính phủ 
về việc thực hiện chế độ đối với quân nhân tham gia kháng chiến chống Mỹ cứu nước có dưới 20 
năm công tác trong quân đội đã phục viên, xuất ngũ về địa phương; 
e) Quyết định số 53/2010/QĐ-TTg ngày 20 tháng 8 năm 2010 của Thủ tướng Chính phủ về chế độ đối 
với cán bộ, chiến sĩ Công an nhân dân tham gia kháng chiến chống Mỹ có dưới 20 năm công tác 
trong Công an nhân dân đã thôi việc, xuất ngũ về địa phương; 
g) Quyết định số 62/2011/QĐ-TTg ngày 09 tháng 11 năm 2011 của Thủ tướng Chính phủ về chế độ, 
chính sách đối với đối tượng tham gia chiến tranh bảo vệ Tổ quốc, làm nhiệm vụ quốc tế ở Căm-pu-
chi-a, giúp bạn Lào sau ngày 30 tháng 4 năm 1975 đã phục viên, xuất ngũ, thôi việc. 
Trường hợp người lao động có thời gian công tác là quân nhân, công an nhân dân đã phục viên, xuất 
ngũ, thôi việc trước ngày 15 tháng 12 năm 1993, tham gia bảo hiểm xã hội tự nguyện sau đó mới 
tham gia bảo hiểm xã hội bắt buộc thuộc đối tượng áp dụng quy định tại khoản này để tính hưởng bảo 
hiểm xã hội. 
3. Người lao động có thời gian là quân nhân, công an nhân dân đã phục viên, xuất ngũ, thôi việc trong 
khoảng thời gian từ ngày 15 tháng 12 năm 1993 đến ngày 31 tháng 12 năm 1994 mà chưa giải quyết 
trợ cấp thôi việc hoặc trợ cấp một lần, trợ cấp xuất ngũ, phục viên, bảo hiểm xã hội một lần thì thời 
gian công tác thực tế trong quân đội, công an nhân dân được tính hưởng bảo hiểm xã hội. 
4. Trường hợp người lao động không còn đủ hồ sơ gốc thể hiện thời gian làm việc trong khu vực nhà 
nước trước ngày 01 tháng 01 năm 1995 thì cơ quan bảo hiểm xã hội hội xem xét, quyết định tính 
hoặc không tính thời gian công tác trước ngày 01 tháng 01 năm 1995 để hưởng bảo hiểm xã hội dựa 
trên cơ sở văn bản đề nghị của người lao động, văn bản xác nhận của cơ quan, đơn vị trực tiếp quản 
lý người lao động và các hồ sơ, giấy tờ có liên quan đến thời gian công tác đề nghị tính hưởng bảo 
hiểm xã hội. Trường hợp cần thiết, cơ quan bảo hiểm xã hội phối hợp với các cơ quan chức năng có 
liên quan tại địa phương rà soát, đối chiếu hồ sơ của người lao động để làm rõ các vấn đề có liên 
quan trước khi quyết định. 
a) Nội dung văn bản xác nhận của cơ quan, đơn vị trực tiếp quản lý người lao động phải nêu rõ lý do 
không còn đủ hồ sơ gốc của người lao động, thời điểm tuyển dụng, diễn biến quá trình công tác, diễn 
biến tiền lương của người lao động; việc người lao động chưa được giải quyết trợ cấp thôi việc hoặc 
trợ cấp một lần, lý do chưa được giải quyết; lý do gián đoạn hoặc nghỉ việc và trách nhiệm của cơ 
quan, đơn vị quản lý trong việc giải quyết chế độ tại thời điểm nghỉ việc đối với người lao động có thời 
gian công tác gián đoạn hoặc đã nghỉ việc trước ngày 01 tháng 01 năm 1995. Trường hợp cơ quan, 
đơn vị trực tiếp quản lý người lao động không còn tồn tại thì cơ quan quản lý cấp trên trực tiếp xác 
nhận; 
b) Các hồ sơ, giấy tờ có liên quan đến thời gian công tác đề nghị tính hưởng bảo hiểm xã hội là các 
hồ sơ, giấy tờ có liên quan chứng minh, thể hiện thời gian làm việc trong khu vực nhà nước trước 
ngày 01 tháng 01 năm 1995 như: Lý lịch đảng viên, Lý lịch đoàn viên, sổ lao động, danh sách lao 
động, sổ theo dõi, danh sách chi trả lương, sổ lương thực, giấy khen, bằng khen, kỷ niệm chương, 
văn bằng, chứng chỉ, hồ sơ giải quyết chế độ của người lao động khi thực hiện cổ phần hóa doanh 
nghiệp nhà nước và các giấy tờ khác thể hiện quá trình công tác, tiền lương của người lao động; 
c) Cơ quan, đơn vị trực tiếp quản lý người lao động hoặc cơ quan quản lý cấp trên trực tiếp của 
người lao động phải căn cứ vào hồ sơ, giấy tờ liên quan quy định tại điểm b khoản này để xác nhận 
và phải chịu trách nhiệm trước pháp luật về các nội dung xác nhận quy định tại điểm a khoản này.

[RULES]
{"id": "LAB-11-D34-000", "type": "condition", "premises": ["working_for_state_agency", "worked_before_01_01_1995", "not_received_severance_pay"], "conclusion": "has_full_contribution_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 34 khoản 1 điểm a", "exception_to": "", "quote": "thời gian làm việc trước ngày 01 tháng 01 năm 1995 đó được tính là thời gian đã đóng bảo hiểm xã hội"}
{"id": "LAB-11-D34-001", "type": "condition", "premises": ["worked_before_01_01_1995", "~not_received_severance_pay"], "conclusion": "has_full_contribution_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 34 khoản 1 điểm b", "exception_to": "Điều 3 của Nghị định số 66/CP ngày 30 tháng 9 năm 1993", "quote": "việc xác định thời gian công tác liên tục, thời gian công tác thực tế để tính hưởng bảo hiểm xã hội được thực hiện theo các văn bản quy định trước đây"}
{"id": "LAB-11-D34-002", "type": "condition", "premises": ["is_military_officer", "not_received_benefit_for_disability"], "conclusion": "can_receive_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 34 khoản 1 điểm c", "exception_to": "", "quote": "Thời gian tính hưởng bảo hiểm xã hội là thời gian đã đóng bảo hiểm xã hội theo quy định của pháp luật về bảo hiểm xã hội"}
{"id": "LAB-11-D34-003", "type": "condition", "premises": ["is_military_officer", "worked_before_15_12_1993", "started_si_after_1995"], "conclusion": "has_full_contribution_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 34 khoản 2", "exception_to": "", "quote": "thời gian công tác thực tế trong quân đội, công an nhân dân trước đó được cộng với thời gian công tác có đóng bảo hiểm xã hội sau này"}
{"id": "LAB-11-D34-004", "type": "condition", "premises": ["is_military_officer", "worked_between_15_12_1993_and_31_12_1994", "not_received_severance_pay"], "conclusion": "can_receive_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 34 khoản 3", "exception_to": "", "quote": "thời gian công tác thực tế trong quân đội, công an nhân dân được tính hưởng bảo hiểm xã hội"}
{"id": "LAB-11-D34-100", "type": "condition", "premises": ["working_for_state_agency", "~not_has_full_salary_during_detention", "~not_enough_contribution_years"], "conclusion": "must_count_previous_work_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 34 khoản 1", "exception_to": "", "quote": "Trường hợp người lao động không còn đủ hồ sơ gốc thể hiện thời gian làm việc trong khu vực nhà nước trước ngày 01 tháng 01 năm 1995..."}
{"id": "LAB-11-D34-101", "type": "condition", "premises": ["working_for_state_agency", "~not_has_full_salary_during_detention"], "conclusion": "must_provide_conditions_for_negotiation", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 34 khoản 1 điểm a", "exception_to": "", "quote": "Nội dung văn bản xác nhận của cơ quan, đơn vị trực tiếp quản lý người lao động phải nêu rõ lý do không còn đủ hồ sơ gốc..."}
{"id": "LAB-11-D34-102", "type": "condition", "premises": ["working_for_state_agency"], "conclusion": "must_provide_documents_for_change_of_representative", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 34 khoản 1 điểm b", "exception_to": "", "quote": "Các hồ sơ, giấy tờ có liên quan đến thời gian công tác đề nghị tính hưởng bảo hiểm xã hội là các hồ sơ, giấy tờ có liên quan chứng minh..."}
{"id": "LAB-11-D34-103", "type": "condition", "premises": ["working_for_state_agency"], "conclusion": "must_complete_insurance_procedure", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 34 khoản 1 điểm c", "exception_to": "", "quote": "Cơ quan, đơn vị trực tiếp quản lý người lao động hoặc cơ quan quản lý cấp trên trực tiếp của người lao động phải căn cứ vào hồ sơ, giấy tờ liên quan..."}


######## 11_nghi_dinh_158_2025_ND-CP — Điều 35. Tính thời gian công tác đối với người lao động đi hợp tác lao động trước ngày 01
[NGUYÊN VĂN]
Điều 35. Tính thời gian công tác đối với người lao động đi hợp tác lao động trước ngày 01 
tháng 01 năm 1995 
1. Người lao động thuộc biên chế của các cơ quan nhà nước, tổ chức chính trị, tổ chức chính trị - xã 
hội, doanh nghiệp nhà nước, đơn vị lực lượng vũ trang được cơ quan, đơn vị cử đi công tác, học tập, 
làm việc có thời hạn đã xuất cảnh hợp pháp ra nước ngoài, đã về nước nhưng không đúng hạn hoặc 
về nước đúng thời hạn nhưng đơn vị cũ không bố trí, sắp xếp được việc làm thì thời gian làm việc 
trong nước trước khi đi công tác, học tập, làm việc ở nước ngoài và thời gian ở nước ngoài trong thời 
hạn cho phép trước ngày 01 tháng 01 năm 1995 nếu chưa được giải quyết chế độ trợ cấp thôi việc 
hoặc trợ cấp một lần, trợ cấp phục viên, xuất ngũ hoặc bảo hiểm xã hội một lần được tính để hưởng 
chế độ hưu trí và tử tuất. Việc tính thời gian công tác trước ngày 01 tháng 01 năm 1995 để tính 
hưởng bảo hiểm xã hội thực hiện theo quy định tại Điều 34 của Nghị định này. 
Đối tượng lao động xã hội được cử đi hợp tác lao động sau khi về nước tiếp tục tham gia đóng bảo 
hiểm xã hội bắt buộc thì thời gian làm việc ở nước ngoài trong thời hạn cho phép trước ngày 01 tháng 
01 năm 1995 nếu chưa được giải quyết chế độ trợ cấp thôi việc hoặc trợ cấp một lần được tính để 
hưởng chế độ hưu trí và tử tuất. 
2. Thời gian công tác, học tập, làm việc ở nước ngoài trong thời hạn cho phép quy định tại khoản 1 
Điều này bao gồm: 
a) Thời gian công tác, học tập, làm việc thực tế trong thời hạn được ghi trong quyết định của đơn vị 
cử đi công tác, học tập, làm việc ở nước ngoài, kể cả thời gian được gia hạn do đơn vị cử đi cho 
phép; 
b) Trường hợp một người có nhiều lần đi công tác, học tập, làm việc ở nước ngoài thì được cộng thời 
gian của các lần ở nước ngoài trong thời hạn cho phép thành thời gian công tác để tính hưởng chế độ 
hưu trí, tử tuất; 
c) Người lao động đang làm việc ở trong nước, được đơn vị cử đi nâng cao tay nghề ở nước ngoài, 
sau đó chuyển sang hợp tác lao động theo Hiệp định của Chính phủ thì thời gian nâng cao tay nghề 
được tính để hưởng chế độ hưu trí, tử tuất; 
d) Đối tượng lao động xã hội là học sinh học nghề chuyển sang hợp tác lao động theo Hiệp định của 
Chính phủ thì thời gian hợp tác lao động theo Hiệp định của Chính phủ được tính để hưởng chế độ 
hưu trí và tử tuất; thời gian học nghề không được tính để hưởng bảo hiểm xã hội. 
3. Không áp dụng quy định tại khoản 1 Điều này đối với các trường hợp vi phạm pháp luật ở nước 
ngoài bị trục xuất về nước hoặc bị kỷ luật buộc phải về nước hoặc bị phạt tù giam trước ngày 01 
tháng 01 năm 1995. 
4. Mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội 
a) Mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội để tính lương hưu, trợ cấp một lần khi 
nghỉ hưu, bảo hiểm xã hội một lần và trợ cấp tuất một lần của các đối tượng quy định tại khoản 1 Điều 
này được tính theo quy định tại Điều 72 của Luật Bảo hiểm xã hội và Điều 15 của Nghị định này; 
b) Đối với trường hợp có thời gian công tác trong quân đội, công an nhân dân tiếp đó đi hợp tác lao 
động ở nước ngoài, sau khi về nước được chuyển ngành sang làm việc tại các cơ quan, đơn vị, 
doanh nghiệp nhà nước thuộc diện được tính cộng phụ cấp thâm niên nghề trong lương hưu theo quy 
định thì mức phụ cấp thâm niên quân đội, công an nhân dân được tính trên cơ sở mức lương sĩ quan, 
quân nhân chuyên nghiệp quân đội nhân dân và sĩ quan, hạ sĩ quan công an nhân dân tại thời điểm 
trước khi đi hợp tác lao động ở nước ngoài, được chuyển đổi theo chế độ tiền lương quy định tại thời 
điểm giải quyết hưởng chế độ; 
c) Đối với người lao động trước khi đi hợp tác lao động đang hưởng tiền lương do Nhà nước quy định 
mà có số năm cuối để tính mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội bao gồm cả 
thời gian đi làm việc ở nước ngoài thì tiền lương làm căn cứ đóng bảo hiểm xã hội của thời gian đi 
làm việc ở nước ngoài được lấy theo tiền lương tại thời điểm trước khi đi nước ngoài để làm cơ sở 
tính lương hưu, trợ cấp bảo hiểm xã hội. 
Đối với những người là lao động xã hội được tính thời gian đi hợp tác lao động để tính hưởng chế độ 
hưu trí, tử tuất quy định tại khoản 1 Điều này thì tiền lương làm căn cứ đóng bảo hiểm xã hội của thời 
gian đi hợp tác lao động để làm căn cứ tính mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã 
hội được tính bằng hai lần mức tham chiếu tại thời điểm hưởng bảo hiểm xã hội.

[RULES]
{"id": "LAB-11-D35-000", "type": "condition", "premises": ["working_for_state_agency", "worked_before_01_01_1995", "~has_full_contribution_time_by_state"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 35 khoản 1", "exception_to": "", "quote": "thời gian làm việc trong nước trước khi đi công tác, học tập, làm việc ở nước ngoài... được tính để hưởng chế độ hưu trí và tử tuất."}
{"id": "LAB-11-D35-001", "type": "condition", "premises": ["working_for_state_agency", "worked_before_01_01_1995", "has_full_contribution_time_by_state"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 35 khoản 1", "exception_to": "", "quote": "thời gian làm việc trong nước trước khi đi công tác, học tập, làm việc ở nước ngoài... được tính để hưởng chế độ hưu trí và tử tuất."}
{"id": "LAB-11-D35-002", "type": "condition", "premises": ["working_for_state_agency", "worked_before_01_01_1995"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 35 khoản 2", "exception_to": "", "quote": "thời gian công tác, học tập, làm việc ở nước ngoài trong thời hạn cho phép quy định tại khoản 1 Điều này bao gồm..."}
{"id": "LAB-11-D35-003", "type": "condition", "premises": ["worked_before_01_01_1995", "~not_allowed_to_work_in_hazardous_jobs"], "conclusion": "~benefit_calculation_based_on_contribution_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 35 khoản 3", "exception_to": "", "quote": "Không áp dụng quy định tại khoản 1 Điều này đối với các trường hợp vi phạm pháp luật ở nước ngoài..."}
{"id": "LAB-11-D35-004", "type": "condition", "premises": ["working_for_state_agency", "worked_before_01_01_1995"], "conclusion": "benefit_calculation_based_on_contribution_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 35 khoản 4", "exception_to": "", "quote": "Mức bình quân tiền lương làm căn cứ đóng bảo hiểm xã hội để tính lương hưu, trợ cấp một lần khi nghỉ hưu..."}


######## 11_nghi_dinh_158_2025_ND-CP — Điều 36. Hồ sơ đề nghị tính thời gian công tác đối với người lao động đi hợp tác lao động
[NGUYÊN VĂN]
Điều 36. Hồ sơ đề nghị tính thời gian công tác đối với người lao động đi hợp tác lao động 
trước ngày 01 tháng 01 năm 1995 
1. Hồ sơ đối với trường hợp người đi lao động có thời gian ở nước ngoài theo Hiệp định của Chính 
phủ và người đi làm đội trưởng, phiên dịch, cán bộ vùng do nước ngoài trả lương bao gồm: 
a) Lý lịch gốc, lý lịch bổ sung (nếu có), các giấy tờ gốc có liên quan đến thời gian làm việc, tiền lương 
của người lao động trước khi đi làm việc ở nước ngoài; quyết định tiếp nhận trở lại làm việc đối với 
trường hợp người lao động về nước và tiếp tục làm việc trước ngày 01 tháng 01 năm 1995. Trường 
hợp không có Quyết định tiếp nhận thì được thay thế bằng Lý lịch do người lao động khai khi được 
tiếp nhận trở lại làm việc hoặc lý lịch của người lao động khai có xác nhận của đơn vị tiếp nhận; 
b) Bản chính “Thông báo chuyển trả” hoặc “Quyết định chuyển trả” của Cục Hợp tác quốc tế về lao 
động (nay là Cục Quản lý lao động ngoài nước) cấp. 
Trường hợp không còn bản chính “Thông báo chuyển trả” hoặc “Quyết định chuyển trả” thì phải có 
Giấy xác nhận về thời gian đi hợp tác lao động để giải quyết chế độ bảo hiểm xã hội của Cục Quản lý 
lao động ngoài nước trên cơ sở đơn đề nghị của người lao động (theo Mẫu số 01 và số 02 Phụ lục II 
ban hành kèm theo Nghị định này); 
c) Giấy xác nhận chưa được giải quyết trợ cấp thôi việc, trợ cấp một lần (hoặc trợ cấp một lần, trợ 
cấp phục viên, xuất ngũ đối với trường hợp quân nhân, công an nhân dân phục viên, xuất ngũ, thôi 
việc trong khoảng thời gian ngày 15 tháng 12 năm 1993 đến ngày 31 tháng 12 năm 1994) sau khi về 
nước của cơ quan, đơn vị trực tiếp quản lý người lao động trước khi đi công tác, làm việc có thời hạn 
ở nước ngoài. Trường hợp cơ quan, đơn vị đã giải thể thì cơ quan, đơn vị quản lý cấp trên trực tiếp 
xác nhận. 
Đối với những người là lao động xã hội đi hợp tác lao động; công nhân, viên chức Nhà nước, công an 
nhân dân, quân nhân trước khi đi hợp tác lao động ở nước ngoài đã hưởng trợ cấp thôi việc hoặc 
phục viên, xuất ngũ; quân nhân, công nhân viên quốc phòng sau khi về nước đã được Bộ Quốc 
phòng lập hồ sơ giải quyết chế độ phục viên, xuất ngũ riêng đối với thời gian trước khi đi hợp tác lao 
động ở nước ngoài và cấp “Giấy chứng nhận thời gian đi hợp tác lao động ở nước ngoài” thì do Sở 
Nội vụ xác nhận; 
d) Đơn đề nghị tính thời gian công tác hưởng chế độ hưu trí, tử tuất đối với người lao động đã nghỉ 
việc. 
2. Hồ sơ đối với trường hợp người đi làm việc ở nước ngoài theo hình thức hợp tác trực tiếp giữa các 
bộ, địa phương của Nhà nước ta với các tổ chức kinh tế của nước ngoài bao gồm: 
a) Hồ sơ quy định tại các điểm a, c và d khoản 1 Điều này; 
b) Bản chính Quyết định cử đi làm việc có thời hạn ở nước ngoài hoặc bản sao Quyết định trong 
trường hợp người lao động được cử đi làm việc có thời hạn ở nước ngoài bằng một Quyết định 
chung cho nhiều người. 
Trường hợp không còn bản chính Quyết định cử đi làm việc có thời hạn ở nước ngoài thì được thay 
thế bằng bản sao Quyết định có xác nhận của bộ chủ quản đối với người lao động làm việc ở nước 
ngoài theo hình thức hợp tác do bộ cử đi hoặc xác nhận của Sở Nội vụ đối với người lao động do địa 
phương cử đi. 
Đối với trường hợp không có Quyết định cử đi làm việc có thời hạn ở nước ngoài thì phải có xác nhận 
bằng văn bản của thủ trưởng cơ quan, đơn vị cử người lao động, trong đó ghi rõ thời gian người lao 
động được cử đi làm việc có thời hạn ở nước ngoài và phải chịu trách nhiệm trước pháp luật về nội 
dung xác nhận. Trường hợp cơ quan, đơn vị cử đi không còn tồn tại thì cơ quan quản lý cấp trên trực 
tiếp xác nhận và chịu trách nhiệm trước pháp luật về nội dung xác nhận. 
3. Hồ sơ đối với trường hợp người đi học tập, thực tập ở nước ngoài bao gồm: 
a) Hồ sơ quy định tại các điểm a, c và d khoản 1 Điều này; 
b) Bản chính Quyết định cử đi học tập, thực tập có thời hạn ở nước ngoài hoặc bản sao Quyết định 
trong trường hợp người lao động được cử đi học tập, thực tập có thời hạn ở nước ngoài bằng một 
Quyết định chung cho nhiều người. 
Trường hợp không còn bản chính Quyết định cử đi học tập, thực tập có thời hạn ở nước ngoài thì 
được thay thế bằng bản sao Quyết định có xác nhận của đơn vị cử đi. 
Đối với trường hợp không có Quyết định cử đi học tập, thực tập có thời hạn ở nước ngoài thì phải có 
xác nhận bằng văn bản của thủ trưởng cơ quan, đơn vị cử người lao động, trong đó ghi rõ thời gian 
người lao động được cử đi học tập, thực tập có thời hạn ở nước ngoài và phải chịu trách nhiệm trước 
pháp luật về nội dung xác nhận. Trường hợp cơ quan, đơn vị cử đi không còn tồn tại thì cơ quan 
quản lý cấp trên trực tiếp xác nhận và chịu trách nhiệm trước pháp luật về nội dung xác nhận. 
4. Hồ sơ đối với trường hợp người đi làm chuyên gia theo Hiệp định của Chính phủ bao gồm: 
a) Hồ sơ quy định tại các điểm a, c và d khoản 1 Điều này; 
b) Bản chính Quyết định cử đi làm chuyên gia ở nước ngoài hoặc bản sao Quyết định trong trường 
hợp người lao động được cử đi làm chuyên gia bằng một Quyết định chung cho nhiều người. 
Trường hợp không còn bản chính Quyết định cử đi làm chuyên gia ở nước ngoài thì được thay thế 
bằng bản sao Quyết định có xác nhận của đơn vị cử đi. 
Đối với trường hợp không có Quyết định cử đi làm chuyên gia ở nước ngoài thì phải có xác nhận 
bằng văn bản của thủ trưởng cơ quan, đơn vị cử người lao động, trong đó ghi rõ thời gian người lao 
động được cử đi làm chuyên gia ở nước ngoài và phải chịu trách nhiệm trước pháp luật về nội dung 
xác nhận. Trường hợp cơ quan, đơn vị cử đi không còn tồn tại thì cơ quan quản lý cấp trên trực tiếp 
xác nhận và chịu trách nhiệm trước pháp luật về nội dung xác nhận; 
c) Giấy xác nhận của cơ quan quản lý chuyên gia về việc đã hoàn thành nghĩa vụ đóng góp cho ngân 
sách nhà nước và đóng bảo hiểm xã hội theo quy định của Nhà nước của chuyên gia trong thời gian 
làm việc ở nước ngoài.

[RULES]
{"id": "LAB-11-D36-000", "type": "condition", "premises": ["worked_before_01_01_1995", "has_full_contribution_time"], "conclusion": "must_submit_application_for_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 36 khoản 1 điểm a", "exception_to": "", "quote": "Hồ sơ đối với trường hợp người đi lao động có thời gian ở nước ngoài theo Hiệp định của Chính phủ và người đi làm đội trưởng, phiên dịch, cán bộ vùng do nước ngoài trả lương bao gồm..."}
{"id": "LAB-11-D36-001", "type": "condition", "premises": ["worked_before_01_01_1995", "has_full_contribution_time"], "conclusion": "must_submit_application_for_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 36 khoản 1 điểm b", "exception_to": "", "quote": "Bản chính “Thông báo chuyển trả” hoặc “Quyết định chuyển trả” của Cục Hợp tác quốc tế về lao động..."}
{"id": "LAB-11-D36-002", "type": "condition", "premises": ["worked_before_01_01_1995", "has_full_contribution_time"], "conclusion": "must_submit_application_for_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 36 khoản 1 điểm c", "exception_to": "", "quote": "Giấy xác nhận chưa được giải quyết trợ cấp thôi việc, trợ cấp một lần..."}
{"id": "LAB-11-D36-003", "type": "condition", "premises": ["worked_before_01_01_1995"], "conclusion": "must_submit_application_for_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 36 khoản 1 điểm d", "exception_to": "", "quote": "Đơn đề nghị tính thời gian công tác hưởng chế độ hưu trí, tử tuất đối với người lao động đã nghỉ việc."}
{"id": "LAB-11-D36-004", "type": "condition", "premises": ["worked_before_01_01_1995"], "conclusion": "must_submit_application_for_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 36 khoản 2 điểm a", "exception_to": "", "quote": "Hồ sơ quy định tại các điểm a, c và d khoản 1 Điều này."}
{"id": "LAB-11-D36-005", "type": "condition", "premises": ["worked_before_01_01_1995"], "conclusion": "must_submit_application_for_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 36 khoản 2 điểm b", "exception_to": "", "quote": "Bản chính Quyết định cử đi làm việc có thời hạn ở nước ngoài..."}
{"id": "LAB-11-D36-006", "type": "condition", "premises": ["worked_before_01_01_1995"], "conclusion": "must_submit_application_for_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 36 khoản 3 điểm a", "exception_to": "", "quote": "Hồ sơ quy định tại các điểm a, c và d khoản 1 Điều này."}
{"id": "LAB-11-D36-007", "type": "condition", "premises": ["worked_before_01_01_1995"], "conclusion": "must_submit_application_for_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 36 khoản 3 điểm b", "exception_to": "", "quote": "Bản chính Quyết định cử đi học tập, thực tập có thời hạn ở nước ngoài..."}
{"id": "LAB-11-D36-008", "type": "condition", "premises": ["worked_before_01_01_1995"], "conclusion": "must_submit_application_for_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 36 khoản 4 điểm a", "exception_to": "", "quote": "Hồ sơ quy định tại các điểm a, c và d khoản 1 Điều này."}
{"id": "LAB-11-D36-009", "type": "condition", "premises": ["worked_before_01_01_1995"], "conclusion": "must_submit_application_for_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 36 khoản 4 điểm b", "exception_to": "", "quote": "Bản chính Quyết định cử đi làm chuyên gia ở nước ngoài..."}


######## 11_nghi_dinh_158_2025_ND-CP — Điều 37. Giải quyết tính thời gian công tác đối với người lao động đi hợp tác lao động trước
[NGUYÊN VĂN]
Điều 37. Giải quyết tính thời gian công tác đối với người lao động đi hợp tác lao động trước 
ngày 01 tháng 01 năm 1995 
1. Đối với trường hợp người lao động đã nghỉ việc: 
a) Người lao động nộp hồ sơ quy định tại Điều 36 của Nghị định này cho đơn vị quản lý cuối cùng nơi 
người lao động làm việc. Trường hợp đơn vị quản lý cuối cùng không còn tồn tại thì người lao động 
nộp hồ sơ cho cơ quan quản lý cấp trên trực tiếp; 
b) Đơn vị quản lý cuối cùng của người lao động hoặc cơ quan quản lý cấp trên trực tiếp trong trường 
hợp đơn vị quản lý cuối cùng không còn tồn tại có trách nhiệm tiếp nhận hồ sơ và chuyển hồ sơ của 
người lao động kèm theo văn bản đề nghị gửi cơ quan bảo hiểm xã hội nơi đơn vị đóng bảo hiểm xã 
hội; 
c) Cơ quan bảo hiểm xã hội có trách nhiệm tiếp nhận hồ sơ từ người sử dụng lao động hoặc người 
lao động để giải quyết ghi nhận thời gian đóng bảo hiểm xã hội cho người lao động trong thời hạn 15 
ngày làm việc kể từ ngày nhận đủ hồ sơ theo quy định; trường hợp không giải quyết thì phải trả lời 
bằng văn bản và nêu rõ lý do. 
2. Đối với trường hợp người lao động đang đóng bảo hiểm xã hội: 
a) Người lao động có trách nhiệm bổ sung hồ sơ quy định tại Điều 36 của Nghị định này cho đơn vị 
sử dụng lao động khi được yêu cầu; 
b) Đơn vị sử dụng lao động có trách nhiệm chuyển hồ sơ của người lao động kèm theo văn bản đề 
nghị gửi cơ quan bảo hiểm xã hội nơi đơn vị đóng bảo hiểm xã hội; 
c) Cơ quan bảo hiểm xã hội có trách nhiệm tiếp nhận hồ sơ và giải quyết theo quy định tại điểm c 
khoản 1 Điều này. 
3. Đối với trường hợp người lao động đã chết sau khi về nước nhưng thân nhân chưa được hưởng 
chế độ tử tuất: 
a) Thân nhân của người lao động nộp hồ sơ theo quy định tại Điều 36 của Nghị định này, khoản 1 
Điều 90 của Luật Bảo hiểm xã hội kèm theo đơn đề nghị giải quyết chế độ tử tuất cho đơn vị quản lý 
cuối cùng của người lao động (theo Mẫu số 03 Phụ lục II ban hành kèm theo Nghị định này). Trường 
hợp đơn vị quản lý cuối cùng không còn tồn tại thì thân nhân của người lao động nộp hồ sơ cho cơ 
quan quản lý cấp trên trực tiếp; 
b) Đơn vị quản lý cuối cùng của người lao động hoặc cơ quan quản lý cấp trên trực tiếp trong trường 
hợp đơn vị quản lý cuối cùng không còn tồn tại có trách nhiệm tiếp nhận, hướng dẫn thân nhân người 
lao động hoàn thiện hồ sơ và chuyển đến cơ quan bảo hiểm xã hội nơi đơn vị đóng bảo hiểm xã hội 
kèm theo công văn đề nghị giải quyết chế độ; 
c) Cơ quan bảo hiểm xã hội có trách nhiệm tiếp nhận hồ sơ và giải quyết chế độ tử tuất đối với thân 
nhân của người lao động trong thời hạn quy định tại khoản 3 Điều 91 của Luật Bảo hiểm xã hội. 
Trường hợp không giải quyết thì cơ quan bảo hiểm xã hội phải trả lời bằng văn bản và nêu rõ lý do.

[RULES]
{"id": "LAB-11-D37-000", "type": "condition", "premises": ["worked_before_01_01_1995"], "conclusion": "must_submit_application_to_last_management_unit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 37 khoản 1 điểm a", "exception_to": "", "quote": "Người lao động nộp hồ sơ quy định tại Điều 36 của Nghị định này cho đơn vị quản lý cuối cùng nơi người lao động làm việc."}
{"id": "LAB-11-D37-001", "type": "condition", "premises": ["not_worked_before_01_01_1995"], "conclusion": "must_submit_application_to_superior_agency", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 37 khoản 1 điểm a", "exception_to": "", "quote": "Trường hợp đơn vị quản lý cuối cùng không còn tồn tại thì người lao động nộp hồ sơ cho cơ quan quản lý cấp trên trực tiếp."}
{"id": "LAB-11-D37-002", "type": "condition", "premises": ["must_submit_application_to_last_management_unit"], "conclusion": "must_transfer_application_to_social_insurance_agency", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 37 khoản 1 điểm b", "exception_to": "", "quote": "Đơn vị quản lý cuối cùng của người lao động hoặc cơ quan quản lý cấp trên trực tiếp có trách nhiệm tiếp nhận hồ sơ và chuyển hồ sơ của người lao động kèm theo văn bản đề nghị gửi cơ quan bảo hiểm xã hội nơi đơn vị đóng bảo hiểm xã hội."}
{"id": "LAB-11-D37-003", "type": "condition", "premises": ["must_transfer_application_to_social_insurance_agency"], "conclusion": "must_process_application_within_15_days", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 37 khoản 1 điểm c", "exception_to": "", "quote": "Cơ quan bảo hiểm xã hội có trách nhiệm tiếp nhận hồ sơ từ người sử dụng lao động hoặc người lao động để giải quyết ghi nhận thời gian đóng bảo hiểm xã hội cho người lao động trong thời hạn 15 ngày làm việc kể từ ngày nhận đủ hồ sơ theo quy định."}
{"id": "LAB-11-D37-004", "type": "condition", "premises": ["is_under_management"], "conclusion": "must_complete_application_for_insurance", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 37 khoản 2 điểm a", "exception_to": "", "quote": "Người lao động có trách nhiệm bổ sung hồ sơ quy định tại Điều 36 của Nghị định này cho đơn vị sử dụng lao động khi được yêu cầu."}
{"id": "LAB-11-D37-005", "type": "condition", "premises": ["must_complete_application_for_insurance"], "conclusion": "must_transfer_application_to_social_insurance_agency", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 37 khoản 2 điểm b", "exception_to": "", "quote": "Đơn vị sử dụng lao động có trách nhiệm chuyển hồ sơ của người lao động kèm theo văn bản đề nghị gửi cơ quan bảo hiểm xã hội nơi đơn vị đóng bảo hiểm xã hội."}
{"id": "LAB-11-D37-006", "type": "condition", "premises": ["must_transfer_application_to_social_insurance_agency"], "conclusion": "must_process_application_as_per_point_c", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 37 khoản 2 điểm c", "exception_to": "", "quote": "Cơ quan bảo hiểm xã hội có trách nhiệm tiếp nhận hồ sơ và giải quyết theo quy định tại điểm c khoản 1 Điều này."}
{"id": "LAB-11-D37-007", "type": "condition", "premises": ["is_deceased"], "conclusion": "must_submit_application_for_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 37 khoản 3 điểm a", "exception_to": "", "quote": "Thân nhân của người lao động nộp hồ sơ theo quy định tại Điều 36 của Nghị định này, khoản 1 Điều 90 của Luật Bảo hiểm xã hội kèm theo đơn đề nghị giải quyết chế độ tử tuất cho đơn vị quản lý cuối cùng của người lao động."}
{"id": "LAB-11-D37-008", "type": "condition", "premises": ["must_submit_application_for_survivor_benefit"], "conclusion": "must_transfer_application_to_social_insurance_agency", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 37 khoản 3 điểm b", "exception_to": "", "quote": "Đơn vị quản lý cuối cùng của người lao động hoặc cơ quan quản lý cấp trên trực tiếp có trách nhiệm tiếp nhận, hướng dẫn thân nhân người lao động hoàn thiện hồ sơ và chuyển đến cơ quan bảo hiểm xã hội nơi đơn vị đóng bảo hiểm xã hội kèm theo công văn đề nghị giải quyết chế độ."}
{"id": "LAB-11-D37-009", "type": "condition", "premises": ["must_transfer_application_to_social_insurance_agency"], "conclusion": "must_process_survivor_benefit_application", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 37 khoản 3 điểm c", "exception_to": "", "quote": "Cơ quan bảo hiểm xã hội có trách nhiệm tiếp nhận hồ sơ và giải quyết chế độ tử tuất đối với thân nhân của người lao động trong thời hạn quy định tại khoản 3 Điều 91 của Luật Bảo hiểm xã hội."}


######## 11_nghi_dinh_158_2025_ND-CP — Điều 38. Tính thời gian công tác để hưởng bảo hiểm xã hội đối với người lao động làm việc
[NGUYÊN VĂN]
Điều 38. Tính thời gian công tác để hưởng bảo hiểm xã hội đối với người lao động làm việc 
thuộc khu vực nhà nước, nghỉ chờ việc từ ngày 01 tháng 11 năm 1987 đến trước ngày 01 
tháng 01 năm 1995 
1. Người lao động làm việc thuộc khu vực nhà nước, nghỉ chờ việc từ ngày 01 tháng 11 năm 1987 
đến trước ngày 01 tháng 01 năm 1995 do doanh nghiệp, cơ quan, tổ chức không sắp xếp, bố trí được 
việc làm, chưa giải quyết trợ cấp thôi việc hoặc bảo hiểm xã hội một lần, tính đến ngày 31 tháng 12 
năm 1994 vẫn còn có tên trong danh sách lao động của đơn vị thì được tính thời gian công tác trước 
khi nghỉ chờ việc để tính hưởng bảo hiểm xã hội. Đối với cán bộ xã có thời gian đảm nhiệm chức 
danh theo Nghị định số 09/1998/NĐ-CP, việc tính thời gian công tác hưởng bảo hiểm xã hội thực hiện 
theo quy định tại Điều 39 của Nghị định này. 
2. Hồ sơ đề nghị tính thời gian công tác trước khi nghỉ chờ việc bao gồm: 
a) Tờ khai đăng ký tham gia bảo hiểm xã hội của người lao động; 
b) Lý lịch gốc và lý lịch bổ sung (nếu có) của người lao động, quyết định tiếp nhận, hợp đồng lao 
động, các giấy tờ có liên quan khác như: quyết định nâng bậc lương, quyết định điều động hoặc quyết 
định chuyển công tác, quyết định phục viên xuất ngũ, chuyển ngành, giấy thôi trả lương; 
c) Danh sách của đơn vị có tên người lao động đến ngày 31 tháng 12 năm 1994 hoặc các giấy tờ xác 
định người lao động có tên trong danh sách của đơn vị đến ngày 31 tháng 12 năm 1994; 
d) Quyết định nghỉ chờ việc. Trường hợp không có quyết định nghỉ chờ việc thì phải có xác nhận 
bằng văn bản của thủ trưởng đơn vị tại thời điểm lập hồ sơ đề nghị cấp sổ bảo hiểm xã hội, trong đó 
đảm bảo người lao động có tên trong danh sách của đơn vị tại thời điểm có quyết định nghỉ chờ việc 
và chưa giải quyết trợ cấp thôi việc hoặc bảo hiểm xã hội một lần. Trường hợp đơn vị đó giải thể, thì 
do cơ quan quản lý cấp trên trực tiếp xác nhận. 
3. Trình tự, thời hạn giải quyết: 
a) Người lao động và người sử dụng lao động hoàn thiện hồ sơ quy định tại khoản 2 Điều này gửi cơ 
quan bảo hiểm xã hội; 
b) Trong thời hạn 15 ngày làm việc kể từ ngày nhận được hồ sơ từ người sử dụng lao động, cơ quan 
bảo hiểm xã hội phải giải quyết; trường hợp không giải quyết thì phải trả lời bằng văn bản và nêu rõ lý 
do.

[RULES]
{"id": "LAB-11-D38-000", "type": "condition", "premises": ["working_for_state_agency", "~not_allowed_to_work_in_hazardous_jobs", "started_si_before_1995", "not_require_security_deposit", "has_full_contribution_time"], "conclusion": "must_count_previous_work_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 38 khoản 1", "exception_to": "", "quote": "thì được tính thời gian công tác trước khi nghỉ chờ việc để tính hưởng bảo hiểm xã hội."}
{"id": "LAB-11-D38-001", "type": "lookup", "premises": [], "conclusion": "must_provide_documents_for_change_of_representative", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 38 khoản 2", "exception_to": "", "quote": "Hồ sơ đề nghị tính thời gian công tác trước khi nghỉ chờ việc bao gồm..."}
{"id": "LAB-11-D38-002", "type": "condition", "premises": ["must_complete_insurance_procedure", "must_submit_application_to_department"], "conclusion": "must_respond_in_writing_if_not_approved", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 38 khoản 3", "exception_to": "", "quote": "Trong thời hạn 15 ngày làm việc kể từ ngày nhận được hồ sơ từ người sử dụng lao động, cơ quan bảo hiểm xã hội phải giải quyết."}


######## 11_nghi_dinh_158_2025_ND-CP — Điều 39. Tính thời gian công tác hưởng bảo hiểm xã hội đối với cán bộ xã có thời gian đảm
[NGUYÊN VĂN]
Điều 39. Tính thời gian công tác hưởng bảo hiểm xã hội đối với cán bộ xã có thời gian đảm 
nhiệm chức danh theo Nghị định số 09/1998/NĐ-CP 
1. Cán bộ cấp xã có thời gian đảm nhiệm chức danh theo Nghị định số 09/1998/NĐ-CP (bao gồm cả 
chức danh khác có trong định biên được phê duyệt thuộc Ủy ban nhân dân theo quy định tại khoản 5 
Điều 3 Nghị định số 09/1998/NĐ-CP), nếu công tác liên tục đến ngày 01 tháng 01 năm 1998 và 
hưởng sinh hoạt phí theo Nghị định số 09/1998/NĐ-CP thì thời gian đảm nhiệm chức danh theo Nghị 
định số 09/1998/NĐ-CP trước ngày 01 tháng 01 năm 1998 được tính là thời gian đã đóng bảo hiểm 
xã hội. 
a) Trường hợp có thời gian là công nhân, viên chức Nhà nước chưa hưởng trợ cấp nghỉ việc một lần 
hoặc bảo hiểm xã hội một lần, được điều động về xã giữ chức danh theo Nghị định số 09/1998/NĐ-
CP thì được cộng nối thời gian là công nhân, viên chức Nhà nước với thời gian giữ chức danh theo 
Nghị định số 09/1998/NĐ-CP để tính hưởng bảo hiểm xã hội; 
b) Đối với cán bộ cấp xã thuộc chức danh quy định tại Nghị định số 09/1998/NĐ-CP, nếu trước ngày 
01 tháng 01 năm 1998 được cơ quan có thẩm quyền cử đi học chuyên môn, chính trị, sau khi hoàn 
thành nhiệm vụ khóa học tiếp tục giữ chức danh theo Nghị định số 09/1998/NĐ-CP thì thời gian đi học 
này được tính thời gian công tác liên tục để tính hưởng bảo hiểm xã hội. 
2. Người lao động có thời gian đảm nhiệm các chức danh (kể cả chức danh khác có trong định biên 
được phê duyệt thuộc Ủy ban nhân dân theo quy định tại khoản 5 Điều 3 Nghị định số 09/1998/NĐ-
CP) thuộc đối tượng đóng bảo hiểm xã hội theo quy định tại Nghị định số 09/1998/NĐ-CP mà trong 
thời gian đảm nhiệm các chức danh này được điều động, tuyển dụng vào quân đội nhân dân, công an 
nhân dân hoặc vào làm việc trong các cơ quan, đơn vị, doanh nghiệp của Nhà nước, tổ chức chính 
trị, tổ chức chính trị - xã hội trước ngày 01 tháng 01 năm 1998 thì thời gian đảm nhiệm các chức danh 
trên được tính là thời gian đã đóng bảo hiểm xã hội để cộng nối với thời gian đóng bảo hiểm xã hội 
sau khi được điều động, tuyển dụng để tính hưởng bảo hiểm xã hội. 
3. Đối với cán bộ cấp xã giữ chức danh theo Nghị định số 09/1998/NĐ-CP (bao gồm cả chức danh 
khác có trong định biên được phê duyệt thuộc Ủy ban nhân dân theo quy định tại khoản 5 Điều 3 Nghị 
định số 09/1998/NĐ-CP) có thời gian gián đoạn trước ngày 01 tháng 01 năm 1998 không quá 12 
tháng thì được cộng nối thời gian công tác trước đó với thời gian công tác sau này để tính hưởng bảo 
hiểm xã hội.

[RULES]
{"id": "LAB-11-D39-000", "type": "condition", "premises": ["is_local_official", "worked_continuously_until_1998", "received_allowance_under_09_1998"], "conclusion": "has_full_contribution_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 39 khoản 1", "exception_to": "", "quote": "thời gian đảm nhiệm chức danh theo Nghị định số 09/1998/NĐ-CP trước ngày 01 tháng 01 năm 1998 được tính là thời gian đã đóng bảo hiểm xã hội."}
{"id": "LAB-11-D39-001", "type": "condition", "premises": ["is_state_employee", "not_received_one_time_benefit", "assigned_to_local_office"], "conclusion": "can_count_previous_work_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 39 khoản 1 điểm a", "exception_to": "", "quote": "thời gian là công nhân, viên chức Nhà nước chưa hưởng trợ cấp nghỉ việc một lần hoặc bảo hiểm xã hội một lần, được điều động về xã giữ chức danh theo Nghị định số 09/1998/NĐ-CP thì được cộng nối thời gian là công nhân, viên chức Nhà nước với thời gian giữ chức danh theo Nghị định số 09/1998/NĐ-CP để tính hưởng bảo hiểm xã hội;"}
{"id": "LAB-11-D39-002", "type": "condition", "premises": ["is_local_official", "sent_for_training_before_1998", "continued_work_after_training"], "conclusion": "can_count_training_time_as_work_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 39 khoản 1 điểm b", "exception_to": "", "quote": "thời gian đi học này được tính thời gian công tác liên tục để tính hưởng bảo hiểm xã hội."}
{"id": "LAB-11-D39-003", "type": "condition", "premises": ["is_local_official", "assigned_to_military_or_police_before_1998"], "conclusion": "can_count_previous_work_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 39 khoản 2", "exception_to": "", "quote": "thời gian đảm nhiệm các chức danh trên được tính là thời gian đã đóng bảo hiểm xã hội để cộng nối với thời gian đóng bảo hiểm xã hội sau khi được điều động, tuyển dụng để tính hưởng bảo hiểm xã hội."}
{"id": "LAB-11-D39-004", "type": "condition", "premises": ["is_local_official", "interrupted_work_before_1998", "interruption_time_less_than_12_months"], "conclusion": "can_count_previous_work_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 39 khoản 3", "exception_to": "", "quote": "có thời gian gián đoạn trước ngày 01 tháng 01 năm 1998 không quá 12 tháng thì được cộng nối thời gian công tác trước đó với thời gian công tác sau này để tính hưởng bảo hiểm xã hội."}


######## 11_nghi_dinh_158_2025_ND-CP — Điều 40. Chế độ đối với người đang hưởng trợ cấp hằng tháng mà có thời gian đóng bảo hiểm
[NGUYÊN VĂN]
Điều 40. Chế độ đối với người đang hưởng trợ cấp hằng tháng mà có thời gian đóng bảo hiểm 
xã hội chưa được tính hưởng bảo hiểm xã hội 
Người lao động đang hưởng trợ cấp mất sức lao động hằng tháng và người có đủ điều kiện hưởng 
trợ cấp hằng tháng theo Quyết định số 91/2000/QĐ-TTg, Quyết định số 613/QĐ-TTg mà có thời gian 
đóng bảo hiểm xã hội chưa được tính hưởng bảo hiểm xã hội thì thực hiện như sau: 
1. Người lao động có thời gian đóng bảo hiểm xã hội (không bao gồm thời gian công tác đã được tính 
hưởng trợ cấp mất sức lao động) đủ điều kiện hưởng lương hưu thì được lựa chọn hưởng một chế 
độ như sau: 
a) Trường hợp lựa chọn hưởng lương hưu thì dừng hưởng trợ cấp mất sức lao động hằng tháng, trợ 
cấp hằng tháng từ tháng hưởng lương hưu; 
b) Trường hợp lựa chọn hưởng trợ cấp mất sức lao động hằng tháng, trợ cấp hằng tháng thì được 
giải quyết hưởng bảo hiểm xã hội một lần đối với thời gian đã đóng bảo hiểm xã hội. 
2. Người lao động có thời gian đóng bảo hiểm xã hội nhưng không đủ điều kiện hưởng lương hưu thì 
giải quyết hưởng bảo hiểm xã hội một lần đối với thời gian đã đóng bảo hiểm xã hội, không bao gồm 
thời gian công tác đã được tính hưởng trợ cấp mất sức lao động.

[RULES]
{"id": "LAB-11-D40-000", "type": "condition", "premises": ["is_receiving_monthly_allowance", "has_full_contribution_time"], "conclusion": "entitled_lump_sum", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 40 khoản 1", "exception_to": "", "quote": "Người lao động đang hưởng trợ cấp mất sức lao động hằng tháng và người có đủ điều kiện hưởng trợ cấp hằng tháng... thì được giải quyết hưởng bảo hiểm xã hội một lần đối với thời gian đã đóng bảo hiểm xã hội."}
{"id": "LAB-11-D40-001", "type": "condition", "premises": ["is_receiving_monthly_allowance", "~has_full_contribution_time"], "conclusion": "must_submit_application_for_lump_sum", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 40 khoản 1", "exception_to": "", "quote": "Người lao động có thời gian đóng bảo hiểm xã hội nhưng không đủ điều kiện hưởng lương hưu thì giải quyết hưởng bảo hiểm xã hội một lần đối với thời gian đã đóng bảo hiểm xã hội."}
{"id": "LAB-11-D40-002", "type": "condition", "premises": ["has_full_contribution_time", "pension_conditions_based_on_compulsory_si"], "conclusion": "suspend_benefits_regulated_by_si_law", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 40 khoản 1", "exception_to": "", "quote": "Trường hợp lựa chọn hưởng lương hưu thì dừng hưởng trợ cấp mất sức lao động hằng tháng."}
{"id": "LAB-11-D40-003", "type": "condition", "premises": ["not_enough_contribution_years"], "conclusion": "entitled_lump_sum", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 40 khoản 2", "exception_to": "", "quote": "Người lao động có thời gian đóng bảo hiểm xã hội nhưng không đủ điều kiện hưởng lương hưu thì giải quyết hưởng bảo hiểm xã hội một lần đối với thời gian đã đóng bảo hiểm xã hội."}


######## 11_nghi_dinh_158_2025_ND-CP — Điều 41. Chế độ đối với người lao động đã có quyết định nghỉ việc chờ giải quyết chế độ hưu
[NGUYÊN VĂN]
Điều 41. Chế độ đối với người lao động đã có quyết định nghỉ việc chờ giải quyết chế độ hưu 
trí, trợ cấp hằng tháng 
Chế độ đối với người lao động đã có quyết định nghỉ việc chờ giải quyết chế độ hưu trí, trợ cấp hằng 
tháng được thực hiện theo khoản 10 Điều 141 của Luật Bảo hiểm xã hội và được quy định chi tiết như 
sau: 
1. Người lao động có từ đủ 15 năm đóng bảo hiểm xã hội trở lên và có văn bản của cơ quan bảo hiểm 
xã hội xác nhận về việc chờ đủ điều kiện về tuổi đời để hưởng lương hưu được quy định tại Nghị định 
số 12/CP ngày 26 tháng 01 năm 1995 được sửa đổi, bổ sung một số điều theo Nghị định số 
01/2003/NĐ-CP ngày 09 tháng 01 năm 2003 của Chính phủ (sau đây được viết là Nghị định số 
12/CP) thì được hưởng lương hưu khi nam đủ 60 tuổi, nữ đủ 55 tuổi. Mức lương hưu được tính theo 
quy định của Nghị định số 12/CP và được điều chỉnh theo các quy định về điều chỉnh lương hưu, trợ 
cấp bảo hiểm xã hội và trợ cấp hằng tháng của từng thời kỳ. 
Trong thời gian người lao động nghỉ chờ để hưởng lương hưu mà bị chết thì thân nhân được giải 
quyết chế độ tử tuất theo quy định của Luật Bảo hiểm xã hội. 
2. Cán bộ xã thuộc đối tượng điều chỉnh của Nghị định số 09/1998/NĐ-CP đã có quyết định hoặc giấy 
chứng nhận chờ đủ điều kiện về tuổi đời để hưởng trợ cấp hằng tháng của cơ quan bảo hiểm xã hội 
thì được hưởng trợ cấp hằng tháng khi nam đủ 55 tuổi, nữ đủ 50 tuổi. Mức trợ cấp hằng tháng được 
tính theo quy định của Nghị định số 09/1998/NĐ-CP và được điều chỉnh theo các quy định về điều 
chỉnh lương hưu, trợ cấp bảo hiểm xã hội và trợ cấp hằng tháng của từng thời kỳ. 
Trong thời gian cán bộ xã nghỉ chờ để hưởng trợ cấp hằng tháng mà bị chết thì thân nhân được giải 
quyết chế độ tử tuất theo quy định của Luật Bảo hiểm xã hội. Mức trợ cấp tuất một lần tính trên mức 
bình quân sinh hoạt phí của 5 năm cuối trước khi nghỉ việc được quy đổi theo mức lương cơ sở tại 
tháng cán bộ xã chết. Kể từ khi mức lương cơ sở bị bãi bỏ thì quy đổi tương ứng theo mức tham 
chiếu. 
3. Trường hợp trong thời gian chờ đủ điều kiện về tuổi đời để hưởng lương hưu hoặc trợ cấp hằng 
tháng mà người lao động tiếp tục tham gia bảo hiểm xã hội thì được tính cộng nối thời gian công tác 
đã được ghi nhận trong quyết định hoặc giấy chứng nhận chờ đủ điều kiện về tuổi đời để hưởng 
lương hưu hoặc trợ cấp hằng tháng với thời gian đóng bảo hiểm xã hội sau này để tính hưởng bảo 
hiểm xã hội theo quy định của Luật Bảo hiểm xã hội. 
4. Trường hợp đối tượng quy định tại khoản 1 và khoản 2 Điều này mà được tính cộng nối thời gian 
công tác trước ngày 01 tháng 01 năm 1995 đối với người chờ hưởng lương hưu và trước ngày 01 
tháng 01 năm 1998 đối với người chờ hưởng trợ cấp hằng tháng để tính hưởng bảo hiểm xã hội thì tỷ 
lệ hưởng lương hưu hoặc tỷ lệ hưởng trợ cấp hằng tháng vẫn được tính theo chính sách tại thời điểm 
người lao động nghỉ chờ.

[RULES]
{"id": "LAB-11-D41-000", "type": "condition", "premises": ["has_full_contribution_time", "received_request_document"], "conclusion": "entitled_pension", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 41 khoản 1", "exception_to": "", "quote": "Người lao động có từ đủ 15 năm đóng bảo hiểm xã hội trở lên và có văn bản của cơ quan bảo hiểm xã hội xác nhận về việc chờ đủ điều kiện về tuổi đời để hưởng lương hưu..."}
{"id": "LAB-11-D41-001", "type": "condition", "premises": ["has_full_contribution_time", "is_within_90_days_of_death"], "conclusion": "survivor_benefit_regulated_by_si_law", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 41 khoản 1", "exception_to": "", "quote": "Trong thời gian người lao động nghỉ chờ để hưởng lương hưu mà bị chết thì thân nhân được giải quyết chế độ tử tuất..."}
{"id": "LAB-11-D41-002", "type": "condition", "premises": ["has_full_contribution_time_by_state", "received_request_document"], "conclusion": "higher_monthly_allowance", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 41 khoản 2", "exception_to": "", "quote": "Cán bộ xã thuộc đối tượng điều chỉnh của Nghị định số 09/1998/NĐ-CP đã có quyết định hoặc giấy chứng nhận chờ đủ điều kiện về tuổi đời để hưởng trợ cấp hằng tháng..."}
{"id": "LAB-11-D41-003", "type": "condition", "premises": ["has_full_contribution_time_by_state", "is_within_90_days_of_death"], "conclusion": "survivor_benefit_regulated_by_si_law", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 41 khoản 2", "exception_to": "", "quote": "Trong thời gian cán bộ xã nghỉ chờ để hưởng trợ cấp hằng tháng mà bị chết thì thân nhân được giải quyết chế độ tử tuất..."}
{"id": "LAB-11-D41-004", "type": "condition", "premises": ["has_full_contribution_time", "started_si_before_1995"], "conclusion": "can_preserve_contribution_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 41 khoản 3", "exception_to": "", "quote": "Trường hợp trong thời gian chờ đủ điều kiện về tuổi đời để hưởng lương hưu hoặc trợ cấp hằng tháng mà người lao động tiếp tục tham gia bảo hiểm xã hội thì được tính cộng nối thời gian công tác..."}
{"id": "LAB-11-D41-005", "type": "condition", "premises": ["has_full_contribution_time", "started_si_before_1995"], "conclusion": "entitled_pension", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 41 khoản 4", "exception_to": "", "quote": "Trường hợp đối tượng quy định tại khoản 1 và khoản 2 Điều này mà được tính cộng nối thời gian công tác trước ngày 01 tháng 01 năm 1995..."}


######## 11_nghi_dinh_158_2025_ND-CP — Điều 42. Chế độ đối với người lao động đang nghỉ việc hưởng chế độ ốm đau do mắc bệnh
[NGUYÊN VĂN]
Điều 42. Chế độ đối với người lao động đang nghỉ việc hưởng chế độ ốm đau do mắc bệnh 
thuộc danh mục bệnh cần chữa trị dài ngày hoặc đang nghỉ việc hưởng chế độ thai sản theo 
quy định của Luật Bảo hiểm xã hội số 58/2014/QH13 
1. Người lao động nghỉ việc do mắc bệnh thuộc Danh mục bệnh cần chữa trị dài ngày do Bộ Y tế ban 
hành đang hưởng chế độ ốm đau trước ngày 01 tháng 7 năm 2025 và từ ngày 01 tháng 7 năm 2025 
vẫn đang nghỉ việc hưởng trợ cấp ốm đau thì tiếp tục thực hiện chế độ ốm đau theo quy định của Luật 
Bảo hiểm xã hội số 58/2014/QH13. 
Đối với trường hợp hưởng chế độ ốm đau do mắc bệnh thuộc Danh mục bệnh cần chữa trị dài ngày 
do Bộ Y tế ban hành mà hồ sơ đề nghị hưởng có ngày bắt đầu nghỉ hưởng chế độ ốm đau từ ngày 01 
tháng 7 năm 2025 trở đi thì áp dụng quy định tại Luật Bảo hiểm xã hội số 41/2024/QH15. 
2. Người lao động đang nghỉ việc hưởng chế độ thai sản trước ngày 01 tháng 7 năm 2025 và từ ngày 
01 tháng 7 năm 2025 vẫn đang hưởng chế độ thai sản thì tiếp tục thực hiện chế độ thai sản theo quy 
định tại mục 2 Chương III của Luật Bảo hiểm xã hội số 58/2014/QH13. 
Chương VII 
ĐIỀU KHOẢN THI HÀNH

[RULES]
{"id": "LAB-11-D42-000", "type": "condition", "premises": ["health_not_recovered_after_long_illness", "started_si_before_2025"], "conclusion": "sickness_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 42 khoản 1", "exception_to": "", "quote": "Người lao động nghỉ việc do mắc bệnh thuộc Danh mục bệnh cần chữa trị dài ngày... thì tiếp tục thực hiện chế độ ốm đau theo quy định của Luật Bảo hiểm xã hội số 58/2014/QH13."}
{"id": "LAB-11-D42-001", "type": "condition", "premises": ["health_not_recovered_after_long_illness", "started_si_after_2025"], "conclusion": "sickness_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 42 khoản 1", "exception_to": "Luật Bảo hiểm xã hội số 41/2024/QH15", "quote": "Đối với trường hợp hưởng chế độ ốm đau do mắc bệnh thuộc Danh mục bệnh cần chữa trị dài ngày... thì áp dụng quy định tại Luật Bảo hiểm xã hội số 41/2024/QH15."}
{"id": "LAB-11-D42-002", "type": "condition", "premises": ["worker_continue_working", "meets_conditions_for_maternity_benefit", "has_not_taken_60_days_leave"], "conclusion": "maternity_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 42 khoản 2", "exception_to": "", "quote": "Người lao động đang nghỉ việc hưởng chế độ thai sản trước ngày 01 tháng 7 năm 2025... thì tiếp tục thực hiện chế độ thai sản theo quy định tại mục 2 Chương III của Luật Bảo hiểm xã hội số 58/2014/QH13."}


######## 11_nghi_dinh_158_2025_ND-CP — Điều 43. Sửa đổi, bổ sung một số văn bản quy phạm pháp luật có liên quan đến bảo hiểm xã
[NGUYÊN VĂN]
Điều 43. Sửa đổi, bổ sung một số văn bản quy phạm pháp luật có liên quan đến bảo hiểm xã 
hội 
1. Sửa đổi, bổ sung một số điều của Nghị định số 88/2020/NĐ-CP ngày 28 tháng 7 năm 2020 của 
Chính phủ quy định chi tiết và hướng dẫn thi hành một số điều của Luật An toàn, vệ sinh lao động về 
bảo hiểm tai nạn lao động, bệnh nghề nghiệp bắt buộc như sau: 
a) Sửa đổi, bổ sung khoản 1 Điều 2 như sau: 
“1. Người lao động quy định tại các điểm a, b, c, d, đ, e, i và l khoản 1 Điều 2 của Luật Bảo hiểm xã 
hội tham gia bảo hiểm tai nạn lao động, bệnh nghề nghiệp bắt buộc. 
Người lao động là công dân nước ngoài làm việc tại Việt Nam quy định tại khoản 2 Điều 2 của Luật 
Bảo hiểm xã hội tham gia bảo hiểm tai nạn lao động, bệnh nghề nghiệp bắt buộc và thực hiện chế độ 
bảo hiểm tai nạn lao động, bệnh nghề nghiệp theo quy định tại Mục 3 của Luật An toàn, vệ sinh lao 
động và quy định tại Nghị định này.” 
b) Sửa đổi điểm b và điểm c khoản 3 Điều 11 như sau: 
“b) Thời gian hưởng chế độ thai sản của người lao động chấm dứt hợp đồng lao động, hợp đồng làm 
việc hoặc thôi việc trước thời điểm sinh con hoặc nhận con nuôi dưới 06 tháng tuổi quy định tại khoản 
4 Điều 50 của Luật Bảo hiểm xã hội không được tính là thời gian đã đóng bảo hiểm vào Quỹ bảo hiểm 
tai nạn lao động, bệnh nghề nghiệp; 
c) Trường hợp lao động nữ trở lại làm việc trước khi hết thời gian nghỉ việc hưởng chế độ thai sản khi 
sinh con theo quy định tại khoản 4 Điều 139 của Bộ luật Lao động thì thời gian từ khi nghỉ việc hưởng 
chế độ thai sản đến khi trở lại làm việc được tính là thời gian đóng bảo hiểm vào Quỹ bảo hiểm tai 
nạn lao động, bệnh nghề nghiệp, kể từ thời điểm trở lại làm việc thì lao động nữ vẫn được hưởng trợ 
cấp thai sản cho đến khi hết thời hạn quy định tại khoản 1 Điều 53 của Luật Bảo hiểm xã hội nhưng 
người sử dụng lao động phải đóng bảo hiểm vào Quỹ bảo hiểm tai nạn lao động, bệnh nghề nghiệp.” 
c) Sửa đổi Điều 39 như sau: 
“Điều 39. Chi tổ chức và hoạt động bảo hiểm tai nạn lao động, bệnh nghề nghiệp 
Chi tổ chức và hoạt động bảo hiểm tai nạn lao động, bệnh nghề nghiệp thực hiện theo quy định tại 
Điều 120 của Luật Bảo hiểm xã hội và quy định của pháp luật về quản lý tài chính đối với Bảo hiểm xã 
hội Việt Nam.” 
2. Sửa đổi, bổ sung một số điều của Nghị định số 58/2020/NĐ-CP ngày 27 tháng 5 năm 2020 của 
Chính phủ quy định mức đóng bảo hiểm xã hội bắt buộc vào Quỹ bảo hiểm tai nạn lao động, bệnh 
nghề nghiệp như sau: 
a) Sửa đổi, bổ sung khoản 1 Điều 4 như sau: 
“1. Người sử dụng lao động hằng tháng đóng trên tiền lương làm căn cứ đóng bảo hiểm xã hội bắt 
buộc của đối tượng quy định tại các điểm a, b, c, d, đ, e, i và l khoản 1 Điều 2 và khoản 2 Điều 2 của 
Luật Bảo hiểm xã hội theo một trong các mức sau: 
a) Mức đóng bình thường bằng 0,5% tiền lương làm căn cứ đóng bảo hiểm xã hội bắt buộc; đồng thời 
được áp dụng đối với người lao động là cán bộ, công chức, viên chức và người thuộc lực lượng vũ 
trang thuộc các cơ quan của Đảng, Nhà nước, tổ chức chính trị - xã hội, quân đội, công an, đơn vị sự 
nghiệp công lập sử dụng ngân sách nhà nước; 
b) Mức đóng bằng 0,3% tiền lương làm căn cứ đóng bảo hiểm xã hội bắt buộc được áp dụng đối với 
doanh nghiệp bảo đảm điều kiện theo quy định tại Điều 5 của Nghị định này.” 
b) Bỏ khoản 2 Điều 4.

[RULES]
{"id": "LAB-11-D43-000", "type": "condition", "premises": ["covered_point_a", "covered_point_b", "covered_point_d", "covered_point_e", "covered_point_i", "covered_point_l"], "conclusion": "compulsory_si", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 43 khoản 1 điểm a", "exception_to": "", "quote": "Người lao động quy định tại các điểm a, b, c, d, đ, e, i và l khoản 1 Điều 2 của Luật Bảo hiểm xã hội tham gia bảo hiểm tai nạn lao động, bệnh nghề nghiệp bắt buộc."}
{"id": "LAB-11-D43-001", "type": "condition", "premises": ["returns_to_work_before_maternity_leave_ends"], "conclusion": "must_count_work_stoppage_time_as_working_time", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 43 khoản 1 điểm b", "exception_to": "", "quote": "Thời gian từ khi nghỉ việc hưởng chế độ thai sản đến khi trở lại làm việc được tính là thời gian đóng bảo hiểm vào Quỹ bảo hiểm tai nạn lao động, bệnh nghề nghiệp."}
{"id": "LAB-11-D43-002", "type": "condition", "premises": [], "conclusion": "insurance_activity_regulated_by_si_law", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 43 khoản 1 điểm c", "exception_to": "", "quote": "Chi tổ chức và hoạt động bảo hiểm tai nạn lao động, bệnh nghề nghiệp thực hiện theo quy định tại Điều 120 của Luật Bảo hiểm xã hội."}
{"id": "LAB-11-D43-003", "type": "condition", "premises": ["has_full_contribution_time_by_employer"], "conclusion": "must_pay_salary_during_representation", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 43 khoản 2 điểm a", "exception_to": "", "quote": "Người sử dụng lao động hằng tháng đóng trên tiền lương làm căn cứ đóng bảo hiểm xã hội bắt buộc."}
{"id": "LAB-11-D43-004", "type": "condition", "premises": [], "conclusion": "~must_not_interfere_with_normal_operations", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 43 khoản 2 điểm b", "exception_to": "", "quote": "Bỏ khoản 2 Điều 4."}


######## 11_nghi_dinh_158_2025_ND-CP — Điều 44. Hiệu lực thi hành
[NGUYÊN VĂN]
Điều 44. Hiệu lực thi hành 
1. Nghị định này có hiệu lực thi hành từ ngày 01 tháng 7 năm 2025. 
2. Kể từ ngày Nghị định này có hiệu lực thi hành, các Nghị định của Chính phủ và các điều khoản sau 
đây hết hiệu lực thi hành: 
a) Nghị định số 115/2015/NĐ-CP ngày 11 tháng 11 năm 2015 của Chính phủ quy định chi tiết một số 
điều của Luật Bảo hiểm xã hội về bảo hiểm xã hội bắt buộc; 
b) Nghị định số 143/2018/NĐ-CP ngày 15 tháng 10 năm 2018 của Chính phủ quy định chi tiết Luật 
Bảo hiểm xã hội và Luật An toàn, vệ sinh lao động về bảo hiểm xã hội bắt buộc đối với người lao 
động là công dân nước ngoài làm việc tại Việt Nam; 
c) Khoản 2 Điều 3; các khoản 1, 3 Điều 7 và khoản 2 Điều 8 của Nghị định số 135/2020/NĐ-CP ngày 
18 tháng 11 năm 2020 của Chính phủ quy định về tuổi nghỉ hưu. 
Phụ lục III ban hành kèm theo Nghị định số 135/2020/NĐ-CP ngày 18 tháng 11 năm 2020 của Chính 
phủ quy định về tuổi nghỉ hưu; 
d) Các khoản 7, 8 và 9 Điều 38 của Nghị định số 33/2023/NĐ-CP ngày 10 tháng 6 năm 2023 của 
Chính phủ quy định về cán bộ, công chức cấp xã và người hoạt động không chuyên trách ở cấp xã, ở 
thôn, tổ dân phố.

[RULES]
{"id": "LAB-11-D44-000", "type": "condition", "premises": [], "conclusion": "effective_date_is_01_07_2025", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 44 khoản 1", "exception_to": "", "quote": "Nghị định này có hiệu lực thi hành từ ngày 01 tháng 7 năm 2025."}
{"id": "LAB-11-D44-001", "type": "condition", "premises": [], "conclusion": "previous_law_invalid", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 44 khoản 2", "exception_to": "", "quote": "Kể từ ngày Nghị định này có hiệu lực thi hành, các Nghị định của Chính phủ và các điều khoản sau đây hết hiệu lực thi hành."}
{"id": "LAB-11-D44-002", "type": "condition", "premises": [], "conclusion": "previous_law_invalid", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 44 khoản 2 điểm a", "exception_to": "", "quote": "Nghị định số 115/2015/NĐ-CP ngày 11 tháng 11 năm 2015 của Chính phủ quy định chi tiết một số điều của Luật Bảo hiểm xã hội về bảo hiểm xã hội bắt buộc."}
{"id": "LAB-11-D44-003", "type": "condition", "premises": [], "conclusion": "previous_law_invalid", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 44 khoản 2 điểm b", "exception_to": "", "quote": "Nghị định số 143/2018/NĐ-CP ngày 15 tháng 10 năm 2018 của Chính phủ quy định chi tiết Luật Bảo hiểm xã hội và Luật An toàn, vệ sinh lao động về bảo hiểm xã hội bắt buộc đối với người lao động là công dân nước ngoài làm việc tại Việt Nam."}
{"id": "LAB-11-D44-004", "type": "condition", "premises": [], "conclusion": "previous_law_invalid", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 44 khoản 2 điểm c", "exception_to": "", "quote": "Khoản 2 Điều 3; các khoản 1, 3 Điều 7 và khoản 2 Điều 8 của Nghị định số 135/2020/NĐ-CP ngày 18 tháng 11 năm 2020 của Chính phủ quy định về tuổi nghỉ hưu."}
{"id": "LAB-11-D44-005", "type": "condition", "premises": [], "conclusion": "previous_law_invalid", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 44 khoản 2 điểm d", "exception_to": "", "quote": "Các khoản 7, 8 và 9 Điều 38 của Nghị định số 33/2023/NĐ-CP ngày 10 tháng 6 năm 2023 của Chính phủ quy định về cán bộ, công chức cấp xã và người hoạt động không chuyên trách ở cấp xã, ở thôn, tổ dân phố."}


######## 11_nghi_dinh_158_2025_ND-CP — Điều 45. Trách nhiệm tổ chức thi hành
[NGUYÊN VĂN]
Điều 45. Trách nhiệm tổ chức thi hành 
1. Bộ trưởng Bộ Nội vụ có trách nhiệm hướng dẫn thi hành Nghị định này. 
2. Bộ trưởng Bộ Tài chính có trách nhiệm chỉ đạo: 
a) Hằng năm, Cục Thống kê có trách nhiệm cung cấp kịp thời cho Bảo hiểm xã hội Việt Nam chỉ số 
giá tiêu dùng bình quân năm tính theo gốc so sánh bình quân năm 1994 để xác định hệ số điều chỉnh 
tiền lương làm căn cứ đóng bảo hiểm xã hội theo quy định tại khoản 2 Điều 16 của Nghị định này; 
b) Hằng năm, Bảo hiểm xã hội Việt Nam có trách nhiệm công khai hệ số điều chỉnh tiền lương làm 
căn cứ đóng bảo hiểm xã hội quy định tại khoản 2 Điều 16 của Nghị định này. 
3. Các Bộ trưởng, Thủ trưởng cơ quan ngang Bộ, Thủ trưởng cơ quan thuộc Chính phủ, Chủ tịch Ủy 
ban nhân dân các cấp và tổ chức, cá nhân khác có liên quan chịu trách nhiệm thi hành Nghị định 
này./. 
 
Nơi nhận: 
- Ban Bí thư Trung ương Đảng; 
- Thủ tướng, các Phó Thủ tướng Chính phủ; 
- Các bộ, cơ quan ngang bộ, cơ quan thuộc Chính phủ; 
- HĐND, UBND các tỉnh, thành phố trực thuộc trung; 
- Văn phòng Trung ương và các Ban của Đảng; 
- Văn phòng Tổng Bí thư; 
- Văn phòng Chủ tịch nước; 
- Hội đồng Dân tộc và các Ủy ban của Quốc hội; 
- Văn phòng Quốc hội; 
- Tòa án nhân dân tối cao; 
- Viện kiểm sát nhân dân tối cao; 
- Kiểm toán nhà nước; 
- Ủy ban Trung ương Mặt trận Tổ quốc Việt Nam; 
- Cơ quan trung ương của các đoàn thể; 
- VPCP: BTCN, các PCN, Trợ lý TTg, TGĐ Cổng TTĐT, các 
Vụ, Cục, đơn vị trực thuộc, Công báo; 
- Lưu: VT, KTTH(2b) 
TM. CHÍNH PHỦ 
KT. THỦ TƯỚNG 
PHÓ THỦ TƯỚNG 
 
 
 
 
Hồ Đức Phớc 
 
PHỤ LỤC I 
CÔNG VIỆC KHAI THÁC THAN TRONG HẦM LÒ 
(Kèm theo Nghị định số 158/2025/NĐ-CP ngày 25 tháng 6 năm 2025 của Chính phủ) 
1. Khai thác mỏ hầm lò. 
2. Khoan đá bằng búa máy cầm tay trong hầm lò. 
3. Đội viên cứu hộ mỏ. 
4. Sửa chữa cơ điện trong hầm lò. 
5. Vận hành trạm quạt khí nén, điện, diezel, trạm sạc ắc quy trong hầm lò. 
6. Thợ sắt, thợ thoát nước trong hầm lò. 
7. Vận tải than trong hầm lò. 
8. Đo khí, đo gió, trực cửa gió, trắc địa, KCS trong hầm lò. 
9. Công nhân vận hành, sửa chữa các thiết bị trong hầm lò. 
10. Vận hành và phụ tàu điện, tàu ắc quy trong hầm lò. 
11. Vận hành, sửa chữa, nạp ắc quy trong hầm lò. 
12. Nghiệm thu các sản phẩm trong hầm lò. 
13. Thủ kho các loại trong hầm lò. 
14. Bảo vệ kho trong hầm lò. 
15. Quét dọn hầm vệ sinh, nạo vét bùn trong hầm lò. 
16. Vận chuyển vật liệu trong hầm lò. 
17. Trực gác tín hiệu trong hầm lò. 
18. Phục vụ bồi dưỡng trong hầm lò. 
19. Lắp đặt, sửa chữa hệ thống thông tin liên lạc trong hầm lò. 
20. Vận hành trạm mạng trong hầm lò. 
21. Trực gác cửa gió trong hầm lò. 
22. Chỉ đạo kỹ thuật trực tiếp trong hầm lò. 
23. Chỉ đạo sản xuất trực tiếp trong hầm lò (quản đốc, phó quản đốc, đội trưởng lò, lò trưởng). 
24. Nhân viên, công nhân giám sát an toàn trong hầm lò. 
 
PHỤ LỤC II 
DANH MỤC BIỂU MẪU 
(Kèm theo Nghị định số 158/2025/NĐ-CP ngày 25 tháng 6 năm 2025 của Chính phủ) 
STT 
Số thứ tự mẫu 
Tên mẫu 
1 
Mẫu số 01 
Đơn đề nghị xác nhận 
2 
Mẫu số 02 
Giấy xác nhận 
3 
Mẫu số 03 
Đơn đề nghị giải quyết chế độ tử tuất 
 
Mẫu số 01 (Dành cho người lao động) 
CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM 
Độc lập - Tự do - Hạnh phúc 
--------------- 
ĐƠN ĐỀ NGHỊ XÁC NHẬN 
Về thời gian đi hợp tác lao động để giải quyết chế độ bảo hiểm xã hội 
(Đối với người đi lao động có thời hạn ở nước ngoài theo Hiệp định Chính phủ, kể cả người đi làm đội 
trưởng, phiên dịch, cán bộ vùng) 
Kính gửi: Cục Quản lý lao động ngoài nước. 
Tên tôi là ……………………………………………………………………… 
Sinh ngày:……………………………………………………………………... 
Đơn vị cử đi hợp tác lao động:………………………………………………… 
Cơ quan chủ quản (Bộ, ngành):………………………………………………. 
Nước đến hợp tác lao động:…………………………………………………... 
Tên đơn vị, nhà máy đến làm việc:…………………………………………… 
Thời hạn đi hợp tác lao động theo Hiệp định từ…………….đến……………. 
Thời điểm về nước: ngày………..tháng…………năm……………. 
Lý do về nước:…………………………………………………………………. 
Được chuyển trả về đơn vị:…………………………………………………….. 
Hồ sơ kèm theo (nếu có) gồm:…………………………………………………. 
………………………………………………………………………………….. 
………………………………………………………………………………….. 
Khi về nước tôi chưa được giải quyết trợ cấp thôi việc theo quy định tại Thông tư số 12/TT-LB ngày 
3/8/1992 và Thông tư số 24/LB-TT ngày 19/9/1994 của Liên Bộ Lao động - Thương binh và Xã hội - 
Tài chính. 
Tôi xin cam đoan lời khai trên đây của tôi là đúng sự thật. Tôi xin chịu trách nhiệm trước pháp luật về 
lời khai của mình. 
 
…….., ngày.... tháng....... năm…… 
Người viết đơn 
(Ký và ghi rõ họ tên) 
 
Mẫu số 02 
BỘ NỘI VỤ 
CỤC QUẢN LÝ LAO ĐỘNG 
NGOÀI NƯỚC 
------- 
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM 
Độc lập - Tự do - Hạnh phúc 
--------------- 
Số: …/CQLLĐNN-XN 
Hà Nội, ngày …… tháng … năm …. 
 
GIẤY XÁC NHẬN 
Về thời gian đi hợp tác lao động để giải quyết chế độ bảo hiểm xã hội 
(Đối với người đi lao động có thời hạn ở nước ngoài theo Hiệp định của Chính phủ, kể cả người đi 
làm đội trưởng, phiên dịch, cán bộ vùng) 
Căn cứ hồ sơ do người lao động xuất trình (nếu có) và hồ sơ lưu trữ, Cục Quản lý lao động ngoài 
nước xác nhận: 
Ông (bà):……………………………………………………………………. 
Sinh ngày:……………………………………………………………………. 
Đi hợp tác lao động tại………….từ……………..đến………………….. 
Thời điểm về nước: ngày…….. tháng………năm……….. 
Về nước với lý do:………………………………………………………. 
Được chuyển trả về đơn vị:…………………………………………….. 
Ông (bà)…………………….(có hoặc không)……………………. tên trong danh sách đã được Cục 
Quản lý lao động ngoài nước duyệt hồ sơ để nhận trợ cấp cấp thôi việc theo quy định tại Thông tư số 
12/TT-LB ngày 3/8/1992 và Thông tư số 24/LB-TT ngày 19/9/1994 của Liên Bộ Lao động - Thương 
binh và Xã hội - Tài chính. 
Xác nhận này có giá trị thay thế Giấy chứng nhận của Ban quản lý lao động Việt Nam tại 
……………………… và Thông báo chuyển trả của Cục Quản lý lao động ngoài nước để xem xét tính 
thời gian công tác hưởng bảo hiểm xã hội. 
 
Nơi nhận: 
- Ông (bà) ………; 
- Lưu VT, Cục QLLĐNN. 
CỤC TRƯỞNG 
 
Mẫu số 03 (Dành cho thân nhân của người lao động) 
CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM 
Độc lập - Tự do - Hạnh phúc 
--------------- 
ĐƠN ĐỀ NGHỊ GIẢI QUYẾT CHẾ ĐỘ TỬ TUẤT 
Đối với người được cử đi công tác, học tập, làm việc có thời hạn ở nước ngoài 
đã chết sau khi về nước nhưng thân nhân chưa được hưởng trợ cấp tuất 
Kính gửi: …………………………………. 
Tên tôi là…………….………………….. Số căn cước công dân/………………… 
Hộ khẩu thường trú:………………………………………………………. là thân nhân (nêu rõ mối quan hệ 
thân nhân với người lao động):……………. của ông (bà)………………. Sinh 
ngày:……………………….. 
Được cử đi (hợp tác lao động, học tập, thực tập, làm chuyên gia):.......... tại (tên đơn vị, tổ chức và tên 
nước)............................................................... 
Đơn vị cử đi:………………………………………………………………… 
Cơ quan chủ quản (Bộ, ngành): ....................................................................... 
Thời hạn làm việc ghi trong Quyết định của đơn vị cử đi: từ ……..đến…….. 
Thời điểm về nước: ngày…………tháng……..năm…….. 
Lý do về nước:………………………………………………………………….. 
Được chuyển trả về đơn vị:…………………………………………………….. 
Ông (bà)………………..đã từ trần ngày…………tháng………..năm………. 
Từ khi về nước đến khi từ trần, ông (bà)……………………………….. chưa được giải quyết trợ cấp 
thôi việc, chế độ bảo hiểm xã hội. 
Tôi xin cam đoan lời khai trên đây của tôi là đúng sự thật. Tôi xin chịu trách nhiệm trước pháp luật về 
lời khai của mình. 
Đề nghị …………………..lập hồ sơ và làm thủ tục giải quyết chế độ tử tuất đối với ông 
(bà)………………………… 
 
…, ngày …… tháng…….năm……. 
Xác nhận của UBND xã, phường nơi cư trú 
(Ký, đóng dấu) 
…., ngày …..tháng…..năm….. 
Người viết đơn 
(Ký và ghi rõ họ tên) 
 
Ghi chú: 
- Mẫu này áp dụng đối với thân nhân của người lao động đã chết sau khi về nước nhưng thân nhân 
chưa được hưởng trợ cấp tuất; 
- Ủy ban nhân dân xã, phường xác nhận mối quan hệ của người viết đơn với người lao động.

[RULES]
{"id": "LAB-11-D45-000", "type": "condition", "premises": ["must_provide_conditions_for_negotiation", "has_full_contribution_time"], "conclusion": "must_publish_job_list_impacting_reproduction", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 45 khoản 2 điểm a", "exception_to": "", "quote": "Hằng năm, Cục Thống kê có trách nhiệm cung cấp kịp thời cho Bảo hiểm xã hội Việt Nam chỉ số giá tiêu dùng bình quân năm..."}
{"id": "LAB-11-D45-001", "type": "condition", "premises": ["must_provide_conditions_for_negotiation"], "conclusion": "must_publish_job_list_impacting_reproduction", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 45 khoản 2 điểm b", "exception_to": "", "quote": "Hằng năm, Bảo hiểm xã hội Việt Nam có trách nhiệm công khai hệ số điều chỉnh tiền lương..."}
{"id": "LAB-11-D45-002", "type": "condition", "premises": ["must_fulfill_chairman_responsibilities"], "conclusion": "is_responsible_for_decisions", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 45 khoản 3", "exception_to": "", "quote": "Các Bộ trưởng, Thủ trưởng cơ quan ngang Bộ, Thủ trưởng cơ quan thuộc Chính phủ, Chủ tịch Ủy ban nhân dân các cấp và tổ chức, cá nhân khác có liên quan chịu trách nhiệm thi hành Nghị định này."}
{"id": "LAB-11-D45-100", "type": "condition", "premises": ["is_worker_in_mine"], "conclusion": "must_have_safety_supervisor", "source": "11_nghi_dinh_158_2025_ND-CP, Điều 45 khoản 24", "exception_to": "", "quote": "Nhân viên, công nhân giám sát an toàn trong hầm lò."}
{"id": "LAB-11-D45-101", "type": "lookup", "premises": [], "conclusion": "application_requirements_for_si_confirmation", "source": "11_nghi_dinh_158_2025_ND-CP, Mẫu số 01", "exception_to": "", "quote": "Hồ sơ kèm theo (nếu có) gồm:..."}
{"id": "LAB-11-D45-102", "type": "lookup", "premises": [], "conclusion": "application_requirements_for_si_confirmation", "source": "11_nghi_dinh_158_2025_ND-CP, Mẫu số 02", "exception_to": "", "quote": "Căn cứ hồ sơ do người lao động xuất trình (nếu có) và hồ sơ lưu trữ..."}
{"id": "LAB-11-D45-103", "type": "lookup", "premises": [], "conclusion": "application_requirements_for_survivor_benefit", "source": "11_nghi_dinh_158_2025_ND-CP, Mẫu số 03", "exception_to": "", "quote": "Đơn đề nghị giải quyết chế độ tử tuất..."}
