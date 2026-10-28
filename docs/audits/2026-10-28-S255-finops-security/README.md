---
id: FIN-03-2026-10-28-s255
title: "FinOps refresh, security baseline quote and Cost Operations slices (S255)"
description: "acc2 runs at ~8.7 USD/day (~260 USD/month from November), acc3 LLM spend 242 USD for October; AA-873 baseline quoted at ~16-21 USD/month (GuardDuty dominates); five Cost Operations slices for AA-665."
type: report
status: draft
owner: nghiep
audience: [owner, engineer, agent]
applies_to: [ecosystem, aa-cis-infra, aa-cis]
last_reviewed: 2026-10-28
related: [AA-896, AA-873, AA-665, AA-828, AA-884, FIN-02-2026-10-prelim]
---

# FinOps (AA-896), nền phát hiện bảo mật (AA-873) và trang Cost Operations (AA-665) — S255

- Phiên S255, 28/10/2026 khoảng 06:00 UTC. Tác nhân: Claude Code (lane advisory, **chỉ đọc**). Không apply, không tạo
  tài nguyên, không đổi cấu hình.
- Báo cáo nối tiếp bản sơ bộ S248 ([`../2026-10-23-S248-cost-report/README.md`](../2026-10-23-S248-cost-report/README.md),
  số tới 22/10). Ở đây: số tới **27/10**, các bước nhảy mới sau 22/10, và hai phần mới (AA-873, AA-665).
- Dữ liệu thô: [`data/`](data/) (JSON Cost Explorer, đã bỏ ResponseMetadata, không có account ID). Lệnh:
  [`scripts/fetch_ce.md`](scripts/fetch_ce.md). Script đọc DB cho đơn giá: [`scripts/unit_costs_readonly.py`](scripts/unit_costs_readonly.py)
  (chưa chạy — cần ECS exec, bước của orchestrator).
- Bản nháp Terraform (chưa nằm trong repo Infra, chỉ `terraform fmt`): [`tf/`](tf/).
- **Chi phí của báo cáo này:** 13 request Cost Explorer × 0,01 USD = **0,13 USD** (acc2 9, acc3 4). Budgets, Pricing
  API, describe/list và 1 ngày log CloudTrail (18 MB, cùng region) = 0 USD.
- MFA: phiên `aa365-admin` hết hạn **13:35 UTC (20:35 giờ VN) 28/10**.

## 1. Tóm tắt (5 dòng)

1. **acc2 (hạ tầng)**: tháng 8 = 140,22, tháng 9 = 134,96, tháng 10 (01–27) = **176,04 USD**; AWS dự báo cả tháng 10 là
   **209,21** (budget 250). Nhưng nhịp mấy ngày cuối là **8,1–9,0 USD/ngày** → **tháng 11 khoảng 255–265 USD, vượt budget 250**.
2. Nhịp tăng sau 22/10 (S248 đo 6,24 USD/ngày) đến từ dịch vụ mới luôn chạy: CRM api/web/portal (23–26/10), WAF cho Cognito
   (25/10), 50 secret (từ ~11 hồi tháng 9), 93 alarm; không phải sự cố.
3. **acc3 (LLM)**: tháng 8 = 20,72, tháng 9 = 51,43, tháng 10 (01–27) = **242,13 USD** (budget 250, AWS dự báo **310,41**).
   Các ngày đỉnh trùng các wave: 08/10 34,27 (Haiku 4.5), 24/10 36,09 và 25/10 28,31 (Sonnet 5.5 writer v2).
4. Cost Anomaly Detection: acc2 đã có (monitor dịch vụ + IMMEDIATE ≥ 5 USD → topic alerts). **Monitor theo tag `App` không tạo
   được** trên account thành viên (chỉ management account làm được) → thay bằng budget per-App có FORECASTED. acc3 mới có email
   DAILY → đề xuất thêm IMMEDIATE qua SNS ([`tf/acc3_cost_anomaly_immediate.tf`](tf/acc3_cost_anomaly_immediate.tf)).
5. AA-873: acc2 **chưa có** GuardDuty, Access Analyzer, BPA cấp account; CloudTrail 1 region, không KMS, bucket không versioning.
   Báo giá cả gói **~16–21 USD/tháng**, gần như toàn bộ là GuardDuty; BPA, Access Analyzer (external), cảnh báo EventBridge = 0 USD.

## 2. Tổng theo account (USD, Unblended)

| Account | Tháng 8 | Tháng 9 | Tháng 10 (01–27) | USD/ngày T9 → T10 | Dự báo T10 (AWS) | Nhịp 20–27/10 → tháng 11 |
|---|---:|---:|---:|---|---:|---:|
| acc2 — hạ tầng | 140,22 | 134,96 | 176,04 | 4,50 → 6,52 | 209,21 | **~255–265** |
| acc3 — LLM chính | 20,72 (+1,68 thuế) | 51,43 | 242,13 | 1,71 → 8,97 | 310,41 | tuỳ wave (8 ngày cuối 14,2/ngày) |
| acc1 — LLM dự phòng | (S248: 45,15) | 0,97 | ~0,1 | — | — | ≈ 0 (không đọc lại) |
| **Cộng acc2 + acc3** | 160,94 | 186,39 | **418,17** | | **~520** | |

- **NetUnblended = Unblended** trên cả hai account: không có dòng Credit/Refund. acc3 chỉ có RECORD_TYPE `Usage` (và `Tax`
  tháng 8) → credit AWS Lift **không hiện** trong Cost Explorer của acc3 (giống S248 F1; vẫn chờ anh xem hoá đơn eCloudvalley).
- `App` tag có số từ **15/10** (CE theo ngày: 15/10 là ngày đầu có `cis`/`shared`/`booking`), trước đó toàn bộ là untagged.

## 3. acc2 theo dịch vụ — giải thích từng bước nhảy

| Dịch vụ | T8 | T9 | T10 (01–27) | Thay đổi /ngày T9→T10 | Nguyên nhân (đã kiểm live) |
|---|---:|---:|---:|---:|---|
| ECS (Fargate) | 21,54 | 21,13 | **45,11** | +137 % | vCPU-giờ 360 → 694: `aa-cis-dev-worker` tách riêng từ 05/10 (0,5 vCPU/1 GB ≈ 21 USD/tháng), `aa-booking-dev-api` 14/10 (0,25/0,5 ≈ 10,5), CRM `api`/`web` 23–24/10 và `portal` 26/10 (ARM 0,25/0,5 ≈ 8 mỗi cái). Thêm DataTransfer-Regional của ECS +3,17 |
| Elastic Load Balancing | 37,61 | 36,41 | 32,89 | ≈ 0 | ALB + NLB (VPC link), không đổi; giảm chỉ vì tháng 10 mới 27 ngày |
| RDS | 20,82 | 20,39 | **25,22** | +37 % | db.t3.micro → **db.t4g.small** khoảng 15/10 (≈ 17 → ≈ 31 USD/tháng); backup +0,91 |
| CloudWatch | 6,92 | 7,86 | **15,16** | +114 % | **93 alarm** (AlarmMonitorUsage 39 alarm-tháng tính tới 27/10), custom metric 20 metric-tháng (AA/RDS 14, AA/Jobs/*, AA/Identity…), log ingest/scan |
| ElastiCache | 16,37 | 15,84 | 14,08 | ≈ 0 | 1 node cache.t3.micro (CIS) |
| VPC (IPv4 public) | 11,17 | 10,81 | 9,72 | ≈ 0 | 3 EIP + IP public của ALB/NLB |
| WAF | 9,37 | 9,46 | 9,45 | +11 % | thêm web ACL trên 3 user pool Cognito (`identity`, từ 25/10 ≈ 10 USD/tháng) |
| Secrets Manager | 3,61 | 4,42 | **9,01** | +127 % | **50 secret** (0,40 USD/secret/tháng = 20 USD/tháng). 40 cái tạo trong tháng 10: tài khoản e2e tenant/CRM (13), Sentry DSN (5), tách login DB (3), CRM (6), Cognito BFF/HMAC (3)… |
| EC2-Other | 3,21 | 3,44 | 6,06 | +96 % | DataTransfer-Regional (giữa AZ) +3,04 — xem F-3 |
| EC2 compute | 3,72 | 3,98 | 3,57 | ≈ 0 | NAT instance t4g.nano |
| API Gateway | 0,12 | 0,38 | 2,15 | mới | REST API Booking + CIS, 282k request (0,99 USD), data out 1,13 USD |
| Bedrock (trên acc2) | 5,10 | 0,00 | 0,38 | — | T8: còn gọi trên acc2 trước khi chuyển sang satellite; T10: Bedrock Guardrails của CRM (0,24 USD tag `crm`, đúng thiết kế) + Cohere Embed 4 0,14 — xem F-6 |
| KMS / Cognito / Route 53 / CloudFront / S3 / ECR / CE | 0,65 | 0,78 | 3,21 | mới | 3 key CRM, token M2M, 2 hosted zone, edge CRM, request S3, ảnh, CE API (52 request) |
| **Cộng** | **140,22** | **134,96** | **176,04** | | |

- **T8 → T9 (−5,26):** Bedrock rời acc2 (−4,52 Claude, −0,58 Palmyra) sang mô hình satellite; tháng 9 ít hơn tháng 8 một ngày
  (các dịch vụ tính theo giờ giảm ~3 %); CloudWatch +0,94 và Secrets +0,81 bù lại một phần.
- **T9 → T10 (+41,08 tới 27/10, dự báo +74):** gần hết là ECS mới (+24), RDS lên đời (+4,8), CloudWatch (+7,3), Secrets (+4,6),
  truyền dữ liệu giữa AZ (+6,2). Đây là **mức nền mới**, không tự giảm.

## 4. acc2 theo `App` tag và budget

Nhịp 20–27/10 (8 ngày; CRM và identity lấy 3 ngày cuối vì mới chạy đủ), × 30,4 ngày:

| App | USD/ngày | ≈ USD/tháng | Budget hiện tại (actual T10) | Dịch vụ chính |
|---|---:|---:|---|---|
| shared | 3,30 | **~100** | 100 (40,54) → **FORECASTED 100 % sẽ báo từ tháng 11** | RDS 1,21/ngày, ELB 1,21, WAF 0,33, EC2-Other 0,30 |
| cis | 2,17 | ~66 | 90 (26,99) | ECS 1,47, ElastiCache 0,50, Secrets 0,09 |
| untagged | 1,64 | ~50 | chỉ nằm trong budget tổng | CloudWatch 0,79, IPv4 0,36, Secrets 0,26, ECS 0,14 |
| crm | 0,75 | ~23 | 25 (3,30) → sát | ECS (3 service ARM), Secrets, KMS, Bedrock |
| booking | 0,36 | ~11 | 25 (4,56) | ECS 0,34 |
| identity | 0,33 | ~10 | **không có budget** (giá trị tag ngoài danh sách) | WAF 0,11+, Secrets |
| tripplanner | 0,05 | ~1,5 | 10 (0,58) | Secrets |
| **Cộng** | **~8,6** | **~261** | tổng **250** (176,04; dự báo T10 209,21) | |

Budget tổng `aa-cis-dev-monthly-total` **không có thông báo FORECASTED** (chỉ ACTUAL 80 %/100 %), nên tháng 11 sẽ chỉ báo
khi đã vượt. Đề xuất D1 (mục 9) và bản nháp [`tf/acc2_finops_budgets.tf`](tf/acc2_finops_budgets.tf).

## 5. acc3 theo model (USD)

| Model | T8 | T9 | T10 (01–27) |
|---|---:|---:|---:|
| Claude Haiku 4.5 | 2,49 | 18,27 | **104,12** |
| Claude Sonnet 5.5 | 0 | 0 | **55,49** (từ 23/10, S1 writer v2) |
| Claude Sonnet 4.6 | 18,23 | 33,05 | 52,48 |
| OpenAI GPT-5.6 Luna | 0 | 0,05 | 16,90 |
| OpenAI GPT-6 Luna | 0 | 0 | 11,84 |
| Khác (Opus 5.5, Sonnet 5, Haiku 5.5, CE) | 0 | 0,06 | 1,30 |
| **Cộng (Usage)** | **20,72** | **51,43** | **242,13** |

Ngày cao nhất tháng 10: 24/10 **36,09** (Sonnet 5.5 29,75), 08/10 **34,27** (Haiku 4.5 28,94), 25/10 28,31, 10/10 22,83,
26/10 22,26 (Haiku 11,70). 17–19/10 = 0 (không chạy wave). Nghĩa là chi LLM **đi theo wave**, không theo nền: tháng có rerun cả
catalogue sẽ ~250–300 USD, tháng không rerun ~50–80 USD. Budget acc3 250 USD đã chạm 80 % (actual 242,13) — theo memory
`acc3-budget-is-a-warning` đây là cảnh báo, không phải cổng chặn.

**Đơn giá (unit cost)** — chưa chốt: cần `scripts/unit_costs_readonly.py` (LLM theo tháng × provider × account và theo stage,
DFS, Jev, số tour cập nhật / publish theo tháng). Tính: USD LLM/tour cập nhật = LLM tháng ÷ `tours_updated`; USD hạ tầng/tour
sống = acc2 tháng ÷ tour `master_status` đang sống. Đơn giá Booking (USD/booking) **chưa có nghĩa**: `booking.trip_cases`
mới ~10 dòng thử, và login `cis_app` không đọc được schema `booking`.

## 6. Cost Anomaly Detection — hiện trạng và đề xuất (AA-896)

| Account | Monitor | Subscription | Ghi chú |
|---|---|---|---|
| acc2 | `Default-Services-Monitor` (DIMENSIONAL/SERVICE, Terraform quản lý từ 19/10, 27 dịch vụ đang theo dõi, đánh giá lần cuối 28/10 05:06Z) | `aa-cis-dev-cost-anomaly-to-alerts` IMMEDIATE ≥ 5 USD → SNS alerts; `Default-Services-Subscription` DAILY ≥ 100 USD **và** ≥ 40 % | Đủ cho phần dịch vụ |
| acc3 | `Default-Services-Monitor` | `aa3-cost-anomaly-daily` DAILY ≥ 10 USD (email); `Default-Services-Subscription` DAILY | Chậm tới ~24 h trong khi một ngày wave là 30+ USD |

- **Monitor theo tag `App`:** hướng dẫn AWS (getting-started-ad, đọc 28/10): *"Cost monitors for linked accounts, cost allocation
  tags, and cost categories can only be created in the management account"*. acc2 là account thành viên của payer TrueIDC →
  **không tạo được**; khối Terraform để tham khảo nằm (comment) trong [`tf/acc2_finops_budgets.tf`](tf/acc2_finops_budgets.tf).
  Thay thế đã có: budget per-App (ACTUAL 80 % + FORECASTED 100 %) + monitor dịch vụ IMMEDIATE ≥ 5 USD.
- **Việc còn lại của AA-896** (theo Done-when của issue): `docs/ops/finops.md`, script `docs/ops/cost/YYYY-MM.md`, báo cáo
  `2026-10.md` chạy **sau 01/11** (tháng 10 chốt). Monitor dịch vụ đã live (F7 của S248) nên tiêu chí "Anomaly monitor live" đã đạt.

## 7. AA-873 — hiện trạng bảo mật account (acc2, us-west-1, đọc 28/10) và báo giá

| Hạng mục | Hiện trạng | Đề xuất | USD/tháng |
|---|---|---|---:|
| GuardDuty | **0 detector** | Foundational + RDS login (đúng phạm vi issue); S3 data events tuỳ chọn; Runtime/EBS/EKS/Lambda tắt | **~15–20** |
| IAM Access Analyzer | **0 analyzer** | 1 analyzer `ACCOUNT` (external access) + rule EventBridge khi có finding ACTIVE. Không bật "unused access" (0,20 USD/role/tháng) | **0** |
| S3 Block Public Access (account) | **chưa đặt** (NoSuchPublicAccessBlockConfiguration) | Bật cả 4 cờ. **An toàn:** cả 16 bucket đã BPA 4/4 ở mức bucket, không bucket nào có policy public | **0** |
| CloudTrail | `aa-cis-dev-trail`: 1 region, global events có, log file validation có, **không KMS**, không CloudWatch Logs, chỉ management events | Multi-region (bản copy đầu tiên của management event miễn phí) + KMS CMK | **~1,05** |
| Cảnh báo (root, IAM, SG, trail) | Chưa có (chỉ có rule riêng cho Cognito, break-glass, secret bị từ chối, KMS CRM) | **EventBridge rule → topic alerts** (cùng mẫu `identity_alerts.tf`), không dùng CloudWatch metric filter (~5 USD/tháng). Sự kiện IAM/root chỉ về EventBridge ở **us-east-1** → 1 rule forward sang bus us-west-1 | **0** |
| Bucket log CloudTrail | Versioning **tắt**, Object Lock **tắt**, SSE-S3, lifecycle "Deep Archive sau 30 ngày" **không bao giờ chạy** (ngưỡng tối thiểu 128 KB, file trung bình ~62 KB) | Versioning + Object Lock GOVERNANCE 365 ngày (D-09); thay lifecycle bằng dọn noncurrent/multipart; giữ Standard | **~0,2** |
| Security Hub / AWS Config | Chưa bật | Ngoài phạm vi AA-873 (Config tính theo configuration item, Security Hub theo check) | — |
| **Cộng** | | | **~16–21** |

**Cách tính GuardDuty** (bảng giá us-west-1 lấy bằng Pricing API 28/10):

| Nguồn | Khối lượng của mình | Đơn giá | USD/tháng |
|---|---|---|---:|
| CloudTrail management events | 77.173 event ngày 26/10 (65.380 read-only) → ~2,0–2,4 triệu/tháng | 4,40 USD / triệu | 9–10,5 |
| VPC flow + DNS logs | Flow log của 4 subnet ALB/NLB đã ghi 2,28 GB trong 27 ngày → toàn VPC ước 3–6 GB | 1,10 USD/GB | 3,3–6,6 |
| RDS login (db.t4g.small, 2 vCPU) | 2 vCPU | 1,34 USD/vCPU-tháng | 2,68 |
| S3 data events (tuỳ chọn) | ~63k Tier1 + 157k Tier2 request/27 ngày → ~0,25 triệu | 1,20 USD / triệu | 0,30 |
| Runtime Fargate (tắt) | 2,0 vCPU (1,25 x86 + 0,75 ARM) | 1,85 USD/vCPU-tháng | (3,70) |
| Runtime EC2 NAT (tắt) | t4g.nano 2 vCPU | 1,85 | (3,70) |

- 30 ngày đầu GuardDuty miễn phí; sau ~7 ngày đọc `get-usage-statistics` để so với báo giá (Done-when của AA-873).
- **Giảm được ~1,8 USD/tháng GuardDuty** bằng cách bớt event ồn: NAT instance gọi `RegisterContainerInstance` 3.586 lần/ngày
  (F-4), job drift Terraform (plan) tạo ~10k event/ngày (KMS Decrypt 3.788, DescribeAlarms 1.581, ListTagsForResource 1.509,
  GetBucketVersioning 864). `DescribeTargetHealth` của ECS (9.803/ngày) là bình thường, không giảm được.
- Bản nháp Terraform: [`tf/acc2_security_baseline.tf`](tf/acc2_security_baseline.tf) — GuardDuty sau cờ `guardduty_enabled`
  (mặc định `false`, bật khi anh duyệt giá), BPA, Access Analyzer, KMS + sửa trail, versioning + Object Lock, 4 rule cảnh báo +
  forwarder us-east-1. Thứ tự PR đề xuất: (1) phần miễn phí, (2) CloudTrail/KMS/bucket, (3) GuardDuty.
- Bài thử Done-when (sau apply): tạo rồi xoá 1 IAM policy thử bằng phiên MFA admin → nhận email `[aa-sec] iam_change`.

## 8. AA-665 — Cost Operations: đã có gì, còn thiếu gì

**Đã có trong AA-CIS-App (main `8aabaf0a`):**

- `/admin/llm-usage` "External Spend" (`frontend/app/admin/llm-usage/page.tsx`, 1.101 dòng): tab **Overview / LLM / DataForSEO /
  Budgets**; bộ lọc tenant + account; banner số dư DFS thấp; panel Cost Explorer (`/admin/cost-explorer` + nút check);
  trend ngày (`/admin/spend/daily`); bảng LLM theo tenant → model → stage có đánh dấu fallback; `BudgetsPanel.tsx` sửa
  `shared.spend_budget` (per_run/per_day/hard_stop/alert_pct).
- API (`api/routers/admin_llm_ops.py`): `/llm-usage/tree`, `/dfs-usage`, `/dfs-usage/by-country`, `/spend/daily`,
  `/dfs-balance` + `/dfs-balance/check`, `/cost-explorer` + `/check`, `/jev-canary/check`, `/jev/402-sweep`;
  `admin_budgets.py` (GET + PUT budget); `admin_decisions.py` (`/summary`, `/outcomes/summary`, `/log`, `/jev-credit`).
- `/admin/platform/cost` "Cost per app" (AA-884) và thẻ cost của `/admin/overview` (AA-858), cùng một module `api/services/platform_cost.py`.

**Còn thiếu so với issue:** tên trang + redirect; tab Jev và tab AWS bill riêng; dự báo cuối tháng so với budget theo
provider/account; **"cái gì đã kích hoạt mỗi lần chạy DFS"** — `shared.dfs_call_log` không có `job_id` (chỉ `tenant_id`,
`tour_id`, `meta`; client DFS không truyền `meta`), trong khi `shared.llm_call_log` đã có `job_id` qua `current_job_id()`;
lịch sử số dư DFS / credit Jev dạng biểu đồ; trạng thái budget AWS (Budgets API) cạnh budget nội bộ.

**5 lát tối thiểu (mỗi lát ~1 PR):**

| # | Lát | Repo / file | Ghi chú |
|---|---|---|---|
| C1 | Đổi tên "External Spend" → **Cost Operations**, route `/admin/cost-ops`, redirect từ `/admin/llm-usage`; tách panel Cost Explorer ra tab **AWS bill**; thêm tab **Jev** dùng lại `/admin/decisions/summary` + `/admin/decisions/jev-credit` | CIS `frontend/app/admin/llm-usage/page.tsx` → `frontend/app/admin/cost-ops/`, `frontend/app/_kit/adminNav.tsx` (không phải `_kit/core`), `frontend/next.config.*` redirect | Chỉ FE; UI verify theo `aa-ui-verify` |
| C2 | **Quy kết DFS theo job**: migration CIS **293** (số kế tiếp sau 292; lane khác có thể lấy trước → đánh lại) thêm `shared.dfs_call_log.job_id uuid` + index `(job_id)`; `record_dfs_call_sync` ghi `current_job_id()`; endpoint `GET /admin/dfs-usage/runs?from&to` gộp theo `job_id` JOIN `shared.job` (`kind`, `created_by`, `payload` → scope, `cost_usd` dự tính, `status`, `error`) | CIS `api/migrations/293_dfs_call_log_job_id.sql` (commit riêng), `shared/dfs_client/call_log.py`, `services/seo_intelligence/dataforseo_client.py`, `api/routers/admin_llm_ops.py`, tab DataForSEO bảng "Runs" | Trả lời Done-when "sự cố 25/09 giải thích được": dòng cũ không có `job_id` → script chỉ đọc khớp theo cửa sổ `started_at..finished_at` của job (best-effort, ghi rõ) |
| C3 | **Overview: chi vs budget + dự báo cuối tháng** theo provider (Bedrock acc3/acc1, OpenAI, Jev, DFS) và acc2 AWS: run-rate 7 ngày × ngày còn lại; màu khi dự báo > budget | CIS `api/routers/admin_llm_ops.py` (endpoint `GET /admin/cost-ops/forecast` dùng `llm_call_daily` + `llm_call_log` theo cách `platform_cost.AI_SPEND_SQL`, `dfs_call_log`, `decision_log`, `cost_explorer_snapshot`), tab Overview | Không gọi CE mới; dùng snapshot đã lưu |
| C4 | **Lịch sử số dư**: biểu đồ `shared.dfs_balance_snapshot` + credit Jev (đã có endpoint) trong tab DataForSEO / Jev | CIS FE | Dữ liệu sẵn |
| C5 | (tuỳ chọn) **Budget AWS read-only** cạnh budget nội bộ: đọc `budgets:DescribeBudgets` của acc2 (+ acc3 qua role satellite như CE) | Infra: thêm `budgets:ViewBudget` cho task role CIS (+ role reader acc3); CIS: endpoint + bảng trong tab Budgets | Cần PR Infra trước |

## 9. Phát hiện (S255)

| # | Phát hiện | Việc đề xuất |
|---|---|---|
| F-1 | acc2 sẽ vượt budget 250 USD từ tháng 11 (~255–265) và budget tổng không có FORECASTED | D1 |
| F-2 | Budget `shared` 100 = đúng nhịp (sẽ báo FORECASTED hằng tháng); `crm` 25 sát 23; `identity` (~10 USD) không có budget | D1 (bản nháp đã gồm) |
| F-3 | Truyền dữ liệu giữa AZ **727 GB** trong 27 ngày (7,27 USD; ECS 3,71 + EC2-Other 3,56), tăng từ ~106 GB tháng 9 | Bật CE resource-level (opt-in, 14 ngày) hoặc đọc flow log 1 ngày theo cặp ENI để tìm cặp service nói chuyện chéo AZ (worker ↔ RDS/Redis?) |
| F-4 | NAT instance chạy **AMI ECS-optimized** (bộ lọc `al2023-ami-*-arm64` khớp nhầm) → agent ECS gọi `RegisterContainerInstance` 3.586 lần/ngày | [`tf/vpc_nat_ami_fix.tf`](tf/vpc_nat_ami_fix.tf): tắt agent bằng SSM Run Command ngay; sửa data source (có `ignore_changes = [ami]` nên không thay instance) |
| F-5 | Lifecycle bucket CloudTrail "Deep Archive sau 30 ngày" không bao giờ chạy (file < 128 KB) | Thay trong PR AA-873 (bản nháp có) |
| F-6 | Bedrock trên acc2 tháng 10: 0,24 USD tag `crm` = **Bedrock Guardrails** của bộ lọc PII F3 (đúng thiết kế, AA-Partner CONTEXT.md ghi ~0,72 USD/tháng); thêm **Cohere Embed 4** 0,14 USD (T9 0,02) chưa rõ app nào gọi | Thấp: tra CloudTrail `InvokeModel` trên acc2 để biết role gọi Cohere Embed; nếu là CIS thì xác nhận nó có ghi `shared.llm_call_log` (DM-10, AA-635) |
| F-7 | acc3 không có dòng Credit (như S248 F1) | Anh xem hoá đơn eCloudvalley / Billing → Credits trên acc3 |
| F-8 | 50 secret = 20 USD/tháng; 13 là tài khoản e2e (tenant/CRM) | Không đổi bây giờ (memory: giữ secret e2e). Khi làm lại e2e: gộp mỗi app 1 secret JSON (~4–5 USD/tháng) |
| F-9 | ELB 32–37 USD/tháng gồm NLB chỉ để REST API vào VPC link | Nghiên cứu: REST API private integration thẳng tới ALB (VPC link v2) nếu đã có ở us-west-1 → bỏ NLB (~16 USD/tháng). Cần kiểm tài liệu AWS hiện hành trước khi đề xuất |

## 10. Quyết định cần anh (kèm câu trả lời đề xuất)

| # | Câu hỏi | Đề xuất |
|---|---|---|
| D1 | Budget acc2 tháng 11 trở đi? | **Nâng tổng 250 → 300**, thêm FORECASTED 100 %; per-App: shared 120, crm 35, identity 10 (mới), giữ cis 90 / booking 25 / tripplanner 10 (tổng 290). Lý do: nền mới ~261 + AA-873 ~18 = ~279 |
| D2 | acc3 có cần cảnh báo ngay (không đợi email hằng ngày)? | **Có**: SNS topic trên acc3 + IMMEDIATE ≥ 15 USD (0 USD/tháng) |
| D3 | AA-873 bật gì, theo thứ tự? | (1) BPA + Access Analyzer + rule EventBridge (0 USD) ngay; (2) CloudTrail multi-region + KMS + versioning/Object Lock (~1,25 USD); (3) GuardDuty foundational + RDS login (~15–20 USD), đọc usage sau 7 ngày dùng thử |
| D4 | GuardDuty S3 data events? | **Bật** (+0,30 USD/tháng) vì có bucket tài liệu CRM; Runtime Monitoring để sau (cần thêm bộ nhớ cho sidecar Fargate) |
| D5 | Thứ tự AA-665? | C1 → C2 → C3 (C4, C5 khi rảnh); C2 có migration → luồng D8 |
