# Nếu duyệt chạy lại toàn bộ ~900 tour S1 bằng Sonnet: tác động toàn platform

Bản tư vấn cho Nghiệp · S248 · 23/10/2026 · Tác nhân: Claude Code
Nguồn: 4 báo cáo đọc code (A3/atom, T-series tenant, TripPlanner + places, Booking + bề mặt publish), bản phản biện (critic) đã kiểm lại trong code, và bản tư vấn AA-645 (`decision-memo.md`, số chất lượng/chi phí writer). Chỉ đọc code + schema dump 23/10; không chạy DB, không gọi API trả tiền.

---

## 1. Tóm tắt (5 dòng)

1. **Nên đi, nhưng chưa đi được ngay.** Writer v2 **chưa được nối vào pipeline thật** (`s1_writer_v2.py:1-6`), và judge brand-fit hiện tại có thể loại trang viết trung tính. Chạy bây giờ là trả tiền mà nhiều tour vẫn giữ text cũ, và không ai thấy (tour đang live mà fail gate thì bị `dismissed` im lặng, không vào hàng duyệt).
2. **Tiền không phải vấn đề:** một lần chạy sạch toàn catalogue khoảng **$85** (khoảng $70–160), trong đó S1 Sonnet ~$72. Atomize lại chỉ ~$7–15, không phải ~$30–45 như memo AA-645 ghi.
3. **Thời gian và độ lệch mới là vấn đề:** atomize chạy từng tour một, nên đuôi atomize mất **~30–45 giờ**. Trong khoảng đó bảng job bận, cấm merge/deploy backend và cấm DB Migrate `apply`, còn text Master, atom, place và pin TripPlanner lệch nhau.
4. **Không có đường rollback sạch hôm nay:** nút "promote" chỉ chép tên + subtitle, còn export lại bản cũ thì không atomize lại (dedupe key đã dùng). Phải snapshot `published_tours` và sửa promote trước.
5. **Điều kiện đi:** A/B run 2 xác nhận writer → đo brand-fit offline (~$0,26) → nối v2 sau cờ (chỉ A1) + đổi judge → làm xong các migration/PR đang chờ → chạy wave 3 → ≤50 → từng nước. Chạy toàn catalogue cần anh duyệt riêng sau wave ≤50.

---

## 2. Chuỗi tác động

Chú thích: **[auto]** tự chạy · **[job]** job tự xếp hàng · **[tay]** admin phải bấm/chạy · **ID** = ID có đổi không · **$** = chi phí cho ~892 tour · **⏱** = thời gian

```
S1 rewrite (writer v2, Sonnet 5.5)                       [job s1_rewrite, 6 song song]
│   ID: generated_content.id MỚI mỗi tour (version_num+1); quality_scores.id mới
│   $: ~$72 ($61–105) toàn chuỗi A1   ⏱: ~6–9 giờ (ước từ S218, chưa đo Sonnet ở 6 song song)
│   Fail gate + tour đã live → review_status='dismissed' (IM LẶNG), giữ Master cũ
│
▼ qua gate → process_export()                            [auto]
Master: gold_aa_internal.published_tours (upsert theo tour_id)
│   ID: published_tours.id GIỮ; tour_id, source_id GIỮ
│   ĐỔI: toàn bộ text + seo_title/seo_meta; published_at = NOW(); slug ĐỔI ~96% (slug theo aa_name)
│   catalog.v_tour: content_hash + updated_at đổi cho ~900 tour cùng lúc
│   $: 0   ⏱: tức thì
│
├──► A3 atomize                                          [job a3_atomize, 1 tour/lần toàn hệ thống]
│     tour_atoms: đọc lại MỌI ngày (fingerprint theo version id mới)
│     ID: atom_id = hash(tour|ngày|place|action) → đổi chữ là ID MỚI, atom cũ soft-delete
│         (đo proxy: chỉ ~54% tên riêng giữ nguyên chữ với W×Sonnet; Haiku chạy lại cũng chỉ 65%)
│     Segment: GIỮ phần lớn (upsert, alias); chữ mới có thể sinh Segment mới
│     Route: đổi nội dung → bản :vN mới, bản cũ superseded (KHÔNG "ổn định")
│     $: ~$7–15 (tệ nhất ~$50 nếu toàn bộ rơi về Haiku)   ⏱: ~30–45 giờ
│     │
│     ├──► recompute (landing → score → route)            [job, debounce 180 s, trần 20 phút]
│     │     atom_matches, atom_embedding, atom_ranking, route   $: <$1 embed + Jev phần lớn có cache
│     │
│     ├──► place_extract → geo.tour_place, component     [CHỈ auto nếu PLACE_PIPELINE_AUTO bật — Dev đang TẮT → tay]
│     │     ID: component_id = uuid5(nguồn, ngày, tên place, nước, hoạt động) → phần lớn ĐỔI
│     │     $: ~$1–3 cho ~120 tour đã build   ⏱: 8–15 giờ (chỉ chạy được khi job S1/atomize/recompute rảnh)
│     │
│     ├──► place cards (atom_place_card)                 [tay: admin place_cards_build hoặc T8 khi cần]
│     │     card_id theo place → GIỮ; link tới atom mới phải tạo lại (phần lớn miễn phí)
│     │     $: <$1 (thẻ mới $0,0022/thẻ)
│     │
│     └──► DataForSEO segment research                   [tay, chỉ admin từ AA-646]   $: 0 tự động
│
├──► T-series tenant
│     T2 tenant_tour_versions: KHÔNG tự viết lại, giữ mô tả Master cũ; tenant tự bấm rewrite (tính quota)
│     T7 slate/subject: subject trỏ segment/route (GIỮ); seed atom chọn lại live; slate tự làm mới sau 24 giờ
│     T8/T9: request đang dở (~21 dòng) có atom bị soft-delete → AtomNotFoundError / ContentWritingError
│     Bài đã đăng WordPress/Facebook: KHÔNG đổi (chỉ có create)
│     $: 0 tự động; gián tiếp: debate cache miss + T2 rewrite tenant chọn (chưa định giá)
│
├──► TripPlanner                                         [auto, đọc live]
│     Text, narration, day guard: đổi ngay
│     Tour detail places (v_tour_place, đọc atom live): đổi ngay
│     Pin, route, search, graph (geo.tour_place): CŨ cho tới khi place_extract chạy
│     Bản nháp chuyến đi của khách: pin có component_id biến mất → bị BỎ im lặng
│     Slug đổi → 308 sang slug mới (link cũ vẫn chạy); sắp xếp browse theo published_at bị xáo
│
└──► Booking                                             [không ghép text/version]
      trip_plans, B2B products, inquiry legs theo (source_system, source_id) → KHÔNG ảnh hưởng
      Proposal đã tạo: giữ tiêu đề ngày cũ (theo thiết kế)
      Số ngày tour đổi → trip_plan_components.day_no có thể nằm sai ngày
      Feed B2B updated_since KHÔNG nhúc nhích; partner phải đồng bộ theo content_hash (~900 thay đổi)
```

---

## 3. Chi phí một lần và thời gian chạy

### 3.1 Chi phí

| Hạng mục | Chi phí ~892 tour | Ghi chú |
|---|---:|---|
| S1 toàn chuỗi A1, W×Sonnet | **~$72** ($61–105) | Theo memo AA-645. Kịch bản cao ($105) xảy ra nếu judge brand-fit chấm trang trung tính < 7 → retry tăng |
| A3 atomize (LLM, route `a3_atomize` = gpt-6-luna) | ~$5–7 | ~9.800 lần gọi (1/ngày). Tệ nhất (toàn bộ rơi về Haiku) ~$41 |
| Jev `a3_atom_in_text` | ~$0,5–0,7 | Cache đều miss vì key chứa `md5(day_text)` |
| Jev cấp Segment (demand, type, landing, match…) | ~$1–3 (trần ~$7,4) | Cache 180 ngày; chỉ hỏi lại moment mới. $1–3 là ước tính |
| Embedding atom mới | < $1 | |
| **Cộng A3** | **~$7–15** (tệ nhất ~$50) | **Đính chính memo AA-645:** con số "+$30–45" dùng giá Haiku, cao hơn thực tế |
| Place re-extract (~120 tour đã build) | ~$1–3 | Toàn catalogue $9–21 là việc AA-712/AA-905 riêng, chạy SAU rerun |
| Place cards (link lại + thẻ mới) | < $1 | Giá đo: $0,0022/thẻ (AA-772). AA-784 (~$15–25) là việc riêng |
| DataForSEO | **$0 tự động** | S1 dùng lại `seo_context` ≤ 180 ngày; segment research chỉ chạy tay. Con số ~$16,6/wave trong memo là của A3 search demand chạy tay |
| T-series gián tiếp | chưa định giá | Slate đề xuất lại + debate cache miss; T2 rewrite do tenant chọn (tính vào quota tenant) |
| **Tổng một lần chạy sạch** | **~$85** (khoảng $70–160) | |
| Shadow trước khi publish (nếu shadow cả catalogue) | + ~$72 | Shadow không publish nên không kéo theo A3. Đề xuất: shadow chỉ trên pilot + ≤50 (~$4), không shadow cả catalogue |
| Việc đo trước (run 2 + brand-fit offline) | ~$2–3 + $0,26 | Panel chấm bằng agent Claude: $0 |

So sánh nếu chọn W×Luna: S1 ~$11 thay vì $72, phần còn lại như nhau → tổng ~$25. Phần A3/places/T-series **không phụ thuộc writer**.

### 3.2 Thời gian

| Khâu | Thời gian | Ghi chú |
|---|---|---|
| S1 (6 song song, worker 8 slot) | ~6–9 giờ | Ước từ Sri Lanka S218 (123 tour / 73,6 phút ở 4 song song). Run 1: 122 lần gọi Sonnet trong ~7,5 phút, 0 lỗi. **Quota acc3 ở 6 song song chưa kiểm** |
| Đuôi atomize (1 tour/lần) | **~30–45 giờ** | 20–30 job ≈ 1 giờ. Recompute chen vào ít nhất 20 phút/lần, ~5 phút mỗi lần |
| Place re-extract + geocode + graph | ~8–15 giờ | Chỉ chạy được khi job S1/atomize/recompute rảnh. Theo lô ≤50 |
| **Tổng cả catalogue** | **~2–3 ngày bảng job bận** | Trong đó: không merge/deploy backend CIS (deploy guard fail-closed), không DB Migrate `apply` cho MỌI app (DM-11.4) |

---

## 4. Rủi ro theo mức và cách giảm

### Cao

| # | Rủi ro | Cách giảm |
|---|---|---|
| C1 | **Writer v2 chưa nối vào pipeline.** Judge brand-fit (điểm ≥ 7) có thể chấm thấp trang trung tính. Tour live fail thì bị `dismissed` im lặng, giữ text v1, mà vẫn tốn tiền. Writer đã là Sonnet nên không còn đường "nâng Haiku→Sonnet" cứu tour fail | Chạy đo brand-fit offline (~$0,26) trước. Nối v2 sau cờ, mặc định tắt. Đổi judge theo memo §3: brand-fit chỉ báo cáo, bỏ `s1_itinerary_nudge`, thu hẹp `s1_flag_fix`, bật enforce mã day-oracle. Mỗi wave báo cáo số tour "ở lại v1" theo nước |
| C2 | **Không có rollback sạch.** Nút promote chỉ chép `aa_name`, subtitle, điểm → trang lẫn nội dung, không atomize lại. Export lại bản cũ thì không atomize lại vì dedupe key `a3_atomize:<version_id>` đã dùng vĩnh viễn | Snapshot `published_tours` trước mỗi wave (RDS snapshot hoặc copy bảng qua DB Migrate `run-script`). Sửa promote để gọi `process_export` rồi atomize lại với `dedupe=False` |
| C3 | **Freeze ~2 ngày chặn việc khác.** Migration chờ: AA-932 (`rl-003`/`rl-004`, CIS mig 269), Booking bk-020 (AA-973), bk-021 (AA-974). PR đang mở: CIS #945, #946, Booking #64. Kiểm live AA-982, AA-983 đang chờ | Làm xong và merge tất cả trước wave. Chạy backfill AA-983 trước wave (hoặc chạy lại sau). Chia wave theo nước để có cửa sổ deploy/migrate xen giữa |
| C4 | **Text Master và atom/place lệch nhau hàng giờ tới ngày.** Seed T8/T9 vẫn trích chữ cũ. Trên ~120 tour đã build place, tour detail (atom mới) và pin/route/search (component cũ) không khớp, mà cờ `is_stale` vẫn false | Giữ `PLACE_PIPELINE_AUTO` tắt. Sau mỗi wave: chờ `shared.job` rảnh → backfill place `only_stale=true` (chạy `dry_run` trước) → geocode/graph → `place_cards_build`. Không để lệch quá 1 wave |
| C5 | **Request T8/T9 đang dở bị hỏng** (~21 dòng `angle_gate_request`): atom bị soft-delete → `AtomNotFoundError` / `ContentWritingError` | Trước wave: liệt kê request ở `pending_goal`/`pending_choice`/`approved`, cho xong hoặc tạm dừng. Hoặc trỏ lại sang atom thay thế (cùng tour, ngày, place) |
| C6 | **Số ngày đổi → atom "mồ côi" vẫn live.** Soft-delete chỉ chạy trên các ngày được đọc lại. Ví dụ s1-001: live 4 ngày, v2 còn 1 ngày → atom ngày 2–4 vẫn live, vẫn hiện ở tour detail TripPlanner, slate, seed T8. Run 1: 1/25 tour (4%) | Đếm số tour đổi số ngày trên cả catalogue trước wave. Sửa nhỏ trong code: soft-delete atom ở ngày > số ngày mới. Kiểm số ngày Booking `trip_plan_components.day_no` cho các tour này |
| C7 | **Bản nháp chuyến đi của khách mất pin im lặng.** Component ID đổi → pin bị bỏ lần fold event tới, không báo lỗi (Dev: ~98 bản nháp) | Snapshot `geo.tour_place` trước re-extract. Sau đó map cũ → mới theo (nguồn, ngày, destination_id) rồi theo tên, thêm vào `component_id_map` qua master run-script (như AA-847) |
| C8 | **Tour cưỡi voi** (chính sách chị Thư 08/10: giữ nguyên, người duyệt, không bao giờ viết lại) | Loại khỏi `expected_set` ngay từ đầu. Báo cáo đếm riêng là "chờ người duyệt (cưỡi voi)", không tính là fail |

### Trung bình

| # | Rủi ro | Cách giảm |
|---|---|---|
| T1 | **Slug đổi ~96%** (slug theo `aa_name`; ngay cả A+ chạy lại cũng chỉ giữ tên 4/25). 308 redirect giữ link cũ, nhưng ~900 URL đổi cùng lúc → Google crawl và xếp hạng lại; lịch sử lượt xem theo URL bị gãy | Hoặc chấp nhận (redirect đã có), hoặc thêm cờ writer giữ nguyên `aa_name` cũ → slug không đổi. Ghi lại ngày cutover để so trước/sau (chưa kiểm TripPlanner có bật Analytics không) |
| T2 | **`published_at` reset về NOW()** → thứ tự "Browse pool" của tenant và trang browse công khai của TripPlanner bị xáo theo thứ tự chạy, tour cũ trông như mới | Sửa upsert giữ `published_at` đầu tiên, hoặc thêm `first_published_at` để sắp xếp |
| T3 | **Bản T2 của tenant mô tả Master cũ**, không có dấu "nguồn đã cập nhật". Màn so sánh QA admin ghép bản T2 cũ với Master mới → so sai | Thêm dấu "nguồn đã cập nhật" (so `ttv.created_at` với `pt.published_at`). Lưu `generated_content_id` trên bản T2 mới; ghi nhãn bản cũ "viết từ Master trước". Câu hỏi re-rewrite miễn phí: xem mục 7 |
| T4 | **Thao tác dọn atom của admin bị hoàn tác.** Chữ mới sinh lại đúng atom admin đã xoá (cùng ID) → upsert đặt `deleted=false`. Kết quả Jev học từ lần xoá không mang sang | Trước wave: xuất `decision_log` có `source='admin_atom_delete'`; sau atomize: áp lại các lần xoá theo (tour, ngày, place, action) |
| T5 | **Atomize fail 2 lần** (`max_attempts=2`) → tour có Master mới nhưng atom cũ/thiếu, không ai xếp hàng lại (dedupe key đã dùng) | Báo cáo mỗi wave đếm "đã publish, chưa atomize"; chạy lại qua đường admin với `dedupe=False` |
| T6 | **Lặp góc viết (angle).** Lịch sử chống lặp angle của T8 theo `atom_id` → atom ID mới mất lịch sử, T8 có thể gợi ý góc tenant đã đăng | Đổi khoá lịch sử sang segment, hoặc map atom cũ → mới qua `atom_segment_member` |
| T7 | **Hai "giọng văn" trong catalogue** (v2 cho tour qua, v1 cho tour fail) | Đếm "ở lại v1" theo nước mỗi wave; xử lý riêng nhóm này sau |
| T8 | **T2 dùng chung `graph.py`.** Nếu cờ v2 không giới hạn ở A1, tenant rewrite mất khối khác biệt brand mà v2 bỏ đi | Cờ chỉ áp cho A1; thêm kiểm hồi quy T2 |
| T9 | **Bộ golden trôi.** Sau rerun, text live không còn là "A+ hôm nay" của `fixture-1.1.0.json`, không tái tạo được từ DB | Đóng băng fixture + snapshot nguồn trước rerun; gate hồi quy đọc từ fixture, không đọc `published_tours`. Xong adjudication n = 50 Sonnet vs Luna TRƯỚC rerun |
| T10 | **Quota Sonnet acc3** ở 6 song song nhiều giờ chưa kiểm | Kiểm `service-quotas` (1 dòng) trước wave |
| T11 | **Partner/catalog consumer** nhận ~900 thay đổi `content_hash` cùng lúc; AA-976 ("CIS catalog over HTTP") đang làm trên catalogue đang chuyển động | Báo trước; ghi thời điểm vào AA-976 |
| T12 | **Paid place pass chạy trước rerun = trả 2 lần** (AA-712/AA-905, AA-784) | Ghi "blocked by S1 rerun" vào các dòng backlog (`docs/backlog/README.md:96,102,116`) |
| T13 | **Brand-fit debate cache cũ** cho segment giữ ID (điểm tính trên chữ cũ) | Tăng `brand_version` hoặc xoá `debate_brand_fit_cache` sau wave (528 dòng, tính lại rẻ) |

### Thấp

| # | Rủi ro | Cách giảm |
|---|---|---|
| L1 | Đường legacy của atomize (khi itinerary không có `Day N —`) chèn ID ngẫu nhiên, không xoá atom cũ → atom gấp đôi. Run 1: 25/25 trang v2 giữ đúng header | Kiểm trong pilot; sửa nhỏ: đường legacy soft-delete atom cũ của tour |
| L2 | DB phình thêm ~100–200 MB (`atom_embedding` không bao giờ xoá; ước tính, chưa đếm dòng). DB hiện 985 MB | Theo dõi; dọn sau nếu cần |
| L3 | Đổi model `a3_atomize` giữa wave → mọi fingerprint đổi, tính tiền lại toàn bộ | Khoá route `a3_atomize` tới hết wave |
| L4 | Sentry/alert ồn: `AtomNotFoundError`, `ContentWritingError`, `export_failed`, `review_queue_enqueue_failed` (chưa kiểm `logger.error` có lên Sentry không) | Quyết định mute hoặc gắn tag trước wave |
| L5 | Quarter plan (6 plan) giữ `atom_ids` cũ; atom mới `usage_log` rỗng nên trông như "chưa dùng" | Chấp nhận; plan mới đọc atom live nên đúng |
| L6 | Destination mới từ cách viết tên mới → geocode + dedupe tự động | Merge hoàn tác được; kiểm số destination mới mỗi wave |
| L7 | Trang `/trip/{tour_id}` đổi nội dung tại chỗ | ~0 dòng, URL ổn định, không canonical/robots → không rủi ro SEO |
| L8 | Booking | Không ghép text/version; chỉ lưu ý `day_no` khi số ngày đổi (C6) |

**Bỏ một đề xuất cũ:** "embed lại `content_embedding`" — không router/service nào trong CIS, TripPlanner, Booking đọc cột này (chỉ lộ qua view `acp_contract.v_trip_registry`). Ghi nhận cột này là cột chết, không cần làm.

---

## 5. Tenant và chị Thư thấy gì, cần báo trước gì

**Tenant sẽ thấy:**
- Mô tả tour Master trong pool mới hơn, sát nguồn hơn; thứ tự pool có thể xáo (nếu chưa sửa `published_at`).
- Gợi ý chủ đề (slate) đổi nhẹ trong vài ngày sau.
- Request T8/T9 đang dở có thể báo lỗi nếu không xử lý trước (C5).

**Tenant sẽ KHÔNG thấy đổi:**
- Tour họ đã rewrite (T2) và nội dung đã xuất.
- Bài đã đăng trên WordPress/Facebook (publish chỉ có create, không có update).
- Không có QA, gate, cờ nào lộ ra phía tenant (luật "tenant chỉ thấy nội dung").

**Lời báo tenant (đơn giản, về sản phẩm):** mô tả tour Master đang được làm mới bằng cách viết sát nguồn hơn; tour đã rewrite và bài đã đăng giữ nguyên; muốn lấy bản Master mới thì rewrite lại tour (miễn phí hay không: chờ quyết định ở mục 7); gợi ý chủ đề có thể đổi nhẹ vài ngày.

**Cho chị Thư (qua Jira draft cuối phiên, anh duyệt rồi mới đăng; link báo cáo wave đi kèm Jira, không gửi lẻ Zalo):**
- Đây là làm mới toàn bộ catalogue Master; không nội dung nào tenant đã đăng bị đụng.
- Không có rủi ro pháp lý mới: kênh tenant không bị đổi nội dung, text Master trung tính, white-label; code không có điều khoản công bố AI theo tenant, nên không cần đổi gì.
- Một việc kinh doanh cần chị chọn (đề xuất nhẹ nhàng, không ép): có cho tenant rewrite lại miễn phí một lần mỗi tour không.
- Tour cưỡi voi vẫn theo chính sách của chị: giữ nguyên, người duyệt.
- Trên Dev: 4 tenant, 53 bản T2, 317 content piece bị ảnh hưởng ở mức "bản T2 mô tả Master cũ".
- URL công khai của tour trên TripPlanner sẽ đổi (link cũ tự chuyển hướng).

---

## 6. Kế hoạch chạy đề xuất

### Bước 0: điều kiện trước (chưa tốn tiền đáng kể)
1. **A/B run 2** (golden 25:50, ~$2–3) + **đo brand-fit offline** (~$0,26) + adjudication n = 50 Sonnet vs Luna. Chốt writer.
2. **Đóng băng** `fixture-1.1.0.json` + snapshot nguồn.
3. **PR CIS nối v2 sau cờ, chỉ A1, mặc định tắt** + đổi judge (memo §3) + kiểm hồi quy T2. Kèm các sửa nhỏ, đề xuất làm luôn:
   - soft-delete atom ở ngày > số ngày mới;
   - đường legacy soft-delete atom cũ;
   - giữ `published_at` đầu tiên (hoặc `first_published_at`);
   - promote gọi `process_export` + atomize `dedupe=False`;
   - (tuỳ quyết định) cờ giữ `aa_name` cũ.
   PR này đụng pipeline/gate → cho agent review độc lập trước khi merge.
4. **Dọn đường:** land AA-932, bk-020, bk-021; merge/đóng CIS #945, #946, Booking #64; xong AA-982, AA-983 (kể cả backfill AA-983); ghi "blocked by S1 rerun" cho AA-712/905/784; ghi thời điểm vào AA-976.
5. **Chuẩn bị dữ liệu:**
   - xử lý ~21 request T8/T9 đang dở;
   - xuất `decision_log` `admin_atom_delete`;
   - loại tour cưỡi voi khỏi `expected_set`;
   - đếm tour đổi số ngày;
   - kiểm quota Sonnet acc3;
   - quyết mute/tag Sentry.

### Bước 1: shadow (không publish, không kéo A3)
- Bật cờ ở chế độ shadow/review trên pilot 3 tour rồi ≤50 tour (~$4).
- Đo: tỉ lệ judge cho qua, số lần thử/run, gate code sau flag_fix, Jev trên trang mới, chi phí thật/tour so với mô hình.

### Bước 2: wave thật theo `aa-wave-rerun` (dừng báo cáo, chờ duyệt giữa các wave)
- **Snapshot** `published_tours` + `geo.tour_place` trước MỖI wave.
- **Pilot 3 tour**, ưu tiên tour Lào đã build place, để đo độ đổi component ID.
- **≤ 50 tour.**
- **Phần còn lại theo từng nước** (~50–240 tour/wave), có cửa sổ deploy/migrate xen giữa. Chạy toàn catalogue **cần anh duyệt riêng** sau wave ≤50 (luật paid-runs-subset).
- **Trong wave:** không merge/deploy backend; khoá route `a3_atomize`; `PLACE_PIPELINE_AUTO` tắt.
- **Sau mỗi wave**, khi `shared.job` rảnh:
  1. segment research dry-run (có `max_places` + budget);
  2. place backfill `only_stale=true` (`dry_run` trước) → geocode/graph;
  3. map component cũ → mới vào `component_id_map`;
  4. `place_cards_build` theo tour;
  5. áp lại các lần xoá atom của admin;
  6. xoá/bump brand-fit cache.

**Kiểm mỗi tour trong pilot và báo cáo mỗi wave:**
- Parse ngày chuẩn thành công (không đi đường legacy).
- Số atom live trước/sau; số atom ở ngày vượt số ngày mới (phải = 0).
- Tỉ lệ atom giữ ID / ID mới; số Segment mới sinh / Segment nhập vào.
- Số component mất/thêm; số bản nháp khách bị rớt pin; số tour đổi số ngày.
- Số tour "ở lại v1" (`dismissed` của wave này); số tour cưỡi voi; số "đã publish, chưa atomize".
- Gate code mỗi trang, tỉ lệ judge < 7, chi phí/tour từ `shared.llm_call_log`.
- Số trang có "Adventure Asia" / "Design This Journey" khi nguồn không có.

### Điều kiện dừng (đề xuất, anh chốt con số)
Dừng wave và báo anh nếu một trong các điều sau xảy ra:
- tỉ lệ "ở lại v1" > 10% của wave;
- có tour đi đường legacy;
- có atom live ở ngày vượt số ngày mới;
- chi phí thật/tour > 1,5 lần mô hình (> ~$0,12 với Sonnet);
- có lỗi throttle Bedrock acc3;
- có tour atomize fail mà không chạy lại được;
- tỉ lệ lỗi nghiêm trọng trong mẫu kiểm wave ≤50 không còn vượt A+.

### Rollback
- **Toàn wave:** khôi phục `published_tours` từ snapshot của wave, rồi atomize lại các tour đó với `dedupe=False`. Atom ID là hash nội dung, nên atomize từ text cũ sẽ sinh lại đúng ID cũ và upsert bỏ cờ deleted. Sau đó backfill place + map component.
- **Từng tour:** chỉ dùng được sau khi đã sửa promote (bước 0.3). Promote bản cũ → `process_export` → atomize `dedupe=False`.
- **Không hoàn tác được:** bản T2 tenant tạo trong lúc wave, bài tenant đã đăng, bản nháp khách đã rớt pin (trừ khi đã map `component_id_map`), slug đã bị Google ghi nhận (redirect vẫn chạy).

---

## 7. Câu hỏi cần anh quyết (kèm đề xuất)

| # | Câu hỏi | Đề xuất |
|---|---|---|
| Q1 | Writer: Sonnet hay Luna? | Chờ run 2 (n = 50). Nếu vẫn hòa: Sonnet (theo memo AA-645, vì là nền dữ liệu). Phần A3/places/T-series như nhau với cả hai; chênh chỉ ~$60 ở S1 |
| Q2 | Shadow cả catalogue (~+$72) hay chỉ pilot + ≤50? | Chỉ pilot + ≤50 (~$4); đủ để đo tỉ lệ judge cho qua và chi phí |
| Q3 | Duyệt chạy toàn catalogue bây giờ hay sau wave ≤50? | Sau wave ≤50, bằng một lần duyệt riêng có số liệu thật |
| Q4 | Slug: giữ `aa_name` cũ (slug ổn định) hay chấp nhận ~96% slug đổi? | Chấp nhận đổi: redirect 308 đã có, tên mới sát nguồn hơn. Nếu anh coi trọng SEO hơn thì thêm cờ giữ tên |
| Q5 | `published_at`: sửa để giữ ngày publish đầu, hay chấp nhận pool/browse bị xáo? | Sửa (nhỏ, cùng PR bước 0.3) |
| Q6 | Cho tenant rewrite lại miễn phí một lần mỗi tour? | Đề xuất có, dưới dạng gợi ý cho chị Thư quyết (việc kinh doanh). Cần một đường admin không tính quota |
| Q7 | Làm các sửa nhỏ atomize (ngày vượt số ngày mới, đường legacy) trước wave? | Có; rẻ và chặn được rủi ro C6/L1 |
| Q8 | `PLACE_PIPELINE_AUTO`: bật hay giữ tắt? | Giữ tắt trong wave; chạy backfill tay sau mỗi wave. Có thể bật sau khi xong toàn bộ |
| Q9 | AA-712/AA-905/AA-784 (paid place pass): dời sau rerun? | Có, để không trả tiền hai lần |
| Q10 | Cửa sổ freeze ~2–3 ngày: chọn khi nào? | Ngay sau khi land AA-932, bk-020, bk-021 và đóng các PR đang mở; chia theo nước để có cửa sổ deploy giữa wave |
| Q11 | Sentry: mute hay tag lỗi dự kiến trong wave? | Gắn tag theo wave, không mute (để vẫn thấy lỗi lạ) |
| Q12 | Ngưỡng dừng ở mục 6 (10% ở lại v1, 1,5 lần chi phí…) | Dùng như đề xuất cho wave 3 và ≤50, chỉnh lại theo số thật trước wave lớn |

---

Đính chính so với các phần trước:
- **Chi phí atomize:** ~$7–15, không phải $30–45.
- **Route ID:** có bản `:vN` mới khi nội dung đổi, không "ổn định".
- **Tour fail gate:** tour đang live bị `dismissed` im lặng, không vào hàng duyệt.
- **Giá thẻ place:** dùng giá đo $0,0022/thẻ.
- **`content_embedding`:** bỏ đề xuất embed lại vì không ai đọc cột này.

File liên quan: `/home/nghiep/projects/AA-Ecosys/.tmp-session/S248/aa645ab/decision-memo.md`, `/home/nghiep/projects/AA-Ecosys/.tmp-session/S248/aa645ab/llmcost.txt`, `/home/nghiep/projects/AA-Ecosys/.tmp-session/S248/aa645ab/run/pages.json`, `/home/nghiep/projects/AA-Ecosys/.tmp-session/S248/aa645ab/fixture-1.1.0.json`.

## 8. Kết quả đo judge brand-fit offline (S248, 23/10, $0,25, 351 lượt gọi)

Judge thật của A1 (`s1_judge` = gpt-5.6-luna, chế độ prod AA-714: trung vị 3 lần khi gần ngưỡng), gate `brand_fit < 7` → retry,
chấm 125 trang của A/B run 1 (25 tour golden × 5 arm).

| Arm | brand_fit TB | % sẽ retry (< 7) | So với A+ Haiku (cặp theo tour) | Lỗi nghiêm trọng / trang (panel) |
|---|---|---|---|---|
| A+ × Haiku (hiện tại) | 7,56 | 16% | — | 2,38 |
| W × Sonnet | 6,72 | **36%** | −0,84 (thấp hơn 13, cao hơn 3, hoà 9; p = 0,02) | **0,18** |
| W × Luna | 6,72 | 32% | −0,84 (p = 0,0005) | 0,24 |
| E × Sonnet | 7,16 | 8% | −0,40 (p = 0,06) | 0,24 |
| E × Luna | 6,68 | 36% | −0,88 (p = 0,01) | 0,38 |

Đọc: judge brand-fit **không thưởng cho việc đúng nguồn** (Spearman theo trang giữa brand_fit và tỉ lệ lỗi nghiêm trọng = 0,08,
gần 0). Trang W ít bịa hơn ~13 lần nhưng bị chấm thấp hơn ~0,8 điểm, và 32–36% trang sẽ bị retry (gấp đôi hiện tại).
Phản hồi của judge chê "generic" ở 56–60% trang W (A+: 40%).

Hệ quả: rủi ro C1 là **thật**, không còn là giả định. Nếu nối writer v2 mà giữ gate brand-fit như cũ thì (a) chi phí lên kịch
bản cao (~$105), (b) retry đẩy writer quay lại thêm "màu brand" — đúng thứ sinh ra claim bịa, (c) tour live fail sẽ `dismissed`.
Điều kiện trước bước 1 (§6) vì thế bắt buộc: brand-fit chỉ báo cáo (không chặn) cho A1 v2, hoặc viết lại rubric brand-fit để
chấm giọng văn trong giới hạn nguồn rồi đo lại trên 125 trang này (~$0,25) trước khi bật lại gate.

## 9. Quyết định của Nghiệp (S248, 23/10, trang quyết định d01–d14)

| # | Quyết định | Ghi chú của Nghiệp → việc phải làm |
|---|---|---|
| d01 | Writer **W×Sonnet** | — |
| d02 | Brand-fit **chỉ báo cáo** cho A1 v2 | Hỏi "sao không dùng rubric, cách nào tốt hơn" → giải thích ở S248; rubric mới vẫn làm, đo lại trên 125 trang trước khi bật lại làm gate |
| d03 | Shadow chỉ pilot + ≤ 50 tour | — |
| d04 | Toàn catalogue: sau wave ≤ 50, duyệt riêng | — |
| d05 | Chấp nhận slug đổi (redirect 308) | — |
| d06 | **Giữ ngày publish đầu** cho tour cũ (đổi theo chat S248) | Tour mới nhận ngày publish thật; tour cũ viết lại giữ `published_at` gốc, lần viết lại ghi ở `updated_at` → PR nhỏ cùng bước 0 |
| d07 | **Không** đưa "rewrite miễn phí" cho chị Thư | Chưa có tenant thật; tìm cách cải thiện hệ thống (ví dụ tự làm mới nội dung tenant) thay vì hỏi chị Thư |
| d08 | Sửa nhỏ atomize trước wave | — |
| d09 | `PLACE_PIPELINE_AUTO` tắt trong wave | Cần nói rõ mức tác động và cách đúng |
| d10 | Dời place trả phí sau rerun | Đánh giá bản viết lại có tốt hơn hẳn không rồi mới chạy place |
| d11 | Freeze ngay khi các PR đang mở đã land | — |
| d12 | Sentry gắn tag theo wave | — |
| d13 | Ngưỡng dừng như đề xuất | **Mỗi wave phân tích chất lượng có cải thiện rõ không** (so trước/sau theo nước) |
| d14 | Xoá 8 bảng TP cũ ngay (AA-712 tp-018) | Phân tích thận trọng xem place từ tour viết mới có tốt hơn |
