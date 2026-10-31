---
id: OPS-08-s261-aa923-writing-memory
title: "S261 AA-923 labels on T2/A1, offboarding deletion proof, WM-34 quarantine evidence"
description: "Live evidence on Dev for AA-923: WM-32 labels on a T2 version and an A1 rewrite (T9 labels unchanged), WM-33 data_erasure DRY RUN and real run on a throwaway synthetic tenant (other tenants untouched), WM-34 post-quarantine check."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [aa-cis-api, ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-923, AA-839, AA-921, AA-922]
---

# AA-923 — writing memory: labels on T2/A1, offboarding deletion, retired lesson tables (S261)

Session S261 (31/10/2026, Claude Code). Scope: lane 1 item 1 of the S260 In Progress triage
(`docs/audits/2026-10-30-S260-inprogress-triage/README.md` §4). Code is merged and deployed (CIS #1188 code,
#1189 quarantine migration 316, schema 317 on Dev); this file holds the live proof.

Status of this file: **prepared** (scripts written and compiled). The orchestrator runs them and fills §4.

Scripts (run inside the CIS api container through `tools/ecs/ecsx.sh`, role `cis_app`, admin API on
`127.0.0.1:8000`): `.tmp-session/S261/aa-923/` — `wm34_post_quarantine.py`, `wm32_labels.py`, `wm33_seed.py`,
`wm33_erasure.py`. Repo script: `apps/AA-CIS-App/scripts/aa923/wm34_dry_run.py`.

## 1. What is checked

| Done-when line | How | Proof in the output |
|---|---|---|
| WM-34: DRY RUN evidence in a comment | `scripts/aa923/wm34_dry_run.py` (read-only, `cis_app`) ran at 01:19 UTC, after the 316 apply | `SCRIPT table=… exists=f` for both and `verdict ready=false reasons=…:missing`: expected after the quarantine (the script checks the source schemas) |
| WM-34: the tables left their schemas | `wm34_post_quarantine.py` (catalog only) | `WM34Q table … in_source:false, in_retired:true, cis_app_any_privilege:false`, the drop-not-before date in `comment_prefix`; `WM34Q route` GET / PATCH `/v1/rules` 404; `WM34Q verdict quarantined:true` |
| WM-32: one label of each type on Dev | `wm32_labels.py MODE=apply`: `POST /admin/content-quality/tour-versions/{id}/label` and `…/a1-content/{id}/label` | `WM32 post` HTTP 200 twice; `WM32 proof_rows n:2` (one `t2_version`, one `a1_content`, labeller `admin:s261-orchestrator`) |
| WM-32: existing T9 labels unchanged | same run: count and md5 of every `acp_shared.content_piece_label` row before / after | `WM32 verdict t9_unchanged:true, done:true` |
| WM-33: DRY RUN for a synthetic tenant, counts before | `wm33_seed.py` then `wm33_erasure.py PHASE=dry_run` (`POST /admin/job-runner/erasure/run`) | `WM33S counts_after_seed every_store_has_a_row:true`; `WM33E dry_learned_store_rows` lists each store; `WM33E dry_verdict ok:true` (no blocker, DRY RUN wrote nothing) |
| WM-33: real run, counts after | `wm33_erasure.py PHASE=apply` | `WM33E apply_result verified:true`; `WM33E stores_after all_zero:true`; one `tenant.erased` audit row |
| WM-33: other tenants untouched | per-(table, tenant) row counts of every inventory table with `tenant_id`, before and after, same process | `WM33E others_after unchanged:true, diffs:[]`; `WM33E apply_verdict done:true` |
| WM-33: independent verification | `wm33_erasure.py PHASE=verify` (new process, verification DRY RUN through the API) | `WM33E verify_verdict ok:true` (every non-keep count 0, tenant state null) |
| WM-33: agent review on the PR (data deletion) | CIS #1188 adds no deletion code (the AA-839 `data_erasure` job is the offboarding function); its WM-33 part is the integration test `test_offboarding_erases_every_learned_writing_store_and_no_other_tenant` | to record: the review of #1188 (or an independent one) in §4 |

## 2. The synthetic tenant and why

A new throwaway tenant, slug `aa923-wm33-s261`, name `AA-923 WM-33 synthetic (S261)`, created and offboarded
through the admin API (runbook `docs/legal/dsar-erasure-runbook.md` section 5). Not one of the four E2E tenants
(`atlas-hearth`, `terra-family`, `trail-pulse`, `wildkind-travel`): an erasure deletes the whole tenant (account row,
key, brand, T2 versions) and cannot be undone, and those four back Playwright, UI verify and UAT. They are the
"other tenants" of the check.

Seeded rows (fictional text, shapes of the CI test `_seed_learned_writing`): one row each in `shared.writing_signal`,
`shared.writing_rule` (a preference summary), `shared.writing_exemplar`, `shared.writing_memory_release`,
`shared.writing_memory_release_exemplar`, `shared.writing_memory_shadow`, `shared.writing_memory_keep`,
`shared.writing_memory_disagreement`, plus a T2 version (`gold_aa_internal.tenant_tour_versions`, status
`needs_review`) labelled through the API (`acp_shared.content_label`, labeller `admin:s261-wm33-seed`). The
learned-writing rows have no $0 API (signals come from tenant edits, exemplars from content, shadow outputs from a
paid shadow run), so they are inserted as `cis_app`. The tenant is offboarded before the seed. One platform-level row
is left behind by the seed (the `shared.prompt_eval_runs` row the shadow output needs); `PHASE=cleanup` removes it
after the verification. Golden-set items are not seeded (their set row is not deletable by `cis_app`).

## 3. The real run: which path

- **Path A (used unless noted in §4):** `wm33_erasure.py PHASE=apply` runs the `data_erasure` handler itself in the
  api container on a `shared.job` row it creates as `running`, with the apply flag and a 0-day retention window
  passed to the handler only (as the CI test does). Every check inside the job runs (approved fingerprint, DRY RUN
  < 24 h, single use, tenant offboarded and locked, recount inside the transaction, exact rows per statement,
  recount 0, audit row). It skips the API's Cognito staff-session check and the `ERASURE_APPLY_ENABLED` env flag;
  both stay off on Dev. The script refuses any tenant but the throwaway one.
- **Path B (runbook section 4 steps 6-7):** `erasure_drill = true` in AA-CIS-Infra (Terraform + CIS deploy), the
  tech lead applies from `/admin/data-erasure` with a Cognito session, then `erasure_drill = false` again.

## 4. Results

Run 31/10/2026 03:19–03:55Z by the orchestrator over ECS exec (tech lead approved the drill in the session).

| Step | Result | File |
|---|---|---|
| WM-34 DRY RUN after quarantine 316 | `shared.pipeline_lessons` and `acp_shared.acp_output_rules` no longer in their schemas (`exists=f`); both in schema `retired` | `wm34-out.txt` |
| WM-32 labels | 2 labels saved through the admin API (one `t2_version` on E2E tenant terra-family, one `a1_content` on the AA tenant), labelled_by `admin:s261-orchestrator`, has_sha; T9 labels unchanged (1 → 1, same fingerprint) | `wm32-apply-out.txt` |
| WM-33 seed | synthetic tenant `aa923-wm33-s261` created and offboarded via the API; 1 row in each of the 10 learning stores | `wm33-seed-out.txt` |
| WM-33 DRY RUN | job `dba93d6e…`: succeeded, offboarded, not blocked, 35 checks passed, delete 15 / keep 2, fingerprint `9d7cb232…6427157`; dry run wrote nothing | `wm33-dry-out.txt` |
| Snapshot | `tenant-erase-20261031-pre` available 03:48:51Z; deleted after the drill | — |
| WM-33 real run | job `653f7e6f…` (path A, in-process with the approved DRY RUN and fingerprint): verified true, delete 15; every store of the tenant 0; other tenants unchanged (39 tables, SHA equal before/after); 1 `tenant_erased` audit row | `wm33-apply-out.txt` |
| Verify (new process) | verification DRY RUN `cf16d788…`: only 3 audit rows kept, no other row; no S3 objects or secrets for the tenant | `wm33-verify-out.txt` |
| Cleanup | the one platform seed row (marker `zz923-s261-30d13c8b`) deleted after a DRY RUN | — |

Independent review of CIS #1188 (S261, data-deletion lens): **approve**, no blocking finding. Minor follow-ups: m1 a
concurrent label save during apply could leave one row (route should refuse offboarded tenants or add an FK); m2 the
WM-33 integration test lacks platform rows and cross-tenant WM links; m3 the fingerprint binds counts per table, not
row identity or an inventory hash; m4 the inventory still lists `acp_shared.acp_output_rules` (retired by 316); m5 the
DSAR runbook does not mention the writing-memory stores; m6 (pre-existing) the job does not require an actor on apply.
Seeding note: the learning-store rows of the synthetic tenant were inserted as `cis_app` with the CI test shapes (no
admin route creates them without an LLM call); the tenant, its offboarding and its label went through the API.

