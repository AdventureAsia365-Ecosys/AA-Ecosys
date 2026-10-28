# AA-671 follow-up: Marketplace activity / intensity / recently-added filters and cover photos (S255, 28/10/2026)

Built from AA-Partner branch `feat/aa-671-filters-cover`, `next build` + `next start` locally, against a mock of the
CIS API with the new pool fields (`.tmp-session/S255/aa671-facets/mock_api.py`: fabricated sample tours, generated SVG
covers, every 5th tour without a photo). Captured by `.tmp-session/S255/aa671-facets/shots.cjs` (Playwright).
Desktop 1440x900 and phone 390x844, light and dark.

| File | What |
|---|---|
| 10-grid-covers-* | All tours: cover on each card (placeholder for a tour without a photo), intensity chip, activity tags, the three new filters |
| 11-selected-over-cover-* | A selected card: the select box over the cover, bulk bar |
| 12-drawer-cover-* | Drawer: large cover, "Intensity: ..." chip, activities |
| 13-activity-intensity-* | Activity Trekking & hiking + Intensity Challenging (2 matches in the mock) |
| 14-recently-added-* | Added in the last 14 days (5 matches in the mock) |

Checks in the run: 0 console errors; `document.scrollWidth <= innerWidth` and `[data-pshell=main]` scrollWidth ==
clientWidth in every measured state; 20 photo covers + 4 placeholders on page 1.
Not covered here: real Dev data (the orchestrator re-shoots after the CIS deploy and the Vercel preview).
