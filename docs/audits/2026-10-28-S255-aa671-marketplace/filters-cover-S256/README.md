# AA-671 Marketplace: filters + responsive cover photos (S256, 28/10/2026)

Built from AA-Partner `feat/aa-671-filters-cover` at `34b5e45` (rebased on `main` 2556d31; S255 commit `3c32ccb` +
S256 `34b5e45`), `next build` + `next start` locally, against a mock of the CIS API with the new pool fields
(`.tmp-session/S256/aa671/mock_api.py`: fabricated sample tours, generated SVG covers with distinct `size=small` /
`size=large` URLs labelled "600w" / "1600w" so the browser's `srcset` choice is visible; every 5th tour has no photo).
Captured by `.tmp-session/S256/aa671/shots.cjs` (Playwright). Desktop 1440x900 and phone 390x844, light and dark.

| File | What |
|---|---|
| 20-grid-covers-filters-* | All tours: the six filters (search, country, length, activity, intensity, recently added), cover on each card (placeholder for a tour without a photo), intensity chip, activity tags |
| 21-country-activity-* | Country Vietnam + Activity Culture & heritage (5 matches in the mock) |
| 22-intensity-recent-* | Intensity Challenging + Added in the last 30 days (2 matches in the mock) |
| 23-drawer-cover-* | Drawer: cover (eager, srcset), "Intensity: ..." chip, activities, rewrite CTA with the quota note |

Measured in the run (shots.out):

- 0 console errors, 0 page errors; `document.scrollWidth <= innerWidth` and `[data-pshell=main]` scrollWidth ==
  clientWidth in every state; no element past the right edge.
- Page 1: 20 photo covers + 4 placeholders; all 20 photo `<img>` carry `srcset` (600w, 1600w) and `sizes`;
  card covers `loading="lazy"`, drawer cover `loading="eager"`.
- Lazy: on the 390 px phone 8 covers loaded, 12 below the fold not fetched.
- Density: 1x desktop cards load the 600 px rendition (20/20); a 3x phone loads the 1600 px one (8/8 started).

Not covered here: real Dev data (needs the CIS deploy of `feat/aa-671-pool-fields`, then the portal deploy).
