# Lan truyền khi xoá tour ở S0/A0: audit S248

- Ngày: 23/10/2026, phiên S248. Tác nhân: Claude Code (subagent, chỉ đọc code: không sửa repo, không chạy AWS/ECS).
- Yêu cầu của Nghiệp (nguyên văn): "Nên kiểm đồng bộ khi 1 tour bị xóa ở S0/A0 luôn nha, thì các dẫn xuất của nó đều
  phải ẩn đi, kể cả bên tenant, chỉ giữ copy T2 của họ, nhưng phải cảnh báo tour này không còn được phục vụ, đúng logic
  lan truyền toàn hệ thống".
- Nguồn đã đọc (origin): AA-CIS-App `main` 40bada6a, AA-Booking `main` c314e00, AA-TripPlanner-Web `main` 46f3bfb,
  AA-Partner `main` 55e235a (worktree `.tmp-session/wt/aa-partner`), AA-CIS-Infra `main` 8e7f3f6, repo gốc `master`
  28e9c72. Tên bảng/cột lấy từ `docs/architecture/db-schema-reference.md` (Verified 2026-10-23 06:35 UTC, CIS 270).
- Đường dẫn file dưới đây tương đối theo repo con: `CIS:` = apps/AA-CIS-App, `BK:` = apps/AA-Booking,
  `TP:` = apps/AA-TripPlanner-Web, `PT:` = AA-Partner, `ROOT:` = repo gốc.
- **Chưa có số liệu live.** Mọi kết luận ở đây là từ code. Hai probe chỉ-đọc đã viết sẵn (§6) sẽ cho số thật trên Dev.

---

## 1. Trả lời ngắn

**Hôm nay việc xoá tour ở S0/A0 KHÔNG lan truyền đúng như Nghiệp muốn.** Có đúng một đường xoá cascade tốt:
`PATCH /admin/tours/{id}/trash` (AA-716, CIS:api/routers/admin.py:1780-1860). Trong một transaction nó tắt Master
(1817-1825), dismiss review đang chờ (1828-1836) và ghi `tour.discontinued` cho tenant có bản T2 (74-98, 1848-1849).
Sau commit nó gỡ ranking/route (CIS:services/export/handler.py:53-70) và dựng lại graph
(CIS:services/places/enqueue.py:99-111). Catalog (`catalog._live_tour`, CIS:api/migrations/258_catalog_live_source_key.sql:123-136)
ẩn tour đó với TripPlanner và Booking ngay lần đọc kế tiếp.

Đường này hỏng ở bảy chỗ:

1. **Không bấm được cho tour cần xoá nhất.** Nút xoá chỉ có trên trang Upload, lấy danh sách tour còn `ingested`
   (CIS:frontend/app/admin/upload/page.tsx:349-353, CIS:api/routers/admin_pipeline.py:1987-2008). Tour đã rewrite hay
   publish (tức là tour có dẫn xuất) thì không xoá ở nguồn được từ UI.
2. **Ba đường khác loại nguồn mà không cascade gì:** thay bản qua Excel (staging replace/update,
   admin_pipeline.py:1752-1830, là đường UI thật: upload/page.tsx:760), `set-active` (admin_pipeline.py:1848-1886)
   và `DELETE /admin/raw-tours/{id}` (admin_pipeline.py:1889-1925).
3. **Bốn đường âm thầm làm tour đã xoá sống lại:** nút Activate trên Master Content không kiểm nguồn
   (admin.py:2045-2086, 1661-1711; UI master-content/page.tsx:1022-1026); review đang chờ của tour đã xoá vẫn approve
   được và publish ra Master `active` theo default cột (v1_pipeline.py:478-575; CIS:api/migrations/052_tour_lifecycle_adr018.sql:32);
   upload lại Excel trùng tên khôi phục tour qua staging (services/ingestion/handler.py:219-240); upload với tên hơi
   khác vào thành tour mới, vì kiểm gần-trùng bỏ qua tour trashed (services/ingestion/near_duplicate.py:101-107).
4. **Hai lớp dùng hai luật "còn sống" khác nhau (split brain).** Phía A3/tenant dùng `acp_contract.v_active_tour_atoms`,
   chỉ kiểm Master (CIS:api/migrations/208_drop_distinctiveness_competitors.sql:20-28). Catalog kiểm cả Master lẫn nguồn
   (258:123-136). Luật của view còn bị chép tay vào hai chỗ (CIS:services/acp_shared/subject_seed.py:199-211,
   route_guard.py:84-96), nên sửa view thôi chưa đủ.
5. **Cảnh báo tenant không tới tenant.** `tour.discontinued` được ghi vào `shared.notifications`, nhưng nơi duy nhất đọc
   bảng này là chuông của staff (admin.py:2200-2235). Bảng không có RLS và chỉ grant cho `cis_app`
   (db-schema-reference.md:3509-3525). Chuông trên portal chỉ là view của hoạt động billing (CIS:portal/app/portal/_components/NotificationsBell.tsx:2-4).
   Yêu cầu "phải cảnh báo" hiện **không xảy ra ở đâu cả**.
6. **Phía tenant vẫn chạy tiếp.** Bản T2 được giữ, đúng ý Nghiệp, nhưng không có cờ "không còn phục vụ". Job T2/T9 đang
   chờ vẫn chạy và tốn LLM. Planner T7 vẫn xếp lịch cho tour. T11 vẫn cho đăng bài mới. Bài WordPress/Facebook đã đăng vẫn
   live.
7. **Booking và TripPlanner chỉ ẩn ở danh sách.** Booking ẩn tour khỏi danh sách và khỏi feed B2B, nhưng quote và hold
   không kiểm catalog, không có tín hiệu "đã rút" cho CRM (chờ AA-975), và trip case không có cờ. TripPlanner ẩn tour khỏi
   browse, nhưng chuyến đã lưu vẫn hiện tour cũ không cảnh báo, và trang tour trả 404 chứ không phải 410.

**Gốc của vấn đề:** quyết định "ẩn dẫn xuất" đang nằm rải rác ở từng đường ghi, không ở một chỗ. Cách sửa là một luật
"tour còn được phục vụ" do CIS sở hữu, một service duy nhất đổi trạng thái đó (có cascade + thông báo), và một bản ghi
"đã ngừng" (tombstone) cho các app khác đọc (§3, §4).

---

## 2. Ma trận lan truyền (layer × hôm nay)

Cột "Lọc xoá?": **có** = lớp này ẩn hoặc chặn tour đã xoá ở nguồn; **một phần** = chỉ ẩn khi Master đã bị tắt, hoặc chỉ
lọc một trạng thái; **không** = không lọc.

### 2.1 CIS: nguồn S0/A0 (đường ghi)

| Lớp | Đọc/ghi | Lọc xoá? | Bằng chứng | Hôm nay thấy gì | Nên là |
|---|---|---|---|---|---|
| Xoá nguồn AA-716 `PATCH /admin/tours/{id}/trash` | raw_tours, published_tours, review_queue, notifications | có | CIS:api/routers/admin.py:1780-1860; cascade 1817-1836; notify 74-98 | Cascade đúng, nhưng chỉ bấm được cho tour `ingested` (upload/page.tsx:349-353; admin_pipeline.py:1987-2008). Hộp xác nhận chỉ nói "hidden from the rewrite queue" (page.tsx:350) | Bấm được ở mọi giai đoạn (Master Content, trang chi tiết tour). Hộp xác nhận nêu số tenant / bài / booking bị ảnh hưởng |
| `DELETE /admin/raw-tours/{id}` (cũ) | raw_tours | một phần | admin_pipeline.py:1889-1925 (409 nếu đã có Master, 1898-1907) | Không dismiss review, không thông báo, không dựng graph | Gọi chung service xoá (hoặc bỏ endpoint) |
| Staging replace/update (thay bản Excel) | raw_tours | một phần | admin_pipeline.py:1752-1761 (supersede), 1781-1830 (insert) | Master bản cũ vẫn `active`: atom, ranking, route, Slate tenant vẫn phục vụ bản cũ. Khi publish bản mới thì có **2 Master active** trong cùng group (default 052:32). T2 của tenant vẫn trỏ bản cũ, không có cảnh báo | Cascade "đã có bản mới": tắt Master cũ, chuyển T2 sang cờ "nguồn đã cập nhật" |
| `POST /admin/raw-tours/{id}/set-active` | raw_tours | không | admin_pipeline.py:1848-1886; 1867-1876 không kiểm trạng thái, không xoá `deleted_at` | Có thể dựng row trashed thành `active` mà `deleted_at` vẫn còn (mâu thuẫn). Bản bị hạ cấp không cascade | Từ chối row trashed; đi qua service |
| Ingest khớp chính xác | raw_tours | không | services/ingestion/handler.py:219-240 | Khớp cả tour trashed → staging replace → tour đã xoá sống lại cùng `source_key`. Không có `tour.reinstated` | Staging hiện "tour này đã xoá ngày X" và lựa chọn "Khôi phục" rõ ràng |
| Kiểm gần-trùng | raw_tours | một phần | near_duplicate.py:101-107 (bỏ trashed) | Tour đã xoá đổi tên chút → vào thành tour mới (handler.py:251-256) | So cả với tour trashed và cảnh báo |
| Preview / staging list | raw_tours | không | admin_pipeline.py:1476-1484, 1657-1696; UI upload/page.tsx:716-775 | Không cho biết bản khớp đã bị xoá hay đã bị thay | Hiện `source_status` + `deleted_at` |
| Khôi phục `PATCH /admin/tours/{id}/restore` | raw_tours, published_tours | một phần | admin.py:1865-1936; bật lại MỌI Master `inactive` 1907-1914 (comment 1904-1906 nói khác); recompute với `"inactive"` ở 1930 | Master staff đã cố ý tắt trước đó cũng bật lại. Không enqueue `place_extract` (enqueue.py:102-106) | Chỉ bật Master do cascade tắt (cần ghi lý do). Recompute với `"active"` |
| Activate/toggle Master | published_tours | không | admin.py:2045-2086, 1661-1711; list không trả `source_status` 950-962 | Một click làm tour đã xoá nguồn sống lại cho A3, Slate, pool tenant. Catalog vẫn ẩn. Tenant không nhận `tour.reinstated` | 409 `source_not_live`, hoặc hỏi "khôi phục cả nguồn?" |
| `raw_tours.lifecycle_stage` | — | không | chỉ default ở CIS:api/migrations/086_raw_tours_lifecycle_stage.sql:40-42; không có code ghi | Mọi chỗ lọc `retired` (T7, TP browse) là code chết | Chỉ giữ cho bán hàng (phasing_out); không dùng làm tín hiệu xoá |

### 2.2 CIS: A1–A4, Master, catalog

| Lớp | Đọc từ | Lọc xoá? | Bằng chứng | Hôm nay thấy gì | Nên là |
|---|---|---|---|---|---|
| Review queue list + approve (đường UI thật) | review_queue ⋈ generated_content ⋈ raw_tours | không | CIS:api/routers/v1_pipeline.py:436-466, 478-575 (claim 502-512); admin wrapper admin_pipeline.py:2680-2697; UI review/reviewApi.ts:44 | Review của tour đã xoá vẫn hiện và approve được → Master `active` | Ẩn khỏi list. Approve trả 409 `source_not_live` |
| `process_export` (publish Master) | generated_content ⋈ raw_tours | không | services/export/handler.py:323-445 (gate duy nhất 344-346); shared/repository/published_catalog_repository.py:15-48; default 052:32 | Publish được bản trashed/superseded thành Master active. Atom vào `v_active_tour_atoms` | Kiểm luật served trước INSERT |
| `_enqueue_review` | published_tours | một phần | admin_pipeline.py:180-222 | S1 xong sau khi xoá nguồn → sinh review `pending` mới | Kiểm nguồn |
| S1 rewrite (single/batch) | raw_tours | có | admin_pipeline.py:490-509; s1_batch.py:58-68 | Chặn đúng ở đầu vào, nhưng không kiểm lại trước export (831-844) | Kiểm lại ở export |
| Revalidate | gc ⋈ raw_tours | không | admin_pipeline.py:966-993 | Tốn tiền trên tour đã xoá | Bỏ qua tour không served |
| `acp_contract.v_active_tour_atoms` | tour_atoms ⋈ published_tours | một phần | 208:20-28 (không join raw_tours) | Theo xoá nguồn chỉ khi Master đã bị tắt | Thêm `rt.source_status='active' AND rt.deleted_at IS NULL` |
| Bản chép tay của luật view (Slate seed, route guard) | tour_atoms ⋈ published_tours | một phần | subject_seed.py:199-211; route_guard.py:84-96 | Như trên, và sẽ lệch nếu chỉ sửa view | Dùng chung một hàm hoặc view |
| Ranking / route / segment matching | v_active_tour_atoms | một phần | atom_ranking.py:704, 891; route_detection.py:319-320; segment_matching.py:904 | Theo view | Theo luật served |
| Atomize-all, segment research, question top-up, debate | tour_atoms / published_tours | không | admin_atoms.py:551-630; segment_research.py:610-619; question_topup.py:69-82; debate.py:88-102 | Tốn tiền LLM/DFS cho tour đã xoá; evidence lấy từ atom chết | Lọc served |
| Admin atom list, overview, dashboard | tour_atoms, raw_tours | một phần | admin_atoms.py:195-212, 273-276; admin_overview.py:50-56; admin_dashboard.py:166-178 | Đếm atom chết là sống. Không có bộ đếm cho sai lệch | Cột served + ô "sai lệch lan truyền" |
| `catalog._live_tour` → `catalog.v_tour*` | published_tours ⋈ raw_tours | có | 258:123-136; v_tour 253_catalog_l4_read_model.sql:125-176 | Tour biến mất lặng lẽ. Không có tombstone hay outbox (225_catalog_views.sql:47-48; CIS:CONTEXT.md:833) | Thêm tombstone `catalog.tour.retired` (§3.3) |
| `acp_contract.v_trip_registry` | raw_tours | một phần | 195_v_trip_registry_active_sources.sql:36-43; không có code đọc | Object chết | Đưa vào Dead Table Registry |
| Admin search / export CSV / trang chi tiết | raw_tours | một phần / không | admin_search.py:50-60; admin_pipeline.py:2130-2170, 2920-2945, 3664-3680 | Không có badge "đã xoá" | Badge |

### 2.3 CIS: phía tenant (T0–T11, portal, API)

| Lớp | Đọc từ | Lọc xoá? | Bằng chứng | Hôm nay tenant thấy gì | Nên là |
|---|---|---|---|---|---|
| Pool `/v1/tours/pool` + trigger rewrite | published_tours ⋈ raw_tours | có (chỉ Master) | CIS:api/routers/v1_tours.py:90-93, 121-130, 448-458 | Ẩn đúng, trừ khi Master bị bật lại | Luật served. 409 `tour_discontinued` thay vì 404 chung |
| Job `t2_rewrite` đang chờ + retry | published_tours theo id | không | services/jobs/t2_rewrite_job.py:28-37, 341-358; v1_tours.py:637-682 | Job vẫn chạy, tốn LLM, tạo bản T2 mới của tour đã ngừng. Retry không trừ quota | Huỷ job khi xoá. Retry trả 409 |
| My Tours `/v1/tours/my-versions`, chi tiết, export DOCX | ttv ⋈ published_tours ⋈ raw_tours | không | v1_tours.py:546-634, 846-905, 913-960; RLS không có điều kiện sống (db-schema-reference.md:2934) | **Bản T2 được giữ (đúng)** nhưng không có trường hay badge nào | Giữ, thêm `served_status` + badge bền "AA không còn phục vụ tour này" |
| Thông báo `tour.discontinued` / `tour.reinstated` | shared.notifications | một phần | services/notifications.py:23-24, 43-44; admin.py:74-98; chỉ staff đọc (admin.py:2200-2235); portal bell NotificationsBell.tsx:2-4 | **Tenant không bao giờ thấy.** Xoá/tắt Master không phát gì | Route `/v1/notifications` cho tenant + bell đọc nó. Phát cho mọi tenant có dẫn xuất |
| Marketplace | ttv ⋈ published_tours, tour_atoms | không | v1_marketplace.py:77-154 | Tour đã ngừng vẫn tính vào total_atoms và runway | Cờ served, loại khỏi runway |
| Slate (đề xuất / GET / pick) | atom_ranking, route, subject | có / không / có | slate.py:167-352 (ranking bị gỡ đồng bộ); GET 744-797 không lọc, stale tới 24h (647, 701-707); pick 409 (v1_planning.py:150-158) | Subject `proposed` còn tới 24h. `picked`/`used` còn mãi. Lỗi 409 ghi "Segment/Route rebuilt" | Lọc ở GET, cờ trên subject cũ, mã `tour_discontinued` |
| T8 goal + job `t8_angles` | v_active_tour_atoms | một phần | services/acp_angle_gate/service.py:356-397, 71-97; t8_angles_job.py:36, 44-51 | Tốn 2 lần chạy rồi báo "generation failed" chung chung, retry mãi | 409 ngay ở HTTP |
| T9 write + job `t9_write` đang chờ | v_active_tour_atoms | có / không | acp_content_writing/service.py:111-131 (router map ra 500: v1_content_writing.py:68-69); job 1579-1617 rơi về seed cũ 1594-1595 | Viết mới: 500. Job đang chờ: vẫn viết xong, tốn tiền | 409. Huỷ job khi xoá |
| T10 review / piece / export | content_piece ⋈ tour_atoms | không | service.py:2698-2715, 2836-2950; v1_content_writing.py:128-235 | Bài được giữ (đúng), không cờ | Giữ + badge |
| T11 pending + publish | content_piece ⋈ angle_gate_* | không | CIS:api/routers/v1_publish.py:293-367 (không join tour), 442-560 (cho cả `held`) | Vẫn đăng được bài mới về tour AA đã ngừng | 409 `tour_discontinued` cho bài mới |
| Bài đã live + gỡ bài | publish_log | không | v1_publish.py:95-290; admin A4 force-unpublish chỉ đổi DB, không gọi kênh (admin_a4.py:536-542) | Bài WP/FB vẫn live, tenant không được báo. Force-unpublish ghi "đã gỡ" trong khi bài vẫn live | Giữ bài (quyền của tenant), gắn cờ + nút gỡ 1 click. Sửa nhãn A4 |
| Planner T7 (quarter/runway/reallocation) | ttv ⋈ raw_tours.lifecycle_stage, url_alive | không | services/acp_planning/quarter.py:184-189; runway.py:152-168; tenant_pool.py:64-92 | Tour đã xoá vẫn được xếp slot | Loại tour không served |
| Trang public `/v1/trip/{id}` + recheck | raw_tours ⋈ published_tours | có | v1_trip_page.py:88-96 (lọc đủ 4 điều kiện); recheck 189-216 không ai gọi | 404, `url_alive` chỉ lật khi có người mở trang | 410 khi đã xoá, 301 khi superseded. Recheck chạy theo sự kiện |
| Webhook tenant | webhook_deliveries | — | không có router (CIS:api/main.py:254-301); CIS:CONTEXT.md:833 | Tenant dùng API không nhận tín hiệu máy đọc được | Sự kiện `catalog.tour.retired` (outbox) |

### 2.4 AA-Booking

| Lớp | Đọc từ | Lọc xoá? | Bằng chứng | Hôm nay thấy gì | Nên là |
|---|---|---|---|---|---|
| Danh sách / chi tiết trip plan (staff) | catalog.v_tour LEFT JOIN trip_plans | có | BK:backend/app/catalog/trip_plans.py:1-17, 74-77; 404 `tour_not_in_catalog` 186-187 | Tour biến mất khỏi danh sách. Plan `sellable=true` mồ côi thì staff không còn nhìn thấy | Bộ lọc "Tour đã rời catalog" liệt kê plan mồ côi + lý do |
| B2B products / departures / plan hint | trip_plans + EXISTS catalog.v_tour | có | BK:backend/app/b2b/reads.py:57-59, 79; departures.py:202-205 | Biến mất khỏi feed. Delta sync không thấy tour bị rút; CRM phải full-resync (reads.py:42-44, chờ AA-975) | Delta liệt kê sản phẩm bị rút (`withdrawn`) + sự kiện AA-975 |
| B2B quote pricing | trip_plans.sellable | không | BK:backend/app/b2b/components.py:99, 255-257 | Báo giá được cho plan mà tour đã rời catalog | 409 `tour_not_served` |
| B2B hold | departures + trip_plans | không | BK:backend/app/b2b/holds.py:347-363, 637-638 | Giữ chỗ được trên tour đã xoá | Chặn hold mới. Hold/booking đã confirm thì giữ + cờ staff |
| Trip case / leg / inquiry intake | trip_case_legs (source_id) | không | BK:backend/app/inquiry/leg_keys.py:3-20, 80-91; trip_cases/sql.py:58-64 | Leg giữ khoá. Không có cờ "tour đã ngừng" | Giữ case đã có + cờ staff trên leg |

### 2.5 AA-TripPlanner-Web

| Lớp | Đọc từ | Lọc xoá? | Bằng chứng | Hôm nay thấy gì | Nên là |
|---|---|---|---|---|---|
| Browse / countries / sitemap | catalog.v_tour | có | TP:backend/browse/catalog.py:52-58, 64-66; frontend/app/sitemap.ts:1 | Ẩn đúng | Giữ |
| Trang tour theo slug | catalog.v_tour | có | catalog.py:61-71, 462-470; browse/handler.py:117-120 | 404 `tour not found` | 410 khi đã xoá. Khi superseded thì slug-theo-`source_id` đã tự trỏ bản mới |
| Ghép chuyến (components, suggestions, coverage) | catalog.v_tour_component / v_tour_stop | có | assembly/events.py:48-51; suggestions.py:99-142; coverage.py:29-35 | Không gợi ý tour chết | Giữ |
| Chuyến đã lưu `GET /trip/{id}` | tripplanner.trip_events → itinerary đã lưu | không | TP:backend/assembly/handler.py:115-124; events.py:168, 185 | Vẫn hiện tour đã ngừng như bình thường | Gắn `available:false` mỗi điểm + banner "không còn phục vụ" |
| Hand-off sang Booking | catalog.v_tour | một phần | TP:backend/assembly/handoff.py:10-15, 48-51, 93-109 | Khoá null, vẫn gửi. Booking báo leg unmatched | Gửi kèm cờ, staff thấy lý do |

### 2.6 AA-Partner

| Lớp | Bằng chứng | Hôm nay | Nên là |
|---|---|---|---|
| Dữ liệu tour | PT: chỉ có skeleton (55e235a). Không có code đọc tour; chỉ tiêu thụ qua `booking.b2b.v1` + `catalog.http.v1` (PT:CONTEXT.md:49-50) | Chưa có gì để lan truyền | Khi làm AA-928/976: tour bị rút → dòng đề xuất "no longer offered" |
| Contract `catalog.http.v1` | ROOT:docs/contracts/catalog.http.v1.openapi.yaml:14 hứa "a removed tour is 410" | CIS chưa phục vụ `/catalog/v1` (grep không thấy route). Muốn phân biệt 410 với 404 thì cần tombstone | Tombstone (§3.3) là điều kiện để giữ lời contract |

Test hiện có: chỉ `CIS:tests/unit/test_aa716_raw_trash_cascade.py` (xoá + khôi phục). Không có test nào cho supersede,
set-active, DELETE raw-tours, approve trên nguồn đã chết, hay activate Master trên nguồn đã chết.

---

## 3. Luật đích (luật của Nghiệp, viết chính xác)

### 3.1 Một tín hiệu chuẩn: "tour được phục vụ" (served)

Đơn vị là **tour theo khoá catalog** `(source_system='cis', source_id = raw_tours.source_key)`. `source_key` =
COALESCE(source_group_id, tour_id) (258:20), ổn định qua các lần upload lại. Chủ sở hữu là **CIS**.

| Trạng thái | Định nghĩa (bảng thật) | Phía người dùng |
|---|---|---|
| `served` | Có đúng một version `source_status='active' AND deleted_at IS NULL`, và Master của version đó `master_status='active' AND deleted_at IS NULL` | Bình thường |
| `retired` (ngừng ở nguồn) | Không còn version nào live trong group vì bị xoá ở S0/A0 (trash hay DELETE), hoặc Master bị trash | Ẩn mọi dẫn xuất. Bản T2 và bài của tenant được giữ + cảnh báo "AA không còn phục vụ tour này" |
| `paused` (tạm ẩn) | Nguồn live nhưng Master `inactive` | Ẩn như `retired`. Badge "tạm ngừng" (xem Q1) |
| `restored` | Từ `retired`/`paused` quay lại `served` | Hiện lại mọi thứ, gỡ badge, gửi `tour.reinstated` |

**Supersede không phải là xoá.** Tour vẫn `served` dưới cùng `source_key`. Phần thuộc version cũ (Master, atom, ranking,
route) phải chuyển sang version mới hoặc tắt. Bản T2 trỏ version cũ nhận cờ khác: "nguồn AA đã có bản mới" (Q2).
Không bao giờ được có 2 Master active trong một group.

### 3.2 Một chỗ ghi, một chỗ đọc (trong CIS)

- **Đọc:** một view (đề xuất `catalog.v_tour_liveness`: tour_id, source_key, state, reason, changed_at) hoặc một hàm SQL.
  `catalog._live_tour`, `v_active_tour_atoms`, hai bản chép tay (subject_seed, route_guard), `process_export`, approve,
  pool, `/v1/trip` và planner T7 đều dùng nó. Bước tối thiểu: thêm điều kiện nguồn vào `v_active_tour_atoms` và hai bản
  chép.
- **Ghi:** một service CIS duy nhất (ví dụ `services/tour_lifecycle`) với các hành động `retire`, `pause`, `supersede`
  và `restore`. Mọi endpoint ở §2.1 phải đi qua nó: trash, DELETE raw-tours, staging replace, set-active,
  trash/deactivate/activate Master, restore. Trong một transaction, service làm năm việc:
  1. Đổi trạng thái nguồn và Master. Ghi lý do, để restore chỉ bật lại đúng Master mà cascade đã tắt.
  2. Dismiss review đang chờ.
  3. Huỷ job `t2_rewrite`/`t8_angles`/`t9_write` đang chờ của tour.
  4. Ghi tombstone/outbox.
  5. Phát thông báo cho **mọi tenant có dẫn xuất**: có bản T2, subject, angle_gate_request, content_piece hay publish_log
     trỏ tới tour (không chỉ tenant có T2).

  Sau commit, service gỡ cache, recompute với **đúng trạng thái mới**, dựng graph và recheck trang trip.
- **Activate Master trên nguồn đã chết:** trả 409 `source_not_live`, kèm lựa chọn "khôi phục cả nguồn".

### 3.3 Tín hiệu ra ngoài CIS (cho Booking, TripPlanner, Partner, API tenant)

Thêm tombstone do CIS sở hữu, chính là lát outbox `catalog.tour.*` đang hoãn của AA-679 (225:47-48, CIS:CONTEXT.md:833).
Mỗi `source_key` có một dòng trạng thái `retired|paused|restored` + `changed_at`. Đọc qua view `catalog.v_tour_retired`,
grant cho `booking` và `tripplanner` như CIS 225. Contract `catalog.tour.v1.3` (additive) mô tả nó.
`catalog.v_tour` giữ nguyên (chỉ tour sống).

### 3.4 Hành vi từng nơi

- **Tenant (CIS portal + /v1):**
  - **Giữ** bản T2, bài viết và export. RLS đã giữ sẵn (db-schema-reference.md:2934); không xoá gì của tenant.
  - Thêm `served_status`, `served_reason`, `discontinued_at` vào my-versions, chi tiết version, marketplace, review/piece
    và publish pending.
  - Badge bền trên My Tours, Content và Publish. Chuông portal đọc thông báo tenant thật.
  - Chặn việc mới (rewrite, retry, goal, write, publish bài mới) bằng 409 `tour_discontinued` với câu dễ hiểu.
  - Lọc Slate GET. Planner T7 bỏ tour.
- **Bài tenant đã đăng:** giữ, gắn cờ "tour đã ngừng: nên gỡ hoặc sửa", nút gỡ 1 click trên kênh. **Không tự gỡ**
  (đó là site/page của tenant). Sửa A4 force-unpublish để nó nói thật, hoặc gọi kênh thật.
- **Booking:**
  - Chặn quote và hold mới (409 `tour_not_served`).
  - **Giữ** trip case, booking và hold đã confirm, kèm cờ staff trên leg và plan.
  - Danh sách plan có bộ lọc "plan mồ côi".
  - Feed B2B delta liệt kê sản phẩm bị rút (`withdrawn`). Sự kiện `product.withdrawn` vào AA-975.
- **AA-Partner:** ẩn khỏi danh sách để chào bán. Dòng đề xuất cũ đánh dấu "no longer offered", nhờ 410 của
  `catalog.http.v1` và feed delta của Booking.
- **TripPlanner:**
  - Browse ẩn (đã có).
  - Trang tour 410 khi retired; khi superseded thì slug theo `source_id` đã dẫn tới bản mới.
  - Chuyến đã lưu: mỗi điểm gắn "không còn phục vụ" và có banner. Hand-off vẫn gửi nhưng mang cờ.
- **Khôi phục:** `restore` trả mọi thứ về `served`, gửi `tour.reinstated` cho đúng các tenant đã nhận cảnh báo, gỡ
  badge, đóng tombstone (`restored`), enqueue `place_extract`. Các app khác thấy lại tour qua catalog.
- **SEO:** 410 Gone cho tour retired (CIS `/v1/trip/{id}`, TP trang tour). 301 khi superseded (cùng `source_key`) sang
  tour_id/slug hiện hành. Sitemap tự rơi (đã lấy từ catalog).

---

## 4. Lát triển khai (cỡ issue, theo thứ tự)

Chi phí AWS: **~$0**. Không thêm dịch vụ mới. Probe hằng đêm chạy như DB Schema Dump (một task ECS vài giây/đêm), dưới
$0.10/tháng.

| # | Lát | Repo | Migration | Test | Ghi chú |
|---|---|---|---|---|---|
| L1 | **Chặn rò A-side:** thêm điều kiện nguồn vào `v_active_tour_atoms` + 2 bản chép (subject_seed, route_guard). `process_export` và approve từ chối nguồn không served. `_enqueue_review` kiểm nguồn. Review list ẩn | CIS | Có: CIS 27x `CREATE OR REPLACE VIEW` (cùng cột) | Unit/integration: publish/approve trên nguồn trashed và superseded → 409; atom không vào view | Rủi ro schema → review agent trước (DM-11.5). Đóng ngay các rò "sống lại qua approve" |
| L2 | **Một service lifecycle:** mọi writer ở §2.1 đi qua nó. Activate trả 409 khi nguồn chết. Restore chỉ bật Master do cascade tắt + recompute `"active"`. Staging replace cascade Master cũ (không còn 2 Master active). DELETE raw-tours ủy quyền cho service. set-active từ chối trashed. Re-upload tour đã xoá → staging báo "đã xoá" + nút Khôi phục. Kiểm gần-trùng gồm cả trashed. Nút "Ngừng phục vụ" trên Master Content kèm dry-run số tenant/bài/booking | CIS (api + admin FE) | Có: cột lý do trên `published_tours` (ví dụ `master_status_reason`) | Ma trận test: mỗi writer × dẫn xuất; regression cho bug restore (admin.py:1930) | Lát lớn nhất. Có thể tách L2a backend / L2b UI |
| L3 | **Tenant thấy và bị chặn đúng:** trường `served_*` trên /v1. Route `/v1/notifications` (grant/RLS cho tenant pool) + portal bell. Badge bền. 409 `tour_discontinued` cho rewrite/retry/goal/write/publish. Huỷ job đang chờ. Planner T7 + Slate GET lọc. Publish-log gắn cờ + gỡ 1 click. Sửa A4 force-unpublish | CIS (api + portal) | Có: grant/RLS `shared.notifications` cho `aa_app_user`, hoặc bảng tenant riêng | E2E portal: xoá tour → badge + chuông. Unit 409 | Đây là phần "phải cảnh báo" Nghiệp hỏi |
| L4 | **Tombstone/outbox catalog:** `catalog.v_tour_retired` (hoặc outbox `catalog.tour.retired/restored`) + grant `booking`/`tripplanner`. Contract `catalog.tour.v1.3`. `/v1/trip` 410/301 + recheck theo sự kiện | CIS + ROOT contracts + Infra (grant) | Có | Contract test, probe | Mở khoá L5/L6 và giữ lời 410 của `catalog.http.v1` |
| L5 | **Booking:** quote/hold kiểm `catalog.v_tour` (409). Cờ staff trên trip case leg + bộ lọc plan mồ côi. Delta B2B liệt kê `withdrawn` (đọc tombstone). Sự kiện vào AA-975 | BK (+FE staff) | Có thể (bk-0xx nếu lưu cờ) hoặc không (đọc trực tiếp) | Unit quote/hold trên tour đã rút | Booking/hold đã confirm: chỉ gắn cờ, không huỷ |
| L6 | **TripPlanner:** `GET /trip` gắn `available` mỗi điểm. Banner FE. Trang tour 410 | TP | Không | Unit handler + UI smoke | Nhỏ |
| L7 | **Gác cổng toàn hệ:** đưa probe master (§6) thành script trong Infra, chạy **hằng đêm** cạnh DB Schema Dump, đỏ khi có `violations > 0`. Viết ADR hệ sinh thái "tour liveness & retirement propagation" ở `ROOT:docs/adr/` (đụng ≥ 2 repo). Thêm `v_trip_registry` vào Dead Table Registry | Infra + ROOT | Không | Chính probe là test hồi quy | Làm sớm phần ADR, trước L2–L5 |

Partner: không có lát riêng. Ghi yêu cầu "410 → no longer offered" vào AA-928/AA-976 khi làm consumer.

Thứ tự đề xuất: **L7-ADR → L1 → L2 → L3 → L4 → L5, L6 song song → L7-probe hằng đêm.** Riêng L1 đã chặn được các rò
nặng nhất trong một PR nhỏ.

---

## 5. Câu hỏi mở (kèm đề xuất trả lời)

| # | Câu hỏi | Đề xuất |
|---|---|---|
| Q1 | Tắt Master (deactivate, nguồn vẫn còn) có tính là "không còn phục vụ" không? | Ẩn giống hệt `retired`, nhưng badge là "tạm ngừng" và không đẩy thông báo. Riêng **trash Master** thì tính là `retired` và có cảnh báo |
| Q2 | Thay bản Excel (supersede): bản T2 của tenant trỏ version cũ thì sao? | Không coi là ngừng. Badge "nguồn AA đã cập nhật" + nút rewrite theo bản mới, không trừ quota |
| Q3 | Bài tenant đã đăng về tour bị xoá: tự gỡ không? | Không tự gỡ. Gắn cờ + nút gỡ 1 click + nêu trong thông báo |
| Q4 | Booking: departure tương lai đã bán chỗ / booking confirmed của tour bị xoá? | Giữ nguyên, cờ staff. Chặn hold/quote mới. Việc huỷ là quyết định kinh doanh của chị Thư (ghi đề xuất, không ép) |
| Q5 | SEO: 410 hay redirect? | 410 khi retired. 301 khi superseded (cùng `source_key`). Restore thì trang sống lại |
| Q6 | Upload lại tour đã xoá: tự khôi phục hay hỏi? | Staging hiện rõ "tour đã xoá ngày X". Admin chọn "Khôi phục" (chạy restore + `tour.reinstated`) hoặc "Tạo tour mới" |
| Q7 | Kênh cảnh báo tenant? | Badge bền (nguồn sự thật) + chuông portal đọc `shared.notifications` của tenant. Email/webhook để sau, khi có outbox (L4) |
| Q8 | Ai được xoá tour đã publish? | Staff có quyền Master Content. Hộp xác nhận hiện dry-run số tenant/bài/booking bị ảnh hưởng |
| Q9 | `lifecycle_stage` (không có code ghi)? | Không dùng làm tín hiệu xoá. Giữ cho bán hàng (`phasing_out`). T7 và TP đổi sang luật served |
| Q10 | Tenant chỉ dùng tour qua Slate/plan (không có T2) có được báo không? | Có: phát cho mọi tenant có bất kỳ dẫn xuất nào (subject, angle request, piece, publish_log), không chỉ T2 |

---

## 6. Probe live: chạy trước khi code

Script và hướng dẫn đã có sẵn (chỉ đọc, đã chạy xanh trên stub PostgreSQL local, **chưa chạy trên Dev**):
`.tmp-session/S248-lanes/tour_deletion_probe.py` (nửa CIS), `.tmp-session/S248-lanes/tour_deletion_probe_master.py`
(nửa master) và run sheet `.tmp-session/S248-lanes/tour-deletion-probe.md`.

**Bước 1: nửa CIS** (ECS exec, `cis_app`, read-only repeatable read; lệnh 1 dòng đầy đủ ở run sheet §A):

```
aws sts get-caller-identity --profile aa365-admin
```

Sau đó làm lần lượt: upload `tour_deletion_probe.py` + wrapper → presign + lấy task → `execute-command` (grep `UPLOADED`)
→ tải `s3://aa-cis-bronze-<acc2-id>/scripts/out/s248-tdp.txt` → in tóm tắt. Cần thấy `role cis_app ro on errors 0`.

**Bước 2: nửa master** (run sheet §B). Agent điều phối copy script vào
`infra/AA-CIS-Infra/db/scripts/s248_tour_deletion_probe.py`, mở PR, merge, rồi chạy:

```
gh workflow run db-migrate.yml -R AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f environment=dev -f mode=run-script -f script=db/scripts/s248_tour_deletion_probe.py
```

Đây là nền cho gác cổng hằng đêm ở L7.

**Đọc kết quả với ma trận ở §2:**
- Bucket `trashed`/`group_dead`: các lớp `master_active_tenant_pool`, `atoms_live_platform`, `catalog_v_tour`,
  `atom_ranking_current`, `route_current` phải = 0.
- `tenant_t2_unwarned` cho biết số cặp tenant–tour chưa được cảnh báo. Theo §1 điểm 5, dù cảnh báo đã ghi thì tenant
  vẫn không đọc được.
- Anomaly `trashed_source_master_active`, `superseded_source_master_active`, `active_source_with_deleted_at`,
  `trashed_group_revived_by_newer_version`, `master_published_without_live_source` đo trực tiếp các rò ở §2.1/§2.2.
- Lớp Booking/TripPlanner (nửa master) cho số plan mồ côi, hold/quote, trip case và draft đang trỏ tour đã rời catalog.

Có số live rồi mới chốt độ ưu tiên giữa L1 và L2. Nếu Dev đang có tour bị 2 Master active hay bị sống lại, cần dọn dữ
liệu theo quy trình DRY RUN (skill `aa-cis-schema` references/destructive-ops.md) ngay trong L2.

---

## 7. Phụ lục: kết quả probe live nửa CIS (23/10/2026 08:01 UTC)

Chạy bằng ECS exec, role `cis_app`, transaction read-only, `errors: []` (schema ref CIS 270).

- 987 version, 982 group: 917 group live, **65 group chết** (44 version `trashed`, 21 `superseded` không có bản kế;
  5 `superseded` khác đã có bản mới). 892 Master `active`.
- Mọi lớp kỳ vọng `zero` ở §6 (pool tenant, review chờ, catalog, atom live, ranking, route, Slate, angle request, T9,
  T11, trang trip) đều **= 0** cho mọi bucket. Mọi anomaly (Master active trên nguồn chết, `active` + `deleted_at`,
  group sống lại, Master không nguồn live) **= 0**. Không tenant nào có bản T2 của tour chết.
- `shared.notifications`: 4 `tour.source.trashed`, 2 `tour.source.restored`, 7 `tour.master.deactivated` (1 tenant).
- Role `cis_app` không đọc được `catalog.v_tour` (InsufficientPrivilege) — đúng thiết kế; lớp catalog đo bằng luật
  `catalog._live_tour` chép trong probe.

Kết luận: các rò ở §2 là **đường đang mở**, chưa gây hỏng dữ liệu trên Dev. Không cần dọn dữ liệu trước L1/L2. Nửa
master (Booking/TripPlanner) chưa chạy. Quyết định kiến trúc: ADR 0015 (`docs/adr/0015-tour-liveness-and-retirement-propagation.md`).
