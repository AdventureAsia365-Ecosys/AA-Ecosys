# S214 — AA-734 atom_ranking no-dip (ADR 0003 nấc 2) + wave Laos 45/46 (06/10/2026)

**Tác nhân:** Kiro (VSCode/WSL) · **ECS cuối phiên:** `aa-cis-dev-api:458` + `aa-cis-dev-worker:13` (đều COMPLETED) · **Migration mới:** 204 (atom_ranking versioning) · **Image api==worker:** rollout COMPLETED sau #572

## Trạng thái
Giao được 2 việc chính đầu phiên: AA-734 Done trọn (no-dip verify live), wave Laos 45/46 master (1 tour để AA-724). Nghiệp chốt: gom nhiều mẫu rồi mới sửa AA-724 (không làm với 1 mẫu).

## Đối chiếu list việc đầu phiên S214
| Việc | Kết quả |
|---|---|
| 1. AA-734 atom_ranking no-dip (ADR 0003 nấc 2) | ✅ Done (2 PR #571 + #572 hotfix, verify live) |
| 2. Wave Laos 46 (AA-653) | ✅ 45/46 master, 1 rớt (AA-724/641) |
| 3. AA-725 deploy guard | ❌ chưa → phiên sau |
| 4. AA-733 skill restructure | ❌ chưa → phiên sau (skill-draft/ còn untracked ở root) |

## AA-734 — atom_ranking versioned-swap (Done)
**Phương án 1 (Nghiệp chốt):** mỗi bảng no-dip bằng pointer riêng, KHÔNG gộp ranking+route 1 transaction khổng lồ (tránh giữ lock 1-5 phút). Khác mô tả gốc issue (option B "one transaction") — đổi hướng có chủ ý, Nghiệp duyệt trong chat.

- **Migration 204:** `atom_ranking` thêm `version INT NN DEFAULT 1` + `superseded_at TIMESTAMPTZ NULL`; PK đổi `(market,tour_id,segment_id)` → `(market,tour_id,segment_id,version)`; partial unique index `idx_atom_ranking_current_identity (market,tour_id,segment_id) WHERE superseded_at IS NULL`; 2 partial index thay 2 index cũ. 32508 dòng cũ backfill version=1/current.
- **Writer (`run_atom_ranking`):** DELETE+INSERT → versioned-swap. **Thứ tự QUAN TRỌNG: supersede hàng cũ TRƯỚC, INSERT hàng mới SAU** (cùng 1 transaction). Hotfix #572 sửa đúng điểm này — PR gốc #571 insert trước → vi phạm partial unique index (UniqueViolationError live). Sau swap commit, DELETE hàng superseded (fresh acquire, ngoài txn, không dip). atom_ranking KHÔNG giữ history (khác route — route giữ vì subject.route_id FK).
- **Readers** (tất cả lọc `superseded_at IS NULL`): admin_overview (count headline), slate.py ×2, v1_route_hub, admin_dashboard (overview counts + score/segment/route/hub panels), admin_atoms, route_detection (ranked-pair read — chạy sau ranking swap nên đọc bộ fresh).

**Verify LIVE:** migration 204 applied Dev; deploy COMPLETED (api:458/worker:13); enqueue platform recompute → **succeeded** (attempt 1, ~5 phút); 85 mẫu/170s: `current_count` = 32508 ở MỌI mẫu (0 dip; trước đây DELETE+INSERT rớt ~5418/market); version bump 1→2; superseded cleanup 0 còn lại; mỗi market 5418 current. `/admin/overview` score_count=32508.

## Wave Laos (AA-653) — 45/46 master
| cột | số |
|---|---|
| raw active (source_status=active) | 46 (3 superseded loại) |
| S1 rewrite succeeded (lượt đầu) | 43 |
| master active | **45** |
| atomized | 45 |
| còn review | 1 |

- **Flow:** seo-prefetch 1 job (43 tour active, succeeded, ~8.5 phút) → 43 s1_rewrite (concurrency 4) → 38 thẳng master, 5 rớt review → regenerate.
- **Regenerate (cơ chế FE — batch_id random mỗi lần, tối đa 3 vòng):**
  - V1: LUXURIOUS LAOS + MUDDY SPOKES → master (2/5)
  - V2: Laos-Vietnam Explorer + Luang Prabang - Vang Vieng → master (2/5)
  - V3: Wellbeing and Yoga VẪN rớt (điểm 3→6→3→5, không chạm 7.0)
- **1 tour chịu (Wellbeing and Yoga):** FORBIDDEN_WORD + SEO_META_TOO_LONG lặp cả 4 lần = đúng lớp lỗi AA-724 (hype/forbidden word) + AA-641 (seo_meta). Để review cho AA-724/641. Nghiệp chốt: gom nhiều mẫu rồi sửa AA-724 (1 mẫu quá ít).
- **Laos total raw = 49** = 46 active + 3 superseded. 3 superseded (dup CLASSIC/SOUTHERN/LUXURIOUS LAOS) đúng ra bị loại — 2 cancelled, 1 failed tự nhiên, không tạo content.

## Bằng chứng verify
- AA-734: xem phần trên (85 mẫu no-dip, job succeeded, version 2).
- Laos: 45 published/master active, 45 atomized, 1 pending review (Wellbeing and Yoga).

## Còn lại (chuyển phiên sau)
1. **AA-724** (gom mẫu rồi sửa — Nghiệp chốt): writer emit FORBIDDEN_WORD/hype tone, regenerate không cứu. Thu thập thêm tour cycle/bike/yoga hype-tone từ các nước sau làm ca mẫu A/B. Hiện có: Wellbeing and Yoga (Laos) + 2 tour Thailand pending (S212).
2. **AA-641** SEO_META_TOO_LONG deterministic fit (In Progress) — liên quan tour trên.
3. **Wave các nước tiếp theo** (AA-653): Nepal(86) → Sri Lanka(126) → India(236). Japan(80)/Philippines(46)/Pakistan(18) chưa gán thứ tự. **NHỚ lọc `source_status='active'` khi lấy danh sách** (bài học phiên này — gửi nhầm 3 tour superseded).
4. **AA-725** (High) deploy guard shared.job + post-deploy smoke.
5. **AA-733** (High) skill restructure — skill-draft/ còn untracked ở root.
6. AA-726, AA-714 (In Review), AA-732, AA-729.

## Lưu ý kỹ thuật / BÀI HỌC
- **atom_ranking versioned-swap: supersede TRƯỚC insert SAU** — partial unique index `WHERE superseded_at IS NULL` đòi hỏi 1 current row/identity tại mọi thời điểm. Insert-trước vi phạm (lỗi #571→#572). MVCC vẫn giữ no-dip: reader connection khác thấy snapshot pre-commit tới khi commit.
- **Lấy danh sách tour cho wave PHẢI lọc `source_status='active'`** — raw có versioning (`superseded`), tour superseded là bản cũ bị thay, không nên chạy. Query lọc `pipeline_status='ingested'` + chưa publish là CHƯA đủ. Bài học: gửi nhầm 3 superseded → prefetch skip (query prefetch tự lọc `source_status='active'`, hiện `done 40/43`), rewrite fail/cancelled.
- **Regenerate đúng cơ chế FE = batch_id RANDOM mỗi lần** (`crypto.randomUUID()` trong reviewApi.ts::startRegenerate). Idem key s1_rewrite = `s1_rewrite:{tour}:{tier}:{batch}` KHÔNG có retry_count → dùng lại batch cũ bị dedup (reuse job succeeded cũ, không regenerate thật). Phải đổi batch_id.
- **"job succeeded" ≠ "lên master"** — 43 job succeeded nhưng 38 master, 5 rớt review. Luôn tách: job ok / master / review-pending / atomized.
- **FORBIDDEN_WORD + SEO_META_TOO_LONG = lỗi deterministic regenerate KHÔNG cứu** (điểm dao động quanh ngưỡng, không hội tụ). Khác low_quality sát ngưỡng (cứu được bằng regenerate, như 4/5 tour phiên này).
- ECS exec runner `.tmp-session/s209_run.sh <py> <s3key>`; lệnh dài chạy nền/poll S3; STS 8h hết → Nghiệp refresh MFA. `_SingleConn` wrapper cho script enqueue cần cả `fetch/fetchval/execute` (queue.list_jobs gọi pool.fetch thẳng).
- Log local: file này. Memory Notion: prepend S215.
