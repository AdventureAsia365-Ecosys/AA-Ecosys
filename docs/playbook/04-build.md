---
id: GUIDE-14-build
title: "Phase 4: Build"
description: Turn small, ready issues into reviewed changes - the Definition of Ready, delivery paths, appetite, lanes and common mistakes.
type: how-to
status: draft
owner: nghiep
audience: [engineer, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-test, GUIDE-14-agents, TPL-01-dor]
---

# Phase 4: Build

**Goal:** small, ready issues turned into reviewed changes. **Accountable:** the tech lead. **Follows:** Kanban
(visualise, limit WIP, manage flow), Shape Up (appetite, circuit breaker), trunk-based development, Scrum (Definition
of Done). No sprints: one ordered queue, sessions pull from the top.

## Gate G4, per issue: Definition of Ready

Work starts only when the issue passes the [Definition of Ready](../templates/definition-of-ready.md): problem with
evidence, goal, scope with "out", 3 to 6 Done-when lines checkable on the real environment, how to verify, risk class,
dependencies, docs impact, cost, **path** and **appetite**.

## Paths

The path decides how much process an issue gets, so a typo fix does not pay for a feature's ceremony.

| Path | When | Stages and artifacts | Review |
|---|---|---|---|
| `fix` | A defect with a known symptom | Failing test first, then the fix; short implementation note | CI; one lens (correctness) |
| `small` | No new contract, table or page | Implementation note | CI; one lens |
| `feature` | New behaviour users see | Plan section at the top of the implementation note, then build; UI check when visible | CI; correctness lens |
| `risky` | Auth or permissions, migration or schema, CI or secrets, data deletion | As `feature`, plus the independent review before merge | CI; correctness plus security and data lenses |

## Deliverables

- Changes on short branches or worktrees from the latest main; conventional commit subjects; the issue key in the body.
- An [implementation note](../templates/implementation-note.md) per issue, written while working: Plan, Decisions,
  Changed, Tradeoffs, Should know.
- Migrations through expand / contract ([migration template](../templates/migration-file.md)).
- Contracts updated with samples ([contract template](../templates/contract.md)).
- Settings rows for any new threshold ([settings entry template](../templates/settings-entry.md)); flag register rows
  for any new flag.
- A lesson line whenever a root cause is found, with the guard that will stop it next time.

## Flow rules

- At most 8 issues In Progress. Finish before starting: an issue that has stalled is closed with evidence, finished,
  or returned to the backlog with the reason.
- Over the appetite: stop, re-shape or split (circuit breaker). Do not keep going silently.
- Done-when is frozen once the issue is In Progress; new scope becomes a new linked issue.
- One issue is one deliverable slice: about one PR or a small group of PRs.

## Common mistakes

- Starting from an issue whose Done-when says "code merged".
- A `fix` without a failing test, so the same bug can return unseen.
- A diff that touches files the Plan never named, with no Plan update.
- Literal thresholds in code instead of settings.
- Writing the implementation note at the end, from memory.
