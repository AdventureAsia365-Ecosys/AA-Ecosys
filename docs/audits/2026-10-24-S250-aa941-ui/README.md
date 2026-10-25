# AA-941 (CRM-13a) — live UI check of the AA admin L1 console (S250, 24/10/2026)

Page under test: CIS admin Production `https://aa-cis.lumiguides.it.com/admin/platform/agencies`
(screen S-01, "Platform › Tenants › Agencies (CRM)"; the agency detail is a drawer on the same page, not a separate route).

## Who may see the page (from the code)

| Layer | Rule | Source |
|---|---|---|
| CIS frontend proxy | `/admin/platform*` pages: role `admin` only; any other staff role is redirected to its own landing page | `frontend/lib/rbac.ts` PAGE_RULES, `frontend/proxy.ts` |
| CIS BFF `/api/admin/platform/*` | role `admin` only | `frontend/lib/rbac.ts` (API rule `platform`) |
| CIS API `/admin/platform/crm/*` | GET needs `tenant.read`, writes `tenant.write` (both `admin` role only) | `api/core/staff_authz.py`, `api/routers/admin_crm_console.py` |
| CRM `crm.ops.v1` | reads: Cognito group `cis-admin` or `crm-platform-admin`; writes: `crm-platform-admin` only | `admin_crm_console.py` docstring, AA-941 ship comment |

So a full check needs a staff user with CIS role `admin` **and** WORKFORCE group `cis-admin` (read) or
`crm-platform-admin` (read + write actions).

## Method

1. Local headless Playwright (chromium, repo `apps/AA-CIS-App/node_modules`), one browser, against the Production host.
2. Sign-in with the existing E2E staff user `e2e@e2e-mail.lumiguides.it.com` through the shared helper
   `tests/e2e/helpers/cognitoSignIn.ts` (managed login on `staff-auth.lumiguides.it.com`, email code read from the
   SES inbound mailbox in S3 with the operator's `aa365-admin` credentials). No screenshot during sign-in; the code
   and tokens were never printed or stored.
3. With the session: `GET` the BFF routes the page calls, then open the page at 1440 px light, 1440 px dark
   (`localStorage.cis_theme`), 390 px light; capture console errors and every `/api/*` response.
4. Without a session: `curl` the BFF, the CIS API and the CRM `crm.ops.v1` directly.
5. No user, group, role, secret, workflow or repo change. No CI dispatch: no workflow signs in as an admin
   (`e2e-cognito.yml` runs a fixed sign-in spec; `ui-smoke.yml` covers this page only as `viewerRefused`).

## Results

| Check | Expected | Observed | Result |
|---|---|---|---|
| Cognito email-code sign-in on Production | lands under `/admin` | landed on `/admin/review`, cookies `cis_admin_token`, `cis_role`, `cis_user`; role `reviewer` | Pass |
| Open `/admin/platform/agencies` as reviewer | refused (admin-only page) | redirected to `/admin/review` (Review Queue); "Agencies (CRM)" not in the nav (0 links) | Pass (correct refusal) |
| BFF `GET /api/admin/platform/crm/console` with reviewer session | 403 | 403 `{"detail":"Only an admin can do this"}` | Pass (refusal) |
| BFF `GET /api/admin/platform/crm/agencies?limit=50` with reviewer session | 403 | 403 `{"detail":"Only an admin can do this"}` | Pass (refusal) |
| BFF `GET /api/admin/tenants` with reviewer session | 403 | 403 `Role 'reviewer' lacks the 'tenant.read' permission` | Pass (refusal) |
| BFF `GET /api/admin/platform/crm/console` / `agencies` without session | 401 | 401 `{"error":"Unauthorized"}` (both) | Pass |
| CIS API `GET /admin/platform/crm/console` / `agencies` without auth | refused | 403 `{"detail":"Invalid admin secret"}` (both) | Pass |
| CRM `GET /crm/ops/v1/console` / `tenants` without token (`partner-dev.lumiguides.it.com`) | 401 | 401 `{"detail":"missing_bearer_token"}` (both) | Pass |
| Console errors during the run | none | 0 | Pass |
| Network errors during the run (`/api/*` ≥ 400 other than the probes above) | none | 0 (all page calls 200, `/api/auth/refresh` 200) | Pass |
| 390 px horizontal scroll (landing page) | none | none | Pass |
| Agency list with the 3 E2E agencies, columns (Agency, State, Synthetic, Owner, Has travellers, Created), Refresh / Create agency, row → drawer with meters and L1 actions | rendered with real data | **not reachable**: the only E2E staff identity is `reviewer` | **Not tested** |
| BFF agencies `200` with a session | 200 | not reachable with a reviewer session | **Not tested** |

Fixed Preview host `https://aa-cis-preview.lumiguides.it.com` was not used: its session is capped at `viewer`, which
is refused by the same rules, and the host is behind Vercel Authentication (302 without bypass).

## Screenshots (all show the reviewer's redirect to Review Queue, not the agencies console)

- `01-reviewer-agencies-redirect-1440-light.png`
- `02-reviewer-agencies-redirect-1440-dark.png`
- `03-reviewer-agencies-redirect-390-light.png`

## Verdict

**Not done.** The refusal paths are verified live (reviewer → redirect + 403; no session → 401; CRM without token → 401),
but the S-01 console itself (list with real data, drawer, meters, actions) could not be rendered: it needs a CIS staff
user with role `admin` that is also in the WORKFORCE group `cis-admin` (read-only view) or `crm-platform-admin`
(view + write actions). The E2E staff user has CIS role `reviewer`, which the CIS proxy, BFF and API already refuse before
the CRM group is ever checked (its Cognito groups were not inspected).

To close: either Nghiệp signs in with his own admin account (in `crm-platform-admin`) and the same script captures the
page, or the E2E staff user is temporarily promoted to `admin` + added to `cis-admin` for one run and set back
afterwards (a staff-directory + Cognito group change, out of scope for this check).

## Admin attempt: temporary elevation of the E2E user (S250, later the same day)

Nghiệp approved one temporary elevation of `e2e@e2e-mail.lumiguides.it.com` (WORKFORCE pool `aa-workforce-dev`)
for a single run, restored afterwards.

| Step | Observed |
|---|---|
| Where the CIS role comes from | Cognito groups only (`api/core/staff_identity.py` `GROUP_ROLES`: `cis-admin` → `admin`); `shared.admin_users.role` is not used for authorisation (a difference is only logged as `staff_role_drift`), so no DB change was made |
| Groups before | `["cis-reviewer"]` |
| Elevated (twice, one run each) | `["cis-admin", "cis-reviewer", "crm-platform-admin"]` |
| Email-code sign-in on Production | **refused** on the code step: `PreTokenGenerationV2_0 failed with error Not authorised for AA staff sign-in.` (no token issued, never reached `/admin`) |
| Groups after (restored by a shell `trap`, re-read) | `["cis-reviewer"]`, equal to before: **yes** (both runs) |

Cause (by design): the WORKFORCE pre-token trigger
(`infra/AA-CIS-Infra/accounts/aa365/lambda_src/identity_triggers/workforce.py`, AA-816 "option B", root ADR 0006a)
issues a token to the E2E address only while its staff groups are **exactly** `E2E_TEST_STAFF_GROUPS = ("cis-reviewer",)`.
It is a code constant on purpose ("no configuration can widen it"), and a wider group set is refused, not stripped.
So the E2E user cannot be elevated by a group change alone. The CIS directory holds the same rule
(migration 250, `staff_directory.E2E_TEST_STAFF_EMAIL`).

No screenshots `04-…` onward were produced: the console page was never reached. Each refused sign-in wrote one
`Deny` line in the WORKFORCE trigger's log ("E2E test account outside its allowed groups").

### Verdict (admin part)

**Not tested; still open.** The admin view (list with the 3 E2E agencies, columns, Refresh, Create agency
open/cancel, drawer meters and actions, API 200 with a session) needs one of:

1. Nghiệp signs in with his own admin account (in `crm-platform-admin`) and the spec
   `.tmp-session/s250/aa941-admin/verify.spec.ts` is run against that session (e.g. a saved storage state); or
2. a deliberate, reviewed change to the E2E exception (trigger code constant + migration 250 rule), which is a
   security-boundary change outside a verification run.

## Admin session (Nghiệp, 24/10/2026 ~16:20 UTC, Chrome on Windows)

The E2E user cannot be elevated (the workforce pre-token Lambda pins it to exactly `cis-reviewer`, A10), so Nghiệp
opened the page with his own CIS admin session.

- `https://aa-cis.lumiguides.it.com/admin/platform/agencies` renders the live CRM data: 3 E2E agencies (Southern Cross
  Journeys, Lữ hành Sen Vàng, Harbour Lights Travel Co.), state ACTIVE, SYNTHETIC badge, owner Yes, has travellers.
- The drawer (Southern Cross Journeys) shows: usage meters (seats 4 / 10, active members 0, storage 0 B, AI spend
  $0.000 of $2.00 budget, failed jobs 0, inbound mail "not tracked yet", last activity none), Access, First owner
  (owner_exists), Features allowed (plan free, 10 seats), AA insights (included), Data requests (none), Owner recovery
  (4 members: 2 owners, 2 agents, all active), Failed jobs (7 days): none; Refresh button.
- The page and drawer say "Read only; your staff account is not in the crm-platform-admin group", so the write actions
  are hidden — the designed behaviour for an admin without that CRM group. Write actions were not clicked live; they
  are covered by the CRM API tests (401 without token, 403 without the group) and the S249 console E2E.
- Screenshot: [10-admin-agencies-drawer-nghiep.png](10-admin-agencies-drawer-nghiep.png).
