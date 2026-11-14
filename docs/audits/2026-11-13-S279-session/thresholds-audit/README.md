# S279 thresholds audit: what is admin-editable and what is not

**Date:** 13/11/2026 (S279) · **Audience:** tech lead · **Scope:** origin/main code of AA-CIS-App, AA-Booking, AA-Partner (CRM), AA-TripPlanner-Web and AA-CIS-Infra.

**Rule under test.** This is the S278 pricing rule, widened in S279. Every threshold, limit, cap, floor, ceiling, quota, budget, policy timeout, retry or attempt limit, retention window and business policy value must be changeable on an admin page by the administrator role. Where it matters, the change is versioned and audited, and the page is seeded with the approved default. A literal in code does not meet the rule. Nor does an env var or a registry YAML value on its own, because changing any of them needs a deploy.

**Method and limits.** We read the code only. There were no live reads of the DB, AWS or Vercel, so DB-backed rows show their migration seed values, and env values show the Terraform or code defaults. We left out purely technical constants on purpose: pool sizes, crypto sizes, JWKS caching, page sizes and text max lengths. A critic pass corrected the finders' labels, and the counts below include those corrections.

---

## 1. Summary

There are 780 inventory rows. About 55 of them describe a setting that another area already counted, so there are roughly 725 distinct settings.

**Rows per app and mechanism (after the critic's corrections)**

| App (owning area) | Rows | AA admin page | Agency-owner page only | DB, no page (API or migration only) | Registry YAML | Env var | Terraform value | Hardcoded |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CIS (quality, LLM ops, tenant) | 330 | 24 | 0 | 12 | 29 | 35 | 4 | 226 |
| Booking | 119 | 37 | 0 | 18 | 0 | 1 | 0 | 63 |
| CRM (AA-Partner) | 126 | 2 | 13 | 3 | 0 | 13 | 8 | 87 |
| TripPlanner | 110 | 5 | 0 | 2 | 0 | 22 | 14 | 67 |
| Infra (Terraform) | 95 | 0 | 0 | 0 | 0 | 18 | 31 | 46 |
| **Total** | **780** | **68** | **13** | **35** | **29** | **89** | **57** | **489** |

Notes on the table:
- **TripPlanner admin pages.** Its 5 page-editable rows are CIS pages: the app profile, the tenant AI budget, the lead route and stage routes. TripPlanner has no admin page or settings table of its own.
- **"Env var" vs "Terraform value".** Both mean a container or Lambda env var. "Terraform value" means Terraform sets the value; "env var" means the code default applies. Several settings appeared twice under the two labels and are counted once in the totals.
- **Agency-owner pages.** These 13 CRM rows are edited only by the agency owner for their own agency. No AA administrator page sets the platform default or the allowed range for them.

**In plain words:**
- **Only about 1 setting in 11 meets the rule today:** 68 of 780 rows, or 9 %. Leaving out the 95 Terraform/AWS rows, it is still only 10 %.
- **High-impact items do better:** about 55 rows are rated high, and about 20 of them (roughly a third) already have a staff page.
- **Almost none are administrator-only.** The CIS gateway and spend pages (`ai.admin`, `spend.write`) are also open to `ai_ops`. Booking pricing pages are open to `contracting` and `finance`. The per-tenant RPM and publish limits are open to `customer_success`. Only the CIS `tenant.write` pages are admin-only: plans, plan features, entitlement overrides and lead route.
- **Some pages edit values that nothing reads.** A page that changes nothing gives a false sense of control:
  - 13 of Booking's 20 Pricing Policy parameters are stored only.
  - CIS `plan_feature api.calls_monthly`: the usage view still reads `membership_plans`.
  - CIS `policy.notice_days`: the retirement fan-out reads a different table.
  - The CIS Settings page shows "trash retention 30 days", but no job purges trash.
  - TripPlanner `GUEST_SESSION_DAYS` is set but never enforced.
- **The same value is copied in several places that can drift apart:**
  - The TripPlanner daily cap of $5 sits in the TP code, in Terraform and in a CIS mirror.
  - `PLAN_RPM` is a fallback copy of the plan RPMs. Its enterprise value is 9999; the plan says 1000.
  - The geocoder backfill cap repeats a `spend_budget` row.
  - The admin bundles hold frontend copies of backend limits.
  - The `tenant_ai_budget` `hard_stop` default disagrees with itself: `True` in the PUT body, `False` in the service DEFAULTS.

---

## 2. What is already right (build on these)

| App | Mechanism | Page | Who can write | Audit |
|---|---|---|---|---|
| CIS | `shared.plan`, `shared.plan_feature`, `shared.tenant_entitlement_override` (prices, rewrite quota, AI budget, RPM, CRM seats) | Tenants > Plans & add-ons; Tenant 360 > Subscription | `tenant.write` = admin only | Versioned (409 on a stale version), `audit_log` |
| CIS | `shared.tenants.rate_limit_rpm`, `daily_publish_limit`, `posts_per_week` | Tenant 360 > Settings | admin, plus `customer_success` for its own book | Audited |
| CIS | `shared.spend_budget` (provider caps and central LLM caps) | AI gateway > Budgets | `spend.write` = admin + ai_ops | `updated_by` only, no audit row |
| CIS | `shared.llm_provider_connection` limits and `llm_connection_cost_policy` | AI gateway > Providers > Connections | `ai.admin` = admin + ai_ops | Audited. The form covers LLM kinds only |
| CIS | `shared.tenant_ai_budget` | Tenant 360 > Cost | `spend.write` | Audited |
| CIS | `shared.llm_app_profile` (AI on/off, bulk pause, daily budget per app; TripPlanner and CRM read it) | AI gateway > App profiles | `ai.admin` | Audited |
| CIS | `shared.llm_route_policy`, `llm_role_config` (routes, shadow %, stage kill switch), route control versions | AI gateway > Trace / Routing / Route control | `ai.admin` | Audited; evidence needed on gated stages |
| CIS | `shared.decision_question` (Jev mode, accept and reject floors) | /admin/decisions | `ai.admin` | `threshold_version`, `updated_by` |
| CIS | `shared.writing_memory_writer` kill switch | Writing Lab | `ai.admin` | Audited |
| Booking | `booking.pricing_policy` (20 parameters, effective-dated, maker-checker) | Pricing > Policy | Propose: admin, contracting, finance. Approve: admin plus contracting or finance by group; the proposer cannot approve | Event table |
| Booking | `pricing_rules`, `fx_rates`, agency tiers and rate cards, seasons, holiday events, price list versions | /pricing/* | admin + contracting, maker-checker | Approvals table |
| Booking | `billing_terms`, `tax_rule`, `trip_plan_billing_terms`, terms clauses | /agency-billing, trip-plan Agency terms panel | admin + finance (clause approval: admin only) | Audited, no maker-checker |
| Booking | Per-departure rules, allotments, fees, price adjustments | Departure board, trip-plan Departures panel | admin, contracting, sales by type | Maker-checker on allotments and fees |
| CRM | `crm.llm_app_profile` | Relayed from the CIS AI gateway App profiles card | crm-platform-admin | Audited |
| CRM | `crm.tenant_entitlement` | Projected from CIS plans every 120 s | CIS `tenant.write` | Through CIS |

Two patterns are worth copying everywhere:
- **Booking `pricing_policy`:** typed parameters with code bounds, effective dating, maker-checker and an event log.
- **CIS plans:** optimistic versioning and an `audit_log` row per change.

---

## 3. Gaps by priority

### 3.1 High impact, not editable by the administrator today

| App | Setting | Value today | Where | Mechanism today | Who would change it, and why |
|---|---|---|---|---|---|
| CIS | Quality pass line (`pass_line`, read by A1 retry/HITL, publish floor, Review approve, T2 status, T3 revise, T7 cut, golden set) | 7.0 | services/quality/thresholds.yaml:17 | Registry YAML; read-only on Settings > Pipeline gates | Administrator with the content lead, to tune the publish bar after an eval. Today: a PR, the change_control lock and a redeploy |
| CIS | Detector modes (enforce or warn per detector) | 51 enforce, 31 warn/shadow | services/quality/taxonomy.yaml:30 | Registry YAML | Administrator, to promote or demote a check after its shadow data |
| CIS | Claim policy D1–D15 verdicts (what AI content may say) | e.g. rarity enforce, hypothetical warn | services/quality/writing_policy.yaml:85 | Registry YAML, compiled into prompts | Administrator with the content lead: business policy |
| CIS | SEO bands (meta 140–155, title 45–60, slug ≤ 60) | as listed | writing_policy.yaml:46 | Registry YAML | Administrator: SEO policy |
| CIS | T9 blog length band, writer target margin | 4,700–13,000 chars; margin 0.17 | acp_content_writing/length_contract.py:45; thresholds.yaml:83 | Hardcoded / YAML (tied to the prompt hash) | Administrator: product length policy |
| CIS | Blog seed floor `T7_BLOG_MIN_SEED_WORDS` | 600 (code default 0) | acp_shared/blog_seed.py:24; Infra aa365 main.tf:222 | Env var set in Terraform | Administrator: what may be proposed on Blog |
| CIS | T7 channel bars (`CHANNEL_BARS`: demand 1000, questions 3, words 150, per-hub caps) | as listed | acp_shared/slate.py:118 | Hardcoded | Administrator: which segments get proposed |
| CIS | Attempt limits: T9 `MAX_ATTEMPTS` 3, A1 `MAX_RETRIES` 3 | 3 / 3 | acp_content_writing/service.py:122; content_generation/graph.py:44 | Hardcoded | Administrator: cost vs. hold rate |
| CIS | T2 per-version budget (2 writer, 3 repair, 1 voice, $0.25) | as listed | content_generation/t2_orchestrator.py:103 | Hardcoded | Administrator: spend per tenant version |
| CIS | Writing-memory month cap $25 (the run cap is partly in `spend_budget`) | $25 / month | writing_memory/config.py:40 | Hardcoded (partial) | Administrator: learning-loop spend |
| CIS | Rewrite over-quota rule (soft: allow and bill overage) | soft | api/routers/v1_tours.py:449 | Hardcoded | Administrator or finance: block vs. bill |
| CIS | Platform default daily publish limit | 20 / tenant / day (max 1000) | acp_publish/daily_limit.py:35 | Hardcoded (only the per-tenant override has a page) | Administrator: AUP default |
| Booking | Cancellation fee schedule (B2B FIT scale) | ≥31 d free … 0–1 d 100 % | migrations/051 (API: /booking/pricing/cancellation-policies) | DB, API only. The Policy page link goes to a page with no cancellation tab | Administrator or contracting: commercial terms |
| Booking | B2B hold length `b2b_hold_hours` | 48 h | migrations/020; b2b/holds.py:59 | DB, no page (`booking.settings`; the app role has SELECT only, so a change needs a migration) | Administrator or contracting |
| CRM | Platform AI budget ceiling per agency `AI_BUDGET_MAX_USD` | $2 / month | AA-Partner api/app/settings.py:253 | Env var (code default) | Administrator: plan cap for agencies |
| CRM | Refund/cancel-fee owner-approval threshold `refund_owner_threshold_base` | 1000 (base currency) | migrations/008:507 | DB, no page | Administrator sets the platform default; the agency owner sets its own |
| CRM | Overdue-invoice reminders (`EVERY_DAYS` 3, `MAX_REMINDERS` 5) | as listed | payments/reminders.py:32 | Hardcoded | Administrator: client messaging policy |
| CRM | Inquiry-form quota `RATE_LIMIT_INTAKE_FORM_PER_HOUR` | 200 / form / hour | settings.py:229; Infra crm_app.tf:465 | Env var set in Terraform | Administrator, per agency: a busy agency needs more |
| CRM | Agency-owner settings defaults and ranges (AI budget default $2, discount 10 %, markup 0–300 %, public price checks 10–600/min, trash 1–30 d, archive 12–120 mo) | as listed | intake/booking_settings.py:25, proposals/retail.py:34, lifecycle/rules.py:14 | Agency-owner page for the value; defaults and ranges hardcoded | Administrator sets the platform defaults and allowed ranges; the owner picks inside them |
| TripPlanner | Daily AI spend cap | $5 / UTC day | backend/config.py:247; Infra tripplanner_variables.tf:103; CIS mirror app_registry.py:61 | Env var set in Terraform. The CIS app-profile `default_daily_budget_usd` overrides it, but that row is NULL | Administrator: customer-facing AI spend |
| TripPlanner | Planning-chat monthly caps (whole app, and per tenant) | $2 / $2 | config.py:300–301 | Env var (code default) | Administrator; per tenant later |
| TripPlanner | Per-visitor AI limits (narrate 10/h, search 30/min, chat 20/h, chat per IP 40/h) | as listed | config.py:283–293 | Env var (code default) | Administrator: abuse vs. conversion |
| TripPlanner | Leads per tenant per day | 200 / 24 h | config.py:175 | Env var | Administrator, per tenant |

### 3.2 Medium impact (grouped; full rows are in the inventory)

**CIS**
- **Need a form only; the API already exists:**
  - Geoapify `daily_credit_limit` (2500/day).
  - DFS low-balance alert ($10) and Jev low-credit alert ($3).
  - Jev timeout and retries.
  - Capacity TPM limits (`llm_capacity_limit`).
- **Need an API and a page:**
  - Route deadlines (`route_deadline_s`) and `stage_model_params` (max_tokens, effort).
  - Model catalog output caps.
  - The platform tour-retirement notice (7 d; the platform row has no writer).
- **Paid-run caps in code:**
  - Segment research $50/run; place backfill 50 tours / $50; rerun wave 2000 tours.
  - Question top-up $3; embedding re-embed $25.
  - The `DFS_CALL_ESTIMATE_USD` price table (AA-1055 was 2.4x off).
  - Wave quality gates ($0.12/tour).
  - S1 SEO prefetch (30 Jev asks per tour, reuse 180 d).
- **Quality and gate switches:**
  - `AUTO_UPGRADE_THRESHOLD` 8.5; `T2_JUDGE_GATE`, `T3_BACKGROUND_FACTS` and the S1/T2/T9 writer switches (Terraform literals or env).
  - T10 gate modes: split them into env modes and the hardcoded blocking flags.
  - Seed-align and brief-grounding modes.
  - Brand-fit caps; atom seed floors; the platform forbidden-word lists.
  - Elephant-policy country exception; near-duplicate thresholds; place dedupe and geomatch distance rules.
- **Tenant and plan values:**
  - `PLAN_ALERT_PCT` 80 / `PLAN_APPROVAL_PCT` 100 (applies to every tenant without a budget row); `TRIAL_DAYS_MAX` 60.
  - The posts-per-week ceiling of 14, coded in three places.
  - Commercial and AA sales-link host lists (env plus code).
- **Ops and data policy:**
  - Retention windows: `llm_call_log` 180 d, `tenant_api_usage` 90 d, job 30/90 d.
  - `ERASURE_TENANT_RETENTION_DAYS` 30.
  - Job-kind concurrency and attempts (~60 kinds); circuit-breaker rules; ops-check alert thresholds (starved 900 s, research stale 20 %).
  - Report flag thresholds (money, reliability, security); LLM cost reconcile tolerance; `PLACE_PIPELINE_AUTO` (a paid-run gate).

**Booking**
- **`booking.settings` rows to move onto Pricing > Policy:** hold extend 72 h, re-hold limit 3/day, on-request answer SLA 1 business day, child/infant age bands 11/1, `pre_departure_days` 14, `supplier_answer_days` 2, `emergency_contact_keep_days` 90.
- **Code constants:** agency reminder steps [1, 7, 14] (hardcoded, no row), `ROUNDING_INCREMENTS` 5 per currency, `DEFAULT_DECISION_DAYS` 21, cost-sheet pax bands, one hold extension per hold, retention windows (job 30/90 d, inbox redaction 90 d).

**CRM**
- **Platform rate limits:** public 60/min, intake 5/min, member 600/min, AI 6/min, Book now 5 per address per hour.
- **AI:** `CRM_LLM_MAX_TOKENS` 800; `crm.llm_stage_profile` (attempts, deadline) and `llm_stage_route` (no write route).
- **Lifetimes:** invitation TTL 168 h; offboarding cool-off 72 h; client link lifetimes 14/14/30 d.
- **Pipeline policy:** Stage 2/3 completeness gates 80/100 %; quiet/stalled days 3/14; workflow cooldowns 12 h / 3 d; reply SLA 2 h.
- **Data lifecycle:** submission redaction 90 d, LLM ledger 180 d, signed agreements 36 mo; `LIFECYCLE_DRY_RUN` and the retention dry-run switches (Terraform).
- **Limits and sync:** document and import caps (7 MiB, 5000 rows); Booking sync retry policy.

**TripPlanner**
- **Leads:** lead hold 7 d (bounds 3–7); signed-in factor 2x; send-to-advisor limits 5/20 per hour; `ADVISOR_HANDOFF_DEMO`, `REQUIRE_REGISTRATION_BEFORE_HANDOFF`, lead CRM pull enable; budget bands.
- **AI cost:** narration cache TTL 7 d; narration max_tokens 1200; chat steps 3 / tokens 700.
- **Ranking and display:** suggestion weights and distances; country page counts (12/24/12); route-proposal day range 2–30.
- **Data:** outbox redaction 90 d; guest session 90 d (not enforced).
- **Edge:** the API Gateway narrate/search throttles stay in Terraform (see section 4).

### 3.3 Defects found along the way (fix with the lanes)
1. **The tenant AI budget default disagrees with itself.** The PUT body says `hard_stop=True`; the service DEFAULTS say `False`.
2. **Editable but unread:**
   - CIS `api.calls_monthly` and `policy.notice_days`.
   - Booking's 13 stored-only policy parameters.
   - Booking B2C settings rows (deposit, quote validity, invoice schedule, `payment_overdue_reminder_days`).
   - `ops_docs_max_bytes` (the code cap is 3 MB; the setting says 10 MB).
3. **Shown but not enforced:** the CIS trash retention of 30 days and the TripPlanner guest session of 90 days.
4. **Dead config:**
   - The API Gateway usage plans (starter, growth, business, internal) are attached to no API keys.
   - `SF_BATCH_THRESHOLD` has no reader.
   - The `b2b_quote_valid_hours` row is retired.
   - `QUALITY_PASS_THRESHOLD` 3.0 is a second pass line with no caller.
5. **Two break-glass minimums:** change_control requires 12 chars, route evidence requires 20.
6. **No spend guard on acc1.** acc1 now serves Bedrock (S278), but it has no AWS Budget or anomaly monitor, and the acc1 connection's `monthly_budget_usd` in the CIS gateway is NULL.

---

## 4. Items that should stay in Terraform or code

The default answer is "admin-editable". The exceptions below are kept narrow:

1. **WAF rate rules, geo allow-list, managed-rule overrides and protected paths** (CIS, staff, TripPlanner, Cognito ACLs). These are AWS edge resources. The app role must never hold `wafv2:UpdateWebACL`, so changes go through a reviewed Infra PR. Show them read-only on admin Platform > Infra. Turn the `RateLimit1000` literal into a variable.
2. **API Gateway stage and route throttles, Lambda reserved concurrency, ECS task sizing and worker max count.** These are capacity limits tied to the RDS connection budget (`connection_budget.json`). They are a cost and abuse backstop under the app-level limits, which are the tunable layer.
3. **AWS Budgets and Cost Anomaly thresholds on acc2, acc3 and acc4.** These are AWS resources, and acc3/acc4 are other accounts the app cannot reach. Show them read-only next to the CIS spend page. The app-side LLM caps in `spend_budget` are the editable layer.
4. **CloudWatch alarms and SES/identity alarms.** Ops monitoring defined with the resources they watch. Make them variables where they are literals.
5. **Log retention, S3 lifecycle, Object Lock, CloudTrail and RDS backup/snapshot retention.** These are compliance and backup policy, and Object Lock cannot be shortened anyway. App-table retention (`llm_call_log`, `booking.job`, CRM lifecycle) is not in this group: it moves to settings.
6. **Cognito token lifetimes, password and MFA policy, IAM session lengths, `RATE_LIMIT_XFF_HOPS`.** Auth perimeter and network topology.
7. **Destructive kill switches: `ERASURE_APPLY_ENABLED`, `SEGMENT_GC_MODE`.** Two-key rule on data deletion: Terraform must allow it, and the app then runs it.
8. **Technical and protocol constants:** JWT leeway, JWKS TTL, DB/S3/HTTP connect timeouts, job lease/heartbeat/poll, body caps that must match ALB/API Gateway limits, crypto sizes. These are engineering, not policy.
9. **Engine invariants and the bounds of a setting.** Examples: pricing ratio < 1, target + uplift + fee < 1, `Param.minimum/maximum`, `RATE_LIMIT_RPM_MAX`. These are guard rails. They live in the setting's definition row, seeded by migration, so widening a bound is a reviewed PR (as ADR 0005b already does for Booking).
10. **`GUEST_LEGACY_GRACE_UNTIL`** (closed on purpose) and the E2E fixture constants (test-only).

Frontend mirrors of backend limits are neither settings nor keepers. Remove them and read the values from the API.

---

## 5. Design proposal: one settings pattern, stored by each owner

**Principle.** Use one table shape, one reader library, one admin page and one CI guard. Each schema owner keeps its own rows: CIS in `shared`, Booking in `booking`, CRM in `crm`. TripPlanner has no staff surface, so its rows live in CIS and are exposed through a `catalog` view. That is the pattern it already uses for `v_llm_app_profile_v1` and `v_tenant_ai_budget_v1`.

### 5.1 Tables (per owner schema)

`<schema>.setting_definition`: one row per setting, written only by migration.

| Column | Meaning |
|---|---|
| `key` (PK) | e.g. `cis.quality.pass_line`, `tp.ai.daily_cap_usd`, `crm.rate.intake_form_per_hour` |
| `app`, `area`, `label`, `description` | For page grouping and help text |
| `value_type` | `int`, `numeric`, `bool`, `enum`, `duration_s`, `usd`, `pct`, `list`, `json` |
| `unit` | Shown on the page |
| `min_value`, `max_value`, `allowed_values` | Bounds. Changing them needs a migration |
| `default_value` | Approved seed (today's effective value) |
| `scope_kind` | `platform` or `platform+tenant` (per-tenant override allowed) |
| `impact` | `high` / `medium` / `low` |
| `approval` | `single` or `maker_checker` |
| `evidence_required` | true for evidence-gated quality keys (eval run id) |
| `env_override` | Name of the emergency env var, if any |
| `cache_s` | Reader cache, default 30 s |
| `enforced` | false = stored only. The page shows "not enforced yet" |

`<schema>.setting_value`: append-only and versioned.

| Column | Meaning |
|---|---|
| `id`, `key` (FK), `tenant_id` (NULL = platform) | Which setting, at which scope |
| `value` (jsonb) | Typed through `value_type` |
| `version` | Per key and scope; optimistic lock (409 on a stale version) |
| `status` | `proposed` / `approved` / `rejected` / `superseded` |
| `effective_from` | Future dating allowed (as in Booking) |
| `proposed_by`, `approved_by` | The approver is never the proposer when `approval = maker_checker` |
| `reason` | At least 20 characters (one break-glass minimum for the whole platform) |
| `evidence_ref` | Eval or golden-set run id, required when `evidence_required` |
| `created_at` | — |

Every approve writes an audit row: `acp_shared.audit_log` for CIS, `pricing_policy_events` for Booking, the CRM audit for CRM.

**Booking** does not get new tables. It extends `booking.pricing_policy` with new groups (holds, desk SLA, ops lifecycle, ages, retention, reminders, rounding) and keeps the Pricing > Policy maker-checker page. The `booking.settings` rows move into it, and the dead B2C rows are retired.

### 5.2 Reader

- **One small library per language,** shared like `aa_llm`: CIS owns it, and the other apps vendor a byte copy.
- **Call shape:** `setting("key", tenant_id=None)` returns a typed value.
- **Resolution order:** env override (if the definition allows it, logged as a warning) → approved tenant row with `effective_from ≤ now` → approved platform row → `default_value`.
- **Cache:** per process, for `cache_s` (default 30 s).
- **Safe fallback:** on a DB error, keep the last good value; with none, use the compiled default. The compiled defaults come from a file generated from the migration seed, and CI fails if the two differ. An out-of-bounds value from the DB is refused, the default is used, and an ops alert is raised.
- **Prompt-embedded values** (SEO bands, blog word band, claim verdicts): prompts render them at call time, and the settings version joins the prompt hash. Each `llm_call_log` row then records which policy produced a piece.

### 5.3 Admin page

- **Location:** one page in CIS admin, Platform > Settings, with tabs by app, then by area. Each tab calls the owning app's settings API. CIS stays the single admin console, and the owner keeps its table: this is the same relay pattern as the CRM app profile.
- **Content per row:** value, unit, default, bounds, last change (who, when, reason), history and diff, the "overridden by env" or "not enforced yet" badge, and pending proposals.
- **Permissions:** a new CIS capability `settings.write` and `settings.approve`, held by **admin only**. Existing delegated pages (finance billing, contracting pricing, ai_ops gateway) stay where they are and are listed in the page's role matrix (see Q1).
- **CRM** gets AA-platform limits and the platform defaults and ranges for agency settings. The agency owner's Settings pages keep editing per-agency values, inside the platform range.
- **Booking** keeps Pricing > Policy as its page. The CIS tab links to it, and Booking groups appear there read-only.
- **Bounds** are validated in the API (422 out of range) and in the DB (CHECK against the definition).

### 5.4 CI guard (per repo)
1. **`settings-lint`.** In the governed modules (listed in a repo file: quality, content writing, slate, cost guard, jobs, retention, CRM payments/intake/lifecycle/ratelimit, TP config/assembly, Booking b2b/ops/retention), a new UPPER_CASE numeric constant whose name looks like policy (`*_MAX`, `*_MIN`, `*_CAP`, `*_LIMIT`, `*_DAYS`, `*_HOURS`, `*_PCT`, `*_THRESHOLD`, `*_USD`, `*_ATTEMPTS`, `*_RETRIES`) fails the build, unless it carries `# technical-constant: <reason>`. A new `os.environ` / `getenv` read of a numeric value fails unless it is on the allow-list.
2. **No dead settings.** Every `setting_definition` key must have a reader call, and every reader key must exist, or the key must be marked `enforced=false` with an issue reference. This catches the Booking stored-only parameters and CIS `api.calls_monthly`.
3. **No mirrors.** Frontend constants that match a setting key fail the build; the frontend reads the value from the API.
4. **Seed parity.** The compiled defaults file must equal the migration seed.
5. **The change_control lock moves.** For keys moved out of `thresholds.yaml` and `writing_policy.yaml`, the lock now checks that each such key has `evidence_required=true`, instead of a YAML sha.

### 5.5 How today's values migrate
- **Seed from the effective value, not the code default.** Use the Terraform value where it differs, e.g. CRM `RATE_LIMIT_PUBLIC` is 60 in Terraform vs. 120 in code, and `T7_BLOG_MIN_SEED_WORDS` is 600 vs. 0. The migration comment cites the source of each value.
- **Env vars** become an emergency override for one release, with a page badge and a log warning. After that, remove them from Terraform. Only the destructive kill switches in section 4 stay in Terraform.
- **Registry YAML** (`thresholds.yaml`, `writing_policy.yaml` numbers, `taxonomy.yaml` modes): the first migration seeds the definitions from the YAML. The YAML is then deleted, or reduced to non-numeric structure (rule ids, text). `quality-registry.generated.ts` is replaced by a runtime read.
- **DB rows without a page** (`route_deadline_s`, `stage_model_params`, `llm_capacity_limit`, the CRM stage profile/route, `booking.settings`): keep each table and add the editor. `booking.settings` is the exception: it folds into `pricing_policy`.
- **Duplicates** keep one setting and drop the copies: the TP $5 cap in three places, the `PLAN_RPM` fallback, the geocoder backfill cap vs. `spend_budget`, and the frontend mirrors.

---

## 6. Lanes

| # | Repo | Scope | Migration owner | Order |
|---|---|---|---|---|
| L1 | AA-CIS-App | **The mechanism:** `shared.setting_definition`/`setting_value`, reader library, `settings.write`/`approve` (admin only), Platform > Settings page, audit, CI guard skeleton. **High-impact items:** T7 blog seed floor, platform daily publish limit, rewrite over-quota mode, T9/A1 attempt limits, T2 version budget, writing-memory month cap, paid-run caps (segment research, place backfill, rerun wave size, question top-up, DFS price table), platform retirement notice days, retention windows, erasure retention days. **Forms for API-only fields:** Geoapify credits, DFS/Jev low balance, Jev timeout, capacity TPM, `route_deadline_s`, `stage_model_params`. **Defect fixes:** tenant AI budget default, wire or remove `api.calls_monthly` / `policy.notice_days` / trash 30 | CIS (`NNN`) | First |
| L2 | AA-CIS-App | **Quality registry move:** `thresholds.yaml`, `writing_policy` numbers, `taxonomy.yaml` modes, T10/seed-align env modes, `AUTO_UPGRADE_THRESHOLD`, `T2_JUDGE_GATE`/`T3_BACKGROUND_FACTS`. Evidence-gated maker-checker; prompt hash includes the settings version; the generated frontend constants go; change_control lock adapted. Risky (gates, prompts), so review before merge | CIS | After L1 |
| L3 | AA-Booking | Extend `pricing_policy` groups. Move the `booking.settings` policy rows (hold 48 h, extend 72 h, re-hold 3, on-request SLA, ages, ops lifecycle days). Add a cancellation-policy tab to the Policy page. Reminder steps, rounding increments, decision days, retention windows. Badge or wire the 13 stored-only parameters; retire the dead B2C rows | Booking (`bk-NNN`) | Parallel with L1 (no dependency) |
| L4 | AA-Partner (+ CIS tab) | `crm.setting_*` + `/crm/ops/v1/settings` (crm-platform-admin) + CIS Platform > Settings CRM tab (relay). Items: `AI_BUDGET_MAX_USD`, rate limits (public, intake, form quota per agency, member, AI), `refund_owner_threshold_base` default (plus an owner field), invoice reminder cadence, `CRM_LLM_MAX_TOKENS` moved onto the stage route, a stage profile/route editor, platform defaults and ranges for the agency-owner settings, lifecycle windows, dry-run switches if approved (Q7) | CRM (`crm-NNN`); CIS for the tab | After L1 (reuses the reader and page component) |
| L5 | AA-CIS-App + AA-TripPlanner-Web | CIS rows with `app='tripplanner'` + `catalog.v_app_settings_v1`; TP reader with a 20–30 s cache. Items: daily cap (seed the app-profile `default_daily_budget_usd` = 5.0 and make it the single source), plan-chat monthly caps (+ per tenant), visitor rate limits, lead cap per tenant, lead hold days, narration TTL and tokens, chat steps, handoff switches. Remove the CIS mirror `TP_DEFAULT_DAILY_CAP_USD` | CIS (rows and view); TP code only | After L1 |
| L6 | AA-CIS-Infra (+ CIS read-only view) | Remove env vars once L1/L4/L5 read the DB. Turn literals into variables (WAF `RateLimit1000`, CIS and Booking stage throttles, CRM SLO locals). Delete the dead API Gateway usage plans and `SF_BATCH_THRESHOLD`. Publish edge, budget and alarm values as a Terraform output shown read-only on admin Platform > Infra. Act on the acc1 guard per Q9 | Infra | Last |

Each lane is one PR group. L1, L2 and L4 change auth or permissions plus a migration, so an independent agent review runs before merge (dev-phase rule).

---

## 7. Open questions for the tech lead (each with a proposed default)

1. **Who may write besides the administrator?** Today `ai_ops` can raise spend caps, `customer_success` can change a tenant's RPM and publish limit, and `contracting`/`finance` own pricing and billing.
   - **Proposed default:** the new registry is admin-only. Delegated roles keep their domain pages (finance: billing; contracting: pricing). `ai_ops` and `customer_success` become **tighten-only** on limits (they may lower a cap or turn AI off, never raise it).
2. **Maker-checker with one administrator.**
   - **Proposed default:** in the dev phase, the admin may self-approve high-impact changes with a reason, and an e-mail goes to the tech lead. True two-person approval applies from the first prod or paying tenant, the same trigger as the merge rule.
3. **Quality thresholds: DB-editable with evidence, or keep them PR-only?**
   - **Proposed default:** DB-editable, with `evidence_ref` required for the pass line, detector modes and claim verdicts. The page can run a dry eval on a proposed value before approval.
4. **Per-tenant overrides.**
   - **Proposed default:** allowed for the TP lead cap, plan-chat cap, CRM form quota and AI budget. Where a plan concept exists, use plan entitlements first; otherwise a tenant row.
5. **Env vars after migration.**
   - **Proposed default:** an emergency override for one release, then removed. Only the destructive kill switches stay in Terraform.
6. **Stored-only and dead settings** (Booking's 13 parameters, B2C rows, `api.calls_monthly`, trash 30, usage plans).
   - **Proposed default:** wire `api.calls_monthly` and the trash purge. Badge the Booking parameters "not enforced yet" until their features ship. Delete the B2C rows, usage plans and `SF_BATCH_THRESHOLD`.
7. **CRM retention dry-run switches: admin page or Terraform?**
   - **Proposed default:** an admin-only switch with maker-checker. Terraform keeps a hard "never delete" env floor.
8. **Tenant AI budget `hard_stop` default.**
   - **Proposed default:** `true` (fail closed on money). Fix the service DEFAULTS.
9. **acc1 spend guard.** acc1 serves Bedrock but may hold no other resources. Is an AWS Budget there allowed?
   - **Proposed default:** set `monthly_budget_usd` with hard stop on the acc1 Bedrock connection row now; the admin page already exists. Also allow an AWS Budget and anomaly monitor on acc1 as a billing-only exception, recorded in ADR 0001a.
10. **Low-impact detector sensitivities** (~40 rows: hygiene Jaccards, geomatch distances, F13/F15 thresholds).
    - **Proposed default:** a later phase, under an "Advanced" group with evidence required. Not in the first lanes.
11. **Where the page lives.**
    - **Proposed default:** one CIS Platform > Settings page for all apps, with Booking's tab linking to its own Pricing > Policy page. The alternative is one settings page per app.
