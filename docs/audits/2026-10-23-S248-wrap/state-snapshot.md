# S248 close — live state snapshot (23/10/2026, ~14:50 UTC)

Read from the live sources, not from memory. Account ids, ARNs and hostnames of internal resources are left out (public repo).

## ECS (cluster aa-cis-dev-cluster)

| Service | Task definition | Image tag | Running | Rollout |
|---|---|---|---|---|
| aa-cis-dev-api | :799 | dev-5543d1fc | 1 | COMPLETED |
| aa-cis-dev-worker | :358 | dev-5543d1fc | 1 | COMPLETED |
| aa-booking-dev-api | :49 | ab5641d1 | 1 | COMPLETED |

API and worker run the same SHA.

## Health

- CIS `/health` 200; `/health/ready` 200: schema **274** (required 273), git_sha 5543d1fc.
- Booking `/booking/health` 200; `/booking/health/ready` 200: schema **bk-021**.
- TripPlanner Lambdas `aa-tripplanner-dev-browse` / `-assembly`: same CodeSha256, updated 23/10 14:22 UTC (TP #142).

## Latest migration per owner

CIS **274** · Booking **bk-021** · TripPlanner **tp-018** (schema reference Verified 23/10 13:44 UTC, root #214). The `crm` schema is present (5 objects); its owner is not in the "Latest migration per owner" line of the generator.

## Repos (default branch head at close)

- AA-CIS-App main 5543d1fc (#967). Open: release PR #950 (0.7.0).
- AA-Booking main ec860ff (#74 Next 16.4.1, frontend only). Open: release PR #66 (0.4.0).
- AA-TripPlanner-Web main e6f5c4a (#142). Open: release PR #137 (0.6.0).
- AA-CIS-Infra main 2c32a03 (#329). Open: none.
- AA-Partner main (after #2, actions bump). Open: release PR #3 (0.2.0).
- AA-Ecosys master 31ac1c5 (#214) + this close branch.

## Vercel production

- aa-tripplanner: e6f5c4a (READY).
- aa-booking-admin: redeploying for #74 at snapshot time.

## Jobs and flags

- `shared.job` / `booking.job`: no deploy was blocked by the job tables in the session; the last DB Migrate apply (274) passed the idle check.
- Erasure flags on Dev: `ERASURE_APPLY_ENABLED` off, tenant retention 30 days (Infra #322).
- `S1_WRITER_V2` unset on both CIS task definitions (AA-645 step 0).
- Nightly tour liveness gate (`db-tour-liveness-gate.yml`): strict, LANDED {L2, L4}, L3/L5 enforced from 2026-10-23.
