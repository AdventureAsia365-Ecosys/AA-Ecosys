# On-demand reports (DATA-05)

Part of the AA-1001 report catalog advisory (S258, 2026-10-29). See [catalog.md](catalog.md) for the scheduled reports
and [automation-plan.md](automation-plan.md) for the engine (`/admin/reports`, `shared.report_run`) this page relies on;
both are proposals.

## When to use

A question that no scheduled report answers, a scheduled report for another period, or a one-off export. If the same question comes twice in 90 days, it becomes a registry report instead (K-OD-REPEAT).

## How to ask

Use the Request form on `/admin/reports`, or a Jira/Linear comment. Fields:

| Field | Example |
|---|---|
| Question | How many Vietnam tours lost their cover photo after the last wave? |
| Decision it supports | Re-run photo matching for Vietnam or not |
| Period | 2026-10-01 to 2026-10-31 (ICT) |
| Audience | business owner / staff / tenant / agency |
| Format | table on screen, CSV, Markdown, PDF |
| Sensitivity | platform / tenant / commercial / personal |
| Needed by | date |
| Paid calls allowed? | no (default) / yes with quote |

## Service levels

| Type | Example | SLA |
|---|---|---|
| Rerun a registry report for another period | FI-01 for September | same working day |
| Count or export from existing views | tours without cover by country | 1 working day |
| New analysis on existing data | margin by trip style for Q4 | 3 working days |
| Needs new data capture or a migration | acquisition by campaign | planned as a backlog item, not on demand |
| Needs paid API or LLM calls | re-scoring 50 tours | only after a cost quote and an explicit yes (memory cost-advice-new-aws-services, paid-runs-subset) |

## Rules

- Table and column names only from `docs/architecture/db-schema-reference.md`. CIS data through ECS exec with the container `DATABASE_URL` (role cis_app). Booking, TripPlanner and CRM data through DB Migrate `mode=run-script` or the owning app's endpoint, never with the master secret from a container.
- Results inherit the sensitivity of their most sensitive input: commercial or personal results go to S3 under the owning app's prefix, never to git or Jira. Technical, non-sensitive analyses go to `docs/audits/<date>-S<nnn>-<slug>/` with a root PR (memory save-audits-locally).
- Every result states its period, sources, run time and limits. Dev data is labelled as Dev.
- Each request writes a `shared.report_run` row with report_id DATA-05 so the hub shows it and repeats can be counted.
- At the end, decide whether to promote it to the registry (new report ID, template, cadence) and note the decision in the result.

## Self-serve views (no request needed)

- `/admin/overview` Trend tab with CSV for any range (EX-04)
- `/admin/cost-ops` and `/admin/platform/cost` with Download JSON/CSV (FI-01..FI-06)
- `/admin/data-coverage`, `/admin/places`, `/admin/writing-memory`, `/admin/jobs`
- Booking Reports and billing pages with CSV (BK-02, BK-03, FI-07)
- CRM Reports page for agency owners (CRM-01..CRM-06)

Only `/admin/data-coverage`, `/admin/places`, `/admin/writing-memory`, `/admin/jobs`, `/admin/cost-ops`,
`/admin/platform/cost` and the Booking billing CSV exist today; the Trend tab, Download buttons, Booking Reports and
CRM Reports pages are proposals in this catalog.
