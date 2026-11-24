# AA-1153 hotel contracts (part 1) and AA-1158 supplier bank accounts (part 2): live check on Dev (S289)

- When: 2026-11-24, 03:50–03:57 UTC (10:50–10:57 +07). Run by an agent, headless Playwright (Node, the Booking
  `frontend/node_modules`) against `https://booking.lumiguides.it.com` (BFF `/api/booking/*`).
- Deployed: Booking `/booking/health` `git_sha 094d678d…`. `/booking/health/ready` `schema_version bk-071`,
  `storage.supplier_bank_key configured`.
- Sign-in: Cognito managed login with an e-mail code, the same way as S288 (`2026-11-23-S288-session/live/e2e-owner/evidence.md`).
  - The code was read from the S3 prefix `inbound-admin/` with the MFA admin profile.
  - It was never printed, logged or screenshotted.
  - No screenshot was taken on the sign-in host.
  - The local browser state files were deleted at the end.
- Identities (root ADR 0006a):
  - pricing maker (A10e-2..A10e-5): `staff/me` 200, role `contracting`. This is the group granted again on 24/11.
  - pricing checker (A10e-2/3): role `contracting`.
  - E2E owner (A10h): role `admin`.
  - None of them is the business owner.
- Masking:
  - The synthetic bank account number was generated in memory, sent once, and never printed or logged. It is not in this file.
  - The runner scanned every bank-account response for it, and the local copy was deleted.
  - Only the last 4 digits appear here: `0875`.
  - E2E addresses are masked in the screenshots.
- No DB query, no ECS exec, no push, merge or workflow run.

## A) AA-1153 part 1: one hotel, two DMC contracts, HB quote

| # | Step | Time (UTC) | Request → status | Result |
|---|---|---|---|---|
| A1 | Maker creates two SYNTHETIC hotel DMCs | 03:51:49 | 2 × `POST /suppliers` → 201 | `SUP-000016` "SYNTHETIC S289 AA-1153 Lotus DMC A (live check, not real)" and `SUP-000017` "SYNTHETIC S289 AA-1153 Lantern DMC B (live check, not real)", both start **pending** |
| A2 | Checker activates both | 03:51:58 | 2 × `POST /suppliers/{code}/activate` → 200 | active (second person, AA-1158 R5) |
| A3 | Maker creates the hotel under DMC A, plus a room type | 03:52:01 | `POST /hotels` → 201, `POST /hotels/HTL-000007/room-types` → 201 | `HTL-000007` "SYNTHETIC S289 AA-1153 Saigon Courtyard (live check, not real)", Ho Chi Minh City, 4 stars; room type `9f6d82d7-…` "SYNTHETIC Deluxe Double", `max_occupancy 3` |
| A4 | Maker links the hotel to DMC B (A10e-5) | 03:52:03 | `POST /hotels/HTL-000007/suppliers` `{supplier_id, supplier_hotel_code: "S289-LANTERN-01"}` → 201 | 2 links, both active, neither preferred. DMC A is `first_listed`; DMC B has its own code `S289-LANTERN-01` |
| A5 | Maker DRY RUN of both rate sheets | 03:52:16 | `POST /suppliers/{code}/rate-sheets?dry_run=true` → 200 × 2 | `checks: []` (no warnings), diff = 1 added rate each. **DMC B's row matched by the DMC's own hotel code**: `published_amount "70"`, `commission_pct "20"` → `net_amount "56.00"` |
| A6 | Maker imports both | 03:52:26–28 | `POST /suppliers/{code}/rate-sheets` → 200 × 2 | draft contracts A `78c8f2dc-…` and B `3ed06d8f-…`. Import rows `56952ebc-…` and `9d35181f-…` (file hash and name kept) |
| A7 | Checker publishes both | 03:52:31 | `PATCH /contracts/{id}` `{status: published}` → 200 × 2 | `published`, `phase in_force`, `created_by` = maker, `published_by` = checker. No acknowledgement needed (`acknowledge false`, no warnings) |
| A8 | Rates read back (owner) | 03:52:48 | `GET /contracts/{id}/rates` → 200 | A: rate `cfd59420-…` HB, 2 pax, **net 60.00**, no source numbers. B: rate `78cedba4-…` HB, 2 pax, **net 56.00, `published_amount 70.00`, `commission_pct 20.00`** (both source numbers kept). Child prices (review): A `10df208e-…` age 2–11 sharing HB 12.00; B `73db045d-…` age 2–11 sharing HB 10.00 |
| A9 | Desk entry with a non-synthetic agency (probe) | 03:52:56 | `POST /b2b-desk/entries` (partner "Synthetic Agency 972 (S248 live verify)") → **403 `e2e_synthetic_only`** | This agency is not marked synthetic in CIS, so the guard refused it. Nothing was written |
| A10 | Maker enters the desk booking (A10e-5) on the synthetic agency "E2E Pilot Rehearsal Travel" | 03:53:07 | `POST /b2b-desk/entries` (Idempotency-Key) → **201** | Line `rt:9f6d82d7-…`, 2027-01-12, **3 nights, HB, 2 adults + 1 child (age 7)**, rooms 1 × double. Agency ref `SYNTHETIC-S289-1153-HB-01`. Desk entry `52b1593c-…` **booked**, quote `f6a7d033-…`, hold `2422d22d-…`, trip case **TC-000039** (confirmed). Agency total 257.15 USD, floor 232.95 |

### Quote vs contract rates (TC-000039 version 1, item `6fd90065-…`, cost row `42035b9d-…`)

| Part | Contract rate used | Per night | Nights | Amount |
|---|---|---|---|---|
| Room, double occupancy (2 adults), HB | DMC B rate `78cedba4-…` (70 USD published less 20 % = 56.00) | 56.00 | 3 | 168.00 |
| Child age 7, sharing (room `max_occupancy 3`, 1 free place), HB | DMC B child price `73db045d-…` (age 2–11) | 10.00 | 3 | 30.00 |
| **Net cost, expected** | | 66.00 | 3 | **198.00 USD** |
| **Net cost, stored on the booking** | `net_amount "198.00" USD`, `supplier_rate_id 78cedba4-…`, note "B2B quote f6a7d033-… line 1 (3 supplier rates, USD at the plain rate)" | | | **198.00 USD: match** |

The same stay at DMC A would cost 3 × (60 + 12) = 216.00. Both DMCs sell HB and neither is preferred, so the rate choice
took the lower net in USD (DMC B), and one DMC priced every night (the AA-1153 "one DMC per room" rule). The agency sell
total of 257.15 USD comes from the pricing rule on top of the net. It is not part of this Done-when.

### Who the booking goes to

- **The desk flow stops at a confirmed trip case with 1 item still to book.**
  - `GET /trip-cases/TC-000039/supplier-bookings`: `items_to_book 1`, `items_booked 0`, line `on_request`.
  - No supplier booking was generated. `POST …/supplier-bookings/generate` is on no E2E allow-list, and it was not part of this brief.
- What decides the DMC is recorded: the version item's cost row names **DMC B's rate** (`supplier_rate_id 78cedba4-…`, contract `3ed06d8f-…`, supplier `SUP-000017`).
  - Per `docs/implementation-notes/AA-1153.md`, a version item's supplier is the contract supplier of its first cost row's rate.
  - So a generated supplier booking would go to DMC B. This was **not observed live**.
- **Finding (known follow-up):** the B2B desk on-request list (`GET /b2b-desk/on-request`) labels this line with the hotel's first DMC, **DMC A** (`component.supplier` = `SUP-000016` Lotus DMC A).
  - The DMC whose rate priced the line was DMC B.
  - This matches the follow-up already listed in AA-1153.md ("the B2B desk labels still name `hotels.supplier_id`").
  - Staff reading the desk queue would chase the wrong DMC until that follow-up ships.
- **Finding (UI):** the supplier Rates tab and the hotel drawer show net 56 USD but not the two source numbers (Published, Commission %). The API returns both, and the Columns menu has no column for them.

Screenshots:
- `a1-hotel-two-dmcs__1440__light.png`: hotel drawer with 2 rates in force (60 and 56 USD per room night, HB, 2 pax) and the activity "Linked SUP-000017 … (code S289-LANTERN-01)".
- `a2-dmc-b-rates-net56__1440__light.png`: DMC B › Rates.
- `a3-desk-booking-tc39-net__1440__light.png`: TC-000039 proposal V1, net costs 198.00 USD.

**LLM cost:** creating the hotel queued one CIS supply-content draft. The hotel drawer shows "Customer content: In review,
Version 1". It was not measured here: the CIS session was not opened. The S289 AA-1151 run measured ≤ 0.003 USD per draft.

## B) AA-1158 part 2: supplier bank account on SYNTHETIC supplier `SUP-000017`

| # | Step | Time (UTC) | Request → status | Result |
|---|---|---|---|---|
| B1a | Pricing maker enters a bank account | 03:54:54 | `POST /suppliers/SUP-000017/bank-accounts` → **403 `e2e_read_only`** | The maker's role holds `supplier_bank.write`, but the route is on no A10e allow-list, so the E2E guard refuses it before the route runs. No A10e identity can enter one |
| B1b | E2E owner (A10h) enters it instead | 03:54:56 | same → **201** | Account `cc582a68-c35d-430a-9570-1eac08ac2f3b`, **status `pending`**, bank "SYNTHETIC S289 Test Bank (not real)", USD, VN, `account_masked "•••• 0875"`, `approve_blocked null`. The owner's own actions: `approve false`, `withdraw true`. A10h D6 allows the E2E owner to be the maker on synthetic suppliers. It holds `supplier_bank.write` (admin) |
| B2a | Approval attempt by the E2E owner | 03:55:04 | `POST /supplier-bank-accounts/cc582a68-…/decision` `{action: approve, note}` → **403 `bank_approver_not_allowed`** | "only the business owner approves a supplier bank account change (the tech lead when she cannot)". The S289 approver rule refused it **before** the maker-checker check (the owner also entered the account) |
| B2b | Approval attempt by the pricing checker | 03:55:05 | same → **403 `e2e_read_only`** | Refused by the E2E guard (the decision route is not on the checker's allow-list) before the service. The checker's role has no `supplier_bank.approve` either |
| B2c | Approval attempt by the pricing maker | 03:55:07 | same → **403 `e2e_read_only`** | as B2b |
| B3 | Payout while pending | — | **not run** | Dev has **no supplier bill** (`GET /supplier-bills?status=all` → `total 0`, also for SUP-000017). A payout needs an approved bill entered by one person and approved by another. `bill.approve` is on no E2E allow-list, and the E2E owner cannot approve its own bill. The lock state was read instead: `payout_lock {"state":"pending"}` for every caller, and the Bank accounts tab says "Payouts to this supplier are paused until the bank account change is decided." |
| B4 | Masked list for roles without `supplier_bank.read` | 03:55:10–12 | `GET /suppliers/SUP-000017/bank-accounts` as checker and as maker (`contracting`) → 200 | `can_read_details false`, `account_masked "•••• 0875"`, `account_last4 "0875"`, `actions.reveal false`, no other account field. The full number (and its first characters) is **absent from both bodies** (scanned) |
| B4b | Reveal by a role without read | 03:55:10–12 | `POST /supplier-bank-accounts/cc582a68-…/reveal` as checker and as maker → **403 `e2e_read_only`** | No details returned |
| B4c | Owner (has `supplier_bank.read`) list | 03:55:14 | `GET …/bank-accounts` → 200 | Still masked (`can_read_details true`, `actions.reveal true`). Reveal was **not** called |
| B5 | Ciphertext at rest | — | **not run here** | No DB query was made, by design. The API never returned the full number to a role without read (B4, B4b). The at-rest check (`ciphertext`, `wrapped_key`, `kms_key_id` on row `cc582a68-…`, no clear number) belongs to the orchestrator |

Screenshots:
- `b-bank-tab-checker__1440__light.png` and `b-bank-tab-checker__390__light.png`: as the pricing checker, "•••• 0875", "Waiting for approval", the payout-paused notice, no buttons.
- `b-bank-tab-owner__1440__light.png`: as the E2E owner, the same row with only Withdraw and Show details, and **no Approve**.

**Left pending on purpose:** account `cc582a68-…` waits for the business owner's approval (or a rejection or withdrawal).
Until then SUP-000017 payouts stay locked. It has no bills.

## Synthetic records created (all kept)

| Kind | Id |
|---|---|
| Suppliers | `SUP-000016` (`69d93956-…`), `SUP-000017` (`ab498f31-…`), active |
| Hotel / room type | `HTL-000007` (`892e362d-…`) / `9f6d82d7-6d12-45e4-b6f0-e37ad4e1a8f4` |
| Link | HTL-000007 ↔ SUP-000017, code `S289-LANTERN-01` |
| Contracts (published) | A `78c8f2dc-8ce3-4644-852d-c894a6e15195`, B `3ed06d8f-c08f-4627-bf99-0c5848a65d28` |
| Desk booking | entry `52b1593c-9010-4289-b4ff-58e4da80fd3b`, quote `f6a7d033-…`, hold `2422d22d-…`, trip case `TC-000039` (confirmed, agency "E2E Pilot Rehearsal Travel"; its CRM gets `booking.created_by_aa`) |
| Bank account | `cc582a68-c35d-430a-9570-1eac08ac2f3b` (pending, •••• 0875) |

ADR 0006a A10e-5 says the agent cancels the synthetic desk booking at cleanup, as an administrator through the desk.
This lane did not cancel it: the orchestrator decides.

## Result per Done-when

| Item | Result |
|---|---|
| AA-1153: one SYNTHETIC hotel with 2 SYNTHETIC DMC contracts | **pass** (HTL-000007, SUP-000016 + SUP-000017, both published by the checker) |
| AA-1153: "published 70, commission 20 %" imports as 56.00 with both numbers kept | **pass** (API rate `78cedba4-…`; the UI shows the net only) |
| AA-1153: 3-night HB quote, 2 adults + 7-year-old, matches the cost | **pass** (198.00 = 3 × (56 + 10), stored on TC-000039) |
| AA-1153: booking goes to the DMC whose rate priced it | **partly**: the cost row names DMC B's rate. No supplier booking was generated (not observed). The desk on-request label shows DMC A (known follow-up) |
| AA-1158 (1) entered account stays pending | **pass**, entered by the E2E owner (A10h). The pricing maker is refused 403 `e2e_read_only` |
| AA-1158 (2) approval by the E2E owner / pricing checker refused | **pass**: owner 403 `bank_approver_not_allowed`; checker 403 `e2e_read_only` (E2E guard, before the service) |
| AA-1158 (3) payout refused while pending | **not run**: no supplier bill on Dev, and no E2E pair can make an approved one. `payout_lock.state pending` shown |
| AA-1158 (4) list masked for a role without read | **pass** (checker and maker) |
| AA-1158 (5) no full number to a role without read | **pass** (API). The at-rest check is left to the orchestrator |
