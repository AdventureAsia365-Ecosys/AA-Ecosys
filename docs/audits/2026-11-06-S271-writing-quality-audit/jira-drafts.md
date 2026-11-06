# S271 — Nháp Jira (CHƯA ĐĂNG, gom sang S272)

Tech lead S271 (07/11/2026): "nháp jira lưu lại gom cho phiên sau". Trước khi đăng ở S272: đọc comment mới nhất của từng
issue để không lặp, kiểm lại số liệu live, chụp ảnh bằng chứng (memory jira-claims-need-live-evidence), tag @thule bằng
mention node, không mã nội bộ, không câu hỏi cho chị, không "ạ" (memory jira-draft-tone). Chỉ báo việc đã ship.

---

## PR-22 — CIS: Nội dung & pipeline

@thule Cập nhật chất lượng viết bài (blog, bài mạng xã hội, tour):

- Đã rà soát toàn bộ cách hệ thống viết, chấm và kiểm bài, cho cả blog, tour catalogue và tour viết cho đại lý. Kết luận: giữ phần viết đang tốt, sắp xếp lại phần kiểm và sửa bài để không còn tình trạng sửa đi sửa lại.
- Đã chốt các quy tắc viết rõ ràng: được viết bối cảnh về địa danh, nhưng không bao giờ hứa hoạt động, dịch vụ, giờ giấc hay cảnh quan mà tour không có; câu về độ phù hợp với trẻ em, độ an toàn, nhịp độ chỉ được viết đúng như nguồn.
- Đã đưa lên hệ thống thử nghiệm (đợt đầu): bài viết không còn bị cắt giữa chừng vì hết giới hạn độ dài; lần sửa thứ ba không còn tốn tiền; tour có cưỡi voi được giữ nguyên văn và đưa vào hàng duyệt; số liệu chất lượng được đo mỗi đêm.
- Số liệu nền (8 tuần qua, dùng để so sánh các đợt sau):

| Loại bài | Đạt ngay lần viết đầu | Bị giữ lại để xem |
|---|---|---|
| Blog | 10% | 36% |
| Tour catalogue | 48% | 11% |
| Tour cho đại lý | 64% | 24% |

- Mục tiêu đợt tới: blog đạt ngay lần đầu từ 30% trở lên.

Kế hoạch các đợt tiếp theo em cập nhật dần ở đây.

---

## PR-17 — Tenant viết lại tour đúng giọng thương hiệu

@thule Tour viết lại cho đại lý:

- Tour có hoạt động cưỡi voi: hệ thống giữ nguyên nội dung gốc, chỉ thêm phần thương hiệu của đại lý, và đưa vào hàng duyệt. Đại lý vẫn nhận bài như bình thường.
- Bước chấm giọng văn giờ chỉ để tham khảo, không còn quyết định số lần viết lại, nên bài ra nhanh hơn và ít tốn hơn.

---

## PR-25 — Booking

@thule Booking: đã gỡ toàn bộ phần dành cho khách lẻ (B2C) khỏi hệ thống, đúng mô hình chỉ bán cho đại lý. Dữ liệu cũ của phần này sẽ được xoá hẳn từ 28/11 sau thời gian giữ an toàn 30 ngày.

---

## PR-20 — Báo cáo nền tảng (tuần 02–08/11)

@thule Báo cáo tuần (soạn đầy đủ ở S272 theo mẫu báo cáo tuần): sao lưu dữ liệu tăng lên 14 ngày; trang quản trị của nhân viên chuyển khỏi Vercel sang hạ tầng của mình; gắn nhãn chi phí theo chuẩn cho toàn bộ tài nguyên AWS; quy trình kiểm thử tự động gọn lại khoảng một nửa thời gian chạy.

---

Ghi chú: PR-27 (hạ tầng) không soạn — quyết định kỹ thuật, không báo trên Jira (memory jira-no-tech-decisions).
