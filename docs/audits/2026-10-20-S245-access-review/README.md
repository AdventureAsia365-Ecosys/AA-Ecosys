---
id: SEC-05-2026Q4
title: Access review 2026-Q4 (first DM-8.10 review)
description: Ai và cái gì có quyền vào từng app (GitHub, Vercel, AWS IAM, Cognito, DB role, secret) tại 20/10/2026, kèm phát hiện và việc tiếp theo.
type: audit
status: final
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem, aa-cis-api, aa-booking, tripplanner-lambda, aa-cis-infra]
last_reviewed: 2026-10-20
review_every_days: 90
related: [SEC-01, SEC-02, SEC-05, AA-878, AA-838, AA-816, AA-829]
---

# Rà soát quyền truy cập 2026-Q4 (lần đầu, DM-8.10)

Ngày: 20/10/2026 (S245). Tác nhân: Claude Code (lane `secretsdrift`, chỉ đọc). Chi phí: 0 USD.
Lần sau: phiên đầu tiên của 2027-Q1 (DM-8.10, nhịp 90 ngày; lịch nhắc thuộc AA-838).

Không có giá trị bí mật, e-mail, account ID hay ARN nào trong trang này: chỉ tên role / pool / project, số
lượng, nhóm và cờ bật/tắt. Người dùng Cognito ghi theo vai trò và tên miền e-mail.

## 1. Nguồn và cách lấy

| Phần | Nguồn (20/10/2026, chỉ đọc) | Ghi chú |
|---|---|---|
| GitHub org + repo | `gh api` GET: `orgs/<org>/members`, `members?role=admin`, `teams`, `outside_collaborators`, `invitations`, `installations`; mỗi repo `collaborators`, `keys`, `hooks`, `environments`; cấu hình org | Token `gho_` mới (Nghiệp xoay 20/10) |
| GitHub secret | Danh sách tên theo repo / environment / Dependabot / org do phiên chính lấy 20/10 | Org: 403 (token không có quyền org-admin) |
| Vercel | Vercel MCP: `list_teams`, `list_projects`, `list_team_members`, `filter_project_envs` (không giải mã) | Chỉ tên biến, target, loại |
| AWS IAM | Terraform trên `origin/main` của AA-CIS-Infra (`accounts/aa365/*.tf`, `modules/ecs`) | Lệnh `aws iam` bị hook subagent chặn; đối chiếu live ở mục 4.3 là việc của phiên chính |
| Cognito | `cognito-idp list-user-pools / describe-user-pool / list-groups / list-users-in-group / list-users / admin-list-groups-for-user` | Chỉ đếm, nhóm, cờ Enabled, tên miền e-mail |
| DB role | `docs/architecture/db-schema-reference.md` mục Roles + Default privileges (dump live 19/10 13:00 UTC) | Không query DB |
| Secret | `docs/security/secrets-register.md` (drift check S245: `diff = 0`) | Ai đọc master RDS: bảng "Who can read the RDS master" |

## 2. GitHub (org AdventureAsia365-Ecosys, gói Free)

| Mục | Hiện trạng 20/10 |
|---|---|
| Thành viên org | 2: `pqnghiep1354`, `adventure365` — **cả hai là admin org** |
| Team | 0 |
| Outside collaborator / lời mời đang chờ | 0 / 0 |
| 2FA bắt buộc | Có |
| Quyền mặc định cho thành viên | `read`; thành viên được tạo repo: **có** |
| Collaborator từng repo (5 repo) | Chỉ 2 thành viên trên, quyền `admin` ở cả 5 repo |
| Deploy key / webhook repo | 0 / 0 ở cả 5 repo |
| GitHub App cài cho org | `vercel`, `linear-code`, `notion-workspace`, `claude` — **cả 4 đều "all repositories"** |
| Environment | AA-CIS-App: `dev`, `e2e`, `prod` (branch policy), `Preview`, `Production`, `staging` (không rule); AA-Booking: `dev` (branch policy), `Preview`, `Production`; AA-TripPlanner-Web: `Preview`, `Production`; AA-CIS-Infra: `dev`, `prod`, `staging` (**không rule**) |
| Secret | Khớp register (drift `diff = 0`); org-level không liệt kê được (403) |

## 3. Vercel (team Hobby)

| Mục | Hiện trạng 20/10 |
|---|---|
| Thành viên team | 1: chủ tài khoản (OWNER, GitHub `pqnghiep1354`); không access group |
| Project | 3: `aa-cis-frontend`, `aa-tripplanner`, `aa-booking-admin`. **Không có `aa-cis-portal`** (xem F-6) |
| Biến chứa bí mật | 9 tên có trong register; drift `diff = 0` |
| Cảnh báo của Vercel | `readable-secret` trên `SENTRY_AUTH_TOKEN`, `ADMIN2_PASSWORD` (aa-cis-frontend) và `TRIPPLANNER_API_KEY` Development + Preview (aa-tripplanner): loại Encrypted, ai vào được dashboard đều đọc được giá trị (F-5) |

## 4. AWS acc2 — IAM

### 4.1 Người

- Người vào acc2 bằng profile `aa365-admin` / `default` (cùng một role có MFA, phiên 8 giờ, AA-517). Agent
  chạy cùng profile đó (D-15: role agent `aa-cis-dev-agent-session` có nhưng chưa bắt buộc tới prod).
- Không có IAM user nào do Terraform tạo trên acc2. Có hay không IAM user / access key tạo tay thì phải đối chiếu
  live (mục 4.3).

### 4.2 Role máy và secret mỗi role đọc được (theo Terraform `origin/main`)

| Role (tên) | Dùng cho | Đọc secret nào |
|---|---|---|
| `aa-cis-dev-ecs-task-role` | CIS api + worker | **`secretsmanager:GetSecretValue` trên `*`**, trừ Deny X1 S19 (master RDS, `db-migrator`, `booking/*`, `tripplanner/*`) và Deny resource-policy của break-glass (open item 2 của register) |
| `aa-cis-dev-ecs-execution-role` | Kéo image, inject secret vào task CIS | Mẫu `aa-cis/dev/*` (execution role) |
| `aa-booking-dev-ecs-execution-role` / `-task-role` | Booking api | Chỉ `booking/dev/database-url` |
| `aa-tripplanner-dev-lambda-exec` | 2 Lambda TripPlanner | Chỉ `tripplanner/dev/database-url`, `tripplanner/dev/api-key` |
| `aa-cis-dev-db-migrate-execution-role` / `-task-role` | DB Migrate, Schema Dump, isolation probe | `db-migrator` (inject); trong task: danh sách DSN + master cho `roles/`, `set-password`, `run-script` |
| `aa-cis-dev-dfs-balance-check-exec` | Lambda ops probe | Chỉ `aa-cis/dev/admin-secret` (theo ARN) |
| `aa-cis-infra-tf-plan` | Terraform Plan (CI, mọi nhánh của Infra) | Danh sách secret có tên (`tf_plan_secret_arns`, để refresh) |
| `aa-cis-infra-tf-apply` | Terraform Apply, DB Migrate, Schema Dump, isolation probe (env `prod` + `main`) | **Mọi secret, kể cả master RDS, `db-migrator`, `booking/*`, `tripplanner/*`**: managed policy `SecretsManagerReadWrite` (1 trong 10 policy AWS, AA-806); boundary `tf_apply_boundary` mở bằng Allow `*` và không Deny nào chạm `secretsmanager`. Riêng break-glass có Deny resource-policy, nhưng role này có `PutResourcePolicy` / `DeleteResourcePolicy` nên gỡ được (có cảnh báo e-mail AA-854). Xem F-7 |
| `aa-cis-dev-app-deploy`, `aa-booking-dev-app-deploy`, `aa-tripplanner-dev-app-deploy` | Deploy app từ GitHub (OIDC) | Không đọc secret |
| `aa-cis-dev-agent-session` | Role agent (AA-730), chưa bắt buộc | Có `GetSecretValue` trong Deny `DenyDangerous` trên `*`, chưa có ngoại lệ cho secret E2E (U-04 bước 2) |
| `aa-identity-dev-*-trigger` (4 Lambda Cognito) | Pre sign-up / pre token | Không đọc secret |
| Role khác (flow logs, API GW logs, scheduler, NAT, snapshot expiry, e2e mail reader) | Hạ tầng | Không đọc secret |

Master RDS (`aa-cis/dev/rds`) đọc được bởi: migrator task role (trong task, cho `roles/`, `set-password`,
`run-script`), người có profile MFA (break-glass) **và role CI `aa-cis-infra-tf-apply`**: mọi workflow chạy trên
`main` của AA-CIS-Infra trong env `prod` (terraform-apply, db-migrate, db-schema-dump, db-isolation-probe) gọi được
`GetSecretValue` trên master và trên mọi secret khác (F-7). Container CIS: đã kiểm 20/20 AccessDenied (S243).
Chi tiết: register, mục "Who can read the RDS master".

### 4.3 Đối chiếu live còn thiếu (phiên chính chạy, chỉ đọc)

Lệnh một dòng, kết quả chỉ ghi số và tên vào mục này ở lần cập nhật sau:

```bash
aws iam list-users --profile aa365-admin --region us-west-1 --query 'Users[].[UserName,PasswordLastUsed]' --output text
aws iam generate-credential-report --profile aa365-admin --region us-west-1 --output text
aws iam get-credential-report --profile aa365-admin --region us-west-1 --query Content --output text | base64 -d | cut -d, -f1,4,5,8,9,10,11,14,16
aws iam list-roles --profile aa365-admin --region us-west-1 --query 'Roles[?!starts_with(Path, `/aws-service-role/`)].[RoleName,RoleLastUsed.LastUsedDate]' --output text
```

Câu hỏi cần trả lời: có IAM user nào ngoài Terraform không; access key nào cũ hơn 90 ngày hoặc không dùng; role nào
không dùng quá 90 ngày (ứng viên xoá).

## 5. Cognito (acc2)

| Pool | Người dùng | Nhóm (số thành viên / đang bật) | MFA |
|---|---|---|---|
| `aa-workforce-dev` (staff) | 4 (3 bật, 4 CONFIRMED) | `cis-admin` 3/2, `booking-admin` 2/1, `cis-reviewer` 1/1, `cis-content` 0, `booking-sales` 0, `booking-contracting` 0, `booking-content_creator` 0 | OPTIONAL (break-glass có TOTP; staff đăng nhập bằng mã e-mail) |
| `aa-external-dev` (khách / tenant) | 0 | — | OFF |

Từng người dùng staff (không ghi e-mail):

| Vai trò | Tên miền e-mail | Nhóm | Bật? | Nhận xét |
|---|---|---|---|---|
| Nghiệp | adventure.asia | cis-admin, booking-admin | Có | Đúng |
| Chị Thư (chủ doanh nghiệp) | adventure.asia | cis-admin | Có | Hỏi Nghiệp: chị cần admin hay chỉ reviewer? (Q-1) |
| Break-glass (`admin@`, D1) | adventure.asia | cis-admin, booking-admin | **Không** (tắt khi nghỉ, đúng thiết kế AA-854) | Đúng |
| Hộp thư E2E (AA-816 E1) | e2e-mail.lumiguides.it.com | cis-reviewer | Có | Tài khoản test, quyền reviewer; giữ |

Tài khoản đăng nhập kiểu cũ (`shared.admin_users`, khoảng 10 dòng) chưa query trong lane này. Trạng thái theo
register (S244): `e2e-claude-code` (full admin, legacy, tới S2), `e2e-claude-code-2` (full admin + Booking checker,
**vẫn bật**), `e2e-claude-code-viewer` (viewer, tài khoản smoke CI). Script đếm chỉ đọc cho phiên chính:
`.tmp-session/secretsdrift/s245_admin_users_summary.py` (in số theo role / active / password / cognito, chỉ in
username của tài khoản `e2e-*`).

## 6. DB role (RDS dùng chung)

Theo dump live 19/10 13:00 UTC:

| Role | Login | Thành viên của | Ai dùng |
|---|---|---|---|
| `aa_cis_admin` | có | `rds_superuser`, `cis_owner`, `cis_app`, `bk_owner`, `tp_owner` | Master; người dùng: break-glass + migrator task (`roles/`, `set-password`, `run-script`); secret của nó còn đọc được bởi role CI `aa-cis-infra-tf-apply` (F-7) |
| `db_migrator` | có (limit 5) | `cis_owner`, `cis_app`, `bk_owner`, `tp_owner`, `catalog_owner`, `pg_read_all_stats` | DB Migrate, Schema Dump, probe |
| `cis_app` | có (limit 90) | — | CIS api + worker (từ X1 S18) |
| `aa_app_user` | có (limit 15) | — | Pool tenant CIS (RLS) |
| `booking` | có (limit 15) | — | Booking api |
| `tripplanner` | có (limit 30) | — | 2 Lambda TripPlanner |
| `cis_owner`, `bk_owner`, `tp_owner`, `catalog_owner` | không | — | Chủ sở hữu bảng (NOLOGIN) |

Không role nào `superuser` hay `bypassrls` ngoài kế thừa `rds_superuser` của master. Default privileges: chủ sở hữu
cấp DML cho đúng role runtime của app mình (`cis_owner` → `cis_app`, `bk_owner` → `booking`, `tp_owner` →
`tripplanner`); không cấp chéo app.

## 7. Phát hiện

| # | Phát hiện | Mức | Việc / ai | Issue |
|---|---|---|---|---|
| F-1 | `e2e-claude-code-2` (full admin + Booking checker) vẫn bật | Trung bình | Tắt trên trang Staff (cần phiên owner Cognito: Nghiệp), quyết định D4 / N-F | AA-816 |
| F-2 | `e2e-claude-code` (full admin, đăng nhập mật khẩu) còn tới S2; trên Preview chỉ còn quyền viewer | Thấp (Dev) | Tắt ở S2 | AA-816 |
| F-3 | CIS task role đọc được mọi secret trừ các Deny (Allow `*`) | Trung bình | Thu hẹp Allow thành danh sách; hỏi Nghiệp trước (IAM) | AA-878 open item 2 → follow-up |
| F-4 | 0/29 secret có rotation tự động | Thấp (Dev, D-02/D-03) | Xoay khi nghi lộ / trước prod | Go-live (AA-880) |
| F-5 | 3 biến Vercel bí mật để loại Encrypted (đọc được trên dashboard): `SENTRY_AUTH_TOKEN`, `ADMIN2_PASSWORD`, `TRIPPLANNER_API_KEY` (Dev + Preview) | Thấp | Nghiệp tạo lại dạng Sensitive (tên có gạch dưới: sửa tay); `ADMIN2_PASSWORD` thì xoá luôn (F-11) | AA-878 follow-up |
| F-6 | Không có project Vercel `aa-cis-portal`, dù AA-CIS-App có `vercel-deploy-portal.yml` và secret `VERCEL_PORTAL_BYPASS_SECRET` | Cần làm rõ | Kiểm workflow portal có chạy được không; tạo project hoặc ghi rõ đã bỏ | AA-885 |
| F-7 | Role CI `aa-cis-infra-tf-apply` đọc (và ghi) **mọi secret** trên acc2, kể cả master RDS, `booking/*`, `tripplanner/*` (`SecretsManagerReadWrite`, boundary không chặn). Bất kỳ workflow nào chạy trên `main` của AA-CIS-Infra trong env `prod` đều lấy được giá trị; env `prod` lại không có protection rule trên GitHub, cổng duy nhất là claim `ref = refs/heads/main` trong OIDC trust (AA-866) | Trung bình | (1) Bỏ `SecretsManagerReadWrite` khỏi role apply, thay bằng grant theo tên ARN (giống `tf_plan_secret_arns`: chỉ secret Terraform quản lý + quyền quản lý metadata), hoặc thêm Deny `GetSecretValue` trên master / `booking/*` / `tripplanner/*` vào `tf_apply_boundary`; là bootstrap object nên apply tay bằng profile MFA, hỏi Nghiệp trước (IAM). (2) Thêm branch policy `main` cho env `prod` (miễn phí) để có hai lớp | AA-806 (thu hẹp policy), AA-866 (env) |
| F-8 | 4 GitHub App cài cho **mọi repo** (vercel, linear-code, notion-workspace, claude); 2 thành viên đều là admin org; thành viên được tự tạo repo | Thấp | Thu hẹp App về repo cần dùng (Vercel: 3 repo app; Linear/Claude: theo nhu cầu); cân nhắc tắt "members can create repositories". Nghiệp quyết | mới (hỏi Nghiệp) |
| F-9 | Không liệt kê được secret cấp org (token thiếu quyền org-admin) | Thấp | Nghiệp xem tay: Org Settings > Secrets and variables > Actions; nếu trống, ghi "0" vào register | AA-878 |
| F-10 | Secret cấp repo đọc được từ mọi nhánh: `VERCEL_TOKEN` ×3, `TF_VAR_DB_PASSWORD` | Trung bình | Chuyển vào environment có branch policy | AA-878 open item 7, U-25 |
| F-11 | Vercel `ADMIN_PASSWORD`, `ADMIN2_PASSWORD` (+ username), `INTERNAL_API_KEY`: không ai đọc trên main | Thấp | Nghiệp xác nhận rồi xoá tay | AA-878 open item 5 |
| F-12 | Role agent: `DenyDangerous` chưa có ngoại lệ NotResource cho secret E2E viewer | Thấp (role chưa bắt buộc, D-15) | Làm khi bật role agent bắt buộc (U-53) | U-04 bước 2 |
| F-13 | Dump dữ liệu thật 16/09 vẫn nằm trên laptop (`docs/backups/2026-09-16`, khoảng 11 MB, gitignored) | Trung bình | Chuyển lên S3 SSE-KMS riêng rồi xoá bản local | AA-829 |
| F-14 | Secret của acc1 / acc3 chưa kiểm kê | Thấp | Phiên chính liệt kê tên (MFA) và thêm dòng | AA-878 open item 9 |
| F-15 | IAM chưa đối chiếu live (mục 4.3) | — | Phiên chính chạy 4 lệnh chỉ đọc | AA-878 |

Câu hỏi cho Nghiệp: **Q-1** chị Thư cần `cis-admin` hay `cis-reviewer` là đủ? **Q-2** thu hẹp 4 GitHub App
(F-8) và tắt "members can create repositories"?

## 8. Đã đóng từ lần trước (để đối chiếu)

- Không có lần trước: đây là bản ghi đầu tiên. Trong 7 ngày qua đã đóng: secret Preview `ADMIN_SECRET` bị giới
  hạn viewer (C9), xoay `aa-cis/dev/admin-secret` (I6), smoke CI chạy bằng tài khoản viewer (N1), 4 secret mồ côi
  xoá (19/10), 2 secret GitHub mồ côi xoá (17/10), Lambda TripPlanner hết giá trị bí mật trong env (I2),
  `gho_` được xoay (20/10), token Mapbox geocoding cũ bị thu hồi (20/10), quy tắc deny đọc `~/.aws` và
  `~/.config/gh` cho Claude Code (root #120, U-04 bước 1).

## 9. Làm lại lần sau

1. Chạy drift check theo register ("How to run the drift check") với đủ 4 inventory; `diff = 0` trước khi rà quyền.
2. Lặp lại mục 2–6 bằng đúng các lệnh chỉ đọc ở mục 1 và 4.3.
3. So với bảng phát hiện trên: dòng nào đã đóng thì ghi vào mục 8 của bản mới.
4. Cập nhật bảng SEC-05 trong `docs/security/README.md`.
