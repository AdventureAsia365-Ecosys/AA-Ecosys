# Tenant CRM (AA-821 / Jira PR-19): how it fits the current platform

> Raw research note from the S245 workflow (research lane 1), kept as returned. One edit: a Cognito user-pool ID
> was replaced with `<external-pool-id>` (docs rule: no pool IDs in prose). This note was written before the S245
> "complete product, no MVP" decision, so its v0/v1 split (§4, end) is superseded by the design in `../README.md`.

Research only. No files, Linear, Jira or Notion were changed. Sources were read on 20/10/2026. Paths are relative to `/home/nghiep/projects/AA-Ecosys` unless noted. Jira PR-19 was not opened directly; its content comes from the AA-821 comments of 18/10 and 19/10.

## 0. What the CRM has to be, as recorded

- **Product direction (S243, 19/10):** the CRM sits inside the tenant portal (`portal.lumiguides.it.com`, AA-885) and serves the tenant's own B2C customers. It is not a separate product. Ms. Thư dropped the 40-week plan; we research and re-plan "MVP-first". Sources: AA-821 comments 62495471 and 17d43815; `docs/sessions/2026-10-19-S243-platform-block-portal-ops-cognito-e2e-x1-s18-s19.md` lines 24–25 and 152.
- **Backlog slot:** "AA-821 Tenant CRM re-plan … later | After M1 | Approve the plan with Ms. Thư" (`docs/backlog/README.md:123`). M1 is the platform close-out: X1, the Cognito cutover and removing the CIS→Booking bridge (`docs/audits/2026-10-19-S244-master-plan/README.md:42`).
- **Rules already written down for the CRM:** ADR 0008 §8 (`docs/adr/0008-new-app-integration-and-data-platform-rules.md:163-175`), DM-6.8 (`docs/architecture/data-standards/02-data-management.md:214`), KEY-6 (`docs/architecture/data-standards/01-engineering.md:202-211`), and the worked example in `docs/audits/2026-10-14-S237-lane-backlog/data-architecture/README.md` §6.4 (lines 290–310).

## 1. What a CRM could reuse

| Need | What exists | Where | Reuse verdict |
|---|---|---|---|
| Portal shell and UI | Separate Next.js app `portal/` (Vercel `aa-cis-portal`) with a tenant-only BFF (`app/api/tenant/[...path]`), page gate in `portal/proxy.ts`, and a vendored UI kit (`DataTable`, `Drawer`, `csv.ts`, `savedViews.ts`). Existing pages: `dashboard, t0-brand … t11-publish, marketplace, billing, activity, settings, api` | `apps/AA-CIS-App/CONTEXT.md:40-100` | **Reuse directly.** A `/portal/crm/*` section fits. Kit files are byte-copies guarded by `tests/unit/test_aa885_portal_split.py` |
| Tenant identity (today) | One shared API key per tenant (`shared.tenants.api_key_hash`) → `/auth/tenant-login` → `cis_tenant_token` with role `tenant`. No per-person users | ADR 0006 line 27; `shared.tenants` (~4 rows on Dev) | **Not enough.** CRM data on a shared key gives no per-person audit |
| Tenant identity (target) | Cognito EXTERNAL `<external-pool-id>`, client `cis-portal`. Membership table "e.g. `shared.tenant_members` (tenant_id, user_sub, role owner/editor/viewer, status)" with an invitation flow | ADR 0006 decision 3 (lines 137–152) and Phase 3 (line 400); AA-813 (Backlog) | **Hard dependency.** The table does not exist yet: the schema reference has no `tenant_members` or `tenant_users`. AA-813's description still says password login plus `acp_shared.tenant_users` and needs rewriting to ADR 0006 Phase 3 (`docs/backlog/README.md:112`) |
| Tenant DB isolation | Tenant pool `acquire_scoped_conn` as `aa_app_user`, `SET LOCAL app.tenant_id`, RLS template (CIS 229), "no privilege without RLS" guard (CIS 241), routes fail closed (S241 D-12) | `apps/AA-CIS-App/CONTEXT.md` "Tenant DB role" (~line 935+); `api/core/aa544_tenant_pool.py`; tests `tests/integration/test_tenant_rls.py`, `test_007_rls_isolation.py` | **Reuse the pattern, not the role.** DM-6.8 / ADR 0008 put CRM data in its own schema `crm` with `crm_owner`/`crm_app`, not under `aa_app_user` or `cis_app` |
| Audit log | `acp_shared.audit_log`: append-only, hash chain (`chain_seq`, `prev_hash`, `row_hash`), `tenant_id`, `actor_type`, route/status (CIS 248, AA-884) | db-schema-reference lines 500–530 | **Reuse the design** for spec F5. A CRM-owned `crm.audit_log` on the same trigger template is safer than writing tenant-PII access events into a CIS table that `cis_app` reads across tenants |
| Job runner | Per-owner job tables on one template (ADR 0003a): `shared.job`, `booking.job` | ADR 0003a; DM-7.2 | **Reuse the template** as `crm.job` (`crm_` kinds) for reminders, nudges and TTL deletion |
| Pipeline / state-machine design | Booking `trip_case_status_transitions` plus a trigger rejecting illegal edges, `trip_case_status_history` written by trigger (`new_inquiry → discovery → building → proposal_sent → confirmed/cancelled`) | `apps/AA-Booking/CONTEXT.md:355-364`; bk-003 | **Copy the pattern only.** Booking tables carry no tenant/agency column (one "tenant" mention in all of Booking's CONTEXT, and it is in the legal section) |
| Lead → customer flow | `bk_inquiry_process` creates a **lead** customer (`verified=false`, `needs_merge_review`, `merge_candidate_id`, consent), a trip case, a notification and an audit row. Inbox is idempotent `booking.inbox_events UNIQUE (source, contract, idempotency_key)` with 90-day PII redaction (`bk_retention_inbox_redact`) | `apps/AA-Booking/CONTEXT.md:267-271`; `booking.customers` columns (schema ref lines 907–943) | **Copy the pattern only.** KEY-6 / DM-6.8 forbid the CRM from reading or writing `booking.customers` or `tripplanner.customers` (a different data controller) |
| Consent model | `contact_consent`, `contact_consent_at` on `booking.customers` and `tripplanner.customers` (DM-6.5) | schema ref; DM-6.5 | **Reuse the shape.** The S237 sketch upgrades it to an append-only `crm.contact_consent` |
| Catalog / tour interest | `catalog.v_tour`, `v_tour_day`, `v_tour_photo`, `v_destination`. Tour key `(source_system, source_id)` per ADR 0008 §9 | ecosystem-architecture §3.4 | **Reuse.** A deal or trip stores the soft key, never `tour_id` (S237 §6.4) |
| Tenant's own tour copy | `gold_aa_internal.tenant_tour_versions` (T2, ~48 rows), `acp_shared.content_piece`, `acp_shared.publish_log` (`external_url`, `channel`, `tenant_id`) | schema ref | **Reuse** to link "which piece or tour the lead came from", if attribution is added (see §3) |
| Channel integrations | `shared.tenant_integrations` (RLS; column grants to `aa_app_user`; secrets referenced in Secrets Manager); `/v1/integrations/{wordpress,facebook}` connect/test/disconnect | `api/routers/v1_integrations.py`; schema ref lines 3198–3222 | **Reuse** the connect/test/disconnect pattern for a later email inbox integration (spec module 5) |
| Brand CTA | `shared.tenant_brand_rules.default_cta` (CIS 220), published word for word | `api/migrations/220_*.sql:39-41`; CONTEXT ~1457 | **Hook point.** The CTA could carry a tenant lead-form link |
| B2B resale path into AA | ADR 0005 decision 9: tenants see a B2B net price list (15% margin) in the portal; bookings arrive through a B2B channel carrying `tenant_id`; AA invoices the tenant. `booking.pricing_rules.channel` already includes `b2b` | `docs/adr/0005-pricing-and-supplier-rates.md:74-77`; `apps/AA-Booking/CONTEXT.md:368` | **This is the natural CRM → AA hand-off.** Gated on "after AA-Booking can quote (AA-681)". No B2B endpoint exists yet |
| Webhooks | Portal API tab says "Coming soon"; the playground proxy allow-lists `/v1/webhooks`, but no API router serves it (only a mention in `api/migrations/002_schema_v2.sql`) | `portal/app/portal/_components/ApiTab.tsx:151-161`; `portal/app/api/playground/proxy/route.ts:13` | **Does not exist** |
| AI guardrails | Model Gateway plus `shared.llm_call_log`. DM-6.4: no identifying PII in prompts or logs. AA-820 AI-disclosure rule. Legal draft `docs/legal/tenant-terms-ai-clause-draft.md` | CIS CLAUDE.md; DM-6.4; Booking CONTEXT 532–538 | **Reuse as constraints** for any AI drafting |

## 2. Hard constraints

**Ownership and boundaries**
1. **Own schema `crm` and own key space** `crm-NNN` in `shared.schema_versions`. Roles: `crm_owner` NOLOGIN, `crm_app` LOGIN, optional read-only `crm_staff`. It is a CIS module for now so it can later move to its own repo without renumbering. Sources: ADR 0008 §8; DM-6.8; KEY-6; NAM-1. The registry entry goes in `infra/AA-CIS-Infra/db/owners.yaml` (schema-ownership.md lines 25–28). Migrations go through Infra DB Migrate only.
2. **No reads either way.** The CRM never reads `booking.customers` or `tripplanner.customers`. No AA app reads `crm.*`, including CIS code outside the CRM module. A hand-off to AA is a consented event (e.g. `crm.lead.handoff_requested.v1`), and Booking then creates its **own** customer (KEY-6; DM-6.8). Payloads carry `contact_id`, not contact details (DM-6.3).
3. **Preconditions before any CRM DSN exists** (ADR 0008 §8):

   | Precondition | State |
   |---|---|
   | ADR 0008 | Exists |
   | `owners.yaml` | Exists |
   | X2 RLS catalogue CI guard (AA-848) | Backlog, slot S250 |
   | AA-813 membership + view | Backlog |
   | N3 connection limits (AA-824) | Status not checked |

4. **"Tenant sees content only"** (DM-4.5): any AA-side QA or diagnostics of the CRM stay in admin.

**Isolation**

5. FORCE RLS from day one for a new app (DM-8.4), NULLIF template `TO crm_app` with WITH CHECK. Fail closed when there is no tenant context. `app.tenant_id` is set only after the app's own membership check (DM-8.4: a self-set GUC is not an authorization boundary).
6. **AA-817 is Done, and X1 moved the CIS runtime to `cis_app`.** Per the role table in `db-schema-reference.md` (~line 3887), `cis_app` has no `pg_read_all_data`. However, CIS tables carry `<table>_cis_app_all USING (true)` policies (e.g. `tenant_integrations_cis_app_all`). So **CRM tables must not be granted to `cis_app` at all.** The CRM module needs its own `crm_app` DSN even though its code sits in the CIS API process. `aa_cis_admin` (RDS master, `rds_superuser`) can still read everything, but it is break-glass only (DM-8.9). The caveat "until the role split, `aa_cis_admin` reads `crm.*`" in DM-6.8, KEY-6 and SEC-12 should be reworded: the runtime gap is closed, and the residual risk is master break-glass.
7. **Connection budget.** `max_connections` is 181. LOGIN limits today: `cis_app` 90 + `aa_app_user` 15 + `booking` 15 + `tripplanner` 30 + `db_migrator` 5 = 155. A `crm_app` at 10 (S237 sketch) brings this to 165. That is within the limit but tight, and must be set in git (DM-8.5; `03-scaling.md` C2.2–C2.3).

**Identity**

8. Tenant users sign in on the EXTERNAL pool through `cis-portal`, with email code by invitation. The membership table in CIS is the security boundary, never the token (ADR 0006 decision 3, lines 137–150).
9. **The EXTERNAL pool is shared** by tenant users and AA's own travellers, with one managed-login session across EXTERNAL clients (ADR 0006 lines 43, 97–98, 148–150).
   - If a tenant's B2C clients got accounts (spec module 11 "client portal"), they would sit in AA's traveller pool under AA branding (`auth.lumiguides.it.com`, ADR 0006a A5). AA would then hold their identity, which works against the controller split.
   - **Constraint for the MVP:** CRM travellers get no Cognito accounts. Use signed, expiring links instead. A separate tenant pool is the documented fallback (ADR 0006 Open item 4 / "Three pools" alternative).
10. Cognito custom attributes are permanently fixed once added, so none should be added for the CRM (ADR 0006 line 65).

**PII, consent, retention**

11. Every PII column gets `COMMENT ON COLUMN … 'pii:<class>'` (DM-6.1). Existing classes do not cover passport or government ID, or health/dietary/mobility data (a GDPR special category). The spec's Stage 3 and health flags need new classes plus an amendment to the standards.
12. No identifying PII in LLM prompts, Jev or `shared.llm_call_log` (DM-6.4). No automated PII check exists or is planned (DM-6.4 open point, `02-data-management.md:364`). The spec's F3 scrubber would be new work.
13. Consent stored with value, timestamp and source, checked before marketing (DM-6.5). Retention is per tenant, with hard delete on erasure or offboarding (DM-6.8). Retention-registry row in the same PR (DM-7.1). Owner-run TTL job, DRY RUN on the first run (DM-7.2).
14. A DPA template is required before the first tenant (DM-6.8). The legal draft lists "Is AA a controller or a processor for each kind of record?" as open (`docs/legal/tenant-terms-ai-clause-draft.md:304`).
15. Any new AWS service (e.g. a KMS key per tenant, Presidio hosting, SES inbound) needs a cost quote and Nghiệp's approval (DM-10.7; DM-10.1 `App=crm` tag).

## 3. Where a tenant's lead originates today

**Short answer: tenant channels capture no leads into the AA platform today. Every enquiry lands in the tenant's own systems, or with AA by accident.**

- **T11 publish.**
  - **What publishes automatically:** blog posts go to the tenant's WordPress, and Facebook posts go to their Page feed (`POST /{page_id}/feed`). Sources: `api/routers/v1_publish.py:27-31,73`; `services/acp_publish/facebook.py:12`.
  - **Source drift:** CIS `CONTEXT.md:1621` says "blog Channel only today", but the code also publishes Facebook (AA-462).
  - **Other channels:** the remaining 6 (linkedin, instagram, tiktok, email, landing_page, ads) are export / copy-paste only.
  - **What AA records after a publish:** `acp_shared.publish_log` stores only `external_id` / `external_url`. There are no click, UTM or form-submission columns (schema ref). The Facebook adapter only posts and reads the Page feed: no Messenger, comments or Lead Ads access.
- **The CTA is plain text.** `tenant_brand_rules.default_cta` is published word for word. Any reply (a WP contact form, a FB comment or Messenger message, email) goes to the tenant's own inbox. AA never sees it, and nothing ties it back to the piece.
- **The AA-hosted white-label trip page** `/v1/trip/{tour_id}` → `frontend/app/trip/[tourId]/page.tsx`:
  - It serves only AA master content (`published_tours`), not the tenant's T2 version (router docstring, `api/routers/v1_trip_page.py:1-45`).
  - Its only CTA is a hardcoded `mailto:admin@adventureasia.com` (page.tsx ~line 146). A visitor from a tenant's channel would email AA, not the tenant, which is a cross-controller leak in the wrong direction. Note too that AA's domain elsewhere is `adventure.asia`, so the mailto domain may be wrong; worth verifying.
  - `acp_deliver.tenant_tour_pages` holds ~0 rows (schema ref line 372), so in practice no tenant pages are live.
- **TripPlanner** is AA's own B2C front door with no tenant concept (`apps/AA-TripPlanner-Web/CONTEXT.md:17`). Its inquiries become **AA's** leads in Booking (`booking.customers.source = 'tripplanner_lead'`). A tenant receives nothing from it.
- **Webhooks** to the tenant: "Coming soon" in the portal, no router.
- **Unknown:** what tenants use today (Gmail, WhatsApp, a CRM of their own), how many real tenants exist (Dev `shared.tenants` ~4 rows, including the `aa_internal` sentinel and test tenants), and lead volumes. AA-821 research question 1 ("validate with 2–3 tenants") is still unanswered.

**What this means for design:** a CRM MVP needs its own capture path before a pipeline UI is worth anything. The cheapest options, building only on what exists:
- a hosted tenant lead form (or a CIS endpoint called with the tenant's `X-API-Key` plus an idempotency key, as S237 §6.4 suggests), linked from the tenant CTA and the white-label page;
- an embeddable form for the tenant's WordPress;
- manual entry and CSV import.

## 4. Critique of `partner-crm-spec.md` against the S243 decision

**Where the spec fits:**
- The audience matches: agencies managing their own B2C, with "traveler data belongs to the agency" (§2).
- The tenant-as-controller principle and the k≥10 aggregates match DM-6.8 and KEY-6.
- The "privacy foundation before any traveler data" order matches ADR 0008's preconditions.
- Stage-gated data collection ("never ask earlier what is needed later", bands not numbers) is good minimisation (DM-6.3).
- The pipeline stages map cleanly onto a Booking-style transition table.

**Where it conflicts or overreaches:**

1. **Scope and plan.** The spec has 5 foundation modules plus 18 feature modules over ~40 weeks with 2–3 developers (§10). Ms. Thư explicitly dropped this. It also assumes a dedicated team; this program is one engineer plus agents running 3–5 issues per session.
2. **It reads as a standalone product, not a portal module.**
   - **Spec assumes:** its own users and roles (owner/agent/assistant, F4), its own tenancy, its own client portal, supplier directory and reports.
   - **What already exists:** portal tenancy and the planned AA-813 roles (owner/editor/viewer).
   - **The fix:** reuse those roles. Add an "assistant / no-margin" permission only if tenants ask for it.
3. **"AA never sees who a traveler is" / F1 "encrypted with the agency's own key, no access outside the agency, AA included".** Not achievable as written:
   - AA runs the app and the RDS, and the master `aa_cis_admin` has `rds_superuser`.
   - Agency-held keys would mean customer-managed KMS or client-side encryption per tenant: new cost (DM-10.7) and real complexity, with no search on encrypted fields.
   - The data standards define the realistic bar: AA as processor with RLS, no grants, a break-glass log, an audit trail, plus a DPA. The spec should promise that instead.
4. **F2 pseudonymous profile plus F3 Presidio scrubber plus the AI layer (module 14)** are a large privacy-engineering track. DM-6.4 already bans identifying PII in prompts. An MVP can avoid sending traveller data to an LLM at all. AI drafting also triggers the AA-820 disclosure and human-review rules and the pending legal Terms.
5. **Module 3 "live AA supply, net rates, availability, hold/confirm"** depends on things Booking does not have:
   - Booking has no availability or hold model. Rates are contract net rates entered one by one, and the price matrix / `v_from_prices` are out of scope (`apps/AA-Booking/CONTEXT.md:518-526`).
   - ADR 0005 decision 9 resale waits on Booking quoting (AA-681).
   - **Verdict:** the spec's main differentiator is blocked on Booking. It is phase 2+ at best, and should go through a Booking B2B API carrying `tenant_id`, not CRM reads of `booking.*`.
6. **Module 8 "AA ops release, deleted 90 days after trip"** is effectively the ADR 0008 consented hand-off event. It should be specified as a versioned contract in `docs/contracts/` with Booking creating its own customer, not as AA reading CRM rows.
7. **Module 11 client portal, module 12 e-sign, module 7 Stripe, modules 5/9 Gmail/Outlook/WhatsApp sync** each add a vendor, a DPA and a cost line. None is MVP for "manage B2C customers inside the portal". The identity constraint in §2 item 9 argues for signed links, not traveller accounts, if a client view is ever built.
8. **Stage 3 passport, DOB and health data**: high-risk categories with no `pii:` class, no retention row and no erasure runbook (DM-6.7 covers Booking and TP only). Defer until there is a real ops need (module 8).
9. **Missing from the spec:**
   - Lead capture from the content AA already generates for the tenant: T9/T11 attribution via `publish_log` / `content_piece`, a CTA link and form. That is the one advantage only this platform has.
   - The fact that tenants today receive enquiries outside AA (§3).
   - Build vs integrate (HubSpot/Zoho/Pipedrive export or webhooks), which AA-821 research question 2 asks for and ADR 0008 keeps open ("if HubSpot/Zoho is chosen, only `crm.integration_link` + an outbox").
   - Per-tenant retention defaults and the offboarding hard-delete path.
   - Which membership plan includes the CRM (AA-821 question 6).
10. **Dependency ordering the spec does not see:**
    - M1 platform close-out (backlog).
    - AA-813 tenant users and membership (M5 security order #1, "before the first paying tenant").
    - X2 catalogue guard AA-848 (S250).
    - N3 connection limits.
    - A DPA template.
    - The tenant Terms (`docs/legal/tenant-terms-ai-clause-draft.md`).

    No CRM table can ship before AA-813 and X2.

**Smallest scope consistent with S243 and the standards** (for the re-plan; this is a proposal, not decided):
- **v0:** contacts plus consent, manual entry and CSV import/export, notes and interactions, a simple deal/stage board keyed to the catalog tour soft key, and a hosted lead form linked from the tenant CTA. Built on schema `crm`, FORCE RLS, `crm_app`, AA-813 membership, per-tenant retention and hard delete, and an audit trail.
- **v1:** content attribution (piece / publish_log → lead), reminders and nudges via `crm.job`, a consented hand-off event to Booking.
- **Later:** B2B quoting through Booking (ADR 0005 d9), email sync, client links, AI drafts.

Each step should also be checked against the "integrate HubSpot/Zoho instead" option.

**Source drift found while reading** (for whoever updates the docs):
- `docs/ecosystem-architecture.md:340` still lists Booking staff Cognito as "Phase 2, not started", while S243/S244 shipped the AA-680 staff half.
- DM-6.8, KEY-6 and SEC-12 still describe `aa_cis_admin` runtime access to `crm.*` as an open gap, but X1 S18/S19 is done.
- CIS `CONTEXT.md:1621` says T11 is blog-only, but the code also publishes Facebook.
