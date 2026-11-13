# Tóm tắt: quay video diễn tập pilot (S279, 13/11/2026)

Bản tóm tắt cho tech lead. Chi tiết từng bước (tiếng Anh): [README.md](README.md).
Video: Drive `01 Video/UAT (kiểm thử nghiệm thu)/Diễn tập pilot (13-11-2026)`, mỗi app một thư mục con (cis-admin,
booking, content-studio, tripplanner, crm). Mỗi video là một file zip: MP4 tiếng Anh và tiếng Việt, MP3 lời đọc,
phụ đề SRT/VTT, kịch bản lời đọc.

## Kết quả

- **24 video: 20 PASS, 4 FAIL.** Tổng chi phí LLM **0,29 USD** (trần 10 USD).
- Đại lý tổng hợp `pilot-rehearsal-01`. Tour X là tour 6 ngày ở Philippines: không có tour Laos nào có giá hay
  được bán cho đại lý trên Dev, nên bên điều phối chọn tour này cho mọi bước. Ở bước 5, khách tìm "Bohol" thay vì "Laos".
- **Chạy trọn từ đầu đến cuối:**
  - Tạo đại lý (CIS, CRM, Booking).
  - Studio: nhập cẩm nang thương hiệu, nhận 3 tour, viết bài LinkedIn và Facebook.
  - Trang lập kế hoạch của đại lý: tìm kiếm, thêm tour, chat 3 lượt, xem trên điện thoại.
  - CRM: nhận lead, báo giá có tour AA và giảm giá cần duyệt, chủ duyệt và gửi, khách chấp nhận, đặt cọc, AA xác nhận
    (giá B2B khớp giá trong báo giá), bảng điều hành AA thấy chuyến.

## 4 video FAIL

1. **REH-04-topics:** cả 3 tour đã nhận đều không có chủ đề bài viết (`seed_too_thin`, mô tả tour quá ngắn cho bài
   khoảng 900 chữ). Trang ghi rõ lý do từng tour. Vì không có chủ đề, chuỗi bài blog (viết, sửa, đăng WordPress) không quay được.
2. **REH-04b-facebook:** Facebook từ chối kết nối Page thử nghiệm: "Invalid or expired Page Access Token". Token của
   Page thử nghiệm trong secret đã hết hạn.
3. **REH-06:** về sản phẩm thì đạt: bấm Gửi hai lần chỉ ra một yêu cầu, và CRM nhận đúng một lead (REH-06-lead PASS).
   Video FAIL do phần đếm lần gửi lặp của kịch bản. Chưa quay lại để không tạo lead thứ hai cho đại lý.
4. **REH-10-portal:** đăng nhập bằng mã, hộ chiếu, chuyến bay đến và ký điện tử đều đạt. Lịch trình có đủ 7 ngày nhưng
   không có tên ngày, nơi đến hay mục dịch vụ, nên không thấy tour AA đã xác nhận và chưa tới bước phiếu dịch vụ.
   Có thể là do bước đồng bộ chuyển giao (chạy mỗi giờ) chưa chạy; cần kiểm lại trước khi coi là lỗi code.

## Cần tech lead

- Gia hạn token Page Facebook thử nghiệm, rồi quay lại REH-04b-facebook và REH-04b-takedown.
- Muốn chạy bằng tour Laos: cần nhập giá một tour Laos và được người thứ hai duyệt (REH-01-price-import).
- Bước 12 (đặt giới hạn ngân sách AI) và bước pilot (tenant marker): chưa làm hôm nay, nên chưa quay.
- Booking (REH-09 nhà cung cấp, REH-11 maker/checker): cần chạy seeder Booking cho đại lý này (ECS exec, việc của bên
  điều phối), rồi mới quay được.
- Chọn cách cho chủ đề blog: dùng tour có mô tả dài hơn, hoặc bổ sung mô tả cho tour X.

## Ghi chú khác

- Tour X không có ảnh trong catalogue.
- Chuyến 6 ngày hiện ra 4 nhóm ngày trên trang lập kế hoạch, và mục "Getting there" gợi ý bay vào Đài Bắc.
- Bảng điều hành ghi "0 of 1 complete" dù khách đã nhập hộ chiếu (cùng nghi vấn đồng bộ).
- Hai bài mạng xã hội viết về tour khác, không phải tour X.
- Lời đọc tiếng Việt được ghép sau khi quay (lúc quay worktree thiếu `venv-vi`). Mọi đoạn đều có tiếng; đoạn dài nhất
  lố 1,7 giây so với bước của nó.
- CRM được deploy lại giữa lúc quay REH-10b; video cuối (v4) quay trên bản mới.
