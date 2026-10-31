# AA-896 implementation notes (S262 lane w4f-finops-896: monthly report pipeline, FinOps page, App-tag monitor)

Session S262 (31/10/2026), Claude Code subagent, branches `docs/aa-896-finops` (root) and `feat/aa-896-cost-anomaly`
(AA-CIS-Infra). Earlier notes: `AA-896-docs.md` (S243), `AA-896-cost-report.md` (S248).

## Decisions

- **No new Cost Explorer script.** The lane brief asked for `tools/finops/cost_report.py` calling `GetCostAndUsage`
  with the `aa365-admin` / `aa-mgmt` profiles. The repo already decided against that (S243 reconciliation K-14,
  `docs/ops/finops.md` "Do not write a new script that calls Cost Explorer", `docs/ops/cost/README.md`): the CIS
  client stores Cost Explorer by `App` tag and service, and `api.services.platform_cost.cost_by_app` is the one cost
  module. So the slice extends the existing `tools/finops/monthly_cost_report.py` and adds a collector that runs
  `cost_by_app` inside the CIS container. Same numbers as the admin page, no second CE client to keep in step.
- **Collector run through `tools/ecs/ecsx.sh`** (`tools/finops/collect_month.py`, `PART=cis|booking|crm`). One run per
  app container, because each DB login reads only its own schemas (`cis_app` cannot read `booking.*` or `crm.*`).
  Read-only (`default_transaction_read_only`), except `REFRESH=1`, which refreshes a stale App-tag window through the
  CIS client (one CE request, about 0.01 USD per month window) and therefore needs write.
- **Report location stays `docs/audits/<date>-S<nnn>-capacity-review/`** (C8a in data standards 03-scaling; the cost
  report and the capacity review are one document, K-05). The brief's `docs/ops/cost/YYYY-MM.md` would contradict
  C8a and `docs/ops/cost/README.md` ("this folder holds only this how-to"). The Linear "2026-10.md report" maps to
  that audit README.
- **Bundle files carry no account IDs** (review fix pass). The root repo is public for now (ADR 0014 amendment) and
  the inputs are kept next to the report. `cost_by_app` holds IDs in three shapes, not only `account_id`:
  `apps[].ai_by_source[].account_name` (accounts.account_name gives the ID of acc2/acc3) and
  `llm_satellites.lines[].label` ("<id> (LLM)"). `scrub()` now drops `account_id`, turns `account_name` into the
  entry's account key and the line label into "acc3 (LLM)", and replaces any other 12-digit run in a string or key
  (an ARN in a refresh error, a future field) with `<account-id>`. `find_account_ids()` is the last guard: `main()`
  prints nothing and exits 3 if one is left. The report refuses to draft Markdown that holds a 12-digit number.
  The regex skips a digits-only UUID tail (`-` before it) and floats are not checked (amounts, not IDs).
- **Last month's per-tour cost is n/a unless frozen** (review fix pass). `published_tours` has one row per tour and a
  republish overwrites `published_at`; no table logs each publish of a master tour (`acp_shared.publish_log` is the
  tenant channel log, checked in db-schema-reference). So the report month's count is taken right after the month
  ends, and last month's comes from the CIS bundle saved with last month's report (`--prev-units`, bundle or units
  JSON). Without it the "Last month" cell of the two tour rows says "n/a (published_at is overwritten on
  republish)". Trip-case units use `created_at`, which does not move, so they keep the last-month column.
- **Management account in the totals** (review fix pass). The CIS client reads acc2 and acc3 only. `--mgmt-usd` /
  `--mgmt-prev-usd` take the management account's own spend from a one-line `aws ce get-cost-and-usage` with profile
  `aa-mgmt` (filter LINKED_ACCOUNT = itself, so member accounts it may pay for later are not counted twice; 0.01 USD
  per request, run by the orchestrator). It is its own row in "Totals by account", added to the grand total and to
  Vietnamese line 1; line 2 compares like for like (with it only when both months are given). Without the input the
  totals and line 1 say plainly that the management account is not included. Not a standing CE client: one read per
  month in an account the CIS client cannot reach.
- **Retired satellite key.** `cost_by_app` names the former fallback account `retired` since AA-998; the report's
  satellite rows now accept it (old exports still use `acc1`).
- **CRM LLM spend from `crm.llm_usage_daily`** (PART=crm). `cost_by_app` gets the CRM spend only through the staff
  token path (`crm_llm`), which a container script does not have. The report adds the CRM part to the `crm` row as
  spend outside the acc2 bill, like the admin page does.
- **Vietnamese summary drafted from the numbers.** Lines 1, 2, 4 and the unit cost are filled; the reason (line 3)
  and the decision (line 5) stay `<điền>` because the data does not know them.
- **acc3 Cost Explorer vs the gateway estimate.** Since 29/10 acc3 pays with its AWS Lift credit, and CE
  `UnblendedCost` is net of credits (lesson log, S260). The report flags a CE figure under half the estimate instead
  of treating it as a saving.
- **Infra: App-tag anomaly monitor prepared, off by default.** acc2 is a member of the reseller's organization, not of
  ours, so tag monitors (management account only) cannot see its spend today; the existing services monitor and the
  IMMEDIATE SNS subscription on acc2 (S243) and the per-account monitors in the management root (AA-1004) already
  exist. The management root gets one CUSTOM monitor per `App` value plus a daily e-mail subscription, behind
  `app_tag_anomaly_monitors_enabled = false`, switched on after the nonprod account joins the organization and the
  tag is active in the management account.

## Changed

- `tools/finops/collect_month.py` (new) + tests.
- `tools/finops/monthly_cost_report.py`: `--bundle` / `--booking-bundle` / `--crm-bundle` / `--month` inputs,
  month-over-month section for every month in the bundle, LLM table with app column, unit costs incl. the bookings
  count, budget line, Vietnamese summary draft, acc3 credit finding, CRM finding. The old flags still work.
- `docs/ops/finops.md`: rules stated (explicit yes before a paid service, run ladder, LLM ledger), the
  `shared.spend_budget` caps (migration 318), the gateway connection budgets (ADR 0009 decision 6), the management
  root guards (AA-1004), the AI use register link, the App-tag monitor status.
- `docs/ops/cost/README.md`: the collector steps replace the manual JSON/CSV export.
- Infra `accounts/management/cost_anomaly_app_tag.tf` + variables + README row + static tests.
- Untracked `tools/finops/__pycache__/*.pyc` (committed by mistake in S243; `__pycache__/` is already in `.gitignore`).

## Tradeoffs

- One script per container instead of one call: three exec runs at month end, but no cross-schema grant.
- `published_at` counts tours published or republished in the month (republish moves `published_at`); the unit is
  "USD per published or republished tour". The live count at month end is shown next to it.
- Trip plans are still a manual `--units` input: TripPlanner runs in Lambda, there is no container to exec into.

## Should know

- Review fix pass (S262): the sample CIS bundle now has the current `cost_by_app` shape (`hint`, `ai_by_source` with
  `account_name`, `llm_satellites.lines`) in its scrubbed form; the raw shape with invented IDs is built in
  `test_collect_month.py` (`test_a_cost_by_app_answer_leaves_no_account_id_in_the_bundle`).

- Nothing here calls AWS from a test; the collector's DB part is tested with a fake connection.
- The final October numbers: run on or after 03/11 (CE revises a day for about 48 h); a run on 01/11 is provisional.
- The App-tag monitor needs no apply now (default false: the plan is empty). Activating `App` as a cost allocation
  tag in the management account stays a console step (Billing, Cost allocation tags), see the Infra notes.
- `ecsx.sh` prints the bundle line on stdout; `--bundle` finds the `FINOPS_BUNDLE` line among other output lines.
