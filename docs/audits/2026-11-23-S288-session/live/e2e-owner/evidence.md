# E2E owner live run on Dev: business-owner preparation and owner-only checks (AA-1176, S288)

- When: 2026-11-23, 14:31–15:07 UTC. Run by an agent signed in as the Dev-only E2E owner
  `e2e-owner@e2e-mail.lumiguides.it.com` (root ADR 0006a A10h): CIS administrator with the owner marker, Booking
  admin, no CRM role.
- This is the main record. `evidence-copy2.md` comes from a second copy of this lane that ran at the same time. The
  coordinator stopped it. Its only writes were two `PUT …/business-owner` calls, both refused with 403.
- Sign-in: Cognito managed login with an e-mail code. The code was read from the S3 prefix `inbound-admin/` with the
  MFA admin profile. It was never printed, logged or screenshotted, and no screenshot was taken on the sign-in host.
  The local browser state file was deleted at the end.
- Masking: every `@adventure.asia` address except `info@` was masked in the page before each screenshot. The
  business owner is written here as t***@adventure.asia.
- Runbook followed: `docs/guides/business-owner-onboarding-and-pricing.md`, Parts A and B.

## Prerequisites

| Time (UTC) | Check | Result |
|---|---|---|
| 14:03–14:26 | CIS `/health/ready`, polled every 3 min | schema 472 → 473 at 14:09; AA-CIS-App #1649 merged at 14:25 (merge `8019c841`) |
| 14:29 | CIS `/health/ready` | `schema_version` 473, `git_sha` `8019c841…` (identical to the merge commit) |
| 14:31 | First sign-in | no code mail: the WORKFORCE pool had no E2E owner user yet; reported to the coordinator |
| 14:43–14:55 | Coordinator | Cognito user created (groups `cis-admin` + `booking-admin`); Infra run-script `aa1176_e2e_owner_row.py` run first as a DRY RUN, then applied (row `admin`, `is_owner` true, Booking `admin`) |
| 14:56 | Sign-in | OK. `GET /api/admin/session` 200: `role admin`, `read_only false` |

## Steps

| # | Step | Result | Evidence |
|---|---|---|---|
| 1 | Platform › Staff & access says platform owner | **done** | Page text "As a platform owner you can add accounts and change roles and access here; …". `GET /api/admin/platform/roles`: `can_view_as: true`. `01-cis-staff-platform-owner.png` |
| 2a | Staff account for the business owner, preset Business owner | **done, existing row used** | A row for t***@adventure.asia already existed (created 2026-10-18, display name "ThuLe", CIS admin, no Booking role, invite sent 2026-10-18, never signed in, not linked). Runbook A1 step 3 says to use the existing row, so **Add staff was not sent and no invitation went out**. The display name stays "ThuLe": the drawer has no name field. The drawer showed **Business owner › Apply** → **Apply**, then "Business owner preset saved in CIS and the company sign-in…". `PATCH …/roles` 200, Cognito steps `add_group:cis-admin`, `add_group:booking-admin`. The row is now CIS Administrator + Booking admin. `02a-thu-business-owner-preset.png` |
| 2b | Make business owner (the marker) | **refused (by design)** | The drawer showed **Make business owner** → confirm. The API answered `PUT …/business-owner` **403** "The E2E owner account may not change the business owner" (A10h D5). The marker is still not set. `02b-thu-business-owner-marker.png` (the error toast had faded when the shot was taken; the drawer still offers "Make business owner") |
| 3a | Tenants › Directory › New Tenant | **done, CRM part needs the tech lead** | Company Name "Test Agency - Business Owner" (hyphen, as in the runbook), slug `test-agency-business-owner`, plan starter, Posts/week 1, CRM add-on **CRM Core (crm.core)**, Agency owner e-mail empty. `POST /api/admin/tenants/provision` 202, tenant `c4e6a94f-f2f9-4ffa-9f28-18d1a7e11dc7`. Outcome: Tenant account Done, Content studio subscription Done (active), CRM add-on Done, **CRM agency: Needs a look (crm_unavailable)**, **Owner invitation: Needs a look (crm_unavailable)**. The CRM onboarding error is `{"step":"agency_read","http_status":503,"code":"crm_unavailable"}`. Cause: the E2E owner has no `crm-platform-admin` group, and the CRM agencies page says "Read only: your staff account is not in the crm-platform-admin group, so the actions are hidden". The runbook B1 also says an `e2e-` account can never create a CRM agency. `03a-new-tenant-form.png`, `03b-new-tenant-outcome.png`, `03d-crm-agencies-page.png` |
| 3b | Monthly AI budget 2 USD | **done** | Tenant 360 › Cost › AI budget: **Set a budget**, Monthly budget (USD) 2 → Save → confirm. `PUT /api/admin/ai-gateway/tenant-budgets/c4e6…` 200: `monthly_usd 2.0`, `alert_pct 80`, `approval_pct 100`, `hard_stop true`. The tile now reads "$2.00 … Set here (replaces the plan's included spend) · E2E owner (agent, Dev only)" (before: $15.00 from the plan). `03c-tenant360-ai-budget.png` |
| 4 | Invite first owner | **not clicked** (held for the morning) | The button would not be shown anyway: CRM agency actions need `crm-platform-admin` |
| 5 | info@adventure.asia as Content, invitation sent | **done** | Add staff: Work email info@adventure.asia, Display name "Adventure Asia info", Role **Custom (show all roles)**, CIS role **Content** (`custom_content`), Booking role none, no CRM role, **Send invitation email** ticked → Create account. `POST /api/admin/platform/staff` 201, Cognito `create_user`, `add_group:cis-custom`. Banner: "Created info@adventure.asia. An invitation email with the sign-in steps goes to that address in about 2 minutes." `05a-add-info-content-form.png`, `05b-add-info-content-created.png` |
| 6 | Platform › Compliance readiness › Refresh evidence | **done; crm_ops now has a last-seen** | `POST /api/admin/platform/compliance/refresh` 200: published file 17 rows read, 17 new. Live `cis_db` ok (2 rows: 1 pass, 1 fail). Live `crm_ops` ok (HTTP 200, 2 rows: 1 pass, 1 manual). After the refresh the page shows `cis_db` and `crm_ops` "Last evidence 23 Nov 2026, 22:01" (+07). The line under the button reads "Published evidence file: 17 results read, 17 new". The toast was gone before the shot. The failing check is AAC-PRV-06: "3 retention kind(s) never had a live run (DRY RUN only)". `06b-compliance-after-refresh.png` |
| 7a | CIS view as the custom role "Content" | **partly works: banner bug found** | Roles & permissions › **View as** on Content. Defaults: 30 min, reason "Check what this role sees" → Start view. The session started (`GET /api/view-as/roles`: `active true`, `view_role custom_content`, `read_only true`; `/api/admin/session`: `role custom_content`, `reason view_as`) and the page landed on `/admin/my-work`. Probe `POST /api/admin/s288-view-as-probe` → **403 `view_as_read_only`** (as expected). Server-side scope holds: `/admin/platform/staff` redirects to My work, and `/api/admin/platform/roles` → 403 "Only an admin can do this". **But no banner showed, and the sidebar still listed every section** (F1 below), so there was no **Back** button. Back was done the way the banner's Back does it: `DELETE /api/view-as/roles` 200 `{"ended":true}`, then Roles. After that the view was inactive and the session was back to `admin`. `07a-cis-view-as-content-no-banner.png`, `07b-cis-view-as-ended-roles.png` |
| 7b | Booking view as "Product, ops & accounting" | **done** | Booking sign-in reused the CIS company sign-in (no new code). `/api/booking/staff/me`: role admin, name "E2E owner (agent, Dev only)". Roles › View as a role: role `custom_product_ops_accounting`, 30 min, reason empty (optional) → Start. Banner: "Viewing as Product, ops & accounting · Read only: every change is refused. Your own sign-in is not changed. · Ends in 31 min · Back". Probe `POST /api/booking/s288-view-as-probe` → **403 `view_as_read_only`**. **Back** → `/roles`, `staff/me` `role admin`, `view_as null`, no banner. `07c-booking-view-as-product-ops-accounting.png`, `07d-booking-view-as-back.png` |
| 8 | Sign out | **done** | Booking account menu → Sign out → `/login`; `staff/me` 401. CIS account menu → Sign out → `/login`; `/api/admin/session` 401. |

## Findings

- **F1 (bug, AA-1157 CIS): the CIS view-as banner and the filtered nav never show.**
  - The BFF writes the display cookie `cis_view` already URI-encoded: `frontend/lib/staffViewCookies.ts`
    `setStaffViewCookies` → `res.cookies.set(STAFF_VIEW_DISPLAY_COOKIE, displayCookieValue(display), …)`, and
    `displayCookieValue` = `encodeURIComponent(JSON.stringify(d))`. Next's `ResponseCookies` encodes the value again.
  - The browser holds `%257B%2522role%2522…` (seen in `document.cookie`). `parseDisplayCookie` decodes only once,
    so `JSON.parse` fails, `StaffViewAsBanner` gets null, and the nav hint gets nothing.
  - The server-side read-only rules hold (403 `view_as_read_only`, admin pages refused), so this is a UI problem,
    not a security one. Still, the owner has no Back button and no sign that a view is running. The view ends only
    at expiry, or by signing out (the logout route clears the cookies).
  - Fix: write the raw JSON and let `cookies.set` encode it, or decode until stable. Add a unit test that
    round-trips through `ResponseCookies`.
  - The `viewas-banner.spec.ts` admin-evidence spec could not catch this: before AA-1176 no E2E identity could start
    a view.
- **F2 (expected, needs the tech lead): the CRM agency for the test tenant was not created.** The E2E owner has no
  `crm-platform-admin` group (A10h, by design). The tenant, the Content studio subscription, the CRM add-on and the
  AI budget exist. The CRM agency must be created by the tech lead: **Tenants › CRM agencies › Create agency** for
  "Test Agency - Business Owner" (runbook B1 "If a row shows attention"). The dialog has no retry button.
- **F3 (expected): the E2E owner cannot set the business-owner marker** (A10h D5). This stays a tech-lead step
  (runbook A5).
- **Note:** the business owner's staff row existed before this run (since 2026-10-18), with display name "ThuLe".
  It was not renamed to "Lê Thư". If the name matters, rename it outside this run.

## Writes on Dev made by this run

- Staff row t***@adventure.asia: preset Business owner (Booking role none → admin; CIS admin unchanged). Cognito
  groups `cis-admin` + `booking-admin`. No invitation.
- Tenant "Test Agency - Business Owner" (`c4e6a94f-f2f9-4ffa-9f28-18d1a7e11dc7`) with crm.core, plus its AI budget of
  2 USD a month.
- Staff row info@adventure.asia (custom role Content, `cis-custom`), invitation queued.
- One compliance refresh.
- One CIS view-as session (custom_content, started and ended) and one Booking view-as session
  (custom_product_ops_accounting, started and ended).
- One refused business-owner change (403, nothing changed).

## Left for the morning (tech lead)

1. The business owner's staff account: the row exists and the Business owner preset is applied. When the business
   owner is ready, use **Resend invite** on the row (runbook A3). The last invite was sent 2026-10-18. Then do the
   first sign-in (A4), **Make business owner** (A5), Booking (A6) and the authenticator setup (A7).
2. Test agency: **Tenants › CRM agencies › Create agency** for "Test Agency - Business Owner" (F2). Then
   **Invite first owner**, ticking **Also invite to the Content studio as owner** (runbook B3).
3. Fix F1 (CIS view-as display cookie double encoding).
