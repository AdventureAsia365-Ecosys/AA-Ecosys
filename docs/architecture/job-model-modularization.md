# Job / Background-work modularization — plan

Companion to ADR 0003 (`docs/adr/0003-one-durable-job-model.md`). Written S213 (06/10/2026).
This is the sequenced delivery plan; the ADR holds the decision.

## Current mechanisms (survey, S213)

| Mechanism | Count | Survives deploy? | On Jobs page? |
|---|---|---|---|
| Durable job kinds (`shared.job` + worker) | 10 (incl. s1_rewrite, revalidate, s1_batch_ingest, recompute) | yes | yes |
| Standalone Lambdas (dfs_balance, s4_trigger, sweeper, canary, dlq_classifier) | 5 | yes (separate fn) | no |
| In-process `asyncio.create_task` in the API | 0 after AA-723 | — | — |
| Legacy `shared.pipeline_jobs` (boot sweep) | 1 | n/a | no |

## Three layers (ADR 0003)

- **A — Trigger/Enqueue:** endpoint / cron Lambda / EventBridge only enqueues a job (payload) with an idempotency key. Never runs the work inline.
- **B — Job kind + stage registry:** a kind declares the stages it runs; each stage is a pure `run(ctx, scope)` declaring the tables it reads/writes. The orchestrator reads the stage list.
- **C — Write strategy per stage:** each stage declares how it writes (UPSERT / versioned-swap / delete-insert). Swap-safety lives here, isolated from orchestrator and readers.

## Sequence

| Nac | Content | Repo | Status |
|---|---|---|---|
| PR1 | s1_rewrite + revalidate + s1_batch_ingest → worker | CIS | done S213 (#568) |
| PR2 nac 1 | 2 recompute → one `recompute` job kind (scope/stages in payload) + debounce; keep write logic | CIS | done S213 (#569) |
| PR2 nac 2 | `atom_ranking` → versioned-swap (like `route`); update every reader | CIS | S213 (in progress) |
| Nac 3 | full stage registry: segment/score/route/hub as declared modules; fold a3_atomize's inline recompute into the one gate | CIS | future |
| Nac 4 | cron/event Lambdas enqueue jobs instead of running work inline | CIS + Infra | future |
| Nac 5 | flip `JOB_WORKER_IN_API` default to false; retire legacy `pipeline_jobs` + dead `_background_tasks` drain | CIS | future |
| Nac 6 | grant `shared.job` to a second repo; TripPlanner extraction + embeddings-backfill become job kinds | cross-repo | when needed |

## Readers that must learn the current-pointer filter (nac 2)

`atom_ranking` has no version/pointer today; these read it and would see a dip:
`services/acp_shared/slate.py` (×2), `api/routers/v1_route_hub.py`, `api/routers/admin_dashboard.py` (score/segment/route/hub panels), `api/routers/admin_atoms.py`, `api/routers/admin_overview.py` (headline count — most visible). `route` already filters `superseded_at IS NULL` (AA-532) — reuse that model.
