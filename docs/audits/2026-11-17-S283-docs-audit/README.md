---
id: CAT-00-docs-audit-s283
title: Docs audit 2026-11 (S283)
description: Every living doc page in the six repos checked against the live system on 17/11/2026 (AA-1124), with a verdict per page and PR-sized fix batches for AA-1118.
type: report
status: draft
owner: tech-lead
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-17
related: [CAT-00, TPL-02, AA-1124, AA-1118, AA-1109]
---

# Docs audit 2026-11 (S283)

Date: 17/11/2026 (S283). Agent: Claude Code (workflow lanes), read-only. Issue: AA-1124. Fixes go to AA-1118.
Cost: 0 USD (repo reads, read-only AWS CLI, public curl, `gh api` reads).

No account ID, ARN, resource ID, secret, e-mail address or personal name is on this page or in `rows.json`. Where a
page under audit quotes a person, the quote is replaced by the role (`<tech lead>`, `<business owner>`). Local
absolute paths were turned into repo-relative paths.

Files in this folder:

| File | What |
|---|---|
| `README.md` | This report |
| `rows.json` | One record per audited page: verdict, severity, stale claims (line, claim, live truth, evidence), broken links, contradictions, proposal, notes |
| `tom-tat.vi.md` | Short Vietnamese summary for the tech lead |

## 1. Summary

401 records cover the 361 pages of the inventory plus 40 Vietnamese siblings that got a record of their own (the other `.vi.md` siblings are covered in the English record). They hold 908 stale claims, 64 broken links and 226 contradictions.

- **24 pages are wrong** (following them gives a wrong result or an unsafe step) and **222 are partly stale**; 10 are orphans (pre-build or historical pages with no live reader), 1 has only broken links, 144 are current.
- Severity: **35 high**, 121 medium, 108 low, 137 none.
- The drift is not random. Eight changes of the last four weeks explain most of it (records touched):
  - acc1 serves Bedrock first since S278 (AA-1095), acc3 is the fallback: 66 records still say "acc3 only" or "acc1 retired".
  - B2C half retired (AA-1046, ADR 0019 d8/d11): 47 records still describe the TripPlanner → Booking inquiry, customers, `bk_notify_email` or traveller sign-in.
  - Vercel retired for every frontend (AA-911, AA-1038, AA-979): 45 records.
  - Terraform moved into `modules/environment/` (AA-1004): 26 records, some with `-target`/`-replace` addresses that no longer match.
  - Portal merged into the CRM web (AA-1036 R3): 20 records point at `portal/` or `aa-crm-dev-portal`.
  - Root and Infra repos are public (ADR 0014 amendment): 17 records still say "private".
  - Dev RDS backups are 14 days (ADR 0019 d16): 13 records say 7 days.
  - Migrations ship in the app PR (ADR 0017/0017a): 9 records still describe the hand-copy + hand-apply flow.
- Agent instruction files (`CLAUDE.md`, `.kiro/steering`, skills, sub-agent definitions) carry 16 of the 35 high findings.
  They are loaded into every session, so they are the first batch to fix.

### Per verdict and severity

| Verdict | high | medium | low | none | Total |
|---|---|---|---|---|---|
| wrong | 20 | 4 | 0 | 0 | 24 |
| partly_stale | 15 | 114 | 93 | 0 | 222 |
| orphan | 0 | 3 | 7 | 0 | 10 |
| broken_links_only | 0 | 0 | 1 | 0 | 1 |
| current | 0 | 0 | 7 | 137 | 144 |
| **Total** | 35 | 121 | 108 | 137 | 401 |

### Per repo

| Repo | Records | wrong | partly_stale | orphan | broken_links_only | current | high | medium | low |
|---|---|---|---|---|---|---|---|---|---|
| AA-Ecosys (root) | 314 | 11 | 170 | 1 | 1 | 131 | 21 | 92 | 77 |
| AA-CIS-App | 31 | 5 | 19 | 0 | 0 | 7 | 4 | 10 | 10 |
| AA-Booking | 11 | 0 | 10 | 0 | 0 | 1 | 1 | 5 | 4 |
| AA-Partner | 9 | 0 | 6 | 0 | 0 | 3 | 0 | 2 | 4 |
| AA-TripPlanner-Web | 22 | 6 | 6 | 9 | 0 | 1 | 7 | 6 | 8 |
| AA-CIS-Infra | 14 | 2 | 11 | 0 | 0 | 1 | 2 | 6 | 5 |

Root pages are the most numerous; the TripPlanner repo has the worst ratio (15 of 22 records wrong or orphan), because its agent files, Kiro steering and docs still describe the B2C MVP of September 2026.

## 2. Method

1. **Inventory.** Every tracked Markdown or YAML doc page in the root repo and the five child repos (`main`/`master`
   heads of 17/11/2026), minus records and generated files (section 5). 361 pages, split into 19 chunks by area.
2. **Facts snapshot.** One read-only lane gathered the live state first (17/11/2026): ECS services and task
   definitions, public health and readiness endpoints, latest migration per owner, job kinds from code, settings
   registry, CI workflows and required checks, Terraform roots, Lambda and edge, plans and prices, ADR index, account
   roles, and a list of retired things. The snapshot stays in the session scratch folder because it names AWS
   resources; nothing from it that is not public-safe is copied here.
3. **Audit pass.** One lane per chunk read each page in full and checked every factual claim (paths, commands,
   service names, versions, numbers, statuses, links) against the snapshot, the code on `main`, the live schema
   reference (Verified 2026-11-16) and, where needed, a fresh read-only call (AWS CLI single-line on the Dev account,
   `curl` of public hosts, `gh api` GET). Each page got a verdict:
   - `wrong`: following the page gives a wrong result or an unsafe step;
   - `partly_stale`: some claims are out of date, the page is still usable;
   - `orphan`: pre-build or historical page with no live reader and no banner saying so;
   - `broken_links_only`: facts right, links broken;
   - `current`: no stale claim found.
   Severity: `high` = an agent or an operator acting on it would do harm or a legal/security statement is false;
   `medium` = misleads a reader; `low` = cosmetic or history; `none` = current.
4. **Verification pass.** Every `high` record and the doubtful ones were re-checked by a second lane that tried to
   refute each claim (their notes say "Re-check"). Refuted claims were dropped (for example the TripPlanner
   runbook's acc3 caveat, which is still true for TripPlanner); wrong line anchors were corrected; several records were
   lowered from high to medium where the harm was smaller than first judged.
5. **Report pass (this page).** The records were checked once more for shape: no duplicate path, every path exists,
   every inventory page has a record, and the redaction rules above hold.

Limits: no page was changed. Some live reads were not possible read-only (IAM reads are blocked for sub-agents,
the Organizations read needed an expired SSO session, Mapbox console, live `allowed_scopes` values); records say so
where it matters. Line numbers are those of `main` on 17/11/2026.

## 3. Top findings

High severity first. Each item names the evidence; full detail is in `rows.json`.

### 3.1 High: agent instruction files tell agents to do the wrong thing

| Page | What is wrong | Evidence |
|---|---|---|
| `infra/AA-CIS-Infra/.claude/CLAUDE.md` | Says `accounts/acc1-bedrock` is retired and "its only remaining step is a human terraform destroy". It is the live first Bedrock route; also recommends the forbidden `export $(…)` credential recipe. | `accounts/aa365/bedrock_satellite_assume.tf` (statement for acc1, AA-1095); root steering MFA rule (S244) |
| `skill/ai-nghiep/references/aws.md` | Account map without acc1/acc4, "never add acc1 back", 5 ECS services, no cross-account fallback. | ADR 0001a Note S278; 8 ECS services live |
| `apps/AA-CIS-App/.claude/skills/ecs-exec-pattern.md`, `.claude/agents/db-auditor.md` | Script template reads the master DSN secret inside the container; the task role is denied it since X1 S18/S19, so scripts fail with AccessDenied. | Infra `modules/ecs/main.tf` deny statement; `skill/aa-cis-schema/references/ecs-exec.md` uses `DATABASE_URL` |
| `apps/AA-CIS-App/.claude/CLAUDE.md` | Admin on Vercel, hand-copy + hand-apply migrations, 5 required checks, old deploy-gate rule. | 10 required checks + merge queue; ADR 0017/0017a; `deploy_job_guard.sh` |
| `.claude/CLAUDE.md` (root) | Admins on Vercel, TripPlanner "B2C … 2 Lambda", acc1-bedrock root "destroyed", ADR range 0001–0008, 7 services. | 8 ECS services; ADR files to 0022 |
| `.claude/skills/kiro-delegate/SKILL.md` (+ `brief-template.md`) | Kiro's loop waits for a UI smoke on a Vercel preview that never runs. | `ui-smoke.yml` runs only after the ECS deploy; no preview exists |
| `skill/aa-ui-verify/SKILL.md`, `skill/aa-ecosys-repos/*` | Send UI work to `AA-Partner/portal/` (gone), Booking E2E "no account", Terraform in `accounts/aa365/booking.tf`. | AA-1036 R3; `tools/uat/lib/signin.cjs`; `modules/environment/` |
| `apps/AA-TripPlanner-Web/.claude/CLAUDE.md`, `.kiro/steering/{product,structure,tech}.md` | Describe the September B2C MVP: extraction pipeline, `itinerary_components`, `shared.destinations`, 2 Lambdas, hard-coded model ids; `tech.md` gives an unsafe MFA recipe. | tp-018, CIS 270, 3 Lambdas live, gateway route views |
| `apps/AA-Booking/.claude/CLAUDE.md` | "A human merges after the 5 required checks"; env vars set by hand. | 9 required checks + merge queue; S241 D-13 |

### 3.2 High: runbooks and legal pages with wrong or unsafe steps

| Page | What is wrong | Evidence |
|---|---|---|
| `docs/legal/dsar-erasure-runbook.md` | Says the offboarding saga is planned and to use a CIS-only procedure; says bk-045 dropped `booking.customers` and that the lookup reads `booking.retired_b2c_record`. The saga is built and drilled (15/11), the customer tables still exist and the archive table does not: the lookup would fail and miss customer rows. | saga commits in every deployed SHA; `045_finance_costs_orders_profit.sql`; schema reference (bk-058) |
| `docs/legal/consent-capture-query.md` | Skips live Booking consent columns (same bk-045 error); step 1 expects a `tripplanner.customers` row the B2B flow never writes. | schema reference; TripPlanner `assembly/handler.py` |
| `docs/ops/runbooks/crm-keys.md` | `-target=aws_kms_key.crm_*` matches nothing after the module move: a policy check reports "No changes" while drifted, and a restore applies nothing. | `accounts/aa365/environment.tf` moved blocks; `tools/terraform/crm_key_policy_diff.py` |
| `docs/ops/runbooks/secret-rotation.md` | Class 5 `-replace=random_password.tripplanner_api_key` matches nothing (key not rotated); Vercel step instead of an ECS redeploy. | `environment.tf` moved block; `tripplanner_web.tf` secret mapping |
| `docs/ops/runbooks/pilot-agency-onboarding.md` | Says no CIS/TripPlanner tenant restore and no cross-app erasure; tells the operator to erase by hand per app, bypassing the saga's DRY RUN and approval guards. | restore drills 13/11 and 15/11; AA-1093 Done S281 |
| `docs/ops/playbooks/5xx-spike.md`, `llm-cost-spike.md`, `docs/ops/README.md` | CRM has "no runbook, fall back to Vercel"; Bedrock spend "on acc3 only" (misses the acc1 bill and budget); admin services sent to a rollback helper that refuses them. | `tools/ops/ecs_rollback.sh`; acc1 cost guard (Infra #804) |
| `docs/guides/booking-admin-runbook.md`, `tripplanner-runbook.md`, `cis-admin-runbook.md` (+ `.vi.md`) | Describe the B2C inquiry, customer invoices, traveller sign-in, the old role set and menu. | `AA-Booking backend/app/b2c.py`; `frontend/lib/rbac.ts`, `adminIa.ts` |
| `apps/AA-TripPlanner-Web/docs/smoke-test-runbook.md`, `e2e-uat-guide.md` | Apply migrations with `psql` on the shared RDS and run a deleted extraction module. | DB Migrate rule; `backend/extraction/` holds only a 410 stub |

### 3.3 High: false statements about data protection and security posture

- `apps/AA-CIS-App/docs/adr/0012-llm-data-scopes-per-stage.md`: states tenant writers are `aws_only`, so the Anthropic
  API is "safe". CIS 344 and 366 gave every writer/judge/validate stage `{aws_only, vendor_direct}`; tenant content can
  reach vendor APIs after AWS. Same gap in `docs/architecture/ai-use-register.md` (feeds the tenant terms provider list).
- `infra/AA-CIS-Infra/CONTEXT.md` (19 stale claims): says the ALB admits only :80 from the VPC; it has an HTTPS :443
  listener open to the internet for the staff hosts. Also SES "sandbox", nameservers "not switched", no Anthropic key.
- `docs/guides/cio.md`: GuardDuty "Done, detector live" (no detector exists, paid observability is on hold), acc1
  removed, 7-day backups.

### 3.4 Public-repo hygiene found on the way (not staleness)

These pages print things the public-repo rule forbids. They are listed by location only:

- personal e-mail addresses: `apps/AA-TripPlanner-Web/.kiro/specs/tripplanner-mvp/design.md` (line 224),
  `apps/AA-TripPlanner-Web/docs/task-assessment.md` (line 78), `docs/ecosystem-architecture.md` (line 422);
- resource identifiers: `apps/AA-CIS-App/README.md` (REST API ID, line 17), `infra/AA-CIS-Infra/CONTEXT.md` (REST API
  IDs), `infra/AA-CIS-Infra/tools/identity/README.md` (user pool ID and an admin e-mail),
  `infra/AA-CIS-Infra/accounts/management/README.md` (Identity Center portal identifier),
  `apps/AA-Booking/frontend/README.md` (app client ID, line 47);
- stray agent notes inside ADRs: `docs/adr/0006b-partner-pool-and-mfa.md` lines 131-132, `docs/adr/0008-new-app-integration-and-data-platform-rules.md` lines 89-90;
- personal names where a role is meant: root `README.md` line 69, `apps/AA-Booking/CONTEXT.md` around line 826,
  `apps/AA-TripPlanner-Web/README.md` line 152, `.kiro/steering/tech.md` line 89.

### 3.5 Contradictions that need a decision, not just an edit

- **TripPlanner traveller sign-in.** ADR 0019 d11 (S278 amendment) says no page offers traveller Sign in, but
  `/sign-in` serves a live form and the `/trips` empty state shows a Sign in button; `docs/catalogue/features.yaml`
  TP-F004 is `live`. Either the code removes them or the ADR records that they stay.
- **Root repo required checks.** The steering file, ADR 0011a d5, ADR 0014 and `testing-strategy.md` say root and
  Infra have no required checks; both have active rulesets (root "Catalogue guard", Infra five checks).
- **ADR statuses.** 0005b (built and served), 0010a (implemented), 0011a (acceptance condition met in S259) still say
  Proposed; 0011 and 0014 say both Accepted and "stays Proposed".
- **Academy.** `docs/backlog/README.md` reports AA-1105 done, but ADR 0022 decisions 3, 5 and 10 (CIS admin link,
  Platform › Academy page with `learn.admin`, `learn_retention` job) are not built.
- **Stripe for agencies.** ADR 0010 d9 says restricted key; the CRM code is Connect Standard (paused) and cites ADR
  0019 b14, which is about AA's own billing.
- **Owner slug.** The front-matter schema says the default owner slug (a first name) stands for the tech-lead
  role; two audit records ask for `tech-lead` instead. One convention should win.

## 4. Proposals ranked by impact

All doc fixes belong to **AA-1118**. One batch = one PR (or one PR per repo where the batch spans repos). Effort:
XS < 1 h, S ≈ half a day, M ≈ one day, L > one day.

| # | Batch | Pages | Repos | Effort | Why first |
|---|---|---|---|---|---|
| 1 | **Public-repo hygiene**: remove the e-mail addresses, resource IDs, stray agent notes and personal names of section 3.4 | ~12 | root, CIS, Booking, TripPlanner, Infra | XS | Exposure in public repos; tiny diff |
| 2 | **Agent files, root**: `.claude/CLAUDE.md`, `skill/ai-nghiep/references/aws.md`, `skill/ai-nghiep/SKILL.md`, `skill/aa-ui-verify`, `skill/aa-ecosys-repos/*`, `skill/aa-ship`, `skill/aa-session`, `skill/aa-cis-schema/*`, `skill/aa-uat-video`, `.claude/skills/kiro-delegate/*`, `.claude/agents/kiro-reviewer.md`, `.kiro/steering/db-schema.md`, `docs/agents.md` | ~20 | root | M | Loaded into every session; 7 high |
| 3 | **Agent files, apps**: CIS `.claude/CLAUDE.md` + `ecs-exec-pattern.md` + `db-auditor.md` + `code-reviewer.md` + `test-runner.md`; Booking `.claude/CLAUDE.md`; TripPlanner `.claude/CLAUDE.md` + `.kiro/steering/*`; Infra `.claude/CLAUDE.md` | 13 | CIS, Booking, TripPlanner, Infra (one PR each) | M | 9 high; ECS-exec scripts fail today |
| 4 | **Legal and data-protection pages**: DSAR erasure runbook, consent-capture query, DPA 11.2/11.4, register (+ regenerate the column inventory), retention log, readiness packet (+ `.vi.md`), AI schedule, annexes 1 and 3, pilot contract set, VN transfer dossier, `ai-use-register.md`; CIS ADR 0012 amendment | ~15 | root, CIS | M | False data-protection statements; DSAR lookup would fail |
| 5 | **Ops runbooks with wrong addresses/steps**: crm-keys, secret-rotation, pilot-agency-onboarding, pilot-rehearsal, 5xx-spike, llm-cost-spike, ops README, rollback-ecs/cis/booking/tp-lambda/terraform, drills README, rollback-game-day, restore-rds-pitr, restore-schema, database-operations, db-migrate, legacy-login-flag, llm-anthropic-api-key, ses-bounce, staff-web cut-over, tenant-restore-drill, queue-stuck, feature-flags, job-kinds (regenerate from code), finops, cost README, incident-response, postmortems README; Infra crm-mail-ingest, `tools/identity/README.md` | ~30 | root, Infra | L (split in 2) | Wrong Terraform addresses give false "No changes"; erasure guidance bypasses guards |
| 6 | **Staff and owner guides (B2B-only, ECS, nav)**: booking-admin, tripplanner, cis-admin runbooks (rewrites), app-access, content-studio, crm-runbook, ai-providers runbook, ceo, cio, cto, devops, new-engineer, all with `.vi.md` in the same PR | 23 | root | L | Read by staff and the business owner |
| 7 | **Account and LLM-route sweep (acc1 first)**: docs/README, STYLE, glossary (+ vi), onboarding (decide acc1/acc4 rows), ecosystem-architecture, engineering-handbook (+ vi), ai-gateway (+ vi), tagging-standard, diagrams (redraw), integrations.yaml (after the route-snapshot refresh), reports catalog/kpis (+ CIS copy), templates cost-report and access-review | ~18 | root, CIS | M | Same wrong fact repeated on every architecture page |
| 8 | **ADR housekeeping**: statuses (0005b, 0010a, 0011, 0011a, 0014, 0021, 0022), pointers (0001, 0001a, 0003a, 0004, 0004b, 0005a, 0006a, 0006b, 0007, 0008, 0008a, 0009, 0010, 0012, 0015, 0016, 0018, 0019), ADR README; CIS ADR README and 0002, 0004–0008, 0010, 0011; Booking/Partner/TripPlanner ADR READMEs and Partner/Booking ADR 0001 | ~40 | all | M | Small edits; amendment headers only, decisions unchanged |
| 9 | **App docs refresh**: Booking CONTEXT/README/api README/figma-coverage/ui-spec/frontend README/tools docs; Partner CONTEXT/README/slo/ADRs/tools docs; TripPlanner README/CONTEXT/jobs-runbook/tools docs; CIS CONTEXT/README/frontend README/api README/eval-runbook/runbooks; Infra CONTEXT (19 claims, ALB statement first)/README/db READMEs/docs | ~35 | CIS, Booking, Partner, TripPlanner, Infra | L (one PR per repo) | CONTEXT.md is the design source agents must follow |
| 10 | **Small factual refresh**: 14-day PITR, 300 USD budget, data-standards (README, Parts A-C), dead-table registry, ERD design pages, schema-ownership, contracts README and three contract pages, backlog §6 + header, tracker README, artifacts README, templates (capacity-review, migration-file, runbook, role-guide, release-note, uat-report, definition-of-ready, contract, README.vi), kit skills, playbook aa-profile/agents, learn README, research READMEs, PRD, tools READMEs | ~45 | root | M | Mostly one-line fixes |
| 11 | **Archive orphans** with a banner or a move to `docs/archive/`: `docs/AAA/erd-v2/`, `job-model-modularization.md`, `t-series-audit-and-plan.md` (root and CIS), CIS `clean-rerun.md`, `at-series-v2-design.md`; TripPlanner `.kiro/specs/tripplanner-mvp/*`, `roadmap.md`, `brand-sync-adventure-asia.md`, `content-handoff/`, `bao-cao-hien-trang-vi.md`, `change-report-mvp-completion.md`, `task-assessment.md`, `architecture-overview.md`; Booking `ui-spec.md` banner | ~18 | root, CIS, TripPlanner | S | Stops agents from reading dead designs |

Suggested order: 1, 2, 3, 4, 5 in the next session (all high findings), then 6-11.

### 4.1 Findings that need a code, config or infra change (not a doc edit)

Ask before opening issues for these (Linear quota). Each is a small change in the named place:

| Finding | Change | Where |
|---|---|---|
| `tools/ops/ecs_rollback.sh` refuses `aa-cis-dev-admin` and `aa-booking-dev-admin` | Add the two services (or document the manual path only) | root `tools/ops/` |
| Retired kind `bk_inquiry_pull` still exempt in deploy and idle gates | Drop it from `DEPLOY_GATE_EXEMPT` and from the idle-exempt lists | AA-Booking `backend/app/jobs/kinds.py`; Infra `db/run_migration.py`, `db/owners.yaml` |
| Booking B2C tables still live although legal pages say they were dropped | Ship the B2C drop migration (next free bk- number, DRY RUN procedure), or keep the docs saying "still live" | AA-Booking migrations |
| TripPlanner `/sign-in` page and `/trips` Sign in button vs ADR 0019 d11 | Remove them or amend the ADR | AA-TripPlanner-Web frontend or root ADR 0019 |
| `tools/finops/monthly_cost_report.py` labels acc1 "retired"; `collect_month.py` has no acc1 reader | Add an acc1 cost line | root `tools/finops/` |
| `docs/generated/llm-routes.snapshot.json` predates the acc1 connection | Refresh the snapshot so the catalogue guard accepts acc1 | root generated file (workflow) |
| Vendored `tools/docs/test_docs_tools.py` diverged (root-only AI-gateway test); Partner copies older; Partner drift loop compares the Booking copy | Move the root-only test out of the shared file, re-sync, add a CI drift check now that root is public | root, Booking, Partner, TripPlanner, Infra `tools/docs/` |
| `aa-ecosys-ci-bot` private key is a repo-level secret on public AA-CIS-Infra | Move it to a main-only environment | GitHub settings (Infra) |
| CI hygiene known-repo list lacks `project-template` (open issue #840) | Add the repo | root `tools/github/ci_hygiene.py` |
| `preview-signin` rulesets still active on CIS and Booking | Delete the rulesets and leftover preview branches | GitHub settings |
| `crm_dev_identity.py web-secret` defaults to `--pool external` | Default to `partner` (or refuse external) | Infra `tools/identity/` |
| `cis-portal` EXTERNAL client still provisioned after P2b | Remove in Terraform | Infra `accounts/aa365/identity.tf` |
| Booking dev server port 3100 vs Cognito callback on 3001 | Align the port | AA-Booking `frontend/package.json` or `lib/cognito.ts` |
| Booking `api-contract.yml` public-path regex still includes `customer/` | Drop it | AA-Booking workflow |
| Booking Trip Cases "Inquiries" tab copy | Remove the B2C UI copy | AA-Booking `frontend/app/(staff)/cases/page.tsx` |
| Learn content review items are never opened; Academy link, team view and `learn_retention` not built (ADR 0022) | Build, or mark the ADR decisions as not built | AA-CIS-App |
| Project kit: template `AGENTS.md` lacks parameters the kit skills name; PII and Stop hooks not shipped | Add the rows / hooks or trim the skills | project-template repo, `skill/kit/` |
| Wrong migration numbers in code comments (`role_config.py:161` "266", Infra `main.tf` "CIS 428"; `dm65_consent_capture.py` docstring bk-045) | Fix the comments | AA-CIS-App, Infra |
| Stale phrases come back after each change | Add a "retired phrase" check (acc3 only, Vercel preview, `portal/`, `bk_inquiry_pull`, 7-day PITR) to `check_docs_text.py`, as the S282 audit proposed | root `tools/docs/` |

## 5. Pages not audited

8769 tracked files were left out on purpose (records, generated pages, assets). Rules:

| Pattern | Files | Reason |
|---|---|---|
| `docs/sessions/** (root)` | 110 | Dated session logs (records, not living docs) |
| `docs/linear-export/** (root)` | 745 | Exported closed Linear issues (records) |
| `docs/audits/** (root)` | 5665 | Dated audit records and evidence (all tracked files incl. images/data) |
| `docs/archive/** (root 17, CIS 3)` | 20 | Archived pages, intentionally historical |
| `docs/implementation-notes/** (root 93, CIS 800, Booking 125, Partner 151, TripPlanner 104, Infra 237)` | 1510 | Per-issue implementation notes (records) |
| `apps/AA-CIS-App/docs/claude_tasks/**` | 74 | Historical agent task prompts / work logs (last touched 19/10/2026) |
| `apps/AA-CIS-App/docs/claude_audit/**` | 74 | Historical per-issue audit write-ups (work logs) |
| `apps/AA-CIS-App/.agents/skills/**` | 98 | Vendored third-party generic agent skills, not AA documentation |
| `apps/AA-CIS-App/docs/investigation/AA-*.md` | 3 | Dated per-issue investigation records |
| `apps/AA-CIS-App/docs/calibration/** (17 md + data files)` | 28 | Calibration / pre-registration measurement records tied to dated runs |
| `docs/architecture/db-schema-reference.md` | 1 | Generated live DB dump; it is the source of truth, not audited |
| `docs/architecture/erd/*.md (live ERDs incl. README)` | 15 | Generated from the live catalog dump by DB Schema Dump workflow (hand-written design ERDs under erd/design are included) |
| `docs/generated/*.md` | 6 | Generated from Terraform / gateway snapshot (alarms, env-config, iam-roles, inventory, llm-routes, network) |
| `**/*.openapi.yaml (root docs/contracts 9, CIS 6, Partner 3)` | 18 | Machine-readable API contracts checked by contract tooling, not prose docs (contract README and .md contracts are included) |
| `docs/contracts/samples/** (json), docs/learn/schema/*.json, docs/templates/frontmatter.schema.json, docs/AAA/figma_AAA/**, docs/architecture/diagrams/* (non-md)` | 300 | Non-page assets: sample payloads, JSON schemas, images/diagram sources |
| `CHANGELOG.md (CIS, Booking, Partner, TripPlanner)` | 4 | Generated by release-please |
| `docs/research/2026-*/** and docs/research/2026-*.md` | 11 | Dated research records (point-in-time findings, incl. a Jira draft) |
| `docs/architecture/ecosystem-review-2026-09.md` | 1 | Dated September 2026 review proposal (record; its decisions live in the ADRs) |
| `docs/ops/postmortems/2026-10-29-*.md` | 1 | Dated postmortem record (postmortems README included) |
| `docs/calib/jira-PR-13-draft.md` | 1 | Dated Jira draft record |
| `skill/VERIFY-LOG.md` | 1 | Dated work log of the S215 skill restructure |
| `*.vi.md siblings` | 72 | Audited together with their English page, listed as 'path.md (+ .vi.md)' (tools/uat/own-voice/README.vi.md has no English sibling and is listed on its own) |
| `Code/config YAML in app repos (CIS services/quality/*.yaml, services/acp_content_writing/route_table.yaml, services/reports/registry/*.yaml, docker/wordpress-uat/docker-compose.yml, tests fixtures; Infra db/owners.yaml)` | 11 | Runtime/CI configuration and test fixtures, not documentation |
| `.github/** markdown/yaml in all repos` | 0 | Workflows and PR templates are CI config, not doc pages (not counted individually) |
| `.claude/worktrees/**, node_modules/**` | 0 | Not tracked in git |

The Vietnamese siblings are not counted twice: 40 of them have a record of their own; the rest are covered in the record of their English page.

## 6. Every page

Sorted by repo, then severity. "Finding" is the live truth of the first stale claim (or the first broken link or contradiction); `rows.json` has every claim with its evidence.

### AA-Ecosys (root) (314)

| Path | Verdict | Severity | Finding |
|---|---|---|---|
| `.claude/skills/kiro-delegate/SKILL.md` | wrong | high | There are no Vercel previews (AA-911 S272, AA-1038, AA-979 P2b). CIS ui-smoke.yml runs only via workflow_call from deploy-admin-dev.yml after an ECS… (+1 more) |
| `docs/guides/booking-admin-runbook.md` | wrong | high | B2C intake retired (AA-1046): bk_inquiry_pull / bk_inquiry_process / bk_notify_email have no handler; the AA TripPlanner hand-off is a demo (nothing… (+10 more) |
| `docs/guides/booking-admin-runbook.vi.md` | wrong | high | See English page (B2B-only Booking, Finance role, new nav, App health) |
| `docs/guides/cis-admin-runbook.md` | wrong | high | reviewer merged into content (CIS 363, alias removed CIS 375); nine roles: admin, content, viewer, content_lead, tenant_qa, customer_success, support… (+7 more) |
| `docs/guides/cis-admin-runbook.vi.md` | wrong | high | See English page |
| `docs/guides/tripplanner-runbook.md` | wrong | high | On the AA demo site the hand-off is a demo (nothing sent); on an agency site the trip request goes to the agency as lead.submitted.v1 (CRM pull crm_t… (+6 more) |
| `docs/guides/tripplanner-runbook.vi.md` | wrong | high | See English page |
| `docs/legal/dsar-erasure-runbook.md` | wrong | high | The saga is built and deployed in all four apps: CIS tenant_erasure_saga (CIS 408-411, #1477), Booking bk_tenant_erase (#247), TripPlanner tp_tenant_… (+5 more) |
| `skill/aa-ecosys-repos/references/tripplanner.md` | wrong | high | POST /trip/{id}/send-to-advisor: on an agency tenant (verified tenant assertion) it becomes a lead.submitted.v1 for that tenant's CRM; on the AA demo… (+4 more) |
| `skill/ai-nghiep/references/aws.md` | wrong | high | Since S278 (AA-1095), acc1 serves Bedrock LLM first and acc3 is the fallback behind it. acc4 is the AA management org (Identity Center, billing, no w… (+3 more) |
| `.claude/CLAUDE.md` | partly_stale | high | CIS staff admin runs on ECS aa-cis-dev-admin (AA-911, S272); the CIS portal/ copy was deleted at P2b (+6 more) |
| `docs/guides/cio.md` | partly_stale | high | acc1 serves Bedrock LLM for CIS since S278 via one invoker role (+ break-glass), acc3 is the fallback behind it (route Claude = Anthropic API → acc1… (+8 more) |
| `docs/ops/README.md` | partly_stale | high | Since S278 (2026-11-12, AA-1095) Bedrock LLM is served by acc1 first (Claude = Anthropic API -> acc1 -> acc3; GPT = acc1 -> acc3 -> OpenAI API); acc3… (+7 more) |
| `docs/ops/playbooks/5xx-spike.md` | partly_stale | high | rollback-ecs covers aa-crm-dev-api and aa-crm-dev-web (portal merged into web, AA-1036) and was drilled on CRM API on 2026-11-02; no Vercel project i… (+3 more) |
| `docs/ops/playbooks/llm-cost-spike.md` | partly_stale | high | Since S278 acc1 serves Bedrock first (paid by card; the Lift credit does not cover Claude); acc3 is the fallback (+3 more) |
| `docs/ops/runbooks/crm-keys.md` | partly_stale | high | Both files moved to `modules/environment/crm_data.tf` and `modules/environment/crm_storage.tf` (AA-1004 slice 2, Infra #643). The aa365 root keeps on… (+3 more) |
| `docs/ops/runbooks/pilot-agency-onboarding.md` | partly_stale | high | Both exist and passed drills: the CIS tenant_backup restore drill on 13/11 (76 tables, 1565/1565 rows) and the TripPlanner tenant backup and restore… (+4 more) |
| `docs/ops/runbooks/secret-rotation.md` | partly_stale | high | The resource moved into the module. Its address is `module.environment.random_password.tripplanner_api_key`, so the documented -replace matches nothi… (+2 more) |
| `skill/aa-ecosys-repos/SKILL.md` | partly_stale | high | AA-Partner/portal/ was removed at AA-1036 R3; the tenant portal / Content studio lives in AA-Partner web/app/(studio) (+4 more) |
| `skill/aa-ecosys-repos/references/infra.md` | partly_stale | high | booking.tf, tripplanner*.tf, crm_app/crm_data/... and staff_web.tf live in modules/environment (AA-1004 slice 3); accounts/aa365 keeps only edge/vari… (+3 more) |
| `skill/aa-ui-verify/SKILL.md` | partly_stale | high | AA-Partner has no portal/ directory. It was removed in AA-1036 R3, and the studio now lives in web/app/(studio) on ECS aa-crm-dev-web. No Vercel prev… (+9 more) |
| `docs/legal/consent-capture-query.md` | wrong | medium | bk-045 is the finance migration, and the B2C drop has not been applied. booking.customers still exists (about 1 row) with contact_consent and contact… (+2 more) |
| `.claude/skills/kiro-delegate/brief-template.md` | partly_stale | medium | No Vercel preview exists; no UI smoke runs on a feature branch (only post-merge on the ECS hosts) |
| `README.md` | partly_stale | medium | CIS staff admin runs on ECS aa-cis-dev-admin (Deploy Admin Dev) since AA-911 / S272; no Vercel project is left (+6 more) |
| `docs/README.md` | partly_stale | medium | Since S278 (AA-1095) acc1 serves Bedrock chat through one invoker role; route order Claude = Anthropic API -> acc1 -> acc3, GPT = acc1 -> acc3 -> Ope… (+4 more) |
| `docs/adr/0001a-retire-acc1-llm-on-acc3-only.md` | partly_stale | medium | Since Note S278 acc1 is the first Bedrock account for chat models and acc3 is a fallback that AWS still refuses at account level. (+2 more) |
| `docs/adr/0004-aa-booking-stack-and-bootstrap.md` | partly_stale | medium | The bridge is off: Booking accepts the WORKFORCE issuer only and a bridge token gets 401. CIS no longer mints bridge tokens, and the signing-key secr… (+4 more) |
| `docs/adr/0005b-price-versions.md` | partly_stale | medium | The design is built and live on Dev: policy parameters (bk-050), price list versions (bk-054), season calendars and holiday events (bk-055), versions… (+1 more) |
| `docs/adr/0006a-identity-phase1-amendments.md` | partly_stale | medium | There is no Vercel target. The CIS staff BFF runs on ECS aa-cis-dev-admin, whose task definition does not set the flag. A rollback means setting it o… (+2 more) |
| `docs/adr/0008-new-app-integration-and-data-platform-rules.md` | partly_stale | medium | ADR 0018 (Accepted 2026-10-31) puts prod in its own account aa-prod. The page's own Scope line (10-11) already says so, so the page contradicts itsel… (+1 more) |
| `docs/adr/0008a-crm-separate-app-exceptions.md` | partly_stale | medium | The CRM gateway calls Amazon Nova Lite on acc2 through the CRM task role (AA-1027 F4, re-scoped S265; ADR 0009 d14 amendment, Dev only). There is no… (+1 more) |
| `docs/adr/0009-ai-platform-and-provider-gateway.md` | partly_stale | medium | The Anthropic API key is stored and connection anthropic-direct has been on since S269. Route control version 6 applies the preset prefer_anthropic_a… (+4 more) |
| `docs/adr/0010-aa-partner-app.md` | partly_stale | medium | The CRM's stripe payment provider is designed as Stripe Connect Standard on the agency's own account. It is paused and answers 409 provider_not_avail… (+3 more) |
| `docs/adr/0011a-ci-bot-merges-copy-and-dump-prs.md` | partly_stale | medium | ADR 0017 is Accepted (2026-10-30, S259) and says a bot copy PR was merged with no hand step. The schema-dump PR auto-merge by ci-bot is live (db-sche… (+1 more) |
| `docs/adr/0012-environment-model.md` | partly_stale | medium | Phase 1 is done: the Infra GitHub environment `dev` is used by Terraform Apply and the workflow is named 'Terraform Apply Dev'. The Dev role trust mo… (+2 more) |
| `docs/adr/0014-repo-visibility-and-github-plan.md` | partly_stale | medium | Accepted 2026-11-14 (S280), per line 3 and the ADR index. (+3 more) |
| `docs/adr/0018-lean-aws-account-model.md` | partly_stale | medium | Since S278, acc1 serves Bedrock LLM first through one invoker role (Terraform root accounts/acc1-bedrock, live again), and acc3 is the fallback. The… (+4 more) |
| `docs/adr/0019-b2b-only-ecosystem-model.md` | partly_stale | medium | The header link was removed, but /trips shows an empty state 'Sign in to see your trips' with a Sign in button. /sign-in serves a live 'Sign in or cr… (+1 more) |
| `docs/adr/0022-aa-academy-learning-platform.md` | partly_stale | medium | The learn_retention job has not shipped. No job kind is registered, and the setting is marked not enforced. (+3 more) |
| `docs/adr/README.md` | partly_stale | medium | Since Note S278 (2026-11-12, AA-1095) acc1 serves the Bedrock chat models first and acc3 is the fallback (route-control v10/v11: Claude = Anthropic A… (+2 more) |
| `docs/agents.md` | partly_stale | medium | Last changed 2026-11-12; it no longer mentions aa-cis-portal, but still says CIS admin (Vercel) and 'Booking admin: Vercel project aa-booking-admin'… (+6 more) |
| `docs/architecture/ai-gateway.md` | partly_stale | medium | Since S278 (12/11/2026, AA-1095) Bedrock chat is served from acc1 through connection `acc1` (CIS 406, 13 deployments); acc3 is the fallback behind it… (+5 more) |
| `docs/architecture/ai-gateway.vi.md` | partly_stale | medium | acc1 serves Bedrock first since S278 (CIS 406); acc3 is the fallback (+4 more) |
| `docs/architecture/ai-use-register.md` | partly_stale | medium | Since S278 (12/11, AA-1095) Bedrock is served from acc1 first (CIS 406), acc3 behind it; route control v10/v11 (+5 more) |
| `docs/architecture/data-standards/01-engineering.md` | partly_stale | medium | N3 limits on every login role, N5 runner (lock/statement timeouts, no-transaction, destructive snapshot, lint), shared.llm_call_daily, the RLS catalo… (+5 more) |
| `docs/architecture/data-standards/02-data-management.md` | partly_stale | medium | Dev backup retention is 14 days (+5 more) |
| `docs/architecture/data-standards/README.md` | partly_stale | medium | The account total budget is 300 USD (per-app budgets cis 90, shared 120, crm 35, booking 25, identity 10, tripplanner 10) (+3 more) |
| `docs/architecture/dead-table-registry.md` | partly_stale | medium | All ten were dropped by CIS 296 (applied); schema `retired` now holds only acp_output_rules and pipeline_lessons (+3 more) |
| `docs/architecture/diagrams/README.md` | partly_stale | medium | Staff admins run on ECS (aa-cis-dev-admin, aa-booking-dev-admin) since AA-911; TripPlanner web on ECS (aa-tripplanner-dev-web) since AA-1038 (+3 more) |
| `docs/architecture/testing-strategy.md` | partly_stale | medium | Both have active rulesets: Infra 'main: PR and required checks (AA-993 I1)' requires Terraform Plan (dev), gitleaks, Copies match owner main, Migrati… (+1 more) |
| `docs/backlog/README.md` | partly_stale | medium | S282 closed (§5 'Closed in S282' at line 265) but the header and the §3 S282 row were not moved on (+4 more) |
| `docs/catalogue/features.yaml` | partly_stale | medium | ADR 0019 d11: travellers are guests; the EXTERNAL client tripplanner is frozen; S278 amendment: 'no page offers traveller Sign in'. The /sign-in page… (+1 more) |
| `docs/contracts/README.md` | partly_stale | medium | The contract file is 1.9 (1.8 AA-1090 CIS 429; 1.9 AA-1116 option B pricing, CIS 435-438) (+6 more) |
| `docs/ecosystem-architecture.md` | partly_stale | medium | CIS 442, tp-033, bk-058, crm-075 (+14 more) |
| `docs/engineering-handbook.md` | partly_stale | medium | Live CIS 0.19.0, Booking 0.15.0, TripPlanner 0.14.0, CRM (AA-Partner) 0.12.0, all via release-please (+13 more) |
| `docs/engineering-handbook.vi.md` | partly_stale | medium | CIS 0.19.0, Booking 0.15.0, TripPlanner 0.14.0, CRM 0.12.0 (+5 more) |
| `docs/glossary.md` | partly_stale | medium | acc1 serves Bedrock chat since S278 (first Bedrock rung), acc3 is the fallback; acc4 (management) exists, no workload (+4 more) |
| `docs/glossary.vi.md` | partly_stale | medium | acc1 serves Bedrock since S278; acc3 fallback; acc4 management (+3 more) |
| `docs/guides/ai-providers-and-reports-runbook.md` | partly_stale | medium | Nav groups are Home (Overview, App health, Reports, Data coverage) and AI & spend (AI gateway, Spend, Usage explorer); the page is titled 'AI gateway' (+7 more) |
| `docs/guides/ai-providers-and-reports-runbook.vi.md` | partly_stale | medium | See English page: AI gateway + Spend, nine tabs, acc1 + Anthropic API route live |
| `docs/guides/app-access-and-operations.md` | partly_stale | medium | Travellers are guests (ADR 0019 d11); no page offers 'Sign in' (AA-1094). TripPlanner is the multi-tenant agency site (demo tenant at /, agencies at… (+4 more) |
| `docs/guides/app-access-and-operations.vi.md` | partly_stale | medium | See English page |
| `docs/guides/ceo.md` | partly_stale | medium | TripPlanner is the agency site product (demo tenant + agency sites); leads go to the agency (B2B-only model) (+6 more) |
| `docs/guides/ceo.vi.md` | partly_stale | medium | See English page |
| `docs/guides/content-studio-runbook.md` | partly_stale | medium | CIS tenant detail has 'Invite member' (+3 more) |
| `docs/guides/content-studio-runbook.vi.md` | partly_stale | medium | See English page |
| `docs/guides/crm-runbook.md` | partly_stale | medium | CRM api calls Bedrock (Nova Lite) (+3 more) |
| `docs/guides/crm-runbook.vi.md` | partly_stale | medium | See English page |
| `docs/guides/cto.md` | partly_stale | medium | Claude = Anthropic API -> acc1 -> acc3; GPT = acc1 -> acc3 -> OpenAI; acc1 primary Bedrock since S278 (+7 more) |
| `docs/guides/devops.md` | partly_stale | medium | Eight services: also aa-cis-dev-admin, aa-booking-dev-admin (with the test-wp sidecar), aa-tripplanner-dev-web (the page itself names them in the dep… (+9 more) |
| `docs/guides/new-engineer.md` | partly_stale | medium | acc1 primary for Bedrock since S278, acc3 fallback; Anthropic/OpenAI APIs also used (+6 more) |
| `docs/learn/README.md` | partly_stale | medium | The academy host and the learning API are live, but the CIS admin has neither an Academy link nor the team view (team progress, content review, certi… (+1 more) |
| `docs/learn/README.vi.md` | partly_stale | medium | The Academy link and team view are decided but not built. (+1 more) |
| `docs/legal/dpa.md` | partly_stale | medium | All four saga steps and the contract are built and deployed on Dev (apply switches off by default); a DRY RUN drill path exists (CIS #1484) |
| `docs/legal/readiness-packet.md` | partly_stale | medium | The DPA is draft v0.5 (2026-11-13, AA-1093) (+4 more) |
| `docs/legal/register.md` | partly_stale | medium | tripplanner.job exists with kind tp_retention_outbox_redact (jobs Lambda). Send-to-advisor answers 410 b2b_only; leads go to the agency as lead.submi… (+6 more) |
| `docs/legal/tenant-ai-schedule.md` | partly_stale | medium | Since 2026-11-12 (S278, route control v10/v11) the GPT scoring and checking stages are answered on Amazon Bedrock in the tech lead's account. Only th… (+1 more) |
| `docs/ops/cost/README.md` | partly_stale | medium | Since S278 acc1 serves Bedrock first and is paid by card; there is no Cost Explorer reader on acc1, so the monthly report as written omits acc1's AWS… (+1 more) |
| `docs/ops/database-operations.md` | partly_stale | medium | BackupRetentionPeriod = 14 days |
| `docs/ops/drills/README.md` | partly_stale | medium | The game day ran 2026-11-02 (S264): Booking API, CRM API, Lambda browse and the job-idle gate all PASS (D3 was then Vercel booking-admin; TripPlanner… (+1 more) |
| `docs/ops/feature-flags.md` | partly_stale | medium | COGNITO_WORKFORCE_DOMAIN is an ECS task env of aa-cis-dev-admin and aa-booking-dev-admin (Infra modules/environment/staff_web.tf:108,117), set to the… (+5 more) |
| `docs/ops/finops.md` | partly_stale | medium | Since AA-1116 (CIS 436) new rows default to cis.billing.ai_alert_pct_default / ai_approval_pct_default / ai_hard_stop_default = 80 / 100 / on (+2 more) |
| `docs/ops/job-kinds.md` | partly_stale | medium | All three are RETIRED_KINDS (B2C retired, AA-1046); the worker cancels leftover rows (+6 more) |
| `docs/ops/runbooks/db-migrate.md` | partly_stale | medium | A Dev run now uses the GitHub environment `dev`. `prod` is a separate guarded path that is refused until the prod account exists. (+2 more) |
| `docs/ops/runbooks/legacy-login-flag.md` | partly_stale | medium | The CIS to Booking bridge is retired. `/auth/booking-token` is gone (CIS #1339, 06/11/2026), and Booking accepts only the WORKFORCE Cognito issuer (B… (+1 more) |
| `docs/ops/runbooks/llm-anthropic-api-key.md` | partly_stale | medium | Since S278 (AA-1095, route-control v10/v11) Claude goes Anthropic API, then acc1, then acc3 (model-first family order set by a route-control version)… (+3 more) |
| `docs/ops/runbooks/pilot-rehearsal.md` | partly_stale | medium | The rehearsal ran in S279-S281 and AA-1086 is Done: marker 1b and 12b PASS, X2 PASS including the CRM part, teardown done. (+2 more) |
| `docs/ops/runbooks/restore-rds-pitr.md` | partly_stale | medium | BackupRetentionPeriod = 14 (+1 more) |
| `docs/ops/runbooks/restore-schema.md` | partly_stale | medium | PITR window is 14 days |
| `docs/ops/runbooks/rollback-ecs.md` | partly_stale | medium | The game day the same evening applied the helper on aa-booking-dev-api and aa-crm-dev-api both ways - PASS; it also found the helper reports 'rollout… (+1 more) |
| `docs/ops/runbooks/rollback-terraform.md` | partly_stale | medium | accounts/acc1-bedrock is back on Infra main since S278 (invoker role, break-glass, alert-only budget; applied by a human). accounts/management (acc4)… (+1 more) |
| `docs/ops/runbooks/rollback-tp-lambda.md` | partly_stale | medium | deploy-lambdas.yml deploys three functions incl. aa-tripplanner-dev-jobs (jobs.zip in the same bucket); path B does not cover the jobs Lambda (+2 more) |
| `docs/ops/runbooks/ses-bounce.md` | partly_stale | medium | bk_notify_email was retired with the B2C intake (AA-1046). Booking mail now comes from kinds such as bk_agency_invoice_reminders and bk_ops_reminders… (+1 more) |
| `docs/product/partner-crm/prd.md` | partly_stale | medium | 'CRM free at launch' is superseded (ADR 0019); option B (S282): CRM Core 19 USD and Pro 29 USD per seat per month, minimum 3 seats (+2 more) |
| `docs/security/baseline.md` | partly_stale | medium | Backup retention is 14 days. (+8 more) |
| `docs/security/github-apps.md` | partly_stale | medium | There are six repos: AA-Partner also uses aa-agent (its recent PRs are authored by aa-agent[bot]) and has a release environment. (+2 more) |
| `docs/security/secrets-register.md` | partly_stale | medium | A fresh read-only run of register_check.py (AWS list-secrets plus Lambda env only) prints diff = 11: 7 UNREGISTERED (acp/cms/41ea21ee…, acp/cms/9149d… (+5 more) |
| `docs/security/secrets-register.yaml` | partly_stale | medium | The register_check.py run gives diff = 11 against the 17/11 AWS + Lambda inventory (7 unregistered, 3 planned-now-present, 1 Lambda env key). (+1 more) |
| `docs/security/vulnerability-management.md` | partly_stale | medium | chromadb and langchain were dropped from requirements and langgraph-sdk is pinned at the fixed version 0.4.4 or later. CIS .github/pip-audit-ignore.t… (+3 more) |
| `docs/templates/access-review.md` | partly_stale | medium | Since S278 (12/11/2026, AA-1095) acc1 serves Bedrock LLM through the role AA1-Bedrock-Invoker plus the break-glass role AA-BreakGlass-Admin, and acc3… (+1 more) |
| `docs/templates/capacity-review.md` | partly_stale | medium | C8b now lists 10 mandatory items. Item 10, added in S271, is untagged spend and resources missing a mandatory tag, from AA-CIS-Infra tools/finops/unt… (+2 more) |
| `docs/templates/cost-report.md` | partly_stale | medium | Since S278 acc1 serves Bedrock LLM first (route Claude = Anthropic API → acc1 → acc3; GPT = acc1 → acc3 → OpenAI API), and acc3 is only the fallback.… (+3 more) |
| `docs/templates/migration-file.md` | partly_stale | medium | AA migration files are named NNN_slug.sql. The key prefix (bk-, crm-, tp-) goes inside the file and the registry, not in the file name. Files live in… (+1 more) |
| `docs/templates/migration-file.vi.md` | partly_stale | medium | AA uses NNN_slug.sql in the owner's migrations folder (MIG-3 PATH_RE). (+1 more) |
| `docs/templates/release-note.md` | partly_stale | medium | Since S255, language-convention.md has removed side-by-side EN-VI pages. docs/STYLE.md:127-130 says 'No mixed-language page' and 'This replaces the s… (+2 more) |
| `docs/templates/role-guide.md` | partly_stale | medium | ADR 0018 (Accepted 2026-10-31) replaced the 'prod on acc2' amendment: prod runs in its own account aa-prod. That account does not exist yet: the Infr… (+3 more) |
| `skill/aa-cis-schema/references/gotchas.md` | partly_stale | medium | shared.acp_runs no longer exists: quarantined to retired by CIS 294 (AA-850) and since dropped; retired now holds only acp_output_rules and pipeline_… (+1 more) |
| `skill/aa-ecosys-repos/references/booking.md` | partly_stale | medium | The B2C intake is retired (AA-1046): bk_inquiry_pull has no handler (RETIRED_KINDS); TripPlanner leads go to the agency CRM as lead.submitted.v1 (+2 more) |
| `skill/aa-ecosys-repos/references/cis-app.md` | partly_stale | medium | Both are gone: CIS portal/ deleted at P2b, AA-Partner portal/ removed at AA-1036 R3 (studio in web/app/(studio)) (+5 more) |
| `skill/aa-ship/SKILL.md` | partly_stale | medium | Also writing_memory_r2 and writing_memory_shadow are deploy_blocking (the page's own §3 step 8 says r2 blocks deploy) (+5 more) |
| `skill/ai-nghiep/SKILL.md` | partly_stale | medium | Booking admin runs on ECS aa-booking-dev-admin (Vercel left at AA-911, S272) (+2 more) |
| `tools/docs/README.md` | partly_stale | medium | AA-Partner also vendors tools/docs (8 files) and runs a docs-lint workflow. Its docslib.py, check_frontmatter.py and test_docs_tools.py are older tha… (+3 more) |
| `tools/uat/scenarios/crm/PROGRESS.md` | partly_stale | medium | 8 of those 10 cards are now Done: CRM-28 (AA-958), 29a (AA-959), 29b (AA-960), 32 (AA-963), 33b (AA-965), 36 (AA-968), 37a (AA-969), 37b (AA-970). On… (+2 more) |
| `.claude/agents/kiro-reviewer.md` | partly_stale | low | Current; note: Description says 'Use after every kiro-run.sh' while .claude/skills/kiro-delegate/SKILL.md section 3 step 3 says the kiro-reviewe… |
| `.kiro/steering/db-schema.md` | partly_stale | low | CIS (cis_owner) also owns learn (Academy) and retired (+1 more) |
| `docs/STYLE.md` | partly_stale | low | acc1 is back for Bedrock only since S278 (invoker role + break-glass profile); acc3 is the fallback (+2 more) |
| `docs/adr/0001-ecosystem-target-architecture.md` | partly_stale | low | Vercel is retired for every ecosystem frontend: staff admins moved to ECS (aa-cis-dev-admin, aa-booking-dev-admin) at AA-911 S272, TripPlanner to ECS… (+1 more) |
| `docs/adr/0003a-per-owner-job-tables.md` | partly_stale | low | bk_inquiry_pull no longer exists (B2C intake retired, AA-1046). Current pull kinds include crm_tp_lead_pull and bk_tenant_pull. |
| `docs/adr/0004b-per-app-security-groups.md` | partly_stale | low | No crm-portal group exists (the portal service was merged into aa-crm-dev-web, AA-1036). The current groups also include sg-staff-web (staff admins o… |
| `docs/adr/0005a-b2b-resale-warn-and-vnd.md` | partly_stale | low | price.from.v1 and booking.v_from_prices are built (bk-039). price_parity reads the RRP from v_from_prices (FROM_PRICE_SQL). |
| `docs/adr/0006b-partner-pool-and-mfa.md` | partly_stale | low | AA-979 (P2b) is Done, but the cis-portal client is still provisioned in Terraform. (+1 more) |
| `docs/adr/0007-place-pipeline-in-cis.md` | partly_stale | low | TripPlanner's latest migration is tp-033. |
| `docs/adr/0010a-content-studio-partner-sign-in.md` | partly_stale | low | The ADR was implemented (cutover S253, clean-up S256) and is largely superseded by ADR 0019 d6/R3. Its status was never updated. (+2 more) |
| `docs/adr/0011-github-app-identity-and-merge-rights.md` | partly_stale | low | The header (line 3) says Accepted 2026-11-14 (S280). The implementation-status line contradicts it. (+1 more) |
| `docs/adr/0015-tour-liveness-and-retirement-propagation.md` | partly_stale | low | TripPlanner runs on ECS (AA-1038). CATALOG_REVALIDATE_SECRET is an ECS task env from key catalog_revalidate_secret of the TripPlanner web secret. (+1 more) |
| `docs/adr/0016-one-design-system-guarded-kit-copies.md` | partly_stale | low | There are three consumers: crm-web, booking and tripplanner. AA-Partner portal/ no longer exists. (+1 more) |
| `docs/adr/0021-github-org-security-and-ci-hygiene.md` | partly_stale | low | The root environment ci-hygiene and the variable AA_CI_BOT_APP_ID exist. The daily CI hygiene runs are green, and no 'needs permission' issue is open… (+1 more) |
| `docs/architecture/data-standards/03-scaling.md` | partly_stale | low | Backup retention is 14 days (+1 more) |
| `docs/architecture/erd/design/README.md` | partly_stale | low | Schema learn is live (CIS 420/421 applied), 9 tables (+1 more) |
| `docs/architecture/erd/design/crm.md` | partly_stale | low | Those 14 tables are live in schema crm (+1 more) |
| `docs/architecture/erd/design/learn.md` | partly_stale | low | CIS 420 and 421 are applied; the nine designed tables (certificate, content_review_item, enrollment, lab_run, learner, lesson_progress, quiz_attempt,… |
| `docs/architecture/job-model-modularization.md` | partly_stale | low | About 62 CIS kinds, plus per-owner job tables booking.job, crm.job, tripplanner.job (+2 more) |
| `docs/architecture/t-series-audit-and-plan.md` | partly_stale | low | Separate T stage keys exist: t2_judge, t2_brand_audit, t7_debate_judge, t10_judge, t10_adjudicate (+2 more) |
| `docs/architecture/tagging-standard.md` | partly_stale | low | Root accounts/acc1-bedrock is live again since S278 with all eight default tags (App shared, Component llm, Environment dev) (+1 more) |
| `docs/backlog/tracker/README.md` | partly_stale | low | Committed index.html SES_ORDER runs to S283 with 'after S281'; LANES to S282 |
| `docs/catalogue/integrations.yaml` | partly_stale | low | acc1 is the first Bedrock chat connection since S278; acc3 is the fallback |
| `docs/contracts/ops.overview.v1.md` | partly_stale | low | The view still exists; bk-045 is the finance file and the B2C drop file (next free bk- number) has not shipped |
| `docs/contracts/price.from.v1.md` | partly_stale | low | catalog.v_tenant_tour_v1 is live (CIS 404) and registered as catalog.tenant_tour.v1 |
| `docs/contracts/samples/README.md` | partly_stale | low | REQUIRED_NEGATIVES also covers catalog.tenant_tour.v1, learn.http.v1, tenant.addons.v1, tenant.entitlements.v1 |
| `docs/database/schema-ownership.md` | partly_stale | low | Applied: CIS 420, 421, 425 exist and schema learn holds 9 objects (+2 more) |
| `docs/legal/dpa-annex-1-processing.md` | partly_stale | low | ADR 0019 d11 makes the traveller a guest who returns through the CRM link. The EXTERNAL `tripplanner` client is frozen, and the S278 amendment says n… (+1 more) |
| `docs/legal/dpa-annex-3-subprocessors.md` | partly_stale | low | The TripPlanner gateway calls Bedrock on AA's AI account (acc3) only; it never calls the tech lead's account (+1 more) |
| `docs/legal/pilot-contract-set.md` | partly_stale | low | Since S278 the GPT stages run on Bedrock in the tech lead's account. Only the Claude stages go to the Anthropic API first (+1 more) |
| `docs/legal/retention-log.md` | partly_stale | low | A CIS tenant erasure drill ran on 2026-10-23 (aa839-drill-1), and the page's own runs table lists two 2026-10-31 erasure drills (+1 more) |
| `docs/legal/vn-cross-border-transfer-dossier.md` | partly_stale | low | The OpenAI API is now the last fallback. Bedrock in the tech lead's account (us-west-1, no new destination) answers the GPT stages (+1 more) |
| `docs/onboarding.md` | partly_stale | low | acc1 is the first Bedrock rung (Claude: Anthropic API -> acc1 -> acc3; GPT: acc1 -> acc3 -> OpenAI); acc3 is the fallback (+2 more) |
| `docs/ops/drills/rollback-game-day.md` | partly_stale | low | The first run happened 2026-11-02 (S264) with PASS on D1, D2, D4, D5; the 'After the run' updates were never applied (+1 more) |
| `docs/ops/incident-response.md` | partly_stale | low | Also /ecs/aa-cis-dev-admin, /ecs/aa-booking-dev-admin and /ecs/aa-tripplanner-dev-web exist for the staff admins and the TripPlanner web (+1 more) |
| `docs/ops/playbooks/queue-stuck.md` | partly_stale | low | bk_inquiry_pull is a retired kind (B2C retired); the worker cancels a leftover row (+1 more) |
| `docs/ops/postmortems/README.md` | partly_stale | low | Impact stopped: interim OpenAI/acc2 routes (S263) and since S278 acc1 answers all 13 gateway chat models; status should be 'mitigated' |
| `docs/ops/runbooks/rollback-booking.md` | partly_stale | low | D1 of the 2026-11-02 game day rolled aa-booking-dev-api back and forward (150 s back, health + ready 200) - PASS |
| `docs/ops/runbooks/rollback-cis.md` | partly_stale | low | The rollback-ecs helper does not accept aa-cis-dev-admin (unknown service); only its manual fallback lines work, and aa-cis. has no health route |
| `docs/ops/runbooks/staff-web-ecs-cutover.md` | partly_stale | low | The rulesets 'preview-signin locked (AA-911)' are still active on AA-CIS-App and AA-Booking. The repos still have preview branches (2 on AA-CIS-App,… |
| `docs/ops/runbooks/tenant-restore-drill.md` | partly_stale | low | The TripPlanner backup and drill are built and passed on 2026-11-15, as the page's own TripPlanner section says. |
| `docs/playbook/aa-profile.md` | partly_stale | low | The generic English skills already exist in skill/kit/ and are copied into the project-template repo. Only the AA overlay skills are Vietnamese. (+1 more) |
| `docs/playbook/aa-profile.vi.md` | partly_stale | low | The generic skills already exist in skill/kit/. (+1 more) |
| `docs/playbook/agents.md` | partly_stale | low | The reference project's personal-data guard blocks agents from reading row-level personal-data column values through SQL commands. Prompts, logs and… (+1 more) |
| `docs/playbook/agents.vi.md` | partly_stale | low | The guard blocks SQL that returns personal-data column values; it does not inspect prompts, logs or commits. |
| `docs/reports/catalog.yaml` | partly_stale | low | acc1 serves Bedrock since S278, so its spend is not zero (alert budget 100 USD/month) (+6 more) |
| `docs/reports/kpis.yaml` | partly_stale | low | acc1 Bedrock spend (since S278, alert budget 100 USD) is a third AWS cost line (+1 more) |
| `docs/research/lms/README.md` | partly_stale | low | ADR 0022 is Accepted; decisions 6 to 11 were accepted on 14/11/2026 (S280) (+2 more) |
| `docs/research/new-project-playbook/README.md` | partly_stale | low | GUIDE-08 is filled by docs/playbook/03-setup.md (draft, AA-1102), and docs/playbook/ has all nine phases plus their .vi.md siblings (+2 more) |
| `docs/research/partner-crm-spec.md` | partly_stale | low | CRM Core is 19 USD per seat per month and CRM Pro 29 USD per seat (minimum 3 seats billed), per ADR 0019 Amendment S282 option B (+1 more) |
| `docs/templates/README.vi.md` | partly_stale | low | 12 templates with front-matter have no .vi.md sibling: access-review, capacity-review, cost-report, definition-of-ready, explanation, how-to, postmor… |
| `docs/templates/contract.md` | partly_stale | low | AA keeps contracts flat: docs/contracts/<name>.v<major>[.<minor>].json or <name>.v<major>.openapi.yaml, with samples under docs/contracts/samples/<na… |
| `docs/templates/contract.vi.md` | partly_stale | low | AA uses the flat docs/contracts/ layout with samples/<name>/ folders (see the English row). |
| `docs/templates/definition-of-ready.md` | partly_stale | low | The current rule for a risky PR is an independent read-only subagent review before merge. Steering allows 'kiro-reviewer or an independent subagent r… |
| `docs/templates/runbook.md` | partly_stale | low | Each app has its own job table, and the deploy gate (DM-11.4) covers all of them: CIS shared.job, Booking booking.job, CRM crm.job, TripPlanner tripp… |
| `docs/templates/uat-report.md` | partly_stale | low | Under the S260/S265 re-scope, UAT runs in rounds: round 1 Content + CRM, round 2 TripPlanner after R5. A later round re-records only new or changed f… |
| `skill/README.md` | partly_stale | low | aa-lessons also holds guards.md (lessons turned into guards), linked from aa-lessons/SKILL.md section 4 (+1 more) |
| `skill/aa-cis-schema/SKILL.md` | partly_stale | low | Four job tables: TripPlanner also has tripplanner.job (Lambda aa-tripplanner-dev-jobs); the Terraform Apply / DB Migrate idle gate checks all four (+2 more) |
| `skill/aa-cis-schema/references/ecs-exec.md` | partly_stale | low | 10 Lambdas: also aa-tripplanner-dev-jobs (tripplanner.job runner) and aa-sec-dev-admin-session-digest (+1 more) |
| `skill/aa-lessons/lessons.md` | partly_stale | low | TripPlanner left Vercel at AA-1038; the bot check is now the ALB web ACL (rate rules + JS Challenge) (+1 more) |
| `skill/aa-session/SKILL.md` | partly_stale | low | A fourth owner table tripplanner.job exists (run by the aa-tripplanner-dev-jobs Lambda) (+1 more) |
| `skill/aa-uat-video/SKILL.md` | partly_stale | low | No app frontend is on Vercel any more (staff admin, portal, TripPlanner all on ECS/CloudFront); the reason is obsolete (tools/uat/run.sh:14 and dryru… (+1 more) |
| `skill/kit/README.md` | partly_stale | low | Each kit file is copied through tools/project-kit/kit_transform.py, which leaves out the kit:skip/kit:drop parts and puts in the kit:only parts. This… (+1 more) |
| `skill/kit/project-batch-run/SKILL.md` | partly_stale | low | The template AGENTS.md 'Project parameters' table has rows for 'Cost ledger' and 'Job table' (the job table row only when has_api). It has no row for… |
| `skill/kit/project-business-update/SKILL.md` | partly_stale | low | The template AGENTS.md has a single row, 'Business channel and reader language'. It has no row for the epics per product or for how a mention is writ… |
| `skill/kit/project-issue/SKILL.md` | partly_stale | low | The template has rows for Tracker, Issue key prefix, Tracker projects and Priority scale. It has no plan-quota row. (+1 more) |
| `skill/kit/project-uat/SKILL.md` | partly_stale | low | The template has 'Sign-in for automated checks' (web only) and 'Languages'. It has no row for UAT voices or the upload destination. |
| `tools/contracts/README.md` | partly_stale | low | Five repos carry a vendored tools/docs copy: AA-Partner also has one. The shared test_docs_tools.py is no longer identical in any vendored repo. See… |
| `docs/AAA/erd-v2/README.md` | orphan | low | AA-Booking is live since 2026-10-14; it has no docs/erd/; the live schema is in db-schema-reference.md (+4 more) |
| `docs/ops/runbooks/ecs-exec-s3-mediated.md` | broken_links_only | low | The container names are right (live: api), but the files are now `modules/environment/booking.tf` and `modules/environment/crm_app.tf`. |
| `docs/templates/postmortem.md` | current | low | Current; note: §11 (line 108-109) says the business summary is written in English, with a Vietnamese version in a sibling .vi.md. docs/STYLE.md:… |
| `skill/kit/project-session/SKILL.md` | current | low | Current. |
| `skill/kit/project-ui-verify/SKILL.md` | current | low | Current. |
| `tools/github/README.md` | current | low | Current. |
| `tools/uat/arch/README.md` | current | low | Current. |
| `tools/uat/own-voice/README.vi.md` | current | low | Current; note: Language convention: a .vi.md page is meant to be the translation sibling of an English page, but here there is no README.md. The… |
| `tools/uat/scenarios/crm/REHEARSAL.md` | current | low | Current. |
| `.kiro/steering/language-convention.md` | current | none | Current. |
| `.kiro/steering/session-workflow.md` | current | none | Current. |
| `docs/adr/0002-only-cis-writes-content.md` | current | none | Current. |
| `docs/adr/0003-one-durable-job-model.md` | current | none | Current. |
| `docs/adr/0004a-supply-content-ownership.md` | current | none | Current. |
| `docs/adr/0005-pricing-and-supplier-rates.md` | current | none | Current. |
| `docs/adr/0006-ecosystem-identity.md` | current | none | Current. |
| `docs/adr/0017-migrations-in-app-pr-expand-auto-apply.md` | current | none | Current; note: Rollout M5 says 'ADR 0011a -> Accepted', but ADR 0011a still says Proposed (the stale side is 0011a). |
| `docs/adr/0017a-dev-auto-applies-contract-migrations.md` | current | none | Current. |
| `docs/adr/0020-content-quality-architecture.md` | current | none | Current. |
| `docs/architecture/erd/design/tripplanner.md` | current | none | Current. |
| `docs/artifacts/README.md` | current | none | Current; note: Line 16 lists the Master Plan source as tracker 'index.html + plan.json + sessions/', but tracker/README.md says sessions/ files… |
| `docs/calib/README.md` | current | none | Current. |
| `docs/catalogue/README.md` | current | none | Current. |
| `docs/guides/booking-price-setup.md` | current | none | Current; note: booking-admin-runbook.md (linked for sign-in and roles) still lists only four Booking roles and an old menu |
| `docs/guides/booking-price-setup.vi.md` | current | none | Current. |
| `docs/guides/delivery-metrics.md` | current | none | Current. |
| `docs/guides/delivery-metrics.vi.md` | current | none | Current. |
| `docs/guides/pm.md` | current | none | Current. |
| `docs/guides/working-rules/README.md` | current | none | Current. |
| `docs/guides/working-rules/README.vi.md` | current | none | Current. |
| `docs/guides/working-rules/planning-and-issues.md` | current | none | Current. |
| `docs/guides/working-rules/planning-and-issues.vi.md` | current | none | Current. |
| `docs/guides/working-rules/sessions.md` | current | none | Current. |
| `docs/guides/working-rules/sessions.vi.md` | current | none | Current. |
| `docs/guides/working-rules/stakeholder-communication.md` | current | none | Current. |
| `docs/guides/working-rules/stakeholder-communication.vi.md` | current | none | Current. |
| `docs/learn/allowlist.yaml` | current | none | Current. |
| `docs/learn/modules/F3-how-work-flows/lessons/01-which-source-wins.md` | current | none | Current. |
| `docs/learn/modules/F3-how-work-flows/lessons/02-decide-and-done.md` | current | none | Current. |
| `docs/learn/modules/F3-how-work-flows/module.yaml` | current | none | Current. |
| `docs/learn/modules/F3-how-work-flows/quiz.yaml` | current | none | Current. |
| `docs/learn/paths/fundamentals.yaml` | current | none | Current. |
| `docs/legal/dpa-annex-2-security.md` | current | none | Current. |
| `docs/legal/dpa-annex-4-transfers.md` | current | none | Current. |
| `docs/legal/dpa-pack-outline.md` | current | none | Current. |
| `docs/legal/dpa-template.md` | current | none | Current. |
| `docs/legal/tenant-terms-ai-clause-draft.md` | current | none | Current. |
| `docs/ops/playbooks/cognito-login.md` | current | none | Current. |
| `docs/ops/playbooks/llm-access-denied.md` | current | none | Current. |
| `docs/ops/runbooks/break-glass.md` | current | none | Current. |
| `docs/ops/runbooks/deploy-gate-override.md` | current | none | Current. |
| `docs/ops/runbooks/embedding-re-embed.md` | current | none | Current. |
| `docs/ops/runbooks/isolation-probe.md` | current | none | Current. |
| `docs/ops/runbooks/pilot-tenant-restore-drill.md` | current | none | Current. |
| `docs/ops/runbooks/rollback-vercel.md` | current | none | Current; note: Rows 30-31 send the CIS and Booking admins to rollback-ecs, whose helper does not accept those services (manual path only) |
| `docs/ops/runbooks/tripplanner-web-ecs-cutover.md` | current | none | Current. |
| `docs/playbook/01-discovery.md` | current | none | Current. |
| `docs/playbook/02-architecture.md` | current | none | Current. |
| `docs/playbook/03-setup.md` | current | none | Current. |
| `docs/playbook/04-build.md` | current | none | Current. |
| `docs/playbook/05-test.md` | current | none | Current. |
| `docs/playbook/06-release.md` | current | none | Current. |
| `docs/playbook/07-operate.md` | current | none | Current. |
| `docs/playbook/08-scale.md` | current | none | Current. |
| `docs/playbook/09-retire.md` | current | none | Current. |
| `docs/playbook/README.md` | current | none | Current. |
| `docs/playbook/adoption.md` | current | none | Current. |
| `docs/playbook/metrics.md` | current | none | Current. |
| `docs/playbook/principles.md` | current | none | Current. |
| `docs/product/README.md` | current | none | Current. |
| `docs/research/lms/inventory.md` | current | none | Current. |
| `docs/research/new-project-playbook/inventory.md` | current | none | Current. |
| `docs/security/README.md` | current | none | Current. |
| `docs/templates/README.md` | current | none | Current. |
| `docs/templates/adr-http-api-conventions.md` | current | none | Current. |
| `docs/templates/adr.md` | current | none | Current. |
| `docs/templates/context-arc42.md` | current | none | Current. |
| `docs/templates/context-arc42.vi.md` | current | none | Current. |
| `docs/templates/cost-sheet.md` | current | none | Current. |
| `docs/templates/cost-sheet.vi.md` | current | none | Current. |
| `docs/templates/delivery-metrics-report.md` | current | none | Current. |
| `docs/templates/delivery-metrics-report.vi.md` | current | none | Current. |
| `docs/templates/discovery-brief.md` | current | none | Current. |
| `docs/templates/discovery-brief.vi.md` | current | none | Current. |
| `docs/templates/explanation.md` | current | none | Current. |
| `docs/templates/how-to.md` | current | none | Current. |
| `docs/templates/implementation-note.md` | current | none | Current. |
| `docs/templates/incident-record.md` | current | none | Current. |
| `docs/templates/incident-record.vi.md` | current | none | Current. |
| `docs/templates/project-charter.md` | current | none | Current. |
| `docs/templates/project-charter.vi.md` | current | none | Current. |
| `docs/templates/reference.md` | current | none | Current. |
| `docs/templates/release-checklist.md` | current | none | Current. |
| `docs/templates/release-checklist.vi.md` | current | none | Current. |
| `docs/templates/retirement-checklist.md` | current | none | Current. |
| `docs/templates/retirement-checklist.vi.md` | current | none | Current. |
| `docs/templates/risk-register.md` | current | none | Current. |
| `docs/templates/risk-register.vi.md` | current | none | Current. |
| `docs/templates/security-checklist.md` | current | none | Current. |
| `docs/templates/security-checklist.vi.md` | current | none | Current. |
| `docs/templates/session-checklist.md` | current | none | Current. |
| `docs/templates/session-checklist.vi.md` | current | none | Current. |
| `docs/templates/settings-entry.md` | current | none | Current. |
| `docs/templates/settings-entry.vi.md` | current | none | Current. |
| `docs/templates/slo-error-budget.md` | current | none | Current. |
| `docs/templates/slo-error-budget.vi.md` | current | none | Current. |
| `docs/templates/stakeholder-raci.md` | current | none | Current. |
| `docs/templates/stakeholder-raci.vi.md` | current | none | Current. |
| `docs/templates/test-strategy.md` | current | none | Current. |
| `docs/templates/test-strategy.vi.md` | current | none | Current. |
| `docs/templates/threat-model.md` | current | none | Current. |
| `docs/templates/threat-model.vi.md` | current | none | Current. |
| `docs/templates/vendor-selection.md` | current | none | Current. |
| `docs/templates/vendor-selection.vi.md` | current | none | Current. |
| `skill/REVIEW-CHECKLIST.md` | current | none | Current. |
| `skill/aa-cis-schema/references/destructive-ops.md` | current | none | Current. |
| `skill/aa-ecosys-repos/references/pipeline.md` | current | none | Current. |
| `skill/aa-jira-update/SKILL.md` | current | none | Current. |
| `skill/aa-lessons/SKILL.md` | current | none | Current. |
| `skill/aa-lessons/guards.md` | current | none | Current. |
| `skill/aa-linear-issue/SKILL.md` | current | none | Current. |
| `skill/aa-session/references/parallel-lanes.md` | current | none | Current. |
| `skill/aa-ship/references/merge-trains.md` | current | none | Current. |
| `skill/aa-uat-video/references/voices-licences.md` | current | none | Current. |
| `skill/aa-ui-verify/references/evidence-report.md` | current | none | Current. |
| `skill/aa-wave-rerun/SKILL.md` | current | none | Current. |
| `skill/ai-nghiep/references/adr.md` | current | none | Current. |
| `skill/ai-nghiep/references/handoff-prompt.md` | current | none | Current. |
| `skill/ai-nghiep/references/stakeholders-english.md` | current | none | Current. |
| `skill/kit/project-lessons/SKILL.md` | current | none | Current. |
| `skill/kit/project-rules/SKILL.md` | current | none | Current. |
| `skill/kit/project-ship/SKILL.md` | current | none | Current. |
| `tools/linear/README.md` | current | none | Current. |

### AA-CIS-App (31)

| Path | Verdict | Severity | Finding |
|---|---|---|---|
| `apps/AA-CIS-App/.claude/CLAUDE.md` | wrong | high | Admin runs on ECS service aa-cis-dev-admin (AA-911); the Vercel project was retired in S272. The tenant portal is the portal. host served by AA-Partn… (+8 more) |
| `apps/AA-CIS-App/.claude/agents/db-auditor.md` | wrong | high | The CIS task role has been denied aa-cis/dev/rds since X1 S19. Use the container DATABASE_URL (cis_app: no booking.*/tripplanner.* base tables, no DD… (+1 more) |
| `apps/AA-CIS-App/.claude/skills/ecs-exec-pattern.md` | wrong | high | Since X1 S18/S19 (AA-860) the CIS task role is denied GetSecretValue on the master secret. Container scripts must use the container env var DATABASE_… (+2 more) |
| `apps/AA-CIS-App/docs/adr/0012-llm-data-scopes-per-stage.md` | partly_stale | high | CIS 344 (S264, AA-1026) set {aws_only, vendor_direct} on the six tenant writer stages (t2_generate, t2_flag_fix, t2_itinerary_nudge, t8_angle_gen, t9… (+2 more) |
| `apps/AA-CIS-App/.claude/agents/test-runner.md` | wrong | medium | The file does not exist. The suites are tests/unit, tests/integration, tests/acp, tests/acp_s2 and tests/e2e, plus a few top-level test_*.py files. (+2 more) |
| `apps/AA-CIS-App/tests/load/README.md` | wrong | medium | Neither workflow exists, no workflow runs k6, and there is no staging environment (+3 more) |
| `apps/AA-CIS-App/.claude/agents/code-reviewer.md` | partly_stale | medium | The gateway has an Anthropic Messages adapter and Claude routes start on the Anthropic API; the rule is: no model call outside shared/llm_client (no… (+1 more) |
| `apps/AA-CIS-App/CONTEXT.md` | partly_stale | medium | Since S278 (AA-1095) acc1 serves Bedrock chat; route order Claude = Anthropic API -> acc1 -> acc3, GPT = acc1 -> acc3 -> OpenAI API; acc3 is the fall… (+12 more) |
| `apps/AA-CIS-App/README.md` | partly_stale | medium | The ID is the live CIS REST API ID, but resource IDs must not be written in a public app repo (DM-6.10; root CLAUDE.md: API Gateway IDs are not copie… (+6 more) |
| `apps/AA-CIS-App/docs/adr/0005-model-catalog-and-converse-adapter.md` | partly_stale | medium | Root ADR 0009 (Accepted S261) rewords decision 4 (family fallback; writer routes list no other family) and replaces decision 9 with the decision 13 c… (+3 more) |
| `apps/AA-CIS-App/docs/adr/0006-stage-routes-fallback-and-shadow.md` | partly_stale | medium | GPT-4.1 is retired. The catalog row is disabled since 224, the deployment is switched off and no stage route names gpt-4.1 (a guard enforces this) (+2 more) |
| `apps/AA-CIS-App/docs/adr/0008-validate-stages-any-vendor.md` | partly_stale | medium | s1_generate primary is sonnet-5-5, with fallbacks sonnet-4-6, haiku-4-5 and the OpenAI last rung. The judge is still GPT-5.6 Luna (+2 more) |
| `apps/AA-CIS-App/docs/adr/0011-t9-faq-question-filter-llm-step.md` | partly_stale | medium | The live Dev worker runs T9_FAQ_LLM_FILTER=on. Infra records it as 'on since S247 (shadow verdicts read on real blogs first)'. The ADR never records… (+2 more) |
| `apps/AA-CIS-App/docs/runbooks/clean-rerun.md` | partly_stale | medium | Dev now runs task def aa-cis-dev-api:1185, schema 442 (+3 more) |
| `apps/AA-CIS-App/docs/CIS_Runbook_v1.md` | partly_stale | low | Root repo is public (temporary, ADR 0014 amendment) |
| `apps/AA-CIS-App/docs/adr/0002-search-demand-shared-across-tenants.md` | partly_stale | low | Freshness is now an admin setting: cis.seo.research_volume_fresh_days and cis.seo.research_serp_fresh_days, both defaulting to 365 days, read by serv… (+2 more) |
| `apps/AA-CIS-App/docs/adr/0004-live-writing-progress-via-redis-poll.md` | partly_stale | low | Since S278 (AA-1095, 12/11/2026) acc1 serves Bedrock LLM again through the acc1 connection (CIS 406). invoke_claude accepts any assume-role connectio… |
| `apps/AA-CIS-App/docs/adr/0010-governed-writing-memory.md` | partly_stale | low | Root ADR 0009 'AI platform and provider gateway' is written and Accepted (S261, decisions 1-9, 13, 14) (+2 more) |
| `apps/AA-CIS-App/docs/adr/README.md` | partly_stale | low | The root AA-Ecosys repo has been public since 2026-10-22 (root ADR 0014 amendment S247) (+1 more) |
| `apps/AA-CIS-App/docs/api/README.md` | partly_stale | low | The untyped list holds 51 entries (all /v1/*) |
| `apps/AA-CIS-App/docs/architecture/at-series-v2-design.md` | partly_stale | low | Implemented: Jev seam shared/llm_client/decide.py, shared.decision_log (~652k rows), calibration records in docs/calibration/, admin /admin/decisions (+2 more) |
| `apps/AA-CIS-App/docs/architecture/t-series-audit-and-plan.md` | partly_stale | low | G1 shipped (tenant ContextVar in the ledger), G4 shipped (t2_judge, t2_brand_audit, t7_debate_judge stages), G5 shipped (job kinds t7_slate, t8_angle… (+1 more) |
| `apps/AA-CIS-App/docs/llm/eval-runbook.md` | partly_stale | low | The cap in force is the admin setting cis.writing_memory.month_cap_usd (default 25, editable on Platform > Settings); MONTH_CAP_USD is only its compi… |
| `apps/AA-CIS-App/frontend/README.md` | partly_stale | low | No next/font import; fonts come from the kit tokens (+1 more) |
| `apps/AA-CIS-App/.url-wheels/README.md` | current | none | Current. |
| `apps/AA-CIS-App/docs/adr/0001-atoms-platform-wide-segments-per-tenant.md` | current | none | Current. |
| `apps/AA-CIS-App/docs/adr/0003-segment-score-route-hub-will-become-platform-wide.md` | current | none | Current. |
| `apps/AA-CIS-App/docs/adr/0007-jev-verdicts-may-act.md` | current | none | Current. |
| `apps/AA-CIS-App/docs/adr/0009-f17-owns-offered-moments-promises-gate-dropped.md` | current | none | Current. |
| `apps/AA-CIS-App/docs/llm/prompt-register.md` | current | none | Current. |
| `apps/AA-CIS-App/frontend/AGENTS.md` | current | none | Current. |

### AA-Booking (11)

| Path | Verdict | Severity | Finding |
|---|---|---|---|
| `apps/AA-Booking/.claude/CLAUDE.md` | partly_stale | high | In the dev phase the orchestrating agent merges its own PR once CI is green, using the merge queue through tools/github/ship_merge.py; subagents neve… (+1 more) |
| `apps/AA-Booking/CONTEXT.md` | partly_stale | medium | Booking is B2B-only since AA-1046; live schema bk-058; inquiry intake and customers routes are retired; 9 required checks (+15 more) |
| `apps/AA-Booking/README.md` | partly_stale | medium | B2B-only: trip cases from the B2B confirm, suppliers, pricing, B2B API, agency billing; customer identity/inquiries/customer invoices retired (AA-104… (+6 more) |
| `apps/AA-Booking/docs/adr/0001-implements-root-0004.md` | partly_stale | medium | AA-Booking has frontend/ (the staff admin, ECS service aa-booking-dev-admin) (+4 more) |
| `apps/AA-Booking/docs/figma-coverage.md` | partly_stale | medium | Customers pages removed with the B2C retirement (AA-1046) (+4 more) |
| `apps/AA-Booking/docs/ui-spec.md` | partly_stale | medium | Not updated since 2026-10-30; no mention of AA-1046 (B2C retired), AA-911 (ECS, Cognito sign-in) or the 15+ routes added since (agency-billing, b2b-d… (+3 more) |
| `apps/AA-Booking/docs/adr/README.md` | partly_stale | low | The root repo has been public since 2026-10-22 |
| `apps/AA-Booking/docs/api/README.md` | partly_stale | low | booking.customer.v1 retired (AA-1046): the path answers 404 and no route exists; CONTEXT.md Releases section already lists only b2b, health, ops |
| `apps/AA-Booking/frontend/README.md` | partly_stale | low | Staff sign in with company e-mail through Cognito WORKFORCE (booking-staff client); no CIS account login (+1 more) |
| `apps/AA-Booking/tools/docs/README.md` | partly_stale | low | test_docs_tools.py differs from root in Booking and Infra (root adds AiGatewayNamesTest); the rest are identical (+2 more) |
| `apps/AA-Booking/frontend/e2e/SIGNED-IN-SMOKE.md` | current | none | Current. |

### AA-Partner (9)

| Path | Verdict | Severity | Finding |
|---|---|---|---|
| `apps/AA-Partner/CONTEXT.md` | partly_stale | medium | portal/ is retired (studio in web/app/(studio), AA-1036 R3); live CRM schema crm-075, 34 job kinds (+7 more) |
| `apps/AA-Partner/README.md` | partly_stale | medium | CRM is feature-complete for Dev: 107 web pages, 45 route groups, 34 job kinds, schema crm-075, API 0.12.0 (+3 more) |
| `apps/AA-Partner/docs/adr/0001-implements-root-0010.md` | partly_stale | low | AA-933 PR #1 is merged on main (+1 more) |
| `apps/AA-Partner/docs/adr/README.md` | partly_stale | low | The AA-933 skeleton PR merged (AA-Partner #1, 55e235ad), which per the ADR's own rule makes it Accepted |
| `apps/AA-Partner/docs/operations/slo.md` | partly_stale | low | Since AA-1096 L6 they are the variable crm_slo (declared in accounts/aa365/crm_variables.tf and the module), copied into locals (+1 more) |
| `apps/AA-Partner/tools/docs/README.md` | partly_stale | low | Partner docslib.py and check_frontmatter.py lack the root's .vi.md translation support; test_docs_tools.py differs too (+2 more) |
| `apps/AA-Partner/.claude/CLAUDE.md` | current | none | Current. |
| `apps/AA-Partner/loadtest/README.md` | current | none | Current. |
| `apps/AA-Partner/web/AGENTS.md` | current | none | Current. |

### AA-TripPlanner-Web (22)

| Path | Verdict | Severity | Finding |
|---|---|---|---|
| `apps/AA-TripPlanner-Web/.kiro/steering/product.md` | wrong | high | The product is a B2B white-label planner for partner agencies (demo tenant at /, agencies at /{slug} or a custom domain), and AA keeps no traveller r… (+5 more) |
| `apps/AA-TripPlanner-Web/.kiro/steering/structure.md` | wrong | high | Deploy units are ECS web plus three Lambdas (browse, assembly, jobs). There is no extraction pipeline; its ops answer 410. (+5 more) |
| `apps/AA-TripPlanner-Web/.kiro/steering/tech.md` | wrong | high | tp-018 dropped itinerary_components, and shared.destinations is unreadable to TripPlanner (CIS 270). (+9 more) |
| `apps/AA-TripPlanner-Web/docs/architecture-overview.md` | wrong | high | TripPlanner reads catalog.* views only; CIS 270 revoked the old grants. (+7 more) |
| `apps/AA-TripPlanner-Web/docs/e2e-uat-guide.md` | wrong | high | CONTEXT forbids pointing a local run at the Dev database. Migrations go only through DB Migrate. The extraction module is gone. Access is SSM only, n… (+2 more) |
| `apps/AA-TripPlanner-Web/docs/smoke-test-runbook.md` | wrong | high | Migrations are applied only through AA-CIS-Infra DB Migrate (as tp_owner). 001 and 002 were applied long ago; tp-033 is the latest. (+3 more) |
| `apps/AA-TripPlanner-Web/.claude/CLAUDE.md` | partly_stale | high | There are five child repos (CIS, Booking, TripPlanner, Partner, Infra), and Booking has been live since S235. The hand-off file does not exist. (+9 more) |
| `apps/AA-TripPlanner-Web/CONTEXT.md` | partly_stale | medium | TripPlanner does still call only the acc3 satellite, so that part is right. What is stale is 'the main chat account': since S278 (AA-1095) acc1 serve… (+13 more) |
| `apps/AA-TripPlanner-Web/README.md` | partly_stale | medium | B2B white-label planner per agency tenant (ADR 0019 d10/d11); bare-path send-to-advisor is a demo (410 b2b_only), agency leads go out as lead.submitt… (+6 more) |
| `apps/AA-TripPlanner-Web/docs/jobs-runbook.md` | partly_stale | medium | Six kinds: also tp_lead_deliver (daily, can mark attention and fail the tick) — not covered by the runbook or its alarm section (+1 more) |
| `apps/AA-TripPlanner-Web/.kiro/specs/tripplanner-mvp/design.md` | orphan | medium | acc1 serves Bedrock since S278 (TripPlanner itself still acc3-only) (+2 more) |
| `apps/AA-TripPlanner-Web/.kiro/specs/tripplanner-mvp/requirements.md` | orphan | medium | Pipeline moved to CIS; TripPlanner reads catalog views only (+2 more) |
| `apps/AA-TripPlanner-Web/docs/content-handoff/README.md` | orphan | medium | Photos are synced and matched by CIS (photo_sync, shared.place_photo) and read through catalog views; TripPlanner cannot read shared.destinations (+1 more) |
| `apps/AA-TripPlanner-Web/docs/adr/README.md` | partly_stale | low | The root repo has been public since 2026-10-22 |
| `apps/AA-TripPlanner-Web/tools/docs/README.md` | partly_stale | low | Root repo is public (since 22/10/2026) (+1 more) |
| `apps/AA-TripPlanner-Web/.kiro/specs/tripplanner-mvp/tasks.md` | orphan | low | acc1 serves Bedrock ecosystem-wide since S278 (+1 more) |
| `apps/AA-TripPlanner-Web/docs/bao-cao-hien-trang-vi.md` | orphan | low | ECS behind CloudFront at the tripplanner host; Vercel retired; extraction gone (+1 more) |
| `apps/AA-TripPlanner-Web/docs/brand-sync-adventure-asia.md` | orphan | low | Decided and built in AA-995: Poppins + Satisfy, Inter and Fahkwang removed, colours from the kit core tokens |
| `apps/AA-TripPlanner-Web/docs/change-report-mvp-completion.md` | orphan | low | Vercel retired (AA-1038), Dev only, DM-11.5 merge rule |
| `apps/AA-TripPlanner-Web/docs/roadmap.md` | orphan | low | Dev only; Mapbox restricted (S239), web ACL rules live (AA-1015/1038), Sentry done, share link done (AA-1041), advisor e-mail obsolete (B2B) (+1 more) |
| `apps/AA-TripPlanner-Web/docs/task-assessment.md` | orphan | low | Superseded MVP planning (gateway, ECS, DM-11.5) (+1 more) |
| `apps/AA-TripPlanner-Web/docs/mapbox-setup.md` | current | none | Current. |

### AA-CIS-Infra (14)

| Path | Verdict | Severity | Finding |
|---|---|---|---|
| `infra/AA-CIS-Infra/.claude/CLAUDE.md` | wrong | high | Since S278 (AA-1095) acc1 serves Bedrock chat models through the AA1-Bedrock-Invoker role of the live root accounts/acc1-bedrock (plus an alert-only… (+6 more) |
| `infra/AA-CIS-Infra/CONTEXT.md` | partly_stale | high | Four roots/accounts: aa365 (acc2), acc1-bedrock (acc1, Bedrock primary since S278), acc3-bedrock, management (+18 more) |
| `infra/AA-CIS-Infra/docs/runbooks/crm-mail-ingest.md` | wrong | medium | MAIL_OAUTH_REDIRECT_BASE is the agency host (portal.) since the AA-979 clean-up; partner-dev./connect/mail/callback answers 301 to portal., so regist… (+2 more) |
| `infra/AA-CIS-Infra/README.md` | partly_stale | medium | aa365 (with modules/environment) also holds Booking, AA-Partner CRM, staff web on ECS, TripPlanner web on ECS and 3 TripPlanner Lambdas (assembly, br… (+8 more) |
| `infra/AA-CIS-Infra/db/README.md` | partly_stale | medium | Copies are pulled by Migration Sync (ci-bot opens + merges) and expand/contract files are auto-applied by Migration Apply on Dev (DB_AUTO_APPLY=true,… (+6 more) |
| `infra/AA-CIS-Infra/db/scripts/README.md` | partly_stale | medium | The runner already reads the master DSN in the task from aa-cis/dev/rds for roles/, set-password and run-script (+2 more) |
| `infra/AA-CIS-Infra/docs/agent-session-role.md` | partly_stale | medium | Workspace rules and every runbook/skill have agents run single-line commands with --profile aa365-admin (S3-mediated ECS exec pattern included); aa36… (+1 more) |
| `infra/AA-CIS-Infra/tools/identity/README.md` | partly_stale | medium | crm_partner_signin_enabled is permanently true and the CRM API refuses cis-portal tokens since AA-979 P2b; web-secret without --pool partner would wr… |
| `infra/AA-CIS-Infra/accounts/management/README.md` | partly_stale | low | Applied: the management root on main contains both and the nightly management drift is green (state matches main) (+2 more) |
| `infra/AA-CIS-Infra/docs/adr/README.md` | partly_stale | low | Booking stack moved to modules/environment/booking.tf (AA-1004 slice 1) (+1 more) |
| `infra/AA-CIS-Infra/docs/ci-role-split.md` | partly_stale | low | It also deploys the CIS staff admin (aa-cis-dev-admin family/service, cicd_split.tf cis_app_deploy_staff_web, AA-911) via deploy-admin-dev.yml (+2 more) |
| `infra/AA-CIS-Infra/docs/waf-count-review.md` | partly_stale | low | Flipped: default false since S239 (enforced, with SizeRestrictions_BODY / GenericLFI_BODY / CrossSiteScripting_BODY overrides in COUNT) |
| `infra/AA-CIS-Infra/tools/docs/README.md` | partly_stale | low | Root docslib.py, check_docs_text.py, check_adr_index.py, check_frontmatter.py, lychee.toml, requirements.txt are byte-identical to Infra; test_docs_t… (+2 more) |
| `infra/AA-CIS-Infra/docs/runbooks/org-move-readiness-checks.md` | current | none | Current. |
