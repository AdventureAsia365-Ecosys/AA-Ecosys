# AA-1093 — Implementation notes (root repo, lane L0 / l11: erasure contract and docs)

Source: the S279 plan `docs/audits/2026-11-13-S279-session/aa1093-plan.md` and the tech lead's decisions D1-D11 of
13/11/2026 on Linear AA-1093 (D2 changed to 90 days for the CRM). This file covers the root-repo lane only; the CIS,
Booking, TripPlanner and AA-Partner lanes keep their own `AA-1093-<lane>.md`.

## Decisions

- **Contract format: one OpenAPI 3.1 file** (`docs/contracts/tenant.erasure.v1.openapi.yaml`), not a JSON Schema file
  plus a separate HTTP file. The CRM needs HTTP routes (it holds no grant on another schema, root ADR 0008a) and the
  two view parts reuse the same shapes, so the view rows are component schemas too (`ErasureRequestRow`,
  `ErasureReportRow`), which gives them samples and CI like the HTTP bodies. `tenant.entitlements.v1` describes its
  view parts in prose only; here the row shapes are typed because three apps implement against them at once.
- **Per-app stages within the phase enum the lanes were given.** With the CRM at T0 + 90 days and the others at
  T0 + 30 days, one approval cannot cover every app at once (it would keep CIS, Booking and TripPlanner data 90 days,
  against D1). The saga therefore runs in stages: a step per app with its own `not_before` and status
  (`waiting` / `active` / `done` / `failed`), and a request `round`. Stage 1 (day 30) takes CIS, Booking and
  TripPlanner through dry_run -> awaiting_approval -> apply -> verify; the request then goes back to `dry_run` with the
  next round and the CRM becomes active at day 90. No `scheduled` phase was added, because the parallel lanes build
  CHECK constraints from the phase list in the lane brief (`dry_run|awaiting_approval|apply|verify|done|failed|cancelled`).
  Before the first `not_before`, phase `dry_run` with no active step means "nothing to do yet".
- **CIS last still holds across stages.** CIS erases in stage 1, before the CRM's stage 2. That is safe because the
  request rows have no foreign key to `shared.tenants` and the CRM reads them over HTTP; the risk the plan names
  ("CIS deletes shared.tenants, which the other apps read the request through") applies only to a view that joins
  `shared.tenants`, which `catalog.v_tenant_erasure_v1` must not do (`is_pilot` / `is_synthetic` are copied onto the
  request at T0).
- **Hashes defined in the contract** (table digest = md5 of sorted `<pk>|<row version>` lines; app plan hash = sha256
  of `tenant.erasure.v1|<tenant>|<round>` plus sorted table lines). Only stability within an app is required, but one
  definition keeps the four implementations comparable and binds every plan to the tenant and the round.
- **Thresholds are CIS settings.** The two exit windows (30 / 90 days) and the approval validity (24 hours) are named as
  CIS settings-registry values (CIS 407 mechanism, administrator role, audited); CIS computes `not_before` and
  `approval_expires_at`, so no consumer holds a window. Key names are left to the CIS saga lane.
- **Field policy:** `tenant.erasure.v1` forbids actors / approvers (`*_by`), row values, audit before / after values,
  tenant name / slug / trading name, free-text reason / note and snapshot ids; required negatives `approved_by`,
  `row_values`, `trading_name`. `tenant.entitlements.v1` 1.7 keeps its policy; a rejected sample shows the new body
  refusing `reason`.
- **`account.erasure_requested` body = `{op: requested | cancelled, request_id}`**: a hint only; the erasure feed is the
  source. Emitted at T0 and on a cancelling restore.
- **DPA wording:** clause 11 says "[90]" / "[30]" days in brackets (values the business owner or counsel may change);
  Booking B2B and the Trip Planner get real deletion text marked "planned, AA-1093"; a new 11.4 describes the one
  process and the receipt. Annex 3 calls acc1 "a second AWS account held by the tech lead" (no account ID, company
  docs name roles not people) and adds a [COUNSEL] note because it departs from ADR 0019 b19 (accounts in AA's name).
- **DSAR runbook:** the saga is written as the target procedure with a "planned" banner; the tested CIS-only steps are
  kept unchanged as section 4.6 (the CIS part, which the saga reuses) and section 4.7 says to use them alone until the
  saga ships. Section 5 references were renumbered to 4.6.
- **Restore drill evidence** is committed as `docs/audits/2026-11-13-S279-cis-restore-drill/restore-drill.json` (the
  drill's own JSON plus run metadata; ids, table names and counts only), the same shape as the CRM drill evidence.

- **Review fix pass (S279):** the CRM export at offboarding is marked planned in DPA 11.1 / 11.2, the DSAR runbook
  4.1 T0 row and the contract text: today the CRM locks an offboarded agency and every member request gets 403
  `tenant_locked` (AA-Partner `api/app/tenancy.py`), so the owner cannot reach Settings > Data and privacy. The CRM
  lane must build the exception into the lock (owner export and download stay open until the CRM `not_before`); until
  then the operator tells the owner before T0. DPA 11.4(d) and runbook 4.4 step 7 now describe the two stages (day 30:
  TripPlanner and Booking in parallel, CIS last; day 90: the CRM alone with its own dry run, approval and snapshot).
  Annex 1 and Annex 4 went to v0.5 so the whole pack matches Annex 3 v0.5 (GPT stages on Amazon Bedrock first, the
  OpenAI API last); pilot contract set row 3 and AI Schedule row 5 name the v0.5 pack.

## Changed

- New: `docs/contracts/tenant.erasure.v1.openapi.yaml`, 11 samples in `docs/contracts/samples/tenant.erasure.v1/`,
  `docs/ops/runbooks/tenant-restore-drill.md`, `docs/audits/2026-11-13-S279-cis-restore-drill/restore-drill.json`.
- `tools/contracts/check_contracts.py`: POLICY and REQUIRED_NEGATIVES entries for `tenant.erasure.v1`;
  `tools/contracts/test_check_contracts.py`: one policy test.
- `docs/contracts/tenant.entitlements.v1.openapi.yaml` 1.6 -> 1.7 (event type, `ErasureRequestChange`), two samples;
  `docs/contracts/README.md` (new row, 1.7 note); `docs/contracts/samples/README.md` (required negatives list).
- `docs/legal/dpa.md` v0.5 (clause 11, C7), `docs/legal/dpa-annex-3-subprocessors.md` v0.5 (§1.2, rows, change log),
  `docs/legal/register.md` (acc1 note, Annex 3 version), `docs/legal/dpa-pack-outline.md` (status line).
- `docs/legal/dpa-annex-1-processing.md` v0.5 and `docs/legal/dpa-annex-4-transfers.md` v0.5 (AI routing rows),
  `docs/legal/pilot-contract-set.md` row 3, `docs/legal/tenant-ai-schedule.md` row 5 (pack versions).
- `docs/legal/dsar-erasure-runbook.md` section 4 (4.1-4.7).
- `docs/architecture/data-standards/02-data-management.md`: four DM-7.1 rows + the S279 rows paragraph.
- `docs/ops/job-kinds.md`: `tenant_erasure_saga`, `tenant_backup`, `bk_tenant_erase`, a CRM table
  (`crm_tour_retired_fanout`, the CRM erasure step) and a TripPlanner table (existing kinds + `tp_tenant_erase`,
  `tp_tenant_backup`).
- `docs/ops/README.md`, `docs/audits/README.md`: index rows.

## Tradeoffs

- **Stages vs one approval:** two approvals (day 30 and day 90) instead of D7's "one combined fingerprint". D7 is kept per
  stage (one fingerprint per stage over every active app, one snapshot per stage); a single approval at day 90 would
  break D1.
- **Feed of full request state vs events:** the CRM feed re-serves the whole request (CRM step only) on every change, so
  the CRM never replays history; the cost is a few repeated rows per request.
- **Typed view rows** make the contract longer, but each consumer lane can test its view against a sample.

## Should know

- **Order (MIG-4):** this root PR must be on `master` before the AA-CIS-Infra copies of CIS 408, Booking bk-057 and
  TripPlanner tp-030 (DM-7.1 retention rows). The `Retention rows` Infra check is scoped to `crm` today, but DM-7.1 asks
  for the rows for every owner.
- **CIS byte copy of tenant.entitlements.v1:** AA-CIS-App pins the root file by sha256
  (`tests/unit/test_aa1028_tenant_account_contract.py`, copy `docs/contracts/tenant.entitlements.v1.openapi.yaml`); the
  CIS saga lane must copy 1.7 and update the pin, and widen the `shared.tenant_account_event` type CHECK (CIS 353) in its
  migration. The workspace-only M1 check of `check_contracts.py` reports the copy until then.
- **New M2M scope `cis.tenant/erasure`** needs an AA-CIS-Infra change (`identity_m2m.tf`) and the CRM client grant.
- **Names the lanes must keep:** `catalog.v_tenant_erasure_v1`, `booking.v_tenant_erasure_report_v1`,
  `tripplanner.v_tenant_erasure_report_v1`, `booking.tenant_erasure_log`, `tripplanner.tenant_erasure_log`,
  `shared.tenant_erasure_request`, `shared.tenant_erasure_step`, kinds `tenant_erasure_saga`, `bk_tenant_erase`,
  `tp_tenant_erase`, `tp_tenant_backup`. A rename means a follow-up root PR (retention rows, job kinds, contract text).
- `tenant_backup` reads its size cap from the env var `TENANT_BACKUP_MAX_BYTES` (CIS lane l6): a threshold outside the
  settings registry, flagged as a follow-up for that lane.
