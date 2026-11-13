# Tóm tắt: quay video diễn tập pilot (S279, 13/11/2026)

Bản tóm tắt cho tech lead. Chi tiết từng bước (tiếng Anh): [README.md](README.md).
Video: Drive `01 Video/UAT (kiểm thử nghiệm thu)/Diễn tập pilot (13-11-2026)`, mỗi app một thư mục con (cis-admin,
booking, content-studio, tripplanner, crm). Mỗi video là một file zip gồm MP4 tiếng Anh và tiếng Việt, MP3 lời đọc,
phụ đề SRT/VTT và kịch bản lời đọc.

## Kết quả

- **34 video: 32 PASS, 2 FAIL.** Tổng chi phí LLM **0,49 USD** (trần 10 USD).
- Đại lý tổng hợp `pilot-rehearsal-01`. Tour X là tour 6 ngày ở Philippines, vì không có tour Laos nào có giá hay
  được bán cho đại lý trên Dev. Bước 5 tìm "Bohol".
- Chuỗi bài blog dùng **tour Y** (tour Trung Quốc 20 ngày, có ảnh, chưa có giá), tech lead đã duyệt: mô tả của tour X
  quá ngắn để viết một bài blog (xem mục "Phát hiện").
- **Chạy trọn từ đầu đến cuối:**
  - Tạo đại lý trên CIS, CRM và Booking.
  - Studio: nhập cẩm nang thương hiệu, nhận tour, cập nhật chủ đề, viết blog, LinkedIn và Facebook, sửa bài (thêm link
    lập kế hoạch), đăng / gỡ / đăng lại trên WordPress và trên Page Facebook thử nghiệm (token mới), rồi gỡ hết bài thử.
  - Trang lập kế hoạch của đại lý: tìm kiếm, thêm tour, chat 3 lượt, xem trên điện thoại.
  - CRM: nhận lead, báo giá, chủ duyệt giảm giá và gửi, khách chấp nhận, đặt cọc, AA xác nhận, bảng điều hành AA thấy
    chuyến.
  - Booking: đặt chỗ nhà cung cấp, maker ghi nhận thanh toán, checker duyệt.
  - DRILL-01: diễn tập xoá dữ liệu khi offboard tenant (DRY RUN).

## 2 video FAIL

1. **REH-06:** về sản phẩm thì đạt. Bấm Gửi hai lần chỉ ra một yêu cầu, và CRM nhận đúng một lead. Video FAIL do kịch
   bản đếm sai lần gửi lặp. Lỗi kịch bản đã sửa và có unit test; chưa quay lại để không tạo thêm một lead.
2. **REH-10-portal (v1):** lần đầu, lịch trình chỉ có ngày, không có tên ngày, nơi đến hay dịch vụ (dòng tour AA bị ẩn
   với khách, ngày trong báo giá chưa có nội dung). **Đã sửa** trong AA-Partner #306 (crm-065) và #307. Sau đó quay
   thêm hai video, cả hai PASS: **REH-10a**, chủ đại lý bấm "Show to travellers" cho dòng tour AA (dòng này được xác
   nhận trước bản sửa nên đang ẩn), và **REH-10c**, khách đăng nhập lại và thấy 7 ngày có tên và nơi đến của tour, tour
   đã xác nhận trong mục "What is booked", cùng phiếu dịch vụ.

## Phát hiện cần tech lead quyết

- **Chất lượng dữ liệu: mô tả tour X quá mỏng để viết blog.** Ngưỡng hạt giống cho blog là khoảng 1.398 từ: lấy
  4.700 ký tự chia cho tỷ lệ 3,364 ký tự mỗi từ hạt giống (setting `cis.t7.blog_chars_per_seed_word`), và không dưới
  mức phẳng 600 từ. Lịch trình tour X chỉ khoảng 240 từ, tour Y khoảng 1.900 từ. Trong 841 tour có thể nhận, chỉ 23 tour
  có lịch trình từ 1.400 từ trở lên, và không tour nào trong số đó có giá.
- **Trang Integrations của studio hiện Page id Facebook rõ ràng**, không có chỗ nào để làm mờ khi quay. Kịch bản giờ
  không mở trang này nữa. Hai video lỡ hiện Page id đã bị xoá trên máy, chưa từng upload.
- **"Test & Connect" thất bại vẫn lưu kết nối Facebook** (trạng thái "Needs attention" với token hỏng). Muốn thay token
  phải ngắt kết nối trước. Kịch bản giờ ngắt một lần khi kết nối hỏng rồi kết nối lại.
- Bước 12 (giới hạn ngân sách AI) và bước pilot (tenant marker) chưa làm hôm nay nên chưa quay. REH-08a (Đặt ngay) cần
  bật Book now và có form key.

## Ghi chú khác

- Tour X không có ảnh; tour Y chưa có giá.
- Chuyến 6 ngày hiện thành 4 nhóm ngày trên trang lập kế hoạch, và mục "Getting there" gợi ý bay vào Đài Bắc.
- Bảng điều hành ghi "0 of 1 complete" dù khách đã nhập hộ chiếu.
- Hai bài mạng xã hội viết về tour khác, không phải tour X.
- Lời đọc tiếng Việt của các video đầu được ghép sau khi quay. Mọi đoạn đều có tiếng; đoạn dài nhất lố 1,7 giây so với
  bước của nó.
- CRM được deploy lại giữa lúc quay REH-10b; video cuối (v4) quay trên bản mới.
