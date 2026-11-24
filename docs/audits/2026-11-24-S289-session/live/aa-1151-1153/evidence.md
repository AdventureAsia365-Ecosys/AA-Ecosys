# AA-1151 add-on offers and AA-1153 hotel contracts: live check on Dev (S289)

- When: 2026-11-23, 22:04–22:15 UTC (2026-11-24 05:04–05:15 +07). Run by an agent, headless Playwright (Node, the
  Booking `frontend/node_modules`) against `https://booking.lumiguides.it.com` (BFF `/api/booking/*` →
  `https://api-booking.lumiguides.it.com/booking/*`).
- Deployed Booking API: `/booking/health` `git_sha ef1cf756…` (= `origin/main`, #314 AA-1153 part 1 on top of #313
  AA-1151), `/booking/health/ready` `schema_version bk-069`.
- Sign-in: Cognito managed login with an e-mail code, as in S288 (`2026-11-23-S288-session/live/e2e-owner/evidence.md`).
  The code was read from the S3 prefix `inbound-admin/` with the MFA admin profile (helper copied from the Booking
  `e2e/signed-in/helpers`). It was never printed, logged or screenshotted, and no screenshot was taken on the sign-in
  host. The local browser state files were deleted at the end.
- Identities (root ADR 0006a): the pricing maker (A10e-2 / A10e-3 / A10e-4), the pricing checker (A10e-2 / A10e-3),
  the E2E owner (A10h).
- **Writes on Dev made by this run: none.** The write flow could not start (blocker B1 below).

## Blocker B1: the pricing maker cannot sign in to Booking

| Time (UTC) | Step | Result |
|---|---|---|
| 22:05 | Sign in as the pricing maker (`e2e-cis-cs@…`, A10d / A10e-2) | Cognito accepted the code, then Booking sent the browser back to `/login?reason=forbidden`: "Booking refused this account. Ask a Booking admin to check your staff profile." |
| 22:06 | Read-only check of its WORKFORCE groups (`cognito-idp admin-list-groups-for-user`, pool `aa-workforce-dev`) | `cis-customer_success` only. The A10e-2 writer rule (`backend/app/auth/e2e_staff.py`, `pricing_maker`) needs exactly `{cis-customer_success, booking-contracting}`, so `check_session` refuses the token. |
| 22:06 | Pricing checker groups (same read) | `booking-contracting`, enabled |

This is the same state as S286 finding F3 (`2026-11-20-S286-session/live/evidence.md`): the "Pricing team" preset
(Booking `contracting`) was removed from the maker after the AA-1091 check (the A10e-2 revoke step) and was never put
back. Every maker step of A and B needs it. Per the lane rules no other identity was used in its place (the checker's
allow-list has no import, the E2E owner may not publish offers it wrote).

**Unblock (one step, a CIS owner):** CIS › Platform › Staff › row `e2e-cis-cs@…` › preset **Pricing team** › Apply
(Booking role `contracting`, one audited `roles_changed` row, A10e-2). The A10h E2E owner can open that drawer, but
granting a Booking role to an E2E identity was not part of this lane's brief, so it was not done here. Remove the grant
again after the check (A10e-2 "Revoke").

## Sign-ins that worked

| Time (UTC) | Identity | `GET /api/booking/staff/me` |
|---|---|---|
| 22:08 | E2E owner (A10h) | 200, `role admin`, name "E2E owner (agent, Dev only)", permissions include `addon.approve`, `addon.read`, `addon.write` |
| 22:08 | Pricing checker (A10e-2) | 200, `role contracting`, permissions include `addon.approve`, `addon.write`, `contract.publish` |

## A) AA-1151 add-on offers

| # | Step | Time (UTC) | Request → status | Excerpt / result | Evidence |
|---|---|---|---|---|---|
| A1a | Template download (owner) | 22:09 | `GET /activity-sheets/template` → 200 | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, 5 732 bytes; sheets `Contract` (Title, Reference, Valid from, Valid to, Currency, Payment terms, Cancellation policy) and `Activities` (Title, Places, Unit, Duration minutes, Max group size, Inclusions, Min pax, Cut-off hours, Weekdays, Start times, Net adult, Net child, Child age max, Child %, Season, Valid from, Valid to) | — |
| A1b | Fill 5 rows, DRY RUN, import (maker) | — | not sent | **blocked by B1**. The file is ready locally: contract "SYNTHETIC S289 AA-1151 activity catalogue (live check, not real)", USD, 2026-11-24 → 2027-01-15 (inside the 60-day window), 5 rows "SYNTHETIC S289 …" at Ho Chi Minh City (`d6b4a043-…`), no Inclusions, net adult 25 / 30 / 45 / 35 / 40; one row limited to Mon, Wed, Fri, one row valid only 2026-12-01 → 2026-12-10 (to show in-force days) | — |
| A2 | Checker publishes the draft contract | — | not sent | **blocked** (no draft: A1b) | — |
| A3 | Owner publishes the 5 offers | — | not sent | **blocked** (no draft offers: A1b) | — |
| A4 | Place add-on view (owner) | 22:09 | `GET /add-ons/place-days?destination_id=d6b4a043-…&date_from=2026-11-24&date_to=2027-01-31` → 200 | `{"items":[],"days_ahead":365}`: the route works and reads the policy horizon; no offer exists on Dev (`GET /add-ons` → 200 `{"items":[],"total":0}`), so the "only in-force days" rule could not be shown | — |
| A5 | Contracts ending soon (owner) | 22:09 | `GET /contracts/expiring` → 200 | `{"window_days":60,"today":"2026-11-23","items":[{"title":"SYNTHETIC S248 B2B verification contract","supplier_code":"SUP-000002","valid_to":"2027-01-21","days_left":59,"announced":true}]}` | `a5-addons-page__1440__light.png`, `a5-addons-page__390__light.png` |
| A5b | Window value on Pricing › Policy (owner) | 22:09 | `GET /pricing/policy` → 200 | "Contract expiring warning (days)" `contract_expiry_alert_days` **60 days**, v1 since 2026-01-01, approver Pricing lead; "Add-ons: days listed ahead" `addon_days_ahead` **365 days** | `a5-pricing-policy-expiry-window__1440__light.png` |

The Add-ons page (1440 and 390) shows the card "Contracts ending soon: Published supplier contracts that end within
60 days" with the pill "59 days left · SYNTHETIC S248 Supplier · SYNTHETIC S248 B2B verification contract · ends 21 Jan
2027", then "0 add-ons" and the empty state "No add-on yet". `announced: true` means the daily expiry job has already
sent its notification for this contract and end date.

**Keep / retire:** no SYNTHETIC offer was created, so nothing was retired and nothing is visible in
`booking.v_place_addons`. AA-1152 tonight still needs a published add-on: it will not find one until A1–A3 run.

## B) AA-1153 hotel contracts

| # | Step | Time (UTC) | Request → status | Excerpt / result |
|---|---|---|---|---|
| B0 | Rate-sheet template (owner) | 22:09 | `GET /rate-sheets/template` → 200 | 9 563 bytes; sheet `Hotel` has `Hotel code, Room type, Season, Valid from, Valid to, Meal plan, Pax min, Pax max, Net, Notes, Published, Commission %`; new sheets `Seasons` (Season, From, To) and `Hotel children` (Hotel code, Age min, Age max, Basis, Meal plan, Net) |
| B0b | Default board (owner) | 22:09 | `GET /pricing/policy` → 200 | `hotel_default_board` (type `code`) is in use |
| B1 | Maker creates a SYNTHETIC hotel + a second SYNTHETIC DMC | — | not sent | **blocked by B1** |
| B2 | Link the hotel to the second DMC | — | not sent | **blocked by B1**. Note for the rerun: `POST /booking/hotels/{hotel_ref}/suppliers` is **not** in the pricing maker's allow-list (`e2e_staff.py`: supplier create / deactivate, rate-sheet and activity-sheet import, contract status, hotel / room type / service create and deactivate only), so this step will answer 403 `e2e_read_only` even after the grant. A rate sheet of the second DMC only matches hotels linked to it, so "one hotel with 2 DMC contracts" cannot be shown with the E2E pair as the allow-list stands. |
| B3 | Import "70 USD, 20 %" → net 56 with both source numbers | — | not sent | **blocked by B1** (possible on the first DMC's own hotel once the grant is back) |
| B4 | Checker publishes the contract | — | not sent | **blocked** (no draft) |
| B5 | 3-night HB quote, 2 adults + 7-year-old | — | not sent | **blocked**: no E2E identity may write a quote; not attempted |

Allotment (part 2) skipped as asked.

## Existing SYNTHETIC suppliers on Dev (read, owner, 22:09)

| Code | Status | Created by | Name |
|---|---|---|---|
| SUP-000002 | active | seed-s248-aa | SYNTHETIC S248 Supplier |
| SUP-000004 | active | system:aa835 | SYNTHETIC S251 AA-835 Evidence Supplier |
| SUP-000006 | active | — | SYNTHETIC S252 AA-682 Supplier |
| SUP-000008 | active | seed-s267-aa | SYNTHETIC S267 Lumen Ridge Travel Co |
| SUP-000009 | inactive | the pricing maker (S280) | SYNTHETIC S280 supply (AA-1091 live check, not real) |
| SUP-000012..14 | inactive | the custom-role maker (A10g, S288) | SYNTHETIC aa1158-… custom |

SUP-000009 is the maker's own synthetic supplier (A10e-3); it is inactive, so a rerun either creates a new one (pending,
the checker activates it: `SUPPLIER_ACTIVATE` is on the checker's allow-list) or needs it reactivated.

## LLM cost

None. No import ran, so no service was created and no CIS supply-content draft job was queued.

## Result per Done-when

| Item | Result |
|---|---|
| AA-1151: importing 5 activities creates 5 drafts | **blocked** (B1) |
| AA-1151: a second person publishes | **blocked** (B1) |
| AA-1151: place view returns only in-force days | **blocked** (route live, 200, empty: no offer on Dev) |
| AA-1151: 60-day alert shows in admin | **pass** (card on Add-ons at 1440 / 390, `window_days` 60 = policy value, 1 contract at 59 days) |
| AA-1153: one hotel with 2 DMC contracts | **blocked** (B1), and the hotel-to-DMC link is outside the maker allow-list |
| AA-1153: "70 USD, 20 %" imports as 56 net, both numbers kept | **blocked** (B1); template columns `Published` + `Commission %` present |
| AA-1153: 3-night HB quote matches the cost | **blocked** (no E2E quote write) |
