# AA-817 scope addition 1 — migration 237 (shared.tenant_integrations RLS), S239

Agent: Claude Code (subagent). Committed locally only, nothing pushed, nothing applied on Dev.

## What was built
| repo | worktree | branch | commit |
|---|---|---|---|
| AA-CIS-App | `.tmp-session/wt/aa817` | `feat/aa817-mig237-tenant-integrations-rls` (from origin/main 802b5920) | 932e1697 |
| AA-CIS-Infra | `.tmp-session/wt/aa817infra` | `chore/aa817-copy-237` (from origin/main 78736be) | e4b3e71 |

`api/migrations/237_tenant_integrations_rls.sql` is the 229 template applied to one table:
- `ENABLE ROW LEVEL SECURITY`, no FORCE (D2: owner aa_cis_admin stays exempt, main pool unchanged);
- `POLICY tenant_isolation AS PERMISSIVE FOR ALL TO aa_app_user USING / WITH CHECK (tenant_id =
  NULLIF(current_setting('app.tenant_id', true), '')::uuid)`;
- `GRANT USAGE ON SCHEMA shared` + `GRANT SELECT, DELETE ON shared.tenant_integrations TO aa_app_user`.
  SELECT + DELETE is exactly what `v1_integrations._disconnect` does on the tenant pool (SELECT secret_key,
  then DELETE ... WHERE); 229 likewise granted only what its routes needed (no DELETE there).
- Header, `schema_versions` row `'237'` (ON CONFLICT DO NOTHING), BEGIN/COMMIT, `lock_timeout 10s`, LOCK before
  count, rollback block, idempotent (policy dropped by name).
- In-transaction guards (229 set + extras): owner / no FORCE / **no other grantee**; runner still exempt;
  aa_app_user reads 0 and a WHERE-less DELETE removes 0 under a foreign or `''` GUC (own-tenant count when
  rows exist); policy set and **shape** (Dev table is empty, so counts alone prove nothing); SELECT+DELETE,
  **no TRUNCATE**; transaction-scoped `GRANT aa_app_user` to the runner, revoked before COMMIT.

Tests: `shared.tenant_integrations` added to `TENANT_TABLES` (WHERE-less read + new WHERE-less DELETE case;
INSERT/UPDATE/TRUNCATE denied); new `tests/integration/test_aa817_migration_237.py` (11). conftest revokes the
CI-only `app_user` blanket grant on this table (Dev has no such grantee).

## Evidence
| file | what |
|---|---|
| `migration-number.txt` | 237 is the next free number: CIS and Infra origin/main both end at 236; no branch/PR holds 237; Dev max 236 |
| `dev-probe-before-237.json` | read-only Dev probe (BEGIN READ ONLY, rolled back; `logs/aa817_ti_probe.py`): owner aa_cis_admin, rls false, force false, ACL = owner + aa_app_user SELECT only, **0 rows**, shared.job idle, runner cannot SET ROLE aa_app_user (guard 3 will use the GRANT path), tenant-pool login reads 0 rows (vacuous: empty table) |
| `logs/aa817-tests-verbose.txt` | 54 passed: isolation (19), migration 237 (11), migration 229, tenant-pool content, AA-815 SQL |
| `logs/integration-full-summary.txt` | full CI integration command: 300 passed, 1 skipped |
| `logs/unit-acp-summary.txt` | `tests/unit` + `tests/acp`: 4751 passed |
| `logs/mutation-checks.txt` | 7 mutations, each caught (tests or a guard aborting the apply) |
| `cmp-proof.txt` | CIS file vs Infra copy: `cmp` exit 0, same sha256 and git blob |

Integration run: local throwaway PostgreSQL 16 cluster (port 55817, superuser `cistest`, timezone UTC),
the same command as CI's Integration Tests job; CI runs postgres:15 and Dev is 15.17. Not run on PG15 locally.

## Not done (next steps)
1. Push both branches, open the CIS PR (migration-only, not auto-merged) and the Infra byte-copy PR.
2. Nghiệp approves Infra PR → DB Migrate `check` → `apply` with `shared.job` idle → schema dump PR.
3. Post-apply probe: Dev table is **empty**, so seed one test connection (E2E WordPress test site / FB test
   Page) before probing foreign / empty / own.
4. Observed window (Nghiệp approves): flag `aa544:integration_disconnect_pool` on, test tenant disconnects →
   200, row gone, secret tombstoned. Code PR then updates the stale "Do NOT turn on yet" comment
   (`api/core/aa544_tenant_pool.py:47-50`) and should consider `fail_closed=True` for `_disconnect`.
5. Housekeeping from the same scope addition (DM-8.4 line, stale branch `chore/aa-817-role-matrix`) not done here.
