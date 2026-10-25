# AA-CIS-Infra

Nguồn sự thật: `infra/AA-CIS-Infra/.claude/CLAUDE.md` + `docs/`. Quy trình apply/merge/verify: skill `aa-ship`.

- Roots: `accounts/aa365` (acc2: `main.tf` ECS CIS + RDS + S3; `booking.tf`; `tripplanner.tf`; `crm_*.tf` AA-Partner;
  `identity*.tf` Cognito WORKFORCE / M2M / partner; `cicd*.tf` role CI; `db_migrator.tf`; observability, cost, SES,
  DNS…), `accounts/acc3-bedrock` và `accounts/acc1-bedrock` (role satellite Bedrock). Module dùng chung ở `modules/`.
- Workflow: `terraform-plan.yml` chạy tự động trên PR; `terraform-apply.yml` **chỉ chạy bằng workflow_dispatch trên
  `main`**, có plan guard (AA-846: từ chối khi plan đổi secret version / `random_password` / RDS instance, trừ khi
  `allow_guarded` + lý do). Không apply tay bằng CLI, trừ object bootstrap mà role CI bị cấm đổi (role CI, boundary,
  OIDC provider) — người apply bằng admin MFA.
- Role CI theo việc (AA-806, `cicd_split.tf`): `aa-cis-dev-app-deploy` (deploy CIS), `aa-cis-infra-tf-plan` (chỉ đọc),
  `aa-cis-infra-tf-apply` (apply + DB Migrate, có permissions boundary); mỗi app khác một role deploy riêng
  (ví dụ `aa-booking-dev-app-deploy`, `aa-crm-dev-app-deploy`). Trust OIDC dùng subject bất biến dạng
  `repo:<org>@<org_id>/<repo>@<repo_id>:<context>` — đổi tên hoặc tạo lại repo thì role thôi tin (fail closed).
- State key vẫn là `dev/terraform.tfstate` dù environment GitHub tên `prod` — lệch tên, không phải lỗi.
- Hai plan/apply chạy cùng lúc tranh S3 state lock ("Error acquiring the state lock") — chạy lại sau khi run kia xong,
  không phải lỗi code.
- Apply chạm task definition ECS đăng ký một **revision template** (image placeholder/`bootstrap`, env theo template),
  và lần deploy kế của app chép revision mới nhất → env đặt tay trên revision đang chạy có thể mất. Sau mọi apply như
  vậy, so tên env của revision mới nhất với revision đang chạy (bài học S250 trong `aa-lessons`).
- IAM vừa cấp trong cùng lần apply → có thể cần apply lại lần 2 (eventual consistency); Deny mới cần vài phút mới ổn định.
- DB: `db/owners.yaml` (sổ đăng ký chủ schema, role, prefix key, bảng job), `db/migrations/<owner>/` (`cis`,
  `booking`, `tripplanner`, `crm` — copy byte-identical của migration app; Migration Copy Guard so với `main` của repo
  chủ, nên PR của repo chủ phải merge trước) + `db/migrations/roles/` (Infra-native, `rl-NNN`). Workflow DB Migrate
  (`check` → `apply`; `apply` chờ mọi bảng job rảnh), DB Schema Dump (hằng đêm + sau apply: mở PR
  `bot/db-schema-reference` trên repo gốc, báo verdict drift — AA-853), DB Isolation Probe, DB Tour Liveness Gate chạy
  task migrator (`db_migrator.tf`, login `db_migrator`); master chỉ đọc trong task cho `roles/`, `set-password`,
  `run-script` (`db/scripts/`). Runbook: `docs/ops/runbooks/db-migrate.md` (repo gốc).
- Terraform Apply không có guard job: apply roll ECS service / task def / Lambda → kiểm bảng job rảnh trước (`aa-ship`).
- Bedrock satellite IAM: role invoker và batch trên acc3/acc1 trust ECS task role của acc2; ExternalId riêng từng
  account. Policy assume ở `aa-cis-dev-ecs-assume-bedrock-invoker` (`bedrock_satellite_assume.tf`, khác
  `aa-cis-dev-ecs-task-policy`).
