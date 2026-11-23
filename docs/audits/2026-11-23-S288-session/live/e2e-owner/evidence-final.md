# E2E owner live run on Dev: final checks (group size bands, sale exception, CIS view-as banner) (AA-1176, S288)

- When: 2026-11-23, 15:30–15:38 UTC. Run by an agent signed in as the Dev-only E2E owner
  `e2e-owner@e2e-mail.lumiguides.it.com` (root ADR 0006a A10h). This was the only browser lane running.
- Follows `evidence.md` (the earlier run today, findings F1–F3). Same sign-in path: Cognito managed login with an
  e-mail code read from the S3 prefix `inbound-admin/` with the MFA admin profile. The code was never printed, logged or
  screenshotted. No screenshot was taken on the sign-in host. Booking reused the CIS company sign-in (no new code).
- Masking: before each screenshot, every `@adventure.asia` address except `info@` was masked in the page. None of the
- API results in the table were read by the run's browser driver and are recorded here as prose; no raw responses were saved. Screenshots back only what each row names.
  pages shot here shows such an address or a staff row.
- Screenshots: 1440x900, light, PNG, compressed with `tools/docs/compress_images.py` (all ≤ 53 KiB).

## Steps

| # | Time (UTC) | Step | Result | Evidence |
|---|---|---|---|---|
| 0 | 15:30 | Sign in to CIS | **done** | `GET /api/admin/session` 200: `role admin`, `read_only false` |
| A | 15:31 | Booking › Pricing policy › "Group size bands" (AA-1175), read only | **done** | `GET /api/booking/staff/me` 200 (`role admin`, `view_as null`). `GET /api/booking/pricing/policy` 200. Parameter `price_pax_bands`, section Prices, approver group `pricing` (Pricing lead), no open change. Value in force: **1, 2, 3, 4, 5–7, 8–10, 11+ travellers**, "v2 · since 2026-11-23", badge "In use". History: v2 In force since 2026-11-23 ("The business owner's group-size bands (2, 4, 5-7, 8-10 per person, double occupancy), with 3 on its own and an open 11+ top band", made by Migration seed, approved by tech lead S288); v1 Superseded since 2026-01-01 (1, 2, 3–4, 5–6, 7–10, 11+; "the code constant PAX_BANDS"). Second approver: the page intro says "A change is a new version that takes effect only after a second person approves it", and the row names the approver group Pricing lead. Nothing was edited (Change was not pressed). `final-1-pricing-policy-group-size-bands.png`, `final-2-pricing-policy-group-size-bands-history.png` |
| B | 15:32 | Sale exception on a synthetic tour (AA-1149) | **skipped: no synthetic tour on Dev** | `GET /api/booking/catalog/price-readiness` 200: 892 trip plans (844 served, 48 paused, all `blocked` under "Can operate"; 2 priced, 890 no components). No title starts with "SYNTHETIC" and no row carries a synthetic or E2E marker (the response has no such field). Searches `q=SYNTHETIC`, `q=synthetic`, `q=test` return 0 rows; `q=E2E` returns 5 real catalogue tours whose UUID key happens to contain "e2e". The 2 priced tours are real catalogue tours (Philippines, Japan), so they were not used. This matches `live/aa-1149/evidence.md`: the synthetic tour of plan step 2 has not been created yet. No exception was saved. Note for later: the drawer's Revoke sends a fixed reason "Revoked by the administrator" (no free-text reason), default length 14 days, maximum 30 (from `GET …/operability`). `final-5-price-readiness-no-synthetic-tour.png` |
| C0 | 15:30–15:36 | Wait for AA-CIS-App #1651 (fix of F1) on the admin web | **done** | #1651 `MERGED`, merge `f4aab0c4d67d…`. 15:30: admin service PRIMARY `aa-cis-dev-admin:89` (image `dev-b8d040cb…`). 15:33: PRIMARY `:90` `IN_PROGRESS`, image `dev-f4aab0c4d67d…`. 15:36:41: PRIMARY `:90` seen **COMPLETED** (ECS `updatedAt` 15:35:19 UTC; re-checked after the run: still PRIMARY, image `dev-f4aab0c4d67d…`), image tag `dev-f4aab0c4…` (identical to the merge commit) |
| C | 15:36 | CIS › Platform › Roles & permissions › View as "Content" | **done: F1 fixed** | Modal defaults 30 min, reason "Check what this role sees" → Start view. `POST /api/view-as/roles` 201. Landed on `/admin/my-work`. **Banner shows**: "Viewing as Content · Read only: nothing can be changed. Data that depends on your own assignments may be empty. · Ends in 29:56 · Back". **Sidebar filtered**: Home shows only My work; Tenants, AA catalogue, Tenant content QA, Writing lab, Platform, Apps remain; Overview, App health, Reports, Data coverage, AI & spend and Trade are gone (AI & spend and Trade are back after Back in `final-4`; the Home items sit in the collapsed Home group there). `GET /api/view-as/roles` 200 `active true`, `view_role custom_content`, `read_only true`, expires 16:06:56. `GET /api/admin/session` 200 `role custom_content`, `read_only true`, `reason view_as`. A write to a probe path (`POST /api/admin/s288-view-as-probe`, not a real endpoint) was refused by the view-as guard before routing → **403 `view_as_read_only`**. Display cookie `cis_view` in `document.cookie` starts **`%7B`** (single-encoded; the earlier run saw `%257B`). `final-3-cis-view-as-content-banner.png` |
| C-back | 15:37 | Press the banner's **Back** button | **done** | The click sent `DELETE /api/view-as/roles` 200 and landed on `/admin/platform/roles`. No banner, `cis_view` cookie gone, `GET /api/view-as/roles` 200 `{"active":false}`, `/api/admin/session` `role admin`, `read_only false`. The full sidebar is back (Platform › Staff & access … Docs). `final-4-cis-view-as-back.png` |
| D | 15:37–15:38 | Sign out of both apps | **done (CIS needed a second pass)** | Booking: account menu → Sign out → `/login`; `GET /api/booking/staff/me` **401**. CIS, first pass: the driver looked for the account button by the user's name, but its accessible name is "Account menu", so it found no sign-out control and `/api/admin/session` was still 200. The browser state file was then deleted too early, before a UI sign-out. Second pass: signed in to CIS again (new code, same rules), account menu → **Sign out** → `POST /api/auth/admin-logout` 200 → `/login`; `GET /api/admin/session` **401**, Booking `staff/me` **401**. Browser state file deleted at the end. |

## Findings

- **F1 fixed (AA-1157 CIS, #1651).** The display cookie is now single-encoded (`%7B…`), the banner with role, minutes
  left and Back shows, the sidebar lists only Content's sections, and Back ends the view through the UI. The server
  side holds as before (403 `view_as_read_only`).
- **Step B could not run on Dev**: no synthetic tour exists in Price readiness. The sale exception stays unchecked live
  until the AA-1149 plan step 2 synthetic tour is created.
- **Run note (no product defect):** the first CIS session of this run (signed in at 15:30) was not ended by a UI sign-out.
  Its cookies were dropped with the deleted browser state, so nothing local can use it. Its refresh token was not
  revoked and lapses at its normal expiry. The second session was revoked properly by Sign out.

## Writes on Dev made by this run

- One CIS view-as session (role `custom_content`, 15:36:56, started and ended by the banner's Back at 15:37).
- One refused write probe (`POST /api/admin/s288-view-as-probe` → 403, nothing changed).
- Two CIS sign-ins and one CIS sign-out (revoke), one Booking sign-in (reused) and its sign-out.
- No pricing policy change, no sale exception, no staff, tenant or invitation change.
