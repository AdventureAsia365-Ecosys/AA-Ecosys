# AA-817 — live verify of the two tenant-pool flags (S239, 16/10/2026, Dev)

Flags under test (turned on by Nghiep this morning; not changed here):

| Flag (Redis, value `"true"`) | Route(s) behind it | Code |
|---|---|---|
| `aa817:content_piece_reads_pool` | `GET /v1/content-writing/requests/{id}/latest-piece` (the only call site) | `services/acp_content_writing/service.py::fetch_latest_piece_for_request`, `fail_closed=True`, logs `aa817_latest_piece used_tenant_pool=` |
| `aa544:integration_disconnect_pool` | `DELETE /v1/integrations/wordpress`, `DELETE /v1/integrations/facebook` (both reads + the DELETE in `_disconnect`) | `api/routers/v1_integrations.py::_disconnect`, not fail-closed, **logs no pool** |

Deployed: CIS api :634 / worker :191. One api task served every call: `api/api/b931286ceb9d445183d068d5669d3b30`.

## Method

- Auth: `/v1/*` takes a tenant JWT (`get_tenant` -> `verify_tenant_jwt`). The script gets one from
  `POST /auth/tenant-login {api_key}` with the key read at run time from `aa-cis/dev/e2e-tenant/<slug>`.
  Keys, JWTs and the WordPress app password are never printed or saved (a scan of this folder for every
  secret value found 0 hits).
- Tenant A = **terra-family** (`20d07d32-…`) did all writes. atlas-hearth (`9149d3c6-…`), trail-pulse
  (`692a3214-…`), wildkind-travel (`885d4916-…`) were used read-only as the "foreign" tenants: each listed its
  own `GET /v1/content-writing/reviews`, so the foreign ids are real ids with real pieces (control C2).
- WordPress: TasteWP site from `aa-cis/dev/e2e-wordpress-test` (alive, `wp-json` 200). Its stored application
  password still worked (`users/me` 200), so no WP-admin/Playwright step and no new app password was created.
  terra-family had no WordPress or Facebook integration before (W0, W7a) and has none after: end state = start state.
- Script: `verify_flags.py` (run 05:15:13Z–05:15:50Z). Raw responses: `raw/*.json` (content_text cut to 120 chars).
  Log/metadata commands: `logs_queries.sh`; outputs in `logs/`.
- Only the public Dev API was called; nothing in Redis, the DB or AWS was changed by hand. Side effects of the
  normal API flow: one `shared.tenant_integrations` row created then deleted, `acp/cms/20d07d32-…` written
  (05:15:45Z) then tombstoned (05:15:48Z) by the app, one tenant audit row.

## Results — 29/29 API checks PASS

### Flag 1 — `aa817:content_piece_reads_pool`

| Check | Result | Evidence |
|---|---|---|
| C1.0–C1.8 terra-family reads its 9 own requests' latest-piece -> 200, piece with the same request id | PASS | `raw/c1_own_latest_*.json` |
| C2 each foreign tenant reads its own request (control: the foreign id does have a piece) | PASS (3/3) | `raw/c2_owner_latest_*.json` |
| C3 terra-family -> atlas-hearth / trail-pulse / wildkind-travel request ids | PASS: 200 `{"piece": null}` x3, no foreign content | `raw/c3_cross_latest_*.json` |
| C4 reverse: atlas-hearth -> terra-family's request id | PASS: 200 `{"piece": null}` | `raw/c4_reverse_latest.json` |
| C5 random UUID | PASS: 200 `{"piece": null}` | `raw/c5_random_latest.json` |
| Pool used (CloudWatch) | PASS: all 17 `aa817_latest_piece` lines in the run are `used_tenant_pool=True` (all 4 tenants) | `logs/api_window_raw.json`, `logs/insights_q5_latest_piece_today.json` |
| No 503 / fail-closed errors | PASS: 0 `aa817_tenant_context_unavailable`, 0 `aa817_tenant_guc_not_applied`, 0 "Tenant data path unavailable", 0 tracebacks/5xx in the window and 0 of these all day | `logs/insights_q1.json`, `logs/insights_q2.json` |

Today's 9 `used_tenant_pool=False` lines for this event are all at or before 03:33:17Z, before the flag went on;
none after (q5).

Context, not under test: `GET /v1/content-writing/pieces/{id}` is behind a different flag
(`aa544:stage5:get_piece_pool`), which is also on: own piece 200, the 3 foreign pieces 404 (C6, C7), all
`aa544_stage5_fetch_piece used_tenant_pool=True`.

### Flag 2 — `aa544:integration_disconnect_pool`

| Check | Result | Evidence |
|---|---|---|
| W0 status before | PASS: `connected=false` | `raw/w0_status_before.json` |
| W1 connect WordPress (TasteWP) | PASS: 200 `connected=true` | `raw/w1_connect.json` |
| W2 test connection | PASS: 200 `success=true` | `raw/w2_test.json` |
| W3 status | PASS: `connected=true`, site_url set | `raw/w3_status_connected.json` |
| **W4 `DELETE /v1/integrations/wordpress`** | PASS: 200 `disconnected=true` | `raw/w4_disconnect.json`, log `integration_disconnected` 05:15:48Z |
| W5 re-read | PASS: `connected=false` | `raw/w5_status_after.json` |
| W6 second DELETE (no row) | PASS: 200 `disconnected=false`, idempotent | `raw/w6_disconnect_again.json` |
| W7 `DELETE /v1/integrations/facebook`, tenant has none | PASS: 200 `disconnected=false` | `raw/w7_disconnect_facebook_none.json` |
| Secret tombstoned by the app | PASS: `acp/cms/20d07d32-…` new AWSCURRENT at 05:15:48Z (connect version 05:15:45Z is AWSPREVIOUS); metadata only, value not read | `logs/tenant_cms_secret_describe.json` |
| No 5xx / privilege errors | PASS: 0 tracebacks, 0 `permission denied` / `InsufficientPrivilege`, 0 `integration_secret_tombstone_failed` all day | `logs/insights_q2.json`, `logs/api_window_raw.json` |
| Pool used (CloudWatch) | **Not directly provable**: `_disconnect` logs no pool | see below |

Which pool served the disconnect is inferred, not logged. `acquire_scoped_conn` without `fail_closed` uses the
tenant pool when `app.state.tenant_pool` exists and the Redis value is exactly `"true"`. On the same task, in the
same minute, the tenant pool was up (21 `used_tenant_pool=True` lines from the content routes, 05:15:27–05:15:42Z),
Redis was readable (0 `aa544_flag_read_failed`), and Nghiep set the flag to `"true"`. So the DELETE ran as
`aa_app_user` under the 237 policy, and it succeeded, which matches the 237 `GRANT SELECT, DELETE`. If the flag value
were anything else, the same calls would silently run on the admin pool and give the same 200s. RDS has no
statement or connection logging (`log_min_duration_statement=500` only) and Performance Insights sampled nothing for
these ~1 ms queries, so the DB side cannot show it either.

## Gaps and follow-ups (for AA-817)

1. **Disconnect route has no pool proof and no fail-closed.** Suggest: log `used_tenant_pool` in `_disconnect`
   (like `aa817_latest_piece`) and pass `fail_closed=True`, so a missing tenant pool is a 503 rather than a silent
   fall back to the owner pool that RLS does not filter. Then re-run W4 for a direct log proof.
2. This is API-level proof (cross-tenant ids return nothing). The Linear Done-when, "forged foreign
   `app.tenant_id` returns 0 rows from every RLS table", is a DB-level check: the route's own
   `WHERE tenant_id = $2` would also hide foreign rows on the admin pool. RLS-alone evidence stays with
   `tests/integration/test_aa817_rls_tenant_isolation.py` and the 229/237 probes.
3. Facebook disconnect was only exercised on the no-row path (no FB test page connect in this run).
