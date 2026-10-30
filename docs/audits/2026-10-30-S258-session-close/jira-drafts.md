# S258 — nháp Jira (CHƯA đăng: gom sang phiên sau cùng ngày, S259)

Tech lead 30/10: lưu nháp, gom với phiên sau cùng ngày; bỏ PR-27 (việc kỹ thuật, tech lead tự quyết).

Mỗi comment mở bằng mention @thule (mention node khi đăng). Không mã Linear. Đứng tên Nghiệp.

## PR-22 (CIS — Nội dung & pipeline)

@thule Cập nhật ảnh bìa tour trên Marketplace đại lý (29–30/10):
- Ghép ảnh với điểm đến tốt hơn: thêm 326 ảnh được gắn đúng điểm đến (tổng 1.919 ảnh), 336 điểm đến có ảnh bìa.
- Tour trong kho cho đại lý có ảnh bìa: **302 → 444 / 892 tour**.
- 448 tour còn thiếu chủ yếu thuộc India (215), Japan (79), Laos (45), Philippines (44), Thailand (43): các nước này chưa có thư mục ảnh nguồn, cần bổ sung ảnh chứ không phải sửa code.
- Phần AI viết nội dung vẫn tạm dừng do AWS chặn Bedrock trên tài khoản AI; hệ thống đã báo trạng thái này trên trang quản trị và dừng các việc AI ngay thay vì thử lại.

## PR-24 (TripPlanner)

@thule Trang điểm đến tải nhanh hơn trên điện thoại (đo thật trên bản production, 5 lần):
| Trang | Trước | Sau |
|---|---|---|
| /destinations/bhutan | 3,95 s | 2,49 s |
| /destinations | 2,46 s | 1,38 s |
Cách làm: ảnh nằm dưới màn hình đầu chỉ tải khi khách cuộn tới; ảnh đầu trang dùng đúng kích cỡ.

## PR-26 (CRM cho đại lý)

@thule Kiểm thử đầy đủ trên môi trường Dev (30/10) với đại lý thử:
- Một chuyến đi chạy trọn từ Yêu cầu → Báo giá → Đặt cọc → Đã đặt → Đang đi → **Hoàn tất**, có dịch vụ của nhà cung cấp riêng của đại lý.
- Tài khoản trợ lý của đại lý đọc 7 trang có tiền: **không thấy lãi / giá net / hoa hồng**; chủ đại lý vẫn thấy đủ.
- Sản phẩm Adventure Asia trong đề xuất: báo giá, giữ chỗ và khách chấp nhận chạy đúng; giữ chỗ hết hạn thì hệ thống từ chối và mời báo giá lại.
- Tài khoản quản trị nội bộ không vào được cổng của đại lý.
Còn lại: bước xác nhận đặt chỗ với Booking sau khi khách đặt cọc cho sản phẩm Adventure Asia.
