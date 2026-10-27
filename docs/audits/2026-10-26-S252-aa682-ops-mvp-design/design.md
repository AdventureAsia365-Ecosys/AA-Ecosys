# AA-682 — Operations MVP design (supplier bookings, trip checks, invoices + payment schedule, supplier bills, My Payments)

S252, 26/10/2026. Read-only design lane (Claude Code). Nothing applied, no issue changed. Linear AA-682 (Backlog, Low,
project "TripPlanner & AA-Booking", no relations). The issue already decides: **manual payment marking only** (no
online provider). Its 06/10 comment adds 4 rules (idempotency key on every money write, read-before-retry, no payment
credentials or payment actions in agent sessions / prompts / logs, invoice + payment states enforced in the DB).

## 0. Sources read and facts this design rests on

| Source | Fact used |
|---|---|
| AA-Booking `CONTEXT.md` (origin/main `5569f2b`) | Role `booking` = per-table grants, no DELETE on business tables, `audit_logs` append-only; migrations run as `bk_owner`; guard forbids SECURITY DEFINER, grants outside `booking`, role switches; column tags DM-6.1 in the creating file; "post-sale status edges" and "operations / money" explicitly wait for AA-682; customer e-mail out of scope (staff SES only); worker in-process, kinds `bk_*`, deploy gate counts every non-exempt queued/running job |
| `migrations/` on origin/main | Latest **bk-025** (`025_ops_data_coverage_views.sql`); scan of every Booking and AA-CIS-Infra branch: no `026+` file anywhere → **next free key bk-026** (re-check and hold the number with the Infra copy branch the day S1 starts, memo seam 9) |
| `db-schema-reference.md` (verified 25/10 14:58 UTC, Booking at bk-024) | `trip_cases.status` 13-value CHECK, `channel` b2c/b2b CHECK (b2b ⇒ `customer_id` NULL), edges table `trip_case_status_transitions` + trigger `trip_case_check_transition`, history via `booking.actor` / `booking.status_note`; `trip_case_versions` one approved per case, `total_price`, `currency`, `fx_rate_locked`; items `trip_case_version_itinerary` (`position`, `hotel_room_type_id` / `service_id`, no unit price); `version_item_costs` (`net_amount` conf:commercial); `b2b_hold_lines (hold_id, line_no, line_ref, held_as, status)`; `outbox` with closed `outbox_event_type_chk`; `settings` (SELECT only; `deposit_pct` = 30 seeded by bk-005); `media_files` (bk-001, customer photos); `entity_media` (supplier photos, SSE-S3 bucket). **No booking table has RLS** (0 of 53 objects) |
| Current case edges (bk-003 + bk-005) | `new_inquiry→discovery→building→proposal_sent`, back-steps, `→cancelled` from the four pre-sale states, `proposal_sent→confirmed` (approval), `confirmed→cancelled`, `cancelled→new_inquiry`. B2B confirm (`app/b2b/holds.py _open_case`) **inserts** the case directly at `confirmed` with an approved V1 whose item `position` = hold `line_no` |
| ERD v2 `booking.dbml` + README | `supplier_bookings`, `supplier_bills` + `supplier_bill_items`, `invoices` + `invoice_items`, `payment_schedule`, `payments` (evidence media), `trip_case_checks` (one boolean row per case); enums `supplier_booking_status`, `invoice_status`, `payment_status`, `payment_kind`, `bill_status` |
| PRD PDF §7–9 | Not readable here (no pdftotext / pypdf / poppler in WSL). Its content is carried by ERD v2 (decision 5 cites PRD §7–10) and the S236 module spec `09-payments.md` + `ui-spec.md` W3 (§6.4, §8 W3, Q21–Q24), which read the PRD-derived Figma. **Gap to close in S1:** open the PDF once on Windows and diff §7–9 against §2 below |
| `ui-spec.md` W3 + `09-payments.md` | Routes `/billing`, `/billing/invoices/[number]`, `/billing/payments/[ref]`, `/trip-checks`, case tabs Billing / Checks, supplier tabs Bookings / Bills; Q22 manual recording; Q23 no hard delete (cancel / void with reason); Q24 lines from the approved version + audited adjustments; tasks replace the boolean checks row; `bk_invoice_overdue`; Figma "Delete" = cancel/void |
| Commercial-core memo (AA-928, S247) | Seam 1: supplier bookings / checks / bills hang off version items for B2C **and** B2B cases. Seam 2: no new NOT NULL path through `customer_id`. Seam 3: customer-side cancellation fees reuse the AA-974 model later. Seam 4: AA-682's supplier-booking status drives `line.confirmed` / `line.declined`; desk and supplier booking are **one action**. Seam 5: invoices are B2C; name the bill-to party as a kind. Seam 8: AA-682 writes no CRM-facing event of its own. Seam 10: link to the B2B desk, do not duplicate it |
| `booking.b2b.v1` 1.1 + CRM design final §5.3–5.4, O-10 | Agencies see AA lines only through the `/events` feed (`line.confirmed` / `line.declined` …) into `crm.booking_line`; "owed to suppliers" waits for AA-682 (O-10); vouchers to travellers are a CRM-side document, never Booking PII |
| `app/b2b/desk.py answer_line(conn, staff, hold_id, line_ref, accept, decline_code)` | Reusable inside a transaction; its UPDATE fires the bk-022 trigger that writes the outbox row |
| ADR 0004 O8, ADR 0006 (clients), AA-908 | Booking's customer surface = sign-in, My Trips, payments; **My Trips is built in TripPlanner** (`/trips`, BFF + Lambda, `traveller_accounts`, tp-019); Booking customer routes = EXTERNAL × {`booking-customer`, `tripplanner`}; Booking maps `(iss, sub)` → `customer_identities` (bk-024) |
| ADR 0005 d4–d5, d10 | Invoices and payments use the quote currency; FX locked at send; tax via a `tax_rules` table, never hard-coded; B2C prices shown tax-inclusive; rates still with the accountant |
| Data standards DM-6.1 / 6.7 / 6.8, DM-7.1–7.5 | Classes incl. `payment` (references only, never card numbers) and `emergency_contact`; erasure runbook scope; no traveller name of a B2B (CRM) trip in `booking.*`; every new table gets a retention row in a **root PR merged before the Infra copy**; accounting exception exists for CRM money rows |
| Lessons log | Code needing a new migration merges only after the apply (S249); a CHECK value must exist before its writer (AA-847); binary bodies through API Gateway REST break → base64 JSON (S229); two lanes changing one role's grants (S243); strict branch protection → merge serially |

## 1. Scope and decisions taken in this design (proposed; §11 lists what Nghiệp / Ms. Thư confirm)

| # | Decision | Why |
|---|---|---|
| D1 | Case status stays the **13 DB values**; no new value. "Confirmed & Booked" = a **derived supply badge** (`booked`: ≥ 1 live supplier booking and all confirmed) shown next to the status | The 13-value CHECK lives in 4 objects + `v_ops_*` views + `ops.overview.v1`; a new value buys nothing a badge cannot show |
| D2 | Case status is **auto-advanced forward** from facts (supply track, money track, dates) by one service function, through DB-checked edges; staff never pick post-sale statuses by hand except cancel | One writer; matches the B2B confirm path (system actor) |
| D3 | Supply and money may happen in either order (deposit-first or book-first): status = furthest milestone reached; the case header shows both tracks | AA's real order is a Ms. Thư question; the model works for both |
| D4 | One generic transitions table `booking.ops_transitions(entity, from, to)` + one trigger function (arg = entity) for supplier bookings, invoices, supplier bills | Issue comment: states enforced in the DB, same pattern as the case machine; one function to review |
| D5 | Invoice money states (`sent`, `partially_paid`, `paid`) **cannot be written** unless they equal what the verified payments imply (BEFORE UPDATE guard recomputes) | "Never mark paid without recorded money": the app cannot bypass it |
| D6 | Payment = **record (maker) → verify (checker, another person)**; only verified, non-voided payments count; evidence file required to verify (except `cash`); every money write takes an `Idempotency-Key` (unique per invoice) | Manual marking is the only control; two people + evidence replace the provider reference |
| D7 | MVP invoice is a **proforma / payment request** (`document_type = 'proforma'`), prices tax-inclusive, no tax lines. The legal VAT e-invoice stays outside Booking until the accountant decides | ADR 0005 d10: tax rates not confirmed; a VN legal e-invoice goes through a licensed provider |
| D8 | Invoice lines: one `version_total` line from the approved version (locked) + `adjustment` lines with a reason (Q24 recommended). One live invoice per case. After send, adjustments are append-only and change the total (amendment rule, §3.3 — critic) | Version items carry no selling price; the version total is the sold price |
| D9 | Schedule rows hold `kind`, `amount`, `due_date` only; their paid / due / overdue state is **derived** (waterfall of verified payments, oldest due first) in a view, not stored | No stored status to drift; no allocation table |
| D10 | Files (payment evidence, vouchers, supplier confirmations, bills, payout evidence) in a **new private bucket with a KMS CMK**; upload = base64 JSON through the BFF (the AA-835 path), ≤ 10 MB DB cap, ~3 MB effective through Vercel | Proven path; avoids the API Gateway binary bug; KMS because evidence is `pii:payment` |
| D11 | **No RLS** on the new tables (consistent with all 53 Booking objects): isolation = schema + role `booking` + per-table / per-column grants + triggers; customer scoping is in SQL by `customer_id` and tested | Booking is single-tenant; FORCE RLS would only guard role `booking` from itself |
| D12 | B2B cases: supplier bookings, checks and supplier bills apply; **no customer invoice** (agency settlement is O-10, later); **no voucher file upload and no emergency contact** on B2B cases (DM-6.8: no traveller data in `booking.*`) | Seams 1, 5; DM-6.8 |
| D13 | B2B tie-in: confirming / declining a supplier booking whose item is an **on-request** hold line calls `desk.answer_line()` in the same transaction → existing trigger emits `line.confirmed` / `line.declined`. No new event type, `booking.b2b.v1` unchanged. **Critic — both directions, one action (seam 4):** a desk answer (`POST` on the B2B desk) of a line that has a live supplier booking moves that booking too (accept → `confirmed` needs a `confirmation_ref`, so the desk answer is refused with 409 `answer_from_suppliers_tab` and links there); plan (departure) lines have no supplier and keep being answered on the desk only. A desk line is answered once (`line_answered` 409), so a B2B-linked supplier booking that is `confirmed` cannot be re-requested or cancelled by staff (409 `b2b_line_answered`; only the agency cancel moves it); a `declined` one is final (no replacement — the agency was told `line.declined`) | Seams 4, 8, 10 |
| D14 | My Payments lives in **TripPlanner My Trips** (`/trips`), fed by new Booking customer routes over a new HTTP contract `booking.customer.v1`; read-only (no pay button, no upload) | O8 + AA-908 put My Trips in TripPlanner; no second customer app to build |
| D15 | Customer reminders = customer `notifications` rows (My Trips feed) only; staff get bell notifications; no customer e-mail (Q21 still open) | CONTEXT: customer e-mail out of scope; copy never claims an e-mail |
| D16 | No new staff role in the MVP; permissions on existing roles (§5). A `booking-finance` group is additive later | Q5; a Cognito group + CIS Staff UI change is not needed to ship |

## 2. Slices (each ~1 PR group: migration PR → Infra copy → DB Migrate apply → code PR(s) → FE PR)

| Slice | Scope | Migration | Depends on | Done when |
|---|---|---|---|---|
| **S0** Docs + numbers (½ session, with S1) | `docs/implementation-notes/AA-682.md`; root PR: DM-7 retention rows for every S1–S4 table (DM-7.1, merged before any Infra copy); hold `bk-026` with the Infra copy branch; read PRD §7–9 once and log any delta | — | — | Root PR merged; implementation notes list D1–D16; PRD delta recorded |
| **S1** Supplier bookings + supply track | `ops_transitions`, post-sale case edges + guard, `ops_files` (+ Infra bucket / CMK / IAM / env), `supplier_bookings`, settings rows, `v_trip_case_supply_state`; generate from approved version, request / confirm / decline / cancel / re-request, voucher + confirmation upload, B2B desk tie-in, case auto-advance `confirmed → supplier_confirming`; staff UI case **Suppliers** tab, supplier **Bookings** tab, header supply badge, dashboard tile | **bk-026** | Infra PR (bucket + CMK + task-role policy) applied before the code deploy | Dev: an approved B2C case generates N bookings, confirm all → badge "Confirmed & Booked", case `supplier_confirming`; illegal edge → 409 from the DB; B2B on-request line confirmed from the Suppliers tab → `line.confirmed` row in `booking.outbox` + visible in `GET /booking/b2b/v1/events`; voucher upload/download (presigned 300 s) audited; `/booking/health/ready` lists bk-026; UI shots 1440/390 light/dark |
| **S2** Trip checks + case lifecycle | `trip_case_checks` + seeding trigger (on entering `confirmed`), derived checks (suppliers confirmed, payment verified) in `v_trip_check_board`; `bk_case_lifecycle` + `bk_ops_reminders` (supplier-answer + check-due parts); staff UI `/trip-checks` (shipped) + case **Checks** tab | **bk-027** | S1 | Every confirmed case (B2C and B2B, incl. existing ones by backfill) has its check rows; B2B emergency-contact write refused by the DB; `bk_case_lifecycle` DRY RUN on Dev lists the moves it would make, then live moves a synthetic case `pre_departure → on_trip → completed` |
| **S3** Invoices + schedule + manual payments | `invoices`, `invoice_items`, `payment_schedule`, `payments`, settle + guard triggers, `v_invoice_balance`, `v_payment_schedule_status`, reminder dedupe index; create (from approved version) / edit draft / send / cancel / remind; record / verify / void / refund; `bk_ops_reminders` payment part; case money track auto-advance; staff UI `/billing` (Invoices / Payments tabs + KPIs), invoice + payment detail, Create Invoice stepper, Record / Verify / Void dialogs, case **Billing** tab | **bk-028** | S1 (files), S2 (`payment_verified` check) | Dev synthetic B2C case: invoice 30/70 sent → case `invoice_sent`; deposit recorded by A, verify by A → 403 `maker_checker`, by B → case `payment_pending`; balance → `paid`; void → back to `payment_pending`; same Idempotency-Key twice → one payment; direct `UPDATE invoices SET status='paid'` as `booking` → error; overdue reminder created once per key |
| **S4** Supplier bills + payouts | `supplier_bills`, `supplier_bill_items`, `supplier_payouts`, settle trigger; enter bill (from confirmed supplier bookings), approve (≠ maker), record payout (Idempotency-Key, evidence), void; bill-due reminders; staff UI supplier **Bills** tab, `/billing?tab=supplier-bills`, bill drawer; case cost vs billed variance panel | **bk-029** | S1 | Bill matched to 2 bookings, approve by maker → 403, by other → `approved`; payout = amount → `paid`; void → `approved`; variance net vs billed shown with `pricing.read` only |
| **S5** My Payments (customer) | Booking customer routes `/booking/customer/v1/*` (EXTERNAL verifier, `(iss, sub)` → customer); root contract `booking.customer.v1.openapi.yaml` + samples + field policy; TripPlanner BFF route + `/trips` "Payments" section | none (reads S3 tables) | S3; TripPlanner lane (1 TP PR) | Signed-in traveller sees only own invoices (other customer's number → 404), schedule chips, verified payments, payment instructions; no staff name, evidence, net or supplier field in any response (contract CI); Playwright 1440/390 on TP live |

**Who performs the live writes (critic).** The agent's only staff session on Dev is the AA-910 E2E admin, which is
read-only by design (and preview sessions are too), and the AA-682 comment forbids payment actions in agent sessions.
So: S1/S2 live writes (generate, confirm, B2B line confirm, checks) run as a DB Migrate `run-script` that calls the
service functions on a synthetic case with a script actor (the AA-947 setup pattern, audit `script:aa682_*`), DRY RUN
first. S3/S4 money flows (record by A, verify by B, void, refund, payout) are proven by the CI integration tests on
PostgreSQL (real triggers, two staff rows) — **not** by an agent on Dev; the Dev walkthrough of record → verify → void
is a human step (Nghiệp + a second admin, synthetic case) recorded in the AA-855 UAT videos, after which the agent
checks only reads (GET shapes, balances, screenshots). The S3 Done-when items "recorded by A, verify by A → 403, by
B …" and "direct UPDATE as `booking` → error" are therefore CI evidence plus a read-only live check.

Delivery fits plan.json L4: Part 1 = S0+S1+S2, Part 2 = S3, Part 3 = S4+S5. S1/S2 need no money decision and can start now; S3 ships with the §11 defaults as **settings rows** (Ms. Thư's answers change values, not code).

## 3. Data model

Common to every new table: owned by `bk_owner`; `uuid` PK `gen_random_uuid()`; `created_at` / `updated_at` + `set_updated_at` trigger; staff columns are staff keys (`text`, FK `staff_users(cis_user_id)`); human codes from a sequence with a CHECK on the format; no DELETE grant; tags in the same file; `REQUIRED_SCHEMA_VERSIONS += bk-0NN` only in the code PR after the apply.

### 3.1 bk-026 (S1)

| Object | Columns / rules | Grants (role `booking`) | Tags |
|---|---|---|---|
| `ops_transitions` | `entity` CHECK (`supplier_booking`,`invoice`,`supplier_bill`), `from_status`, `to_status`, PK (entity, from, to), CHECK from ≠ to. Function `ops_check_transition()` (TG_ARGV[0] = entity, not SECURITY DEFINER, `search_path = pg_catalog`) raises `check_violation` on an edge not listed. bk-026 seeds the supplier-booking edges; bk-028 / bk-029 add theirs | SELECT | — |
| `trip_case_status_transitions` rows | **bk-026 (critic: money edges moved to bk-028):** `confirmed→supplier_confirming`, `supplier_confirming→confirmed` (every live booking cancelled); travel: `confirmed→pre_departure`, `supplier_confirming→pre_departure` (B2B only, guard), `pre_departure→on_trip`, `on_trip→completed`; cancel from `supplier_confirming`, `pre_departure`. **bk-028 adds** `confirmed→invoice_sent`, `supplier_confirming→invoice_sent`, `invoice_sent→payment_pending`, `invoice_sent→paid`, `payment_pending→paid`, back-steps `payment_pending→invoice_sent`, `paid→payment_pending`, `paid→invoice_sent`, `invoice_sent→confirmed`, `invoice_sent→supplier_confirming`, `paid→pre_departure`, and cancel from `invoice_sent`, `payment_pending`, `paid` (not from `on_trip` / `completed`) | (SELECT, unchanged) | — |
| trigger `trip_cases_post_sale_guard` (BEFORE UPDATE OF status) | **Fact guard (critic):** the existing staff route `POST /trip-cases/{ref}/status` (`service.change_status`) walks any edge in the table, so an edge alone is no control. The guard checks the fact behind each post-sale target: `supplier_confirming` needs ≥ 1 live supplier booking; `pre_departure` needs supply state `booked` or `none` and, for B2C, the live invoice `paid`; `on_trip` needs `start_date ≤ current_date`; `completed` needs `end_date < current_date`; B2B may not enter `invoice_sent`/`payment_pending`/`paid`. bk-028 replaces the function (CREATE OR REPLACE) to add: `invoice_sent`/`payment_pending`/`paid` must equal what the live invoice implies (same rule as `invoice_money_guard`). App side (S1): `change_status` refuses every post-sale target except `cancelled` with 409 `status_system_managed` (extend `APPROVAL_ONLY_STATUSES` to a `SYSTEM_STATUSES` set); only `advance_case` / `bk_case_lifecycle` move them | — | — |
| case cancel + reopen (critic) | Staff cancel of a post-sale case: pending supplier bookings → `cancelled` in the same transaction; `requested` / `confirmed` ones stay and raise one staff notification "cancel with supplier" (cancelling with a supplier is a real-world act with fees); a draft invoice is soft-deleted; a sent invoice stays until refunds bring net paid to 0, then staff cancel it. **Reopen** (`cancelled → new_inquiry`, bk-005 edge) is refused by the guard while the case has any live supplier booking, a non-cancelled invoice or a non-voided payment | — | — |
| B2B agency cancel (critic, S1 code) | `app/b2b/cancellation.py` refuses unless `trip_cases.status = 'confirmed'` (line ~314). Once S1 auto-advances a B2B case to `supplier_confirming` / `pre_departure`, `POST /bookings/{id}/cancel` of `booking.b2b.v1` would answer `invalid` and break the contract. S1 widens that check to `status IN ('confirmed','supplier_confirming','pre_departure')`, cancels pending supplier bookings and notifies staff for requested / confirmed ones in the same transaction, and keeps the audit `before.status` as the real status; integration test replays an agency cancel on a `supplier_confirming` case | — | — |
| `ops_files` | `kind` CHECK (`payment_evidence`,`supplier_voucher`,`supplier_confirmation`,`supplier_bill`,`payout_evidence`); `entity_type` CHECK (`payment`,`supplier_booking`,`supplier_bill`,`supplier_payout`), `entity_id` (no FK, typed check in service); `trip_case_id` FK NULL; `s3_bucket` CHECK `^aa-booking-[a-z0-9]+-ops-docs-[0-9]{12}$`; `s3_key` CHECK = `ops-docs/<kind>/<id>.<ext>` (derived, as `entity_media`); `content_type` CHECK pdf/jpeg/png/webp; `bytes` 1–10,485,760; `sha256` `^[0-9a-f]{64}$`; `file_name` 1–200; `status` `active`/`removed` (final); `removed_reason`, `uploaded_by`, `removed_by`, timestamps; UNIQUE (entity_type, entity_id, sha256) WHERE active | SELECT, INSERT; UPDATE (status, removed_reason, removed_by, updated_at); guard trigger: removed is final | `s3_key` `pii:payment (also pii:name); object may hold bank refs and names`; `file_name` `pii:free_text` |
| `supplier_bookings` | `code` `SB-000123`; `trip_case_id` FK; `version_item_id` FK NULL (UNIQUE WHERE status IN ('pending','requested','confirmed') — critic: `declined` must not block a replacement booking with another supplier; "live" = pending / requested / confirmed everywhere, incl. `v_trip_case_supply_state`); `supplier_id` FK NOT NULL; `hotel_room_type_id` / `service_id` (≤ 1, as items); `item_description` 1–500; `service_date`, `nights` 0–60; `pax` 1–120 (counts only); `net_amount` numeric(16,2) ≥ 0, `net_currency` `^[A-Z]{3}$` (copied from `version_item_costs`, editable until confirmed); `status` CHECK (`pending`,`requested`,`confirmed`,`declined`,`cancelled`); `requested_at/by`, `confirmed_at/by`, `confirmation_ref` 1–100; `decline_code` (same 4 codes as the desk) ⇔ declined; `cancel_reason` ⇔ cancelled; `voucher_file_id` FK `ops_files`; `b2b_hold_id` + `b2b_line_ref` (both or neither); `notes`. CHECKs: confirmed ⇒ `confirmation_ref` and `confirmed_at`. Trigger `ops_check_transition('supplier_booking')`; trigger refusing `voucher_file_id` on a `b2b` case | SELECT, INSERT, UPDATE | `net_amount`, `notes` `conf:commercial`; `confirmation_ref` none |
| supplier-booking edges | `pending→requested`, `pending→cancelled`, `requested→confirmed`, `requested→declined`, `requested→cancelled`, `confirmed→requested` (change, reason in audit), `confirmed→cancelled` | — | — |
| `v_trip_case_supply_state` | per case: live / confirmed / pending counts, `state` `none`/`confirming`/`booked`. Critic: `none` (no supply item, e.g. a B2B case of only fixed-departure plan lines, which carry no supplier) passes the `pre_departure` gate like `booked`, else such cases never leave `confirmed` | SELECT (read-only view) | — |
| `settings` rows | `supplier_answer_days` 2, `pre_departure_days` 14, `ops_docs_max_bytes` 10485760 | (SELECT) | — |

### 3.2 bk-027 (S2)

| Object | Columns / rules | Grants | Tags |
|---|---|---|---|
| `trip_case_checks` | `trip_case_id` FK; `code` CHECK (`pre_trip_recheck`,`emergency_contact`,`insurance`,`custom`); `title` 1–200 (required for custom); `status` `open`/`done`/`not_applicable`; `due_date`; `assignee_ref` FK staff; `done_by/at` (done ⇔ done_at); `note`; `emergency_contact_name`, `emergency_contact_phone` (only on `emergency_contact`, CHECK); UNIQUE (trip_case_id, code) WHERE code <> 'custom'. Trigger: a `b2b` case keeps `emergency_contact` `not_applicable` with null fields | SELECT, INSERT, UPDATE | `note` `pii:free_text`; `emergency_contact_name` `pii:emergency_contact (also pii:name)`; `emergency_contact_phone` `pii:emergency_contact (also pii:contact)` |
| trigger `trip_cases_seed_checks` (AFTER INSERT OR UPDATE OF status, status = `confirmed`) | inserts the 3 standard rows `ON CONFLICT DO NOTHING` (due = start_date − `pre_departure_days`); covers B2C approval and the B2B insert-at-confirmed without touching `holds.py`; one backfill statement for cases already ≥ `confirmed` | — | — |
| `v_trip_check_board` | stored checks + derived `suppliers_confirmed` (from 3.1 view) + `payment_verified` (from S3, NULL until bk-028) | SELECT | — |

### 3.3 bk-028 (S3)

| Object | Columns / rules | Grants | Tags |
|---|---|---|---|
| `invoices` | `invoice_number` `INV-000123`; `trip_case_id` FK; `version_id` FK (must be the approved version, trigger); `bill_to_kind` CHECK (`customer`) (+ `b2b_partner` later, seam 5); `customer_id` FK, CHECK bill_to_kind = customer ⇒ NOT NULL (no table-level NOT NULL); snapshot at send `bill_to_name`, `bill_to_email`, `bill_to_address`; `document_type` CHECK (`proforma`); `currency` = version currency (trigger); `total_amount` numeric(14,2) ≥ 0; `status` (`draft`,`sent`,`partially_paid`,`paid`,`cancelled`); `issued_at`, `sent_by`, `notes`, `terms`; `cancelled_at/by`, `cancel_reason` ⇔ cancelled; `idempotency_key` UNIQUE + `request_sha256` (critic, as payments); `deleted_at` (draft only, CHECK); UNIQUE live invoice per case (status ≠ cancelled, deleted_at NULL). Triggers: `ops_check_transition('invoice')`; `invoice_money_guard` (status in sent/partially_paid/paid must equal the computed state; send requires Σ items = total = Σ schedule, and a non-NULL version `total_price` + `currency`); sent ⇒ bill-to snapshot immutable; `total_amount` changes after send **only** through an amendment (critic, below) |
| invoice amendment (critic) | The original "change after send = cancel + reissue" cannot work once money is in: cancel needs net verified paid = 0, so a trip changed after the deposit (extra night, fewer pax, bank fee shortfall) would need a refund of the deposit first. Rule: on a `sent` / `partially_paid` / `paid` invoice, staff (billing.write) may **append** `adjustment` items (never edit or delete an item after send) with a reason; a trigger recomputes `total_amount` = Σ items; schedule rows not yet covered by the waterfall may be edited / added so that Σ schedule = new total (checked at commit by a deferred constraint trigger); the settle logic recomputes the state (a paid invoice can drop to `partially_paid`). One audit row with before / after total; customer notification "Your payment request was updated". Covered by S3 tests | — | — | SELECT, INSERT; UPDATE (status, issued_at, sent_by, bill_to_*, notes, terms, cancelled_*, cancel_reason, deleted_at, updated_*) | `bill_to_name` `pii:name`; `bill_to_email` `pii:contact`; `bill_to_address` `pii:address`; `notes`, `terms` `pii:free_text` |
| invoice edges | `draft→sent`, `sent→partially_paid`, `sent→paid`, `partially_paid→paid`, `partially_paid→sent`, `paid→partially_paid`, `paid→sent`, `sent→cancelled`, `partially_paid→cancelled` + guard: cancel only when net verified paid = 0 (refund first) | — | — |
| `invoice_items` | `invoice_id` FK; `position`; `kind` (`version_total`,`adjustment`); `description` 1–500; `quantity` > 0; `unit_price` (may be negative for adjustments); `amount` = round(qty × unit, 2) CHECK; `reason` ⇔ adjustment. Lock trigger: UPDATE / DELETE only while the invoice is `draft`; after send only INSERT of `adjustment` rows (critic, amendment rule) | SELECT, INSERT, UPDATE, DELETE (draft only, trigger) | `description`, `reason` `pii:free_text` |
| `payment_schedule` | `invoice_id` FK; `seq` 1–10 UNIQUE per invoice; `kind` (`deposit`,`second`,`final`,`other`); `amount` > 0; `due_date`. Lock: free while draft; after send a row already covered (fully or partly) by verified payments is frozen, the others may change under the amendment rule (critic) | SELECT, INSERT, UPDATE, DELETE (draft only) | — |
| `payments` | `ref` `PMT-000123`; `invoice_id` FK; `kind` (`receipt`,`refund`); `amount` numeric(14,2) > 0; (critic) insert refused unless the invoice is `sent`/`partially_paid`/`paid` (never draft / cancelled); verifying a refund refused when it would take net verified paid below 0; a receipt that takes net verified paid above the total is allowed (real overpayment) but the invoice reads `paid` with a negative balance and a staff notification "overpaid, refund or adjust"; `request_sha256` (hash of the canonical request body) NOT NULL so a replayed Idempotency-Key can be compared (same hash → stored row 200; other hash → 409 `idempotency_conflict`); `currency` = invoice currency (trigger); `method` (`bank_transfer`,`card_offline`,`cash`,`other`); `received_at`; `reference` 1–100; `note`; `evidence_file_id` FK `ops_files`; `idempotency_key` 8–200, UNIQUE (invoice_id, key); `recorded_by`, `recorded_at`; `verified_by/at` (CHECK verified_by ≠ recorded_by; verify needs evidence unless `cash`); `voided_at/by`, `void_reason` (void ⇔ reason; final). Guard: reference / note editable only before verify; amount / kind / invoice never | SELECT, INSERT; UPDATE (reference, note, evidence_file_id, verified_by, verified_at, voided_at, voided_by, void_reason, updated_*) | `reference` `pii:payment; bank or receipt reference, never a card number`; `note` `pii:free_text` |
| trigger `payments_settle` (AFTER INSERT / UPDATE) | **first** `SELECT … FROM booking.invoices WHERE id = NEW.invoice_id FOR UPDATE` (critic: without the lock two concurrent verifies on one invoice each sum without the other's row under READ COMMITTED and both write `partially_paid` for a fully paid invoice; after the lock the next statement takes a new snapshot), then recomputes the invoice state from verified, non-voided receipts − refunds and writes it (passes the guard); the service also locks the invoice row at the start of record / verify / void; then the service advances the case. Same lock-first rule for `supplier_payouts` → `supplier_bills` | — | — |
| `v_invoice_balance` | total, verified paid, unverified, refunded, balance, next due, overdue amount | SELECT | — |
| `v_payment_schedule_status` | per row: `scheduled` / `due` (≤ 7 days) / `paid` / `overdue` by waterfall | SELECT | — |
| `notifications_reminder_uq` | UNIQUE (recipient_type, type, entity_id, (data->>'reminder_key')) WHERE data ? 'reminder_key' (critic: `recipient_type` added, else the staff row and the customer row of one reminder collide); `notify_staff` / `notify_customer` get an `ON CONFLICT DO NOTHING` variant for reminders so a duplicate never aborts the job transaction | (unchanged) | — |
| `settings` rows | `deposit_due_days` 3, `balance_due_days_before_start` 30, `payment_due_soon_days` 7, `invoice_issuer` (legal name + address, placeholder), `payment_instructions` (bank details text, placeholder; Ms. Thư). Critic: the migration seeds **placeholders only** — AA-Booking is a public repo, so the real bank details and legal address are set by a DB Migrate `run-script` (role `booking` has SELECT only on `settings`), never in a migration file; every later value change (deposit %, due days) is likewise a migration or run-script, not a UI edit | (SELECT) | — |

### 3.4 bk-029 (S4)

| Object | Columns / rules | Grants | Tags |
|---|---|---|---|
| `supplier_bills` | `code` `BIL-000123`; `supplier_id` FK; `trip_case_id` FK NULL; `bill_number` (supplier's) UNIQUE per supplier WHERE not cancelled; `currency`; `amount` > 0; `issue_date`, `due_date` ≥ issue; `document_file_id` FK; `status` (`received`,`approved`,`paid`,`cancelled`); `created_by`; `approved_by/at` (≠ `created_by`, CHECK); `cancel_reason` ⇔ cancelled; `notes`. Edges: `received→approved`, `received→cancelled`, `approved→paid`, `approved→cancelled` (no live payout), `paid→approved` (payout void). Paid ⇔ Σ live payouts = amount (guard) | SELECT, INSERT, UPDATE | `amount`, `notes`, `bill_number` `conf:commercial` |
| `supplier_bill_items` | PK (bill_id, supplier_booking_id); `amount` (bill currency); booking must be `confirmed`, same supplier; locked once approved | SELECT, INSERT, DELETE (received only) | `amount` `conf:commercial` |
| `supplier_payouts` | `code` `SPO-000123`; `bill_id` FK; `amount` > 0; `currency` = bill; `paid_at`; `method`; `reference`; `evidence_file_id`; `idempotency_key` UNIQUE per bill; `recorded_by`; `voided_*` + reason. Settle trigger as payments | SELECT, INSERT; UPDATE (void columns) | `reference`, `amount` `conf:commercial` |

### 3.5 Retention and PII (root DM-7 rows, S0)

| Table(s) | Proposed window | Archive | Erasure (DM-6.7) |
|---|---|---|---|
| `invoices`, `invoice_items`, `payment_schedule`, `payments`, `supplier_bills`, `supplier_bill_items`, `supplier_payouts`, `ops_files` of kinds payment_evidence / supplier_bill / payout_evidence (+ S3 objects) | **Accounting exception:** statutory period of the selling entity (proposed 10 years after the fiscal year, VN Law on Accounting 2015; accountant confirms), kept through an erasure request; receipt says so | No (rows kept) | Free text (`notes`, `terms`, `note`) redacted; `bill_to_*` kept (accounting) |
| `supplier_bookings`, `ops_files` voucher / confirmation | Kept with the case; window set before prod (like `trip_case_status_history`) | — | `notes` redacted (no PII by design) |
| `trip_case_checks` | Emergency contact fields nulled at trip end + 90 days (`bk_case_lifecycle`); rows kept with the case | — | Emergency contact + note nulled |
| `ops_files` `removed` | Object + row deleted 30 days after removal (only kinds outside the accounting exception) | — | — |
| `ops_transitions` | Reference data, kept | — | — |

## 4. State machines

| Machine | States | Driven by | DB enforcement |
|---|---|---|---|
| Supplier booking | `pending → requested → confirmed`; `requested → declined`; `pending/requested/confirmed → cancelled`; `confirmed → requested` (change) | Staff (ops.write); B2B on-request lines also call `desk.answer_line` (accept on confirm, decline code on decline) in the same transaction | `ops_transitions` + CHECKs (ref on confirm, code on decline, reason on cancel) |
| Supply track (derived) | `none` → `confirming` (any live booking not confirmed) → `booked` = **"Confirmed & Booked"** | View | — |
| Trip case — staff moves (critic) | Staff may only **cancel** a post-sale case (with reason; cascade + reopen rule in §3.1); every other post-sale status is `SYSTEM_STATUSES` in `change_status` (409 `status_system_managed`) and fact-checked by `trip_cases_post_sale_guard` | `service.change_status` | guard |
| Trip case (post-sale, B2C) | `confirmed` → `supplier_confirming` (first request) → `invoice_sent` (invoice sent) → `payment_pending` (first verified receipt < total) → `paid` (balance 0) → `pre_departure` (job: paid + booked + start − 14 d) → `on_trip` (start date) → `completed` (end date + 1). Forward-only auto; back-steps only on payment void / invoice cancel; cancel by staff with a reason | `advance_case(conn, case_id)` called after every S1/S3 write; `bk_case_lifecycle` for dates | Edges table + `trip_cases_post_sale_guard` |
| Trip case (B2B) | `confirmed` → `supplier_confirming` → `pre_departure` (booked + start − 14 d) → `on_trip` → `completed`; never a money status | same | guard refuses money states for `b2b` |
| Invoice | `draft → sent → partially_paid ⇄ paid`; `sent/partially_paid → cancelled` (net paid 0); draft soft-deleted | Staff send / cancel; money states only by `payments_settle` | edges + `invoice_money_guard` (status must equal computed) |
| Schedule row (derived) | `scheduled` → `due` (≤ 7 d) → `overdue`; `paid` by waterfall | View | — |
| Payment | `recorded → verified`; any → `voided` (final); refund = a `refund` payment, same steps | Staff (maker) / admin (checker ≠ maker) | CHECKs + column grants + guard |
| Supplier bill | `received → approved → paid`; `received/approved → cancelled`; `paid → approved` on payout void | Staff (maker / checker); `paid` only by settle trigger | edges + guard |
| Trip check | `open → done` / `not_applicable`; `done → open` (reopen) | Staff; seeded on `confirmed` | CHECKs, B2B trigger |

## 5. API routes (all under `/booking`; staff = WORKFORCE token, preview / E2E sessions stay read-only by the existing global rule)

New permissions in `app/auth/staff.py`: `ops.read` = admin, sales, contracting; `ops.write` = admin, sales, contracting; `billing.read` = admin, sales; `billing.write` = admin, sales; `payment.verify` = admin (and ≠ recorder, 403 `maker_checker`); `bill.read` = admin, sales, contracting; `bill.write` = admin, contracting; `bill.approve` = admin, contracting (≠ creator); `payout.write` = admin (≠ bill creator). Reads join into `PREVIEW_PERMISSIONS`. Net amounts appear only with `pricing.read`. Every write: one `audit_logs` row; every money write requires `Idempotency-Key` (same key + same body → the stored row, 200; same key + other body → 409 `idempotency_conflict`).

| Method + path | Perm | Slice | Notes |
|---|---|---|---|
| `GET /trip-cases/{ref}/supplier-bookings` | ops.read | S1 | + supply state |
| `POST /trip-cases/{ref}/supplier-bookings/generate` | ops.write | S1 | idempotent: one per approved item that books supply; 409 `no_approved_version` |
| `POST /trip-cases/{ref}/supplier-bookings` | ops.write | S1 | extra / free-text item, supplier required |
| `PATCH /supplier-bookings/{id}` | ops.write | S1 | pending/requested only |
| `POST /supplier-bookings/{id}/request` · `/confirm {confirmation_ref, voucher_file_id?}` · `/decline {decline_code}` · `/cancel {reason}` · `/rerequest {reason}` | ops.write (+ `b2b_desk.write` on a B2B on-request line) | S1 | DB edge refusal → 409 `illegal_transition` |
| `GET /supplier-bookings?supplier_id=&status=&from=&to=` | ops.read | S1 | supplier Bookings tab, dashboard tile |
| `POST /ops-files` `{kind, entity_type, entity_id, file_name, content_type, data_base64}` | ops.write / billing.write / bill.write by kind | S1 | type + size read from bytes; 503 `ops_storage_unavailable` when bucket unset; 422 for a voucher on a B2B case |
| `GET /ops-files/{id}/download` → `{url, expires_in: 300}` | read perm of the parent | S1 | audited `ops_file.downloaded` |
| `POST /ops-files/{id}/remove {reason}` | write perm of the parent | S1 | not for files under a verified payment / paid bill |
| `GET /trip-checks?status=&due_before=&assignee=` · `GET /trip-cases/{ref}/checks` · `POST /trip-cases/{ref}/checks` (custom) · `PATCH /trip-checks/{id}` | ops.read / ops.write | S2 | emergency contact fields only for B2C |
| `GET /invoices?status=&overdue=&case=&q=&from=&to=` · `GET /invoices/{number}` | billing.read | S3 | + items, schedule (derived status), payments, balance |
| `POST /trip-cases/{ref}/invoices` `{adjustments[], schedule[]? , notes, terms, send_now}` | billing.write | S3 | default schedule from settings; 409 without approved version, for a B2B case, or with a live invoice |
| `PATCH /invoices/{number}` · `DELETE /invoices/{number}` (draft, soft) | billing.write | S3 | |
| `POST /invoices/{number}/send` · `/cancel {reason}` · `/remind` | billing.write | S3 | send snapshots bill-to, writes a customer notification row; remind = customer notification row (no e-mail) |
| `POST /invoices/{number}/payments` `{kind, amount, method, received_at, reference, note, evidence_file_id?}` | billing.write | S3 | Idempotency-Key required; 409 `duplicate_reference` warning when the same method + reference exists live (override flag) |
| `POST /payments/{ref}/verify` · `POST /payments/{ref}/void {reason}` · `PATCH /payments/{ref}` (reference / note before verify) | payment.verify / billing.write | S3 | verify: 422 `evidence_required` |
| `GET /payments?…` · `GET /payments/{ref}` · `GET /billing/summary` | billing.read | S3 | KPIs in USD at the approved FX row of the payment date |
| `GET/POST /supplier-bills` · `GET/PATCH /supplier-bills/{id}` · `POST …/approve` · `POST …/cancel` | bill.read / bill.write / bill.approve | S4 | |
| `POST /supplier-bills/{id}/payouts` · `POST /supplier-payouts/{id}/void` | payout.write | S4 | Idempotency-Key required |
| `GET /customer/v1/payments` · `GET /customer/v1/invoices/{number}` | EXTERNAL token × {`tripplanner`, `booking-customer`}; `(iss, sub)` → `customer_identities` | S5 | own B2C invoices with status ≠ draft only; 404 for any other; no staff name, evidence, net, supplier, internal note |

No route in any slice is reachable by an M2M token, and no agent tool calls them (issue comment: payment actions are never executed by an agent; the E2E and preview sessions are read-only before any DB access).

## 6. Staff admin UI (kit: `frontend/ui/` copies + `ui/booking/`)

| Page / part | Slice | Kit parts |
|---|---|---|
| Case header: supply badge ("Suppliers 3/5" / "Confirmed & Booked"), money badge (invoice state + balance) | S1, S3 | `StatusBadge` (new maps: supplier booking, supply state, invoice, payment, bill, check), `StatusStepper` (post-sale steps now live) |
| Case **Suppliers** tab (`/cases/[code]?tab=suppliers`): table per item, Generate, Request / Confirm drawer (ref + voucher upload) / Decline (code) / Cancel; B2B on-request rows link to the B2B desk entry | S1 | `DataTable`, `Drawer`, `ConfirmDialog`, upload component from AA-835 (re-encode images, PDF as is) |
| `/suppliers/[id]` **Bookings** tab (frame → real); dashboard tile "Supplier answers pending" | S1 | `DataTable`, KPI tile |
| `/trip-checks` (nav `shipped: true`) + case **Checks** tab + check drawer | S2 | `DataTable` filters, `Drawer`, `StaffPicker` |
| `/billing` Invoices / Payments tabs + 4 KPIs; `/billing/invoices/[number]`; `/billing/payments/[ref]`; Create Invoice `Stepper` (approved version → adjustments → schedule → review, Send now); Record Payment modal (+ evidence); Verify / Void / Cancel / Remind dialogs; case **Billing** tab | S3 | `Stepper`, `CustomerCombobox` not needed (case-bound), money input, `ConfirmDialog` with reason |
| `/billing?tab=supplier-bills` (admin, contracting) + `/suppliers/[id]` **Bills** tab + bill drawer + payout modal; case cost vs billed panel | S4 | same |

Copy rules: never "e-mail sent"; "Marked as paid" never appears without a verified payment; Figma "Delete" becomes Cancel / Void with a reason (Q23).

## 7. Customer page (S5, TripPlanner)

`/trips` gains a **Payments** section per trip (or `/trips/payments`): invoice number, total, paid, balance, next due date; schedule rows with chips (Scheduled / Due soon / Paid / Overdue); verified payments (date, amount, method); `payment_instructions` text; "Questions? Contact your trip consultant". Read-only, English by default, signed-in only (401 → sign-in prompt, as My Trips). TP BFF route forwards the traveller access token to `GET /booking/customer/v1/payments`; nothing stored in `tripplanner.*`.

## 8. Contracts and outbox events touched (versioned)

| Contract | Change | Version |
|---|---|---|
| `booking.b2b.v1` | **None.** `line.confirmed` / `line.declined` now also originate from a supplier-booking confirm / decline via `desk.answer_line` (same rows, same trigger, same semantics) | stays 1.1 |
| `booking.customer.v1` (new, `docs/contracts/booking.customer.v1.openapi.yaml`) | AA-Booking → TripPlanner, HTTP, EXTERNAL token; `Payments`, `Invoice`, `ScheduleRow`, `Payment`; samples (valid + rejected: staff name, evidence url, `net_*`, `supplier_*`); field policy in `contracts.yml`; README row | 1.0, S5 |
| `booking.outbox` / `outbox_event_type_chk` | **No change** in the MVP (no new stream, no CRM-facing AA-682 event, seam 8) | — |
| `ops.overview.v1` (bk-017 views) | None in the MVP; additive metrics `invoice_sent` / `paid` possible later (names append-only) | later minor |
| Planned `trip_case.status_changed.v1` | Not needed: My Payments reads over HTTP | — |
| Later (not MVP) | `booking.b2b.v1` 1.2 `line.voucher_ready` + agency invoices (CRM O-10) | later |

## 9. Jobs (`booking.job`, kinds listed in `kinds.py` with `EXPECTED_SECONDS`; not deploy-gate exempt; queued by a worker maintenance hook once per UTC day at ≥ 01:00 UTC, idempotency key `<kind>:<UTC date>`)

| Kind | Slice | What | Safety |
|---|---|---|---|
| `bk_case_lifecycle` | S2 | Date moves: (B2C paid / B2B any) + booked + start − `pre_departure_days` → `pre_departure`; start date → `on_trip`; end date + 1 → `completed`; a blocked gate (not paid / not booked / open checks) → one staff notification `trip_case.gate_blocked`; nulls emergency contacts at trip end + 90 d | Batches of 200, `FOR UPDATE SKIP LOCKED`, system actor + `status_note`; first run DRY RUN (counts in result), then live (DM-7.2 style for the nulling part) |
| `bk_ops_reminders` | S2 (supplier answers, checks), S3 (payments), S4 (bills) | Supplier bookings `requested` > `supplier_answer_days` → `supplier_booking.waiting`; checks due ≤ 3 d → `trip_check.due`; schedule rows due in 7 d → staff `payment.due_soon` + customer row; overdue day 1 / 7 → staff `invoice.overdue` + customer row; bills due ≤ 3 d → `supplier_bill.due` | Dedupe by `notifications_reminder_uq` (`reminder_key` = `<type>:<row id>:<step>`); no e-mail; no PII in the job payload or logs |

No job ever writes a payment, payout or money status (only staff routes do).

## 10. Tests per slice (5 required checks + Frontend Build; live verify per aa-ship)

| Slice | Migration / integration (Postgres 15, non-superuser replay) | Unit / API | FE / live |
|---|---|---|---|
| S1 | guard passes (bk_owner, BEGIN/COMMIT, registers bk-026, per-table grants); every illegal supplier-booking and case edge raises; B2B voucher refused; `booking` has no DELETE on new tables; tags present (`test_bk018_pii_tags` allowlist untouched) | generate idempotent; permission matrix incl. preview / E2E 403; B2B on-request confirm writes `line.confirmed` outbox row and is idempotent; upload sniffing (type, size, sha256), 503 without bucket; download audited | UI smoke Suppliers tab; Playwright shots 1440 / 390, light / dark (self-serve); live: ready lists bk-026, B2B event visible in `/events` |
| S2 | seeding trigger on insert-at-confirmed (B2B path) and on approval; B2B emergency contact refused; backfill count | lifecycle DRY RUN result shape; reminder dedupe | `/trip-checks` live data; job result on Dev |
| S3 | money guard: direct status write refused; settle trigger correctness (receipt, refund, void, partial); verify ≠ recorder CHECK; currency trigger; item / schedule lock after send; Σ checks at send | schedule builder (deposit %, short lead time → single payment); waterfall; Idempotency-Key replay / conflict; duplicate reference warning; case auto-advance and back-step on void; `billing.read` never leaks to contracting | Billing pages; full synthetic flow on Dev (§2 Done-when) with screenshots |
| S4 | bill guard (paid only by payouts), approve ≠ creator, items only confirmed bookings of the same supplier | payout idempotency, void → approved | Bills tab + payout flow on Dev |
| S5 | — | customer route: other customer's invoice 404, draft hidden, field allow-list test over every response; contract samples in root CI; token from WORKFORCE / M2M → 401 | TP Playwright 1440 / 390 on the live TP with a signed-in E2E traveller |

## 11. Open questions (proposed answer first)

| # | Question | Proposed answer | Who |
|---|---|---|---|
| Q1 | "Confirmed & Booked" — a new status? | No: derived supply badge (D1) | Nghiệp |
| Q2 | Book suppliers before or after the deposit? | Both allowed (D3); default AA practice as Ms. Thư says, only the UI hint changes | Ms. Thư (non-blocking) |
| Q3 | Tax on invoices | MVP proforma, prices tax-inclusive, no tax line (D7); `tax_rules` + legal e-invoice when the accountant answers | Ms. Thư / accountant |
| Q4 | Deposit % and due dates | Existing `deposit_pct` 30; deposit due issue + 3 d; balance due start − 30 d; lead time < 30 d → one payment; editable per invoice before send | Ms. Thư (setting values) |
| Q5 | Payment marking | Record by admin/sales, verify by a second person (admin), evidence required except cash (D6) | Ms. Thư |
| Q6 | Finance role? | Not in MVP; `booking-finance` later, additive (D16) | Nghiệp |
| Q7 | B2C cancellation fees / refunds | MVP: refund recorded manually with reason; fee policy = widen AA-974 `cancellation_policies.channel` to `b2c` later (seam 3) | Ms. Thư |
| Q8 | Customer e-mail for invoices / reminders | Not in MVP (D15); SES customer mail is its own decision (Q21) | Nghiệp |
| Q9 | Where is My Payments? | TripPlanner My Trips over `booking.customer.v1` (D14) | Nghiệp |
| Q10 | Upload path | base64 via BFF (≤ ~3 MB effective) now; presigned POST if real receipts exceed it | Nghiệp |
| Q11 | B2B vouchers | Confirmation ref only in Booking; vouchers to agencies later via `line.voucher_ready` (D12) | Nghiệp |
| Q12 | Agency invoices (CRM O-10) | Out; `bill_to_kind` keeps it additive | Nghiệp |
| Q13 | Store emergency contacts in Booking? | Yes for B2C, tagged, nulled at trip end + 90 d; never for B2B | Nghiệp |
| Q14 | Statutory period for money rows | 10 years (VN accounting documents), confirmed by the accountant before prod | Ms. Thư / accountant |
| Q15 | One live invoice per case enough? | Yes for MVP; changes after send = appended adjustment lines (amendment rule, §3.3; critic: cancel + reissue is impossible once a payment is verified); cancel + reissue only while nothing is paid | Ms. Thư |
| Q16 | ADR? | Root ADR **0016** (next free) "Booking operations money: manual marking, proforma, My Payments in TripPlanner" — two repos (Booking, TripPlanner) change if reversed | Nghiệp accepts |

## 12. Cost (AWS, Dev; no LLM)

| Item | $/month |
|---|---|
| S3 `aa-booking-dev-ops-docs-<acct>` (< 1 GB, versioning, few requests) | < $0.05 |
| KMS CMK `alias/aa-booking-dev-ops-docs` (+ S3 Bucket Key, so few KMS requests) | ~$1.00 |
| Compute (jobs run in the existing in-process worker; routes on the existing service) | $0 |
| CloudWatch (no new log group, no new alarm; job kinds use the existing `AA/Jobs/Booking` sampler) | $0 |
| SES (no customer mail) | $0 |
| **Total** | **≈ $1.05** (prod adds one more CMK ≈ $1) |

## 13. Risks

| Risk | Mitigation |
|---|---|
| Staff marks money that never arrived | Two-person verify + evidence + DB guard on money states + audit row per write |
| Double recording of one transfer (double click, retry) | Idempotency-Key unique per invoice; duplicate reference warning; read-before-retry in the FE (refetch on timeout) |
| Booking "invoice" mistaken for a legal VAT invoice | `document_type = proforma`, title "Payment request" on customer views, accountant gate before tax lines |
| Traveller PII of agency trips in `booking.*` / S3 (vouchers, emergency contacts) | DB triggers refuse voucher files and emergency contacts on B2B cases; upload copy warns on B2C |
| Evidence files leak (bank details, names) | Private bucket, Block Public Access, TLS only, SSE-KMS CMK, 300 s presigned GET for staff only, download audited, never exposed on customer routes |
| Auto-advance fights the existing approve / B2B confirm paths | One `advance_case` function; forward-only; edges table; integration test replays both entry paths |
| Two slices / lanes on one migration number or role grants | Hold bk-026 with the Infra copy branch at S1 start; list grant changes per role in each review (lesson S243) |
| Code deployed before its migration | Migration-only PR → Infra copy → DB Migrate apply → code PR (lesson S249) |
| Deploy blocked by daily jobs | Kinds run in seconds, daily; gate already handles; schedule at 01:00 UTC away from deploy windows |
| PRD §7–9 not re-read (PDF unreadable here) | S0 task: read it once on Windows and record deltas before S1 code |
| Booking API Gateway body limit for uploads | ~3 MB effective; PDFs above it → Q10 presigned POST |
