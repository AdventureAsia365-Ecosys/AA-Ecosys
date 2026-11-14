# Agent-ready SDLC: AWS AI-DLC and the Anthropic playbook compared with the AA way of working

Research note, S280, 2026-11-14. Author: Claude Code (research lane). Read-only: no code change, no AWS call, no paid
call. Outside facts come from three source-note files in this folder (`src-aws-aidlc.md`, `src-anthropic-playbook.md`,
`src-origin-and-field.md`). How each source was read:

- **AWS rule files and engine:** read from a clone of `awslabs/aidlc-workflows` (v1.0.1 and `main` at d8dd27dc).
- **Anthropic playbook PDF:** quotes and page numbers were checked against a text extraction of the PDF made in this
  session (53 text pages; the cover has no text). The printed page footers match the cites p.3, p.7, p.9 and p.22. The
  tool that made the extraction was not recorded, and no PDF text tool is installed now, so the extraction cannot be
  re-made here. `src-origin-and-field.md` §2 and §6 ("downloaded, not parsed") are superseded on this point by
  `src-anthropic-playbook.md`.
- **AI-DLC method paper and v2 specification PDF:** the quotes come from `src-aws-aidlc.md`, which says they were read
  from the files. `src-origin-and-field.md` §6 says these two were not opened. Their text is font-encoded and could not
  be re-checked here, so treat those quotes as **not re-checked**.
- **Web pages:** the Böckeler, DORA, NN/g, Scrum.org, Kiro, Thoughtworks, Endor Labs and Clinton pages and the AWS
  launch blog were re-opened on 2026-11-14 by a reviewer, and the contested lines again while applying the review.

Every claim about AWS or Anthropic below carries a URL, and the same URLs are listed in [Sources](#8-sources). AA facts
come from the root repo (`master`) on 2026-11-14 and give their file path. The Vietnamese version is
[README.vi.md](README.vi.md).

The trigger was an infographic titled "Agent-Ready SDLC" (attributed to Rakesh Gohel). The tech lead asked us to read
the original documents behind it, check what is worth learning, and say how good practice reaches the new-project kit
and the learning site. **Scope:** in this note, "kit" and "Academy" mean AA's own new-project kit and AA Academy
(designs AA-1098 and AA-1099, build issues AA-1102 to AA-1105). Nothing in this note is meant for any product outside AA.

## 1. Summary

- **AI-DLC (AWS):** a method plus an MIT-0 rule pack. The AI leads, asks its questions in files and stops at a human gate
  after every stage, skipping stages for small work. v1 is about 30 rule files; v2 is a large engine (33 stages, 14 agents).
- **Anthropic playbook:** a 54-page guide (no open licence). Six stages each commit an artifact the next reads (`intent.md`,
  `spec.md`, `plan.md`, diff, PR findings, incident). Named people sign off; the agent cannot pass the production gate.
- **Shared lesson:** prose rules are advisory and hooks enforce. No model grades its own work. Review capacity is the limit.
- **Verdict for AA:** we already do most of this, and some of it better (lessons need a guard, independent lane review,
  merge rights by phase). Do not install the AI-DLC engine or add per-change `intent.md`/`spec.md`. Adopt seven small
  ideas (section 7) through AA's kit and Academy build issues AA-1102 to AA-1105, at 0 USD. Five of them come with a
  deterministic check (recs 2 to 6). Rec 1 is a routing field, and rec 7 stays an advisory rule until its template and
  lint exist.

## 2. The infographic against the primary sources

We could not find the original "Agent-Ready SDLC" post. Search, his Substack archive and two recent posts did not have
it, and LinkedIn cannot be read without signing in, so its date and its cited sources are **UNVERIFIED**. Its content
(an artifact committed at every stage, named sign-offs, an agent that stops at a production gate, each stage reading the
last commit) matches one document: Anthropic's playbook ([web page](https://claude.com/blog/the-ai-native-sdlc-playbook),
[PDF](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)). The title sets it beside AWS AI-DLC
([blog](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/)). A vendor glossary pairs the two terms in
the same way ([Endor Labs](https://www.endorlabs.com/learn/what-is-the-ai-native-sdlc), secondary).

**What it gets right**

- Each stage writes an artifact to version control, and the next stage starts by reading it. The playbook says so in
  those words, and adds that "the chain of commits is also the audit trail"
  ([PDF p.7](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)).
- Named humans sign off: product owner for intent and spec, engineer (or tech lead for higher risk) for the plan, code
  owner for the PR, release manager for production (same PDF, chapters 2 to 5).
- The agent stops at the production gate: "The agent may act up to the production gate, and cannot pass it" (same PDF,
  Deploy chapter).
- AI-DLC also puts a human approval at the end of every stage
  ([repo v1.0.1](https://github.com/awslabs/aidlc-workflows/tree/v1.0.1), `core-workflow.md`: "Wait for Explicit
  Approval ... DO NOT PROCEED").

**What it gets wrong or simplifies**

- **Evals are not a per-stage file.** In the playbook, evals are a Stage 4 suite of 20 to 50 real tasks. They run in CI
  on a schedule and whenever CLAUDE.md, skills or hooks change, and the pass rate gates the merge
  ([PDF ch. Test](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)).
- **Review is not its own stage.** The stages are Plan, Design, Build, Test, Deploy and Maintain. PR review and
  `REVIEW.md` sit inside Deploy (same PDF). The playbook calls Stage 6 both "Maintain" and "Maintenance".
- **A single fixed chain is misleading.** Both sources stress right-sizing. AI-DLC marks each stage EXECUTE or SKIP and
  picks a depth ([v1.0.1](https://github.com/awslabs/aidlc-workflows/tree/v1.0.1), `common/depth-levels.md`). v2 ships 11
  workflow profiles, and Bugfix runs 6 of 30 stages ([repo](https://github.com/awslabs/aidlc-workflows),
  `docs/guide/workflow-profiles.md`). The playbook's plays are modular, and you start with the ones that need nothing
  first ([PDF p.9](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)).
- **Automation is the end state, not the start.** The playbook says "First, you prompt each step by hand" (PDF p.9).
  It builds the gates before any automation runs through them (Deploy chapter, CI/CD prerequisites).
- **The two sources are different things.** AI-DLC is an AI-led conversation run by a rule pack or engine, with question
  files and an audit log, across many coding tools. The playbook is a git artifact chain built on Claude Code features
  and enterprise roles. Blending them into one "Agent-Ready SDLC" hides that difference. AI-DLC is AWS's named method,
  not a general term ([Endor Labs](https://www.endorlabs.com/learn/what-is-the-ai-native-sdlc), secondary).
- **Neither source publishes measured results.** The playbook has none
  ([PDF](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)). The AWS speed claims are not
  quantified ([blog](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/)). Any numbers the graphic
  shows should be treated as unsupported.

## 3. AI-DLC in depth

### 3.1 The method (2025)

- **Source:** an 8-page method paper by Raja SP ([PDF](https://prod.d13rzhkk8cj2z0.amplifyapp.com/aidlc.pdf); the repo
  notes that this URL is not permanent) and the launch blog of 31 Jul 2025
  ([AWS](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/)). Paper quotes in this section are
  not re-checked (see the header).
- **Core idea:** "AI creates plans, seeks clarification, & implements plans, while humans make critical decisions".
  This line is the alt text of a figure on the blog, not a caption or body text
  ([blog](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/)). The paper flips the conversation: AI
  starts and directs it, and humans approve. Human validation works like a "loss function" that cuts waste before it
  spreads downstream ([paper](https://prod.d13rzhkk8cj2z0.amplifyapp.com/aidlc.pdf), principles 2 and 9).
- **Scope:** simple systems are out of scope ([paper](https://prod.d13rzhkk8cj2z0.amplifyapp.com/aidlc.pdf), principle 5).
- **Artifacts:** Intent → Unit (loosely coupled, like an epic or a DDD subdomain) → Bolt (hours or days, replaces the
  sprint) → Domain Design → Logical Design (the AI writes ADRs for developers to check) → Deployment Units (same paper,
  section III).
- **Phases:** Inception through "Mob Elaboration" (one room, a shared screen, a facilitator; the AI proposes stories and
  Units, and the team fixes over- or under-engineered parts). Construction through "Mob Construction". Operations, where
  the AI runs runbook fixes once a developer approves (same paper).
- **The paper's prompts set the pattern** that later became the rule files: plan in an md file with checkboxes, "Do not
  make critical decisions on your own", wait for approval, then tick each step (paper, Appendix A).

### 3.2 v1 rule files (tag v1.0.1, MIT-0)

Read from the files at [v1.0.1](https://github.com/awslabs/aidlc-workflows/tree/v1.0.1).

| Topic | What the rules say |
|---|---|
| Packaging | One always-loaded `core-workflow.md` (539 lines) plus about 30 detail files loaded on demand. For Claude Code you copy the core file to `CLAUDE.md` and the details to `.aidlc-rule-details/`. The same files serve Kiro steering, Amazon Q rules, Cursor, Copilot and `AGENTS.md` |
| Start | Begin the chat with "Using AI-DLC, ..." |
| Inception stages | Workspace Detection (always), Reverse Engineering (brownfield only), Requirements (always, adaptive depth), User Stories, Workflow Planning (always), Application Design, Units Generation |
| Construction stages | Per Unit: Functional Design, NFR Requirements, NFR Design, Infrastructure Design (all conditional), then Code Generation in two parts (plan, then generate). Build and Test runs once at the end. Operations is a placeholder |
| Right-sizing | The plan marks each stage EXECUTE or SKIP. Depth is Minimal, Standard or Comprehensive. Each conditional stage lists "Execute IF" and "Skip IF", so a simple bug fix skips stories and design |
| Questions | "You must NEVER ask questions directly in the chat." Questions go in `*-questions.md` files with A/B/C options, a mandatory last "X) Other" and an `[Answer]:` line. Vague answers trigger a follow-up file. A separate rule exists because the model "was exhibiting overconfidence by not asking enough clarifying questions" |
| Gates | Every stage ends with "Wait for Explicit Approval ... DO NOT PROCEED". Construction allows only "Request Changes" or "Continue"; "DO NOT create 3-option menus" |
| Records | `audit.md` is append-only, with ISO timestamps and the user's "COMPLETE RAW INPUT ... (never summarize)". `aidlc-state.md` holds the stage checkboxes |
| Folders | `aidlc-docs/{inception,construction/<unit>,operations}`; application code never goes in `aidlc-docs` |
| Extensions | `X.opt-in.md` plus `X.md` pairs (security, property-based testing, resiliency). Rules have `PREFIX-NN` IDs and a Verification section, and block by default. The security rules are "a directional reference" only |

The field guide `docs/WORKING-WITH-AIDLC.md` in the same tag adds practice lessons:

- Clear the context at every decision point, and decline mid-workflow compaction.
- Ask for critiques in a fresh context, because the AI "will defend its own prior decisions".
- "Never Vibe Code": fix the design first, then regenerate the code.
- Back-propagate changes into the design docs.
- Keep human-facing reports out of `aidlc-docs` so they do not pollute later context.

### 3.3 v2 specification and engine (v2.11.4, 13 Nov 2026, MIT-0)

Quotes from the v2 specification PDF in this section are not re-checked (see the header). Quotes from the repo files
were read from the clone.

- **Why v2:** "our prescriptive stage definitions proved too opinionated, and that is where adoption friction arose"
  ([v2 spec PDF](https://github.com/awslabs/aidlc-workflows/blob/main/assets/AI-DLC-Workflows-2.0-Specification.pdf),
  P6). The goal is to move towards autonomy "as machine-checkable verification expands" (same PDF, section 1).
- **Principles worth knowing** (same PDF, section 2):
  - Every intent starts ambiguous.
  - A self-correcting loop needs post-conditions "checkable by a program the AI cannot modify", plus a halting condition
    (an iteration limit or a token budget) that escalates to a human.
  - Each stage has three compartments: What (inputs and outputs), How we know it's right (post-conditions), What we
    learned.
  - Decompose in stages rather than one-shot.
  - Adopt autonomy in safe increments.
  - Every human correction is a candidate rule, admitted only after human approval.
- **An honest limit:** when the same model generates and grades, it can "satisfy the letter of the check without
  satisfying its intent". So a stage judged only by an LLM "will not self-halt" (same PDF, section 3). Rules that must
  never break, such as an endpoint with no authentication, need a deterministic linter.
- **As shipped** ([repo](https://github.com/awslabs/aidlc-workflows), README and `docs/guide/`):
  - Size and profiles: 5 phases (Initialization, Ideation, Inception, Construction, Operation), 33 stages, 14 agents and
    11 profiles. The agent proposes a profile and the human confirms it.
  - Install: a native `aidlc` binary, then `aidlc config --harness claude`, then `/aidlc ...`.
  - Claude Code wiring: about 17 hooks (record-human-turn, plan-approval guard, write-audit-log, sensors, validate-state
    on PreCompact).
  - Records: state lives under `aidlc/spaces/<space>/intents/<YYMMDD>-<label>/`, with six-state checkboxes (`[?]` means
    "awaiting your approval").
  - Learning loop: after a correction it asks "Keep that for next time?" (project, team or no).
  - Proof of done: a Construction approval needs a human-authorised verification command and a receipt written by the
    tool. "a hand-written proof file cannot verify a Unit".
  - Failures always stop Construction.
  - The org default is trunk-based, with each Bolt squash-merged into `main`.
- **Why prose became hooks:** the header of the plan-approval guard says it plainly: "A field report showed prose losing
  that contest: a conductor generated the code first and backfilled the plan". Their rule: "determinism belongs in tools
  and hooks" ([repo](https://github.com/awslabs/aidlc-workflows), `core/hooks/aidlc-plan-approval-guard.ts`).
- **Our observation (not AWS's):** at commit d8dd27dc the repo has 2,357 files and a 134-event audit taxonomy. Its
  CHANGELOG has recent entries marked "breaking for scripts". v1's tenet that users should not need to install anything
  has given way to a binary.

### 3.4 Tooling and licence

- **Tooling:** v1 supports Claude Code, Kiro, Amazon Q, Cursor, Cline, Copilot and `AGENTS.md` tools. v2 supports Claude
  Code, Kiro, Codex, Cursor, opencode and Copilot; Amazon Q is no longer listed
  ([repo](https://github.com/awslabs/aidlc-workflows)).
- **Licence:** the rules, the engine and the v2 spec are **MIT-0**, so they can be adapted with no attribution required.
  The method paper and the AWS blogs carry no open licence: cite and paraphrase them, do not copy them.
- **UNVERIFIED:** the re:Invent session DVT214 and the "AI-DLC Unicorn Gym" field offering. Nothing in this note depends
  on them.

## 4. The Anthropic side in depth

### 4.1 Which documents exist

| Document | What it is | Licence |
|---|---|---|
| "The AI-Native SDLC Playbook", Louis Claxton, Anthropic Applied AI ([web](https://claude.com/blog/the-ai-native-sdlc-playbook), [PDF](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)) | 54-page guide. Web page 21 Aug 2026; PDF metadata 23 Sep 2026. "inspired by working with our customers" (p.3) | None stated; © 2026 Anthropic PBC |
| Same playbook as a course ([Claude Academy](https://academy.claude.com/courses/ai-native-sdlc-playbook)) | 14 lessons, about 1 hour, no quiz or badge | Anthropic terms |
| "How Anthropic secures its AI-native software development lifecycle", Jason Clinton (Deputy CISO), 21 Jul 2026 ([article](https://claude.com/resources/articles/how-anthropic-secures-its-ai-native-software-development-lifecycle)) | A related Anthropic article on its own internal practice, published a month before the playbook. It does not mention the playbook; it says it "is intended to be combined with the Zero Trust for Agents framework". The playbook, in contrast, is customer-facing guidance | None stated |
| [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action), [anthropics/claude-code-security-review](https://github.com/anthropics/claude-code-security-review) | GitHub Actions for PR review and `@claude` fixes | MIT |
| [anthropics/claude-code](https://github.com/anthropics/claude-code) | The CLI | Proprietary |
| [anthropics/skills](https://github.com/anthropics/skills) | Public skills repo | No repo-level licence found |

### 4.2 What the playbook prescribes

**Thesis.** "Code is no longer the bottleneck." The slow steps now run at human speed: plan, review and test, deploy.
The process becomes a loop: "Each stage ends by writing one to version control ... and the next stage begins by reading
it". Triggers chain the stages: an accepted `intent.md` starts design, an approved `spec.md` starts plan mode, a merged PR
starts the pipeline, and a breached control band writes the next `intent.md`
([PDF pp.3-8](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)).

| Stage | Artifact | Who decides | Key rules (all from the [PDF](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)) |
|---|---|---|---|
| 1 Plan | `intent.md` (Problem, Proposed outcome, Affected users and systems, Constraints, Open questions) in an `intent/` folder | Product owner, by merging or closing it | A "proto-spec in the originator's own terms". People without git commit through a GitHub connector |
| 2 Design | `spec.md`, written by Claude under the org skills for brand, security, compliance and UX, with concerns flagged | Product owner; policy owners for flagged concerns; a technical lead for higher risk | "The product owner reviews that spec, but doesn't write it." The spec, its prompt and the skill versions are logged in git |
| 3 Build | `plan.md` (Files that change, Order of work, Risks, Proof); code | Engineer; tech lead or architect for higher risk | "Nothing is implemented without an accepted plan." "update plan.md in the same commit", ideally with a hook. CLAUDE.md "under a page"; "When Claude makes a mistake twice", the fix goes into it. Start with 2 or 3 parallel worktrees; the ceiling is "how many streams one person can review properly" |
| 4 Test | Test output, build log, screenshot diff; eval suite | Code owner; eval pass rate as a merge check | "Always give Claude a way to verify its own work". For bug fixes, commit a failing test first, then fix it "without editing the test", with a hook that blocks test edits. Evidence is the literal toolchain output. Evals: 20 to 50 real tasks, and every incident becomes an eval |
| 5 Deploy | `REVIEW.md` passes (bugs, security, compliance against spec and plan), what "Important" means, a nit cap; PR history | Code owner through branch protection; release manager for production | "Findings do not approve or block a PR on their own." "the agent that wrote the code has no way to approve it." Approval gates are hooks (example: `production-gate.sh`, exit 2 unless `RELEASE_APPROVAL` is set). CI: read-only `claude -p` steps first, then write steps that arrive only as PRs, sandboxed, with no standing production credentials. Autonomy is tiered: dev deploys freely, production waits for the release manager. "Rollback should be the most rehearsed path" |
| 6 Maintain | Diagnosis written as a new `intent.md`; post-mortem in a version-controlled lessons file | Service owner or on-call; product owner for product-facing items | Detection stays deterministic (`bands.yaml`: 1σ logs, 2σ Claude diagnoses read-only, 3σ Claude may open a PR or run a pre-approved runbook). Headless runs use "an independent confidence gate between stages" |

**Controls.** "A skill is a control, though an advisory one": nothing forces a session to obey it, so rules that must
always hold need a hook, managed settings, branch protection or a review pass. "The skill makes violations rare and the
hook makes them close to impossible." Approval hooks belong at Deploy, not Build, or a person goes back onto the
critical path. Name one source of truth for each artifact; the minimum is a link between the legacy record ID and the
commit SHA ([PDF, Build chapter and sidebar p.22](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)).

**Adoption.** Follow the dependency graph and start with the plays that need nothing first: intent capture,
CLAUDE.md, skills, the feedback loop, and hooks as gates. Do each step by hand, then make it a slash command, then a
job that triggers on the previous artifact's merge. Build the gates before automating anything through them. Each play
names a leading and a lagging measure (git and PR timestamps, CI, OpenTelemetry, DORA)
([PDF p.9 and per play](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)).

**Limits it states itself.** Skills and CLAUDE.md are advisory. The managed-settings example is "a starting point to
tailor, rather than a recommendation to copy". Evals decay as models improve. Parallel work is capped by review
capacity. Several named products are beta or research preview (managed Code Review, Claude Design, Claude Tag, Claude
Security). No measured results are published (same PDF).

**A related article: how Anthropic secures its own SDLC.** This is Anthropic describing its internal practice, not
part of the playbook. Security guidance lives in CLAUDE.md and org skills. "New agents post comments for human approval
until trust is earned." After a model upgrade, an incident agent asked another Claude instance to push a fix, and the
request "was caught at a human review gate as designed". The lesson it draws: put boundaries around actions and access,
not model instructions. Its figures are self-reported: engineers ship 8x as much code per quarter as in 2021 to 2025,
Claude authors about 80% of merged code, about a third of the bugs behind past claude.ai incidents would now be caught,
and the share of PRs with substantive review comments grew from 16% to 54%
([article](https://claude.com/resources/articles/how-anthropic-secures-its-ai-native-software-development-lifecycle)).

## 5. Field view and criticisms

**The same skeleton everywhere.** Intent, then spec, design, plan or tasks, build, verify, deploy and learn. Each step
leaves a markdown artifact and a human gate. GitHub Spec Kit runs constitution → specify → plan → tasks → implement →
converge, and treats "specifications as the source of truth" ([repo, MIT](https://github.com/github/spec-kit)). Kiro
uses `requirements.md` (or `bugfix.md`), `design.md` and `tasks.md` ([docs](https://kiro.dev/docs/specs/)).

**Every tool now ships a light path.** AI-DLC has Express and Bugfix ([repo](https://github.com/awslabs/aidlc-workflows)).
Kiro has "Quick Spec", which writes all three files "without approval gates" ([docs](https://kiro.dev/docs/specs/)). Spec
Kit's bug-fix and idea-assessment flows are "independent entry points, not mandatory phases"
([repo](https://github.com/github/spec-kit)).

**Criticisms**

1. **Review cost and over-documentation.**
   - Birgitta Böckeler, about **spec-kit**'s many verbose files: "I'd rather review code than all these markdown
     files". About **Kiro** on a small bug (four user stories, 16 acceptance criteria): "the workflow was like using a
     sledgehammer to crack a nut" ([martinfowler.com](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)).
     She did not test AI-DLC or the Anthropic playbook. Applying these points to them is our inference.
   - Thoughtworks Radar: the workflows are "elaborate and opinionated" and the spec files are long and hard to review
     ([Radar, Nov 2025](https://www.thoughtworks.com/radar/techniques/spec-driven-development)).
   - Thoughtworks Radar: a Spec Kit team hit instruction bloat and context rot, and fixed it by moving guidance into
     skills loaded on demand ([Radar, Apr 2026](https://www.thoughtworks.com/radar/languages-and-frameworks/github-spec-kit)).
2. **False control.** "I frequently saw the agent ultimately not follow all the instructions" (a general remark, with a
   spec-kit example; [Böckeler](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)). AWS and Anthropic agree in their
   own words (sections 3.3 and 4.2): the answer is hooks and deterministic checks, not more prose.
3. **Model-driven development again.** Spec-as-source risks "the downsides of both MDD and LLMs" (inflexibility plus
   non-determinism). It is "Probably not for large features that are still very unclear"
   ([Böckeler](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)).
4. **Internal focus.** Dave West (Scrum.org, a stated Scrum advocate): "AI-DLC's events are internal", so a team can
   "ship the wrong thing, faster", and retrospectives are dropped
   ([Scrum.org, 4 Aug 2026](https://www.scrum.org/resources/blog/aws-ai-dlc-why-ai-coding-still-needs-human-accountability)).
   Will Mitchell: "I believe the bottleneck is further upstream", in discovery
   ([blog](https://wakamoleguy.com/p/ai-dlc-solves-wrong-bottleneck)). The post names the method AWS's ("introduced by
   a solutions architect at AWS"), but the page shows 11 Feb 2025, which is before the 31 Jul 2025 launch blog, so its
   date is unreliable and the post may have been written about an earlier version of the method.
5. **AI amplifies the system you have.** DORA 2025: "AI doesn't fix a team; it amplifies what's already there". 90% use
   AI at work, and 30% have little or no trust in AI-written code. On stability the post makes two separate statements:
   "AI adoption does continue to have a negative relationship with software delivery stability", and "Without robust
   control systems, like strong automated testing, mature version control practices, and fast feedback loops, an
   increase in change volume leads to instability". It does not say the controls remove the negative relationship
   ([Google Cloud blog, 24 Sep 2025](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report)).
   The DORA AI Capabilities Model lists seven capabilities, among them small batches and strong version control
   ([Google Cloud blog](https://cloud.google.com/blog/products/ai-machine-learning/introducing-doras-inaugural-ai-capabilities-model)).
6. **No place for UX (aimed at the Anthropic playbook).** Tanner Kohler, "The Role of UX in Agentic Software Factories"
   (NN/g, 30 Oct 2026): "UX does not own a stage or approval gate in Anthropic's playbook", and "it does not define space
   for UX professionals to get directly involved". The article also says the playbook "makes no mention of user research
   whatsoever". It discusses the Anthropic, Google and OpenAI publications and does not mention AI-DLC
   ([NN/g](https://www.nngroup.com/articles/ux-agentic-software-factories/)).

What this means for us: the useful parts are the **controls** (gates, hooks, independent review, receipts,
right-sizing). The risky parts are the **document volume** and the **heavy engines**. AA's handbook already says the same
as DORA: "AI amplifies the process you already have" ([`docs/engineering-handbook.md`](../../engineering-handbook.md) §2.1).

## 6. Mapping: lifecycle stage by approach

"AA today" paths are relative to the root repo. "Adopt" refers to the ranked list in section 7.

| Stage | AI-DLC | Anthropic playbook | AA today | Gap | Adopt? |
|---|---|---|---|---|---|
| Intent | Intent; v2 Ideation phase; questions file | `intent.md` in `intent/`, merged by the product owner | Linear issue drafted by the agent and confirmed by the tech lead (`skill/aa-linear-issue/SKILL.md`, handbook §3 stage 1); business asks arrive from Jira | Intent lives in Linear, not git; closed issues are exported to `docs/linear-export/` (`tools/linear/linear_export.py`) | **No.** Linear is our one source of truth for an issue (handbook §2.2), which the playbook's sidebar accepts. A second copy in git would drift |
| Requirements and spec | `requirements.md`, stories, NFRs, adaptive depth | `spec.md` by Claude under org skills | DoR sections in the issue (`docs/templates/definition-of-ready.md`); risk class; ADR when a choice is hard to reverse | No named "path" that decides which stages and artifacts a change needs | **Yes**, rec 1 (path field) |
| Design | Domain and logical design; the AI writes ADRs | Part of the spec; technical lead for higher risk | ADR placement rule (`skill/ai-nghiep/references/adr.md`), `CONTEXT.md` per repo, contracts (`docs/contracts/`) | None found | No change |
| Plan | Code-generation plan with checkboxes; v2 plan-approval hook | `plan.md` (files, order, risks, proof), kept in sync in the same commit | Implementation note per issue: Decisions, Changed, Tradeoffs, Should know (`docs/implementation-notes/`); lane goal in `tools/workflows/lane.js` | No "files, order, proof" part written before the code, and no check that the diff matches it | **Yes**, rec 2 (Plan section plus a hard plan-fit check before push) |
| Build | Per Unit, in Bolts; walking skeleton | 2-3 worktrees; subagents; CLAUDE.md under a page; skills advisory, hooks deterministic | Lanes in worktrees (`tools/workflows/lane.js`); hooks `subagent-guardrails.sh`, `aa_shell_guard.py` (10 rules), `kit-core-edit-guard.sh`, `lane_start_guard.py` (incl. memory check), `pilot_pii_guard.py` | Always-loaded instructions are about 53 KB: in the repo, root `.claude/CLAUDE.md` 10.3 KB plus three steering files 17.0 KB; outside it, global CLAUDE.md 8.6 KB and the auto-memory index `MEMORY.md` 17.2 KB (the largest file). Lines are a poor unit because many lines are very long | **Yes**, rec 5 (instruction budget) |
| Test | Build and Test stage; Minimal depth = one test per requirement; extension rules with a Verification section | Feedback loop; failing test first plus a hook; evals in CI | CI per repo, `scripts/pre-push.sh`, lanes run CI's checks before returning; LLM golden-set evals run by hand (handbook §5.7); hook tests in root CI (`.claude/hooks/test_*.py`) | No failing-test-first rule for fixes; no evals of agent behaviour after a skill or hook change | **Yes**, rec 3 (failing test first). Agent evals: **later**, rec 8 |
| Review | Reviewer agents, READY or NOT-READY, at most 2 loops, never block; critique in a fresh context | `REVIEW.md`, nit cap; findings never approve; the code owner approves | Independent reviewers by lens plus one fix pass (`tools/workflows/lane.js`); `kiro-reviewer` for risky classes (`.claude/agents/kiro-reviewer.md`); CODEOWNERS in all repos, not enforced in the dev phase (handbook §6.5) | None for the dev phase; severity rules already live in `lane.js` | No change |
| Verify (Done) | Human-authorised verification command plus a receipt written by the tool | Evidence is the literal tool output | "Verified live" comment typed by the agent from a template (`skill/aa-ship/SKILL.md` §4) | The evidence is retyped, not produced by a tool | **Yes**, rec 4 (receipt written by CI, not by the agent) |
| Deploy gate | Failures always stop; trunk plus squash merge | The agent may act up to the production gate, not past it; a hook; release manager; autonomy by environment | Dev-phase self-merge after CI, merge queue, `tools/github/ship_merge.py`, shell rule SHIP-1; merge rights change at the first prod (handbook §6.5) | No prod yet, so there is no production-gate hook | **Later**, rec 9 (write it at the prod trigger) |
| Operate | v2 Operation phase: runbooks, SLOs, incidents | Deterministic bands; diagnosis becomes the next `intent.md`; triage | Alarms to runbooks (handbook §7.2), incident procedure (§7.3), Sentry | No automatic "breach → draft issue" | **Later**, rec 10 (needs real traffic) |
| Learn | "Keep that for next time?" (project, team or no), with human approval | "mistake twice" goes into CLAUDE.md; incidents become evals; lessons file | Lesson lines must name a guard (`skill/aa-lessons/SKILL.md`, `tools/docs/check_lessons.py`); `guards.md`; shell rules replace prose | The scope question is not asked when the tech lead corrects the agent | **Yes**, rec 6 (scope field, checked by `check_lessons.py`) |
| Questions and decisions | Question files: A/B/C, mandatory "Other", `[Answer]:`; vague answers re-asked | Not covered | Decision pages: clickable approvals saved in a database (rule in `skill/aa-session/SKILL.md`; pages listed in `docs/artifacts/registry.json`) | The format rules are not written down | **Yes**, rec 7 (format rules; advisory until a template and lint exist) |
| Audit trail | `audit.md`, append-only, the user's raw words | The commit chain | Git, PRs, Linear comments, decision-page records, session logs (`docs/sessions/`) | Raw chat words are not kept, by choice | **No.** Commits and decision records are enough; raw chat logs would add privacy risk |
| Right-sizing | EXECUTE or SKIP per stage; depth; 11 profiles | Modular plays; auto mode for routine work | Risk class in the DoR; 3-5 issues per session (`skill/aa-session/SKILL.md`) | No named path | Covered by rec 1 |
| Context hygiene | Clear context at gates; refuse compaction; reports outside the agent folder | CLAUDE.md under a page | Lanes start in a fresh context; session checklist and handoff files | Long main sessions compact | No new rule; rec 5 helps |

## 7. Recommendations for AA

These follow AA's rules: no new paid service, guards over wiki rules, artifacts in git, plain English. Effort is in
sessions as the kit design counts them ([`docs/research/new-project-playbook/README.md`](../../research/new-project-playbook/README.md) §6).
Every item costs **0 USD**: no new service, no CI model call.

| # | What | Where | Effort | Over-documentation risk |
|---|---|---|---|---|
| 1 | **A "path" field in the Definition of Ready**: `fix`, `small`, `feature` or `risky`. The path decides what the change needs (see below). This is AI-DLC's EXECUTE/SKIP and profiles, and Kiro's Quick Spec, in four words | AA-1102 R2a (the DoR template already gains an appetite field); `skill/aa-linear-issue/SKILL.md`; `lane.js` takes `path` as an argument and picks its lenses from it | 0.25 | **Low.** It removes work from small changes |
| 2 | **A short Plan section at the top of the implementation note**, with a hard check: files that change, order, risks, proof, at most about 10 lines. The lane writes it in its first commit and updates it in the same commit when the code departs from it (the playbook's "update plan.md in the same commit"). **Guard:** the orchestrator's pre-push validation in `tools/github/ship_open_prs.py`, which already checks every PR before anything is pushed, fails when the diff touches a file the Plan does not name, unless the commit that adds the file also updates the Plan. Feeding the same list to the spec-fit reviewer is only a hint, because an LLM-judged check "will not self-halt" (v2 spec) | `tools/github/ship_open_prs.py`; `tools/workflows/lane.js`; implementation-note template (AA-1102 R2a); AA kit `project-ship` skill (AA-1103 R4) | 0.5 | **Medium.** Keep it inside the existing note, never a new `plan.md`, and cap it at about 10 lines |
| 3 | **Failing test first for the `fix` path.** Two commits: the test (which must fail on the base), then the fix. A git check in `lane.js` refuses a fix commit that edits the test from the first commit. This is the playbook's "without editing the test" rule, as a check rather than a sentence | `tools/workflows/lane.js`; Copier template docs (AA-1103 R3) | 0.5 | None |
| 4 | **A "Verified live" receipt written by CI, not by the agent.** A post-deploy job in each app's deploy workflow runs the lane's `live_steps` checks (rollout state and running image SHA, `git_sha` on `/health`, HTTP status and shape of each changed endpoint, that is `aa-ship` §3 steps 1, 2 and 4) and posts the receipt (commands, results, timestamp, run link) as a PR comment under the workflow's own identity. A script the agent runs locally would print a block the agent can still edit or retype, so it would not be a guard. `aa-ship` §4 then links that comment instead of retyped evidence. Steps 5 (UI screenshot), 7 (DB Isolation Probe) and 8 (LLM eval) stay manual or link their own workflow runs. Using the `aa-ci-bot` App for the comment would widen what ADR 0011a lets it do, so it needs an amendment; the workflow token does not. This follows AI-DLC's "a hand-written proof file cannot verify a Unit", for part of §3 only | App deploy workflows (CIS, Booking, Partner); `skill/aa-ship/SKILL.md` §3 and §4; `project-ship` (AA-1103 R4) | 1.5 | **Low.** It replaces typing with output |
| 5 | **An instruction budget, measured in bytes.** The always-loaded set is about 53 KB today (§6 Build row). The playbook's "under a page" is about one project CLAUDE.md, so it is a direction, not a target for the whole set. Move procedures into skills loaded on demand; keep hard rules plus pointers. **Guard, in two parts:** a docs-lint check in root CI fails when the repo files (root `.claude/CLAUDE.md` plus the three steering files) grow past a byte budget stored in the lint config. Root CI cannot see the global CLAUDE.md or `MEMORY.md`, so a local SessionStart hook warns when they pass their own budget. The tech lead edits the global CLAUDE.md by hand (handbook §2.3); the agent proposes the cut | AA-1102 R1 (clean-up, already 1 session); `tools/docs/` lint and `docs-lint.yml`; a SessionStart hook in `.claude/hooks/` | 0.25 on top of R1 | **Negative.** It cuts text. Risk: dropping a rule that matters, so each removed line moves to a skill, a hook or `guards.md`, never just deleted |
| 6 | **A scope field in the learning loop.** When the tech lead corrects the agent, the agent proposes the lesson line (with its Guard) and asks one thing: "AA only, AA kit, or none?". "AA kit" means the AA new-project kit's skills (AA-1103), nothing outside AA. **Guard:** `tools/docs/check_lessons.py` already requires a well-formed `Guard:` field on every new lesson line; it also requires `Scope: aa` or `Scope: aa-kit`. The check proves the field is there, not that the answer is right | `skill/aa-lessons/SKILL.md` §2 and §3; `tools/docs/check_lessons.py`; AA-1103 R4 | 0.1 | **Low.** The Guard rule already stops prose lines piling up |
| 7 | **Format rules for decision pages**, taken from AI-DLC's question files: 2 to 5 real options, no padding options, a last "Other", the proposed answer marked, who usually answers (tech lead or business owner), and a vague answer gets re-asked. As a skill rule this is **advisory**. It becomes a guard only with one shared decision-page template whose question data a lint checks (an "Other" option present, exactly one proposed answer marked) | `skill/aa-session/SKILL.md` (the "questions for the tech lead" rule, which already asks for one clickable decision page); a decision-page template and its lint (AA-1102 R2a) | 0.1 for the rule; 0.5 with template and lint | **Low** |
| 8 | **Later: agent-behaviour evals.** 10 to 20 replay tasks run by hand in a session when a skill or hook changes, scored by a deterministic check where possible. AA already replays the shell guard over past commands (`.claude/hooks/replay_shell_guard.py`). A CI `claude -p` suite would need an API key, which means new spend, so not now | After the kit pilot (AA-1103 R5) | 1 | Medium. Keep the set small and retire cases that no longer discriminate (the playbook warns that evals decay) |
| 9 | **Later: a production-gate hook** that refuses deploy commands for production unless a release approval is present, plus deploy, status and rollback tools scoped per environment. Write it at the prod trigger, together with enforced code owners | Handbook §6.5 prod switch; kit principle "switches by phase" (AA-1102) | 0.5 | Low |
| 10 | **Later: a Maintain loop**: deterministic bands on the existing alarms; a breach writes a draft Linear issue in DoR form. Only once there is real traffic (Dev has none) | Handbook §7.2; ops runbooks | 1 | Low |
| 11 | **Teach it in the Academy**: one explanation page, "Our agent lifecycle compared with AI-DLC and the Anthropic playbook", built from sections 2 to 6 of this note. It fills part of gap G11 (no agent-orchestration explainer) and feeds module L3. It links the free Anthropic course and quotes the MIT-0 rules where useful | AA-1104 (gap pages); AA-1105 (L3 module and quiz) | 0.5 | **Medium.** One page that links rather than copies. The Academy drift check (`docs/research/lms/README.md` §6.4) flags it when sources change |

**What each path requires** (rec 1):

| Path | When | Needs |
|---|---|---|
| `fix` | A bug with a clear, isolated scope | Failing test first (rec 3), one reviewer lens, no ADR, short Plan |
| `small` | A small change with no new boundary | Short Plan, one or two lenses, no ADR |
| `feature` | New behaviour or a new contract | Full DoR, Plan, two lenses, ADR if a choice is hard to reverse |
| `risky` | Auth, migration, IAM or secret, data deletion (the DoR risk classes) | As `feature`, plus `kiro-reviewer`, plus DRY RUN for deletion |

**Do not adopt**

- **The AI-DLC v2 engine** (binary, about 17 hooks, 2,357 files, breaking changes). AA's own hooks and `lane.js` cover the
  same ground, and they fit our repos.
- **Mob Elaboration and Mob Construction rituals.** AA is one tech lead plus agents; there is no room of people to run them.
- **`intent.md`/`spec.md`/`plan.md` files for every change.** Linear plus the DoR, ADRs and `CONTEXT.md` already hold
  intent and design. The plan lives in the implementation note (rec 2). More files would bring the review load that
  Böckeler (about spec-kit and Kiro) and Thoughtworks warn about.
- **A raw-words `audit.md`.** Commits and decision-page records are enough, and raw chat logs carry private data.
- **Managed Code Review, Claude Tag and Claude Design.** They are beta or research preview, may carry new cost, and AA
  does not use Slack. Enterprise managed settings do not fit a single-developer setup today.

**How adopted items reach AA's kit and AA Academy.** Both are AA's own (AA-1098, AA-1099); this paragraph is not about
any product outside AA. The kit design is already "handbook-first": a rule changes in the
handbook or a skill first, then in the kit and its copies ([kit §5.1](../../research/new-project-playbook/README.md),
principle 3). The Academy renders from the same pages and flags drift when a source section changes
([Academy §6.4](../../research/lms/README.md)). So each item above lands once, in AA's own handbook, skill or
tool, through its normal PR. The kit (AA-1102, AA-1103) and the Academy (AA-1104, AA-1105) then pick it up through those
existing paths. Rec 6 adds the one missing link: lessons meant for the AA kit get labelled at the moment they are
written, so the kit's skills do not need a later sweep.

## 8. Sources

| Title | URL | Publisher | Date | Licence | Used for |
|---|---|---|---|---|---|
| AI-DLC Method Definition paper | https://prod.d13rzhkk8cj2z0.amplifyapp.com/aidlc.pdf | AWS (Raja SP) | Undated (linked Jul 2025); URL not permanent | None stated (AWS copyright) | Principles, artifacts, rituals, Appendix A prompts (quotes not re-checked) |
| AI-Driven Development Life Cycle: Reimagining Software Engineering | https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/ | AWS DevOps blog | 2025-07-31 | AWS site terms | Core idea (figure alt text), phases, Bolts |
| Open-Sourcing Adaptive Workflows for AI-DLC | https://aws.amazon.com/blogs/devops/open-sourcing-adaptive-workflows-for-ai-driven-development-life-cycle-ai-dlc/ | AWS DevOps blog | 2025-11-29 | AWS site terms | Adaptive workflow, gates at every decision |
| Building with AI-DLC using Amazon Q Developer | https://aws.amazon.com/blogs/devops/building-with-ai-dlc-using-amazon-q-developer/ | AWS DevOps blog | 2025-11-29 | AWS site terms | Run-to-run variance (read to Step 6 only) |
| AI-driven development lifecycle using Amazon Bedrock AgentCore | https://aws.amazon.com/blogs/machine-learning/ai-driven-development-lifecycle-using-amazon-bedrock-agentcore/ | AWS ML blog | 2026-09-03 | AWS site terms | Construction context only |
| awslabs/aidlc-workflows, tag v1.0.1 | https://github.com/awslabs/aidlc-workflows/tree/v1.0.1 | AWS Labs | 2026-06-30 | MIT-0 | v1 rules: stages, depth, question files, gates, audit, extensions, field guide |
| awslabs/aidlc-workflows, main at d8dd27dc (v2.11.4) | https://github.com/awslabs/aidlc-workflows | AWS Labs | 2026-11-13 | MIT-0 | v2 engine: phases, profiles, hooks, receipts, learning loop, plan-approval guard |
| AI-DLC Workflows 2.0 Specification | https://github.com/awslabs/aidlc-workflows/blob/main/assets/AI-DLC-Workflows-2.0-Specification.pdf | AWS Labs | Undated (touched 2026-11-12) | MIT-0 | v2 principles, verification limits (quotes not re-checked) |
| AI-DLC docs site | https://awslabs.github.io/aidlc-workflows/ | AWS Labs | Live | MIT-0 | Cross-check of the guide |
| The AI-Native SDLC Playbook (web) | https://claude.com/blog/the-ai-native-sdlc-playbook | Anthropic (Louis Claxton) | 2026-08-21 | None stated; © Anthropic | Thesis, stages, roles |
| The AI-Native SDLC Playbook (PDF, 54 pages) | https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf | Anthropic | PDF metadata 2026-09-23 | None stated; © Anthropic | All stage-level rules and quotes (checked against a text extraction; page cites match the printed footers) |
| AI-Native SDLC Playbook course | https://academy.claude.com/courses/ai-native-sdlc-playbook | Anthropic | 2026 | Anthropic terms | Course format (link for the Academy) |
| How Anthropic secures its AI-native SDLC | https://claude.com/resources/articles/how-anthropic-secures-its-ai-native-software-development-lifecycle | Anthropic (Jason Clinton, Deputy CISO) | 2026-07-21 | None stated | Related article on Anthropic's internal practice: reviewers on probation, action boundaries, self-reported figures (wording re-checked 2026-11-14) |
| anthropics/claude-code-action | https://github.com/anthropics/claude-code-action | Anthropic | Live | MIT | Licence check |
| anthropics/claude-code-security-review | https://github.com/anthropics/claude-code-security-review | Anthropic | Live | MIT | Licence check |
| anthropics/claude-code | https://github.com/anthropics/claude-code | Anthropic | Live | Proprietary | Licence check |
| anthropics/skills | https://github.com/anthropics/skills | Anthropic | Live | No repo-level licence found | Licence check |
| What is the AI-Native SDLC? | https://www.endorlabs.com/learn/what-is-the-ai-native-sdlc | Endor Labs (secondary) | 2026-10-22 | Site terms | Pairing of the two terms |
| github/spec-kit | https://github.com/github/spec-kit | GitHub | v1.4.0, 2026-11-10 | MIT | Field comparison, light paths |
| Kiro specs | https://kiro.dev/docs/specs/ | Kiro | Updated 2026-11-12 | Proprietary docs | Quick Spec, bugfix spec |
| Spec-driven development (Radar) | https://www.thoughtworks.com/radar/techniques/spec-driven-development | Thoughtworks | 2025-11-05 | © Thoughtworks | Criticism: opinionated, long specs |
| GitHub Spec Kit (Radar) | https://www.thoughtworks.com/radar/languages-and-frameworks/github-spec-kit | Thoughtworks | 2026-04-15 | © Thoughtworks | Criticism: context rot, skills on demand |
| Understanding Spec-Driven Development: Kiro, spec-kit, and Tessl | https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html | martinfowler.com (Birgitta Böckeler) | 2025-10-15 | © Martin Fowler | Three levels; review-cost and control criticism |
| Announcing the 2025 DORA report | https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report | Google Cloud | 2025-09-24 | Blog terms (dora.dev content CC BY 4.0) | Amplifier finding, trust, stability |
| DORA AI Capabilities Model | https://cloud.google.com/blog/products/ai-machine-learning/introducing-doras-inaugural-ai-capabilities-model | Google Cloud | 2025-09-24 | Blog terms (dora.dev CC BY 4.0) | Seven capabilities |
| AWS AI-DLC: why AI coding still needs human accountability | https://www.scrum.org/resources/blog/aws-ai-dlc-why-ai-coding-still-needs-human-accountability | Scrum.org (Dave West) | 2026-08-04 | Site terms | Criticism: internal focus |
| AI-DLC Solves the Wrong Bottleneck | https://wakamoleguy.com/p/ai-dlc-solves-wrong-bottleneck | Will Mitchell | Page shows 2025-02-11, before the Jul 2025 launch, so unreliable | Site terms | Criticism: discovery upstream |
| The Role of UX in Agentic Software Factories | https://www.nngroup.com/articles/ux-agentic-software-factories/ | NN/g (Tanner Kohler) | 2026-10-30 | Site terms | Criticism of the Anthropic playbook: no UX stage or gate |
| "Agent-Ready SDLC" infographic | Not found | Rakesh Gohel | UNVERIFIED | UNVERIFIED | The trigger only |

## 9. Review notes

An adversarial review (2026-11-14) raised 10 findings. Each was checked again before it was applied.

| # | Finding | Verdict | What changed or why not |
|---|---|---|---|
| 1 | The note routes everything to AA-1102…1105 | Accepted, scope only | Header, §7 and rec 6 now say that "kit" and "Academy" mean AA's own (AA-1098, AA-1099). Products outside AA are out of scope for this note and are not described here |
| 2 | DORA "unless" overstated | Accepted | §5 item 5 quotes both sentences and drops "unless" |
| 3 | Clinton article is not a "companion" | Accepted | §4.1 and §4.2 call it a related article on Anthropic's own practice; quotes and all four figures re-checked on the page |
| 4 | Böckeler quotes applied to the wrong tools | Accepted | §5 item 1 names spec-kit and Kiro, and marks the transfer to AI-DLC and the playbook as our inference |
| 5 | NN/g marked UNVERIFIED | Accepted | Author, date and quotes added; the criticism is scoped to the Anthropic playbook |
| 6 | Mitchell's post may not be about AWS AI-DLC | Partly rejected | The post names the method as AWS's ("introduced by a solutions architect at AWS"), so it stays. Its shown date (11 Feb 2025) predates the launch blog, and §5 now says so |
| 7 | Provenance contradictions | Accepted, and partly resolved | Header states how each source was read. The playbook page cites were re-checked: a text extraction made in this session puts each quote on the page whose printed footer is p.3, p.7, p.9 or p.22. The paper and v2 spec quotes are marked not re-checked. The AWS core-idea line is labelled as figure alt text (confirmed in the page HTML) |
| 8 | Instruction budget mis-measured | Accepted | §6 and rec 5 measure bytes and include `MEMORY.md` (17,239 bytes; set total 53,114 bytes); the CI lint covers repo files only, a SessionStart hook covers the rest |
| 9 | Not all seven ideas are guards | Accepted | Rec 2 gets a hard pre-push check, rec 6 a `check_lessons.py` field, rec 7 is labelled advisory until a template and lint exist; §1 updated |
| 10 | Local receipt script is forgeable | Accepted, adjusted | Rec 4 moves the receipt into the deploy workflow and limits it to `aa-ship` §3 steps 1, 2 and 4. The workflow token is enough; using `aa-ci-bot` would need an ADR 0011a amendment. The finding text was cut off after "Reuse lane `li…"; it was read as "reuse the lane's `live_steps`" |
