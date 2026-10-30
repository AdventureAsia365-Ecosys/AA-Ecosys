---
id: PROD-01-aa997-interim-s260
title: "AA-997 interim geocode audit after day 1 of the v2 relocate chain (S260)"
description: "Bản tư vấn cho tech lead: độ đúng geocode 78,4 % ±4,0 (S254 75,4 %, dự phóng 80 %, FAIL mốc 90 %), recheck_14 route 13/16, all-confirmed 0/16, pin được phục vụ 80,6 % → 86,6 % nếu chạy hide_flagged; việc tiếp theo sau lượt chuỗi 31/10."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [aa-cis, aa-booking, tripplanner]
last_reviewed: 2026-10-30
review_every_days: 30
related: [AA-997, AA-990, docs/audits/2026-10-29-S257-aa997-interim/README.md, docs/audits/2026-10-28-S254-geocode-audit/README.md]
---

# AA-997 — audit giữa chừng sau ngày 1 của chuỗi relocate v2 (S260)

Phiên S260, 30/10/2026. Tác nhân: Claude Code (lane L11 chuẩn bị + điều phối chạy). Issue: AA-997 (đầu vào cho AA-990
`recheck_14`). Bản tư vấn cho tech lead, nối tiếp audit S257 (`../2026-10-29-S257-aa997-interim/README.md`).

Mọi script chỉ đọc: một transaction `REPEATABLE READ READ ONLY` (rollback ở cuối), login `cis_app` (biến
`DATABASE_URL` của container CIS api, `ssl="require"`). Không ghi DB, không gọi Geoapify hay LLM: chi phí $0. Riêng
`hide_report.py` xếp một job `place_relocate` mode `hide_flagged` **chỉ báo cáo** (không ẩn dòng nào) và thử một lần
confirm để kiểm lời từ chối 409.

## 1. Trả lời trước

- **Độ đúng (mẫu 600 dòng S254 chấm lại trên toạ độ hôm nay), 30/10 08:25Z: 78,4 % ±4,0** (phân tầng theo cờ),
  so với **75,4 %** ở S254 và 77,7 % ±4,1 ở S257 (29/10). Phân tầng theo provenance: 77,8 % ±3,8. Sai: 18,0 %
  (S254: 21,0 %).
- **Dự phóng theo ô cho toàn bộ 7.986 dòng resolved: 80,0 %.** Cổng: `GATE AA-997 accuracy flag-strat 78.4% FAIL
  (bar 90%)`. Khi chuỗi chạy xong, con số nhiều khả năng vẫn quanh 80 %: chuỗi chỉ xác nhận được ~27 % số dòng nó
  xử lý, phần còn lại giữ điểm của model và chỉ bị gắn cờ.
- **`recheck_14` (AA-990): route 13/16, all-confirmed 0/16 (loose 3/16).** S257: 13/16 và 1/16. Số all-confirmed
  giảm vì luật S258 v2 chặt hơn (không cho `review_reason`), không phải vì dữ liệu tệ đi.
- **Pin được phục vụ cho khách (sau CIS #1178): 80,6 % ±5,0, phủ 65 % dòng. Nếu chạy `hide_flagged`: 86,6 % ±4,6,
  phủ 52 %; ẩn thêm `non_place`: 88,7 % ±4,3.** Vẫn dưới 90 %, và ẩn nghĩa là mất pin: 1.015 pin đang gắn tour sẽ biến
  khỏi bản đồ.
- **Báo cáo `hide_flagged` (job `31b5617a`, 10:08Z): 2.017 dòng ứng viên, 1.015 dòng đang gắn tour.** Confirm bị
  từ chối 409 đúng thiết kế vì job chuỗi `dac718c6` còn queued (chạy 31/10 00:12Z).
- **Đường đọc đã sửa trong phiên:** CIS #1185, Booking #160, TripPlanner #195 bỏ điểm `suspect` và xử lý id đã gộp.

## 2. Chuỗi `place_relocate` v2 đến 30/10

| | số |
|---|---|
| job apply v2 (`accept_rule` aa997.3, strategy v2, `RULE_VERSION` aa997.2) | `d1c6446d` → `3b7c7fd8` → `0286393a` (dừng `stopped_credit_limit`) → `dac718c6` queued 31/10 00:12Z |
| dòng xử lý ngày 1 (`done`) | 830 |
| `confirmed` / `non_place` / `off_route` / `llm_point` | 220 / 49 / 23 / 538 |
| request Geoapify / chi phí | 1.019 / $0 |
| còn lại cho chuỗi (`located_by = llm`, chưa có dấu aa997.2) | 1.005 |

Dấu `geocoder_meta.relocate` theo phiên bản (đếm trên bảng, gồm cả dòng chạm ở S257):

| dấu | confirmed | llm_point | off_route | non_place |
|---|---|---|---|---|
| aa997.1 (29/10, luật cũ) | 325 | 1.004 | 193 | 99 |
| aa997.2 / aa997.3 (30/10) | 334 | 779 | 41 | 62 |

Khối proxy (chỉ dòng của chuỗi v2, không nhãn, 1.216 dòng): pin do geocoder viết qua mọi proxy 83,3 %
(`plausible_confirmed_or_moved`), điểm model giữ lại vẫn trông đúng 70,0 %; 599 / 1.154 pin không có route để chấm.
Khoảng dời: < 1 km 105, 1–5 km 108, 5–25 km 71, 25–100 km 30, > 100 km 20 (trung vị 2,7 km); 71 / 109 lần dời đến gần
route có neo hơn. Theo nước, chuỗi v2 đến giờ chỉ chạm IN, NP, JP, MN (và vài dòng KG, KZ, KP, PK).

## 3. Độ đúng trên mẫu có nhãn

| nhóm | n | đúng trước | đúng hôm nay | sai hôm nay |
|---|---|---|---|---|
| **toàn bộ, phân tầng theo cờ** | 7.924 (S254) | 75,4 % | **78,4 % ±4,0** | 18,0 % |
| toàn bộ, phân tầng theo provenance | | 74,8 % | 77,8 % ±3,8 | |
| dòng mẫu chuỗi v2 đã chạm | 94 | 69,1 % | 71,3 % | 25,5 % |
| mọi dòng mẫu đã chạm (aa997.1 + v2) | 279 | 61,6 % | 66,7 % | 28,7 % |
| dòng mẫu chưa chạm | 321 | 83,5 % | 83,5 % | 14,6 % |

- Theo outcome của chuỗi v2 (đúng / n): confirmed 22/29, llm_point 36/55, non_place 7/7, off_route 2/3.
- `regressed` (S254 đúng, geocoder dời quá dung sai): 9 dòng trên toàn mẫu, 6 trong chuỗi v2. Ví dụ: Sheeshganj
  Gurudwara (2 tour), Janaki Temple, Meherangarh Fort (2 cách viết), Chaturbhuj Temple. Đây là ca geocoder trúng một
  điểm cùng tên khác, cần đọc từng dòng (`L chain_wrong` trong `audit-out-2.txt`).
- Dự phóng theo ô (tỉ lệ đúng của ô × số dòng): geoapify 4.006 dòng 93 %, relocate gắn cờ 2.001 dòng 65 %, llm chưa
  chạm 994 dòng 58 %, relocate confirmed 620 dòng 75 %, mapbox 210 dòng 89 %, relocate non_place 155 dòng 97 %
  → **80,0 %**.

Đọc cổng: một pin sai vẫn tính sai dù đã gắn `review_reason` hay bị ẩn. Chỉ khi một điểm được dời vào dung sai của
điểm `expected` S254 thì dòng sai mới thành dòng đúng. Cờ làm lỗi hiện ra cho người duyệt, nhưng không nâng con số này.

## 4. `recheck_14` (AA-990)

16 tour: 14 tour N1 đang chờ geocode + 2 tour luật chặng transit. 119 địa điểm, 54 đã được geocoder xác nhận,
**65 chưa xác nhận**, chia theo bước kế tiếp (`SUMMARY.next_steps` trong `r14-out-mid.txt`):

| bước kế tiếp | địa điểm | ai làm |
|---|---|---|
| `unlinked`: tên chưa resolve (thường là cụm chặng "A to B", tên mô tả) | 35 | `place_geocode` / admin |
| `old-rule flagged` (aa997.1): llm_point 9, off_route 1 | 10 | chạy relocate `recheck` (strategy v2, aa997.3), dry run trước |
| `relocate chain pending`: chuỗi 31/10 sẽ xử lý | 7 | chờ chuỗi |
| `mapbox point` | 6 | relocate `located_by = ['mapbox']` hoặc admin |
| `chain flagged llm_point` (v2 không tìm được) + `flagged centroid_fallback` | 6 + 1 | admin review trong `/admin/places` |

Tour có `route = N`: `3eda85ad`, `a44bf9c4`, `b5c3c908` (tour 1 ngày không có stop). Tour loose = Y: `0c608efd`,
`b7188d60`, `b9b39260` (thiếu đúng một điểm). 4 tour còn `pending_chain` > 0 (`229f2c60`, `2d9ccb23`, `56e78342`,
`c6b24380`): chạy lại sau chuỗi.

## 5. Pin được phục vụ và đòn bẩy `hide_flagged` (sau CIS #1178)

CIS #1178 (merge `b1dbfca0`, deploy api `:929` / worker `:495`) thêm mode `hide_flagged` / `unhide` cho
`POST /admin/places/relocate` và mục `V` / dòng `SERVED` trong `audit_relocated.py`. Lần chạy 10:08Z
(`audit-out-2.txt`):

| trạng thái | đúng | sai | n có nhãn | phủ |
|---|---|---|---|---|
| mọi dòng (cổng) | 78,4 % ±4,0 | 18,0 % | 600 | 100 % |
| pin phục vụ hôm nay | **80,6 % ±5,0** | 16,3 % | 355 | 65,0 % |
| nếu chạy `hide_flagged` (llm_point + off_route) | **86,6 % ±4,6** | 11,2 % | 270 | 52,0 % |
| + ẩn `non_place` (tuỳ chọn) | **88,7 % ±4,3** | 9,1 % | 261 | 50,8 % |

Dự phóng theo ô trên tập phục vụ: 80,4 % → 85,6 % nếu ẩn (86,7 % kèm non_place). Ô kéo xuống nhiều nhất là
`llm_untouched` (474 dòng phục vụ, 46 %) và `rl_confirmed` (463 dòng, 69 %): ẩn dòng gắn cờ không chạm tới hai ô này.

Lưu ý đo: `V served.source` = `fallback_linked_rows`. `cis_app` không đọc được `catalog.v_tour_component` /
`v_tour_stop` / `v_tour_place` (InsufficientPrivilege), nên "phục vụ" ở đây là mọi destination đang gắn tour (4.855
dòng), chưa trừ tour không live. Con số thật có thể lệch một chút.

### Báo cáo `hide_flagged` (job `31b5617a`, chỉ báo cáo, `hide-report-out.txt`)

- 2.017 dòng ứng viên (`located_by = llm`, outcome llm_point 1.783 / off_route 234; lý do llm_point 1.352,
  unconfirmed_hard_type 431, off_route 234; dấu aa997.1 1.197 / aa997.2 820), **1.015 đang gắn tour**,
  `restored_skipped` 0, `hidden` 0.
- Theo nước: India 567, China 529, Nepal 253, Laos 211, Japan 179, Bhutan 90, Mongolia 69, Sri Lanka 26, Cambodia 17,
  Philippines 17, South Korea 13, Kyrgyzstan 9, Pakistan 9, Taiwan 9, Thailand 7, Kazakhstan 5, Vietnam 3,
  Hong Kong 2, North Korea 1, Tanzania 1.
- 25 mẫu rải theo nước nằm trong output (lat/lng để mở OSM).

### Lời từ chối 409 khi chuỗi còn mở

`{"mode":"hide_flagged","confirm":true,"country":"India"}` → **409** `a place_relocate apply is queued or running: it
keeps stamping rows, confirm once it stopped (and after a new report)`, `apply_job` = `dac718c6`. Đúng luật sau review
#1178: confirm cần một báo cáo succeeded < 6 h với **cùng selection** (outcomes, stamp_versions, stamp_accept, country,
located_by), và không có apply `place_relocate` nào queued/running. Confirm chỉ ẩn dòng có trong cả báo cáo lẫn
selection hiện tại với digest không đổi. Restore một dòng theo `destination_ids` thì dính (pass ẩn sau bỏ qua); unhide
hàng loạt theo dấu thì không dính. Chi tiết: `RUNBOOK.md` §4–5.

## 6. Đường đọc đã sửa trong phiên

| PR | sửa gì |
|---|---|
| CIS #1185 (`2b5b3712`) | route destination của catalog bỏ điểm `suspect`, từ chối id đã gộp |
| Booking #160 (`636df62c`) | màn destination của Booking đánh dấu địa điểm CIS bị ẩn khỏi khách; CONTEXT ghi tên view redirect |
| TripPlanner #195 (`26c2c976`) | trang destination ẩn điểm `suspect`, redirect id đã gộp sang dòng chuẩn |

Trước các PR này, pin bị đánh `suspect` hoặc dòng đã gộp vẫn có thể hiện qua đường đọc chi tiết. Sau khi chúng merge,
`hide_flagged` có tác dụng trên mọi app.

## 7. Việc tiếp theo (sau lượt chuỗi 31/10)

1. **31/10 sau ~01:00Z:** kiểm `dac718c6` và job nối tiếp (1.005 dòng; ngày 1 xử lý 830 dòng với ~1.000 request, nên
   có thể tràn sang 01/11). Khi `J open = []` và `S left_for_chain` ≈ 0, chạy lại `audit_relocated.py` +
   `recheck_14.py` để có số cuối.
2. **Quyết định hide (tech lead):** nếu vẫn dưới 90 % (dự kiến), chạy báo cáo `hide_flagged` mới, đọc 25 mẫu, rồi
   confirm với đúng selection đó. Pin phục vụ dự kiến lên ~86–87 %, phủ ~52 %; undo được (`unhide` theo dấu).
3. **Recheck dòng luật cũ:** 1.197 dòng aa997.1 (llm_point / off_route) chạy relocate `recheck` (strategy v2,
   aa997.3), dry run trước. Đây là đòn bẩy duy nhất thật sự dời được điểm sai vào chỗ đúng, nên cũng là cách duy nhất
   nâng con số cổng.
4. **Mapbox:** 210 dòng (89 % đúng) đứng ngoài chuỗi; chạy relocate `located_by = ['mapbox']` (dry run) hoặc để nguyên.
5. **`regressed`:** đọc 6 dòng của chuỗi v2 (§3). Nếu cùng một mẫu (đền/pháo đài trùng tên trong bán kính route), siết
   luật accept trước lượt recheck.
6. **AA-990:** đóng `recheck_14` chỉ cho tour `route = Y` và `all_confirmed = Y`. 35 địa điểm `unlinked` là phần lớn
   khoảng trống: tách cụm chặng "A to B" ở parse, hoặc sửa tay.
7. **Đo phục vụ cho đúng:** cấp `cis_app` SELECT trên ba view catalog cho script audit (hoặc chạy audit bằng role đọc
   catalog), để `SERVED` đo trên tour live thay vì `fallback_linked_rows`.

## 8. File trong thư mục

| file | nội dung |
|---|---|
| `RUNBOOK.md` | runbook của điều phối (tiếng Anh): chạy, đọc cổng, proxy, `recheck_14`, pass `hide_flagged`, luật confirm sau review |
| `audit_relocated.src.py`, `build_audit_relocated.py` | nguồn audit + builder. Builder nhúng 600 dòng `../2026-10-28-S254-geocode-audit/verified.json` qua `row()` của builder S257 và sinh `audit_relocated.py` (~105 KB, không commit) |
| `recheck_14.py` | AA-990 `recheck_14` (logic S258 v2, cập nhật cho chuỗi v2) |
| `hide_report.py` | xếp job báo cáo `hide_flagged` qua admin API trong container, chờ, in kết quả, thử confirm âm (409) |
| `selftest/fake_audit.py`, `selftest/fake-audit-out.txt` | test local bằng connection giả |
| `audit-out-mid.txt` | lần chạy 08:25Z (trước deploy #1178, chưa có mục `V`) |
| `audit-out-2.txt` | lần chạy 10:08Z (sau deploy #1178, có mục `V` / `SERVED`) |
| `r14-out-mid.txt` | `recheck_14` 08:25Z |
| `hide-report-out.txt` | báo cáo `hide_flagged` + 409 |

Các đường dẫn trong script và `RUNBOOK.md` vẫn trỏ về chỗ chạy gốc `.tmp-session/S260/aa997/`. Muốn chạy lại từ thư
mục này: `python3 build_audit_relocated.py` (nó tự sinh `audit_relocated.py` cạnh nó), rồi
`tools/ecs/ecsx.sh docs/audits/2026-10-30-S260-aa997-interim/audit_relocated.py`. `selftest/fake_audit.py` cần sửa
`path` ở cuối file.

## 9. Giới hạn

- Ground truth vẫn là phán định của người kiểm ở S254 (600 dòng chọn từ dữ liệu 28/10). Dòng dời được chấm theo
  khoảng cách tới điểm `expected` ước lượng.
- Số liệu là giữa chừng: còn 1.005 dòng cho chuỗi. Chuỗi chạy điểm ngủ đêm trước, site sau.
- Tập phục vụ đo bằng fallback (mọi destination đang gắn tour), không qua view catalog (§5).
- Ô ít mẫu (mapbox 9, rl_non_place 9–16) có sai số lớn. Đọc như xu hướng.
