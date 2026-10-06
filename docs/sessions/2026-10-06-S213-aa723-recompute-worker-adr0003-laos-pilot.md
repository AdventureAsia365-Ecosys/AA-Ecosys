# S213 — AA-723 bg-tasks → worker, ADR 0003 job model, pilot Laos (06/10/2026)

**Tác nhân:** Kiro (VSCode/WSL) · **ECS cuối phiên:** `aa-cis-dev-api:455` + `aa-cis-dev-worker:11` (đều COMPLETED) · **Migration:** không có migration mới · **Image digest api==worker:** `d9cdc0c9`

## Trạng thái
Phiên dài, trọng tâm chuyển từ "làm nốt AA-723" thành "thiết kế module hóa job cho toàn hệ sinh thái" (Nghiệp mở rộng). Giao được: AA-666 verify, AA-723 Done trọn (3 PR + hotfix), ADR 0003, pilot Laos 3 tour. Dừng trước nấc 2 (atom_ranking swap) để làm cẩn thận phiên sau.

## Đối chiếu list việc đầu phiên
| Việc | Kết quả |
|---|---|
| a. AA-666 verify live tab inline | ✅ inline trong `/admin/tenants` (KHÔNG trang riêng); 3 endpoint data 200. Memory không lệch. |
| b. AA-723 S1 → worker | ✅ PR1 #568, DoD pass (deploy giữa wave → 0 interrupted) |
| c. AA-725 pre-deploy guard | ❌ chưa làm → phiên sau (backlog) |
| d. AA-726 bước 0 (publish_log + WP password) | ❌ chưa làm → phiên sau (backlog) |
| e. Pilot Laos 3 tour | ✅ 3/3 master; wave 46 còn lại CHƯA bung |
| f. AA-733 skill restructure | ❌ chưa làm; `skill-draft/` còn untracked ở root → phiên sau |

## Kết quả chính (4 PR merged + verified live)
- **AA-666 Done verify:** route check — chỉ 1 route `/admin/tenants` (page.tsx), không có `/admin/tenants/[id]`. 3 endpoint tab inline live 200: `/tenants/{id}/details`, `/admin/billing?tenant_id=`, `/tenants/{id}/audit`. (Side finding: `/tenants/{id}/usage` 500 nhưng KHÔNG FE nào gọi — endpoint chết, không chặn.)
- **AA-723 Done (3 PR):**
  - **#568** s1_rewrite + revalidate + s1_batch_ingest → shared.job/worker. Giữ live stream AA-667 (redis worker), read-before-write (version_id vào progress → reap idempotent). `GET /admin/jobs/{id}` map shared.job → shape cũ FE (không đổi FE). Xóa 4 wrapper chết.
  - **#569** gom 2 recompute (atom-delete scope=tour, status-change scope=platform) → 1 kind `recompute` + **debounce** (burst reuse 1 pending job). admin.py `_recompute_after_status_change` async + enqueue (5 call-site); admin_atoms enqueue. Chạy own-thread/loop/conn như a3 (vì `time.sleep` Cohere).
  - **#570 hotfix** `route_pkey` collision khi reactivate tour (AA-713 deactivate→activate): route_detection insert raw route_id v1 trùng row superseded cũ. Bug tiền tồn, trước bị nuốt im lặng (fire-and-forget), worker phơi ra. Fix: version theo max-ever-per-identity (incl superseded).
- **ADR 0003 #27 (root, merged tay):** one durable job model, 3 lớp (enqueue / stage registry / write strategy). + `docs/architecture/job-model-modularization.md` (kế hoạch nấc 1-6).
- **Pilot Laos (first-run, 0 master trước):** 3/3 lên master, 0 rớt review, atomized. 4 cột:
  | tour | master | q | atoms | review |
  |---|---|---|---|---|
  | 3 Rivers Discovery Loop | active | 7.0 | 51 | none |
  | CHICKEN RUN | active | 8.0 | 6 | none |
  | CLASSIC LAOS | active | 7.0 | 28 | none |

## Bằng chứng verify LIVE
- AA-723 DoD: enqueue 3 s1_rewrite → force-deploy API giữa chừng (03:31Z), worker KHÔNG restart → 3/3 succeeded attempt 1, 0 interrupted, 1 version/tour.
- recompute kind: deactivate+activate pilot tour → 1 job (debounce 2→1), sau hotfix chạy succeeded (routes_written 59, superseded 58, unchanged 260, tours_ranked 228).
- Rollout COMPLETED, api==worker digest `d9cdc0c9`, 3+1 kind mới live trên `/admin/job-runner`.

## Còn lại (chuyển phiên sau — ĐÃ neo Linear)
1. **AA-734** (mới, Medium): atom_ranking versioned-swap — cách B (gộp write 6 market + route 1 transaction, MVCC, không cột version, không sửa reader). Lưu ý: route_detection ĐỌC atom_ranking → compute/write phải tách, write chung 1 transaction. Verify poll overview+Slate no-dip. **Làm riêng 1 phiên.**
2. **AA-735** (mới, Low): job-model nấc 3-6 (stage registry + fold a3-recompute; cron→job; flip JOB_WORKER_IN_API default + dọn pipeline_jobs legacy + dead `_background_tasks` drain; cross-repo khi cần).
3. **Wave Laos 46 tour** — bung SAU khi AA-734 xong (recompute mới no-dip). Nhớ: wave 46 phải gọi `POST /admin/s1/seo-prefetch` cho cả 46 TRƯỚC khi rewrite (mua SEO gom 1 lần — bước FE, không tự enqueue trong run-tour). Thuộc AA-653.
4. AA-725, AA-726, AA-733 (chưa đụng phiên này).

## Lưu ý kỹ thuật / BÀI HỌC
- **s1_seo_prefetch KHÔNG tự enqueue trong run-tour** — là bước FE riêng (`startRun` gọi prefetch trước). Chạy wave bằng curl thẳng run-tour-async thì skip prefetch (admin S1 tự `process_seo()` lẻ, vẫn có SEO nhưng mua lẻ). Wave 46 phải prefetch trước.
- **Move sang durable worker PHƠI lỗi bị giấu:** route_pkey collision (AA-713 reactivate) vốn bị fire-and-forget nuốt → tour reactivate âm thầm không route. Durable+retry làm nó hiện ra = giá trị thật.
- **run-tour-async giờ enqueue shared.job** (không asyncio). `GET /admin/jobs/{id}` đọc shared.job trước, fallback pipeline_jobs. `_SHARED_JOB_STATUS_MAP`: cancelled→interrupted cho FE.
- **recompute concurrency=1**, own thread/loop/conn (a3 pattern) vì Cohere `time.sleep(3.5)` starve /health (S201).
- **JOB_WORKER_IN_API default=true** là điểm dễ vỡ: api set env `false` thủ công mới không chạy 2 worker. Dọn ở AA-735.
- ECS exec enum gotcha: `coalesce(source_status,'')` fail (enum) → dùng `::text NOT IN (...)`. published_tours KHÔNG có `created_at` (dùng `published_at`); review_queue có `review_status`/`failure_summary` (không `status`/`reason`).
- Secret admin header: `X-Admin-Secret` (`aa-cis/dev/admin-secret`). Domain Dev `https://api-cis.lumiguides.it.com`. WanderLux `a1b2c3d4-0001-4000-8000-000000000001`.
- Runner ECS exec: `.tmp-session/s209_run.sh <py> <s3key>`; lệnh >~100s chạy nền + poll S3; `--profile aa365-admin` flag rời (zsh không word-split `$P`).
- Log local: file này. Memory Notion: prepend S214... (phiên này là S213).
