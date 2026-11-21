---
id: OPS-08-s287-aa1155-live-evidence
title: "S287 live evidence: AA-1155 custom staff roles (CIS Roles & permissions, Booking role editor)"
description: "Agent-run read-only Playwright evidence on the Dev hosts for AA-1155 (CIS #1624, Booking #294), 21/11/2026; maker checks pending the grant."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-21
review_every_days: 30
related: [AA-1155]
---

# S287 live evidence: AA-1155 custom staff roles (21/11/2026, about 12:00 +07)

Headless Chromium (Playwright), one browser at a time, after both deploys were live:
CIS API `/health/ready` git_sha `60867997` (schema `464`), Booking API `/booking/health` git_sha `d704f327`.
Hosts: CIS admin `https://aa-cis.lumiguides.it.com`, Booking staff admin `https://booking.lumiguides.it.com`.

Identities (by role; codes read at run time from the e2e mailbox, never written down; no screenshot of the managed-login
host): the Dev-only E2E CIS admin (read-only, not an owner) and the E2E Booking admin (`booking-admin`, read-only).
Only GETs, page views and `POST /auth/verify-admin` (it verifies the session's own token, nothing else) were sent.
Screenshots mask every @-address, the account chip and the E2E user chip.

## Results

| Req | Check | Result | Record |
|---|---|---|---|
| R5.2 | `POST /auth/verify-admin` as the E2E admin: 200, role `admin`, `capabilities` present (40), sorted, includes `staff.read`, equals the `cis_caps` cookie; `custom_role_label` null | **PASS** | `cis-readonly.json` `verify_admin` |
| R5.4 | `/admin/platform/roles` loads (`GET /api/admin/platform/roles` 200), sections CIS, CIS permission matrix, Booking, Partner CRM, TripPlanner all visible | **PASS** | `cis-platform-roles-1440-light.png`, `cis-platform-roles-390-dark.png` |
| R5.4 | CIS custom role `custom_content` "Content", based on `content_lead`, 18 permissions, holds `tenant.read`, not `content.settings.write` | **PASS** | `cis-readonly.json` `roles_api.content_role` |
| R5.4 | Booking custom role "Product, ops & accounting" listed (24 permissions, none approve-class); 3 CRM fixed groups (Agency admin, Operations, Support); TripPlanner "No staff roles" | **PASS** | same |
| R5.4 | No issue ID, e-mail, 12-digit account ID, E2E marker or "agent" text in the page body; console errors 0, failing requests 0 | **PASS** | `cis-readonly.json` `page.forbidden` |
| R4.2 | `GET /booking/staff-roles` as the Booking admin: 200, 5 built-in roles, custom `custom_product_ops_accounting` with 24 capabilities, 0 approve-class (by the D4 rule and by the API's own `assignable` flags), `can_edit` false (not an owner) | **PASS** | `booking-readonly.json` |
| R4.2 | Booking `/roles` page: custom role row, built-in roles read-only, the non-owner line "Only an owner (CIS → Platform → Staff) creates or changes custom roles.", no New / Edit / Archive buttons, console errors 0, failing requests 0 | **PASS** | `booking-roles-1440-light.png`, `booking-roles-390-dark.png` |

Observation (not a failure): the CIS catalogue lists 4 Booking built-in roles (admin, sales, contracting, finance), the
Booking role editor 5 (it also lists `content_creator`, permission `catalog.read`). The CIS Staff page treats
`content_creator` as a retired Booking role, so leaving it out of the CIS list looks intended; worth one line in the
spec if so.

## Pending the maker grant (not run)

The A10g maker (`cis-custom` + `booking-custom`) needs its CIS row set to `custom_content` and its Booking grant to
`custom_product_ops_accounting`. Prepared, not dispatched: run-script `aa1155_custom_maker_grants.py` (DRY RUN by
default) and the spec `aa1155-maker.spec.ts` (S287 scratch). They cover:

| Req | Check | Status |
|---|---|---|
| R5.1 | Maker `verify-admin`: role `custom_content`, label "Content", 18 capabilities, no `content.settings.write`; a content write (`PUT /api/admin/aa-content/<random uuid>/draft`) refused 403 `e2e_read_only`; Platform pages redirect | **PENDING grant** |
| R4.1 | Maker `GET /booking/staff/me`: role `custom_product_ops_accounting`, label "Product, ops & accounting", permissions equal to the 24 seed; `GET /booking/suppliers`, `/supplier-bills`, `/agency-invoices` 200 | **PENDING grant** |
| R4.3 | Maker gets 403 `forbidden` on each approve-class write (13 routes from the Booking PR's live steps, random UUIDs so nothing can change) | **PENDING grant** |

The Booking PR's maker write step (create a SYNTHETIC supplier, then deactivate it) is left out of the spec on purpose:
it creates a row.

## Needs the tech lead (is_owner session)

| Req | Check | Status |
|---|---|---|
| R3.3 / R5.3 | On CIS Staff & access, set the business-owner marker on one account; read `acp_shared.audit_log` action `staff.business_owner_changed` with `{is_business_owner: {before: false, after: true}}`; clear it again if it was a test | **NEEDS TECH LEAD** (the E2E admin is not an owner) |
| R5.5 | Change one AI budget value in the admin UI; the audit row holds before and after | **NEEDS TECH LEAD** (the routes need a real Cognito session; the E2E admin is read-only) |
| R4.4 | On Booking `/roles` as an owner: create, edit and archive a test role; audit `staff_role.created` / `staff_role.updated` with before / after; a non-owner admin gets 403 `owner_only` on `POST /booking/staff-roles` | **NEEDS TECH LEAD** for the owner half |

Not covered here: R5.5 "admin secret + forged role header gets 403" (a curl with the admin secret; the orchestrator's
step), the Staff page pickers listing the custom roles (render only for an owner).
