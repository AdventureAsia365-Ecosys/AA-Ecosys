**Tóm tắt thiết kế CRM v3 cho đại lý (AA-821)**

Bản này ghép ba bản nháp (UX, dữ liệu/bảo mật/tích hợp, kế hoạch). Mọi điểm bên phản biện nêu đều đã được sửa. Chưa ghi gì vào repo, AWS, Linear hay Jira, và không gọi dịch vụ trả tiền nào.

**1. Sản phẩm**
- App riêng tên **AA-Partner**, gồm cổng đại lý, CRM web và CRM API, nối với cổng tenant hiện có. Đại lý dùng miễn phí, làm đủ 23 module trên Dev với đại lý giả.
- Lấy **chuyến đi làm thư mục trung tâm**: lead chính là chuyến ở cột đầu.
- Bảng pipeline là hàng đợi việc, có nhãn "đang chờ ai" thống nhất: đại lý, khách, AA, nhà cung cấp, không ai.
- Khách không cần tạo tài khoản. Form và đề xuất mở bằng link ký. Cổng khách vào bằng mã qua email cho từng người; nếu một email gia đình dùng chung thì có màn chọn "Bạn là ai?".
- Kho AA nằm trong ngăn kéo "+ Thêm" của trình soạn đề xuất: giá B2B, giá bán, lãi, tình trạng (có ngay / chờ AA xác nhận trong 1 ngày làm việc / hết).

**2. Các sửa lớn so với bản nháp**
- **Lộ dữ liệu:**
  - F2 vẫn nối được với danh tính qua `trip_id` đối với `crm_app` và tài khoản master. Bản v3 nói thẳng điều này, chặn các vai đọc AI, thống kê và hỗ trợ, và sửa câu chữ trong DPA.
  - Bản offline chỉ lưu lịch trình. Tài liệu chỉ mở khi có mạng.
- **Chống lạm dụng giữ chỗ:**
  - Mỗi phiên bản đề xuất chỉ giữ chỗ một lần.
  - Nút "kiểm tra lại chỗ" dùng tối đa 3 lần mỗi ngày.
  - Mỗi lần giữ lại chỗ đều báo agent.
  - Booking thêm giới hạn tần suất.
- **Chuyển khoản (C31):** khách bấm "Tôi đã chuyển" thì gia hạn hold một lần, và agent nhận việc kiểm tra tiền trước hạn mới.
- **Đăng nhập:** pool Cognito riêng cho đại lý, bắt buộc MFA, làm ngay trên Dev ở W2. Pool EXTERNAL (TripPlanner, Booking) giữ nguyên.
- **Quyền:** có bảng quyền chủ / agent / trợ lý. Lớp lọc trường trả về có test trên mọi route, để trợ lý không bao giờ thấy lãi, giá net hay hoa hồng.
- **Mục chưa duyệt:** bỏ C13 khỏi phần build. C47 gộp vào R6, C39 thành yêu cầu cơ bản của module 5, C34 bỏ.
- **Phạm vi việc nền:**
  - Tách ADR (CRM-01a) và chuẩn dữ liệu (CRM-01b).
  - Ba khoá KMS và hai bucket Object Lock tạo ngay ở CRM-04.
  - Tài liệu mã hoá phía app bằng DEK riêng.
- **Việc thiếu đã bổ sung:**
  - CRM-B2b ở Booking: VND, chính sách phí huỷ, gia hạn hold.
  - CRM-B5 ở CIS: gói "Trước khi đi", mẫu AA, khối nội dung cho chiến dịch.
- **Xoá dữ liệu:**
  - Hàm xoá riêng được phép xoá cả bản ghi chỉ-thêm.
  - Giấy tờ đã ký giữ trong thời hạn khiếu nại bảo hiểm. Đề xuất 3 năm sau chuyến; luật sư xác nhận.
- **Hỗ trợ AA:** lớp L1 (bảng điều khiển, không có dữ liệu cá nhân) vẫn ở W2. L2 (hỗ trợ do chủ cấp quyền) và L3 (truy cập khẩn) dời sang W7, vẫn xong trước Go-real.

**3. Kế hoạch**
- **53 issue** con của AA-821, chia W0–W8, cộng làn Booking/CIS (6 issue) và làn chuyển cổng (2 issue). Tạo issue trước một đợt, nên lúc nào cũng chỉ khoảng 10–14 issue mở.
- **Khối lượng ước tính: 40–45 phiên** (bản nháp ghi 32).
- Với khoảng 2,8 phiên CRM mỗi tuần:
  - M1 khoảng giữa tháng 11;
  - M2 khoảng giữa tháng 12;
  - M3 khoảng đầu tháng 1/2027;
  - **đủ 23 module trên Dev khoảng giữa tháng 2 đến cuối tháng 3/2027**.
- R28, R36, R40, R41, R42 được phép làm sau M4 (vẫn trước Go-real) để rút ngắn đường găng.
- Trình soạn chạy dạng danh sách ngày, không chờ bản đồ TripPlanner (T13).

**4. Chi phí AWS ước tính mỗi tháng**
- Dev khoảng $13–22.
- 10 đại lý khoảng $84–97 (nếu prod là cell riêng thì $104–152).
- 50 đại lý khoảng $319–344.
- Chi phí vendor của AA là $0 theo các lựa chọn đã chốt. Ngưỡng chuyển sang gói trả phí ($150/tháng) sẽ chạm ở khoảng 18–25 đại lý.

**5. Việc của anh**
- Duyệt 8 quyết định trong danh sách.
- Chấp nhận các ADR.
- 7 lần apply cần MFA.
- Nhập secret bằng tay. ⚠️ Có biến env chứa dấu gạch dưới, cần sửa tay trong VSCode.
- Tạo tài khoản test miễn phí: Stripe, Twilio, Google, Microsoft.
- Gửi một câu hỏi cho Twilio.

**6. Việc của chị Thư**
- Xác nhận 12 câu v2.
- Đội của chị viết khoảng 10 gói "Trước khi đi" và mẫu điều khoản / miễn trừ song ngữ, quay video hướng dẫn.
- Lo phần hãng bảo hiểm, luật sư, DPA.
- Sắp xếp người nhập giá net thật.
- Chọn đại lý thật đầu tiên.

**7. Rủi ro lớn nhất**
- Booking chưa có lịch khởi hành, hold hay API B2B.
- Chưa có giá net thật.
- Khối lượng có thể vẫn bị ước thấp.
- Quy định ISV của Twilio.
- Hãng bảo hiểm có thể không nhận chữ ký điện tử tự làm.
