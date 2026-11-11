# CRM live verification on Dev: sales partners (AA-1071) and Book now with online payment (AA-1072)

Date: 11/11/2026 (S277). Live CRM API and web on Dev, `main` at the AA-1072 merge or later (API health reported the
crm-058 readiness commit). Every step ran on the **synthetic E2E agency** only. Names are invented and contain
"E2E"; e-mail addresses use `.invalid`. The payment gateway ran in **stub mode**, with an invented merchant code and a
random hash secret that was never stored. No real gateway was called and no real money moved.

How it ran: a local Playwright script signed in as the synthetic agency's e2e owner (partner pool, password and
authenticator code read into memory, never printed). It called the CRM web's BFF from the signed-in page and opened
the public client host in separate browser contexts. No sign-in code, token or secret appears in this folder.

## AA-1071: sales partners and commission

| Check | Result | Evidence |
|---|---|---|
| `GET /bff/sales-partners` | PASS | 200 `{items: [], base_currency: "USD", terms_visible: true}` before the run |
| Create a `sub_agent` partner | PASS | 201, `commission_type: percent`, `rate: 10.00`, `basis: revenue`, `payout_due_days: 30` |
| Issue a partner view link | PASS | 201 `{link_id, purpose: "view", path: "/c/a/<token>", expires_at}` (shown once) |
| Attach the partner to a booked synthetic trip | PASS | `PUT /bff/trips/{id}/sales-partner` 200 |
| `GET /bff/partner-commissions?status=all` | PASS | one item, `status: accrued`, `basis_amount: 300.00`, `amount: 30.00 USD`, `amount_base: 30.00`, `trip_ref: T-…`, due 30 days after the trip; totals `accrued: 30.00` |
| Trip P&L | PASS | `GET /bff/trips/{id}/pnl` 200, `costs.partner_commission_base: "30.00"` |
| `/c/a/<token>` on the client host | PASS | 303 to `/c/a`; cookie `aa_partner_link`: host-only, Path `/crm/public/v1/partner`, HttpOnly, Secure, SameSite=Strict |
| `GET /crm/public/v1/partner` | PASS | 200 `{agency, signed_in: false, link_expires_at}` |
| `/partners` and the trip partner picker | PASS | screenshots below; no sideways scroll at 390 px; no console errors |

The booked trip came from a Book now booking (USD, 2 adults and 1 child) whose deposit was recorded by the agency
(bank transfer, synthetic). The record moved the trip from Proposal to Booked.

## AA-1072: Book now and online payment (stub)

| Check | Result | Evidence |
|---|---|---|
| Book now off by default | PASS | `GET /bff/settings/online-booking` → `enabled: false` before the run |
| Connect the stub gateway | PASS | `PUT /bff/settings/payment-methods/vn-gateway` 200, account `vn_gateway` active, currency VND, `mode: stub` |
| `GET /crm/public/v1/book/<form key>?tour=…` | PASS | 200 with `agency_name, tour, title, duration_days, currency, child_age_max, infant_age_max, honeypot_field, consent_text, privacy_notice_url, departures[{departure_id, start_date, seats_left}]` |
| `POST …/price` `{adults: 2, child_ages: [7]}` | PASS | 200 `{currency: "USD", total: "300.00", lines: [adult ×2 100.00, child ×1 100.00], availability: "available", start_date}`. With the agency in VND: `total: "8250000.00"`, VND |
| IPN with a dummy reference and a zero hash | PASS | 200 `{RspCode: "01", Message: "Order not found"}` (a notice without amount / response code answers `99`) |
| Book now in a browser | PASS | widget → price → booking 201 → client page `/c/p`, the token removed from the address |
| Deposit invoice at accept (web booking) | PASS | hold → active, accept → a deposit invoice issued right away (30 % of the total) |
| "Pay online" in the pay box | PASS (VND invoice) | shown next to the bank details and "I have paid" |
| Stub page → Pay (simulated) | PASS | card route 200 → stub page "Amount: 1,650,000 VND" → back on `/c/p`, "Paid. Thank you." |
| Payment recorded, trip booked | PASS | invoice `paid`, payment `method: online`, `provider: vn_gateway`; trip stage `booked`, lead source `web_booking` |
| Settings > Payments panels | PASS | screenshots below (the form key is masked) |

VNPay settles VND only, so "Pay online" appears only on a VND invoice. The synthetic agency uses USD, so its base
currency was set to VND for the length of that one booking, then set back to USD. At the end of the run the agency
was as before: base currency USD, Book now off, gateway account disconnected.

The CIS trip page answer carries no catalogue key yet (a follow-up listed in the AA-1072 notes). The widget link
therefore used `p=<AA tour key>` on another served trip page. The widget shows the AA seed tour, while the page text
belongs to a different tour.

## Findings

1. **Gateway still "Connected" after disconnect (bug, low).** After Settings > Payments disconnects the VNPay
   account (200, account `disconnected`), `GET /settings/payment-methods/vn-gateway` still answers
   `connected: true, mode: "stub"`, and the Online payment panel still shows "Connected". `gateway.status()` reads the
   `integration_credential` row, which disconnect does not remove, instead of the active account. Each new connect
   also adds another account row. Screenshot: `finding-gateway-after-disconnect-1440-light.png`. Not checked: whether
   the client pay box offers "Pay online" while in this state (it should not, because `pay_online` needs an active
   account).
2. **Book now can stop at the owner's discount gate (bug, medium).** A booking for 1 adult (VND) answered 409
   `discount_needs_approval`, `reason: below_cost`. The retail suggestion (AA price per person) was below the B2B net
   for a single traveller, so the builder's discount gate ran on the public path. The implementation notes say this
   gate never applies there. The visitor sees only "Something went wrong. Try again in a minute." Each try also uses
   one of the 5 attempts an hour. 2 adults passed.
3. **The per-address write limit is shared across the whole client journey (risk, low).** See price, Book now, hold,
   accept and Pay online each use the anonymous limit of 5 writes a minute per address. A visitor who checks the price
   twice and then pays within one minute gets 429 on "Pay online". The run hit this once.
4. **Two payment schedules on the client page (observation).** On a departure 9 days out, the summary showed
   "Balance … due 21 Oct 2026", a date in the past. The schedule list below it showed every instalment due today.

## Synthetic records created

| Record | Id (first 8) | State at the end |
|---|---|---|
| Trip 1, Book now, USD, 2 adults + 1 child, departure 20 Nov | 9f0976dc | booked (deposit recorded by the agency), partner attached |
| Sales partner "E2E … Lotus Referral Desk" (sub_agent, 10 % of revenue) | bfab5378 | active |
| Partner view link | 36a2274f | active, expires in 30 days |
| Partner commission (trip 1) | 2bca4171 | accrued, 30.00 USD |
| Trip 2, Book now, VND, 2 adults, departure 4 Dec | 1a214876 | lost (unpaid; its link cannot be re-issued after accept) |
| Trip 3, Book now, VND, 2 adults, departure 4 Dec | 8eab17e9 | booked through the stub payment |
| Stub gateway accounts | e4addf2d + 2 more | disconnected |

Seats used on the AA seed supply: 3 on the 20 Nov departure (trip 1) and 2 on the 4 Dec departure (trip 3). Trip 2 was
marked Lost, which releases its hold by design; the release on Booking was not checked again.

## Screenshots

- AA-1071: `aa1071-partners-{1440,390}-{light,dark}.png`, `aa1071-trip-partner-{1440,390}-{light,dark}.png`,
  `aa1071-trip-partner-picker-open-{1440,390}-{light,dark}.png`, `aa1071-partner-page-signin-{1440,390}-light.png`
- AA-1072: `aa1072-tour-widget-{1440,390}-{light,dark}.png` (the public trip page has no dark theme, so the light and
  dark images are the same), `aa1072-tour-widget-price-{1440,390}-light.png`,
  `aa1072-client-paybox-{1440,390}-{light,dark}.png`, `aa1072-client-page-{1440,390}-{light,dark}.png`,
  `aa1072-stub-gateway-{1440,390}.png`, `aa1072-client-paid-{1440,390}-light.png`,
  `aa1072-settings-payments-{1440,390}-{light,dark}.png`
- Finding 1: `finding-gateway-after-disconnect-1440-light.png`

## After the fix (PR #282, API and web at 066560e7)

The re-check ran under the same rules as the first run: the synthetic agency only, the stub gateway only, and no
token or secret printed. At the end the agency was as before: base USD, Book now off, gateway disconnected, no retail
markup. Screenshots are in `after-fix/`.

| Check | Result | Evidence |
|---|---|---|
| 1. Disconnect → not connected | PASS | `GET /bff/settings/payment-methods/vn-gateway` → `{connected: false, mode: null}`; the panel shows "Not connected" (`1-gateway-panel-disconnected-{1440,390}-light.png`) |
| 1. Reconnect reuses the account | PASS | the same account id is active again on two reconnects; still 3 `vn_gateway` rows (the old ones from the first run), none added |
| 1. No "Pay online" while disconnected | PASS | accepted VND trip, open deposit: the pay box has bank transfer + "I have paid" only (`client-pay-online` count 0); `1b-paybox-gateway-disconnected-{1440,390}-light.png` |
| 2. 1 adult, VND, no markup | PASS | `POST …/price` → 409 `price_on_request`; `POST …/bookings` → 409 `price_on_request` (not counted as an attempt); the widget says "The agency prices this trip for your party on request. Send them a question and they will quote you." (`2a-widget-price-on-request-*`) |
| 2. 1 adult, VND, trip_plan markup 20 % | PASS | price 3,842,400 VND → booking 201 → hold active → accept → Pay online → stub "Amount: 1,152,720 VND" → Pay → "Paid. Thank you."; invoice `paid`, payment `online` / `vn_gateway`; trip `booked`, party 1 (`2b-paybox-pay-online-*`, `2b-paybox-paid-*`) |
| 3. No 429 on Pay online | PASS | one address, 6.0 s and 10.3 s runs: price 200, price 200, bookings 201, hold 200, accept 200, card 200 |
| 4. Balance date (departure 9 and 16 days out) | PASS | summary "Balance 2,689,680 VND, due 11 Nov 2026" = schedule rows "Deposit / Instalment 1 / Balance … due 11 Nov 2026" (today); `4-client-summary-{1440,390}-light.png` |

Note: one extra "Pay online" press, made by the test right after the first, was refused with 429. That was the sixth
write from the address in the same minute, counting a 2a booking call. Retrying after the window is expected
behaviour, not a fault. That trip could not be paid afterwards (an accepted proposal's link cannot be re-issued), so it
was marked Lost and a fresh booking was paid instead.

New synthetic records: trip `99e71c90` (1 adult, VND, 20 Nov; marked Lost), trip `8b32a904` (1 adult, VND, 27 Nov;
booked and paid through the stub). The gateway account in use was `ebec9f04`, now disconnected.
