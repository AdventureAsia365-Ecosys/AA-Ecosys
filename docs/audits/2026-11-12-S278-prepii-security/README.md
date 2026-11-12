# Rà bảo mật trước dữ liệu cá nhân thật (AA-1092, S278)

*12/11/2026, viết cho tech lead. Nguồn: mục M19 và M24 của bản audit hệ thống S278. Lane l15 của phiên S278, đọc code
trên `origin/main` của 4 repo, chạy test local (PostgreSQL 16, không gọi AWS ngoài một `terraform plan` chỉ đọc).*

Repo app và repo gốc đang public: bản này chỉ ghi việc đã làm và kiểm soát đang có. Rủi ro còn lại ghi trong Linear
AA-1092, không ghi ở đây.

## 1. Bốn hạng mục

| # | Hạng mục | Đã làm | Ghi chú chi tiết |
|---|---|---|---|
| 1 | TripPlanner: khoá ký tenant assertion (M19) | Khoá riêng `tripplanner/<env>/tenant-assertion-key` (JSON `current`, `previous`, `previous_until`, `edge_derived_until`); xoay khoá có thời gian ân hạn tối đa 7 ngày; Lambda từ chối chữ ký giả, khoá cũ hết hạn, assertion hết hạn (401) và secret hỏng (503); tool điền và xoay khoá ở Infra; Terraform chỉ tạo vỏ secret, quyền đọc cho Lambda và ánh xạ vào task web. Thứ tự rollout: Lambda trước (PR backend), rồi Terraform, điền khoá, chờ 10 phút (cache secret của Lambda), rồi mới PR web; Lambda đọc lại secret một lần khi chữ ký không khớp (tối đa 1 lần/30 giây) | AA-TripPlanner-Web `docs/implementation-notes/AA-1092.md`; AA-CIS-Infra `docs/implementation-notes/AA-1092-tp-key.md` |
| 2 | CRM: các route công khai mới sau đợt rà AA-969 (M24) | Rà 16 điểm (Book now, VNPay IPN, cổng stub, trang cộng tác viên, mã đăng nhập, route traveller mới, nút trả tiền online). Sửa 3: IPN không chữ ký bị từ chối trước khi tra DB; IPN chữ ký sai bị giới hạn theo cặp (địa chỉ gửi, mã giao dịch): không theo địa chỉ riêng (VNPay dùng chung địa chỉ), không theo mã giao dịch riêng (người biết mã có thể chặn IPN thật của VNPay); Book now có trần theo giờ cho mỗi đại lý. Không còn phát hiện mức cao | AA-Partner `docs/implementation-notes/AA-1092.md` (bảng R1–R16) |
| 3 | Booking: RLS cho `booking.b2b_partners` | Migration bk-049 (contract): ENABLE + FORCE RLS, 2 policy đọc `app.tenant_id`. Back office (staff, job, tra partner của B2B API) không bind tenant nên thấy như cũ; giao dịch có bind tenant chỉ đọc đúng dòng của mình, không ghi được | AA-Booking `docs/implementation-notes/AA-1092.md` |
| 4 | Infra: WAF trên các host công khai | Bảng host ↔ kiểm soát biên đọc từ Terraform; bật web ACL dùng chung trên stage REST của CIS và Booking (miễn rate cho NAT của mình, miễn geo cho host API); thêm pool M2M vào web ACL Cognito. Không thêm ACL hay rule mới | AA-CIS-Infra `docs/implementation-notes/AA-1092-waf.md` |

## 2. Chi phí (ước tính, giá niêm yết us-west-1)

- Secret mới: 0,40 USD/tháng.
- WAF: 0 USD cố định (không ACL, không rule mới; IP set miễn phí); 0,60 USD mỗi triệu request được kiểm tra trên 2
  stage và pool M2M. Dev dưới 1 triệu request/tháng: dưới 0,60 USD/tháng.

## 3. Kiểm live cần làm sau khi merge (phiên điều phối)

1. TripPlanner: sau khi điền khoá và deploy web, gửi assertion ký bằng khoá giả / khoá cũ (edge-derived sau
   `edge_derived_until`) / đã hết hạn → 401; log Lambda hết dòng `tenant_assertion_key_used` sau deploy web.
2. CRM: IPN không chữ ký → `{"RspCode": "97"}`, không có dòng audit; IPN chữ ký sai → `97`, sau 10 lần cùng mã từ cùng một địa chỉ → 429 (địa chỉ khác vẫn qua).
3. Booking: sau Migration Apply, `relrowsecurity` và `relforcerowsecurity` của `booking.b2b_partners` đều true; DB
   Schema Dump không còn vi phạm rule a của bảng này.
4. WAF: `get-web-acl-for-resource` trả web ACL cho stage CIS, stage Booking và pool M2M; sampled requests của
   api-cis hiện địa chỉ viewer; metric `RateLimit1000` của địa chỉ NAT bằng 0.
