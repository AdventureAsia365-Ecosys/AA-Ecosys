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
| Tour Y (blog chain only) | A 20-day China tour: CIS source `35784e28`, pool / TripPlanner tour id `80172001`, with a photo, not priced. Tour X's description is too thin for an article (finding 1), so the article, its edit and the WordPress publish used tour Y (approved by the tech lead). |
| Booking fixtures | The Booking E2E seeder run `s279reh` for this agency (trip case, supplier booking, invoice, on tour X), seeded by the orchestrator |
| Identities | E2E CIS admin (A10b), E2E Booking admin (A10a), E2E Booking writers (A10e), E2E CRM staff (A10c), the agency's E2E owner and agent, an invented traveller on `example.invalid` |
| Egress | VN for every take (checked before each take); RAM at least 2.5 GB free before each take |
| App versions | AA-Partner (CRM, portal) `d3cd905` for the CRM takes up to REH-10, redeployed to `0f2baf4` during the REH-10b takes (v4 ran on `0f2baf4`); REH-10a and REH-10c ran on `3ed93c8` (the #306/#307 fix) |

## Takes

Length in seconds. "Failed at" is the step and its start / end time in the video. The version is the one packaged.

| Step | Scenario | App | Verdict | Length | Failed at | What it shows |
|---|---|---|---|---|---|---|
| 0 | REH-00-baseline (v1) | CIS admin | PASS | 27 | - | Platform overview, job queue and AI spend caps before the run |
| 1 | REH-01-provisioned (v1) | CIS admin | PASS | 28 | - | Tenant 360 of the agency: kind demo, in service, not the pilot, Content plan with CRM and TripPlanner add-ons |
| 1 | REH-01-crm-agency (v1) | CIS admin | PASS | 23 | - | CRM agencies: the agency is active, synthetic, has an owner |
| 1 | REH-01-booking-partner (v1) | Booking | PASS | 19 | - | Booking knows the agency as a partner; its tariff prices tour X per group size |
| 2 | REH-02-members (v1) | CIS admin | PASS | 20 | - | Members: the owner is active; the E2E admin cannot invite an owner |
| 2b | REH-02b-agency-setup (v1) | CRM | PASS | 68 | - | Owner saves bank-transfer instructions, publishes booking terms and a waiver |
| 3 | REH-03-brand (v1) | Studio | PASS | 30 | - | Brand guide (.docx) imported, brief read, brand saved |
| 3 | REH-03-adopt (v2) | Studio | PASS | 82 | - | Tour X and two more adopted in one bulk rewrite (3 rewrites), DOCX export with the AI mark. Data gap: tour X has no catalog photo |
| 3 | REH-03-adopt (v3) | Studio | PASS | 116 | - | Tour Y adopted (1 rewrite) for the blog chain; recorded gap: not priced |
| 4 | REH-04-topics (v3) | Studio | PASS | 98 | - | Topic update (31 s); tour Y gets 8 article topics, the three thin tours show their reason; top topic picked, goal, three angles, article started |
| 4 | REH-04-blog (v1) | Studio | PASS | 47 | - | The article is written live (steps shown) and delivered to My Content |
| 4 | REH-04-linkedin (v2) | Studio | PASS | 59 | - | One LinkedIn post: topic, goal, three angles, write, AI notice |
| 4 | REH-04-facebook (v1) | Studio | PASS | 66 | - | One Facebook post, same flow |
| 4 | REH-04-edit (v1) | Studio | PASS | 39 | - | Owner edits the article in the viewer: adds the planner link of tour Y; no writer brief or search context in the viewer |
| 4b | REH-04b-wordpress (v3) | Studio | PASS | 58 | - | WordPress test site connected, article published (live post carries the planner link and the AI mark), unpublished, published again: one live post |
| 4b | REH-04b-facebook (v4) | Studio | PASS | 46 | - | Facebook test Page (renewed token) publish, unpublish, publish again: one live post; the Page id is blurred |
| 4b | REH-04b-takedown (v4) | Studio | PASS | 24 | - | Teardown: every live test post (WordPress and Facebook) unpublished; the publish log keeps each as Unpublished |
| 5 | REH-05 (v1) | TripPlanner | PASS | 62 | - | Agency planner with its colours and name, search "Bohol", tour X pinned from the agency's own list, three chat turns answered |
| 5 | REH-05.m (v1) | TripPlanner | PASS | 29 | - | At 390 px: tour X added, a stop reordered, no sideways scroll |
| 6 | REH-06 (v1) | TripPlanner | FAIL | 50 | step 5, 29.6-47.6 s | Double-click on Send: one request, panel "Sent to the agency", button off. The FAIL is the harness (its count of the repeated send); fixed since, not re-taken (a new take adds a second lead). The product side is proven by REH-06-lead (one lead) |
| 6 | REH-06-lead (v1) | CRM | PASS | 54 | - | The planner lead is in the pipeline; owner assigns the agent, sets dates from tour X's departure, moves stages |
| 7 | REH-07-quote (v1) | CRM | PASS | 94 | - | Agent builds the proposal: AA line for tour X with a live Booking quote, own hotel, inclusions, discount above the agent's limit asks for approval |
| 7b | REH-07b-approve (v1) | CRM | PASS | 35 | - | Owner approves the discount, publishes and sends the quote |
| 8 | REH-08-accept (v1) | CRM | PASS | 43 | - | Client accepts on the phone (Booking hold placed) |
| 8b | REH-08b-deposit (v1) | CRM | PASS | 48 | - | Deposit invoice, client "I've paid", agency records the payment, trip booked |
| 8c | REH-08c-aa-confirmed (v1) | CRM | PASS | 33 | - | AA booking confirmed (instant-confirm departure); the AA B2B price equals the net quoted in the builder (168.84 USD) |
| 9 | REH-09-supplier (v1) | Booking | PASS | 26 | - | Booking staff (A10e) request the seeded supplier booking of the agency's trip case and record the supplier's confirmation |
| 10 | REH-10-portal (v1) | CRM portal | FAIL | 72 | step 6, 63.1-69.5 s | Traveller code sign-in, passport details, arrival flight and e-sign pass. The itinerary lists 7 dated days (right count) but no day titles or places and no services block: the confirmed AA tour is not listed, so the voucher step is not reached (finding 2; fixed since, see REH-10a and REH-10c) |
| 10 | REH-10a-show-aa-line (v1) | CRM | PASS | 22 | - | After the CRM fix (AA-Partner #306/#307), the owner shows the trip's confirmed AA line to travellers from the Bookings panel ("Show to travellers"); the line was confirmed before the fix, so it started hidden |
| 10 | REH-10c-itinerary (v1) | CRM portal | PASS | 36 | - | The traveller signs in again: the itinerary lists the 7 days with the tour's day titles and places (6 days with content), "What is booked" lists the confirmed tour, and the tour voucher is there |
| 10b | REH-10b-ops-view (v4) | CRM staff console | PASS | 24 | - | AA ground operations board lists the trip with tour X's departure; the release shows the departure and the lead's name |
| 11 | REH-11-maker (v1) | Booking | PASS | 23 | - | Finance maker records the agency's payment on its seeded invoice |
| 11 | REH-11-checker (v1) | Booking | PASS | 17 | - | A second finance user (checker) approves that payment |
| - | DRILL-01 (v5) | CIS admin | PASS | 719 | - | Tenant offboarding erasure drill on a synthetic audit tenant: offboard, start the drill, DRY RUN reports per app, approval closed, stop for good, restore (recorded in the drill worktree; Vietnamese track added afterwards) |

**34 videos: 32 PASS, 2 FAIL.** The two FAILs: REH-06 (harness, fixed) and REH-10-portal v1 (the product gap of finding 2, fixed and re-checked by REH-10c).

Earlier takes kept on the drive as evidence of what changed: REH-04-topics v2 (FAIL: every adopted tour
`seed_too_thin`), REH-04b-facebook v3 (FAIL: "Invalid or expired Page Access Token", before the token was renewed),
REH-04b-takedown v1. Takes that were scenario bugs, fixed and re-taken: REH-03-adopt v1, REH-04-topics v1 (an automatic
topic update was still running), REH-04-linkedin v1, REH-04b-facebook v1/v2, REH-04b-wordpress v1, REH-10b-ops-view
v1-v3. Two takes were deleted locally and never uploaded because they showed the test Facebook Page id in clear:
REH-04b-wordpress v2 (the Facebook card of the publish page was not blurred in the WordPress scenario) and an earlier
REH-04b-facebook v4 (the integrations page shows the Page id with no hook to blur it); both paths are fixed.

## Later takes (S280, S281)

Same harness and drive folder. The S280 takes REH-06 v2, REH-12-budget-on and REH-12-budget-off were uploaded in S281;
the S280 REH-08a PASS take was lost with its worktree and was taken again in S281 (v4).

| Step | Scenario (take) | App | Verdict | When | What it shows |
|---|---|---|---|---|---|
| 6 | REH-06 (v2) | TripPlanner | PASS 6/6 | S280 | Guest trip and one request to the agency; a double click on Send sends once (replaces the v1 harness FAIL) |
| 8a | REH-08a (v4) | CRM | PASS 5/5 | S281 | Book now on the agency's trip page: price check, then one booking on a departure with seats for the party; the Book now switch was on for the take only |
| X1 | REH-12-budget-on (v1) | CIS admin | PASS 3/3 | S280 | AI budget override of 0.05 USD with reason and expiry; the CRM draft is refused with `budget_exhausted` before any model call |
| X1 | REH-12-budget-off (v1) | CIS admin | PASS 3/3 | S280 | The override removed; CRM AI back to off with its 2.00 USD budget |
| 1b | REH-01b-pilot-on (v1) | CIS admin | PASS 3/3 | S281 | The marker tenant (kind agency) is the Dev pilot with an end date; End pilot sits next to the badge for the admin role (not pressed) |
| 12b | REH-12b-pilot-off (v1) | CIS admin | PASS 2/2 | S281 | After End pilot the badge and the button are gone; the Dev pilot slot is free |

Administrator writes of steps 1b and 12b (S281, actor `admin:agent-s281-aa1086`, API answers kept locally): the marker
tenant `a4dd7561` was provisioned with `pilot_weeks` 1 (job steps `tenant_created`, `pilot_marked`); a second pilot
request failed with `pilot_taken`; End pilot returned `changed` true; the soft offboard scheduled its erasure
(CIS, Booking, TripPlanner not before 2026-12-14, CRM not before 2027-02-12, the agreed retention); the marker's
Booking partner row read `suspended` about five minutes after the offboard (Teardown 7). The Dev pilot slot is free.
The erasure apply after 2026-12-14 needs a person's approval of its DRY RUN fingerprint (runbook Teardown 2).

## Not recorded

| Scenario | Why |
|---|---|
| REH-01-price-import, REH-01-prices, REH-01-from-price | Covered without video by the S280 pricing run (`docs/audits/2026-11-14-S280-session/verify/aa1091/`): a synthetic supplier, 4 tours priced through the Excel DRY RUN and import, the agency tariff and the TripPlanner "From" price checked. The synthetic supply was removed after that run, so the takes cannot be filmed now. |
| X1 items 2-3 (studio and planner refusal on budget) | No scenario yet (gap G8 of the runbook); the CRM refusal of X1 item 4 is filmed above |
| REH-02-owner-invite | Tech-lead act (done earlier today, off camera) |
| X2 (tour retirement) | Not run yet: retiring tour X changes shared Dev state for every tenant and is a tech-lead act in the runbook. The CRM handler it checks is live (CRM migration 063, `aa_tour_discontinued` task), so the CRM part is expected to PASS when X2 runs. |
| X3 (AA cancels a departure) | Proven live on the CRM E2E agency in S279 (`../verify/aa1087-crm13/`); on this agency it needs gaps G1 and G11 |

## Findings

Product or data gaps (no issue opened by this run):

1. **Data quality: tour X's description is too thin for an article.** The studio proposes a blog topic only when the
   seed of the pick reaches the blog seed floor (AA-CIS-App `services/acp_shared/blog_seed.py`: `max(flat, sized)`
   with the flat `cis.t7.blog_min_seed_words` 600 and the sized floor `ceil(4,700 / cis.t7.blog_chars_per_seed_word
   3.364)` = 1,398 seed words). Tour X and the two other auto-picked tours were all `seed_too_thin` (tour X's itinerary
   is about 240 words). Tour Y (itinerary about 1,900 words) got 8 topics at once. Of the 841 adoptable tours in the
   pool, 23 have an itinerary of 1,400 words or more, and none of those is priced.
2. **Traveller portal itinerary was empty of content** (REH-10-portal v1, step 6): dated days only, no titles or
   places, no services. Cause: the portal lists only lines marked `visible_to_travelers`, and the AA line was hidden by
   default; the accepted proposal's days had no title or place. **Fixed** by AA-Partner #306 (crm-065) and #307: a
   confirmed AA line is shown to travellers when the sync confirms it, the agency can show or hide it on the trip's
   Bookings panel, a whole AA tour added to a proposal brings its days' titles and places, and the portal falls back to
   the shown AA line's days for versions accepted before. The rehearsal trip's line was confirmed before the fix, so
   REH-10a shows it through the new control, and REH-10c reads the itinerary and the voucher (PASS). The first visit's
   details, flight and signature are not re-recorded: a recorded take never narrates work that is already done.
3. **The studio integrations page shows the Facebook Page id in clear** and gives no test id or class to blur it in a
   recording (`FacebookStatusCard`). The publish scenarios now never open that page; a `data-testid` on the Page line
   would let a future take show it safely.
4. A failed "Test & Connect" still stores the Facebook connection (state "Needs attention" with the failing token);
   replacing the token then needs a disconnect first. The publish scenarios now disconnect a stale connection once
   (capped, only when its last check failed) and connect again.
5. Tour X has no catalog photo; tour Y is not priced.
6. TripPlanner: the 6-day tour lands as 4 day groups / 4 stops in the guest trip, and "Getting there" suggests flying
   into Taipei with a ~1,700 km overland transfer to the first stop (Manila). Worth a look by the TripPlanner owner.
7. Ops board: the rehearsal trip shows "0 of 1 complete" travel details after the traveller saved passport and flight
   data in REH-10.
8. The two social posts were written about another adopted tour (the topic list ranks across all adopted tours), not
   tour X.

Harness:

- REH-06: the repeated send now records its own answer (the listener missed it when the page never read the body);
  unit-tested, not re-taken live.
- The Vietnamese narration track of the first takes was added after recording (the VieNeu venv was not linked in the
  worktree then); later takes were built with it. `check_sync.py --track 1` finds speech at every cue start of every
  take; the longest Vietnamese line runs 1.7 s past its step (REH-02-members).

## LLM spend

Read from the CIS admin tenant cost view (`shared.llm_call_log`, this calendar month, the agency's tenant id, shadow
rows excluded). The agency had no spend before this run. The Booking, CRM and drill takes made no model call; no CRM
AI draft was made.

| Stage | Calls | USD |
|---|---|---|
| t2_generate (4 rewrites: tour X and two more, then tour Y) | 4 | 0.2115 |
| t9_write (article and social posts) | 6 | 0.1178 |
| t8_angle_gen | 4 | 0.1068 |
| tp_plan_chat (3 chat turns) | 14 | 0.0276 |
| t10_judge | 8 | 0.0081 |
| t7_debate_judge (topic updates) | 63 | 0.0071 |
| t9_repair, t9_faq_answer_fit, t9_faq_filter, t2_judge, t2_flag_fix, f10_embed, tp_search_embed | 19 | 0.0119 |
| **Total** | | **0.4908** |

Cap 10 USD; estimate in the runbook 2-4 USD.

## Scenario fixes made during the run

All on `feat/aa1086-uat-rehearsal` (local): the merge of the five branches (one method-aware `limitWrites`: `method`
one/list/`'*'`, `read`, `accept`, `strict`; method-aware `allowWrites` in `net-guard`), the `signin.cjs` merge fix,
REH-05 search term from `UAT_REH_SEARCH`, REH-03-adopt photo as a data gap and an unpriced blog-chain tour behind
`UAT_REH_PRICE_OPTIONAL`, the AI-notice locator of the social posts, the Test & Connect button and the form-only blur
check of the publish scenarios, the Facebook summary blurred in every publish take and the capped reconnect of a stale
channel, `build.py` names for ids with a dot (REH-05.m), the REH-10b row locator and wrap-tolerant departure match, the REH-06 replay accounting, and the
new REH-10a (show the AA line) and REH-10c (second portal visit) scenarios.
