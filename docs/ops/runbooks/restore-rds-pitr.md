---
id: OPS-03-pitr
title: Restore the shared RDS to a point in time
description: Restore aa-cis-dev-db to a new temporary instance with point-in-time recovery, check it schema by schema, and delete it; the basis of the restore drill and of a single-schema restore.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [aa-cis-dev-db]
last_reviewed: 2026-10-19
review_every_days: 90
last_tested: 2026-10-17
tested_where: drill
tested_evidence: docs/audits/2026-10-17-S241-restore-drill/
related: [OPS-03, OPS-03-schema, OPS-03-drills, OPS-05, AA-829, AA-892]
---

# Restore the shared RDS to a point in time

## When to use

- The restore drill (DM-9.3): on Dev when this procedure changes and once before prod; quarterly from prod.
- First half of a [single-schema restore](restore-schema.md) after data loss in one app (DM-9.4).
- Not for: replacing the live instance. An in-place restore of the shared instance rolls back all three apps; it
  needs every owner's agreement (DM-9.4) and a DSN cutover that does not exist yet (DM-9.5 CNAME, AA-829).

## Facts (read 19/10/2026)

- `aa-cis-dev-db`: PostgreSQL 15, `db.t4g.small`, single-AZ, encrypted, deletion protection on, automated backups
  **7 days** (PITR window), backup window 03:00-04:00 UTC, subnet group `aa-cis-dev-db-subnet-group`, parameter
  group `aa-cis-dev-pg15`, one security group (`aa-cis-dev-sg-rds`). `LatestRestorableTime` trails now by about
  5 minutes.
- Drill on 17/10/2026: restore started 08:21:59Z, available 08:39:17Z, checked 08:43:37Z, about **22 minutes** end to
  end against the Dev target RTO < 1 h (C1.2). 148/148 tables, migration heads equal; 18 Booking and 25 shared rows
  differed, all written after the restore point.
- Cost: a `db.t4g.micro` for under an hour, well under 1 USD.

## Preconditions

- Access: profile `aa365-admin` with an MFA session.
- The temporary instance name is free: `aa-cis-dev-db-drill-<yyyymmdd>`.

```bash
aws sts get-caller-identity --profile aa365-admin
```

Expected: the acc2 account from the [account map](../../onboarding.md#account-map).

## Steps

1. Read the restore window (read-only).

   ```bash
   aws rds describe-db-instances --db-instance-identifier aa-cis-dev-db --profile aa365-admin --region us-west-1 --query "DBInstances[0].{latest:LatestRestorableTime,retention:BackupRetentionPeriod,sng:DBSubnetGroup.DBSubnetGroupName,pg:DBParameterGroups[0].DBParameterGroupName}" --output table
   ```

   Expected: retention 7; the restore time you want is inside the last 7 days and before `latest`.
   Rollback: none - read-only.

2. Look up the RDS security group ID (IDs stay out of docs).

   ```bash
   SG=$(aws ec2 describe-security-groups --filters Name=group-name,Values=aa-cis-dev-sg-rds --profile aa365-admin --region us-west-1 --query "SecurityGroups[0].GroupId" --output text)
   ```

   Expected: `$SG` starts with `sg-`.
   Rollback: none - read-only.

3. Restore to a new instance. Use `--restore-time <ISO-8601 UTC>` for an exact point, or
   `--use-latest-restorable-time`.

   ```bash
   aws rds restore-db-instance-to-point-in-time --source-db-instance-identifier aa-cis-dev-db --target-db-instance-identifier aa-cis-dev-db-drill-<yyyymmdd> --use-latest-restorable-time --db-instance-class db.t4g.micro --db-subnet-group-name aa-cis-dev-db-subnet-group --vpc-security-group-ids $SG --db-parameter-group-name aa-cis-dev-pg15 --no-publicly-accessible --no-multi-az --no-deletion-protection --tags Key=App,Value=shared Key=Environment,Value=dev Key=Purpose,Value=restore-drill --profile aa365-admin --region us-west-1 --query "DBInstance.DBInstanceStatus" --output text # WRITE
   aws rds wait db-instance-available --db-instance-identifier aa-cis-dev-db-drill-<yyyymmdd> --profile aa365-admin --region us-west-1
   ```

   Expected: `creating`, then the wait returns (about 17 minutes in the drill). Note both times for the RTO.
   The S241 drill used the same settings (micro class, same subnet group and security group); this exact command
   line was written from them on 19/10/2026 and has not been pasted as-is yet. Tags follow DM-10.1 (`App` +
   the existing `Environment`, same values as the source instance).
   Verify: `aws rds describe-db-instances --db-instance-identifier aa-cis-dev-db-drill-<yyyymmdd> --profile aa365-admin --region us-west-1 --query "DBInstances[0].[DBInstanceStatus,Endpoint.Address]" --output text`
   shows `available` and an endpoint.
   Rollback: step 5 (delete the copy).

4. Compare the copy with the source, per schema: table count, row count per table, latest
   `shared.schema_versions`. The drill used `docs/audits/2026-10-17-S241-restore-drill/drill_check.py` through
   [ECS exec](ecs-exec-s3-mediated.md), with the master login read from the secret.
   - Until X1 S19 that still works.
   - **From X1 S19 the CIS task role cannot read the master secret**, and `cis_app` cannot read `booking.*` /
     `tripplanner.*`. Run the comparison as a reviewed **read-only** `db/scripts/` file through
     [DB Migrate run-script](db-migrate.md). The migrator task holds the master DSN; the script connects a second time
     with the same credentials and the drill host. This variant is UNTESTED.

   Expected: equal table counts, equal migration heads, row differences only in tables written after the restore point.
   Verify: save the JSON output in `docs/audits/<date>-S<nnn>-restore-drill/` (DM-8.10, C7.2b).
   Rollback: none - read-only.

5. Delete the temporary instance (no final snapshot; it is a copy).

   ```bash
   aws rds delete-db-instance --db-instance-identifier aa-cis-dev-db-drill-<yyyymmdd> --skip-final-snapshot --delete-automated-backups --profile aa365-admin --region us-west-1 --query "DBInstance.DBInstanceStatus" --output text # WRITE
   aws rds wait db-instance-deleted --db-instance-identifier aa-cis-dev-db-drill-<yyyymmdd> --profile aa365-admin --region us-west-1
   ```

   Expected: `deleting`, then the wait returns.
   Verify: `aws rds describe-db-instances --profile aa365-admin --region us-west-1 --query "DBInstances[].DBInstanceIdentifier" --output text`
   lists only `aa-cis-dev-db`.
   Rollback: none (it was a copy). Double-check the identifier before running: never the source name.

## Verify the result

- The evidence folder holds the compare JSON, the start, available and checked times, and the RTO against < 1 h.
- No `aa-cis-dev-db-drill-*` instance is left running.
- AA-829 gets a comment with the numbers; the [drills index](../drills/README.md) gets a row.

## Roll back or abort

- At any point, step 5 removes the copy. The source instance is never written by this runbook.

## Escalation

- A drill that fails (missing tables, migration head mismatch, RTO over 1 h) is a SEV3 finding with an issue. A real
  data loss is SEV1: [incident response](../incident-response.md).

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-10-17 | drill (Dev acc2) | Claude Code (main session) + Nghiệp | `docs/audits/2026-10-17-S241-restore-drill/`, S241 decisions D-10, AA-829 comment | pass, ~22 min |
| 2026-10-19 | dev-acc2, step 1 only | Claude Code | `docs/audits/2026-10-19-S243-ops-runbooks/readonly-checks.md` | read-only |
