# Nháp Jira S257 (29/10/2026) — đã đăng sau khi tech lead duyệt

Soạn cuối phiên S257 (Claude Code), chỉ đọc Jira, không đăng gì. Mỗi comment đứng tên tech lead; khi đăng thay `@thule`
bằng mention node (`<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`,
`contentFormat: html`), bảng markdown đổi sang bảng HTML **nằm ngoài danh sách** (bảng trong `<li>` bị Jira trả 400, S256).
Số liệu lấy trong phiên S257 (29/10/2026).

## Rà Jira trước khi soạn (29/10, chỉ đọc)

- JQL `project in (PR, KAN, CON) AND statusCategory != Done`: **125 issue** (như S256). Issue cập nhật từ 28/10: chỉ 6 epic
  PR-22…PR-27 (do chính các comment của tech lead) → **không có yêu cầu mới** từ chị Thư.
- Comment mới nhất: PR-22 10521, PR-24 10526, PR-25 10527, PR-23 10528, PR-27 10529 (đăng 29/10 09:30–09:31); PR-26 10519
  (28/10). Nháp dưới đây không lặp lại các comment đó, chỗ nào nối tiếp thì ghi "tiếp theo cập nhật sáng 29/10".
- Các mục nối tiếp đã hứa trong comment cũ: PR-24 10526 "hai trang điểm đến còn chậm … xử lý ở bản kế tiếp"; PR-22 10515
  "đợt sửa lại 3.842 điểm … khoảng 3 ngày", "Writing memory … chưa đủ chuẩn để bật, đang tiếp tục", "Giọng thương hiệu
  (vòng thử 8) … giữ bản cũ".

---

## PR-24 — TripPlanner — Lên lịch trình trên bản đồ (khách B2C)

**Vì sao:** nối tiếp câu "hai trang điểm đến … xử lý ở bản kế tiếp" (10526); thêm việc tự xoá thông tin liên hệ cũ.
**Đăng ở:** comment trên epic PR-24.

> @thule Cập nhật TripPlanner ngày 29/10 (tiếp theo cập nhật sáng 29/10):
>
> - **Trang điểm đến tải nhanh hơn** (bản 0.12.0): phần đọc địa điểm của tour nhanh hơn khoảng 8 lần, và mọi ảnh trên
>   trang điểm đến giờ tải cùng đường với trang (không còn ảnh nào tải qua máy chủ API).
>
> | Đo trên Dev (29/10) | Trước | Sau |
> |---|---|---|
> | Đọc địa điểm cho 25 tour | 2,5 giây | 0,31 giây |
>
> - **Tự xoá thông tin liên hệ của khách sau 90 ngày** trong bản lưu tạm các yêu cầu tư vấn gửi từ TripPlanner, chạy tự động
>   mỗi ngày. Lần chạy thật đầu tiên 29/10: 0 yêu cầu (chưa có yêu cầu nào quá 90 ngày). Chạy thử không ghi với mốc 3 ngày:
>   7 yêu cầu sẽ được xoá. Việc chuyển yêu cầu sang Booking vẫn chạy bình thường.
> - **Đo lại trên điện thoại (production, trung vị 3 lần):** trang danh sách điểm đến hiện nội dung chính sau 2,46 giây
>   (trước 3,38 giây), điểm hiệu năng 97 (trước 92). Trang một nước (ví dụ Bhutan) vẫn khoảng 3,9 giây vì ảnh lớn đầu
>   trang, đang xử lý tiếp. Trang chủ và trang tour giữ khoảng 1,5–1,6 giây.

**Ảnh đề xuất:** (1) trang danh sách điểm đến trên điện thoại 390 px, production, kèm tab Network lọc ảnh cho thấy ảnh từ
`/photo-cdn` (cùng tên miền); (2) tuỳ chọn: trang một nước (Bhutan) 390 px. Không cần ảnh cho mục xoá thông tin (việc chạy
nền, bằng chứng là kết quả job).

| Câu | Bằng chứng (nội bộ, không đăng) |
|---|---|
| Đọc địa điểm 2,5 s → 0,31 s (25 tour) | probe run-script 40822241134 (`S257/audits/2026-10-29-S257-c43-w44/tp-place-read-probe-40822241134.txt`: n25 median 2.554 ms với JIT, 0,31 s khi tắt JIT); TP #181 `7118a92` |
| Ảnh cùng đường, 0 ảnh qua api-cis | TP #181; verify live của điều phối (trang điểm đến 0 ảnh api-cis) |
| Bản 0.12.0 | TP #182 `14280c1` (29/10 13:08 +07) |
| Xoá sau 90 ngày, mỗi ngày, lần thật 0 dòng | TP #183 `35e294b` (tp-021), #185 `a694a88`; `S257/aa861/out.json` (mode live, cutoff 31/07, affected 0) |
| Chạy thử 3 ngày: 7 yêu cầu | dry run của điều phối (older_than_days=3) — điều phối điền đường dẫn output |
| Chuyển sang Booking không ảnh hưởng | kiểm của điều phối (`/booking/health` 200, inbox pull) |

---

## PR-23 — Portal tenant — Cổng cho đối tác

**Vì sao:** sửa nhãn giá Marketplace; vai "chỉ xem" dùng được kiểm CTA (thử thật); Facts Entry nếu đã kiểm live.
**Đăng ở:** comment trên epic PR-23.

> @thule Cập nhật Portal ngày 29/10 (tiếp theo cập nhật sáng 29/10):
>
> - **Nhãn giá trên thẻ tour Marketplace gọn lại:** biểu tượng không còn co thành một chấm, các mức giá nằm trên một dòng.
> - **Vai "chỉ xem" dùng được phần kiểm câu kêu gọi (CTA) trên trang Brand:** gõ câu là thấy cảnh báo ngay, còn mọi thao tác
>   sửa, ghi vẫn bị chặn (ví dụ câu nhắc "đánh giá 5 sao" thì hiện lời nhắc chỉ nêu đánh giá có thật). Đã thử trên bản đang
>   chạy 29/10 bằng một tài khoản thử chuyển tạm sang vai "chỉ xem" rồi trả lại.
> - **Trang Facts mới trong Content studio:** đại lý tự thêm thông tin có nguồn của mình (giá, mùa, điều khoản đặt chỗ,
>   thời gian di chuyển…), có hạn hiệu lực. Khi viết bài, hệ thống ưu tiên thông tin của đại lý hơn thông tin chung của
>   Adventure Asia cho cùng chủ đề, và ghi rõ nguồn. Thông tin của đại lý nào chỉ đại lý đó thấy. Đã thử trên bản đang chạy
>   29/10: thêm một giá thử → bài viết kế tiếp của tour đó dùng đúng giá này; một đại lý khác không thấy; xoá xong thì hết.
>
> Ảnh: (1) nhãn giá trên thẻ tour và trong ô chi tiết, (2) trang Brand với vai "chỉ xem" khi kiểm CTA, (3) trang Facts của
> đại lý.

**Ảnh đề xuất:** (1) Marketplace, cận cảnh thẻ tour có nhiều mức giá, 1440 px và 390 px, live trên portal (chưa có — cần
chụp); (2) đã có: `.tmp-session/S257/audits/2026-10-29-S257-viewer-cta/viewer-2026-10-29T05-49-37-708Z-brand.png` (đã xem:
hiện đúng khung cảnh báo "Only mention reviews or ratings if they are real…"; ô CTA còn chữ "(probe 2026-10-29T05-49-37-708Z)"
của kịch bản thử — chấp nhận được, hoặc cắt ảnh chỉ lấy khung cảnh báo); (3) chỉ khi Facts đã kiểm live: trang Facts của tenant thử với 1 thông tin
có nguồn + một bản viết lại cho thấy thông tin đó được dùng.

| Câu | Bằng chứng (nội bộ, không đăng) |
|---|---|
| Nhãn giá | Partner #117 `fac5ea8` (checklist mục 11: "cần ảnh live") — chỉ đăng khi có ảnh live |
| Viewer kiểm CTA 200, ghi bị chặn 403 | CIS #1127 `6e68f48e`; `S257/viewer_cta/results/viewer-2026-10-29T05-49-37-708Z.json` (csr=viewer; ui.cta-check 200; BFF + CIS write/PATCH → 403 `studio_role_forbidden`); owner trả lại 05:50Z |
| Facts Entry | CIS #1138 (mig 302: `valid_until`), CIS #1141 `d8fce643` (tenant `/v1/facts`, ưu tiên tenant trong T9 seed, viewer read-only), Partner #120 `767b686`, root `3cca8e5` (cờ `aa814:facts_pool`) — **chưa có bằng chứng live trong nháp này; cờ phải BẬT cho tenant thử** |

---

## PR-22 — CIS — Nội dung & pipeline

**Vì sao:** nối tiếp ba mục đã báo ở 10515 (định vị địa điểm, Writing memory, giọng thương hiệu). Không phải tính năng mới
ship → **toàn bộ mục này là tuỳ chọn**; tech lead bỏ nếu chỉ muốn báo tính năng.
**Đăng ở:** comment trên epic PR-22.

> @thule Cập nhật CIS ngày 29/10 (tiếp theo cập nhật 28/10):
>
> - **Định vị lại địa điểm (đang chạy):** kiểm mẫu giữa chừng, tỷ lệ địa điểm đúng tăng từ 75,4 % lên 77,7 %, dự kiến khoảng
>   79,5 % khi chạy xong, còn dưới mục tiêu 90 %. Đã thử một quy tắc chấp nhận chặt hơn, chưa bật; đang cải tiến tiếp.
> - **Writing memory:** so sánh 3 model chấm với nhãn chấm tay. Model tốt nhất khớp 0,562 (cách chấm hiện tại 0,316, thang
>   0–1); cần từ 0,6 mới đổi, nên chưa đổi. Bước tiếp: gán thêm nhãn chấm tay.
> - **Giọng thương hiệu (vòng thử 9 và 10):** chấm mù chưa tốt hơn bản đang dùng, giữ bản cũ.

**Ảnh đề xuất:** không bắt buộc (kết quả đo, không phải giao diện). Nếu giữ dòng Facts: trang `/admin/facts` 1440 px.

| Câu | Bằng chứng (nội bộ, không đăng) |
|---|---|
| 75,4 → 77,7 %, dự phóng 79,5 %, mục tiêu 90 % | `S257/audits/2026-10-29-S257-aa997-interim/output.txt`, `docs/audits/2026-10-29-S257-aa997-interim/`; checklist mục 18 |
| Quy tắc chặt hơn, chưa bật | CIS #1139 `070dd7ba` (switch, mặc định tắt) — điều phối xác nhận vẫn tắt |
| Kappa 0,562 vs 0,316, ngưỡng 0,6 | `S257/audits/2026-10-29-S257-aa919-judge-compare/judge-compare-s257.txt`, `kappa-diag-s257.txt`; CIS #1132 `eba2ab7f` |
| Vòng 10 không đạt, giữ bản cũ | `S257/audits/2026-10-29-S257-aa790-r10-panel/aggregate-output.txt` ("round 10: FAIL -> keep both flags off"); vòng 9: S256 r9 panel |
| Trang Facts admin | CIS #1141 — chưa có bằng chứng live |

---

## PR-27 — Nền tảng — Đăng nhập, bảo mật, hạ tầng

**Vì sao:** dọn tài nguyên thừa, chốt cách dựng môi trường Prod, sơ đồ kiến trúc được duyệt (comment 10529 mới mô tả sơ đồ),
các bản phát hành mới.
**Đăng ở:** comment trên epic PR-27.

> @thule Cập nhật nền tảng ngày 29/10 (tiếp theo cập nhật sáng 29/10):
>
> - **Gỡ một ổ lưu trữ file trên AWS (EFS) không còn dùng**, bớt tài nguyên thừa.
> - **Đã chốt cách dựng môi trường chạy thật (Prod):** cùng tài khoản AWS hạ tầng với Dev nhưng tách riêng hoàn toàn (mạng,
>   cơ sở dữ liệu, đăng nhập, khoá mã hoá, quyền); không có môi trường trung gian. Chỉ bắt đầu dựng khi có ngày go-live; bản
>   thiết kế chi tiết Prod làm sau.
> - **Sơ đồ kiến trúc** (đã báo sáng 29/10) được duyệt làm bản chuẩn.
> - Các bản phát hành mới (29/10): CIS 0.15.0 và 0.16.0, Booking 0.11.0 và 0.12.0, CRM 0.9.0, 0.9.1 và 0.10.0,
>   TripPlanner 0.11.1, 0.12.0 và 0.13.0.

**Ảnh đề xuất:** không bắt buộc. Tuỳ chọn: trang Docs của admin mở ADR môi trường (bảng tách riêng Prod) 1440 px.

| Câu | Bằng chứng (nội bộ, không đăng) |
|---|---|
| EFS đã gỡ | Infra #492 `e67b7bcb`, plan 6 destroy; **checklist mục 3 ghi apply bị auto mode chặn** → điều phối xác nhận apply xong + `aws efs describe-file-systems` rỗng trước khi đăng |
| Mô hình môi trường | root #320 `daf49f7a`; `docs/adr/0012-environment-model.md` (Accepted 29/10; §1 không staging, §2 Prod trên acc2, §3 tách riêng từng lớp, phase 3 khi có ngày go-live) |
| Sơ đồ được duyệt | AA-697 Done, root #320 |
| Bản phát hành | CIS #1113 `92934598`, Booking #138 `b2a2124`, Partner #114 `1e32e7f` + #118 `0475679`, TP #179 `c961e12` + #182 `14280c1` |

Ghi chú: Booking 0.11.0 chủ yếu gồm hai việc đã báo sáng 29/10 (danh sách trip plan nhanh hơn, tải chứng từ) — chỉ nêu số bản.

---

## Rà, không cập nhật (và lý do)

- **PR-25 Booking:** S257 không có tính năng Booking mới (chỉ đồng bộ bộ giao diện chung); số bản 0.11.0 nêu ở PR-27.
- **PR-26 CRM:** không có tính năng CRM mới; các bản 0.9.x của AA-Partner chứa việc Portal (báo ở PR-23).
- **PR-20 / PR-28 (báo cáo định kỳ):** kỳ 2 (PR-28, 20–26/10) đã xong; kỳ 3 (27/10–02/11) soạn từ thứ Hai 02/11 theo nhịp
  mỗi tuần một kỳ.
- **KAN-90 (DataforSEO):** không có gì mới sau S256 (tech lead đã chọn bỏ nháp KAN-90 ở S256).
- **KAN / CON còn lại (≈102 issue):** không có cập nhật nào từ 28/10, không khớp việc S257.
- **Không đưa vào (nội bộ):** bot tự mở và gộp bản sao migration, tự gộp bản tham chiếu schema; sửa test chập chờn feed;
  bộ đồng bộ kit; sổ đăng ký prompt LLM; chỉnh độ nhạy cổng T10; ảnh bìa dự phòng theo địa điểm (+0 ảnh, chưa có tác dụng).

## Bằng chứng live bổ sung (điều phối, 29/10 chiều)

- Lighthouse mobile production 3 lần (`docs/audits/2026-10-29-S257-aa995-tp-perf/lighthouse-prod-after-s257.json`):
  /destinations perf 97, LCP 2,46 s; /destinations/bhutan perf 87, LCP 3,95 s; home 1,62 s; tour 1,54 s.
- Dry run 3 ngày: job `f5552794` (7 ứng viên, 7 có liên hệ, 0 ghi); lần thật: job `d0cb7915` (0 dòng); Booking
  `bk_inquiry_pull` 122 lần thành công trong 3 giờ, lần cuối 06:48 UTC.
- Ảnh portal (verdict PASS 8/8): `docs/audits/2026-10-29-S257-ui-evidence/portal-facts-{1440x900,390x844}.png`,
  `portal-tours-card-price-*.png`, `portal-tours-drawer-price-*.png`, `portal-tours-drawer-*.png`.
- Facts live: `docs/audits/2026-10-29-S257-aa814-live/` (tạo 201, cách ly 0/1, seed T9 có `[Fact id=…]` + "agency fact",
  xoá 200).
- EFS: apply local 29/10 (6 destroyed), `describe-file-systems` = 0.
- Dòng Facts admin ở PR-22 đã bỏ (chưa thử live: tài khoản E2E admin chỉ đọc).

## Kết quả đăng

Tech lead duyệt 29/10 (~15:25 +07), đăng cùng ngày:

- PR-24 comment #10530 (không ảnh)
- PR-22 comment #10531 (không ảnh)
- PR-27 comment #10532 (không ảnh)
- PR-23 comment #10533, kèm 4 ảnh nhúng: nhãn giá thẻ tour, nhãn giá ô chi tiết, trang Brand vai "chỉ xem", trang Facts đại lý
