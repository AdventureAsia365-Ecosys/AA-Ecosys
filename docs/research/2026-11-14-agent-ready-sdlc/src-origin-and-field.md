# Agent-Ready SDLC: origin of the infographic and the field around it

Research notes, 14 Nov 2026. Primary sources only, unless a line is marked SECONDARY or UNVERIFIED. Quotes are
verbatim and kept short. No private or company data was used.

---

## 0. The infographic itself (Rakesh Gohel): UNVERIFIED

- Searched: web (standard + extended), the Substack archive API at `rakeshgohel.substack.com/api/v1/archive`
  (searched for "SDLC", "AI-DLC", "lifecycle", "playbook", "spec", "agent-ready"), and his two newest posts
  (5 Nov and 12 Nov 2026). None has an "Agent-Ready SDLC" post or graphic. LinkedIn
  (`linkedin.com/in/rakeshgohel01`) cannot be fetched without logging in.
- **Status: UNVERIFIED.** The original post, its date, and the sources it cites were not found. It is most likely a
  LinkedIn-only carousel or image.
- **Inference (not verified):** the title pairs "AI-DLC" with "AI-native SDLC". Those are the names of two primary
  sources that were both public by Nov 2026, and they are almost certainly what the graphic summarises:
  1. AWS **AI-DLC** (AI-Driven Development Life Cycle): Raja SP, AWS DevOps blog, 31 Jul 2025, plus the open-source
     `awslabs/aidlc-workflows` repo.
  2. Anthropic's **"The AI-native SDLC playbook"** (Louis Claxton, claude.com, 21 Aug 2026).
  - A vendor glossary that maps the terms supports this pairing: Endor Labs, "What is the AI-Native SDLC?"
    (published 22 Oct 2026, updated 27 Oct 2026), https://www.endorlabs.com/learn/what-is-the-ai-native-sdlc. It
    cites the Anthropic playbook URL and says "AI-DLC usually means AWS's named methodology, not shorthand for
    'AI-driven SDLC.'" (SECONDARY)
- Before you quote the infographic: get the exact post URL from the person who shared it, and check its
  stage-by-stage claims against sections 1 and 2 below.

---

## 1. AWS AI-DLC (AI-Driven Development Life Cycle)

### 1a. Launch blog post (the methodology)
- URL: https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/
- Author/date: Raja SP (Principal SA, AWS), **31 Jul 2025**. Licence: standard AWS site terms, not open licensed.
- Core model: "AI creates plans, seeks clarification, & implements plans, while humans make critical decisions"
  (figure caption).
- Three phases:
  - **Inception**: AI turns business intent into requirements, stories and units through **Mob Elaboration**, where
    "the entire team actively validates AI's questions and proposals."
  - **Construction**: AI proposes architecture, domain model, code and tests through **Mob Construction**, where
    "the team provides clarification on technical decisions and architectural choices in real time."
  - **Operations**: AI uses the accumulated context to "manage infrastructure as code and deployments, with team
    oversight."
- Vocabulary: **Bolts** replace sprints, described as "shorter, more intense work cycles measured in hours or days
  rather than weeks". "Epics are replaced by Units of Work."
- Gates: AI "implements solutions only after receiving human validation". The post lists no discrete gates.
- Artifacts: AI stores "plans, requirements, and design artifacts to your project repository."
- Limits stated: none. The speed claims are not quantified.

### 1b. Open-sourcing post
- URL: https://aws.amazon.com/blogs/devops/open-sourcing-adaptive-workflows-for-ai-driven-development-life-cycle-ai-dlc
- Authors/date: Will Matos, Raj Jain, Siddhesh Jog, Raja SP. **29 Nov 2025**.
- Key idea: the workflow "adapts to the problem rather than forcing the problem to adapt to the process". For
  example, a defect fix skips the deep requirements analysis. "Human approvals are embedded at every decision gate."
- First shipped as Amazon Q Developer Rules and Kiro steering files.

### 1c. Official repo `awslabs/aidlc-workflows` (primary; read the README and guide files directly via the GitHub API)
- URL: https://github.com/awslabs/aidlc-workflows
- **Licence: MIT-0** ("MIT No Attribution", Copyright Amazon.com). Repo created 13 Nov 2025. Latest stable release
  **v2.11.4 (13 Nov 2026)**, with preview v2.11.5 on 14 Nov 2026. About 6.1k stars.
- The repo has grown well past the 2025 blog. It is now an engine plus skill pack that runs in Claude Code, Kiro
  CLI/IDE, Codex CLI, Cursor, opencode and GitHub Copilot. README: "5 phases and 33 stages from initialization
  through operation"; "14 agents: 11 domain experts, 2 reviewers, and an adaptive composer"; "11 workflow profiles";
  "Human approval gates and source-bound review evidence"; "134-event audit trail plus persistent state, team
  knowledge, and learned rules".
- Phases (guide `docs/guide/04-phases-and-stages.md`):
  - **0 Initialization**: workspace scaffold, `aidlc-state.md`, `audit/` shards.
  - **1 Ideation**: intent capture, market research, feasibility (RAID log), scope, team formation, rough mockups,
    approval and handoff (initiative brief, decision log).
  - **2 Inception**: reverse engineering (brownfield), practices discovery (`team-practices.md`), `requirements.md`,
    `stories.md`/`personas.md`, domain design (`components.md`, `decisions.md` ADRs), units generation
    (`unit-of-work.md`, `unit-of-work-dependency.md` DAG), contract design, delivery planning (`bolt-plan.md`,
    risk/sequencing rationale).
  - **3 Construction** (per Unit): functional design, NFR requirements and design, infra design, code generation,
    build and test, CI pipeline.
  - **4 Operation**: deployment pipeline (rollback runbook), environment provisioning, deployment execution (smoke
    tests), observability (SLOs, alarms), incident response, performance validation, feedback and optimisation
    (cost analysis).
- Per-intent record directory: `aidlc/spaces/<space>/intents/<YYMMDD>-<label>/`.
- **Gates** (guide `07-interaction-modes.md`): "Every stage (except the 3 Initialization stages) ends with an
  approval gate". The options are Approve or Request Changes. The gate "requires an observed human-interaction
  seam". It records a `HUMAN_TURN` audit event, and the guide says this "proves presence and ordering, not
  authorship".
- **Walking skeleton plus a recorded verification command** (guide 04): "the first DAG Unit is the smallest working
  integrated slice. Its code must run through a real end-to-end check". The check is a "human-authorized
  `Construction Verification Command`", and "a hand-written proof file cannot verify a Unit".
- Phase-boundary verification: required artifacts exist, "every requirement maps to a story", no orphans.
- Failures halt work: "Failures always stop Construction, even in autonomous mode."
- Autonomy is opt-in: "Continue automatically / Review each checkpoint". The offer comes only after the skeleton
  checkpoint.
- Right-sizing: workflow profiles. **Express** = "The lightest requirements-to-code-and-test path" (7 of 30 stages).
  **Classic** = 15 of 30 stages. The guide says "Do not choose Express for ambiguous, cross-team, regulated, or
  architecture-heavy" work.
- Philosophy, "Small Mob, Broad Agents": "Rather than dozens of narrow specialists (an approach that recreates
  waterfall handoff chains)", it uses broad agents that carry context across stages.
- Limits stated: "Generative AI can make mistakes. Review generated output and costs before acting on them."; "works
  best with capable reasoning models". Trusting a Kiro folder lets its `.kiro` hooks run commands on your machine.
- Referenced, not opened: "AI-DLC Workflows 2.0 Specification" PDF (`assets/`), and the Method Definition Paper at
  https://prod.d13rzhkk8cj2z0.amplifyapp.com/. That page is JavaScript-rendered and came back with only a title, so
  it is **UNVERIFIED**.

### 1d. Criticisms of AI-DLC (practitioner blogs)
- Dave West (Scrum.org, author is a Scrum advocate and says so), 4 Aug 2026,
  https://www.scrum.org/resources/blog/aws-ai-dlc-why-ai-coding-still-needs-human-accountability. He writes that
  "AI-DLC's events are internal" and that a team could "ship the wrong thing, faster". Retrospectives are dropped,
  and psychological safety and skill growth are treated as out of scope.
- Will Mitchell, "AI-DLC Solves the Wrong Bottleneck", https://wakamoleguy.com/p/ai-dlc-solves-wrong-bottleneck:
  "I believe the bottleneck is further upstream", meaning discovery and well-scoped work. The page date reads
  11 Feb 2025, which is before AI-DLC launched, so the **date is UNVERIFIED**.
- Other blogs report that the full ceremony is too heavy for small or solo projects, and that mob rituals collapse
  when only one person in the room can read the artifacts. These are SECONDARY and were not opened in full.

---

## 2. Anthropic: "The AI-native SDLC playbook"

- URL: https://claude.com/resources/articles/the-ai-native-sdlc-playbook
- PDF (same content): https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf. Downloaded (1.5 MB)
  but not parsed: no PDF text tool is installed here. The quotes below come from the HTML page.
- Author/date: **Louis Claxton**, **21 Aug 2026**. A secondary source mentions a 28 Sep revision, but the page shows
  none (UNVERIFIED). Also published as a free Claude Academy course: https://academy.claude.com/courses/ai-native-sdlc-playbook
  (not opened).
- **Licence: none specific.** The footer says "© 2026 Anthropic PBC", under the general Anthropic terms. It is
  vendor content that promotes Claude products.
- Premise: "Build is no longer the constraint — the human-speed steps around it are." Old controls "stop matching
  reality and become intractable".
- Six stages, with the committed artifact as the common thread ("the commit chain serves as the audit trail"):

| Stage | Human | Agent | Artifact | Gate |
|---|---|---|---|---|
| 1 Plan | originator describes the idea; product owner corrects and commits | drafts a proto-spec | `intent.md` | product owner accepts/rejects |
| 2 Design | product owner; resolves policy conflicts | requirements and design, constrained by org skills | `spec.md` | product owner (plus tech lead if high risk) |
| 3 Build | engineer edits/approves plan, monitors parallel sessions | plan mode, then implementation (auto mode allowed) | `plan.md`, code, `CLAUDE.md`, skills | engineer (plus architect if high risk) |
| 4 Test | reviews evidence | tests, builds, screenshots; evals in CI | test output, eval results | code owner; eval pass-rate merge check |
| 5 Deploy | release manager authorises prod; code owner approves PRs | AI PR review, `@claude` fixes, release prep | `REVIEW.md` findings, PR history | branch protection; production deploy hook |
| 6 Maintain | service owner triages | monitors bands, diagnoses breaches, scheduled scans | `intent.md` from incidents, scan reports | triage; PR review for fixes |

- Key rules (verbatim):
  - `intent.md`: "The artifact contains what is wanted, why, and under which constraints."
  - Skills: "The organization's skills are applied as constraints on the spec." "A skill is a control, though an
    advisory one", and "nothing forces a session to comply with it", which is why hooks exist.
  - "Nothing is implemented without an accepted plan." "Plan mode enforces this itself, since Claude cannot edit
    files until the engineer accepts the plan."
  - **Spec drift**: "When implementation departs from the plan, update `plan.md` in the same commit." "Consider using
    a hook to enforce synchronization between the two."
  - **Review bottleneck**: "Two or three sessions is a sensible starting point." "The practical ceiling is how many
    streams one person can review properly, so add sessions only while review is keeping up."
  - **Evals**: "The pass-rate threshold is enforced as a merge check". "A skill change that drops the pass rate gets
    reviewed before it merges." "The evals should be seen as a live suite."
  - **Production gate**: "the agent may act up to the production gate and cannot pass it." "the agent has no route
    to push to main." "Findings do not approve or block a PR on their own".
  - **Maintain**: "Detection stays deterministic. Claude is invoked once a band is breached".
  - Scans: a scan "is a point-in-time statement about a codebase under a particular model, and both halves go stale."
  - Legacy systems: Jira and ServiceNow are hard to displace "because auditors and regulators already accept them".
    The advice is to name one source of truth per artifact.
  - Settings: "a starting point to tailor, rather than a recommendation to copy"; "every deny trades against
    capability".
- Adoption: the plays are modular. "Start with any clay play — nothing points into it, so it needs nothing first."
  Progression: "First, you prompt each step by hand with the end state being a loop in which each accepted artifact
  fires the next gate." Each play lists leading and lagging metrics, for example time to a committed `intent.md`,
  first-pass merge rate, rework cycles, eval pass rate, and DORA measures. No measured results are given.
- Plays by stage: Plan "Capture as intent.md". Design "Requirements and design". Build: plan mode as default, auto
  mode, CLAUDE.md, skills, hooks, parallel sessions and subagents. Test: feedback loop, continuous evals in CI.
  Deploy: AI in the PR review loop, hooks as approval gates, CI/CD. Maintain: closing the loop, recurring scans,
  Claude on call.

---

## 3. The field: spec-driven / agent-ready lifecycles to compare with

### 3a. GitHub Spec Kit (primary: repo README and `spec-driven.md`)
- URL: https://github.com/github/spec-kit. Docs: https://github.github.io/spec-kit/
- **Licence: MIT** (Copyright GitHub, Inc.). Created 21 Aug 2025. Latest release **v1.4.0 (10 Nov 2026)**. About
  150k stars.
- Flow: `/speckit-constitution` → `/speckit-specify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-implement` →
  `/speckit-converge`. "Repeat implement and converge until convergence reports `Converged`." The README says to
  review each result before continuing.
- Now also a framework of processes: bug fixing (`verified`/`partial`/`failed` verdict) and idea assessment
  (`go`/`needs-clarification`/`kill`). "These are independent entry points, not mandatory phases."
- Philosophy (`spec-driven.md`, "The Power Inversion"): "treating specifications as the source of truth, with code
  as the generated output". The constitution (`memory/constitution.md`) has nine articles: library-first, CLI,
  **"Test-First Imperative"**, project-defined IV to VI, **Simplicity and Anti-Abstraction gates** ("force it to
  justify every layer of complexity"), and integration-first testing.

### 3b. Kiro specs (primary: official docs)
- URL: https://kiro.dev/docs/specs/. **Last updated 12 Nov 2026.** The docs are proprietary product documentation.
- "structured artifacts that formalize the development process for features and bug fixes". Files:
  `requirements.md` (or `bugfix.md`), `design.md`, `tasks.md`.
- Variants: Feature spec (Requirements-First or Design-First), Bugfix spec (current, expected and unchanged
  behaviour, to prevent regressions), and **Quick Spec**, which generates all three "without approval gates" for
  well-understood features. The Quick Spec variant is Kiro's own answer to the "too heavy for small tasks" criticism.
- Review: "Markdown Review" with inline comments between phases. "Run all tasks" builds a dependency graph and runs
  independent tasks in parallel waves.

### 3c. Thoughtworks Technology Radar (primary; quoted under the 125-character limit)
- Spec-driven development, **Assess, published 5 Nov 2025** (Vol 33),
  https://www.thoughtworks.com/radar/techniques/spec-driven-development. It compares Kiro, spec-kit and Tessl.
  Caveats: workflows are "elaborate and opinionated". Some tools generate lengthy spec files that are hard to review.
  It is unclear who the PRDs are for. The field may be relearning the "bitter lesson" (hand-crafted rules for AI do
  not scale). The blip is not on the current edition.
- GitHub Spec Kit, **Assess, 15 Apr 2026**, https://www.thoughtworks.com/radar/languages-and-frameworks/github-spec-kit.
  The page's PDF link points to vol_35, while a search summary says Vol 34, so the volume is UNVERIFIED. Teams use it
  mostly in **brownfield** codebases and find the constitution useful. Problems reported: **instruction bloat leading
  to context rot**, which one team fixed by moving guidance into skills loaded on demand; unnecessary defensive checks;
  and verbose markdown that raised cognitive load. Experienced engineers with strong architecture practices got the
  most value.
- Licence: Radar content is © Thoughtworks. The pages show no open licence.

### 3d. Birgitta Böckeler (Thoughtworks), martinfowler.com (primary)
- "Understanding Spec-Driven-Development: Kiro, spec-kit, and Tessl", **15 Oct 2025**,
  https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html. Footer "© Martin Fowler"; no open licence.
- Three levels: **spec-first** ("A well thought-out spec is written first"), **spec-anchored** ("The spec is kept
  even after the task is complete"), **spec-as-source** ("the human never touches the code").
- Criticisms:
  - One workflow for every size: for a small bug, Kiro's workflow was "like using a sledgehammer to crack a nut".
  - Review cost: "I'd rather review code than all these markdown files."
  - False control: "I frequently saw the agent ultimately not follow all the instructions."
  - The line between a functional and a technical spec is unclear.
  - The MDD comparison: these approaches "might end up with the downsides of both MDD and LLMs" (inflexibility plus
    non-determinism).
  - Target user: "Probably not for large features that are still very unclear."
  - "Are we making something worse in the attempt of making it better?"

### 3e. DORA / Google Cloud (primary)
- 2025 DORA report, "State of AI-assisted Software Development". Announcement by Nathen Harvey and Derek DeBellis,
  **24 Sep 2025**, https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report. The
  survey covers nearly 5,000 respondents.
  - "AI doesn't fix a team; it amplifies what's already there."
  - "90% of survey respondents report using AI at work", and "30% report little or no trust in the code generated
    by AI."
  - Throughput is up, but "AI adoption does continue to have a negative relationship with software delivery
    stability". The report explains that "an increase in change volume leads to instability" without "robust control
    systems, like strong automated testing, mature version control practices, and fast feedback loops."
- DORA AI Capabilities Model, Kevin M. Storer and Derek DeBellis, 24 Sep 2025,
  https://cloud.google.com/blog/products/ai-machine-learning/introducing-doras-inaugural-ai-capabilities-model. The
  seven capabilities:
  1. Clear and communicated AI stance
  2. Healthy data ecosystems
  3. AI-accessible internal data
  4. Strong version control practices
  5. Working in small batches ("especially powerful in an AI-assisted environment")
  6. User-centric focus
  7. Quality internal platforms
- Licence: dora.dev content is **CC BY 4.0** ("All content on this site is licensed by Google LLC under CC BY 4.0,
  unless otherwise specified"). The capabilities model page was last updated 25 Nov 2025. The full report PDF was not
  opened, and its own terms are UNVERIFIED.

---

## 4. Synthesis: where the sources agree, and the strongest criticisms

**Common skeleton.** Intent, then spec/requirements, then design, then plan/tasks, then build, then verify, then
deploy, then operate/learn, with each step leaving a committed markdown artifact and a human gate.
- AWS: Inception, Construction, Operations (plus Ideation and Initialization in the 2.x repo).
- Anthropic: Plan, Design, Build, Test, Deploy, Maintain.
- Spec Kit: constitution, specify, plan, tasks, implement, converge.
- Kiro: requirements, design, tasks.

**Shared mechanisms**
- Persistent project rules: Spec Kit constitution, Kiro steering, `CLAUDE.md`, AI-DLC team knowledge and learned
  rules.
- Explicit approval gates.
- Units or tasks as a dependency graph run in parallel waves (AI-DLC DAG, Kiro waves).
- Deterministic hooks for rules that must hold.
- Evals or tests as merge checks.
- The agent never passes the production gate.

**Right-sizing has converged.** Every tool now ships a light path: AI-DLC Express, Kiro Quick Spec, Spec Kit's
separate bug-fix process. This answers the "sledgehammer" criticism.

**Strongest criticisms**
1. **Review bottleneck / verification debt**:
   - Anthropic caps parallel sessions at what one person "can review properly".
   - Böckeler would "rather review code than all these markdown files".
   - Thoughtworks warns of lengthy specs that are hard to review.
   - DORA links higher change volume to lower stability unless testing and version control are strong.
2. **Spec drift and false control**:
   - Agents ignore instructions (Böckeler).
   - A skill is "advisory" (Anthropic).
   - The fix is hooks that enforce updating `plan.md` in the same commit, and deterministic checks.
3. **Over-documentation, instruction bloat, context rot**: Thoughtworks Spec Kit blip; verbose markdown; the "bitter
   lesson".
4. **Wrong bottleneck / internal focus**: discovery and market validation sit upstream and outside the room (West,
   Mitchell).
5. **MDD redux**: spec-as-source risks inflexibility plus non-determinism (Böckeler).

**Recommended adoption steps, across sources**
- Start with no-prerequisite plays: intent capture, a rules file, skills (Anthropic "clay plays").
- Run 2 or 3 parallel sessions at most, and add more only while review keeps up.
- Turn on read-only pipeline steps before write steps.
- Prove a walking skeleton with a human-authorised verification command before autonomy (AI-DLC).
- Pick the lightest profile that fits; do not use Express for ambiguous or regulated work (AI-DLC).
- Strengthen the DORA foundations first: small batches, version control, automated tests, AI-accessible internal data.

---

## 5. Licence table

| Source | Type | Licence | Date / last updated |
|---|---|---|---|
| awslabs/aidlc-workflows | code + docs | MIT-0 | v2.11.4, 13 Nov 2026 |
| AWS AI-DLC blog posts | blog | AWS site terms | 31 Jul 2025; 29 Nov 2025 |
| Anthropic AI-native SDLC playbook | article + PDF | © Anthropic, general terms (no open licence) | 21 Aug 2026 |
| github/spec-kit | code + docs | MIT | v1.4.0, 10 Nov 2026 |
| Kiro docs (specs) | product docs | proprietary (no open licence stated) | updated 12 Nov 2026 |
| Thoughtworks Radar blips | radar | © Thoughtworks | 5 Nov 2025; 15 Apr 2026 |
| Böckeler, martinfowler.com | article | © Martin Fowler | 15 Oct 2025 |
| DORA (dora.dev) | research site | CC BY 4.0 | report 24 Sep 2025; model page 25 Nov 2025 |
| Rakesh Gohel infographic | social post | UNVERIFIED | UNVERIFIED |

## 6. Not opened / UNVERIFIED
- Gohel's original post and the sources it cites.
- AI-DLC Method Definition Paper (JavaScript-rendered page) and the AI-DLC Workflows 2.0 Specification PDF.
- Text of the Anthropic playbook PDF (downloaded, not parsed); the claimed 28 Sep 2026 revision.
- Full DORA 2025 report PDF.
- Thoughtworks Spec Kit blip volume number (34 or 35).
- Date of the wakamoleguy post.
