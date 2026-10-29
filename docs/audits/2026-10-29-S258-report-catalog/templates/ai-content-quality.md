---
id: APP-12-yyyy-ww
title: AI content quality report <period>
description: <One sentence - whether writing quality is stable, the judge is reliable and the active release should stay.>
type: report
status: draft
owner: nghiep
audience: [engineer, pm, agent]
applies_to: [aa-cis-api]
last_reviewed: 2026-10-29
review_every_days: 90
related: [APP-06, PLAT-01, AA-922]
---

# AI content quality report <period>

<!-- Report family: AI content quality. Register APP-12 in docs/README.md before first use. Used by CIS-05 (weekly),
CIS-06 (per eval or release, id APP-12-rel-<release>) and CIS-07 (per wave, id APP-12-wave-<wave>).
The report reads stored rows only and never starts a paid eval or LLM call.
Every cost line comes from shared.llm_call_log / shared.llm_call_daily by stage and job_id (memory wave-report-cost).
Internal only: gate results, held reasons and judge scores never reach a tenant. Delete this comment. -->

> [!NOTE]
> Judge agreement is computed on the labelled sample of the latest eval run. Its date is shown; an old run means the KPI may be stale.

Period or event: <ISO week | release id | wave id>. Generated: <UTC time>, run <id>. Writer(s): <a1 | t2 | t9_blog | t9_social>.
Active release: <id, activated date>. Baseline: <release or run id>. Latest eval run: <id, finished date>.

## 1. Verdict

NARRATIVE: keep / roll back / investigate, in one sentence, with the KPI that decides it.

## 2. How to read this report

- Kappa measures judge agreement with human labels; below 0.6 the judge informs but does not gate.
- A gate fire rate outside +/-5 points of its 4-week median is a drift signal, not a failure by itself.
- Quality delta compares the run with its baseline on the same items.

## 3. KPIs

| KPI (ID@version) | Definition | Target | Actual | Previous | Trend | Status |
|---|---|---|---|---|---|---|
| K-AIQ-KAPPA@1 | Judge kappa, latest finished run | >= 0.6 | | | | |
| K-AIQ-REGRESSION@1 | Runs with regression_detected | 0 | | | | |
| K-AIQ-SCORE@1 | Average score_overall | drop <= 3 points | | | | |
| K-AIQ-GATEFIRE@1 | Fire rate per gate (worst gate shown) | +/-5 pts of median | | | | |
| K-TEN-HELD@1 | Held rate (content_piece status held) | < 10 % | | | | |
| K-EVAL-COST@1 | Eval or wave cost vs cap | <= cap | | | | |

## 4. Gates

| Gate | Fire rate | 4-week median | Change | Top reason |
|---|---|---|---|---|

## 5. Releases and signals

| Writer | Active release | Reverify flag | Days since activation | Signals this period | Rules active |
|---|---|---|---|---|---|

## 6. Item-level regressions (eval or release only)

Top 10 items by score drop, with the gate or rule that changed. No tenant names.

## 7. Cost (wave or eval only)

| Stage | Calls | Cost USD | USD per tour | Cap | Status |
|---|---|---|---|---|---|
| Wave total | | | | | |
| Running total for the run | | | | | |

## 8. Decisions needed

| # | Decision | Context | Options | Recommendation | Owner role | Needed by |
|---|---|---|---|---|---|---|

## Sources

shared.prompt_eval_runs, shared.eval_item_result, shared.writing_memory_release, shared.writing_signal,
acp_shared.content_piece, silver_aa_internal.quality_scores, shared.llm_call_log; run ids.
