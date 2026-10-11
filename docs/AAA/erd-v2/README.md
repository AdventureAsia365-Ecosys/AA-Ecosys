# AA-Booking (AAA) — ERD v2

Written for AA-677 (S225), decisions confirmed S226 (AA builds AA-Booking in-house). It moves to
the AA-Booking repo (`docs/erd/`) once that repo exists (AA-678). Schema `booking.*` on the shared acc2 RDS; owner repo AA-Booking; migration key
`bk-NNN` (`docs/database/schema-ownership.md`). The DBML is in [`booking.dbml`](booking.dbml);
paste it into dbdiagram.io to render it.

**Inputs:**
- `../AA ERD.pdf` (v1: 17 tables, 6 enums);
- `../Adventure Asia PRD and Technical Spec Doc [Final].pdf`;
- `../AAA_Quanskill_Handover_Review.docx` (10/06/2026);
- ADR 0001 (decisions 5–7) and ADR 0002;
- `../../tripplanner-to-aaa-handoff.md`.

## Decisions encoded

1. **Same RDS, own schema.** `booking.*` on acc2. UUID primary keys everywhere (v1 used `int`).
   `created_at` / `updated_at` on every business table, `deleted_at` where users can delete. This
   closes the handover P1 item on audit columns and soft delete.
2. **Golden records, not copies** (ADR 0002 — only CIS writes content):
   - **Places:** `shared.destinations` (CIS) is the place record. AAA keeps only its commercial page
     in `destination_profiles` (keyed by the CIS id).
   - **Countries:** keyed by ISO code in `country_profiles`, with area, FAQ, festivals and weather.
   - **Coordinates:** none stored in `booking.*`.
   - **Photos:** tour photos are read from `shared.v_tour_photos`.
3. **Catalog lineage.** `trip_plans` and `activities` carry `(source_system, source_id)` with a
   unique index. A CIS `catalog.tour.*` event is applied idempotently: `source_id` =
   `published_tours.tour_id` or an atom id. Commercial fields stay AAA's: prices, hotels,
   suppliers, SKU.
4. **Multi-tour, multi-country** (answers two open questions):
   - a template lists its places in `trip_plan_destinations` (M:N, ordered);
   - a case lists its countries in `trip_case_countries`;
   - a case keeps the TripPlanner leg chain in `trip_case_legs` (`source_tour_id`, `day_from`, `day_to`).
   - The single `country_id` columns are gone.
5. **Handover P0/P1 gaps closed:**
   - `media_files` (`s3_bucket` + `s3_key`; CDN URL built by the API) plus `entity_media` for galleries;
   - `supplier_bookings` (item, supplier, price, voucher, status);
   - `supplier_bills` + `supplier_bill_items`;
   - `invoice_items` (was `items json`);
   - `payment_schedule` (deposit / second / final);
   - payment evidence: `payments.payment_description` + `evidence_media_id`;
   - `trip_case_status` enum (13 values) + `trip_case_status_history`;
   - `audit_logs`.
6. **Pricing.** `trip_plan_prices` (season or date range, pax band, currency) replaces
   `trip_plans.price json`. A case's price lives on the approved version (`total_price`, item
   `unit_price`), then on invoices — not on `trip_cases`.
7. **Identity.** Customers and staff are separate tables:
   - **Customers** are OTP-only (`customer_otps` stores a hash, never the code). After the first OTP
     they get a refresh-token session (`customer_sessions`).
   - **Staff** use the ecosystem staff model from AA-656 (one RBAC matrix). `staff_users.role` is
     `admin` / `sales` / `content_creator`. Permissions are the PRD matrix in code, not Spatie-style
     tables.
8. **Contracts in.** `inbox_events` is the consumer side of the ADR 0001 outbox:
   - `inquiry.submitted` from TripPlanner and `catalog.tour.*` from CIS;
   - one row per `idempotency_key`, processed once.
   - `trip_cases.idempotency_key` keeps one inquiry from creating two cases.

## v1 → v2 mapping

| v1 table | v2 | Change and reason |
|---|---|---|
| `users` | `customers` + `staff_users` | Split: customers are OTP-only, staff share the ecosystem staff model; `role customer` disappears. Profile picture → media file |
| `user_otps` | `customer_otps` | Store `otp_hash`, `used_at`, `attempts` (rate limit) instead of plain `otp_code` + `is_used` |
| — | `customer_sessions` | New: refresh token after OTP (open question 1) |
| `areas` | `areas` | + `updated_at` |
| `countries` | `country_profiles` | Keyed by ISO code; + `subtitle`, `status`, audit (handover P2); lat/lng dropped (CIS owns places); `media` → `cover_media_id` |
| `destinations` | `destination_profiles` | Keyed by CIS `shared.destinations.id`; name/lat/lng read from CIS; + `status`, audit |
| `suppliers` | `suppliers` | + `address`, `status`, split `contact_email` / `contact_phone`, audit, soft delete (handover P2) |
| `hotels` | `hotels` | `destination_id` → CIS place, `country_id` derived; + `hotel_style`, `status`, audit, soft delete; media → `entity_media` |
| `activities` | `activities` | `country_id` + `city` + lat/lng → `destination_id`; + `source_system/source_id` (catalog sync), `is_draft` (content-creator drafts, PRD), `status`, audit |
| `trip_plans` | `trip_plans` | + `sku`, `slug`, `title`, `duration_days/nights`, lineage, audit, soft delete; − lat/lng, − `country_id` (→ `trip_plan_destinations`), − start/end date (a template has a duration), − `price json` (→ `trip_plan_prices`), `status varchar` → enum |
| — | `trip_plan_destinations`, `trip_plan_prices` | New (destination link question; pricing) |
| `trip_plan_itinerary` | `trip_plan_itinerary` | `hotel varchar` → `hotel_id`; + `destination_id` (instead of item lat/lng), `status`, audit; `travel_hours` numeric |
| `trip_cases` | `trip_cases` | + `code`, `pax`, `currency`, lineage + `idempotency_key`; `status varchar` → 13-value enum; − `price varchar`, − lat/lng, − `country_id` (→ `trip_case_countries`) |
| — | `trip_case_countries`, `trip_case_legs`, `trip_case_status_history` | New (multi-country; TripPlanner leg chain; status trace) |
| `trip_case_versions` | `trip_case_versions` | Boolean flags kept (project rule); + `total_price`, `approved_at`, `updated_at`; unique approved version per case (locked) |
| `trip_case_version_itinerary` | same | `hotel varchar` → `hotel_id`; + `destination_id`, `unit_price`, audit |
| `trip_case_checks` | same | One row per case (PK = `trip_case_id`); + `updated_by` |
| `staff_assignments` | same | `staff_user_id` → `staff_users`; + `unassigned_at` |
| `notifications` | same | `recipient_type` + `recipient_id` (customer or staff); `is_read` → `read_at` |
| `payments` | `payments` | Linked to `payment_schedule` + invoice; + `payment_description`, `evidence_media_id`, `received_at`, `recorded_by`; `type` enum moves to the schedule (`payment_kind`) |
| `invoices` | `invoices` + `invoice_items` | + `trip_case_id`, `invoice_number`, currency, cancel fields (CANCEL INVOICE screen); `items json` → `invoice_items`; `status` → enum |
| — | `payment_schedule`, `supplier_bookings`, `supplier_bills`, `supplier_bill_items`, `media_files`, `entity_media`, `audit_logs`, `inbox_events` | New (PRD §7–10, handover P0/P1, ADR 0001 contracts) |

Enums: `user_role` → `staff_role` (no `customer`); `payment_type` → `payment_kind` (+ `second`,
`other`); new `trip_case_status`, `record_status`, `payment_status`, `supplier_booking_status`,
`invoice_status`, `bill_status`, `source_system`. Enum values are lower-case.

## The 6 open business questions — decided (we build AA-Booking ourselves)

Confirmed by Nghiệp (S226): AA builds AA-Booking in-house, so these are no longer "ask the
external handover team" items (Mr. Mạnh is no longer involved in AAA). The v2 schema encodes the
answers below; revisit only if a concrete requirement contradicts one.

| # | Question (handover §3.2) | Decision in v2 |
|---|---|---|
| 1 | Does a customer enter an OTP every time the app opens? | No. OTP once per device, then a refresh-token session (`customer_sessions`, 30 days, revocable). OTP again on a new device or after revoke |
| 2 | How do trip plans link to destinations? | Many-to-many, ordered: `trip_plan_destinations` → CIS `shared.destinations`. Countries follow from the destinations |
| 3 | Can one trip case cover several countries? | Yes: `trip_case_countries` (M:N), plus `trip_case_legs` when the case comes from a multi-tour TripPlanner draft |
| 4 | Are customer accounts managed in the admin dashboard? | Yes: staff with role `admin` see and block customers (`customers.is_blocked`); customers are created by their first OTP or by an inquiry, never with a password |
| 5 | Detailed permissions (replace the 3 Spatie tables with an enum)? | Yes: `staff_role` enum + the PRD permission matrix in code (same pattern as CIS `frontend/lib/rbac.ts`, AA-656). Revisit only if per-user overrides are needed |
| 6 | What are lat/lng for (trip plans, trip cases, itinerary)? | Nothing AAA needs to store: coordinates come from CIS places through `destination_id`. All lat/lng columns are removed |

## Not decided here

- Hotel and supplier sync with an external system (Lemax-style back office, AA-710) — out of scope.
- Exact `inquiry.submitted` / `catalog.tour.*` payloads: `docs/contracts/` (not created yet) and
  the handoff spec.
- `country_profiles` keys by ISO code, but `shared.destinations.country` is a country name today.
  CIS needs a name → ISO mapping (or a `shared.countries` table owned by CIS) before AAA reads
  countries from places.
