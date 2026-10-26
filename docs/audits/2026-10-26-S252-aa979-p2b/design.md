# AA-979 P2b — tenant portal from Vercel to CloudFront → Fargate, partner-pool sign-in, 301 `/trip/*`, Sentry

Read-only design, S252 (Claude Code). Nothing applied, pushed or written outside this folder.

Sources read: Linear AA-979 (+ the S250 comment), AA-978 (Done); AA-Partner `CONTEXT.md`, `portal/`
(`next.config.ts`, `proxy.ts`, `lib/auth-server.ts`, `app/api/auth/tenant-login`), `web/` (`Dockerfile`,
`next.config.ts`, `proxy.ts`, `lib/oauth.ts`, `lib/writeGuard.ts`), `api/app/settings.py`,
`docs/implementation-notes/AA-979.md` + `AA-978.md`; AA-CIS-App `api/routers/auth.py`, `api/routers/v1_trip_page.py`,
`frontend/app/trip/[tourId]`, notes `AA-978.md` / `AA-979.md`; root ADR 0010 (§2, §6, §7), final design §4.2–4.5,
design v3 §2.1 / §4.7 / Lane P card, `delivery-plan.md` CRM-P2, `ecosystem-architecture.md`, backlog rows 0j / C16,
`db-schema-reference.md` (`shared.tenant_members`); AA-CIS-Infra `crm_edge.tf`, `crm_client_edge.tf`, `crm_web.tf`,
`crm_app.tf` (deploy role), `cicd_crm.tf`, `alb_rules.tf`, `identity_partner.tf`, `identity_variables.tf`,
`custom_domains*.tf`, `terraform.tfvars`, `modules/api_gateway`; `skill/aa-lessons/lessons.md` (Vận hành, Frontend).

---

## 0. What the design documents say P2b is (and is not)

| Source | P2b content |
|---|---|
| ADR 0010 §2 | Agency host is `portal.` (**Dev: `partner-dev.` until P2b**); cookies host-only; edge CloudFront → VPC origin → ALB → Fargate |
| ADR 0010 §6 / final §4.4 | `portal.` moves to CloudFront → Fargate (ALB host rule + secret origin header); Content studio users invited to re-enrol in the partner pool; 301 `/trip/*`; Sentry on the portal; rollback drill to Vercel. Vercel kept ≥ 7 calendar days, then clean-up (remove Vercel, delete CIS `portal/`, invert AA-885 guard) |
| final §4.2 / §4.3 | One host, one sign-in (partner pool, MFA), one sidebar; `tenant-login` (API key) **replaced** by partner-pool sign-in, API keys stay for machines; `/trip/[tourId]` → 301 to the client host |
| ADR 0010 §7 | Content studio business logic and data stay in the CIS API; `portal/` is UI only |
| Card R / E | R: a `cis-admin` token gets no portal session. E: a re-enrolled user keeps tenant and content; old Vercel URLs redirect with path; rollback drill to Vercel passes; the 24 portal smokes green on the new host |
| Partner CONTEXT | The EXTERNAL `cis-portal` bridge on `/crm/v1` is removed at P2b |

Facts that shape the design (checked in code, 26/10/2026):

1. **CIS `/v1/*` only knows the CIS tenant JWT** (HS256, `role=tenant`, `sub=tenant_id`, minted by
   `/auth/tenant-login` from the API key). CIS verifies no partner-pool token today (`identity_config.py`: WORKFORCE +
   M2M only).
2. **`shared.tenant_members` (CIS 276) already has `cognito_iss` / `cognito_sub`, `content_studio_role`
   (owner/editor/viewer), `status` invited/active/removed and `invitation_id`**, and its trigger feeds
   `tenant.membership.v1`. It holds **no e-mail** by design (AA-813 addendum). No invite/activate route exists yet
   (AA-978 notes: "No membership invite / activate route: AA-979").
3. **Only the CRM API may create partner-pool users** (task-role allow-list; an EventBridge alert fires on
   `AdminCreateUser` by anyone else) and the CRM already has invitation = claim → accept with AA system mail.
4. **`/trip/[tourId]` is not a portal page**: it is the CIS admin frontend (`aa-cis.lumiguides.it.com`,
   Vercel `aa-cis-frontend`), reading the public CIS `GET /v1/trip/{id}`; `v1_trip_page.py` hard-codes
   `real_url = https://aa-cis.lumiguides.it.com/trip/{id}`. The client host `go-dev.` serves `/c/*` only today.
5. Neither `portal/` nor `web/` has Sentry today.
6. `portal.lumiguides.it.com` is a Route 53 **CNAME** (TTL 300) to Vercel, from
   `aws_route53_record.vercel_frontend["portal"]` (`custom_domains.tf`, map `custom_domain_vercel_hosts`).
7. `crm_partner_signin_enabled = true` already (CRM web on the partner pool).
8. Path namespaces of the two Next apps do not collide except `/_next/*` and `/assets/*`: portal uses `/portal/*`,
   `/api/*`, `/tenant-login`, `/terms`, `/privacy`, `/assets/*` (logo); web uses `/`, `/(crm)/*`, `/auth/*`,
   `/bff/*`, `/join/*`, `/connect/*`, `/c/*`, `/healthz`, `/health`, `/prefs/*`, `/select-agency`, `/signed-out`.

---

## 1. Target architecture

```
                         Route 53 lumiguides.it.com
   portal.  CNAME ──(cutover flips the target; TTL 60 during the window)──┐
   partner-dev. A/AAAA alias ─┐                       go-dev. A/AAAA ─┐    │
                              v                                       v    v
 CloudFront crm_partner (as is)        CloudFront crm_client (as is)    CloudFront crm_agency  (NEW, portal.)
   cert partner-dev.                     cert go-dev.                     cert portal. (NEW, us-east-1)
   + X-AA-Origin secret                  + X-AA-Origin secret             + X-AA-Origin secret (same)
   CachingDisabled / AllViewer+CF        idem                             idem
              \                               |                               /
               └────────── VPC origin crm-vpc-origin (shared, as is) ────────┘
                                              |
                                 internal NLB aa-cis-dev-nlb :80
                                              |
                                  ALB :80 listener (alb_rules.tf order)
   prio  5 crm_api              partner-dev + secret + /crm,/crm/*            -> TG aa-crm-dev-api   (as is)
   prio  6 crm_client_public    go-dev + secret + /crm/public/*               -> TG aa-crm-dev-api   (as is)
   prio  7 crm_agency_api       portal. + secret + /crm,/crm/*                -> TG aa-crm-dev-api   (NEW)
   prio  8 crm_agency_studio    portal. + secret + /portal*,/api/*,/tenant-login* -> TG aa-crm-dev-portal (NEW)
   prio  9 crm_agency_studio_x  portal. + secret + /terms,/privacy,/assets/*  -> TG aa-crm-dev-portal (NEW)
   prio 10 crm_partner_default  partner-dev + secret                          -> TG aa-crm-dev-web   (as is)
   prio 11 crm_client_default   go-dev + secret                               -> TG aa-crm-dev-web   (as is)
   prio 12 crm_agency_default   portal. + secret                              -> TG aa-crm-dev-web   (NEW)
   prio 20 crm_origin_deny      any X-AA-Origin                               -> 403 (as is)
   prio 100 booking … default CIS (API Gateway path, untouched)
                                              |
            ECS cluster aa-cis-dev-cluster (Fargate ARM64)
            aa-crm-dev-api (as is)   aa-crm-dev-web (as is, env change)   aa-crm-dev-portal (NEW, Spot, :3000, /healthz)
                                                                              |  server to server, no CORS
                                                                              v
                              https://api-cis.lumiguides.it.com (API GW → VPC link → ALB → aa-cis-dev-api)
                                  /auth/tenant-session (NEW: partner token → short CIS tenant JWT)
                                  /v1/* (unchanged; tenant JWT)

 Sign-in on portal. (one sign-in, one sign-out):
   browser → /portal/... → portal proxy reads the CRM web session cookie __Host-aa_crm_s (sealed; portal unseals it
   READ-ONLY with the same session key) → no valid partner access token → 307 /auth/refresh?next=/portal/...
   (CRM web, same host) → managed login partner-auth (MFA) → back → portal BFF exchanges the partner access token at
   CIS /auth/tenant-session → host-only cookie cis_tenant_token (≤ 15 min, client=portal, csr=<role>, mid=<membership>)
   → existing /api/tenant/[...path] BFF unchanged.
 Legacy (window only): /tenant-login API-key form kept behind PORTAL_API_KEY_SIGNIN=true, removed at clean-up.
```

Why a third distribution (not an alias on `crm_partner`): adding a name to the partner distribution means swapping
the certificate of a live host (the reason `crm_client_edge.tf` gives); a new distribution reuses the VPC origin,
the origin secret and the managed policies at $0. Why a separate portal service (not merging `portal/` into
`web/`): P2b is a hosting + sign-in move; merging two Next apps is the "one shell" UI work (design §4.3, later);
separate images keep the rollback to Vercel trivially equivalent (same `portal/` code).

ALB limit that drives the rule split: **5 condition values per rule** (host + header + paths). `/portal*` (no slash)
also matches the asset prefix `/portal-assets/...`, so the studio needs only two rules.

---

## 2. Changes per repo

### 2.1 AA-Partner `portal/` (UI only; ADR 0010 §7)

| Change | Detail |
|---|---|
| Standalone build | `next.config.ts`: `output: "standalone"`, `outputFileTracingRoot: __dirname`, `assetPrefix: "/portal-assets"` (Next ≥ 15 serves the zone's own assets under the prefix; **gate: container smoke must load `/portal-assets/_next/static/*` with 200**; fallback if not: `basePath: "/studio"` + 308 map, more churn). Keep headers + 308 slug map. Drop the `/` → `/portal/dashboard` redirect only on Fargate builds (on `portal.` `/` is the CRM Home); keep it for the Vercel build via an env flag `PORTAL_ROOT_REDIRECT` |
| Dockerfile | `portal/Dockerfile` = copy of `web/Dockerfile` (node:22-alpine, `npm ci`, build, runtime without npm/corepack, user 10001, `KEEP_ALIVE_TIMEOUT=105000`, **`CMD node -e "process.env.HOSTNAME='0.0.0.0'; require('./server.js')"`** — lesson S249), `.dockerignore`; build args `GIT_SHA`, `APP_VERSION`, `NEXT_PUBLIC_CRM_URL=/` (same host now), `NEXT_PUBLIC_SENTRY_DSN`. Not a verbatim copy: `portal/` has no `.npmrc` (web's `COPY ... .npmrc` would fail), and `xlsx` installs from `cdn.sheetjs.com` (build needs that egress; Trivy/SBOM will list it) |
| Health | `portal/app/healthz/route.ts` → 200 `{ok, version, sha}` for any Host (outside the proxy matcher); Docker HEALTHCHECK + task healthCheck on it |
| Host guard | `PORTAL_HOSTS` env; proxy answers 404 for any other Host except `/healthz` (same rule as `web/lib/hosts.ts`); the proxy matcher must widen beyond `/portal/:path*` + `/tenant-login` (today) to cover `/api/*`, `/terms`, `/privacy` (exclude `/portal-assets`, `/healthz`) |
| Public origin (critic fix C2) | Behind CloudFront → ALB the standalone server builds `request.url` / `nextUrl.origin` from its bind address (`http://0.0.0.0:3000`, S249 finding in `web/lib/writeGuard.ts`). Today `proxy.ts` redirects with `new URL(LOGIN_PATH, request.url)` and `tenant-logout`, `tenant/[...path]`, `playground/proxy` call `refuseCrossSiteWrite(req)` against `nextUrl.origin` → on Fargate every redirect goes to `http://0.0.0.0:3000/...` and every write is 403. Add `portal/lib/writeGuard.ts` + `respond.ts` on the web's pattern using `PORTAL_PUBLIC_ORIGIN` (vendored `sameOrigin.ts` / `crossSiteGuard.ts` stay byte copies); a unit test lists every write route. Vercel builds leave `PORTAL_PUBLIC_ORIGIN` empty → request origin as today. Container smoke adds a POST with `Origin: https://portal.…` and a redirect `Location` check |
| Partner session gate | `portal/lib/session.ts` + `portal/lib/seal.ts` = **byte copies** of `web/lib/session.ts` / `web/lib/seal.ts` (add to `scripts/check_vendored_copies.py`, intra-repo pair), used **read-only** (portal never writes or refreshes `__Host-aa_crm_s`; `__Secure-aa_crm_r` has Path `/auth` and never reaches the portal). `session.ts` imports the type `WebConfig` from `./config`, so the portal needs a type-compatible `lib/config.ts` (or the copy pair widens to include the type). `proxy.ts` order (critic fix C3 — the earlier "no partner token → /auth/refresh" would bounce every existing API-key session at the flip and contradict "sessions survive"): (1) a `cis_tenant_token` that verifies and has no `amr=partner` (API-key session) → pass while `PORTAL_API_KEY_SIGNIN=true`; (2) valid partner access token → ensure CIS token (below) → pass; (3) otherwise 307 `/auth/refresh?next=<path>`, built on `PORTAL_PUBLIC_ORIGIN`. Fail closed outside development, as today |
| Exchange | `portal/lib/tenantSession.ts`: when `cis_tenant_token` is missing or expires in < 60 s, POST CIS `/auth/tenant-session` with the partner access token (and the chosen `tenant_id`); set the same 5 host-only cookies as `tenant-login` (Max-Age = token exp). **Also in the BFF route `/api/tenant/[...path]`** (critic S1): exchanged tokens live ≤ 15 min (API-key tokens 24 h, `JWT_EXPIRY_H`), and client fetches never pass the page proxy, so a page left open > 15 min would get 401s; the BFF re-exchanges when the partner token is still valid, else answers 401 and the client does a full `window.location.reload()` (proxy → `/auth/refresh`), never a push to `/tenant-login`. 409 `choose_tenant` → `/portal/select-tenant` (new page: list from CIS `GET /auth/tenant-memberships`). 403 `no_membership` → a "no Content studio access" page with a link to the CRM |
| API-key sign-in | `/tenant-login` + `/api/auth/tenant-login` stay, behind `PORTAL_API_KEY_SIGNIN` (true during the window, false at clean-up), labelled "Sign in with an API key (until <date>)"; a session from it behaves exactly as today |
| Sign-out | Portal sign-out clears the 5 `cis_*` cookies, then posts to the web's `/auth/sign-out` (one sign-out: CRM cookies + Cognito logout) |
| Sentry | `@sentry/nextjs` (server + client), DSN server-side from env `SENTRY_DSN` (secret), client from build arg; `environment=dev`, release = git SHA; no PII (`sendDefaultPii: false`, scrub cookies/Authorization) |
| Vercel during the window | `vercel.json` gets a host-conditioned redirect `has: host = aa-cis-portal.vercel.app` → `https://portal.lumiguides.it.com/:path*` (301) — conditioned so a rollback that points `portal.` back at Vercel does not loop. One last Vercel production deploy carries it (from the P2a code), then the production job in `vercel-deploy-portal.yml` is disabled (dispatch only, for the drill); PR previews kept until clean-up. **Order (critic fix C5)**: `vercel-deploy-portal.yml` deploys production on every push to `main` touching `portal/**`, and dispatch-production runs only from `main`. So this redirect + "no production on push" change must be its own small PR merged and deployed **before** the step-4 portal PR; otherwise merging step 4 ships the P2b portal (partner gate → `/auth/refresh`, which does not exist on Vercel) to the live `portal.` host and locks every tenant out before the flip. Vercel PR previews of P2b PRs run with `PORTAL_PUBLIC_ORIGIN` empty and `PORTAL_API_KEY_SIGNIN=true`, so the API-key preview smoke still works |

### 2.2 AA-Partner `web/`

- `WEB_PARTNER_HOSTS` takes both hosts. **Critic fix C4 — per-host public origin**: today `writeGuard`, `respond.ts`,
  `proxy.ts` and `oauth.ts` (redirect_uri, logout_uri) all use the ONE `WEB_PUBLIC_ORIGIN`. With that, the web on
  `portal.` before the flip sends every redirect and OAuth callback to `partner-dev.` (cookies land on the wrong host,
  so the pre-cutover partner sign-in smoke of step 5 cannot pass) and refuses every POST whose `Origin` is `portal.`;
  after a flip of the single origin, every `partner-dev.` POST would 403. Change: `publicOriginFor(cfg, hostHeader)`
  = `https://<host>` when the Host is in `WEB_PARTNER_HOSTS`, else `WEB_PUBLIC_ORIGIN` (never the bind address);
  used by write guard, redirects, the gate and the OAuth redirect/logout URIs (both hosts registered on `partner-web`).
  The OAuth tx cookie is host-only, so the callback must return to the host that started the sign-in — the per-host
  redirect_uri does that. `CRM_API_ORIGIN` stays `partner-dev.` (server to server).
- Zero CRM memberships after sign-in (`/select-agency` with an empty list) → redirect to `/portal/dashboard` instead
  of the empty-state page (a Content-studio-only person).
- Sidebar "Content studio" = same-origin `/portal/dashboard` (`CONTENT_STUDIO_URL`).
- `/auth/sign-out` also deletes the 5 `cis_*` cookies (both apps share the host).
- `/trip/[tourId]` on the **client host** (`lib/hosts.ts` `clientPathAllowed` adds `/trip/`): port of the CIS page,
  server-side fetch of CIS public `GET /v1/trip/{id}` (env `CIS_API_URL`), follows its 301/410 like the CIS page,
  `Referrer-Policy` default, indexable — but `web/public/robots.txt` is `Disallow: /` for every host (served on the
  client host via `CLIENT_PATH_PREFIXES`), so "indexable" needs a host-aware `app/robots.ts` (client host allows
  `/trip/`), or drop the claim (the CIS page sets no robots rule today). Separate slice, after the cutover (§3 step 9).
- Minor: `portal/app/favicon.ico` is served at `/favicon.ico`, which the ALB sends to the web on `portal.` (web has
  only `icon.svg`) → studio pages lose their tab icon; move the portal icon under `/assets/` or `app/portal/icon.*`.

### 2.3 AA-Partner `api/`

- **Studio invitations** (re-enrolment, §4): `crm-0NN` migration. **Critic fix C6**: the earlier "NULL role on
  `member_invitation`" plan does not fit the live table: `role` is NOT NULL, `member_invitation_accept_chk` requires
  `member_id` on `accepted`, the write guard is `crm.guard_invitation_write` (not only `guard_member_write`), crm-008
  rules (CRM02) govern it, and `tenant_id` has an FK to `crm.tenant` — but CONTEXT.md says a CIS tenant may have **no
  CRM agency**, so a studio-only tenant cannot hold a row there. Proposed: a separate `crm.studio_invitation`
  (same token/e-mail encryption/claim shape and expiry rules, `cis_tenant_id uuid NN` without FK, `cis_invitation_id
  uuid NN UNIQUE`, no role, no member_id, status pending → claimed → activated/expired/revoked, own guard) and the
  claim endpoint dispatches on which table the token hash is in. A person invited to both gets two invitations.
  Ops route `POST /crm/ops/v1/tenants/{id}/studio-invitations`
  (WORKFORCE `cis-admin`, group `crm-platform-admin` or `cis-admin` write — see Q4) `{email, cis_invitation_id,
  locale, crm_role?}`; same AA system mail, claim, accept. On accept: call CIS M2M
  `POST /tenant/membership/v1/invitations/{cis_invitation_id}/activate {iss, sub}` (new scope `cis.tenant/activate`);
  on failure a `crm_studio_activation` job retries (outbox, backoff), the join page says "Content studio access is
  being set up".
- Origins: the API has no Origin check for partner calls (BFF is server to server); `PARTNER_WEB_ORIGIN` is only
  the join-link origin. Keep it and `MAIL_OAUTH_REDIRECT_BASE` on `partner-dev.` for the whole window (critic C4:
  no API env change → no `crm.job`-gated API deploy inside cutover or rollback); switch both at clean-up together
  with the Google/Microsoft redirect URIs. The CRM M2M client must request `cis.tenant/activate` in its own token
  request (`app/cis/m2m.py` asks for `cis.tenant/read` alone today).
- Remove the Dev EXTERNAL `cis-portal` bridge on `/crm/v1` (code path + `COGNITO_EXTERNAL_ISSUER` /
  `COGNITO_CIS_PORTAL_CLIENT_ID` env) — **last**, after the cutover is verified.

### 2.4 AA-Partner CI / workflows / docs

- `ci.yml`: **Portal Docker Build Check** (native arm64, container smoke: `/healthz` 200, `/tenant-login` 200,
  `/portal-assets/_next/static/...` 200, Trivy, SBOM) → required check; Portal Build stays.
- New `deploy-portal-dev.yml` = copy of `deploy-web-dev.yml` (OIDC role `aa-crm-dev-app-deploy` via `AWS_ROLE_ARN`
  variable, environment `dev`, immutable SHA tag, latest revision with only the image swapped, no job guard — the
  portal runs no worker; gate variable `CRM_PORTAL_ENABLED`); post-deploy smoke `/healthz` on the task + public
  `https://<PORTAL_BASE_URL>/tenant-login`; then `ui-smoke-portal.yml` against the Dev host (base URL variable, no
  Vercel bypass on Fargate).
- `api/tests/unit/test_portal_guards.py`: invert/extend (standalone + assetPrefix set, `/healthz` public, no staff
  session, partner gate present, API-key route only behind the flag, deploy on `portal/**` triggers
  `deploy-portal-dev.yml`, no Vercel production deploy on push after cutover). No account IDs/ARNs (public repo).
- `CONTEXT.md` (Stack row Portal, Edge rows, Tenant portal section, Route classes: bridge removed),
  `docs/implementation-notes/AA-979.md` (P2b section, written while implementing).

### 2.5 AA-CIS-Infra (all through the CI apply role; grants already exist — `cicd_crm.tf` covers ECR `aa-crm-<env>-*`,
CloudFront distributions/functions/VPC origin, ACM, Route 53, ELB rules, ECS, logs)

New file `accounts/aa365/crm_portal.tf` (pattern of `crm_web.tf`):

| Resource | Spec |
|---|---|
| ECR `aa-crm-dev-portal` | IMMUTABLE, scan on push, keep last 10 |
| Execution role `aa-crm-dev-portal-ecs-execution-role` | workload boundary; ECR pull this repo; logs to the existing `/ecs/aa-crm-dev` group (30 d, AA-872) stream prefix `portal` (or its own group `/ecs/aa-crm-dev-portal`, 30 d — see Q8); read `crm/dev/web` (only the `session_secret` JSON key is mapped into the container, but IAM cannot scope to a JSON key: the execution role can read the whole secret incl. `cognito_client_secret`; if that is not acceptable, split `session_secret` into its own secret shell `crm/dev/web-session` read by both tasks — +$0.40/month) and `crm/dev/portal-sentry-dsn` |
| Task role `aa-crm-dev-portal-ecs-task-role` | ECS Exec SSM channel + exec session logs only; no AWS API |
| Secret shell `crm/dev/portal-sentry-dsn` | no `secret_version` (value out of band, like `crm_sentry_dsn`); mapped only with `crm_portal_sentry_enabled` |
| Task def `aa-crm-dev-portal` | Fargate ARM64, 0.25 vCPU / 0.5 GB (raise to 1 GB only if the container smoke shows memory pressure), port 3000, tag `bootstrap`; env `ENVIRONMENT`, `API_URL=https://api-cis.<zone>`, `PORTAL_HOSTS`, `PORTAL_PUBLIC_ORIGIN`, `PORTAL_API_KEY_SIGNIN`, `CRM_WEB_SIGN_IN_PATH=/auth/refresh`; secrets `WEB_SESSION_SECRET`, `SENTRY_DSN`; healthCheck `node -e fetch(/healthz)` |
| SG `aa-crm-dev-portal` (`app_security_groups.tf`) | ingress ALB → 3000 only; egress 443 (CIS API via NAT); not admitted by RDS |
| TG `aa-crm-dev-portal-tg` | ip, HTTP 3000, health `/healthz`, dereg 30 s |
| Service `aa-crm-dev-portal` | FARGATE_SPOT, desired 0 at create (→ 1 after the first image), circuit breaker + rollback, min 100 / max 200, grace 60 s, `ignore_changes [desired_count, task_definition]`, exec on, `propagate_tags=SERVICE`, tag `App=crm` |
| Alarms | no healthy target, unhealthy target (as web), TG 5xx count > 5 in 5 min |

New file `accounts/aa365/crm_agency_edge.tf` (pattern of `crm_client_edge.tf`):

| Resource | Spec |
|---|---|
| ACM `crm_agency` (us-east-1) + validation CNAME | **`*.<zone>` (wildcard), NOT `portal.<zone>`** — critic fix C1: `portal.` CNAMEs to `22ba595c1afe124b.vercel-dns-017.com`, whose CAA set (checked 26/10: globalsign, sectigo, pki.goog, letsencrypt) does not list Amazon, and a CAA lookup follows the CNAME, so an ACM cert for `portal.` fails with CAA_ERROR until the flip. A wildcard is CAA-checked at `lumiguides.it.com` / `it.com` (no CAA). Attached only to `crm_agency`; validation record `_x.lumiguides.it.com` does not touch the live `portal.` CNAME. Clean-up may swap to a `portal.`-only cert once the CNAME points at CloudFront (`cloudfront.net` has only `issuewild`) |
| CloudFront `crm_agency` | aliases `portal.<zone>`, same VPC origin / secret header / CachingDisabled / AllViewerAndCloudFrontHeaders, timeouts 60 s, PriceClass_200, http2and3, IPv6, TLSv1.2_2021, no WAF (W8), no geo block |
| ALB rules (priorities added to `alb_rules.tf`) | `crm_agency_api` 7, `crm_agency_studio` 8, `crm_agency_studio_x` 9, `crm_agency_default` 12 (§1); `tools/terraform/alb_rule_order.py` must pass |
| DNS record `portal.` | `moved { from = aws_route53_record.vercel_frontend["portal"] to = aws_route53_record.crm_agency }`, remove `portal` from `custom_domain_vercel_hosts`; record stays **CNAME** (a subdomain may CNAME to CloudFront), `records = [var.crm_agency_live ? <distribution domain> : var.crm_agency_vercel_target]`, TTL 60 during the window (300 after clean-up). Flip = in-place UPSERT, no delete/create gap |
| Variable `crm_agency_live` (bool, default false) | the ONE cutover switch: **the DNS target only** (critic fix C4). The web answers on both hosts with a per-host public origin (§2.2), so no web/API env flips and no ECS deploy is part of cutover or rollback; the CRM API keeps `PARTNER_WEB_ORIGIN` / `MAIL_OAUTH_REDIRECT_BASE` = `partner-dev.` for the whole window (join links and the registered mail OAuth redirect URIs keep working there) and moves at clean-up |

Edits:
- `crm_web.tf`: `WEB_PARTNER_HOSTS = partner-dev,portal`; `WEB_PUBLIC_ORIGIN` / `CRM_API_ORIGIN` unchanged
  (fallback only, C4).
- `crm_app.tf`: no origin change in P2b (C4); drop the EXTERNAL bridge env (last PR); deploy role: ECR push
  `aa-crm-dev-portal`, Register/Tag on `aa-crm-dev-portal:*`, UpdateService on the portal service with a portal-only
  task-definition condition (as `EcsUpdateCrmWebService`), DescribeServices, PassRole the two portal roles.
- `identity_partner.tf`: `partner-web` callback/logout add `https://portal.<zone>/auth/callback` and `/signed-out`.
- CIS api task env: **none** (critic S3). `api/core/identity_config.py` takes the Dev issuer / client ids as code
  constants with an env override precisely "so the ECS task definitions need no new variables"; the exchange uses
  `DEV_PARTNER_ISSUER` / `DEV_PARTNER_WEB_CLIENT_ID` the same way, in its own `MultiIssuerVerifier` that is never
  added to `cis_staff_issuers()` (a partner token must stay 401/403 on every staff path). This also removes the S250
  template-drift risk from Infra PR-1.
- M2M resource server: scope `cis.tenant/activate`, granted to the CRM M2M client only (then update the client
  secret's `scopes`).
- API Gateway: none — `/auth/{auth_proxy+}` and `/tenant/membership/{membership_proxy+}` already exist.
- Clean-up PR (not P2b): CloudFront Function on `crm_partner` 301 `partner-dev.` → `portal.` (except `/crm/*`), remove
  `crm_agency_vercel_target`, TTL 300, remove the `cis-portal` EXTERNAL client callbacks to `portal.`.

### 2.6 AA-CIS-App

| Change | Detail |
|---|---|
| `POST /auth/tenant-session` | Bearer = partner-pool **access** token, verified by the vendored `identity_verifier` against `(COGNITO_PARTNER_ISSUER, partner-web)` only — WORKFORCE (`cis-admin`, `breakglass`, …), EXTERNAL and M2M tokens → 403 (the card's R). Looks up `shared.tenant_members` active rows for `(iss, sub)` on active tenants; `tenant_id` in the body must be one of them; none → 403 `no_membership`; several and none chosen → 409 `choose_tenant`. Mints the existing tenant JWT with `client="portal"` (unmetered, AA-760) + `amr="partner"`, `mid`, `csr`; `exp = min(now+15 min, access token exp)`. Rate limited per `(iss, sub)` in Redis, **not per IP** (critic S2: on Fargate every portal → CIS call leaves through the one NAT address, so `login_throttle`'s per-IP buckets — 20 failures / 15 min — become one bucket for all tenants; for the kept API-key sign-in the portal BFF adds its own per-viewer limit on `CloudFront-Viewer-Address` before calling `/auth/tenant-login`); structured log without identity (fingerprint only) |
| `GET /auth/tenant-memberships` | same verification; list `{tenant_id, tenant_name, content_studio_role}` (no identity) |
| `POST /tenant/membership/v1/invitations/{invitation_id}/activate` | M2M scope `cis.tenant/activate`; row must be `invited` with that `invitation_id`; binds `(iss, sub)` → `active` in one transaction (trigger emits `membership.activated`; the CRM feed ignores it, as designed); idempotent for the same identity; 409 for another identity. Contract `tenant.membership.v1` → v1.1 in root `docs/contracts/` + samples |
| Staff invite | `POST /admin/tenants/{id}/members/invitations` (`tenant.write`, admin): creates the `invited` row (CIS decides the Content studio role), then the **CIS API relays** the staff Bearer to the CRM ops route (existing pattern `platform_apps.relay_authorization`, AA-936 — the CRM ops class accepts only WORKFORCE `cis-admin` tokens, and the CRM API has no CORS for a browser call), passing the e-mail (never stored in CIS) and `cis_invitation_id`. CRM failure → the row stays `invited` and the tab offers "send again" (idempotent on `cis_invitation_id`) |
| Role enforcement | tokens with `csr=viewer` → 403 on every non-GET `/v1/*` (one check in the tenant-JWT dependency); `csr=editor` → 403 on account writes (integrations, API key, members) — see Q5. API-key tokens (no `csr`) keep owner behaviour |
| `/trip/*` 301 | `frontend/next.config.ts` redirect `/trip/:path*` → `https://go-dev.<zone>/trip/:path*` — **307 first, 301 at clean-up** (critic S5: browsers cache a 301 without expiry, so a 301 cannot be rolled back for anyone who followed it) (query kept); `v1_trip_page.py` `real_url` from env `TRIP_PAGE_BASE_URL` (Dev `https://go-dev.lumiguides.it.com`); ships only after the web page is live |
| CORS / cookie domain | **No change.** The portal keeps calling CIS server to server; cookies stay host-only on `portal.`, no `Domain` attribute; the admin's 308 to `PORTAL_BASE_URL` keeps the same host |
| Frozen `portal/` copy | untouched in P2b (deleted at clean-up) |

### 2.7 Root repo

- ADR: a short **ADR 0010a** (or an amendment note on 0006b) — "Content studio sign-in: partner pool + CIS token
  exchange (`/auth/tenant-session`); CIS stays the only owner of Content studio roles; studio invitations are
  CIS-created and CRM-delivered; API keys are machine-only after clean-up". Two repos change if reversed → root ADR.
- ADR 0010 §2 / §6 status note (Dev agency host is `portal.` from the cutover date; P2b done).
- `docs/ecosystem-architecture.md`: AA-Partner row (portal on Fargate `aa-crm-dev-portal`, CloudFront `portal.`),
  diagram node `VERCEL_PORTAL` → kept "rollback only until <date>", Tenant users row (partner pool).
- `docs/contracts/tenant.membership.v1.openapi.yaml` v1.1; `docs/security/secrets-register.md` (`crm/dev/portal-sentry-dsn`);
  backlog row 0j / C16 + the "P2b + 7 days" time-gated row with the real date; master plan tracker.

---

## 3. Order of work and cutover (zero tenant downtime)

Gaps only (DM-11.4): no CIS deploy during a wave or with `shared.job` busy; CRM API deploy gated by `crm.job`.

| # | Step | Repo | Gate to go on |
|---|---|---|---|
| 0 | Inventory (read-only): active CIS tenants, which are synthetic, which used the portal in 30 days (CIS logs `client=portal` / tenant-login), current `shared.tenant_members` rows | CIS (ECS exec read-only) | list of people to re-enrol |
| 1 | Infra PR-1: `portal.` CNAME TTL 300 → 60 via the `moved` block (target unchanged = Vercel; if the new record uses `count`, the target address is `aws_route53_record.crm_agency[0]` and it keeps the `custom_domains_enabled` gate), wildcard cert (C1), M2M scope, `crm_portal.tf` (desired 0), `crm_agency_edge.tf` (distribution + cert + rules, `crm_agency_live=false`), alarms, deploy-role grants, partner-web callbacks | Infra | plan shows the CNAME as **update in place** (no destroy); apply; `alb_rule_order.py` on `describe-rules` |
| 2 | CIS PR: exchange + memberships + activate + staff invite + role checks (independent review: auth) | CIS | deploy, live: unauth 401, workforce token 403, M2M without scope 403 |
| 3 | Partner API PR: `crm-0NN` + studio invitations + activation job + origin list (independent review: migration + auth) | Partner + Infra DB Migrate copy | DB Migrate apply, deploy, schema-dump PR merged |
| 3b | **(moved up from step 7, critic C5)** Vercel freeze PR: host-conditioned 301 in `vercel.json` + production-on-push removed; one production deploy from it | Partner | `aa-cis-portal.vercel.app/x` → 301 `portal.…/x`; `portal.…` unchanged on Vercel |
| 3c | Web PR: per-host public origin (C4), zero-membership redirect, `cis_*` sign-out | Partner | Deploy Web Dev; `partner-dev.` CRM smoke green |
| 4 | Partner portal PR: standalone/Docker/healthz/assetPrefix/public-origin guard (C2)/partner gate (C3)/exchange/chooser/sign-out/Sentry/deploy workflow/CI check (risky: auth + workflow → review) | Partner | first image deployed, scale 0 → 1, rollout COMPLETED; no Vercel production run triggered |
| 5 | **Pre-cutover smoke on Fargate without DNS**: Playwright with `--host-resolver-rules="MAP portal.lumiguides.it.com <crm_agency CloudFront IP>"` (and `curl --resolve`): 24 smokes, partner sign-in, API-key sign-in, exchange, select-tenant, R and E checks | Partner e2e | all green |
| 6 | Re-enrol: staff invites each studio user (synthetic first); each claims, sets password + authenticator, accepts; activation lands; E check (same tenant, same tour/piece counts as via the API key) | CIS admin + CRM web | every invited person active, or still on the API key (allowed) |
| 7 | (done in 3b) | — | — |
| 8 | **Cutover** Infra PR-2: `crm_agency_live=true` = CNAME UPSERT to CloudFront only → apply. No ECS deploy (C4) | Infra | §6 live checks on both hosts; `dig portal.` → CloudFront; `via: … cloudfront` |
| 9 | `/trip` slice: web `/trip/[tourId]` on `go-dev.` live → CIS redirect + `TRIP_PAGE_BASE_URL` | Partner, CIS, Infra (env) | 301 map §5 |
| 10 | Rollback drill (§4) same day, timed | all | portal back on Vercel and forward again, smokes green both times |
| 11 | Remove the EXTERNAL `cis-portal` bridge on `/crm/v1` | Partner, Infra | CRM smoke green |
| 12 | Root PR: ADR 0010a, 0010 note, ecosystem-architecture, contract v1.1, register, backlog date "P2b + 7 = <date>" | root | — |

Why there is no downtime:
- The host and the cookies do not change: `cis_tenant_token` & co. are host-only on `portal.`, so every session that
  exists on Vercel at the flip keeps working on Fargate (the CIS JWT is verified by CIS, not by the host).
- The flip is an in-place CNAME UPSERT (no NXDOMAIN gap); with TTL 60 lowered ≥ 5 min (old TTL) before, resolvers
  move within ~1–2 min; during that time both targets serve the same users correctly.
- API-key sign-in stays available on Fargate during the window, so a tenant who has not re-enrolled is never locked
  out (design "API keys for machines only" happens at clean-up).
- The CRM keeps working on `partner-dev.` for the whole window (per-host origin, C4) and also on `portal.` after
  step 8; the `partner-dev.` → `portal.` 301 is clean-up.
- Residual (accepted on Dev): the portal runs one FARGATE_SPOT task, so a Spot interruption is a ~1–2 min 503 on the
  studio paths (same as the web today). For the cutover day only, run desired 2 or a `FARGATE` base of 1 if wanted
  (≈ +$0.25/day on demand).

---

## 4. Rollback

- **Trigger**: any red smoke, 5xx alarm, Sentry error burst, or sign-in failure on `portal.` that a forward fix cannot
  close in 30 min.
- **Action**: `crm_agency_live=false` → apply (CNAME back to the Vercel target; nothing else, so no ECS deploy and no
  `crm.job` / `shared.job` gate stands in the way — C4). CRM users go back to `partner-dev.` (fully working all
  window). Emergency only (CI blocked): one-line
  `aws route53 change-resource-record-sets --hosted-zone-id <id> --change-batch file://<tmp>.json --profile aa365-admin --region us-west-1`
  UPSERT of the same CNAME, then reconcile Terraform the same day.
- **What survives a rollback**: API-key sessions (same cookie, valid on Vercel); exchanged sessions too, until their
  ≤ 15 min token expires (Vercel's proxy verifies any tenant JWT at `/auth/verify-tenant`); partner-only people then
  use the API key or wait for roll-forward. CRM: unaffected (back on `partner-dev.`).
- **Vercel stays deployable** for 7 calendar days: project, domain attachment, last production build (P2a code + the
  host-conditioned redirect), `VERCEL_*` repo values. The CIS frozen copy is not needed for rollback (Vercel builds
  from AA-Partner) but stays until clean-up as decided.
- **Rollback of the other slices** (critic S6, previously missing): CIS exchange / memberships / activate / role
  checks are additive routes → revert PR + Deploy Dev (gated by `shared.job` / wave, so not on the cutover path);
  `crm-0NN` (new table only) → leave in place, disable the route by env flag; portal Fargate service → desired 0
  after DNS is back; `/trip` → revert the 307 (why 307 first); Cognito callback additions → harmless, left.
- **Drill** (card E): step 10, recorded with timings (flip → first green smoke on Vercel; flip back → green on
  Fargate).

---

## 5. 301 map

| From | To | Code | Where | When |
|---|---|---|---|---|
| `https://aa-cis.lumiguides.it.com/trip/:tourId` (+ query) | `https://go-dev.lumiguides.it.com/trip/:tourId` | 307 in P2b, 301 at clean-up | CIS `frontend/next.config.ts` | P2b step 9, after the client-host page is live |
| `https://aa-cis-portal.vercel.app/:path*` (old Vercel URL) | `https://portal.lumiguides.it.com/:path*` | 301 | `portal/vercel.json` redirect with `has: host` | P2b step 3b |
| `/portal/t1-rewrite`, … (13 old slugs) | new paths | 308 (unchanged) | `portal/next.config.ts` | as today |
| `https://portal.…/` | CRM Home (web); studio-only people → `/portal/dashboard` | 307 | web | step 8 |
| `https://partner-dev.lumiguides.it.com/:path*` except `/crm/*` | `https://portal.lumiguides.it.com/:path*` | 301 | CloudFront Function on `crm_partner` | **clean-up**, not P2b (CI deploy gates call `partner-dev./crm/*`; a POST must not be redirected) |
| `https://portal.…/tenant-login` | `/auth/sign-in?next=/portal/dashboard` | 308 | portal | **clean-up** (API-key sign-in removed) |

Stored URLs that keep working through the 301: `acp_deliver.tenant_tour_pages.url` rows and published copy that
links `aa-cis…/trip/…`; the page itself still calls CIS `GET /v1/trip/{id}`, which keeps `url_alive` fresh.

---

## 6. Tests and live verification

Unit / integration (in the PRs):
- CIS: exchange — partner-web access token → 200 + claims (`client=portal`, `amr`, `mid`, `csr`, exp ≤ 15 min);
  `cis-admin` / `breakglass` / EXTERNAL `cis-portal` / M2M / partner **id** token → 403; removed member → 403; tenant
  not in the caller's list → 403; two tenants → 409; inactive tenant → 403; viewer non-GET `/v1/*` → 403; editor
  account write → 403; API-key token unchanged. Activate — scope, idempotency, other identity 409, wrong status 409,
  integration on PG 15 with mig 276.
- Partner API: studio-only invitation writes no `crm.member`; accept with a CIS outage → job retries then succeeds;
  `crm_role` + studio invitation writes both; route-class test (ops route refuses partner tokens); guard SQLSTATEs.
- Portal: vendored session copies byte-equal; gate redirects without a partner session; staff cookie never accepted;
  API-key route 404 when the flag is off; `/healthz` public; assetPrefix set; `node --test` helpers for the exchange.
- Web: zero memberships → `/portal/dashboard`; sign-out clears `cis_*`; client host allows `/trip/`.
- Infra: `terraform plan` (CNAME = update in place, no destroy of any live record/rule), `alb_rule_order.py` source +
  post-apply `describe-rules`, `managed_login_branding.py` unaffected, `crm_edge_live_check.py` extended to `portal.`.

Live (Dev), with evidence in the AA-979 Linear comment:
1. Pre-cutover (host mapping to CloudFront): 24 portal smokes green on Fargate; `/portal-assets/_next/static/*` 200.
2. After cutover — **UI smoke both hosts**: `https://portal.lumiguides.it.com` (Fargate: 24 portal smokes + CRM web
   smoke + sign-in with partner pool + MFA) and the Vercel rollback target (`aa-cis-portal.vercel.app` → 301 with
   path; during the drill, the 24 smokes on Vercel via `portal.`). Screenshots desktop/390 px, light/dark (aa-ui-verify).
3. `curl -sI https://portal.lumiguides.it.com/tenant-login` → 200, `via` CloudFront, security headers present;
   raw `*.cloudfront.net` → 403 (deny rule); `https://portal.…/crm/health` → 200.
4. R: a `cis-admin` Cognito token at `/auth/tenant-session` → 403; a staff session in the browser on `portal.` gets no
   `/portal/*` page.
5. E: a re-enrolled synthetic user sees the same tenant name, tour pool count and content list as with the API key.
6. ECS: `aa-crm-dev-portal` rollout COMPLETED, image = merged SHA, alarms OK; Sentry test event received with release SHA.
7. `/trip`: `curl -sI https://aa-cis.lumiguides.it.com/trip/<id>` → 301 `go-dev…/trip/<id>`; target 200; a superseded
   id still 301s to the current one; a retired id 404/410 as before.
8. Rollback drill timings recorded.

---

## 7. Monthly cost (Dev, us-west-1, AWS list prices, est., D-19)

| New resource | $/month |
|---|---|
| ECS service `aa-crm-dev-portal`, Fargate **Spot** ARM64 0.25 vCPU / 0.5 GB, 24/7 (same size and estimate as `crm_web.tf`) | ≈ 2.2 (on-demand would be ≈ 7.2; 1 GB adds ≈ 0.7 Spot) |
| ECR `aa-crm-dev-portal` (≤ 10 images) | < 0.05 |
| CloudFront distribution `crm_agency` (Dev traffic inside the always-free 1 TB / 10 M requests) | 0 |
| ACM certificate `portal.` | 0 |
| Route 53 (record already exists; validation CNAMEs; queries) | ≈ 0 (cents) |
| 4 ALB listener rules (inside the LCU rule allowance at Dev volume) | < 0.10 |
| 3 CloudWatch alarms | 0.30 |
| Secrets Manager `crm/dev/portal-sentry-dsn` | 0.40 |
| Logs (30 d retention, a few MB) | < 0.10 |
| Portal → CIS API egress via the NAT instance | < 0.10 |
| CloudFront Function (clean-up only, free tier 2 M invocations) | 0 |
| Sentry (existing org plan; one more project) | 0 |
| **Total new** | **≈ 3.2 / month** (≈ 8.2 if on-demand) |

Vercel Hobby `aa-cis-portal`: $0 today, $0 removed (no saving, one less moving part).

---

## 8. What P2b must NOT do

- Not remove the Vercel project, its domain attachment or its `VERCEL_*` repo values, nor delete the CIS frozen
  `portal/` copy or invert the AA-885 guard — all clean-up, ≥ 7 calendar days after the cutover.
- Not redeploy Vercel production with P2b code (only the host-conditioned redirect build of step 7).
- Not move any Content studio business logic, data or role decision into AA-Partner; the portal never reads the
  `crm` or CIS schemas and never calls `/crm/*` (ADR 0010 §7). CIS decides Content studio roles; the CRM only carries
  the verified identity. No CIS event grants a CRM role; no CRM event grants a CIS role.
- Not enable CORS on CIS, not set a cookie `Domain`, not share cookies across hosts (`partner-dev.`, `portal.`,
  `go-dev.` stay host-only).
- Not change `/auth/tenant-login` or `X-API-Key` behaviour for machine callers; not remove the portal's API-key
  sign-in during the window.
- Not delete-and-recreate the `portal.` DNS record (CNAME UPSERT only), not swap the certificate of the
  `partner-dev.` or `go-dev.` distributions, not change existing ALB rule priorities.
- Not cache at CloudFront (CachingDisabled stays), not add WAF / geo block / prod pool (W8, AA-980).
- Not 301 `partner-dev.` in P2b (CI deploy gates and the API use it).
- Not touch the EXTERNAL pool beyond callback URL lists (TripPlanner / Booking travellers).
- Not put account IDs, ARNs, SG/VPC ids or the origin secret in AA-Partner (public repo, DM-6.10).
- Not use `:latest`; not deploy during a wave or with `shared.job` / `crm.job` busy; not let a subagent merge.
- Not merge the portal into `web/` (one-shell UI work is later, design §4.3).

---

## 9. Lessons applied

- S249 Next standalone on Fargate: force `HOSTNAME=0.0.0.0` in CMD.
- S250 Terraform apply re-registers CIS task defs from the template: check runtime flags are in the template before
  the CIS env change.
- S247 CloudFront data-source lookups need explicit List/Get grants (already in `CrmEdgeReadLookups`).
- S243/S248 two Terraform runs race the state lock: push Infra PRs one at a time.
- S240 apply from merged `main`, re-plan shows "No changes".
- S241 old branches keep repo-level secrets: delete `VERCEL_PORTAL_*` / `E2E_TENANT_API_KEY` at clean-up the same day
  the workflow is removed.
- S239 Vercel Hobby ~100 deployments/day: do the step-7 Vercel deploy early in the session.
- S237 Vercel preview without env is a no-op check: previews keep their env until clean-up.
- S248/S251 subagents cannot run live windows: prep scripts in lanes, the orchestrator runs steps 1, 5–10.
- AWS WAFv2 descriptions without parentheses (only relevant if a WAF is added later).
