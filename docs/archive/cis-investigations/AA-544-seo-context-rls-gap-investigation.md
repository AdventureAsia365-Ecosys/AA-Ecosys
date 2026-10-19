# AA-544 — seo_context RLS gap: điều tra thiết kế + phạm vi lỗ hổng thật

Investigation-only, KHÔNG code fix. Xuất phát từ AA-543 Phần 4.2.

**10/09/2026 — Phần 2 (round 2):** Nghiệp chốt hướng tách 2 connection pool (Admin giữ
`aa_cis_admin` bypass, Tenant Portal chuyển `aa_app_user` non-bypass + set GUC đúng), yêu cầu điều
tra thêm trước khi thiết kế chi tiết. Xem mục 7-11 dưới đây (nối tiếp mục 1-6 ở round 1).

## 1. Ý định thiết kế ban đầu — per-tenant thật hay platform-wide?

**Kết luận: per-tenant THẬT, không phải platform-wide-by-design.** Bằng chứng theo thời gian:

- `002_schema_v2.sql:679-700` (bản nháp comment-out sớm nhất trong repo, trước cả migration 004
  tồn tại) đã phân biệt rõ 2 role: "DBA account bypass RLS" (`aa_cis_admin`) vs. "Application user
  (app_user — read/write nhưng KHÔNG bypass RLS)". Tức là ý định real-enforcement-via-non-bypass-role
  có từ bản thiết kế đầu tiên, không phải nghĩ thêm sau.
- `004_tenant_rls.sql` (S7, sprint "onboarding B2B tenants") hiện thực hoá: thêm cột `tenant_id`,
  FK vào `shared.tenants`, `ENABLE ROW LEVEL SECURITY` + `CREATE POLICY` + **`FORCE ROW LEVEL
  SECURITY`** trên 6 bảng gồm `seo_context`. `FORCE` chỉ có ý nghĩa khi ai đó định query bằng
  owner-role không có BYPASSRLS — tức người viết migration này thực sự kỳ vọng có một role thật sự
  bị RLS chặn.
- `007b_create_app_user.sql` — comment ngay đầu file: *"aa_cis_admin has SUPERUSER/BYPASSRLS → RLS
  policies don't apply to it. aa_app_user is the runtime application role — RLS IS enforced."*
  Role `aa_app_user` (NOSUPERUSER/NOBYPASSRLS) được tạo **có chủ đích** để làm role vận hành thật.
- `008_rls_gold_silver.sql` (S9) mở rộng RLS sang gold_aa_internal, với lý do nêu rõ: *"S9
  discovered gold_aa_internal and silver_aa_internal tables had no RLS, allowing cross-tenant data
  access via aa_app_user role."* — tại thời điểm S9, người viết tin rằng `aa_app_user` **đã** là
  role chạy production thật (nếu không thì "allowing cross-tenant access" vô nghĩa).

→ Không có bất kỳ dấu vết nào cho thấy `seo_context` (hay 5 bảng khác trong 004) từng được định
nghĩa là platform-wide-by-design. Design intent nhất quán suốt lịch sử migration: per-tenant thật,
enforced qua RLS + role tách biệt.

## 2. Vì sao vẫn bypass 100% trong thực tế — root cause thật

Không phải RLS policy sai. Root cause là **role thật sự dùng ở production KHÔNG PHẢI
`aa_app_user`**, mà là `aa_cis_admin` — role BYPASSRLS đó luôn.

Bằng chứng (Terraform, `AA-CIS-Infra`):
- `variables.tf:22-25` — `db_username` mặc định `"aa_cis_admin"`.
- `modules/rds/main.tf:19` — `username = var.db_username` → đây là **master user thật của chính
  RDS instance**, tạo ra với quyền superuser/BYPASSRLS.
- `modules/ecs/main.tf:266` — ECS task định nghĩa biến môi trường `DATABASE_URL` trỏ vào
  `var.secret_rds_arn` — chính secret Secrets Manager chứa DSN của `aa_cis_admin`.
- `api/main.py:64-66` — pool duy nhất của toàn bộ app được tạo từ `os.environ["DATABASE_URL"]`.
  Không có pool thứ hai, không có logic chọn role theo tenant hay theo request.

→ **`aa_app_user` chưa từng được wire vào bất kỳ thành phần chạy thật nào** (ECS task, Lambda).
Nó tồn tại duy nhất để phục vụ 2 file test (`tests/integration/test_007_rls_isolation.py`,
`tests/integration/test_tenant_rls.py`) — và cả 2 file đó tự kết nối tới **một Postgres cục bộ
khác** (`localhost:5432`, DB `cis_integration_test`), KHÔNG PHẢI RDS thật. Tức là ngay cả role
đúng cũng chưa từng được test chạy áp lên RDS thật — chỉ áp lên một bản sao schema cục bộ.

Về phần GUC (`app.tenant_id`): `shared/repository/raw_tour_repository.py:22-27` **có thật sự gọi**
`SELECT set_config('app.tenant_id', $1, true)` trước mỗi query — đây KHÔNG phải code chết, là nỗ
lực enforcement thật ở tầng app. Nhưng vì pool luôn connect bằng `aa_cis_admin` (BYPASSRLS), lệnh
`set_config` này hoàn toàn vô nghĩa với RLS — mọi bảo vệ thật sự tới từ mệnh đề `WHERE tenant_id =
$N` viết tay trong từng câu query, không phải RLS.

Riêng `seo_context`: `shared/repository/seo_context_repository.py` **không hề gọi `set_config`**
(khác `RawTourRepository`) — và mọi query thật trong repo (`services/acp_shared/dfs_relevance.py`,
`api/routers/admin_pipeline.py`, `services/acp_angle_gate/service.py`, `services/acp_shared/
slate.py`, `services/seo_intelligence/handler.py`) đều lọc `WHERE tour_id = $1`, không có tham số
tenant nào — khớp với phát hiện gốc trong AA-543/AA-544.

## 3. Các bảng RLS khác có cùng lỗ hổng không?

**Có — TẤT CẢ bảng có RLS policy trong repo này cùng chung gốc lỗ hổng** (role bypass ở tầng kết
nối, áp dụng cho mọi bảng bất kể policy đúng hay sai). Danh sách đầy đủ (grep `CREATE POLICY` toàn
bộ `api/migrations/`):

| Bảng | Migration | GUC dùng | `FORCE RLS`? | `aa_app_user` có GRANT? |
|---|---|---|---|---|
| `shared.pipeline_runs` | 003, 004 | `app.tenant_id` | Có (004) | Có (007b) |
| `silver_aa_internal.raw_tours` | 002(dead)/004/008 | `app.tenant_id` | Có | Có |
| `silver_aa_internal.seo_context` | 004/008 | `app.tenant_id` | Có | Có |
| `silver_aa_internal.generated_content` | 004/008 | `app.tenant_id` | Có | Có |
| `silver_aa_internal.quality_scores` | 004/008 | `app.tenant_id` | Có | Có |
| `gold_aa_internal.published_tours` | 004/008 | `app.tenant_id` | Có | Có |
| `gold_aa_internal.content_exports` | 006/008 | `app.tenant_id` | Có | Có |
| `gold_aa_internal.webhook_deliveries` | 006/008 | `app.tenant_id` | Có | Có |
| `acp_deliver.packets` | 094 | `app.tenant_id` | **Không** | Có (094) |
| `acp_deliver.pieces` | 094 | `app.tenant_id` | **Không** | Có (094) |
| `acp_shared.acp_v2_runs` | 096 | `app.tenant_id` | **Không** | Có (096) |
| `acp_shared.acp_v2_slots` | 096 | `app.tenant_id` | **Không** | Có (096) |
| `acp_shared.unknown_ledger` | 095 | `app.tenant_id` | **Không** | Có (095) |
| `acp_shared.angle_gate_request` | 113 | `app.tenant_id` | **Không** | **Không** |
| `acp_shared.content_metric_snapshot` | 112 | `app.tenant_id` | **Không** | **Không** |
| `acp_shared.content_piece` | 115 | `app.tenant_id` | **Không** | **Không** |
| `acp_shared.publish_log` | 116 | `app.tenant_id` | **Không** | **Không** |
| `acp_shared.facts` | 145 | `app.tenant_id` (+ `scope='platform'` OR) | **Không** | **Không** |
| `acp_silver_s3.ads_plan` | 031 | `app.current_tenant` ⚠️ | **Không** | **Không** |
| `acp_shared.acp_lessons_agency` | 031 | `app.current_tenant` ⚠️ | **Không** | **Không** |
| `acp_silver_s4.social_content` | 019 | `app.current_tenant` ⚠️ | **Không** | **Không** |

Ghi chú quan trọng:

- **3 bảng dùng GUC `app.current_tenant`** (031, 019) — grep toàn bộ repo (`api/`, `services/`,
  `tests/`) xác nhận **0 nơi nào từng set biến này**, kể cả trong test. Đây là một GUC "chết" —
  ngay cả nếu role đúng (`aa_app_user`) và có GRANT, policy này sẽ luôn fail-closed (0 hàng), vì
  `current_setting('app.current_tenant', true)` trả `NULL` mãi mãi. Lỗi khác loại với nhóm
  `app.tenant_id` (nhóm kia fail-open do bypass; nhóm này sẽ fail-closed nếu role đúng — nhưng vì
  role cũng sai/bypass nên hiện tại nó cũng đang fail-open y hệt các bảng khác). Bằng chứng này đã
  được một session trước phát hiện độc lập (comment trong `094_acp_deliver_pieces_packets.sql:22-36`
  và `096_acp_v2_runs_slots.sql:35-39`, viết khi làm AA-364/AA-377/AA-378) — không phải phát hiện
  mới của AA-544, nhưng AA-544 là issue đầu tiên đề xuất xử lý nó thay vì chỉ ghi chú lại.
- **7 bảng ACP-era (112/113/115/116/145) hoàn toàn không GRANT cho `aa_app_user`** — tức là ngay cả
  đường test "đúng" (role non-bypass) cũng không kết nối được tới các bảng này. Không schema RLS
  nào trong nhóm ACP từng được verify sống bằng role không-bypass, kể cả ở môi trường test cục bộ.
- **`FORCE ROW LEVEL SECURITY` chỉ tồn tại ở 6 bảng của migration 004/008.** Về mặt lý thuyết không
  quan trọng ngay bây giờ (role production có BYPASSRLS ở cấp session, FORCE hay không đều bị bỏ
  qua như nhau) — nhưng nếu hướng sửa sau này đổi sang role non-bypass mà quên thêm FORCE cho 14
  bảng còn lại, connection bằng chính table owner (không phải aa_app_user) vẫn sẽ bypass được.
- **`silver_aa_internal.raw_sources` và `review_queue`**: xác nhận qua comment `008_rls_gold_
  silver.sql:41,97-99` — cố ý loại khỏi RLS vì không có cột `tenant_id` (không phải gap, là platform-
  wide chính danh).
- Không có bảng nào khác ngoài `seo_context` là "riêng lẻ" — đây là **lỗ hổng hệ thống ở tầng kết
  nối DB**, áp dụng đồng loạt cho toàn bộ 20 bảng có RLS trong repo, không phải đặc thù của
  `seo_context`. `seo_context` chỉ là bảng đầu tiên được audit kỹ (AA-543 Phần 4.2).

## 4. Đối chiếu CONTEXT.md hiện tại

`CONTEXT.md` (mục "Cross-tenant mechanisms — full inventory", dòng ~224-237) hiện liệt kê đúng 3 cơ
chế cross-tenant **có chủ đích thiết kế**: Master Content/Atom pool, Search Demand, Facts Entry
(`scope='platform'`). `seo_context` không nằm trong danh sách này, và **đúng là không nên nằm
trong danh sách này theo nghĩa gốc** — 3 cơ chế kia là platform-wide-by-design (ví dụ Search Demand
không hề có cột `tenant_id`), còn lỗ hổng RLS của `seo_context` (và 19 bảng khác) là **accidental
gap**, không phải chủ đích. Nếu hướng sửa cuối cùng là "chấp nhận platform-wide chính thức" (Hướng
B ở mục 5 dưới), đây sẽ là cơ chế cross-tenant thứ 4 — nhưng khác loại 3 cơ chế kia: nó không phải
"chủ đích từ đầu", mà là "chấp nhận hiện trạng vì chi phí sửa cao hơn lợi ích, ở thời điểm 0 tenant
thật có dữ liệu riêng."

## 5. Hai hướng sửa — effort/risk, KHÔNG chọn hướng

### Hướng A — Per-tenant thật: đổi role production + set GUC đúng chỗ

Việc cần làm:
1. Đổi `DATABASE_URL` production trỏ về role non-bypass (`aa_app_user` đã có sẵn, hoặc tạo role
   mới sạch hơn — `aa_app_user` hiện có password hardcode trong migration file, nên đổi password +
   luân chuyển qua Secrets Manager trước khi dùng thật).
2. Gọi `SELECT set_config('app.tenant_id', $tenant, true)` **ở đúng 1 điểm trung tâm** cho MỌI
   connection lấy ra từ pool (ví dụ asyncpg pool's `setup`/`init` callback hoặc 1 middleware
   `acquire()` wrapper) — không lặp lại việc set rải rác trong từng repository như
   `RawTourRepository` đang làm (dễ sót, sai chỗ).
3. Áp `FORCE ROW LEVEL SECURITY` cho 14 bảng ACP-era hiện chưa có.
4. Đổi GUC name của 3 bảng dùng `app.current_tenant` (031, 019) về `app.tenant_id` cho khớp cơ chế
   thật — hoặc xoá hẳn (xem việc cần làm chung ở dưới).
5. GRANT `aa_app_user` cho 7 bảng ACP-era hiện chưa có (112/113/115/116/145 + 2 bảng 031/019).
6. Rà lại TOÀN BỘ query hiện dùng `aa_cis_admin` cho các thao tác admin/cross-tenant có chủ đích
   (A-series Master Content, Search Demand, Facts Entry platform-scope, F10 cannibalization gate
   đọc chéo tenant) — các đường này **phải tiếp tục bypass được**, nghĩa là cần phân tách rõ 2 loại
   kết nối (tenant-scoped vs. admin/platform-scoped), không thể đổi toàn bộ `DATABASE_URL` sang
   non-bypass một cách mù quáng — sẽ gãy ít nhất 4 luồng đã biết.
7. Viết lại test suite (`test_007_rls_isolation.py`, `test_tenant_rls.py`) để chạy thật lên RDS
   dev thay vì Postgres cục bộ — nếu không, "fix" này vẫn chưa từng được verify sống.

Effort: **Cao** — không phải 1 migration, mà là thay đổi kiến trúc kết nối DB (2 role/2 pool tối
thiểu), rà soát lại ~20 bảng, và audit mọi call site admin/cross-tenant hiện đang ngầm dựa vào
bypass. Ước lượng nhiều PR, khả năng cần 1 ADR riêng trước khi code (theo quy trình AA-539 của repo
này — thay đổi kiến trúc khó đảo ngược).

Rủi ro: **Cao nếu làm vội.** Đổi role production sai 1 GRANT có thể làm sập một luồng đang chạy live
(ví dụ Master Content admin write) do thiếu quyền, hoặc bug 1 GUC set sai thời điểm (connection
pool tái sử dụng connection giữa các request khác tenant nếu không reset đúng — asyncpg pool reuse
là điểm cần cẩn trọng đặc biệt) có thể gây injection HÀNG THẬT của tenant khác vào response — tức
là biến 1 lỗ hổng "silent, 0 tenant thật bị ảnh hưởng" thành 1 bug "active, có thể leak dữ liệu
thật" nếu làm sai. Cần test suite thật (chạy trên RDS, không phải Postgres cục bộ) trước khi merge.

Lợi ích: Đúng với ý định thiết kế gốc (mục 1), đóng lỗ hổng thật trước khi có tenant thật ghi dữ
liệu riêng — tức sửa "trong lúc rẻ" thay vì đợi có dữ liệu thật rồi mới phát hiện leak.

### Hướng B — Chấp nhận platform-wide chính thức: xoá RLS, đổi `tenant_id` thành cột ghi chú

Việc cần làm:
1. Với `seo_context` cụ thể (phạm vi chính AA-544): `DROP POLICY`, `ALTER TABLE ... DISABLE ROW
   LEVEL SECURITY` (hoặc `NO FORCE` + drop policy), giữ cột `tenant_id` lại (không xoá — vẫn hữu
   ích cho audit/debug, chỉ không còn là cơ chế bảo mật) — 1 migration nhỏ.
2. Cập nhật `CONTEXT.md`'s cross-tenant table: thêm `seo_context` là cơ chế cross-tenant thứ 4,
   với chú thích rõ ràng nó khác loại 3 cơ chế kia (accidental/pragmatic, không phải chủ đích từ
   đầu — xem mục 4).
3. Quyết định riêng (ngoài phạm vi 1 migration): 19 bảng còn lại (mục 3) có cùng áp dụng Hướng B
   không, hay để nguyên as-is (RLS "trang trí", không gây hại gì thêm nhưng cũng không bảo vệ gì)
   cho tới khi có nhu cầu thật. Nếu để nguyên, nên ghi rõ trong `CLAUDE.md`/`CONTEXT.md` rằng RLS
   trong toàn repo này hiện là **không có hiệu lực enforcement thật** (chỉ còn ý nghĩa tài liệu),
   để không ai — người hay AI — hiểu nhầm nó đang bảo vệ gì trong lúc audit sau này (chính là điều
   AA-543 Phần 4.2 và AA-544 vừa gặp phải).

Effort: **Thấp.** 1 migration nhỏ cho `seo_context` (nếu chỉ làm phạm vi chính) + 1 đoạn cập nhật
CONTEXT.md. Nếu mở rộng cho cả 19 bảng còn lại, vẫn chỉ là DROP POLICY hàng loạt, không đổi kiến
trúc kết nối — có thể gộp 1 migration.

Rủi ro: **Thấp về mặt vận hành ngay bây giờ** (0 tenant thật có dữ liệu riêng ở bất kỳ bảng nào
trong 20 bảng này — hiện trạng thực tế production đã platform-wide-trong-thực-tế dù RLS nói khác,
nên xoá RLS không đổi hành vi thật nào cả). Rủi ro thật nằm ở **tương lai**: nếu sau này có tenant
thật cần cách ly dữ liệu (ví dụ B2B tenant lo ngại lộ nội dung SEO cho tenant khác), sẽ phải làm lại
từ đầu theo Hướng A — tức là Hướng B không phải "sửa xong", mà là "hoãn nợ kỹ thuật có ghi chép rõ
ràng", đánh đổi lấy việc không phải touch kiến trúc kết nối DB ngay bây giờ khi chưa có nhu cầu thật.

## 6. Việc KHÔNG làm trong investigation này

- Không sửa code, không tạo/xoá migration nào.
- Không tự chọn Hướng A hay B — chờ Nghiệp xác nhận trong Linear.
- Không set Linear issue Done.
- Không mở rộng sang thiết kế lại Segment/Score/Route/Hub (AA-543/AA-545, độc lập).

---

## Round 2 (10/09/2026) — Điều tra theo mô hình tách 2 connection pool

Ngữ cảnh: comment mới nhất trên AA-544 chốt Hướng A theo mô hình tách pool (Admin giữ
`aa_cis_admin` bypass; Tenant Portal chuyển `aa_app_user` non-bypass + set GUC), không phải "bật
RLS toàn hệ thống" như ước lượng ban đầu ở round 1. 5 việc cần điều tra trước khi thiết kế chi
tiết — dưới đây.

### 7. 4 luồng cross-tenant có chủ đích — gọi từ đâu?

| Luồng | Bảng | Router/entrypoint | Auth dependency | Gọi từ |
|---|---|---|---|---|
| **Master Content pool** | `gold_aa_internal.published_tours` (`tenant_id = aa_internal` sentinel) | `GET /v1/tours/pool` (`browse_pool()`, `api/routers/v1_tours.py:114-207`) | `Depends(get_tenant)` — tenant JWT only | **Chỉ `/portal/*`** (Tenant Portal frontend, tenant JWT thật) |
| **Search Demand** | `acp_contract.search_demand` + `segment_research_log` (migration 130) — **không có cột `tenant_id`**, không nằm trong danh sách 20 bảng có RLS | `_run_research_only()` (`v1_tours.py:38-57`, trigger nội bộ trong luồng T2 rewrite) | (không phải 1 endpoint riêng — chạy nền sau khi tenant gọi rewrite) | **Chỉ `/portal/*`** (tenant trigger), nhưng KHÔNG liên quan RLS — bảng không có RLS |
| **Facts Entry (platform scope)** | `acp_shared.facts` (migration 145) | `fetch_facts_for_writing()` (`services/acp_content_writing/facts.py`), gọi từ T9 write (`v1_content_writing.py`) | `Depends(get_tenant)` | **Chỉ `/portal/*`** — chưa có endpoint admin-write thật (comment trong `facts.py`: "No write-side service function here on purpose... UI... deferred") |
| **F10 cannibalization gate** | `acp_shared.content_piece` (migration 115) | `gate_cannibalization()` → `find_similar_pieces(cross_tenant=True)` (`services/acp_shared/piece_similarity.py`, query `_CROSS_TENANT_QUERY` — **0 filter tenant**), gọi từ `service.py:482-483` trong `POST /v1/content-writing/{request_id}/write` | `Depends(get_tenant)` | **Chỉ `/portal/*`** |

**Kết luận mục 7**: cả 4 luồng đều chỉ được GỌI từ phía Tenant Portal (không có luồng nào admin
tự gọi trực tiếp) — nhưng 2 trong 4 (Master Content pool, F10 gate) cần ĐỌC XUYÊN TENANT ngay bên
trong 1 request tenant-authenticated. Đây chính là điểm xung đột với mô hình tách-pool đơn giản —
xem mục 9.

Chi tiết 2 xung đột:

- **Master Content pool** (`browse_pool()`, dòng 127-128 chính code đã tự ghi chú: *"Browse AA
  shared pool (published_tours from aa_internal). All active tenants can read the pool — RLS
  bypassed via aa_internal filter."*): query cứng `pt.tenant_id =
  '00000000-0000-0000-0000-000000000001'::uuid` — đọc row thuộc sở hữu sentinel `aa_internal`, KHÔNG
  phải tenant gọi request. Nếu Tenant Portal pool chuyển sang `aa_app_user` + set
  `app.tenant_id` = tenant_id THẬT của người gọi, RLS (`tenant_id = current_setting(...)`) sẽ chặn
  toàn bộ — tính năng "duyệt kho chung" (core feature P3-S4) sẽ trả về 0 kết quả, không lỗi, không
  cảnh báo.
- **F10 cannibalization gate**: `_CROSS_TENANT_QUERY` (`piece_similarity.py:44-53`) hoàn toàn
  không có `WHERE tenant_id = ...` — đọc `content_piece` của MỌI tenant khác để so sánh độ trùng
  lặp nội dung (ngưỡng cosine 0.92, gate BLOCKING thật). Cùng lý do: dưới RLS thật, query này sẽ
  chỉ thấy piece của chính tenant gọi — gate sẽ luôn "pass" (không bao giờ phát hiện trùng lặp
  chéo tenant nữa), lặng lẽ, không lỗi, không log bất thường.

Khác với 2 luồng trên, **Facts Entry không xung đột**: policy RLS của `acp_shared.facts`
(migration 145) đã có sẵn `USING (scope = 'platform' OR tenant_id::text =
current_setting('app.tenant_id', true))` — khớp CHÍNH XÁC với điều kiện `WHERE scope = 'platform'
OR (scope = 'tenant' AND tenant_id = $1)` mà `fetch_facts_for_writing()` đã tự lọc ở tầng app. Đây
là ví dụ đúng của việc "bake platform-scope exception vào chính policy" — không cần escape hatch gì
thêm.

### 8. Cơ chế phân biệt admin/tenant đã có sẵn — có, nhưng KHÔNG tập trung

Có, ở tầng HTTP auth — nhưng thực hiện rải rác, không qua 1 điểm chung:

- **Tenant JWT** (`role: "tenant"` trong payload, ký bởi `_create_jwt()`) — decode qua hàm
  `get_tenant()`, nhưng hàm này được **copy-paste độc lập** trong `v1_tours.py` VÀ `v1_exports.py`
  (2 bản giống hệt nhau, không import chung 1 module).
- **Admin** — 2 cơ chế khác nhau cùng tồn tại song song: (a) `X-Admin-Secret` header so khớp
  `ADMIN_SECRET` env var (dùng trong `admin.py`/`admin_pipeline.py`/`admin_atoms.py`/... và trong
  `verify_tenant_api_key()` của `auth.py`), (b) admin JWT riêng (`_create_admin_jwt()`, `role:
  "admin"|"reviewer"`, dùng cho `/auth/admin-login`).
- **`rate_limit_middleware`** (`api/middleware/rate_limit.py`, wired global cho mọi request,
  `api/main.py:144`) đã có sẵn logic rẽ nhánh `path.startswith("/admin/")` vs `/v1/*` — NHƯNG với
  `/v1/*`, nếu request không có header `Authorization: Bearer ...` (tức dùng `X-Admin-Secret` thay
  vào), middleware này **im lặng bỏ qua hoàn toàn** (dòng 76-78: `if not auth.startswith("Bearer
  "): return await call_next(request)`) — không nhận diện, không track, không rate-limit. Tức là
  middleware này KHÔNG phải điểm hook sẵn sàng dùng ngay cho việc chọn pool — cần sửa thêm.

**Kết luận mục 8**: tín hiệu phân biệt admin/tenant tồn tại thật (ở tầng JWT/header), nhưng codebase
hiện có **ít nhất 4 biến thể hàm auth khác nhau** rải rác qua nhiều router file
(`get_tenant`/`_get_tenant`(dual-mode)/`verify_tenant_api_key`/admin JWT riêng) — không có 1 điểm
tập trung để hook logic "chọn pool theo danh tính" vào. Đây là phần việc thật cần làm trước khi
switch pool, không chỉ đổi `DATABASE_URL`.

### 9. Luồng gọi từ CẢ 2 phía — có, phát hiện mới ngoài 4 luồng được nêu — BÁO LẠI, KHÔNG TỰ QUYẾT

**`api/routers/v1_s0.py`** định nghĩa `_get_tenant()` (dòng 44-57) chấp nhận **CẢ 2**: hoặc
`X-Admin-Secret` đúng (trả về danh tính sentinel `00000000-...-0001`, `role: "admin"`) HOẶC 1 tenant
JWT hợp lệ qua Bearer — **CÙNG 1 code path, cùng 1 endpoint**. Các endpoint dùng dependency này
(`Depends(_get_tenant)`, dòng 83/178/219/243) đọc/ghi trực tiếp **`silver_aa_internal.raw_tours`**
— bảng ĐÃ có RLS + `FORCE ROW LEVEL SECURITY` từ migration 004/008. Đây là trường hợp phức tạp thật
sự: KHÔNG THỂ tách pool theo "router file" hay "URL prefix" cho endpoint này — cùng 1 route phải
dùng admin pool (bypass) khi caller là admin, và tenant pool (RLS-enforced) khi caller là tenant
thật, quyết định NGAY TRONG lúc xử lý request, không phải tại thời điểm đăng ký router.

`api/routers/v1_competitors.py` có **cùng pattern `_get_tenant()` dual-mode y hệt** (dòng 23-36),
nhưng bảng đích (`acp_silver_s2.competitor_inputs`) KHÔNG nằm trong danh sách 20 bảng có RLS — nên
về mặt RLS không xung đột, nhưng vẫn cùng 1 vấn đề kiến trúc (route không đơn-danh-tính).

Kiểm tra thêm (frontend, không phải suy đoán): `grep` toàn bộ `frontend/` chỉ tìm thấy
`/v1/competitors` được gọi từ ĐÚNG 1 nơi — `frontend/app/(tenant)/portal/_components/
CompetitorsTab.tsx` (Tenant Portal, luôn dùng JWT thật, không dùng nhánh admin trong thực tế hiện
nay). `/v1/s0` **không có bất kỳ frontend caller nào** (không `/admin/*`, không `/portal/*`) — có
vẻ là endpoint chết/chưa nối UI, nhưng code vẫn hỗ trợ dual-mode thật, và `rate_limit_middleware`
(mục 8) không track được nhánh admin-secret trên `/v1/*` nên không thể loại trừ hoàn toàn có caller
khác (Swagger/curl trực tiếp/tool nội bộ) đang dùng nhánh đó.

**→ Báo lại theo đúng yêu cầu, KHÔNG tự quyết**: `v1_s0.py` là trường hợp cần thiết kế riêng trước
khi tách pool — ít nhất cần xác nhận (a) endpoint này còn dùng thật không (không frontend nào gọi),
(b) nếu còn dùng, việc chọn pool phải dựa trên `role` đã resolve được SAU KHI auth chạy xong, không
phải theo router/file như giả định ban đầu.

### 10. Effort/rủi ro ước tính lại theo đúng mô hình tách-pool

So với ước tính "Hướng A" ban đầu (round 1, giả định đổi `DATABASE_URL` toàn hệ thống) — mô hình
tách-pool THỰC SỰ thu hẹp phạm vi đáng kể, vì **phía Admin hoàn toàn không đổi** (vẫn
`aa_cis_admin`, vẫn bypass, 0 rủi ro cho các luồng admin đang chạy live). Nhưng vẫn còn việc thật,
không phải "1 migration nhỏ":

**Việc cần làm:**
1. `aa_app_user`: đổi password khỏi hardcode trong migration file → Secrets Manager; bổ sung GRANT
   cho 7 bảng ACP-era còn thiếu (từ báo cáo round 1, mục 3) — ít nhất những bảng Tenant Portal thật
   sự sẽ chạm tới.
2. Thêm pool thứ 2 trong `api/main.py` (dùng `aa_app_user` DSN), song song pool hiện tại — không
   đụng pool cũ.
3. **Tập trung hoá** ít nhất 4 biến thể hàm auth (mục 8) về 1 điểm — đây là phần việc refactor thật,
   không nhỏ, vì rải qua ≥9 router file (`v1_marketplace.py`, `v1_angle_gate.py`, `v1_publish.py`,
   `v1_route_hub.py`, `v1_tours.py`, `v1_planning.py`, `v1_content_writing.py`, `v1_exports.py`,
   `v1_integrations.py`, cộng `v1_s0.py`/`v1_competitors.py` dual-mode) — điểm hook chọn pool phải
   nằm SAU khi danh tính được resolve (role tenant vs admin-sentinel), không phải trước.
4. `set_config('app.tenant_id', ...)` — set 1 lần đúng chỗ mỗi khi acquire connection từ pool MỚI
   (không rải rác theo từng repository như `RawTourRepository` hiện làm).
5. **Quyết định riêng** (không tự chọn ở đây) cách xử lý 2 xung đột thật (mục 7 — Master Content
   pool, F10 gate): hoặc (a) 2 query cụ thể này tiếp tục dùng pool admin (bypass) ngay cả khi được
   gọi từ tenant-authenticated request — escape hatch ở tầng query, phạm vi hẹp, không mở rộng
   quyền đọc chung; hoặc (b) sửa policy RLS của 2 bảng này thêm điều kiện OR như `acp_shared.facts`
   đã làm — đơn giản hơn về code, nhưng MỞ RỘNG quyền SELECT cho MỌI query trên bảng đó qua pool
   tenant (kể cả những query tương lai chưa viết), không chỉ riêng 2 flow đã biết — rủi ro bảo mật
   rộng hơn (a).
6. **Quyết định riêng** cách xử lý `v1_s0.py`/`v1_competitors.py` (mục 9) — chọn pool theo `role`
   đã resolve, không theo router.
7. Viết lại test RLS để chạy thật lên RDS dev (gap đã nêu ở round 1) — bắt buộc trước khi cutover,
   đặc biệt test 2 tenant đồng thời để bắt race condition GUC trên connection tái sử dụng.

**Effort**: **Trung bình** (hạ từ "Cao" ở round 1) — không phải kiến trúc lại toàn bộ kết nối DB,
nhưng vẫn là refactor thật qua ~11 router file + 1 quyết định thiết kế cho mỗi trong 2 nhóm xung đột
(mục 5, 6 ở trên). Không còn cần audit "mọi luồng admin có thể gãy" như round 1 (vì admin pool
không đổi) — phạm vi audit giờ thu hẹp còn: mọi endpoint `/v1/*` (và bất kỳ route nào dùng
`_get_tenant()` dual-mode) cần rà xem có đọc bảng RLS theo kiểu "ngoài phạm vi tenant của chính
mình" hay không, giống cách đã làm với 2 xung đột ở mục 7.

**Rủi ro**: rủi ro với **Admin = gần như 0** (pool không đổi). Rủi ro dồn hết vào pool Tenant mới:
- Thiếu 1 GRANT → lỗi `permission denied` (500, ồn ào, dễ bắt khi test) — an toàn hơn hiện trạng
  (hiện trạng: leak âm thầm, không lỗi).
- 2 xung đột đã biết (mục 7) nếu KHÔNG xử lý trước khi cutover → hỏng tính năng thật (kho chung
  trống, F10 gate mất tác dụng) — lặng lẽ, không lỗi, không log — đây là rủi ro cụ thể nhất, phải
  chặn trước khi bật pool mới cho bất kỳ route nào chạm 2 luồng này.
- `v1_s0.py` nếu chuyển pool sai (theo router thay vì theo role) → nhánh admin của endpoint này sẽ
  bị RLS chặn nhầm khi gọi bằng `X-Admin-Secret` (admin sentinel tenant_id không khớp bất kỳ hàng
  raw_tours thật nào) — hỏng nhánh admin dù rủi ro thấp (chưa xác nhận có caller thật).
- Rủi ro nặng nhất về lý thuyết (chưa xảy ra, cần test riêng): asyncpg pool tái sử dụng connection
  giữa các request — nếu `set_config` không reset đúng khi connection quay về pool, 1 request của
  tenant A có thể vô tình thừa hưởng GUC còn sót của tenant B trên cùng connection → leak dữ liệu
  thật. Bắt buộc có test 2-tenant-đồng-thời trước khi cutover bất kỳ route nào.

### 11. Đề xuất thứ tự triển khai an toàn — có rollback ở mỗi bước

1. **Stage 0 — chuẩn bị hạ tầng, 0 thay đổi hành vi**: đổi password `aa_app_user` qua Secrets
   Manager, bổ sung GRANT còn thiếu. Không route nào dùng role này — hoàn toàn reversible (chưa ai
   dùng đến).
2. **Stage 1 — pool mới, 1 route rủi ro thấp nhất, sau 1 feature flag**: thêm pool thứ 2 trong
   code, chọn 1 endpoint đã filter đúng theo tenant ở tầng app và KHÔNG nằm trong 2 xung đột đã biết
   (ví dụ `GET /v1/tours` — `list_tours()`, đã `WHERE pt.tenant_id = $1` sẵn, trùng khớp policy RLS
   100%) — bật qua env var (`TENANT_POOL_ENABLED` hoặc tương đương), tắt được ngay lập tức không
   cần deploy lại nếu có sự cố.
3. **Stage 2 — test 2-tenant-đồng-thời trên RDS dev thật**: xác nhận (a) tenant A không bao giờ thấy
   dữ liệu tenant B qua route đã bật ở Stage 1, (b) không có GUC leak khi connection tái sử dụng
   dưới tải đồng thời.
4. **Stage 3 — xử lý 2 xung đột đã xác nhận (mục 7)**: cần quyết định (a) hay (b) ở mục 10.5 trước,
   sau đó mới bật pool mới cho `browse_pool()` và luồng `write()`/F10 gate.
5. **Stage 4 — xử lý `v1_s0.py`/`v1_competitors.py` (mục 9)**: xác nhận còn dùng thật không; nếu
   còn, chuyển chọn-pool sang dựa theo `role` đã resolve (không theo router) trước khi bật.
6. **Stage 5 — mở rộng dần từng route/router còn lại** trong danh sách `Depends(get_tenant)` (mục
   8), theo dõi `X-RateLimit-*`/Sentry/error rate sau mỗi route — mỗi route độc lập, revert riêng lẻ
   được qua flag.
7. **Stage 6 — dọn dẹp**: sau khi toàn bộ `/v1/*` đã chuyển và soak-test ổn định, gỡ flag; xét riêng
   (không thuộc phạm vi issue này) có áp Hướng B (xoá RLS/dọn GUC chết) cho 3 bảng dùng
   `app.current_tenant` (round 1 mục 3) và các bảng ACP-era chưa từng được Tenant Portal chạm tới.

**Rollback ở bất kỳ stage nào**: tắt flag → toàn bộ traffic quay lại pool `aa_cis_admin` hiện tại
(hành vi y hệt bây giờ). Không cần revert migration nào — GRANT thêm ở Stage 0 vô hại nếu để lại dù
rollback toàn bộ.

---

## Round 3 (10/09/2026) — `v1_s0.py` còn dùng thật hay đã chết?

Yêu cầu: CHỈ xác nhận `v1_s0.py` còn dùng hay chết (CloudWatch + Notion/ADR), báo cáo qua comment,
KHÔNG code, KHÔNG bắt đầu Stage 0.

### A. CloudWatch (`/ecs/aa-cis-dev`, retention 14 ngày — cửa sổ tối đa còn truy được)

Logs Insights `filter @message like /v1\/s0/` trên toàn bộ 14 ngày → 24 dòng match, gần nhất
07/09/2026. Thoạt nhìn có vẻ "còn traffic" — nhưng truy lại TOÀN BỘ request cùng source IP/port
(`10.2.2.162:26144`, `10.2.1.137:22822`) trong cùng khung giờ thì lộ rõ bản chất: đây là **bot quét
lỗ hổng tự động**, không phải người dùng thật. Cùng 1 burst request (cách nhau <1s mỗi dòng) gồm cả
`/v1/s0/review`, `/v1/s0/approve`, `/v1/s0/reject` XEN LẪN với các path dò lỗ hổng kinh điển:
`/.env.local`, `/.git/HEAD`, `/wp-login.php`, `/phpinfo.php`, `/backup.sql`, `/.DS_Store`,
`/actuator/health`, `/swagger/v1/swagger.json`, `/v2/api-docs`, `/Gemfile`, `/.well-known/
security.txt` — toàn path dò scan chung, không liên quan gì riêng tới S0. Bot vào qua
`/docs/oauth2-redirect` (Swagger UI, trả 200 — bản thân việc Swagger public cũng đáng lưu ý riêng,
ngoài phạm vi round này) rồi duyệt máy qua toàn bộ route khai báo trong OpenAPI schema, kể cả
`/v1/s0/*`. Tất cả request `/v1/s0/*` quan sát được đều 401 (GET review, thiếu auth) hoặc 405 (GET
lên endpoint chỉ nhận POST — approve/reject) — không có request thành công nào, không có pattern
giống người dùng thật (không có sequence review→edit→approve hợp lý, không cùng 1 JWT/session).

**Kết luận A**: 24 dòng log KHÔNG chứng minh có người dùng thật — là nhiễu bot quét tự động, giống
hệt cách nó cũng quét cả `/wp-login.php` (route không tồn tại trong app này).

### B. Notion — đối chiếu ACP PRD / Pipeline Spec

Tìm thấy CHÍNH XÁC bản thiết kế khớp `v1_s0.py`: **"📘 ACP PRD v1.3 — AUTHORITATIVE (21/05/2026)"**
— trích: *"GET /v1/s0/review/queue List raw_tours..."*, *"raw_tours.review_status: NULL →
pending_review → approved | rejected"* — khớp 100% với `v1_s0.py` (built AA-44, 19/05/2026, 2 ngày
trước bản PRD này). Xác nhận: `v1_s0.py` ĐÚNG LÀ hiện thực hoá 1 thiết kế thật đã từng được ghi
trong PRD.

**Nhưng** — trang này nằm trong folder Notion **"🗄️ Archive — superseded (pre v0.1.0)"**, và trang
mục lục của folder đó tự ghi rõ: *"kept for history only. They are superseded by the Source of
Truth (dev v0.1.0) pages."* Đối chiếu tiếp bản **Source of Truth — dev v0.2.0** (mới hơn, 25/06–
11/07/2026) — trang "12 · Stage / Pipeline Spec (S0–S4.2)" định nghĩa lại "S0" thành khái niệm
KHÁC HẲN: *"S0 — upload + brand brief → `silver_aa_internal.upload_staging`"* (một bảng khác, mục
đích khác — tenant/brand-brief upload, không phải review raw_tours trước khi generate). Tức là
ngay trong Notion, khái niệm "S0" đã bị ĐỊNH NGHĨA LẠI 1 lần (PRD v1.3 → dev v0.2.0) trước khi
`v1_s0.py` kịp theo kịp thay đổi nào.

Xa hơn nữa: toàn bộ pipeline S0-S4.2 trong bản dev v0.2.0 đó (gates `/v1/acp/gate/gate1/approve`,
`/v1/acp/gate/s3/approve`, bảng `acp_run_context`...) chính là **ACPv1 — đã bị Nghiệp/session trước
XOÁ HẲN thật** (`AA-477`, 27/08/2026, CLAUDE.md: "ACPv1 teardown... 21 dead tables dropped"),
thay bằng ACPv2 (T0-T11, ADR-2026-038). Không endpoint `/v1/acp/gate/*` nào trong bản dev v0.2.0
này còn tồn tại trong code thật hôm nay (đã kiểm chứng qua các round trước — `api/main.py` không
có router nào tên như vậy).

**Kết luận B**: "S0 Input Manager" trong Master Implementation Plan/ACP PRD, nếu có, chỉ tồn tại
dưới 2 dạng: (1) bản PRD v1.3 gốc — khớp code `v1_s0.py`, nhưng bản này đã bị chính Notion đánh dấu
"superseded" từ lâu; (2) bản dev v0.2.0 định nghĩa lại "S0" = upload+brand-brief cho ACPv1 — pipeline
này đã bị xoá hẳn khỏi code thật (AA-477). **Không có bản kế hoạch NÀO còn hiệu lực hôm nay nhắc tới
việc dùng lại/hoàn thiện tiếp `v1_s0.py`**.

### Xác nhận cuối: `v1_s0.py` — CHẾT, có bằng chứng 3 nguồn độc lập

1. **Git history** (round 2): 0 file frontend nào từng gọi `/v1/s0` trong toàn bộ lịch sử repo.
2. **CloudWatch** (round 3.A): traffic duy nhất là nhiễu bot quét lỗ hổng, không phải người dùng
   thật.
3. **Notion** (round 3.B): thiết kế gốc khớp code đã bị archive từ 21/05→25/06/2026; khái niệm "S0"
   sau đó bị định nghĩa lại rồi cả pipeline chứa nó bị xoá hẳn (AA-477).

Đề xuất của Nghiệp trong comment trước ("nếu xác nhận chết: comment out hoặc xoá hẳn route thay vì
tốn công thiết kế chọn-pool-theo-role cho code chết") — dữ liệu điều tra ủng hộ nhánh "đã chết".
Nhưng đây là ĐỀ XUẤT, chưa phải quyết định — theo đúng yêu cầu, DỪNG LẠI ở đây chờ Nghiệp xác nhận,
KHÔNG tự xoá/comment-out code, KHÔNG bắt đầu Stage 0.

---

## Round 4 (10/09/2026) — "S0 Input Manager" (upload Excel thật) có liên quan `v1_s0.py` không?

Yêu cầu: xác nhận bằng CODE THẬT (không chỉ tài liệu) 3 câu hỏi — route/file nào xử lý upload Excel
hôm nay, có dùng chung file/hàm với `v1_s0.py` không, và liệu 2 file có phải 2 giai đoạn của cùng 1
luồng cũ (upload → review). DỪNG LẠI sau báo cáo, không code.

### Q1 — Route/file thật xử lý "upload tour thô từ Excel" hôm nay

Trace từ frontend thật: `frontend/app/admin/upload/page.tsx` gọi:
- `GET /api/admin/upload-staging/{batchId}` → `api/routers/admin_pipeline.py:1276`
  (`list_upload_staging`)
- `POST /api/admin/upload-staging/{staging_id}/decide` → `admin_pipeline.py:1333`
  (`decide_staging`)
- (cùng file, không trong đoạn trích) `POST /admin/upload-url` (`:1075`), `POST /admin/ingest-s3`
  (`:1096`), `POST /admin/brand-identity/upload` (`:4294`, brand brief).

Ingestion thật (S3-triggered, ExcelParser): `services/ingestion/handler.py` — import
`from .excel_parser import ExcelParser` → file thật là **`services/ingestion/excel_parser.py`**
(không phải `api/services/excel_parser.py` như CLAUDE.md ghi — path đó lệch, ngoài phạm vi sửa ở
đây). `handler.py` dùng `RawTourRepository`/`RawSourceRepository` (`shared/repository/`).

Cả 2 file thật (`admin_pipeline.py`, `services/ingestion/handler.py`) auth bằng
`x_admin_secret: str = Header(None)` — khác cả `get_tenant()` (JWT-only) LẪN `_get_tenant()`
(dual-mode) mà round 2 đã nêu — tức đây là biến thể auth thứ 3.

### Q2 — Có dùng chung file/hàm với `v1_s0.py` không? XÁC NHẬN 100%: KHÔNG

- `grep` toàn repo cho `import v1_s0\|from api.routers.v1_s0\|v1_s0_router` → CHỈ 2 dòng, cả 2 đều
  ở `api/main.py` (đăng ký router: `from api.routers.v1_s0 import router as v1_s0_router` +
  `app.include_router(v1_s0_router)`) — thuần đăng ký route, không có logic dùng chung.
- `v1_s0.py` tự nó chỉ import `fastapi`/`structlog`/`datetime`/auth — không import gì từ
  `admin_pipeline.py`, `services/ingestion/*`, hay `excel_parser.py`.
- `services/ingestion/handler.py` không import gì từ `v1_s0.py`.

**→ 2 file hoàn toàn độc lập về code — 0 import, 0 gọi hàm chéo, chỉ chung 1 chỗ duy nhất:
`api/main.py` đăng ký cả 2 làm router riêng biệt.**

### Q3 — Có phải 2 giai đoạn của CÙNG 1 luồng cũ (upload → review), chỉ 1 nửa còn sống?

**Đúng — xác nhận bằng dữ liệu, không phải suy đoán tên gọi.** Cả 2 file CÙNG thao tác trên
`silver_aa_internal.raw_tours`, và migration tạo ra 4 cột review (`review_status`, `reviewed_by`,
`reviewed_at`, `review_notes`) — `api/migrations/024_s0_review_status.sql` — tự ghi rõ trong header:
*"Ticket: AA-44 — S0 Data Quality Review"* — CHÍNH LÀ ticket đã tạo `v1_s0.py` (cùng ngày
19/05/2026). Tức 2 file này ban đầu ĐÚNG LÀ 2 giai đoạn 1 thiết kế: **upload → staging → (review qua
v1_s0.py) → approved**.

Bằng chứng cụ thể luồng review đã đứt, không chỉ là suy đoán:

- `decide_staging()` (`admin_pipeline.py:1333-1470`, đường sống duy nhất đưa row vào `raw_tours`
  hôm nay qua UI) — câu `INSERT INTO silver_aa_internal.raw_tours (...)` ở dòng ~1409 **KHÔNG liệt
  kê cột `review_status`** trong danh sách cột insert. `RawTourRepository.insert()`
  (`shared/repository/raw_tour_repository.py`, đường ingest S3/Lambda) **cũng không** liệt kê cột
  này.
- Vì `review_status` có `DEFAULT 'pending_review'` (migration 024), **mọi row `raw_tours` do 2
  đường sống này tạo ra đều tự động dừng ở `pending_review` — VĨNH VIỄN**, vì không còn code sống
  nào tiến trạng thái này tiếp (chỉ `v1_s0.py`'s PATCH/approve/reject mới làm việc đó, và nó chết).
  Đây không phải lỗi mới — là hệ quả trực tiếp, đang tích luỹ mỗi lần có tour mới, của việc nửa
  "review" trong thiết kế gốc đã bị bỏ dở.
- Rà toàn bộ `review_status` khác trong code sống (để không nhầm lẫn) — TẤT CẢ tham chiếu
  `review_status` còn lại trong live code (`v1_pipeline.py`, `admin_pipeline.py` các dòng khác,
  `admin_a4.py`, `services/acp_produce/packets.py`) là **CỘT KHÁC, BẢNG KHÁC** —
  `review_queue.review_status` (content review, AA-234/240/241) hoặc `content_piece.review_status`
  (migration 105, T10) — không liên quan `raw_tours.review_status`. Riêng
  `services/acp_canary/lambda_handler.py:69,98` CÓ set `raw_tours.review_status='approved'` trực
  tiếp qua SQL — nhưng đây là script seed fixture cho canary/test, ghi cứng giá trị, bỏ qua hẳn quy
  trình review (không gọi `v1_s0.py`).

**Phát hiện phụ (không phải câu hỏi gốc, nhưng liên quan trực tiếp "XLSX validation ≥8/10 required
fields" Nghiệp trích từ Master Implementation Plan)**: không tìm thấy logic validate field-coverage
nào trong đường ingest sống (`services/ingestion/handler.py`, `services/ingestion/excel_parser.py`
— 0 match "coverage"/"required"). Logic coverage-percentage DUY NHẤT trong toàn repo là
`v1_s0.py::_field_coverage_pct()` — nhưng tính trên **7 field** (không phải 8/10), trả về %
hiển thị (không phải cổng chặn cứng), và đang chết. Tức tiêu chí "≥8/10 required fields" trong
Master Implementation Plan có vẻ **chưa từng được hiện thực hoá ở đường sống** — không phải đã có
sẵn trong `v1_s0.py` chờ dùng lại (khác số field, khác cơ chế).

### Kết luận Round 4

1. **Route thật xử lý upload Excel hôm nay**: `admin_pipeline.py` (`/admin/upload-url`,
   `/admin/ingest-s3`, `/admin/upload-staging/*`, `/admin/brand-identity/upload`) +
   `services/ingestion/handler.py` + `services/ingestion/excel_parser.py`.
2. **Độc lập 100% với `v1_s0.py`** — xác nhận bằng grep import/reference, không phải suy đoán.
3. **Đúng là 2 giai đoạn của 1 thiết kế cũ** (cùng ticket AA-44, cùng migration 024, cùng bảng/cột
   `raw_tours.review_status`) — nhưng chỉ giai đoạn "upload" (qua `upload_staging`) còn sống, giai
   đoạn "review" (`v1_s0.py`) đã chết y như round 3 xác nhận. Xoá `v1_s0.py` **không ảnh hưởng** gì
   tới luồng upload Excel thật đang chạy (0 code liên kết) — nhưng khoảng trống "review" mà nó từng
   định lấp (mọi tour mới kẹt ở `pending_review` mãi mãi) **vẫn còn đó dù xoá hay không xoá
   `v1_s0.py`** — xoá file chỉ dọn code chết, không tạo ra và cũng không giải quyết gap review này.
4. Phát hiện phụ: tiêu chí "XLSX validation ≥8/10 required fields" từ Master Implementation Plan
   chưa thấy hiện thực ở đường sống — nếu Nghiệp coi đây là việc cần làm, đó là 1 issue/tính năng
   MỚI cần build (không phải khôi phục lại gì có sẵn), độc lập với quyết định xoá/giữ `v1_s0.py`.

**DỪNG LẠI — không code, không xoá/sửa `v1_s0.py`, không đụng gì khác. Chờ Nghiệp xác nhận.**

---

## Round 5 (10/09/2026) — Xoá `v1_s0.py` (đã xác nhận) + review_status có chặn gì không?

Nghiệp xác nhận cho phép xoá ở round 4. 2 việc độc lập, làm cùng lượt theo yêu cầu.

### Việc 1 — Đã xoá `v1_s0.py`

- Xoá `api/routers/v1_s0.py` (263 dòng) + `tests/unit/test_s0.py` (136 dòng, chỉ test module đã
  xoá) + 2 dòng đăng ký router trong `api/main.py` (import + `app.include_router`).
- Verify trước khi commit: `api.main` import sạch (183 route đăng ký, 0 path `/s0` còn lại),
  `flake8 api/main.py` sạch, toàn bộ unit test suite collect sạch (1935 test, 0 lỗi).
- Branch mới `pqnghiep1354/aa-544-remove-dead-v1-s0` (từ `main` mới nhất) — không dùng lại branch
  `aa-576-...` cũ đang active trước đó trong session (đã merge, không liên quan).
- PR #365, `chore: remove dead v1_s0.py S0 review route [AA-544]`, 5 required check pass (Lint,
  Security Audit, Unit Tests, Integration Tests, Docker Build Check) — auto-merge (solo-operator
  mode). **Merged vào `main` lúc 09:56:18 UTC 10/09/2026.**
- Migration `024_s0_review_status.sql` GIỮ NGUYÊN (không xoá/sửa migration đã apply — 4 cột
  `review_status`/`reviewed_by`/`reviewed_at`/`review_notes` vẫn còn trên `raw_tours`, vô hại nếu
  để lại, xem Việc 2 dưới).

### Việc 2 — `review_status='pending_review'` vĩnh viễn có chặn gì trong luồng sống không?

**KHÔNG — xác nhận bằng grep toàn repo, không phải suy đoán.** Đã rà TOÀN BỘ tham chiếu
`review_status` còn lại trong code sống (sau khi xoá `v1_s0.py`):

- `api/routers/v1_pipeline.py`, `admin_pipeline.py` (dòng ~2035-2166), `admin_a4.py`,
  `services/validation/handler.py` — tất cả đọc/ghi **`review_queue.review_status`** (alias `rq`) —
  bảng review NỘI DUNG ĐÃ SINH (generated_content, AA-234/240/241 HITL flow), khác hẳn
  `raw_tours.review_status`.
- `services/acp_produce/packets.py` — đọc/ghi **`content_piece`/pieces `review_status`** (migration
  105, T10) — cũng khác bảng.
- `services/acp_canary/lambda_handler.py:69,98` — set cứng `raw_tours.review_status='approved'`
  qua SQL trực tiếp trong script seed fixture canary/test, không qua workflow nào — không phải 1
  gate đọc điều kiện này, chỉ ghi 1 chiều.
- **0 kết quả** cho bất kỳ `WHERE`/`AND`/`FILTER` nào kiểm tra `raw_tours.review_status` trước khi
  cho publish/dùng tiếp, ở bất kỳ router hay service nào (`admin_pipeline.py`, `v1_tours.py`,
  `services/export/handler.py`, `services/acp_planning/*`, v.v.).

Cột gate THẬT cho vòng đời `raw_tours` là **`pipeline_status`** (khác cột, khác cơ chế) — xác nhận
qua chính code sống: `services/export/handler.py:157` (`WHERE ... pipeline_status = 'published'`
trước khi coi 1 batch đã xuất xong), `:195`/`:262` (set `'hitl_rejected'`/`'published'`),
`admin_pipeline.py:1618` (`WHERE t.pipeline_status = 'ingested'`). Toàn bộ luồng publish/pipeline
thật (A3 atomize, export, Master Content promotion) gate trên `pipeline_status`, không hề đọc
`review_status`.

Đã rà thêm phía frontend để chắc chắn: `frontend/app/admin/platform-stats/page.tsx` có hiển thị 1
trường tên `review_status`, nhưng nguồn dữ liệu là `GET /admin/a4/review-log` (`admin_a4.py`, đọc
`review_queue.review_status`) — không phải `raw_tours`. Không trang frontend nào đọc
`raw_tours.review_status`.

**Kết luận Việc 2**: gap này AN TOÀN — chỉ là dữ liệu "để đó", không chặn publish, không chặn
pipeline, không chặn bất kỳ query nào trong luồng sống. Không cần vá gấp; nếu Nghiệp muốn dọn dẹp
triệt để (xoá 4 cột chết hoặc build lại luồng review S0 thật), có thể xếp làm sau, không khẩn cấp.

### Việc 2b — `v1_s0.py` ngừng hoạt động từ ngày nào?

Không thể xác định 1 ngày "ngừng hoạt động" theo đúng nghĩa (route không hề bị lỗi/crash — nó vẫn
chạy đúng, chỉ đơn giản không ai gọi) — dữ liệu cho thấy câu hỏi đúng hơn là "nó có bao giờ thực sự
hoạt động thật không", và bằng chứng nghiêng về KHÔNG:

- **Reachable liên tục từ 19/05/2026** (AA-44 merge vào `main`) tới lúc xoá hôm nay (10/09/2026) —
  code luôn được deploy, route luôn đăng ký, không hề bị gỡ khỏi router giữa chừng.
- **Lần cuối có người thật động vào code**: `31383b1`, 11/06/2026 (AA-174) — fix bug 500 thật
  (`created_at` không tồn tại) — nghĩa là có người (Nghiệp, theo commit) còn test/dùng thủ công tới
  thời điểm đó, đủ để phát hiện và báo lỗi. Sau 11/06/2026: **0 commit nào khác từng chạm file này**
  cho tới khi xoá.
  - Riêng bằng chứng "còn thật sự được ai đó dùng liên tục sau 11/06/2026" — không xác định được
    vượt quá cửa sổ CloudWatch 14 ngày (round 3, chỉ còn nhiễu bot). Không có access log nào giữ
    lâu hơn để kiểm tra khoảng 11/06 → cuối tháng 8.
  - Không có frontend nào TỪNG tồn tại gọi route này (git history round 2) — nên "ngừng hoạt động"
    không mô tả đúng bản chất; sát hơn là: **có giai đoạn phát triển/test thủ công ngắn (19/05 →
    11/06/2026), sau đó bị bỏ dở khi hướng redesign khác (Notion "S0" định nghĩa lại, rồi ACPv1 bị
    xoá hẳn AA-477) — không phải một sự cố khiến nó "ngừng chạy" ở 1 thời điểm cụ thể.**

**Ngày gần nhất có bằng chứng cụ thể nhất để dùng làm mốc, nếu cần 1 con số**: 11/06/2026 (AA-174,
lần cuối có tương tác con người thật với code này).
