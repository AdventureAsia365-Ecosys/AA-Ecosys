---
id: spec-AA-1155
issue: AA-1155
title: Custom staff roles - roles as data, one combined role per person
status: approved
owner_repo: AA-Ecosys
kind: feature
approved_at: 2026-11-20 (S286 session list; decisions Q1, Q2 option A, Q3, Q7, Q11 by the tech lead in S285)
---

# Custom staff roles

## Problem

Booking resolves exactly one built-in role per person, the first `booking-*` Cognito group, and its capabilities are a
code dict. CIS roles are a code dict plus an enum, and the CIS frontend gates pages by role lists. The content +
operations staff member needs one combined role per app that no built-in role expresses: make and read rights across
supply, pricing, operations, supplier bills and agency billing (plus agency quote and booking, Q3) and no approve
right in Booking; content_lead without content settings, plus the tenant directory read, in CIS (Q7). A group alone
cannot say which custom role a person holds, and Booking cannot read the CIS directory. Source:
`docs/audits/2026-11-19-S285-session/plan-audit-roles-trang.md` section 3, `plan-audit-issue-drafts.md` NEW-R1.

## Requirements

### R1 Groups and E2E identities

- R1.1 THE SYSTEM SHALL provide the WORKFORCE groups cis-custom and booking-custom, which the pre token trigger keeps and which grant no capability without a custom role in the CIS directory.
  Verify: test accounts/aa365/lambda_src/identity_triggers_tests/test_workforce.py (AA-CIS-Infra); live: the decoded access token of the E2E custom-role maker carries booking-custom
- R1.2 WHEN the Dev-only E2E flag is on THE SYSTEM SHALL issue a token to the A10f content_lead address and the A10g custom-role maker only with their exact group sets, and SHALL refuse them with any other set or without the flag.
  Verify: test accounts/aa365/lambda_src/identity_triggers_tests/test_workforce.py and tools/identity/tests/test_crm_dev_identity.py (AA-CIS-Infra)

### R2 Roles as data

- R2.1 THE SYSTEM SHALL keep built-in roles in code and hold only custom roles in shared.staff_role / shared.staff_role_capability (CIS) and booking.staff_role / booking.staff_role_capability (Booking).
  Verify: test tests/integration/test_aa1155_migration_462.py (AA-CIS-App), backend/tests/integration/test_bk062_schema.py (AA-Booking)
- R2.2 WHEN a custom role is saved with an approve-class capability or a capability the code does not know THE SYSTEM SHALL refuse it (400 on the role editor, a CHECK violation in the database).
  Verify: test tests/integration/test_aa1155_migration_462.py, backend/tests/integration/test_bk062_schema.py; test the Booking role editor unit tests of task T6
- R2.3 THE SYSTEM SHALL seed the Booking role "Product, ops & accounting" and the CIS role "Content" with their exact allow-lists, and SHALL fail a unit test when a seed and the code's capability set disagree.
  Verify: test backend/tests/integration/test_bk062_schema.py, tests/integration/test_aa1155_migration_462.py; test the seed unit tests of tasks T6 and T8

### R3 Transport between the apps

- R3.1 THE SYSTEM SHALL publish the key-only contract view shared.v_staff_booking_grant (cognito_sub, booking_role_code, is_owner, is_business_owner), readable by the booking role only, while shared.admin_users, shared.staff_app_grant and shared.staff_role stay closed to it.
  Verify: test tests/integration/test_aa1155_migration_462.py (AA-CIS-App), db/tests/test_isolation_probe.py (AA-CIS-Infra); live: the isolation probe cell consumer.contract_grants.462 passes after the apply
- R3.2 THE SYSTEM SHALL publish the key-only view booking.v_staff_role_capability, readable by cis_app, while booking.staff_role stays closed to it.
  Verify: test backend/tests/integration/test_bk062_schema.py (AA-Booking), db/tests/test_isolation_probe.py (AA-CIS-Infra); live: the isolation probe cell consumer.contract_grants.bk-062 passes after the apply
- R3.3 THE SYSTEM SHALL let at most one staff member hold the business-owner marker, set only on the CIS Staff page by an is_owner user and audited before and after.
  Verify: test tests/integration/test_aa1155_migration_462.py (unique index); test the Staff page unit tests of task T9; live: the audit row of setting the marker on Dev

### R4 Booking

- R4.1 WHEN a booking-custom holder calls Booking THE SYSTEM SHALL resolve the role from shared.v_staff_booking_grant and booking.staff_role (cached at most 60 seconds) and SHALL answer Staff.can() from that role's capabilities.
  Verify: test the Booking auth unit and integration tests of task T5; live: the E2E maker gets 200 on /suppliers, /billing and /agency-billing
- R4.2 WHEN the view or the role table cannot be read, or the role is unknown or archived, THE SYSTEM SHALL refuse a custom holder and SHALL keep built-in holders, the administrator included, signed in.
  Verify: test the Booking integration test of task T5 with the grant revoked; live: admin opens /staff in Booking after the apply
- R4.3 WHEN a custom holder calls an approve-class write THE SYSTEM SHALL answer 403, including the approvals that a write capability gates today (pricing rules, FX rates, cancellation policies, agency pricing, price adjustments, allotments, supplier activate, contract publish, stop-sale review).
  Verify: test the Booking API integration tests of tasks T4.1 and T5; live: the E2E maker gets 403 on supplier activate, contract publish, stop-sale review and end, pricing-rule, FX-rate and cancellation-policy approve, agency tier-discount and rate-card approve, price-adjustment approve, allotment approve, payout and billing-config writes
- R4.4 WHEN a staff member who is not is_owner writes on the role editor THE SYSTEM SHALL answer 403, and SHALL audit every owner change with before and after.
  Verify: test the role editor unit and integration tests of task T6
- R4.5 THE SYSTEM SHALL gate the Booking admin pages by the capabilities in me.permissions instead of role names.
  Verify: test the Booking frontend unit tests, tsc and lint of task T7

### R5 CIS

- R5.1 WHEN a cis-custom holder calls CIS THE SYSTEM SHALL authorise from the custom role's capabilities and SHALL refuse the holder when the role or its capabilities cannot be read.
  Verify: test the staff_authz unit tests of task T8
- R5.2 THE SYSTEM SHALL return the caller's capability list from /auth/verify-admin and SHALL gate the CIS admin pages (rbac.ts can(), PAGE_RULES) by it.
  Verify: test the CIS API unit tests and the frontend tests of tasks T8 and T10
- R5.3 THE SYSTEM SHALL list each app's built-in and custom roles in the CIS Staff page pickers and SHALL put a custom holder in cis-custom / booking-custom on Sync.
  Verify: test the staff directory unit tests of task T9
- R5.4 THE SYSTEM SHALL show a read-only "Roles & permissions" page with the CIS and Booking roles, the three CRM staff groups as static rows and TripPlanner as "no staff roles", and SHALL show no agent rows, E2E rows, person names or issue IDs.
  Verify: test the page unit test of task T10; live: screenshot of the page on Dev
- R5.5 WHEN a budget or AI gateway route is called without a verified Cognito session THE SYSTEM SHALL answer 401 or 403 whatever x-admin-role says, and SHALL audit every budget change with before and after.
  Verify: test the CIS unit tests of task T11; live: curl with a forged x-admin-role and no session gets 401 or 403

### R6 Rollout

- R6.1 THE SYSTEM SHALL apply the change in the order Infra apply, CIS and Booking migrations, schema-reference PR, Booking and CIS code, hand step.
  Verify: live: Terraform Apply Dev, the Migration Apply run (CIS 462 and bk-062, class contract), the schema-reference PR merged, rollouts COMPLETED with /health and /booking/health 200, the content and operations staff member on the custom roles, pricing E2E green
