# S242 — 18/10/2026 — Đăng nhập staff bằng mã email (Cognito Phase 0+1), X1 tách mạng S9→S14, trang đăng nhập riêng AA, dọn Dependabot

**Tác nhân:** Claude Code (VS Code, Ultracode). Phiên chính điều phối, workflow nhiều agent (build trong worktree → review
→ sửa; agent con chỉ commit). Push, PR, merge, Terraform apply, DB Migrate, ECS exec, Cognito, Vercel, Linear do phiên
chính làm. Nghiệp tắt auto mode vài lần cho các bước bị chặn (ghi Cognito/Secrets Manager, apply MFA). Phiên có một lần
tạm dừng (Nghiệp cho máy ngủ, ghi chú `.tmp-session/s242/RESUME.md`) rồi tiếp tục.

**Audit / bằng chứng (repo gốc):** `docs/audits/2026-10-18-S242-cognito-phase1/` (plan.md = kế hoạch Phase 1 do judge gộp
2 phương án; reader-maps.md; aa854-evidence.md; screens/01–04 managed login cũ, 10–11 thiết kế AA mới).

## Quyết định của Nghiệp trong phiên
- Duyệt danh sách đầu phiên (AA-854 → X1 → AA-885 → AA-816 …), "làm luôn", tắt auto mode khi cần.
- Break-glass giữ `admin@adventure.asia` (S241); tài khoản staff hằng ngày của Nghiệp = `nghieppham@adventure.asia`.
- Thêm chị Thư `thu@adventure.asia` làm admin CIS (Nghiệp tự tạo trên trang Staff; sau đó tự chuyển Booking role về None).
- Trang đăng nhập phải đồng bộ UI AA; chuyển sang domain riêng sau khi Chrome báo "Dangerous site".
- Có thư mời khi tạo nhân viên; thêm bộ lọc "Show disabled". Không có nút xoá staff (giữ lịch sử, Disable = nghỉ việc).
- Dọn sạch PR Dependabot ở mọi repo.
- Cuối phiên: giải thích đơn giản việc đã làm.

## Kết quả chính
- **AA-854 Done** (Cognito Phase 0): break-glass (password + TOTP, secret, alarm OK→ALARM, disable lại), spike SUPPRESS +
  EMAIL_OTP → user CONFIRMED đăng nhập được, user không nhóm bị trigger chặn, tự đăng ký bị chặn, managed login v2 + PKCE.
- **AA-816 (Phase 1 CIS staff) live trên Dev** — In Progress (còn cutover):
  - Infra: I1 #183 cảnh báo đọc/ghi secret break-glass + resource policy; I2 #184 tool `tools/identity/workforce_bootstrap.py`;
    I3 #185 task role CIS quản lý WORKFORCE + Deny chiếm tài khoản; #194 custom domain `staff-auth.lumiguides.it.com` +
    branding AA (provider 6) + apex A → Vercel; #191 TXT Google Search Console.
  - CIS: C1 #807 mig **247** (+ Infra #186); C2 #808 verifier JWKS; C3 #809 API nhận token Cognito + middleware Bearer;
    C8 #810 gắn email (nghiep owner, admin = break-glass); C4+C5 #811 đăng nhập "Sign in with company email" (PKCE) + BFF
    chuyển Bearer; C6 #812 trang Staff tạo/khoá/đổi vai trò; C7 #813 job đối soát; #826 frontend sang domain mới;
    #828 thư mời SES + "Resend invite" + ẩn tài khoản disabled; #829 sửa test (CodeQL); #827 CONTEXT.md.
  - **Verify live:** Nghiệp đăng nhập bằng mã email (log `staff_identity_linked` → `staff_bearer_verified role=admin`,
    DB `cognito_sub` + `last_login_at`); token RS256 giả → 401; probe task role (ListUsers OK, SetUserPassword/GetUser/EXTERNAL
    → AccessDenied); tạo ThuLe (Cognito CONFIRMED, đúng nhóm); thư mời tới hộp thư (job + audit `staff.invite_sent`); bấm lại
    → 429 "đợi 9 phút"; bộ lọc disabled chạy.
- **Chrome "Dangerous site"** (Safe Browsing gắn cờ lumiguides.it.com "deceptive" sau khi mở đăng nhập qua
  `amazoncognito.com`): Nghiệp gửi form báo nhầm + verify Search Console + Request review (18/10). Mình chuyển đăng nhập
  sang `staff-auth.lumiguides.it.com` với logo/màu AA (pre-validate trên client EXTERNAL; Cognito bắt logo tỉ lệ ≤ 4:1).
  **Chờ Google duyệt** (email Search Console).
- **AA-852 X1 S9→S14 (đợt 3, mạng + migrator):** S9 bk-015/tp-014 chạy đúng `bk_owner`/`tp_owner`; S10 ADR 0004b (root #95);
  S11 #180 6 SG + task def migrator; S12 #182 DB Migrate/Dump/probe chạy trên migrator, mode `set-password`/`run-script`,
  không thêm env var; S13 #187/#188/#189 Booking, TP + dfs Lambda, CIS api/worker sang SG riêng (Booking không tới Redis:
  TimeoutError); S14 #190 bỏ sg-app khỏi RDS/Redis/EFS. Probe **39 pass / 16 pending / 0 fail**.
- **Dọn Dependabot:** CIS #814 (next 16.4.2 …), #820, #819 (pytest 9 + pytest-asyncio 1.3, bỏ mục pip-audit pytest), #830
  (5 bản vá + `dependabot.yml` gom security updates, tắt version updates); Infra #192 (Actions), #193 (**AWS provider 6.69.1**,
  apply No changes). Đóng #800–#804, #815–#818, #821–#825, Infra #174/#181.
- Tài liệu R1: ADR **0006a** (root), ecosystem-architecture §4.6 Identity, schema-ownership, x1-plan "S242 amendments".

## Trạng thái cuối phiên
- ECS CIS api `:684` / worker `:241` COMPLETED; Booking `/booking/health/ready` 200 bk-015; TP tp-014; CIS migration **247**.
- Cognito WORKFORCE: nghieppham (owner, linked), admin (break-glass, disabled, TOTP), thu (admin, chưa đăng nhập).
- Terraform acc2 trên provider 6.69.1; state cũ v5: version `J5F5SH1RZxnqFSJKPfAcfNtlfw3aHK.H` (đường lùi).
- Repo: 4 repo con về main sạch; PR mở còn #830 (auto-merge) khi viết log.

## Còn lại
- AA-816: thử break-glass qua managed login (`/api/auth/signin/cognito-breakglass`); kiểm TOTP có chặn đăng nhập chỉ bằng
  mã email cho break-glass không; lịch chạy hằng ngày cho job đối soát (Infra: ops-probe gọi schedule); hộp thư E2E (D2);
  cutover (tắt đăng nhập mật khẩu khi mọi dòng active có `cognito_sub`, xử lý `e2e-claude-code*`).
- Gửi thư mời cho chị Thư **sau khi Google gỡ cờ** (Resend invite trên trang Staff).
- Lệch nhóm: nghieppham + admin có nhóm `booking-admin` trong Cognito nhưng không có `staff_app_grant` (job đối soát sẽ báo).
- X1 đợt 4 (S15–S19, AA-860, `cis_app`) sau Cognito; S17 Nghiệp lưu DSN `cis_app` trong Console.
- Booking Phase 2 (AA-680 staff): Booking chưa nhận issuer Cognito (cần sửa code, không chỉ config).

## Lưu ý kỹ thuật cho phiên sau
- boto3 không đọc cache MFA của CLI → script dùng `C=$(aws configure export-credentials …) || exit 1; export $C`.
- Shell có `AWS_REGION=ap-southeast-1` → lệnh AWS luôn ghi `--region us-west-1`.
- Dependabot PR không có secret (Vercel/AWS) → check đỏ; dựng lại nội dung trên branch của mình.
- PR song song cùng sửa 1 file ghi chú → DIRTY, auto-merge đứng im (lesson mới); mỗi lane ghi notes file riêng.
- Cognito: logo managed login tỉ lệ 1:1–4:1; asset thay đổi = branding bị thay mới (id mới); hosted domain không có
  `/.well-known/openid-configuration` (nằm ở URL issuer).
- `terraform plan` local sau khi lên v6 in "Failed to decode resource from state" (thuộc tính v5 còn sót) — chỉ cảnh báo.
