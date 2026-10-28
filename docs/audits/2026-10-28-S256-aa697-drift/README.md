# AA-697 — đối chiếu sơ đồ Infra với Terraform thật (S256, 28/10/2026)

Mục "Done when" còn lại của AA-697: *TerraVision cross-check shows no drift vs the Infra diagram*. Bản này đối chiếu sơ đồ
[`infra.py`](../../architecture/diagrams/infra.py) và [`ecosystem.py`](../../architecture/diagrams/ecosystem.py) (kèm các
nhãn hạ tầng trong `cis.py`, `booking.py`, `partner.py`) với **state Terraform đang chạy** của root `accounts/aa365`, sửa
sơ đồ ở mọi chỗ lệch thật, rồi render lại SVG.

## Cách làm

1. **Nguồn sự thật = state live, không phải đọc file `.tf`.** Trên `origin/main` của AA-CIS-Infra (`2403ed7`), chạy
   `terraform plan -lock=false -refresh=false` (chỉ đọc, không giữ khoá state, không gọi refresh) → **"No changes. Your
   infrastructure matches the configuration."** Nghĩa là code trên `main` và state khớp nhau, nên kê tài nguyên từ plan là
   kê đúng thứ đang tồn tại (813 tài nguyên, 129 loại).
2. **TerraVision 0.56.0** (venv riêng trong `.tmp-session/`, Graphviz `dot` giải nén cục bộ không cần sudo): `terravision
   graphdata --planfile <plan JSON> --graphfile <terraform graph -plan>` chạy được, không gọi thêm lệnh Terraform nào. Danh
   sách dịch vụ nó vẽ được (75 loại) dùng làm lưới kiểm thứ hai.
   - Hạn chế: TerraVision **bỏ sót** vài loại khi vẽ (không có `aws_db_instance`, `aws_elasticache_replication_group`,
     `aws_sqs_queue`, `aws_instance` trong danh sách dịch vụ của nó), nên bảng dưới lấy từ plan JSON, TerraVision chỉ để
     đối chiếu. Ảnh TerraVision không đưa vào repo (nhãn có tên bucket kèm số tài khoản).
3. Root `accounts/acc3-bedrock` đọc từ file `.tf` (không có quyền state acc3 trong lane này): invoker role, Bedrock Batch
   service role, Cost Explorer reader role, budget + anomaly + SNS — khớp sơ đồ, không lệch.

## Bảng lệch (sơ đồ trước S256 ↔ live)

| # | Thành phần | Sơ đồ cũ | Live (state aa365) | Loại | Đã sửa |
|---|---|---|---|---|---|
| 1 | NAT | "NAT gateway" (icon NAT Gateway) | **NAT instance** EC2 `t4g.nano` + Elastic IP (`module.vpc.aws_instance.nat`), không có `aws_nat_gateway` | Sai | `infra.py`: icon EC2, nhãn "NAT instance" |
| 2 | WAF | WAF `aa-cis-dev-waf` gắn REST API (`infra.py`, `ecosystem.py`, `cis.py`) | Web ACL `aa-cis-dev-waf` gắn **ALB** (`module.waf…association.alb`); không gắn stage REST nào (`waf_protect_rest_api_stages` tắt). Web ACL thứ hai `aa-identity-dev-pools` gắn **3 user pool Cognito** | Sai | cả 3 view: WAF chuyển sang ALB; `infra.py` thêm WAF của Cognito |
| 3 | S3 "ops docs" + KMS "ops docs CMK" | `infra.py`, `ecosystem.py`, `booking.py` vẽ bucket ops-docs + CMK | **Không tồn tại.** Không có bucket `aa-booking-dev-ops-docs-*`, không CMK nào cho nó; task Booking không có `OPS_DOCS_BUCKET` | Sai (vẽ theo thiết kế AA-682, hạ tầng chưa làm) | `infra.py`/`ecosystem.py`: bỏ; `booking.py`: giữ nút, ghi "not provisioned yet" + "uploads answer 503" |
| 4 | KMS | 1 CMK (ops docs), cạnh Booking → KMS | **4 CMK**: CloudTrail, CRM data, CRM ingest, CRM seal. Booking không dùng KMS | Sai | `infra.py`: nhãn 4 CMK, cạnh CRM → KMS; `partner.py`: thêm S3 crm + 3 CMK |
| 5 | S3 | "bronze · artifacts · media · ops docs" | **15 bucket**: CIS bronze/silver/gold, ACP bronze/silver/gold, CRM documents/ingest/audit-c/audit-g (SSE-KMS), Booking supply media, TripPlanner artifacts, CloudTrail logs, ALB diag logs, e2e mail | Thiếu | nhãn mới (`infra.py`, `ecosystem.py`) |
| 6 | CloudFront | 3 distribution partner · agency · client | **4**: thêm `photos_cdn` (ảnh CIS, origin S3 bronze `photos/` qua OAC) | Thiếu | `infra.py`: nhãn + cạnh "OAC" → S3; `ecosystem.py`: "+ photos" |
| 7 | Lambda | "TripPlanner + ops probe" | **8**: TripPlanner browse + assembly, DFS balance check (trong VPC); 4 Cognito trigger (pre-sign-up, pre-token × workforce/external) + RDS snapshot expiry (ngoài VPC) | Thiếu | `infra.py`: tách 2 nút trong / ngoài VPC, cạnh Cognito "triggers" |
| 8 | Bedrock trên acc2 | không có trong `infra.py` | Guardrail `aa-crm-dev-scrub` (Terraform) + embeddings (IAM, không có tài nguyên riêng) | Thiếu | `infra.py`: nút "Bedrock (acc2)"; `ecosystem.py`: "CRM guardrail" |
| 9 | EFS | không có | `aa-cis-dev-efs` + 2 mount target, **không task definition nào mount** | Thiếu (và có thể là tài nguyên thừa) | `infra.py`: nút "EFS (no task mounts it)" — xem việc tiếp theo |
| 10 | Bảo mật / sự kiện | không có | CloudTrail (KMS) + IAM Access Analyzer; 14 EventBridge rule (security, identity, CRM KMS) → SNS alerts; ACP bus + DLQ FIFO (không rule, AA-989) | Thiếu | `infra.py`: nút CloudTrail, EventBridge, cạnh → SNS |
| 11 | Scheduler | "aa-cis-dev-acp" | cùng group, **5 schedule** ngày (booking uptime, DFS balance, photo sync, RDS snapshot expiry, retention) | Nhãn | `infra.py`: "5 daily schedules" |
| 12 | ECS | 6 service + task DB Migrate | khớp (CIS api/worker, Booking api, CRM api/web/portal; Fargate + Fargate Spot) | Khớp | nhãn cluster "(Fargate + Spot)", Booking "+ booking.job" |
| 13 | Edge còn lại | Route 53 public + private, REST CIS + Booking, HTTP TripPlanner, NLB → ALB, VPC link / VPC origin | khớp | Khớp | — |
| 14 | RDS, Valkey, ECR, Secrets, Cognito, SES, SNS, Budgets, OIDC | — | RDS PG 15 deletion protection ✓; Valkey 8 TLS ✓; ECR 5 repo ✓; 17 secret ✓; 4 user pool ✓; SES identity + receipt rule ✓; SNS alerts + SES feedback ✓; 7 budget + anomaly ✓; GitHub OIDC ✓ | Khớp | nhãn chi tiết hơn (Valkey 8, 5 repo, inbound test mail, SES feedback) |
| 15 | GuardDuty | không vẽ | `count = 0` (`guardduty_enabled = false`, chờ duyệt chi phí) | Khớp | — |

Sau khi sửa: mọi nhóm dịch vụ trong state aa365 (trừ phần phụ trợ: IAM policy, SG, route, log group, alarm, record DNS,
ACM) đều có nút trên sơ đồ Infra; không nút nào vẽ thứ không tồn tại (bucket ops-docs ở view Booking ghi rõ "not
provisioned yet"). `render.py --check`: 6/6 SVG ok.

## Việc tiếp theo (không làm trong lane này)

- **Bucket ops-docs của AA-Booking chưa có.** `CONTEXT.md` của AA-Booking nói AA-CIS-Infra tạo bucket
  `aa-booking-<env>-ops-docs-<account>` + CMK + quyền task role và đặt `OPS_DOCS_BUCKET`; Terraform chưa có gì. Hệ quả: tải
  lên / tải về chứng từ vận hành (AA-682 S1) trả 503 `ops_storage_unavailable` trên Dev. Cần một PR Infra (S3 + 1 CMK
  ~1 USD/tháng → hỏi duyệt chi phí trước theo luật dịch vụ trả phí).
- **EFS `aa-cis-dev-efs` không ai mount.** Ứng viên xoá (tiền gần 0 khi rỗng, nhưng là tài nguyên mồ côi + 2 mount target
  trong SG). Cần kiểm dữ liệu bên trong trước theo quy trình DRY RUN.
- **Prose lệch:** CONTEXT.md của AA-CIS-Infra (§Edge) đã nói đúng WAF bám ALB và stage REST chỉ khi bật biến; tài liệu
  `ecosystem-architecture.md` không nhắc WAF trên REST nên không phải sửa.
