---
id: GUIDE-14-scale
title: "Phase 8: Scale"
description: Grow only when a measured trigger says so, cheapest lever first, and switch on the prod controls at gate G7.
type: how-to
status: draft
owner: nghiep
audience: [owner, cto, engineer, devops]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-operate, GUIDE-14-principles]
---

# Phase 8: Scale

**Goal:** grow only when a measured trigger says so, cheapest lever first. **Accountable:** the business owner, because
the phase exists to approve new spend; the tech lead designs the change. **Follows:** Google SRE (SLOs and error budget
policy), the FinOps "cheapest lever first" habit, startup-scale environment models (two environments until a trigger).

## Triggers

Write a trigger table early; act only when a row fires.

| Trigger (measured) | Example threshold | First lever (cheapest) | Next lever |
|---|---|---|---|
| Database CPU or connections | sustained above 70 % for a week | fix the top queries; a connection pooler | a larger instance |
| Queue or job backlog | oldest job older than its window, daily | tune worker concurrency | another worker task |
| Latency SLO at risk | error budget below 25 % | cache, index, payload size | scale out |
| Cost per unit rising | unit cost up 30 % month on month | remove waste found in the review | change the architecture |
| First prod release or first paying tenant | a date is set | switch on the prod controls below | - |

## Gate G7: switch on the prod controls

Written during the dev phase, switched on together when the first prod release or the first paying tenant is dated
(kit decision D10):

- [ ] SLO and error budget policy active ([template](../templates/slo-error-budget.md)).
- [ ] On-call and incident contacts set; alarms route to a person, not only to e-mail.
- [ ] Code owners enforced on risky paths; the tech lead approves risky merges before they land.
- [ ] The agent runs with a least-privilege role, not an admin profile.
- [ ] A prod environment in its own account, built from the prod blueprint, with its own budget.
- [ ] Secrets rotated that were exposed or shared during the dev phase.

## Deliverables

- Trigger table and capacity review ([cost and capacity review](../templates/cost-report.md)).
- Prod blueprint (environments, accounts, data residency, backups and restore targets).
- The governance switch above, recorded as a decision with its date.

## Common mistakes

- Scaling on a feeling or a single spike.
- Buying a bigger instance before fixing the top query.
- Switching prod controls on one by one, so the team never knows which rules apply.
- Building prod before a go-live date exists.
