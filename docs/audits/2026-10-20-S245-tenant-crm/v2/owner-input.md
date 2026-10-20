# Owner input, 20/10/2026 (Nghiệp, S245) — verbatim intent, translated

## Tenant CRM (Jira PR-19, Linear AA-821)
Owner rejects "CRM as a module inside AA-CIS-App". Reasons given:
- Cost of the recommended design rose too much (Dev +$85–160/month; prod ~$500–925 at 10 agencies). Find the leanest design that still meets EVERY item of Ms. Thư's spec (docs/research/partner-crm-spec.md) — no MVP, complete product, but no bloat.
- Ms. Thư said the CRM is INTEGRATED INTO THE TENANT PORTAL. Evaluate the CRM together with the tenant portal app, not as part of CIS.
- The CIS admin UI and the tenant portal UI still link to each other — that is wrong. They are two separate apps for two different audiences (AA staff vs. partner agencies) and must be fully separated.
- Target shape: CRM as its own app (own code boundary / repo), sharing only infrastructure (acc2 VPC, ECS cluster, RDS instance, Cognito, API Gateway/VPC link, S3, Vercel team) and integrated into the tenant portal.
- Follow Ms. Thư's spec more closely.
- H1–H11 (questions for Ms. Thư) must each come with a PROPOSED ANSWER for approval, not open questions.

### Owner answers to D1–D24 (from docs/audits/2026-10-20-S245-tenant-crm/README.md §15)
D1 b (fourth app AA-CRM — but re-analysed per above: separate app, shared infra, integrated into the portal)
D2 có (yes) · D3 a (own lane in parallel from S246) · D4 a (agent team, ~6 issues/session) · D5 có (start external processes at W0)
D6 b (gmail.send + SES forwarding only, NO two-way Gmail / NO CASA)
D7 a (one KMS key per agency + per-customer DEK) · D8 có (reword F1 sentence, after H3)
D9 a (WhatsApp Embedded Signup, agency owns WABA, Cloud API direct) · D10 a (VN payment gateway after quote; manual meanwhile)
D11 b (Documenso Platform for e-sign) · D12 có (Bedrock acc3 us. only, ZDR models, AI off by default per tenant)
D13 không (prod is NOT a hard precondition of the pilot) · D13-date 30/11/2026 (go-live date)
D14 không (do NOT buy Vercel Pro now) · D15 không (do NOT send lawyer brief now)
D16 có (Linear project "Tenant CRM" + issues per wave) · D17 có (own ECS service from Dev)
D18 có (fix hard-coded mailto:admin@adventureasia.com CTA on /trip/[tourId]) · D19 a (Messenger + Instagram in W6)
D20 a (EN/VI UI with i18n frame) · D21 c (builder lives in the portal/CRM app, reusing TripPlanner map/route components by guarded byte-copy)
D22 b (CRM gets its own job runner copy, does not touch CIS shared/jobs) · D23 có (split conditions in ADR — now moot/adapted since it is its own app)
D24 có (insights: ≥3 agencies + k≥10 + per-tenant opt-in)

Tensions the redesign must handle explicitly (do not silently ignore):
- D13 không + go-live 30/11/2026 + D14 không (Vercel Hobby forbids commercial use) → what runs the pilot, on what, legally/ToS-safe, at what cost.
- D15 không (no lawyer now) vs. PDPL VN / GDPR / APP obligations → what is deferred, what blocks which agency country.
- D6 b removes CASA; D11 b Documenso; D22 b own runner.

## Self-improving writing system (docs/audits/2026-10-20-S245-writing-learning-loop/)
Owner approves ALL proposals D1–D16. Concern: the monthly cost (~$30–50/month Dev, cap $60, +17–21% per article for S1) looks too high. Wants concrete ways to cut or optimise cost while keeping the same safety (replay → golden → shadow → approve) and learning value.

## AA-779 (FAQ / People Also Ask)
Owner worries: "if we drop PAA, articles no longer match what real users search for." The checkpoint found both blog requests had NO PAA in keyword snapshot / SEO context. Need advice: why PAA was empty, how to make PAA (or an equivalent real-user-question source) reliably available, and a Done-when that keeps real-user questions central.

## Notifications
System notification emails must go to nghieppham@adventure.asia instead of pqnghiep1354@gmail.com.
