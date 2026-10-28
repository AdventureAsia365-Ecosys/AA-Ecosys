# Nháp Jira S254 + S255 (28/10/2026) — đã duyệt và đăng 28/10

Gom nháp của S254 (tech lead chốt 10:40: gộp sang phiên sau cùng ngày) và S255. Một comment cho mỗi epic, đứng tên tech
lead, tag @thule bằng mention node khi đăng. Số liệu lấy trong ngày 28/10/2026 (giờ ghi trong log phiên S255).

---

## PR-22 — CIS nội dung & pipeline

@thule Cập nhật CIS ngày 28/10:

- **Địa điểm trên bản đồ chính xác hơn.** Toạ độ địa điểm giờ chỉ lấy từ dịch vụ bản đồ (geocoder), không dùng toạ độ do AI
  đoán nữa. Có thêm bước kiểm điểm nằm lệch xa lộ trình tour, và bộ lọc loại các tên không phải địa điểm (bữa ăn, khách sạn
  chung chung, chặng di chuyển) trước khi tra bản đồ. Đợt sửa lại 3.842 điểm cũ đang chạy tự động trong khoảng 3 ngày,
  không tốn phí (gói miễn phí của dịch vụ bản đồ).
- **Tour có chặng di chuyển dài nay có lộ trình.** Ví dụ tour Seoul–Busan từ 1 ngày có điểm lên 11/14 ngày; 53 tour được
  dựng lại lộ trình.
- **Trang Cost Operations trong admin** (đổi tên từ External Spend): tổng chi theo nhà cung cấp và tài khoản, dự báo tới cuối
  tháng, tab hoá đơn AWS, tab Jev, và chi phí DataForSEO theo từng lần chạy.
- **Trang Docs trong admin**: đọc toàn bộ 98 tài liệu của hệ thống ngay trong admin; trang chỉ dành cho chủ doanh nghiệp chỉ
  hiện khi đăng nhập đúng quyền. Tài liệu cập nhật vài phút sau mỗi lần sửa.
- **Writing memory**: bộ kiểm tra trước khi phát hành quy tắc viết mới đã chạy thử trên dữ liệu thật; cách chấm đã được sửa
  cho khớp với nhãn chấm tay hơn (chưa đủ chuẩn để bật, đang tiếp tục).
- **Giọng thương hiệu (vòng thử 8)**: thử đổi cách chọn góc viết; chấm mù cho thấy chưa tốt hơn bản hiện tại nên giữ bản cũ.

## PR-23 — Portal tenant

@thule Cập nhật Portal ngày 28/10:

- **Marketplace mới**: lưới tour có bộ lọc và ngăn xem chi tiết. Bộ lọc theo loại hoạt động và độ khó, cùng ảnh bìa mỗi tour,
  sẽ có ở bản kế tiếp.
- Giao diện Portal và CRM dùng chung bộ thành phần thiết kế với admin, có kiểm tra tự động để không lệch nhau.

## PR-24 — TripPlanner

@thule Cập nhật TripPlanner ngày 27–28/10:

- Toàn bộ trang khách hàng theo thiết kế Golden Hour mới (font Poppins, tuỳ chọn giảm chuyển động, mở/đóng tất cả các ngày),
  sửa tràn trang trên điện thoại.
- Ảnh trùng lặp giữa các điểm đến đã được gộp.
- Còn lại: tốc độ tải ảnh đầu trang trên điện thoại (khoảng 4,8 giây, mục tiêu 2,5 giây) — cần thêm cỡ ảnh trung bình, làm ở
  bản kế tiếp.

## PR-25 — Booking

@thule Cập nhật Booking ngày 27–28/10:

- **Phủ đủ các màn hình theo Figma**: Countries (có ảnh), nhà cung cấp + bảng giá, hồ sơ chuyến, báo giá, kiểm tra chuyến,
  hoá đơn nhà cung cấp và chi trả, mục "My Payments" cho khách, xuất CSV ở 9 danh sách, bố cục gọn cho laptop.
- Lỗi danh sách trip plan không mở được (27/10) đã sửa trong ngày; có kiểm tra tự động chặn lỗi đọc dữ liệu chậm này tái diễn.

## PR-26 — CRM cho đại lý

@thule Cập nhật CRM ngày 28/10:

- Gửi email cho khách an toàn khi hệ thống cập nhật: mỗi email được ghi nhận trước khi gửi, nên lúc cập nhật phần mềm giữa
  chừng sẽ không gửi trùng hai lần cho khách.

## PR-27 — Nền tảng (đăng nhập, bảo mật, hạ tầng)

@thule Cập nhật nền tảng ngày 28/10:

- **Bảo mật tài khoản AWS**: chặn mọi kho lưu trữ bị mở công khai, bật công cụ phát hiện tài nguyên chia sẻ ra ngoài, gửi
  email cảnh báo khi có thay đổi quyền truy cập, tường lửa, đăng nhập tài khoản gốc hay tắt nhật ký. Nhật ký hoạt động
  (CloudTrail) giờ ghi mọi vùng, được mã hoá và khoá chống sửa/xoá 365 ngày. Chi phí khoảng 1 USD/tháng.
- **Cảnh báo chi phí**: ngân sách tháng chung nâng lên 300 USD kèm cảnh báo dự báo; tài khoản chạy AI có cảnh báo tức thì khi
  chi phí tăng bất thường từ 15 USD.
- **Gỡ tài khoản AWS cá nhân khỏi hệ thống**: toàn bộ dịch vụ giờ chỉ chạy trên tài khoản hạ tầng và tài khoản AI của công ty;
  mọi tài nguyên cũ trên tài khoản cá nhân đã xoá.
- Bảng dữ liệu cũ không còn dùng đã được dọn khỏi cơ sở dữ liệu (có bản sao lưu giữ 180 ngày).
- Các bản phát hành mới: CIS 0.13.0, Booking 0.9.0, CRM 0.7.0, TripPlanner 0.10.0.

---

## Kết quả đăng

Tech lead duyệt 28/10 ~20:50; đăng nguyên văn, tag @thule bằng mention node:

| Epic | Comment id | Link |
|---|---|---|
| PR-22 | 10515 | https://adventure-asia.atlassian.net/browse/PR-22?focusedCommentId=10515 |
| PR-23 | 10516 | https://adventure-asia.atlassian.net/browse/PR-23?focusedCommentId=10516 |
| PR-24 | 10517 | https://adventure-asia.atlassian.net/browse/PR-24?focusedCommentId=10517 |
| PR-25 | 10518 | https://adventure-asia.atlassian.net/browse/PR-25?focusedCommentId=10518 |
| PR-26 | 10519 | https://adventure-asia.atlassian.net/browse/PR-26?focusedCommentId=10519 |
| PR-27 | 10520 | https://adventure-asia.atlassian.net/browse/PR-27?focusedCommentId=10520 |
