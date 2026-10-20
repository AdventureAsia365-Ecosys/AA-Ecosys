# CRM redesign: judge panel on Design A (one tenant app, ECS) vs Design B (serverless)

Date: 20/10/2026 (S245 r2). Read-only review. No repo, AWS, Vercel, Linear or Jira change; no paid API call.
The only network calls were public AWS price-list JSON files and public vendor/AWS documentation pages.

**Panel:** two lenses.
- **PO lens:** a product owner who must satisfy Ms. Thư's spec (`docs/research/partner-crm-spec.md`, the "spec").
- **CTO lens:** one engineer plus agents, on a tight budget.

**Read in full:**
- `.tmp-session/s245-r2/owner-input.md`;
- the spec;
- `out/crm-01-current-state.md` (the "scout");
- `out/crm-design-A-one-tenant-app.md` ("A");
- `out/crm-design-B-serverless.md` ("B").

**Snapshots verified:**

| Repo | Ref |
|---|---|
| AA-CIS-App | `origin/main` @ `b7e6da66`, read with `git show` |
| AA-CIS-Infra | `4824c81` |
| AA-Booking | `f4fb80d` |
| AA-TripPlanner-Web | `b79ec48` |
| root | `f8a9938` |

---

## 0. Verdict in 10 lines

1. **Scores are close** (§3): A = 21/30 on both lenses; B = 22/30 (PO) and 21/30 (CTO). Neither design can ship as written.
2. **Base = Design A.** It keeps D17 (own ECS service), the Booking bootstrap template, the in-process Booking runner copy (D22 b) and the Guardrails scrubber, which supports Vietnamese. That gives one runtime pattern that one engineer already runs.
3. **Graft from B (four things):**
   - the **CRM-only prod cell** for real traveller data, which replaces A's R1 "real PII on Dev" amendment;
   - **HTTP-only cross-app reads**, with no grants on other schemas;
   - **module 8 kept in the CRM** under an AA-ops key;
   - **portal hosting on Lambda + Lambda Web Adapter + CloudFront**, which replaces A's Amplify plan. Amplify is documented only "up through Next.js 15", and the portal runs Next 16.4.2.
4. **Both designs share wrong items** that the synthesis must fix:
   - "Reuse the shared WAF ACL" is not $0-and-done. The ACL geo-blocks every country except 10, and the stage association is gated off.
   - Documenso **Free** has no API, so it cannot run the Dev adapter tests.
   - Spec **module 5 is a Phase 1 module**, so it belongs in the 30/11 pilot scope. Both designs move it after go-live.
   - Event tracking lands too late to measure any success metric during the pilot.
5. **Synthesis cost:**
   - Dev ≈ **$11–13/month**.
   - Prod pilot at 10 agencies ≈ **$320/month** with Documenso Platform (D11 b), or ≈ **$110** if Documenso confirms that Teams is allowed for the pilot.
   - Documenso is ~78% of the 10-agency bill. It is the only big lever left, and it belongs to the owner.

---

## 1. What was verified (and how)

### 1.1 Code and Terraform claims (17 spot-checks; ✔ = matches the design text)

| # | Claim (where used) | Evidence | Result |
|---|---|---|---|
| V1 | Staff login has a "B2B Tenant login →" link (A L1, B S1) | `AA-CIS-App/frontend/app/login/LoginForm.tsx:10,159` | ✔ |
| V2 | Tenant login has a "← Staff login" link (A L2, B S2) | `portal/app/tenant-login/page.tsx:4,111-112` | ✔ (A cites 108-114 and B cites 110-112; both cover it) |
| V3 | 308 redirects on the admin host, required by a test (A L3, B S3) | `frontend/next.config.ts:4,23-25`; `tests/unit/test_aa885_portal_split.py:104-117` | ✔ |
| V4 | `/auth/verify-tenant` uses `verify_jwt`, not `verify_tenant_jwt`; one HS256 secret signs both token types | `api/main.py:326-335`; `api/routers/auth.py:34,40,76,86-87` | ✔ |
| V5 | CORS allow-list has no portal host | `api/main.py:162-173` | ✔ |
| V6 | Portal runs Next 16.4.2 (B's argument against Amplify) | `portal/package.json:15` | ✔ |
| V7 | Portal size: 100 files and ~13.6k lines (A) or ~20.7k lines (B) | `git ls-tree`: 101 files; 13,576 TS/TSX/CSS lines; 20,705 lines in all files including `package-lock.json` | ✔ (both right; they count different things) |
| V8 | Trip page served by admin, with mailto CTA and admin-host URL (D18) | `frontend/app/trip/[tourId]/page.tsx:146`; `api/routers/v1_trip_page.py:157` | ✔ |
| V9 | Portal BFF forwards any path | `portal/app/api/tenant/[...path]/route.ts:20-33` (no allow-list) | ✔ |
| V10 | `alert_email` default is `pqnghiep1354@gmail.com` | `infra/AA-CIS-Infra/accounts/aa365/variables.tf:152-156` | ✔ |
| V11 | LOGIN connection limits total 155 of 181 | `observability_ecosys.tf:52,59-72` (30+15+15+90+5) | ✔ |
| V12 | Booking task is 256/512, FARGATE base 1 + SPOT 3, `ignore_changes` | `booking.tf:285-286,392-400,435` | ✔ |
| V13 | Booking pool `max_size=5`; runner is 675 lines and runs in-process with release on shutdown | `AA-Booking/backend/app/db.py:65-72`; `wc -l backend/app/jobs/*.py` = 675; `jobs/worker.py:1-20`; `main.py:79-92` | ✔ |
| V14 | TripPlanner Lambdas reserve 15 + 5 concurrency (B's offset 30 → 22) | `tripplanner_variables.tf:69-79` | ✔ |
| V15 | One active SES receipt rule set per region | `e2e_mailbox.tf:14-17,203-207` | ✔ |
| V16 | Cognito `cis-portal` client exists with **fixed** callback URLs | `identity.tf:168-171`; `identity_variables.tf:163-168` | ✔ It also matters for previews (D-B4) |
| V17 | TP map stack: `mapbox-gl` 3.7.0, MapView 803 lines, imports `@/lib/{api,tileLoader,types,useTrip}` | `AA-TripPlanner-Web/frontend/package.json:14`; `components/MapView.tsx:4-17` | ✔ TP is on **Next 15.5.28** (`package.json:15`), the portal on 16. The byte-copied components must work across that gap (not in either design) |

**Wrong or incomplete infra claims found during verification:**

| # | What both designs assume | What the code says |
|---|---|---|
| V18 | "Associate the existing shared regional WAF ACL with the CRM stage, ~$0" (A §4.2, §8; B §8.2) | The ACL's rule 4 **blocks every country not in** `["US","GB","AU","SG","VN","IN","JP","TH","NZ","CA"]` (`modules/waf/variables.tf:20-25`, `modules/waf/main.tf:158-178`). The stage association is **off** because the CI role lacks `apigateway:SetWebACL` (`accounts/aa365/variables.tf:198-205`; `main.tf:272-277`). See defect X1 |
| V19 | B: "`envs/prod/` (0 bytes today)" | The directory **does not exist** (`infra/AA-CIS-Infra/envs/` holds only `dev`). Same conclusion, one more bootstrap step |
| V20 | Both: Booking `/booking/b2b/v1` with departures, allotments and holds | **Nothing exists yet.** `b2b` appears only as a pricing channel (`AA-Booking/backend/app/pricing/engine.py`; `CONTEXT.md:368`). The Booking-side W4 work is all new and sits on the 30/11 critical path |
| V21 | ADR numbers 0014/0015 | `docs/adr/` holds 0001–0008 only. Other documents refer to ADR 0009/0012 as planned, so check the numbering before allocating (minor) |

### 1.2 Prices (15 spot-checks, all accessed 20/10/2026)

AWS price-list JSON for us-west-1 (`https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/<code>/current/us-west-1/index.json`):

| Line | Price-list value | Used by | Result |
|---|---|---|---|
| Fargate x86 | $0.04656/vCPU-h, $0.00511/GB-h (pub. 2026-10-19) | A, B, scout | ✔ |
| Fargate ARM | $0.03725/vCPU-h, $0.00409/GB-h | A, B | ✔ |
| Fargate Spot discount | not in the price list | A (60–70%) | Estimate, correctly marked |
| Lambda ARM | $0.0000133334/GB-s, $0.20/M requests (pub. 2026-10-16) | B | ✔ |
| RDS PostgreSQL | t4g.micro $0.021/h single-AZ, $0.043/h Multi-AZ; t4g.small $0.043/$0.085; t4g.medium $0.085/$0.171 (pub. 2026-10-20) | A, B | ✔ |
| API Gateway REST | $3.50/M (first 333M); HTTP API $1.17/M | A, B | ✔ |
| WAF | $5.00 per web ACL-month, $1.00 per rule-month, $0.60/M requests | A, B | ✔ (a new ACL with 4 rules ≈ $9 + requests) |
| SES | send $0.0001/recipient; receive $0.0001/message + $0.00009/chunk | A, B | ✔ |
| Amplify Hosting | SSR $0.30/M requests + $0.20/GB-h; transfer $0.15/GB; build $0.01/min; **Amplify WAF $15/month** | A | Prices ✔; A does not count the WAF line |

Vendor and documentation pages:

| Line | Source | Used by | Result |
|---|---|---|---|
| KMS | $1/key-month; rotations add $1 for the first two only ("capped at the second rotation"); **keys scheduled for deletion are not charged**; 20k free requests ([aws.amazon.com/kms/pricing](https://aws.amazon.com/kms/pricing/)) | A, B | ✔ (B's lazy-create / delete-free lever is real) |
| Bedrock Guardrails | Sensitive-info (PII) filter "$0.10 per 1,000 text units", regex filters free, 1 unit ≤ 1,000 chars ([aws.amazon.com/bedrock/pricing](https://aws.amazon.com/bedrock/pricing/)) | A | ✔ |
| Guardrails Vietnamese | Sensitive-information filters list **"Vietnamese: Optimized and supported"** ([guardrails-supported-languages](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-supported-languages.html)) | A | ✔ |
| Claude Haiku 5.5 / Sonnet 5.5 | $0.10/$0.50 and $2/$10 per MTok, first-party list (claude-api skill, cached 2026-10-06; Haiku price applies to prompts ≤100K) | A, B | ✔ for the Anthropic list. **The Bedrock price is unverified**: the Bedrock pricing page shows no Anthropic figures. Both designs assume parity; keep it marked as an estimate |
| CloudFront flat-rate plans | **Free** $0: 1M requests, 100 GB, **WAF with 5 rules included**, always-on DDoS. **Pro** $15: 10M requests, 50 TB, 25 rules ([aws.amazon.com/cloudfront/pricing](https://aws.amazon.com/cloudfront/pricing/)) | B | ✔ B does not use the bundled WAF (see X1) |
| Amplify Next.js support | "versions up through Next.js 15"; compute SSR for "12 through 15" ([ssr-amplify-support](https://docs.aws.amazon.com/amplify/latest/userguide/ssr-amplify-support.html)) | A | **Fails A's plan**: the portal is Next 16.4.2 (V6) |
| Documenso | Free $0: 5 docs/month, **no API listed**. Individual $25: "API Access for Personal Use". Teams $40: 5 users, "API Access for Automation", "Embedded Signing", 1 team. Platform $250: unlimited, "Embedded Signing (Whitelabel)". **All paid plans are billed yearly** (Platform $3,000/year) ([documenso.com/pricing](https://documenso.com/pricing)) | A, B | **Wrong in both:** Dev on the Free plan cannot exercise the API (X2). Platform is a $3,000 annual commitment, which neither design says |

### 1.3 Arithmetic re-done

| Design | Line | Re-computed | Result |
|---|---|---|---|
| A | LLM per agency | 0.8×(2.4×0.10 + 0.36×0.50) + 0.2×(2.4×2 + 0.36×10) = 0.336 + 1.68 = **$2.02** | ✔ |
| A | Guardrails per agency | 1,800 units × $0.0001 = **$0.18** | ✔ |
| A | Dev Fargate | 0.25×0.03725×730 + 0.5×0.00409×730 = **$8.29** on-demand → $2.5–3.3 on Spot (estimate) | ✔ |
| A | Prod compute | 2 × (0.5×0.03725×730 + 1×0.00409×730) = **$33.2** | ✔ |
| B | LLM per agency | 0.9×0.42×1.1 + 0.1×8.4×1.1 = **$1.34** | ✔ |
| B | Pilot DB | t4g.micro 0.021×730 = $15.33 + 20 GB × $0.138 = $2.76 → **~$19** | ✔ |
| B | Prod totals | 10 agencies: 13 + 10–30 + 2 + 1 + 1.5 + 1.2 + 1.3 + 0 + 19 + 3 + 250 = **$302–322** | ✔ (50 and 200 also re-add) |

**A's and B's prod totals are not comparable as published.** A runs the pilot on Dev and excludes any prod database. B includes its own pilot database ($19 / $133 / $141). Normalised on the same basis, the two are within ~$10–30/month of each other at every scale. **Runtime choice is not where the money is**, and B says so itself (B §0.3).

---

## 2. Defects

### 2.1 Defects in BOTH designs

| # | Defect | Evidence | Fix in the synthesis |
|---|---|---|---|
| **X1** | "Reuse the shared WAF ACL, ~$0" is wrong on three counts. (a) Rule 4 geo-blocks every country outside 10: travellers in DE, FR, IT, NL, US-adjacent markets and others could not reach the intake form, and **webhook senders** outside the list (e.g. EU-hosted Documenso, Meta, Stripe egress) would be blocked. (b) The association needs `apigateway:SetWebACL` on the CI role, which it does not have. (c) In both designs, traveller traffic reaches `api-crm` **through a BFF**, so the per-IP rate rule sees the BFF egress IP. That is the same failure the module documents for NLB IPs (`modules/waf/main.tf:49-50`): either all travellers share one bucket or the rule protects nothing | V18 | Put protection at the **edge of the traveller host**: CloudFront flat-rate Free includes WAF with 5 rules ($0), so use rate, CommonRuleSet and bot rules there, with **no geo block**. On `api-crm`: no association during the pilot, or the shared ACL with a scope-down that exempts the CRM host from rule 4, after the CI grant. Webhooks are protected by signature checks + throttling. Add an in-app rate limit keyed on the client IP, which the BFF forwards in an HMAC-signed header |
| **X2** | "Documenso Free on Dev for the adapter tests" cannot work: the Free plan lists no API access | §1.2 Documenso | Run the AGPL **self-hosted Documenso container in CI / Dev** for adapter and contract tests ($0, no data leaves). Use the paid plan only from go-live |
| **X3** | **Module 5 (email inbox) is wrongly scheduled after go-live.** Spec §10 Phase 1 is "S8 4 + 5" (`partner-crm-spec.md:191`), and the pilot is "at the end of Phase 2" (`:196`). A (§13: W0–W5 + W8a) and B (§9.1: "Modules 5 and 9 … follow in W6–W8 … in the spec's own phase order") both claim the spec's pilot point while omitting module 5. Without it, agencies keep using Gmail, which breaks spec §2 ("faster than … Gmail") and module 1's "first reply under 2 hours" | spec:186-196 | Move module 5 (D6 b: SES forwarding in, `gmail.send`/Graph send out, threading, saved replies, notes) **before 30/11**: ≈4 issues from W6 into W3/W5. WhatsApp (module 9) stays in W6 (spec Phase 3), which also fits the Meta verification clock |
| **X4** | Event tracking (spec gap §11.7) sits in W7 in both designs, so no module success metric can be measured during the pilot (≥80% budget band, deposits paid within 48 h, emails per trip, upgrade picks ≥20%) | A §13 W7; B §14 W7 | One W3 issue: a `crm.metric_event` baseline (≈10 events). Full reports stay in W7 |
| **X5** | A shared CIS JWT secret and API-key tenant login remain until AA-813 lands, and both designs need AA-813 inside W1. That is 3 issues in the **CIS** repo on the CRM critical path | V4; scout §1 Cognito row | Keep, but fix B3 in the very first CIS PR (it is a 2-line change), so a staff token gets a 401, not a 500 |
| **X6** | Cognito clients have **fixed callback URLs** (V16). B's per-PR Lambda function URLs and A's per-PR Vercel previews cannot complete a Cognito login | `identity_variables.tf:163-168` | One fixed preview host (e.g. `portal-pr.lumiguides.it.com`) registered on the client. CI deploys the PR under test there (last writer wins). Smoke tests sign in with the `e2e-test-*` tenant user |
| **X7** | TripPlanner is on Next 15.5.28 and the portal on Next 16.4.2 (V17). "Byte-copy unchanged" (A §5.3) assumes the copied client components build unchanged under Next 16 | V17 | The manifest guard stays. Add a CI build of the copied files under the portal's Next version, and note the copy may need a thin wrapper (D21 c already allows adapters) |
| **X8** | The Booking B2B surface (departures, allotments, holds, quote, confirm) does not exist (V20). Both designs put ~6–7 Booking-repo issues on the 30/11 critical path (W4) without naming a Booking owner or lane | V20 | Name the Booking lane owner in W0. On-request mode ("hold → AA ops confirms in one working day", B H8) is the go-live fallback, so the pilot does not wait for allotments |
| **X9** | Spec §1 says AA product is "confirmed automatically". Both H8 answers make non-allotment tours "on request" without recording this as a spec deviation for Ms. Thư | spec:9 | Record it in the spec-deviation list next to module 5 / D6 b |

### 2.2 Defects only in Design A

| # | Defect | Evidence | Severity |
|---|---|---|---|
| A-1 | **The pilot host does not work as planned.** Amplify supports Next "up through 15", and the portal is 16.4.2. A's fallback (R2: Vercel Pro $20) contradicts D14 (no Pro). The D14 tension is therefore left unresolved | §1.2 Amplify; V6 | High |
| A-2 | **R1 puts real traveller PII on Dev.** That amends C7.1a ("Production personal data MUST NOT be copied to Dev", `03-scaling.md:364`) and the handbook's "Test data only" (`engineering-handbook.md:500`). The Dev master `aa_cis_admin` can still read `crm.*` (ADR 0008 `:175`). Only ciphertext, but schema and metadata are public by design | `03-scaling.md:364`; ADR 0008:168-175 | High (governance) |
| A-3 | **A breaks its own R1.** R1 allows real data "only inside `crm.*` vault ciphertext", yet module 8 (A §8) pushes traveller PII to **Booking's** receiver, and Booking runs only on Dev. So real PII lands in `booking.*` on Dev | A §8 row "Module 8", §12.1 | High |
| A-4 | Amplify host costs omit Amplify WAF ($15/month per the price list). The traveller host then has no edge WAF at all (X1) | §1.2 | Low |
| A-5 | The A prod totals at 50 and 200 agencies exclude a prod database (A §11.2 "Not included … AA-880"). They read lower than B's only for that reason | §1.3 | Low (presentation) |
| A-6 | H4 allows **EU agencies with real data** under standard SCCs and no counsel (A §12.3, H4). GDPR Art. 27 and the SCC annex are exactly what D15 defers. B's "non-EU, non-VN only" is the safer reading of D15 | A §12.3; B §9.2 | Medium |
| A-7 | Onboarding: A drops the Gmail import (spec gap §11.5 "import from Gmail / CSV") and replaces it with a CSV export from Gmail. B keeps an mbox upload plus a Gmail contacts import | A §14 last rows | Low |
| A-8 | One task role can decrypt the vault and also serves the internet-facing intake and webhooks. B's per-function least privilege (`crm-public` gets Encrypt only) is not possible with one ECS task role. A does not name this as a residual risk | B §5.2 | Medium |

### 2.3 Defects only in Design B

| # | Defect | Evidence | Severity |
|---|---|---|---|
| B-1 | **It overturns D17**, an owner answer given the same day ("D17 có, own ECS service from Dev"). The saving is ≈ $8/month on Dev and $30–80/month in prod. It adds a second backend runtime (Lambda + LWA), EventBridge Scheduler one-time schedules, async invoke, an SQS DLQ, a sweeper and per-stage reserved concurrency. That is a **new runner, not a copy** (D22 b), with more failure modes, for one engineer | B §7.1; owner-input:21 | High (CTO) |
| B-2 | **The prod cell depends on Dev.** It calls CIS Dev and Booking Dev and signs users in through `aa-external-dev`. C7.1b says "Dev MAY be stopped to save cost" (`03-scaling.md:365`), so the pilot's availability equals Dev's. Real AA holds would live in Booking Dev, which has no prod DR | B §9.1 "Other apps" row | Medium. Accept for ≤10 agencies, write it into the C7.2a exception, and add "do not stop Dev while the pilot runs" to the ops rules |
| B-3 | The **scrubber is weaker for Vietnamese**: Presidio + spaCy *English* plus a ~100-surname gazetteer. AWS documents Guardrails' sensitive-info filter as "Vietnamese: Optimized and supported" at $0.18/agency-month (§1.2). The Presidio image also enlarges the worker cold start | B §5.3 | Medium |
| B-4 | Per-PR Lambda function URLs cannot sign in through Cognito (X6). B presents them as the replacement for Vercel previews | B §7.2 | Medium |
| B-5 | Reserved concurrency `api` = 8 at 200 agencies. The portal SSR, BFF and react-query bursts reproduce TripPlanner's S237 503s at cap 5 (`tripplanner_variables.tf:66-68` comment). Dev and pilot scale are fine | V14 | Low |
| B-6 | N7 (Documenso Teams first) deviates from D11 b without written terms. Teams lists no white-label, so travellers may see Documenso branding. B marks it "unverified" but recommends it | §1.2 Documenso | Low (the owner decides) |
| B-7 | Several more pre-30/11 infra items, each new to the platform: the `envs/prod` root (V19), the C7.2d DB Migrate `environment` input ("To build", `03-scaling.md:374`), the portal-on-Lambda module and the prod Lambda stage. That raises W1/W5 risk | V19 | Medium |

---

## 3. Scores (1–5, 5 = best; for "delivery risk", 5 = lowest risk)

| Criterion | A, PO | A, CTO | B, PO | B, CTO | Why |
|---|---|---|---|---|---|
| Spec coverage | 4 | 4 | 4 | 4 | Both trace every module and section, but both move module 5 after go-live (X3) and leave event tracking late (X4). A matches the module 8 "sent to AA" wording, but on Dev (A-3). B keeps Gmail/mbox import |
| Cost, Dev + prod | 4 | 4 | 4 | 4 | Dev $10–12 vs $9–12. Normalised prod is equal within ~$30. A's host line is invalid (A-1); B's DB line is real. Documenso dominates both |
| Separation from CIS/admin | 4 | 4 | 5 | 5 | Both remove every link (V1–V3) and move the portal out of the CIS repo. B also has no cross-schema grants, staff views go through the API with a WORKFORCE token, and the cookie namespace is cleaned up |
| Ops simplicity | 4 | 4 | 3 | 2 | A = the Booking template (one ECS pattern) plus a second hosting platform (Amplify). B = 5 Lambdas, Scheduler, DLQ, sweeper, CloudFront and a second RDS |
| Security / compliance | 3 | 2 | 4 | 4 | A puts real PII on Dev (A-2, A-3), allows EU data without counsel (A-6) and has one decrypt-capable task role (A-8). B has the prod cell, per-function KMS and a stricter jurisdiction gate, but a weaker VN scrubber (B-3) and a prod cell that depends on Dev (B-2) |
| Delivery risk before 30/11 | 2 | 3 | 2 | 2 | Both need ~84–94 issues in 41 days plus AA-813, the Booking B2B work (V20) and external clocks. A's hosting answer is broken (A-1). B adds a new runtime and new prod infra (B-7) |
| **Total / 30** | **21** | **21** | **22** | **21** | |

**Reading the tie:**
- The PO prefers B's **data and compliance architecture**, which is what Ms. Thư's "AA never sees who the traveller is" needs.
- The CTO prefers A's **runtime**, which is what one engineer can operate.
- The synthesis takes each lens's winner. Neither design is accepted whole.

---

## 4. Synthesis (the design to take forward)

### 4.1 Shape

| Area | Choice | From | Why |
|---|---|---|---|
| Repo | One new public repo `AA-Partner` with `web/` (the portal moved from `AA-CIS-App/portal/` with history, CRM UI as a `/crm` section, traveller host) and `api/` (CRM backend). Add an import-boundary test: `api/` never imports `web/`, and `web/` reaches the API only over HTTP | B §3.1 naming and test; A §4.1 layout | Owner: the CRM is its own app, integrated into the portal, and has nothing in CIS. One repo means one CI, one branch protection, one OIDC role |
| Backend runtime | ECS service `aa-crm-dev-api`, **ARM64 0.25 vCPU / 0.5 GB**, Dev = FARGATE_SPOT only, in-process `crm.job` worker copied from Booking (675 lines), deploy gate copied from Booking | A §4.2, §9 | D17 and D22 b as approved. Same pattern as Booking. ≈ $2.5–3.3/month on Dev |
| Portal + traveller hosting (Dev and pilot prod) | Next 16 `output: "standalone"` on **Lambda + Lambda Web Adapter**, behind **CloudFront flat-rate Free**, which includes WAF with 5 rules and DDoS protection. Static assets go to S3. Retire the `aa-cis-portal` Vercel project. W0 spike: Next 16 Proxy, SSR and BFF on LWA. **Fallback (not Vercel Pro):** the same container as a small Fargate service behind the same CloudFront (+≈ $8/month) | B §7.2, §9.1; fallback is new | Solves D14 without Pro and without Amplify (A-1). One host for Dev and prod. Frees the Hobby 100-deploys/day cap |
| Previews | One fixed `portal-pr.` host registered on the Cognito client. CI deploys the PR under test there | new (X6) | Cognito callbacks are fixed URLs |
| Real data / pilot prod | **CRM-only prod cell** in a new `envs/prod/`: `aa-crm-prod-db` t4g.micro single-AZ (14-day PITR, deletion protection, cross-region snapshot copy, a restore drill before go-live) and service `aa-crm-prod-api` (ARM, on-demand, 1 task during the pilot). Write a C7.2a exception for ≤10 agencies, with the trigger "11th agency or AA-880 ready → move schema". **Drop A's R1** | B §9.1, N4 | C7.1a stays intact. ≈ $19 + $8.3/month |
| Cross-app reads | HTTP only: a CIS tenant-member feed + `catalog.v1` (cached in `crm.catalog_cache`), and Booking B2B over IAM/SigV4. **No grants from or to `crm.*`** | B §4 | Works the same for Dev and the prod cell. The isolation probe stays simple |
| Module 8 | Data stays in the CRM under an AA-ops CMK. AA ops read it from a Booking-admin page through `/crm/ops/v1` with a WORKFORCE token. Every read is audited to the agency. Purge at return date + 90 days with a receipt | B §5.4 (N5) | Fixes A-3. ADR 0014 must record this as the module 8 form of ADR 0008's "consented hand-off" (`0008:171-174`) |
| F3 scrubber | 3 passes: known values → regex → **Bedrock Guardrails sensitive-info filter** (ANONYMIZE), fail closed, EN/VI corpus gate | A §7 | Vietnamese is optimized (§1.2). ≈ $0.18/agency. W0 spike: Guardrails on acc2 vs acc3 |
| KMS | One key per agency (D7 a), created lazily at the first traveller. Offboarding uses `ScheduleKeyDeletion` (not billed while pending). Automatic rotation stays a security-review choice (A's R4; the rotation cap limits it to $3/key anyway) | B §5.2 + A §6.1 | Verified prices |
| Public-path least privilege | Accept a single task role for the pilot and record it as residual risk (A-8). Option before AA-880: a second ECS service from the same image for `/crm/public/*` and `/crm/hooks/*` with an **Encrypt/GenerateDataKey-only** role (+≈ $2.5 Dev Spot / $8.3 prod) | B §5.2 idea, ECS form | Keeps one runtime |
| WAF / abuse | X1 fix: edge WAF via the CloudFront plan (rate + CommonRuleSet, **no geo block**); no shared-ACL association on `api-crm` until the CI grant exists and a scope-down exempts the CRM host; in-app per-traveller rate limit using a signed forwarded IP; webhook signatures + idempotency | new | Verified ACL rules |
| AI | Haiku 5.5 default, Sonnet 5.5 for opt-in proposal prose only; acc3 satellite, `us.` profile, retention none; AI off per tenant (D12); per-tenant cap $2/month | A §7.3 + B §5.5 | Bedrock price parity stays marked as an estimate |
| E-sign (D11 b) | Dev and CI: self-hosted Documenso container ($0, X2). Prod: Platform from go-live per D11 b; flag that it is **$3,000 billed yearly**. Re-decision option: Teams ($480/year) for ≤5 pilot agencies **only with Documenso's written OK** on multi-agency use and acceptance of non-white-label signing | A R3 / B N7, corrected | Biggest line; the owner decides |
| Channels | Module 5 before go-live (X3). WhatsApp via Embedded Signup, agency-owned WABA (D9 a). BYO Twilio for SMS. Messenger and IG in W6 (D19 a) | A §8 / B §6 | Per the spec phases |
| Separation work | Union of A §3 and B §3.3: L1/S1, L2/S2, L3/S3 (delete + invert the guard test), L4/S9, L5/S4, L6–L7/S5 (trip page to the traveller host, CTA = agency intake, D18), P1–P3/S6, N1/S7, B2–B4/S8 + `/v1/brand-identity`, B7 BFF allow-list, C1–C3 (the portal owns its kit; drop the byte-equality test) | A §3, B §3.3 | All verified (V1–V9) |

### 4.2 Synthesis cost (per month)

| Item | Dev | Prod, 10 agencies | Prod, 50 | Prod, 200 |
|---|---|---|---|---|
| CRM API compute (ECS ARM) | 2.5–3.3 (Spot) | 8.3 (1 task, 0.25/0.5) | 33 (2 × 0.5/1 GB) | 66–100 |
| Portal Lambda + CloudFront (Free → Pro $15 above 1M requests) | ~0.5 | ~1.5 | ~8 | ~45 |
| Database | 0 (shared Dev; `crm_app` 5, offset booking 15 → 10) | 19 (t4g.micro cell) | 133 (cell → t4g.medium Multi-AZ, or move onto AA-880) | 141–216 |
| KMS (agency keys + AA-ops key) | 3–4 | 11 | 51 | 201 (+ rotation if chosen) |
| LLM (B's mix; worst case, AI on everywhere) | ≤2 (cap) | 13 | 67 | 268 |
| Guardrails, SES, S3, API GW, logs, secrets, ECR | ~4 | ~10 | ~30 | ~110 |
| Mapbox (shared free 50k loads) | 0 | 0 | 0 | ~70 (lever: static map on the traveller host) |
| Documenso Platform (D11 b) | 0 (self-host test container) | 250 | 250 | 250 |
| **Total (Platform)** | **≈ $11–13** | **≈ $313–320** | **≈ $570** | **≈ $1.15–1.26k** |
| Total if Teams is confirmed for the pilot | — | ≈ $103–110 | — | — |
| Previous design | $85–160 | $500–925 (no DB) | $1.6–2.0k | $4.7–5.2k |

All rows are estimates built on the verified unit prices in §1.2. Volume assumptions are those of research 04 §1, as used by A and B.

Optional extras:
- the public-path second service: +$2.5 Dev / +$8.3 prod;
- a portal Fargate fallback if the LWA spike fails: +$8.

### 4.3 The owner's tensions, answered by the synthesis

| Tension | Answer |
|---|---|
| D13 không + 30/11 | The pilot runs in the CRM-only prod cell (≈ $27/month for DB + API). No AA-880 dependency. Real traveller PII never touches Dev |
| D14 không (no Vercel Pro) | Portal and traveller host run on AWS (Lambda + CloudFront), so the Vercel Hobby clause no longer applies to the partner app. The Hobby exposure of the **other** Dev frontends is a separate platform decision (B N9); it is not settled here |
| D15 không (no lawyer) | Real data only for non-VN, non-EU agencies (B N8 / H4). VN and EU agencies get demo mode on synthetic data. Lawyer brief triggers: the first VN or EU agency with real data, the 6th agency or first paid plan, or 60 days after the first real traveller record (A §12.3 triggers) |
| D6 b / D11 b / D22 b | Built as answered. Module 5 forwarding counts as the spec's "two-way" inbox and is recorded as a deviation. Documenso per §4.1. The runner is the Booking copy, in-process |

### 4.4 H1–H11: merged proposed answers

Where the two designs differ, the stricter or more concrete answer was taken.

| H | Proposed answer | Source |
|---|---|---|
| H1 | Keep all 23 modules; drop only the 40-week schedule. The pilot opens 30/11/2026 with Phase 0–2 modules **including module 5 (email)**; Phase 3–4 ship during the pilot. Recorded deviations: email by forwarding + send-as (D6 b), and on-request confirmation for non-allotment tours (X9) | A/B + X3, X9 |
| H2 | Free for partners, no seat fee. Agencies pay their own WhatsApp (Meta), SMS (Twilio) and card fees (Stripe) through their own accounts. AI is included up to $2 of model use per agency-month. AA's cost is ≈ $11/agency/month at 50 agencies. Review at 50 agencies | B |
| H3 | "Only the CRM system can use your agency's key. Every use is logged and visible to you. AA staff cannot open traveller records. With your own key (BYOK) you can revoke access, and deleting the key makes the data unreadable." | B |
| H4 | 3–5 friendly agencies from Australia or another non-EU, non-VN country, named by Ms. Thư in W0, with a 30-minute interview each. VN and EU agencies join in demo mode until a lawyer's review | B (fixes A-6) |
| H5 | The AA entity that signs partner agreements today (Ms. Thư names it). DPA from the AA-886 template, no lawyer for the pilot (D15); the lawyer brief is prepared, not sent | A/B |
| H6 | AA's current trekking insurer; Ms. Thư names the contact in W0. Waivers are e-signed meanwhile and marked "insurer review pending" | A/B |
| H7 | Zalo is not in v1. Revisit when VN agencies are unblocked | A/B |
| H8 | AA ops keep departures and seats in Booking for fixed-date tours. Every other tour is "on request": the hold is confirmed by AA ops within one working day | B |
| H9 | Use the ADR 0005 B2B net list (15%) unchanged; the agency sets its own sell price | A/B |
| H10 | AA provides default EN/VI terms and waiver templates adapted from AA's current terms. Agencies may upload their own. The insurer reviews the waiver | A/B |
| H11 | Yes (D24): k ≥ 10, ≥ 3 agencies, opt-in per agency, default off | A/B |

### 4.5 New decisions the synthesis needs (for the approval page)

| # | Decision | Recommendation | Effect |
|---|---|---|---|
| S-1 | Portal and CRM hosting on Lambda + LWA + CloudFront (Dev and prod); retire Vercel `aa-cis-portal` | Yes | D14 holds. $0–2/month at pilot size |
| S-2 | CRM-only prod cell (t4g.micro) with a C7.2a exception for ≤10 agencies; no real PII on Dev | Yes | +$27/month. C7.1a intact |
| S-3 | Module 8 stays in the CRM under an AA-ops key (B N5) | Yes | No PII in Booking Dev |
| S-4 | Module 5 and an event-tracking baseline move before 30/11 | Yes | +≈5 issues before go-live |
| S-5 | Documenso: Platform at go-live (D11 b, $3,000/year), **or** Teams for the pilot with written vendor OK | Owner | −$210/month if Teams |
| S-6 | Optional second ECS service for public routes (Encrypt-only role) | Before AA-880, not for the pilot | +$8.3/month prod |

### 4.6 Waves (adjusted from A §13, with B's prod-cell work added)

| Wave | Change versus A |
|---|---|
| W0 | + LWA/Next 16 spike (replaces the Amplify spike), Guardrails spike, Documenso self-host test container, Booking-lane owner named (X8) |
| W1 | + portal Lambda/CloudFront module, fixed preview host, CIS tenant-member feed + `catalog.v1` endpoints (replace the catalog grants). B3 fix goes first |
| W3 | + module 5 (≈4 issues), event baseline (1) |
| W5 | + `envs/prod` root, prod cell, C7.2d DB Migrate `environment` input, restore drill (≈4) |

Total ≈ **95 issues to 30/11 (≈ 16 sessions)**, ≈ 118 in all. At ~6 issues/session that is ~2.7 CRM sessions/week from S246.

**This is the main risk.** If the lane slips, keep the scope and move the date (both designs agree). On-request supply (H8) keeps W4 off the Booking allotment build.

---

## 5. Notes outside the CRM, observed while verifying

- **Notifications request:** `var.alert_email` default (`accounts/aa365/variables.tf:152-156`) feeds SNS and Budgets (scout §6.7). Changing it to `nghieppham@adventure.asia` is a one-line Infra PR plus SNS subscription confirmation from the new mailbox. CRM alarms inherit it.
- **Vercel Hobby exposure** of the CIS and Booking admin frontends (B N9): out of scope here, but S-1 creates a reusable hosting module if the owner wants to converge.
