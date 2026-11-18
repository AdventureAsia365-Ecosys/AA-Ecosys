# S284 — AWS Update Q3/2026 (deck TrueIDC) đối chiếu với hạ tầng thật

Ngày 18/11/2026. Nghiên cứu bằng tài liệu AWS + Pricing API (chỉ đọc), có agent phản biện.

## 1. Có nên chuyển compute từ T3 sang T8i không?

Không. Hệ thống của mình không có gì để chuyển sang T8i. T8i chỉ có ở EC2. ElastiCache và RDS chưa có class T8i: Pricing API trả về 0 sản phẩm cho cache.t8i và db.t8i, và lệnh orderable cho db.t8i.small cũng trả về 0. Resource T3 duy nhất của mình là cache Valkey (cache.t3.micro), nên không chuyển được. EC2 duy nhất là NAT t4g.nano, đã chạy Graviton. Ở us-west-1, T8i đắt hơn T3 khoảng 20%/giờ và đắt hơn T4g khoảng 49%/giờ. "Price-performance tốt hơn tới 30%" nghĩa là được nhiều hiệu năng hơn trên mỗi đô, chứ hóa đơn không giảm. Hóa đơn chỉ giảm khi hạ được size máy. Dev của mình đang rất nhàn: ECS CPU trung bình 3.5–7.1%, RDS 5.3%, Valkey 0.73%. Nên trả lời reseller là "không áp dụng". Cái tiết kiệm thật đến từ việc chuyển sang Graviton/ARM64 và cách đặt capacity, không đến từ thế hệ T mới. Khoản tiết kiệm ít rủi ro làm được ngay là khoảng 11 USD/tháng.

Brief ban đầu sai 2 điểm:
- Chỉ có 3 service ECS chạy x86, không phải 6.
- Không phải cả 8 service đều chạy Spot. Có 4 service đặt FARGATE base=1. Mỗi service chỉ có 1 task (desiredCount 1), nên task đó đang chạy on-demand.

## 2. Bảng resource của mình

Giá on-demand us-west-1, tính 730 giờ/tháng.

| Resource | Hiện tại | Lựa chọn tốt nhất | USD/tháng: hiện tại → sau | Công sức | Khuyến nghị |
|---|---|---|---|---|---|
| ECS: CIS api, CIS worker, Booking api | Fargate X86_64, on-demand | Fargate ARM64 (Graviton) | 51.80 → 41.45 (−10.35) | M: 3 PR (CI build arm64/multi-arch ở 2 repo app + đổi Terraform `cpu_architecture`) | Làm ngay, tiết kiệm. Không thêm dịch vụ trả phí. Đây là PR CI/workflow nên cần agent review trước. |
| ElastiCache aa-cis-dev-cache | cache.t3.micro Valkey 8.2, 1 node | cache.t4g.micro | 12.85 → 12.26 (−0.58) | S: đổi 1 biến Terraform | Làm ngay, tiết kiệm. Gộp vào PR Infra kế tiếp. Cache chỉ có 1 node, không failover, nên sẽ ngắt kết nối ngắn. Chạy lúc không có wave hay job. |
| 4 service base=1 (CIS api, CIS worker, Booking api, CRM api) | 1 task on-demand FARGATE mỗi service | Đặt base=0, chạy hết trên Spot | 60.09 → ~14.9 (ước tính theo comment trong repo; Pricing API không có giá Spot chính thức) | S: Terraform `capacity_provider_strategy` | Cần anh duyệt. Đây là đánh đổi độ ổn định: S276 từng ghi 14 lần 503 liên tiếp sau một lần Spot bị thu hồi. |
| ECR aa-cis-dev-api | 244 image, 62.47 GB, giữ 30 image dev-<sha> | Giữ ít hơn, ví dụ 15 | Trần ~6.25 → thấp hơn (chưa đo; con số này đếm trùng các layer dùng chung) | S: lifecycle policy trong Terraform | Làm ngay, miễn phí, nhưng đo chi phí ECR thật trong Cost Explorer trước. |
| NAT EC2 | t4g.nano arm64 | Giữ nguyên (t8i.nano đắt hơn) | 3.65 → 3.65 (nếu đổi sang t8i.nano: 5.43, tăng 49%) | — | Không áp dụng |
| RDS aa-cis-dev-db | db.t4g.small, PG 15.17 | Giữ nguyên (không có db.t8*) | 31.39 → 31.39 | — | Không áp dụng. 30 ngày qua không bị tính surplus credit. |
| Lambda x86 (dfs-balance-check, tripplanner jobs, assembly, browse) | x86_64 | arm64 | ~0.05 → ~0.04 (giá list) | S–M: đổi packaging sang wheel aarch64 | Để lúc prod, hoặc làm khi sửa packaging lần tới. Free tier có thể không được tính cho acc2 vì acc2 nằm trong org TrueIDC. |
| 5 service ECS còn lại (CIS admin, Booking admin, CRM api, CRM web, TripPlanner web) | Đã chạy ARM64 | — | — | — | Không áp dụng |
| RDS lúc lên prod | — | Class Graviton mới nhất ở region prod: r8g/m8g ở us-west-1, R9g chỉ có ở us-east-1/us-east-2/us-west-2/eu-central-1 | Tham khảo: db.r8g.large ~195.64, db.m8g.large ~140.16 (Single-AZ) | S, chọn lúc thiết kế prod | Để lúc prod |

## 3. Các mục khác trong deck

- **Hanoi Local Zone** (GA 19/06/2026). Chỉ có EC2 C7i/M7i/R7i, ECS on EC2 và ALB. Không có Fargate, RDS, ElastiCache hay NAT Gateway. Máy rẻ nhất khoảng 75 USD/tháng (c7i.large). Để lúc prod, chỉ khi cần latency thấp hoặc giữ dữ liệu tại VN. Việc chọn region cho prod (us-west-1 hay ap-southeast-1) quan trọng hơn Local Zone.
- **Shield Advanced, hạn 29/01/2027.** Không áp dụng. Mình không đăng ký Shield Advanced, chỉ dùng WAF thường.
- **Security Hub network scanning.** Không miễn phí riêng, chỉ đi kèm gói Essentials có tính phí. Con số ~84 USD/tháng chỉ là trần lỏng. Phần ECR bị thổi lên vì đếm cả các manifest con untagged. Đây là dịch vụ trả phí mới, để lúc prod và cần anh đồng ý riêng.
- **S3 chuyển sang IA từ ngày 0.** Không áp dụng. Bucket bronze có khoảng 10.3 GB, tốn khoảng 0.27 USD/tháng, nên tiết kiệm dưới 0.10 USD. Có thể thêm expiration rule cho `db-schema-dump/` (tùy chọn).
- **Claude Fable 5.2.** Giá 8/40 USD mỗi MTok (global), gấp 2 lần Opus 5.5. Phải bật data retention `aws_review` trên acc1. Cần anh duyệt, và chỉ dùng khi có nhu cầu đo được.
- **Claude Mythos 5.2.** Không áp dụng, vì chỉ dành cho tổ chức đã qua chương trình xác minh của Anthropic. Hệ số burndown 2.5x chỉ ảnh hưởng quota, không đổi giá.
- **GPT-6.1 Sol.** Giá 2/10 USD, gấp 20 lần GPT-6 Luna. Chỉ đáng dùng để thay GPT-6 Sol: cùng giá, cache read 0.10 thay vì 0.20. Cần anh duyệt nếu muốn thêm.
- **Kimi K3.1 Pro.** Giá 4/20 USD. Gateway chưa có role nào hợp với nó. Không áp dụng.
- **SageMaker maintenance mode.** acc2 không có endpoint, notebook hay domain nào. Không áp dụng.

## 4. Việc đề xuất (theo mức tiết kiệm và công sức)

1. Trả lời reseller: T3 → T8i không áp dụng cho mình. Miễn phí.
2. Chuyển CIS api, CIS worker và Booking api sang Fargate ARM64: −10.35 USD/tháng. Thứ tự làm: build image multi-arch trước, sau đó mới đổi Terraform. CIS api và worker dùng chung image nên phải đổi cùng lúc. Kiểm bảng job rảnh trước khi deploy. Cần agent review, nhưng không cần anh đồng ý về chi phí.
3. Đổi cache.t3.micro sang cache.t4g.micro: −0.58 USD/tháng. Gộp vào PR Infra kế tiếp, chạy lúc không có wave.
4. Đo chi phí ECR trong Cost Explorer, rồi mới quyết có giảm số image dev-<sha> giữ lại hay không. Tối đa tiết kiệm vài USD/tháng.
5. Lambda x86 → arm64: làm khi sửa packaging lần tới.
6. **Cần anh duyệt (rủi ro độ ổn định, không tăng chi phí):** đưa 4 service base=1 lên Spot. Ước tính tiết kiệm khoảng 45 USD/tháng, nhưng chưa có giá Spot chính thức.
7. **Cần anh nói "có" rõ ràng vì tăng chi phí:** Security Hub Essentials (để lúc prod), Fable 5.2 (gấp 2 Opus 5.5, kèm bật data retention trên acc1), GPT-6.1 Sol (chỉ để thay GPT-6 Sol), Anti-DDoS rule group (20 USD/tháng mỗi web ACL + 0.15 USD/1M request, để lúc prod).

## Nguồn

- https://aws.amazon.com/about-aws/whats-new/2026/09/ec2-t8i-instances-ga/
- https://aws.amazon.com/about-aws/whats-new/2026/11/amazon-aurora-rds-postgresql-mysql-mariadb-r9g-instances/
- https://aws.amazon.com/about-aws/whats-new/2026/06/amazon-rds-postgresql-mysql-mariadb-m9g-instances/
- https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/redis-cluster-vertical-scaling.html
- https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/useconsolidatedbilling-effective.html
- https://aws.amazon.com/lambda/pricing/ ; https://aws.amazon.com/fargate/pricing/
- https://aws.amazon.com/about-aws/whats-new/2026/06/aws-local-zones-hanoi-vietnam/ ; https://aws.amazon.com/about-aws/global-infrastructure/localzones/features/ ; https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cluster-regions-zones.html
- https://aws.amazon.com/blogs/security/aws-shield-advanced-is-embracing-the-aws-waf-anti-ddos-managed-rule-group-what-changes-and-how-to-prepare/
- https://aws.amazon.com/about-aws/whats-new/2026/07/aws-security-hub-network-scanning/ ; https://aws.amazon.com/about-aws/whats-new/2026/11/security-hub-network-scanning-rds/ ; https://aws.amazon.com/security-hub/pricing/
- https://aws.amazon.com/about-aws/whats-new/2026/07/s3-removes-30-day-transitions-standard-ia-one-zone-ia/
- https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-fable-5-2.html ; https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-mythos-5-2.html ; https://docs.aws.amazon.com/bedrock/latest/userguide/quotas-token-burndown.html ; https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-6-1-sol.html ; https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-moonshot-ai-kimi-k3-1-highspeed.html
- AWS CLI live, chỉ đọc, ngày 18/11/2026 trên acc2: `aws pricing get-products` (AmazonEC2, AmazonElastiCache, AmazonRDS, AmazonECS, AWSLambda, AmazonBedrockFoundationModels, AWSSecurityHub, awswaf, AmazonS3, AmazonECR); `ec2 describe-instance-types` / `describe-instance-type-offerings` / `describe-instances`; `rds describe-orderable-db-instance-options` / `describe-db-instances`; `elasticache describe-replication-groups` / `list-allowed-node-type-modifications`; `ecs describe-services` / `describe-task-definition` / `describe-tasks`; `ecr describe-images` / `get-lifecycle-policy`; `lambda list-functions`; `cloudwatch get-metric-statistics` (30 ngày); `shield` / `wafv2` / `securityhub` / `sagemaker`.
- Repo: infra/AA-CIS-Infra/modules/environment/tripplanner_web.tf (ước tính giá Spot ARM), audit S276 (docs/audits/2026-11-10-S276-aa741-phase3, mục 21).
- Script truy vấn, chỉ đọc:
  - /tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/5ede7452-c93e-4902-9115-13a9ae9ad89c/scratchpad/q.sh
  - /tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/5ede7452-c93e-4902-9115-13a9ae9ad89c/scratchpad/e.sh
  - /tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/5ede7452-c93e-4902-9115-13a9ae9ad89c/scratchpad/b.sh
  - /tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/5ede7452-c93e-4902-9115-13a9ae9ad89c/scratchpad/c.sh
