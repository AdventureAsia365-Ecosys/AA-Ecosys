# AA-979 P2b — runbook: merge / apply order, pre-cutover checks, phase 2 (cutover, rollback drill, `/trip`)

S252, Claude Code (prepared by the implementation lane; the orchestrator runs every live step). Design:
`design.md` + `critic.md` (this folder). ADR: root `docs/adr/0010a-content-studio-partner-sign-in.md`.
Orchestrator decisions: Q1–Q13 = the proposed answers (CRM web on `portal.` with `partner-dev.` kept; web session read
only; API-key sign-in behind `PORTAL_API_KEY_SIGNIN`; staff invites via the CIS relay; studio roles enforced; `/trip`
307 after cutover, not in phase 1; shared log group prefix `portal`; separate `crm.studio_invitation`; wildcard cert on
`crm_agency` only; both hosts serve during the window; Spot accepted).

**Phase 1 (this runbook §1–§3) changes nothing users see**: `crm_agency_live = false` the whole time, so `portal.`
keeps resolving to Vercel. Phase 2 (§4) is prepared, not run.

Rules for every step: one-line AWS CLI only (WSL); `terraform-apply.yml` from merged `main`, one Terraform run at a time
(S243 lock race), re-plan "No changes" after each apply (S240); no CIS deploy during a wave or with `shared.job` busy, no
CRM API deploy with `crm.job` busy (DM-11.4, the deploy guards enforce it); AA-Partner has strict branch protection
(BEHIND -> update-branch -> CI -> squash; no auto-merge); risky PRs (auth, migration, workflow) get an independent agent
review before merge.

---

## 0. The PRs (all committed locally, none pushed)

| # | Repo | Worktree (`.tmp-session/wt/…`) | Branch | Commits | Risk / review |
|---|---|---|---|---|---|
| R | root | `root-aa979` | `docs/aa-979-p2b-adr-0010a` | `12bce3c` (+ this runbook sync) | docs + contracts (no CI gate) |
| I1 | AA-CIS-Infra | `infra-aa979` | `feat/aa-979-p2b-portal-service` | `6aba92c` | Terraform/IAM: review the plan |
| C | AA-CIS-App | `cis-aa979` | `feat/aa-979-tenant-session-exchange` | `c73d63c5`, `c14012e4` | auth: independent review |
| M | AA-Partner | `partner-aa979-mig` | `feat/aa-979-crm-studio-invitation` | `270f3bb` | migration: review |
| I2 | AA-CIS-Infra | `infra-aa979-crm020` | `chore/aa-979-copy-crm-020` | `38b3af3` | copy only |
| A | AA-Partner | `partner-aa979-api` | `feat/aa-979-studio-invitations-api` (on top of M) | `d39f85e`, `0f60f02` | auth + job: review |
| F | AA-Partner | `partner-aa979-freeze` | `feat/aa-979-portal-vercel-freeze` | `8ab9932` | workflow |
| W | AA-Partner | `partner-aa979-web` | `feat/aa-979-web-per-host-origin` | `e6475c9`, `dfe49a8` | auth redirects: review |
| P | AA-Partner | `partner-aa979` | `feat/aa-979-p2b-portal-fargate` | `d418fa1`, `b57c780` | auth + workflow: review |

PR A is stacked on M: after M squash-merges, rebase A onto `origin/main` (`git rebase --onto origin/main <M head> A`,
then resolve nothing: A only adds), push, open.

---

## 1. Merge / apply order (phase 1)

1. **R — root PR** first. It carries `tenant.membership.v1` 1.1 (the file C and A pin by sha256), `crm.ops.v1` 1.3
   (+ the checker policy for the second write-only field), ADR 0010a + pointers, the DM-7 row for
   `crm.studio_invitation` (I2's retention check needs it), the secrets register row (`crm/dev/portal-sentry-dsn`
   planned), schema ownership, ecosystem architecture, this audit folder. Check: `python3 tools/contracts/check_contracts.py`
   -> `contracts: 0 errors` (in the workspace, M1 also compares the CIS and Partner copies once C and A are merged).
2. **I1 — Infra PR-1** (TTL 300 -> 60 must be live ≥ 5 min before any cutover; do it first).
   - CI plan must show: `aws_route53_record.vercel_frontend["portal"]` **has moved to** `aws_route53_record.crm_agency[0]`,
     update in place (TTL only, same target); NO destroy of any record, rule or service. Create: ECR, 2 roles + policies,
     secret shell, task def, TG, service (desired 0), SG, 3 alarms, ACM (wildcard) + validation CNAME, distribution,
     4 listener rules. In place: `aws_ecs_task_definition.crm_web` (new revision: `WEB_PARTNER_HOSTS` = both hosts),
     `aws_cognito_resource_server.cis_tenant` (+ `activate`), `aws_cognito_user_pool_client.m2m_crm` (+ scope, same id),
     `aws_cognito_user_pool_client.partner["partner-web"]` (+ portal. callback / sign-out), `aws_iam_role_policy.crm_app_deploy`.
   - Merge -> dispatch `terraform-apply.yml` from `main` -> re-plan "No changes".
   - Live: `aws elbv2 describe-rules --listener-arn <http listener> --profile aa365-admin --region us-west-1 --output json > /tmp/rules.json`
     then `python3 tools/terraform/alb_rule_order.py --live /tmp/rules.json` -> OK (priorities 5,6,7,8,9,10,11,12,20,100).
   - Live: `terraform output -json crm_agency_edge` -> note `distribution_domain` (= `<CF>` below).
   - Live: `python3 tools/terraform/crm_edge_live_check.py --cf-domain <partner CF> --agency-cf-domain <CF>` -> all PASS
     (agency-studio / agency-legal 503 is fine while the portal is at desired 0).
   - `dig +short portal.lumiguides.it.com CNAME` -> still the Vercel target; `dig portal.lumiguides.it.com` TTL ≤ 60.
   - Secret value: none needed now (`crm_portal_sentry_enabled` stays false until a Sentry project exists).
   - Optional bookkeeping: add `cis.tenant/activate` to the `scopes` field of `aa-crm/dev/m2m-booking-client` (informational).
3. **C — CIS PR** (independent auth review first). Merge only with `shared.job` idle and no wave -> Deploy Dev ->
   rollout COMPLETED. Live checks (`api-cis.lumiguides.it.com`):
   - `curl -s -o /dev/null -w '%{http_code}' -X POST https://api-cis.lumiguides.it.com/auth/tenant-session` -> 401;
   - a WORKFORCE `cis-admin` access token as Bearer on the same route -> 403 `forbidden` (card R);
   - `GET /auth/tenant-memberships` without token -> 401;
   - `POST /tenant/membership/v1/invitations/<uuid>/activate` with an M2M token of scope `cis.tenant/read` only -> 403;
     without token -> 401;
   - an existing API-key token still works on `/v1/tours/pool` (owner behaviour unchanged).
4. **M — Partner crm-020 PR** (review) -> merge (Partner deploys on `api/**`: harmless, nothing reads the table yet;
   `crm.job` gate applies) -> **I2 — Infra copy PR** -> merge (Copy Guard + retention check green now) ->
   **DB Migrate** `check` then `apply` with `migration=crm/020_crm_studio_invitation.sql` (waits for every job table idle)
   -> merge the `bot/db-schema-reference` PR (crm ERD design page is `enforce=false`: no drift failure).
5. **A — Partner API PR** (review; rebased on main) -> merge with `crm.job` idle -> Deploy Dev -> `/crm/health/ready`
   200 (it now requires crm-020). Live: through the CIS relay once a staff Cognito session exists (see §3 step 6).
6. **F — Vercel freeze PR** -> merge -> **dispatch `Vercel Deploy (portal)` with target=production on main** (one
   deploy, early in the day: Hobby cap) -> `curl -sI https://aa-cis-portal.vercel.app/tenant-login` -> 301
   `location: https://portal.lumiguides.it.com/tenant-login`; `curl -sI https://portal.lumiguides.it.com/tenant-login`
   -> 200 (still Vercel). From now on no push deploys Vercel production.
7. **W — web PR** (review) -> merge -> Deploy Web Dev (no job guard) -> its smoke on `partner-dev.` green; then the agency
   host through the new distribution:
   `curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' --connect-to portal.lumiguides.it.com:443:<CF>:443 https://portal.lumiguides.it.com/clients`
   -> `307 https://portal.lumiguides.it.com/auth/refresh?next=%2Fclients` (per-host origin, not partner-dev.).
8. **P — portal PR** (review). Before merging: GitHub environment `dev` (AA-Partner) variables `CRM_PORTAL_ENABLED=true`,
   `CRM_AGENCY_CF_DOMAIN=<CF>` (optional `PORTAL_PUBLIC_SENTRY_DSN`). F must be merged and deployed (critic C5).
   Merge -> Deploy Portal Dev builds and pushes; desired is 0, so its smoke is skipped -> scale:
   `aws ecs update-service --cluster aa-cis-dev-cluster --service aa-crm-dev-portal --desired-count 1 --profile aa365-admin --region us-west-1`
   -> `aws ecs wait services-stable --cluster aa-cis-dev-cluster --services aa-crm-dev-portal --profile aa365-admin --region us-west-1`
   -> re-run Deploy Portal Dev (workflow_dispatch) so its smoke runs against the task (through `<CF>`).
   Verify no Vercel production run was triggered by the merge (Actions list of `vercel-deploy-portal.yml`).

---

## 2. Pre-cutover checks (portal. still on Vercel; reach the new stack through the distribution)

All green before phase 2. Evidence (outputs + screenshots) goes into the AA-979 Linear comment.

1. **Container smoke** — CI "Portal Docker Build Check" on P's head: `/healthz` 200 with the SHA, Host guard 404,
   `/tenant-login` 200, `/portal-assets/_next/static/*` 200 (the asset-prefix gate of the design), the signed-out redirect
   to `https://portal.example.test/auth/refresh?next=%2Fportal%2Fdashboard` (public origin, critic C2), same-origin POST
   200 / foreign origin 403. Trivy + SBOM green.
2. **CloudFront with `--resolve` / `--connect-to`** (one line each; `<CF>` = `crm_agency_edge.distribution_domain`):
   - `curl -sI --connect-to portal.lumiguides.it.com:443:<CF>:443 https://portal.lumiguides.it.com/tenant-login` -> 200,
     `via: … cloudfront`, HSTS / X-Frame-Options / CSP present;
   - `curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' --connect-to portal.lumiguides.it.com:443:<CF>:443 https://portal.lumiguides.it.com/portal/dashboard`
     -> `307 https://portal.lumiguides.it.com/auth/refresh?next=%2Fportal%2Fdashboard`;
   - `…/crm/health` -> 200 `aa-crm-api`; `…/` -> 307 `/auth/refresh` (CRM web); `…/healthz` -> the web's JSON;
   - `curl -sI https://<CF>/` -> 403 "Forbidden" (deny rule: raw CloudFront name);
   - `python3 tools/terraform/crm_edge_live_check.py --cf-domain <partner CF> --agency-cf-domain <CF>` -> all PASS.
3. **The 24 portal smokes on Fargate** — dispatch AA-Partner `UI Smoke (portal)` with `base_url=https://portal.lumiguides.it.com`,
   `target=fargate`, `resolve_via=<CF>` (pins the host in the runner's /etc/hosts). Needs `E2E_TENANT_API_KEY` (repo secret,
   exists) for the logged-in specs (API-key sign-in still on). Expect all green (host specs adapted for `fargate`).
4. **Partner sign-in end to end** (human, browser — see §5): map `portal.lumiguides.it.com` to `<CF>` in the local hosts
   file (one `getent ahostsv4 <CF>` IP), open `https://portal.lumiguides.it.com/` -> partner managed login (MFA) -> CRM
   home on portal.; then `/portal/dashboard` with a re-enrolled synthetic studio user -> the studio opens without the API
   key; several studios -> `/portal-access/select`; no studio -> `/portal-access/none`. Sign-out from the studio ends the
   CRM session too (back to `/signed-out` on portal.).
5. **API-key sign-in on Fargate** (same mapping): `/tenant-login` with the E2E tenant key -> dashboard; the session
   survives a reload; editor/viewer role checks do not apply to API-key sessions (owner behaviour).
6. **R check**: a `cis-admin` token on `POST /auth/tenant-session` -> 403; a staff session cookie on `portal.` opens no
   `/portal/*` page (the gate knows no staff cookie).
7. **E check** (after §3 re-enrolment of a synthetic user): the partner-signed-in user sees the same tenant name, tour
   pool count and content list as with the API key (`/api/tenant/me`, `/api/tenant/v1/tours/pool`, `/portal/content`).
8. **ECS / alarms**: `aa-crm-dev-portal` rollout COMPLETED, image = P's merged SHA, `aa-crm-dev-portal-*` alarms OK.

---

## 3. Re-enrolment (before the cutover; works on partner-dev. and through the distribution)

5. Inventory (read-only, CIS): active tenants, synthetic ones, who used the portal in 30 days (CIS logs
   `client=portal`, `tenant.login` audit rows), current `shared.tenant_members` rows.
6. Staff invite: `POST https://api-cis.lumiguides.it.com/admin/tenants/<tenant>/members/invitations`
   `{email, content_studio_role, locale}` through the admin BFF (staff `tenant.write`, a **Cognito** staff session: the CIS
   relay forwards the staff member's own WORKFORCE token to `crm.ops.v1`). Answer `delivery.status = sent`; send again
   with `…/members/<membership_id>/invitation/send`. Synthetic tenants first.
7. The person: mail -> `https://partner-dev.lumiguides.it.com/join?t=…` (PARTNER_WEB_ORIGIN stays partner-dev. in the
   window) -> claim (temporary password) -> managed login (new password + authenticator) -> accept -> "Content studio
   access is ready" (or "being set up": the `crm_studio_activation` job retries). CIS row `active` with the identity;
   feed event `membership.activated`.

---

## 4. Phase 2 — prepared, NOT run in this phase

### 4.1 Cutover (Infra PR-2)

- Precondition: §2 all green; TTL 60 live for ≥ 5 min; no wave needed (no ECS deploy in the cutover).
- Change: `accounts/aa365/terraform.tfvars` `crm_agency_live = true` (one line). Plan must show exactly one in-place
  update: `aws_route53_record.crm_agency[0]` records = the distribution domain. Merge -> apply -> re-plan "No changes".
- Optional for the day (Q13): `aws ecs update-service --cluster aa-cis-dev-cluster --service aa-crm-dev-portal --desired-count 2 --profile aa365-admin --region us-west-1` (≈ +$0.10/day on Spot); back to 1 after.
- Live (§6 of the design): `dig +short portal.lumiguides.it.com CNAME` -> `<CF>`; `curl -sI https://portal.lumiguides.it.com/tenant-login`
  -> 200 `via … cloudfront`; `…/crm/health` 200; raw `<CF>` 403; `crm_edge_live_check.py … --agency-cf-domain <CF> --agency-direct`
  PASS; UI smoke `target=fargate` without `resolve_via` green; partner sign-in + MFA on portal.; screenshots desktop / 390 px,
  light / dark (aa-ui-verify); `https://aa-cis-portal.vercel.app/x` -> 301 `portal.…/x`; Sentry test event with the SHA.

### 4.2 Rollback (and the drill, same day, timed)

- Trigger: a red smoke, the 5xx alarm, a Sentry burst or a sign-in failure on portal. not fixable in 30 min.
- Action: `crm_agency_live = false` -> plan (one in-place CNAME update back to the Vercel target) -> apply. Nothing else:
  no ECS deploy, no job gate. CRM users use partner-dev. (fully working all window).
- Emergency (CI blocked): one-line UPSERT of the same CNAME
  `aws route53 change-resource-record-sets --hosted-zone-id <zone id from terraform output lumiguides_zone_id> --change-batch file:///tmp/portal-cname.json --profile aa365-admin --region us-west-1`
  with `{"Changes":[{"Action":"UPSERT","ResourceRecordSet":{"Name":"portal.lumiguides.it.com","Type":"CNAME","TTL":60,"ResourceRecords":[{"Value":"<vercel target>"}]}}]}`,
  then reconcile Terraform the same day (re-plan must be "No changes" with `crm_agency_live = false`).
- Survives: API-key sessions (Vercel verifies any tenant JWT); exchanged sessions until their ≤ 15 min token expires,
  then API key or roll-forward. Other slices: CIS routes additive (revert PR + Deploy Dev if ever needed); crm-020 stays
  (new table only); portal service -> desired 0 after DNS is back; Cognito callbacks harmless.
- **Drill**: flip false at T0 -> first green Vercel smoke (UI smoke target=vercel on portal.) at T1 -> flip true at T2 ->
  first green Fargate smoke at T3. Record T1−T0 and T3−T2 in the Linear comment.

### 4.3 `/trip` slice (after the cutover is verified; separate PRs)

1. AA-Partner web: `/trip/[tourId]` on the client host (`clientPathAllowed` + `/trip/`, server-side CIS `GET /v1/trip/{id}`,
   follow 301 / 410 like the CIS page, host-aware `app/robots.ts` if it must be indexable — critic S9). Deploy Web Dev,
   check `https://go-dev.lumiguides.it.com/trip/<id>` 200.
2. AA-CIS-App: `frontend/next.config.ts` redirect `/trip/:path*` -> `https://go-dev.lumiguides.it.com/trip/:path*` as
   **307** (301 only at clean-up: a cached 301 cannot be rolled back, critic S5); `v1_trip_page.py` `real_url` from env
   `TRIP_PAGE_BASE_URL` (code default the current admin host, so no Terraform env change is needed first; S250 lesson).
3. Live: `curl -sI https://aa-cis.lumiguides.it.com/trip/<id>` -> 307 `go-dev…/trip/<id>`; target 200; a superseded id
   still forwards; a retired id 404/410 as before.

### 4.4 After the cutover (still P2b)

- Remove the Dev EXTERNAL `cis-portal` bridge on `/crm/v1` (Partner code + `COGNITO_EXTERNAL_ISSUER` /
  `COGNITO_CIS_PORTAL_CLIENT_ID` env in `crm_app.tf`) — last, after the cutover is verified.

### 4.5 Clean-up (≥ 7 calendar days after the cutover; root backlog time-gated row "P2b + 7 = <date>")

`PORTAL_API_KEY_SIGNIN=false` (`crm_portal_api_key_signin = false`); `/tenant-login` -> 308 partner sign-in; delete the
Vercel project / domain / `VERCEL_PORTAL_*` + `E2E_TENANT_API_KEY` repo values the same day the workflow goes (S241);
delete the CIS frozen `portal/` and invert the AA-885 guard; CloudFront Function 301 `partner-dev.` -> `portal.` (except
`/crm/*`); move `PARTNER_WEB_ORIGIN` / `MAIL_OAUTH_REDIRECT_BASE` + Google / Microsoft redirect URIs to portal.; remove
`crm_agency_vercel_target`, TTL 300; optional portal.-only certificate; `/trip` 307 -> 301.

---

## 5. Needs a human (browser / vendor console) — with proposed answers

| Step | Why a human | Proposed answer |
|---|---|---|
| Partner sign-in + MFA smoke (§2.4, §4.1) | managed login with an authenticator, browser only | Nghiệp (or the E2E partner user with its TOTP seed from Secrets Manager, if the e2e harness supports TOTP) runs it once with the hosts-file mapping; agent records the result |
| Staff invite call (§3.6) | the CIS relay needs a WORKFORCE **Cognito** staff session (MFA); no admin UI exists yet for Members invites | Nghiệp signs in to the admin, the agent drives the call through the admin BFF in that session; follow-up issue: a Tenant 360 Members tab with Invite / Send again |
| Sentry project `aa-partner-portal` + DSN (optional) | Sentry console | create it, put the DSN in `crm/dev/portal-sentry-dsn` (value out of band), set `crm_portal_sentry_enabled = true` and the `PORTAL_PUBLIC_SENTRY_DSN` variable; or leave Sentry off for Dev (proposed: create it, cost $0 on the current plan) |
| Re-enrolled people's own sign-in (§3.7) | their mailbox + authenticator | synthetic users first (Dev holds synthetic data only); real tenant users are not on Dev |
| Vercel production dispatch (§1.6) | none (agent, GitHub Actions) | — |
| Mail OAuth redirect URIs (Google / Microsoft console) | vendor consoles | NOT needed in P2b (stay on partner-dev. until clean-up, critic C4) |

## 6. Monthly cost of the new resources (Dev, us-west-1, list prices, est., D-19)

| Resource | $/month |
|---|---|
| ECS `aa-crm-dev-portal`, Fargate Spot ARM64 0.25 vCPU / 0.5 GB, 24/7 at desired 1 | ≈ 2.2 (0 at desired 0; on demand ≈ 7.2) |
| ECR `aa-crm-dev-portal` (≤ 10 images) | < 0.05 |
| Secrets Manager `crm/dev/portal-sentry-dsn` | 0.40 |
| 3 CloudWatch alarms | 0.30 |
| Logs (`/ecs/aa-crm-dev`, prefix portal, 30 d) | < 0.10 |
| NAT egress portal -> CIS API | < 0.10 |
| CloudFront distribution `crm_agency` + VPC origin reuse (free tier traffic) | 0 |
| ACM wildcard certificate + validation record | 0 (Route 53 queries: cents) |
| 4 ALB listener rules | < 0.10 |
| M2M scope, Cognito callback URLs | 0 |
| `crm.studio_invitation` rows, `crm_studio_activation` jobs | 0 |
| **Total** | **≈ 3.2 / month running (≈ 0.9 idle)** |
