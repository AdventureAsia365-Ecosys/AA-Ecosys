# ADR 0002 — Only CIS writes content; other apps read it through views

- **Status:** Accepted (01/10/2026, S207 — Nghiệp: "không để các app khác ngoài CIS ghi nội dung").
- **Scope:** AA-Ecosys (AA-CIS-App, AA-TripPlanner-Web, AA-CIS-Infra, future AA-Booking).
- **Implements / tightens:** ADR 0001 decision 1 ("CIS is the content system of record").

## Context

ADR 0001 made CIS the content system of record, but nothing enforced who may write. On 01/10/2026
the TripPlanner still created and edited content in the shared database:

- `shared.destinations`: rows inserted by `extraction/geocode.py` and `locate.py`, and coordinates
  or country rewritten by `regeocode_outliers.py` and `backfill_country.py`.
- `tripplanner.itinerary_components`, `tour_stop`, `tour_graph_*`: which places each AA tour visits,
  derived from CIS tours but computed and stored by the TripPlanner.

This content already has downstream users inside CIS. AA photos (AA-708) are matched to places on a
tour's itinerary, and covers are set on `shared.destinations`. Two writers to the same data means no
single place for fixes, reruns or audit. The S207 clean rerun showed the cost: `shared.destinations`
still held places from the tours published before the reset, and only the TripPlanner could
rebuild them.

## Decision

1. **Content is written only by CIS.** Content covers:
   - tours and their versions;
   - atoms and segments;
   - places (`shared.destinations`) and their coordinates;
   - a tour's itinerary places and the tour graph;
   - photos and their matches.

   Every create, update and delete of content runs in CIS, as a CIS job or admin action, and is
   observable on an admin page.
2. **Other apps read content through published views**, never the tables:
   - `shared.v_tour_photos` and `shared.v_destination_photos` (AA-708, migration 200);
   - catalog and tour-graph views under ADR 0001's read model.

   A view is a contract. Its table may change and the view stays.
3. **Other apps write only their own state** in their own schema: TripPlanner sessions, drafts,
   customers and trip events; AA-Booking cases, orders and payments. One shared exception: the
   telemetry log `shared.llm_call_log` (append-only cost rows, not content).
4. **Enforced in the database, not only in code.** Each app connects with its own DB role. Non-CIS
   roles get `SELECT` on the content schemas and views, `INSERT` only on `shared.llm_call_log`, and
   full rights only on their own schema.

## Consequences

- **The place pipeline moves to CIS.** Today it runs in the TripPlanner: extraction of a tour's
  places, geocoding through Mapbox, the `destinations` upsert, and the `tour_stop` / tour-graph build.
  - It becomes CIS job kinds, run after A3 atomize for each rerun wave.
  - The TripPlanner keeps only its trip-planning logic and reads the results through views.
  - The Mapbox key moves to CIS secrets.
- **Until that migration ships**, the TripPlanner's existing writers are frozen. They are not run
  for new waves. CIS-side photo place matching waits for the CIS place pipeline.
- **AA-Booking (AA-679 catalog sync)** follows this ADR from its first commit and reads views only.
- **Revisit** if a second app ever has to author content of its own, for example agency-written
  tours. It would then write through a CIS API, never straight to the tables.
