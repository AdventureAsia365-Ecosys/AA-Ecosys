# AA-712 slice 6b — browse readers, legacy vs cis parity (Laos)

TripPlanner branch `feat/aa-712-slice-6b-places-source`. The browse readers (tiles, countries, by-country,
destination detail, search, routes, tour-route) read the frozen TripPlanner tables with
`PLACES_SOURCE=legacy` (default) and the CIS catalog views of migration 228 with `PLACES_SOURCE=cis`.
This file compares the two paths for Laos, the country CIS has built (46 / 46 tours, batch (b) 00:08Z).

## Status

- **Dev run: PENDING (orchestrator).** The build subagent cannot run ECS exec (subagent guardrail hook),
  and its HTTP read of the live BFF was refused, so the Dev numbers below still have to be produced. The
  runner is ready and was dry-run end to end on a local Postgres (section "Local dry run").
- What to expect (from the code, the local run and the integration test): same countries / by-country /
  tiles counts wherever the frozen tables and `catalog.v_tour_component` hold the same tours; routes and
  tour-route differ where the frozen graph keyed a tour by a published tour_id that is no longer live, or
  by a source_id (re-uploaded tours); search returns **more** destinations on cis, because legacy search
  only ranks components whose `source_tour_id` is a live published tour_id.

## How to run (read-only, ~2-5 min)

```bash
cd /home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-14-S237-lane-backlog
python3 aa712-6b-parity.py build /home/nghiep/projects/AA-Ecosys/.tmp-session/wt/s237-tp-6b /home/nghiep/projects/AA-Ecosys/.tmp-session/s237/p6b.zip
TMO=900 /home/nghiep/projects/AA-Ecosys/.tmp-session/s237/exec.sh /home/nghiep/projects/AA-Ecosys/.tmp-session/s237/p6b.zip > /home/nghiep/projects/AA-Ecosys/.tmp-session/s237/p6b_out.json
python3 aa712-6b-parity.py report /home/nghiep/projects/AA-Ecosys/.tmp-session/s237/p6b_out.json
```

`exec.sh` downloads the file as `/tmp/s.py` and runs `python3 /tmp/s.py`; Python runs a zip archive
whatever its name (checked locally), so the zip needs no wrapper. The runner:

- reads the DSN from `aa-cis/dev/rds`, opens two connections, both `default_transaction_read_only = on`;
  one does `SET ROLE tripplanner` and runs the real TripPlanner `handler.route()` (bundled from the branch)
  twice, `legacy` then `cis`, and reads 8 Laos component embeddings (frozen table) as fixed query vectors;
  the other (admin) only maps legacy tour keys to catalog source_ids (`silver_aa_internal.raw_tours`,
  FORCE RLS, so it sets `app.tenant_id` = AA master tenant for its session; `coverage.raw_tours_mapped`
  must be > 0 on Dev, else the mapping did not work and the routes "same tour sets" column is meaningless);
- makes no Bedrock call (search gets an injected embedder) and writes nothing;
- prints one JSON line: coverage, per-reader counts and timings, search top-10 overlap, tour-route
  status / match per live Laos tour, destination-detail component counts per destination.

Paste the `report` output under "Dev results" and fill the verdict.

## Dev results

_(pending — paste `report` output here)_

## Verdict

_(pending)_ Pass = every reader 200 on cis; countries / by-country / tiles counts within the expected
differences above; routes for Laos give at least as many proposals on cis for each duration; tour-route
200 on cis for every tour CIS built (46); cis timings acceptable for the browse Lambda (tiles per cell and
search per query well under 1 s).

## Local dry run (throwaway Postgres 16, synthetic 2 Laos + 1 Vietnam tours)

Same fixture as `backend/tests/test_places_source_pg.py` (view stand-in tables with the 228 column names;
legacy key quirk: one tour keyed by its source_id). It only proves the runner works end to end and that both
SQL paths execute; the tour-set "False" rows come from the fixture's raw_tours mapping, not from the readers.

Role: `postgres`, country: Laos.

#### Coverage (tour graph)

| | value |
|---|---|
| catalog_live_tours | 2 |
| legacy_graph_tours | 2 |
| legacy_key_is_live_source_id | 1 |
| legacy_key_is_tour_id_mapped | 0 |
| legacy_key_not_live | 1 |
| legacy_graph_live | 1 |
| cis_graph_tours | 2 |
| cis_graph_live | 2 |
| in_both | 1 |

#### Readers

| Reader | legacy | cis |
|---|---|---|
| /browse/countries: Laos components | 9 (1 ms) | 9 (0 ms) |
| /browse/by-country: destinations / components | 4 / 9 (1 ms) | 4 / 9 (0 ms) |
| /browse/tiles, 80 one-degree cells: destinations / components / total ms | 5 / 12 / 0 | 5 / 12 / 0 |
| /browse/tiles/10_100_10: destinations (ms) | 4 (0) | 4 (0) |
| /browse/tour-route over 2 live tours: status:match | {'200:tour_graph': 1, '200:places': 1} (4 ms) | {'200:tour_graph': 2} (1 ms) |
| cis located_by / precision (by-country) | | {'llm': 1, 'geoapify': 3} / {'area': 1, 'point': 3} |

#### Destination detail (union of both by-country lists)

4 destinations: same component count 4, cis more 0, cis fewer 0; only in legacy 0, only in cis 0. Time legacy 1 ms, cis 0 ms. Largest differences (id, legacy, cis): [['00000000-0000-0000-0000-000000000001', 2, 2], ['00000000-0000-0000-0000-000000000002', 1, 1], ['00000000-0000-0000-0000-000000000003', 5, 5], ['00000000-0000-0000-0000-000000000004', 1, 1]].

#### Routes (/browse/routes, country = Laos)

| days | legacy proposals (whole / chains) | cis proposals (whole / chains) | same tour sets | pinned days legacy / cis | ms legacy / cis |
|---|---|---|---|---|---|
| 3 | 2 (1 / 0) | 2 (1 / 0) | False | 6/6 / 6/6 | 2 / 2 |
| 5 | 3 (2 / 1) | 3 (2 / 1) | False | 12/12 / 12/12 | 1 / 1 |
| 7 | 2 (1 / 1) | 2 (1 / 1) | False | 11/11 / 11/11 | 1 / 1 |
| 9 | 1 (0 / 1) | 1 (0 / 1) | False | 7/7 / 7/7 | 1 / 1 |
| 10 | 1 (0 / 1) | 1 (0 / 1) | False | 7/7 / 7/7 | 1 / 1 |
| 12 | 0 (0 / 0) | 0 (0 / 0) | True | 0/0 / 0/0 | 0 / 1 |
| 14 | 0 (0 / 0) | 0 (0 / 0) | True | 0/0 / 0/0 | 0 / 0 |
| 16 | 0 (0 / 0) | 0 (0 / 0) | True | 0/0 / 0/0 | 0 / 0 |
| 21 | 0 (0 / 0) | 0 (0 / 0) | True | 0/0 / 0/0 | 0 / 0 |

#### Search (8 fixed query vectors = embeddings of Laos components; no Bedrock call)

| q | country filter | results legacy / cis | top-10 overlap | same top-1 | ms legacy / cis |
|---|---|---|---|---|---|
| 0 | False | 4 / 5 | 4 | False | 8 / 1 |
| 0 | True | 3 / 4 | 3 | False | 1 / 1 |
| 1 | False | 4 / 5 | 4 | False | 2 / 1 |
| 1 | True | 3 / 4 | 3 | False | 1 / 1 |
| 2 | False | 4 / 5 | 4 | True | 2 / 1 |
| 2 | True | 3 / 4 | 3 | True | 1 / 1 |
| 3 | False | 4 / 5 | 4 | False | 1 / 1 |
| 3 | True | 3 / 4 | 3 | False | 1 / 0 |
| 4 | False | 4 / 5 | 4 | True | 2 / 0 |
| 4 | True | 3 / 4 | 3 | True | 1 / 1 |
| 5 | False | 4 / 5 | 4 | False | 2 / 1 |
| 5 | True | 3 / 4 | 3 | False | 1 / 0 |
| 6 | False | 4 / 5 | 4 | True | 1 / 0 |
| 6 | True | 3 / 4 | 3 | True | 1 / 0 |
| 7 | False | 4 / 5 | 4 | True | 2 / 1 |
| 7 | True | 3 / 4 | 3 | True | 1 / 0 |

Tour-route: both 200 on 2 tours (2 with the same day count); legacy 200 but cis 404: 0 []; legacy 404 but cis 200: 0.
