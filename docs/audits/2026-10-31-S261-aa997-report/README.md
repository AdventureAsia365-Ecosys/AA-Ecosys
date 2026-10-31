---
id: PROD-01-aa997-report-s261
title: "AA-997 Places geocode accuracy: full report 28/10 → 01/11/2026 (S254–S261)"
description: "Báo cáo tổng cho tech lead về AA-997: mục tiêu 90 %, cách đo, dòng thời gian theo ngày, các luật aa997.1→aa997.4, lỗi và cách sửa, số liệu, chuỗi recheck aa997.4 (01/11, phần kết quả cuối điền sau) và việc còn lại."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [aa-cis, aa-booking, tripplanner]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-997, AA-990, docs/audits/2026-10-28-S254-geocode-audit/README.md, docs/audits/2026-10-30-S260-aa997-interim/README.md]
---

# AA-997: báo cáo tổng về độ đúng toạ độ địa điểm (S254 → S261)

Phiên S261, 31/10/2026. Tác nhân: Claude Code. Issue: AA-997 "[Places] Geocode accuracy" (liên quan AA-990
`recheck_14`). Bản tư vấn cho tech lead, gom lại các audit S254, S257, S258, S260 và output S261.

Quy ước:

- Giờ có hậu tố `Z` là UTC, lấy từ dòng `JOB` của audit (đọc thẳng từ DB). Giờ `+07` là giờ VN, lấy từ log phiên
  hoặc thời điểm sửa file. Credit Geoapify reset lúc 00:00Z mỗi ngày.
- Mã job viết tắt 8 ký tự. Mọi số liệu S261 hiện chỉ có trong `.tmp-session/S261/aa997/` (chưa commit); các file
  đó được nêu ở §9.
- "Số đã chốt" là số lịch sử không đổi nữa. "Số giữa chừng" sẽ đổi sau chuỗi recheck 01/11 (§7).
- Toàn bộ việc geocode chạy trên gói Free của Geoapify và không gọi LLM: **chi phí $0** cho cả issue.

---

## 1. Tóm tắt

1. **Mục tiêu:** ≥ 90 % pin địa điểm đúng chỗ (Done-when trên Linear: mẫu mù mới ≥ 200 tên, chia theo provenance).
2. **Hiện tại (31/10 01:15Z, sau khi chuỗi v2 chạy xong):** cổng chấm lại mẫu 600 dòng S254 đạt **78,8 % ±4,0,
   FAIL**; nền S254 là 75,4 %. Dự phóng theo ô cho toàn bộ ~7.986 dòng: 81,3 %.
3. **Vì sao chưa đạt:** Geoapify chỉ xác nhận được 28,4 % số pin do LLM viết mà chuỗi v2 đã xử lý (602 / 2.120 pin;
   tính cả chuỗi aa997.1 thì 927 / 3.842 dòng = 24,1 %). Phần còn lại
   giữ điểm của model và chỉ bị gắn cờ (ô `rl_flagged` 2.697 dòng, đúng ~64 %). Cổng tính pin sai là sai kể cả khi
   đã gắn cờ hay ẩn.
4. **Đã sửa:** toạ độ chỉ lấy từ geocoder cho tên mới (CIS #1092), luật nhận chặt dần aa997.1 → aa997.4, bộ lọc
   non-place, HK/MO, chia credit theo ngày, chính sách ẩn `hide_flagged` có báo cáo + confirm, các đường đọc của
   CIS/Booking/TripPlanner không còn trả điểm `suspect` hay id đã gộp, 5 điểm regressed đã trả về điểm cũ.
5. **Còn lại:** chuỗi recheck aa997.4 cho 1.197 dòng aa997.1 (còn 1.024 dòng, chạy từ 01/11 00:11Z; sát trần 1.500
   credit/ngày nên có thể tràn sang 02/11, xem §7.1), audit cuối,
   quyết định `hide_flagged`, chặng "A to B", dòng mapbox, quyền đọc view catalog để đo pin phục vụ, mẫu mù mới.
6. **Nếu ẩn** các pin còn gắn cờ (`hide_flagged`) thì pin **phục vụ khách** lên 87,8 %, ẩn thêm non_place thì
   90,7 % ±4,3, đổi lại độ phủ giảm từ 65 % xuống ~48 % (khoảng 1.293 pin đang gắn tour biến khỏi bản đồ).
7. **Khuyến nghị:** sau audit cuối (khi chuỗi đóng, dự kiến 01/11, muộn nhất 02/11), đóng AA-997 dạng **Done-with-scope** (đạt mục tiêu chặn sai cho tên mới,
   không đạt 90 % trên dữ liệu cũ), confirm `hide_flagged` theo đề xuất đã duyệt, và mở follow-up có điều kiện
   "[Places] Reach 90%" cho phần dữ liệu cũ (§8).
8. Các ô `{{FINAL_*}}` (§3.1, §6, §7) điền số cuối sau khi chuỗi xong; §7.2 là bảng tổng.

---

## 2. Mục tiêu và cách đo

**Mục tiêu** (mô tả AA-997 trên Linear): một mẫu mù mới ≥ 200 tên đã resolve, chia theo provenance, đúng ≥ 90 %;
có số trước/sau cho bộ lọc non-place; chi phí geocoder nằm trong free tier.

Đến nay có bốn cách đo. Chúng trả lời bốn câu hỏi khác nhau:

| thước đo | nói đơn giản | pin sai đã gắn cờ / đã ẩn thì sao | vai trò |
|---|---|---|---|
| **Cổng flag-strat (`GATE`)** | Lấy lại đúng 600 dòng người kiểm đã chấm ở S254 (200 dòng ngẫu nhiên không cờ + 400 dòng có cờ rủi ro cao). So toạ độ **hôm nay** với điểm đúng S254 ghi (dung sai 4 km cho site, 5 km cho chỗ khác). Kết quả từng tầng nhân ngược về toàn bộ (5.603 dòng không cờ / 2.321 dòng có cờ). | **Vẫn sai.** Chỉ dời điểm vào đúng chỗ mới nâng được số này. | **Đây là cổng 90 %.** Tái tính S254 phải ra đúng 75,4 % thì phép chấm lại mới được tin. |
| prov-strat | Cùng 600 dòng, phân tầng theo nguồn toạ độ (`located_by` × cờ). | như trên | Kiểm chéo: lệch flag-strat dưới ~1 điểm. |
| Dự phóng theo ô (`L projection`) | Chia toàn bộ dòng resolved hôm nay vào các ô (geoapify, relocate confirmed, relocate gắn cờ, non_place, mapbox, llm chưa chạm), nhân tỉ lệ đúng của từng ô với số dòng. | như trên | Chỉ kiểm chéo. Ô ít mẫu (mapbox n = 9) sai số lớn. |
| **Pin phục vụ (`SERVED`)** | Chỉ tính pin mà app thật sự cho khách thấy (đã bỏ `suspect` và dòng gộp). Dòng ẩn ra khỏi mẫu số; non_place còn hiện thì tính là lỗi. Kèm độ phủ = tỉ lệ pin còn được phục vụ. | Dòng ẩn **ra khỏi mẫu số**, nên ẩn **có** nâng số này nhưng mất pin. | Đo tác dụng của `hide_flagged`, không thay cổng được. |
| Proxy (`R proxy`) | Không có nhãn. Chỉ xét các dòng chuỗi đã chạm: điểm có trong nước, gần route có neo, không phải trả lời bằng thành phố/quận, không dồn chung điểm. | — | Tín hiệu, **không phải độ đúng**. Hơn nửa số dòng không có route để chấm. |

Giới hạn cần nhớ khi đọc số:

- **Chưa có mẫu mù mới.** Mọi số dưới đây chấm lại mẫu 600 dòng S254, chưa đúng điều kiện Done-when.
- **Pin phục vụ đo bằng đường vòng.** Role `cis_app` không đọc được `catalog.v_tour_component` / `v_tour_stop` /
  `v_tour_place`, nên tập phục vụ được tính bằng `fallback_linked_rows`: 4.855 destination đang gắn tour, kể cả
  tour không live.
- Điểm "đúng" là phán định của người kiểm S254, không phải một geocoder thứ hai.

---

## 3. Dòng thời gian theo ngày

### 3.1 Bảng tổng

| ngày | phiên | việc chạy | số liệu | quyết định |
|---|---|---|---|---|
| 28/10 (sáng) | S254 | Audit chỉ đọc trên 9.545 tên `geo.place_name` (7.924 resolved, 1.203 pending, 418 unknown); mẫu 600 dòng (seed 254). | Đúng **75,4 %** (CI 71,2–79,6); Geoapify ~91 %, toạ độ LLM 53–60 %; 3.770 dòng LLM chứa ~1.400 / ~1.700 pin sai; 1.621 tên chưa resolve chia 14 nhóm. $0. | Tạo AA-997 (High), kế hoạch sửa 8 bước. |
| 28/10 07:06Z | S255 | Merge CIS #1092 `2076d583` (luật `aa997.1`), live api :879 / worker :445. Review 2 vòng (`a3defb63`, `94b04fb8`). | — | Toạ độ chỉ từ geocoder; job `place_relocate` dry_run/apply. |
| 28/10 07:19–07:43Z | S255 | Dry run `14fde6da` (07:19Z), `daf3542c` (07:35Z). Apply Laos `2b1fb176` (07:43Z). | Dry run mọi nước (comment S255 trên Linear, 12:33Z; không ghi mã job, nên là một trong hai dry run trên): 3.842 dòng, 3.607 request, ~3 ngày với 1.500 credit/ngày; 406 off-route, 200 non-place, 3 HK/MO. `2b1fb176` dừng ngay ở `stopped_credit_limit`, **0/302 dòng**, nối tiếp bằng `71781806`. | Laos chạy trước, mọi nước sau. |
| 28/10 14:30–14:32Z | S256 (bắt đầu 28/10 21:20 +07) | Dry run mọi nước `ce96dfa5` (14:30Z), apply mọi nước `445f9770` (14:32Z). | `ce96dfa5`: 3.842 dòng / 3.607 request / $0 (log S256). | Lệnh huỷ job Laos bị auto mode chặn → giữ nguyên, apply mọi nước xếp sau Laos. |
| 29/10 00:11–00:56Z | (tự chạy) | Chuỗi aa997.1: `71781806` (Laos, xong 00:17Z), `445f9770`, `15e57253`, `f1418889`, `63ecc2dc`. | Laos 302 dòng / 272 request; mọi nước 1.319 dòng / 1.228 request; `63ecc2dc` dừng credit sau 119 dòng, còn 2.221 dòng. | — |
| 29/10 (sáng) | S256 | Không code AA-997. DB Migrate apply migration 301 (AA-995, run 40791617873) cần override vì bảng job còn chuỗi `place_relocate` xếp hàng. | — | Tech lead duyệt override (chuỗi chỉ có job queued, chưa tới hạn). |
| 29/10 04:03Z | S257 | Audit giữa chừng 1 (luật aa997.1, 1.621/3.842 dòng). | **77,7 % ±4,1**; dòng chạm 57,8 → 64,3 %; `confirmed` chỉ 18/29; 3 regressed; dự phóng ~79,5 %; `recheck_14` route 13/16, all-confirmed 1/16. | Cần luật chặt hơn. |
| 29/10 06:31Z | S257 | Merge CIS #1139 `070dd7ba` (luật `aa997.2`, strategy v2, recheck, trần request, hide/unhide), live api :912 / worker :478. Mọi thứ mặc định TẮT. | Cổng P4: aa997.2 từ chối **34/251 dòng đúng (13,5 %)**, ngưỡng ≤ 2 % → **FAIL**. | aa997.2 giữ tắt, không apply. |
| 29/10 14:34Z | S258 | Merge CIS #1147 `24fda208` (luật `aa997.3`, preset từ sweep `9b1365c0`); root #340. | P4: **3/251 (1,2 %) PASS**, bắt 4/30 dòng sai (mất Huashan). | — |
| 29/10 17:48Z | S258 | Census dry run `08132f64` (aa997.3) và `78ad0797` (aa997.2) trên 3.842 dòng Geoapify gốc. | aa997.3 từ chối 33 (0,9 %); aa997.2 từ chối 259 (6,7 %). | — |
| 30/10 00:13Z | (tự chạy) | `767ed487` (job aa997.1 còn xếp hàng). | `refused_rule_version_changed`: 0 request, 0 ghi. | Đúng thiết kế. |
| 30/10 (sáng) | S259 | Đọc tay 33 dòng aa997.3 từ chối. Dry run v2 `5f570b90` (01:54Z). Chuỗi v2 ngày 1: `d1c6446d`, `3b7c7fd8`, `0286393a` (dừng credit 02:20Z). | 6 từ chối đúng, 21 sai, 6 lưng chừng. Dry run 2.221 dòng / 3.018 request. Ngày 1: 830 dòng theo bộ đếm job (1.216 theo dấu), 1.019 request, 0 lỗi. | Dùng aa997.3 + v2 cho dòng `llm` chưa chạm; **không** recheck `confirmed`; 2 sân bay để sửa tay. Một deploy CIS rơi vào lúc job chạy → nhả và nhận lại, không mất, không trùng. |
| 30/10 08:25Z | S260 | Audit giữa chừng 2. | **78,4 % ±4,0**; dự phóng 80,0 %; 9 regressed (6 trong v2); `recheck_14` 13/16, 0/16 (loose 3/16). | — |
| 30/10 09:53–12:25Z | S260 | Merge CIS #1178 `b1dbfca0` (09:53Z; `hide_flagged`/`unhide`, 3 vòng review), live api :929 / worker :495. Merge CIS #1185 `2b5b3712` (12:10Z), Booking #160 `636df62c` (12:17Z), TripPlanner #195 `26c2c976` (12:25Z). | Audit lần 2 10:08Z (sau deploy #1178, có mục `SERVED`). Báo cáo hide `31b5617a` (10:08Z): 2.017 ứng viên, 1.015 đang gắn tour. Confirm nhận **409** đúng thiết kế (chuỗi còn mở). Pin phục vụ 80,6 % → 86,6 % nếu ẩn → 88,7 % nếu ẩn thêm non_place. | Bật ẩn là việc của tech lead; S260 chưa ẩn dòng nào. |
| 31/10 00:20–00:34Z | (tự chạy) | Chuỗi v2 ngày 2: `dac718c6`, `730e5ee9`, `629c3774` (ok, `remaining 0`). | 1.005 dòng, 1.242 request. Chuỗi v2 đóng: 2.221 dòng theo dấu (602 confirmed). | — |
| 31/10 01:15Z | S261 | Audit cuối chuỗi v2 (chỉ đọc). | **78,8 % ±4,0, FAIL**; dự phóng 81,3 %; 6 regressed trong v2; pin phục vụ 80,6 % → 87,8 % → 90,7 %; `recheck_14` 13/16, 0/16, loose 3/16. | — |
| 31/10 ~01:16Z | S261 | Dry run recheck aa997.3 `229a6def`. | 1.197 dòng (llm_point 1.004 + off_route 193 của aa997.1), 1.648 request. | — |
| 31/10 01:54Z | S261 | Merge CIS #1193 `1b6e9448` (luật `aa997.4`), live api :940 / worker :506. | — | Thêm guard bằng chứng trong ngày để chặn dời sang POI trùng tên. |
| 31/10 ~02:07–02:43Z | S261 | Dry run aa997.4 `8fa953f3`; trial `32ace765` → `6086f577`; trả 5 điểm regressed về điểm cũ; chuỗi đầy đủ `b0190743`. | Dry run khớp aa997.3 (1.197 / 1.648). Trial 98 dòng (50 dòng đầu: confirmed 6, `kept_model` 0, 76 request). `b0190743`: 75 dòng, confirmed 15, 108 request, dừng credit; còn **1.024 dòng**, `dc260ef8` chạy 01/11 00:11Z. | `hide_flagged` coi như đã duyệt theo đề xuất. Kế hoạch: audit cuối sáng 01/11 → Done-with-scope + follow-up. AA-990 đóng Done-with-scope; `recheck_14` theo AA-997. |
| 01/11 từ 00:11Z | (tự chạy) | Chuỗi recheck aa997.4 tiếp tục (`dc260ef8` và các job nối tiếp). | Xem §7. `{{FINAL_TIMELINE_0111}}` | `{{FINAL_DECISION_0111}}` |
| 02/11 (nếu tràn) | (tự chạy) | Phần còn lại của chuỗi nếu 01/11 hết credit. | `{{FINAL_TIMELINE_0211}}` (xoá dòng nếu chuỗi đóng trong 01/11) | — |
| sau khi chuỗi đóng | S262? | Audit cuối (`audit_relocated.py`, `recheck_14.py`), báo cáo + confirm `hide_flagged`, comment Linear. | `{{FINAL_AUDIT_AT}}` | `{{FINAL_CLOSE_DECISION}}` |

### 3.2 Các chuỗi `place_relocate`

| chuỗi | luật / strategy | job apply (theo thứ tự) | dòng xong | confirmed / llm_point / off_route / non_place | request | chi phí |
|---|---|---|---|---|---|---|
| aa997.1, Laos | v1 / v1 | `2b1fb176` (0 dòng, credit) → `71781806` | 302 | 67 / 183 / 28 / 24 | 272 | $0 |
| aa997.1, mọi nước | v1 / v1 | `445f9770` → `15e57253` → `f1418889` → `63ecc2dc` (credit) → `767ed487` (`refused_rule_version_changed`) | 1.319 | 258 / 821 / 165 / 75 | 1.228 | $0 |
| **Cộng aa997.1** | | | **1.621** | **325 / 1.004 / 193 / 99** (+3 dòng đổi nước HK/MO) | **1.500** | $0 |
| v2, dòng `llm` chưa chạm | accept aa997.3, strategy v2, `RULE_VERSION` aa997.2 | `d1c6446d` → `3b7c7fd8` → `0286393a` (credit) → `dac718c6` → `730e5ee9` → `629c3774` | 2.221 theo dấu (1.835 theo bộ đếm job) | 602 / 1.443 / 75 / 101 theo dấu (488 confirmed theo bộ đếm) | 2.261 theo bộ đếm (thật cao hơn) | $0 |
| Recheck aa997.1, trial | accept aa997.4, v2, limit 50, trần 150 request | `32ace765` → `6086f577` | 98 | `32ace765`: 6 / 23 / 21 / 0, `kept_model` 0 | 76 (`32ace765`) | $0 |
| Recheck aa997.1, đầy đủ | accept aa997.4, v2, 400 dòng/lượt | `b0190743` (credit) → `dc260ef8` (01/11) → … | 75 (tới 31/10) | 15 / 44 / 16 / 0, `kept_model` 0 | 108 | $0 |

Cộng mọi lượt relocate trên dòng `llm` (aa997.1 + v2): **3.842 dòng**, confirmed 927 (24,1 %), llm_point 2.447,
off_route 268, non_place 200. Khớp với số ứng viên ẩn và `review_reason` của audit S261.

---

## 4. Các luật đã áp dụng

### 4.1 Phiên bản theo thời gian

| ngày (UTC) | phiên | PR / commit | luật mới |
|---|---|---|---|
| 28/10 | S254 | audit `docs/audits/2026-10-28-S254-geocode-audit/` | Chưa có luật code; kế hoạch sửa 8 bước. |
| 28/10 07:06 | S255 | CIS #1092 `2076d583` | `RULE_VERSION aa997.1`; accept `v1` + route guard + day-trip; lọc non-place; HK/MO; đọc nước lỏng; job `place_relocate`; switch `hide_unconfirmed`; credit guard. |
| 29/10 06:31 | S257 | CIS #1139 `070dd7ba` | `RULE_VERSION aa997.2`; accept `aa997.2` (có switch); strategy `v2`; `recheck`; trần request theo chuỗi; `hide`/`unhide`; outcome `weak_confirm`, `kept`, `kept_unjudged`, `reconfirmed`. |
| 29/10 14:34 | S258 | CIS #1147 `24fda208` (preset `9b1365c0`); root #340 | Accept `aa997.3` (`StrictParams`: route có neo, re-judge off-route 500 km…). |
| 30/10 09:53 | S260 | CIS #1178 `b1dbfca0` | Mode `hide_flagged` (stamp `aa997.3-flagged`); restore theo id thì dính; tự hiện lại khi geocoder xác nhận. |
| 30/10 12:10–12:25 | S260 | CIS #1185, Booking #160, TripPlanner #195 | Luật đọc: điểm `suspect` không phục vụ, id gộp bị từ chối hoặc redirect. |
| 31/10 01:54 | S261 | CIS #1193 `1b6e9448` | Accept `aa997.4` (guard bằng chứng trong ngày), outcome `kept_model`, lý do `same_name_elsewhere`. |

### 4.2 RULE_VERSION (dấu relocate) khác accept rule

| dấu | làm gì | ghi chú |
|---|---|---|
| `aa997.1` | Mỗi dòng relocate đã xử lý được đóng dấu `geocoder_meta.relocate = {v, outcome, at, moved_km?}`. Lần chạy sau bỏ qua dòng đã có dấu cùng version. | 1.621 dòng mang dấu này. |
| `aa997.2` | Dòng mang dấu cũ chỉ được lấy lại khi outcome nằm trong `recheck`. Job còn xếp hàng của chuỗi trước tự từ chối (`refused_rule_version_changed`). | Giữ nguyên tới nay (`relocate.py:94`). |
| (không có aa997.3 / aa997.4) | aa997.3 và aa997.4 chỉ là **accept rule**: một lựa chọn trong payload, ghi vào stamp (`accept_rule`) và `geocoder_meta.rule`. | Tăng version sẽ làm mọi chuỗi đang xếp dưới aa997.2 bị từ chối. Hệ quả: dòng đã đóng dấu bởi một apply aa997.2 không được run aa997.3 lấy lại. |

Hai bẫy: `hide_unconfirmed` chỉ chọn được một lần cho mỗi RULE_VERSION (vì vậy mới cần `hide_flagged`); stamp
`hidden.by` (`aa997.2-policy`, `aa997.3-flagged`) là tên **chính sách ẩn**, không phải tên accept rule.

### 4.3 Accept rule: khi nào nhận một đáp án của Geoapify

| luật | nói đơn giản | sinh ra để sửa | kết quả đo / trạng thái |
|---|---|---|---|
| **`v1`** (#1092, mặc định) | Xét top 3 ứng viên. Đúng nước (CN gồm HK/MO). Tên khớp (sim ≥ 0,999, hoặc ≥ 0,5 khi ≥ 2 token). Loại type country/state/county/postcode, loại `city` khi tên không phải thị trấn. Có route thì route quyết (≤ 50 km site, ≤ 100 km địa vật dài); không route thì cách điểm model ≤ 25 km; không cả hai thì `no_reference`. `day_trip` là lựa chọn thứ hai (lệch route nhưng ≤ 150 km và khớp điểm model). | Toạ độ LLM chỉ đúng 53–60 %; homonym kiểu Bell Tower Xi'an ghim ở Bắc Kinh; bán kính 50 km cứng làm rớt Ayutthaya, Mutianyu. | Vẫn là luật cho **tên mới** (env `GEOCODER_ACCEPT_RULE` mặc định `v1`, không thấy đổi trong Infra). |
| **`aa997.2`** (#1139, tắt) | v1 + lý do từ chối chặt: `site_type` (site mà đáp án là suburb/district/city), `match` (Geoapify trả fallback theo thành phố), `kind` (POI khác loại có chứa tên: khách sạn, quán, đường), `ambiguous_route` (> 300 km so với > 1/5 số route), `hint_disagree` (điểm model nằm trên route mà ứng viên ở ngoài thì chỉ tên khớp chính xác mới thắng). Check thiếu dữ liệu thì "unjudged", không từ chối. | `confirmed` của aa997.1 chỉ đúng 18/29; đọc code thấy 6 lỗ (§5, P2). | P4 **FAIL** 34/251 (13,5 %); census từ chối 259 (6,7 %). Chưa bao giờ dùng cho apply. |
| **`aa997.3`** (#1147) | aa997.2 + `anchored_only` (chỉ tin route khi **ngày đó có điểm ngủ riêng** đã định vị), `rejudge_off_route_km = 500`, `rejudge_v1_checks = False`, `site_admin_named` ("Horombo Hut" được map là locality vẫn qua). | 27/34 lần từ chối sai (off_route 17 + ambiguous_route 10) vì route thiếu điểm ngủ của chính ngày đó (ngày đến/đi, bay/tàu đêm, đêm trek, hoặc chính là điểm ngủ) → `anchored_only` + re-judge 500 km; site_type 4 (Horombo Hut) → `site_admin_named`; name 3 → re-judge không chấm lại check tên của v1. | P4 **PASS** 3/251 (1,2 %); census 33 (0,9 %); đọc tay 21/33 từ chối sai → không recheck `confirmed`. Dùng cho chuỗi v2. |
| **`aa997.4`** (#1193) | aa997.3 + `day_guard`. Dời ≤ 2 km thì không xét. **Luật 1:** các địa điểm khác cùng ngày (đã được geocoder định vị) nằm gần điểm model (≤ 3 km) và điểm model rõ ràng gần hơn ứng viên (≤ ½ khoảng cách, gần hơn ≥ 1,5 km) → từ chối; ngược lại chúng gần ứng viên → nhận ngay. Riêng **dời gần** (trong bán kính bake-off) thì miễn xét nếu điểm model trùng thị trấn ngủ (≤ 0,5 km), chép điểm của địa điểm khác (≤ 0,3 km) hoặc < 2 điểm hỗ trợ; dời xa không có miễn trừ này. **Luật 2:** điểm model ≤ 15 km từ điểm ngủ của chính ngày, ứng viên ở xa và gần một điểm ngủ KHÁC → từ chối. Lý do `day_disagree` (dời xa) và `day_disagree_near` (dời gần). | aa997.3 dời 6 dòng S254 chấm đúng sang một địa vật trùng tên (đền ở thị trấn ngủ kế tiếp ~142 km, đền gần thành phố gốc ~118 km, pháo đài / gurudwara cùng thành phố 4–5 km). | Đang chạy recheck 1.197 dòng aa997.1. Ngưỡng đặt từ 4 hình mẫu đã audit, **chưa sweep** trên mẫu có nhãn. |

Switch: cho relocate là payload `accept_rule` (`^(v1|aa997\.[234])$`); cho tên mới là env `GEOCODER_ACCEPT_RULE`
(mặc định `v1`). Mọi đáp án được nhận đều ghi `geocoder_meta.rule` và `geocoder_meta.hint`. Lần từ chối strict cuối
ghi `last_error = 'unconfirmed_by_geocoder:strict=<reasons>'`, không retry (gọi lại chỉ tốn credit).

> ⚠️ `GEOCODER_ACCEPT_RULE` và `GEOCODER_STRATEGY` có dấu gạch dưới: đổi bằng tay trong task definition / Terraform,
> không sinh script tự động.

### 4.4 Strategy tìm kiếm

| strategy | làm gì | vì sao |
|---|---|---|
| `v1` (mặc định) | Một truy vấn: tên chuẩn hoá trong nước của model (1–2 request). Bias = điểm giữa route ĐẦU TIÊN, hoặc không bias. | Hành vi gốc (#1092). |
| `v2` (#1139) | Tối đa 3 request: (1) ngữ cảnh riêng "X in/at/near Y" trước rồi X trơn; tên chung kiểu "Great Wall at Mutianyu" tìm cả tên rồi "Mutianyu Great Wall"; (2) phần trong ngoặc là bí danh ("Hawa Mahal"); (3) ngữ cảnh phải có từ riêng; (4) cuối cùng là thị trấn ngủ của ngày. Bias = điểm model khi không có route hoặc khi điểm đó nằm trên route. `name_sim_v2` so tên dạng gộp (Konglor = Kong Lor), bỏ `mt`/`mount`/`in`/`at`/`near`. | `llm_point` chiếm 62 % outcome aa997.1: thiếu bias khi không route, một truy vấn, phiên âm gộp/tách, "Mt". |

Chuỗi S259–S261 chạy `strategy v2`; tên mới vẫn `v1` (env `GEOCODER_STRATEGY` mặc định). Mapbox làm geocoder thứ hai
**không** triển khai: kết quả Temporary không được lưu, Permanent phải trả tiền và cấm hiển thị trên bản đồ công khai.

### 4.5 Outcome của relocate (`geocoder_meta.relocate.outcome`)

| outcome | nghĩa | điểm trên bản đồ |
|---|---|---|
| `confirmed` | Geocoder xác nhận, điểm được viết lại; stamp giữ `prev` để hoàn tác. | Điểm geocoder |
| `llm_point` | Không đáp án nào qua; giữ điểm model, `review_reason llm_point`. | Model (gắn cờ, ẩn được) |
| `off_route` | Như trên, điểm model nằm xa mọi route của các tour dùng nó. | Model (gắn cờ, ẩn được) |
| `non_place` | Bộ lọc coi là không phải địa điểm, không gọi geocoder. | Giữ nguyên (ẩn chỉ khi opt-in) |
| `country_fixed` | Cờ phụ: CN → Hong Kong / Macao theo polygon. | — |
| `skipped` | Admin đã sửa, dòng đã gộp, hoặc `located_by` đổi sau khi chọn. Đọc lại dưới lock, không ghi. | Không đổi |
| `kept` / `kept_unjudged` | Re-judge đáp án Geoapify đã lưu bằng luật strict (không tốn gọi): qua hết / qua nhưng có check không xét được. | Không đổi |
| `reconfirmed` | Re-judge từ chối, tìm lại có đáp án qua và nằm trong trần dời. | Điểm mới |
| `weak_confirm` | Re-judge từ chối, không tìm lại được hoặc dời quá trần; ghi `move_refused_km`. | Gắn cờ, ẩn được |
| `kept_model` | aa997.4 từ chối một lần dời XA (`day_disagree`), giữ điểm model. Không thuộc `HIDE_FLAGGED_OUTCOMES`. Chỉ khi cờ cũ là cờ do relocate tạo (không cờ / llm_point / off_route / weak_confirm) thì lý do đổi thành `same_name_elsewhere` (không thuộc `HIDE_REASONS`) và dòng đang bị chính sách ẩn sẽ hiện lại; cờ khác (`unconfirmed_hard_type`, `centroid_fallback`, `non_place:*`…) giữ nguyên. Từ chối **gần** (`day_disagree_near`) không thành `kept_model`: dòng giữ cờ llm_point / off_route, ẩn được. | Model (hiện, có trong danh sách review) |

### 4.6 Guard

| guard | làm gì | vì sao |
|---|---|---|
| Toạ độ chỉ từ geocoder | Model chỉ đưa tên, nước, thị trấn. (a) tìm tên → nhận thì lấy điểm; (b) tìm thị trấn model nêu → điểm thị trấn, `geo_precision='area'`, `centroid_fallback`; (c) không có → `unconfirmed_by_geocoder` là kết quả cuối. | Kế hoạch S254 bước 1, 5, 6. |
| Route coherence | Khoảng cách tới polyline nối điểm ngủ đáng tin của ngày d−1..d+1 của mọi tour dùng tên. Ngưỡng 50 / 100 / 150 km (day-trip). | Thay luật `tour_spread` (precision 23 %). |
| Route có neo (aa997.3), `own`/`day` (aa997.4) | Route chỉ là bằng chứng khi ngày có điểm ngủ riêng; aa997.4 thêm điểm ngủ của chính ngày và các địa điểm khác của ngày. | §4.3. |
| Polygon nước | Điểm phải nằm trong bbox VÀ polygon nước (đệm 10 km). | Có từ AA-990 (Kilimanjaro thành Kenya, Siem Reap thành Thái Lan). |
| Hong Kong / Macao | Tìm "China" lọc `countrycode:cn,hk,mo`; `same_country` coi HK/MO thuộc CN; `refine_country` lưu thành HK/MO theo polygon. | S254: cả 13 dòng HK và 7 dòng MO bị lưu thành CN. |
| Đọc nước lỏng | "Tibet, China" → China; "India and Pakistan" giữ unknown. | Kế hoạch bước 6. |
| Lọc non-place | Trước mọi gọi trả phí; 7 nhóm: `route_segment`, `lodging`, `activity`, `region`, `generic_kind`, `descriptive`, `annotation_only`. Kết quả `unknown` + `last_error non_place:<cause>`, không thêm status mới. | Trên nhãn S254: bỏ nhầm 3/439 tên đúng, bắt 25/28 non-place, 195/222 chặng. |
| Đọc lại dưới lock | Admin sửa / dedupe / đổi `located_by` trong lúc chạy → `skipped`. Thị trấn ngủ xử lý trước để làm neo. | Review #1092. |
| Trần dời khi reconfirm | Đáp án re-search cách điểm đang lưu hơn `route_radius` → không ghi, `weak_confirm`. | Review vòng 2 #1139. |
| Credit theo ngày | Relocate dùng 2.500 − 1.000 dự trữ = **1.500 credit/ngày**; hết → `stopped_credit_limit`, xếp lại lúc reset UTC. Không còn phần → `refused_no_credit_share`. `BudgetExceeded` → `stopped_budget`. | Để dành credit cho `place_geocode` xử lý tên mới. |
| Trần request theo chuỗi | `max_requests` + `chain_id`, đếm từ `geo.geocode_call`; hết → `stopped_request_cap`. | #1139. |
| Không deploy khi chuỗi chạy | `place_relocate` ghi `shared.destinations` nên áp DM-11.4; guard AA-993 nhả và nhận lại job khi deploy. | Đã kiểm thật ở S259. |

### 4.7 Chính sách ẩn

| chính sách | làm gì | trạng thái |
|---|---|---|
| `hide_unconfirmed` (switch của apply) | Dòng không xác nhận được bị đặt `suspect` lúc apply. Chọn được một lần mỗi RULE_VERSION. | Chưa bật trong chuỗi nào. |
| `hide` / `unhide` theo lý do (`aa997.2-policy`) | Ẩn dòng còn mang llm_point, off_route, unconfirmed_hard_type, weak_confirm (non_place khi opt-in). | Chưa confirm lần nào. Chọn theo `review_reason` nên lấy cả dòng `unconfirmed_hard_type` chưa qua relocate (S260: 626 dòng có lý do này, chỉ 431 trong tập `hide_flagged`), nên không dùng. Tới S261 cả 577 dòng `unconfirmed_hard_type` đều nằm trong tập `hide_flagged`. |
| **`hide_flagged`** (`aa997.3-flagged`) | Chỉ ẩn dòng relocate ĐÃ xử lý và còn để trên điểm model (llm_point / off_route; `weak_confirm` khi opt-in), đúng `located_by`, `geo_status ok`. Bước 1 báo cáo (ids + digest), bước 2 confirm gắn đúng báo cáo đó: < 6 h, cùng selection, không apply nào đang mở, digest không đổi. Ẩn theo lô 100, mỗi lô một dòng `acp_shared.audit_log`. | Báo cáo `31b5617a` (S260); confirm 409 đúng thiết kế. **Chưa confirm.** Đề xuất đã được duyệt trong S261. |
| `unhide` theo stamp / restore theo id | Theo stamp: không dính, lượt ẩn sau có thể ẩn lại. Theo id (≤ 500): **dính**, các lượt ẩn sau bỏ qua cho tới khi relocate chấm lại dòng. | #1178. |
| Tự hiện khi geocoder xác nhận | `confirmed`/`reconfirmed` trên dòng bị ẩn bởi chính sách → về `ok`, `resolved`. Recheck đổi lý do thì stamp ẩn chuyển theo. | #1178. |
| Luật đọc | CIS: suspect trả 200 với lat/lng null, gộp trả 404. TripPlanner: gộp 301, suspect `location_hidden`. Booking: `hidden_from_customers`, picker bỏ dòng gộp. | #1185, Booking #160, TripPlanner #195. |

### 4.8 Chế độ chạy và recheck

| mode | làm gì |
|---|---|
| `dry_run` | Không gọi, không ghi; đếm non-place, on/off route, HK/MO; ước request (cận trên). **Không cho thấy tác dụng của aa997.4** vì guard chỉ chạy khi có đáp án geocoder. |
| `apply` | 409 nếu chưa có dry run cùng selection; ≤ 400 dòng/lượt, tự xếp lượt tiếp; dùng lại apply đang mở. |
| `recheck` ∈ `llm_point`, `off_route`, `confirmed`, `geoapify` | Lấy lại dòng version cũ. `confirmed`/`geoapify` cần luật strict; `geoapify` chỉ dry run. |
| `limit`, `max_requests`, `chain_id` | Chạy thử và giới hạn chi phí cho cả chuỗi. |

---

## 5. Lỗi và vấn đề phát hiện được

| # | triệu chứng | nguyên nhân gốc | cách sửa | PR / commit | trạng thái 31/10 |
|---|---|---|---|---|---|
| P1 | Pin đúng chỉ 75,4 %; toạ độ LLM đúng 53–60 %, Geoapify ~91 %. Lệch 5–100 km (45 dòng), tâm thị trấn thay cho site (44), non-place (28), trùng tên khác thành phố (20), HK/MO (4). | Pipeline lưu toạ độ do model tự viết; cờ audit gần như không tách đúng/sai (19 % lỗi ở nhóm không cờ so với 26 % nhóm cờ cao). | Toạ độ chỉ từ geocoder; chuỗi `place_relocate` xử lý dữ liệu cũ. | CIS #1092 `2076d583`; chuỗi aa997.1, v2, aa997.4 | **Một phần**: 78,8 %, chưa đạt 90 %. Chuỗi chỉ xác nhận ~28 % pin. |
| P2 | `confirmed` của aa997.1 chỉ đúng 18/29 (~62 %). | Bán kính route 50/100 km rộng gấp ~10 lần dung sai site; "gần BẤT KỲ route nào" của mọi tour dùng tên; nhận suburb/district/city cho site; không đọc `match_type`; so tên một chiều; bỏ điểm model khi có route. Phía recall: không bias khi thiếu route, một truy vấn, phiên âm, "Mt". | Luật chặt aa997.2 + strategy v2. | CIS #1139 `070dd7ba` | Code đã ship; aa997.2 thay bằng aa997.3 vì trượt P4. |
| P3 | aa997.2 từ chối 34/251 dòng đúng (off_route 17, ambiguous_route 10, site_type 4, name 3): Delhi Airport, Pingyao, Hong Kong, Mount Kailash… | Route dựng từ điểm ngủ d−1..d+1; ngày không có điểm ngủ riêng (đi/đến, bay/tàu đêm, lều trek, chính là điểm ngủ) thì route chỉ đo quãng di chuyển. | `anchored_only`, re-judge 500 km, `site_admin_named`. | CIS #1147 `24fda208`, `9b1365c0`; root #340 | Đã sửa cho lần chấm mới (P4 1,2 %). Vẫn 21/33 từ chối sai khi đọc tay → không recheck `confirmed`. Còn 28 dòng `reject_unanchored`. |
| P4 | Dòng S254 đúng bị dời sai (regressed): 3 (S257), 9 (S260), 6 trong v2 ở S261: Sheeshganj Gurudwara ×2, Janaki Temple, Meherangarh/Meharangadh Fort ×2, Chaturbhuj Temple. | Tên khớp chính xác thắng điểm model đang nằm trên route; route và điểm model không phân biệt được hai địa điểm cùng tên trên cùng hành trình. | Luật aa997.4 (guard bằng chứng trong ngày); trả 5 điểm về `relocate.prev` (`located_by='manual'`, `geocoder_meta.reverted`, 1 dòng audit_log). | CIS #1193 `1b6e9448`; `revert_regressed.py` | Luật live. Revert 5 điểm (chỉ có trong checklist). Dòng "sheeshganj gurudwara sikh temple" không có trong script revert: **cần kiểm**. Đã biết mất case A (sửa gần phố cổ → cung điện ngoài thị trấn bị từ chối). |
| P5 | Site được trả lời bằng thành phố/quận: Urumqi Airport → Ürümqi, Angkor Thom → trung tâm Siem Reap; 2 sân bay ghim tâm thành phố; S261 có các dòng WATCH (Guryong Valley → Guryong-ri, Samal Island → district). | v1 chỉ loại country/state/county/postcode và `city` cho tên kiểu feature. | `site_type`, `match` (aa997.2), `site_admin_named` (aa997.3). | #1139, #1147 | **Một phần**: 2 sân bay (Hà Nội lệch ~25 km, Urumqi ~15 km; đọc tay S259) chờ sửa tay (chưa có endpoint sửa điểm có audit); 30 dòng WATCH S261 chưa đọc từng dòng. |
| P6 | Nhiều tên dồn chung một điểm (`dup_coords` 927 dòng, lỗi 28,6 %); 4 tên ở Irkutsk cùng điểm thành phố; Pisang → Pisang Peak. | Model/geocoder trả cùng một tâm khu vực; luật audit không phân biệt tên thị trấn với tên site. | Kế hoạch bước 5 (site-type trên điểm chung ≥ 3 tên) chưa làm. | — | **Còn mở**. |
| P7 | 13 dòng HK và 7 dòng MO lưu thành CN. | Không xử lý HK/MO riêng. | `refine_country`, `same_country`, lọc `countrycode:cn,hk,mo`. | #1092 | **Đã sửa** (3 dòng `country_fixed`). |
| P8 | ~300 pin là non-place (chặng, khách sạn, hoạt động, người); ~½ tên unresolved là rác trích xuất. | Không có bộ lọc trước khi geocode. | `name_filter.py`; từ chỉ nước chỉ tính ở chữ thường ("Ocean Park" giữ). | #1092 | Lọc đã sửa (101 dòng v2 gắn non_place, đúng 13/13). Còn **74 pin non_place đang phục vụ**; ẩn non_place chưa quyết. |
| P9 | `recheck_14`: 35/60 địa điểm chưa xác nhận (S261) là `unlinked` (tên chưa resolve); all-confirmed 0/16. Đếm trong `r14-out.txt`: chặng "A to B" chỉ **6**, cụm mô tả / chung chung **13** ("the office" ×4, "a coffee shop", "local home-stay", "remote village"…), tên thật chưa resolve **16** (Ban Mae Khi, Musunun Beach, Masuya Meat Shop, Roadside Station Oze Katashina…). | Chặng: `name_filter` chỉ gắn `non_place:route_segment`; tách chặng thành hai đầu mút đổi component id mà TripPlanner đang pin. Cụm mô tả: rác trích xuất (non-place đúng). Tên thật: `place_geocode` chưa tìm được. | Chưa sửa. | — | **Còn mở**. |
| P10 | Đường đọc vẫn trả điểm `suspect` hoặc id đã gộp (TripPlanner destination detail, Booking geo + picker, CIS `GET /catalog/v1/destinations/{id}`) → ẩn không có tác dụng. | Các reader không lọc `geo_status` / `duplicate_of`. | suspect → lat/lng null hoặc `location_hidden`; gộp → 404 / 301; Booking `hidden_from_customers`. | CIS #1185 `2b5b3712`, Booking #160 `636df62c`, TripPlanner #195 `26c2c976` | **Đã sửa**. |
| P11 | 210 dòng mapbox (S254, đúng 8/9; 289 dòng `located_by mapbox` ở S257/S261) không nằm trong chuỗi. | Chuỗi chạy `located_by=['llm']` theo quyết định; Mapbox Temporary không được lưu. Review #1178 tìm ra `hide_flagged` bỏ qua `located_by` → đã sửa, mặc định chỉ `llm`. | — | #1178 (phần `located_by`) | **Chấp nhận / còn mở** (6 điểm mapbox trong `recheck_14`). Lệch 210 / 289 chưa rõ nguyên nhân. |
| P12 | Không đo đúng "pin phục vụ": `InsufficientPrivilegeError` trên 3 view catalog. | `cis_app` không có SELECT trên `v_tour_component`/`v_tour_stop`/`v_tour_place`. | Tạm dùng `fallback_linked_rows`. | — | **Còn mở**. |
| P13 | Apply Laos `2b1fb176` dừng 0/302; chuỗi có thể tự xếp lại mãi; apply thứ hai tạo chuỗi mới; `BudgetExceeded` đếm như lỗi dòng. | Credit ngày bị `place_geocode` dùng hết; thiếu guard. Lệnh huỷ job Laos đang xếp hàng (S256) bị auto mode chặn nên nó chạy tiếp 29/10 00:11Z. | Chia credit 1.500/ngày; re-raise `BudgetExceeded`; dùng lại apply đang mở; `refused_no_credit_share`; trần request theo chuỗi. | #1092 `94b04fb8`; #1139 | **Đã sửa**. Chuỗi aa997.4 còn 1.024 dòng. |
| P14 | Chuỗi aa997.1 bị từ chối khi luật đổi; deploy/migrate trong lúc chuỗi chạy; confirm hide 409. | Có chủ đích: payload cũ không có `rule_version`; DM-11.4. | `refused_rule_version_changed`; guard AA-993; override migrate 301 do tech lead duyệt. | #1139; AA-993 | **Đúng thiết kế**. Bài học "xếp migration vào khoảng rảnh giữa các chuỗi" đã ghi. |
| P15 | Lỗi review trên các PR. | #1092: bán kính cứng rớt day-trip; vòng 2 có 4 should-fix (re-raise `BudgetExceeded`, apply thứ hai dùng lại apply đang mở, giữ `linear_feature`, từ chối khi hết phần credit). #1139: 7 phát hiện (luật chặt bật luôn, `ambiguous_route` 50 km, query plan v2 không gửi gì cho "Great Wall at Mutianyu", alias hỏng…). #1178: adversarial tìm 4 lỗi lớn (confirm chỉ so số dòng, bỏ `located_by`, unhide hàng loạt thành dính, `hide` không audit). #1193: từ chối gần là bằng chứng yếu; `kept_model` chỉ đổi nhãn cờ do relocate tạo. | Sửa trước merge. | các PR trên | Đã sửa, trừ **3 lỗi nhỏ #1178 còn mở**: unhide trả mọi `suspect` về `resolved`; reveal / đổi lý do hide không có audit_log; `_HIDE_FLAGGED_ROW_SQL` không kiểm lại `relocate.v`/accept/country. |
| P16 | Mục nhỏ kế hoạch S254 chưa làm. | — | `name_norm` bỏ "An" ở đầu (25 dòng, An Binh Island lệch 35 km); polygon ven biển cho đảo; backfill provenance (506 dòng `provenance_null`); ghim tay 113 dòng sai, bảng alias; lỗi nước của tour nguồn chuyển cho chủ Excel. | — | **Còn mở**. |
| P17 | Lỗi công cụ đo. | Dump làm tròn 6 chữ số còn DB 7 (so `==` báo lệch 130/281); script ECS exec > ~15 phút không trả output; `KeyError: slice` khi in samples; subagent không chạy được ECS exec. | Dung sai 1e-5; chia đoạn / chạy thành job; ghi bài học. | — | Đã xử lý / ghi bài học. |

### 5.1 Chỗ lệch giữa các nguồn

1. Comment S255 trên Linear viết "Applied: Laos first (302 rows, job 2b1fb176)". Thực tế `2b1fb176` làm 0 dòng; 302
   dòng Laos do `71781806` làm lúc 29/10 00:17Z.
2. Chuỗi v2: bộ đếm job ra 1.835 done / 488 confirmed / 2.261 request; dấu trên bảng ra 2.221 dòng / 602 confirmed.
   `d1c6446d` báo `done` 400 nhưng `remaining` 1.435 = 2.221 − 400 − 386. Suy luận (chưa kiểm): lần ghi đầu đã đóng
   dấu 386 dòng, khi job bị nhả lúc deploy rồi chạy lại thì bộ đếm của lần đó mất. Không mất dòng nào, nhưng số
   request thật ngày 30/10 cao hơn 1.019.
3. Không có file output của `revert_regressed.py` với `DRY=0`; số 5 chỉ có trong checklist S261, và checklist còn ghi
   "6 dòng regressed cũ cần khôi phục (follow-up)".
4. Không có file kết quả của `6086f577` (chỉ có "98 dòng" trong checklist).
5. Chưa thấy output cổng replay `replay_day_guard.py` (điều kiện "GATE PASS ≤ 2" trước apply aa997.4).
6. Linear AA-997 chưa có comment S261 (mới nhất là S260), trạng thái In Progress.
7. S258 README §3 ghi `rejudge_off_route_km 300`, code và preset cuối là 500.
8. Comment S255 trên Linear (12:33Z 28/10) đã có số dry run mọi nước (3.842 / 3.607 / 406 / 200 / 3), trước
   `ce96dfa5` (14:30Z, S256). Dry run của S255 là `14fde6da` hoặc `daf3542c`; output audit không cho biết cái nào.
9. File `docs/audits/2026-10-30-S258-session-close/evidence/aa997-census-*.txt` chỉ có dòng xếp job. Số census (259 /
   33, chia off_route 14 / site_type 9 / ambiguous_route 10) chỉ có trong comment S258 trên Linear và log S258.
10. Audit S260 (§4) và comment S258 trên Linear mô tả 35 dòng `unlinked` là "chặng A to B" / "non-place names". Đếm
    lại `r14-out.txt` S261: 6 chặng, 13 cụm mô tả, 16 tên thật chưa resolve (P9).
11. Output S261 (`.tmp-session/S261/aa997/`) và checklist chưa nằm trong repo; cần chép vào thư mục báo cáo này khi
    commit, nếu không các trích dẫn §9 sẽ mất khi dọn `.tmp-session/`.

---

## 6. Số liệu

### 6.1 Độ đúng theo mốc

| mốc | thời điểm | flag-strat (cổng) | sai | prov-strat | dự phóng theo ô | cổng 90 % |
|---|---|---|---|---|---|---|
| S254 nền | 28/10 | **75,4 %** (71,2–79,6) | 21,0 % | 74,8 % | — | — |
| S257 (aa997.1, 1.621/3.842) | 29/10 04:03Z | **77,7 % ±4,1** | 18,7 % | 77,1 % ±3,8 | ~79,5 % | FAIL |
| S260 (v2 ngày 1) | 30/10 08:25Z | **78,4 % ±4,0** | 18,0 % | 77,8 % ±3,8 | 80,0 % | FAIL |
| S261 (v2 xong) | 31/10 01:15Z | **78,8 % ±4,0** | 17,2 % | 78,3 % ±3,8 | 81,3 % | **FAIL** |
| Cuối (sau recheck aa997.4) | 01/11 | `{{FINAL_GATE_FLAGSTRAT}}` | `{{FINAL_WRONG}}` | `{{FINAL_GATE_PROVSTRAT}}` | `{{FINAL_PROJECTION}}` | `{{FINAL_GATE_VERDICT}}` |

### 6.2 Dự phóng theo ô

| ô | S257 | S260 | S261 | Cuối (01/11) |
|---|---|---|---|---|
| geoapify | 4.006 @ 93 % | 4.006 @ 93 % | 4.006 @ 93 % (n 254) | `{{FINAL_CELL_GEOAPIFY}}` |
| relocate gắn cờ (`rl_flagged`) | 1.207 @ 66 % | 2.001 @ 65 % | **2.697 @ 64 %** (n 232) | `{{FINAL_CELL_RL_FLAGGED}}` |
| relocate confirmed | 314 @ 64 % | 620 @ 75 % | 880 @ 77 % (n 63) | `{{FINAL_CELL_RL_CONFIRMED}}` |
| llm chưa chạm | 2.152 @ 63 % | 994 @ 58 % | 0 | 0 |
| mapbox | 210 @ 89 % | 210 @ 89 % | 210 @ 89 % (n 9) | `{{FINAL_CELL_MAPBOX}}` |
| relocate non_place | 97 @ 95 % | 155 @ 97 % | 193 @ 98 % (n 22) | `{{FINAL_CELL_RL_NON_PLACE}}` |
| **tổng** | **~79,5 %** | **80,0 %** | **81,3 %** | `{{FINAL_PROJECTION}}` |

Ô kéo số xuống là `rl_flagged`: các dòng geocoder không xác nhận được nên vẫn giữ điểm model.

### 6.3 Theo nhóm trên mẫu có nhãn

| nhóm | S257 | S260 | S261 | Cuối (recheck aa997.4) |
|---|---|---|---|---|
| dòng của chuỗi hiện tại, trước → nay | n 185 (aa997.1): 57,8 → 64,3 % | n 94 (v2): 69,1 → 71,3 % | n 148 (v2): 62,2 → 67,6 % | `{{FINAL_GROUP_CHAIN}}` |
| mọi dòng đã chạm | — | n 279: 61,6 → 66,7 % | n 333: 59,8 → 65,8 % | `{{FINAL_GROUP_TOUCHED}}` |
| dòng chưa chạm | n 415: 80,2 % | n 321: 83,5 % | n 267: 90,3 % | `{{FINAL_GROUP_UNTOUCHED}}` |
| theo outcome (đúng / n) | confirmed 18/29, llm_point 84/132, non_place 8/9, off_route 9/15 | 22/29, 36/55, 7/7, 2/3 | **28/38, 57/92, 13/13, 2/5** | `{{FINAL_CHAIN_BY_OUTCOME}}` (gồm `kept_model`) |
| regressed | 3 | 9 (6 trong v2) | 9 (6 trong v2; 5 đã trả về sau lần đo này) | `{{FINAL_REGRESSED}}` |

Trên mẫu có nhãn, chuỗi v2 sửa được 3 dòng sai (TC>fixed 2 + WP>fixed 1) nhưng làm hỏng 6 dòng đúng. Phần tăng
S260 → S261 (+0,4 điểm) chủ yếu đến từ non_place được gắn cờ (`np_flagged` 13 → 19), không phải từ dời đúng chỗ.

### 6.4 Pin phục vụ và đòn bẩy `hide_flagged`

| trạng thái | S260 (30/10 10:08Z) | S261 (31/10 01:15Z) | độ phủ S260 → S261 | Cuối (01/11) |
|---|---|---|---|---|
| mọi dòng (cổng) | 78,4 % | 78,8 % | 100 % | `{{FINAL_GATE_FLAGSTRAT}}` |
| pin phục vụ hôm nay | 80,6 % ±5,0 | **80,6 % ±5,0** | 65,0 % → 65,0 % | `{{FINAL_SERVED_NOW}}` |
| nếu `hide_flagged` | 86,6 % ±4,6 | **87,8 % ±4,6** | 52,0 % → 49,9 % | `{{FINAL_SERVED_IF_HIDE}}` |
| + ẩn `non_place` | 88,7 % ±4,3 | **90,7 % ±4,3** | 50,8 % → 48,3 % | `{{FINAL_SERVED_IF_HIDE_NP}}` |
| dự phóng theo ô (phục vụ → ẩn → + non_place) | 80,4 → 85,6 → 86,7 % | 81,7 → 89,4 → 91,3 % | | `{{FINAL_SERVED_PROJECTION}}` |
| ứng viên ẩn / pin gắn tour sẽ biến mất | 2.017 / 1.015 | 2.715 / **1.293** | | `{{FINAL_HIDE_CANDIDATES}}` |
| non_place đang phục vụ | 51 | 74 | | `{{FINAL_NON_PLACE_SERVED}}` |

Ứng viên ẩn S261 theo nước (script chỉ in 14 nước lớn nhất, cộng 2.667; 48 dòng còn lại ở nước khác): India 567, China 529, Nepal 253, Laos 211, Japan 179, Sri Lanka 177, South Korea 143,
Thailand 142, Philippines 108, Bhutan 90, Pakistan 87, Taiwan 82, Mongolia 69, Vietnam 30.

Đọc kết quả: ẩn cả cờ lẫn non_place thì điểm ước lượng lần đầu vượt 90 %, nhưng ±4,3 nên cận dưới ~86,4 %, và độ phủ
giảm từ 65 % xuống ~48 %. Số cổng (mọi dòng) không đổi khi ẩn.

### 6.5 Cổng luật chặt (P4 / census)

| phép đo | aa997.2 | aa997.3 | aa997.4 |
|---|---|---|---|
| P4: dòng đúng bị từ chối (cổng ≤ 2 %) | 34/251 = 13,5 % FAIL | 3/251 = 1,2 % PASS | chưa có output replay `{{FINAL_REPLAY_GATE}}` |
| P4: dòng sai bị bắt | 5/30 | 4/30 (mất Huashan) | `{{FINAL_REPLAY_CAUGHT}}` |
| census 3.842 dòng Geoapify gốc | 259 (6,7 %) | 33 (0,9 %): off_route 14, site_type 9, ambiguous_route 10 | — |
| đọc tay 33 dòng aa997.3 | — | 6 đúng, 21 sai, 6 lưng chừng | — |
| dry run recheck 1.197 dòng aa997.1 | — | `229a6def`: 1.197 / 1.648 req | `8fa953f3`: 1.197 / 1.648 req (khớp) |

### 6.6 Khoảng dời và proxy

- Khoảng dời v2: < 1 km 195, 1–5 km 169, 5–25 km 128, 25–100 km 72, > 100 km 38; trung vị 2,9 km, lớn nhất
  1.208 km; 135/201 lần dời đến gần route có neo hơn.
- Khoảng dời aa997.1: < 1 km 61, 1–5 km 63, 5–25 km 86, 25–100 km 82, > 100 km 33.

| proxy (dòng chuỗi v2, không nhãn) | S260 (1.216 dòng, 1.154 pin) | S261 (2.221 dòng, 2.120 pin) | Cuối (chuỗi aa997.4) |
|---|---|---|---|
| chấm được / không route | 555 / 599 | 1.038 / 1.082 | `{{FINAL_PROXY_JUDGED}}` |
| điểm geocoder viết hợp lý | 83,3 % | 83,9 % (mong ≥ 90 %) | `{{FINAL_PROXY_MOVED}}` |
| điểm model giữ lại hợp lý | 70,0 % | 68,6 % | `{{FINAL_PROXY_KEPT}}` |
| tất cả | 74,8 % | 74,1 % | `{{FINAL_PROXY_ALL}}` |
| confirmed / pin | 28,9 % | 28,4 % | `{{FINAL_PROXY_CONFIRMED_SHARE}}` |

Cuối: chạy `audit_relocated.py` với `ACCEPT=aa997.4` (bước cuối của `l4-live-steps.json`) để khối `R` lấy dòng của chuỗi recheck.

### 6.7 `recheck_14` (16 tour của AA-990)

| mốc | route đạt | all-confirmed | loose | xác nhận / tổng địa điểm | chưa xác nhận |
|---|---|---|---|---|---|
| S257 | 13/16 | 1/16 | — | — | — |
| S258 | 13/16 | 0/16 | — | — | 35 unlinked |
| S260 | 13/16 | 0/16 | 3/16 | 54/119 | 65 |
| S261 | **13/16** | **0/16** | **3/16** | **59/119** | **60** |
| Cuối | `{{FINAL_R14_ROUTE}}` | `{{FINAL_R14_ALL_CONFIRMED}}` | `{{FINAL_R14_LOOSE}}` | `{{FINAL_R14_CONFIRMED_PLACES}}` | `{{FINAL_R14_UNCONFIRMED}}` |

60 địa điểm chưa xác nhận ở S261: unlinked 35 (6 chặng "A to B", 13 cụm mô tả, 16 tên thật chưa resolve; P9); luật cũ aa997.1 gắn cờ 10 (llm_point 9, off_route 1, **chuỗi 01/11
xử lý**); chuỗi v2 llm_point 8; điểm mapbox 6; centroid_fallback 1. Tour `route = N`: `3eda85ad`, `a44bf9c4`,
`b5c3c908` (tour 1 ngày không có stop). Tour loose: `0c608efd`, `b7188d60`, `b9b39260`.

### 6.8 Tên chưa resolve (trước/sau theo Done-when)

| mốc | resolved | pending | unknown |
|---|---|---|---|
| S254 | 7.924 | 1.203 | 418 |
| S257 | 7.986 | 1.011 | 580 |
| S260 / S261 | chưa đo (`audit_relocated.py` không in trạng thái `geo.place_name`) | | |
| Cuối | `{{FINAL_RESOLVED}}` | `{{FINAL_PENDING}}` | `{{FINAL_UNKNOWN}}` |

---

## 7. Chuỗi recheck aa997.4 (31/10 → 01/11)

Selection: 1.197 dòng mang dấu aa997.1 có outcome `llm_point` (1.004) hoặc `off_route` (193). Payload: accept
`aa997.4`, strategy `v2`, `hide_unconfirmed: false`. Mục đích: dời các pin sai còn lại vào đúng chỗ, và không dời
nhầm sang POI trùng tên.

### 7.1 Các job đã biết

| job | loại | thời điểm | dòng | confirmed / llm_point / off_route / non_place / kept_model | request | kết thúc |
|---|---|---|---|---|---|---|
| `229a6def` | dry run aa997.3 | 31/10 ~01:16Z | 1.197 | — | 1.648 (ước) | succeeded |
| `8fa953f3` | dry run aa997.4 | 31/10 ~02:07Z | 1.197 | — | 1.648 (ước) | succeeded (khớp aa997.3) |
| `32ace765` | trial apply, limit 50, trần 150 | 31/10 ~02:09Z | 50 | 6 / 23 / 21 / 0 / 0 | 76 | ok, 0 lỗi |
| `6086f577` | nối tiếp trial | 31/10 | 48 (= 1.147 − 1.024 − 75; tổng trial 98) | chưa có file | ≤ 74 (suy ra: 1.242 + 76 + 74 + 108 = 1.500 credit relocate ngày 31/10) | dừng ở trần 150 (checklist) |
| `b0190743` | apply đầy đủ, 400 dòng/lượt | 31/10 ~02:43Z | 75 | 15 / 44 / 16 / 0 / 0 | 108 | `stopped_credit_limit` |
| `dc260ef8` | nối tiếp | 01/11 ~00:11Z | `{{FINAL_JOB_DC260EF8_ROWS}}` | `{{FINAL_JOB_DC260EF8_OUTCOMES}}` | `{{FINAL_JOB_DC260EF8_REQ}}` | `{{FINAL_JOB_DC260EF8_STATUS}}` |
| (job nối tiếp khác) | | 01/11 | `{{FINAL_JOBS_MORE}}` | | | |

Sau 31/10 còn **1.024 dòng** (1.197 − 98 − 75). Tỉ lệ request thật: 1,52/dòng (`32ace765`), 1,44/dòng (`b0190743`);
dry run ước 1,38/dòng và `days: 2`. 1.024 dòng × 1,38–1,52 ≈ 1.410–1.560 request, sát trần 1.500 credit/ngày của
relocate (trần này tính cả credit `place_geocode` dùng trong ngày). Chuỗi có thể xong trong 01/11 hoặc tràn sang lượt
02/11 00:11Z: kiểm `remaining` của job cuối trước khi audit.

### 7.2 KẾT QUẢ CUỐI (điền sau khi chuỗi xong 01/11)

Chạy lại `audit_relocated.py` và `recheck_14.py` (chỉ đọc, $0) khi bảng job không còn job `place_relocate` mở.

| chỉ số | giá trị |
|---|---|
| Thời điểm chuỗi đóng (job cuối, `remaining 0`) | `{{FINAL_CHAIN_CLOSED_AT}}` |
| Cổng flag-strat (`GATE`) | `{{FINAL_GATE_FLAGSTRAT}}` (`{{FINAL_GATE_VERDICT}}`, mốc 90 %) |
| Cổng prov-strat | `{{FINAL_GATE_PROVSTRAT}}` |
| Dự phóng theo ô | `{{FINAL_PROJECTION}}` |
| Pin phục vụ hôm nay / độ phủ | `{{FINAL_SERVED_NOW}}` / `{{FINAL_SERVED_NOW_COVERAGE}}` |
| Pin phục vụ nếu `hide_flagged` / độ phủ | `{{FINAL_SERVED_IF_HIDE}}` / `{{FINAL_SERVED_IF_HIDE_COVERAGE}}` |
| Pin phục vụ nếu ẩn thêm `non_place` / độ phủ | `{{FINAL_SERVED_IF_HIDE_NP}}` / `{{FINAL_SERVED_IF_HIDE_NP_COVERAGE}}` |
| Ứng viên ẩn / pin gắn tour sẽ biến mất | `{{FINAL_HIDE_CANDIDATES}}` / `{{FINAL_HIDE_LINKED}}` |
| `recheck_14`: route / all-confirmed / loose | `{{FINAL_R14_ROUTE}}` / `{{FINAL_R14_ALL_CONFIRMED}}` / `{{FINAL_R14_LOOSE}}` |
| Chain sums aa997.4: dòng done | `{{FINAL_CHAIN_DONE}}` (kỳ vọng 1.197) |
| Chain sums: confirmed / llm_point / off_route / non_place | `{{FINAL_CHAIN_CONFIRMED}}` / `{{FINAL_CHAIN_LLM_POINT}}` / `{{FINAL_CHAIN_OFF_ROUTE}}` / `{{FINAL_CHAIN_NON_PLACE}}` |
| Chain sums: `kept_model` (guard aa997.4 chặn dời xa) | `{{FINAL_CHAIN_KEPT_MODEL}}` |
| Chain sums: request Geoapify / chi phí | `{{FINAL_CHAIN_REQUESTS}}` / `{{FINAL_CHAIN_COST}}` (kỳ vọng $0) |
| Regressed trên mẫu (S254 đúng, nay sai) | `{{FINAL_REGRESSED}}` (31/10: 9, trong đó 6 của v2; 5 đã trả về) |
| Regressed mới do aa997.4 | `{{FINAL_REGRESSED_NEW_AA9974}}` |
| Tên `geo.place_name`: resolved / pending / unknown (cần query riêng, audit không in) | `{{FINAL_RESOLVED}}` / `{{FINAL_PENDING}}` / `{{FINAL_UNKNOWN}}` |

Kết luận cuối: `{{FINAL_VERDICT_TEXT}}`

---

## 8. Còn lại và đề xuất tiếp

Thứ tự đề xuất sau khi chuỗi 01/11 xong:

1. **Audit cuối và đóng AA-997 dạng Done-with-scope.** Điền §7.2, comment S261/S262 lên Linear kèm số, ghi rõ: tên
   mới đã có toạ độ từ geocoder (mục tiêu chặn sai từ nguồn đã đạt), dữ liệu cũ chưa đạt 90 % trên cổng. Ghi rõ
   phần Done-when chưa đo (mẫu mù mới).
2. **Confirm `hide_flagged`** (đã duyệt theo đề xuất S261). Báo cáo mới → confirm trong 6 h khi không còn chuỗi mở.
   Không ẩn `non_place` cho tới khi có quyết định riêng (bỏ nhầm 3/439 tên đúng). Trước khi confirm, sửa hoặc chấp
   nhận rõ 3 lỗi nhỏ còn mở của #1178 (P15). Đo lại pin phục vụ sau khi ẩn.
3. **Kiểm 6 dòng regressed:** đọc DB xác nhận 5 điểm đã revert, và dòng "sheeshganj gurudwara sikh temple" còn ở
   điểm sai hay không; nếu còn thì trả về `relocate.prev` cùng cách (manual + audit_log).
4. **Follow-up có điều kiện** "[Places] Reach 90%: LLM-assisted adjudication of llm_point rows + alias table + hand
   pins". Chỉ mở nếu tech lead muốn đạt 90 % trên cổng cho dữ liệu cũ. Khoảng cách còn ~+11 điểm, tương đương ~32
   dòng mẫu ngẫu nhiên hoặc ~150 dòng có cờ phải được dời đúng chỗ; recheck aa997.4 tới 31/10 xác nhận 12–20 % dòng
   (`32ace765` 6/50, `b0190743` 15/75) nên khó tự đạt. Nội dung: model chấm chọn giữa các ứng viên geocoder cho dòng `llm_point` (ghi cost qua
   `LLMClient` + `shared.llm_call_log`, chạy thử nhỏ trước), bảng alias tên, ghim tay ~113 dòng sai đã biết. Cần
   endpoint sửa điểm bằng tay có audit trước (hiện sửa phải qua SQL thô).
5. **Dòng mapbox** (210–289 dòng, đúng ~89 %): chạy dry run `located_by=['mapbox']` để xem quy mô, hoặc để nguyên.
   Giải thích lệch 210 / 289.
6. **35 địa điểm `unlinked` của `recheck_14`:** 6 chặng "A to B" (tách chặng ở bước parse, đổi component id, phải
   phối hợp TripPlanner, hoặc sửa tay); 13 cụm mô tả (đánh dấu non-place, không cần toạ độ); 16 tên thật chưa resolve
   (`place_geocode` thử lại hoặc admin ghim tay).
7. **Quyền đọc view catalog để đo pin phục vụ:** cấp SELECT trên `catalog.v_tour_component` / `v_tour_stop` /
   `v_tour_place` cho login audit, hoặc chạy audit qua DB Migrate `mode=run-script` với role đọc được catalog. Đây là
   migration/grant, phải qua review.
8. **16 tour của AA-990** (`recheck_14`): sau chuỗi 01/11, xử lý 8 dòng llm_point v2, 6 điểm mapbox, 1 centroid và 3
   tour 1 ngày không có stop; mục tiêu all-confirmed > 0/16.
9. **Mẫu mù mới ≥ 200 tên chia theo provenance** để đóng đúng Done-when (người kiểm chấm, không dùng lại mẫu S254).
10. **Việc nhỏ còn lại:** `name_norm` bỏ "An" ở đầu; polygon ven biển cho đảo; backfill provenance; sweep ngưỡng
    aa997.4 trên mẫu có nhãn; đọc 30 dòng WATCH; quyết định có đổi env `GEOCODER_STRATEGY` sang `v2` cho tên mới
    (cần census trước vì `site_admin_named` cũng đổi cách nhận tên mới). ⚠️ Biến env có gạch dưới: sửa tay.
11. **Lỗi nước của tour nguồn** (Kilimanjaro lưu là India, "Bhutan Cultural Tour" lưu là Nepal): ngoài hệ thống,
    chuyển cho chủ file Excel nguồn.

---

## 9. Nguồn

Audit và tài liệu trong repo gốc:

- `docs/audits/2026-10-28-S254-geocode-audit/README.md` (audit nền, kế hoạch 8 bước)
- `docs/audits/2026-10-29-S257-aa997-interim/README.md`, `output.txt`
- `docs/audits/2026-10-29-S258-aa997-p4-tune/README.md`
- `docs/audits/2026-10-30-S258-session-close/evidence/aa997-census-*.txt`, `state-snapshot.md`
- `docs/audits/2026-10-30-S260-aa997-interim/README.md`, `RUNBOOK.md`, `audit-out-mid.txt`, `audit-out-2.txt`,
  `r14-out-mid.txt`, `hide-report-out.txt`
- `docs/audits/2026-10-28-S255-session-close/state-snapshot.md`
- Log phiên `docs/sessions/2026-10-28-S254-…`, S255, S256, S257, S258, S259, S260
- `skill/aa-lessons/lessons.md` (bài học migration giữa các chuỗi, ECS exec timeout, làm tròn toạ độ, openapi)

AA-CIS-App:

- `apps/AA-CIS-App/docs/implementation-notes/AA-997.md` (Part 1–5), `AA-997-aa9974.md`
- `services/places/relocate.py`, `geomatch.py`, `guards.py`, `geocoder.py`, `name_filter.py`,
  `services/jobs/place_relocate_job.py`, `api/routers/admin_places.py`
- PR #1092, #1139, #1147, #1178, #1185, #1193; Booking #160; TripPlanner #195; root #340

Output S261 (chưa commit, `.tmp-session/S261/aa997/`):

- `audit-out.txt` (dòng `JOB`, `GATE`, `L overall`, `L projection`, `L chain_*`, `V accuracy`, `SERVED`,
  `R rows`, `J chain_sums`), `r14-out.txt`
- `recheck-dry-out.txt`, `recheck-dry-v4-out.txt`, `recheck-trial-out.txt`, `recheck-full-out.txt`
- `revert_regressed.py`
- `.tmp-session/S261-checklist.md` (mục 10–11)

Linear: AA-997 (mô tả, comment S255 → S260; comment S258 là nguồn duy nhất của phân rã census, comment S259 là nguồn của
đọc tay 33 dòng và 2 sân bay / 4 tên Irkutsk), AA-990.

Log phiên S256 (`docs/sessions/2026-10-29-S256-…`) là nguồn cho `ce96dfa5`, lệnh huỷ Laos bị chặn và override 301.
`apps/AA-CIS-App/docs/implementation-notes/AA-997.md` Part 4 là nguồn cho 3 lỗi nhỏ còn mở của #1178.
