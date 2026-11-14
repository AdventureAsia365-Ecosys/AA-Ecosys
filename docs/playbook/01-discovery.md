---
id: GUIDE-14-discovery
title: "Phase 1: Discovery"
description: Understand the problem and decide whether to build at all - deliverables, gate G1 checklist, templates and common mistakes.
type: how-to
status: draft
owner: nghiep
audience: [owner, cto, pm, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-principles, GUIDE-14-architecture]
---

# Phase 1: Discovery

**Goal:** understand the problem and decide whether to build at all. **Accountable:** the business owner.
**Follows:** UK GDS discovery (restate the solution as a problem, size the cost of the problem, stopping is not
failure), 18F buy versus build, four PMBOK 7 domains (stakeholders, planning, measurement, uncertainty).

## Deliverables

| Deliverable | Template | Owner |
|---|---|---|
| Discovery brief: problem, evidence, cost of the problem, options | [Discovery brief](../templates/discovery-brief.md) | Tech lead and orchestrator agent draft; business owner reviews |
| Project charter: product goal, success metric, appetite, tolerances, out of scope | [Project charter](../templates/project-charter.md) | Business owner |
| Stakeholder map and RACI | [Stakeholder map and RACI](../templates/stakeholder-raci.md) | Tech lead |
| First RAID log | [RAID log](../templates/risk-register.md) | Orchestrator agent |
| Cost sheet v0, with the monthly running cost of the Dev skeleton | [Cost sheet](../templates/cost-sheet.md) | Tech lead |
| Buy-versus-build note, vendor comparison when buying | [Vendor selection](../templates/vendor-selection.md) | Tech lead |
| First data look and privacy screening | Section 4 of the discovery brief | Tech lead |

## Gate G1: go / no-go

Rate each line red, amber or green. The business owner signs.

| # | Question |
|---|---|
| 1 | Is the problem backed by evidence, with its source? |
| 2 | Is one success metric defined, with a baseline and a target? |
| 3 | Is the appetite set in sessions and USD? |
| 4 | Which shape is it: a new app, a module of an existing app, or an API client of one? |
| 5 | Was "stop" a real option, and is the no-go case written down? |
| 6 | Privacy screening: personal data classes, countries, where the data lives, lawful basis per purpose, and whether a full impact assessment is needed |
| 7 | Is the monthly running cost of the Dev skeleton quoted ([adoption](adoption.md), running cost)? |
| 8 | Are the tolerances in the charter filled in? |

## Common mistakes

- Starting with a solution ("we need a CRM") instead of the problem it solves.
- No baseline for the success metric, so success can never be shown.
- Treating the build cost as the whole cost; the monthly running cost is quoted at G1 too.
- Skipping the privacy screening because the product "only stores a few fields".
- Letting discovery run open-ended: give it an appetite of its own.

## How AA does it

The ADR 0008 decision gate (new app, module or API client) and research notes in `docs/research/` play the discovery
role; see the [AA profile](aa-profile.md).
