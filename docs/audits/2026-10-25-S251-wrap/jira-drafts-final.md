# S251 — Jira drafts, bản rút gọn để duyệt (25/10/2026)

Bản dài + bảng "câu → bằng chứng": `jira-drafts.md`. Bản này đã điền các ô `[K1]`–`[K4]` theo số kiểm lúc ~16:30Z:
K1 = 80/96 (CIS #1010 chờ nhãn); K2 = CIS 0 cảnh báo quét mã mở (#1011 merged); K3 = E2E Dev CRM run 40202260808 xanh
(6 ảnh aa-lines + ảnh lifecycle); K4 = ảnh portal `.tmp-session/s251/ui-portal/` (Billing, Activity, Integrations, Members).

---

## PR-22 — CIS — Nội dung & pipeline

@thule Dạ chị, việc viết lại toàn bộ nội dung Master đã xong (số liệu 25/10/2026):

| Nước / đợt | Tour viết lại = lên Master | Cờ kiểm tự động (trước → sau) | Chi phí (USD) |
|---|---|---|---|
| Thử 3 + mẫu 50 (13 nước) | 53 | 15 → 4 | 4,11 |
| Mongolia / Pakistan / Hàn Quốc / Bhutan | 13 / 14 / 26 / 27 | 9→0 / 5→2 / 15→3 / 9→0 | 6,25 |
| Đài Loan / Thái Lan / Lào / Philippines | 29 / 34 / 36 / 40 | 8→2 / 13→1 / 11→1 / 13→2 | 9,63 |
| Nhật Bản / Nepal / Trung Quốc | 72 / 76 / 111 | 30→3 / 29→7 / 47→5 | 18,74 |
| Sri Lanka / Ấn Độ | 112 / 167 | 40→0 / 68→6 | 20,63 |
| **Tổng** | **810 (0 chờ duyệt, 0 giữ bản cũ)** | **312 → 36** | **59,34** |

- Chi phí 59,34 USD trong trần 120 USD, khoảng 0,07 USD/tour.
- Giữ số liệu của tour gốc nhiều hơn (độ cao, khoảng cách, thời gian di chuyển): khoảng 42% → 67%.
- Đường dẫn tour đổi theo tên mới; trên TripPlanner đường dẫn cũ tự chuyển sang mới (đã kiểm từng tour).
- 39 tour có cưỡi voi giữ nguyên bản cũ chờ người đọc lại, theo hướng chị đã chọn.
- Bộ viết mới là mặc định từ nay, kể cả tour mới.

**Bước tiếp:** các phần dùng lại nội dung tour (tuyến gợi ý, xếp hạng, địa điểm, TripPlanner, CRM, Booking, SEO) phải đi
theo nội dung mới. Đã có phép đo tự động chạy mỗi đêm để biết phần nào còn dùng nội dung cũ; em đang sửa từng phần.

---

## PR-26 — CRM cho đại lý

@thule Dạ chị, cập nhật CRM cho đại lý (Dev, đại lý thử nghiệm, dữ liệu giả, 25/10/2026):

**Đã thử trọn vòng trên Dev bằng phiên đăng nhập thật (bộ kiểm tự động ngày 25/10, đạt toàn bộ):**
- Nhận yêu cầu khách → thẻ trên bảng theo dõi 9 bước → hồ sơ chuyến; phiếu thông tin chuyến, hoàn tác 10 giây.
- Đề xuất → khách chấp nhận → đánh dấu đã nhận cọc → chuyến chuyển "Đã đặt" → cổng khách bằng mã 6 số → ký điện tử bản
  đầu.
- **Tour AA trong chuyến:** thêm tour AA → "AA đang xử lý" → AA báo giá (có cảnh báo khi giá bán thấp hơn giá "từ") →
  giữ chỗ với AA → đánh dấu mất khách, hoàn tác trong 10 giây vẫn giữ chỗ → mất khách hẳn thì chỗ được trả lại. Đại lý không
  sửa tay được dòng AA; trợ lý của đại lý không tự xác nhận được booking AA.
- Email: thư khách gửi tới được gắn đúng chuyến; thư không khớp vào hộp "Chưa gắn chuyến"; file PDF lưu được.
- Mời thành viên: người được mời dùng được sau khoảng 10 giây.

**Đã có, mới kiểm trong bộ kiểm thử phần mềm:** sổ dịch vụ / nhà cung cấp / tỷ giá; nhật ký không sửa được (xuất mỗi giờ);
che thông tin cá nhân trước khi gửi AI (0 lọt / 260 mẫu); thùng rác, giữ dữ liệu pháp lý, xoá theo yêu cầu; nội dung AA dùng
chung; trang quản lý đại lý cho nhân viên AA.

**Chưa thử:** kết nối Gmail / Microsoft 365 để gửi thư bằng địa chỉ của đại lý (cần người đăng nhập tài khoản thật).

Ảnh: (1) báo giá AA có cảnh báo giá "từ", (2) giữ chỗ với AA, (3) mất khách → đã trả chỗ, (4) chuyến sau khi nhận cọc.

---

## PR-25 — Booking

@thule Dạ chị, cập nhật Booking (Dev, 25/10/2026):

- **Nội dung khách sạn và dịch vụ đi qua CIS (mới, đã chạy thật trên Dev):** nhân viên nhập thông tin khách sạn/dịch vụ
  trên Booking → CIS tự viết bản mô tả (khoảng 0,005 USD/bản) → người duyệt đăng → Booking hiển thị bản đã duyệt, kể cả trong
  đề xuất gửi khách. Đổi thông tin trên Booking thì bản cũ tự ngưng hiển thị và có bản viết mới chờ duyệt; ảnh chỉ được dùng
  khi đã có quyền sử dụng, rút quyền thì ảnh tự gỡ khỏi web; ngừng khách sạn thì nội dung tự gỡ. Bản viết chỉ nói đúng thông
  tin đã nhập.
- **Luồng sự kiện cho đại lý** (báo giá, giữ chỗ, gia hạn, huỷ), không chứa thông tin khách, đại lý không đọc được của nhau;
  CRM của đại lý đang dùng luồng này (đã thử trọn vòng, xem cập nhật CRM).
- **Bàn xử lý yêu cầu "on-request"** và **cờ sự cố cho chuyến khởi hành** (mới kiểm trong bộ kiểm thử phần mềm).
- **Giao diện 1440 px:** 25 trang, nền sáng/tối, máy tính và điện thoại: 100/100 lần mở không tràn ngang.
- **Tự dọn dữ liệu cũ** đã chạy thật một lần trên Dev: lưu trữ trước rồi mới xoá 17 việc nền cũ; xoá thông tin cá nhân của
  5 yêu cầu gốc cũ. Môi trường thật vẫn giữ mốc 90 ngày.

Ảnh: (1) danh sách hồ sơ chuyến 1440 px, (2) bảng đề xuất nền tối, (3) panel nội dung khách sạn đã duyệt + nút "Edit in CIS".

---

## PR-24 — TripPlanner

@thule Dạ chị, cập nhật TripPlanner (25/10/2026):

- **Tour bị gỡ biến mất sau 8 giây** (trước đây tới 30 phút); phục vụ lại thì hiện lại sau 24 giây.
- **Khách đăng nhập bằng mã gửi qua email**, không cần mật khẩu; lần đầu thì tài khoản được tạo luôn.
- **"Chuyến đi của tôi":** chuyến lập khi chưa đăng nhập tự gắn vào tài khoản; mở được trên máy khác; khách khác không thấy.
  Đã kiểm trên bản đang chạy với 2 tài khoản thử, máy tính và điện thoại.
- Đường dẫn tour cũ tự chuyển sang đường dẫn mới sau lần viết lại nội dung.

Chưa thử thật: gửi chuyến cho tư vấn viên khi khách đã đăng nhập. Chưa làm: đăng nhập bằng Google/Facebook.

Ảnh: (1) đăng nhập bằng email, (2) "Chuyến đi của tôi", (3) mở lại trên điện thoại.

---

## PR-27 — Nền tảng

@thule Dạ chị, cập nhật nền tảng (25/10/2026):

- **Diễn tập khôi phục cơ sở dữ liệu:** sẵn sàng sau 21 phút 20 giây (mục tiêu dưới 1 giờ), 164/164 bảng khớp, dữ liệu xoá
  thử lấy lại đúng; chi phí dưới 1 USD.
- **Bộ nhớ đệm CIS được mã hoá**, có mật khẩu; bản cũ đã gỡ (rẻ hơn khoảng 2,8 USD/tháng).
- **Đổi mật khẩu DataForSEO**, kiểm lại chạy bình thường.
- **Cảnh báo "lộ khoá" giả:** 96 cảnh báo là khoá mẫu trong file cấu hình của chính công cụ quét, không phải khoá thật của
  AA. 80/96 đã đóng; 16 cảnh báo còn lại ở kho CIS sẽ đóng khi bản sửa được đưa lên.
- **Lỗi do công cụ quét mã tìm ra:** đã sửa 7 lỗi (chủ yếu mẫu tìm chữ có thể bị làm chậm cố ý) ở CIS và TripPlanner; hiện
  không còn cảnh báo mở.
- **Kiểm độ mới dữ liệu mỗi đêm:** sau khi một tour đổi hoặc ngừng, phép kiểm tự động đo các phần đi theo (tuyến, xếp hạng,
  địa điểm, SEO…) và báo phần nào còn cũ.
- Báo lỗi tự động không còn kèm mã đăng nhập hay email; cảnh báo khi đọc cài đặt tenant bị lỗi (đã thử bằng lỗi giả); tường
  lửa cho các trang đăng nhập (chưa thử tấn công giả lập).

---

## PR-23 — Portal tenant

@thule Dạ chị, cập nhật portal tenant (25/10/2026):

- **Trang Tài khoản dùng dữ liệu thật:** Thanh toán (hạn mức đã dùng, ngày làm mới, phần vượt), Hoạt động (lọc, xuất CSV),
  Kết nối (trạng thái kênh đăng, khoá API được che). Đã kiểm bằng phiên tenant thật trên 2 tenant thử, máy tính và điện
  thoại, nền sáng/tối: không lỗi, dữ liệu hai tenant không lẫn nhau.
- **Bảng "Nội dung của tôi":** lọc, sắp xếp, xem đã lưu, xuất nhiều bài; vừa sửa bố cục ở màn hình rộng (ảnh gửi sau).
- Công cụ nội dung đã chuyển về cùng ứng dụng với CRM ở phía sau; tenant không thấy thay đổi.

**Điều khoản sử dụng AI cho tenant** (chính sách mới của Anthropic hiệu lực 12/11/2026, đã đọc lại 24/10: ngày không đổi):
bản tóm tắt đã có ở mục 3 trang điều khoản (https://portal.lumiguides.it.com/terms, ghi "Draft — pending legal review"),
bản đầy đủ v0.2 để đính kèm hợp đồng. Chưa có tenant thật nên chưa cần thông báo cho ai.
- **A.** Dùng như bản nháp, kịp 12/11. **B.** Nhờ luật sư xem trước. **C.** Dùng ngay như A, nhờ luật sư xem trước tenant trả
  tiền đầu tiên.
- Đề xuất: A hoặc C. Khi tiện chị chọn giúp em; có nhờ luật sư hay không là chị quyết.

Ảnh: (1) Thanh toán, (2) Hoạt động, (3) Kết nối, (4) trên điện thoại.

---

## PR-20 — Báo cáo nền tảng tuần (story mới, kỳ 2: 20–26/10/2026)

@thule Dạ chị, báo cáo nền tảng kỳ 2 (số liệu 25/10/2026). Chi tiết ở comment mới trên từng epic.

| App | Đã xong trong kỳ | Tiếp theo |
|---|---|---|
| CIS (PR-22) | Viết lại 810/810 tour, lên Master hết, cờ kiểm 312 → 36, 59,34 USD | Các phần dùng lại nội dung tour đi theo nội dung mới (đã có phép đo mỗi đêm) |
| Portal (PR-23) | Trang Tài khoản dữ liệu thật; bảng Nội dung của tôi | Chị chọn phương án điều khoản AI (A/B/C) |
| TripPlanner (PR-24) | Tour gỡ biến mất sau 8 giây; đăng nhập bằng mã email; Chuyến đi của tôi | Gửi chuyến cho tư vấn viên khi đã đăng nhập |
| Booking (PR-25) | Nội dung khách sạn/dịch vụ qua CIS chạy thật; luồng sự kiện cho đại lý; tự dọn dữ liệu cũ | Câu hỏi phí huỷ, gia hạn giữ chỗ (PR-25 ngày 23/10) chờ chị |
| CRM (PR-26) | Thử trọn vòng: yêu cầu → đề xuất → cọc → cổng khách → ký; tour AA báo giá/giữ chỗ/trả chỗ | Kết nối Gmail / Microsoft 365 |
| Nền tảng (PR-27) | Diễn tập khôi phục 21 phút, 164/164 bảng; mã hoá bộ nhớ đệm; sửa 7 lỗi quét mã | Thử tấn công giả lập cho tường lửa đăng nhập |

**Chi phí:** viết lại nội dung 59,34 USD (trần 120). Tài khoản AWS cho AI báo chạm mốc 201,69 / 250 USD tháng 10, chủ yếu do
lần viết lại; dự kiến cả tháng 215–225 USD. Rà soát chi phí theo app đầu tháng 11.

**Rủi ro:** không có sự cố ảnh hưởng người dùng; hệ thống vẫn ở môi trường thử nghiệm với dữ liệu thử.

---

## Đã đăng (Nghiệp duyệt "duyệt đăng", 25/10/2026 ~16:10Z)

| Issue | Comment / issue | Ảnh nhúng |
|---|---|---|
| PR-22 | comment 10503 | — |
| PR-27 | comment 10504 | — |
| PR-26 | comment 10505 | 4 (E2E Dev run 40202260808: aa-lines 03/04/06, lifecycle 05) |
| PR-25 | comment 10506 | 5 (cases 1440, proposals dark, panel Customer content desktop + mobile do Nghiệp chụp, trang CIS supply-content) |
| PR-24 | comment 10507 | 3 |
| PR-23 | comment 10508 | 4 (portal atlas-hearth billing/activity/integrations 1440 + billing 390) |
| PR-20 | story mới **PR-28** "Báo cáo nền tảng kỳ 2 (20–26/10/2026)" | — |
