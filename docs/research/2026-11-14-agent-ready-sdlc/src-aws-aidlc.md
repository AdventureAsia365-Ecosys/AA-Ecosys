# Source notes: AWS AI-Driven Development Life Cycle (AI-DLC)

Researched 2026-11-14. Primary sources only (official AWS blog, AWS Labs repo at pinned commits, the method
paper PDF, the v2 specification PDF in the repo). Quotes are verbatim and short. Repo quotes were read from the
files themselves (git clone), not from summaries. Blog quotes came through a page fetcher and are marked
"(via fetch)": they are reliable in substance, but check the exact wording against the page before you publish
any of them.

## 0. Source register

| # | Source | URL | Type / author | Date | Licence |
|---|---|---|---|---|---|
| S1 | AI-DLC Method Definition paper (8-page PDF, the "white paper") | https://prod.d13rzhkk8cj2z0.amplifyapp.com/ (a viewer of `./aidlc.pdf`, direct: https://prod.d13rzhkk8cj2z0.amplifyapp.com/aidlc.pdf) | Raja SP, AWS | Undated (first linked from S2, Jul 2025) | No licence stated. Assume AWS copyright: quote, do not copy |
| S2 | Blog "AI-Driven Development Life Cycle: Reimagining Software Engineering" | https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/ | Raja SP, AWS DevOps blog | 2025-07-31 | AWS site terms (not open) |
| S3 | Blog "Open-Sourcing Adaptive Workflows for AI-DLC" | https://aws.amazon.com/blogs/devops/open-sourcing-adaptive-workflows-for-ai-driven-development-life-cycle-ai-dlc/ | Will Matos, Raj Jain, Siddhesh Jog, Raja SP | 2025-11-29 | AWS site terms |
| S4 | Blog "Building with AI-DLC using Amazon Q Developer" (walkthrough) | https://aws.amazon.com/blogs/devops/building-with-ai-dlc-using-amazon-q-developer/ | same authors as S3 | 2025-11-29 | AWS site terms. The fetch returned only part of the page (up to Step 6) |
| S5 | Repo awslabs/aidlc-workflows, **v1 line**, tag v1.0.1 (the "rules files" edition) | https://github.com/awslabs/aidlc-workflows/tree/v1.0.1 (commit e49341dbeb8a) | AWS Labs | v1.0.0 2026-06-17, v1.0.1 2026-06-30 (first was v0.1.x, early 2026) | **MIT-0** (MIT No Attribution, `LICENSE`) |
| S6 | Same repo, **v2 line**, `main` at commit d8dd27dcf1fe (README badge 2.11.4) | https://github.com/awslabs/aidlc-workflows (commit d8dd27dcf1fe889dd521ea462d983aef831ae815) | AWS Labs | v2.0.0 2026-06-18; v2.11.4 2026-11-13; last commit 2026-11-13 | **MIT-0** |
| S7 | "AI-DLC Workflows 2.0" specification (6-page PDF in the repo) | https://github.com/awslabs/aidlc-workflows/blob/main/assets/AI-DLC-Workflows-2.0-Specification.pdf | AWS Labs (no author named) | Undated; last touched in the repo 2026-11-12 | Ships in the MIT-0 repo |
| S8 | Blog "AI-driven development lifecycle using Amazon Bedrock AgentCore" | https://aws.amazon.com/blogs/machine-learning/ai-driven-development-lifecycle-using-amazon-bedrock-agentcore/ | Banerjee, Kommuri, Ghosh, Pathangi | 2026-09-03 | AWS site terms. Construction phase only |
| S9 | Project docs site | https://awslabs.github.io/aidlc-workflows/ | AWS Labs | live | MIT-0 (rendered from repo `docs/`) |
| U1 | re:Invent 2025 session DVT214 "Introducing AI-Driven Development Lifecycle (AI-DLC)" (Anupam Mishra, Raja SP) | official session page / recording **not opened** | — | Dec 2025 | **UNVERIFIED**: only third-party write-ups seen (e.g. dev.to, jonmatum.github.io). No claims below rely on it |
| U2 | "AI-DLC Unicorn Gym" field offering (named in S1 §VI) | no public page opened | — | — | **UNVERIFIED** beyond its mention in S1 |

Note: the repo README's link to the method paper carries a TODO comment: "Replace this Amplify URL with a
permanent/stable URL when available" (S5 README line 10). So the paper URL may move.

## 1. The method (S1 paper, S2 blog)

### Principles (S1 §II, 10 principles, verbatim headings)
1. **Reimagine rather than retrofit**: "We need automobiles and not the faster horse chariots."
2. **Reverse the conversation direction**: "AI initiates & directs the conversations with humans"; "Humans serve as approvers, validating, selecting options, and confirming decisions at critical junctures." Analogy: Google Maps (human sets the destination, AI gives the turns).
3. **Integration of design techniques into the core**: DDD, BDD or TDD "flavors". The paper describes the DDD flavour.
4. **Align with AI capability**: "current AI is advancing but not yet reliable in autonomously translating high-level intentions into executable code"; "developers retain ultimate responsibility for validation, decision-making, and oversight."
5. **Cater to building complex systems**: "Simpler systems ... are outside the scope of AI-DLC and are better suited for low-code/no-code approaches."
6. **Retain what enhances human symbiosis**: keep user stories ("well-defined contracts") and the Risk Register.
7. **Facilitate transition through familiarity**: a practitioner should "orient and start practicing it in a single day"; "AI-DLC rebrands Sprints as Bolts".
8. **Streamline responsibilities for efficiency**: fewer specialist roles, but "Product Owners and developers remain integral".
9. **Minimise stages, maximise flow**: human validations "act as a form of 'loss function', by identifying and pruning wasteful downstream efforts before they occur."
10. **No hard-wired, opinionated SDLC workflows**: "AI recommends the Level 1 Plan based on the given pathway intention. Humans verify and moderate these AI-generated plans".

### Artefacts (S1 §III.1)
- **Intent**: "a high-level statement of purpose that encapsulates what needs to be achieved, whether a business goal, a feature, or a technical outcome".
- **Unit**: "a cohesive, self-contained work element derived from an Intent, specifically designed to deliver measurable value", "analogous to Subdomains in DDD or Epics in Scrum"; "The units are loosely coupled, enabling autonomous development and independent deployment".
- **Bolt**: "the smallest iteration in AI-DLC"; "build-validation cycles measured in hours or days rather than weeks"; "AI will plan the Bolts with developers / Product Owners validating it."
- **Domain Design**: business logic "independently of the infrastructure components", using DDD (aggregates, value objects, entities, domain events, repositories, factories).
- **Logical Design**: extends the domain design for NFRs with patterns (CQRS, circuit breakers). "AI creates the Architecture Decision Records (ADRs) for validation by the Developers."
- **Deployment Units**: packaged code + config + IaC "tested for functional acceptance, security, NFRs and other risks."

### Phases and rituals (S1 §III.2, S2)
- **Inception / Mob Elaboration**: "This happens in a single room with a shared screen led by a facilitator." AI proposes "User Stories, Acceptance Criteria and Units"; "the mob" (PO, developers, QA, stakeholders) adjusts "under-engineered or over-engineered parts". Outputs: "a) PRFAQ, b) User Stories, c) Non-Functional Requirement (NFR) definitions, d) Description of Risks (matching with organization's Risk Register, if present), e) Measurement Criteria that traces to the business intent and the f) Suggested Bolts". S2 (via fetch): "the entire team actively validates AI's questions and proposals."
- **Construction / Mob Construction** (also "Mob Programming and Mob Testing" in §IV): Domain Design, then Logical Design, then code and tests. Brownfield first lifts code into "static models" and "dynamic models". "AI-DLC recommends that this be done with all teams collocated in a single room". Teams "exchange the integration specifications (from domain model stage)".
- **Operations**: AI analyses telemetry, proposes runbook actions, "and execute the resolutions when approved by the Developers."

### Workflow (S1 §III.3)
- Nine-step figure: build context from existing code, elaborate intent with stories, plan units, model domain + code + test, NFRs, deployment architecture, generate IaC + test, deploy, monitor.
- "Each step serves as a strategic decision point where human oversight functions like a loss function - catching and correcting errors early before they snowball downstream."
- "All artefacts generated ... are persisted and serve as a 'context memory' that the AI references across the lifecycle"; "all artefacts are linked, allowing for backward and forward traceability".

### Appendix A prompt pattern (S1 pp. 7-8): the seed of the later rules files
Each prompt follows the same template: role, then "plan ... in an md file with checkboxes", then "If any step needs my clarification, add a note in the step", then "Do not make critical decisions on your own", then "ask for my review and approval", then "mark the checkboxes as done". Folder convention: `aidlc-docs/plans`, `aidlc-docs/requirements`, `aidlc-docs/story-artifacts`, `aidlc-docs/design-artifacts`, and "All prompts in order must be stored in the aidlc-docs/prompts.md file."

### Adoption (S1 §VI)
- "Learning by Practicing": practise the rituals on real problems. The AWS SA field offering is the "AI-DLC Unicorn Gym" (U2).
- "By embedding AI-DLC in the new Developer Experience Tooling", naming partner tools (FlowSource, CodeSpell, AIForce).

### Claimed benefits (S2, via fetch)
Velocity (weeks to "hours or days"), innovation, quality ("teams build precisely what they have in mind"), market responsiveness, developer experience. No measured figures in S1 or S2.

## 2. v1 rules edition (S5, tag v1.0.1): what the agent actually reads

### Packaging and installation
- The release zip has `aidlc-rules/aws-aidlc-rules/core-workflow.md` (the single always-loaded rule, 539 lines) and `aidlc-rules/aws-aidlc-rule-details/{common,inception,construction,extensions,operations}/` (about 30 files, ~6,300 lines in total), loaded on demand.
- Where each tool reads it (S5 README "Platform-Specific Setup"):
  - Kiro: `.kiro/steering/aws-aidlc-rules/` plus `.kiro/aws-aidlc-rule-details/`. README: use Kiro "in Vibe mode"; "Select `No`" when Kiro nudges you to spec mode.
  - Amazon Q: `.amazonq/rules/aws-aidlc-rules/` plus `.amazonq/aws-aidlc-rule-details/`.
  - Cursor: `.cursor/rules/ai-dlc-workflow.mdc` (with `alwaysApply: true` frontmatter) plus `.aidlc-rule-details/`.
  - Cline: `.clinerules/`.
  - **Claude Code**: "cp ... core-workflow.md ./CLAUDE.md" (or `.claude/CLAUDE.md`) plus `.aidlc-rule-details/`.
  - Copilot: `.github/copilot-instructions.md`.
  - Codex and others: `AGENTS.md`.
- The core file resolves the details folder by probing a path list: "Check these paths in order and use the first one that exists" (core-workflow.md, "MANDATORY: Rule Details Loading").
- Trigger: start the chat with "Using AI-DLC, ..." (README "Usage").
- The experimental "AI-assisted setup" has the agent download the release into `.aidlc/` and gitignore it.

### Stages (core-workflow.md)
- **INCEPTION**: Workspace Detection (ALWAYS), Reverse Engineering (CONDITIONAL, brownfield only), Requirements Analysis (ALWAYS, adaptive depth), User Stories (CONDITIONAL), Workflow Planning (ALWAYS), Application Design (CONDITIONAL), Units Generation (CONDITIONAL).
- **CONSTRUCTION**, run per unit: Functional Design, NFR Requirements, NFR Design, Infrastructure Design (all CONDITIONAL), then Code Generation (ALWAYS, "Part 1 - Planning" then "Part 2 - Generation"). Build and Test (ALWAYS) runs once after all units. "Each unit is completed fully (design + code) before moving to the next unit."
- **OPERATIONS**: "PLACEHOLDER". "All build and test activities are handled in the CONSTRUCTION phase."
- Each conditional stage has explicit "Execute IF" and "Skip IF" lists. For example, User Stories is skipped for "Simple bug fixes with clear, isolated scope", while "When in doubt, favor inclusion".

### Adaptive depth (common/depth-levels.md)
- "Stage Selection (Binary)": Workflow Planning decides "EXECUTE or SKIP". "If EXECUTE: Stage runs and creates ALL its defined artifacts".
- "Detail Level (Adaptive)": "Minimal", "Standard" or "Comprehensive". "Create exactly the detail needed for the problem at hand - no more, no less."
- Requirements Analysis scores request clarity, type (bug fix to new project), scope (single file to cross-system) and complexity (trivial to complex) to pick the depth.

### Questions in files (common/question-format-guide.md)
- "You must NEVER ask questions directly in the chat. ALL questions must be placed in dedicated question files."
- Format: `## Question N`, then options `A)`, `B)` ..., then `X) Other (please describe after [Answer]: tag below)`, then an empty `[Answer]:` line. "'Other' is MANDATORY as the LAST option"; "Don't make up options just to fill slots"; 2 to 5 meaningful options.
- The agent waits for "done", reads the file, checks every answer, and flags empty or invalid ones. Vague answers ("depends", "maybe", "mix of") trigger follow-up question files (common/overconfidence-prevention.md).
- Rationale (overconfidence-prevention.md): "AI-DLC was exhibiting overconfidence by not asking enough clarifying questions"; new rule: "When in doubt, ask the question - overconfidence leads to poor outcomes."

### Approval gates and how approvals are recorded
- Every executed stage ends with "**Wait for Explicit Approval** ... DO NOT PROCEED until user confirms", then "Log user's response in audit.md with complete raw input".
- Requirements gate: "⛔ GATE: Await User Answers ... Present the question file to the user and STOP."
- Fixed completion message: "REVIEW REQUIRED", then "WHAT'S NEXT?" with "Request Changes" or "Approve & Continue", plus "Add User Stories" when that stage was skipped. Construction stages must use the "standardized 2-option completion message"; "NO EMERGENT BEHAVIOR ... DO NOT create 3-option menus".
- **audit.md** (append-only): "Log EVERY user input ... with timestamp"; "Capture user's COMPLETE RAW INPUT exactly as provided (never summarize)"; "NEVER use file writing tools ... that overwrite the entire contents of audit.md". Entry template: `## [Stage]`, `**Timestamp**` (ISO 8601), `**User Input**`, `**AI Response**`, `**Context**`.
- **aidlc-state.md**: stage checklist plus `## Extension Configuration` table. Two-level checkbox tracking: plan files and the state file. Steps are marked "[x]" "in the SAME interaction where the work is completed".

### Artifacts written (core-workflow.md "Directory Structure")
- `aidlc-docs/inception/{plans,reverse-engineering,requirements,user-stories,application-design}/`
- `aidlc-docs/construction/{plans,<unit>/{functional-design,nfr-requirements,nfr-design,infrastructure-design,code},build-and-test}/`
- `aidlc-docs/operations/`, `aidlc-state.md`, `audit.md`.
- "Application code: Workspace root (NEVER in aidlc-docs/)".
- Named files include `requirement-verification-questions.md`, `requirements.md`, `stories.md`, `personas.md`, `unit-of-work.md`, `unit-of-work-dependency.md`, `unit-of-work-story-map.md`, `{unit}-code-generation-plan.md`, and `build-and-test/{build-instructions,unit-test-instructions,integration-test-instructions,performance-test-instructions,build-and-test-summary}.md`.

### Session continuity (common/session-continuity.md)
"Always read aidlc-state.md first". Before resuming, reload the artifacts of earlier stages. The "Welcome back" prompt itself is a multiple-choice question.

### Extensions (README "Extensions", core-workflow.md)
- Opt-in pairs `X.md` plus `X.opt-in.md`. Only `*.opt-in.md` loads at start: "saving context". Opt-in questions are asked during Requirements Analysis.
- Shipped: security baseline, property-based testing, resiliency baseline.
- Rule format: `## Rule <PREFIX-NN>: <Title>` with Rule and Verification sections. "Rules are blocking by default." Each stage completion includes a "compliant/non-compliant/N/A" summary.
- Caveat in the README: the security rules are "a directional reference ... Each organization should build, customize, and thoroughly test their own security rules".

### Tenets (S5 README "Tenets")
"No duplication", "Methodology first", "Reproducible" ("Rules should be clear enough that different models produce similar outcomes"), "Agnostic", "Human in the loop" ("The agent proposes, the human approves").

### Practitioner guidance (S5 docs/WORKING-WITH-AIDLC.md, field and workshop lessons)
- "clear the context at every natural decision point". "If your tool offers a 'compact context' prompt mid-workflow, always decline it". Resume with "Go to aidlc-docs/aidlc-state.md, find the first unchecked item". Commit at every reset.
- "AIDLC will defend its own prior decisions". So ask for a critique "in a fresh context".
- **"Never Vibe Code"**: "You never fix code directly ... go back to AIDLC and say: I have discovered issue X. Review the design and make a plan to fix it." The rule: "update the design first, then generate the code."
- Back-propagation sweep after code is done. At project end, "Create a set of reusable specification documents from the patterns expressed in this project". Keep human-facing reports out of `aidlc-docs/` so they do not pollute later context.
- Batching: "When two changes are tightly coupled ... include both in one prompt. When ... unrelated, do them one at a time."
- S5 also ships `docs/writing-inputs/` (vision document guide and technical-environment guide, with examples).

### Supporting tools in v1 (S5 README "Supporting Tools")
- `scripts/aidlc-evaluator`: golden test cases, semantic evaluation, code evaluation, NFR evaluation ("token usage, execution time, cross-model consistency"), CI.
- `scripts/aidlc-designreview`: "EXPERIMENTAL". Three review agents (Critique, Alternatives, Gap Analysis) on Bedrock Claude, run from the CLI or as a Claude Code hook.

## 3. v2 specification (S7) and engine (S6)

### Why v2 (S7 §1, §2 P6)
- "Version 2 keeps the methodology and rebuilds the workflow layer to march progressively towards autonomous software delivery — reducing human intervention as machine-checkable verification expands."
- Customer lesson: "our prescriptive stage definitions proved too opinionated, and that is where adoption friction arose. For example, AI-DLC 1.0 treats Build & Test as one stage, but for almost all customers it spans multiple activities". Their answer: Skills (agentskills.io spec) "as the unit of composition".

### v2 principles (S7 §2)
- P1 "Human Judgement Insights Can Be Distilled into Machines". "we have not yet reached consensus on whether human-in-the-loop can be eliminated entirely".
- P2 "Every Intent Starts Ambiguous (and That's OK)".
- P3 "AI as a Self-Correcting Solver (with a Safety Net)". It needs post-conditions "checkable by a program the AI cannot modify", a tractable success criterion and cheap iteration. "every self-correcting loop must include a halting condition, defined either as a maximum number of iterations or a token budget", then escalate to a human.
- P4 "The Three-Compartment Model": C1 "What" (declarative inputs and outputs, incl. required intermediates); C2 "How Do We Know It's Right" (post-conditions); C3 "What Did We Learn" (runtime learning to promote into C2).
- P6 "Staged Decomposition Over Single-Shot Compression": "Post-condition explosion" and "Combinatorial search explosion".
- P7 "Autonomous Development in Safe Increments Rather than as a Big-Bang": "Start with what you have", "Hydrate incrementally", "Expand the safe increment size".
- P8 Extensibility: additive, replacement, composable new stages.
- P9 "Learning from Practice (Compound Engineering)": "every correction is a candidate learning ... The proposal is shown to the human for approval before being promoted into the active rule set."

### Verification honesty (S7 §3)
- Two modes: "Inferential Verification Rules" (LLM instructions) and "Computational Verifications" (executables).
- Stated limit: "When the same model generates a candidate and then evaluates whether it meets a post-condition ... there is a risk that the model will converge on outputs that satisfy the letter of the check without satisfying its intent. For this reason, a stage whose Compartment 2 contains only LLM-judged post-conditions will not self-halt on its own verification."
- No-go rules ("no API endpoint shall be exposed without authentication") "must be verified deterministically using a custom linter or static analysis tool".

### Orchestrator and package manager (S7 §4-6)
- Orchestrator duties: goal ownership, workflow composition ("plan is mutable"), routing/observability/control (incl. a "full audit trail of every decision"), "Abstraction Boundary" (each stage is a black box), and "Cross-Stage Invariants".
- Package manager: one canonical stage file; tool emitters reference it "rather than physically copying" it (DRY), without dropping to the "lowest common denominator".
- Implementation guidelines (verbatim list): "Deterministic routing", "Agent specialization", "Artifact traceability", "Human approval: non-bootstrap stages require explicit approval", "Tool-owned state", "Advisory verification", "Controlled learning: new rules are admitted deliberately, not silently", "No hidden delegation: agents do not recursively spawn other agents".

### v2 as shipped (S6 README, docs/guide/*, at 2.11.4)
- "5 phases and 33 stages from initialization through operation", "14 agents: 11 domain experts, 2 reviewers, and an adaptive composer", "11 workflow profiles", "134-event audit trail" (README "Why AI-DLC").
- Phases (docs/guide/04-phases-and-stages.md): Initialization (0.1-0.3), Ideation (1.1 Intent Capture & Framing ... 1.7 Approval & Handoff), Inception (2.1 Reverse Engineering, 2.2 Practices Discovery, 2.3 Requirements Analysis, 2.4 User Stories, 2.5 Refined Mockups, 2.6 Domain Design, 2.7 Units Generation, 2.8 Contract Design, 2.9 Delivery Planning with `bolt-plan.md`), Construction (3.1-3.7, incl. 3.7 CI Pipeline), Operation (4.1 Deployment Pipeline ... 4.7 Feedback & Optimization). Operations is no longer a placeholder.
- Install: native `aidlc` binary (`curl ... install.sh | sh`), then `aidlc config --harness claude`, `aidlc doctor`, `/aidlc <request>`. Harnesses: Claude Code, Kiro (IDE plus CLI v3), Kiro CLI (V2), Codex CLI, Cursor, opencode, GitHub Copilot. Amazon Q is no longer listed in v2.
- Claude Code integration (S6 `harness/claude/`): `.claude/rules/aidlc.md` is an `@`-import stub of `aidlc/active-memory/{org,team,project}.md` plus phase rule files. `settings.json` registers hooks on SessionStart/End, UserPromptSubmit (record-human-turn), PreToolUse (guard-tool-call, deliver-stage-rules), PostToolUse Write|Edit (write-audit-log, run-sensors), PreCompact (validate-state), SubagentStart/Stop and Stop (continue-workflow). `.mcp.json` ships context7 and four AWS MCP servers.
- Workspace layout: `aidlc/spaces/<space>/{memory,knowledge,intents/<YYMMDD>-<label>/}`. Each intent record has `aidlc-state.md`, `audit/` shards (`<host>-<clone>.md`) and per-stage folders (glossary: "Record dir", "Audit trail").
- Six-state checkboxes (docs/guide/10-state-and-audit.md): `[ ]`, `[-]` in progress, `[?]` "Awaiting your approval (gate open)", `[R]` revising, `[x]`, `[S]` skipped.
- Profiles and adaptive depth (docs/guide/workflow-profiles.md): Classic 15/30 stages, Express 7, Feature 30, Enterprise 30 (Comprehensive), MVP 20, PoC 5, **Bugfix 6** (Minimal; "Skips ... design and architecture stages"), Refactor 7, Infra 12, Security patch 7, Workshop 23. The agent proposes a profile from the request and the human confirms. Example: "I'd run the "bugfix" plan ... 5 stages, 5 approval gates" (05-scopes-and-depth.md).
- Test strategy is separate from depth. Minimal is the "Nyquist model": "1 test per identified requirement", "~5-15 tests total".
- Questions (07-interaction-modes.md): still written to a questions file, now with three answer modes: "Guide me", "I'll edit the file", "Chat" ("Extracted decisions are written back to the questions file as the source of truth"). Each question is labelled with who usually answers it, e.g. `[Product owner]`, `[Developer]`.
- Approvals: a reviewer agent writes "READY / NOT-READY plus findings", loops up to `reviewer_max_iterations` (default 2), and "never blocks — the human always decides" (glossary "Reviewer"). Audit rows record "your git name" (10-state-and-audit.md "Who decided"). In Construction, an approval needs a recorded `Construction Verification Command` (SHA-256 bound to the human's Approve) and a tool-owned `CHECKPOINT_VERIFICATION_RECORDED` receipt: "a hand-written proof file cannot verify a Unit". There is a walking skeleton option. Autonomy choice: "Continue automatically" or "Review each checkpoint". "Failures always stop Construction, even in autonomous mode."
- Rules chain (09-rules-and-the-learning-loop.md): "org → team → project → phase → stage", "strict-additive". Learning loop question: "You asked me to <your change>. Keep that for next time?", with answers "Yes, for this project" / "Yes, for the team" / "No". Sensors are deterministic checks that run at gates (e.g. required-sections, upstream-coverage, traceability, linter, type-check, claim-sources).
- Stage definition file = YAML frontmatter contract (core/aidlc-common/stages/inception/units-generation.md): `lead_agent`, `support_agents`, `mode`, `reviewer`, `produces`, `consumes`, `requires_stage`, `sensors`, `scopes`, then the steps as prose.
- Phase boundary verification checks "every requirement maps to a story", orphaned artifacts and consistency (04-phases-and-stages.md).
- Org default (core/memory/org.md): trunk-based, "Each Bolt branch is **squash-merged** into `main`".

## 4. Criticisms and limits the sources themselves state
1. **Prose rules lose to the model.** core/hooks/aidlc-plan-approval-guard.ts header: "A field report showed prose losing that contest: a conductor generated the code first and backfilled the plan ... Per the framework layering (determinism belongs in tools and hooks, knowledge in agents, judgement with humans), this hook is the ordering's deterministic twin."
2. **The v1 stages were too opinionated** (S7 P6, quoted above). This drove the v2 rebuild.
3. **The model under-asks.** overconfidence-prevention.md says so outright and fixes it by asking more questions.
4. **LLM-judged checks can be gamed by the generating model** (S7 §3). Such stages cannot self-halt.
5. **AI is not reliable on its own yet** (S1 P4). The method does not suit simple or no-trade-off systems (S1 P5).
6. **Outputs are non-deterministic**: per S4 (via fetch), questions and artifacts differ between runs and the authors call this expected. The S5 tenet "Reproducible" aims only to "minimize variance".
7. **Context degrades**: "Output quality degrades in ways that are subtle and hard to diagnose" if context builds up across gates (WORKING-WITH-AIDLC.md).
8. **The security and resiliency extensions are directional only** (S5 README).
9. **Generative AI can make mistakes**: "Review generated output and costs" (S5/S6 README IMPORTANT box).
10. Observed, not stated by the authors: v2 has become a large engine (2,357 files at d8dd27d, a 134-event taxonomy, guard fences, weekly breaking "Compatibility: breaking for scripts" notes in the CHANGELOG). The "Methodology first ... Users shouldn't need to install anything" tenet of v1 has given way to a native binary install. The heavy ceremony also needs `/aidlc --learnings off` style switches and the Express/Bugfix profiles to keep small work light.

## 5. Adoption steps the sources recommend
- S1 §VI: learn by practising the rituals on real work (Unicorn Gym), and embed AI-DLC in internal developer tooling.
- S5 README "Usage": 1) start with "Using AI-DLC, ..."; 2) answer the structured questions; 3) "Carefully review every plan"; 4) review the execution plan; 5) "approve each stage"; 6) artifacts land in `aidlc-docs/`.
- S5 version control: commit `CLAUDE.md`, `AGENTS.md`, `.kiro/steering/`, `.aidlc-rule-details/` etc. Keep `.claude/settings.local.json` local.
- S7 P7: start with the post-conditions you can already codify, hydrate incrementally, then widen the autonomous increment.
- S6 docs/guide/onboarding.md (outline only, not read in full): "a five-run path for first-time teams" (00-introduction.md guide map). Prepare a vision document and a technical-environment document before larger work (docs/guide/writing-inputs/).

## 6. Takeaways for an agent-ready SDLC (generic, my synthesis, not from the sources)
- **Questions as a file with A/B/C + mandatory "Other" + `[Answer]:`** is a cheap, auditable decision format. It matches a "decision page" pattern. Steal the rules: no padding options, every option on its own line, validate empty or vague answers, and let v2's tri-mode (guide / edit file / chat writes back to the file) keep one source of truth.
- **Stage selection is binary, depth is adaptive.** Make the plan say EXECUTE/SKIP per stage with a one-line reason, and keep depth as a separate knob. Keep test volume as a third, separate knob ("Nyquist" minimal = 1 test per requirement).
- **Append-only audit log with the raw human words + ISO timestamps**, kept apart from a state file of checkboxes that resume reads first. In v2, gates show `[?]` "awaiting approval" so you can see who is blocking.
- **Deterministic guards beat prose.** Plan approval before code, as a PreToolUse hook. Proof receipts written by tools, not hand-written. Hold sensors at gates. Same lesson as "make guards, not reminders".
- **Learning loop with consent.** After a human correction, ask "Keep that for next time? project / team / no", then write to a layered rules file (org → team → project → phase). This is a structured version of a lessons log.
- **Never vibe-code**: fix the design or spec first, regenerate, then back-propagate. Critique in a fresh context. Clear context at gates instead of compacting. Keep reports out of the agent's context folder.
- **For a course (Academy/LMS)**: the S1 principles (loss-function gates, Intent→Unit→Bolt, mob elaboration) and the S7 three-compartment model (What / How we know it's right / What we learned) make clean lesson units. The MIT-0 licence of the rules lets you quote and adapt the rules files (S5/S6) freely. The S1 paper and the blogs carry no open licence: cite and paraphrase them.
- **For a project template**: a v1-style minimal kit (one core rule file, on-demand detail files, `questions/`, `state.md`, `audit.md`, extension opt-in pairs with `PREFIX-NN` rule IDs plus a Verification section) is small enough to fork. v2's engine is the "scale-up" reference, not the starting point.
