# AA-682 design — adversarial critic (S252)

Read-only review of `design.md` against `docs/architecture/db-schema-reference.md` (verified 25/10, Booking at bk-024),
AA-Booking origin/main `5569f2b` (`backend/app/trip_cases/service.py`, `backend/app/b2b/{desk,holds,cancellation}.py`,
`backend/app/auth/staff.py`, `backend/app/notifications/service.py`, `migrations/003,005`), `CONTEXT.md`, `ui-spec.md`,
the backlog and the S252 AA-950 runbook. Every fix applied to `design.md` is marked "critic" in the text. Nothing was
run on Dev, nothing pushed, no Linear change, nothing paid.

## Verified as correct

- Latest Booking migration on origin/main is bk-025; no branch has 026+; the parallel AA-950 lane adds no Booking
  migration (Booking change is code only) → bk-026..029 are free.
- The table and column facts in §0 match the dump: 13-value status CHECK in `trip_cases`, history and transitions;
  `channel` CHECK (b2b ⇒ `customer_id` NULL + `party_tenant_id`); `trip_case_versions` one approved per case,
  `total_price numeric(12,2)` + `currency` (both nullable); itinerary `hotel_room_type_id` / `service_id` (≤ 1), no
  price; `version_item_costs.net_amount numeric(16,2)`; `b2b_hold_lines` decline codes = the 4 used by the design;
  `outbox_event_type_chk` closed; `settings` SELECT only, `deposit_pct` 30 from bk-005; `entity_media` bucket/key
  CHECK pattern mirrored by `ops_files`; no RLS on any of the 53 booking objects.
- Edges seeded by bk-003 / bk-005 are exactly as §0 says. B2B `_open_case` inserts the case at `confirmed` with an
  approved V1 whose item `position` = `line_no` and USD costs. `desk.answer_line` is transaction-safe, locks the
  hold, works only on `confirmed` holds and fires the bk-022 outbox trigger.
- Permissions: roles admin / sales / contracting exist; `b2b_desk.write`, `pricing.read`, `PREVIEW_PERMISSIONS` exist.
- Cost ≈ $1.05/month (one CMK $1 + S3 pennies) is right; no compute, no LLM.

## Blocking issues (all fixed in design.md)

| # | Issue | Evidence | Fix in design |
|---|---|---|---|
| B1 | **Post-sale statuses settable by hand → "paid" without money.** The existing `POST /trip-cases/{ref}/status` (`change_status`) walks any edge in `trip_case_status_transitions`; only `confirmed` is approval-only. bk-026 seeded `invoice_sent→paid`, `payment_pending→paid` etc., and the guard did not check facts, so any sales user could move a case to `paid` (and B2C to `pre_departure`) with no invoice. | `service.py` `change_status`, `APPROVAL_ONLY_STATUSES = {"confirmed"}` | Money edges move to bk-028; `trip_cases_post_sale_guard` becomes a fact guard per target status (bookings, supply state, invoice state, dates); `change_status` refuses all post-sale targets except `cancelled` (409 `status_system_managed`). §3.1, §4 |
| B2 | **Auto-advance breaks the B2B cancel contract.** `cancellation.py` refuses unless the case status is exactly `confirmed`; after S1 moves a B2B case to `supplier_confirming` / `pre_departure`, an agency's `POST /bookings/{id}/cancel` (AA-974, used by CRM `cancel_trip`) answers `invalid`. | `cancellation.py` ~L314 | S1 widens the check to confirmed / supplier_confirming / pre_departure, cancels pending supplier bookings and notifies staff for requested / confirmed ones; integration test. §3.1 |
| B3 | **Declined supplier booking blocks its replacement.** `UNIQUE (version_item_id) WHERE status <> 'cancelled'` keeps `declined` rows → no second booking with another supplier for the same item (the normal B2C flow after a decline); "live" undefined for the supply badge. | §3.1 | Partial unique WHERE status IN (pending, requested, confirmed); "live" defined the same everywhere. |
| B4 | **Settle trigger loses updates under concurrency.** Two verifies on one invoice in parallel (READ COMMITTED) each sum without the other's uncommitted row → both write `partially_paid` though the invoice is paid; same for payouts. | §3.3 `payments_settle` | Lock the invoice (bill) row `FOR UPDATE` first in the trigger and at the start of record / verify / void. |
| B5 | **"Change after send = cancel + reissue" contradicts "cancel only when net paid = 0".** Any trip change after the deposit (extra night, pax change, bank-fee shortfall, discount) would need a refund first; real flows change after deposit routinely. | §3.3 invoice edges + schedule lock + Q15 | Amendment rule: append-only adjustment lines after send, total recomputed, uncovered schedule rows editable (deferred Σ check), state recomputed, audit + customer notification. D8, §3.3, Q15. |
| B6 | **Idempotency "same key + same body → stored row, other body → 409" is not implementable** with only a key column. | §5 vs §3.3 | `request_sha256` NOT NULL on `payments` and `invoices` (and payouts by the same rule). |
| B7 | **Reminder dedupe index collides staff and customer rows** of the same reminder (same type / entity / key), and a unique violation would abort the job transaction (`notify_staff` is a plain INSERT). | `notifications/service.py` | Index includes `recipient_type`; reminder inserts use `ON CONFLICT DO NOTHING`. |
| B8 | **Done-when not executable as written.** The agent's Dev staff session (AA-910 E2E admin) and preview sessions are read-only, and the AA-682 comment forbids payment actions in agent sessions, yet S1/S3 Done-when has "confirm from the Suppliers tab", "recorded by A, verified by B" on Dev. | `staff.py` docstring (E2E cap, preview) + issue comment | §2 note: S1/S2 writes via DB Migrate run-script calling the services (AA-947 pattern, DRY RUN first); S3/S4 money proven by CI integration tests; the Dev money walkthrough is a human step (UAT video, AA-855); agent checks reads only. |
| B9 | **Case cancel / reopen undefined after money and supply exist.** `confirmed→cancelled` and `cancelled→new_inquiry` (bk-005) exist; nothing said what happens to supplier bookings, invoices, payments, and a reopened case would keep a live invoice. | bk-005 edges | Cancel cascade (pending bookings cancelled, others → staff "cancel with supplier", draft invoice soft-deleted, sent invoice stays until refunds); reopen refused while any live booking / invoice / payment exists. §3.1 |

Also fixed (smaller, in the same edits): payments refused on draft / cancelled invoices; a verified refund may not
take net paid below 0; overpayment allowed but flagged; `payment_instructions` / `invoice_issuer` seeded as
placeholders only (public repo — real bank details via run-script); supply state `none` passes the pre_departure gate
(B2B cases made only of plan lines have no supplier and would never leave `confirmed`); D13 made two-way (desk answer
of a line with a live supplier booking → 409 `answer_from_suppliers_tab`; a B2B-linked confirmed / declined booking
cannot be re-requested, cancelled or replaced by staff).

## Non-blocking notes

1. **PRD §7–9 still unread.** The Read tool also fails here (no `pdftoppm`); raw stream extraction found no text
   (compressed object streams / CID fonts). Keep it as an S0 task (Windows reader), before S1 code.
2. **FK indexes (data standards C5.2e).** The design lists no indexes: every FK (`trip_case_id`, `supplier_id`,
   `invoice_id`, `bill_id`, `*_file_id`, `version_item_id`, staff keys) and every retention predicate column needs
   one; add a line "one btree per FK" to §3 common rules.
3. **Minor units / rounding.** `numeric(…,2)` is fine for storage, but the schedule builder must round each row to the
   currency's minor unit (VND / JPY / IDR = 0) and put the remainder on the last row so Σ schedule = total exactly;
   state it in §3.3 and test it (B2B quotes already use VND, AA-974).
4. **Payment currency.** `payments.currency = invoice currency` forces staff to convert a VND transfer against a USD
   invoice by hand; consider optional `received_amount` / `received_currency` (informational) so evidence matches.
5. **KPI FX.** "USD at the approved FX row of the payment date" differs from ADR 0005 d5 (FX locked at send); using
   the version's `fx_rate_locked` keeps KPIs consistent with the quote. Pick one and say why.
6. **Evidence upload order.** `POST /invoices/{n}/payments {evidence_file_id?}` implies the file exists first, but
   `ops_files` needs `entity_id` = the payment. Specify: record → upload with `entity_id` = payment id → the upload
   service sets `evidence_file_id` in the same transaction (trigger: `evidence_file_id` must point to a file of that
   entity and kind).
7. **File serving.** Presigned GET with `ResponseContentDisposition=attachment` and the stored content type; PDFs are
   stored as uploaded (no re-encode), so never render them inline in the admin. Task role needs `kms:GenerateDataKey`
   + `kms:Decrypt` on the CMK (presigned GET of an SSE-KMS object uses the signer's KMS rights).
8. **Preview exposure.** Adding `billing.read` to `PREVIEW_PERMISSIONS` lets unmerged PR code on the preview host read
   bill-to snapshots and payment references; consider keeping billing reads out of preview (pricing.read precedent is
   commercial data, not PII).
9. **PII tags.** `supplier_bookings.notes` and `supplier_bills.notes` are free text staff will fill with traveller
   names ("room for Mr X"); tag `pii:free_text` as well (DM-6.8 for B2B: name it in the field help); §3.5 "notes
   redacted (no PII by design)" contradicts that.
10. **Customer scope (S5).** Scope invoices by `trip_cases.customer_id` of the invoice's case (not only
    `invoices.customer_id`), so a later customer merge does not orphan them; lead customers (unverified,
    `needs_merge_review`) never match a signed-in identity, so My Payments is empty for them — say so in the copy.
    Booking has no EXTERNAL-token customer route yet and `COGNITO_EXTERNAL_ISSUER` is "never set on Dev" (CONTEXT):
    S5 needs that env + an Infra route/authorizer change; list it under S5 dependencies.
11. **Customer reminders have no reader.** D15 writes customer `notifications` rows, but `booking.customer.v1`
    covers payments only; either add a notifications list to the contract or drop customer rows and rely on the
    Due soon / Overdue chips.
12. **Status of B2C after travel on a void / refund.** No back-step from `pre_departure` / `on_trip` / `completed`;
    say the case keeps its travel status and the invoice / balance badge shows the debt (plus a staff notification).
13. **UI spec drift.** `ui-spec.md` payment states are `received` / `voided` and `/payments/[ref]` is "A S(r)"
    (sales read-only); the design adds `verified` and gives sales `billing.write`. Update the ui-spec status map and
    roles in the S3 PR.
14. **Settings changes are migrations.** Role `booking` has SELECT only on `settings`; Ms. Thư's answers (deposit %,
    due days) become a migration / run-script, not a UI edit — fine, but the "no code change" claim should say so
    (noted in §3.3).
15. **S0 registers.** Besides DM-7 rows, S0's root PR must add the new tables to `docs/database/schema-ownership.md`
    (booking row) and the contracts README row for `booking.customer.v1` (S5).
16. **Agency money to AA.** `b2b_holds.deposit_ref` is a free claim; nothing in AA-682 records or verifies money AA
    receives from agencies (O-10 later). Make that explicit in §1 D12 so "owed by agencies" is not assumed covered.
17. **Supplier booking dates/pax** come from case `start_date` + item `day_from` / `day_to` and case pax; B2B costs
    are one USD row per item (`version_item_costs` is not unique per item) — "copied from version_item_costs" should
    say "sum of the item's cost rows, net currency of the first; refuse when currencies differ".
18. **Version with NULL `total_price` / `currency`** (allowed by the schema): invoice create must 409
    `version_not_priced` (added to the send check; add to the create route too).

## Verdict

Sound overall shape (derived badge, DB-enforced machines, maker-checker, proforma, no RLS consistent with Booking,
reuse of `desk.answer_line`, no new outbox event, cheap). With B1–B9 fixed in `design.md`, S0–S2 can start;
S3 should not start before notes 2, 3 and 6 are written into the design.
