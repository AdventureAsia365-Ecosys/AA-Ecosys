# ADR 0003 — One durable job model for all deferred work

- **Status:** Accepted (06/10/2026, S213 — Nghiệp: module hóa job cho toàn hệ, làm tuần tự nhiều phiên).
- **Scope:** AA-Ecosys (AA-CIS-App, AA-TripPlanner-Web, AA-CIS-Infra, future AA-Booking).
- **Implements / tightens:** ADR 0001 (ecosystem architecture). Related: AA-650/651/652 (durable runner + worker ECS), AA-723 (move the remaining in-process tasks).

## Context

Deferred and background work in the ecosystem runs on four different mechanisms today, each with a
different durability and visibility:

| Mechanism | Count | Survives deploy? | On Jobs page? |
|---|---|---|---|
| Durable job kinds (`shared.job` + worker) | 9 | yes | yes |
| Standalone Lambdas (dfs_balance, s4_trigger, sweeper, canary, dlq_classifier) | 5 | yes (separate fn) | no |
| In-process `asyncio.create_task` in the API | 2 (both recompute) | no | no |
| Legacy `shared.pipeline_jobs` (boot sweep) | 1 | n/a | no |

The in-process tasks are the problem AA-650/652 set out to remove but did not finish:

- The two remaining ones (`admin_atoms` recompute-after-delete, `admin.py` recompute-after-status-
  change, AA-713) die on every API deploy and are invisible; one keeps no task reference and can be
  garbage-collected mid-flight. S212 lost 16 Thailand tours to exactly this class of bug on the S1
  path (fixed in AA-723 PR1).
- The platform-wide Segment/Score/Route recompute is entered from three paths (the a3_atomize job,
  atom-delete, status-change) with no single gate and no dedup, so one atom delete triggers a full
  6-market platform rebuild.
- `acp_contract.atom_ranking` is rebuilt DELETE+INSERT across six separate transactions, so readers
  (overview count, Slate panels) see counts dip mid-recompute. `acp_contract.route` already avoids
  this with a `superseded_at IS NULL` current-pointer (AA-532).
- The worker defaults to running in-process (`JOB_WORKER_IN_API` default true); only a manually set
  env on the api task-def keeps it from running two workers.
- TripPlanner has no job model at all (manual scripts + synchronous Lambdas); AA-Booking does not
  exist yet. Both share the same RDS (acc2), so `shared.job` is physically reachable from them.

## Decision

1. **One durable job model is the single mechanism for deferred work: `shared.job` + the worker ECS
   service.** No new fire-and-forget `asyncio.create_task` in a request path. Every unit of deferred
   work is a job row — durable, retryable, visible on the Jobs page.
2. **Three layers, kept separate** (mirrors the LLM-gateway split of role-config / call-log /
   shadow):
   - **A — Trigger/Enqueue.** An HTTP endpoint, a cron Lambda or an EventBridge rule only *enqueues*
     a job (a payload describing the work) with an idempotency key. It never runs the work inline.
   - **B — Job kind + stage registry.** A kind declares the stages it runs; each stage is a pure
     `run(ctx, scope)` that declares the tables it reads and writes. The orchestrator reads the stage
     list and runs them. Adding or changing one stage does not touch the others.
   - **C — Write strategy per stage.** Each stage declares how it writes (UPSERT / versioned-swap /
     delete-insert). Swap-safety lives here, isolated from the orchestrator and from readers.
3. **Readers never see a partially-recomputed set.** Any stage whose readers would otherwise see a
   dip writes via a current-pointer (the `route.superseded_at` model), and every reader filters on
   that pointer. A recompute makes the new set current in one swap, never by deleting the old set
   first.
4. **`shared/jobs/` is shared library code, available to every repo, forced on none.** It is reusable
   like `shared/llm_client/`. A non-CIS repo (TripPlanner, future AA-Booking) enqueues into
   `shared.job` only when it has real deferred work, and only with the DB grant that ADR 0002 governs
   (content stays CIS-written; a job row is state, not content). We do not build a cross-repo job
   model ahead of a second real consumer.
5. **Standalone Lambdas stay as triggers, not as executors of heavy work.** A cron/event Lambda may
   enqueue a job so the work itself is durable and visible, rather than doing the work inside the
   Lambda invisibly.

## Consequences

Delivered in sequence, verified at each step (survive-deploy; and for recompute, no-dip). Each nac
is its own PR; later nac are their own sessions.

- **Nac 1 (CIS):** the two recompute tasks become one job kind `recompute` with `{scope, stages,
  reason}` in the payload; the three call-sites enqueue instead of running inline; dedup by
  idempotency key so a burst of edits does not trigger N full rebuilds. Write logic unchanged.
- **Nac 2 (CIS):** `atom_ranking` gains a current-pointer (versioned-swap, like `route`); every
  reader (Slate, overview, admin panels, v1_route_hub) filters on it. No more count dip.
- **Nac 3 (CIS):** full stage registry — segment / score / route / hub become declared modules; the
  a3_atomize job's inline recompute also goes through the one gate.
- **Nac 4 (CIS + Infra):** cron/event Lambdas enqueue jobs instead of running work inline, so they
  show on the Jobs page.
- **Nac 5 (CIS):** flip `JOB_WORKER_IN_API` default to false; retire the legacy `pipeline_jobs`
  path and the dead `_background_tasks` drain.
- **Nac 6 (cross-repo, when needed):** grant `shared.job` to a second repo; TripPlanner's extraction
  and embeddings-backfill become job kinds instead of hand-run scripts.

**Revisit** if a second repo needs a job model before AA-Booking exists, or if a job ever needs
cross-region / cross-account execution (today everything runs on the single acc2 worker).
