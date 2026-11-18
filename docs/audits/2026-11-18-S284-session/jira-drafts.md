# S284 — nháp Jira (chờ tech lead duyệt)

Trạng thái: **đã đăng** 18/11 sau khi tech lead duyệt cả 3 (~16:15): PR-24 comment 10669, PR-25 comment 10670, PR-22 comment 10671 (https://adventure-asia.atlassian.net/browse/PR-24?focusedCommentId=10669, …PR-25?focusedCommentId=10670, …PR-22?focusedCommentId=10671).

## PR-24 — TripPlanner

@thule Yêu cầu khách gửi từ trang TripPlanner của đại lý giờ đã chắc chắn tới tay đại lý, theo cả ba cách đại lý chọn:

- **Vào CRM của đại lý** (đại lý có gói CRM): yêu cầu hiện trong CRM.
- **Qua e-mail**: thư gửi tới địa chỉ đại lý khai, tên người gửi là tên đại lý, bấm "Trả lời" là trả lời thẳng cho khách.
- **Qua hệ thống riêng của đại lý (webhook)**: có chữ ký để hệ thống của đại lý kiểm thư thật.
- Thử ngày 18/11 trên đại lý giả lập, cả ba cách đều tới nơi.
- Khi đại lý dùng hết số phiên AI trong tháng của gói, trợ lý lên lịch tạm dừng và báo cho khách (thử 18/11: dừng đúng, không tốn tiền AI).

## PR-25 — Booking

@thule Hoá đơn phần mềm hằng tháng giờ tính thêm chỗ vượt gói:

- Gói CRM gồm 3 chỗ; đại lý dùng nhiều hơn thì mỗi chỗ thêm là một dòng "Extra seats" riêng trên hoá đơn, cùng giá mỗi chỗ.
- Thử ngày 18/11 với một đại lý giả lập dùng 5 chỗ:

| Dòng | Số lượng | Đơn giá | Thành tiền |
|---|---|---|---|
| Content (Starter) | 1 | 149 USD | 149 USD |
| CRM Core, 3 chỗ trong gói | 3 | 19 USD | 57 USD |
| Extra seats (vượt 3 chỗ) | 2 | 19 USD | 38 USD |
| **Tổng** | | | **244 USD**, khớp báo giá trên hồ sơ đại lý |

- Trả về 3 chỗ thì hoá đơn tự bỏ dòng chỗ thêm (206 USD).

## PR-22 — CIS

@thule Trang tài liệu nội bộ (Docs) đã mở cho mọi nhân viên, dùng giống các trang tài liệu phổ biến:

- Ô tìm kiếm toàn văn trên mọi trang, kết quả có đoạn trích tô đậm từ khoá, bấm là tới đúng mục.
- Mục lục theo chủ đề bên trái, mục lục trong trang bên phải (màn rộng) hoặc ở đầu trang (màn hẹp, điện thoại).
- Mỗi trang ghi ngày sửa gần nhất và lịch sử thay đổi; có trang "What changed in docs" tổng hợp các thay đổi gần đây.
- Trang nào vừa có phần hệ thống liên quan thay đổi được gắn nhãn "Needs review" để người phụ trách xem lại.
- Cuối trang có ô "Trang này có hữu ích không?" để nhân viên góp ý.
