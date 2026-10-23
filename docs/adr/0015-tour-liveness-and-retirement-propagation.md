# ADR 0015 — Tour liveness and retirement propagation

- **Status:** Accepted (23/10/2026, S248). Nghiệp asked for the rule in S248 and decided Q1–Q10 on the S248 decision
  page (table at the end); Q2, Q4 and Q8 differ from the first proposal. Q11 (added by this ADR) takes its proposed
  answer; Nghiệp can change it, and the decision it affects is named.
- **Scope:** AA-Ecosys: AA-CIS-App (the served state, the write service, the read view, tenant `/v1` and portal,
  schema `catalog`), AA-Booking (quote, hold, trip case legs, B2B feed), AA-TripPlanner-Web (tour page, saved trips,
  hand-off), AA-Partner (offer lists, through `catalog.http.v1` and `booking.b2b.v1`), AA-CIS-Infra (grants, the
  nightly probe), the root repo (contracts).
- **Amended:** A1, 23/10/2026 (AA-987, S249): TripPlanner cache purge notice fed from the outbox (section
  "Amendments").
- **Amends / Supersedes:** none. It keeps ADR 0007's rule that liveness is derived from columns, not stored (decision
  1), and adds the change record that rule did not cover (decision 4).
- **Implements:** ADR 0001 decision 1 and ADR 0002 (CIS is the content system of record and the only writer);
  ADR 0008 decision 3 (playbook steps 6–7: cross-app reads through contract views, events through an outbox),
  decision 5 (contracts are views only; CIS contract views live in `catalog`) and decision 9 (tour key
  `(source_system, source_id)`); [`contracts/README.md`](../contracts/README.md) rules 1–5.
- **Design and evidence:** audit memo
  [`docs/audits/2026-10-23-S248-tour-deletion-propagation/memo.md`](../audits/2026-10-23-S248-tour-deletion-propagation/memo.md)
  (§2 matrix with file:line evidence for every layer, §3 target rule, §4 slices L1–L7, §5 questions). Live probe of
  the CIS half on Dev, 23/10/2026: 65 dead tour groups (44 trashed sources, 21 superseded without a successor), and
  **zero** derivatives of a dead tour in any layer, zero anomalies. The leaks the memo found are paths that are open,
  not damage that has happened, so no data clean-up is needed before the slices.
- **Related Linear:** AA-986 (this rule and its slices); AA-716 (the one cascading trash path today); AA-679 (catalog
  read model, its deferred `catalog.tour.*` events); AA-975 (Booking B2B events to the CRM); AA-928 / AA-976
  (AA-Partner catalog consumer).

## Context

Nghiệp's requirement (S248): when a tour is deleted at the source (S0/A0), every derivative of it is hidden across the
ecosystem, tenants included; a tenant keeps its own T2 copy but is warned that AA no longer serves the tour.

The audit memo (§1, §2) shows the ecosystem does not do this today:

- **One good path, unreachable for the tours that matter.** `PATCH /admin/tours/{id}/trash` (AA-716) cascades
  correctly, but the UI offers it only for tours still `ingested`, which have no derivatives.
- **Three writers that change a source without any cascade** (Excel replace / supersede, `set-active`,
  `DELETE /admin/raw-tours/{id}`) and **four paths that silently revive a deleted tour** (Master Activate, approving a
  pending review of a dead source, re-upload with the same name, re-upload with a near-duplicate name).
- **Two liveness rules (split brain).** `catalog._live_tour` checks Master and source;
  `acp_contract.v_active_tour_atoms` checks Master only, and its rule is copied by hand into two services.
- **The tenant warning never reaches the tenant.** `tour.discontinued` is written to `shared.notifications`, which
  only the staff bell reads. Tenant jobs (T2 rewrite, T8, T9) keep running and spending on a dead tour; T7 still plans
  it; T11 still publishes new posts about it.
- **Booking and TripPlanner only hide the tour from lists.** Booking still quotes and holds it; TripPlanner shows saved
  trips with the dead tour and no warning, and answers 404 where the `catalog.http.v1` contract promises 410.

The root cause is that "hide the derivatives" is decided separately in each write path and each reader, never in one
place. Consumers outside CIS also have no way to learn that a tour left: since S237 D4 they read the catalog live and
a retired tour is simply absent, which they cannot tell from "never existed".

## Decisions

### 1. One canonical served state per catalog key, owned by CIS, derived from real columns

The unit is the **catalog key** `(source_system = 'cis', source_id = silver_aa_internal.raw_tours.source_key)`, where
`source_key = COALESCE(source_group_id, tour_id)` (CIS 258), stable across re-uploads. CIS owns the state. It is
**derived** from columns that already exist, never stored as a second truth:

| State | Definition on today's columns | Reason (working values) | Seen by users |
|---|---|---|---|
| `served` | The key has a live version (`raw_tours.source_status = 'active' AND raw_tours.deleted_at IS NULL`; at most one per group, unique index `uq_raw_tours_active_per_group`) and that version's Master is live (`gold_aa_internal.published_tours.master_status = 'active' AND published_tours.deleted_at IS NULL`) | — | Normal |
| `retired` | The key was ever served (some version of the group has a `published_tours` row, any status) and either: no live version because the source was deleted at S0/A0 (trash or `DELETE`); or the live version's Master is `trashed`; or no version is live, none is trashed and the newest one is `superseded` (a supersede whose successor is gone) | `source_deleted`, `master_trashed`, `superseded_orphan` | Every derivative hidden; tenant copies kept with a "no longer served by AA" warning |
| `paused` | A live version exists but its Master is `inactive` (Q1), or a supersede is waiting for the new version's Master (Q11) | `master_inactive`, `superseded_pending` | Hidden like `retired`; badge "paused"; no push notification (Q1); per-consumer answers in decision 5 |
| `restored` | A key that was `retired` or `paused` and is `served` again | the action that served it (`restore`, `publish`) | Behaves as `served`; consumers that acted on the retirement undo it (badges removed, `tour.reinstated` sent) |

- A key that was never served (no version has a Master: uploaded, never published) has no state: consumers see 404,
  not 410. This covers a group whose versions are all `superseded` and that never had a Master.
- **All-superseded groups** (`superseded_orphan`, the probe bucket of the same name): Dev has 21 of them on 23/10/2026.
  The probe's Master counts (892 Master rows, all `master_status = 'active'`, and zero active Masters in any dead
  group) say none of them ever had a Master, so today they are "never served" and answer 404; slice L1 confirms that
  with one read-only count before the view relies on it. A group of this shape that once had a Master is `retired`
  (410). Alternative (Q11, not yet decided): treat the shape as an anomaly the nightly probe reports and slice L2
  cleans up (the group is set to trashed through the service); that answer changes decisions 1 and 6 only.
- **Supersede is not deletion.** Replacing a version (Excel replace/update) keeps the key `served` under the same
  `source_key`. What belonged to the old version (Master, atoms, ranking, route) moves to the new version or is
  switched off. **Never two active Masters in one group.** A tenant T2 copy that points at the old version gets no badge
  and no notification: a supersede is invisible to the tenant (Q2, Nghiệp S248).
- `raw_tours.lifecycle_stage` is **not** a deletion signal (no code writes it; Q9). It keeps its sales meaning
  (`phasing_out`); readers that filter `retired` on it switch to the served state.
- `restored` is a recorded transition (decision 4) more than a fourth steady state: the derived state of a restored key
  is `served`. It is listed so consumers know to reverse what they did on `retired` / `paused`.

### 2. One CIS write service

Every change to a key's served state goes through **one CIS service** (working name `services/tour_lifecycle`) with
the actions `retire`, `pause`, `supersede`, `restore` and `publish`. Every writer in memo §2.1 calls it: trash,
`DELETE` raw-tours, staging replace/update, `set-active`, Master trash / deactivate / activate, restore. The two
**INSERT** paths that set these columns also go through it, because both can change the served state:

- **Inserting a version** (ingest / staging): the row is born `source_status = 'active'` (default of CIS 052). When
  the group already has a version this is `supersede` (old version `superseded`, key `paused` /
  `superseded_pending` until the new Master publishes, Q11); for a new key it is a plain insert with no event,
  because a key without a Master has no state (decision 1).
- **Inserting a Master** (`process_export`, born `master_status = 'active'`, default of CIS 052) is `publish`. When
  the key was `paused` or `retired` (a `superseded_pending` gap, or a re-publish after a restore of the source),
  `publish` writes the closing `restored` event, so the tombstone (decision 4) clears in the same transaction that
  serves the key again.

In **one transaction** the service:

1. changes the source and Master status and records **why**, so `restore` re-enables only the Masters this service
   switched off (not a Master staff had deactivated on purpose);
2. dismisses pending reviews of the key;
3. cancels queued `t2_rewrite`, `t8_angles` and `t9_write` jobs of the key;
4. writes the change record (decision 4);
5. notifies **every tenant with a derivative** of the key: a T2 copy, a Slate subject, an angle-gate request, a
   content piece or a publish-log row, not only T2 holders (Q10).

After commit it clears caches, recomputes ranking and routes with the **new** state, rebuilds the graph
(`place_extract` on restore) and rechecks the public trip pages.

Rules the service enforces:

- Activating a Master whose source is not live answers **409 `source_not_live`**, with the choice "restore the source
  too".
- Approve and `process_export` refuse a source that is not live (409 `source_not_live`); `set-active` refuses a
  trashed row.
- Re-uploading a deleted tour (exact or near-duplicate match) shows "deleted on <date>" in staging and offers
  **Restore** or **Create a new tour**; it never revives silently (Q6).
- Retiring a published tour is open to staff with Master Content rights and to admins; the confirm dialog shows a dry
  run of the tenants, pieces, posts and bookings affected (Q8, Nghiệp S248).
- No other CIS code changes `raw_tours.source_status`, `raw_tours.deleted_at`, `published_tours.master_status` or
  `published_tours.deleted_at`, and no other code inserts into `raw_tours` or `published_tours`. A CIS guard test
  enforces both, UPDATE and INSERT alike (the service is the only allowed writer): it scans for SQL that writes these
  columns or tables outside the service module and fails the CI run.

### 3. One read view inside CIS

CIS reads the served state from **one view** (working name `gold_aa_internal.v_tour_liveness`: `source_system`,
`source_id`, `tour_id`, `state`, `reason`, `changed_at`) or one SQL function behind it. `catalog._live_tour`,
`acp_contract.v_active_tour_atoms`, the two hand copies of its rule (Slate subject seed, route guard), approve,
`process_export`, the tenant pool, `/v1/trip/{id}` and the T7 planner all use it. The first step (slice L1) is
smaller: add the source condition to `v_active_tour_atoms` and its two copies, so both sides of CIS agree at once.

The view lives in a **CIS schema, not in `catalog`**: `catalog` holds contract views only (owner `catalog_owner`,
`schema-ownership.md`; ADR 0008 decision 5), and the CIS runtime `cis_app` has no `USAGE` on `catalog` (the live probe
got `InsufficientPrivilegeError` on `catalog.v_tour` as `cis_app`). `gold_aa_internal` fits: `cis_app`, `aa_app_user`
(tenant pool) and `catalog_owner` already have `USAGE` there. Grants: `SELECT` to `cis_app` and `aa_app_user`, and to
`catalog_owner` so `catalog._live_tour` reads it (the view reads RLS tables such as `published_tours`, so it follows
the catalog-view recipe and the reader policies, as CIS 266 did for `catalog_owner`). It is not granted to other apps:
consumers outside CIS use decision 4 and the existing `catalog.v_tour`, which keeps showing live tours only.

### 4. A CIS-owned change record and outbox for the other apps

CIS adds an append-only record of served-state changes per key. The **table** lives in a CIS schema written by
`cis_app` (working name `gold_aa_internal.tour_lifecycle_event`: key, `tour_id`, event
`retired | paused | restored | superseded`, reason, `replaced_by_tour_id` for a supersede, `occurred_at`,
`idempotency_key`), owned by `cis_owner`, with `cis_app` `INSERT` + `SELECT` only (no `UPDATE` / `DELETE`: append-only)
and `catalog_owner` `SELECT`. Only the write service (decision 2) inserts. `catalog` stays views only, so no
`schema-ownership.md` exception and no `cis_app` grant on `catalog` is needed; slice L4 adds the two views to the
`catalog` row there and a retention row for the table (ADR 0008 decision 3 step 9).

Two **contract views** read it, in `catalog`, owned by `catalog_owner` like CIS 225 and granted to `booking`,
`tripplanner` and `aa_app_user` (unguarded, `contracts/README.md` rule 5):

- `catalog.v_tour_lifecycle_outbox`: the events, for pull consumers (ADR 0008 decision 3 step 7; contracts rules 3–4:
  idempotency key, cursor);
- `catalog.v_tour_retired`: the tombstone, one row per key whose latest event is `retired`, `paused` or `superseded`
  (shown as `paused` / `superseded_pending` until `publish` writes `restored`), with `state` and `reason`, so a
  consumer can tell 410 (`retired`) from a temporary absence (`paused`) and list withdrawn products in a delta feed
  (`retired` only).

Contract **`catalog.tour.v1.3`** (additive over 1.2) describes both; `catalog.v_tour` does not change. This does not
reverse S237 D4: tour content is still read live, never copied; the record carries only state changes, which a live
read of `v_tour` cannot show. It is the narrow part of AA-679's deferred `catalog.tour.*` events. The derived state
(decision 1) stays the truth; the nightly probe (decision 6) fails when the tombstone and the derived state disagree.

The names in decisions 2–4 are working names; the slice PRs fix them.

### 5. Behaviour per consumer

**Tenant (CIS portal and tenant `/v1` API):**

- **Keep** the tenant's T2 copies, content pieces and exports; delete nothing of the tenant's. RLS already keeps
  them visible to the tenant.
- Add `served_status`, `served_reason` and `discontinued_at` to my-versions, version detail, marketplace, review /
  piece and publish-pending responses.
- A persistent **badge** on My Tours, Content and Publish ("AA no longer serves this tour"; "paused" for `paused`,
  none for a supersede, Q2).
- The portal **bell** reads the tenant's real notifications (`tour.discontinued`, `tour.reinstated`) through a
  tenant-scoped `/v1/notifications` route (Q7). Email and webhooks come later, from the outbox of decision 4.
- **New work on the tour is refused** with 409 `tour_discontinued` and a plain sentence: rewrite, retry, T8 goal,
  T9 write, publishing a new post. Slate `GET` filters the tour; the T7 planner drops it.
- **Posts already live** on the tenant's WordPress / Facebook stay up (they are the tenant's site and page): flagged
  "tour discontinued: remove or edit", with a one-click unpublish on the channel. AA never unpublishes them on its own
  (Q3). The admin A4 force-unpublish either calls the channel or stops saying the post was removed.

**AA-Booking:**

- Refuse **new** quotes and holds on a key that is not `served`: 409 `tour_not_served` (additive error in
  `booking.b2b.v1`).
- **Keep** confirmed bookings, confirmed holds and existing trip cases, with a staff flag on the leg and the plan,
  **and notify staff** (a staff notification per affected trip case / plan when the key is retired, through the
  staff bell; Q4, Nghiệp S248). Cancelling them is an operations decision taken by staff, never automatic.
- The plan list gets an "orphaned plans" filter (plans whose tour left the catalog, with the reason).
- The B2B delta feed lists withdrawn products (`withdrawn`, from `catalog.v_tour_retired`); the event
  `product.withdrawn` goes into AA-975.

**AA-Partner:** hides the tour from offer lists and marks old proposal lines "no longer offered", driven by the 410 of
`catalog.http.v1` and the Booking delta feed. No own slice; the requirement goes into AA-928 / AA-976.

**AA-TripPlanner-Web:**

- Browse, countries and sitemap already hide the tour (they read `catalog.v_tour`).
- The tour page answers **410** for a `retired` key. For a superseded key the slug keyed on `source_id` already leads
  to the current version.
- **Saved trips** (`GET /trip/{id}`) mark each stop of a non-served tour `available: false` and the page shows a
  banner "no longer offered". The hand-off to Booking still goes, carrying the flag, so staff see why a leg is
  unmatched.

**SEO** (CIS `/v1/trip/{id}`, TripPlanner tour page): **410 Gone** for `retired`; **301** to the current tour for a
superseded version of the same `source_key`; a restored tour's page comes back (Q5). Sitemaps already drop it.

**A `paused` key** (Master `inactive`, Q1; or `superseded_pending`, Q11) is hidden everywhere like a `retired` one,
but every answer says "temporary", never "gone":

| Consumer | Answer for `paused` |
|---|---|
| Tenant (portal, `/v1`) | Badge "paused"; no push notification (Q1); new work refused with 409 `tour_paused` (working name) |
| AA-Booking | New quotes and holds refused with the same 409 `tour_not_served`, `reason` set; confirmed work kept, no staff flag; the B2B delta feed does **not** list it as `withdrawn` |
| AA-TripPlanner-Web | Tour page **404** (not 410); saved trips mark the stop `available: false` with "temporarily unavailable" |
| SEO (`/v1/trip/{id}`, tour page) | **404**, no 410 and no 301, so search engines keep the URL for when it returns; `superseded_pending` may answer 503 with `Retry-After` instead if the gap proves long (decided in L4) |
| AA-Partner | Hidden from offer lists; proposal lines are not marked "no longer offered" |

**Restore:** `restore` returns every layer to `served`, sends `tour.reinstated` to exactly the tenants that got the
warning, removes the badges, writes `restored` to the record, enqueues `place_extract`. Other apps see the tour again
through the catalog and the record.

### 6. One ecosystem gate

The live probe of memo §6 (CIS half and master half: Booking and TripPlanner layers) becomes a script in AA-CIS-Infra
that runs **nightly** beside DB Schema Dump and fails when a derivative of a non-served key is live, when two Masters
are active in one group, when a Master is active over a dead source, when the tombstone disagrees with the derived
state (including a `paused` row left open after the key is served again), or when an all-superseded group has a
Master but no `retired` row. It is the regression test of this ADR. `acp_contract.v_trip_registry` (no reader)
goes into the Dead Table Registry.

### 7. Order of work

Slices as in memo §4: **L7a (this ADR) → L1** (close the A-side leaks: view condition, approve and export refuse dead
sources) **→ L2** (the write service and every writer through it, admin UI) **→ L3** (tenant fields, badge, bell,
409s, job cancel) **→ L4** (change record, outbox, `catalog.tour.v1.3`, 410/301) **→ L5** Booking and **L6**
TripPlanner in parallel **→ L7b** nightly probe. L1 is small and closes the worst leaks on its own. Every slice that
changes a view, a grant or auth is reviewed by an agent before merge (DM-11.5).

## Consequences

- (+) One answer to "is this tour served?", the same in CIS, Booking, TripPlanner, AA-Partner and the tenant API.
- (+) Tenants keep what they paid for and are told, in the product, when AA stops serving a tour; no LLM spend on
  dead tours.
- (+) Booking never sells a retired tour, and keeps what was already sold.
- (+) The `catalog.http.v1` promise "a removed tour is 410" becomes keepable; SEO gets correct 410/301 answers.
- (+) Revivals become explicit actions with a record, instead of side effects of Activate, approve or re-upload.
- (+) Cost about $0: no new AWS service; the nightly probe is a few seconds of an ECS task (under $0.10 a month).
- (−) Every CIS writer of source or Master status must move into one service (slice L2, the largest), and a guard test
  must keep it there.
- (−) A new contract minor (`catalog.tour.v1.3`), a new CIS table (`gold_aa_internal`) and two new `catalog` views
  to own and test; consumers gain a pull job.
- (−) `process_export` and the version insert of ingest / staging move behind the write service too (decision 2), so
  slice L2 touches the publish path, not only the trash and status buttons.
- (−) More 409 paths for tenants and B2B callers; messages must be clear, or support load moves to Nghiệp.
- (−) Until L4 ships, consumers still cannot tell 410 from 404, and the CRM still needs a full resync to see a
  withdrawal.

## Alternatives considered

- **Fix each endpoint where the audit found a leak, no shared rule.** Rejected: that is how the split brain came to
  be; the next writer would leak again.
- **Hard delete with cascade.** Rejected: it destroys tenant copies and sold bookings, and makes restore impossible.
- **Store the served state as a column and treat it as the truth.** Rejected: a second truth drifts from the status
  columns that every reader already uses; ADR 0007 kept liveness derived for that reason. The change record stores
  transitions only, and the probe checks it against the derived state.
- **Use `raw_tours.lifecycle_stage` (`retired`).** Rejected: nothing writes it, and it means sales phase-out (Q9).
- **Let consumers detect retirement by diffing `catalog.v_tour`.** Rejected: they cannot tell 410 from 404 or say
  why, and the CRM would have to resync everything.
- **Push webhooks from CIS to each app.** Rejected for now: the ecosystem pattern is outbox → pull → inbox
  (ADR 0001, 0008); a tenant webhook can be fed from the same outbox later (Q7). Narrowed by amendment A1 (below): a signed
  cache purge notice to TripPlanner, fed from this outbox, is allowed; the outbox stays the source.

## Questions and decisions (Nghiệp, S248 decision page)

Q1–Q10 were decided by Nghiệp on the S248 decision page (23/10/2026). Q11 keeps its proposed answer until he changes it; a different answer changes only the decisions named in the last column.

| # | Question | Decision | Changes |
|---|---|---|---|
| Q1 | Does deactivating a Master (source still live) count as "no longer served"? | Hidden exactly like `retired`, but the badge says "paused" and no notification is pushed. **Trashing** a Master counts as `retired`, with the warning | 1, 5 |
| Q2 | Supersede (Excel replace): what happens to a tenant T2 copy of the old version? | Not a discontinuation, and **nothing is shown to the tenant** (no badge, no notification). (Proposed was a badge "AA source updated"; Nghiệp chose none.) | 1, 5 |
| Q3 | Tenant posts already live about a retired tour: unpublish automatically? | No. Flag, one-click unpublish, and mention in the notification | 5 |
| Q4 | Booking: future departures with seats sold, confirmed bookings of a retired tour? | Keep, staff flag **and a staff notification**; refuse new quotes and holds. Cancelling is a staff operations decision, never automatic | 5 |
| Q5 | SEO: 410 or redirect? | 410 when retired; 301 when superseded (same `source_key`); the page returns on restore | 5 |
| Q6 | Re-uploading a deleted tour: restore automatically or ask? | Staging shows "deleted on <date>"; staff choose Restore (runs `restore` + `tour.reinstated`) or Create a new tour | 2 |
| Q7 | Channel for the tenant warning? | Persistent badge (the source of truth) + the portal bell reading the tenant's notifications. Email and webhook later, from the outbox | 5 |
| Q8 | Who may retire a published tour? | Staff with Master Content rights **and admins**; the confirm dialog shows a dry run of affected tenants, posts and bookings | 2 |
| Q9 | `lifecycle_stage` (nothing writes it)? | Not a deletion signal. Kept for sales (`phasing_out`); T7 and TripPlanner switch to the served state | 1 |
| Q10 | Is a tenant that uses the tour only through Slate / planning (no T2) warned? | Yes: every tenant with any derivative (subject, angle request, piece, publish-log row) | 2 |
| Q11 (proposed, not yet decided) | Between a supersede and the publish of the new version's Master, is the key served? (added by this ADR; today the tour drops out of the catalog in that gap) | `paused`, reason `superseded_pending`, no notification; consumers treat it as temporary (decision 5 `paused` table: TripPlanner and SEO 404, not 410). The `publish` action of the new Master closes it with `restored`. Same question for a group whose versions are all `superseded`: retired (410) if it ever had a Master, no state (404) if not; alternative, a probe anomaly that L2 cleans up. Alternative for the gap: keep serving the old version until the new Master is published | 1, 2, 5, 6 |

## Amendments

### A1 (23/10/2026, AA-987, S249): a signed cache purge notice from the outbox to TripPlanner

- **Why.** Decision 5 asks TripPlanner to answer 410 and drop a retired tour; pulling `catalog.v_tour_retired` alone
  left it on the public site for up to 30 minutes (S248 measurement on Dev: tour page 410 after ~16 min, browse list
  after ~30 min), because the tour page, the lists and the Vercel CDN copies of the browse BFF are cached for the
  catalog TTL. TripPlanner has no scheduler that runs every minute (Vercel Hobby cron runs once a day), and a new
  EventBridge schedule for a pull job would add an AWS resource for one consumer.
- **Decision.** CIS delivers every row of `catalog.v_tour_lifecycle_outbox` to TripPlanner as an HTTP notice,
  contract [`catalog.tour.lifecycle.v1`](../contracts/catalog.tour.lifecycle.v1.openapi.yaml): CIS job
  `tripplanner_purge`, one job per event, idempotency key `tripplanner_purge:<event idempotency_key>` (shared.job is
  the delivery inbox, contracts rules 3 and 4), enqueued after commit, by the export publish, and by a sweep of the
  last 2 hours in the api ops sampler; signed with HMAC-SHA256 (`X-AA-Signature`, ±300 s), secret
  `aa-cis/<env>/tripplanner-revalidate-hmac` = Vercel env `CATALOG_REVALIDATE_SECRET`. TripPlanner
  (`POST /api/revalidate/catalog`) verifies it and drops its caches; it stores nothing, so a replay is harmless.
- **What does not change.** The outbox stays the one source of the change record (decision 4) and the pull contract
  for every consumer: the notice carries the outbox row as is, and TripPlanner still reads `catalog.v_tour_retired`
  for the 410 and its reason. A lost or refused notice costs freshness only (the TTLs still bound the lag), never
  correctness. AA-Booking and AA-Partner keep pulling. A tenant webhook (Q7) remains "later, from the outbox".
- **Cost.** One Secrets Manager secret (about $0.40 a month); no other AWS resource.
