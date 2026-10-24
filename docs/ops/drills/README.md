---
id: OPS-03-drills
title: Drill index
description: Every restore and rollback drill run on the ecosystem, with links to its evidence in docs/audits; this page holds no evidence itself.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-24
review_every_days: 90
related: [OPS-02-cis, OPS-03-pitr, OPS-03-schema, OPS-01, AA-829, AA-869]
---

# Drill index

Evidence (command output, JSON, times) lives in `docs/audits/<date>-S<nnn>-<slug>/` (DM-8.10, C7.2b). This page only
lists the runs. Cadence (DM-9.3): on Dev, re-run a drill when its procedure changes and once before prod; quarterly from
prod. A `last_tested` older than the review window on Dev is a warning, not an order to re-run.

| Date | Drill | Runbook | Result | RTO / duration | Evidence |
|---|---|---|---|---|---|
| 2026-10-17 | Full PITR restore of `aa-cis-dev-db` to a temporary instance, compare per schema, delete | [restore-rds-pitr](../runbooks/restore-rds-pitr.md) | pass: 148/148 tables, migration heads equal, row differences only after the restore point | about 22 min (target < 1 h, C1.2) | [`audits/2026-10-17-S241-restore-drill/`](../../audits/2026-10-17-S241-restore-drill/), S241 decisions D-10, AA-829 comment |
| 2026-10-24 | PITR restore to a point between two marked writes, compare, **single-schema restore (option A)**, **repoint `db.dev.internal` to the copy and back** (4 services redeployed each way), delete | [restore-rds-pitr](../runbooks/restore-rds-pitr.md), [restore-schema](../runbooks/restore-schema.md) | pass: 164/164 tables, heads equal; 40/40 rows restored; services ran on the copy (readiness refused the copy where its schema was older); back on live with no Terraform drift | restore 21 min 20 s; repoint ~40 s + ~3 min redeploy each way | [`audits/2026-10-24-S249-restore-drill/`](../../audits/2026-10-24-S249-restore-drill/), AA-829 |
| 2026-10-17 | CIS api + worker rollback two revisions back to an older image, `/health` 200, then forward again | [rollback-cis](../runbooks/rollback-cis.md) | pass | minutes (not timed) | S241 session log (AA-869) |

## Not drilled yet

| Runbook | Blocker or next step |
|---|---|
| [rollback-booking](../runbooks/rollback-booking.md), [rollback-vercel](../runbooks/rollback-vercel.md), [rollback-tp-lambda](../runbooks/rollback-tp-lambda.md), [rollback-terraform](../runbooks/rollback-terraform.md) | once each before prod (DM-9.3); cost 0 USD |
| [break-glass](../runbooks/break-glass.md) via managed login | AA-816 open item |
| [legacy-login-flag](../runbooks/legacy-login-flag.md) | the AA-816 cutover itself |
