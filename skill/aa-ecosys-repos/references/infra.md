# AA-CIS-Infra

- Roots: `accounts/aa365` (acc2: ECS api+worker, RDS, S3 trong `main.tf`; IAM/OIDC `cicd.tf`; TripPlanner BE `tripplanner.tf`; cost explorer + DFS balance + observability), `accounts/acc3-bedrock` và `accounts/acc1-bedrock` (trust role satellite).
- Workflow: `terraform-plan.yml` chạy tự động trên PR; `terraform-apply.yml` **chỉ chạy bằng workflow_dispatch** (`--ref main`). Không apply tay bằng CLI.
- OIDC: `cicd.tf` (`aa-cis-dev-role`) trust `repo:<org>/*:*`; TripPlanner deploy role dùng dạng `@id` wildcard.
- IAM vừa cấp trong cùng lần apply → có thể cần apply lại lần 2 (eventual consistency).
- CI role phải có quyền `application-autoscaling` write cho worker.
- State key vẫn là `dev/terraform.tfstate` dù environment tên `prod` — lệch tên, không phải lỗi.
- DB: `db/owners.yaml` (sổ đăng ký chủ schema, role, prefix key, job table), `db/migrations/<owner>/` (copy
  byte-identical của migration app; Copy Guard kiểm) + `db/migrations/roles/` (Infra-native, `rl-NNN`: role,
  `CONNECTION LIMIT`, extension, undo X1). Workflow DB Migrate / DB Schema Dump / DB Isolation Probe chạy task
  migrator (`accounts/aa365/db_migrator.tf`), login `db_migrator` từ X1 S22; master chỉ đọc trong task cho `roles/`,
  `set-password`, `run-script` (`db/scripts/`; DB Tour Liveness Gate hằng đêm cũng là một run-script READ_ONLY,
  AA-986, data standards DM-4.9). `apply` từ chối (exit 7) khi bảng job nào còn bận.
- Terraform Apply không có guard job: apply roll ECS service / task def / Lambda → idle gate tay trước (skill `aa-ship` mục 2).
- Bedrock satellite IAM: role invoker và batch trên acc3/acc1 trust ECS task role của acc2; ExternalId riêng từng account. Policy assume nằm ở `aa-cis-dev-ecs-assume-bedrock-invoker` (khác `aa-cis-dev-ecs-task-policy`).
