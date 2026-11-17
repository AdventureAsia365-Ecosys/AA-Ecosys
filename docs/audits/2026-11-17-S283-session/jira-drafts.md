# S283 — nháp Jira (17/11/2026)

Số liệu đo trên Dev ngày 17/11 (giờ ghi ở từng câu). Chờ tech lead duyệt trước khi đăng. Mỗi comment mở đầu bằng mention
chị Thư (html mention node khi đăng).

## 1. PR-25 Booking — hoá đơn phần mềm hằng tháng có dòng giảm giá

Vì sao: tính năng ship hôm nay, đã thử thật.

> @thule Hoá đơn phần mềm hằng tháng cho đại lý giờ ghi đúng phần giảm giá trong báo giá.
>
> - Mỗi gói được giảm (ưu đãi gộp gói, ưu đãi đại lý đầu tiên) có một dòng giảm giá riêng, ngay dưới dòng gói đó. Trước đây chỉ có một dòng 0 đồng nhắc "xem báo giá".
> - Thử ngày 17/11 với một đại lý giả lập có đủ 3 gói (Content, CRM 3 chỗ, TripPlanner), giảm gộp gói 10 %:
>
> | Gói | Giá | Giảm |
> |---|---|---|
> | Content | 349 USD | −34,90 |
> | CRM (3 chỗ) | 57 USD | −5,70 |
> | TripPlanner | 49 USD | −4,90 |
> | **Tổng** | | **409,50 USD**, khớp báo giá trên hồ sơ đại lý |
>
> - Mức giảm vẫn chỉnh trên trang Plans; hoá đơn tự theo.

| Câu | Bằng chứng |
|---|---|
| 409,50 USD, 3 dòng giảm | nháp SaaS chạy 17/11 04:23Z, job succeeded, discounted 3 (S283 log) |

## 2. PR-26 CRM — tạo đại lý mới là có ngay CRM, mời chủ đại lý tự động

Vì sao: tính năng ship hôm nay, tech lead tự thử trên giao diện.

> @thule Tạo đại lý mới có gói CRM giờ không còn bước tay:
>
> - Ở Platform › Tenants › New tenant, chọn gói CRM và nhập e-mail chủ đại lý. Hệ thống tạo đại lý, bật Content studio, tạo luôn tài khoản CRM của đại lý và gửi lời mời cho chủ đại lý trong cùng một lần bấm. Hộp kết quả liệt kê từng bước đã làm.
> - Thử ngày 17/11 với một đại lý giả lập: hộp báo "CRM agency is ready and the owner is invited", hồ sơ có gói Content và CRM Core đang hoạt động.
> - CRM khoá đúng theo gói: nút xuất CSV ở Reports và kết nối Stripe chỉ mở khi gói của đại lý có tính năng đó; gói chưa có thì nút hiện khoá kèm lời nhắc nâng gói.

| Câu | Bằng chứng |
|---|---|
| Tạo đại lý + CRM + mời | tech lead tạo tenant thử 17/11 ~04:40Z; DB: content.starter + crm.core active |
| Khoá theo gói | Partner #334 live 17/11; test từng cổng |

## 3. PR-24 TripPlanner — trang của đại lý chỉ mang thương hiệu đại lý

Vì sao: tính năng ship hôm nay, kiểm live bằng trình duyệt và curl.

> @thule Trang TripPlanner của đại lý giờ chỉ mang thương hiệu đại lý:
>
> - Tiêu đề trang, mô tả khi chia sẻ link, ngôn ngữ trang theo đại lý; không còn chữ "Adventure Asia" trên trang lên lịch, trang chia sẻ, điều khoản và quyền riêng tư của đại lý (kiểm 17/11 trên đại lý thử: 0 chỗ). Trang của AA vẫn giữ thương hiệu AA.
> - Mỗi đại lý có trang Điều khoản và Quyền riêng tư (bản nháp) riêng; form gửi yêu cầu dẫn tới các trang này.
> - Bỏ hẳn phần đăng nhập và "chuyến của tôi" dành cho khách lẻ (mô hình chỉ bán qua đại lý).
> - Trang Add-ons của đại lý có nút/đường link mở trang lên lịch của chính đại lý để gắn vào website.

| Câu | Bằng chứng |
|---|---|
| 0 chữ AA trên trang đại lý | curl 17/11 sau deploy 58eace37: plan/privacy/terms = 0 |
| Bỏ đăng nhập khách lẻ | /sign-in, /trips, /api/me trả 404 (17/11) |

## 4. PR-22 CIS — báo cáo đối tác và che thông tin cá nhân trước khi gửi AI

Vì sao: hai tính năng ship hôm nay có ý nghĩa với chủ doanh nghiệp (báo cáo, bảo vệ dữ liệu).

> @thule Hai cập nhật trên CIS:
>
> - **Báo cáo:** ba báo cáo về đối tác (tăng trưởng và rời bỏ, phễu tiếp nhận đại lý, sử dụng trợ lý AI trong CRM) đã chạy thật từ nút "Generate now" ngày 17/11. Trang Reports giờ có mục tình trạng của toàn bộ 65 báo cáo trong danh mục (đang tự chạy, một phần, dự kiến, đã bỏ) và khi nào báo cáo dự kiến sẽ được làm.
> - **Bảo vệ dữ liệu:** trước khi gửi nội dung của đại lý cho AI viết bài, hệ thống tự che e-mail, số điện thoại, số thẻ, số giấy tờ và mã OTP. Nếu bước che lỗi thì không gửi gì đi. Áp dụng cho các bước viết bài, viết lại tour và gợi ý góc bài của đại lý.

| Câu | Bằng chứng |
|---|---|
| 3 báo cáo chạy thật | report_run EX-03/EX-07/CRM-04 succeeded 04:37–04:38Z 17/11 |
| 65 báo cáo trong danh mục | EX-06 run 01:20Z: exists 2, partial 47, planned 9, missing 6, retired 1 |
| Che PII | CIS #1559 live 17/11 (a627afd1), 44 test |

## Kết quả đăng

_(điền sau khi tech lead duyệt)_
