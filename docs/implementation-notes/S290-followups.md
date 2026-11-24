# S290 lane g-s289-followups: five small follow-ups of the S289 live checks (no new Linear issue)

The tech lead approved the list in the S290 session (item 7). One PR per repo: AA-Partner, AA-CIS-App, AA-CIS-Infra,
AA-TripPlanner-Web (two fixes), and this note in the root. No migration, no new setting, no paid call.

## Decisions

- **(1) CRM pull of tenants CIS no longer lists** (AA-Partner `app/cis/entitlement_feed.py`). The hourly reconcile asks
  CIS for the account snapshot of every agency the CRM holds; about 13 Dev agencies have no CIS tenant any more, so
  each pass got 404s (1,196 in 24 h on Dev). A 404 now marks the tenant *gone* inside the worker: one warning
  `crm_entitlement_tenant_gone`, then the next reconciles skip it without a call (`gone_count` in the job result). The
  event pull never skips it: an account event that names the tenant means CIS lists it again, so its snapshot is read
  and, on a 200, it leaves the gone set (`crm_entitlement_tenant_back`) and is projected as usual. A new worker asks
  once more per tenant.
- **(2) Session checks out of the CIS client error rate** (AA-CIS-App, AA-1140). `POST /auth/verify-admin` counts
  each 401 per 5-minute bucket in the api's Redis (`api/services/ops_status/session_checks.py`); the current-period
  signals read subtracts the count over the same span CloudWatch was read for and adds `session_checks`, which the
  CIS tile shows under the 4xx rate ("Session checks N (not counted)", EN + VI). Only those 401s: a 403, the 404s of
  retired tours and every other 4xx stay in the rate. The limit stays the `cis.ops.status_client_error_warn_pct`
  setting; the counters' life follows the `cis.ops.status_history_days` setting (+1 day).
- **(3) PII allowlist** (AA-CIS-Infra `db/gen_schema_reference.py`). The live reference lists three untagged Booking
  candidates, all supply data: `booking.supplier_contract_seasons.name`, `booking.rate_sheet_imports.file_name`
  (bk-069) and `booking.v_place_addons.title` (bk-070). They go on `PII_ALLOWLIST` with one-line reasons, nothing else.
- **(4) Another agency's trip id under a new session** (AA-TripPlanner-Web, AA-1160). A fresh session of agency B
  passed the token check and saw no draft (RLS hides A's), so the `trip_drafts` upsert met A's hidden row and RLS
  refused it (42501): 500 with rollback. `events.append_event` now raises `TripOfAnotherTenant` on exactly that
  SQLSTATE and `serve()` answers the existing 403 `forbidden` ("this trip belongs to another session"). Reads stay
  the 404 of an unknown trip; a known session of A under B's header stays 401.
- **(5) Planner heading in Vietnamese** (AA-TripPlanner-Web, AA-1160). The open route finder's heading and its Close
  button were literals; they read the `ROUTES` catalogue (vi "Lên kế hoạch từ tuyến của tour", "Đóng").

## Changed

- (1) No table: the gone set lives in the worker process (see Tradeoffs). CONTEXT.md job row updated.
- (2) No CloudWatch change and no migration; the route's OpenAPI text is unchanged (the docstring stays on the route,
  the body moved to `_verify_admin`).
- (4) 403 rather than 404: the same answer the guard already gives for a trip owned by another session of the same
  agency. The trip id is a random UUID, so the 403 tells nothing a caller could use.

## Tradeoffs

- (1) In memory vs a table: a table (or a column on `crm.entitlement_feed_state`) would need a contract migration and
  a MIG-4 chain for a Dev-only noise fix. The memory set costs one call per gone tenant per new worker (deploys),
  which is the "log once" asked for. Not covered: a tenant CIS brings back with the same id but without any account
  event is read again only by a new worker (CIS emits events on every account change, so this should not happen).
- (2) Redis counters vs API Gateway detailed metrics: API Gateway has no per-status count and its per-method metrics
  would cover the whole `/auth/{auth_proxy+}` resource at extra metric cost. Without Redis the tile shows CloudWatch's
  rate as before (never a guess); the net count never goes below 0. Counts start at deploy.

## Should know

- (1) The gone agencies stay in the CRM (active or locked, as they are). Removing them is a separate clean-up (the
  console's test-agency delete for synthetic ones).
- (3) The allowlist change moves the reference fingerprint, so the next DB Schema Dump opens the bot PR with the three
  rows under "Allowlisted" and no Booking candidate.
- (4) The pg test needs a local Postgres (`--pg-dsn`); it runs on the tp-028 FORCE RLS replay as the runtime role.
