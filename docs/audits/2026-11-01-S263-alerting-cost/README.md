---
id: OPS-08-s263-alerting-cost
title: "Alerting cost and inventory: CloudWatch alarms, SNS, SES, EventBridge on acc2, acc3 and management (S263)"
description: "Read-only audit of what the alerting stack (CloudWatch alarms, custom metrics, dashboards, SNS, SES, EventBridge, probe Lambdas) really costs per account for Sep and Oct 2026, with a full inventory and a remove/merge list with USD savings and risk."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-01
review_every_days: 30
related: [OPS-08-s262-assessment-followup]
---

# Chi phí cảnh báo thật: alarm, SNS, SES, EventBridge (S263, 01/11/2026)

> [!NOTE]
> Câu hỏi của tech lead: "có quá nhiều SNS topic, CloudWatch alarm, SES và tài nguyên cảnh báo — tốn bao nhiêu thật?"
>
> **Trả lời ngắn:** nhóm cảnh báo tốn **15,59 USD trong tháng 10** trên acc2 (7,3% của 212,21 USD tổng acc2),
> **0 USD** trên acc3 và **0 USD** trên management. Không phải "quá nhiều topic": chỉ có **3 topic** trên cả ba account.
> Thứ tốn tiền là **101 CloudWatch alarm** (5,05 USD tháng 10, tăng lên ~10,5 USD/tháng từ tháng 11 vì phần lớn
> alarm mới tạo giữa tháng 10) và **~30 custom metric** nuôi các alarm đó (8,11 USD). SNS, SES, EventBridge, Lambda
> probe cộng lại < 0,07 USD. Cảm giác "quá nhiều" đến từ **email**, không phải tiền: 92/101 alarm gửi cả ALARM lẫn OK,
> hai người nhận, cộng 9 rule bảo mật EventBridge → **~375 email/tháng**.
>
> Dọn theo §5 tiết kiệm **~5–6 USD/tháng** (còn ~15–16 USD/tháng thay vì ~21) và giảm khoảng một nửa số email.

## 1. Cách kiểm

- Chỉ đọc: `describe-*`, `list-*`, `get-*` của CloudWatch, SNS, SESv2/SES, EventBridge, Scheduler, Logs, Lambda,
  Budgets, Organizations, Application Auto Scaling, ELBv2, ECS; `ce get-cost-and-usage`. Không đổi gì trên AWS.
- Ba account, mỗi account hai region (us-west-1, us-east-1): acc2 (workload), acc3 (AI), management. Cả ba phiên
  đăng nhập còn hạn, không thiếu account nào.
- Cost Explorer: **4 lần gọi `get-cost-and-usage`** (3 theo SERVICE, 1 theo SERVICE + USAGE_TYPE cho acc2) và 3 lần
  `get-anomaly-monitors` — tổng ≈ 0,07 USD. Tháng 11 (month-to-date) = **0 USD ở mọi account**: Cost Explorer chưa
  có dữ liệu ngày 01/11, nên bảng chỉ dùng tháng 9 và tháng 10.
- Management account: Organization chỉ có **1 thành viên là chính nó**. acc2 và acc3 **chưa** nằm trong Organization,
  nên Cost Explorer ở management chỉ thấy tiền của management (không có dữ liệu hợp nhất).
- Số lượng email/notification lấy từ CloudWatch `NumberOfMessagesPublished` / `NumberOfNotificationsDelivered` 30 ngày
  (02/10–01/11), lịch sử chuyển trạng thái alarm 30 ngày, và `AWS/Events TriggeredRules`.

## 2. Tóm tắt tiền thật (tháng 10/2026, UnblendedCost = NetUnblendedCost, không có credit)

| Account | Tổng account tháng 10 | Nhóm cảnh báo tháng 10 | Tỉ lệ | Nhóm cảnh báo tháng 9 | Log CloudWatch tháng 10 (để so) |
|---|---:|---:|---:|---:|---:|
| acc2 (workload) | 212,21 USD | **15,59 USD** | 7,3% | 6,33 USD | 4,21 USD |
| acc3 (AI) | 0,20 USD | **0,00 USD** | 0% | 0,00 USD | 0,00 USD |
| management | 0,03 USD | **0,00 USD** | 0% | 0,00 USD | 0,00 USD |
| **Cộng** | 212,44 USD | **15,59 USD** | | 6,33 USD | 4,21 USD |

"Nhóm cảnh báo" = CloudWatch alarm + custom metric + dashboard + API CloudWatch + SNS + SES + EventBridge + Lambda
probe. Log (ingest, vended log, Logs Insights) để riêng vì là chi phí quan sát/điều tra, không phải cảnh báo.

**Ước tính tháng 11 ở quy mô hiện tại (acc2):** alarm ~10,5 USD (105 alarm-metric × 0,10) + custom metric ~8–9 USD +
dashboard ~2,3–3 USD + phần còn lại ~0,1 USD ≈ **21 USD/tháng**. Lý do tăng: số alarm-tháng tính tiền trung bình tháng 10
chỉ là 51,7 (nhiều alarm CRM/identity/tenant tạo trong tháng 10), nay là 101 alarm chạy cả tháng.

> [!WARNING]
> acc2 **không được hưởng free tier của CloudWatch**: 51,7 alarm-tháng bị tính 5,05 USD (≈ 0,098 USD/alarm, không trừ
> 10 alarm miễn phí); 27,5 metric-tháng bị tính 8,11 USD (≈ 0,295 USD/metric, không trừ 10 metric miễn phí); dashboard
> 8 metric vẫn bị tính tiền. Vì vậy công thức "×0,10 USD, 10 cái đầu miễn phí" ở brief **không đúng cho acc2** — mọi
> alarm và custom metric đều tính tiền từ cái đầu tiên.

## 3. Chi tiết theo dịch vụ / usage type (acc2)

| Dịch vụ | Usage type | Tháng 9 | Tháng 10 | Lượng tháng 10 | Ghi chú |
|---|---|---:|---:|---|---|
| CloudWatch | `CW:AlarmMonitorUsage` | 1,68 | **5,05** | 51,7 alarm-tháng | alarm chuẩn; anomaly alarm tính 3 |
| CloudWatch | `CW:MetricMonitorUsage` | 2,25 | **8,11** | 27,5 metric-tháng | custom metric `AA/*`, `aa-cis/ops`, `acp` |
| CloudWatch | `DashboardsUsageHour-Basic` | 2,40 | 2,32 | 1 dashboard | `aa-cis-dev-pipeline`, 4 widget, 8 metric |
| CloudWatch | `CW:GMD-Metrics` + `CW:Requests` | 0,00 | 0,05 | 1.284 metric GMD, 18k request | admin UI / script đọc metric |
| CloudWatch | `CW:DatabaseInsights-API` | 0,00 | 0,00 | 10 call | |
| SNS | `Requests-Tier1`, `DeliveryAttempts-SMTP` | 0,00 | 0,00 | 8.067 request, 375 email | trong free tier |
| SES | `Essentials-Outbound-Email` + `Message` | 0,00 | 0,06 | 259 + 216 | email ứng dụng, không phải cảnh báo |
| EventBridge (CloudWatch Events) | `ScheduledInvocation`, `Event-64K-Chunks` | 0,00 | 0,00 | 2.980 lần, 58 chunk | Scheduler + rule sự kiện AWS miễn phí |
| Lambda | `Request`, `GB-Second` | 0,01 | 0,00 | 23k request, 3.678 GB-s | probe/ops Lambda, trong free tier |
| **Cộng nhóm cảnh báo** | | **6,33** | **15,59** | | |
| CloudWatch Logs | `VendedLog-Bytes` (VPC flow log) | 0,87 | 1,78 | 2,7 GB | |
| CloudWatch Logs | `VendedLog-Bytes-WAFLogs` | 0,56 | 1,18 | 1,8 GB | |
| CloudWatch Logs | `DataProcessing-Bytes` (ingest ECS/Lambda/API GW) | 0,10 | 0,98 | 1,5 GB | |
| CloudWatch Logs | `DataScanned-Bytes` (Logs Insights) | 0,00 | 0,27 | 40,1 GB quét | |
| CloudWatch Logs | `TimedStorage-ByteHrs` | 0,00 | 0,00 | 2,1 GB-tháng | |
| **Cộng log** | | **1,54** | **4,21** | | |
| Cost Explorer API (tham khảo) | `APIRequest` | 0,08 | 0,68 | 68 request | script/agent tự gọi CE, không phải cảnh báo |

acc3: tháng 10 chỉ có Claude Sonnet 4.6 trên Bedrock 0,107 USD, Cost Explorer 0,07 USD, thuế 0,02 USD; CloudWatch 0.
management: KMS 0,028 USD, S3 0,004 USD; CloudWatch 0.

## 4. Kiểm kê (số lượng, 01/11/2026)

### 4.1 Tổng hợp theo account

| Hạng mục | acc2 us-west-1 | acc2 us-east-1 | acc3 (cả 2 region) | management (cả 2 region) |
|---|---:|---:|---:|---:|
| CloudWatch metric alarm | **101** | 0 | 0 | 0 |
| Composite alarm | 0 | 0 | 0 | 0 |
| Anomaly-detection alarm | 1 (`aa-crm-dev-kms-decrypt-anomaly`, tính như 3) | 0 | 0 | 0 |
| Metric-math alarm (tính theo số metric) | 2 (`aa-cis-dev-acp-piece-held-rate-high`, `aa-cis-dev-rds-snapshot-expiry-copy-age-aa-cis-dev-db`) | 0 | 0 | 0 |
| High-resolution alarm (< 60 s) | 0 | 0 | 0 | 0 |
| Alarm INSUFFICIENT_DATA > 7 ngày | 0 | — | — | — |
| Alarm trỏ tới topic đã xoá | 0 | — | — | — |
| Custom metric (thấy trong 14 ngày / còn hoạt động 3 giờ qua) | 34 / 26 | 0 | 0 | 0 |
| Dashboard (toàn cục) | 1 | (cùng 1) | 0 | 0 |
| SNS topic | 2 | 0 | 1 (`aa3-cost-alerts`) | 0 |
| SES identity | 1 domain (đã verify, production) | 0 (sandbox) | 0 (sandbox) | 0 (sandbox) |
| SES configuration set | 3 | 0 | 0 | 0 |
| EventBridge rule (bus default) | 13 | 1 (`aa-sec-dev-global-forward`) | 0 | 0 |
| Custom event bus | 1 (`aa-cis-dev-acp-events`, 0 rule) | 0 | 0 | 0 |
| EventBridge Scheduler schedule | 6 (nhóm `aa-cis-dev-acp`) | 0 | 0 | 0 |
| Log group / không đặt retention | 19 / 1 | 0 | 0 | 0 |
| Metric filter | 22 | 0 | 0 | 0 |
| Lambda | 9 | 0 | 0 | 0 |
| AWS Budgets | 7 | — | 1 | 2 |
| Cost Anomaly Detection monitor | 1 (mặc định) | — | 1 (mặc định) | 2 |

### 4.2 Alarm acc2 theo tiền tố tên

| Tiền tố | Số alarm | Gồm |
|---|---:|---|
| `aa-cis-dev-*` | 38 | RDS (CPU, memory, storage, latency, XID, credits, connections, 6 role-pct + 1 heartbeat), jobs CIS, API GW 5xx/latency, `aa-cis/ops` write-failed ×4, tenant ×5, ACP ×4, snapshot ×2, ECS running tasks |
| `aa-crm-dev-*` | 22 | jobs CRM, audit ×3, breakglass ×2, membership ×2, ops-release ×2, bulk reveal, KMS anomaly, ALB (api/portal/web) ×7, CPU |
| `aa-identity-dev-*` | 15 | 4 Lambda Cognito trigger × (errors, throttles, duration p99), WAF blocked, breakglass token, trigger error |
| `TargetTracking-*` (Auto Scaling tạo) | 8 | aa-cis-dev-api + worker × (CPU, memory) × (High, Low) |
| `aa-booking-dev-*` | 8 | API GW 5xx, CPU, jobs ×3, ALB ×2, uptime probe |
| `aa-tripplanner-dev-*` | 6 | assembly/browse × (errors, throttles), jobs errors, jobs not-run |
| `aa-ecosys-dev-*` | 2 | NAT `StatusCheckFailed` + NAT `StatusCheckFailed_System` (recover) |
| `aa-email-dev-*` | 2 | SES bounce rate, complaint rate |

Theo namespace: 57 alarm trên metric AWS (Lambda 20, ECS 10 gồm 8 target tracking, ALB 9, RDS 9, API GW 3, EC2 2,
SES 2, SQS 1, WAF 1), 40 trên custom metric (`aa-cis/ops` 9, `AA/RDS` 8, `AA/Jobs/*` 13, `AA/Crm/*` 6, `AA/Identity` 2,
`acp` 2), 1 trên `ECS/ContainerInsights`, 2 metric-math, 1 anomaly.
Trạng thái: 97 OK, 4 ALARM (đều là alarm `AlarmLow` của target tracking — bình thường khi tải thấp).
`TreatMissingData`: 87 `notBreaching`, 6 `breaching` (heartbeat "sampling-stopped"), 8 mặc định (target tracking).

**Alarm không có dữ liệu metric trong 14 ngày (17):** phần lớn là alarm "sự kiện" (metric chỉ phát khi có lỗi) nên
im lặng là đúng: `aa-cis-dev-*-write-failed` (2/4), `aa-cis-dev-tenant-*` (4), `aa-crm-dev-membership-*` (2),
`aa-crm-dev-breakglass-owner-not-mailed`, `aa-crm-dev-portal-target-5xx`, `aa-identity-dev-waf-blocked`,
`aa-cis-dev-rds-cis-app-too-many-connections`, `aa-cis-dev-acp-*` (3, emitter còn trong code tenant pipeline, chỉ phát
khi có tenant run). **Ngoại lệ thật: `aa-cis-dev-ecs-running-tasks-low` bị mù** — nó đọc `ECS/ContainerInsights`
nhưng Container Insights trên cluster đang **tắt**, nên alarm luôn OK (112 ngày) dù không có task nào. CIS api là service
duy nhất **không** có alarm `HealthyHostCount` trên ALB (Booking, CRM api/portal/web đều có).

### 4.3 SNS

| Account | Topic | Subscription | Publish 30 ngày | Delivery 30 ngày |
|---|---|---|---:|---:|
| acc2 | `aa-cis-dev-acp-alerts` (topic cảnh báo chung, tên cũ còn "acp") | 2 × email `@adventure.asia`, đều confirmed | 263 | 381 |
| acc2 | `aa-email-dev-feedback` (SES bounce/complaint/reject) | **0** (cố ý, ghi trong `ses.tf`: app sẽ subscribe khi làm suppression) | 3 | 0 |
| acc3 | `aa3-cost-alerts` (budget) | 1 × email `@adventure.asia`, confirmed | 0 (budget gửi trực tiếp) | 2 |

Nguồn của 263 lần publish vào topic chung (30 ngày):
- **Alarm**: 36 lần chuyển sang ALARM (ngoài target tracking) + tương ứng OK. **92/101 alarm có `OKActions`** → mỗi sự
  cố = 2 email × 2 người nhận = 4 email. Alarm "ồn" nhất: `aa-tripplanner-dev-browse-throttles` (8 lần),
  `aa-identity-dev-breakglass-token-issued` (3), `aa-cis-dev-api-5xx` (2), `aa-booking-dev-jobs-queue-age` (2).
- **EventBridge → SNS** (9 rule bảo mật/identity): `aa-identity-dev-breakglass-secret-access` **64 lần**,
  `aa-identity-dev-partner-admin-bypass` 14, `aa-sec-dev-access-analyzer-finding` 14, `aa-sec-dev-iam-change` 12,
  `aa-sec-dev-security-group-change` 5, `aa-identity-dev-denied-secret-read` 2, `aa-sec-dev-cloudtrail-tamper` 2,
  `aa-crm-dev-kms-key-admin` 1. (`aa-crm-dev-kms-decrypt-log` ~1.000 lần nhưng đích là log group, không gửi email.)

### 4.4 SES

| Account / region | Chế độ | Quota 24h | Gửi 24h qua | Gửi ~14 ngày (dữ liệu SES giữ 2 tuần) | Bounce / complaint / reject |
|---|---|---:|---:|---:|---|
| acc2 us-west-1 | production | 50.000 (14/s) | 23 | 252 | 0 / 0 / 0 |
| acc2 us-east-1, acc3, management | sandbox | 200 | 0 | 0 | — |

Identity: 1 domain (sub-domain dev của hệ, đã verify). Configuration set: `aa-email-dev-external`,
`aa-email-dev-transactional`, `aa-email-dev-workforce`, mỗi set 1 event destination `feedback-sns`
(BOUNCE, COMPLAINT, REJECT → `aa-email-dev-feedback`). SES là email **ứng dụng** (sign-up, mời, thông báo CRM), không
phải kênh cảnh báo; alarm cảnh báo đi qua SNS email.

### 4.5 EventBridge, log, Lambda

- **Rule acc2 us-west-1 (13):** 5 rule `aa-sec-dev-*` (root activity, IAM change, SG change, CloudTrail tamper,
  Access Analyzer), 5 rule `aa-identity-dev-*`, 3 rule `aa-crm-dev-kms-*`. 12 đích SNS topic chung, 1 đích log group.
  us-east-1: `aa-sec-dev-global-forward` chuyển sự kiện IAM/global về bus default us-west-1. Bus
  `aa-cis-dev-acp-events` không còn rule nào; DLQ `aa-cis-dev-acp-events-dlq.fifo` đang rỗng.
- **Scheduler (6):** booking uptime, RDS snapshot expiry, DFS balance check, retention, photo sync (4 cái gọi chung
  Lambda `aa-cis-dev-dfs-balance-check` làm "ops probe"), TripPlanner jobs daily. Alarm `aa-booking-dev-uptime` đọc
  `Errors` của Lambda ops-probe này — đúng thiết kế (mô tả alarm ghi rõ), không phải cấu hình nhầm.
- **Log group (19, 4,56 GB lưu):** `/aa-cis-dev/diagnostic/vpc-flow-logs` 2,08 GB (365 ngày), `aws-waf-logs-aa-cis-dev`
  1,85 GB (365 ngày), `/ecs/aa-cis-dev` 309 MB (30 ngày), log thực thi API Gateway stage dev 208 MB (30 ngày), còn lại
  < 40 MB. Retention: 9 nhóm 365 ngày, 9 nhóm 30 ngày, **1 nhóm không đặt** (`/aws/apigateway/welcome`, 0 byte).
- **Metric filter (22):** 16 trên `/ecs/aa-cis-dev` và `/ecs/aa-crm-dev` (write-failed, tenant, breakglass,
  membership, ops-release, cis_app too-many-connections), 5 trên log Lambda identity (breakglass token, unexpected error
  ×4), 1 trên log KMS decrypt. Phần lớn chỉ sinh metric khi có lỗi nên gần như không tính tiền.
- **Lambda (9):** 4 Cognito trigger identity, 3 TripPlanner, ops-probe/DFS balance, RDS snapshot expiry. Không có
  Lambda chỉ dùng để chuyển tiếp cảnh báo (không có Slack/Chatbot forwarder).
- **Budgets:** acc2 7 budget (tổng 300 USD + 6 theo app), acc3 1 (`aa3-llm-monthly-total` 250 USD), management 2
  (`aa-management-monthly` 10 USD, `aa-org-monthly` 300 USD). Không có budget action nên không tính tiền
  (Cost Explorer không có dòng "AWS Budgets").

## 5. Đề xuất gỡ / gộp (tech lead đồng ý tất cả trong S263; bản làm thật ở §8 và `diet.md`)

Giá: 0,10 USD/alarm-metric/tháng, 0,30 USD/custom metric/tháng, dashboard ~2,3–3 USD/tháng (acc2 không có free tier).
Mọi alarm/rule đều do Terraform trong `infra/AA-CIS-Infra/accounts/aa365/*.tf` (và `modules/eventbridge`) quản lý,
riêng 8 alarm target tracking do Application Auto Scaling sinh — sửa ở Terraform, không xoá tay trên console.

| # | Tên | Hành động | Tiết kiệm USD/tháng | Rủi ro |
|---|---|---|---:|---|
| 1 | Dashboard `aa-cis-dev-pipeline` | Xoá nếu không ai mở (admin UI `/admin` đã có trang job/LLM) | 2,3–3,0 | Thấp — 8 metric, xem lại được trong Metrics console |
| 2 | 5 custom metric `AA/RDS RoleConnections` (role ≠ `aa_app_user`) | Ngừng publish trong `ops_metrics_sampler` (chỉ alarm heartbeat dùng 1 metric này; alarm pct dùng `RoleConnectionLimitPct`) | 1,50 | Thấp — mất số tuyệt đối trên đồ thị, giữ % |
| 3 | `aa-cis-dev-rds-role-connections-sampling-stopped` | Gỡ: cùng sampler với `aa-cis-dev-jobs-sampling-stopped` (một process phát cả `AA/RDS` và `AA/Jobs/CIS`) | 0,10 | Thấp |
| 4 | `aa-cis-dev-jobs-sampling-stopped`, `aa-booking-dev-jobs-sampling-stopped`, `aa-crm-dev-jobs-sampling-stopped` | Gộp vào alarm `*-jobs-queue-age` cùng metric bằng `TreatMissingData=breaching` | 0,30 | Trung bình — một alarm cho hai nguyên nhân, email kém cụ thể hơn |
| 5 | `aa-booking-dev-unhealthy-hosts`, `aa-crm-dev-unhealthy-hosts`, `aa-crm-dev-portal-unhealthy-hosts`, `aa-crm-dev-web-unhealthy-hosts` | Gỡ: mỗi service chạy 1 task, `*-no-healthy-task` đã bắt sự cố; hai alarm cùng bắn một lúc | 0,40 | Thấp ở dev; xem lại khi chạy ≥ 2 task |
| 6 | 4 alarm target tracking **Memory** của `aa-cis-dev-api` / `aa-cis-dev-worker` | Bỏ policy scale theo memory, giữ CPU (min 1, max 3). AlarmLow memory nằm ALARM liên tục 115 ngày | 0,40 | Thấp–trung bình — wave nặng RAM sẽ không tự scale |
| 7 | `aa-identity-dev-*-duration-p99` (4) | Gỡ, giữ errors + throttles (trigger timeout 5 s thì lỗi sẽ hiện ở errors) | 0,40 | Trung bình — mất cảnh báo sớm khi trigger chậm |
| 8 | `aa-cis-dev-rds-connections-high` | Gỡ: trùng ý với 6 alarm `rds-role-connections-*` + `cis-app-too-many-connections` | 0,10 | Thấp |
| 9 | `aa-ecosys-dev-nat-status-check-failed` | Đổi metric sang `StatusCheckFailed_Instance` (phần system đã có `aa-ecosys-dev-nat-system-check-recover`) — hết cặp email trùng | 0 | Thấp |
| 10 | `aa-cis-dev-ecs-running-tasks-low` | **Thay** bằng `aa-cis-dev-no-healthy-task` (ALB `HealthyHostCount` trên target group CIS api) — alarm hiện tại mù vì Container Insights tắt | 0 (đổi 1 lấy 1) | Sửa lỗ hổng; không bật Container Insights (tốn tiền) |
| 11 | `OKActions` trên ~92 alarm | Bỏ OK cho alarm "sự kiện" (write-failed, tenant, breakglass, membership, ops-release…) — giữ OK cho alarm tài nguyên | 0 | Thấp — giảm ~1/3 email |
| 12 | Rule `aa-identity-dev-breakglass-secret-access` (64 email/tháng) | Tìm ai đọc secret break-glass 64 lần (tự động hoá hợp lệ thì loại principal đó khỏi pattern; nếu không thì đây là phát hiện bảo mật) | 0 | Cần điều tra trước khi lọc |
| 13 | Log `/aa-cis-dev/diagnostic/vpc-flow-logs`, `aws-waf-logs-aa-cis-dev` (365 ngày) | Hạ retention xuống 30–90 ngày ở dev; cân nhắc tắt VPC flow log khi không điều tra | 0 hôm nay (dưới ngưỡng lưu trữ), ~1,8 nếu tắt flow log | Thấp ở dev; giữ 365 ngày cho prod |
| 14 | Log group `/aws/apigateway/welcome` | Xoá (0 byte, không retention) | 0 | Không |

**Gói khuyến nghị (#1, #2, #3, #5, #6, #8, #9, #10, #11, #14):** ~4,8–5,5 USD/tháng, rủi ro thấp; thêm #4 và #7
thì ~5,5–6,2 USD/tháng. Sau dọn: ~89 alarm, ~25 custom metric, 0 dashboard → **~15–16 USD/tháng** cho nhóm cảnh báo
thay vì ~21 USD, và khoảng một nửa số email.

Không đề xuất gỡ: alarm throttles TripPlanner (`browse-throttles` đã bắn 8 lần/30 ngày — tín hiệu thật), alarm RDS tài
nguyên, alarm SES bounce/complaint (yêu cầu của SES), các rule `aa-sec-dev-*` (miễn phí, là baseline bảo mật).
Không gộp 6 alarm `rds-role-connections-*` thành 1 metric-math: alarm metric-math tính tiền theo **số metric** bên trong,
nên không rẻ hơn.

## 6. Thứ không tốn tiền (hoặc gần 0)

- **SNS**: 3 topic, ~8.000 request và 375 email/tháng — nằm trong free tier (1 triệu request, 1.000 email). Số topic
  không phải vấn đề tiền.
- **EventBridge**: 14 rule trên bus default nhận sự kiện dịch vụ AWS (miễn phí), 6 schedule Scheduler (~3.000 lần/tháng,
  trong 14 triệu lần miễn phí), bus `aa-cis-dev-acp-events` rỗng không tốn gì.
- **SES**: 0,06 USD/tháng cho ~250 email ứng dụng; 3 configuration set và topic feedback không tính phí.
- **Lambda** probe/ops: < 0,01 USD/tháng.
- **AWS Budgets** (10 budget trên 3 account) và **Cost Anomaly Detection**: 0 USD (không có budget action).
- **Metric filter**: không tính phí riêng (chỉ tính custom metric chúng sinh ra, đã gồm trong 8,11 USD).
- **acc3 và management**: không có alarm, dashboard, log group nào; chỉ có budget + anomaly monitor + 1 topic budget.
- **SQS DLQ** `aa-cis-dev-acp-events-dlq.fifo`: rỗng, ~0 USD.

## 7. Ghi chú

- Mọi con số tiền là UnblendedCost từ Cost Explorer; NetUnblendedCost bằng nhau (không có credit/discount ghi nhận
  trên ba account này trong tháng 9–10).
- Không ghi account ID, ARN, ID tài nguyên, địa chỉ email vào file này (repo public). Topic, alarm, rule chỉ ghi theo tên.
- Muốn số tháng 11 thật: chạy lại Cost Explorer sau ngày 03/11 (dữ liệu trễ 24–48 giờ).

## 8. Sau khi dọn (S263 alert diet, AA-1025)

Tech lead: "chỉ giữ những cái thật cần thiết, đồng ý các đề xuất để giảm tiền". Bảng quyết định từng alarm
(giữ / gỡ / chuyển vào app, lý do, check thay thế, test) ở [`diet.md`](diet.md); làm theo bảng đó trong 4 PR
(AA-CIS-Infra, AA-CIS-App, AA-Booking, AA-Partner) + PR repo gốc này.

| | Trước (dự báo tháng 11) | Sau |
|---|---:|---:|
| Alarm | 101 (+1 mới) → ~10,5 USD | 24 alarm, 27 đơn vị tính tiền → **2,70 USD** |
| Custom metric | ~28 → ~8–9 USD | ~3 → **~0,90 USD** |
| Dashboard | 1 → ~2,3–3 USD | 0 |
| **Tổng nhóm cảnh báo** | **~21 USD/tháng** | **~3,7 USD/tháng** (vượt mục tiêu ≤ 6 USD) |
| Log vended (VPC flow + WAF) | ~3,0 USD (tháng 10) | ~0,3 USD (flow log chỉ REJECT, WAF log chỉ request bị chặn/đếm, 30 ngày) |
| Email | ~375/tháng, 92 alarm gửi cả OK | chỉ 13 alarm trạng thái gửi OK; check trong app tối đa 1 email/check/ngày |

Chuyển vào app ($0, dùng chung topic SNS cảnh báo nên người nhận không đổi): hàng đợi job của CIS/Booking/CRM,
giới hạn kết nối theo role, tuổi XID, các log event (ghi cost-log lỗi, tenant pool fail-closed, cis_app hết kết nối),
audit export CRM, break-glass, membership feed, ops release, bulk reveal. Gỡ hẳn: 8 alarm target tracking (bỏ
autoscaling theo CPU/memory trên Dev), alarm 5xx/latency API (Sentry bắt lỗi app; sập service đã có
`*-no-healthy-task`), unhealthy-hosts, CPU service, RDS memory/latency/disk queue/surplus credits, NAT
StatusCheckFailed trùng, alarm ACP chết (emitter không ai gọi), DLQ ACP, uptime Booking, throttles/duration identity,
WAF blocked. Thêm 1: `aa-cis-dev-api-no-healthy-task` (thay alarm mù `ecs-running-tasks-low`).
Số thật sau apply: đếm lại alarm/custom metric theo live step của PR Infra; Cost Explorer tháng 12 mới thấy đủ.

