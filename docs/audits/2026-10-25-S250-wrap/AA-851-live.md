# AA-851 — live verification (S250, read-only, no ECS exec)

Scope checked: `shared.countries` (ISO 3166-1), `country_iso2` on `silver_aa_internal.raw_tours` and
`shared.destinations`, `catalog.v_country`, `catalog.v_destination.country_iso2`, orphan report
`shared.v_country_unmapped`. CIS migration 279, applied on Dev.

Sources used (no database session was opened by this check):

- Root `docs/architecture/db-schema-reference.md` on `origin/master` @ `d79eec7` (bot PR #244, merged
  2026-10-25 04:34 UTC). Verified line: **2026-10-25 03:17 UTC**, latest CIS migration **280** (so 279 is included).
- AA-CIS-Infra DB Migrate run 40157371485 (job "Migrate (dev apply cis/279_countries_iso3166.sql)", success).
- AA-CIS-App `origin/main` @ `8952afa3` (code grep), `docs/implementation-notes/AA-851.md`.
- Root `docs/contracts/catalog.country.v1.json`, `docs/database/schema-ownership.md`.

## 1. Apply evidence (DB Migrate log, run 40157371485)

```
MIGRATE file=cis/279_countries_iso3166.sql version=279 sha256=16240732fe22 mode=apply
MIGRATE directives: transaction=yes destructive=no lock_timeout=5s statement_timeout=15min
MIGRATE ran as: cis_owner ... SET ROLE cis_owner for this file
MIGRATE before: latest_registered_same_owner=278 this_version_applied_at=None
MIGRATE idle: shared.job running=0 queued=0 / booking.job 0/0 / crm.job 0/0 / shared.rerun_wave open=0
MIGRATE after: applied_at=2026-10-25 03:13:40.526694+00:00
exit code: 0  status: STOPPED
```

The migration's NOTICE lines (mapped / total per table, unmapped values) are not in the GitHub job log (the
runner prints only the MIGRATE summary), so the orphan numbers still need the SQL in section 5.

Follow-ups dispatched by that run: DB Isolation Probe 40157461956 and 40157567108 — **success**. DB Schema Dump
40157460313 / 40157565576 — conclusion "failure", but only at the last step "Design ERD drift (report)"
(`tripplanner: 2 drift finding(s)`); dump, render and "Open or update the root PR" steps passed and produced PR #244.
That failure is unrelated to AA-851.

## 2. Structure in the live dump (db-schema-reference.md, Verified 03:17 UTC)

| Object | What the dump shows |
|---|---|
| `shared.countries` | table, **~249 rows** (reltuples), cols `iso2` PK, `iso3` UNIQUE, `numeric_code` UNIQUE, `name` UNIQUE, `iso_name`, `aliases text[]`; CHECKs on code shape / lower-case aliases; owner `cis_owner`; grants `catalog_owner` SELECT, `cis_app` SELECT |
| Table activity row | `shared.countries` — ~rows 249, ins / upd / del **249 / 0 / 0** |
| `silver_aa_internal.raw_tours.country_iso2` | `character(2)`, index `raw_tours_country_iso2_idx`, FK → `shared.countries.iso2`, trigger `raw_tours_country_iso2` BEFORE INSERT OR UPDATE OF country → `shared.set_country_iso2()` |
| `shared.destinations.country_iso2` | `character(2)`, index `destinations_country_iso2_idx`, FK → `shared.countries.iso2`, trigger `destinations_country_iso2` (same function) |
| `shared.country_iso2(text)` / `shared.set_country_iso2()` | functions owned by `cis_owner`, not SECURITY DEFINER |
| `shared.v_country_unmapped` | view (`source`, `country`, `row_count`), owner `cis_owner`, grant `cis_app` SELECT |
| `catalog.v_country` | view (`iso2`, `iso3`, `numeric_code`, `name`, `iso_name`), owner `catalog_owner`, grants **`booking` SELECT, `tripplanner` SELECT** |
| `catalog.v_destination` | last column `country_iso2 character(2)`; grants `aa_app_user`, `booking`, `tripplanner` SELECT |
| schema `catalog` | USAGE for `booking`, `tripplanner`, `aa_app_user`, `catalog_owner` |
| Migration register | `279 | 2026-10-25 03:13:40 | AA-851: shared.countries (ISO 3166-1, 249 rows), country_iso2 on raw_tours and shared.destinations (trigger + backfill, orphan report shared.v_country_unmapped), catalog.v_country and catalog.v_destination.country_iso2` |

## 3. API exposure (CIS `origin/main`)

No CIS endpoint exposes `country_iso2` or countries today. `git grep country_iso2` hits only `CONTEXT.md`, the
migration, the implementation notes and the integration tests (`tests/integration/test_aa851_migration_279.py`).
The catalog HTTP reader (`services/catalog_http/reader.py`) selects `destination_id, name, country, lat, lng` from
`catalog.v_destination` — not `country_iso2`. This matches the design: `v_country` is not granted to `aa_app_user`
until `catalog.http.v1` serves countries (implementation notes, AA-859 rule). So there is no live HTTP check to run.

## 4. Linear Done-when vs evidence

Note: the issue text says `catalog.v_countries` / `v_destinations`; the shipped names are **`catalog.v_country`**
and **`catalog.v_destination.country_iso2`** (singular, like every catalog view; DM-2), recorded in
`docs/implementation-notes/AA-851.md` ("v_countries is named catalog.v_country").

| Done-when item | Verifiable here? | Evidence | Status |
|---|---|---|---|
| `SELECT count(*) FROM shared.countries` = 249 | Indirect only | Dump: ~249 rows (reltuples) and pg_stat ins/upd/del 249/0/0; migration register text "249 rows" | Strongly indicated; exact count = SQL below |
| `SELECT * FROM catalog.v_country LIMIT 5` returns rows as `booking` | Privileges yes, rows no | Dump: `catalog.v_country` grant `booking` SELECT, schema `catalog` USAGE `booking`; view owner `catalog_owner` has SELECT on `shared.countries` | Needs the role query (master) |
| same as `tripplanner` | Privileges yes, rows no | Same, grant `tripplanner` SELECT | Needs the role query (master) |
| Scope: seeded `shared.countries` (alpha-2, alpha-3, name) | Yes | Section 2 | Done |
| Scope: catalog contract views + grants | Yes | Section 2 (`v_country`, `v_destination.country_iso2`) | Done |
| Scope: Infra byte copy, DB Migrate, schema reference regenerated | Yes | Run 40157371485 apply success; PR #244 merged with Verified 03:17 UTC, CIS 280 | Done |
| Scope: contract doc in root `docs/contracts/` | Yes | `docs/contracts/catalog.country.v1.json` + 3 samples (root PR #247); ownership + DM-7 rows in `schema-ownership.md` | Done |
| S241 extension: backfill, orphan report empty | No (needs data) | View exists and is granted to `cis_app` | SQL below |

## 5. Read-only SQL for the orchestrator

A. ECS exec, container `DATABASE_URL` (role `cis_app` — has SELECT on `shared.countries`, `shared.v_country_unmapped`,
`shared.destinations`, and the `raw_tours_cis_app_all` policy so it sees every raw_tours row), one line:

```sql
SELECT (SELECT count(*) FROM shared.countries) AS countries, (SELECT count(*) FROM shared.v_country_unmapped) AS unmapped_groups, (SELECT coalesce(sum(row_count),0) FROM shared.v_country_unmapped) AS unmapped_rows, (SELECT count(*) FROM silver_aa_internal.raw_tours WHERE country_iso2 IS NULL) AS raw_tours_null_iso2, (SELECT count(*) FROM silver_aa_internal.raw_tours WHERE country IS NOT NULL AND country_iso2 IS NULL) AS raw_tours_orphans, (SELECT count(*) FROM shared.destinations WHERE country_iso2 IS NULL) AS destinations_null_iso2, (SELECT count(*) FROM shared.destinations WHERE country IS NOT NULL AND country_iso2 IS NULL) AS destinations_orphans, has_table_privilege('booking','catalog.v_country','SELECT') AS booking_can_read, has_table_privilege('tripplanner','catalog.v_country','SELECT') AS tripplanner_can_read;
```

Expected: `countries = 249`, `unmapped_groups = 0`, `unmapped_rows = 0`, both `*_orphans = 0`,
`*_null_iso2` = rows whose `country` is NULL (raw_tours `country` is nullable; `destinations.country` is NOT NULL per
AA-712, so `destinations_null_iso2` should equal `destinations_orphans` = 0), both `*_can_read = true`. If
`unmapped_groups > 0`, also run `SELECT * FROM shared.v_country_unmapped ORDER BY row_count DESC;` (each row = an
alias to add in a new migration).

B. Done-when rows as the consumer roles: `cis_app` is not a member of `booking` / `tripplanner`, so this needs the
master via AA-CIS-Infra DB Migrate `mode=run-script` (never ECS exec):

```sql
SET ROLE booking; SELECT iso2, iso3, name FROM catalog.v_country ORDER BY iso2 LIMIT 5; SELECT count(*) FILTER (WHERE country_iso2 IS NOT NULL) AS with_iso2, count(*) AS total FROM catalog.v_destination; RESET ROLE; SET ROLE tripplanner; SELECT iso2, iso3, name FROM catalog.v_country ORDER BY iso2 LIMIT 5; RESET ROLE;
```

Expected: 5 rows each (`AD`, `AE`, `AF`, `AG`, `AI` in ISO order), and `with_iso2 = total`.

## Not verified here

- Exact row counts, orphan report contents, and NULL `country_iso2` counts (no DB access from this agent).
- Rows actually returned to `booking` / `tripplanner` (privileges are confirmed from the dump; the SELECT itself is not).
- The trigger firing on a new write (covered by `tests/integration/test_aa851_migration_279.py` in CI, not live).
