---
id: TPL-01-release-checklist
title: Release checklist
description: What a change must pass from merge to verified live - the Definition of Done as one checklist, by quality area.
type: template
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 180
related: [TPL-01, TPL-01-dor, skill/aa-ship/SKILL.md]
---

# Release checklist

The generic form of the Definition of Done (new-project playbook, phase 6 Release, gate G6). AA's own procedure, with
its tools and commands, is the skill `skill/aa-ship/SKILL.md`. Copy the list into the PR or the release issue and tick
it with evidence; an unticked line is either done or written as "n.a.: <why>".

## Before merge

- [ ] Every check is green, not only the required ones; nothing pending.
- [ ] A risky class (auth or permissions, migration or schema, CI or secrets, data deletion) had an independent review.
- [ ] Docs impact done in the same PR: `CONTEXT.md`, ADR, runbook, contract, catalog page.
- [ ] Cost: a new paid item is quoted and has its own yes; tags set on new resources.
- [ ] AI change: prompt or model version bumped; eval regression green; AI use register row updated.
- [ ] PR title reads as a changelog line; the body says how to roll back.

## Deploy

- [ ] No job or batch run is open that the deploy would break (deploy gate green).
- [ ] Migrations applied in order through CI: expand before the code that needs it, contract after.
- [ ] Feature flags set to their release state on purpose; fail-closed flags set off before the code lands.
- [ ] Rollout completed; every service of the app runs the same commit.

## Verified live (Done)

- [ ] `/health` returns the new commit SHA; `/health/ready` is green.
- [ ] The changed endpoint or page answers with the expected shape on the live environment (command and output kept).
- [ ] UI checked at desktop and phone width, light and dark, no console error, when the change is visible.
- [ ] Evidence posted on the tracker issue; the issue is closed by hand only now.

## Quality areas (ISO/IEC 25010:2023), when relevant

| Area | Question for this release |
|---|---|
| Functional suitability | Does it do what the Done-when says, and nothing it should not? |
| Performance efficiency | Any new slow query, N+1 call or large payload? |
| Compatibility | Do old clients and contract consumers still work? |
| Interaction capability | Clear UI text, keyboard and screen-reader basics, phone width? |
| Reliability | Retries, timeouts, idempotency, alarms for the new path? |
| Security | ASVS level 1 items of the touched area checked? |
| Maintainability | Code health and coverage did not drop? |
| Flexibility | Thresholds as settings, not constants? |
| Safety | Can a wrong value harm a person, money or data, and what stops it? |

## Tell the business

- [ ] A business-facing release note for verified work only, in the business owner's language.
