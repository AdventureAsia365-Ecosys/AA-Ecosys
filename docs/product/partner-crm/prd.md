---
id: APP-10-partner-crm
title: "PRD: Partner CRM (AA-Partner)"
description: "Product requirements and acceptance criteria of the free CRM for partner travel agencies in AA-Partner, summarised from the accepted final design and the S247 errata, with links to ADRs, contracts and the crm design ERD."
type: reference
status: draft
owner: nghiep
audience: [owner, engineer, pm, agent]
applies_to: [aa-partner, aa-booking-api, aa-cis-api]
last_reviewed: 2026-10-22
review_every_days: 30
related: [APP-10, APP-04-erd-design-crm, AA-821, AA-894, docs/research/partner-crm-spec.md]
linear: [AA-821, AA-928, AA-929, AA-930, AA-931, AA-932, AA-933, AA-934, AA-935, AA-936, AA-937, AA-938, AA-939,
  AA-940, AA-941, AA-942, AA-943, AA-944, AA-945, AA-946, AA-947, AA-948, AA-949, AA-950, AA-951, AA-952, AA-953,
  AA-954, AA-955, AA-956, AA-957, AA-958, AA-959, AA-960, AA-961, AA-962, AA-963, AA-964, AA-965, AA-966, AA-967,
  AA-968, AA-969, AA-970, AA-971, AA-972, AA-973, AA-974, AA-975, AA-976, AA-977, AA-978, AA-979, AA-980]
adrs:
  - docs/adr/0005a-b2b-resale-warn-and-vnd.md
  - docs/adr/0006b-partner-pool-and-mfa.md
  - docs/adr/0008a-crm-separate-app-exceptions.md
  - docs/adr/0010-aa-partner-app.md
contracts:
  - docs/contracts/booking.b2b.v1.openapi.yaml
  - docs/contracts/crm.ops.v9-does-not-exist.openapi.yaml
  - docs/contracts/tenant.membership.v1.openapi.yaml
  - docs/contracts/catalog.http.v1.openapi.yaml
erd:
  - docs/architecture/erd/design/crm.md
migrations: []
---

# PRD: Partner CRM (AA-Partner)

AA gives partner travel agencies a free CRM to run their own clients: inquiry → proposal → booking → payment → trip
→ follow-up, with AA's products bookable inside it. The agency is the data controller for its travellers; AA is the
processor. This page is the requirement summary and the acceptance list. The detail lives in the sources below and
is linked, not copied.

| Source | What it holds |
|---|---|
| [Spec (Ms. Thư)](../../research/partner-crm-spec.md) | The 23 modules (F1–F5, M1–M18) as the business asked for them |
| [Final design](../../audits/2026-10-21-S246-crm-design-v3/final/crm-design-final.md) (accepted S246) | Decisions D1–D8, scope, UX, data model, privacy, delivery plan, cost, risks |
| [Errata S247](../../audits/2026-10-21-S246-crm-design-v3/final/errata-s247-byo.md) | Integrations are bring-your-own; wins over the final design once ADR 0010 is accepted |
| [Design v3](../../audits/2026-10-21-S246-crm-design-v3/design-v3.md) and its lanes | Full column lists, wireframes, the 53 issue cards |
| [Design ERD `crm`](../../architecture/erd/design/crm.md) | The planned schema, compared with live by the drift check |

## Problem and goal

Partner agencies sell AA's tours but run their clients in spreadsheets, mailboxes and chat apps. Proposals,
payments and the hand-off to AA ops are manual, and AA cannot offer its supply to them in one place. Goal: one app,
AA-Partner, where an agency runs the whole trip and books AA products at its B2B price, without AA ever seeing the
agency's clients outside three narrow, logged paths.

## Users and hosts

| User | Where | Sign-in |
|---|---|---|
| Agency owner, agent, assistant | AA-Partner agency app (CRM + Content studio, one sidebar) | Partner pool, two-step sign-in required for owner and agent ([ADR 0006b](../../adr/0006b-partner-pool-and-mfa.md)) |
| Travellers and prospects | Client pages (forms, proposal, client portal) | Signed link; email code per person; never an AA account |
| AA staff | CIS admin (L1 console, insights), AA-Partner staff routes (ops release, support session) | WORKFORCE with MFA |

Hosts, roles and the permission matrix: final design §3.1 and §5.5.

## Scope

- **Build before any real agency (waves W0–W7):** all 23 spec modules plus the approved ideas, on Dev with synthetic
  agencies only ([final design §2.1](../../audits/2026-10-21-S246-crm-design-v3/final/crm-design-final.md#21-scope)).
- **Go-real (W8, AA-980):** prod placement, prod partner pool, WAF, vendor verifications of AA's own OAuth apps, DPA,
  public data page. Opens when Ms. Thư names the first real agency.
- **Later (no issues):** group departures, in-app insurance sales, Messenger/Instagram, BYOK, two-way mail sync,
  Zalo, tier billing, a VN payment gateway.
- **Not in scope:** post-trip rating form.

Module-to-screen-to-table traceability: final design §2.2. Ideas and client items (R, C): final design §2.3.

## Requirements

Each line summarises a module; the design section linked in the "Detail" column is the requirement text.

| Area | The CRM must | Detail |
|---|---|---|
| Trip pipeline (M1, M2, §4) | Turn an embedded form submission into an Inquiry card; move each trip through `inquiry` … `completed` / `lost` / `cancelled` with DB-enforced edges and the date rule; show one "waiting on" chip | Final design §0 items 3, §5.2, §5.4 |
| Proposal and AA supply (M3, M4, §9) | Build day-by-day proposals with options; show AA products with B2B price, sell, margin and availability; let the client keep or swap options on a phone page without an account; place one hold set per accepted version | Final design §0 items 4–5; [ADR 0005a](../../adr/0005a-b2b-resale-warn-and-vnd.md); contract `booking.b2b.v1` |
| Money (M6, M7, M13, M15) | Keep a bookings ledger with frozen FX per line, invoices and deposit links tied to the hold expiry, payments through the agency's own Stripe key, refunds from approved requests, expected and received commission | Final design §5.4; errata §1 (CRM-23) |
| Messages (M5, M9) | Send and receive mail from the agency's own mailbox (Gmail, Microsoft 365, SMTP) and SMS/WhatsApp through its own Twilio; hold sends when a connection is down | Errata §1–§3 |
| Client portal and agreements (M11, M12) | Give each traveller their own email-code sign-in; collect terms, waivers and signatures with an evidence trail | Final design §3.6 |
| Automation and AI (M10, M14) | Run workflow templates and tasks; draft replies with AI only through the PII filter, with AI off by default and a $2 budget per agency | Final design §5.5 (F3); [ADR 0008a](../../adr/0008a-crm-separate-app-exceptions.md) |
| Ops hand-off (M8) | Release the minimal traveller data AA ops need for a confirmed AA departure, log each view into the agency's audit, purge at trip end + 90 days | Final design §5.5 "M8 ops release" |
| Reports and insights (M16, M17) | Agency reports; AA insights only as aggregates with n ≥ 10 travellers and ≥ 3 agencies | Final design §5.5, DM-7 rows |
| Privacy foundation (F1–F5, M18) | Encrypt identity per agency, log every reveal, keep a pseudonymous profile for AI and insights, enforce tenancy in the DB, export and erase on the owner's request | Final design §5.5–§5.6; [data standards DM-6.8](../../architecture/data-standards/02-data-management.md) |
| Connections (BYO) | A Connections page with test button and health state per vendor account; AA holds no vendor master account for an agency | Errata §2; [ADR 0010](../../adr/0010-aa-partner-app.md) decision 9 |
| One app (portal merge) | Move the tenant portal (Content studio) into AA-Partner in stages without breaking it | Final design §4; contract `tenant.membership.v1` |
| AA access | L1 console without personal data (`crm.ops.v1`), L2 owner-granted support, L3 break-glass | Final design §5.5 "AA access, three layers"; contract `crm.ops.v1` |

## Constraints

- **Data:** schema `crm` only, owned by AA-Partner (`crm-NNN`), never joined with or copied to `booking.customers`
  or `tripplanner.customers`; Booking sees a B2B trip case with counts and age bands only (DM-6.8). Retention per the
  `crm.*` rows of DM-7.
- **Boundaries:** other apps over HTTP contracts only; no cross-schema grants; the isolation probe expects 42501
  for every AA app role on every `crm.*` object.
- **Delivery:** Dev only, synthetic agencies, vendors in test mode until W8; risky PRs get an independent review;
  at most one critical-path step per session ([final design §7.1](../../audits/2026-10-21-S246-crm-design-v3/final/crm-design-final.md#71-rules)).
- **Cost** *(est., AA AWS per month)*: Dev ≈ $13–22; 10 agencies ≈ $84–97; AA's vendor cost $0 (final design §8,
  errata).

## Delivery

Waves W0–W8, Lane B (Booking and CIS) and Lane P (portal), with milestones C-M1 "CRM runs on Dev", C-M2 "full
lifecycle with agency goods", C-M3 "AA supply in the CRM", M4 "23 modules on Dev" and M5 "Go-real":
[final design §7.2–§7.4](../../audits/2026-10-21-S246-crm-design-v3/final/crm-design-final.md#72-waves-and-issues).
Risks and the open points that still need an owner: final design §9.

## Acceptance criteria

Linear Done-when points to these IDs (see [the PRD rules](../README.md#acceptance-criteria-and-linear)). Each is
checked on Dev with synthetic agencies unless it says otherwise.

- **AC-1** (C-M1; AA-932…AA-936) A synthetic agency's owner signs in on the agency host; a public form submission
  becomes an Inquiry card within 1 minute; the F1 columns of that traveller hold ciphertext only; the CIS admin
  shows the `crm.job` rows.
- **AC-2** (AA-932, AA-937) `crm_app` reading `booking.*` and `cis_app`, `booking`, `tripplanner`, `aa_app_user`
  reading any `crm.*` object get SQLSTATE 42501 in the isolation probe; every NOLOGIN reader gets 42501 on
  `trip_traveler` and the vault tables.
- **AC-3** (AA-932, AA-933) A request to a non-partner host is refused (403) and a `cis-admin` or break-glass token
  on any `/crm/v1` route gets 403; a cross-tenant SELECT inside `tenant_tx()` returns 0 rows.
- **AC-4** (C-M2; AA-937…AA-946) One trip goes from Inquiry to Completed with agency suppliers only; the partner
  pool refuses an owner or agent without two-step sign-in; the field-filter test passes on every `/crm/v1` route.
- **AC-5** (AA-946, AA-969) An assistant never receives a margin field (B2B price, cost, margin, commission) from
  any route: a contract test over every route proves it.
- **AC-6** (C-M3; AA-947, AA-949, AA-950, AA-951) An AA product is quoted, held and confirmed from the interactive
  proposal; accepting after the hold expired returns 409 `hold_expired`; `booking.b2b.v1` responses never carry
  `supplier_net` or a traveller's personal data.
- **AC-7** (AA-938, AA-964) No LLM call leaves without the PII filter: the CI corpus of at least 200 EN/VI samples
  shows 0 leaks, and the filter fails closed when it cannot run.
- **AC-8** (AA-934, AA-940) Every reveal of an F1 field writes an `audit_event` in the same transaction, and the
  owner sees the last 12 months of the agency's audit, including AA ops views of an ops release.
- **AC-9** (AA-934, AA-962) A connected vendor credential is stored encrypted; no route returns `secret_enc` or a
  decrypted value (contract test); a revoked credential shows `disconnected` and holds the sends on that channel.
- **AC-10** (AA-967) An owner's erasure request runs DRY RUN counts, then the erasure, then a verify step with a
  receipt; signed agreements and accounting records are kept as the DM-7 rows say, and the receipt says so.
- **AC-11** (AA-894, AA-933 onwards) After each `crm` migration, the DB Schema Dump drift report shows the migrated
  tables in sync with the [design ERD](../../architecture/erd/design/crm.md); the design page is set to
  `enforce=true` once the first wave is in sync.
- **AC-12** (M4; AA-952…AA-971) All 23 modules run on Dev and the security review (AA-969) has no High finding.
- **AC-13** (M5; AA-980) Before the first real agency: prod placement decided, prod partner pool, WAF, AA's OAuth app
  verifications, DPA and public data page done, and the ops owner has signed off the real net rates.
