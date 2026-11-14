# AA-1093 erasure saga: live DRY RUN drill on Dev (S279)

Date: 13/11/2026. Agent: Claude Code (subagent). Admin host: `https://aa-cis.lumiguides.it.com`, signed in as the
Dev-only E2E CIS admin (A10b, Cognito). CIS API `git_sha` 85db0005 (CIS #1477).

**Result: BLOCKED before the drill started.** The A10b session is read-only on every saga write route, and on
offboard and restore. Those routes are not on the A10b write allow-list (`api/core/e2e_staff.E2E_ALLOWED_WRITES`).
The staff bearer middleware refuses them with `403 e2e_read_only` before the route runs. Because restore is refused
too, the spec did not offboard the tenant: it could not have restored it afterwards. Nothing was offboarded,
drilled, approved or applied, and no data changed.

## Tenant

- Used: `audit-wildkind-travel`: synthetic (members/access gives the A10b session `invite=true`, which happens only
  when `is_canary` is true and the tenant is not the pilot), active, not offboarded.
- Also checked: `audit-trail-pulse`, also synthetic and active.

## Steps

| # | Step | Result |
|---|------|--------|
| 0 | Unauthenticated `GET /api/admin/job-runner/erasure/requests` (BFF) | **401** `{"error":"Unauthorized"}` |
| 0b | Unauthenticated `GET /admin/job-runner/erasure/requests` straight to the API | 403 `Invalid admin secret` (all `/admin/*` routes answer this way, e.g. `/admin/tenants`) |
| 0c | Unauthenticated `POST .../requests/drill` | BFF 401, API 403 |
| 1 | Sign in (company email, managed login, code) | ok |
| 2 | `GET /api/admin/job-runner/erasure/requests` | 200, **0 requests** on Dev. Settings: apply **off** (`cis.erasure.saga_apply_enabled`), windows CIS/Booking/TripPlanner 30 d, CRM 90 d, approval valid 24 h, environment `dev` |
| 3 | Data erasure > Tenant offboarding tab | renders: settings, empty request list, drill form (it lists offboarded tenants only) |
| 4 | Probe `POST .../requests/drill` `{tenant_id}` (tenant not offboarded: the route would answer 409 and write nothing) | **403 `e2e_read_only`** |
| 5 | Probe `POST .../requests/{random uuid}/advance` | **403 `e2e_read_only`** |
| 6 | Probe `POST .../requests/{random uuid}/stop` | **403 `e2e_read_only`** |
| 7 | Probe `POST /api/admin/tenants/{id}/restore` (tenant not offboarded: the route would answer 409) | **403 `e2e_read_only`** |
| — | Offboard | **not attempted**: it is not on the allow-list either, and the tenant could not have been restored |
| — | Drill to dry_run, worker poll, per-app plan hashes, Stop, restore | **not reached** |

## Per-app results

None. No request exists, so there are no CIS, Booking, TripPlanner or CRM DRY RUN steps, plan hashes or error codes
to report. What the code leads us to expect from a real drill (not observed): stage 1 = CIS + Booking +
TripPlanner. The CRM is stage 2 and only starts after stage 1 is done. Until the CRM erasure lane ships, the CRM may
show `app_not_ready`.

## What is needed to run the drill

Choose one:

1. **A10b allow-list amendment** (root ADR 0006a, "A10b-5"). Add these routes to `E2E_ALLOWED_WRITES` and
   `E2E_ALLOWED_WRITE_PATHS`, and accept them only for a synthetic tenant (`is_synthetic_tenant`, as A10b-3 and A10b-4
   do): `POST /admin/tenants/{id}/offboard`, `POST /admin/tenants/{id}/restore`, `POST .../requests/drill`,
   `.../{id}/advance` and `.../{id}/stop`. Never `approve` or `new-round`. The offboard and restore checks must go in
   the routes themselves, because offboard is a real-tenant write elsewhere. After that, run the spec with
   `E2E_DRILL_FULL=1`.
2. **The tech lead runs the drill** with his own Cognito admin session in the browser: Tenant 360 > Offboard
   `audit-wildkind-travel`, then Data erasure > Tenant offboarding > Start drill, Run now, wait, then Stop for good,
   then Tenant 360 > Restore.

## Evidence files

- `01-offboarding-tab-1440-light.png`, `01-offboarding-tab-1440-dark.png`: the Tenant offboarding tab at 1440 px.
- `drill-evidence.json`: the candidates, the settings, the requests before the run (none), and the probe answers.

Spec: AA-CIS-App `tests/e2e/admin-evidence/erasure-drill.spec.ts`. Opt-in (`E2EADMIN=1`). It is committed on the
local branch `test/aa1093-erasure-drill-spec` in the scratch worktree and has not been pushed. The full drill path
(`E2E_DRILL_FULL=1`) has not run yet. It restores the tenant in a `finally` block and never calls approve.

**Nothing was approved or applied.** The apply switch stayed off for the whole run.
