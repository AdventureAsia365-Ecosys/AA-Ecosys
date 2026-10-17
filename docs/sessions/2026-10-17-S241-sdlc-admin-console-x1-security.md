# S241 — 17/10/2026 — Rà soát SDLC + data, console admin 2 khu, X1 tách quyền DB (S1→S8), Cognito Phase 0, đợt bảo mật tier-1

**Tác nhân:** Claude Code (VS Code, Ultracode). Phiên chính điều phối, workflow nhiều agent:
build trong worktree → review đối kháng → sửa. Agent con chỉ commit; push, PR, merge, Terraform apply,
DB Migrate, ECS exec, Redis, Vercel, GitHub settings và Linear đều do phiên chính làm. Giai đoạn dev:
agent tự code → push → merge → deploy → verify → báo cáo (Nghiệp chốt S241, memory `dev-phase-self-merge`).

**Audit / bằng chứng (repo gốc, private):**
- `docs/audits/2026-10-17-S241-sdlc-review/` (báo cáo SDLC/ADLC + lộ trình hợp nhất với data standards, artifact
  https://claude.ai/artifact/MQtWM3o23Tit1tzvJ4D3ko, gitleaks AA-ACP-App);
- `docs/audits/2026-10-17-S241-admin-console/` (tư vấn tổ chức admin, Q1–Q10);
- `docs/audits/2026-10-17-S241-x1/` (kế hoạch X1 23 bước / 5 đợt, bản undo);
- `docs/audits/2026-10-17-S241-ui-verify/` (Playwright 1440/390, sáng/tối);
- `docs/audits/2026-10-17-S241-restore-drill/`.

**Quyết định của Nghiệp:** `docs/sessions/2026-10-17-S241-decisions.md` (D-01…D-25, Q1…Q10, Cognito, cách khách đăng nhập,
và các chốt buổi tối).

## Trạng thái cuối phiên
- **ECS CIS:** api `:673` / worker `:230`, cùng image `dev-58801f33…` (#805), rollout COMPLETED, `/health` 200.
- **Booking:** `/booking/health/ready` = 200, `bk-014`. **TripPlanner:** tp-013, browse 200.
- **Migration áp trong phiên** (DB Migrate check → apply, `shared.job` rảnh):
  - X1 S8: `roles/001_x1_owner_roles.sql` (rl-001) → CIS **243** → Booking **bk-014** → TripPlanner **tp-013**.
  - Bảng Booking/TripPlanner giờ thuộc `bk_owner` / `tp_owner` (NOLOGIN). DB Migrate đọc chủ sở hữu thật trước mỗi file.
- **Probe cô lập X1** (`db-isolation-probe.yml`): **39 pass / 16 pending / 0 fail**. 16 ô pending đều phía CIS (đợt S11–S19).
- **Terraform (acc2)** áp trong phiên:
  - Cognito Phase 0 (58 tài nguyên);
  - ECS Exec session logging + RDS `log_connections`;
  - alarm OK mail + retention;
  - trust OIDC chỉ `main`;
  - ECR CIS IMMUTABLE + lifecycle;
  - alarm API GW CIS;
  - Lambda tự xoá snapshot RDS (đang chạy thật).
- **GitHub:**
  - repo gốc AA-Ecosys chuyển **private**;
  - org bắt buộc 2FA (chỉ phương thức an toàn);
  - 3 repo app public bật secret scanning, push protection, Dependabot, CodeQL, PVR, ruleset chặn force-push/xoá `main`;
  - Infra và repo gốc bật Dependabot alerts;
  - env `dev` của CIS chỉ cho `main`;
  - `ADMIN_SECRET` chuyển vào env `dev`;
  - xoá secret thừa `VERCEL_DEPLOY_HOOK`, `ACPCORE_READ_TOKEN`;
  - **AA-ACP-App đã xoá** (Nghiệp xoá trên web).
- **Vercel:** Git integration tắt ở 3 repo, deploy do CI tạo chỉ khi đổi `frontend/**` (`VERCEL_TOKEN` do Nghiệp tạo).
- **Sentry:** backend CIS gửi lỗi (project `aa-cis-api`). Uptime monitor `api-cis…/health` mỗi phút; gói free chỉ 1 monitor.
- **Snapshot RDS thủ công:** còn 3 (01/10, 05/10, 16/10). `g0-audit-20260916` đã bị Lambda xoá theo luật 30 ngày.
- **`shared.job`:** rỗng lúc deploy cuối (deploy-gate `safe_to_deploy: true`).

## Kết quả chính (issue → PR → bằng chứng)
- **Tư vấn SDLC/ADLC + hợp nhất với data standards:** báo cáo, bảng điểm 1,5/4, P0-A/P0-B, lộ trình U-01…, 25 quyết định D-xx.
  Tạo 25 issue mới (AA-866…AA-886) + viết lại AA-729 (bộ mẫu chuẩn ~100). Đi qua từng quyết định với Nghiệp.
- **Vercel CPU + tần suất deploy:**
  - CIS #787: poller admin chạy trên react-query; Jobs chỉ poll khi có việc; list `fields=summary`; verify cache 5 phút; BFF stream body.
  - #788 / Booking #28 / TP #95: deploy do CI tạo theo `frontend/**`.
- **AA-836 / AA-863 / AA-834** (#787, sửa thêm #789/#790): portal tenant 390 px, catalog 404, markdown thô, seed place, smoke chờ hydrate.
  UI verify đạt; lỗi pill ROUTE đã sửa ở #789.
- **Xoay admin secret** đủ 5 nơi: Secrets Manager, ECS api+worker, Vercel prod+preview, GitHub, Lambda DFS.
- **Hotfix auth admin** (#791): các GET admin ẩn danh trả 403; thêm CI guard "mọi route admin phải có auth"
  (chạy được trên cả FastAPI 0.110 và 0.143).
- **D-12 tenant pool fail-closed** (#792): đọc cờ lỗi thì đi tenant pool. Đã ghim cờ `aa544:publish_log_list_pool` = "false" trước merge.
  Infra #164 copy lại comment 237/241.
- **AA-882 phân quyền server** (#793 GĐ1, #794 GĐ3): `staff_policy` theo (method, route); verify-admin đọc lại role/is_active.
  reviewer 403 / admin 200.
- **AA-883 console 2 khu** (#794, #796, Booking #30): Platform / CIS Content, trang Staff chỉ đọc, link qua lại các app.
  Smoke 36/36. **Done.**
- **AA-751 X6 đợt 2** (Booking #27 deploy gate OIDC, #29 preflight): seed job → deploy bị chặn → huỷ → qua.
  Alarm tồn đọng Booking ALARM → OK. Docs R1 trong PR gốc này.
- **Cognito Phase 0** (Infra #162, AA-854):
  - pool `aa-workforce-dev` (us-west-1_bCcFvbSOS) và `aa-external-dev` (us-west-1_nKOvHan0W);
  - 7 group (thêm `booking-content_creator`), 4 trigger Lambda, 14 alarm, 2 metric, secret break-glass;
  - WAF tắt; khoảng 2,4 USD/tháng.
- **D-07/D-08** (Infra #161): nhật ký phiên ECS Exec (`/ecs/aa-cis-dev/exec-sessions`), RDS log_connections/disconnections.
- **D-10 restore drill:** PITR ra instance tạm khoảng 22 phút, 148/148 bảng, migration khớp, instance tạm đã xoá.
  Comment AA-829.
- **D-01:** Dev không có PII thật (8 khách Booking + 6 khách TP, toàn email test).
- **X1 (AA-852):**
  - S1 Infra #163 (owners.yaml, `roles/`, DB Migrate chuyển role theo chủ sở hữu thật);
  - S2 #165 (probe; baseline 24/27/4/0);
  - S3 #166 rl-001; S4 CIS #795 (243);
  - S5 Booking #31; S6 Booking #32 (bk-014); S7 TP #96 (tp-013); copy Infra #167;
  - đoàn tàu S8 apply cả 4 file.
  - Sau đó: Booking ready 200 / bk-014, TP browse 200, probe 39/16/0.
- **AA-868** (#797): pip-audit chặn thật (danh sách bỏ qua có hạn), `concurrency: deploy-dev-cis`, guard job fail-closed
  (script + test). **Done.**
- **AA-872** (Infra #168): 53/53 alarm có OKActions (test ALARM → OK có mail); retention 365 (flow, WAF, exec, postgresql) / 30 (app).
  Khoảng +0,5 USD/tháng sau 1 năm. **Done.**
- **AA-866** (Infra #169/#170, settings): env `dev` chỉ `main`; `terraform-apply` chỉ chạy từ `main`.
  Trust IAM có `ref = refs/heads/main` trên `aa-cis-dev-app-deploy` + `aa-cis-infra-tf-apply`.
  Thử trước bằng role nháp; role thật từ chối khi gọi từ nhánh khác (run 39034825070). **Done.**
- **AA-867:** tính năng bảo mật GitHub miễn phí, ruleset, Dependabot (Infra #173), 2FA org, gitleaks AA-ACP-App 0 phát hiện, repo đã xoá. **Done.**
- **AA-869:**
  - ECR CIS IMMUTABLE (#798 bỏ `:latest`, Infra #171, quyền #176 apply tay; #799 dùng lại image cùng SHA);
  - diễn tập rollback 672/229 → 670/227 (SHA cũ, `/health` 200) → trở lại;
  - Lambda hết hạn snapshot (Infra #177, #178 bật thật; xoá 1, giữ 3);
  - runbook `skill/aa-ship` §5 + `docs/ops/incident-response.md` trong PR gốc này.
  - **Done khi PR gốc merge.**
- **AA-870** (Infra #172, CIS #805):
  - alarm 5xx (≥ 5/5 phút) + p95 > 5 s;
  - Sentry backend api + worker (không gửi body/cookie, header theo danh sách cho phép, release = SHA image), secret `aa-cis/dev/sentry-dsn-api`;
  - lỗi test hiện trên Sentry (ảnh Nghiệp); uptime CIS.
  - **Done.**
- **CIS #806** (docs): ghi chú freeze view `catalog.*` tới X1 S22 trong CONTEXT.md.

## Thay đổi Codebase
- **CIS:** #787–#799, #805, #806.
- **Booking:** #27–#32.
- **TripPlanner:** #94–#96.
- **Infra:** #161–#173, #176–#178.
- **Gốc (PR cuối phiên):**
  - data standards: C4.1, C5.1b 0,02/50, C5.2e, C6.x, bảng enforcement, retention: snapshot 30 ngày, postgresql 365 ngày;
  - schema-ownership;
  - ADR 0006: thêm group `booking-content_creator`;
  - `skill/aa-ship` §5 Rollback; `docs/ops/incident-response.md`;
  - lessons: Copy Guard, ECR immutable, quyền role apply, nhánh cũ + secret repo;
  - các thư mục audit S241, log + quyết định + nháp Jira, backlog.

## Còn lại (việc chưa xong) → chi tiết trong `docs/backlog/README.md`
- **X1 (AA-852 / AA-860):** S9 file probe, S10 ADR 0004b, S11–S14 SG theo app + `db_migrator`, S15–S19 `cis_app` / `cis_owner` (CIS 245),
  S20–S23. Freeze view `catalog.*` tới S22.
- **Cognito (AA-854 → AA-703):**
  - tạo user break-glass (AdminCreateUser SUPPRESS → nhóm cis-admin + booking-admin → disable; Nghiệp tự đặt giá trị secret);
  - Phase 1: staff CIS + Booking đăng nhập qua WORKFORCE pool;
  - sau đó AA-816 (UI tạo/khoá staff).
- **AA-885** tách portal tenant (Q8, làm ngay). **AA-858** Overview (Q9, agent thiết kế rồi đưa chị Thư xem). **AA-884** Apps / nhật ký / chi phí.
- **AA-729** bộ mẫu chuẩn khoảng 100 mẫu (D-23).
- **Bảo mật tier-1 còn lại:** AA-873 GuardDuty…, AA-874 Redis AUTH/TLS, AA-875 safe_http, AA-876 biên API, AA-878 sổ secret + tài khoản E2E chỉ đọc,
  AA-879 cổng CI đồng đều, AA-871 Sentry/JSON log cho Booking + TP.
- **AA-859** đợt 3–4, D5b. **AA-861** `tripplanner.job`. **AA-829** runbook khôi phục 1 schema + CNAME DSN + dump 16/09.
- **Ghi chú cho chị Thư:** Vercel Pro khi có tenant trả tiền đầu (D-18); hồ sơ pháp lý (AA-886) có Sentry là bên xử lý phụ.
  Nháp Zalo ở `docs/sessions/2026-10-17-S241-jira-drafts.md`.
- **AA-ACP-Core** (private, archived, 23 KB): Nghiệp chốt **giữ nguyên** (không ảnh hưởng gì).

## Lưu ý kỹ thuật cho phiên sau
- **Bootstrap role** (`aa-cis-infra-tf-apply`, `aa-cis-dev-app-deploy`, inline policy của chúng): CI apply không sửa được → plan có target
  từ main đã merge, apply tay bằng `export $(aws configure export-credentials --profile aa365-admin --format env | xargs) && unset AWS_PROFILE`.
- **Trust giờ có `ref = main`:** mọi workflow dùng 2 role này phải chạy từ `main` (dispatch nhánh khác sẽ `Not authorized`).
- `terraform-apply.yml` chỉ chạy bằng dispatch → sau merge Infra phải `gh workflow run terraform-apply.yml --ref main`.
- **ECR CIS IMMUTABLE:** deploy cùng SHA tự dùng lại image. Không bao giờ push `:latest` (placeholder cũ sẽ hết hạn theo lifecycle).
- **Rollback ECS:** `skill/aa-ship` §5. Chọn revision gần nhất có **image khác** (deploy dùng lại image vẫn tạo revision mới).
- Đổi file migration CIS đã có bản copy Infra, kể cả comment → ship PR copy Infra cùng lúc (Copy Guard).
- DB Migrate dispatch chỉ nhận input `migration`, `mode` (+`override_busy_jobs`). Log runner nằm ở CloudWatch `/ecs/aa-cis-dev`.
- **Sentry:** `shared/sentry_init.py` dùng chung api + worker. Lỗi cùng stack sẽ gộp 1 issue. Gói free: 5k lỗi/tháng, 1 uptime monitor.
- `git cherry-pick` không có cờ `-q`. zsh không tách biến chứa danh sách → dùng `bash -c` khi lặp.
- **Snapshot thủ công:** muốn giữ quá 30 ngày thì đặt tên `keep-…` hoặc tag `aa:retain=keep` / `aa:retain-until=YYYY-MM-DD`.
