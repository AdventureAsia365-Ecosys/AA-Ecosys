---
id: GUIDE-03
title: Glossary
description: Delivery, operations, data and AA-Ecosys terms, what each means and where each shows up in our system.
type: reference
status: active
owner: nghiep
audience: [owner, engineer, devops, cto, cio, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-28
review_every_days: 180
related: [CAT-00, TPL-02]
---

# Glossary

Terms used across AA-Ecosys docs. Built from the S243 SDLC guide §8 and extended with program terms. Use the
English term in technical docs and keep it the same everywhere ([STYLE](STYLE.md#voice-and-structure)). Add a term
in the same PR that first uses it. The Vietnamese version of this page, with the Vietnamese term for each entry, is
[glossary.vi.md](glossary.vi.md).

## Process and delivery

| Term | Meaning | In AA-Ecosys |
|---|---|---|
| SDLC | The life of software from idea to retirement. | Plan, build, verify, release, operate, retire. |
| ADLC | Our name for the SDLC plus control of AI agents and the life cycle of LLM features. | Kiro or a subagent writes code, Claude Code gates; writer/judge prompts have evals. |
| Trunk-based development | Short branches merged often into one always-deployable branch. | `main` in the app and Infra repos, `master` in root (ADR-2026-023). |
| Pull request (PR) | A proposed change where review and CI run. | Squash merge, body carries `Refs AA-xxx`. |
| CI (continuous integration) | Build and test every change automatically. | `ci.yml` in every app repo (for CIS: Lint, Security Audit, Unit Tests, Integration Tests, Docker Build Check, Frontend Build, Frontend Lint). |
| CD (continuous delivery / deployment) | Ship a change that passed CI to an environment automatically. | `deploy-dev.yml` (CIS), `deploy-lambdas.yml` (TripPlanner). |
| Required checks / branch protection | Checks that must be green before a merge. | Branch protection on the four app repos (CIS 9 checks, Booking 7, TripPlanner 5, Partner 10, read 2026-10-28). Root and Infra have none. |
| Deploy gate | CI step that blocks a backend deploy while a rerun wave is open or a deploy-blocking job of that app runs or is due (C6.3a, AA-993 G5). | CIS: open wave or `data_erasure`, `s1_batch_ingest`, `writing_memory_r2`, `writing_memory_shadow`; Booking: the two retention kinds; Partner: none today (`crm_dispatch` stopped blocking in AA-993 G4b). Other queued/running jobs are released and re-claimed. Override is the tech lead's call. |
| Definition of Ready (DoR) | What an issue needs before work starts. | [`templates/definition-of-ready.md`](templates/definition-of-ready.md). |
| Definition of Done (DoD) | What must be true to call work done. | `skill/aa-ship`: merged, CI green, rollout COMPLETED, verified live. |
| Kanban | Pull work from one ordered queue with a work-in-progress limit, no sprints. | The live backlog plus sessions of 3 to 5 issues. |
| Change record | The written trace of a change, its risk and its rollback. | The PR itself; risky classes get `kiro-reviewer`. |
| DORA metrics | Deploy frequency, lead time, recovery time, change-fail rate, rework rate. | Later (U-47, at first prod). |

## Versions and releases

| Term | Meaning | In AA-Ecosys |
|---|---|---|
| Conventional Commits | Commit subject format `type(scope)!: subject`. | `fix: excel price mapping`, body `Refs AA-26`. |
| SemVer | `MAJOR.MINOR.PATCH` by compatibility. | App versions from release-please (AA-891), for example CIS `v0.13.0` (2026-10-28). |
| CalVer | Version by date. | Optional for Infra. |
| Git tag | A fixed label on one commit. | One `vX.Y.Z` tag per release of each app repo (AA-891). |
| GitHub Release | A page for a tag with notes and artifacts. | Created by release-please (AA-891). |
| CHANGELOG | Human-readable list of changes per version. | `CHANGELOG.md` per repo (AA-891). |
| Release note | Business summary of a release. | Jira draft for the business owner, [template](templates/release-note.md). |
| release-please | Bot that opens a release PR with the version bump and changelog and tags on merge. | AA-891 (U-47, pulled early). |
| Immutable image tag | An image tag that cannot be overwritten. | ECR `dev-<sha>`, IMMUTABLE, last 30 kept (CIS). |
| Task definition revision | A numbered ECS run configuration. | Rollback points the service at the previous revision (`skill/aa-ship` §5). |
| Rolling deploy | Replace tasks gradually. | ECS default for CIS, Booking and Partner. |
| Circuit breaker (ECS) | ECS stops and rolls back a deploy whose tasks do not become healthy. | Enabled on the ECS services in Terraform. |
| Blue/green, canary | Switch traffic between two stacks / shift a percentage gradually. | Not needed yet. |
| Rollback / roll-forward | Return to the previous version / ship a fix. | `skill/aa-ship` §5; rollback runbooks (OPS-02). |
| Build once, deploy many | One artifact, same digest in every environment; only config differs. | `dev-<sha>` image, later promoted to prod. |
| Feature flag | Switch a feature without a deploy. | Register in `docs/ops/feature-flags.md` (OPS-06); tenant-pool flags are a security control. |
| Deploy vs release | Code running vs users seeing it. | Turn a flag on for one tenant first. |
| Expand / contract | Change a schema or API in three steps so old and new run together. | Migrations and contract versions. |
| Breaking change | A change that breaks existing clients. | Removing a response field; caught by oasdiff (AA-899). |
| OpenAPI | Machine-readable REST API spec. | `/booking/openapi.json`; export for CIS and Booking in AA-899. |
| Deprecation / Sunset header | HTTP headers that announce an API is going away and when. | RFC 9745 / RFC 8594; with ADR 0013 (U-44). |

## Documentation

| Term | Meaning | In AA-Ecosys |
|---|---|---|
| Docs-as-code | Docs in the repo, changed in the same PR, checked by CI. | This catalog; lint in AA-888. |
| Diátaxis | Four doc types: tutorial, how-to, reference, explanation. | The `type` field of the [front-matter](templates/frontmatter.schema.json). |
| Doc catalog | The list of every maintained doc, owner and cadence. | [`docs/README.md`](README.md). |
| Front-matter | YAML block at the top of a page with its metadata. | Required: id, title, type, status, owner, last_reviewed. |
| Runbook / playbook | Exact steps for one task / strategy for one kind of incident. | `docs/ops/runbooks/`, `docs/ops/playbooks/`. |
| ADR | Context, decision and consequences of an architecture choice. | `docs/adr/` (root), app and Infra repos. |
| CONTEXT.md | Per-repo page on stack, boundaries and ownership; read before designing. | CIS, Booking, TripPlanner, Partner, Infra. |
| C4 model | Architecture diagrams at four zoom levels; we use L1 context and L2 containers. | `ecosystem-architecture.md`. |
| llms.txt | A Markdown index that tells AI agents what to read. | [`docs/llms.txt`](llms.txt). |
| Freshness | Whether `last_reviewed` is inside `review_every_days`. | Weekly report with AA-888. |
| Postmortem (blameless) | Incident analysis without blame, ending in action items. | [`templates/postmortem.md`](templates/postmortem.md); lesson line in `lessons.md`. |

## Infrastructure and operations

| Term | Meaning | In AA-Ecosys |
|---|---|---|
| acc2 / acc3 | The two AWS accounts of the ecosystem. | acc2 = all infrastructure; acc3 = the LLM satellite (Amazon Bedrock). acc1, a personal account, left the ecosystem in S255 (AA-998): there is no cross-account LLM fallback. Map: [onboarding](onboarding.md#account-map). |
| Infrastructure as Code (IaC) | Infrastructure declared in code. | Terraform in AA-CIS-Infra. |
| Terraform state / lock file | Record of real resources / pinned provider versions. | Remote state on S3; `.terraform.lock.hcl`. |
| Terraform drift | Real infrastructure differs from code or state. | Apply only from `main` through `terraform-apply.yml`. |
| OIDC (CI to AWS) | CI gets short-lived AWS credentials without static keys. | Trust limited to `refs/heads/main` (AA-866). |
| ECS exec, S3-mediated | Run a script inside the CIS container: upload to S3, presign, curl it in, run with python3. | The standard way to reach the private RDS (D-07); sessions are logged. |
| Break-glass | An emergency credential or switch used only when normal access fails. | Cognito `breakglass` user with TOTP; RDS master (DM-8.9). Runbook OPS-10. |
| Observability | Understanding the system through logs, metrics and traces. | CloudWatch, Sentry (CIS, Booking, TripPlanner), admin pages. |
| Log retention | How long logs are kept. | Security logs (flow, WAF, ECS exec, PostgreSQL) 365 days, app logs 30 days (D-09, AA-872). |
| SLI / SLO / SLA / error budget | Measure / target / contract / allowed failure share. | SLOs with first prod (AA-880, U-49). |
| RPO / RTO | Acceptable data loss / downtime. | Targets in DM-9.6; Dev restore drills took about 22 minutes (S241) and 21 minutes (S249). |
| PITR | Restore a database to any moment in its retention window. | Dev RDS keeps 7 days; prod will keep 14 (C7.2b). |
| Restore drill | Practice restore with a recorded RTO. | Dev: when the procedure changes and once before prod; quarterly in prod (DM-9.3). |
| FinOps / unit cost | Managing cloud spend / cost per business unit. | USD LLM per published tour; monthly review (FIN-02). |
| Cost allocation tag | A tag Cost Explorer can split spend by. | `App` (active in Billing since 2026-10-15) and `Environment` (DM-10.1). |
| Ledger | A table that records every paid call with its cost. | `shared.llm_call_log`, `shared.decision_log`, `shared.dfs_call_log` (DM-10.4). |
| SBOM | List of every library and version in an artifact. | syft in CIS CI (AA-177). |
| SLSA / provenance | Supply-chain trust levels / proof of who built what from which commit. | Later (U-43, first prod). |

## Data

| Term | Meaning | In AA-Ecosys |
|---|---|---|
| Migration | A numbered SQL file that changes the schema. | Keys `NNN` (CIS), `tp-NNN`, `bk-NNN`, `crm-NNN`; applied by Infra DB Migrate. |
| Forward-only | Never roll a schema back; undo with a new migration. | DB Migrate rule; the old app must run on the new schema. |
| Idempotent | Running twice has the same effect as once. | `ON CONFLICT DO NOTHING` in `schema_versions`. |
| Schema owner | The only repo that writes migrations and rows for a schema. | [`schema-ownership.md`](database/schema-ownership.md); registry `db/owners.yaml` in Infra. |
| Kernel schema | `shared`: tenants, destinations, countries, LLM gateway, `schema_versions` only. | DM-1.5; app tables go to the owner's schema. |
| Contract (event / API / view) | Versioned interface between apps. | `docs/contracts/`, `catalog.*` views (ADR 0008). |
| RLS | PostgreSQL row-level security that filters rows per tenant. | Tenant pool and isolation probe (AA-817, U-16). |
| Tenant pool | DB connection pool whose role is bound by RLS. | Fail-closed globally (D-12). |
| Dead Table Registry | Tables kept but no longer written, with their removal plan. | ARCH-09 (AA-850). |
| PII | Data that identifies a person. | Dev holds test data only (D-01); `pii:` column tags (DM-6.1, AA-877). |

## LLM operations

| Term | Meaning | In AA-Ecosys |
|---|---|---|
| LLMOps | Versioning prompts and models, evals, quality and cost monitoring. | APP-06 (AA-900, narrowed). |
| Model Gateway | The single seam for paid model calls. | `LLMClient.generate()` writes `shared.llm_call_log`. |
| Writer / judge / validate | The three LLM roles in the pipeline. | `role` in `shared.llm_call_log`. |
| Eval / golden set | A fixed sample to score LLM quality before changing a prompt or model. | About 100 samples (AA-729); runs by hand or dispatch (D-23). |
| Shadow run | Run a new model or route next to the live one without serving its output. | `shared.llm_shadow_log`. |
| Jev | The external decision service that gives verdicts on content. | `decide()` writes `shared.decision_log`. |
| Atom | A reusable piece of tour content produced by the A-series pipeline. | Read through `acp_contract.v_active_tour_atoms`. |
| A-series / T-series | Admin pipeline stages A0-A4 / tenant stages T0-T11. | CIS CONTEXT.md. |

## Program and governance

| Term | Meaning | In AA-Ecosys |
|---|---|---|
| Dev phase | Today: only a Dev environment, no real users, test data only. | Agents merge after green CI (D-13; DM-11.5 in v1.1). |
| Prod | The future production environment. | Separate RDS instance on acc2 (ADR 0001, C7.2a, D-17); dated at go-live (AA-880). |
| Data standards | Binding MIG-x (Part A), DM-x (Part B) and C-x (Part C) rules for the shared RDS. | [`docs/architecture/data-standards/`](architecture/data-standards/README.md), version 1.6 (2026-10-28). |
| U-xx / D-xx | S241 roadmap items / the tech lead's recorded decisions. | [Handbook §9–§10](engineering-handbook.md#9-roadmap); D-xx record in `docs/sessions/2026-10-17-S241-decisions.md`. |
| Session (`S<nnn>`) | One numbered working session with a log. | `docs/sessions/`, Notion memory. |
| CODEOWNERS | GitHub file that assigns required reviewers by path. | Later, needs a separate agent identity (U-25). |
| NIST SSDF (SP 800-218) | Secure software development practices in four groups. | Reading checklist, later. |
| Workforce pool | The Cognito user pool for staff sign-in. | CIS staff sign in with an e-mail code (ADR 0006a). |
