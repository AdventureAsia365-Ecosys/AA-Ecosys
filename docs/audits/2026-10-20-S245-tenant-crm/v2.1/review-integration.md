# Tenant CRM v2: independent review, integration + spec coverage lens

Date 20/10/2026 (S245, round 3). Reviewer: Claude Code subagent. Read-only: no repo, AWS, Vercel, Linear or Jira
change, and no paid API call. Web pages were accessed on 20/10/2026.

**Inputs read in full:** `owner-input.md`, `owner-approvals-r2.md` (round 2 overrides: N3 = b Fargate, H1 = b,
H4 = synthetic agencies, the D12/D22 "CIS can monitor" changes, and no prod cell until real agencies),
`docs/research/partner-crm-spec.md` ("spec"), `out/crm-design-v2.md` ("v2"), `out/crm-questions.json`,
`out/crm-01-current-state.md` ("scout") and `out/crm-judges.md` ("panel").

**Code refs used.** v2 cites older bases (CIS `b7e6da66`, Infra `4824c81`, TripPlanner `b79ec48`). I read the
current `origin/main` of each repo:

| Repo | Ref | Drift from v2's base |
|---|---|---|
| CIS | `4117d96d` | +1 commit, migration 251, not portal |
| Infra | `ede5e67` | +3 commits, including `08f73f6` "send SNS and budget alerts to the work inbox" |
| Booking | `e478663` | — |
| TripPlanner | `db7bb7b` | +4 commits, legal pages / docs / pin |
| root | `f8a9938` | — |

None of the drift changes v2's coupling line numbers. One v2 item is already done (finding L2).

Severity scale:
- **Critical:** blocks a spec differentiator, or the chosen design cannot work as written.
- **High:** wrong or missing integration contract; schedule or decision impact.
- **Medium:** gap that needs a concrete fix before real data.
- **Low:** hygiene.

---

## 0. Verdict in 12 lines

1. v2's separation plan (31 coupling points) is accurate where it was checked. The integration contracts it relies on are mostly unwritten, and some do not match what exists.
2. **Critical: AA live supply (spec §1 #1, modules 3/6) is not "6–7 Booking issues".** Booking has:
   - no cost sheet or price matrix;
   - no departures, allotments or holds;
   - no tenant on trip cases, and `customer_id` is NOT NULL;
   - no B2B settlement (ADR 0005 §9 says "AA invoices the tenant").

   Two of these are formally "waiting for decisions" in Booking's CONTEXT.
3. **Critical: N3 = b (Fargate behind CloudFront) has no working origin path as costed.** CloudFront's Free and Pro flat-rate plans exclude VPC origins. The shared ALB admits only the VPC CIDR.
4. **High: API Gateway `AWS_IAM` is not a boundary inside the VPC.** The ALB and NLB security groups admit the whole VPC CIDR, so any task (including CRM) can call `/booking/*` and the CIS default action directly.
5. **High: the acc3 Bedrock invoker** allows only `global.` Claude profiles (Haiku 4.5, Sonnet 4.6/5, Opus 5.5), with no `us.` profile, no Haiku 5.5, no `ApplyGuardrail`, and no CRM principal. D12 "us. only" + N10 Haiku 5.5 is not implementable today.
6. **High: the builder (D21 c) byte-copies only the frontend.** Routes, coverage, suggestions and tiles come from TripPlanner's Python backend. This is the same "route stitching" logic Nghiệp wants investigated.
7. **High: "catalog.v1" does not exist.** The real contracts (`catalog.tour.v1.1`, `catalog.graph.v1`) are DB-view contracts delivered by grants. The HTTP form must be designed, about 2–3 CIS issues.
8. **High: tenant roles conflict.** ADR 0006 membership = owner/editor/viewer; spec = owner/agent/assistant + margin visibility. A 1-minute mirror is too slow for revocation. There are also no WORKFORCE groups for AA ops / AA management.
9. **High: plan sync (owner's H2 note) needs a CIS→CRM entitlement contract** that v2 does not have.
10. **Spec walk (§9):**
    - 15 of 23 modules are covered;
    - 5 are covered only with a recorded deviation or an undecided external vendor (5, 7, 9, 12, 14);
    - 3 have a real gap (3, 6, 8: Booking/ops dependencies).
11. **E-sign (§5.1):** Dev needs no vendor at all, because CI already runs the self-hosted container. The vendor choice can wait until real agencies (H1 = b). Four options, including an in-house simple signature at $0, are listed for Ms. Thư.
12. **Net effect:**
    - roughly +14–20 issues, mostly Booking and Infra;
    - one hosting decision to re-open (N3 origin path);
    - one IAM/model decision (acc3);
    - Dev cost unchanged ±$2, or about +$16/month if ALB-free paths are rejected;
    - no new paid vendor needed for Dev.

---

## 1. Critical findings

### C1. AA live supply (spec §1 #1, modules 3, 6, part of 8) depends on Booking pieces that do not exist, and some wait on open decisions

**Evidence**
- **Pricing is manual today.** Quotes are priced only from staff-entered cost lines: `backend/app/pricing/service.py:1-5` says "Shared by `POST /booking/pricing/quote-preview` … and `POST …/versions/{n}/price`". `booking.version_item_costs` (`db-schema-reference.md:1687-1700`) holds hand-entered `net_amount` with an optional `supplier_rate_id`.
- **No tour-level cost sheet or price list.** `booking.trip_plans` has only `price_hint_*` (`db-schema-reference.md:1603-1620`). Booking CONTEXT lists "the trip plan price matrix / `v_from_prices`" under "Waiting for decisions" and "Out of scope today", along with "rate-sheet upload (rates are entered one by one under a draft contract)" (`apps/AA-Booking/CONTEXT.md:515-525`).
- **No departures, allotments or holds anywhere.** `grep departure|allotment` over the live dump finds only status enums.
- **Trip cases cannot carry an agency booking without PII.** `booking.trip_cases.customer_id uuid NN` and there is no `tenant_id` (`db-schema-reference.md:1559-1580`). A B2B hold or confirm cannot become a Booking trip case without either putting a traveller into `booking.customers` (which breaks v2's "hold carries no PII", v2 §10.1) or a schema change.
- **Settlement is required but uncovered.** ADR 0005 §9: "bookings arrive through a B2B channel carrying `tenant_id`; AA invoices the tenant, not the end customer. **Rate parity:** a tenant may not advertise below AA's public B2C 'from' price" (`docs/adr/0005-pricing-and-supplier-rates.md:74-77`). Neither is in v2. AA→agency invoicing is part of AA-682 "operations / money", also "waiting for decisions" (`Booking CONTEXT.md:515-517`).
- **What does exist.** Booking has component supply that fits the spec's option types:
  - `booking.services.service_type ∈ {activity, transfer, guide, entrance, meal}` (`db-schema-reference.md:1236`);
  - `booking.hotels` + `hotel_room_types`;
  - `booking.supplier_rates` (`room_night/person/group/vehicle/day`, `:1343-1378`);
  - a B2B rule channel (`pricing/engine.py:58`).

  This is a good base for spec §7 `OptionBlock.type ∈ day|activity|lodging|transfer`. v2 never maps to it: it names a `v_b2b_offer` that does not exist.
- **Currencies.** Booking selling currencies are `{"USD","EUR","GBP","AUD","SGD"}` (`engine.py:35`); the spec's NFR needs VND (spec §11.6).

**What the B2B API actually needs** (Booking repo owns all of it):

| # | Booking piece | Endpoint / migration | Blocked by |
|---|---|---|---|
| 1 | Service identity for CRM (not staff), carrying `tenant_id` per call | auth module (see H1) | — |
| 2 | Cost sheet: tour day → services/hotel rates by pax band × season (ADR 0005 §3) | bk-0xx + staff UI | "price matrix" decision (Booking CONTEXT :515) |
| 3 | Component catalogue for the builder: sellable trip plans + hotels/services linked to the catalog key `(source_system, source_id)` and `destination_id` | `GET /booking/b2b/v1/products`, `/components` | — |
| 4 | Quote per option line and per proposal: B2B price, FX lock, `valid_until`, `price_hash` | `POST /booking/b2b/v1/quotes` (reuses `pricing.service.price`) | #2 for tour-level options; synthetic rates on Dev |
| 5 | Availability | `fixed_departure` only; every other line returns `on_request` (H8 a) | departures data |
| 6 | Holds with expiry + reaper (`bk_hold_reap`, kind exempt from the deploy gate) | bk-0xx `b2b_hold` + `POST/DELETE /holds` | — |
| 7 | Confirm → B2B trip case: `tenant_id`, `channel='b2b'`, agency as the party, `customer_id` nullable for B2B or a per-tenant "agency customer" row | bk-0xx on `trip_cases` + transitions | AA-682 post-sale edges |
| 8 | Status/event feed for ledger auto-fill (conf no, net, currency, status) and F2 "AA trip history" | `GET /booking/b2b/v1/events?after=` (HTTP form of the outbox; no grants per N5) | — |
| 9 | AA→agency invoice and payment (settlement) | AA-682 | business terms (Questions §11) |
| 10 | Ops UI for B2B holds and confirmations ("AA ops confirm within 1 working day") | Booking admin pages | — |
| 11 | Rate-parity check (sell ≥ B2C "from") if Ms. Thư wants it enforced | `v_from_prices` | price matrix |

**Fix**
- Write `docs/contracts/booking.b2b.v1` (OpenAPI) in W0 from the table above.
- Re-count the Booking lane at **≈ 12–16 issues** (not 6–7) and name an owner.
- For "Dev as early as possible" with synthetic agencies:
  - seed synthetic suppliers, rates and FX on Dev;
  - ship rows 1, 3, 4 (component-level), 5 (`on_request`), 6, 7 and 8 first;
  - leave the tour-level cost sheet (#2) and settlement (#9) as decision-gated issues.
- Record "live price for whole AA tours needs the price matrix decision" as a spec dependency for Ms. Thư.

**Changes:** schedule (+6–9 Booking issues) and a decision (price matrix and AA-682 must be decided before real agencies). Cost: none.

### C2. N3 = b (agency app as a Fargate container behind CloudFront) has no costed origin path

**Evidence**
- **The Free and Pro plans exclude VPC origins.** CloudFront pricing: Free is "for hobbyists… VPC origins, uptime SLA, and private origin endpoints are not included". Pro likewise has "VPC origins … not included". Only **Business ($200/month)** includes "private origins within VPC" ([aws.amazon.com/cloudfront/pricing](https://aws.amazon.com/cloudfront/pricing/)).
- **The shared ALB cannot be a VPC origin and is closed to CloudFront.** VPC origins need the ALB "in the private subnet" ([VPC origins docs](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html)). The shared ALB is internet-facing (`modules/alb/main.tf:13`), and its SG admits only `cidr_blocks = [var.vpc_cidr]` on :80, with :443 closed (`modules/vpc/main.tf:261-273`). CloudFront therefore cannot reach a Fargate task on the shared ALB at all today.
- **The design's own fallback assumed a reachable origin.** v2 §3.4 described the Fargate fallback as "same container behind the same CloudFront, +≈ $8". The judges never costed the origin either.

**Options** (technical; the owner picks):

| Option | How | Extra $/month (Dev) | Notes |
|---|---|---|---|
| a | CloudFront **pay-as-you-go** (not flat-rate) + VPC origin on a **new internal ALB** | ALB ≈ $16+ (estimate, not re-priced) + CloudFront PAYG at Dev volume ≈ $0–1; VPC origins themselves have "no additional cost" ([AWS announcement](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-cloudfront-vpc-origins)) | Loses the bundled 5-rule WAF; edge WAF then costs ≈ $5 + $1/rule |
| b | Keep CloudFront Free. Open the **existing** ALB's HTTPS listener (it exists, `modules/alb/main.tf:92-97`) to the CloudFront managed prefix list `com.amazonaws.global.cloudfront.origin-facing` only. Add a listener rule `host = portal./go.` + a secret origin header → portal target group | ≈ $0 | Partly reverses the S235 Phase 0 closure of :443. The prefix list weighs heavily against the SG rule quota. Needs a custom header secret (rotate) |
| c | CloudFront Free → the portal's own **REST API** (public URL) → VPC link → ALB | ≈ $3.50/M requests | REST API buffers (no SSR streaming), 29 s timeout, 10 MB payload; every page view pays API GW |
| d | Revert to N3 a (Lambda + Web Adapter, public function URL with OAC) | ≈ $0–0.5 | Owner chose b over a; only if the spike or the owner revisits |

**Recommendation (technical):** option **b** for Dev, with two guards:
1. a listener rule that requires the origin-verify header;
2. the SG rule scoped to the prefix list only.

Re-check at prod time whether Business or option a is warranted.

**Previews:** the fixed `portal-pr.` host (v2 §3.4) now needs its own Fargate task, or must share the Dev task (last writer wins). Say which. Spot ≈ $2.5–3.3/month (v2 §9.2 basis).

**Changes:** decision (N3 origin path) and cost (b: $0; a: about +$16–25; c: request-based).

---

## 2. High findings

### H1. `AWS_IAM` on API Gateway is not a trust boundary for in-VPC callers (Booking B2B, CIS `/internal/v1/*`)

**Evidence**
- The ALB SG ingress is the VPC CIDR (`modules/vpc/main.tf:267-273`). The VPC-link NLB SG is also VPC CIDR (`modules/alb/vpc_link.tf:9-19`).
- `booking.tf:41-43`: "the CIS ALB … admits :80 only from the VPC CIDR … The gateway does no auth (authorization NONE …): the Booking app must authenticate every non-health route."
- So a CRM task, or any VPC workload (TripPlanner Lambdas run in the VPC, `tripplanner.tf:350`), can call `http://<alb>/booking/b2b/...` or a CIS `/internal/v1/tenant-members` path directly, with no SigV4 check.
- v2 §7.1 and §8 rely on "`AWS_IAM` on `/booking/b2b/*`" and "two internal endpoints `AWS_IAM`".

**Fix**
- **App-level service auth on both producers.** Options:
  - CRM signs a short-lived JWT with a KMS asymmetric key (`kms:Sign`, $1/key-month), verified by Booking/CIS against the public key;
  - or a Cognito machine (client-credentials) client.

  Either way the producer verifies the caller and `tenant_id` itself, and API Gateway `AWS_IAM` becomes defence in depth only.
- **Tighten the ALB SG:** ingress from the NLB SG (the NLB already has one, `vpc_link.tf:38`) instead of the VPC CIDR. This closes the bypass for CIS and Booking too.
- 2 issues (Infra + a shared verifier per producer).

**Changes:** schedule +2 issues; no cost (KMS key $1).

### H2. The acc3 Bedrock satellite cannot serve the CRM as decided (D12, N10, N9 fallback)

**Evidence**
- The trust policy allows only `aa-cis-dev-ecs-task-role` and `aa-tripplanner-dev-lambda-exec`, with a shared ExternalId `aa296-satellite-bedrock-acc3` (`infra/AA-CIS-Infra/accounts/acc3-bedrock/main.tf:21-52`).
- The invoke policy lists only `inference-profile/global.anthropic.claude-{sonnet-4-6, haiku-4-5-20251001-v1:0, sonnet-5, opus-5-5}` (and GPT/Cohere), with no `us.` profile (`main.tf:84-106`).
- There is no `bedrock:ApplyGuardrail` (grep: none).
- v2 §7.3 requires "Haiku 5.5 … profile `us.`, retention none" and Guardrails with "fallback acc3". The design's "CRM calls the acc3 satellite role like TripPlanner does" is true for the mechanism only.

**Fix** (an acc3-bedrock Terraform root change, separate MFA apply with profile `nghiep_aa365`):
- add a CRM task-role statement with its **own** ExternalId;
- allow the `us.` inference profiles for the chosen models;
- add `bedrock:ApplyGuardrail` on a CRM guardrail ARN;
- confirm that Haiku 5.5 / Sonnet 5.5 are enabled in acc3 us-west-1. Not verified: a W0 spike, free (no model call needed, `get-foundation-model-availability`).

**For the round-2 D12 change** (CIS must see CRM LLM calls and cost): create a Bedrock **application inference profile per app** with an `App=crm` tag, so the acc3 bill splits per app, and expose `GET /crm/ops/v1/llm-usage` (see H7). Today all three apps share one role, so acc3 cost cannot be attributed to the CRM except through the CRM's own estimates.

**Changes:** schedule (+1 Infra issue, separate account root) and a decision (if Haiku 5.5 is not available on `us.` in us-west-1, N10 falls back to Haiku 4.5 at its own price; re-price).

### H3. Builder (D21 c): the byte-copied map components need TripPlanner's backend logic, which is not part of the copy

**Evidence**
- **MapView pulls in the TP API layer.** It imports `fetchByCountry, fetchTile, tileScope` from `@/lib/api`, plus `useTrip`, `fetchRouteLegs` (Mapbox Directions) and `TileLoader` (`AA-TripPlanner-Web/frontend/components/MapView.tsx:1-17`).
- **The `lib/api.ts` it needs is about 20 functions over TP's own backend:**
  - `/api/browse` for tiles, countries, routes, catalog tours, tour route;
  - `/api/trip` for trip, components, reorder, coverage, suggestions, `applyRoute`, `addDay`, narrate.

  (`frontend/lib/api.ts:26-340`.)
- **RoutePlanner (173 lines) is a thin UI.** It calls `fetchRoutes` and imports `@/ui/Icon` (not in v2's import list).
- **The route logic lives in TP Python:** `backend/browse/routes.py`, `backend/assembly/{coverage,suggestions,handler}.py`.
- **Styling and filename mismatches.** TP uses Tailwind **3.4.14** (`frontend/package.json:29`); the portal uses Tailwind **4** (`portal/package.json:21,27`). The copied components use Tailwind classes (RoutePlanner has 22 `className=` uses). The file is `useTrip.tsx`, not `.ts`.
- **v2 §3.4 underestimates the work.** It plans "adapter with the same function signatures for `lib/tp/api.ts` and `lib/tp/useTrip.ts`" and allows only "a thin wrapper". An adapter that reimplements route proposals, coverage and stop activities is a third copy of TP's assembly logic, not a wrapper.

**Fix:** decide one of the following (technical; ties to the owner's new "investigate route stitching" issue, which should explicitly include "how the CRM builder reuses stitching"):
- (i) TripPlanner exposes a versioned read API `tp.routes.v1` (routes, coverage, tiles) that the CRM calls server-side. TP becomes a producer: new contract, TP lane issues ≈ 2–3.
- (ii) Move stitching into CIS as a `catalog.graph`-derived read API that both TP and the CRM use (bigger, cleaner).
- (iii) The CRM reimplements it (a third copy; reject).

Either way, the drift guard must cover: the TP Tailwind config/tokens, `ui/Icon`, and a CI build under Next 16 + Tailwind 4 (or vendor TP's Tailwind 3 config as a scoped CSS build).

Mapbox Directions is a separate meter from map loads (v2 §8 counts map loads only). The Mapbox token's URL restrictions must add the new hosts. ⚠️ The token is the underscore env var `NEXT_PUBLIC_MAPBOX_TOKEN` (`frontend/lib/mapbox.ts:4`): Nghiệp edits it by hand.

**Changes:** schedule (+2–4 issues TP/CIS) and a decision (i or ii). Cost ≈ $0.

### H4. "catalog.v1" is not an existing contract; the HTTP projection must be designed

**Evidence**
- **No contract by that name.** `docs/contracts/README.md` registers `catalog.tour.v1` / `v1.1` and `catalog.graph.v1` as **views in schema `catalog`**. The rules are "Owner … the read view" (rule 1) and the producer's migration "grants `SELECT` on the view to the consumer role" (rule 5). There is no `catalog.v1`.
- **N5 a needs a new HTTP projection.** v2 N5 a (no grants, approved) means CIS must build `GET /internal/v1/catalog/*` covering:
  - `v_tour` + `v_tour_day`, `v_tour_place`, `v_tour_photo`;
  - `v_destination`;
  - the 7 graph views (if H3 ii);

  with paging, a `content_hash` re-sync and liveness ("a tour that leaves the catalog is simply absent").
- **The membership feed cursor breaks the contract rules.** It is `GET /internal/v1/tenant-members?since=` (v2 §7.1), a timestamp cursor. That conflicts with README rule 4 ("must not use the producer's BIGSERIAL id as the only cursor … anti-join … or keep a lag window"); a timestamp has the same out-of-order problem.
- **The original N5 reason has gone.** With H1 = b and no prod cell until real agencies, N5's main reason ("the prod cell has its own RDS") no longer applies right now. N5 a stays valid for the future cell, but it costs more CIS work than v2 counts ("2 small endpoints").

**Fix**
- Add `docs/contracts/catalog.http.v1.json`: the same payloads as `catalog.tour.v1.1` / `catalog.graph.v1` over HTTP, a snapshot + `content_hash` list endpoint, and per-tour detail.
- Add `tenant.membership.v1`: a full snapshot (small) + an ETag, or an outbox `id` with a lag window.
- Count 3 CIS issues, not 1. Producer and consumer tests use the same samples (README rule 7).

**Changes:** schedule (+2 CIS issues); no decision change.

### H5. Tenant identity and roles: two role models, a slow revocation path, and missing staff groups

**Evidence**
- **ADR 0006 already fixes the tenant role model.** It defines the tenant membership table with "`role` (`owner` / `editor` / `viewer`)", resolved "on each request (cache ≤ 60 s, invalidated on any membership write)", and only `owner` invites (`docs/adr/0006-ecosystem-identity.md:139-145,400`).
- **The spec needs different roles.** It wants owner / agent / assistant with margin visibility (spec §3, F4 "New user set up in under 5 minutes").
- **v2 adds a third structure.** It adds `crm.member_role` plus `crm.member_mirror` "pulled from CIS ≤ 1 minute" (v2 §7.1). A removed agency user would keep CRM access for up to 1 minute plus cache, and two screens or two writes would set up one person.
- **No staff groups for the CRM's AA users.** WORKFORCE groups are only `cis-admin|reviewer|content`, `booking-admin|sales|contracting|content_creator` (`infra/.../identity.tf:134-143`), "Written only by the staff directory (AA-816)" (`identity.tf:498-499`). There is no group for spec "AA ops" (module 8) or "AA management" (module 17).
- **Token audiences need allow-listing.** Booking accepts WORKFORCE tokens only from its own client ids (`AA-Booking/backend/app/auth/identity_config.py:5-6,55`). The CRM must explicitly allow-list `booking-staff` (ops page) and `cis-admin` (insights, observability) client ids.

**Fix**
- Amend AA-813 before building it: membership + **per-app grants** (`tenant_member_app_grant`: `content ∈ {owner, editor, viewer}`, `crm ∈ {owner, agent, assistant}`). This mirrors the existing staff pattern `shared.staff_app_grant` (ADR 0006 line 5).
- Use one team screen in AA-Partner that calls CIS.
- The CRM resolves membership per request through `tenant.membership.v1` with a ≤ 60 s cache and a CIS→CRM invalidation call on every write (same rule as ADR 0006).
- Add WORKFORCE groups `crm-ops` and `crm-insights` via the staff directory (CIS) + `identity.tf`.

**Changes:** schedule (+1–2 issues, mostly re-scoping AA-813, which is "M5 security order #1", `docs/backlog/README.md:112`); no cost.

### H6. Separating `portal/` from AA-CIS-App: v2's single W1 bundle is not a safe cutover order, and the coupling list misses a few items

**Evidence**
- v2 W1 packs into one wave of 21 issues (v2 §11):
  - the repo move;
  - the hosting move (Vercel → AWS);
  - AA-813 (Cognito login + closing API-key login);
  - the BFF allow-list;
  - the trip-page move;
  - deleting `portal/`.
- **Couplings beyond the 31 points** (all `origin/main`):
  - `tests/e2e/smoke/aa885-portal-redirect.spec.ts` (asserts the 308s that L3 deletes);
  - `tests/e2e/smoke-portal/*` (must move);
  - `frontend/lib/rbac.ts:44` and `frontend/proxy.ts:53` (portal comments);
  - CIS `CONTEXT.md:9,54-55,852` (`applies_to: aa-cis-portal`, route table);
  - the `VERCEL_PORTAL_BYPASS_SECRET` / `VERCEL_PORTAL_PROJECT_ID` repo settings (`vercel-deploy-portal.yml:17-19,58`);
  - the non-required `portal-lint` job, which carries 9 pre-existing errors (`ci.yml:257-260`): the new repo's required lint would start red.
- **L6/L7 (trip page) are more than a host move:**
  - The page is aa_internal-only and keyed by `tour_id`. The docstring says "Real per-TENANT rewritten versions … are NOT wired into this page yet" (`api/routers/v1_trip_page.py:30-40`).
  - The URL is written by an admin-triggered publish into `acp_deliver.tenant_tour_pages` (`:140-163`) and consumed by the T10 gate F6 and planning runway (`services/acp_planning/runway.py:152-205`, `tenant_pool.py:66`).
  - `tour_id` changes on re-upload (catalog key = `source_id`, `catalog.tour.v1.json` description).
  - v2's `go.…/t/{tenant}/{tour}` therefore needs per-tenant page data in CIS (new content work) and a stable key.
  - URLs already handed out on published posts keep pointing at `aa-cis.lumiguides.it.com/trip/{id}`.

**Fix: ordered cutover.** Each step can be deployed alone, and tenants keep working at every step.

| Step | Repo | Content | Tenants impacted? |
|---|---|---|---|
| S0 | CIS | B3 fix (staff token → 401); D18 CTA; add `/v1/brand-identity` **alongside** `/admin/brand-identity`; generate `cis.tenant-api.v1` from the literal paths the portal calls + a contract test | No |
| S1 | root + AA-Partner | `git filter-repo` the portal into AA-Partner. **No behaviour change:** API-key login, same cookies, same paths. Deploy the container to a staging host (`portal-next.`) on the C2 origin path; run the portal smoke there | No |
| S2 | Infra/DNS | Flip `portal.lumiguides.it.com` to CloudFront. Keep Vercel `aa-cis-portal` for 1 week as the rollback | Sessions reset once |
| S3 | CIS | Delete `portal/`, the two workflows, the redirect e2e spec and L1/L3/L4/L5. Invert the guard test. Update CONTEXT | No (portal is already served from AA-Partner) |
| S4 | CIS + AA-Partner | AA-813 (amended per H5) behind a flag. **Dual-auth window:** the CIS tenant routes accept both the HS256 tenant JWT and Cognito + membership. Invite each test tenant's owner, then close the human API-key login | Re-login via invite |
| S5 | AA-Partner | Switch on the BFF allow-list (after the S0 contract test is green); drop `/admin/brand-identity` use; `pp_*` cookies | No |
| S6 | CIS + AA-Partner | Trip page: keep CIS `GET /v1/trip/{id}`; AA-Partner serves `go.…/trip/{source_id}` (aa_internal) first. **Keep a 301 from `aa-cis…/trip/*`** to the traveller host. That is a traveller URL, not an admin↔portal link, so it does not break the owner's separation rule. Per-tenant pages = a separate CIS issue | No |

Then CRM pages (W2+), in parallel with the CRM API skeleton (`crm.tf`, owners, runner), which has no dependency on S0–S6.

**Changes:** schedule (+2–3 issues: S6 per-tenant data, redirect, contract generator); the order is safer. No cost.

### H7. The round-2 changes (CIS monitors CRM jobs and LLM calls) and the owner's H2 note need contracts v2 does not have

**Evidence**
- **No cross-app job view exists today.** CIS's job admin reads only its own runner: `GET /admin/job-runner/summary` (`api/routers/admin_job_runner.py:7`, `frontend/app/admin/jobs/page.tsx:198`). It does not observe `booking.job` today either.
- **CRM calls cannot reach the CIS LLM pages by DB.** The CIS LLM ops pages read `shared.llm_call_log` by SQL (`api/routers/admin_llm_ops.py`, among 9 routers using it). CRM calls in `crm.llm_call` cannot reach them without a grant (N5 forbids it).
- **The owner wants CRM plans synced with portal plans.** H2 note: "subscription plan synced with the tenant portal plan". The portal plan lives in CIS (`shared.tenants.plan_tier`, `/v1/billing`, `/v1/quota`, scout §1). v2 has no plan/entitlement contract for the CRM.

**Fix: three small HTTP contracts, CRM as producer (first two) and CIS as producer (third).**
- **`ops.job_summary.v1`:** the same shape as CIS `/admin/job-runner/summary`, served by the CRM at `/crm/ops/v1/job-runner/summary`. The CIS admin BFF calls it with the staff's `cis-admin` access token, and CIS shows a "CRM" tab. Reusable for Booking later.
- **`llm.usage_summary.v1`:** `/crm/ops/v1/llm-usage?from&to`, returning per day × stage × model: calls, tokens and estimated cost. **No tenant names and no text.** The CIS cost page merges it next to `shared.llm_call_log`.
- **`tenant.entitlements.v1`** (CIS → CRM): plan tier, CRM feature flags and the AI cap per tenant, cached like membership (H5).

The DB Migrate idle gate already discovers every `<schema>.job` automatically (`.github/workflows/db-migrate.yml:21`). `crm.job`'s periodic kinds (membership pull, mail ingest, workflow tick) **must** be in `IDLE_EXEMPT_KINDS` from day one, or every CIS/Booking/TP migration will block (v2 §3.3 says this; keep it).

**Changes:** schedule (+3 issues); no cost; the H2 decision itself goes to Ms. Thư.

---

## 3. Medium findings

### M1. Email (module 5, D6 b): verification, token, quota and encryption details

**What was verified**
- **CASA is not needed for `gmail.send`.** It is **Sensitive**, while `gmail.readonly`, `gmail.compose` and `gmail.modify` are **Restricted** ([Gmail scopes](https://developers.google.com/workspace/gmail/api/auth/scopes)). CASA (Google's Cloud Application Security Assessment) applies only to restricted scopes, so D6 b correctly avoids it.
- **Google OAuth app verification is still needed** before real agencies: brand, homepage, privacy policy, scope justification.
- **On Dev the app stays in "Testing".** Refresh tokens then expire in 7 days ("is issued a refresh token expiring in 7 days", [Google OAuth2](https://developers.google.com/identity/protocols/oauth2)). Synthetic agency mailboxes must re-consent weekly; plan for this in E2E.
- **Refresh-token cap:** "100 refresh tokens per Google Account per OAuth 2.0 client ID".
- **Microsoft `Mail.Send` (delegated, multitenant):** users in other tenants "can't consent to most newly registered multitenant apps that aren't publisher verified" when risk-based step-up consent is on. Publisher verification is free but needs a Microsoft AI Cloud Partner Program account and an **Entra work/school tenant** with a verified domain ([publisher verification](https://learn.microsoft.com/en-us/entra/identity-platform/publisher-verification-overview)).
- **SES receiving works in us-west-1** (`e2e_mailbox.tf:15-18`).
- **SES quota problem:** "Maximum number of rules per receipt rule set: **200** (not adjustable)"; 500 recipients per rule ([SES quotas](https://docs.aws.amazon.com/ses/latest/dg/quotas.html)). v2's "one rule per agency in the single active set" (v2 §8, shared with e2e) fails before 200 agencies.
- **Raw inbound mail is not under the agency key.** v2 stores it in an S3 "mail in" bucket before the worker knows the tenant (v2 §3.1). That contradicts F1 ("encrypted with the agency's own key") for the raw copy.

**Fix**
- Use **one** domain rule (`in.crm.lumiguides.it.com`) → S3 with a CRM ingest KMS key, object TTL 1 day. The ingest job re-encrypts each message under the agency DEK at once and deletes the raw copy, writing an audit row.
- Document "raw copy ≤ 1 day under the CRM key" as an F1 note.
- The Google/Microsoft verifications are external processes: list them for Ms. Thư (branding domain, legal entity).

**Changes:** schedule (≈ +1 issue); cost $0; one decision (domain for the OAuth consent screen).

### M2. Module 18 "verified deletion" vs backups and third parties

v2 deletes a traveller by dropping the DEK (crypto-shred) and deletes an agency by `ScheduleKeyDeletion` (v2 §7.2). Two gaps:
- **Per-traveller:** the wrapped DEK row stays in RDS PITR backups (14 days on the cell, v2 §10.1) and in snapshot copies. It stays decryptable with the still-live agency key until those backups expire.
- **Third parties hold copies:**
  - Documenso Cloud: signer name, email and signed PDF;
  - Meta and Twilio: agency-owned message history;
  - the SES raw mail (M1).

**Fix**
- The deletion receipt states a "backups purge by <date>" window.
- Deletion calls the e-sign provider's delete API, or uses the self-host / in-house options (§5.1), which keep the data inside the CRM.
- Message history held by the agency's own WABA/Twilio is out of AA's control: say so in the export/delete UI.

**Changes:** none to cost; +0.5 issue.

### M3. Module 8 vs how ops actually works

- **v2's model:** ops-release PII stays in the CRM under the AA-ops key, and AA ops read it in a Booking-admin page (v2 N6, approved).
- **What ops needs:** ADR 0005 §8 says "Ops checks availability and books suppliers". Hotels and transfer suppliers need passenger names (rooming lists, vouchers). The data will leave the system by email or export, and the spec's "deleted automatically 90 days after the trip … deletion can be verified" then covers only the CRM copy.
- **Missing pieces:** the Booking-admin page also needs the H5 `crm-ops` group, and an export that is itself audited and watermarked.

**Fix:** a "supplier manifest" export from the CRM ops page (PDF/CSV, logged to the agency audit, with an expiry notice). The scope of what suppliers receive goes to Ms. Thư.

**Changes:** +1 issue; no cost.

### M4. Payments (module 7): Stripe Connect Standard

**What was verified**
- **No platform fee on Standard.** Stripe charges the platform "No fees for your platform" when "Stripe handles pricing for your users" ([stripe.com/connect/pricing](https://stripe.com/connect/pricing)). AA cost = $0, as v2 says.
- **Vietnam is not a Stripe country.** "Vietnam: Not listed"; Australia, Singapore, Malaysia and Thailand are listed ([stripe.com/global](https://stripe.com/global)). VN agencies need D10 a (manual + VN gateway). That matches v2, but the gateway vendor is an external-app choice for Ms. Thư, not engineering.
- **Spec §9 edge cases** (failed payment, refunds, multi-currency) need explicit Stripe webhooks: `payment_intent.payment_failed`, `charge.refunded` and `account.updated` (Connect). v2 lists only "pay links, webhooks". VND is not in Booking's selling currencies (C1).

**Changes:** +0.5 issue.

### M5. WhatsApp / Messenger / Instagram (module 9, D9 a, D19 a)

**What was verified:** to become a Tech Provider for Embedded Signup you need:
- a Meta app;
- **business verification** ("must be verified before you can start the app review process");
- **App Review** with two screen-recorded videos;
- advanced access to `whatsapp_business_messaging` and `whatsapp_business_management`;
- onboarded clients "must add a credit card" ([Meta Tech Provider docs](https://developers.facebook.com/docs/whatsapp/solution-providers/get-started-for-tech-providers)).

Messenger and Instagram need their own permissions and App Review.

**Dev with synthetic agencies:** the Meta app's own test number works in development mode without review. External review can start later, but the clock is 2–4+ weeks (spec §10 non-code track).

**Spec deviation to record:** the spec names "Twilio / 360dialog" (spec §6 module 9, §9). D9 a is Cloud API direct, and SMS = the agency's own Twilio (N12). Add both to the v2 §5 deviation list for Ms. Thư.

**Changes:** none (timing only).

### M6. Traveller-facing host and brand

- **Hosts:** v2 serves intake, proposals, the client portal and OTP mails from `go.lumiguides.it.com` and `no-reply@lumiguides.it.com` (v2 §3.4, scout SES row). `lumiguides.it.com` is the ecosystem's **Dev** hostname family (project CLAUDE.md "Dev hostnames").
- **What travellers would see:** an Australian agency's travellers would see that domain on every link and mail.
- **Technical options:**
  - per-agency custom domain: CloudFront alternate names, ACM certificates, and the agency's DNS CNAME;
  - per-agency SES DKIM identity (v2 mentions it as a fallback only);
  - or a neutral production domain.

**Changes:** a decision for Ms. Thư (brand); small cost (ACM free; Route 53 zone $0.50 if a new domain; the domain itself is a vendor cost).

### M7. AI agent layer (module 14) dependencies

Spec: "Module 14 needs F3, F5, 5 and 9" (`partner-crm-spec.md:200`). v2 places 14 in W7 after 9 (W6): consistent. Two items are open:
- the acc3 changes (H2);
- the Guardrails availability spike on acc2 vs acc3. Memory says acc2 Bedrock LLMs are blocked by the reseller; ApplyGuardrail may be too. If it runs on acc3, raw unscrubbed text crosses accounts before scrubbing. That is AA-internal, but state it in F3's design and the DPA sub-processor list (both accounts are AA's).

---

## 4. Low findings

- **L1.** v2 §11 "Out of CRM but asked: change `alert_email` to `nghieppham@adventure.asia`" is **already merged** (Infra `08f73f6`). Remove it from the plan; confirm the SNS subscription only.
- **L2.** Spec module 1: "first reply under 2 hours" needs an **agent notification** (email/web push) when an Inquiry lands. v2 creates only a task (v2 §6). Add the notification to `crm_intake_process` (SES, $0).
- **L3.** Portal BFF → CRM API currently goes portal task → NAT instance (`t4g.nano`) → `api-crm` public → VPC link → ALB. Both are in the same VPC; once H1 locks the ALB SG, add an explicit SG rule from the portal SG, or use ECS Service Connect for BFF→CRM. Keep `api-crm` for webhooks and public routes only (saves NAT hops and API GW requests).
- **L4.** The traveller client portal OTP duplicates Booking's own OTP tables (`booking.customer_otps`, `customer_sessions`). That is fine across separate apps, but reuse Booking's tested rate-limit and lockout rules as the spec for the CRM version.
- **L5.** Spec §9 builder events `itinerary.sent/accepted/updated`: with the builder inside the app, these become internal events. Keep the names in `crm.metric_event`, so spec §11.7 tracking and module 3 metrics ("upgrade picked ≥ 20%") are measurable.

---

## 5. Integration contracts: what exists, what v2 assumes, what is needed

| Contract | Producer → consumer | Exists today? | v2 says | Needed (owner repo) |
|---|---|---|---|---|
| Catalog | CIS → CRM | Views only: `catalog.tour.v1.1`, `catalog.graph.v1` (`docs/contracts/README.md` registry) | "catalog.v1" over `GET /internal/v1/catalog/*` | `catalog.http.v1` (CIS), H4 |
| Membership | CIS → CRM | No (AA-813 not built; ADR 0006 :139-145) | feed `?since=`, mirror ≤ 1 min | `tenant.membership.v1` + per-app grants + invalidation (CIS), H5 |
| Entitlements / plan | CIS → CRM | No | — | `tenant.entitlements.v1` (CIS), H7 |
| Tenant content API used by the portal | CIS → AA-Partner | Implicit (`/v1/*` + `/admin/brand-identity`) | `cis.tenant-api.v1` + contract test | Same, generated from the portal's literal paths (CIS + AA-Partner), H6 S0 |
| Trip page data | CIS → AA-Partner | `GET /v1/trip/{tour_id}` public, aa_internal only | Move the page; backfill URLs | Key by `source_id`; per-tenant data = new CIS issue; 301 kept (H6 S6) |
| B2B supply | Booking → CRM | **No** (only a `b2b` pricing channel) | 6–7 issues | `booking.b2b.v1` (Booking), C1 table, 12–16 issues |
| Service auth | CRM → CIS/Booking | No (API GW auth NONE everywhere) | API GW `AWS_IAM` | App-verified service JWT + ALB SG tightening (Infra + producers), H1 |
| Route stitching / tiles | TP (or CIS) → CRM | Inside TP (`backend/browse`, `backend/assembly`) | Byte-copy the frontend only | `tp.routes.v1` or a CIS graph API, H3 |
| CRM jobs and LLM usage | CRM → CIS admin | No cross-app precedent | Not specified | `ops.job_summary.v1`, `llm.usage_summary.v1` (CRM), H7 |
| Ops release / insights | CRM → Booking admin / CIS admin | — | `/crm/ops/v1`, `/crm/insights/v1` with WORKFORCE | + `crm-ops` / `crm-insights` groups + client-id allow-list (H5) |
| E-sign | Vendor ↔ CRM | — | Documenso API + webhook | Provider-neutral `esign` adapter interface (§5.1) |
| Payments | Stripe ↔ CRM | — | Connect Standard, pay links | + failure/refund/account webhooks (M4) |
| Messaging | Meta / Twilio ↔ CRM | — | Embedded Signup, BYO Twilio | as v2 + record the spec deviation (M5) |
| Email | Agency Gmail/Outlook + SES ↔ CRM | SES rule set exists (e2e) | Rule per agency | One domain rule + re-encrypt (M1) |

---

## 5.1 E-sign (module 12): technical options for Ms. Thư (none decided here)

**Facts** (all accessed 20/10/2026):
- **Documenso pricing** ([documenso.com/pricing](https://documenso.com/pricing)):
  - Free: "5 documents per month", no API listed;
  - Teams: $40/month or **$480 billed yearly**, "Includes 5 users", "API Access for Automation", "Embedded Signing";
  - Platform: $250/month or **$3,000 billed yearly**, "Embedded Signing (Whitelabel)";
  - self-hosted Enterprise: quote only.
- **Documenso Community Edition** is AGPL-3.0. You may "Run Documenso for any purpose, including commercial use", but offering signing services triggers AGPL source obligations ([CE policy](https://docs.documenso.com/docs/policies/community-edition)). Enterprise features such as "embed authoring white label" need a licence key ([search summary of Documenso docs](https://docs.documenso.com/docs/policies/enterprise-edition)). Whether plain **embedded signing** works in CE is **not stated**: verify in the W0 CI container.
- **OpenSign** is AGPL-3, Node + MongoDB ([github.com/OpenSignLabs/OpenSign](https://github.com/OpenSignLabs/OpenSign)). Third-party reviews say API tokens in self-hosted need a paid plan ([verdocs.com/blog/opensign-pricing](https://verdocs.com/blog/opensign-pricing), a competitor source, unverified). MongoDB is a new datastore for this platform.

| Option | AA cost/month | Engineering | Data location | Insurer / legal | Fit |
|---|---|---|---|---|---|
| A. Documenso Cloud Teams | $40 (annual $480) | Adapter + webhook ≈ 2–3 issues | Documenso's cloud (sub-processor holds signer PII + PDFs) | Standard e-sign audit trail; insurer to confirm | Needs written OK for multi-agency use; Documenso branding possible (H12) |
| B. Documenso Cloud Platform | $250 (annual $3,000) | Same | Same | Same | White-label |
| C. Self-hosted Documenso CE in acc2 | ≈ $5–17 compute (Fargate 0.5 vCPU/1 GB ARM: on-demand ≈ $16.6, Spot ≈ $5–7, **estimate** from v2 §9.1 unit prices) + a signing certificate (Dev: self-signed; prod: CA document-signing certificate, price **unverified**) | Same adapter (CI already runs this container, v2 §8) + ops (upgrades, SMTP via SES, its own Postgres DB **outside DB Migrate**: Prisma migrations, so it needs its own database/role and connection budget) | Inside acc2; deletable with the CRM | Same trail; AGPL obligations if modified; embed licensing to verify | No vendor; fully inside the privacy boundary |
| D. In-house simple e-signature | $0 (+ $1/month KMS asymmetric key for the PDF seal) | ≈ 3–4 issues: server-rendered terms/waiver PDF; client-portal OTP (email possession) + typed name + explicit "I agree" + timestamp, IP (the HMAC-signed forwarded IP of v2 §7.4) and user agent; document SHA-256; PAdES seal by an AA key in KMS (`kms:Sign`); appended audit certificate; stored under the agency key; signed copy emailed | Inside the CRM | A "simple electronic signature" level; whether the insurer accepts it is the real gate (spec module 12 success = "accepted by insurer"). Legal validity per country is for counsel (D15) | Cheapest, simplest data story; no vendor API to pass in review |

**Engineering view** (decision stays with Ms. Thư):
- **Build the adapter provider-neutral** (`esign.create_envelope / status / signed_pdf / delete`), so A, B, C and D are interchangeable.
- **Dev needs no paid vendor:** under H1 = b, Dev uses C (already planned for CI). The vendor/plan choice (N8, H12) can therefore wait until just before real agencies.
- **The insurer question (H6) decides between D and A/B/C,** so ask the insurer first.

**Changes:** removes $40–250/month from the Dev period; the decision moves later.

---

## 6. N3 = b, H1 = b, H4: what changes in v2's plan (integration view)

- **The prod cell (v2 §10.1, W5) leaves the pre-real-agency scope.** Remove from the "Dev ASAP" path:
  - `envs/prod`;
  - the C7.2a exception;
  - the restore drill;
  - the DB Migrate `environment` input.

  That is about −4 issues before Dev readiness; they come back before the first real agency.
- **All external vendors can run in test/sandbox on Dev:**
  - Stripe test mode;
  - the Meta test number;
  - Google "Testing" (7-day tokens, M1);
  - Microsoft in AA's own tenant (if AA has one);
  - Documenso self-hosted.

  None needs a paid plan or a contract before real agencies.
- **The Dev readiness path (technical order):**
  1. CRM API skeleton + runner + `crm-001`;
  2. portal cutover S0–S3 (H6), in parallel;
  3. AA-813 amended (H5);
  4. F1–F5;
  5. modules 1/2/4/5/15/16-basic;
  6. Booking B2B rows 1, 3–8 with synthetic rates (C1);
  7. builder after the H3 decision;
  8. modules 7/11/12/13/8 in test mode;
  9. modules 9/10/14/17/18.
- **Cost on Dev:**
  - v2's ≈ $11–13/month stands;
  - plus C2 option b ($0), or option a (≈ +$16–25);
  - plus the Documenso CE container in CI only ($0) or as a Dev service (≈ $5–7 Spot, estimate).

---

## 7. Spec walk, all 23 modules

Legend:
- ✅ covered by v2 as designed;
- ⚠️ covered with a recorded deviation, or only by an external vendor/app still undecided;
- ❌ gap: v2's coverage depends on something that does not exist or is under-scoped.

| # | Module | v2 coverage | Status | What is missing / reference |
|---|---|---|---|---|
| F1 | Identity vault | KMS key per agency + DEK per traveller | ✅ | Raw inbound mail ≤ 1 day under the CRM key (M1); backups window for deletion (M2) |
| F2 | Pseudonymous profile | `crm.traveler_profile` + NOLOGIN readers | ✅ | "AA trip history" needs the Booking B2B event feed (C1 row 8) |
| F3 | PII scrubber | known values → regex → Guardrails | ✅ | acc3 `ApplyGuardrail` grant + availability spike (H2, M7) |
| F4 | Tenancy & access | AA-813 + `crm.member_role` + RLS | ✅ with fix | Role model / revocation (H5) |
| F5 | Audit log | hash-chained `crm.access_event` | ✅ | Include AA-ops exports (M3) |
| 1 | Intake form | Traveller host + widget + intake job | ✅ | Agent notification for "< 2 h" (L2); traveller domain (M6) |
| 2 | Trip pipeline | Board + timeline + panel; "quiet 3 days" in W6 | ✅ | — |
| 3 | Interactive proposal | Proposal model + picker + live price + rules | ❌ | Booking quote/availability/hold not built and partly decision-gated (C1); builder backend logic (H3) |
| 4 | Text proposal | Renderer, shared price hash | ✅ | Price hash must come from the Booking quote (C1 row 4) |
| 5 | Unified inbox (email) | Forwarding in + `gmail.send`/Graph out | ⚠️ | Deviation from "two-way sync" (recorded); Google/Microsoft verification external (M1); SES rule cap (M1) |
| 6 | Bookings ledger | `crm.booking_line`, AA lines auto | ❌ | Auto-fill needs Booking confirm + event feed + B2B trip case (C1 rows 7–8) |
| 7 | Invoices & payments | Stripe Connect Standard; VN manual | ⚠️ | VN gateway vendor undecided (D10 a); failure/refund webhooks (M4); AA→agency settlement not covered (C1 row 9) |
| 8 | AA ops release | In CRM, AA-ops key, Booking admin page | ❌ | No `crm-ops` group (H5); supplier manifests leave the system (M3); depends on B2B confirm (C1) |
| 9 | Inbox (WhatsApp/SMS) | Embedded Signup + BYO Twilio | ⚠️ | Meta Tech Provider + App Review external; spec names Twilio/360dialog → deviation (M5) |
| 10 | Workflow automation | `crm.workflow_*` + tick | ✅ | Tick kinds in `IDLE_EXEMPT_KINDS` (H7) |
| 11 | Client portal | Traveller host, signed link + OTP | ✅ | Brand/domain (M6) |
| 12 | Contracts & waivers | Documenso (N8 b pending written OK) | ⚠️ | Vendor/plan undecided; insurer acceptance; alternatives §5.1 |
| 13 | Commission tracking | expected/received + overdue | ✅ | AA lines are a net model: commission applies to non-AA suppliers; state it in the UI |
| 14 | AI agent layer | Haiku default, scrub, approval | ⚠️ | Model/profile not allowed on acc3 today (H2); CIS cost view contract (H7) |
| 15 | Supplier directory | `crm.agency_supplier`, AA default | ✅ | Builder must accept non-AA items without catalog geo (H3) |
| 16 | Agency reports | basic W3, full W7 | ✅ | Option-pick events (L5) |
| 17 | AA insights | k ≥ 10, ≥ 3 agencies, opt-in, CIS admin page | ✅ | `crm-insights` group + `cis-admin` client allow-list (H5) |
| 18 | Data portability | export/delete W5, full W7 | ✅ with fix | Backups window + third-party deletion (M2) |

**Count:** ✅ 15 · ⚠️ 5 (5, 7, 9, 12, 14) · ❌ 3 (3, 6, 8).

**Non-module spec sections:**
- **§1 "AA trips, net rates and availability … confirmed automatically":** ❌ until C1. The H8 "on request" deviation is already recorded.
- **§4 pipeline gates:** "Booked when deposit paid" needs the Stripe webhook or a manual mark: ✅.
- **§9 integration "AA inventory API: hold expiry, error/outage behaviour":** C1 rows 4–6 must define the hold TTL and the "Booking down" behaviour in `booking.b2b.v1`.
- **§10 dependency "Module 3 needs the inventory API and the builder contract":** both open (C1, H3).
- **§11.6 currencies AUD/USD/VND/EUR:** VND missing in Booking (C1).

---

## 8. Ranked fix list with impact

| Rank | Finding | Fix (short) | Cost | Schedule | Decision |
|---|---|---|---|---|---|
| 1 | C1 Booking B2B | Write `booking.b2b.v1`; Booking lane 12–16 issues; synthetic rates on Dev; price matrix + AA-682 to decide | 0 | +6–9 issues | Yes (price matrix, settlement → Ms. Thư) |
| 2 | C2 hosting origin | Option b (prefix list + origin header) or a | 0 / +16–25 | +1 | Yes (N3 origin) |
| 3 | H1 in-VPC bypass | App-verified service JWT; ALB SG ← NLB SG | +$1 | +2 | No |
| 4 | H2 acc3 | Trust + `us.` profiles + ApplyGuardrail + app inference profiles | 0 | +1 | Yes if Haiku 5.5 is unavailable |
| 5 | H3 builder backend | `tp.routes.v1` or a CIS graph API; extend the route-stitching investigation | 0 | +2–4 | Yes (i/ii) |
| 6 | H6 cutover order | S0–S6 order; extra couplings; trip-page 301 | 0 | +2–3 | No |
| 7 | H5 roles | Per-app grants in AA-813; ≤ 60 s + invalidation; new groups | 0 | +1–2 | Re-scope AA-813 |
| 8 | H4 catalog HTTP | `catalog.http.v1`, `tenant.membership.v1` | 0 | +2 | No |
| 9 | H7 observability + plan | 3 small contracts | 0 | +3 | H2 to Ms. Thư |
| 10 | M1–M7 | as written | ≈ 0 | +3–4 | Domain, vendors → Ms. Thư |

Total ≈ +23–31 issues over v2's 117, partly offset by about −4 prod-cell issues deferred under H1 = b. Net ≈ +14–20 before real agencies.

---

## 9. Sources

**Code and docs** (`origin/main` unless stated):
- `apps/AA-Booking/backend/app/pricing/{service.py,engine.py}`, `CONTEXT.md:505-525`
- `docs/architecture/db-schema-reference.md` (verified 2026-10-20 01:02 UTC)
- `docs/adr/0005-pricing-and-supplier-rates.md:30-90`, `docs/adr/0006-ecosystem-identity.md:139-145,400`
- `docs/contracts/README.md` + `*.json`
- `infra/AA-CIS-Infra/accounts/aa365/{booking.tf,identity.tf,identity_variables.tf,e2e_mailbox.tf,tripplanner.tf}`, `accounts/acc3-bedrock/main.tf`, `modules/{vpc,alb}/*.tf`, `db/owners.yaml`, `.github/workflows/db-migrate.yml`
- `apps/AA-CIS-App/{api/routers/v1_trip_page.py, frontend/app/trip/[tourId]/page.tsx, .github/workflows/*, tests/e2e/*, frontend/lib/{apps,rbac}.ts}`
- `apps/AA-TripPlanner-Web/frontend/{components/MapView.tsx,components/RoutePlanner.tsx,lib/api.ts,lib/mapbox.ts,package.json}`, `backend/{browse,assembly}`

**Web** (accessed 20/10/2026):
- [CloudFront pricing](https://aws.amazon.com/cloudfront/pricing/)
- [CloudFront VPC origins](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html)
- [VPC origins announcement](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-cloudfront-vpc-origins)
- [Documenso pricing](https://documenso.com/pricing)
- [Documenso Community Edition](https://docs.documenso.com/docs/policies/community-edition)
- [Documenso Enterprise Edition](https://docs.documenso.com/docs/policies/enterprise-edition)
- [OpenSign repo](https://github.com/OpenSignLabs/OpenSign)
- [Verdocs on OpenSign pricing](https://verdocs.com/blog/opensign-pricing) (competitor source)
- [Gmail API scopes](https://developers.google.com/workspace/gmail/api/auth/scopes)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Microsoft publisher verification](https://learn.microsoft.com/en-us/entra/identity-platform/publisher-verification-overview)
- [SES quotas](https://docs.aws.amazon.com/ses/latest/dg/quotas.html)
- [Stripe Connect pricing](https://stripe.com/connect/pricing)
- [Stripe global availability](https://stripe.com/global)
- [Meta Tech Provider guide](https://developers.facebook.com/docs/whatsapp/solution-providers/get-started-for-tech-providers)

**Unverified / estimates:**
- Haiku 5.5 / Sonnet 5.5 availability on Bedrock `us.` in us-west-1;
- whether Documenso CE allows embedded signing;
- OpenSign self-host API gating;
- the internal ALB price;
- the CA document-signing certificate price;
- Spot discounts.

---

## Questions for Ms. Thư (non-technical items hit in this review; engineering does not decide these)

1. **E-sign provider** (module 12): choose among Documenso Cloud Teams ($480/year), Documenso Platform ($3,000/year), self-hosted Documenso inside AA's AWS (≈ $5–17/month + a signing certificate), or an AA-built simple e-signature ($0). Before choosing: **will AA's trekking insurer accept** each option? Is a third-party provider holding travellers' names and signed waivers acceptable? Can this wait until just before real agencies? (Dev uses the self-hosted test version at no cost.)
2. **How agencies pay AA for AA trips** (ADR 0005 §9 "AA invoices the tenant"): credit terms or prepayment, deposit %, invoice currency, and whether the built-in 3% card fee in the B2B price rule applies to bank transfers.
3. **Who loads supplier net rates and tour cost sheets** into Booking (ADR 0005 §8 "contracting" role: Ms. Thư or a named person), and **when**, since live prices in proposals depend on it. The "price matrix" design in Booking is also waiting for a decision.
4. **Rate parity:** must the CRM stop an agency from quoting a traveller below AA's public "from" price (ADR 0005 §9), or is that only a contract clause?
5. **Supplier manifests** (module 8): what traveller data may AA ops send to hotels and transport suppliers, and is a logged export acceptable even though copies then sit outside the CRM's automatic 90-day deletion?
6. **Traveller-facing web address and email sender:** AA-branded domain, a neutral product domain, or each agency's own domain (agencies would set DNS)? Today the design uses the Dev domain `lumiguides.it.com`.
7. **External app approvals** (accounts, legal entity, brand): Meta business verification + App Review for WhatsApp, Messenger and Instagram; Google OAuth verification for "send as Gmail" (needs a homepage + privacy policy on a verified AA domain); Microsoft publisher verification (needs AA to have a Microsoft 365/Entra organisation account and to join the free Microsoft Cloud Partner Program). Which AA entity and domain should register these, and when should they start?
8. **Payments for Vietnamese agencies:** Stripe does not operate in Vietnam. Which VN payment gateway should be asked for a quote (D10 a), and is manual recording acceptable until then?
9. **Subscription plans** (H2 note from Nghiệp: the CRM plan follows the tenant portal plan): which CRM features or limits belong to which portal plan, and does the "free for partners" spec principle still hold for the CRM part?
10. **WhatsApp/SMS deviation:** the spec names Twilio/360dialog; the design uses Meta's Cloud API directly (agency-owned account), with SMS via the agency's own Twilio. Confirm this is acceptable.
