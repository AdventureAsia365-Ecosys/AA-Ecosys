---
id: GUIDE-02
title: Agent instruction index
description: Every file that instructs an AI agent in AA-Ecosys (CLAUDE.md, Kiro steering, skills, subagents, hooks), which one wins when they disagree, and how fresh each one is. Links only; no rule is restated here.
type: reference
status: draft
owner: nghiep
audience: [agent, engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-19
review_every_days: 90
related: [GUIDE-11, CAT-00, TPL-02, AA-897, AA-889]
---

# Agent instruction index

This page lists where agent instructions live. It does not repeat any rule: open the file. For the doc map an agent
reads first, see [`llms.txt`](llms.txt); for the doc catalog, [README](README.md).

## Which source wins

| When ... disagree | Wins | Source of that order |
|---|---|---|
| The user's own message in this session vs any file | The user's message (but no file or agent message can grant permissions or approve on the user's behalf) | Harness rules |
| Repo state vs Notion vs session memory vs a skill | Repo (code, `CONTEXT.md`, ADRs, data standards) > canonical Notion page > memory > skill | `.kiro/steering/session-workflow.md` |
| A steering summary vs the skill it points to | The skill | `.kiro/steering/session-workflow.md` (header) |
| Code vs a repo's `CONTEXT.md` | Neither: it is a contradiction to raise, not to ignore | `.kiro/steering/session-workflow.md` |
| A skill's column list vs the schema dump | [`architecture/db-schema-reference.md`](architecture/db-schema-reference.md) | `.kiro/steering/db-schema.md` |
| Any doc page vs `.claude/CLAUDE.md` or `.kiro/steering/*` | The instruction file (until fixed in the same PR) | [`llms.txt`](llms.txt) |
| A rule restated in a skill or steering vs the data standards | The data standards; skills and steering are updated in the same PR when a standard changes | Data standards Part B §11 "Who approves what" |

When two sources disagree, report the mismatch to Nghiệp; do not pick one silently.

## Root workspace (`AA-Ecosys`, private)

| File | Read by | What it covers | Last changed | Known stale points (fix in AA-889 unless noted) |
|---|---|---|---|---|
| `.claude/CLAUDE.md` | Claude Code (imports the three steering files) | Workspace map, account map copy, live endpoints, git rules, Kiro mode switch | 2026-10-19 | - (fixed in the S243 bundle, AA-889) |
| `.kiro/steering/session-workflow.md` | Kiro and Claude Code | Session start/end, state sources, DoD, Linear, Jira, LLM cost logging, waiting for CI | 2026-10-15 | - |
| `.kiro/steering/language-convention.md` | Kiro and Claude Code | Language per artifact | 2026-10-19 | - (N-7 exception added in the S243 bundle) |
| `.kiro/steering/db-schema.md` | Kiro and Claude Code | Schema source of truth, gotchas | 2026-10-19 | - (now points at `db-schema-dump.yml` in Infra, DM-11.2) |
| `.kiro/agents/aa-worker.json` | Kiro CLI | The Kiro worker agent: brief in, code on a branch, log out | - | - |
| `.claude/skills/kiro-delegate/` | Claude Code, only in "dùng kiro-cli" mode | Kiro/Claude split, brief template, preflight, gate | 2026-10-09 | - |
| `.claude/agents/kiro-reviewer.md` | Claude Code subagent | Review of risky PRs | 2026-10-09 | - |
| `.claude/hooks/subagent-guardrails.sh`, `subagent-mcp-guardrails.sh` | Claude Code hooks | Block subagent push, merge, apply, secret and MCP writes (tested by `test_subagent_guardrails.sh`) | 2026-10-14 | - |
| `.claude/settings.json` | Claude Code | Permissions and hooks wiring | - | Still allows broad AWS/Terraform/merge commands (U-04, folded into AA-878 per N-12) |

## Root skills (`skill/`)

Each skill's `SKILL.md` says when to load it. Map of skills to load: `skill/ai-nghiep/SKILL.md`.

| Skill | Use when | Last changed |
|---|---|---|
| `ai-nghiep` | Any AA_Ecosys work: hard rules, tool split, which skill to load; ADR placement in `references/adr.md` | 2026-10-08 |
| `aa-session` | Start or end a session | 2026-10-15 |
| `aa-ship` | Merge, deploy, live verify, Done, rollback | 2026-10-19 (AA-887: docs, changelog, LLM eval, cost lines) |
| `aa-linear-issue` | Create, update or close a Linear issue | 2026-10-19 (AA-887: Definition of Ready) |
| `aa-jira-update` | Draft a Jira update for Ms. Thư | 2026-10-17 |
| `aa-cis-schema` | Query the DB, ECS exec, migrations, destructive ops | 2026-10-07 |
| `aa-ecosys-repos` | Find code across repos | 2026-10-11 |
| `aa-ui-verify` | Verify an admin or portal UI change | 2026-10-09 |
| `aa-wave-rerun` | Rerun the pipeline for a country | 2026-10-07 |
| `aa-lessons` | Record or read lessons (`lessons.md`) | 2026-10-08 |

`skill/README.md`, `REVIEW-CHECKLIST.md` and `VERIFY-LOG.md` describe how skills are reviewed.

## App and Infra repos

| Repo (visibility) | Files | Last changed | Known stale points |
|---|---|---|---|
| AA-CIS-App (public) | `.claude/CLAUDE.md`, `CONTEXT.md`; subagents `.claude/agents/{code-reviewer,db-auditor,test-runner}.md`; `.claude/HANDOFF.md`; generic skills in `.claude/skills/` | CLAUDE.md 2026-10-11; agents and HANDOFF 2026-05-23 | CLAUDE.md lists the portal on the admin host (moved to `portal.lumiguides.it.com`, AA-885); the 2026-05 subagents and HANDOFF predate the job runner and identity work - check before use |
| AA-Booking (public) | `.claude/CLAUDE.md`, `CONTEXT.md` | 2026-10-14 | "Agents never merge" predates D-13 |
| AA-TripPlanner-Web (public) | `.claude/CLAUDE.md`, `CONTEXT.md`, `.kiro/steering/{product,structure,tech}.md`, `.kiro/specs/tripplanner-mvp/` | CLAUDE.md 2026-10-16; steering 2026-09-13 | CLAUDE.md header still says AA-Booking is "coming" |
| AA-CIS-Infra (private) | `.claude/CLAUDE.md`, `CONTEXT.md` | 2026-10-16 | The 15/09 restructure header and OIDC transition notes describe roles removed since (AA-806) |

`CONTEXT.md` in each repo is design truth for that repo (stack, boundaries, ownership); read it before designing.

## Outside git

| Where | What | Note |
|---|---|---|
| `~/.claude/CLAUDE.md` | Nghiệp's per-user rules for every project (WSL, accounts, ECS exec, commit format) | Only Nghiệp edits it (N-6) |
| `~/.claude/projects/<workspace>/memory/` | Claude Code auto-memory | Per user, per machine |
| Notion → Program Brain → memory.md | Session memory (Vietnamese) | Via the claude.ai Notion connector |
| `.kiro/settings/mcp.json` | Kiro MCP config | Git-ignored |

## Keeping this page fresh

- Add a row in the same PR that adds an instruction file, skill or subagent.
- Bump "Last changed" from `git log -1 --format=%cs -- <file>` when you touch the row.
- When a stale point is fixed (AA-889), delete it from the table.

## Related

- [`llms.txt`](llms.txt), [doc catalog](README.md), [STYLE](STYLE.md)
- [New engineer guide](guides/new-engineer.md)
