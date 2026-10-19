# AA-896 implementation notes (root repo: FinOps process and monthly cost report)

Scope: S243 (19/10/2026), Claude Code, branch `docs/aa895-aa896-security-finops`. Pages: `docs/ops/finops.md`
(FIN-01), `docs/ops/cost/README.md` (FIN-02 how-to), script `tools/finops/monthly_cost_report.py` with a unit test
and synthetic samples. Companion: AA-CIS-Infra `feat/aa896-cost-anomaly-alarm-runbooks` (Cost Anomaly Detection
to the alerts topic, runbook links in alarm descriptions for AA-893 step 1).

## Decisions

- **finops.md links DM-10 instead of copying it** (reconciliation K-13, correction 11). The "quote the monthly
  cost before a new service" rule is S241 D-19; the page marks it as a proposed DM-10.7 line for v1.1 (N-1).
- **No new Cost Explorer script** (DM-10.4, K-14, correction 11). The brief asked for a script that reads Cost
  Explorer; the reconciliation forbids it, so `monthly_cost_report.py` reads the JSON of
  `GET /admin/platform/cost` (AA-884, which already stores CE data by `App` tag and service and LLM spend by
  app) and an optional CSV of LLM spend by stage (read-only SQL mirroring `platform_cost.AI_SPEND_SQL`). Zero AWS
  calls; standard library only.
- **Tag `Environment`, not `Env`** (DM-10.1, correction 10). Live check: `aws ce list-cost-allocation-tags`
  answers "Linked account doesn't have access to cost allocation tags", so activation is done by the payer, as
  for `App` on 15/10. Written as a Nghiệp action.
- **Report location**: `docs/audits/<date>-S<nnn>-capacity-review/` (C8a, K-05, correction 5); `docs/ops/cost/`
  holds only the how-to. One report = C8 capacity review + cost report.
- **No App-tag anomaly monitor**: the AWS guide allows tag monitors only in the management account; acc2 is a
  member account. Per-App budgets (AA-828) cover that.

## Changed

- Brief: "tools/finops/monthly_cost_report.py reads Cost Explorer read-only + optional CSV". Done as "reads the
  AA-884 export + optional CSV", per the reconciliation.
- Brief: "tags App + proposal Env". Done as App + existing `Environment`.
- Brief: "docs/ops/cost/README.md explaining the monthly report". Done; it states that the reports live in
  `docs/audits/`.
- Budgets cost: AWS Budgets without actions are free (pricing page read 19/10), so the guards cost 0 USD.

## Tradeoffs

- Reading the admin export means the report depends on the AA-884 code path being correct; the upside is one
  number source for the admin page, the overview card and the report (reconciliation overlap row AA-896).
- The export needs either a browser (Nghiệp) or ECS exec (orchestrator only); subagents cannot produce it.

## Should know

- Tests: `python3 -m unittest discover -s tools/finops -p 'test_*.py'` (4 tests, synthetic data, account IDs
  replaced by placeholders).
- The how-to is `status: draft` with a NOTE: never run on real data. First real run: the October report in the
  first session on or after 01/11, which also compares August to October (memory `infra-cost-audit-nov-2026`).
- Budgets on acc1/acc3 were not checked (other profiles); listed as a check for the first monthly review.
- The `/admin/platform/cost` JSON saved with each monthly report contains the real account IDs
  (`aws.account_id`, `llm_satellites.*.account_id`). That is allowed in the private root repo (SEC-06, D-25);
  the how-to says so and forbids copying the inputs into an app repo. The drafted Markdown does not print them
  (S243 review).
