---
id: OPS-04-pm-yyyy-mm-dd-slug
title: "Postmortem: <short title> (<YYYY-MM-DD>)"
description: <One sentence - what broke or overspent, for how long and what it cost.>
type: report
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [replace-me]
last_reviewed: 2026-10-30
related: [OPS-04, FIN-01]
---

# Postmortem: <short title> (<YYYY-MM-DD>)

<!-- Report OPS-04 (incident and postmortem, cost incidents included; root docs/reports/catalog.yaml). Blameless.
Store at docs/ops/postmortems/<YYYY-MM-DD>-<slug>.md and add a row to docs/ops/postmortems/README.md (single place for
incident records, G-14). Write within 5 working days of a SEV1 or SEV2 (docs/ops/incident-response.md); the Linear note
within 2 working days. A cost incident is SEV2 when the excess is >= 50 USD or > 20 % of a monthly budget. Write the
lesson to skill/aa-lessons/lessons.md at root-cause time. No account IDs, ARNs, secrets or vendor contract terms: this
repo may be public. Delete this comment. -->

## 1. Summary

<Two or three sentences: what happened, impact, how it ended.>

## 2. Impact

| Item | Value |
|---|---|
| SEV | <1 / 2 / 3> |
| Who was affected | <tenants / travellers / staff / none external> |
| Duration | <start - end ICT, minutes> |
| Data | <lost / exposed / none> (Dev holds test data only) |
| Cost impact | <USD excess vs baseline, or none> |
| Paid runs stopped or delayed | <which, how long> |

## 3. Key times

| KPI (ID@version) | Definition | Target | Actual |
|---|---|---|---|
| K-INC-TTD@1 | Impact start to first alert or report | < 15 min (SEV1) | |
| K-INC-TTR@1 | Detection to restored | < 1 working day | |
| K-INC-COSTATTR@1 | Cost alert to written cause | <= 1 working day | |

## 4. Timeline (UTC+7)

| Time | Event | Source (alarm, bell, e-mail, person) |
|---|---|---|
| <hh:mm> | <event> | <source> |

## 5. Detection

Which signal fired first, which should have fired and did not, and how long the gap was.

## 6. Root cause

5 whys down to the system cause (process, guard, test or design), not a person.

## 7. Cost attribution (cost incidents)

| Account | App tag | Service / usage type | LLM stage or job kind | job_id(s) | Excess USD |
|---|---|---|---|---|---|

Trigger: <deploy, wave, job, test tenant, provider change>. Guard that should have stopped it: <spend_budget, cap, kill
switch>. Write "Not a cost incident" when nothing overspent.

## 8. What went well, what went badly

### Went well

- <...>

### Went badly

- <...>

### Where we got lucky

- <...>

## 9. Actions

| Action | Type (guard, test, alarm, runbook, design) | Owner role | Due | Linear issue | Status |
|---|---|---|---|---|---|

## 10. Communication

Who was told and when (business owner within 30 min for SEV1; tenants within 2 h if affected).

## 11. Business summary

<Three sentences for the business owner: what happened, what it affected, what stops a repeat. No issue keys, no
jargon. A Vietnamese version goes in a sibling `.vi.md` file when needed (docs/STYLE.md, Language).>

## 12. Lessons

Link to the lessons entry (`skill/aa-lessons/lessons.md`) and to any runbook or playbook changed.
