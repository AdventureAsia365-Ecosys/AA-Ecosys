# Area 4 — API design and management (OWASP API Security Top 10 2023)

Scope: CIS, AA-Booking, TripPlanner, Next.js BFF proxies, API Gateway/WAF. Read-only, 17/10/2026. Sources: local checkouts (CIS 353c328d, Booking dc51c8b, TripPlanner 088d28d, Infra a6605ce), AWS describe/list on acc2, unauthenticated GETs to public health/docs URLs.

Synthesis note (`../README.md` §8.3): this area proposed "ADR 0009" for HTTP conventions; 0009 is reserved for AI platform (AA-804), so new ADRs start at 0010.

## Inventory (observed)

- **CIS FastAPI**: 258 decorated routes (grep over api/routers/*.py + api/main.py).
  - /admin ≈180 routes in 22 routers (admin_pipeline 55, admin 25, admin_content_quality 19, admin_llm_ops 18, admin_job_runner 11).
  - /v1 (tenant) 63 routes in 14 routers (v1_tours 11, v1_integrations 8, v1_content_writing 8). Public no-auth: GET /v1/trip/{tour_id}, /content/photos/{id}.
  - main.py: live /auth routes (tenant-login, verify-tenant, admin-login, verify-admin, booking-token, /.well-known/jwks.json), /health, gated /docs, /redoc, /openapi.json. routers/auth.py's own router is not mounted (auth.py:258-262).
- **AA-Booking**: 86 routes in 11 routers under /booking; live OpenAPI 65 paths / 87 operations. Unauthenticated: /booking/health, /health/ready. /booking/ops/deploy-gate uses GithubDeployOIDC.
- **TripPlanner**: HTTP API 9vqkfbukvh with 4 routes, all AuthorizationType NONE (ANY /browse/{proxy+}, ANY /trip/{proxy+}, POST /trip/{trip_id}/narrate, GET /browse/search). Assembly Lambda 12 internal routes (handler.py:59-72); browse Lambda tiles/destinations/search/routes/tour-route.
- **BFF**: CIS /api/admin/[...path], /api/tenant/[...path], /api/pipeline/[...path], /api/playground/proxy, /api/tour-full/[id], auth routes; TP /api/trip, /api/browse.

## Auth schemes (observed)

- CIS staff: username + bcrypt → HS256 JWT 24h, no iss/aud, shares JWT_SECRET with tenant tokens (auth.py:38-39, 300-308). BFF adds static X-Admin-Secret and forwards x-admin-role / x-admin-user-id as plain headers; backend checks secret with `!=` (admin.py:113).
- CIS tenant: API key exchanged at /auth/tenant-login for 24h JWT; /v1 accepts only that Bearer (v1_tours.py:26 get_tenant). `verify_tenant_api_key` dependency exists but no route uses it.
- Booking: RS256 staff JWT minted by CIS /auth/booking-token (15 min, aud=booking, re-checks admin_users.is_active); verified via JWKS with pinned iss/aud and kid-rotation throttle (tokens.py); in-code permission matrix (auth/staff.py:178 require()).
- TripPlanner: edge shared secret X-TripPlanner-Key (shared/auth.py, compare_digest) + hashed HttpOnly guest token on 8 mutation routes (AA-827); GET reads not gated.
- ADR 0006 (Cognito, two pools) accepted, not built.

## Edge (live AWS)

- WAF aa-cis-dev-waf attached only to ALB; list-resources-for-web-acl API_GATEWAY → []; both REST stages webAclArn null. ALB SG allows only 10.2.0.0/16:80 → all public traffic enters via API GW where no WAF applies.
- CIS stage dev: throttling -1/-1, no access logs, tracing off. Booking: 20 rps / burst 40, no access logs. TP $default: 500 rps / 1000 burst; narrate 2/5; search 10/20; no access logs.
- 4 CIS usage plans (starter, growth, business, internal) but get-api-keys → [] and every method authorization NONE → plans do nothing.
- All three APIs keep execute-api endpoint enabled.

## Docs and contracts

- CIS docs gated on ECS (curl /openapi.json → 403); admins read /admin/api-docs.
- Booking docs public: /booking/openapi.json and /booking/docs → 200 (110 KB).
- docs/contracts: JSON Schemas for DB-view and outbox contracts (inquiry.submitted v1/1.1/1.2, catalog.tour v1/1.1, catalog.graph v1) with versioning rules; Booking/TP copies match (sha1); Booking pins hashes (test_inquiry_contract.py:26).
- No HTTP API contract or OpenAPI diff in any CI. data-standards/01-engineering.md has no HTTP API conventions section.
- INFERENCE: the real CIS staff authorization boundary is the Vercel BFF, not the API; the B2B "API" is in practice the portal's back end.

## Strengths

- Booking staff auth near best practice (RS256, aud=booking, 15 min, is_active re-check at mint, api/main.py:373-417; JWKS pinned iss/aud, kid refetch throttle, size-capped fetch, tokens.py:28-36; deny-by-default matrix staff.py:178).
- Mature cross-app event/read-model contracts (owner, minor/major versioning, idempotency_key + inbox UNIQUE, pull-consumer rules); byte-identical copies (sha1 c89927fb, 55af4ade, e2584ffc), pinned sha256 in Booking tests.
- CIS hides Swagger/ReDoc/OpenAPI live (api/main.py:136-204, AA-577); role-checked /admin/api-docs.
- BFF blocks path traversal (lib/bffPath.ts); tenant token can't act as staff (verify_tenant_jwt, auth.py:84-92; get_tenant 403 for staff token).
- Tenant isolation moving to Postgres RLS (aa_app_user, ~14 /v1 routes, aa544_tenant_pool.py; SEC-6..10, TST-4).
- Per-tenant Redis RPM limiter with 30 s revoke, Retry-After, X-RateLimit-* (rate_limit.py:62-148).
- WAF logs redact Authorization and X-Admin-Secret (AA-806); managed common rules blocking (3 noisy sub-rules in COUNT).
- TP guest identity well designed (32-byte token, __Host- HttpOnly cookie, sha256 stored, compare_digest, same-origin POST checks, narrate 2 rps, search 10 rps).
- Booking machine-readable error codes (errors.py ServiceError) and keyset cursor pagination (paging.py) — template for others.
- Booking deploy-gate authenticated by GitHub OIDC, not a static secret.

## Gaps

### A1 — Broken function-level authorization: staff RBAC only in BFF, default-allow; backend trusts forwarded role headers — HIGH, M, automatable
- Evidence: (1) frontend/lib/rbac.ts:66-72 API_RULES.admin = ALL_STAFF; API_WRITE_RULES (79-91) restricts only content-quality/* and tenants*; canWriteAdminPath returns true when no rule matches (117-121). (2) Backend writes with secret-only checks: PATCH /admin/llm-config/{stage} (admin_llm_ops.py:206-213, "admin-only, confirm-gated on the FE"), PUT /admin/budgets/{provider}/{scope} incl. hard_stop (admin_budgets.py:57-60), POST /admin/job-runner/jobs/{id}/cancel|retry and /retention/run (admin_job_runner.py:169-215), PATCH /admin/settings/seo; only admin.py, admin_api_docs.py, admin_content_quality.py read x-admin-role. (3) Staff branch of app/api/tenant/[...path]/route.ts:54-63, :85 sends X-Admin-Secret to ANY backend path without write rules or x-admin-role. (4) Backend accepts x-admin-role/x-admin-user-id from any ADMIN_SECRET holder (admin.py:119-124). PAGE_RULES make /admin/llm-usage and /admin/jobs admin-only but their APIs are not.
- Risk: reviewer/content account or stolen staff session switches LLM models, raises/removes budgets, cancels jobs, runs retention; ADMIN_SECRET holder (Vercel env, ADR 0006 line 390) = full admin + tenant impersonation + forged audit identity.
- Recommendation: (a) `require_staff(roles=...)` at APIRouter level on every /admin router; (b) backend verifies staff JWT (Bearer) and derives role/user from claims, stop trusting headers; X-Admin-Secret only as temporary S2S layer until ADR 0006 Phase 1; (c) CI test walking app.routes failing on non-GET /admin route without role policy; (d) meanwhile default-deny API_WRITE_RULES for non-admins; tenant-proxy staff branch through rbac + x-admin-role.
- Standards: OWASP API5:2023 BFLA; API1; NIST SSDF PW.1.1; NIST SP 800-53 AC-6.

### A2 — Weak staff and tenant authentication — HIGH, M, automatable
- Evidence: auth.py:38-39 (HS256, 24h), :62-71, :300-308 same JWT_SECRET, no iss/aud; verify-admin docstring (main.py:341-345) "a deactivated admin stays valid until token expiry (24h)"; POST /auth/admin-login (main.py:307-337) no rate limit/lockout (grep lockout|login_attempt|brute → nothing; limiter only on /v1 Bearer, rate_limit.py:73-78); `!=` at admin.py:113, auth.py:218 (only v1_pipeline.py:51 compare_digest); RotationEnabled None for admin-secret and jwt-secret; ADR 0006 "Shared passwords, no email, no MFA"; /auth/verify-tenant (main.py:296-305) accepts any JWT and reads payload['name'] → staff token raises 500.
- Risk: online password guessing (no MFA, no edge limit); leaked token usable 24h; leaked JWT_SECRET forges both identities; timing side channel; SOC 2 CC6.1/CC6.6 questionnaire blocker.
- Recommendation: interim (S): Redis per-username + per-IP lockout on /auth/admin-login and /auth/tenant-login (e.g. 5 failures/15 min) + WAF rate rule on /auth/*; compare_digest everywhere; iss/aud ('cis-staff'/'cis-tenant') and separate keys; staff TTL 8h + per-request is_active (cached ~60 s); fix verify-tenant to use verify_tenant_jwt. Target (L): ADR 0006 Phase 1 Cognito WORKFORCE (email OTP + TOTP break-glass), then rotate ADMIN_SECRET with schedule.
- Standards: OWASP API2:2023; NIST SP 800-63B §5.2.2, §4.2; RFC 8725.

### A3 — No effective edge rate limiting or WAF on public API traffic; usage plans dead config — HIGH, S, automatable
- Evidence: WAF API_GATEWAY resources []; webAclArn null on 4ylo382khg and 9z3xnalp59; ALB-only WAF where every public request comes through the VPC link and matches VpcLinkInternalAllow (priority 2) before RateLimit1000 and GeoBlock; waf_protect_rest_api_stages default false (variables.tf:188-191), not set in tfvars; CIS methodSettings */* -1/-1; 4 usage plans, 0 API keys, all methods NONE (modules/api_gateway/main.tf); app limiter skips /v1 without valid Bearer (rate_limit.py:76-84); public GET /v1/trip/{tour_id} runs UPDATE on BYPASSRLS pool every request (v1_trip_page.py:93-115) and a non-UUID id fails the `$1::uuid` cast; TP HTTP API can't carry WAF, $default 500/1000 anonymous, GET reads ungated.
- Risk: anonymous floods reach ECS + shared RDS; write amplification; credential stuffing on /auth; LLM/Bedrock cost spike via TP (narrate capped only globally); false sense of protection.
- Recommendation: (1) apigateway:SetWebACL + waf_protect_rest_api_stages=true (Booking geo allow-list first or per-stage ACL without geo); (2) CIS stage throttling (e.g. 50/100) + tighter /auth/*; (3) wire usage plans to real keys or delete; (4) move liveness stamp off public GET (job) + validate UUID first; (5) TP: CloudFront + WAF per-IP rate rules in front of HTTP API or per-route throttles on all mutating routes + per-guest-token LLM budget on narrate.
- Standards: OWASP API4/API6/API8:2023; AWS WA SEC 6/REL 5.

### A4 — No consumable B2B API product — HIGH, L, partially automatable
- Evidence: ADR 0006 lines 94-95, 392 "API keys remain for machine access (X-API-Key on the public API)"; verify_tenant_api_key (auth.py:201-253) unused; API GW TOKEN authorizer removed (modules/api_gateway/main.tf:17, AA-750) but api/lambda_authorizer/ remains; only machine path = /auth/tenant-login → 24h JWT; deprecated=True only on unmounted router (auth.py:97), live copy main.py:259 not flagged; shared.tenants single api_key_hash (db-schema-reference.md:3063), generate-key overwrites (admin.py ~1297-1301) — no overlap, scopes, expiry, last_used; Playground (portal/_components/api-playground/endpoints-config.ts:67-85) advertises POST /v1/webhooks which doesn't exist; no developer portal/SLA/SLO (03-scaling C1 "not paging promises").
- Risk: B2B customer can't integrate safely (rotation downtime, untraceable leaked key, 404 docs); blocks selling an API tier; plan_tier/rate_limit_rpm unenforceable.
- Recommendation: ADR "CIS Public API v1": (a) shared.tenant_api_keys (id, tenant_id, prefix, sha256 hash, scopes[], created_by, expires_at, last_used_at, revoked_at), ≥2 active keys; (b) X-API-Key directly on curated /v1 subset, per-key rate limit (Redis or API GW keys + usage plans); (c) drop admin-secret impersonation branch from tenant dependency; (d) public OpenAPI from /v1 public tag, static Redoc from CI; (e) generate Playground config from schema, remove or build /v1/webhooks; (f) per-plan SLOs + support/deprecation policy.
- Standards: OWASP API9/API2:2023; NIST SSDF PW.1; ISO 27001 A.5.17.

### A5 — OpenAPI incomplete; no breaking-change detection — HIGH, M, automatable
- Evidence: response_model= on 11/258 CIS routes; Booking live OpenAPI 1/87 operations with typed 200; no oasdiff/schemathesis/spectral/pact in any workflow (CIS ci/deploy-dev/eval-regression/ui-smoke; Booking ci/deploy-dev; TP ci/deploy-lambdas); docs/contracts only DB views + outbox; HTTP contracts (booking-token + JWKS → Booking; TP BFF → Lambda op mapping app/api/trip/route.ts:97-138; CIS BFF → /admin, /v1) lack schema/consumer tests; tenant responses shaped by hand (routers/_tenant_projection.py, AA-770/796).
- Risk: silent field removal breaks portal/Booking/B2B; internal fields (scores, QA flags) leak to tenants (BOPLA); agents lack exact contract → higher regression rate.
- Recommendation: (1) response_model (Pydantic, extra='forbid' on outputs) on every tenant /v1 route, then Booking; (2) CI dumps app.openapi() → committed openapi.json → `oasdiff breaking` vs main, fail unless label `breaking-approved`; (3) schemathesis with seeded DB; (4) HTTP contracts registered in docs/contracts with TST-6 producer/consumer rule.
- Standards: OWASP API3/API9:2023; NIST SSDF PW.4/PW.8; TST-6.

### A6 — Booking OpenAPI and Swagger public on live domain — MEDIUM, XS, automatable
- Evidence: curl https://api-booking.lumiguides.it.com/booking/openapi.json → 200, 110,749 bytes (65 paths, 87 ops, HTTPBearer + GithubDeployOIDC); /booking/docs 200; backend/app/main.py:95-101 no auth; /booking/health returns git_sha (health.py:21); CIS gates same (api/main.py:136-204, live 403).
- Risk: free full map of staff, customer-data, supplier/pricing endpoints incl. deploy-gate (CIS fixed this after real scanner traffic, AA-577).
- Recommendation: docs_url/redoc_url/openapi_url=None when deployed (AWS_EXECUTION_ENV) + staff-authenticated /booking/admin/openapi.json via BFF; git_sha only on internal/auth health or accept explicitly; unit test like test_aa577_swagger_docs_gate.py.
- Standards: OWASP API8/API9:2023.

### A7 — Tenant object-level isolation (BOLA) still mostly hand-written WHERE tenant_id over BYPASSRLS pool with Redis kill-switches — MEDIUM, M, automatable
- Evidence: acquire_scoped_conn on ~14/63 /v1 routes (aa544_tenant_pool.py:8-26); others e.g. GET /v1/tours/versions/{id}/export-docx (v1_tours.py:883-900) use app.state.pool (aa_cis_admin, BYPASSRLS) + manual filter; every RLS route gated by Redis flag, `redis-cli DEL <flag>` reverts to admin pool; no test enumerates /v1 routes for cross-tenant denial (TST-4 covers tables).
- Risk: one missing predicate (easy in AI-generated code) exposes another tenant's content/credentials; flags = standing bypass.
- Recommendation: finish AA-859 waves; after soak delete flags; CI "route policy" test (every /v1 route uses acquire_scoped_conn or is on reviewed allowlist); two-tenant integration test per route (A's token → 404 for B's ids).
- Standards: OWASP API1:2023; SEC-10/TST-4; NIST SP 800-53 AC-3/AC-4.

### A8 — SSRF protection on tenant integration URLs blocks only IP literals and follows redirects — MEDIUM, S, automatable
- Evidence: api/routers/v1_integrations.py:61-86 `_validate_wp_url` "Deliberately does NOT perform DNS resolution"; test call `session.get(f"{wp_url}/wp-json/wp/v2/users/me", auth=auth)` (L340) with aiohttp default allow_redirects=True; publish path services/acp_s4_blog/cms/wordpress.py posts to same URL.
- Risk: hostname resolving/redirecting to 10.2.x or 169.254.170.2 → blind SSRF with tenant-controlled Basic Auth; grows with more integrations.
- Recommendation: shared safe_http client (resolve + reject private/loopback/link-local/reserved after resolution, pin IP, allow_redirects=False or re-validate each hop, size/timeout caps, log destination); optionally restrict ECS egress SG to 443.
- Standards: OWASP API7:2023; OWASP SSRF Prevention Cheat Sheet.

### A9 — No shared HTTP API conventions — MEDIUM, M, automatable
- Evidence: CIS {'detail': free text} (main.py:330, rate_limit.py:99); Booking {'detail': code, 'message'} (errors.py:20-21) next to default HTTPException/422; TP {'error'} and {'detail'} (browse/handler.py:153, assembly handler.py:189-193); BFFs mix {'detail'}/{'error'}; CIS pagination limit/offset (14/10 params) + page/page_size (5/4), Booking keyset; only tenant API has /v1; Deprecation/Sunset headers 0; X-Request-ID 0; 01-engineering.md no HTTP section.
- Risk: every client special-cases errors/pages; no announced path for breaking changes; incidents untraceable across BFF → API → job.
- Recommendation: "Part D — HTTP API conventions" in data-standards or a new ADR (≥0010): problem+json with stable `code` + `request_id`; keyset envelope {items, next_cursor}; /v1 only for external surfaces with 6-month deprecation, Deprecation/Sunset, CHANGELOG; X-Request-ID minted at BFF/edge and logged everywhere; kebab-case paths, snake_case JSON; one shared middleware per stack + CI lint of new routes.
- Standards: RFC 9457; RFC 8594; Microsoft/Google/Zalando API guidelines; NIST SSDF PO.1; OWASP API9.

### A10 — API Gateway access logging off on every stage; tracing disabled — MEDIUM, S, automatable
- Evidence: accessLogSettings null for CIS dev and Booking dev; CIS tracingEnabled false; TP AccessLogSettings null; only WAF logs (ALB path).
- Risk: abuse, credential stuffing, tenant disputes, incidents uninvestigable; no per-tenant SLA reporting.
- Recommendation: JSON access logs on all 3 stages (30–90 days): $context.requestId, identity.sourceIp, routeKey/resourcePath, status, responseLatency, integrationLatency, API key id (later), never headers; pass requestId as X-Request-ID; metric filters + alarms on 4xx/5xx/429.
- Standards: OWASP API9; NIST SP 800-92; SOC 2 CC7.2; AWS WA SEC 4.

### A11 — No client-facing idempotency keys — MEDIUM, M, automatable
- Evidence: Idempotency-Key only internal (shared/jobs, booking/jobs/queue.py:53-69, intake ON CONFLICT); no route reads the header; costly POSTs e.g. /v1/tours/pool/{published_tour_id}/rewrite (v1_tours.py:426, LLM spend), Booking trip-case/supplier writes; ADR 0005 plans payments.
- Risk: retries/double clicks duplicate rewrites (cost), trip cases, later double charges; integrators can't retry safely.
- Recommendation: FastAPI Idempotency-Key dependency storing (caller, key, request hash, response) 24h in Postgres/Redis; replay returns stored response, mismatched body 422; mandatory on payment, booking creation, LLM-costing tenant POSTs; documented.
- Standards: IETF draft-ietf-httpapi-idempotency-key-header; OWASP API6; PCI DSS 4.0 req. 6.

### A12 — CIS CORS allows localhost origins with credentials and wildcards in deployed env — LOW, XS, automatable
- Evidence: api/main.py:144-155 allow_origins incl. http://localhost:3000/3001 + prod hosts, allow_credentials=True, methods/headers '*', no env switch; all browser traffic actually via same-origin BFF.
- Risk: low today (header credentials, host-only cookies); real once any endpoint accepts cookies or a local tool runs on those ports.
- Recommendation: deployed → allow_origins [] (or exact Vercel origin) with explicit methods/headers; localhost only when AWS_EXECUTION_ENV unset (reuse _is_publicly_deployed()).
- Standards: OWASP API8:2023.

### A13 — Default execute-api endpoints remain enabled — LOW, XS, automatable
- Evidence: disableExecuteApiEndpoint False for aa-cis-dev-api, aa-booking-dev-api; DisableExecuteApiEndpoint false for aa-tripplanner-dev-api; ecosystem-architecture.md:200 "the execute-api URL still answers"; custom domains api-cis, api-cis-aa365, api-booking, api-tripplanner (TLS_1_2, no mTLS).
- Risk: future custom-domain/CloudFront controls (WAF, mTLS, logging) bypassable; unused legacy domain api-cis-aa365 in attack surface.
- Recommendation: after confirming all clients use custom domains (Vercel API_URL, TRIP_API_URL, workflows, smoke), disable_execute_api_endpoint=true for all three; retire api-cis-aa365 if unused; inventory table (domain, API, owner, auth, consumers) in ecosystem-architecture.md.
- Standards: OWASP API9/API8:2023.

### A14 — Body/input size limits rely on API GW defaults; inputs only partly schema-validated — LOW, S, automatable
- Evidence: 7 handlers parse raw `await request.json()` (main.py:298, 347; admin.py ×1; admin_pipeline.py ×4); /auth/verify-tenant indexes keys directly; extra='forbid' 0 in CIS vs 34 in Booking; only explicit cap _BRIEF_PARSE_MAX_BYTES = 5 MB (admin_pipeline.py:4864) relying on 10 MB API GW cap; WAF SizeRestrictions_BODY in COUNT (modules/waf/main.tf:79-85); BFF proxies buffer any body.
- Risk: malformed/oversized payloads → 500 instead of 4xx; unknown fields silently accepted (mass assignment risk); ECS memory pressure on large uploads.
- Recommendation: Pydantic request models (extra='forbid', length/size constraints); ASGI body-size middleware per route class (e.g. 1 MB JSON, 10 MB uploads) + Content-Length check in BFF; then reconsider enforcing SizeRestrictions_BODY with scope-down for uploads.
- Standards: OWASP API3/API4:2023; ASVS 5.1.
