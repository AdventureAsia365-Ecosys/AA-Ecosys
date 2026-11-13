---
id: CAT-01-research-playbook-inventory
title: New-project playbook practice inventory
description: Every AA practice the new-project kit can reuse, with its source and what a generic version must change (AA-1099 research).
type: reference
status: draft
owner: nghiep
audience: [cto, engineer, pm, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-13
review_every_days: 90
lang: en
related: [CAT-01-research-playbook, CAT-01, AA-1099, AA-1098]
---

# New-project playbook practice inventory

Research for AA-1099, S279, 2026-11-13. Companion of the [playbook research](README.md). Every row was read from the
source path it cites. Root paths were checked to exist on `master`, and app or Infra paths on each repo's
`origin/main`, on 2026-11-13.

**Classes**

- **G**: general. Reuse as is in the kit.
- **P**: general pattern with AA wiring. The kit keeps the pattern and turns names, paths and tools into parameters.
- **A**: AA-specific. Stays in the AA overlay; LMS material (AA-1098), not kit material.

App and Infra repos are separate repos, so their paths are shown as code, not links.

| Part | Rows | G | P | A |
|---|---|---|---|---|
| Technical | 85 | 47 | 33 | 5 |
| Process | 34 | 23 | 11 | 0 |
| Governance | 24 | 21 | 3 | 0 |
| Management | 18 | 10 | 8 | 0 |
| **Total** | **161** | **101** | **55** | **5** |

**Scope placement.** AA-1099 groups "DRY RUN" under process and "data standards" under governance. This inventory
files them by their source, which is technical: T43 (DRY RUN for destructive work) and T35, T36 and T38 (data
standards). They are counted once, under Technical. Cross-references: T43 also belongs to Process (it is a change
procedure), and T35, T36 and T38 also belong to Governance (they are binding standards with a version and an
approver).

## Technical

### Architecture

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| T1 | Ecosystem architecture, C4 levels 1-2, facts marked [FACT] / [TO CONFIRM] | [`docs/ecosystem-architecture.md`](../../../docs/ecosystem-architecture.md) | P | Becomes the arc42 canvas plus C4 context, container and deployment views. Keep the FACT / TO CONFIRM marks. |
| T2 | Multi-repo layout: each app repo deploys alone; the root repo holds docs, ADRs, contracts and tools | [`docs/ecosystem-architecture.md`](../../../docs/ecosystem-architecture.md) §1<br>[`skill/aa-ecosys-repos/SKILL.md`](../../../skill/aa-ecosys-repos/SKILL.md) | P | Copier question: single repo or root + app repos. Ship the root skeleton (docs/, contracts/, tools/). |
| T3 | Apps ship code, Infra creates every cloud resource (placeholder zip, ignore code changes) | [`docs/ecosystem-architecture.md`](../../../docs/ecosystem-architecture.md) §4.2<br>`infra/AA-CIS-Infra/CONTEXT.md` | G | Copy the rule as is. The scaffold ships an infra folder with the placeholder pattern. |
| T4 | Architecture diagrams as code (Python diagrams with a Mermaid twin) | [`docs/architecture/diagrams/README.md`](../../../docs/architecture/diagrams/README.md) | G | Ship Mermaid by default; the Python renderer is optional. |
| T5 | CONTEXT.md per repo, read before any design and updated with any boundary change | `apps/AA-CIS-App/CONTEXT.md`<br>[`.kiro/steering/session-workflow.md`](../../../.kiro/steering/session-workflow.md) | P | Template with arc42 headings and a size cap; the CIS file is about 530 KB, so split it into module pages. |
| T6 | ADR system: placement by blast radius, numbering checked by CI, amendments NNNNa | [`docs/adr/README.md`](../../../docs/adr/README.md)<br>[`skill/ai-nghiep/references/adr.md`](../../../skill/ai-nghiep/references/adr.md)<br>[`tools/adr/check_adr_numbers.py`](../../../tools/adr/check_adr_numbers.py) | G | Use the MADR-minimal shape. Add a prune / supersede step so stale ADRs do not mislead agents. |
| T7 | Single writer per entity; other apps read through contracts (ADR 0002) | [`docs/adr/0002-only-cis-writes-content.md`](../../../docs/adr/0002-only-cis-writes-content.md) | P | State it as a generic data rule; the content example stays AA. |
| T8 | New-app decision gate and 12-step playbook (ADR 0008) | [`docs/adr/0008-new-app-integration-and-data-platform-rules.md`](../../../docs/adr/0008-new-app-integration-and-data-platform-rules.md) | P | Becomes the Setup phase checklist; schema, role and pool names become placeholders. |
| T9 | Retire an entity with one state, tombstone and outbox views (ADR 0015) | [`docs/adr/0015-tour-liveness-and-retirement-propagation.md`](../../../docs/adr/0015-tour-liveness-and-retirement-propagation.md) | P | Generic pattern page in the Retire phase. |
| T10 | Lean environment and account model: two environments, prod built when go-live is dated | [`docs/adr/0012-environment-model.md`](../../../docs/adr/0012-environment-model.md)<br>[`docs/adr/0018-lean-aws-account-model.md`](../../../docs/adr/0018-lean-aws-account-model.md) | G | Default of the kit; the AA account map stays AA. |
| T11 | Glossary in two languages | [`docs/glossary.md`](../../../docs/glossary.md) | P | Ship the SDLC / ADLC / ops terms; each project adds its own domain terms. |

### Domain (AA product)

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| T12 | CIS content pipeline A0-A4 and T0-T11, atoms, slate, place and photo pipelines | `apps/AA-CIS-App/CONTEXT.md`<br>[`docs/adr/0019-b2b-only-ecosystem-model.md`](../../../docs/adr/0019-b2b-only-ecosystem-model.md) | A | Not in the kit. Course material for the LMS (AA-1098). |
| T13 | Booking and Partner domain: pricing, supplier rates, trip cases, CRM modules | `apps/AA-Booking/CONTEXT.md`<br>`apps/AA-Partner/CONTEXT.md`<br>[`docs/adr/0005b-price-versions.md`](../../../docs/adr/0005b-price-versions.md) | A | Not in the kit. Maker-checker and price versions move to governance as a generic rule. |
| T14 | AI write, verify, repair loop with grounding against the source (A1, ADR 0020) | `apps/AA-CIS-App/CONTEXT.md` §A1<br>[`docs/adr/0020-content-quality-architecture.md`](../../../docs/adr/0020-content-quality-architecture.md) | P | Generic pattern page: one policy registry, one fact sheet, measured gates, one exit contract. |
| T15 | Shadow, then enforce: a new automatic check acts only after a precision read | `apps/AA-CIS-App/CONTEXT.md` §A1 | G | Generic rule for any new gate; the threshold becomes a setting. |
| T16 | Human review queue for rows that fail automatic checks | `apps/AA-CIS-App/CONTEXT.md` §A2 | G | Pattern page. |
| T17 | Calibrated AI judge: a verdict acts only after calibration on labelled samples | `apps/AA-CIS-App/docs/adr/0007-jev-verdicts-may-act.md` | P | Generic rule; the vendor stays AA. |

### Platform

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| T18 | Settings registry: every threshold, limit and cap is editable on an admin page, with a guide per key | `apps/AA-CIS-App/api/services/settings_registry.py`<br>`apps/AA-CIS-App/CONTEXT.md` | P | Scaffold ships the table, an admin page stub and a CI guard against new literals. |
| T19 | Staff roles mapped from identity groups; page rules enforced in proxy and API | `apps/AA-CIS-App/CONTEXT.md` | P | Template role matrix, provider-neutral. |
| T20 | Tenant control plane, lifecycle, DB role with RLS context that fails closed | `apps/AA-CIS-App/CONTEXT.md`<br>[`docs/architecture/data-standards/01-engineering.md`](../../../docs/architecture/data-standards/01-engineering.md) §4 | P | Copier question: multi-tenant yes or no. Yes adds the RLS template with FORCE from day 1. |
| T21 | BFF security: cross-site write guard, six security headers, no CORS grant | `apps/AA-CIS-App/CONTEXT.md` | G | Ships inside the web skeleton. |
| T22 | Identity: one pool per audience, identity = (iss, sub), BFF code + PKCE, scoped machine tokens | [`docs/adr/0006-ecosystem-identity.md`](../../../docs/adr/0006-ecosystem-identity.md)<br>[`docs/ecosystem-architecture.md`](../../../docs/ecosystem-architecture.md) §4.6 | P | Provider-neutral identity checklist; Cognito is the AA profile. |
| T23 | Edge shared secret that fails closed; one token class per route prefix; hashed client links | `apps/AA-TripPlanner-Web/CONTEXT.md`<br>`apps/AA-Partner/CONTEXT.md` | G | Pattern items in the security baseline. |
| T24 | Tenant fair-share gate (noisy-neighbour control) | `apps/AA-Partner/CONTEXT.md` | G | Part of the multi-tenant option. |

### Job runner

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| T25 | One durable job model, one job table per owner, SKIP LOCKED claim, drain and re-claim on deploy | [`docs/adr/0003-one-durable-job-model.md`](../../../docs/adr/0003-one-durable-job-model.md)<br>[`docs/adr/0003a-per-owner-job-tables.md`](../../../docs/adr/0003a-per-owner-job-tables.md)<br>[`docs/architecture/data-standards/03-scaling.md`](../../../docs/architecture/data-standards/03-scaling.md) C6 | G | Scaffold ships the DDL template and the worker loop. |
| T26 | Job-kind register with kill switches; deploy gate that waits only on blocking kinds | [`docs/ops/job-kinds.md`](../../../docs/ops/job-kinds.md)<br>[`docs/ops/runbooks/deploy-gate-override.md`](../../../docs/ops/runbooks/deploy-gate-override.md) | P | Register template and a deploy-gate endpoint in the scaffold. |

### AI platform

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| T27 | AI gateway: one seam for every paid AI or data call, routes with fallback, budgets, circuit breakers | [`docs/adr/0009-ai-platform-and-provider-gateway.md`](../../../docs/adr/0009-ai-platform-and-provider-gateway.md)<br>[`docs/architecture/ai-gateway.md`](../../../docs/architecture/ai-gateway.md) | P | Copier question: AI features yes or no. Yes vendors the gateway core under a sync guard. |
| T28 | Ledger row per attempt, refusals and errors included; ad-hoc scripts tagged adhoc_<issue> | [`docs/architecture/ai-gateway.md`](../../../docs/architecture/ai-gateway.md) §6<br>[`.kiro/steering/session-workflow.md`](../../../.kiro/steering/session-workflow.md) | G | Mandatory rule for every paid call. |
| T29 | Data scopes per stage, prompt register, AI use register | `apps/AA-CIS-App/docs/adr/0012-llm-data-scopes-per-stage.md`<br>`apps/AA-CIS-App/docs/llm/prompt-register.md`<br>[`docs/architecture/ai-use-register.md`](../../../docs/architecture/ai-use-register.md) | G | Three templates. |
| T30 | Evals: golden set, shadow runs, eval-regression CI | `apps/AA-CIS-App/docs/llm/eval-runbook.md`<br>`apps/AA-CIS-App/.github/workflows/eval-regression.yml` | G | Workflow template and a golden folder. |
| T31 | AI boundary for high-risk advice; AI mark on delivered content | `apps/AA-Booking/CONTEXT.md`<br>[`docs/adr/0020-content-quality-architecture.md`](../../../docs/adr/0020-content-quality-architecture.md) | G | Items in the release checklist (AI section). |
| T32 | Provider failure domain: an account-level refusal took every model down at once | [`docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md`](../../../docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md) | P | Rule: two independent provider paths before AI is relied on in prod. |
| T33 | Cross-account invoke, provider route order, key runbook, gateway CLI tools | [`docs/ecosystem-architecture.md`](../../../docs/ecosystem-architecture.md) §4.3<br>[`docs/ops/runbooks/llm-anthropic-api-key.md`](../../../docs/ops/runbooks/llm-anthropic-api-key.md)<br>[`tools/llm/`](../../../tools/llm/) | A | AA overlay only. |

### Data platform

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| T34 | Shared database, one owner per schema, ownership register | [`docs/database/schema-ownership.md`](../../../docs/database/schema-ownership.md) | G | Register template. |
| T35 | Data standards (version 1.13 as of 2026-11-13): 20 golden rules, Parts A (engineering), B (management), C (scaling) | [`docs/architecture/data-standards/README.md`](../../../docs/architecture/data-standards/README.md) | P | Ship a core copy; AA numbers (windows, budgets) become defaults the project sets. |
| T36 | Naming, keys and types (NAM, KEY), query rules (QRY), SQL PR checklist | [`docs/architecture/data-standards/01-engineering.md`](../../../docs/architecture/data-standards/01-engineering.md) | G | Copy as is. |
| T37 | Migrations: per-owner keys, idempotent, no down files, expand / contract, expand auto-applied on Dev | [`docs/architecture/data-standards/01-engineering.md`](../../../docs/architecture/data-standards/01-engineering.md) §3<br>[`docs/adr/0017-migrations-in-app-pr-expand-auto-apply.md`](../../../docs/adr/0017-migrations-in-app-pr-expand-auto-apply.md) | P | Migration template and preflight; the Infra copy step only for multi-repo projects. |
| T38 | Roles, grants and one RLS template (SEC-1..12) | [`docs/architecture/data-standards/01-engineering.md`](../../../docs/architecture/data-standards/01-engineering.md) §4 | G | Copy as is. |
| T39 | Contract views, JSON Schema per contract, minor additive / major parallel, contract lint | [`docs/contracts/README.md`](../../../docs/contracts/README.md)<br>[`tools/contracts/check_contracts.py`](../../../tools/contracts/check_contracts.py) | G | Contract template and lint in the scaffold. |
| T40 | Outbox, pull job, idempotent inbox | [`docs/architecture/data-standards/README.md`](../../../docs/architecture/data-standards/README.md) | G | Pattern page. |
| T41 | PII column tags, retention row per log table, archive to object storage | [`docs/architecture/data-standards/02-data-management.md`](../../../docs/architecture/data-standards/02-data-management.md) §6-7 | G | Retention template; PII inventory generator. |
| T42 | Generated schema reference and ERD; agents never guess table or column names | [`docs/architecture/db-schema-reference.md`](../../../docs/architecture/db-schema-reference.md)<br>[`.kiro/steering/db-schema.md`](../../../.kiro/steering/db-schema.md) | P | Dump workflow in the scaffold. This is the DORA 'AI-accessible internal data' capability. |
| T43 | Dead table registry; destructive work as DRY RUN first | [`docs/architecture/dead-table-registry.md`](../../../docs/architecture/dead-table-registry.md)<br>[`skill/aa-cis-schema/references/destructive-ops.md`](../../../skill/aa-cis-schema/references/destructive-ops.md) | G | Copy as is. |
| T44 | Isolation probe: 0 cross-tenant rows when RLS or roles change | [`docs/ops/runbooks/isolation-probe.md`](../../../docs/ops/runbooks/isolation-probe.md) | G | CI probe template for the multi-tenant option. |
| T45 | DB Migrate workflow, container exec via object storage, schema gotchas | [`docs/ops/runbooks/db-migrate.md`](../../../docs/ops/runbooks/db-migrate.md)<br>[`docs/ops/runbooks/ecs-exec-s3-mediated.md`](../../../docs/ops/runbooks/ecs-exec-s3-mediated.md) | A | AA overlay. The kit keeps only the principle: DDL runs from CI, never from a laptop. |

### Scaling and reliability

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| T46 | SLOs, connection budget at most 75%, scale on measured trigger, Postgres maintenance, monthly capacity review | [`docs/architecture/data-standards/03-scaling.md`](../../../docs/architecture/data-standards/03-scaling.md) | G | Defaults; SLOs and an error budget switch on at the first prod release. |

### Infrastructure

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| T47 | IaC: one root per account, state backend, plan on PR, apply only from main, scheduled drift check | `infra/AA-CIS-Infra/CONTEXT.md` | P | Infra skeleton with the same workflows; account names become parameters. |
| T48 | CI to cloud with OIDC, one role per repo and job | [`docs/ecosystem-architecture.md`](../../../docs/ecosystem-architecture.md) §5 | G | Copy as is. |
| T49 | Tagging standard with a CI tag guard; Terraform plan guards | [`docs/architecture/tagging-standard.md`](../../../docs/architecture/tagging-standard.md) | G | Tag keys keep their names; values per project. |
| T50 | Generated references: inventory, IAM roles, network, alarms, env config (names only) | [`docs/generated/alarms.md`](../../../docs/generated/alarms.md)<br>[`docs/generated/env-config.md`](../../../docs/generated/env-config.md) | P | docs-gen workflow in the infra skeleton. |
| T51 | Containers on Fargate, immutable image tags per commit, /health reports git_sha | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §5.3 | G | Copy as is. |
| T52 | One security group per caller | [`docs/adr/0004b-per-app-security-groups.md`](../../../docs/adr/0004b-per-app-security-groups.md) | G | Copy as is. |

### Engineering practice

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| T53 | CI pipeline: lint, sharded unit and integration tests, image build, frontend build | `apps/AA-CIS-App/.github/workflows/ci.yml` | P | One template per stack (Python API, Next.js web, Lambda). |
| T54 | Pre-push hook with fast local checks | `apps/AA-CIS-App/.githooks/pre-push`<br>`apps/AA-CIS-App/scripts/pre-push.sh` | G | Ships in the scaffold. |
| T55 | Code-health ratchets: complexity at most 10, file at most 800 lines, shrink-only baseline (AA-1097) | `apps/AA-CIS-App/.github/scripts/code_health.py`<br>`apps/AA-CIS-App/.github/code-health.json` | G | Ships from day 1 with an empty baseline, so the limit holds from the first commit. |
| T56 | Coverage ratchet: the floor only moves up | `apps/AA-CIS-App/.github/scripts/coverage_ratchet.py` | G | Ships in the scaffold. |
| T57 | CI/CD hygiene: action allowlist, pin freshness, cache budget, workflow lint | [`docs/adr/0021-github-org-security-and-ci-hygiene.md`](../../../docs/adr/0021-github-org-security-and-ci-hygiene.md)<br>[`tools/github/ci_hygiene.py`](../../../tools/github/ci_hygiene.py) | G | Copy as is. |
| T58 | Secret scanning on PRs and on full history | [`.github/workflows/secret-scan.yml`](../../../.github/workflows/secret-scan.yml) | G | Copy as is. |
| T59 | PR title check and the Refs rule | [`.github/workflows/pr-title.yml`](../../../.github/workflows/pr-title.yml) | P | The tracker key pattern becomes a parameter. |
| T60 | PR template as change record: risk, rollback, cost, docs impact | [`.github/pull_request_template.md`](../../../.github/pull_request_template.md) | G | Copy as is. |
| T61 | Release-please, build once deploy many, post-deploy verify, /health and /health/ready contract | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §5.2<br>`apps/AA-CIS-App/.github/workflows/post-deploy-verify.yml` | G | Ships in the scaffold. |
| T62 | Feature flag register: deploy is not release | [`docs/ops/feature-flags.md`](../../../docs/ops/feature-flags.md) | G | Template register. |
| T63 | API contract diff (OpenAPI export and breaking-change check) | `apps/AA-CIS-App/.github/workflows/api-contract.yml` | G | Ships in the scaffold. |
| T64 | Byte-copy guards for vendored shared code (UI kit, AI core, identity verifier) | [`docs/adr/0016-one-design-system-guarded-kit-copies.md`](../../../docs/adr/0016-one-design-system-guarded-kit-copies.md)<br>[`tools/kit/kit-sync.sh`](../../../tools/kit/kit-sync.sh) | G | Generic sync script with a source list. |
| T65 | Merge queue and ship tools (gate, wave, train, copy and apply) | [`tools/github/README.md`](../../../tools/github/README.md)<br>[`skill/aa-ship/references/merge-trains.md`](../../../skill/aa-ship/references/merge-trains.md) | P | The repo list (apps.env) and bot names become parameters. |

### Frontend and testing

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| T66 | One design system, canonical kit copied byte for byte, edit guard | [`docs/adr/0016-one-design-system-guarded-kit-copies.md`](../../../docs/adr/0016-one-design-system-guarded-kit-copies.md) | P | Kit option; an accessibility standard must be added (gap). |
| T67 | UI verify: build, preview, screenshots light / dark / mobile, console and network errors, real data | [`skill/aa-ui-verify/SKILL.md`](../../../skill/aa-ui-verify/SKILL.md) | P | Generic skill. |
| T68 | Playwright smoke, visual diff, signed-in E2E, nightly integration | `apps/AA-CIS-App/.github/workflows/ui-smoke.yml`<br>`apps/AA-CIS-App/.github/workflows/visual.yml` | G | Workflow templates. |
| T69 | UAT harness: scripted run to video with captions and free local narration | [`tools/uat/build.py`](../../../tools/uat/build.py)<br>[`skill/aa-uat-video/SKILL.md`](../../../skill/aa-uat-video/SKILL.md) | G | Ships as a tool. |

### Observability and security

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| T70 | Observability baseline: structured JSON logs with request id, symptom alarms, error tracker, health SHA | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §7.1 | G | Copy as is. |
| T71 | Alarm catalog where every alarm links its runbook (lint fails otherwise) | [`docs/generated/alarms.md`](../../../docs/generated/alarms.md)<br>[`tools/docs/check_alarm_runbooks.py`](../../../tools/docs/check_alarm_runbooks.py) | G | Copy as is. |
| T72 | Security baseline checklist with live status and re-check command | [`docs/security/baseline.md`](../../../docs/security/baseline.md) | P | Re-map to OWASP ASVS 5.0 level 1 and a light SAMM self-check. |
| T73 | Secrets register (names only), rotation runbook, vulnerability management | [`docs/security/secrets-register.md`](../../../docs/security/secrets-register.md)<br>[`docs/ops/runbooks/secret-rotation.md`](../../../docs/ops/runbooks/secret-rotation.md)<br>[`docs/security/vulnerability-management.md`](../../../docs/security/vulnerability-management.md) | G | Templates. |
| T74 | Public-repo safe writing: no account IDs, ARNs, network IDs or weaknesses | [`docs/STYLE.md`](../../../docs/STYLE.md)<br>[`docs/adr/0014-repo-visibility-and-github-plan.md`](../../../docs/adr/0014-repo-visibility-and-github-plan.md) | G | Copy as is. |
| T75 | Agent guardrail hooks: subagent, MCP, shell guard, kit edit, PII guard, with red-team tests | [`.claude/hooks/subagent-guardrails.sh`](../../../.claude/hooks/subagent-guardrails.sh)<br>[`.claude/hooks/aa_shell_guard.py`](../../../.claude/hooks/aa_shell_guard.py)<br>[`.claude/settings.json`](../../../.claude/settings.json) | P | Split into generic rules and AA rules; tests ship with them. |
| T76 | Privacy register: processing records, sub-processors, DPA, data subject requests | [`docs/legal/register.md`](../../../docs/legal/register.md) | P | Template; legal text per jurisdiction. |

### Cost and documentation

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| T77 | FinOps: tags, budgets, DB spend caps, monthly cost report tool | [`docs/ops/finops.md`](../../../docs/ops/finops.md)<br>[`tools/finops/monthly_cost_report.py`](../../../tools/finops/monthly_cost_report.py) | P | Cost sheet template; the report tool reads a project config. |
| T78 | Admin spend page and nightly ledger reconcile | [`docs/ecosystem-architecture.md`](../../../docs/ecosystem-architecture.md) §4.4 | A | AA overlay. |
| T79 | Docs as code: catalog, Diátaxis types, front-matter schema, docs lint | [`docs/README.md`](../../../docs/README.md)<br>[`docs/STYLE.md`](../../../docs/STYLE.md)<br>[`tools/docs/README.md`](../../../tools/docs/README.md) | G | Ships the catalog skeleton and lint. |
| T80 | Language rule: English pages, second language as .vi.md sibling | [`.kiro/steering/language-convention.md`](../../../.kiro/steering/language-convention.md) | P | Parameters: primary and secondary language. |
| T81 | Doc templates: ADR, runbook, how-to, reference, explanation, postmortem, release note, reviews | [`docs/templates/adr.md`](../../../docs/templates/adr.md)<br>[`docs/templates/runbook.md`](../../../docs/templates/runbook.md) | G | Copy as is. |
| T82 | Onboarding, role guides, new engineer learning path | [`docs/onboarding.md`](../../../docs/onboarding.md)<br>[`docs/guides/new-engineer.md`](../../../docs/guides/new-engineer.md) | P | Template structure; content per project. |
| T83 | PRD as code with acceptance criteria AC-n | [`docs/product/README.md`](../../../docs/product/README.md) | G | Copy as is. |
| T84 | Implementation notes per issue (Decisions, Changed, Tradeoffs, Should know) | [`docs/implementation-notes/`](../../../docs/implementation-notes/) | G | Copy as is. |
| T85 | Admin docs reader with EN / VI toggle and ID redaction | [`tools/docs/build_docs_reader.py`](../../../tools/docs/build_docs_reader.py) | P | Base for the LMS (AA-1098). |

## Process

### Session management

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| R1 | Session start: read state, live checks, AI gateway status, propose issues by plan slot | [`skill/aa-session/SKILL.md`](../../../skill/aa-session/SKILL.md)<br>[`.kiro/steering/session-workflow.md`](../../../.kiro/steering/session-workflow.md) | P | Generic skill; live checks come from a project config file. |
| R2 | Session end in strict order: close work, live snapshot, lessons, drafts approved, then logs | [`skill/aa-session/SKILL.md`](../../../skill/aa-session/SKILL.md) | P | Generic skill; evidence before logs stays. |
| R3 | Live session checklist, published as the tracker's session tab | [`docs/backlog/tracker/README.md`](../../../docs/backlog/tracker/README.md) | P | Checklist file in the repo; publishing optional. |
| R4 | Session size 3-5 issues; at most 8 In Progress; convergence pass above the cap | [`skill/aa-session/SKILL.md`](../../../skill/aa-session/SKILL.md) | G | This is a Kanban WIP limit; add work item age and cycle time. |
| R5 | Periodic reviews: weekly slow queries, monthly capacity and cost, quarterly access | [`skill/aa-session/SKILL.md`](../../../skill/aa-session/SKILL.md)<br>[`docs/templates/capacity-review.md`](../../../docs/templates/capacity-review.md)<br>[`docs/templates/access-review.md`](../../../docs/templates/access-review.md) | G | Copy the cadence; due dates from the latest record. |
| R6 | Session logs, numbering and memory block | [`docs/sessions/README.md`](../../../docs/sessions/README.md) | P | Memory store becomes a parameter (repo file by default). |
| R7 | Sources of truth for process state and conflict order | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §2.2 | G | Copy as is. |
| R8 | Finish before closing; stop hook blocks a stop while unblocked items remain | [`.claude/hooks/stop-open-work.sh`](../../../.claude/hooks/stop-open-work.sh) | G | Ships with the agent hooks. |

### Ready and done

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| R9 | Definition of Ready with risk classes (auth, migration, IAM/secret, delete, cost, LLM) | [`docs/templates/definition-of-ready.md`](../../../docs/templates/definition-of-ready.md) | G | Copy as is; add an appetite field. |
| R10 | Definition of Done = verified live, with an evidence comment | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md) | G | Copy as is. |
| R11 | Done-when frozen at In Progress; Done-with-scope only with follow-ups | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md) | G | Copy as is. |

### Ship and release

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| R12 | Pre-merge checklist; gate on every check, not only required ones | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md) | P | Generic skill; tool names become parameters. |
| R13 | Deploy only when no blocking job or batch run is open; drain and re-claim the rest | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md)<br>[`docs/architecture/data-standards/03-scaling.md`](../../../docs/architecture/data-standards/03-scaling.md) | G | Copy as is. |
| R14 | Infrastructure apply only through the workflow, from main | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md) | G | Copy as is. |
| R15 | Post-deploy live verification steps | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md) | G | Becomes the release checklist. |
| R16 | Release notes from verified work only | [`docs/templates/release-note.md`](../../../docs/templates/release-note.md) | G | Copy as is. |
| R17 | Rollback: app first, database forward-only; runbooks and a game day | [`docs/ops/runbooks/rollback-ecs.md`](../../../docs/ops/runbooks/rollback-ecs.md)<br>[`docs/ops/drills/rollback-game-day.md`](../../../docs/ops/drills/rollback-game-day.md) | G | Templates; most AA rollback runbooks are still UNTESTED. |
| R18 | Flag and migration order: flag OFF, deploy, apply, flag ON, verify | [`docs/ops/feature-flags.md`](../../../docs/ops/feature-flags.md) | G | Copy as is. |
| R19 | Versioning: commits, app versions, image tags, migration keys, API, prompt and model versions | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §5 | G | Copy as is. |

### Paid batch runs

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| R20 | Batch run as a fixed set: 3, then at most 50, then all; snapshot; stop conditions in numbers; report with exit code | [`skill/aa-wave-rerun/SKILL.md`](../../../skill/aa-wave-rerun/SKILL.md) | P | Generic batch-run skill. |
| R21 | Cost estimate before a paid run; no basis means a 3-item trial first | [`tools/llm/cost_estimate.py`](../../../tools/llm/cost_estimate.py) | P | Reads the project's ledger. |

### Incidents and learning

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| R22 | Incident response: severity, first 15 minutes, who is told, breach path | [`docs/ops/incident-response.md`](../../../docs/ops/incident-response.md) | G | Copy as is. |
| R23 | Playbooks by symptom, runbook library, the 'tested' rule | [`docs/ops/README.md`](../../../docs/ops/README.md)<br>[`docs/STYLE.md`](../../../docs/STYLE.md) | P | Index template; the tested rule stays. |
| R24 | Drills and game days with evidence links | [`docs/ops/drills/README.md`](../../../docs/ops/drills/README.md) | G | Copy as is. |
| R25 | Blameless postmortem template and index | [`docs/templates/postmortem.md`](../../../docs/templates/postmortem.md)<br>[`docs/ops/postmortems/README.md`](../../../docs/ops/postmortems/README.md) | G | Add the SRE trigger list. |
| R26 | Lesson log with a mandatory Guard field; lessons become tests or hooks | [`skill/aa-lessons/SKILL.md`](../../../skill/aa-lessons/SKILL.md)<br>[`tools/docs/check_lessons.py`](../../../tools/docs/check_lessons.py)<br>[`skill/aa-lessons/guards.md`](../../../skill/aa-lessons/guards.md) | G | Ships with an empty log and the checker. |
| R27 | Hard rules: verify, do not assume; root cause first; verify live before claiming | [`skill/ai-nghiep/SKILL.md`](../../../skill/ai-nghiep/SKILL.md) | G | Copy as is. |

### Agent orchestration

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| R28 | Orchestrator and subagent rights: subagents code and commit locally; the orchestrator ships | [`skill/ai-nghiep/SKILL.md`](../../../skill/ai-nghiep/SKILL.md) | G | Copy as is; the hooks enforce it. |
| R29 | Parallel lanes: worktree per lane, reviewers by lens, one fix pass, PR list with live steps | [`tools/workflows/lane.js`](../../../tools/workflows/lane.js)<br>[`skill/aa-session/references/parallel-lanes.md`](../../../skill/aa-session/references/parallel-lanes.md) | P | Split the COMMON rules into a generic block and an AA block. |
| R30 | Task handoff template | [`skill/ai-nghiep/references/handoff-prompt.md`](../../../skill/ai-nghiep/references/handoff-prompt.md) | G | Copy as is. |
| R31 | Delegation to a second coding agent (Kiro) with preflight and gatekeeping | [`.claude/skills/kiro-delegate/SKILL.md`](../../../.claude/skills/kiro-delegate/SKILL.md)<br>[`.claude/agents/kiro-reviewer.md`](../../../.claude/agents/kiro-reviewer.md) | P | Vendor-neutral 'second agent' pattern. |
| R32 | Agent instruction stack and index: CLAUDE.md, steering, skills, llms.txt | [`docs/agents.md`](../../../docs/agents.md)<br>[`docs/llms.txt`](../../../docs/llms.txt) | P | AGENTS.md becomes the source; CLAUDE.md imports it. |
| R33 | Skill maintenance: short SKILL.md, references, prune superseded rules, rules turned into CI removed | [`skill/README.md`](../../../skill/README.md) | G | Copy as is. |
| R34 | Explain each issue in plain words before work | [`skill/aa-session/SKILL.md`](../../../skill/aa-session/SKILL.md) | G | Copy as is. |

## Governance

### Decisions

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| V1 | When to write an ADR; technology selection frame | [`skill/ai-nghiep/references/adr.md`](../../../skill/ai-nghiep/references/adr.md) | G | Copy as is. |
| V2 | Locked decisions list, reopened only with new evidence | [`skill/ai-nghiep/references/adr.md`](../../../skill/ai-nghiep/references/adr.md) | P | Empty list per project. |
| V3 | Source precedence: ADRs over standards over decisions over handbook over skills | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §1.3<br>[`docs/agents.md`](../../../docs/agents.md) | G | Copy as is. |
| V4 | Tech lead decision log, each decision with where it is enforced | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §10 | G | Copy as is. |
| V5 | Change the canonical source first, then the summaries | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §1.4 | G | This is the GitLab handbook-first rule. |
| V6 | 'Do not do now' list with a reason per item | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §9.3 | G | Each project keeps its own list. |

### Change control

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| V7 | Merge rights by phase: agent self-merges on green during dev; the tech lead approves risky classes from first prod | [`docs/architecture/data-standards/02-data-management.md`](../../../docs/architecture/data-standards/02-data-management.md)<br>[`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §6.5 | G | Copy as is; it is ITIL's 'standard change' in plain words. |
| V8 | Who approves what, per change type | [`docs/architecture/data-standards/02-data-management.md`](../../../docs/architecture/data-standards/02-data-management.md) | G | Becomes part of the RACI. |
| V9 | Independent agent review for risky PRs (maker-checker for agents) | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md)<br>[`.claude/agents/kiro-reviewer.md`](../../../.claude/agents/kiro-reviewer.md) | G | Copy as is. |
| V10 | Maker-checker on business data: a second person publishes prices | [`docs/adr/0005b-price-versions.md`](../../../docs/adr/0005b-price-versions.md) | G | Extend to settings changes and data fixes (gap). |
| V11 | An agent's own output is not evidence; the judge differs from the writer | [`skill/ai-nghiep/SKILL.md`](../../../skill/ai-nghiep/SKILL.md) | G | Copy as is. |
| V12 | Agents push and merge as a GitHub App; a bot merges generated PRs | [`docs/adr/0011-github-app-identity-and-merge-rights.md`](../../../docs/adr/0011-github-app-identity-and-merge-rights.md)<br>[`docs/security/github-apps.md`](../../../docs/security/github-apps.md) | G | Copy as is; ADR 0011 is still Proposed (gap). |
| V13 | Agents never scale, stop or start infrastructure | [`skill/ai-nghiep/SKILL.md`](../../../skill/ai-nghiep/SKILL.md) | G | Copy as is. |
| V14 | Decisions asked as one page with a proposed answer each; act freely inside agreed limits | [`skill/aa-session/SKILL.md`](../../../skill/aa-session/SKILL.md) | G | Write it down as PRINCE2-style tolerances (today partly in private memory). |

### Data, security and AI

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| V15 | Schema ownership and the migration order (migration PR, copy, apply, schema dump, code) | [`docs/database/schema-ownership.md`](../../../docs/database/schema-ownership.md)<br>[`docs/ops/runbooks/db-migrate.md`](../../../docs/ops/runbooks/db-migrate.md) | P | Single-repo projects skip the copy step. |
| V16 | PII rules and a hook that keeps agents off personal rows | [`docs/architecture/data-standards/02-data-management.md`](../../../docs/architecture/data-standards/02-data-management.md) §6<br>[`.claude/hooks/pilot-pii-guard.sh`](../../../.claude/hooks/pilot-pii-guard.sh) | G | Copy as is. |
| V17 | Quarterly access review, break-glass with review after use | [`docs/templates/access-review.md`](../../../docs/templates/access-review.md)<br>[`docs/ops/runbooks/break-glass.md`](../../../docs/ops/runbooks/break-glass.md) | G | Copy as is. |
| V18 | AI use register with OWASP LLM Top 10 map and output marking | [`docs/architecture/ai-use-register.md`](../../../docs/architecture/ai-use-register.md) | G | Copy as is. |
| V19 | LLM change governance: prompt register ID, eval run and cost in the PR, revert on a failed verdict | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md)<br>[`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §5.7 | G | Copy as is. |
| V20 | Every threshold editable by the administrator; literals or env vars alone do not count | `apps/AA-CIS-App/CONTEXT.md` ("Settings registry: every key ships its guide")<br>Linear AA-1096 | G | Write the rule into the ecosystem standards for every app; today it is a CIS rule and an open issue (gap 7). |
| V21 | Repo visibility and paid plans decided by ADR | [`docs/adr/0014-repo-visibility-and-github-plan.md`](../../../docs/adr/0014-repo-visibility-and-github-plan.md) | P | Decision template. |

### Cost

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| V22 | Quote the monthly cost and get an explicit yes for each paid item | [`docs/ops/finops.md`](../../../docs/ops/finops.md) | G | Copy as is; it is a PRINCE2 cost tolerance. |
| V23 | Paid run ladder: about 3, then at most 50, never the whole set without approval | [`docs/architecture/data-standards/02-data-management.md`](../../../docs/architecture/data-standards/02-data-management.md) §10 | G | Copy as is. |
| V24 | Cost line in every PR; scale only on a measured trigger, cheapest lever first | [`.github/pull_request_template.md`](../../../.github/pull_request_template.md)<br>[`docs/architecture/data-standards/03-scaling.md`](../../../docs/architecture/data-standards/03-scaling.md) | G | Copy as is. |

## Management

### Planning

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| M1 | Operating model: Kanban queue, DevOps, trunk-based, ADLC | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §2.1 | G | Copy as is. |
| M2 | 12-stage lifecycle from idea to telling the business | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §3 | G | Extend at both ends: discovery before stage 1, retirement after stage 9. |
| M3 | Living backlog: ordered queue, time-gated checks, items waiting on the tech lead | [`docs/backlog/README.md`](../../../docs/backlog/README.md) | G | Template. |
| M4 | Master plan tracker (plan.json and an HTML page) with milestones, Done-when and risks | [`docs/backlog/tracker/README.md`](../../../docs/backlog/tracker/README.md)<br>[`docs/backlog/tracker/plan.json`](../../../docs/backlog/tracker/plan.json) | P | Schema and page reused; the sync tool reads the tracker named in the config. |
| M5 | One-way sync from the issue tracker to the plan | [`tools/linear/plan_sync.py`](../../../tools/linear/plan_sync.py) | P | Adapter per tracker. |
| M6 | Platform roadmap with keys and a decisions log | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §9 | P | Empty table per project. |

### Issue tracking

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| M7 | Ask before creating; duplicate check; Problem / Scope / Done-when template; one project; priority scale | [`skill/aa-linear-issue/SKILL.md`](../../../skill/aa-linear-issue/SKILL.md) | P | Generic skill; project names become parameters. |
| M8 | Free-plan quota: one issue per deliverable slice, export closed issues to the repo, then archive | [`tools/linear/linear_export.py`](../../../tools/linear/linear_export.py) | P | Optional module, Linear Free only. |
| M9 | Verify the issue identity before writing; Refs, never Fixes / Closes | [`skill/aa-linear-issue/SKILL.md`](../../../skill/aa-linear-issue/SKILL.md)<br>[`.github/workflows/pr-title.yml`](../../../.github/workflows/pr-title.yml) | G | Copy as is. |
| M10 | Done audit: issues moved to Done without evidence are reopened | [`tools/linear/done_audit.py`](../../../tools/linear/done_audit.py) | P | Adapter per tracker. |
| M11 | Scope found mid-work goes to a new linked issue | [`skill/aa-linear-issue/SKILL.md`](../../../skill/aa-linear-issue/SKILL.md) | G | Copy as is. |

### Reporting and stakeholders

| # | Practice | AA source | Class | What the generic version must change |
|---|---|---|---|---|
| M12 | Business updates: draft, tech lead approves, then post; product progress only; batch at session end | [`skill/aa-jira-update/SKILL.md`](../../../skill/aa-jira-update/SKILL.md) | P | Generic 'business update' skill; channel is a parameter. |
| M13 | Business versus tech decision split; first check whether a system change removes the question | [`skill/aa-jira-update/SKILL.md`](../../../skill/aa-jira-update/SKILL.md) | G | Copy as is. |
| M14 | Stakeholder voice guide and vendor handling | [`skill/ai-nghiep/references/stakeholders-english.md`](../../../skill/ai-nghiep/references/stakeholders-english.md) | P | Structure reused; names removed. Add a vendor selection checklist (gap). |
| M15 | Report and KPI registries, linted | [`docs/reports/catalog.yaml`](../../../docs/reports/catalog.yaml)<br>[`docs/reports/kpis.yaml`](../../../docs/reports/kpis.yaml) | G | Copy as is. |
| M16 | Monthly capacity and cost review | [`docs/templates/capacity-review.md`](../../../docs/templates/capacity-review.md)<br>[`docs/templates/cost-report.md`](../../../docs/templates/cost-report.md) | G | Copy as is. |
| M17 | Audits folder per session and artifact registry | [`docs/artifacts/README.md`](../../../docs/artifacts/README.md) | G | Copy as is. |
| M18 | Engineering handbook linking every canonical source | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) | G | Becomes the playbook's front page. |
