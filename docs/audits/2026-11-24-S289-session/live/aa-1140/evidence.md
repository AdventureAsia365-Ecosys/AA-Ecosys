# AA-1140 Ecosystem status page (/admin/overview): live check on Dev (S289)

- When: 2026-11-24, 02:20–02:30 UTC (09:20–09:30 +07). Run by an agent, headless Playwright (Node,
  `tools/uat/node_modules`, Chromium), read only.
- Deployed at the time of the check: CIS `/health/ready` `git_sha 4fc24809…`, `schema_version` 476. That is
  AA-CIS-App #1659 (CIS 476, settings registry chore) on top of `eb85befc` (#1657, the AA-1140 backend) and
  `ff86cb60` (#1658, the AA-1140 page), so both AA-1140 commits are live. The Services table shows `aa-cis-dev-admin`
  on `ff86cb6`.
- Sign-in: the Dev-only E2E owner (root ADR 0006a A10h), Cognito managed login with an e-mail code, as in
  `2026-11-23-S288-session/live/e2e-owner/evidence.md`. The code was read from the S3 prefix `inbound-admin/` with the
  MFA admin profile (`tools/uat/lib/mailbox.cjs`). It was never printed, logged or screenshotted. No screenshot was
  taken on the sign-in host. `GET /api/admin/session` 200, `role admin`. The saved browser state was a scratch file.
  It was deleted at the end.
- **Writes on Dev made by this run: none.** After sign-in every non-GET browser request was aborted by a route guard,
  and Node-side requests were limited to GET. The only aborted requests were Sentry envelopes and the
  `/api/auth/refresh` keep-alive. No setting was changed. "Copy link" only writes the local clipboard.
- Masking: every e-mail address in the page that is not an `e2e-mail` address was masked before each screenshot.

## BFF answer: `GET /api/admin/overview/status?range=24h` (one call, 02:20:55 UTC)

- HTTP 200. Top-level keys: `generated_at, environment, range, previous, buckets, verdict, thresholds, sections,
  sources`.
- `environment` dev. `range` 24h, step 3600 s, 24 buckets. `previous` null (compare off).
- **Verdict `attention`**, `open` 7, `unknown` [] (every core source answered). Chips: alarms firing 1, open alerts
  7, deploy gate open.
- The 7 items are all SEV3:
  - CIS 4xx 14.97 % against the 10 % warn
  - free storage 14.83 GiB against the 15 GiB warn
  - 4 ops check bells
  - the RDS snapshot-copy-age alarm
- `thresholds`: 16 keys, each with its settings key: `cis.ops.status_*` and the two CIS 469 keys
  `cis.ops.role_connections_pct` / `cis.ops.xid_age_limit`. `history_days` 14, `stale_factor` 3, `uptime_slo_pct`
  99.5.

| Section | status | as_of (UTC) | measured / not measured |
|---|---|---|---|
| signals | ok | 02:20:39 | `apps.measured`: cis true, tripplanner true, booking true, **crm false** |
| apps | ok | 02:20:39 | CRM traffic `not_measured` (shared ALB, no DescribeTargetGroups), CRM activity `not_measured`, TripPlanner health null |
| runtimes | ok | 02:15:00 (last 5-min sample) | 12 rows: 10 sampled ok, 2 `not_measured` (TripPlanner Lambda, TripPlanner web on Vercel) |
| resources | ok | 02:20:57 | 6 tiles measured |
| jobs | ok | 02:20:57 | `shared` ok, `crm` ok, **`booking` `not_measured`** (no owner view for CIS) |
| ai | ok | 02:20:57 | 4 apps, 6 connections |
| cost | ok | 02:20:41 | month 2026-11: spent 268.93 USD, forecast 345.04 USD of a 1000 USD budget |
| events | ok | 02:20:57 | 18 events: 12 deploy, 4 check, 1 service_down, 1 alarm |
| delivery | ok | 02:20:57 | 6 repos green. Guards: 2 passed, **6 `not_measured`** (GitHub only / ECS task without a verdict line) |

`sources`: 9 rows, all `ok`, each with its own `as_of`.

### Short sampler history

The sampler started at about 01:15 UTC (08:15 +07). The Jobs summary showed `ops_status_sample` succeeded 14 and
none failed. No section is empty, but the sampled series are short:

- Runtimes: 3 of 48 uptime-strip cells are filled.
- Busiest DB role and XID age: 2 of 24 points each.
- `shared.job` oldest-wait series: 2 points.
- Uptime is computed over about 14 samples. One bad sample of `aa-booking-dev-admin` (a `service_down` event) makes its
  24 h uptime 92.86 % and its error budget left −1329 %. The row's current state is ok. This is how the arithmetic
  works on a short history, not a bug, but it will read alarming until about a day of samples exists.
- The CloudWatch charts, the cost section and the AI section do not depend on the sampler. They have the full range.

## Done-when checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Page live at `/admin/overview`, read at 1440 / 390, light / dark, EN / VI | **pass** | h1 "Ecosystem status" / "Trạng thái hệ sinh thái". Verdict "7 things need you" / "7 việc cần bạn xem". `html[data-theme]` matched the theme and `html[lang]` matched the language each time. Body background light `rgb(244,241,236)`, dark `rgb(15,20,27)`. No horizontal overflow at 390 (`scrollWidth − innerWidth` = 0). No console error other than the aborted telemetry. The page is about 8,200 px tall at 1440 and about 20,200 px at 390; the 390 shots stop at 16,000 px (the event list and the sources table are cut). Files `01`–`08`. |
| 2 | Each section reads real Dev data with its as_of | **pass** | 9 cards each show "as of …" (VI "lúc …") on the viewer's clock (+07), matching the API `as_of` (Services 09:15 = the 02:15 UTC sample). Values match the API, for example CIS requests 21,5xx, Booking 3,6xx/3,7xx (the page refreshed between reads), RDS free storage 14.8 GiB warn, 7 of 7 ECS tasks. |
| 3 | A signal not wired yet shows "not measured yet", never green | **pass** | 15 grey "Not measured yet" chips (text colour `rgb(75,85,99)`, neutral tone): CRM traffic and activity, the CRM legend entry of 3 charts, the Booking and CRM legend entries of the queue chart, the Booking queue row, 6 nightly guards, TripPlanner health. The 2 TripPlanner runtime rows sit under the "No sample 2" filter, not under Healthy. None of them is green. Minor: the TripPlanner health chip has no reason text (F3). |
| 4 | Every chart draws thresholds from Settings or the alarm, plus a headroom line | **pass, with a bug** | Each of the 4 charts has a headroom line. Errors, latency and queue draw warn as a dashed reference line and critical as a solid line with the area above it shaded, at exactly the API `thresholds` values from settings: errors 1 / 5 %, p95 1.5 / 3 s, queue 15 / 60 min. Latency also draws the TripPlanner Lambda limit, 6 s (`cis.ops.status_lambda_p95_limit_ms`). Alarm bands (1) and deploy ticks (12) are drawn. Requests per minute has no limit by design ("Load-test capacity: not measured yet", "Headroom: no value"). Resources tiles show now / worst / warn / critical / headroom from the same keys. **Bug F1** below. |
| 5 | Filters, time range, legends, sort, compare and URL state work, and survive a reload | **pass, with a bug** | Changed in the UI: 6 h, compare on, apps CIS + TripPlanner, latency legend TripPlanner off, SEV3, services filter Healthy, services sorted by Uptime, events Info, events sorted by Time, attention sort "app ↑". URL: `?range=6h&compare=1&apps=cis,tripplanner&hide=latency:tripplanner&sev=sev3&svc=healthy&sort=svc:uptime:desc,ev:t:asc,att:app:asc&ev=info`. After a reload, all 10 controls kept their state (`aria-pressed` / `aria-checked` / `aria-sort` / checkbox / select read before and after). Compare drew 2 dashed previous-period lines. The app filter left 2 app cards, 4 services and 7 events. "Copy link to this view" copied exactly `location.href`; opened in a new tab it showed the same 10 states. "Reset view" went back to a bare `/admin/overview`. A custom range 20 days back was refused in the picker: Apply was disabled, with "The start must be within the last 14 days" (`history_days` 14). A custom range 3 h to 1 h ago was applied (`range=custom&from=…Z&to=…Z`, read "06:20 – 08:25 · step 5 min") and kept after a reload. **Bug F2** below. Files `09`, `10`. |
| 6 | One BFF call: keys, verdict, as_of / measured per section | **pass** | See the section above. |

## Findings

- **F1 (bug, minor): the latency headroom compares TripPlanner Lambda p95 with the API warn limit.**
  - File: `frontend/app/admin/overview/_status/Signals.tsx`. The latency spec has `limit: thresholds(th, "p95_ms")`.
    `HeadroomLine` takes the peak over every shown series.
  - In the default 24 h view the line reads "peak 2.17 s · Headroom −668 ms · warn 1.50 s". That peak is TripPlanner
    (API: max p95 2,167 ms). TripPlanner's own limit is 6 s, and its tile and its `p95_level` say ok.
  - So the page shows a negative headroom with no matching attention item. The TripPlanner line also crosses the
    dashed API warn line.
  - Hiding TripPlanner in the legend gives "peak 409 ms · Headroom 1.09 s".
  - Fix idea: compute the headroom per series against that series' own limit (the API p95 limit for API Gateway
    apps, `lambda_p95_limit_ms` for TripPlanner), or leave TripPlanner out of the API-limit headroom.
- **F2 (bug, minor): two quick chip clicks lose the first one.**
  - Clicking CIS, then Booking 100 ms later, gave `apps=booking`: CIS was dropped. Clicks 1.5 s apart work.
  - Cause: `ChipFilter.flip` (`_status/ui.tsx`) builds the next list from the `view` prop. The URL update
    (`useView` → `setMany` in `page.tsx`) has not re-rendered yet, so the second click starts from the stale list.
  - The same applies to every chip filter and to legend toggles.
  - Fix idea: a functional update that reads the current search params when it writes.
- **F3 (cosmetic): TripPlanner health shows "Not measured yet" with no reason.** The API gives `health: null`, so the
  chip has no title or text. Every other not-measured chip says why.
- **F4 (cosmetic): the app tile metric row is cramped at 1440.** The labels "REQUESTS5XX" run together, and values
  wrap as "0.00 / %" across two lines in the 4-up grid (`01`). At 390 the row is fine.
- Note: the CIS app tile says "ok — traffic looks normal" while its 4xx share, 15 %, is over the 10 % warn and is a
  SEV3 attention item. The overall verdict ignores client errors. That looks intended, but it reads oddly next to the
  amber 4xx value.

## Screenshots

| File | View |
|---|---|
| `01-overview__1440__light__en.webp` | 1440, light, EN, full page |
| `02-overview__1440__dark__en.webp` | 1440, dark, EN |
| `03-overview__1440__light__vi.webp` | 1440, light, VI |
| `04-overview__1440__dark__vi.webp` | 1440, dark, VI |
| `05-overview__390__light__en.webp` | 390, light, EN (first 16,000 px) |
| `06-overview__390__dark__en.webp` | 390, dark, EN |
| `07-overview__390__light__vi.webp` | 390, light, VI |
| `08-overview__390__dark__vi.webp` | 390, dark, VI |
| `09-view-state-after-reload__1440__light.png` | The changed view after a reload (6 h, compare, CIS + TripPlanner, SEV3) |
| `10-custom-range-too-old__1440__light.png` | Custom range 20 days back, refused in the picker |

All images were compressed with `tools/docs/compress_images.py`. Each is 400 KiB or less.
