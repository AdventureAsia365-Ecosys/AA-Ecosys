# AA-859 implementation plan: tenant pool wave 2 (revised after critique)

Architect: Claude Code. Base: AA-CIS-App `main` b478a18b (migrations up to 240), AA-CIS-Infra 684a88a. Live grants and RLS come from `.tmp-session/s240/grants.json`, **with one known blind spot** (see D1): that probe reads `information_schema.role_table_grants`, which hides grants whose grantor is a role the runner is not a member of (`catalog_owner`). This plan was written read-only: nothing was run against AWS, the DB, GitHub, Linear or Notion.

**Re-checked in code for this revision** (in addition to the draft's list):
- `225_catalog_views.sql:389-392` and `228_catalog_place_graph_views.sql:447-451` grant SELECT on every `catalog.v_*` view (owner `catalog_owner`, all `security_barrier`) to `aa_app_user, tripplanner, booking`. `grants.json` (48 rows) has no `catalog.*` row: confirmed blind spot.
- `acp_contract.tour_atoms` has no RLS today; grants are `catalog_owner` SELECT and a `tripplanner` column grant (`db-schema-reference.md:260+`). The catalog views join it with no `owner_scope` filter (`225:257-258`, `228:143-144`, `235:54-55`); only the parent tour is master-filtered.
- `test_aa817_rls_tenant_isolation.py`: `test_owner_still_sees_every_tenant` uses `count(DISTINCT tenant_id)` (`:221`), `WRITE_TABLES = TENANT_TABLES - DELETE_ONLY_TABLES` (`:228`), `test_forged_tenant_writes_no_foreign_rows` runs `UPDATE … SET tenant_id = tenant_id` (`:245`), `NO_RLS_NO_WRITE_TABLES` (`:82`) feeds `test_tenant_role_cannot_write_tables_without_rls` (`:415-422`).
- `conftest.py:40-50` `TTV_STANDIN_DDL` has no `version_number`, `parent_version_id`, `edited_at`, `edited_by_user`, `job_id`.
- `v1_content_writing.py:57-98` enqueue + `content_piece.job_id` UPDATE; `v1_planning.py` `POST /slate/refresh` calls `request_slate_proposal` on the main pool; `/v1/billing` reads `shared.v_tenant_monthly_usage` (`_billing.py`), `/v1/quota` in `v1_tours.py:169+`.
- Disconnect tests that encode the old order: unit `test_aa817_fail_closed_routes.py:252, 267, 285, 296, 320, 331`; integration `test_aa817_tenant_pool_routes.py:167, 183`. `test_aa497_reopen_angle.py:30` calls `reopen_request(TENANT_ID, REQUEST_ID, pool)`.

---

## 0. Decisions

### Decisions Nghiệp must make (asked once, at the start of the relevant step)
| # | Question | When | Default if he says nothing |
|---|---|---|---|
| Q1 (D3) | Close the tenant-JWT branch of `/admin/atoms` (403) instead of moving it to the tenant pool, as AA-859 item 4 literally asks | Before PR-J | PR-J waits |
| Q2 (D6) | Re-scope AA-859's Done-when to items 1, 5, 6, W9 connect/test, `/admin/atoms`, and open two follow-up issues (wave 3, wave 4); Linear quota check first | End of S240 | AA-859 stays In Progress |
| Q3 (D4) | Retire the route hub (`/v1/routes`, `/v1/hubs`, `/v1/route-picks`) instead of moving it | Start of wave 4 | Keep and move |
| Q4 (new, D9) | If P0 finds tenant-owned atoms on live master tours: accept that `catalog.*` exposes them (as today, to TP/Booking too) or open a catalog-contract issue to filter `owner_scope = 'platform'` in the views | After P0 | Document, no change |

### D1. Item 5 becomes one rule in one migration (241), scoped to what CIS owns
**The rule after 241:** aa_app_user holds no privilege on any relation without RLS (tables, partitioned tables, views, matviews, foreign tables, including column privileges), **except** the cross-app catalog contract: relations owned by `catalog_owner` in schema `catalog`, SELECT only (225/228 design, asserted by `test_aa679:159-164`, `test_aa712_228:228, :455, :523`).

- 241's loop only touches relations the runner can act for: `pg_has_role(current_user, c.relowner, 'USAGE')` **and** owner not in `{catalog_owner, tripplanner, booking}` (the explicit exclusion is needed because the CI runner is a superuser, for whom `pg_has_role` is always true).
- Why: on Dev, `aa_cis_admin` is deliberately not a member of `catalog_owner` (225 `REVOKE catalog_owner FROM CURRENT_USER`, `228:495`, `test_aa679:192`). `REVOKE ALL ON catalog.v_tour FROM aa_app_user` as `aa_cis_admin` would either fail ("permission denied") or revoke nothing, and the guard would raise. Either way the apply would fail. Giving the runner `catalog_owner` membership to "fix" that is rejected: it breaks the documented catalog read contract.
- A non-owner REVOKE silently skips aclitems granted by someone else. So guard 0 also requires every in-scope aclitem's grantor to be a role the runner can act for, and raises otherwise (a human looks).
- Sequences (`relkind 'S'`) are out of the rule: they hold no tenant data, and some INSERTs may need USAGE.
- On Dev, these lose every privilege (from `grants.json`, confirmed by P0 #1 before the header is written):
  - every non-RLS `shared.*` table: tenants (`api_key_hash`), tenant_brand_rules, tenant_seo_config, tenant_export_config (`auth_header`), llm_call_log, llm_model_catalog, decision_log, dfs_call_log, jev_tenant_allowlist, unmapped_market_requests, tenant_rewrite_usage, job, the platform tables, tenant_brand_rules_deleted_aa404;
  - the views `v_destination_photos`, `v_tour_photos`, and the owner-rights `acp_contract.v_active_tour_atoms` (owner `aa_cis_admin`, so in scope);
  - `acp_shared.tenant_atom_state`, `year_plan`, `marketplace_portfolios` (which loses I/S/U).
- **Not touched:** the 13 `catalog.v_*` views (SELECT stays, owner `catalog_owner`).
- **Safe today:** the tenant pool's only reads are publish_log, content_piece, angle_gate_request (RLS), tenant_integrations (RLS) and angle_gate_option, which gets RLS in the same file (`v1_publish.py:98-114`, `:262-285`; `service.py:2071-2175`). No current tenant-pool route reads `catalog.*`. Only the API tenant pool logs in as `aa-cis/dev/rds-app-user`.
- Revoking `v_active_tour_atoms` in 241 matters for later: 243 grants USAGE on `acp_contract`, which would otherwise switch on an unfiltered all-tenant atom read.
- **The invariant query** (one SQL text, shared by 241 guard 4, the CI test and probe v3 verdict, kept in `tests/integration/_rls_fixture_helpers.py` and copied byte-for-byte into the probe):

```sql
-- rows returned = violations
SELECT c.oid::regclass AS rel, a.privilege_type, (att.attname IS NOT NULL) AS column_level
  FROM pg_class c
  JOIN pg_namespace ns ON ns.oid = c.relnamespace
  LEFT JOIN pg_attribute att ON att.attrelid = c.oid AND att.attacl IS NOT NULL
  CROSS JOIN LATERAL aclexplode(COALESCE(att.attacl, c.relacl)) a
 WHERE c.relkind IN ('r','p','v','m','f')
   AND NOT c.relrowsecurity
   AND ns.nspname NOT IN ('pg_catalog','information_schema') AND ns.nspname NOT LIKE 'pg_toast%'
   AND a.grantee = 'aa_app_user'::regrole
   AND NOT (ns.nspname = 'catalog' AND c.relowner = to_regrole('catalog_owner')
            AND att.attname IS NULL AND a.privilege_type = 'SELECT');
```
(The guard version also UNIONs the table-level `aclexplode(c.relacl)` rows when column ACLs exist, so neither level hides the other; the exact text is fixed in PR-B and reviewed with the test.)

### D2. Documented MAIN exceptions
Each one gets a code comment `# AA-859 MAIN exception: <reason>` and a row in CONTEXT.md.

| Exception | Why |
|---|---|
| `write_audit_log` / audit_log inserts (W2, W4, publish, connect, trip-reallocation confirm, subject pick) | No RLS on audit_log, and it never will be granted. Runs after the tenant transaction commits, best-effort, with a log. |
| Enqueue paths: POST `/v1/angle-gate/requests/{id}/goal`, POST `/v1/tours/pool/{id}/rewrite`, POST `/v1/tours/versions/{id}/retry`, **POST `/v1/content-writing/requests/{id}/write`** (enqueue + `content_piece.job_id` UPDATE, `v1_content_writing.py:57-98`), **POST `/v1/slate/refresh`**, the `request_slate_proposal` part of GET `/v1/slate` | The UPDATE/INSERT and the shared.job enqueue share one transaction (advisory lock). Splitting them breaks the atomicity. |
| Job-status lookups (`fetch_request` → `last_generation`, slate `last_proposal`, W5 `job_status`) | shared.job has no tenant column (tenant only in `payload`) and is worker-hot. Read on MAIN, keyed by request_id / job_id values first obtained through RLS on the tenant pool. |
| Tenant self-config and usage reads: `shared.tenants` (`daily_publish_limit`, `posts_per_week`), `acp_shared.tenant_config`, **GET `/v1/quota`** (`tenant_rewrite_usage`), **GET `/v1/billing`** (`shared.v_tenant_monthly_usage`, no grant) | Single-tenant lookup on the JWT `sub`, done on MAIN. Avoids RLS on `shared.tenants` (223k seq scans, used by auth). A unit test asserts that each helper's SQL filters on `tenant_id = $1`. |
| `fetch_request` re-read after choose/reopen (until wave 4) | It reads subject / atom_segment / route / alias, which have no grant until 243. Ownership is proven inside the tenant transaction (the RLS-filtered `FOR UPDATE` returned the row). |
| Staff branches: `/admin/brand-identity` with X-Admin-Secret (master tenant; BFF `pipeline/brand-identity/route.ts` is staff-only), the `/v1/tours/{id}/full` admin branch | Admin is out of the tenant boundary. |
| `/admin/brand-identity/upload` and `/parse` | No DB access. |
| `check_saved_cta` → `notify_admins` | Platform notifications, best-effort. |
| `/admin/atoms` recompute enqueue + decision_log stamp | Admin-only after PR-J. |

### D3. `/admin/atoms`: close the tenant-JWT branch (PR-J), **subject to Q1**
- No portal caller remains since AA-526 (`portal/layout.tsx:31`). The admin BFF (`frontend/app/api/admin/[...path]/route.ts`) sends only X-Admin-Secret.
- Closing the branch removes the only tenant write on tour_atoms, so 244 needs `FOR SELECT` only.
- This deviates from AA-859 item 4's text ("move to the tenant pool"), so it goes to Nghiệp (Q1) and into the Done-when re-scope (Q2).
- To honour "each route group behind its own Redis flag", the 403 sits behind `ADMIN_ATOMS_STAFF_ONLY_FLAG` / `aa859:admin_atoms_staff_only`, **fail closed = staff-only** (if Redis is unreadable, a tenant bearer gets 403). Rollback is `DEL` of the key, not a redeploy. After a week of no tenant callers in logs, a later PR removes the dead branch and the flag.
- Pre-flight P0 counts `owner_scope <> 'platform'` rows, for the record.

### D4. Route hub: retire, don't move (Q3, at the start of wave 4)
Unchanged: `/v1/routes`, `/v1/hubs`, `/v1/route-picks` have no portal consumer; `/v1/routes` already passes a tuple into `$2::text[]` (`v1_route_hub.py:92`, `slate.py:185`). Retiring drops `route_pick` RLS, `tenant_seo_config` reads and the `unmapped_market_requests` write-in-read-path. If kept, they move in wave 4 with the write moved to MAIN after commit.

### D5. Pool sizing (revised)
See §2. Tenant pool max 1 → 2, api autoscale max 10 → 7. **The main pool stays at 10 in S240.** Shrinking it waits until wave 4 has moved the bulk of tenant reads and main-pool wait has been measured.

### D6. Session scope
See §4. S240 does items 5, 6, W2/W3/W4/W6 (+ W5 if time), W9 connect/test, and `/admin/atoms` (if Q1 yes). Wave 3 (brand identity + publish) and wave 4 (atoms / subject / planning) become follow-ups (Q2).

### D7. Flags
- Each flag is a named constant in `aa544_tenant_pool.py`, placed after line 59. Redis key prefix `aa859:`. Every call site uses `fail_closed=True`. Each moved route logs one event with `used_tenant_pool=`.

| Constant | Redis key | Route group | Depends on 241 grants |
|---|---|---|---|
| `PIECE_EDIT_FLAG` | `aa859:piece_edit_pool` | W2 | no |
| `T2_VERSION_WRITE_FLAG` | `aa859:t2_version_write_pool` | W6 | no |
| `ANGLE_GATE_DECIDE_FLAG` | `aa859:angle_gate_decide_pool` | W3 choose + reopen | **yes** |
| `UNPUBLISH_FLAG` | `aa859:unpublish_pool` | W4 | no |
| `T2_VERSION_READS_FLAG` | `aa859:t2_version_reads_pool` | W5 | no (job status on MAIN) |
| `INTEGRATION_CONNECT_FLAG` | `aa859:integration_connect_pool` | W9 GET / POST / test | **yes** |
| `ADMIN_ATOMS_STAFF_ONLY_FLAG` | `aa859:admin_atoms_staff_only` | item 4 `/admin/atoms` | no |
| `PUBLISH_FLAG` | `aa859:publish_pool` | W9 publish (follow-up) | 242 |
| `BRAND_IDENTITY_FLAG` | `aa859:brand_identity_pool` | brand identity (follow-up) | 242 |
| wave 4: `ANGLE_GATE_READ_FLAG`, `SLATE_READS_FLAG`, `SUBJECT_DECIDE_FLAG`, `TRIP_REALLOCATION_FLAG`, `MARKETPLACE_FLAG`, `REVIEWS_FLAG` | `aa859:<name>_pool` | follow-up | 243/244 |

The "depends on 241" column is what the 241 rollback must turn off first (PR-B header).

### D8. Flip ritual (unchanged from AA-544 / AA-817)
1. Report the order and the route to Nghiệp, and wait for his confirmation.
2. Flip with the S3-mediated ECS exec script (based on `.tmp-session/s239/aa817_flags.py`): GET, SET `"true"`, GET, output written to S3.
3. Curls for tenant A and tenant B.
4. Logs Insights q3 shows `used_tenant_pool=True`.
5. Revert = `DEL` the key.

⚠️ The flag script contains underscore env vars (the Redis host env). Edit it manually in VSCode.

### D9. Catalog views and tenant-owned atoms (new, from critique)
The catalog views run with `catalog_owner`'s rights and join `tour_atoms` with no `owner_scope` filter. Any tenant-owned atom attached to a live master tour is visible through `catalog.v_tour_place` / `v_tour_component` to aa_app_user, tripplanner and booking **today**; AA-859 does not create this, but 244's `tenant_isolation` on tour_atoms cannot close it while D1 keeps the catalog SELECT.
- P0 #2 measures it (count of non-platform atoms on live master tours, and how many reach `catalog.v_tour_place` / `v_tour_component`).
- 0 → document in CONTEXT.md and add a 244 guard + probe check that keeps it at 0.
- > 0 → Q4. A view change is a cross-app catalog contract change (TripPlanner, Booking) and needs a root ADR, so it is not done inside AA-859.

---

## 1. Ordered PR list

Conventions:
- CIS repo `AdventureAsia365-Ecosys/AA-CIS-App`, Infra repo `AA-CIS-Infra`.
- Every commit and PR body carries `Refs AA-859` (never `Fixes`/`Closes`).
- Each PR stays under about 600 changed lines, tests included, **unless** splitting would leave `main` with red CI (PR-B).
- Flags default to off, so code PRs can be deployed in batches. Only flips are one at a time.

### PR-0 (pre-flight, no repo change): read-only probe P0 on Dev
S3-mediated ECS exec (asyncpg, `ssl="require"`, output to S3, read only after `wc -c` / `json.loads`). One READ ONLY transaction, rolled back. It records:
1. **From `pg_class.relacl` / `pg_attribute.attacl` via `aclexplode`, not `information_schema`:** every aclitem of aa_app_user and PUBLIC on every relation with `NOT relrowsecurity`, with **owner, grantor, schema, relkind, column**. Classified as: (a) 241 will revoke, (b) catalog contract (kept), (c) out of 241's reach and not catalog → must be empty, otherwise 241 is rewritten before merge. PUBLIC grants in schemas where aa_app_user has USAGE are listed separately (input to guard 0).
2. `tour_atoms`: `owner_scope` distribution (platform / canonical lower-case uuid / non-canonical / orphan with no `shared.tenants` row), **plus D9: non-platform atoms on live master tours, and how many appear in `catalog.v_tour_place` / `v_tour_component`.**
3. `angle_gate_option` per tenant through its parent; `tenant_tour_pages` distinct tenant_id; `subject` / `quarter_plan` per tenant.
4. `pg_stat_activity` grouped by `application_name` (cis-api / cis-tenant / cis-worker / tripplanner / booking): the D5 baseline.
5. `shared.job` queued / running count, which must be 0 before any DB Migrate apply.

Also rewrite `.tmp-session/s240/grants_probe.py` on `aclexplode` so later runs do not repeat the blind spot. Output to `docs/audits/2026-10-16-S240-aa859/p0_preflight.json` (root PR at session end).

### PR-A: CIS `fix: tenant disconnect without holding the tenant connection across Secrets Manager`
Size M (~400 lines). No migration. Existing flag `INTEGRATION_DISCONNECT_FLAG`. Item 6, plus groundwork for D5.

**Files**
- `api/routers/v1_integrations.py`: `_disconnect` (`:535-583`), `_get_secret` / `_put_secret` callers, credential readers.
- `api/core/aa544_tenant_pool.py`: wait / hold timing, `UUID(tenant_id)` validation.
- `tests/unit/test_aa817_fail_closed_routes.py`, `tests/integration/test_aa817_tenant_pool_routes.py`, new `tests/unit/test_aa859_tenant_pool_reentrancy.py`.

**New `_disconnect` design** (single design that fixes both follow-ups)
1. `acquire_scoped_conn` #1: `SELECT secret_key, updated_at FROM shared.tenant_integrations WHERE tenant_id = $1::uuid AND integration_type = $2`. Release.
   - No row → 200 `{"disconnected": false}`.
2. Tombstone with **no connection held**: `await asyncio.to_thread(_tombstone, secret_key)` with the bounded `_TOMBSTONE_SM_CONFIG`.
   - Failure → 502. Row and credentials stay intact.
3. `acquire_scoped_conn` #2: `DELETE … WHERE tenant_id = $1::uuid AND integration_type = $2 AND updated_at = $3 RETURNING secret_key`.
   - A row → 200 `disconnected=true`.
   - 0 rows → re-SELECT in the same transaction:
     - gone → 200 `disconnected=false` and log **`aa859_integration_disconnect_raced`** (the double-click branch, distinct from the step-1 "no row" branch);
     - still visible → 503 `aa817_integration_disconnect_row_mismatch` (RLS refusal, or a reconnect changed `updated_at`).
4. Audit on MAIN after commit (unchanged).
5. `aa859_integration_disconnect_tombstoned_not_deleted` when step 3 fails after step 2 (acquire timeout / connection drop): row stays with dead credentials; a retry heals it.

**Rejected alternative:** a "probe DELETE" in a rolled-back savepoint before the tombstone; more clever than needed, and the remaining window self-heals.

**Hardening in the same PR**
- Credential readers (`test_wordpress` reads `creds["wp_url"]`, publish / unpublish `_wordpress(creds)`, the facebook equivalents): a secret equal to `{"disconnected": true}` → 422 "reconnect the integration", not KeyError → 500.
- All sync boto3 calls in this router go through `asyncio.to_thread`.
- `acquire_scoped_conn` validates `UUID(tenant_id)`; a malformed `sub` → 503 `aa817_tenant_context_unavailable`, never a uuid cast error inside a policy.

**Pool instrumentation** (`acquire_scoped_conn`): `tenant_pool_wait_ms` around the acquire and `tenant_pool_hold_ms` acquire→release (`time.monotonic()`), one `aa859_tenant_pool_timing flag_key=… wait_ms=… hold_ms=…` INFO line, so Logs Insights `pct()` works. Nothing logged when the tenant pool was not used.

**Tests (complete list)**
- Unit, rewrite to the new order: `test_disconnect_zero_row_delete_is_503_and_leaves_the_secret` (`:252`; now the secret is tombstoned before the 0-row DELETE → rename `…_is_503_after_tombstone`), `test_disconnect_deletes_before_tombstone_inside_one_transaction` (`:267` → `…_tombstones_between_two_short_transactions`), `test_disconnect_tombstone_timeout_is_502_and_rolls_back` (`:296` → 502, no DELETE issued), `test_disconnect_commit_failure_after_tombstone_is_logged` (`:320` → `tombstoned_not_deleted` event), `test_disconnect_missing_secret_still_deletes` (`:331`).
- Unit, re-check: `test_disconnect_flag_off_opens_its_own_transaction` (`:285`) — flag off now opens two MAIN transactions; adjust the assertion.
- Unit, new: DELETE 0 rows + re-SELECT 0 rows → 200 `disconnected=false` and the `raced` event; tombstone secret → 422 in test / publish / unpublish credential readers; malformed sub → 503.
- Integration, rewrite: `test_disconnect_zero_row_delete_keeps_row_and_secret` (`:167`, RESTRICTIVE FOR DELETE USING false) → row kept, secret **tombstoned**, 503 row_mismatch; rename `…_keeps_row_tombstones_secret`. `test_disconnect_tombstone_failure_rolls_the_delete_back` (`:183`) → "tombstone failure leaves the row and never deletes".
- Integration, new: two real connections (committed seed, cleanup in `finally`), interleaved via an `asyncio.Event` so both pass step 1 before either reaches step 3 → one `true`, one `false` (raced branch), no 503, no 500. This is the proof of the double-click fix.
- `test_aa859_tenant_pool_reentrancy.py`: a pool stub that raises on a second `acquire()` while the same task holds one; parametrized over every moved handler (later PRs add their route).

**Rollout and evidence**
1. Merge, deploy Dev (rollout COMPLETED), `INTEGRATION_DISCONNECT_FLAG` already on.
2. On terra-family (tenant A): connect the E2E WP test site, two parallel DELETEs (`curl … & curl …`). Expect one `true`, one `false`, no 503.
3. q3: `aa817_integration_disconnect used_tenant_pool=True`. If `aa859_integration_disconnect_raced` appears, the live race is proven; if not (requests did not overlap), the report says so plainly and cites the interleaved integration test as the proof.
4. Reconnect afterwards. Do not delete the test-site secret.

**Rollback:** revert the PR. **Dependencies:** none. Lands before PR-S.

---

### PR-B: CIS migration-only `feat: migration 241 drops tenant-role privileges on CIS relations without RLS and puts angle_gate_option under RLS`
Size L (SQL ~350, tests ~300). **Not split:** once 241 is in `api/migrations`, conftest applies it, and the existing 239 re-apply fixtures (`test_aa817_rls_tenant_isolation.py:108-123`, `test_aa817_migration_239.py:57-70`) hit 239 guard 1 (`239:204-206`), and `test_tenant_role_cannot_write_tables_without_rls` (`:415`) fails because `SET chosen = chosen` is now allowed. CI would go red and CIS requires CI to merge. Only the brand-new `test_aa859_migration_241.py` may move to a follow-up PR-B2 if review asks for it. Migration **241**. No flag. Items 5 + W3 + W9 grants.

**Files**
- `api/migrations/241_tenant_pool_grant_hardening.sql`.
- New `tests/integration/test_aa859_migration_241.py`.
- `tests/integration/test_aa817_rls_tenant_isolation.py`, `tests/integration/test_aa817_migration_239.py`.
- New `tests/integration/_rls_fixture_helpers.py`: `undo_241_for_239_reapply(cur)`, `migration_body(n)`, `NO_PRIVILEGE_WITHOUT_RLS_SQL` (the D1 invariant query).

**241 statements** (inside `BEGIN; SET LOCAL lock_timeout = '10s'; … COMMIT;`, guards in `DO $$` blocks, 237/239 style):

```sql
-- 1. item 5: no privilege for the tenant role on any CIS-owned relation without RLS
DO $$
DECLARE r record; n int := 0;
BEGIN
    FOR r IN
        SELECT c.oid::regclass AS rel
          FROM pg_class c JOIN pg_namespace ns ON ns.oid = c.relnamespace
         WHERE c.relkind IN ('r','p','v','m','f')
           AND NOT c.relrowsecurity
           AND ns.nspname NOT IN ('pg_catalog','information_schema') AND ns.nspname NOT LIKE 'pg_toast%'
           AND pg_has_role(current_user, c.relowner, 'USAGE')                     -- runner can act for the owner
           AND c.relowner NOT IN (SELECT oid FROM pg_roles
                                   WHERE rolname IN ('catalog_owner','tripplanner','booking'))  -- CI runner is superuser
           AND (EXISTS (SELECT 1 FROM aclexplode(c.relacl) a WHERE a.grantee = 'aa_app_user'::regrole)
                OR EXISTS (SELECT 1 FROM pg_attribute at, aclexplode(at.attacl) a
                            WHERE at.attrelid = c.oid AND at.attacl IS NOT NULL
                              AND a.grantee = 'aa_app_user'::regrole))
    LOOP
        EXECUTE format('REVOKE ALL ON %s FROM aa_app_user', r.rel);
        RAISE NOTICE 'migration 241: revoked all privileges of aa_app_user on %', r.rel;
        n := n + 1;
    END LOOP;
    RAISE NOTICE 'migration 241: % relations revoked', n;
END $$;

-- 2. W3: angle_gate_option under RLS through its parent request (no tenant column)
LOCK TABLE acp_shared.angle_gate_option IN ACCESS EXCLUSIVE MODE;
ALTER TABLE acp_shared.angle_gate_option ENABLE ROW LEVEL SECURITY;      -- not FORCE: owner (worker t8) exempt
DROP POLICY IF EXISTS tenant_isolation ON acp_shared.angle_gate_option;  -- idempotent re-apply
CREATE POLICY tenant_isolation ON acp_shared.angle_gate_option
    AS PERMISSIVE FOR ALL TO aa_app_user
    USING (EXISTS (SELECT 1 FROM acp_shared.angle_gate_request r
                    WHERE r.request_id = angle_gate_option.request_id
                      AND r.tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid))
    WITH CHECK (EXISTS (SELECT 1 FROM acp_shared.angle_gate_request r
                    WHERE r.request_id = angle_gate_option.request_id
                      AND r.tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid));
GRANT SELECT ON acp_shared.angle_gate_option TO aa_app_user;
GRANT UPDATE (chosen) ON acp_shared.angle_gate_option TO aa_app_user;  -- INSERT stays with the t8 worker (MAIN)

-- 3. W9 connect/test: the columns the UPSERT and the verify UPDATE write (237 policy is FOR ALL + WITH CHECK)
GRANT INSERT (tenant_id, integration_type, config, secret_key, connected_at)
    ON shared.tenant_integrations TO aa_app_user;
GRANT UPDATE (config, secret_key, updated_at, last_verified_at, last_verify_error)
    ON shared.tenant_integrations TO aa_app_user;

INSERT INTO shared.schema_versions (version, applied_at, description)
VALUES ('241', now(), 'AA-859: aa_app_user loses every privilege on CIS relations without RLS (catalog_owner '
        'catalog.* SELECT contract kept); angle_gate_option RLS via parent request (SELECT + UPDATE(chosen)); '
        'tenant_integrations column INSERT/UPDATE for connect/test')
ON CONFLICT (version) DO NOTHING;
```

**Guards** (behavioural, lesson S236)
- **Guard 0, before:**
  - aa_app_user is not superuser / BYPASSRLS and has no members;
  - angle_gate_option exists, the runner owns it or bypasses RLS, it is not FORCEd; grantee set ⊆ {owner, aa_app_user}; policy set ⊆ {tenant_isolation}; `row_security_active('acp_shared.angle_gate_option')` is false for the runner;
  - **every aa_app_user aclitem the loop will revoke has a grantor the runner can act for** (`pg_has_role(current_user, grantor, 'USAGE')`), else raise with the relation name (a non-owner REVOKE would silently skip it);
  - **every aa_app_user aclitem on a non-RLS relation that the loop will NOT touch is in the catalog contract** (schema `catalog`, owner `catalog_owner`, table-level SELECT); anything else → raise;
  - no PUBLIC INSERT / UPDATE / DELETE / TRUNCATE grant on a non-RLS relation in a schema where aa_app_user has USAGE (raise); PUBLIC SELECT → NOTICE only (P0 lists them);
  - record the runner's angle_gate_option count under a foreign GUC (`aa241.n_before`).
- **Guard 1, after (runner):** not filtered, same count under a foreign GUC.
- **Guard 2, policy shape:** exactly `{tenant_isolation}`, `cmd = 'ALL'`, roles `{aa_app_user}`, qual and with_check `ILIKE '%angle_gate_request%NULLIF(current_setting(''app.tenant_id''%'`.
- **Guard 3, as aa_app_user** (transaction-scoped `GRANT aa_app_user TO current_user` only on `insufficient_privilege`, revoked at the end, as in 237):
  - under a foreign GUC and under `''`: `count(*) = 0`, a WHERE-less `UPDATE … SET chosen = chosen` touches 0 rows;
  - under the busiest tenant (taken through the parent as the runner): count = the runner's count of that tenant's options;
  - `INSERT` raises `insufficient_privilege` (sub-block);
  - empty table (CI): seed one request + one option in a savepoint and roll it back.
- **Guard 4, after:** `NO_PRIVILEGE_WITHOUT_RLS_SQL` (D1) returns 0 rows; tenant_integrations has no TRUNCATE and no DELETE beyond 237's; angle_gate_option privileges are exactly SELECT + column UPDATE(chosen).

**Header**
- Not destructive, so no `migrate:` directive.
- Lists what the loop revoked on Dev and the kept catalog contract (13 views), both from P0 #1.
- Rollback:

```sql
-- STEP 0 (before the SQL): DEL every 241-dependent flag, then confirm q3 shows no new traffic on them:
--   aa859:angle_gate_decide_pool, aa859:integration_connect_pool (+ any later flag marked "depends on 241" in D7).
--   Otherwise choose/connect/test fail with 42501 → 500 the moment the grants go.
BEGIN;
DROP POLICY IF EXISTS tenant_isolation ON acp_shared.angle_gate_option;
ALTER TABLE acp_shared.angle_gate_option DISABLE ROW LEVEL SECURITY;
REVOKE UPDATE (chosen) ON acp_shared.angle_gate_option FROM aa_app_user;   -- SELECT kept (pre-241 state)
REVOKE INSERT, UPDATE ON shared.tenant_integrations FROM aa_app_user;
GRANT SELECT, DELETE ON shared.tenant_integrations TO aa_app_user;          -- 237 state
DELETE FROM shared.schema_versions WHERE version = '241';
COMMIT;
-- The revoked SELECTs are NOT restored: they were the leak. Restore one only if a route proves to need it.
```

**Test changes in the same PR**
- Both 239 re-apply fixtures call `undo_241_for_239_reapply(c)` (DROP the 241 policy, DISABLE RLS on angle_gate_option, re-grant DEV_LEGACY_GRANTS) before re-applying 239, then re-apply the 241 body. `test_guard_refuses_rls_on_a_revoke_table` stays valid.
- Replace `NO_RLS_NO_WRITE_TABLES` (`:82`) and `test_tenant_role_cannot_write_tables_without_rls` (`:415`) with `test_tenant_role_has_no_privilege_on_any_relation_without_rls`, running `NO_PRIVILEGE_WITHOUT_RLS_SQL` on the fully migrated CI DB. Because the invariant allows the catalog contract, the committed re-grants left by `test_aa679_catalog_views.py:48-95` and `test_aa712_migration_228.py:62-112` do not break it; the contract tests (`test_aa679:159-164`, `test_aa712_228:228, :455, :523`) stay green.
- **angle_gate_option does not join `TENANT_TABLES`** (the generic tests assume a `tenant_id` column: `:221` `count(DISTINCT tenant_id)`, `:228` `WRITE_TABLES`, `:245` `SET tenant_id = tenant_id`). Instead:
  - new `CHILD_RLS_TABLES = {"acp_shared.angle_gate_option": "(SELECT r.tenant_id FROM acp_shared.angle_gate_request r WHERE r.request_id = t.request_id)"}`;
  - `test_child_forged_tenant_reads_no_foreign_rows` and `test_owner_still_sees_every_tenant_of_child_tables` use the key expression;
  - `test_angle_gate_option_writes`: under the own GUC `UPDATE … SET chosen = chosen` touches exactly the own tenant's options; under a foreign or `''` GUC 0 rows; INSERT raises 42501. Seed parent request first.
  - `test_every_rls_table_is_covered` (`:344`) counts `TENANT_TABLES ∪ CHILD_RLS_TABLES ∪ legacy`: `ALL_RLS_TABLES == 16`.
- `DELETE_ONLY_TABLES` loses tenant_integrations. Invert `test_tenant_role_cannot_insert_or_update_delete_only_tables` (`:296`): own-tenant INSERT works; a foreign-tenant INSERT is refused (WITH CHECK); a WHERE-less UPDATE under a foreign or `''` GUC touches 0 rows; an UPDATE of a column outside the grant (e.g. `integration_type`) raises 42501.
- New `test_aa859_migration_241.py`:
  - `test_applied_by_conftest` (schema_versions has 241, policy exists, RLS on). conftest swallows errors (lesson AA-741).
  - idempotent re-run;
  - RDS-like runner via `SET LOCAL SESSION AUTHORIZATION` (owner, NOSUPERUSER, BYPASSRLS standing in for rds_superuser; lesson S237): the runner still sees every option under a foreign GUC, **and the loop skips a catalog_owner-owned view it cannot act for without error**;
  - guard refusals: unknown policy, FORCE on, a PUBLIC INSERT grant on a non-RLS table, an aa_app_user grant on a non-catalog relation owned by a role the runner cannot act for;
  - mutation check: remove the temporary GRANT and the RDS-like test must fail.

**D8 flow**
1. Merge the CIS PR (CI green).
2. Infra PR `chore: copy CIS migration 241 into db/migrations/cis`, byte copy (`cmp` in the PR body). Nghiệp approves it.
3. DB Migrate `check`, then `apply`, with `shared.job` idle (P0 #5 rerun right before).
4. The automatic schema-dump PR updates `db-schema-reference.md`.

**Live evidence**
- Probe v3 (PR-P): angle_gate_option row 0 FAIL; `no_privilege_without_rls_violations == []`; catalog contract rows listed and unchanged vs P0.
- The 5 existing flagged routes still answer 200 for tenant A: publish-log list, pending, latest-piece, get-piece, disconnect (they LEFT JOIN angle_gate_option).
- TripPlanner browse smoke (catalog views untouched; cheap confirmation).

**Rollback:** header STEP 0 + SQL through DB Migrate (Nghiệp approves).
**Dependencies:** P0 (its class (c) must be empty). Applied before PR-D3 and PR-I flips.

---

### PR-P: root repo `chore: probe v3 for AA-859 tables and the no-privilege-without-RLS verdict`
Size M. File: `docs/audits/2026-10-16-S240-aa859/aa859_probe_v3.py`, copy-and-extend of v2. Root PR.
- Phase `post-241` (later `post-243`, `post-244`); S3 key `s240/`.
- Grants read from `aclexplode(relacl/attacl)` with owner and grantor (no `information_schema`).
- Per-table key-expression map replaces the hard-coded `tenant_id` in `_cell_sql`, `_runner_counts`, `_busiest_non_master` (`::text` casts for text keys).
- Categories: `CHILD_OF_PARENT` (angle_gate_option, later quarter_plan_version: runner pre-computes parent ids per GUC tenant; leak = a visible child not in that set); `PLATFORM_PLUS_OWN` (tour_atoms on `owner_scope`); `MASTER_PLUS_OWN_TEXT` (tenant_tour_pages).
- Verdicts: `no_privilege_without_rls_violations` = the D1 query (must be empty, FAIL otherwise); catalog contract set unchanged vs P0; a "moved route reads a non-RLS relation" check against a static route→table list in the script; **D9: non-platform atoms visible to aa_app_user through `catalog.*`** (reported; FAIL only after 244 if it was 0 at P0 and rose).
- `pg_stat_activity` by `application_name` (feeds D5).
- Keep-alive matrix (wave 4 on): `SET LOCAL ROLE tripplanner` / `catalog_owner` counts on tour_atoms and the catalog views equal the baseline JSON; "skipped" with the reason when SET ROLE is refused.
- Fix the stale q1/q2 regexes in `aa817-flags-verify/logs_queries.sh`: `aa817_tenant_flag_read_failed`, `aa817_tenant_pool_unavailable`, `aa817_tenant_context_unavailable`, `aa817_tenant_guc_not_applied`, `aa544_tenant_pool_create_failed`, `aa817_integration_disconnect_row_mismatch`, `aa859_integration_disconnect_tombstoned_not_deleted`, `aa859_integration_disconnect_raced`.
- Read-only mode only.

---

### PR-D2: CIS `feat: PATCH content piece on the tenant pool (AA-859 W2)`
Size S (~150). No migration. Flag `PIECE_EDIT_FLAG`.
- **Files:** `api/routers/v1_content_writing.py:147-157`; `services/acp_content_writing/service.py:2172-2203` (UPDATE lifted into `_PIECE_EDIT_SQL`); flags module; unit matrix; `tests/integration/test_aa817_tenant_pool_content.py`.
- **Change:** one `acquire_scoped_conn(..., PIECE_EDIT_FLAG, fail_closed=True)` running `UPDATE … WHERE piece_id AND tenant_id AND status IN ('approved','held') RETURNING …`; after commit, `write_audit_log` on MAIN, best-effort (`aa859_piece_edit_audit_failed`, response stays 200); log `aa859_piece_edit used_tenant_pool=`.
- **Tests:** fail-closed matrix; forgotten-WHERE (patch `_PIECE_EDIT_SQL`, replace `tenant_id = $n` with `$n::uuid IS NOT NULL`: B cannot edit A's piece with the flag on; flag-off admin pool does, as sanity); audit failure does not fail the request; reentrancy stub entry.
- **Evidence:** A edits its own approved/held piece → 200 (original text saved and restored); B PATCHes A's piece_id → 404; q3.
- **Rollback:** DEL the flag. **Dependencies:** none.

### PR-D6: CIS `feat: PATCH tenant tour version on the tenant pool (AA-859 W6)`
Size M (~300, larger because of the CI stand-in). No migration. Flag `T2_VERSION_WRITE_FLAG`.
- **Files:** `api/routers/v1_tours.py:957-1015` (SQL into constants), flags module, tests, new `tests/integration/_ttv_live_standin.py`.
- **Change:** one scoped transaction:
  1. own-row SELECT of the version (`WHERE id = $1 AND tenant_id = $2`), 404 if none;
  2. for an edit: `SELECT pg_advisory_xact_lock(<AA859_TTV_LOCK_CLASS>, hashtext($tenant::text || ':' || $published_tour_id::text))` (two-int form so the key space cannot collide with the enqueue advisory locks; needs no grant), then the existing `SELECT COALESCE(MAX(version_number), 0) + 1 …` (no `FOR UPDATE`: PostgreSQL rejects locking clauses on aggregates, 0A000), then INSERT;
  3. backstop: `UniqueViolationError` on the live UNIQUE `(tenant_id, published_tour_id, version_number)` → 409 `version_conflict` (never 500);
  4. otherwise UPDATE status.
- Delete `PATCH /v1/tours/{tour_id}/approve` (`:1020-1046`, 0 rows for every tenant, still returns ok:true) **if** a frontend grep shows no caller; otherwise 410 with a note.
- **CI stand-in:** `conftest.py`'s `TTV_STANDIN_DDL` stays unchanged (`test_aa766`'s `_ttv_minimal()` relies on `version_number` being absent). The new helper creates, inside each test's own transaction, a stand-in with the live columns (`version_number`, `parent_version_id`, `edited_at`, `edited_by_user`, `job_id`, …) and the UNIQUE constraint, then re-applies 229 and 239 in that transaction (RLS + master read for the pt/rt/sc joins), as `test_aa817_rls_tenant_isolation` does.
- **Tests:** matrix entry; forgotten-WHERE on the own-row SELECT; foreign `version_id` → 404; **edit path on real Postgres through the tenant pool** (new version row, number + 1); **two connections editing concurrently → numbers N+1 and N+2, no 500**; mutation check: remove the advisory lock → the concurrent test gets 409 or a duplicate attempt, never silent success with equal numbers.
- **Evidence:** A changes status and reverts it; A inline-edits a version (new number) and the extra version is cleaned up or left as a normal edit (stated in the report); B gets 404; q3.
- **Dependencies:** none.

### PR-D3: CIS `feat: angle-gate choose and reopen on the tenant pool (AA-859 W3)`
Size M (~400). No migration (needs 241 applied). Flag `ANGLE_GATE_DECIDE_FLAG`.
- **Files:** `api/routers/v1_angle_gate.py:87-117`; `services/acp_angle_gate/service.py:341-412` (functions take `conn` and `tenant_id`; SQL in constants `_CHOOSE_LOCK_SQL`, `_OPTION_EXISTS_SQL`, `_OPTION_CHOOSE_SQL`, `_REQUEST_APPROVE_SQL`, `_REOPEN_SQL`); flags module; tests; **`tests/unit/test_aa497_reopen_angle.py` and the `test_aa449_angle_gate_service.py` helpers it reuses** (signature change from `pool` to `conn`).
- **Change** (one tenant transaction, then the re-read on MAIN):

```sql
-- choose
SELECT status FROM acp_shared.angle_gate_request
 WHERE request_id = $1 AND tenant_id = $2::uuid FOR UPDATE;          -- 404 if none
-- status must be 'pending_choice' or 'reusable', else WrongStatusError (409)
SELECT 1 FROM acp_shared.angle_gate_option WHERE request_id = $1 AND idx = $3;   -- else AngleGateError
UPDATE acp_shared.angle_gate_option SET chosen = (idx = $3) WHERE request_id = $1;   -- _OPTION_CHOOSE_SQL
UPDATE acp_shared.angle_gate_request SET status = 'approved', updated_at = now()
 WHERE request_id = $1 AND tenant_id = $2::uuid AND status IN ('pending_choice','reusable');
-- reopen
UPDATE acp_shared.angle_gate_request SET status = 'reusable', updated_at = now()
 WHERE request_id = $1 AND tenant_id = $2::uuid AND status = 'approved' RETURNING request_id;
-- 0 rows -> re-read status under the same conn -> 404 or WrongStatusError
```
- Closes the time-of-check/time-of-use gap. Lock order (request, then options) matches the t8 worker. Response from `fetch_request(tenant_id, request_id, pool)` on MAIN after commit (D2 exception until wave 4).
- **Tests:**
  - matrix entry; forgotten-WHERE on the request SELECT; concurrent choose (second sees `approved` → WrongStatusError); reentrancy stub.
  - **The 241 RLS assertion, run directly, not through the route** (the route's request SELECT already 404s for B, so it cannot test the option policy): as aa_app_user with B's GUC, execute `_OPTION_CHOOSE_SQL` against A's `request_id` → 0 rows updated, A's `chosen` unchanged. **Mutation check:** the same test with `ALTER TABLE acp_shared.angle_gate_option DISABLE ROW LEVEL SECURITY` in its transaction must fail (rows updated > 0).
- **Evidence:** A reopens an approved request, chooses a different idx, then chooses the original idx back (state restored); B chooses on A's id → 404; q3; portal AngleGateWizard smoke (screenshot).
- **Dependencies:** 241 applied.

### PR-D4: CIS `feat: unpublish on the tenant pool (AA-859 W4)`
Size S–M. No migration. Flag `UNPUBLISH_FLAG`.
- **Files:** `api/routers/v1_publish.py:163-253`, flags module, tests.
- **Change:** three short scoped blocks under one flag: (1) SELECT publish_log; (2) SELECT tenant_integrations; (3) after GetSecretValue (`asyncio.to_thread`) and the remote delete, UPDATE … `AND status='published'` RETURNING. No connection held across Secrets Manager or HTTP. Audit on MAIN. Tombstoned credentials → 422 (PR-A).
- **Tests:** matrix entry; forgotten-WHERE on the publish_log SELECT; double unpublish → second 404/409 from the status guard; mocked remote delete; reentrancy stub.
- **Evidence:** A publishes a test piece to the E2E WP site (existing MAIN route); unpublish with the flag on → 200, WP post trashed; B DELETEs A's publish_id → 404; q3.
- **Dependencies:** PR-A.

### PR-S (sizing): CIS `chore: tenant pool max 2` + Infra `chore: cap api autoscaling at 7 tasks`
Size S + S. No migration. Details in §2.
- **CIS:** `aa544_tenant_pool.py:69-70` (`TENANT_POOL_MAX_SIZE = 2`, comment); `tests/unit/test_aa817_fail_closed_routes.py:342` (`TENANT_POOL_MAX_SIZE * API_MAX_TASKS <= 15` with `API_MAX_TASKS = 7` and a comment pointing at Infra `modules/ecs/main.tf:428`). **`api/main.py:79` main pool stays at 10.**
- **Main-pool visibility (new, small):** a 60 s gauge log `aa859_main_pool_gauge size=… idle=…` from a lifespan task, so wave 4 can decide the main shrink on data. No acquire timeout change in this PR.
- **Infra:** `modules/ecs/main.tf:428` (`max_capacity = 7`); root `docs/architecture/data-standards/03-scaling.md` C2.2 rows (cis-api 10 × 7, cis-tenant 2 × 7 = 14; the stale "today 5" fixed).
- **Order:** Infra PR (Nghiệp approves, terraform plan/apply with MFA) before the CIS deploy, so `2 × max tasks` never exceeds 15.
- **Evidence:** P0 #4 rerun shows `cis-tenant` ≤ 2 per task; after a page-load burst on tenant A's portal, `aa859_tenant_pool_timing` p95 `wait_ms` < 50 and no `aa817_tenant_pool_unavailable`; main gauge recorded as the wave-4 baseline.
- **Rollback:** revert both (Infra first). **Dependencies:** PR-A deployed.

### PR-D5: CIS `feat: T2 version reads on the tenant pool (AA-859 W5)`
Size M–L (~500; split into D5a "pool + my-versions" and D5b "full / tour / versions / export" if > 600). No migration. Flag `T2_VERSION_READS_FLAG`.
- **Files:** `api/routers/v1_tours.py` (`:51-166`, `:506-566`, `:610-743`, `:750-948`), flags module, tests (reuses `_ttv_live_standin.py` from PR-D6).
- **Change:** one scoped block per request; `shared.job` LEFT JOINs become a second MAIN query `SELECT id, status FROM shared.job WHERE id = ANY($1::uuid[])` keyed by job_ids returned through RLS (D2), merged in Python; `/full` admin branch stays on MAIN; export-docx audit on MAIN; remove the stale "Nothing in this function is eligible" comment (`:72-83`).
- **Tests:** matrix entry; forgotten-WHERE for my-versions and versions/{id} (against the live-shape stand-in); foreign version id → 404; job status still appears; reentrancy stub per handler.
- **Evidence:** A: pool, my-versions, tour/full, version, export-docx → 200 with the same shape as flag off (JSON keys and counts compared before/after); B: A's version_id → 404; q3 per route; portal DashboardTab / PoolTab smoke + `wait_ms` percentiles.
- **Dependencies:** 241 applied (shared.job SELECT revoked, so the split is required); PR-S deployed before the flip.

### PR-I: CIS `feat: integration connect, test and status on the tenant pool (AA-859 W9)`
Size M. No migration (241 grants). Flag `INTEGRATION_CONNECT_FLAG`.
- **Files:** `api/routers/v1_integrations.py` (`:129-302`, `:332-478`), flags module, tests.
- **Change:** GET status one block; POST connect: Secrets Manager put (`asyncio.to_thread`) first, then one block with the UPSERT; POST test: block #1 SELECT config / secret_key, then GetSecretValue + HTTP with no connection, then block #2 UPDATE `last_verified_at` / `last_verify_error`.
- **Tests:** matrix entry; forgotten-WHERE on the status SELECT; UPSERT with a foreign `tenant_id` refused by WITH CHECK; UPDATE of a column outside the 241 grant raises 42501; reentrancy stub.
- **Evidence:** A: GET, connect the WP test site, test → 200 and `last_verified_at` set; B: GET shows only its own state; q3.
- **Dependencies:** 241 applied, PR-A.

### PR-J: CIS `fix: /admin/atoms is staff-only behind a flag (AA-859 item 4)` — only if Q1 = yes
Size S. No migration. Flag `ADMIN_ATOMS_STAFF_ONLY_FLAG` (fail closed = staff-only).
- **Files:** `api/routers/admin_atoms.py` (`_resolve_atom_owner_scope` `:74-89`, `:203-505`), its tests.
- **Change:** with the flag on (or Redis unreadable), a tenant Bearer → 403 and log `aa859_admin_atoms_tenant_refused`; X-Admin-Secret unchanged. The tenant branches stay in code until a follow-up removes them.
- **Tests:** flag on → tenant 403, admin 200; flag read fails → tenant 403; flag off → old behaviour.
- **Evidence:** tenant A's JWT through `/api/tenant/admin/atoms` → 403; admin atom-curation page loads (screenshot); q3 shows no `aa859_admin_atoms_tenant_refused` from the portal over the session.
- **Rollback:** DEL the flag. **Dependencies:** none. Keeps 244 SELECT-only.

---

## Follow-up waves (not S240; each its own issue after Q2 and the Linear quota check)

### Wave 3: brand identity + publish (M–L)
**Migration 242** `feat: RLS on tenant_brand_rules and tenant_seo_config for the tenant pool` — SQL as in the draft (229 uuid template on both tables, `GRANT SELECT, INSERT` + column UPDATE; column names confirmed against `db-schema-reference.md` at write time). Guards in the 237 style (no FORCE, grantee set ⊆ {owner, aa_app_user}) plus the D1 invariant re-asserted.
- **brand-identity GET / POST** (`BRAND_IDENTITY_FLAG`): tenant branch moves; staff branch and `notify_admins` stay on MAIN. The acc1 `BRONZE_BUCKET` default at `admin_pipeline.py:4917` is fixed in a separate one-line `fix:` PR (code default, not an env var).
- **publish** (`PUBLISH_FLAG`): `daily_publish_limit` read on MAIN before the claim (D2). Blocks: piece read → integration SELECT → (Secrets Manager, no connection) → `claim()` (nested transaction becomes a savepoint) → (remote post, no connection) → `finish()`. Audit on MAIN. Coordinate with AA-815/AA-819.

### Wave 4: atoms / subject / planning (L)
Starts with Q3 (route hub) and, if P0 #2 showed a D9 exposure, the Q4 outcome. Before this wave's code PRs, decide the main-pool shrink from the `aa859_main_pool_gauge` data (D5).

**Migration 243** — as in the draft (`tenant_tour_pages` CREATE IF NOT EXISTS with the live DDL for CI; 229 template on subject / quarter_plan / year_plan [+ route_pick only if Q3 keeps the hub]; child policy on quarter_plan_version; text policy + master read on tenant_tour_pages; `GRANT USAGE ON SCHEMA acp_contract` and the 9-relation SELECT `PLATFORM_READ_ALLOWLIST`). Guard changes from the critique:
- the D1 invariant becomes "catalog contract **∪** `PLATFORM_READ_ALLOWLIST` (exactly the 9 relations, SELECT only)", same shared SQL text;
- aa_app_user holds no privilege on any view in `acp_contract` (`v_active_tour_atoms` stays revoked);
- behavioural counts per table, seeded rows rolled back for empty tables;
- fixture helper becomes `undo_24x_for_239_reapply` and also undoes RLS on `year_plan`.
- `tenant_atom_state` stays revoked with no RLS: Dead Table Registry candidate with `marketplace_portfolios`.

**Migration 244** — tour_atoms RLS with `atoms_platform_read`, `tenant_isolation` (text, no cast), `catalog_owner_read USING (true)`, `tripplanner_read USING (true)`, `GRANT SELECT` to aa_app_user. Guards as in the draft (grantee set ⊆ {owner, catalog_owner, tripplanner, aa_app_user}; catalog_owner / tripplanner counts on tour_atoms and through `catalog.v_tour_place` / `v_tour_component` unchanged; every `owner_scope` is `'platform'` or canonical lower-case uuid), **plus D9:** the count of non-platform atoms visible to aa_app_user through `catalog.*` must equal the P0 value (0 expected, or the value Nghiệp accepted under Q4). EXPLAIN (ANALYZE) TP's real `v_tour_place` / `v_tour_component` query with `= ANY($1)` before/after (lesson S238); `test_aa679_catalog_views.py` green.

**Code PRs** (one group each, own flag): angle-gate GET + reviews, slate reads (config pre-read on MAIN, `request_slate_proposal` and `/slate/refresh` stay on MAIN), subject pick / cut, trip-reallocation suggest / confirm (one conn instead of 5 acquires), marketplace. The `tenant_tour_pages` LATERAL join fix (draft SQL) goes with the first PR that reads it. Wave 4 also extends `test_aa817_rls_tenant_isolation` and the probe keep-alive matrix to the new tables.

---

## 2. Pool sizing decision (revised)

**Inputs:** `max_connections` 181, minus 3 superuser-reserved = 178; C2.3c 75% ceiling ≈ 135–140. Role limits: tripplanner 30, booking 15, aa_app_user 15. Today: tenant pool 1/task, api autoscale max 10, main pool 10/task, worker `max(5, 8+2) = 10` × max 3 tasks, plus uncapped per-job pools.

**Today's worst case:** main 100 + tenant 10 + worker 30 + TP 30 + booking 15 + migrate 1 + ops ~15 = **~201**, over 178; only Dev's desired_count 1 hides it.

**S240 decision**

| Item | Change | Worst case |
|---|---|---|
| tenant pool | max 1 → **2** per task | 2 × 7 = **14 ≤ 15** |
| api autoscale | max_capacity 10 → **7** | |
| main pool | **unchanged at 10** | 10 × 7 = 70 |
| total | | 70 + 14 + 30 + 30 + 15 + 1 + 15 = **~175**: under 178, above the 75% ceiling |

**Why the main pool is not shrunk now:** in S240 only W2–W6 and W9 leave main; slate, angle-gate GET, reviews, marketplace, brand identity, publish, `/v1/quota`, `/v1/billing` and every admin route stay, and D2 adds a MAIN acquire to each moved route (audit, job status, `fetch_request` re-read). Main acquires have no timeout (`aa544_tenant_pool.py:200`, ~180 `pool.acquire()` call sites), so starvation would show only as requests hanging to the API Gateway 30 s limit, which nothing measures yet. The shrink (target 5, total ≈ 140) is decided in wave 4 from the `aa859_main_pool_gauge` baseline, possibly together with a main acquire timeout.

**Why tenant 2, not 1:** with max 1, one slow statement (up to the 15 s `statement_timeout`) makes every queued tenant request on that task 503 after the 5 s acquire timeout. W5 puts DashboardTab / PoolTab (5–8 parallel calls) and three pollers on the pool. Hold time (3–10 ms) is not the issue; head-of-line blocking is.

**Why not 3:** needs aa_app_user 15 → 30, total ≈ 190. Waits for an instance resize or X1.

**Accepted residual risk:** the autoscale worst case stays above the 75% ceiling until wave 4; Dev runs 1 task (2 during a rolling deploy), so the real peak is far below. A rolling deploy at full scale (14 tasks × 2) can transiently hit 53300 on aa_app_user → per-request 503 on new tasks; not reachable on Dev. Documented in C2.2; alarms belong to AA-832.

**Cost:** none. An optional metric filter + alarm on `aa817_tenant_pool_unavailable` (~$0.10/month) belongs to AA-832.

---

## 3. Risks and how each PR handles them

| Risk | Where | Mitigation |
|---|---|---|
| **241 apply fails on objects the runner cannot act for** (catalog_owner views, other-grantor aclitems) | 241 | Loop filtered by `pg_has_role(current_user, relowner)` + owner exclusion; guard 0 raises with names on other-grantor or non-catalog out-of-reach grants; P0 #1 (aclexplode, owner, grantor) must show class (c) empty before merge. |
| **Catalog contract broken by the cleanup** | 241, 243 | Contract excluded by owner+schema+SELECT rule; `test_aa679` / `test_aa712` contract tests unchanged; TP browse smoke after the apply. |
| **Tenant atoms readable through `catalog.*`** (pre-existing) | 244, D9 | Measured in P0, guarded in 244 and probe v3, decision Q4; no view change inside AA-859. |
| **Silent 0 rows for worker / main** | Every new RLS table | ENABLE without FORCE, owner exempt; guards check `row_security_active` false and the runner count under a foreign GUC. Never FORCE. The 8 legacy FORCE tables are untouched. |
| **Silent 0 rows for tripplanner / catalog_owner** | 244 | Keep-alive `USING (true)`; per-role and per-view counts; `test_aa679_catalog_views.py`; probe keep-alive matrix; TP smoke. 241–243 touch no table they read. |
| **Owner-rights views bypass RLS** | `v_active_tour_atoms` | Revoked in 241, before 243 grants USAGE on `acp_contract`; 243 guard asserts no aa_app_user privilege on any `acp_contract` view. |
| **241 revokes something a live route reads** | 241 | P0 lists every revocation; current tenant-pool reads are RLS tables + angle_gate_option (re-granted in the same transaction); smoke of the 5 flagged routes after apply; recovery is one GRANT. |
| **241 rollback 500s flagged routes** | 241 rollback | Header STEP 0 DELs every "depends on 241" flag (D7 column) first. |
| **PUBLIC grants slip past the rule** | 241 | Guard 0 raises on PUBLIC write grants; PUBLIC SELECT listed by P0 and the probe. |
| **Invalid SQL / lost update in W6** | PR-D6 | Advisory xact lock + MAX (no aggregate FOR UPDATE); UniqueViolation → 409; real-Postgres edit and concurrent-edit tests on a live-shape stand-in. |
| **Tests that cannot fail** | PR-D3, PR-A | Option-policy test runs the UPDATE directly with a DISABLE-RLS mutation check; double-click proven by an interleaved two-connection integration test, live evidence only claimed if the `raced` event appears. |
| **Generic RLS tests assume `tenant_id`** | PR-B | angle_gate_option in `CHILD_RLS_TABLES`, not `TENANT_TABLES`; dedicated tests. |
| **22P02 on text tenant ids** | tenant_tour_pages, tour_atoms | Text policies without `::uuid`; `''` → NULL → no rows; P0 + 244 guard check canonical lower-case; `UUID(tenant_id)` validation in `acquire_scoped_conn` (PR-A). |
| **Writes swallowed inside a read path** | slate `_tenant_market_codes` | Wave 4: MAIN after commit, or retire (Q3). Rule: no try/except around a statement in a scoped block without a savepoint. |
| **Self-deadlock on the tenant pool** | W3, W5, wave 4 | One `acquire_scoped_conn` per request path; reentrancy stub parametrized over every moved handler. |
| **Connection held across Secrets Manager / HTTP** | W4, W9, disconnect | Short blocks around external calls; boto3 via `asyncio.to_thread`. |
| **Main-pool starvation unseen** | PR-S | Main not shrunk in S240; `aa859_main_pool_gauge` baseline before wave 4. |
| **CI silently skips a migration** | 241, 243 | `test_applied_by_conftest` per migration; 243 creates `tenant_tour_pages` IF NOT EXISTS. |
| **239 re-apply fixtures break / red CI between PRs** | 241, 243 | Undo helper and replaced tests ship in the same PR as the migration (PR-B not split). |
| **Lock on hot tables** | 244 | `shared.job` idle, `lock_timeout 10s`, never during a wave. 241 locks only angle_gate_option (33 rows). |

---

## 4. What fits in S240 and what does not

Each migration costs ~45–60 min wall time (CIS PR CI → Infra copy PR → Nghiệp approves → DB Migrate check/apply → probe). Code PRs can be batched into one or two Dev deploys because flags default off. Flips are serial, each with report-then-confirm.

**S240 (in order)**
1. P0 pre-flight (aclexplode grants, D9 counts) + Q1 to Nghiệp.
2. PR-A (disconnect + timing + uuid validation): deploy and evidence.
3. PR-B migration 241 → Infra copy → apply → PR-P probe (0 FAIL, catalog contract unchanged).
4. PR-D2, PR-D6, PR-D3, PR-D4: one batched deploy, then four flips with evidence.
5. PR-S sizing (Infra apply needs Nghiệp + MFA).
6. PR-D5, then flip.
7. PR-I, then flip.
8. PR-J (if Q1 = yes), then flip.

Cut line if time runs out: after step 4; D5 / I / J / S move to S241 under AA-859.

**After S240:** items 5 and 6 done; item 1 done (W2–W6); item 3 except publish; item 4 `/admin/atoms` (if Q1). "No aa_app_user privilege on a CIS relation without RLS, catalog contract excepted" proven by guard 4, the CI test and the probe.

**Not in S240** (Q2: re-scope AA-859's Done-when or open two issues, after the Linear quota check): wave 3 (242 + brand identity + publish); wave 4 (Q3, Q4, 243/244, angle-gate GET / reviews / slate / subject / trip-reallocation / marketplace, `tenant_tour_pages` join fix, probe keep-alive matrix, `test_aa817_rls_tenant_isolation` coverage of the new tables, main-pool shrink).

**Housekeeping in the same session**
- `docs/implementation-notes/AA-859.md` (CIS repo), updated per PR, including the D1 catalog exclusion and the D3 deviation.
- Lesson for `skill/aa-lessons/lessons.md` (root-caused in this review): "grant probes must read `aclexplode(relacl/attacl)` with owner and grantor; `information_schema.role_table_grants` hides grants from roles the runner is not a member of — symptom: a catalog-wide REVOKE planned against an incomplete list (S240, AA-859). Catch by: the D1 invariant query in CI."
- Logs-query regex fix (PR-P).
- CONTEXT.md: D2 exception table and the catalog contract exception (PR-B or PR-D2).
- Side findings: `catalogApi.fetchPoolTour` 404 → AA-863; `marketplace_portfolios` / `tenant_atom_state` → Dead Table Registry note; D9 → Q4.

---

## Appendix: critique disposition

**Accepted**
| Critique | Change in this plan |
|---|---|
| Safety #1 / Feasibility #1: 241 loop hits `catalog.*` views; `grants.json` blind spot | D1 rewritten: owner-scoped loop, catalog contract exception in one shared invariant query, grantor check in guard 0, P0 and grants probe on `aclexplode`; 243 allowlist = contract ∪ 9 relations; lesson recorded. |
| Safety #2: catalog views expose tenant atoms, bypassing 244 | D9 + Q4; P0 measures, 244 guard and probe keep it fixed. |
| Safety #3 / Feasibility #2: `MAX … FOR UPDATE` invalid; `ORDER BY … LIMIT 1 FOR UPDATE` does not serialise | Advisory xact lock (namespaced two-int form) + UniqueViolation → 409; real-Postgres and concurrent tests. |
| Safety #4: main pool halved while most tenant traffic stays on it | Main stays 10 in S240; gauge log; shrink decided in wave 4. |
| Safety #5: rollback breaks flagged routes | Rollback STEP 0 DELs the "depends on 241" flags (D7 column). |
| Feasibility #3: angle_gate_option breaks the generic tests | `CHILD_RLS_TABLES` + dedicated tests; not in `TENANT_TABLES` / `WRITE_TABLES`. |
| Feasibility #4: D3 RLS assertion cannot fail | Direct UPDATE as aa_app_user with B's GUC + DISABLE-RLS mutation check. |
| Feasibility #5: no TTV table shape in CI | Per-test live-shape stand-in with UNIQUE, re-applying 229/239; conftest untouched. |
| Feasibility #6: PR-B cannot split tests | PR-B ships the fixture helper and replaced tests; only the new 241 test file may move. |
| Feasibility #7: D3/PR-J changes item 4 without a decision, no flag | Q1 + Q2; PR-J behind a fail-closed Redis flag, rollback = DEL. |
| Feasibility #8: D2 table incomplete | Added content-writing write, slate refresh, `/v1/billing`, `/v1/quota`. |
| Feasibility #9: test lists undercount | PR-A lists all six unit and two integration tests; PR-D3 lists `test_aa497` / `test_aa449` helpers. |
| Feasibility #10: double-click evidence proves nothing alone | `aa859_integration_disconnect_raced` event; interleaved integration test is the proof; live claim only if the event appears. |

**Rejected or modified**
- **Safety #1 fix option "`c.relowner = current_user::regrole`"**: replaced by `pg_has_role(current_user, relowner, 'USAGE')` + explicit owner exclusion. Owner equality would skip CIS tables owned by another role the runner acts for, and alone it does not protect the CI superuser run.
- **Feasibility #1 "allowlist the catalog views by name"**: modified to an owner + schema + SELECT-only rule. A name list goes stale each time a catalog view is added (225 → 228 → 235 already changed it) and would turn the next catalog migration's CI red for no security reason. The guard still pins the privilege to SELECT and the owner to `catalog_owner`.
- **Feasibility #1 claim that catalog views "never show another tenant's rows" because of catalog_owner's policies**: not accepted as stated. `tour_atoms` has no RLS today and the views do not filter `owner_scope`; handled as D9 (Safety #2).
- **Safety #2 fix "add `owner_scope = 'platform'` inside the catalog views" within AA-859**: deferred to Q4. It changes the cross-app catalog contract (TripPlanner, Booking), needs a root ADR, and the exposure predates AA-859.
- **Safety #4 "add a main acquire timeout"**: not in S240. It touches ~180 call sites; the gauge gives the data first, and the decision is taken with the wave-4 shrink.
