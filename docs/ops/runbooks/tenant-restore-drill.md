---
id: OPS-03-tenant-restore
title: Restore one tenant's CIS and TripPlanner data from its own backup
description: The one-tenant backup and restore drill of CIS (job tenant_backup, restore_drill into a throwaway schema, counts and checksums compared) and the planned TripPlanner drill; the CRM has its own runbook.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-api, aa-cis-worker, aa-cis-dev-db, tripplanner-lambda]
last_reviewed: 2026-11-13
review_every_days: 90
last_tested: 2026-11-13
tested_where: drill
tested_evidence: docs/audits/2026-11-13-S279-cis-restore-drill/restore-drill.json
related: [OPS-03-pilot-tenant, OPS-03-pitr, OPS-03-schema, OPS-05-ecs-exec, SEC-04-dsar, AA-1093]
---

# Restore one tenant's CIS and TripPlanner data from its own backup

RDS point-in-time recovery restores the whole shared database of all four apps, never one tenant
([Restore the shared RDS to a point in time](restore-rds-pitr.md)). A single tenant is recovered from its own backup:
the CRM from its nightly sealed export ([CRM pilot drill](pilot-tenant-restore-drill.md)), CIS from the `tenant_backup`
job below, and TripPlanner from a job of its own (planned). This page is the drill that proves a CIS backup restores
(AA-1093, gap M27 of the S278 system audit), and the TripPlanner part once it is built. Run the CIS drill before the
pilot agency gets real data, after a CIS release that adds a tenant table, and whenever the tech lead asks.

The **CIS drill passed on Dev on 2026-11-13** for the synthetic tenant `audit-atlas-hearth`: `ok` true, `complete`
true, 77 checksums verified, 76 tables, 1565 rows restored out of 1565 in the manifest
([evidence](../../audits/2026-11-13-S279-cis-restore-drill/restore-drill.json)).

## CIS

### What is in place

| Piece | Where |
|---|---|
| The backup job | CIS job kind `tenant_backup` (AA-CIS-App `services/jobs/tenant_backup_job.py`, logic `services/tenant_backup/`): background, concurrency 1, at most 2 attempts, no paid call. On demand for any tenant; nightly for the pilot tenant only (`shared.tenants.is_pilot`) once the switch `TENANT_BACKUP_PILOT=on` is set on the api task (default off, decision D11) |
| What it copies | Every table of the tenant erasure inventory (`services/erasure/inventory.py`), each read with the tenant's erasure predicate, all in one repeatable-read snapshot. Left out on purpose, each with its reason in the manifest: the cost ledgers the erasure detaches or merges, the append-only audit hash chain, job history, the model reply cache and the per-request API metering. The AA internal tenant (it owns the shared catalogue) is refused: PITR restores it |
| The files | Gold bucket, prefix `exports/tenants/<tenant>/cis/<backup id>/` (backup id = the job id): `tables/<schema>.<table>.jsonl.gz` (one `to_jsonb` row per line), `manifest.json` (format `cis-tenant-backup/1`, schema version, rows, sizes and sha256 per table, restore order) and `SHA256SUMS` written last. The bucket rule `exports-expire` deletes them after 7 days (D11) |
| Size cap | Tables are copied smallest first; a table that would cross the cap is left out whole and listed under `skipped` (the backup is then `complete: false`). The cap is 512 MiB of JSON today |
| The drill | AA-CIS-App `python -m services.tenant_backup.restore_drill` in the CIS **api** container (it has the `cis_app` DSN and reads the gold bucket) |

### 1. Take a backup (or use the nightly one)

Queue one backup from a shell of the CIS api container through the ECS exec wrapper
([Query the database through ECS exec](ecs-exec-s3-mediated.md); orchestrator only). The wrapper runs a script file
with cwd `/app`, so write a two-line starter to `.tmp-session/tenant_backup.py`:

```python
import os, sys
from services.tenant_backup.enqueue import cli
sys.exit(cli(["--tenant", os.environ["TENANT"]] if os.environ.get("TENANT") else ["--wait", os.environ["JOB"]]))
```

Then queue (prints `{"job_id": ..., "created": true}`) and wait for it (prints the status and the result counts;
the worker service runs the job):

```bash
tools/ecs/ecsx.sh .tmp-session/tenant_backup.py TENANT=<tenant uuid>
tools/ecs/ecsx.sh .tmp-session/tenant_backup.py JOB=<job id>
```

Expected: `status` `succeeded`, `complete` true, `skipped` and `unregistered` empty, `sha256sums_sha256` 64 hex
characters. A failed job prints the error code only (never a database message).

### 2. Run the drill

Write the starter `.tmp-session/restore_drill.py`:

```python
import os, sys
from services.tenant_backup.restore_drill import cli
sys.exit(cli([a for k in ("TENANT", "BACKUP") if os.environ.get(k) for a in (f"--{k.lower()}", os.environ[k])]))
```

and run it (the pilot tenant and its newest backup when no variable is given):

```bash
tools/ecs/ecsx.sh .tmp-session/restore_drill.py TENANT=<tenant uuid>
```

Add `BACKUP=<job id>` to drill one given backup. In a shell of the container the same module runs as
`python -m services.tenant_backup.restore_drill [--tenant <uuid>] [--backup <job id>]`.

The drill never writes a live table: it loads every table into a temporary table of its own session (`pg_temp`,
`ON COMMIT DROP`) made from the live table's columns and types, and rolls the whole transaction back at the end. Then
it writes one audit row `tenant.restore_drill` (ids and counts only).

### 3. Read the result

The JSON it prints holds ids, table names, counts and digests, never a value of a row.

| Key | Pass when |
|---|---|
| `ok` | `true`: every digest matched and every table restored as many rows as the manifest lists (exit code 0 or 3) |
| `complete` | `true` (exit code 0). `false` with `ok: true` = exit code 3: the rows restored but the backup itself left a table out (`skipped` by the size cap, or `unregistered`) |
| `checksums_verified` | every table file and the manifest matched their `SHA256SUMS` line, and `SHA256SUMS` matched the digest kept in the job result |
| `manifest_rows` / `restored_rows` | equal; `mismatched_tables` empty |
| `tables[].live_rows`, `live_pk_matched`, `live_identical` | reported only: the tenant may have changed after the backup (`live_differs` names those tables) |
| `excluded` | the tables left out on purpose, with their reason (see "What it copies") |

Exit code 3 before the pilot has real data that matters: tell the tech lead (a larger cap or a split backup is a
design change, not a drill step).

### 4. Failure codes

A failure prints `{"ok": false, "error": "<code>"}` and exits 1 (2 for `not_configured`):

| Code | Meaning | Do |
|---|---|---|
| `no_pilot_tenant` | no tenant is marked pilot and no `--tenant` was given | pass `TENANT=<uuid>` |
| `bad_backup_id` / `no_tenant` | the id given is not a UUID, or the tenant has no row | check the ids |
| `no_backup` | no succeeded `tenant_backup` job of the tenant (or the job id given is not one) | take a backup (step 1) |
| `backup_of_another_tenant` | the job id given belongs to another tenant | use that tenant's job |
| `backup_not_ready` | the job has not succeeded or has no digest | wait for it, or take a new one |
| `object_missing` | a file is gone: the 7-day bucket rule took it | take a new backup |
| `sums_digest_mismatch` / `checksum_mismatch` / `manifest_mismatch` / `checksum_missing_file` / `sums_shape` | the stored copy changed or is incomplete | stop; incident ([incident response](../incident-response.md)) |
| `not_configured` | the container has no `DATABASE_URL` | check the CIS api task definition |
| `unexpected` | anything else: only the error class and SQLSTATE are printed | read `/ecs/aa-cis-dev` for `cis-restore-drill`, fix, run again |

### 5. Record it

Put the JSON and the date in `docs/audits/<date>-S<nnn>-cis-restore-drill/restore-drill.json` and update
`last_tested`, `tested_where` and `tested_evidence` of this page in the same root PR.

### A real one-tenant restore

The drill proves the copy restores; restoring a tenant's rows into the live tables after a loss is a separate decision
of the tech lead, under the DRY RUN procedure of `skill/aa-cis-schema/references/destructive-ops.md` (load the backup
into a scratch schema, compare, then insert parents first in the manifest's restore order). Never run an
instance-wide PITR while the pilot runs without telling the pilot agency first (root ADR 0019 d16). A tenant erased
by the offboarding saga is not restored from its backup: the erasure's manual checklist removes the backup prefix when
the erasure falls inside the backup's 7 days ([DSAR runbook](../../legal/dsar-erasure-runbook.md) section 4).

## TripPlanner

**Planned (AA-1093 L4).** The same shape for TripPlanner's tenant tables (`tripplanner.sessions`,
`tripplanner.trip_drafts`, `tripplanner.trip_events`, `tripplanner.outbox` of one tenant): a job kind
`tp_tenant_backup` in `tripplanner.job`, run by the TripPlanner jobs Lambda, writing JSONL, a manifest and checksums
under the tenant's own prefix, and a `restore_drill` op of the jobs Lambda that loads them into a throwaway schema and
compares counts, with Lambda IAM for that prefix only. This section gets its steps, pass keys and failure codes when
the TripPlanner change ships; until then a TripPlanner tenant is recovered only through PITR.
