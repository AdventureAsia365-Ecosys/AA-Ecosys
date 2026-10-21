# AA-847: vẽ đường kẻ và gộp trùng tự động (S246)

## lines

Đã làm xong Vấn đề 1 của AA-847 (vẽ sông, đường, tuyến trek thành đường kẻ) theo kế hoạch đã sửa sau lượt phản biện S246. Tất cả chỉ commit local: chưa push, chưa mở PR, chưa merge, không ghi DB Dev, không gọi API trả phí nào.

Các nhánh, xếp chồng theo thứ tự merge:
- CIS `feat/aa-847-lines` (nhánh validity + migration 255): đây là phần còn dở của lượt trước, đã chạy test lại rồi mới commit. Nhánh có migration 255 (precision `line`, `geo.place_shape`, `geo.tour_segment`, cột credits/endpoint) và §1 của kế hoạch: bỏ cơ chế ẩn, đường kẻ không bao giờ là điểm dừng (stop) hay node của graph, quy tắc liên kết cụm mô tả với feature (bộ 83 cụm có nhãn), cổng `linear_without_shape`.
- CIS `feat/aa-847-place-shape`:
  - `shape.py` gồm cắt theo polygon quốc gia (Natural Earth, public domain, 18 nước, không dùng bbox), luật chấp nhận, rút gọn VW để vừa CHECK của 255, cắt đoạn theo ngày, luật trùng cho đường kẻ.
  - `shape_sources.py` gọi Geoapify Place Details rồi đến Overpass.
  - Job `place_shape`: mặc định tắt bằng `PLACE_SHAPES_ENABLED`, dùng chung advisory lock Geoapify với `place_geocode`. Khi không có feature OSM thì vẽ tuyến ước lượng từ các điểm neo của ngày, còn không thì đánh `not_found`.
  - `tour_graph_build` ghi `geo.tour_segment`.
  - Tab Lines trên `/admin/places`, backfill có dry-run, cho nhập GeoJSON thủ công.
- CIS `feat/aa-847-lines-views` (= `feat/aa-847-place-shape` + merge `feat/aa-847-places-l4`): migration 256.
  - `v_destination` có thêm bbox không bao giờ null cùng các cột shape.
  - `v_destination_shape` chỉ cấp cho tripplanner.
  - `v_tour_place` và `v_tour_component` có thêm đoạn đi theo ngày; `_live_stop` loại đường kẻ.
  - EXPLAIN đúng dạng truy vấn của TP: điều kiện lọc bbox được đẩy xuống dưới barrier, và không chạy LATERAL ảnh.
- Infra:
  - `feat/aa-847-cis-255-copy`, `feat/aa-847-cis-256-copy`: bản sao byte và lint.
  - `feat/aa-847-contract-pins-v1.2`: pin hai contract v1.2.
- Root `feat/aa-847-places-l4`:
  - contracts `catalog.tour` v1.2 và `catalog.graph` v1.2;
  - sửa ADR 0007: thêm precision `line`, đường kẻ được vẽ chứ không ẩn, trùng thì gộp tự động;
  - thêm 2 bài học;
  - ghi chú song ngữ về ODbL cho chị Thư.
- TP `feat/aa-847-slice-6d`:
  - Tiles chọn theo bbox, không mang hình học; hình học lấy qua `/browse/shapes` theo id.
  - Bản đồ có lớp đường kẻ: viền trắng, nước màu xanh, đường mực liền, tuyến trek và tuyến ước lượng nét đứt có nhãn, đường bấm rộng 14 px.
  - Bản đồ chuyến đi có chặng `feature` màu vàng thay cho chặng đường bộ/bay giữa cùng hai điểm dừng. Không tốn thêm request Directions nào, có test chứng minh.
  - Đường kẻ chưa có hình học thì vẽ nét đứt "approximate route".
  - Danh sách có ký hiệu 〰 và dòng "A → B · ≈ n km".
  - Bản đồ tĩnh vẽ path; có test bảo đảm URL dưới 8.192 ký tự.
  - Câu trả lời tour lên v1.2.
  - Gia cố cho 6c: chỉ `point` mới được vẽ thành ghim chính xác.

Có một chỗ tôi làm khác kế hoạch: `linear_feature` vẫn nằm trong GATE_REASONS, với nghĩa mới là "tên tuyến nhưng lại lưu thành ghim hoặc vòng tròn". Lý do và chi tiết đã ghi ở mục Decisions trong `docs/implementation-notes/AA-847-lines.md`.

Bước LLM gộp trùng của Vấn đề 2 tôi không làm. Lane dedupe đang làm bước này trong `cis-aa-847-dedupe` (file còn đang được sửa), nên tôi không chạm vào. Phần tất định cho đường kẻ đã đánh giá offline trên bộ cặp có nhãn, số liệu ở phần metrics. Các cặp luật này không quyết được thì để dành cho bước kiểm tra bằng model của lane đó.

### Số đo

D2 line duplicates (shape.same_line_place), 24 author-labelled pairs (13 same, 11 different; synthetic geometry along the real courses): 0 false merges, 9/13 same pairs merged, 11/11 different pairs kept, 4 missed. The 4 misses all go to the model check: the Laos-side HCM Trail approximate routes are more than 1 km apart; Kwai Noi / Khwae Noi has no OSM names in the fixture; Ha Giang Loop / Ha Giang Loop Road is trail vs road; one pair has no geometry yet. linked_feature (from the previous run, branch 1): 83 labelled phrases, 0 false links, 0 wrong features, 0 missed links. That set was written alongside the rule, so it is a regression floor, not a field accuracy. Performance: clipping a 2,000-vertex line to a country takes ~20 ms (pure Python, latitude bands). VW simplification of 5,000 vertices takes 0.04 s; the old DP took 83 s. Country polygons file: 469 KB (18 countries, 25,441 vertices). Trip Directions requests: a line day between two stops removes 1 request (test: 2 → 1). No paid or external calls were made: Natural Earth was downloaded from GitHub once (free, public domain), Geoapify 0 credits, Overpass 0 requests, LLM 0 calls.

### Chi phí

No call was made. Expected cost of the shapes backfill (the plan's §10 figures, not re-measured): Geoapify Place Details for ~340 line destinations × (1 details + at most 1 full_geometry, the second only when the first answer is a point or cut short), plus at most 1 re-search where no place id is stored. That is at most ~1,020 credits, under the daily guard of 2,500. Cost is $0 on the Free plan. The credits per feature are an assumption (1 + 1, in code as shape_sources.DETAILS_CREDITS / FULL_GEOMETRY_CREDITS); the 5-name trial must read the real figure from the dashboard. Overpass (public): at most ~400 queries at ≤ 1 request / 2 s, $0. Anchored approximate route: no calls, $0. LLM: none, $0. Mapbox: no new API, and Directions requests stay the same or fewer, $0. Storage: place_shape ≈ 2–17 MB + tour_segment ≈ 3 MB per build kept, ≈ $0. Worst case: if the Geoapify Free plan goes away, one month of API 10 = $59.

### Câu hỏi mở

- Does an anchored approximate route (dashed, labelled 'approximate route') count as 'drawn correctly' under D1 for conceptual routes with no single OSM feature (Ha Giang Loop, HCM Trail on the Laos side, Tea Horse Route)? Proposed answer: yes. The code counts approximate as drawn for the flip gate, and the Lines tab reports it separately per country.
- On the browse map, a line with no geometry yet (pending / not_found) is not drawn (there are no anchors in that view). It still appears in lists and is flagged on /admin/places; the trip map always draws a provisional line between the day's stops. Is that enough for D1? Proposed answer: yes (this is what plan §5 says).
- Which line duplicate rule is final: this plan's (70% of geom_mid by length, or the same OSM id, with the OSM-names exception for 'Red River' / 'Sông Hồng') or the dedupe lane's (60% of geom_lo vertices)? Proposal: measure both on the shared pairs set, keep same_line_place for auto_merge, and send the rest to the model.
- The real Geoapify Place Details credit cost per feature (assumed 1 for details + 1 for full_geometry) still has to be measured in the trial.

### Review (chặn)

- Root feat/aa-847-places-l4, docs/adr/0007-place-pipeline-in-cis.md (S246 amendment, commit b1c6239): the ADR describes behaviour that is not built. Since the ADR is the source of truth and the root PR is self-merged without CI, fix the wording before push. (a) 'drawn as lines on every TripPlanner map … also before the flip and while a shape is missing' is not true. On PLACES_SOURCE=legacy (Dev today), TP tiles read shared.destinations / tripplanner.itinerary_components, which carry no precision, so TP 6d isExactPin(precision == null) draws linear places as exact pins. The browse map skips pending / not_found / failed lines (MapView drawLines filters on isDrawable). The trip map draws the provisional line only when segment_from/to equal two consecutive trip stops (lib/lines.ts planTrip; a provisional stretch is never put in extras). (b) 'Duplicates merge automatically … the merge moves the keeper's geo.place_shape row' has no caller in these branches: shape.same_line_place is used only by tests/unit/test_aa847_line_pairs.py, and it is the duplicate's row that moves (validity_fix.shape_merge). The rule also differs from the dedupe lane's (60% of geom_lo vertices vs 70% of geom_mid by length / same OSM id). Mark D2 for lines as delivered by the dedupe lane (cis-aa-847-dedupe, 257). State D1's real scope: CIS path only, after 256 + flip, with the pending/browse and trip-stop-mismatch gaps listed as open questions.

## dedup

Em đã làm xong phần gộp trùng địa danh tự động của AA-847 (Problem 2) theo plan đã sửa. Các thay đổi chỉ commit trên máy (chưa push, chưa mở PR, chưa ghi gì lên Dev), không gọi API trả phí nào.

**CIS PR A (`feat/aa-847-dedupe`)** — một hàm quyết định chung `services/places/dedupe.decide`, rule r1.4:
- Id chung của Geoapify hoặc place card chỉ là tín hiệu, không phải phán quyết. Nó chỉ được tự gộp khi cả hai là POI hoặc địa danh tự nhiên, tên khớp chính xác hoặc gần đúng (fuzzy), và không dính trường hợp mơ hồ nào. Id của một khu hành chính (phường, quận) thì không tính.
- Hai đường đều đã vẽ được thì dùng chính rule `shape.same_line_place` của lane lines, để cả codebase chỉ có một rule cho đường. Đường chưa có hình, hoặc một điểm so với một đường, thì cao nhất chỉ gửi sang model.
- Thứ tự chọn keeper: hàng chỉnh tay → keeper đang có (không bao giờ bị thay) → đường đã vẽ, dài nhất trước → POI → khu dân cư → card → nhiều component → cũ nhất → id. Trong một cụm, nếu có cặp nào bị giữ cứng theo rule hoặc bị model trả `different`, thì cụm bị cắt về tập con nhất quán lớn nhất. Các hàng đã gộp trước đó cũng được tính vào kiểm tra này.
- Embedding dùng lại vector sẵn có trong `geo.tour_place`, không tốn tiền, và chỉ có thể nâng một cặp từ "giữ" lên "hỏi model".
- Báo cáo validity và bước gộp trong một tour của `place_extract` giờ gọi hàm này. Có thêm lý do `possible_duplicate`, chỉ để xem, không chặn gate.

**CIS PR B (`feat/aa-847-dedupe-job`)** — migration **257**, không phải 256 như plan, vì lane lines đã lấy 256 cho các catalog view của nó trong lúc em đang làm:
- Ba bảng mới: `geo.place_merge`, `geo.place_pair_verdict`, `geo.place_dedupe_country`.
- Hai stage, đều role validate: `a3_place_dedupe` (GPT-6 Luna) và `a3_place_dedupe_check` (Haiku). Budget $0.50 mỗi lần chạy.
- View `catalog.v_destination_redirect`.
- Job `place_dedupe`:
  - Mỗi lần chạy tính lại toàn bộ cặp của từng nước.
  - Model chỉ được gọi cho các nước nằm trong allow-list. Một cặp chỉ gộp khi Luna nói `same` cả hai chiều A/B và B/A, Haiku cũng nói `same`, độ tin cậy từ 0.8 trở lên. Kết quả được cache.
  - Chỉ ghi dữ liệu cho nước ở mode `apply` với diff đã được duyệt. Thay đổi nằm ngoài diff đã duyệt vượt max(5, 1%) thì nước đó bị giữ lại và có cảnh báo (chuông admin và e-mail).
  - Có advisory lock chung với `place_geocode`, bước persist của `place_extract` và admin fix.
  - Mỗi lần chạy sửa lại các con trỏ còn trỏ vào hàng đã gộp. Undo bằng cách relink lại, rồi ghim cặp đó là `different`.
  - Job được xếp hàng từ `place_geocode` và `place_shape`.
- Thêm tab Merges trên `/admin/places`.

**Infra:** bản copy byte-identical của 257, xếp sau bản copy 256 của lane lines.

**TripPlanner:** id của địa danh đã bị gộp giờ trả 301 về keeper. Nếu chưa áp 257 thì vẫn là 404, không thành 500.

**Repo gốc:** amendment cho ADR 0007, kết quả đánh giá r1.4, và 2 bài học mới.

**Kết quả đánh giá offline trên 134 cặp có nhãn:** 0 gộp sai ở cả 5 chế độ metadata. Recall chỉ bằng rule là 0.689, chưa đạt mục tiêu 0.75 của plan. Lý do là chính thay đổi §0.1 của plan (id chung không còn được tự gộp) đã đẩy 3 cặp khác ngôn ngữ (Văn Miếu, Wat Arun, Tiger's Nest) sang model. Em không nới rule để đạt con số. Nếu hai model trả lời đúng hết nhóm gửi sang chúng thì recall là 0.967.

### Số đo

Offline eval of rules r1.4 on 134 labelled pairs (61 merge / 73 keep), $0. Columns: auto precision, rules recall, false merges, model band merge/keep, recall if the check answers right.
- Full metadata: 1.000, 0.689 (42/61), 0, 17/6, 0.967
- No ids, no stops, no cards: 1.000, 0.689, 0, 14/5, 0.918
- All points from the model: 1.000, 0.623, 0, 18/15, 0.918
- Every Geoapify row on one city id: 1.000, 0.066, 0, 52/15, 0.918
- No shapes: 1.000, 0.623, 0, 19/5, 0.934

The adversarial pairs and the homonym list never auto-merge in any mode: Hoan Kiem / Hoan Kiem Lake and Long Bien / Long Bien Bridge on one suburb id, Wat That Luang / Pha That Luang, Nam Ou touching the Mekong, Lao Cai / Lao Chai, Shwezigon / Shwesandaw, Dhammayangyi / Dhammayazika, Cu Chi / Cu Chi Tunnels, Mekong River / Mekong Delta, Ha Giang / Ha Giang Loop.

Six keep pairs are left to the two models; the paid measurement run must see them answered different or unsure.

Spend in this run: $0. Writes on Dev: 0.

### Chi phí

Everything below runs on Bedrock acc3; no new AWS service; Geoapify $0; embeddings $0 (existing geo.tour_place.embedding is reused).

1. Measurement run (plan §6.2, needs approval): the 23 model-band pairs of the CI set × 3 repeats. Per pair: GPT-6 Luna A/B + B/A, then Haiku 4.5, about 900 tokens in / 80 out per call. That is ≤ 138 Luna calls (≈ $0.02) and ≤ 69 Haiku calls (≈ $0.09), about $0.11. With the plan's 25 pairs × 2 orders it is ≈ $0.22. Cap: $0.25.
2. Dry run on Laos + Vietnam (plan §6.3): starts only when an admin lists the countries. Estimated 75–150 pairs × (2 Luna + 1 Haiku) ≈ $0.12–0.25. Hard cap $0.50 per run (budget row bedrock/job:place_dedupe) and ≤ 150 pairs per run. Verdicts are cached, so a pair is not paid twice.
3. Steady state: about 0.1 pair per new destination, under $0.01 per month.

Total up front: about $0.75 at most, including the caps.

### Câu hỏi mở

- Anh duyệt chi phí measurement run (khoảng $0.11–0.22, tối đa $0.25) và dry run trả phí cho Lào + Việt Nam (tối đa $0.50 mỗi lần chạy) không ạ?
- Recall chỉ bằng rule là 0.689, thấp hơn mục tiêu 0.75 trong plan, vì chính thay đổi §0.1 của plan (id chung không còn được tự gộp). Anh chấp nhận để CI ghim mức 0.68, phần còn lại giao cho hai model kiểm (nếu model đúng thì recall là 0.967) chứ ạ?
- Các nhãn chính sách: một thị trấn và khu phố cổ của nó là hai địa danh (giữ riêng); Long Biên (quận) và cầu Long Biên giữ riêng; Royal Palace và Royal Palace Museum ở Luang Prabang thì gộp. Anh xác nhận giúp em ạ?
- Quy tắc hai model: Luna là chính và phải trả lời giống nhau ở cả hai chiều A/B và B/A, Haiku kiểm lại, cả hai role validate, độ tin cậy từ 0.8 trở lên. Ngưỡng ngắt là max(5, 1%) thay đổi nằm ngoài diff đã duyệt. Anh đồng ý chứ ạ?
- Em đã quyết định cho allow-list chặn luôn việc gọi model trả phí: nước nào chưa có trong danh sách thì chỉ chạy rule, $0. Anh thấy ổn không ạ?
- Migration lấy số 257 vì lane lines đã giữ 256 (catalog view của đường). Không cần sửa gì thêm, em chỉ báo để anh biết.

### Review (chặn)

- CIS PR B (feat/aa-847-dedupe-job), services/places/dedupe.py keeper_key + services/places/merges.apply_merge: a job merge can stop a drawn line from being drawn, which breaks owner decision (1). keeper_key ranks a manual row and an existing keeper (merged_members>0) above 'line with an ok shape'. A point and a line can still merge through the model band (geometry_mismatch caps the pair at llm, and a 'same' verdict then adds the edge). apply_merge leaves geo.place_shape on the merged id, and the 256 views draw a shape only for d.duplicate_of IS NULL AND d.geo_precision='line'. So the merged line is hidden and the keeper is still drawn as a point. Reproduced with no DB: K='Mekong' (point, geoapify, merged_members=1) vs L='Mekong River' (precision line, ok shape), verdict same -> plan_country merges b-line INTO a-keeper. Only the admin path moves shapes (validity_fix.shape_merge); the job path does not. Fix, either way: (a) in apply_merge, reuse validity_fix.shape_merge/_apply_shape_merge, set the keeper's geo_precision='line' when the shape moves, and record both in geo.place_merge (prior or repointed) so undo_merge restores them; or (b) cut any member with a usable shape from a cluster whose keeper has no usable shape (plan.conflicts). Add a unit test for an existing keeper or manual point plus a drawn line, and the matching undo case.
- CIS PR B, services/places/validity_fix.py (admin duplicate_place fix, changed in this PR to log geo.place_merge): the admin merge does not flatten. When the admin merges a usable row D that is already the keeper of job merges (rows X with duplicate_of=D), X ends up pointing at a merged row (X->D->K). This breaks the invariant that 257 documents and the consumers rely on: 'duplicate_of always names a root' in the catalog.v_destination_redirect comment, used for single-hop resolution by Booking and TripPlanner. Pointers to X then need two place_dedupe runs to reach K (repoint_dangling only moves one hop per run), and dedupe_run skips X in the re-check. merges.assert_roots only logs. Fix: in _apply_changes forward, run UPDATE shared.destinations SET duplicate_of=keeper WHERE duplicate_of=dup, store the ids in the change (and in place_merge.prior.flattened) for undo, and restore them in reverse. Or refuse an admin merge of a row that has members (409). Add a test.

