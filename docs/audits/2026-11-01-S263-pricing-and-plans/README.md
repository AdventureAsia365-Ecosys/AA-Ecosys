---
id: OPS-08-s263-pricing-and-plans
title: "Tour pricing chain and customer plans: as-built research (S263)"
description: "Read-only research of where tour prices come from (supplier net, AA sell, agency price) and how tenant/agency plans drive limits, with gaps."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-01
review_every_days: 30
related: [AA-1016, AA-1025]
---

# Tour pricing chain and customer plans (S263, 01/11/2026)

Two read-only research reports (code + db-schema-reference), raw text below.

## 1. Tour pricing across the chain

**Tour pricing across the chain: what exists, where a tour's price comes from today, and the gaps**

**Short answer:** The pricing model is designed and mostly built in AA-Booking. It is set by ADR 0005 and ADR 0005a, and it covers supplier net rates, margin rules per channel, FX, a per-tour price matrix and B2B quotes. Nothing links it to CIS. CIS and the tenant portal still show a parsed `price_raw` string. TripPlanner shows no price. The live tables are almost empty: `booking.trip_plans` has about 2 rows, and the schema reference gives no row count for `supplier_rates` or `trip_plan_prices`, so they are probably empty.

**1. Raw tour (CIS)**
- `silver_aa_internal.raw_tours.price_raw` and `period` are free-text columns filled by the Excel column mapper (`apps/AA-CIS-App/services/ingestion/excel_parser.py`, where `price` and `price_usd` both map to `price_raw`). They also pass through `acp_contract.v_trip_registry`.
- There is no net cost, currency, season or pax column.
- The `facts` table has a `kind='price'|'season'` value used for content grounding. It is not a price.

**2. Master / published tour**
- `gold_aa_internal.published_tours` and the `catalog.v_tour` view have no price columns at all. ADR 0005 d1 says all prices belong to schema `booking`.
- The tenant portal marketplace shows `parse_price(price_raw)` as an indicative USD figure:
  - `apps/AA-CIS-App/services/acp_shared/marketplace_estimates.py`
  - `apps/AA-CIS-App/api/routers/v1_marketplace.py:140`
  - `apps/AA-Partner/portal/app/portal/_components/marketplace/TourDrawer.tsx:131`

**3. AA-Booking (owner of all prices, ADR 0005)**

Tables (in `docs/architecture/db-schema-reference.md`):
- **Supplier net cost:** `booking.suppliers` → `supplier_contracts` (validity, currency; maker-checker publish, never overwritten) → `supplier_rates`. A rate holds `net_amount`, `currency`, `season`, `valid_from`/`valid_to`, `pax_min`/`pax_max`, `meal_plan`, and a unit (room_night, person, group, vehicle or day).
- **Margin rules:** `booking.pricing_rules`, per channel (b2c_tailor_made, fixed_departure, b2b). Each rule has `target_margin`, `floor_margin`, `peak_uplift_pts`, `card_fee_pct` and `valid_from`. Approval is maker-checker via `policy_approvals`.
- **FX:** `booking.fx_rates` (`rate_per_usd`, `buffer_pct`, `as_of`).
- **Published price list:** `booking.trip_plan_prices`, one row per channel × season/peak × validity × pax band × currency. A row stores the selling `amount`, plus `net_amount`, `effective_margin`, `priced_on` and an `overridden` flag. `trip_plans` adds `supplier_id` and a single `price_hint_*` value.
- **Case costs:** `version_item_costs` (with `supplier_rate_id` as provenance) and `trip_case_versions` (`total_price`, `fx_rate_locked`).
- **B2B:** `b2b_partners` (agency, `billing_currency`, `credit_terms_ref`). `b2b_quotes` and `b2b_quote_lines` are append-only. They store the locked FX, `margin_applied`, `price_hash`, `valid_until`, and per line `b2b_price` with a hidden `net_cost_usd`.

Code (all under `apps/AA-Booking/`):
- `backend/app/pricing/engine.py` holds the formula: sell = net_usd ÷ (1 − margin − card fee). Margin is gross on the selling price, not markup. Non-USD prices = USD × rate × (1 + buffer). B2C totals round up to $5.
- `backend/app/pricing/service.py`, `backend/app/pricing/repository.py` and `backend/app/pricing/policy.py` load the rule and FX in force and run the engine.
- `backend/app/supply/rates.py` picks the rate in force (published contract, validity covers the day, pax band).
- `backend/app/catalog/trip_plan_prices.py` handles the price matrix (bk-032). A row is either priced from a net cost or typed by hand. Saving replaces the whole set.
- `backend/app/b2b/components.py` computes a line's net from the rates in force (for a `tp:` plan, the sum of its components). `backend/app/b2b/quotes.py` prices it with the `b2b` rule.
- `backend/app/b2b/reads.py` serves `/price-parity`. Its "from" price comes from the old `price_hint` field, not the matrix.
- `backend/app/routers/pricing.py` serves quote-preview, rules and fx-rates.

Admin pages (in `apps/AA-Booking/frontend/app/(staff)/`):
- `pricing/rules`
- `pricing/calculator`
- `suppliers/rate-sheets/[id]`
- `catalog/trip-plans/_parts/PriceMatrixEditor.tsx`
- `cases/[code]/CostVsBilled.tsx`

**4. CRM (AA-Partner), the agency side**
- AA items come in at the Booking `b2b_price` (`api/app/proposals/aa_options.py`).
- The agency types its own selling price (`sell_amount`) by hand on each option in `crm.option` (`api/app/proposals/builder.py`).
- If that price is below AA's "from" price, the CRM warns but does not block (`_below_from`, ADR 0005a).
- `crm.booking_line_money` records each money line as cost, sell, commission_expected or cancellation_cost, with FX.
- `crm.agency_supplier.default_commission_pct` and `crm.commission` (crm-035, `api/app/commissions/service.py`) track the commission the agency earns from its own suppliers. This is not an AA → agency commission.
- `api/app/margin.py` hides net, cost and margin fields from the assistant role.

**5. B2C (TripPlanner)**
- No price is shown. `apps/AA-TripPlanner-Web/frontend/app/tours/[slug]/page.tsx:2` says there is no price source yet.

**Gaps**
1. **No CIS → Booking link.** There is no `trip_plans` row for most published tours. `price_raw` is never turned into a reviewed reference price, although ADR 0005 d7 planned that.
2. **`booking.v_from_prices` (contract `price.from.v1`) is not built.** TripPlanner and the portal therefore have no real price. Price parity still uses `price_hint` instead of `trip_plan_prices`.
3. **No per-agency pricing.** There is one global `b2b` margin rule: no per-partner markup, tier, rate card or contract price list. No commission model exists where AA pays an agency; AA earns through the B2B margin instead. Retail prices are typed by hand in the CRM, with no default markup.
4. **The cost sheet is not automated.** ADR 0005 d3 wants a net per pax band and season computed from the plan's components. Today the matrix needs a typed net or a typed amount (the B2B quote does compute from components). Nothing populates `trip_plan_prices` automatically.
5. **Price history lives only in audit rows.** For `trip_plan_prices`, the history is the before/after rows in `audit_logs`, because each save replaces the set. Rates are versioned by contract. Rules and FX are dated append rows.
6. **Open items:** the tax table (ADR 0005 d10) does not exist. Rounding for non-USD currencies is still open on AA-810. Supplier rate-sheet Excel import exists, but live data is almost empty.

**Design docs**
- `docs/adr/0005-pricing-and-supplier-rates.md`
- `docs/adr/0005a-b2b-resale-warn-and-vnd.md`
- `docs/audits/2026-10-22-S247-crm-w0/booking-commercial-core-memo.md` (seam 7: one engine)
- `apps/AA-Booking/CONTEXT.md` (lines ~106 and 205–240)
- `apps/AA-Booking/migrations/004_pricing_rules_fx.sql`, `010_hotels_services_rates.sql`, `019_b2b_partners_quotes.sql`, `021_b2b_commercial_rules.sql` and `032_trip_plan_supplier_prices.sql`

## 2. Customer plans for tenants and agencies

### Short answer
There is no single place where an admin defines a plan once and assigns it, with budgets, entitlements and quotas following from it. There are three separate partial mechanisms (CIS tenants, CRM agencies, AI budget), and none of them has an admin editor for the plan definitions themselves. I found no Content studio code that reads any plan; everything Content studio has is described in section 1.

### What exists

**1. Content studio / CIS tenants: the closest thing to a plan catalogue**
- `shared.membership_plans` holds `plan_name`, `tours_quota_monthly`, `api_calls_quota_monthly`, `price_usd_monthly` and two overage rates. Schema: `docs/architecture/db-schema-reference.md:8651`.
  - The table was created by hand on Dev, then written into a migration in `apps/AA-CIS-App/api/migrations/223_tenant_usage_real_llm_cost.sql:56-77`.
  - That migration seeds 5 rows: starter 50 tours / $299, growth 200 / $799, business 500 / $1499, enterprise, internal.
- `shared.tenants` has two plan columns (db-schema-reference.md:9344):
  - `plan_tier` (enum `internal/starter/growth/business/enterprise`, line 10550).
  - `plan_id`, a foreign key to `membership_plans`.
  - It also has per-tenant limit columns: `rate_limit_rpm`, `posts_per_week`, `daily_publish_limit`.
- Consumers:
  - Tours quota and billing: `api/routers/v1_tours.py:330-358,458-464`, `api/routers/_billing.py`, and the view `shared.v_tenant_monthly_usage`.
  - Rate limit per plan: a hardcoded Python dict, `PLAN_LIMITS`, in `api/routers/admin.py:80-86` (starter 60, growth 300, business 1000).
- Assigning a plan:
  - `POST /admin/tenants` (`admin.py:195`) and `PATCH /admin/tenants/{id}` (`admin.py:550`, plan logic around 596-620) set `plan_tier`, `plan_id` and `rpm`.
  - UI: `frontend/app/admin/tenants/page.tsx:87` (`PLAN_OPTIONS = starter/growth/business`) and `Tenant360Settings.tsx`.
- Gaps:
  - There is no CRUD route or admin page for `membership_plans`. Plan rows can only change through SQL or a migration.
  - The `acp_shared.acp_quota_ledger` limits (s2/s3/s4 runs) are hardcoded to 10/10/50 at tenant creation (`admin.py:238-245`). They ignore the plan, and a plan change does not update them.

**2. Content studio AI budget (AA-1016)**
- `shared.tenant_ai_budget` (migration 321) has these fields: `monthly_usd`, `alert_pct`, `approval_pct`, `hard_stop`, `notes`.
- The service is `apps/AA-CIS-App/api/services/tenant_ai_budget.py`. Its header says:
  - No row means unlimited.
  - Rows are created only manually, per tenant, through `PUT/DELETE /admin/ai-gateway/tenant-budgets/{tenant_id}` (`api/routers/admin_ai_gateway.py:154-175`). Each change is audited.
  - Default values are applied in code, not in the database (`DEFAULTS`, line 37: monthly null, alert 100, approval 150).
  - Enforcement is described as "a later gateway slice". The module only stores and reports the row.
- UI: `frontend/app/admin/ai-gateway/BudgetsTab.tsx` and Tenant 360 › Cost.
- Nothing links the budget to `plan_id` or `plan_tier`. Creating a tenant or changing its plan does not create a budget row.
- ADR `docs/adr/0009-ai-platform-and-provider-gateway.md:176-178` says the Content studio amounts "come from the business owner's plan prices". That is intended but not built.
- There is no `AA-1016*.md` implementation note in `apps/AA-CIS-App/docs/implementation-notes/`.

**3. CRM agencies (AA-Partner)**
- `crm.tenant_entitlement` (`apps/AA-Partner/api/migrations/008_crm_roles_members.sql:447-504`):
  - `plan` is limited by a CHECK to free/core/pro (default free).
  - `member_limit` defaults to 10.
  - `allowed_features[]` is limited by a CHECK to a fixed list: ai_assist, whatsapp_sms, stripe_connect, campaigns, custom_domain, insights_export.
  - A trigger allows writes only from platform contexts. No row means the code default, `DEFAULT_PLAN` in `api/app/members/team.py:43`.
- Enforcement:
  - Only `member_limit` is enforced (`team.py:270`).
  - `allowed_features`, including `ai_assist`, is stored but checked nowhere in `api/app`. The LLM gateway checks `crm.tenant_settings.ai_enabled` and `ai_budget_usd` instead (`api/app/llm/gateway.py:94,261`).
  - The AI budget defaults to $2 (`005_crm_intake_pipeline.sql:105`). The agency owner sets it (`agency_ai.py`), not the plan.
- Admin editing:
  - The CIS admin page `frontend/app/admin/platform/agencies/AgencyDrawer.tsx:355-390` calls `PUT /tenants/{id}/entitlements-allowed` (`apps/AA-Partner/api/app/routers/ops.py:626`, `ops/console.py:93`).
  - That page can only toggle features and the insights opt-out. There is no route to change `plan` or `member_limit`.
- Design docs:
  - `docs/audits/2026-10-21-S246-crm-design-v3/final/crm-design-final.md:94` says every agency is free at launch, with tiers later on triggers (cost over $150/month or 20 agencies). Line 163 puts "tier billing" in the backlog.
  - `lanes/data-privacy-integrations.md:133` plans `tenant_entitlement` as a mirror of a CIS contract `tenant.entitlements.v1` (plan, features, seat_limit, `ai_fair_use_usd`). That contract appears only in docs, with no code.

### What is missing for "define once, assign, limits follow"
1. **One plan catalogue for both products.** Either extend `shared.membership_plans` or add a new `shared.plan` table with a product column (content_studio or crm). It would need columns for: AI monthly USD with alert and approval percentages, `rpm`, the s2/s3/s4 quotas, `posts_per_week`, `member_limit`, features[], and price.
   - This replaces the hardcoded `PLAN_LIMITS`, the ledger's 10/10/50, the CRM free/core/pro CHECK, `DEFAULT_PLAN` and the $2 default.
2. **An admin CRUD page** under CIS `/admin` for the plans, audited and versioned. None exists today.
3. **Assignment that applies the plan.**
   - Content studio: creating a tenant or changing its plan should write `tenant_ai_budget` and `acp_quota_ledger` from the plan. Alternatively, the readers resolve values as plan default plus a per-tenant override, so an existing row acts as the override.
   - CRM: a plan or seat assignment route. Today only features can be toggled.
4. **Building the `tenant.entitlements.v1` contract** (CIS to Partner) so that `crm.tenant_entitlement` becomes a synced mirror of the plan.
5. **Enforcement.**
   - CRM: check `allowed_features` (for example, `ai_assist` should gate `ai_enabled`).
   - Content studio: the budget gateway slice, meaning the approval wait at `approval_pct`.
6. **Decide who owns the CRM AI budget:** the plan's fair-use amount or the owner-set `ai_budget_usd`. One option is a plan ceiling with the owner allowed to set a lower value.
