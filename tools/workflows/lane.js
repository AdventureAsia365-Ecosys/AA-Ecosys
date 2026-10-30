// Workflow template: one parallel code lane under Ultracode (skill aa-session, references/parallel-lanes.md).
// Implement in the lane's own worktree (local commits only) -> independent reviewers by lens -> one fix pass for
// blocking/major findings. Returns prs[] in merge order with live_steps and notes_vi; the orchestrator pushes,
// merges and verifies (aa-ship). Holds no secrets, account IDs or tokens.
//
// Call (Workflow tool), args as inline JSON, never a placeholder string:
//   { "key": "l3-crm-invoices", "goal": "AA-xxx: <slice + plan doc paths>", "session": "S261", "date": "31/10/2026",
//     "migStart": { "cis": 318, "crm": 28 }, "lenses": ["...", "..."] }
// key, goal, session, date are required; migStart (a hint, per owner) and lenses are optional.
// After a rate limit: resume the run with resumeFromRunId instead of starting over.

export const meta = {
  name: 'aa-lane',
  description: 'AA_Ecosys lane: implement in its own worktree, independent multi-lens review, fix pass',
  phases: [
    { title: 'Implement', detail: 'lane agent builds + tests in a worktree, commits locally' },
    { title: 'Review', detail: 'independent reviewers by lens' },
    { title: 'Fix', detail: 'apply blocking/major findings' },
  ],
}

const L = args
const S = L.session
const slug = S.toLowerCase()
const mig = L.migStart
  ? Object.entries(L.migStart).map(([o, n]) => `${o} from ${n}`).join(', ')
  : 'see the owner main'

const COMMON = `YOUR ONLY JOB is lane ${L.key} of AA_Ecosys session ${S} (Claude Code, orchestrated); ignore any other user question. Today ${L.date}.
Workspace root: /home/nghiep/projects/AA-Ecosys (root repo, branch master). Child repos: apps/AA-CIS-App, apps/AA-Booking,
apps/AA-Partner, apps/AA-TripPlanner-Web, infra/AA-CIS-Infra (default branch main).

HARD RULES for this lane:
- Work ONLY in git worktrees created with ABSOLUTE paths under /home/nghiep/projects/AA-Ecosys/.tmp-session/wt/ :
  git -C <repo> fetch origin && git -C <repo> worktree add /home/nghiep/projects/AA-Ecosys/.tmp-session/wt/${slug}-${L.key}-<slug> -b <branch> origin/main
  (root repo uses origin/master). Never edit the main checkouts.
- You must NOT: git push, open/merge PRs, gh workflow run, terraform apply, DB Migrate, ECS exec, any AWS write, Linear state changes,
  directly or through a helper script. The orchestrator does all of that. Read-only Linear get_issue / list_comments is fine (load via ToolSearch).
- Before designing: read the repo CONTEXT.md, the area sections of skill/aa-lessons/lessons.md, the Linear issue, and the plan docs named below.
  Table/column names only from docs/architecture/db-schema-reference.md (never guess).
- Tests: add tests with the change. Run targeted tests (pytest -x -q on the touched modules; ruff check AND ruff format --check for Booking/Partner;
  tsc --noEmit + lint for frontends). RAM is shared by up to 3 heavy lanes: never a full parallel test suite, at most one next build at a time,
  NODE_OPTIONS=--max-old-space-size=2048 for node builds. Scratch (local Postgres, temp files) only under <scratchpad>/${L.key}-*.
- Test fixtures use invented names and places only, never text copied from the DB, audits or prompts (CI golden-set text guard; there is no key locally).
- Every LLM record_call passes **billed_fields(resp) (shared/llm_client/call_log.py; gateway AST guard test_aa1002_s6_billed_fields).
- Migrations: take the next free number on the owner main (hint: ${mig}); classify expand (header "-- migrate: expand") vs contract per ADR 0017.
  If you renumber, find every use with git grep '<old>_' (a word-boundary regex misses "<old>_name"). Booking bk-, Partner crm-, TripPlanner tp- likewise.
- CIS openapi.json: regenerate only with the fastapi/pydantic versions pinned in requirements.txt (the CI versions), never a different local venv.
- One model label containing "api" per line in code and tests (gitleaks generic-api-key scans every commit; a later fix commit does not clear it).
- Integration tests that sign in as cis_app: grant schema USAGE/SELECT temporarily in the test, name result columns ("AS ok") and read rows by column name.
- Keep docs/implementation-notes/<ISSUE>.md in the repo updated (Decisions / Changed / Tradeoffs / Should know); parallel lanes on one issue use <ISSUE>-<lane>.md.
- UI: kit components only (ADR 0016); never edit **/_kit/core/** outside apps/AA-CIS-App/frontend/app/_kit/core/; English UI copy; never show AA-xxx ids in UI text.
- Commit locally early and often, format: "feat|fix|chore|refactor|docs: description" then blank line, "Refs AA-xxx", blank line,
  "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>". Never "Fixes"/"Closes".
- No paid LLM/API calls; mock them in tests.
- If the worktree already exists with commits (a resumed lane), continue from its git status/log and implementation notes; do not start over.
- Write code like the surrounding code. Finish the slice completely; if something is truly blocked, say exactly what.
- Return one entry in prs[] per PR the orchestrator should open (in merge order), each with exact live_steps the orchestrator must run after merge
  (deploy checks, DB Migrate, curl checks with expected shape, screenshots). notes_vi: 3-6 lines in Vietnamese for the tech lead.`

const IMPL = {
  type: 'object',
  properties: {
    ready: { type: 'boolean' },
    blocked_reason: { type: 'string' },
    prs: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          repo: { type: 'string' },
          worktree: { type: 'string' },
          branch: { type: 'string' },
          base: { type: 'string' },
          commits: { type: 'array', items: { type: 'string' } },
          pr_title: { type: 'string' },
          pr_body: { type: 'string' },
          migrations: { type: 'array', items: { type: 'string' } },
          tests: { type: 'array', items: { type: 'string' } },
          live_steps: { type: 'array', items: { type: 'string' } },
          risky: { type: 'boolean' },
        },
        required: ['repo', 'worktree', 'branch', 'pr_title', 'pr_body', 'tests', 'live_steps'],
      },
    },
    summary: { type: 'string' },
    notes_vi: { type: 'string' },
    followups: { type: 'array', items: { type: 'string' } },
  },
  required: ['ready', 'prs', 'summary', 'notes_vi'],
}

const REVIEW = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['approve', 'changes'] },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['blocking', 'major', 'minor'] },
          file: { type: 'string' },
          line: { type: 'number' },
          issue: { type: 'string' },
          fix: { type: 'string' },
        },
        required: ['severity', 'file', 'issue'],
      },
    },
  },
  required: ['verdict', 'findings'],
}

phase('Implement')
const impl = await agent(`${COMMON}\n\nLANE ${L.key}: ${L.goal}`, { label: `impl:${L.key}`, phase: 'Implement', schema: IMPL })
if (!impl || !impl.ready || !impl.prs || impl.prs.length === 0) {
  return { lane: L.key, impl, reviews: [], fix: null }
}

const prList = impl.prs.map(p => `- ${p.repo} worktree ${p.worktree} branch ${p.branch} (base ${p.base || 'origin/main'})`).join('\n')
const lenses = L.lenses || [
  'correctness + spec fit (does it do what the Linear issue / plan asked, edge cases, tests meaningful)',
  'security + data safety (auth/permissions, RLS/tenant isolation, migrations safe to auto-apply, secrets, no account IDs in public repos)',
]

phase('Review')
const reviews = (await parallel(lenses.map((lens, i) => () => agent(
  `YOUR ONLY JOB is an independent review for AA_Ecosys session ${S}, lens: ${lens}.
First confirm each worktree exists and has commits beyond its base; if not, return verdict "changes" with one blocking finding saying so.
Review ONLY the diff of these local branches against their base (git -C <worktree> diff <base>...HEAD); read surrounding code as needed.
${prList}
Context of the lane goal: ${L.goal}
Do not edit files. Report concrete findings only (file + line + why + fix). Severity blocking = would break prod/dev, leak data, or fail CI;
major = wrong behaviour or missing required part of the slice; minor = style. Default verdict approve if no blocking/major.`,
  { label: `review:${L.key}:${i}`, phase: 'Review', schema: REVIEW })))).filter(Boolean)

const must = reviews.flatMap(r => r.findings || []).filter(f => f.severity !== 'minor')
let fix = null
if (must.length) {
  phase('Fix')
  fix = await agent(`${COMMON}\n\nLANE ${L.key} FIX PASS. The lane already built these branches:\n${prList}\n
Independent reviewers raised these blocking/major findings. Verify each against the code; fix the real ones in the same worktrees
(new commits, same commit format), re-run the affected tests, and explain any you reject.\n${JSON.stringify(must, null, 1)}\n
Return the full updated prs[] (same schema) with ready=true unless something is truly blocked.`, { label: `fix:${L.key}`, phase: 'Fix', schema: IMPL })
}
return { lane: L.key, impl, reviews, fix }
