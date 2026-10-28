# ADR 0010a — Amendment: Content studio sign-in through the partner pool and a CIS token exchange

- **Status:** Proposed (2026-10-26, S252). The design's open questions Q1–Q13 were decided by the orchestrating
  session on their proposed answers (critic-fixed design, S252); the tech lead confirms this ADR.
- **Scope:** AA-Ecosys: AA-Partner (`portal/` Content studio, `web/` CRM web, the CRM API), AA-CIS-App (the token
  exchange, the Content studio roles, the membership directory), AA-CIS-Infra (the agency host edge, the studio's
  Fargate service, the partner-web client, the M2M scope), the root repo (contracts).
- **Amends:** [ADR 0010](0010-aa-partner-app.md) decision 6 (portal move, stage P2b: how the studio signs people in
  and how they are re-enrolled) and decision 2 (the agency host serves the CRM and the studio from one CloudFront
  distribution on Fargate). [ADR 0006b](0006b-partner-pool-and-mfa.md) is applied as written (the partner pool is the
  pool of agency people, MFA required); this file only says how the Content studio uses it.
- **Implements:** ADR 0010 §6 P2b, final design §4.2–§4.4 ("one host, one sign-in, one sidebar"; `tenant-login`
  replaced by the partner-pool sign-in; API keys stay for machines).
- **Design and evidence:** [`design.md`](../audits/2026-10-26-S252-aa979-p2b/design.md) and
  [`critic.md`](../audits/2026-10-26-S252-aa979-p2b/critic.md) (S252, read-only design with an adversarial critic; fixes
  C1–C6, S1–S12); merge / apply order, pre-cutover checks and the prepared cutover, rollback drill and `/trip` slice:
  [`RUNBOOK.md`](../audits/2026-10-26-S252-aa979-p2b/RUNBOOK.md).
- **Related Linear:** AA-979 (CRM-P2), AA-978 (membership feed, Done), AA-813 (identity phase 3: tenant users).
- **Implementation status (2026-10-28):** the DNS cutover ran on 2026-10-27 (S253), with a rollback drill both ways.
  `portal.` points at the agency CloudFront distribution (Fargate); the Vercel project `aa-cis-portal` answers 301 to
  `portal.` and stays the rollback path. The clean-up (decision 5: the API-key sign-in flag off, the Vercel project
  removed) starts on 2026-11-03. Evidence: [cutover record](../audits/2026-10-27-S253-aa979-cutover/README.md).

## Context

Until P2b the tenant Content studio (AA-Partner `portal/`, Vercel project `aa-cis-portal`, host `portal.`) signs a
tenant in with its CIS **API key**: the portal BFF calls CIS `POST /auth/tenant-login` and keeps the 24-hour tenant
JWT in five host-only cookies. The CRM web signs agency people in through the **partner pool** (ADR 0006b). ADR 0010
asks for one host, one sign-in and one sidebar after P2b. Constraints that shape the answer:

- CIS `/v1/*` knows only its own tenant JWT; nothing in CIS verified a partner-pool token.
- CIS is the directory of Content studio memberships (`shared.tenant_members`, CIS 276, AA-978) and holds no e-mail.
- Only the CRM API may create partner-pool accounts (task-role allow-list, EventBridge alert on any other caller).
- A CIS tenant may have no CRM agency (a studio-only customer).
- ADR 0010 §7: Content studio logic and data stay in the CIS API; the studio is UI only. No CIS event grants a CRM
  role; no CRM event grants a CIS role.

## Decisions

1. **One host, one sign-in.** On the agency host the CRM web owns the partner-pool session (sealed host-only cookie).
   The studio reads that session **read only** with the same key and never writes or refreshes it (the web's
   `/auth/refresh` does). Sign-out is one action: the studio clears its cookies and posts the web's sign-out (which
   clears the studio's cookies too and ends the Cognito session).
2. **CIS token exchange.** The studio swaps the person's partner-pool **access** token (client `partner-web`) for a
   short CIS tenant JWT at CIS `POST /auth/tenant-session`: at most 15 minutes and never past the access token, claims
   `client=portal` (unmetered), `amr=partner`, `mid` (membership), `csr` (Content studio role). CIS verifies the token
   with its own partner-pool verifier, which is never a staff issuer: WORKFORCE (`cis-admin`, `breakglass`), EXTERNAL
   and M2M tokens are refused (403). Several memberships -> the person chooses (`GET /auth/tenant-memberships`); none
   -> no studio. The exchange is throttled per identity, not per IP (one NAT address on Fargate).
3. **CIS stays the only owner of Content studio roles**, and enforces them on every tenant-JWT path: viewer = read
   only; editor = no account writes (channel connections, API key, members, webhooks); owner and API-key tokens
   unchanged. The CRM role plays no part in the studio, and CIS never passes a CRM role.
4. **Invitations are CIS-created and CRM-delivered.** Staff invite from Tenant 360 (CIS `tenant.write`): CIS creates
   the `invited` membership with the role it decides, then relays the address ONCE (staff relay, the CRM `crm.ops.v1`
   route `POST /tenants/{id}/studio-invitations`) to the CRM, which sends the AA system mail and owns claim and accept
   in the partner pool (its own table `crm.studio_invitation`, crm-020, because the tenant may have no CRM agency). On
   accept the CRM binds the verified identity at CIS (`tenant.membership.v1` 1.1 `activateInvitation`, M2M scope
   `cis.tenant/activate`), retried by a job when CIS is down. CIS never stores the e-mail; the CRM stores it sealed
   under a key derived from the invitation token.
5. **API keys are for machines after the clean-up.** During the P2b window (the DNS cutover plus at least 7 calendar
   days) the studio keeps the API-key sign-in behind `PORTAL_API_KEY_SIGNIN`, so nobody who has not re-enrolled is
   locked out and a session that existed at the cutover survives it. At the clean-up the flag goes off and
   `/tenant-login` goes to the partner sign-in; `X-API-Key` and `/auth/tenant-login` stay for machine callers.
6. **Hosting.** The studio runs as its own Fargate service (`aa-crm-<env>-portal`, Spot on Dev) behind a third
   CloudFront distribution for the agency host (wildcard certificate: the Vercel CNAME's CAA forbids a host-only one
   before the flip), sharing the VPC origin and origin secret. The ALB routes the studio's paths (`/portal*` including
   its asset prefix, `/api/*`, `/tenant-login*`, `/terms`, `/privacy`, `/assets/*`) to the studio, `/crm*` to the
   CRM API, the rest to the CRM web. The CRM web answers both agency hosts (`partner-dev.` and `portal.`) with a
   per-host public origin during the window, so the **cutover and its rollback change one DNS value** (the `portal.`
   CNAME) and no ECS deploy.

## Consequences

- A removed member or a disabled account loses the studio within 15 minutes (the exchanged token's lifetime), with no
  revocation list.
- The studio depends on the CRM web for sign-in; a CRM web outage on the agency host is a studio sign-in outage
  (pages already open keep working until their token needs renewing).
- The studio task can read the whole `crm/<env>/web` secret (IAM cannot scope a JSON key); accepted on Dev, a split
  secret is the option if wanted.
- Rolling back the DNS sends the agency host to the frozen Vercel copy (API-key sign-in only) for the window.
- Contracts: `tenant.membership.v1` 1.1 (activateInvitation), `crm.ops.v1` 1.3 (studio invitations).

## Alternatives considered

- **Merge the studio into the CRM web** now: the one-shell UI work is later (final design §4.3); separate images keep
  the rollback to Vercel trivially equivalent.
- **Make CIS verify partner tokens on every `/v1/*` route**: every route and middleware would change, and CIS would
  need the CRM's session; the exchange keeps `/v1/*` untouched.
- **Studio invitations in `crm.member_invitation`**: its role is NOT NULL, accept creates a CRM member, and its tenant
  must be a CRM agency (critic C6).
- **Flip one `WEB_PUBLIC_ORIGIN` at cutover**: needs a web and an API deploy in the cutover and in the rollback
  (job-gated) and breaks the other host meanwhile (critic C4).
