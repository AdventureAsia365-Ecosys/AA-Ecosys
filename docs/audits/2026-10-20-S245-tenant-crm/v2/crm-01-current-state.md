# CRM redesign scout 01: current state (tenant portal, admin/portal coupling, shared infra, Booking template, cost lines)

Date: 20/10/2026 (S245 r2). Read-only scout for the CRM-as-its-own-app redesign. Nothing in any repo, AWS,
Vercel, Linear or Jira was changed.

**Snapshot used (cite base for every `file:line` below):**

| Repo | Ref read | Note |
|---|---|---|
| `apps/AA-CIS-App` | `origin/main` @ `b7e6da66` (read with `git show` / `git grep`) | The local checkout `f9fc32d6` is 9 commits behind. Those commits touch `portal/` (AA-886 legal pages, `lib/hosts.ts`, `next.config.ts`), so all CIS line numbers here are origin/main ones |
| `apps/AA-Booking` | `origin/main` @ `e478663` for `CONTEXT.md` (+14 front-matter lines), working tree `f4fb80d` otherwise | Only `CONTEXT.md` and one notes file differ |
| `infra/AA-CIS-Infra` | `main` @ `4824c81` (= origin/main) | |
| Root `AA-Ecosys` | `master` @ `f8a9938` | |

**Live reads (free, read-only AWS calls, 20/10/2026, profile `aa365-admin`, account 005097885195):**
`ecs describe-services`: `aa-cis-dev-api`, `aa-cis-dev-worker` and `aa-booking-dev-api` each have desired 1 and running 1, with FARGATE base 1 and FARGATE_SPOT weight 3. Those are the only three services on `aa-cis-dev-cluster`.
`ecs describe-task-definition`:

| Task definition | CPU | Memory | Architecture |
|---|---|---|---|
| `aa-booking-dev-api:33` | 256 | 512 | x86 (default) |
| `aa-cis-dev-api:717` | 512 | 1024 | x86 (default) |
| `aa-cis-dev-worker:274` | 512 | 1024 | x86 (default) |

`rds describe-db-instances`: `db.t4g.small`, single-AZ, 20 GB, available. No Cost Explorer call was made ($0.01 per request, a paid API).

---

## 1. The tenant portal today

| Aspect | Fact | Source |
|---|---|---|
| Where | `apps/AA-CIS-App/portal/`, a second Next.js app inside the CIS repo, split out of `frontend/` by AA-885 | `portal/next.config.ts:1-3`; CIS `CONTEXT.md:79-83` |
| Framework | Next 16.4.2, React 19.2.4, react-query 5, TanStack Table 8, lucide. Tailwind 4 is a dev dependency, but pages use inline styles. Dev port 3004 | `portal/package.json` (`"next": "16.4.2"`, `"dev": "next dev -p 3004"`) |
| Host / Vercel | Vercel project `aa-cis-portal` with Root Directory `portal`, at `https://portal.lumiguides.it.com`. The Git integration is off (`git.deploymentEnabled: false`), so deploys come only from CI | `portal/vercel.json:3-5`; `.github/workflows/vercel-deploy-portal.yml:3-9,57-58` |
| Build/deploy | GitHub workflow `vercel-deploy-portal.yml`: PRs get a preview plus UI smoke (`ui-smoke-portal.yml`), and a push to `main` goes to production. The project id comes from the repo variable `VERCEL_PORTAL_PROJECT_ID`. The `VERCEL_TOKEN` secret is shared with the admin workflow, under the same Vercel team `team_zHOm…`. The path filter is `portal/**` only. A portal change never redeploys ECS | `vercel-deploy-portal.yml:15-21,24-36,56-60`; guard `tests/unit/test_aa885_portal_split.py:163-174` |
| Vercel plan | Hobby team. The workflow notes "the Hobby team cap is ~100 deployments / 24 h for the whole team". Handbook D-18 says "Vercel Hobby until the first paying tenant, then Pro" | `vercel-deploy-portal.yml:7-9`; `docs/engineering-handbook.md:499,947` |
| Routes (pages) | `/` → 307 to `/portal/dashboard`. `/tenant-login`, `/privacy` and `/terms` are public. Behind the gate: `/portal/{dashboard, t0-brand, t1-rewrite, t4-pool, t7-planning, t8-angle-gate, t10-review, t11-publish, t11-publish/connection, help/facebook, marketplace, api, activity, billing, settings}` | `portal/next.config.ts:31-37`; file list `git ls-tree origin/main portal/app`; sidebar `portal/app/portal/_components/Sidebar.tsx:28-50` |
| BFF routes | `app/api/auth/tenant-login`, `app/api/auth/tenant-logout`, `app/api/tenant/me`, `app/api/tenant/[...path]` (a generic proxy to any backend path, with a verified tenant Bearer), and `app/api/playground/proxy` (an allow-list of 3 paths) | `portal/app/api/tenant/[...path]/route.ts:20-61`; `portal/app/api/playground/proxy/route.ts:10-20` |
| Auth (human) | **One shared API key per tenant, not Cognito.** `/tenant-login` posts the key to the BFF, which calls `POST {API_URL}/auth/tenant-login`. The backend hashes the key with SHA-256, looks it up in `shared.tenants.api_key_hash`, and mints an HS256 JWT (`role: tenant`, 24 h). The BFF sets 5 httpOnly host-only cookies (`cis_role=tenant`, `cis_tenant_token`, `cis_tenant_id`, `cis_tenant_name`, `cis_tenant_plan`) | `portal/app/tenant-login/page.tsx:14-38,59-73`; `portal/app/api/auth/tenant-login/route.ts:29-71`; `api/main.py:289-324`; `api/routers/auth.py:59-73` |
| Page gate | `portal/proxy.ts` (Next 16 Proxy) matches `/portal/:path*` and `/tenant-login`. The token is verified by `POST /auth/verify-tenant` (3 s timeout, 20 s cache). It fails closed outside development | `portal/proxy.ts:27-55`; `portal/lib/auth-server.ts:13,91-109` |
| Cognito EXTERNAL | Pool `aa-external-dev` and confidential client `cis-portal` already exist, with callback `https://portal.lumiguides.it.com/api/auth/callback/cognito` and port 3004. They are **not used yet**: "Still placeholders: tenants sign in with an API key". Membership table (`shared.tenant_members`, AA-813) does not exist | `infra/.../accounts/aa365/identity.tf:14-18,168-184,606-616`; `identity_variables.tf:163-168`; ADR 0006 `docs/adr/0006-ecosystem-identity.md:137-150` |
| Backend called | Only the CIS API (`API_URL`, default `https://api-cis.lumiguides.it.com`, no Vercel env var needed). Backend paths reached through `/api/tenant/*`: `/v1/tours/{pool, my-versions, versions/{id}[/retry, /export-docx], pool/{id}/rewrite}`, `/v1/slate[/refresh]`, `/v1/subjects/{id}/{pick,cut}`, `/v1/angle-gate/*`, `/v1/content-writing/*` (requests, pieces, reviews, cta-check), `/v1/publish-log/*`, `/v1/integrations/{wordpress,facebook}[/test]`, `/v1/planning/trip-reallocation/*`, `/v1/marketplace`, `/v1/billing`, `/v1/quota`, `/v1/progress/{kind}/{id}`, and **`/admin/brand-identity[/upload,/parse]`** (an admin-prefixed path that also takes a tenant token, see §2.5) | `portal/lib/auth-server.ts:15`; CIS `CONTEXT.md:92-94`; grep of `/api/tenant/…` literals in `portal/` (e.g. `BrandTab.tsx:126,155,211,219`, `catalogApi.ts:35,41`, `reviewListApi.ts:48`) |
| Code shared with `frontend/` | 14 files are **byte-copies** of admin files, enforced by a unit test: `_kit/{tokens,primitives,Modal,Drawer,Toast,api,useMediaQuery,Providers,DataTable,csv,savedViews}`, `_brand/tokens.ts`, `lib/bffPath.ts`, `lib/proxyResponse.ts`. `globals.css`, `lib/auth-server.ts` and `_kit/index.ts` are portal-owned. There is no npm workspace or package: the copy is the sharing mechanism | `tests/unit/test_aa885_portal_split.py:24-40,66-81`; CIS `CONTEXT.md:109-117` |
| Not moved | The public white-label page `/trip/[tourId]`, which is tenant-facing, stays on the **admin** app. No Sentry on the portal | CIS `CONTEXT.md:118-119`; `frontend/app/trip/[tourId]/page.tsx:1-10` |

---

## 2. Everything that couples the CIS staff admin (`frontend/`) and the tenant portal (`portal/`)

The UI split (AA-885) is mostly done, and a guard test protects it (`test_aa885_portal_split.py`). What remains is
listed exhaustively below. "Direction" is who points at whom.

### 2.1 Links, redirects and nav items (UI-visible)

| # | Direction | File:line (origin/main) | What it does |
|---|---|---|---|
| L1 | admin → portal | `frontend/app/login/LoginForm.tsx:10,158-160` | The staff login page shows **"B2B Tenant login →"**, linking to `${PORTAL_BASE_URL}/tenant-login`. This is the visible cross-link the owner objects to |
| L2 | portal → admin | `portal/app/tenant-login/page.tsx:4,109-114` + `portal/lib/hosts.ts:5-9` | The tenant login page shows **"← Staff login"**, linking to `https://aa-cis.lumiguides.it.com/login` (`ADMIN_BASE_URL`, `STAFF_LOGIN_URL`). This is the mirror cross-link |
| L3 | admin → portal | `frontend/next.config.ts:4,20-25` + `frontend/lib/apps.ts:25-28` | 308 redirects on the admin host: `/portal`, `/portal/:path*` and `/tenant-login` go to the portal host. These are legacy-URL forwarding, not shown in the UI. The guard test **requires** them (`test_aa885_portal_split.py:104-117`, which also asserts `PORTAL_BASE_URL` in `apps.ts`) |
| L4 | admin → portal (text) | `frontend/app/admin/atom-curation/page.tsx:1106-1107` | Help text tells staff that tenants act on `/portal/t7-planning`. It is text only, not a link |
| L5 | admin (dead code) | `frontend/components/NavBar.tsx:6-12` | Legacy nav with a `{ href: "/tenant", label: "Tenant Portal" }` item. Not imported anywhere (`git grep NavBar` shows only its own definition). Delete it |
| L6 | admin → tenant-facing page | `frontend/app/trip/[tourId]/page.tsx:1-15,145-148` | A **public tenant-channel page served by the admin app** (no auth). Its CTA is a hard-coded `mailto:admin@adventureasia.com` (D18) |
| L7 | backend → admin host for tenant URLs | `api/routers/v1_trip_page.py:6,27,157` | `real_url = f"https://aa-cis.lumiguides.it.com/trip/{tour_id}"`. Stored `trip_url`s used by tenant publishing point at the admin host (`CONTEXT.md:118-119`) |
| L8 | none (explicit) | `frontend/lib/apps.ts:30-32` | No "Tenant portal" entry in the admin Apps sidebar (by design: "a staff member cannot open it"). The admin Apps block lists only Booking and TripPlanner (`apps.ts:46-61`; `frontend/app/_kit/Sidebar.tsx:34,149`) |

### 2.2 Shared code (copies) and shared styles

| # | File:line | What |
|---|---|---|
| C1 | `tests/unit/test_aa885_portal_split.py:25-40` | 14 vendored byte-copies (list in §1). Any admin kit change must be copied into `portal/` in the same PR or CI goes red. This is a **build-time coupling**: the portal cannot change its kit without changing the admin's, and the reverse |
| C2 | `portal/app/_kit/api.ts:17-25` (vendored) | `adminHeaders()` sends `x-reviewer-id` from `localStorage.cis_reviewer_id`. Admin-only logic shipped inside the portal bundle (dead there) |
| C3 | `portal/app/globals.css:4-15,300-303,337-405,435-474` | The portal-owned CSS still carries the **admin theme and shell styles** (`.aa-admin-sidebar`, `.aa-admin-hamburger`, the "Admin /" crumb). It was copied, not split |
| C4 | `portal/app/_brand/tokens.ts:2-3,50-52` (vendored) | Comments describe admin `adminUi.tsx` and the admin `middleware.ts /brand` route. The tokens are shared on purpose (brand); the comments are admin context |
| C5 | `portal/app/_kit/primitives.tsx:5-7,65,132,330,429` (vendored) | Comments referencing admin pages (e.g. `/admin/platform/staff`). Harmless, but they show the kit is admin-owned |

### 2.3 Shared names, cookies, env vars and hosts

| # | File:line | What |
|---|---|---|
| N1 | `portal/app/api/auth/tenant-login/route.ts:63` vs `frontend/lib/cognito.ts:429-438` | The **same cookie name `cis_role`**: the portal sets `cis_role=tenant` (httpOnly), and the admin sets `cis_role=<staff role>` (not httpOnly). They are host-only on different hosts today, so there is no live clash. The admin code still carries a comment and handling for "the httpOnly `cis_role=tenant` a tenant-portal login leaves on the same host" (`cognito.ts:432`), which is a pre-AA-885 leftover |
| N2 | `portal/lib/auth-server.ts:15`; `frontend/app/api/tenant/[...path]/route.ts:41`; `frontend/app/trip/[tourId]/page.tsx:15`; `frontend/proxy.ts:71` | Both apps use the **same backend** and the same env name `API_URL` (admin also `NEXT_PUBLIC_API_URL` — ⚠️ underscore env var, edit by hand), default `https://api-cis.lumiguides.it.com` |
| N3 | `.github/workflows/vercel-deploy-portal.yml:16,57` | The same Vercel team (`VERCEL_ORG_ID`) and the same `VERCEL_TOKEN` secret as the admin workflow. They also share the Hobby team-wide **100 deployments/day** cap |
| N4 | `api/main.py:162-173` | Backend CORS allow-list has the admin host but **not** the portal host. That works only because the portal browser never calls the API directly (BFF). A separate CRM UI calling an API from the browser would need its own origin entry, or its own BFF |
| N5 | Repo/CI | One repo (`AA-CIS-App`) and one `ci.yml` (5 checks) cover API, worker, admin and portal. Branch protection of the CIS repo applies to portal PRs (CIS `CONTEXT.md:472-475`) |

### 2.4 Admin-side "tenant" proxies (naming coupling, staff-only since AA-885)

| # | File:line | What |
|---|---|---|
| P1 | `frontend/app/api/tenant/[...path]/route.ts:1-19,48-54` | The admin app still has a route called `/api/tenant/[...path]`. It is **staff-only** (`requireAdmin(req, API_RULES.tenantProxy)`) and forwards `X-Admin-Secret` to **any** backend path. The guard test checks it is staff-only (`test_aa885_portal_split.py:132-136`) |
| P2 | `frontend/app/admin/master-content/page.tsx:857` | A staff page calls `/api/tenant/admin/tenants/${AA_INTERNAL_ID}/details` through that staff proxy |
| P3 | `frontend/app/api/tenant/pipeline/brand-identity/route.ts` (exists, listed by `git ls-tree`) + `frontend/lib/rbac.ts:93-94` | Staff route named "tenant/…" for the AA-internal brand rules |

### 2.5 Backend coupling (one FastAPI app serves both audiences)

| # | File:line | What |
|---|---|---|
| B1 | `api/main.py:24-62,227-269` | One process registers tenant routers (`v1_*`) and staff routers (`admin_*`) together, with one pool (`DATABASE_URL` = `cis_app`, `main.py:89-94`), one rate limiter, one Sentry and one deploy. A tenant feature ships on the CIS deploy cadence and job gate |
| B2 | `api/routers/auth.py:34-41,64-73,330-338` | **One `JWT_SECRET` signs both tenant JWTs and legacy staff JWTs** (HS256). They are told apart only by the `role` claim (`verify_tenant_jwt`, `auth.py:86-94`) |
| B3 | `api/main.py:326-335` | `POST /auth/verify-tenant` (used by the portal gate) calls `verify_jwt`, **not** `verify_tenant_jwt`. It does not check `role == "tenant"`, so a valid staff token is not refused with 401 here. It fails with a KeyError → 500 instead, because the staff payload has no `name`/`plan_tier` (`auth.py:330-338`). Worth a fix in any split. (`auth.py:158-170` has the same shape, but that router is not registered in `main.py:227-269`) |
| B4 | `api/routers/admin_pipeline.py:1-4,4658-4690` | `GET/POST /admin/brand-identity` is **dual-auth**: a tenant Bearer gives that tenant's rules, and `X-Admin-Secret` gives the AA-internal rules. The portal calls it under the `/admin` prefix |
| B5 | `api/routers/v1_tours.py:676-696` | `GET /v1/tours/{id}/full` is dual-auth (admin secret → AA internal tenant, else tenant JWT) |
| B6 | `api/routers/v1_pipeline.py:44-69` | A staff-only router lives under the tenant-looking `/v1/pipeline` prefix |
| B7 | `api/routers/admin_atoms.py:60-90` | Staff-only route that inspects tenant Bearers in order to refuse and log them. This is defensive code that exists because `portal/app/api/tenant/[...path]` forwards **any** path (`route.ts:27-32`, no allow-list) |
| B8 | `api/routers/auth.py:173-240` | `verify_tenant_api_key`: one dependency accepts **either** `X-Admin-Secret` (as the AA-internal pseudo-tenant) **or** `X-API-Key` (tenant). Server-to-server tenant auth and staff auth are fused |
| B9 | `api/main.py:289-335` + `modules/api_gateway/main.tf:94-339` | Tenant login, tenant APIs and staff APIs share one REST API, one stage, one custom domain `api-cis.lumiguides.it.com` (resources `/auth`, `/admin`, `/content`, `/v1`, docs) and one throttle and WAF profile |
| B10 | `frontend/app/admin/tenants/*` (Tenant 360) and `/admin/tenant-activity` | Legitimate staff views **of** tenants (support, cost, quality). This is not a link between the apps, but it is the reason a "staff support view" of the portal does not exist (`apps.ts:30-32`) |

**Separation checklist implied by §2:** remove L1/L2 (both login cross-links). Decide whether L3 stays (old bookmarks) and drop it from the guard test if not. Delete L5. Move L6/L7 (the trip page) to the portal/CRM host. Turn C1 into a versioned package, or let the portal own its copy (drop the byte-equality test). Strip C2/C3. Rename the admin `/api/tenant/*` proxies (P1–P3) to `/api/admin/*`. Give the tenant (and CRM) API its own prefix and domain or REST API, and its own token audience and secret (B2/B3/B4/B9). Add a path allow-list to the portal BFF (B7).

---

## 3. Shared infrastructure on acc2 and what a new app can reuse at about $0 marginal cost

| Resource | Today | Source | Reuse by a new app (CRM) | Marginal cost to the new app |
|---|---|---|---|---|
| VPC, private subnets, NAT **instance** `t4g.nano` | Shared (`App=shared`) | `accounts/aa365/main.tf:60-79`; `modules/vpc/main.tf:154` | Yes: tasks in the existing private subnets, own SG (ADR 0004b) | $0 (NAT instance, not NAT Gateway: no per-GB processing fee; estimate) |
| ECS cluster `aa-cis-dev-cluster` | 3 services (live). Container Insights **disabled**. Capacity providers FARGATE + FARGATE_SPOT. Exec logging OVERRIDE to one group | `modules/ecs/main.tf:40-80`; live `list-services` | Yes: a new service on the same cluster (Booking pattern) | $0 for the cluster. Pay only per task (§4) |
| ALB (internet-facing, SG admits :80 only from the VPC) + internal NLB + **VPC link** | Shared. CIS is the default action; Booking has a `/booking/*` listener rule, priority 100 | `main.tf:145-160`; `modules/alb/vpc_link.tf:34-38`; `booking.tf:23-25,32-44,356` | Yes: one more listener rule (e.g. `/crm/*`) + target group | ~$0 (target group free; a rule adds negligible LCU at Dev volume; estimate) |
| API Gateway | CIS REST API (`/auth`, `/admin`, `/content`, `/v1`, docs; domain `api-cis.…` with an empty base path, so no second mapping on that domain). Booking has its **own REST API** on the same VPC link, domain `api-booking.…` with throttle 20/40. TripPlanner uses HTTP API v2 + Lambda | `modules/api_gateway/main.tf:9-339,542-551`; `booking.tf:445-567`; `custom_domains.tf:119-143,160-183` | Yes: a third REST API + `api-crm.lumiguides.it.com` (cert + Route 53 record), copying `booking.tf` | REST API pay-per-request (~$3.50/M requests, estimate). Dev volume ≈ $0. Custom domain/ACM free; Route 53 record free within the hosted zone (estimate) |
| RDS `aa-cis-dev-db` | `db.t4g.small` (2 GB), single-AZ, gp3 20 GB (max 100), PG 15.17. `max_connections` **181** (measured 16/10) | `modules/rds/variables.tf:9-26`; `modules/rds/main.tf:108-131`; live describe; `observability_ecosys.tf:48-52` | Yes: own schema `crm`, roles `crm_owner` NOLOGIN / `crm_app` LOGIN with CONNECTION LIMIT (ADR 0008 §3 steps 3-4) | $0 until a resize. **Connection budget:** LOGIN limits today are `cis_app` 90 + `tripplanner` 30 + `booking` 15 + `aa_app_user` 15 + `db_migrator` 5 = **155 / 181** (`observability_ecosys.tf:59-72`), plus the master (unlimited) and 3 reserved. Booking actually uses a pool `max_size=5` against its limit of 15 (`AA-Booking backend/app/db.py:65-69`). A `crm_app` of 5-10 fits only with an offset (e.g. Booking 15 → 10) or a resize to t4g.medium (~+$31/month single-AZ, research/04 §1 price list) |
| ElastiCache Redis | `cache.t3.micro`, 1 node, tagged `cis`, used by the CIS api (rate limit, flags) | `main.tf:117-129`; `modules/elasticache/variables.tf:17-19`, `main.tf:41-42` | Possible (add the CRM SG to `redis_ingress_sg_ids`), but it is a CIS-tagged resource | $0 marginal; adds coupling |
| Cognito | 2 pools on **Essentials**: WORKFORCE (staff) and EXTERNAL (tenant users + travellers). The EXTERNAL `cis-portal` confidential client already exists for the portal host | `identity.tf:13-18,168-184`; `identity_variables.tf:163-168` | Yes: the CRM UI under the portal host can use the **same `cis-portal` client** (same callback host), or a new EXTERNAL client (free) | $0 under 10,000 MAU/account, then $0.015/MAU (ADR 0006 `0006-ecosystem-identity.md:428-440`). External managed-login branding is still missing (`identity.tf:76-79`) |
| SES | Domain identity `lumiguides.it.com`, DKIM, MAIL FROM `bounce.`; 3 configuration sets (`workforce`, `external`, `transactional`); one From `no-reply@lumiguides.it.com`; out of sandbox (17/10) | `ses.tf:27-31,47-48,123-173`; `ses_variables.tf:15-24`; `identity.tf:35` | Yes: send through `transactional` (one IAM policy like `ses.tf:216` `booking_ecs_task_ses_send`) | $0.10 per 1,000 mails (ADR 0006:432) |
| SES inbound | One **active receipt rule set per region**, currently `aa-cis-dev-e2e` (single recipient on `e2e-mail.` sub-domain → S3) | `e2e_mailbox.tf:47-53,196-207` | CRM forwarding addresses (D6 b) must be added as rules **in this same active set** | $0.10/1,000 + $0.09/1,000 chunks (research/04 §1, AWS SES pricing) |
| S3 | Bronze bucket (CIS), TP artifacts, diag ALB logs, e2e mail | `main.tf:100-107`; `tripplanner.tf:167`; `e2e_mailbox.tf:71` | A new bucket per app (Booking has none) | Storage cents at Dev volume (estimate) |
| WAF | One web ACL `module.waf` on the **ALB** (CommonRuleSet enforced, rate 1000). REST API stage association is **off** (`waf_protect_rest_api_stages = false`) | `main.tf:260-284`; `variables.tf:202-205`; `modules/waf/main.tf:197-210` | Reuse the same web ACL. Associating another stage adds requests only, with no new ACL fee ($0.60/M requests; ADR 0006:444-446) | ~$0 at Dev volume. A **new** ACL would be ~$5 + $1/rule |
| Secrets Manager | Per-app DSN secrets (`booking/dev/database-url`, `tripplanner/...`) | `booking.tf:137-142` | Own `crm/dev/database-url` | $0.40/secret-month (research/04 §1) |
| Observability | SNS alerts topic → `var.alert_email` (default **`pqnghiep1354@gmail.com`**); budgets per App (`cis 150, tripplanner 25, booking 25, shared 50`; key `crm` already allowed); per-role connection alarms | `variables.tf:152-156,168-180`; `observability.tf:60-65,262-331`; `observability_ecosys.tf:59-72` | Add a `crm` budget and a role row | $0 (budgets without actions are free; `docs/ops/finops.md:71-73`) |
| CI / deploy | GitHub OIDC least-privilege deploy role per app; DB Migrate + Schema Dump + isolation probe workflows in Infra | `booking.tf:569-708`; Infra `.github/workflows/{db-migrate,db-schema-dump,db-isolation-probe}.yml` | Yes: a `crm` entry in `db/owners.yaml`, mirrored migrations `db/migrations/crm/` | $0 (GitHub Actions minutes on the org plan, not checked) |
| Vercel | **Hobby** team: 200 projects, **100 deployments/day**, non-commercial use only. **Microfrontends: Hobby includes 2 microfrontend projects and 50K routed requests/month**; Pro charges $2/1M and $250 per extra project | [vercel.com/docs/plans/hobby](https://vercel.com/docs/plans/hobby) and [vercel.com/docs/microfrontends](https://vercel.com/docs/microfrontends), accessed 20/10/2026 | A new project for a CRM UI is $0 on Hobby, but it shares the 100/day deploy cap and the non-commercial clause. The portal + CRM as 2 microfrontend projects fit the Hobby allowance. Plain Next.js `rewrites` (multi-zone) cost nothing extra | $0 on Hobby. Pro = $20/developer seat-month (same page) |

**Net:** a new app on this platform pays only for (a) its own Fargate task(s), (b) a secret, logs and ECR storage,
(c) per-request API Gateway/SES/WAF at Dev volume, and (d) the new paid services the spec needs (KMS keys, e-sign,
LLM, messaging). Everything else is already paid under `App=shared`, `App=cis`, or is free.

---

## 4. How AA-Booking was bootstrapped on shared infra (the template for a separate CRM app)

| Piece | Booking's implementation | Source |
|---|---|---|
| Decision record | Root ADR 0004 (stack = CIS stack, repo layout, CI 5 checks, deploy path, runtime, DB role, migrations, own job table, health/ready) + repo ADR `docs/adr/0001-implements-root-0004.md` | `docs/adr/0004-aa-booking-stack-and-bootstrap.md:50-200` |
| Repo | `AdventureAsia365-Ecosys/AA-Booking`: `backend/` (FastAPI + asyncpg), `frontend/` (Next 16 staff admin, **copied CIS kit tokens**), `migrations/` | Booking `CONTEXT.md` (origin/main) :73-74 |
| Infra file | One self-contained `accounts/aa365/booking.tf` (735 lines) + `booking_variables.tf`. Prefix `aa-booking-<env>-*`. It only **reads** module outputs. The only touch on a CIS resource is one ALB listener rule | `booking.tf:1-45` |
| Resources | ECR `aa-booking-dev-api` (IMMUTABLE git-SHA tags, keep 10); log group `/ecs/aa-booking-dev` (30 days); secret `booking/dev/database-url` with **no value in Terraform**; own execution role (one secret only) and task role (SSM exec + SES send + PutMetricData only, workload boundary); task def **256 CPU / 512 MB**; service on the shared cluster with FARGATE base 1 + SPOT 3, circuit breaker, `ignore_changes [desired_count, task_definition]`, `propagate_tags = SERVICE` (`App=booking`); own SG (ADR 0004b); target group + listener rule `/booking*`; **own REST API** on the existing VPC link with throttle 20 rps / 40 burst; custom domain `api-booking.lumiguides.it.com`; GitHub OIDC deploy role scoped to its own ECR and service | `booking.tf:90-127,137-142,164-264,281-304,331-442,449-567,575-708`; `custom_domains.tf:119-143` |
| DB | Schema `booking`, role `booking` LOGIN (limit 15), DSN set by hand; key `bk-NNN`; byte copy in `AA-CIS-Infra/db/migrations/booking/`, applied by DB Migrate; reads CIS only through `catalog.v_*` grants; publishes 2 aggregate views to `cis_app` | ADR 0004 :137-183; Booking `CONTEXT.md` (origin/main) :58 |
| Jobs | Own `booking.job` table from the CIS DDL template (`shared/jobs/job_table_template.sql`, ADR 0003a), kinds `bk_*`. **Worker runs inside the API process as a lifespan task** (`WORKER_ENABLED`), not as a separate service (ADR 0004 d8 planned a separate worker service; the implementation chose in-process) | Booking `CONTEXT.md` (origin/main) :240-246; `backend/app/main.py:12,85-94` |
| Deploy guard | `deploy-dev.yml` preflight: reads task counts, then calls `GET /booking/ops/deploy-gate` with a GitHub OIDC token (audience `aa-booking-deploy-gate`, **no secret**). `DEPLOY_GATE_EXEMPT` kinds; fail closed | Booking `.github/workflows/deploy-dev.yml:15-35` |
| Frontend | Vercel project `aa-booking-admin`, deployed by its own CI workflow; staff sign in with Cognito WORKFORCE `booking-staff` | Booking `CONTEXT.md` (origin/main) :74; `identity_variables.tf:160` |
| Pool | asyncpg `min_size=0, max_size=5`, named `application_name` | `backend/app/db.py:65-72` |

**Booking's real monthly marginal cost on Dev.** Fargate us-west-1 x86 prices are $0.04656/vCPU-h and $0.00511/GB-h, from the AWS price list read in research/04 §1, accessed 20/10/2026 (not re-fetched here).

| Item | $/month | Basis |
|---|---|---|
| Fargate task 0.25 vCPU / 0.5 GB, always on (base 1 = on-demand) | **≈ $10.4** | 0.25×0.04656×730 = 8.50 + 0.5×0.00511×730 = 1.87 |
| Secrets Manager, 1 secret | $0.40 | research/04 §1 |
| CloudWatch logs (30-day retention) + alarms | ~$1–3 | estimate |
| ECR storage (≤ 10 images) | < $0.50 | estimate ($0.10/GB-month) |
| REST API requests, ALB rule, SES at Dev volume | < $1 | estimate |
| Vercel `aa-booking-admin` (Hobby) | $0 | Vercel Hobby page, accessed 20/10/2026 |
| **Total** | **≈ $12–15/month** | The `booking` per-App budget is 25 USD (`variables.tf:174`); ADR 0004 :134 said "a few USD per month" |

A CRM app on the same template at the same size (one 0.25/0.5 task with an in-process `crm.job` worker) costs about the
same before any spec-driven service (KMS, e-sign, scrubber, messaging) is added. At 0.5 vCPU / 1 GB it is ≈ $20.7
(0.5×0.04656×730 + 1×0.00511×730), which is the "$21" line of the previous recommendation.

**Serverless alternative already in the platform:** TripPlanner runs as 2 Lambdas behind an HTTP API v2 (`tripplanner.tf:331-506`). Idle cost there is ≈ $0 (pay per request). An option for low-traffic CRM public endpoints (intake form, client links), not for the job worker.

---

## 5. Cost lines of the previous recommendation: "module in CIS" choice vs intrinsic to the spec

Source: `docs/audits/2026-10-20-S245-tenant-crm/README.md` §13 (lines 654-702), §5 table (139-147), and
`research/04-economics-compliance-security.md` §3 (lines 171-208); `research/options.json` → option C `monthly_cost`.

**Key fact first.** The "module in CIS" choice was **not** what made the bill grow. Option C (pure module, inside the CIS
api/worker processes) was the *cheapest* option on Dev: $80–150 (`options.json` C; README:144). The extras came from
(a) giving the module its own always-on ECS service for isolation (+$21, D17), (b) an always-on Presidio scrubber
service, (c) a new WAF ACL, (d) vendor and sizing choices. The prod table (README:678-689) is **the same for A, B and C**
(README:145; research/04 §3.2), so the prod cost comes from the spec plus vendor/sizing choices, not from where the code lives.

### 5.1 Dev increment ($85–160/month, README:660-672)

| Line | $/month | Driven by | Classification | Lean lever (facts only) |
|---|---|---|---|---|
| Service `aa-cis-dev-crm` 0.5 vCPU / 1 GB, always on | ~21 | D17 (own service), isolation graft (README:208-213) | **Architecture choice.** Needed for any separate app, but the size is a choice | The Booking size (0.25/0.5) is ≈ $10.4. In-process worker (Booking pattern). Scale to 0 outside sessions (README:674 notes −$40–50 for CRM + scrubber) |
| Presidio scrubber, separate service 1 vCPU / 4 GB | 39 (ARM) – 49 (x86) | Spec F3 (scrubber) + choice of a self-hosted Presidio sidecar (research/04 §2.6) | **F3 is intrinsic. A separate always-on service is a choice** | Run the scrubber only on the worker path or on demand (README:675); ARM; known-value pass first (README:357). Comprehend is EN/ES only (research/04:47,140), so it does not fit VN |
| WAF for `/crm/public/*` | 10–15 | Spec module 1 public intake | Protection is intrinsic. A **new** web ACL is a choice | Reuse the existing shared web ACL (`main.tf:260-284`; association only adds $0.60/M requests) |
| KMS, a few test keys | 1–5 | Spec F1 + D7 a (key per agency) | **Intrinsic** (D7 a chosen) | — |
| S3 + SES inbound | < 5 | D6 b (SES forwarding) | **Intrinsic** | Reuse the active receipt rule set (`e2e_mailbox.tf:196-207`) |
| Twilio / Meta test numbers | ~5 | Spec module 9, D9 a | **Intrinsic**. D9 a (agency-owned WABA on Cloud API) means no BSP fee | No Twilio WhatsApp number needed on Dev if Cloud API test numbers suffice (unverified) |
| E-sign sandbox / BoldSign | 0–30 | Spec module 12 | Intrinsic need. Vendor is a choice; **D11 b = Documenso** | Documenso Teams $40 / Platform $250 / self-host (research/04 §2.5; documenso.com/pricing, accessed 20/10/2026 per that note). Dev can use a free sandbox (unverified) |
| Gateway test calls | 5–20 | Spec module 14 (AI) | **Intrinsic**. Capped by `shared.spend_budget` | Haiku default, test cap |
| Secret + log/alarm | 4–7 | Ops standard (ADR 0008 step 11) | Intrinsic | — |

### 5.2 Prod increment (10 / 50 / 200 agencies ≈ $500–925 / $1.6–2.0k / $4.7–5.2k, README:680-689)

| Line | 10 / 50 / 200 | Driven by | Classification | Effect of owner's answers (D1–D24) |
|---|---|---|---|---|
| WhatsApp via Twilio ~$5/agency | 50 / 250 / 1,000 | Spec module 9 + BSP choice | Choice | **D9 a**: the agency owns its WABA on Cloud API direct, so the AA cost is ≈ $0 (research/04:117; options.json C) |
| SMS ~$3/agency | 30 / 150 / 600 | Spec module 9 | Intrinsic, but pass-through is possible | Twilio sub-account billed to the agency (README:697) |
| LLM Sonnet ~$8.4/agency | 84 / 420 / 1,680 | Spec module 14 + model choice | Model is a choice | Haiku saves ≈ $8/agency (research/04:203). AI is off by default per tenant (D12), so real usage is likely lower |
| KMS $1–3/agency | 10–30 / 50–150 / 200–600 | Spec F1 + **D7 a** | Intrinsic (chosen) | Rotation drives $1→$3 (research/04:148) |
| SES ~$0.3/agency | 3 / 15 / 60 | Spec | Intrinsic | — |
| E-sign | 75 / 250 / 250 | Spec module 12 + vendor | Vendor choice | **D11 b Documenso Platform** = $250 flat from day one (BoldSign would be $75 at 10). Documenso Teams $40 or self-host are options to check against the Platform licence terms |
| Compute | 111 / 222 / 395 | Sizing: API 2 tasks + worker + Presidio (research/04:194) | **Sizing choice** | 1 task + in-process worker at pilot size; Presidio on demand |
| RDS increment | 0 / +63 / +188 | Scale (Multi-AZ resizes) | Intrinsic at scale | Prod RDS is part of AA-880 anyway |
| Vercel Pro | 40–60 / 60 / 60–100 | Hobby is non-commercial (research/04:15,49) | Platform/ToS, not CRM-specific | **D14 không** (no Pro now). This is a tension for the 30/11/2026 go-live (Hobby page: "restricts users to non-commercial, personal use only") |
| Google CASA (amortised) | 56–450 | Two-way Gmail sync (restricted scopes) | Choice | **D6 b removes it: $0** |
| Security baseline / WAF | 25–40 | Public surfaces | Partly reusable | Reuse the shared ACL |
| Not in totals: prod baseline | ~150–300 | AA-880 / ADR 0012 | Platform, not CRM | **D13 không** (prod not a precondition), but C7.1a forbids real PII on Dev (research/04:15) — a tension to resolve |

### 5.3 What moves with the owner's answers (arithmetic from the rows above, mid case, not a new design)

- Removed by D6 b: CASA $56–450/month (one-off $675–5,400/year).
- Removed by D9 a: WhatsApp BSP ≈ $5/agency → ≈ $0.
- Added by D11 b: e-sign is $250 flat from the first agency, instead of $75 at 10 agencies.
- Removed if D14 holds: Vercel Pro $40–100. Hobby ToS risk then remains for paying or commercial use.
- Choices not set by any D-answer, which the lean redesign can still change: compute sizing, an always-on scrubber service,
  a new WAF ACL, and Sonnet vs Haiku.

---

## 6. Facts the redesign must carry (no recommendations)

1. The portal is already its own Next.js app and Vercel project, but it lives in the CIS repo. It vendors the admin kit by
   byte-copy, uses the CIS API for everything, and signs tenants in with a shared API key. Cognito `cis-portal` and
   AA-813 membership are unbuilt.
2. The two visible cross-links are `frontend/app/login/LoginForm.tsx:159` and `portal/app/tenant-login/page.tsx:111`. The
   308s in `frontend/next.config.ts:23-25` are invisible legacy forwarding, required by a test.
3. A tenant-facing public page (`/trip/[tourId]`) and the URLs stored for it live on the admin host
   (`frontend/app/trip/...`, `api/routers/v1_trip_page.py:157`).
4. The backend has no tenant/staff boundary at deploy or auth level: one process, one HS256 secret for both token
   types, dual-auth routes, and an any-path tenant BFF.
5. A separate CRM app on the Booking template costs ≈ $10–21/month of compute on Dev (by size). Everything else on acc2
   is reusable at ≈ $0, except: the connection budget (155/181 already allocated), the single active SES receipt rule
   set, and the Hobby 100-deploys/day team cap and non-commercial clause.
6. Vercel Hobby allows 2 microfrontend projects (50K routed requests/month), so "CRM as its own Vercel project shown
   under the portal host" is possible at $0 on Hobby, within those limits.
7. Side note for the notifications request: the SNS and budget alert address is `var.alert_email`, default
   `pqnghiep1354@gmail.com`, at `infra/AA-CIS-Infra/accounts/aa365/variables.tf:152-156` (used by
   `observability.tf:65,262,270,323,331` and `cost_anomaly.tf:15`). `cis_ops_alert_email` and
   `booking_staff_notify_email` default to empty (`ses_variables.tf:40-49`, `booking_variables.tf:13-16`).
