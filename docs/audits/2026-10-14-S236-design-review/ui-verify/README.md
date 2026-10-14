# UI verify — S236 design review (14/10/2026)

Read-only verification (no data written, no setting saved, "Send to an advisor" never clicked).
Tooling: Playwright (chromium-1217) + Lighthouse 12.8.2, run from the Claude Code scratchpad with a
scratch Chrome profile. Run in two parts: part 1 (interrupted) produced `cis/`, `tp/` screenshots +
`results.json` and 8 Lighthouse reports; part 2 finished the remaining alias Lighthouse runs, scrubbed
the Vercel protection cookie that part 1 had left in 8 reports, and added `tp/results-supplement.json`
(re-check of /plan, Customise on two more tours, Mapbox on the prod alias).

Targets
- TripPlanner (AA-812): deployment `aa-tripplanner-79o04iy51-…vercel.app` (Vercel-protected, share-link
  cookie) and its public prod alias `aa-tripplanner.vercel.app` — **same build** (`buildId wEg7P9OR1VeKxsUkHSQci`).
- CIS admin (AA-766): `https://aa-cis.lumiguides.it.com/admin/tenants`, tenant `atlas-hearth`
  (`9149d3c6-…`), E2E admin `e2e-claude-code` (password read from Secrets Manager into env only).

## Summary

| Area | Verdict |
|---|---|
| CIS admin — Tenants › atlas-hearth Cost/Quality/Markets/Settings | **PASS** |
| TP home, destinations (bhutan, vietnam), 3 tour pages | **PASS** (minor defects) |
| TP home search → /plan pre-fill | **PASS** |
| TP /plan (map + List view) | **FAIL** — tile-request storm on the prod alias (D1) |
| TP "Customise this trip" → /plan with tour applied | **FAIL** — tour never applied, `tour-route` 404 (D2) |
| Lighthouse SEO ≥ 90 | **PASS on prod alias (100)**; 61 on the protected deployment URL is a Vercel artefact |

## A) TripPlanner (AA-812)

### Per page (1440/390 × light/dark, `tp/<page>-<w>-<scheme>.png`)

| Page | HTTP | Console errors | Overflow @390 | Images | SEO tags | Verdict |
|---|---|---|---|---|---|---|
| `/` | 200 | 0 | none | 13/13 | title, canonical, meta, JSON-LD WebSite | PASS |
| `/plan` | 200 | Mapbox 403 ×12 + `[mapbox error]` (deployment URL only); 1440-light run: timeout + ~8.4k `ERR_INSUFFICIENT_RESOURCES`, ~1.6k 503 | none | — | noindex by robots (intended) | **FAIL (D1)** |
| `/plan` List view | — | — | none | thumbnails partly blank | — | PASS (892 tours listed, stays light) |
| `/destinations/bhutan` | 200 | 0 | none | 14/15 (static map) | TouristDestination | PASS |
| `/destinations/vietnam` | 200 | 0 | none | 1/2 (static map) | TouristDestination | PASS |
| `/tours/…kailash…98624d92` | 200 | 0 | none | 1/2 (static map) | TouristTrip | PASS |
| `/tours/…sri-lanka…63d21f32` | 200 | 0 | none | 1/2 (static map) | TouristTrip | PASS |
| `/tours/…agra…ea434fb6` | 200 | 0 | none | 1/2 (static map) | TouristTrip | PASS |

- `/plan` stays light in dark mode (`data-theme=light` in all 4 runs) — as required.
- Missing image on destination/tour pages = Mapbox static map blocked (`ERR_BLOCKED_BY_ORB`, i.e. 403)
  **only on the deployment URL**; on the prod alias the same image loads (`results-supplement.json`
  › `alias_tour_srilanka`: 26 requests all 200, map image ok). The Mapbox token is URL-restricted to the alias.

### Flows

- **Home search** (Vietnam, 14 days, 2 travellers) → `/plan?country=Vietnam&days=14&travellers=2`;
  route planner pre-filled (Heading to = Vietnam, 14 days, "Planning for 2 travellers", one matching
  route offered). PASS — `tp/flow-home-search-plan.jpg`.
- **Customise this trip** (Sri Lanka, Kailash, Agra) → `/plan?tour=…&source=…&country=…&days=…`;
  country and days are pre-filled but the tour itself is **not** applied: toast "This tour isn't on the
  planner map yet", "Your trip" stays empty. `GET /api/browse?resource=tour-route&tour_id=…&source_id=…`
  → 404 `{"error":"no planner route for this tour"}` for all three (reproduced with curl on the alias).
  FAIL — `tp/flow-customise-plan.jpg`, `tp/flow-customise-kailash.jpg`, `tp/flow-customise-agra.jpg`.

### Lighthouse (`lighthouse-scores.json (full reports kept outside the repo) — *.report.html|json`)

| Page | URL | Mobile P/A/SEO | Desktop P/A/SEO |
|---|---|---|---|
| Home | deployment (cookie) | 100 / 96 / 61 | 88 / 96 / 61 |
| Tour Sri Lanka | deployment (cookie) | 75 / 96 / 61 | 100 / 96 / 61 |
| Destination Vietnam | deployment (cookie) | 100 / 96 / 61 | 100 / 96 / 61 |
| Home | prod alias | 100 / 96 / **100** | 86 / 96 / **100** |
| Tour Sri Lanka | prod alias | 100 / 96 / **100** | 99 / 96 / **100** |
| Destination Vietnam | prod alias | 100 / 96 / **100** | 100 / 96 / **100** |

- SEO 61 on the deployment URL comes only from `is-crawlable` (Vercel sends `x-robots-tag: noindex` on
  deployment URLs) and `robots-txt` (robots.txt fetched without the cookie gets the SSO page). The prod
  alias scores 100 on every page → target SEO ≥ 90 **met**.
- Accessibility 96 everywhere: single failing audit `color-contrast`.
- Performance outliers (75 tour mobile, 86–88 home desktop: LCP 2.4 s / TBT 1.1 s) are single-run
  noise-prone numbers; the alias re-runs are 99–100.

## B) CIS admin — Tenants › atlas-hearth (AA-766)

Screenshots `cis/tenants-expanded-*` and `cis/tab-{cost,quality,markets,settings}-{1440,390}-{light,dark}.png`.

| Check | Result |
|---|---|
| Console errors / warnings | 0 / 0 in all 4 runs |
| Network | `details`, `rewrite-activity`, `cost`, `quality?days=30`, `markets`, `config` all **200**; no failed requests |
| Cost | LLM cost (2026-10, MTD) **$8.49** (expected ≈ 8.48 — matches); plan revenue $799.00, margin $790.51 (98.9 %), $/tour $0.3824, $/blog $0.0060; cost-by-stage table (t9_write 54 %, t2_generate 31 %, …) |
| Quality / Markets / Settings | render, no error state |
| Overflow @390 | none on any tab |
| Settings | opened only, nothing saved |

Verdict: **PASS**. Note: the tab screenshots are element captures of the expanded tenant panel, which
scrolls internally, so long tabs (Cost) are clipped at the panel height with blank space below — a
capture limitation, not a page defect.

## Defects

| # | Sev | Page | Description | Evidence |
|---|---|---|---|---|
| D1 | **High** | TP `/plan` (prod alias) | Once the Mapbox map loads, the page fires ~10,200 `GET /api/browse?resource=tiles&tile_id=…` in ~8 s → ~1,050× 503 and ~8,900× `net::ERR_INSUFFICIENT_RESOURCES`, `TypeError: Failed to fetch`; no experience markers render. Not visible on the deployment URL only because Mapbox 403s there and the map never loads (part-1 1440-light run hit it too: 60 s timeout). | `tp/recheck-plan-1440-light-alias.jpg`, `tp/results-supplement.json › plan_alias`, `tp/results.json` (plan 1440 light) |
| D2 | **High** | TP tour → `/plan` | "Customise this trip" never applies the tour: `tour-route` 404 "no planner route for this tour" for Sri Lanka, Kailash and Agra; user gets "This tour isn't on the planner map yet". | `tp/flow-customise-*.png`, `results-supplement.json › customise_*` |
| D3 | Low | TP `/plan` | Icon glyphs render as tofu boxes (empty-state icon, Tip line, mobile "Explore" / "Your trip" tabs). | `tp/plan-1440-light.jpg`, `tp/plan-390-dark.jpg` |
| D4 | Low | TP tour pages | Hero shows camera placeholder (no tour photo) on all 3 tours. | `tp/tour-srilanka-390-dark.jpg` |
| D5 | Low | TP `/plan` List view | Many card thumbnails blank/placeholder. | `tp/plan-list-1440-light.jpg` |
| D6 | Low | TP all | Lighthouse `color-contrast` fails (a11y 96). | `lighthouse-scores.json (full reports kept outside the repo) — *-mobile.report.html` |
| D7 | Info | TP deployment URL | Mapbox token rejects the deployment hostname (403 tiles, static maps blocked). Prod alias fine; preview/deployment reviews will always look map-less. | `tp/results.json` http_errors |

## Blocking Done

- **AA-812: blocked** by D1 (planner floods the tiles API on prod) and D2 (Customise-this-trip does not
  apply the tour). Everything else (pages, SEO ≥ 90 on prod, a11y 96, home-search pre-fill, light-only
  /plan, no 390 overflow) passes.
- **AA-766: not blocked** — all four tabs load with real data, 0 console errors, all APIs 200, Cost MTD $8.49.

## Hygiene

- Vercel protection cookie scrubbed from all Lighthouse reports (`<redacted>`); no `_vercel_jwt` or
  share token in this folder. Mapbox `pk.` (public) token appears in recorded URLs.
- No password written anywhere. Chrome/Lighthouse profiles lived in the scratchpad; repo root unchanged.
