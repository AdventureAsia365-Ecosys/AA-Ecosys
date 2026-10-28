# AA-998 — Gỡ acc1 (tài khoản AWS cá nhân) khỏi hệ sinh thái (S255, 28/10/2026)

Yêu cầu của tech lead (S255): hệ sinh thái chỉ dùng acc2 (hạ tầng) và acc3 (Bedrock); không để tài khoản cá nhân tốn tiền.

## Kết quả

| Bước | Bằng chứng |
|---|---|
| Audit code (chỉ đọc, 6 repo + skill + memory) | `audit-code.md`: 99 tham chiếu (CIS 35, Infra 23, root 23, TripPlanner 10, Booking/Partner gần như sạch) |
| Chi phí acc1 trước khi gỡ | 08/2026 45,15 USD · 09/2026 0,97 USD · 10/2026 (tới 27/10) 0,76 USD — từ tháng 9 toàn bộ là Bedrock gọi dự phòng khi acc3 lỗi; 139 lệnh gọi / 0,69 USD trong 30 ngày (`llm_call_log`) |
| Cắt đường gọi | CIS #1102 (`9d919f0f`, LLM chỉ acc3, Cost Explorer acc2/acc3, admin hiện ID tài khoản) + migration 295 (check 40690011298 / apply 40690255382); TripPlanner #174 (deploy-lambdas 40675128858); Infra #466 (bỏ grant AssumeRole, env fallback, bucket policy; apply 40675584095) |
| Verify sau khi cắt | CIS :889/:455 không còn `BEDROCK_ACCT_FALLBACK`; 2 Lambda TripPlanner 0 biến fallback; DB: 0 catalog có profile acc1, 0 route khác acc3, 0 lệnh gọi acc1 sau deploy |
| Xoá trên acc1 — đợt 1 (tech lead duyệt mọi đề xuất) | `deletion-dry-run.md`, `delete-phase1.log`: Lambda cũ, 3 log group, mọi ECS task definition, 3 role chưa dùng + 2 instance profile, GitHub OIDC provider, bucket `acp-gold` (đã tải về: 11 object), 2 budget cũ → 1 budget 1 USD, access key tĩnh → Inactive |
| Xoá trên acc1 — đợt 2 | Terraform destroy `accounts/acc1-bedrock` (7 tài nguyên: 3 role + 4 policy) + xoá bucket state (11 version) |
| Kiểm kê lại | `reinventory-final.txt`: 0 role ngoài AWS/SSO, 0 OIDC, 0 bucket, 0 Lambda, 0 log group, 0 secret, 0 task definition; budget 1 USD; key tĩnh Inactive |
| Tài liệu / hướng dẫn | `~/.claude/CLAUDE.md`, memory, docs/skills của repo gốc (PR riêng) |

## Còn lại (theo Done-when)

- Cost Explorer acc1 tháng 11/2026 = 0 USD cho dịch vụ hệ sinh thái: kiểm ở phiên đầu tiên của tháng 12/2026.
- Giữ lại có chủ đích trên acc1 (thuộc tài khoản cá nhân, không tốn phí): Organization một tài khoản, IAM Identity Center
  (SSO `pqnghiep-admin`), service-linked role của AWS, phương thức thanh toán, budget cảnh báo 1 USD.
