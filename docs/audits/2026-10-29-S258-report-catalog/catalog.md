# Report catalog: detail per report

Part of the AA-1001 report catalog advisory (S258, 2026-10-29). Generated from [catalog.json](catalog.json) (do not edit by hand; edit the JSON and regenerate). Overview and recommendation (Vietnamese, for the tech lead): [README.md](README.md). Engine and schedule: [automation-plan.md](automation-plan.md). On-demand requests: [on-demand.md](on-demand.md).

> [!NOTE]
> All numbers on the platform today are Dev-phase: no real customers, tenants or bookings yet. Thresholds marked trend or baseline become targets after the first production month or quarter. Tables, views, job kinds and pages marked proposed do not exist yet; every other table and column name was checked against `docs/architecture/db-schema-reference.md`.

63 reports in 14 families. Priority: P0 7, P1 25, P2 23, P3 8. KPI IDs (K-...) are defined once; other reports write `Defined in <report>`.

## Index

| ID | Report | Family | Cadence | Automation | Today | Priority |
|---|---|---|---|---|---|---|
| [EX-01](#ex-01) | Weekly business pack | Executive and business | weekly: auto-draft Monday 01:30 UTC for the previous ISO week in ICT | semi | partial | P0 |
| [EX-02](#ex-02) | Monthly business review | Executive and business | monthly: auto-draft business day 2 at 02:00 UTC for the previous month | semi | missing | P1 |
| [EX-03](#ex-03) | Partner growth and churn | Executive and business | monthly section of EX-02 + live tab | auto | missing | P2 |
| [EX-04](#ex-04) | Executive KPI scorecard with daily history | Executive and business | daily snapshot 00:30 UTC for the previous ICT day + live on demand | auto | partial | P0 |
| [EX-05](#ex-05) | Quarterly business review and annual plan | Executive and business | quarterly: auto-draft with the monthly pack on business day 2 of Janu… | semi | missing | P2 |
| [EX-06](#ex-06) | Report register and calendar (reports hub) | Executive and business | live | auto | missing | P0 |
| [EX-07](#ex-07) | Partner onboarding funnel | Executive and business | weekly Monday 01:30 UTC + monthly in EX-02 | auto | missing | P2 |
| [FI-01](#fi-01) | Monthly cost review | Cost, FinOps and finance | monthly: auto-draft business day 2 at 02:00 UTC | semi | partial | P0 |
| [FI-02](#fi-02) | Weekly spend and vendor balance digest | Cost, FinOps and finance | weekly: Monday 01:30 UTC for the previous ISO week in ICT | auto | missing | P1 |
| [FI-03](#fi-03) | LLM cost attribution | Cost, FinOps and finance | monthly section of FI-01 + live | auto | partial | P1 |
| [FI-04](#fi-04) | Vendor spend, balances and contract register | Cost, FinOps and finance | monthly spend in FI-01 | semi | partial | P1 |
| [FI-05](#fi-05) | Unit economics | Cost, FinOps and finance | monthly section of FI-01 + live endpoint | auto | partial | P1 |
| [FI-06](#fi-06) | Budget vs actual and credit runway | Cost, FinOps and finance | monthly section of FI-01 | semi | partial | P1 |
| [FI-07](#fi-07) | Revenue, bookings and margin (weekly flash + monthly close) | Cost, FinOps and finance | weekly flash Monday 01:30 UTC | auto | partial | P2 |
| [FI-09](#fi-09) | Tenant billing run | Cost, FinOps and finance | monthly, business day 2 for the previous month | semi | missing | P3 |
| [BK-03](#bk-03) | Receivables and payables aging with collections | Cost, FinOps and finance | weekly Monday 01:30 UTC + month-end statement business day 2 | auto | missing | P1 |
| [CIS-01](#cis-01) | Weekly catalog health | Product and app operations | weekly Monday 01:30 UTC + live page | auto | partial | P1 |
| [CIS-03](#cis-03) | Tenant content delivery (internal) | Product and app operations | monthly business day 2 + live | auto | partial | P2 |
| [TP-01](#tp-01) | Weekly TripPlanner funnel | Product and app operations | weekly Monday 01:30 UTC + live card | auto | partial | P1 |
| [BK-01](#bk-01) | Booking daily operations digest | Product and app operations | daily 01:00 UTC, Monday to Friday | auto | partial | P1 |
| [BK-02](#bk-02) | Booking sales pipeline | Product and app operations | weekly Monday 01:30 UTC + monthly business day 2 | auto | partial | P2 |
| [BK-04](#bk-04) | Supplier performance and contract renewals | Product and app operations | monthly business day 2 | auto | partial | P3 |
| [BK-05](#bk-05) | B2B partner desk report | Product and app operations | monthly business day 2 | auto | partial | P3 |
| [BK-06](#bk-06) | Departure fill and incidents | Product and app operations | weekly Monday 01:30 UTC | auto | missing | P3 |
| [OPS-14](#ops-14) | Job runner health (all job tables) | Product and app operations | weekly Monday 01:30 UTC + daily failures in OPS-12 | auto | partial | P1 |
| [OPS-15](#ops-15) | Session-close state snapshot | Product and app operations | every session close | semi | partial | P1 |
| [CIS-05](#cis-05) | Weekly AI content quality KPIs | AI content quality | weekly Monday 01:30 UTC | auto | planned | P1 |
| [CIS-06](#cis-06) | Eval and release report | AI content quality | event: each eval run finish or release status change | auto | partial | P2 |
| [CIS-07](#cis-07) | Rerun wave and paid-run report with cost | AI content quality | event: each wave close or paid batch | auto | partial | P1 |
| [CIS-02](#cis-02) | Place and geocode quality | Data quality and reconciliation | monthly + after each geocode chain batch | semi | partial | P2 |
| [TP-03](#tp-03) | Inquiry handoff reconciliation (TripPlanner to Booking) | Data quality and reconciliation | hourly check + daily summary 01:00 UTC | auto | missing | P0 |
| [DATA-01](#data-01) | Nightly data integrity digest | Data quality and reconciliation | nightly | auto | partial | P1 |
| [DATA-02](#data-02) | Weekly cross-app reconciliation | Data quality and reconciliation | weekly Monday 01:30 UTC | auto | missing | P2 |
| [DATA-03](#data-03) | Schema and contract change report | Data quality and reconciliation | event + weekly summary Monday in DEV-03 | auto | partial | P3 |
| [DATA-04](#data-04) | Ledger growth and retention compliance | Data quality and reconciliation | monthly business day 2 | auto | partial | P2 |
| [TP-02](#tp-02) | Monthly TripPlanner performance and reliability | Reliability, capacity and SLO | monthly business day 2 + Lighthouse on every frontend release | semi | partial | P2 |
| [OPS-12](#ops-12) | Daily platform health digest | Reliability, capacity and SLO | daily 01:00 UTC, every day | auto | missing | P0 |
| [OPS-13](#ops-13) | Weekly SLO and DB performance check | Reliability, capacity and SLO | weekly Monday: probe 00:43 UTC, report 01:30 UTC | semi | partial | P1 |
| [OPS-08](#ops-08) | Monthly capacity, SLO and availability review | Reliability, capacity and SLO | monthly business day 2 with FI-01 | semi | partial | P1 |
| [OPS-16](#ops-16) | Capacity and growth forecast | Reliability, capacity and SLO | quarterly with EX-05 | semi | missing | P2 |
| [OPS-03](#ops-03) | Backup, restore and rollback drill record | Reliability, capacity and SLO | when a procedure changes and once before prod | manual | partial | P2 |
| [OPS-04](#ops-04) | Incident and postmortem report (incl. cost incidents) | Incidents | event: write within 5 working days of a SEV1-2 | manual | partial | P0 |
| [CRM-06](#crm-06) | Agency access and data-rights report | Security, privacy and legal | monthly + on demand | auto | partial | P3 |
| [SEC-03](#sec-03) | Monthly security hygiene report | Security, privacy and legal | monthly business day 2 | semi | partial | P1 |
| [SEC-05](#sec-05) | Quarterly access review | Security, privacy and legal | quarterly: first session of each quarter, scheduled with the business… | semi | exists | P1 |
| [SEC-08](#sec-08) | Privileged action and audit-log review | Security, privacy and legal | monthly business day 2 | semi | partial | P2 |
| [SEC-09](#sec-09) | Privacy and data-rights report | Security, privacy and legal | quarterly with EX-05 | semi | partial | P2 |
| [SEC-10](#sec-10) | Legal, policy and AI-terms readiness tracker | Security, privacy and legal | monthly count + quarterly full review with EX-05 | semi | partial | P1 |
| [DEV-01](#dev-01) | Monthly delivery and DORA report | Delivery and release | monthly business day 2 | auto | missing | P1 |
| [DEV-02](#dev-02) | Release notes per app | Delivery and release | event: each release-please release | semi | partial | P2 |
| [DEV-03](#dev-03) | Weekly engineering flow | Delivery and release | weekly Monday 01:30 UTC | auto | partial | P1 |
| [OPS-17](#ops-17) | Go-live readiness scorecard | Readiness and sign-off | event: when a go-live date is set, then weekly until go-live | semi | missing | P1 |
| [DEV-04](#dev-04) | UAT sign-off record | Readiness and sign-off | event: once after all technical work or when the business owner says | manual | planned | P2 |
| [CX-01](#cx-01) | Traveller satisfaction and reviews | Customer | monthly business day 2 + complaint alert on each detractor answer | auto | missing | P2 |
| [MKT-01](#mkt-01) | Acquisition and marketing funnel | Growth and marketing | monthly business day 2 + weekly line in EX-01 | auto | missing | P2 |
| [MKT-02](#mkt-02) | SEO and content performance | Growth and marketing | monthly business day 2 | semi | missing | P3 |
| [CIS-04](#cis-04) | Tenant monthly usage statement | Tenant- and agency-facing | monthly business day 2, only for tenants with activity | auto | partial | P3 |
| [CRM-01](#crm-01) | Agency pipeline and conversion | Tenant- and agency-facing | live + monthly in CRM-05 | auto | planned | P1 |
| [CRM-02](#crm-02) | Agency response time and workload | Tenant- and agency-facing | weekly Monday + live tile | auto | missing | P2 |
| [CRM-03](#crm-03) | Agency e-mail channel health | Tenant- and agency-facing | daily job + weekly summary | auto | partial | P2 |
| [CRM-04](#crm-04) | CRM AI assistant usage | Tenant- and agency-facing | monthly in CRM-05 + live | auto | missing | P2 |
| [CRM-05](#crm-05) | Agency monthly summary | Tenant- and agency-facing | monthly business day 2 | auto | missing | P2 |
| [DATA-05](#data-05) | On-demand report or data request | On demand | on demand | on_demand | missing | P1 |

## Executive and business

<a id="ex-01"></a>

### EX-01 Weekly business pack

Vietnamese name: Gói báo cáo kinh doanh hằng tuần.

| Field | Value |
|---|---|
| Audience | business owner (primary reader), tech lead (approver) |
| Decision it supports | Is the program on track this week, is spend inside budget, and which decisions must the business owner make now? |
| Cadence | weekly: auto-draft Monday 01:30 UTC (08:30 ICT) for the previous ISO week in ICT; approved and posted by Tuesday |
| Channel | Jira comment under the weekly platform report epic PR-20 (Vietnamese, @thule mention node, no Linear IDs, no 'ạ'); draft JSON + Markdown in S3 and /admin/reports; Jira draft copy in docs/audits/<date>-S<nnn>-session-close/jira-drafts.md without commercial numbers while the root repo is public |
| Automation | semi |
| Owner | tech lead (approves); agent drafts the narrative and posts after approval |
| Status today | partial |
| Priority | P0 |
| Trigger | Every Monday; a skipped week is back-filled at the next session, one report per week |
| Retention | Jira permanent; shared.report_run row + S3 JSON 5 years |
| Build effort | S (2 engineer-days) once EX-04 and EX-06 exist: template + one CIS endpoint GET /admin/reports/EX-01?period=YYYY-Www returning KPI JSON and a Markdown fragment |
| Running cost | 0 USD (stored snapshots only; no Cost Explorer or LLM API call; narrative written by Claude Code in session) |

Sections:

- Headline: three Vietnamese lines (went well / went wrong / money)
- KPI strip with week-over-week arrows, read from EX-04 snapshots (never typed by hand)
- Shipped per app (CIS, TripPlanner, Booking, Partner/CRM, Infra) from release-please CHANGELOG versions and DEV-03 Done-with-live-verify issues
- Money: week spend, month-to-date vs prorated budget, month-end forecast (from FI-02)
- Demand and catalog headline (TP-01, BK-02 counts, CIS-01 tours live, CIS-05 quality headline)
- Incidents and risks (OPS-04 records, OPS-12 week roll-up, blocked items such as the acc3 Bedrock access incident)
- Next week: top 3-5 items from docs/backlog/README.md
- Decisions needed (options + recommendation; docs/backlog/README.md section 2, docs/guides/ceo.md section 6)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-DEL-SHIPPED Features shipped | Linear issues moved to Done in the ISO week (Mon 00:00 to Sun 23:59 ICT) with merge + deploy + live verify per skill/aa-ship/SKILL.md | Trend; 0 in a week with planned work = red |
| K-COST-MTD Spend month-to-date vs prorated budget | (acc2 MTD from shared.cost_explorer_snapshot + acc3 gross) / (budget x elapsed days / days in month); budgets: acc2 var.total_monthly_budget_usd = 300 (infra/AA-CIS-Infra/accounts/aa365/variables.tf lines 159-162), acc3 var.acc3_budget_monthly_usd = 250 (accounts/acc3-bedrock/cost_guard.tf line 29) | Green <= 1.0, amber 1.0-1.1, red > 1.1 |
| K-LLM-COST-WEEK LLM spend | Sum shared.llm_call_daily.cost_usd for the 7 ICT days, is_shadow split shown | Flag > 1.3 x 4-week average and > 5 USD |
| K-CAT-LIVE Tours live | Defined once in CIS-01 | Flag a drop > 2 % week over week |
| K-DEM-INQ Demand | 7-day sums of tripplanner.v_ops_traffic_daily metrics trip_started, inquiry_sent and booking.v_ops_funnel_daily metrics inquiry_received, confirmed | Trend only (Dev) |
| K-REL-SEV Platform health | SEV1-SEV2 incidents opened in the week (docs/ops/incident-response.md) + count of CloudWatch alarms that fired | 0 SEV1-2; every fired alarm explained |

Data sources:

- Proposed shared.kpi_daily (EX-04; not in docs/architecture/db-schema-reference.md today)
- FI-02, DEV-03, TP-01, BK-02, CIS-01, CIS-05 run outputs (shared.report_run, proposed)
- CHANGELOG.md of each app (apps/*/release-please-config.json)
- docs/backlog/README.md, docs/linear-export/
- Jira PR-20 epic; latest draft example docs/audits/2026-10-27-S253-session-close/jira-drafts.md section 7

Notes: Posted to Jira PR-20 (internal location, not part of the name). Absorbs the draft PR-20 process. Fixes the overlapping cost window of period 3 (docs/audits/2026-10-27-S253-session-close/jira-drafts.md note 5; period 3 drafted but not posted, docs/backlog/README.md line 23). Rules: skill/aa-jira-update/SKILL.md; claims need live evidence per channel (memory jira-claims-need-live-evidence); drafts batched at session end (memory batch-drafts-at-session-end). Budget status depends on roadmap R0 (cost_ops.py budget constant).

<a id="ex-02"></a>

### EX-02 Monthly business review

Vietnamese name: Báo cáo kinh doanh hằng tháng cho chủ doanh nghiệp.

| Field | Value |
|---|---|
| Audience | business owner (reader, decisions), tech lead (author, approver) |
| Decision it supports | Where did the money go and what did it buy, is demand and commercial traction moving, and what must the business owner decide next month (pricing, tenants, go-live, paid runs)? |
| Cadence | monthly: auto-draft business day 2 at 02:00 UTC (09:00 ICT) for the previous month; cost section marked provisional when BD2 falls before day 3 and refreshed automatically on day 3; approved by business day 5 |
| Channel | S3 (Markdown + PDF) and /admin/reports; five-line Vietnamese summary as a Jira comment under the weekly report epic with the link; optional one-page HTML artifact for phone reading; platform-only sections may be copied to docs/audits/<date>-S<nnn>-mbr/ |
| Automation | semi |
| Owner | tech lead (author/approver); business owner (reader) |
| Status today | missing |
| Priority | P1 |
| Trigger | Monthly; also in the go-live month and after any month with a SEV1 |
| Retention | S3 + shared.report_run 10 years (holds commercial aggregates); Jira permanent |
| Build effort | M (3 engineer-days): template + assembly from the other monthly runs; no new page |
| Running cost | 0 USD |

Sections:

- Executive summary, five Vietnamese lines: delivered, money, demand, risks, decisions
- Scorecard: this month vs last month vs 3-month average (EX-04)
- Delivery per app: released versions (DEV-02) and per-app Jira epic highlights; DORA headline (DEV-01)
- Content and catalog: tours published, republished, retired, served; quality gate pass rate (CIS-01, CIS-05)
- Demand funnel: TripPlanner session -> trip started -> inquiry sent -> Booking inquiry -> trip case -> proposal sent -> confirmed (TP-01, BK-02); acquisition sources (MKT-01)
- Commercial summary from FI-07 (aggregates only); shows 'not live (Dev)' until the first real booking
- Partners (EX-03, EX-07 summary)
- Cost and unit costs (FI-01, FI-05 headline): total by app, top 5 movers with reasons, cost per published tour
- Reliability and security: incidents (OPS-04), SLO misses (OPS-13), security hygiene counts (SEC-03), legal readiness count (SEC-10)
- Customer satisfaction headline (CX-01) once real trips complete
- Risks and decisions needed (options + recommendation; clickable decision page per memory artifact-decisions-interactive)
- Goals for next month

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-COST-TOTAL Total platform cost | acc2 Cost Explorer month total + acc3 gross (before credits) + vendor ledgers (Jev shared.decision_log.cost_usd, DataForSEO shared.dfs_call_log.cost_usd, Geoapify geo.geocode_call.cost_usd, OpenAI rows of shared.llm_call_log provider openai) | acc2 <= 300 USD, acc3 <= 250 USD gross |
| K-UNIT-TOUR Cost per published tour | Defined once in FI-05 | Flag MoM increase > 20 %; baseline after 3 months |
| K-BK-CONV Inquiry to confirmed | Defined once in BK-02 (cohort month) | Business owner sets target at go-live; Dev = trend |
| K-DEL-PLAN Delivery reliability | Planned slots for the month in docs/backlog/tracker/plan.json Done with live verify / planned | >= 70 % |
| K-REL-SEV SEV1-SEV2 incidents | Incidents in the month per docs/ops/incident-response.md severity table | 0; each has a postmortem within 5 working days |
| K-PART-PAYING Active paying partners | Defined once in EX-03 | Trend; 0 until first paying tenant |

Data sources:

- Proposed shared.kpi_daily (EX-04)
- FI-01, FI-05, FI-07 (aggregate contract view), EX-03, EX-07, CIS-01, CIS-05, TP-01, BK-02, MKT-01, CX-01, OPS-04, OPS-13, SEC-03, SEC-10, DEV-01 run outputs
- CHANGELOG.md per app, Jira per-app epics PR-22..PR-27
- docs/backlog/README.md section 2, docs/guides/ceo.md section 6, docs/backlog/tracker/plan.json

Notes: docs/guides/ceo.md lines 86-89 promises a monthly cost and capacity summary from November 2026; nothing covers demand, partners or commercial today. Company docs use roles, not names (memory docs-roles-not-names). Business/legal items are calm proposals (memory tech-focus-business-to-thu).

<a id="ex-03"></a>

### EX-03 Partner growth and churn

Vietnamese name: Tăng trưởng và rời bỏ của đối tác (tenant Content studio, đại lý CRM, đối tác B2B).

| Field | Value |
|---|---|
| Audience | business owner, tech lead, AA staff managing partners |
| Decision it supports | Which partners to upsell, rescue or offboard; is the partner business growing; which plan and price work? |
| Cadence | monthly section of EX-02 (business day 2) + live tab; quarterly cohort in EX-05 |
| Channel | New Summary tab on /admin/platform/agencies (merged with the planned S-03 AA insights, AA-966) + CSV; monthly numbers into EX-02 |
| Automation | auto |
| Owner | business owner (decisions); tech lead (build) |
| Status today | missing |
| Priority | P2 |
| Trigger | Becomes P1 at the first paying tenant or agency (docs/guides/ceo.md section 6: no paying tenant yet) |
| Retention | Monthly snapshots in shared.kpi_daily, permanent |
| Build effort | M (3 engineer-days): one CIS endpoint + tab, one crm.ops.v1 aggregate endpoint in AA-Partner (contract change) |
| Running cost | 0 USD |

Sections:

- Partner count by product (Content studio tenant, CRM agency, Booking B2B partner) and plan: active, new, churned
- MRR bridge: start + new + expansion - contraction - churn = end
- Activation headline (detail in EX-07)
- Usage and quota: tours rewritten, API calls, quota %, overage, CRM seats vs member_limit
- Health list: at-risk partners and upsell candidates
- Churn reasons (shared.tenants.cancellation_reason, CRM offboarding)
- Cohort table by sign-up month (quarterly, in EX-05)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-PART-PAYING Active paying partners | shared.tenants is_active and is_canary not true, joined on plan_id to shared.membership_plans with price_usd_monthly > 0, plus crm.tenant status 'active' and is_synthetic false with crm.tenant_entitlement.plan in ('core','pro'), plus booking.b2b_partners status active | Trend; business owner sets the yearly goal |
| K-PART-CHURN Logo churn rate | Partners with shared.tenants.cancelled_at in the month or crm.tenant status moved to 'offboarding'/'offboarded' in the month / active at month start | Amber > 2 %, red > 5 % per month |
| K-PART-MRR MRR (USD) | Sum shared.membership_plans.price_usd_monthly of active non-canary tenants + CRM plan price (price list to be set by the business owner) + overage_usd from shared.v_tenant_monthly_usage | Net revenue retention >= 100 % |
| K-PART-ACT Activation rate | Defined once in EX-07 | >= 60 % |
| K-PART-QUOTA Quota utilisation | Per-tenant quota_tours_pct / quota_calls_pct from shared.v_tenant_monthly_usage; CRM active crm.member rows / crm.tenant_entitlement.member_limit | > 80 % upsell flag; < 10 % for 2 months churn-risk flag |

Data sources:

- shared.tenants, shared.membership_plans, shared.v_tenant_monthly_usage, shared.tenant_api_usage_monthly, shared.tenant_membership_event
- acp_shared.publish_log, acp_shared.acp_quota_ledger
- crm.tenant, crm.tenant_entitlement, crm.v_insight_fact through the crm.ops.v1 feed (CRM tables are RLS; needs a new aggregate endpoint in docs/contracts/crm.ops.v1.openapi.yaml)
- booking.b2b_partners, booking.v_ops_data_totals

Notes: Agencies console is per agency only (apps/AA-CIS-App/api/routers/admin_crm_console.py). Exclude E2E, synthetic (crm.tenant.is_synthetic) and canary (shared.tenants.is_canary) tenants everywhere. CRM pricing is not defined yet: show plan mix until it is.

<a id="ex-04"></a>

### EX-04 Executive KPI scorecard with daily history

Vietnamese name: Bảng chỉ số điều hành có lịch sử theo ngày (xương sống số liệu).

| Field | Value |
|---|---|
| Audience | business owner, tech lead; feeds every periodic report |
| Decision it supports | Is any headline number moving the wrong way vs last week/month, without waiting for a written report? |
| Cadence | daily snapshot 00:30 UTC (07:30 ICT) for the previous ICT day + live on demand; cost values provisional for 48 h (Cost Explorer settles late, docs/ops/finops.md) |
| Channel | /admin/overview new Trend tab + CSV export; feeds EX-01, EX-02, EX-05, FI-05 |
| Automation | auto |
| Owner | tech lead |
| Status today | partial |
| Priority | P0 |
| Trigger | Daily schedule |
| Retention | Forever (one row per KPI per app per day, < 10 MB per year) |
| Build effort | M (3 engineer-days): CIS migration, job kind kpi_snapshot_daily, Trend tab |
| Running cost | 0 USD (DB reads; no Cost Explorer call, DM-10.4) |

Sections:

- KPI tiles with 7/30/90-day sparkline and delta vs prior period
- Cost: spend MTD, month-end forecast vs budget, LLM spend per day per app
- Catalog: tours live, published per day
- Demand: TripPlanner sessions, trips, inquiries; Booking inquiries, proposals, confirmed
- Partners: active tenants, active CRM agencies
- Health: apps green, failed jobs 24 h per job table, alarms in ALARM
- CSV export of the snapshot table for any range

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-COST-FCST Month-end forecast | GET /admin/cost-ops/forecast per account, stored daily (budget side valid only after roadmap R0 fixes the 250 USD constant) | <= budget (300 acc2, 250 acc3) |
| K-LLM-COST-DAY LLM cost per day | shared.llm_call_daily.cost_usd for the ICT day, by app | Flag > 2 x 14-day median |
| K-CAT-LIVE Tours live | Defined once in CIS-01 | Flag drop > 2 % day over day |
| K-TP-TRIPS / K-TP-INQ | tripplanner.v_ops_traffic_daily metric trip_started / inquiry_sent | Trend |
| K-BK-INQ / K-BK-CONF | booking.v_ops_funnel_daily metric inquiry_received / confirmed | Trend |
| K-JOB-FAIL Failed jobs 24 h | Rows with status failed and finished_at in the last 24 h in shared.job, booking.job, tripplanner.job, crm.job (crm via crm.ops.v1) | 0 green, >= 1 amber, >= 5 red |

Data sources:

- apps/AA-CIS-App/api/services/ops_overview/__init__.py (same queries as /admin/overview)
- tripplanner.v_ops_traffic_daily, tripplanner.v_ops_data_totals, booking.v_ops_funnel_daily, booking.v_ops_case_status, booking.v_ops_data_totals
- shared.llm_call_daily, shared.cost_explorer_snapshot, GET /admin/cost-ops/forecast
- gold_aa_internal.v_tour_liveness, gold_aa_internal.published_tours
- shared.job, booking.job, tripplanner.job, crm.ops.v1
- Proposed new CIS table shared.kpi_daily(day, kpi_id, kpi_version, app, value, unit, data_as_of) - not in db-schema-reference.md, needs a CIS migration

Notes: /admin/overview has no history, comparison, export or push (apps/AA-CIS-App/CONTEXT.md). Contract views exclude conf:commercial columns (docs/contracts/ops.overview.v1.md line 17), so revenue tiles wait for FI-07's aggregate view. Backfill from views that keep 400 days (tripplanner migration 015).

<a id="ex-05"></a>

### EX-05 Quarterly business review and annual plan

Vietnamese name: Báo cáo kinh doanh hằng quý và kế hoạch năm.

| Field | Value |
|---|---|
| Audience | business owner (approves budget), tech lead (author) |
| Decision it supports | Strategy and budget for the next quarter or year: which apps to invest in, go-live timing, pricing, vendor changes. |
| Cadence | quarterly: auto-draft with the monthly pack on business day 2 of January, April, July, October; approved by business day 10; annual plan in December or before prod go-live |
| Channel | S3 + /admin/reports; summary as a Jira comment under the weekly report epic; optional Slides-type artifact for presentation |
| Automation | semi |
| Owner | tech lead (author); business owner (approver) |
| Status today | missing |
| Priority | P2 |
| Trigger | Quarter end; prod go-live decision |
| Retention | 10 years (budget record) |
| Build effort | S (1.5 engineer-days): template only, data from monthly runs |
| Running cost | 0 USD |

Sections:

- Quarter in one page (Vietnamese): goals vs results
- Trend of the three monthly reviews: cost, unit costs, demand, partners, revenue
- Budget vs actual for the quarter and year to date (FI-06)
- Vendor and contract review (FI-04 quarterly part)
- Security and compliance: SEC-05 access review status, SEC-09 privacy counts, SEC-10 legal readiness
- Delivery: DORA trend (DEV-01), roadmap next quarter from docs/backlog/tracker/plan.json
- Partner cohorts (EX-03, EX-07)
- Capacity and growth forecast (OPS-16)
- Q4 only: next-year budget per app and prod cost model

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-FIN-QVAR Quarter cost vs budget | Sum of 3 months actual (FI-06) / sum of monthly budgets | <= 100 % |
| K-UNIT-TREND Unit cost trend | FI-05 unit costs, quarter vs previous quarter | Flat or down |
| K-PART-NET Partner net growth | Active paying partners end - start of quarter (EX-03) | Business owner goal |
| K-DEL-ROADMAP Roadmap delivery | Milestones in docs/backlog/tracker/plan.json planned for the quarter and Done / planned | >= 70 % |

Data sources:

- EX-02 runs of the quarter, shared.kpi_daily
- FI-04, FI-06, DEV-01, SEC-05, SEC-09, SEC-10, OPS-16 runs
- docs/backlog/tracker/plan.json, docs/legal/register.md

Notes: Folds in the quarterly 'reconciliation report' named without a template in docs/guides/cto.md. Go-live date and pricing are business-owner decisions (docs/guides/ceo.md section 6).

<a id="ex-06"></a>

### EX-06 Report register and calendar (reports hub)

Vietnamese name: Sổ đăng ký và lịch báo cáo (trung tâm báo cáo).

| Field | Value |
|---|---|
| Audience | tech lead, business owner, agents |
| Decision it supports | Which recurring report is due or overdue, where is the latest copy, who approved it? |
| Cadence | live; due check daily at 02:00 UTC inside the scheduler |
| Channel | /admin/reports (CIS admin) + bell; overdue list in OPS-12 and EX-01 |
| Automation | auto |
| Owner | tech lead |
| Status today | missing |
| Priority | P0 |
| Trigger | Daily |
| Retention | report_run rows permanent |
| Build effort | M (3 engineer-days): YAML schema + loader, report_run table, /admin/reports page; docs reader must accept docs/reports/ (apps/AA-CIS-App/api/services/docs_reader.py excludes audits today) |
| Running cost | 0 USD |

Sections:

- Catalogue: every report ID, family, cadence, owner role, channel, status
- Due list: next due date, last run, run status (scheduled / draft / approved / posted / failed / overdue)
- Latest output links (S3 object, Jira URL, git path, admin page)
- Overdue and failed runs
- Report usage: opens per report in 90 days (to retire unread reports)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-RPT-ONTIME Reports on time | Runs delivered (approved or posted) by due date / runs due in the month | >= 90 % |
| K-RPT-OVERDUE Overdue reports | Runs past due + grace with no approved output | 0; bell after 3 days |
| K-RPT-FAILED Failed generations | Proposed shared.report_run rows with status failed in 7 days | 0 |

Data sources:

- Proposed docs/reports/catalog.yaml + docs/reports/kpis.yaml (root repo, folder does not exist yet; synced to S3 like the docs bundle)
- Proposed shared.report_run, booking.report_run (status via a bk-NNN contract view), crm report status via crm.ops.v1 - none in db-schema-reference.md today
- docs/backlog/README.md section 1 time-gated checks (today the only due-date list)
- shared.notifications (bell)

Notes: Today due dates live only in docs/backlog/README.md and session logs. Replaces the hand-tracked C4.3, C8 and DM-8.10 due dates in skill/aa-session step 6. Register every report ID that shares a namespace with the docs catalog (docs/README.md) in the same PR.

<a id="ex-07"></a>

### EX-07 Partner onboarding funnel

Vietnamese name: Phễu kích hoạt đối tác mới (tenant Content studio và đại lý CRM).

| Field | Value |
|---|---|
| Audience | business owner, AA staff managing partners, tech lead |
| Decision it supports | Where do new tenants and agencies stall between invitation and first value, and who needs a hand-hold call this week? |
| Cadence | weekly Monday 01:30 UTC (stuck list) + monthly in EX-02 |
| Channel | /admin/platform/agencies Onboarding tab + section of EX-03; stuck list in the weekly SES digest to AA admins |
| Automation | auto |
| Owner | AA staff managing partners; business owner reviews |
| Status today | missing |
| Priority | P2 |
| Trigger | Becomes P1 with the first external tenant or agency invitation |
| Retention | Monthly cohort snapshots in shared.kpi_daily, permanent |
| Build effort | M (2.5 engineer-days): CIS query + tab, crm.ops.v1 counts endpoint shared with EX-03 |
| Running cost | 0 USD |

Sections:

- Content studio funnel: tenant created -> first staff sign-in -> brand brief uploaded -> first approved piece -> first publish
- CRM funnel: invitation sent -> invitation accepted -> first trip -> first proposal -> first booked trip
- Median days per step, by sign-up month
- Stuck list: partners more than 7 days on one step, with owner role
- Setup gaps: mailbox not connected (crm.channel_account), no SEO config (shared.tenant_seo_config)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-PART-ACT Activation rate (Content studio) | Tenants created in the cohort month (shared.tenants.created_at, is_canary not true) with a first acp_shared.publish_log row of status 'published' within 14 days / tenants created | >= 60 % |
| K-ONB-CRM CRM activation | Agencies (crm.tenant, is_synthetic false) with a crm.proposal within 14 days of crm.tenant.created_at / agencies created | >= 50 % (set after the first 5 agencies) |
| K-ONB-TTV Time to first value | Median days from tenant or agency creation to first publish (Content studio) or first proposal (CRM) | <= 7 days |
| K-ONB-STUCK Stuck partners | Partners with no step progress for more than 7 days before activation | 0 without an owner note |

Data sources:

- shared.tenants (created_at, last_brand_brief_s3_key, is_canary), shared.tenant_membership_event, shared.tenant_seo_config
- acp_shared.content_piece (status approved), acp_shared.publish_log (status published)
- crm.member_invitation, crm.studio_invitation, crm.tenant, crm.trip, crm.proposal, crm.channel_account via a crm.ops.v1 aggregate endpoint (counts only)

Notes: Counts only across the CRM boundary; AA staff never see agency PII. Exclude E2E, canary and synthetic tenants.

## Cost, FinOps and finance

<a id="fi-01"></a>

### FI-01 Monthly cost review

Vietnamese name: Báo cáo chi phí hằng tháng (nửa chi phí của rà soát năng lực OPS-08).

| Field | Value |
|---|---|
| Audience | tech lead (approves), business owner (five-line Vietnamese summary) |
| Decision it supports | Was the month's spend justified, which items to cut or scale, are we within budget? |
| Cadence | monthly: auto-draft business day 2 at 02:00 UTC; cost provisional when before day 3 (Cost Explorer settles ~48 h, docs/ops/finops.md) and refreshed on day 3; approved by business day 5. First real run: October 2026, on or after 2026-11-03 |
| Channel | docs/audits/<date>-S<nnn>-capacity-review/cost.md via root PR (platform cost is not commercial data) next to the OPS-08 README; Vietnamese summary inside EX-02 and the weekly Jira comment |
| Automation | semi |
| Owner | tech lead |
| Status today | partial |
| Priority | P0 |
| Trigger | Monthly; extra run after a wave that doubles a ledger (docs/architecture/data-standards/03-scaling.md C8) |
| Retention | Permanent in git; month reports read shared.llm_call_daily because raw shared.llm_call_log is kept 180 days (docs/legal/retention-log.md) |
| Build effort | S (2 engineer-days): Download JSON on /admin/platform/cost, scheduled draft, one template replacing docs/templates/cost-report.md |
| Running cost | 0-0.04 USD per month (one Cost Explorer refresh at 0.01 USD per request via the existing CIS client) |

Sections:

- Summary for the business owner (Vietnamese, 5 lines)
- Totals by account (acc2, acc3 gross and credits; retired acc1 = 0 check)
- By App tag: cis, tripplanner, booking, crm, identity, shared, untagged
- Top 5 services and every change > 20 % with reasons
- LLM spend (FI-03 summary, incl. cost per tenant)
- Unit costs (FI-05)
- Budgets, anomalies and hard stops (FI-06)
- Actions

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-COST-ACC2 acc2 total vs budget | Cost Explorer month total (shared.cost_explorer_snapshot.amount_usd for the acc2 account_id) / var.total_monthly_budget_usd 300 (infra/AA-CIS-Infra/accounts/aa365/variables.tf lines 159-162) | <= 100 % |
| K-COST-APP Per-App actual vs budget | shared.cost_explorer_app_snapshot.amount_usd per app_tag vs var.per_app_monthly_budgets (cis 90, tripplanner 10, booking 25, crm 35, identity 10, shared 120; variables.tf lines 184-193) | Each <= 100 %; amber at 80 % |
| K-COST-UNTAGGED Untagged share | Untagged App spend / acc2 total | < 5 % (DM-10.1) |
| K-COST-EXPLAINED Explained movers | Services with MoM change > 20 % and > 2 USD that carry a written reason / all such services | 100 % |
| K-LLM-RECON LLM ledger accuracy (canonical definition) | \|Cost Explorer Bedrock cost on acc3 - sum shared.llm_call_daily.cost_usd where account = acc3\| / Cost Explorer Bedrock cost on acc3 | <= 10 % |

Data sources:

- GET /admin/platform/cost?month=YYYY-MM (apps/AA-CIS-App/api/services/platform_cost.py)
- shared.cost_explorer_snapshot, shared.cost_explorer_app_snapshot, shared.llm_call_daily
- tools/finops/monthly_cost_report.py; docs/ops/cost/README.md; docs/ops/finops.md 'Monthly review'

Notes: Doc catalog ID FIN-02 (docs/README.md). Merged with the cost half of OPS-08, same folder. Script tested on synthetic inputs only (docs/ops/cost/README.md). Do not repeat direct Cost Explorer calls (DM-10.4). Due item AA-896 (docs/backlog/README.md).

<a id="fi-02"></a>

### FI-02 Weekly spend and vendor balance digest

Vietnamese name: Bản tin chi tiêu và số dư nhà cung cấp hằng tuần (e-mail tự động).

| Field | Value |
|---|---|
| Audience | tech lead, business owner (opt-in) |
| Decision it supports | Slow a paid run, top up a vendor credit, or investigate a spend jump before the month closes? |
| Cadence | weekly: Monday 01:30 UTC (08:30 ICT) for the previous ISO week in ICT |
| Channel | SES e-mail to report subscribers + Weekly panel on /admin/cost-ops; headline into EX-01 |
| Automation | auto |
| Owner | tech lead |
| Status today | missing |
| Priority | P1 |
| Trigger | Weekly schedule |
| Retention | Digest JSON in S3 + shared.report_run 2 years; e-mails not kept |
| Build effort | S (2 engineer-days): report_generate handler + SES via the ops_alert_email path (apps/AA-CIS-App/services/jobs/ops_alert_email_job.py, shared/aws_client ses_mailer); add to docs/ops/job-kinds.md |
| Running cost | ~0 USD (SES ~4 e-mails per month) |

Sections:

- Month-to-date spend per account and App vs budget, month-end forecast
- Last 7 days vs previous 7 days per provider: AWS acc2, Bedrock acc3, Jev, DataForSEO, Geoapify, OpenAI
- Top 5 LLM stages by cost this week
- Balances and runway: DataForSEO, Jev credit, acc3 AWS Lift credit (expires 31/12/2026)
- Budget bells, anomaly alerts and spend_budget hard stops in the week
- Link to /admin/cost-ops

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-COST-FCST Forecast / budget | GET /admin/cost-ops/forecast month-end forecast / budget, per account and App (needs roadmap R0: budget constant 250 -> 300 for acc2) | Amber >= 0.8, red >= 1.0 |
| K-COST-WOW Week-over-week change per provider | (last 7 d - prior 7 d) / prior 7 d | Flag > 30 % and > 5 USD |
| K-RUNWAY-DFS DataForSEO runway (days) | Latest shared.dfs_balance_snapshot.balance_usd / average daily shared.dfs_call_log.cost_usd over 14 d | Red < 14 days |
| K-RUNWAY-JEV Jev runway (days) | (sum shared.jev_credit_topup.amount_usd - sum shared.decision_log.cost_usd since the first top-up) / 14-day daily average | Red < 14 days |
| K-RUNWAY-ACC3 acc3 credit runway | Remaining AWS Lift credit (from proposed docs/finance/vendors.yaml) / average daily acc3 gross spend, vs the 31/12/2026 expiry | Flag > 50 USD expiring unused or exhaustion before expiry |

Data sources:

- GET /admin/cost-ops/forecast, /admin/spend/daily (apps/AA-CIS-App/api/routers/admin_llm_ops.py, api/services/cost_ops.py)
- shared.cost_explorer_snapshot, shared.cost_explorer_app_snapshot, shared.llm_call_daily
- shared.decision_log, shared.jev_credit_topup, shared.dfs_call_log, shared.dfs_balance_snapshot, geo.geocode_call
- shared.spend_budget, shared.notifications
- Proposed docs/finance/vendors.yaml (FI-04; folder does not exist yet)

Notes: Only per-event alerts exist today; no digest job kind (docs/ops/job-kinds.md). acc3 credit figures come from memory acc3-budget-is-a-warning and must move into vendors.yaml so the job can read them (amounts out of git while the root repo is public: keep them in Secrets/SSM or S3).

<a id="fi-03"></a>

### FI-03 LLM cost attribution

Vietnamese name: Phân bổ chi phí LLM theo bước, vai trò, model, tenant và app.

| Field | Value |
|---|---|
| Audience | tech lead, engineer, business owner (tenant margin) |
| Decision it supports | Which stage or model to optimise or reroute, which tenant is unprofitable, how much shadow/eval spend to keep? |
| Cadence | monthly section of FI-01 (business day 2) + live |
| Channel | /admin/cost-ops LLM tab with CSV export + FI-01 section |
| Automation | auto |
| Owner | tech lead |
| Status today | partial |
| Priority | P1 |
| Trigger | Monthly; any FI-02 LLM flag |
| Retention | Rollups permanent; raw 180 days |
| Build effort | S (1.5 engineer-days): CSV export, tenant-margin column, reconciliation tile, move the shadow report out of Settings |
| Running cost | 0 USD |

Sections:

- LLM spend by app and stage (month, 6-month trend)
- By model and provider/account (acc3 Bedrock, OpenAI last resort)
- Shadow and eval share (is_shadow, adhoc_* stages)
- Fallback rate and failures (outage windows shown as zero-call days, not savings)
- Cost per tenant (Content studio and CRM) vs plan revenue
- Gateway ledger vs Cost Explorer reconciliation (K-LLM-RECON from FI-01)
- TripPlanner and CRM ledgers

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-LLM-APP LLM spend by app | sum shared.llm_call_daily.cost_usd by app + tripplanner.llm_spend_daily.cost_usd + crm.llm_usage_daily.cost_usd (check overlap with shared.llm_call_daily app values before summing) | Within FI-06 allocation |
| K-LLM-TENANT AI cost per tenant | sum shared.llm_call_daily.cost_usd by tenant_id (Content studio) and sum crm.llm_call.cost_usd_est by tenant_id (CRM, counts via crm.ops.v1) in the month; null tenant_id = platform work | <= 30 % of the tenant's plan price (feeds FI-09 margin) |
| K-LLM-SHADOW Shadow share | cost_usd where is_shadow / total (shared.llm_call_daily) | Flag > 15 % |
| K-LLM-FALLBACK Fallback rate | sum fallback_calls / sum calls (shared.llm_call_daily) | Red > 5 % |
| K-LLM-ADHOC Ad hoc spend | cost_usd where stage like 'adhoc_%' by stage (AA-635 rule) | Each run appears in its CIS-07 or DATA-05 report |
| K-LLM-RECON Ledger vs bill | Defined in FI-01 | <= 10 % |

Data sources:

- shared.llm_call_daily (kept beyond 180 days; has tenant_id), shared.llm_call_log (180 days), shared.llm_shadow_log, shared.llm_role_config, shared.llm_model_catalog
- tripplanner.llm_spend_daily, crm.llm_usage_daily, crm.llm_call
- shared.v_tenant_monthly_usage (llm_cost_usd, price_usd_monthly)
- /admin/cost-ops LLM tab, /admin/llm-usage/tree, /admin/llm-shadow/report (apps/AA-CIS-App/api/routers/admin_llm_ops.py)

Notes: Shadow report is hidden in Settings (admin_llm_ops.py). Since the S257 acc3 incident (docs/backlog/README.md) zero-call days must be labelled as outage.

<a id="fi-04"></a>

### FI-04 Vendor spend, balances and contract register

Vietnamese name: Sổ nhà cung cấp nền tảng: chi phí, số dư, hạn mức, hợp đồng.

| Field | Value |
|---|---|
| Audience | tech lead, business owner |
| Decision it supports | Renew, downgrade, top up or replace a platform vendor; which contracts/DPAs are missing before prod? |
| Cadence | monthly spend in FI-01; quarterly contract review in EX-05; event 30 days before a renewal or credit expiry |
| Channel | Sections of FI-01 / EX-05; renewal bell on /admin |
| Automation | semi |
| Owner | tech lead (register); business owner (contract decisions) |
| Status today | partial |
| Priority | P1 |
| Trigger | Monthly; renewal or expiry dates; any new paid service request (quote + explicit yes, memory cost-advice-new-aws-services) |
| Retention | Register in git, permanent |
| Build effort | S (1 engineer-day): vendors.yaml + read in FI-02 + template section |
| Running cost | 0 USD |

Sections:

- Vendor table: use, plan, fixed fee, usage spend this month, owner role, reseller/payer
- Credits and balances: AWS Lift (acc3), Jev, DataForSEO
- Free-plan headroom: Vercel Hobby, Sentry free, GitHub Actions minutes (private repos), Geoapify free tier, Linear Free (250 unarchived)
- Contracts: start, renewal, notice period, DPA / zero-retention status
- Changes since last review and renewals in the next 60 days

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-VEND-SPEND Vendor spend | Jev shared.decision_log.cost_usd; DataForSEO shared.dfs_call_log.cost_usd; Geoapify geo.geocode_call.cost_usd; OpenAI shared.llm_call_log rows with provider openai; fixed fees from vendors.yaml | Within FI-06 vendor lines |
| K-VEND-EXPIRY Credit expiry risk | Credit forecast to remain at expiry at current burn | Flag > 50 USD |
| K-VEND-HEADROOM Free-plan headroom | Usage / plan limit per free plan | Amber > 70 %, red > 90 % |
| K-VEND-DPA DPA coverage | Personal-data vendors with signed DPA / all such vendors (docs/legal/register.md vendor table; none signed today, line 245) | 100 % before prod go-live |

Data sources:

- docs/legal/register.md vendor section
- docs/guides/cio.md vendor table
- docs/security/secrets-register.md (AWS payer)
- shared.decision_log, shared.jev_credit_topup, shared.dfs_call_log, shared.dfs_balance_snapshot, geo.geocode_call, shared.llm_call_log
- Proposed docs/finance/vendors.yaml (new file, read by FI-02)

Notes: Platform vendors only; travel supplier contracts are in BK-04. No Namecheap auto-renew reminders (memory no-remind-manual-chores). Advice is the best technical option without new contracts or added cost (memory advise-dont-push-contracts). Commercially sensitive amounts stay out of git while the root repo is public.

<a id="fi-05"></a>

### FI-05 Unit economics

Vietnamese name: Chi phí đơn vị (mỗi tour, kế hoạch chuyến đi, booking, đại lý).

| Field | Value |
|---|---|
| Audience | business owner, tech lead |
| Decision it supports | Is the platform getting cheaper per unit of output; what price floor do tenant plans and bookings need? |
| Cadence | monthly section of FI-01 (business day 2) + live endpoint |
| Channel | /admin/platform/cost Unit costs card + FI-01 section; headline into EX-02 |
| Automation | auto |
| Owner | tech lead |
| Status today | partial |
| Priority | P1 |
| Trigger | Monthly |
| Retention | Monthly values in shared.kpi_daily, permanent |
| Build effort | S (1.5 engineer-days): one endpoint + card |
| Running cost | 0 USD |

Sections:

- Unit cost table: this month vs last vs 3-month average
- Numerators (App-tag totals + LLM per app) beside denominators
- LLM units per model: USD per 1,000 calls, per 1M tokens
- Vendor units: Jev per 1,000 decisions, DataForSEO per keyword, Geoapify per 1,000 requests
- Commentary on movers

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-UNIT-TOUR USD per published tour | (cis App total + cis LLM spend) / tours published or republished in the month (gold_aa_internal.published_tours.published_at) | Flag MoM +20 %; baseline after 3 months |
| K-UNIT-TRIP USD per trip plan | (tripplanner App total + tripplanner.llm_spend_daily.cost_usd) / trip_started (tripplanner.v_ops_traffic_daily) | Trend |
| K-UNIT-BOOKING USD per confirmed booking | booking App total / confirmed (booking.v_ops_funnel_daily) | n/a until first booking; then <= 5 % of average booking margin |
| K-UNIT-AGENCY USD per active agency | (crm App total + crm.llm_usage_daily.cost_usd) / active CRM tenants (EX-03) | Below CRM plan price |
| K-UNIT-JEV Jev USD per 1,000 decisions | sum shared.decision_log.cost_usd / count of rows with cached false x 1000 | Trend |

Data sources:

- GET /admin/platform/cost (cost_by_app)
- shared.llm_call_daily, tripplanner.llm_spend_daily, crm.llm_usage_daily
- gold_aa_internal.published_tours, tripplanner.v_ops_traffic_daily, booking.v_ops_funnel_daily
- shared.decision_log, shared.dfs_call_log, geo.geocode_call
- Proposed GET /admin/platform/unit-costs?month=

Notes: Denominators are manual today (docs/ops/finops.md). Dev numbers are trend only; docs/guides/ceo.md lines 86-89 promises cost per published tour from November.

<a id="fi-06"></a>

### FI-06 Budget vs actual and credit runway

Vietnamese name: Ngân sách so với thực chi và thời gian còn dùng credit.

| Field | Value |
|---|---|
| Audience | business owner (approves budget), tech lead (proposes) |
| Decision it supports | Raise, cut or reallocate budgets per app; spend or save credits; approve next year's budget. |
| Cadence | monthly section of FI-01; quarterly in EX-05; annual budget in December or before prod |
| Channel | /admin/cost-ops Budgets tab + FI-01 / EX-05 sections |
| Automation | semi |
| Owner | business owner (approves); tech lead (proposes) |
| Status today | partial |
| Priority | P1 |
| Trigger | Monthly; before any Terraform budget change |
| Retention | Permanent |
| Build effort | S (1.5 engineer-days): read AWS Budgets live instead of the constant (AA-665 C5), annual YAML, variance columns |
| Running cost | 0 USD (DescribeBudgets is free) |

Sections:

- Budget table: account, App, vendor, budget, actual, variance, forecast
- Year to date vs annual plan
- Credits remaining and expiry
- Hard stops hit (shared.spend_budget) and budget alerts fired
- Proposed budget changes (Terraform var.per_app_monthly_budgets) with reasons
- Annual plan and prod cost scenarios (EX-05, Q4)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-FIN-VAR Variance per budget line | (actual - budget) / budget | Amber > 0 %, red > +10 % |
| K-FIN-FCSTACC Forecast accuracy | \|forecast at day 15 - actual\| / actual | <= 15 % |
| K-FIN-YTD YTD vs annual plan | Actual year to date / prorated annual budget | <= 100 % |
| K-FIN-HARDSTOP Hard stops | Calls refused by a shared.spend_budget row with hard_stop true in the month (from the gateway refusal log) | 0 unplanned |

Data sources:

- infra/AA-CIS-Infra/accounts/aa365/variables.tf (total_monthly_budget_usd, per_app_monthly_budgets), accounts/acc3-bedrock/cost_guard.tf
- shared.spend_budget, shared.cost_explorer_snapshot, shared.cost_explorer_app_snapshot
- GET /admin/cost-ops/forecast, /admin/cost-ops Budgets tab
- Proposed docs/finance/budget-<year>.yaml

Notes: Cost Ops reads budgets from AWS_MONTHLY_BUDGET_USD = {acc2: 250, acc3: 250} (apps/AA-CIS-App/api/services/cost_ops.py line 62) unless env COST_OPS_AWS_BUDGETS_USD overrides; Terraform says 300 for acc2. Fix first (roadmap R0). Sum of per-App budgets stays <= the account budget (Terraform precondition, docs/ops/finops.md).

<a id="fi-07"></a>

### FI-07 Revenue, bookings and margin (weekly flash + monthly close)

Vietnamese name: Doanh thu, booking và biên lợi nhuận (bản nhanh tuần + đóng sổ tháng).

| Field | Value |
|---|---|
| Audience | business owner, Booking admin (finance), sales lead |
| Decision it supports | Is the travel business profitable per booking, channel and destination; are pricing rules and supplier contracts right? |
| Cadence | weekly flash Monday 01:30 UTC; monthly flash business day 2 (feeds EX-02); monthly close final by business day 5 |
| Channel | New Booking staff page Finance reports (month picker, CSV/XLSX, PDF of the close) stored under the booking/ prefix of the reports bucket; only aggregate totals reach CIS through a new bk-NNN contract view |
| Automation | auto |
| Owner | Booking admin (finance) prepares; business owner reviews |
| Status today | partial |
| Priority | P2 |
| Trigger | Becomes P0 at the first real booking / prod go-live |
| Retention | 10 years (Vietnam Law on Accounting 88/2015/QH13; confirm with the company accountant) |
| Build effort | M-L (5 engineer-days): Booking endpoint + page + export + aggregate contract view |
| Running cost | 0 USD |

Sections:

- Bookings confirmed and cancelled by channel (B2C, B2B partner via party_tenant_id), destination, trip style; confirmed pax
- GMV and average booking value (approved version total_price at fx_rate_locked)
- Gross margin: sell price - supplier net cost (booking.version_item_costs)
- Cash: invoiced, collected (verified), refunds, supplier payouts
- Pipeline: proposals sent not approved, value at stake
- FX exposure: currencies sold vs paid
- Monthly close checklist: unverified payments, unmatched supplier bills, voided items
- Departures next month
- Five-line Vietnamese summary

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-BK-CONFIRMED Confirmed bookings | Trip cases whose first booking.trip_case_status_history row with to_status 'confirmed' falls in the period | Business owner target at go-live |
| K-BK-GMV GMV | Sum booking.trip_case_versions.total_price (is_approved true) of cases confirmed in the period, converted with fx_rate_locked | Business owner target |
| K-BK-MARGIN Gross margin % | (GMV - sum booking.version_item_costs.net_amount converted from net_currency) / GMV | Red below booking.pricing_rules.floor_margin for the channel |
| K-BK-CASH Cash collected | Sum booking.payments.amount with verified_at not null and voided_at null, by received_on | Matches bank statement at close |
| K-BK-INVOICED Invoiced revenue | Sum booking.invoices.total_amount with issued_at in the month and cancelled_at null, per currency | vs previous month and same month last year |
| K-BK-CANCEL Cancellation rate | Cases reaching 'cancelled' / (confirmed + cancelled) in the period | Flag > 10 % |

Data sources:

- booking.trip_cases, booking.trip_case_versions, booking.version_item_costs (conf:commercial)
- booking.invoices, booking.invoice_items, booking.payments, booking.payment_schedule
- booking.supplier_bills, booking.supplier_payouts, booking.fx_rates, booking.pricing_rules
- booking.trip_case_status_history, booking.v_ops_funnel_daily
- Booking endpoints /booking/billing/summary, /booking/supplier-bills/summary, /booking/trip-cases/summary

Notes: Absorbs draft BK-06 (month-end business review). Finance views are granted to role booking only (docs/architecture/db-schema-reference.md) and ops.overview.v1 excludes conf:commercial (docs/contracts/ops.overview.v1.md line 17): build in AA-Booking, expose aggregates only.

<a id="fi-09"></a>

### FI-09 Tenant billing run

Vietnamese name: Kỳ tính phí tenant và đại lý hằng tháng.

| Field | Value |
|---|---|
| Audience | business owner (approves charges), AA staff (billing) |
| Decision it supports | What each partner owes this month (plan + overage) and whether plans and quotas are priced right. |
| Cadence | monthly, business day 2 for the previous month; approved by business day 5 |
| Channel | CIS admin billing-run view in /admin/reports; statements via CIS-04 and CRM-05 |
| Automation | semi |
| Owner | business owner (approves) |
| Status today | missing |
| Priority | P3 |
| Trigger | First paying tenant or agency (none today, docs/guides/ceo.md section 6) |
| Retention | 10 years once invoices are real (confirm with accountant) |
| Build effort | M (3 engineer-days) |
| Running cost | 0 USD |

Sections:

- Billing run: tenant, plan, plan fee, usage, overage, amount due
- Cost to serve per tenant (LLM + DataForSEO) and margin
- Quota breaches and plan-change suggestions
- Statements issued (links to CIS-04 / CRM-05)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-BILL-AMOUNT Amount billable | price_usd_monthly + overage_usd from shared.v_tenant_monthly_usage; CRM plan fee from crm.tenant_entitlement.plan (price list pending) | Reconciles 100 % with issued invoices |
| K-BILL-OVERAGE Overage share | overage_usd / amount billable | > 30 % two months running = suggest upgrade |
| K-BILL-MARGIN Tenant margin | (amount billable - K-LLM-TENANT - shared.dfs_call_log.cost_usd for the tenant_id) / amount billable | Flag < 50 % |

Data sources:

- shared.v_tenant_monthly_usage, shared.tenant_api_usage_monthly, shared.membership_plans, shared.tenants
- acp_shared.acp_quota_ledger, shared.dfs_call_log, shared.llm_call_daily (tenant_id)
- crm.tenant_entitlement via crm.ops.v1

Notes: Legal tax e-invoices stay in the company's accounting tool; this run only computes amounts.

<a id="bk-03"></a>

### BK-03 Receivables and payables aging with collections

Vietnamese name: Tuổi nợ phải thu, phải trả và thu hồi công nợ.

| Field | Value |
|---|---|
| Audience | Booking admin (finance), sales, contracting staff, business owner |
| Decision it supports | Whom to chase today, which supplier bills to pay this week, is cash enough to pay suppliers before customers pay? |
| Cadence | weekly Monday 01:30 UTC + month-end statement business day 2; overdue items also in BK-01 daily |
| Channel | Booking billing page Aging tab with CSV; weekly e-mail to Booking admin |
| Automation | auto |
| Owner | Booking admin (finance) |
| Status today | missing |
| Priority | P1 |
| Trigger | Becomes P0 at the first real customer invoice |
| Retention | Month-end snapshots 10 years (accounting evidence; confirm with accountant) |
| Build effort | S-M (2.5 engineer-days): views already compute balance and days_overdue |
| Running cost | 0 USD |

Sections:

- AR aging buckets (current, 1-30, 31-60, 61-90, > 90 days) per currency
- Overdue list with next action
- Payments awaiting verification
- Deposits and instalments due before departure
- AP: supplier bills due in 14 days, overdue, paid this week
- Cash gap: AP due vs AR expected in 30 days
- Collection trend

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-AR-OVERDUE AR overdue | sum booking.v_invoice_balance.overdue_amount / sum balance, per currency | Red > 10 % |
| K-AR-AGING Aging buckets | sum booking.v_payment_schedule_status.remaining_amount by days_overdue bucket | > 60 days = 0 |
| K-AR-DSO DSO | Open receivables / invoiced amount in the last 90 days x 90 | <= 30 days |
| K-AR-UNVERIFIED Unverified payments | sum booking.v_invoice_balance.unverified_amount and max age | 0 older than 2 working days |
| K-AP-OVERDUE AP overdue | sum booking.v_supplier_bill_balance.balance where overdue | 0 |

Data sources:

- booking.v_invoice_balance, booking.v_payment_schedule_status, booking.v_supplier_bill_balance
- booking.invoices, booking.payments, booking.supplier_payouts
- GET /booking/billing/summary, /booking/supplier-bills/summary

Notes: Absorbs draft FI-08 and the payables part of draft BK-04. Billing page has KPIs + CSV but no aging (apps/AA-Booking/frontend/app/(staff)/billing/page.tsx).

## Product and app operations

<a id="cis-01"></a>

### CIS-01 Weekly catalog health

Vietnamese name: Sức khoẻ catalog hằng tuần.

| Field | Value |
|---|---|
| Audience | tech lead, content ops, business owner (headline) |
| Decision it supports | Is the sellable catalog complete and current; which countries or tours need rewrite, photos, republish or retirement this week? |
| Cadence | weekly Monday 01:30 UTC + live page; extra run when a rerun wave closes |
| Channel | /admin/data-coverage Weekly tab (stored snapshots) + SES digest to subscribers; headline in EX-01 |
| Automation | auto |
| Owner | tech lead |
| Status today | partial |
| Priority | P1 |
| Trigger | Weekly; wave close |
| Retention | Weekly snapshots 24 months (aggregates, no PII) |
| Build effort | M (3 engineer-days) on top of R1 core |
| Running cost | ~0 USD |

Sections:

- Headline: tours live / paused / retired and week-over-week delta
- Lifecycle events this week with reasons
- S1 rewrite coverage per country (current writer done vs pending)
- Photo and cover coverage per country
- Downstream freshness (from DATA-01)
- Top 10 action list

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-CAT-LIVE Tours live (canonical definition) | Rows of gold_aa_internal.v_tour_liveness with state 'live' at the snapshot; paused and retired counted the same way | No unexplained drop > 2 % week over week (EX-04 uses day over day) |
| K-CAT-COVER Cover coverage | catalog.v_tour rows with cover_photo_path not null / all catalog.v_tour rows | >= 95 %; red < 90 % |
| K-CAT-PHOTO Photo depth | Share of catalog.v_tour rows with photo_count >= 3 | >= 80 % |
| K-CAT-S1 S1 rewrite coverage | Live gold_aa_internal.published_tours (deleted_at null) rewritten by the current S1 writer / all live published tours, same count as /admin/s1-rewrite | 100 %; countries < 90 % listed |
| K-CAT-LIFECYCLE Lifecycle events | gold_aa_internal.tour_lifecycle_event by event (retired, paused, restored, superseded) and reason in the week; superseded events shown with replaced_by_tour_id | Informational; retirements with reason source_deleted or master_trashed listed for review |

Data sources:

- gold_aa_internal.v_tour_liveness, gold_aa_internal.tour_lifecycle_event, gold_aa_internal.published_tours
- catalog.v_tour, shared.place_photo
- /admin/data-coverage service (apps/AA-CIS-App/api/routers/admin_data_coverage.py); DATA-01 freshness results

Notes: Reuse /admin/data-coverage (counts exist, no history: docs/audits/2026-10-26-S252-data-coverage/). Freshness counts live in DATA-01. replaced_by_tour_id is set only for superseded events (tour_lifecycle_event_successor_check).

<a id="cis-03"></a>

### CIS-03 Tenant content delivery (internal)

Vietnamese name: Phân phối nội dung cho tenant (nội bộ AA).

| Field | Value |
|---|---|
| Audience | AA admin, tech lead, business owner |
| Decision it supports | Which tenants get value; where does the T-series hold or regenerate too much; who is near quota or overage? |
| Cadence | monthly business day 2 + live |
| Channel | /admin/tenant-activity Monthly tab; SES digest to AA admins |
| Automation | auto |
| Owner | AA admin (reviewer role) |
| Status today | partial |
| Priority | P2 |
| Trigger | Month end; becomes P1 at the first paying tenant |
| Retention | Monthly snapshots 36 months (billing evidence) |
| Build effort | M (2.5 engineer-days) |
| Running cost | ~0 USD |

Sections:

- Pieces approved / held / failed per tenant and channel
- Held reasons, top 5
- Regeneration rate
- Publish results per channel
- Quota and overage per tenant
- LLM cost per approved piece

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-TEN-DELIVERED Delivered pieces | acp_shared.content_piece with status 'approved' and created_at in the month, per tenant (status values: processing, approved, held, failed) | Trend |
| K-TEN-HELD Held rate | content_piece status 'held' / pieces created in the period | < 10 %; red > 20 % |
| K-TEN-REGEN Regeneration rate | pieces with attempt_number > 1 / all pieces | < 15 % |
| K-TEN-PUBLISH Publish success | acp_shared.publish_log status 'published' / attempts with status published or failed, per channel | >= 98 % |
| K-TEN-PIECECOST LLM cost per delivered piece | shared.v_tenant_monthly_usage.llm_cost_usd / delivered pieces | Margin alert if cost > 30 % of plan price |

Data sources:

- acp_shared.content_piece, acp_shared.publish_log
- shared.v_tenant_monthly_usage, shared.tenant_rewrite_usage, shared.tenant_api_usage_monthly
- /admin/tenant-activity, /admin/content-quality

Notes: Content Trace is row-level only today. QA, gates and held details stay internal (memory tenant-sees-content-only).

<a id="tp-01"></a>

### TP-01 Weekly TripPlanner funnel

Vietnamese name: Phễu TripPlanner hằng tuần.

| Field | Value |
|---|---|
| Audience | business owner, tech lead |
| Decision it supports | Is the B2C planner turning visitors into advisor inquiries; where does the funnel leak? |
| Cadence | weekly Monday 01:30 UTC + live card |
| Channel | /admin/overview TripPlanner card with week/month comparison; SES digest; headline in EX-01 |
| Automation | auto |
| Owner | tech lead |
| Status today | partial |
| Priority | P1 |
| Trigger | Weekly |
| Retention | View keeps 400 days; weekly snapshots 36 months |
| Build effort | S (1.5 engineer-days), CIS only |
| Running cost | 0 USD |

Sections:

- Sessions, trips started, trips edited, inquiries sent (week + 4-week trend)
- Step conversion
- AI searches and keyword-fallback share
- TripPlanner LLM spend vs daily cap
- Top pinned components

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-TP-SESSIONS Sessions | sum n of tripplanner.v_ops_traffic_daily metric planner_session_started | Trend until prod traffic |
| K-TP-S2T Session to trip | trip_started / planner_session_started | >= 25 % (baseline after first prod month) |
| K-TP-T2I Trip to inquiry | inquiry_sent / trip_started | >= 5 % (baseline after first prod month) |
| K-TP-LLMCAP LLM spend vs cap | tripplanner.llm_spend_daily.cost_usd per UTC day (online stages) vs TP_DAILY_SPEND_CAP_USD (placeholder default 5.0, apps/AA-TripPlanner-Web/backend/config.py lines 117-122; business cap still open) | < 80 % of cap any day |

Data sources:

- tripplanner.v_ops_traffic_daily (tp-015), tripplanner.v_ops_pin_components, tripplanner.llm_spend_daily
- shared.llm_call_log stage tp_search_embed
- /admin/overview ops section

Notes: Metric names are contract (docs/contracts/ops.overview.v1.md): add, never rename (apps/AA-TripPlanner-Web/migrations/015_ops_overview_view.sql). Acquisition sources are in MKT-01.

<a id="bk-01"></a>

### BK-01 Booking daily operations digest

Vietnamese name: Bản tin vận hành Booking mỗi sáng.

| Field | Value |
|---|---|
| Audience | ops staff, sales, Booking admin |
| Decision it supports | What must staff do today: overdue checks, unconfirmed suppliers, expiring quotes and holds, unpaid deposits for near departures? |
| Cadence | daily 01:00 UTC (08:00 ICT), Monday to Friday (Monday covers the weekend) |
| Channel | One e-mail per staff member via bk_notify_email + Booking dashboard Today panel |
| Automation | auto |
| Owner | ops staff (Booking admin owns recipients) |
| Status today | partial |
| Priority | P1 |
| Trigger | Daily; must be live before the first production booking |
| Retention | Digest rows 90 days |
| Build effort | M (2.5 engineer-days): extend bk_ops_reminders to compose one digest (reminders are in-app only, apps/AA-Booking/backend/app/ops/invoices.py) |
| Running cost | ~0 USD (SES) |

Sections:

- Departures in 14 days with blockers
- Overdue trip checks by assignee
- Supplier requests waiting > 48 h
- Quotes/proposals expiring in 3 days
- B2B holds expiring in 48 h
- Payments recorded but not verified
- Inquiries parked or failed (TP-03)
- Open departure incidents (BK-06)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-BK-OVERDUECHECKS Overdue checks | sum booking.v_trip_check_board.checks_overdue | 0; red if a case departs within 7 days with overdue checks |
| K-BK-ATRISK At-risk departures | v_trip_check_board rows with start_date within 14 days and suppliers_confirmed false or payment_verified false | 0 at T-7 |
| K-BK-SUPPENDING Pending supplier confirmations | booking.supplier_bookings with status 'requested', requested_at older than 48 h | 0 |
| K-BK-EXPIRING Expiring quotes and holds | booking.trip_case_versions with is_sent_to_customer true, is_approved false, valid_until within 3 days; booking.b2b_quotes valid_until within 3 days; booking.b2b_holds status 'active' with expires_at within 48 h | Each listed with owner |
| K-BK-UNVERIFIED Unverified payments | sum booking.v_invoice_balance.unverified_count | 0 older than 2 working days |

Data sources:

- booking.v_trip_check_board, booking.supplier_bookings, booking.trip_case_versions, booking.b2b_quotes, booking.b2b_holds, booking.v_invoice_balance, booking.notifications, booking.departure_incidents
- bk_case_lifecycle / bk_ops_reminders (apps/AA-Booking/backend/app/ops/lifecycle.py)

Notes: v_invoice_balance and v_payment_schedule_status are granted to role booking only, so it lives in Booking. Names and codes only in the mail, no passport or contact data.

<a id="bk-02"></a>

### BK-02 Booking sales pipeline

Vietnamese name: Phễu bán hàng Booking (tuần/tháng).

| Field | Value |
|---|---|
| Audience | business owner, sales lead |
| Decision it supports | How fast and how often do inquiries become confirmed trips; which source and channel convert; where do cases stall? |
| Cadence | weekly Monday 01:30 UTC (sales) + monthly business day 2 (business owner) |
| Channel | Booking dashboard Reports tab with CSV; counts to CIS through ops.overview.v1 |
| Automation | auto |
| Owner | business owner |
| Status today | partial |
| Priority | P2 |
| Trigger | Weekly and month end |
| Retention | Monthly snapshots 5 years |
| Build effort | M (3 engineer-days) |
| Running cost | 0 USD |

Sections:

- Funnel by source_system and channel: inquiries, cases, proposal sent, confirmed, cancelled
- Conversion per step, month over month
- Time to first proposal and to confirmation (median, p90)
- Open cases by status and age
- Quoted and confirmed value (inside Booking only)
- Lost/cancel reasons

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-BK-CONV Inquiry to confirmed | Cases whose first booking.trip_case_status_history row with to_status 'confirmed' exists / inquiry_received, same cohort month | Baseline after first prod quarter; alert on -20 % vs trailing 3 months |
| K-BK-TTP Time to first proposal | median(first changed_at with to_status 'proposal_sent' - booking.trip_cases.created_at) | <= 48 h |
| K-BK-TTC Time to confirm | median and p90 of first 'confirmed' changed_at - created_at | Tracked |
| K-BK-STALLED Stalled cases | booking.trip_cases not in completed/cancelled with last status change > 7 days ago | 0 without a note |

Data sources:

- booking.v_ops_funnel_daily, booking.v_ops_case_status, booking.trip_case_status_history, booking.trip_cases, booking.trip_case_versions
- GET /booking/trip-cases/summary

Notes: Value metrics stay in Booking (conf:commercial). Status values from trip_cases_status_chk.

<a id="bk-04"></a>

### BK-04 Supplier performance and contract renewals

Vietnamese name: Hiệu suất và hợp đồng nhà cung cấp du lịch.

| Field | Value |
|---|---|
| Audience | contracting staff, Booking admin |
| Decision it supports | Which suppliers confirm slowly, decline often or cause incidents; which contracts to renew or renegotiate before they expire? |
| Cadence | monthly business day 2; contract expiry check weekly Monday |
| Channel | Booking suppliers page Performance tab + CSV; expiry list in the BK-01 digest on Mondays |
| Automation | auto |
| Owner | contracting staff |
| Status today | partial |
| Priority | P3 |
| Trigger | Month end; meaningful after real suppliers |
| Retention | 5 years |
| Build effort | S (2 engineer-days) |
| Running cost | 0 USD |

Sections:

- Confirmation lead time per supplier
- Decline and cancellation rates with decline codes
- Volume per supplier
- Supplier-caused departure incidents (BK-06)
- Contracts expiring in 60 days and contracts already expired with live bookings

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-SUP-LEAD Confirmation lead time | median(confirmed_at - requested_at) per supplier_id in booking.supplier_bookings | <= 48 h |
| K-SUP-DECLINE Decline rate | supplier_bookings with declined_at not null / rows with requested_at not null, per supplier | < 10 % |
| K-SUP-CONTRACT Contracts expiring | booking.supplier_contracts with valid_to within 60 days and status not expired, per supplier | Each has a renewal owner; 0 expired with future service_date bookings |
| K-SUP-INCIDENT Supplier incidents | booking.departure_incidents with incident_code 'supplier' in the period | Trend; > 2 per supplier per quarter = review |

Data sources:

- booking.supplier_bookings, booking.supplier_contracts, booking.suppliers, booking.departure_incidents
- GET /booking/supplier-bookings/summary, /booking/suppliers/summary

Notes: Payables moved to BK-03. Summary tiles exist; add period, per-supplier breakdown and contract expiry. Platform vendors are in FI-04.

<a id="bk-05"></a>

### BK-05 B2B partner desk report

Vietnamese name: Kênh B2B: báo giá và giữ chỗ.

| Field | Value |
|---|---|
| Audience | sales lead, business owner |
| Decision it supports | Are partner agencies converting holds into bookings; are hold rules right? |
| Cadence | monthly business day 2 |
| Channel | Booking b2b-desk Report tab + CSV |
| Automation | auto |
| Owner | sales lead |
| Status today | partial |
| Priority | P3 |
| Trigger | First real B2B partner |
| Retention | 5 years |
| Build effort | S (1 engineer-day) |
| Running cost | 0 USD |

Sections:

- Quotes priced per partner
- Holds created, confirmed, released, expired, extended
- Hold to confirm rate and average hold life
- FX buffer and margin applied (internal)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-B2B-H2C Hold to confirm | booking.b2b_holds with confirmed_at not null / holds created | >= 40 % (baseline after first prod quarter) |
| K-B2B-EXPIRED Expired holds | holds with expired_at not null / holds created | < 30 % |
| K-B2B-EXT Extensions per hold | avg booking.b2b_holds.extended_count | <= 1 |

Data sources:

- booking.b2b_quotes, booking.b2b_holds, booking.b2b_partners
- /b2b-desk summary (apps/AA-Booking/backend/app/routers/b2b_desk.py)

Notes: About 2 holds on Dev today.

<a id="bk-06"></a>

### BK-06 Departure fill and incidents

Vietnamese name: Lấp đầy chuyến khởi hành và sự cố trên tuyến.

| Field | Value |
|---|---|
| Audience | ops staff, sales lead, business owner |
| Decision it supports | Which fixed departures will run, need a push or should be cancelled; are on-trip incidents cleared fast? |
| Cadence | weekly Monday 01:30 UTC; open incidents also in BK-01 daily |
| Channel | Booking departures page Report tab + CSV |
| Automation | auto |
| Owner | ops staff |
| Status today | missing |
| Priority | P3 |
| Trigger | First published fixed departure |
| Retention | 5 years |
| Build effort | S (1.5 engineer-days); confirm the pax link from departures to bookings in db-schema-reference.md before building |
| Running cost | 0 USD |

Sections:

- Departures in 60 days: capacity, booked pax, fill %
- Departures below the minimum fill at T-30
- Incidents by code (weather, road, health, political, supplier, other), open and cleared
- Time to clear incidents

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-DEP-FILL Fill rate | Booked pax (b2b hold lines and trip cases linked to the departure) / booking.departures.capacity, per departure | Business owner sets the go/no-go floor; flag < floor at T-30 |
| K-DEP-INC Open incidents | booking.departure_incidents with cleared_at null | 0 older than 24 h without a note |
| K-DEP-TTC Time to clear | median(cleared_at - flagged_at) per incident_code | Trend |

Data sources:

- booking.departures, booking.departure_incidents, booking.b2b_hold_lines, booking.trip_plans, booking.trip_cases
- booking.outbox (departure_id, incident_code events)

Notes: Incident codes from departure_incidents_code_chk. No traveller data in the report.

<a id="ops-14"></a>

### OPS-14 Job runner health (all job tables)

Vietnamese name: Sức khoẻ bộ chạy job của cả bốn app.

| Field | Value |
|---|---|
| Audience | engineer, tech lead |
| Decision it supports | Which job kinds fail, retry, run late or never run; tune concurrency or fix code? |
| Cadence | weekly Monday 01:30 UTC (section of OPS-13) + daily failures in OPS-12 |
| Channel | /admin/jobs new All apps tab; weekly section |
| Automation | auto |
| Owner | engineer on duty |
| Status today | partial |
| Priority | P1 |
| Trigger | Weekly |
| Retention | Weekly aggregates 24 months |
| Build effort | S-M (2 engineer-days): Booking and TripPlanner status views granted to cis_app (bk-NNN, tp-NNN) + tab |
| Running cost | 0 USD |

Sections:

- Per app and kind: runs, failures, retries, p95 duration vs expected (docs/ops/job-kinds.md)
- Overdue running rows and queue age
- Kinds that never ran in 30 days
- Deploy-gate blocks and overrides
- Paid-call kinds: cost per run

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-JOB-FAILRATE Failure rate per kind | Rows with status failed / rows finished (finished_at in the window) per kind (shared.job, booking.job, tripplanner.job, crm.job via crm.ops.v1) | < 2 % |
| K-JOB-P95 Duration vs expected | p95(finished_at - started_at) / expected seconds per kind | < 1.0 |
| K-JOB-QUEUEAGE Queue age p95 | p95(started_at - greatest(created_at, run_after)) per kind (job tables have no claimed_at) | < 5 min for foreground kinds |
| K-JOB-DEAD Dead kinds | Registered scheduled kinds with no run in 30 days | 0 |

Data sources:

- shared.job, shared.job_worker, booking.job, tripplanner.job, crm.ops.v1 failed jobs feed
- docs/ops/job-kinds.md
- /admin/jobs, /admin/job-runner/summary (apps/AA-CIS-App/api/routers/admin_job_runner.py)

Notes: /admin/jobs shows the CIS queue only today. Memory job-runner-in-api-process: always state job vs ECS exec in reports.

<a id="ops-15"></a>

### OPS-15 Session-close state snapshot

Vietnamese name: Ảnh chụp trạng thái cuối phiên (máy đọc được).

| Field | Value |
|---|---|
| Audience | tech lead, next agent session |
| Decision it supports | What exactly is live now (images, migrations, jobs, PRs) so the next session starts from facts? |
| Cadence | every session close (event) |
| Channel | docs/audits/<date>-S<nnn>-session-close/state-snapshot.md + state-snapshot.json via root PR |
| Automation | semi |
| Owner | tech lead (agent runs it) |
| Status today | partial |
| Priority | P1 |
| Trigger | Every session close |
| Retention | Permanent in git |
| Build effort | S (2 engineer-days): one read-only script printing JSON + Markdown |
| Running cost | 0 USD |

Sections:

- ECS services: task definition, image SHA, rollout state, api/worker SHA match
- Health: /health and /health/ready per app
- Migrations: latest per owner
- Lambda versions/aliases, Vercel production commits per project
- Job tables: queued/running per owner (shared.job, booking.job, crm.job, tripplanner.job), open waves
- Open PRs per repo, repo heads

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-SNAP-COVERAGE Snapshot coverage | Checks captured / checks in the script list | 100 % |
| K-SNAP-DRIFT Drift found | Services whose live SHA differs from main head without an open PR | 0 |

Data sources:

- skill/aa-session/SKILL.md (end of session, step 2)
- Single-line AWS CLI (ECS, Lambda), gh, Vercel MCP list_deployments
- Latest example docs/audits/2026-10-29-S257-session-close/state-snapshot.md

Notes: A script fixes coverage (job tables of all four apps, Vercel production commits) and enables trends.

## AI content quality

<a id="cis-05"></a>

### CIS-05 Weekly AI content quality KPIs

Vietnamese name: KPI chất lượng nội dung AI hằng tuần (Writing Memory).

| Field | Value |
|---|---|
| Audience | tech lead, reviewer |
| Decision it supports | Is writing quality stable or drifting; keep or roll back the active writing-memory release; is the judge reliable enough to gate? |
| Cadence | weekly Monday 01:30 UTC |
| Channel | /admin/writing-memory KPIs tab + SES digest; headline in EX-01 |
| Automation | auto |
| Owner | tech lead |
| Status today | planned |
| Priority | P1 |
| Trigger | Weekly; any regression_detected |
| Retention | Weekly snapshots 24 months |
| Build effort | M (3 engineer-days; planned as AA-922, slot S262, docs/backlog/README.md) |
| Running cost | 0 USD for the report; eval runs stay manual and paid (eval-regression.yml is dispatch-only) |

Sections:

- Judge agreement (kappa) of the latest eval vs threshold, with its date
- Gate fire rates per gate, 4-week trend
- Held and flagged rates in tenant and admin content
- Average quality score
- Writing signals captured and rules active
- Active release per writer (a1, t2, t9_blog, t9_social), reverify flags
- Disagreement queue size and age

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-AIQ-KAPPA Judge kappa | shared.prompt_eval_runs.judge_kappa of the latest run with finished_at not null, per writer | >= 0.6 to let the judge gate (AA-919 best 0.562) |
| K-AIQ-REGRESSION Regression flag | shared.prompt_eval_runs.regression_detected true for runs finished in the week | 0; any true triggers CIS-06 review |
| K-AIQ-GATEFIRE Gate fire rate per gate | Share of acp_shared.content_piece rows whose gate_ledger records a fail for the gate | Within +/-5 points of the 4-week median |
| K-AIQ-SCORE Average quality score | avg silver_aa_internal.quality_scores.score_overall with evaluated_at in the week | No drop > 3 points week over week |
| K-AIQ-RELEASE Release status | shared.writing_memory_release rows with status 'active' per writer; reverify true with reverify_at older than 7 days | 0 stale reverify flags |

Data sources:

- shared.prompt_eval_runs, shared.eval_item_result, shared.writing_memory_release, shared.writing_signal, shared.writing_rule
- acp_shared.content_piece.gate_ledger, silver_aa_internal.quality_scores
- /admin/writing-memory, /admin/content-quality, /admin/platform-stats

Notes: Reads stored eval rows only, never triggers paid evals. LLM paths blocked on acc3 since S257 (docs/backlog/README.md), so kappa may be stale; always print its date.

<a id="cis-06"></a>

### CIS-06 Eval and release report

Vietnamese name: Báo cáo đánh giá / phát hành prompt (theo sự kiện).

| Field | Value |
|---|---|
| Audience | tech lead, reviewer |
| Decision it supports | Approve, reject or roll back a writing-memory release or prompt version. |
| Cadence | event: each eval run finish or release status change |
| Channel | /admin/writing-memory release drawer with a printable summary; JSON in S3 |
| Automation | auto |
| Owner | reviewer |
| Status today | partial |
| Priority | P2 |
| Trigger | prompt_eval_runs.finished_at set or writing_memory_release.status change |
| Retention | Life of the release + 24 months |
| Build effort | S (1 engineer-day) |
| Running cost | 0 USD |

Sections:

- Release and baseline identifiers
- Verdict, kappa, quality delta vs baseline
- Gate pass/fail counts
- Cost vs cost cap
- Top 10 item-level regressions
- Approval record

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-EVAL-DELTA Quality delta | prompt_eval_runs.avg_quality_score - baseline_avg_quality_score | >= 0 to approve |
| K-EVAL-GATEPASS Gate pass | gate_pass_count / (gate_pass_count + gate_fail_count) | >= baseline |
| K-EVAL-COST Eval cost | prompt_eval_runs.cost_usd vs cost_cap_usd | <= cap |

Data sources:

- shared.prompt_eval_runs, shared.eval_item_result, shared.writing_memory_release
- shared.llm_call_log (eval stage)

Notes: ReleasesTab exists; add a printable summary, not a new page.

<a id="cis-07"></a>

### CIS-07 Rerun wave and paid-run report with cost

Vietnamese name: Báo cáo wave chạy lại và đợt chạy trả tiền (kèm chi phí).

| Field | Value |
|---|---|
| Audience | tech lead, business owner (large runs) |
| Decision it supports | Was the wave complete and within budget; start, scale or stop the next wave? |
| Cadence | event: each wave close or paid batch; daily stuck check exists (POST /admin/waves/check) |
| Channel | Small /admin/waves page (none today) + Markdown in docs/audits/<date>-S<nnn>-<wave>/; summary line in EX-01 |
| Automation | auto |
| Owner | tech lead |
| Status today | partial |
| Priority | P1 |
| Trigger | Wave close; paid runs follow trial ~3 then <= ~50 tours (memory paid-runs-subset) |
| Retention | Permanent (audit evidence) |
| Build effort | S-M (2.5 engineer-days): cost block in services/waves/report.py + page |
| Running cost | 0 USD for the report |

Sections:

- Scope: expected vs done vs stuck tours
- Gate and Jev outcomes
- Cost per stage (S1 rewrite, review, atomize, judges, Jev, DataForSEO, geocoding)
- Wave total, running total vs approved cap, USD per tour, projection for the full country/catalog
- Failures and retry cost
- Next-wave recommendation

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-WAVE-DONE Completion | Done tours / shared.rerun_wave.expected_tour_ids | 100 % before closing |
| K-WAVE-UNIT USD per tour | Wave cost (shared.llm_call_log + shared.decision_log + shared.dfs_call_log + geo.geocode_call, joined by job_id to the wave's shared.job rows) / tours done | Within approved estimate +20 % and the shared.spend_budget per_run_usd cap |
| K-WAVE-RUNNING Running total vs cap | Sum of all waves in the run / approved cap | Stop at 100 % |
| K-WAVE-RETRY Retry waste | Cost of attempts that failed / wave total | < 10 % |
| K-WAVE-STUCK Stuck tours | Expected tours with no progress since shared.rerun_wave.last_checked_at | 0 at close |

Data sources:

- GET /admin/waves/{id}/report (apps/AA-CIS-App/api/routers/admin_waves.py, apps/AA-CIS-App/services/waves/report.py)
- shared.rerun_wave, shared.job (cost_usd, attempt)
- shared.llm_call_log, shared.decision_log, shared.dfs_call_log, geo.geocode_call (job_id)

Notes: Absorbs draft FI-11. Removes the hand-written cost section required by memory wave-report-cost. Example: docs/audits/2026-10-24-S249-s1-wave50/README.md.

## Data quality and reconciliation

<a id="cis-02"></a>

### CIS-02 Place and geocode quality

Vietnamese name: Chất lượng địa điểm và geocode.

| Field | Value |
|---|---|
| Audience | tech lead, content ops |
| Decision it supports | Is place data accurate enough for TripPlanner maps and Booking itineraries; continue, change or stop the geocode chain (AA-997)? |
| Cadence | monthly (business day 2) + after each geocode chain batch |
| Channel | /admin/places summary card; accuracy audit Markdown in docs/audits/<date>-S<nnn>-geo-quality/ |
| Automation | semi |
| Owner | tech lead |
| Status today | partial |
| Priority | P2 |
| Trigger | Chain batch completion or monthly |
| Retention | 24 months |
| Build effort | S (1.5 engineer-days) for counts; accuracy stays a sampled audit labelled by the agent panel |
| Running cost | 0 USD (no paid API for the report) |

Sections:

- Accuracy on the fixed 600-row audit sample (S254) vs target
- Chain progress and projected end accuracy
- Outliers present and merges awaiting review
- Geocode calls and cost
- Places without coordinates or low precision per country

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-GEO-ACC Geocode accuracy | Correct rows / audited rows on the fixed S254 600-row sample (method of the AA-997 interim audit) | >= 90 % (S257 interim 77.7 %, projection ~79.5 %, docs/backlog/README.md) |
| K-GEO-OUTLIERS Outliers | Rows in geo.place_outlier at the snapshot, and rows with observed_at in the period (the table has no resolution column) | Downward; red if growing two periods running |
| K-GEO-COST Geocode spend | sum geo.geocode_call.cost_usd, requests and credits with called_at in the period | Within the Geoapify credit plan; bell at 80 % |
| K-GEO-TOURPLACE Tour-place coverage | Live tours (K-CAT-LIVE) with at least one geo.tour_place row / live tours | >= 98 % |

Data sources:

- geo.geocode_call, geo.place_outlier, geo.place_merge, geo.tour_place, catalog.v_tour_place
- /admin/places (MergesTab, LinesTab)
- docs/backlog/README.md (AA-997 interim figures)

Notes: Accuracy needs ground truth; keep the fixed sample so numbers stay comparable (memory claude-audits-quality).

<a id="tp-03"></a>

### TP-03 Inquiry handoff reconciliation (TripPlanner to Booking)

Vietnamese name: Đối soát yêu cầu tư vấn TripPlanner sang Booking (mỗi giờ + tổng hợp ngày).

| Field | Value |
|---|---|
| Audience | ops staff, tech lead |
| Decision it supports | Did every customer inquiry reach Booking and become a trip case; which ones are parked or failed? |
| Cadence | hourly check (cheap view reads) + daily summary 01:00 UTC (08:00 ICT) |
| Channel | Line in OPS-12 and BK-01; bell (shared.notifications) + ops alert e-mail only when a gap exists |
| Automation | auto |
| Owner | ops staff |
| Status today | missing |
| Priority | P0 |
| Trigger | Hourly; alert when gap > 0 |
| Retention | Daily results 90 days |
| Build effort | S (1.5 engineer-days): one CIS report handler + one grant/view for inbox status |
| Running cost | 0 USD |

Sections:

- Inquiries sent vs received per day
- Parked and failed inquiries with age
- Received but no trip case after 24 h
- Mismatches over the last 7 days

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-TP-HANDOFFGAP Handoff gap | tripplanner.v_inquiry_outbox rows older than 15 min with no booking.inbox_events row of the same idempotency_key; daily view: v_ops_traffic_daily inquiry_sent - v_ops_funnel_daily inquiry_received (source_system tripplanner) per closed day | 0; any gap = alert at the next hourly check |
| K-BK-PARKED Parked/failed inquiries | booking.v_ops_funnel_daily metrics inquiry_parked + inquiry_failed; age from booking.inbox_events (status, received_at, processed_at) | 0 open older than 4 h |
| K-BK-INQ2CASE Inquiry to case | trip_case_created / inquiry_received, same source_system | 100 % within 24 h |

Data sources:

- tripplanner.v_ops_traffic_daily, tripplanner.v_inquiry_outbox, booking.v_ops_funnel_daily (bk-017; granted to cis_app per db-schema-reference.md)
- booking.inbox_events (needs a bk-NNN grant or contract view for cis_app if read from CIS)

Notes: Silent lead loss is the highest business risk before production; detectable on Dev today with E2E inquiries.

<a id="data-01"></a>

### DATA-01 Nightly data integrity digest

Vietnamese name: Bản tin toàn vẹn dữ liệu hằng đêm (tổng hợp các probe).

| Field | Value |
|---|---|
| Audience | tech lead, engineer |
| Decision it supports | Did any nightly integrity probe fail; which layer is stale or drifting? |
| Cadence | nightly (02:17-05:13 UTC); reported in the next OPS-12 digest at 01:00 UTC (results about 20 h old, run time printed) |
| Channel | Each workflow uploads a summary JSON to the reports bucket; section of OPS-12; weekly roll-up in CIS-01 |
| Automation | auto |
| Owner | tech lead |
| Status today | partial |
| Priority | P1 |
| Trigger | Nightly |
| Retention | JSON 1 year |
| Build effort | S (2 engineer-days): one reusable upload step + least-privilege OIDC role in Infra |
| Running cost | 0 USD |

Sections:

- Probe results: migration copy guard (02:17 UTC), contract copy guard (02:29), connection budget (02:43), schema dump/drift (03:43), isolation (04:13), CRM key policy diff (04:29), tour liveness gate (04:43), freshness (05:13)
- Stale rows aged > 24 h per downstream layer
- Liveness gate violations
- Unexpected schema drift

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-DATA-PROBES Probes passed | Nightly integrity workflows with conclusion success / scheduled runs | All |
| K-DATA-STALE Stale rows > 24 h | Sum of aged > 24 h counts per layer from db-freshness-probe (segments, ranking, routes, geo.tour_place, place cards, seo_context vs published_tours) | 0 (enforcing since S253) |
| K-DATA-LIVENESS Liveness violations | Rows flagged by db-tour-liveness-gate | 0 |
| K-DATA-DRIFT Schema drift | Structure changes in the dump not explained by a registered migration | 0 |

Data sources:

- infra/AA-CIS-Infra/.github/workflows/migration-copy-guard.yml, contract-copy-guard.yml, connection-budget.yml, db-schema-dump.yml, db-isolation-probe.yml, crm-key-policy-diff.yml, db-tour-liveness-gate.yml, db-freshness-probe.yml (cron times in each file)

Notes: Results live only in GITHUB_STEP_SUMMARY today, so no trend and no digest.

<a id="data-02"></a>

### DATA-02 Weekly cross-app reconciliation

Vietnamese name: Đối soát liên ứng dụng hằng tuần.

| Field | Value |
|---|---|
| Audience | tech lead, engineer |
| Decision it supports | Are events flowing between apps without loss or lag; does the LLM ledger match the bill? |
| Cadence | weekly Monday 01:30 UTC |
| Channel | Section of OPS-13 weekly; /admin/reports |
| Automation | auto |
| Owner | tech lead |
| Status today | missing |
| Priority | P2 |
| Trigger | Weekly |
| Retention | Weekly JSON 1 year |
| Build effort | M (2.5 engineer-days): status views per owner (bk-NNN, tp-NNN, crm-NNN) granted to cis_app |
| Running cost | 0 USD |

Sections:

- Inquiry handoff: TripPlanner outbox vs Booking inbox (weekly roll-up of TP-03)
- Booking inbox backlog and age (booking.inbox_events)
- Tour lifecycle events read by bk_tour_lifecycle_pull (AA-986): lag
- Booking supply feed (booking.v_supply_outbox) consumption by CRM (crm.booking_feed_state)
- LLM gateway ledger vs Cost Explorer (K-LLM-RECON, FI-01)
- crm.ops.v1 feed freshness
- Vercel production commit vs main per project

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-REC-INBOX Inbox age p95 | p95 of now - received_at for booking.inbox_events with processed_at null; p95 of processed_at - received_at for processed rows | < 5 min (inquiry lag objective, C1.2) |
| K-REC-UNMATCHED Unmatched events | tripplanner.v_inquiry_outbox rows with no booking.inbox_events row of the same idempotency_key after 24 h | 0 |
| K-REC-FEEDLAG Feed lag | max booking.outbox.feed_seq - position stored in crm.booking_feed_state | 0 after 15 min |
| K-LLM-RECON Ledger vs bill | Defined in FI-01 | <= 10 % |

Data sources:

- tripplanner.v_inquiry_outbox, booking.inbox_events, booking.outbox, booking.v_supply_outbox, crm.booking_feed_state (confirm columns in db-schema-reference.md before building)
- bk_tour_lifecycle_pull job rows in booking.job
- crm.ops.v1
- Vercel MCP list_deployments

Notes: tripplanner.outbox and booking.outbox have no processed flag; reconcile by idempotency_key and feed_seq instead. Each app reads only its own tables; cross-app numbers go through contract views.

<a id="data-03"></a>

### DATA-03 Schema and contract change report

Vietnamese name: Báo cáo thay đổi schema và hợp đồng dữ liệu.

| Field | Value |
|---|---|
| Audience | engineer, tech lead, agents |
| Decision it supports | Which migrations and contract changes landed; did any break a consumer? |
| Cadence | event (each DB Migrate apply) + weekly summary Monday in DEV-03 |
| Channel | PR body of the schema-reference bot PR; weekly section of DEV-03 |
| Automation | auto |
| Owner | engineer |
| Status today | partial |
| Priority | P3 |
| Trigger | DB Migrate apply |
| Retention | Git history |
| Build effort | S (1 engineer-day) |
| Running cost | 0 USD |

Sections:

- Migrations applied per owner (CIS, tp-, bk-, crm-)
- bot/db-schema-reference PRs and drift status
- Contract changes in docs/contracts and API contract checks
- ERD drift

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-SCH-APPLIED Migrations applied | DB Migrate apply runs succeeded per owner | Informational |
| K-SCH-BREAKING Breaking contract changes | api-contract.yml / contracts.yml failures merged or overridden | 0 |
| K-SCH-REFLAG Reference lag | Hours from apply to merged db-schema-reference PR | < 24 h |

Data sources:

- infra/AA-CIS-Infra/.github/workflows/db-migrate.yml, db-schema-dump.yml
- docs/architecture/db-schema-reference.md header (latest migration per owner)
- .github/workflows/contracts.yml, apps/AA-CIS-App and apps/AA-Booking .github/workflows/api-contract.yml

Notes: The schema dump PR already auto-merges when clean (AA-993 M1).

<a id="data-04"></a>

### DATA-04 Ledger growth and retention compliance

Vietnamese name: Tăng trưởng sổ ghi và tuân thủ thời hạn lưu trữ.

| Field | Value |
|---|---|
| Audience | tech lead |
| Decision it supports | Are ledgers inside their retention windows and is growth sustainable? |
| Cadence | monthly business day 2 (item 4 of OPS-08) |
| Channel | Section of OPS-08 |
| Automation | auto |
| Owner | tech lead |
| Status today | partial |
| Priority | P2 |
| Trigger | Monthly |
| Retention | Permanent in git |
| Build effort | S (1 engineer-day) |
| Running cost | 0 USD |

Sections:

- Row counts and size of ledgers (shared.llm_call_log, shared.job, shared.decision_log, shared.tenant_api_usage_monthly, shared.cost_explorer_snapshot, booking.job, booking.inbox_events)
- Rows older than their window
- Retention job outcomes (CIS retention_* kinds, bk_retention_job, bk_retention_inbox_redact)
- Top 20 tables by size and 30-day growth

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-RET-OVERDUE Rows past window | Rows older than the C5.4 window per ledger | 0 |
| K-RET-RUNS Retention runs succeeded | Succeeded / scheduled retention runs | 100 % |
| K-RET-GROWTH Ledger growth | Rows per day, 30-day average, per ledger | Within C3 triggers |

Data sources:

- docs/architecture/data-standards/03-scaling.md C5.4
- docs/ops/job-kinds.md retention kinds
- docs/legal/retention-log.md
- docs/architecture/db-schema-reference.md row estimates (lag between structural changes)

Notes: Feeds SEC-09 retention KPI and OPS-16 growth model.

## Reliability, capacity and SLO

<a id="tp-02"></a>

### TP-02 Monthly TripPlanner performance and reliability

Vietnamese name: Hiệu năng web và độ ổn định Lambda TripPlanner hằng tháng.

| Field | Value |
|---|---|
| Audience | tech lead, engineer |
| Decision it supports | Do the map pages meet Core Web Vitals and are Browse/Assembly Lambdas healthy; what to optimise next? |
| Cadence | monthly business day 2 + Lighthouse on every frontend release |
| Channel | GitHub Actions summary JSON to S3; section of OPS-08; /admin/platform/apps card |
| Automation | semi |
| Owner | tech lead |
| Status today | partial |
| Priority | P2 |
| Trigger | Monthly; TripPlanner release tag |
| Retention | 12 months |
| Build effort | M (2.5 engineer-days): Lighthouse CI workflow + CloudWatch query reuse |
| Running cost | 0 USD with Lighthouse CI; Vercel Speed Insights / Web Analytics are not installed and are paid beyond the free quota: ask first |

Sections:

- Lighthouse mobile/desktop LCP, CLS, INP on key pages
- Lambda Browse and Assembly errors, throttles, p95 duration
- Embedding fallback chain usage
- Narration failures and cost
- Regressions vs last month

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-TP-LCP Mobile LCP | Lighthouse CI median LCP on home and planner pages (mobile) | <= 2.5 s |
| K-TP-LAMBDAERR Lambda error rate | CloudWatch AWS/Lambda Errors / Invocations per function | < 1 % |
| K-TP-LAMBDAP95 Lambda p95 duration | CloudWatch Duration p95 per function | Browse < 800 ms, Assembly < 8 s |
| K-TP-FALLBACK Keyword fallback share | shared.llm_call_log rows of stage tp_search_embed with fallback_used true / all tp_search_embed rows | < 5 % |

Data sources:

- CloudWatch AWS/Lambda
- shared.llm_call_log (tp_search_embed, tp_compose)
- Lighthouse CI in GitHub Actions (new, free)
- docs/audits/2026-10-29-S257-aa995-tp-perf/ (baseline)

Notes: TripPlanner has no /health endpoint; adding one is a prerequisite for availability numbers in OPS-08 and OPS-12. AA-995 left mobile LCP open.

<a id="ops-12"></a>

### OPS-12 Daily platform health digest

Vietnamese name: Bản tin sức khoẻ nền tảng mỗi sáng.

| Field | Value |
|---|---|
| Audience | tech lead, engineer on duty |
| Decision it supports | Is anything broken or drifting that needs work today? |
| Cadence | daily 01:00 UTC (08:00 ICT), every day; short when all green so a missing digest is itself a signal. Probe results are from the previous run window (02:17-05:13 UTC, about 20 h earlier) |
| Channel | SES e-mail to subscribers + Daily tile on /admin/reports |
| Automation | auto |
| Owner | tech lead |
| Status today | missing |
| Priority | P0 |
| Trigger | Daily |
| Retention | JSON 90 days |
| Build effort | S-M (2 engineer-days) on R1 core |
| Running cost | ~0 USD (SES ~30 e-mails per month; CloudWatch API within free tier) |

Sections:

- Apps: /health and /health/ready per app with a probe, deployed SHA per service (api and worker on the same SHA); TripPlanner listed as 'no probe' until it has /health
- Alarms in ALARM now and fired in 24 h
- Jobs: failed and overdue per job table (OPS-14)
- LLM route health: calls, fallback rate, errors in 24 h; acc3 status
- Last nightly probes (DATA-01) with their run time
- Spend yesterday vs 14-day median (EX-04)
- Open waves, inquiry handoff gap (TP-03), overdue reports (EX-06)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-OPS-APPSGREEN Apps green | Apps with a health endpoint answering /health and /health/ready 200 at 00:55 UTC / apps with a health endpoint (GET /admin/platform/apps) | All |
| K-OPS-ALARMS Alarms fired 24 h | CloudWatch DescribeAlarmHistory state changes to ALARM in 24 h | 0; each explained |
| K-JOB-FAIL Failed jobs 24 h | Defined in EX-04 | 0 |
| K-LLM-FALLBACK-24H Fallback rate 24 h | fallback_calls / calls in shared.llm_call_daily for yesterday | < 5 % |
| K-DATA-PROBES Nightly probes passed | Defined in DATA-01 | All |

Data sources:

- GET /admin/platform/apps (apps/AA-CIS-App/api/routers/admin_platform_ops.py)
- CloudWatch alarms (catalog docs/generated/alarms.md)
- shared.job, booking.job, tripplanner.job, crm.ops.v1
- shared.llm_call_daily
- DATA-01 results, TP-03, EX-06

Notes: A digest, not an alarm: SEV-worthy signals still page through SNS alerts in real time. Today only per-event e-mails and bells exist (ops_alert_email, shared.notifications).

<a id="ops-13"></a>

### OPS-13 Weekly SLO and DB performance check

Vietnamese name: Kiểm tra SLO và hiệu năng DB hằng tuần.

| Field | Value |
|---|---|
| Audience | tech lead, engineer |
| Decision it supports | Did any DB SLI miss its objective two weeks running; which query or index to fix? |
| Cadence | weekly Monday: probe 00:43 UTC, report 01:30 UTC; also after each wave |
| Channel | S3 + /admin/reports; Markdown only when a miss needs analysis, in docs/audits/<date>-S<nnn>-c43-w<nn>/; headline in EX-01 |
| Automation | semi |
| Owner | tech lead |
| Status today | partial |
| Priority | P1 |
| Trigger | Weekly; wave close |
| Retention | Raw probe 1 year; summaries permanent |
| Build effort | M (2.5 engineer-days): scheduled Infra workflow running the existing probe in an ECS task (like db-freshness-probe.yml) writing JSON; generator compares with last week |
| Running cost | ~0 USD (one Fargate task-minute per week; PI API within free tier) |

Sections:

- SLI table: objective vs measured per app
- Top 20 statements per role by total and by mean (pg_stat_statements)
- Slow log > 500 ms, lock waits
- Connection saturation vs max_connections (181) and role limits
- Two-week misses escalated with the offending query and proposed fix
- Job runner health summary (OPS-14)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-SLI-MET SLIs met | C1.2 objectives met / objectives measured (docs/architecture/data-standards/03-scaling.md) | All |
| K-SLI-2WEEK Two-week misses | Objectives missed in two consecutive weekly checks | 0; else raised to the tech lead (C1.2a) |
| K-DB-SLOWSTMT Slow statements | Statements with calls >= 20 and mean > 200 ms | Trend down |
| K-DB-CONN Connection saturation | DatabaseConnections p95 / max_connections; per role vs its connection limit (db-schema-reference.md Roles table: cis_app 90, tripplanner 30, booking 15, crm_app 6) | < 60 %; each role < 80 % of its limit; 0 too many connections |

Data sources:

- pg_stat_statements probe via DB Migrate run-script (raw example docs/audits/2026-10-29-S257-c43-w44/)
- Performance Insights top SQL (enabled, 7-day free retention: infra/AA-CIS-Infra/modules/rds/main.tf lines 164-165)
- CloudWatch RDS
- skill/aa-session/SKILL.md step 6; docs/backlog/README.md

Notes: Data standards check C4.3 (internal code, not part of the name). Today a paragraph in the session log with due dates worked out by hand.

<a id="ops-08"></a>

### OPS-08 Monthly capacity, SLO and availability review

Vietnamese name: Rà soát năng lực, SLO và độ sẵn sàng hằng tháng.

| Field | Value |
|---|---|
| Audience | tech lead (approves), CTO/CIO guides |
| Decision it supports | Is capacity enough for next month; resize, tune or accept; which C3 triggers fired? |
| Cadence | monthly business day 2 with FI-01; approved by business day 5 |
| Channel | docs/audits/<date>-S<nnn>-capacity-review/README.md via root PR (FI-01 cost.md in the same folder) |
| Automation | semi |
| Owner | tech lead |
| Status today | partial |
| Priority | P1 |
| Trigger | Monthly; a wave that doubles a ledger |
| Retention | Permanent in git |
| Build effort | S (2 engineer-days): scheduled data pull of the probe and CloudWatch scripts; narrative stays manual |
| Running cost | ~0 USD (CloudWatch GetMetricData + PI API) |

Sections:

- The nine C8b items (CloudWatch RDS 30 days, pg_stat_statements per role with C1.2 SLIs, table/index growth, ledgers vs retention (DATA-04), Lambda concurrency (TP-02), job backlog per owner (OPS-14), connection budget C2.2, C3 triggers, RDS cost line (FI-01))
- Availability per app from health probes
- Monitoring gaps vs C4.1
- Decisions

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-CAP-CPU CPU hours above baseline | Hours with hourly average CPU > 20 % (T baseline) in 30 days | Trigger per C3 |
| K-CAP-STORAGE Storage growth | GB/day over 30 and 7 days | Trigger > 1 GB/day for a week |
| K-CAP-CONN Connection peak | DatabaseConnections max and p95 vs max_connections | p95 < 60 % |
| K-AVAIL Availability per app | Successful health probes / probes in the month (Booking 5-minute uptime schedule, ops probe for others; TripPlanner after it gets /health) | Dev informational; prod SLO set in OPS-17 / PROD-01 |
| K-CAP-TRIGGERS C3 triggers fired | Count of C3 triggers fired with decision recorded | Each has a decision |

Data sources:

- docs/templates/capacity-review.md (template), docs/architecture/data-standards/03-scaling.md C8b
- CloudWatch RDS, Performance Insights, scripts in docs/audits/2026-10-28-S255-aa838-capacity/
- infra/AA-CIS-Infra/accounts/aa365/dfs_balance.tf (Booking uptime rate(5 minutes))
- infra/AA-CIS-Infra/db/check_connection_budget.py

Notes: Data standards review C8; doc catalog OPS-08 (docs/README.md). First review done 2026-10 (docs/audits/2026-10-28-S255-aa838-capacity/). Forward-looking forecast is OPS-16.

<a id="ops-16"></a>

### OPS-16 Capacity and growth forecast

Vietnamese name: Dự báo năng lực và tăng trưởng (6-12 tháng).

| Field | Value |
|---|---|
| Audience | tech lead, business owner (budget) |
| Decision it supports | When will storage, connections, CPU, LLM spend or free-plan limits run out under the planned waves and go-live, and what to provision or change ahead of time? |
| Cadence | quarterly with EX-05; again when a go-live date is set |
| Channel | docs/audits/<date>-S<nnn>-capacity-forecast/README.md via root PR; summary in EX-05 |
| Automation | semi |
| Owner | tech lead |
| Status today | missing |
| Priority | P2 |
| Trigger | Quarter start; go-live date set; a C3 trigger fired |
| Retention | Permanent in git |
| Build effort | S (1.5 engineer-days): projection script over stored monthly snapshots + template section |
| Running cost | 0 USD |

Sections:

- Growth model: rows/day per ledger (DATA-04), DB size trend (1.5 GB at the 2026-10-29 dump), job volume
- Planned load: master plan slots, wave schedule, go-live scenario (traffic assumptions stated)
- Runway per limit: RDS storage, max_connections 181 and role limits, CPU baseline, Lambda concurrency, Vercel and GitHub free plans, Linear 250 issues
- Cost projection per app for 3/6/12 months (feeds FI-06 and EX-05)
- Actions with lead time

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-FC-RUNWAY Shortest runway | Months until the first limit is reached at projected growth | >= 6 months; < 3 months = act now |
| K-FC-ACCURACY Forecast accuracy | \|last quarter's forecast for this quarter - actual\| / actual for DB size and monthly cost | <= 20 % |
| K-FC-COST12 12-month cost projection | Projected monthly cost per account at month 12 vs budget | <= budget or a decision recorded |

Data sources:

- OPS-08 and DATA-04 monthly runs, shared.kpi_daily
- docs/architecture/db-schema-reference.md header (database size, max_connections, row estimates)
- docs/backlog/tracker/plan.json, CIS-07 wave costs
- docs/architecture/data-standards/03-scaling.md C3 triggers

Notes: Uses stored data only. Projections state their assumptions and are compared with actuals next quarter.

<a id="ops-03"></a>

### OPS-03 Backup, restore and rollback drill record

Vietnamese name: Biên bản diễn tập sao lưu, khôi phục và rollback.

| Field | Value |
|---|---|
| Audience | tech lead, CTO |
| Decision it supports | Can we restore and roll back within target; which runbook step failed? |
| Cadence | when a procedure changes and once before prod (Dev); quarterly from prod (DM-9.3) |
| Channel | docs/audits/<date>-S<nnn>-<drill>/ via root PR; index docs/ops/drills/README.md |
| Automation | manual |
| Owner | tech lead |
| Status today | partial |
| Priority | P2 |
| Trigger | Procedure change; pre-prod readiness (OPS-17) |
| Retention | Permanent |
| Build effort | XS (template section only) |
| Running cost | Small RDS restore cost during the drill (temporary instance, < 1 USD) |

Sections:

- Drill scope (PITR, single schema, app rollback, Terraform rollback)
- Measured RTO and RPO
- Steps that failed or were unclear
- Runbook changes made

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-DR-RTO RTO measured | Start of restore to verified service | < 1 h on Dev (03-scaling.md C1.2) |
| K-DR-RPO RPO | Data window lost (PITR) | <= 5 min |
| K-DR-STALE Runbooks past drill cadence | Runbooks whose last_tested is older than the DM-9.3 cadence | 0 before prod |

Data sources:

- docs/ops/drills/README.md, docs/ops/runbooks/restore-rds-pitr.md, restore-schema.md, rollback-*.md
- docs/STYLE.md Runbooks and tested section

Notes: Drill evidence stays in docs/audits (C7.2b).

## Incidents

<a id="ops-04"></a>

### OPS-04 Incident and postmortem report (incl. cost incidents)

Vietnamese name: Báo cáo sự cố và postmortem (gồm sự cố chi phí).

| Field | Value |
|---|---|
| Audience | tech lead, engineer, business owner (SEV1-2 summary) |
| Decision it supports | What broke or overspent, is it stopped, which guard prevents a repeat? |
| Cadence | event: write within 5 working days of a SEV1-2 (2 days for the Linear note); monthly roll-up in EX-02 and DEV-01 |
| Channel | docs/ops/postmortems/<YYYY-MM-DD>-<slug>.md (folder does not exist yet; create it); SEV3 as a session-log line; summary line in EX-01 |
| Automation | manual |
| Owner | tech lead |
| Status today | partial |
| Priority | P0 |
| Trigger | Any SEV1-2; cost anomaly >= 5 USD (acc2) / >= 15 USD (acc3); budget 100 % actual; spend_budget hard stop |
| Retention | Permanent in git |
| Build effort | XS (0.5 engineer-day): create the folder, extend the template with the cost section, index page |
| Running cost | 0 USD |

Sections:

- Summary and SEV
- Impact (who, how long, data, cost USD)
- Timeline (UTC+7) with detection source
- Root cause (5 whys) and contributing factors
- Cost attribution for cost incidents (account, App tag, service, LLM stage/job_id)
- What went well / badly
- Actions with owner and due date
- Lessons written to skill/aa-lessons/lessons.md

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-INC-COUNT Incidents by SEV | Incidents opened per SEV in the period | 0 SEV1 |
| K-INC-TTD Time to detect | Start of impact to first alert or human report | < 15 min SEV1 |
| K-INC-TTR Time to restore | Detection to service restored (median feeds DEV-01 MTTR) | < 1 working day |
| K-INC-ACTIONS Actions on time | Postmortem actions closed by due date / due | >= 90 % |
| K-INC-COSTATTR Cost incident attribution time | Alert to written cause | <= 1 working day; >= 50 USD or > 20 % of a budget = SEV2 |

Data sources:

- docs/ops/incident-response.md (severity, communication)
- docs/templates/postmortem.md
- Cost Anomaly Detection and AWS Budgets alerts (infra/AA-CIS-Infra/accounts/aa365/cost_anomaly.tf, accounts/acc3-bedrock/cost_anomaly_immediate.tf)
- shared.llm_call_log, shared.dfs_call_log, shared.job by job_id; docs/ops/playbooks/llm-cost-spike.md

Notes: Absorbs draft FI-10. The S257 acc3 access incident has no postmortem record yet: write it as the first entry.

## Security, privacy and legal

<a id="crm-06"></a>

### CRM-06 Agency access and data-rights report

Vietnamese name: Truy cập và quyền dữ liệu của đại lý.

| Field | Value |
|---|---|
| Audience | agency owner (controller); AA staff counts only |
| Decision it supports | Who accessed traveller data, which exports and erasures ran, is the agency meeting its controller duties? |
| Cadence | monthly (section of CRM-05) + on demand |
| Channel | CRM settings access-log and data pages |
| Automation | auto |
| Owner | agency owner |
| Status today | partial |
| Priority | P3 |
| Trigger | Monthly |
| Retention | Audit events per CRM retention policy (12 months shown today) |
| Build effort | S (1 engineer-day) |
| Running cost | 0 USD |

Sections:

- Access events by member and action (crm.audit_event)
- Audit exports (crm.audit_export_manifest)
- Traveller portal access (crm.traveler_access)
- Erasure requests and status (crm.erasure_request)
- Consent records (crm.consent)
- Lifecycle/retention runs (crm.lifecycle_run)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| Erasure requests closed | crm.erasure_request with executed_at not null / requested in the period | 100 % within the deadline in docs/legal/dsar-erasure-runbook.md |
| Audit exports | crm.audit_export_manifest rows in the period | Informational |
| Stale traveller access | crm.traveler_access rows not deleted with purge_after passed | 0 |

Data sources:

- crm.audit_event, crm.audit_export_manifest, crm.traveler_access, crm.erasure_request, crm.consent, crm.lifecycle_run
- apps/AA-Partner/web/app/(crm)/settings/access-log/page.tsx (12 months + download), apps/AA-Partner/web/app/(crm)/settings/data/page.tsx

Notes: Agencies own controller duties (memory crm-byo-shared-responsibility).

<a id="sec-03"></a>

### SEC-03 Monthly security hygiene report

Vietnamese name: Báo cáo vệ sinh bảo mật hằng tháng (lỗ hổng, secret, probe cách ly).

| Field | Value |
|---|---|
| Audience | tech lead, CIO guide |
| Decision it supports | Which vulnerabilities, secret drifts or isolation failures must be fixed this month; which ignores expire? |
| Cadence | monthly business day 2 |
| Channel | docs/audits/<date>-S<nnn>-security-review/README.md via root PR + generated docs/generated/security-alerts.md (planned); counts into EX-02 |
| Automation | semi |
| Owner | tech lead |
| Status today | partial |
| Priority | P1 |
| Trigger | Monthly; any critical alert opens an incident check |
| Retention | Permanent in git |
| Build effort | S-M (2 engineer-days): root workflow collecting alerts JSON + template |
| Running cost | 0 USD while the root repo is public; after it goes private (November 2026) the collection run uses a few free private-repo Actions minutes |

Sections:

- Dependabot alerts per repo by severity and age
- pip-audit / npm ignores and their expiry
- Trivy image findings (report only)
- Secret scanning results (secret-scan, secret-scan-history workflows)
- Secrets register drift (Secrets Manager, Lambda env, GitHub, Vercel names)
- Nightly tenant-isolation probe and CRM key policy diff results
- Actions

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-SEC-VULNSLA Alerts past SLA | Open critical/high alerts older than the SLA in docs/security/vulnerability-management.md | 0 |
| K-SEC-SECRETFIND Secret findings | New secret-scan findings in the month | 0 unresolved |
| K-SEC-DRIFT Register drift | Secrets present in a system but not in docs/security/secrets-register.yaml, or the reverse | 0 |
| K-SEC-ISOLATION Isolation probe failures | Failed runs of db-isolation-probe.yml in the month | 0 |

Data sources:

- gh api Dependabot alerts per repo; docs/security/vulnerability-management.md
- secret-scan.yml / secret-scan-history.yml in every app repo
- docs/security/secrets-register.md + .yaml and its check script
- infra/AA-CIS-Infra/.github/workflows/db-isolation-probe.yml, crm-key-policy-diff.yml

Notes: Doc catalog SEC-03 (vulnerability management). Merges the monthly secrets drift check (docs/guides/cio.md). No unfixed exploit detail in git while the root repo is public.

<a id="sec-05"></a>

### SEC-05 Quarterly access review

Vietnamese name: Rà soát quyền truy cập hằng quý.

| Field | Value |
|---|---|
| Audience | tech lead, CIO/CTO guides |
| Decision it supports | Who can reach each app and system, and which access to remove? |
| Cadence | quarterly: first session of each quarter, scheduled with the business day 2 pack |
| Channel | docs/audits/<date>-S<nnn>-access-review/README.md via root PR; index docs/security/README.md |
| Automation | semi |
| Owner | tech lead |
| Status today | exists |
| Priority | P1 |
| Trigger | Quarter start; after break-glass use; before prod |
| Retention | Permanent |
| Build effort | S (2 engineer-days): read-only script bundle to rerun the collection |
| Running cost | 0 USD |

Sections:

- GitHub org members, apps, deploy keys
- Vercel members and tokens
- AWS IAM users, roles, static keys (acc2, acc3)
- Cognito WORKFORCE users and groups vs staff directory (DirectoryHealth)
- DB roles and grants (db-schema-reference roles section)
- Secrets access
- Findings and removals

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-ACC-UNJUSTIFIED Unjustified access | Principals without a documented need | 0 at sign-off |
| K-ACC-STALE Stale identities | Users with no sign-in in 90 days | 0 or justified |
| K-ACC-KEYS Active static IAM keys | Active IAM user access keys in ecosystem accounts | 0 (except documented bootstrap) |
| K-ACC-CARRYOVER Findings carried over | Open findings from the previous review | 0 |

Data sources:

- docs/templates/access-review.md; docs/audits/2026-10-20-S245-access-review/README.md
- gh api, Vercel listings, aws iam read-only, Cognito list-users
- GET /admin/platform/staff-directory/health (apps/AA-CIS-App/api/routers/admin_platform.py)
- docs/architecture/db-schema-reference.md roles section

Notes: Data standards rule DM-8.10; doc catalog SEC-05. Live IAM user/key part was pending (F-15 in the S245 review). Next due: first session of 2027-Q1.

<a id="sec-08"></a>

### SEC-08 Privileged action and audit-log review

Vietnamese name: Rà soát thao tác đặc quyền và nhật ký kiểm toán.

| Field | Value |
|---|---|
| Audience | tech lead |
| Decision it supports | Were privileged actions expected and recorded; is the audit chain intact? |
| Cadence | monthly business day 2 (section of SEC-03) |
| Channel | Section of SEC-03 |
| Automation | semi |
| Owner | tech lead |
| Status today | partial |
| Priority | P2 |
| Trigger | Monthly; any break-glass use |
| Retention | Permanent (summary); source logs per their retention |
| Build effort | S (1.5 engineer-days) |
| Running cost | 0 USD |

Sections:

- CIS audit hash-chain verification
- Break-glass uses and deploy-gate overrides with reasons
- Role changes (Booking staff role sync, CIS staff role drift)
- Admin actions by type (CIS acp_shared.audit_log, booking.audit_logs, CRM counts)
- Unusual patterns (off-hours bulk actions)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-AUD-CHAIN Hash-chain verify | GET /admin/platform/audit/verify result for the month (acp_shared.audit_log chain_seq, prev_hash, row_hash) | Pass |
| K-AUD-BREAKGLASS Break-glass uses | Uses in the month, each with a record per docs/ops/runbooks/break-glass.md | 100 % recorded |
| K-AUD-OVERRIDES Deploy-gate overrides | Deploy runs with input override_running_jobs set (apps/AA-CIS-App/.github/workflows/deploy-dev.yml) with a reason (docs/ops/runbooks/deploy-gate-override.md) | 100 % with reason |

Data sources:

- acp_shared.audit_log, booking.audit_logs, crm.audit_event (counts via crm.ops.v1)
- /admin/platform/audit, Booking audit-log page
- CloudTrail event history (90 days, free)

Notes: CIS and Booking audit logs are separate today.

<a id="sec-09"></a>

### SEC-09 Privacy and data-rights report

Vietnamese name: Báo cáo quyền riêng tư và yêu cầu của chủ thể dữ liệu.

| Field | Value |
|---|---|
| Audience | tech lead, business owner (legal calls) |
| Decision it supports | Are data-subject requests, erasures, retention and consent handled on time? |
| Cadence | quarterly with EX-05; monthly counts in SEC-03 |
| Channel | docs/audits/<date>-S<nnn>-privacy-review/ via root PR (counts only, no subject data) |
| Automation | semi |
| Owner | tech lead; business owner for legal decisions |
| Status today | partial |
| Priority | P2 |
| Trigger | Quarterly; any DSAR |
| Retention | Permanent (counts); request records per the legal register |
| Build effort | S (1.5 engineer-days) |
| Running cost | 0 USD |

Sections:

- DSARs received and closed (docs/legal/register.md)
- Erasure runs: DRY RUN vs apply (CIS data_erasure job, crm.erasure_request)
- Retention runs on schedule (docs/legal/retention-log.md, retention_* kinds, bk_retention_job)
- Consent capture check (DM-6.5)
- Open privacy items handed to SEC-10

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-PRIV-DSAR DSARs on time | Requests closed within the deadline in docs/legal/dsar-erasure-runbook.md / received | 100 % |
| K-PRIV-RETENTION Retention runs on schedule | Scheduled retention runs succeeded / scheduled | 100 % |
| K-PRIV-CONSENT Consent coverage | Result of docs/legal/consent-capture-query.md (booking.customers.contact_consent, crm.consent) | 100 % of records with consent where required |

Data sources:

- docs/legal/register.md, docs/legal/retention-log.md, docs/legal/consent-capture-query.md, docs/legal/dsar-erasure-runbook.md
- /admin/data-erasure (job data_erasure), crm.erasure_request, crm.consent
- shared.job / booking.job retention kinds

Notes: Doc catalog OPS-09 is the DSAR procedure; this report measures it. Business/legal items are calm proposals for the business owner (memory tech-focus-business-to-thu).

<a id="sec-10"></a>

### SEC-10 Legal, policy and AI-terms readiness tracker

Vietnamese name: Theo dõi sẵn sàng pháp lý, chính sách và điều khoản AI.

| Field | Value |
|---|---|
| Audience | business owner (decisions, lawyer is their call), tech lead |
| Decision it supports | Which privacy, terms, DPA, sub-processor and AI-clause items are still open before go-live, and which need a business or legal answer this month? |
| Cadence | monthly count (section of SEC-03) + quarterly full review with EX-05; weekly inside OPS-17 once a go-live date is set |
| Channel | docs/audits/<date>-S<nnn>-legal-readiness/README.md via root PR (company doc in English + .vi.md for the business owner); open items as a clickable decision page |
| Automation | semi |
| Owner | tech lead (tracks); business owner (decides with a lawyer) |
| Status today | partial |
| Priority | P1 |
| Trigger | Monthly; go-live date set; any new vendor or AI provider |
| Retention | Permanent |
| Build effort | S (1 engineer-day): marker count script + template |
| Running cost | 0 USD (no new contract or paid service; memory advise-dont-push-contracts) |

Sections:

- The twelve readiness topics from docs/legal/readiness-packet.md: status, proposed answer, owner role
- Draft pages still marked 'Draft - pending legal review' (TripPlanner and Partner privacy/terms)
- Vendor DPAs and AI zero-retention status (docs/legal/register.md vendor table)
- Tenant AI clause status (docs/legal/tenant-terms-ai-clause-draft.md)
- '[to be confirmed]' markers remaining in public pages
- Changes since last review

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-LEGAL-OPEN Open readiness topics | Topics in docs/legal/readiness-packet.md without an accepted answer | 0 before go-live |
| K-LEGAL-TBC Open markers | Count of '[to be confirmed]' in published legal pages and docs/legal/register.md | 0 before go-live |
| K-VEND-DPA DPA coverage | Defined in FI-04 | 100 % before prod go-live |

Data sources:

- docs/legal/readiness-packet.md (+ .vi.md), docs/legal/register.md (line 245: no DPA signed), docs/legal/tenant-terms-ai-clause-draft.md, docs/legal/dpa-template.md
- Published privacy/terms pages of TripPlanner and the Partner portal

Notes: Advice only: best technical option, no pressure, lawyer is the business owner's call (memory tech-focus-business-to-thu). Links for the business owner travel via the session-end Jira drafts (memory thu-links-via-jira).

## Delivery and release

<a id="dev-01"></a>

### DEV-01 Monthly delivery and DORA report

Vietnamese name: Báo cáo phân phối phần mềm và DORA hằng tháng.

| Field | Value |
|---|---|
| Audience | tech lead, CTO guide |
| Decision it supports | Is delivery fast and safe enough; where to invest in CI, tests or review? |
| Cadence | monthly business day 2 |
| Channel | S3 + /admin/reports; Markdown in docs/audits/<date>-S<nnn>-delivery/; headline in EX-02 |
| Automation | auto |
| Owner | tech lead |
| Status today | missing |
| Priority | P1 |
| Trigger | Monthly |
| Retention | Permanent |
| Build effort | M (3 engineer-days): root scheduled workflow collecting GitHub data to JSON + generator |
| Running cost | 0 USD while repos are public; ~30 private-repo Actions minutes per month after the root repo goes private in November 2026 (inside the free allowance) |

Sections:

- DORA per app: deployment frequency, lead time for changes, change failure rate, time to restore
- CI health: duration, failure rate on main, re-runs, flaky tests, Actions minutes
- Release versions shipped (DEV-02)
- Post-deploy verify failures and rollbacks
- Improvement actions

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-DORA-DF Deployment frequency | Successful deploy runs per app per week (deploy-dev.yml for CIS, Booking, Partner; deploy-web-dev.yml / deploy-portal-dev.yml for Partner; deploy-lambdas.yml for TripPlanner; vercel-deploy.yml) | >= daily on active apps (elite band, context only) |
| K-DORA-LT Lead time for changes | Median time from PR first commit to the successful deploy that contains the merge SHA | < 1 day |
| K-DORA-CFR Change failure rate | Deploys followed within 24 h by a rollback, a fix PR on the same area, a failed post-deploy-verify or an incident / deploys | < 15 % |
| K-DORA-MTTR Time to restore | Median OPS-04 time to restore | < 1 day |
| K-CI-MAINFAIL CI failure rate on main | Failed ci.yml runs on main / runs | < 5 % |

Data sources:

- gh run list / GitHub API for deploy workflows, post-deploy-verify.yml, ci.yml, release-please.yml in each app repo
- GitHub PR API (created, merged_at, commits)
- docs/ops/runbooks/rollback-*.md uses, OPS-04 records
- docs/linear-export/

Notes: Bands from the DORA research are context, not targets for a one-person dev team; trend matters.

<a id="dev-02"></a>

### DEV-02 Release notes per app

Vietnamese name: Ghi chú phát hành theo app.

| Field | Value |
|---|---|
| Audience | business owner (Vietnamese summary), staff, engineers |
| Decision it supports | What changed for users in this release; is any action needed from staff or tenants? |
| Cadence | event: each release-please release |
| Channel | CHANGELOG.md (auto) + Jira epic comment for user-visible releases (batched at session end) |
| Automation | semi |
| Owner | tech lead |
| Status today | partial |
| Priority | P2 |
| Trigger | Release tag |
| Retention | Permanent |
| Build effort | XS |
| Running cost | 0 USD |

Sections:

- Version and date
- User-visible changes in business words
- Fixes
- Breaking or behaviour changes and required actions
- Links to CHANGELOG and evidence

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-REL-NOTES Releases with notes | release-please releases with a user-facing note / releases | 100 % |

Data sources:

- apps/*/release-please-config.json, CHANGELOG.md per app
- docs/templates/release-note.md
- Jira per-app epics PR-22..PR-27

Notes: Doc catalog APP-07. Jira wording rules: skill/aa-jira-update; no issue IDs in user text (memory no-issue-ids-in-ui).

<a id="dev-03"></a>

### DEV-03 Weekly engineering flow

Vietnamese name: Dòng chảy công việc kỹ thuật hằng tuần.

| Field | Value |
|---|---|
| Audience | tech lead |
| Decision it supports | Is work converging (In Progress closing, PRs merging) and are master-plan slots on track? |
| Cadence | weekly Monday 01:30 UTC |
| Channel | /admin/reports + section of EX-01 (counts only, no Linear IDs in Jira) |
| Automation | auto |
| Owner | tech lead |
| Status today | partial |
| Priority | P1 |
| Trigger | Weekly |
| Retention | 1 year |
| Build effort | S (1.5 engineer-days): root workflow + Linear API key as a GitHub secret |
| Running cost | 0 USD (private-repo Actions minutes after November 2026 stay inside the free allowance) |

Sections:

- Issues Done with live verify (K-DEL-SHIPPED)
- In Progress older than 7 days
- Open PRs per repo and age
- Master plan slot progress (docs/backlog/tracker/plan.json)
- Schema and contract changes (DATA-03)
- Linear quota (Free plan, 250 unarchived)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-DEL-SHIPPED Issues shipped | Defined in EX-01 | Trend |
| K-FLOW-WIPAGE In Progress > 7 days | Linear issues In Progress for more than 7 days | 0 (memory in-progress-must-converge) |
| K-FLOW-PRAGE PRs open > 3 days | Open PRs older than 3 days across the six repos | 0 without a note |
| K-FLOW-QUOTA Linear quota | Unarchived issues / 250 | < 80 % |

Data sources:

- Linear API (tools/linear/linear_export.py), docs/linear-export/
- gh pr list per repo
- docs/backlog/tracker/plan.json

Notes: Linear key must be stored as a repo secret; never in the repo.

## Readiness and sign-off

<a id="ops-17"></a>

### OPS-17 Go-live readiness scorecard

Vietnamese name: Bảng điểm sẵn sàng go-live theo app.

| Field | Value |
|---|---|
| Audience | business owner (go/no-go), tech lead |
| Decision it supports | Is each app ready to go to production, and what blocks the go-live date? |
| Cadence | event: when a go-live date is set, then weekly until go-live |
| Channel | docs/audits/<date>-S<nnn>-go-live-readiness/README.md via root PR + a clickable decision page for the business owner |
| Automation | semi |
| Owner | tech lead (prepares); business owner (decides) |
| Status today | missing |
| Priority | P1 |
| Trigger | Go-live date set (docs/guides/ceo.md: prod work starts when a date is set) |
| Retention | Permanent |
| Build effort | S (1.5 engineer-days): checklist YAML + generator reading other report runs |
| Running cost | 0 USD |

Sections:

- Checklist per app from the prod blueprint (PROD-01: ADR 0012 + prod section of docs/ops/README.md)
- Status per item: done / in progress / blocked, with evidence link
- Linked gates: SLO set (OPS-08), drills done (OPS-03), access review (SEC-05), legal readiness (SEC-10), UAT signed (DEV-04), security alerts past SLA (SEC-03), budget approved (FI-06)
- Blockers and owners
- Go/no-go recommendation

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-GO-READY Readiness per app | Checklist items done with evidence / items, per app | 100 % of must items before go-live |
| K-GO-BLOCKERS Open blockers | Must items blocked or without an owner | 0 at the go/no-go meeting |

Data sources:

- docs/adr/0012-*.md, docs/ops/README.md prod section (PROD-01 in docs/README.md line 78), AA-880
- OPS-03, OPS-08, SEC-03, SEC-05, SEC-10, DEV-04, FI-06 runs

Notes: No go-live date yet; build the checklist file now so readiness is visible early.

<a id="dev-04"></a>

### DEV-04 UAT sign-off record

Vietnamese name: Biên bản nghiệm thu UAT theo app.

| Field | Value |
|---|---|
| Audience | business owner (accepts), tech lead, staff testers |
| Decision it supports | Does each app do what the business needs, recorded on video, and is it accepted for go-live? |
| Cadence | event: once after all technical work or when the business owner says (AA-855, > S262); repeat for major releases before prod |
| Channel | docs/audits/<date>-S<nnn>-uat/README.md via root PR (links, no personal data) + a clickable sign-off page for the business owner; summary in the Jira epic per app |
| Automation | manual |
| Owner | tech lead (prepares); business owner (signs off) |
| Status today | planned |
| Priority | P2 |
| Trigger | AA-855 start; go-live readiness (OPS-17) |
| Retention | Permanent |
| Build effort | S (1 engineer-day) for the template and scenario list; recording time separate |
| Running cost | 0 USD |

Sections:

- Scope: apps and roles tested (CIS admin + portal, TripPlanner, Booking, CRM)
- Scenario list per app with expected result
- Result per scenario: pass / fail / pass with note, video link, screenshot
- Defects found with severity and fix status
- Sign-off: accepted / accepted with conditions / rejected, by role and date

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-UAT-PASS Scenario pass rate | Scenarios passed / scenarios run, per app | 100 % of must scenarios |
| K-UAT-DEFECTS Open blocking defects | Severity 1-2 defects found in UAT not yet fixed and verified | 0 at sign-off |
| K-UAT-COVER Video coverage | Scenarios with a recorded video / scenarios | 100 % (memory uat-videos-after-tech) |

Data sources:

- AA-855 scope (docs/backlog/README.md lines 53, 202)
- Role guides (docs/guides/) for scenario lists
- Recorded videos (Google Drive folder per memory gdrive-adventureasia-folder)

Notes: Agent records the videos itself with E2E logins (memory screenshots-self-serve). Becomes P1 when a go-live date is set.

## Customer

<a id="cx-01"></a>

### CX-01 Traveller satisfaction and reviews

Vietnamese name: Mức hài lòng của khách và đánh giá sau chuyến đi.

| Field | Value |
|---|---|
| Audience | business owner, sales lead, contracting staff; agency owner for CRM agencies (own data only) |
| Decision it supports | Are travellers happy, which suppliers, guides or itineraries cause complaints, and which reviews can be used in marketing (with consent)? |
| Cadence | monthly business day 2 + complaint alert on each detractor answer |
| Channel | Booking Reports tab (AA trips); CRM Reports page (agency trips, agency only); aggregate scores to CIS via a bk-NNN contract view for EX-02 |
| Automation | auto |
| Owner | sales lead (AA); agency owner (CRM) |
| Status today | missing |
| Priority | P2 |
| Trigger | First real completed trip |
| Retention | Answers 36 months; published reviews while consent stands |
| Build effort | M (4 engineer-days): table + post-trip e-mail job + form + report |
| Running cost | ~0 USD (SES; no paid survey tool) |

Sections:

- Survey response rate after trip end
- CSAT and NPS by destination, trip style, channel
- Supplier and guide mentions (scores per supplier)
- Complaints and follow-ups with owner and status
- Incidents during the trip (BK-06) next to the score
- Reviews with publish consent (count only in CIS; text stays in the owning app)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-CX-RESP Response rate | Surveys answered / surveys sent for trips that reached 'completed' in the period | >= 30 % |
| K-CX-CSAT CSAT | Share of answers scoring 4-5 on the 5-point overall question | >= 85 % |
| K-CX-NPS NPS | % promoters (9-10) - % detractors (0-6) on the recommend question | >= 40 (baseline after first prod quarter) |
| K-CX-COMPLAINT Complaint closure | Complaints closed within 5 working days / complaints raised | >= 90 % |

Data sources:

- Proposed booking-owned table booking.trip_feedback (bk-NNN; not in db-schema-reference.md today): trip_case_id, sent_at, answered_at, csat, nps, supplier scores, consent_to_publish
- CRM: a post-trip form stage on crm.form_definition / crm.form_submission (tables exist; stage support to confirm in AA-Partner)
- booking.trip_cases (status completed), booking.departure_incidents

Notes: Free-text answers are pii:free_text (DM-6.1 tag); never in CIS or git. Consent to publish follows docs/legal/consent-capture-query.md patterns.

## Growth and marketing

<a id="mkt-01"></a>

### MKT-01 Acquisition and marketing funnel

Vietnamese name: Nguồn khách và phễu marketing.

| Field | Value |
|---|---|
| Audience | business owner, sales lead |
| Decision it supports | Which channels bring travellers and partners that convert, and where to spend marketing effort? |
| Cadence | monthly business day 2 (section of EX-02) + weekly line in EX-01 |
| Channel | /admin/overview Acquisition card + EX-02 section |
| Automation | auto |
| Owner | business owner |
| Status today | missing |
| Priority | P2 |
| Trigger | Before prod launch marketing |
| Retention | Monthly aggregates 36 months; raw session source 400 days with the view |
| Build effort | M (3 engineer-days): tp migration + BFF capture + view metrics + card |
| Running cost | 0 USD (first-party capture; Vercel Web Analytics and paid tools only after a quote and explicit yes) |

Sections:

- Sessions and sign-ups by source (direct, search, social, partner, campaign)
- Source -> trip -> inquiry -> confirmed, per source
- Booking customers by booking.customers.source and trip case channel
- Partner leads (B2B, Content studio, CRM) by source
- Campaign list with results (when CRM campaigns exist, AA-968)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-MKT-SOURCE Sessions by source | TripPlanner sessions grouped by first-touch source (proposed tp-NNN columns referrer_host, utm_source, utm_medium, utm_campaign on tripplanner.sessions) | Trend |
| K-MKT-CONV Source conversion | Inquiries sent / sessions, per source; confirmed cases per source via booking.trip_cases.source_system + inquiry_snapshot | Business owner sets after first prod quarter |
| K-MKT-CUSTSRC New customers by source | booking.customers created in the period grouped by source | Trend |

Data sources:

- Proposed tp-NNN migration adding first-touch referrer/UTM columns to tripplanner.sessions (today: id, guest_token, customer_id, created_at, expires_at, guest_token_hash, account_id)
- tripplanner.v_ops_traffic_daily (add per-source metric rows; add, never rename)
- booking.customers.source, booking.trip_cases (source_system, channel)
- crm.trip.lead_source (agency-only, counts via crm.ops.v1)

Notes: Capture source only, no third-party trackers or cookies beyond the session (privacy notice in docs/legal/readiness-packet.md).

<a id="mkt-02"></a>

### MKT-02 SEO and content performance

Vietnamese name: Hiệu quả SEO và nội dung.

| Field | Value |
|---|---|
| Audience | business owner, content ops, tenant owner (own sites, later) |
| Decision it supports | Is published content reaching search demand; which tours or tenant posts to refresh; is DataForSEO spend paying off? |
| Cadence | monthly business day 2 |
| Channel | /admin/content-quality SEO tab; tenant view later in the portal |
| Automation | semi |
| Owner | content ops |
| Status today | missing |
| Priority | P3 |
| Trigger | Monthly; after the first public tenant site |
| Retention | Monthly aggregates 24 months |
| Build effort | S (1.5 engineer-days) for coverage and spend; M (+2 days) for Search Console |
| Running cost | 0 USD (Search Console API free; no new paid SEO tool) |

Sections:

- Keyword coverage: tours with seo_context and top keywords
- DataForSEO spend per tour and per tenant, cache hit rate
- Published pages per channel (acp_shared.publish_log external_url)
- Search impressions, clicks and average position per page (Google Search Console, once verified)
- Refresh list: pages with falling clicks or expired seo_context

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-SEO-COVER Keyword coverage | Live tours with a silver_aa_internal.seo_context row with expires_at in the future / live tours | >= 95 % |
| K-SEO-DFSCACHE DataForSEO cache hit | shared.dfs_call_log rows with cache_hit true / all rows in the period | >= 70 % |
| K-SEO-CTR Search CTR | Clicks / impressions per published page from Search Console | Trend; flag a page falling > 30 % month over month |

Data sources:

- silver_aa_internal.seo_context, shared.tenant_seo_config, shared.dfs_call_log
- acp_shared.publish_log (external_url, published_at)
- Google Search Console API (free; needs property verification per site: ask the business owner first, no cost)

Notes: DataForSEO cost totals stay in FI-01/FI-04; this report covers coverage and outcome.

## Tenant- and agency-facing

<a id="cis-04"></a>

### CIS-04 Tenant monthly usage statement

Vietnamese name: Bảng kê sử dụng hằng tháng gửi tenant Content studio.

| Field | Value |
|---|---|
| Audience | tenant owner/admin (Content studio) |
| Decision it supports | Tenant checks what it used and pays for, and whether to change plan. |
| Cadence | monthly business day 2, only for tenants with activity |
| Channel | Tenant portal account/billing page (PDF/CSV download) + e-mail to the tenant owner; object under the tenant prefix of the reports bucket |
| Automation | auto |
| Owner | AA admin |
| Status today | partial |
| Priority | P3 |
| Trigger | First paying tenant |
| Retention | 36 months per tenant |
| Build effort | S-M (2 engineer-days) |
| Running cost | ~0 USD |

Sections:

- Plan and quota
- Tours rewritten and API calls vs quota
- Pieces delivered and published per channel
- Overage (if any) and next reset date

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| Tours rewritten | shared.v_tenant_monthly_usage.tours_rewritten for billing_month vs tours_quota_monthly | Shown vs quota |
| API calls used | shared.v_tenant_monthly_usage.api_calls_used vs api_calls_quota_monthly | Shown vs quota |
| Pieces delivered / published | acp_shared.content_piece status 'approved' and acp_shared.publish_log status 'published' for the tenant | Informational |
| Overage (USD) | shared.v_tenant_monthly_usage.overage_usd | Shown only when > 0 |

Data sources:

- shared.v_tenant_monthly_usage, acp_shared.content_piece, acp_shared.publish_log
- Portal /v1/billing and /v1/quota (apps/AA-Partner/portal/app/portal/_components/DashboardTab.tsx)

Notes: Tenant-facing: plain KPI names, no K- IDs, no issue IDs. Never show held reasons, gates or LLM cost to the tenant. English by default, Vietnamese when the user picks it (memory pages-default-english).

<a id="crm-01"></a>

### CRM-01 Agency pipeline and conversion

Vietnamese name: Pipeline và chuyển đổi của đại lý.

| Field | Value |
|---|---|
| Audience | agency owner/admin, agency agents |
| Decision it supports | Which leads and sources convert, where trips stall, why trips are lost. |
| Cadence | live + monthly in CRM-05 |
| Channel | CRM web Reports page (apps/AA-Partner/web/lib/nav.ts, 'reports' entry, empty today) + Home KPI tiles |
| Automation | auto |
| Owner | agency owner |
| Status today | planned |
| Priority | P1 |
| Trigger | With the CRM release; before the first paying agency |
| Retention | Per agency retention settings; aggregates 36 months |
| Build effort | L (6 engineer-days; AA-966, slotted >= S263) |
| Running cost | 0 USD |

Sections:

- Trips by stage and stage age
- Stage conversion and win rate
- Lead source performance
- Lost and cancel reasons
- Cycle time inquiry to booked
- Year-on-year tiles

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| Win rate | Trips with a crm.trip_stage_history row with to_stage 'booked' / trips created in the cohort month (stages: inquiry, qualifying, proposal, booked, pre_departure, travelling, completed, lost, cancelled) | Agency-set target; trend |
| Stalled trips | crm.trip with stage_entered_at older than 14 days, stage not in completed/lost/cancelled | 0 without waiting_on |
| Lost reasons | crm.trip.lost_reason_code distribution (price, price_aa_tour, aa_sold_out, aa_on_request_declined, dates_changed, went_elsewhere, no_response, postponed, other) | Top 3 shown |
| Lead source mix | crm.trip.lead_source share and win rate | Informational |

Data sources:

- crm.trip, crm.trip_stage_history, crm.metric_event, crm.v_booking_line_money_current
- Planned crm metric_daily rollup (AA-966)

Notes: Design reference A-14 in docs/audits/2026-10-21-S246-crm-design-v3/final/crm-design-final.md (internal; not shown to agencies). RLS per tenant; AA staff never see agency PII. Agency-facing: plain KPI names, no IDs.

<a id="crm-02"></a>

### CRM-02 Agency response time and workload

Vietnamese name: Thời gian phản hồi và khối lượng việc của đại lý.

| Field | Value |
|---|---|
| Audience | agency owner/admin |
| Decision it supports | Are travellers answered fast enough; is any agent overloaded or late on tasks? |
| Cadence | weekly Monday + live tile; monthly in CRM-05 |
| Channel | CRM Reports page section + weekly in-app digest for the agency owner |
| Automation | auto |
| Owner | agency owner |
| Status today | missing |
| Priority | P2 |
| Trigger | Weekly |
| Retention | Aggregates 24 months |
| Build effort | M (2.5 engineer-days, inside AA-966) |
| Running cost | 0 USD |

Sections:

- First response time per conversation and per agent
- Unanswered inbound older than 24 h
- Overdue tasks by assignee
- Trips per owner

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| First response time | median(first outbound crm.message.occurred_at - first inbound occurred_at) per conversation_id, metadata only | <= 4 working hours |
| Unanswered > 24 h | Conversations whose latest crm.message is inbound and older than 24 h | 0 |
| Overdue tasks | crm.task not done (done_at null) with due_at < now, per assignee_member_id | 0 older than 2 days |

Data sources:

- crm.message (direction, occurred_at, conversation_id, author_member_id), crm.conversation, crm.task, crm.trip.owner_member_id

Notes: Never decrypt subject/body for reporting; timestamps only.

<a id="crm-03"></a>

### CRM-03 Agency e-mail channel health

Vietnamese name: Sức khoẻ kênh e-mail của đại lý.

| Field | Value |
|---|---|
| Audience | agency owner/admin; AA staff (counts only) |
| Decision it supports | Are connected mailboxes working; must the agency reconnect? |
| Cadence | daily job (exists) + weekly summary; monthly in CRM-05 |
| Channel | CRM settings health card; AA counts via the Agencies console (crm.ops.v1) |
| Automation | auto |
| Owner | agency owner |
| Status today | partial |
| Priority | P2 |
| Trigger | Daily; immediate alert on disconnect (exists) |
| Retention | Detail 90 days, aggregates 12 months |
| Build effort | S (1.5 engineer-days) |
| Running cost | 0 USD |

Sections:

- Mailboxes by status and last token check
- Send attempts and failures by outcome
- Mail imports (imported, duplicate, skipped)
- Disconnect alerts sent

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| Healthy mailboxes | crm.channel_account with status 'connected' and last_token_check_at within 24 h / accounts not deleted (statuses: connected, needs_attention, disconnected) | 100 % |
| Send failure | crm.dispatch_attempt with outcome in ('send_failed','send_uncertain') / attempts with decided_at not null and outcome <> 'retry' | < 2 % |
| Import skip | crm.mail_import skipped_count / total_count | < 5 % |

Data sources:

- crm.channel_account, crm.dispatch_attempt, crm.dispatch_queue, crm.mail_import
- crm_mail_health job (apps/AA-Partner/api/app/mail/health.py)

Notes: BYO mailboxes: the agency owns the account (memory crm-byo-shared-responsibility). Values from channel_account_status_chk and dispatch_attempt_outcome_chk.

<a id="crm-04"></a>

### CRM-04 CRM AI assistant usage

Vietnamese name: Sử dụng trợ lý AI trong CRM.

| Field | Value |
|---|---|
| Audience | agency owner/admin, AA staff (counts), tech lead |
| Decision it supports | Is the assistant used and useful per agency; is cost within entitlement; are refusals or errors rising? |
| Cadence | monthly in CRM-05 + live; AA roll-up monthly in FI-03 (K-LLM-TENANT) |
| Channel | CRM Reports page AI section; AA view counts only via crm.ops.v1 |
| Automation | auto |
| Owner | agency owner; tech lead for the AA roll-up |
| Status today | missing |
| Priority | P2 |
| Trigger | Monthly |
| Retention | Aggregates 24 months |
| Build effort | S (1.5 engineer-days) |
| Running cost | 0 USD |

Sections:

- Calls by stage and outcome
- Refusals and error classes
- Cost per agency vs entitlement
- Latency p95
- Scrubber receipts (PII removed counts)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| AI calls per active member | crm.llm_call rows per tenant_id / active crm.member rows | Adoption trend |
| Failure rate | crm.llm_usage_daily.failed_calls / calls (platform-wide; table has no tenant column) | < 3 % |
| Refusal rate | crm.llm_call with refusal_code not null / calls, per tenant | Flag > 5 % |
| Cost per agency | sum crm.llm_call.cost_usd_est per tenant_id in the month vs entitlement (allowed_features contains ai_assist) | <= entitlement |
| Latency p95 | p95 crm.llm_call.latency_ms | Trend |

Data sources:

- crm.llm_call (tenant_id, stage, outcome, refusal_code, error_class, cost_usd_est, latency_ms, scrub_receipt)
- crm.llm_usage_daily, crm.tenant_entitlement

Notes: Per-agency numbers come from crm.llm_call under RLS.

<a id="crm-05"></a>

### CRM-05 Agency monthly summary

Vietnamese name: Báo cáo tháng gửi chủ đại lý.

| Field | Value |
|---|---|
| Audience | agency owner |
| Decision it supports | How did the agency do this month and what to fix next month? |
| Cadence | monthly business day 2 |
| Channel | CRM Reports page (PDF/CSV) + e-mail to the agency owner; object under crm/<tenant>/ in the reports bucket, encrypted with the CRM key policy |
| Automation | auto |
| Owner | agency owner |
| Status today | missing |
| Priority | P2 |
| Trigger | Month end, agencies with activity |
| Retention | 36 months or the agency's retention setting, whichever is shorter |
| Build effort | M (2.5 engineer-days) after CRM-01 |
| Running cost | ~0 USD (SES) |

Sections:

- Headline: trips booked, revenue booked, win rate vs last month
- Pipeline (CRM-01)
- Response and workload (CRM-02)
- Channel health (CRM-03)
- AI assistant use (CRM-04)
- Seats vs member_limit and plan
- Data lifecycle runs and access summary (CRM-06)
- Traveller satisfaction (CX-01, agency trips)

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| Win rate | Defined in CRM-01 | Agency target |
| Booked value | crm.v_booking_line_money_current amount_base sums for trips that reached 'booked' in the month, in base_currency | vs last month |
| Seat use | Active crm.member rows / crm.tenant_entitlement.member_limit | > 90 % suggests plan change |

Data sources:

- CRM-01..CRM-04, CRM-06, CX-01 outputs
- crm.v_booking_line_money_current, crm.tenant_entitlement, crm.lifecycle_run

Notes: English by default; Vietnamese on user choice. Never shown to AA staff except counts.

## On demand

<a id="data-05"></a>

### DATA-05 On-demand report or data request

Vietnamese name: Yêu cầu báo cáo hoặc trích xuất số liệu theo nhu cầu.

| Field | Value |
|---|---|
| Audience | business owner, tech lead, Booking admin, AA staff |
| Decision it supports | Answer a specific question not covered by a scheduled report, or rerun a report for another period. |
| Cadence | on demand |
| Channel | /admin/reports Request form or a Jira/Linear comment; result in S3 + report_run; technical analyses in docs/audits/<date>-S<nnn>-<slug>/ |
| Automation | on_demand |
| Owner | tech lead (triage); agent runs |
| Status today | missing |
| Priority | P1 |
| Trigger | Request |
| Retention | Per the most sensitive data in the result |
| Build effort | S (1 engineer-day) for the form and run-for-period button |
| Running cost | 0 USD unless the request needs paid calls (then quote first) |

Sections:

- Request (question, decision it supports, period, audience)
- Method and sources
- Result
- Limits and caveats
- Promote-to-registry decision

KPIs:

| KPI | Definition | Target or threshold |
|---|---|---|
| K-OD-SLA Requests on time | Requests delivered within the SLA of their type / requests | >= 90 % |
| K-OD-REPEAT Repeat requests | Requests for the same question 2+ times in 90 days | 0 (promote to the registry instead) |

Data sources:

- Any registry KPI or report generator
- docs/architecture/db-schema-reference.md for new queries

Notes: See on-demand.md for fields and SLA.
