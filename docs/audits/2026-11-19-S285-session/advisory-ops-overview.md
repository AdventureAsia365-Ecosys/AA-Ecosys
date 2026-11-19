# Tư vấn: trang giám sát toàn hệ sinh thái và một ngày vận hành

*Đọc code main CIS `43d288c5d` (18/11), ảnh audit S283 và hai bản thiết kế độc lập. Lần này chỉ đọc, không gọi AWS hay DB, nên số liệu là theo code, chưa phải giá trị live.*

## 1. Trả lời ngắn

Có cách làm chuyên nghiệp. **Khuyến nghị: biến `/admin/overview` thành một trang trạng thái duy nhất, "Ecosystem status".** Trang chỉ trả lời một câu: *"Bây giờ có gì hỏng hoặc sắp hỏng trong 4 app, và 24h qua đã xảy ra gì?"*

- Trên cùng là **một câu kết luận**: "All systems normal" hoặc "N việc cần anh".
- Tiếp theo là danh sách việc cần xử lý, mỗi dòng có runbook.
- Sau đó là lưới dịch vụ, biểu đồ 24h dùng chung trục thời gian có mốc deploy, hàng job queue, chi tiêu AI so với cap, và timeline sự kiện.

Funnel nội dung, kho atom, tenant và chi phí MTD chuyển sang các trang drill-down sẵn có. Phase 0–3 tốn **0 USD dịch vụ mới**. Các phần trả phí đều là tuỳ chọn, ghi rõ USD/tháng ở mục 7.

## 2. Vì sao trang hiện tại rối

1. **Trộn bốn mối quan tâm trong một trang cuộn.** Trang có ops, tài chính MTD, kho nội dung và tenant. Phần mô tả cũng nói vậy: "business… then the content pipeline" (`frontend/app/admin/overview/messages.ts:16-18`). Tổng cộng 8 card, khoảng 30 con số, khoảng 40 icon (i) SourceHint, nhưng **không có câu kết luận nào ở cấp trang**.
2. **Tám cửa sổ thời gian:** 24h, MTD, tháng trước, 7d, 30d, "today UTC", now, all-time. Không có bộ chọn thời gian chung.
3. **Gần như không có trục thời gian.** Chỉ có 3 sparkline cao 44 px, không trục, mỗi app một thang đo riêng (`overview/_components/AppHealthStrip.tsx:35-62`). 4xx của CIS khoảng 10% nhưng tô xám mờ.
4. **Màu không mang nghĩa trạng thái:** cột vàng "ok", delta xanh "+n/7d", badge đỏ cho số FAILED cộng dồn 30 ngày (`page.tsx:485-519`). Hàng đợi đang chạy, thứ chặn deploy, lại là dòng chữ nhỏ.
5. **Trùng lặp.** Chi phí xuất hiện 3 lần với 3 tổng khác nhau: $47.11, $35.92 và bảng Cost per app (`page.tsx:523-574`, `CostByAppCard.tsx`). Alert lặp lại nội dung chuông thông báo.
6. **Alert là mã thô.** Chỉ hiện `event_type` và `entity_id` (`AlertList.tsx:48-63`), không parse `payload.message`, không dedupe, không có link runbook. Link "Alerts" còn trỏ nhầm sang `/admin/jobs` (`page.tsx:577-583`).
7. **Thiếu phạm vi:**
   - Không có Partner CRM. Prefix alarm chỉ gồm `aa-ecosys/aa-identity/aa-email` (`api/services/ops_overview/cloudwatch.py:67`), thiếu `aa-crm-*` và `aa-sec-*`.
   - Không có ECS/RDS, `booking.job`, `crm.job`, Sentry, CI/guard.
   - TripPlanner đã có `/api/health` nhưng CIS vẫn coi là không có (`api/services/platform_apps.py:26,390`).
8. **Hai kiểu refresh, hai bộ card.** Nửa dưới tự poll 60 s (`page.tsx:297`), nửa trên không bao giờ poll (`:303`). Có hai cặp component tự chế, Section/Stat (`page.tsx:135-250`) và OpsCard/Kpi (`opsUi.tsx:46,151`), thay vì dùng kit.
9. **Ngưỡng hard-code:** `WARN_ERROR_RATE_PCT = 1.0` (`cloudwatch.py:36`).

## 3. Nguyên tắc thiết kế trang giám sát chuyên nghiệp

- **Alert-first, xanh thì im lặng.** Đây là cách của Statuspage/NOC và "management by exception". Phần khoẻ gom lại thành 1 dòng xanh; chỉ phần vượt ngưỡng mới mở ra.
- **Golden signals.** Dịch vụ nhận request theo RED (Rate, Errors, Duration, theo Tom Wilkie, Grafana Labs). Tài nguyên RDS, ECS và job queue theo USE (Utilisation, Saturation, Errors, theo Brendan Gregg). Cả hai bắt nguồn từ bốn golden signals trong *Google SRE Book*, chương "Monitoring Distributed Systems".
- **Mỗi widget trả lời đúng một câu hỏi**, và tiêu đề chính là câu trả lời, ví dụ "Jobs: queue clear, 2 failed in 24h". Đây là tinh thần của Stephen Few, *Information Dashboard Design*.
- **Chỉ một khung thời gian: "now + 24h"**, giờ ICT. Mọi biểu đồ dùng chung trục x, crosshair, **mốc deploy** và dải thời gian alarm firing, như hướng dẫn dashboard của Grafana. Nhìn vào là trả lời được "deploy có gây ra lỗi không".
- **SLO và error-budget burn rate**, theo *SRE Workbook*, chương "Alerting on SLOs". Trên Dev gắn nhãn "Dev numbers".
- **Ngưỡng là setting**, đặt trong namespace `cis.ops.*` theo mẫu `cis.delivery.*`. Tín hiệu nào đã có CloudWatch alarm thì lấy **trạng thái alarm** làm verdict, không chép ngưỡng Terraform sang một setting thứ hai.
- **Màu chỉ mang nghĩa trạng thái** (đỏ, vàng, xanh, xám khi không có dữ liệu hoặc stale). Không dùng gauge hay pie; dùng bullet bar có vạch cap.
- **Mỗi số có ngữ cảnh**: ngưỡng, thời điểm "as of" và link drill-down. Tín hiệu chưa nối thì hiện pill xám "not measured yet", để chỗ trống không bị đọc nhầm thành xanh.
- **Chỉ dùng kit (ADR 0016).** Thêm vào `_kit/core` ba primitive dùng lại được: `Sparkline24h`, `UptimeStrip`, `EventStrip`.

## 4. Bố cục đề xuất (từ trên xuống)

```
[Z0] Ecosystem status · Dev · "Now + last 24h (ICT)" · Updated 08:52 · auto 60s · [Refresh] · [Sources & freshness]
[Z1] ● All systems normal — 4 apps · 8 ECS services · 3 queues · 0 alarms · deploy gate OPEN
     (khi lỗi) ▲ 2 việc cần anh: [SEV2] câu dễ đọc · since 06:40 · ×3 · [Runbook] [Open] [Ack]   (tối đa 5–8 dòng)
[Z2] App tiles 2×2: CIS · TripPlanner · Booking · Partner CRM
     pill + lý do | Requests 24h · 5xx% · p95 (+4xx% khi vượt ngưỡng) | line 24h chung trục + mốc deploy
     dòng "24h activity" | Deployed <sha> · api 1/1 · worker 1/1 · ready ✓
[Z3] Services & data grid (gom lại khi xanh): 8 ECS services · 2 Lambda TP · RDS
     running/desired · rollout · image sha · uptime strip 24h | RDS: CPU · conn% · free GiB · XID age
[Z4] 24h golden signals 2×2: Traffic · 5xx% (vạch warn/crit) · p95 · Queue backlog
[Z5] Job queues: shared.job · booking.job · crm.job — queued · running · oldest wait · failed 24h · workers | chip Deploy gate
[Z6] AI spend 24h: bullet bar từng app so với daily cap + sparkline giờ | trạng thái provider | 1 dòng "Tháng: $x · forecast $y / budget $z"
[Z7] Event timeline 24h: làn Deploys · Alarms · Ops checks · Guards/probes · Cap hits + list 10 dòng
[Z8] Delivery & nightly guards: 6 repo (main xanh/đỏ, deploy gần nhất) + ô từng guard đêm
[Footer] Nguồn/độ tươi mỗi section · link drill-down · danh sách "not measured yet"
```

| Widget | Câu hỏi | Biểu đồ | Nguồn | Trạng thái |
|---|---|---|---|---|
| Verdict + Needs attention | Có gì cần người xử lý, làm gì? | Banner + DataTable SEV | Hàm verdict mới đọc alarm, `shared.notifications` (parse message), deploy gate | Thiếu (ghép từ phần đã có) |
| App tile ×4 | App có sống, nhanh, ít lỗi không? | Stat + line 24h | `app_health.traffic_section`, `platform_apps.collect_apps`; CRM qua ALB target group | Có 3 tile, thiếu CRM |
| Dòng activity 24h | App có làm việc thật không? | Dòng chữ | CIS publish/review; Booking `v_ops_funnel_daily`/`v_ops_inquiry_inbox` (đơn vị ngày); CRM cần M2M | CIS/Booking có; CRM chưa đo |
| Service grid + uptime | Có runtime nào lệch version, rollout kẹt hay sập trong ngày? | Status grid + strip | ECS DescribeServices (IAM sẵn), `shared.ops_sample` mới | Thiếu |
| RDS USE | DB sắp chạm giới hạn chưa? | KpiTile + sparkline | GetMetricData AWS/RDS lúc mở trang; sampler (role conn, XID) | Thiếu UI, alarm đã có |
| 5xx / p95 / 4xx | Có lỗi hay chậm sau deploy không? | Line small-multiples | API GW, Lambda, ALB qua GetMetricData | Có một phần |
| Job queues | Job có chảy không, gate có mở không? | Bảng + bar 24h | `shared.job`; `booking.job` cần view; `crm.job` cần M2M | Chỉ có CIS |
| AI spend vs cap | App nào sắp chạm cap ngày? | Bullet bar | `llm_call_log`, `spend_budget` | Có dữ liệu, thiếu UI |
| Event timeline | Đêm qua xảy ra gì, theo thứ tự? | EventStrip + list | `shared.ops_event` mới (sampler diff DescribeAlarms), summary.json | Thiếu |
| Delivery & guards | Main có xanh không, guard đêm có pass không? | Grid | summary.json; `services/reports/probes.py` | Repo có; guard chưa có trang |
| Sentry new issues | Có exception mới không? | Số trong tile | Sentry API | **Trả phí, cần "yes"** |

**Đã loại khỏi hai bản thiết kế**:

- Dòng Vercel booking-admin: admin đã chạy trên ECS, không có nguồn đọc.
- "Quotes sent": chưa thấy view nào cấp số này.
- Toggle 6h/24h: không cần, giữ cố định 24h.

## 5. Một ngày vận hành của tech lead (giờ ICT)

| Giờ | Việc | Phút | Khi nào hành động / runbook |
|---|---|---|---|
| 08:00 | Đọc digest OPS-12 (đến lúc 01:00 UTC), mở trang: verdict → Needs attention → timeline đêm | 5–10 | Có dòng đỏ thì vào incident mode (`docs/ops/incident-response.md:23-27`). Đỏ trùng mốc deploy thì rollback theo `docs/ops/runbooks/rollback-*.md` |
| 08:10 | Z5/Z6: queue có wait không, RDS, spend so với cap, provider circuit | 5 | App ≥80% cap trước trưa thì vào AI gateway › Budgets. Kết nối DB >80% thì làm theo `docs/ops/database-operations.md` |
| Trước mỗi wave merge | Gate OPEN, main xanh, không alarm | 2 | Gate đóng thì chờ. Không override nếu chưa có lý do do tech lead ghi (DM-11.4) |
| +10–15′ sau deploy | SHA mới, rollout COMPLETED; 5xx/p95 sau mốc deploy | 3 | Vượt ngưỡng crit thì rollback (aa-ship) và ghi lesson |
| 13:00 | Hàng guard đêm (chạy khoảng 10:45–12:40 ICT, thường trễ) | 5 | Isolation probe đỏ là SEV1. Drift hoặc copy-guard đỏ thì xử lý trong ngày. Ô xám thì chạy lại workflow |
| Khi chạy wave hoặc batch trả phí | Liếc Z5/Z6 mỗi 30–60 phút | 2 | Spend vượt 3× median hoặc chạm cap thì dừng wave (aa-wave-rerun) |
| 17:30 | Không còn dòng đỏ/vàng nào chưa có chủ, không job nào chặn deploy đêm | 10 | Ghi sự cố vào log phiên |
| Thứ Hai | SLO/burn, alert-noise review (check nào kêu quá 3 lần mà không ai hành động thì chỉnh trong Settings), pg_stat_statements, DORA | 30 | — |
| Đầu tháng | Đối soát chi phí (C8), capacity; mỗi quý thêm review quyền (DM-8.10) | 60 | — |

Business owner chỉ cần đọc verdict và 4 dòng "24h activity" trên điện thoại, khoảng 1 phút.

## 6. Lộ trình (mỗi phase giao trong 1 phiên)

- **Phase 0, sửa nhanh (1 PR CIS, 0 USD):**
  - Thêm lọc `tenant_id` cho `rev_c` (`admin_overview.py:72-78`).
  - Thêm prefix `aa-crm-`/`aa-sec-` (`cloudwatch.py:67`).
  - Alert hiện message dễ đọc, sửa link.
  - Công nhận health của TripPlanner.
  - Migration `455_*` seed `cis.ops.*`, bỏ hằng số `WARN_ERROR_RATE_PCT`.
  - Cho agent review trước khi merge vì có schema/settings.
- **Phase 1, trang mới trên dữ liệu đã có (0 USD):**
  - `GET /admin/overview/status` trả các section `{status, as_of, data}`, mỗi section có TTL riêng và giữ giá trị last-good (tái dùng `ops_overview/cache.py:54-116`).
  - `services/ops_status/verdict.py` có unit test.
  - Viết lại `page.tsx` thành Z0–Z3 (chưa có history), Z5 (chỉ CIS), Z6, Z7 (dạng list), Z8. Chỉ dùng kit.
  - Chuyển funnel, intelligence và tenant sang tab "Content pipeline" của `/admin/data-coverage`. Xoá B2C ẩn, card trùng và SourceHint.
- **Phase 2, collector 0 USD:**
  - Migration `shared.ops_sample` (giữ 14 ngày) và `shared.ops_event` (giữ 30 ngày).
  - Mở rộng `api/core/ops_metrics_sampler.py` (tick 300 s): /health của 4 app, DescribeServices cho 8 service, queue, role connection/XID, diff trạng thái alarm.
  - Sửa `describe_ecs` từ 5 lên 8 service (`services/reports/delivery.py:457-499`). Bỏ `/admin/infra/status`: nó so với ECR `:latest`, điều không bao giờ đúng (`metrics.py:450`).
  - Đọc RDS và ALB 24h bằng GetMetricData **lúc mở trang**, cache 5 phút.
  - Thêm 3 kit primitive. Mở Z4 và uptime strip.
- **Phase 3, contract liên app (0 USD, review rủi ro theo D-13):**
  - Booking: `bk-NNN` tạo view `booking.v_ops_job_summary` (chỉ đếm), GRANT cho `cis_app`.
  - Partner + Infra: Cognito M2M client-credentials chỉ đọc cho `crm.ops.v1` (`/jobs/summary`, `/llm/usage`, endpoint mới `/ops/activity-24h`).
  - Infra: probe isolation và schema dump in ra dòng verdict để parse được.
- **Phase 4, polish:**
  - OPS-12 digest và snapshot OPS-15 dùng chung hàm verdict.
  - Chạy aa-ui-verify (375 px, light/dark).
  - Viết trang docs "How to read the status page" (EN + `.vi.md`).
  - Cho `/admin/platform` trỏ về trang này.
  - Sau 2 tuần, chỉnh các ngưỡng gây nhiễu.

## 7. Chi phí

| Hạng mục | USD/tháng |
|---|---|
| ECS DescribeServices, DescribeAlarms, probe /health, bảng sample/event trên RDS hiện có | 0 |
| GetMetricData thêm khoảng 40 metric RDS/ALB, đọc lúc mở trang, cache 5 phút | < 1 (cộng thêm vào mức tệ nhất ~0.60 hiện nay) |
| Cognito M2M client | 0 ở lưu lượng này |
| *Tuỳ chọn:* Secret chứa Sentry read token | ~0.40 |
| *Tuỳ chọn:* SNS→SQS cho security events | ~0, nhưng là resource mới |
| *Không khuyến nghị:* Route 53 health check / CloudWatch Synthetics | 0.50–0.75 mỗi check (~6–9 cho 12 runtime) / ~10 mỗi canary |

Lấy mẫu CloudWatch liên tục 24/7 tốn khoảng 3.50 USD/tháng, nên đề xuất đọc lúc mở trang.

## 8. Quyết định cần tech lead chốt

1. **Overview chỉ là trang trạng thái; nội dung, tài chính và tenant chuyển sang drill-down?** Đề xuất: **Có.**
2. **Có giữ 1 dòng "tháng: forecast so với budget" không?** Đề xuất: **Giữ.** Budget tính theo tháng và business owner cần dòng này. Bảng MTD chỉ để ở `/admin/spend`.
3. **Namespace settings:** đề xuất **`cis.ops.*`**. Tín hiệu đã có alarm thì dùng trạng thái alarm, không lặp ngưỡng.
4. **Endpoint:** đề xuất **`/admin/overview/status`**, dùng chung hàm verdict với digest.
5. **History:** đề xuất **sampler tự viết + đọc CloudWatch lúc mở trang (0 USD)**, không dùng Synthetics.
6. **Contract liên app (Booking view, CRM M2M):** đề xuất **làm ở Phase 3**, review rủi ro trước khi merge.
7. **Sentry token (~0.40 USD/tháng):** đề xuất **Yes**. Đây là tín hiệu duy nhất bắt được exception mà HTTP status không thấy.
8. **SNS→SQS cho security events:** đề xuất **làm sau khi lên prod**. Trên Dev, email SNS là đủ.
9. **Ngưỡng mặc định:**
   - 5xx: warn 1% / crit 5%; 4xx: warn 10%.
   - p95: warn 1500 / crit 3000 ms.
   - Queue wait: warn 15 / crit 60 phút.
   - RDS CPU: warn 70%; free storage: warn 15 GiB.
   - Bỏ tính tỉ lệ khi < 50 request.
   - Đề xuất: **dùng các số này, chỉnh lại sau 2 tuần.**
