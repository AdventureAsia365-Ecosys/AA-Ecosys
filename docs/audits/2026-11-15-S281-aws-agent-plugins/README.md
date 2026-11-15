# AWS Agent Plugins (plugin AWS cho AI agent) — có ích gì cho AA, và đã quyết định gì

*15/11/2026, cuối phiên S281 (Claude Code), viết cho tech lead. Nguồn: một bài chia sẻ trên mạng xã hội về plugin AWS
cho Claude Code. Cách làm: 3 agent (nghiên cứu nguồn gốc của AWS, rà repo AA, phản biện), rồi điều phối tự kiểm các điểm
then chốt và thử thật. Tech lead đồng ý đề xuất cùng ngày.*

Tệp kèm:

- `plugin-research.md`: plugin thật sự chứa gì (skills, MCP server, hook), có link nguồn gốc.
- `assessment.md`: đánh giá từng thành phần cho AA, rủi ro, kế hoạch, các điểm bài viết sai.
- `knowledge_probe.py`: script gọi thẳng AWS Knowledge MCP (JSON-RPC) để kiểm câu trả lời.

## 1. Kết luận

Không cài plugin AWS nào. Chỉ thêm AWS Knowledge MCP (từ xa, chỉ đọc, miễn phí). Không dùng Pricing MCP (tra giá bằng
CLI). Không dùng MCP gọi AWS API.

Lý do chính:

1. AA chỉ dùng Terraform (153 file `.tf`, 0 file CloudFormation / CDK / SAM). Phần lớn giá trị bài viết khen (cfn-lint,
   cfn-guard, đọc event stack, SAM) không áp dụng.
2. Mọi guard AWS của AA (shell guard, guard subagent, PII guard) chỉ đọc lệnh Bash. Hook cho công cụ `mcp__*` bỏ qua
   phiên chính và chỉ chặn ghi GitHub / Linear / Notion / Vercel cho subagent. Một MCP gọi AWS API sẽ đi vòng qua tất cả.
3. Plugin không truyền profile, region hay chế độ chỉ đọc; region mặc định us-east-1; `aws-serverless` bật sẵn
   `--allow-write`. Với nhiều account (acc1 / acc2 / acc3 / acc4), rủi ro gọi nhầm account là thật.
4. `aws-core` kèm hook chặn `secretsmanager get-secret-value`, làm vỡ các runbook đang dùng lệnh này.

## 2. Bài viết sai hoặc chưa kiểm được

- `aws-core` không ở repo `awslabs/agent-plugins` mà ở `aws/agent-toolkit-for-aws` (repo awslabs đã ghi là bị thay thế).
- Không plugin nào tự chạy cfn-lint / cfn-guard bằng hook; chỉ có `sam validate` cho `template.yaml`, và tự bỏ qua nếu
  máy không có SAM CLI.
- "Mặc định least privilege" chỉ là lời văn trong skill, không có kiểm tra nào.
- `databases-on-aws` chỉ có Aurora DSQL, không có RDS PostgreSQL.

Chi tiết và link: `assessment.md` mục D, `plugin-research.md`.

## 3. Đã làm sau khi tech lead đồng ý

| Bước | Kết quả |
|---|---|
| Thêm AWS Knowledge MCP mức user (`claude mcp add --transport http aws-knowledge https://knowledge-mcp.global.api.aws --scope user`) | Connected. 5 công cụ: `aws___search_documentation`, `aws___read_documentation`, `aws___list_regions`, `aws___get_regional_availability`, `aws___retrieve_skill`. Không chạy process local, không cần credential. |
| Kiểm bằng 3 bài học đã biết trong `skill/aa-lessons/lessons.md` | WAF xoá ACL: đúng (bỏ liên kết trước, với CloudFront dùng `UpdateDistribution` với ACL ID rỗng), có link tài liệu. Ký tự cho phép trong description web ACL: tìm đúng trang nhưng pattern bị hỏng khi render (mất dấu ngoặc), nên guard test và lessons vẫn là nguồn chính. `ListInstanceProfilesForRole` khi xoá role: chỉ ra trang gần đúng (instance profile), không nói thẳng quyền cần. Kết luận: giữ, dùng để tra tài liệu và giới hạn API, không thay lessons. |
| Thử Pricing MCP | Dừng. boto3 trong process MCP không dùng chung cache STS của CLI nên hỏi mã MFA và lỗi `EOFError`. Sửa bằng cách bơm credential admin 12 h vào process chạy lâu, hoặc tạo role không MFA, đều làm yếu bảo mật. |
| Tra giá bằng CLI thay thế | `aws pricing get-products --region us-east-1` chạy được với phiên MFA hiện có, vẫn qua hook Bash. Ví dụ RDS `db.t4g.small` Single-AZ PostgreSQL ở us-west-1: 0,043 USD/giờ (khoảng 31 USD/tháng). Số từ Price List API là giá niêm yết, ghi là "ước tính". |

## 4. Việc đề xuất tiếp (chưa làm)

1. **tflint + checkov (hoặc trivy) trong CI của AA-CIS-Infra**, miễn phí, kết quả cố định. Đây mới là chỗ mang lại lợi
   ích "IAM bớt rộng, template đúng" mà bài viết hướng tới. Bản rà đếm được 3 chỗ `Action="*"` và 78 chỗ resource `"*"`
   (mới đếm, chưa xem từng chỗ). Thay đổi CI thuộc loại rủi ro: cần review độc lập trước khi merge. Đặt vào S282.
2. **Nếu sau này cần MCP AWS có credential:** role chỉ đọc riêng, IAM Deny ghi với điều kiện `aws:ViaAWSMCPService`, chạy
   `--read-only --profile <ro> --region us-west-1`, và hook PreToolUse chặn công cụ `mcp__*aws*` cho cả subagent lẫn phiên
   chính. Chưa làm, chưa cần.
3. Tìm hiểu `terraform-mcp-server` của HashiCorp (tra tài liệu registry provider). Chưa kiểm.
