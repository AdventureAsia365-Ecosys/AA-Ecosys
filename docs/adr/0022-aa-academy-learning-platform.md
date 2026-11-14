# ADR 0022 — AA Academy: courses and learner records in CIS, one academy host on the CRM web, a learning route class

- **Status:** **Accepted** (tech lead, S279, 13/11/2026: decisions D1-D16 of the AA Academy research, AA-1098, and
  decision D17 on the S279 decision page). This ADR records the cross-repo part; the build is AA-1105 (S280).
- **Amends:** [ADR 0006b](0006b-partner-pool-and-mfa.md) decision 6 (a new WORKFORCE app client and a new route class
  in its table), under [ADR 0006](0006-ecosystem-identity.md) decision 8 rule 6 (one route class, one verifier).
- **Respects, unchanged:** [ADR 0002](0002-only-cis-writes-content.md) (CIS writes content; the courses are files in
  the root repo, published by the Docs sync), [ADR 0008](0008-new-app-integration-and-data-platform-rules.md) and
  [0008a](0008a-crm-separate-app-exceptions.md) (the CRM holds no grant on another schema and calls CIS over HTTP),
  [ADR 0016](0016-one-design-system-guarded-kit-copies.md) (the academy pages use the kit; kit core changes start in
  CIS), data standards DM-7.1 (retention rows before the migration copy).
- **Sources:** [research](../research/lms/README.md) §4.3, §5.4 (with its Note S280), §6.4, §7.2, §7.4 and §9;
  design ERD [learn.md](../architecture/erd/design/learn.md); contract
  [learn.http.v1](../contracts/learn.http.v1.openapi.yaml); course format [GUIDE-13](../learn/README.md).

## Context

The research (AA-1098) proposed a learning site built into the running stack: courses as Markdown and YAML in
`docs/learn/`, published by the Docs sync as a learn bundle; a learning API and a `learn` schema in CIS; a staff UI at
`/admin/learn` in the CIS admin and an agency UI in the CRM web. The tech lead accepted D1-D16 and added D17: one
learner front door for every audience, on its own host, served by the CRM web, so staff and (later) agencies share one
UI and the CIS admin stays an operator console. Part 1 (AA-1104, root #775) shipped the course format and the bundle.

Three things cross repos and need a record: who owns the learner data, how the academy host signs staff in without
mixing route classes, and where the bytes of videos live.

## Decision

1. **Courses are files, learner records are CIS data (D1, D3).** Paths, modules, lessons and quiz items stay in the
   root repo and reach CIS only as the learn bundle under the docs reader prefix (manifest format 1). Learner records
   live in a new schema `learn`, owned by AA-CIS-App in the CIS migration key space (`cis_owner` / `cis_app`).
   `aa_app_user` holds nothing on it until the agency academy (P7); no other app reads it. Every learner-data table
   carries `tenant_id` under the CIS row-level security template now, so P7 adds no table rewrite.
2. **One academy host, served by the CRM web (D17).** `academy.<env domain>` (Dev: `academy.lumiguides.it.com`) is an
   alias on the existing agency CloudFront distribution, routed by the ALB to the CRM web. The host serves only the
   academy pages, its sign-in and the public verify page; agency and staff-console routes answer 404 there, and the
   academy routes answer 404 on the other CRM hosts. Its session is its own (own cookies, own seal key), never the
   agency or the staff-console session.
3. **A new WORKFORCE app client `academy-web` and a new CIS route class `/learn/v1`.** The client is confidential,
   authorization code with PKCE, callback on the academy host. `/learn/v1/*` accepts only WORKFORCE × {`academy-web`},
   verified by its own module (like `partner_identity.py`), and that client is accepted nowhere else; it is never added
   to the CIS staff issuers. Neither `crm-staff` (its callback signs out anyone without a CRM ops or support group) nor
   `cis-admin` (another host, another route class) is reused. The learner is the active CIS staff directory row matched
   on the verified `(iss, sub)`, any role; anyone else gets 403 `not_a_learner`. Partner tokens get 403 until P7 (D6).
   `/learn/public/v1/certificates/{code}` is a public, rate-limited verify route.
4. **The CIS admin links to the academy and keeps the team view.** An "Academy" sidebar link to the academy host and a
   Platform › Academy page (capability `learn.admin`): team progress, content review items, certificate revoke. There
   is no `/admin/learn` reader.
5. **Videos live under their own private prefix (D8).** `<bronze bucket>/learn-media/`, not under the docs reader
   prefix (the Docs sync owns that prefix and deletes what it did not upload). The CIS task role may only read there;
   the learning API presigns a GET whose lifetime is a setting. A lesson names its video in the course file (`video`
   field, an additive field of manifest format 1).
6. **Every threshold is a setting (§7.4, D7).** Pass marks, retake delay, items per attempt, recertification period
   and paths, video URL lifetime, learner retention and review limits are `learn.*` keys of the CIS settings registry,
   each with an EN and VI operator guide.
7. **Retention (D11).** Learner data is kept while the account is active plus 365 days, then deleted by the CIS job
   `learn_retention`, whose first Dev run is a DRY RUN (DM-7.2).

## Consequences

- AA-CIS-Infra adds `learn` to the CIS entry of `db/owners.yaml` and its mirrors, the `academy-web` client, the
  academy host alias and ALB rule, a CIS API Gateway resource `learn/{learn_proxy+}`, the CRM web task settings and
  the read-only grant on `learn-media/`, before the CIS migration copy.
- AA-CIS-App ships the `learn` migration, the learning API, the jobs and the admin page; AA-Partner ships the academy
  host pages and their BFF. Each slice is its own PR, in the MIG-4 order (migration, copy, apply, schema dump, code).
- Agencies (P7) need a partner sign-in on the academy host and the `aa_app_user` grants; both are follow-ups with their
  own risky-change review.
- A new route class is a new authentication surface: negative tests per route group (a `cis-admin`, `crm-staff` or
  partner token on `/learn/v1` is refused) are part of the build.
