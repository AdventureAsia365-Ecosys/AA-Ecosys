# ADR 0019 — B2B-only ecosystem model: Adventure Asia sells to tenants only; Content is the base product, CRM and TripPlanner are add-ons, Booking is the B2B back office

- **Status:** **Accepted** (tech lead, S265, 03/11/2026) for the invariants and technical decisions d1–d23. The S265 decision page recorded all 44 items. 40 follow the recommendation. Four take another option: d6 `merge_now`, d9 `all_in_booking`, d16 `all_on_dev` and d23 `move_tp_to_ecs`. Items b1–b21 are **business decisions taken by the tech lead on the decision page (S265); the business owner may revisit** them. A change there updates this ADR. It does not reopen d1–d23.
- **Context source:** the meeting of 02/11/2026 that settled the B2B-only model.
- **Design and evidence:** [`docs/audits/2026-11-03-S265-ecosystem-restructure/README.md`](./README.md) (sections 1–13), `decisions.json` (options and trade-offs), `approvals.json` (choices and notes) and [`clarifications.md`](./clarifications.md) (answers to the approval notes, the redesign for the four other choices, the staff role matrix, TripPlanner hosting cost, the prod plan and the revised order), all in that folder.
- **Amends:** ADR 0001, 0004, 0005, 0005a, 0006, 0010, 0010a, 0016 and 0018. Each one gets a one-line pointer to this ADR (see [ADRs amended](#adrs-amended)). It extends ADR 0015 (d20) but does not change any of its decisions.
- **Respects, unchanged:** ADR 0002 (only CIS writes content), 0003/0003a (job tables per owner), 0006b d4 (a CIS event never grants a CRM role), 0008/0008a (no fifth app; the CRM keeps its own gateway), 0009 (gateway route order), 0010 d9 (bring-your-own integrations), 0017 (migrations in the app PR). It also keeps the standing rule that every new paid service needs its own yes, with the monthly cost stated first.
- **Scope:** every repo: AA-CIS-App, AA-Partner, AA-Booking, AA-TripPlanner-Web, AA-CIS-Infra and root.
- **Related Linear:** AA-1028 (becomes R1), AA-1016, AA-1029, AA-1030, AA-1007, AA-1008, AA-1004, AA-820, AA-969, AA-1005 and AA-703 (both re-scoped), AA-990, AA-1003, AA-855, AA-965.

## Context

Until now the ecosystem served two audiences. TripPlanner was a B2C front door under the Adventure Asia (AA) brand. Its leads became AA-owned B2C trip cases in Booking, and Booking held raw traveller PII. On 02/11/2026 the business settled one model: **AA sells only to partner agencies (tenants)**, sells no tour it does not operate, and keeps no end-customer data of its own.

The S265 audit found that the codebase already has most of the pieces: tenant RLS, the partner pool with MFA, the CRM vault, catalog contracts and tour liveness (ADR 0015). Four things are wrong for the new model:

- **One agency, three records.** An agency lives in `shared.tenants`, `crm.tenant` and `booking.b2b_partners`. Creating one takes seven manual steps across three UIs. There are three status vocabularies and three sets of plan names.
- **No tenant in TripPlanner.** TripPlanner has no `tenant_id`, and its leads become AA B2C cases.
- **Staff roles are too coarse.** `shared.admin_role` is `admin`, `reviewer`, `content` or `viewer`, so all tenant, money and AI work requires `admin`. Nothing assigns tenants to an account manager.
- **The CRM can sell non-AA products.** It allows agency-owned suppliers, tours included.

## Decision

### Invariants

1. AA sells to tenants only. After cut-over, no app creates an AA-owned end-customer record.
2. The tenant is the **controller** of end-customer data and AA is the **processor**, on every app. This extends ADR 0008a d1 from the CRM to the whole platform.
3. Anything a tenant shows or sells that refers to a tour or experience points to a **live** AA `tour_id` or atom (ADR 0002, 0015).
4. Tenants see content only. QA, held items and flags stay in AA Admin.
5. Mail, payments and messaging run on the agency's own accounts (bring-your-own).
6. Apps check **feature keys**, never plan names.

### Technical decisions (tech lead; dN answers TL-N)

**d1 Control plane in CIS `shared` (TL-1).** The CIS `shared` schema is the master for the tenant account, lifecycle, plans, subscriptions, entitlements, staff assignment and `data_region`.
- `crm.tenant` and `booking.b2b_partners` become read-only projections of the CIS master. CIS is the only **source**: no app edits account, lifecycle or plan data locally. Each app's own pull job writes its own projection: AA-Partner `crm_entitlement_pull` writes the CRM side, and Booking `bk_tenant_pull` creates and updates `booking.b2b_partners` (owned by `bk_owner`).
- New in R1: columns on `shared.tenants` (`account_status`, `suspend_reason`, `data_region` default `'us'`, `kind`, `time_zone`, billing fields) and the tables `shared.plan`, `shared.plan_feature`, `shared.tenant_subscription`, `shared.tenant_entitlement`, `shared.tenant_entitlement_override` and `shared.tenant_account_event`.
- Creating a tenant becomes one action: the `tenant_provision` saga on `shared.job`.
- "Booking only manages tenants (B2B)" means Booking does only B2B work with tenants. It does not hold the tenant master record.

**d2 Feature keys (TL-2).** Entitlements are materialised in `shared.tenant_entitlement` and published as the new contract `tenant.entitlements.v1`.
- The contract has three parts: the view `shared.v_tenant_entitlement_v1`, `GET /tenant/v1/tenants/{id}/account` and an account-event feed.
- Consumers pull it: CRM `crm_entitlement_pull` and Booking `bk_tenant_pull`. TripPlanner reads the view.
- The hard-coded `PLAN_LIMITS`, the 10/10/50 quota ledger and the UI `PLAN_OPTIONS` are retired. `ai.budget_usd_monthly` replaces the stand-alone budget rows (closes AA-1016).

**d3 Staff roles (TL-3).**
- `shared.admin_role` gains `content_lead`, `tenant_qa`, `customer_success`, `support`, `finance` and `ai_ops`. `ALTER TYPE` runs in its own migration.
- `reviewer` merges into `content`. The same CIS migration fixes `admin_users_email_chk`, and the `cis-reviewer` group stays as an alias for one release.
- `shared.staff_app_grant` and `shared.staff_crm_grant` stay. Booking `sales` now means the agency desk.
- Booking gains a `finance` role (d9). This takes three changes:
  - a **CIS** migration adds `'finance'` to `staff_app_grant_role_chk`. The check is on `shared.staff_app_grant` (owner `cis_owner`), which `schema-ownership.md` gives to CIS, so Booking may not migrate it;
  - Infra adds a Cognito group `booking-finance` in `identity.tf` (proposed precedence 75, between `booking-content_creator` 70 and `crm-platform-admin` 80);
  - Booking reads the role from `cognito:groups` or the bridge token, like its other roles, and gates the invoice and payment routes with it.
- The full role table and permission matrix are in `clarifications.md` section 3.

**d4 Tenant scope enforced on the server (TL-4).**
- New `shared.staff_tenant_assignment` (owner, backup or support; one owner per tenant).
- Every `{tenant_id}` route uses the `require_tenant_scope` dependency. A CI test checks that every such route uses it, and an isolation probe runs against it.
- The `crm.ops.v1` relay forwards the staff member's scope. `admin` bypasses scope.
- This is an auth change, so it gets an independent review.

**d5 Support access (TL-5).** "View as tenant" is read-only, lasts at most 60 minutes, requires a reason or ticket, shows a banner and is logged in `shared.staff_view_as_session`. Staff reach end-customer PII in the CRM only through `crm.support_grant`, which the tenant owner grants.

**d6 One agency app now (TL-6, chosen over `keep_crm_host`).** In R3, AA-Partner `portal/` merges into `web/` as one Next.js app with route groups for studio, CRM and planner.
- The `aa-crm-<env>-portal` service is removed after the cut-over.
- People sign in one way only: the partner pool with MFA, through one session owned by the merged app.
- API-key sign-in for people (`/tenant-login`, `PORTAL_API_KEY_SIGNIN`) is removed in the same release, which brings forward ADR 0010a d5's clean-up.
- All tenant API-key code and data go too:
  - CIS `POST /auth/tenant-login`, which has two handlers: `api/main.py:385` (not marked deprecated) and `api/routers/auth.py:163` (`deprecated=True`). Before removal, 30 days of `audit_log` are checked for callers.
  - `verify_tenant_api_key` (`api/routers/auth.py:267`; no route depends on it), the dead Lambda authorizer, the key issue / rotate / restore code in `api/routers/admin.py`, and the API-key card in Account.
  - `shared.tenants.api_key_hash` is set to NULL, then dropped under the destructive-ops DRY RUN.
  - Offboarding moves from the `REVOKED_` key marker to `account_status` (d1).
- **Consequence:** the only machine path an agency has to `/v1/*` today is the 24-hour JWT from `POST /auth/tenant-login` (`X-API-Key` is not wired to any route). Removing it ends all agency machine access to `/v1/*` until R8.
- **Stays:** AA-internal M2M. AA-Partner calls `booking.b2b.v1` and CIS `tenant.membership.v1` with `aa-m2m` client credentials. That is AA machines calling AA machines, not a tenant key.
- **Deferred to R8:** a machine API for agencies (higher tier, b4), built only when a paying tenant asks, with scoped, rotatable credentials and its own cost yes.
- The CIS tenant-session exchange stays as a server-side call, now inside the one app, so the byte copies of `portal/lib/session.ts` and `seal.ts` go.

**d7 One invitation carrying a role map (TL-7).**
- An invitation sent through the AA-Partner API carries `{"content": …, "crm": …}`. The `crm` key is valid only when the tenant has `crm.core`.
- The CRM role is written to `crm.member` by the tenant owner or admin's own action. This keeps ADR 0006b d4.
- `shared.tenant_members` and `crm.member` stay separate records.
- A tenant always lands on Content. Add-ons open per entitlement or after a "Request" to the account manager.

**d8 Booking's B2C part: freeze, port one gap, drop (TL-8).**
- Now: a feature flag plus `REVOKE INSERT` on `booking.customers` and its customer tables.
- `booking.trip_cases` gets a `b2b`-only CHECK (`NOT VALID`, then validated).
- One slice is ported to the CRM: maker-checker for manual payments, optional per tenant.
- The tables are dropped later under the destructive-ops DRY RUN procedure.
- S253 "build every Figma screen" is reversed for the B2C screens. Supply, pricing, ops and B2B screens stay, and Partners and Settlement are added.

**d9 Every invoice is issued from Booking (TL-9, chosen over `manual_split`).** Booking issues both SaaS subscription invoices and tour settlement invoices to agencies.
- **New tables (bk migration):**
  - `booking.agency_invoice`, keyed by `party_tenant_id`, with `invoice_kind` ∈ `saas`, `settlement`, period, currency, tax, status, `e_invoice_no` and a bill-to snapshot.
  - `booking.agency_invoice_line`, with a CHECK that every line has its invoice's kind, so software fees and tour money never share an invoice (b17).
  - `booking.agency_payment`: maker-checker (recorder ≠ approver), evidence required.
  - `booking.invoice_sequence`: gap-free numbers, one series per kind (`AAS-` software fee, `AAT-` tour settlement).
  - `booking.billing_entity` (AA's issuing legal entity, b10) and `booking.tax_rule` (tax and footer wording as data, b17).
- `booking.invoices` stays B2C-only (`bill_to_kind` is `'customer'` only, `trip_case_id` NOT NULL) and is frozen with d8.
- **Bill-to legal fields** (legal name, tax ID, billing e-mail) live on `shared.tenants` (CIS is master, d1). Booking takes a snapshot of them into the invoice when it is issued.
- **Every tenant**, Content-only included, gets a `booking.b2b_partners` projection row from `bk_tenant_pull`. `m2m_client_id` is AA-Partner's client, not a per-tenant one, so the row can exist for any tenant. d17 needs it too.
- **Jobs:** `bk_saas_invoice_draft` (start of period, lines from the subscription in `tenant.entitlements.v1`) and `bk_settlement_draft`.
- **Paid-through:** Booking publishes `booking.v_tenant_billing_status` (`paid_through`, `overdue_amount`). The CIS `tenant_billing_tick` job reads it and moves the subscription status. CIS stays the only writer of subscription state.
- **Role:** `finance` (d3).
- **Screens now:** a "Trade" group in the AA Admin nav opens Booking admin through the app switcher (same WORKFORCE sign-in), and Tenant 360 gets a read-only Billing tab with "Open in Booking". Merging the Booking screens into the CIS frontend is deferred to R8, after the B2C screens are gone.
- **No paid service:** invoice documents are generated in the system and payment is marked by hand (b14).

**d10 TripPlanner rebuilt in place (TL-10).** TripPlanner gets `tenant_id NOT NULL` with ENABLE and FORCE RLS, after a backfill to a demo tenant and one shadow deploy.
- The tenant comes from the path `/{slug}` on the existing host, plus a launcher button. CSP stays `frame-ancestors 'none'`.
- Tenant configuration comes from `catalog.v_tenant_tripplanner_v1` and tours from `catalog.v_tenant_tour_v1`.
- Subdomains, custom domains, iframe embed and a headless API come later, each on its own trigger.

**d11 Travellers are guests; leads go to the tenant (TL-11).**
- A traveller is a guest (cookie) and gives an e-mail when they submit. They return through the CRM client-portal link.
- Leads travel on the new `lead.submitted.v1` into CRM intake. A tenant without the CRM gets a signed webhook or an e-mail.
- `inquiry.submitted` and `bk_inquiry_pull` run in parallel for one release, then stop. The EXTERNAL clients `tripplanner` and `booking-customer` are frozen.

**d12 Region field and PII class (TL-12).**
- `data_region` exists from R1.
- Each gateway stage declares a `pii_class`: PII routes to `us`, and content may route to `global`.
- An EU cell is built only on a trigger: (a) a signed contract requires EU hosting; (b) about 3–5 paying EU tenants bring about 3× the cell's cost; or (c) a legal shock in which SCCs plus the transfer impact assessment (TIA) no longer hold.
- No "AI processed in the EU" claim is made while Bedrock LLMs are blocked.

**d13 AA Admin information architecture (TL-13).** The admin nav becomes Home, Tenants, AA Catalogue, Tenant QA, AI & spend, Writing Lab and Platform. Writing Lab only regroups the UI over the existing tables. The S262 TL-11 freeze on learning logic stays, and is lifted per stage later. Old URLs redirect.

**d14 Repos and records (TL-14).** The six repos stay, with no monorepo and no fifth app. This ADR plus pointer lines in the amended ADRs record the change. Each repo rewrites its `CONTEXT.md` in R0 or R1.

**d15 Order (TL-15).**

Sizes after the four other choices: R3 6–7 sessions of work (merge and key removal 3, studio i18n 2–3, the rest of the old portal-shell scope about 1), R4 3–4, R5 4–6 (the ECS move included). R0–R8 total about 32–39 sessions, up from 25–30; the prod plan (8–10 sessions) is counted separately.

| Slot | Work |
|---|---|
| S265 | R0; close the gateway items In Review; AA-820 |
| S266–S268 | R1 (AA-1028 moved up) |
| S268–S272 | R3: merge and key removal S268–S270; studio i18n on a parallel lane S269–S272 (+AA-1007, AA-1008) |
| S269–S271 | R2 with the Booking `finance` role (parallel lane); AA-969 |
| ~S272 | **Pilot milestone 1:** Content + CRM, after R1, the R3 merge, R2 and AA-969 |
| S271–S274 | R4 (+AA-1029, AA-1030) |
| S272–S277 | R5 |
| ~S277 | **Pilot milestone 2:** TripPlanner, after R5 |
| S277–S280 | R7 |
| Parallel lane | R6 (with the d20 e-mail); d19 before 02/12/2026; P0 of the prod plan |

- **Paused:** AA-960, 963, 968, 970, 980; AA-1003, which is re-scoped.
- **AA-965** waits for b6.
- **Kept:** AA-969, AA-1024…1027, AA-820, AA-896, AA-873.

**d16 Pilot on Dev with real data (TL-16, chosen over `content_dev_crm_prod`).**
- The first pilot runs on Dev and covers Content, CRM and TripPlanner as one end-to-end trial with real agency and traveller data. This amends ADR 0018 d2 and data standard C7.1a as a **time-boxed exception**:
  - **One tenant only**, with `kind='agency'` and a pilot marker (feature key or column, settled in the R1 migration).
  - **At most 8 weeks, or until `aa-prod` exists**, whichever comes first.
  - The pilot letter says "test environment, no SLA" and comes with a DPA. The business owner settles the wording.
- **Before any real PII** (all zero cost):
  1. AA-969 (CRM security review) is done.
  2. A hook blocks agents and DB Migrate `run-script` from reading the pilot tenant's PII rows; scripts print counts only, because the Infra repo's CI logs are public.
  3. Every clean-up, E2E and wave job skips the pilot tenant.
  4. A nightly per-tenant export of the pilot tenant through `crm.export_job`, so one tenant can be restored on its own.
  5. Traveller PII stays in the CRM vault under RLS; destructive work follows DRY RUN; RDS automated backups stay on.
- **Caveat:** PITR restores the whole database of all four apps, never one tenant. No instance-wide PITR runs without telling the pilot agency first; per-tenant recovery uses the nightly export.
- **Optional, paid:** raising RDS backup retention from 7 to 14 days (under 1 USD a month) needs its own yes.
- **Two milestones** (d15): Content + CRM at about S272, after R1, R3, R2 and AA-969; TripPlanner at about S277, after R5.
- **Exit:** the six-phase prod plan (P0–P6, about 8–10 sessions) in `clarifications.md` section 5. P0 (module split with `moved` blocks, 0 USD) runs early on a parallel lane; P2–P6 start when the business owner sets the go-live date (b18), before the first paying tenant.

**d17 "Book with AA" for Content-only tenants (TL-17).**
- A tour page in Content gets a quote/hold form. It calls `booking.b2b.v1` through the AA-Partner API under the tenant's identity, and the request lands in Booking's Agency desk.
- A "Bookings with AA" page shows status and settlement invoices.
- E-mail to the agency desk is the fallback.
- A public B2B API opens only when a tenant asks for it.

**d18 Anthropic switched on stage by stage (TL-18).** The ADR 0009 route order stays. The Anthropic key goes live in this order:
1. `s1_generate` and `place_card` (AA content).
2. The tenant writing stages, after AA-820 (b20).
3. `tp_compose`, after the per-tenant AI cap.
4. `crm_draft_reply` last, on geo `us`.

Each step goes shadow → 3 tours → at most about 50 tours, and reports cost per tour. The judge keeps the OpenAI API as its warm path, in a family different from the writer's.

**d19 AI notice (TL-19).**
- One AI-notice component in the kit, used by TripPlanner chat and narration, the CRM AI draft and the "AI-assisted" label in Content.
- `ai_generated`, model and date metadata go on CIS exports, `/v1/*` and published WordPress pages.
- Done before 02/12/2026. That date for EU AI Act Art. 50(2) comes from secondary sources and has not been checked against the official text.

**d20 Retired tours fan out (TL-20).** CIS emits `catalog.tour_liveness_changed` (append-only). Each consumer then:

| Consumer | Behaviour |
|---|---|
| TripPlanner | Hides the tour at once |
| Pending publish items | Cancelled |
| WordPress | Tenant notice plus a flag; the page goes to draft after the notice period (default 7 days, b7) |
| Facebook | Notice plus a flag; nothing is deleted |
| CRM | The line is marked and the agent gets a task |
| Booking | New holds are blocked; confirmed bookings stay |

Flags show only in Tenant QA › Compliance.

Tenants are told on two channels:
- **In the portal:** already built (`tour.discontinued` in `shared.notifications`, the bell).
- **E-mail through SES (R6):** sent at once when a `retired` tour still has live pages or posts for the tenant; otherwise folded into a daily digest. Recipients are the owner and the content members. The mail names the tour, the stop date, what the system already did, when the WordPress page goes to draft, which Facebook posts to edit, and a replacement tour if any. A `restored` tour gets a "back on sale" mail; a `paused` tour gets no mail. Wording is content-style, never "flag" or "QA".

**d21 Content gate without an LLM (TL-21).** When a piece is created and again before it is published:
- Every piece must link to at least one AA subject: a live tour, an AA atom or place, or brand content with no sales CTA.
- Sales links and CTAs may point only to AA tour pages or the tenant's TripPlanner site.
- A piece that fails is held in Tenant QA › Compliance, and the tenant sees a content-style reason.

**d22 Localisation (TL-22).** One message catalogue in the kit, with English and Vietnamese by default. The Content studio has no i18n today, so extracting its strings into the catalogue (2–3 sessions) moves into R3, together with the d6 merge. Opening the kit beyond `en`/`vi` and adding languages come in R8, after R5; machine translation tokens need their own yes. `shared.tenants.time_zone` (IANA) plus a per-user zone, with storage in UTC. A per-tenant `display_currency` for display; AA invoices stay in USD unless the contract says otherwise.

**d23 TripPlanner frontend moves to ECS (TL-23, chosen over `pro_now`).**
- The Next.js frontend becomes a Fargate ARM service (0.5 vCPU / 1 GB) in the existing cluster, behind the shared ALB, following the `aa-crm-<env>-portal` pattern. The `browse` and `assembly` Lambdas stay.
- A **new CloudFront distribution** reuses the existing VPC origin and wildcard certificate.
- A **CLOUDFRONT-scope web ACL** replaces Vercel BotID: a per-IP rate rule plus a Challenge rule on `/api/browse/search` and `/api/trip/narrate`. Today's web ACLs (`identity.tf`, `modules/waf`) are all `REGIONAL`, so this is a new resource.
- `vercel-cdn-cache-control` headers change to `s-maxage`; `/photo-cdn` becomes a CloudFront behavior.
- Per-PR Vercel previews are replaced by visual tests against `next start` in CI (R7).
- Dev runs on Spot; on-demand from the first paying tenant. A tenant never uses a surface on Vercel Hobby.
- Work: about 1–2 extra sessions in R5.
- **Two separate yeses before the Terraform apply:** Fargate (8.3–16.6 USD a month) and the WAF (about 7.4 USD a month at pilot volume). Cost basis in [Consequences](#consequences).

### Business decisions taken by the tech lead on the decision page (S265); the business owner may revisit

| # | Choice (starting values are policy data, changeable without code) |
|---|---|
| b1 | Approve the commitment wording now ("AA sells only to partner agencies; never directly to travellers; never uses agency customer data for marketing"); counsel reviews it with the contract set |
| b2 | Content tiers 299 / 799 / 1,499 USD a month. Enterprise is "contact sales": contract price no lower than Business, a named owner, a higher SLA and paid EU hosting as an option. Reviewed after 3 agencies. 14-day trial |
| b3 | CRM priced per seat, below the main competitor (for example 25–35 USD per user a month) |
| b4 | TripPlanner sold as a subscription per site: base tier = hosted page plus launcher; higher tier = custom domain plus API |
| b5 | The agency is merchant of record; AA invoices the agency at the B2B price |
| b6 | The CRM may add non-AA ancillaries only (flights, insurance, visa, transfers, fees); tours must be AA's |
| b7 | Resale clause: warn, then suspend if not fixed within a 7-day notice period (adjustable at prod) |
| b8 | "Powered by AA" is optional and off by default |
| b9 | Agency = controller, AA = processor; a joint-controller clause covers the embedded collection; agencies show their own cookie notice |
| b10 | Confirm the contracting legal entity and take counsel advice (Vietnamese licence, EU representative) before Vietnamese agencies store customer data or before the first EU agency |
| b11 | Sell worldwide from US hosting with SCCs plus a TIA; EU hosting only when a contract requires it, at a price; mainland China gets Content only |
| b12 | The agency stays the organiser; AA provides a tour and supplier information pack |
| b13 | Every agency has a named owner; high-touch care for Business and Enterprise; a shared queue for the rest as volume grows |
| b14 | No Stripe Billing now; invoices issued by hand (d9); asked again when monthly volume exceeds manual capacity |
| b15 | One net price per tour per season; three agency tiers with percentage discounts set per contract (0 / 3 / 6 % to start); suggested retail price (RRP) = net + 25 % |
| b16 | New agencies pay a 30 % deposit at confirmation and the balance 30 days before departure (in full if booked late). Credit only after about 6 months of good payment, with a contract limit. USD |
| b17 | Note to the accountant now; contracts say "prices exclude tax"; two invoice kinds (software fee, tour settlement); design the invoice template now |
| b18 | Go-live date set when a pilot agency agrees to use the CRM with real customers. 99.5 % uptime for Business and Enterprise; support reply in 1 business day (4 hours for higher tiers). No SOC 2 or ISO until a large or EU agency asks. Penetration test before go-live |
| b19 | Anthropic account in the AA company's name; cap of 150 USD a month; AI included per plan: Starter 15, Growth 40, Business 80 USD, Enterprise per contract; a soft stop above that, with no overage billing yet |
| b20 | Approve the AI-terms draft (AA-820) now; counsel reviews it before the first paying agency |
| b21 | Light business checks: business registration, a travel licence where the agency's country requires one, a manual check of free public sanctions lists. The agency's owner at AA approves; the business owner approves exceptions |

## ADRs amended

Each one gets a one-line pointer to this ADR.

- **0001:** d5 (drafts open a Booking trip case) and d6 (`inquiry.submitted` to Booking) are superseded by d10/d11 and `lead.submitted.v1`. The end customer lives only in `crm.traveler`.
- **0004:** O6 (guest inquiry → Booking case) and O8 (TripPlanner as the customer front door; Booking customer app) are superseded. Booking is the B2B back office.
- **0005:** the B2C channels and margins (d4) are retired. "From" (d6) = RRP per b15, kept as policy data in `booking.pricing_rules`.
- **0005a:** "no subscription line, CRM free at launch" is superseded. Tenants pay subscriptions; CRM and TripPlanner are paid add-ons (b2–b4); settlement is invoiced from Booking (d9).
- **0006:** the EXTERNAL traveller clients `tripplanner` and `booking-customer` are frozen (d11). Phase 4 traveller accounts are re-scoped to "access through a CRM link" (AA-1005).
- **0010:** d5 is narrowed (agency suppliers for ancillaries only, b6). d6 ends with one app (d6 here).
- **0010a:** d1 and d6 are superseded (one app, one session, no studio service); d5's clean-up is brought forward (d6). d2 and d3 stay. d4 is delivered through the role-map invitation (d7).
- **0016:** adds a runtime per-tenant brand-token layer, the AI-notice component and the message catalogue, built once in the CIS canonical core and synced. Four kit consumers after the merge, not five.
- **0018:** d7 ("residency settled: US") becomes "US by default, EU cell on triggers" (d12); this is decided before `aa-prod` is created. d2's "test data only on Dev" gets the pilot exception (d16). The TripPlanner ECS service lives in `aa-nonprod` (no new account).

## Consequences

- (+) One master record per agency and one action to create one. Pricing and packaging change without code (feature keys).
- (+) AA holds no end-customer identity of its own. Every app is processor-only for travellers.
- (+) No new paid service in R0–R7 except these, each with its own yes:
  - d23: Fargate for TripPlanner and a CLOUDFRONT-scope WAF web ACL (new; today's web ACLs are `REGIONAL`).
  - d20: SES send volume. SES is already in use on the account, so only sending is added: 0.10 USD per 1,000 mails (https://aws.amazon.com/ses/pricing/, accessed 03/11/2026), cents a month at pilot volume.
  - d16 (optional): 14-day RDS backup retention. Free backup storage equals the total provisioned DB storage in the region (https://aws.amazon.com/rds/faqs/); beyond that 0.095 USD per GB-month in us-west-1 (AWS Price List API, accessed 03/11/2026). Estimated under 1 USD a month.
- (+) The merge removes one Fargate service. `aa-crm-dev-portal` already runs on `FARGATE_SPOT` (`crm_portal.tf`), so the saving today is about 2.2–2.5 USD a month. The 8.3 USD on-demand figure applies only if the service would otherwise have moved to on-demand (prod).
- (−) d9 puts platform (SaaS) revenue in the DMC back office. Accounting keeps the two invoice kinds and their number series apart, and CIS must read a Booking view for paid-through.
- (−) d16 puts real PII on the shared Dev environment, with no SLA and only database-wide PITR (per-tenant recovery relies on the nightly export). The risk is accepted for one pilot tenant for at most 8 weeks, and the `aa-prod` plan is the exit.
- (−) d6 makes R3 bigger (two apps merged, all tenant key code removed, studio i18n added: 6–7 sessions of work). Agency machine access to `/v1/*` stops until R8.
- (−) d23 cost and work. Fargate ARM in us-west-1 costs 0.03725 USD per vCPU-hour and 0.00409 USD per GB-hour (AWS Price List API, accessed 03/11/2026).
  - One always-on task: about 8.3 USD a month at 0.25 vCPU / 0.5 GB, or about 16.6 at 0.5 vCPU / 1 GB.
  - Spot has no fixed list price; the Fargate pricing page says "up to a 70% discount" (https://aws.amazon.com/fargate/pricing/). Assuming about 70 %, a 0.5 / 1 GB task is about 5 USD a month. This is an estimate.
  - WAF (CLOUDFRONT scope): 5 USD per web ACL + 1 USD per rule (2 rules) + 0.60 USD per million requests + 0.40 USD per million Challenge responses (https://aws.amazon.com/waf/pricing/ and the AWS Price List API, `ChallengeServed`, accessed 03/11/2026). About 7.4 USD a month at pilot volume (0.5 million requests), about 14 USD at growth volume (10 million).
  - Totals (from `clarifications.md` section 4): Dev on Spot with WAF about 16 USD a month; pilot on-demand with WAF about 28 USD; about 85–100 USD at about 50 tenants with 2 tasks, mostly CloudFront GB and request charges plus WAF. These are not small. CloudFront Asia is 0.12 USD per GB with no free tier assumed (https://aws.amazon.com/cloudfront/pricing/).
  - For comparison, Vercel Pro is 20 USD a month per developer seat, 20–40 USD at growth volume (https://vercel.com/pricing, accessed 03/11/2026). At about 50 tenants, ECS costs more than Vercel; the gain is that the tenant-facing surface stays on AWS, one sub-processor fewer in the DPA, and free ACM certificates for custom domains.
  - The move also loses Vercel's per-PR previews (replaced by `next start` in CI) and adds a deploy workflow.
- **Reversal:** d1, d2 and d10 are cheap to reverse before R1 ships. After R1, the projections make CIS the source, and moving the master is a data migration. d8's drop cannot be undone and stays behind DRY RUN.

## Open items

The approval notes (TL-1, TL-3, TL-7, TL-10, TL-11, TL-19, TL-21 explanations; TL-6 keys; TL-9 UI merge; TL-16 prod and pilot plan; TL-20 channels; TL-8; TL-22; BO-4; BO-8; BO-10; BO-14) are all answered in [`clarifications.md`](./clarifications.md), and the answers are folded into d1–d23 above. Still open (`clarifications.md` section 7):

1. Whether `ai_ops` may read tenant text in Writing Lab (`tenant_content.read`, Lab only, logged), or tenant text is masked for that role.
2. CIS admin and Booking admin on Vercel: Pro with one seat, or a move to ECS on the TripPlanner pattern.
3. The cost yeses: Fargate for TripPlanner (8.3–16.6 USD a month), the CLOUDFRONT-scope WAF (about 7.4 USD a month), and optionally 14-day RDS backups (under 1 USD a month).

**Follow-ups in the R0 PR:**
- Add the README row for 0019 and set the next free number to 0020.
- Add pointer lines in the nine amended ADRs.
- Add a note on data standard C7.1a for the d16 exception.
- Write `CONTEXT.md` in each repo, including the master-per-data-type table (d1).
- Draft `tenant.entitlements.v1` and `lead.submitted.v1` in `docs/contracts/`.
- Check 30 days of `audit_log` for callers of `POST /auth/tenant-login` (d6).
