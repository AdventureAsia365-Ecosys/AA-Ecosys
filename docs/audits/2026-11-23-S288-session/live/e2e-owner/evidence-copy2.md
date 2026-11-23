# E2E owner live check: evidence from the second (resumed) copy of the lane

- When: 2026-11-23, 14:03–15:05 UTC, by an agent signed in as the Dev-only E2E owner (root ADR 0006a A10h, AA-1176).
- Why there are two files: a resumed second copy of this lane ran at the same time as the original one. Once
  the audit log showed the overlap, the coordinator stopped this copy before step 7. The original lane's
  `evidence.md` is the main record. This file lists only what this copy saw and did.
- Sign-in: the managed-login e-mail code was read from the admin mailbox prefix by the MFA admin role. The code was
  never printed, logged or shown in a screenshot.

## Prerequisites as observed

| Time (UTC) | Check | Result |
|---|---|---|
| 14:03 | CIS `/health/ready` | `schema_version` 472; AA-CIS-App #1649 still open |
| 14:09 | CIS `/health/ready` | `schema_version` 473 (DB Migrate apply 473 at 14:07) |
| 14:25 | AA-CIS-App #1649 | merged, merge commit `8019c841` |
| 14:29 | CIS `/health/ready` | `git_sha` `8019c841…` (identical to the merge commit), `schema_version` 473 |
| 14:31 | First sign-in attempt | no code mail: the WORKFORCE pool had no user for the E2E owner address yet (SES rule `e2e-cognito-admin` already listed it) |
| 14:43 | Cognito user | present, groups exactly `cis-admin` + `booking-admin` |
| 14:44 | Infra run-script `aa1176_e2e_owner_row.py` | DRY RUN: 0 rows matched, 3 writes planned |
| 14:46 | Sign-in attempt | Cognito accepted the code, but CIS answered `/login?error=no_access` (no directory row yet) |
| 14:53 | Infra run-script, apply | row created as `admin`, `is_owner` true, Booking role `admin`, 3 audit rows |
| ~14:56 | Sign-in | OK; `/api/admin/session` 200 `role: admin`, `read_only: false` |

## Steps

| # | Step | Result | Evidence |
|---|---|---|---|
| 1 | Platform › Staff & access shows a platform owner | **done** | Page text "As a platform owner you can add accounts and change roles and access here…"; `GET /api/admin/platform/roles` `can_view_as: true` ((screenshot removed: duplicate of the main record, it showed the username)) |
| 2a | Staff row for the business owner | **not added (row exists)** | A row for t***@adventure.asia has existed since 2026-10-18 (display name "ThuLe", CIS admin, Booking admin, invite sent 2026-10-18, never signed in, not linked). Runbook A1 step 3 says to use the existing row, so no Add was sent. The display name was not changed. The **Business owner** preset shows "Current". The audit log shows the original lane applied it at 14:58:15 (`staff.roles_changed`, preset `business_owner`, Booking role null → admin). |
| 2b | Make business owner | **refused, as designed** | Two tries from the drawer: `PUT /api/admin/platform/staff/<id>/business-owner` → **403** "The E2E owner account may not change the business owner" (A10h D5: the E2E owner never sets or clears the marker). The drawer shows the error ((screenshot removed: duplicate of the main record, it showed the username)). The marker stays a tech-lead step. |
| 3 | Test agency + AI budget | **done by the original lane** (not repeated here) | Tenant "Test Agency - Business Owner" (`c4e6a94f…`, plan starter) provisioned at 14:59:53. `GET /api/admin/ai-gateway/tenant-budgets/<id>`: `monthly_usd` 2.0, `alert_pct` 80, `hard_stop` true, `state ok`, set by "E2E owner (agent, Dev only)" at 15:00:19. Tenant 360 › Cost shows "AI budget (this month) $2.00, within budget" (`copy2-3-tenant360-ai-budget.png`). |
| 4 | Invite first owner | **not clicked** | held for the morning |
| 5 | info@adventure.asia as Content, invitation sent | **done by the original lane** (not repeated here) | `staff.created` at 15:00:47: role `custom_content` (custom role "Content", base `content_lead`), no Booking or CRM role, `send_invite: true`, display name "Adventure Asia info". `staff.invite_requested` was queued in the same second. The drawer shows CIS role Content, Booking None, CRM None, last invited "Sending" ((screenshot removed: duplicate of the main record, it showed the username)). |
| 6 | Compliance › Refresh evidence | **done by the original lane** (not repeated here) | Refresh at 15:01:14. `GET /api/admin/platform/compliance` heartbeat: `crm_ops` last seen 2026-11-23T15:01:11Z, `ok: true`, 2 evidence rows (it now has a last-seen). `cis_db` was refreshed at the same time (4 rows), and `root_daily` at 11:15:34 (54 rows). |
| 7 | View as (CIS Content, Booking Product, ops & accounting) | **not run by this copy** | The coordinator stopped it. The original lane runs it. |

## Writes made by this copy

Only the two refused `PUT …/business-owner` calls (403, nothing changed) and the CIS sign-in itself. No tenant,
no staff row, no invitation, no refresh and no view-as session came from this copy.

## Left for the morning

- The tech lead sets the business-owner marker on the business owner's row (Make business owner). The E2E owner
  cannot set it.
- Staff invite to the business owner: the row exists and its last invitation was sent 2026-10-18. Use **Resend
  invite** (runbook A3) when the business owner is ready.
- Tenants › CRM agencies › the test agency › **Invite first owner** (runbook B3).
