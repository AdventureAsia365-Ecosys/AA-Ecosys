# TripPlanner planner (/plan): Lighthouse before and after the planner stop-photos slice

Date: 2026-11-11. Done-when under test: "Lighthouse performance is not below today's" for the planner slice
(TripPlanner PR #250, merge `0391f7b7`).

## What was compared

| Version | Commit | How it was served |
|---|---|---|
| BEFORE | `0d6b5eb8` (main just before #250) | local production build (`NEXT_OUTPUT=standalone`, `node server.js`), port 3101 |
| AFTER | `60e5db15` (main today, the live image) | local production build, same settings, port 3102 |
| AFTER, live (reference only) | `60e5db15` | `https://tripplanner.lumiguides.it.com` (CloudFront + ECS) |

There are no immutable `*.vercel.app` URLs to compare. The TripPlanner web moved from Vercel to ECS behind CloudFront
when Vercel was retired on 2026-11-08 (runbook `docs/ops/runbooks/tripplanner-web-ecs-cutover.md`), so no Vercel
deployment of either commit exists. No live BEFORE exists either. The like-for-like comparison is therefore two local
production builds of the two commits:

- Same dependencies (the frontend `package.json` and lock file do not change between the two commits), same build
  values (the Mapbox public token of the local `.env.local`, the canonical site URL), the same Node 22 runtime.
- Same data: the BFF's upstream (`BROWSE_API_URL`, `TRIP_API_URL`) points at `scripts/shim.mjs`. The shim maps the
  Lambda REST paths back onto the live public browse endpoint (`/api/browse?resource=...`), records each answer once
  and replays it, so both builds render the same Laos catalog data. Trip reads answer 404, which the BFF turns into
  the empty trip a new visitor gets.
- The live reference run carries an `aws-waf-token` cookie from one real browser load of `/plan` (as an extra
  header), so Lighthouse measures the planner page itself, not the WAF Challenge interstitial. Every document
  answered 200. The cookie is not stored here.

## Method

- Lighthouse 12.8.2 through its Node API (`scripts/run.mjs`), performance category only, default mobile settings
  (Moto G Power emulation, simulated slow 4G and 4x CPU throttling), a fresh Chrome profile on every run (cold cache).
- Headless Chrome with software WebGL (`--use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist`).
  Without WebGL the planner's Mapbox map cannot start and the page falls into the "This page couldn't load" error
  screen. A first set measured that error screen on both versions and was thrown away.
- Per URL: one warm-up run (discarded, first server hit), then 3 measured runs. Median of the 3.
- Confirmation set (`scripts/interleave.mjs`): 5 more rounds on the two local builds, before and after alternating
  in order each round, so machine load lands on both alike. The machine was shared with other work (load average
  about 2.5).
- Observed versus simulated timings (`scripts/obs.mjs`): 6 extra runs on `/plan?country=Laos` to tell real paint
  delays from Lighthouse modelling.

## Results: medians

3 measured runs per URL (`local-before-0d6b5eb.json`, `local-after-60e5db1.json`, `live-after-60e5db1.json`):

| URL | Version | Score | LCP | TBT | CLS | FCP |
|---|---|---|---|---|---|---|
| `/plan?country=Laos` | BEFORE (local) | 49 | 5.63 s | 1923 ms | 0.009 | 0.91 s |
| `/plan?country=Laos` | AFTER (local) | 41 | 5.97 s | 2470 ms | 0.009 | 0.92 s |
| `/plan?country=Laos` | AFTER (live) | 45 | 4.93 s | 2268 ms | 0.010 | 1.23 s |
| `/plan` | BEFORE (local) | 50 | 5.55 s | 1974 ms | 0.009 | 0.91 s |
| `/plan` | AFTER (local) | 48 | 5.78 s | 2114 ms | 0.009 | 0.91 s |
| `/plan` | AFTER (live) | 45 | 4.94 s | 2165 ms | 0.010 | 1.22 s |

Interleaved confirmation, 5 rounds (`local-interleaved-5x.json`):

| URL | Version | Score | LCP | TBT | CLS | FCP |
|---|---|---|---|---|---|---|
| `/plan?country=Laos` | BEFORE | 48 | 5.78 s | 2203 ms | 0.009 | 0.91 s |
| `/plan?country=Laos` | AFTER | 39 | 5.81 s | 2271 ms | 0.009 | 4.75 s |
| `/plan` | BEFORE | 49 | 5.64 s | 2185 ms | 0.009 | 0.91 s |
| `/plan` | AFTER | 48 | 5.82 s | 2439 ms | 0.009 | 0.91 s |

The LCP element is the same in every run and both versions: the planner search box placeholder ("Search experiences
— e.g. sunrise trek, street food, temples"). No console errors. Script transfer on first load: 554 KB before, 560 KB
after.

## Reading

- `/plan?country=Laos`: AFTER is lower by 8 to 9 points. The metric that moved most is the simulated FCP. On the AFTER
  build it lands at about 4.75 s in about half the runs (4 of 8 measured runs) and at 0.91 s in the others. On the
  BEFORE build it is 0.91 s in all 8 runs. A 4.75 s FCP costs about 9 points.
- The FCP jump is Lighthouse's simulation, not a slower first paint. In the observed-timing runs the observed FCP was
  0.51 to 0.60 s on AFTER and 0.52 s on BEFORE, including the run whose simulated FCP was 4.68 s. The simulation
  sometimes places the first paint behind the first large script task (a planner chunk of about 1 s at 4.7 s
  simulated time). It does this only on the AFTER build. Observed LCP rose slightly: 0.93 to 1.11 s AFTER against
  0.87 to 0.88 s BEFORE.
- Without the FCP flip, AFTER is 1 to 2 points lower: TBT up by about 70 to 550 ms (median of medians about +250 ms)
  and LCP up by about 30 to 340 ms.
- `/plan`: AFTER is lower by 1 to 2 points (50 to 48, then 49 to 48), mainly from TBT (+140 to +250 ms). This is within
  run-to-run noise, but it points the same way in both sets.
- Live AFTER scores about 45 on both URLs. Its LCP is lower than local because the real CDN and network timings differ
  from the local server. Its FCP never flipped. There is no live BEFORE to compare it with.

## Verdict

Below. By the Lighthouse performance score the AFTER build is **8 to 9 points below** BEFORE on `/plan?country=Laos`,
and 1 to 2 points below on `/plan`. The metric that moved most is the simulated FCP on `/plan?country=Laos`: 0.91 s
before, about 4.75 s in half the after runs. Real (observed) paint timings show no comparable regression. The real
cost of the slice is extra main-thread work, about +150 to +250 ms TBT, plus about 50 to 200 ms observed LCP.

## After #254

TripPlanner PR #254 ("planner loads Mapbox after first paint, chat on first open, hover sync in its own context"),
commit `63a2aa2a`, live on 2026-11-11 (`/api/health` shows `git_sha` `63a2aa2a`). The method is the same as above.

- Live: the same WAF-token method, Lighthouse 12.8.2, mobile defaults, one warm-up run and the median of 3
  (`live-after254-63a2aa2a.json`).
- Local: a production build of `63a2aa2a`, built with the same build values and dependencies (the lock file does not
  change). It was measured against the same BEFORE build `0d6b5eb8` in 3 interleaved rounds, with order alternating,
  the same shim data and one unmeasured warm-up load per server and URL. The script is `scripts/interleave.mjs` with
  `ROUNDS=3` and the after target pointed at the `63a2aa2a` server (`local-interleaved-3x-after254.json`).

Live, after #254 against the earlier live reference (`60e5db15`):

| URL | Live version | Score | LCP | TBT | CLS | FCP |
|---|---|---|---|---|---|---|
| `/plan?country=Laos` | `60e5db15` (before #254) | 45 | 4.93 s | 2268 ms | 0.010 | 1.23 s |
| `/plan?country=Laos` | `63a2aa2a` (#254) | 62 | 2.58 s | 1611 ms | 0.008 | 1.23 s |
| `/plan` | `60e5db15` (before #254) | 45 | 4.94 s | 2165 ms | 0.010 | 1.22 s |
| `/plan` | `63a2aa2a` (#254) | 61 | 2.56 s | 2325 ms | 0.008 | 1.21 s |

Local, interleaved 3 rounds, BEFORE the planner slice against #254:

| URL | Version | Score | LCP | TBT | CLS | FCP |
|---|---|---|---|---|---|---|
| `/plan?country=Laos` | BEFORE `0d6b5eb8` | 50 | 5.64 s | 1808 ms | 0.009 | 0.91 s |
| `/plan?country=Laos` | #254 `63a2aa2a` | 53 | 5.39 s | 1309 ms | 0.007 | 0.76 s |
| `/plan` | BEFORE `0d6b5eb8` | 50 | 5.57 s | 1916 ms | 0.009 | 0.91 s |
| `/plan` | #254 `63a2aa2a` | 55 | 5.23 s | 1157 ms | 0.007 | 0.76 s |

Reading:

- Live: the score rose by 16 to 17 points on both URLs. LCP nearly halved (4.9 s to 2.6 s). TBT fell on Laos
  (-660 ms) and rose on `/plan` (+160 ms). The TBT spread between the three runs is wide (860 to 2340 ms), so that
  difference is within run-to-run noise.
- Local: #254 is above the pre-slice BEFORE build in every one of the 6 paired runs. Score +3 on Laos and +5 on
  `/plan`, TBT -500 to -760 ms, LCP -250 to -340 ms, FCP -150 ms. The simulated FCP flip seen on `60e5db15` (about
  4.75 s) did not occur in any #254 run.

Verdict after #254: **not below**. The planner is now faster than before the slice on both URLs, locally (score 50 to
53 on Laos, 50 to 55 on `/plan`) and live (45 to 62 and 45 to 61 against the `60e5db15` reference). The metric that
moved most is LCP: about 2.3 s better live.

## Limits

- Local builds, not deployments, because no BEFORE deployment exists. Absolute numbers differ from the live site.
  Only the before/after difference is meant to be read.
- Software WebGL in headless Chrome makes the map's main-thread work heavier than on a phone GPU, so TBT is high in
  absolute terms on every version.
- Some Mapbox requests from `127.0.0.1` answered 403 (the token's URL restriction). This hit both local builds alike.
  The live runs had no 403.
- With 3 runs per set and a shared machine, differences of 1 to 2 points are noise level.
