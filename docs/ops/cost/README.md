---
id: FIN-02-howto
title: Monthly cost report
description: Step by step, how Claude Code drafts the monthly cost and capacity review from data the CIS API already stores, without new Cost Explorer calls.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-03
review_every_days: 90
related: [FIN-01, FIN-02, OPS-08, AA-896, AA-838, AA-884]
---

# Monthly cost report

The monthly report is **one** document: the C8 capacity review plus the cost report (FIN-02 = OPS-08). It is
saved as `docs/audits/<date>-S<nnn>-capacity-review/README.md` with a root PR, drafted by Claude Code and
approved by the tech lead (C8a). This folder holds only this how-to; reports live in `docs/audits/` (DM-8.10, C8a).
Rules and budgets: [FinOps process](../finops.md).

## Before you start

- When: the first session of the month, for the month that just ended. The same session runs the vulnerability
  triage ([SEC-03](../../security/vulnerability-management.md#monthly-triage)).
- Cost: 0 USD when the stored Cost Explorer data is final; with `REFRESH=1` about 0.03 USD per month that is not
  final yet (step 2), plus two one-line reads in the management account (step 3, 0.02 USD) and, to explain the
  jumps, about two usage-type reads (0.02 USD, see "What the first real run taught"). No new Cost Explorer script
  (DM-10.4).
- Wait two days after the month ends: Cost Explorer revises a day for about 48 hours. Collect the final report's
  bundles at or after month end + 48 hours (for October 2026: 2026-11-02 23:30 UTC), with `REFRESH=1` (step 2).

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

   Verify: each file has one line starting with `FINOPS_BUNDLE`. For the final report add `REFRESH=1` to the CIS
   line (after `PART=cis`): for every month whose stored Cost Explorer data is not final yet (fetched less than
   3 days after the month ended) it makes the same two fetches as `POST /admin/cost-explorer/check`, through the CIS
   client: the acc2 App-tag snapshot (one request, about 0.01 USD) and the acc2 + acc3 SERVICE snapshot that the
   acc3 line reads (one request per account, about 0.02 USD). A final month is not fetched again, so the older
   months of `MONTHS` cost nothing. Check `months.<month>.refreshed` in the bundle: `service.ok` is true and
   `service.accounts_failed` is empty. If the report lists "Stored Cost Explorer data was stale", run the CIS line
   again with `REFRESH=1`.

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

## What the first real run taught (October 2026, S265)

The first run on real data was the October 2026 report
([`docs/audits/2026-11-03-S265-capacity-review/`](../../audits/2026-11-03-S265-capacity-review/README.md)).

- **`REFRESH=1` refreshed only half of the data.** It refreshed the acc2 App-tag snapshot
  (`shared.cost_explorer_app_snapshot`), which the App rows and the acc2 total read, but not the acc2 + acc3 SERVICE
  snapshot (`shared.cost_explorer_snapshot`), which the acc3 Bedrock line (`llm_satellites`) reads: the first
  bundle's acc3 figure was a fetch from five days before the month ended. The orchestrator had to run the
  equivalent of `POST /admin/cost-explorer/check` for the month first (`fetch_all_accounts_cost` +
  `record_snapshot`, about 0.02 USD). Fixed with the October report: `REFRESH=1` now refreshes both snapshots
  (step 2).
- **"fresh" is not "final".** The stale rule of the cost module (`platform_cost._is_stale`) calls a month `fresh`
  when every stored day was fetched less than 24 hours ago, even before `FINAL_AFTER` (3 days after the month
  ended). A bundle collected on the 1st can therefore read `fresh` and still miss the last day and the revisions of
  the last 48 hours (October: +11.02 USD on acc2 between the 01/11 and the 02/11 fetch). Run the final report's
  refresh at or after month end + 48 hours; `REFRESH=1` now also refreshes a `fresh` month until it is final.
- **Explaining the jumps needs usage types.** The bundle carries service and `App` tag only. Two one-line
  `get-cost-and-usage` reads on acc2 (0.01 USD each) answered most of the open items: one MONTHLY read of the report
  month and the month before, grouped by `SERVICE` and `USAGE_TYPE` and filtered to the flagged services; one DAILY
  read of the report month, filtered to the usage types that moved. The S248 11-request script is not needed for
  this.
- **The MFA session can expire in the middle of the run.** Plan the Cost Explorer reads in one window right after
  `aws sts get-caller-identity`; a read that stops at the MFA prompt is not sent and costs nothing.

## The first report (October 2026)

Besides the normal content, compare August, September and October per app and per service and explain each jump
(the per-App tags exist only from 2026-10-15, so earlier months are by service only).

That comparison was drafted early, with October month to date, on 2026-10-23 (S248):
[`docs/audits/2026-10-23-S248-cost-report/`](../../audits/2026-10-23-S248-cost-report/README.md). Its section 9 lists
the refresh after the month closes. Its `scripts/fetch_ce.sh` is a one-off audit pull (11 Cost Explorer requests,
about 0.11 USD), kept so the numbers can be reproduced; it is not a standing client and does not replace step 2.
