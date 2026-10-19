---
id: OPS-03-schema
title: Restore one schema or table from a point-in-time copy
description: Bring back lost or damaged rows of one app's schema from a temporary PITR copy, without rolling back the other apps on the shared instance.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-dev-db]
last_reviewed: 2026-10-19
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: [OPS-03-pitr, OPS-05-db-migrate, OPS-03-drills, AA-829, AA-892]
---

# Restore one schema or table from a point-in-time copy

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> The rehearsal is the open part of AA-829 (U-20). Only the PITR half ([restore-rds-pitr](restore-rds-pitr.md)) has
> been drilled.
<!-- callout break -->
> [!CAUTION]
> This writes production-shaped data back into the live shared instance. It follows the DRY RUN procedure
> (`skill/aa-cis-schema/references/destructive-ops.md`): counts first, Nghiệp's OK, then the write.

## When to use

- One app lost or corrupted rows (a bad script, a bad migration, a bug) and a forward fix cannot rebuild them.
- DM-9.4: the shared instance is **never** restored in place for one app's mistake unless every owner agrees.
- Not for: structure mistakes (write a forward migration), or rows that the app can rebuild (re-run the job instead).

## Approach

The container image has no `pg_dump`/`psql`, and no bastion is kept (DM-8.8). Two zero-cost options:

| Option | How | Use when |
|---|---|---|
| A. Reviewed copy script (preferred) | A `db/scripts/<name>.py` in AA-CIS-Infra, run by [DB Migrate run-script](db-migrate.md) as the master: it opens a second connection to the temporary instance with the same master credentials, reads the affected rows (`COPY ... TO` into memory or `SELECT`), and writes them into the live tables inside one transaction (`INSERT ... ON CONFLICT DO NOTHING` or `UPDATE` by primary key) | A bounded set of tables and rows (thousands, not millions), within the 30-minute run-script ceiling |
| B. One-off `pg_dump` task | A one-off Fargate task from the public `postgres:15` image in the migrator's subnets and security group, `pg_dump --schema <s>` from the copy and `pg_restore --data-only` into a staging schema on the live instance, then a reviewed script moves rows | A whole schema or large tables. Needs Nghiệp's approval: it creates a task definition and touches IAM |

Both read only from the copy; the live write is a separate, reviewed step.

## Preconditions

- The restore point is known (just before the damage) and inside the 7-day PITR window.
- The owning app is told and, if its jobs touch the tables, its job table is idle (DB Migrate idle check enforces it).
- Cost: under 1 USD (temporary micro instance for about an hour).

```bash
aws sts get-caller-identity --profile aa365-admin
```

Expected: the acc2 account from the [account map](../../onboarding.md#account-map).

## Steps

1. Restore a copy to the point just before the damage: [restore-rds-pitr](restore-rds-pitr.md) steps 1-3 with
   `--restore-time <ISO-8601 UTC>` (not latest).
   Expected: `aa-cis-dev-db-drill-<yyyymmdd>` available.
   Rollback: delete the copy (restore-rds-pitr step 5).

2. DRY RUN (read-only script, `READ_ONLY = True`): for each affected table, count the rows in the copy, in live, and
   the rows that would be inserted or updated (by primary key). Print counts only, never row values.
   Expected: numbers that match the damage report.
   Verify: Nghiệp reads the counts and says OK in the issue.
   Rollback: none - read-only.

3. Snapshot the live instance by hand (run-script takes none).

   ```bash
   aws rds create-db-snapshot --db-instance-identifier aa-cis-dev-db --db-snapshot-identifier aa-cis-dev-db-pre-restore-<yyyymmdd> --profile aa365-admin --region us-west-1 --query "DBSnapshot.Status" --output text # WRITE
   aws rds wait db-snapshot-available --db-snapshot-identifier aa-cis-dev-db-pre-restore-<yyyymmdd> --profile aa365-admin --region us-west-1
   ```

   Expected: `creating`, then available. Manual snapshots expire after 30 days unless named `keep-…` or tagged
   `aa:retain=keep` / `aa:retain-until=YYYY-MM-DD` (snapshot-expiry Lambda, AA-869).
   Rollback: none needed.

4. Write: the reviewed copy script (option A) merged on Infra `main`, then DB Migrate `mode=run-script`. All tables in
   one transaction; the script re-counts inside the transaction and raises (rolls back) when the counts differ from the
   DRY RUN.
   Expected: `SCRIPT` lines with the same counts as step 2.
   Verify: step 5.
   Rollback: the transaction rolls back on any error. After COMMIT, restore the affected rows from the step 3
   snapshot the same way.

5. Verify independently: a new connection (a second read-only script, or a CIS [ECS exec](ecs-exec-s3-mediated.md)
   query for CIS schemas) counts the rows again; the owning app's health and the affected pages work.

6. Delete the copy (restore-rds-pitr step 5). Keep the step 3 snapshot until the app owner confirms.

## Verify the result

- Counts match the DRY RUN, the app works, the copy is deleted, the evidence (counts, times, script run IDs) is in
  `docs/audits/<date>-S<nnn>-restore/`.

## Roll back or abort

- Before step 4 nothing live has changed: delete the copy and stop.
- After step 4: the step 3 snapshot is the way back for the touched tables.

## Escalation

- Data loss is SEV1 if a tenant or customer sees it ([incident response](../incident-response.md)). Personal data
  involved: Ms. Thư decides with the lawyer on notice duties (Dev holds test data only, D-01).

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| - | - | - | - | not run yet (AA-829 rehearsal) |
