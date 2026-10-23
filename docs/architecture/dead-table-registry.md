---
id: ARCH-09
title: Dead Table Registry
description: Tables on the shared RDS that are kept but no longer written or read, or were dropped, with the migration and the evidence.
type: reference
status: draft
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem, aa-cis-dev-db]
last_reviewed: 2026-10-23
review_every_days: 90
related: [ARCH-08, docs/database/schema-ownership.md]
---

# Dead Table Registry

One row per table that is frozen (kept, no writer) or dropped. Procedure for a drop: skill `aa-cis-schema`
`references/destructive-ops.md` (DRY RUN → snapshot → apply → independent verify). Update the row before the apply
(the DRY RUN numbers, the approval) and after it (the apply run, the verify). Table and column names:
[`db-schema-reference.md`](db-schema-reference.md).

| Table | Owner | State | Since | Migration | Why | Evidence |
|---|---|---|---|---|---|---|
| `tripplanner.itinerary_components` | AA-TripPlanner-Web | frozen → drop pending approval | frozen 14/10/2026 (AA-712 slice 6a, TP #75) | tp-018 (AA-712 X4) | the pilot's extraction output; CIS builds `geo.tour_place` behind `catalog.v_tour_component` (ADR 0007); unread since the TripPlanner X4 reader removal | DRY RUN `aa712_frozen_tables_dry_run.py` (rows, last write, dependents): to fill before apply |
| `tripplanner.tour_day` | AA-TripPlanner-Web | frozen → drop pending approval | 14/10/2026 | tp-018 | replaced by `geo.tour_day` / `catalog.v_tour_day` | same DRY RUN |
| `tripplanner.tour_stop` | AA-TripPlanner-Web | frozen → drop pending approval | 14/10/2026 | tp-018 | replaced by `geo.tour_stop` / `catalog.v_tour_stop` | same DRY RUN |
| `tripplanner.tour_graph_build` | AA-TripPlanner-Web | frozen → drop pending approval | 14/10/2026 | tp-018 | replaced by `geo.graph_build` | same DRY RUN |
| `tripplanner.tour_graph_edge` | AA-TripPlanner-Web | frozen → drop pending approval | 14/10/2026 | tp-018 | replaced by `geo.graph_edge` / `catalog.v_graph_edge` | same DRY RUN |
| `tripplanner.tour_graph_node` | AA-TripPlanner-Web | frozen → drop pending approval | 14/10/2026 | tp-018 | replaced by `geo.graph_node` / `catalog.v_graph_node` | same DRY RUN |
| `tripplanner.tour_leg` | AA-TripPlanner-Web | frozen → drop pending approval | 14/10/2026 | tp-018 | replaced by `geo.tour_leg` / `catalog.v_tour_leg` | same DRY RUN |
| `tripplanner.tour_junction` | AA-TripPlanner-Web | frozen → drop pending approval | 14/10/2026 | tp-018 | replaced by `geo.tour_junction` / `catalog.v_tour_junction` | same DRY RUN |

**Exception for the eight `tripplanner` place tables (tp-018), needs Nghiệp's written approval in the tp-018 PR and
the session log** (data standards README: an exception to a MUST): root ADR 0007 decision 10 says "14 days after the
flip" (05/11/2026) and DM-3.8 / DM-3.9 ask for 14 days of `pg_stat_user_tables`, a quarantine (`ALTER … SET SCHEMA
retired`) and an S3 archive first. On Dev these are replaced by: two DRY RUN dispatches (before and after a
TripPlanner smoke) whose read and write counters must not move; no quarantine (the rows are derived data CIS rebuilds
in `geo`; a quarantine keeps the foreign keys to `shared.destinations` and needs a second destructive apply);
**archive location** = the DB Migrate pre-apply RDS snapshot of the tp-018 apply, tagged `aa:retain-until` = apply
date + 180 days and `aa:purpose` = `aa712-tp018-pre-drop` (the DM-7.3 S3 archive does not exist yet, N4). ADR 0007
carries the matching conditional amendment (S248). Lock note: the drop takes ACCESS EXCLUSIVE on CIS's
`shared.destinations` for its length (RI triggers of 11 foreign keys); apply while the job tables are idle, retry on a
lock timeout. Fill in, before the apply: approval (who, date, link); after it: snapshot id, apply run, verify.

Kept on purpose: `tripplanner.component_id_map` (tp-017) maps the pre-flip component ids that old drafts' trip events
still carry to catalog ids; it has no foreign key to `itinerary_components` and outlives it.
