# S239: live re-verify of TripPlanner #88 (AA-819) and CIS #758 (AA-831)

Date: 2026-10-16. Agent: Claude Code. Playwright (Chromium) against Dev production URLs. Read-only:
no API writes, no LLM calls. The tenant key was read from Secrets Manager at run time
(`aa-cis/dev/e2e-tenant/terra-family`, profile aa365-admin). It was not printed or saved.

What is deployed (GitHub Production deployments):
- TripPlanner `fb0653a5` (#88), deployed 2026-10-16T02:24Z. This is the head of `main`.
- CIS frontend `802b5920` (#758), deployed 2026-10-16T02:26Z. This is the head of `main`.

Files in this folder:
- Scripts: `tp.mjs`, `cis.mjs`.
- Raw measurements: `tp_out.json`, `cis_out.json`.
- Screenshots: `aa819-*.png` and `aa831-*.png`.

## AA-819: the AI label popover stays inside the viewport (TripPlanner #88): PASS

Page: `/tours/delhi-agra-jaipur-three-capitals-in-2-days-india-a4966d23`.

Method:
- Each label was opened, measured and screenshotted, then closed again: the header pill, summary,
  Highlights and Day by day.
- At 390 px the labels were opened by touch tap; at 1440 px by mouse click.
- Assertions:
  - The explanation panel is visible.
  - Its right edge is at most `innerWidth - 4` and its left edge is at least 0.
  - `document.documentElement` and `main` both have scrollWidth ≤ clientWidth.
  - The label closes again (`aria-expanded=false`).

| Run | header pill right | summary right | Highlights right (shift) | Day by day right (shift) | doc / main scroll | Result |
|---|---|---|---|---|---|---|
| 390x844 light | 332 / 386 | 272 / 386 | 382 / 386 (−17.8 px) | 382 / 386 (−25.8 px) | 390/390, 390/390 | PASS |
| 390x844 dark | 332 / 386 | 272 / 386 | 382 / 386 (−17.8 px) | 382 / 386 (−25.8 px) | 390/390, 390/390 | PASS |
| 1440x900 light | 476 / 1436 | 416 / 1436 | 544 / 1436 (none) | 552 / 1436 (none) | 1440/1440, 1152/1152 | PASS |
| 1440x900 dark | 476 / 1436 | 416 / 1436 | 544 / 1436 (none) | 552 / 1436 (none) | 1440/1440, 1152/1152 | PASS |

Notes on the table:
- Before #88, Highlights and Day by day ran to 400–408 px on a 390 px screen.
- They are now shifted left with `translateX` and end at 382 px, which is `innerWidth - 8` as designed.
- At 1440 px no shift is applied because none is needed.
- All runs had 0 console errors and 0 HTTP errors ≥ 400. The theme was confirmed through `data-theme`.

Site pill copy: in all 4 runs the header pill explanation does not contain "AI-assisted". It now
reads: "…Trip narration carries its own Adventure Asia AI label, which says how much of it AI
wrote…" (full text in `tp_out.json` under `site_pill`).

Screenshots: `aa819-tour-{390-light,390-dark,1440-light,1440-dark}-{header-pill,summary,highlights,day-by-day}-open.png`.

## AA-831: the portal breadcrumb ends in an ellipsis (CIS #758): PASS

Flow:
1. Log in as tenant terra-family at `/tenant-login`.
2. Open the page directly.
3. At 390 px, wait for the mobile shell (the "Open menu" hamburger) before measuring.

| Run | Title text | text-overflow | title scroll / client | Truncated | Crumb right / next control | doc / main scroll | Result |
|---|---|---|---|---|---|---|---|
| /portal/help/facebook 390 light | Connect your Facebook Page | ellipsis | 181 / 169 | yes | 318 / 338 | 390/390, 390/390 | PASS |
| /portal/help/facebook 390 "dark" | Connect your Facebook Page | ellipsis | 181 / 169 | yes | 318 / 338 | 390/390, 390/390 | PASS (renders light, see below) |
| /portal/billing 390 light | Billing | ellipsis | 36 / 36 | no | 185 / 338 | 390/390, 390/390 | PASS (unchanged) |
| /portal/billing 1440 light | Billing | ellipsis | 36 / 36 | no | 391 / 1372 | 1440/1440, 1204/1204 | PASS (unchanged) |
| /portal/help/facebook 1440 light | Connect your Facebook Page | ellipsis | 181 / 181 | no | 536 / 1372 | 1440/1440, 1204/1204 | PASS (full title) |

What the measurements show:
- The full title is kept in `title=` ("Connect your Facebook Page").
- In every run the crumb ends before the next header control, so nothing overlaps.
- Every run had 0 console errors and 0 API errors.
- Short titles such as "Billing" are not cut off. The `text-overflow: ellipsis` rule only shows when the text is too long.

Dark mode: the tenant portal is light by design. `portal/layout.tsx` wraps the portal in
`data-theme="light"`, under "AA-601 part B: the tenant portal stays LIGHT". With OS dark and
`cis_theme=dark`, the page still renders light (`aa831-help-facebook-390-dark.png`). This means:
- AA-831's "light and dark" screenshot requirement cannot apply to the portal until the portal redesign.
- The S239 audit note "the portal supports dark mode" is inaccurate.

Screenshots: `aa831-{help-facebook-390-light,help-facebook-390-dark,billing-390-light,billing-1440-light,help-facebook-1440-light}.png`.
Each one also has a `-topbar.png` crop.
