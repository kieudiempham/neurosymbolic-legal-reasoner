# Predicate vocabulary cho việc tạo dataset

## A. Predicate CHUẨN (đã dùng trong KB viết tay, ưu tiên dùng đúng tên này)

| predicate | loại | nghĩa khi đúng | nghĩa khi sai |
|---|---|---|---|
| `signed_labor_contract` | input | Người lao động đã ký hợp đồng lao động. | Người lao động không ký hợp đồng lao động. |
| `paid_wage` | input | Người lao động được trả lương hoặc tiền công cho công việc. | Người lao động không được trả lương cho công việc. |
| `under_management` | input | Người lao động chịu sự quản lý, điều hành, giám sát của bên sử dụng lao động. | Người lao động không chịu sự quản lý, điều hành của bên sử dụng lao động. |
| `term_at_least_1_month` | input | Hợp đồng có thời hạn từ đủ 01 tháng trở lên. | Hợp đồng có thời hạn dưới 01 tháng. |
| `term_at_least_12_months` | input | Hợp đồng có thời hạn từ đủ 12 tháng trở lên. | Hợp đồng có thời hạn dưới 12 tháng. |
| `probation_only` | input | Người lao động chỉ ký hợp đồng thử việc, chưa ký hợp đồng lao động. | Người lao động không chỉ ký hợp đồng thử việc. |
| `foreign_citizen` | input | Người lao động là công dân nước ngoài. | Người lao động là công dân Việt Nam. |
| `part_time` | input | Người lao động làm việc không trọn thời gian. | Người lao động làm việc trọn thời gian. |
| `wage_at_least_min_base` | input | Tiền lương trong tháng của người lao động bằng hoặc cao hơn mức lương thấp nhất làm căn cứ đóng bảo hiểm xã hội. | Tiền lương trong tháng của người lao động thấp hơn mức lương thấp nhất làm căn cứ đóng bảo hiểm xã hội. |
| `enterprise_manager` | input | Người này là người quản lý doanh nghiệp. | Người này không phải là người quản lý doanh nghiệp. |
| `receives_salary` | input | Người này nhận tiền lương từ doanh nghiệp. | Người này không nhận tiền lương từ doanh nghiệp. |
| `receiving_pension` | input | Người lao động đang hưởng lương hưu. | Người lao động không hưởng lương hưu. |
| `domestic_worker` | input | Người lao động là người giúp việc gia đình. | Người lao động không phải là người giúp việc gia đình. |
| `intra_company_transfer` | input | Người lao động nước ngoài di chuyển trong nội bộ doanh nghiệp. | Người lao động nước ngoài không di chuyển trong nội bộ doanh nghiệp. |
| `retirement_age_at_signing` | input | Tại thời điểm ký hợp đồng, người lao động đã đủ tuổi nghỉ hưu. | Tại thời điểm ký hợp đồng, người lao động chưa đủ tuổi nghỉ hưu. |
| `contract_suspended` | input | Hợp đồng lao động đang tạm hoãn thực hiện. | Hợp đồng lao động không bị tạm hoãn. |
| `unpaid_14_days` | input | Trong tháng, người lao động không hưởng tiền lương từ 14 ngày làm việc trở lên. | Trong tháng, người lao động có hưởng lương phần lớn số ngày làm việc. |
| `agreed_contribution` | input | Người lao động và công ty thỏa thuận vẫn đóng bảo hiểm xã hội trong thời gian này. | Người lao động và công ty không có thỏa thuận về việc đóng bảo hiểm xã hội trong thời gian này. |
| `multiple_contracts` | input | Người lao động giao kết hợp đồng lao động với nhiều người sử dụng lao động. | Người lao động chỉ làm việc cho một người sử dụng lao động. |
| `reached_retirement_age` | input | Người lao động đã đủ tuổi nghỉ hưu. | Người lao động chưa đủ tuổi nghỉ hưu. |
| `contribution_15_years` | input | Người lao động đã đóng bảo hiểm xã hội bắt buộc từ đủ 15 năm trở lên. | Người lao động đóng bảo hiểm xã hội chưa đủ 15 năm. |
| `stopped_working` | input | Người lao động đã nghỉ việc. | Người lao động vẫn đang làm việc. |
| `terminated_participation` | input | Người lao động đã chấm dứt tham gia bảo hiểm xã hội. | Người lao động vẫn đang tham gia bảo hiểm xã hội. |
| `requested_lump_sum` | input | Người lao động đề nghị hưởng bảo hiểm xã hội một lần. | Người lao động không muốn hưởng bảo hiểm xã hội một lần. |
| `emigrating` | input | Người lao động ra nước ngoài để định cư. | Người lao động không ra nước ngoài định cư. |
| `serious_illness` | input | Người lao động đang mắc bệnh ung thư, bại liệt, xơ gan mất bù, lao nặng hoặc AIDS. | Người lao động không mắc bệnh hiểm nghèo. |
| `labor_relation` | derived | Giữa hai bên tồn tại quan hệ lao động. | Giữa hai bên không tồn tại quan hệ lao động. |
| `covered_point_a` | derived | Người lao động thuộc diện quy định tại điểm a khoản 1 Điều 2 Luật BHXH. | Người lao động không thuộc diện quy định tại điểm a khoản 1 Điều 2 Luật BHXH. |
| `compulsory_si` | derived | Người lao động thuộc đối tượng tham gia bảo hiểm xã hội bắt buộc. | Người lao động không thuộc đối tượng tham gia bảo hiểm xã hội bắt buộc. |
| `must_contribute_month` | derived | Người lao động phải đóng bảo hiểm xã hội bắt buộc trong tháng đó. | Người lao động không phải đóng bảo hiểm xã hội bắt buộc trong tháng đó. |
| `contribute_at_first_contract` | derived | Người lao động tham gia bảo hiểm xã hội bắt buộc theo hợp đồng lao động giao kết đầu tiên. | Người lao động không tham gia theo hợp đồng giao kết đầu tiên. |
| `voluntary_si_eligible` | derived | Người lao động thuộc đối tượng tham gia bảo hiểm xã hội tự nguyện. | Người lao động không thuộc đối tượng tham gia bảo hiểm xã hội tự nguyện. |
| `entitled_pension` | derived | Người lao động đủ điều kiện hưởng lương hưu. | Người lao động không đủ điều kiện hưởng lương hưu. |
| `entitled_lump_sum` | derived | Người lao động được hưởng bảo hiểm xã hội một lần. | Người lao động không được hưởng bảo hiểm xã hội một lần. |

## B. Predicate GỢI Ý (trích tự động, CHƯA chuẩn hoá — dùng lại nếu đúng nghĩa, nếu tên xấu thì đề xuất tên mới)

### Bảo hiểm xã hội

| predicate | loại | nghĩa khi đúng |
|---|---|---|
| `social_insurance_agency` | derived | Cơ quan bảo hiểm xã hội là cơ quan nhà nước. |
| `deceased` | input | Người lao động đã chết. |
| `is_worker_dead` | input | Người lao động đã chết. |
| `maternity_benefit` | derived | Người lao động được hưởng trợ cấp thai sản. |
| `worked_before_01_01_1995` | input | Người lao động đã làm việc trước ngày 01 tháng 01 năm 1995. |
| `must_respond_in_writing_if_not_approved` | derived | Cơ quan bảo hiểm xã hội phải trả lời bằng văn bản nếu không giải quyết. |
| `is_male_worker` | input | Người lao động là nam. |
| `sickness_benefit` | derived | Người lao động được hưởng trợ cấp ốm đau. |
| `contribution_20_years` | input | Người lao động đã đóng bảo hiểm xã hội bắt buộc từ đủ 20 năm trở lên. |
| `has_social_insurance_book` | input | Người lao động có sổ bảo hiểm xã hội. |
| `cham_dong_bhxh` | derived | Hành vi chậm đóng bảo hiểm xã hội xảy ra. |
| `has_full_contribution_time_by_state` | input | Người lao động có thời gian đóng bảo hiểm xã hội thuộc đối tượng thực hiện chế độ tiền lương do Nhà nước quy định. |
| `survivor_benefit` | derived | Người lao động được hưởng trợ cấp tử tuất. |
| `can_take_health_recovery_leave` | derived | Người lao động có thể nghỉ dưỡng sức, phục hồi sức khỏe. |
| `funeral_support` | derived | Người lao động được hỗ trợ chi phí mai táng. |
| `covered_point_d` | derived | Người lao động thuộc diện quy định tại điểm d khoản 1 Điều 2 Luật BHXH. |
| `has_request_document` | input | Người lao động có văn bản đề nghị hưởng trợ cấp. |
| `adopted_child_under_6_months` | input | Người lao động nhận nuôi con nuôi dưới 6 tháng tuổi. |
| `is_female_worker` | input | Người lao động là nữ. |
| `is_receiving_monthly_allowance` | input | Người lao động đang hưởng trợ cấp hằng tháng. |
| `is_civil_servant` | input | Người lao động là cán bộ, công chức, viên chức. |
| `has_given_birth` | input | Người lao động đã sinh con. |
| `is_business_owner` | input | Người lao động là chủ hộ kinh doanh của hộ kinh doanh có đăng ký kinh doanh. |
| `receive_health_insurance` | derived | Người thụ hưởng chế độ bảo hiểm xã hội được hưởng bảo hiểm y tế. |
| `contribution_30_years` | input | Người lao động đã đóng bảo hiểm xã hội bắt buộc từ đủ 30 năm trở lên. |
| `spouse_has_child_birth` | input | Vợ của người lao động đã sinh con. |
| `is_female_worker_with_surrogate_pregnancy` | input | Người lao động nữ mang thai hộ. |
| `must_transfer_application_to_social_insurance_agency` | derived | Hồ sơ của người lao động phải được chuyển đến cơ quan bảo hiểm xã hội. |
| `mother_dies_after_birth` | input | Mẹ chết sau khi sinh con. |
| `pension_benefit` | derived | Người lao động được hưởng lương hưu. |
| `can_preserve_contribution_time` | derived | Người lao động được bảo lưu thời gian đóng bảo hiểm xã hội. |
| `can_suspend_compulsory_si_contribution` | derived | Người sử dụng lao động có quyền tạm dừng đóng bảo hiểm xã hội bắt buộc. |
| `meets_conditions_for_maternity_benefit` | input | Người lao động đáp ứng đủ điều kiện hưởng chế độ thai sản. |
| `base_salary_abrogated` | input | Mức lương cơ sở đã bị bãi bỏ. |
| `is_local_official` | input | Người lao động là cán bộ cấp xã. |
| `is_military_officer` | input | Người lao động là sĩ quan, quân nhân chuyên nghiệp quân đội nhân dân. |
| `issued_insurance_book` | derived | Người tham gia bảo hiểm xã hội được cấp sổ bảo hiểm xã hội. |
| `advise_on_policy_changes` | derived | Tổ chức đại diện kiến nghị, tham gia xây dựng, sửa đổi, bổ sung chính sách về bảo hiểm xã hội. |
| `is_vietnamese_citizen` | input | Người này là công dân Việt Nam. |
| `female_worker_pregnant` | input | Người lao động nữ mang thai. |
| `returns_to_work_before_maternity_leave_ends` | input | Người lao động trở lại làm việc trước khi hết thời gian nghỉ thai sản. |
| `can_take_maternity_leave` | derived | Lao động nữ có thể nghỉ thai sản. |
| `suspend_pension_benefits` | derived | Người lao động bị tạm dừng hưởng lương hưu. |
| `terminate_pension_benefits` | derived | Người lao động bị chấm dứt hưởng lương hưu. |
| `detention_duration_at_least_14_days` | input | Thời gian tạm giam từ 14 ngày trở lên. |

### Doanh nghiệp

| predicate | loại | nghĩa khi đúng |
|---|---|---|
| `is_registered_enterprise` | input | Doanh nghiệp đã được đăng ký thành lập. |
| `valid_application` | derived | Hồ sơ hợp lệ là hồ sơ có đầy đủ giấy tờ theo quy định của Luật này. |
| `notified_authorities_within_3_days` | input | Đã thông báo cho cơ quan đăng ký kinh doanh và cơ quan thuế trong thời hạn 03 ngày. |
| `is_llc_member` | input | Là thành viên công ty trách nhiệm hữu hạn. |
| `must_include_signature_of_owner_or_representative` | derived | Điều lệ công ty phải bao gồm chữ ký của chủ sở hữu hoặc người đại diện. |
| `not_notified_authorities` | input | Doanh nghiệp chưa thông báo cho cơ quan đăng ký kinh doanh và cơ quan thuế. |
| `must_fulfill_other_legal_obligations` | derived | Doanh nghiệp đã thực hiện các nghĩa vụ khác theo quy định của pháp luật. |
| `is_member_of_board_or_chairman` | input | Người này là thành viên Hội đồng thành viên hoặc Chủ tịch công ty. |
| `must_provide_documents_for_change_of_representative` | derived | Doanh nghiệp phải cung cấp các văn bản quy định tại các khoản 2, 3 và 4 Điều 24 |
| `can_vote_on_company_matters` | derived | Người sở hữu có quyền biểu quyết về những vấn đề thuộc thẩm quyền quyết định của Hội đồng thành viên hoặc Đại hội đồng cổ đông. |
| `must_notify_enterprise_about_related_business` | derived | Người đại diện theo pháp luật của doanh nghiệp phải thông báo cho doanh nghiệp về doanh nghiệp mà mình có liên quan. |
| `must_keep_company_documents` | derived | Doanh nghiệp phải lưu giữ điều lệ công ty và các tài liệu liên quan. |
| `is_shareholder` | input | Người này là cổ đông của công ty cổ phần. |
| `can_revoke_business_registration_certificate` | derived | Cơ quan đăng ký kinh doanh có quyền thu hồi Giấy chứng nhận đăng ký hộ kinh doanh. |
| `is_local_registration_authority` | input | Cơ quan này là cơ quan đăng ký kinh doanh cấp xã. |
| `must_notify_if_application_invalid` | derived | Cơ quan đăng ký kinh doanh phải thông báo nếu hồ sơ không hợp lệ. |
| `must_complete_capital_contribution` | derived | Việc góp vốn được coi là thanh toán xong khi quyền sở hữu hợp pháp đã chuyển sang công ty. |
| `must_publicize_business_info` | input | Doanh nghiệp đã công khai thông tin về thành lập và hoạt động. |
| `valid_application_online` | derived | Hồ sơ đăng ký doanh nghiệp qua mạng thông tin điện tử là hợp lệ. |
| `is_provincial_registration_authority` | input | Cơ quan này là cơ quan đăng ký kinh doanh cấp tỉnh. |
| `must_notify_invalid_application` | derived | Cơ quan đăng ký kinh doanh phải thông báo nếu hồ sơ chưa hợp lệ. |
| `is_member_of_board` | input | Người này là thành viên của Hội đồng thành viên. |
| `is_registered_capital` | derived | Vốn điều lệ được xác định là tổng giá trị tài sản do các thành viên công ty đã góp. |
| `must_perform_duties_honestly` | derived | Người đại diện theo pháp luật của doanh nghiệp phải thực hiện nhiệm vụ một cách trung thực. |
| `must_notify_enterprise_timely_and_accurately` | derived | Người đại diện theo pháp luật của doanh nghiệp phải thông báo kịp thời và chính xác cho doanh nghiệp. |
| `must_not_use_enterprise_info_for_personal_gain` | derived | Người đại diện theo pháp luật của doanh nghiệp không được sử dụng thông tin của doanh nghiệp để tư lợi. |
| `must_not_transfer_property_ownership` | derived | Tài sản được sử dụng vào hoạt động kinh doanh của chủ doanh nghiệp tư nhân không phải làm thủ tục chuyển quyền sở hữu. |
| `is_single_member_llc` | input | Là chủ sở hữu công ty trách nhiệm hữu hạn một thành viên. |
| `must_notify_changes_other_contents` | derived | Doanh nghiệp phải thông báo khi có thay đổi nội dung khác trong hồ sơ đăng ký doanh nghiệp. |
| `must_notify_authorities_about_changes` | derived | Công ty phải thông báo cho cơ quan nhà nước về các thay đổi |
| `must_perform_duties_carefully` | derived | Người đại diện theo pháp luật của doanh nghiệp phải thực hiện nhiệm vụ một cách cẩn trọng. |
| `can_exercise_other_rights_and_duties` | derived | Hội đồng thành viên có quyền và nghĩa vụ khác theo quy định của Luật này. |
| `is_business_license_revoked` | input | Giấy chứng nhận đăng ký doanh nghiệp bị thu hồi. |
| `must_issue_receipt_and_schedule_result` | derived | Cơ quan đăng ký kinh doanh phải cấp giấy tiếp nhận và hẹn trả kết quả. |
| `must_report_honesty` | input | Doanh nghiệp đã chịu trách nhiệm về tính trung thực của thông tin kê khai. |
| `must_define_representative_roles_in_charter` | derived | Điều lệ công ty phải quy định rõ vai trò của các người đại diện theo pháp luật. |
| `must_notify_if_application_rejected` | derived | Cơ quan đăng ký kinh doanh phải thông báo nếu hồ sơ bị từ chối. |
| `must_get_approval_from_members` | derived | Giá trị tài sản góp vốn phải được trên 50% số thành viên chấp thuận. |
| `must_not_use_duplicate_or_confusing_name` | derived | Tên doanh nghiệp không được trùng hoặc gây nhầm lẫn với tên doanh nghiệp đã đăng ký. |
| `can_decide_management_structure` | derived | Hội đồng thành viên có quyền quyết định cơ cấu tổ chức quản lý. |
| `must_notify_tax_authority_about_branch_termination` | derived | Cơ quan đăng ký kinh doanh phải thông báo cho cơ quan thuế về việc chấm dứt hoạt động chi nhánh. |
| `must_register_business` | input | Doanh nghiệp đã thực hiện nghĩa vụ đăng ký doanh nghiệp. |
| `is_legal_representative` | input | Người này là người đại diện theo pháp luật của doanh nghiệp. |
| `has_highest_decision_body` | derived | Công ty có Hội đồng thành viên. |
| `can_be_member_of_board` | derived | Người này có thể là thành viên Hội đồng thành viên. |

### Thuế

| predicate | loại | nghĩa khi đúng |
|---|---|---|
| `is_authorized_to_share_taxpayer_info` | input | Đây là cơ quan, tổ chức, cá nhân được ủy quyền để chia sẻ thông tin người nộp thuế. |
| `is_non_compliance_with_tax_authority` | input | Đây là trường hợp không thực hiện yêu cầu của cơ quan quản lý thuế. |
| `must_provide_taxpayer_info` | derived | Cơ quan, tổ chức, cá nhân phải cung cấp thông tin người nộp thuế. |
| `is_enforcement_case` | input | Đây là trường hợp cưỡng chế thi hành quyết định hành chính về quản lý thuế. |
| `is_taxpayer_using_direct_tax_method` | input | Người nộp thuế đang khai, tính thuế giá trị gia tăng theo phương pháp trực tiếp. |
| `taxpayer_includes_legal_entities` | derived | Người nộp thuế bao gồm các tổ chức được thành lập và đăng ký kinh doanh theo Luật Doanh nghiệp, Luật Hợp tác xã và pháp luật chuyên ngành khác. |
| `is_tax_management_agency_or_official` | input | Đây là cơ quan quản lý thuế hoặc công chức quản lý thuế. |
| `goods_subject_to_vat` | derived | Hàng hóa, dịch vụ này thuộc đối tượng chịu thuế giá trị gia tăng. |
| `is_exporting_goods_or_services_abroad` | input | Người nộp thuế đang xuất khẩu hàng hóa, cung cấp dịch vụ ra nước ngoài. |
| `is_tax_deduction` | derived | Khoản chi được trừ khi xác định thu nhập chịu thuế |
| `must_use_price_excluding_vat` | derived | Cơ sở phải sử dụng giá bán chưa có thuế giá trị gia tăng. |
| `must_have_invoice_for_deduction` | derived | Cơ sở kinh doanh phải có hóa đơn để khấu trừ thuế giá trị gia tăng. |
| `taxpayer_has_obligation_to_pay_taxes` | input | Người nộp thuế có nghĩa vụ nộp thuế. |
| `is_taxpayer_authorized_to_use_invoice` | input | Người nộp thuế được cơ quan thuế chấp thuận sử dụng hóa đơn. |
| `must_follow_current_tax_law` | derived | Người nộp thuế phải xử lý theo quy định của Luật này. |
| `is_taxpayer_with_business_activity_in_different_location` | input | Người nộp thuế có hoạt động kinh doanh tại địa điểm khác. |
| `must_pay_tax_on_business_income` | derived | Người nộp thuế phải nộp thuế đối với các khoản thu từ kinh doanh. |
| `is_foreign_entity_with_income_in_vietnam` | input | Tổ chức, cá nhân nước ngoài có doanh thu phát sinh tại Việt Nam. |
| `is_selling_goods_or_services_in_domestic` | input | Người nộp thuế đang bán hàng hóa, cung cấp dịch vụ trong nội địa. |
| `taxpayer_must_file_tax_returns` | input | Người nộp thuế phải kê khai thuế. |
| `must_follow_tax_management_law_38_2019` | derived | Người nộp thuế phải tiếp tục xử lý theo quy định của Luật Quản lý thuế số 38/2019/QH14. |
| `must_use_e_invoice_for_exported_goods_or_services` | derived | Cơ sở phải sử dụng hóa đơn điện tử cho hàng hóa, dịch vụ xuất khẩu. |
| `must_deduct_input_vat` | derived | Cơ sở kinh doanh được khấu trừ thuế giá trị gia tăng đầu vào. |
| `tax_assessment` | input | Người nộp thuế đã bị ấn định thuế. |
| `is_legal_entity_or_non_legal_entity_taxpayer` | input | Người nộp thuế là doanh nghiệp hoặc tổ chức không có tư cách pháp nhân. |
| `must_use_non_cash_payment_receipt` | derived | Cơ sở kinh doanh phải sử dụng chứng từ thanh toán không dùng tiền mặt. |
| `must_have_service_contract_with_foreign_entity` | derived | Cơ sở kinh doanh phải có hợp đồng cung cấp dịch vụ với tổ chức, cá nhân ở nước ngoài. |
| `taxpayer_includes_foreign_entities` | derived | Người nộp thuế bao gồm tổ chức và cá nhân nước ngoài. |
| `is_tax_violation_case` | input | Đây là trường hợp vi phạm pháp luật về thuế. |
| `is_taxpayer_not_in_case_a_or_b` | input | Người nộp thuế không thuộc trường hợp a hoặc b. |
| `taxpayer_includes_other_income_contributors` | derived | Người nộp thuế bao gồm các tổ chức và cá nhân nộp các khoản thu khác. |
| `must_manage_tax_contents` | derived | Cơ quan thuế phải quản lý các nội dung thuế. |
| `is_foreign_individual` | input | Đây là người Việt Nam xuất cảnh để định cư ở nước ngoài hoặc người nước ngoài. |
| `must_send_suspend_invoice_decision_to_related_entities` | derived | Cơ quan thuế phải gửi quyết định ngừng sử dụng hóa đơn cho các tổ chức, cá nhân liên quan. |
| `must_use_invoice_from_tax_authority` | derived | Người bán hàng hóa, cung cấp dịch vụ phải sử dụng hóa đơn từ cơ quan thuế. |
| `must_deduct_input_vat_full` | derived | Cơ sở kinh doanh được khấu trừ toàn bộ thuế giá trị gia tăng đầu vào. |
| `tax_authority_must_fine_non_compliance` | derived | Cơ quan quản lý thuế phải xử phạt vi phạm đối với tổ chức tín dụng, ngân hàng nước ngoài không thực hiện trách nhiệm. |
| `is_electronic_invoice_with_tax_code` | input | Hóa đơn điện tử có mã của cơ quan thuế. |
| `invoice_type_is_electronic` | input | Hóa đơn là hóa đơn điện tử. |
| `must_enforce_tax_collection_measures` | derived | Cơ quan quản lý thuế phải thực hiện biện pháp cưỡng chế thu thuế. |
| `must_provide_decision_and_record_to_taxpayer` | derived | Cơ quan quản lý thuế phải cung cấp quyết định và biên bản cho người nộp thuế. |
| `taxpayer_must_pay_taxes_to_state_budget` | derived | Người nộp thuế phải nộp thuế vào ngân sách nhà nước. |
| `is_technology_incident` | input | Có sự cố kỹ thuật của Hệ thống thông tin quản lý thuế. |
| `must_terminate_suspend_invoice_decision` | derived | Quyết định ngừng sử dụng hóa đơn phải chấm dứt hiệu lực khi người nộp thuế đã nộp đủ số tiền thuế nợ. |
| `is_using_invalid_invoice_or_document` | input | Đây là việc sử dụng hóa đơn, chứng từ không hợp pháp. |

### Lao động

| predicate | loại | nghĩa khi đúng |
|---|---|---|
| `must_follow_labor_law` | derived | Người lao động phải thực hiện quy định của pháp luật về lao động. |
| `can_terminate_contract` | derived | Người lao động có quyền đơn phương chấm dứt hợp đồng lao động. |
| `not_can_terminate_contract` | derived | Người sử dụng lao động không được thực hiện quyền đơn phương chấm dứt hợp đồng lao động. |
| `must_provide_conditions_for_negotiation` | derived | Người sử dụng lao động có trách nhiệm bố trí thời gian, địa điểm và các điều kiện cần thiết để tổ chức các phiên họp thương lượng tập thể. |
| `can_request_negotiation` | derived | Người sử dụng lao động có quyền yêu cầu thương lượng. |
| `not_use_workers_without_agreement` | derived | Bên thuê lại lao động không được sử dụng lao động thuê lại nếu không có thỏa thuận cụ thể về trách nhiệm bồi thường. |
| `must_include_main_contents` | derived | Hợp đồng phải bao gồm các nội dung chủ yếu. |
| `worker_rights_protected` | input | Quyền và lợi ích hợp pháp của người lao động được bảo vệ. |
| `contract_in_written_form` | input | Hợp đồng lao động được giao kết bằng văn bản. |
| `not_use_workers_without_license` | derived | Bên thuê lại lao động không được sử dụng người lao động thuê lại được cung cấp bởi doanh nghiệp không có Giấy phép hoạt động cho thuê lại lao động. |
| `age_at_least_15` | input | Người lao động đủ 15 tuổi. |
| `employer_rights_protected` | input | Quyền và lợi ích hợp pháp của người sử dụng lao động được bảo vệ. |
| `must_notify_authorities` | derived | Người sử dụng lao động phải thông báo cho cơ quan có thẩm quyền. |
| `must_pay_wages_and_benefits` | derived | Người sử dụng lao động phải trả tiền lương và đóng bảo hiểm xã hội cho người lao động. |
| `worker_continue_working` | input | Người lao động vẫn tiếp tục làm việc. |
| `must_consult_workers_representative` | derived | Phải trao đổi ý kiến với tổ chức đại diện người lao động. |
| `not_paid_salary` | derived | Người lao động không được trả đủ lương. |
| `not_conflict_with_law` | input | Nội dung thỏa ước không trái với quy định của pháp luật. |
| `contract_invalid_full` | input | Hợp đồng lao động bị tuyên bố vô hiệu toàn bộ. |
| `leasing_company_has_license` | input | Doanh nghiệp cho thuê lại có Giấy phép hoạt động. |
| `must_notify_workers` | derived | Người sử dụng lao động phải thông báo cho người lao động. |
| `not_reached_retirement_age` | input | Người lao động chưa đủ tuổi nghỉ hưu. |
| `can_lead_strike` | derived | Tổ chức đại diện người lao động tại cơ sở có quyền tổ chức và lãnh đạo đình công. |
| `must_provide_business_info` | derived | Bên người sử dụng lao động có trách nhiệm cung cấp thông tin về tình hình hoạt động sản xuất, kinh doanh. |
| `entitled_annual_leave` | derived | Người lao động có quyền nghỉ hằng năm có hưởng lương. |
| `must_notify_worker` | derived | Người sử dụng lao động phải thông báo cho người lao động. |
| `dialogue_between_workers_and_employers` | input | Có đối thoại giữa người lao động và người sử dụng lao động. |
| `employer_involvement` | input | Người sử dụng lao động tham gia giải quyết việc làm. |
| `worker_is_pregnant` | input | Người lao động nữ đang mang thai. |
| `not_use_workers_during_strike` | derived | Bên thuê lại lao động không được sử dụng lao động thuê lại để thay thế người lao động đang trong thời gian thực hiện quyền đình công. |
| `can_use_workers_for_special_jobs` | derived | Người sử dụng lao động có thể sử dụng người lao động làm thêm giờ trong các trường hợp đặc biệt. |
| `within_30_days` | input | Người sử dụng lao động khai trình trong thời hạn 30 ngày. |
| `must_provide_work_documents` | derived | Người sử dụng lao động phải cung cấp bản sao các tài liệu liên quan đến quá trình làm việc. |
| `contract_invalid_partial` | input | Hợp đồng lao động bị tuyên bố vô hiệu từng phần. |
| `must_pay_compensation_for_damage` | derived | Người sử dụng lao động phải bồi thường thiệt hại do làm hư hỏng dụng cụ, thiết bị, tài sản. |
| `must_pay_full_salary` | derived | Người lao động được trả đủ tiền lương cho thời gian bị tạm đình chỉ công việc. |
| `provincial_committee_submits_to_people_council` | input | Ủy ban nhân dân cấp tỉnh đã trình Hội đồng nhân dân cùng cấp. |
| `can_suspend_strike` | derived | Chủ tịch Ủy ban nhân dân cấp tỉnh có quyền quyết định hoãn hoặc ngừng đình công. |
| `must_notify_department_about_overtime` | derived | Người sử dụng lao động phải thông báo cho Sở Lao động - Thương binh và Xã hội về việc làm thêm. |
| `not_discriminated` | derived | Người lao động không bị phân biệt đối xử. |
| `must_follow_management` | derived | Người lao động phải tuân theo sự quản lý của người sử dụng lao động. |
| `valid_contract` | derived | Hợp đồng lao động là hợp lệ. |
| `must_pay_additional_compensation` | derived | Người sử dụng lao động phải trả thêm khoản tiền bồi thường cho người lao động. |
| `not_lower_worker_rights` | derived | Quyền lợi của người lao động không được thấp hơn hợp đồng lao động. |
| `must_provide_workers_with_required_skills` | derived | Doanh nghiệp phải bảo đảm đưa người lao động có trình độ phù hợp với yêu cầu. |
