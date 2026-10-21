---
id: SEC-04
title: Compliance and privacy register
description: Records of processing (RoPA), the sub-processor list and the legal decisions log for AA-Ecosys, each line tied to code or the live schema dump; provisional until the pii column tags land.
type: reference
status: draft
owner: nghiep
audience: [cio, owner, engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-21
review_every_days: 90
related: [AA-886, AA-877, AA-804, AA-839, AA-820, SEC-04-retention, SEC-04-dpa, SEC-04-dsar, SEC-04-packet, SEC-04-consent-query]
---

# Compliance and privacy register

This register lists what personal data AA-Ecosys processes, where it lives, who else receives it and which legal
decisions have been taken. It is the in-repo form of the RoPA, sub-processor list and decisions log asked for in
the legal packet. Business and legal calls are Ms. Thư's; this page records facts and open points.

Related pages: [retention log](retention-log.md), [DPA template](dpa-template.md),
[DSAR and erasure runbook](dsar-erasure-runbook.md), [readiness packet for Ms. Thư](readiness-packet.md),
[consent capture check](consent-capture-query.md).

How to read it:

- **Evidence** cites `repo@main file:line`, read on 2026-10-21, or the live schema dump
  ([`db-schema-reference.md`](../architecture/db-schema-reference.md), Verified 2026-10-20 05:28 UTC). Repos:
  CIS = AA-CIS-App, BK = AA-Booking, TP = AA-TripPlanner-Web, INF = AA-CIS-Infra.
- **Live** means the control runs on Dev today. **Planned** means it does not run yet; the open work item is named.
- `[to be confirmed]` is a point for Ms. Thư or counsel. AWS accounts are named acc1, acc2 and acc3 only; the
  account map is in [onboarding](../onboarding.md).

## (a) Records of processing (RoPA)

> [!IMPORTANT]
> **Provisional.** The rows below name every column that AA-877 tags (`bk-018`, `tp-016`, CIS 247 and 251), checked
> against the migrations on 2026-10-21. The note goes, and the generated column inventory appears under the table,
> once those tags are live and the schema reference carries them (see "How to regenerate this table").

Data classes are the DM-6.1 classes of [`02-data-management.md`](../architecture/data-standards/02-data-management.md):
`contact`, `name`, `address`, `profile`, `online_id`, `free_text`, `travel`, `payment`, and `conf:credential` for
hashes and keys. Legal basis is `[to be confirmed]` on every row. Retention links the
[§7 retention table](../architecture/data-standards/02-data-management.md#7-retention-and-archival) (DM-7.1 is the registry).

| # | Purpose | Data subjects | Data classes | Tables and columns (dump 2026-10-20) | Retention | Recipients and sub-processors | Transfer |
|---|---|---|---|---|---|---|---|
| 1 | TripPlanner guest trip and inquiry to an advisor, with contact consent | Travellers (guests, no account) | `name`, `contact`, `travel`, `free_text` (traveller notes on custom days and `add_day` edits), `conf:credential` (guest token hash) | `tripplanner.customers` (`name`, `email`, `phone`, `contact_consent`, `contact_consent_at`); `tripplanner.outbox.payload` (copy of the inquiry, `inquiry.submitted`) and the view `tripplanner.v_inquiry_outbox.payload` over it; `tripplanner.sessions` (`guest_token_hash`, `customer_id`; plaintext `guest_token` retired by CHECK `sessions_guest_token_retired_chk`); `tripplanner.trip_drafts` (`itinerary`, `date_start`, `date_end`) and `tripplanner.trip_events.payload`, linked to a person through `session_id` → `sessions.customer_id` | Outbox payload: 90-day redaction approved (DM-6.6), **not built** (TripPlanner has no job table; AA-861 blocked on `tripplanner.job`). Customers, sessions, drafts, events: no window yet (proposed in L3) | AA advisors via AA-Booking; AWS acc2 (RDS, Lambda); Vercel (TripPlanner BFF carries the form in transit); Bedrock on acc3/acc1 (trip contents and search text, no identity: TP `/privacy` §5, DM-6.4); Mapbox (browser: IP, map area) | US (us-west-1); Bedrock `global.` inference profiles on acc3/acc1 may process prompts outside the US; Vercel function region not pinned (default region `[to be confirmed]`); Mapbox edge locations |
| 2 | Booking customer master and trip cases | Travellers who sent an inquiry or were entered by staff | `name`, `contact`, `address`, `profile`, `travel`, `free_text`, `conf:credential` | `booking.customers` (`name`, `email`, `phone`, `address`, `gender`, `marital_status`, `profession`, `profile_media_id`, `external_ref`, `contact_consent`, `contact_consent_at`, `source`); `booking.v_customer_summary` (`name`, `email`, `phone`, `address`: staff list view over `customers`); `booking.inbox_events` (`payload`: copy of the inquiry; `error`: may quote it; both redacted together, `redacted_at` column); `booking.trip_cases` (`notes`, `inquiry_snapshot`, `start_date`, `end_date`, `pax`, `pax_adults`, `pax_children`, `trip_style`); `booking.trip_case_status_history.note`; `booking.trip_case_versions` (`title`, `notes`, `approval_note`: the proposal staff send to the traveller); `booking.trip_case_version_itinerary.notes`; `booking.customer_otps.otp_hash`, `booking.customer_sessions.refresh_token_hash` (hashes only); `booking.media_files.s3_key` (S3 object of a profile photo, linked from `customers.profile_media_id`; nothing uploads to it yet) | Inbox payload: 90-day redaction (DM-6.6): job `bk_retention_inbox_redact` exists (BK `backend/app/retention/policy.py:9-15`, `:83-90`), **DRY RUN only**, no real run yet. OTP/sessions: proposed 7 days after expiry. Customers, trip cases: no window yet | AA staff (Booking admin); AWS acc2 (RDS, ECS, S3); SES (new-inquiry mail, row 3); Vercel (Booking admin) | US (us-west-1) |
| 3 | Booking notifications, staff e-mail and audit | Travellers named in a case; staff | `name`, `contact`, `free_text` | `booking.notifications` (`recipient_ref`, `title`, `message`, `data`); `booking.audit_logs` (`before`, `after` jsonb row snapshots, `summary` names the traveller of a manual lead, `entity_label` names staff; rule: redact, never delete, DM-6.7); the `bk_notify_email` message to the staff inbox carries the traveller's name, e-mail and phone (BK `backend/app/notifications/staff_email.py:174-190`) | Notifications: proposed (read 90 days, unread 180). Audit logs: kept, window set before prod | Staff inbox set by the Booking `STAFF_NOTIFY_EMAIL` setting (BK `backend/app/settings.py:30`); SES; the mail host of that inbox (DreamHost if it is an adventure.asia address, INF `accounts/aa365/identity.tf:22-23`) `[to be confirmed]` | US (SES us-west-1); mail host `[to be confirmed]` |
| 4 | Staff users and sign-in | AA staff | `name`, `contact`, `online_id`, `conf:credential` (legacy password hash) | Cognito WORKFORCE pool (INF `identity.tf:344`); `booking.staff_users` (`email`, `name`, `cis_user_id`: `cog:` plus the Cognito sub on WORKFORCE rows, `cognito_iss`, `cognito_sub`, `last_seen_at`); `shared.admin_users` (`email`, `display_name`, `username`, `cognito_iss`, `cognito_sub`, `password_hash`: legacy login, NULL for Cognito-only staff, `last_login_at`; e-mail CHECK limits it to `@adventure.asia` plus one e2e address); staff invitation mail (CIS `services/jobs/staff_invite_email_job.py:1-24`) | No window yet | AWS acc2 (Cognito, SES, RDS); Sentry (possible, see sub-processors) | US (us-west-1) |
| 5 | Tenant (partner business) accounts and channel connections | Tenant businesses; their staff only through shared credentials | business data, `conf:credential` | `shared.tenants` (`name`, `slug`, `country`, `api_key_hash`): **no individual contact column**. Portal sign-in is one shared tenant key; tenant user accounts (AA-813) are not built. Channel credentials: `shared.tenant_integrations` (`config`, `secret_key`) and Secrets Manager `acp/cms/*`, `acp/social/*` (`conf:credential`). `acp_shared.audit_log` (`actor`, `actor_type`, `route`, `details`) | Audit log: kept, window set before prod. Others: while the account is active, then `[to be confirmed]` | AA admins; AWS acc2; Vercel (portal); the tenant's own channels (WordPress, Meta) when the tenant publishes: those are the tenant's providers, not AA sub-processors | US (us-west-1) |
| 6 | AI content generation and review | None identified: no identifying PII may be sent (DM-6.4) | tour and tenant content; `travel` for TripPlanner narration | `shared.llm_call_log` (no PII by rule, DM-6.4); prompts are not stored. DM-6.4 is enforced by code review only: no automated PII check exists | `llm_call_log` 180 days (approved; retention kind scheduled, see the retention log) | Bedrock on acc2 (native), acc3 (primary satellite) and acc1 (fallback) with Claude and GPT models; OpenAI API (last resort for some judges); Jev (content decisions, allowlisted tenants only) | US; `global.` profiles on acc3/acc1 may process outside the US |
| 7 | Operational alert mail | AA staff and operators | `contact` | `shared.alert_recipient` (`email`, `subscription_arn`, `note`); addresses are shape-checked only, no domain rule (CIS `shared/alert_recipients.py:98-108`) | No window yet | SNS e-mail subscriptions (INF `accounts/aa365/observability.tf:53`, CIS `api/services/alert_recipients.py`); SES ops mail (CIS `services/jobs/ops_alert_email_job.py:1-22`) | US (us-west-1) |
| 8 | Supplier contacts (hotels, transport, local partners) | Supplier staff | `name`, `contact`, `profile` (job title), `address` (business address, untagged) | `booking.suppliers` (`contact_name`, `contact_title`, `contact_email`, `contact_phone`, `address`; `company_name` is business data) | No window yet | AA staff (Booking admin); AWS acc2 (RDS); Vercel (Booking admin) | US (us-west-1) |

The consent chain of rows 1 and 2 was checked on Dev on 2026-10-20 (DM-6.5): see the
[consent capture check](consent-capture-query.md).

### How to regenerate this table

1. Owners tag a column that holds personal data in the migration that creates it: `COMMENT ON COLUMN … IS
   'pii:<class>; …'` (DM-6.1). The DB Schema Dump carries the tags into
   [`db-schema-reference.md`](../architecture/db-schema-reference.md), section *Personal and confidential data tags
   (DM-6.1)*, for every schema.
2. Run `python3 tools/data/gen_pii_inventory.py` from the repo root. It rewrites the generated "Column inventory
   (from pii tags)" block of this section (`pii:*` and `conf:credential` columns; `conf:commercial` is business data
   and is left out).
3. Run `python3 tools/data/gen_pii_inventory.py --check`. It exits 1 when the block is stale or when a tagged column
   is named by no row: a new processing line, to add to the right row (or a new row) with its purpose, retention and
   recipients. It also prints tagging gaps: columns of `booking.*` / `tripplanner.*` named here without a tag. The
   consent flags, `external_ref`, `source`, `recipient_ref`, `last_seen_at`, `redacted_at`, `sessions.customer_id` and
   the supplier business fields are untagged on purpose; any other gap goes to the owner repo as a tag migration.
4. Name columns in the "Tables and columns" cells as `` `schema.relation.column` `` or
   `` `schema.relation` (`column`, …) ``, so the check can see them. Plain words are not read.
5. Bump `last_reviewed`.

## (b) Sub-processors

Contract and DPA status is `[to be confirmed]` for every vendor: no DPA has been signed or checked in this repo.

| Vendor | Service | Data | PII | Region | Contract / DPA | Evidence |
|---|---|---|---|---|---|---|
| Amazon Web Services, acc2, billed through the reseller TrueIDC | Hosting: RDS, ECS, Lambda, S3, Secrets Manager, CloudWatch, API Gateway | Every schema of rows 1-8 | Yes | us-west-1 | `[to be confirmed]`. The reseller's management account has privileged access to acc2 (S241 review P0-12) | Account map in [onboarding](../onboarding.md); `docs/audits/2026-10-17-S241-sdlc-review/README.md:323` |
| TrueIDC (AWS reseller for acc2) | Billing and account management | Account-level access, no data processing by design | Possible (privileged access) | `[to be confirmed]` | Whether a reseller is a sub-processor: for counsel | S241 review P0-12; CRM research `04-economics-compliance-security.md:167` |
| AWS Bedrock: acc2 (native), acc3 (primary satellite, billed through the reseller eCloudvalley), acc1 (fallback) | AI models: Claude (Anthropic) and GPT models on Bedrock | Tour and tenant content; TripPlanner trip contents and search text (the narration prompt carries place names and text extracts, no customer identifier) | No identifying PII (DM-6.4) | API calls to us-west-1. Inference profiles as seeded: `us.` on acc2, `global.` on acc3 and acc1; a `global.` profile can route a prompt to a region outside the US. Live routing `[to be confirmed]` (`shared.llm_model_catalog`) | `[to be confirmed]`; reseller question as above | TP `backend/config.py:49`, `:54`, `backend/shared/llm_gateway.py:104-105`, `backend/assembly/agent.py:43`; CIS `api/migrations/169_llm_model_catalog.sql:57-66`, `:72-77`; CIS `CONTEXT.md:160-176` |
| Anthropic, OpenAI as model makers on Bedrock | Models served by Bedrock | Per the S245 CRM research, Anthropic receives no data according to AWS documentation (CRM research `04-…md:268`) | No | — | For counsel to confirm whether they are listed | CRM research `04-economics-compliance-security.md:152-167`, `:268` |
| OpenAI API (platform, last resort only) | Judge model fallback | Judge prompts on tour and tenant content | No (DM-6.4) | US `[to be confirmed]` | `[to be confirmed]`; abuse-monitoring logs kept up to 30 days unless zero retention is approved | CIS `CONTEXT.md:160-176`; secret `aa-cis/dev/openai-key` ([secrets register](../security/secrets-register.md)); CRM research `04-…md:162-165` |
| Jev (Typesafe API) | Content decisions | Tour text; tenant text only for tenants on `shared.jev_tenant_allowlist` | No (DM-6.4) | `[to be confirmed]` | **Open contract item:** DM-6.4 requires a DPA / zero-retention agreement before tenant content is sent (ADR 0001) | CIS `shared/secrets.py:70-86`; secret `aa-cis/dev/typesafe` ([secrets register](../security/secrets-register.md)); CIS `CONTEXT.md:197-210` |
| Sentry | Error tracking for CIS api and worker (live, AA-870); CIS admin UI SDK present | Error events: stack traces, redacted URLs, allowlisted headers; no bodies, no cookies, no default PII | Should be none; see note 1 | `[to be confirmed]` | `[to be confirmed]` | CIS `shared/sentry_init.py:6-9`, `:66-79`, `:96-108`; `api/main.py:77`; `worker/__main__.py:17`; `frontend/package.json:12`; portal has none (`CONTEXT.md:119`); TP and BK: no SDK |
| Amazon SES (acc2) | E-mail: Booking new-inquiry mail to staff; CIS staff invitations; CIS ops alerts; Cognito sign-in codes | Traveller name, e-mail, phone (Booking mail); staff addresses | Yes | us-west-1 | Part of AWS | BK `backend/app/mailer.py:1-9`, `notifications/staff_email.py:1-16`; CIS `shared/aws_client/ses_mailer.py:1-26`; INF `identity.tf:34` |
| Amazon SNS (acc2) | Alarm e-mail subscriptions | Alert-recipient addresses | Yes (staff) | us-west-1 | Part of AWS | INF `observability.tf:53`; CIS `api/services/alert_recipients.py` |
| Amazon Cognito (acc2) | Staff sign-in (WORKFORCE, live); EXTERNAL pool defined for future customer and tenant sign-in, with Google and Facebook identity providers created only when their client variables are set | Staff e-mail, `sub`, sign-in events | Yes (staff) | us-west-1 | Part of AWS | INF `identity.tf:344`, `:421`, `:524`, `:545`; EXTERNAL native sign-up refused until a flag is set (`identity.tf:36-38`, `:45`); no live app signs travellers in through EXTERNAL yet (no Cognito reference in TripPlanner on main) |
| Vercel (Hobby plan) | Hosts TripPlanner, the tenant portal, the CIS admin and the Booking admin | Page requests and IP; the TripPlanner BFF carries the inquiry form in transit | Yes, in transit | No function region pinned (`vercel.json` holds git settings only): Vercel default region `[to be confirmed]`; edge worldwide | `[to be confirmed]`; plan decision D-18 | [CIO guide](../guides/cio.md) vendor table; AA-886 Linear comment 2026-10-20 |
| Mapbox | Map tiles and directions in the TripPlanner browser | IP address, map area viewed | IP only | Global | `[to be confirmed]` | TP `frontend/lib/mapbox.ts:119`; TP `/privacy` §6 |
| Geoapify | Geocoding of place names (CIS worker) | Place names | No | `[to be confirmed]` | `[to be confirmed]` | CIS `shared/secrets.py:89-106` |
| DataForSEO | SEO search demand (CIS api and worker) | Keywords | No | `[to be confirmed]` | `[to be confirmed]` | [Secrets register](../security/secrets-register.md) row `aa-cis/dev/dataforseo` |
| Google (Drive API key) | Reads tour photo originals | Photos | No | Google | — | Secrets register row `aa-cis/dev/gdrive-photo-reader` |
| DreamHost | Mail host of adventure.asia: staff mailboxes, the published contact `info@adventure.asia`, possibly the Booking new-inquiry inbox | Traveller contact data if the inquiry inbox or a privacy request lands there | `[to be confirmed]` | `[to be confirmed]` | `[to be confirmed]` | INF `identity.tf:22-23`; TP `frontend/lib/legal.ts` (`LEGAL_CONTACT_EMAIL`) |
| GitHub (Free plan) | Code and CI | Code, CI logs | No traveller PII | US | — | CIO guide vendor table |
| Namecheap | Domain registrar (DNS records are in Route 53) | Domain registration | No | — | — | ADR 0006a `:163` |
| Linear, Notion, Atlassian Jira | Work tracking and notes | Work items | Staff names only. Linear would hold traveller PII if `support@` mail were routed into it (packet domain 9) | — | — | CIO guide vendor table |

**Not AA sub-processors:** the tenant's own channels (WordPress sites, Facebook Pages through Meta). AA publishes
there only on the tenant's instruction with credentials the tenant supplies; the tenant chose those providers
(AA-820 draft §1 "Who publishes"; portal `/privacy` §6 "Your channels").

**Not active:** Langfuse (LLM tracing) is commented out in Terraform (INF `modules/secrets/main.tf:55`); not a sub-processor today.

**Analytics:** none. No analytics or tag SDK is on main in the three app repos (grep for `@vercel/analytics`,
`speed-insights`, `gtag`, `googletagmanager`, `posthog`, `mixpanel`, `plausible`, `hotjar`, `clarity`, `amplitude`:
0 hits, 2026-10-21). Both privacy pages say "no advertising or analytics cookies", which matches.

Notes:

1. **Sentry and personal data.** `send_default_pii=False`, request bodies and cookies dropped, headers reduced to an
   allowlist, key-like query values redacted (CIS `shared/sentry_init.py`). The init does not set
   `include_local_variables`; the Python SDK's default attaches stack-frame local variables, which can hold a staff
   e-mail or tenant text. To confirm against the SDK docs and decide (CIS code follow-up). The admin UI SDK
   (`frontend/sentry.client.config.ts:3-8`) sends only when its DSN variable is set on Vercel; not checked here.
2. **TripPlanner and CIS.** TripPlanner photo URLs point at the CIS public API (TP `backend/config.py:45`), so a
   traveller's browser sends requests to a Sentry-instrumented process. Sentry collects no IP by default.

### Page copy follow-ups (app PR, not this register)

The live draft pages were compared with this list on 2026-10-21 (TP `c497489`, CIS `6e00458d`):

| # | Page | Gap | Owner repo |
|---|---|---|---|
| 1 | TripPlanner and portal `/privacy` §6 | Sentry is not named (portal requests reach the CIS api; TripPlanner photos load from it) | TP, CIS |
| 2 | Portal `/privacy` §5 | "The full list of AI providers is [to be confirmed]": the list is above (Bedrock with Claude and GPT models, OpenAI API last resort, Jev) | CIS |
| 3 | TripPlanner `/privacy` §6 | The mail host of the staff inquiry inbox (DreamHost, if adventure.asia) is not named `[to be confirmed]` | TP |
| 4 | TripPlanner `/privacy` §6 | "The full list of service providers will be kept in a register [to be confirmed]": the register exists (private); the page could offer the list on request | TP |
| 5 | CIS code, not copy | Sentry `include_local_variables` (note 1) | CIS |

### Tenant CRM (placeholder)

Added by the CRM legal track (DM-6.8) when the CRM design is approved: messaging providers (Twilio or 360dialog,
Meta), e-signature, Stripe, and the calendar providers (Google, Microsoft) for book-a-call with calendar sync. Not
listed until then.

## (c) Decisions log

| Date | Decision | Who | Evidence |
|---|---|---|---|
| | | | |

Ms. Thư's decisions on the [readiness packet](readiness-packet.md) are recorded here, one row each.

## (d) Data-subject requests log

One row per access, correction, deletion, objection or consent-withdrawal request, written the day it arrives
([DSAR and erasure runbook](dsar-erasure-runbook.md) step 1.2). **No name, e-mail or phone here:** refer to the mail
thread by its date and subject.

| Received | Type | Mail thread (date, subject) | Identity checked | Answered | Erasure run (retention log row) |
|---|---|---|---|---|---|
| | | | | | |
