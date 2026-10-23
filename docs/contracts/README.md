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
8. **HTTP contracts.** A contract served over HTTP (one app calling another's API, no view grant: the partner CRM
   holds no grant on any other schema, root ADR 0008a) is an OpenAPI 3.1 file `<name>.v<major>.openapi.yaml`. Its
   component schemas are JSON Schema 2020-12, every object sets `additionalProperties: false`, money is a decimal
   string with an ISO 4217 currency, and personal-data fields carry `x-pii: <class>` (the DM-6.1 classes). The
   major is in the URL prefix; a breaking change is a new major served in parallel, as in rule 2.
9. **Samples and CI.** Each HTTP contract has samples in [`samples/<contract>/`](samples/README.md): valid payloads,
   and the rejected payloads the design requires. The root workflow `contracts.yml`
   ([`tools/contracts/check_contracts.py`](../../tools/contracts/check_contracts.py)) validates every contract file,
   every sample, and each contract's field policy (forbidden fields such as `trip_count`, `revenue` and `pii:` in
   `crm.ops.v1`, `supplier_net` in `booking.b2b.v1`). The policy lives in the checker, not in the contract file.

## Registry

| Contract | Producer → consumer | View | Status |
|---|---|---|---|
| `inquiry.submitted.v1.json` | TripPlanner → AA-Booking | `tripplanner.v_inquiry_outbox` (tp-008) | superseded by 1.1 (additive) |
| `inquiry.submitted.v1.1.json` | TripPlanner → AA-Booking | same | superseded by 1.2 (additive); SELECT to `booking` granted (tp-009, applied on Dev) |
| `inquiry.submitted.v1.2.json` | TripPlanner → AA-Booking | same | current once the AA-830 TripPlanner change is deployed: each leg adds the catalog tour key `source_system` + `source_id` (resolved against `catalog.v_tour`; both null when unresolvable), `source_tour_id` kept. AA-Booking accepts 1, 1.1 and 1.2 and stores the key on `booking.trip_case_legs` (bk-011) |
| `catalog.tour.v1.json` | CIS → AA-Booking, TripPlanner | schema `catalog` (CIS 225): `v_tour` + `v_tour_day`, `v_tour_place`, `v_tour_photo`; also `v_destination`, `v_destination_photo` | live (AA-679, CIS 225 applied on Dev 14/10/2026); consumers poll `v_tour` and re-sync on `content_hash` (`updated_at` is not a change cursor: an in-place content edit does not move it). Events `catalog.tour.published/updated/trashed` (outbox) = next additive minor |
| `catalog.tour.v1.1.json` | CIS → AA-Booking, TripPlanner | same views; CIS 228 appends `located_by`, `precision` to `v_tour_place` and `geo_status`, `located_by`, `precision` to `v_destination` | additive over 1 (AA-712); live (CIS 228 applied on Dev 15/10/2026). `destination_id` comes from the place pipeline first; suspect / duplicate destinations are never returned |
| `catalog.graph.v1.json` | CIS → TripPlanner (AA-Booking later) | schema `catalog` (CIS 228, views only): `v_tour_component`, `v_tour_day_route`, `v_tour_stop`, `v_tour_leg`, `v_graph_node`, `v_graph_edge`, `v_tour_junction` over CIS-internal `geo` | live (AA-712, ADR 0007; CIS 228 applied on Dev 15/10/2026). Read on demand, no events; no top-k vector function in v1 (S237 D7). TripPlanner column mapping in each row definition |
| `catalog.graph.v1.1.json` | CIS → TripPlanner | v1 + `catalog.v_component_embedding` (CIS 253, AA-847): the HNSW top-k scan object over the components `v_tour_component` shows (live, usable place; no check after the scan), not security_barrier, granted to `tripplanner` only; liveness of every place / graph view from the internal `catalog._live_tour` (same rows and columns) | additive over v1; consumers accept 1 and 1.1. TripPlanner `vector_topk.CIS` (slice 6c) reads it |
| `catalog.tour.v1.2.json` | CIS → AA-Booking, TripPlanner | same views; CIS 256 (AA-847) appends the day stretch of a line (`segment`, `segment_basis`, `segment_from_destination_id`, `segment_to_destination_id`, `segment_km`) to `v_tour_place`, `precision` gains `line`; `v_destination` appends `shape_kind`, `shape_status`, `shape_source`, `length_km`, never-null `min_lat` / `min_lng` / `max_lat` / `max_lng`, `shape_lo` | additive over 1.1; planned (CIS 256 not applied yet). Lines are drawn, never a pin (owner decision S246) |
| `catalog.graph.v1.2.json` | CIS → TripPlanner | v1.1 + `v_tour_component` appends `precision` and the day stretch; `destination_shapes` = `catalog.v_destination_shape` (CIS 256, TripPlanner only): a line destination's geometry by id | additive over v1.1; planned (CIS 256 not applied yet) |
| `trip_case.status_changed.v1` | AA-Booking → TripPlanner | `booking.v_trip_case_status_outbox` | planned |
| `crm.ops.v1.openapi.yaml` | AA-Partner → CIS admin (L1 console S-01) | HTTP `/crm/ops/v1`, WORKFORCE `cis-admin` token | proposed (AA-928; ADR 0010, 0006b). No trip, revenue, margin, commission or personal-data field (CI). Built by AA-933 / AA-941 |
| `booking.b2b.v1.openapi.yaml` | AA-Booking → AA-Partner | HTTP `/booking/b2b/v1` (prefix provisional until ADR 0013), M2M token + `X-AA-Tenant-Id` | proposed (AA-928; ADR 0005a). `b2b_price` only, never `supplier_net` (CI); pax counts only. Built by AA-972…AA-975; 409 `tour_not_served` + withdrawn products in the delta: AA-986 (ADR 0015) |
| `catalog.http.v1.openapi.yaml` | CIS → AA-Partner | HTTP `/catalog/v1` over the `catalog` views + AA-authored content (prep packs, starter templates, campaign blocks) | proposed (AA-928). No prices, no personal data. Built by AA-976 / AA-977 |
| `tenant.membership.v1.openapi.yaml` | CIS → AA-Partner | HTTP `/tenant/membership/v1` over `catalog.v_tenant_member`, keyed by `(iss, sub)` | proposed (AA-928; ADR 0006b). Content studio role only, never a CRM role; no email or name (CI). Built by AA-978 (AA-813 re-scoped) |
