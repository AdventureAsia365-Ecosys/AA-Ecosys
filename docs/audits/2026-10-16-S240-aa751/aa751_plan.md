# AA-751 (X6): plan (revised after adversarial review)

Prepared by the architect, read-only. HEADs: CIS `cb86de35`, Booking `a35792c`, Infra `ef5226a`. This revision takes in every valid point of the review. I re-checked the code for each one (Booking `test_bk001.py:28-34`, `002_inquiry_intake.sql:75-90`, `001_booking_foundation.sql:67-74`, `app/jobs/queue.py:66-180`, `deploy-dev.yml:17-21,120-160`, `backend/Dockerfile:4,23`; CIS `shared/jobs/queue.py:80-100,127,217`, `worker.py:96-113,282-286`, the three integration tests; Infra `dfs_balance.tf:143-149,295-312`, `handler.py:60-125`, `migration-copy-guard.yml:17-28`, `observability_ecosys.tf:450-467`). The appendix lists the alternatives I did not take, with reasons. No critique point is rejected outright.

⚠️ This contains underscore env vars (`MIGRATION_IDLE_OVERRIDE`, `ACTIONS_ID_TOKEN_REQUEST_TOKEN` / `ACTIONS_ID_TOKEN_REQUEST_URL`, `REQUIRED_SCHEMA_VERSIONS`, `WORKER_ENABLED`, `DATABASE_URL`). Edit them by hand in VSCode. Nghiệp does not have to set any new variable in the GitHub or AWS UI. The Booking gate uses GitHub's built-in OIDC token, and every new knob is a code constant.

---

## 0. Facts that change the scope

| # | Fact | Evidence | Consequence |
|---|---|---|---|
| F1 | `shared.job` is CIS 174 plus `job_finished_idx` (233). It has **no** kind CHECK, lease CHECK, `attempt >= 0` CHECK, `updated_at` trigger or reloptions. **Caveat:** `db-schema-reference.md` is stale (it lists CIS 236 and bk-011). | `api/migrations/174_job_queue.sql:13-50`, 233:66 | **CIS needs migration 242.** The C1 pre-check is **mandatory** and reads the live catalog (§2 C1), because the dump is stale. |
| F2 | `booking.job` already has the kind, status, attempts and lease CHECKs and the trigger. bk-012 added `job_finished_idx`. Checked against the files and the S239 `/ready = bk-012`, not against the dump. | `002:66-90`, `012_retention.sql:37-38` | Scope item 2's "finished_at index" is already done. bk-013 adds the 4 columns, the parent index and the index alignment. |
| F3 | Booking indexes are `job_due_idx` / `job_lease_idx (locked_until)`. CIS indexes are `job_queued_due_idx` / `job_running_idx (kind, locked_until)`. Booking has no parent index and has an extra `job_active_pull_uq`. | 002:75-85, 174:40-50 | The comparator matches indexes by definition. bk-013 converges Booking on the template names (F10). |
| F4 | The `max_attempts` default is 3 on CIS and 5 on Booking. | 174:21, 002 | Template placeholder `{{max_attempts_default}}`. |
| F5 | Booking has no release on shutdown: the `CancelledError` path leaves the row `running` until its lease expires (300 s). Booking claim (`queue.py:76`) and reaper (`:150-180`) also ignore `cancel_requested`, because the column does not exist yet. | `main.py:47-75`, `worker.py:113-129` | B2 ports CIS `release`, plus the `cancel_requested` filters in claim and reaper. |
| F6 | Booking has no machine credential. The ALB is internet-facing. Booking already has an RS256 `JwksCache` + `http_fetcher` (`app/auth/tokens.py:57-114`). `deploy-dev.yml` already has `id-token: write`. | `booking.tf:339-351` | The gate authenticates with GitHub's OIDC token (§3). |
| F7 | `bk_inquiry_pull` is always queued (at +60 s). CIS `ops_rds_role_connections` is enqueued every 5 min and is `deploy_gate_exempt`. | `worker.py:87-99`, `intake.py:45-61` | Both the gate and the DB Migrate idle check need exempt-kind lists. |
| F8 | `acp_shared.acp_runs` was dropped by CIS 121. Its readers are dead: `admin_pipeline.py:5022-5085`, `cost_utils.py:44-114`, `services/acp_canary/`, and in-app Terraform at `infrastructure/canary/`. | grep | Item 6 is a deletion plus a guard test (§6). |
| F9 | DB Migrate has no idle check. The runner connects as `aa_cis_admin`. | `run_migration.py:269-339` | §4 |
| F10 | **Both owners re-run migrations.** CIS conftest swallows migration errors (`conftest.py:250-258`). Booking `test_bk001.py:31` applies **every** migration a second time on the migrated DB, so 002 re-creates `job_due_idx` / `job_lease_idx` with `IF NOT EXISTS` after bk-013 removed them. | | bk-013 must **converge** after a second pass of 001→013: no RENAME. The CIS comparator is the only check that catches a failing 242. |
| F11 | App repos are public. Infra `check_migration_copies.py` reads owner files anonymously. | `db/check_migration_copies.py:16-18` | Booking's vendored template copy can be drift-checked the same way. |
| F12 | Already met: the ADR 0003 header points to 0003a (`0003-one-durable-job-model.md:5`), and `schema-ownership.md:70` has the job row and kind prefixes. `schema-ownership.md:79,93-96` still list `acp_runs`. | | R1 only re-verifies and updates them. |
| F13 | C4.1a: missing data is not breaching. A plain "oldest queued > 15 min" alarm on CIS would fire in every wave. Per-kind caps, **per-worker slots** (`WORKER_MAX_PARALLEL_DEFAULT = 8`, `BACKGROUND_RESERVE = 2`, `BACKGROUND_MAX_RUNNING = 1`) and a serial Booking worker all keep due jobs queued by design. | `03-scaling.md:195,200`; `worker.py:96-113,282-286` | Capacity-aware metrics (§5). Deviation from the C4.1 wording, for Nghiệp to approve. |
| F14 | Booking `set_updated_at()` ends with `END $$;`; the template ends with `END;\n$$`. | `001:67-74` | The comparator normalises the function body (§2.1). |
| F15 | `pg_get_constraintdef` / `pg_get_indexdef` qualify a relation only when it is not visible on `search_path`. Role `booking` has `"$user"` = booking on its path. | | `read_shape` runs under `SET LOCAL search_path = pg_catalog`. |
| F16 | Three CIS integration tests insert `status='running'` with no lease: `test_aa727_waves.py:46-51` (used at :129), `test_aa825_retention_jobs.py:192-197` (used at :204), `test_aa797_tenant_admin.py:180-181`. No production writer breaks the lease rule (claim/release/reap/retry, `admin.py:1400`, the two `_COALESCE_SQL` touch only queued rows). | | C1 fixes those helpers in the same PR. |
| F17 | Autovacuum starts at threshold + scale × N. The default is 50 + 0.2N. C5.1b as written (1000 + 0.02N) only beats the default above N ≈ 5,278 rows. With retention, `shared.job` holds ~2.5k rows and `booking.job` ~1.4k, so those values would make vacuum **rarer**. | `03-scaling.md:233` | Template / 242 / bk-013 use `scale 0.02, threshold 50`: never later than the default, for any N. C5.1b is amended in R1 (decision for Nghiệp). |
| F18 | Both claims keep the **first** attempt's `started_at` (`coalesce(started_at, now())`: CIS `queue.py:92`, Booking `queue.py:73`). CIS `progress` writes always merge (`queue.py:127,217`). | | Overdue-running uses a per-attempt `progress.attempt_started_at` written by the claim (§5). No DDL. |
| F19 | `deploy-dev.yml` treats desired count 0 as normal (smoke skipped at :137-139). The deploy role can already call `ecs:DescribeServices`. | | The gate passes when `runningCount == 0` (§3). |
| F20 | The Booking image is `python:3.12-slim` with **no curl** (`Dockerfile:23`). | | Booking ECS exec uses `python3 -c "import urllib.request;exec(...)"`, not the curl pattern. |
| F21 | The ops-probe Lambda has a 30 s timeout (`dfs_balance.tf:148`) and a 30 s urlopen per path (`handler.py:121`). | | The CIS sample goes **inside** the existing `/rds-role-connections/schedule` handler: no second path, no Lambda re-zip (§5). |
| F22 | Booking Deploy Dev triggers on `backend/**`, which includes `backend/tests/**`. It has no guard until B4. | `deploy-dev.yml:25-30` | B1, B2 and B3 merge only while `booking.job` is idle. B4 adds `!backend/tests/**`. |

---

## 1. Ordered PR list

Repos: **C** = AA-CIS-App, **B** = AA-Booking, **I** = AA-CIS-Infra, **R** = root. Every commit body has `Refs AA-751`. Agents never merge, apply Terraform or dispatch DB Migrate. The orchestrator or Nghiệp does those.

| Order | PR | Repo | Title | Migration | Size | Depends on |
|---|---|---|---|---|---|---|
| 1 | I1 | I | `feat: DB Migrate refuses apply while any owner job table is busy` | — | M | — |
| 2 | C1 | C | `feat: job table DDL template, shape comparison test, shared.job conformance (242)` | **242** | M | — |
| 3 | B1 | B | `feat: bk-013 booking.job catches up with the job table template` | **bk-013** | S | — |
| 4 | I2 | I | `chore: copy migrations 242 and bk-013 for DB Migrate` | copies | S | C1, B1 merged |
| — | Window A | ops | pre-checks, check, two seeded refusals (booking.job, shared.job), apply | — | — | I1, I2 |
| 5 | B2 | B | `feat: release running jobs on shutdown, honour cancel_requested, job table template test` | — | M | bk-013 applied |
| 6 | C3 | C | `refactor: remove readers of the dropped acp_shared.acp_runs` | — | S | — (parallel) |
| 7 | B3 | B | `feat: deploy-gate endpoint authenticated by the GitHub OIDC token` | — | S-M | B2 deployed |
| 8 | B4 | B | `ci: block Booking deploys while booking.job has queued or running jobs` | — | S | B3 deployed |
| 9 | C2 | C | `feat: publish shared.job backlog metrics (AA/Jobs/CIS) from the 5-minute ops schedule` | — | S-M | C1 merged |
| 10 | B5 | B | `feat: publish booking.job backlog metrics to CloudWatch` | — | M | B2 |
| 11 | I3 | I | `feat: job backlog-age alarms per owner and PutMetricData grants` | — | S-M | C2, B5 deployed |
| — | Window B | ops | gate blocked, then passes; alarms fire and recover | — | — | B4, B5, I3 |
| 12 | R1 | R | `docs: X6 job table template, guards and alarms (AA-751)` | — | S | all; dump regenerated |

C1 and B1 can run in parallel with I1. C3 can run in parallel with everything. **Until B4 is deployed, every Booking merge (B1, B2, B3) happens only after a read-only check shows `booking.job` has no non-exempt queued or running rows** (F22; bk-012 #22 is the precedent).

---

## 2. PR details

### I1: DB Migrate idle check (Infra). Design in §4.

- **Files:** `db/run_migration.py`, `.github/workflows/db-migrate.yml`, `db/tests/test_run_migration.py`, `db/README.md`. Recommended, folded in: `db/schema_dump.py` adds `c.reloptions` to the relations query (:58-78) and prints it in the Markdown, which is the only live evidence for C5.1b.
- **Tests** (FakeConn gains `fetch`):
  1. A busy `booking.job` refuses apply with exit 7, and the log names `booking.job`.
  2. A busy `shared.job` refuses and names `shared.job`.
  3. Check mode logs busy and returns 0.
  4. Idle tables pass.
  5. An exempt kind (queued **and** running) is ignored.
  6. The override logs its reason and proceeds.
  7. An open `shared.rerun_wave` refuses.
  8. The wait loop passes when the table goes idle on the 2nd check (inject `sleep`).
  9. An already-applied file skips before the idle check.
- **Rollout and evidence:** **Migration Copy Guard runs on the PR** (its `pull_request` paths include `db/run_migration.py` and `db/tests/**`; it also runs nightly and does not run on merge). Its evidence is the PR checks. Then a human merge. No Terraform. Behaviour evidence comes from window A.
- **Rollback:** revert, or use the `override_busy_jobs` input for a single run.

### C1: template, comparator, 242 (CIS)

**Files:**
- `shared/jobs/job_table_template.sql` (new)
- `shared/jobs/job_table_shape.py` (new, §2.1)
- `api/migrations/242_job_table_template_conformance.sql` (new)
- `tests/integration/test_aa751_job_table_template.py` (new)
- `tests/unit/test_aa751_job_table_template_render.py` (new; no PG; every placeholder is filled; statement count)
- **Fixes for the lease CHECK (F16):** `tests/integration/test_aa727_waves.py` `_job` helper, `tests/integration/test_aa825_retention_jobs.py` `job` helper, and `tests/integration/test_aa797_tenant_admin.py:180-181`. When the status is `running`, they insert `locked_by='test'` and `locked_until=now()+interval '5 min'` (e.g. `CASE WHEN $3='running' THEN 'test' END`).
- `docs/implementation-notes/AA-751.md` (force-add)
- `CONTEXT.md` job runner section: template, trigger, kind CHECK

**Mandatory pre-checks before writing 242:**

1. Grep the tests for writers that would break the new CHECKs:
   - `grep -rn "INSERT INTO shared.job\|UPDATE shared.job" tests/`: check every hit that can produce `status='running'` for a lease (the three above are known), and every kind literal against `^(?!bk_|tp_)[a-z][a-z0-9_]*$`.
   - Payload or idempotency values such as `t-1` or `rerun:VN` are not kinds.
2. Run a read-only ECS exec on the CIS api (S3-mediated pattern, `ssl="require"`). The dump is stale (F1), so this query is the source of truth for both the data and the current catalog:

   ```sql
   SELECT count(*) FILTER (WHERE status='running' AND (locked_by IS NULL OR locked_until IS NULL)) AS lease_bad,
          count(*) FILTER (WHERE attempt < 0) AS attempt_bad,
          count(*) FILTER (WHERE kind !~ '^(?!bk_|tp_)[a-z][a-z0-9_]*$') AS kind_bad,
          count(*) AS n,
          (SELECT reloptions FROM pg_class WHERE oid = 'shared.job'::regclass) AS reloptions,
          (SELECT array_agg(conname || ':' || pg_get_constraintdef(oid)) FROM pg_constraint WHERE conrelid = 'shared.job'::regclass) AS constraints,
          (SELECT array_agg(tgname) FROM pg_trigger WHERE tgrelid = 'shared.job'::regclass AND NOT tgisinternal) AS triggers
   FROM shared.job;
   ```

   Any `*_bad > 0` means fixing the rows first (or changing the plan). A failure at apply time (exit 6) would waste window A.

**Template `shared/jobs/job_table_template.sql`:**

```sql
-- Job table DDL template — ADR 0003a decision 2, roadmap X6 (AA-751), data standards C5.1b (as amended by AA-751),
-- C5.2e, C6.1d.
--
-- The reference shape of every owner's <schema>.job. No runner applies this file. An owner copies the
-- rendered statements into its OWN migration (CIS NNN, TripPlanner tp-NNN, Booking bk-NNN; add IF NOT EXISTS
-- there), and its CI renders this file into a scratch schema and compares its live table with it through
-- pg_catalog (shared/jobs/job_table_shape.py): columns, CHECKs, FK, indexes by definition, the updated_at
-- trigger and reloptions. Names of indexes / constraints / the trigger function are not compared.
--
-- Placeholders (job_table_shape.render):
--   {{schema}}                owner schema (shared, booking, tripplanner, ...)
--   {{kind_pattern}}          owner kind regex: CIS '^(?!bk_|tp_)[a-z][a-z0-9_]*$' (unprefixed, ADR 0003a d3),
--                             Booking '^bk_[a-z0-9_]+$', TripPlanner '^tp_[a-z0-9_]+$'
--   {{extra_statuses}}        owner-only statuses, e.g. ", 'stopped_budget'" (CIS) or "" (others)
--   {{max_attempts_default}}  CIS 3, Booking 5
--
-- Byte copies: AA-Booking backend/tests/job_template/job_table_template.sql (drift-checked by its CI).
-- Changing this file = copy it there in the same session.

CREATE TABLE {{schema}}.job (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind             TEXT NOT NULL,
    payload          JSONB NOT NULL DEFAULT '{}'::jsonb,
    status           TEXT NOT NULL DEFAULT 'queued',
    attempt          INTEGER NOT NULL DEFAULT 0,
    max_attempts     INTEGER NOT NULL DEFAULT {{max_attempts_default}},
    run_after        TIMESTAMPTZ NOT NULL DEFAULT now(),
    locked_by        TEXT,
    locked_until     TIMESTAMPTZ,
    cancel_requested BOOLEAN NOT NULL DEFAULT false,
    idempotency_key  TEXT,
    progress         JSONB NOT NULL DEFAULT '{}'::jsonb,
    result           JSONB,
    cost_usd         NUMERIC(12, 6) NOT NULL DEFAULT 0,
    error            TEXT,
    parent_job_id    UUID REFERENCES {{schema}}.job(id),
    created_by       TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at       TIMESTAMPTZ,
    finished_at      TIMESTAMPTZ,
    CONSTRAINT job_kind_chk     CHECK (kind ~ '{{kind_pattern}}'),
    CONSTRAINT job_status_chk   CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled'{{extra_statuses}})),
    CONSTRAINT job_attempts_chk CHECK (attempt >= 0 AND max_attempts >= 1),
    CONSTRAINT job_lease_chk    CHECK (status <> 'running' OR (locked_by IS NOT NULL AND locked_until IS NOT NULL))
);

-- One job per idempotency key, ever.
CREATE UNIQUE INDEX job_idempotency_key_uq ON {{schema}}.job (idempotency_key) WHERE idempotency_key IS NOT NULL;
-- Claim path: next due queued job.
CREATE INDEX job_queued_due_idx ON {{schema}}.job (run_after, created_at) WHERE status = 'queued';
-- Reaper + per-kind running count.
CREATE INDEX job_running_idx ON {{schema}}.job (kind, locked_until) WHERE status = 'running';
-- Admin Jobs page.
CREATE INDEX job_kind_created_idx ON {{schema}}.job (kind, created_at DESC);
CREATE INDEX job_parent_idx ON {{schema}}.job (parent_job_id) WHERE parent_job_id IS NOT NULL;
-- Retention keyset walk (NAM-15, C5.2e).
CREATE INDEX job_finished_idx ON {{schema}}.job (finished_at, id) WHERE finished_at IS NOT NULL;

CREATE FUNCTION {{schema}}.job_set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER job_set_updated_at
    BEFORE UPDATE ON {{schema}}.job
    FOR EACH ROW EXECUTE FUNCTION {{schema}}.job_set_updated_at();

-- High-churn queue (heartbeat UPDATEs), C5.1b as amended by AA-751: 50 + 2 % of rows is never later than the
-- default 50 + 20 %, at any table size (retention keeps job tables at a few thousand rows).
ALTER TABLE {{schema}}.job SET (autovacuum_vacuum_scale_factor = 0.02, autovacuum_vacuum_threshold = 50);
```

Booking keeps its generic `booking.set_updated_at()` (bk-001:67-74, body `END $$;`). The comparator compares the trigger's timing, level and event, plus the normalised body and the `proconfig`. It does not compare the function name (§2.1).

**Migration `242_job_table_template_conformance.sql`:**

```sql
-- Migration 242: AA-751 (X6) — shared.job conforms to the job table DDL template
-- (shared/jobs/job_table_template.sql, ADR 0003a decision 2).
--
-- shared.job (CIS 174 + 233) lacked the kind CHECK, the running-lease CHECK, attempt >= 0 and the updated_at
-- trigger the template fixes, and had no queue autovacuum settings (C5.1b as amended by AA-751). All CIS writers
-- already keep the invariants (shared/jobs/queue.py claim/_finish/fail/release/reap). The trigger also covers two
-- UPDATEs that never set updated_at (services/places/enqueue.py _COALESCE_SQL, services/jobs/recompute_job.py
-- _COALESCE_SQL). CIS kinds stay unprefixed (ADR 0003a d3); the CHECK rejects other owners' prefixes bk_ / tp_.
--
-- Hot-table DDL (C5.2g): apply only when every job table is idle (DB Migrate refuses otherwise, AA-751 I1).
-- ADD CONSTRAINT ... CHECK scans the retained rows under ACCESS EXCLUSIVE (small table); a bad row aborts the
-- whole file and nothing changes. Re-running is a no-op.

BEGIN;

SET LOCAL lock_timeout = '5s';

CREATE OR REPLACE FUNCTION shared.job_set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;
COMMENT ON FUNCTION shared.job_set_updated_at() IS 'AA-751: BEFORE UPDATE trigger on shared.job, keeps updated_at current.';

CREATE OR REPLACE TRIGGER job_set_updated_at
    BEFORE UPDATE ON shared.job
    FOR EACH ROW EXECUTE FUNCTION shared.job_set_updated_at();

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'shared.job'::regclass AND conname = 'job_kind_chk') THEN
        ALTER TABLE shared.job ADD CONSTRAINT job_kind_chk
            CHECK (kind ~ '^(?!bk_|tp_)[a-z][a-z0-9_]*$');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'shared.job'::regclass AND conname = 'job_lease_chk') THEN
        ALTER TABLE shared.job ADD CONSTRAINT job_lease_chk
            CHECK (status <> 'running' OR (locked_by IS NOT NULL AND locked_until IS NOT NULL));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'shared.job'::regclass AND conname = 'job_attempts_chk') THEN
        ALTER TABLE shared.job ADD CONSTRAINT job_attempts_chk
            CHECK (attempt >= 0 AND max_attempts >= 1);
    END IF;
END $$;

-- Superseded by job_attempts_chk (CIS 174 inline CHECK).
ALTER TABLE shared.job DROP CONSTRAINT IF EXISTS job_max_attempts_check;

ALTER TABLE shared.job SET (autovacuum_vacuum_scale_factor = 0.02, autovacuum_vacuum_threshold = 50);

INSERT INTO shared.schema_versions (version, applied_at, description)
VALUES ('242', now(), 'AA-751 (X6): shared.job conforms to the job table template — kind/lease/attempts CHECKs, updated_at trigger, queue autovacuum')
ON CONFLICT (version) DO NOTHING;

COMMIT;
```

- **Lint:** the `run_migration` destructive regex does not flag `DROP CONSTRAINT`.
- **Lock:** ACCESS EXCLUSIVE until COMMIT, on an idle and small table, inside `lock_timeout 5s`.
- **Regex:** PostgreSQL ARE supports `(?!…)`.
- **Constraint name:** confirm `job_max_attempts_check` from the pre-check's `constraints` list. If the auto-generated name differs, use the live name.

**Integration test `test_aa751_job_table_template.py`** (asyncpg, setup like `test_aa650_job_queue.py:10-21`):
1. In one transaction that is rolled back: `CREATE SCHEMA x6_tmpl`, then execute `render(schema="x6_tmpl", kind_pattern=CIS_KIND_PATTERN, extra_statuses=", 'stopped_budget'", max_attempts_default=3)`.
2. `assert compare(await read_shape(conn, "x6_tmpl"), await read_shape(conn, "shared")) == []`. The failure message lists each diff.
3. Behaviour on `shared.job`:
   - `kind='bk_x'` raises CheckViolation;
   - an UPDATE to `running` with NULL `locked_by` raises CheckViolation;
   - an UPDATE bumps `updated_at`.

**Rollout:**
1. Human merge (a migration PR is never auto-merged). Deploy Dev runs and needs `shared.job` idle; the code change is inert.
2. I2, then window A.

**Evidence:**
- `shared.schema_versions` has row 242;
- the dump shows the three constraints, the trigger, and reloptions (if I1 added them);
- CI Integration Tests are green with the comparator and the three fixed tests.

**Rollback:** migration 243 drops the trigger, the function and the three constraints, re-adds `CHECK (max_attempts >= 1)`, and runs `ALTER TABLE shared.job RESET (autovacuum_vacuum_scale_factor, autovacuum_vacuum_threshold)`.

### B1: bk-013 (Booking, migration-only PR, D8)

- **Files:**
  - `migrations/013_job_template_catch_up.sql`
  - `backend/tests/integration/test_bk013_schema.py` (pattern of `test_bk012_schema.py:24-44`). It checks:
    - the 4 columns with their types and defaults, and the FK;
    - `job_parent_idx`, `job_running_idx` and `job_queued_due_idx` are present;
    - `job_lease_idx` and `job_due_idx` are absent;
    - the reloptions.
    
    It runs after `test_bk001`'s second pass, so it also proves the migration converges.
  - `docs/implementation-notes/AA-751.md`
- `test_migration_guard.py` needs no change (013 is contiguous).

```sql
-- Migration bk-013: AA-751 (X6) — booking.job catches up with the job table template
-- (AA-CIS-App shared/jobs/job_table_template.sql; ADR 0003a decisions 2 and 6).
--
-- Owner: AA-Booking (key bk-NNN). A byte-identical copy goes to AA-CIS-Infra db/migrations/booking/013_job_template_catch_up.sql
-- and is applied to Dev by the DB Migrate workflow (check, then apply), as aa_cis_admin. Never run it from a laptop.
--
-- Depends on bk-002 (booking.job) and bk-012 (job_finished_idx, already the template's retention index).
-- Adds the four columns bk-002 left out (cancel_requested, progress, cost_usd, parent_job_id; constant defaults,
-- so no table rewrite on PG 15), the parent index, the template's running index (kind, locked_until) and the
-- template's due-index name, and the queue autovacuum settings (C5.1b as amended by AA-751). progress /
-- cancel_requested are what release-on-shutdown needs (C6.2c). Role booking already has table-level
-- SELECT/INSERT/UPDATE/DELETE on booking.job: no grant change.
-- Converges: bk-002 re-creates job_due_idx / job_lease_idx with IF NOT EXISTS when every migration is re-run
-- (backend/tests/integration/test_bk001.py); the CREATE IF NOT EXISTS + DROP IF EXISTS pairs below end in the
-- same state after one or two passes. No RENAME, on purpose.
-- Hot-table DDL (C5.2g): DB Migrate refuses apply while any job table is busy.

BEGIN;

SET LOCAL lock_timeout = '5s';

ALTER TABLE booking.job
    ADD COLUMN IF NOT EXISTS cancel_requested BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS progress JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS cost_usd NUMERIC(12, 6) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS parent_job_id UUID REFERENCES booking.job(id);

COMMENT ON COLUMN booking.job.cancel_requested IS 'bk-013 (X6): a staff cancel request; never claimed, reaped or released back to queued (cancelled instead).';
COMMENT ON COLUMN booking.job.progress IS 'bk-013 (X6): handler checkpoint / counters; attempt_started_at per claim, releases on shutdown in progress->>''releases''.';
COMMENT ON COLUMN booking.job.cost_usd IS 'bk-013 (X6): external cost of the job, USD (0 when none).';
COMMENT ON COLUMN booking.job.parent_job_id IS 'bk-013 (X6): the job that spawned this one (same table).';

CREATE INDEX IF NOT EXISTS job_parent_idx
    ON booking.job (parent_job_id) WHERE parent_job_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS job_running_idx
    ON booking.job (kind, locked_until) WHERE status = 'running';
CREATE INDEX IF NOT EXISTS job_queued_due_idx
    ON booking.job (run_after, created_at) WHERE status = 'queued';
DROP INDEX IF EXISTS booking.job_lease_idx;
DROP INDEX IF EXISTS booking.job_due_idx;

ALTER TABLE booking.job SET (autovacuum_vacuum_scale_factor = 0.02, autovacuum_vacuum_threshold = 50);

INSERT INTO shared.schema_versions (version, applied_at, description)
VALUES ('bk-013', now(), 'AA-751 (X6): booking.job template catch-up — cancel_requested, progress, cost_usd, parent_job_id (+FK, job_parent_idx), job_running_idx, job_queued_due_idx, queue autovacuum')
ON CONFLICT (version) DO NOTHING;

COMMIT;
```

- **Guard:** `DROP INDEX booking.…` matches the guard's DROP target rule (`migration_guard.py:199-244`). The ON CONFLICT registration is present. No grant.
- **Second pass:**
  1. 002 re-creates `job_due_idx` and `job_lease_idx`.
  2. bk-013 skips the existing `job_queued_due_idx`, `job_running_idx` and `job_parent_idx`, and drops both old indexes again.
  3. `ADD COLUMN IF NOT EXISTS` skips its inline FK.

  The end state is the same.
- **Should know:**
  - The FK `ON DELETE` is NO ACTION (same as CIS). No Booking kind sets a parent today; record that constraint in CONTEXT.md for a future spawning kind.
  - Nothing in Booking code or docs refers to `job_due_idx` or `job_lease_idx`.
- **Rollout:** human merge **while `booking.job` is idle** (the test file triggers Deploy Dev, F22), then I2, then window A. `REQUIRED_SCHEMA_VERSIONS` waits for B2 (apply first, then code).
- **Rollback:** the change is additive, so leave the columns. Reverting the indexes would need a bk-014; not expected.

### I2: copy 242 + bk-013 (Infra)

Byte copies from owner main: `db/migrations/cis/242_job_table_template_conformance.sql` and `db/migrations/booking/013_job_template_catch_up.sql` (precedent 400fdbc / #151, #157). Migration Copy Guard on the PR must pass. S, human merge.

### DB Migrate window A (ops, orchestrator)

This window produces the Done-when evidence "refuses apply while **any** owner job table is busy, and logs which", for both tables.

0. **Pre-checks (read-only):**
   - The C1 catalog/data query has run with every `*_bad = 0`.
   - `SELECT id, name, created_at FROM shared.rerun_wave WHERE status = 'open'` returns no rows. The CIS deploy gate never checks waves, so an abandoned open wave would make every apply refuse. If one exists, close it or ask Nghiệp first.
   - Re-check `shared.job` right before applying (lessons :57/:58).
1. Dispatch `check cis/242_…` and `check booking/013_…`. Each logs `before:` and the per-table busy report.
2. **Booking probe.** ECS exec on cluster `aa-cis-dev-cluster`, service `aa-booking-dev-api`, container `api`. There is **no curl** (F20), so the command is `--command "python3 -c \"import urllib.request;exec(urllib.request.urlopen('$URL',timeout=30).read())\""`. The script uses asyncpg on the container's `DATABASE_URL` (role booking). The kind has no handler, so it is never claimed:

   ```sql
   INSERT INTO booking.job (kind, payload, created_by, run_after) VALUES ('bk_x6_probe', '{"probe":"AA-751 window A"}', 'aa-751-probe', now()) RETURNING id;
   ```

   - Dispatch `apply booking/013_…`. Expect exit 7 and `MIGRATE ERROR: refusing apply — busy: booking.job (queued=1)`. Copy the step summary.
   - Cancel the probe:

     ```sql
     UPDATE booking.job SET status='cancelled', finished_at=now(), error='AA-751 probe' WHERE kind='bk_x6_probe' AND status='queued';
     ```
3. **CIS probe** (S3-mediated ECS exec on the CIS api; curl exists there):

   ```sql
   INSERT INTO shared.job (kind, payload, created_by) VALUES ('x6_probe', '{"probe":"AA-751 window A"}', 'aa-751-probe');
   ```

   - The kind is unregistered, so it is never claimed, and it passes the future 242 CHECK.
   - Dispatch `apply cis/242_…`. Expect exit 7 naming `shared.job`.
   - **Cancel it at once** (it also blocks CIS Deploy Dev):

     ```sql
     UPDATE shared.job SET status='cancelled', finished_at=now(), error='AA-751 probe' WHERE kind='x6_probe' AND status='queued';
     ```
4. `apply booking/013_…` → ok. Then `apply cis/242_…` → ok. The auto-dispatched DB Schema Dump opens the root reference PR, which also refreshes the stale dump.

### B2: release on shutdown, cancel_requested, attempt timestamp, template test (Booking app)

**Files:**
- **`backend/app/jobs/queue.py`:**
  - Add `MAX_RELEASES = 3` and `release(pool, job_id, worker_id)`, a port of CIS `queue.py:195-224`:
    - the status becomes `cancelled` if `cancel_requested`, `failed` at the 3rd release, otherwise `queued`;
    - `attempt = greatest(attempt-1, 0)`, `run_after = now()`, the lock is cleared;
    - `progress = progress || {released, releases}`;
    - guarded by `status='running' AND locked_by=$2`.
  - **claim:** add `AND NOT cancel_requested` to the inner SELECT, and set `progress = progress || jsonb_build_object('attempt_started_at', now())` (F18).
  - **reap:** a running row with `cancel_requested` and an expired lease becomes `cancelled` (with `finished_at`) instead of being requeued, as in CIS.
- **`backend/app/jobs/worker.py` `_run`:** add `except asyncio.CancelledError:` that runs `await asyncio.shield(queue.release(pool, job.id, self.worker_id))`, logs, and re-raises. The heartbeat cancel stays in `finally`. `wait_for` in `main.py` awaits the cancelled task, so the release runs before `db.close()`, inside 20 s + ~1 s, which is below `stopTimeout` 30 s. Update the `main.py:47-49` comment.
- **`backend/app/db.py`:** `REQUIRED_SCHEMA_VERSIONS` += `"bk-013"`.
- **`backend/tests/job_template/job_table_template.sql` + `job_table_shape.py`:** byte copies of the C1 files. Exclude the directory from ruff if Booking's rules differ.
- **`backend/tests/integration/test_job_table_template.py`:** render with `schema="x6_tmpl", kind_pattern='^bk_[a-z0-9_]+$', extra_statuses="", max_attempts_default=5`. Compare against `booking` with `allow_extra_indexes=("UNIQUE … (kind) WHERE ((kind = 'bk_inquiry_pull'::text) AND (status = ANY (ARRAY['queued'::text, 'running'::text])))",)`. The exact text is what `pg_get_indexdef` prints under `search_path = pg_catalog`; take it from a first run.
- **`backend/scripts/check_job_template_copy.py`:** stdlib, contents API, anonymous or `github.token`, retry then FAIL, modelled on Infra `check_migration_copies.py`. It compares both vendored files with AA-CIS-App main.
- **`.github/workflows/ci.yml`:** new job "Job template copy". Whether it is a required check is Nghiệp's decision.
- **Unit tests** (`tests/unit/test_job_queue.py`, `test_job_worker.py`):
  - the release SQL shape;
  - the claim SQL has the cancel filter and the attempt timestamp;
  - the reaper's cancel branch;
  - the `CancelledError` path calls release and re-raises.
- **Integration tests:**
  - claim → handler sleeps → stop + `wait_for` timeout → the row is `queued`, `attempt=0`, `progress.releases=1`;
  - a third release → `failed`;
  - `cancel_requested=true` → release gives `cancelled`, the claim skips it, an expired lease reaps it to `cancelled`;
  - a re-claim overwrites `progress.attempt_started_at`.
- **`CONTEXT.md`** §Deferred work (:176-196): the retention `max_attempts = 1` "no progress column yet" note becomes "released on shutdown". Also `docs/implementation-notes/AA-751.md`.

**Rollout:**
1. Merge only after bk-013 is applied (otherwise `/booking/health/ready` returns 503) **and** while `booking.job` is idle (F22).
2. Deploy Dev; smoke `/booking/health` and `/ready`.

**Evidence:** CI integration is green (template test plus release and cancel tests), and `/ready` returns 200 listing bk-013. A live release proof is optional; the integration test is the gate.

**Rollback:** revert. The columns stay.

### C3: acp_runs readers (CIS). Design in §6.
### B3 / B4: Booking deploy gate. Design in §3.
### C2 / B5 / I3: backlog-age alarms. Design in §5.

### R1: root docs (at the end; a partial R1 this session is fine)

- **`docs/database/schema-ownership.md`:**
  - :70: add "idle-exempt kinds: CIS `ops_rds_role_connections`, Booking `bk_inquiry_pull`" (the source until X1 `owners.yaml`; also the list hard-coded in `run_migration.py` `IDLE_EXEMPT_KINDS` and Booking `DEPLOY_GATE_EXEMPT`) and "template `apps/AA-CIS-App/shared/jobs/job_table_template.sql`";
  - :79: `acp_runs` has no readers;
  - :93-96: Dead Table Registry candidate `shared.acp_runs`.
- **`docs/architecture/data-standards/03-scaling.md`:**
  - **amend C5.1b** (:233) to "`autovacuum_vacuum_scale_factor = 0.02` and `autovacuum_vacuum_threshold = 50` (never later than the default at any size; a threshold of ~1000 only helps above ~5k rows)";
  - reword C4.1 (:195) to "oldest **claimable** queued, capacity-aware";
  - flip C4.1, C5.1b, C5.2e Booking (:245), C6.1d (:304), C6.2c (:312), C6.3a (:318) and C6.3b (:319) to Exists with PR numbers;
  - C6 preamble (:283-293): "re-queued only when its lease expires" becomes "released on shutdown";
  - current-facts row (:406).
- **Other:**
  - `02-data-management.md:351`;
  - `docs/backlog/README.md:34, :86`;
  - `db-schema-reference.md` via the dump PR only;
  - save this plan as `docs/audits/2026-10-16-S240-aa751-x6-plan/README.md`.

---

## 2.1 Comparator `shared/jobs/job_table_shape.py` (CIS; byte copy in Booking)

```python
# render(template_text, *, schema, kind_pattern, extra_statuses, max_attempts_default) -> str
# async read_shape(conn, schema) -> Shape   (Shape: columns, checks, fks, pk, indexes, triggers, reloptions)
# compare(template: Shape, owner: Shape, *, allow_extra_indexes=()) -> list[str]   (human-readable diffs)
```

`read_shape` opens `async with conn.transaction():` and first runs **`SET LOCAL search_path = pg_catalog`** (F15). Every `pg_get_*def` then qualifies `<schema>.job`, whatever the role's path. It then reads, with `$1 = f'{schema}.job'`:

```sql
SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS type, a.attnotnull, pg_get_expr(d.adbin, d.adrelid) AS dflt
  FROM pg_attribute a LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
 WHERE a.attrelid = $1::regclass AND a.attnum > 0 AND NOT a.attisdropped;
SELECT contype, convalidated, pg_get_constraintdef(oid) AS def FROM pg_constraint WHERE conrelid = $1::regclass;
SELECT pg_get_indexdef(indexrelid) AS def FROM pg_index WHERE indrelid = $1::regclass;
SELECT t.tgtype, p.prosrc, p.proconfig FROM pg_trigger t JOIN pg_proc p ON p.oid = t.tgfoid
 WHERE t.tgrelid = $1::regclass AND NOT t.tgisinternal;
SELECT coalesce(reloptions, '{}') FROM pg_class WHERE oid = $1::regclass;
```

**Normalization:**
- **Columns:** matched by name, order-insensitive. Compare type, NOT NULL and default text.
- **CHECKs:** names are stripped. The status CHECK is parsed into a set from `ARRAY[...]`. Every constraint must be `convalidated`.
- **FK and index text:** replace the qualified `<schema>.job` with a placeholder (it is always qualified under the pinned path).
- **Indexes:** strip `CREATE [UNIQUE] INDEX <name> ON <schema>.job`, keep `UNIQUE` and `USING …`, compare as a multiset. Owner extras are allowed only when listed.
- **Trigger:** exactly one BEFORE UPDATE FOR EACH ROW trigger. Its body is normalised: collapse whitespace, strip, then strip trailing `;` and whitespace (F14: `END;` and `END` compare equal). The normalised body must equal the template's, and `proconfig` must contain `search_path=pg_catalog`.
- **reloptions:** owner ⊇ template.
- **Skipped:** grants, comments, owner.
- **Unit tests (no PG):**
  - the body normaliser (`END $$;` vs `END;\n$$`);
  - FK/index placeholdering;
  - the status set parse.

---

## 3. Booking deploy gate (B3 + B4)

**Rejected designs:**
- (a) a new shared secret: $0.40/month, a task-def change, and a GitHub secret to set by hand;
- (b) public queue counts on `/ready`;
- (c) `ecs:RunTask` / `ExecuteCommand` on the deploy role;
- (d) reading the B5 metric, which can be up to 5 min stale.

**Chosen:** a GitHub Actions OIDC token, verified by Booking's existing JWKS code. Cost $0, no secret, no Terraform.

### B3 (app)
- **`backend/app/auth/ci.py`:** `GithubDeployVerifier(JwksCache(http_fetcher(GITHUB_JWKS_URL)))`. Code constants:
  - `GITHUB_OIDC_ISSUER = "https://token.actions.githubusercontent.com"`;
  - `GITHUB_JWKS_URL = ISSUER + "/.well-known/jwks"`;
  - `DEPLOY_GATE_AUDIENCE = "aa-booking-deploy-gate"`.

  `jwt.decode(..., algorithms=["RS256"], audience=…, issuer=…, options={"require": ["exp","iat","iss","aud"]})`, then require:
  - `repository == "AdventureAsia365-Ecosys/AA-Booking"`;
  - `ref == "refs/heads/main"`;
  - `environment == "dev"`;
  - `event_name in {"push","workflow_dispatch"}`;
  - `job_workflow_ref` starts with `AdventureAsia365-Ecosys/AA-Booking/.github/workflows/deploy-dev.yml@refs/heads/main`.

  Any failure → 401. JWKS unavailable → 503 (fail closed).
- **`backend/app/jobs/kinds.py`** (new): `DEPLOY_GATE_EXEMPT = frozenset({"bk_inquiry_pull"})`, plus `EXPECTED_SECONDS` / `DEFAULT_EXPECTED_SECONDS = 300` (used by B5).
- **`queue.active_count(pool, exempt_kinds)`:** `SELECT status, kind, count(*) FROM booking.job WHERE status IN ('queued','running') AND NOT (kind = ANY($1)) GROUP BY status, kind`.
- **`backend/app/routers/ops.py`:** `GET /booking/ops/deploy-gate` returns `{active, by_status, by_kind, safe_to_deploy, exempt_kinds}`. Register it in `main.py`.
- **Tests:** unit tests with a local RSA key and a fake JWKS (each claim, expiry, wrong aud/repo/ref/env → 401; JWKS down → 503); `active_count` integration. Keep the 90 % floor.
- **`CONTEXT.md`** auth section: "one machine caller: the deploy workflow, by GitHub OIDC".
- **Merge while `booking.job` is idle** (F22).

### B4 (workflow `deploy-dev.yml`)
- **Paths:** add `"!backend/tests/**"` under `on.push.paths`, so test-only and template-copy PRs no longer deploy (F22).
- **Input:** `workflow_dispatch.inputs.override_running_jobs` (string, "Nghiệp only, reason").
- **New job `preflight`** (`needs: config`, `if: enabled`, `environment: dev`), mirroring CIS `deploy-dev.yml:36-66`:
  1. `aws-actions/configure-aws-credentials` with the same OIDC deploy role (`vars.AWS_ROLE_ARN`). Run `aws ecs describe-services … --query 'services[0].runningCount'`. **If `runningCount == 0`**, emit `::notice::no task running — nothing can be interrupted, gate skipped` and pass (F19).
  2. Otherwise, mint the token: `curl -sS -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=aa-booking-deploy-gate" | jq -r .value`.
  3. GET `${BASE_URL%/}/booking/ops/deploy-gate`. If `safe_to_deploy == true`, pass.
  4. If not safe and an override with a reason is given: `::warning::` naming the reason and the active count.
  5. If not safe and no override: `::error::Deploy blocked: N job(s) queued/running (by kind …)` and exit 1.
  6. If `runningCount > 0` and `BOOKING_API_BASE_URL` is unset, or the response is unreachable or not JSON: block unless overridden (fail closed).
- `deploy.needs: [config, preflight]`. Rewrite the header text at :17-21 to describe the guard.

**Evidence (window B):**
1. Seed `bk_x6_probe` (§5).
2. Dispatch Deploy Dev → preflight is red with "1 job(s) queued (bk_x6_probe)".
3. Cancel the probe → re-dispatch → green, rollout COMPLETED, smoke `/booking/health` + `/ready` return 200.

**Rollback:** the override input, or revert B4 (B3 is inert on its own).

---

## 4. DB Migrate idle check (I1)

**Where:**
- In `run_task` (`db/run_migration.py:290-339`), after the `before:` log (:297), **always** run `report = await job_tables_busy(conn)` and log one line per table. In check mode, return 0 after that.
- In apply mode, after `skip: already applied` (:300-302) and before the destructive/apply path (:303), run `await wait_until_idle(conn, attempts=3, interval_s=20, sleep=asyncio.sleep)`. If the tables are still busy and there is no override, log the refusal and `return 7`.
- Document exit code 7 in the docstring (:28-29) and in `db/README.md`.
- `lock_timeout 5s` stays as the backstop for the check-then-apply race.

**SQL** (ops tooling may read every owner; ADR 0003a d1):

```sql
-- every owner job table (a future tripplanner.job is covered automatically)
SELECT n.nspname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE c.relname = 'job' AND c.relkind IN ('r', 'p')
   AND EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid = c.oid AND a.attname = 'status' AND NOT a.attisdropped)
 ORDER BY n.nspname;
-- per table (identifier quoted from the catalog value)
SELECT kind, status, count(*)::int AS n,
       count(*) FILTER (WHERE status = 'queued' AND run_after <= now())::int AS due
  FROM <table> WHERE status IN ('queued', 'running') AND NOT (kind = ANY($1::text[]))
 GROUP BY kind, status ORDER BY kind, status;
-- open wave (C6.3b), only if to_regclass('shared.rerun_wave') IS NOT NULL
SELECT count(*)::int FROM shared.rerun_wave WHERE status = 'open';
```

**Exempt kinds:** the exemptions are needed. `ops_rds_role_connections` is queued or running every 5 min, and `bk_inquiry_pull` is always queued at +60 s. A *running* exempt row is also safe: both handlers run short transactions (`intake.py:68-128` does no HTTP while its transaction is open), and `lock_timeout` is the backstop. Daily retention kinds stay NOT exempt.

```python
IDLE_EXEMPT_KINDS = {"shared": frozenset({"ops_rds_role_connections"}),   # CIS registry deploy_gate_exempt
                     "booking": frozenset({"bk_inquiry_pull"})}           # Booking DEPLOY_GATE_EXEMPT
```

- **Busy** means any non-exempt queued row (any `run_after`) or running row, matching the deploy-gate semantics. A missing table is a WARNING.

**Log lines** (they reach `$GITHUB_STEP_SUMMARY` through the existing `grep '^MIGRATE'`):

```
MIGRATE idle: shared.job running=0 queued=0 (exempt: ops_rds_role_connections)
MIGRATE busy: booking.job running=0 queued=1 due=1 kinds=[bk_x6_probe:queued=1]
MIGRATE busy: shared.rerun_wave open=1
MIGRATE ERROR: refusing apply — busy: booking.job (queued=1). Wait until every job table is idle, or re-dispatch with override_busy_jobs=<reason> (Nghiệp only)
```

**Override:**
- New `workflow_dispatch` input `override_busy_jobs`. It is passed as `{name: "MIGRATION_IDLE_OVERRIDE", value: $override}` in the `jq` overrides (`db-migrate.yml:130-140`) and echoed into the summary.
- The runner logs `MIGRATE WARNING: idle check OVERRIDDEN (<reason>)` with the report and proceeds.
- Dispatch stays human-only behind `environment: prod`.

**Known costs:**
- A destructive apply takes its snapshot (:93-106) before the idle check, so a refusal wastes one snapshot. The runbook says run `check` first, and `check` now shows busy.
- The exempt list duplicates the CIS and Booking registries until X1.

---

## 5. Backlog-age metrics per owner (C2, B5, I3)

**Design rules:**
- The sample never depends on the queue it measures. The CIS sample runs in an API request, the Booking sample in an independent asyncio loop.
- The metrics are **capacity-aware**, so normal waves and long serial jobs do not page (F13).

| | CIS | Booking |
|---|---|---|
| Namespace | `AA/Jobs/CIS` | `AA/Jobs/Booking` (one per owner: IAM keeps each app to its own namespace) |
| `OldestQueuedAgeSeconds` | Max(now − `run_after`) over **starved** due queued rows; 0 when there are none. A row is starved when either: (a) there is **no live worker** (`shared.job_worker` with `stopped_at IS NULL AND last_seen_at > now() − 3 × the worker heartbeat interval`), or the kind is unregistered (never claimable: a bug); or (b) some live worker *would claim it right now*: the kind is in that worker's `caps` and is in the result of the worker's claim-caps rule, given its free slots (`max_parallel − running rows locked_by that worker`) and its running background count, **and** the kind's global running count is below its `concurrency`. To avoid drift, extract the body of `Worker.claim_caps` (`worker.py:104-113`) into a pure `claim_caps_for(max_parallel, caps, free_slots, running_background)` that both the worker and the sampler call. A wave that fills every slot gives 0; stuck slots show up as overdue-running instead. | Max(now − `run_after`) over due queued rows, **but 0 while a non-overdue job is running**. The worker is serial, so a due row waiting behind a healthy job is normal, and an unhealthy one shows up as overdue. Unhandled kinds count (that is how the probe fires). |
| `OverdueRunningJobs` | Count of running rows with now − `coalesce((progress->>'attempt_started_at')::timestamptz, started_at)` > 2 × `expected_seconds` (registry; default 600) | Same expression, against `app/jobs/kinds.py` `EXPECTED_SECONDS` (default 300) |
| Attempt timestamp (F18) | C2 changes CIS claim (`queue.py:89-93`): `progress = progress \|\| jsonb_build_object('attempt_started_at', now())`. Handlers already merge progress (`queue.py:127`). Check that `retention_job.py:196` reads only its own keys. | Done in B2 (claim) |
| Publisher | **Inside the existing `POST /admin/job-runner/rds-role-connections/schedule` handler** (`admin_job_runner.py:284-295`), after the enqueue, in `try/except` (a sample failure is logged and never fails the enqueue). Logic in `shared/jobs/backlog.py`: a pure `backlog_sample(queued_rows, running_rows, workers, kinds, now)` and a publish through `asyncio.to_thread(client.put_metric_data)` with botocore `Config(connect_timeout=3, read_timeout=5, retries={"max_attempts": 1})`, like `ops_rds_role_connections_job.py:94-113`. The response gains `backlog: {...}` or `backlog_error`. **No new path, no `_ALLOWED_PATHS` or schedule-input change, no Lambda re-zip** (F21). | `backend/app/jobs/metrics.py` `JobMetricsSampler(pool, every_s=300)`, started in the lifespan next to the worker when `worker_enabled and db.configured`, cancelled on shutdown. 2 SELECTs and 1 PutMetricData (boto3 in a thread, same timeouts). Failures are logged and never raised. |
| IAM | `cis_ecs_task_put_metric_aa_rds` (`observability_ecosys.tf:453-467`, on `module.ecs.task_role_name`): condition `cloudwatch:namespace = ["AA/RDS", "AA/Jobs/CIS"]`. I3 confirms the api task definition uses that task role (the AA-832 comment says worker and api share `aa-cis-dev-ecs-task-role`). | New `aws_iam_role_policy.booking_ecs_task_put_metric_jobs` on `aws_iam_role.booking_ecs_task` (pattern of `ses.tf:214-218`): `cloudwatch:PutMetricData`, `Resource *`, namespace `AA/Jobs/Booking`. |
| Alarms (I3, `for_each` over `local.job_backlog_owners`, SNS `aws_sns_topic.alerts` alarm + ok) | `${local.name_prefix}-jobs-queue-age`, `-jobs-overdue-running`, `-jobs-sampling-stopped` | `${local.bk_name_prefix}-jobs-…` (same 3), tag `App = "booking"` |

**Alarm parameters:**
- **queue-age:** `Maximum`, period 300, eval 2 / datapoints 1, `> 900`, `notBreaching`.
- **overdue-running:** `Maximum`, 300, 2 / 1, `> 0`, `notBreaching`.
- **sampling-stopped:** `SampleCount` of `OldestQueuedAgeSeconds`, period 900, eval 3, `< 1`, `breaching`. This is the documented exception, like AA-832 :474-490. The Booking one also fires when the service is scaled to 0 or `WORKER_ENABLED` is off; document that next to the alarm.

**Booking `EXPECTED_SECONDS`** (B5), proposed values:
- `bk_inquiry_pull` 60
- `bk_inquiry_process` 60
- `bk_notify_email` 60
- `bk_retention_job` 900
- `bk_retention_inbox_redact` 900

Before merging, confirm them against p95 of `finished_at − started_at` per kind (read-only ECS exec on Booking with the python/urllib command, F20). With the "running → 0" rule, a 900 s retention run no longer ages the queue metric.

**Monthly cost** (us-west-1 list prices, the same basis as the AA-832 block :329-339, no free tier):
- 4 custom metrics × $0.30 = **$1.20**
- 6 standard alarms × $0.10 = **$0.60**
- PutMetricData: 8,640 (CIS) + 8,640 (Booking) = 17,280 × $0.01/1k = **$0.17**
- The CIS sample rides the existing 5-min invocation: **$0** extra API GW / WAF / Lambda.
- Booking gate (OIDC): **$0**.
- **Total ≈ $1.97/month**, CloudWatch only, no new service. The cost block goes in I3.

**Rollout:**
1. C2 deploys; the handler logs AccessDenied for the sample until I3. Merge it while `shared.job` is idle (CIS Deploy Dev guard).
2. B5 deploys (merge while `booking.job` is idle, or after B4).
3. I3: plan and apply from a merged **main** checkout. No Lambda zip changes in this revision.

**Evidence (exist and OK):**
- `aws cloudwatch describe-alarms --alarm-name-prefix aa-cis-dev-jobs --profile aa365-admin --region us-west-1 --query 'MetricAlarms[].[AlarmName,StateValue]' --output text`, and the same for `aa-booking-dev-jobs`;
- `get-metric-statistics` per namespace.

**Window B (fired and recovered).** Run it only while no wave is planned.
1. **CIS probe** (curl pattern):

   ```sql
   INSERT INTO shared.job (kind, payload, created_by, run_after) VALUES ('x6_probe', '{"probe":"AA-751"}', 'aa-751-probe', now() - interval '20 minutes')
   ```

   It is unregistered, so it is starved by rule (a). It also blocks CIS Deploy Dev while queued.
2. **Booking probe** (python/urllib command): the same with `bk_x6_probe`.
3. At the next sample, both queue-age alarms go to ALARM (SNS email). Run the Booking gate test (§3) while the probe is seeded.
4. Cancel both probes:

   ```sql
   UPDATE … SET status='cancelled', finished_at=now(), error='AA-751 probe' WHERE kind IN ('x6_probe','bk_x6_probe') AND status='queued'
   ```

   The next sample is 0, then the alarms go to OK.
5. Evidence: `aws cloudwatch describe-alarm-history --alarm-name <name> --history-item-type StateUpdate --max-records 5 --profile aa365-admin --region us-west-1` (ALARM → OK) for each owner, plus the SNS emails. Overdue-running is not fire-tested; unit tests cover it (including the re-claim case), and the report says so.

**Rollback:** revert I3. The handler and the sampler are harmless without IAM.

---

## 6. acp_runs readers (C3)

Nothing moves to `shared.job`. The readers point at a table that CIS 121 dropped, and `shared.job` already covers stuck runs (reaper, Jobs page).

- **Delete:**
  - `api/routers/admin_pipeline.py:5022-5085` (`GET /admin/acp/stuck-runs`, `POST /admin/acp/runs/{run_id}/force-fail`);
  - `services/acp_shared/cost_utils.py` `record_stage_cost` / `finalize_run_cost` (the whole file if nothing else is in it);
  - `services/acp_canary/`;
  - `infrastructure/canary/`. First the orchestrator confirms it is not live: `aws scheduler get-schedule --name aa-cis-dev-acp-canary-weekly --group-name default --profile aa365-admin --region us-west-1` should return ResourceNotFound.
- **Keep:** comments and docstrings (`services/export/handler.py:427-429`, `acp_produce/reliability.py:19`, `acp_planning/quarter.py:20`, `acp_shared/tracer.py:4`), the migrations, and the `tests/integration/conftest.py:126-137` FK stub.
- **Guard:** `tests/unit/test_aa751_no_acp_runs_reader.py` scans `api/`, `services/` and `shared/` `*.py` with `re.compile(r"\b(FROM|JOIN|UPDATE|INTO)\s+(acp_shared|shared)\.acp_runs\b", re.I)` and fails with file:line.
- **Should know:** `acp_produce/reliability.py:31` imports `acp_shared/stage_checkpoint`, whose table is also gone. That is a follow-up for the Dead Table Registry (N6).
- **Rollout:** human merge while `shared.job` is idle → Deploy Dev → `curl -s -o /dev/null -w "%{http_code}" -H "x-admin-secret: …" https://api-cis.lumiguides.it.com/admin/acp/stuck-runs` → 404. Update the `CONTEXT.md` legacy-models line.
- **Rollback:** revert.

---

## 7. Done-when mapping

| Done-when | Delivered by | Evidence |
|---|---|---|
| Template + comparison tests green for CIS + Booking in CI | C1, B2 | CI Integration Tests runs |
| bk-NNN applied via DB Migrate | B1, I2, window A | DB Migrate run log; `shared.schema_versions` bk-013 (+ 242) |
| Booking deploy blocked by a seeded queued bk_ job, then passes when idle | B3, B4, window B | 2 Deploy Dev runs + rollout COMPLETED + smoke |
| DB Migrate refuses apply while any owner job table is busy, and logs which | I1, window A | two refusals: `busy: booking.job` and `busy: shared.job` (exit 7) |
| Backlog-age alarms exist (OK), one fired and recovered | C2, B5, I3, window B | `describe-alarms`; `describe-alarm-history` ALARM → OK per owner; SNS |
| No runtime reader of acp_runs | C3 | guard test; 404 |
| ADR 0003 header points to 0003a | already met (F12) | `0003-one-durable-job-model.md:5` |
| schema-ownership.md job row + kind prefixes | already met; R1 adds exempt kinds + template path | `schema-ownership.md:70` |

---

## 8. This session (~3 h) vs follow-up

**This session**, two lanes. The orchestrator or Nghiệp runs every merge, dispatch and apply.
- **Lane 1:**
  - I1 (~45 min with CI)
  - C1 (~70 min, including the three test fixes and the mandatory pre-check exec)
  - B1 (~20 min, in parallel)
  - I2 (10 min)
  - window A (~30 min: pre-checks, two refusals, two applies)
- **Lane 2:**
  - C3 (~25 min)
  - B2 (~60 min, after bk-013 is applied; it now includes the cancel and attempt-timestamp ports)
- **Docs:** partial R1 (C5.1b amendment and flips for C5.1b, C5.2e, C6.1d, C6.2c, C6.3b) and the saved plan.
- **Done-when closed this session:** template + tests, bk-013 applied, DB Migrate refusal (both tables), no acp_runs reader. AA-751 stays In Progress.

**Follow-up session (~3 h):**
- B3 → B4
- C2 + B5 → I3 (Nghiệp-approved ~$1.97/month)
- window B
- final R1 after the dump PR
- Done per aa-ship

**Decisions for Nghiệp before coding:**
1. Amend data standard C5.1b to `scale 0.02, threshold 50`. As written (~1000), it would make vacuum rarer on both job tables at their real sizes (F17).
2. The C4.1 deviation: capacity-aware "starved queued" age (CIS) and "0 while a healthy job runs" (Booking) instead of plain oldest queued (F13).
3. Is the Booking "Job template copy" CI job a required check?
4. The Booking sampling-stopped alarm also fires when Booking is scaled to 0: accept or drop it (saves $0.10).
5. Approve the I3 cost (~$1.97/month).

## 9. Lessons (skill/aa-lessons/lessons.md)

- :57 / :58: re-check `shared.job` before each CIS merge and before the window A applies.
- Terraform runs only from a merged main checkout.
- The export-credentials env-leak line.
- Subagents cannot merge, apply or dispatch.
- **New, to write when C1/B1 land:**
  1. "ADR text described a shape the live table did not have (CIS 174 lacked lease/kind CHECK + trigger); verify ADR claims against the live catalog, not a stale dump, before scoping."
  2. "Booking re-runs every migration (test_bk001): never RENAME an object an earlier migration creates with IF NOT EXISTS; use CREATE IF NOT EXISTS + DROP IF EXISTS so the file converges." Catch it with the test_bk013 schema test.
  3. "Check per-table autovacuum numbers against the real row count: threshold + scale × N vs the default 50 + 0.2N."

---

## Appendix: review points: accepted, and alternatives not taken

All 15 points were checked against the code and are valid. Each is fixed above:
- 1 → B1 / F10
- 2 → §2.1 / F14
- 3 → C1 / F16
- 4 → F17, template / 242 / bk-013, decision 1
- 5 → F18, B2, C2
- 6 → B4 / F19
- 7 → windows A and B / F20
- 8 → §5 / F13
- 9 → §5 / F21
- 10 → §2.1 / F15, and B2 cancel filters
- 11 → window A steps 0 and 3
- 12 → §4, which keeps the exemptions and adds the running-row reasoning
- 13 → 242 uses plain ADD CONSTRAINT, and the pre-check is mandatory
- 14 → I1 rollout
- 15 → F22 and B4 paths

The review's caveat about the stale dump is accepted: F1/F2 and the mandatory catalog pre-check.

Alternatives the review offered that I did not take:

| Point | Alternative not taken | Why |
|---|---|---|
| 1 | Keep Booking's old index names (the comparator ignores names) | Converging on the template names is just as cheap with CREATE IF NOT EXISTS + DROP IF EXISTS, and it makes both tables read the same in `\d`, the dump and the docs. |
| 2 | Rewrite the template body as `END $$;` instead of normalising | Normalising in the comparator covers both spellings and any future owner. Editing the template text alone would just move the mismatch to CIS. |
| 4 | `autovacuum_vacuum_threshold = 100` | 50 equals the default threshold, so with scale 0.02 the trigger point is never later than the default at any N. 100 would be later than the default below ~280 rows. |
| 8 (CIS) | "Due claimable rows exist AND no claim in the last 15 min" | It needs a claim-time scan over the whole table, and it stays green while one kind starves as long as other kinds keep claiming. Reusing the worker's own claim-caps rule over live `shared.job_worker` rows is exact, stays in sync with the claim code, and keeps the 15-min threshold. |
| 8 (Booking) | Raise Booking's threshold above its largest `EXPECTED_SECONDS` | That would push stall detection past ~30 min. "0 while a non-overdue job is running" keeps 15 min, and overdue-running covers a stuck job. |
| 9 | Raise the Lambda timeout to 60 s and cap each path at ~10 s | Folding the sample into the existing handler is simpler: no Lambda re-zip (which also avoids the `__pycache__` lesson), no new path, $0.04/month less. |
