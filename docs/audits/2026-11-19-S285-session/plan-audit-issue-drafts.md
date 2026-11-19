# Linear issue drafts: lean roles and My work (S285 re-plan)

Status: drafts only. Per the Linear rules, the tech lead approves before anything is created (Q12 in
`plan-audit-roles-trang.md`). The drafts give five new issues and one re-scope. Each is one deliverable slice (a small
group of PRs).

Names used here:
- **tech lead** (Administrator role)
- **business owner** (Business owner role)
- **content+ops staff** (the "Content + Product, operations & accounting" role)

Product UI never shows person names or issue IDs.

Project placement:
- Booking-led slices go to "TripPlanner & AA-Booking". CIS-only slices go to the CIS project.
- Check that each project has fewer than 100 unarchived issues before creating.
- Milestone for all six: **M-ROLES** ("Lean permissions + My work", S286–S289).

Rules that apply to every slice:
- **Migration rule:** a DB Migrate `apply` runs only when `shared.job`, `booking.job` and `crm.job` are all idle (DM-11.4). Apply migrations before any paid LLM run in the same session.
- **Review:** every auth, permission, migration or money PR gets an independent agent review before the orchestrator merges it.

---

## AA-1150 (re-scope, existing issue)

**Title:** `[CIS + Booking] Lean staff roles step 1: three people-role presets, finance reads, make/approve capability split, one sign-in`

### Problem
The approved model is three people-roles: Administrator, Business owner, and Content + Product & operations.

The Staff page still offers 8 CIS and 5 Booking roles, and has no preset for that model.

In Booking:
- `content_creator` is still a role.
- `finance` cannot read bills, prices, supply, ops, trip cases or catalog (L7a).
- Approve rights are bundled into write rights:
  - `supply.write` activates suppliers and publishes contracts.
  - `stop_sale.write` reviews and ends stop-sales.

  As a result, a role that makes work but does not approve it cannot be expressed.

Nothing proves that one WORKFORCE sign-in opens every app a person needs.

### Scope
**CIS** (`api/services/staff_directory.py`, `api/routers/admin_platform.py`, `frontend/app/admin/platform/staff/StaffManage.tsx`, `messages.ts`):
- Add three presets: "Administrator", "Business owner" and "Content + Product & operations". Put every other role behind "Show all roles".
- Drop `content_creator` from `BOOKING_ROLES`. Add a retired-groups list so Sync strips `booking-content_creator`.
- Change the Booking role label to "Product & operations".

**Booking** (`backend/app/auth/staff.py`, `routers/suppliers.py`, `seasons_admin.py`, `frontend/lib/rbac.ts`, `CONTEXT.md`):
- L7a: give `finance` `bill.read`, `pricing.read`, `supply.read`, `ops.read`, `trip_case.read` and `catalog.read`. Add `F` to the matching page rules.
- Split three new capabilities out of the write rights:
  - `supplier.activate` (`POST /suppliers/{ref}/activate`)
  - `contract.publish` (contract `status=published`)
  - `stop_sale.approve` (review or end a stop-sale)
- Built-in `admin` and `contracting` keep all three new capabilities. The A10e-2 pricing checker E2E and the CIS "Pricing team" preset keep working.

**Out of scope** (each moves to its own issue):
- Custom roles → NEW-R1.
- View-as → NEW-R2.
- Approval rules, owner self-approval, supplier profile and bank accounts → NEW-R3.
- `payout.write` for finance is dropped: payouts stay admin only, and the business owner records them.
- The KMS need is answered (A1 = yes).
- "Sales sees a masked account" is removed, because `sales` is hidden under the lean model.

### Done-when
- [ ] Staff page shows the three presets. Applying "Content + Product & operations" sets CIS `content_lead` and no Booking role, until NEW-R1 lands. Screenshots taken.
- [ ] Sync removes `booking-content_creator` from a test user. Cognito `list-users-in-group` shows 0 holders.
- [ ] A `finance` user gets 200 on `/billing` reads, pricing, supply and ops reads.
- [ ] A user with `supply.write` but without `supplier.activate` gets 403 on activate. The same holds for contract publish and stop-sale review/end. Covered by CI tests.
- [ ] Pricing E2E (A10e-2) is green.
- [ ] One sign-in:
  - A non-admin E2E staff user signs in once and opens CIS `/admin`, then Booking staff, with no second sign-in prompt (Playwright trace).
  - Repeated with the content+ops staff member's real account (screenshots).
- [ ] CIS and Booking deploys reach rollout COMPLETED. `/health` and `/booking/health` return 200.

Size M · Migration no · Depends on the live check (slice 0) · Session S286.

---

## NEW-R1: `[Booking + CIS] Custom staff roles: roles as data, one combined role per person`

### Problem
Booking resolves exactly one role per person: the first `booking-*` Cognito group (`backend/app/auth/staff.py` `BOOKING_GROUP_ROLES`). Capabilities are a hard-coded dict.

The content+ops role needs contracting and finance make/read rights with no approve rights. No built-in role expresses that.

A `booking-custom` group alone does not say *which* custom role a person holds:
- The assignment lives in CIS `shared.staff_app_grant`, which Booking cannot read.
- `cis_app` cannot write `booking.*`.

CIS roles are also a code dict plus an enum, and the frontend gates pages by role lists.

### Scope
**Transport** (decision Q2; recommended option A; record it in an ADR 0006 amendment):
- CIS publishes a key-only contract view `shared.v_staff_booking_grant(cognito_sub, booking_role_code, is_owner, is_business_owner)`.
- Only the `booking` role gets SELECT. Mirror it in Infra `db/owners.yaml` `consumer_grants` and the isolation probe.
- `is_business_owner` is a new server-side marker on `shared.admin_users`, held by at most one person (partial unique index). It is set only on the Staff page by an `is_owner` user, with audit.

**Infra PR** (apply first, with MFA), in `accounts/aa365/identity.tf` and `lambda_src/identity_triggers`:
- Add WORKFORCE groups `booking-custom` and `cis-custom`. Each grants nothing by itself.
- Add one E2E "maker" identity that holds `booking-custom` (write-capable, not read-only).
- Add the A10f E2E `content_lead` identity.
- Add trigger tests.

**One CIS migration** (next free number) holding every CIS role schema change:
- `shared.staff_role` and `shared.staff_role_capability` for custom roles only.
- `admin_users.custom_role` and `admin_users.is_business_owner`.
- `staff_app_grant_role_chk` widened so it accepts Booking custom role codes.
- The contract view above.
- If NEW-R2's design is final in time, also the staff view-as columns. That saves one apply.

**One Booking migration** (next free bk-NNN):
- `booking.staff_role` (code, label, based_on, archived) and `booking.staff_role_capability`, for custom roles only.
- A key-only view of role → capability, granted to `cis_app` for the matrix page.

**Built-in roles stay in code.** `PERMISSIONS` and `ROLE_PERMS` stay authoritative:
- The tables hold only custom roles.
- Each capability in the tables is validated against the code's capability set.
- Only `booking-custom` / `cis-custom` holders fail closed when the table or the view cannot be read.

**Approve-class capabilities are reserved for built-in roles.** Code refuses any custom role that contains one: `*.approve`, `supplier.activate`, `contract.publish`, `stop_sale.approve`, `payout.write`, `payment.verify`, `billing_config.write`, `staff.admin`.

**Booking code:**
- `Staff.can()` resolves `booking-custom` holders through the transport view, with a 60 s cache.
- Role editor page: clone a built-in role, then tick capabilities. Only `is_owner` staff may use it. Every change is audited before and after.
- Frontend page rules switch from role letters to `me.permissions`.

**CIS code:**
- `staff_authz` reads custom roles from the table.
- `/auth/verify-admin` returns the caller's capability list. `rbac.ts` `can()` and `PAGE_RULES` read it.
- The CIS role table is seeded. There is no CIS editor UI until a second CIS custom role is needed.
- Staff page pickers list each app's roles.

**Read-only "Roles & permissions" page** (CIS), generated from code and the tables:
- CIS and Booking roles.
- The 3 CRM staff groups as static rows.
- TripPlanner shown as "no staff roles".

**P13:** the AI cap routes (`admin_budgets.py`, `admin_ai_gateway*.py`) require a verified Cognito session and write a before/after audit row on budget changes.

**Seeds** (exact allow-lists, each with a unit test):
- Booking "Product, ops & accounting":
  - `supply.read/write`, `pricing.read/write`, `trip_plan.write`, `stop_sale.write`, `catalog.read`, `ops.read/write`, `b2b_desk.read/write`, `staff.directory`, `bill.read/write`, `billing.read/write`, agency billing make/read, `profit.read`.
  - Only if Q3 says yes: `b2b_desk.book`, `trip_case.read/write`, `customer.read/write`.
  - The test asserts the role has no approve-class capability, `payout.write`, `billing_config.write` or `supplier_bank.*`.
- CIS "Content": `content_lead` minus `content.settings.write`, plus `tenant.read` (Q7).

**Order:**
1. Infra PR, applied with MFA.
2. CIS + bk- migrations, applied when all job tables are idle.
3. Schema-reference PR merged.
4. Booking + CIS code deployed.
5. Hand step: switch the content+ops staff member to the custom role.

The CIS part starts only after the CIS PR of AA-1150 merges, because both touch `staff_directory.py` and `StaffManage.tsx`.

### Done-when
- [ ] Terraform applied. A decoded token of a `booking-custom` holder carries the group.
- [ ] CIS and bk- migrations applied on Dev by DB Migrate. The schema-reference PR is merged. The isolation probe is green.
- [ ] Custom role assigned from the CIS Staff page. After sign-in:
  - the holder gets 200 on `/suppliers`, `/billing` and `/agency-billing`;
  - the holder gets 403 on supplier activate, contract publish, stop-sale review, payout and billing-config writes.

  Use the E2E maker identity, or API integration tests in CI if no write-capable E2E session is possible (say which).
- [ ] Saving a custom role with any approve-class capability is refused (400). Covered by a unit test.
- [ ] A non-owner gets 403 on every role-editor write. An owner's change appears in the audit with before and after.
- [ ] With the role table or the transport view revoked in a test:
  - custom-role holders are denied;
  - admin still signs in and opens `/staff` in both apps.
- [ ] A budget route call with a forged `x-admin-role` and no session gets 401/403.
- [ ] The matrix page shows all four apps. It has no agent rows, no E2E rows, no person names and no issue IDs.
- [ ] Pricing E2E is green. Deploys reach rollout COMPLETED. `/health` and `/booking/health` return 200.

Size L · Migration yes (CIS + bk-) · Depends on AA-1150, Q2, Q3 · Session S286 (Infra + migration PRs) → S287 (apply, code, hand step).

---

## NEW-R2: `[CIS + Booking] View as a lower role: read-only, logged, never changes the sign-in`

### Problem
The tech lead and the business owner cannot see what a lower role sees without a second account.

CIS view-as covers tenants only (`api/core/view_as.py`, `shared.staff_view_as_session` with `tenant_id` NOT NULL). Booking has no view-as, and it cannot trust a CIS view-as session.

### Scope
- **CIS:** widen the view-as session to staff roles (`tenant_id` NULL + `view_role`). This is folded into the NEW-R1 CIS migration if ready, otherwise it is its own migration.
- **Booking:** a signed, short-lived cookie (60 min) plus the existing Booking audit log, with no new table. The viewer's `is_owner` comes from the NEW-R1 transport view.
- **In both apps:**
  - Only `is_owner` staff may start view-as.
  - "Downward" means the target role's read capabilities are a subset of the viewer's (Q6).
  - Every non-GET request is refused before the route runs.
  - The start row logs the viewer, the target role, the target role's full capability list and the time. The end row is logged too.
  - A banner and a "Back" button are shown. The Cognito session is untouched.

### Done-when
- [ ] The tech lead views as "Content + Product & operations" and sees that role's nav in CIS and in Booking (screenshots with the banner).
- [ ] Every POST/PATCH/DELETE during the view gets 403. A test covers each app.
- [ ] A view-as to a role whose read rights go beyond the viewer's is refused. A non-owner cannot start view-as.
- [ ] The audit shows start and end rows, and the start row holds the target role's capability list.
- [ ] The sign-in session id is the same before and after.
- [ ] Deploys reach rollout COMPLETED.

Size L · Migration CIS (or none if folded into NEW-R1), Booking none · Depends on NEW-R1 · Session S288.

---

## NEW-R3: `[Booking + Infra] Approval rules for a three-person team, business-owner self-approval, supplier profile and bank-detail controls`

### Problem
With three people, strict maker ≠ checker blocks the business owner's own work. Several approval gaps remain:
- New suppliers are active at once (R5).
- The contract maker check reads only `updated_by or created_by` (R4).
- The payer can be the bill approver (R3).
- `billing_config.write` lets one person change AA's `payment_instructions` (the bank details printed on agency invoices) and `is_default` with no second person.
- A tour can be made `sellable` with no approved price.
- Suppliers lack a legal entity, tax ID, role contacts and payment terms.
- There is no controlled place for supplier bank accounts, which is the main payout fraud path.

### Scope
**Part 1** (bk- migration + code, session S288):
- R5: supplier status `pending` plus an `activated_by` CHECK (activator ≠ creator).
- R4: contract writer list plus a CHECK.
- R3: payer ≠ bill approver in `supplier_bills.py`, with a `same_approver_payer` flag. The business owner may both approve and record a payout, flagged (Q4). The tech lead is the fallback payer. The content+ops role never holds `payout.write`.
- Owner self-approval:
  - Add `owner_self_approved` columns and relaxed CHECKs on suppliers, `supplier_contracts`, price versions and seasons, `supplier_bills`, `agency_payment`, price adjustments and the billing entity change.
  - The flag is accepted only when the approver's server-side record carries `is_business_owner` (from the NEW-R1 transport view). It is never taken from a request field.
  - The tech lead never self-approves.
  - Scope is per Q5. Not included: Pricing › Policy rules and lifting a stop-sale.
- Billing entity: changes to `payment_instructions` and `is_default` stay pending until a second person approves (business owner self-approval flagged), then apply.
- `sellable = true` requires an approved price version, or the tour being price-ready (Q9). Check the existing readiness logic first.
- No digest job. Add a saved audit filter `owner_self_approved = true`, shown on the owner's Booking dashboard.

**Part 2** (Infra KMS PR, then bk- migration + code, session S289):
- One KMS key for supplier bank data (A1, about 1 USD/month). Only the Booking task role can use it.
- Supplier profile fields: legal entity, tax ID, contacts by role, structured payment terms.
- A `supplier_bank_account` table encrypted with that key, with capabilities `supplier_bank.read`, `supplier_bank.write` and `supplier_bank.approve`.
- A change stays pending until the business owner approves it, with a call-back note.
- After any approved change, a 24 h payout lock applies to that supplier.
- If Q10 is yes, add `supplier_bank.write` (entry only) to the content+ops custom role.

### Done-when
- [ ] Both bk- migrations applied on Dev. Schema-reference PRs merged. Terraform applied (the key exists and its policy allows only the Booking task role).
- [ ] A supplier created by the content+ops role stays `pending`. Activation by its creator is refused. Activation by the business owner works.
- [ ] The business owner creates and activates a supplier: the row has `owner_self_approved = true`.
- [ ] The tech lead approving his own supplier, contract or bill is refused at both the API (4xx) and the DB (CHECK or trigger).
- [ ] The bill approver recording the payout is refused, except for the business owner, whose payout is flagged.
- [ ] A `payment_instructions` change stays pending until approved. Invoices keep the old details until then.
- [ ] Setting `sellable = true` on a tour with no approved price is refused.
- [ ] A bank account entered by a non-owner stays pending. A payout to that supplier is refused until it is approved and 24 h have passed (test with a clock override). The stored number is ciphertext in the DB and masked in the UI for roles without `supplier_bank.read`.
- [ ] The owner's dashboard shows the self-approval filter.
- [ ] Deploys reach rollout COMPLETED. `/booking/health` returns 200.

Size L (two parts) · Migration yes (bk- ×2) · Depends on NEW-R1, Q4, Q5, Q9, Q10 · Sessions S288 (part 1), S289 (part 2).

---

## NEW-W1: `[CIS] My work: one queue page for content roles`

### Problem
Content staff have no list of what is due. They check about 15 pages: Review Queue, supply copy, AA content, place cards, compliance holds and others.

AA-1148's planned content desk (M0) waits for the tour editor, so it would arrive late.

### Scope
- New page `/admin/my-work` ("My work"). It is shown by capability, never by person.
- **Content band.** Each tile shows a count, the age of the oldest item and one link to the exact filtered page:
  - Review Queue waiting
  - supply copy drafts, and hotels or activities with no description
  - AA content drafts
  - place cards to review
  - compliance holds
- When AA-1148 lands, add these tiles: my drafts, returned to me, tours below 100% complete, tours without a cover photo.
- `landingPage()` sends content roles here. Admin keeps `/admin/overview`, with My work in the nav.
- A link "Booking: My work" opens the Booking dashboard through `appPageUrl`, for users with a Booking grant (from `/auth/verify-admin` once NEW-R1 returns it; until then the link is shown to content roles).
- Refresh button, no polling. English by default, Vietnamese on choice. Built with the UI kit.
- Replaces AA-1148 M0.

### Done-when
- [ ] Signed in as the E2E content role, the user lands on `/admin/my-work`. Each tile count matches the filtered count on its target page on Dev (screenshot pairs).
- [ ] Screenshots on desktop and mobile, in light and dark. No console errors.
- [ ] Admin still lands on `/admin/overview`.
- [ ] Deployed and live on `aa-cis.lumiguides.it.com`.

Size M · Migration no · Depends on none · Session S286.

---

## NEW-W2: `[Booking] My work on the staff dashboard: permission-filtered queues, filtered lists, approvals waiting`

### Problem
The content+ops role's Booking work has no queue. The work covers supplier bookings, B2B on-request lines, price readiness, expiring contracts, stop-sales, supplier bills and agency invoices.

The dashboard (`app/(staff)/page.tsx`) shows only trip-case tiles. Some lists do not exist:
- bills due within 7 days
- contracts expiring
- supplier bookings across cases

Notifications target built-in roles, so custom-role holders miss them. Makers cannot see what waits for a second person, and the business owner has no approvals inbox.

A cross-app contract view read by CIS is deliberately not built (Q8). It is added only if switching between the two apps proves to be a real problem.

### Scope
- A "My work" band on the Booking staff dashboard. It reads Booking's own tables, with no migration. Tiles show by `me.permissions`:
  - supplier bookings to send or waiting on the supplier (`ops.read`)
  - B2B on-request lines (`b2b_desk.read`)
  - trip checks due
  - tours not price-ready (`pricing.read`)
  - contracts expiring within N days (N is a Policy setting, editable in admin)
  - stop-sales waiting for review
  - bills to enter, bills due within 7 days, bills approved but unpaid (`bill.read`)
  - agency invoices overdue and payments to approve (`agency_billing.read`)
- New filtered lists the tiles open:
  - `/billing?due=7d` and "approved, unpaid"
  - contracts expiring
  - a supplier bookings list across cases
- A "CIS: My work" link in the Booking nav.
- The notifications service targets by capability, so custom roles receive `supplier_bill.due`, `supplier_booking.waiting`, `b2b.on_request` and `invoice.overdue`.
- After NEW-R3 part 1 lands:
  - a "Waiting on someone else" band for makers (contracts to publish, suppliers to activate, bills to approve, bank and billing-entity changes);
  - a "Waiting on me" band for the business owner, which is the approvals inbox, including the self-approval audit filter.

### Done-when
- [ ] The content+ops custom role sees its tiles. A CIS-only content user with no Booking grant sees none.
- [ ] Each tile opens its filtered list (200), and the count matches a DB check on Dev (screenshots).
- [ ] A custom-role user receives a due-bill notification in a Dev test.
- [ ] A supplier created by the content+ops role appears in that user's "Waiting on someone else" and in the business owner's "Waiting on me". After activation it disappears from both.
- [ ] The tech lead viewing as the content+ops role (NEW-R2) sees that role's band, read-only.
- [ ] Desktop and mobile screenshots. Deploy reaches rollout COMPLETED.

Size M · Migration no · Depends on NEW-R1 (capabilities), NEW-R3 part 1 (waiting bands), NEW-R2 (view-as check) · Sessions S287–S289.

---

## Changes to other existing issues (comments or edits, no new issues)

- **AA-1145:** drop ", lean staff roles" from the title. Live-verify R6, then mark Done.
- **AA-1146:** close on part 1 (D1, D5, CIS 457/458) with live evidence. Part 2 (Tour editor page) moves to AA-1148.
- **AA-1148:**
  - Remove M0 (replaced by NEW-W1).
  - Remove "Content staff work only in CIS". Keep "`content_creator` hidden from Booking".
  - Add AA-1146 part 2.
  - Add `photos.upload`, its authz part after NEW-R2 merges.
  - Sessions S288–S290.
- **AA-1121:** close as a duplicate of AA-1103, with a comment that points to it. Do not delete.
