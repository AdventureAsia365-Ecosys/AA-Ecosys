# staff.roles.v1 — custom staff roles between CIS and AA-Booking (two key-only views)

Root ADR 0006a A14 (AA-1155, tech lead S285 decision Q2 = option A). The CIS staff directory is the only place a
person's roles are assigned. A WORKFORCE group `booking-custom` / `cis-custom` only says "a custom role"; the two views
below carry WHICH one, in each direction. Spec: `.kiro/specs/AA-1155-custom-staff-roles/`.

## staff.booking_grant (CIS → AA-Booking)

| | |
|---|---|
| View | `shared.v_staff_booking_grant` (CIS migration 462), owner `cis_owner`, `security_barrier` |
| Readers | role `booking` only: `SELECT` on the view + `USAGE` on schema `shared`; `shared.admin_users`, `shared.staff_app_grant` and `shared.staff_role` stay closed (AA-CIS-Infra `db/owners.yaml` consumer grant, isolation probe cell `consumer.contract_grants.462` and cross-app cells) |
| Key | `cognito_sub` (the WORKFORCE sub of the caller's token) |
| Rows | one per active directory row with a Cognito identity that holds a Booking grant, `is_owner` or `is_business_owner` |

| Column | Type | Meaning |
|---|---|---|
| `cognito_sub` | text | the WORKFORCE sub (`pii:online_id`, the key) |
| `booking_role_code` | text, null | the Booking role of the CIS Staff page grant: a built-in role or a `booking.staff_role` code (`custom_...`); null = no Booking grant |
| `is_owner` | boolean | the platform owner flag (staff directory writes) |
| `is_business_owner` | boolean | the business-owner marker, at most one person |

## staff.role_capability (AA-Booking → CIS)

| | |
|---|---|
| View | `booking.v_staff_role_capability` (Booking migration bk-062), owner `bk_owner`, `security_barrier` |
| Readers | role `cis_app` (the CIS "Roles & permissions" page and the Staff page pickers): `SELECT` + `USAGE` on schema `booking`; `booking.staff_role` stays closed (probe cell `consumer.contract_grants.bk-062`); role `booking` itself |
| Rows | one per (custom role, capability); a role without a capability has one row with `capability` null |

| Column | Type | Meaning |
|---|---|---|
| `role_code` | text | `custom_...` |
| `label` | text | the role's display label |
| `based_on` | text | the built-in role it was cloned from |
| `archived` | boolean | true = no longer assignable; a holder is refused |
| `capability` | text, null | a capability name of `backend/app/auth/staff.py` PERMISSIONS (never the approve class) |

## Rules

- Key-only: no e-mail, name, CIS role or free text in either view (CI policy of the owner migrations' guards).
- Columns are append-only; a change of meaning is `staff.roles.v2` (new views).
- Booking reads `staff.booking_grant` only for a `booking-custom` holder and for the owner markers, cached at most 60
  seconds, and **fails closed** for a custom holder (view unreadable, no row, unknown or archived role = 403).
  Built-in holders never read it.
- CIS treats a missing `booking.v_staff_role_capability` (42P01 / 42501) as "no Booking custom roles" on the matrix
  page and in the pickers (fail soft: a read-only page).
