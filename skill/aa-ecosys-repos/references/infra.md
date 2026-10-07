# AA-CIS-Infra

- Roots: `accounts/aa365` (acc2: ECS api+worker, RDS, S3 trong `main.tf`; IAM/OIDC `cicd.tf`; TripPlanner BE `tripplanner.tf`; cost explorer + DFS balance + observability), `accounts/acc3-bedrock` và `accounts/acc1-bedrock` (trust role satellite).
- Workflow: `terraform-plan.yml` chạy tự động trên PR; `terraform-apply.yml` **chỉ chạy bằng workflow_dispatch** (`--ref main`). Không apply tay bằng CLI.
- OIDC: `cicd.tf` (`aa-cis-dev-role`) trust `repo:<org>/*:*`; TripPlanner deploy role dùng dạng `@id` wildcard.
- IAM vừa cấp trong cùng lần apply → có thể cần apply lại lần 2 (eventual consistency).
- CI role phải có quyền `application-autoscaling` write cho worker.
- State key vẫn là `dev/terraform.tfstate` dù environment tên `prod` — lệch tên, không phải lỗi.
- Bedrock satellite IAM: role invoker và batch trên acc3/acc1 trust ECS task role của acc2; ExternalId riêng từng account. Policy assume nằm ở `aa-cis-dev-ecs-assume-bedrock-invoker` (khác `aa-cis-dev-ecs-task-policy`).
