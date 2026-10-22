# S247 — 22/10/2026: 20 issue Done — pool tenant đợt 3–4, FAQ T9 lọc bằng LLM, GitHub App + release-please, lật Places, CRM W0

**Tác nhân:** Claude Code (Ultracode, nhiều workflow và subagent song song; VSCode, WSL2; agent điều phối tự merge/deploy/verify theo luật giai đoạn dev, push/merge bằng GitHub App `aa-agent` từ giữa phiên).

Nguồn số liệu: `docs/audits/2026-10-22-S247-wrap/state-snapshot.md` (kiểm live ~14:45 UTC), comment Done cuối của từng issue trên Linear, checklist sống `.tmp-session/S247-checklist.md`. Phần chưa kiểm được ghi rõ "chưa verify".

## Trạng thái

- **ECS (kiểm ~14:45 UTC 22/10):**
  - CIS `aa-cis-dev-api:775` và `aa-cis-dev-worker:334` cùng image `dev-5a54bd2` (release 0.5.0), rollout COMPLETED, 1/1. Worker chạy `T9_FAQ_LLM_FILTER=on`.
  - CIS `/health`: version **0.5.0**, git_sha 5a54bd2; `/health/ready`: schema **268** (yêu cầu 257).
  - Booking `aa-booking-dev-api:42`, image 466ad8e, rollout COMPLETED; `/booking/health` version 0.2.0; ready schema **bk-018**.
  - Lambda TripPlanner `aa-tripplanner-dev-browse` / `-assembly`: cùng CodeSha256, cập nhật 22/10 06:47 UTC; `PLACES_SOURCE=cis` (lật trong phiên, AA-847).
  - `shared.job` queued/running: **0**. Cờ AA-859 đợt 4: 6/6 `"true"`.
- **Migration mới nhất mỗi owner** (db-schema-reference Verified 22/10 13:28 UTC): CIS **268**, TripPlanner **tp-017**, Booking **bk-018**.
- **Vercel Production:** aa-cis-frontend 51415e2 (#936; các merge sau chỉ đổi backend); aa-tripplanner 0e9fdcf (release 0.4.0).
- **Repo (default branch):** AA-Ecosys master 998bc0a (#180) + nhánh đóng phiên `docs/s247-close`; AA-CIS-App main 5a54bd2 (PR mở: #908, nháp luật bữa ăn); AA-Booking main 466ad8e; AA-TripPlanner-Web main 0e9fdcf; AA-CIS-Infra main 62d0f79 (#291).
- **Visibility:** AA-Ecosys và AA-CIS-Infra **chuyển sang public** từ 22/10 (Nghiệp quyết; phút GitHub Actions cho repo private đã hết tháng 10). Ba repo app vẫn public như trước.
- **Linear (đọc lại cuối phiên):**
  - Done trong phiên (20): AA-859, AA-901, AA-909, AA-879, AA-903, AA-871, AA-891, AA-779, AA-780, AA-845, AA-803, AA-847, AA-760, AA-759, AA-894, AA-928, AA-929, AA-930, AA-931, AA-886.
  - Còn In Progress: AA-816, AA-911, AA-839 (AA-839 ở plan.json trước đây ghi Backlog — lệch, đã sửa theo Linear).
  - Không tạo issue mới trong phiên.

## Quyết định của Nghiệp (trong phiên)

- Làm hết việc làm được, không đề xuất đóng phiên khi còn việc (memory `finish-before-closing`). Dev không chờ nhiều ngày — đo ngay (memory `dev-no-waiting` cập nhật): burst AA-847 thay cửa sổ 7 ngày; burst main pool AA-859.
- Thứ tự đóng phiên mới: nháp Jira → duyệt → đăng trước, kiểm nguồn thật trước khi viết log (root #172).
- Skill đóng gói zip vào `skill/dist` (root #176); bỏ zip gộp (root #181). Nghiệp tự upload 5 zip lên claude.ai.
- Jev: đánh giá câu Jev hiện có, chỉ áp vào T-series nếu có hiệu quả → kết quả: verdict Jev có sẵn kém Haiku cho FAQ (chỉ phủ 66/200 câu); tái dùng ở T-series $0 không thấy hại (0 mục bị loại tới tenant); FAQ giữ Haiku + Sonnet.
- AA-803/AA-845: chấp nhận giữ `a1_claim_supported` + `a1_promise_unsupported` **ON** là kết quả cuối (comment Linear 03:41 UTC) — xem mục "Lệch" bên dưới về #908.
- Duyệt cả 8 đề xuất ("OK hết"): xoá 5 biến Vercel `ADMIN_*`; `SENTRY_AUTH_TOKEN` + `TRIPPLANNER_API_KEY` (preview) chuyển sang Secret, bỏ bản dev; thu hẹp GitHub App bên thứ ba (vercel 3 repo, linear 5 repo; notion giữ nguyên); trạng thái rỗng portal bằng route interception (không tạo tenant mới); metering không đếm lượt portal; `--aa-muted2` đậm hơn; FK thật bằng migration.
- Root + Infra public ("code xong rồi quay lại private"). Mật khẩu DataForSEO trong lịch sử Infra: **không xoay** (Nghiệp; như AA-841 S239). ADR 0014 có amendment (root #182).
- Tắt auto mode; 4 luật quyền bền trong root `.claude/settings.json`, luật dùng một lần chuyển sang `settings.local.json`.
- PAT cũ: khuyên thu hồi, Nghiệp chưa làm.
- S3 script cũ: xoá (đã làm: 2.471 → 51 object, giữ `restore/`, `*_swap/`, `aa545_code/`, `sync/`).
- Jira: duyệt cả 5 nháp ("Ok hết").

## Thay đổi Codebase

**AA-CIS-App** (PR đã merge, theo comment Linear): #906 (Trivy chặn + coverage ratchet), #907 (`ITIN_MEAL_INVENTED` rộng hơn), #909 (migration 261: `a3_place_locate` về Sonnet), #910 (`POST /admin/places/backfill` nhận `tour_ids`), #914 (PortalShell), #915, #921 (Vercel Deploy `id-token`), #923, #924 + #926 (log JSON + request id, worker `service=cis-worker`), #925 (rà portal, PR đầu tiên mở bằng `app/aa-agent`), #927 (pool tenant đợt 3, migration 262), #928 + #930 (release-please, v0.4.0), #929 (`/v1/trip/abc` → 404), #931 (lọc câu FAQ bằng Haiku, migration 264), #933 (migration 254), #934 (answer-fit Sonnet, migration 267, CIS ADR 0011 Accepted), #935 (pool tenant đợt 4, migration 265/266), #936 (portal: trạng thái rỗng, metering, tương phản), #937 (migration 268 FK), #938 (tín hiệu chờ của main pool). Sau đó release **0.5.0** (main 5a54bd2). #919 là PR thử đỏ (đóng, không merge). **#908** (luật bữa ăn) vẫn mở dạng nháp.

**AA-Booking:** #55 (kiểm security header), #57 (guard thiếu DSN), #59 (tag runtime Sentry), #60 + #61 (release-please, v0.2.0).

**AA-TripPlanner-Web:** #122 (guest token trên 4 GET đọc), #123 (CI gate parity), #124 (smoke chờ 404), #126–#129 (log JSON, Sentry, body hỏng → 400, environment dev), #130 + #131 (release-please, v0.4.0).

**AA-CIS-Infra:** #265 (lint tag class + retention row), #267 (2 cờ Places vào Terraform), #268 + #271 (bootstrap CRM, CloudFront VPC origin), #272/#273 (điền id-map component), #274 (lật Places), #279 (drift check ERD), #280 (env-config register), #281 (3 workflow docs dùng token App), #282–#288 (bản sao migration 262/254/265/266/264/267), #284 + #289 (`t9_faq_llm_filter` shadow → on), #290 (bản sao 268), #291 (isolation probe phủ bảng đợt 4).

**AA-Ecosys (root):** #156, #157, #158, #160, #161, #164, #166, #168 (CRM W0: ADR 0005a/0006b/0008a/0010 Accepted, contracts, errata, data standards v1.3, readiness, design ERD crm, ADR 0010/0011 GitHub App + visibility, CODEOWNERS), #165, #167, #171–#176, #181, #182 (ADR 0014 amendment public, secrets register, lessons, audits); bot PR #162, #163, #170, #177, #178, #179, #180. PR này: log + backlog + tracker + snapshot + nháp Jira.

## Thay đổi Hạ tầng

- **Migration áp lên Dev qua DB Migrate (check → apply, bảng job rảnh):** CIS 261, 262, 254, 264, 265, 266, 267, 268. Không có migration Booking/TripPlanner mới (vẫn bk-018, tp-017). Số 263 không xuất hiện trong input (chưa verify có tồn tại hay không).
- **Places lật (AA-847):** Infra #274 → Terraform Apply 39721126752: `PLACES_SOURCE=cis` trên 2 Lambda TP; CIS `PLACE_SHAPES_ENABLED=on`.
- **T9 FAQ:** Terraform `t9_faq_llm_filter=on` (Infra #289, apply 39785219378).
- **CRM W0 (AA-931):** policy `aa-cis-infra-tf-apply-crm` + permissions boundary (bootstrap tay, MFA); CI apply 39718038099 (20 add, 6 change, 2 destroy — chỉ revision task-def template); CloudFront + VPC origin dùng lại NLB nội bộ có sẵn, task hello scale về 0. Chi phí $0 ở mức hiện tại.
- **GitHub:** 2 App `aa-agent` (5421824) và `aa-ecosys-ci-bot` (5421877) cài trên 5 repo; khoá App lưu Secrets Manager / GitHub secret env `release` (Infra: repo-level); secret `ROOT_REPO_DOCS_TOKEN` đã xoá. Root + Infra public. GitHub App bên thứ ba thu hẹp (vercel 3 repo, linear 5).
- **Vercel:** xoá 5 biến `ADMIN_*`; `SENTRY_AUTH_TOKEN` + `TRIPPLANNER_API_KEY` (preview) thành Secret.
- **Sentry:** project mới cho Booking và TripPlanner (lambdas + web); 8 issue thử đã resolve.
- **S3:** dọn script cũ trong bucket bronze `scripts/` (2.471 → 51).

## Bằng chứng verify

- **AA-859** (đợt 3–4): flip-verify 3 cờ đợt 3 và 6 cờ đợt 4 đều ON; main pool đo bằng burst, giữ 10; DB Isolation Probe run 39794013142: **58/58 pass, 0 dòng đọc chéo**.
- **AA-779:** đợt kiểm 8 blog với bộ lọc `on` (4 tenant, $0,855): 36 cặp viết → bỏ 7 → **29 giao**; panel 3 giám khảo: **0 câu trả lời lạc** (trước 3/31); F1 29/29. Shadow 2 blog: bắt đúng 1/9 câu lạc.
- **AA-847:** chạy place có phí đúng 58 tour coverage gate ($0,577) + thử Mông Cổ ($0,076); sau lật: coverage gate PASS, parity 21/21 (3 lượt); 353 call HTTP, 1 non-200 có lý do (tour Việt Nam không có tuyến cả trước lật); 4 trang 200 ở 1440/400 px; burst 120 s, 1.367 call đều 200, p95 669 ms, Lambda throttle/error 0.
- **AA-909:** 2 phiên khách độc lập: chủ 200, người khác/không cookie 404 trên cả 4 GET; body từ chối `{"error": "not found"}`.
- **AA-871:** request id từ header live → dòng JSON trên Logs Insights cho CIS, Booking, TP; Sentry nhận lỗi thử không PII (AA-BOOKING-API-1/2, AA-TRIPPLANNER-LAMBDAS-1, AA-TRIPPLANNER-WEB-1).
- **AA-891:** `/health` CIS 0.4.0 lúc đóng issue (nay 0.5.0), Booking 0.2.0, TP 0.4.0; PR release mở bởi `app/aa-ecosys-ci-bot`.
- **AA-901:** root #173 và CIS #925 tác giả `app/aa-agent`, đủ check bắt buộc xanh.
- **AA-879:** PR thử #919 đỏ ở Frontend Build; deploy TP chờ CI + smoke xanh; merge chỉ frontend không chạy Deploy Dev (#914, #915), đối chứng #923 có chạy.
- **AA-903:** Dependabot CIS #901: job "Vercel deploy" skipping, check bắt buộc xanh.
- **AA-760:** UI Smoke portal prod **50/50** (run 39786059490), 20 ảnh trạng thái rỗng; metering live trail-pulse 2684 → 2684 (3 call portal) → 2685 (1 call máy).
- **AA-759:** 13 đường dẫn cũ trả 308; UI Smoke portal 44 passed (run 39712530665).
- **AA-894:** bot PR #179 hiện diff FK của migration 268; `/admin/data-model` ảnh owner 1440/400 sáng/tối; reviewer/tenant/không auth đều 403.
- **AA-780:** rerun PASS 15/15, 0 câu sáo, 0 bài dưới 120 chữ ($0,344); brand rules Trail Pulse version 4.
- **AA-931:** host CloudFront trần → 403; partner 200; stream 30 s không bị cắt.
- **AA-886:** 7 Google Doc trong thư mục Drive "Legal readiness packet"; sharing chưa mở cho chị Thư.
- Bằng chứng chi tiết: `docs/audits/2026-10-22-S247-*` (aa760-portal, aa779-llm, aa847-flip, aa859-wave3, aa871-observability, aa894-data-model, crm-byo, crm-readiness, crm-w0, wrap).

## Jira

Nghiệp duyệt cả 5 nháp ("Ok hết"). Atlassian MCP rất chậm (nhiều lần timeout > 300 s). Nháp + trạng thái: `docs/audits/2026-10-22-S247-wrap/jira-drafts.md`.

- **Đã đăng:** PR-22 (comment 10491).
- **Có vẻ đã đăng, chưa verify:** PR-24 và PR-13 — issue cập nhật 22:40–22:42 giờ VN nhưng lệnh đăng timeout; cần mở xem bằng mắt.
- **Chưa xác nhận:** PR-27 — 2 lần đăng đều timeout; kiểm trước khi đăng lại (tránh trùng). Trước khi đăng, Nghiệp mở quyền chia sẻ thư mục Drive pháp lý cho chị Thư.
- **Chưa đăng:** PR-23 (kèm 2 ảnh `docs/audits/2026-10-22-S247-aa760-portal/empty-dashboard-desktop-light.png` và `empty-tours-mine-phone-dark.png`).
- Không đăng: PR-20 (báo cáo tuần, kỳ tới ~26/10), PR-19/PR-26 (CRM mới xong nền móng).

## Lệch phát hiện

- **#908 (luật bữa ăn):** comment Done của AA-803 (03:41 UTC) ghi #908 "parked as draft after six adversarial rounds", Nghiệp chấp nhận giữ ON là kết quả cuối; còn danh sách việc phiên sau trong session-facts ghi "#908 kiểm đối kháng rồi merge, sau đó tắt `a1_claim_supported`/`a1_promise_unsupported` (quyết định 1 S246)"; nháp Jira PR-13 viết "sẽ tắt sau khi có luật kiểm bữa ăn bằng code (đang làm)". Cần Nghiệp chốt một hướng ở S248.
- **AA-839:** Linear In Progress, plan.json ghi Backlog → sửa theo Linear.
- **AA-779:** comment Done ghi worker rev 333 (image c0b6c37); snapshot cuối phiên là rev 334 (dev-5a54bd2) do deploy sau đó — không phải lỗi.

## Còn lại

1. **Jira:** kiểm PR-27 (không đăng trùng), kiểm PR-24/PR-13 bằng mắt; đăng PR-23 kèm 2 ảnh. Nghiệp mở sharing thư mục pháp lý trên Drive.
2. **CIS #908** (luật bữa ăn có cấu trúc, phần B chồng lên phần A): kiểm đối kháng rồi merge, sau đó tắt `a1_claim_supported`/`a1_promise_unsupported` — chờ Nghiệp chốt vì lệch với kết quả AA-803 (mục trên). Chưa có issue.
3. **Đề xuất $0:** bỏ khỏi đầu vào writer T9 các câu `place_paa` đã bị `a3_question_about_here` / `a3_landing_belongs` loại (đo 32/52). Chưa có issue.
4. **CRM W1 AA-932:** pool `crm` phải vừa ngân sách kết nối (cis-api giữ 10 → 132/135; crm 6 thì thành 138).
5. **Repo public:** khi code xong trả root + Infra về private và quyết phút Actions (budget hay self-hosted runner). `AA_CI_BOT_PRIVATE_KEY` là secret repo-level trên Infra public (đọc được trong `pull_request` — chỉ người có quyền ghi).
6. **Thu hồi 3 PAT không dùng** (`aa-cis-infra-schema-dump`, `ACPCORE_READ_TOKEN`, `aa-cis-acpcore-read`) — Nghiệp; cùng PAT cũ của `ROOT_REPO_DOCS_TOKEN`.
7. **Follow-up đã ghi trên Linear (chưa có issue riêng):** admin app light `--aa-muted2` còn #9099A6; portal `--aa-muted` 4,43:1; revalidation đặt `published_tours.quality_score_id` NULL thay vì chuyển sang dòng score mới; hàng filter `/admin/review` bị cắt ở 400 px; mục probe `angle_gate_option` PARENT_SCOPED; blog bị giữ trong đợt 8 bài (F9 body facts ×2, F4 length ×1).
8. **Cost audit đầu tháng 11** (memory `infra-cost-audit-nov-2026`): phiên đầu tiên ≥ 01/11.
9. Theo master plan: AA-712 (sau lật), CRM W1 (AA-932, AA-972 — cần MFA), S1-first bước 2 (AA-645), AA-816 S2.

## Lưu ý kỹ thuật cho phiên sau

- **Claude Code khởi động lại là xoá scratchpad và giết workflow chạy nền;** helper điều phối nay ở `.tmp-session/s247/common.sh`.
- **Auto mode** từng chặn merge/apply/ghi secret/đổi visibility; Nghiệp đã tắt auto mode. Luật quyền bền ở root `.claude/settings.json`.
- **gh 2.45 không có `--accept-visibility-change-consequences`:** đổi visibility bằng `gh api -X PATCH repos/<org>/<repo> -f visibility=…`.
- **Atlassian MCP timeout (> 300 s) khi tải nặng; lệnh ghi có thể đã vào dù báo timeout** — kiểm bằng JQL `updated >= -Nm` trước khi gửi lại.
- **Push/merge bằng App:** `tools/github/as-app.sh` (token installation 1 giờ, `skill/aa-ship` §1). Subagent vẫn không push/merge.
- **Places:** `PLACES_SOURCE=cis` (2 Lambda TP), `PLACE_SHAPES_ENABLED=on` (CIS) — cả hai đã nằm trong Terraform (Infra #267/#274), không sửa tay nữa. `a3_place_days` Haiku 4.5, `a3_place_locate` Sonnet (migration 261).
- **Pool tenant:** cờ đọc lỗi = pool tenant (fail closed); 6 cờ đợt 4 ON; main pool giữ 10 (bão hoà từ c50); định cỡ pool theo gauge của pool, không theo `pg_stat_activity`.
- **Log JSON:** script grep log kiểu `key=value` cũ sẽ đọc 0 dòng — đọc trường JSON (bài học S247).
- Bài học mới của phiên trong `skill/aa-lessons/lessons.md` (root #182): worktree phải dùng đường dẫn tuyệt đối, helper ngoài scratchpad, cửa sổ log flip-verify sau t0, archive issue cha kéo theo sub-issue, gitleaks bỏ sót tfvars, Playwright fill trước hydrate, ECS exec cần `sh -c`.
