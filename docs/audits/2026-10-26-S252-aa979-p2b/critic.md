# AA-979 P2b — adversarial critic of design.md (S252, read-only)

Verified against: AA-CIS-Infra main (5ebb4f4), AA-Partner main (336377b, one commit behind origin, portal-only UI
change), AA-CIS-App main (df811ef6), live DNS (dig, 26/10/2026), live ACM us-east-1 listing, db-schema-reference
(verified 25/10). All fixes below are applied in design.md (marked "critic fix Cn" / "critic Sn").

## Blocking (fixed in design.md)

| # | Issue | Evidence | Fix applied |
|---|---|---|---|
| C1 | ACM cert for `portal.` cannot be issued before the flip | `portal.` CNAME → `22ba595c1afe124b.vercel-dns-017.com`; CAA there = globalsign, sectigo, pki.goog, letsencrypt (no Amazon). CAA lookup follows the CNAME → ACM CAA_ERROR in Infra PR-1 | Wildcard `*.lumiguides.it.com` cert (CAA checked at the apex: none) on `crm_agency` only |
| C2 | Portal on Fargate: every redirect goes to `http://0.0.0.0:3000/...` and every BFF write is 403 | `web/lib/writeGuard.ts` documents that standalone `nextUrl` = bind address (S249); portal `proxy.ts` uses `new URL(LOGIN_PATH, request.url)`; `tenant-logout`, `tenant/[...path]` and `playground/proxy` call `refuseCrossSiteWrite` against `nextUrl.origin`. The design had a `PORTAL_PUBLIC_ORIGIN` env with no code using it | Portal `writeGuard.ts` / `respond.ts` on the web pattern; container smoke checks a POST with `Origin` and the redirect `Location` |
| C3 | The partner gate as written logs every existing API-key session out at the flip | Design proxy: "no valid partner token → 307 /auth/refresh". API-key sessions have no partner cookie, which contradicts "sessions survive" and "API-key sign-in kept" | Proxy order: verified API-key token (no `amr=partner`) passes while `PORTAL_API_KEY_SIGNIN=true`, then the partner path, then refresh |
| C4 | The web's single `WEB_PUBLIC_ORIGIN` breaks the dual-host window | `oauth.ts` redirect_uri/logout_uri, `respond.ts`, `writeGuard.ts` and the `proxy.ts` refresh redirect all use the one origin. Before the flip, partner sign-in on `portal.` sends the callback to `partner-dev.`, so the step-5 pre-cutover partner smoke cannot pass. After the flip, every `partner-dev.` POST is 403. Cutover and rollback also needed web plus CRM-API redeploys, and the API deploy is `crm.job`-gated (DM-11.4) | Per-host public origin for hosts in `WEB_PARTNER_HOSTS`. `crm_agency_live` now flips DNS only, so cutover and rollback are a single apply with no ECS deploy. The API's `PARTNER_WEB_ORIGIN` and `MAIL_OAUTH_REDIRECT_BASE` stay on `partner-dev.` until clean-up |
| C5 | Merging the portal PR (step 4) ships P2b code to the live Vercel `portal.` before the flip | `vercel-deploy-portal.yml`: push to `main` on `portal/**` deploys production, and a dispatch to production runs only from `main`. The "last Vercel deploy from P2a code" at step 7 was impossible once step 4 had merged, and the P2b gate redirects to `/auth/refresh`, which does not exist on Vercel | Vercel freeze PR (host-conditioned 301 + no production on push) moved to step 3b, before step 4 |
| C6 | The studio-invitation migration does not fit the live schema | `crm.member_invitation`: `role` NOT NULL, `accept_chk` requires `member_id`, guard `crm.guard_invitation_write`, crm-008 CRM02 rules, `tenant_id` FK → `crm.tenant`; CONTEXT.md: a CIS tenant may have NO CRM agency | Proposed a separate `crm.studio_invitation` (no FK to `crm.tenant`, no role/member), with the claim dispatching by token table |

## Should fix (applied in design.md)

- S1: Exchanged CIS tokens last at most 15 min, but client fetches never pass the page proxy. A page left open longer gets 401s. Fix: the BFF re-exchanges too, and on a 401 the client does a full reload (proxy → `/auth/refresh`) instead of going to `/tenant-login`.
- S2: On Fargate, all portal → CIS calls leave through one NAT IP. `login_throttle` is per IP (20 failures / 15 min), so one tenant's typos, or an attacker, block API-key sign-in for every tenant. Fix: throttle the exchange per `(iss, sub)`, and add a per-viewer limit (`CloudFront-Viewer-Address`) in the portal BFF before `/auth/tenant-login`.
- S3: The CIS env change in Infra PR-1 is not needed. `identity_config.py` already uses code constants with an env override "so task defs need no new variables". The partner verifier must be a separate `MultiIssuerVerifier` and never be added to `cis_staff_issuers()`. This also removes the S250 template-drift risk.
- S4: The staff invite "Tenant 360 calls the CRM ops route" would be a browser call to the CRM API, which has no CORS. Use the existing CIS relay pattern (`platform_apps.relay_authorization`, AA-936).
- S5: `/trip` 301 is cached by browsers with no expiry, so it cannot be rolled back. Use 307 in P2b and 301 at clean-up.
- S6: Rollback covered only DNS. Added rollback notes for the CIS routes, `crm-0NN`, the portal service, `/trip` and Cognito callbacks.
- S7: The execution role can read the whole `crm/dev/web` secret (IAM cannot scope a JSON key). This is stated now, with a split-secret option (+$0.40/month).
- S8: The "copy of web/Dockerfile" fails as-is: `portal/` has no `.npmrc`, and `xlsx` comes from `cdn.sheetjs.com`.
- S9: "Indexable" `/trip` on `go-dev.` conflicts with `web/public/robots.txt` `Disallow: /` (all hosts). Needs a host-aware `app/robots.ts`, or drop the claim.
- S10: The portal's `/favicon.ico` routes to the web on `portal.`, so the studio pages lose their icon. The portal proxy matcher must also widen for the Host guard.
- S11: `moved` target: if `crm_agency` uses `count`, the address is `[0]`, and it must keep the `custom_domains_enabled` gate.
- S12: The CRM M2M client requests `cis.tenant/read` alone (`app/cis/m2m.py`). The activate call needs its own scope request.

## Checked and OK

- ALB priorities 7/8/9/12 are free (map: 5, 6, 10, 11, 20, 100). Condition values per rule ≤ 5 (host 1 + header 1 + 3 paths). The origin secret is `special = false`, so it has no wildcards. All new rules sit below the deny rule at 20 (`alb_rule_order.py` invariants).
- No path collisions: the web has no `/api/*`. The portal uses no `next/image`, `next/font` or server actions, so `/_next/image` does not leak to the web.
- The VPC origin, the `X-AA-Origin` secret and the managed policies can be reused (the `crm_client_edge.tf` pattern). CachingDisabled, so authenticated pages are not cached at CloudFront.
- The web session cookie `__Host-aa_crm_s` (Path=/) carries `at`/`atExp`/`iss`/`sub`/`cid`. It reaches `/portal/*`, the refresh cookie stays on `/auth`, and `safeNext` allows `/portal/...`.
- `GET /auth/refresh?next=` exists. API GW `/auth/{auth_proxy+}` and `/tenant/membership/{membership_proxy+}` exist. `StaffBearerMiddleware` covers only staff paths, so `/auth/tenant-session` is not intercepted.
- The CIS verifier checks `token_use=access` and `client_id`, so partner ID tokens are rejected as the design expects.
- `shared.tenant_members` guard allows invited → active with an identity bound once. The activate route fits.
- Fargate Spot + ARM64 already run `aa-crm-dev-web`. The cost estimate matches `crm_web.tf` (≈ $2.2 Spot / $7.2 on-demand).
- The 301 loop risk is handled: the Vercel redirect only fires for host `aa-cis-portal.vercel.app`.
- `cloudfront.net` CAA has only `issuewild` entries, so a later `portal.`-only cert after the flip is possible.
- Vercel's own LE cert for `portal.` (issued ~S243) stays valid well past the 7-day window, so rollback serves valid TLS.

## Open questions with proposed answers (new or changed)

- Q2 (changed): share the web session secret? **Proposed:** yes for P2b. Note the execution role then reads the whole `crm/dev/web` secret. Split `session_secret` into `crm/dev/web-session` only if Nghiệp wants the CRM Cognito client secret out of the portal's reach.
- Q10 (sharpened, now a design input): the CRM `crm.tenant.tenant_id` equals the CIS `tenant_id` (the membership feed matches on it), but a CIS tenant may have no `crm.tenant` row. **Proposed:** separate `crm.studio_invitation` with no FK (C6). The alternative, provisioning a CRM agency for every studio tenant, is a business decision and is not proposed.
- Q11 (new): the wildcard cert covers every `*.lumiguides.it.com` name, but only on the `crm_agency` distribution. **Proposed:** accept on Dev and swap to a `portal.`-only cert at clean-up, or keep the wildcard. AWS holds the key, so the exposure is distribution-scoped.
- Q12 (new): during the window both hosts serve the CRM fully (C4). **Proposed:** yes. The `partner-dev.` → `portal.` 301 waits for clean-up, as already planned.
- Q13 (new): a Spot interruption causes a ~1–2 min studio outage. **Proposed:** accept on Dev. Optionally add a `FARGATE` base of 1 for the cutover day only.
- Q1, Q3–Q9: agree with the designer's proposed answers. For Q7, the mail OAuth redirect stays on `partner-dev.` until clean-up (C4), so no vendor-console step is needed before the cutover.
