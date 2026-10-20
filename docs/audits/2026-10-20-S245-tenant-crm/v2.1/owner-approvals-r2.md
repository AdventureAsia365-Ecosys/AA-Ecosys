# Owner approvals, round 2 (Nghiệp, 20/10/2026, S245) — read from the approval pages' database

## Tenant CRM v2 (artifact KgdjgAVf77xCG4r4KunPsJ; questions in out/crm-questions.json)
All N1–N19 approved as recommended EXCEPT:
- N3 = b: the agency app (portal + CRM + traveller pages) runs as a Fargate container behind CloudFront from the start (+≈$8/month), not Lambda + Web Adapter.
- N4 = a approved but owner wants it explained further (prod cell for the pilot with real data). See also H1/H4 below: the pilot with real agencies waits; synthetic agencies first.
- N5 = a approved; owner asks "is that a new DB?" (explain: HTTP-only reads; the prod cell RDS is the only new DB, and only when real data arrives).
- N8 = b (Documenso Teams for pilot if Documenso agrees in writing) — owner wants it explained further; e-sign vendor/cost questions go to Ms. Thư.
- N10 = a (Haiku default) — owner asks what it is used for (drafting emails/proposals etc.).
Re-confirmations: D1 a, D2 a, D11 a, D16 a, D17 a, D21 a, D23 a (kept with the new meaning), and two CHANGES:
- D12 → change: "Should have both: CIS must still be able to monitor the CRM's LLM calls, and the CRM should have its own gateway." => CRM has its own LLM gateway/log (crm.llm_call), AND CIS observability (admin) can see CRM LLM calls/cost (e.g. a read-only feed/metrics endpoint or shared cost view), without DB grants across apps.
- D22 → change: "Own copy, but CIS should be able to monitor it." => CRM keeps its own job runner copy (crm.job), AND the CIS ops/job-runner admin can observe CRM jobs (read-only summary over HTTP).
Questions for Ms. Thư (answered by Nghiệp on her behalf for now):
- H1 = b: wait until all 23 modules are done before real agencies use it. Owner adds: 30/11/2026 was only his estimate; the goal is to have it RUNNING ON DEV AS EARLY AS POSSIBLE, then decide.
- H2 = d (wants to discuss): pricing — owner note: "use a subscription plan synced with the tenant portal plan, combining several of the options." Business decision for Ms. Thư.
- H3 a, H7 a, H8 a, H10 a, H11 a, H12 a: agreed as proposed.
- H4 = c with note: "use fake (synthetic) agencies to test first."
- H5, H6, H9 = c: business/legal items — Ms. Thư decides later.

## Owner direction for the next step
- Focus on TECHNICAL work. Technical issues in the design need a closer review.
- Business, legal and external-cost items (especially EXTERNAL APPS/VENDORS: Documenso/e-sign, Twilio, WhatsApp/Meta, Stripe, VN payment gateway, CASA/Google, Microsoft, insurer, lawyer) are NOT decided by engineering: list them for Ms. Thư to give her opinion.
- Run on Dev with synthetic agencies as early as possible; no prod cell until real agencies (after all 23 modules).

## Writing Memory v1 (artifact LAM1LXGEQq9nCiRSkJCUNm)
E1–E4 approved as recommended (monthly release train; targeted shadow 20 with T2/Facebook at 50; S1 rules only + pinned 2 examples for T2/T9; cap $25/month and $10 per R2). D1–D16 approved earlier.
