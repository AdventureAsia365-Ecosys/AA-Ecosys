---
id: OPS-08-s261-aa921-exemplars
title: "S261 AA-921 Exemplars live check and CIS #1186 review"
description: "The $0 part of AA-921 on the synthetic E2E tenant: find and add example candidates, pin and unpin with a reason, the Next draft preview, isolation; plus an independent tenant-data review of CIS #1186 (migration 313)."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-921, AA-916, AA-919, AA-920]
---

# AA-921 — Exemplars live check on the E2E tenant ($0 part) and review of CIS #1186

Session S261 (31/10/2026, Claude Code). Scope: the $0 half of AA-921 named in the S260 In Progress triage
(`docs/audits/2026-10-30-S260-inprogress-triage/README.md` §4 lane 1 item 2). The LLM halves (WM-27 R2 paired
result, WM-28 approved summary with R2) stay blocked on the LLM path and move to Backlog.

Status of this file: **prepared** (script and review done). The orchestrator fills §3 with the run output.

## 1. What is checked

| Done-when line (this lane) | How | Proof in the output |
|---|---|---|
| "Find candidates (dry run)" works on the E2E tenant | `POST /admin/writing-memory/exemplars/refresh {dry_run:true}` | `DISCOVER.find_candidates_dry_run` / `REFRESH.find_candidates_dry_run`: HTTP 200, `dry_run:true`, `added` = `sim_total` (`match:true`), pool counts unchanged |
| "Add candidates" adds the E2E examples | same route, `{dry_run:false}` | `REFRESH.add_candidates` HTTP 200 `added ≥ 1`; `REFRESH.after.pool_e2e` grows by `added`; `REFRESH.idempotent_dry_run` `added:0` |
| Pin then unpin one example, with a reason | `POST …/exemplars/{id}/pin` and `…/unpin` `{reason}` | `PIN.pinned` 200 `status:pinned`; `UNPIN.unpinned` 200 `status:candidate` + reason; `audit_rows` 1 pin + 1 unpin |
| The "Next draft" preview changes | `GET …/exemplars/selection?writer=&scope=tenant&tenant_id=` (the same `pick()` the draft calls) and `in_next_draft` on `GET …/exemplars` | `PIN.after.changed:true` and the pinned id at `pos:1` with `st:pinned`; `UNPIN.after.next_draft` equals `PIN.before.next_draft` |
| Guards | bad bodies and transitions | `PIN.guard_short_reason` 422, `PIN.guard_repin` 409 `bad_transition`, `VERIFY.guard_owner_422` 422 |
| Tenant isolation (WM-27, read side) | selection and pool of every other tenant and of platform | `VERIFY.isolation.pass:true`, `leaks: []` |

The release half of WM-29 ("pin change shows in the next draft **release**") is the same `select_for_release` call at
draft time; drafting a tenant `rules` release needs a rule and its R2 / shadow evidence (LLM path), so the live
check stops at the preview. The release behaviour is covered by
`tests/integration/test_aa921_exemplars.py::test_a_pin_change_shows_in_the_next_draft_release`.

## 2. How it runs

Script: `.tmp-session/S261/aa-921/aa921_exemplars.py` (not committed), run by the orchestrator in the CIS api
container with `tools/ecs/ecsx.sh`. It reads with `cis_app` (`DATABASE_URL`, `ssl=require`) and writes **only through
the admin API** on `127.0.0.1:8000` (`x-admin-secret`, `x-admin-role: admin`). The actor header is a fixed UUID
(uuid5 of `aa-ecosys:s261-orchestrator`), because the write routes refuse a non-UUID actor (403 `no_actor`).

Each write step is a DRY RUN unless `APPLY=1` and prints before/after counts. Tenant: the single synthetic tenant
(`shared.tenants.is_canary`); the script stops if the chosen tenant is not synthetic. `Add candidates` is a
platform-wide action (it reads every tenant's "use as example" signals); the script stops before the apply if another
tenant would get rows, unless `ALLOW_OTHER_TENANTS=1`.

Steps: `discover` → (only if the plan says so: `seed` → `fact_filter`) → `mark` → `refresh` → `pin` → `unpin` →
`verify`. `seed` cuts one sentence from a few approved pieces of the synthetic tenant (the admin sentence action,
mode cut, no model call) only when that tenant has no admin sentence edit to use as an example.

Cost: $0 (no model call; the fact filter is deterministic).

## 3. Results (31/10/2026, orchestrator over ECS exec, $0, E2E tenant atlas-hearth)

| Done-when line | Result |
|---|---|
| Find candidates (dry run) | 200, dry_run true, added 1 = simulated 1 (match), pool unchanged |
| Add candidates | 200, added 1; pool atlas-hearth t2/tour_page candidate 1; a second dry run adds 0 (idempotent) |
| Pin with a reason | 200 pinned by admin actor; short reason refused 422; re-pin refused 409 bad_transition; audit exemplar_pin 1 |
| "Next draft" preview changes | before: candidate at position 1; after pin: pinned at position 1 (changed true); after unpin: back to candidate (changed true) |
| Unpin | 200 candidate with reason; audit exemplar_pin 1 + exemplar_unpin 1 |
| Isolation | 9 owners × 3 writers checked, 0 leaks; owner guard 422; Tenant 360 voice card shows 1 exemplar |
| Screenshots | `aa921-exemplars-pinned-1440.png`, `aa921-exemplars-pinned-1440-dark.png` (Exemplars tab, owner Atlas & Hearth, PINNED + "Next draft" item 1; 0 console errors) |

Raw lines: `run-lines.txt`. One `use` mark was set on one admin sentence-edit signal of the synthetic tenant (step mark).
Still blocked (LLM path): WM-27 R2 paired result, WM-28 approved preference summary, release-level WM-29 check.

## 4. Independent review of CIS #1186 (tenant-data safety)

Read-only review of `gh pr diff 1186` (merged 30/10/2026, merge commit `a70bb7a3`) and the code on `main`
(`services/writing_memory/exemplars.py`, `insertion.py`, `releases.py`, `api/routers/admin_writing_memory.py`,
`api/migrations/313_writing_exemplar.sql`, `services/erasure/inventory.py`, `api/core/staff_authz.py`).

**Verdict: approve. No blocking tenant-data finding.**

Isolation holds at four layers:

1. **Pool creation.** `refresh` takes only `scope = 'tenant'` "use" signals with `fact_status = 'pass'`, reads the
   source by id and the signal's own tenant (`content_piece … AND tenant_id = $2`, same for T2 versions), and writes
   the example with that tenant. The "use" flag itself can be set only on an admin sentence edit of that same object
   and tenant (`_EXEMPLAR_UPDATE_SQL`). Nothing creates platform examples from tenant text.
2. **Selection.** `owner_pool` filters `writer`, `scope` and `tenant_id IS NOT DISTINCT FROM`; a platform draft sees
   only platform rows, a tenant draft only its own.
3. **DB trigger (313).** A link must match the release's writer, scope, tenant and channel, is never `never`, is
   written only in the draft's own transaction and only for a `rules` release; links are never updated.
4. **Resolve time.** `load_release_exemplars` drops the whole part when any link does not belong to the release, and
   the items hash covers the masked text, so an edited or erased example renders nothing (fail closed).

At write time, tenant examples go only into the tenant part: the T9 user prompt (never the cached shared T9 system
prompt) and the T2 block that already carries the tenant rules; platform examples fill gaps, never another tenant's.
RLS is enabled and forced on both tables, the tenant pool role has no grant, reads need `tenant.read` (admin only in
`ROLE_PERMS`) and writes `ai.admin`. Both tables are in the erasure inventory and cascade from the release and the
example. Audit rows carry ids and statuses only.

Non-blocking observations (follow-up candidates, none needed to close the $0 lane):

- **O1 — "Add candidates" is platform-wide.** The Exemplars tab filters by owner, but the refresh reads every
  tenant's "use" signals. Admin-only and correct per tenant, but an admin working on one tenant may not expect rows
  for others. Option: an optional `tenant_id` on the refresh body.
- **O2 — Masking keeps a lone sentence-initial name** (documented in `masking.mask`). The example reaches only its own
  tenant's writer, so this is not a cross-tenant leak; the carry-over check (`eval_checks.exemplar_copies`) is the
  backstop for copying.
- **O3 — Order inside one refresh batch.** All rows added by one refresh share `created_at` (one transaction), so
  "newest candidate first" falls back to the random `exemplar_id`. Cosmetic; a pin overrides it.
- **O4 — `never` after a draft** is refused at the first activation by the API, not by the DB (documented trade-off:
  a DB rule would be a contract change on the release table).
