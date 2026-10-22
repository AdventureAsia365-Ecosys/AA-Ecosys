# S247 — nháp Jira (22/10/2026)

Tác nhân: Claude Code. **Nghiệp duyệt cả 5 nháp ("Ok hết").** Đăng tối 22/10; Atlassian MCP rất chậm (nhiều lần timeout > 300 s, lệnh ghi có thể đã vào dù báo timeout — kiểm bằng JQL `updated >= -Nm` trước khi đăng lại). Không đổi trạng thái, không tạo issue.

## Trạng thái đăng

| # | Issue | Trạng thái |
|---|---|---|
| 1 | PR-22 | **Đã đăng** — comment 10491 |
| 2 | PR-23 | **Đã đăng** kèm 2 link ảnh trên GitHub (tải ảnh lên Jira timeout); xác nhận qua màn hình Nghiệp |
| 3 | PR-27 | **Đã đăng** (1 comment; xác nhận qua Activity stream của Nghiệp). Nghiệp mở quyền chia sẻ thư mục Drive pháp lý cho chị Thư |
| 4 | PR-24 | **Đã đăng** (xác nhận qua Activity stream) |
| 5 | PR-13 | **Đã đăng** (xác nhận qua Activity stream) |

Bản trong repo (public): link thư mục Google Drive ở mục 3 thay bằng chỗ trỏ tới Linear AA-886 (link gốc nằm trong bản nháp đăng Jira và comment Linear); nội dung khác giữ nguyên.

Rà: `project in (PR, KAN, CON) AND statusCategory != Done` — PR 22 issue, KAN/CON 50+ issue (việc nội dung/marketing, không có việc kỹ thuật S247). PR-20 báo cáo tuần: kỳ trước 19/10, kỳ tới ~26/10, không đăng lần này. CRM (PR-19/PR-26): mới xong phần nền móng, chưa có tính năng để báo → không đăng.
Mỗi bản đăng dạng HTML, mở đầu bằng mention `@thule` (span data-type="mention").

---

## 1. PR-22 — CIS nội dung (đã đăng, comment 10491)

@thule Cập nhật nội dung blog và LinkedIn ngày 22/10:

- **FAQ trong bài blog**: câu hỏi FAQ giờ lấy từ câu hỏi thật người dùng tìm trên Google (mục "People also ask") cho đúng địa điểm của bài, câu lạc đề bị lọc. Mỗi câu trả lời được kiểm xem có trả lời đúng câu hỏi không; cặp nào không đạt bị bỏ trước khi giao cho tenant.
- Kiểm trên 8 bài blog mới của 4 thương hiệu mẫu (22/10): 36 cặp hỏi–đáp viết ra, 7 cặp bị bỏ vì trả lời lạc, **29 cặp giao đi — 3 người chấm độc lập: 0 câu trả lời lạc** (lần đo trước: 3/31). Cả 29 câu đều khớp nguồn tour.
- **Bài LinkedIn**: tối thiểu 120 chữ, đúng giọng thương hiệu, bỏ kiểu mỗi câu một dòng và các câu sáo.
- Chi phí thêm cho phần kiểm FAQ: khoảng 0,5 cent mỗi bài.

## 2. PR-23 — Portal tenant (đã đăng)

@thule Portal cho đối tác đã được làm lại khung và rà từng trang (22/10):

- Khung mới: menu gom theo nhóm, ô tìm nhanh (Ctrl K), thanh điều hướng dưới cùng trên điện thoại, giao diện sáng/tối.
- Rà từng trang ở máy tính và điện thoại, sáng và tối: trang trống có hướng dẫn bước tiếp ("Browse tours") thay cho số 0; có trạng thái đang tải và nút thử lại; chữ xám đủ độ tương phản để đọc.
- Số "API calls" ở trang Billing giờ chỉ đếm lượt gọi API của hệ thống tenant, không đếm lượt mở trang portal (kiểm live: mở 3 trang → số không đổi; 1 lượt gọi API → tăng 1).
- Kiểm tự động trên portal thật với tài khoản tenant thử: 50/50 bước đạt. Ảnh đính kèm: Dashboard trống (máy tính) và My Tours trống (điện thoại, nền tối).

## 3. PR-27 — Nền tảng (bảo mật, vận hành, pháp lý) (đã đăng)

@thule Cập nhật nền tảng chung ngày 22/10:

- **Tách dữ liệu giữa các tenant ngay ở cơ sở dữ liệu**: mọi trang của tenant (danh sách chủ đề, kế hoạch, duyệt bài, marketplace, đánh giá) giờ chạy bằng quyền chỉ đọc/ghi được dữ liệu của chính tenant đó. Một bài kiểm tự động chạy hằng đêm thử đọc chéo giữa các tenant: 58/58 đạt, 0 dòng đọc chéo.
- **Theo dõi lỗi** cho hệ thống Booking và TripPlanner (báo lỗi tự động, mỗi yêu cầu có mã để tra).
- **Số phiên bản và nhật ký thay đổi** cho từng app: CIS 0.5.0, Booking 0.2.0, TripPlanner 0.4.0 — biết chính xác bản nào đang chạy.
- **Bộ hồ sơ pháp lý (bản nháp để chị xem)**, trên Google Drive, thư mục "Legal readiness packet (2026-10-22)": (link thư mục Drive — xem comment Done của Linear AA-886) — gồm bản tóm tắt song ngữ, danh mục xử lý dữ liệu, mẫu thỏa thuận xử lý dữ liệu (DPA), quy trình xử lý yêu cầu xoá dữ liệu, điều khoản sử dụng AI cho tenant (nháp). Trang /privacy và /terms đang ở dạng nháp có ghi "chờ duyệt pháp lý". Việc có cần luật sư xem hay không là chị quyết.

## 4. PR-24 — TripPlanner (đã đăng)

@thule Cập nhật TripPlanner ngày 22/10 (bản 0.4.0):

- Chuyến đi của khách giờ chỉ mở được bằng đúng mã của khách đó; đoán đường dẫn không xem được chuyến của người khác.
- Dữ liệu địa điểm trên bản đồ giờ lấy từ kho nội dung chung của Adventure Asia (cùng nguồn với CIS), không còn bảng riêng.
- Có theo dõi lỗi tự động cho trang web và phần xử lý phía máy chủ.

## 5. PR-13 — Jev (đã đăng)

@thule Cập nhật về Jev (lớp ra quyết định) ngày 22/10:

- Đã đánh giá từng câu hỏi Jev trên dữ liệu thật: giữ các câu có tác dụng thật và đáng tin (phân loại dòng khi tải file lên, lọc từ khoá và câu hỏi tìm kiếm theo địa điểm, ghép địa điểm), đã tắt 2 câu không thêm giá trị. Câu chấm văn bản tour còn chạy, sẽ tắt sau khi có luật kiểm bữa ăn bằng code (đang làm).
- Phần nội dung của tenant (bài viết, mạng xã hội) hiện không gửi qua Jev, vì chưa có thỏa thuận xử lý dữ liệu với nhà cung cấp.
- Đã so Jev với bộ lọc hiện tại cho câu hỏi FAQ: Jev chỉ có sẵn kết quả cho khoảng 1/3 câu hỏi và kém chính xác hơn, nên FAQ giữ bộ lọc hiện tại.
