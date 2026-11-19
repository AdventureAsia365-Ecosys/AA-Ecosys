# Design - custom staff roles

Spec: [requirements](requirements.md). Decision record: root ADR 0006a A14 (transport, roles as data), A10f and A10g
(E2E identities). Source: `docs/audits/2026-11-19-S285-session/plan-audit-roles-trang.md` section 3.4.

## Decisions

### D1 Booking reads a person's custom role through a CIS contract view (Q2 option A)

Hard to reverse: yes (a cross-app grant and a contract between two apps)
Approved: tech lead, S285 decision Q2 = option A (AA-1155)

CIS publishes `shared.v_staff_booking_grant(cognito_sub, booking_role_code, is_owner, is_business_owner)`: active
directory rows with a Cognito sub that hold a Booking grant or an owner marker; no e-mail, name or CIS role.
`booking` gets USAGE on schema `shared` and SELECT on the view only (CIS 462), mirrored in AA-CIS-Infra
`db/owners.yaml` `consumer_grants` and the isolation probe (base tables stay 42501). The CIS directory stays the only
writer of a person's roles (ADR 0006a A1). Rejected: option B (Booking keeps the role on its own `/staff` page): two
places to assign one person. Not `catalog.*`: the content read model has its own owner role and recipe.

### D2 Custom roles only in the tables; built-in roles stay in code

Hard to reverse: no (tables can be emptied; the code never depended on them for built-ins)

`staff_authz.ROLE_PERMS` (CIS) and `staff.PERMISSIONS` (Booking) stay authoritative. Only `cis-custom` /
`booking-custom` holders read the tables, so a table or view outage refuses custom holders and never an administrator.

### D3 One code pattern for custom roles in both apps

Hard to reverse: no (a CHECK)

`^custom_[a-z][a-z0-9_]{1,46}$`: never equal to a built-in role, so `shared.staff_app_grant_role_chk` accepts a
Booking custom code without a cross-schema foreign key and `booking.staff_users.role` can hold the resolved code.
Booking validates the code against `booking.staff_role` (unknown or archived = refused).

### D4 The approve class is reserved for built-in roles, in code and in the database

Hard to reverse: no (a CHECK and a code list)

Booking: `*.approve`, `*.approve_<x>`, `supplier.activate`, `contract.publish`, `stop_sale.approve`, `payout.write`,
`payment.verify`, `billing_config.write`, `staff.admin`. CIS: `*.approve`, `*.approve_<x>`, `staff.write`,
`staff.admin`. The editor answers 400; a table CHECK refuses the same names if the code is bypassed. `supplier_bank.*`
is not refused by the CHECK (Q10 may add `supplier_bank.write`, entry only).

Reserved ahead of use: `pricing.approve`, `supplier.activate`, `contract.publish` and `stop_sale.approve` are not in
Booking `PERMISSIONS` on main today. Until the AA-1150 Booking split and task T4.1 re-gate the routes, `supply.write`
(supplier, hotel and service activate, contract publish), `stop_sale.write` (stop-sale review and end), `pricing.write`
(approve of pricing rules, FX rates, cancellation policies, agency pricing and price adjustments) and `b2b_desk.write`
(allotment approve) still carry those approvals. The seed keeps these write capabilities; the CHECK and the code then
refuse the new approve capabilities to custom roles. So T5 starts after both, and no one gets `booking-custom` before.

### D5 A custom CIS holder keeps a built-in base role that is never admin

Hard to reverse: no

`shared.admin_users.role` is NOT NULL, so a `cis-custom` holder keeps the custom role's `based_on` there
(informational; authorisation never falls back to it). `based_on` is never admin, viewer or reviewer and
`admin_users_custom_role_chk` refuses a custom holder whose role is one of them, so no code that still tests
`role == 'admin'` lets a custom holder through.

### D6 The business-owner marker is a column, one holder at most

Hard to reverse: no (a column and an index)

`shared.admin_users.is_business_owner` with a partial unique index; set on the Staff page by an `is_owner` user,
audited. Approvals that need it (AA-1158) read it server-side from the view. No `booking-business_owner` group.

### D7 Two Dev-only E2E identities prove the flow with real sessions

Hard to reverse: no (removed with the A10 family)

A10f `e2e-cis-content-lead@` (exactly `cis-content_lead`): the second person of two-person publishing. A10g
`e2e-custom-maker@` (exactly `cis-custom` + `booking-custom`): the custom-role maker, created by the Infra identity
tool so the token proof runs right after Terraform Apply. Both codes land in the MFA-admin-only mailbox prefix.

### D8 Migrations are contract files in one batch per owner

Hard to reverse: no

CIS 462 and bk-062 alter existing tables and seed rows: contract (ADR 0017 d3), migration-only PRs (MIG-4), applied by
Infra Migration Apply when `shared.job`, `booking.job` and `crm.job` are idle. The view-as columns of AA-1157 are not
in CIS 462: that design is not final.

## Cost

0 USD a month: two Cognito groups, two trigger entries, two SES recipients on an existing rule, four small tables and
two views.
