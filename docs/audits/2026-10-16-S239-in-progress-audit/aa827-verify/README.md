# AA-827 live verification on Dev: guest owner flows and replay

- **Where:** https://tripplanner.lumiguides.it.com. TripPlanner `main` @ `7150c00` (PR #85: HttpOnly guest cookie, guard and owner check on every trip mutation).
- **When:** 2026-10-16, 01:16:42–01:17:39 UTC.
- **How:** Playwright Chromium (headless), with three fresh browser contexts: A (1440x900 light), B (1440x900 light) and C (390x844 light, mobile). Script: `.tmp-session/s239/aa827_verify.mjs`. Raw output: `.tmp-session/s239/aa827_verify_out.json`.
- **Scope:** VERIFY ON DEV item (c), browser part, from `.tmp-session/s239/aa827_design.md`. The DB checks are not covered here: the 32-byte hash and NULL `guest_token` on A's row, and the `tripplanner.outbox` row with Booking ingest. Neither are the log checks of item (d). They need ECS exec and Logs Insights.
- **Secret handling:** the cookie value was never printed or saved. The script holds it in memory only to check where it could leak, and records only its attributes and length.
- **Cost:** one narrate call. It returned the AA master text (`AA itinerary` badge, as in the AA-819 run), so this run probably made no LLM call.

## Context A ids (the owner)

| Field | Value |
|---|---|
| session_id | `63173af2-3102-43ea-a8a0-3692b7c51b63` |
| trip_id | `d55186f1-e346-42e5-9493-a5f97b914c0d` |

## Steps and status codes

### Context A: owner flow
The page opened `/plan?tour=78c5f4b7-5648-40ca-8d01-2474d785148a&source=a4966d23-3e6c-468e-84fb-558d284a9c3c`. The tour prefill pins the tour's 2 stops (Fatehpur Sikri, Amber Fort) through `apply_route`.

| # | Call | Status | Notes |
|---|---|---|---|
| 1 | GET `/api/trip?trip_id=…` | 200 | restore (empty trip) |
| 2 | POST `apply_route` | **200** | 2 stops pinned, 2 days |
| 3 | GET suggestions / coverage | 200 / 200 | |
| 4 | POST `add_day` (+ free day) | **200** | |
| 5 | POST `remove_day` | **200** | custom_days back to 0 |
| 6 | POST `narrate` (Compose, once) | **200** | the second-call guard never fired |
| 7 | POST `send` | 422 `registration_required` | expected: this opens the registration form |
| 8 | POST `send` (name `AA827 Verify`, email `nghieppham+aa827@adventure.asia`, consent ticked) | **200** | UI: "Sent to an advisor. They'll be in touch shortly." |
| 9 | GET `/api/trip?trip_id=…` | 200 | final state: 2 days, 0 custom days |

Every A mutation returned 2xx, apart from the 422 the registration flow is designed to return.

### Context B: replay of A's ids
Before the first load, an init script seeded `aa-tripplanner:ids` = A's {sessionId, tripId}. It did this once per tab, so the reset reload is not re-seeded. B has its own cookie, minted by the middleware when `/plan` loaded.

| # | Call | Status | Notes |
|---|---|---|---|
| 1 | GET trip / coverage / suggestions on A's trip_id | 200 | GETs are ungated, so B can see A's 2-day trip. This is a known residual (design FLAGS). |
| 2 | UI mutation: POST `add_day` with A's ids | **401** | the UI reset its ids and reloaded with the notice "This trip belongs to another browser — starting a new trip." It now has a new empty trip. |
| 3 | GET on the new trip | 200 | new ids: session `d4979389-312f-4bd1-8a16-84787bddd948`, trip `93a880a0-e2be-44ac-ad9c-84026d0a02b9` |
| 4 | direct POST `add` (A's trip_id, B's new session_id, A's component) | **403** `forbidden` | "this trip belongs to another session" |
| 5 | direct POST `narrate` (same) | **403** `forbidden` | refused before any LLM call |
| 6 | direct POST `send` (same) | **403** `forbidden` | |
| 7 | direct POST `add` (A's trip_id **and** A's session_id, with B's cookie) | **401** `guest_session_invalid` | |

The response body for B row 2 could not be read because the page reloaded. The client resets only on a 401 `guest_session_invalid` or a 403 `forbidden`, and the reset notice appeared, so this was the `guest_session_invalid` branch. Row 7 shows the same 401 body directly.

### Context C: the reset notice at 390
Same seeding as B, at 390x844. The UI `add_day` returned 401, the ids were reset to a new trip (`c71ff5bd-…`), and the notice appeared (screenshot 12).

## Cookie and storage (context A, after all flows)

| Check | Result |
|---|---|
| Cookie name | `__Host-tp_guest` (the only cookie on the origin) |
| HttpOnly / Secure / SameSite / Path | true / true / Lax / `/` |
| Domain | host-only `tripplanner.lumiguides.it.com` (no Domain attribute, as `__Host-` requires) |
| Expiry | 400 days (Max-Age=34560000), sliding: re-sent on every `/plan` and `/api/trip` response |
| Value | length 43, base64url format; same value from first load to the end |
| Set-Cookie attributes seen | `Path=/; Max-Age=34560000; HttpOnly; SameSite=Lax; Secure` on every matched response |
| `document.cookie` | empty: no `tp_guest`, token absent |
| localStorage | `aa-tripplanner:ids` = exactly {sessionId, tripId}, plus 2 Mapbox telemetry keys; token absent |
| sessionStorage | token absent |
| `x-middleware-set-cookie` response header | absent on every response in A, B and C |
| Token in any response header or `/api/trip` body | absent (A and B, each checked against its own token) |
| B's cookie | its own token (length 43, different from A's), same attributes, absent from `document.cookie` |

## Verdict

| Item | Verdict |
|---|---|
| Owner flows: pin (apply-route), add and remove a day, narrate, send through the 422 registration form, all 2xx | **PASS** |
| `__Host-tp_guest` is HttpOnly, Secure, Lax, Path=/ | **PASS** |
| The cookie is absent from `document.cookie`, and localStorage holds only {sessionId, tripId} | **PASS** (the 2 Mapbox telemetry keys are unrelated) |
| No `x-middleware-set-cookie` header, and the token is never echoed | **PASS** |
| Replayed ids (B's token, A's session): mutation refused with 401 `guest_session_invalid`, the UI shows the notice and starts a new trip | **PASS** (1440 and 390) |
| B's session on A's trip: 403 `forbidden` on add, narrate and send | **PASS** |
| Narration AI badge shown | **N/A for this run**: the narration came from the AA master text, so the block shows `AA itinerary`. The header still shows `AI-assisted`. This is the same narrate behaviour AA-819 recorded, so it does not affect AA-827. |
| DB row hashed, outbox row and Booking ingest, legacy-guest grace, log checks | **Not tested here** (needs ECS exec and Logs Insights) |

## Defects
None found for AA-827.

Observations outside AA-827:
1. The GET reads are still ungated, so a second browser holding A's trip_id can read A's itinerary (B row 1). The design FLAGS already list this as a known residual, to be handled in a follow-up.
2. The narration for this trip has a Day 2 text, "Khimsar to Jaisalmer…", that does not match its second stop, Amber Fort. This is the narration content issue already under separate investigation (narration D1 bug), not AA-827.

## Screenshots

| File | What |
|---|---|
| `01-A-plan-1440-light-pinned.png` | A after the prefill apply-route (2 stops) |
| `02-A-plan-1440-light-day-added.png` | A with the free day added |
| `03-A-narration-block-1440.png` | narration block, 1440 |
| `04-A-registration-form-1440.png` | registration form after the 422 |
| `05-A-registration-success-1440-light.png` | sent-to-advisor success, 1440 |
| `06-A-plan-1440-light-after-flows.png` | planner after all flows, 1440 |
| `07-A-plan-390-light-after-flows.png` | planner after all flows, 390 |
| `08-A-narration-block-390.png` | narration block, 390 |
| `09-A-registration-success-390-light.png` | success state, 390 |
| `10-B-plan-1440-replayed-ids-before-mutation.png` | B with A's ids, before the mutation (ungated GET shows A's trip) |
| `11-B-reset-notice-1440-light.png` | B's reset notice and new empty trip, 1440 |
| `12-B-reset-notice-390-light.png` | reset notice, 390 (context C) |
