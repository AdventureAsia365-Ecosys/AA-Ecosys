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
- **Bundle files carry no account IDs.** The collector drops every `account_id` key before printing, because the
  root repo is public for now (ADR 0014 amendment) and the inputs are kept next to the report.
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
- Infra `accounts/management/cost_anomaly_app_tag.tf` + variables + README row.

## Tradeoffs

- One script per container instead of one call: three exec runs at month end, but no cross-schema grant.
- `published_at` counts tours published or republished in the month (republish moves `published_at`); the unit is
  "USD per published or republished tour". The live count at month end is shown next to it.
- Trip plans are still a manual `--units` input: TripPlanner runs in Lambda, there is no container to exec into.

## Should know

- Nothing here calls AWS from a test; the collector's DB part is tested with a fake connection.
- The final October numbers: run on or after 03/11 (CE revises a day for about 48 h); a run on 01/11 is provisional.
- The App-tag monitor needs no apply now (default false: the plan is empty).
