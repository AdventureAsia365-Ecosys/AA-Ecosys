# AA-779 — Tư vấn FAQ / People Also Ask (PAA): vì sao rỗng, lấy câu hỏi thật ở đâu, Done-when

S245 r2, 20/10/2026. Tác nhân: Claude Code (subagent, chỉ đọc). Không gọi API trả phí, không chạy SQL:
mọi câu SQL bên dưới để orchestrator chạy (ECS exec, `DATABASE_URL` của container = `cis_app`, chỉ SELECT).
Code trích theo `apps/AA-CIS-App` (local `main` khớp `origin/main` ở các file này; riêng phần AA-779 mới
merge (#870) thì đọc từ `origin/main`). Tên bảng/cột lấy theo `docs/architecture/db-schema-reference.md`
(Verified 2026-10-20 01:02 UTC).

---

## 0. Trả lời ngắn cho anh

- **Không ai bỏ PAA.** PR #870 (AA-779) đã đưa PAA vào bài blog: vào writer, bản viết lại (rewrite) và
  `write_faq` dưới dạng SEARCH QUESTIONS. Lần này cả 8 bài không dùng câu nào vì **dữ liệu vào rỗng**,
  không phải vì code bỏ qua.
- **Vì sao rỗng (giả thuyết mạnh nhất, cần SQL xác nhận):** T8/T9 chỉ đọc PAA ở **cấp tour**
  (`silver_aa_internal.seo_context`). PAA cấp tour lấy từ **một** lần gọi SERP cho seed là **tên tour**
  ("Khovsgol and gobi tour mongolia"). Truy vấn dài và hiếm như vậy Google thường không hiện ô PAA.
  SERP vẫn trả `related_searches` ("… price", "… reviews", "… cost") nên ta biết lần gọi đã thành công;
  chỉ là trên trang kết quả không có ô PAA.
- **Trong khi đó, câu hỏi thật cấp ĐỊA ĐIỂM có lẽ đã nằm sẵn trong DB** mà T9 không đọc:
  `acp_contract.search_demand.people_also_ask` (SERP cho từ khoá của từng địa điểm, ví dụ "lake khovsgol")
  và `acp_contract.atom_matches` (câu PAA đã được gắn vào atom bằng embedding và đã qua hai cổng Jev về
  phạm vi). Theo S228, 11.076/82.446 dòng ranking có câu hỏi.
- **Đề xuất:**
  - **Chính:** T9 lấy câu hỏi ở cấp địa điểm/Segment của chính bài viết, tốn $0. Địa điểm nào vẫn trống
    thì phía admin mua bù một SERP cho từ khoá chính của địa điểm, có `people_also_ask_click_depth=2`,
    khoảng $0,0023/địa điểm (live).
  - **Dự phòng:** DataForSEO Google Autocomplete với tiền tố câu hỏi, $0,0006/lần gọi (standard queue).
  - Câu hỏi do LLM tự nghĩ ra **không bao giờ** được tính là "câu hỏi người dùng thật".
- **Done-when mới** đặt câu hỏi thật vào trung tâm. Điều kiện về độ phủ được đo trên toàn bộ Subject blog,
  và nếu không đạt thì issue **không Done**. Dòng điều kiện cũ "vacuous nếu snapshot rỗng" được bỏ (xem §4).

---

## 1. PAA đến từ đâu: lần theo code

### 1a. Cấp tour: `silver_aa_internal.seo_context` (đường S1 / A-series)

| Bước | Ở đâu | Chi tiết |
|---|---|---|
| Job | `services/jobs/s1_seo_prefetch_job.py:57,63` | `s1_seo_prefetch` (admin), market = `resolve_buyer_market(target_market)` của tenant chạy job (master = AA internal); lỗi → mặc định US/en (`:28-30`). |
| Seed | `services/seo_intelligence/s1_prefetch.py:58-70` (`tour_spec`) → `seed_builder.py:147-167` (`build_seed`) | Ưu tiên `"{activity} in {country}"`, nếu không có thì **tên tour + country**. Tour Khövsgöl–Gobi ra seed "Khovsgol and gobi tour mongolia". `related_keywords` trong snapshot ("Khovsgol and gobi tour mongolia price/reviews/cost") khớp đúng seed này. |
| PAA từ cache trước | `s1_prefetch.py:153-168` (`cached_ideas`), query `:306-308` | Lấy PAA từ `acp_contract.search_demand` cho keyword **chứa một title place term** (`title_place_terms`, `seed_builder.py:198-214`, ví dụ "khovsgol", "gobi"), chỉ trong **market của job**, `search_volume > 0`, tối đa 5 câu/keyword, 10 câu tổng. So khớp bằng substring, nên các cách phiên âm khác ("khuvsgul", "hovsgol") không khớp. |
| SERP mua | `s1_prefetch.py:381-391` | **Chỉ khi cache không có PAA**: `client._serp_advanced(s["seed"], …)` → `_parse_paa` + `_parse_related`. |
| Lệnh gọi DFS | `services/seo_intelligence/dataforseo_client.py:235-262` | `POST /v3/serp/google/organic/live/advanced`, payload chỉ có `language_code`, `location_code`, `keyword` (`:242-246`). **Không** có `people_also_ask_click_depth`, **không** có `device` (mặc định desktop), không có `depth` (mặc định 10). |
| Parse | `dataforseo_client.py:427-437` | Item `type == "people_also_ask"`, lấy `items[].title`, tối đa 10. `related_searches` ở `:525-539`. |
| Lưu | `s1_prefetch.py:261-275` → `shared/repository/seo_context_repository.py` (upsert `ON CONFLICT (tour_id)`) | `seo_context.people_also_ask` (jsonb), `related_keywords`, `keyword_search` (= seed), `cache_key` (`seo:<seed>:<loc>:ideas_v3`), `fetched_at`. Mỗi tour **một dòng** (`seo_context_tour_id_key` UNIQUE). |
| Dùng lại | `s1_prefetch.py:37,171-178` | `REUSE_DAYS=180`: suốt 180 ngày tour không được mua lại, kể cả khi `search_demand` đã có PAA mới. |
| Log chi phí | `dataforseo_client.py:84-95` | `shared.dfs_call_log` (endpoint `serp_advanced`, `keyword`, `location_code`, `tour_id`, `cost_usd`), **không ghi `meta`** cho live call, nên không xem lại được trang SERP đã trả những loại item nào. |

Đường cũ `handler.process_seo` → `fetch_all` (`handler.py:186`, `dataforseo_client.py:339-407`) cũng là một
SERP cho cùng seed, cùng không có click depth.

### 1b. Cấp địa điểm: `acp_contract.search_demand` + `acp_contract.atom_matches` (đường A3 / Segment research)

| Bước | Ở đâu | Chi tiết |
|---|---|---|
| Chọn keyword | `services/acp_contract/segment_research_batch.py:66,310-337` | Mỗi địa điểm lấy **1** keyword có volume cao nhất (`SERP_KEYWORDS_PER_PLACE = 1`), chỉ ở các market keyword đó có volume. |
| SERP | `services/acp_contract/segment_research.py:382-421` (`_serp_tool`) | Cùng `_serp_advanced` (không có click depth), mỗi market một lần gọi. |
| Lưu PAA | `segment_research.py:297-307` (`_store_paa`) | `UPDATE acp_contract.search_demand SET people_also_ask` theo `(keyword, market)`. **Không làm gì khi danh sách rỗng** (`:298-299`). |
| Gắn vào atom | `services/acp_contract/atom_ranking.py:428-445` (shortlist theo tên), `:728,730` (Jev `a3_question_scope` + `a3_question_landing`), `:751` → `:473-539` | Embedding match, ghi `acp_contract.atom_matches (query, kind='question', atom_id, distance, matched_by, matched_at)` (`:530-536`). Mỗi Segment có `atom_segment.questions_count`. |
| Ai đọc | — | **Chỉ phần ranking** (trục `questions`). Ngoài các lệnh ghi ở trên, `git grep atom_matches` không thấy chỗ nào khác đọc bảng này. T8/T9 **không** đọc. Bảng chỉ upsert, không có lệnh xoá, nên một câu sau này bị Jev loại có thể vẫn còn lại trong bảng (cần lọc theo `matched_at` hoặc kiểm lại). |

### 1c. Blog T8 → T9 (snapshot của request)

| Bước | Ở đâu | Chi tiết |
|---|---|---|
| T8 đọc tín hiệu | `services/acp_angle_gate/service.py:159-167` → `services/acp_shared/dfs_relevance.py:84-90,141-170` | `fetch_search_demand_signal(trip_id)`: lấy dòng `seo_context` **mới nhất của tour** (`people_also_ask`, `related_keywords`, `keyword_ideas`). Không theo địa điểm, không theo market của tenant. |
| T8 chụp snapshot | `acp_angle_gate/service.py:221,233-242` | `angle_gate_request.dfs_paa_snapshot = asdict(SearchDemandSignal)`, đông cứng tại thời điểm đặt goal (AA-501). Sau này `seo_context` có đổi thì snapshot vẫn giữ nguyên. |
| T8 ranking | `acp_angle_gate/service.py:197` | `asked_questions = search_demand.people_also_ask`, lấy cùng nguồn. |
| T9 đọc | `services/acp_content_writing/service.py:1208-1209,1227` (origin/main) | `people_also_ask` lấy từ snapshot, tối đa `PAA_RAW_MAX = 12` (`:327`). |
| T9 lọc | `service.py:1418-1421` → `quality_gates.py:2030-2068` (`paa_for_scope`, `PAA_MAX_QUESTIONS = 6` `:2010`) | Bỏ câu nhắc địa điểm ngoài phạm vi, câu nguồn không trả lời được, câu không nêu địa điểm của bài và chung dưới 2 từ với seed. |
| Không mua DFS | CONTEXT.md bảng Ownership dòng 4 (AA-646) | Thao tác của tenant không bao giờ mua DataForSEO, nên T8/T9 chỉ đọc dữ liệu có sẵn. |

**Kết luận phần 1:** bài blog viết theo một **Route/Segment** (ví dụ chặng chỉ có Khövsgöl), nhưng câu hỏi
lại lấy từ **SERP của tên cả tour**. Đây là chỗ lệch cấu trúc. Câu hỏi nằm đúng cấp (địa điểm/Segment)
thì đã có ở `search_demand` / `atom_matches` mà không đi tới T9.

---

## 2. Vì sao cả hai request đều rỗng: giả thuyết xếp hạng + cách kiểm

Dữ kiện đã có (`.tmp-session/paafaq/step0.json`): cả hai request trỏ **cùng một tour**, `snapshot_present=true`,
`snapshot_paa=[]`, `related_keywords` có 8 mục, `seo_context_paa=[]`, `seo_context.fetched_at = 2026-10-02 11:25 UTC`.
Request được tạo ở r5 (S235, 14/10), sau khi có dòng `seo_context`.

Thay `:rid` bằng `'1dfbf5e6-bf67-45a3-84c8-7fc37d62868a'` (Atlas & Hearth) hoặc
`'3bf7a5f7-7ddc-45f2-af25-ca1a81b49d21'` (Terra Family).

**Q0. Ngữ cảnh request** (chạy trước):
```sql
SELECT request_id, tenant_id, atom_id, trip_id, channel, subject_id, route_segment_ids,
       jsonb_typeof(dfs_paa_snapshot) AS snap_type,
       dfs_paa_snapshot -> 'people_also_ask' AS snap_paa
FROM acp_shared.angle_gate_request
WHERE request_id IN ('1dfbf5e6-bf67-45a3-84c8-7fc37d62868a','3bf7a5f7-7ddc-45f2-af25-ca1a81b49d21');
```

### H1 (khả năng cao nhất). Seed là tên tour, dài và hiếm, nên Google không hiện ô PAA
SERP đã chạy thành công: có related, mà ở S1 thì related chỉ đến từ SERP (`s1_prefetch.py:381-391`).
Nhưng trang kết quả không có item `people_also_ask`.
```sql
SELECT sc.tour_id, sc.keyword_search, sc.cache_key, sc.fetched_at,
       CASE WHEN jsonb_typeof(sc.people_also_ask)='array' THEN jsonb_array_length(sc.people_also_ask) ELSE -1 END AS n_paa,
       CASE WHEN jsonb_typeof(sc.related_keywords)='array' THEN jsonb_array_length(sc.related_keywords) ELSE -1 END AS n_related
FROM silver_aa_internal.seo_context sc
WHERE sc.tour_id = (SELECT trip_id FROM acp_shared.angle_gate_request WHERE request_id = :rid);

SELECT created_at, endpoint, keyword, location_code, cost_usd, fetched_live
FROM shared.dfs_call_log
WHERE tour_id = (SELECT trip_id FROM acp_shared.angle_gate_request WHERE request_id = :rid)
ORDER BY created_at;
```
H1 được xác nhận khi: có dòng `serp_advanced` với `keyword` = tên tour + country, `n_paa = 0`, `n_related > 0`.

Độ phổ biến trên toàn platform (để biết đây là bệnh chung hay chỉ một tour):
```sql
SELECT (keyword_search ILIKE '% in %') AS activity_seed,
       count(*) AS tours,
       count(*) FILTER (WHERE jsonb_typeof(people_also_ask)='array' AND jsonb_array_length(people_also_ask) > 0) AS with_paa,
       count(*) FILTER (WHERE jsonb_typeof(related_keywords)='array' AND jsonb_array_length(related_keywords) > 0) AS with_related
FROM silver_aa_internal.seo_context
GROUP BY 1;
```

### H2 (khả năng cao, và đây là chỗ đáng sửa). Câu hỏi cấp địa điểm có sẵn nhưng T9 không đọc
```sql
-- PAA da mua cho cac dia diem cua chang Khovsgol (nhieu cach phien am)
SELECT keyword, market, search_volume, retrieved_on,
       jsonb_array_length(people_also_ask) AS n_paa, people_also_ask
FROM acp_contract.search_demand
WHERE keyword ~* '(kh?[oöu]v?s?g[oöu]l|h[oö]vsg[oö]l|khuvsgul|tsaatan|dukha|m[oö]r[oö]n|uran.?togoo)'
ORDER BY n_paa DESC, search_volume DESC NULLS LAST;

SELECT canonical_place, market, researched_at
FROM acp_contract.segment_research_log
WHERE canonical_place ~* '(kh?[oöu]v?s?g[oöu]l|h[oö]vsg[oö]l|khuvsgul|tsaatan|dukha|m[oö]r[oö]n|uran.?togoo)'
ORDER BY researched_at;

-- Cau hoi da gan vao Segment cua chinh request (atom cua request + Segment cua Route)
WITH req AS (
  SELECT atom_id, route_segment_ids FROM acp_shared.angle_gate_request WHERE request_id = :rid
), segs AS (
  SELECT asm.segment_id FROM acp_contract.atom_segment_member asm JOIN req ON asm.atom_id = req.atom_id
  UNION
  SELECT jsonb_array_elements_text(req.route_segment_ids) FROM req
   WHERE jsonb_typeof(req.route_segment_ids) = 'array'
)
SELECT s.segment_id, seg.canonical_place, seg.canonical_action, seg.questions_count,
       am.query, am.matched_by, round(am.distance::numeric, 3) AS distance, am.matched_at
FROM segs s
JOIN acp_contract.atom_segment seg ON seg.segment_id = s.segment_id
LEFT JOIN acp_contract.atom_segment_member asm2 ON asm2.segment_id = s.segment_id
LEFT JOIN acp_contract.atom_matches am ON am.atom_id = asm2.atom_id AND am.kind = 'question'
ORDER BY s.segment_id, am.distance NULLS LAST;
```
H2 được xác nhận khi `search_demand` có PAA cho "lake khovsgol"/"khuvsgul" v.v. hoặc `questions_count > 0` /
`atom_matches` có câu cho các Segment của request. (Nếu `route_segment_ids` không phải mảng chuỗi
segment_id thì xem `jsonb_typeof` ở Q0 rồi chỉnh vế UNION.)

### H3. Thứ tự thời gian: PAA địa điểm có sau ngày 02/10, nhưng `seo_context` dùng lại 180 ngày và snapshot T8 bị đông cứng
So `segment_research_log.researched_at` và `search_demand.retrieved_on` (ở H2) với `seo_context.fetched_at`
(2026-10-02) và thời điểm request:
```sql
SELECT request_id, created_at, updated_at FROM acp_shared.angle_gate_request WHERE request_id = :rid;
```
Nếu PAA địa điểm có sau 02/10, hoặc có trước nhưng không khớp (xem H4), thì `seo_context` sẽ không được làm
mới tới ~03/2027 (`s1_prefetch.py:37,171-178`), và snapshot của request cũng không bao giờ đổi
(`acp_angle_gate/service.py:221`).

### H4. Lệch phiên âm / lệch market khi S1 lấy PAA từ cache
`cached_ideas` khớp bằng substring title term ("khovsgol", "gobi"), chỉ trong market của job, và chỉ khi
`search_volume > 0` (`s1_prefetch.py:153-168,306-308`). Keyword "khuvsgul lake" / "hovsgol lake", hoặc PAA
mua ở market UK/AU, đều bị bỏ qua. Kiểm bằng query `search_demand` ở H2: xem cột `keyword` và `market` của
các dòng có `n_paa > 0`.
```sql
SELECT keyword, market, search_volume, jsonb_array_length(people_also_ask) AS n_paa
FROM acp_contract.search_demand
WHERE jsonb_array_length(people_also_ask) > 0
  AND (keyword ILIKE '%khovsgol%' OR keyword ILIKE '%gobi%');   -- dung y logic substring cua cached_ideas
```
Nếu query regex ở H2 ra nhiều dòng hơn query này, nghĩa là S1 đã bỏ sót PAA vì phiên âm.

### H5 (thấp). Parse bỏ sót / thiết bị / thiếu click depth
`_parse_paa` chỉ đọc `items[].title` của item `people_also_ask` (`dataforseo_client.py:427-437`). Theo
docs, mỗi phần tử là `people_also_ask_element` có `title`, `seed_question`, `expanded_element`, nên parse
đúng. Request dùng desktop mặc định, không có click depth: click depth chỉ **thêm** câu khi ô PAA đã có,
không làm ô PAA xuất hiện. Không kiểm lại được bằng dữ liệu cũ vì `dfs_call_log.meta` không lưu loại item
(`dataforseo_client.py:91-95`). Muốn kiểm thì cần mua lại **một** SERP (khoảng $0,002, cần Nghiệp đồng ý)
và lưu `item_types`.

### H6 (đã loại). SERP lỗi / bị filter làm rơi / snapshot chụp trước khi có PAA / luồng blog không có dữ liệu SEO
- SERP lỗi: nếu lỗi thì `related` cũng rỗng (`s1_prefetch.py:386-391`), nhưng thực tế có 8 related. **Loại.**
- `paa_for_scope` làm rơi: danh sách raw đã rỗng ngay từ snapshot, filter chưa kịp chạy. **Loại cho lần
  này**, nhưng sẽ quan trọng khi có dữ liệu (đo bằng `step0_filter.py`).
- Snapshot chụp trước khi có `seo_context`: `fetched_at` 02/10 sớm hơn r5 14/10. **Loại.**
- Luồng blog không có dữ liệu SEO: **đúng một phần.** T8/T9 không bao giờ mua SERP (AA-646) và chỉ đọc
  `seo_context` của tour. Đây chính là nguyên nhân cấu trúc ở H1/H2.

---

## 3. Các phương án lấy câu hỏi thật cho mọi blog/tour

Giá tra ngày **20/10/2026**:
- SERP: <https://dataforseo.com/pricing/google-serp/google-organic-serp-api>
- Click depth, `device`, `depth`, loại item: <https://docs.dataforseo.com/v3/serp/google/organic/live/advanced/>
- Autocomplete: <https://dataforseo.com/pricing/serp/google-autocomplete-serp-api>
- Labs: <https://dataforseo.com/pricing/dataforseo-labs/dataforseo-google-api>
- AlsoAsked: <https://alsoasked.com/pricing>
- Reddit: không có trang giá chính thức; tổng hợp thứ cấp tại <https://octolens.com/blog/reddit-api-pricing>,
  <https://data365.co/blog/reddit-api-pricing>.

| # | Phương án | Chi phí | Đúng "câu hỏi người thật"? | Hợp pipeline? |
|---|---|---|---|---|
| A | **Dùng lại PAA cấp địa điểm/Segment đã có** (`atom_matches` của các Segment trong bài + `search_demand.people_also_ask` của keyword chứa tên địa điểm, ở mọi market của tenant), sau đó mới tới PAA cấp tour | **$0** | Có, đều là PAA của Google, và `atom_matches` đã qua Jev `a3_question_scope`/`a3_question_landing` | Rất hợp: chỉ đọc bảng sẵn có trong T8 (khi tạo snapshot) / T9 `start_write`, rồi vẫn đi qua `paa_for_scope`. Không mua DFS phía tenant (AA-646). |
| B | **SERP mua bù cho từ khoá chính của địa điểm, có `people_also_ask_click_depth=2`** (phía admin, trong Segment research, chỉ cho địa điểm chưa có câu nào) | Live $0,002 + $0,00015/click (≤ $0,0023); standard queue $0,0006 + click (≤ $0,0009). Click không xảy ra thì được hoàn | Có. Click depth mở thêm câu (thường gấp 2–3 lần) khi ô PAA có | Hợp: sửa `_serp_advanced` thêm tham số, lưu vào `search_demand` như cũ. Cùng response có `discussions_and_forums` (tiêu đề thread Reddit/Quora/TripAdvisor kèm `posts_count`), parse **miễn phí** làm nguồn phụ. |
| C | **Google Autocomplete (DFS) với tiền tố câu hỏi** ("is lake khovsgol", "how … lake khovsgol", "what … lake khovsgol", "can you … lake khovsgol", "lake khovsgol vs"): 4–6 lần gọi/địa điểm | $0,0006/lần (standard) hoặc $0,002 (live), khoảng $0,003–0,012/địa điểm | Có (gợi ý từ truy vấn thật), nhưng là mảnh truy vấn, phải chuẩn hoá thành câu hỏi | Hợp làm **dự phòng** cho địa điểm có ô PAA rỗng ngay cả với từ khoá chính. Cần bộ lọc như `paa_for_scope`. |
| D | **Câu hỏi trong `keyword_ideas` / Labs `keyword_suggestions`** (lọc keyword bắt đầu bằng how/what/is/can/best time…) | Ideas đã có sẵn: $0. Labs: $0,012/task + $0,00012/item (50 item ≈ $0,018) | Có volume thật, nhưng là keyword, không phải câu hoàn chỉnh | Phần $0 (lọc `seo_context.keyword_ideas` có sẵn) dùng tốt làm tín hiệu phụ. Labs thì đắt hơn C và trùng phần lớn. |
| E | **Mở rộng từ long-tail lên chủ đề cha** (seed = tên địa điểm/khu vực thay vì tên tour) | Như B | Có | Thực chất là B. Seed S1 cấp tour giữ nguyên cho keyword chính; chỉ nguồn câu hỏi chuyển lên cấp địa điểm. |
| F | Reddit / Quora API trực tiếp | Reddit: $0,24/1.000 call theo công bố 2023, dùng thương mại phải có thoả thuận riêng (con số $12.000 đến từ nguồn thứ cấp, chưa kiểm; **ước tính**). Quora: không có API công khai | Có, nhưng ồn và ToS khó | **Không khuyến nghị.** `discussions_and_forums` trong B đã cho tín hiệu này mà không vướng ToS. |
| G | AlsoAsked (API) | $12 / $23 / $47 mỗi tháng cho 100 / 300 / 1.000 credit (trang ghi giá tháng và giá năm $144 / $276 / $564; trả theo năm rẻ hơn 20%) | Có (bản thân cũng là PAA đào sâu) | **Không khuyến nghị**: thêm vendor + phí cố định hằng tháng mà kết quả trùng B (click depth ra cùng loại dữ liệu, theo đơn giá dùng bao nhiêu trả bấy nhiêu). |
| H | LLM tự sinh câu hỏi | Token | **Không**, không phải nhu cầu thật | Chỉ được dùng làm FAQ dự phòng như hiện nay (khi không có câu thật), **không bao giờ** tính vào độ phủ. |

### Ước tính chi phí cho cả platform (**ước tính**)
`segment_research_log` có khoảng 1.337 dòng (địa điểm × market, theo schema reference).
- B áp cho địa điểm chưa có PAA, giả định khoảng 500 lần gọi: live ≈ $1,15; standard ≈ $0,45.
- C cho khoảng 250 địa điểm vẫn trống × 5 tiền tố × $0,0006 ≈ $0,75.
- Tổng một lần khoảng **$1–2**. Làm mới theo chu kỳ 180 ngày như `FRESH_FOR`/`REUSE_DAYS`.
- Trial trước: khoảng 3 địa điểm (Khövsgöl, Mörön, Uran Togoo), dưới $0,05, theo luật paid-runs-subset.

### Khuyến nghị
- **Chính = A + B.**
  - T8 (lúc tạo snapshot) và T9 lấy câu hỏi theo thứ tự ưu tiên:
    1. `atom_matches` trên các Segment của bài, chỉ lấy dòng có `matched_at` sau lần `questions_count`
       được tính gần nhất.
    2. `search_demand.people_also_ask` của keyword chứa tên địa điểm của bài, ở mọi market của tenant.
    3. PAA cấp tour.
  - Gộp, bỏ trùng, gắn nhãn nguồn, rồi đi qua `paa_for_scope` như hiện nay.
  - Phía admin, Segment research thêm `people_also_ask_click_depth=2` và mua bù SERP cho địa điểm có 0 câu.
    Đồng thời parse `discussions_and_forums` (miễn phí) và ghi `item_types` vào `dfs_call_log.meta` để lần
    sau kiểm được.
- **Dự phòng = C** (Autocomplete với tiền tố câu hỏi), chỉ cho địa điểm vẫn 0 câu sau A+B. Chạy phía admin,
  lưu vào cùng chỗ với PAA nhưng gắn nhãn nguồn `autocomplete`.
- Không dùng F, G, H cho việc đo độ phủ.

Ghi chú thiết kế: snapshot T8 nên lưu thêm `people_also_ask_sources` (nguồn của từng câu) để admin xem được.
Tenant không thấy gì về nguồn hay cổng kiểm (memory tenant-sees-content-only). T8 ranking
(`asked_questions`, `acp_angle_gate/service.py:197`) cũng được hưởng lợi từ cùng danh sách này.

---

## 4. Done-when đề xuất cho AA-779 (thay bản "vacuous")

Bỏ câu "nếu không request nào có PAA trong phạm vi thì dòng này vacuous". Đó chính là trường hợp vừa xảy ra:
Done-when đạt trên giấy nhưng câu hỏi thật không vào bài nào.

1. **Độ phủ ($0, đo bằng SQL/script trên toàn bộ Subject blog đang `proposed`/`picked`, không chỉ 2 request
   checkpoint):** ≥ **80%** Subject blog có **≥ 3** câu hỏi thật trong phạm vi sau chuỗi A → B → C. "Thật"
   gồm PAA, `discussions_and_forums` hoặc autocomplete; LLM tự sinh không tính. "Trong phạm vi" nghĩa là qua
   `paa_for_scope`. Báo cáo tách theo nguồn. Dưới 80% thì **chưa Done**, và phải ghi lại các địa điểm còn
   trống kèm lý do (không có volume / không có ô PAA / autocomplete rỗng).
2. **Được dùng thật (checkpoint 8 blog kế tiếp):**
   - ≥ **6/8** blog có ≥ **2** câu FAQ lấy từ danh sách câu hỏi thật (khớp sau chuẩn hoá, hoặc trùng ≥ 0,8
     token nội dung). `blog8_measure.py` đã có `paa_used`, chỉ cần nới cho các nguồn mới.
   - Trên toàn bộ 8 blog, ≥ **50%** câu FAQ có nguồn thật.
3. **Chất lượng trả lời:**
   - Panel thấy **0** FAQ không trả lời câu hỏi.
   - `F16_faq` hold = 0.
   - Mọi câu FAQ dùng câu hỏi thật đều qua F1 grounding (không có claim nào ngoài seed/FACTS).
   - Câu nguồn không trả lời được thì bị bỏ (`unanswerable_faq_topics`), không được trả lời vòng vo.
   - 40–60 từ mỗi câu trả lời.
   - Câu đầu của câu trả lời nêu chủ thể (`faq_answer_problem` = OK).
4. **Truy vết:** mỗi bài lưu danh sách câu hỏi đã dùng kèm nguồn (trong flag `F7_faq_autofix` /
   `quality_signal`), admin xem được ở `/admin`; tenant không thấy.
5. **Chi phí và ranh giới:**
   - Phần mua bù B/C chạy trong job admin, ghi vào `shared.dfs_call_log`, lần chạy đầu cho cả platform ≤ **$3**.
   - Thao tác của tenant vẫn không mua DFS (AA-646).
6. **Test:** unit test cho thứ tự gộp nguồn, chống trùng, nhãn nguồn, và trường hợp cả 3 nguồn rỗng (FAQ dự
   phòng vẫn chạy, Subject đó được đếm vào phần "chưa phủ").

Trình tự đề xuất:
1. Chạy SQL ở §2 ($0) để chốt H1/H2/H3/H4.
2. Làm A ($0, chỉ code). Đo lại tiêu chí 1: có thể đã đạt khá cao chỉ với dữ liệu sẵn có.
3. Trial B+C trên khoảng 3 địa điểm (< $0,05).
4. Chạy B+C bù cho các địa điểm còn trống.
5. Chạy checkpoint 8 blog (khoảng $0,9–1,3, gộp với đợt trả phí khác).
