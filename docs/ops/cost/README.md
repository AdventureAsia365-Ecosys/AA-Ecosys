---
id: FIN-02-howto
title: Monthly cost report
description: Step by step, how Claude Code drafts the monthly cost and capacity review from data the CIS API already stores, without new Cost Explorer calls.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-19
review_every_days: 90
related: [FIN-01, FIN-02, OPS-08, AA-896, AA-838, AA-884]
---

# Monthly cost report

The monthly report is **one** document: the C8 capacity review plus the cost report (FIN-02 = OPS-08). It is
saved as `docs/audits/<date>-S<nnn>-capacity-review/README.md` with a root PR, drafted by Claude Code and
approved by Nghiệp (C8a). This folder holds only this how-to; reports live in `docs/audits/` (DM-8.10, C8a).
Rules and budgets: [FinOps process](../finops.md).

> [!NOTE]
> Not yet run on real data. `tools/finops/monthly_cost_report.py` is tested with synthetic inputs only
> (`tools/finops/test_monthly_cost_report.py`). The first real run is the October 2026 report, in the first
> session on or after 2026-11-01. Update this page with what that run teaches.

## Before you start

- When: the first session of the month, for the month that just ended. The same session runs the vulnerability
  triage ([SEC-03](../../security/vulnerability-management.md#monthly-triage)).
- Cost: 0 USD when the stored Cost Explorer data is fresh; one Cost Explorer request (0.01 USD) per month window
  that the admin page refreshes. No new Cost Explorer script (DM-10.4).
- Wait two days after the month ends: Cost Explorer revises a day for about 48 hours.

## Steps

1. Confirm the account.

   ```bash
   aws sts get-caller-identity --profile aa365-admin
   ```

   Expected: the acc2 account (account map in `docs/onboarding.md`). Abort on any other account.

2. Export the cost-per-app JSON for the month and for the month before. Choose one way:
   - **Browser (Nghiệp):** open the admin console page **Cost per app** (`/admin/platform/cost`), pick the month,
     and in the browser developer tools save the response of the `cost?month=YYYY-MM` request as
     `platform-cost-YYYY-MM.json`.
   - **ECS exec (orchestrator session only):** a short script inside the api container calls
     `api.services.platform_cost.cost_by_app(pool, "YYYY-MM", refresh_if_stale=False)` and writes the JSON to the
     bronze bucket `scripts/` prefix (S3-mediated pattern, `skill/aa-cis-schema/references/ecs-exec.md`).
     Subagents cannot run ECS exec.

   Verify: the JSON has `month`, `aws.covered_from`, `aws.covered_to` and `refresh.stale = false`. If `stale` is
   true, refresh first (admin page, or `POST /admin/cost-explorer/check`, about 0.01 USD) and export again.

3. Export LLM spend by stage for the month (read only):

   ```bash
   python3 tools/finops/monthly_cost_report.py --print-sql
   ```

   Run the printed SQL through the same ECS exec pattern with the first day of the month and of the next month,
   and save the result as CSV with a header row (`stage,role,account,calls,cost_usd`).
   Verify: the CSV total is close to the LLM total in the JSON (they read the same ledgers).

4. Optional: write the unit-cost denominators to `units-YYYY-MM.json`, for example
   `{"published_tours": 0, "trip_plans": 0, "bookings": 0}`. Take the counts with read-only queries; read the
   table and column names in `docs/architecture/db-schema-reference.md`, never from memory.

5. Draft the cost sections:

   ```bash
   python3 tools/finops/monthly_cost_report.py --current platform-cost-2026-10.json --previous platform-cost-2026-09.json --llm-csv llm-by-stage-2026-10.csv --units units-2026-10.json --out cost-sections.md
   ```

   Expected: Markdown with "Totals by account", "By app", "Top 5 services", "LLM spend", "Unit costs" and
   "Findings from the data". Untagged spend and changes over 20 % are flagged.
   If it stops with "not a /admin/platform/cost response", the export in step 2 saved the wrong request.

6. Create `docs/audits/<date>-S<nnn>-capacity-review/README.md` from
   [`templates/cost-report.md`](../../templates/cost-report.md). Paste the drafted sections, keep the input files
   in the same folder, then fill in by hand. The inputs hold no secrets and no personal data, but the
   `/admin/platform/cost` JSON contains the real account IDs (`aws.account_id`, `llm_satellites.*.account_id`):
   keep them in this private root repo only, never copy them into an app repo (SEC-06, D-25). The drafted
   Markdown does not print account IDs.
   - the reason for each flagged change (Terraform applies, deploys, waves, batch runs in the month);
   - "Budgets and anomalies": budget e-mails and Cost Anomaly Detection alerts of the month;
   - the C8b capacity checklist (CloudWatch, Performance Insights, table sizes, ledgers, Lambda, jobs);
   - the five-line Vietnamese summary for Ms. Thư (plain words, no Linear keys);
   - the action list.

7. Open the root PR (`docs: capacity and cost review YYYY-MM`, body `Refs AA-838, AA-896`) and ask Nghiệp to
   approve. Rollback: the PR only adds files; close it to discard.

## The first report (October 2026)

Besides the normal content, compare August, September and October per app and per service and explain each jump
(the per-App tags exist only from 2026-10-15, so earlier months are by service only).

That comparison was drafted early, with October month to date, on 2026-10-23 (S248):
[`docs/audits/2026-10-23-S248-cost-report/`](../../audits/2026-10-23-S248-cost-report/README.md). Its section 9 lists
the refresh after the month closes. Its `scripts/fetch_ce.sh` is a one-off audit pull (11 Cost Explorer requests,
about 0.11 USD), kept so the numbers can be reproduced; it is not a standing client and does not replace step 2.
