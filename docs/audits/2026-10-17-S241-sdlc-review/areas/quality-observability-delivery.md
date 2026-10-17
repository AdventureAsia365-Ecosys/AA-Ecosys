# Area 5 — Testing, quality gates, observability, incident & product delivery process

Read-only, 17/10/2026.

## Current state (observed)

- **Testing / CI**
  - AA-CIS-App: 354 unit files / ~4,267 test functions, 58 integration files / ~439, 1 acp file / 14 (grep `def test_`). ci.yml: flake8 (~20 rules ignored), pip-audit `|| true` (~L50), unit `--cov-fail-under=30`, integration on postgres:15 + redis, Docker build + Trivy `exit-code: "0"` + syft SBOM. Frontend: ESLint only, `continue-on-error: true` ("74 pre-existing errors", AA-601); no tsc, no `next build`, no FE unit tests. 10 test files at tests/ root (e.g. tests/test_sentry.py) not in any CI path. Branch protection: 5 required checks, 0 reviews, enforce_admins=false.
  - AA-Booking: 52 test files / ~671 tests; coverage floor 90%; pip-audit fails build; gitleaks full history; integration fails on skip; Docker health-contract check; FE build job (eslint + tsc + next build) not required; 0 FE tests.
  - AA-TripPlanner-Web: 18 backend + 5 frontend test files; CI pytest, lint, typecheck, `npm test`, build; no coverage floor, dependency audit or secret scan; deploy-lambdas.yml `update-function-code --publish` then only `lambda wait function-updated`.
  - AA-CIS-Infra: plan/apply, migration-copy-guard (nightly), gitleaks secret-scan, DB Migrate with busy-job guard; branch protection 403.
- **UI smoke**: Playwright 3 specs (~12 tests) at apps/AA-CIS-App/tests/e2e/smoke; runs on `deployment_status` for Vercel Preview only; not required; 1 of last 100 runs actually ran. No Playwright for Booking staff UI or TP. k6 scripts in tests/load last changed 2026-09-11, not in CI.
- **LLM eval**: eval-regression.yml workflow_dispatch only, `s1_old` only, last and only run 2026-08-01; services/eval/baselines/itinerary_compression_baseline.json missing; `_detect_itinerary_regression` returns False when baseline None (regression.py:134-142).
- **Deploy gates**: CIS deploy-dev pre-deploy job guard + post-deploy smoke (health, admin endpoints, worker kinds = registered kinds); Booking smoke /booking/health + /health/ready with git_sha. All 3 ECS services circuit breaker enable+rollback, desiredCount 1.
- **Observability**: 47 CloudWatch alarms (Booking 5xx/ALB/CPU/job; CIS RDS ×11, job-queue, ledger-write-failed, ACP, running-task; TP Lambda errors/throttles ×4; SES bounce/complaint). All notify SNS aa-cis-dev-acp-alerts (only `email` subscription); most without OKActions. No 5xx/latency alarm on CIS API GW 4ylo382khg. No Synthetics canaries, no Route53 health checks. One dashboard `aa-cis-dev-pipeline`. Log retention 14 days (WAF 30, flow logs 7). CIS logs: structlog default console renderer (130 files import structlog; no structlog.configure/JSONRenderer outside tests); uvicorn access plain text, no request id; Booking logging.basicConfig text (main.py:47).
- **Sentry**: code exists (api/core/sentry.py, traces_sample_rate 0.1; frontend sentry.*.config.ts) but secret aa-cis/dev/sentry-dsn-api does not exist (ResourceNotFoundException); /ecs/aa-cis-dev logs "Sentry DSN not found — error tracking disabled". Booking/TP have no Sentry/OTel. Tracing parked (AA-842, backlog row 85). API GW stage dev tracingEnabled=False, execution logging INFO.
- **Backups**: aa-cis-dev-db retention 7, deletion protection, single-AZ, encrypted; 4 manual snapshots; no AWS Backup plans; restore drill "never" (03-scaling.md:336); real-data pg_dumps docs/backups/2026-09-16 (11 MB, gitignored) on laptop.
- **SLOs**: 03-scaling.md C1.2 only Dev DB-latency SLIs; no HTTP availability/error-rate SLO, no error budget.
- **Incidents**: no incident/on-call/postmortem doc; apps/AA-CIS-App/docs/CIS_Runbook_v1.md (20/04/2026) names account 867490540162 (acc1, infra destroyed); apps/AA-CIS-App/docs/runbooks only clean-rerun.
- **Delivery**: skill/aa-ship DoD = merge + CI + rollout COMPLETED + live curl/shape + UI verify + evidence comment; 10 ecosystem ADRs + index; CONTEXT.md in all 4 repos (1275/454/348/286 lines); 63 session logs; living backlog; 143-line lessons log; implementation notes (CIS 417, Booking 16, root 4); Linear 4 projects, no target dates/milestones; Jira drafts approved first.
- **Releases**: 0 releases/tags in 5 repos; GitHub envs "prod"/"staging" in CIS-App and Infra empty or unprotected.
- **B2B readiness**: no status page, SLA, support channel, changelog, privacy policy page (TP frontend/app has no privacy/terms/legal route), DPA template; docs/legal only tenant-terms-ai-clause-draft.md ("DRAFT … NOT APPROVED"); DM-6.8 "A DPA template is required before the first tenant"; DM-6.4 "No automated PII check exists or is on the roadmap".
- INFERENCE: Vercel team on Hobby (non-commercial use per Vercel terms).

## Strengths

- Rigorous, evidence-based Definition of Done (skill/aa-ship).
- Deploy safety above average for solo dev (busy-job guard, post-deploy smoke with git_sha and worker caps, circuit breaker rollback).
- AA-Booking CI as model (90% floor, failing pip-audit, gitleaks history, no-skip integration, Docker health contract, SBOM).
- Large backend suites (CIS ~4.3k unit, ~440 integration on real PG15 + Redis); versioned event contracts tested on both sides (Booking test_inquiry_contract.py, TP tests/contracts).
- Broad alarms for Dev (47; RDS health, per-role connection %, queue age, overdue jobs, ledger failures, SES reputation, Lambda errors, NAT; many in Terraform, 03-scaling C4.1a).
- Strong architecture governance (ADRs + amendment convention, CONTEXT.md, data standards with RPO/RTO DM-9.6, PII tagging DM-6.1, retention DM-7, capacity review C8b).
- Working knowledge loop (lessons log, implementation notes, session logs + living backlog, Jira draft-then-approve).
- Runtime LLM cost/quality records (llm_call_log; gateway enforced by tests/unit/test_aa685_no_raw_model_calls.py; Jev; grounding-score alarm).

## Gaps

### Q1 — Production errors invisible: Sentry disabled live, Booking/TP without error tracker, no CIS API 5xx/latency alarm — CRITICAL, S, automatable
- Evidence: sentry.py `_get_dsn` reads aa-cis/dev/sentry-dsn-api → ResourceNotFoundException; log "Sentry DSN not found — error tracking disabled"; Booking/TP requirements/package.json without sentry/otel; aa-booking-dev-api-5xx exists but nothing on CIS API GW (5XXError/Latency); no p95 latency alarm on any app.
- Risk: tenant /v1 failure found only via complaint; 14-day retention may erase evidence.
- Recommendation: create DSN secret (Sentry free tier) or CloudWatch Application Signals; error tracking in Booking (FastAPI) and TP (Lambda + Next.js) with release = git SHA; Terraform CIS API GW 5XXError-rate, IntegrationLatency p95, ALB TargetResponseTime alarms; CI guard failing when init_sentry finds no DSN while ENVIRONMENT != test.
- Standards: NIST SSDF RV.1; Google SRE four golden signals; ISO 27001 A.8.16.

### Q2 — Backups never restore-tested; single-AZ same-region only; real-data dumps on laptop — CRITICAL, M, automatable
- Evidence: retention 7, MultiAZ False; backup plans empty; 03-scaling.md:336 "Restore drill | never", :338 laptop dumps; 11 MB (shared, tripplanner …); DM-9.3/9.6 "to build".
- Risk: one shared RDS for 3 apps (CIS content, Booking PII, TP inquiries); unknown RTO; no proven recovery from bad migration/delete; unencrypted PII on laptop; customers/DPAs ask for both.
- Recommendation: X10 drill now (PITR → new instance → per-app smoke queries → record RTO in docs/audits → delete; script as quarterly workflow_dispatch); dumps to SSE-KMS private S3 then delete locally; before prod Multi-AZ, 14-day PITR, AWS Backup plan with cross-region copy (DM-9.6).
- Standards: ISO 27001 A.8.13; SOC 2 A1.2/A1.3; NIST CSF RC.RP.

### Q3 — No external uptime/synthetic monitoring; email-only alerting; no status page — HIGH, S, automatable
- Evidence: synthetics describe-canaries none; route53 list-health-checks none; SNS one email subscription; OKActions mostly empty; Vercel frontends unmonitored; no status page.
- Risk: DNS/Vercel/API GW/cert outage or scaled-to-0 service unnoticed; alarm mails drown; customers can't check status.
- Recommendation: CloudWatch Synthetics or free external checker (Better Stack/UptimeRobot) on 5 URLs (CIS /health, a /v1 tenant route, Booking /booking/health/ready, TP home + browse API, admin login); route alarms to phone push (SNS → Slack/Zalo/PagerDuty-free/ntfy) with OK actions; free hosted status page.
- Standards: Google SRE black-box monitoring; SOC 2 CC7.2; DORA MTTR.

### Q4 — No incident-management process; runbooks stale or missing — HIGH, S, not automatable
- Evidence: no incident/on-call/severity/postmortem doc anywhere; CIS_Runbook_v1.md "Last Updated 20/04/2026 … Account: 867490540162"; runbooks only clean-rerun.md; aa-ship has no rollback section; backlog §1 secrets leak with rotation deferred and no incident record.
- Risk: improvisation under stress; stale runbook sends commands to wrong account (AA-517 already showed 2 wrong-account writes); repeat failures.
- Recommendation: docs/ops/incident-response.md (SEV1–3; who/how notified incl. Ms. Thư and tenant contact; first 15 min: status, rollback via previous ECS task def or Vercel promote-previous, status page; comms templates; blameless postmortem template in docs/incidents/); retire/rewrite CIS_Runbook_v1 for acc2; per-app rollback + restore-one-schema runbooks (DM-9.4); secret exposure = incident with record.
- Standards: NIST SP 800-61r3; ISO 27001 A.5.24–A.5.27; SOC 2 CC7.3–CC7.5.

### Q5 — LLM eval regression stale and toothless; no offline eval for tenant T-series — HIGH, M, automatable
- Evidence: eval-regression.yml dispatch only, 1 run ever (2026-08-01, total_count 1), `s1_old` only; baseline file missing → regression.py:139-142 returns False; no eval for T2 rewrite / T9 social although writers/prompts changed S230–S240.
- Risk: prompt/model/route changes (llm_role_config flips, catalog swaps) silently degrade tenant content quality/fidelity/authenticity; found by Ms. Thư or tenants.
- Recommendation: golden set ~20–30 per tenant-facing stage (T2, T9, authenticity filter) with expected properties (no invented facts, no testimonials, CTA rules, length); run via LLMClient (stage=adhoc_eval, cost logged) on PRs touching prompts/catalog/role config + weekly, cost-capped (~3 tours' worth); committed baselines; fail on regression.
- Standards: NIST AI RMF MEASURE 2.x; ISO/IEC 42001 8.x; eval-driven development.

### Q6 — Frontend quality gates weak — HIGH, M, automatable
- Evidence: CIS frontend-lint continue-on-error, no tsc/`next build`; 5 required checks all backend; ui-smoke only on Preview deployment_status (1/100 non-skipped), not required; Booking FE 0 tests, build job not required; TP no Playwright.
- Risk: UI regressions in tenant portal, B2C trip planner, staff booking admin (already happened: AA-834 flaky smoke, AA-836 portal 390 px).
- Recommendation: required `tsc --noEmit` + `next build` in CIS CI; burn down 74 lint errors (AA-601) and remove continue-on-error; UI smoke required (CI-created preview for frontend/**); 3–5 critical-journey Playwright tests per app (TP browse→plan→inquiry; Booking inquiry→trip case); same smoke after production promote.
- Standards: Scorecard CI-Tests; DORA CFR; ISO 25010.

### Q7 — No versioned releases, changelog or release notes; deploy = every push to main — HIGH, S, automatable
- Evidence: releases 0, tags 0 in 5 repos; Linear 4 projects targetDate null, no milestones; deploy-dev on push main; CIS-App prod env only branch_policy, Infra prod none.
- Risk: can't tell tenants what changed/when, roll back to a known version, or map bug reports to builds; once prod exists every merge is a production change without gate.
- Recommendation: Conventional Commits (already ~followed) + release-please/semantic-release per repo (SemVer tags, Releases, CHANGELOG.md); prod deploys tag-triggered behind protected `prod` env with required reviewer = Nghiệp; tenant release notes from CHANGELOG; Linear milestones mapped to releases.
- Standards: SLSA Build L2; NIST SSDF PS.2/PS.3; ITIL release management.

### Q8 — B2B/B2C commercial-readiness artifacts missing — HIGH, M, not automatable
- Evidence: docs/legal only tenant-terms-ai-clause-draft.md ("DRAFT … NOT APPROVED", AA-820); DM-6.8 DPA required before first tenant; ADR 0001:100 Jev needs DPA/ZDR; TP frontend/app no privacy/terms/cookie route while inquiry outbox carries name/email/phone + consent (CONTEXT.md:320); no SLA/support/ticketing doc; INFERENCE Hobby non-commercial.
- Risk: PII without privacy notice risks Vietnam PDPD Decree 13/2023 and GDPR; tenants won't sign without DPA/SLA/support; Hobby terms may forbid commercial launch.
- Recommendation: packet for Ms. Thư and counsel (calm proposal): privacy policy + cookie notice on TP and portal; DPA template (processor terms, sub-processors AWS, Bedrock/Anthropic, OpenAI, Jev/TypeSafe, Vercel, Sentry); lean SLA (e.g. 99.5% monthly, response times, maintenance windows, credits); support@ → ticket tool or Linear intake; Vercel Pro before charging.
- Standards: GDPR Art. 13/28; Vietnam Decree 13/2023/ND-CP; SOC 2 CC2.3; ISO 27001 A.5.34.

### Q9 — Unstructured logs without request/correlation ID; 14-day retention; no tracing — MEDIUM, M, automatable
- Evidence: no structlog.configure/JSONRenderer outside tests; live lines like `2026-10-17 00:19:15 [info     ] ops_metrics_sampled …`; uvicorn `INFO: 10.2.2.248 - "GET /health" 200`; Booking basicConfig text (main.py:47); no request_id/traceparent middleware (api/middleware has rate_limit, sentry_context); retention 14 days; API GW tracing off; AA-842 parked.
- Risk: can't follow TP → outbox → Booking or tenant → CIS → LLM gateway → job; fragile Logs Insights; per-tenant support questions unanswerable after 14 days; audit evidence expires.
- Recommendation: structlog JSONRenderer (timestamper, level, logger) per entrypoint; middleware accepting/creating X-Request-ID binding request_id, tenant_id, job_id to contextvars; propagate in outbox metadata + job rows; log db_ms and latency (C1.1d); retention 30–90 days + S3/Glacier export 1 year; revisit AA-842 option B.
- Standards: OWASP ASVS V7; NIST SP 800-92; OpenTelemetry semantic conventions.

### Q10 — SLOs cover only Dev DB latency — MEDIUM, S, automatable
- Evidence: 03-scaling.md C1.2 DB-time p95, job claim, connection objectives ("targets that trigger work, not paging promises"); list-dashboards only aa-cis-dev-pipeline; no HTTP SLI.
- Risk: no basis for SLA or features-vs-reliability decisions; silent degradation.
- Recommendation: 3–4 user-facing SLOs (tenant /v1 99.5% + p95 < 800 ms; TP browse availability; Booking inquiry ingestion lag p95 < 5 min; content job success rate); ALB/API GW metrics in one dashboard per app with multi-window burn-rate alarms; monthly review in C8.
- Standards: Google SRE workbook; DORA reliability.

### Q11 — Inconsistent quality gates across repos — MEDIUM, S, automatable
- Evidence: CIS pip-audit `|| true` under required Security Audit; Trivy exit-code 0 in CIS + Booking; CIS cov 30 vs Booking 90; 10 orphan root tests outside `pytest tests/unit/ tests/acp/`; TP no --cov, no pip-audit/npm audit, no gitleaks.
- Risk: false assurance; vulnerable deps/images ship; untested paths grow in largest codebase.
- Recommendation: failing CIS pip-audit with expiring ignore list; Trivy exit-code 1 + --ignore-unfixed for CRITICAL after review; ratchet CIS coverage (+5%/month), move/delete orphan tests; copy Booking security job + floor into TP; ideally one reusable org workflow.
- Standards: Scorecard Vulnerabilities/SAST/CI-Tests; NIST SSDF PW.7/PW.8/RV.1.

### Q12 — TP Lambda deploy without live verification/rollback; FE production promotes not smoke-tested — MEDIUM, S, automatable
- Evidence: deploy-lambdas.yml publish + wait only ("Both Lambdas updated."), no invoke/HTTP smoke, no alias; ui-smoke gates on environment == 'Preview' only; aa-ship §3 manual curl.
- Risk: broken package (import error, missing env var) takes down B2C front door; no one-step rollback.
- Recommendation: publish to `live` alias, smoke invoke/curl with shape assertion, on failure re-point alias (optional CodeDeploy canary 10%/5 min with Lambda error alarms); ui-smoke also on Production deployment_status with read-only subset.
- Standards: DORA; SLSA/NIST SSDF PS.3.

### Q13 — No automated PII/data-quality guard for LLM prompts and logs — MEDIUM, M, automatable
- Evidence: 02-data-management.md DM-6.4 "No personal data MAY be written to shared.llm_call_log … No automated PII check exists or is on the roadmap (open point)"; DM-6.1 pii: column tags enforced by review only.
- Risk: traveller PII from TP assembly free text or Booking notes leaks into 180-day LLM ledgers, Jev requests or logs.
- Recommendation: regex/presidio-lite guard in LLMClient.generate() and log processor (email, phone, passport) → block/redact + CloudWatch metric + alarm; CI migration lint failing new email/phone/name/address columns without `pii:` COMMENT; nightly query on llm_call_log samples.
- Standards: GDPR Art. 25/32; NIST AI RMF MAP/MANAGE; ISO 27701.

### Q14 — Performance/load testing only as unused scripts — LOW, S, automatable
- Evidence: tests/load k6_api_smoke_test.js, k6_b2b_load_test.js, k6_golden_regression.js, k6_pipeline_load_test.js last changed 2026-09-11; no workflow references k6; ECS desiredCount 1 each; RDS db.t4g.small single-AZ.
- Risk: capacity limits (Hobby CPU cap already hit at 52%, burstable RDS credits, single task) found by first busy tenant; sales commitments unbacked.
- Recommendation: workflow_dispatch k6 of k6_b2b_load_test.js against Dev with thresholds tied to SLOs; run before releases or monthly in C8; record in docs/audits; small load.
- Standards: ISO 25010 performance efficiency; Google SRE capacity planning.

### Q15 — Process state spread over 5 hand-synced sources; docs drift — LOW, S, automatable
- Evidence: session ritual syncs Notion memory, docs/sessions (63), docs/backlog/README.md, Linear (4 projects, no milestones), Jira drafts by hand; drift: CIS_Runbook_v1 names acc1; global CLAUDE.md mandates ECS/RDS stop reminders while memory says not to; implementation notes uneven (CIS 417, Booking 16, root 4).
- Risk: per-session sync cost; stale docs mislead agents into wrong commands.
- Recommendation: Linear + repos as system of record; auto-generate session summary/backlog status from Linear and GitHub (`Refs AA-xxx` links); Notion memory as short pointer; CI doc-freshness check (grep retired account IDs/hostnames).
- Standards: DORA documentation quality; ITIL knowledge management.
