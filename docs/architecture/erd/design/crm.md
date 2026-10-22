---
id: APP-04-erd-design-crm
title: "ERD design: crm schema (planned)"
description: "Hand-written design ERD of the planned crm schema of AA-Partner (88 tables and one view in ten groups), reviewed before the first crm migration and compared with the live dump by the drift check."
type: reference
status: draft
owner: nghiep
audience: [engineer, agent]
applies_to: [aa-cis-dev-db, aa-partner]
last_reviewed: 2026-10-22
review_every_days: 30
generated: false
related: [APP-04, APP-04-erd, APP-04-erd-design, APP-10-partner-crm, AA-894, AA-932]
---

# ERD design: crm schema (planned)

<!-- erd-design schema=crm enforce=false implied-fk=tenant_id:tenant -->

Design ERD of schema `crm`, owned by AA-Partner (migrations `crm-NNN`, byte copy in AA-CIS-Infra
`db/migrations/crm/`). Nothing of it is live yet: AA-932 creates the schema and the roles; the first tables come
with `crm-001` (base template, AA-933) and the slices after it. This page is the diagram the migration PRs are
reviewed against. After every DB Migrate apply, the drift check of the DB Schema Dump workflow compares it with the
live catalog (see [design ERDs](README.md)).

Sources, in order of precedence:

1. [CRM final design §5](../../../audits/2026-10-21-S246-crm-design-v3/final/crm-design-final.md#5-data-model-and-privacy-f1f5)
   and its [errata S247](../../../audits/2026-10-21-S246-crm-design-v3/final/errata-s247-byo.md) (bring-your-own
   integrations).
2. [Design v3 §3.3](../../../audits/2026-10-21-S246-crm-design-v3/design-v3.md#33-tables-about-76-in-11-groups-full-columns-in-data-privacy-integrationsmd-2-unless-changed-here)
   (the table list) and the column lists in the
   [data and privacy lane §2](../../../audits/2026-10-21-S246-crm-design-v3/lanes/data-privacy-integrations.md#2-data-model-schema-crm).
3. The `crm.*` retention rows of [data standards DM-7](../../data-standards/02-data-management.md) (88 table names).

## How to read this page

- **Keys only.** Each box shows the primary key (`PK`), the foreign keys (`FK`), single-column unique keys (`UK`) and
  the column that names the state (`stage`, `status`). Full columns stay in the lane §2. Attribute comments are the
  DM-6.1 tags the column will carry.
- **Edges.** The parent is on the left, the child on the right. The label is the child's FK column list, so the
  drift check can compare it with the live `FOREIGN KEY` columns. `|o` marks a nullable FK.
- **The tenant edge is implied.** Every box with a `tenant_id ... FK` attribute has an FK `tenant_id` to `tenant`
  (the marker comment under the title says so). Drawing about 80 such lines would hide everything else.
- **One box per table.** A table has its attribute block in exactly one diagram. A bare name in another diagram is
  a reference to that box.
- **Not drawn:** soft keys to other apps (`bk_hold_id`, `bk_booking_id`, `departure_id`, `aa_component_ref`,
  `cis_pack_id`, CIS place ids), which are text ids under DM-4.2, and the Booking-owned objects (`b2b_*`,
  `departure`), which are Booking's design ([final design §5.3](../../../audits/2026-10-21-S246-crm-design-v3/final/crm-design-final.md#53-booking-owned-additions-aa-booking-bk-nnn-no-pii)).

## Overview: the trip is the folder

The core path from an agency to money and messages. Boxes are defined in the group diagrams below.

```mermaid
erDiagram
    tenant ||--o{ member : "tenant_id"
    member |o--o{ trip : "owner_member_id"
    trip ||--o{ trip_traveler : "trip_id"
    traveler ||--o{ trip_traveler : "traveler_id"
    trip ||--o{ trip_party : "trip_id"
    traveler_profile ||--o{ trip_party : "traveler_token"
    trip ||--o{ proposal : "trip_id"
    trip ||--o{ booking_line : "trip_id"
    trip ||--o{ invoice : "trip_id"
    invoice ||--o{ payment : "invoice_id"
    traveler |o--o{ conversation : "traveler_id"
    conversation ||--o{ message : "conversation_id"
    trip ||--o| ops_release : "trip_id"
```

`traveler` (F1, identity) and `traveler_profile` (F2, pseudonymous) have **no FK** between them: the link is the
encrypted `profile_token_enc` column. The honest threat model is in the final design §5.5.

## A. Tenancy, keys and access (F4, F5, L1–L2)

```mermaid
erDiagram
    tenant {
        uuid tenant_id PK "= CIS tenant id"
        text slug UK
        text status
    }
    tenant_settings {
        uuid tenant_id PK, FK
    }
    tenant_entitlement {
        uuid tenant_id PK, FK
    }
    member {
        uuid member_id PK
        uuid tenant_id FK
        text iss
        text sub
        text display_name "pii:name"
        text email "pii:contact"
        text role
        text status
    }
    owner_recovery_request {
        uuid owner_recovery_request_id PK
        uuid tenant_id FK
        uuid candidate_member_id FK
    }
    support_grant {
        uuid support_grant_id PK
        uuid tenant_id FK
        uuid granted_by FK
    }
    support_session {
        uuid support_session_id PK
        uuid tenant_id FK
        uuid grant_id FK
    }
    tenant_key {
        uuid tenant_key_id PK
        uuid tenant_id FK
        text purpose
        int key_version
    }
    integration_credential {
        uuid integration_credential_id PK
        uuid tenant_id FK
        text provider
        bytea secret_enc "conf:credential"
        text status
    }
    tenant ||--o| tenant_settings : "tenant_id"
    tenant ||--o| tenant_entitlement : "tenant_id"
    tenant ||--o{ member : "tenant_id"
    tenant ||--o{ tenant_key : "tenant_id"
    tenant ||--o{ integration_credential : "tenant_id"
    member ||--o{ owner_recovery_request : "candidate_member_id"
    member ||--o{ support_grant : "granted_by"
    support_grant ||--o{ support_session : "grant_id"
```

`member` is unique on `(tenant_id, iss, sub)`. `integration_credential.provider` takes the errata list (`twilio`,
`stripe_key`, `stripe_webhook_secret`, `google`, `microsoft`, `smtp`, `esign`) and `status` the four connection
states (`not_set_up`, `connected`, `needs_attention`, `disconnected`).

## B and C. F1 identity vault and F2 pseudonymous profile

```mermaid
erDiagram
    traveler {
        uuid traveler_id PK
        uuid tenant_id FK
        uuid owner_member_id FK
        uuid referrer_traveler_id FK
        bytea email_enc "pii:contact"
        bytea email_bidx
        bytea phone_bidx
        bytea passport_no_enc "pii:government_id"
        bytea profile_token_enc
    }
    traveler_health {
        uuid traveler_health_id PK
        uuid tenant_id FK
        uuid traveler_id FK, UK
        uuid consent_id FK
        bytea health_flags_enc "pii:health"
    }
    traveler_relation {
        uuid traveler_relation_id PK
        uuid tenant_id FK
        uuid from_id FK
        uuid to_id FK
        uuid inverse_id FK
        text kind
    }
    traveler_flight {
        uuid traveler_flight_id PK
        uuid tenant_id FK
        uuid trip_id FK
        uuid traveler_id FK
        bytea flight_no_enc "pii:travel"
    }
    document {
        uuid document_id PK
        uuid tenant_id FK
        uuid trip_id FK
        uuid traveler_id FK
        text kind
    }
    consent {
        uuid consent_id PK
        uuid tenant_id FK
        uuid traveler_id FK
        uuid agreement_doc_id FK
        text purpose
    }
    traveler_profile {
        uuid traveler_token PK "random, no FK to traveler"
        uuid tenant_id FK
    }
    trip_party {
        uuid trip_party_id PK
        uuid tenant_id FK
        uuid trip_id FK
        uuid traveler_token FK
        text role
    }
    profile_history {
        uuid profile_history_id PK
        uuid tenant_id FK
        uuid traveler_token FK
    }
    member |o--o{ traveler : "owner_member_id"
    traveler |o--o{ traveler : "referrer_traveler_id"
    traveler ||--o| traveler_health : "traveler_id"
    consent ||--o{ traveler_health : "consent_id"
    traveler ||--o{ traveler_relation : "from_id"
    traveler ||--o{ traveler_relation : "to_id"
    traveler_relation |o--o| traveler_relation : "inverse_id"
    trip ||--o{ traveler_flight : "trip_id"
    traveler ||--o{ traveler_flight : "traveler_id"
    trip ||--o{ document : "trip_id"
    traveler |o--o{ document : "traveler_id"
    traveler ||--o{ consent : "traveler_id"
    agreement_doc |o--o{ consent : "agreement_doc_id"
    traveler_profile ||--o{ trip_party : "traveler_token"
    traveler_profile ||--o{ profile_history : "traveler_token"
    trip ||--o{ trip_party : "trip_id"
```

`consent`, like `terms_acceptance` and `signature_event`, is append-only (INSERT and SELECT only); only
`crm.erase_subject()` deletes it.

## D. Pipeline and tasks (M2, M10)

```mermaid
erDiagram
    trip {
        uuid trip_id PK
        uuid tenant_id FK
        uuid owner_member_id FK
        text stage
        text waiting_on
    }
    trip_stage_transition {
        text from_stage PK
        text to_stage PK
    }
    trip_stage_history {
        uuid trip_stage_history_id PK
        uuid tenant_id FK
        uuid trip_id FK
        text from_stage
        text to_stage
    }
    trip_traveler {
        uuid trip_id PK, FK
        uuid traveler_id PK, FK
        uuid tenant_id FK
        text role
    }
    task {
        uuid task_id PK
        uuid tenant_id FK
        uuid trip_id FK
        uuid assignee_member_id FK
        uuid workflow_run_id FK
        text status
    }
    note {
        uuid note_id PK
        uuid tenant_id FK
        uuid trip_id FK
        uuid traveler_id FK
        bytea body_enc "pii:free_text"
    }
    tag {
        uuid tag_id PK
        uuid tenant_id FK
        text kind
    }
    tag_link {
        uuid tag_link_id PK
        uuid tenant_id FK
        uuid tag_id FK
        text object_kind
        uuid object_id
    }
    member |o--o{ trip : "owner_member_id"
    trip ||--o{ trip_stage_history : "trip_id"
    trip ||--o{ trip_traveler : "trip_id"
    traveler ||--o{ trip_traveler : "traveler_id"
    trip |o--o{ task : "trip_id"
    member |o--o{ task : "assignee_member_id"
    workflow_run |o--o{ task : "workflow_run_id"
    trip |o--o{ note : "trip_id"
    traveler |o--o{ note : "traveler_id"
    tag ||--o{ tag_link : "tag_id"
```

`trip_stage_transition` holds the allowed edges (no `tenant_id`, the Booking `trip_case_status_transitions`
pattern); a trigger checks each `trip_stage_history` row against it. `trip.stage` is
`inquiry|qualifying|proposal|booked|pre_departure|travelling|completed|lost|cancelled`, `trip.waiting_on`
`agency|client|aa|supplier|none`.

## D. Intake and metrics (M1, M16)

```mermaid
erDiagram
    form_definition {
        uuid form_definition_id PK
        uuid tenant_id FK
        text stage
        int version
    }
    intake_form {
        uuid intake_form_id PK
        uuid tenant_id FK
        uuid form_definition_id FK
        text public_key UK
    }
    form_submission {
        uuid form_submission_id PK
        uuid tenant_id FK
        uuid intake_form_id FK
        uuid trip_id FK
        text idempotency_key UK
        bytea payload_enc "pii:free_text"
    }
    metric_event {
        uuid metric_event_id PK
        uuid tenant_id FK
        uuid trip_id FK
        text name
    }
    metric_daily {
        uuid tenant_id PK, FK
        date day PK
        text metric PK
    }
    form_definition ||--o{ intake_form : "form_definition_id"
    intake_form ||--o{ form_submission : "intake_form_id"
    trip |o--o{ form_submission : "trip_id"
    trip |o--o{ metric_event : "trip_id"
```

## E. Proposal builder (M3, M4)

```mermaid
erDiagram
    proposal {
        uuid proposal_id PK
        uuid tenant_id FK
        uuid trip_id FK
        uuid agreement_doc_id FK
        int version
        text status
        text price_visibility
    }
    proposal_day {
        uuid proposal_day_id PK
        uuid tenant_id FK
        uuid proposal_id FK
        int day_no
    }
    option_block {
        uuid option_block_id PK
        uuid tenant_id FK
        uuid proposal_day_id FK
        uuid default_option_id FK
        text type
    }
    option {
        uuid option_id PK
        uuid tenant_id FK
        uuid option_block_id FK
        uuid agency_supplier_id FK
        text source
        numeric(14_2) net_delta "conf:commercial"
    }
    option_rule {
        uuid option_rule_id PK
        uuid tenant_id FK
        uuid option_id FK
    }
    selection {
        uuid selection_id PK
        uuid tenant_id FK
        uuid proposal_id FK
        uuid option_id FK
        text by
    }
    trip ||--o{ proposal : "trip_id"
    agreement_doc |o--o{ proposal : "agreement_doc_id"
    proposal ||--o{ proposal_day : "proposal_id"
    proposal_day ||--o{ option_block : "proposal_day_id"
    option_block ||--o{ option : "option_block_id"
    option |o--o{ option_block : "default_option_id"
    agency_supplier |o--o{ option : "agency_supplier_id"
    option ||--o{ option_rule : "option_id"
    proposal ||--o{ selection : "proposal_id"
    option ||--o{ selection : "option_id"
```

`proposal` is unique on `(trip_id, version)`; the hold set reference is unique on `(proposal_id, version)`.
`price_visibility` is `total_with_deltas` (default) or `total_only`.

## E. Client access and agreements (M11, M12)

```mermaid
erDiagram
    client_link {
        uuid client_link_id PK
        uuid tenant_id FK
        uuid trip_id FK
        uuid traveler_id FK
        uuid reissued_from FK
        bytea token_hash UK "conf:credential"
    }
    traveler_access {
        uuid traveler_access_id PK
        uuid tenant_id FK
        uuid trip_id FK
        uuid traveler_id FK
        text level
    }
    otp_challenge {
        uuid otp_challenge_id PK
        uuid tenant_id FK
        uuid traveler_id FK
        bytea code_hash "conf:credential"
    }
    prep_pack_selection {
        uuid prep_pack_selection_id PK
        uuid tenant_id FK
        uuid trip_id FK
    }
    agreement_doc {
        uuid agreement_doc_id PK
        uuid tenant_id FK
        uuid published_by FK
        text kind
        int version
    }
    terms_acceptance {
        uuid terms_acceptance_id PK
        uuid tenant_id FK
        uuid trip_id FK
        uuid traveler_id FK
        uuid agreement_doc_id FK
        uuid proposal_id FK
    }
    signature_request {
        uuid signature_request_id PK
        uuid tenant_id FK
        uuid trip_id FK
        uuid traveler_id FK
        uuid signed_pdf_document_id FK
        text status
    }
    signature_event {
        uuid signature_event_id PK
        uuid tenant_id FK
        uuid signature_request_id FK
    }
    trip ||--o{ client_link : "trip_id"
    traveler |o--o{ client_link : "traveler_id"
    client_link |o--o{ client_link : "reissued_from"
    trip ||--o{ traveler_access : "trip_id"
    traveler ||--o{ traveler_access : "traveler_id"
    traveler ||--o{ otp_challenge : "traveler_id"
    trip ||--o{ prep_pack_selection : "trip_id"
    member |o--o{ agreement_doc : "published_by"
    trip ||--o{ terms_acceptance : "trip_id"
    traveler ||--o{ terms_acceptance : "traveler_id"
    agreement_doc ||--o{ terms_acceptance : "agreement_doc_id"
    proposal ||--o{ terms_acceptance : "proposal_id"
    trip ||--o{ signature_request : "trip_id"
    traveler ||--o{ signature_request : "traveler_id"
    document |o--o{ signature_request : "signed_pdf_document_id"
    signature_request ||--o{ signature_event : "signature_request_id"
```

## F. Money (M6, M7, M13, M15)

```mermaid
erDiagram
    agency_supplier {
        uuid agency_supplier_id PK
        uuid tenant_id FK
        text kind
        text contact_email "pii:contact"
    }
    booking_line {
        uuid booking_line_id PK
        uuid tenant_id FK
        uuid trip_id FK
        uuid agency_supplier_id FK
        text status
    }
    booking_line_money {
        uuid booking_line_money_id PK
        uuid tenant_id FK
        uuid booking_line_id FK
        uuid supersedes_id FK
    }
    fx_rate_platform {
        date rate_date PK
        char(3) base PK
        char(3) quote PK
        text source PK
    }
    fx_rate_override {
        uuid fx_rate_override_id PK
        uuid tenant_id FK
        uuid set_by FK
    }
    invoice {
        uuid invoice_id PK
        uuid tenant_id FK
        uuid trip_id FK
        uuid payer_traveler_id FK
        text status
    }
    payment_schedule {
        uuid payment_schedule_id PK
        uuid tenant_id FK
        uuid trip_id FK
    }
    payment {
        uuid payment_id PK
        uuid tenant_id FK
        uuid invoice_id FK
        uuid refund_of FK
        text status
    }
    refund_request {
        uuid refund_request_id PK
        uuid tenant_id FK
        uuid payment_id FK
        uuid approved_by FK
        text status
    }
    commission {
        uuid commission_id PK
        uuid tenant_id FK
        uuid booking_line_id FK, UK
        text status
    }
    payment_provider_account {
        uuid payment_provider_account_id PK
        uuid tenant_id FK
        text provider
    }
    trip ||--o{ booking_line : "trip_id"
    agency_supplier |o--o{ booking_line : "agency_supplier_id"
    booking_line ||--o{ booking_line_money : "booking_line_id"
    booking_line_money |o--o| booking_line_money : "supersedes_id"
    member ||--o{ fx_rate_override : "set_by"
    trip ||--o{ invoice : "trip_id"
    traveler |o--o{ invoice : "payer_traveler_id"
    trip ||--o{ payment_schedule : "trip_id"
    invoice ||--o{ payment : "invoice_id"
    payment |o--o{ payment : "refund_of"
    payment ||--o{ refund_request : "payment_id"
    member |o--o{ refund_request : "approved_by"
    booking_line ||--o| commission : "booking_line_id"
```

`booking_line_money` carries the margin (RLS adds `app.member_role IN ('owner', 'agent')`). Money rows freeze
their FX block; a correction is a new row with `supersedes_id`. `invoice.status` is
`draft|open|payment_claimed|paid|paid_unfulfillable|void|expired`. `fx_rate_platform` is reference data without
`tenant_id`.

## G. Messages and channels (M5, M9)

```mermaid
erDiagram
    channel_account {
        uuid channel_account_id PK
        uuid tenant_id FK
        uuid credential_id FK
        text kind
        text status
    }
    ingest_address {
        uuid ingest_address_id PK
        uuid tenant_id FK
        text local_part UK
    }
    conversation {
        uuid conversation_id PK
        uuid tenant_id FK
        uuid traveler_id FK
        uuid trip_id FK
        text channel
    }
    message {
        uuid message_id PK
        uuid tenant_id FK
        uuid conversation_id FK
        uuid template_id FK
        uuid ai_draft_id FK
        bytea body_enc "pii:free_text"
        text status
    }
    saved_reply {
        uuid saved_reply_id PK
        uuid tenant_id FK
    }
    message_template {
        uuid message_template_id PK
        uuid tenant_id FK
    }
    dispatch_queue {
        uuid dispatch_queue_id PK
        uuid tenant_id FK
        uuid message_id FK
        timestamptz not_before
    }
    integration_credential |o--o{ channel_account : "credential_id"
    traveler |o--o{ conversation : "traveler_id"
    trip |o--o{ conversation : "trip_id"
    conversation ||--o{ message : "conversation_id"
    message_template |o--o{ message : "template_id"
    ai_draft |o--o{ message : "ai_draft_id"
    message ||--o{ dispatch_queue : "message_id"
```

`message.status` is `queued|held_reconnect|sent|delivered|read|failed`; sender kinds are `agency_mailbox|system`
(errata S247: `platform` is removed). `message.external_id` is unique per channel.

## G. Campaigns and calendar (R14, R15)

```mermaid
erDiagram
    campaign {
        uuid campaign_id PK
        uuid tenant_id FK
    }
    campaign_recipient {
        uuid campaign_recipient_id PK
        uuid tenant_id FK
        uuid campaign_id FK
        uuid traveler_id FK
        text status
    }
    unsubscribe_token {
        uuid unsubscribe_token_id PK
        uuid tenant_id FK
        uuid traveler_id FK
        bytea token_hash UK "conf:credential"
    }
    calendar_connection {
        uuid calendar_connection_id PK
        uuid tenant_id FK
        uuid credential_id FK
        text provider
    }
    meeting_slot {
        uuid meeting_slot_id PK
        uuid tenant_id FK
        uuid trip_id FK
        uuid calendar_connection_id FK
        text status
    }
    campaign ||--o{ campaign_recipient : "campaign_id"
    traveler ||--o{ campaign_recipient : "traveler_id"
    traveler ||--o{ unsubscribe_token : "traveler_id"
    integration_credential ||--o{ calendar_connection : "credential_id"
    trip |o--o{ meeting_slot : "trip_id"
    calendar_connection |o--o{ meeting_slot : "calendar_connection_id"
```

## H. Automation and AI (M10, M14)

```mermaid
erDiagram
    workflow_template {
        uuid workflow_template_id PK
        uuid tenant_id FK
        text scope
    }
    workflow_rule {
        uuid workflow_rule_id PK
        uuid tenant_id FK
        uuid workflow_template_id FK
        text trigger
    }
    workflow_run {
        uuid workflow_run_id PK
        uuid tenant_id FK
        uuid rule_id FK
        uuid trip_id FK
        text status
    }
    ai_draft {
        uuid ai_draft_id PK
        uuid tenant_id FK
        uuid trip_id FK
        uuid voice_profile_id FK
        text status
    }
    placeholder_map {
        uuid placeholder_map_id PK
        uuid tenant_id FK
        uuid ai_draft_id FK
        bytea map_enc
    }
    voice_profile {
        uuid voice_profile_id PK
        uuid tenant_id FK
        uuid member_id FK
    }
    llm_call {
        uuid llm_call_id PK
        uuid tenant_id FK
    }
    spend_budget {
        uuid tenant_id PK, FK
        date month PK
    }
    workflow_template ||--o{ workflow_rule : "workflow_template_id"
    workflow_rule ||--o{ workflow_run : "rule_id"
    trip ||--o{ workflow_run : "trip_id"
    trip ||--o{ ai_draft : "trip_id"
    voice_profile |o--o{ ai_draft : "voice_profile_id"
    ai_draft ||--o{ placeholder_map : "ai_draft_id"
    member ||--o{ voice_profile : "member_id"
```

`llm_call` holds no prompt or output text and no `traveler_token`; `ai_draft` stores text with placeholders only.

## I. Ops hand-off and insights (M8, M17)

```mermaid
erDiagram
    ops_release {
        uuid ops_release_id PK
        uuid tenant_id FK
        uuid trip_id FK, UK
        bytea payload_enc "pii:travel"
    }
    supplier_manifest_export {
        uuid supplier_manifest_export_id PK
        uuid tenant_id FK
        uuid ops_release_id FK
        uuid exported_by FK
    }
    incident_flag {
        uuid incident_flag_id PK
        uuid tenant_id FK
        text departure_id
    }
    insight_fact {
        uuid tenant_id "view for crm_insights"
        text month
        text budget_band
    }
    insight_aggregate {
        uuid insight_aggregate_id PK
        int n_travelers
        int n_agencies
    }
    trip ||--o| ops_release : "trip_id"
    ops_release ||--o{ supplier_manifest_export : "ops_release_id"
    member ||--o{ supplier_manifest_export : "exported_by"
```

`insight_fact` is a view (no keys). `insight_aggregate` has **no `tenant_id`**: a cell is published only when
n ≥ 10 travellers and ≥ 3 agencies.

## J. Audit, deletion and platform (F5, M18)

```mermaid
erDiagram
    audit_event {
        uuid event_id PK
        timestamptz at PK "monthly partitions"
        uuid tenant_id FK
        text action
    }
    audit_export_manifest {
        uuid audit_export_manifest_id PK
        uuid tenant_id FK
        timestamptz hour UK
    }
    erasure_request {
        uuid erasure_request_id PK
        uuid tenant_id FK
        uuid confirmed_by FK
        text scope
    }
    export_job {
        uuid export_job_id PK
        uuid tenant_id FK
        uuid confirmed_by FK
    }
    job {
        uuid id PK "ADR 0003a template"
        uuid parent_job_id FK
    }
    outbox {
        uuid id PK
    }
    inbox_events {
        uuid id PK
    }
    release_note {
        uuid release_note_id PK
    }
    member |o--o{ erasure_request : "confirmed_by"
    member |o--o{ export_job : "confirmed_by"
    job |o--o{ job : "parent_job_id"
```

`job`, `outbox` and `inbox_events` follow the ADR 0003a and contracts templates (`id` keys, ids-only payloads,
`inbox_events` unique on `(source, contract, idempotency_key)`); `crm.job` has no RLS. `audit_event` is partitioned
by month, so its primary key includes `at`. `release_note` is platform data without `tenant_id`.

## Open points for the migration PRs

Choices this page makes where the sources are silent. The PR that creates the table either follows them or changes
this page in the same PR (the drift check reads this page).

| Point | This page | Decide in |
|---|---|---|
| Primary keys | `<table>_id uuid` (the lane's own names: `tenant_id`, `member_id`, `trip_id`); natural keys for `tenant_settings`, `tenant_entitlement`, `metric_daily`, `spend_budget`, `fx_rate_platform`, `trip_stage_transition`, `trip_traveler`; template `id` for `job`, `outbox`, `inbox_events` | AA-933 (`crm-001` base template) |
| Tenant FK form | Single-column `tenant_id` to `tenant` on every tenant table; child FKs single-column. A composite `(tenant_id, <parent>_id)` FK is the alternative that makes a cross-tenant link impossible even for the owner role | AA-933 |
| `trip_stage_transition` | Global rows without `tenant_id` (Booking pattern), although DM-7 lists it with the tenant configuration tables | AA-943 |
| Inferred FKs | `form_submission.intake_form_id`, `workflow_rule.workflow_template_id`, `meeting_slot.calendar_connection_id`, `booking_line_money.booking_line_id` (the lane says `line_id`) | the card that creates each table |
| Errata additions | The data-request log and the owner's shared-responsibility acknowledgement (errata §1, CRM-31 and CRM-35) have no table name or DM-7 row yet; they are not drawn | AA-962, AA-967 (DM-7 row first, DM-7.1) |
