# Nháp Jira S256 (29/10/2026) — CHƯA ĐĂNG, chờ tech lead duyệt

Soạn lúc 29/10 08:15 +07 (Claude Code, phiên S256). Một comment cho mỗi epic có tính năng ship trong phiên, đứng tên tech
lead, tag chị Thư bằng mention node khi đăng (`<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`,
`contentFormat: html`; bảng markdown đổi sang bảng HTML khi đăng). Số liệu lấy trong phiên S256 (28–29/10/2026), giờ ghi ở
bảng bằng chứng cuối mỗi mục.

## Rà Jira trước khi soạn (29/10 08:05 +07, chỉ đọc)

- JQL `project in (PR, KAN, CON) AND statusCategory != Done`: **125 issue** (KAN 65, CON 37, PR 23). Không có yêu cầu mới
  nào sau 28/10 trong PR/KAN/CON.
- Comment mới nhất trên các epic: PR-22…PR-27 đều là comment 10515–10520 đăng 28/10 20:43 (S254 + S255). Nháp dưới đây
  **không lặp lại** nội dung đó; chỗ nào nối tiếp thì ghi rõ "tiếp theo cập nhật 28/10".
- PR-20 (báo cáo định kỳ): 0 comment; kỳ 2 là PR-28 (20–26/10). Theo nhịp mỗi tuần một kỳ (memory `platform-report-weekly`),
  **kỳ 3 (27/10–02/11) soạn từ thứ Hai 02/11**, không soạn hôm nay.
- KAN-90 "DataforSEO search spent high: critical" (To Do): đã có giải thích nguyên nhân 28/09 và kết quả sau sửa 03/10. Việc
  mới của S256 (sự cố 25/09 hiện trên trang Cost Operations) khớp issue này → nháp tuỳ chọn ở cuối.

## Ảnh nhúng

Thư mục `docs/audits/2026-10-29-S256-ui-evidence/` **chưa có lúc soạn** (08:11). Tên file ghi ở từng mục là tên đề xuất;
điều phối thay bằng tên file thật trước khi đăng. Quy tắc: câu nào nói "chạy được trên giao diện" chỉ giữ khi có ảnh live
tương ứng; không có ảnh thì bỏ dòng "Ảnh:" và giữ cách viết "đã kiểm bằng kịch bản, chưa thử qua giao diện".

---

## PR-22 — CIS nội dung & pipeline

**Vì sao:** chi phí 25/09 nay giải thích được ngay trong admin; kiểm tra chất lượng bản viết lại của tenant có thêm bước mới.
**Đăng ở:** comment trên epic PR-22.

> @thule Cập nhật CIS ngày 29/10 (tiếp theo cập nhật 28/10):
>
> - **Sự cố chi phí 25/09 hiện ngay trong trang Cost Operations** (tab DataForSEO): thẻ sự cố ghi số lần gọi, số tiền, hai
>   đợt chạy và nguyên nhân. Chi tiết ở KAN-90.
> - **Kiểm câu khẳng định về thương hiệu trong bản viết lại của tenant.** Mỗi bản viết lại giờ lưu điểm chấm chi tiết, và
>   các câu tenant khẳng định về mình (ví dụ "trẻ từ 7 đến 16 tuổi", "do người địa phương sở hữu") được đối chiếu với hồ sơ
>   thương hiệu. Câu không có nguồn bị gắn cờ cho người duyệt; tenant không thấy phần chấm này.
>   Đã chạy thử trên Dev 28/10 với một bản viết lại mới: đạt. Quét lại 61 bản viết lại cũ: 9 bản có câu không có trong
>   nguồn, đã gắn cờ.
> - **Writing memory:** mỗi bản viết lại của tenant ghi lại bộ quy tắc viết đã dùng, để biết bản nào viết theo quy tắc nào
>   khi bắt đầu áp quy tắc mới. Tenant không thấy thông tin này (đã kiểm qua đúng các đường tenant đọc). Trang Releases có
>   nút "Check now" kiểm thử trước khi áp, không tốn phí.
>
> Ảnh: (1) thẻ sự cố 25/09 trên tab DataForSEO của Cost Operations, (2) phần chấm chi tiết của một bản viết lại.

Ảnh (live, 29/10): `docs/audits/2026-10-29-S256-ui-evidence/05b-cost-ops-dfs-incident-card.png`, `04b-content-quality-t2-judge-breakdown-drawer-1440.png`.

| Câu | Bằng chứng (nội bộ, không đăng) |
|---|---|
| Thẻ sự cố 25/09 trên Cost Operations | CIS #1106 `1b88edce` deploy; `GET /admin/dfs-usage/runs?start=2026-09-25&end=2026-09-25` → 200, `incidents[0].id = 2026-09-25-dfs-research-sweep` (28/10, `docs/audits/2026-10-28-S256-aa665-spike-attribution/live-verify-dfs-usage-runs.txt`); viewer 403 |
| Kiểm câu khẳng định, chạy thử đạt, 61 → 9 | mig 300 + CIS #1123 `b6b6ea82`; `docs/audits/2026-10-28-S256-aa795-t2-judge/live-proof.txt` (verdict PASS, 28/10 18:47Z; claims scan 61 scanned / 9 flagged) |
| Ghi bộ quy tắc, tenant không thấy, Check now | mig 297 + CIS #1114 `717c58f1`; `docs/audits/2026-10-28-S256-aa920-wm25/live-proof.txt` (PASS, curl tenant 0 khoá cấm) |

---

## PR-23 — Portal tenant

**Vì sao:** Marketplace có bộ lọc + ảnh bìa (đã hẹn "bản kế tiếp" ở comment 28/10); portal chỉ còn một bản.
**Đăng ở:** comment trên epic PR-23. **Điều kiện đăng:** mục portal chỉ đăng khi việc chuyển portal được điều phối chốt xong
(còn deploy CRM và sửa một lỗi vai "chỉ xem" trong phiên); Marketplace chỉ đăng câu "trên bản đang chạy" khi có ảnh live.

> @thule Cập nhật Portal ngày 29/10 (tiếp theo cập nhật 28/10):
>
> - **Marketplace có bộ lọc mới và ảnh bìa:** lọc theo nước, số ngày, loại hoạt động, độ khó, "mới thêm trong 30 ngày", kèm
>   ô tìm kiếm. Mỗi thẻ tour có ảnh bìa, nhãn độ khó và các loại hoạt động; ảnh tải dần khi cuộn và tự chọn cỡ ảnh hợp màn
>   hình. Tour chưa có ảnh hiện ô thay thế.
>
>   | Đo trên dữ liệu thật (28/10) | Kết quả |
>   |---|---|
>   | Tour trong Marketplace | 892 |
>   | Có loại hoạt động / độ khó | 877 / 877 |
>   | Có ảnh bìa | 162 |
>   | Thời gian lọc (nặng nhất: hoạt động "Trekking") | dưới 0,07 giây |
>
> - **Portal chỉ còn một bản** ở portal.lumiguides.it.com, chạy trên máy chủ của AA. Bản cũ trên Vercel đã gỡ, địa chỉ cũ
>   partner-dev.lumiguides.it.com tự chuyển sang portal. Cách đăng nhập cũ bằng khoá API đã tắt: đại lý chỉ đăng nhập bằng
>   tài khoản riêng và mã 6 số trên điện thoại. Bộ kiểm giao diện tự động sau khi chuyển: đạt hết.
> - Kết nối Gmail của đại lý trên địa chỉ mới: đã kiểm tới bước chuyển sang trang đồng ý của Google (đúng địa chỉ trả về
>   portal.lumiguides.it.com); chưa bấm đồng ý bằng một hộp thư thật.
>
> Ảnh: (1) Marketplace với bộ lọc và ảnh bìa trên máy tính, (2) trên điện thoại, (3) ngăn chi tiết tour có ảnh bìa.

Ảnh (live trên portal, 29/10): `docs/audits/2026-10-29-S256-ui-evidence/01h-portal-marketplace-covers-country-activity-1440.png`,
`01l-portal-marketplace-covers-grid-390.png` (điện thoại, nền sáng — đổi chữ "nền tối" thành "điện thoại"), `01j-portal-marketplace-drawer-cover-1440.png`.

| Câu | Bằng chứng (nội bộ, không đăng) |
|---|---|
| Bộ lọc + ảnh bìa đã ship | CIS #1111 `e85c37f4`, Partner #111 `09c562b`; portal deploy run 40794245317 (29/10 07:29) |
| 892 / 877 / 877 / 162, < 0,07 s | `docs/audits/2026-10-28-S255-aa671-marketplace/filters-cover-S256/live-timing-coverage.txt` (count trekking 66,1 ms, các lọc khác ≤ 49 ms) |
| Ảnh tải dần, chọn cỡ ảnh | README cùng thư mục (dữ liệu giả, local build) — cần ảnh live để đăng |
| Một bản portal, Vercel gỡ, partner-dev 301, khoá API tắt | Partner #115 `a6d6f28`, Infra #484 apply; curl 29/10 08:11 +07: partner-dev → 301 (CloudFront), `aa-cis-portal.vercel.app` → 404, `portal…/tenant-login` → 308 tới `/auth/refresh`; checklist: Deploy Portal Dev success, smoke 63/63 |
| Gmail chưa thử | checklist cửa sổ 2: redirect URI Google chưa thêm |

---

## PR-24 — TripPlanner

**Vì sao:** comment 28/10 báo tốc độ tải trên điện thoại còn khoảng 4,8 giây (mục tiêu 2,5 giây); nay trang chủ và trang tour
đạt trên bản đang chạy.
**Đăng ở:** comment trên epic PR-24 (story PR-11 không cần comment riêng).

> @thule Cập nhật TripPlanner ngày 29/10 (tiếp theo cập nhật 28/10):
>
> - **Tốc độ tải trên điện thoại đạt mục tiêu ở trang chủ và trang tour.** Ảnh đầu trang tải cùng đường với trang, không tải
>   nhầm ảnh của trang khác; CIS có thêm cỡ ảnh trung bình (960 px) cho 3.229 ảnh.
>
>   | Đo trên bản đang chạy (Lighthouse điện thoại, 29/10) | Hiện ảnh chính | Điểm tốc độ |
>   |---|---|---|
>   | Trang chủ | 1,54 giây | 100/100 |
>   | Trang tour | 1,57 giây | 100/100 |
>   | Danh sách điểm đến | 3,38 giây | 92/100 |
>   | Trang một nước (Bhutan) | 3,88 giây | 88/100 |
>
>   Mục tiêu: dưới 2,5 giây. Hai trang điểm đến còn chậm hơn mục tiêu và dao động nhiều giữa các lần đo (1,4–4,8 giây); xử lý ở
>   bản kế tiếp.


Ảnh đề xuất: `tp-home-390-light.png`, `tp-tour-390-light.png` (production). Ảnh local build ở
`docs/audits/2026-10-28-S256-aa995-lcp/shots/` không dùng để đăng.

| Câu | Bằng chứng (nội bộ, không đăng) |
|---|---|
| Số Lighthouse production | `docs/audits/2026-10-28-S256-aa995-lcp/production-after.md` (29/10 ~08:00 +07, 3 lần, trung vị); TP #178 `c9d84bc3` |
| 3.229 ảnh 960 px | mig 301 (CIS #1124, Infra #490, apply 40791617873) + CIS #1125 `5923c46b`; backfill 3.229 ghi / 0 lỗi / 0 còn lại |
| Ảnh đầu trang cùng đường, không tải nhầm | README AA-995 lcp mục "What was slowing the LCP" 1–2; production `/photo-cdn` 200 `image/webp`, lần 2 HIT |

---

## PR-25 — Booking

**Vì sao:** danh sách trip plan (lỗi 27/10) nay nhanh hơn rõ; chứng từ tải lên được sau khi tạo kho lưu trữ.
**Đăng ở:** comment trên epic PR-25.

> @thule Cập nhật Booking ngày 29/10 (tiếp theo cập nhật 28/10):
>
> - **Danh sách trip plan nhanh hơn khoảng 4 lần:** phần đọc tên địa điểm của tour được đọc sẵn từ CIS.
>
>   | Đo trên Dev (29/10) | Trước | Sau |
>   |---|---|---|
>   | Tên địa điểm cho 25 tour | 0,38 giây | 0,11 giây |
>   | Tên địa điểm cho 100 tour | 1,18 giây | 0,27 giây |
>   | Cả trang danh sách 100 trip plan (lần mở đầu) | — | 0,50 giây |
>
>   Kết quả địa điểm giữ nguyên như trước (kiểm 100/100 tour).
> - **Tải chứng từ lên Booking đã chạy:** voucher và xác nhận của nhà cung cấp, chứng từ thanh toán, hoá đơn nhà cung cấp,
>   phiếu chi. Trước đây việc tải lên báo lỗi trên Dev vì kho lưu file chưa được tạo; nay có kho riêng, không công khai, có
>   mã hoá. Đã kiểm trên Dev 29/10 với một booking nhà cung cấp thử: tải lên → tải về đúng file → gỡ file, mỗi bước có ghi
>   nhật ký. Lần kiểm này chạy bằng kịch bản kiểm trong hệ thống, chưa thử bấm qua giao diện.


Ảnh đề xuất: `booking-trip-plans-1440-light.png`. Nếu thư mục ui-evidence có ảnh tải voucher qua giao diện
(`booking-supplier-voucher-upload-1440-light.png`) thì đổi câu cuối thành "đã thử qua giao diện" và thêm ảnh (2).

| Câu | Bằng chứng (nội bộ, không đăng) |
|---|---|
| 25 tour 381 → 109 ms; 100 tour 1.176 → 274 ms; list 497 ms; same_places | `docs/audits/2026-10-28-S254-booking-figma-audit/v-tour-place-name-live-S256.md` (29/10 00:35 +07, BUDGET_OK); CIS #1118 mig 298, Infra #487, DB Migrate 40734310260, Booking #141 `ad4be194` |
| Chứng từ tải lên / tải về / gỡ, nhật ký | `docs/audits/2026-10-29-S256-aa682-ops-docs/README.md` (sha256 khớp, AES256, 3 dòng audit, RC=0); Infra #489 `77185f97` + apply 40788053737, Booking #142 `5a115023`; `/booking/health/ready` ops_docs = configured |
| Kho không công khai, mã hoá | cùng README: public access block 4/4, mã hoá mặc định AES256 |

---

## PR-27 — Nền tảng (đăng nhập, bảo mật, hạ tầng)

**Vì sao:** cảnh báo bảo mật báo 28/10 nay đã thử bằng thay đổi thật; rà dung lượng tháng đầu; sơ đồ kiến trúc mới.
**Đăng ở:** comment trên epic PR-27.

> @thule Cập nhật nền tảng ngày 29/10 (tiếp theo cập nhật 28/10):
>
> - **Cảnh báo bảo mật đã thử bằng thay đổi thật** trên tài khoản AWS (tạo rồi xoá ngay các đối tượng thử, không ảnh hưởng hệ
>   thống):
>
>   | Loại thay đổi | Lần thử | Có cảnh báo |
>   |---|---|---|
>   | Tường lửa (mở/đóng cổng) | 4 | 4 |
>   | Quyền truy cập (tạo, gắn nhãn, xoá) | 6 | 6 |
>   | Nhật ký hoạt động | 1 | 1 |
>   | Tài nguyên chia sẻ ra ngoài | 1 | 1 |
>
>   Email gửi đi không lỗi lần nào. Khi chuẩn bị thử, phát hiện việc đổi nhãn trên quyền truy cập chưa bị báo; đã bổ sung.
> - **Rà các tài nguyên chia sẻ ra ngoài:** 11 mục, đều là kết nối có chủ đích (triển khai tự động từ GitHub, tài khoản quản
>   trị của tổ chức, tài khoản AI đọc dữ liệu xử lý theo lô). Không có chỗ nào bị lộ. Từ nay chỉ mục mới phát sinh mới gửi cảnh
>   báo.
> - **Rà dung lượng hệ thống tháng đầu:** giới hạn số máy chủ API tự mở rộng từ 7 xuống 3 để không vượt số kết nối cơ sở dữ liệu
>   cho phép; bật thống kê truy vấn đầy đủ hơn. Cơ sở dữ liệu khởi động lại lúc 06:40 sáng 29/10, CIS, Booking và CRM hoạt động
>   bình thường ngay sau đó. Từ nay rà dung lượng và chi phí hằng tháng, rà quyền truy cập hằng quý.
> - **Sơ đồ kiến trúc** dùng biểu tượng AWS chính thức: toàn hệ thống và từng app (CIS, Booking, TripPlanner, CRM/Portal, hạ
>   tầng), xem trong trang Docs của admin. Sơ đồ đã đối chiếu với hạ tầng đang chạy; chỗ lệch đã sửa (nhờ đó tìm ra kho chứng
>   từ Booking chưa được tạo, xem cập nhật Booking).
> - **Admin CIS có hai ngôn ngữ:** mặc định tiếng Anh, bấm nút EN | VI trên thanh trên cùng để chuyển sang tiếng Việt; trang
>   nào cũng một ngôn ngữ, không trộn. Đã kiểm trên bản đang chạy 29/10: Tổng quan, Hàng chờ duyệt, Job đổi đúng ngôn ngữ, chuyển
>   lại tiếng Anh được. Câu do hệ thống trả về (ví dụ thông báo trạng thái) vẫn tiếng Anh ở bản này.
> - Các bản phát hành mới (28/10): CIS 0.14.0, Booking 0.10.0, CRM 0.8.0, TripPlanner 0.11.0.
>
> Ảnh: (1) sơ đồ toàn hệ thống trong trang Docs của admin, (2) admin ở chế độ tiếng Việt.

Ảnh (live, 29/10): `docs/audits/2026-10-29-S256-ui-evidence/03b-docs-diagrams-ecosystem-svg-1440.png`, `07b-admin-overview-vi.png`.

| Câu | Bằng chứng (nội bộ, không đăng) |
|---|---|
| Bảng thử cảnh báo, 0 lỗi gửi | `docs/audits/2026-10-28-S256-aa873-triage/alert-test-live.log` (28/10 23:40–23:50Z: SG 4, IAM 6, trail 1, analyzer 1, FailedInvocations 0, SNS Failed 0) |
| Lỗ hổng đổi nhãn, đã bổ sung | README triage §1.4; Infra #483 `b152372e`, apply 40788053737; `sec_alert_check.py` 44 ca / 0 lỗi |
| 11 mục có chủ đích, 0 lộ, chỉ báo mục mới | README triage §2; 3 archive rule + apply-archive-rule ×3 → 0 ACTIVE (Linear comment 28/10 23:51Z) |
| Autoscale 7 → 3, pgss, reboot 06:40, health ok | Infra #481, apply 40712053694; Linear AA-838 comment 28/10 23:53Z; root #314 |
| Sơ đồ, đối chiếu hạ tầng | root #311, #313, CIS #1110 `e1a5f820`, #1115 `4b356ebe`; `docs/audits/2026-10-28-S256-aa697-drift/` |
| Admin EN/VI live | CIS #1129 `3994a1a8` (production f80429a9); `ui-evidence/07a–07c`, `data/cis-run3.json` (0 lỗi console) |
| Bản phát hành | CIS #1093 `67af0922`, Booking #133 `f025ac3b`, Partner #106 `82ab367f`, TP #173 `e4facdea` |

Ghi chú: sơ đồ vẫn chờ tech lead duyệt bản thử (issue sơ đồ còn In Progress); nếu tech lead muốn duyệt trước rồi mới báo chị
Thư thì bỏ mục sơ đồ và câu ngoặc ở mục Booking.

---

## KAN-90 — DataforSEO search spent high: critical (tuỳ chọn)

**Vì sao:** issue chị Thư mở cho sự cố 25/09 vẫn To Do; nay sự cố được ghi lại và xem được trong admin. Không nhắc lại
nguyên nhân đã giải thích 28/09. **Không đổi trạng thái** (tech lead tự quyết nếu muốn đóng).
**Đăng ở:** comment trên KAN-90. Nếu không đăng mục này thì bỏ câu "Chi tiết ở KAN-90" trong nháp PR-22.

> @thule Cập nhật ngày 29/10: sự cố chi phí 25/09 nay được ghi lại trong admin, trang Cost Operations, tab DataForSEO (thẻ sự
> cố), với số liệu đối chiếu từ nhật ký gọi:
>
> | Ngày 25/09 (giờ VN) | Lần gọi | Chi phí |
> |---|---|---|
> | DataForSEO, đợt 1 (12:05–12:23) | 563 | 24,04 USD |
> | DataForSEO, đợt 2 (15:33–15:51) | 605 | 24,98 USD |
> | DataForSEO, cả ngày | 1.169 | 49,02 USD |
> | AI phân tích nhu cầu tìm kiếm đi kèm | 7.856 | 10,27 USD |
>
> Từ sau bản sửa ngày 28/09, việc viết lại tour của tenant không còn gọi DataForSEO; các ngày 26–29/09 chi DataForSEO mỗi
> ngày dưới 1,2 USD.
>
> Ảnh: (1) thẻ sự cố 25/09 trên tab DataForSEO.

| Câu | Bằng chứng (nội bộ, không đăng) |
|---|---|
| Bảng đợt / lần gọi / chi phí | `docs/audits/2026-10-28-S256-aa665-spike-attribution/spike_0925_live_output.txt` (dòng `B dfs_live#1/#3`, `T dfs`, `S a3_search_demand`) |
| 26–29/09 < 1,2 USD/ngày | cùng file, dòng `dfs_by_day_20_29`: 26/09 0, 27/09 0, 28/09 1,118, 29/09 0,386 |
| Thẻ sự cố trong admin | như PR-22 |

---

## Không soạn / không đưa vào (và lý do)

- **PR-26 CRM:** không có tính năng CRM mới ship trong S256 (deploy CRM của việc chuyển portal còn chờ). Không comment.
- **PR-20 / báo cáo kỳ 3:** soạn từ 02/11 (một kỳ mỗi tuần).
- **Chuyển giao diện admin EN/VI trong bộ giao diện chung:** chưa làm trong S256 (checklist mục 8 chưa đánh dấu; không có
  commit CIS nào sau 28/10 18:00 về việc này). Trang Docs EN/VI đã báo 28/10.
- **Định vị lại địa điểm mọi nước:** đang chạy (báo 28/10 "khoảng 3 ngày"); báo khi xong và kiểm lại (~31/10).
- **Giọng thương hiệu vòng thử 9, hiệu chuẩn bộ chấm Writing memory:** thử nghiệm chưa đạt, cờ vẫn tắt; không phải tính năng
  ship. Tech lead muốn báo cho đủ thì thêm một dòng vào PR-22: "Giọng thương hiệu vòng thử 9: chấm mù vẫn chưa tốt hơn bản
  hiện tại, giữ bản cũ."
- **Quy trình phát hành, kiểm quyền DB Migrate, gộp bộ chấm điểm, xoá endpoint cũ:** việc nội bộ, không đổi gì chị Thư thấy.
- **GuardDuty:** quyết định chi phí của tech lead (~15–20 USD/tháng), không đưa chị Thư.

## Kết quả đăng

Chưa đăng. Ghi comment id / link vào đây sau khi tech lead duyệt và điều phối đăng.
