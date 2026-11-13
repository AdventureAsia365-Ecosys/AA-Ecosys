# Pilot rehearsal UAT videos (S279, 2026-11-13)

The AA-1086 synthetic pilot rehearsal ([runbook](../../../ops/runbooks/pilot-rehearsal.md)) recorded as UAT videos,
one take per scenario, on Dev. Harness: `tools/uat/` (branch `feat/aa1086-uat-rehearsal`, the five rehearsal scenario
branches merged). Each video has burned-in English subtitles, an English (Kokoro) and a Vietnamese (VieNeu) narration
track, and SRT/VTT sidecars; each is packaged as one zip and stored on the team drive (link not in this public repo).

## Set-up

| Item | Value |
|---|---|
| Agency | `pilot-rehearsal-01` (synthetic, kind demo, CRM + TripPlanner add-ons), id `41ea21ee` |
| Tour X | A 6-day Philippines tour: CIS source `000e3340`, pool / TripPlanner tour id `0c8bdf9e`. The tech lead's first choice was a Laos tour, but no Laos tour is priced or sold to agencies on Dev (Booking price workbench: Laos 45 tours, 0 priced; the CRM answers `aa_product_not_found`). This tour is the only one sold to agencies, so the orchestrator picked it for every step. Step 5 searches "Bohol" (`UAT_REH_SEARCH`) instead of "Laos". |
| Identities | E2E CIS admin (A10b), E2E Booking admin (A10a), E2E CRM staff (A10c), the agency's E2E owner and agent, an invented traveller on `example.invalid` |
| Egress | VN for every take (checked before each take); RAM at least 2.5 GB free before each take |
| App versions | AA-Partner (CRM, portal) `d3cd905` for every CRM take, redeployed to `0f2baf4` during the REH-10b takes (the v3 take stopped on that; v4 ran on `0f2baf4`) |

## Takes

Length in seconds. "Failed at" is the step and its start / end time in the video.

| # | Scenario | App | Verdict | Length | Failed at | What it shows |
|---|---|---|---|---|---|---|
| 0 | REH-00-baseline (v1) | CIS admin | PASS | 27 | - | Platform overview, job queue and AI spend caps before the run |
| 1 | REH-01-provisioned (v1) | CIS admin | PASS | 28 | - | Tenant 360 of the agency: kind demo, in service, not the pilot, Content plan with CRM and TripPlanner add-ons |
| 1 | REH-01-crm-agency (v1) | CIS admin | PASS | 23 | - | CRM agencies: the agency is active, synthetic, has an owner |
| 1 | REH-01-booking-partner (v1) | Booking | PASS | 19 | - | Booking knows the agency as a partner; its tariff prices tour X per group size |
| 2 | REH-02-members (v1) | CIS admin | PASS | 20 | - | Members: the owner is active; the E2E admin cannot invite an owner |
| 2b | REH-02b-agency-setup (v1) | CRM | PASS | 68 | - | Owner saves bank-transfer instructions, publishes booking terms and a waiver |
| 3 | REH-03-brand (v1) | Studio | PASS | 30 | - | Brand guide (.docx) imported, brief read, brand saved |
| 3 | REH-03-adopt (v2) | Studio | PASS | 82 | - | Tour X and two more adopted in one bulk rewrite (3 rewrites), DOCX export with the AI mark. Data gap: tour X has no catalog photo (card placeholder) |
| 4 | REH-04-topics (v2) | Studio | FAIL | 56 | step 3, 20.0-53.6 s | Topic update ran (4 s), but none of the 3 adopted tours got an article topic: each is `seed_too_thin` (description too short for a ~900-word article). The page states the reason per tour; with no topic there is nothing to pick |
| 4 | REH-04-linkedin (v2) | Studio | PASS | 59 | - | One LinkedIn post: topic, goal, three angles, write, AI notice |
| 4 | REH-04-facebook (v1) | Studio | PASS | 66 | - | One Facebook post, same flow |
| 4b | REH-04b-facebook (v3) | Studio | FAIL | 75 | step 2, 7.3-73.1 s | Connecting the Facebook test Page is refused: "Invalid or expired Page Access Token". The stored test-Page token has expired |
| 4b | REH-04b-takedown (v1) | Studio | PASS | 21 | - | Teardown: no live test post is left |
| 5 | REH-05 (v1) | TripPlanner | PASS | 62 | - | Agency planner with its colours and name, search "Bohol", tour X pinned from the agency's own list, three chat turns answered |
| 5 | REH-05.m (v1) | TripPlanner | PASS | 29 | - | At 390 px: tour X added, a stop reordered, no sideways scroll |
| 6 | REH-06 (v1) | TripPlanner | FAIL | 50 | step 5, 29.6-47.6 s | Double-click on Send: one request, panel "Sent to the agency", button off. The FAIL is the harness: the repeated send it replays to prove idempotency got no recorded answer. The product side is proven by REH-06-lead (one lead). Not re-taken: a second take would add a second lead to the agency |
| 6 | REH-06-lead (v1) | CRM | PASS | 54 | - | The planner lead is in the pipeline; owner assigns the agent, sets dates from tour X's departure, moves stages |
| 7 | REH-07-quote (v1) | CRM | PASS | 94 | - | Agent builds the proposal: AA line for tour X with a live Booking quote, own hotel, inclusions, discount above the agent's limit asks for approval |
| 7b | REH-07b-approve (v1) | CRM | PASS | 35 | - | Owner approves the discount, publishes and sends the quote |
| 8 | REH-08-accept (v1) | CRM | PASS | 43 | - | Client accepts on the phone (Booking hold placed) |
| 8b | REH-08b-deposit (v1) | CRM | PASS | 48 | - | Deposit invoice, client "I've paid", agency records the payment, trip booked |
| 8c | REH-08c-aa-confirmed (v1) | CRM | PASS | 33 | - | AA booking confirmed (instant-confirm departure); the AA B2B price equals the net quoted in the builder (168.84 USD) |
| 10 | REH-10-portal (v1) | CRM portal | FAIL | 72 | step 6, 63.1-69.5 s | Traveller code sign-in, passport details, arrival flight and e-sign pass. The itinerary lists 7 dated days (right count) but no day titles or places and no services block: the confirmed AA tour is not listed, so the voucher step is not reached |
| 10b | REH-10b-ops-view (v4) | CRM staff console | PASS | 24 | - | AA ground operations board lists the trip with tour X's departure; the release shows the departure and the lead's name |

Takes that were scenario bugs and were fixed, then re-taken (the earlier takes are not kept as evidence):
REH-03-adopt v1 (photo assert), REH-04-topics v1 (an automatic topic update was still running after the adoption;
timing), REH-04-linkedin v1 (AI notice looked for inside the wrong element), REH-04b-facebook v1/v2 (clicked the
WordPress card's Test & Connect button), REH-10b-ops-view v1/v2 (row locator), v3 (CRM redeployed during the take).

## Not recorded

| Scenario | Why |
|---|---|
| REH-04-blog, REH-04-edit, REH-04b-wordpress | No article topic exists (REH-04-topics), so no blog article to write, edit or publish. The WordPress test site answers JSON on `/wp-json/` |
| REH-08a (Book now) | Needs the agency's Book now switch and its form key (not set) |
| REH-09-supplier, REH-11-maker, REH-11-checker | Need the Booking seeder output for this agency (`python -m app.e2e_fixtures --apply ... --agency-tenant`, ECS exec): an orchestrator step |
| REH-01-price-import, REH-01-prices, REH-01-from-price | Price import and its approvals are tech-lead steps; only 2 tours are priced on Dev |
| REH-01b, REH-12b (pilot marker), REH-12-budget-* (X1) | Need the tech lead: no marker tenant and no budget override today |
| REH-02-owner-invite | Tech-lead act (done earlier today, off camera) |

## Findings

Product or data gaps (each needs an owner decision; no issue was opened by this run):

1. **Topics: tour X and both other auto-picked tours are `seed_too_thin`.** No article topic, so step 4's blog chain
   cannot run on this tour set. Either richer tour descriptions for the rehearsal tour or an adoption choice that
   includes a tour with a long description.
2. **Traveller portal itinerary is empty of content** (REH-10, step 6): dated days only, no day titles/places, no
   services, so the confirmed AA tour is not shown. Could be the hourly ops-release sync not having run yet; re-check
   before treating it as a code gap.
3. **Facebook test Page token expired** (REH-04b-facebook): the tech lead renews the long-lived Page token in the
   test-channel secret; then REH-04b-facebook and REH-04b-takedown are re-recorded.
4. Tour X has no catalog photo (studio card shows the placeholder).
5. TripPlanner: the 6-day tour lands as 4 day groups / 4 stops in the guest trip, and "Getting there" suggests flying
   into Taipei with a ~1,700 km overland transfer to the first stop (Manila). Worth a look by the TripPlanner owner.
6. Ops board: the rehearsal trip shows "0 of 1 complete" travel details after the traveller saved passport and flight
   data in REH-10 (likely the release resync; same note as item 2).
7. The two social posts were written about another adopted tour (the topic list ranks across all adopted tours), not
   tour X.

Harness:

- REH-06: the idempotency replay accounting (send answers) needs a fix before the next take (open).
- The Vietnamese narration track was added after recording for every take (the VieNeu venv was not linked in the
  worktree during the takes): steps were held to the English narration length, so a Vietnamese line can run past its
  step. `check_sync.py --track 1` finds speech at every cue start of every take (0 cues without speech); the longest
  Vietnamese line runs 1.7 s past its step (REH-02-members), every other take 0.9 s or less. Fixed for the next run:
  the worktree now links `venv-vi` too.

## LLM spend

Read from the CIS admin tenant cost view (`shared.llm_call_log`, this calendar month, the agency's tenant id, shadow
rows excluded). The agency had no spend before this run. CRM AI drafts: none were made.

| Stage | Calls | USD |
|---|---|---|
| t2_generate (3 rewrites) | 3 | 0.1210 |
| t8_angle_gen | 3 | 0.0713 |
| t9_write | 5 | 0.0610 |
| tp_plan_chat (3 chat turns) | 14 | 0.0276 |
| t10_judge | 6 | 0.0048 |
| t7_debate_judge (topic update) | 13 | 0.0015 |
| t2_judge, t2_flag_fix, t9_repair, f10_embed, tp_search_embed | 12 | 0.0021 |
| **Total** | | **0.2893** |

Cap 10 USD; estimate in the runbook 2-4 USD (lower here because no article was written).

## Scenario fixes made during the run

All on `feat/aa1086-uat-rehearsal` (local): the merge of the five branches (one method-aware `limitWrites`:
`method` one/list/`'*'`, `read`, `accept`, `strict`; method-aware `allowWrites` in `net-guard`), the `signin.cjs`
merge fix, REH-05 search term from `UAT_REH_SEARCH`, REH-03-adopt photo as a data gap, the AI-notice locator of the
social posts, the Test & Connect button of the publish scenarios, `build.py` names for ids with a dot (REH-05.m), and
the REH-10b row locator and wrap-tolerant departure match.
