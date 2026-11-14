# AA-1093 plan: lifecycle events across apps

S279 design pass (read-only, Plan agent). Sources: the S278 system audit (M27, M29, M31), ADR 0015 with amendment A1,
ADR 0019 d1 / d16, `docs/legal/dsar-erasure-runbook.md` §4, `docs/legal/dpa.md` §11, data standards DM-6 / DM-7, the
restore runbooks, and the code paths named below.

## 1. What exists today, and the gaps

### Part 1: tour retired

- **CIS (producer, done).** `gold_aa_internal.tour_lifecycle_event` → `catalog.v_tour_lifecycle_outbox` (events
  `retired|paused|restored|superseded`) and `catalog.v_tour_retired` (`catalog.tour.v1.3`). The tenant fan-out
  `services/tour_lifecycle/fanout.py` with the jobs in `services/jobs/tour_retirement_jobs.py` (`tour_retirement_fanout`,
  `retired_page_draft`, `tour_notice_email`, immediate or the daily digest); tenant bell `tour.discontinued` /
  `tour.reinstated`; a signed TripPlanner purge notice (`tripplanner_purge`, `catalog.tour.lifecycle.v1`).
- **Booking (done, AA-986 L5).** `backend/app/catalog/lifecycle.py`, kind `bk_tour_lifecycle_pull`: reads the outbox into
  `booking.inbox_events`. On `retired` it sends a staff notification per open trip case and trip plan (confirmed
  bookings and active holds listed); on restore `tour.reinstated`. It never cancels. New quotes and holds get 409
  `tour_not_served`; the delta feed lists the tour as `withdrawn` (`booking.b2b.v1` 1.9).
- **TripPlanner (done, AA-986 L6).** `backend/assembly/availability.py`: saved trips list `unavailable_stops`; the tour
  page answers 410; the purge runs from `POST /api/revalidate/catalog`.
- **CRM (the M29 gap).** No event consumer. The hourly `crm_catalog_sync` (`api/app/catalog/sync.py`) turns a 410 into
  `crm.aa_catalog_tour.served_state = 'retired'`, read only at use time (builder `aa_served_state`; reactive 409
  `aa_tour_not_served`). No flag on trips or options, no task, no check of held or confirmed lines. `crm.option` has the
  `option_draft_only` trigger, so a flag needs its own table; `crm.incident_flag` (AA-961) is the template.

### Part 2: offboarding and erasure

- **CIS.** Soft offboard `POST /admin/tenants/{id}/offboard` (`account_status = offboarding`, `/restore` reverses it);
  `account.status_changed` on `tenant.entitlements.v1` 1.6. Erasure: the `data_erasure` job
  (`services/jobs/erasure_job.py`, `services/erasure/inventory.py`, `plan.py`) with a DRY RUN fingerprint v2; apply
  needs `ERASURE_APPLY_ENABLED`, a Cognito staff session, `approved_fingerprint` and the retention window
  (`ERASURE_TENANT_RETENTION_DAYS`, default 30). Drilled once (S248). CIS only; S3, secrets and Cognito are manual.
- **CRM.** Owner-driven offboarding (`api/app/lifecycle/offboarding.py`, kind `crm_offboard`, `crm.erasure_request`,
  `crm.erase_subject('tenant')`, crypto-shred, receipt with `backup_purge_by` = erasure + 30 days), gated by
  `LIFECYCLE_DRY_RUN` and a 72 h cool-off. AA cannot run a CRM erasure (CRM18 trigger, `crm.ops.v1`). When CIS stops
  serving a tenant, the CRM only locks the agency.
- **Booking.** No tenant erasure. `bk_tenant_pull` suspends a gone tenant's partner. Booking holds no traveller identity
  (DM-6.8); it holds the agency name, B2B case free text, emergency contacts in `trip_case_checks`, notifications, audit
  before/after fields, and the bill-to snapshot on agency invoices (accounting exception).
- **TripPlanner.** No tenant erasure. Tenant tables (tp-028 FORCE RLS): `sessions`, `trip_drafts`, `trip_events`,
  `outbox`, plus `ai_spend_month` scope `tenant:<id>`. The DPA §11.2 table has no TripPlanner row.
- **Agreed schedule (draft, DPA §11):** exit window of 30 days, CRM 72 h cool-off, CIS 30-day retention window, Booking
  keeps commercial and accounting records, automated backups age out in 14 days.

### Part 3: restore

- **CRM (done).** Nightly sealed per-tenant export (`crm_pilot_backup`, 7 days) and
  `python -m app.portability.restore_drill` into `pg_temp` (runbook `docs/ops/runbooks/pilot-tenant-restore-drill.md`).
  The stored drill evidence contradicts itself (S278 audit finding 16): re-run it.
- **CIS and TripPlanner (the M27 gap).** Only whole-instance PITR (`restore-rds-pitr.md`; about 22 minutes, under
  1 USD per use). The gold bucket already expires `exports/` after 7 days.

## 2. Design

### Tour retired

No new CIS event. The CRM detects `served→retired` and `retired→served` in `crm_catalog_sync` and queues one
`crm_tour_retired_fanout` job per transition (idempotency key per source id, transition and change time). Per agency,
in its own transaction: `crm.tour_retired_flag` rows (kind `open_option|held_line|quoted_line|confirmed_line`, status
`open|cleared`), one task per affected trip (`aa_tour_discontinued`, trip owner, fallback agency owner). It never
writes a booking line or an option; a confirmed line gets an informational flag only. Reinstate clears the flags.
`paused` is ignored (ADR 0015 decision 5).

### Offboarding saga (orchestrator: CIS, master of the tenant account, ADR 0019 d1)

- New contract `tenant.erasure.v1` 1.0 (producer CIS; consumers CRM, Booking, TripPlanner). Requests through
  `catalog.v_tenant_erasure_v1` (Booking, TripPlanner) and `GET /tenant/v1/erasure-requests?after=` (CRM).
  `tenant.entitlements.v1` 1.7 adds `account.erasure_requested`. Reports through `booking.v_tenant_erasure_report_v1`,
  `tripplanner.v_tenant_erasure_report_v1` and a CRM `POST …/reports` (new M2M scope `cis.tenant/erasure`). Ids,
  counts and hashes only.
- CIS job `tenant_erasure_saga`, tables `shared.tenant_erasure_request` / `shared.tenant_erasure_step` (no FK to
  `shared.tenants`).
- **T0** soft offboard stops service everywhere; the request gets `not_before` = T0 + exit window; the CRM offers the
  owner a full export; a CIS restore before `not_before` cancels the request.
- **T + window:** (1) every app computes a DRY RUN plan hash (per table: action, count,
  `md5(string_agg(id || updated_at))`, no row values); (2) a combined fingerprint; (3) the tech lead approves it once
  (Cognito admin only, valid 24 h); (4) one pre-erase RDS snapshot; (5) apply in TripPlanner, Booking and CRM in
  parallel, each recomputing and matching its approved hash (`plan_changed` refuses), then CIS last; (6) verify: a
  census of every `pii:`-tagged column for the tenant must be 0; receipt; (7) manual checklist outside the database
  (S3 prefixes, per-tenant secrets, Cognito partner users, error tracker).
- Audit row per app and mode, plus one row in `docs/legal/retention-log.md`.
- Guards: the saga refuses the pilot tenant; on Dev, apply only for synthetic tenants; default-off apply flags per app.
- Per-app actions (proposed): CIS today's inventory; CRM today's erase with crypto-shred run by the platform after the
  window; Booking anonymise (free text redacted, agency name replaced, audit before/after redacted, money rows and
  bill-to kept, `bk_tenant_pull` skips erased partners); TripPlanner delete the tenant's rows and merge its spend rows.

### Restore drill (same shape as the CRM's, cheapest option)

- **CIS:** job `tenant_backup` (on demand; nightly for the pilot) reusing the erasure inventory as the table catalogue;
  JSONL + manifest + checksums to the gold bucket `exports/tenants/<t>/cis/` (existing 7-day rule);
  `python -m services.tenant_backup.restore_drill --tenant <uuid>` loads into `pg_temp`, compares manifest / restored /
  live counts, writes one audit row.
- **TripPlanner:** kind `tp_tenant_backup` (4 tables) and a jobs-Lambda `restore_drill` op; Lambda IAM for its prefix only.
- **Cost:** no new resource (existing bucket and rule); S3 storage is cents per month; PITR stays the fallback.

## 3. Lanes (migrations first, MIG-4; all expand-only)

| Lane | Repo | Content |
|---|---|---|
| L0 | root | contract `tenant.erasure.v1`, `tenant.entitlements.v1` 1.7, DM-7.1 retention rows, DSAR runbook §4 as the saga, tenant restore drill runbook, DPA §11.2 TripPlanner row, job kinds |
| L1 | AA-Partner | crm-063 `crm.tour_retired_flag` + fan-out job, task kind, builder and trip badge (tour part first); crm-064 + erasure feed after D2 |
| L2 | AA-CIS-App | CIS 407 (erasure request / step tables, `catalog.v_tenant_erasure_v1`), saga, routes, admin tab, `tenant_backup` + restore drill |
| L3 | AA-Booking | bk-056 (erasure log, report view), `bk_tenant_erase` with DRY RUN / `--expect-plan`, pull skips erased partners |
| L4 | AA-TripPlanner-Web | tp-030 (erasure log, `erase_tenant` function, report view), erase and backup jobs, restore drill op; Infra IAM + flag |

Order: L0 → CIS 407 → bk-056 / tp-030 / crm-063 → L1 tour part, L3, L4 code (each feature-detects the CIS view) → L2
saga → crm-064 + L1 saga part → drills.

## 4. Decisions for the tech lead (proposed defaults)

| # | Decision | Proposed default |
|---|---|---|
| D1 | Exit window | 30 days (DPA §11.1) |
| D2 | AA erases CRM data after the window without the owner's click | Yes, as DPA §11.1 says (changes the CRM18 rule; export offered at T0) |
| D3 | Booking | Anonymise, not delete; money and bill-to rows kept (accounting exception) |
| D4 | TripPlanner | Delete every tenant row; spend rows merged into the app scope |
| D5 | CIS | Today's inventory; live posts stay on the agency's own channels (receipt says so) |
| D6 | Cognito partner users | Delete users whose only membership was this tenant (manual step) |
| D7 | Approval | One combined fingerprint approval and one shared pre-erase snapshot |
| D8 | Scope | Saga refuses the pilot tenant; on Dev, apply only for synthetic tenants |
| D9 | How the CRM learns of a retirement | The hourly sync (no new CIS event feed) |
| D10 | CRM task | One per affected trip, to the trip owner; confirmed lines get an informational flag only |
| D11 | Per-tenant export | Nightly only for the pilot, kept 7 days |

## 5. Risks

- CIS must erase last (it deletes `shared.tenants`, which the other apps read the request through).
- `bk_tenant_pull` would write the agency name back unless it skips erased partners.
- Plan hashes drift while a tenant still writes; T0 stops service everywhere first.
- CIS export size (raw tours, atoms): add a size cap and report it.
- Re-run the CRM restore drill (contradictory S278 evidence).

## 6. Proving the Done-when on Dev

- Exit window and backup age-out: drill with window 0 on a synthetic tenant; unit-test the schedule with an injected
  clock; later read the oldest restorable time against the erase time.
- "A re-read finds no personal data": the `pii:` column census (counts only) from a new session, the CRM crypto-shred
  canary, and listings of the out-of-database items.
- "Each app reports erase done": a synthetic tenant with rows in all four apps (CIS E2E fixtures, the CRM E2E agency,
  TripPlanner trips through the planner, a Booking B2B case).
- "A retired synthetic tour": reuse the S276 AA-1039 drill guard (a Dev tour no non-E2E tenant uses), retire it, prove
  the CRM flags, the Booking staff notice and TripPlanner `available: false`, then restore at once.
- Every DRY RUN approval: a Linear comment with the job ids, plan hashes, the combined fingerprint and the approval.
