# S291 — nháp Jira (chờ tech lead duyệt, CHƯA đăng)

Mỗi nháp đăng dưới tên tech lead, mention @thule bằng mention node khi đăng. Ảnh nhúng từ `live/`.

## J1 — PR-25 (Booking)

@thule Cập nhật Booking đêm 24–25/11:

- Tab **Suppliers** của trip case: các booking nhà cung cấp sinh ra từ tour đã bán giờ ghi rõ "from the tour, day N" thay vì "extra item". Kiểm trên Dev với trip case thử TC-000040: 10/10 dòng đúng nhãn (ảnh).
- Thông báo nội bộ của nhân viên không còn kèm dữ liệu kỹ thuật về e-mail; nhắc hợp đồng sắp hết hạn được ghi theo từng lần gửi, nên nếu gửi dở giữa chừng thì lần sau chỉ gửi phần còn thiếu, không gửi lại cả loạt.
- Lịch mùa giá: các tour chưa có điểm đến không bị đọc lại mỗi lượt nữa; trang Seasons có thêm số "deferred". Khoảng kiểm lại (7 ngày) sửa được ở Pricing › Policy.

Ảnh: `s291-booking-suppliers-tab-from-tour.png`

## J2 — PR-30 (Khách sạn)

@thule Khách sạn qua nhiều DMC — ba chỉnh sửa sau đợt 24/11:

- Khi nhập lại bảng giá Excel, màn so sánh có thêm phần **Inventory**: allotment bị thu hẹp sẽ được báo rõ.
- Hợp đồng gốc để so sánh được chọn cố định, đúng hợp đồng mà file nhập nhắm tới, kể cả khi cùng DMC có hai hợp đồng cùng ngày bắt đầu.
- Sửa cách đếm phòng allotment: một dòng báo giá on request không còn giữ chỗ phòng của các dòng sau.

Ba điểm này đã kiểm bằng test tự động; chưa chạy lại một lượt nhập Excel thật trên Dev.

## J3 — PR-29 (Optional activity add-on)

@thule Add-on của AA trong báo giá CRM của đại lý: ngăn "AA add-on" giờ chỉ gợi ý những dịch vụ bán tại điểm đến của đúng ngày tour đó, giống thẻ ngày trên TripPlanner. Nếu cố thêm một add-on ở nơi khác, hệ thống từ chối và báo lý do. Đã lên Dev 25/11; kiểm bằng test tự động, chưa thử tay trên một báo giá thật.

## J4 — PR-24 (TripPlanner)

@thule TripPlanner: sửa một lỗi có thể làm trang lên lịch trình không mở được khi dữ liệu add-on theo ngày trả về sai dạng. Giờ trang vẫn chạy bình thường, chỉ không hiện add-on đó. Bộ kiểm tra giao diện sau mỗi lần phát hành đã xanh lại trên Dev (25/11).

## J5 — PR-27 (Nền tảng)

@thule Trang **Ecosystem status** trong CIS admin có thêm (đã lên Dev 25/11, ảnh desktop / mobile, sáng / tối):

- Bảng **What changed**: lần phát hành, đổi cài đặt, cập nhật dữ liệu, đổi định tuyến AI, có đánh dấu trên biểu đồ.
- Người phụ trách có thể **xác nhận / tạm hoãn / tắt tiếng** một cảnh báo kèm lý do, có ghi lại ai làm lúc nào. Chủ doanh nghiệp chỉ xem, không có nút.
- Nhãn "as of" cho biết dữ liệu mới tới đâu, dự báo còn bao nhiêu ngày tới giới hạn dung lượng và hạn mức AI, cảnh báo chi phí AI tăng bất thường, lưu các góc nhìn hay dùng.
- Nút **Actions** trên mỗi cảnh báo mở danh sách việc nên làm, xếp theo rủi ro, có cách quay lại. Chưa dùng AI, không tự chạy việc gì.

Ngoài ra, nếu bước kiểm tra sau phát hành báo đỏ, CIS admin, Booking admin, CRM web và TripPlanner web giờ tự quay về bản trước và mở ghi chú lỗi.

Ảnh: `s291-aa1141-status-1440-light.png`, `s291-aa1141-status-1440-dark.png`, `s291-aa1141-status-390-light.png`, `s291-aa1154-status-actions-drawer.png`
