---
id: GUIDE-14-operate
title: "Phase 7: Operate"
description: Keep the product running, learn from every failure and watch the cost - periodic reviews, incidents, runbooks and common mistakes.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-release, GUIDE-14-scale, GUIDE-14-metrics]
---

# Phase 7: Operate

**Goal:** keep it running, learn from every failure, watch the cost. **Accountable:** the tech lead. **Follows:**
Google SRE (blameless postmortems with triggers), ITIL 4 (light incident management), FinOps Framework (inform,
optimise, operate at crawl / walk), DORA (delivery metrics).

There is no permanent gate in this phase: the periodic reviews are the control.

## Deliverables

| Deliverable | Template | Cadence |
|---|---|---|
| Alarms, each linked to a runbook | [Runbook](../templates/runbook.md) | per alarm |
| Incident records | [Incident record](../templates/incident-record.md) | per incident |
| Postmortems | [Postmortem](../templates/postmortem.md) | when a trigger applies |
| Drills of the runbooks that matter (restore, rollback, break-glass, secret rotation) | Runbook with `last_tested` | on a procedure change, and before prod |
| Delivery metrics report | [Delivery metrics report](../templates/delivery-metrics-report.md) | weekly |
| Cost and capacity review | [Cost and capacity review](../templates/cost-report.md), [cost sheet](../templates/cost-sheet.md) | monthly |
| Access review | [Access review](../templates/access-review.md) | quarterly |
| Lessons turned into guards | Project's lesson log | at root-cause time |

## Rules

- A runbook that has not been run is marked untested and is not trusted in an incident.
- A lesson that a machine can check becomes a test, a lint rule, a hook or a CI step; then the lesson line is retired.
- Every alarm has a runbook; an alarm nobody acts on is deleted or fixed.
- Cost has one source of truth per kind (cloud bill, model ledger); a report states which.

## Review calendar

| Review | Inputs | Output |
|---|---|---|
| Weekly delivery | Git, deploy runs, incidents, tracker | Delivery metrics report |
| Monthly cost and capacity | Bill by tag and service, ledger by stage, database and queue sizes | Cost and capacity review with decisions |
| Quarterly access | Code host, cloud roles, identity users, database roles, secret readers | Access review with findings |
| 90-day playbook retro | This playbook, the instructions, the ADRs | Prune pass; playbook issues raised |

## Common mistakes

- Treating a green dashboard as proof when the probe behind it is stale.
- Writing a postmortem that names a person instead of the missing guard.
- Letting untested runbooks pile up until the incident that needs one.
- Reading cost from two sources that disagree without saying which wins.
