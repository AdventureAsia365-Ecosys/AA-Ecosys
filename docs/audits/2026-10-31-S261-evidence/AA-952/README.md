# AA-952 (CRM-23 slice 4, AA-Partner PR #143): invoice claim, one hold extension, Not received, void guard, live check (S261, 31/10/2026)

Run by the agent at 04:21–04:40Z on Dev, synthetic agency only.

**Result.** Every step that can run today passed: the pay box, "I have paid", the verify task, the bell, Booking's one
hold extension, "Not received", the void guard and the card guard. Two checks are **not run yet** because they need
time to pass on Dev: the expired pay link (with the late-money re-hold) and the overdue reminders. Both specs are ready
and both have a time set (see "Not tested"). Two findings came up: F1 is medium and F2 is minor.

## How it was run

- Deployed build: `GET /crm/health` gave `git_sha 132112aa` (AA-Partner main, which contains #143). `GET /crm/health/ready`
  gave `schema_version crm-031`, with `crm-028` among `registered_keys`.
- Headless Chromium (Playwright). Only one browser ran at a time, and it was closed after each spec. Hosts:
  - agency app: `https://portal.lumiguides.it.com`. Agency writes went through the same-origin BFF `/bff/…`.
  - client proposal page: `https://go-dev.lumiguides.it.com/c/p`. The proposal cookie was set from the link that
    `send` returned. Client API calls were same-origin `fetch` calls to `/crm/public/v1/proposal/…`.
- Agency identity: the e2e **owner** of the synthetic agency "Lữ hành Sen Vàng". Its stored session from the earlier
  S261 run was reused (partner pool, password + authenticator). No credential was printed or written.
- Client identities: two new synthetic prospects, "E2E S261 Payer vwatohA" and "E2E S261 Payer vwatohB", with
  `@example.invalid` addresses. No mail was sent by hand and no real mailbox was involved.
- The agency already had a manual pay-by method (Settings > Payments: "Bank transfer", e2e text). It was not changed.
- Client writes were spaced about 14 s apart (the limit is 5 per address per minute). No 429 came back.
- The specs are local only (root `.tmp-session/S261/aa952/`, not committed). [`run-log.txt`](run-log.txt) and
  [`run-data.json`](run-data.json) hold ids, statuses and codes. They hold no tokens, codes or contact data.

### Setup: two accepted day-by-day versions, each holding an AA item

Each trip went through the same steps as the S259 C-M3 proof:

1. Inquiry form gave **202**. The owner took the trip, set the dates, then moved it Qualifying → Proposal (override
   `info_by_phone`).
2. Builder version: an agency lodging option, plus the AA seed day tour (E2ECRMAATOUR) from a live Booking quote.
3. Publish, then send.
4. The client asked for a hold: `POST /proposal/hold` gave **200** and the Booking hold was `active`.
5. The client accepted: **200**.
6. From the deposit schedule row (540.00 USD): invoice draft **201**, then issue **200**.

| Trip | Invoice | Booking hold (48 h) | Use |
|---|---|---|---|
| A `87f9e5ee` | INV-000002 (deposit, due 31 Oct 2026) | until 2026-11-02T04:23:07Z | claim, extension, Not received, guards |
| B `6034f3a8` | INV-000003 (deposit, due 31 Oct 2026) | until **2026-11-02T04:25:05Z** | left issued and unclaimed, for the natural expiry check |

## Results per Done-when line

| # | Done-when | Result | Evidence |
|---|---|---|---|
| 1 | Client pay box on an accepted proposal with an issued deposit invoice (open window) | **PASS.** `GET /crm/public/v1/proposal` gave `payments[]` = INV-000002, `pay_window {state: open, until: 2026-11-02T04:23:07Z}` (= the hold), `can_claim: true`, `pay_by` present, balance 540.00. The page shows the deposit line, "540.00 USD to pay by 31 Oct 2026", "Pay by bank transfer before 2 Nov 2026, 11:23 am…", the agency's bank details and **I have paid**. | `01-client-pay-box-open-390.png`, `01b-…-detail-390.png`, `01c-…-1440.png`, `01d-…-dark-390.png` |
| 2a | "I have paid" → invoice `payment_claimed` | **PASS.** Clicked in the UI: `POST …/invoices/<id>/claim` gave **200** `outcome: claimed`. The agency `GET /invoices/<id>` shows `status payment_claimed`, `claimed_at` set, `actions [record_payment, reject_claim]`. The client box says "Thank you. Lữ hành Sen Vàng will check the transfer before 5 Nov 2026, 11:23 am…", with no bank details and no button (`pay_by: null`, `can_claim: false`). | `02-…-claimed-390.png`, `02b-…-detail-390.png`, `02c-…-1440.png`, `02d-…-dark-390.png` |
| 2b | Urgent `verify_transfer` task on the trip owner | **PASS.** One open task `verify_transfer`, priority `urgent`, assignee = the trip owner (the e2e owner), `due_at` = the new hold expiry 2026-11-05T04:23:07Z. | `run-data.json` `verify_tasks_after_claim`; `03e-trip-page-claimed-dark-1440.png` (Tasks card: "URGENT Check the client's bank transfer, due 5 Nov") |
| 2c | Bell on the trip owner | **PASS.** `GET /bell` gave `invoice.payment_claimed` for trip A, `detail {kind: deposit, number: INV-000002}` (number and kind only, as designed). | `run-data.json` `bell_after_claim` |
| 2d | One hold extension (`hold_extended_at` set or Booking code shown) | **PASS (extended).** The claim answer had `extension {code: extended, until: 2026-11-05T04:23:07Z}`, so Booking added 72 h to the hold. The invoice shows `hold_extended_at` 04:23:35Z and `hold_extend_code extended`. The client page hold and `pay_window.until` moved to 5 Nov. The trip's AA line read `held`, until 5 Nov, a few minutes later (the feed refresh). **Only once:** a second claim while claimed gave **200**, `extension: null`. A claim after "Not received" gave **200**, `extension: null`, with `hold_extended_at` unchanged. | `run-data.json` `claim`, `agency_after_claim`, `second_claim`, `claim_after_reject`; run log 04:29Z "A AA lines now" |
| 3 | Agent "Not received" → back to `open` | **PASS.** Clicked on the trip Invoices card: `POST /bff/invoices/<id>/reject-claim` gave **200** with the message "Marked as not received. The invoice is open again." The invoice is `open` with `actions [record_payment, void]`, `pay_window open until 5 Nov`. The `verify_transfer` task is `skipped`. The row re-renders as open within 2 s; no reload is needed (rechecked). The client box shows the open state again, with the bank details and the button. | `05b-invoices-card-not-received-after-10s-1440.png`, `05c-…-after-reload-1440.png`, `06-client-pay-box-open-again-390.png` |
| 4 | A claimed invoice cannot be voided (409 `invoice_claimed`) | **PASS.** `POST /bff/invoices/<id>/void` while claimed gave **409 `invoice_claimed`**. | run log 04:23Z |
| 5 | Expired link page: no bank details; the card button returns 410 `pay_link_expired` with no session | **NOT TESTED (time-gated).** See "Not tested". Run today with an open window, the card guard does refuse without a provider: **409 `invoice_not_payable`** while claimed, and **409 `card_not_offered`** with an open window (the agency has no card account). | run log |
| 6 | Reminders: a past-due invoice → `invoice_overdue` bell and task from the hourly rule | **NOT TESTED (time-gated).** See "Not tested". | — |
| 7 | Screenshots: pay box states, Invoices card with the claim note, `/payments` note | **Done for open and claimed** (light 390 / 1440, dark 390). Invoices card with the claim note "The client says they paid. Check your account before 5 Nov 2026, 11:23 am, when the AA places are released." and the **Not received** button (light 1440 / 390). `/payments` with the receivables note (light 1440 / 390, dark 1440). **Expired state: not yet** (see 5). | `03-…`, `03b-trip-page-claimed-1440.png`, `03c-…-390.png`, `04-…`, `04b-…-390.png`, `04c-…-dark-1440.png` |
| 8 | Late money re-hold / refund request | **NOT TESTED (time-gated).** See "Not tested". | — |

Console: the only console errors were the three deliberate probes (void 409 and card 409 ×2), which the browser logs as
failed loads. No other console error. Mobile 390: no sideways scroll on any page shot (document 0 px, main 0 px).

### Extra check (AA-955 × AA-952)

A builder version saves `terms_doc_id: null`. In this agency, the published booking terms (`s261-aa955-vra8tb`) were
therefore "updated after you accepted", and `GET trips/{id}/agreements` gave `reaccept_required: true` with no
acceptance on both trips. A 1.00 payment on INV-000002 at that point gave **409 `terms_reaccept_required`**, and
nothing was recorded (the AA-955 gate holds on the invoice path too). Both clients then re-accepted on their page
(`POST /proposal/terms` **200**) and `reaccept_required` became `false`. This keeps the later checks simple. See F1.

## Findings

- **F1 (medium, UX and process gap).** While a terms re-accept is pending, the client page shows "Updated booking
  terms… please read and accept them **before you pay the deposit**". Directly below it, the pay box offers the bank
  details and **I have paid** (`07-client-reaccept-and-pay-box-together-390.png`). The claim is accepted: it opens
  the urgent verify task and uses up the one hold extension. But the agent's Record payment is refused (409
  `terms_reaccept_required`) until the client re-accepts. Suggested fix: hide or disable the pay box (or show "accept
  the updated terms first") while `terms_reaccept` is set, and/or refuse the claim with the same code. Related: the
  builder version saves `terms_doc_id` null, at least on the API path the C-M3 proof and this run use. I did not check
  whether the builder UI pins the terms.
- **F2 (minor, display).** The claim-note deadline is formatted in UTC with no zone label on `/payments` ("4:23 am",
  `04-…`). The trip Invoices card shows the browser's time ("11:23 am", `03-…`). For an agency in Asia/Ho_Chi_Minh,
  `/payments` shows the deadline 7 h earlier than the local time. The trip card's text also reads in UTC in the server
  HTML before hydration (seen in the run log). This is the same class of bug as #142 (agency timezone).
- **Observation (dark mode, not investigated).** On the trip page, the Invoices panel rendered with a white background
  in a dark-scheme browser (`03d-…`, `03e-…`). One run reported `<html data-theme="dark">` and a recheck reported
  `light`. `/payments` (`04c-…`) and the client page (`01d`, `02d`) render dark correctly. This is outside AA-952's
  code: it should go to the CRM web dark-mode pass.
- **Not ours:** the CRM web task was stopped by a Fargate Spot interruption at 04:27:58Z. `/bff` answered 503 for
  about 1 minute until the replacement task registered (ECS service events, read only).
- **Outside this issue's scope:** the Tasks card shows the raw kind `collect_deposit` (not a label) (`03e-…`).

## Not tested, and why

1. **Expired pay link + card 410 + late-money re-hold / refund request.** These need a deposit invoice whose AA
   hold has ended. Dev holds last 48 h. The only other way is to move `crm.proposal.hold_expires_at` by ECS exec,
   which this lane may not run. Trip B was set up so the hold runs out **naturally at 2026-11-02T04:25:05Z**: never
   claimed, never extended, client terms re-accepted, cookie kept. The spec `expired.spec.ts` (with `LATE=1`) checks
   these things:
   - the page shows the `expired` state with no bank details and no button (screenshots 390 / 1440 / dark);
   - the card button gives 410 `pay_link_expired`, and "I have paid" gives 410;
   - the agency sees the "re-quote before the client pays" note;
   - it then records the full late deposit and waits for the Booking sync: `paid` (held again) or
     `paid_unfulfillable` with a refund request and the urgent `payment_unfulfillable` task.
2. **Overdue reminders.** Issuing an invoice clamps `due_on` to today or later, so no invoice can be past due on the
   day it is issued. The agency had no older unpaid issued invoice (`GET /invoices` was empty before this run).
   INV-000002 (open again) and INV-000003 are due 31 Oct 2026. They become overdue at agency midnight (Asia/Ho_Chi_Minh,
   2026-10-31T17:00Z), and the next hourly `crm_stage_date_rule` should remind them. The spec `reminders.spec.ts`:
   - `MODE=check`: `invoice.overdue` bell items and one open `invoice_overdue` task on trips A and B (screenshots); then
     a full payment on A, after which A's `invoice_overdue` task is `done`;
   - `MODE=after` (one hourly run later): no new reminder for A.
   The job result count (`invoice_reminders >= 1`) and `done_by` are in the DB only (the task view has no `done_by`).
   Reading them needs a DB Migrate `run-script`, which this lane did not run.
3. **DB-side facts** (`crm.invoice.reminder_count`, `crm.task.done_by`, the `crm_stage_date_rule` job result) were not
   read: no ECS exec or DB Migrate in this lane.
4. **Vietnamese strings** of the pay box and notes: not opened (the agency UI ran in EN).
5. **Card session with a real provider:** none exists. By design, slice 4 always refuses with 409 or 410.

## Screenshots

| File | What |
|---|---|
| `01-client-pay-box-open-390.png`, `01b-…-detail-390.png`, `01c-…-1440.png`, `01d-…-dark-390.png` | client pay box, open (bank details, "I have paid") |
| `02-client-pay-box-claimed-390.png`, `02b-…-detail-390.png`, `02c-…-1440.png`, `02d-…-dark-390.png` | client pay box, claimed ("will check the transfer before 5 Nov…") |
| `03-invoices-card-claimed-1440.png`, `03c-…-390.png`, `03d-…-dark-1440.png` | trip Invoices card: "CLIENT SAYS PAID", claim note, **Not received** |
| `03b-trip-page-claimed-1440.png`, `03e-trip-page-claimed-dark-1440.png` | whole trip page while claimed (Tasks card with the urgent verify task; AA line held until 5 Nov) |
| `04-payments-receivables-claim-note-1440.png`, `04b-…-390.png`, `04c-…-dark-1440.png` | `/payments` receivables with the claim note |
| `05b-invoices-card-not-received-after-10s-1440.png`, `05c-…-after-reload-1440.png` | after "Not received": open again (`05` was taken before the row refreshed and was removed) |
| `06-client-pay-box-open-again-390.png` | client box open again after "Not received" (window until 5 Nov) |
| `07-client-reaccept-and-pay-box-together-390.png` | F1: terms re-accept box and pay box offered together |

## Data left on Dev

- Trip A: INV-000002 is open and unpaid, with the hold extended to 5 Nov.
- Trip B: INV-000003 is open and unpaid, with the hold until 2 Nov 04:25Z.
- Both are synthetic Sen Vang trips at Proposal with accepted builder versions. They are needed by the two follow-up
  specs.
- The client cookies and run state are in `.tmp-session/S261/aa952/.client-{A,B}.json` and `.state.json` (0600).
  Delete them after the follow-ups.
