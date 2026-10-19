# AA-543 — Điều tra thật để thiết kế Segment/Score/Route/Hub platform-wide

Investigate-only, không code, không migration. Mọi kết luận dưới đây bám theo nguyên tắc phân
tầng đã chốt ở ADR-0003 (không diễn giải lại): **"bước này có đọc brand voice/DFS riêng của
tenant không" — không phải "bảng này có cột tenant_id không".**

Nền tảng đã có sẵn từ AA-539/540/541/542 (`CONTEXT.md`, `docs/adr/0001-*.md`, `0002-*.md`,
`0003-*.md`) — báo cáo này KHÔNG lặp lại phần đã chốt, mà đào sâu thêm theo đúng yêu cầu AA-543:
bằng chứng file:line cho từng điểm chạm tenant_id, xác nhận lại 2 rào cản AA-526, mở rộng ranh
giới Slate (Phần 4 — yêu cầu riêng của Nghiệp), và số liệu production thật (Phần 5).

---

## Phần 1 — Segment

### 1.1 Mọi điểm chạm `tenant_id` trong `segment_matching.py`, đọc brand voice/DFS hay không

File: `services/acp_contract/segment_matching.py`.

| # | Dòng | Việc gì | Đọc brand voice/DFS của tenant? | Bằng chứng |
|---|------|---------|----------------------------------|------------|
| 1 | `_mint()` :160-169 | Băm `segment_id = sha256(tenant_id\|place\|verb)` | **Không.** `tenant_id` chỉ là input băm để tránh 2 tenant cùng tạo ra 1 PK trùng (`atom_segment` PK là `segment_id`) — không đọc bất kỳ dữ liệu brand/DFS nào. | Docstring module dòng 17-22 tự nói rõ: lý do DUY NHẤT tenant_id có trong hash là tránh va chạm PK, không phải vì thuật toán cần biết brand. |
| 2 | `run_segment_matching()` đọc `tour_atoms` :394-412 | Lọc atom theo `ta.owner_scope = $1 OR (ta.owner_scope='platform' AND ta.tour_id IN (SELECT ... ttv.tenant_id = $1))` | **Không.** Chỉ lọc THEO TOUR mà tenant đã pick (qua `tenant_tour_versions`), không đọc `tenant_brand_rules`/`tenant_seo_config`/`seo_context` ở bước này. | Chính câu SQL — không JOIN bất kỳ bảng brand/DFS nào. |
| 3 | `run_segment_matching()` đọc `atom_segment_member`/`atom_segment` :413-418 | Lấy segment đã gán trước đó của tenant, để `reconcile_ids()` giữ id ổn định | **Không.** Thuần đọc lại chính output cũ của module này. | Cùng file. |
| 4 | Ghi `atom_segment`/`atom_segment_member`/`atom_segment_alias` :430-483 | Ghi kết quả | **Không.** | Cùng file. |

**Bản thân thuật toán nhóm** (`derive_segments`/`_key`/`_looks_like_one_moment`/`_connected`,
dòng 104-369) là hàm thuần (`from __future__ import annotations`, không I/O — xác nhận lại đúng
như module docstring dòng 2 tự khai: "pure function, không I/O") — không nhận `tenant_id` làm
tham số so sánh nào ngoài việc truyền qua cho `_mint()`. **Kết luận Phần 1.1: không một điểm chạm
`tenant_id` nào trong toàn bộ file đọc brand voice hay DFS riêng tenant.** Khớp 100% với
`docs/adr/0003-*.md`.

### 1.2 Đối chiếu `aa-social-media` — xác nhận đúng file (không lặp lỗi AA-525 vòng 4)

- `docs/AI-gent-for automation works/aa-soscial-media-main/src/aa_social/segments.py` (350 dòng)
  — **đây là file đúng** để đối chiếu Segment: docstring dòng 1-13 tự mô tả "Grouping Atoms that
  describe one real-world moment... Deterministic and free: token similarity on `place`, verb
  match on `action`, no embeddings and no network." Không có khái niệm tenant/brand nào trong
  toàn bộ file (source repo là 1 SQLite file/1 brand, không multi-tenant).
- `docs/AI-gent-for automation works/aa-soscial-media-main/src/aa_social/matching.py` (305 dòng)
  — **file KHÁC, không phải Segment.** Docstring dòng 1-16 tự mô tả: "Landing harvested queries
  on the Atoms they belong to... Per ADR 0002 this is the one job embeddings do" — đây là bước
  landing truy vấn tìm-kiếm (embedding) lên Atom, một cơ chế hoàn toàn khác, không liên quan gì
  đến việc nhóm Segment. AA-CIS-App's `segment_matching.py` docstring dòng 11-12 tự trích dẫn
  đúng `docs/adr/0002-vector-store-scoped-to-search-matching.md` — đúng ADR 0002 gốc của
  `matching.py`, không nhầm.
- Xác nhận: `segment_matching.py` là port gần-verbatim của `segments.py` (thuật toán Jaccard
  place + verb-match hành động), KHÔNG liên quan `matching.py`. Không phát hiện nhầm lẫn nào
  trong code hiện tại (báo cáo AA-525 vòng 4 lỗi này đã bị bắt trước khi AA-509 build, không lặp
  lại ở đây).

### 1.3 Xác nhận lại 2 rào cản kỹ thuật AA-526 (còn đúng không, có rào cản khác không)

Đọc trực tiếp schema + code hiện tại (không suy đoán từ ADR):

1. **`atom_segment.tenant_id UUID NOT NULL`** — `api/migrations/129_atom_segment...sql:49`:
   ```
   tenant_id        UUID NOT NULL REFERENCES shared.tenants(tenant_id),
   ```
   **Còn đúng.** `'platform'` (chuỗi, dùng cho `tour_atoms.owner_scope`) không phải UUID hợp lệ
   — insert sẽ lỗi cast/NOT NULL ngay. Đây là rào cản thật, chưa sửa.

2. **`atom_ranking.py` đọc Segment theo tenant cố định** — `services/acp_contract/
   atom_ranking.py:243`:
   ```python
   WHERE asg.tenant_id = $1::uuid AND NOT ta.deleted AND NOT ta.is_empty_marker
   ```
   **Còn đúng.** Một Segment platform-scope sẽ vô hình với truy vấn này (không có `tenant_id`
   thật để so `$1`). Đây là rào cản thật thứ 2, chưa sửa.

**Rào cản khác tìm thấy thêm (chưa từng ghi nhận trước đây):**

3. **`route_detection.py` cũng đọc theo tenant cố định** — `run_route_detection()`,
   `services/acp_contract/route_detection.py:268`: `WHERE ar.tenant_id = $1::uuid AND
   ar.excluded_reason IS NULL`, và `route_id` là composite `f"{tenant_id}:{tour_id}:
   {first}-{last}"` (dòng 105) — nếu Segment/Score platform-wide hóa mà Route không đổi cùng lúc,
   Route vẫn tạo ra 1 bản/tenant dù input (Segment/Score) đã dùng chung. Đây LÀ rào cản thứ 3,
   không phải rào cản mới phát sinh từ AA-532 (AA-532 chỉ đổi delete+insert → versioning, không
   đổi identity/scope — xem 3.2 dưới), mà là hệ quả tất yếu nếu chỉ sửa Segment/Score mà bỏ sót
   Route trong cùng 1 lần redesign. Ghi nhận rõ để thiết kế mới không lặp lại kiểu sửa-nửa-vời
   của AA-526.
4. **`slate.py` (`_fetch_segment_candidates`/`_fetch_route_candidates`/`_fetch_segment_hub_map`)
   cũng lọc `WHERE ... tenant_id = $1::uuid`** ở cả 3 hàm (dòng 153, 195, 228) — cùng lý do,
   Slate hiện đọc Score/Route/Hub theo tenant, sẽ cần đổi song song nếu 3 tầng dưới đổi platform-
   wide (xem Phần 4 — Slate/Subject tự nó ĐÚNG là per-tenant, nhưng cách nó ĐỌC tầng dưới cần
   đổi cùng lúc).

Không tìm thấy rào cản thứ 5 nào khác ngoài 4 điểm trên (đã rà toàn bộ `WHERE ... tenant_id`
trong `segment_matching.py`, `atom_ranking.py`, `route_detection.py`, `slate.py`).

**Kết luận Phần 1**: Segment — **per-tenant nhưng là nợ kỹ thuật (cần sửa)**, khớp `docs/adr/
0001-*.md`/`0003-*.md`. Không có bằng chứng mới nào đảo ngược kết luận đó; bằng chứng mới ở đây
chỉ mở rộng danh sách rào cản kỹ thuật từ 2 lên 4 (thêm Route/Hub, Slate-read) — quan trọng cho
scope của issue thiết kế lại sắp tới.

---

## Phần 2 — Score (Atom Ranking, AA-515)

### 2.1 Mọi điểm chạm `tenant_id`, đọc brand voice/DFS hay không

File: `services/acp_contract/atom_ranking.py`.

| # | Dòng | Việc gì | Đọc brand voice/DFS tenant? | Bằng chứng |
|---|------|---------|------------------------------|------------|
| 1 | `run_atom_ranking()` đọc `atom_segment`/`atom_segment_member`/`tour_atoms` :236-245 | Lấy Segment của tenant + text để tính `said` | **Không.** `WHERE asg.tenant_id = $1::uuid` — chỉ lọc phạm vi, không đọc brand/DFS. | Dòng 243. |
| 2 | Đọc `search_demand` :247-250 | Lấy TOÀN BỘ bảng, không lọc tenant | **Không — và đây chính là bằng chứng Score không cần brand/DFS riêng tenant**: `search_demand` (migration 130) không có cột `tenant_id`, câu SQL dòng 247-250 không có `WHERE` theo tenant nào — đọc y hệt cho mọi tenant. | Dòng 247-250: `SELECT keyword, market, search_volume, people_also_ask FROM acp_contract.search_demand WHERE search_volume IS NOT NULL` — không có tenant filter. |
| 3 | Ghi `atom_ranking` (DELETE+INSERT) :286-312 | Ghi kết quả | **Không.** | Cùng file. |

**Bản thân thuật toán rank-sum** (`rank_segments`/`compute_demand`/`compute_questions`/
`classify_exclusion`, dòng 101-218) là hàm thuần, không nhận brand/DFS-tenant nào làm input —
chỉ nhận `Candidate` (từ Segment) + `demand_rows` (từ `search_demand`, đã xác nhận platform-wide
ở #2). **Kết luận 2.1: giống Segment, không một điểm chạm nào đọc brand voice/DFS riêng tenant.**

### 2.2 `atom_ranking.py` là điểm chặn chính (AA-541) — sửa thế nào để bỏ phụ thuộc tenant mà
không phá ranking hiện có

Đọc kỹ để trả lời đúng yêu cầu STEP0 của AA-543 (chỉ điều tra, không code — nêu hướng, không
thiết kế chi tiết):

- **Điểm neo (anchor) hiện tại** để "recompute toàn bộ Segment của 1 tenant" là tham số
  `tenant_id` truyền vào `run_atom_ranking(tenant_id, markets, pool)` (dòng 223) — nếu bỏ tenant
  làm đơn vị tính, đơn vị mới phải là **toàn bộ Master Content pool** (mọi Segment platform-wide
  cùng lúc), giống cách `run_segment_matching()` sẽ phải đổi.
- **`markets` list hiện đến từ tenant** (dòng 231-233 tự khai: "the tenant's resolved market-code
  list (`resolve_buyer_markets()`, via the caller's already-loaded `target_market`") — đây LÀ một
  input thật-sự-per-tenant (`shared.tenant_seo_config.target_market`, theo AA-533/534's finding).
  Đây là điểm cần thiết kế cẩn thận: nếu Score platform-wide hóa nhưng `markets` vẫn khác nhau
  giữa các tenant (vì mỗi tenant target thị trường khác nhau), thì Score-cho-1-Segment sẽ CÓ
  NHIỀU giá trị khác nhau tùy theo tenant nào đang xem — tức là **Score không thể trở thành 1 con
  số duy nhất per Segment mà vẫn giữ nguyên ngữ nghĩa "rank theo thị trường tenant target"**, trừ
  khi: (a) tính Score cho MỖI market có thể có (không phải mỗi tenant) rồi tenant chỉ chọn market
  của mình khi đọc — market là hữu hạn và platform-wide (không phải 1-1 với tenant), khác hẳn
  brand voice; hoặc (b) chấp nhận Score platform-wide chỉ tính trên 1 market mặc định, tenant
  target market khác phải tự suy ra. Đây LÀ quyết định thiết kế thật sự cần Nghiệp/Claude Chat
  chốt, không phải rào cản kỹ thuật đơn thuần như NOT NULL — ghi nhận là câu hỏi mở cho issue
  thiết kế tiếp theo, KHÔNG tự quyết ở đây (đúng yêu cầu "không suy đoán nghe hợp lý").
- **`atom_ranking` PK hiện tại** `PRIMARY KEY (tenant_id, tour_id, segment_id)` (migration
  130:76) — nếu bỏ `tenant_id` khỏi PK, PK còn lại `(tour_id, segment_id)` vẫn hợp lệ về mặt
  logic (1 Segment platform-wide đã cố định `tour_ids` của nó rồi) — không phát sinh rào cản kỹ
  thuật mới ngoài việc phải migrate PK + mọi FK/index phụ thuộc (`idx_atom_ranking_tenant_tour`,
  `idx_atom_ranking_tenant_score`, migration 130:79-81).
- **Kết luận 2.2**: rào cản kỹ thuật thuần (PK, FK) không lớn hơn Phần 1 đã nêu; nhưng có 1 câu
  hỏi thiết kế thật (xử lý `markets` per-tenant) cần quyết trước khi build, khác hẳn dạng NOT
  NULL constraint đơn giản.

**Kết luận Phần 2**: Score — **per-tenant nhưng là nợ kỹ thuật (cần sửa)**, cùng nhóm với
Segment/Route/Hub theo `docs/adr/0003-*.md`. Phát hiện mới: việc platform-wide hóa Score có 1
câu hỏi thiết kế thật về xử lý `markets`, chưa được `docs/adr/0003-*.md` nêu tên cụ thể.

---

## Phần 3 — Route/Hub (AA-510, AA-532)

### 3.1 Mọi điểm chạm `tenant_id`, đọc brand voice/DFS hay không

File: `services/acp_contract/route_detection.py`.

| # | Dòng | Việc gì | Đọc brand voice/DFS tenant? | Bằng chứng |
|---|------|---------|------------------------------|------------|
| 1 | `derive_routes()`/`route_id` composite :83-114 | `route_id = f"{tenant_id}:{tour_id}:{first}-{last}"` | **Không.** `tenant_id` chỉ để đảm bảo định danh không va chạm giữa 2 tenant cùng chọn 1 tour — không đọc brand/DFS. | Dòng 105. |
| 2 | `run_route_detection()` đọc `atom_ranking`/`hub`/`route` hiện tại :258-289 | 3 câu SQL đều `WHERE ... tenant_id = $1::uuid` | **Không.** Chỉ đọc lại Score (đã xác nhận Phần 2 không brand/DFS) và Route/Hub cũ của chính tenant. | Dòng 268, 278, 288. |
| 3 | `create_route_pick()` :480-486 | Snapshot 1 Route thành `route_pick` | **Không.** Đọc `acp_contract.route`/`atom_segment`/`tour_atoms`, không đọc brand/DFS. | Dòng 480-503. |

**Thuật toán `families()`/`_runs()`/`_spans()`/`journey_name()`** (dòng 117-228) hoàn toàn thuần,
không nhận tenant/brand/DFS làm tín hiệu gì — chỉ nhận `tour_ids`/`Segment` sets. **Kết luận 3.1:
giống Segment/Score, không điểm chạm nào đọc brand voice/DFS riêng tenant.**

### 3.2 AA-532 (route_detection.py versioning fix) — ảnh hưởng gì đến thiết kế platform-wide

Đọc trực tiếp `run_route_detection()` docstring (dòng 233-252) + code (dòng 377-446):

- **AA-532 đổi CÁCH GHI** (DELETE+INSERT-toàn-bộ → supersede+insert-version, giữ định danh
  `(tenant_id, tour_id, first_day, last_day)` làm identity ổn định) — **không đổi PHẠM VI SCOPE**
  (vẫn `WHERE ar.tenant_id = $1::uuid`, dòng 268). Đây là điểm quan trọng cần làm rõ cho thiết kế
  mới: **AA-532 KHÔNG phải rào cản với việc platform-wide hóa, và cũng không tự động giải quyết
  nó** — 2 việc độc lập nhau.
- **Ảnh hưởng thật sự đến thiết kế platform-wide**: cơ chế versioning (supersede-never-delete,
  `route_id` gốc + hậu tố `:vN`) là 1 pattern tốt để TÁI SỬ DỤNG khi Route platform-wide hóa —
  vì lý do y hệt AA-532 tự nêu (dòng 234-239): `acp_shared.subject.route_id` (nay `route_pick`)
  có FK thật, NO ACTION on delete, vào `route.route_id`. Nếu Route platform-wide hóa mà quay lại
  kiểu DELETE+INSERT-toàn-bộ (bỏ pattern AA-532 vừa sửa), FK-violation y hệt AA-532's bug sẽ tái
  diễn — chỉ khác là giờ ảnh hưởng MỌI tenant cùng lúc (vì Route dùng chung), thay vì 1 tenant
  một lúc như trước. **Khuyến nghị (không phải quyết định — issue thiết kế sau tự cân nhắc)**:
  bất kỳ redesign Route platform-wide nào PHẢI giữ pattern versioning AA-532 đã có, không được
  quay lại pattern cũ.
- **`acp_contract.hub` không có versioning** (docstring dòng 251-252 tự xác nhận: "still never
  rebuilt the same way (unaffected by this change)") — Hub hiện tại reuse-hoặc-tạo-mới, không
  bao giờ xóa. Platform-wide hóa Hub sẽ đơn giản hơn Route (không có bug FK tương tự để lo, vì
  Hub chưa từng bị xóa-rồi-tạo-lại).

### 3.3 Dữ liệu Hub thực tế

Production hiện có **0 hàng `acp_contract.hub`** (xem Phần 5) — nghĩa là chưa có tour nào thực
sự tạo thành 1 "gia đình" đủ điều kiện (`SHARED_ENOUGH = 0.3`, `route_detection.py:49`). Không
đánh giá được hành vi Hub thật với dữ liệu thật ngoài code-read — ghi rõ, không suy đoán thêm.

**Kết luận Phần 3**: Route/Hub — **per-tenant nhưng là nợ kỹ thuật (cần sửa)**, cùng nhóm
Segment/Score. AA-532 là 1 fix độc lập, đúng đắn, và nên được GIỮ LẠI nguyên vẹn trong thiết kế
platform-wide tiếp theo (không phải rào cản, mà là tiền đề tốt).

---

## Phần 4 — Ranh giới Slate (T7) — mở rộng theo yêu cầu Nghiệp

### 4.1 Slate có đọc brand voice/DFS trực tiếp không?

File: `services/acp_shared/slate.py`, toàn bộ 4 hàm DB-facing
(`_fetch_segment_candidates`/`_fetch_route_candidates`/`_fetch_segment_hub_map`/`propose_slate`/
`fetch_slate`/`pick_subject`) đọc CHÍNH XÁC các bảng sau, không hơn:
`acp_contract.atom_ranking`, `acp_contract.atom_segment`, `acp_contract.atom_segment_member`,
`acp_contract.route`, `acp_contract.tour_atoms`, `acp_shared.subject`,
`acp_shared.angle_gate_request` (ghi, không đọc brand). **Không có JOIN/SELECT nào vào
`shared.tenant_brand_rules` hay `silver_aa_internal.seo_context` hay `acp_contract.search_demand`
trực tiếp trong toàn bộ file này** (rà từng hàm, xác nhận bằng grep nội bộ — 0 kết quả).

Điều này khác với mô tả trong đề bài AA-543 ("Slate là nơi tenant brand voice/DFS THẬT SỰ được
đọc") — **cần đính chính, có bằng chứng file:line**: Slate tự nó **KHÔNG đọc brand voice/DFS
trực tiếp** — nó chỉ đọc Score (`atom_ranking`, đã xác nhận Phần 2 không brand/DFS) và Route
(Phần 3, cũng không). Brand voice/DFS được đọc **một bước SAU Slate**, ở T8 (Angle Gate), không
phải tại Slate:

- **Brand voice**: `services/acp_angle_gate/brand_audience.py::fetch_brand_audience()`
  (dòng 27-40) — `SELECT customer_segment, customer_mindset FROM shared.tenant_brand_rules WHERE
  tenant_id = $1 AND is_active = true` — gọi từ `set_goal_and_generate()`,
  `services/acp_angle_gate/service.py:116`, tức LÀ SAU khi `pick_subject()` (Slate) đã chạy xong
  và tạo `angle_gate_request`.
- **DFS/search-demand (dạng khác search_demand)**: cùng hàm `set_goal_and_generate()`, dòng
  135-137: `fetch_search_demand_signal(req["trip_id"], pool)` — đọc `silver_aa_internal.
  seo_context` (xem 4.2 dưới), cũng SAU Slate.

**Kết luận 4.1 — trả lời trực tiếp câu hỏi AA-543 đặt ra**: Slate **ĐÚNG LÀ ranh giới
platform-wide → per-tenant về mặt SCOPE (dữ liệu nó đọc — Score/Route — đã xác nhận không cần
brand/DFS)**, nhưng Slate **KHÔNG PHẢI nơi brand voice/DFS thật sự được đọc** — đó là T8, một
bước SAU Slate. Không phát hiện rò rỉ tenant-dependency nào TRƯỚC Slate ngoài Segment/Score/
Route/Hub đã biết (đã rà toàn bộ 3 file Phần 1-3, không có brand/DFS ở đâu trong chuỗi Atom→
Segment→Score→Route→Slate). Đây là 1 đính chính quan trọng so với khung của issue, không phải
phủ nhận nguyên tắc phân tầng — ngược lại, nó CHỨNG MINH nguyên tắc phân tầng đúng: ranh giới
thật là "trước T8" chứ không phải "trước Slate" cụ thể — Slate nằm gọn trong vùng platform-wide-
đúng-ra-nên-là, cùng Segment/Score/Route/Hub.

### 4.2 `seo_context` — platform-wide hay per-tenant, có ảnh hưởng thiết kế mới không

**Phát hiện quan trọng: có HAI bảng "search demand" khác nhau, không phải một — đề bài AA-543 tự
thân dễ nhầm 2 khái niệm này với nhau, giống cách AA-525 vòng 4 từng nhầm `segments.py`/
`matching.py`:**

1. **`acp_contract.search_demand`** (migration 130) — bảng dùng bởi Score (`atom_ranking.py`),
   **KHÔNG có cột `tenant_id`** — platform-wide cache thật, đã xác nhận ở `docs/adr/
   0002-*.md`/AA-540. Đây LÀ bảng Score dùng, không phải `seo_context`.
2. **`silver_aa_internal.seo_context`** — bảng CŨ, thuộc pipeline S1-rewrite admin (không liên
   quan Score/Slate qua đường Segment) — **CÓ cột `tenant_id` (TEXT, `DEFAULT 'aa_internal'`,
   thêm ở migration `004_tenant_rls.sql:7-8`)**, có RLS policy (`004_tenant_rls.sql:54-56`:
   `USING (tenant_id = current_setting('app.tenant_id', true))`). Về mặt SCHEMA, bảng này trông
   như "per-tenant, RLS-enforced" — nhưng thực tế vận hành khác hẳn:
   - `grep -rn "app.tenant_id\|set_config\|SET LOCAL"` trên toàn bộ `api/`+`services/` trả về
     **0 kết quả** — không có bất kỳ dòng code Python nào từng gọi `SET app.tenant_id` hay
     `set_config`. Nghĩa là GUC `app.tenant_id` không bao giờ được set trong runtime thật.
   - `api/main.py:63-64` tạo pool bằng 1 `DATABASE_URL` duy nhất (không phân theo tenant), và
     `007b_create_app_user.sql:2-7` tự ghi rõ: role `aa_cis_admin` (SUPERUSER/BYPASSRLS) là role
     mà ứng dụng thật sự chạy production, `aa_app_user` (RLS-enforced) là role RIÊNG được tạo
     cho mục đích khác — không xác nhận được app runtime có dùng `aa_app_user` hay không từ code
     đọc được (không đọc được giá trị `DATABASE_URL` thật/task-def env trong phạm vi điều tra
     này), nhưng nếu app dùng `aa_cis_admin` như comment tự khai, RLS trên `seo_context` **không
     có hiệu lực thật** ở runtime — mọi truy vấn đọc được MỌI hàng bất kể tenant nào.
   - Bằng chứng thực nghiệm xác nhận RLS không chặn: `fetch_search_demand_signal(tour_id, pool)`
     (`services/acp_shared/dfs_relevance.py:146-155`) — câu SQL `_SEO_CONTEXT_SINGLE_TOUR_QUERY`
     (dòng 89-95) **không có tham số tenant nào, chỉ lọc `WHERE tour_id = $1`** — và tính năng
     này đã live-verify chạy thật ở AA-501 (migration 127, xem `docs/implementation-notes/
     AA-501.md`) — tức là nó ĐÃ đọc được dữ liệu thật trong production. Nếu RLS thật sự chặn
     theo `app.tenant_id` (không set = NULL = không khớp bất kỳ hàng nào), tính năng đó phải LUÔN
     trả `None` — thực tế nó hoạt động, nên RLS không phải cơ chế đang chặn.
   - **Dữ liệu thật xác nhận luôn** (Phần 5, truy vấn trực tiếp RDS dev):
     `seo_context_distinct_tenant_id = 1`, giá trị DUY NHẤT trong 55 hàng là
     `00000000-0000-0000-0000-000000000001` (sentinel `aa_internal` — cùng sentinel Master
     Content pool dùng, xem `CONTEXT.md` dòng 208). **Không một hàng `seo_context` nào trong
     production hiện tại thuộc về 1 tenant thật** — toàn bộ 55 hàng là DFS admin chạy ở A1/S1,
     không phải DFS tenant tự chạy khi rewrite.

**Kết luận 4.2**: `seo_context`, dù schema/RLS nói là per-tenant, **trong thực tế vận hành và dữ
liệu thật, hành xử y hệt Master Content pool (platform-wide, đọc chung bởi mọi tenant qua
`tour_id`, không lọc tenant)** — không phải 1 tín hiệu per-tenant thật như tên RLS-policy gợi ý.
Đây LÀ 1 phát hiện mới, khác với những gì `CONTEXT.md`'s cross-tenant table (AA-540) đã liệt kê
(bảng đó chỉ nêu 3 cơ chế cross-tenant: Master Content/Atom pool, Search Demand
(`acp_contract.search_demand`), Facts Entry platform-scope — chưa từng xét `seo_context` là 1
biến thể thứ 4 của cùng hiện tượng). **Ảnh hưởng đến thiết kế mới**: `seo_context` không phải
rào cản hay tín hiệu cần platform-wide hóa (nó ĐÃ platform-wide trong thực tế, dù schema không
nói vậy) — nhưng RLS "trên giấy" không khớp thực tế vận hành là 1 khoảng cách tài liệu/schema
đáng lưu ý riêng (không thuộc phạm vi sửa của issue thiết kế Segment/Score/Route/Hub — ghi nhận
để cân nhắc dọn dẹp/làm rõ ở 1 issue khác, không tự sửa ở đây theo đúng yêu cầu KHÔNG CODE).

**Kết luận Phần 4**: Slate **đúng thiết kế per-tenant** (nó là nơi Bar/Channel/State — quyết định
mang tính tenant thật, dù bản thân Slate không trực tiếp đọc brand/DFS) và **đúng là ranh giới
platform-wide→per-tenant về mặt kiến trúc dữ liệu nó tiêu thụ** — không có rò rỉ tenant-dependency
nào trước nó ngoài chính Segment/Score/Route/Hub. `seo_context` không phải một điểm rò rỉ mới —
nó là 1 biến thể (âm thầm, do RLS không hoạt động) của cùng cơ chế Master-Content-pool đã biết.

---

## Phần 5 — Dữ liệu production hiện tại

Truy vấn trực tiếp RDS dev (`aa-cis-dev-db`, secret `aa-cis/dev/rds`) qua S3-mediated ECS exec
pattern, 06/09/2026, container `aa-cis-dev-api` task đang chạy (desired=1/running=1, RDS
`available`).

| Bảng | Tổng hàng | Số tenant khác nhau | Ghi chú |
|------|-----------|----------------------|---------|
| `shared.tenants` | 4 total, 4 active | — | |
| `gold_aa_internal.published_tours` | 74 | — (platform-wide, 1 sentinel) | |
| `gold_aa_internal.tenant_tour_versions` | 15 | — | 0 tour nào được ≥2 tenant cùng pick (`shared_tours_multi_tenant = 0`) |
| `acp_contract.tour_atoms` (chưa xóa) | 377 | — | 302 `owner_scope='platform'` (post-AA-526), **75 vẫn `owner_scope=`tenant cũ (legacy, pre-AA-526, chưa dọn — khớp đúng số 75 đã ghi nhận ở AA-526's implementation notes, chưa thay đổi)** |
| `acp_contract.atom_segment` | 23 | **1** | Chỉ 1 tenant từng chạy Segment matching thật |
| `acp_contract.atom_ranking` | 23 | **1** | Cùng 1 tenant trên |
| `acp_contract.route` (current, chưa superseded) | 2 | **2** | Xem chi tiết dưới |
| `acp_contract.hub` | **0** | 0 | Chưa có Hub nào tồn tại trong production |
| `acp_shared.subject` | 49 | **1** | 39 `proposed` + 10 `picked`, 0 `used`/`cut` |
| `acp_contract.route_pick` | **0** | — | Chưa có ai thật sự "chốt" 1 Route |
| `acp_contract.search_demand` | 480 | — (không có cột tenant_id) | |
| `silver_aa_internal.seo_context` | 55 | **1** (toàn bộ = sentinel `aa_internal`) | Xem Phần 4.2 |

### Số lượng bản ghi TRÙNG LẶP thật giữa các tenant (do per-tenant hóa)

- **Segment**: `segment_duplicate_groups_count = 0` — vì chỉ có 1 tenant từng chạy Segment
  matching (`atom_segment_distinct_tenants = 1`), nên KHÔNG có trùng lặp thật nào tồn tại trong
  dữ liệu hiện tại (điều kiện tiên quyết — 2 tenant cùng chọn 1 tour — chưa từng xảy ra thật).
- **Score**: tương tự, 0 (`atom_ranking_distinct_segment_tenant_pairs_shared_segment = 0`).
- **Route**: **có đúng 1 nhóm trùng thật** — `tour_id=4bf83a2c-cec0-4127-ac82-1a26fbbd48a3`,
  `first_day=1, last_day=5`, `n_tenants=2`. Đây khớp với ghi chú trong
  [[project_aa527_bosung_aa532_route_versioning]] (memory phiên trước): AA-527's live-verify đã
  chủ động tạo dữ liệu SOUTHERN LAOS cho 2 tenant trên cùng 1 tour để xác nhận "cross-tenant Route
  đúng thiết kế" — **đây là dữ liệu do live-verify tạo ra, không phải usage thật của khách hàng.**
  Không có nhóm trùng lặp thứ 2 nào khác.
- **Subject**: không tính được trùng lặp (chỉ 1 tenant có Subject).

### Kết luận Phần 5 — quy mô thật cho việc gộp lại platform-wide

**Quy mô dọn dữ liệu khi gộp platform-wide, TÍNH ĐẾN HIỆN TẠI, gần như bằng KHÔNG**: chỉ 1 tenant
thật (+1 bộ dữ liệu test do live-verify AA-527 tạo) từng đi qua Segment/Score/Route/Slate — chưa
có tình huống 2 tenant thật cùng rewrite 1 tour nào xảy ra tự nhiên để tạo ra bản ghi Segment/
Score trùng lặp thật cần gộp. Rủi ro dữ liệu trùng lặp là **rủi ro tương lai** (khi có ≥2 tenant
thật cùng chọn 1 tour trong 74 published tour hiện có), không phải gánh nặng dọn dẹp đã tồn tại —
khác với lo ngại "cần ước lượng độ phức tạp dọn dữ liệu" trong đề bài AA-543, thực tế là: **việc
này rẻ hơn dự kiến, đây là thời điểm TỐT để redesign** (trước khi dữ liệu tích lũy thêm), không
phải lý do trì hoãn. Việc cần dọn dẹp thật sự đã biết từ trước (75 atom/23 segment/2 route/49
subject cũ dưới tenant legacy — pre-AA-526) là câu hỏi độc lập, đã ghi nhận ở
[[project_aa522_526_527_chain_shipped]] mục "2 quyết định còn treo" — số liệu ở đây (`75` atom
legacy) khớp chính xác, xác nhận vẫn CHƯA được xử lý tính đến hôm nay, liên quan trực tiếp
AA-495 (RESET) như đề bài đã liên hệ.

---

## Tổng kết theo yêu cầu bắt buộc #3 (mỗi bước — 1 trong 3 nhãn)

| Bước | Nhãn |
|------|------|
| Atom (A3) | Platform-wide đúng thiết kế |
| Search Demand (`acp_contract.search_demand`) | Platform-wide đúng thiết kế |
| `seo_context` (thực tế vận hành, dù schema nói khác) | Platform-wide trên thực tế (không cần sửa để đạt mục tiêu này — nhưng RLS "trên giấy" sai lệch với thực tế, đáng 1 issue riêng, ngoài phạm vi ở đây) |
| **Segment** | **Per-tenant nhưng là nợ kỹ thuật (cần sửa)** |
| **Score (Atom Ranking)** | **Per-tenant nhưng là nợ kỹ thuật (cần sửa)** — thêm câu hỏi thiết kế thật về `markets` (2.2), chưa có trong ADR-0003 |
| **Route** | **Per-tenant nhưng là nợ kỹ thuật (cần sửa)** — giữ nguyên pattern versioning AA-532 khi redesign |
| **Hub** | **Per-tenant nhưng là nợ kỹ thuật (cần sửa)** — 0 dữ liệu thật để kiểm chứng hành vi |
| Slate / Subject | Per-tenant đúng thiết kế (ranh giới xác nhận đúng — không đọc brand/DFS trực tiếp, nhưng là nơi quyết định mang tính tenant: Channel/Bar/State) |
| Goal/Angle/Write/Gate/Piece/Publish (T8+) | Per-tenant đúng thiết kế (đọc brand voice thật — `brand_audience.py`, và DFS/PAA thật — `seo_context` qua `dfs_relevance.py`, dù nguồn dữ liệu DFS đó hóa ra platform-wide trên thực tế) |

## Việc KHÔNG làm trong investigation này (đúng phạm vi AA-543)

Không sửa code, không tạo migration nào. Không tự quyết câu hỏi mở về `markets` per-market-vs-
per-tenant (2.2). Không sửa khoảng cách RLS/`seo_context` (4.2). Không dọn 75 atom/23 segment/2
route/49 subject legacy (Phần 5) — để dành cho issue thiết kế/build tiếp theo, đúng như AA-542's
Decision đã chốt phạm vi.
