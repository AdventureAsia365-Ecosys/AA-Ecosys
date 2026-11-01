---
id: OPS-08-s262-capacity-review-prelim
title: Cost and capacity review 2026-10 (preliminary)
description: "Preliminary October 2026 review: about 472 USD (AWS acc2 203 + LLM outside AWS 269) vs 178 in September, driven by two catalogue rewrites and new always-on services; final version from 03/11."
type: report
status: draft
owner: nghiep
audience: [owner, engineer, cto, cio, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-01
review_every_days: 30
related: [FIN-02, OPS-08, FIN-01, FIN-02-2026-10-prelim, OPS-08-2026-10, AA-896, AA-838, AA-884, AA-828]
---

# Rà soát chi phí và dung lượng tháng 10/2026 (sơ bộ)

> [!WARNING]
> **SƠ BỘ — Cost Explorer đến 30/10; bản chính thức từ 03/11 theo runbook.** acc2 có số 01–30/10 (thiếu 31/10);
> acc3 có số Cost Explorer đọc ngày 27/10 (tới khoảng 26/10). Cost Explorer còn sửa số khoảng 48 giờ sau cuối tháng.
> Mọi số là môi trường **Dev**, chưa có khách thật: chỉ để xem xu hướng, không dùng để lập kế hoạch.

- Phiên: S262, 01/11/2026. Tác nhân: Claude Code (subagent, chỉ đọc file local). Mẫu: [`templates/cost-report.md`](../../templates/cost-report.md)
  + phần dung lượng của [`templates/capacity-review.md`](../../templates/capacity-review.md). Runbook:
  [`ops/finops.md`](../../ops/finops.md#monthly-review), [`ops/cost/README.md`](../../ops/cost/README.md).
- Nguồn số liệu: 3 bundle của `tools/finops/collect_month.py` (CIS, Booking, CRM) do phiên điều phối chạy qua
  `tools/ecs/ecsx.sh` lúc **01/11 00:03 UTC**, rồi `tools/finops/monthly_cost_report.py` soạn các bảng. Bundle đã gỡ
  account ID; bản sao ở [`data/`](data/) (đã `grep` số 12 chữ số và `arn:`: không có). Bundle đọc dữ liệu Cost Explorer
  **đã lưu sẵn** trong DB (`refresh.attempted = false`), nên báo cáo này tốn **0 USD**: không gọi Cost Explorer, không
  gọi LLM, không ghi gì lên AWS.
- Lý do của từng bước nhảy lấy từ log phiên `docs/sessions/2026-10-*.md`, hai báo cáo trước
  ([S248 cost](../2026-10-23-S248-cost-report/README.md), [S255 capacity](../2026-10-28-S255-aa838-capacity/README.md))
  và register secret. Chỗ nào log hay dữ liệu không chứng minh được thì ghi **"chưa rõ — kiểm ở bản chính thức"**.
- Số "nhịp 23–30/10" dưới đây = (số tháng 10 của bundle − số 01–22/10 của S248) ÷ 8 ngày. Hai nguồn khác nhau (Cost
  Explorer đọc trực tiếp ngày 23/10 và bản lưu trong DB), nên chỉ là ước lượng.

## Tóm tắt cho chủ doanh nghiệp (VI)

1. Tổng chi phí tháng 10/2026 (sơ bộ): khoảng **472 USD** — hạ tầng AWS 203 USD (tính tới 30/10) và AI 269 USD; chưa gồm tài khoản quản lý AWS mới lập cuối tháng (khoảng 1–1.5 USD/tháng).
2. So với tháng 9 (178 USD): tăng khoảng **165 %**.
3. Lý do chính: AI viết lại toàn bộ catalogue tour hai lần trong tháng (đầu tháng chạy lại 14 nước; 24–25/10 viết lại 810 tour bằng cách viết mới, khoảng 59 USD), dựng thẻ địa điểm và các vòng thử chất lượng bài viết; hạ tầng tăng khoảng 68 USD vì có thêm hệ thống đặt tour, CRM cho đại lý, máy chạy việc nền riêng, cơ sở dữ liệu lớn hơn, nhiều cảnh báo và khoá bảo mật hơn.
4. Ngân sách: hạ tầng dùng 203 / 300 USD (68 %); tài khoản AI 236 / 250 USD (94 %), theo nhà cung cấp phần thử nghiệm tới 29/10 đã được họ trả; từ 29/10 tiền AI trừ vào credit AWS (còn khoảng 250 USD) rồi mới tới thẻ công ty, và từ 29/10 tài khoản AI đang bị AWS tạm chặn nên gần như không phát sinh.
5. Chi phí cho mỗi tour đang bán là 0.34 USD (riêng AI 0.30 USD), số Dev chỉ để xem xu hướng; tháng 11 dự kiến thấp hơn vì không còn đợt viết lại cả catalogue. Cần quyết định: không có.

## Totals by account

| Account | 2026-08 | 2026-09 | 2026-10 | Change 09 → 10 | Note |
|---|---:|---:|---:|---:|---|
| acc2 (infra, all App tags) | 140.22 ¹ | 134.96 | **202.85** | +50.3 % | Stored Cost Explorer, days 01–30/10, fetched 31/10 03:40 UTC. 6.76 USD/day (Sep 4.50); with 31/10 ≈ 209.6 |
| acc3 (LLM, Bedrock, Cost Explorer) | 22.40 ¹ | 51.37 | **236.16** | +359.7 % | Stored figure fetched **27/10** 03:59 UTC (≈ to 26/10). Gateway estimate for the whole month 248.33 |
| Retired account (acc1, former LLM fallback) | 45.15 ¹ | 0.89 | 0.69 | −22.9 % | Removed from the ecosystem 28/10 (AA-998, S255) |
| Management account (org trail, KMS, budgets) | — | — | not included | | Created 30/10 (AA-1004, S259); S259 estimate ~1–1.5 USD/month; read in the final version (runbook step 3) |
| LLM outside acc2 (gateway, every provider) | n/a | 42.78 | 268.85 | +528.5 % | acc3 Bedrock + Jev + OpenAI + acc1, from `shared.llm_call_log` |
| **Total (AA-884: acc2 + LLM outside acc2)** | n/a | **177.74** | **471.70** | **+165.4 %** | |

¹ August from the S248 report (Cost Explorer read 23/10). The bundle's stored acc2 snapshot has no August data
(`aws.has_data = false`), so the "2026-08 = 0.00" column of the generated draft means "no data", not zero; its acc3
snapshot holds only 0.42 USD for August (fetched 29/09), far below S248's 22.40, so S248 is used for every August cell.

## By app (tag `App`)

The `App` tag counts only from **15–16/10** (AA-828); everything before sits in "Not assigned". The app lines below are
therefore about half a month (16–30/10); the per-month estimate (×2, or per active day) is a rough guide only.

| App | 2026-10 (USD) | 2026-09 | AWS | LLM | ≈ USD/month at the 16–30/10 rate | Note |
|---|---:|---:|---:|---:|---:|---|
| CIS (content + catalog) | 302.36 | 41.33 | 33.54 | 269.32 | AWS ≈ 67 | ECS 22.69, ElastiCache 7.61, Secrets 1.32, API GW 0.69, ECR 0.62 |
| Booking | 5.68 | 0.00 | 5.68 | 0.00 | ≈ 11 | **New**: live since 14/10 (S235). ECS 5.24, Secrets 0.32, API GW 0.06 |
| Partner CRM | 5.55 | 0.00 | 5.55 | 0.00 ² | ≈ 21 (services from 23–26/10) | **New**: ECS 3.13, Secrets 1.09, KMS 0.77, Bedrock Guardrail 0.29, CloudFront 0.16 |
| TripPlanner | 0.75 | 1.45 | 0.72 | 0.03 | ≈ 1.5 | Secrets 0.59; Lambda and API ≈ 0 |
| Shared platform | 50.77 | n/a | 50.77 | 0.00 | ≈ 102 | RDS 18.71, ELB 18.62, WAF 5.05, EC2-Other 4.47, EC2 1.89, CloudWatch 1.40 |
| Staff sign-in (identity) | 2.09 | n/a | 2.09 | 0.00 | ≈ 8 (WAF from 24–25/10) | WAF `aa-identity-dev-pools` 1.75 (new in S250, 24–25/10), Secrets 0.34 |
| Platform tooling / tag `ecosystem` | 0.14 | n/a | 0.14 | 0.00 | — | Tag values outside DM-10.1 (S248 F6 named `identity` and `platform`; `ecosystem` is one more) |
| Not assigned to an app | 104.36 | 134.96 | 104.36 | 0.00 | chưa rõ ³ | Finding (DM-10.1), see "Untagged" below |

² The CRM's own gateway logged 2 calls, 0.0001 USD (Guardrail scrub + a stub model).
³ The bundle has no daily split, so the untagged rate after 16/10 is not known; S248 measured 1.21 USD/day for
16–22/10 (19 % of acc2). Chưa rõ — kiểm ở bản chính thức.

## Month over month

| Line | 2026-08 | 2026-09 | 2026-10 | Change, last month |
|---|---:|---:|---:|---|
| AWS acc2 | 140.22 ¹ | 134.96 | 202.85 | +50.3 % |
| acc3 Bedrock (Cost Explorer) | 22.40 ¹ | 51.37 | 236.16 | +359.7 % |
| LLM, all apps (gateway estimate) | n/a ⁴ | 42.79 | 269.35 | +529.5 % |
| — of which CIS | n/a | 41.34 | 269.32 | +551.5 % |
| **Total (AWS acc2 + LLM outside AWS)** | n/a | 177.74 | 471.70 | +165.4 % |

⁴ `shared.llm_call_log` starts on 17/09 (S255 capacity review §4), so there is no August LLM row.

Top 10 acc2 services (per-app split: bundle `data/cis.json`):

| Service | 2026-09 | 2026-10 | Change | cis | booking | crm | shared / identity | untagged |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Elastic Container Service | 21.13 | 52.19 | **+147.0 %** | 22.69 | 5.24 | 3.13 | — | 21.13 |
| Elastic Load Balancing | 36.41 | 36.44 | +0.1 % | — | — | — | 18.62 | 17.81 |
| Relational Database Service | 20.39 | 29.03 | **+42.4 %** | — | — | — | 18.71 | 10.32 |
| CloudWatch | 7.86 | 18.53 | **+135.6 %** | 0.28 | — | — | 1.40 | 16.79 |
| ElastiCache | 15.84 | 15.31 | −3.4 % | 7.61 | — | — | — | 7.70 |
| WAF | 9.46 | 11.32 | +19.6 % | — | — | — | 5.05 + 1.75 | 4.52 |
| Secrets Manager | 4.42 | 10.96 | **+148.0 %** | 1.32 | 0.32 | 1.09 | 0.17 + 0.34 | 6.99 |
| VPC (public IPv4) | 10.81 | 10.77 | −0.4 % | — | — | — | — | 10.77 |
| EC2 - Other | 3.44 | 7.01 | **+103.9 %** | — | — | — | 4.47 | 2.53 |
| EC2 - Compute (NAT instance) | 3.98 | 3.92 | −1.6 % | — | — | — | 1.89 | 2.03 |

## Top 5 services and changes over 20 %

| Service | This month | Last month | Change | Reason |
|---|---:|---:|---:|---|
| Elastic Container Service | 52.19 | 21.13 | +147.0 % | New always-on services: `aa-cis-dev-worker` from 05/10 (S210, AA-651), `aa-booking-dev-api` from 14/10 (S235), three CRM services (ARM64, 0.25 vCPU) from 23, 24 and 26/10 (S255 capacity review, ECS table); autoscaling of api/worker during the waves; short tasks (DB Migrate, nightly Schema Dump) and overlapping tasks on deploys (S248 §4). Rate 1.45 USD/day on 01–22/10 (S248) → ≈ 2.54 USD/day on 23–30/10 (CRM services + S1 catalogue waves 24–25/10) |
| Elastic Load Balancing | 36.44 | 36.41 | +0.1 % | Flat: one ALB + one NLB for the VPC link, unchanged (S248 §4) |
| Relational Database Service | 29.03 | 20.39 | +42.4 % | `db.t3.micro` → `db.t4g.small` + Performance Insights on 15/10 (S237, S255 capacity review); S248 expected ≈ 30 USD/month after the change. The 23–30/10 rate (≈ 1.38 USD/day) is above t4g.small ≈ 0.88 USD/day plus backup: **chưa rõ — kiểm ở bản chính thức** (candidates with evidence: 20 manual snapshots `aa-cis-dev-db-pre-s1-*`, one per S1 wave, S249–S250; DB Migrate snapshots, S248) |
| CloudWatch | 18.53 | 7.86 | +135.6 % | More alarms, metrics and logs during the month: 4 log-write-failed alarms + metric filters (S225), RDS alarms (S237), job-backlog alarms + `AA/Jobs/*` metrics (S240), Cognito 14 alarms + 2 metrics, ECS Exec session logs, RDS `log_connections` (S241), log retention 365 days for flow, WAF, exec and postgresql logs (AA-872, S241), backup alarm (S249), `crm_app` alarm (S255), 2 TripPlanner job alarms (S257). S248 measured alarms 0.056 → 0.099 USD/day and custom metrics 0.075 → 0.149 USD/day for 01–22/10. The 23–30/10 rate (≈ 1.15 USD/day, 2.7 × the 01–22/10 rate) is **chưa rõ — kiểm ở bản chính thức** (usage type). 91 % of CloudWatch is untagged |
| ElastiCache | 15.31 | 15.84 | −3.4 % | Flat; the Redis node was replaced by Valkey `cache.t3.micro` on 24–25/10 with no parallel run (S250, AA-874) |
| Secrets Manager | 10.96 | 4.42 | +148.0 % | Live secrets 29 (19/10, S244) → 49 (25/10, S250 register re-read): Booking, staff identity, CRM (web, M2M client, six e2e users, mail OAuth), TripPlanner Cognito keys, Redis AUTH. 49 × 0.40 USD = 19.6 USD/month new baseline; the 23–30/10 rate (≈ 0.67 USD/day) matches 49 secrets. 64 % of the line has no `App` tag |
| API Gateway | 2.37 | 0.38 | +517.1 % | **chưa rõ — kiểm ở bản chính thức.** Booking REST API (from 14/10) carries only 0.06 USD; the rest is cis 0.69 + untagged 1.58 + TripPlanner 0.03 (S248 candidates: TripPlanner traffic, probes and smokes; also possible: the S247 AA-847 burst test of 1,367 calls) |
| S3 | 1.22 | 0.23 | +423.3 % | **chưa rõ — kiểm ở bản chính thức** (candidates: Drive → S3 photo sync of 3,232 photos on 01/10, S207; CRM bucket, S248; Booking ops-docs bucket, S256) |
| EC2 - Other | 7.01 | 3.44 | +103.9 % | Partly seen in S248 (usage type, 01–22/10): inter-AZ transfer 0.036 → 0.213 USD/day, internet out 0.002 → 0.069 USD/day. Source still **chưa rõ — kiểm ở bản chính thức** (S248 F5) |

WAF (+19.6 %, under the 20 % flag): the new web ACL `aa-identity-dev-pools` from 24–25/10 (S250, ≈ 9 USD/month list price).

## Explanations in more detail

### LLM: +529.5 % on the gateway log, +359.7 % on Cost Explorer

- **Read the Cost Explorer figure for the trend.** The September gateway log is incomplete: it starts on 17/09 and
  lost rows when the single-connection bug made log writes fail until 09/10 (S224, AA-756); acc3 in the log was 40.37 vs
  51.37 USD in Cost Explorer (≈ 79 %). Since AA-927 (S246) every call writes exactly one row. So the +529.5 % is
  inflated; acc3 Cost Explorer grew **+359.7 %**.
- **By pipeline family (CIS, October, gateway):**

| Family | USD | Share | Calls | What ran (session / issue) |
|---|---:|---:|---:|---|
| S1 rewrite (`s1_*`) | 117.80 | 44 % | 133,965 | (a) 01–10/10: re-run of all 14 countries (S207–S218) and the India waves + A/B (S223); S1 LLM ≈ 0.08 USD/tour on 01/10 (S207). (b) 24–25/10: catalogue rewrite of 810 tours with writer v2 on Sonnet 5.5, **59.34 USD** in total (S249–S251, AA-645), ≈ 0.073 USD/tour. The remaining ≈ 58 USD is (a) plus regenerates (subtraction, not split by day) |
| A3 atomize, legacy key `t5_atomize` | 42.32 | 16 % | 10,059 | Atomize on Haiku 4.5 during the early-October re-run; moved to GPT-6 Luna and renamed `a3_atomize` (migrations 213/214, AA-757, S224). After that `a3_atomize` cost 5.34 USD for 56,403 calls |
| Tenant series (`t2`, `t3`, `t7`–`t10`) | 35.29 | 13 % | 7,543 | `t9_write` 18.39 (blog/social pilot S231, 80 articles S234, writer rounds r5–r7 S235–S239; split per run **chưa rõ**), `t2_generate` 10.78 (pilot S231, T2 re-run 3.49 S235, AA-793 1.42 S237), `t10_judge` 2.58 |
| Ad-hoc (`adhoc_<issue>`) | 35.41 | 13 % | 15,441 | AA-645 11.23 (writer v2 A/B, pilot), AA-790 10.83 (T9 writer rounds r6b–r10, S254–S257), AA-729 5.74 (golden set baseline + regenerate, S245), AA-784 1.84, AA-801 0.99, AA-768 0.82, rest < 0.75 each |
| Places (`a3_place_*`) | 23.88 | 9 % | 18,520 | Place cards for 892 tours 12.65 USD and place build 4.31 USD (S252, AA-784 / AA-905), Laos batch 0.755 (S237), AA-847 0.65 (S247); `a3_place_locate` on Sonnet (migration 261), `a3_place_days` on Haiku 4.5 (migration 260) |
| A3 atomize, `a3_atomize` (after the switch) | 5.34 | 2 % | 56,403 | acc3 4.22 USD / 6,528 calls (GPT-6 Luna, Haiku fallback, migrations 213/214, S224) + 1.12 USD / 49,875 calls without an AWS account (shown as acc2 by the collector, P2); not part of the 42.32 above |
| A3 segment / demand / question | 7.39 | 3 % | 97,971 | Mostly Jev decisions (see next point) |
| Other (writing memory, A1 SEO, embeddings, supply, TripPlanner, A0) | 1.91 | 1 % | 20,774 | |

- **By provider (CIS, October):** acc3 Bedrock 248.31 USD (67,091 calls); **Jev 19.10 USD (288,883 calls)**; OpenAI
  0.73; acc1 0.69; acc2 Bedrock 0.49; OpenAI and Anthropic direct ≈ 0 (connection tests). Jev was ≈ 8 USD/month in
  the S223 plan; October's 19.10 follows the two S1 campaigns (`s1_grounding` alone 9.56 USD / 111,179 calls).
- **By role:** writer 198.56 USD (74 %), validate 48.94, judge 21.70, embed 0.14.
- **Models:** the bundle has no model column. Cost Explorer for 01–22/10 (S248 §5): Haiku 4.5 86.45, Sonnet 4.6 37.41,
  GPT-5.6 Luna 10.73, GPT-6 Luna 3.40 USD; from 24/10 `s1_generate` runs on Sonnet 5.5 (S250 decision). Per-model
  split for the whole month: **chưa rõ — kiểm ở bản chính thức** (CloudWatch `AWS/Bedrock`, S248 scripts).
- **After 29/10:** acc3 answers Error 002 on every Bedrock model (S257–S261), so LLM spend from 29/10 is ≈ 0
  (S258–S260 logs: "LLM $0").
- Not in the bundle: DataForSEO (`shared.dfs_call_log`) and the geocoder — **chưa rõ — kiểm ở bản chính thức**.
  Geoapify ran on its free plan (S259).

### Untagged spend: 104.36 USD

- 01–15/10 is untagged by construction: the `App` tag counts from 15–16/10 and Cost Explorer does not re-tag older
  usage (AA-828, `ops/finops.md` Tags).
- After 16/10 the known untagged sources are CloudWatch alarms and logs, the public IPv4 addresses (VPC), 20 of 34
  secrets at 23/10, and short ECS tasks (S248 F4). The split before / after 16/10 is **chưa rõ — kiểm ở bản chính
  thức** (the bundle has no daily data).

### Booking and CRM (new this month)

- **Booking** 5.68 USD: live on Dev since 14/10 (S235); ECS 0.25 vCPU / 0.5 GB, a REST API of its own. 23 trip cases
  and 10 bookings in October are test data (S241 D-01 counted 17/10: only test or internal e-mails, no real PII; rows
  after 17/10 not re-checked here).
- **Partner CRM** 5.55 USD: `aa-crm-dev-api` running from 23/10 (S248), web 24/10, portal 26/10 (S255 capacity
  review); KMS key and bucket (S248), Bedrock Guardrail scrub ≈ 0.75 USD/month (S249), CloudFront with VPC origin
  (S247). Budget 35 USD/month (S255).

## Unit costs

| Unit | Value (USD) | Last month | Basis |
|---|---:|---|---|
| USD per published tour | 0.34 | n/a | cis total 302.36 / 892 tours published or republished in October (all 892 live tours have `published_at` in October) |
| USD LLM per published tour | 0.30 | n/a | cis LLM 269.32 / 892. S1 campaign alone ≈ 0.073 USD/tour (S251) |
| USD per trip plan | n/a | n/a | No trip plan count (runbook step 4 not run) |
| USD per trip case | 0.25 | n/a | booking 5.68 / 23 test trip cases |
| USD per booking | 0.57 | n/a | booking 5.68 / 10 test bookings: no business meaning on Dev |

Last month's per-tour figure is `n/a` because September had no saved bundle; `data/cis.json` (counted 01/11 00:03 UTC)
is November's `--prev-units`.

## Budgets and anomalies

| Budget / monitor | Limit | Actual | Alerts fired |
|---|---|---|---|
| acc2 `aa-cis-dev-monthly-total` | 300 USD (S255) | 202.85 (01–30/10), 68 % | 80 % actual (240) not reached on these numbers; forecast e-mails: **chưa rõ — kiểm ở bản chính thức** |
| acc2 per-App budgets | cis 90, shared 120, booking 25, crm 35, identity 10, tripplanner 10 | 33.54 / 50.77 / 5.68 / 5.55 / 2.09 / 0.72 (16–30/10) | **chưa rõ — kiểm ở bản chính thức.** At the 16–30/10 rate a full month is ≈ cis 67, **shared ≈ 102 (85 %)**, booking 11, crm 21, **identity ≈ 8 (82 %)**, tripplanner 1.5: shared and identity would cross their 80 % actual threshold in a full month |
| acc3 `aa3-llm-monthly-total` | 250 USD gross of credits | 236.16 (to ≈ 26/10), 94 % | The 80 % threshold (200) was crossed around 25/10 (S251: 201.69 / 250); whether the e-mail arrived: **chưa rõ — kiểm ở bản chính thức** |
| acc2 Cost Anomaly Detection, immediate ≥ 5 USD | | | **chưa rõ** — no October session log records an alert |
| acc3 anomaly subscriptions (daily ≥ 10, immediate ≥ 15 USD, S255) | | | **chưa rõ** — no session log records an alert |
| Organization budget `aa-org-monthly` | 300 USD | management account created 30/10 | **chưa rõ** |
| acc3 credits | AWS Lift 250 USD (01/09 → 31/12) | 249.94 left when read 29/10 (S257) | The reseller said on 29/10 that it covered 250 USD of testing; charges from 29/10 draw the Lift credit, then the card. The real October invoice: **chưa rõ — kiểm ở bản chính thức** |

## Capacity (C8b checklist)

The bundle carries cost only. Items that need CloudWatch, Performance Insights or the probe were **not measured**
here; the last measured values are in the [S255 review](../2026-10-28-S255-aa838-capacity/README.md) (window to 28/10)
and its decisions D1–D13 were applied in S256.

| # | C8b item | This preliminary | Last measured (S255, 28/10) |
|---|---|---|---|
| 1 | CloudWatch RDS (CPU, memory, connections, storage, IOPS, credits) | **chưa đo** | CPU avg 4.7 %, 0 h over the 20 % baseline; connections max 30 / 181; memory min 257 MB; storage ≈ 4.5 / 20 GB, +0.09 GB/day (7 d); no resize trigger |
| 2 | Top queries per role, C1.2 SLIs | **chưa đo** (weekly check W45 is due 02/11) | TripPlanner browse SLI missed (heaviest `tripplanner` statement p95 ≈ 2.5 s); CIS tenant reads missed on 1–2 statements |
| 3 | Tables and indexes | **chưa đo** | DB 1,527 MB; largest `shared.decision_log` 444 MB, `shared.llm_call_log` 203 MB |
| 4 | Ledgers vs retention | **Partly, from the bundle:** the gateway logged ≈ 360.7k LLM calls in October (≈ 26.2k in September); since AA-927 one call = one `shared.llm_call_log` row, so October ≈ 360k new rows (of which Jev 288.9k). Row counts, oldest row and retention mode: **chưa đo** | `llm_call_log` 386k rows, `decision_log` 434k; 1 M rows expected 25/11–30/12; first retention window (tenant usage) on 15/12 |
| 5 | Lambda concurrency and throttles | **chưa đo** (TripPlanner AWS cost 0.72 USD, Lambda ≈ 0) | browse hit its reserved 15; 99 throttles after 16/10 |
| 6 | Job backlog and duration per owner | **chưa đo** | CIS oldest due 1,407 s once; Booking 38,746 s sample explained (D8) |
| 7 | C2.2 connection budget from live Terraform | **chưa đo** | 120 / 135 after api autoscaling max 7 → 3 (D2, Infra #481, S256) |
| 8 | C3 triggers | **chưa đo** | none fired except "materialized catalog read model" (almost certain, text pending, D12) and C2.2 total on paper (168 / 135, cleared by D2 → 120 / 135) |
| 9 | RDS cost vs budget | **Measured:** RDS 29.03 USD (Sep 20.39); `shared` 18.71 from 16/10 + untagged 10.32 before; budget `shared` 120 USD/month; t4g.small run-rate ≈ 30 USD/month (S248) but 23–30/10 ≈ 1.38 USD/day (see RDS reason); `CPUSurplusCreditsCharged` **chưa đo** (0 on 28/10) | ≈ 30 USD/month after the resize |
| — | ECS services | **Cost measured** (cis 22.69, booking 5.24, crm 3.13, untagged 21.13); CPU / memory **chưa đo** | no service short of resources; CRM services at the smallest Fargate size |

## Findings and proposed decisions (C8c)

Proposals for the tech lead; nothing applied. No item adds a paid AWS service. Ask before creating any Linear issue.

| # | Finding | Proposed decision | Type | Cost impact |
|---|---|---|---|---|
| P1 | Untagged 104.36 USD; after 16/10 still CloudWatch, IPv4, 64 % of the Secrets line, short ECS tasks (S248 F4 still open) | Add `App` to secrets, alarms and log groups that lack it; tag short Infra tasks (`propagateTags`) | tune | 0 |
| P2 | The collector writes `coalesce(account, 'acc2')` for LLM rows (`tools/finops/collect_month.py`), so Jev and OpenAI rows show as "acc2" in "By stage and role" (e.g. `s1_grounding` 111k calls) | Show the provider (or `external`) instead of `acc2` for rows without an AWS account | tune (tool) | 0 |
| P3 | acc3 Cost Explorer in the bundle was fetched 27/10 though `refresh.reason = fresh` | Final version: collect CIS with `REFRESH=1`; check whether the staleness test covers acc3 | investigate | ≈ 0.01–0.03 USD |
| P4 | CloudWatch rate 23–30/10 ≈ 2.7 × earlier in October; RDS above the t4g.small run-rate; EC2-Other, API Gateway, S3 sources unknown | Final version: one usage-type pull (S248 `scripts/fetch_ce.sh`, 11 requests ≈ 0.11 USD) to name each source; then decide (e.g. Dev log retention, expired `pre-s1` snapshots — they expire by the 30-day rule around 23–25/11) | investigate | ≈ 0.11 USD once |
| P5 | Secrets baseline now ≈ 19.6 USD/month (49 secrets) | Keep; revisit S248 option S7 (static secrets → SSM Parameter Store SecureString) only with the tech lead's approval | no action | 0 now |
| P6 | Budgets `shared` (120) and `identity` (10) would cross 80 % actual in a full month at the late-October rate | No change now; re-check with November, the first fully tagged month | no action | 0 |
| P7 | Gateway log vs Cost Explorer: September log ≈ 79 % of CE; October log 248.33 vs CE 236.16 (CE stops ≈ 26/10) | Final version: reconcile per month with a refreshed CE (S248 §9 step 5) | investigate | 0 |
| P8 | DataForSEO and geocoder spend are outside the bundle | Final version: add `shared.dfs_call_log` and `geo.geocode_call` totals for October | investigate | 0 |

## Steps for the final version (first session on or after 03/11)

1. `aws sts get-caller-identity --profile aa365-admin`, then re-collect the three bundles (runbook step 2), CIS with
   `REFRESH=1` (P3).
2. Management account amounts (runbook step 3, 2 requests ≈ 0.02 USD) → `--mgmt-usd` / `--mgmt-prev-usd`.
3. Trip plan count (runbook step 4) → `units-2026-10.json`.
4. Re-draft with `monthly_cost_report.py --budget-usd 300`; fill the reasons of P4 from one usage-type pull (≈ 0.11 USD)
   and the per-model LLM split (CloudWatch `AWS/Bedrock`, ≈ 0.001 USD).
5. C8b items 1–8: CloudWatch + PI (S255 `scripts/`), probe through DB Migrate `run-script`, `check_connection_budget.py`.
6. Budgets and anomalies: read the alert mailbox and the acc3 invoice / Billing → Credits.
7. Save `cis` bundle for December's `--prev-units`; set this page to `status: superseded`.

## Data

- [`data/cis.json`](data/cis.json), [`data/booking.json`](data/booking.json), [`data/crm.json`](data/crm.json): the
  `FINOPS_BUNDLE` JSON of 01/11 00:03 UTC (months 2026-08 to 2026-10). Checked before commit: no 12-digit number,
  no `arn:`, no e-mail address.
