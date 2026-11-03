---
id: OPS-08-s265-capacity-review-2026-10
title: Cost and capacity review 2026-10 (final)
description: "Final October 2026 review: 482.77 USD (AWS acc2 213.87 + AI outside AWS 268.85 + management 0.04) vs 177.74 in September, driven by two catalogue rewrites and new always-on services; every flagged jump explained by usage type except inter-AZ traffic and part of API Gateway."
type: report
status: draft
owner: nghiep
audience: [owner, engineer, cto, cio, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-03
review_every_days: 30
related: [FIN-02, OPS-08, FIN-01, OPS-08-s262-capacity-review-prelim, OPS-08-s263-alerting-cost, AA-896, AA-838, AA-884, AA-828]
---

# Rà soát chi phí và dung lượng tháng 10/2026 (bản chính thức)

> [!NOTE]
> **BẢN CHÍNH THỨC** của tháng 10/2026, thay bản sơ bộ ngày 01/11
> ([S262](../2026-11-01-S262-capacity-review/README.md)). `status: draft` chỉ có nghĩa là tech lead chưa đọc
> (schema front-matter không có giá trị "final"). Cost Explorer đọc lại **02/11 23:33 UTC ≈ 48 giờ sau cuối tháng**,
> cả acc2 (theo tag `App` và theo dịch vụ) lẫn acc3. Mọi số là môi trường **Dev**, chưa có khách thật: chỉ để xem
> xu hướng, không dùng để lập kế hoạch.

- Phiên: S265, 03/11/2026. Tác nhân: Claude Code (subagent; chỉ đọc file local + 3 lệnh Cost Explorer chỉ đọc). Mẫu:
  [`templates/cost-report.md`](../../templates/cost-report.md). Runbook: [`ops/finops.md`](../../ops/finops.md#monthly-review),
  [`ops/cost/README.md`](../../ops/cost/README.md).
- Nguồn số liệu:
  - 3 bundle của `tools/finops/collect_month.py` (CIS, Booking, CRM) do phiên điều phối chạy qua `tools/ecs/ecsx.sh`
    lúc **02/11 23:31–23:34 UTC**, sau khi làm mới snapshot SERVICE (acc2 + acc3) và snapshot tag `App` (acc2) cho
    tháng 10 bằng đúng hai lệnh của `POST /admin/cost-explorer/check` (≈ 0.03 USD). Bản sao ở [`data/`](data/).
  - `tools/finops/monthly_cost_report.py --mgmt-usd 0.04 --mgmt-prev-usd 0 --budget-usd 300` soạn các bảng.
  - Subagent này gọi thêm **3 lệnh Cost Explorer chỉ đọc trên acc2** (0.03 USD): usage type tháng 9 + 10 của 7 dịch vụ
    bị gắn cờ, usage type theo ngày tháng 10 cho 10 usage type, và `get-anomaly-monitors`. Kết quả hai lệnh đầu ở
    [`data/acc2-usage-type-2026-09-10.csv`](data/acc2-usage-type-2026-09-10.csv) và
    [`data/acc2-daily-usage-2026-10.csv`](data/acc2-daily-usage-2026-10.csv). Hai lệnh nữa (danh sách subscription và
    anomaly tháng 10) **không chạy được**: phiên MFA hết hạn giữa chừng, lệnh dừng ở bước hỏi mã, không gửi tới AWS.
  - Lý do từng bước nhảy: log phiên `docs/sessions/2026-10-*.md`, `2026-11-0*.md`, bản sơ bộ S262, audit cảnh báo
    [S263](../2026-11-01-S263-alerting-cost/README.md) và báo cáo [S248](../2026-10-23-S248-cost-report/README.md).
    Chỗ không chứng minh được ghi **"chưa rõ"** kèm cách kiểm.
- Không gọi LLM, không ghi gì lên AWS, không ECS exec trong lane này.

## Tóm tắt cho chủ doanh nghiệp (VI)

1. Tổng chi phí tháng 10/2026: **482.77 USD** (hạ tầng AWS 213.87 USD, AI tính ngoài hoá đơn AWS 268.85 USD, tài khoản quản lý AWS 0.04 USD). Đây là mức **sử dụng**; phần AI trên tài khoản AI ngày 01–28/10 (khoảng 236 USD) do nhà cung cấp cũ trả trong thời gian tài khoản còn ở tổ chức của họ, nên tiền công ty thực trả cho tháng 10 thấp hơn khoảng 236 USD.
2. So với tháng 09/2026 (177.74 USD): **+171.6 %** (gấp khoảng 2.7 lần).
3. Thay đổi lớn nhất: CIS (content + catalog) +263.50 USD; lý do: AI viết lại toàn bộ catalogue tour hai lần trong tháng (đầu tháng chạy lại 14 nước, 24–25/10 viết lại 810 tour), dựng thẻ địa điểm và các vòng thử chất lượng bài viết (AI 269 USD); hạ tầng AWS tăng 79 USD vì có thêm hệ thống đặt tour, CRM cho đại lý, máy chạy việc nền riêng, cơ sở dữ liệu lớn hơn kèm bản sao lưu trước mỗi đợt viết lại, khoảng 100 cảnh báo và gần 50 khoá bảo mật.
4. Ngân sách AWS tháng: đã dùng 213.87 / 300.00 USD (71 %), còn 86.13 USD; tài khoản AI dùng 236.27 / 250 USD (94 %), không vượt; từ 29/10 tài khoản AI tự trả (0.20 USD tới 31/10).
5. Chi phí mỗi tour xuất bản: 0.34 USD (riêng AI 0.30 USD); số liệu môi trường Dev, chỉ để xem xu hướng. Tháng 11 dự kiến thấp hơn: không còn đợt viết lại cả catalogue và số cảnh báo đã giảm từ 101 xuống 27 ngày 01/11. Cần quyết định: không có.

## Khác bản sơ bộ (01/11 → 03/11)

| Line | Sơ bộ 01/11 | Chính thức 03/11 | Δ | Vì sao |
|---|---:|---:|---:|---|
| acc2 (AWS, every App tag) | 202.85 (01–30/10) | **213.87** (01–31/10) | +11.02 | Day 31/10 added (≈ 7–8 USD/day at the late-October rate) plus Cost Explorer revising the last days upward |
| acc3 Bedrock (Cost Explorer) | 236.16 (fetched 27/10) | **236.27** (fetched 02/11) | +0.11 | Re-read for the whole month: Cost Explorer adds only 0.11 USD after 26/10 (see "LLM" below) |
| Management account | not included | **0.04** | +0.04 | Read in its own account (runbook step 3) |
| LLM outside acc2 (gateway) | 268.85 | 268.85 | 0 | The gateway ledger was already complete on 01/11 |
| **Total** | **471.70** | **482.77** | **+11.07** | |
| Untagged acc2 | 104.36 | 106.51 | +2.15 | |
| Unit cost per booking / trip case | 0.57 / 0.25 | 0.61 / 0.27 | | booking AWS 5.68 → 6.11 |
| WAF change vs September | +19.6 % | +27.7 % | | Now over the 20 % flag (identity web ACL, full last week) |

The "chưa rõ" items of the preliminary report and where they stand now:

| Item (S262) | Status 03/11 | Answer |
|---|---|---|
| RDS above the t4g.small run-rate on 23–30/10 | **Explained** | See RDS reason: backup storage beyond the free allowance grew from ≈ 0.3 to 2.4 GB-month per day after the 20 `pre-s1` snapshots; plus 11.2 h of a `db.t4g.micro` on 23–24/10 (the point-in-time restore drill) |
| CloudWatch rate 23–30/10 ≈ 2.7 × earlier | **Explained** | Billed alarms grew from ≈ 18 to ≈ 100 and custom metrics from ≈ 10 to ≈ 55 during the month; acc2 gets no CloudWatch free tier (S263 audit) |
| API Gateway +517 % | **Mostly explained** | REST requests ×6.8 and 13.1 GB data out; the source of the steady 15–20k requests/day after 25/10 is likely but not proven |
| S3 +423 % | **Mostly explained** | Photo storage and reads; the 28–31/10 write bursts are still unknown (0.10 USD) |
| EC2 - Other +104 % | **Measured, source unknown** | Inter-AZ traffic (449 GB, 4.49 USD) with the same amount on the ECS line; ≈ 20 GB/day from 14/10 |
| Untagged split before / after 16/10 | **Chưa rõ** | Needs one daily App-tag pull; not done (request cap of this lane) |
| Per-App budget alerts, acc3 80 % e-mail, organization budget | **Chưa rõ** | No mailbox access in this lane; see "Budgets and anomalies" |
| Per-model LLM split | **Chưa rõ** | Needs an acc3 read (not allowed in this lane); S248 split for 01–22/10 still the best available |
| DataForSEO and geocoder spend | **Chưa rõ** | Needs `shared.dfs_call_log` / `geo.geocode_call` totals through ECS exec (orchestrator) |
| acc3 invoice and credits | **Chưa rõ** | Not read |

## Totals by account

| Account | 2026-08 | 2026-09 | 2026-10 | Change 09 → 10 | Note |
|---|---:|---:|---:|---:|---|
| acc2 (infra, all App tags) | 140.22 | 134.96 | **213.87** | +58.5 % | Cost Explorer, days 01–31/10, fetched 02/11 23:33 UTC. 6.90 USD/day (Sep 4.50) |
| acc3 (LLM, Bedrock, Cost Explorer) | 22.40 ¹ | 51.37 | **236.27** | +359.9 % | Fetched 02/11 23:33 UTC. Gateway estimate 248.33 |
| Retired account (former LLM fallback) | 45.15 ¹ | 0.89 | 0.69 | −22.9 % | Removed from the ecosystem 28/10 |
| Management account (org trail, KMS, budgets) | — | 0.00 | **0.04** | new | Created 30/10; read in its own account |
| LLM outside acc2 (gateway, every provider) | n/a | 42.78 | 268.85 | +528.5 % | acc3 Bedrock + Jev + OpenAI + retired account, from `shared.llm_call_log` |
| **Total (acc2 + LLM outside acc2 + management)** | n/a | **177.74** | **482.77** | **+171.6 %** | AA-884 rule (acc2 Bedrock counted once): 482.73 without the management account |

¹ August acc3 and retired-account figures from the S248 report (Cost Explorer read 23/10): the stored acc3 snapshot
holds only 0.42 USD for August (a partial fetch of 29/09). The acc2 August figure (140.22) is now in the stored
snapshot too (refetched 02/11) and matches S248.

## By app (tag `App`)

The `App` tag counts only from **15–16/10** (AA-828); everything before sits in "Not assigned". App lines are about
half a month (16–31/10). The "≈ full month" column is the 16–31/10 rate × 31/16, or per active day for services that
started later: a rough guide for November, not a forecast.

| App | 2026-10 (USD) | 2026-09 | AWS | LLM | ≈ full month AWS at the late-October rate | Biggest AWS lines |
|---|---:|---:|---:|---:|---:|---|
| CIS (content + catalog) | 304.83 | 41.33 | 36.01 | 269.32 | ≈ 70 | ECS 24.34, ElastiCache 8.07, Secrets 1.44, ECR 0.75, API GW 0.74 |
| Partner CRM | 6.63 | 0.00 | 6.63 | 0.00 ² | ≈ 25 (services from 23–26/10) | ECS 3.66, Secrets 1.28, KMS 0.88, Bedrock Guardrail 0.37, CloudFront 0.32 |
| Booking | 6.11 | 0.00 | 6.11 | 0.00 | ≈ 12 | ECS 5.63, Secrets 0.35, API GW 0.07 |
| TripPlanner | 0.81 | 1.45 | 0.79 | 0.03 | ≈ 1.5 | Secrets 0.64, S3 0.10, API GW 0.04; Lambda ≈ 0 |
| Shared platform | 55.21 | n/a | 55.21 | 0.00 | ≈ 107 | RDS 20.47, ELB 20.00, WAF 5.49, EC2-Other 4.84, EC2 2.03, CloudWatch 1.69 |
| Staff sign-in (identity) | 2.46 | n/a | 2.46 | 0.00 | ≈ 9–10 (WAF from 24–25/10) | WAF 2.08, Secrets 0.38 |
| Tags `platform` / `ecosystem` | 0.16 | n/a | 0.16 | 0.00 | — | Tag values outside DM-10.1 (S248 F6) |
| Not assigned to an app | 106.51 | 134.96 | 106.51 | 0.00 | chưa rõ ³ | ECS 21.30, CloudWatch 17.82, ELB 17.81, VPC 11.17, RDS 10.32, ElastiCache 7.70, Secrets 7.28, WAF 4.52 |

² The CRM's own gateway logged 2 calls, 0.0001 USD (Guardrail scrub + a stub model).
³ The bundle has no daily App split. Known untagged after 16/10: all public IPv4 (VPC 11.17 for the whole month),
90 % of CloudWatch (alarms without `App`), 62 % of Secrets Manager, short ECS tasks, Cost Explorer requests (0.68).

## Month over month

| Line | 2026-08 | 2026-09 | 2026-10 | Change, last month |
|---|---:|---:|---:|---|
| AWS acc2 | 140.22 | 134.96 | 213.87 | +58.5 % |
| acc3 Bedrock (Cost Explorer) | 22.40 ¹ | 51.37 | 236.27 | +359.9 % |
| LLM, all apps (gateway estimate) | n/a ⁴ | 42.79 | 269.35 | +529.5 % |
| — of which CIS | n/a | 41.34 | 269.32 | +551.5 % |
| **Total (AWS acc2 + LLM outside AWS)** | n/a | 177.74 | 482.73 | +171.6 % |

⁴ `shared.llm_call_log` starts on 17/09, so there is no August LLM row.

Top acc2 services, with the per-tag split of October (bundle `data/cis.txt`):

| Service | 2026-08 | 2026-09 | 2026-10 | Change | cis | booking | crm | shared / identity | untagged |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Elastic Container Service | 21.54 | 21.13 | 54.92 | **+159.9 %** | 24.34 | 5.63 | 3.66 | — | 21.30 |
| Elastic Load Balancing | 37.61 | 36.41 | 37.82 | +3.9 % | — | — | — | 20.00 | 17.81 |
| Relational Database Service | 20.82 | 20.39 | 30.80 | **+51.0 %** | — | — | — | 20.47 | 10.32 |
| CloudWatch | 6.92 | 7.86 | 19.90 | **+153.0 %** | 0.30 | 0.03 | 0.04 | 1.69 | 17.82 |
| ElastiCache | 16.37 | 15.84 | 15.77 | −0.5 % | 8.07 | — | — | — | 7.70 |
| WAF | 9.37 | 9.46 | 12.09 | **+27.7 %** | — | — | — | 5.49 + 2.08 | 4.52 |
| Secrets Manager | 3.61 | 4.42 | 11.72 | **+165.2 %** | 1.44 | 0.35 | 1.28 | 0.19 + 0.38 | 7.28 |
| VPC (public IPv4) | 11.17 | 10.81 | 11.17 | +3.4 % | — | — | — | — | 11.17 |
| EC2 - Other | 3.21 | 3.44 | 7.37 | **+114.5 %** | — | — | — | 4.84 | 2.53 |
| EC2 - Compute (NAT instance) | 3.72 | 3.98 | 4.06 | +2.0 % | — | — | — | 2.03 | 2.03 |
| API Gateway | — | 0.38 | 2.43 | **+534.6 %** | 0.74 | 0.07 | — | — | 1.58 (+ TripPlanner 0.04) |
| S3 | — | 0.23 | 1.33 | **+470.4 %** | 0.32 | 0.00 | 0.06 | 0.12 | 0.72 (+ TripPlanner 0.10) |
| ECR | — | 0.47 | 1.06 | **+122.9 %** | 0.75 | 0.02 | 0.03 | — | 0.27 |

## Top 5 services and changes over 20 %

Usage types: [`data/acc2-usage-type-2026-09-10.csv`](data/acc2-usage-type-2026-09-10.csv) (September → October, USD
and quantity); daily: [`data/acc2-daily-usage-2026-10.csv`](data/acc2-daily-usage-2026-10.csv).

| Service | This month | Last month | Change | Reason |
|---|---:|---:|---:|---|
| Elastic Container Service | 54.92 | 21.13 | +159.9 % | **Explained.** x86 Fargate 362 → 818 vCPU-hours (+21.21 USD) and 725 → 1,636 GB-hours (+4.65): `aa-cis-dev-worker` always on from 05/10 (S210), `aa-booking-dev-api` from 14/10 (S235), api/worker autoscaling during the waves, short DB Migrate / Schema Dump tasks. New ARM Fargate 3.55 USD (on-demand 53.5 vCPU-h + Spot 82.3 vCPU-h): the three CRM services from 23, 24 and 26/10. Inter-AZ data transfer 54 → 465 GB (+4.11 USD): see EC2 - Other |
| Elastic Load Balancing | 37.82 | 36.41 | +3.9 % | Flat: one ALB + one NLB for the VPC link (S248 §4) |
| Relational Database Service | 30.80 | 20.39 | +51.0 % | **Explained.** Instance `db.t3.micro` 343.5 h (8.24 USD) until the resize on 15/10, then `db.t4g.small` 400.3 h (17.21 USD, 0.043 USD/h ≈ 31–32 USD per full month); storage gp3 20 GB 2.80 (flat); backup storage beyond the free allowance 3.7 → 24.3 GB-month (0.35 → 2.31 USD), from ≈ 0.3 GB-month/day before 24/10 to 2.4/day on 30–31/10 after the 20 manual snapshots `aa-cis-dev-db-pre-s1-*` (one per S1 wave, S249–S250) and the DB Migrate snapshots; `db.t4g.micro` 11.2 h on 23–24/10 (0.23 USD): the point-in-time restore drill (AA-829, PITR 21′20″, S249). At the end-October backup level a full month costs ≈ 6.8 USD of backup storage until the `pre-s1` snapshots expire (30-day rule, ≈ 23–25/11) |
| CloudWatch | 19.90 | 7.86 | +153.0 % | **Explained** (with the [S263 alerting audit](../2026-11-01-S263-alerting-cost/README.md)). Custom metrics 7.5 → 27.8 metric-months (2.25 → 8.22 USD), alarms 18.0 → 51.9 alarm-months (1.68 → 5.08 USD): alarms grew from ≈ 18 to ≈ 100 and billed custom metrics from ≈ 10 to ≈ 55 through October (daily billed quantity × 30; S263 counted ≈ 30 metric names, each dimension set is billed apart) (RDS S237, jobs S240, Cognito S241, backup S249, CRM S255, TripPlanner S257), billed from the first one (acc2 gets no CloudWatch free tier). Dashboard 2.32 (flat), vended logs (VPC flow 1.79, WAF 1.19), log ingest 0.98, Logs Insights scanned 0.27. **After 01/11** the alert diet left 27 alarms and no dashboard (Infra #586, S263): the S263 target for November is ≈ 6 USD for alerting, plus ≈ 4–5 USD of logs |
| ElastiCache | 15.77 | 15.84 | −0.5 % | Flat; Redis replaced by Valkey `cache.t3.micro` on 24–25/10 with no parallel run (S250) |
| Secrets Manager | 11.72 | 4.42 | +165.2 % | **Explained.** 11.0 → 28.7 secret-months (11.48 USD): Booking, staff identity, CRM (web, M2M client, six e2e users, mail OAuth), TripPlanner Cognito keys, Redis AUTH; ≈ 49 secrets at month end = ≈ 19.6 USD per full month. API requests 4,332 → 47,898 (0.24 USD): more services and more task starts (not split by caller) |
| API Gateway | 2.43 | 0.38 | +534.6 % | **Mostly explained.** REST requests 51k → 349k (0.18 → 1.22 USD); data out 0.3 → 13.1 GB (1.18 USD), 11 GB of it on 01–15/10 (peaks 03, 08, 10 and 13/10, during the 14-country re-run and the review pages): the route that returned it is **chưa rõ**. HTTP API requests fell 154k → 28k (probably TripPlanner's HTTP API). From 25/10 the REST API carries a steady 15–20k requests/day even with no wave running; likely source (not proven): the CRM portal service, live on ECS from 26/10, calls the CIS API server to server through the public host (`crm_portal.tf`). Check with the API Gateway access log by route |
| S3 | 1.33 | 0.23 | +470.4 % | **Mostly explained.** Storage 1.7 → 10.1 GB-month (0.26 USD): Drive → S3 photo sync on 01/10 (11,236 PUT requests that day, S207); reads (GET) 18k → 220k (0.10), 95 % of them from 14/10; data out 0.2 → 5.4 GB (0.48), nearly all from 14/10 (likely photos served to the front ends); PUT/LIST 30k → 88k (0.49), with bursts of 6–12k/day on 28–31/10 whose source is **chưa rõ** (≈ 0.10 USD) |
| EC2 - Other | 7.37 | 3.44 | +114.5 % | **Measured, source chưa rõ.** EBS gp3 30 GB of the NAT instance 2.88 (flat). Inter-AZ data transfer 53 → 449 GB (0.52 → 4.49 USD), with the same 465 GB on the ECS line: traffic between Fargate tasks and the NAT instance in the other Availability Zone (the VPC has only the S3 gateway endpoint, so every other AWS API and the internet go through the NAT instance). ≈ 1–10 GB/day on 01–13/10, ≈ 20 GB/day from 14/10 (peak 31 on 23/10), unchanged on 29–31/10 when the LLM traffic had stopped: so it is not LLM traffic. ≈ 12–13 USD per full month on both lines together at this rate (finding P9) |
| ECR | 1.06 | 0.47 | +122.9 % | Inferred, usage type not pulled: image storage grows with every deploy (immutable `dev-<sha>` tags, CIS + Booking + three CRM images) |
| WAF | 12.09 | 9.46 | +27.7 % | The web ACL `aa-identity-dev-pools` from 24–25/10 (S250, 2.08 USD in October, ≈ 9 USD per full month list price); the rest flat. Usage type not pulled |

## LLM spend

### +529.5 % on the gateway log, +359.9 % on Cost Explorer

- **Read the Cost Explorer figure for the trend.** The September gateway log is incomplete (starts 17/09; rows lost
  until 09/10, AA-756): acc3 in the log 40.37 vs 51.37 USD in Cost Explorer. Since AA-927 (S246) one call writes
  exactly one row.
- **Gateway vs Cost Explorer, October (acc3):** gateway estimate 248.33, Cost Explorer 236.27 (refetched 02/11):
  the gateway is **12.06 USD (5.1 %) above** the bill. The preliminary report expected the gap to close once Cost
  Explorer had the last days; it did not: Cost Explorer added only 0.11 USD between the 27/10 fetch and the 02/11
  fetch. Either acc3 spend after 26/10 really was small, or the gateway's price table overestimates some calls
  (cache reads, the Sonnet 5.5 price). Split by day and model: **chưa rõ** (one acc3 daily pull, ≈ 0.01 USD, plus the
  gateway by day). The nightly `llm_cost_reconcile` job (D6, from 01/12) is the standing check.
- **By pipeline family (CIS, October, gateway):** unchanged from the preliminary (the ledger was complete on 01/11):
  S1 rewrite 117.80 USD (44 %: re-run of 14 countries 01–10/10 and the 810-tour rewrite 24–25/10, 59.34 USD), legacy
  `t5_atomize` 42.32 (16 %), tenant series 35.29 (13 %), ad-hoc runs 35.41 (13 %), places 23.88 (9 %), `a3_atomize`
  5.34, segment / demand / question 7.39, other 1.91. Detail per family and run: [S262](../2026-11-01-S262-capacity-review/README.md#explanations-in-more-detail).
- **By provider (CIS):** acc3 Bedrock 248.31 USD (67,091 calls), Jev 19.10 (288,883 calls), OpenAI 0.73, retired
  account 0.69, acc2 Bedrock 0.49.
- **After 29/10:** acc3 refuses every Bedrock model (Error 002), so LLM spend there is ≈ 0 from 29/10. From S263 the
  gateway routes to OpenAI and acc2 models meanwhile.
- **Not in the bundle:** DataForSEO (`shared.dfs_call_log`) and the geocoder (`geo.geocode_call`): **chưa rõ**
  (finding P8). Geoapify ran on its free plan (S259).
- **acc3: usage vs what we pay (P11, resolved by the orchestrator 03/11):** both numbers are acc3 and both are right.
  The CIS snapshot rows for 01–26/10 (236.40 USD, 155 rows) were fetched on 27/10, while acc3 was still a member of the
  former reseller's organization; the 02/11 refetch returned only 29–31/10 (0.20 USD, 12 rows). A direct read of
  acc3's own Cost Explorer on 03/11 (profile of acc3, one request) shows the same 0.20 USD for October (Claude Sonnet
  4.6 0.11, Cost Explorer 0.07, tax 0.02): once an account leaves an organization, its spend from the member period
  belongs to the former payer's bill. So **236.27 USD is real usage** (the gateway estimate 248.31 agrees) **but it was
  billed to the former reseller** under its trial cover; the company pays only the 0.20 USD from 29/10. The S263
  alerting audit read acc3 after 29/10 and was not wrong. Cash view of October: about 482.77 − 236.07 ≈ **246.70 USD**.

### By stage and role — 233.93 USD (top 20)

| App | Stage | Role | Account | Calls | USD |
|---|---|---|---|---|---|
| cis | s1_generate | writer | acc3 | 3,887 | 78.14 |
| cis | t5_atomize | writer | acc3 | 10,016 | 42.29 |
| cis | t9_write | writer | acc3 | 793 | 18.39 |
| cis | s1_judge | judge | acc3 | 10,469 | 12.13 |
| cis | t2_generate | writer | acc3 | 238 | 10.78 |
| cis | s1_flag_fix | writer | acc3 | 3,144 | 9.58 |
| cis | s1_grounding | validate | acc2 ⁵ | 111,179 | 9.56 |
| cis | a3_place_card_check | validate | acc3 | 7,282 | 9.04 |
| cis | s1_itinerary_nudge | writer | acc3 | 5,104 | 7.56 |
| cis | a3_place_locate | validate | acc3 | 289 | 5.07 |
| cis | a3_atomize | validate | acc3 | 6,528 | 4.22 |
| cis | a3_place_card | validate | acc3 | 8,623 | 4.11 |
| cis | a3_place_days | validate | acc3 | 872 | 3.76 |
| cis | a3_demand | validate | acc2 ⁵ | 33,488 | 3.23 |
| cis | a3_segment_type | validate | acc2 ⁵ | 15,948 | 2.80 |
| cis | t10_judge | judge | acc3 | 1,457 | 2.58 |
| cis | a3_place_card | writer | acc3 | 169 | 1.24 |
| cis | t9_repair | writer | acc3 | 427 | 1.23 |
| cis | writing_memory_eval | writer | acc3 | 73 | 1.19 |
| cis | a3_atomize | validate | acc2 ⁵ | 49,875 | 1.12 |

⁵ "acc2" here means "no AWS account on the row" (the collector writes `coalesce(account, 'acc2')`): these are mostly
Jev and OpenAI calls, not acc2 Bedrock (finding P2).

### Ad-hoc runs (stage `adhoc_<issue>`) — 35.41 USD

AA-645 11.23 (writer v2 A/B, pilot), AA-790 10.83 (T9 writer rounds, S254–S257), AA-729 5.74 (golden set baseline,
S245), AA-784 1.84, AA-801 0.99, AA-768 0.82, every other run under 0.75. Full table: the drafted sections of the
preliminary report (same ledger).

## Unit costs

| Unit | Value (USD) | Last month | Basis |
|---|---:|---|---|
| USD per published tour | 0.34 | n/a | cis total 304.83 / 892 tours published or republished in October (all 892 live tours have `published_at` in October) |
| USD LLM per published tour | 0.30 | n/a | cis LLM 269.32 / 892; the S1 campaign alone ≈ 0.073 USD/tour (S251) |
| USD per trip plan | n/a | n/a | No trip plan count (runbook step 4 not run) |
| USD per trip case | 0.27 | n/a | booking 6.11 / 23 test trip cases |
| USD per booking | 0.61 | n/a | booking 6.11 / 10 test bookings: no business meaning on Dev |

Last month's figures are `n/a` because September had no saved bundle. [`data/cis.txt`](data/cis.txt) (counted 02/11
23:34 UTC: 892 published, 892 live) is the `--prev-units` of the November report.

## Budgets and anomalies

| Budget / monitor | Limit | Actual (October) | Alerts fired |
|---|---|---|---|
| acc2 `aa-cis-dev-monthly-total` | 300 USD | 213.87, 71 % | 80 % actual (240) not reached. 100 % forecast: unlikely (late-October rate ≈ 7–8 USD/day ⇒ forecast ≈ 215–230). E-mails not checked |
| acc2 per-App budgets (tag from 16/10) | cis 90, shared 120, booking 25, crm 35, identity 10, tripplanner 10 | cis 36.01 (40 %), shared 55.21 (46 %), booking 6.11 (24 %), crm 6.63 (19 %), identity 2.46 (25 %), tripplanner 0.79 (8 %) | No 80 % actual crossing in October (half month tagged). At the late-October rate a full month is ≈ **shared 107 (89 %)**, **identity ≈ 9–10 (≈ 95 %)**, cis 70 (78 %), crm 25 (71 %), booking 12, tripplanner 1.5: shared and identity will cross 80 % actual in November, identity may forecast above 100 % (finding P6). E-mails not checked |
| acc3 `aa3-llm-monthly-total` | 250 USD gross of credits | 236.27, 94.5 % | 80 % (200) crossed around 25/10 (S251: 201.69 / 250); 100 % not crossed. Whether the e-mails arrived: **chưa rõ** |
| Organization budget `aa-org-monthly` | 300 USD | 0.04 (the organization holds only the management account; acc2 and acc3 are not members, S263) | None possible |
| acc2 Cost Anomaly Detection, AWS services monitor | Immediate SNS alert at total impact ≥ 5 USD | — | **Monitor live:** `Default-Services-Monitor` (SERVICE, 28 services tracked), last evaluated **02/11 18:55 UTC** (read 03/11 with `get-anomaly-monitors`); owned by Terraform with the IMMEDIATE ≥ 5 USD subscription to the alerts topic (Infra `accounts/aa365/cost_anomaly.tf`, S243). The subscription and the list of October anomalies were **not read** (MFA expired): **chưa rõ** whether the ECS or CloudWatch growth raised one. No October session log records an anomaly e-mail |
| acc3 anomaly subscriptions (daily ≥ 10, immediate ≥ 15 USD, S255) | | | **chưa rõ** (no acc3 read in this lane); no session log records an alert |
| acc3 credits | AWS Lift 250 USD (01/09 → 31/12) | 249.94 left when read 29/10 (S257) | The reseller said on 29/10 it covered 250 USD of testing; real October invoice **chưa rõ** |

## Capacity (C8b checklist)

**Từ bản sơ bộ 01/11** (S262, values of the S255 review to 28/10), still valid: the bundle carries cost only, and
nothing in the capacity picture changed between 01/11 and 03/11 except item 2 (weekly check W45 ran on 02/11).

| # | C8b item | Status | Last measured |
|---|---|---|---|
| 1 | CloudWatch RDS (CPU, memory, connections, storage, IOPS, credits) | từ bản sơ bộ 01/11 | S255 (28/10): CPU avg 4.7 %, 0 h over the 20 % baseline; connections max 30 / 181; memory min 257 MB; storage ≈ 4.5 / 20 GB, +0.09 GB/day; no resize trigger |
| 2 | Top queries per role, C1.2 SLIs | **Measured 02/11** ([W45](../2026-11-02-S264-c43-w45/README.md)) | No target missed: tenant reads p95 ≈ 111 ms, job claim mean 1.1 ms, Booking p95 < 1 ms, admin cost aggregate mean ≈ 217 ms, TripPlanner place read new-call mean ≈ 82 ms; lock waits 0, cache hit 99.14 %, connections 7 / 181 |
| 3 | Tables and indexes | từ bản sơ bộ 01/11 | DB 1,527 MB; largest `shared.decision_log` 444 MB, `shared.llm_call_log` 203 MB |
| 4 | Ledgers vs retention | từ bản sơ bộ 01/11 | ≈ 360.7k LLM calls in October (≈ 26.2k in September), one row each; `llm_call_log` 386k rows on 28/10; 1 M rows expected 25/11–30/12; first retention window (tenant usage) on 15/12 |
| 5 | Lambda concurrency and throttles | từ bản sơ bộ 01/11 | browse hit its reserved 15; 99 throttles after 16/10; TripPlanner AWS cost 0.79 USD |
| 6 | Job backlog and duration per owner | từ bản sơ bộ 01/11 | CIS oldest due 1,407 s once; Booking 38,746 s sample explained (D8) |
| 7 | C2.2 connection budget from live Terraform | từ bản sơ bộ 01/11 | 120 / 135 after api autoscaling max 7 → 3 (D2, S256) |
| 8 | C3 triggers | từ bản sơ bộ 01/11 | none fired except "materialized catalog read model" (D12) |
| 9 | RDS cost vs budget | **Measured (this report)** | RDS 30.80 USD; `db.t4g.small` ≈ 31–32 USD per full month for the instance alone, plus storage 2.8 and backup storage (≈ 6.8 USD/month at the end-October level until the `pre-s1` snapshots expire): November ≈ 38–40 USD, above the ≈ 30 assumed in S248 (finding P10) |
| — | ECS services | **Cost measured** | cis 24.34, booking 5.63, crm 3.66, untagged 21.30; CPU / memory từ bản sơ bộ 01/11 (no service short of resources) |

## Findings and proposed decisions (C8c)

**Từ bản sơ bộ 01/11** (P1–P8), with their status on 03/11, plus new items P9–P12. Proposals for the tech lead;
nothing applied. No item adds a paid AWS service. Ask before creating any Linear issue.

| # | Finding | Proposed decision | Type | Cost impact | Status 03/11 |
|---|---|---|---|---|---|
| P1 | Untagged 106.51 USD; after 16/10 still public IPv4, 90 % of CloudWatch, 62 % of Secrets, short ECS tasks | Add `App` to secrets, the remaining alarms and log groups; tag short Infra tasks (`propagateTags`); public IPv4 cannot carry a cost tag (stays shared) | tune | 0 | open |
| P2 | Rows without an AWS account show as "acc2" in "By stage and role" | Show the provider (or `external`) instead | tune (tool) | 0 | open |
| P3 | `REFRESH=1` refreshed only the App-tag snapshot; acc3 kept the 27/10 fetch | **Done in this PR:** `collect_month.py` `REFRESH=1` also refreshes the SERVICE snapshot, both until the month is final | fix | ≈ 0.03 USD per non-final month | done (this PR) |
| P4 | CloudWatch, RDS, EC2-Other, API Gateway, S3 sources unknown | Answered with 2 usage-type pulls (0.02 USD) instead of the 11-request script | investigate | — | done, except P9 and the API Gateway source |
| P5 | Secrets baseline ≈ 19.6 USD/month (≈ 49 secrets) | Keep; S248 option S7 (static secrets → SSM Parameter Store) only with the tech lead's approval | no action | 0 now | open |
| P6 | Budgets `shared` (≈ 89 %) and `identity` (≈ 95 %) will cross 80 % actual in November at the late-October rate | No change now; re-read after the first fully tagged week of November. If needed, move headroom inside the 300 USD total (for example cis 90 → 80, identity 10 → 12, shared 120 → 128) | no action | 0 | open |
| P7 | Gateway vs Cost Explorer: September log ≈ 79 % of CE; October gateway 5.1 % above CE | Reconcile per day for October with one acc3 daily pull; the `llm_cost_reconcile` job covers it from 01/12 | investigate | ≈ 0.01 USD | open |
| P8 | DataForSEO and geocoder spend outside the bundle | Add `shared.dfs_call_log` and `geo.geocode_call` totals to `collect_month.py` (PART=cis) | investigate | 0 | open |
| P9 | Inter-AZ traffic between Fargate tasks and the NAT instance ≈ 20 GB/day from 14/10 (9.14 USD in October on ECS + EC2-Other, ≈ 12–13 USD per full month), not LLM traffic | Find the source first: one CloudWatch Logs Insights query on the VPC flow log (already on, 365-day retention) grouped by source ENI / destination port for one day; then decide (for example keep the busiest service in the NAT's Availability Zone). No interface endpoint before the source is known (each costs more than it would save) | investigate | ≈ 0.01–0.05 USD once | new |
| P10 | RDS backup storage beyond the free allowance ≈ 6.8 USD/month at the end-October level; the 20 `pre-s1` snapshots expire only ≈ 23–25/11 | Either let them expire (≈ 5 USD more in November) or delete the ones the catalogue no longer needs, through the DRY RUN procedure (`skill/aa-cis-schema/references/destructive-ops.md`) | tune | saves ≈ 4–5 USD once | new |
| P11 | acc3 October: CIS snapshot 236.27 USD vs acc3's own Cost Explorer 0.20 USD | Resolved 03/11: the 01–26/10 usage was billed to the former reseller (member period); the company pays 0.20 USD. From November the report shows usage and cash side by side for acc3 | done | 0.01 | resolved |
| P12 | API Gateway carries a steady 15–20k REST requests/day from 25/10, likely the CRM portal calling the CIS API through the public host | Confirm from the API Gateway access log by route; if confirmed and it grows, consider the private path (ALB inside the VPC) for server-to-server calls | investigate | 0 | new |

## Data

- [`data/cis.txt`](data/cis.txt), [`data/booking.txt`](data/booking.txt), [`data/crm.txt`](data/crm.txt): the
  `FINOPS_BUNDLE` lines of 02/11 23:31–23:34 UTC (months 2026-08 to 2026-10), account IDs removed by the collector.
  Keep `cis.txt`: it is the `--prev-units` of the November report.
- [`data/acc2-usage-type-2026-09-10.csv`](data/acc2-usage-type-2026-09-10.csv): acc2 cost and quantity by service and
  usage type, September and October, for ECS, RDS, CloudWatch, Secrets Manager, API Gateway, S3 and EC2 - Other.
- [`data/acc2-daily-usage-2026-10.csv`](data/acc2-daily-usage-2026-10.csv): acc2 per day of October for 10 usage types
  (API Gateway requests, data out, inter-AZ transfer, S3 requests, CloudWatch alarms and metrics, log ingest, RDS
  backup storage, `db.t4g.micro`).
- Checked before commit: no 12-digit number and no ARN in this folder (`grep` for the 12-digit pattern and for the ARN prefix: both empty).
- Cost of this report: ≈ 0.02–0.03 USD (collector refresh, orchestrator) + 0.03 USD (3 Cost Explorer requests, this lane) +
  0.02 USD (management account, runbook step 3). No LLM call.
