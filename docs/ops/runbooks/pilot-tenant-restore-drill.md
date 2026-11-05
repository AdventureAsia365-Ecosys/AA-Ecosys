---
id: OPS-03-pilot-tenant
title: Restore one tenant's CRM data from its nightly export
description: The one-tenant restore drill of the Dev pilot agency (root ADR 0019 d16) - open the newest nightly crm.export_job export, restore every table into a throwaway schema and compare row counts.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-crm-dev-api, aa-cis-dev-db]
last_reviewed: 2026-11-05
review_every_days: 90
last_tested: never
tested_where: none
related: [OPS-03-schema, OPS-03-pitr, OPS-05-ecs-exec, AA-969, AA-1028]
---

# Restore one tenant's CRM data from its nightly export

Root [ADR 0019](../../adr/0019-b2b-only-ecosystem-model.md) d16 runs one real agency (the pilot) on Dev. RDS
point-in-time recovery restores the whole database of all four apps, never one tenant
([Restore the shared RDS to a point in time](restore-rds-pitr.md)), so the pilot agency is recovered from its own
export: AA-Partner's `crm_pilot_backup` job queues one portability export of the pilot agency every night, and this
drill proves that export restores. Run it once before the pilot gets real data, then after every CRM release that adds a
tenant table.

## What is in place

| Piece | Where |
|---|---|
| Pilot marker | CIS `shared.tenants.is_pilot` (CIS 354), projected to `crm.tenant.is_pilot` (crm-044) by `crm_entitlement_pull` |
| Nightly export | `crm_pilot_backup` (daily, from `JOB_RETENTION_UTC_HOUR`), one `crm.export_job` row (`requested_by = job:crm_pilot_backup`) and its `crm_data_export` job |
| The export file | documents bucket `exports/tenants/<tenant>/portability/<export>.zip.enc`, sealed under the agency `export` DEK; the `exports/` bucket rule deletes it after 7 days ([DM-7.1](../../architecture/data-standards/02-data-management.md), row `crm.export_job`) |
| The drill | AA-Partner `python -m app.portability.restore_drill` (in the CRM API container) |
| Clean-up skips the pilot | CIS retention of tenant rows, Booking case-lifecycle clearing and inbox redaction, CRM `crm_lifecycle` and the L1 test-agency delete (AA-969 part 2) |
| No agent reads of the pilot's personal data | root hook `.claude/hooks/pilot-pii-guard.sh`, AA-CIS-Infra run-script guard (`db/scripts/README.md`) |

## Before you start

- [ ] A pilot agency is marked in CIS (`is_pilot`), or you drill another agency with `--tenant <uuid>`.
- [ ] The agency has a `ready` nightly export younger than 7 days. Count only:
      `SELECT count(*) AS n FROM crm.export_job WHERE requested_by = 'job:crm_pilot_backup' AND status = 'ready' AND expires_at > now()`
      run as the agency (the drill itself also says `no_export` when there is none).
- [ ] The CRM API task is not building another export right now (the drill holds the ZIP in the 512 MB task).

## Run the drill

1. Start the drill in the CRM API container through the ECS exec wrapper
   ([Query the database through ECS exec](ecs-exec-s3-mediated.md); it runs a script file with cwd `/app`, local mode on
   CRM containers). Write the three-line starter to `.tmp-session/restore_drill.py`:

   ```python
   import os, sys
   from app.portability.restore_drill import cli
   sys.exit(cli([a for k in ("TENANT", "EXPORT") if os.environ.get(k) for a in (f"--{k.lower()}", os.environ[k])]))
   ```

   then run it (orchestrator only; one line):

   ```bash
   ECSX_SERVICE=aa-crm-dev-api tools/ecs/ecsx.sh .tmp-session/restore_drill.py
   ```

   For another agency, or one given export, add `TENANT=<uuid>` and `EXPORT=<uuid>` after the script path. The same
   module also runs as `python -m app.portability.restore_drill [--tenant <uuid>] [--export <uuid>]` in a shell of the
   container.

2. Read the JSON it prints (ids, table names and counts only; never a value of a row):

   | Key | Pass when |
   |---|---|
   | `ok` | `true` (exit code 0) |
   | `checksums_verified` | every file of the ZIP (`SHA256SUMS`) matched; the object and ZIP digests are checked before |
   | `tables[].manifest_rows` / `restored_rows` | equal for every table (`mismatched_tables` is empty) |
   | `tables[].live_rows` / `live_pk_matched` | reported only: the agency kept working after the export, so live counts may differ |
   | `documents.included` / `skipped` | the export's document count (files up to 25 MiB per export; the rest is listed `skipped_size_cap`) |

3. A failure prints `{"ok": false, "error": "<code>"}`:

   | Code | Meaning | Do |
   |---|---|---|
   | `no_pilot_agency` | no agency is marked pilot | mark it in CIS (Tenant 360) or pass `--tenant` |
   | `no_export` | no ready nightly export | wait for the next night, or queue one: the agency owner's own export does not count (it is the owner's download) |
   | `object_missing` | the bucket rule took it (7 days) | use a younger export |
   | `object_digest_mismatch` / `content_digest_mismatch` / `checksum_mismatch` | the stored copy changed | stop; incident ([incident response](../incident-response.md)) |
   | `not_configured` | the container has no KMS key, bucket or DSN | check the CRM task definition |

4. Record the result: the JSON (it holds no personal data) and the date go into a drill folder
   `docs/audits/<date>-S<nnn>-pilot-restore-drill/`, and `last_tested` / `tested_where` / `tested_evidence` of this page
   are updated in the same root PR.

## How the restore works

The drill runs as `crm_app` in one transaction of the agency (its row security applies):

1. It reads the export row, gets the sealed object, checks its SHA-256, opens it under the agency `export` DEK and checks
   the ZIP's SHA-256 and every line of `SHA256SUMS`.
2. Every table of `manifest.json` becomes a temporary table of the session (`pg_temp`, `ON COMMIT DROP`): a throwaway
   schema no other session sees, dropped when the drill ends. A column the live table has keeps its type (a value that
   no longer parses fails the drill); decrypted `*_enc` values and other types are kept as text.
3. Each table's `json/<table>.json` is loaded with `jsonb_populate_recordset`, then counted, and compared with the
   manifest, the live table and the live primary keys.
4. One `restore_drill` audit event (reason `ok` / `mismatch`) goes into the agency's access log. Nothing else is written.

## A real one-tenant restore

The drill proves the copy restores; a real restore of the pilot's data after a loss is a separate decision of the tech
lead. Use the same export, restore it into a scratch tenant or back into `crm` with the owner's agreement, and follow the
DRY RUN procedure of `skill/aa-cis-schema/references/destructive-ops.md`. Never run an instance-wide PITR while the
pilot runs without telling the pilot agency first (ADR 0019 d16).
