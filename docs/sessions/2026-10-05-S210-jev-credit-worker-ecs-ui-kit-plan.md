# S210 — Backfill memory H2, AA-720 (Jev credit) Done, AA-651 (worker ECS) Done, thiết kế AA-662 UI kit (05/10/2026)

**Tác nhân:** Kiro (VSCode/WSL) · **ECS cuối phiên:** `aa-cis-dev-api:436` COMPLETED + `aa-cis-dev-worker:1` COMPLETED (service mới) · **Migration mới nhất:** CIS 203 (không có migration mới phiên này)

## Trạng thái
- **Backfill memory Notion H2:** trang `memory_archive_2026H2` bị mất S197→S206 khi copy; đã backfill 10 phiên từ log local (tóm tắt phong cách memory, mới nhất ở đầu, nối liền H1 kết ở S196 và memory.md chính S207–S209).
- **AA-720 Done** (Jev credit monitoring) — verify live đủ 4 tiêu chí.
- **AA-651 Done** (worker ECS service) — verify live đủ, A 1-bước (api tắt in-process worker).
- **AA-662 (UI kit): mới ở bước thiết kế** — chốt phạm vi, Nghiệp duyệt tách 3 PR + làm bulk (B) + dùng react-query (C). **Chưa code.** Để trọn phiên S211.
- **AA-653 (rerun):** chưa đụng, xếp cuối, dời sang phiên sau.
- `.gitignore` bỏ dòng `skill/` + `git add skill/` (3 file) — đưa vào PR root cuối phiên cùng log + learning S210.

## Jev credit — đánh giá China (câu hỏi mở S209 → ĐÓNG)
- Probe live: `GET /v1/models` 200, `POST /v1/systemone` 400/422 (schema), KHÔNG còn 402 → credit ĐÃ nạp.
- Canary endpoint (sau deploy) trả `credit_ok:true` → bằng chứng vận hành xác nhận Jev sống lại.
- Đợt China 03/10 fail-open ~47.900 verdict `zone=error` (a1_claim_supported 57%, a3_atom_in_text 55%...).
  **ĐỌC CODE XÁC NHẬN fail-open KHÔNG hỏng dữ liệu:** grounding vẫn chạy luật số-liệu deterministic
  (`find_novel_numeric_claims` luôn chạy, chỉ mất tín hiệu `UNSUPPORTED_CLAIM`); `ground_day_atoms`
  `_keep = not rejected` → `zone=error` giữ nguyên atom. KHÔNG có đường re-verdict Jev read-only
  (a1_claim_supported trong graph S1 → reject kéo `s1_flag_fix` LLM writer đổi nội dung;
  a3_atom_in_text trong vòng atomize per-day + fingerprint-gated skip). **Quyết: China KHÔNG re-run**
  (chi phí = bậc đợt gốc + đổi content đã publish, không xứng); Jev phủ đủ từ pilot nước kế.

## Thay đổi Codebase
| Repo | PR | Nội dung |
|---|---|---|
| AA-CIS-App | #548 merged (6fd2b6d) | **AA-720** `decide.py`: `is_billing_error` (402 error_type), circuit breaker per-process (`_jev_cooldown_until`, env `JEV_CREDIT_COOLDOWN_MIN`=15m), trip+alert `platform.jev_credit.exhausted` throttle 1/24h, vẫn fail-open. `admin_llm_ops.py`: `POST /admin/jev-canary/check` + `/admin/jev/402-sweep` (secret-gated). 11 test mock-only. Không migration. |
| AA-CIS-Infra | #79 merged | **AA-720** Lambda `dfs-balance-check` mở rộng gọi 3 path (DFS + jev-canary + 402-sweep), độc lập per-path. |
| AA-CIS-App | #549 merged | **AA-651** `worker/` package (`python -m worker` entrypoint, shim over `shared.jobs.worker._main`); `deploy-dev.yml` deploy cả api + `${ECS_SERVICE}-worker`, skip worker nếu service chưa tồn tại. |
| AA-CIS-App | #550 merged | **AA-651** follow-up: `COPY worker/` vào Dockerfile + `worker/**` path filter (Dockerfile không copy cả repo). |
| AA-CIS-Infra | #80 merged | **AA-651** `aws_ecs_task_definition.worker` + `aws_ecs_service.worker` (no ALB, Spot-weighted, stopTimeout 120s, log prefix `worker`) + autoscaling target+policies (min1/max3); api task-def thêm env `JOB_WORKER_IN_API=false`. Biến mới `worker_task_cpu/memory/desired_count/max_count` (512/1024/1/3). |
| AA-CIS-Infra | #81 merged | **AA-651** grant CI role `application-autoscaling` write (Register/Deregister/PutScalingPolicy/DeleteScalingPolicy/TagResource/UntagResource). |
| AA-Ecosys (root) | PR cuối phiên | `.gitignore` bỏ `skill/`; version-control `skill/*.md`; learning S210; log S210 + index. |

## Thay đổi Hạ tầng (Dev)
- **AA-720:** Terraform Apply Prod #79 success (0 add/3 change/0 destroy, Lambda update in-place).
- **AA-651:** Terraform Apply Prod #80 (worker service + task-def + api env) — apply đầu fail autoscaling
  (CI role thiếu `application-autoscaling:TagResource`); #81 cấp quyền → apply lại **lần 2 mới ăn**
  (IAM eventual consistency); autoscaling worker tạo (3 added). ECS: api :433→:436, worker service mới `:1`.
- Deploy App: nhiều lần (merge #548, #549 không trigger deploy vì path, #550 trigger, re-run thủ công sau Infra).

## Bằng chứng verify
- **AA-720:** `POST /admin/jev/402-sweep` → 200 `{errors_24h:0,...}`; `POST /admin/jev-canary/check` → 200
  `{credit_ok:true,billing_error:false,breaker_open:false}`. Lambda invoke end-to-end → 200, 3 path ok/200.
  `jev_alerts_last_24h=0` (không false positive). CI 5/5 + Vercel pass; ECS :433 rollout COMPLETED.
- **AA-651:** worker service ACTIVE rollout COMPLETED running=desired=1 task-def `aa-cis-dev-worker:1`;
  log worker `job_worker_started kinds=[a3_atomize,photo_sync,s1_seo_prefetch,segment_research,t2_rewrite,t9_write]`;
  api task-def :436 `JOB_WORKER_IN_API=false` rollout COMPLETED; `shared.job_worker` sau khi settle:
  **live_workers_60s=1** (chỉ worker service beat, api tắt in-process). max_parallel=4.

## Còn lại
1. **AA-662 (UI kit)** — trọn phiên S211. Đã chốt: tách 3 PR (kit+demo / Review Queue / My Content),
   làm **bulk action** luôn (B), **dùng react-query** (C — adopt làm chuẩn fetching mới cho UI v2,
   thay fetch tay; cân nhắc QueryClientProvider ở layout). Kiểm kỹ (Vercel + render Dev từng PR).
2. **AA-653 (rerun)** các nước còn lại (Thái Lan → Lào → Nepal → Sri Lanka → Ấn Độ → Bhutan[chờ 2 NCC]),
   pilot 3 tour, báo cáo đầy đủ sau mỗi wave. Để sau AA-662.
3. AA-716 / AA-718 / AA-719 (bulk sẽ 1 phần làm trong AA-662) / AA-705 / AA-686 theo thứ tự ưu tiên.

## Lưu ý kỹ thuật cho phiên sau
- **AA-662 react-query:** Nghiệp chốt adopt react-query (đã cài `@tanstack/react-query ^5.99` nhưng chưa
  trang nào dùng — hiện fetch tay useState/useEffect/setInterval khắp nơi). DataTable + 2 trang migrate
  dùng `useQuery`/`useMutation`. `@tanstack/react-table` CHƯA cài — cần thêm. Frontend KHÔNG dùng Tailwind
  className mà inline-style + brand token (`A` admin / `T` portal, nguồn `app/_brand/tokens.ts`).
- **Primitive cũ divergent** cần hợp nhất qua kit + shim (đừng đổi signature `adminUi.tsx` — ~16 import site):
  Badge admin dùng `color` vs portal `variant`; EmptyState 2 chữ ký; Skeleton chỉ portal; ErrorState chỉ admin.
  2 trang migrate: Review Queue `app/admin/review/page.tsx` (~900 dòng, chưa có bulk → AA-719); My Content =
  `app/(tenant)/portal/_components/CatalogTab.tsx` (drawer/toast/export viết tay). BFF proxy, mọi page `"use client"`.
- **Thêm module top-level mới (App):** PHẢI thêm `COPY <mod>/` vào Dockerfile + path filter `deploy-dev.yml`
  (Dockerfile chỉ copy api/shared/services). Thay đổi chỉ-ngoài-filter → Deploy Dev KHÔNG chạy.
- **Terraform apply qua workflow repo Infra** (`gh workflow run "Terraform Apply Prod"`), KHÔNG apply CLI tay.
  CI role thiếu autoscaling write (api scalable target là out-of-band). Cấp-rồi-dùng quyền trong CÙNG apply →
  IAM eventual consistency, **re-run apply lần 2** là ăn. ECS task-def "must be replaced" = bình thường (immutable).
- **ECS exec từ Kiro:** zsh KHÔNG word-split biến nhiều flag → `bash -c` hoặc flag rời. `execute-command` treo
  tới timeout tool 120s → chạy nền + poll S3. Runner `.tmp-session/s210_run.sh <script.py>`, out `scripts/out/`.
  STS 8h hết hạn → dùng `--profile aa365-admin` (session cache còn). `control_bash_process` reuse terminal cũ
  (isReused:true) KHÔNG chạy lệnh mới — cẩn thận khi lặp exec. Chi tiết đầy đủ ở `skill/aa-cis-schema.md`.
- Secret admin verify endpoint: `aa-cis/dev/admin-secret` (JSON ~44 ký tự). Domain Dev `https://api-cis.lumiguides.it.com`.
