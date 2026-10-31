# AA-955 (CRM-25 Module 12 contracts and waivers): expired code, terms re-accept, waiver + insurance declination, live check (S261, 31/10/2026)

Lane 2 item 2 of the S260 In Progress triage (`docs/audits/2026-10-30-S260-inprogress-triage/README.md` §4, §6).
Run by the agent at 02:02–02:15Z, Dev only, synthetic agency only. Result: **PASS** on all three checks.

## How it was run

- Headless Chromium (Playwright, `@playwright/test`), one browser with two contexts (agency, client), closed at the
  end. Egress checked first: VN, not the VPN.
- Deployed CRM API: `/crm/health` `git_sha 3718242a` (AA-Partner #140, which contains the e-sign code of #136).
- Hosts: the agency app on `https://portal.lumiguides.it.com` (the old `partner-dev.` answers 301 to it, AA-979); the
  client pages (proposal page, traveller portal) on the client host `https://go-dev.lumiguides.it.com`.
- Agency identity: the e2e **owner** of the synthetic agency "Lữ hành Sen Vàng" (partner pool, password and
  authenticator). Its credentials were read at run time from the e2e user's secret (read only). They were never written
  down or printed. No screenshot was taken on the managed-login host.
- Client identity: a fresh synthetic prospect "E2E S261 Signer vra8tb", sent through the agency's public inquiry form
  with an `@example.invalid` address. No real mailbox is involved. The portal codes come from the Dev
  `PORTAL_OTP_DEV_ECHO` answer, which shows them in the page. Every code hint and code field is **masked** (magenta) in
  the screenshots. No code is written in the logs.
- Agency writes go through the CRM BFF from the signed-in page (`fetch('/bff/…')`, same origin). "Mark paid" was
  clicked in the trip page UI. All client steps were clicked in the client pages.
- The client host allows 5 writes per address per minute. The run spaced its client writes about 14 s apart and hit
  no 429.
- The spec is local only (not committed). It sits in the root `.tmp-session/S261/aa955/`. The run log
  ([`run-log.txt`](run-log.txt)) and the data file ([`run-data.json`](run-data.json)) hold ids cut to 8 characters,
  HTTP statuses, version labels and hashes. They hold no codes, tokens or contact data.

### Setup (one trip made for this run)

| Step | Result |
|---|---|
| Documents in force before the run | booking terms `e2e-mvp3tg5i`, waiver `e2e-mvp3tg5i`, **no insurance declination** |
| Inquiry form on the client host (Vietnam, 5 nights, 1 adult) | `POST /crm/public/v1/forms/<key>/submissions` **202**. Trip `13efea13` "Việt Nam, 5 đêm" appears at Inquiry |
| Dates, then Qualifying → Proposal (override `info_by_phone`) | **200**, **200**, **200** |
| Text proposal pinned to terms `e2e-mvp3tg5i` (1,000 USD, deposit 200, balance due 10 Nov), sent | draft **201**, send **200** (the link is returned once) |
| Client opens the link, ticks the terms, types the name, accepts | `POST /crm/public/v1/proposal/accept` **200**. Schedule: deposit **due**, balance due. `deposit_paid: false` |

## Check (2): terms published after acceptance → re-accept before payment

| # | Step | Result | Evidence |
|---|---|---|---|
| 2.1 | Agency drafts and publishes booking terms `s261-aa955-vra8tb` (this retires `e2e-mvp3tg5i`) | draft **201**, publish **200**. `GET trips/{id}/agreements`: `terms.published = s261-aa955-vra8tb`, **`reaccept_required: true`** | `01c-…` ("The client must accept your newer booking terms before the deposit.") |
| 2.2 | Trip page › Proposal › deposit row › **Mark paid** › Record payment | `POST /bff/schedule/<id>/mark-paid` **409 `terms_reaccept_required`**, `version_label: s261-aa955-vra8tb`. The UI shows "The client has not accepted your newer booking terms yet…". The deposit stays **due** | `01-…` (full page), `01b-…` (Proposal panel) |
| 2.3 | Client reopens the proposal page (cookie link) | Section "Updated booking terms (s261-aa955-vra8tb)" with the new text, a tick box and a name field | `02-client-terms-updated-390.png` |
| 2.4 | Client ticks, types the name, clicks "Accept the updated terms" | `POST /crm/public/v1/proposal/terms` **200**. The section goes away | `02b-client-terms-reaccepted-390.png` |
| 2.5 | Agency: Mark paid again | **200** `status: paid`. `trip_moved: proposal → booked`, 1 traveller invited to the portal. Agreements: `reaccept_required: false`. Acceptances: `reaccept` s261-aa955-vra8tb, `proposal` e2e-mvp3tg5i | `03-…` (the success message; see note F1), `08-…` (top half: stage **Booked**, deposit **Paid**, Activity "deposit_paid → Booked") |

## Check (3), part 1: an insurance declination is published

| # | Step | Result |
|---|---|---|
| 3.1 | Agency drafts and publishes `insurance_declination` `s261-aa955-vra8tb` | draft **201**, publish **200** |

## Check (1): a signing code past its TTL is refused and logged

TTL read from the code: `api/app/portal/public.py` `CODE_MINUTES = 10` (10 minutes, under the 15-minute limit), so
the run waited it out live. No DB or clock step was needed.

| # | Step | Result | Evidence |
|---|---|---|---|
| 1.1 | Client opens the portal link (from the Mark paid answer), "Send code", types the echoed code | `…/code` 202, `…/session` 200, portal home | — |
| 1.2 | Your signature: "No, I decline travel insurance" (the declination text shows), "Send me a signing code" at **02:03:40.697Z**, tick, name, code filled | `…/code` (purpose `sign`) **202** | `04-portal-sign-form-declined-390.png`, `04b-…-1440.png` |
| 1.3 | Wait **645 s** (TTL 600 s + margin), then click **Sign** with that code | `POST /crm/public/v1/portal/<token>/sign` **422 `code_expired`**, `attempts_left: 0`. UI: "That code has expired. Ask for a new one." | `05-portal-code-expired-1440.png`, `05b-…-390.png` |
| 1.4 | Agency `GET trips/{id}/agreements` right after | signing log: **`code_refused` with reason `code_expired`**, after `code_sent` | `07b-…` / `07c-…` ("signing code refused (code_expired)") |

## Check (3), part 2: one envelope with the waiver and the insurance declination

| # | Step | Result | Evidence |
|---|---|---|---|
| 3.2 | Fresh signing code, insurance declined, Sign | `…/code` **202**, `…/sign` **200** `status: signed`, `signer_role: self`, `seal_alg: kms-rsassa-pss-sha256`, `envelope_sha256 f3d45779…e180` | `06-portal-signed-declined-1440.png`, `06b-…-390.png` |
| 3.3 | Agency `GET trips/{id}/agreements` | `all_signed: true`. Lead: `waiver_signed: true`, **`insurance_choice: declined`**, **`with_terms: true`**, **`with_declination: true`**, KMS seal. Acceptances: `envelope` s261-aa955-vra8tb, `reaccept` s261-aa955-vra8tb, `proposal` e2e-mvp3tg5i. Log: `code_sent`, `code_refused (code_expired)`, `code_sent`, `signed` | `run-data.json` |
| 3.4 | Trip page › **Signed documents** panel | "Every traveller has signed."; lead "Signed 31 Oct 2026 · **declined travel insurance** · sealed"; Booking terms "In use: s261-aa955-vra8tb" with the 3 acceptances; signing log with the expired-code refusal | `07-…-1440.png` (full page), `07b-…-element-1440.png`, `07c-…-element-390.png`, `07d-…-390.png` |
| 3.5 | "View sealed document" with reason "client request" | `POST /bff/signatures/<id>/envelope` **200**, `seal.alg kms-rsassa-pss-sha256`, **`seal.verified: true`**. Envelope text `aa-partner-envelope/1`, "Documents: 3": booking terms s261-aa955-vra8tb, waiver e2e-mvp3tg5i, travel insurance declination s261-aa955-vra8tb, each with its SHA-256. Modal "Seal checked: valid." | `08-sealed-envelope-1440.png` |

### Layout, console, network

- 390 px: no sideways scroll on any page shot (document 0 px, `main` 0 px), including the agreements panel at 390.
- Console errors: 2. Both are the deliberate refusals: the 409 of step 2.2 and the 422 of step 1.3.
- CRM responses ≥ 400: only those two. No 5xx.

### Findings

- **F1 (evidence only, not a defect):** `03-mark-paid-ok-booked-1440.png` was taken right after the success message.
  The page had not refreshed yet, so the panel still shows the deposit as DUE and the stage as Proposal. The API answer
  (200 `paid`, `proposal → booked`) and the later full-page shot `08-…` (stage Booked, deposit Paid) show the final
  state.

## Done-when lines

| Line (Linear AA-955) | Status |
|---|---|
| **R:** an expired code is refused and logged | **PASS**, live: 422 `code_expired`, `code_refused (code_expired)` in the signing log and the panel (Check 1) |
| **E:** terms updated after viewing → re-accept before payment | **PASS**, live: 409 `terms_reaccept_required` → client re-accepts → 200, trip Booked (Check 2) |
| Waiver + decline in one envelope | **PASS**, live: one sealed envelope with terms + waiver + insurance declination, `insurance_choice: declined`, seal verified (Check 3) |
| Versioned docs; acceptance pinned to version + `price_hash` | Versions: **PASS**, live. Three acceptances, each pinned to its own version. `price_hash`: the code writes it on the proposal and re-accept rows (`esign/terms.py` `record`), and the S260 data shows the field. Its value was not inspected in this run |
| Per-adult signing, guardian for minors; gate | Evidenced live in S260 (Linear comment 30/10; root `docs/audits/2026-10-30-S260-evidence/` §5). Not re-run here |
| e-sign v1 **with PAdES via `seal`** | **Not delivered.** v1 is a KMS RSASSA-PSS seal over a canonical text envelope, not a PAdES-signed PDF. Per the triage §6 this moves to the new follow-up "[CRM] CRM-25b PAdES-B-B signed PDF" |

## Not tested, and why

- **PAdES (signed PDF).** Not built in v1. It goes to the CRM-25b follow-up (triage §6).
- **"Yes, I have travel insurance".** Only the decline path was signed. The insured path has no declination document,
  and nothing here checked that it is left out of the envelope.
- **Minor / guardian signing and the `guardian_signs` refusal.** Not repeated. S260 showed them live.
- **Real e-mail delivery of the codes.** The run used the Dev echo (`delivery = dev_echo`). Mailbox delivery of signing
  codes was not exercised.
- **The re-accept rule on the invoice payment path** (`record_payment` on an issued invoice calls the same
  `require_terms_current`). Only "Mark paid" was exercised.
- **Vietnamese UI and dark mode.** Not part of this item.

## State left on Dev (synthetic only)

- Sen Vàng now has booking terms **`s261-aa955-vra8tb`** published (`e2e-mvp3tg5i` retired) and its **first insurance
  declination** `s261-aa955-vra8tb` published. Any trip with an accepted proposal and an unpaid deposit now needs a
  terms re-accept before Mark paid. The portal signing form now asks the insurance question. The Dev E2E suite
  publishes a fresh terms version on each run anyway.
- Trip `13efea13` "Việt Nam, 5 đêm" (lead "E2E S261 Signer vra8tb", `@example.invalid`): Booked, deposit paid, balance
  due, one signed envelope. It was kept as evidence and not trashed.

## Screenshots

These are full-page captures unless the name says "element". The agency shell scrolls inside the page, so its sidebar
and top bar show at the place the page was scrolled to. That is how the capture works, not a layout bug: the overflow
checks are 0. Magenta boxes are masked code hints, code fields and the one-time portal link.

| File | What it shows |
|---|---|
| `01-mark-paid-refused-terms-reaccept-1440.png` | Trip page after Mark paid: 409 message, deposit still due |
| `01b-proposal-panel-409-1440.png` | Proposal panel (element) with the re-accept message |
| `01c-agreements-reaccept-required-1440.png` | Signed documents panel: "In use: s261-aa955-vra8tb", re-accept required |
| `02-client-terms-updated-390.png` | Client proposal page: "Updated booking terms" section |
| `02b-client-terms-reaccepted-390.png` | Client proposal page after the re-accept |
| `03-mark-paid-ok-booked-1440.png` | "Deposit recorded. The trip is booked…" (before the page refresh, see F1) |
| `04-portal-sign-form-declined-390.png`, `04b-…-1440.png` | Portal signing form: insurance declined, declination text, code asked (masked) |
| `05-portal-code-expired-1440.png`, `05b-…-390.png` | "That code has expired. Ask for a new one." after 645 s |
| `06-portal-signed-declined-1440.png`, `06b-…-390.png` | Portal after signing |
| `07-agreements-panel-signed-declined-1440.png`, `07d-…-390.png` | Trip page with the Signed documents panel |
| `07b-agreements-panel-element-1440.png`, `07c-…-element-390.png` | The panel itself: declined travel insurance, sealed, 3 acceptances, signing log with `code_expired` |
| `08-sealed-envelope-1440.png` | Sealed envelope modal: "Seal checked: valid.", 3 documents incl. the declination; page behind shows Booked / deposit Paid |
| `run-log.txt`, `run-data.json` | Per-step statuses and shapes (ids cut to 8 characters) |
