# UI verify: AA-812 tour/destination polish (S237, local build)

Branch `feat/aa-812-pdp-polish` (TripPlanner). Run on 15/10/2026 against a **local production build**
(`next build` + `next start`), with the browse API served by `backend.tests.dev_browse_server` over
the catalog fixtures. Photos are generated SVG gradients that read "fixture photo", not real AA photos.
The re-verify on the Vercel prod alias with real data runs after merge and deploy (orchestrator step).

Tooling: Playwright (chromium-1217), axe-core 4.10.3 (`color-contrast`, `image-alt`,
`image-redundant-alt`), Lighthouse 12.8.2 (accessibility + SEO, mobile and desktop presets).

## Result

| Check | Result |
|---|---|
| 6 pages x 1440/390 x light/dark (24 runs) | all 200, theme applied, no 390 overflow, 0 axe violations |
| Lighthouse a11y / SEO, 6 pages x mobile/desktop | **100 / 100** on all 12, `color-contrast` passes (`lighthouse-scores.json`) |
| Tour without its own photo (Mekong fixture) | hero = destination photo, captioned "Destination photo · Ha Long Bay", alt "Ha Long Bay — destination photo" |
| Tours with photos (Hanoi, Sri Lanka) | own gallery, unchanged |
| /plan List view, month filter (Vietnam) | Any month **2** tours, October **1** (`plan-list-any-*`, `plan-list-october-*`) |
| List thumbnail fallback | Mekong card shows the destination photo, alt "Ha Long Bay — destination photo"; own covers keep alt "" |
| Console | 1 error on the first page load of each context: `/favicon.ico` 404 (there was no favicon before this change either) |

Before (S236, prod alias): a11y 96 on every page, with `color-contrast` as the only failing audit.
After: 100. The fixes are the three light tokens (`--aa-accent-deep`, `--aa-muted`,
`--aa-on-accent`) and a solid dark layer under the destination hero text (`--aa-hero-bg`). Without
that layer, axe measured the white hero text against the page background (1.07:1), and a missing or
failed photo would make the text unreadable.

## Files

- `<page>-<1440|390>-<light|dark>.png`: viewport screenshots of home, tour-hanoi, tour-srilanka,
  tour-mekong-fallback, dest-vietnam and dest-sri-lanka.
- `plan-list-any-<w>-light.png`, `plan-list-october-<w>-light.png`: the planner List view before and
  after the month filter. /plan is light-only by design.
- `results.json`: per run, the status, theme, overflow, axe violations, console errors, hero alt and
  caption, and the list counts and thumbnail alts.
- `lighthouse-scores.json`: scores and failing binary audits per run. The full reports were left out
  of the repo.
