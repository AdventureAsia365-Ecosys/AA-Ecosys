# AA-953 — Traveller portal per person: live check on Dev (S261, 31/10/2026)

**Feature:** CRM-24a portal per person (AA-Partner PR #145, merge `df5ac86`; checked on Partner main `132112aa`,
`/crm/health` `git_sha 132112aa1fbf…`, `/crm/health/ready` 200, `registered_keys` up to `crm-031` incl. `crm-029`).
**Hosts:** CRM web + API `https://portal.lumiguides.it.com`, client host `https://go-dev.lumiguides.it.com` (`/c/t`).
**Who:** synthetic agency *Lữ hành Sen Vàng* (e2e owner, partner pool password + authenticator); a second agency
(*Southern Cross* e2e owner) only to own one document for the cross-agency check. All people and addresses are invented
(`@example.invalid`). Sign-in codes came from the Dev echo (`PORTAL_OTP_DEV_ECHO`); no real mail was sent or clicked.
**How:** headless Playwright (Chromium), one browser, several contexts (one per traveller device), closed at the end.
Client-host writes were paced (5 per minute per address). Every API status below was read from the live response.

## What was set up (CRM side, Sen Vàng)

Run `vwye3w`, trip `18c61c49` "Việt Nam, 5 đêm" (30 Nov – 5 Dec 2026):

1. Inquiry form (client host) -> trip -> Qualifying -> Proposal (override `info_by_phone`) -> text proposal
   (USD 1234, deposit 321, published terms `s261-aa955-vra8tb`) -> sent -> the client accepts.
2. Party: **lead** (from the inquiry, own e-mail), **adult companion** with own e-mail, **child companion** without
   e-mail (DOB 2016-05-01, age band `2_11`).
3. Booking lines: Hotel (shared), Boat (shared, sell 777.77 / cost 555.55), Kayak (shared, then **cancelled**),
   Internal (not shared).
4. Documents (tiny synthetic PDFs): trip-wide shared, child's own shared, adult's own shared, child's own **not** shared.
5. **Mark paid** (deposit) in the trip page UI -> 200, trip `proposal -> booked`, `invite_all` invited 3 (lead,
   companion, companion), skipped none. The three "Copy link" boxes ("Portal link for …") were read from the page
   (`01-…png`, links masked).

## Results per check (Done-when lines of the live steps)

| # | Check | Result |
|---|---|---|
| 1 | Lead + adult with e-mail + child without e-mail on one trip, invite all, Copy link each | **PASS** — Mark paid 200, `invite_all` 3 invited / 0 skipped; 3 Copy-link boxes, all on `go-dev.lumiguides.it.com`. CRM portal rows after the run: lead *Signed in*, adult *Invited*, child *Signed in* (`07-…png`). |
| 2 | One link, cookie exchange | **PASS** — `/c/t/<token>` -> 303 -> `/c/t` (token leaves the address bar). `aa_portal_link`: Path `/crm/public/v1/traveller`, HttpOnly, Secure, SameSite Strict, host-only. Session cookie `aa_portal_s`: same path and flags. |
| 3 | Child's link -> code goes to the lead's address -> "Who are you?" | **PASS** — `POST /traveller/code` 202; `POST /traveller/session` without `traveler_id` -> **200 `{signed_in:false, pick:[lead, child]}`** (names shown only after the correct code; the child entry is flagged `link`). Picker screenshots `02-…` (1440/390, light/dark). |
| 4 | Pick the child -> separate session | **PASS** — same code with the child's `traveler_id` -> 200 `signed_in:true`; `GET /traveller`: `me` = child, role companion, `switch_to = [lead]`. On the **lead's** link (another browser context) a new code -> picker `[lead, child]` -> pick lead -> `me` = lead, while the child-link context still answers `me` = child (two separate sessions; access log `portal_sign_in` allowed ×2 + allowed(picked) ×1, `portal_pick` asked ×3). |
| 5 | Switch | **PASS** — UI "Switch to … Lead" -> `POST /switch` 200, `me` = lead (party of 3, `switch_to=[child]`); "Switch to … Child" -> 200, `me` = child. Switch to the adult (own address) -> **403 `not_your_traveller`** (logged `portal_switch` denied `not_in_group`). |
| 6 | Per-person home: own flights | **PASS** — as the child `PUT /traveller/flights` (arrival VN0123 SGN, departure VN124 HAN, Asia/Ho_Chi_Minh) -> 200; home shows both with UTC+07:00 and "on the first day / on day 6 of your trip" (`03-…`). |
| 7 | Own / shared documents | **PASS** — child home lists exactly `child-shared (for you)` and `trip-shared (for the whole group)`; opening each -> 200 with content. The adult's own sign-in lists only his own + the trip document. |
| 8 | No prices | **PASS** — child home JSON has no `payments`, no `party`, no `amount/sell/cost`, none of 777.77 / 555.55 / 1234 / 321.00; service rows carry only title, dates, status, confirm class, pay-on-arrival. The page text has no "777". (The **lead** home does show the payment schedule — deposit 321 paid, balance 913 due — by design of the AA-946 base.) |
| 9 | No cancelled lines | **PASS** — services = Hotel + Boat only; Kayak (cancelled) and Internal (not shared) absent in API and UI. |
| 10 | Passport scan write-only | **PASS** — `POST /traveller/passport-scan` (1×1 PNG) -> 200 `{received:true, kind:"passport_scan", size_bytes:70}` (no content echoed); home says "A passport scan is on file". Agency list: `write_only true`, `visible_to_travelers false`. Child opening it -> **403 `document_write_only`**. |
| 11 | Other traveller's document | **PASS** — child opening the adult's shared document -> **403 `document_not_yours`**; adult opening the child's shared document -> **403 `document_not_yours`**. Bonus: child's own unshared document -> 403 `document_not_shared`. |
| 12 | Another agency's document | **PASS** — a Southern Cross document (shared with travellers there) opened from the Sen Vàng child session -> **404 `document_not_found`**. |
| 13 | Companion invite 409 rules | **PASS** — lead `POST /companions {adult}` -> **409 `already_invited`**, and the adult's link still opens afterwards (`GET /traveller` 200, sign-in page). Lead giving the child the adult's address (UI) -> **409 `email_in_use`**, note "This e-mail address cannot be used…" (`04a-…`). After the child got an own address, `POST /companions {child}` -> **409 `already_invited`**. |
| 14 | Lead gives the child an own e-mail -> reach own, no link | **PASS** — UI invite with a fresh address -> **200 `{reach:"own", link_path:null}`**; note "…'s link goes to their own e-mail address…"; no `/c/t/` link anywhere on the page (`04-…`, 1440/390, light/dark). Lead's party now shows the child "own e-mail · has opened their page". |
| 15 | The old child session is signed out | **PASS** — (a) the lead-address session acting as the child **on the lead's link** -> `GET /traveller` 200 **`signed_in:false`** (address binding, `sent_to_bidx`), reload shows the sign-in page; (b) the child-link session -> **404 `link_not_found`** because the invite re-issued the child's link to the new address (page: "This link does not work any more…", `05-…`). The lead's own session stays signed in (`me` = lead). Note: on the child's old link the answer is 404 (link revoked), not `signed_in:false` as the step text says; both end the old session. |
| 16 | Access log | **PASS** — Settings > Access log filtered `portal_companion_email`: one **allowed** (object client = the child) and one **REFUSED, reason: email in use** on the lead's traveller access (`06-…`). Also logged in the last hour: `portal_document` allowed 2 / denied `document_write_only`, `document_not_yours`, `document_not_shared` (`06b-…`); `portal_companion_invite` allowed(own_address) 1, denied(already_invited) 2; `portal_flights` allowed 1; `portal_invite` new 6 (two setup runs) + reissue 1. |
| 17 | Console / network | Console errors 10, **all** "Failed to load resource" for the deliberate refusals (403 ×4, 404 ×3, 409 ×3); CRM responses ≥ 400 are exactly the refused calls above. Setup run: 0 errors. No sideways overflow at 1440 or 390 on any shot. |

## Screenshots (this folder)

| File | What |
|---|---|
| `01-crm-mark-paid-invite-all-copy-links-1440.png` | CRM trip page after Mark paid: three "Portal link for …" Copy-link boxes (masked) |
| `02-portal-picker-who-are-you-{1440,390}-{light,dark}.png` | `/c/t` "Who are you?" picker on the child's link (code + hint masked) |
| `03-portal-child-home-{1440,390}-{light,dark}.png` | Child home: two shared lines, flights, scan on file, own + trip documents, no prices |
| `04-portal-lead-group-after-own-invite-{1440,390}-{light,dark}.png` | Lead home: note after the own-address invite (no link), "Your group" with reach per person |
| `04a-portal-lead-refused-address-1440-light.png` | Lead: refused address note (`email_in_use`) |
| `05-portal-old-child-link-after-own-address-390-light.png` | The child's old link after the re-issue: "This link does not work any more" |
| `06-crm-access-log-portal-companion-email-1440-light.png` | CRM Access log: allowed + REFUSED (email in use) |
| `06b-crm-access-log-portal-document-1440-light.png` | CRM Access log: portal_document events |
| `07-crm-trip-portal-rows-1440-light.png` | CRM trip page portal rows after the run |
| `08-portal-sign-in-dark-preference-on-load-390.png` | `/c/t` loaded with a dark system preference (`data-theme=dark`) |

Dark shots: the page follows `prefers-color-scheme: dark` **on load** (shot 08: `data-theme=dark`); it does not switch
live when the preference changes after load, so for the dark shots of an already-signed-in page the run set
`data-theme="dark"` on `<html>` (the same attribute the restore script sets), instead of reloading and losing the
picker state.

## Small findings (not blockers)

- **1440 child home, flight form:** the "Local time at the airport" `datetime-local` input sticks out ~30 px past the
  right border of its flight card (`03-portal-child-home-1440-light.png`); no page overflow, fine at 390. Cosmetic.
- **Access log filter dropdown:** opened with `?action=portal_companion_email`, the rows are filtered but the Action
  select still reads "Any action" (`06-…`).
- **CRM portal rows right after Mark paid** read "No portal link yet" until the page refreshes (the setup read them
  immediately after the click); after a reload they show Signed in / Invited correctly (`07-…`).

## Not tested (and why)

- **Real code e-mail delivery / mailbox path:** Dev echoes the code (`delivery = dev_echo`); no mail was sent or opened
  (rule: never send real mail). Delivery through the lead's address is proven by the picker content, not by a mail.
- **Atlas & Hearth** as the "other agency": no CRM e2e user is a member of it (same as the AA-961 note); the
  cross-agency 404 used the Southern Cross e2e owner's synthetic document instead.
- **`ask_your_agent`** (lead sets an address for a companion who is on another trip), **`email_on_file`** and the
  **429 `too_many_attempts`** cap after three refused addresses: not exercised live (one refusal only, to keep the
  lead under the cap); covered by the PR's integration tests.
- **Agency changing the lead's address ends sessions** (`test_an_agency_address_change_ends_the_sessions_it_proved`):
  not run live.
- **Proposal days / itinerary block:** the text proposal has no days, so the itinerary list was empty.
- **Uploading the scan through the page's file picker:** the scan was posted with the same cookie route the page uses
  (`fetch` from the page); the button itself was not clicked.
- **Lead signing as guardian for the child / Stage 3 save:** out of AA-953's live steps (AA-955 e-sign).

## Data left on Dev (synthetic)

- Sen Vàng: trip `18c61c49` (run `vwye3w`, Booked) with 3 clients, 4 lines, 5 documents (incl. the PNG scan);
  trip `3a1fa893` (run `vwx685`, Booked) from a first setup run whose script stopped after Mark paid on a test-side
  lookup bug (lead id missing from the board card) — same shape, no portal checks run on it.
- Southern Cross: client "E2E S261 Other …" + one shared document.

Scripts and raw run data stay in the gitignored `.tmp-session/S261/aa953/` (`run-log.txt`, `setup.json`,
`portal.json`, `cookies.json`, `other-agency.json`); link tokens, codes and session values were never logged.
