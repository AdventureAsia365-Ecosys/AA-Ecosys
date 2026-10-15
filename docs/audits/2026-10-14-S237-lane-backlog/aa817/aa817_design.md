# AA-817 step 1: role x table design notes (S237)

Status: draft for the orchestrator. The live facts marked **[probe]** are filled in from
`.tmp-session/s237/aa817_probe.py` once it has run on Dev. Everything else was read from the code at
`origin/main` 44443ec8 (worktree `.tmp-session/wt/s237-cis-817-probe`, branch
`chore/aa-817-role-matrix`).

Locked decision D2: migration 229 uses ENABLE ROW LEVEL SECURITY **without FORCE**, follows the
115/116/145 pattern, and the owner stays exempt.

---

## 1. How to run the probe

```bash
TMO=300 bash /home/nghiep/projects/AA-Ecosys/.tmp-session/s237/exec.sh /home/nghiep/projects/AA-Ecosys/.tmp-session/s237/aa817_probe.py > /home/nghiep/projects/AA-Ecosys/.tmp-session/s237/aa817_probe_out.json
```

- The probe is read-only. Everything runs in `BEGIN READ ONLY`, which is rolled back at the end.
  `SET LOCAL ROLE` and `set_config(..., true)` live inside savepoints, and each savepoint is rolled
  back too. The probe never grants or alters anything and never prints a password or a DSN.
- If the runner cannot `SET ROLE aa_app_user`, the probe falls back to a second read-only login
  through the existing secret `aa-cis/dev/rds-app-user`. That is the same DSN the API tenant pool
  uses (`api/core/aa544_tenant_pool.py:47`).
- The output is a single JSON line of about 40–80 KB. The container also keeps a copy at
  `/tmp/aa817_probe_out.json`, and uploads one to
  `s3://aa-cis-bronze-005097885195/scripts/out/s237_aa817_probe.json` (same prefix as the s209 schema
  dump). If the exec session cuts the line, read the S3 copy:
  `aws s3 cp s3://aa-cis-bronze-005097885195/scripts/out/s237_aa817_probe.json /home/nghiep/projects/AA-Ecosys/.tmp-session/s237/aa817_probe_out.json --profile aa365-admin --region us-west-1`
  and delete the S3 object afterwards.
- The probe was tested locally on a throwaway PG16 cluster with an RDS-like runner (NOSUPERUSER,
  NOBYPASSRLS, CREATEROLE, a member of catalog_owner). No fatal error. All paths ran: SET ROLE
  allowed, SET ROLE denied followed by the app-user login fallback, and errors caught per cell.

### Reading the output

| key | meaning |
|---|---|
| `main_secret_user`, `api_env_database_url_user` | The user names behind `aa-cis/dev/rds` and the container's `DATABASE_URL`. Task defs api:596 and worker:152 both map `DATABASE_URL` to `aa-cis/dev/rds` (checked read-only with `describe-task-definition`). DB Migrate also runs from the api task def, so **one role serves as API main pool, worker and migration runner**. |
| `identity` | `current_user`/`session_user`, `rolsuper`, `rolbypassrls`, `rolcreaterole`, `row_security`, server version |
| `membership_chain` | Every role the runner inherits (recursive), with the attributes of each. Look for `rds_superuser`, `catalog_owner` and any role with `rolbypassrls`. |
| `tables[]` | Per table or view: owner, `rls`, `force`, `tenant_col`, `rls_active_for_me` (`row_security_active()` for the runner), and the privileges of aa_app_user, tripplanner, booking and catalog_owner (`S/I/U/D`) |
| `policies[]` | `pg_policies` for the 7 schemas |
| `matrix_runner` / `as_role.<role>.matrix` / `app_user_login.matrix` | Per RLS table plus `tenant_tour_versions`, a cell `"rows/distinct tenants"` under app.tenant_id `unset` (reports the GUC it actually saw), `empty` `''`, `foreign` (random uuid), `master` and `own` (the busiest tenant of that table) |

### Settling the S236 question ("aa_cis_admin reads all of published_tours under a foreign tenant")

| matrix_runner pattern | mechanism | consequence for 229 |
|---|---|---|
| `foreign` > 0 on published_tours/raw_tours only, and 0 or ERR on the **other** FORCE tables (generated_content, seo_context, quality_scores, content_exports, webhook_deliveries, pipeline_runs) | The runner still **inherits catalog_owner**, so policy `catalog_owner_aa_master_read` (225) admits every master row. `membership_chain` should show catalog_owner with `inherits_privs=true`. 225 revokes this membership at the end of the file, and the lesson S236 entry was written while 225 was being applied, so this only fits if the revoke did not stick. | 229 is unaffected (no catalog_owner policy on tenant_tour_versions). Separate fix: `REVOKE catalog_owner FROM aa_cis_admin`, a 1-line migration, Nghiệp approves. ADR 0004a's "aa_cis_admin reads all of booking" gap is a different issue: it is about ownership and grants, not RLS. |
| `foreign` > 0 on **every** FORCE table and `rls_active_for_me=false` everywhere | A real bypass: some role in `membership_chain` has `rolbypassrls`, or RDS gives `rds_superuser` that semantic | ENABLE without FORCE behaves the same for the runner (it is exempt either way). D2 holds. Record this on AA-817, because then FORCE would not protect the main pool either. |
| `foreign` = 0 on FORCE tables and `rls_active_for_me=true` there | The runner is filtered by FORCE, which is the documented behaviour (225 header, `services/places/store.py:4-7`) | D2 holds. Owner exemption without FORCE is the only thing that keeps T2/admin working on tenant_tour_versions after 229. |

In every branch, 229 is safe only if the runner **owns** `gold_aa_internal.tenant_tour_versions`
(or holds BYPASSRLS). Check `tables[] gold_aa_internal.tenant_tour_versions.owner == identity.cu`.
If the owner is a different role, ENABLE without FORCE **filters the runner**. The T2 worker,
the admin lists and v1_tours would then all see 0 rows, so stop and redesign. 229 below asserts
this itself.

---

## 2. Code-path inventory: main pool (runner role) vs tenant pool (aa_app_user)

Pools:
- **Main pool**: `api/main.py:77` `asyncpg.create_pool(os.environ["DATABASE_URL"])` connects as the
  `aa-cis/dev/rds` user. The worker opens its own pool from the same secret at
  `shared/jobs/worker.py:323` `create_pool(get_database_url())`. One-off jobs and handlers do the
  same: `services/export/handler.py:82`, `services/content_generation/grounding.py:266`,
  `services/ingestion/jev_gates.py:112`.
- **Tenant pool**: `api/core/aa544_tenant_pool.py:51-65` `create_tenant_pool()` reads the
  `aa-cis/dev/rds-app-user` secret (max 5 connections). Access goes only through
  `acquire_scoped_conn()` (`:83-108`), behind one Redis flag per route. Fail-closed: when the flag
  is off, the route stays on the main pool.

### Already on the tenant pool (flag-gated)
| route | code | tables |
|---|---|---|
| GET /v1/publish-log/pending (Stage 1) | `api/routers/v1_publish.py:138` | content_piece, angle_gate_request, angle_gate_option, publish_log |
| GET /v1/content-writing/pieces/{id} (Stage 5) | `services/acp_content_writing/service.py:1910` | content_piece |

### Tenant (/v1, tenant JWT) routes still on the main pool, i.e. isolated only by WHERE
| group | code (file:line) | tenant tables touched | can move to aa_app_user? |
|---|---|---|---|
| Content-writing reads | `v1_content_writing.py:209` → `service.py:1868` fetch_latest_piece_for_request (`_CHOSEN_OPTION_QUERY` :1851, `_LATEST_PIECE_FOR_OPTION_QUERY` :1856) | content_piece (RLS 115), angle_gate_option (no tenant_id) | **Yes, cleanest next route.** Both tables are granted to aa_app_user (147). No published_tours join. |
| | `v1_content_writing.py:221` → `service.py:2146` fetch_review_list (`_TENANT_REVIEWS_QUERY` :2105) + `fetch_tenant_trips` | content_piece, angle_gate_request, angle_gate_option, **acp_contract.tour_atoms** | After a fix. tour_atoms has no grant to aa_app_user ([probe] `privs`). `fetch_tenant_trips` (`services/acp_planning/tenant_pool.py:142`) joins FORCE-RLS published_tours, so it must stay on the main pool. Split: the piece query goes on the tenant pool, the trips lookup stays on main. |
| | `v1_content_writing.py:234` → `service.py:2013` fetch_review → `acp_angle_gate/service.py:414` fetch_request | angle_gate_request, angle_gate_option, **acp_shared.subject, acp_contract.atom_segment, acp_contract.route** | After grants. subject/atom_segment/route are not granted to aa_app_user ([probe]). |
| | `v1_content_writing.py:120` PATCH /pieces/{id} → `service.py:1937` update_piece_content_text | content_piece UPDATE | Yes. A write through RLS has USING as an implicit WITH CHECK, and UPDATE is granted (147). Second route of the group. |
| | `v1_content_writing.py:54` POST write, `:94` UPDATE content_piece.job_id | content_piece | No. It enqueues a job, and the T9 write itself runs in the worker on the main pool. |
| Publish | `v1_publish.py:76` DELETE /{publish_id}, `:235` POST /{piece_id}/publish | publish_log, content_piece | Later. Writes plus integration secrets; lane cis-portal AA-815 touches unpublish. |
| T2 versions | `v1_tours.py:51` /pool, `:389` rewrite (INSERT :449), `:506` /my-versions, `:569` retry, `:610` /{id}/full, `:720`, `:750` /versions/{id}, `:801` export-docx, `:942` PATCH version, `:1005` approve | **tenant_tour_versions** (no RLS until 229) + published_tours / raw_tours (FORCE RLS, AA master rows) | Stage 2, after 229, and **only with a master-read path for aa_app_user**. Under aa_app_user with a tenant GUC, `tenant_isolation` hides every AA-master published_tours/raw_tours row, so every join to the master catalog returns nothing (this is the AA-578 note at `v1_marketplace.py:65-67`, `v1_route_hub.py:44-46`, `acp_planning/tenant_pool.py:50-52`, `acp_shared/slate.py:153-155`: "KHÔNG BAO GIỜ chuyển sang RLS pool"). Fix options: (a) a policy `aa_app_user_aa_master_read FOR SELECT TO aa_app_user USING (tenant_id = master)` on published_tours/raw_tours, mirroring catalog_owner's (225), or (b) read master content through `catalog.v_tour*`, which is already granted to aa_app_user (225). Option (a) is smaller. It needs its own migration (next free number after 231) and must not go into 229 (D2 scope). |
| Marketplace / route hub / planning / slate | `v1_marketplace.py:74`, `v1_route_hub.py:50`, `services/acp_planning/tenant_pool.py:59`, `services/acp_shared/slate.py:159` | tenant_tour_versions + published_tours | Same blocker as T2 versions. Wait for (a) or (b). |
| Progress | `shared/jobs/queue.py:566` (via `v1_progress.py`) | tenant_tour_versions by job_id | Stage 2. |
| Facts (tenant scope) | `services/acp_content_writing/facts.py:38` (read during T9 in the worker) | acp_shared.facts (RLS 145, platform rows shared) | Worker path, so it stays on main. No tenant /v1 facts route exists today. Lane backup item 6 assumed one; re-check before planning it. |
| Other /v1 | `v1_angle_gate.py` (4 main-pool uses), `v1_planning.py` (6), `v1_integrations.py` (6), `v1_pipeline.py` (4), `v1_trip_page.py` (3) | angle_gate_request, year/quarter plan, tenant_integrations, … | Not this session. Each one needs AA-544's report-then-confirm ritual. |

### Platform/admin and worker paths that must keep seeing every tenant (main pool; after 229 they rely on owner exemption)
- T2 worker writes: `services/jobs/t2_rewrite_job.py:229` (UPDATE rewritten content), `:298`
  (UPDATE status failed), `:316`, `:353` (SELECT). The INSERT comes from the API at `v1_tours.py:449`
  (tenant route, main pool).
- Admin reads: `api/routers/admin_content_quality.py:658`, `:692` (the tour-versions list, the
  smoke target after 229); `admin.py:75` (offboard / version helper), `:460`, `:757`, `:867`, `:888`,
  `:1161`; `admin_pipeline.py:3918`, `:3923`, `:3930`, `:4987`; `admin_tenant360.py:134`, `:150`;
  `admin_overview.py:130`.
- Portal AA-802 (lane cis-portal #5): admin UPDATE of a T2 sentence on tenant_tour_versions as the
  runner. With ENABLE and no FORCE, the owner is exempt, so nothing changes. With FORCE it would
  update 0 rows (the reason for D2).

---

## 3. Draft migration 229 (not committed; written after the probe confirms ownership)

```sql
-- Migration 229: AA-817 — RLS on gold_aa_internal.tenant_tour_versions (T2 tenant versions).
--
-- The largest tenant-owned table had no RLS at all (migrations 001/107/108/109/128/175/223 never
-- enabled it), so moving its reads to the tenant pool (aa_app_user, AA-544) would isolate nothing.
-- Decision D2 (S237): ENABLE without FORCE, the 115/116/145 pattern. The owner (the CIS runtime +
-- migration role behind aa-cis/dev/rds: API main pool, worker, DB Migrate) stays exempt, so the T2
-- worker, admin lists and every route still on the main pool are unchanged; aa_app_user is filtered.
-- Policy reads NULLIF(current_setting('app.tenant_id', true), '')::uuid like 225: a pooled
-- connection holds '' after any set_config(..., true) transaction, and '' must mean "no tenant"
-- (0 rows), never an "invalid input syntax for type uuid" error.
-- No FORCE: with FORCE the owner is filtered too, and the T2 worker / admin Content Quality /
-- v1_tours on the main pool would see 0 rows (cross-lane review S237).

BEGIN;

-- Guard 1: the runner must own the table (or bypass RLS); otherwise ENABLE alone filters it and
-- every main-pool reader of this table goes empty.
DO $$
DECLARE owner_ok boolean; bypass boolean;
BEGIN
    IF to_regclass('gold_aa_internal.tenant_tour_versions') IS NULL THEN
        RAISE EXCEPTION 'migration 229: gold_aa_internal.tenant_tour_versions does not exist';
    END IF;
    SELECT pg_has_role(current_user, c.relowner, 'USAGE') INTO owner_ok
      FROM pg_class c WHERE c.oid = 'gold_aa_internal.tenant_tour_versions'::regclass;
    SELECT rolbypassrls INTO bypass FROM pg_roles WHERE rolname = current_user;
    IF NOT owner_ok AND NOT bypass THEN
        RAISE EXCEPTION 'migration 229: % neither owns tenant_tour_versions nor has BYPASSRLS — '
                        'ENABLE RLS would hide every row from the main pool', current_user;
    END IF;
    -- row count BEFORE RLS, compared in guard 2 (a count taken after ENABLE could itself be filtered)
    PERFORM set_config('aa817.n_before',
                       (SELECT count(*) FROM gold_aa_internal.tenant_tour_versions)::text, true);
END $$;

ALTER TABLE gold_aa_internal.tenant_tour_versions ENABLE ROW LEVEL SECURITY;
-- deliberately NO "FORCE ROW LEVEL SECURITY" (D2)

DROP POLICY IF EXISTS tenant_isolation ON gold_aa_internal.tenant_tour_versions;
CREATE POLICY tenant_isolation ON gold_aa_internal.tenant_tour_versions
    USING      (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);
COMMENT ON POLICY tenant_isolation ON gold_aa_internal.tenant_tour_versions IS
    'AA-817 (229): tenant rows for the tenant pool (aa_app_user + app.tenant_id). Owner exempt (no FORCE).';

-- Tenant pool grants for the stage-2 routes (v1_tours: read, rewrite INSERT, PATCH edit, retry).
-- Cross-owner grant is not IF EXISTS-guarded (schema-ownership rule 5): aa_app_user must exist.
GRANT USAGE ON SCHEMA gold_aa_internal TO aa_app_user;
GRANT SELECT, INSERT, UPDATE ON gold_aa_internal.tenant_tour_versions TO aa_app_user;

-- Guard 2 (behavioural, lesson S236): the runner still sees every row under a foreign tenant,
-- and aa_app_user sees none.
DO $$
DECLARE n_all bigint; n_runner_foreign bigint; n_app_foreign bigint; n_app_empty bigint;
BEGIN
    n_all := current_setting('aa817.n_before')::bigint;
    PERFORM set_config('app.tenant_id', '00000000-0000-0000-0000-00000000dead', true);
    SELECT count(*) INTO n_runner_foreign FROM gold_aa_internal.tenant_tour_versions;
    IF n_runner_foreign <> n_all THEN
        RAISE EXCEPTION 'migration 229: runner sees % of % rows under a foreign tenant — it is filtered',
                        n_runner_foreign, n_all;
    END IF;
    IF row_security_active('gold_aa_internal.tenant_tour_versions') THEN
        RAISE EXCEPTION 'migration 229: RLS is active for the runner %', current_user;
    END IF;
    -- aa_app_user checks only when the runner may SET ROLE it (CI superuser yes; RDS maybe not —
    -- then the post-apply probe run covers it)
    IF pg_has_role(current_user, 'aa_app_user', 'MEMBER') THEN
        SET LOCAL ROLE aa_app_user;
        SELECT count(*) INTO n_app_foreign FROM gold_aa_internal.tenant_tour_versions;
        PERFORM set_config('app.tenant_id', '', true);
        SELECT count(*) INTO n_app_empty FROM gold_aa_internal.tenant_tour_versions;
        RESET ROLE;
        IF n_app_foreign <> 0 OR n_app_empty <> 0 THEN
            RAISE EXCEPTION 'migration 229: aa_app_user reads % (foreign) / % (empty) rows', n_app_foreign, n_app_empty;
        END IF;
    END IF;
    PERFORM set_config('app.tenant_id', '', true);
END $$;

INSERT INTO shared.schema_versions (version, applied_at, description)
VALUES ('229', now(),
    'AA-817: ENABLE RLS (no FORCE, owner exempt) + tenant_isolation (NULLIF GUC) on '
    'gold_aa_internal.tenant_tour_versions; SELECT/INSERT/UPDATE to aa_app_user')
ON CONFLICT (version) DO NOTHING;

COMMIT;
```

Notes on the draft:
- The draft was dry-run (`COMMIT` swapped for `ROLLBACK`) on a throwaway PG16 cluster with a
  stand-in table holding 5 rows from 2 tenants:
  - as a superuser: passes;
  - as an RDS-like owner (NOSUPERUSER, NOBYPASSRLS): passes;
  - as that owner with aa_app_user membership, so the aa_app_user branch runs: passes, with
    aa_app_user reading 0 rows under foreign and 0 under empty;
  - as a non-owner: guard 1 raises;
  - with a `FORCE` line added: guard 2 raises "runner sees 0 of 5 rows".
- `SET LOCAL ROLE` inside a `DO` block is allowed (225 uses `SET LOCAL ROLE catalog_owner` the same
  way). If the plpgsql `SET LOCAL ROLE` form is rejected, use
  `PERFORM set_config('role', 'aa_app_user', true)`.
- No DELETE grant. Tenants do not delete versions today. Offboard (`admin.py`) runs on the main
  pool.
- Apply 229 in a window with no `t2_rewrite` job queued or running (cross-lane note). Afterwards,
  smoke one T2 job (cheap trial tour) and `GET /admin/content-quality/...` (the tour-versions list
  at `admin_content_quality.py:658`). Rerun the probe and expect: runner
  `tenant_tour_versions.foreign == unset`; aa_app_user `foreign=0/0`, `empty=0/0`, `own=n/1`.
- Flow D8: a PR with only the migration file goes to AA-CIS-App main, then a byte copy goes to
  `AA-CIS-Infra/db/migrations/cis/229_*.sql`, then DB Migrate `check` → `apply`, then the schema
  reference is regenerated, then the code PR (stage-2 routes) follows.

### CI caveat for 229
The CI DB has **no** `gold_aa_internal.tenant_tour_versions`. Migration 001 is skipped, so
107/108/109/128/175/223 have always failed silently in CI (see `test_aa766_tenant360_sql.py:3-9`).
229 would fail silently in CI too, because its guard 1 raises. The 229 PR should therefore:
1. Make `tests/integration/conftest.py` pre-create `gold_aa_internal.tenant_tour_versions` in its
   live shape (`docs/architecture/db-schema-reference.md:1258`) before the migration loop, the same
   way it pre-creates `shared.destinations` for 198. 107/…/223/229 then apply for real. Check that
   test_aa766/797/798, which create their own stand-ins with `IF NOT EXISTS`, still pass.
2. Add `"gold_aa_internal.tenant_tour_versions": False` to `TENANT_TABLES` in
   `tests/integration/test_aa817_rls_tenant_isolation.py` (this branch) and seed one row per tenant
   in `_seed`.
3. Optionally re-apply 229 as an RDS-like runner (NOSUPERUSER, NOBYPASSRLS, owner), following the
   `test_aa679_catalog_views.py` `rds_like_225` fixture, so that guard 1 and guard 2 run the way
   they will on Dev.

---

## 4. CI guard

Shipped on this branch: `tests/integration/test_aa817_rls_tenant_isolation.py`. As `aa_app_user`,
with app.tenant_id set to the own tenant, the other tenant, a forged uuid or `''`, a **WHERE-less**
`SELECT DISTINCT tenant_id` on angle_gate_request, content_piece, publish_log and facts returns
only the own tenant's rows. For facts, platform rows (NULL tenant) are also returned, by design. It
also checks that aa_app_user is not super/bypass, owns none of the tables and has SELECT.
Write side (added in review, for the PATCH /pieces/{id} route): a WHERE-less UPDATE as aa_app_user
touches only the own tenant's row (0 under a forged uuid or `''`); handing a row to another tenant
and INSERTing a row for another tenant (or with `''`) are refused by the policy's implicit WITH
CHECK. Local run: 10 passed, 1 xfailed (strict, the facts write gap in section 5). Mutation checks:
115 policy `USING (true)` fails the content_piece read case; `WITH CHECK (true)` on 113 fails the
angle_gate_request write and insert cases.

Next guard (proposed, not built): a **"new tenant table without RLS" catalog test**. Enumerate
every table with a `tenant_id` column in gold_aa_internal, silver_aa_internal, acp_shared,
acp_contract and shared. Assert that it has `relrowsecurity` and a policy whose qual references
`app.tenant_id`, or that it is in an explicit `NO_RLS_ALLOWLIST = {table: reason}` (for example
`shared.tenants`: the registry itself; `shared.llm_call_log`: platform cost log, admin only;
`shared.jev_tenant_allowlist`: admin config). A new tenant-owned table then has to choose RLS or
justify itself in review. That is the gap 229 closes for tenant_tour_versions. Because the CI DB
misses some live tables, run the same check against Dev in the schema-dump step
(`s209_schema_dump.py`), and have the dump list `tenant_id` tables without RLS so the gap shows up
in `db-schema-reference.md`.

---

## 5. Gaps found while reading (not fixed here)
- Policies 004/008 on generated_content, seo_context, quality_scores, content_exports,
  webhook_deliveries and pipeline_runs still cast `current_setting(...)::uuid` without NULLIF. With
  the GUC at `''` (a pooled connection), a non-exempt reader gets
  `invalid input syntax for type uuid` instead of 0 rows (seen in the local run). This does not
  matter until a route on the tenant pool reads them. When one does, extend 225's NULLIF loop to
  them.
- `acp_shared.angle_gate_option` has no tenant_id and no RLS (113, "isolated via its parent").
  On the tenant pool, a query that reaches an option by id without going through
  angle_gate_request can read another tenant's option text. Today every query joins through
  content_piece or angle_gate_request.
- `aa_app_user` has no grant on `acp_contract.tour_atoms`, `acp_shared.subject`,
  `acp_contract.atom_segment` or `acp_contract.route` (the AA-544 stage-0 note chose this on
  purpose). These need grants before `GET /v1/content-writing/reviews` and `/requests/{id}/review`
  can move.
- **acp_shared.facts write gap (found in review, pinned by a strict xfail in the CI guard).**
  Policy 145 is `FOR ALL USING (scope = 'platform' OR tenant_id = GUC)` with no separate WITH CHECK,
  and 147 grants INSERT/UPDATE on facts to aa_app_user. So the tenant role can UPDATE every platform
  fact and INSERT new `scope = 'platform'` facts, which every tenant's T9 then cites. Latent: no
  tenant-pool route writes facts today. Fix before any tenant facts route moves to the pool: split
  the policy (SELECT keeps the platform branch; INSERT/UPDATE check `scope = 'tenant' AND
  tenant_id = NULLIF(GUC, '')::uuid`) or revoke INSERT/UPDATE from aa_app_user. Separate migration
  (not 229, D2 scope); drop the xfail in the same PR.
- ADR 0004a ("aa_cis_admin reads all of booking") stays a documented known gap. Neither 229 nor
  this slice changes the runtime role.
