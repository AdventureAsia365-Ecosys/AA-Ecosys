# AA-908 live check — traveller sign-in by email code (S250, 25/10/2026)

Target: <https://tripplanner.lumiguides.it.com> (Vercel production). It was checked after these changes were live:
TripPlanner #147 (assembly Lambda, git sha `90ea21f`) and #148 (BFF sign-in, merged 03:05Z), and Infra #360 and #374
(WAF, EXTERNAL callbacks, sign-up proof trigger).

**Verdict: not done.** Sign-up, sign-in, sign-out, the wrong-code error and restarting an abandoned sign-up all work
live. **My Trips and the guest-trip claim are broken.** The TripPlanner HTTP API (`aa-tripplanner-dev-api`) has no
route for `/me/*`, so `GET /me/trips` and `POST /me/claim` never reach the assembly Lambda.

**Update, re-check after Infra #381 (same day, 10:56–10:58 +07): steps 3 and 5 now PASS.** With the new
`ANY /me/{proxy+}` route the claim, My Trips, opening a trip from a second browser and the per-traveller isolation all
work live; there were no 5xx responses. See [Re-check after Infra #381](#re-check-after-infra-381).

## Method

- Playwright 1.x, one headless Chromium with a separate browser context per "device". Screenshots were taken at 1440 and
  390 px. The spec and its run logs are in the scratch folder `.tmp-session/s250/aa908-live/`, which is not committed.
- Addresses: `e2e-test-traveller@e2e-mail.lumiguides.it.com` (T1) and `e2e-test-traveller-2@…` (T2). The email codes
  were read from the E2E SES mailbox (`s3://aa-cis-dev-e2e-mail-<acc2>/inbound/`) with AA-CIS-App
  `tests/e2e/helpers/mailbox.ts` and its `recipient` parameter. No code was printed, logged or saved, and no screenshot
  was taken while a real code was in a field. The run output was also filtered for 6–8 digit numbers and JWTs.
- AWS was used read-only (`aa365-admin`): Cognito `list-users` on `aa-external-dev`, the SES receipt rule, API
  Gateway `get-routes`, and the assembly Lambda's CloudWatch logs.
- The `/api/auth/verify` answer was captured through a Playwright route pass-through, because the page navigates away
  on success. The body holds only `signed_in`, `claimed`, `resent`, `mode` and `error`.
- Runs:
  - Run 1 created T1. My Trips failed there, so the run was stopped before T2.
  - Run 3 was the full run (`results-main-run.json`).
  - A last short run finished T2 (`results-t2-finish.json`).

## Results

| # | Step | Result | Evidence |
|---|------|--------|----------|
| 0 | Signed out: `/api/me` and `/trips` | PASS | `/api/me` answered 401 `{"error":"sign_in_required"}`. `/api/auth/status` answered `{"signed_in":false,"available":true}`. `/trips` shows "Sign in to see your trips". `00-*` |
| 1 | Guest starts a trip (`/plan` → Heading to Vietnam → Find routes → Start with this route) | PASS | The first `POST /api/trip` (`apply_route`) answered 200. The trip read has 6 days. The cookie `__Host-tp_guest` is HttpOnly, Secure and SameSite=Lax. `01-*` |
| 2a | First sign-in of a **new** address (T1, run 1) = sign-up | PASS | One code was enough to sign in and land on `/trips`. `__Host-tp_auth` and `__Host-tp_refresh` are set (HttpOnly, Secure, Lax). Cognito user: CONFIRMED, `email` = T1, `email_verified` = true. `02a-*`, `02b-*` (email form and the empty code step) |
| 2b | Sign-in of the existing T1 (run 3, header link "Sign in" → `/sign-in`) | PASS | `start` answered 200 `{"step":"code"}`, then `verify` answered 200 `{"signed_in":true,"claimed":null}` with a single code. The page landed on `/trips`. The header link changes to "My trips". |
| 3 | Guest-trip claim and My Trips list | **FAIL** | `verify` returned `claimed: null` (the claim call failed). `GET /api/me` answered **502 `{"error":"upstream_error"}`** and `/trips` shows "Something went wrong — We could not load your trips". `03-*` |
| 4 | Sign out | PASS (BFF) / **UI gap** | `POST /api/auth/sign-out` answered 200. Afterwards `/api/me` answers 401 and `/api/auth/status` answers `signed_in:false`. `__Host-tp_auth` and `__Host-tp_refresh` are gone, and the localStorage trip ids are cleared. The sign-out button exists only in the loaded My Trips list, so with step 3 broken **there is no sign-out control in the UI**. The test called the same route that `signOut()` uses. `04-*` |
| 5 | Second sign-in on a fresh browser ("second device") lists and opens the trip | **FAIL** (blocked by 3) | Sign-in itself passes (one code, `signed_in:true`, status shows T1 with `email_verified:true`). My Trips answers 502 again, so nothing can be listed or opened. `05a-*` |
| 6 | Negative: wrong code | PASS | `verify` answered 400 `{"error":"code_invalid"}` and the form shows "That code is not right. Check the latest email and try again." `/api/me` answers 401 and no `__Host-tp_auth` is set (only `__Host-tp_signin` is kept). The real code still signed in after one wrong try (info). `06-*` |
| 7a | Case "SignUp sets email" | PASS | Both T1 and T2 are CONFIRMED in `aa-external-dev` with `email` set to the address and `email_verified` = true. No Infra change to the write attributes is needed. |
| 7b | Case "ConfirmSignUp returns a usable Session" | PASS | Both sign-ups (T1, and T2 after its restart) signed in with **one** code. No extra sign-in code was mailed. |
| 7c | Case "simulated-challenge fallback" (abandoned sign-up, then a restart) | Not reachable (no defect) | When T2 restarted, Cognito mailed a new code within 60 s. So `InitiateAuth` answered `UserNotConfirmedException`, which leads to `ResendConfirmationCode`, and no simulated challenge occurred. The fallback stays an unused safety net. Restarting in a fresh browser and entering the newest code finished the sign-up (step 8, PASS). |
| 7d | Case "stale sign-up Session retry" (code entered more than 3 min after it was requested) | **Inconclusive** | The test entered the restart's (newer) code in the *first* browser, whose pending step still held the original SignUp Session, at 221 s. It got 400 `code_invalid` (`CodeMismatchException`, which is not retried by design). This mixed two effects: the newer code and the stale Session. The pure case (the original code, no restart, more than 3 min) was not run, and no fresh address is left to run it (see below). |
| 8 | T2 restart finishes, T2 cannot read T1's trip, T2 signs out | PASS | One code was enough to sign in. Reading T1's trip id as T2 returns the empty trip (the Lambda's 404 is mapped to 200 with 0 days). Sign-out is clean. `08a-*`, `08b-*`, `08c-*` |
| — | Console / 5xx | FAIL | The only 5xx responses are the `/api/me` 502s from step 3. The 400 and 401 responses are the expected negatives. |

## Root cause of steps 3 and 5

The routes of `aa-tripplanner-dev-api` are `ANY /browse/{proxy+}`, `ANY /trip/{proxy+}`, `GET /browse/search` and
`POST /trip/{trip_id}/narrate`. There is **no `/me/*` route**:

- `curl https://<api-id>.execute-api.us-west-1.amazonaws.com/me/trips` answers 404 `{"message":"Not Found"}`. On the
  same API, `/trip/x` answers 401, which shows the Lambda is reached on that route.
- The assembly Lambda's logs for the test window contain no `me_trips` or `me_claim` request. Every request that
  reached it was `get_trip`, `apply_route`, `coverage` or `suggestions`.
- The BFF maps the non-401 upstream answer to 502 `upstream_error` (`app/api/me/route.ts`). The claim in
  `/api/auth/verify` is best effort, so it fails silently (`claimed: null`).

**Fix (AA-CIS-Infra, `accounts/aa365/tripplanner.tf`):** add a route on the assembly integration, for example:

```hcl
resource "aws_apigatewayv2_route" "tripplanner_me" {
  api_id    = aws_apigatewayv2_api.tripplanner.id
  route_key = "ANY /me/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.tripplanner_assembly.id}"
}
```

The Lambda permission already allows `${execution_arn}/*/*`, so no IAM change is needed. The stage default throttle
applies. After the apply, re-run steps 3 and 5 (claim, list, open from a second browser), then the send-with-account
check from the #148 test plan.

## Re-check after Infra #381

Infra #381 added `ANY /me/{proxy+}` on `aa-tripplanner-dev-api`, targeting the assembly integration. Read-only checks
first: `get-routes` now lists `ANY /me/{proxy+}`, and an unauthenticated `GET /me/trips` on the execute-api URL answers
401 `{"error": "unauthorized"}` (it was 404 before), so the Lambda is reached.

Method: the same helpers as the first run, in a new spec `recheck.spec.ts` (scratch folder, not committed). One headless
Chromium with three browser contexts: A (guest → T1), B (T1 on a "second device"), D (T2). The wrong-code and T2
sign-up cases were not repeated, because nothing in them depends on `/me/*`. Codes were handled as before: never printed,
saved or shown in a screenshot. The output was filtered for 6–8 digit numbers and JWTs. Raw results:
`results-recheck-381.json`.

| # | Step | Result | Evidence |
|---|------|--------|----------|
| R1 | Guest starts a trip on `/plan` (Heading to Vietnam → Find routes → Start with this route) | PASS | `POST /api/trip` answered 200. Trip `537cdedf-…` has 6 days. Only `__Host-tp_guest` is set. `r01-*` |
| R2 | T1 signs in from the header link (`/sign-in`, one email code) | PASS | `start` answered 200 `{"step":"code"}`. `verify` answered 200 **`{"signed_in":true,"claimed":1}`**. The page landed on `/trips`. `/api/auth/status` right after sign-in: `signed_in:true`, T1, **`email_verified:true`**. |
| R3 | Guest-trip claim and My Trips list | **PASS** | `GET /api/me` answered 200 with T1, `email_verified:true` and 1 trip: `537cdedf-…`, `draft`, 6 days. `/trips` shows the list (Draft · "Nam Ou Dam · 100 Waterfalls · Muang Ngoi village …" · 6 days · 6 stops), with "Sign out" visible and the header link "My trips". `r03-*` |
| R3c | Open the claimed trip from My Trips | PASS | "Open" loaded `/plan`. `GET /api/trip?trip_id=537cdedf-…` answered 200 with 6 days. `r03c-*` |
| R4 | Sign out **from the UI** (My Trips "Sign out" button) | PASS | The button now exists because the list loads. `POST /api/auth/sign-out` answered 200 and the page landed on `/`. `/api/me` answers 401 and `/api/auth/status` answers `signed_in:false`. `__Host-tp_auth` and `__Host-tp_refresh` are gone, and the localStorage trip ids are cleared. `r04-*` |
| R5 | Second sign-in on a fresh browser lists the same trips and opens the claimed one | **PASS** | One code; `verify` answered `claimed:0` (no guest trips in that browser) and status showed `email_verified:true`. `/api/me` answered 200 with the same trip ids as the first session (1 trip). "Open" loaded the trip (200, 6 days). Sign-out from the button was clean. `r05a-*`, `r05b-*` |
| R6 | T2 signs in and sees none of T1's trips | PASS | One code; `claimed:0` and `email_verified:true`. `/api/me` answered 200 with T2 and **0 trips** (no overlap with T1's ids). `/trips` shows "No trips yet". Reading T1's trip id as T2 returns the empty trip (200, 0 days, as in step 8). Sign-out from the button was clean. `r06-*` |
| — | Console / 5xx | PASS | There were no console errors and no 5xx responses in the whole run. |

Assembly Lambda logs for the run (`/aws/lambda/aa-tripplanner-dev-assembly`) now show the `/me/*` traffic:
`me_claim` 200 with `claimed: 1` (A), `me_claim` 200 with `claimed: 0` (B, D), and `me_trips` 200 with `trips: 1`. The two
`me_trips` 401 lines are the unauthenticated execute-api probes above.

Notes:

- T1's list holds only the trip from this run. The guest trips from the first runs (`28b56b85-…`, `afe610f4-…`,
  `b8623c0e-…`) were never claimed: their claim failed then, and their browser contexts (the guest cookies) are gone.
  This is expected, not a defect.
- `email_verified` was `true` right after every sign-in in this run (T1 twice, T2 once). These were all sign-ins of
  confirmed accounts. The open point in "Other findings" 2 (`false` in the **first session right after a sign-up**)
  could not be re-tested, because no unconfirmed E2E address is left (see finding 3).
- Finding 1 (no sign-out control when My Trips fails to load) still holds as a design gap. It no longer shows up in the
  normal flow, because the list now loads.
- Still not run: Send to an advisor with the account email (Booking v1.4 `verified=true`), from the #148 test plan.

## Other findings

1. **No sign-out control when My Trips fails to load.** `signOut()` is called only from the loaded list
   (`components/MyTrips.tsx`). Neither the error state nor the header offers it. Suggested change: a sign-out link in
   the error state and/or the header menu (TripPlanner).
2. **`email_verified:false` in the first session after a sign-up.** After T2's sign-up, `/api/auth/status` showed
   `email_verified:false`. Cognito has `email_verified=true` for the user, and T1's later sign-ins show `true`. The
   BFF reads the claim from the access token issued by the auto sign-in right after `ConfirmSignUp`.
   - Consequence: a send made in that first session would go to Booking v1.4 with `verified=false` until the token
     refreshes (at most about 1 h) or the traveller signs in again.
   - Worth checking which claim source the EXTERNAL pre-token trigger uses at auto sign-in (Infra
     `lambda_src/identity_triggers/external.py`).
3. **Stale-Session case cannot be re-run with the current addresses.** T1 and T2 are both CONFIRMED now. A clean run of
   the pure case needs either a third E2E traveller address in the SES rule `e2e-cognito` (for example
   `e2e-test-traveller-3@…`) or deleting T2 from `aa-external-dev` first. Both are write actions and were not done here.
4. Not run (outside this task or a write action): Send to an advisor with the read-only account email (Booking v1.4
   `verified=true`), and the direct public-API `SignUp` with a password and no proof (extra case 3 in the notes).

## Test data left on Dev

- Cognito `aa-external-dev`: T1 (created 25/10 10:36 +07) and T2 (created 10:45 +07), both CONFIRMED.
- TripPlanner guest sessions and trips: `28b56b85-…`, `afe610f4-…`, `b8623c0e-…`. All are unclaimed drafts, never
  sent.
- From the re-check: trip `537cdedf-…`, claimed by T1 (draft, never sent).
- E2E mailbox: the code mails expire under the bucket lifecycle (1 day).
