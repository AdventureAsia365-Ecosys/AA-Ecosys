# Kiểm tra lan truyền dữ liệu: tour thô → Master → atom → … → TripPlanner (S252)

**Câu hỏi của Nghiệp:** "kiểm tra toàn bộ dữ liệu lan truyền đã đầy đủ chưa, từ tour thô, đến master content, atom,
segment, route, hub, place card... đã được sinh đầy đủ hết chưa hay cần chạy tay hay tự động sinh — cho cả
tripplanner nữa".

**Tác nhân:** Claude Code · **Ngày:** 26/10/2026 (S252) · Chỉ đọc, không ghi dữ liệu, không tốn phí model.

**Nguồn số liệu (mọi con số trong file này đều trích từ đây, kèm tên key):**

| Ký hiệu | Nguồn | Đọc bằng | Thời điểm |
|---|---|---|---|
| `cov` | `coverage.json` (59 câu SQL, `coverage.py`) | `cis_app`, `read_only = on` (`cov → read_as`, `read_only`), `errors = {}` | `cov → as_of` 2026-10-25 23:57:43Z |
| `tp` | `aa990-run.txt` (DB Migrate `run-script`, master, `default_transaction_read_only=on`): TripPlanner, saved-trip pins, CRM cache | master login, read-only | sau 23:00Z 25/10 (CRM full pass 23:00:19Z) |
| `chain` | `chain-map.md`: generator, trigger, flag, giá trị Terraform | đọc code CIS `303ae6e9`, Infra `258b087` | 26/10 |
| `tpchain` | `tripplanner-chain.md`: TripPlanner đọc gì, từ đâu | đọc code TP `52e9e90` | 26/10 |
| `facts` | `SESSION-FACTS.md`: số backfill S252 + probe độ tươi sau backfill (run `40244664055`) | — | 25/10 |

Các file gốc ở `.tmp-session/s252/propagation/` (không commit). Hai dòng `tp_tour_layers` và `tp_place_build` trong
`aa990-run.txt` bị cắt ở 700 ký tự, nên một vài key cuối (ví dụ `without_itin…`, `with_place…`) không đọc được; các
số dùng dưới đây đều nằm trong phần còn đọc được.

"Tour live" = quy tắc `catalog._live_tour` (Master của AA, `master_status = 'active'`, chưa xoá, `raw_tours.source_status = 'active'`).
Hôm nay có **892 tour live** (`cov → master.status`, `tp → tp_tour_layers.live_tours`, `tp → crm_coverage.catalog_tours`).

---

## 1. Tóm tắt (10 dòng)

1. **Đủ, và tự động theo khi Master đổi:** Master → SEO (892/892) → atom (892/892, 0 atom cũ hơn Master) → segment (883/892, 9 còn lại bị loại theo luật) → ranking (883/883, 6 market) → landing PAA (9.040/9.040 segment đã tính) → TripPlanner phần chữ (day list 892/892) → CRM cache (892/892).
2. **Routes:** 700/892 tour (78,5%); 192 tour không có route là do không có chặng đủ điều kiện, đúng thiết kế. **Hub:** chỉ 155/1.261 route hiện hành có hub; con số này lệch với định nghĩa "mọi route có hub" trong `chain`, cần làm rõ.
3. **Thiếu lớn nhất là lớp địa điểm:** chỉ 123/892 nguồn đã build `geo` (13,8%), nên TripPlanner chỉ có component/điểm dừng cho 121 tour (13,6%) và route trên bản đồ cho 122 tour. 769 nguồn chưa build **sẽ không bao giờ tự build** vì `PLACE_PIPELINE_AUTO` đang tắt.
4. **Place card:** mới link 878/25.878 atom (3,4%); 18.755 atom chưa có dòng nào. Việc soạn card là admin bấm tay và có trả phí (AA-784).
5. **Ảnh:** 162/892 tour có ảnh (18,2%); 0/1.182 destination có ảnh. Job sync chạy tự động mỗi ngày, nhưng chỉ ghép được ảnh đã có trong Drive.
6. **Tự động hôm nay:** atomize, segment, ranking, route/hub, landing PAA, relink card ($0), place build **chỉ cho nguồn đã build** (AA-989), purge TripPlanner, sync ảnh hằng ngày, CRM sync hằng giờ.
7. **Chạy tay và trả phí:** nạp Excel, S1 rewrite, build địa điểm lần đầu (AA-905), soạn place card (AA-784), nghiên cứu PAA/`search_demand` (lần cuối 12/10), SEO prefetch.
8. **Lỗi/bất thường:** 322/371 pin chuyến đã lưu không còn component (99/103 chuyến); 14/25 angle request trỏ vào atom đã thay; 10.547 member segment nằm trên atom đã chết; 228 atom không rõ vì sao không có member; `SEGMENT_GC_MODE=apply` chưa vào task đang chạy.
9. **Đề xuất, theo thứ tự:** (a) deploy CIS Dev để `apply` GC; (b) sửa pin treo + trỏ lại angle request + dọn member chết (đều $0); (c) build địa điểm 769 nguồn theo thang 3 → 50 → hết (≈ $5–15); (d) sau đó bật `PLACE_PIPELINE_AUTO`; (e) báo giá rồi soạn place card (dry run trước); (f) làm mới PAA theo market.
10. **Cần Nghiệp quyết:** duyệt chi cho (c), (e), (f); bật `PLACE_PIPELINE_AUTO`; có viết lại 82 Master đang ở model cũ hay không. Câu trả lời đề xuất có ở §6.

---

## 2. Bảng chuỗi đầy đủ, mỗi lớp một dòng

Ký hiệu kết luận: **Đủ** · **Thiếu có lý do** (loại trừ có chủ đích) · **Thiếu cần làm**.

| # | Lớp | Bảng / view | Độ phủ đo được | "Đủ" nghĩa là gì (loại trừ có chủ đích) | Sinh khi nào: tự động / tay / trả phí (flag = giá trị live) | Kết luận |
|---|---|---|---|---|---|---|
| 1 | Tour thô | `silver_aa_internal.raw_tours` | 917 nguồn live; 892 có Master active = **97,3%**; 25 chưa có (`cov → raw.live_sources_vs_master`). Cả 25 đều `latest_version_status = hitl`, `latest_review_status = pending` (`cov → raw.without_master_by_reason`): India 18, Sri Lanka 4, Philippines 2, Nepal 1 (`raw.without_master_by_country`). Ngoài ra 43 trashed, 26 superseded, 1 `hitl_rejected` (`raw.status_breakdown`) | Mọi nguồn live có Master; trừ nguồn đang chờ review, nguồn trùng đã staged, nguồn bị loại | **Tay**: admin `POST /admin/ingest-s3`. Không có S3 event trigger. EventBridge `ACP.DailyIngest` bắn nhưng không rule nào nhận (`chain` §1) | Thiếu có lý do: 25 tour chờ người review |
| 2 | Master content | `gold_aa_internal.published_tours`, `silver_aa_internal.generated_content`, `quality_scores`, `review_queue` | 892/892 active; 892/892 có `quality_score_id` (`cov → master.quality`). `model_editorial`: `satellite-sonnet-5-5` 810, `satellite-haiku-4-5` 81 (mới nhất 10/10), `satellite-sonnet-4-6` 1 (`master.version_meta`). Bản mới hơn đang chờ: 2 `hitl` (từ 10/10), 1 `rejected` (`master.newer_version_waiting`). `review_queue`: pending 43 (mới nhất 14/10), dismissed 148, superseded 80, rejected 3 (`review.queue_status`) | Mọi tour live có Master + quality score; không có bản mới nào nằm chờ lâu | **Tay + trả phí**: S1 do admin chạy (`s1_rewrite`, `s1_batch_ingest`), `S1_WRITER_V2 = on` (Terraform `true`, chỉ worker có, api task không thấy: `cov → api_task_env.S1_WRITER_V2 = null`). Tự publish nếu qua gate, không thì vào review | Đủ, nhưng còn 82 Master ở model cũ và 43 mục review đang chờ (xem §5) |
| 3 | SEO context | `silver_aa_internal.seo_context` | 892/892 = **100%**; 892 dòng `ideas_v3` còn mới; 75 dòng hết hạn, nhưng tour nào cũng có dòng `ideas_v3` mới để dùng lại; 634 tour có PAA; 892 có top keywords (`cov → seo.coverage`, `seo.provider` = `dataforseo` 892). Probe: `seo_context_expired_active_tours` 0 (`facts` dòng 30) | Mọi tour live có dòng; dòng mới nhất là `ideas_v3` còn mới (< 180 ngày) | Tự động **bên trong S1** (DFS trả phí, trừ khi dùng lại `ideas_v3` 180 ngày, `S1_SEO_REUSE_DAYS` không đặt nên = 180). `s1_seo_prefetch` là admin chạy tay (lần cuối 10/10, `cov → jobs.chain_last_success`) | Đủ |
| 4 | Atoms | `acp_contract.tour_atoms` (+ `v_active_tour_atoms`) | 892/892 = **100%**; 25.878 atom active, toàn bộ là atom địa điểm; `atoms_older_than_master` 0; `atoms_without_action` 0 (`cov → atoms.coverage`). Lịch sử: 28.235 dòng đã xoá mềm, 283 marker (`atoms.inactive_rows`) | Mọi tour live có ≥1 atom active; không có atom cũ hơn Master | **Tự động** sau publish (`a3_atomize`, trả phí: 30 ngày $5,1962 / 55.451 call, `cov → cost.llm_by_stage_30d`). 7 ngày qua: 815 job thành công (`jobs.chain_7d`) | Đủ |
| 5 | Segments | `acp_contract.atom_segment`, `atom_segment_member`, `atom_segment_alias` | Tour: 883/892 = **99,0%** (`cov → segments.tour_coverage`); 9 tour thiếu đều `all_excluded_by_rule` (`facts` dòng 21, 30). Atom: 9.008 không có member, gồm 8.780 bị loại theo luật và **228 không giải thích được** ở 157 tour (`segments.no_member_classified`). Kho: 11.308 segment, 10.396 có member active, 912 không có (`segments.inventory`). **10.547/27.712 dòng member nằm trên atom đã chết** (`segments.dead_member_rows`) | Mọi atom địa điểm mà `forms_segment()` nhận đều có member; 0 member trên atom chết; 0 orphan không ai tham chiếu. Loại trừ: transit / unnamed_place; orphan còn được alias / subject / brand-fit / angle tham chiếu | **Tự động** trong job atomize (Jev `a3_segment_match`, 30 ngày $0,1635); GC chạy trong mỗi lần `recompute` platform. `SEGMENT_GC_MODE`: Terraform `apply` (Infra #400) nhưng lần recompute cuối vẫn `mode = report` (`cov → jobs.recompute_segment_gc_last[0]`, 20:55:53Z) | Thiếu cần làm: 228 atom không giải thích được, 10.547 member chết, GC chưa ở `apply` |
| 6 | Ranking | `acp_contract.atom_ranking` | 883/883 tour có segment đều được xếp hạng = **100%**, `segmented_but_unranked` 0 (`cov → ranking.tour_coverage`). Mỗi market AU/DE/FR/NL/UK/US: 15.987 dòng, 13.863 có hạng, 2.124 bị loại, mới nhất 20:54–20:55Z 25/10 (`ranking.by_market`) | Mọi cặp (tour, segment) có member active đều có dòng hiện hành ở mọi market; dòng transit/unnamed giữ lại nhưng không xếp hạng | **Tự động** (stage `score` trong `recompute`; Jev `a3_demand` $3,4808 và `a3_segment_type` $2,8921 trong 30 ngày) | Đủ |
| 7 | Routes + hubs | `acp_contract.route`, `hub` | Route: 700/892 tour = **78,5%**, 1.261 route hiện hành, 9.917 superseded (`cov → routes.by_country`, `routes.hubs`). Hub: 82 hub, 19 được route hiện hành dùng; **1.106/1.261 route hiện hành không có hub** (155 có = 12,3%) | Route khớp `derive_routes` (probe: `routes_missing`/`routes_differ` = 0, `chain` §4); 192 tour không có chặng đủ điều kiện (≥2 ngày liền, ≥2 địa điểm) thì không có route, đúng thiết kế. `chain` §3 ghi "every current route has a hub", nhưng số đo không khớp | **Tự động** (stage `route` trong `recompute`, $0) | Route: Đủ. Hub: Thiếu cần làm (làm rõ định nghĩa, §5.6) |
| 8 | PAA: `search_demand`, landing, question embedding | `acp_contract.search_demand`, `atom_segment.questions_count`, `atom_matches`, `question_embedding` | Landing: 9.040/9.040 segment có hạng đã tính = **100%**; 1.122 có câu hỏi, 7.918 có 0 câu hỏi (`cov → paa.ranked_segment_landing`). `atom_matches` 14.902 dòng / 3.518 atom (`paa.atom_matches`). `question_embedding` 1.009 (`paa.question_embedding`). Dữ liệu nguồn `search_demand` mới nhất: AU 28/09, UK 28/09, US 30/09, DE/FR/NL 12/10; riêng nhóm không gắn market (5.097 keyword) và `US-PAA2` (8 keyword) có dòng mới nhất 20/10 (`paa.search_demand`); `segment_research` thành công lần cuối 12/10, tổng cộng 6 lần (`jobs.chain_last_success`) | Mọi segment có hạng đều có `questions_count` (khác NULL). 0 câu hỏi là kết quả hợp lệ khi `search_demand` không có PAA cho địa điểm/market đó | Landing **tự động** (`recompute` stage `landing`, Jev `a3_question_landing` $1,0819 / 30 ngày). **Nguồn `search_demand` chỉ có khi admin chạy, trả phí DFS** (`segment_research`; script `aa779_serp_topup` qua ECS exec) | Landing: Đủ. Dữ liệu nguồn: Thiếu cần làm (cũ từ 2–4 tuần, địa điểm mới chưa có) |
| 9 | Atom embeddings | `acp_contract.atom_embedding` (view `place`, `place_action`) | Trong phạm vi landing: 1.982/2.047 atom có đủ 2 view = **96,8%**, 65 atom không có view nào (`cov → emb.atom_embedding_landing_scope`). 10.826 dòng, trong đó 6.300 nằm trên atom không active (cache) (`emb.atom_embedding_totals`). `published_tours.content_embedding` khác NULL: 0 (cột chết, đúng thiết kế); `content_piece` 305/346 có vector (`emb.dead_and_tenant_columns`) | Atom của segment có `questions_count > 0` có đủ 2 view; atom ngoài phạm vi landing không cần (AA-989 D1) | **Lười**: được tạo trong lượt landing (Cohere `f10_embed` $0,1196 / 30 ngày) | Đủ (65 atom thiếu sẽ được bù ở lượt landing sau, $0) |
| 10 | Geo: `tour_place` / destinations / tour graph / shapes | `geo.tour_build`, `tour_day`, `tour_place`, `place_name`; `shared.destinations`; `geo.graph_build`, `tour_stop`, `tour_leg`…; `geo.place_shape` | Build: **123/892 = 13,8%**, 123/123 trên `tour_id` hiện hành (`cov → geo.build_status`). Component: 2.152 dòng, 1.843 được phục vụ, 309 không có destination, 0 trên atom chết, 2.152/2.152 có vector (`geo.by_country`, tổng). `place_name`: resolved 1.897, unknown 217, pending 189 (`geo.place_name_status`). Destinations: 1 dòng `suspect` (đã merge), còn lại `ok` (`geo.destinations`). Graph hiện hành 20:53:43Z: 434 node, 1.005 stop, 5.149 leg, 122 nguồn có stop; 122/123 nguồn đã build nằm trong graph, 0 build mới hơn graph (`geo.graph_current`, `geo.graph_vs_built`). Shape (line): ok 17, approximate 23, not_found 8, failed 2 (`geo.place_shape`) | Mọi nguồn live có build `ok` trên `tour_id` hiện hành; 0 `tour_place` trên atom chết (probe `geo_tour_place_stale_rows` = 0, `facts` dòng 30); graph mới hơn build mới nhất | **Tự động chỉ cho nguồn đã build** (AA-989 `maintain_built`). `PLACE_PIPELINE_AUTO` không đặt nên tắt (`cov → api_task_env.PLACE_PIPELINE_AUTO = null`). Nguồn mới: admin `POST /admin/places/backfill` (trả phí `a3_place_days`, `a3_place_embed`, `a3_place_locate`). Geocode/shape/graph tự chạy sau đó; `PLACE_SHAPES_ENABLED = on` (`api_task_env`) | Thiếu cần làm: 769 nguồn chưa build (AA-905) |
| 11 | Place cards | `acp_shared.place_card`, `place_card_alias`, `place_card_miss`, `atom_place_card` | 25.878 atom địa điểm: **link 878 (3,4%)**, dòng miss 6.245, **không có dòng 18.755**, đã giải quyết (link + miss) 27,5%; 160/892 tour có ít nhất 1 card (`cov → cards.by_country`, tổng). Lý do miss: unnamed 5.349, logistics_place 895, no_name 1 (`cards.miss_reasons`). Kho card: 112 card `auto_checked` (66 + 46), đã tốn $0,9668 (`cards.inventory`). `place_cards_build` chạy lần cuối 13/10, 5 lần tổng cộng (`jobs.chain_last_success`) | Mọi atom địa điểm của tour live có dòng `atom_place_card` (link hoặc miss có ghi lại). Atom bị luật bỏ qua → miss, đúng thiết kế | Relink **tự động, $0** trong atomize (chỉ link vào card đã có; backfill S252: 891 tour, 773 link, 0 soạn mới, `facts` dòng 22). **Soạn card mới: admin bấm tay hoặc T8 theo yêu cầu, trả phí** (`a3_place_card`, `a3_place_card_check`) | Thiếu cần làm (AA-784) |
| 12 | Ảnh | `shared.place_photo`, `catalog.v_tour_photo`, `v_destination_photo` | Tour: **162/892 = 18,2%** có ảnh trên `tour_id` hiện hành, 0 tour chỉ có ảnh ở bản cũ (`cov → photos.by_country`). Ảnh: matched auto 2.395, matched manual 234, unmatched 603; **mọi ảnh đều `has_destination = false`** (`photos.status`). **Destination được phục vụ có ảnh: 0/1.182** (`photos.served_destinations`) | Mọi tour live có ≥1 ảnh; mọi destination được phục vụ có ≥1 ảnh. Loại trừ: tour không có thư mục Drive | **Tự động hằng ngày** (EventBridge 21:00 UTC → `photo_sync`; 35 lần chạy trong 7 ngày, `jobs.chain_7d`), $0, nhưng chỉ ghép ảnh đã có trong Drive | Thiếu cần làm (ảnh destination = 0 nhiều khả năng do lỗi ghép theo nhãn, chưa xác minh; ảnh tour cần nguồn ảnh) |
| 13 | Tenant: angle request | `acp_shared.angle_gate_request`, `angle_gate_option` | 25 request: approved 21, pending_choice 2, pending_goal 2; **14 trỏ vào atom không active** (11 + 2 + 1) (`cov → tenant.angle_requests`); probe `angle_gate_requests_on_inactive_atoms` 14 (`facts` dòng 30) | Không có catalogue target. Sức khoẻ: 0 request trên atom chết | Tenant tự tạo (T8, trả phí `t8_angle_*`) | Thiếu cần làm (trỏ lại, AA-988) |
| 14 | Tenant: subjects | `acp_shared.subject` | proposed 383, used 18, picked 4, cut 2 (`cov → tenant.subjects`, cộng theo kênh) | Không có catalogue target | Tenant (T7) | Đủ (theo yêu cầu) |
| 15 | Tenant: content pieces | `acp_shared.content_piece` | 346 bài: linkedin approved 128 / held 36, blog approved 85 / held 96, facebook approved 1 (`cov → tenant.content_pieces`); 305/346 có vector (`emb.dead_and_tenant_columns`) | Không có catalogue target | Tenant (T9, trả phí; `t9_write` $18,321 / 30 ngày) | Đủ (theo yêu cầu) |
| 16 | Tenant: tenant versions | `gold_aa_internal.tenant_tour_versions` | 15 tour tenant; **2 cũ hơn Master**; 0 trên Master không active (`cov → tenant.versions_vs_master`) | Bản tenant không cũ hơn Master | Tenant (T2) | Thiếu nhẹ: 2 bản cũ hơn Master (tenant quyết định viết lại hay không) |
| 17 | Tenant: trip pages | `acp_deliver.tenant_tour_pages` | 0 dòng (`cov → tenant.trip_pages = []`) | Không có catalogue target | Tenant | Đủ (chưa có tenant nào dùng) |
| 18 | Supply | `shared.supply_entity`, `supply_content_version` → `catalog.v_supply_content` | 2 entity (1 hotel, 1 service), cả hai đều `active = false`, `content_status = unpublished`, đã từng có bản published (`cov → supply.entities`). Version: approved 2, superseded 2, draft 1, rejected (human) 1 (`supply.versions`). `supply_content_draft` trong 7 ngày: 5 thành công, **3 lỗi** (mới nhất 13:46Z 25/10) (`jobs.chain_7d`) | Mọi entity active có bản published | **Tự động** kéo feed (`SUPPLY_FEED_PULL` không đặt nên bật), soạn nháp trả phí (`supply_content_writer`), nhân viên duyệt | Đủ (0 entity active); 3 job lỗi để xem lại |
| 19 | Catalog views | `catalog.v_tour`, `v_tour_day`, `v_tour_component`, `v_tour_place`, `v_graph_node`, `v_destination`, `v_tour_photo`… | `v_tour` = 892 (`tp → tp_tour_layers.live_tours`, `crm_coverage.catalog_tours`) | Giống các bảng bên dưới | View sống, $0 (`chain` §1 hàng 19) | Đủ (phản ánh đúng lớp bên dưới) |
| 20 | TripPlanner: day list | `catalog.v_tour_day` | **892/892 = 100%** (`tp → tp_tour_layers.with_day_list`) | Mọi tour live có ≥1 dòng ngày | Tự động (view sống; cache TP 30 phút) | Đủ |
| 21 | TripPlanner: địa điểm trên trang tour | `catalog.v_tour_place` | 892/892 tour có địa điểm; 627 tour có ít nhất 1 địa điểm có toạ độ (70,3%); 265 tour không có địa điểm nào có toạ độ (`tp → tp_tour_layers.with_places`, `with_located_places`, `places_none_located`) | Mọi dòng địa điểm có `lat`/`lng` | Tên: tự động sau atomize. Toạ độ: cần build địa điểm hoặc destination đã có | Thiếu cần làm (theo lớp 10) |
| 22 | TripPlanner: components / stops | `catalog.v_tour_component` | **121/892 = 13,6%** tour có component; 1.843 component được phục vụ, 0 cũ (stale) (`tp → tp_tour_layers.with_components`, `tp_components`); 0 component chỉ dựa trên atom đã thay (`tp_component_atoms.on_replaced_atoms_only`) | Mọi tour live có ≥1 component được phục vụ, `is_stale = false` | Đọc sống `geo.tour_place`; nguồn chưa build thì không có gì | Thiếu cần làm (theo lớp 10) |
| 23 | TripPlanner: legs / route trên bản đồ | `catalog.v_tour_stop`, `v_tour_leg`, `v_graph_node` | Stop: 122/892 (13,7%), leg: 110/892 (`tp → tp_tour_layers.with_route_stops`, `with_route_legs`); graph 434 node, 0 build mới hơn graph (`tp_graph`) | Mọi tour đã build có stop; leg cần ≥2 ngày | Tự động theo graph, $0 | Thiếu cần làm (theo lớp 10) |
| 24 | TripPlanner: search index | `catalog.v_component_embedding` (HNSW trên `geo.tour_place.embedding`) | 1.843/1.843 component được phục vụ có vector; 0 dòng `tour_place` thiếu vector (`tp → tp_components.search_index_rows`, `tour_place_unembedded`). Truy vấn: 1.509 call `tp_search_embed` $0,0012 (`tp → tp_spend`) | Mọi component được phục vụ có vector | Cùng `place_extract` (Cohere, chỉ text mới) | Đủ trên phần đã build |
| 25 | TripPlanner: narration cache | `tripplanner.narration_cache` | 1 dòng, nguồn `llm`, 1 hit, còn trong TTL, cũ hơn lần cập nhật tour mới nhất (`tp → tp_narration_cache`); `tp_compose` 1 call $0,0018 (`tp_spend`) | Không cần sinh trước; key cache băm theo chữ Master nên bản sau rewrite không bị phục vụ nhầm (`tpchain` hàng 12, dòng 42) | Theo yêu cầu của khách | Đủ (không có target) |
| 26 | TripPlanner: pin chuyến đã lưu | `tripplanner.trip_events`, `trip_drafts`, `component_id_map` | **371 pin, chỉ 49 còn được phục vụ; 322 không còn dòng component**; 0 trên tour đã nghỉ hoặc tạm dừng; **99/103 chuyến có pin không phục vụ được** (`tp → tp_pins_served`, `pins`). `component_id_map` 750 dòng (`tp_own_rows`) | Mọi pin trỏ (qua map) tới component đang phục vụ, hoặc được báo "không còn" khi tour nghỉ/tạm dừng | Do khách thao tác; mỗi lần đọc đều gấp lại theo `v_tour_component` | Thiếu cần làm (§5.1) |
| 27 | TripPlanner: purge tour đã nghỉ | job CIS `tripplanner_purge` ← `catalog.v_tour_lifecycle_outbox` | 6 sự kiện → job `succeeded`, `delivered = true`; **4 sự kiện không có job** (`no_job`, mới nhất 23/10 15:04Z) (`tp → tp_purge`). Phục vụ tour đã nghỉ: 0 tour / 0 ngày / 0 component / 0 stop (`tp_retired`) | Mọi sự kiện lifecycle có job purge `delivered = true`; 0 dòng phục vụ cho tour nghỉ/tạm dừng | Tự động (sau commit + sweep 5 phút) | Đủ về kết quả (0 phục vụ sai); 4 sự kiện không có job cần kiểm (§5.8) |
| 28 | Booking: trip plans | `booking.trip_plans` (giá, bán được) + đọc sống `catalog.v_tour`/`v_tour_day`/`v_tour_photo` | **Chưa đo trong lần chạy này**: câu SQL Booking trong `chain` §6 không có trong `aa990-run.txt` | Phần chữ đọc sống nên tự theo; dòng thương mại chỉ có cho tour nhân viên chọn bán (không phải coverage target) | Chữ: tự động. Dòng thương mại: nhân viên làm tay, đúng thiết kế | Đủ theo thiết kế (số `orphaned_plans` chưa đo) |
| 29 | CRM catalog cache | `crm.aa_catalog_tour`, `crm.aa_catalog_state` | 892/892 đã cache, `not_cached` 0, `served_state = served`; full pass cuối 23:00:19Z, 0 lỗi (`tp → crm_cache`, `crm_coverage`, `crm_state`). **`hash_matches_live` 0/892** | Mọi tour live có dòng `served`; full pass < 2 giờ | **Tự động hằng giờ** (`crm_catalog_sync`, $0) | **Đủ** (hash khác định nghĩa theo thiết kế, §5.2) |

---

## 3. Theo quốc gia

Nguồn: `cov → live.by_country`, `raw.without_master_by_country`, `segments.tour_coverage`,
`segments.no_member_classified.by_country`, `routes.by_country`, `geo.by_country`, `cards.by_country`, `photos.by_country`.

| Nước | Tour live | Raw chưa có Master | Tour có segment | Atom không rõ lý do thiếu member | Tour có route (route có hub) | Nguồn đã build geo | Tour có component được phục vụ | Atom link card (đã giải quyết %) | Tour có ảnh |
|---|---|---|---|---|---|---|---|---|---|
| India | 218 | 18 | 218 (100%) | 63 | 187 = 85,8% (67/344) | 4 | 4 = 1,8% | 0 = 0,0% (19,7%) | 0 = 0,0% |
| Sri Lanka | 122 | 4 | 121 (99,2%) | 23 | 102 = 83,6% (26/159) | 11 | 11 = 9,0% | 0 = 0,0% (36,9%) | 2 = 1,6% |
| China | 121 | 0 | 120 (99,2%) | 31 | 82 = 67,8% (14/166) | 3 | 3 = 2,5% | 148 = 4,5% (28,7%) | 69 = 57,0% |
| Nepal | 85 | 1 | 85 (100%) | 56 | 74 = 87,1% (27/164) | 10 | 10 = 11,8% | 344 = 10,7% (27,3%) | 0 = 0,0% |
| Japan | 79 | 0 | 75 (94,9%) | 3 | 23 = 29,1% (0/26) | 6 | 6 = 7,6% | 0 = 0,0% (33,1%) | 0 = 0,0% |
| Laos | 46 | 0 | 46 (100%) | 7 | 44 = 95,7% (0/79) | **46** | 46 = **100%** | 137 = 8,4% (36,1%) | 0 = 0,0% |
| Philippines | 44 | 2 | 44 (100%) | 5 | 41 = 93,2% (0/54) | 1 | 0 = 0,0% | 0 = 0,0% (19,6%) | 0 = 0,0% |
| Thailand | 43 | 0 | 41 (95,3%) | 7 | 33 = 76,7% (2/59) | 6 | 6 = 14,0% | 0 = 0,0% (39,2%) | 0 = 0,0% |
| Taiwan | 36 | 0 | 35 (97,2%) | 5 | 23 = 63,9% (1/33) | 3 | 3 = 8,3% | 0 = 0,0% (32,2%) | 30 = 83,3% |
| Bhutan | 32 | 0 | 32 (100%) | 6 | 32 = 100% (18/61) | 6 | 6 = 18,8% | 160 = 16,9% (35,4%) | 29 = 90,6% |
| South Korea | 30 | 0 | 30 (100%) | 14 | 30 = 100% (0/57) | 10 | 10 = 33,3% | 0 = 0,0% (16,0%) | 16 = 53,3% |
| Pakistan | 18 | 0 | 18 (100%) | 5 | 17 = 94,4% (0/40) | **0** | 0 = 0,0% | 7 = 1,0% (11,0%) | 0 = 0,0% |
| Mongolia | 17 | 0 | 17 (100%) | 3 | 11 = 64,7% (0/17) | **17** | 16 = 94,1% | 81 = 22,8% (53,7%) | 16 = 94,1% |
| Vietnam | 1 | 0 | 1 (100%) | 0 | 1 = 100% (0/2) | 0 | 0 = 0,0% | 1 = 1,8% (14,3%) | 0 = 0,0% |
| **Tổng** | **892** | **25** | **883 (99,0%)** | **228** | **700 = 78,5% (155/1.261)** | **123** | **121 = 13,6%** | **878 = 3,4% (27,5%)** | **162 = 18,2%** |

Đọc nhanh:
- Chỉ **Laos** (46/46) và **Mongolia** (17/17) đã build địa điểm đủ cả nước. Ba nước lớn nhất (India, Sri Lanka, China:
  461 tour) mới có 18 nguồn được build.
- **Pakistan** và **Vietnam** chưa build nguồn nào. Philippines có 1 nguồn đã build nhưng 5/5 component không có
  destination nên không có gì được phục vụ (`geo.by_country` Philippines `components_no_destination` 5). Nguồn duy nhất
  thiếu trong graph hiện hành (`geo.graph_vs_built.missing_sample` = `0c8bdf9e…`) khớp với Philippines
  `in_current_graph` 0.
- Ảnh tour = 0 ở 8/14 nước, trong đó có India, Nepal, Japan, Laos, Thailand.
- Japan có tỉ lệ route thấp (29,1%) và 4/79 tour không có segment, nhiều nhất trong các nước.

---

## 4. Một TOUR MỚI hôm nay nhận được gì

Theo `chain` §1 (code CIS `303ae6e9`, đã gồm #1020 / AA-988/989), đối chiếu số job live.

### 4.1 Bước phải bấm tay

| Bước | Ai bấm | Phí |
|---|---|---|
| Nạp Excel → `raw_tours` | Admin `POST /admin/ingest-s3`. Không có trigger S3, EventBridge `ACP.DailyIngest` không ai nhận | Jev `a0_ingest` (30 ngày $0,0782) |
| **S1 rewrite** → `generated_content` + `quality_scores` + `seo_context` | **Admin** (trang S1 / `s1-batch` / Regenerate). Sau upload không có gì tự enqueue S1 | **Trả phí**: `s1_generate` $77,6104, `s1_judge` $12,6937, `s1_flag_fix` $9,6394, `s1_grounding` $9,5328, `s1_itinerary_nudge` $7,7035… (30 ngày, `cov → cost.llm_by_stage_30d`); DFS cho SEO trừ khi dùng lại `ideas_v3` |
| Duyệt review khi bản S1 không qua gate | Người duyệt (`review_queue`) | $0 |

### 4.2 Bước tự chạy sau khi Master được publish

| Bước | Bằng chứng live |
|---|---|
| Atomize → atom | 815 `a3_atomize` thành công / 7 ngày (`cov → jobs.chain_7d`) |
| Segment (trong job atomize) + dọn member chết **của chính tour đó** (#1020) | `segment_step_failed = false` ở mọi lần atomize trong 7 ngày (`jobs.a3_atomize_followups_7d`) |
| Relink card vào card **đã có** ($0, không bao giờ soạn mới) | Lần chạy sau #1020: `card_relink_ran = true` (1 lần, promote của tour A); 814 lần atomize chạy trước #1020 (813 publish wave + 1 promote) nên `card_relink_ran = null` (`jobs.a3_atomize_followups_7d`) |
| `recompute` platform (debounce 180 s): landing PAA → score → route/hub → segment GC | 66 lần `recompute` / 7 ngày; ranking mới nhất 20:55Z (`ranking.by_market`) |
| Purge TripPlanner, **chỉ khi publish có ghi sự kiện lifecycle** (bản mới thay bản cũ, khôi phục). Viết lại chữ cho tour đang phục vụ thì TP tự làm mới sau cache 30 phút | 6 job `tripplanner_purge` thành công (`jobs.chain_7d`) |
| Place build: **chỉ khi nguồn đã có build** (`maintain_built`) hoặc `PLACE_PIPELINE_AUTO` bật (đang tắt) | Trong 7 ngày: 813 lần publish wave + 1 promote ghi `place_extract = "skipped: PLACE_PIPELINE_AUTO off"`; chỉ 1 lần ghi `maintain_built` (`jobs.a3_atomize_followups_7d`) |
| Geocode → shape → dedupe → graph (theo sau place build) | 11 `place_geocode`, 5 `place_shape`, 9 `place_dedupe`, 20 `tour_graph_build` / 7 ngày |
| Ảnh: sync hằng ngày 21:00 UTC | 35 `photo_sync` / 7 ngày; chỉ ghép ảnh có trong Drive |
| CRM cache: hằng giờ | full pass 23:00:19Z, 0 lỗi (`tp → crm_state`) |
| Probe độ tươi hằng đêm (AA-991, 05:13 UTC): **chỉ báo cáo** (`ENFORCE = False`), không đo độ phủ mở rộng | Lần sau backfill (run `40244664055`): stale = 4 (`facts` dòng 30) |

Chứng minh trên tour thật: rewrite tour A (promote 20:49Z 25/10): **7/8 lớp tự theo** (master, atoms, segments,
`tour_place` sau 199 s; ranking, routes sau 396 s; angle_requests); place_cards không theo, vì 11 atom cần card soạn
trả phí (`facts` dòng 29; `cov → jobs.a3_card_relink_sums_7d`: places 11, over_cap 11, skipped_by_rule 6, drafted 0).
Tour A là nguồn **đã build**. Một tour **chưa build** sẽ dừng ở khoảng 6/8: bằng 7/8 của tour A trừ `tour_place`,
vì `place_extract` bị bỏ qua. Đây là số suy ra, chưa đo trên tour thật. Số 5/8 trong `facts` dòng 7 là lần đo tour A
**trước** khi deploy #1020.

### 4.3 Bước không bao giờ chạy nếu không có người chạy

| Bước | Hệ quả cho tour mới | Ai / phí |
|---|---|---|
| **Place build cho nguồn chưa build** | Không có `geo`, component, stop, leg, toạ độ; trên TripPlanner tour chỉ có chữ + day list | Admin `/admin/places/backfill` (AA-905). Ngoại lệ: set-active / restore lại enqueue `place_extract` **không qua gate** (§5.4) |
| **Soạn place card** | Atom chỉ được link nếu card đã có; địa điểm mới thì không có card | Admin `POST /admin/place-cards/build` (lần cuối 13/10) hoặc T8 theo từng atom; trả phí |
| **Nghiên cứu PAA** (`segment_research`, `aa779_serp_topup`) | Địa điểm/market mới có `questions_count = 0` | Admin, trả phí DFS (lần cuối 12/10) |
| **SEO prefetch** (`s1_seo_prefetch`) | Không bắt buộc, vì S1 tự gọi SEO | Admin (lần cuối 10/10) |
| Ảnh cho tour không có thư mục Drive | Không có ảnh | Upload Drive / gán tay, $0 |
| EventBridge `ACP.DailyIngest`, `ACP.WeeklyExport`, `ACP.VetoWindowClose` | Bắn nhưng không rule nào nhận: không có ingest hay export hằng ngày | (§5.5) |

---

## 5. Bất thường và lỗi tìm thấy

### 5.1 Pin chuyến đã lưu bị treo: 322/371 (86,8%), 99/103 chuyến
`tp → tp_pins_served`: `pins` 371, `served` 49, `no_component_row` 322, `on_retired_tour` 0, `on_paused_tour` 0,
`hidden_other` 0, `trips_with_unserved_pin` 99; `tp → pins`: `dangling` 322, `on_replaced_atoms` 0, `trips` 103.
`tripplanner.component_id_map` có 750 dòng (`tp_own_rows`).
- Pin không trỏ vào tour đã nghỉ hay tạm dừng, mà trỏ vào id component không còn trong `v_tour_component`, kể cả sau
  khi tra qua map. Vì vậy TripPlanner không báo được "không còn", pin chỉ biến mất.
- Hai nguyên nhân khả dĩ, **chưa xác minh**: (a) id cũ từ trước tp-017 mà map không có; (b) rebuild địa điểm (re-sync
  123 nguồn S252, hoặc rebuild trước đó) đổi id component mà không mang id cũ sang (`carry_over_ids`, AA-989).
- Dev không có khách thật (103 chuyến chủ yếu là dữ liệu test), nên tác động hôm nay thấp. Nhưng nếu nguyên nhân là
  (b), cơ chế này sẽ mất pin của khách thật mỗi khi rebuild trên prod.

### 5.2 CRM cache: `hash_matches_live` 0/892 — đã kiểm, **không phải lỗi** (S252)
`tp → crm_cache`: `cached` 892, `hash_matches_live` 0; `crm_state`: full pass 23:00:19Z (sau lần S1 cuối 09:40:59Z), 0 lỗi.
Đã đọc định nghĩa hai phía: HTTP catalog của CIS gửi cho CRM `content_hash = sha256` trên **toàn bộ body JSON**
(`AA-CIS-App services/catalog_http/mapping.py:20-22, 189-192`), còn `catalog.v_tour.content_hash` là `md5` chỉ trên các
cột của view. Hai hash khác nhau theo thiết kế, nên câu đối chiếu so sai thứ. Cache CRM **đủ** (892/892, full pass sau
S1, 0 lỗi). Nếu cần đối chiếu nội dung thì so `crm.aa_catalog_tour.content_hash` với ETag của `GET /catalog/v1/tours/{id}`.

### 5.3 14 angle request trên atom đã thay
`cov → tenant.angle_requests`: 14/25 trên atom không active (approved 11, pending_choice 2, pending_goal 1). Con số
bằng baseline trước backfill (`facts` dòng 21) và probe sau backfill (`facts` dòng 30). Chưa có logic trỏ lại; 0
route request bị mồ côi (`facts` Q-990-B). Việc tiếp theo của AA-988.

### 5.4 `place_extract` khi set-active / restore không qua gate S236
`chain` §1 "Other events": `enqueue.py:130-138` không gọi `auto_allowed`, nên một nguồn **chưa build** khi được
set-active sẽ tự chạy build trả phí, trong khi publish thường thì không. Bằng chứng live: 6 `place_extract` lý do
`status:active` trong 7 ngày (`tp → tp_feed_jobs`), tức đường này có chạy; chưa kiểm trong 6 lần đó có nguồn nào
chưa build hay không (ví dụ tour B `7df4db05` là nguồn đã build). Chi phí nhỏ, nhưng hai đường đi đang không nhất quán.

### 5.5 EventBridge schedule không ai tiêu thụ
`ACP.DailyIngest`, `ACP.WeeklyExport`, `ACP.VetoWindowClose` bắn theo lịch nhưng `modules/eventbridge/main.tf:85-170`
không có rule nào nhận (`chain` §1). Không hại dữ liệu, nhưng dễ khiến người đọc tưởng có ingest/export hằng ngày.

### 5.6 Hub: 1.106/1.261 route hiện hành không có hub
`cov → routes.hubs`: 82 hub, 19 được dùng, `current_routes_no_hub` 1.106. `chain` §3 ghi "every current route has a
hub" là mức đủ. Hoặc định nghĩa sai (hub chỉ dành cho nút giao của nhiều route), hoặc stage hub upsert
(`route_detection.py:441`) không chạy cho phần lớn route. Cần đọc code để chốt định nghĩa.

### 5.7 `SEGMENT_GC_MODE=apply` chưa tới task
Terraform đặt `apply` (Infra #400, worker template `:400`, `facts` dòng 28), nhưng lần `recompute` cuối (20:55:53Z)
vẫn ghi `segment_gc.mode = report`, `orphans` 912, `kept` 910, `deletable` 2 (`cov → jobs.recompute_segment_gc_last[0]`).
Probe sau backfill: `orphan_segments` 2 (`facts` dòng 30). `api_task_env.SEGMENT_GC_MODE = null` (biến chỉ có ở worker).
Cần một lần CIS Deploy Dev để task chạy template mới.

### 5.8 Các lệch số khác

| # | Lệch | Số | Đánh giá |
|---|---|---|---|
| a | Member segment trên atom chết | 10.547/27.712 (`cov → segments.dead_member_rows`) | 813 lần atomize của wave chạy **trước** #1020, nên không dọn member chết; GC chỉ xoá segment mồ côi hoàn toàn (10.129 member rows, `chain` §4). Probe AA-991 không đo chỉ số này. Cần dọn một lần, $0 |
| b | Atom không rõ vì sao thiếu member | 228 atom / 157 tour (`segments.no_member_classified.unexplained`) | `forms_segment()` nhận nhưng không có member. Có thể matching không ra kết quả; cần xem mẫu (`unexplained_tour_sample`) |
| c | Master ở model cũ | `satellite-haiku-4-5` 81 + `satellite-sonnet-4-6` 1 = 82/892 (`master.version_meta`) | Mới nhất 10/10, tức không thuộc lần rewrite writer v2. Cần đối chiếu với expected set của wave |
| d | `place_card_links_missing`: ba con số | baseline 5.138 → relink cho 18.756 atom cần soạn (`facts` dòng 22) → probe sau 18.356 (`facts` dòng 30) → coverage `no_row` 18.755 (`cards.by_country`) | Probe đổi phạm vi đếm (mọi tour có ≥1 dòng card), nên nay đo độ phủ, không còn đo link bị mất. 18.755 so với 18.756 lệch 1 do thời điểm đo |
| e | `geo.tour_place` trước / sau | Trước: 2.480 dòng, 2.038 trên atom thay, 111 tour (`facts` Q-990-A); baseline probe 2.032 / 110 tour (`facts` dòng 21, 23). Sau: 2.152 dòng, 0 trên atom chết (`geo.by_country`), probe 0 | Đã khỏi sau re-sync ($0,755 cho 123 tour, `facts` dòng 28) |
| f | 123 build, 122 trong graph / có stop, 121 có component phục vụ, 110 có leg | `geo.build_status`, `geo.graph_vs_built`, `tp_tour_layers` | 1 nguồn Philippines (5 component không có destination) + 1 tour Mongolia không có component phục vụ; leg cần ≥2 ngày |
| g | 4 sự kiện lifecycle không có job purge | `tp → tp_purge` `no_job` 4, mới nhất 23/10 15:04Z | Kết quả không sai (`tp_retired` toàn 0), nhưng sweep lẽ ra phải đẩy lại purge bị lạc (`chain` §1 hàng 4). Cần kiểm xem sweep có bỏ qua sự kiện cũ không |
| h | `built_before_tour_update` 30 | `tp → tp_place_build` | `built_before_newest_atom` 0 và `build_on_older_tour_version` 0, nên có lẽ `updated_at` của tour bị chạm mà nội dung không đổi. Rủi ro thấp |
| i | Cột `cost_usd` trong bảng job = 0 | `jobs.chain_7d`: `s1_rewrite`, `a3_atomize`, `place_extract` đều 0, trong khi `llm_call_log` có tiền | Báo cáo chi phí phải đọc `shared.llm_call_log`, không đọc `shared.job` |
| j | Graph `per_country` có Vietnam, Cambodia | `geo.graph_current.stats.per_country` có Vietnam 22 node, Cambodia 8 node; `geo.by_country` Vietnam build 0 | Có vẻ graph đếm theo nước của **destination** (tuyến xuyên biên giới, `cross_border_pairs` 160), không theo nước của tour |
| k | `segments.inventory.live_questions_never_computed` 1.248 so với `paa.ranked_segment_landing.never_computed` 0 | — | Khác phạm vi: 1.248 là segment có member nhưng không được xếp hạng (bị loại), landing chỉ tính segment có hạng |
| l | Graph validity: 73/892 tour bị gắn cờ | `geo.graph_current.stats.validity.tours_flagged` 73 (`same_place.possible_duplicate` 63, `not_a_pin.area_feature` 30…) | Thông tin chất lượng, không phải lỗi lan truyền |
| m | `supply_content_draft` lỗi | 3 job lỗi / 7 ngày (`jobs.chain_7d`) | Xem lại log lỗi |

---

## 6. Việc đề xuất (theo thứ tự)

Chi phí ước tính lấy từ `cov → cost.*` và các lần chạy thật trong `facts`. Ước tính ghi rõ cách tính.

| # | Việc | Tự động / chạy một lần | Chi phí ước tính | Issue | Cần Nghiệp quyết? (đề xuất sẵn câu trả lời) |
|---|---|---|---|---|---|
| 1 | **CIS Deploy Dev** để worker chạy template `:400` (`SEGMENT_GC_MODE=apply`); kiểm `recompute` kế tiếp ghi `segment_gc.mode = apply`, `deletable` 0 | Một lần, sau đó tự động | $0 | AA-988 | Không (giai đoạn dev: agent tự làm) |
| 2 | **Pin treo**: lấy mẫu 322 pin, phân loại id trước tp-017 hay id bị rebuild đổi; nếu là rebuild thì sửa `carry_over_ids` khi re-sync, và cho TP báo "không còn" thay vì để pin biến mất | Sửa code, chạy một lần | $0 | AA-990 (+ AA-989) | Không. Đề xuất: không chuyển dữ liệu pin Dev (dữ liệu test), chỉ sửa cơ chế |
| 3 | ~~Hash CRM~~ — đã kiểm S252: khác định nghĩa theo thiết kế (sha256 body vs md5 cột view), cache đủ | — | $0 | AA-990 | Không |
| 4 | **Dọn member chết** (10.547 dòng) bằng logic dead-member của #1020 chạy cho mọi tour (snapshot + DRY RUN theo `destructive-ops.md`); thêm chỉ số này vào probe AA-991 | Một lần, sau đó tự động trong atomize | $0 | AA-988, AA-991 | Không (xoá dữ liệu phái sinh, có snapshot; agent review trước theo luật merge) |
| 5 | **Trỏ lại 14 angle request** sang atom thay thế (hoặc đánh dấu hết hiệu lực) | Code + chạy một lần | $0 | AA-988 | Không |
| 6 | **228 atom không giải thích được + hub 155/1.261**: đọc mẫu, chốt định nghĩa, sửa code hoặc sửa `chain` | Điều tra | $0 | AA-988 / AA-989 | Không |
| 7 | **Build địa điểm cho 769 nguồn chưa build** theo thang 3 → ≤50 → theo nước, ưu tiên Pakistan, Vietnam, India, China, Sri Lanka | Chạy một lần theo lượt (paid run subset) | **≈ $5–15 tổng.** Re-sync thật: $0,755 / 123 tour ≈ $0,006/tour (`facts` dòng 28) → 769 × 0,006 ≈ $4,7; dry-run $0,0095/tour (`chain` §5) → ≈ $7,3; chặn trên theo chi phí địa điểm 30 ngày (`a3_place_days` $1,4012 + `a3_place_locate` $0,9824 + `a3_place_embed` $0,0054 = $2,389 / 123 ≈ $0,019/tour) → ≈ $15. Geoapify: 1.461 credit / 30 ngày (search 1.407 + place_details 54), $0 (`cost.geocode_30d`) | AA-905 | **Có.** Đề xuất: duyệt trần $15, chạy trial 3 → 50 ngay phiên sau, báo chi phí từng lượt |
| 8 | **Bật `PLACE_PIPELINE_AUTO=on`** (Terraform) sau khi (7) xong; khi đó tour mới tự có địa điểm, và lỗ hổng gate ở set-active (§5.4) không còn quan trọng | Thay đổi cấu hình, sau đó tự động | ≈ $0,006–0,019 mỗi tour mới (như trên) | AA-905 / AA-989 | **Có** (đảo quyết định S236). Đề xuất: bật, vì chi phí mỗi tour chỉ vài cent và không bật thì TripPlanner luôn thiếu tour mới |
| 9 | **Soạn place card** cho 18.755 atom (9.187 nhóm địa điểm, `chain` §4) theo nước, có dry-run quote trước | Chạy một lần theo lượt; sau đó relink tự động $0 | **Phải quote trước.** Từ kho thật: $0,9668 / 112 card ≈ $0,0086/card (`cards.inventory`); theo stage 30 ngày ($1,2957 + $0,1298) / 112 ≈ $0,0127/card → chặn trên ≈ **$79–117** nếu mỗi nhóm cần một card mới. Backlog (`docs/backlog/README.md` mục 29, AA-784) đang ghi ≈ $15–25 cho 7–9,7k địa điểm, lệch so với số này, nên dry-run quyết định | AA-784 | **Có.** Đề xuất: chạy dry-run quote cho 1 nước (Laos, đã build đủ), rồi duyệt theo nước có trần |
| 10 | **Làm mới PAA / `search_demand`** theo market (dữ liệu từ 28/09–12/10); sau đó landing tự tính lại | Chạy một lần theo market | DFS 30 ngày tổng ≈ $20,99 (`keywords_for_keywords` $17,19, `serp_advanced` $1,984, `search_volume_bulk` $1,17, `search_volume` $0,63; `cost.dfs_30d`); một lượt làm mới ước cùng bậc, quote trước | (L1 / PAA, theo AA-779) | **Có.** Đề xuất: làm sau (7), vì địa điểm mới từ (7) cần câu hỏi |
| 11 | **Ảnh destination = 0/1.182**: kiểm vì sao `photo_sync` không ghép được ảnh nào theo nhãn destination; ảnh tour (18,2%) cần thư mục Drive | Sửa code ($0); bổ sung ảnh theo nguồn có sẵn | $0 | (mới, hoặc gộp vào AA-905) | Không với phần code. Đề xuất: sửa ghép destination trước, không hỏi chị Thư |
| 12 | **82 Master ở model cũ**: đối chiếu expected set của wave; nếu nằm ngoài wave thì viết lại theo runbook `aa-wave-rerun` | Chạy một lần (S1 trả phí) | Quote theo báo cáo wave (S1 là stage đắt nhất: tổng `s1_*` ≈ $117,5 / 30 ngày) | (wave S1) | **Có.** Đề xuất: viết lại 82 tour này để cả catalogue cùng một writer |
| 13 | **25 nguồn chờ review + 2 bản `hitl` từ 10/10 + 43 mục `review_queue` pending**: duyệt trong admin | Tay | $0 | — | Không (việc vận hành) |
| 14 | **Probe AA-991**: bật `ENFORCE`; thêm các chỉ số độ phủ (build geo, card, ảnh, member chết, pin treo, hash CRM) chạy hằng đêm thay cho `coverage.py` chạy tay | Tự động | $0 | AA-991 | Không |
| 15 | **Gate `place_extract` ở set-active** (nếu không làm việc 8) và **xoá EventBridge schedule chết** (hoặc ghi rõ là để dành) | Code + Terraform | $0 | AA-989 / Infra | Đề xuất: xoá 3 schedule chết; gate chỉ cần nếu Nghiệp chưa bật việc 8 |
| 16 | Kiểm 4 sự kiện lifecycle không có job purge; 3 `supply_content_draft` lỗi; đo Booking `orphaned_plans` (SQL `chain` §6) | Một lần | $0 | AA-990 | Không |
| — | Lớp tenant (T0→T11) kiểm đầu cuối | Theo kế hoạch | ~$10–20 (backlog) | AA-741 | Theo slot master plan |

**Tóm lại cho câu hỏi "chạy tay hay tự động":** chuỗi chữ (Master → atom → segment → ranking → route → landing PAA → TripPlanner
chữ → CRM) **đã đủ và tự chạy**. Chuỗi địa điểm (geo → component/stop/leg TripPlanner → toạ độ), place card, ảnh
destination và dữ liệu PAA nguồn **chưa đủ và sẽ không tự đủ**: cần một lần backfill trả phí (việc 7, 9, 10), sau
đó bật tự động (việc 8) để tour mới không bị thiếu lại.
