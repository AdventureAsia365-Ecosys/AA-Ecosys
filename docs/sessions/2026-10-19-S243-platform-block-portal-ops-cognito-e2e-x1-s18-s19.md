# S243 — 19/10/2026 — Khối nền tảng: tách portal tenant, Ops overview + Platform, Booking staff Cognito, E2E Cognito, X1 S15→S19, handbook

**Tác nhân:** Claude Code (Ultracode). Phiên chính điều phối, workflow nhiều agent (plan → critic → build trong worktree →
review → sửa; agent con chỉ commit). Push, PR, merge, Terraform apply, DB Migrate, ECS exec, Cognito, Vercel, Linear, Jira
do phiên chính làm. Merge theo luật dev-phase (S241 D-13, data standards v1.1 N-1): phiên chính tự merge khi CI xanh.

**Bằng chứng / audit (repo gốc):** `docs/audits/2026-10-19-S243-*` (ops runbooks, sdlc-docs-versioning), brief phiên
`.tmp-session/s243/` (session-facts.md, decisions.md, lessons-draft.md — không commit).

## Quyết định của Nghiệp trong phiên
- "bắt đầu session mới" → "ok làm hết" 8 lane: AA-816 (Cognito Phase 1), AA-885 (tách portal tenant), AA-680 (Booking
  staff qua Cognito), AA-858 (Ops overview), AA-884 (Platform apps/audit/cost), chore (TF imports/lockfile, Next 16
  proxy), AA-860 (X1 đợt 4, **S18/S19 làm cuối phiên**), AA-878 (secrets register, dọn secret mồ côi, tài khoản E2E chỉ đọc).
- AA-680: Booking giữ staff theo `cognito_sub`, backfill một lần; không view/endpoint CIS.
- AA-885: domain `portal.lumiguides.it.com`; `/privacy` trỏ trang adventure.asia, `/terms` tạm (adventure.asia chưa có).
- Link admin dùng domain chính thức (`booking.lumiguides.it.com`, `tripplanner.lumiguides.it.com`).
- Tài khoản `trang`: Disable (gắn email/sửa sau). Booking role của Nghiệp = admin.
- Secrets: cho phép script tự sinh mật khẩu và ghi thẳng vào Secrets Manager (không ai thấy giá trị); xoá 4 secret mồ côi
  sau khi kiểm (cửa sổ khôi phục 30 ngày). Token Mapbox cũ: Nghiệp tự thu hồi trong tài khoản Mapbox.
- Docs/SDLC: duyệt toàn bộ handbook, "làm hết theo lộ trình, ưu tiên 0 USD"; guide CEO song ngữ EN–VI + guide theo vai
  trò (new engineer, DevOps, CTO, CIO, PM); một handbook thống nhất. Đối chiếu S241 + data standards: N-1…N-12 "Ok hết"
  theo khuyến nghị (N-1 = quyền merge v1.1 dev-phase tự merge; N-7 = guide vai trò song ngữ, audit cho Nghiệp được viết
  tiếng Việt; N-6 tạo AA-901; N-12 gộp U-04 → AA-878, U-61 → AA-879).
- CRM (PR-19 / AA-821): tích hợp trong portal tenant cho khách B2C của tenant; chị Thư (Zalo 11:21): bỏ kế hoạch 40 tuần;
  mình nghiên cứu + lập kế hoạch lại sau ("làm sau"). Đã ghi vào AA-821 (2 comment 19/10).
- Jira: phương án D — Epic + Story báo cáo 2 tuần/lần trong project PR; kỳ 1 (01–19/10) chi tiết, không ghi số tiền
  (chi phí báo kỳ sau, sau rà soát chi phí đầu tháng 11), giọng "lưu ý" nhẹ, bỏ mục Vercel plan → "ok đăng đi" → đã đăng.
- Hộp thư E2E Cognito: **phương án B** — địa chỉ test tạm làm staff reviewer, gỡ khi xong việc E2E (ADR 0006a A10).
- TripPlanner: "TP #100/#101 merge luôn, sao lại không tự merge" → phiên chính tự merge cả PR TP (memory cập nhật).
- H7: "Làm luôn H7 đi" → mục DB connection trong `~/.claude/CLAUDE.md` (global) nay ghi: container `DATABASE_URL` =
  `cis_app`; việc cần master đi qua DB Migrate `run-script`.
- "Làm luôn đi, còn gì dang dở nữa không" → nghi thức cuối phiên.

## Kết quả theo repo

### Repo gốc (AA-Ecosys, master)
- #105 **engineering handbook thống nhất** (`docs/engineering-handbook.md`, catalog `docs/README.md`, templates, STYLE,
  glossary, llms.txt, guide vai trò `docs/guides/{ceo,new-engineer,devops,cto,cio,pm}.md` song ngữ, onboarding,
  agents.md, runbooks/playbooks ops, security baseline + vuln mgmt, finops, data standards v1.1, quyền merge v1.1).
- #101 secrets register (AA-878); #99 X1 plan S243 amendments; #102/#103/#104 schema reference sinh lại
  (#104: CIS 250, tp-015, bk-017, 256 version); #106 ADR 0006a **A10** (ngoại lệ staff E2E tạm + cách gỡ);
  #100 tài liệu ECS exec sau X1 S19 (`skill/aa-cis-schema/references/ecs-exec.md`, `skill/ai-nghiep/references/aws.md`).

### AA-CIS-App (main)
- **AA-885 Done:** #832 portal tenant thành Next.js app + Vercel project riêng `aa-cis-portal` trên
  `portal.lumiguides.it.com` (Infra #197 CNAME + URL client); smoke prod portal **24/24**.
- **AA-858:** #839 API ops overview, #840 `/admin/overview` (sức khoẻ app, TripPlanner traffic, phễu Booking, chi phí theo
  app); view hợp đồng Booking #37 (bk-017), TP #98 (tp-015), Infra #205.
- **AA-884:** #835 (CIS **248**: `acp_shared.audit_log` append-only có chuỗi hash, `job_worker.git_sha`, snapshot chi phí
  theo tag App), #836 API Platform apps/audit/cost + `/health` git_sha + `/health/ready`, #837 sửa cast uuid ở audit,
  #838 trang Platform (apps, nhật ký thao tác staff, chi phí theo app).
- **#848 (c201afa1)** một định nghĩa sức khoẻ cho Overview + Platform (`app_health.py`), luật worker alive, staff
  `readiness_now`, chi phí một nguồn (`shownSum`; Jev ghi `typesafe` gộp thành Jev, bedrock-satellite thành Bedrock),
  bảng mobile ScrollX, audit phân trang + thẻ trên điện thoại, bỏ mã nội bộ. **Verify live:** apps cis/booking/tripplanner
  overall ok; tổng chi phí 101.24 + 144.35 − 0.42 = 245.17; Jev 15.56 có dòng riêng; staff health có readiness_now.
  Phát hiện 8 (Bhutan: S1 sinh 33 vs raw active 32) chỉ ghi lại → backlog.
- **AA-878:** #841 vai trò **viewer** chỉ đọc (CIS **249**) + smoke login qua `context.request`; tài khoản
  `e2e-claude-code-viewer` + secret `aa-cis/dev/e2e-test-viewer` đã tạo (không Booking). Khuyến nghị: CI smoke vẫn dùng admin.
- **AA-816:** #842 E2E đăng nhập bằng mã email Cognito với hộp thư SES (Infra #198); #849 (411e5f18) ngoại lệ staff E2E
  tạm (CIS **250**: `admin_users_email_chk` chỉ cho `e2e@e2e-mail.lumiguides.it.com` làm reviewer, không owner, không mật khẩu;
  `E2E_TEST_STAFF_EMAIL` + `require_e2e_test_scope`).
- **AA-860 (X1):** #833 photo sync đọc place từ `geo` (S15), #834 mig **244** grant runtime + RLS parity cho `cis_app` (S16),
  #843/#845 sửa 244 (probe qua EXECUTE; chỉ cho view `v_ops_*` ngoài CIS) → 244 applied.
- Khác: #831 middleware.ts → proxy.ts (Next 16), #844 link admin dùng custom domain, #846 PR template + ADR index,
  #847 theo dõi Markdown docs, bỏ runbook v1.

### AA-CIS-Infra (main)
- #195 ops-probe đọc admin secret theo ARN (rời env + state), thêm enqueue `staff_directory_reconcile` vào lượt 06:15 UTC,
  bỏ 5 khối `import` đã apply, quyền StateLockfile; #196 alarm AdminCreateUser có mật khẩu (A8) + probe break-glass
  (`breakglass-otp-probe`: EMAIL_OTP **không** được đề nghị trên client breakglass và cis-admin → OK).
- #197 CNAME portal; #198 hộp thư SES inbound cho E2E; #199 link staff Booking thời bridge sang Cognito + copy bk-016;
  #200 run-script chỉ đọc (ngân sách kết nối cis_app, parity ảnh); #202 probe RLS parity `cis_app`; #206 quyền CloudWatch
  cho task role CIS; #207 Lambda TP đọc secret theo tên + quên secret mồ côi; #208/#201/#214/#210/#216 copy migration CIS
  248/244/249/250; #205 copy bk-017/tp-015; #209 `/health/ready` qua API GW; #211 PR template + ADR index; #212 context;
  #213 **cost anomaly** (IMMEDIATE ≥ $5 → topic alerts, miễn phí) + link runbook trong mọi alarm.
- #215 trigger WORKFORCE cho đúng 1 địa chỉ E2E (pre sign-up chỉ AdminCreateUser; pre token đòi đúng `cis-reviewer`)
  + SES receipt rule `tls_policy Require` → Terraform Apply 9 changed. #216 copy CIS 250 → DB Migrate check+apply 250
  (applied 2026-10-19 05:58:39Z, run 39207222673).
- #203 X1 **S18**, #204 X1 **S19** (xem mục X1).

### AA-Booking (main)
- **AA-680 staff qua Cognito live:** #34 bk-016 cột identity, #35 nhận token WORKFORCE song song bridge CIS, #36 nút
  "Sign in with company email" (client booking-staff), #37 view ops, #41 domain mặc định, #42 PR template/title check,
  #43 Dependabot config. Bằng chứng: log `booking_staff_provisioned`, ảnh Nghiệp chụp; SSO CIS/Booking = chung phiên managed
  login, mỗi app tự kiểm role.
- Dependabot: #44 (actions), #38 (source-map-js), #40 (next 16.2.4 → 16.3.8) merged cuối phiên; **#39 còn mở** (trùng #40,
  để Dependabot tự rebase/đóng).

### AA-TripPlanner-Web (main)
- #98 view ops traffic (tp-015), #99 Lambda đọc edge API key từ Secrets Manager, fail closed; #100 PR template/title
  check/ADR index; #101 Dependabot config; #102 bump actions.
- **#104 còn mở** (Next 14 → 15 major + postcss): build fail `ERESOLVE` (eslint-config-next@16 vs eslint 8) → cần kế
  hoạch nâng Next 15 riêng (backlog), không merge kiểu Dependabot.
- PR Dependabot luôn đỏ job "Vercel deploy" vì run của Dependabot không có Actions secret (`VERCEL_TOKEN`) — đúng dự
  kiến; việc tiếp: bỏ qua job đó khi actor là `dependabot[bot]` (backlog).

## AA-816 — phương án B (hộp thư E2E làm staff tạm)
- Staff tạo qua `staff_directory.create_staff`, actor `nghiep` (owner), audit `staff.created` 2026-10-19 06:00:03Z;
  Cognito user CONFIRMED, nhóm chỉ `cis-reviewer`; 0 grant Booking; không mật khẩu.
- `e2e-cognito.yml` run **39207450965** trên main: **7 passed** (đăng nhập thật bằng mã email, vào /admin, sign-out không tự
  đăng nhập lại).
- Gỡ = các bước removal của ADR 0006a **A10**; đã ghi vào backlog dưới AA-816.
- Còn lại của AA-816 (cutover, Stage S): mọi dòng active có email + `cognito_sub` riêng (staff health: thiếu email
  `e2e-claude-code`, `e2e-claude-code-2`, `e2e-claude-code-viewer`; thiếu `cognito_sub` admin, e2e-claude-code ×3, thu);
  thử break-glass qua managed login; xoay `ADMIN_SECRET`; tắt cờ legacy; thư mời (follow-up); xác nhận job đối soát chạy
  hằng ngày (trigger đã có, Infra #195); chị Thư đăng nhập lần đầu.

## X1 (AA-860) — S18 / S19
- S17: mật khẩu `cis_app` đã đặt đầu phiên (script tự sinh, ghi thẳng secret); 244 applied.
- **S18:** ARN rollback api:701 / worker:258 (ACTIVE). Infra #203 merge + apply (4 add / 2 destroy: 2 task def, metric
  filter, alarm 53300) → Deploy Dev 39208280468 → **api:703, worker:260 COMPLETED**. Phiên DB: `cis_app` (cis-api ×2,
  cis-worker ×1); đọc `booking.*`/`tripplanner.*` → 42501; 8 bảng ENABLE-only đếm = baseline; tour-versions 51 = baseline;
  admin smoke 200; tenant `/v1` 200; job `staff_directory_reconcile` b8155c60 succeeded trên worker; RoleConnections
  `cis_app` 3–4; probe xanh, không pending. Còn 1 phiên master mồ côi từ task api:701 đã dừng (10.2.10.69).
- **S19:** Infra #204 merge + apply (1 changed): task role CIS **Deny** `GetSecretValue` trên `aa-cis/dev/rds` (master),
  `aa-cis/dev/db-migrator`, `booking/*`, `tripplanner/*`. Từ container: 4 nhóm đó AccessDenied (IAM lan truyền ~8 phút:
  5 phút đầu kết quả lẫn lộn, sau đó 20/20 denied); `rds-app-user`, `rds-cis-app`, gdrive, booking-jwt, e2e-tenant vẫn đọc
  được. Probe xanh. Root #100 (tài liệu ECS exec) merged. Hết đóng băng merge CIS sau verify S19.
- Hệ quả: script ECS exec dùng `DATABASE_URL` của container (`cis_app`); việc cần master → DB Migrate `mode=run-script`.
- **Tiếp theo: đợt 5** — S20 (rl-002 `cis_owner` + `db_migrator`; Nghiệp tự đặt giá trị secret `aa-cis/dev/db-migrator`),
  S21 (CIS 245 chuyển ownership), S22 (workflow sang `db_migrator`; hết freeze `catalog.*` view).

## Jira
- Đã đăng (Nghiệp duyệt): Epic **PR-20** "Nền tảng kỹ thuật & vận hành — báo cáo định kỳ" và Story **PR-21** "Báo cáo nền
  tảng kỳ 1 (01–19/10/2026)" (parent PR-20). Chi tiết + nháp: [2026-10-19-S243-jira-drafts.md](2026-10-19-S243-jira-drafts.md).

## Trạng thái cuối phiên
- ECS CIS api **:703** / worker **:260** COMPLETED, chạy bằng `cis_app`; CIS migration **250**; Booking **bk-017**;
  TripPlanner **tp-015**; schema reference sinh lại (#104).
- Cognito WORKFORCE: nghieppham (owner), admin (break-glass, disabled), thu (admin, chưa đăng nhập), e2e@e2e-mail (reviewer tạm).
- 4 secret mồ côi lên lịch xoá 19/10 (khôi phục được tới **18/11/2026**): `aa-cis/dev/api-keys`, `aa-cis/dev/acp-webhook-secret`,
  `aa-cis/dev/acp-partner-api`, `tripplanner/dev/mapbox-geocoding-token`.
- Google Search Console: review lumiguides.it.com thành công, Chrome gỡ cảnh báo "Dangerous site" (19/10).
- PR mở: Booking #39 (Dependabot, chờ tự đóng), TP #104 (Next 15, chờ kế hoạch nâng cấp). Môi trường để chạy (không dừng hạ tầng).

## Còn lại / việc tiếp theo (theo thứ tự)
1. **X1 đợt 5** (AA-860): S20 → S21 → S22 (Nghiệp đặt giá trị secret db-migrator ở S20).
2. **AA-816 cutover** (Stage S) + gỡ ngoại lệ E2E tạm theo ADR 0006a A10 khi xong việc E2E.
3. **CI:** bỏ qua job "Vercel deploy" cho `dependabot[bot]` ở Booking/TP/CIS; **TP nâng Next 15** (thay cho Dependabot #104).
4. Đóng AA-858 / AA-884 / AA-878 khi đủ Done-when (đã live; còn mục nào thì làm nốt), AA-680 Phase 2 bỏ bridge CIS.
5. Rà soát chi phí đầu tháng 11 (Aug/Sep/Oct theo tag App) → số chi phí cho báo cáo Jira kỳ 2.
6. Dữ liệu: khoảng trống geo 8 nước của place-pipeline (backfill tốn tiền → cần duyệt); lệch Bhutan 33 vs 32.
7. CRM (AA-821 / PR-19): nghiên cứu + kế hoạch gọn, không theo kế hoạch 40 tuần.
8. Việc của Nghiệp: thu hồi token Mapbox cũ; chị Thư đăng nhập admin lần đầu; giá trị secret db-migrator ở S20.

## Lưu ý kỹ thuật cho phiên sau
- Script ECS exec: dùng `DATABASE_URL` (cis_app), không đọc `aa-cis/dev/rds` (AccessDenied từ S19); master → DB Migrate run-script.
- Sau khi apply một Deny IAM: verify lặp nhiều lần sau ≥ 5 phút (eventual consistency).
- Nhiều PR Infra cùng lúc → lỗi state lock ở Terraform Plan; đẩy lần lượt hoặc rerun sau khi apply xong.
- Shell phiên là zsh: biến chứa nhiều từ không tự tách; vòng lặp viết trong `bash -c`.
- DB Migrate: input `migration` có tiền tố owner (`cis/250_x.sql`); log đọc qua `gh api …/actions/jobs/<job>/logs`.
- Dependabot PR đỏ "Vercel deploy" là do thiếu secret, không phải lỗi code.
- Bài học mới đã ghi vào `skill/aa-lessons/lessons.md` (9 dòng S243).
