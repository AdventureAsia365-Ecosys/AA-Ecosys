# AA-990 parity — F2 and F3 investigation (read-only)

Run: 27/10/2026 06:30 +07 (26/10 23:31 UTC), Claude Code subagent. No DB access, no AWS, no writes. The code was read at
AA-CIS-App `origin/main` eb1c3f80 and AA-TripPlanner-Web `origin/main` 7441859. That TripPlanner commit has no
`backend/browse` change since before the audit, so the Lambda code the audit hit is the code read here. The public
endpoints were re-called with curl. The SQL below is for the orchestrator to run.

## Summary

| | Root cause | Data or code | Fix |
|---|---|---|---|
| **F3**: Pakistan and Philippines missing | CIS place guard has no Pakistan or Philippines (`services/places/guards.py:21-50`), so every PK/PH place name is thrown away at geocoding and never gets coordinates | **Code** (CIS). Mig 197 (01/10) added both countries to `chk_raw_tours_country`; the guard list was never updated | Add `pk`/`ph` to the guard maps and BBOX, add a drift test, then re-geocode the PK/PH names (reset + one `place_geocode`; the graph rebuilds itself) |
| **F3**: Cambodia and Kyrgyzstan present | The planner list is "countries of **places** that have a component" (`backend/browse/countries.py:24-32`), not countries of tours. Cambodia and Kyrgyzstan places come from cross-border tours sold under another country | **By design** | Nothing needed. If product wants "tour countries", change the SQL (option below) |
| **F2**: route shorter than the tour | (a) TripPlanner sizes a Tour Graph route from the first to the last **stop** day (`backend/browse/routes.py:247-256`). Stop-less days at the start or end (arrival, departure) are cut off. Unlike `places`, no coverage rule applies to `tour_graph` (`routes.py:330-334`). (b) Some tours still have unresolved places for whole stretches of days | (a) **Code** (TripPlanner): 8 of the 11 still-short tours are only missing the departure day and/or the arrival day. (b) **Data**: 3 tours (more likely), plus the audit sample was taken while AA-905 lot 7 was still running | Code: span the route over tour days 1..N, carry the nearest stop into those days without a pin, and gate `tour_graph` by pinned-day share like `places`. Data: run Q7–Q9; re-geocode the names still pending |
| **F2**: "no `match`/`total_days` keys" on 27/10 | The routed answer has always been `{tour_id, proposal:{…}}`. `match` and `total_days` sit under `proposal` | **No format change** (shape dates from TP #72/#73, 14/10) | Read `.proposal.match` / `.proposal.total_days` |

## F2 — what tour-route returns now

`GET https://aa-tripplanner.vercel.app/api/browse?resource=tour-route&tour_id=335c1a57-9e06-4e1c-8b89-22669993ab63&source_id=700044ca-18e8-405a-b9af-54739cd6c0c8`
→ **200**, `cache-control: public, max-age=60`, `x-vercel-cache: MISS`:

```json
{
  "tour_id": "335c1a57-9e06-4e1c-8b89-22669993ab63",
  "proposal": {
    "total_days": 11, "transfers": 0, "transfer_km": 0.0, "whole_tour": true, "match": "tour_graph",
    "segments": [{"tour_id": "335c1a57-…", "tour_name": "Northern Thailand and Laos Cycling Tour — 12 Days",
                  "day_from": 1, "day_to": 11, "days": 11, "source_id": "700044ca-…"}],
    "days": [{"day": 1, "tour_id": "335c1a57-…", "tour_day": 1, "component_id": null,
              "destination_id": "b5e3c9f2-…", "name": "Chiang Mai", "lat": 18.787453, "lng": 98.9937,
              "country": "Thailand", "source_id": "700044ca-…"}, "… 11 rows"]
  }
}
```

A tour with no route answers 200 `{"match": "none", "tour": {"title", "country", "duration_days", "days": [{day, title}]}}`.
The Lambda's 404 is rewritten by the BFF (`frontend/lib/tourRoute.ts`, `frontend/app/api/browse/route.ts:99-107`).

**The format did not change.** The Lambda body is built at `backend/browse/handler.py:164`
(`{"tour_id": current, "proposal": proposal}`, since TP #72, 14/10), and `match` is set at `routes.py:253` (TP #73, 14/10).
The audit script read `proposal.*`, as `results.json` shows. A body "without `match`/`total_days`" is the routed answer
read at the top level. The Lambdas were redeployed on 26/10 15:36Z (#160, CI only), but no browse code changed.

**What did change is the data.** This tour went from 4/12 at the audit (26/10 13:52Z) to 11/12 now. The re-probe of all
43 sampled tours (same URLs as `results.json`) gives:

- 700044ca: tour_graph 4 → **11** days (12-day tour).
- 7100f50c (Thailand): `none` → **tour_graph 7/7**.
- Every other tour is unchanged: still 11 short `tour_graph` routes (10 from the audit plus 700044ca now at 11/12). Vietnam ca1d7500 at
  12/14 matches its 12 `v_tour_day` blocks (a content note, not a route issue). Pakistan and Philippines are still `none`.

Timing: AA-905 lot 7 (Sri Lanka 55, Taiwan 31, Thailand 14, **incl. 700044ca and 74f84466**) was enqueued at 13:25:50Z.
Lot 8 (Thailand 20, **incl. 7100f50c**) was enqueued at 14:28:10Z
(`.tmp-session/s252/aa905/lot7_real.json`, `lot8_real.json`). The audit's 13:52Z sample therefore caught lot 7 mid-flight:
places were extracted, but most names were not yet geocoded. When the names resolved, `place_geocode` re-enqueued
`tour_graph_build` and the route grew.

### Which days are missing (current answer vs the tour page's day list)

| Tour (source prefix) | Route / tour days | Missing tour days | Class |
|---|---|---|---|
| Bhutan c58222c8 | 6/7 | 7 "Hotel checkout and departure" | A: departure |
| India 5122bd9b | 7/8 | 8 "Delhi: departure" | A |
| South Korea d9b10288 | 8/9 | 9 "Departure from Seoul" | A |
| Sri Lanka cd8bc159 | 6/7 | 7 "Negombo to the airport" | A |
| Thailand e53c44c6 | 13/14 | 14 "airport transfer" | A |
| Thailand 700044ca | 11/12 | 12 "free time and airport transfer" | A |
| Nepal de1eea74 | 13/15 (days 2–14) | 1 "airport pick-up", 15 "transfer to airport" | A: arrival + departure |
| Nepal 2b9070e3 | 6/9 (days 3–8) | 1 "Arrival", 2 "…trek to Australian Camp", 9 "Departure" | A + B (day 2 place; days 4–6 carry "Pothana") |
| India 51285758 | 1/4 (day 4 only, **0 pins**) | 1 Kullu, 2 Barot/Badagram, 3 Billing | **B: places unresolved** |
| Japan a90ddcc5 | 2/6 | 3 Shiobara, 4 Nikko, 5 Lake Chuzenji, 6 Tobu Nikko | **B** |
| Taiwan 74f84466 | 1/3 (day 3 only) | 1 Taipei riverside, 2 Yangmingshan | **B** (lot 7) |

- **Class A (code, 8 tours)**: a day with no overnight and no located place has no stop, which is correct for the graph
  (`services/places/graph.py:68-87`, stop = overnight destination, else the day's main place). TripPlanner then sizes
  the "whole tour" from the first stop day to the last (`routes.py:249-252`), and `day_by_day` walks only
  `d_from..d_to` (`routes.py:144-146`). Edge days without a stop are dropped instead of being shown unpinned. A rebuild
  does not fix this.
- **Class B (data, 3 tours)**: whole stretches of days have no stop. The likely cause is that their anchor and place
  names are still `pending`, `unknown` or `failed` in `geo.place_name`. Possible reasons: Geoapify daily credit guard
  `stopped_credit_limit` (2,500/day; about 634 new names per AA-905 lot × 8 lots). A deferred name stays pending, and
  `place_geocode` does **not** re-enqueue itself after a credit stop (`services/jobs/place_geocode_job.py:15-19`). Other
  reasons: model "unknown", or bbox rejects. **Unverified**: Q8 settles it per day.
- 51285758 shows a planner route that pins **nothing**: its only stop day has no component.
  `_graph_route` accepts a graph that has any component anywhere in the tour (`routes.py:264-268`), and no share rule
  applies (`PLACES_MIN_DAY_SHARE` is used only in `_places_route`, `routes.py:305-309`).

### F2 fix

1. **TripPlanner code** (`backend/browse/routes.py`):
   - In `tour_route` / `_proposal` (`routes.py:247-256, 313-339`), read `TOUR_DAYS_COUNT_SQL` (`routes.py:223-227`,
     already there) as N. For `match: tour_graph`, span the proposal over days `1..max(N, last stop)`: leading days take the
     first stop, trailing days carry the last stop, and both stay unpinned (`component_id: null`).
     `day_by_day` (`routes.py:136-156`) needs a seed for the leading days, for example an optional `seed_stop`.
     Add `tour_days: N` and `pinned_days` to the proposal (additive keys, no client break).
   - Apply the S236 share rule to the graph too. If the graph route pins fewer than `PLACES_MIN_DAY_SHARE × N` days, try
     `_places_route` and keep the route with more pinned days. If neither reaches the share, return None so the planner
     shows the day list. This removes the 0-pin route on 51285758, and probably a90ddcc5 and 74f84466 until their
     places resolve.
   - Tests: `backend/tests` cases for a departure day without a stop, arrival and departure, a 0-pin graph, and a
     graph below the share with places above it.
2. **Data**: run Q7–Q9. For Class B names still `pending` with `next_retry_at <= now()`, or deferred by the credit limit,
   enqueue one `place_geocode` (worker job, ≈ $0.015 per 40 names + free Geoapify credits). It enqueues
   `tour_graph_build` itself. Names marked `unknown` need an admin fix or a source text fix; a rebuild does not fix
   them. A re-extract or rebuild **is not needed** for Class A.

## F3 — country list

`GET https://aa-tripplanner.vercel.app/api/browse?resource=countries` → 200 (now):
`Bhutan 577, Cambodia 48, China 1699, India 3619, Japan 84, Kyrgyzstan 18, Laos 468, Mongolia 98, Nepal 708,
South Korea 347, Sri Lanka 757, Taiwan 23, Thailand 180, Vietnam 73` (`component_count`). Pakistan and Philippines are
still absent.

**Where the list comes from**: BFF `resource=countries` → Lambda `/browse/countries` (`frontend/app/api/browse/route.ts:56-57`
→ `backend/browse/handler.py:166-168`) → `COUNTRIES_SQL` (`backend/browse/countries.py:24-32`):
`catalog.v_destination d JOIN catalog.v_tour_component c ON c.destination_id = d.destination_id GROUP BY d.country`.
`v_tour_component` (CIS mig 258, lines 157-189) = `geo.tour_place` of live tours **inner-joined to `shared.destinations`**
(not suspect, not a duplicate). A component therefore counts only when its place name has been geocoded into a
destination, and the country shown is the **destination's** country.

**Root cause (Pakistan, Philippines): CIS code.**
- `services/places/guards.py:21-50`: `COUNTRY_ISO2`, `ISO2_COUNTRY`, `ISO2_ISO3` and `BBOX` list 19 countries.
  Pakistan and Philippines are missing, while the comment at :18-20 says the list "equals the `chk_raw_tours_country`
  constraint". Mig **197** (`api/migrations/197_country_pakistan_philippines.sql`, 01/10, AA-653) added both
  countries to that constraint, and the guard was not updated.
- Effect: `canonical_country("Pakistan")` returns None. In `services/places/locate.py:146,153`, `parse_answer` turns
  every model answer for a PK/PH name into None, so the outcome is `unknown_to_model` (`locate.py:205`). If an answer got
  further, `point_ok` would return `not_aa_country` (`guards.py:103-104`). `geocode_pending` → `store.mark_name`
  (`services/places/store.py:660-677`) counts a try (pending again in 1 day, `unknown` after 3 tries). No
  `shared.destinations` row → `v_tour_component` has no PK/PH rows → no country in the list, no stops in the graph,
  tour-route `none`, and no "Where you go" map. Every retry also **pays** for a model locate call that cannot succeed.
- The AA-905 runs built PK/PH places on 26/10: trial3 had 1 PK, to50 had 4 PK + 3 PH, lot 5 had 13 PK + 8 PH, and lot 6
  had 32 PH. Their names are now on the 1-day retry loop.
- The same gap reaches `AA_ISO2` in `services/aa_content/validate.py:20-28` (AA content country codes) and Geoapify's
  country filter (`services/places/geocoder.py:289`). `services/catalog_http/geo.py:28-29` already has PK/PH, so the
  CIS country lists disagree with each other.

**Cambodia and Kyrgyzstan**: these are destination countries of cross-border tours (for example the Thailand tour
e53c44c6 crosses into Cambodia). This matches the query's design (the planner filters **places** on the map), and
`/browse/routes` also matches legs by `v_tour_leg.countries`. Not a bug. If product wants only countries that sell a
tour, change `COUNTRIES_SQL` to group by the tour's country (`JOIN catalog.v_tour t ON t.source_id = c.source_id`,
`GROUP BY t.country`). The catalogue pages already use the tour-country list
(`/browse/catalog/destinations`, `backend/browse/catalog.py:608-623`).

### F3 fix

1. **CIS code** (`services/places/guards.py`):
   - Add `"pakistan": "pk", "philippines": "ph"` to `COUNTRY_ISO2`, `"pk": "Pakistan", "ph": "Philippines"` to
     `ISO2_COUNTRY`, and `"pk": "PAK", "ph": "PHL"` to `ISO2_ISO3`.
   - Add BBOX rows (±0.3° like the others): `"pk": (23.3, 37.4, 60.6, 78.1)`, `"ph": (4.3, 21.4, 116.6, 126.9)`.
   - Optional aliases: `"islamic republic of pakistan"`, `"republic of the philippines"`.
   - Add a drift test so this cannot happen again: every value of `chk_raw_tours_country` (mig 197/281 list) passes
     `canonical_country()` and has a BBOX row. Longer term, read the list from `shared.countries` (mig 279).
   - Check that the locate prompt does not hard-code the country list (`services/places/locate.py` SYSTEM_PROMPT).
2. **Data, after the deploy** (worker, about $0.1–0.3 of model calls, Geoapify free):
   - Reset the PK/PH names, as a write by an approved step through `cis_app` (DML on `geo.place_name`):
     `UPDATE geo.place_name SET status='pending', tries=0, last_error=NULL, next_retry_at=now() WHERE lower(country) IN ('pakistan','philippines') AND status IN ('pending','unknown');`
   - Enqueue one `place_geocode` (no admin endpoint; `shared.jobs.registry.enqueue(pool, 'place_geocode', {'reason': 'aa990_f3'})`
     from the worker). Re-running place_extract is not enough: an unchanged build returns `skipped_unchanged` and queues no geocode.
   - The geocode job relinks `tour_place` / `tour_day` and enqueues `tour_graph_build`. Then re-curl `resource=countries`
     (Pakistan and Philippines should appear) and tour-route for the 6 PK/PH sample tours.
3. **TripPlanner**: nothing.

## Queries

`cis_app` (container `DATABASE_URL`) can read `geo.*`, `shared.*`, `silver_aa_internal.*` and `gold_aa_internal.*`.
It has **no USAGE on schema `catalog`** and none on `tripplanner`. The two FORCE-RLS tour tables need the master tenant
set inside the same transaction. Run each block in one transaction:

```sql
BEGIN;
SELECT set_config('app.tenant_id', '00000000-0000-0000-0000-000000000001', true);
-- query
COMMIT;
```

The shared CTE `live` (same as `services/places/store.py:16-26`):

```sql
WITH live AS (
  SELECT pt.tour_id, COALESCE(rt.source_group_id, rt.tour_id)::text AS source_id, rt.country,
         pt.updated_at AS content_updated_at, pt.generated_content_id
    FROM gold_aa_internal.published_tours pt
    JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = pt.tour_id
   WHERE pt.tenant_id = '00000000-0000-0000-0000-000000000001'::uuid
     AND pt.master_status = 'active' AND pt.deleted_at IS NULL
     AND rt.source_status = 'active' AND rt.deleted_at IS NULL)
```

### F3

**Q1 — reproduce the planner country list (cis_app)**: should return the same 14 rows as the endpoint.
```sql
<live CTE>
SELECT d.country, count(*) AS component_count, count(DISTINCT gp.source_id) AS tours
  FROM geo.tour_place gp
  JOIN live l ON l.source_id = gp.source_id
  JOIN shared.destinations d ON d.id = gp.destination_id AND d.geo_status <> 'suspect' AND d.duplicate_of IS NULL
 GROUP BY d.country ORDER BY d.country;
```

**Q1m — the same from the views TripPlanner reads (needs master / DB Migrate run-script, or the `tripplanner` role)**:
```sql
SELECT d.country, COUNT(c.component_id) FROM catalog.v_destination d
  JOIN catalog.v_tour_component c ON c.destination_id = d.destination_id
 WHERE d.country <> '' GROUP BY d.country ORDER BY 1;
```

**Q2 — PK/PH place-name status (cis_app)**: expected to show all pending or unknown, `last_error` = `unknown_to_model` or `not_aa_country`, and 0 resolved.
```sql
SELECT country, status, left(last_error, 40) AS err, count(*), max(tries) AS max_tries,
       min(next_retry_at) AS next_retry, max(updated_at) AS last_try
  FROM geo.place_name WHERE lower(country) IN ('pakistan','philippines')
 GROUP BY 1,2,3 ORDER BY 1,2,4 DESC;
```

**Q3 — PK/PH builds exist but nothing is linked (cis_app)**:
```sql
<live CTE>
SELECT l.country, tb.status, count(*) AS tours,
       sum((tb.counts->>'components')::int) AS components, sum((tb.counts->>'places_linked')::int) AS places_linked,
       sum((tb.counts->>'nights_linked')::int) AS nights_linked, min(tb.built_at), max(tb.built_at)
  FROM live l LEFT JOIN geo.tour_build tb ON tb.source_id = l.source_id
 WHERE lower(l.country) IN ('pakistan','philippines') GROUP BY 1,2;
SELECT country, count(*) FROM shared.destinations WHERE lower(country) IN ('pakistan','philippines') GROUP BY 1;
```

**Q4 — where Cambodia and Kyrgyzstan come from (cis_app)**:
```sql
<live CTE>
SELECT d.country AS place_country, l.country AS tour_country, count(DISTINCT l.source_id) AS tours,
       count(*) AS components, (array_agg(DISTINCT d.name))[1:8] AS sample_places
  FROM geo.tour_place gp JOIN live l ON l.source_id = gp.source_id
  JOIN shared.destinations d ON d.id = gp.destination_id AND d.geo_status <> 'suspect' AND d.duplicate_of IS NULL
 WHERE d.country IN ('Cambodia','Kyrgyzstan') GROUP BY 1,2 ORDER BY 1,3 DESC;
```

**Q5 — catalogue countries vs planner countries in one table (cis_app)**:
```sql
<live CTE>
, tour_c AS (SELECT country, count(*) AS tours FROM live GROUP BY 1),
  place_c AS (SELECT d.country, count(*) AS comps FROM geo.tour_place gp JOIN live l ON l.source_id = gp.source_id
                JOIN shared.destinations d ON d.id = gp.destination_id AND d.geo_status <> 'suspect' AND d.duplicate_of IS NULL
               GROUP BY 1)
SELECT coalesce(t.country, p.country) AS country, t.tours, p.comps
  FROM tour_c t FULL JOIN place_c p ON p.country = t.country ORDER BY 1;
```

### F2

**Q6 — graph builds (cis_app)**: confirms a build after lot 7/8 (26/10 ≥ 14:28Z) and that the current build is the newest.
```sql
SELECT build_id, built_at, is_current, job_id, stats->'tours' AS tours, stats->'stops' AS stops, stats->'legs' AS legs
  FROM geo.graph_build ORDER BY built_at DESC;
SELECT id, status, created_at, finished_at, payload->>'reason' AS reason, payload->>'coalesced' AS coalesced
  FROM shared.job WHERE kind = 'tour_graph_build' AND created_at > now() - interval '3 days' ORDER BY created_at DESC LIMIT 15;
```

**Q7 — the 12 short tours: graph build vs content and place build time, stop span (cis_app)**:
```sql
<live CTE>
, ids(sid) AS (VALUES ('c58222c8-ac29-418d-ad82-da954cdfff1f'),('51285758-4fa2-453c-b54b-3d056e163f38'),
   ('5122bd9b-bc28-478d-a76e-dab82ff961ee'),('a90ddcc5-2703-48ca-b60b-a80954860ed5'),('de1eea74-286f-4c12-b075-bc8a7609779e'),
   ('2b9070e3-3667-4a99-a9b1-eca0d416e7d4'),('d9b10288-9d20-4b24-87af-6cc814e5df17'),('cd8bc159-a99f-49e6-8bed-efa0b673c352'),
   ('74f84466-512a-4df7-9ee5-353b222c547e'),('e53c44c6-7cfd-47d0-9c1a-1627868d1b15'),('700044ca-18e8-405a-b9af-54739cd6c0c8'),
   ('ca1d7500-a3a6-4278-83ad-fee7a9e5f670')),
  cur AS (SELECT build_id, built_at FROM geo.graph_build WHERE is_current)
SELECT l.country, left(l.source_id, 8) AS src, l.content_updated_at, tb.built_at AS places_built, tb.status AS place_status,
       (tb.tour_id = l.tour_id) AS build_on_live_version, cur.built_at AS graph_built,
       (tb.built_at <= cur.built_at) AS graph_after_places,
       (SELECT count(*) FROM geo.tour_day td WHERE td.source_id = l.source_id) AS days_extracted,
       (SELECT count(*) FROM geo.tour_day td WHERE td.source_id = l.source_id AND td.overnight_destination_id IS NOT NULL) AS nights_linked,
       (SELECT count(*) FROM geo.tour_stop s WHERE s.build_id = cur.build_id AND s.source_id = l.source_id) AS stop_days,
       (SELECT min(day_index) || '-' || max(day_index) FROM geo.tour_stop s WHERE s.build_id = cur.build_id AND s.source_id = l.source_id) AS stop_span,
       (SELECT count(*) FROM geo.tour_place gp WHERE gp.source_id = l.source_id AND gp.destination_id IS NULL) AS places_unlinked,
       tb.counts->>'names_new_pending' AS names_pending_at_build
  FROM live l JOIN ids ON ids.sid = l.source_id CROSS JOIN cur
  LEFT JOIN geo.tour_build tb ON tb.source_id = l.source_id ORDER BY 1, 2;
```
How to read it: `graph_after_places` false → the graph is stale (rebuild). `build_on_live_version` false → place build
predates the live version (re-extract). `places_unlinked` > 0 or `nights_linked` < `days_extracted` → names not yet
geocoded (Class B data).

**Q8 — per day, why a day has no stop (cis_app)** (shown here for the three Class B tours; add others as needed):
```sql
WITH cur AS (SELECT build_id FROM geo.graph_build WHERE is_current)
SELECT left(td.source_id, 8) AS src, td.day_index, left(td.title, 50) AS title, td.anchor_place,
       td.overnight_destination_id IS NOT NULL AS night_linked, pn.status AS anchor_status, pn.tries, left(pn.last_error, 50) AS anchor_err,
       s.destination_id IS NOT NULL AS has_stop, s.source AS stop_source,
       (SELECT count(*) FROM geo.tour_place gp WHERE gp.source_id = td.source_id AND gp.day_index = td.day_index) AS places,
       (SELECT count(*) FROM geo.tour_place gp WHERE gp.source_id = td.source_id AND gp.day_index = td.day_index AND gp.destination_id IS NOT NULL) AS places_linked,
       (SELECT string_agg(DISTINCT p2.status || ':' || coalesce(left(p2.last_error, 25), ''), ', ')
          FROM geo.tour_place gp JOIN geo.place_name p2 ON (p2.name_norm, p2.country_norm, p2.locality_norm) = (gp.name_norm, gp.country_norm, gp.locality_norm)
         WHERE gp.source_id = td.source_id AND gp.day_index = td.day_index AND gp.destination_id IS NULL) AS unlinked_name_status
  FROM geo.tour_day td CROSS JOIN cur
  LEFT JOIN geo.place_name pn ON (pn.name_norm, pn.country_norm, pn.locality_norm) = (td.anchor_norm, td.anchor_country_norm, td.anchor_locality_norm)
  LEFT JOIN geo.tour_stop s ON s.build_id = cur.build_id AND s.source_id = td.source_id AND s.day_index = td.day_index
 WHERE td.source_id IN ('51285758-4fa2-453c-b54b-3d056e163f38','a90ddcc5-2703-48ca-b60b-a80954860ed5',
                        '74f84466-512a-4df7-9ee5-353b222c547e','2b9070e3-3667-4a99-a9b1-eca0d416e7d4')
 ORDER BY 1, 2;
```

**Q9 — is geocoding stuck behind the credit guard? (cis_app)**
```sql
SELECT status, count(*), count(*) FILTER (WHERE next_retry_at <= now()) AS due_now FROM geo.place_name GROUP BY 1;
SELECT date_trunc('day', called_at) AS utc_day, provider, endpoint, sum(requests) AS requests, sum(credits) AS credits
  FROM geo.geocode_call WHERE called_at > now() - interval '3 days' GROUP BY 1,2,3 ORDER BY 1 DESC;
SELECT id, status, created_at, finished_at, result->>'names' AS names, result->>'resolved' AS resolved,
       result->>'deferred' AS deferred, result->>'unknown' AS unknown, result->>'failed' AS failed,
       result->>'stopped_credit_limit' AS credit_stop
  FROM shared.job WHERE kind = 'place_geocode' AND created_at > now() - interval '3 days' ORDER BY created_at DESC LIMIT 15;
```

**Q10 — the whole catalogue: graph route span vs tour length (needs master / run-script, or the `tripplanner` role; catalog views)**:
```sql
WITH span AS (SELECT source_id, min(day_index) AS f, max(day_index) AS l, count(*) AS stop_days FROM catalog.v_tour_stop GROUP BY 1),
     n AS (SELECT t.source_id, t.country, GREATEST(coalesce(t.duration_days, 0),
                  (SELECT count(*) FROM catalog.v_tour_day d WHERE d.tour_id = t.tour_id)) AS days FROM catalog.v_tour t)
SELECT n.country, count(*) AS tours, count(s.source_id) AS with_graph,
       count(*) FILTER (WHERE s.l - s.f + 1 < n.days) AS short,
       count(*) FILTER (WHERE s.f > 1) AS starts_late, count(*) FILTER (WHERE s.l < n.days) AS ends_early,
       count(*) FILTER (WHERE s.l - s.f + 1 < 0.5 * n.days) AS below_half
  FROM n LEFT JOIN span s USING (source_id) GROUP BY ROLLUP (n.country) ORDER BY 1 NULLS LAST;
```

## Not done here

- No DB read, so these points are inferred from the code, the AA-905 lot files and live curls, and need Q2/Q7/Q8/Q9 to confirm:
  the Class B per-day causes, the PK/PH name statuses, and whether credit-limit deferrals left names pending.
- Narrate, search and the `/plan` UI were not opened (no LLM calls, no writes).
