# AA-997 — audit giữa chừng độ đúng geocode sau chuỗi `place_relocate` (S257)

Phiên S257, 29/10/2026. Tác nhân: Claude Code (lane chuẩn bị + điều phối chạy). Issue: AA-997 (đầu vào cho AA-990
`recheck_14`). Bản tư vấn cho tech lead. **Đã chạy 29/10 04:03 UTC (luật `aa997.1`); mục 1 đã điền số từ `output.txt`. Các bảng chi tiết ở mục 3–5 còn giữ
chỗ trống mẫu `{{...}}` — số thật của chúng nằm nguyên trong `output.txt` (dòng P1 / P2 / P3).**

Chỉ đọc: một transaction `REPEATABLE READ READ ONLY` (rollback ở cuối), login `cis_app`, `application_name`
`aa997-interim-audit`, `statement_timeout` 60 s. Không ghi DB, không gọi geocoder hay LLM: chi phí $0.

| file | nội dung |
|---|---|
| `README.md` | báo cáo này |
| `aa997_interim_audit.py` | script chạy trong container CIS api (`tools/ecs/ecsx.sh`), có nhúng 600 dòng `verified.json` của S254 |
| `build_aa997_interim_audit.py`, `aa997_interim_audit.src.py` | sinh script trên từ `verified.json` (chép từ `.tmp-session/S257/` khi commit) |
| `output.txt` | output thô của lần chạy (chỉ số tổng hợp, không dữ liệu dòng) |

## 1. Trả lời trước

- **Độ đúng hiện tại (cùng mẫu 600 dòng S254, chấm lại trên toạ độ hôm nay): 77,7 %** (khoảng tin cậy 95 %
  ±4,1), so với **75,4 %** ở S254. Phân tầng theo provenance: 77,1 % (S254: 74,8 %).
- **Dòng chuỗi relocate đã xử lý trong mẫu: 185 dòng, đúng 57,8 % → 64,3 %.**
  Dòng chưa xử lý: 415 dòng, đúng 80,2 % (không đổi so với S254 là bình thường).
- **Ước tính toàn bộ dòng resolved hôm nay** (tỉ lệ theo ô provenance hiện tại × số dòng của ô): ~79,5 %.
  Mục tiêu AA-997 là ≥ 90 %; khoảng cách còn lại chủ yếu nằm ở các dòng LLM định vị chưa được chuỗi xử lý (2.152 dòng, ~63 % đúng) và dòng relocate bị gắn cờ (1.207 dòng, ~66 %); dòng Geoapify chưa đụng đúng 90,3 %.
- **Chuỗi `place_relocate` đến giờ:** 1.621 / 3.842 dòng (`confirmed` 325, `non_place` 99,
  `off_route` 193, `llm_point` 1.004, đổi nước HK/MO 3), 1.500 request Geoapify, $0.
  Còn 2.221 dòng `located_by = llm`; theo credit 1.500/ngày cần thêm ~2 ngày.
- **Tour có mọi địa điểm đã được geocoder xác nhận:** 76 / 892 tour live (chặt hơn — thêm điều
  kiện không còn component chưa link: 57). Trong 14 + 2 tour của `recheck_14`: route đạt
  13 / 16, mọi địa điểm xác nhận 1 / 16.

## 2. Cách đo

### 2.1 Chuỗi relocate (phần P1)

- `shared.job` kind `place_relocate`: đếm job theo (mode, status, `result.status`), cộng các bộ đếm của mọi job
  `apply` (`rows`, `done`, `confirmed`, `non_place`, `off_route`, `llm_point`, `country_fixed`, `skipped`, `errors`,
  `geocoder_requests`), lấy `remaining` của job apply xong gần nhất và các job còn `queued`.
- Theo nước: dấu của từng dòng `shared.destinations.geocoder_meta.relocate.outcome` (mỗi dòng xử lý đều được đóng
  dấu `{v: aa997.1, outcome, at, moved_km?}`), nhóm theo `country_iso2`; cột "còn lại" = dòng `located_by = 'llm'`,
  chưa gộp, không `manual`, chưa có dấu `aa997.1` (đúng điều kiện chọn của job).
- `country_fixed` không phải một outcome riêng mà là cờ phụ (CN → HK/MO) trên dòng `confirmed` hoặc dòng bị gắn cờ.
- Chuỗi hiện chạy với `located_by = ['llm']`: 210 dòng `mapbox` (S254: 8/9 đúng) chưa nằm trong chuỗi.

### 2.2 Độ đúng (phần P2) — cùng luật chấm của S254 áp lên toạ độ hôm nay

Ground truth là 600 dòng đã kiểm ở S254 (`docs/audits/2026-10-28-S254-geocode-audit/verified.json`: 200 dòng ngẫu
nhiên không cờ + 400 dòng có cờ rủi ro cao nhất), nhúng thẳng vào script (~70 KB, không cần chia đoạn). Mỗi dòng được
nối lại với dòng hiện tại qua khoá `geo.place_name (name_norm, country_norm, locality_norm)` → `shared.destinations`
(theo `duplicate_of` nếu đã gộp). `rules.py` của S254 chỉ sinh **cờ** rủi ro; "đúng / sai" của S254 là phán định của
người kiểm với dung sai **site ~2–4 km, làng/thị trấn ~5 km**. Chấm lại theo đúng dung sai đó (4 km cho tên kiểu site,
5 km cho tên khác):

| phán định S254 | toạ độ hôm nay | chấm lại |
|---|---|---|
| correct | không đổi, hoặc dời ≤ dung sai | đúng |
| correct | dời > dung sai | **sai (`regressed`)** — bảo thủ; đếm riêng để soi |
| wrong_place / too_coarse / wrong_country | dời và nằm trong dung sai của một điểm `expected` | đúng (`fixed`) |
| wrong_country (HK/MO lưu là CN, cùng điểm) | ISO hiện là HK/MO | đúng (`iso_fixed`) |
| wrong_* | không đổi | vẫn sai (đếm riêng dòng đã bị gắn `review_reason`) |
| wrong_* | dời nhưng không có điểm `expected` (2 dòng) | không chấm được |
| not_a_place | `review_reason`/`last_error` `non_place:*`, bị ẩn, hoặc không còn | đúng (đã xử lý) |
| not_a_place | vẫn là pin bình thường | sai |
| unsure | — | vẫn unsure |

- **Ước tính tổng thể**: phân tầng như S254 (theo cờ: 5.603 không cờ / 2.321 có cờ; theo provenance × cờ), có hiệu
  chỉnh quần thể hữu hạn. Script in cả số S254 tái tính để đối chiếu: phải ra **75,4 %** và **74,8 %** (kiểm trên máy
  bằng dữ liệu giả lập không đổi toạ độ: khớp).
- **"Đã chạm"** = dòng destination có dấu `geocoder_meta.relocate`. So sánh trước/sau trên chính các dòng đó.
- **Ước tính toàn bộ** (phụ): chia dòng resolved hôm nay theo ô hiện tại (`geoapify` gốc, relocate `confirmed`,
  relocate gắn cờ `off_route`/`llm_point`, relocate `non_place`, `llm` chưa chạm, `mapbox`, `manual`); tỉ lệ đúng của mỗi
  ô lấy từ các dòng đã kiểm đang nằm trong ô đó, có trọng số theo xác suất chọn mẫu S254 (dòng ngẫu nhiên 28,0, dòng có
  cờ 5,8). Ô ít mẫu thì sai số lớn — đọc như xu hướng.
- **Luật `rules.py` hôm nay**: tính lại 4 cờ (dup_coords, precision_area_site, provenance_null, tour_spread) trên dòng
  resolved hiện tại, so với S254. Hai cờ country / bbox cần bảng nước của S254, không tính lại (S254: 38 / 0 dòng).

### 2.3 Tour đã xác nhận hết (phần P3) — đầu vào AA-990 `recheck_14`

- `recheck_14` (`.tmp-session/S255/aa990/recheck_14.py`, ghi chú AA-990 "Should know") kiểm lại **14 tour N1 đang chờ
  geocode** (S254 close, `docs/audits/2026-10-27-S254-aa990-close/`) cùng 2 tour luật chặng transit (Seoul–Busan,
  Oze–Nikko): tour có route trên Tour Graph khi có stop và số ngày có pin ≥ 0,5 × số ngày tour (ngưỡng S236 của
  TripPlanner; xấp xỉ, mẫu số là ngày cao nhất trong `geo.tour_day`).
- "Địa điểm của tour" = destination của mọi component `geo.tour_place` + điểm ngủ đêm `geo.tour_day`, theo
  `duplicate_of`. "Đã được geocoder xác nhận" = `located_by` là `geoapify` hoặc `manual` (admin sửa) và không `suspect`.
  Bản chặt: thêm điều kiện không còn component nào chưa link (`destination_id` null). Chỉ tour có `tour_build` khác
  `retired`.

## 3. Kết quả chuỗi `place_relocate`

| | số |
|---|---|
| job (mode / status / result.status) | {{P1_JOBS}} |
| dòng đã xử lý (`done`) | {{P1_DONE}} |
| `confirmed` (geocoder xác nhận, điểm được viết lại) | {{P1_CONF}} |
| `non_place` | {{P1_NP}} |
| `off_route` (giữ điểm cũ, gắn cờ) | {{P1_OFF}} |
| `llm_point` (geocoder không xác nhận, giữ điểm cũ, gắn cờ) | {{P1_LLM}} |
| đổi nước CN → HK/MO | {{P1_CF}} |
| `skipped` / `errors` | {{P1_SKIP}} / {{P1_ERR}} |
| request Geoapify / chi phí | {{P1_REQ}} / $0 |
| còn lại (`located_by = llm`) | {{P1_LEFT}} |
| job kế tiếp | {{P1_NEXT}} |

Khoảng dời của dòng `confirmed`: < 1 km {{MV_1}}, 1–5 km {{MV_5}}, 5–25 km {{MV_25}}, 25–100 km {{MV_100}},
> 100 km {{MV_BIG}}. (S254: toạ độ LLM lệch 5–100 km là lỗi phổ biến nhất.)

Theo nước (15 nước nhiều dòng nhất):

| ISO | confirmed | non_place | off_route | llm_point | còn lại |
|---|---|---|---|---|---|
| {{ISO}} | | | | | |

## 4. Độ đúng hiện tại

| nhóm | n | đúng S254 | đúng hôm nay | sai S254 | sai hôm nay |
|---|---|---|---|---|---|
| 200 ngẫu nhiên không cờ | 200 | 77,0 % | {{R_NOW}} | 19,0 % | {{R_ERR}} |
| 400 có cờ | 400 | 71,5 % | {{F_NOW}} | 25,8 % | {{F_ERR}} |
| **toàn bộ, phân tầng theo cờ** | 7.924 | **75,4 %** | **{{P2_NOW_FLAG}}** | 21,0 % | {{P2_NOW_ERR}} |
| toàn bộ, phân tầng theo provenance | 7.924 | 74,8 % | {{P2_NOW_PROV}} | 21,5 % | — |
| dòng relocate đã chạm | {{P2_TOUCHED_N}} | {{P2_TOUCHED_BEFORE}} | {{P2_TOUCHED_NOW}} | | |
| dòng chưa chạm | {{P2_UNTOUCHED_N}} | | {{P2_UNTOUCHED_NOW}} | | |

Theo outcome relocate (đúng / số dòng mẫu): {{P2_BY_OUTCOME}}. Chuyển trạng thái nổi bật: {{P2_TRANSITIONS}}.

- `regressed` (dòng S254 đúng mà geocoder dời > dung sai): {{P2_REGRESSED}}. Nếu đáng kể → soi từng dòng (có thể
  geocoder trúng homonym trong bán kính route, hoặc điểm S254 chỉ vừa đủ dung sai).
- Lỗi chưa sửa nhưng đã bị gắn `review_reason` (không còn hiện như pin chính xác): {{P2_FLAGGED}}.

Ước tính toàn bộ theo ô hiện tại: {{P2_CELLS}} → ~{{P2_PROJ}} %.

Luật `rules.py` hôm nay (S254 trong ngoặc): dup_coords {{RU_DUP}} (927), precision_area_site {{RU_PREC}} (755),
provenance_null {{RU_PROV}} (652), tour_spread {{RU_SPREAD}} (260), có ít nhất một cờ {{RU_ANY}} (~2.286).
Trạng thái `geo.place_name`: {{PN_STATUS}} (S254: resolved 7.924, pending 1.203, unknown 418).

## 5. Tour đã xác nhận hết và `recheck_14`

| | tour |
|---|---|
| tour live | {{P3_TOURS}} |
| mọi địa điểm đã link đều được geocoder xác nhận | {{P3_LINKED}} |
| như trên và không còn component chưa link | {{P3_STRICT}} |
| còn ít nhất một điểm `llm` / `mapbox` / có `review_reason` | {{P3_LLM}} / {{P3_MAPBOX}} / {{P3_FLAGGED}} |
| theo tỉ lệ địa điểm xác nhận (100 % / ≥ 90 % / ≥ 75 % / < 75 %) | {{P3_SHARE}} |

Theo nước của tour: {{P3_BY_COUNTRY}}.

| tour | nhóm | build | ngày | ngày có stop | ngày có pin | route | địa điểm xác nhận | llm | cờ | chưa link | anchor chưa resolve |
|---|---|---|---|---|---|---|---|---|---|---|---|
| {{SID}} | p14 / leg | | | | | Y/N | x / n | | | | |

## 6. Giới hạn

- Ground truth là phán định của người kiểm ở S254 (không phải geocoder thứ hai). Dòng bị dời được chấm bằng khoảng cách
  tới điểm `expected` S254 ghi; điểm đó là ước lượng (~), nên dòng nằm sát dung sai có thể lệch phán định.
- Mẫu 600 dòng chọn từ dữ liệu 28/10. Dòng mới resolve sau đó (pending → resolved) không có trong mẫu; phần ước tính
  toàn bộ gán cho chúng tỉ lệ của ô provenance cùng loại.
- Chuỗi relocate xử lý điểm ngủ đêm trước, site sau (để site có route). Số "đã chạm" giữa chừng nghiêng về thị trấn —
  loại vốn dễ đúng — nên tỉ lệ cuối chuỗi có thể khác.
- `non_place` khi chạy relocate với `hide_unconfirmed = false` (mặc định) chỉ gắn `review_reason`, không ẩn pin; báo cáo
  này tính dòng not_a_place đã gắn cờ là "đã xử lý".

## 7. Việc tiếp theo (đề xuất)

1. Để chuỗi chạy hết theo credit ngày (~31/10), chạy lại đúng script này để có số cuối; nếu ≥ 90 % → đóng phần đo
   của AA-997.
2. Nếu dưới 90 %: ưu tiên theo ô có lỗi lớn nhất ở §4 — thường là dòng `llm_point` / `off_route` còn giữ điểm LLM
   (đề xuất: bật `hide_unconfirmed` cho các dòng này sau khi xem mẫu; quyết định của tech lead) và 210 dòng `mapbox`
   (chạy relocate `located_by = ['mapbox']`, dry run trước).
3. AA-990: chạy `recheck_14` khi các tour trong §5 có `all_confirmed = Y`; tour còn `N` thì liệt kê địa điểm chưa xác
   nhận để sửa tay trong `/admin/places`.
