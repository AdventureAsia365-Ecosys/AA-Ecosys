# AA-896 implementation notes (root repo: Aug/Sep/Oct cost report, S248)

Session S248 (23/10/2026), Claude Code lane `aa896-finops`, branch `docs/aa896-cost-report-aug-oct`. Companion:
AA-CIS-Infra `feat/aa896-cost-anomaly-detection` (acc3 budget + anomaly e-mail, per-App budgets rebalanced).
Earlier notes: `AA-896-docs.md` (S243, FinOps doc + how-to).

## Decisions

- **Done now, not after 01/11** (Nghiệp, S248: no artificial deferrals). October is month to date (01–22/10) plus
  the AWS forecast; the report marks the refresh after the month closes (its section 9).
- **Cost Explorer through the CLI for this audit.** S243 chose "no new Cost Explorer script" (DM-10.4) and a monthly
  report built from the `/admin/platform/cost` export. That export cannot give August and September by usage type,
  nor acc3 by model and day, which the jump analysis needs. So the lane read Cost Explorer directly (18 requests,
  about 0.18 USD) and kept the exact commands in `scripts/fetch_ce.sh` for the refresh. It is documented as a
  one-off audit pull; the standing monthly process is unchanged. If reviewers prefer, delete the script and keep
  only `data/`.
- **Unit costs left as a table to fill.** The denominators need the DB; the subagent guardrail hook blocks ECS Exec.
  `scripts/aa896_units.py` is the read-only SQL (table and column names from `db-schema-reference.md` verified
  2026-10-22) for the orchestrator to run.
- **Per-App budget amounts changed in the doc** to match the Infra branch (cis 90, shared 100).
- **Vietnamese** for the audit (language convention, `docs/audits/` advisory exception); doc pages stay English.

## Changed

- New `docs/audits/2026-10-23-S248-cost-report/` (README, `data/*.json` raw Cost Explorer, `scripts/`).
- `docs/ops/finops.md`: budgets table (per-App amounts, acc3 budget + anomaly, acc1 budgets), acc1/acc3 check done,
  monthly review points at the preliminary report and the refresh date (03/11).
- `docs/ops/cost/README.md`: the first-report section points at the preliminary report.

## Tradeoffs

- Month-to-date numbers can move by a few percent after AWS revises; every October figure is labelled as 01–22/10
  or forecast.
- Explanations of LLM jumps are correlations between acc3 daily cost and session logs, not a per-stage split; the
  refresh replaces them with `llm_call_log` by stage.

## Should know

- `data/*.json` contain no account IDs (checked: no 12-digit account numbers; the 12-digit strings in the forecast
  files are decimal digits).
- The AA-CIS-Infra repo reports `visibility: PUBLIC` (`gh repo view`), while its `.claude/CLAUDE.md` says private.
  The new acc3 Terraform follows the existing files (account from `aws_caller_identity`, monitor UUID and the alert
  e-mail as variable defaults, both already present in that repo). Flagged for the orchestrator.
- acc2 Cost Anomaly Detection is live since 19/10 (Terraform Apply Prod run 39199328963).

## Follow-up on the same day (branch `docs/aa896-unit-costs`)

### Decisions

- **Per-model unit costs from CloudWatch, not the DB.** ECS Exec stays blocked for subagents, but CloudWatch
  `AWS/Bedrock` metrics (Invocations, InputTokenCount, OutputTokenCount, InvocationClientErrors per ModelId, daily
  sums) are readable with the acc3/acc1 profiles and cost about 0.001 USD (96 metrics). Joined with the Cost Explorer
  service lines already in `data/`, they give USD per 1,000 calls, USD per 1M tokens and tokens per call per model and
  month. Token counts times list price match Cost Explorer within 2 % (Haiku 4.5 and Sonnet 4.6, October).
- **Per-tour figure is an upper-bound estimate**, labelled as such: October acc3 LLM divided by the `reltuples`
  estimate of `gold_aa_internal.published_tours` (~892, schema dump 22/10). The exact per-stage, per-published-tour
  numbers still need `scripts/aa896_units.py` (orchestrator, ECS Exec).
- **Section 6 split** into 6a (per model, done) and 6b (per product, estimate + the DB table to fill).

### Changed

- New `scripts/fetch_cw_bedrock.sh`, `scripts/bedrock_units.py`, `data/acc3-bedrock-metrics.json`,
  `data/acc1-bedrock-metrics.json` (no account IDs; checked for 12-digit numbers).
- README: sources line, section 5 (Haiku jump = calls x 2.2 and cost per call x 2.2), section 6a/6b, findings F9
  (client-error rates of trial models) and F10 (Sonnet 4.6 is 4 % of calls, 27 % of LLM cost), section 9 refresh
  step 2 (CloudWatch pull).
- `docs/ops/finops.md`: unit-cost section names the CloudWatch join as the DB-free per-model source.

### Tradeoffs

- CloudWatch days are UTC midnights, Cost Explorer days are also UTC; small edge differences only.
- Model IDs are listed in the script; a new model must be added by hand (the script says how to find them).

### Should know

- `InvocationClientErrors` are counted apart from `Invocations` (successful calls), so error rate = errors /
  (calls + errors).
