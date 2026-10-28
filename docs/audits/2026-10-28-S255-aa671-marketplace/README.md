# AA-671 Marketplace redesign: local screenshots (S255, 28/10/2026)

Built from AA-Partner branch `feat/aa-671-marketplace-redesign` (01-07 shot at pre-rebase commit 953186e, 08-09 after the review fixes; branch head 6bffde1), `next build` + `next start` locally,
API answered by a mock of the CIS API (`.tmp-session/S255/aa671/mock_api.py`, fabricated sample tours, no real tenant
data; the mock quota is 46 of 50 rewrites used so the quota note shows). Captured by `.tmp-session/S255/aa671/shots.cjs`
(Playwright, scrollbars on). Desktop 1440x900 and phone 390x844, light and dark.

| File | What |
|---|---|
| 01-all-tours-* | Marketplace, All tours: grid, filters, counts on the view tabs |
| 02-bulk-select-* | Two cards selected: bulk bar with the quota note |
| 03-drawer-new-tour-* | Drawer of a tour never rewritten: Rewrite this tour + quota note |
| 04-drawer-in-my-tours-* | Drawer of a tour already in My Tours: Open in My Tours, Rewrite again |
| 05-filtered-* | Country Vietnam + length 1-3 days, Clear filters |
| 06-in-my-catalog-* | View In my catalog (?view=mine): price, version, work status |
| 07-in-my-catalog-empty-* | Empty In my catalog (rollup answer mocked empty; the tab count still reads the mock versions) |
| 08-bulk-bar-sticky-* | Grid scrolled with two tours picked: the bulk bar stays at the top of the scrolling main area |
| 09-drawer-paused-tour-* | Drawer of a tour AA paused: served badge and the reason instead of Rewrite |

Checks in the run: no console error on any page; `document.scrollWidth <= innerWidth` and `[data-pshell=main]`
`scrollWidth == clientWidth` in all measured states (01-09); no element past the right edge.
Not covered here: the real Dev data (the orchestrator re-shoots after the Vercel preview / Fargate deploy).
