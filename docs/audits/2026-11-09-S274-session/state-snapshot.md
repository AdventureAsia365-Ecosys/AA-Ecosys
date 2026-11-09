# S274 state snapshot (10/11/2026 ~06:05 +07, read live)

## ECS (cluster aa-cis-dev-cluster), all 1/1 COMPLETED
| Service | Task def | Image / SHA |
|---|---|---|
| aa-cis-dev-api | :1076 | `116179b3` (`/health`, `/health/ready` ok, schema 393) |
| aa-cis-dev-worker | :642 | `116179b3` (same deploy run 42714688092, rerun after the job guard) |
| aa-cis-dev-admin | :15 | — |
| aa-booking-dev-api | :112 | `76140cdf` (`/booking/health` ok) |
| aa-booking-dev-admin | :11 | WordPress test sidecar (AA-1060) |
| aa-crm-dev-api / web | :146 / :119 | — |
| aa-tripplanner-dev-web | :6 | — |

## Deploys this session (CIS)
- `55abc393` (#1412) → `dc4c13e9` (#1413 islands + #1414 retarget apply, wave) → `116179b3` (#1415 stale guard).
- The first #1415 run was blocked by the deploy job guard (a queued place_geocode job). It was rerun after that job finished.

## Migrations
- CIS 393 is the newest applied (`/health/ready` schema_version 393). cis/336 is still time-gated (≥10/11 12:00Z, AA-1024 D8).

## Job tables
- See the close line below (filled at the end of the session).

## Open PRs (not bot release PRs)
- AA-Booking #200: bk-045, from 28/11.
- AA-Booking #210: docs. Transient check failures were re-run.
- CIS `fix/aa-1039-restore-republish`: not pushed. A lane is fixing the second review (1 major + minors). Next session: fetch from the lane clone, review again, push, ship, rehearse on test-wp.

## Blocked on the tech lead (auto mode)
- acc3 `terraform apply` (accounts/acc3-bedrock): 8 in-place updates, all tag standard (`ManagedBy` / `Project` / `App` / `Component` / `CostCenter` / `Owner` / `DataClassification`), plus the SNS cost-alert topic policy rewritten with the same statements. The plan is saved locally. Run it from the main Infra checkout with auto mode off.

## Spend this session (Dev)
- DataForSEO (24 h, `dfs_call_log`): about 7.16 USD before R2, plus R2 DE 0.96 + FR 0.96 + NL 0.96 = about 10.04 USD. The daily budget is alert-only.
- LLM (24 h ledger, all stages): 3.20 USD at 21:56Z. This includes the W4 replay of 0.12 USD and place cards of about 0.44 USD.
