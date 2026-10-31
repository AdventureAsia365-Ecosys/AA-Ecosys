---
id: FIN-02-howto
title: Monthly cost report
description: Step by step, how Claude Code drafts the monthly cost and capacity review from data the CIS API already stores, without new Cost Explorer calls.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 90
related: [FIN-01, FIN-02, OPS-08, AA-896, AA-838, AA-884]
---

# Monthly cost report

The monthly report is **one** document: the C8 capacity review plus the cost report (FIN-02 = OPS-08). It is
saved as `docs/audits/<date>-S<nnn>-capacity-review/README.md` with a root PR, drafted by Claude Code and
approved by the tech lead (C8a). This folder holds only this how-to; reports live in `docs/audits/` (DM-8.10, C8a).
Rules and budgets: [FinOps process](../finops.md).

> [!NOTE]
> Not yet run on real data. `tools/finops/collect_month.py` and `tools/finops/monthly_cost_report.py` are tested
> with synthetic inputs only (`tools/finops/test_*.py`). The first real run is the October 2026 report, in the first
> session on or after 2026-11-03 (see "Before you start"). Update this page with what that run teaches.

## Before you start

- When: the first session of the month, for the month that just ended. The same session runs the vulnerability
  triage ([SEC-03](../../security/vulnerability-management.md#monthly-triage)).
- Cost: 0 USD when the stored Cost Explorer data is fresh; one Cost Explorer request (0.01 USD) per month window
  that the admin page refreshes, plus two one-line reads in the management account (step 3, 0.02 USD). No new Cost
  Explorer script (DM-10.4).
- Wait two days after the month ends: Cost Explorer revises a day for about 48 hours.

## Steps

1. Confirm the account.

   ```bash
   aws sts get-caller-identity --profile aa365-admin
   ```

   Expected: the acc2 account (account map in `docs/onboarding.md`). Abort on any other account.

2. Collect the inputs, one run per app container (orchestrator session only: subagents cannot run ECS exec).
   `collect_month.py` is read-only, reads the stored Cost Explorer data through the CIS cost module
   (`cost_by_app`, the admin page's numbers) and removes every AWS account ID (`account_id` keys dropped,
   `account_name` and the satellite labels turned into the account key `acc2` / `acc3`, any other 12-digit number in
   a text replaced); if one is still left it prints nothing and exits 3. `MONTHS` defaults to the three whole months
   before today; set it to compare other months.

   ```bash
   mkdir -p .tmp-session/cost-2026-10
   tools/ecs/ecsx.sh tools/finops/collect_month.py PART=cis MONTHS=2026-08,2026-09,2026-10 > .tmp-session/cost-2026-10/cis.txt
   ECSX_SERVICE=aa-booking-dev-api tools/ecs/ecsx.sh tools/finops/collect_month.py PART=booking MONTHS=2026-08,2026-09,2026-10 > .tmp-session/cost-2026-10/booking.txt
   ECSX_SERVICE=aa-crm-dev-api tools/ecs/ecsx.sh tools/finops/collect_month.py PART=crm MONTHS=2026-08,2026-09,2026-10 > .tmp-session/cost-2026-10/crm.txt
   ```

   Verify: each file has one line starting with `FINOPS_BUNDLE `. If the report later lists "Stored Cost Explorer
   data was stale", run the CIS line again with `REFRESH=1` (one Cost Explorer request per stale month, about
   0.01 USD each, through the CIS client).

3. Read the management account's own spend for the report month and the month before. The CIS client reads acc2
   and acc3 only; the management account (organization CloudTrail trail and bucket, KMS key, budgets) is read here.
   Sign in first (`aws sso login --sso-session aa-mgmt-sso`), then one line per month (Cost Explorer endpoint is in
   us-east-1; the filter keeps the account itself, not the member accounts it pays for):

   ```bash
   aws ce get-cost-and-usage --time-period Start=2026-10-01,End=2026-11-01 --granularity MONTHLY --metrics UnblendedCost --filter "{\"Dimensions\":{\"Key\":\"LINKED_ACCOUNT\",\"Values\":[\"$(aws sts get-caller-identity --profile aa-mgmt --query Account --output text)\"]}}" --profile aa-mgmt --region us-east-1 --query 'ResultsByTime[0].Total.UnblendedCost.Amount' --output text
   ```

   Pass the two amounts as `--mgmt-usd` and `--mgmt-prev-usd` in step 5. Without them the report says in its totals
   and in summary line 1 that the management account is not included.

4. Optional: write the trip plan count (TripPlanner runs in Lambda, there is no container) to `units-YYYY-MM.json`,
   for example `{"trip_plans": 0}`. Take it with a read-only query; read the table and column names in
   `docs/architecture/db-schema-reference.md`, never from memory.

5. Draft the cost sections:

   ```bash
   python3 tools/finops/monthly_cost_report.py --bundle .tmp-session/cost-2026-10/cis.txt --booking-bundle .tmp-session/cost-2026-10/booking.txt --crm-bundle .tmp-session/cost-2026-10/crm.txt --mgmt-usd <amount> --mgmt-prev-usd <amount> --budget-usd 300 --out .tmp-session/cost-2026-10/cost-sections.md
   ```

   From the second report on, add `--prev-units docs/audits/<last month's review>/cis.txt` (the CIS bundle saved with
   last month's report). Published-tour counts change after the month ends (a republish overwrites `published_at`),
   so last month's per-tour cost comes only from the counts saved then; without `--prev-units` it shows `n/a`.

   Expected: Markdown with the five-line Vietnamese summary (lines 3 and 5 left as `<điền>`), "Totals by account",
   "By app", "Month over month" (every month of the bundle), "Top 5 services", "LLM spend" (by app, stage and role;
   ad-hoc stages apart), "Unit costs" and "Findings from the data". Untagged spend, changes over 20 %, an acc3 Cost
   Explorer figure under half of the gateway estimate (credits) and a missing CRM part are flagged.
   `--month YYYY-MM` drafts an earlier month of the bundle. `--budget-usd` is the acc2 account budget
   ([FinOps process](../finops.md#budgets-and-alerts)).

6. The single-export way still works (`--current` / `--previous` with the `/admin/platform/cost` JSON saved from
   the browser, `--llm-csv` from the SQL that `--print-sql` prints, `--units`), for a month the collector cannot
   reach.

7. Create `docs/audits/<date>-S<nnn>-capacity-review/README.md` from
   [`templates/cost-report.md`](../../templates/cost-report.md). Paste the drafted sections, keep the input files
   in the same folder (keep `cis.txt`: next month's `--prev-units`), then fill in by hand. The bundles hold no
   secrets, no personal data and no account IDs (the collector refuses to print one with an ID, and the report
   refuses to draft text with one). Check before committing:
   `grep -nE '(^|[^0-9A-Za-z_-])[0-9]{12}([^0-9A-Za-z_-]|$)' docs/audits/<folder>/*` prints nothing. A
   browser export of `/admin/platform/cost` does contain account IDs (`aws.account_id`,
   `llm_satellites.*.account_id`): do not commit it while the root repo is public; never copy it into an app repo
   (SEC-06, D-25). The drafted Markdown does not print account IDs.
   - the reason for each flagged change (Terraform applies, deploys, waves, batch runs in the month);
   - "Budgets and anomalies": budget e-mails and Cost Anomaly Detection alerts of the month;
   - the C8b capacity checklist (CloudWatch, Performance Insights, table sizes, ledgers, Lambda, jobs);
   - the five-line Vietnamese summary for the business owner (plain words, no Linear keys);
   - the action list.

8. Open the root PR (`docs: capacity and cost review YYYY-MM`, body `Refs AA-838, AA-896`) and ask the tech lead to
   approve. Rollback: the PR only adds files; close it to discard.

## The first report (October 2026)

Besides the normal content, compare August, September and October per app and per service and explain each jump
(the per-App tags exist only from 2026-10-15, so earlier months are by service only).

That comparison was drafted early, with October month to date, on 2026-10-23 (S248):
[`docs/audits/2026-10-23-S248-cost-report/`](../../audits/2026-10-23-S248-cost-report/README.md). Its section 9 lists
the refresh after the month closes. Its `scripts/fetch_ce.sh` is a one-off audit pull (11 Cost Explorer requests,
about 0.11 USD), kept so the numbers can be reproduced; it is not a standing client and does not replace step 2.
