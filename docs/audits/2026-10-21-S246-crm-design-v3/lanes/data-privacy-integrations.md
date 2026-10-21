# Partner CRM v3: data model, privacy (F1–F5) and integrations

Session S246, 21/10/2026. Lane: data, privacy and integrations architect. Draft only (read-only on repos, no paid calls).

**Inputs used:**
- Spec: `docs/research/partner-crm-spec.md`. The task path `v2.1/partner-crm-spec.md` does not exist (X1 below).
- Designs: v1 `docs/audits/2026-10-20-S245-tenant-crm/README.md` §8.2–8.4 and §14; v2 `v2/crm-design-v2.md`; v2.1
  `v2.1/crm-design-v2.1-tech.md`; v2.2 `.tmp-session/s245-r2/r4/crm-v2.2-simplified.md` + `decisions-v2.2.json`;
  `v2.1/owner-approvals-r2.md`; `v2.1/review-integration.md`.
- Ideas: R1–R16 `docs/audits/2026-10-20-S245-crm-tern-traveljoy/comparison.md` §5; R17–R44 + C12/C31
  `docs/audits/2026-10-21-S246-crm-more-ideas/README.md` + `decisions.json`.
- Answers: `docs/audits/2026-10-21-S246-thu-questionnaire/answers.md` (v1, 41), `reply-to-notes.md`,
  `questions-v2.md` + `answers-v2.md` (v2, 12, treated as decided).
- Platform: `docs/ecosystem-architecture.md`, ADR 0005, 0006, 0008, data standards Part B (`02-data-management.md`),
  `apps/AA-Booking/CONTEXT.md`, `apps/AA-CIS-App/CONTEXT.md`, `docs/architecture/db-schema-reference.md` (Verified
  2026-10-20, Booking at `bk-017`).

**Conventions:**
- `[S:§n]` = spec section; `[M:n]` = spec module (F1–F5, 1–18); `[Rn]` = approved idea; `[Cn]` = AA flow gap;
  `[A:x.y]` = questionnaire v1 answer, `[A2:x.y]` = v2 answer; `[N:x.y]` = reply-to-notes row; `[S1]..[S7]`, `[A1]`,
  `[V1]..[V3]` = v2.2 items; `[Tn]` = v2.1 decisions; `[Dn]`/`[Nn]`/`[Hn]` = owner decisions in v2/v2.1.
- "(est.)" = my estimate, not checked against a source. "(unverified)" = an external fact I did not re-check today.

---

## 0. Summary

1. **Where the data lives.** Schema `crm` on the shared Dev RDS, owned by the new app repo **AA-Partner** (portal +
   CRM web + CRM API, v2 §3.2, N1), migration key `crm-NNN`, roles `crm_owner` (NOLOGIN) / `crm_app` (LOGIN, limit 6,
   pool 3, T4) plus three NOLOGIN read roles. No grant to or from any other schema (N5). Other apps are reached over
   HTTP only: Booking `booking.b2b.v1`, CIS `tenant.membership.v1` / `tenant.entitlements.v1` / `catalog.http.v1`.
   CRM publishes `crm.ops.v1` and `crm.insights.v1`. This contradicts ADR 0008 §8 and DM-6.8 ("a CIS module"), which
   need an amendment (X2).
2. **The data model** has 11 groups and about 75 tables (§2). Five rules are built into the first migrations because
   they are expensive to retrofit:
   - frozen FX on every money row [R17];
   - a booking-line lifecycle [R18];
   - one trash for every object and a delete block [R21];
   - archive + Lost reasons [R23];
   - per-person traveller access [R22].
3. **Privacy (F1–F5)**, per v2.2 and the answers:
   - one KMS key per environment, one DEK per agency per purpose, AES-256-GCM, blind indexes derived by HKDF [S1];
   - F1 and F2 are split, and the link between them is encrypted;
   - a three-pass PII filter before any LLM call, which fails closed;
   - AA support access in three layers [A1, A:3.4, A:3.5, A:6.3];
   - audit: 12 months in the app, hourly S3 Object Lock export, kept for 7 years in total [A:3.8, N:3.8];
   - deletion readable nowhere after at most 30 days [A:3.7, V1].
4. **Integrations**, per the answers:
   - Booking B2B API for products, quote, availability, hold, confirm, cancel and an events feed. It carries no PII,
     only pax counts and age bands;
   - Stripe Connect Standard, Checkout Sessions created on demand, tied to the hold expiry [C31];
   - the agency's own Twilio for WhatsApp and SMS, with a Meta Tech Provider fallback [A:4.2→N:4.2, A:4.4];
   - send-as through the agency's Gmail **and** Outlook, forward-in by one SES domain rule [A2:4.1, N:4.8];
   - self-built e-sign, with BoldSign as the fallback [A:4.1, A2:5.1];
   - SES for system mail and campaigns;
   - an insurance declination signed with the waiver [A2:5.1].
5. **Every approved item is covered:** R1–R44, C12 and C31 (§9). Items decided as "after 23 modules" (R12, in-app
   insurance sales) and "gated" items (R44 step 2) get their data hooks now.
6. **24 contradictions between the inputs are flagged (§10).** Five block code:
   - X2: ADR 0008 / DM-6.8 say CRM is a CIS module;
   - X3: ADR 0008 step 9 + DM-6.4 vs the CRM's own LLM gateway;
   - X4: traveller OTP vs ADR 0008 step 8 / ADR 0006;
   - X5: module 8 data flow vs DM-6.8 "Booking creates its own customer";
   - X16: mandatory agency MFA vs the EXTERNAL pool having MFA off.

---

## 1. Placement: owner, schema, roles, boundaries

### 1.1 ADR 0008 decision gate

| Gate question (ADR 0008 §2) | Answer |
|---|---|
| Owns data nobody else owns? | **Yes.** The agency is the controller of its travellers' data. AA is the processor (DM-6.8, v1 §14) |
| New capability of an existing domain? | **No.** Owner decision 20/10 (`v2/owner-input.md`): a separate app, integrated into the tenant portal, not a CIS module |
| New domain with its own lifecycle? | **Yes** → own schema + the 12-step playbook (ADR 0008 §3) |

### 1.2 Placement table

| Item | Value | Source |
|---|---|---|
| Owning repo | **AA-Partner** (new, public, org AdventureAsia365-Ecosys): `web/` (portal + CRM UI + traveller host), `api/` (CRM FastAPI + in-process `crm.job` worker) | v2 §3.2, N1, D17, D22 b |
| Schema / key | `crm`, migrations `crm-NNN` in `AA-Partner/db/migrations/`. A byte copy goes to `AA-CIS-Infra/db/migrations/crm/` and is applied **only** by DB Migrate. Registered in `owners.yaml` (job-kind prefix `crm_`, `IDLE_EXEMPT_KINDS` from day one) | ADR 0008 §3 steps 2–4; v2.1 §3.3 |
| Dev | Schema `crm` in `aa-cis-dev-db` (acc2). Synthetic agencies only: `tenant.is_synthetic` must be true on Dev (C7.1a guard) | v2.1 §3.4, H4 c |
| Prod (Go-real) | Prod cell RDS or a shared prod RDS. **Not decided now** (N4 deferred to Go-real, v2.2 §2 "Rejected or not done") | T3 |
| DEK store | Dev: table `crm.tenant_key`. Go-real on a shared RDS: S3 with its own retention ≤ 30 days, so the deletion promise does not depend on CIS/Booking snapshots | S1 (E2), V1 |
| Roles | `crm_owner` NOLOGIN owns everything. `crm_app` LOGIN runtime (limit 6, pool 3). `crm_ai_reader` NOLOGIN (F2 + AI views only). `crm_insights` NOLOGIN (insight fact view only). `crm_support_reader` NOLOGIN (SELECT-only + INSERT on `audit_event`; for layer-2 support sessions). `crm_app` reaches the three NOLOGIN roles only through `SET LOCAL ROLE` inside `tenant_tx()` | v1 §8.3, T4, DM-6.8 "explicit policy", §5.6 |
| Cross-schema | **None.** `crm_app` has no grant outside `crm.*`, and no other role has a grant on `crm.*`. An isolation probe as `cis_app`, `booking`, `tripplanner` and `aa_app_user` must return 42501 on every `crm.*` object | N5, ADR 0008 §3 step 12, v1 §8.3 F4 |
| Tour key | `(source_system, source_id)` soft key, never `tour_id` | ADR 0008 §9 |
| CIS tenant | `crm.tenant.tenant_id` = CIS tenant id (soft key). Membership feed from `tenant.membership.v1`. Roles (owner / agent / assistant) are owned and written by CRM only | T9, v2.1 §2.1 |

**Boundary rules:**
- **No FK across schemas.** Booking references are text ids (`bk_hold_id`, `bk_booking_id`, `departure_id`), checked
  over HTTP.
- **Payload rule.** `crm.job.payload`, `crm.outbox` and every event carry ids only. CI rejects any `pii:` key
  (DM-6.3, v2.1 §3.3).
- **Two DB rules, two consequences:**
  - `crm.job` has **no RLS**: it is a platform table with no tenant data, only ids;
  - every tenant table has `tenant_id uuid NOT NULL` and ENABLE + **FORCE** RLS from `crm-001`. The policy is
    `TO crm_app USING/WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)`.
    Membership is checked before the GUC is set (ADR 0008 §3 step 5).

---

## 2. Data model (schema `crm`)

### 2.1 Column conventions

- **Base columns.** Every tenant table has `tenant_id`, `created_at`, `created_by` (member id, `system`, or `traveler:<id>`)
  and `updated_at`.
- **Trash [R21].** Every user-deletable object also has `deleted_at`, `deleted_by` and `purge_after`.
- **Encrypted columns.** `<col>_enc bytea` holds AES-256-GCM ciphertext with the format
  `key_version ‖ nonce ‖ ciphertext ‖ tag`. The AAD is `tenant_id ‖ table ‖ column ‖ row_id`. The DEK comes from the
  tenant's `vault` purpose (§5.1).
- **Blind indexes.** `<col>_bidx bytea` = truncated HMAC (§5.2).
- **PII tags.** Each PII column carries `COMMENT 'pii:<class>'` (DM-6.1). Three classes are **new**: `government_id`,
  `health` and `emergency_contact`. They need a standards amendment (X17).
- **Status columns** use `TEXT + CHECK`. Lifecycle edges are DB-enforced by a transitions table + trigger (Booking
  `bk-003` pattern).
- **Money columns:**
  - every money row stores `amount numeric(14,2)` + `currency char(3)`;
  - it also stores the **frozen FX block** [R17]: `base_currency`, `amount_base`, `fx_rate numeric(18,8)`,
    `fx_rate_date`, `fx_source` (`aa_quote_lock | platform_daily | manual`) and `fx_basis`
    (`booking_date | receipt_date | quote_lock`);
  - a trigger refuses any UPDATE of the FX block. A correction is a new row with `supersedes_id`.

### 2.2 Group A: tenancy, keys, access (F4, F5, A1)

| Table | Key fields | Protection | Implements |
|---|---|---|---|
| `tenant` | `tenant_id` PK (= CIS tenant id), `slug`, `is_synthetic`, `status active\|locked\|offboarding\|deleted`, `offboarding_requested_at` | No PII | M:F4; v2.1 §3.4 |
| `tenant_settings` | See the note below the table | No PII | M:F4; R17, R18, R21, R24, R27, R42; A:3.12; D12 |
| `tenant_entitlement` | Mirror of `tenant.entitlements.v1`: `plan`, `features_allowed[]`, `seat_limit`, `ai_fair_use_usd`, `synced_at` | No PII | R11, A:1.1 (free now, tiers later); H2 |
| `member` | `member_id`, `(iss, sub)` UNIQUE per tenant, `display_name` (`pii:name`), `email` (`pii:contact`), `role owner\|agent\|assistant`, `status invited\|active\|suspended\|removed`, `cis_membership_seen_at` | Agency staff data (not traveller). Plain columns, but every value is fed to the F3 known-value list | M:F4; T9; R8 |
| `owner_recovery_request` | `candidate_member_id` (must be an active member), `requested_by` (aa-staff id), `not_before = requested_at + 14 days`, `cancelled_by`, `executed_at` | — | A1 layer 1; A:6.3 |
| `support_grant` | `granted_by` (owner), `scope read_only`, `reveal_f1 bool` (default false), `expires_at` (1–7 days, default 24 h), `revoked_at`, `reason_required true` | — | A1 layer 2; A:3.5, N:3.5 |
| `support_session` | `grant_id`, `staff_ref` (WORKFORCE `(iss, sub)`), `ticket_ref`, `started_at`, `ended_at` | Every read inside a session also writes an `audit_event` (actor `support:<staff>`) | A1 layer 2; M:F5 |
| `tenant_key` | `purpose` (see §5.1), `key_version`, `wrapped_dek`, `kms_key_arn`, `encryption_context jsonb`, `created_at`, `retired_at`, `destroyed_at` | Wrapped by KMS only; never plaintext at rest | S1; E2 pluggable store; A:3.6 |
| `integration_credential` | `provider twilio\|google\|microsoft\|boldsign`, `account_ref` (Twilio SID, mailbox address), `secret_enc` (purpose `integration`), `status ok\|reconnect_needed\|revoked`, `last_checked_at`, `failure_class` | `conf:credential`. Decrypted only in the dispatcher and hook code paths | S14 (v2.1); R24 |

`tenant_settings` columns:
- `base_currency` (AUD | USD | VND | EUR | …), `timezone`, `default_locale` (`en` | `vi`);
- `trash_days` (default 7), `booking_validation_level off|basic|strict` [R18];
- `service_fee_enabled` (default false) [R27];
- `allow_platform_sender` (default false) [R24];
- `insights_opt_out` (default false) [A:3.12 → N:3.12];
- `ai_enabled` (default false) [D12], `ai_budget_usd` (default 2);
- `release_channel stable|preview` [R42];
- `custom_domain`, `retention_overrides jsonb`.

### 2.3 Group B: F1 identity vault

| Table | Key fields | Protection | Implements |
|---|---|---|---|
| `traveler` | See the column list below the table | Name, email, phone, DOB, passport, emergency contact and the profile pointer are encrypted. Archive and trash columns are plain | M:F1; S:§5 Stage 1/3; R2, R6, R7, R8, R23, R35 |
| `traveler_health` | `traveler_id`, `health_flags_enc` (codes only, never free text), `consent_id` | `pii:health`. Exists only with consent (`consent.purpose = health_data`). Mirrored as codes in F2 | S:§5 rules 3, Data placement |
| `traveler_relation` | `from_id`, `to_id`, `kind spouse\|partner\|parent\|child\|sibling\|friend\|referrer`, `inverse_id` (auto-created pair) | ids only | R7 |
| `traveler_flight` | `trip_id`, `traveler_id`, `direction arrival\|departure`, `flight_no_enc`, `sched_local`, `airport_iata`, `tz` | `pii:travel` (encrypted: it ties a person to a time and place). Structured, so it can feed the ops hand-off | S:§5 Stage 3; R33, R44 |
| `document` | `trip_id`, `traveler_id?`, `kind passport_scan\|waiver_pdf\|terms_pdf\|ticket\|voucher\|invoice_pdf\|supplier_confirmation\|other`, `s3_key`, `sha256`, `size`, `visible_to_travelers bool`, `write_only bool` (passport: true), `uploaded_by member\|traveler\|aa_booking` | Object encrypted client-side with the `docs` DEK before PUT, plus S3 SSE-KMS as a second layer (§5.1). A passport cannot be read back through the traveller host | M:F1, M:11, M:12; R22; R10 |
| `consent` | `traveler_id`, `purpose contact\|marketing\|health_data\|ops_release\|ai_processing\|terms`, `value bool`, `at`, `source form\|portal\|agent_recorded\|import`, `agreement_doc_id?` | Append-only (INSERT/SELECT only) | DM-6.5; R2, R14, R34, R36; S:§5 rule 3 |

`traveler` columns:
- id and names: `traveler_id`, `given_name_enc`, `family_name_enc` (as on passport), `display_name_enc`;
- contact: `email_enc`, `phone_enc` (E.164), `preferred_channel`;
- blind indexes: `email_bidx`, `phone_bidx`, `name_bidx`, `name_token_bidx bytea[]`;
- identity documents: `dob_enc`, `nationality_enc`, `passport_no_enc`, `passport_expiry_enc`,
  `passport_country_enc` (`pii:government_id`);
- `emergency_contact_enc` (`pii:emergency_contact`);
- `profile_token_enc`: the encrypted pointer to F2 (§5.3);
- ownership and lifecycle: `owner_member_id` [R8], `lead_source`, `referrer_traveler_id` [R7], `archived_at`,
  `archive_reason` [R23], trash columns [R21].

### 2.4 Group C: F2 pseudonymous profile (readable by `crm_ai_reader` and `crm_insights` through views)

| Table | Key fields | Protection | Implements |
|---|---|---|---|
| `traveler_profile` | See the column list below the table | No identity column. **No FK** to `traveler`. The token is random, not derived. Free-text Stage 2 answers do **not** go here: they go to `note` (F1-encrypted) | M:F2; S:§5 Stage 1–2 bands; R32, R36 |
| `trip_party` | `trip_id`, `traveler_token`, `role lead\|companion`, `age_band_at_departure` | The F2 twin of `trip_traveler`. This is the only party link AI and insight views can see | M:F2, M:14 |
| `profile_history` | `traveler_token`, `aa_departure_id`, `aa_product_key`, `stage_reached`, `year_month` | From Booking events; no identity | M:F2 "AA trip history"; M:17 |

`traveler_profile` columns:
- token: `traveler_token uuid` PK (random);
- bands: `age_band` (recomputed only when DOB or departure date change [R32]), `residence_country`, `budget_band`
  (per person, excluding flights), `fitness_band`, `trek_experience`, `altitude_ok`, `pace`, `accommodation_tier`,
  `group_pref private|small_group`;
- codes: `interests[]`, `must_do_codes[]`, `must_avoid_codes[]`, `occasion`, `dietary_flags[]`, `mobility_flags[]`;
- planning: `budget_flex`, `decision_maker`, `booking_timeline`, `competing_quotes bool`;
- history and status: `repeat_count`, `marketing_ok bool` (derived from `consent`), `stage2_completeness`.

### 2.5 Group D: pipeline, intake, tasks (modules 1, 2, 10, §4, §5)

| Table | Key fields | Protection | Implements |
|---|---|---|---|
| `trip` | See the column list below the table | `pii:travel`; `note` text lives elsewhere | M:2; S:§4; R1, R12, R23, R29; C12 |
| `trip_stage_transition` | Allowed edges (DB-enforced trigger) | — | S:§4 gates; C12 |
| `trip_stage_history` | Append-only: `from`, `to`, `actor`, `reason`, `override bool` (Stage 2 < 80 % override) | — | S:§4; M:F5 |
| `trip_traveler` | `trip_id`, `traveler_id`, `role lead\|companion`, `portal_access lead\|companion\|none` | F1 side of the party link; `crm_app` only | R22; S:§7 TripTraveler |
| `task` | See the column list below the table | — | M:10; S:§5 automation; R20 |
| `note` | `trip_id?`, `traveler_id?`, `body_enc`, `kind internal\|call_log\|stage2_free_text` | F1-encrypted; passes F3 before any AI use | M:2, M:5; R40 |
| `tag`, `tag_link` | `tag.kind agency\|system`; `system` tags such as `aa:trekking` or `aa:day-tour` are derived from the CIS catalog, never set by hand | — | R3, R29 |
| `form_definition` | `stage s1\|s2\|s3`, `version`, `schema jsonb` (pages, AA-prebuilt conditional branches), `locale` | No PII | M:1; R31; S:§5 rules 1, 4 |
| `intake_form` | `public_key`, `allowed_origins[]`, `form_definition_id`, `honeypot_field` | — | M:1 |
| `form_submission` | `stage`, `trip_id?`, `payload_enc`, `idempotency_key` UNIQUE, `hidden_answers_dropped int`, `purge_after = +90 d` | The server drops answers of hidden branches before storing them [R31] | M:1; DM-6.6 |
| `metric_event` | `name` (`itinerary.sent\|accepted\|updated`, `proposal.viewed`, `selection.changed`, `deposit.paid`, …), `trip_id`, `at`, `props jsonb` (no PII) | — | S:§11.7; R4; L5 |
| `metric_daily` | Per tenant × day × metric rollup, kept 25 months | — | R28 (year-over-year) |

`trip` columns:
- `trip_id`, `title`;
- `stage`: `inquiry|qualifying|proposal|booked|pre_departure|travelling|completed|lost|cancelled`;
- `stage_entered_at`, `waiting_on agency|client|aa|supplier|none` (derived) [R1];
- dates: `start_date?`, `end_date?`, `month?`, `date_flex_days`, `nights`;
- `destinations[]` (CIS place ids), `party_adults`, `party_child_ages int[]`;
- `budget_band`, `trip_style relaxed|balanced|adventure`;
- `proposal_format visual|email|text`, `intake_completeness jsonb {s1, s2, s3}`;
- ownership: `owner_member_id`, `lead_source`;
- end reasons: `lost_reason_code`, `lost_reason_note_enc` [R23], `cancel_reason_code` [C12];
- `group_departure_ref?` (hook for R12), trash columns.

`task` columns:
- `trip_id?`, `kind`, `assignee_member_id`, `status open|done|skipped`;
- due rule [R20]: `due_anchor departure|return|created|stage_entered|hold_expiry|deposit_paid|ops_handoff`,
  `due_offset_days`;
- `due_at?` (NULL = "awaiting dates" bucket), `due_overridden bool` (a manual date is never recomputed);
- `workflow_run_id?`.

**`cancelled`** is a new terminal stage, reachable from `booked`, `pre_departure` and `travelling` [C12]. The spec
pipeline has only `lost` before `booked` (X20).

### 2.6 Group E: proposal, client access, agreements (modules 3, 4, 11, 12)

| Table | Key fields | Protection | Implements |
|---|---|---|---|
| `proposal` | See the column list below the table | — | M:3, M:4; S:§7 |
| `proposal_day` | `day_no` (0 = "Before you go"), `date?`, `tz` (IANA, derived from the AA tour place), `place_id` | — | R33, R38 |
| `option_block` | `type day\|activity\|lodging\|transfer`, `default_option_id` (from Stage 2) | — | M:3; S:§5 rule 5 |
| `option` | See the column list below the table | `conf:commercial` on net | M:3; M:15; R26, R40 |
| `option_rule` | `requires[]`, `excludes[]` | — | M:3 dependency rules |
| `selection` | `proposal_id`, `day_no`, `option_id`, `by client\|agent`, `at` | — | M:3; R19 (diff is computed from consecutive rows) |
| `client_link` | `token_hash` (`conf:credential`), `trip_id`, `purpose proposal\|portal`, `traveler_id?` (portal only), `expires_at`, `first_opened_at`, `cookie_bound bool` | The token moves to a cookie on first open; `Referrer-Policy: no-referrer` (S13) | M:3 (no client login); M:11 |
| `traveler_access` | `trip_id`, `traveler_id`, `level lead\|companion`, `otp_email_hint` (masked) | Each person signs in with their own OTP; a companion never sees another person's F1 [R22] | R22; M:11 |
| `otp_challenge` | `traveler_id`, `code_hash`, `attempts`, `locked_until`, `expires_at` (10 min), `purge_after` (24 h) | Lockout and rate rules copied from Booking (L4) | M:11; R22 |
| `prep_pack_selection` | `trip_id`, `cis_pack_id` + `cis_pack_version`, `agency_edits_enc?`, `checklist[]` | AA pack content stays in CIS (ADR 0002, X12) | R38; A:2.3 |
| `agreement_doc` | `kind terms\|waiver\|insurance_declination\|consent_text`, `version`, `locale`, `body`, `sha256`, `effective_from`, `is_aa_default`, `published_by` | Versioned; never deleted; a new version on each publish | R34; M:12; A:5.3; A2:5.1 |
| `terms_acceptance` | `trip_id`, `traveler_id`, `agreement_doc_id`, `proposal_id`, `price_hash`, `bk_hold_ids[]`, `at`, `ip_hash`, `ua_hash` | Append-only | R34 (click-accept; does not replace e-sign) |
| `signature_request` | `trip_id`, `traveler_id`, `agreement_doc_ids[]`, `provider self\|boldsign`, `provider_ref?`, `status sent\|viewed\|signed\|declined\|expired`, `signed_pdf_document_id` | — | M:12; A:4.1 |
| `signature_event` | Append-only: `otp_verified`, `viewed`, `consent_ticked`, `typed_name_hash`, `signed`, `ip_hash`, `ua_hash`, `at`, `pdf_sha256`, `seal_sig` | The evidence trail for the insurer | M:12; S:§9 audit trail |

`proposal` columns:
- `trip_id`, `version`, `status draft|sent|accepted|superseded|expired`, `format`;
- pricing: `price_hash`, `display_currency`, `quote_fx` (frozen FX block), `price_visibility total_only|per_day|per_line`
  (default `total_only`, C13 note);
- dates: `valid_until` (= min(quote validity, active hold expiries)), `sent_at`, `accepted_at`;
- `agreement_doc_id` [R34].

`option` columns:
- source: `source aa|agency_supplier`, `aa_component_ref` (Booking component id or `(source_system, source_id)`),
  `agency_supplier_id?`;
- `title_from_catalog bool`, `title`;
- prices: `sell_delta`, `net_delta` (agent only, `conf:commercial`);
- availability: `availability available|on_request|sold_out|unknown`, `confirm_class confirmed|aa_on_request|agency_booking`
  [R26], `last_quoted_at`, `bk_quote_line_ref`.

### 2.7 Group F: money (modules 6, 7, 13, 15; R17, R18, R25, R26, R27; C12, C31)

| Table | Key fields | Protection | Implements |
|---|---|---|---|
| `agency_supplier` | `kind aa\|own` (AA is a built-in row), `name`, `category`, `contact_name` (`pii:name`), `contact_email`, `default_commission_pct`, `confirmation_unique bool` | — | M:15; R18 |
| `booking_line` | See the column list below the table | `conf:commercial` | M:6; R18, R22, R25, R26 |
| `booking_line_money` | `line_id`; `cost`, `sell` and `commission_expected`, each with amount + currency + frozen FX block. The FX basis is `booking_date` = the date the line became `confirmed` | **RLS adds `current_setting('app.member_role') IN ('owner', 'agent')`**: the assistant cannot read margins (S:§3) | M:6, M:13; R17 |
| `fx_rate_platform` | `rate_date`, `base`, `quote`, `rate`, `source ecb\|sbv\|booking_b2b\|manual_aa`, `fetched_at` | No `tenant_id`; SELECT for `crm_app` without RLS (reference data) | R17 |
| `fx_rate_override` | `tenant_id`, `rate_date`, `base`, `quote`, `rate`, `set_by` | — | R17 (owner manual entry, e.g. VND) |
| `invoice` | See the column list below the table | — | M:7; R27; C31 |
| `payment_schedule` | `trip_id`, `deposit_pct`, `balance_due_anchor departure`, `balance_due_offset_days` | — | M:7 |
| `payment` | See the column list below the table | `pii:payment` (references only; no card data, PCI out of scope) | M:7; R17; M:13 |
| `refund_request` | `payment_id`, `amount`, `reason`, `status proposed\|approved\|executed\|rejected`, `approved_by` (an agent must approve) | — | C12, C31 |
| `commission` | See the column list below the table | — | M:13; R17, R18 |
| `payment_provider_account` | `provider stripe`, `stripe_account_id`, `country`, `default_currency`, `charges_enabled`, `payouts_enabled`, `details_submitted`, `disconnected_at` | No secret: platform key + `Stripe-Account` header | M:7; D10 a |

`booking_line` columns:
- link: `trip_id`, `supplier_kind aa|agency`, `agency_supplier_id`, `bk_hold_id?`, `bk_booking_id?`, `departure_id?`;
- lifecycle [R18]: `status planning|confirmed|cancelled`, `aa_sub_status held|on_request|declined|expired|null`
  (feed-driven, read-only);
- `confirmation_no`, `service_from`, `service_to`;
- `collect agency|on_arrival` [R25], `confirm_class` [R26];
- `visible_to_travelers` (auto false when cancelled) [R22];
- trash columns (blocked by the delete rule, §3.3).

`invoice` columns:
- `trip_id`, `kind deposit|balance|service_fee|adjustment` [R27];
- `currency`, `amount`, `amount_base` (FX block);
- `due_at`, `status draft|open|paid|void|expired`, `payer_traveler_id` (lead by default);
- C31 fields: `bk_hold_ids[]`, `pay_window_until` (= min of the hold expiries).

`payment` columns:
- `invoice_id`, `provider stripe|manual|vn_gateway`, `provider_ref` (PaymentIntent id);
- `amount`, `currency`;
- `received_at`, plus a frozen FX block with basis `receipt_date`;
- `status succeeded|failed|refunded|partially_refunded|disputed`, `refund_of?`.

`commission` columns:
- `booking_line_id`, `status expected|claimed|received|overdue|written_off|cancelled`, `due_at`;
- `expected`: amount + currency + frozen FX (basis `booking_date`);
- `received`: amount + currency + frozen FX (basis `receipt_date`);
- `fx_difference_base` (its own figure, never an "underpaid" flag [R17]).

### 2.8 Group G: communications (modules 5, 9; R14, R15, R24)

| Table | Key fields | Protection | Implements |
|---|---|---|---|
| `channel_account` | `kind gmail\|outlook\|twilio_sms\|twilio_whatsapp\|ses_platform`, `address_or_number`, `credential_id`, `status connected\|reconnect_needed\|disabled`, `last_token_check_at` | — | M:5, M:9; R24 |
| `ingest_address` | `local_part` (`<slug>-<random>`), `active`, `forwarding_confirmation_enc` | — | M:5 forward-in |
| `conversation` | `traveler_id?` (NULL = unmatched inbound), `trip_id?`, `channel email\|whatsapp\|sms\|messenger\|ig` (last two reserved, S7), `external_thread_ref`, `wa_window_expires_at` | — | M:5, M:9; S:§7 |
| `message` | See the column list below the table | `body_enc` F1-encrypted; rendered in a sandboxed iframe on an origin with no cookies (S10) | M:5, M:9; R24 |
| `saved_reply`, `message_template` | `locale`, `body`, `wa_template_name?`, `wa_status?`, `kind` | — | M:5, M:9 |
| `dispatch_queue` | `message_id`, `not_before`, `gate_result` (consent, archived, window, sender policy), `attempts` | The single choke point for every outbound send | R23, R24; M:10 |
| `campaign`, `campaign_recipient`, `unsubscribe_token` | `campaign.audience_rule`, `content_source agency\|aa_pack`; `recipient.traveler_id`, `status`; token hash | Only travellers with `consent.marketing = true`; one-click unsubscribe | R14; A:2.2 |
| `calendar_connection`, `meeting_slot` | `provider google\|microsoft`, `credential_id`; `slot.trip_id`, `starts_at`, `status` | — | R15 |

`message` columns:
- `conversation_id`, `direction in|out`;
- content: `subject_enc`, `body_enc`, `attachments[]` (document ids);
- `external_id` (UNIQUE per channel), `status queued|held_reconnect|sent|delivered|read|failed`;
- `sender_kind agency_mailbox|platform|system` [R24];
- `template_id?`, `ai_draft_id?`.

### 2.9 Group H: automation and AI (modules 10, 14; R5, R39, R41)

| Table | Key fields | Protection | Implements |
|---|---|---|---|
| `workflow_template` | `scope system\|agency`, `locale`, `steps jsonb` | — | M:10; R9 |
| `workflow_rule` | `trigger state\|stage_enter\|tag\|date_anchor`, `filter_tags[]`, `auto_apply bool` | — | M:10; R29, R30 |
| `workflow_run` | `rule_id`, `trip_id`, `status`, `coverage_gap bool` | — | R30 |
| `ai_draft` | See the column list below the table | Output is stored with placeholders, never restored at rest | M:14; R39, R40 |
| `placeholder_map` | `ai_draft_id`, `map_enc` (purpose `scrub`), `expires_at` (24 h) | Restored only in the agency session | M:F3 |
| `voice_profile` | `member_id`, `locale`, `channel email\|whatsapp`, `descriptors jsonb` (structured, no message text), at most 4 per member | — | R41 |
| `llm_call` | `stage`, `role`, `model`, `input_tokens`, `output_tokens`, `cost_usd_est`, `latency_ms`, `outcome`, `error_class`, `scrub_receipt jsonb` (entity counts, scrubber version) | **No text, no `traveler_token`** | D12 change; v2.1 §3.2 |
| `spend_budget` | `tenant_id`, `month`, `cap_usd`, `spent_usd`, `alerts_sent {75, 90, 100}` | Fail closed at 100 % | R5; D12 |

`ai_draft` columns:
- `trip_id`, `stage` (reply | proposal | follow_up | notes_to_options);
- `prompt_scrubbed` (placeholders only, kept 30 days), `output_scrubbed`;
- `status pending|approved|edited|discarded`, `edit_distance`;
- `feedback_code` (fixed list) [R39], `voice_profile_id`;
- `validation jsonb` (rule checks against Booking) [R39, R40].

### 2.10 Group I: ops hand-off, AA signals, insights (modules 8, 17; R37, R44)

| Table | Key fields | Protection | Implements |
|---|---|---|---|
| `ops_release` | See the column list below the table | `payload_enc` under purpose `ops_release`. Every read by AA ops is logged to the agency audit [A:3.9] | M:8; S:§8; A:3.9 |
| `supplier_manifest_export` | `ops_release_id`, `fields[]` (default name, pax, dietary/mobility; passport only if `supplier.requires_passport`), `exported_by`, `format pdf\|csv`, `watermark`, `at` | Audited; leaves the system (stated in the DPA) | A:3.10; M3 (review) |
| `incident_flag` | `departure_id`, `severity`, `message_code`, `received_at`, `resolved_at` | No identity: CRM maps the departure to its own trips | R37 |
| `insight_fact` (view for `crm_insights`) | `tenant_id`, `month`, `destination`, `product_key`, `budget_band`, `age_band`, `stage_reached`, `lost_reason_code`, `option_pick` | No identity, no token | M:17 |
| `insight_aggregate` | **No `tenant_id`.** Dimension tuple, `n_travelers`, `n_agencies`, `suppressed bool` | Cells published only when n ≥ 10 and agencies ≥ 3; opted-out tenants excluded | M:17; A:3.12 → N:3.12 |

`ops_release` columns:
- `trip_id`, `bk_booking_id`, `departure_id`;
- `released_at`, `released_by`;
- `payload_enc`, `fields_released[]`;
- `purge_at` (= trip end + 90 d), `purged_at`, `deletion_receipt jsonb`.

### 2.11 Group J: audit, deletion, portability, platform (F5, module 18; R21)

| Table | Key fields | Protection | Implements |
|---|---|---|---|
| `audit_event` | See the column list below the table | Partitioned by month; `crm_app` has INSERT and SELECT only; a trigger blocks UPDATE and DELETE; no PII (unit test) | M:F5; S2; A:3.8, A:3.9 |
| `audit_export_manifest` | `hour`, `s3_key`, `sha256`, `prev_sha256` | Chained manifest | S2 |
| `erasure_request` | `scope traveler\|tenant`, `subject_id`, `requested_by` (owner, or `aa-staff` request only), `confirmed_by` (owner), `dry_run_counts jsonb`, `executed_at`, `backup_purge_by`, `receipt jsonb` | Bypasses trash [R21] | M:18; A:3.7 |
| `export_job` | `requested_by`, `confirmed_by` (owner), `s3_key` (encrypted with DEK `export`), `expires_at` (7 d), `downloaded_at` | Only the owner downloads | M:18; A1 |
| `job` | ADR 0003a template, kinds `crm_*`; no RLS; payload = ids | — | D22 b |
| `outbox`, `inbox_events` | Ids only; inbox UNIQUE `(source, contract, idempotency_key)`; payload redacted after 90 d | — | ADR 0008 §3 step 7; DM-6.6 |
| `release_note` | `version`, `locale`, `body`, `published_at` | — | R42 |

`audit_event` columns:
- `event_id`, `at`;
- actor: `actor_kind user|traveler|ai_agent|aa_ops|aa_staff|support|breakglass|system`, `actor_ref` (random id only);
- what: `action`, `object_kind`, `object_id`, `fields[]`;
- why: `reason`, `request_id`.

### 2.12 Relations (summary)

```
tenant 1─1 tenant_settings ; tenant 1─* member ; tenant 1─* tenant_key(purpose)
traveler (F1) ─(profile_token_enc, encrypted)─▶ traveler_profile (F2)      -- no FK, no plaintext join
trip *─* traveler via trip_traveler (F1 side) ; trip *─* traveler_profile via trip_party (F2 side)
trip 1─* proposal 1─* proposal_day 1─* option_block 1─* option ; proposal 1─* selection
trip 1─* booking_line 1─1 booking_line_money ; booking_line 1─0..1 commission
trip 1─* invoice 1─* payment 1─* refund_request ; invoice ─(bk_hold_ids)─▶ Booking holds (soft)
trip 1─* task ; trip 1─* document ; trip 1─* signature_request 1─* signature_event
traveler 1─* conversation 1─* message ; traveler 1─* consent ; trip 1─0..1 ops_release
booking_line ─(bk_booking_id / departure_id, soft)─▶ Booking ; incident_flag(departure_id) ─▶ trips (by join)
```

### 2.13 Booking-owned additions (schema `booking`, `bk-NNN`, AA-Booking repo; no PII)

Booking owns all supply, price and departure data (ADR 0005 §1). The CRM needs the following, re-counted at 12–16
issues (v2.1 C1).

| Booking object | Key fields | Why |
|---|---|---|
| `b2b_partner` | `tenant_id` (soft key), `status`, `billing_currency`, `credit_terms_ref` (AA's current B2B terms [A2:1.2]), `m2m_client_id` | Tenant-scoped authorisation of B2B calls |
| `departure` | `trip_plan_id`, `start_date`, `capacity`, `held`, `sold`, `status scheduled\|guaranteed\|cancelled`, `auto_confirm bool` | Fixed departures confirm automatically; others are on request, confirmed by AA ops within 1 working day [A2:6.1]; R12 later |
| `b2b_quote` (+ lines) | `tenant_id`, lines (component, pax counts by age band, rooms), `currency`, FX lock, `price_hash`, `valid_until` | ADR 0005 decisions 5 and 9 (15 % B2B margin [A2:1.1]) |
| `b2b_hold` (+ lines) | `quote_id`, `tenant_id`, `expires_at`, `status active\|confirmed\|expired\|released`, `line_status available\|on_request` | C31 |
| B2B trip case | `trip_cases.channel = 'b2b'`, `party_tenant_id`, `customer_id` NULL allowed **only** when the channel is b2b (CHECK) | v2.1 K16 / C1: no traveller in `booking.customers` |
| `b2b_event` outbox | `hold.expired`, `line.confirmed`, `line.declined`, `booking.cancelled`, `departure.guaranteed`, `departure.incident` [R37], `departure.time_change` | Ledger auto-fill [M:6]; R18, R23, R37 |
| Cancellation policy | Per product / contract; returned on cancel | C12 |

---

## 3. Cross-cutting data rules (R17, R18, R21, R23, C12, C31)

### 3.1 FX rules [R17] (modules 6, 7, 13, 16, 17)

1. **Reporting currency.** Every tenant has `tenant_settings.base_currency`. Every money row stores the original amount
   + currency **and** the frozen base amount + FX block (§2.1).
2. **Which date's rate:**

   | Number | Rate date | Source priority |
   |---|---|---|
   | Sell, cost, expected commission of a line | The day the line becomes `confirmed` (`booking_date`) | AA lines: the Booking quote's FX lock (ADR 0005 decision 5), copied as `aa_quote_lock`. Agency lines: `fx_rate_override` of that day → `fx_rate_platform` of that day → the latest earlier day (flagged `stale_days`) |
   | Payment received, commission received | `received_at` date (`receipt_date`) | Same, minus the quote lock |
   | Proposal display currency | Quote time | The Booking quote; agency lines via platform rates |
   | Invoice | Issue date; the invoice currency is the quote currency (ADR 0005) | — |

3. **No drift.** A trigger refuses UPDATE of the FX block or `amount_base`. Reports read stored base amounts, never
   re-convert. A correction is a new row that supersedes the old one, and the audit records it.
4. **FX difference.** `commission.fx_difference_base = expected_base − received_base` when the original-currency
   amounts match. "Underpaid" is decided **in the original currency only**, so an FX move never raises a false
   underpaid flag [R17].
5. **Rate sources:**
   - ECB has no VND (R17 note);
   - proposed: `fx_rate_platform` filled daily by job `crm_fx_fetch` from ECB (EUR cross rates) + the State Bank of
     Vietnam central rate for VND (unverified source terms, open point);
   - Booking's approved `fx_rates` via `GET /booking/b2b/v1/fx-rates?date=` when Booking has rows (maker-checker,
     `bk-007`);
   - owner manual override always allowed;
   - Dev: synthetic rates.
6. **Insights** [M:17] aggregate base amounts converted once more to USD at month-end platform rates, and say so on the
   page.

### 3.2 Booking line status [R18] (modules 6, 13, 15, 16)

| Line kind | `planning` | `confirmed` | `cancelled` |
|---|---|---|---|
| AA (from the Booking feed, **read-only**) | `aa_sub_status` = `held` (with `expires_at`) or `on_request` | `line.confirmed` event | `hold.expired`, `line.declined`, `booking.cancelled` |
| Agency supplier | Agent creates | Agent sets; the required fields depend on `booking_validation_level` | Agent sets |

- **Validation levels for agency lines:**
  - `off`: nothing required;
  - `basic`: `confirmation_no` + `cost` + `sell` before `confirmed`;
  - `strict`: basic + commission + `confirmation_no` unique per supplier (partial unique index where
    `agency_supplier.confirmation_unique`).
- **Only `confirmed` counts.** Only `confirmed` lines count in margin, reports, insights and expected commission.
  `planning` shows as pipeline value; `cancelled` is excluded and auto-hidden from travellers [R22].
- **The assistant is never blocked.** An assistant who confirms a line without a commission creates an owner task
  "Add commission" instead of an error [R18].
- **Naming.** The word **Confirmed** is used (not "Booked"), so lines do not clash with the trip stage `booked` [R18].

### 3.3 Trash, delete block, archive [R21, R23]

- **One trash for every user-deletable object:**
  - covers trip, traveler, task, note, document, saved reply, template, agency supplier, workflow and tag;
  - `deleted_at` + `purge_after = deleted_at + tenant_settings.trash_days` (default **7 days**);
  - restore in the app by the owner or the deleting member;
  - job `crm_trash_purge` hard-deletes after the window (DM-7.2 batched, DRY RUN on its first run).
- **Delete is blocked when a trip has any of:**
  - a `succeeded` payment;
  - a signed `signature_request`;
  - a commission row in `received` or `claimed`;
  - an AA line in `held` or `confirmed`.

  The UI then turns "Delete" into **"Cancel trip"** (§3.4).
- **Restore** of a trip that had AA lines re-checks Booking first: holds may have expired, and lines go back as
  `cancelled` / `expired`.
- **Erasure bypasses trash.** A data-subject erasure (`erasure_request scope=traveler`) and an agency offboarding
  (`scope=tenant`) hard-delete at once, so the 30-day promise [A:3.7] is not lengthened by the trash window (R21 note).
- **Archive** [R23]:
  - `traveler.archived_at` + `archive_reason`;
  - hidden from lists, search and group sends;
  - every automated send is stopped **at the dispatcher** (`dispatch_queue.gate_result = archived`);
  - history kept.
- **Auto-archive and delete.** A traveler with no trip activity for the retention window (per tenant;
  `retention_overrides`, default 36 months (est., open point)) is auto-archived. The owner is then asked whether to
  delete. Archive never replaces a GDPR erasure.
- **Lost reasons** [R23]:
  - fixed codes: `price`, `price_aa_tour`, `aa_sold_out`, `aa_on_request_declined`, `dates_changed`, `went_elsewhere`,
    `no_response`, `trip_postponed`, `other`;
  - pre-selected from the Booking feed when the last AA event explains it (for example `hold.expired` after
    `sold_out`);
  - aggregated in module 17 (k ≥ 10).
- **No archived state for trips.** `lost` and `completed` already cover it [R23].

### 3.4 One-action trip cancellation [C12]

`POST /crm/v1/trips/{id}/cancel` with `dry_run=true` first. The preview lists every effect; the agent confirms.

1. **AA lines.** `POST /booking/b2b/v1/bookings/{id}/cancel` or `DELETE /holds/{id}`. Booking returns the cancellation
   fee per policy. The line becomes `cancelled` and the fee becomes a cost line.
2. **Agency lines.** One task per line, "Cancel with supplier" (the CRM cannot call third-party suppliers).
3. **Invoices.** Open invoices are voided. Open Stripe Checkout Sessions are expired (`checkout.sessions.expire`).
4. **Refunds.** The refund due under the agency's terms (`agreement_doc` in force at acceptance [R34]) creates
   `refund_request` rows in `proposed`. **An agent approves each one** before a Stripe refund is executed
   (`refunds.create` on the connected account). Manual and VN payments get a task.
5. **Commission.** Expected commission becomes `cancelled`, or stays if the supplier still pays.
6. **Ops data.** If an `ops_release` exists, it is revoked: purged now if the trip had not started, and AA ops get a
   notice. The purge is recorded in the audit.
7. **Workflows** for the trip stop. The trip moves to `cancelled` with `cancel_reason_code`, and the audit records the
   whole action.

### 3.5 Deposit link validity tied to the hold [C31]

- **The traveller's pay link** is a stable CRM URL (`go.<domain>/pay/<client_link>`), not a Stripe Payment Link.
- **On click**, the CRM checks that every `invoice.bk_hold_ids` hold is `active` (via Booking, cached ≤ 60 s). Then it
  creates a Stripe Checkout Session on the connected account with
  `expires_at = min(earliest hold expiry − 15 min, now + 24 h)`. Stripe's allowed range is 30 min to 24 h (unverified
  today); if less than 30 min is left, the page asks to re-check availability.
- **Hold expired before payment.** The page says "Availability must be re-checked". The agent gets a task; one tap
  re-quotes and re-holds [R26].
- **Race (Checkout completes after the hold expired).** The webhook handler tries to re-hold the same lines:
  - success → confirm as normal;
  - failure → mark the invoice `paid_unfulfillable`, create a `refund_request` (agent approves) and notify the agent.
- **The deposit page groups lines** by `confirm_class` and shows the hold expiry [R26]. A declined on-request line
  creates a task with two choices: swap the product or refund [R26].

---

## 4. Retention schedule (answers A:3.7, A:3.8, N:3.7, N:3.8; DM-7)

| Data | Window | Mechanism |
|---|---|---|
| Traveller F1 + F2, trips, money | Until the agency deletes it or offboards; auto-archive suggestion per tenant window | Owner-driven; erasure → hard delete |
| Erased data in backups | **≤ 30 days**: RDS automated backups ≤ 30 d, manual snapshots ≤ 30 d (including copies to other regions and AWS Backup), DEK store copies ≤ 30 d; prod never stopped (stopped instances can keep backups longer) | V1 rule + alarm on any snapshot holding `crm`; restore drill with a deleted synthetic agency. Fallback 90 days if this cannot be held [N:3.7] |
| Trash | 7 days (tenant setting) | `crm_trash_purge` |
| `audit_event` in the DB | 12 months viewable by the agency | Monthly partitions dropped after their export is verified |
| Audit archive | 12 months **compliance** + 6 years more **governance** (7 years total) | Two Object Lock buckets: `crm-<env>-audit-c` (compliance, default retention 12 months) and `crm-<env>-audit-g` (governance, 7 years). The hourly export writes the same object to both. Reason: an object version cannot move from compliance to governance, so two copies avoid any gap (est.). The agency can download its own copy [A:3.8]. Dev uses governance only until Ms. Thư's go-live |
| `ops_release` | Trip end + **90 days**, then purge + deletion receipt in the agency audit | `crm_ops_release_purge` [M:8] |
| `form_submission`, inbox / outbox payloads | 90 days (payload redacted, row kept) | DM-6.6 |
| `otp_challenge` | 24 h | Purge job |
| `placeholder_map` | 24 h | Purge job |
| `ai_draft.prompt_scrubbed` | 30 days (est.) | Purge job |
| `llm_call` | 180 days raw + daily rollup | ADR 0008 §7 parity |
| `job` | Succeeded 30 d, failed / cancelled 90 d | ADR 0008 §7 |
| Raw inbound mail (S3) | ≤ 1 day under the CRM ingest key, then re-encrypted under the tenant DEK and deleted | Lifecycle rule (M1 review) |
| `metric_daily` | 25 months | R28 year-over-year |
| Export files | 7 days | S3 lifecycle |
| CloudWatch app logs | 30 days, with a data-protection policy that masks PII | S18 (v2.1) |

DM-7.1 needs a retention row for each of these in the same PR that creates the table. DM-7.5 needs Nghiệp's approval of
the windows (X18).

---

## 5. Privacy implementation (F1–F5)

### 5.1 Keys and envelope encryption [S1, A:3.6, N:3.6]

- **One KMS key per environment.** `alias/crm-<env>/data` (symmetric), managed by Terraform. Its three-statement key
  policy:
  - *use*: the CRM task role, with the condition `kms:EncryptionContextKeys` ⊇ {`tenant_id`, `purpose`};
  - *administer*: the Terraform apply role, which has no Decrypt;
  - an explicit `Deny` for every other principal.

  No runtime `kms:CreateKey` and no `BypassPolicyLockoutSafetyCheck` (B2 removed).
- **Second key.** `alias/crm-<env>/ingest` for raw inbound mail and the hourly audit export. It is separate, so the
  ingest bucket never holds tenant-key material.
- **One DEK per tenant per purpose:**
  - purposes: `vault`, `docs`, `integration`, `scrub`, `ops_release`, `export`, `mail`;
  - `GenerateDataKey` with encryption context `{tenant_id, purpose}`;
  - the wrapped DEK is stored in `tenant_key`;
  - the unwrapped DEK is cached in process for about 5 minutes and never logged.
- **Field encryption.** AES-256-GCM from the `cryptography` library, with a 96-bit random nonce. The AAD binds the
  tenant, table, column and row id, so ciphertext cannot be swapped between rows or tenants. No home-made format.
- **Documents** are encrypted with the `docs` DEK before PUT (AAD = tenant + document id), then stored with S3 SSE-KMS
  (`data` key) as a second layer. Client-side encryption keeps crypto-shred per tenant. S3 Bucket Keys would otherwise
  replace a per-tenant encryption context with the bucket ARN (est.).
- **`KeyProvider` interface:** `get_dek(tenant, purpose)`, `rewrap(tenant, new_kek)`, `destroy(tenant)`. The DEK store
  is pluggable (Dev table → S3 at Go-real).
- **Contract test [N:3.6].** Re-wrap every DEK under a new KEK; all data stays readable without re-encrypting any row.
  This is the path to **BYOK later**: the agency's own KMS key wraps the DEK. It is a backlog item "when an agency asks"
  [A:3.6].
- **No per-traveller DEK** [S1]. Traveller erasure = hard delete + backups ≤ 30 days (§4), not crypto-shred.
- **Tenant offboarding:**
  - delete all rows;
  - mark `tenant_key.destroyed_at`;
  - delete the wrapped DEKs from the store;
  - remaining copies exist only in backups, which expire in ≤ 30 days.
- **Guards:**
  - EventBridge → SNS alarm on `PutKeyPolicy`, `CreateGrant`, `ScheduleKeyDeletion`, `DisableKey`, or `Decrypt` by any
    principal other than the task role and the break-glass role;
  - nightly `GetKeyPolicy` diff against Terraform;
  - a Decrypt-rate anomaly alarm (bulk reveal) [S1, v2.2 §7].

### 5.2 Blind indexes [S1, R6, R35]

- **Index key.** `K_idx = HKDF-SHA256(DEK_vault, salt = tenant_id, info = "bidx:" ‖ column)`. Each column gets its own
  derived key, so equal emails in two tenants give different indexes.
- **Index value.** `bidx = HMAC-SHA256(K_idx, normalise(value))`, truncated (CipherSweet style):
  - email and phone: 16 bytes (exact match, near-zero collision);
  - names: 4 bytes per token, so a token index is deliberately lossy and some false positives are filtered after
    decrypting (est. sizes).
- **Normalisation:**
  - email: trim + lowercase;
  - phone: E.164 via libphonenumber (default region = tenant country);
  - name: Unicode NFKD, strip diacritics (so "Nguyễn" = "Nguyen"), casefold, collapse spaces.

  `name_bidx` covers the full normalised name; `name_token_bidx[]` holds one value per token.
- **Uses:**
  - intake dedupe and the duplicate-merge screen [R6] (same DEK in a tenant, so merge needs no re-encryption);
  - inbound WhatsApp/SMS matching by `phone_bidx`;
  - global search Cmd/Ctrl+K [R35]: the query type is detected (`bk-` id, supplier conf no, E.164, email, name tokens)
    and personal values go through the index;
  - fuzzy partial-name search needs a security review before it ships (R35).
- **DEK rotation is not planned.** If it ever happens, a job recomputes the indexes. BYOK re-wrap does not change the
  DEK, so indexes stay valid.

### 5.3 F1 / F2 split and the encrypted link [M:F1, M:F2, S:§8]

- `traveler_profile.traveler_token` is a random UUID. The only link from F1 to F2 is
  `traveler.profile_token_enc`, encrypted under the tenant `vault` DEK. A DB reader, including the master user and
  `crm_ai_reader`, cannot join F2 rows to identities.
- **Trip party links are twins:** `trip_traveler` (F1, `crm_app` only) and `trip_party` (F2, readable by AI views).
  `crm_app` writes both in one transaction.
- **AI reads only views** under `SET LOCAL ROLE crm_ai_reader`:
  - `v_ai_trip_context`: trip bands, days, options, F2 profiles of `trip_party`;
  - that role has **no grant** on `traveler`, `traveler_health`, `trip_traveler`, `note`, `message`, `document`
    or `ops_release`. The DB enforces this (v1 §8.3).
- **Health** is stored as F1 codes with consent and mirrored to F2 `dietary_flags` / `mobility_flags`. The AI sees
  codes only [S:§5 rule 3, R40].
- **Stage 3 data** (passport, DOB, flights, emergency contact) is never part of any AI view or prompt (S6, v2.1).

### 5.4 PII filter before every LLM call [M:F3, D12, S6, T11]

- **Order** (v2.2 §4 "small adjustments"):
  1. **Known values.** Every identity value tied to the trip is replaced by numbered placeholders (`<PERSON_1>`,
     `<EMAIL_1>`, …):
     - traveller and companions: names, emails, phones;
     - emergency contact;
     - agency members' names;
     - supplier contact names.
  2. **Regex:**
     - email;
     - international + VN phone;
     - generic passport pattern; VN CCCD 12 digits;
     - dates of birth;
     - card numbers (Luhn);
     - signed-link URLs and OTP codes.
  3. **Bedrock Guardrails `ApplyGuardrail`** in **detect mode** (action `NONE`) on the remaining free text only. Our
     code numbers the placeholders. The `match` field is never logged (it contains the raw value; S6, K12).
- **Fail closed.** Any error or timeout → no LLM call; the draft shows "reply by hand".
- **Guardrails location:**
  - try acc2 first (raw text does not leave acc2);
  - if acc2 is blocked, the default is **stop**;
  - acc3 is allowed only with a CRM-only role (`AA3-Bedrock-Invoker-CRM`: `us.` profiles + `ApplyGuardrail` only).
    Acc3 is AWS, which is already on the sub-processor list [A:3.11] (v2.1 §2.1).
- **Placeholder map.** Encrypted with the `scrub` DEK, TTL 24 h. It is restored **only** in the agency user's session,
  when the draft is shown for approval.
- **Gateway checks, in order** (D12 change, v2.1 §3.2):
  1. `scrub_receipt`;
  2. `spend_budget` (fail closed at 100 %, alerts at 75 / 90 % [R5]);
  3. tenant `ai_enabled`;
  4. call the model;
  5. write `crm.llm_call` (no text).
- **Release gate.** A CI corpus of ≥ 200 EN/VI samples (including Vietnamese names and phone formats) must show 0
  leaks, about $0.70/month on Guardrails (v2 §7.3).
- **Writes need a human.** Rule checks against Booking (availability, unchanged net) run before a preview card is shown
  [R39]. `notes→options` [R40] can pick only from a closed list of Booking component ids for that day, and the server
  re-validates. Names come from the catalog, never from the LLM.

### 5.5 Tenancy and roles [M:F4, T9]

- **Membership.** CIS AA-813 membership (`tenant.membership.v1`) decides only "this person belongs to agency X". CRM
  writes `member.role`, from the owner's actions only. CIS removal invalidates the CRM cache within 60 s (v2.1 §2.1).
- **Request context.** `tenant_tx()` sets `app.tenant_id` and `app.member_role` with `set_config(..., true)` after
  checking membership in the same transaction. A lint forbids raw queries outside it (S11). Probe: an empty GUC
  returns 0 rows.
- **Margin protection:** column-level (`booking_line_money` RLS on role) plus API field filtering for the assistant.
- **Traveller side** [R22]:
  - per-person OTP with two levels: `lead` sees trip-level documents and itinerary; `companion` sees only their own
    forms and the shared itinerary;
  - passport fields are write-only (masked, e.g. "•••• 123");
  - documents show only when `visible_to_travelers`; cancelled lines are hidden;
  - the public router may call only `traveller_self_reveal(session)`, never generic `reveal()` (boundary test, S6).
- **Agency MFA** [A:3.13]: owner and agent must use a second factor (passkey or authenticator app). This conflicts
  with the EXTERNAL pool (X16). Dev keeps the `cis-portal` client with no MFA (synthetic data only). Go-real uses a
  partner pool with MFA required (T14, S12).

### 5.6 AA support access, three layers [A1, A:3.4, A:3.5, A:6.3, A2:6.2]

| Layer | Who / how | Can | Cannot | Logged |
|---|---|---|---|---|
| **L1 Platform console** (daily, no PII) | CIS admin screen "Agencies (CRM)" calls `crm.ops.v1`. Groups: `cis-admin` (read), `crm-platform-admin` (write) | Usage meters (seats, active users, storage, inbound mail count, AI cost, failed jobs, last activity); create agency; invite the **first** owner only while the agency has no owner and no travellers; lock / unlock; retry jobs; *allow* (not enable) features; request export or delete (owner confirms); start owner recovery: promote an existing member after **14 days**, every member emailed, anyone can cancel [A:6.3] | See trips, pipeline or revenue per agency (a response test forbids those keys); enable AI for an agency; invite a new email as owner | Every write → `audit_event actor_kind=aa_staff` in that agency's audit |
| **L2 Owner-granted support** | Owner enables "Allow AA support" in Settings: 1–7 days, default 24 h, read-only, F1 hidden unless the owner ticks it [A:3.5, N:3.5]. Staff use the AA-Partner staff host with a dedicated WORKFORCE client and group `crm-support`; one staff member at a time; ticket or reason required; banner in the agency UI | Read through `SET LOCAL ROLE crm_support_reader` (SELECT only, DB-enforced) | Send messages, export, change roles or integrations, change the support setting; `/crm/v1` never accepts `cis-admin` or `breakglass` tokens (negative tests) | Grant, extend, revoke, session start / end and every read |
| **L3 Break-glass** (security incident or legal order) | IAM role `crm-<env>-breakglass`, assumed only from the MFA admin role, ≤ 1 hour, `sts:TagSession tenant_id=<x>` required. The KMS policy allows Decrypt only when `kms:EncryptionContext:tenant_id = ${aws:PrincipalTag/tenant_id}`, so one agency at a time | Read that agency's data | Anything for a second agency in the same session | EventBridge → SNS to Nghiệp + a named non-engineer manager [A2:6.2]. Job `crm_kms_audit_ingest` writes CloudTrail Decrypt events into the agency's `audit_event` (`actor_kind=breakglass`). The owner is emailed within **24 hours** [A:3.4]. The reason goes to Linear |

**Module 8 AA ops** is a business flow, not a support layer:
- a `crm-ops` page in AA-Partner (T12) on a staff host, group `crm-ops`;
- reads `ops_release` only;
- each view → agency audit line "AA ops viewed trip X on date Y" [A:3.9];
- supplier manifest per [A:3.10].

### 5.7 Audit (F5) [S2, A:3.8, A:3.9]

- **What is logged:**
  - sign-ins, role changes, every **F1 field read** (`vault.reveal()` writes the event in the same transaction; if the
    write fails, the read fails);
  - exports, deletes, key operations;
  - AI context builds (`ai_agent`), AA ops reads, supplier manifest exports;
  - support session reads, break-glass Decrypts, L1 writes.
- **Volume control.** Bulk system jobs that read F1 (passport-expiry and birthday reminders [R2], age-band recompute
  [R32]) write **one event per job run per tenant**, with counts and field names. Name reveals in the "Where are my
  clients" view [R37] are click-to-reveal and logged one by one.
- **Export.** Hourly to both Object Lock buckets (§4), with a SHA-256 manifest that chains each hour to the last.
  Edits are possible only in a window of ≤ 1 hour.
- **Agency page.** The agency sees 12 months in the app and can download a copy [A:3.8]. No streaming to agency SIEMs
  (enterprise only, N:3.8).

### 5.8 Deletion and portability [M:18, A:3.7]

- **Erasure** (traveller or agency): the owner confirms → DRY RUN counts → hard delete across every `crm` table, the
  documents in S3 and the conversations.
- **Receipt.** It lists:
  - each deleted table count;
  - the `backup_purge_by` date (≤ 30 days);
  - copies outside AA's control: messages held in the agency's own Twilio / WABA / Gmail, supplier manifests already
    sent, a BoldSign copy if that fallback is active (deleted through its API).
- **Export.** Full CSV + JSON zip encrypted with the `export` DEK. Only the owner downloads it; the link expires in
  7 days; the export is audited.
- **Wording.** "Deleted at once in the app; not readable anywhere, including backups, within at most 30 days" [A:3.7],
  with the exceptions stated: the audit log (no PII) and accounting records [N:3.7].

---

## 6. Integrations

### 6.1 Service identity

- **Cognito M2M** on a separate pool `aa-m2m-<env>` [S5]:
  - one app client per caller (CRM; later others);
  - one resource server per API, with scopes such as `booking.b2b/read`, `booking.b2b/quote`, `booking.b2b/hold`,
    `booking.b2b/book`, `cis.catalog/read`, `cis.tenant/read`;
  - access tokens last 6 h and are cached in process (≈ $1/month incl. 1 secret, v2.2 §2 S5).
- **The receiver verifies** the JWT with the same JWKS code as user tokens and pins `client_id` + scope. CRM sends
  `X-AA-Tenant-Id` on every B2B call; Booking checks that `b2b_partner` is active for that tenant.
- **CIS → CRM** (`crm.ops.v1` reads): the signed-in staff member's WORKFORCE token is forwarded; CRM accepts
  `client_id=cis-admin` + group `cis-admin` (read) or `crm-platform-admin` (write) (T7, A1).
- ⚠️ **This contains underscore env vars — edit manually in VSCode** (Cognito M2M client config, DSNs). The agent
  generates no script for them.

### 6.2 AA-Booking B2B API `booking.b2b.v1` [S:§9 "AA inventory API", M:3, M:6, M:8]

The contract is OpenAPI in `docs/contracts/booking.b2b.v1.yaml` (root), written in W0. Base:
`https://api-booking.<domain>/booking/b2b/v1`, reached from CRM through the internal NLB (F5, v2.1).

| Endpoint | Purpose | Notes |
|---|---|---|
| `GET /products?updated_since=` | Sellable trip plans + components (hotels / room types, services) keyed by `(source_system, source_id)` and component ids, with `destination_id` | No price; content comes from CIS `catalog.http.v1` |
| `POST /quotes` | Lines (component, date, pax counts by age band, rooms) → per-line B2B net, `currency`, FX lock, `valid_until`, `price_hash`, `availability available\|on_request\|sold_out` | 15 % B2B rule (ADR 0005 decision 4, [A2:1.1]); reuses `pricing.service`. VND needs a Booking selling-currency change (X10) |
| `GET /departures?trip_plan=&from=&to=` | Fixed departures: capacity, held, sold, guaranteed | Fixed → auto-confirm [A2:6.1] |
| `POST /holds` | `quote_id` + lines → `hold_id`, `expires_at`, per-line status | Requires `Idempotency-Key`. Expiry is a Booking setting; proposed 48 h seats / on-request until ops answer + 24 h (est., Booking owner decides) |
| `POST /holds/{id}/extend` | Extend once if inventory allows | Used by C31 re-check |
| `DELETE /holds/{id}` | Release | Trip lost / cancel [C12] |
| `POST /holds/{id}/confirm` | → `bk_booking_id`; lines `confirmed` (fixed) or `on_request` (ops confirm within 1 working day) | Called after the deposit succeeds |
| `POST /bookings/{id}/cancel` | → cancellation fee per policy | C12 |
| `GET /events?after=<cursor>&limit=` | Feed: `hold.expired`, `line.confirmed`, `line.declined`, `booking.cancelled`, `departure.guaranteed`, `departure.incident`, `departure.time_change` | Pulled every minute by `crm_b2b_events_pull` into `crm.inbox_events` (idempotent) → ledger [R18], Lost reasons [R23], incident banner [R37], F2 history |
| `GET /fx-rates?date=` | Booking-approved rates | R17 source |
| `GET /price-parity?trip_plan=` | Public B2C "from" price | The CRM **warns, never blocks** when the agency sells below it [A2:1.3]; ADR 0005 decision 9 |

**Payload rules:**
- no name, email, phone, DOB or passport ever goes to Booking;
- pax = counts + age bands + room configuration;
- the trip case is B2B with `party_tenant_id`.

**Errors and outages:**

| Response | CRM behaviour |
|---|---|
| `409 price_changed` (new `price_hash`) | Re-quote prompt |
| `410 hold_expired` | Re-hold flow |
| `422 sold_out` | Option disabled; Lost-reason hint |
| `503` / timeout | Proposal shows "indicative price, confirmation pending"; holds and deposit links are disabled until Booking answers. Retry with backoff; never take a deposit without an active hold [C31] |

**Settlement.** AA → agency billing stays outside the CRM, under AA's current B2B terms [A2:1.2].

### 6.3 Stripe Connect Standard [M:7, A:4.5, D10 a]

- **Onboarding.** The owner connects their **own** Stripe account (OAuth / Account Links) → `payment_provider_account`.
  The agency is the merchant of record and pays Stripe fees; AA pays $0 and takes **no application fee** (free plan).
  Stripe now describes Standard through "controller properties"; the build must check the current API form
  (unverified).
- **Charges.** Direct charges on the connected account (`Stripe-Account` header). Checkout Sessions are created on
  demand (§3.5). There is no saved card / `setup_future_usage`, so no card-on-file and PCI stays out of scope [A:4.5].
- **Currencies.** AUD / USD / EUR and others the connected account supports. **Vietnam is not a Stripe country**, so VN
  agencies record payments manually (`provider=manual`); a VN gateway adapter comes later [A:4.6].
- **Webhooks** (Connect endpoint, signature-verified, inbox-idempotent on the Stripe event id):
  - `checkout.session.completed`, `checkout.session.expired`;
  - `payment_intent.succeeded`, `payment_intent.payment_failed`;
  - `charge.refunded`, `charge.dispute.created`;
  - `account.updated`, `account.application.deauthorized`.
- **Tenant mapping** uses `event.account` → `payment_provider_account`, never metadata alone (S19).
- **Refunds** are created only from an approved `refund_request` [C12, C31].
- **Dev.** A Stripe test-mode platform account, created by Nghiệp (B4 a).

### 6.4 WhatsApp and SMS through the agency's own Twilio [M:9, A:4.2 → N:4.2, A:4.3, A:4.4]

- **Primary path (one adapter for both channels):**
  - the owner enters their Twilio **Account SID** + **Auth Token** (needed: Twilio signs webhooks with the account Auth
    Token; API keys cannot validate) + an optional API key for sending;
  - stored as `integration_credential` under the `integration` DEK;
  - the agency registers its WhatsApp sender through Twilio Self Sign-up; the WABA belongs to the agency;
  - Twilio and Meta bill the agency; AA $0 [A:4.4].
- **Webhooks.** `POST /crm/hooks/twilio/<hook_id>` (opaque per-tenant id). The `X-Twilio-Signature` HMAC is verified with
  that tenant's auth token **before** anything is stored (S6, v2.2). Status callbacks update `message.status`.
- **Inbound matching:**
  - by `phone_bidx` → `traveler`;
  - no match → "Unmatched" conversation queue (spec §11.2 edge case);
  - the opt-in state is tracked per conversation.
- **24-hour window.** `conversation.wa_window_expires_at = last_inbound + 24 h`. Outside it, the dispatcher allows only
  approved templates (`message_template.wa_status = approved`) and blocks free text.
- **Auth token risk.** The token gives full control of the agency's Twilio account. Mitigations:
  - decrypted only in the hook and dispatcher paths;
  - never shown back;
  - rotation guidance (Twilio secondary token);
  - an alarm on decrypt spikes.
- **Fallback if Twilio requires ISVs to be Meta Tech Providers** [N:4.2]. Twilio's self sign-up page says "must join";
  the ISV page says "can join". This must be asked before module 9 (open point). In that case:
  - AA joins Meta's Tech Provider programme via Twilio (3–4 weeks);
  - each agency gets a **Twilio subaccount under AA**, with the cost re-billed to the agency;
  - Twilio then becomes an **AA sub-processor** (§7).
- **Messenger and Instagram** stay in the channel enum; they are built after the 23 modules [A:4.3, S7].
- **Dev.** Twilio trial / test credentials of a synthetic agency.

### 6.5 Email: send-as Gmail / Outlook + forward-in [M:5, A2:4.1, N:4.8, R24]

- **Send.** A message leaves from the agency's own mailbox, so it sits in their Sent folder:
  - Gmail: OAuth scope `gmail.send` only (*Sensitive*: Google verification, **no CASA**; K21);
  - Outlook: Microsoft Graph delegated `Mail.Send` + `offline_access`, built **together with Gmail** [N:4.8];
  - refresh tokens are stored as `integration_credential`;
  - on Dev the Google app is in "Testing", so refresh tokens expire after 7 days and synthetic agencies re-consent
    weekly (M1).
- **Receive.**
  - One SES receipt rule for the whole domain `in.<neutral-domain>`; per-agency addresses
    `<slug>-<random>@in.<domain>` (`ingest_address`). One rule avoids the 200-rules limit (T6, K13).
  - SES → S3 bucket under the `ingest` key with a 1-day lifecycle.
  - Job `crm_mail_ingest`:
    1. maps the address to a tenant;
    2. re-encrypts the message under the tenant `mail` / `vault` DEK;
    3. threads it by `Message-ID` / `In-Reply-To` / `References` and a per-trip Reply-To tag;
    4. deletes the raw copy;
    5. writes the audit row.
  - The agency sets auto-forwarding or BCC. The UI shows Gmail's forwarding confirmation code (captured by ingest).
  - Microsoft 365 may block automatic external forwarding by default; the fallback is BCC or a mail-flow rule (the
    help page says so).
- **No two-way sync.** Spec module 5 wording changes (A2:4.1; X8).
- **Sender table [R24]:**
  - generated from the dispatcher code;
  - every send is `agency_mailbox` (client mail), `platform` (system mail to travellers: OTP, pay reminders, in the
    agency's name via a neutral domain) or `system` (to agents);
  - the help page renders the table.
- **Dead token [R24].** Client mail is held in `held_reconnect`, a red banner shows, the owner is emailed, and a
  nightly token check runs. **No silent fallback** to the platform sender unless `allow_platform_sender = true`.
- **Domain [A:2.6].** A neutral product domain for traveller pages and platform mail; optional per-agency custom
  domain (CloudFront alternate name + ACM + agency CNAME, and per-agency SES DKIM identity at Go-real). Client mail
  always goes from the agency mailbox.

### 6.6 SES (system mail and campaigns)

| Item | Detail |
|---|---|
| Configuration set `crm-transactional` | OTP, deposit and Stage 3 nudges, the morning digest to agents (no PII in the digest body: counts + links [R20]), new-inquiry alert to the agent (L2, review) |
| Configuration set `crm-marketing` | Campaigns [R14, A:2.2]: only `consent.marketing = true`, `List-Unsubscribe` + one-click POST, sent in the agency's name (agency domain DKIM if set up, otherwise "<Agency> via <neutral domain>"), with AA-prepared content the agency can pick. A separate set protects transactional reputation (S19) |
| Feedback | Bounces and complaints via SNS → `crm_ses_feedback` → per-tenant suppression; complaint rate alarm |
| Go-real | One SES tenant per agency on the sending side (v2.2 §4) |
| Note | **AA never sends to an agency's travellers on its own behalf** (spec §2) |

### 6.7 E-sign: self-built, BoldSign fallback [M:12, A:4.1, A2:5.1, S3]

- **Self-built flow** (provider `self`):
  1. per-person OTP by email [R22];
  2. show the documents (`agreement_doc` versions + hashes);
  3. typed full name + explicit consent tick per document;
  4. capture IP / UA (hashed in the event table, raw kept inside the sealed certificate);
  5. render the PDF on the server (terms + trekking waiver + **insurance declination** in one signing envelope);
  6. append an audit certificate page;
  7. compute SHA-256 and apply a PAdES signature with a KMS **asymmetric** sealing key (`alias/crm-<env>/seal`,
     ≈ $1/month + per-request cost, est.);
  8. store the PDF as `document kind=waiver_pdf`, encrypted with the `docs` DEK;
  9. append-only `signature_event` rows.
- **Known limit.** A self-signed seal may show "validity unknown" in Adobe Reader (v2.2 Q6, est.). The insurer
  question [A2:5.1] decides whether this is acceptable.
- **Provider-neutral `esign.*` adapter:**
  - `create_request`, `get_status`, `download_signed`, `delete`, webhook `signed|declined|expired`;
  - Dev and CI use a **stub** [S3];
  - Documenso is dropped [A:4.1, N:4.1].
- **BoldSign fallback** (if the insurer requires a named provider; 2–3 issues, from $30/month incl. 40 envelopes +
  $0.75 each, [A2:5.1]):
  - embedded signing;
  - signed PDF copied into our storage;
  - the provider copy deleted through its API (M2 review);
  - BoldSign becomes a sub-processor (§7); the region choice (US / EU / AU) is checked when it is turned on
    (unverified).

### 6.8 Insurance waiver / declination [A2:5.1, A:5.2, R13]

- **Stage 3** "travel insurance" item: `has_policy yes|no`.
  - Yes: insurer name + policy number + emergency hotline, encrypted in F1 (`traveler_insurance` columns on
    `trip_traveler`, `pii:government_id`-adjacent; est. class `travel`).
  - No: the **"I decline travel insurance"** clause becomes part of the signed waiver envelope (§6.7).
- **F2** gets only an `insured bool` flag. The ops release includes the insurer + hotline only when the traveller is
  insured. The policy number is included only when a supplier requires it (est., to confirm with ops).
- **Later hook.** In-app insurance quotes with commission to the agency [A:5.2] come after the 23 modules. Data hook:
  `booking_line.supplier_kind = agency` with `category = insurance`; no schema change needed.

### 6.9 CIS contracts (CRM as consumer)

| Contract | Use |
|---|---|
| `tenant.membership.v1` | Snapshot + ETag + invalidation on removal (AA-813) |
| `tenant.entitlements.v1` | Plan, features allowed, seats [R11] |
| `catalog.http.v1` | Tour content, days, places, photos, `exclusions` (suggests `collect=on_arrival` lines [R25]), activity / intensity facets (system tags [R29]), prep packs [R38] and AA template content [R9]; all **written in CIS** (ADR 0002) |

CRM publishes `crm.ops.v1` (job summary, LLM usage, usage meters, L1 writes) and `crm.insights.v1` (aggregates only).

### 6.10 Calendar (R15), flights (R44), offline itinerary (R16)

- **R15** call booking in the intake form + calendar sync:
  - Google Calendar `calendar.events` (believed *Sensitive*, not Restricted, so no CASA; **unverified**) and Graph
    `Calendars.ReadWrite`;
  - only busy / free and the CRM-created event are written;
  - the event title holds no traveller PII beyond a first name the agent chooses (est.).
- **R44 step 1** [A:2.5]: task `T−48h` "confirm arrival flight" with a status link built from `traveler_flight`
  ($0). A paid flight-status API only after ops report a real missed pickup, with the price approved first. Then it is
  added to §7. Notices go only to the agency and AA ops, never to the traveller.
- **R16** PWA offline itinerary:
  - the service worker caches only the itinerary (days, times, places, agency contact) for the signed-in person;
  - **never** F1 Stage 3 data or documents marked `write_only`;
  - the cache is cleared at sign-out and when the link expires;
  - no push notifications in the first version (est.).

---

## 7. Sub-processor list (draft for the DPA and the public data page [A:3.11, A:3.14, N:3.11])

**AA's sub-processors for agency CRM data** (company + purpose; no account ids):

| Company | Purpose | Region | Condition |
|---|---|---|---|
| Amazon Web Services, Inc. | Hosting (compute, database, storage, keys, email, CDN, identity) and AI (Bedrock, incl. Guardrails) | US (us-west-1) | Always. AI only when the agency enables it. Anthropic is not listed separately (model runs inside Bedrock) [N:3.11] |
| Mapbox, Inc. | Map display in the builder and the traveller proposal page (receives viewer IP and map area; no CRM records) | US | Always (est., confirm it belongs on the list) |
| Twilio Inc. | Messaging, **only** in the Tech Provider fallback where AA owns the subaccounts | US | Conditional (§6.4) |
| BoldSign (Syncfusion, Inc.) | E-signature, **only** if the insurer requires a named provider | US / EU / AU (check) | Conditional (§6.7) |
| Flight-status API vendor | R44 step 2 | — | Conditional, after price approval |
| Error monitoring (e.g. Sentry) | Errors with PII scrubbed | — | Only if enabled in AA-Partner; none today on the portal |

**Open technical check [N:3.11]:** do TrueIDC (acc2 reseller) and eCloudvalley (acc3 reseller) hold IAM roles inside
the accounts? If yes, list them or remove the access.

**The agency's own processors (contracted by the agency, not AA's sub-processors):**
- Stripe (Connect Standard account);
- Twilio and Meta (own account / WABA);
- Google / Microsoft (own mailbox);
- a VN payment gateway later.

The UI and DPA say AA does not control deletion there.

**Not used by the CRM:** OpenAI, Jev, Documenso, 360dialog.

**Public data page:** the promise text, this list, deletion windows, log retention, "AWS holds ISO 27001 / SOC 2 (AWS's
certificates, not AA's)" [N:3.14]. Changes are announced 30 days in advance [N:3.11].

---

## 8. Spec coverage (23 modules) by this lane

| Spec | Data / privacy / integration element |
|---|---|
| F1 | §2.3, §5.1–5.3; R22 traveller side |
| F2 | §2.4, §5.3; `trip_party` |
| F3 | §5.4; `placeholder_map`, `llm_call.scrub_receipt` |
| F4 | §1, §5.5, §5.6; `member`, roles, RLS |
| F5 | §2.11 `audit_event`, §5.7, §4 |
| 1 | `intake_form`, `form_definition`, `form_submission`, blind-index dedupe, agent alert (SES) |
| 2 | `trip` + transitions, `task`, `note`, `tag`, `waiting_on` |
| 3 | proposal group §2.6 + `booking.b2b.v1` quotes / holds / departures |
| 4 | Same proposal data + shared `price_hash`; `message_template` |
| 5 | §6.5, communications group |
| 6 | `booking_line(_money)`, R18 rules, B2B events auto-fill |
| 7 | invoices / payments, §6.3, C31 |
| 8 | `ops_release`, `supplier_manifest_export`, 90-day purge, A:3.9 / 3.10 |
| 9 | §6.4 |
| 10 | workflow tables, `dispatch_queue`, task due rules |
| 11 | `client_link`, `traveler_access`, `otp_challenge`, `document.visible_to_travelers`, PWA rules |
| 12 | Agreements group, §6.7, §6.8 |
| 13 | `commission` + R17 FX |
| 14 | §5.4, `ai_draft`, `voice_profile`, `spend_budget` |
| 15 | `agency_supplier` (AA built-in row) |
| 16 | `metric_event` / `metric_daily`, frozen base amounts |
| 17 | `insight_fact` → `insight_aggregate` (n ≥ 10, ≥ 3 agencies, opt-out) |
| 18 | `export_job`, `erasure_request`, §5.8 |

---

## 9. Approved items: coverage

Every item below is approved. "Covered" means this document defines the data, privacy or integration element. UI
details belong to the UX lane.

| Item | Covered by |
|---|---|
| R1 waiting-on + bulk by stage | `trip.waiting_on` (derived from the last inbound / outbound / AA event); bulk stage change writes `trip_stage_history` per trip |
| R2 special dates | Nightly `crm_reminder_scan` reads F1 passport expiry (default 200 days) / DOB under the system actor (one audit event per run); birthday sends gated on `consent.marketing` |
| R3 tags + tag workflows | `tag`, `tag_link`, `workflow_rule.trigger=tag`, bulk-apply preview count |
| R4 proposal viewed | `metric_event proposal.viewed` from `client_link` open; nudge rule |
| R5 AI meter | `spend_budget` alerts at 75 / 90 / 100 % |
| R6 merge duplicates + staged import | Blind-index dedupe; merge under the same tenant DEK; import order traveler → relation → trip → note via job |
| R7 relations + multi-companion intake | `traveler_relation` (inverse pair), `trip_traveler` rows from one form |
| R8 clients belong to the agency | `traveler.owner_member_id`; reassignment by the owner only; members cannot hard-delete (trash + owner restore) |
| R9 template library + AA content | `workflow_template`, `message_template`, AA packs via `catalog.http.v1` |
| R10 AI reads supplier confirmations | Forward to the ingest address → F3 → suggested `booking_line`; accept writes; passport images never sent |
| R11 tiers (free now) | `tenant_entitlement` mirror; AI fair-use; A:1.1 thresholds are business data |
| R12 group tours (after 23 modules) | Hook: Booking `departure` / allotment + `trip.group_departure_ref` |
| R13 insurance | Declination in the waiver now (§6.8); quote / commission hook later |
| R14 campaigns | `campaign*`, `unsubscribe_token`, `crm-marketing` config set, consent gate |
| R15 call booking + calendar sync (add now) | `calendar_connection`, `meeting_slot`, §6.10 |
| R16 PWA offline (add now) | §6.10 cache rules |
| R17 FX rules | §3.1, frozen FX block |
| R18 line status | §3.2 |
| R19 selection diff | `selection` history + `option.sell_delta` / `net_delta`; batched notification; the email carries no F1 |
| R20 task due by departure | `task.due_anchor` / `due_offset_days` / `due_at` NULL bucket, `due_overridden`; PII-free morning digest |
| R21 trash + delete block | §3.3 |
| R22 per-person traveller access | `traveler_access`, per-person OTP, write-only passport, `visible_to_travelers` |
| R23 archive + Lost reasons | §3.3 |
| R24 sender table + dead token rule | §6.5, `message.sender_kind`, `held_reconnect` |
| R25 collect on arrival | `booking_line.collect`; excluded from pay link / reminders / commission; suggested from CIS `exclusions` |
| R26 deposit page grouping | `option.confirm_class`, hold expiry shown, decline → task |
| R27 service-fee invoice | `invoice.kind = service_fee`, excluded from trip margin; `tenant_settings.service_fee_enabled` default off |
| R28 KPI tiles year-over-year | `metric_daily` 25 months; computed on page open, no per-tenant CloudWatch metric (V2) |
| R29 auto-apply by trip type | System tags from the CIS catalog; T−21 waiver alert |
| R30 workflow coverage report | `workflow_run.coverage_gap` + query; state rules re-evaluated every tick |
| R31 conditional forms | `form_definition` branches; the server drops hidden answers; health questions after consent |
| R32 locale dates + age band | F2 `age_band_at_departure`, recomputed only on change; DOB stays in F1 |
| R33 per-day timezone | `proposal_day.tz`, `traveler_flight` structured; late-arrival warning |
| R34 versioned terms | `agreement_doc`, `terms_acceptance` with `price_hash` + hold ids |
| R35 global search | §5.2 query classification + blind indexes |
| R36 ready to travel again | Rules over F2 + `profile_history`; send gate on marketing consent; AA never contacts |
| R37 where are my clients + incident flag | `incident_flag` from `departure.incident`; names hidden until clicked (F5 per reveal) |
| R38 pre-travel section | `proposal_day.day_no = 0`, `prep_pack_selection`, content in CIS; visa = official links only [A:2.3] |
| R39 AI guardrails | Rule checks against Booking, `feedback_code` fixed list, aggregates k ≥ 10 |
| R40 notes → option blocks | Closed id list, server re-validation, catalog names, health → codes |
| R41 voice profile | `voice_profile` (structured, ≤ 4 per member, opt-in) |
| R42 release notes / preview | `release_note`, `tenant_settings.release_channel`; privacy and price logic never behind a flag |
| R43 support model | L1 / L2 with read-only grants; the agency runs its own import; the help bot reads help pages only, through F3, no vector DB [A2:2.1] |
| R44 flight time changes | Step 1 task + `traveler_flight`; step 2 gated (§6.10) |
| C12 trip cancellation | §3.4 |
| C31 deposit link vs hold | §3.5 |

---

## 10. Contradictions and gaps between the inputs

| # | Contradiction / gap | Where | Resolution in this design | Who decides |
|---|---|---|---|---|
| X1 | The spec path `v2.1/partner-crm-spec.md` and v2.2 under `v2.1/` do not exist. Real files: `docs/research/partner-crm-spec.md`, `.tmp-session/s245-r2/r4/crm-v2.2-simplified.md` (gitignored) | Task inputs; reply-to-notes "Việc cần anh để ý" | Used the real files; copy v2.2 into `docs/audits/` in the root PR | Agent |
| X2 | ADR 0008 §8 and DM-6.8 say the CRM "is a CIS module". The owner decided on a separate app (AA-Partner) | ADR 0008, standards Part B | Separate app; ADR 0008a amendment + a new ADR for AA-Partner (CRM-01) | Nghiệp (ADR) — **blocks the first migration** |
| X3 | ADR 0008 §3 step 9 and §5 ("LLM calls through the Model Gateway into `shared.llm_call_log`") vs D12 change (own gateway, `crm.llm_call`, CIS reads over HTTP) | ADR 0008; owner-approvals r2 | Own gateway; amend step 9 for apps that must not grant into `shared` | Nghiệp |
| X4 | ADR 0008 step 8 ("no password, OTP or session tables") + ADR 0006 (travellers in the EXTERNAL pool) vs the CRM's own traveller OTP and links (spec module 11, R22) | ADR 0006/0008 vs spec | Agency travellers must **not** be in AA's EXTERNAL pool: it is AA-controlled and shared with TripPlanner/Booking, which would make AA a controller and break spec §2. The CRM keeps its own hashed OTP and link tables (DM-6.9). Record as an exception in ADR 0008a | Nghiệp |
| X5 | DM-6.8: "a hand-off to AA … Booking creates its **own** customer" vs module 8 design (data stays in CRM under the `ops_release` DEK, read in AA-Partner, T12) | Standards vs v2 / v2.1 | Keep T12: Booking receives pax counts only; ops PII stays in CRM and is purged at +90 days, verifiable [M:8]. Amend DM-6.8 | Nghiệp |
| X6 | Spec §8 "AA … never contact details" vs ground ops needing an emergency contact, and A:3.10 (manifest to hotels) | Spec vs ops reality | Default `ops_release` fields exclude contact details and the emergency contact; the agency is the emergency channel (R37). A per-trip toggle with `consent.ops_release` could add the emergency contact: open point | Ms. Thư |
| X7 | 3.12: A:3.12 chose **a** (opt-in) and D24 = opt-in, but reply-to-notes switched to default + opt-out (k ≥ 10 + ≥ 3 agencies) | answers.md vs reply-to-notes | Opt-out, per the later notes (no v2 question) | Confirm with Nghiệp |
| X8 | Spec module 5 "two-way Gmail/Outlook sync" vs forward-in + send-as | Spec vs A2:4.1 | Forward-in; reword module 5 | Ms. Thư (treated as decided) |
| X9 | A:4.2 = a (direct Meta, D9 a) and A:4.8 = a (Outlook later) were reversed by reply-to-notes to Twilio-per-agency and Outlook with Gmail; neither went to v2 | answers vs reply-to-notes | Followed the notes, as the task says | Confirm with Nghiệp |
| X10 | Booking selling currencies {USD, EUR, GBP, AUD, SGD} (ADR 0005, `engine.py`) lack **VND**, which spec §11.6 needs; ECB has no VND | ADR 0005 vs spec | Booking adds VND selling / quote currency; CRM gets VND from another source (§3.1) | Booking lane |
| X11 | ADR 0005 decision 9: "a tenant **may not** advertise below the from price" and "a second revenue line next to the subscription" vs A2:1.3 (warn, don't block) and A:1.1 (free) | ADR 0005 vs answers | Warn only; contract clause. Amend ADR 0005 decision 9 wording | Nghiệp |
| X12 | R38 / R9: AA-written prep packs and templates are **content**; ADR 0002 says only CIS writes content | Ideas vs ADR 0002 | Author in CIS, deliver via `catalog.http.v1`; agency edits live in `crm` | — |
| X13 | Spec F1 "encrypted with the agency's own key" + §8 "agency-held keys" vs S1 (one key per env + per-agency DEK) | Spec vs v2.2 | Reword per A2:3.3 a; BYOK later via `KeyProvider.rewrap` | Ms. Thư (treated as decided) |
| X14 | S1 removed the per-traveller DEK, but the v1 DPA text says "DEK per traveller enables per-person crypto-shred" | v1 §14 vs S1 | Per-person erasure = delete + ≤ 30-day backups; fix the DPA draft | Agent (DPA draft) |
| X15 | e-sign: D11 b / N8 b (Documenso) vs A:4.1 (self-built, BoldSign fallback, Documenso dropped) | v2 vs answers | Self-built; stub on Dev | — |
| X16 | A:3.13 mandatory MFA (passkey / TOTP) for owner/agent vs ADR 0006 decision 1 (EXTERNAL MFA **off**, because TOTP locks out email-OTP-first users; changing it affects travellers) | Answers vs ADR 0006 | Partner pool split (ADR 0006 "alternative kept open") at Go-real with MFA required; Dev stays on `cis-portal` | Nghiệp (ADR 0006 amendment) — **blocks real agencies** |
| X17 | DM-6.1 has no `pii:` classes for passport/ID, health or emergency contact | Standards vs v1 §8.2 plan | Add `government_id`, `health`, `emergency_contact` (standards v1.x bump) | Nghiệp |
| X18 | DM-7 retention table has no CRM rows; A:3.8 "6 more years" and A:3.7 "30 days" need DM-7.5 approval | Standards | Add the §4 rows in the CRM-06 PR | Nghiệp |
| X19 | A:3.8 wants "locked, not editable" for 7 years, but N:3.8 uses compliance 12 months then governance (one object cannot change mode) | Notes vs S3 mechanics | Two buckets (§4) | — |
| X20 | The spec pipeline has no post-booking cancellation (only Lost before Booked) vs C12 | Spec §4 | Add terminal `cancelled`; record as a spec deviation | Ms. Thư (wording) |
| X21 | v2.2 decisions S1–S7, A1, V1–V3: no recorded owner click found in the repo (the session log lists v2.2 as "for Nghiệp and Ms. Thư to read") | S245 log | Treated as approved per the task statement and because reply-to-notes builds on S1/S7 | Confirm with Nghiệp |
| X22 | Spec "Booking.status" has no lifecycle; R18 adds `planning/confirmed/cancelled` while Booking has its own 13 trip-case statuses | Spec vs Booking | CRM line status is separate; AA lines map Booking events → R18 states (§3.2) | — |
| X23 | Twilio ISV rules: "must join" vs "can join" Meta's Tech Provider programme | N:4.2 | Primary path + fallback (§6.4); ask Twilio before module 9 | Nghiệp (vendor question) |
| X24 | v2 §7.3 / v1 planned acc3 Guardrails as fallback; v2.1 S6 says stop by default unless a CRM role exists and acc3 is a listed sub-processor; A:3.11 lists AWS only | v2 vs v2.1 | Default stop; acc3 allowed with a CRM-only role (both AWS) | — |

---

## 11. Cost notes for elements added here (Dev, monthly; est.)

| Item | Cost |
|---|---|
| KMS: `data`, `ingest`, `seal` (asymmetric) | ≈ $3 + requests (cents) |
| Cognito M2M | ≈ $1 (v2.2) |
| Two Object Lock buckets, hourly export | Cents |
| Guardrails corpus gate | ≈ $0.70 |
| FX fetch, events pull, purge jobs | $0 extra (in-process runner) |
| Stripe, Twilio, Gmail, Outlook, SES on Dev | $0 (test modes; SES pennies) |
| BoldSign / flight API | $0 until a conditional switch-on (§7) |

**Total added by this lane:** ≈ $4–5/month on top of the v2.2 Dev figure (est.).
