# Cross-app contracts

Every event or read model one app exposes to another is described here as a JSON Schema
`<name>.v<major>[.<minor>].json`. Pattern (ecosystem blueprint, S235, approved by Nghiệp 14/10/2026):
**outbox → pull consumer → inbox**.

## Rules
1. **Owner.** The producing app owns the contract file and the read view (`<schema>.v_<event>_outbox` or a catalog
   view). Consumers never read the producer's tables.
2. **Versioning.**
   - *Minor* (`1` → `1.1`): additive only — new optional/required fields the consumer may ignore, wider enums,
     nullable where it was not. The producer may start sending it at once; consumers must accept every minor of
     their major (`version` enum).
   - *Major* (`1` → `2`): anything that removes, renames or narrows a field. The producer writes **both** majors
     (dual-write, two views) for an agreed window (default 30 days), then drops the old one after every consumer
     confirms.
   - Never edit a published contract file in place except to fix a typo in a description; add a new file.
3. **Idempotency.** Every event carries `idempotency_key` (string, unique per producer + contract). The consumer
   stores it in its own `inbox_events` with `UNIQUE (source, contract, idempotency_key)` and processes each key
   once. Catalog sync keys are `(source_system, source_id)` — the CIS id; `external_ref` in older CIS docs means the
   same thing.
4. **Reading.** Consumers pull with a job (`<app>.job`, kind `<prefix>_<event>_pull`, e.g. `bk_inquiry_pull`) and
   must not use the producer's BIGSERIAL id as the only cursor (out-of-order commits): anti-join against the inbox
   or keep a lag window.
5. **Grants.** The producer's own migration grants `SELECT` on the view to the consumer role, without an
   `IF EXISTS(role)` guard (a guarded no-op still registers the version). The consumer role must exist first.
6. **Ack / status back.** A consumer that changes state the producer's users care about publishes its own event
   (e.g. `trip_case.status_changed` from AA-Booking) — no writes into another app's schema.
7. **CI.** Producer tests validate a sample payload against the schema; consumer tests parse the same sample.

## Registry
| Contract | Producer → consumer | View | Status |
|---|---|---|---|
| `inquiry.submitted.v1.json` | TripPlanner → AA-Booking | `tripplanner.v_inquiry_outbox` (tp-008) | superseded by 1.1 (additive) |
| `inquiry.submitted.v1.1.json` | TripPlanner → AA-Booking | same | current; grant to `booking` pending (tp-009) |
| `catalog.tour.v1.json` | CIS → AA-Booking, TripPlanner | schema `catalog` (CIS 225): `v_tour` + `v_tour_day`, `v_tour_place`, `v_tour_photo`; also `v_destination`, `v_destination_photo` | read model drafted (AA-679, migration 225 not yet applied); consumers poll `v_tour` and re-sync on `content_hash` (`updated_at` is not a change cursor: an in-place content edit does not move it). Events `catalog.tour.published/updated/trashed` (outbox) = next additive minor |
| `catalog.tour.v1.1.json` | CIS → AA-Booking, TripPlanner | same views; CIS 228 appends `located_by`, `precision` to `v_tour_place` and `geo_status`, `located_by`, `precision` to `v_destination` | additive over 1 (AA-712); live once CIS 228 is applied on Dev. `destination_id` comes from the place pipeline first; suspect / duplicate destinations are never returned |
| `catalog.graph.v1.json` | CIS → TripPlanner (AA-Booking later) | schema `catalog` (CIS 228, views only): `v_tour_component`, `v_tour_day_route`, `v_tour_stop`, `v_tour_leg`, `v_graph_node`, `v_graph_edge`, `v_tour_junction` over CIS-internal `geo` | drafted (AA-712, ADR 0007); 228 not yet applied. Read on demand, no events; no top-k vector function in v1 (S237 D7). TripPlanner column mapping in each row definition |
| `trip_case.status_changed.v1` | AA-Booking → TripPlanner | `booking.v_trip_case_status_outbox` | planned |
