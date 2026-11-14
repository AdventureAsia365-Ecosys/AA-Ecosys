# Source notes: Anthropic "The AI-Native SDLC Playbook"

Researched 2026-11-14. All quotes are verbatim from the primary PDF unless marked otherwise. No private or company data used.

## 1. Identification (the infographic's source)

The infographic ("Commits an artifact at every stage": intent.md, spec.md, plan.md, evals, review findings; product owner /
engineer / code owner / release manager sign-offs; production gate where the agent stops; each stage reads the last
commit) matches ONE Anthropic document: **"The AI-Native SDLC Playbook"**, written by Louis Claxton (Anthropic Applied AI).

| Item | Value |
|---|---|
| Web page (blog) | https://claude.com/blog/the-ai-native-sdlc-playbook |
| Web page (resources) | https://claude.com/resources/articles/the-ai-native-sdlc-playbook |
| PDF (54 pages) | https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf |
| Course version | https://academy.claude.com/courses/ai-native-sdlc-playbook (14 lessons, ~1 h, "no quiz or completion badge") |
| Published | 21 Aug 2026 (web page). PDF metadata: CreationDate/ModDate 2026-09-23 (so the PDF was re-exported a month later). Web page shows no "last updated" date. A secondary source claims a revision on 28 Sep 2026: UNVERIFIED. |
| Category / products | "Best practices"; Claude Enterprise, Claude Code, Claude Tag |
| Acknowledged | Jim Blackhurst, Will Steuk, Jamal Arif |
| Licence | **None stated.** Page footer: "(c) 2026 Anthropic PBC" + links to Commercial Terms, Consumer Terms, Usage Policy, Privacy Policy. Treat as all-rights-reserved: summarise and quote briefly with attribution; do not copy wholesale into a product/course. |
| Basis | "best practices for integrating Claude internally across each stage of the SDLC ... inspired by working with our customers" (PDF p.3). No measured outcome figures are published in the playbook. |

## 2. Core thesis (PDF ch.01)

- "Organizations have started using AI to write code at a speed unthinkable one year ago, yet the processes around the code haven't changed at the same pace." (p.3)
- When build gets fast: "The bottleneck moves to the steps to the left and right of the build phase. This is mainly plan, review/test, and deploy, which still run at human speed." / "The controls stop matching reality ..." / "Governance costs increase because exceptions still route through meetings and committees" (p.4)
- "The AI-native SDLC is a reimagined process that combines the old control objectives with new enforcement. Instead of a linear flow, the process becomes a loop" (p.5)
- Artifact chain: "Each stage ends by writing one to version control (including intent.md, spec.md, plan.md, the diff and its tests, the PR with its review findings, and the incident record) and the next stage begins by reading it." (p.7)
- "For the early stages, .md files are the predominant artifact because a product owner and an agent can both read and act on the same file. From Build onward, the artifact is code and its records." (p.7)
- "The chain of commits is also the audit trail: who asked for what, what the agent produced, and who approved it." (p.7)
- Pull-quote: "Every stage commits an artifact the next stage can read. Together, the intent, the spec, the plan, the diff and the review findings are the audit trail." (p.7)
- Triggers: "An accepted intent.md triggers the requirements and design pass, an approved spec.md triggers plan mode, a merged PR triggers the pipeline, and a breached control band in production writes the next intent.md" (p.8)
- Adoption path: "First, you prompt each step by hand with the end state being a loop in which each accepted artifact fires the next gate. Human attention concentrates at the gates" (p.9)
- Each play has the same sections: What changes; Getting started (Prerequisites, Infrastructure); How to execute; Governance considerations; How to measure (leading + lagging indicator). A dependency graph (Figure 3) gives adoption order: "Start with any clay play — nothing points into it" (p.9).

## 3. Stage by stage

### Stage 1 — Plan: "Capture as intent.md" (p.11-13)
- Artifact: `intent.md`, "a proto-spec in the originator's own terms. The artifact contains what is wanted, why, and under which constraints."
- Entry routes: "A person has an idea, a ticket is filed, or an incident is surfaced via an alert".
- Sign-off: "the product owner reviews and corrects the agent-written intent.md before it is committed." Decision "is recorded as the merge or the closing review."
- Home: "For a single product the simplest home is an intent/ folder in the product repo." A dedicated intent repo only when intent spans many repos.
- Non-engineers: "a connector to the version-control system (e.g. GitHub) lets Claude commit markdown files on their behalf from claude.ai or Cowork."
- Template sections (example): Problem / Proposed outcome / Affected users and systems / Constraints / Open questions; header has Author and Status.
- Metrics: leading = time from first conversation to committed intent.md; lagging = "survival rate" (share accepted) + changes to intent.md after first spec.md commit.

### Stage 2 — Design: "Requirements and design" (p.15-17)
- Artifact: `spec.md`, produced by Claude from accepted intent.md, "guided by the organization's skills for brand, security, compliance, and UX", "with flagged areas of concern."
- "The product owner reviews that spec, but doesn't write it."
- Automation path: "Run it by hand at first, then codify it as an organization-level slash command. From there make the acceptance of intent.md in the intent home the trigger, with a non-interactive job that fires on the merge ... and commit spec.md as a pull request".
- Flagged concerns resolved "with its policy owner before engineering sees the spec."
- Gate: "A human team mate always makes this call, and accepting the spec is what starts the plan mode play". Higher-risk: product owner consults a technical lead.
- Governance: "The spec, the prompt that produced it, and the skill versions in force are all logged in version control."
- Lagging metric: "Count spec.md commits dated after the first plan.md commit for the same change."
- Front-end: Claude Design (beta) mock from intent.md, exported to Claude Code.

### Stage 3 — Build (p.19-29)
- Plan mode play. Artifact `plan.md`: "names the files that change, the order of the work, and the tests that prove it." Example sections: Files that change / Order of work / Risks / Proof.
  - "Iterate until an engineer who has never seen the conversation could implement the change from the plan alone."
  - "When implementation departs from the plan, update plan.md in the same commit. Consider using a hook to enforce synchronization between the two."
  - "Plan mode enforces this itself, since Claude cannot edit files until the engineer accepts the plan." Sign-off: "Routine changes are approved by the engineer, and anything the organization classes as higher risk goes to a tech lead or architect."
  - Chapter tagline: "Nothing is implemented without an accepted plan." (p.18)
- Auto mode: auto-accept "becomes the default for routine work: a tight spec.md, a small blast radius, and code the tests already cover." Shift "towards the review of artifacts after longer autonomous sessions."
- Sidebar "Legacy systems and the source of truth" (p.22): "for every artifact the process produces, name one system as the source of truth". Three configs: repo as SoT; legacy system as SoT (Claude reads/writes via MCP); "Linkage as the minimum bar. All artifacts note the record ID and all legacy records contain the commit SHA".
- CLAUDE.md: "/init", cut to day-one knowledge, check into git; "When Claude makes a mistake twice, the correction goes into CLAUDE.md."; "Keep it under a page". Example sections: Commands / Conventions / Architecture / Things Claude gets wrong. Code owners approve changes.
- Skills: "write a skill for institutional knowledge that must be applied consistently". In `.claude/skills/<name>/` or org-wide via plugin. "Test that the skill triggers." Policy owner signs off changes.
  - Key limit: "A skill is a control, though an advisory one ... nothing forces a session to comply with it. A policy that must always hold needs something deterministic behind the skill, such as a hook that blocks the action or a review pass" / "The skill makes violations rare and the hook makes them close to impossible."
  - Lagging metric: PR findings citing the policy should fall to zero; if not, "either the skill isn't triggering or its text has drifted".
- Hooks as build-time guardrails: "A skill is an advisory control while a hook is the deterministic layer behind it." Block protected paths, run formatter/linter, keep credentials out of diff. "build-phase hooks should be fast and scoped to the file that changed. Heavier checks ... belong at the commit or the PR." Approval-asking hooks belong at Deploy, not Build ("puts a person back on the critical path").
- Parallel sessions (worktrees: `claude --worktree feature-auth`) and subagents (`.claude/agents/*.md` with name, description, tools). "Two or three sessions is a sensible starting point. The practical ceiling is how many streams one person can review properly". Example verifier subagent: "Do not fix anything; report only."

### Stage 4 — Test (p.31-35)
- Feedback loop: "Always give Claude a way to verify its own work, whether tests, a build, or a screenshot diff."
  - Single command targets that exit non-zero; list commands with healthy output in CLAUDE.md; quantifiable targets.
  - Bug fixes: failing test first, commit it, "Only then ask Claude to make it pass without editing the test, with the test-file hook ... enforcing the restriction."
  - "the loop itself needs protecting ... A hook that blocks edits to test files during a fix task does this."
  - Evidence: "The literal output of "make test," the build log, or the screenshot diff that Claude ran and pasted". Approver: "The code owner reviewing the PR".
- Continuous evals in CI: "Evals are the AI-native equivalent of stage-gate QA."
  - "collects 20 to 50 real tasks from recent work with its expected/accepted outcome"; runs "on a schedule and on any change to CLAUDE.md, skills or hooks"; "A skill change that drops the pass rate gets reviewed before it merges."; "Each production incident gets an eval".
  - Example workflow `.github/workflows/agent-evals.yml` running `claude -p` per `evals/*.json` + `./evals/check.sh`.
  - Limit: "As models improve, cases that once discriminated stop doing so and new ones must be added". Some teams run evals offline on a cadence instead.

### Stage 5 — Deploy (p.37-46)
- AI in the PR review loop: managed Code Review (research preview) or `claude-code-action` in own CI.
  - `REVIEW.md` at repo root written by tech lead: passes Bugs / Security / Compliance ("the change matches spec.md, plan.md and our design principles"), what "Important" means vs Nit, cap nits (example: at most five), exclusions.
  - "Findings do not approve or block a PR on their own, and branch protection still requires approval from a code owner."
  - "@claude" on a comment -> Claude fixes and pushes; "let Claude babysit the PR to merge" until "green and waiting only on code owner approval".
  - "When a review flags a mistake for the second time, the correction goes into CLAUDE.md". Monthly tuning by rating findings.
  - "Separation of duties is preserved, because the agent that wrote the code has no way to approve it."
- Hooks as approval gates: "A hook can also ask, pausing the action until a specific person approves".
  - Steps: leadership + change management + compliance list gates that must survive; platform engineer writes each as a hook (allow/ask/block); "Team hooks go in .claude/settings.json in git, and non-negotiable hooks go in managed settings"; "A block should explain itself".
  - Example `production-gate.sh` (PreToolUse on Bash) blocks commands containing deploy+production unless `$RELEASE_APPROVAL` is set; "exit 2 blocks the action; the message goes to Claude".
  - Worked example: managed settings for a regulated enterprise (deny .env/secrets/WebFetch/curl/wget; allow git/make; disableBypassPermissionsMode; allowManagedPermissionRulesOnly; sandbox with failIfUnavailable, network allowlist, credential file/env denies; allowManagedHooksOnly; disableSideloadFlags; allowManagedMcpServersOnly; strictKnownMarketplaces; requiredMinimumVersion). Caveat: "Consider the above a starting point to tailor, rather than a recommendation to copy. Every deny trades against capability".
- CI/CD integration: prerequisites = PR review loop + hooks as gates, "because the gates must exist before automation accelerates anything through them."
  - Start read-only (`claude -p` triage failed build, flaky test summary, changelog), then write steps behind gates; "Anything the agent writes arrives as a PR through branch protection, and the agent has no route to push to main."
  - Sandboxed jobs, "short-lived scoped tokens, and hold no production credentials by default."
  - "Expose deployment through MCP. Deploy, status, and rollback become tools, scoped per environment".
  - "Tier the autonomy by environment. In development, the agent deploys freely. In production, the agent prepares the release and the release manager authorizes it, and a hook enforces the production gate. Staging sits somewhere in the middle."
  - "Rollback should be the most rehearsed path in the pipeline".
  - Principle: "The agent may act up to the production gate, and cannot pass it." / "Each non-interactive run acts under the agent's own identity". Lagging metric: DORA.

### Stage 6 — Maintain (p.48-52)
- "Stage 6: Maintenance runs headless, with an independent confidence gate between stages, a deterministic check or an adversarial reviewing agent, deciding whether the previous stage's output continues or is escalated to a human."
- Closing the loop: deterministic detection script (rolling mean/stddev + Western Electric rules), "detection stays entirely deterministic, with no model involved". `bands.yaml` tiers: 1 sigma log; 2 sigma Claude read-only diagnose; 3 sigma Claude "may act, though only by opening a PR into the review gate or triggering a pre-approved runbook."
- Output: "The agent writes its diagnosis as intent.md in the Stage 1: Plan format". Service owner / on-call triages (fix now / schedule / dismiss); product-facing to product owner. "Dismissals tune the bands". After fix: add an eval.
- Claude Tag (public beta, Slack): Claude in incident channels under its own identity; writes post-mortem "to a version-controlled lessons file that future investigations can read"; small fix -> PR, larger -> intent.md.
- Closing: "The loop keeps running. Human judgement stays above it." (p.53)

## 4. Roles and sign-offs (consolidated)

| Gate | Artifact | Human who decides |
|---|---|---|
| Plan -> Design | intent.md | Product owner (merge or close) |
| Design -> Build | spec.md | Product owner; policy owners for flagged concerns; technical lead if higher risk |
| Plan accepted -> code | plan.md | Engineer; tech lead / architect if higher risk |
| Test evidence | test output, build log, screenshot diff, eval pass rate | Code owner (PR); team owning config for eval-gated changes |
| Merge | PR + review findings (REVIEW.md) | Code owner via branch protection |
| Production | release authorization | Release manager (hook-enforced) |
| Maintain triage | intent.md from breach / incident | Service owner or on-call; product owner for product-facing |
| Policy / config | skills, CLAUDE.md, hooks | Policy owner (skills); code owners (CLAUDE.md); platform/IT admin (managed settings) |

Note: "evals" are an artifact of Stage 4 (results + the suite itself) rather than a per-change committed file; the infographic's listing is a simplification.

## 5. Tooling named (all official docs, code.claude.com/docs/en/...)
admin-setup, settings, server-managed-settings, permissions, sandboxing, hooks-guide, hooks, skills, plugin-marketplaces,
managed-mcp, third-party-integrations (Bedrock, Vertex, Foundry), network-config, monitoring-usage (OpenTelemetry),
analytics, security; platform.claude.com/docs/en/manage-claude/compliance-api. Product features: plan mode, auto mode,
`/init`, worktrees, subagents, `claude -p` headless, managed Code Review (research preview), claude-code-action, Claude
Design (beta), Claude Tag (public beta), Claude Security (Enterprise public beta), Agent SDK, Cowork.
(Doc pages listed from the PDF reference page; not individually re-opened in this pass.)

## 6. What is open source, under which licence (checked via GitHub API 2026-11-14)

| Item | Licence |
|---|---|
| The playbook (web/PDF/course) | No licence stated; (c) 2026 Anthropic PBC; Anthropic terms apply. NOT open content. |
| anthropics/claude-code-action (GitHub Action for PR review/@claude) | MIT |
| anthropics/claude-code-security-review (security review Action) | MIT |
| anthropics/claude-code (CLI) | Proprietary: "(c) Anthropic PBC. All rights reserved. Use is subject to Anthropic's Commercial Terms of Service." |
| anthropics/skills (public Agent Skills repo) | No repo-level SPDX licence detected (per-skill licences may differ: UNVERIFIED) |
| Code snippets in the playbook (hooks, settings.json, workflow, bands.yaml) | No separate licence; small illustrative examples. The patterns (file names, structure) are ideas, freely re-implementable; do not paste the prose. |

## 7. Recommended adoption steps (as the playbook states them)
1. Pick plays by the dependency graph; start with plays with no prerequisites (e.g. intent.md, CLAUDE.md, skills, feedback loop, hooks as approval gates have "Prerequisites: None").
2. "First, you prompt each step by hand" -> then org slash command -> then non-interactive job triggered by the merge of the previous artifact.
3. Gates before automation: PR review loop + hooks as approval gates are prerequisites for CI/CD integration.
4. Start CI with read-only judgement steps, then write steps behind gates, then deployment via MCP, tiered by environment.
5. Name one source of truth per artifact (repo, legacy tool, or at minimum linkage record ID <-> commit SHA).
6. Measure each play with a leading and a lagging indicator mostly derived from git/PR timestamps, CI, OpenTelemetry, incident tracker, DORA.

## 8. Limits and criticisms the source states itself
- Skills and CLAUDE.md are advisory; must-hold policies need hooks, managed settings, branch protection or a review pass.
- Managed settings example is "a starting point to tailor, rather than a recommendation to copy."
- Evals decay as models improve; need ongoing case refresh; some teams prefer offline cadence.
- Parallel sessions are capped by human review capacity.
- Approval hooks during Build put humans back on the critical path; keep them at Deploy.
- Legacy systems are hard to displace (auditors accept them), so the process "has to fit around what exists".
- Several products named are beta / research preview / public beta (Claude Design, managed Code Review, Claude Tag, Claude Security).
- No quantified results are published in the playbook itself.
- Minor inconsistency: Stage 6 is called both "Maintain" and "Maintenance".

External criticism (secondary, not primary): an NN/g article notes the lifecycle defines no explicit place for UX professionals (https://www.nngroup.com/articles/ux-agentic-software-factories/ — not opened, UNVERIFIED wording).

## 9. Closest companion official source
"How Anthropic secures its AI-native software development lifecycle", Jason Clinton (Deputy CISO), 21 Jul 2026,
https://claude.com/resources/articles/how-anthropic-secures-its-ai-native-software-development-lifecycle (no licence; (c) Anthropic).
Read via fetch summary (quotes below are as returned by the fetch tool; treat exact wording as near-verbatim):
- secure-coding guidance: "those guidelines are encoded in CLAUDE.md files and references to org-wide skills"
- new AI reviewers in shadow mode: "post comments for human approval until trust is earned"
- "The security engineer's job evolves from monitoring bugs to monitoring loops."
- Incident lesson: after a model upgrade an agent asked another agent to push a fix; a human gate caught it -> draw boundaries around actions and access, not model instructions.
- Self-reported figures (8x code per quarter, ~80% of merged code written by Claude, ~1/3 of past incident bugs would now be caught) are not independently audited.

## 10. Not opened / UNVERIFIED
- Claim of a 28 Sep 2026 revision (secondary only).
- Individual code.claude.com doc pages (only listed from the PDF).
- Related articles "building verification loops in Claude Code with skills" and "how Claude Tag runs on-call for CI/CD at Anthropic" (linked from the page, not opened).
- Licence of individual skills inside anthropics/skills.
