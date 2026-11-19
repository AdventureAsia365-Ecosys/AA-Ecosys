# Tasks - custom staff roles

- [ ] T1 WORKFORCE groups cis-custom and booking-custom, trigger entries A10f / A10g, mailbox recipients, identity tool e2e-custom-maker, owners.yaml consumer grants and isolation probe entries - repo: AA-CIS-Infra - lane: l4-custom-roles-foundation
  _Requirements: R1.1, R1.2, R3.1, R3.2_
- [ ] T2 CIS 462: staff_role, staff_role_capability, admin_users.custom_role and is_business_owner, staff_app_grant_role_chk, A10f / A10g email rule, view shared.v_staff_booking_grant, Content seed - repo: AA-CIS-App - lane: l4-custom-roles-foundation
  _Requirements: R2.1, R2.2, R2.3, R3.1, R3.3_
- [ ] T3 bk-062: booking.staff_role, booking.staff_role_capability, view booking.v_staff_role_capability, staff_users_role_chk, Product, ops & accounting seed - repo: AA-Booking - lane: l4-custom-roles-foundation
  _Requirements: R2.1, R2.2, R2.3, R3.2_
- [ ] T4 ADR 0006a A14 / A10f / A10g, DM-7.1 retention rows, schema ownership, this spec - repo: AA-Ecosys - lane: l4-custom-roles-foundation
  _Requirements: R3.1, R3.2, R6.1_
- [ ] T5 Booking resolver: booking-custom holders through the view and booking.staff_role (60 s cache, fail closed), staff_users role sync, readiness bk-062, A10g allow-list on synthetic records, approve-class 403 tests - repo: AA-Booking
  _Requirements: R4.1, R4.2, R4.3_
- [ ] T6 Booking role editor API: clone a built-in role, tick capabilities, is_owner only, audit before and after, 400 on approve-class or unknown capability, seed allow-list unit test - repo: AA-Booking
  _Requirements: R2.2, R2.3, R4.4_
- [ ] T7 Booking frontend: page rules from me.permissions, role editor page (kit components) - repo: AA-Booking
  _Requirements: R4.5_
- [ ] T8 CIS staff_authz reads custom roles (fail closed), readiness 462, /auth/verify-admin capability list, A10f / A10g directory rules, Content seed unit test; after the AA-1150 CIS PR - repo: AA-CIS-App
  _Requirements: R5.1, R5.2, R2.3_
- [ ] T9 CIS Staff page: role pickers per app (built-in + custom), Sync to cis-custom / booking-custom, business-owner marker (is_owner only, audited); after the AA-1150 CIS PR - repo: AA-CIS-App
  _Requirements: R5.3, R3.3_
- [ ] T10 CIS rbac.ts can() and PAGE_RULES from the capability list, read-only Roles & permissions page - repo: AA-CIS-App
  _Requirements: R5.2, R5.4_
- [ ] T11 AI budget and gateway routes: verified Cognito session, before / after audit of budget changes - repo: AA-CIS-App
  _Requirements: R5.5_
- [ ] T12 Rollout: Terraform Apply Dev, Migration Apply of CIS 462 and bk-062, schema-reference PR, isolation probe, maker token, deploys, hand step, pricing E2E - repo: AA-Ecosys, AA-CIS-Infra
  _Requirements: R1.1, R6.1_
