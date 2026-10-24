# S249 close — live state snapshot (24/10/2026, ~11:53 UTC)

Read from the live sources, not from memory. Account ids, ARNs and internal hostnames are left out.

## ECS (cluster aa-cis-dev-cluster)

| Service | Task definition | Image tag | Running | Rollout |
|---|---|---|---|---|
| aa-cis-dev-api | :807 | dev-aeca5cd8 | 1 | COMPLETED |
| aa-cis-dev-worker | :371 | dev-aeca5cd8 | 1 | COMPLETED |
| aa-booking-dev-api | :52 | 62c5e58b | 1 | COMPLETED |
| aa-crm-dev-api | :29 | a1d7f56d | 1 | COMPLETED |
| aa-crm-dev-web | :15 | 011bf804 | 1 | COMPLETED |

CIS api and worker run the same SHA. CIS main is at the 0.8.0 release commit (85f13ba8), which only changed
CHANGELOG / manifest / `api/version.py` and triggered no deploy: the live image aeca5cd8 holds all code; `/health`
still reports 0.7.0 until the next CIS deploy.

## Health

- CIS `/health/ready` 200: schema **274** (required 273), git_sha aeca5cd8.
- Booking `/booking/health/ready` 200: schema **bk-022**.
- CRM `/crm/health/ready` 200: schema **crm-011**, keys kms; CRM web `/healthz` 200.
- TripPlanner Lambdas browse / assembly: same CodeSha256, updated 23/10 14:22 UTC (S249 TripPlanner changes were on
  the Vercel frontend).

## Latest migration per owner

CIS **274** · Booking **bk-022** · TripPlanner **tp-018** · CRM **crm-011** (crm-003…crm-011 applied in S249).

## Intentionally ON for S250 (Nghiệp: same-day split, keep the wave running)

- Worker `S1_WRITER_V2=on` (inherited by every CIS deploy from the family's latest revision).
- Route `s1_generate` = sonnet-5-5 (acc3), set 08:51:15 UTC.
- No wave open, no S1 job queued at close; next wave: `cw_taiwan_1` (plan `.tmp-session/s249/aa645/realpilot/cw-plan.json`).
- RDS manual snapshots `aa-cis-dev-db-pre-s1-*`: one per wave (expire under the AA-869 30-day rule).

## Repos (default branch head at close)

- AA-CIS-App main 85f13ba8 (#970 release 0.8.0). Open PRs: none.
- AA-Booking main 914409ed (#79 release 0.5.0). Open: none.
- AA-TripPlanner-Web main d5a704b1 (#144 release 0.7.0). Open: none.
- AA-CIS-Infra main 205140df (#352). Open: none.
- AA-Partner main 30a144e9 (#12). Open: none.
- AA-Ecosys master 1d964166 (#222) + this close branch.

## Jobs and gates

- `shared.job`: the last wave (Bhutan) closed 11:27:55 UTC; DB Migrate apply of crm-011 passed the idle check.
- Nightly AA-Partner "Scrub corpus": red (over-scrub 9.1% vs 5%, 0 leaks) — GitHub issue AA-Partner #27, option B
  pending Nghiệp.
