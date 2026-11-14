---
id: GUIDE-14-release
title: "Phase 6: Release"
description: Get changes to Dev (later prod) and prove them live - deploy order, the Definition of Done, release notes and common mistakes.
type: how-to
status: draft
owner: nghiep
audience: [owner, engineer, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-test, GUIDE-14-operate, TPL-01-release-checklist]
---

# Phase 6: Release

**Goal:** changes reach Dev (later prod) and are proven live. **Accountable:** the tech lead; the business owner is
informed. **Follows:** Scrum (Definition of Done), ITIL 4 (a green PR under the merge rights rule is a standard change;
no change board), trunk-based development, semantic versioning with release-please.

Merged and green is not done. A change is done when it runs on the live environment and a check shows the right result.

## Deliverables

| Deliverable | Template |
|---|---|
| Release checklist ticked with evidence | [Release checklist](../templates/release-checklist.md) |
| Migrations applied in order through CI | [Migration file](../templates/migration-file.md) |
| Flags set to their release state on purpose | Project's flag register |
| Post-deploy verify output and a "verified live" comment on the issue | Release checklist, "Verified live" |
| Release note with verified work only | [Release note](../templates/release-note.md) |
| Business update in the business owner's language | Release note, business part |

## Deploy order

1. Expand migration first, applied by the CI migrate workflow.
2. Code that works with both the old and the new shape.
3. Flags flipped when the code is live everywhere.
4. Contract migration only after every reader has moved.

The deploy waits while a job or batch run is open that it would break (a deploy gate in CI). A rollback is the previous
immutable image, never a rebuild.

## Gate G6: Definition of Done, verified live

| # | Question |
|---|---|
| 1 | Merged with every check green? |
| 2 | Rollout completed, every service of the app on the same commit? |
| 3 | `/health` returns the new commit SHA and `/health/ready` is green? |
| 4 | The changed endpoint or page returns the expected shape on the live environment, with the command and output kept? |
| 5 | UI checked when the change is visible? |
| 6 | Evidence posted on the issue, and the issue closed by hand only now? |

## Merge rights by phase

| Phase | Who merges |
|---|---|
| Dev phase (no prod, no paying tenant) | The orchestrator agent merges its own PRs after green CI; risky classes after an independent agent review. Subagents never merge |
| From the first prod or first paying tenant (gate G7) | The tech lead approves IaC and IAM, migration, auth and security, and data-deletion PRs before merge; other PRs as before |

## Common mistakes

- Closing the issue on merge, before the live check.
- A release note that lists merged work that was never verified.
- Deploying while a long job runs, and corrupting its batch.
- Rebuilding an image for a rollback instead of redeploying the previous tag.
