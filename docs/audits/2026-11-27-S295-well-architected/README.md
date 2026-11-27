# Well-Architected self-review — S295 baseline (27/11/2026)

Người đọc: tech lead. Tác nhân: Claude Code. Bản tóm tắt công khai được (repo gốc là public): không có tên tài nguyên,
account ID, ARN hay chi tiết khai thác. Bản đầy đủ (6 file theo trụ + tổng hợp) nằm trong kho bằng chứng ISMS riêng:
`isms/evidence/audits/2026-Q4/2026-11-27-S295-well-architected/` (S3 private, acc2).

## Là gì

- Lần **đầu tiên** đi đủ 6 trụ của AWS Well-Architected Framework (OPS, SEC, REL, PERF, COST, SUS), cộng **SaaS Lens** và
  **Generative AI Lens** ở phần liên quan. Trước đó chỉ có audit S282 dùng vài câu WA làm thước so sánh.
- Là **tự review** (self-review), không phải review của AWS hay partner. Mỗi trụ một người review + một lượt kiểm đối kháng;
  bằng chứng là code trong repo và AWS đọc live (chỉ describe/list/get).
- Môi trường: Dev (pilot chạy trên Dev), lean có chủ đích; Multi-AZ, NAT gateway, backup cross-account để dành cho prod.

## Bảng điểm

| Trụ | HRI | MRI | Nhận định |
|---|---|---|---|
| Operational Excellence | 2 | 8 | CI/CD, IaC, drift đêm, docs-as-code tốt; rủi ro ở kênh cảnh báo và một người vận hành |
| Security | 5 | 14 | Nền kỹ thuật tốt; rủi ro ở danh tính admin, quyền rộng, phát hiện mỏng, phục hồi khi bị chiếm |
| Reliability | 1 | 10 | Phần mềm tự chịu lỗi tốt; backup chưa tách khỏi quyền admin |
| Performance Efficiency | 0 | 6 | SLO DB, review query hằng tuần; còn cache edge CRM, load test |
| Cost Optimization | 0 | 4 | FinOps tốt; phân bổ chi phí cần bật lại sau Billing Transfer, trần phía vendor AI |
| Sustainability | 0 | 4 | Graviton, Fargate, retention log; dữ liệu giữ lâu, chưa có số đo |
| **Tổng** | **8** | **46** | Không có gì chặn pilot về kỹ thuật; 8 HRI sửa được trước dữ liệu pilot thật, gần như 0 USD |

Kết luận: rủi ro cao nằm ở **con người và quyền**, không ở kiến trúc ứng dụng.

## Theo dõi

| Việc | Issue |
|---|---|
| Kênh cảnh báo thứ hai, người trực thứ hai, drill runbook, tabletop | AA-1110 |
| MFA admin, danh tính E2E | AA-1111, AA-1054, AA-1158 |
| Khoá state Terraform, thu hẹp quyền, trần vendor AI | AA-1182 |
| Phân bổ chi phí và anomaly sau 01/12; SCP/RCP | AA-1004 |
| Backup tách quyền + Vault Lock, GuardDuty, quét thử Security Hub / Inspector / Macie | AA-873 |
| Sweep 0 USD (edge, egress, EBS encryption, Access Analyzer CI, Health events, NAT patch, cache CRM) | AA-1185 |
| Gate go-live (bảo trì RDS, chia trần LLM pilot, RTO/RPO nội bộ, load test) | AA-1117 |
| Tự rollback API khi smoke sau deploy đỏ | AA-1193 |
| Diễn tập failover LLM + sổ quota Bedrock | AA-1194 |
| Nguồn traffic liên AZ | AA-1195 |
| Ghi review vào AWS Well-Architected Tool (milestone "S295 baseline") | AA-1166 |
| Review lại hằng năm (27/11/2027, hoặc trước prod) | AA-1184 (lịch vận hành) |
