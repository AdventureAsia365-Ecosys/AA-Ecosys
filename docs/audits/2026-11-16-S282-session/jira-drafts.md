# S282 — Jira: tech lead duyệt "đăng" 16/11 ~20:45; đã đăng PR-26 comment 10662, PR-27 comment 10663, PR-22 comment 10664 (ảnh nhúng)

Số liệu lấy trong phiên S282, 16/11/2026, môi trường Dev, đại lý thử.

## 1. PR-26 (CRM cho đại lý)

@thule Cập nhật CRM đại lý ngày 16/11 (Dev, đại lý thử Sen Vàng, dữ liệu thử):

1. **Ô tìm kiếm chung (Ctrl K)** trong app đại lý:
   - Tìm chuyến, booking, nhà cung cấp, dịch vụ và thư viện. Khách chỉ tìm được bằng email, số điện thoại hoặc tên đầy đủ, không tìm được bằng một phần tên.
   - Có dấu hay không dấu đều ra như nhau. Đã thử: "Hội An" và "Hoi An" cùng ra 1 chuyến.
   - Bật riêng cho từng đại lý, mặc định tắt. Trước khi bật cho đại lý thử, tính năng đã qua một lượt rà soát độc lập: không có lỗi nghiêm trọng, 11 lỗi nhỏ đã sửa xong.
   - Đại lý chưa bật thì không thấy ô tìm kiếm (đã kiểm với một đại lý thử khác).
2. **Chiến dịch e-mail** (mục Marketing):
   - Đại lý soạn chiến dịch, xem trước số người nhận, lên lịch hoặc huỷ.
   - Chỉ gửi cho khách đã đồng ý nhận tin. Lượt thử ngày 16/11: 15 khách đủ điều kiện; 175 khách bị loại vì chưa đồng ý; 12 khách không có email.
   - Thư gửi từ hộp thư của chính đại lý. Danh sách dài hơn giới hạn gửi mỗi ngày (400) thì chia ra nhiều ngày.
   - Lượt thử chỉ lên lịch rồi huỷ, chưa gửi thư thật, vì hộp thư của đại lý thử đang ngắt kết nối.
3. **Tính năng xem trước và mục "Có gì mới":** từng đại lý bật xem trước các màn hình mới. Đã thử: đại lý bật thì thấy, đại lý khác không thấy. Có thêm trang công khai về dữ liệu và danh sách nhà cung cấp xử lý dữ liệu.
4. **Gói CRM:**
   - CRM Core 19 USD và CRM Pro 29 USD mỗi người mỗi tháng, tối thiểu 3 người.
   - Gắn CRM cho một đại lý thì được dùng thử 14 ngày. Đã thử trên đại lý thử: dùng thử tới 30/11.

Ảnh theo thứ tự: (1) ô tìm kiếm Ctrl K, (2) trang Marketing có chiến dịch thử đã huỷ.

| Câu | Bằng chứng |
|---|---|
| Hội An = Hoi An | live S282: 200, trip:1 cả hai |
| đại lý khác không thấy | live: RO 403 search_not_enabled |
| 15 / 175 / 12 | preview campaign 16/11 |
| trial tới 30/11 | Tenant 360 Subscriptions (ảnh tech lead) |

Ảnh: `.tmp-session/S282/aa963/palette-on-desktop.png`, `.tmp-session/S282/aa968/marketing.png`

## 2. PR-27 (Nền tảng)

@thule Cập nhật nền tảng ngày 16/11 (Dev):

1. **Bảng giá gói nhập trong admin:**
   - Mọi giá và điều khoản đều chỉnh được trong admin CIS, có lịch sử thay đổi.
   - Đã nhập theo bảng đề xuất (phương án B):
     - Content: 149 / 349 / 699 USD mỗi tháng (3.790.000 / 8.990.000 / 17.990.000 đ). Enterprise theo hợp đồng, từ 699 USD.
     - CRM: 19 / 29 USD mỗi người, tối thiểu 3 người.
     - TripPlanner: 49 / 99 USD.
   - Điều khoản chỉnh được: dùng thử 14 ngày; trả năm (trả 10 tháng, dùng 12 tháng); ưu đãi đại lý sáng lập 30 %; giảm 10 % khi mua cả ba sản phẩm.
   - Trang của từng đại lý có phần báo giá. Ví dụ đại lý thử dùng gói Growth: 349 USD mỗi tháng, trả năm 3.490 USD.
   - Các app khác đã đọc cùng bảng giá này:
     - Trang thanh toán trong app của đại lý hiện đúng số tiền của báo giá. Đã kiểm trên một đại lý thử dùng cả ba sản phẩm: 349 + 57 + 49 = 455 USD, giảm 10 % còn 409,50 USD, khớp báo giá.
     - Hoá đơn phần mềm hằng tháng (Booking) lập theo đúng tiền tệ của đại lý, kể cả VND. Hoá đơn có ưu đãi được đánh dấu để kế toán kiểm lại theo báo giá. Một tháng đã xuất hoá đơn thì không lập trùng lần nữa.
     - Giới hạn số người dùng CRM mỗi đại lý (mặc định 3, tối đa 500) chỉnh được trong admin.
     - TripPlanner đếm số phiên AI mỗi tháng của từng đại lý và dừng AI khi hết hạn mức. Phần này đã kiểm bằng test tự động, chưa thử trên trình duyệt.
   - Trang đề xuất giá chi tiết: https://claude.ai/artifact/61Ujw9rih2K4WPwMKH9XXJ
2. **Trang Delivery** (theo dõi phát hành): cho từng app (CIS, Booking, CRM, TripPlanner, hạ tầng) hiện số lần phát hành mỗi tuần, thời gian từ lúc sửa code tới lúc chạy, tỉ lệ lần phát hành phải sửa lại và thời gian chạy kiểm tra. Số liệu Dev còn ít, chỉ để xem xu hướng.
3. **Theo dõi lỗi đủ cả hệ thống:** 5 phần trước đây chưa báo lỗi về hệ thống theo dõi nay đã báo: trang quản trị CIS, trang quản trị Booking, máy chủ CRM, trang web CRM và TripPlanner. Đã tạo lỗi thử ở từng phần và thấy lỗi về tới hệ thống; thông tin cá nhân được lọc trước khi gửi.

Ảnh: (1) trang Delivery.

| Câu | Bằng chứng |
|---|---|
| giá đã nhập | Plans API PATCH 8 gói, 200 |
| 409,50 = báo giá | studio Billing đại lý thử audit + quote CIS cùng đại lý, 16/11 |
| giới hạn CRM 3 / 500 | Settings CRM, ảnh 16/11 |
| báo giá 349 / 3.490 | Tenant 360 Quote (ảnh tech lead) |
| lỗi thử tới Sentry | probe S282: ingest requests 4 / 3 / 3, CRM api sentry_enabled |

Ảnh: `.tmp-session/S282/aa1108-desktop-light.png`

## 3. PR-22 (CIS nội dung)

@thule Cập nhật CIS ngày 16/11 (Dev):

1. **Dữ liệu nhu cầu tìm kiếm cho địa điểm đã đủ:**
   - Đủ 5.877 địa điểm trong 6 thị trường (Mỹ, Anh, Úc, Đức, Pháp, Hà Lan), không còn địa điểm nào quá hạn.
   - Lượt bổ sung ngày 16/11 tốn 0,65 USD.
   - Đã sửa lỗi mua trùng: trước đây một lượt chạy hỏng làm mất kết quả đã trả tiền, nên phải mua lại. Nay kết quả đã mua được giữ lại và dùng lại; lượt 16/11 lấy lại 601 từ khoá từ kho thay vì mua mới.
2. **Câu hỏi "People also ask" cho tour:** từ 71 % lên **99,4 % tour đã xuất bản (839/844)**. Câu hỏi lấy từ dữ liệu đã mua sẵn, lượt này không tốn tiền.
3. **Tab Research mới** trong SEO Intelligence (admin CIS):
   - Xem địa điểm đang chờ nghiên cứu, chi tiêu tháng so với mức trần, các lượt chạy gần nhất; có nút xem trước (miễn phí) và nút chạy.
   - Có thêm chế độ tự nghiên cứu địa điểm mới hằng đêm, mức trần mỗi lượt và mỗi tháng chỉnh được trong admin. Chế độ này hiện đang tắt.
   - Hệ thống bắt đầu lưu lịch sử nhu cầu tìm kiếm theo tháng (để thấy mùa cao điểm). Dữ liệu sẽ có dần khi các địa điểm được làm mới.

Ảnh: (1) tab Research.

| Câu | Bằng chứng |
|---|---|
| 5.877 địa điểm, 0 quá hạn, 0,65 USD | research S282 (3 job) |
| 601 từ khoá lấy lại từ kho | job research S282 |
| 99,4 % (839/844) | job bù PAA 218c8080, đếm DB 16/11 |
| tab Research | ảnh desktop/phone 16/11, 0 lỗi console |

Ảnh: `.tmp-session/S282/aa1122-research-desktop-light.png`
