# AA-998 — DRY RUN xoá tài nguyên hệ sinh thái trên acc1 (S255, 28/10/2026)

Kiểm kê live (chỉ đọc, SSO `pqnghiep-admin`, 44 lệnh): `inventory_raw.txt`. Chi phí acc1: 08/2026 $45,15 · 09/2026 $0,97 ·
10/2026 (tới 27/10) **$0,76** — từ tháng 9 toàn bộ là Bedrock gọi dự phòng (Haiku 4.5 / Sonnet 4.6) khi acc3 lỗi.

## Thứ tự

1. **Cắt đường gọi** (code, acc2): `BEDROCK_ACCT_FALLBACK` rỗng cho CIS api/worker + 2 Lambda TripPlanner; gỡ acc1 khỏi
   gateway CIS/TripPlanner, Cost Explorer, catalog (migration mới), Infra `accounts/aa365` (grant AssumeRole sang acc1,
   bucket policy bronze, secret `AWS_ACCOUNT_ALIASES`, cert ACM mặc định). Verify: `llm_call_log` account='acc1' = 0.
2. **Terraform destroy root `accounts/acc1-bedrock`** (3 role bên dưới), rồi xoá thư mục + bucket state.
3. **Xoá phần còn lại bằng tay** (bảng dưới), từng mục, ghi lại.

## Danh sách xoá

| # | Tài nguyên | Hiện trạng | Hành động |
|---|---|---|---|
| 1 | IAM role `AA-Bedrock-Invoker` + inline `InvokeApprovedClaudeModelsOnly` | Terraform acc1-bedrock; đường dự phòng LLM | destroy (bước 2) |
| 2 | IAM role `aa-bedrock-batch-inference-role` | Terraform; batch S1 trên acc1 (không còn dùng) | destroy |
| 3 | IAM role `AA-CostExplorer-Reader` | Terraform; nút "Refresh from AWS" đọc chi phí acc1 | destroy |
| 4 | S3 `aa-cis-tfstate-acc1-bedrock-…` | 1 file state 17 KB | xoá sau bước 2 |
| 5 | S3 `acp-gold-…` | 11 object, 6,7 KB (ACP cũ, 22/05) | tải về lưu riêng rồi xoá bucket |
| 6 | Lambda `aa-cis-dev-acp-s4-trigger` + log group `/aws/lambda/aa-cis-dev-acp-s4-trigger` | sửa lần cuối 22/05, không có event source | xoá |
| 7 | Log group `/ecs/aa-cis-dev-api` (0 B), `/ecs/aa-cis-dev-langfuse` (338 KB) | hạ tầng cũ đã xoá 09/07 | xoá |
| 8 | ECS task definitions `aa-cis-dev-*` (bản cũ) | INACTIVE, không tốn tiền | deregister + delete |
| 9 | IAM role `aa-role-deploy-nonprod`, `aa-role-readonly`, `rds-monitoring-role` | tạo 03/2026, chưa từng dùng | xoá |
| 10 | IAM OIDC provider `token.actions.githubusercontent.com` | GitHub Actions cũ vào acc1 | xoá |
| 11 | Budgets `AAA-Monthly-Total` ($180), `aa-practice-monthly` ($150) | cảnh báo chi phí cũ | Nghiệp chọn: giữ 1 budget nhỏ ($1) để báo nếu còn phát sinh, xoá phần còn lại |
| 12 | Cost Anomaly monitor + subscription | | giữ (miễn phí, báo nếu có chi phí lạ) |
| 13 | IAM user `admin_nghiep` + access key **đang Active** (profile `acc1-legacy-default`) | key tĩnh từ 13/03 | vô hiệu key (deactivate) → xoá profile khỏi `~/.aws`; giữ user nếu Nghiệp còn dùng acc1 cá nhân |
| 14 | Service-linked roles AWS (`AWSServiceRoleFor*`), Organization 1 tài khoản, IAM Identity Center, payment instrument | thuộc tài khoản, không tốn tiền | giữ (tài khoản cá nhân) |

Không thấy trên acc1: secret Secrets Manager (0), KMS key do người tạo (0), SNS topic (0), RDS snapshot (0), EC2 (0), ACM (0),
CloudTrail trail (0), Bedrock provisioned throughput / batch job đang chạy (0).

## Cần Nghiệp quyết

- Duyệt xoá mục 1–10 (đề xuất: duyệt hết; mục 5 tải về trước).
- Mục 11: giữ 1 budget $1 làm chuông báo? (đề xuất: có).
- Mục 13: deactivate access key tĩnh? (đề xuất: có — key tĩnh là nguyên nhân 2 lần ghi nhầm tài khoản, AA-517).
- Giữ tài khoản acc1 cho việc cá nhân hay đóng hẳn? (đề xuất: giữ, chỉ xoá đồ của hệ sinh thái).
