# S278 — nháp Jira (chờ tech lead duyệt)

Quy tắc: chỉ báo tính năng đã ship và kiểm live; không câu hỏi cho chị Thư; không nhắc go-live (D14); không mã issue nội
bộ; mention @thule bằng mention node khi đăng. PR-27 (hạ tầng) không đăng: quyết định kỹ thuật thuộc tech lead.

## PR-25 — Booking

@thule Cập nhật Booking (12/11):

1. Trang Thiết lập giá cho team chăm sóc khách: một bảng liệt kê mọi tour cùng tình trạng sẵn sàng bán (thành phần,
   giá nhà cung cấp, luật giá, mở bán, lịch khởi hành), lọc theo nước và theo việc còn thiếu, mỗi dòng ghi bước tiếp theo.
   Có gợi ý thành phần lấy từ lịch trình CIS (khách sạn, dịch vụ theo ngày) để nhân viên chấp nhận hoặc sửa, và nhập
   hàng loạt bằng Excel có chạy thử trước khi ghi.
2. Trang Chính sách giá (Pricing › Policy): 13 thông số chính sách đã duyệt (biên lợi nhuận, thang phí huỷ, thời hạn
   báo giá, …) nằm trong hệ thống và sửa được trên trang, có người duyệt thứ hai và lịch sử thay đổi, không ghi cứng
   trong code.
3. Xác nhận và voucher của booking B2B ghi đúng ngày kết thúc theo số ngày tour, và hồ sơ booking hiện tên tour thay
   cho mã nội bộ.

## PR-26 — CRM cho đại lý

@thule Cập nhật CRM đại lý (12/11):

1. Điều hành chuyến đi: danh sách khởi hành và danh sách khách theo từng chuyến, voucher cho khách (cả trên cổng của
   khách), file PDF xác nhận và voucher tạo trên máy chủ, danh sách phòng có kiểm sức chứa, kiểm hạn hộ chiếu, theo dõi
   visa theo mẫu từng nước.
2. Danh sách "đã bao gồm / không bao gồm" cho đề xuất tour, đại lý tự quản lý thư viện của mình.
3. Khi AA huỷ một chuyến khởi hành, CRM của đại lý mở một hồ sơ hướng dẫn xử lý cho từng chuyến bị ảnh hưởng.
4. Nhãn cho chuyến đi và khách hàng: đại lý tự tạo nhãn, gắn hàng loạt có xem trước số lượng, nhãn hệ thống do app tự
   gắn (loại tour, chủ đề), danh sách khách "sẵn sàng đi lại".
5. Đặt tour online (Book now): giới hạn số lần tra giá mỗi phút theo đại lý, chủ đại lý chỉnh được trong Cài đặt ›
   Thanh toán.

Đã kiểm trên tài khoản đại lý thử nghiệm: điều hành chuyến 10/11 hạng mục đạt (hạng mục còn lại đã sửa và kiểm lại
đạt), nhãn 8/8 đạt.

## PR-23 — Cổng tenant (Content studio)

@thule Cập nhật Content studio (12/11):

1. Trang Bài viết cho biết lý do khi một tour chưa có chủ đề blog (ví dụ chưa đủ thông tin, ít người tìm), bằng lời
   thường. Trên 4 tenant thử nghiệm: 44/49 tour có chủ đề, 5 tour còn lại đều có lý do.
2. Bảng nội dung chỉ cho đại lý thấy nội dung của mình và ghi chú AI, không còn lộ ghi chú nội bộ.
3. Bài bị giữ lại để kiểm tra không đăng được nếu chủ tài khoản không chủ động xác nhận; đại lý thấy rõ lý do.
4. Trang Điều khoản và Quyền riêng tư mô tả đúng cách đăng nhập hiện tại.

## PR-24 — TripPlanner

@thule Cập nhật TripPlanner (12/11):

1. Trang tour của AA không còn hiện thương hiệu đại lý hay nút Đăng nhập, kể cả khi khách đi từ trang lên lịch của đại
   lý sang (đã kiểm trên máy tính và điện thoại, nền sáng và tối).
2. Nút Đặt ngay trên trang tour luôn đặt đúng tour của trang đó.

## Đã đăng (12/11 ~18:30 +07, tech lead duyệt "duyệt đăng, kèm ảnh")

| Issue | Comment | Ảnh | Sửa so với nháp (theo luật chỉ báo phần đã kiểm live) |
|---|---|---|---|
| PR-25 | 10645 | 4 | "13 thông số" → "20 thông số" (số thật trên trang); gợi ý thành phần + nhập Excel ghi "đã có, chưa thử thật"; "hồ sơ booking mới" |
| PR-26 | 10646 | 5 | hồ sơ AA huỷ chuyến + trần tra giá Book now ghi "đã có, chưa thử trọn vòng" |
| PR-23 | 10647 | 3 | bỏ "đại lý thấy rõ lý do" (mới kiểm qua API) |
| PR-24 | 10648 | 3 | không đổi |

Ảnh chụp live trong phiên (`.tmp-session/S278/verify/`, không commit: repo public).
