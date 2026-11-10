# S274 — nháp Jira (chờ tech lead duyệt, chưa đăng)

Số liệu lấy trong phiên 09–10/11/2026 trên Dev. Mỗi nháp: issue, lý do chọn, nội dung đăng nguyên văn, bảng câu → bằng chứng.

---

## Nháp 1 — KAN-90 "DataforSEO search spent high : critical"

Vì sao: chị Thư theo dõi chi phí DataForSEO ở issue này; phiên này đổi cách mua (rẻ hơn) và làm mới dữ liệu cho cả catalogue.

Nội dung (đăng dạng HTML, mention chị Thư):

> @thule Cập nhật chi phí và dữ liệu tìm kiếm ngày 09–10/11 (Dev):
>
> - **Đổi sang hàng đợi Standard của DataForSEO** (kết quả trả sau vài phút thay vì ngay lập tức): giá dữ liệu lượt tìm kiếm 0,06 USD mỗi 1.000 từ khoá (trước 0,09), giá một trang kết quả Google 0,0006 USD (trước 0,002). Chất lượng kiểm trên dữ liệu thật: 47/50 từ khoá cho đúng cùng số lượt tìm như cách mua cũ; tỉ lệ trang kết quả có từ 3 câu hỏi "People also ask" là 63,6% (cách cũ 65%).
> - **Làm mới dữ liệu tìm kiếm cho toàn catalogue ở 3 thị trường Mỹ, Anh, Úc**, chạy từng nước với trần chi riêng: Mỹ 1,62 USD, Anh 0,48 USD, Úc 0,48 USD. Mọi địa điểm trong tour đang bán (6.134 địa điểm) đều đã có dữ liệu mới; trước đó khoảng 3.400–3.550 địa điểm chưa từng được nghiên cứu ở mỗi thị trường. Kế hoạch tháng trước ước khoảng 60 USD chỉ cho Mỹ.
> - Từ khoá được lọc độ liên quan trước khi mua: giữ khoảng 91–92%, kiểm tay mẫu 86 từ khoá được giữ: 93% đúng.
>
> | Thị trường | Tour có dữ liệu tìm kiếm (trước → sau, trên 883) | Chủ đề đủ chuẩn Blog (trước → sau) |
> |---|---|---|
> | Mỹ | 635 → 867 | 391 → 1.593 |
> | Anh | 540 → 866 | 221 → 1.257 |
> | Úc | 539 → 867 | 190 → 1.060 |
>
> - **Đức, Pháp, Hà Lan** cũng đã làm mới (0,96 USD mỗi nước, khoảng 6.100 từ khoá mỗi nước, giữ 94,5% sau lọc độ liên quan).
> - Hệ thống nay tự theo dõi mỗi ngày tỉ lệ địa điểm có dữ liệu tìm kiếm cũ theo từng thị trường và báo khi vượt 20%.
> - Bước tiếp: các thị trường đại lý khai mà hệ thống chưa hỗ trợ (UAE, Hong Kong, Ả Rập Xê Út, Singapore, Canada, New Zealand).

| Câu | Bằng chứng |
|---|---|
| Giá queue 0,06 / 0,0006 | `research_quality` `job.unit_usd`, `dfs_queue_trial` (aa1055-live/) |
| 47/50 volume bằng live | dfs_queue_trial S274 |
| PAA ≥3 63,6% vs 65% | `r1-us-standard-quality.out` serp.US.paa_ge3_share |
| Chi 1,62 / 0,48 / 0,48 | `bill.total` mỗi job (aa1055-live/r1-*-quality.out) |
| 6.134 địa điểm, chưa research 3.433–3.553 → 0 | completeness run1/run2 `l3_research.<mk>` |
| Giữ 91–92%, panel 93% | `map.<mk>.kept_share`, r1-relevance-panel.json |
| Bảng tour / Blog | completeness `l3_rank.market.<mk>.tours_demand`, `l3_rank.market_seg.<mk>.blog_bar` |
| ~60 USD kế hoạch cũ | Linear AA-1055 mô tả (S273 preview) |
| DE/FR/NL 0,96, ~6.100, 94,5% | aa1055-live/r2-de-fr-nl-quality.out |
| Theo dõi mỗi ngày, ngưỡng 20% | CIS #1415 live, data coverage `research.stale_share.*` |

---

## Nháp 2 — PR-22 "CIS — Nội dung & pipeline"

Vì sao: tiếp nối comment 09/11 (chủ đề Blog cho đại lý, chất lượng viết); phiên này lấp dữ liệu catalogue cho đại lý dùng ngay.

> @thule Cập nhật dữ liệu catalogue cho đại lý ngày 10/11 (Dev, đo 05:35):
>
> - **Đo lại toàn bộ catalogue từ tour thô tới phần đại lý dùng**: 917 tour đang bán → 892 tour đã có bản AA (25 tour đang chờ duyệt nội dung: Ấn Độ 18, Sri Lanka 4, Philippines 2, Nepal 1) → 892 tour đã tách thành các khoảnh khắc (25.989 khoảnh khắc) → 883 tour đã xếp hạng → 699 tour có lộ trình nhiều ngày (160 tour còn lại là tour 1 ngày, không cần lộ trình).
> - **Thẻ địa điểm**: mọi khoảnh khắc đủ điều kiện đều đã có thẻ (trước còn 215 khoảnh khắc chờ viết thẻ); 17.789 khoảnh khắc có thẻ.
> - **Dữ liệu tìm kiếm**: 867/883 tour có dữ liệu ở Mỹ, Anh, Úc (trước khoảng 540–635). Chủ đề đủ chuẩn Blog cho 9 đại lý (gồm đại lý thử) tăng từ 75 lên 141; chủ đề "chưa có dữ liệu" giảm từ 310 xuống 113.
> - **Lỗi đã sửa**: địa điểm trên các đảo nhỏ (ví dụ Koh Tao, Phi Phi, quần đảo Similan) bị hệ thống coi là "ngoài nước" vì bản đồ ranh giới quốc gia không vẽ các đảo này. Đã sửa để các đảo này được ghim đúng trên bản đồ.
> - Phần còn thiếu cần người: 730 tour chưa có ảnh bìa, 281 tour không có giá tham chiếu trong file nguồn, 25 tour chờ duyệt nội dung.

| Câu | Bằng chứng |
|---|---|
| 917 → 892 → 892 → 883 → 699 | completeness run2 `l1_country.ALL`, `l4_country.ALL` |
| 25 chờ duyệt theo nước | `l1_country.<CC>.src.no_master`, AA-1059 diag |
| 215 → 0, 17.789 | run1/run2 `l2_atoms.link` |
| 867/883, 540–635 | `l3_rank.market.<mk>.tours_demand` |
| 75 → 141, 310 → 113 | `slate_bar_compare` (aa1055-slate/) |
| Đảo nhỏ | CIS #1413 — **chỉ đăng câu này sau khi #1413 deploy + 44 tên geocode lại xong** |
| 730 / 281 | run2 `l5_country.ALL` |

---

## Nháp 3 — PR-25 "Booking" (đề xuất nhẹ cho chủ doanh nghiệp)

Vì sao: S273 bức tranh hệ thống mục 11 — Booking có 892 trip plan nhưng chỉ 2 bán được; đây là dữ liệu thương mại, không phải code.

> @thule Ghi chú về Booking (đo 10/11 trên Dev):
>
> - Mỗi tour đang bán trong catalogue đều đã có một kế hoạch chuyến đi trong Booking (892/892). Hiện 2 kế hoạch đủ điều kiện bán. Dữ liệu thương mại trong Booking còn ít: 5 nhà cung cấp, 9 bảng giá còn hiệu lực, 4 ngày khởi hành mở.
> - Đề xuất: chọn khoảng 10–20 tour ưu tiên (ví dụ các tour đại lý thử đang dùng nhiều), nhập giá nhà cung cấp và ngày khởi hành cho các tour đó trước. Phía kỹ thuật không cần thay đổi gì để bán thêm các tour này.

| Câu | Bằng chứng |
|---|---|
| 892/892, 2 bán được | run2 `l5_booking.data_totals` trip_plans, trip_plans_sellable; `live_tours_without_plan=0` |
| 5 nhà cung cấp, 9 bảng giá, 4 ngày khởi hành | `suppliers_active`, `rates_current`, `departures_open` |


## Đăng (S275, 10/11)

Tech lead duyệt trong S275. Nháp 1 đăng ở **PR-22** (comment 10629), không phải KAN-90. Nháp 2 → PR-22 comment 10630. Nháp 3 → PR-25 comment 10632. Chi tiết: `docs/audits/2026-11-10-S275-session/jira-drafts.md`.
