# ops.overview.v1 and ops.data_coverage.v1 — owner contract views read by the CIS admin

Owner apps publish operational numbers to the CIS admin as **views in their own schema**, granted `SELECT` to the CIS
runtime role `cis_app` in their own migration (contracts rule 5; `docs/database/schema-ownership.md` rule 2). The
reader never gets a table: every other object of the owner's schema stays 42501 for `cis_app` (isolation probe cells
`cross.cis_app.booking.customers`, `cross.cis_app.tripplanner.sessions`). The grants are mirrored in AA-CIS-Infra
`db/owners.yaml` `consumer_grants`, the isolation probe `CONSUMER_GRANTS` and the RLS catalogue rule `g` allow-list
(canonical in AA-CIS-App `tests/integration/rls_catalogue_rules.py`, byte copy in AA-CIS-Infra).

Rules for both families:

- Views are named `<schema>.v_ops_*`, owned by the schema owner (`bk_owner`, `tp_owner`), `SELECT` only to `cis_app`;
  the owner's runtime role (`booking`, `tripplanner`) is `SELECT` only too (DML revoked from the default privileges).
- **Metric names and column lists are append-only**: add a metric or a column, never rename or drop one in place. A
  breaking change is a new view.
- Aggregates only, except the key views named below, which carry catalog keys / component ids and nothing else (no
  plan or trip id, no personal data, no `conf:commercial` column).
- The CIS reader treats `UndefinedTable` / `InsufficientPrivilege` / `InvalidSchemaName` as
  `contract_view_missing` and shows the rows as `n/a`, so the CIS code may ship before the owner migration is applied.

## Family ops.overview.v1 (AA-858, CIS `/admin/overview`)

| View | Columns | Metrics | Migration |
|---|---|---|---|
| `booking.v_ops_funnel_daily` | `day date, metric text, source_system text, n bigint` (UTC days, last 400) | `inquiry_received`, `inquiry_parked`, `inquiry_failed`, `trip_case_created`, `proposal_sent`, `confirmed`, `cancelled` (first reach) | bk-017 |
| `booking.v_ops_case_status` | `status text, n bigint` | not soft-deleted trip cases per current status | bk-017 |
| `tripplanner.v_ops_traffic_daily` | `day date, metric text, n bigint` (UTC days, last 400) | `planner_session_started`, `trip_started`, `trip_edited`, `inquiry_sent` | tp-015 |

## Family ops.data_coverage.v1 (AA-992, CIS `/admin/data-coverage`)

| View | Columns | Content | Migration |
|---|---|---|---|
| `tripplanner.v_ops_data_totals` | `metric text, n bigint` | `sessions`, `trip_drafts`, `trip_drafts_sent`, `trips_with_events`, `pin_events`, `pin_events_invalid_id` (pins whose `component_id` is not UUID-shaped: counted, never listed), `component_id_map_rows`, `customers`, `traveller_accounts`, `outbox_rows`, `narration_cache_rows` (totals) | tp-020 |
| `tripplanner.v_ops_pin_components` | `component_id text, trips bigint` | one row per pinned catalog component id (pins ever added, `add_component` events; UUID-shaped ids only, lower-cased) and the trips that pinned it; no trip / session id, no payload text | tp-020 |
| `tripplanner.v_ops_component_id_map` | `old_id text, new_id text` | the `component_id_map` edges (catalog ids only), so CIS walks a pin to its component like TripPlanner (map first, then `geo.component_redirect`, ≤ 5 hops) | tp-020 |
| `booking.v_ops_data_totals` | `metric text, n bigint` | `trip_plans`, `trip_plans_sellable`, `trip_plan_components`, `departures_open`, `suppliers_active`, `contracts_published`, `rates_current`, `media_active`, `media_active_with_rights`, `customers`, `b2b_partners_active`, `b2b_holds_active` (counts as of now) | bk-025 |
| `booking.v_ops_trip_plan_keys` | `source_system text, source_id text, sellable boolean` | the catalog key of each trip plan (no plan id, no `conf:commercial` column), so CIS counts plans whose tour left the live catalogue | bk-025 |

The CRM part of the data coverage page is **not** a view: no AA role has `USAGE` on schema `crm` (ADR 0008a decision
1). It is `crm.ops.v1` 1.4 `GET /crm/ops/v1/data-coverage` (`crm.ops.v1.openapi.yaml`).
