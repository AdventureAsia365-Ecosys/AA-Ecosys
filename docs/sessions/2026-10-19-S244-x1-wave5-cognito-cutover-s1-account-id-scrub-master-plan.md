# S244 — 19/10/2026 — X1 đợt 5 xong (S20→S22), cutover Cognito S1 trên Production, scrub account ID repo public, audit tổng thể + kế hoạch

**Tác nhân:** Claude Code (Ultracode). Phiên chính điều phối 6 workflow (lane code, audit tổng thể 12 agent, code cutover,
S22, khép phiên docs) và vài agent review/smoke. Agent con chỉ commit local; push, PR, merge, Terraform apply, DB Migrate,
ECS exec, Cognito, Secrets Manager, Vercel, Linear do phiên chính làm.

**Bằng chứng / audit (repo gốc):** `docs/audits/2026-10-19-S244-master-plan/` (README tiếng Việt, issues.md, backlog-proposal.md),
`docs/audits/2026-10-19-S244-aa816-cutover/` (cutover-prep.md, cutover-report.md). Scratch `.tmp-session/s244/` (không commit).

## Quyết định của Nghiệp trong phiên
- "ok làm" danh sách đầu phiên (AA-902, AA-860 S20→, AA-903, AA-904, AA-816 chuẩn bị cutover; chore lockfile; Bhutan).
- db_migrator: **script tự sinh mật khẩu** (như cis_app S243).
- AA-816: "làm hoàn thiện đi" → em chọn N-A…N-F theo khuyến nghị (bảng dưới); "Đổi biến vercel gì thì làm luôn rồi báo cáo".
- AA-902: "Làm luôn cho 902, kiểm tra kỹ" → em tự sửa các dòng env/secret có gạch dưới (Infra #221, secret repo TP).
- "Tạo issue follow-up" Next 16 → **AA-906**.
- "Cần audit tổng thể tất cả các issue … không chỉ các issue mới tạo" → workflow audit toàn bộ 84 issue mở.

| N | Câu hỏi | Chọn |
|---|---|---|
| N-A | Dòng chị Thư (email, không mật khẩu, chưa đăng nhập) tính là sẵn sàng? | Có |
| N-B | Xoá `password_hash` cũ của break-glass | DB Migrate run-script có review |
| N-C | Thứ tự | readiness → S1 → C9 + Preview credential + I6 ngay |
| N-D | Phiên HS256 cũ khi tắt cờ | để tự hết hạn ≤24h |
| N-E | Preview mất đăng nhập admin khi tắt cờ API | chỉ tắt cờ BFF Production; cờ API giữ tới S2 |
| N-F | `e2e-claude-code-2` | tắt ngay (cần Nghiệp bấm trên trang Staff) |

## Kết quả chính

### X1 đợt 5 (AA-860 / AA-852) — xong S20, S21, S22
- **S20** Infra #219: rl-002 (`cis_owner` NOLOGIN, `db_migrator` LOGIN limit 5, member bk/tp/cis_owner + catalog_owner + cis_app +
  pg_read_all_stats) + alarm `db_migrator = 5` (Terraform Apply: 1 added; lần apply đầu dùng S3 lockfile OK). DB Migrate apply rl-002.
  Mật khẩu: script dựng DSN từ master, ghi thẳng `aa-cis/dev/db-migrator` (AWS CLI + file tạm 600 + shred, không in giá trị);
  set-password run 39247263215 `test login current_user=db_migrator rolconnlimit=5`. Probe 56/0.
- **S21** CIS #853 (245) + Infra #223: introspect run-script (Infra #220) `move=121 refuse=0 ok=t`; apply 12:11:10Z (bảng job rảnh).
  Probe 57 pass / 0 fail / 0 pending. Smoke CIS admin 4 route 200, TP catalog-tours / routes 200.
- **S22** Infra #225 (task def migrator đăng nhập `db_migrator`; master chỉ đọc trong task cho roles/, set-password, run-script;
  review sửa connect_master + lint recipe catalog) → apply; check cis/242 `ran as: cis_owner — login db_migrator`, booking/013
  `ran as: bk_owner — login db_migrator`; set-password cis_app + run-script qua master trong task; CIS #860 + Infra #226 mig 246
  apply chạy dưới cis_owner. **Probe 58/58** (run 39256408600), catalog login db_migrator, không phiên master. Root #113 schema reference.
- **Hết đóng băng migration CIS và view `catalog.*` (XD9).** Recipe catalog trong CONTEXT.md.
- S23 docs: PR khép phiên (workflow close-out). AA-852: chưa Done — chưa có chỗ cho việc revoke grant 179/180 (audit gợi ý AA-847 nhưng đó là issue Places).

### AA-816 — cutover Stage S, S1 trên Production
- CIS #856 sign-out same-origin + E2E chứng minh lần sau phải nhập mã mới (e2e-cognito 7/7, chạy 4 lần trong phiên).
- **Break-glass qua managed login** (Playwright, mật khẩu + TOTP): vào `/admin/overview`, sign-out về `/login`, mở lại bị hỏi lại;
  alarm token break-glass ALARM đúng thiết kế; user tắt lại. Infra #224 run-script xoá `password_hash` (had_hash_before=true →
  has_hash_after=false, linked=true, audit row a64deb6e…). `breakglass-init` + `breakglass-verify` xoay mật khẩu + TOTP OK.
- **S1:** Vercel aa-cis-frontend Production `LEGACY_ADMIN_LOGIN_ENABLED=false` (tạo mới, plain, có comment rollback) + redeploy:
  `POST /api/auth/login` → 404, `/login` chỉ còn "Sign in with company email"; E2E Cognito xanh.
- **C9** CIS #858 (review độc lập: ship): guard admin-secret nhận principal Cognito đã verify; credential Preview
  `aa-cis/dev/admin-secret-preview` (~0,40 USD/tháng) bị giới hạn viewer; gỡ `create_staff_user.py`. Live: secret máy 200,
  không credential 403, 0 log "Invalid admin secret".
- **E3:** Vercel Preview `ADMIN_SECRET` = credential Preview. Smoke preview lần đầu **đỏ 15 test** (tài khoản smoke vẫn admin) →
  làm lại bước A3 (GitHub `E2E_ADMIN_*` → tài khoản viewer) + CIS #859 (spec ops-overview thiếu skip viewer) → smoke preview
  "logged in with staff role: viewer", **59 pass / 7 skip**.
- **I6:** xoay `aa-cis/dev/admin-secret` (kiểm bảng job rảnh trước), cập nhật GitHub CIS env dev + Vercel Production, restart api/worker,
  redeploy Vercel prod: secret mới 200, cũ 403; E2E Cognito xanh.
- Còn: N-F (Nghiệp), S2 (cờ API) cùng AA-680, A10 gỡ staff E2E tạm (giờ đã hết chặn).

### AA-902 — scrub account ID repo public (High)
- Đầu phiên: Linear tự đóng nhầm khi merge root #109 (thân PR ghi "AA-902–905") → mở lại.
- CIS #854 (23 file, account vệ tinh đọc env, allowlist rỗng), Booking #45, TP #105; Infra #221 (`BEDROCK_ACCT_PRIMARY/FALLBACK` cho
  CIS api/worker + 2 Lambda TP; locals 1 chỗ), Infra #222 copy lại mig 240; secret repo TP cho deploy role. Check resource-ID chặn CI
  ở cả 3 repo; PR thử CIS #857 / Booking #47 / TP #108 đều đỏ đúng "1 findings" rồi đóng.
- Live: CIS Cost Explorer 50 dòng có account_key acc1/2/3; từ container api assume role vào acc3 + acc1 bằng ARN dựng từ env OK;
  TP search `ranking=semantic`; Booking health/ready 200. Baseline page cập nhật (root PR này). Không viết lại lịch sử git.

### Việc khác
- **AA-903** merge 3 repo (review sửa: không bỏ qua deploy khi push lên main); chờ PR Dependabot đụng frontend để có bằng chứng.
  Đóng Booking #39 (Dependabot không rebase được). TP #109 (pytest 9 cần pytest-asyncio 1.4.0) sửa + merge.
- **AA-904 Done:** TP Next 15.5.28 / React 19 (TP #107); smoke preview vs production 4 luồng desktop + 390 px, không regression
  (Mapbox 403 trên URL preview hash do giới hạn token; React #418 thoáng qua sau deploy không tái hiện).
- **Bhutan 33 vs 32:** 1 tour bị trash 05/10 vẫn còn nháp S1; funnel chỉ đếm tour raw active ở mọi cột (CIS #852); live 32/32/32/32.
- **Chore:** Infra #218 S3 `use_lockfile` + CI Terraform 1.15.5 (review: ship; plan + apply dùng lockfile OK).
- **Audit tổng thể** (12 agent, verify phản biện): 84 issue mở (Data Platform 39, CIS Core 28 — 96/100 hạn mức, Portal 7, TP & Booking 10).
  Kế hoạch theo phiên + mốc + đường găng ở `docs/audits/2026-10-19-S244-master-plan/`. Đã áp dụng: mở lại 4 issue Done giả
  (AA-825, AA-805, AA-665, AA-669 → Backlog, có comment). Chờ Nghiệp: huỷ AA-675/AA-689, 4 issue mới N1–N4, nâng ưu tiên AA-901/875/876.
- Backlog sống thay §3/§3a/§4 theo kế hoạch, cập nhật trạng thái cuối S244.

## Sự cố trong phiên
- `export $(aws configure export-credentials …)` bị hỏi MFA (phiên 8h hết hạn), ra rỗng → `export` trần **in toàn bộ env vào
  transcript local**, gồm `GITHUB_PERSONAL_ACCESS_TOKEN` và `TF_VAR_db_password`. Không gửi đi đâu. Đã báo Nghiệp, đề xuất xoay token
  GitHub sớm. Sửa steering `session-workflow.md` sang cách an toàn; bài học trong `skill/aa-lessons/lessons.md`. (CLAUDE.md của Infra
  còn mẫu cũ → sửa ở PR close-out Infra hoặc phiên sau.)
- Bỏ bước A3 (smoke sang viewer) lúc đầu là sai → smoke preview đỏ sau C9; đã làm lại. Bài học đã ghi.

## Trạng thái cuối phiên
- ECS CIS api **:711** / worker **:268** cùng `dev-7e0c68a2`; Booking **:33** (`91812e7e`); CIS migration tới **250** (245, 246 applied);
  roles rl-002; Terraform CI 1.15.5 + lockfile. Không job treo.
- Linear: AA-904 Done; AA-902 Done khi merge root PR này; AA-860 / AA-816 / AA-852 / AA-903 In Progress (comment S244); AA-906 mới.
- MFA `aa365-admin` làm mới lúc ~11:45Z (8h).

## Việc đầu phiên sau (S245) — theo backlog sống §3
1. Kiểm probe đêm 20/10 04:13Z (`sessions.master_break_glass_only` pass) + dump `DUMP login=db_migrator` → AA-860 Done (sau docs S23).
2. AA-816: N-F (Nghiệp bấm Disable `e2e-claude-code-2`), A10 gỡ staff E2E tạm; AA-680 nửa staff (chứng minh user không nhóm booking-* bị từ chối, bỏ bridge).
3. AA-846 apply guard; AA-865 F9 re-flag; quay lại nội dung CIS theo kế hoạch.
4. Nghiệp duyệt các đề xuất audit (§2 backlog).

## Lưu ý kỹ thuật cho phiên sau
- DB Migrate giờ đăng nhập `db_migrator`; `roles/`, set-password, run-script vẫn chạy master (đọc trong task). Script ECS exec vẫn `cis_app`.
- View `catalog.*`: dùng recipe S22 (GRANT CREATE → SET LOCAL ROLE catalog_owner → … → SET LOCAL ROLE cis_owner → REVOKE), không RESET ROLE.
- Production CIS không còn đăng nhập mật khẩu: kiểm UI admin trên production phải qua Cognito; preview chỉ có quyền viewer.
- Thân PR / commit: chỉ ghi mã issue với "Refs"; mã trần (kể cả trong đường dẫn) làm Linear tự gắn và có thể tự Done.
- `gh pr edit` lỗi GraphQL Projects classic → sửa thân PR bằng `gh api -X PATCH repos/…/pulls/<n> --input body.json`.
- Plan Terraform có thể hiện `tags_all` trên object zip TP (deploy-lambdas ghi đè không kèm tag) — vô hại.
