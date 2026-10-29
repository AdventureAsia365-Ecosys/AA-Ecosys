---
id: APP-04-erd-design-tripplanner
title: "ERD design: tripplanner schema"
description: "Design ERD of the tripplanner schema (TripPlanner), enforced against the live dump by the drift check: a migration that changes tables, keys or foreign keys must update this page in the same change."
type: reference
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [aa-cis-dev-db, tripplanner-lambda]
last_reviewed: 2026-10-29
review_every_days: 90
generated: false
related: [APP-04, APP-04-erd, APP-04-erd-design, APP-04-erd-tripplanner, AA-894, AA-861]
---

# ERD design: tripplanner schema

<!-- erd-design schema=tripplanner enforce=true -->

Design ERD of schema `tripplanner` (owner TripPlanner, migrations `tp-NNN`). Started S247 (AA-894) as a copy of the live
model at **tp-017**, re-synced to **tp-018** in S250 and to **tp-019** in S251 (`traveller_accounts` +
`sessions.account_id`, AA-908): the pilot place tables tp-018 dropped (`itinerary_components`,
`tour_day`, `tour_stop`, `tour_graph_*`, `tour_leg`, `tour_junction`) are gone from the page, so the drift check passes
again. Checked against the live dump at **tp-020** in S255: tp-020 (AA-992) adds three ops views only, so no table, key
or foreign key changed. Updated for **tp-021** (AA-861) in S257, in the same change as the migration: the new
`job` table (ADR 0003a job table template, kinds `tp_*`, self FK `parent_job_id`, drawn like `crm.job` and
`booking.job`) and the new nullable `outbox.redacted_at` (the redaction marker of DM-6.6; no key or FK change on
`outbox`). The `job` unique key on `idempotency_key` is a partial unique index, so it is not marked `UK` (the
generated page marks single-column unique keys without a predicate only). The page draws tables only; the views are listed on the generated page. It is **enforced**: the nightly DB Schema Dump fails its drift step when the live tables, primary keys or
foreign keys differ from this page. A TripPlanner migration that changes
them updates this page in the same change (root PR next to the migration copy).

Generated live view: [ERD: tripplanner schema](../tripplanner.md). Conventions: [design README](README.md).

```mermaid
erDiagram
    component_id_map {
        uuid old_id PK
        uuid new_id
        text matched_by
        timestamptz created_at
    }
    customers {
        uuid id PK
        text name "pii:name"
        text phone UK "pii:contact"
        text email UK "pii:contact"
        timestamptz created_at
        boolean contact_consent
        timestamptz contact_consent_at
    }
    job {
        uuid id PK "ADR 0003a template"
        text kind
        jsonb payload
        text status
        integer attempt
        integer max_attempts
        timestamptz run_after
        text locked_by
        timestamptz locked_until
        boolean cancel_requested
        text idempotency_key
        jsonb progress
        jsonb result
        numeric cost_usd
        text error
        uuid parent_job_id FK
        text created_by
        timestamptz created_at
        timestamptz updated_at
        timestamptz started_at
        timestamptz finished_at
    }
    llm_spend_daily {
        date day PK
        text stage PK
        numeric cost_usd
        integer calls
        integer unpriced_calls
        timestamptz updated_at
    }
    narration_cache {
        text itinerary_hash PK
        text mode
        text narration
        text source
        integer days
        timestamptz created_at
        integer hits
        timestamptz last_hit_at
    }
    outbox {
        bigint id PK
        text event
        integer schema_version
        text idempotency_key UK
        uuid aggregate_id
        jsonb payload "pii:contact"
        timestamptz created_at
        timestamptz redacted_at
    }
    sessions {
        uuid id PK
        text guest_token UK "conf:credential"
        uuid customer_id FK
        timestamptz created_at
        timestamptz expires_at
        bytea guest_token_hash "conf:credential"
        uuid account_id FK
    }
    traveller_accounts {
        uuid id PK
        text iss UK "pii:online_id"
        text sub UK "pii:online_id"
        timestamptz created_at
        timestamptz last_sign_in_at
    }
    trip_drafts {
        uuid id PK
        uuid session_id FK
        text status
        jsonb itinerary "pii:travel"
        date date_start "pii:travel"
        date date_end "pii:travel"
        timestamptz created_at
        timestamptz updated_at
    }
    trip_events {
        bigint id PK
        uuid trip_id
        uuid session_id FK
        text event_type
        jsonb payload "pii:free_text"
        timestamptz created_at
    }
    customers |o--o{ sessions : "customer_id"
    job |o--o{ job : "parent_job_id"
    sessions ||--o{ trip_drafts : "session_id"
    sessions ||--o{ trip_events : "session_id"
    traveller_accounts |o--o{ sessions : "account_id"
```
