---
id: CAT-00-alerting-inventory-s287
title: Alarm and notification inventory in the admin - current state and proposal (S287)
description: Advisory for the tech lead - can the admin show how many alarms and notifications the infrastructure has, of which type, for which app, and can they be tuned by hand; current gaps, market practice, options with cost, roadmap tied to the ecosystem status issues, and decisions to take.
type: report
status: draft
owner: tech-lead
audience: [cto, engineer, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-21
related: [OPS-07, AA-913, AA-1096, AA-1110, AA-1140, AA-1141, AA-1142]
---

# Theo dõi alarm và notification trên admin: hiện trạng và đề xuất (S287)

> **Bản tư vấn cho tech lead, đặt trong repo public.** Không có account ID, ARN, ID tài nguyên, e-mail hay tên người.

_Read-only advisory, 21/11/2026 (S287). Tác nhân: Claude Code. Không sửa repo app, không ghi AWS. Đầu vào: code CIS,
Booking, Partner, TripPlanner, Infra; đọc live CloudWatch/EventBridge/SNS trên acc2 us-west-1 cùng ngày. Bản nháp đã
qua một vòng phản biện; các sửa đổi của vòng đó đã đưa vào đây. Chi phí lập báo cáo: 0 USD._

---

## 1. Trả lời ngắn

| Câu hỏi | Trả lời | Chi tiết |
|---|---|---|
| **Đếm được có bao nhiêu alarm/notification?** | **Một phần.** | Overview › Apps health và Platform › App health đếm live số CloudWatch alarm **của từng app** (cache 5 phút). Không có **tổng chung**, không đếm EventBridge rule (16), budget, in-app ops check của CIS/Booking/CRM hay Sentry. |
| **Biết loại gì?** | **Chưa, trên trang live.** | Loại (Lambda errors, ALB health, RDS, SES, Identity, WAF…) chỉ có ở trang docs tĩnh OPS-07 (`docs/generated/alarms.md`), sinh từ Terraform, không có trạng thái live. |
| **Biết của app nào?** | **Có, nhưng xếp sai vài chỗ.** | Admin xếp alarm theo **tiền tố tên**, không theo tag `App`. Tiền tố `aa-cis-dev-` bắt cả 2 alarm CIS + 5 alarm RDS (DB dùng chung) + 1 alarm WAF bảo vệ CRM, nên admin ghi **CIS 8**, đúng ra **CIS 2**. Alarm `aa-sec-dev-admin-session-digest-errors` không khớp tiền tố nào nên admin chỉ thấy **31/32**. |
| **Chỉnh tay được không?** | **Gần như không.** | Chỉnh được: **người nhận** (Platform › Alert recipients, AA-913; một SNS topic chung, nhận tất cả hoặc không gì), ngưỡng route alert của AI gateway, % cảnh báo budget AI. **Không chỉnh được:** ngưỡng 32 CloudWatch alarm (chỉ qua Terraform, Platform › Infra hiện read-only một phần, đúng quyết định AA-1096 L6); ngưỡng in-app check (hằng số code, ví dụ `JOBS_STARVED_AFTER_S = 900`, `ROLE_CONNECTIONS_PCT = 80`, `SPEND_NEAR_RATIO = 0.8`, Booking `STUCK_AFTER_S = 900`), **trái luật "mọi ngưỡng chỉnh được trên admin"**. Không có mute, snooze, ack, maintenance window, lịch sử đã kêu. |

**Kết luận:** chưa có chỗ nào trả lời trọn "đang canh bao nhiêu thứ, loại gì, của app nào, ai nhận, ngưỡng nằm đâu, chỉnh
thế nào". **Đề xuất: mở rộng trang Platform › Alerts sẵn có** (hiện chỉ có tab Recipients) thành khu quản lý cảnh báo,
bắt đầu bằng một **Catalogue read-only** (0 USD), rồi thêm mute có rào chắn; các phần đo độ ồn để tới khi pilot. Chi
tiết ở §4–§5.

### Phát hiện khi kiểm (xử lý được ngay, không cần chờ trang mới)

1. **Alarm WAF `…-crm-edge-rate-blocked` (alarm thứ 32, vừa apply) đang ALARM**: 6.815 request bị chặn trong cửa sổ
   12:48 (+07). Ngưỡng `crm_edge_rate_alarm_threshold = 1`, `evaluation_periods = 1`, `treat_missing_data = notBreaching`,
   chỉ có alarm action. Với ngưỡng 1, mỗi đợt có người bị chặn là một e-mail. Cần xem đó là lạm dụng thật hay limit
   theo viewer đặt quá thấp, rồi đặt điều kiện "kéo dài" (ví dụ ≥ N block trong 2/3 chu kỳ) bằng **một Infra PR thường**.
2. **Topic `aa-cis-dev-acp-alerts` chỉ có 1 người nhận đã xác nhận** (địa chỉ bootstrap). Kênh thứ hai (AA-1110) chưa
   có. Hộp thư đó lỗi thì không ai nhận cảnh báo nào. Cũng chưa có alarm `NumberOfNotificationsFailed` cho topic này.
3. **Topic `aa-email-dev-feedback` có 0 subscriber**: bounce/complaint/reject của SES publish lên đó nhưng không ai đọc.
   Không nên gắn thẳng e-mail (mỗi bounce một thư, toàn nhiễu). Hoặc đọc qua SQS + job CIS (phạm vi 3 của AA-811),
   hoặc chấp nhận 2 alarm tỉ lệ bounce/complaint là đủ cho Dev.
4. **Budget/anomaly của acc4, acc1, acc3** gửi e-mail thẳng, admin không thấy.
5. **`docs/generated/alarms.md` (repo public) chứa hậu tố ID của ALB và target group** (9 dòng), trái DM-6.10/D-25.
   Sửa generator để che.

---

## 2. Hiện trạng

### 2.1 Nguồn cảnh báo

| Lớp | Số lượng | App | Ngưỡng nằm ở | Kênh | Admin thấy? |
|---|---|---|---|---|---|
| CloudWatch metric alarm (acc2 us-west-1) | **32** (0 composite, 0 ở region khác). Theo namespace: Lambda 10, ApplicationELB 8, metric-math 3, RDS 3, SES 2, EC2 2, AA/Identity 2, AA/TripPlanner 1, WAFV2 1. 18 gửi ALARM+OK, 14 chỉ ALARM | Theo tag `App`: CIS 2, Booking 2, CRM 6, TripPlanner 6, Identity 6, Shared 10 (5 RDS, 2 NAT, 2 SES, 1 admin-session digest) | Terraform: 26 giá trị literal, 4 biến, 2 giá trị suy ra | SNS `acp-alerts` → e-mail; alarm NAT còn có EC2 auto-recover | Chỉ số đếm theo app (xếp theo tiền tố, sai như §1); docs tĩnh OPS-07 |
| EventBridge security/audit rule | 16 ở us-west-1 (15 → SNS, 1 → log group) + 3 forwarder ở region khác | Ecosystem (Identity, IAM, KMS, root login…) | Event pattern trong Terraform | SNS → e-mail | Chỉ OPS-07 |
| AWS Budgets + Cost Anomaly (acc2) | 7 budget, 15 notification, 1 anomaly monitor gửi ngay + 1 monitor mặc định của AWS | Ecosystem / theo service | Biến Terraform | SNS; monitor mặc định gửi e-mail root | Platform › Infra (read-only) |
| Budget/anomaly acc4, acc1, acc3 | 1–2 mỗi account | Billing, LLM | Terraform từng root | E-mail trực tiếp | Không |
| CIS in-app ops check (ops sampler trong task api) | 23 check cố định + 9 họ check theo stage (mỗi họ nhân theo số stage) + 2 digest | CIS (và AI gateway của mọi app) | Phần lớn hằng số code; một ít trong settings / route policy | Chuông admin (10 dòng gần nhất) + SNS e-mail | Chỉ chuông |
| CIS `ops_alert_email` | 12 template | CIS | Phần lớn chỉnh được (spend, credit, settings) | Chuông + SES | Chuông |
| Booking ops check | 2 | Booking | Hằng số code | SNS e-mail | Không |
| CRM ops alert | 19 (7 theo trạng thái, 12 theo sự kiện) | CRM | Hằng số code / settings CRM | SNS e-mail | Không |
| Sentry | 4 app có SDK; số alert rule chưa kiểm (connector Sentry cần đăng nhập lại) | 4 app | Trong Sentry | E-mail Sentry | Không |
| CI scheduled guard + Dependabot/secret scanning | 42 workflow theo lịch; Dependabot ở 6 repo | Mọi repo | YAML, tools | E-mail/issue GitHub, `guard_runs.py` | Không |
| Thư từ nhà cung cấp | Vercel (deploy/usage), AWS Health + thông báo account gửi e-mail root, ACM hết hạn cert, console Anthropic/OpenAI (usage/limit) | Theo nhà cung cấp | Ở nhà cung cấp | E-mail | Không |

Ghi chú về con số: **không cộng các dòng trên thành một tổng "số cảnh báo"**. Các họ check CIS nhân theo stage, template
e-mail và notification budget là đơn vị khác nhau. Catalogue (§5) sẽ đếm theo dòng thật, mỗi dòng một điều kiện.

Ghi chú về hai số "10": nhóm **shared** trên admin (tiền tố `aa-ecosys`/`aa-identity`/`aa-email`) = 6 Identity + 2 NAT +
2 SES; nhóm **Shared** theo tag = 5 RDS + 2 NAT + 2 SES + 1 digest. Trùng số nhưng khác tập.

### 2.2 Lỗ hổng phủ sóng

- **Worker CIS và worker Booking không có CloudWatch alarm.** Worker CIS chỉ được check `jobs_starved` canh, mà check
  này chạy trong ops sampler của **task api** (`api/core/ops_metrics_sampler.py`), nên phụ thuộc api còn sống. Khi
  chính các in-app check chết theo api, thứ còn canh là alarm `aa-cis-dev-api-no-healthy-task`.
- **CIS và Booking không có alarm API 5xx/latency.** Chỉ CRM có cặp alarm SLO (5xx rate, p95).
- **Không có uptime/synthetic check từ bên ngoài** (custom domain API Gateway, DNS, cert).
- **Không có alarm giao thư hỏng** (`NumberOfNotificationsFailed`) cho topic cảnh báo duy nhất, cộng thêm việc topic chỉ
  có 1 người nhận.

### 2.3 Trang admin hiện có

| Trang | Hiện gì | Thiếu |
|---|---|---|
| Overview › Apps health | Mỗi app: health, số alarm đang ALARM (CloudWatch, cache 5 phút) | Tổng chung, loại, xếp theo tag |
| Platform › App health (`/admin/platform/apps`) | Như trên, chi tiết hơn theo app | Như trên |
| Platform › Alert recipients (`/admin/platform/alerts`, AA-913) | Thêm/bớt người nhận topic cảnh báo (rbac `alerts.write`) | Catalogue, trạng thái, mute, lịch sử |
| Platform › Infra (AA-1096) | Một số ngưỡng alarm và budget, read-only (L6) | Phần lớn 32 alarm |
| Chuông admin | 10 cảnh báo in-app gần nhất của CIS | Booking/CRM, lọc, ack |
| Docs OPS-07 | Mọi alarm + EventBridge rule, điều kiện, runbook | Trạng thái live; đang lệch (ghi 31) |

---

## 3. Thực hành chuẩn (thị trường và SRE)

- **Một catalogue cho mọi cảnh báo**, mỗi dòng có owner (vai trò), severity, runbook, kênh, ngưỡng và **nguồn sự thật
  của ngưỡng**. Datadog Monitors, Grafana Alerting, New Relic Alerts đều tách *alerting* (cái gì đang canh, ai nhận,
  chỉnh ở đâu) khỏi *dashboard/status* (hệ thống có ổn không).
- **Cấu hình cảnh báo là code** (monitoring-as-code) có review; UI dùng để xem, tắt tạm và đề xuất, không thay git.
- **Tắt tạm có hạn** (Alertmanager silence, Datadog downtime): bắt buộc lý do, tự hết hạn, có audit; không sửa ngưỡng
  lúc nửa đêm.
- **Ack và rà độ ồn** chỉ có nghĩa khi có lưu lượng thật và người trực. Google SRE (book ch. 6, Workbook ch. 5): cảnh
  báo phải hành động được, ưu tiên triệu chứng hơn nguyên nhân; mức chịu đựng khoảng **≤ 2 incident** (không phải alert)
  mỗi ca trực 12 giờ; SLO alert dùng **burn rate nhiều cửa sổ** (14.4× / 6× / 1×).
- **Hai mức là đủ cho đội nhỏ**: *page* (cần người ngay) và *ticket* (xử lý trong giờ). Nhiều mức hơn chỉ có ích khi có
  lịch trực.

---

## 4. Phương án và chi phí

### 4.1 Đặt trang ở đâu

| Phương án | Mô tả | Ưu | Nhược | Chi phí AWS |
|---|---|---|---|---|
| **PA1. Mở rộng Platform › Alerts sẵn có** | Thêm tab **Catalogue** cạnh tab Recipients (AA-913) hiện có; sau đó tab Mutes; Activity để tới pilot | Không thêm mục menu; đúng mô hình tách alerting khỏi status; làm được ngay, không chờ AA-1140; quyền `alerts.write` đã có | Status page phải gọi sang API này để hiện tóm tắt | ~0 USD (xem 4.3) |
| PA2. Một tab trong Ecosystem status (AA-1140/1141) | Gộp vào trang status mới | Một trang ops | Lẫn "xem tình trạng" với "quản trị cấu hình"; phải tách quyền trong một trang; chờ AA-1140 (slot S290) | ~0 USD |
| PA3. Công cụ ngoài | Grafana Cloud, Better Stack, PagerDuty | Có sẵn ack/escalation | Không phủ in-app check; hệ cấu hình thứ hai song song Terraform; thêm nơi đăng nhập; dịch vụ ngoài mới cần chữ "có" riêng | Xem 4.4 |

### 4.2 Chỉnh ngưỡng CloudWatch từ admin thế nào

| Cách | Cơ chế | Đánh giá |
|---|---|---|
| (a) Admin gọi `PutMetricAlarm` | Admin sửa, job ghi thẳng alarm; Terraform `ignore_changes` ngưỡng | **Không.** Task role CIS có quyền ghi alarm: CIS bị chiếm là làm im được alarm security; `PutMetricAlarm` ghi đè cả định nghĩa (lỗi code có thể xoá action); Terraform hết là nguồn sự thật; đảo ngược AA-1096 L6. |
| (b) Terraform là người ghi duy nhất, admin chỉ dẫn đường | Catalogue hiện **ngưỡng live** + **file và biến Terraform** (`threshold_source`) + nút "Change in Terraform" mở thẳng file trên GitHub; agent mở Infra PR | **Đề xuất.** Ngưỡng CloudWatch đổi khoảng một lần mỗi quý, không đáng làm đường ống tự động. Không thêm quyền ghi nào cho runtime. |
| (b') Như (b) nhưng tự động: admin → SSM → workflow mở PR | | **Không.** Thêm lại đường ghi runtime → hạ tầng (CIS ghi SSM, workflow tin nội dung đó), mở đường chèn giá trị vào Terraform. |
| (c) Terraform đọc SSM lúc plan | | **Không.** Chậm như (b) mà mất diff ngưỡng trong PR. |

**Xung đột luật nhà cần chốt:** luật "mọi ngưỡng chỉnh được trên admin" (S278/S279) và AA-1096 L6 ("ngưỡng CloudWatch
read-only, đổi qua Infra PR") mâu thuẫn. Đề xuất ghi rõ **ngoại lệ có chủ đích** cho ngưỡng CloudWatch: admin hiển thị
và dẫn tới chỗ sửa, không ghi (D2).

Ngưỡng **in-app check** thì khác: đó là code của chính app, chuyển vào **settings registry** (`cis.ops.*`, `booking.ops.*`,
`crm.ops.*`; bounds, maker-checker, audit) là đúng luật nhà, có hiệu lực ngay, 0 USD.

### 4.3 Tắt tạm (mute) cho CloudWatch

- Dùng **CloudWatch Alarm Mute Rules** (`PutAlarmMuteRule` / `DeleteAlarmMuteRule`; cửa sổ `at` một lần hoặc `cron`;
  tối đa 100 alarm mỗi rule). Mute chỉ tắt **action**, alarm vẫn đánh giá và ghi lịch sử, không đụng định nghĩa alarm
  nên Terraform không drift. **Giá chưa kiểm: phải kiểm giá và xin chữ "có" kèm số USD/tháng trước khi bật.**
- Rule chọn alarm **theo tên**, không theo tag. Giới hạn theo tag chỉ làm ở IAM: task role CIS chỉ được
  `PutAlarmMuteRule`/`DeleteAlarmMuteRule` trên resource mute rule và alarm có tag `Mutable=true`.
  **CIS không bao giờ được `cloudwatch:TagResource`/`UntagResource`**, nếu không CIS bị chiếm sẽ tự gắn `Mutable=true`.
- Mute tắt **mọi** action: alarm NAT `…-nat-system-check-recover` mà mute thì mất cả EC2 auto-recover, nên phải
  non-mutable.
- **Không bao giờ mute được:** alarm security, Identity, break-glass, KMS anomaly, NAT recover; EventBridge rule (không
  phải alarm, không mute được).
- **Bẫy hết mute:** action chỉ chạy khi **đổi trạng thái**. Alarm còn ALARM lúc mute hết hạn sẽ im lặng tiếp. Admin
  phải đánh dấu "muted alarm still firing at expiry" và bước hết hạn phải publish nhắc lên topic.
- **Rào chắn:** chỉ admin (`alerts.write`); bắt buộc lý do; tối đa 24 giờ (kiểm cả ở server lẫn cửa sổ `at`); gia hạn
  hoặc maintenance window > 24 giờ cần checker (maker-checker); giới hạn số mute cùng lúc; nút unmute sớm.
- **Audit:** CloudTrail chỉ thấy task role CIS, nên dòng audit trong app phải mang danh tính staff, và mỗi lần mute/unmute
  publish một thư lên topic ("X muted Y until Z, reason") để người khác trong đội biết.
- **Phương án dự phòng bị loại:** `DisableAlarmActions` làm `actions_enabled` của Terraform drift, terraform-drift đỏ,
  lần apply sau tự bật lại, không có hạn. Mute rule tạo từ admin **không** để Terraform quản; thêm bước reconcile liệt kê
  mute rule và đánh dấu rule không tạo từ admin (mute tay trên console).

### 4.4 Chi phí

| Hạng mục | Giá (đọc 21/11/2026) | Ghi chú |
|---|---|---|
| `DescribeAlarms`, `DescribeAlarmHistory`, `ListTagsForResource`, `events:ListRules`, `tag:GetResources` | Trong 1 triệu API request miễn phí/tháng | Cache 5 phút. `DescribeAlarmHistory` chỉ giữ 30 ngày, trang 100 dòng |
| `GetMetricData` | 0,01 USD / 1.000 metric, **không** nằm trong free tier | **Không vẽ sparkline mỗi alarm mỗi lần refresh**: 32 alarm × refresh 5 phút ≈ 276 nghìn metric/tháng ≈ 3 USD và tăng theo số alarm |
| Alarm chuẩn mới | 0,10 USD/alarm/tháng (account đã vượt 10 alarm miễn phí) | Ví dụ alarm `NumberOfNotificationsFailed` |
| Alarm metric-math / composite / anomaly band | Tính theo số metric: ratio 2 cửa sổ ≈ 4 metric ≈ 0,40 USD; composite 0,50 USD; anomaly band = 3 metric | Áp dụng khi làm burn-rate (AA-1142) |
| CloudWatch Synthetics | ≈ 10 USD/tháng cho 1 canary chạy 5 phút/lần, cộng Lambda/S3 | Cần chữ "có" riêng (observability trả phí đang hoãn) |
| SQS cho Activity ingest | ~0 USD ở mức này (free tier) | Chỉ khi tới pilot |
| Mute Rules | **Chưa kiểm** | Kiểm trước khi bật |
| Grafana Cloud | Free 3 user IRM; Pro 19 USD/tháng + theo user; datasource CloudWatch gọi `GetMetricData` | Không biết in-app check, không maker-checker |
| Better Stack | Free 10 monitor; gói trả phí từ khoảng 29 USD/tháng | Uptime/synthetic, không đọc alarm |
| PagerDuty | Free 5 user; Professional khoảng 21 USD/user/tháng | Chỉ làm lớp gọi/escalation cho mức *page* |
| Opsgenie / AWS Incident Manager | Opsgenie đã ngừng bán (2025), end of life 2027; Incident Manager đóng với khách mới | Không chọn |

Giá vendor ngoài phải kiểm lại live ngay trước khi xin quyết, và mỗi dịch vụ cần một chữ "có" riêng kèm số USD/tháng.

---

## 5. Đề xuất và lộ trình

**Đề xuất: PA1 + cách (b) cho ngưỡng CloudWatch + settings registry cho in-app check + mute có rào chắn.** Status page
AA-1140 gọi cùng API để hiện tóm tắt "đang kêu / đang mute". Không làm phần đo độ ồn trên Dev: hôm nay có 1 alarm kêu và
1 người nhận, các chỉ số % actionable hay số lần kêu ngoài giờ chưa có nghĩa.

### Catalogue: một dòng cho mỗi điều kiện cảnh báo

| Trường | Nguồn |
|---|---|
| `name`, `app`, `component` | Tên alarm/rule/check; tag `App` (thay tiền tố tên), tag `Component` mới |
| `type` | metric, metric-math, EventBridge, budget, cost anomaly, in-app check, CI |
| `severity` | Tag `Severity` mới: `page` / `ticket` |
| `condition` | Metric, statistic, threshold, period, datapoints, `TreatMissingData` |
| `threshold_source`, `editable_via` | File + biến Terraform (link GitHub) / settings key / hằng số code (đánh dấu đỏ); `settings` / `terraform` / `mute only` / `none` |
| `channel`, `runbook`, `owner` | Topic (ALARM, ALARM+OK), chuông, SES, auto-recover; hậu tố runbook có sẵn (`alarm_runbooks.tf`); vai trò, không tên người |
| `state`, `freshness` | OK / ALARM / INSUFFICIENT_DATA / muted đến khi nào; thời điểm đọc |

Cách lấy dữ liệu, đều 0 USD: CloudWatch alarm + tag bằng một lệnh `tag:GetResources` (ResourceTypeFilters
`cloudwatch:alarm`, kiểm hỗ trợ trước) hoặc `ListTagsForResource`; EventBridge bằng `ListRules`. Cả hai cần thêm quyền
**đọc** cho task role CIS qua Infra PR. Định nghĩa in-app check của Booking/CRM lấy từ registry tĩnh mỗi repo (docs gen
xuất ra), **không** đọc chéo schema `booking.*`/`crm.*`. Budget acc4/acc1/acc3 hiện **tĩnh** từ Terraform docs; account
ID chèn lúc runtime trên admin, không ghi trong docs; **không** tạo role đọc chéo trên acc1. Giao diện tiếng Anh mặc
định, không hiện mã AA-xxx.

Bảng mới (nếu cần) phải đối chiếu `docs/architecture/db-schema-reference.md` và `docs/database/schema-ownership.md`;
ưu tiên dùng lại audit log và `shared.notifications` có sẵn trước khi thêm bảng.

### Lộ trình

| Pha | Khi | Nội dung | Chi phí |
|---|---|---|---|
| **P0. Sửa và Catalogue read-only** | S288–S289 (trước AA-1140) | Infra PR: tag `Severity`/`Component`/`Mutable`, quyền đọc tag + `ListRules` cho task role CIS, sửa alarm WAF (điều kiện kéo dài sau khi điều tra 6.815 request), alarm `NumberOfNotificationsFailed` cho topic cảnh báo. CIS: xếp app theo tag `App`, thêm tổng và đếm theo loại trên App health, tab **Catalogue** read-only trên Platform › Alerts, cột lỗ hổng phủ sóng (§2.2). CIS/Booking/CRM: ngưỡng in-app check vào settings registry. Root: generator `alarms.md` che ID ALB/TG. | 0 USD; alarm mới 0,10 USD/tháng (cần "có") |
| **P1. Mute có rào chắn** | Cùng AA-1141 (S291) | Mute Rules từ admin theo §4.3 (sau khi kiểm giá); ack/snooze cho in-app check; đánh dấu "still firing at expiry"; reconcile mute rule trên console. | Mute Rules: chưa kiểm giá |
| **P2. Khi bắt đầu pilot** | AA-1142 (S292) hoặc khi có lưu lượng thật | Tab Activity: một SQS subscribe topic `acp-alerts` + job CIS đọc → một ledger cho mọi app (mọi nguồn đã publish lên topic này), không cần endpoint M2M, không poll `DescribeAlarmHistory`. Ack, rà độ ồn hằng tháng, SLO burn-rate, synthetic check, PagerDuty Free cho mức *page* nếu có trực ngoài giờ. | SQS ~0 USD; burn-rate ≈ 0,40 USD/alarm; Synthetics ≈ 10 USD (cần "có") |

P0 là code nhỏ, có thể gộp vào AA-1140 hoặc mở issue riêng; **hỏi trước khi tạo issue Linear mới** (quota gói Free).

---

## 6. Quyết định cần tech lead

| # | Bối cảnh (1 dòng) | Đề xuất |
|---|---|---|
| D1 | Trang cảnh báo đặt ở đâu | **Mở rộng Platform › Alerts sẵn có** (tab Catalogue cạnh Recipients); status page AA-1140 chỉ nhúng tóm tắt. |
| D2 | Ngưỡng CloudWatch: luật "mọi ngưỡng chỉnh trên admin" mâu thuẫn AA-1096 L6 | **Chốt ngoại lệ có chủ đích:** Terraform là người ghi duy nhất; admin hiện ngưỡng live + link "Change in Terraform", agent mở Infra PR. Không `PutMetricAlarm`, không đường SSM. |
| D3 | Ngưỡng in-app check đang là hằng số code | **Chuyển vào settings registry ở P0** (0 USD, đúng luật nhà). |
| D4 | Tắt tạm alarm ồn | **Mute Rules từ admin** với rào chắn §4.3, sau khi kiểm giá; loại hẳn `DisableAlarmActions`. |
| D5 | Mức severity | **Hai mức `page` / `ticket`**, gắn tag ngay; giữ một topic, tách topic `page` khi pilot. |
| D6 | Công cụ ngoài | **Chưa dùng ở Dev.** Khi pilot có trực ngoài giờ: PagerDuty Free (0 USD) cho mức `page`, xin "có" riêng lúc đó. |
| D7 | Cảnh báo acc4/acc1/acc3 | **Hiện tĩnh** từ Terraform docs, account ID chèn lúc runtime; không role đọc chéo trên acc1. |
| D8 | Alarm WAF đang ALARM, ngưỡng 1 | **Điều tra 6.815 request bị chặn trước**, rồi đổi sang điều kiện kéo dài bằng Infra PR thường. |
| D9 | Topic cảnh báo 1 người nhận, không alarm giao thư hỏng | **Thêm alarm `NumberOfNotificationsFailed` (0,10 USD/tháng)** ở P0; kênh thứ hai theo AA-1110 (≥01/12). |
| D10 | Topic SES feedback 0 subscriber | **Chấp nhận 2 alarm tỉ lệ cho Dev**; đọc qua SQS + job CIS (AA-811 phạm vi 3) khi có gửi thư thật. Không gắn e-mail thẳng. |
| D11 | Activity, ack, rà độ ồn, burn-rate | **Hoãn tới pilot** (P2): trên Dev chưa có dữ liệu để các chỉ số này có nghĩa. |

---

## 7. Nguồn

- `apps/AA-CIS-App/api/services/ops_overview/cloudwatch.py` (tiền tố app dòng 62–73, gom alarm dòng 205–240)
- `apps/AA-CIS-App/frontend/app/admin/overview/_components/AppHealthStrip.tsx`
- `apps/AA-CIS-App/frontend/app/admin/platform/{apps,alerts,infra}/` (`alerts/page.tsx`: Alert recipients, AA-913)
- `apps/AA-CIS-App/api/services/platform_infra.py` (AA-1096 L6)
- `apps/AA-CIS-App/shared/ops_checks.py` (hằng số dòng 70–171), `apps/AA-CIS-App/api/core/ops_metrics_sampler.py`
- `apps/AA-Booking/backend/app/jobs/ops_checks.py`, `apps/AA-Partner/api/app/observability/ops_alerts.py`
- `infra/AA-CIS-Infra/accounts/aa365/{observability.tf,observability_ecosys.tf,alarm_runbooks.tf,outputs_platform_limits.tf,crm_edge.tf}`
- `docs/generated/alarms.md` (OPS-07), `docs/backlog/README.md` (AA-1140/1141/1142 slot S290–S292, AA-1110)
- Đọc live acc2 us-west-1 ngày 21/11/2026: `DescribeAlarms`, `events:ListRules`, SNS `ListSubscriptionsByTopic`
  (bản liệt kê làm việc giữ ngoài repo, trong `.tmp-session/`)
- Thị trường (đọc 21/11/2026): Google SRE book ch. 6 và Workbook ch. 5; CloudWatch pricing; tài liệu API
  `PutAlarmMuteRule`; trang giá PagerDuty, Grafana Cloud, Better Stack; thông báo ngừng bán Opsgenie; trang AWS Systems
  Manager Incident Manager.

---

## 8. Kết quả quyết định (tech lead, 21/11/2026, trang quyết định S287)

10/10 câu theo đề xuất (D8 bỏ: alarm WAF kêu lúc 12:48 là do lượt burst test, đã tự về OK lúc 13:06). Ba ghi chú của tech lead
và câu trả lời:

- **D1 "có bị trùng khi có 2 nơi?"** Không. Chỉ có **một** nguồn: API catalogue và tab Platform › Alerts › Catalogue (danh
  sách đầy đủ, chỉnh, mute). Trang Ecosystem status chỉ hiện **một thẻ tóm tắt** (số alarm đang kêu theo app + link sang
  Catalogue), không có danh sách thứ hai.
- **D5 "lên prod lại phải sửa nữa à, có nên làm luôn, có tốn phí?"** Làm luôn ở P0: tạo sẵn topic thứ hai cho mức `page` và gắn
  tag severity cho mọi alarm ngay bây giờ, để lúc lên prod chỉ thêm người nhận/kênh, không sửa alarm. SNS topic không tính phí;
  e-mail qua SNS miễn phí 1.000 thư/tháng đầu. Chi phí thêm: 0 USD.
- **D11 "chưa hiểu, có tôi mà"**: ack = một người bấm "tôi đang xử lý" để người khác không làm trùng; đo độ ồn = đếm alarm
  kêu mà không ai cần làm gì; burn-rate = cảnh báo theo tốc độ tiêu hao "ngân sách lỗi" khi có người dùng thật; synthetic =
  robot bên ngoài gọi thử trang mỗi phút (~10 USD/tháng). Khi chỉ có tech lead nhận cảnh báo và Dev chưa có người dùng thật,
  các thứ này chưa có giá trị, nên hoãn tới pilot là đúng.
