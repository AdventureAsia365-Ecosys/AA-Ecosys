---
id: CAT-01
title: AA-Ecosys engineering handbook
description: The single page on how AA-Ecosys is built, documented, versioned, released, operated and paid for - operating model, lifecycle, docs system, versioning, releases, operations, cost, the merged platform roadmap and the decision log.
type: explanation
status: draft
owner: nghiep
audience: [owner, engineer, devops, cto, cio, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-19
review_every_days: 90
related: [CAT-00, TPL-02, GUIDE-02, GUIDE-03, ARCH-08, OPS-01, FIN-01, AA-887]
---

# AA-Ecosys engineering handbook

This page is the single source for **how we build, document, version, release, operate and pay for AA-Ecosys**.
It replaces the S241 SDLC review and platform roadmap and the four S243 advisory files (listed in
[§12](#12-change-history-and-superseded-documents)). It does not restate rules that have a canonical home: it
names them and links there. Where a rule lives in a data standard, an ADR or a skill, that file wins and this page
only points at it.

AA-Ecosys is three apps on one AWS account (acc2): **AA-CIS** (content and catalog), **AA-TripPlanner-Web**
(traveller front door) and **AA-Booking** (customers, trip cases, pricing, payments), plus the Terraform repo
**AA-CIS-Infra** and this private root repo. Today there is one environment, **Dev**, holding test data only
(D-01). The team is one engineer (Nghiệp) working with AI agents (Claude Code, Kiro) for one business owner
(Ms. Thư).

> **For Ms. Thư (CEO) / Dành cho chị Thư:** We build on one shared test environment (Dev, test data only) and will add
> production only when a go-live date is set. Every change passes automated checks and is verified on the live system
> before it counts as done. Spending: the account budget is 250 USD/month today; any new AWS cost is quoted first and
> approved item by item. Your decisions: business, legal and pricing. You receive a short Vietnamese summary of the
> monthly cost, of releases and of any incident. Your guide: [CEO guide](guides/ceo.md).
>
> Hệ hiện chỉ có một môi trường thử (Dev, dữ liệu test); prod chỉ dựng khi có ngày go-live. Mọi thay đổi phải qua
> kiểm tra tự động và kiểm trên hệ thật mới tính là xong. Ngân sách tài khoản hiện 250 USD/tháng; chi phí AWS mới đều
> báo giá trước và duyệt từng mục. Chị quyết việc kinh doanh, pháp lý, giá; chị nhận tóm tắt tiếng Việt về chi phí
> tháng, các bản phát hành và mọi sự cố. Hướng dẫn cho chị: [CEO guide](guides/ceo.md).

How to read it (Tóm tắt (VI): bảng dưới chỉ phần nên đọc theo nhu cầu và theo vai trò):

| Role | Read first |
|---|---|
| CEO | The box above, [§8.3](#83-monthly-review), [§9.3](#93-do-not-do-now), [CEO guide](guides/ceo.md) |
| CTO / CIO | [§1](#1-purpose-scope-and-precedence), [§2](#2-operating-model), [§5](#5-versioning), [§7](#7-operations), [§9](#9-roadmap), [§10](#10-decisions-log) |
| DevOps | [§6](#6-releasing-and-changing-features), [§7](#7-operations), [§8](#8-cost-finops), [DevOps guide](guides/devops.md) |
| PM | [§2](#2-operating-model), [§3](#3-lifecycle-stages), [§6.4](#64-definition-of-ready-and-done), [§9](#9-roadmap) |
| New engineer / agent | [§1](#1-purpose-scope-and-precedence)-[§4](#4-documentation-system), [onboarding](onboarding.md), [agents.md](agents.md) |

| If you want | Read |
|---|---|
| The rules of the game in five minutes | [§1](#1-purpose-scope-and-precedence) and [§2](#2-operating-model) |
| What happens to a piece of work from idea to cost | [§3](#3-lifecycle-stages) |
| Where a doc goes and how to write it | [§4](#4-documentation-system) |
| Versions, releases, migrations, API and prompt versions | [§5](#5-versioning) and [§6](#6-releasing-and-changing-features) |
| Alarms, incidents, backups, secrets, access | [§7](#7-operations) |
| Money | [§8](#8-cost-finops) |
| What is next, what is done, what we will not do | [§9](#9-roadmap) |
| Why something is the way it is | [§10](#10-decisions-log) |
| A word you do not know | [§11](#11-glossary) |

---

## 1. Purpose, scope and precedence

> **Tóm tắt (VI):** Trang này là nguồn duy nhất trả lời "hệ AA-Ecosys được xây, viết tài liệu, đánh version, phát
> hành, vận hành và trả tiền như thế nào". Nó thay bản review và lộ trình S241 cùng bốn file tư vấn S243. Khi lệch nhau, thứ tự thắng:
> ADR đã accepted > data standards v1.1 > quyết định đã ghi của Nghiệp > handbook này > skill/steering. Sửa handbook
> bằng một PR vào repo gốc, sửa luôn các file nó trỏ tới trong cùng PR.

### 1.1 Purpose

- Give every reader (owner, engineer, DevOps, CTO, CIO, PM, agent) one place that explains the whole delivery
  system and links to the page that holds each rule.
- Hold the **one** platform roadmap ([§9](#9-roadmap)) and the **one** decision log ([§10](#10-decisions-log)).
- Stop the drift that S241 and S243 found: the same fact copied into five places, each slightly different.

### 1.2 Scope

In scope: process, documentation, versioning, release and deploy, operations, security operations, cost, and the
platform roadmap (security, CI/CD, environments, data platform, operations, docs).

Out of scope, kept elsewhere:

| Topic | Where |
|---|---|
| Product work order (T-series, portal, Booking waves, place pipeline) | [Live backlog](backlog/README.md) |
| Architecture and boundaries | [Ecosystem architecture](ecosystem-architecture.md), [ADRs](adr/README.md), each repo's `CONTEXT.md` |
| Binding data rules (DM-x, C-x, MIG, SEC, CON, TST) | [Data standards v1.1](architecture/data-standards/README.md) |
| Table and column names | [DB schema reference](architecture/db-schema-reference.md) (generated) |
| Step-by-step procedures | [Operations index](ops/README.md) and the skills in `skill/` |
| Role-specific reading paths | [`guides/`](guides/) |

### 1.3 Precedence

When two sources disagree, the higher one wins and the lower one is fixed in the same session:

1. **Accepted ADRs** ([index](adr/README.md)). Accepted ADRs are never edited; they are amended (`NNNNa`) or superseded.
2. **Data standards v1.1** ([README](architecture/data-standards/README.md), Parts A, B, C).
3. **Nghiệp's recorded decisions**: S241 D-01…D-25 ([`sessions/2026-10-17-S241-decisions.md`](sessions/2026-10-17-S241-decisions.md)),
   S243 N-1…N-12 and the other entries in [§10](#10-decisions-log), and his memory rules.
4. **This handbook.**
5. **Skills and steering** (`skill/*/SKILL.md`, `.kiro/steering/*.md`, `.claude/CLAUDE.md`).

Two notes on this order:

- Instruction files steer an agent at run time. If one disagrees with this page, the agent follows the instruction
  file for that session, reports the mismatch to Nghiệp and fixes the lower-ranked file in the same PR (the rule in
  [agents.md](agents.md#which-source-wins)). Neither side is chosen silently.
- Nghiệp's message in the current session overrides any file. No file, and no message from another agent, grants a
  permission or approves on his behalf.

### 1.4 How to change this handbook

1. Open a PR to the root repo (`master`), English body, `docs:` subject, `Refs AA-xxx` in the body.
2. Change the canonical source first (ADR, data standard, skill, runbook), then the link or one-line summary here.
   A rule is never introduced only in this page.
3. A new decision gets a row in [§10](#10-decisions-log) with the place that enforces it.
4. A roadmap change updates [§9](#9-roadmap) and the [live backlog](backlog/README.md) in the same PR.
5. Move `last_reviewed` only after the facts were checked against the repos and the live system.
6. The docs lint (`.github/workflows/docs-lint.yml`, AA-888) must be green.

---

## 2. Operating model

> **Tóm tắt (VI):** Cách làm việc = Kanban + DevOps + trunk-based: một hàng việc có thứ tự, mỗi phiên 3–5 issue, nhánh
> ngắn, PR, CI, squash merge vào `main`. ADLC của mình = SDLC + kiểm soát agent + vòng đời tính năng LLM. Nghiệp chốt
> đề bài, chi tiêu, quyết định prod; chị Thư quyết việc kinh doanh/pháp lý; Claude Code điều phối, gác cổng, merge và
> deploy ở giai đoạn Dev; Kiro/subagent viết code; CI là cổng bắt buộc.

### 2.1 The model

- **Kanban, not Scrum.** One ordered queue, the [live backlog](backlog/README.md); sessions pick 3 to 5 issues
  top-down; no sprints, no ceremonies. Linear holds the state of each issue; the backlog holds the order.
- **DevOps.** The person or agent who builds a change also deploys it, verifies it live and watches it.
- **Trunk-based development** (ADR-2026-023). Short branches, PR, required CI, squash merge to `main` (`master` in
  root). No `develop` branch. Work in a branch or worktree from the latest `origin/main`.
- **ADLC = SDLC + agent control + LLM feature lifecycle.** ADLC is not a standard term; this is our definition:
  - *Agent control*: agents write most of the code. The human work moves to writing the issue (DoR), giving
    context (`CONTEXT.md`, steering, skills), gating (CI, review, live verify) and holding the dangerous
    permissions.
  - *LLM feature lifecycle* (LLMOps): prompt and model versions, evals, the cost ledger and shadow runs for the
    writer, judge and validate roles ([§5.7](#57-llm-prompts-and-models)).
- **AI amplifies the process you already have.** Good DoR, CI and live verify pay off twice when agents write
  most of the code; weak ones fail twice as often.

### 2.2 Sources of truth for process state

| What | Canonical | Others only link |
|---|---|---|
| Order of work | [Live backlog](backlog/README.md) | Notion memory |
| State of an issue | Linear (team AA_Ecosys) | backlog, session log |
| What happened in a session | `docs/sessions/` (Vietnamese) | Notion memory HOT (summary + link) |
| Progress told to Ms. Thư | Jira (drafted, then approved by Nghiệp) | — |
| How to do a task | `skill/*/SKILL.md` | steering summary, CLAUDE.md |
| Lessons | [`skill/aa-lessons/lessons.md`](../skill/aa-lessons/lessons.md) | — |

When repo, Notion and memory disagree: repo > canonical Notion page > memory > skill
([`session-workflow.md`](../.kiro/steering/session-workflow.md)).

### 2.3 Roles

| Role | Does | Does not | Guide |
|---|---|---|---|
| **Nghiệp** (engineer, owner of the platform) | Approves DoR, ADRs, spend (D-19), prod decisions; overrides the deploy gate; edits underscore env vars and `~/.claude/CLAUDE.md` by hand | — | [New engineer](guides/new-engineer.md), [DevOps](guides/devops.md) |
| **Ms. Thư** (CEO, business owner) | Business, legal and commercial calls; reviews release notes, the cost summary and UAT | Technical approvals | [CEO guide](guides/ceo.md) (EN + VI) |
| **Claude Code, main session** | Picks work, writes or delegates code, gates, merges and deploys on Dev in the dev phase, runs Terraform and DB Migrate, updates Linear | Posts to Jira without approval; touches prod (when it exists) without Nghiệp | [Agent index](agents.md) |
| **Kiro and subagents** | Code, tests and commits on a branch | Push, merge, apply, ECS/RDS/IAM writes, secrets ([`subagent-guardrails.sh`](../.claude/hooks/subagent-guardrails.sh)) | [Agent index](agents.md) |
| **`kiro-reviewer`** (agent) | Reviews risky PRs: auth or permissions, migration or schema, CI/workflow/secret, data deletion ([`kiro-reviewer.md`](../.claude/agents/kiro-reviewer.md)) | Merge | — |
| **CI** | Required checks: CIS 5, Booking 5, TripPlanner 2. The root docs lint runs on every root PR but cannot be a required check (private repo on GitHub Free); the merging agent checks it is green before merging | — | [CTO](guides/cto.md#quality-gates) |
| CTO, CIO, PM readers | Governance, security and compliance, planning views | — | [CTO](guides/cto.md), [CIO](guides/cio.md), [PM](guides/pm.md) |

Merge rights by phase: [§6.5](#65-merge-rights-by-phase).

---

## 3. Lifecycle stages

> **Tóm tắt (VI):** Mỗi việc đi qua: ý tưởng → sẵn sàng (DoR) → thiết kế/ADR → code → review/test → deploy → kiểm live
> (aa-ship) → vận hành → rút bài học → chi phí. Bảng dưới ghi ai làm, ra sản phẩm gì, lưu ở đâu. "Xong" chỉ khi đã merge,
> CI xanh, deploy COMPLETED và kiểm endpoint live có bằng chứng.

| # | Stage | What happens | Who | Artifact | Where |
|---|---|---|---|---|---|
| 1 | Idea | A request from Ms. Thư (Jira), a finding from an audit or alarm, a lesson | Nghiệp | Linear issue | Linear; Jira for the business side |
| 2 | Order | Rank against the queue; time-gated checks | Nghiệp + Claude Code | Backlog row | [Live backlog](backlog/README.md) |
| 3 | **Ready (DoR)** | Problem, goal, scope, acceptance, verify, risk class, dependencies, docs impact | Claude Code drafts, Nghiệp confirms | Issue body | [DoR template](templates/definition-of-ready.md), [`aa-linear-issue`](../skill/aa-linear-issue/SKILL.md) |
| 4 | Design | Boundary, contract or hard-to-reverse choice | Claude Code proposes, Nghiệp accepts | ADR or amendment; `CONTEXT.md`; contract version | [ADR placement](../skill/ai-nghiep/references/adr.md), [ADR template](templates/adr.md), [contracts](contracts/README.md) |
| 5 | Build | Code on a short branch or worktree; implementation note while working | Kiro / subagent / Claude Code | Conventional commits, `Refs AA-xxx` | `docs/implementation-notes/<ISSUE>.md` (and per repo) |
| 6 | Review and test | CI; agent review for risky classes; docs checklist | CI + Claude Code + `kiro-reviewer` | PR = change record (risk, rollback, cost, docs) | [PR template](../.github/pull_request_template.md) |
| 7 | Release and deploy | Merge; image `dev-<sha>`; deploy Dev; migrations through DB Migrate | Claude Code (dev phase) | Task-definition revision; Vercel deployment; later tag + CHANGELOG | [§5](#5-versioning), [§6](#6-releasing-and-changing-features), [ops index](ops/README.md#how-each-app-is-deployed-app-01) |
| 8 | **Verify (Done)** | Rollout COMPLETED, api and worker on the same SHA, live endpoint check, UI check | Claude Code | "Verified live" comment with evidence | [`aa-ship`](../skill/aa-ship/SKILL.md) |
| 9 | Operate | Alarms, Sentry, incidents, backups, secrets, access | Nghiệp + Claude Code | Runbook runs, incident write-ups | [§7](#7-operations) |
| 10 | Learn | Root cause → rule → CI guard | Claude Code writes, Nghiệp approves | Lesson line, guard test, postmortem | [`lessons.md`](../skill/aa-lessons/lessons.md), [postmortem template](templates/postmortem.md) |
| 11 | Cost | Quote before spend; monthly review; anomaly alerts | Claude Code reports, Nghiệp decides | Monthly cost and capacity review | [§8](#8-cost-finops) |
| 12 | Tell the business | Business release note for shipped and verified work | Claude Code drafts, Nghiệp approves | Jira comment | [Release note template](templates/release-note.md), skill `aa-jira-update` |

Notes:

- An issue that misses a DoR section is not handed to Kiro or a subagent.
- Stage 8 is the Definition of Done. Merged and green is not done ([§6.4](#64-definition-of-ready-and-done)).
- Journals (session logs, audits, implementation notes, backlog) record history. They are never the current truth
  for a rule.

---

## 4. Documentation system

> **Tóm tắt (VI):** Tài liệu theo Diátaxis (tutorial, how-to, reference, explanation). `docs/README.md` là cửa vào duy
> nhất: danh mục mọi tài liệu kèm chủ, nhịp review, trạng thái. Git là nguồn sự thật; Drive chỉ chứa bản PDF xuất cho chị
> Thư; trang `/admin/docs` (AA-898) sau này chỉ hiển thị, đồng bộ từ CI theo allowlist, tài liệu bảo mật/audit chỉ owner
> xem (N-3). Docs đổi cùng PR với code; thứ gì sinh được thì để CI sinh; agent chỉ đổi `last_reviewed` khi đã kiểm thật.
> Tài liệu kỹ thuật viết tiếng Anh; hướng dẫn chị Thư và hướng dẫn theo vai trò song ngữ (N-7).

### 4.1 Diátaxis: four kinds of page

| Type | The reader needs | Shape | Examples |
|---|---|---|---|
| Tutorial | To learn by doing | Guided steps with a sure result | [Onboarding](onboarding.md), [new engineer guide](guides/new-engineer.md) |
| How-to (incl. runbook) | To do one task | Steps, one-line commands, verify, rollback | [Runbooks](ops/README.md#runbooks), [playbooks](ops/README.md#something-is-wrong) |
| Reference | Exact facts | Dry tables; generated when possible | [Schema reference](architecture/db-schema-reference.md), [secrets register](security/secrets-register.md) |
| Explanation | Why it is like this | Context, design, trade-offs, links to ADRs | [Architecture](ecosystem-architecture.md), [data standards](architecture/data-standards/README.md), this page |

One page, one type, one main reader. Journals (`docs/sessions/`, `docs/audits/`, `docs/implementation-notes/`,
`docs/backlog/`, `docs/research/`) are outside Diátaxis and are not current truth.

### 4.2 The catalog is the one entry point

[`docs/README.md`](README.md) (CAT-00) lists every maintained page with its ID, type, path, mode (hand-written or
generated), owner, review cadence, audience and status, and opens with "Start here" by role. A page that is not in
the catalog is a journal or a draft. Agents start from [`agents.md`](agents.md) and [`llms.txt`](llms.txt).

### 4.3 Where docs live

| Place | Role | Rule |
|---|---|---|
| **Git** (root, Infra, app repos) | The only source | Changed by PR, reviewed with the code |
| Root repo (private) | Ecosystem docs, account map, security and infra docs, audits, registers by name | [Where a page may live](STYLE.md#where-a-page-may-live-sec-06) |
| App repos (public) | `CONTEXT.md`, app ADRs, public-safe how-tos, LLM docs without tenant data | No account IDs, ARNs, SG/VPC IDs, inventories, secret lists, security reports (DM-6.10, D-14, D-25) |
| Google Drive (AdventureAsia folder) | PDF exports and UAT videos for Ms. Thư | Never a source; each export says which commit it came from |
| `/admin/docs` in the CIS admin (AA-898, later) | A **reader**, not an editor | Synced from a CI checkout of tracked files only, never a laptop; allowlist = catalog entries in root and Infra; always excluded: the git-ignored real-data backups folder, `docs/calib/`, `docs/sessions/`; security and audit pages (`docs/security/`, `docs/audits/`) are synced but served only to the `owner` role through a backend check (N-3); bucket tagged `App=cis`, encrypted, public access blocked, about 0.01 USD/month stated in the PR. Built after AA-885 (done) |
| A separate docs site (Starlight on S3 + CloudFront + Cognito) | Stage 3 only | Trigger: more than two engineers, a contractor without admin access, or prod docs that must be readable while CIS is down. No MkDocs, no Backstage, no Vercel Pro for docs |

Before prod, a break-glass PDF of the operations index, rollback runbooks and incident response goes to Drive,
because the admin docs page goes down with CIS (AA-880).

### 4.4 Front-matter, templates and style

- Front-matter: [`templates/frontmatter.schema.json`](templates/frontmatter.schema.json). Required `id`, `title`,
  `type`, `status`, `owner`, `last_reviewed`; `status` is one of draft, active, deprecated, superseded, archived;
  `audience` uses owner, staff, engineer, devops, cto, cio, pm, agent.
- Templates: [`templates/`](templates/) (runbook, how-to, reference, explanation, ADR, postmortem, cost report,
  release note, UAT report, Definition of Ready, role guide).
- Style: [`STYLE.md`](STYLE.md): voice, one-line AWS CLI with `--profile` and `--region`, names not resource
  IDs, the "tested" rule for runbooks, callouts, diagrams, naming.
- ADRs keep their own `Status` line and are amended, not edited ([ADR placement rule](../skill/ai-nghiep/references/adr.md)).

### 4.5 Docs-as-code rules

1. **Docs change in the same PR as the code they describe.** The [PR template](../.github/pull_request_template.md)
   carries the docs checklist; AA-890 adds a template to every repo.
2. **What triggers a doc update:**

   | When you change | Update |
   |---|---|
   | App boundary, stack, data ownership | That repo's `CONTEXT.md` (+ [architecture](ecosystem-architecture.md) if ecosystem-wide) |
   | A decision that only touching another repo could reverse | ADR or amendment ([placement](../skill/ai-nghiep/references/adr.md)) |
   | Schema structure | Nothing by hand: the DB Schema Dump workflow opens the reference PR; merge it (DM-11.2) |
   | A public endpoint or response shape | OpenAPI (generated, AA-899) and the CHANGELOG (AA-891) |
   | An event or read model between apps | A new contract version per [contracts](contracts/README.md) |
   | An operational procedure | The runbook and the [ops index](ops/README.md) |
   | A paid AWS resource | Monthly cost in the PR (D-19) |
   | A prompt, model or route | Eval run ID in the PR ([§5.7](#57-llm-prompts-and-models)) |
   | A flag | A row in the [flag register](ops/feature-flags.md) |

3. **Generated pages are never edited by hand.** They carry `generated: true`, a generator and a "GENERATED … do
   not edit" first line; only the generator's PR changes them.
4. **`last_reviewed` means checked against the real system.** An agent moves it only after running the verify
   command or reading the source, and says so in the PR. A typo fix does not move it.
5. **New agent-written pages start as `draft`** until Nghiệp has read them (a batch read at session end is fine in
   the dev phase).
6. **No binaries in git.** Spreadsheets, archives and videos go to Drive or S3; git keeps the link.
7. **No secret values, no real customer data, no dumps.** Secret names are fine in the private root repo.
8. **Parallel PRs never append to the same note file.** Each writes its own section or file (lesson in
   [`lessons.md`](../skill/aa-lessons/lessons.md)).
9. **CIS `docs/` is tracked only after a scan.** AA-889 replaces the blanket ignore with "Markdown tracked,
   binaries ignored", after gitleaks and the resource-ID check pass on every file to add. Infra or security details
   move to the private root repo; Nghiệp reviews the list of added files once (DM-6.10, D-25).
10. **Deprecate, then archive** ([STYLE](STYLE.md#deprecate-and-archive)). An outdated page gets `status: deprecated`,
    `superseded_by` and a warning line at the top; after one quarter unused it moves to `docs/archive/YYYY/` with
    `status: archived`. ADRs are never archived (superseded or amended only).

### 4.6 Generated reference

| Reference | Source | Generator | Status |
|---|---|---|---|
| DB schema (all schemas, roles, grants, RLS) | Live catalog | Infra DB Schema Dump workflow (nightly + after every DB Migrate apply), PR into root | Live ([reference](architecture/db-schema-reference.md)) |
| Schema ownership | Infra `db/owners.yaml` (the registry, DM-1.2) | Registry test in Infra; [schema-ownership](database/schema-ownership.md) explains it | Live |
| Contracts | JSON Schema per version | Hand-written, hash pinned in tests | Live; registry table AA-826 |
| OpenAPI per app | FastAPI | CI export + oasdiff (AA-899) | Booking partial; CIS planned |
| Env-config register (names only) + ERD | Live task definitions, Lambda and Vercel config | Infra workflow, PR into root (AA-894) | Planned |
| Alarm, inventory, network and IAM tables | Terraform | Infra docs workflow (AA-893) | Planned (step 1, the runbook link in each alarm description, is live: Infra #213) |
| LLM route table | `shared.llm_role_config`, `shared.llm_model_catalog` | Export (AA-900) | Planned |
| Freshness report | Front-matter | Docs lint weekly run (AA-888) | Ships with the bundle PR; runs weekly once merged (scheduled workflows run only from the default branch) |

Generators that need AWS run in Infra, which has the OIDC roles; the root repo has no AWS access.

### 4.7 Freshness and lint

The docs lint ([workflow](../.github/workflows/docs-lint.yml), [tools](../tools/docs/README.md), AA-888) checks on
every docs PR: front-matter against the schema and unique IDs, ADR status and index, no backslash-continued AWS CLI,
internal links (offline), Markdown style (warning), literal resource IDs (warning in private repos, error in the
public ones once their job lands). Secrets are checked by a separate workflow on every PR, any path
([`secret-scan.yml`](../.github/workflows/secret-scan.yml): gitleaks on the added lines, plus a nightly full-history
scan, AA-981). A weekly run writes the freshness report: pages
past `review_every_days` (default 90) and runbooks with an old `last_tested`. Freshness warns; it never blocks a
merge. At session start, pick one or two stale pages to review with the session's work.

Once a quarter (about 30 minutes, in the first session of the quarter, with the access review in
[§7.6](#76-access)): go through the freshness report, check each section index for orphan pages, ask the six
Well-Architected pillar questions ("if X breaks, which page tells us what to do?"), read the CEO guide as Ms. Thư
would, and run the Diagnose part of one random runbook on Dev. The cadence belongs to U-38 (AA-838).

### 4.8 Language

The rule is [`language-convention.md`](../.kiro/steering/language-convention.md):

- Technical docs, code, commits, PRs, Linear: **English**.
- Conversation with Nghiệp, session logs, Notion memory, advisory audits for Nghiệp in `docs/audits/`: **Vietnamese**.
- **Bilingual EN-VI** (N-7): the guide for Ms. Thư and the role guides, same content in both languages; this
  handbook carries a Vietnamese summary under each section.
- Business summaries for Ms. Thư (cost summary, business release note, postmortem summary): Vietnamese, plain, no
  internal Linear keys.

### 4.9 What fact lives where

| Fact | Canonical home | Others only link |
|---|---|---|
| Stack, boundaries, ownership of one app | That repo's `CONTEXT.md` | CLAUDE.md, skills |
| Architecture decisions | ADRs (root for two or more repos, else the repo) | architecture page, `CONTEXT.md` |
| Table and column names | [Schema reference](architecture/db-schema-reference.md) (generated) | skill `aa-cis-schema` (explains only) |
| Which repo owns which schema | Infra `db/owners.yaml` | [schema-ownership](database/schema-ownership.md) |
| Data rules, retention windows, approvals | [Data standards](architecture/data-standards/README.md); DM-7 is the only retention registry | everything else |
| API shape | OpenAPI generated from code | README, frontend |
| Events and read models between apps | [Contracts](contracts/README.md) | app code (hash pinned) |
| Real infrastructure | Terraform in AA-CIS-Infra + its state | Infra `CONTEXT.md` |
| AWS account IDs | The account map in [onboarding](onboarding.md#account-map) | agent instruction files keep a matching copy |
| Running version | `/health` of each service; later GitHub Deployments | session log |
| Secrets (names) | [Secrets register](security/secrets-register.md) (YAML first) | env-config register links |
| Flags and kill switches | [Flag register](ops/feature-flags.md), [job-kind register](ops/job-kinds.md) | — |
| Process | `skill/*/SKILL.md` | steering summaries |
| Platform roadmap and decisions | [§9](#9-roadmap), [§10](#10-decisions-log) | [backlog §3a](backlog/README.md#3a-platform-roadmap-keys-plat-01) orders the U-xx keys |

---

## 5. Versioning

> **Tóm tắt (VI):** Một "phiên bản" phải truy được từ commit tới release note: commit Conventional có `Refs AA-xxx` →
> image `dev-<sha>` bất biến → task definition → `/health` trả `git_sha` → (sắp có) tag SemVer + CHANGELOG do
> release-please tạo (AA-891, cần token GitHub App AA-901). Migration đánh số, chỉ tiến, đổi schema theo expand/contract.
> Terraform chỉ apply từ `main`. API: export OpenAPI + oasdiff trước (AA-899), ADR 0013 trước khi đổi sang
> `/booking/v1`. Prompt: `prompt_version` đi cùng ledger v2 (AA-804); eval chạy tay trên bộ mẫu chuẩn (D-23).

### 5.1 Commits

- Format: the global commit rule (`feat|fix|chore|refactor|docs|ci|test|perf: description`, English subject),
  body `Refs AA-xxx`. Never `[AA-xx]` in the subject; never `Fixes` or `Closes` (Linear would close the issue). The
  PR title becomes the squash commit, so the PR title follows the same rule.
- This is valid Conventional Commits. `Refs AA-xxx` without a colon is body text, not a footer; Linear reads it and
  release-please ignores it. Keep it.
- For release-please: `feat!:` or a `BREAKING CHANGE:` footer marks a breaking change. CHANGELOG shows `feat`, `fix`,
  `perf`, `revert`; it hides `docs`, `chore`, `refactor`, `test`, `ci`, `build`.
- PR-title lint in every repo: AA-890.

### 5.2 App versions and releases (AA-891)

| Repo | Scheme | First tag | `1.0.0` when |
|---|---|---|---|
| AA-CIS-App | SemVer, release-please | `v0.4.0` (code says 0.3.0 today) | First prod with a stable public `/v1` OpenAPI |
| AA-Booking | SemVer | `v0.2.0` | Prod and a B2B partner on the API |
| AA-TripPlanner-Web | SemVer | `v0.4.0` | Public prod |
| AA-CIS-Infra | Optional (dated tag on a big apply, or release-please) | `v0.1.0` | A separate prod environment |
| AA-Ecosys (root) | No releases; docs version by PR | — | — |

How release-please is set up (AA-891):

- Manifest mode, one package per repo, `bump-minor-pre-major: true` so a breaking change stays on `0.x`.
- The release PR must trigger the required checks, so the action uses the **GitHub App token from AA-901**
  (0 USD). A fine-grained PAT is the fallback only if AA-901 slips, and then it gets a row in the
  [secrets register](security/secrets-register.md) (AA-878).
- CIS keeps one version constant (today the version is written twice in the API), marked for the bot to bump.
- `CHANGELOG.md` and the manifest are path-ignored by the deploy workflows, or one extra deploy is accepted.
- The bot's release PR has no `Refs AA-xxx`; this exception is written into `skill/aa-ship` §1 by AA-891. Nghiệp
  adds the same line to his global rules by hand (N-6).
- Cadence on Dev: cut a release weekly or at a milestone shown to Ms. Thư, not on every merge.
- The CHANGELOG is for engineers (Keep a Changelog sections). The release note is for the business: written by hand
  from the CHANGELOG, only for verified-live features ([template](templates/release-note.md)).
- GitHub Deployments and DORA numbers stay with the rest of U-47 at first prod.

### 5.3 Images and what is running

- **Images are immutable and named by commit:** CIS `dev-<sha>`, Booking the git SHA; ECR IMMUTABLE, CIS keeps the last
  30 `dev-*` images and expires untagged ones after 7 days (AA-869). Never `:latest`.
- A task-definition revision points at one SHA, so **rollback = redeploy the previous revision**
  ([§6.3](#63-rollout-and-rollback)).
- **Every service says what it runs:** CIS `/health` returns `git_sha` and `/health/ready` checks readiness (AA-884,
  live on CIS main); Booking `/booking/health` returns `git_sha` and `/booking/health/ready` checks the DB and the
  required migration. The deploy smoke asserts the SHA. The worker reports its SHA too (api and worker must match).
- When release tags exist, the release tag is added to the same digest; nothing is rebuilt (build once, deploy
  many).
- The admin Apps page (AA-884) shows `service | git_sha | version | deployed_at` for every service.
- Frontends: each Vercel deployment carries its commit; showing the short SHA in the admin footer uses an
  underscore variable that Nghiệp sets by hand.

### 5.4 Database migrations

- **Numbered, forward-only, idempotent, applied by CI**: keys `NNN` (CIS), `tp-NNN`, `bk-NNN`, roles `rl-NNN`;
  `shared.schema_versions` records them. Never edit an applied migration; add a new one. Never run DDL from a
  laptop, ECS exec or app start-up.
- **The D8 path** ([DM-11.2](architecture/data-standards/02-data-management.md#11-change-management), Part A MIG-4):
  migration-only PR → byte copy into Infra → Copy Guard → DB Migrate `check` → `apply` → merge the regenerated schema
  reference PR → then the code PR. The runbook is [DB Migrate](ops/runbooks/db-migrate.md).
- **Expand / contract** for every change that two app versions must survive:
  1. Expand: add the nullable column or the new table (migration-only PR, applied first).
  2. Deploy code that writes old and new; backfill through a job.
  3. Switch reads to the new structure.
  4. Contract in a later release: drop the old (`-- migrate: destructive`, automatic snapshot before).
  Version N and N+1 of the app both run on the schema, so an app rollback is always safe.
- DB Migrate `apply` waits for every job table to be idle (DM-11.4).
- Readiness already checks the schema: CIS `/health/ready` reports `required_schema` next to the applied version, and
  Booking `/booking/health/ready` checks the required migration. Later (U-50): fail fast at start-up as well.

### 5.5 Terraform

- Pin Terraform and providers, commit the lock file; engine versions (PostgreSQL 15, ElastiCache) are pinned in code.
- **Apply only from `main` through the Terraform Apply workflow.** OIDC trust for the deploy and apply roles accepts
  only `refs/heads/main` (AA-866). Never apply from a worktree or branch before merge (that left `main` behind the
  real infrastructure once; see [`lessons.md`](../skill/aa-lessons/lessons.md)).
- Every PR states what changes, the monthly cost and the rollback, with the plan attached.
- The GitHub environment that applies Dev is still named `prod`. Renaming it belongs to ADR 0012 (AA-880, D-16,
  C7.2d); do not rename it now.
- Stray `.bak` and `.tfplan` files in Infra were removed (Infra #211, AA-890). Confirm versioning on the Terraform
  state bucket (not checked in S243). The full Terraform flow (plan comment, apply bound to the plan,
  drift check) is U-42, triggered before prod or by the next drift incident.
- Rollback: [Terraform rollback runbook](ops/runbooks/rollback-terraform.md).

### 5.6 API versions

- The CIS tenant API already has the major version in the URL (`/v1/...`). CIS `/admin/*` and Booking `/booking/*`
  have none yet.
- Inside a major version only additive changes (new field, new endpoint). Removing or renaming a field, changing a
  type or a meaning = a new major or an expand/contract.
- **Now (AA-899, U-44 pulled early, 0 USD):** CI exports `openapi.json` for CIS and Booking and runs oasdiff against
  `main`; a breaking change fails unless labelled. This needs `response_model` on public routes.
- **Before any `/booking/v1` prefix:** ADR 0013 HTTP conventions in root (it touches Booking, its frontend and
  TripPlanner, DM-11.1), citing Part A CON-3 to CON-5 (N-11).
- Deprecation: announce, then `Deprecation` (RFC 9745) and `Sunset` (RFC 8594) headers and a CHANGELOG
  "Deprecated" entry, then remove after the window.
- Events between apps follow [contracts](contracts/README.md): additive = minor, breaking = new major served in
  parallel for at least 30 days.

### 5.7 LLM prompts and models

- **Models** are pinned by exact ID in `shared.llm_model_catalog`; routes live in `shared.llm_role_config` (audited,
  with shadow runs in `shared.llm_shadow_log`). App ADRs in CIS cover the catalog and routing.
- **Every paid call goes through the gateway** and lands in `shared.llm_call_log` (DM-10.4); ad-hoc scripts use
  `stage = adhoc_<issue>` and a role in writer, judge, validate.
- **Prompt version:** a nullable `prompt_version` column ships **inside the AA-804 ledger v2 migration** (one
  expand, through D8; N-5). Until then the prompt register (AA-900) maps prompt id and version to file and stage.
- **Evals:** the golden set of about 100 samples built from existing data is AA-729. Evals run **by hand or by
  dispatch** (D-23), through `LLMClient` with `stage = adhoc_aa900` and a spend cap. A PR that changes a prompt,
  model or route records the eval run ID. A per-PR eval trigger is not enabled (N-4: it would be new recurring spend).
- **AA-900 is to be narrowed** (N-4, N-5) to the prompt register, the eval runbook and a generated route table, so it
  does not build the golden set (AA-729) or touch the ledger (AA-804). The Linear issue still lists the
  `prompt_version` migration and a per-PR eval workflow; its scope and Done-when are updated before work starts.
- The AI platform ADR 0009, the ledger's `app` and `is_shadow` columns and the AI Use Register are AA-804 (U-34).

### 5.8 Docs versions

- Docs in a repo follow that repo's tags: the docs at `v0.4.0` are the docs of `v0.4.0`. No separate mechanism.
- Root docs have no release; the PR history is their version. Pages that others depend on carry their own version
  table: the [data standards](architecture/data-standards/README.md#changing-this-standard), contracts (`vN.M`),
  `owners.yaml`.
- No versioned docs site until outside users run two major API versions at once.

---

## 6. Releasing and changing features

> **Tóm tắt (VI):** Hiện chỉ có Dev, dữ liệu test (D-01). Prod là instance RDS riêng trên acc2, chốt khi có ngày go-live
> (ADR 0001, C7.2a, D-16/D-17, AA-880). Deploy khác release: tính năng mới có thể deploy "tối" sau cờ rồi bật dần. Cờ
> ghi trong `docs/ops/feature-flags.md`; cờ tenant pool là control bảo mật (D-12). Xong = theo aa-ship; sẵn sàng = theo
> mẫu DoR. Giai đoạn Dev agent tự merge khi CI xanh; từ prod/tenant trả tiền đầu Nghiệp duyệt PR rủi ro (DM-11.5).

### 6.1 Environments

| Environment | Purpose | Today | Rule |
|---|---|---|---|
| Local | Develop, unit tests | Yes | — |
| PR preview (Vercel) | See a frontend change before merge | Yes; Playwright UI smoke on CIS previews (the last three `ui-smoke.yml` runs were skipped: fix in AA-879) | Vercel Hobby until the first paying tenant (D-18) |
| **Dev** (acc2) | Integration, allowed to break, demo | Yes | **Test data only** (D-01: exact counts on 17/10/2026; Part C C7.1a forbids prod PII on Dev). No grace windows or time-gated watches: generate evidence now |
| Staging | — | No | Not planned. When prod exists, Dev acts as pre-prod; PR previews cover UI review |
| **Prod** | Real users | No | A separate RDS instance and services **on acc2** (ADR 0001, Part C C7.2a, D-17); account consolidation research AA-864 feeds ADR 0012. Layout, gate and naming in ADR 0012 when go-live is dated (D-16, AA-880, U-40). Prod targets: DM-9.6, C7.2 |

**Build once, deploy many:** the same image digest moves from Dev to prod; only configuration and secrets differ.

### 6.2 Deploy is not release: feature flags

- *Deploy* = the code runs in an environment. *Release* = users see the feature. A flag separates them: merge and
  deploy dark, turn it on for one tenant, then for all; in trouble, turn the flag off instead of rolling back.
- **Register:** [`ops/feature-flags.md`](ops/feature-flags.md) (OPS-06), a document, not a table: DM-1.5 keeps
  `shared` for the kernel, so there is no `shared.feature_flag`. If an app ever needs a flag table, it goes in that
  app's own schema; a flag shared by several apps needs an ADR.
- Kinds: `release` (temporary, has a `remove_by` and an issue to remove it), `ops` (kill switch, permanent),
  `security` (never removed by date).
- **Tenant-pool flags are a security control** (Part C C2.3g, DM-8.4, D-12): an unreadable or missing flag means the
  tenant pool; only an explicit `"false"` moves one route to the admin pool; the emergency switch is in
  [break-glass](ops/runbooks/break-glass.md). They have no `remove_by`.
- The order for a breaking change across apps: **database first, producer next, consumer last, remove the old
  thing at the very end**:

  | Step | Repo | Action |
  |---|---|---|
  | 1 | Owner | Expand migration (migration-only PR, D8) |
  | 2 | Root | Contract minor version (additive field) |
  | 3 | Producer | Write and serve old and new; backfill through a job |
  | 4 | Consumer | Read the new field behind a flag |
  | 5 | — | Flag on for one tenant, verify, then all |
  | 6 | Producer | Mark the old field deprecated (CHANGELOG, headers for REST) |
  | 7 | Owner + producer | After the window: contract migration and a new contract major if a field is removed |

### 6.3 Rollout and rollback

Rollback first, investigate later. Roll forward only when rollback is unsafe (for example after a migration that
cannot be undone).

| Component | Rollout | Rollback |
|---|---|---|
| CIS api and worker (ECS) | Rolling, circuit breaker, deploy gate on `shared.job` | [CIS rollback](ops/runbooks/rollback-cis.md) (previous task definition, api and worker on the same SHA, then revert on `main`) |
| Booking (ECS) | Rolling, circuit breaker, job guard, SHA smoke | [Booking rollback](ops/runbooks/rollback-booking.md) |
| Frontends (Vercel) | CI-created deployments when `frontend/**` changes | [Vercel rollback](ops/runbooks/rollback-vercel.md) (instant rollback, or redeploy an older commit) |
| TripPlanner Lambdas | Path-filtered deploy | [TP Lambda rollback](ops/runbooks/rollback-tp-lambda.md); `needs: ci` + smoke is AA-879, the `live` alias is AA-703 (U-54) |
| Database | Forward-only | No schema rollback; roll forward; PITR is the last resort ([PITR restore](ops/runbooks/restore-rds-pitr.md)) |
| Terraform | Plan in PR, apply from `main` | [Terraform rollback](ops/runbooks/rollback-terraform.md) |

Canary, blue/green and CodeDeploy are not used ([§9.3](#93-do-not-do-now)).

### 6.4 Definition of Ready and Done

- **Ready:** the [DoR template](templates/definition-of-ready.md) (problem, goal, scope, acceptance, verify, risk
  class, dependencies, docs impact) under the house issue format of [`aa-linear-issue`](../skill/aa-linear-issue/SKILL.md).
  Ask Nghiệp before creating an issue; every issue has a project; at most 100 unarchived issues per project.
- **Done:** [`aa-ship`](../skill/aa-ship/SKILL.md): merged, CI green, deploy rollout COMPLETED, api and worker on the
  same SHA, live endpoint check (200 and shape), UI check where relevant, reviewed Terraform plan, and a
  "Verified live" comment with evidence. Set by hand, never by a commit keyword.
- Docs part of Done: the PR docs checklist is ticked; a user-facing `feat` or `fix` has a meaningful title (it
  becomes the CHANGELOG line); an LLM change records the eval run ID; a new AWS resource states its monthly cost.

### 6.5 Merge rights by phase

The rule is **DM-11.5** in [data standards Part B §11](architecture/data-standards/02-data-management.md#11-change-management)
(v1.1, S241 D-13, approved S243 N-1), mirrored in [`.claude/CLAUDE.md`](../.claude/CLAUDE.md) and
[`session-workflow.md`](../.kiro/steering/session-workflow.md). In one line: **in the dev phase the orchestrating
agent merges its own PRs after green CI, risky classes after an agent review; from the first prod environment or
the first paying tenant, Nghiệp approves Terraform/IAM, migration, auth/security and data-deletion PRs before
merge.** Subagents never merge (hook). The "Who approves what" table in the same section says who decides each kind
of data change.

What makes the prod gate real later: a separate agent identity (GitHub Apps `aa-agent` and `aa-ci-bot`,
[ADR 0011](adr/0011-github-app-identity-and-merge-rights.md), AA-901), CODEOWNERS on the risky paths (in all five repos
since AA-901, not enforced in the dev phase) and code-owner review turned on at the prod trigger (U-25). GitHub Team is
not bought (D-14, [ADR 0014](adr/0014-repo-visibility-and-github-plan.md)); the private repos rely on `main`-only OIDC
trust and job guards instead, and ADR 0014 lists the choice to make for them at the prod trigger.

---

## 7. Operations

> **Tóm tắt (VI):** Alarm phải dẫn tới runbook (AA-893; bước 1 đã live, Infra #213). Email alarm gửi cả khi ALARM và khi OK (D-20). Sự cố theo
> `incident-response.md`, mỗi sự cố một bản ghi, postmortem không đổ lỗi, bài học vào `lessons.md`. Backup: PITR 7 ngày,
> đã diễn tập ~22 phút; diễn tập lại khi quy trình đổi (S243 K-04) và một lần trước prod, theo quý từ prod (DM-9.3). Secret: register
> AA-878; xoay khi nghi lộ, khi lên prod, sau khi dùng break-glass, không xoay 90 ngày trên Dev. Access review mỗi quý
> (DM-8.10), bằng chứng trong `docs/audits/`. Log bảo mật giữ 365 ngày, log app 30 ngày (D-09).

Start page: [operations index](ops/README.md) (OPS-01). Day-to-day guide: [DevOps guide](guides/devops.md).

### 7.1 Observability

| Signal | Today | Next |
|---|---|---|
| Logs | CloudWatch; **security and audit logs 365 days, application logs 30 days** (D-09, AA-872; the DM-7 retention table) | JSON logs with request id, tenant id and job id only, no PII (AA-871, U-30) |
| Metrics and alarms | CloudWatch alarms for CIS 5xx and p95 latency, ECS, Booking, TripPlanner Lambdas, RDS, jobs, SES, Cognito; e-mail on **ALARM and OK** (D-20); a runbook link in the alarm description (AA-893 step 1, Infra #213: 57 of 65 alarms in us-west-1 on 19/10) | Links on the remaining alarms and a generated alarm catalog (AA-893 step 2); a second channel and SLOs at prod (AA-880, U-49) |
| Errors | Sentry for the CIS backend and frontend (AA-870), PII not sent | Sentry for Booking and TripPlanner (AA-871) |
| Uptime | One free Sentry monitor on CIS `/health`; Booking relies on AWS alarms (AA-870); daily ops-probe Lambda | — |
| Traces | None | Only when a job is slow and unexplained (D-21, AA-842) |
| LLM | `shared.llm_call_log` (cost, account, fallback, job id) | `prompt_version` with AA-804 |
| What runs where | `/health` SHA per service; admin Apps page (AA-884, CIS #838) and ops overview for Ms. Thư (AA-858, CIS #840), both deployed in CIS `dba9b72` | Done for both after the `aa-ship` live verify |

Alarm on symptoms users feel (5xx, health failing, queue stuck, budget passed), not on causes. Remember RED for
services (rate, errors, duration) and USE for resources (utilization, saturation, errors). SLOs mean something only
with real traffic (prod).

### 7.2 Alarms to runbooks

- Every alarm points to a runbook or playbook (AA-893). Step 1, the link in each alarm description, is live (Infra
  #213, 57 of 65 alarms); step 2 is the generated tables. For an alarm without a link, use the symptom table in the
  [operations index](ops/README.md#something-is-wrong).
- Playbooks: [5xx spike](ops/playbooks/5xx-spike.md), [queue stuck](ops/playbooks/queue-stuck.md),
  [LLM cost spike](ops/playbooks/llm-cost-spike.md), [Cognito sign-in](ops/playbooks/cognito-login.md). The SES
  bounce case is a runbook: [SES bounce](ops/runbooks/ses-bounce.md).
- Kill switches per job kind: [job-kind register](ops/job-kinds.md).
- Runbooks follow the [runbook template](templates/runbook.md) and the "tested" rule in [STYLE](STYLE.md#runbooks-and-tested):
  `active` only after a real run (Dev, drill, incident, or DRY RUN for destructive steps); otherwise `draft` with
  the UNTESTED banner.

### 7.3 Incidents and postmortems (one place)

- Procedure: [incident response](ops/incident-response.md) (SEV1-3, the first 15 minutes, who is told, tenant
  notice). Four steps: detect, mitigate (rollback or flag off), fix, review.
- **One record per incident:** the SEV1-2 write-up starts in the Linear issue within 2 working days; the postmortem
  is written from the [postmortem template](templates/postmortem.md) and kept in the single folder named by the
  OPS-04 catalog row (the folder is created with the first postmortem, AA-892). This replaces the earlier
  separate incidents folder proposed in S241; there is no second place.
- Blameless: timeline, root cause, what went well and badly, action items as Linear issues, and one line in
  [`lessons.md`](../skill/aa-lessons/lessons.md). A lesson that a test can check becomes a CI guard and the line is
  removed.
- Ms. Thư gets a three-sentence Vietnamese summary.

### 7.4 Backups and disaster recovery

- Dev: RDS PITR 7 days, deletion protection, final snapshot, automatic snapshot before a destructive migration,
  manual snapshots expire after 30 days unless kept on purpose (AA-869).
- **Drill result:** a full PITR drill passed on 17/10/2026, about 22 minutes against the < 1 h Dev target
  (D-10; evidence [`audits/2026-10-17-S241-restore-drill/`](audits/2026-10-17-S241-restore-drill/)).
- **Cadence (DM-9.3 + S243 K-04):** on Dev, drill again when the restore or rollback procedure changes (K-04) and once
  before prod; quarterly from prod (DM-9.3). A stale `last_tested` on Dev is a warning, not an order (N-2 kept the default).
- Runbooks: [PITR restore](ops/runbooks/restore-rds-pitr.md), [single-schema restore](ops/runbooks/restore-schema.md)
  (draft); [drill index](ops/drills/README.md). The DSN behind a private CNAME, the single-schema rehearsal and the
  removal of the old laptop dumps are AA-829 (U-20); its Done-when is unchanged.
- **Evidence stays in `docs/audits/<date>-S<nnn>-<slug>/`** (C7.2b, DM-8.10, C8a; N-10 kept the default). The drill
  and security indexes only link there.
- Prod targets (Multi-AZ, 14-day PITR, cross-region backup copy, RPO/RTO): DM-9.6 and C7.2b, confirmed in ADR 0012.
- A backup that was never restored is not a backup.

### 7.5 Secrets

- **Register:** [secrets register](security/secrets-register.md), YAML first ([`secrets-register.yaml`](security/secrets-register.yaml)),
  names and metadata only, with a drift check (AA-878, U-26). The env-config register (AA-894) lists only the names
  each service references and links here.
- **Rotation triggers** (D-02, D-03, DM-8.9): on suspected exposure, at go-live, and after any break-glass use. **No
  90-day cycle on Dev.** The monthly check is a drift check of the register, not a rotation. Procedure per class:
  [secret rotation runbook](ops/runbooks/secret-rotation.md).
- The GitHub token and the RDS master password printed in a local S240 transcript rotate at go-live (D-02, D-03);
  they are on the prod checklist (AA-880).
- Runtime secrets live in Secrets Manager; CI gets short-lived AWS credentials through OIDC; no static keys in CI.
- Before any secret or resource write: `aws sts get-caller-identity --profile aa365-admin` and confirm acc2 (DM-8.7).
- Environment variable names with underscores are edited by Nghiệp by hand in VSCode or the console; agents
  describe the change and never generate it.
- The managed RDS master secret comes after the X1 role split (D-04, U-41).

### 7.6 Access

- **Humans reach the database only through S3-mediated ECS exec** over SSM, never SSH or a public endpoint (DM-8.8,
  D-07); exec sessions are logged and kept 365 days; connection logs are on, pgaudit waits for prod (D-08). How:
  [ECS exec runbook](ops/runbooks/ecs-exec-s3-mediated.md), [database operations](ops/database-operations.md).
- **Agents** run on the `aa365-admin` profile (D-15; N-8 kept it). Narrowing the agent's committed permission lists
  (ask/deny, the e2e secret allowlist) is folded into AA-878 (N-12). A least-privilege agent role and no static keys
  on the laptop are trigger items (U-53), not current work.
- **Quarterly access review** (DM-8.10): roles, grants, the IAM roles that read each DB secret, Cognito workforce
  users, GitHub collaborators and apps, the agents' committed permissions, and MCP connectors; run in the first session of each quarter; record in `docs/audits/<date>-S<nnn>-access-review/`; index in
  [security docs](security/README.md#access-reviews-sec-05). The first one is in AA-878; the cadence is AA-838 (U-38).
- Staff sign-in: Cognito workforce pool with e-mail codes (ADR 0006, 0006a); only owners change other people's
  rights (Q2). The legacy password login ends at the AA-816 cutover ([legacy login flag](ops/runbooks/legacy-login-flag.md)).
- Account map and access per person: [onboarding](onboarding.md).

### 7.7 Break-glass

[Break-glass runbook](ops/runbooks/break-glass.md) (OPS-10): the Cognito `breakglass` account with TOTP, the RDS
master (DM-8.9: break-glass once the CIS runtime has its own role), and the tenant-pool emergency switch. The
deploy-gate override is its own runbook ([deploy-gate override](ops/runbooks/deploy-gate-override.md)) and is
Nghiệp's call with a written reason. Every use is named in the session log and on the Linear issue, and is followed by
a rotation ([§7.5](#75-secrets)).

### 7.8 Security baseline and vulnerabilities

- [Security baseline](security/baseline.md) (SEC-01, AA-895): every control with its live status, evidence and open
  issue (AA-873, AA-874, AA-875, AA-876, AA-879).
- [Vulnerability management](security/vulnerability-management.md) (SEC-03): fix times, the exception list with
  expiry dates, monthly triage; Dependabot for Booking and TripPlanner is part of AA-895.

---

## 8. Cost (FinOps)

> **Tóm tắt (VI):** Luật chi tiêu nằm ở DM-10 (data standards), không chép lại ở đây. Mọi tài nguyên AWS có tag `App`;
> tag `Environment` đã có sẵn, chỉ cần nhờ tài khoản trả tiền kích hoạt (0 USD). Chi phí theo app xem ở trang admin
> (AA-884, AA-858). Cost Anomaly Detection miễn phí, đã live (Infra #213). Báo cáo chi phí tháng gộp với review dung lượng C8, lưu
> trong `docs/audits/`, bản đầu cho tháng 10 làm từ 01/11. Mọi chi tiêu mới phải báo giá trước và Nghiệp duyệt từng mục.

### 8.1 Rules, by reference

The spending rules are **DM-10.1 to DM-10.7** in
[data standards Part B §10](architecture/data-standards/02-data-management.md#10-cost-ownership): `App` tags, per-app
budgets, the RDS paid by Infra, every paid call through its seam and ledger, budgets checked in the database, paid
batches as a trial of about 3 then at most about 50 tours, and Nghiệp's approval for any spend change. Added by
decision: **quote the monthly cost before applying any new AWS service or resource and approve item by item**
(D-19). The process around the rules is the [FinOps page](ops/finops.md) (FIN-01).

### 8.2 What is in place

| Guard | State |
|---|---|
| `App` tag | Active as a cost allocation tag since 15/10/2026 |
| `Environment` tag | Already on every Terraform resource (`default_tags`). acc2 is a member account, so Nghiệp asks the payer to activate it; 0 USD. No new `Env` key (DM-10.1) |
| Account budget 250 USD/month + per-app budgets | Live (Infra observability) |
| Cost Anomaly Detection | Free; live (Infra #213, `cost_anomaly.tf`): immediate alerts to the existing SNS e-mail for anomalies of at least 5 USD. AA-896 stays open for the rest (FinOps page, monthly report tool). Per-tag monitors exist only in the management account; per-app budgets cover that |
| LLM and external API caps | `shared.spend_budget` (DM-10.5) |
| Cost per app | Admin cost page and API (AA-884, CIS #838) and the overview for Ms. Thư on the same module (AA-858, CIS #840): deployed in CIS `dba9b72`; Done after the `aa-ship` live verify |
| Budgets on acc1/acc3 (LLM satellites) | Not verified ([FinOps](ops/finops.md)); check in the first monthly review |

### 8.3 Monthly review

- **One monthly report covers cost and capacity:** FIN-02 = OPS-08 = the C8 capacity review (C8a, C8b). Claude Code
  drafts it from the [cost report template](templates/cost-report.md) with the [how-to](ops/cost/README.md); Nghiệp
  approves; it is saved in `docs/audits/<date>-S<nnn>-capacity-review/` with a root PR.
- Data comes from what CIS already stores: `shared.cost_explorer_snapshot` (and the per-App snapshot) plus
  `shared.llm_call_log` (DM-10.4); the script is [`monthly_cost_report.py`](../tools/finops/monthly_cost_report.py).
  **No new script that calls Cost Explorer**; extend the CIS client if a new grouping is needed.
- Content: totals by `App` versus last month, top five services, every change over 20 % with its reason, LLM by
  stage and account, unit costs, budget status, actions, and a five-line Vietnamese summary for Ms. Thư.
- Unit costs: USD per published tour, USD LLM per published tour, USD per trip plan, USD per booking.
- **First report:** the first session on or after 01/11/2026, for October, comparing August, September and October
  per app and service.
- When an alert fires: [FinOps, "When an alert fires"](ops/finops.md#when-an-alert-fires) and the
  [LLM cost spike playbook](ops/playbooks/llm-cost-spike.md).

### 8.4 Cost of the roadmap

| Block | USD/month | Notes |
|---|---|---|
| Docs, CI, runbooks, registers, guides, release-please, OpenAPI check, anomaly detection | 0 | GitHub Actions minutes inside the free tier |
| `/admin/docs` bucket (AA-898) | ~0.01 | Stated in the PR |
| Before the first paying tenant (Redis AUTH/TLS, WAF and throttles, ECR, logs) | ~2-10 | Each item quoted and approved when its turn comes (D-19) |
| 90-day security (GuardDuty limited, CloudTrail hardening, log retention) | ~4-16 | AA-873 |
| Cognito alarms + break-glass secret | ~2.4 | Approved S241 ("Cognito $") |
| Cognito WAF on the customer pool | ~7 | When customer sign-up opens (S241); Apple Developer 99 USD/year with the AA-680 customer login |
| Vercel Pro | ~20 + usage | Only at the first paying tenant (D-18) |
| Prod (U-40) | ~150-300 (rough) | One reconciled number in ADR 0012; the 250 USD account budget includes Dev today |

---

## 9. Roadmap

> **Tóm tắt (VI):** Một bảng duy nhất gộp lộ trình S241 (U-01…U-61) với các issue S243 (AA-887…AA-901) và các mục còn lại
> của lộ trình S243 (Now / Before prod / Later). Mỗi dòng: việc, trạng thái, issue, chi phí, người làm. Việc 0 USD đứng
> trước. Cuối mục là danh sách "không làm bây giờ". Thứ tự làm thật vẫn theo backlog sống; mục §3a của backlog xếp thứ tự các mã U-xx
> và trỏ về đây.

### 9.1 How to use the roadmap

- This table is the **only** platform roadmap. The [live backlog](backlog/README.md) orders the next sessions; its
  [§3a](backlog/README.md#3a-platform-roadmap-keys-plat-01) (PLAT-01) lists the U-xx keys in the order they are
  picked and does not copy the content.
- Product work (T-series, portal, Booking waves, place pipeline) is not here.
- Horizon: **Now** (next sessions), **Tenant** (before the first paying tenant), **Prod** (before the first prod,
  when go-live is dated), **Trigger** (when its trigger fires), **Later** (team or traffic grows).
- Status on 2026-10-19: Done, In progress, Open, Trigger, Not doing (by decision).
- Cost: extra USD per month; 0 first inside each horizon. Owner: who does the work; "Nghiệp" marks a manual step or
  a decision.
- Every issue named here exists in Linear; an issue that is not yet a row of the live backlog is listed under
  "later" in backlog §3a.

### 9.2 The roadmap table

| # | Item | Horizon | Status | Issue | Cost | Owner |
|---|---|---|---|---|---|---|
| U-01 | OIDC deploy/apply/migrate trust limited to `main` | Now | Done | AA-866 | 0 | Agent |
| U-02 | Admin secret scoped to the `dev` environment and rotated in 5 places | Now | Done | S241 chore | 0 | Agent + Nghiệp |
| U-05 | Free GitHub security features, org 2FA, force-push and deletion block | Now | Done (Dependabot for Booking and TripPlanner in AA-895) | AA-867 | 0 | Agent |
| U-06 | Server-side role checks on llm-config, budgets, job-runner writes | Now | Done (constant-time compare in `api/core/secret_compare.py`, CIS #791) | AA-882 | 0 | Agent |
| U-07 | CIS Sentry, API 5xx and p95 alarms, uptime monitor | Now | Done | AA-870 | 0 | Agent |
| U-08 | Blocking pip-audit, deploy concurrency, fail-closed job guard | Now | Done | AA-868 | 0 | Agent |
| U-18 | One security group per caller, ADR 0004b | Now | Done (X1 S10-S14) | AA-852 | 0 | Agent |
| U-21 | Immutable CIS ECR, rollback runbook, incident page, 30-day snapshot expiry | Now | Done | AA-869 | ~1-3 | Agent |
| U-22 | ECS exec session logs, `log_connections` | Now | Done (Infra #161) | — | ~1-5 | Agent |
| — | Log retention 365 days security / 30 days app, OK e-mails | Now | Done | AA-872 | <1-2 | Agent |
| — | Console sections + Staff page; tenant portal split | Now | Done | AA-883, AA-885 | 0 | Agent |
| — | Data standards v1.1 (DM-11.5, C2.3g/DM-8.4, DM-7 rows, C4.2b, DM-11.2, DM-1.2) | Now | Approved (N-1); merges with the bundle PR | AA-889 | 0 | Agent + Nghiệp |
| AA-887 | Docs standard: catalog, templates, schema, style, glossary, DoR, this handbook (U-48 docs part) | Now | In bundle PR (Linear: Backlog) | AA-887 | 0 | Agent |
| AA-888 | Docs lint + ADR indexes in every repo, freshness report | Now | In progress | AA-888 | 0 | Agent |
| U-09 | Stale docs and agent-instruction drift; CIS `docs/` tracked after scan | Now | In progress | AA-889 | 0 | Agent |
| U-11 | Squash-only, delete branch on merge, branch cleanup, PR template and title lint, Infra `.bak` cleanup, remove `/v1/webhooks` from the Playground (U-48 PR template part) | Now | In progress (Infra PR template and `.bak` cleanup done, Infra #211) | AA-890 | 0 | Agent + Nghiệp (settings) |
| AA-892 | Operations index, rollback runbooks, playbooks, flag and job registers, break-glass, isolation probe | Now | Drafts in bundle PR (Linear: Backlog); runbooks to be run on Dev | AA-892 | 0 | Agent |
| AA-893 | Alarm runbook links (step 1), then generated inventory, network and IAM tables (U-49 runbook part); core Terraform outputs (VPC, RDS, ECS, ALB, SG) first, so generated tables have sources | Now | In progress (step 1 live, Infra #213: 57 of 65 alarms) | AA-893 | 0 | Agent |
| AA-895 | Security baseline, vulnerability policy, Dependabot for Booking and TripPlanner | Now | In progress | AA-895 | 0 | Agent |
| AA-896 | FinOps page, Cost Anomaly Detection, monthly report tool | Now | In progress (anomaly detection live, Infra #213) | AA-896 | 0 | Agent |
| AA-897 | Onboarding, agent index, role guides (bilingual per N-7), add-a-new-app playbook | Now | Drafts in bundle PR (Linear: Backlog) | AA-897 | 0 | Agent |
| U-26 | Secrets register, orphan cleanup, read-only E2E account, first access review | Now | In progress | AA-878 | 0 | Agent + Nghiệp |
| U-04 | Agent permission narrowing (committed ask/deny, e2e secret allowlist), folded per N-12 | Now | Open | AA-878 | 0 | Agent + Nghiệp |
| AA-891 | release-please, CHANGELOG, first tags (U-47 light part); CIS `/health` SHA already shipped with AA-884 | Now | Open (needs the AA-901 token) | AA-891 | 0 | Agent |
| U-25 | GitHub App identity for agents and release-please; root ADRs [0011](adr/0011-github-app-identity-and-merge-rights.md) (identity, merge rights) and [0014](adr/0014-repo-visibility-and-github-plan.md) (visibility, GitHub plan), both Proposed (S247); CODEOWNERS files in all five repos; code-owner review for prod | Now (App) / Prod (gates) | Open | AA-901 | 0 | Agent + Nghiệp |
| U-44 | OpenAPI export + oasdiff for CIS and Booking (pulled early); ADR 0013 before `/booking/v1` | Now | Open | AA-899 | 0 | Agent |
| AA-894 | Generated env-config register (names only) + ERD | Now | Open | AA-894 | 0 | Agent |
| — | Cost per app page and ops overview for Ms. Thư | Now | Deployed (CIS #838, #840; live SHA `dba9b72`); Done after the `aa-ship` verify | AA-884, AA-858 | ~0.30 max | Agent |
| — | `Environment` cost allocation tag activated by the payer | Now | Open | — | 0 | Nghiệp |
| — | Nghiệp edits `~/.claude/CLAUDE.md` by hand: release-PR exception to `Refs`, merge rule by phase (N-6); drop `handoff.md`, stop-ECS reminders, task-def/CI numbers in repo CLAUDE.md, `ADR-2026-0xx` numbering (S243 N4) | Now | Open | — | 0 | Nghiệp |
| U-10 | Read-only checks: (a) real PII on Dev (no, D-01) and (b) commercial data in root (root made private, D-25) done; (c) management-account trust and written policy from the payer open | Now | (a)(b) Done, (c) Open | — | 0 | Nghiệp |
| — | First monthly cost and capacity review (October) | Now (≥ 01/11) | Open | AA-896, AA-838 | 0 | Agent + Nghiệp |
| U-12 | Tenant pool fail-closed (global since D-12) and waves 3-4 | Tenant | In progress | AA-859 | 0 | Agent |
| U-16 | Isolation probe on schedule and after apply; per-PR run when RLS changes | Tenant | Scheduled + after-apply probe live (Infra `db-isolation-probe.yml`, X1 S2); per-PR run when RLS changes open | AA-852 (probe); per-PR part with AA-848 | 0 | Agent |
| U-20 | Restore: PITR drill done; private CNAME DSN, single-schema rehearsal, laptop dumps | Tenant | Open (Linear: Backlog); PITR drill done S241 (D-10) | AA-829 | <1 per drill | Agent + Nghiệp |
| U-14 | SSRF-safe outbound HTTP client | Tenant | Open | AA-875 | 0 | Agent |
| U-15 | X2 catalogue CI guard (RLS, PUBLIC, cross-owner FKs, grants) | Tenant | Open | AA-848 | 0 | Agent |
| U-24 | `pii:` tags on Booking and TripPlanner columns | Tenant | Open | AA-877 | 0 | Agent |
| U-60 | TripPlanner job table + outbox PII redaction | Tenant | Open | AA-861 | ~0 | Agent |
| U-13 | Redis AUTH/TLS/at-rest + flag read-failure alarm | Tenant | Open (quote first) | AA-874 | ~0 | Agent + Nghiệp |
| U-19 | API edge: login rate limit, WAF and throttles, docs gate, CORS, headers | Tenant | Open | AA-876 | ~0-2 | Agent + Nghiệp |
| U-23 | Legal pack proposal for Ms. Thư, `/privacy`, `/terms`, AI clause | Tenant | Open | AA-886, AA-820 | 0 | Agent + Ms. Thư |
| U-27 | Staff RBAC + Cognito Phase 1 cutover | Tenant | In progress | AA-816, AA-703 | 0 | Agent + Nghiệp |
| U-33 | X1 role split chain (owner roles, `db_migrator`, CIS runtime role) | Tenant | In progress (S1-S16 live) | AA-852, AA-860 | 0 | Agent |
| AA-898 | `/admin/docs` reader page (allowlist, owner-only security pages) | Tenant | Open | AA-898 | ~0.01 | Agent |
| U-28 | CI gate parity, TripPlanner Lambda deploy after CI, TripPlanner migration replay | Tenant | Open | AA-879; migration replay AA-849 | 0 | Agent |
| U-61 | TripPlanner `idle_session_timeout` + CI connection-budget check, folded per N-12 | Tenant | Open | AA-879 | 0 | Agent |
| U-29 | Golden set of about 100 samples, eval by hand or dispatch (D-23) | Tenant | Open | AA-729 | ≤ 1 per run | Agent |
| AA-900 | Prompt register, eval runbook, generated route table (to be narrowed per N-4, N-5; Linear scope not yet updated) | Tenant | Open | AA-900 | 0 | Agent |
| U-30 | JSON logs with request ids; Sentry for Booking and TripPlanner | Tenant | Open | AA-871 | 0 | Agent |
| U-31 | GuardDuty (limited), Access Analyzer, S3 BPA, CloudTrail hardening | Tenant | Open (quote first) | AA-873 | ~4-16 | Agent + Nghiệp |
| U-34 | ADR 0009 AI platform, ledger v2 with `prompt_version`, AI Use Register | Tenant | Open | AA-804 | 0 | Agent + Nghiệp |
| U-35 | Contract hash guard + new-app playbook tooling | Tenant | Open | AA-826 | 0 | Agent |
| U-36 | TripPlanner off CIS tables | Tenant | Open | AA-712 | 0 | Agent |
| U-37 | Dead Table Registry + legacy job table archive | Tenant | Open | AA-850 | 0 | Agent |
| U-38 | Recurring reviews in the session ritual (capacity monthly, access quarterly); weekly `pg_stat_statements` check (C4.3); quarterly agent-permission review | Tenant | Open | AA-838 | 0 | Agent + Nghiệp |
| U-39 | `shared.countries` and catalog country view | Tenant | Open | AA-851 | 0 | Agent |
| U-32 | Erasure script and DSAR export | Tenant | Not doing now (D-11): manual runbook on request | AA-839 | 0 | Agent |
| — | Manual data-subject request runbook (delete/export on request, DRY RUN), catalog OPS-09 | Tenant | Open | AA-839 (runbook part, does not wait for Phase 4) | 0 | Agent |
| — | Not numbered in S241 (Nghiệp may fold in): A14 body-size limits + `extra='forbid'` → U-19; E13 free S3 gateway endpoint on Dev → U-40 for the prod part | Tenant | Open (undecided) | AA-876 | 0 | Agent + Nghiệp |
| U-40 | Prod blueprint, ADR 0012 (account, layout, gate, env rename), SLOs, second alert channel, prod budget, break-glass PDF, readiness checklist | Prod | Trigger: go-live date | AA-880 | ~150-300 | Agent + Nghiệp |
| U-03 | Rotate the exposed GitHub token | Prod | Not doing now (D-02): at go-live | AA-880 | 0 | Nghiệp |
| U-17 | Rotate the RDS master password | Prod | Not doing now (D-03): at go-live | AA-880 | 0 | Nghiệp |
| U-41 | Managed master secret | Prod | Trigger: X1 done (D-04) | — | ~0.4 | Agent + Nghiệp |
| U-42 | Terraform flow: plan comment, plan-bound apply, drift check | Prod | Trigger: before prod or next drift | AA-846 (clean plan, version pin, apply guard); `.bak` cleanup done in AA-890 | 0 | Agent |
| U-43 | Build once by digest, SBOM on release, provenance, pinned actions | Prod | Trigger: first prod | — | 0 | Agent |
| U-47 | GitHub Deployments, DORA numbers (rest of U-47) | Prod | Trigger: first prod | AA-891 | 0 | Agent |
| U-49 | SLOs and burn-rate alarms | Prod | Trigger: first prod | AA-880 | ~0-3 | Agent |
| U-54 | `rollback.yml`, Lambda alias `live` | Prod | Trigger: first prod | AA-703 | 0 | Agent |
| U-51 | ECS exec becomes break-glass (D-07 B) | Prod | Trigger: prod | — | 0 | Agent + Nghiệp |
| — | Vercel Pro | Prod | Trigger: first paying tenant (D-18) | — | ~20 + usage | Nghiệp |
| U-44 (rest) | ADR 0013 HTTP conventions, `/booking/v1` prefix | Trigger | Trigger: first tenant integrating by API (N-11) | AA-899 | 0 | Agent + Nghiệp |
| U-45 | Public API keys | Trigger | Trigger: API package sold | AA-813 | ~0 | Agent |
| U-46 | Idempotency-Key on paid POSTs | Trigger | Trigger: payments switched on | AA-682 | 0 | Agent |
| U-48 | Org `.github`, reusable workflows, issue templates, SECURITY.md | Trigger | Trigger: second contributor | — | 0 | Agent |
| U-50 | Migration copy bot, required schema version check | Trigger | Trigger: next "app before migration" incident | AA-826 | 0 | Agent |
| U-52 | Third-party pentest | Trigger | Trigger: first enterprise deal | — | one-off quote | Ms. Thư + Nghiệp |
| U-53 | No static keys on the laptop, agent role, devcontainer | Trigger | Trigger: D-15 reopened | — | 0 | Nghiệp |
| U-55 | AI-agent commit trailer, tracing option B | Trigger | Trigger: slow unexplained jobs (D-21) | AA-842 | 0 | Agent |
| U-56 | PostgreSQL 15 major-upgrade rehearsal | Trigger | Trigger: 05/2027 | AA-881 | <1 | Agent |
| U-57 | Rest of L3 (traveller data, retention rows, erasure) | Trigger | Trigger: ADR 0006 Phase 4 / before prod | AA-839 | 0 | Agent |
| U-58 | Tenant CRM through the new-app playbook | Trigger | Trigger: AA-821 approved | AA-821 | — | Agent + Ms. Thư |
| U-59 | Reserved concurrency for TripPlanner Lambdas | Trigger | Trigger: Lambda quota 1000 | — | 0 | Agent |
| — | Architecture diagrams C4 L1-L2, network page, access matrix | Later | Parked (N-9 kept); tables come from AA-893 | AA-697 | 0 | Agent |
| — | UAT videos for all apps | Later | After the technical work, on Nghiệp's signal | AA-855 | 0 | Agent + Ms. Thư |
| — | Monthly DORA numbers from the GitHub API; unit-cost dashboard | Later | Open | — | 0 | Agent |
| — | Yearly Well-Architected self-review per app (with the Generative AI lens); NIST SSDF, NIST AI RMF, OWASP LLM Top 10 as reading checklists | Later | Open | — | 0 | Nghiệp |
| — | Docs site (stage 3), Vale style lint (warn), `terraform-docs`, `AGENTS.md` for other agents; public partner (B2B) docs as a separate site; orphan-page check; Structurizr C4 | Later | Trigger-based ([§4.3](#43-where-docs-live)) | — | 0-1 | Agent |
| — | OpenTelemetry tracing | Later | Trigger: D-21 | AA-842 | 0 | Agent |

Mapping of the S243 guide's own list (so nothing is built twice): N1 CIS `/health` SHA → shipped with AA-884;
N2 release-please → AA-891; N3 PR template and title lint → AA-890; N4 agent-instruction drift → AA-889; N5 CIS
`docs/` ignore → AA-889; N6 ops index and rollback → AA-892; N7 anomaly detection → AA-896; N8 branch settings →
AA-890; N9 ADR indexes → AA-888; N10 glossary and DoR → AA-887; N11 Infra cleanup → AA-890. P1 → AA-880; P2 →
AA-899; P3 → AA-900 + AA-729 + AA-804; P4 → AA-871; P5 → AA-879 + AA-703; P6 → AA-879; P7 → AA-878, AA-873,
AA-874, AA-876, AA-880; P8 → AA-901; P9 → AA-829 + AA-880; P10 → AA-893 + AA-880; P11 → AA-871 + AA-884; P12 →
payer tag activation, AA-880, AA-891.

### 9.3 Do not do now

Each item is deliberate, with its reason. Reopening one needs a new decision in [§10](#10-decisions-log).

| Do not | Why / until |
|---|---|
| A permanent staging environment, multi-region, active-active | Dev + previews + promoting the same image are enough until prod with large customers |
| A separate AWS account for prod | ADR 0001, C7.2a, D-17; compensating controls go in ADR 0012 |
| Rename the GitHub `prod` environment now | ADR 0012 (D-16, C7.2d) |
| GitHub Team or Enterprise, GHAS for private repos, making Infra public | D-14: Free plan, app repos public, root and Infra private; gitleaks and `main`-only OIDC instead |
| Vercel Pro before the first paying tenant | D-18 |
| A human approval on every PR during the dev phase | DM-11.5 / D-13 |
| A least-privilege agent role switch before prod | D-15, N-8 (trigger item U-53) |
| Security Hub and AWS Config before prod | Cost and noise; with prod (C7.2) |
| pgaudit on Dev | D-08; prod only |
| A 90-day secret rotation on Dev | D-02, D-03, DM-8.9 |
| Quarterly restore drills on Dev | DM-9.3, N-2 |
| A per-PR eval trigger, or an eval over the whole catalog | D-23, N-4, DM-10.6 |
| A `shared.feature_flag` table or a paid flag service | DM-1.5; the register is a document |
| A new `Env` tag or a new script calling Cost Explorer | DM-10.1, DM-10.4 |
| The managed master secret before X1 | C2.3b, DM-8.9, D-04 |
| Canary, blue/green, CodeDeploy for ECS | Circuit breaker + alarms + task-definition rollback suffice |
| A Pact broker | oasdiff + JSON Schema contracts suffice |
| A docs site, MkDocs, Backstage, versioned docs, i18n site, a docs portal | Git + catalog now; `/admin/docs` next; site only on trigger |
| Auto-generated backlog | D-22: updated by hand at session end |
| Tracing before a slow unexplained job | D-21 |
| Kubernetes, a service mesh, a self-hosted developer portal | Out of scale |
| SOC 2 / ISO 27001 / ISO 42001 audits, SLSA L3, full OWASP SAMM, Scrum ceremonies, a CAB, a paging rota, a formal error-budget policy on Dev | Prepare evidence only (PR records, registers, postmortems) |
| A hard lockout by username on login rate limits | Lets an attacker lock staff out |
| Paid DORA/flag platforms (e.g. LaunchDarkly), full arc42, docs analytics or feedback widgets, Vale as a blocking check, multi-person CODEOWNERS, an internal API playground | Overkill for one engineer + agents (S243 guide §7, pro-practices §7.2) |

### 9.4 Rule proposals not in data standards v1.1

S241 roadmap §5 proposed further rules that v1.1 (N-1) did not take. They are not rules. Each is raised again only
with the roadmap item that needs it, in that item's PR: SEC-13 Redis AUTH/TLS (U-13), TST-8 two-tenant and
admin-route tests (U-12, U-27), TST-4 probe in CI (U-16), CON-9 HTTP contract (U-44, ADR 0013), CON-10
Idempotency-Key (U-46), DM-6.4 Sentry as an application log (U-30), DM-6.11 DSAR export (U-32, D-11), DM-6.12
sub-processor list from `pii:` tags (U-23, U-24), DM-8.8 exec logging (U-22, done; text only), DM-8.11 secrets
register (U-26), DM-8.12 per-app SGs (U-18, done; text only), DM-10.7 an "approved" row per new spend (D-19),
DM-11.6 `main`-only OIDC (U-01, done; text only), C2.3i stage throttles (U-19), C6.3c fail-closed deploy guard (U-08,
done; text only), C4.1/C4.1a alarm rows (U-07), C7.1 table rows (U-09), C7.2c/d/g/h and C1.3 (U-40, ADR 0012).
Dropped by decision: DM-8.7 profile change (D-15, N-8), DM-8.9 periodic rotation (D-03), DM-9.3 quarterly Dev
drills (N-2).

---

## 10. Decisions log

> **Tóm tắt (VI):** Mọi quyết định của Nghiệp liên quan quy trình nền tảng, mỗi dòng một quyết định kèm nơi nó được thực
> thi. D-01…D-25 là của S241 (17/10), N-1…N-12 là của S243 (19/10). Muốn đổi một quyết định thì ghi dòng mới, sửa nơi thực
> thi trong cùng PR.

Sources: [`sessions/2026-10-17-S241-decisions.md`](sessions/2026-10-17-S241-decisions.md) for D-xx and Q-xx, and the
S243 session record for N-x. Where a decision changed a standard, the standard is the enforcing text.

### 10.1 S241 (17/10/2026)

| # | Decision | Enforced in |
|---|---|---|
| D-01 | Dev holds no real PII (exact counts: 8 Booking and 6 TripPlanner customers, all test or internal) | This page §6.1; Part C C7.1a; every guide says "test data only" |
| D-02 | Rotate the exposed GitHub token at go-live, not now | AA-880 checklist; [§7.5](#75-secrets) |
| D-03 | Rotate the RDS master password at go-live, no periodic rotation on Dev | DM-8.9; AA-880; [secret rotation runbook](ops/runbooks/secret-rotation.md) |
| D-04 | Managed master password after X1 | U-41 trigger |
| D-05 | X1 role split now | AA-852, AA-860; [X1 plan](audits/2026-10-17-S241-x1/x1-plan.md) |
| D-06 | Per-app security groups in the X1 wave | [ADR 0004b](adr/0004b-per-app-security-groups.md) |
| D-07 | ECS exec stays the standard path, with session logging now | DM-8.8; Infra cluster logging; [ECS exec runbook](ops/runbooks/ecs-exec-s3-mediated.md) |
| D-08 | `log_connections` now, pgaudit at prod | RDS parameter group; AA-880 |
| D-09 | Security/audit logs 365 days, app logs 30 days | DM-7 retention table; C4.2b (v1.1); AA-872 |
| D-10 | Restore drill now; result: passed in about 22 minutes | [Drill evidence](audits/2026-10-17-S241-restore-drill/); DM-9.3 |
| D-11 | No erasure/export feature yet; manual runbook on request; button after Cognito customer sign-in | AA-839 |
| D-12 | Tenant pool fails closed globally; per-route rollback kept | C2.3g, DM-8.4, SEC-10 (v1.1); [flag register](ops/feature-flags.md) |
| D-13 | Merge rights by risk and phase: dev phase agent self-merges incl. security/infra; human gate from prod or first paying tenant | DM-11.5 (v1.1); `.claude/CLAUDE.md`; `session-workflow.md`; subagent hook |
| D-14 | App repos public, root private, GitHub Free | [STYLE, where a page may live](STYLE.md#where-a-page-may-live-sec-06); [ADR 0014](adr/0014-repo-visibility-and-github-plan.md); U-25 |
| D-15 | Agent keeps the `aa365-admin` profile | DM-8.7; [§7.6](#76-access) |
| D-16 | Prod layout and gate chosen with the go-live date | ADR 0012 (AA-880) |
| D-17 | Prod on acc2 by default | ADR 0001; C7.2a; AA-880 |
| D-18 | Vercel Hobby until the first paying tenant, then Pro | [§6.1](#61-environments); note for Ms. Thư |
| D-19 | New AWS spend approved item by item, quoted first | PR template cost section; [FinOps](ops/finops.md); DM-10.7 holds only the approval rule ("spend changes need Nghiệp's approval") |
| D-20 | Alarm e-mails on ALARM and OK | Infra alarms (`ok_actions`); AA-872 |
| D-21 | Tracing only when a job is slow and unexplained | AA-842 |
| D-22 | Backlog updated by hand at session end | `session-workflow.md`; [live backlog](backlog/README.md) |
| D-23 | Measure quality through audit rounds; build a golden set of about 100 samples from existing data | AA-729; [§5.7](#57-llm-prompts-and-models) |
| D-24 | Walk Linear issues with Nghiệp before creating them; avoid the full CIS Core project | `aa-linear-issue` skill; S241 issues went to Data Platform, CIS Portal and TripPlanner & AA-Booking |
| D-25 | Security reports and commercial data only in the private root repo | STYLE SEC-06; AA-889 scan before tracking CIS docs |

Related S241 answers: Q1 one admin console with two areas and links to every app; Q2 only owners (Nghiệp + one
emergency account) change other people's rights; Q3 a grant table (person, app, role); Q4/Q5 Booking staff and
content roles through Cognito groups; Q6 no staff-creation UI before Cognito; Q7 three admin plan issues merged; Q8
split the tenant portal now (AA-885, done); Q9 ops overview by the agent, then shown to Ms. Thư (AA-858); Q10 finish
the platform block (admin, X1, Cognito, portal split) before returning to CIS content. Dev phase: the agent codes,
pushes, merges, verifies and reports, security and infrastructure PRs included.

S241 also approved the Cognito Phase 0 cost (14 alarms, 2 metrics, break-glass secret, ~2.4 USD/month; WAF ~7 USD
when customer sign-up opens) and the customer login methods (AA-680); D-18 adds: revisit Amplify only if Vercel
passes ~50 USD/month.

### 10.2 S243 (19/10/2026)

| # | Decision | Enforced in |
|---|---|---|
| S243 | Accept the whole docs handbook and roadmap; do it all, zero-cost items first; Ms. Thư's guide bilingual; add role guides (new engineer, DevOps, CTO, CIO, PM) | This page; [catalog](README.md); [`guides/`](guides/) |
| N-1 | Data standards v1.1 approved (DM-11.5, C2.3g + DM-8.4 + SEC-10, DM-7 rows + C4.2b, DM-11.2, DM-1.2) | [Data standards changelog](architecture/data-standards/README.md#changing-this-standard) |
| N-2 | Default kept: no quarterly drills on Dev | DM-9.3; [§7.4](#74-backups-and-disaster-recovery) |
| N-3 | Security and audit pages on `/admin/docs` are visible to the `owner` role only | AA-898 backend role check; [§4.3](#43-where-docs-live) |
| N-4 | Default kept: no per-PR eval trigger; evals by hand | AA-900; D-23 |
| N-5 | Default kept: `prompt_version` ships with the AA-804 ledger v2 | AA-804; AA-900 |
| N-6 | Create the U-25 issue: AA-901 (GitHub App, two root ADRs, CODEOWNERS; the ADRs became [0011](adr/0011-github-app-identity-and-merge-rights.md) and [0014](adr/0014-repo-visibility-and-github-plan.md) because 0010 went to AA-Partner); Nghiệp edits his global rules by hand (release-PR exception to `Refs`, merge rule) | AA-901; AA-891 |
| N-7 | Language convention: Ms. Thư's guide and the role guides bilingual EN-VI; advisory audits for Nghiệp may be Vietnamese | [`language-convention.md`](../.kiro/steering/language-convention.md); [§4.8](#48-language) |
| N-8 | Default kept: agent stays on `aa365-admin` | DM-8.7; D-15 |
| N-9 | Default kept: AA-697 stays parked; generated tables come from AA-893 | Backlog §4; AA-893 |
| N-10 | Default kept: drill, access and capacity evidence stays in `docs/audits/` | DM-8.10, C7.2b, C8a |
| N-11 | Default kept: only OpenAPI export + oasdiff now; ADR 0013 before any `/booking/v1` change | AA-899 |
| N-12 | U-04 folded into AA-878, U-61 folded into AA-879 | AA-878, AA-879 |

The same session also decided product and platform items outside this handbook's scope (Booking staff keyed by
Cognito id with a one-time backfill, portal domain and legal page links, orphan secret deletion after checks, the X1
S17 password generation); they are recorded in the S243 session log.

---

## 11. Glossary

> **Tóm tắt (VI):** Bảng thuật ngữ đầy đủ (Anh–Việt) ở `docs/glossary.md`; dưới đây chỉ 15 thuật ngữ quan trọng nhất cho
> quy trình. Thêm thuật ngữ mới vào glossary trong cùng PR dùng nó lần đầu.

Full glossary (EN and VI, by area): [`glossary.md`](glossary.md). The fifteen terms this handbook leans on most:

| Term | Tiếng Việt | Meaning in AA-Ecosys |
|---|---|---|
| ADLC | Vòng đời phát triển có agent | Our name for SDLC + control of AI agents + the LLM feature lifecycle ([§2.1](#21-the-model)) |
| Trunk-based development | Phát triển trên một nhánh chính | Short branches, squash merge to `main` (ADR-2026-023) |
| Definition of Ready (DoR) | Điều kiện sẵn sàng | What an issue needs before an agent builds it ([template](templates/definition-of-ready.md)) |
| Definition of Done (DoD) | Điều kiện hoàn thành | Merged + CI green + rollout COMPLETED + verified live (`aa-ship`) |
| Deploy gate | Cổng chặn deploy | CI step that blocks a backend deploy while the job table has work (DM-11.4) |
| Deploy vs release | Triển khai và phát hành | Code running vs users seeing it; a flag separates them |
| Feature flag | Cờ tính năng | A switch without a deploy; kinds release, ops, security ([register](ops/feature-flags.md)) |
| Expand / contract | Mở rộng / thu hẹp | Change schema or API in steps so old and new run together |
| SemVer | Đánh version ngữ nghĩa | `MAJOR.MINOR.PATCH` by compatibility; we stay on `0.x` until prod |
| release-please | release-please | Bot that opens the release PR with the version bump and CHANGELOG (AA-891) |
| Immutable image tag | Tag image bất biến | `dev-<sha>`, never overwritten, so rollback is exact |
| Runbook / playbook | Sổ tay vận hành / kịch bản xử lý | Exact steps for one task / strategy for one kind of incident |
| Break-glass | Lối khẩn cấp | Emergency access used only when normal access fails, then rotated |
| RPO / RTO | Mất dữ liệu tối đa / thời gian dừng tối đa | Acceptable data loss / downtime; targets in DM-9.6 |
| Cost allocation tag | Tag phân bổ chi phí | `App` and `Environment`, so cost splits by app and environment |

---

## 12. Change history and superseded documents

> **Tóm tắt (VI):** Lịch sử: bản review và lộ trình S241 (17/10) cùng bốn file tư vấn S243 (19/10) đã được gộp vào trang này. Các file
> cũ giữ lại làm lịch sử, có dòng "Superseded" ở đầu; không dùng chúng làm nguồn chuẩn nữa.

### 12.1 Change history

| Date | Session | Change |
|---|---|---|
| 2026-10-17 | S241 | SDLC/ADLC review (six areas) and the unified platform roadmap U-01…U-61 with decisions D-01…D-25 |
| 2026-10-19 | S243 | SDLC/docs/versioning guide, docs standard proposal, professional docs practice, and the reconciliation with S241 and data standards (conflicts K-xx, corrections, decisions N-1…N-12) |
| 2026-10-19 | S243 | This handbook: one page for process, docs, versioning, releases, operations, cost, roadmap and decisions; every reconciliation correction applied; six documents marked superseded: the S241 review and roadmap and the four S243 advisory files (AA-887) |

### 12.2 Superseded documents

Kept for history and evidence. Do not cite them as current rules; cite this page or the canonical source it links.

| Document | Superseded by |
|---|---|
| [`audits/2026-10-17-S241-sdlc-review/README.md`](audits/2026-10-17-S241-sdlc-review/README.md) (S241 SDLC/ADLC review) | This page; evidence per area stays in [`areas/`](audits/2026-10-17-S241-sdlc-review/areas/) |
| [`audits/2026-10-17-S241-sdlc-review/unified-roadmap.md`](audits/2026-10-17-S241-sdlc-review/unified-roadmap.md) (U-01…U-61, D-01…D-25) | [§9](#9-roadmap) and [§10](#10-decisions-log) |
| [`audits/2026-10-19-S243-sdlc-docs-versioning/README.md`](audits/2026-10-19-S243-sdlc-docs-versioning/README.md) (SDLC/ADLC guide, glossary) | [§2](#2-operating-model)-[§8](#8-cost-finops), [glossary](glossary.md) |
| [`audits/2026-10-19-S243-sdlc-docs-versioning/docs-standard-proposal.md`](audits/2026-10-19-S243-sdlc-docs-versioning/docs-standard-proposal.md) (catalog, standards, hosting, issues) | [§4](#4-documentation-system), the [catalog](README.md), [STYLE](STYLE.md) |
| [`audits/2026-10-19-S243-sdlc-docs-versioning/docs-pro-practices.md`](audits/2026-10-19-S243-sdlc-docs-versioning/docs-pro-practices.md) (professional docs practice) | [§4](#4-documentation-system), [STYLE](STYLE.md), [templates](templates/) |
| [`audits/2026-10-19-S243-sdlc-docs-versioning/reconciliation-s241-standards.md`](audits/2026-10-19-S243-sdlc-docs-versioning/reconciliation-s241-standards.md) (K-xx, corrections, N-1…N-12) | Corrections applied throughout this page; decisions in [§10.2](#102-s243-19102026) |

Not superseded: the S241 area reports (evidence), the restore drill and X1 folders, and
[`sessions/2026-10-17-S241-decisions.md`](sessions/2026-10-17-S241-decisions.md) (the decision record itself).
