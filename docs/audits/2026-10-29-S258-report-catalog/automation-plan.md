# Automation plan

Part of the AA-1001 report catalog advisory (S258, 2026-10-29). Report IDs refer to [catalog.md](catalog.md); the
machine-readable list is [catalog.json](catalog.json). Everything below is a proposal: no table, job kind or page in
this plan exists yet unless the text says so.

## 1. One engine, many reports

Every scheduled report runs on the same small engine, built once in CIS (memory consistent-not-one-off):

- **Registry**: `docs/reports/catalog.yaml` (report ID, family, cadence, owner role, channel, template, generator) and `docs/reports/kpis.yaml` (KPI ID, version, definition, source tables, target). Neither file exists yet. Every table name is checked against `docs/architecture/db-schema-reference.md` by a CI lint.
- **Snapshots**: a new CIS table `shared.kpi_daily` (CIS migration) filled by job kind `kpi_snapshot_daily` at 00:30 UTC. Reports read snapshots and never recompute history.
- **Runs**: a new CIS table `shared.report_run` (report_id, period, status scheduled/draft/approved/posted/failed, output URIs, approved_by, approved_at). Booking and CRM keep their own run rows (`booking.report_run` via bk-NNN, CRM via crm.ops.v1), because each app writes only to its own schema.
- **Generator**: job kind `report_generate` (payload: report_id, period) on `aa-cis-dev-worker`, Booking `booking.job` and CRM `crm.job` for the reports those apps own. Output: JSON + Markdown (+ PDF for statements) to the reports bucket under `<app>/<report_id>/<period>/`.
- **Delivery**: SES through the existing `ops_alert_email` path (`apps/AA-CIS-App/services/jobs/ops_alert_email_job.py`), bells through `shared.notifications`, pages under `/admin/reports`. Booking uses `bk_notify_email`. Jira posts stay manual after approval (skill aa-jira-update).
- **Hub**: `/admin/reports` (EX-06) lists due, overdue and failed runs and links the latest output.

## 2. Schedule (UTC; ICT = UTC+7)

| Time | Cadence | Runs |
|---|---|---|
| hourly | every hour | TP-03 handoff check (alert only on gap) |
| 00:30 | daily | EX-04 KPI snapshot for the previous ICT day |
| 01:00 | daily | OPS-12 platform digest (every day), TP-03 daily summary, BK-01 Booking digest (Mon-Fri) |
| 02:00 | daily | EX-06 due/overdue check |
| 02:17-05:13 | nightly | DATA-01 probes (Infra workflows) upload summary JSON |
| Mon 00:43 | weekly | OPS-13 pg_stat_statements probe (Infra workflow) |
| Mon 01:30 | weekly | EX-01 draft, FI-02, CIS-01, CIS-05, TP-01, BK-02, BK-03, BK-06, OPS-13/14, DATA-02, DEV-03, EX-07 stuck list, FI-07 weekly flash, BK-04 contract expiry |
| BD2 02:00 | monthly | EX-02, FI-01 (+FI-03/05/06), FI-07 flash, FI-09, OPS-08 data pull, SEC-03 (+SEC-08/09/10 counts), DEV-01, CIS-02, CIS-03, CIS-04, BK-04, BK-05, CRM-05, MKT-01, MKT-02, CX-01 |
| BD3 | monthly | Cost sections refreshed from provisional to final |
| BD2 of Jan/Apr/Jul/Oct | quarterly | EX-05, SEC-05 reminder, SEC-09, SEC-10 full review, OPS-16 |
| event | on trigger | CIS-06, CIS-07, OPS-04, OPS-15, OPS-03, DATA-03, DEV-02, DEV-04, OPS-17, DATA-05 |

Business day 2 = the second Monday-Friday of the month (no holiday calendar until prod).

## 3. Levels of automation

- **auto** (generated and delivered without a person): EX-03, EX-04, EX-06, EX-07, FI-02, FI-03, FI-05, FI-07, CIS-01, CIS-03..07, TP-01, TP-03, BK-01..06, CRM-01..06, CX-01, MKT-01, OPS-12, OPS-14, DATA-01..04, DEV-01, DEV-03.
- **semi** (numbers generated, a person writes the narrative and approves): EX-01, EX-02, EX-05, FI-01, FI-04, FI-06, FI-09, CIS-02, TP-02, MKT-02, OPS-08, OPS-13, OPS-15, OPS-16, OPS-17, SEC-03, SEC-05, SEC-08, SEC-09, SEC-10, DEV-02.
- **manual** (a person writes it from a template): OPS-03, OPS-04, DEV-04.
- **on_demand**: DATA-05.

## 4. Approval and posting rules

- Drafts for the business owner are prepared during the week and shown once at session end (memory batch-drafts-at-session-end). Jira comments are posted only after approval (skill aa-jira-update).
- Claims say which channel was tested live (memory jira-claims-need-live-evidence).
- A failed generation writes `report_run.status = failed` and rings the bell; the next session re-runs it. A skipped period is back-filled once, never duplicated.

## 5. Guards

- Reports read stored rows only. No report calls an LLM, an eval, Cost Explorer (except FI-01's single refresh) or a paid API (DM-10.4, AA-635).
- Each app reads only its own schema. Cross-app numbers come from contract views granted to `cis_app` (bk-NNN, tp-NNN) or from the crm.ops.v1 feed.
- Commercial and tenant numbers stay in S3 and the owning app. Git gets platform-only reports while the root repo is public.
- Every generator has a unit test that runs its SQL against the schema reference names (column-name lint) and a golden Markdown snapshot.
- Prerequisite R0: fix the acc2 budget the forecast reads (`apps/AA-CIS-App/api/services/cost_ops.py` line 62 says 250; Terraform says 300), or every budget status will be wrong.

## 6. Templates

One template per report family, in [templates/](templates/). Each says in its header comment which report IDs use it.

| Family | Template | Used by |
|---|---|---|
| Executive | [business-review.md](templates/business-review.md) | EX-01 (weekly), EX-02 (monthly), EX-05 (quarterly) |
| Cost and FinOps | [cost-finops-review.md](templates/cost-finops-review.md) | FI-01 with FI-03/05/06; Part B FI-07, BK-03 |
| Product / app ops | [app-ops-report.md](templates/app-ops-report.md) | CIS-01, CIS-03, TP-01, BK-01, BK-02, BK-04..06, OPS-14, OPS-15 |
| AI content quality | [ai-content-quality.md](templates/ai-content-quality.md) | CIS-05, CIS-06, CIS-07 |
| Reliability | [slo-db-performance.md](templates/slo-db-performance.md) | OPS-13 with OPS-14, DATA-02 (monthly OPS-08 keeps `docs/templates/capacity-review.md`) |
| Security | [security-review.md](templates/security-review.md) | SEC-03 with SEC-08, SEC-09, SEC-10 counts (quarterly SEC-05 keeps `docs/templates/access-review.md`) |
| Incident | [incident-postmortem.md](templates/incident-postmortem.md) | OPS-04 (incl. cost incidents) |
| Release | [delivery-dora-report.md](templates/delivery-dora-report.md) | DEV-01 with DEV-02, DEV-03 |
| Data quality | [data-quality-report.md](templates/data-quality-report.md) | DATA-01..04, TP-03, CIS-02 |
| Customer and growth | [customer-growth-report.md](templates/customer-growth-report.md) | MKT-01, MKT-02, EX-07, CX-01 |
| Readiness and sign-off | [readiness-signoff.md](templates/readiness-signoff.md) | OPS-17, DEV-04, SEC-10 |

Agency- and tenant-facing reports (CIS-04, CRM-01..CRM-06) are product pages in AA-Partner and the tenant portal, not
Markdown templates; their sections are listed in the catalog.

When adopted, the templates move to `docs/templates/` (and their new IDs PLAT-03, PLAT-04, APP-11..APP-15, OPS-12..OPS-17,
SEC-08..SEC-10 are registered in `docs/README.md` in the same PR, roadmap R0).
