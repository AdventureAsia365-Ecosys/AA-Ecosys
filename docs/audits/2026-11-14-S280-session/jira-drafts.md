# S280 — Jira drafts (chờ tech lead duyệt)

Trạng thái: **đã đăng** 14/11 ~20:45 +07 sau khi tech lead duyệt ("Đăng"): PR-25 comment 10653 (3 ảnh), PR-26 10654, PR-22 10655, PR-27 10656 (mỗi cái 1 ảnh).
ảnh nhúng từ `docs/audits/2026-11-14-S280-session/verify/`.

## PR-25 (Booking)

@Thư — Cập nhật Booking ngày 14/11:

**Định giá tour cho bộ phận chăm sóc khách hàng đã chạy trọn vẹn trên Dev** (dữ liệu giả lập, đã dọn lại sau khi kiểm):

| Bước | Kết quả |
|---|---|
| Nhân viên CSKH (quyền "Pricing team") nhận gợi ý dịch vụ từ lịch trình CIS cho tour | 4/4 tour nhận đủ |
| Nhập giá bằng file Excel: chạy thử (DRY RUN) rồi nhập thật | 4 tour được định giá, bán được |
| Người tạo không tự duyệt được giá của mình; người thứ hai duyệt | Đúng, hệ thống chặn người tạo |
| Bảng giá đại lý (tariff) và giá "Từ $X" trên TripPlanner / Content studio | Hiện đúng 1.250 / 1.500 / 1.750 / 2.000 USD |

Trang **Pricing › Policy** giờ có một ô tìm chung cho mọi nhóm tham số (tìm cả theo mã tham số).

Ảnh: bảng tariff đại lý, giá "Từ" trên TripPlanner, màn duyệt giá.

## PR-26 (CRM cho đại lý)

@Thư — Cập nhật CRM ngày 14/11:

- **Đặt tour trực tiếp (Book now)** từ trang tour của đại lý đã chạy trọn trên Dev: khách chọn ngày còn chỗ, xem giá, để
  lại tên và email, hệ thống tạo booking và mở đề xuất cho khách chấp nhận và thanh toán. Video diễn tập: PASS.
- **Ngân sách AI của đại lý:** khi đại lý đặt ngân sách 0, CRM từ chối soạn nháp AI và báo nhân viên trả lời tay (đã thử
  thật). Video diễn tập bật/tắt ngân sách: PASS.
- **Cài đặt của đại lý:** trang cài đặt hiện giá trị riêng của từng đại lý và các thay đổi đang chờ; không cho đặt ngày
  hiệu lực trong quá khứ; báo rõ lý do khi một giá trị bị từ chối.

## PR-22 (CIS — nội dung)

@Thư — Cập nhật CIS ngày 14/11:

- **Trang Cài đặt (Platform › Settings):** quản trị viên đổi được một giá trị **cho riêng một đại lý** (ví dụ chỉ bật
  cho một đại lý thử nghiệm), ô tìm tìm được trong mọi nhóm, lịch các thay đổi đã hẹn giờ được hiện rõ. Đã thử đổi một
  giá trị trên CIS và TripPlanner: hai app nhận giá trị mới trong khoảng 1 phút, không cần deploy, rồi đặt lại như cũ.
- **Bản đồ sản phẩm (Platform › Product map):** một trang liệt kê 117 tính năng của 5 app và 37 liên kết giữa các app,
  mỗi liên kết ghi điều kiện để chạy được. Ảnh desktop và mobile.

## PR-27 (Nền tảng)

@Thư — Cập nhật nền tảng ngày 14/11:

- **Xoá dữ liệu khi đại lý ngừng hợp tác** đã chạy thật lần đầu trên Dev với một đại lý giả lập: sau khi ngừng hợp tác và
  được duyệt, dữ liệu của đại lý đó được xoá ở CIS, Booking và TripPlanner; kiểm lại độc lập ở cả ba nơi đều không còn dữ
  liệu cá nhân. Có bản sao lưu trước khi xoá.
- **Giới hạn hạ tầng (Platform › Infra limits):** trang chỉ đọc cho quản trị viên, giải thích từng giới hạn (tường lửa,
  ngân sách AWS, cảnh báo) và chỗ thay đổi.
