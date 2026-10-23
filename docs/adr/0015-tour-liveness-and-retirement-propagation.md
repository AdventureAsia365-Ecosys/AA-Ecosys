# ADR 0015 — Tour liveness and retirement propagation

- **Status:** Proposed (23/10/2026, S248). Nghiệp asked for the rule in S248; the open questions Q1–Q11 at the end
  carry proposed answers that are **pending Nghiệp**. Decisions that depend on one of them name it, so a different
  answer changes one paragraph, not the design.
- **Scope:** AA-Ecosys: AA-CIS-App (the served state, the write service, the read view, tenant `/v1` and portal,
  schema `catalog`), AA-Booking (quote, hold, trip case legs, B2B feed), AA-TripPlanner-Web (tour page, saved trips,
  hand-off), AA-Partner (offer lists, through `catalog.http.v1` and `booking.b2b.v1`), AA-CIS-Infra (grants, the
  nightly probe), the root repo (contracts).
- **Amends / Supersedes:** none. It keeps ADR 0007's rule that liveness is derived from columns, not stored (decision
  1), and adds the change record that rule did not cover (decision 4).
- **Implements:** ADR 0001 decision 1 and ADR 0002 (CIS is the content system of record and the only writer);
  ADR 0008 decisions 6 and 7 (cross-app reads through contract views, events through an outbox);
  [`contracts/README.md`](../contracts/README.md) rules 1–5.
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

| State | Definition on today's columns | Seen by users |
|---|---|---|
| `served` | The key has a live version (`raw_tours.source_status = 'active' AND raw_tours.deleted_at IS NULL`; at most one per group, unique index `uq_raw_tours_active_per_group`) and that version's Master is live (`gold_aa_internal.published_tours.master_status = 'active' AND published_tours.deleted_at IS NULL`) | Normal |
| `retired` | No live version in the group because the source was deleted at S0/A0 (trash or `DELETE`), or the live version's Master is `trashed` | Every derivative hidden; tenant copies kept with a "no longer served by AA" warning |
| `paused` | A live version exists but its Master is `inactive` (Q1), or a supersede is waiting for the new version's Master (Q11) | Hidden like `retired`; badge "paused"; no push notification (Q1) |
| `restored` | A key that was `retired` or `paused` and is `served` again | Behaves as `served`; consumers that acted on the retirement undo it (badges removed, `tour.reinstated` sent) |

- A key that was never served (uploaded, never published) has no state: consumers see 404, not 410.
- **Supersede is not deletion.** Replacing a version (Excel replace/update) keeps the key `served` under the same
  `source_key`. What belonged to the old version (Master, atoms, ranking, route) moves to the new version or is
  switched off. **Never two active Masters in one group.** A tenant T2 copy that points at the old version gets the flag
  "AA source updated", not "discontinued" (Q2).
- `raw_tours.lifecycle_stage` is **not** a deletion signal (no code writes it; Q9). It keeps its sales meaning
  (`phasing_out`); readers that filter `retired` on it switch to the served state.
- `restored` is a recorded transition (decision 4) more than a fourth steady state: the derived state of a restored key
  is `served`. It is listed so consumers know to reverse what they did on `retired` / `paused`.

### 2. One CIS write service

Every change to a key's served state goes through **one CIS service** (working name `services/tour_lifecycle`) with
the actions `retire`, `pause`, `supersede` and `restore`. Every writer in memo §2.1 calls it: trash, `DELETE`
raw-tours, staging replace/update, `set-active`, Master trash / deactivate / activate, restore. In **one transaction**
it:

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
- Retiring a published tour is open to staff with Master Content rights; the confirm dialog shows a dry run of the
  tenants, pieces, posts and bookings affected (Q8).
- No other CIS code changes `raw_tours.source_status`, `raw_tours.deleted_at`, `published_tours.master_status` or
  `published_tours.deleted_at`. A CIS guard test enforces it (the service is the only allowed writer).

### 3. One read view inside CIS

CIS reads the served state from **one view** (working name `catalog.v_tour_liveness`: `source_system`, `source_id`,
`tour_id`, `state`, `reason`, `changed_at`) or one SQL function behind it. `catalog._live_tour`,
`acp_contract.v_active_tour_atoms`, the two hand copies of its rule (Slate subject seed, route guard), approve,
`process_export`, the tenant pool, `/v1/trip/{id}` and the T7 planner all use it. The first step (slice L1) is
smaller: add the source condition to `v_active_tour_atoms` and its two copies, so both sides of CIS agree at once.

The view is internal to CIS (not granted to other apps): consumers outside CIS use decision 4 and the existing
`catalog.v_tour`, which keeps showing live tours only.

### 4. A CIS-owned change record and outbox for the other apps

CIS adds an append-only record of served-state changes per key in schema `catalog` (working name
`catalog.tour_lifecycle_event`: key, `tour_id`, event `retired | paused | restored | superseded`, reason,
`replaced_by_tour_id` for a supersede, `occurred_at`, `idempotency_key`). Only the write service (decision 2) inserts.
Two views read it, owned by `catalog_owner` like CIS 225 and granted to `booking`, `tripplanner` and `aa_app_user`
(unguarded, `contracts/README.md` rule 5):

- `catalog.v_tour_lifecycle_outbox`: the events, for pull consumers (ADR 0008 decision 7; cursor rule of contracts
  rule 4);
- `catalog.v_tour_retired`: the tombstone, one row per key whose latest event is `retired` or `paused`, so a consumer
  can answer 410 instead of 404 and list withdrawn products in a delta feed.

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
  "AA source updated" for a supersede).
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
- **Keep** confirmed bookings, confirmed holds and existing trip cases, with a staff flag on the leg and the plan.
  Cancelling them is a business decision for Ms. Thư, not automatic (Q4).
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

**Restore:** `restore` returns every layer to `served`, sends `tour.reinstated` to exactly the tenants that got the
warning, removes the badges, writes `restored` to the record, enqueues `place_extract`. Other apps see the tour again
through the catalog and the record.

### 6. One ecosystem gate

The live probe of memo §6 (CIS half and master half: Booking and TripPlanner layers) becomes a script in AA-CIS-Infra
that runs **nightly** beside DB Schema Dump and fails when a derivative of a non-served key is live, when two Masters
are active in one group, when a Master is active over a dead source, or when the tombstone disagrees with the derived
state. It is the regression test of this ADR. `acp_contract.v_trip_registry` (no reader) goes into the Dead Table
Registry.

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
- (−) A new contract minor (`catalog.tour.v1.3`) and a new table in `catalog` to own and test; consumers gain a pull
  job.
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
  (ADR 0001, 0008); a tenant webhook can be fed from the same outbox later (Q7).

## Open questions (proposed answers, pending Nghiệp)

Each answer below is what this ADR assumes. A different answer changes only the decision named in the last column.

| # | Question | Proposed answer (pending Nghiệp) | Changes |
|---|---|---|---|
| Q1 | Does deactivating a Master (source still live) count as "no longer served"? | Hidden exactly like `retired`, but the badge says "paused" and no notification is pushed. **Trashing** a Master counts as `retired`, with the warning | 1, 5 |
| Q2 | Supersede (Excel replace): what happens to a tenant T2 copy of the old version? | Not a discontinuation. Badge "AA source updated" and a rewrite button on the new version that does not use quota | 1, 5 |
| Q3 | Tenant posts already live about a retired tour: unpublish automatically? | No. Flag, one-click unpublish, and mention in the notification | 5 |
| Q4 | Booking: future departures with seats sold, confirmed bookings of a retired tour? | Keep, staff flag; refuse new quotes and holds. Cancelling is Ms. Thư's business decision (a proposal, not forced) | 5 |
| Q5 | SEO: 410 or redirect? | 410 when retired; 301 when superseded (same `source_key`); the page returns on restore | 5 |
| Q6 | Re-uploading a deleted tour: restore automatically or ask? | Staging shows "deleted on <date>"; staff choose Restore (runs `restore` + `tour.reinstated`) or Create a new tour | 2 |
| Q7 | Channel for the tenant warning? | Persistent badge (the source of truth) + the portal bell reading the tenant's notifications. Email and webhook later, from the outbox | 5 |
| Q8 | Who may retire a published tour? | Staff with Master Content rights; the confirm dialog shows a dry run of affected tenants, posts and bookings | 2 |
| Q9 | `lifecycle_stage` (nothing writes it)? | Not a deletion signal. Kept for sales (`phasing_out`); T7 and TripPlanner switch to the served state | 1 |
| Q10 | Is a tenant that uses the tour only through Slate / planning (no T2) warned? | Yes: every tenant with any derivative (subject, angle request, piece, publish-log row) | 2 |
| Q11 | Between a supersede and the publish of the new version's Master, is the key served? (added by this ADR; today the tour drops out of the catalog in that gap) | `paused`, reason `superseded_pending`, no notification; consumers treat it as temporary (TripPlanner 404, not 410). Alternative: keep serving the old version until the new Master is published | 1, 2 |
