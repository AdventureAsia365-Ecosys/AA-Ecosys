# AA-837 — prod axe check after TP #134 (S248, 23/10/2026)

Vercel production `e6f5c4a`, https://aa-tripplanner.vercel.app, ~14:50 UTC. Same script as the pre-change baseline
(`.tmp-session/S248-lanes/aa837-evidence/run.mjs`, Playwright 1.59 + axe-core 4.13, wcag2a/2aa/21aa).

| State | Themes × widths | color-contrast | other violations | console errors | failed requests |
|---|---|---|---|---|---|
| plan (`/plan?country=Vietnam&days=7`) | light/dark × 1440/390 | 0 | 0 | 0 | 0 |
| filters-ai | light/dark × 1440/390 | 0 | 0 | 0 | 0 |
| plan-map-mobile | light/dark × 390 | 0 | 0 | 0 | 0 |
| customise (`/plan?tour=<id not on the planner map>`) | light/dark × 1440/390 | 0 | 0 | 0 | 0 |

Baseline before the change (same script on prod): 8 contrast violations and a red console error.
The customise state used the script's placeholder tour id, so it shows the "isn't on the planner map yet" fallback;
it proves the clean console and contrast of that fallback, not a specific Sri Lanka tour.
