---
id: TPL-01-migration
title: Migration file template
description: The header, transaction, self-registration and expand / contract shape every database migration file starts from.
type: template
status: draft
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 180
related: [TPL-01, docs/architecture/data-standards/01-engineering.md]
---

# Migration file template

Copy the block into `db/migrations/<prefix>-<NNN>_<slug>.sql`. It follows the AA migration rules MIG-1 to MIG-14
([data standards Part A](../architecture/data-standards/01-engineering.md)) in a generic form: one owner and one key
space per schema, forward only, idempotent, expand / contract for every shape change, applied from CI only.

```sql
-- Migration <prefix>-<NNN>: <ISSUE-KEY> — <what changes and why, one line>
-- Phase: expand | contract | data | destructive
-- Touches (lock-sensitive): <schema.table, ...> | none
-- migrate: <no-transaction | destructive>   (only when needed; delete otherwise)
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '15min';

-- Expand: add, never rename or drop in the same release.
CREATE TABLE IF NOT EXISTS <schema>.<table> (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id   uuid NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE <schema>.<table> ADD COLUMN IF NOT EXISTS <column> text;
-- A NOT NULL on an existing table: add CHECK (...) NOT VALID here, VALIDATE in a later file.

-- Grants for the runtime role (least privilege).
GRANT SELECT, INSERT, UPDATE ON <schema>.<table> TO <app_runtime_role>;

-- Self-registration: how the runner knows this file ran.
INSERT INTO <schema>.schema_versions (version, description)
VALUES ('<prefix>-<NNN>', '<slug>')
ON CONFLICT (version) DO NOTHING;
COMMIT;
```

## Rules the reviewer checks

- [ ] The file touches only its owner's schemas and its own registration row.
- [ ] Re-running it is a no-op (`IF NOT EXISTS`, `ON CONFLICT DO NOTHING`, `CREATE OR REPLACE` for views).
- [ ] A rename or drop is split: expand, ship readers and writers on both shapes, then contract in a later file.
- [ ] No large backfill inside the migration (more than about 10,000 rows goes to a job).
- [ ] A destructive file follows the dry-run procedure: exact counts shown, snapshot taken, approval recorded.
- [ ] There is no down migration; an undo is a new forward file.
- [ ] Applied by the CI migrate workflow, never from a laptop or app start-up.
