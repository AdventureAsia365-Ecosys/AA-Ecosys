---
id: OPS-03-drills
title: Drill index
description: Every restore and rollback drill run on the ecosystem, with links to its evidence in docs/audits; this page holds no evidence itself.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-17
review_every_days: 90
related: [OPS-02-cis, OPS-02-ecs, OPS-03-gameday, OPS-03-pitr, OPS-03-schema, OPS-03-tabletop, OPS-01, OPS-01-no-agent, AA-829, AA-869, AA-1023, AA-1110]
---

# Drill index

Evidence (command output, JSON, times) lives in `docs/audits/<date>-S<nnn>-<slug>/` (DM-8.10, C7.2b). This page only
lists the runs. Cadence (DM-9.3): on Dev, re-run a drill when its procedure changes and once before prod; quarterly from
prod. A `last_tested` older than the review window on Dev is a warning, not an order to re-run.

Two kinds of run count differently. **Agent-run**: an agent ran the steps (often with a helper script) while the tech
lead watched. **Runbook-only**: a person other than the agent followed the page alone. Only a runbook-only run proves
that the platform can be run without the agent ([run without the agent](../run-without-agent.md)).

| Date | Drill | Runbook | Result | RTO / duration | Evidence |
|---|---|---|---|---|---|
| 2026-10-17 | Full PITR restore of `aa-cis-dev-db` to a temporary instance, compare per schema, delete | [restore-rds-pitr](../runbooks/restore-rds-pitr.md) | pass: 148/148 tables, migration heads equal, row differences only after the restore point | about 22 min (target < 1 h, C1.2) | [`audits/2026-10-17-S241-restore-drill/`](../../audits/2026-10-17-S241-restore-drill/), S241 decisions D-10, AA-829 comment |
| 2026-10-24 | PITR restore to a point between two marked writes, compare, **single-schema restore (option A)**, **repoint `db.dev.internal` to the copy and back** (4 services redeployed each way), delete | [restore-rds-pitr](../runbooks/restore-rds-pitr.md), [restore-schema](../runbooks/restore-schema.md) | pass: 164/164 tables, heads equal; 40/40 rows restored; services ran on the copy (readiness refused the copy where its schema was older); back on live with no Terraform drift | restore 21 min 20 s; repoint ~40 s + ~3 min redeploy each way | [`audits/2026-10-24-S249-restore-drill/`](../../audits/2026-10-24-S249-restore-drill/), AA-829 |
| 2026-10-17 | CIS api + worker rollback two revisions back to an older image, `/health` 200, then forward again | [rollback-cis](../runbooks/rollback-cis.md) | pass | minutes (not timed) | S241 session log (AA-869) |
| 2026-11-02 | Rollback game day, agent-run: Booking API and CRM API back one build and forward (`tools/ops/ecs_rollback.sh`), the Booking admin on Vercel (since retired), Lambda `aa-tripplanner-dev-browse` (path B), the terraform-apply job-idle gate | [rollback-ecs](../runbooks/rollback-ecs.md), [rollback-tp-lambda](../runbooks/rollback-tp-lambda.md), [game day plan](rollback-game-day.md) | pass, 5/5; finding: the helper reported `IN_PROGRESS` once before ECS reached `COMPLETED` | back 150 s / 166 s (ECS), 11 s (Lambda) | [`audits/2026-11-02-S264-rollback-game-day/`](../../audits/2026-11-02-S264-rollback-game-day/README.md), AA-1023 |

## Not drilled yet

| Runbook or drill | Blocker or next step |
|---|---|
| Runbook-only deploy and rollback: a person follows [run without the agent](../run-without-agent.md) alone (one deploy by merge, one ECS rollback and forward) | AA-1110: needs the second key-holder's tested access ([access register](../../security/access-register.md)) |
| [Security tabletop](security-tabletop.md): leaked secret, cross-agency read, a real `db_migrator` password rotation, the CRM data-key rotation talk-through | AA-1110: one 60-minute sitting with the tech lead, the second key-holder and the business owner |
| [rollback-ecs](../runbooks/rollback-ecs.md), [rollback-tp-lambda](../runbooks/rollback-tp-lambda.md) | agent-run once (2026-11-02, above); never runbook-only; the pages are still `draft` and their tested logs do not list the game day yet |
| [rollback-booking](../runbooks/rollback-booking.md) | never run beyond its read-only steps (the game day used rollback-ecs for Booking) |
| [rollback-terraform](../runbooks/rollback-terraform.md) | once before prod (DM-9.3); cost 0 USD |
| [break-glass](../runbooks/break-glass.md) via managed login | done with the tech lead 2026-10-19 (S244); a run by the second key-holder is part of the access test above |
| [legacy-login-flag](../runbooks/legacy-login-flag.md) | the AA-816 cutover itself |
