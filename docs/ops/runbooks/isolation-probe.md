---
id: OPS-11
title: Run and read the DB isolation probe
description: How to run the read-only DB Isolation Probe that proves each app's database roles are isolated, and what to do with a failing cell.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-infra, aa-cis-dev-db]
last_reviewed: 2026-10-28
review_every_days: 90
last_tested: 2026-10-19
tested_where: dev-acc2
tested_evidence: AA-CIS-Infra Actions run 39196200689 (DB Isolation Probe, success, 2026-10-19 03:45 UTC)
related: [OPS-05-db-migrate, OPS-05, docs/database/schema-ownership.md, AA-852, AA-860]
---

# Run and read the DB isolation probe

Source of truth: AA-CIS-Infra `.github/workflows/db-isolation-probe.yml` (header) and `db/isolation_probe.py`.

## What it proves

A one-off migrator task logs in **as each runtime role with its own DSN secret** (`aa_app_user`, `booking`,
`tripplanner`, `cis_app`, `crm_app` once its password is set, and whatever DB secret the running CIS api task
definition injects). It works in read-only transactions that are rolled back. The catalog reads use the task's own
login, `db_migrator` since X1 S22. It checks: role attributes and memberships, owned objects, connection limits,
cross-app reads refused (42501), schema ownership, runtime grants and default privileges, contract consumer grants,
RLS policy parity for `cis_app`, the `aa_app_user` tenant matrix, the CRM cells (`crm_app` and `crm.job` refused
both ways to and from the other apps), master and `db_migrator` sessions. It prints no row values.

Cells that cannot pass until a later X1 step are `pending`, keyed to live state, so the probe stays green between
applies. The job fails when an expected cell fails (task exit 1) or the probe cannot run (exit 2).

## When it runs

- Nightly at 04:13 UTC (30 minutes after the schema dump).
- After every successful DB Migrate apply or run-script (dispatched with a reason).
- By hand when RLS policies, grants or roles change, or during the quarterly access review (DM-8.10).
- Cost: cents per run (one short Fargate task).

## Steps

1. Run it.

   ```bash
   gh workflow run db-isolation-probe.yml --repo AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f reason="<why>"
   gh run watch -R AdventureAsia365-Ecosys/AA-CIS-Infra $(gh run list -R AdventureAsia365-Ecosys/AA-CIS-Infra --workflow db-isolation-probe.yml -L 1 --json databaseId --jq '.[0].databaseId')
   ```

   Expected: green. The step summary shows "N failing, N pass, N pending, N ready"; `probe.json` is an artifact.
   Rollback: none - read-only.

2. Read a failure. Download `probe.json` (`gh run download <run-id> -R AdventureAsia365-Ecosys/AA-CIS-Infra`) and
   find the cells with `FAIL`. Each cell names the role, the object and the expected result.
   - A cross-app read that succeeded (expected 42501): **SEV1 candidate** - an app can read another app's data. Stop
     merges to the repo that last changed grants; [incident response](../incident-response.md).
   - A runtime role that gained an attribute or membership: revert the migration's intent with a forward migration.
   - `ready` cells: a pending step's key became true; the next X1 step can proceed.

3. Record: in an access review or after an X1 step, paste the summary line into the issue and keep `probe.json` in
   `docs/audits/<date>-S<nnn>-<slug>/`.

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-10-19 | dev-acc2 | S243 main session (dispatch) | AA-CIS-Infra run 39196200689 | success |
| 2026-10-18 | dev-acc2 | Claude Code | S242 session log: 39 pass / 16 pending / 0 fail | pass |
