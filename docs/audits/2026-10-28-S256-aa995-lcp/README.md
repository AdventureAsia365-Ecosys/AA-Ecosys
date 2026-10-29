# AA-995 — mobile LCP on the TripPlanner public pages (S256, 28/10/2026)

Target: Lighthouse mobile **LCP ≤ 2.5 s** on the customer pages. Branch `fix/aa-995-mobile-lcp` of
AA-TripPlanner-Web, commit `7f4e5d2` (local; push, PR and deploy are orchestrator steps).

## Result (local production build, Lighthouse 12.6 mobile, 3 runs each, median)

Measured through the local "edge" harness (HTTP/2 over TLS, `/photo-cdn` cached, see Method). Two rounds of three
runs for each build; host load average during the runs 1.0–3.9.

| Page | Before LCP (r1 / r2) | After LCP (r1 / r2) | Before perf | After perf | CLS after |
|---|---|---|---|---|---|
| Home `/` | 2.47 / 2.43 s | 2.12 / 2.41 s | 98 | 98 | 0 |
| Tour (Sri Lanka 3 days) | 3.53 / 3.54 s | **2.26 / 2.26 s** | 91 | 99 | 0 |
| `/destinations` | 4.77 / 4.69 s | **2.37 / 2.25 s** | 83 | 98–99 | 0 |
| `/destinations/bhutan` | 4.16 / 4.25 s | 2.71 / **3.00 s** | 86 | 95–96 | 0 |

FCP unchanged (0.90–1.04 s), TBT ≤ 80 ms, 0 console errors, 0 hydration warnings, no horizontal overflow added
(`verify-after.json`, screenshots in `shots/`).

**Three of four pages meet ≤ 2.5 s. The destination page does not**: its hero is the CDN's 1600 w file (193 KB) and
the CDN has no smaller file that stays sharp. With a 960 w file (made by hand from the same photo, 99 KB) the same
page measures **2.11 s** (`lh/exp960-h2.json`). That needs a CIS change (follow-up below).

The first runs straight against `next start` (HTTP/1.1, no cache) are in `lh/before.json` → `lh/f2.json`:
tour 3.98 → 3.09 s, Bhutan 4.49 → 4.06 s. They show the same order of gains, but they understate them (see Method).

## What was slowing the LCP

1. **Another page's hero downloaded at high priority.** React Flight emits an image preload hint for every eager
   `<img>` / `<link rel=preload>` a Server Component renders, and a `next/link` prefetch applies the hints of the
   prefetched route on the current page. On the tour page the "Sri Lanka" links prefetched `/destinations/sri-lanka`,
   whose hero hint (`sizes=100vw`) fetched the 1600 w file (142 KB) next to the tour's own LCP photo; S255 had seen
   the same effect from links to `/` and turned off those prefetches one by one.
   Fix: LCP images render through a Client Component (`LcpImage`, `HomeHeroPicture`): same HTML, no hint.
2. **The LCP photo on a second origin.** `img.lumiguides.it.com` costs its own DNS + TCP + TLS inside the LCP window.
   Fix: the resolved LCP photo is served as `/photo-cdn/<path>?v=…`, a cached Vercel external rewrite to the CDN, so it
   reuses the page's connection.
3. **`/destinations`: lazy LCP tile behind a redirect.** The first tile loaded lazily through the CIS catalog URL (302
   from the API, ~0.5 s server latency in the trace). Fix: the first row is resolved on the server, eager, and the
   first photo tile has `fetchpriority=high`.
4. **Bytes before the LCP.** The header logo was a 752 x 481 PNG (16 KB) for a 36 px slot → 108 px tall 8-bit PNG
   (6.8 KB). JavaScript is the largest block (~165 KB gzip, ~135 KB brotli on Vercel): without it, home measures
   2.26 s and the tour 2.88 s (HTTP/1.1) (`lh/exp-*nojs.json`), so it sets the floor; it is the framework runtime, not
   page code.

## Checked and not kept

| Change | Measured | Decision |
|---|---|---|
| No font preloads (Poppins + Satisfy) | home LCP 2.64 → 2.48 s, **FCP 0.91 → 1.66 s**, CLS 0.02 | Reverted |
| Destination hero at 600 w on phones | Bhutan 3.19 s (HTTP/1.1); visibly soft (`shots/bhutan-hero-600w-412.png` vs `-1600w-`) | Not kept: a `sizes` value that picks 600 w only at Lighthouse's 1.75 DPR helps the score, not real phones |
| Defer below-the-fold images (strip, map, cards) | Blocking them in Lighthouse gave no LCP gain once the LCP photo was same-origin | Not built |
| `next/image` (Vercel Image Optimization) | not measured | Not used: Hobby team with a monthly transformation quota; a public `/_next/image` over ~2,000 catalog files can be exhausted by crawlers, then LCP images fail. A tech-lead option |

## The image CDN (AA-844) and 960 w

- The CDN serves only the files CIS stores: `<file>-600.webp` and `<file>-1600.webp` (`-960.webp`, `.avif` → 403; no
  resize on query). CIS makes two renditions (`services/photos/sync.py SIZES = {"large": 1600, "small": 600}`,
  WebP q85; columns `s3_key_small|large`), and `/content/photos/{id}?size=` accepts `large|small|original` (`medium` →
  422).
- TripPlanner is ready: `resolveHeroPhoto` asks for `?size=medium` and adds a `960w` srcset entry only when CIS
  redirects it to a file, so the CIS change goes live at the next ISR refresh without a TripPlanner deploy.
- Sizes from the Bhutan hero: 1600 w WebP q85 193 KB · 960 w WebP q85 99 KB · 960 w WebP q75 62 KB · 960 w AVIF q55
  50 KB · 1600 w AVIF q55 96 KB.

**Follow-up (CIS, proposed):** add a `medium` 960 w rendition (WebP; AVIF optional), a `s3_key_medium` column, accept
`size=medium` on `/content/photos/{id}`, and a backfill job for the stored photos (~1,120 distinct files). That brings
the destination pages under 2.5 s and lets phones with DPR ≥ 2 take 960 w instead of 1600 w for tour photos too.

## Method

- **Build**: AA-TripPlanner-Web `origin/main` `e4facde` (before) and `7f4e5d2` (after), `next build && next start`.
- **Data**: the lane had no browse API key, so `harness/server.cjs` serves fixtures from `harness/build_fixtures.py`,
  built only from public production answers (`/api/browse?resource=catalog-tours` for all 892 cards, `by-country`,
  and the JSON-LD/HTML of the measured pages). Photos, tours and places match production; the destination page shows
  12 tours like production but more distinct covers (more lazy images than production: a conservative difference).
  The same fixtures served both builds.
- **Edge harness** (`harness/edge.cjs h2`): HTTP/2 over TLS in front of `next start`, caching `/photo-cdn/*`. Without
  it, Lighthouse's simulation queues same-origin requests behind HTTP/1.1's six connections (Vercel speaks HTTP/2),
  and every run pays a fresh fetch to CloudFront inside the local rewrite (the Vercel CDN fetches once per file). Text
  is gzip here, brotli on Vercel (about 15 % smaller JS), so production should be a little faster than these numbers.
- **Lighthouse**: 12.6.1, default mobile (Moto G Power emulation, 412 x 823 @1.75, simulated 150 ms RTT / 1.6 Mbps,
  4x CPU), performance only, `harness/measure.sh` + `harness/summarize.py`; per-run values in `lh/*.json`.
- The mapbox static map answers 403 for the local token on localhost (0 bytes), and it starts after the LCP on these
  pages; production loads it.

## Production check (orchestrator, after deploy)

`.tmp-session/S256/aa995/postdeploy.sh <sha>`: `/api/health` SHA, the `/photo-cdn` hero twice (200 `image/webp`,
second `x-vercel-cache: HIT`), then the same 3-run Lighthouse on production into `lh/prod-after.json`. Run
`measure.sh prod-before https://aa-tripplanner.vercel.app` before the deploy for the production baseline.
