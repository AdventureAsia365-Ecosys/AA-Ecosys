---
id: GUIDE-13-lms-inventory
title: AA Academy knowledge inventory
description: Every domain, method, standard, process and tool the AA ecosystem runs on, with its source of truth, its audience and the AA Academy module that teaches it.
type: report
status: draft
owner: nghiep
audience: [owner, engineer, devops, cto, cio, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-13
review_every_days: 90
related: [GUIDE-13-lms, CAT-00, AA-1098, AA-1099]
---

# AA Academy knowledge inventory

Research note, S279, 2026-11-13 (AA-1098). Author: Claude Code (research lane). Read-only: no code change, no AWS
call, no paid call. The design that uses this list is in the [AA Academy research page](README.md). The Vietnamese
version is [inventory.vi.md](inventory.vi.md).

**How it was built.** An inventory pass read the root repo, the four app repos and Infra on their main branches:
the doc catalog, ADRs, data standards, runbooks, playbooks, templates, skills, steering files, hooks, tools,
workflows and each repo's `CONTEXT.md`. Each row names one thing a person must know, where it is written down, who
needs it and which module teaches it. Rows that only repeat another row were merged. Gaps (knowledge that has no
page yet) are listed in [README §2.3](README.md#23-gaps-that-block-courses), not here.

**241 items in 24 domains.** [§25](#25-further-sources-not-counted-in-the-241-items) adds the ADRs and history sources that refine these items but are not counted as items.

**Columns.**

- **Kind**: concept, decision, standard, technique, process, rule, runbook, tool, register, template, checklist,
  guide, hook, report, reference, plan.
- **Source**: the source of truth. A lesson links this path and never copies it. When a path lives in more than one repo,
  the row names the repos that hold it ("the four app repos" means AA-CIS-App, AA-Booking, AA-Partner and
  AA-TripPlanner-Web).
- **Audience**: E engineer, D engineer on duty, T tech lead, S ops and support, C content operator, B finance and
  booking staff, A agency owner and agent, O business owner, X AI agents (they read the same sources through
  skills), "all" for every role.
- **Module**: the module that teaches it (F fundamentals, E engineering, L tech lead, S ops and support, C content,
  B booking and finance, A agency, O business owner). The module list is in
  [README §3](README.md#3-audiences-and-learning-paths).

## 1. Architecture (12)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Ecosystem architecture (C4 levels 1–2) | concept | `docs/ecosystem-architecture.md` | all | F2 |
| Multi-repo layout and repo roles | concept | `docs/ecosystem-architecture.md` §1; `skill/aa-ecosys-repos/SKILL.md` | E T X | F2 |
| ADR 0001 target architecture | decision | `docs/adr/0001-ecosystem-target-architecture.md` | E T | F2 |
| ADR 0019 B2B-only ecosystem model | decision | `docs/adr/0019-b2b-only-ecosystem-model.md` | all | F1 |
| ADR 0002 only CIS writes content | decision | `docs/adr/0002-only-cis-writes-content.md` | E T | E3 |
| Apps own code, Infra owns resources | standard | `docs/ecosystem-architecture.md` §4.2; `infra/AA-CIS-Infra/CONTEXT.md` | E D | E10 |
| CONTEXT.md per repo | standard | `apps/AA-CIS-App/CONTEXT.md` (and each repo); `.kiro/steering/session-workflow.md` | E X | E1 |
| Architecture diagrams as code | technique | `docs/architecture/diagrams/README.md` | E T | E1 |
| ADR system, placement and numbering | standard | `docs/adr/README.md`; `skill/ai-nghiep/references/adr.md`; `tools/adr/check_adr_numbers.py` | E T X | L1 |
| ADR 0008 new-app integration rules and 12-step playbook | decision | `docs/adr/0008-new-app-integration-and-data-platform-rules.md`; `docs/adr/0008a-crm-separate-app-exceptions.md` | E T | L8 |
| Tour liveness and retirement propagation (ADR 0015) | decision | `docs/adr/0015-tour-liveness-and-retirement-propagation.md` | E | E11 |
| Glossary | reference | `docs/glossary.md`; `docs/glossary.vi.md` | all | F6 |

## 2. CIS content pipeline (22)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| A-series and T-series model | concept | `apps/AA-CIS-App/CONTEXT.md` (Pipeline stages) | E T C X | C2 |
| A0 upload and raw tours | concept | `apps/AA-CIS-App/CONTEXT.md` §A-series | E C | C2 |
| A1 generic rewrite graph (S1 writer v2) | technique | `apps/AA-CIS-App/CONTEXT.md` §A1 | E C | C2 |
| Grounding against the source | technique | `apps/AA-CIS-App/CONTEXT.md` §A1 grounding | E C | C3 |
| Day oracle and shadow-then-enforce gates | technique | `apps/AA-CIS-App/CONTEXT.md` §A1 day oracle | E C | C3 |
| A2 Review Queue (human in the loop) | concept | `apps/AA-CIS-App/CONTEXT.md` §A2 | E C | C4 |
| A3 Master Content Pool and atomize | concept | `apps/AA-CIS-App/CONTEXT.md` §A3 | E C X | C2 |
| A4 cross-tenant oversight | concept | `apps/AA-CIS-App/CONTEXT.md` §A4 | T C | C2 |
| Segment, score, route and hub rows | concept | `apps/AA-CIS-App/CONTEXT.md` (platform-wide rows) | E | E11 |
| T0 brand identity and brand pack | concept | `apps/AA-CIS-App/CONTEXT.md` §T0 | E A | A2 |
| T1–T4 tenant tour rewrite | concept | `apps/AA-CIS-App/CONTEXT.md` (T-series) | E A | A2 |
| T7 Slate and Debate layer | concept | `apps/AA-CIS-App/CONTEXT.md` §T7 | E A | A2 |
| T8 angle gate, T9 streamed write, place cards | concept | `apps/AA-CIS-App/CONTEXT.md` §T8–T9; `apps/AA-CIS-App/docs/adr/0004-live-writing-progress-via-redis-poll.md` | E A | A2 |
| T10 quality gates (F-codes, F10 near-duplicate check) | concept | `apps/AA-CIS-App/CONTEXT.md` §T10 | E C | C3 |
| T11 publish to WordPress and Facebook | concept | `apps/AA-CIS-App/CONTEXT.md` §T11 | E A | A2 |
| Content quality architecture (ADR 0020) | decision | `docs/adr/0020-content-quality-architecture.md` | E T C O | C3 |
| Governed writing memory | decision | `apps/AA-CIS-App/docs/adr/0010-governed-writing-memory.md` | E T C | C8 |
| Facts entries (platform and tenant scope) | concept | `apps/AA-CIS-App/CONTEXT.md` (ownership table) | E C | C8 |
| Jev decisions and calibration | technique | `apps/AA-CIS-App/docs/adr/0007-jev-verdicts-may-act.md` | E T C | C8 |
| Rerun waves | runbook | `skill/aa-wave-rerun/SKILL.md`; `apps/AA-CIS-App/docs/runbooks/clean-rerun.md` | E T C | C5 |
| Place pipeline in CIS | decision | `docs/adr/0007-place-pipeline-in-cis.md` | E C | C6 |
| Photo pipeline | concept | `docs/ecosystem-architecture.md` §4.5 | E C | C6 |

## 3. CIS platform (6)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Settings registry with operator guides | standard | `apps/AA-CIS-App/CONTEXT.md` §Settings registry | E T C | C7 |
| Staff roles and permissions | concept | `apps/AA-CIS-App/CONTEXT.md` §Staff roles and permissions | E T S | S2 |
| Tenant control plane and lifecycle | concept | `apps/AA-CIS-App/CONTEXT.md` §Tenant control plane; `docs/contracts/README.md` | E T S | S3 |
| Tenant DB role and RLS context | technique | `apps/AA-CIS-App/CONTEXT.md` §Tenant DB role | E | E3 |
| Admin BFF security (write guard, headers, no CORS) | technique | `apps/AA-CIS-App/CONTEXT.md` (Architecture at a glance) | E | E5 |
| Admin docs reader `/admin/docs` | tool | `docs/README.md` (Admin docs page allowlist); `tools/docs/build_docs_reader.py` | all | F6 |

## 4. Job runner (5)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| One durable job model, one job table per owner | decision | `docs/adr/0003-one-durable-job-model.md`; `docs/adr/0003a-per-owner-job-tables.md` | E D | E4 |
| SKIP LOCKED claim, drain and re-claim | technique | `docs/architecture/data-standards/03-scaling.md` C6 | E | E4 |
| Job-kind register and kill switches | register | `docs/ops/job-kinds.md` | D S | E4 |
| Deploy gate and its override | technique | `docs/ops/runbooks/deploy-gate-override.md` | E D | E4 |
| No backend merge during an open wave | rule | `skill/aa-wave-rerun/SKILL.md` §3; `skill/aa-ship/SKILL.md` §2 | E X | E4 |

## 5. AI platform (17)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| AI gateway (ADR 0009) | decision | `docs/adr/0009-ai-platform-and-provider-gateway.md`; `docs/architecture/ai-gateway.md` | E T | E6 |
| Registry, stage routes and route control | technique | `docs/architecture/ai-gateway.md` §3–4; `docs/generated/llm-routes.md` | E T | E6 |
| Gateway guards and budgets | technique | `docs/architecture/ai-gateway.md` §5 | E T | E6 |
| Ledger v2 (`shared.llm_call_log`) | standard | `docs/architecture/ai-gateway.md` §6 | E T X | E6 |
| Shared core `aa_llm`, vendored and checked | technique | `docs/architecture/ai-gateway.md` §7; `tools/llm-core/llm-core-sync.sh` | E | E6 |
| Data scopes per LLM stage | standard | `apps/AA-CIS-App/docs/adr/0012-llm-data-scopes-per-stage.md` | E T | E6 |
| Writer, judge and validate roles | concept | `docs/glossary.md`; `apps/AA-CIS-App/docs/adr/0008-validate-stages-any-vendor.md` | E | E6 |
| Shadow runs, golden sets and eval regression | technique | `apps/AA-CIS-App/docs/llm/eval-runbook.md` | E T | E6 |
| Prompt register | standard | `apps/AA-CIS-App/docs/llm/prompt-register.md` | E | E6 |
| Provider route order and cross-account invoke | concept | `docs/ecosystem-architecture.md` §4.3; `docs/adr/0001a-retire-acc1-llm-on-acc3-only.md` | E D T | E6 |
| Embeddings and re-embed | runbook | `docs/ops/runbooks/embedding-re-embed.md` | E | E6 |
| Gateway CLI tools | tool | `tools/llm/` | E D | E6 |
| AI Use Register | register | `docs/architecture/ai-use-register.md` | E T | L1 |
| AI boundary for high-risk advice | standard | `apps/AA-Partner/CONTEXT.md` (AI boundary for high-risk advice) | E A | A6 |
| AI mark on delivered content | standard | `docs/adr/0020-content-quality-architecture.md` | E A O | A6 |
| LLM access-denied and cost-spike playbooks | runbook | `docs/ops/playbooks/llm-access-denied.md`; `docs/ops/playbooks/llm-cost-spike.md` | D S | E9 |
| Postmortem: LLM account access refusal | report | `docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md` | D T | E15 |

## 6. TripPlanner (7)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Browse and assembly Lambda split | technique | `apps/AA-TripPlanner-Web/CONTEXT.md` §Backend | E | E14 |
| Event-sourced trips | concept | `apps/AA-TripPlanner-Web/CONTEXT.md` §Data model | E | E14 |
| Jobs Lambda and `tripplanner.job` | concept | `apps/AA-TripPlanner-Web/CONTEXT.md` §Jobs Lambda | E D | E14 |
| Guest identity and traveller sign-in | concept | `apps/AA-TripPlanner-Web/CONTEXT.md` §Guest identity | E | E14 |
| Edge shared secret, fail closed | technique | `apps/AA-TripPlanner-Web/CONTEXT.md` §Backend | E | E14 |
| Per-visitor AI rate limits | technique | `docs/ecosystem-architecture.md` §3.3 | E | E14 |
| TripPlanner runbook | guide | `docs/guides/tripplanner-runbook.md` | S O | S2 |

## 7. Booking (12)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Booking stack and bootstrap (ADR 0004) | decision | `docs/adr/0004-aa-booking-stack-and-bootstrap.md` | E | E12 |
| Supply content ownership (ADR 0004a) | decision | `docs/adr/0004a-supply-content-ownership.md` | E | E12 |
| B2B API `booking.b2b.v1` | concept | `docs/contracts/booking.b2b.v1.openapi.yaml` | E | E12 |
| Booking admin runbook | guide | `docs/guides/booking-admin-runbook.md` | B S | B1 |
| Pricing and supplier rates (ADR 0005) | decision | `docs/adr/0005-pricing-and-supplier-rates.md` | E B | B2 |
| Price versions and maker-checker | standard | `docs/adr/0005b-price-versions.md`; `docs/guides/booking-price-setup.md` | E B T | B2 |
| Tour price chain and agency price tiers | concept | `apps/AA-Booking/CONTEXT.md` (Tour price chain, Agency price tiers) | E B | B2 |
| Trip case lifecycle and trip checks | concept | `apps/AA-Booking/CONTEXT.md` §Trip checks | E B | B3 |
| Departures, allotments and booking operations | concept | `apps/AA-Booking/CONTEXT.md` (Agency booking operations) | E B | B3 |
| Supplier bookings, bills and payouts | concept | `apps/AA-Booking/CONTEXT.md` (Supplier bookings, Supplier bills) | E B | B4 |
| Finance: FX-normalised cost, purchase orders, profit | concept | `apps/AA-Booking/CONTEXT.md` §Finance | E B | B5 |
| B2B resale rules (warning below from price, VND quotes) | decision | `docs/adr/0005a-b2b-resale-warn-and-vnd.md` | E B | B6 |

## 8. Partner CRM (13)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| AA-Partner app (ADR 0010) | decision | `docs/adr/0010-aa-partner-app.md`; `apps/AA-Partner/CONTEXT.md` | E T | E13 |
| Tenant fair-share gate | technique | `apps/AA-Partner/CONTEXT.md` (Tenancy and data rules) | E | E13 |
| Signed client links | technique | `apps/AA-Partner/CONTEXT.md` (Route classes) | E | E13 |
| PII scrubber before AI calls | technique | `apps/AA-Partner/CONTEXT.md` (F3 PII scrubber) | E | E13 |
| Route classes and identity verifier | technique | `apps/AA-Partner/CONTEXT.md` (Route classes) | E | E5 |
| Content studio sign-in by token exchange | decision | `docs/adr/0010a-content-studio-partner-sign-in.md` | E | E5 |
| Content studio runbook | guide | `docs/guides/content-studio-runbook.md` | A S | A2 |
| CRM modules (pipeline, proposals, invoices, mail, SMS, workflows, reports) | concept | `docs/guides/crm-runbook.md`; `docs/product/partner-crm/prd.md` | E A | A3 |
| Agency users, roles and settings | guide | `docs/guides/crm-runbook.md` | A | A7 |
| AA support access windows (L2) and break-glass (L3) | standard | `apps/AA-Partner/CONTEXT.md` (AA support access) | E S A | S5 |
| Data portability and deletion | concept | `apps/AA-Partner/CONTEXT.md` (Data lifecycle) | E A | A5 |
| Bring-your-own vendor accounts, shared responsibility | decision | `docs/research/partner-crm-spec.md` | T A | A5 |
| CRM keys runbook | runbook | `docs/ops/runbooks/crm-keys.md` | D | E9 |

## 9. Identity (5)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Ecosystem identity on Cognito (ADR 0006) | decision | `docs/adr/0006-ecosystem-identity.md` | E D | E5 |
| BFF code flow with PKCE and token checks | technique | `docs/ecosystem-architecture.md` §4.6 | E | E5 |
| M2M client credentials with per-receiver scopes | technique | `docs/ecosystem-architecture.md` §4.6 | E | E5 |
| Staff directory in CIS (database first, then Cognito) | technique | `docs/ecosystem-architecture.md` §4.6 | E S | S2 |
| Cognito login playbook | runbook | `docs/ops/playbooks/cognito-login.md` | D S | S4 |

## 10. Data platform (19)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Shared RDS, one owner per schema | standard | `docs/database/schema-ownership.md` | E D X | E3 |
| Data standards: the 20 golden rules | standard | `docs/architecture/data-standards/README.md` | E T | E3 |
| Naming, types and keys | standard | `docs/architecture/data-standards/01-engineering.md` §1–2 | E | E3 |
| Migration mechanics and the MIG-4 flow | standard | `docs/architecture/data-standards/01-engineering.md` §3 | E X | E3 |
| Expand/contract migrations with auto-apply (ADR 0017) | decision | `docs/adr/0017-migrations-in-app-pr-expand-auto-apply.md` | E D | E3 |
| DB Migrate workflow | runbook | `docs/ops/runbooks/db-migrate.md` | E D | E3 |
| Roles, grants and the RLS template | standard | `docs/architecture/data-standards/01-engineering.md` §4 | E | E3 |
| Contract views, versioning and the contracts registry | standard | `docs/architecture/data-standards/01-engineering.md` §5; `docs/contracts/README.md`; `tools/contracts/check_contracts.py` | E | E3 |
| Outbox, pull job, inbox | technique | `docs/architecture/data-standards/01-engineering.md` (CON-7) | E | E3 |
| Query rules and the SQL PR checklist | standard | `docs/architecture/data-standards/01-engineering.md` §6–8 | E | E3 |
| Generated schema reference and ERD | tool | `docs/architecture/db-schema-reference.md`; `docs/architecture/erd/` | E X | E3 |
| Schema gotchas | concept | `.kiro/steering/db-schema.md`; `skill/aa-cis-schema/SKILL.md` | E X | E3 |
| Retention and archival | standard | `docs/architecture/data-standards/02-data-management.md` §7; `docs/legal/retention-log.md` | E T | E3 |
| Dead Table Registry | register | `docs/architecture/dead-table-registry.md` | E | E3 |
| Isolation probe | runbook | `docs/ops/runbooks/isolation-probe.md` | E T | E3 |
| Data management: ownership, catalog, quality, lineage | standard | `docs/architecture/data-standards/02-data-management.md` §1–5 | E T | L1 |
| PII classes and privacy rules | standard | `docs/architecture/data-standards/02-data-management.md` §6 | all | F4 |
| Destructive operations: DRY RUN first | runbook | `skill/aa-cis-schema/references/destructive-ops.md` | E D T | E9 |
| ECS exec through S3 | runbook | `docs/ops/runbooks/ecs-exec-s3-mediated.md`; `tools/ecs/ecsx.sh` | E D | E9 |

## 11. Scaling and reliability (6)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| SLOs and SLIs | standard | `docs/architecture/data-standards/03-scaling.md` C1 | D T | E9 |
| Connection budget | standard | `docs/architecture/data-standards/03-scaling.md` C2 | E D | E10 |
| Postgres maintenance | standard | `docs/architecture/data-standards/03-scaling.md` C5 | D | E10 |
| Scale on a measured trigger, cheapest lever first | technique | `docs/architecture/data-standards/03-scaling.md` C3, C9 | E T | L7 |
| Environment and account model (ADR 0012, ADR 0018) | decision | `docs/adr/0012-environment-model.md`; `docs/adr/0018-lean-aws-account-model.md` | T O | L7 |
| Monthly capacity review | runbook | `docs/templates/capacity-review.md` | D T | L5 |

## 12. Infrastructure (11)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Terraform roots, state and drift check | concept | `infra/AA-CIS-Infra/CONTEXT.md` | E D | E10 |
| Terraform apply only through the workflow | rule | `skill/aa-ship/SKILL.md` §2 | E D X | E10 |
| Edge path: API Gateway, VPC link, load balancers, CloudFront, WAF | concept | `docs/ecosystem-architecture.md` §2, §4.1 | E D | E10 |
| ECS Fargate services and immutable image tags | concept | `docs/ecosystem-architecture.md` §4.2 | E D | E10 |
| Per-app security groups (ADR 0004b) | decision | `docs/adr/0004b-per-app-security-groups.md` | D | E10 |
| GitHub OIDC, one role per repo and job | technique | `docs/ecosystem-architecture.md` §5 | D T | E10 |
| Generated infra references | tool | `docs/generated/` | E D | E10 |
| Environment config register (names only) | standard | `docs/generated/env-config.md` | E D | E10 |
| Tagging standard | standard | `docs/architecture/tagging-standard.md` | E D | F5 |
| Onboarding: accounts and access | guide | `docs/onboarding.md` | E D S | E1 |
| SES mail and bounces | runbook | `docs/ops/runbooks/ses-bounce.md` | D S | S4 |

## 13. Engineering practice (19)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Operating model: Kanban, trunk-based, ADLC | concept | `docs/engineering-handbook.md` §2.1 | all | F3 |
| The 12-stage lifecycle | standard | `docs/engineering-handbook.md` §3 | all | F3 |
| Roles and agent control | standard | `docs/engineering-handbook.md` §2.3; `docs/agents.md` | E T X | F3 |
| Definition of Ready and Definition of Done | standard | `docs/templates/definition-of-ready.md`; `skill/aa-ship/SKILL.md` | E T X | F3 |
| Engineering handbook | guide | `docs/engineering-handbook.md` | E T | F3 |
| Ship process from PR to Done | runbook | `skill/aa-ship/SKILL.md` | E X | E2 |
| Merge queue and ship tools | tool | `tools/github/README.md` | E X | E2 |
| Conventional commits with a Refs line | standard | `docs/engineering-handbook.md` §5.1 | E X | E2 |
| PR template as change record | standard | `.github/pull_request_template.md` | E | E2 |
| Pre-push hook | tool | `scripts/pre-push.sh` (the four app repos) | E X | E2 |
| Code-health and coverage ratchets | technique | `.github/scripts/code_health.py` (the four app repos); `.github/scripts/coverage_ratchet.py` (AA-CIS-App only) | E T | E2 |
| CI pipeline per repo | tool | `.github/workflows/ci.yml` (the four app repos); root: `docs-lint.yml`, `contracts.yml`, `workflow-lint.yml`, `pr-title.yml` (no `ci.yml`); Infra: `terraform-plan.yml`, `docs-lint.yml`, migration guards | E D | E2 |
| Release-please and immutable images | technique | `docs/engineering-handbook.md` §5.2–5.3 | E D | E2 |
| Post-deploy verify and the health contract | technique | `.github/workflows/post-deploy-verify.yml` (the four app repos) | E D | E2 |
| Feature flags register | standard | `docs/ops/feature-flags.md` | E D | E2 |
| API contract diff | tool | `.github/workflows/api-contract.yml` (AA-CIS-App and AA-Booking) | E | E2 |
| Implementation notes per issue | template | `docs/implementation-notes/` | E X | E2 |
| Secret scanning | tool | `.github/workflows/secret-scan.yml` (root, Infra and the four app repos) | E X | E2 |
| Cost line in every PR | rule | `skill/aa-ship/SKILL.md` §1 | E X | E2 |

## 14. Frontend (4)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| One design system, guarded kit copies (ADR 0016) | decision | `docs/adr/0016-one-design-system-guarded-kit-copies.md`; `tools/kit/kit-sync.sh` | E X | E7 |
| Next.js BFF pattern | technique | `docs/ecosystem-architecture.md` §4.1 | E | E7 |
| Vendored copy guards (identity verifier, `aa_llm`, kit) | technique | `tools/kit/`; `tools/llm-core/` | E | E7 |
| UI verification before Done | runbook | `skill/aa-ui-verify/SKILL.md` | E X | E7 |

## 15. Testing (3)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| UI smoke, visual regression and signed-in E2E | tool | `.github/workflows/visual.yml` (the four app repos); `ui-smoke.yml` and `e2e-cognito.yml` (AA-CIS-App); `ui-smoke-portal.yml` (AA-Partner) | E | E8 |
| Nightly integration tests | tool | `apps/AA-CIS-App/.github/workflows/nightly-integration.yml` | E | E8 |
| UAT harness and videos | tool | `tools/uat/build.py`; `skill/aa-uat-video/SKILL.md`; `docs/templates/uat-report.md` | E T O | E8 |

## 16. Observability and operations (12)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Observability baseline and alarm on symptoms | standard | `docs/engineering-handbook.md` §7.1 | E D | E9 |
| Structured logs with request ids | standard | `apps/AA-Booking/CONTEXT.md`; `apps/AA-TripPlanner-Web/CONTEXT.md` | E | E9 |
| Alarm catalog with runbook links | register | `docs/generated/alarms.md`; `tools/docs/check_alarm_runbooks.py` | D | E9 |
| Operations index and symptom table | guide | `docs/ops/README.md` | D S | S1 |
| Incident response and postmortems | process | `docs/ops/incident-response.md`; `docs/ops/postmortems/README.md`; `docs/templates/postmortem.md` | D S T | S1 |
| Playbooks by symptom (5xx spike, queue stuck) | runbook | `docs/ops/playbooks/5xx-spike.md`; `docs/ops/playbooks/queue-stuck.md` | D S | E9 |
| Rollback runbooks and the rollback game day | runbook | `docs/ops/runbooks/rollback-ecs.md` (and the other rollback pages); `docs/ops/drills/rollback-game-day.md` | D | E9 |
| Backup, point-in-time restore and restore drills | runbook | `docs/ops/runbooks/restore-rds-pitr.md`; `docs/ops/drills/README.md` | D | E9 |
| Break-glass | runbook | `docs/ops/runbooks/break-glass.md` | D T | E9 |
| Runbook "tested" rule | standard | `docs/STYLE.md` (Runbooks and tested) | E D | E9 |
| Pilot agency onboarding and rehearsal | runbook | `docs/ops/runbooks/pilot-agency-onboarding.md`; `docs/ops/runbooks/pilot-rehearsal.md` | T S | S3 |
| App access and operations index | guide | `docs/guides/app-access-and-operations.md` | S C B O | S2 |

## 17. Security (8)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Security baseline | checklist | `docs/security/baseline.md` | D T | L9 |
| Secrets register and rotation | register | `docs/security/secrets-register.md`; `docs/ops/runbooks/secret-rotation.md` | D T | E5 |
| Vulnerability management | process | `docs/security/vulnerability-management.md` | E T | L9 |
| Quarterly access review | template | `docs/templates/access-review.md` | T S | L9 |
| CI/CD hygiene and org security (ADR 0021) | decision | `docs/adr/0021-github-org-security-and-ci-hygiene.md`; `tools/github/ci_hygiene.py` | D T | L9 |
| Public-repo safe writing | standard | `docs/STYLE.md` (Where a page may live); `docs/adr/0014-repo-visibility-and-github-plan.md` | all | F4 |
| Compliance and privacy register (DPA, sub-processors, DSAR) | register | `docs/legal/register.md`; `docs/legal/readiness-packet.md` | T O | O5 |
| Tenant AI schedule and DPA pack | template | `docs/legal/tenant-ai-schedule.md`; `docs/legal/dpa.md` | A O | A5 |

## 18. Cost and FinOps (8)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| FinOps process | standard | `docs/ops/finops.md` | T O | F5 |
| Cost ledgers for every paid call | standard | `docs/architecture/data-standards/02-data-management.md` §10 | E | F5 |
| Quote the cost and get a yes per paid item | rule | `docs/ops/finops.md`; `docs/architecture/data-standards/02-data-management.md` DM-10.7 | E T X | F5 |
| Paid-run ladder (trial, then a small batch) | rule | `docs/architecture/data-standards/02-data-management.md` DM-10.6 | E T C | F5 |
| Cost estimate before a paid run | tool | `tools/llm/cost_estimate.py`; `tools/llm/spend_by_stage.py` | E T C | C5 |
| Cost Operations page and nightly reconcile | tool | `docs/ecosystem-architecture.md` §4.4 | T B O | O3 |
| Monthly cost report | tool | `docs/ops/cost/README.md`; `tools/finops/monthly_cost_report.py`; `docs/templates/cost-report.md` | T O | L5 |
| AI providers and reports runbook | guide | `docs/guides/ai-providers-and-reports-runbook.md` | T O | L5 |

## 19. Documentation (8)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Docs-as-code and the role catalog | standard | `docs/README.md`; `docs/engineering-handbook.md` §4 | all | F6 |
| Style guide, front matter and docs lint | standard | `docs/STYLE.md`; `tools/docs/check_frontmatter.py` | E X | F6 |
| Language rule and `.vi.md` translations | rule | `.kiro/steering/language-convention.md`; `docs/STYLE.md` (Language) | all | F6 |
| What fact lives where | standard | `docs/engineering-handbook.md` §4.9 | E X | F6 |
| Templates | template | `docs/templates/` | E T | F6 |
| Role guides | guide | `docs/guides/cto.md`, `cio.md`, `pm.md`, `devops.md` | T O | F1 |
| PRD as code | standard | `docs/product/README.md`; `tools/docs/check_prd_refs.py` | E T | L4 |
| Audits folder and artifact registry | standard | `docs/audits/`; `docs/artifacts/README.md` | T X | L3 |

## 20. Agent operations (11)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Agent instruction stack | concept | `docs/agents.md`; `docs/llms.txt`; `.kiro/steering/` | T X | L3 |
| Session ritual and live checklist | runbook | `skill/aa-session/SKILL.md`; `.kiro/steering/session-workflow.md` | T X | L3 |
| State snapshot before any log | checklist | `skill/aa-session/SKILL.md` (session end, step 2) | T X | L3 |
| Parallel code lanes | tool | `tools/workflows/lane.js`; `skill/aa-session/references/parallel-lanes.md` | T X | L3 |
| Orchestrator and subagent rights | rule | `skill/ai-nghiep/SKILL.md` §3 | T X | L3 |
| Task handoff template | template | `skill/ai-nghiep/references/handoff-prompt.md` | T X | L3 |
| Kiro delegation mode | process | `.claude/skills/kiro-delegate/SKILL.md` | T X | L3 |
| Skill set maintenance | process | `skill/README.md`; `skill/REVIEW-CHECKLIST.md` | T | L3 |
| Subagent and shell guard hooks | hook | `.claude/hooks/`; `.claude/settings.json` | T X | L3 |
| Agents never toggle infrastructure | rule | `skill/ai-nghiep/SKILL.md` §2 | T X | L3 |
| Scheduled guard watch | tool | `tools/github/guard_runs.py` | D T | L9 |

## 21. Planning and issues (9)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Living backlog | register | `docs/backlog/README.md` | T X | L4 |
| Master plan tracker and plan sync | tool | `docs/backlog/tracker/README.md`; `tools/linear/plan_sync.py` | T | L4 |
| Session size, pick order and WIP cap | rule | `skill/aa-session/SKILL.md` (session start, step 3) | T X | L4 |
| Platform roadmap and the "do not do now" list | register | `docs/engineering-handbook.md` §9 | T O | L4 |
| Linear issue standard and template | runbook | `skill/aa-linear-issue/SKILL.md` | T X | L4 |
| Linear Free-plan quota, export and archive | rule | `skill/aa-linear-issue/SKILL.md`; `tools/linear/linear_export.py` | T X | L4 |
| Done audit at session end | tool | `tools/linear/done_audit.py` | T X | L4 |
| Frozen Done-when and Done-with-scope | rule | `skill/aa-ship/SKILL.md` §4 | T X | L4 |
| Milestones from the ADR 0019 phases | plan | `docs/backlog/tracker/plan.json` | T O | O6 |

## 22. Governance and change control (13)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Source precedence | rule | `docs/engineering-handbook.md` §1.3; `docs/agents.md` | all | F3 |
| Hard rules: verify, root cause first | rule | `skill/ai-nghiep/SKILL.md` §2 | all | F3 |
| Technology selection frame | standard | `skill/ai-nghiep/references/adr.md` | T | L1 |
| Locked decisions | register | `docs/adr/README.md` | T X | L1 |
| Tech-lead decision log | register | `docs/engineering-handbook.md` §10 | T | L1 |
| Changing the handbook and the standards | process | `docs/engineering-handbook.md` §1.4 | T | L1 |
| Merge rights by phase | decision | `docs/architecture/data-standards/02-data-management.md` DM-11.5 | E T | L2 |
| Who approves what | register | `docs/architecture/data-standards/02-data-management.md` §11 | E T | L2 |
| Risk classes and independent agent review | process | `docs/templates/definition-of-ready.md`; `.claude/agents/kiro-reviewer.md` | E T X | L2 |
| GitHub App identity for agents (ADR 0011) | decision | `docs/adr/0011-github-app-identity-and-merge-rights.md`; `docs/security/github-apps.md` | D T | L2 |
| Maker-checker in business data | rule | `docs/adr/0005b-price-versions.md`; `docs/guides/booking-admin-runbook.md` | B T | B2 |
| No self-evaluation as evidence | rule | `skill/ai-nghiep/SKILL.md` §2 | E C X | C3 |
| Decision pages with proposed answers | rule | `skill/aa-session/SKILL.md` | T X | L6 |

## 23. Stakeholders and vendors (7)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Jira: draft, approve, post | rule | `skill/aa-jira-update/SKILL.md` | T X | L6 |
| Jira structure: app epics and the weekly report | standard | `skill/aa-jira-update/SKILL.md` | T O | O2 |
| Business or technical decision split | rule | `skill/aa-jira-update/SKILL.md` | T O | L6 |
| Stakeholder voice guide and vendor handling | guide | `skill/ai-nghiep/references/stakeholders-english.md` | T | L6 |
| Report and KPI registries | register | `docs/reports/catalog.yaml`; `docs/reports/kpis.yaml` | T O | O2 |
| Release notes | template | `docs/templates/release-note.md` | T O | O2 |
| CEO guide | guide | `docs/guides/ceo.md`; `docs/guides/ceo.vi.md` | O | O1 |

## 24. Lessons and learning (4)

| Item | Kind | Source | Audience | Module |
|---|---|---|---|---|
| Lesson log with a guard field | process | `skill/aa-lessons/SKILL.md`; `tools/docs/check_lessons.py` | E T X | E15 |
| Lessons become guard tests | process | `skill/aa-lessons/guards.md` | E X | E15 |
| New engineer learning path | guide | `docs/guides/new-engineer.md` | E | E1 |
| CIS admin runbook | guide | `docs/guides/cis-admin-runbook.md` | C S | C1 |

## 25. Further sources (not counted in the 241 items)

These sources are named so a module owner can find them. They are not extra knowledge items: each one refines an
item above, or serves as a worked-example source.

### 25.1 ADRs not named in the rows above

| ADR | Source | Refines | Module |
|---|---|---|---|
| Root 0006a identity phase 1 amendments | `docs/adr/0006a-identity-phase1-amendments.md` | Identity (§9) | E5, S2 |
| Root 0006b partner pool and MFA | `docs/adr/0006b-partner-pool-and-mfa.md` | Identity (§9); agency sign-in with MFA | E5, S4, A1 |
| Root 0011a CI bot merges copy and dump PRs | `docs/adr/0011a-ci-bot-merges-copy-and-dump-prs.md` | Merge rights (§22); migration flow (§10) | E3, L2 |
| Root 0017a Dev auto-applies contract migrations | `docs/adr/0017a-dev-auto-applies-contract-migrations.md` | Migration flow (§10) | E3 |
| CIS 0001 atoms platform-wide, segments per tenant | `apps/AA-CIS-App/docs/adr/0001-atoms-platform-wide-segments-per-tenant.md` | CIS content pipeline (§2) | E11 |
| CIS 0002 search demand shared across tenants | `apps/AA-CIS-App/docs/adr/0002-search-demand-shared-across-tenants.md` | CIS content pipeline (§2) | E11 |
| CIS 0003 segment, score, route and hub become platform-wide | `apps/AA-CIS-App/docs/adr/0003-segment-score-route-hub-will-become-platform-wide.md` | CIS content pipeline (§2) | E11 |
| CIS 0005 model catalog and Converse adapter | `apps/AA-CIS-App/docs/adr/0005-model-catalog-and-converse-adapter.md` | AI platform (§5) | E6 |
| CIS 0006 stage routes, fallback and shadow | `apps/AA-CIS-App/docs/adr/0006-stage-routes-fallback-and-shadow.md` | AI platform (§5) | E6 |
| CIS 0009 F17 owns offered moments | `apps/AA-CIS-App/docs/adr/0009-f17-owns-offered-moments-promises-gate-dropped.md` | Quality gates (§2) | C3 |
| CIS 0011 T9 FAQ question filter step | `apps/AA-CIS-App/docs/adr/0011-t9-faq-question-filter-llm-step.md` | T-series (§2) | E11 |
| Booking 0001 implements root ADR 0004 | `apps/AA-Booking/docs/adr/0001-implements-root-0004.md` | Booking (§7) | E12 |
| Partner 0001 implements root ADR 0010 | `apps/AA-Partner/docs/adr/0001-implements-root-0010.md` | Partner CRM (§8) | E13 |

### 25.2 History sources for worked examples

| Source | Where | What it gives a lesson | Module | Rule for use |
|---|---|---|---|---|
| Session logs | `docs/sessions/` (Vietnamese, with an index) | How a decision or incident unfolded in a real session | E15, L3, L4 | Cite as a worked example with an English summary in the lesson; never the source of a rule |
| Linear export of closed issues | `docs/linear-export/` | Ready issues and the evidence that closed them | E2, L4 | Pick examples that show the DoR and "Done = verified live" |
| Jira history (app epics, weekly report) | Outside the repo, read through the Jira connector | How progress is reported to the business owner | L6, O2 | Staff paths only; summarise, do not copy Jira text into the public repo |
| Audits | `docs/audits/` | How an audit is run and reported | L3, L9 | Already an item in §19; listed here as an example source too |
| Postmortems | `docs/ops/postmortems/` | Problem, cause, fix | E15, S1 | Already items in §5 and §16 |
