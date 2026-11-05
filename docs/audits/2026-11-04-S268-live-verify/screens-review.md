# S268 live verify: screenshot review

Evidence pass over CI screenshots only (no new browser session). Every image in `screens/` was opened and checked.
Sources:

- CIS admin: AA-CIS-App `Vercel Deploy` run 41869320584 on `main` @ `e86bd3c0` (R2 slice 2: view as partner,
  Assignments page). Job "UI smoke, signed in (Cognito E2E user)": 105 passed, 11 skipped. The E2E staff user
  signed in with role **content** (log line `[smoke] signed in (cognito) with staff role: content`).
- Content studio: AA-Partner `Deploy Web Dev` run 41869630655 on `main` @ `bda36d1` (studio EN/VI, after #214
  "from" price). Job "Studio UI smoke": 63 passed, 1 failed (stale AA-761 Activity test that still waits for the
  removed "Signed in with your API key" row; #213 dropped API-key sign-in). The deploy and post-deploy verify passed.

Public-repo check: the images show only the synthetic tenant "Atlas & Hearth", the staff display names
"E2E Cognito" / "Content", and published tour content. No e-mail address, token, secret or account ID. Nothing was
skipped for that reason.

## CIS admin

### What was captured and what was not

| Page asked for | Result |
|---|---|
| AI gateway, Route control (`/admin/ai-gateway?tab=controls`) | Captured **desktop light only**, as a refused page: the content role is sent to Review Queue. File: `cis-ai-gateway-controls-desktop-light-redirected.png`. |
| AI gateway, Trace tab (`/admin/ai-gateway?tab=trace`) | **Missing.** Not in the smoke page list. The nearest page in the matrix is Content Trace (`/admin/tenant-qa/trace`), also refused for the content role; captured as `cis-tenant-qa-trace-desktop-light-redirected.png`. |
| Tenants, Assignments (`/admin/tenants/assignments`) | **Missing.** Route is built (in the Next.js route list of this deploy) but not in the smoke page matrix, so no shot. |
| View as partner (`/admin/tenants/view-as`) | **Missing.** Route is built, not in the smoke page matrix. |
| AI & spend, Usage explorer (`/admin/usage`) | **Missing.** No `/admin/usage` route in this build (not deployed yet on `e86bd3c0`). |

The smoke only takes desktop-light shots of refused pages, so there is no mobile or dark capture of any of these.
The admin-only pages cannot be proven with this E2E user; a live check needs an admin or ai_ops session.

### cis-ai-gateway-controls-desktop-light-redirected.png

- Viewports: desktop 1440, light.
- State: the redirect target (Review Queue) is in its loading state: skeleton rows, "0 Pending" counter.
- Sidebar shows only the AA catalogue group (Upload, Rewrite, Review Queue, Master Content, Facts, Supply copy,
  AA content, Settings) plus Apps; no AI gateway entry, so the page is correctly hidden from this role.
- Real data: none yet (still loading). No internal info beyond what a content staff user may see.
- Defects: none for the redirect itself. The capture proves the guard, not the Route control page.

### cis-tenant-qa-trace-desktop-light-redirected.png

- Viewports: desktop 1440, light.
- State: same Review Queue loading skeleton.
- Defect (low): the sidebar is **empty** (no nav group at all, only Apps), while the controls shot above shows the
  AA catalogue group, and the user chip reads "Content" instead of "E2E Cognito". Most likely captured before the
  nav and profile finished loading; worth a look if it repeats (the nav should not render empty).

## Content studio (AA-Partner web, portal host)

### Marketplace, All tours: studio-marketplace-{desktop,mobile}-{light,dark}.png

- Viewports: desktop 1440 (full page) and mobile 390, light and dark.
- State: loaded with real data: "892 tours available · newest first", page 1 of 38, 24 cards; filters (country,
  length, activity, intensity, added) and "All tours · 892 / In my catalog · 9" tabs. "IN MY TOURS" chips on 3 cards.
- 390 px: header, tabs and filters wrap cleanly; the first card fills the width; bottom nav (Dashboard, Tours,
  Create, Content, More) is present; no horizontal overflow seen.
- Dark mode: correct tokens on cards, chips, filters and pager; text readable.
- Internal info: none visible to the tenant.
- Defects:
  1. **No "From US$X per person" price on any card.** The feature from #214 (AA-1029) shows the price only when
     the pool row has a `from_price` and shows nothing otherwise, so none of the 24 cards on page 1 has a from price
     yet. The price rendering cannot be proven from these shots (data gap, or the field is not reaching the pool).
  2. **Tour drawer not captured.** The test "Marketplace card opens the detail drawer" passed, but it saves no
     screenshot, so there is no image of the drawer or its price line.
  3. Content (low): 17 of 24 page-1 cards (almost all India tours) have no cover photo, only the placeholder icon.
     Some covers look generic for the tour (for example the Colombo Buddha statues photo on "Galle City and
     Countryside Cycling Tour"). Photo coverage, not a UI bug.

### Marketplace, In my catalog: studio-marketplace-in-my-catalog-{desktop,mobile}-{light,dark}.png

- Viewports: desktop 1440 and mobile 390, light and dark.
- State: loaded, 9 tours; KPIs "Tours in your catalog 9", "Posts planned / week 3"; each card shows country, length,
  title, PRICE (for example "$1,225 estimated", "$48 estimated" or "On request"), version chip (V1/V2/V4) and READY.
- 390 px: KPIs stack, cards are full width, no overflow. Dark mode correct; the V1 chip is a little low-contrast in
  dark mode but readable.
- Internal info: none. The version chip is a tenant-facing label.
- Defects: this tab shows the tenant's own estimated price ("$X estimated"), not AA's "From US$X per person", which
  is expected for this view. No defect.

### Marketplace, empty search: studio-marketplace-no-results-desktop-light.png, studio-marketplace-no-results-mobile-dark.png

- Viewports: desktop 1440 light, mobile 390 dark.
- State: designed empty state: "0 tours match", "No tours found / Try another search or fewer filters", two
  "Clear filters" actions.
- 390 px and dark mode: correct, no overflow.
- Internal info: the search box holds the test query `zzqx-no-such-tour-aa760` typed by the smoke test (not UI
  text).
- Defects: none.

### Vietnamese

**No page was captured in Vietnamese.** `bda36d1` ships the studio in English and Vietnamese, but no smoke test
switches the locale, so every studio image is in English. A VI capture needs a new smoke case (or a manual check).

## Defects summary

1. Marketplace cards show no "From US$X per person" price on page 1 (no `from_price` on these pool rows, or not
   reaching the studio); the drawer price is not captured at all.
2. Studio smoke has one stale test (AA-761 Activity waits for the removed API-key sign-in row), so `Deploy Web Dev`
   ends red although the deploy and verify passed.
3. No studio capture in Vietnamese; no smoke case for the VI locale.
4. CIS: AI gateway Route control / Trace, Tenants > Assignments, View as partner cannot be captured with the content
   E2E user; Assignments and View as partner are not in the smoke page matrix; `/admin/usage` does not exist on
   `e86bd3c0`.
5. CIS (low): one refused-page capture shows an empty sidebar and a different user label; probably captured
   mid-load.
6. Content (low): many India tours on Marketplace page 1 have no cover photo.
