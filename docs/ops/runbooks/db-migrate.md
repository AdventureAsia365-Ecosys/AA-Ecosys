---
id: OPS-05-db-migrate
title: Run DB Migrate (check, apply, set-password, run-script)
description: How to apply a reviewed migration, set a role password or run a reviewed master script on the shared RDS through the AA-CIS-Infra DB Migrate workflow.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-infra, aa-cis-dev-db]
last_reviewed: 2026-10-28
review_every_days: 90
last_tested: 2026-10-18
tested_where: dev-acc2
tested_evidence: docs/sessions/2026-10-18-S242-cognito-staff-login-x1-network-dependabot.md (mig 247 apply; X1 S12 set-password and run-script on the migrator task)
related: [OPS-05, OPS-05-ecs-exec, OPS-11, OPS-10-deploy-gate, docs/database/schema-ownership.md, AA-807, AA-852, AA-892]
---

# Run DB Migrate (check, apply, set-password, run-script)

The source of truth for the workflow is AA-CIS-Infra: `.github/workflows/db-migrate.yml` (header comment),
`db/README.md` and `db/scripts/README.md`. This page is the operator's checklist; when they disagree, the
workflow wins and this page gets fixed.

## When to use

- `check` / `apply`: a migration file merged on its owner repo `main` and copied byte-for-byte into AA-CIS-Infra
  `db/migrations/<owner>/` (Migration Copy Guard green, PR merged).
- `set-password`: give `cis_app`, `crm_app` or `db_migrator` the password the tech lead wrote into that role's DSN
  secret (X1; allowlist `password_roles` in `db/owners.yaml`).
- `run-script`: master-level work that is not a migration (another app's data, roles, a fix across owners), as a
  reviewed `db/scripts/<name>.py` on Infra `main`.
- Not for: CIS-scope reads (use [ECS exec](ecs-exec-s3-mediated.md)), or a change that should replay in CI or exist in
  every environment (that is a migration).

## Facts that shape this runbook

- Runs only on Infra `main` (`if: github.ref == 'refs/heads/main'`), in the GitHub environment `prod` (the name is
  historical; ADR 0012 decision 6 renames it to `dev` in phase 1, AA-880, D-16). Concurrency group `db-migrate`, never cancelled.
- The SQL runs in a one-off Fargate task of the migrator family `aa-cis-dev-db-migrate` (container `migrate`,
  security group `aa-cis-dev-sg-db-migrate`), with the image the CIS api runs now. The revision is deregistered at the
  end. Its log is stream `migrate/migrate/<task id>` in `/ecs/aa-cis-dev` and is printed in the job.
- Login: `db_migrator` since X1 S22 (the RDS master before). Each file in an owner directory (`cis/`, `booking/`,
  `tripplanner/`, `crm/`) runs as the live owner of that directory's anchor schema (`db/owners.yaml`). `roles/`
  files, `set-password` and `run-script` use the master DSN, which the task reads itself.
- Every session: `lock_timeout 5s`, `statement_timeout 15min`, `application_name db-migrate`. Header directives:
  `-- migrate: no-transaction`, `lock_timeout=…`, `statement_timeout=…`, `destructive` (the workflow takes a
  manual RDS snapshot first, DM-9.2).
- Idle check: `apply` and a writing `run-script` refuse (exit 7) while any owner job table (`shared.job`,
  `booking.job`, `crm.job`) has a queued or running row of a non-exempt kind (`idle_exempt_kinds` in
  `db/owners.yaml`), or a rerun wave is open. `override_busy_jobs` (one line, a reason, tech lead only) lets one run
  through and is logged. App deploys no longer wait for idle job tables (AA-993 G5); DB Migrate still does.
- A successful `apply` or `run-script` dispatches **DB Schema Dump** (root PR `bot/db-schema-reference`) and
  **DB Isolation Probe**.
- A `cis/` file may change a `catalog.*` view only with the catalog recipe (`SET LOCAL ROLE catalog_owner`, then
  back to `cis_owner` and `REVOKE CREATE`); the lint and the runner refuse it otherwise. The X1 S1-S22 freeze is over.
- Cost: cents per run (one short Fargate task); a `destructive` snapshot is free while it fits the backup quota.

## Preconditions

- The owner repo merged a migration-file-only PR first; code that reads the new objects comes later (S237 D8).
- The Infra copy PR is merged and Migration Copy Guard is green.
- No other DB Migrate run is in progress (`gh run list … --workflow db-migrate.yml -L 3`).

```bash
gh auth status
```

Expected: logged in to github.com with access to `AdventureAsia365-Ecosys`.

## Steps

1. Check (read-only).

   ```bash
   gh workflow run db-migrate.yml --repo AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f environment=dev -f mode=check -f migration=<owner>/<NNN>_<name>.sql
   gh run watch -R AdventureAsia365-Ecosys/AA-CIS-Infra $(gh run list -R AdventureAsia365-Ecosys/AA-CIS-Infra --workflow db-migrate.yml -L 1 --json databaseId --jq '.[0].databaseId')
   ```

   Expected: the summary shows `ran as: <role>`, the version is not registered yet, the latest key of the same owner
   is the previous number, and every job table is idle.
   Verify: lint warnings in the job annotations are understood.
   Rollback: none - read-only.

2. Apply.

   ```bash
   gh workflow run db-migrate.yml --repo AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f environment=dev -f mode=apply -f migration=<owner>/<NNN>_<name>.sql # WRITE
   ```

   Expected: job green; the version key (`NNN`, `bk-NNN`, `tp-NNN`, `crm-NNN`, `rl-NNN`) is in
   `shared.schema_versions`.
   Re-running apply is a no-op.
   Verify: Booking `curl -s https://api-booking.lumiguides.it.com/booking/health/ready` shows the new
   `schema_version`; CIS `curl -s https://api-cis.lumiguides.it.com/health/ready` 200; the Schema Dump PR appears in
   the root repo (merge it by hand) and the Isolation Probe run is green.
   Rollback: migrations do not roll back. Write the inverse as the next migration, through the same flow. Exit 8/9
   (role refused / ownership post-check) roll the transaction back by themselves; a `no-transaction` file can be
   left half applied and unregistered - read the log before re-running.

3. Set a role password (X1).

   ```bash
   gh workflow run db-migrate.yml --repo AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f environment=dev -f mode=set-password -f role=<role> # WRITE
   ```

   `<role>` is `cis_app`, `crm_app` or `db_migrator`.

   Expected: the log prints `current_user` and `rolconnlimit` of a successful test login, never the password.
   Exit 11 = the secret was refused, 12 = the test login failed.
   Rollback: the tech lead writes the previous DSN back into the secret by hand; then run the mode again.

4. Run a reviewed script.

   ```bash
   gh workflow run db-migrate.yml --repo AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f environment=dev -f mode=run-script -f script=db/scripts/<name>.py
   ```

   Expected: the script's `SCRIPT …` lines in the job log; exit 13 = the script raised or returned non-zero.
   A `READ_ONLY = True` script cannot write (SQLSTATE 25006) and only reports the idle check.
   Rollback: `run-script` takes **no** snapshot. Before an irreversible change take one by hand
   (DRY RUN procedure, `skill/aa-cis-schema/references/destructive-ops.md`).

## Verify the result

- The job is green, the version or the script output is in the summary, Schema Dump and Isolation Probe ran.
- After a structure change: the regenerated `docs/architecture/db-schema-reference.md` is merged the same day.

## Roll back or abort

- Abort before `apply` if `check` shows another owner's role, an unexpected registered version or a busy job table.
- After `apply` there is no rollback, only a forward migration; for data loss see
  [restore a single schema](restore-schema.md).

## Escalation

- A failed apply that left objects behind (exit 9 after COMMIT, or a `no-transaction` file): SEV2, stop all merges to
  the owner repo, tell the tech lead. Booking or TripPlanner broken by it: SEV1 ([incident response](../incident-response.md)).

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-10-18 | dev-acc2 | Claude Code (main session) | S242 session log: CIS mig 247 applied; X1 S12 `set-password` and `run-script` on the migrator task | pass |
| 2026-10-17 | dev-acc2 | Claude Code (main session) | S241 session log: X1 S8 apply train (4 files), probe 39/16/0 | pass |
