---
id: APP-10-crm-review-fast-run-s261
title: "CRM review video: full fast run of R00-R20 on Dev (S261)"
description: "Result of one full fast-mode run of the CRM review set (prep, chunks R00 to R20, cleanup) on Dev with the invented agency, before any recording: verdict, failing step, cause and AA-Partner version per chunk, plus what the recording session must still set up."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [aa-partner]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-1014, AA-855, docs/audits/2026-10-31-S261-crm-progress-video-plan/README.md]
---

# CRM review video: full fast run of R00-R20 on Dev (S261)

One full pass of the review set in fast mode (every step acts and asserts; no video, no holds, no narration), run
with `bash tools/uat/scenarios/crm/run-all.sh --fast` on 31/10/2026, 16:22-16:31 (+07). The chunk list and the
identities come from the approved plan
(`2026-10-31-S261-crm-progress-video-plan` (`docs/audits/2026-10-31-S261-crm-progress-video-plan/README.md`, root PR at the S261 close), §3-§5).

## Conditions

| Item | Value |
|---|---|
| Environment | Dev CRM web (`portal.lumiguides.it.com`), invented agency "Lữ hành Sen Vàng" |
| Identities | A = E2E owner, B = E2E assistant (R18), C = anonymous client host (R03, R08 to R11), signed in outside the run |
| Run suffix | `rv202610314` (clients on `@example.invalid`) |
| Prep | departure 2026-11-20 with 4 free seats; deposit invoice due 2026-10-31 (overdue from 2026-11-01) |
| AA-Partner version | `d29e29e` at the start and the end of every chunk (no deploy during the run) |
| Browser | one Chromium at a time, closed after each chunk; RAM available before each launch: about 7.4 GB |
| Egress | VN |
| Cost | $0: no LLM call, no AI button clicked, no real person mailed or invited (see Mail below) |
| Rate limit | no HTTP 429 seen |

## Result per chunk

All 23 runs passed; no failing step, so no cause to classify (product bug or script).

| Chunk | Story | Verdict | Steps | Failing step | Cause | AA-Partner git_sha |
|---|---|---|---|---|---|---|
| CLEANUP (before) | the previous run's leftovers | PASS | 4/4 | – | – | – |
| PREP | departure, invoice, import file | PASS | 6/6 | – | – | d29e29e |
| R00 | intro cards | PASS | 3/3 | – | – | d29e29e |
| R01 | home | PASS | 5/5 | – | – | d29e29e |
| R02 | onboarding and import | PASS | 7/7 | – | – | d29e29e |
| R03 | an inquiry arrives | PASS | 6/6 | – | – | d29e29e |
| R04 | pipeline | PASS | 8/8 | – | – | d29e29e |
| R05 | client profile | PASS | 6/6 | – | – | d29e29e |
| R06 | proposal builder | PASS | 11/11 | – | – | d29e29e |
| R07 | written proposal and Before you go | PASS | 7/7 | – | – | d29e29e |
| R08 | the client accepts on a phone | PASS | 6/6 | – | – | d29e29e |
| R09 | booking terms and e-sign | PASS | 8/8 | – | – | d29e29e |
| R10 | deposit invoice and payment | PASS | 8/8 | – | – | d29e29e |
| R11 | traveller portal | PASS | 8/8 | – | – | d29e29e |
| R12 | travelling now, calendar, ICS feed | PASS | 6/6 | – | – | d29e29e |
| R13 | trip threads, saved reply, draft | PASS | 6/6 | – | – | d29e29e |
| R14 | suppliers and bookings ledger | PASS | 4/4 | – | – | d29e29e |
| R15 | reports and CSV export | PASS | 6/6 | – | – | d29e29e |
| R16 | data export; erasure answered 409 `deletion_dry_run` | PASS | 6/6 | – | – | d29e29e |
| R17 | settings, Vietnamese and back, dark mode and back | PASS | 7/7 | – | – | d29e29e |
| R18 | assistant B: role-blocked items | PASS | 5/5 | – | – | d29e29e |
| R19 | five empty pages and the "Not ready yet" card | PASS | 7/7 | – | – | d29e29e |
| R20 | closing cards | PASS | 2/2 | – | – | d29e29e |
| CLEANUP | this run's data | PASS | 4/4 | – | – | – |

Notes on single chunks:

- **R10**: the run was prepared the same day, so the chunk took its "due today" branch (open invoice, no overdue
  task, caption says what happens once the date passes). The overdue-reminder version needs a prep at least one agency
  day (Ho Chi Minh time) before the recording.
- **R12**: no AA incident was open, so the chunk took its one-step "none open today" branch and checked that the CRM
  API agrees. The incident version (banner and urgent task) runs only when an incident is raised for the trip of
  departure 13/11 and recorded in the run state; that trip leaves the 14-day window after 15/11.
- **R16**: the confirm step asserts HTTP 409 with `detail = deletion_dry_run` and the "Deletion is switched off"
  alert: deletion is switched off on Dev on purpose, nothing is deleted.
- **R18**: besides the hidden menu items and the role page, the chunk asserts that the server refuses the team list
  to the assistant (HTTP 403), not only the screen.
- **R19**: the plan listed six empty pages; Help is built now (getting-started guides), so five real empty pages are
  shown (Tasks, Automations, Commissions, Marketing, Library) and Help is not faked as empty.
- **Cleanup**: trips moved to Lost (one booked example left at booked), the Adventure Asia hold released, saved reply and draft
  deleted, ICS feed revoked, both data requests closed as withdrawn, the R16 client moved to the trash.

## Re-run after the review fixes (17:07-17:33 +07)

After the review fixes (masks on before the first paint and asserted where a secret shows, link tokens tied to their
trip, phone chunks as a real mobile context, cleanup of the imported clients), two full fast passes and one re-run:

| Pass | Run | Result | Failing step | Cause | Fix |
|---|---|---|---|---|---|
| 1 | `rv202610315` | 21 of 23 PASS | R08 step 4 (R09 step 1 follows) | Booking refused the client hold: "You checked availability 3 times today". Booking allows 3 re-holds of a departure per UTC day once a hold of it was let go, and runs 1 to 5 of the day all held, then released, the same departure (2026-11-20). Product rule working as designed. | prep takes the next eligible departure per run; R08 names a refused hold |
| 2 | `rv202610316` (departure 2026-12-04) | 21 of 23 PASS | R17 step 6; R19 step 4 | R17: the language was picked before the reloaded page hydrated, so the select did not submit (script timing). R19: one page landed on the partner sign-in page in the middle of the chunk, near the 30-minute access-token renewal; the saved session was still valid right after. | R17 waits for the page and submits the form when the pick did not |
| re-run | `rv202610316` | R17 PASS 7/7, R19 PASS 7/7 | – | – | – |

Every other chunk passed in both passes, AA-Partner `d29e29e` at the start and the end of each. The R19 sign-in
redirect was seen once in three passes; if it shows again in a recorded take, the take stops (the chunk fails) and is
recorded again. No HTTP 429 from the anonymous client host.

## Mail during a run

The review never presses Send in the mail composer (R13) or the written-proposal hand-over (R07), but some steps
make the CRM queue mail to the invented client, and that mail really leaves: the CRM sends client mail only through
the agency's connected mailbox (no fallback to Adventure Asia's mail service), and the invented agency has a real
Gmail account connected on Dev. The mails are:

- sending a proposal (prep for R10, R06): the client link to the lead;
- the paid deposit (R10): a portal invitation to each traveller;
- the traveller portal (R11): the sign-in code mail and the companion invite.

That is about 6 to 8 mails per run, all to `@example.invalid` addresses, which no server accepts: each one bounces
back into the connected Gmail mailbox. No real person receives anything. The clean-up step reports the outbound mail
of the run's trips by status (`meta.outbound_mail` in its result, no address or subject).
Ways to stop this, for the tech lead to choose: connect a test-only mailbox to the invented agency instead of the
real Gmail account (the bounces then land there), or add a Dev-only rule in AA-Partner that marks mail to `.invalid`
recipients as sent without handing it to the provider.

## Deviations from the plan

- **R10**: the plan lists the Booking staff identity (D) for R10. The invoice trip has no Adventure Asia item, so
  there is nothing for Booking staff to see; the Adventure Asia hold appears in R08 (client hold) and R12 instead.
- **R19**: Help is built now, so five empty pages are shown, not six (see above).
- **Plan risk row "real mail leaving"**: it reads as if no mail leaves; see Mail during a run for what does.

## Not covered by this run

- Recorded takes, narration and the long-form build (`run-all.sh` without `--fast`, then `longform.py`): left for the
  recording session.
- The R10 overdue version and the R12 incident version, for the timing reasons above.

## How to repeat

```bash
bash tools/uat/scenarios/crm/run-all.sh --fast          # cleanup last run, new prep, R00..R20, cleanup
bash tools/uat/scenarios/crm/run-all.sh --fast --only 10,12 --keep-run   # re-run single chunks on the current run
```

Per-chunk rows are written to `tools/uat/work/crm/run-all.tsv` (gitignored).
