# ADR 0008 — Amendment: the partner CRM is a separate app; traveller OTP and an own LLM gateway as playbook exceptions

- **Status:** Proposed (22/10/2026, S247). Nghiệp accepts; until then ADR 0008 decision 8 applies unchanged.
- **Scope:** AA-Ecosys: the partner CRM (AA-821) in the new app AA-Partner ([ADR 0010](0010-aa-partner-app.md)),
  and every app that would read or write its data (AA-CIS-App, AA-Booking, AA-TripPlanner-Web, AA-CIS-Infra).
- **Amends:** [ADR 0008](0008-new-app-integration-and-data-platform-rules.md) decision 8 ("If built, it is a CIS
  module …", the hand-off sentence and the preconditions), and decision 3 steps 8 and 9 **for AA-Partner only**.
  Data standards DM-6.8 is rewritten to match in AA-929 (CRM-01b); until then this ADR wins (ADR 0008 decision 4,
  precedence).
- **Implements:** ADR 0008 decision 2, gate answer 3 (a new domain with its own lifecycle: the agency's own clients),
  and decision 3 step 1 (design + ADR).
- **Design and evidence:** final design
  [`docs/audits/2026-10-21-S246-crm-design-v3/final/crm-design-final.md`](../audits/2026-10-21-S246-crm-design-v3/final/crm-design-final.md)
  (decisions D1–D8, approved S246); design v3 §3.1, §4.3, §4.5, §4.7 and the contradiction list X2–X5 in
  [`lanes/data-privacy-integrations.md`](../audits/2026-10-21-S246-crm-design-v3/lanes/data-privacy-integrations.md);
  v2.2 base decisions S1–S7, A1, V1–V3
  ([`inputs/crm-v2.2-simplified.md`](../audits/2026-10-21-S246-crm-design-v3/inputs/crm-v2.2-simplified.md),
  approved as recommended, D8); owner round 2 D12 (own gateway, CIS still observes)
  ([`owner-approvals-r2.md`](../audits/2026-10-20-S245-tenant-crm/v2.1/owner-approvals-r2.md)).
- **Related Linear:** AA-821 (epic), AA-928 (this ADR), AA-929 (standards text), AA-932 (DB owner `crm`), AA-933
  (repo), AA-964/AA-965 (AI layer), AA-978 (membership feed), AA-804 (ADR 0009, AI platform).

## Context

ADR 0008 §8 was written before the CRM was designed. It said: research first; "if built, it is a CIS module with its
own `crm` schema"; "a hand-off to AA is a consented event after which Booking creates its own customer"; and it
listed the AA-813 membership view as a precondition before any CRM DSN. The playbook (decision 3) also says step 8
"no password, OTP or session tables" and step 9 "LLM calls through the Model Gateway into `shared.llm_call_log`".

The S245–S246 design (owner decisions; D1–D8 approved S246) changed four facts:

| Id | ADR 0008 text | Design decision |
|---|---|---|
| X2 | CRM is a CIS module | A separate app, AA-Partner (portal + CRM web + CRM API), ADR 0010 |
| X3 | Step 9: LLM calls into `shared.llm_call_log` | The CRM has its own gateway and ledger (`crm.llm_call`); CIS still observes CRM AI usage (owner D12) |
| X4 | Step 8: no OTP or session tables; ADR 0006 puts travellers in the EXTERNAL pool | Agency travellers sign in with a per-person email code and signed links owned by the CRM; they never get an AA Cognito account |
| X5 | Hand-off → Booking creates its own customer (DM-6.8) | Booking receives pax counts only; ops data stays in the CRM (M8) and is purged at trip end + 90 days |

The design marks X2–X5 as **blocking the first CRM migration** (design v3 §9.2), so they need an ADR before AA-932.

## Decisions

### 1. The partner CRM is a separate app, not a CIS module (X2)

- ADR 0008 §8's sentence "If built, it is a CIS module …" is replaced by: **the CRM is built in AA-Partner**
  (ADR 0010), with schema `crm`, owner role `crm_owner` (NOLOGIN), runtime `crm_app` (LOGIN, connection limit 6,
  pool 3), migration key `crm-NNN` and job table `crm.job` (ADR 0003a), applied only by DB Migrate from the byte copy
  in AA-CIS-Infra.
- Kept from §8 unchanged: the agency (tenant) is the **data controller** and AA the processor; the CRM never reads
  `booking.customers` or `tripplanner.customers`; no AA app reads `crm.*`.
  - Pointer (S247): who does what under that split, and the rule that the agency's vendors (Stripe, Twilio,
    mailbox, …) are its own accounts and its own processors, are in [ADR 0010](0010-aa-partner-app.md) decision 9
    (integrations are bring-your-own; shared responsibility).
- Tightened: **no cross-schema grants in either direction** (design N5). `crm_app` gets nothing outside `crm`; no
  other app role gets anything on `crm`. Everything between AA-Partner and the other apps goes over versioned HTTP
  contracts in `docs/contracts/` (ADR 0010 decision 4). The isolation probe expects 42501 for `cis_app`, `booking`,
  `tripplanner` and `aa_app_user` on every `crm.*` object (ADR 0008 step 12).
- AA support access is a NOLOGIN role inside the CRM (`crm_support_reader`, reached only by `SET LOCAL ROLE` during an
  owner-granted support window); there is no AA database login on `crm`.
- Since X1 is done (ADR 0008 follow-ups, S244), `aa_cis_admin` is break-glass only, so the "isolation is partial"
  caveat of §8 no longer applies to new data.

### 2. Preconditions before the CRM DSN and before real agencies

ADR 0008 §8 listed "this ADR, `owners.yaml`, the catalogue guard (X2), AA-813 membership + view, and N3" before any
CRM DSN. They become:

| Before | Preconditions |
|---|---|
| The first CRM DSN (AA-932, Dev, synthetic tenants only) | This amendment and ADR 0010 accepted; `owners.yaml` row for `crm` with the `crm_` kind prefix in `IDLE_EXEMPT_KINDS`; the catalogue guard (exists); the CRM row in the connection budget (Part C C2.2, AA-929) |
| The first real agency, and P2b (portal host + sign-in switch) | CIS membership table keyed by `(iss, sub)` + `catalog.v_tenant_member` + the `tenant.membership.v1` feed (AA-813 re-scoped, delivered by AA-978); partner pool (ADR 0006b) |

Reason: W1 (AA-932, about S249) needs the DSN seven sessions before the membership feed (AA-978, about S256). Until
then Dev holds only synthetic agencies (`tenant.is_synthetic = true`, enforced: a non-synthetic tenant on Dev → 422),
whose members are seeded in `crm.member`.

### 3. Hand-off to AA: Booking creates no customer for CRM trips (X5)

- ADR 0008 §8's "a hand-off to AA is a consented event after which Booking creates its own customer" does **not**
  apply to CRM trips. AA products sold by an agency reach Booking as a **B2B trip case** (`channel = 'b2b'`, the
  agency's `tenant_id` as party, `customer_id` NULL, allowed only for B2B by a CHECK) that carries pax counts, age
  bands and room configuration only (`booking.b2b.v1`, no names, contacts, DOB or passports).
- What AA ground operations need for a confirmed departure (names, pax, dietary and mobility flags, flights; a passport
  number only when the supplier requires it) stays in the CRM as an **ops release** under its own data key, read by AA
  ops in AA-Partner's staff page (spec module 8), every view logged in the agency's audit, purged at trip end + 90 days
  with a receipt.
- DM-6.8 is rewritten in this sense by AA-929.

### 4. Playbook step 8 exception: travellers sign in with CRM-owned codes and links (X4)

- **Scope of the exception:** the agency's **travellers** only. Agency people (owner, agent, assistant) still sign in
  through Cognito ([ADR 0006b](0006b-partner-pool-and-mfa.md)); their authorization is the CRM's own membership and
  role rows keyed by `(iss, sub)`, never token claims alone (step 8 unchanged for them).
- Travellers never get an account in an AA Cognito pool. The EXTERNAL pool is AA-controlled and shared with
  TripPlanner and Booking; putting an agency's clients in it would make AA a controller of those people and break the
  spec's principle "traveller data belongs to the agency".
- The CRM keeps, in schema `crm`: signed client-link tokens (forms, proposal, deposit) and per-person email-code
  challenges for the client portal and e-signing (spec module 11, R22). Rules:
  - link tokens are random with ≥ 128 bits of entropy; email codes are short numeric codes, single use, valid
    ≤ 10 minutes *(est.)*, with an attempt limit per challenge and rate limits per person and per IP; both are
    **stored hashed** (DM-6.9, tagged `conf:credential`);
  - a link token is exchanged for a host-only cookie and stripped from the URL, stays valid until it expires or is
    revoked, and can be re-issued by the agent;
  - OTP rows are kept 24 h; no passwords, ever.
- This is the only OTP / session store outside Booking's customer OTP (ADR 0001 decision 6) and Cognito.

### 5. Playbook step 9 exception: the CRM has its own LLM gateway and ledger (X3)

- CRM AI features call Amazon Bedrock through an **in-process gateway inside AA-Partner** in a fixed order: PII filter
  (F3: known values → placeholders, patterns, Bedrock Guardrails; fails closed) → budget (75 / 90 / 100 %) →
  `ai_enabled` → call → ledger row in **`crm.llm_call`** (stage, model, tokens, cost, status, scrub receipt; **no
  prompt or completion text**).
- The CRM does **not** write `shared.llm_call_log` and holds no grant on `shared.*` (decision 1; the INSERT exception
  of ADR 0008 decision 5 is not extended to `crm`). Reason: a cross-schema write from the CRM would break the
  "no grants in either direction" rule that the privacy promise to agencies rests on, and the CRM's stage
  configuration is per agency (budget, on/off), not CIS's.
- **CIS still observes CRM AI usage** (owner D12): `crm.ops.v1` serves daily LLM usage per stage and model, and the
  per-agency AI cost in the usage meters; the CIS admin shows it beside the CIS ledger.
- AI is AA's feature, not a bring-your-own integration: no agency-supplied LLM keys ([ADR 0010](0010-aa-partner-app.md)
  decision 9, S247).
- Providers: Bedrock only; OpenAI and Jev are never routed for CRM stages. If acc2 cannot run the models or Guardrails
  (it cannot run Bedrock LLMs today, through TrueIDC), the planned path is acc3 through a CRM-only role
  (`us.` inference profiles + `ApplyGuardrail` only), checked in AA-930.
- The rest of step 9 is unchanged: job table from the shared template with the `crm_` prefix, a retention row for every
  log, event or job table (`crm.llm_call`: 180 days + rollup).

### 6. Relation to ADR 0009 (AI platform, AA-804)

ADR 0009 is reserved and not written yet. ADR 0008 decision 5 leaves "the gateway contract" to it. So that the two do
not collide:

- ADR 0009 treats `crm.llm_call` as a **second ledger under the same column contract** as the shared ledger v2
  (`app = 'crm'`, status, attempt number, prompt hash, shadow / experiment flags, cost), and its AI Use Register lists
  the CRM stages with owner, budget and kill switch, fed from `crm.ops.v1`.
- ADR 0009 may share the gateway **code** (a vendored library, the pattern of `identity_verifier.py`), but not a
  database control plane: the CRM reads no `shared.llm_*` table. CRM stage settings live in `crm`.
- If ADR 0009 chooses a different shape for the CRM (for example a ledger service over HTTP), it amends this decision
  by name; it does not silently override it.

## Consequences

- **Positive:**
  - the first CRM migration is unblocked with a written boundary: one schema, no grants either way, HTTP contracts;
  - the privacy promise to agencies is checkable (isolation probe, contract CI, no AA account for travellers);
  - CIS keeps its cost view of CRM AI without a write path into `shared`.
- **Negative / cost:**
  - a second ledger to keep in step with the shared one (ADR 0009 has to name both);
  - one more OTP / link implementation to secure and test (rate limits, hashing, expiry) instead of reusing Cognito;
  - more HTTP contracts to version than a CIS module would need.

## Alternatives considered

- **CIS module with its own ECS service** (S245 panel option, ADR 0008 §8 as written). Rejected by the owner in S245
  round 2: the CRM would share the CIS repo, deploy guard (DM-11.4 blocks CIS deploys while `shared.job` is busy) and
  the CIS task role's secret access, and the tenant portal still had to leave CIS.
- **Travellers in the EXTERNAL pool.** Rejected: AA would control agency clients' identities (controller separation,
  X4), and one managed-login session covers every EXTERNAL client.
- **CRM writes `shared.llm_call_log`.** Rejected: needs a cross-schema INSERT grant from the CRM, and CIS would hold
  rows about agency AI use that agencies cannot see or delete.

## Follow-ups

- AA-929: DM-6.8 and DM-6.1 classes, DM-7 rows, C2.2 row (`crm_app` 6 / pool 3).
- AA-932: `owners.yaml`, roles bootstrap, `crm-001`, isolation probe rows.
- AA-978: CIS membership + `catalog.v_tenant_member` + `tenant.membership.v1` (AA-813 re-scoped).
- AA-804: ADR 0009 cites decision 6.
- On acceptance: status line here and in the index; pointer line in ADR 0008 stays.
