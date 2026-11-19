// Workflow template: one parallel code lane under Ultracode (skill aa-session, references/parallel-lanes.md).
// Implement in the lane's own worktree (local commits only) -> independent reviewers by lens -> one fix pass for
// blocking/major findings. Returns prs[] in merge order with live_steps and notes_vi; the orchestrator pushes,
// merges and verifies (aa-ship). Holds no secrets, account IDs or tokens.
//
// Call (Workflow tool), args as inline JSON, never a placeholder string:
//   { "key": "l3-crm-invoices", "goal": "AA-xxx: <slice + plan doc paths>", "session": "S261", "date": "31/10/2026",
//     "migStart": { "cis": 318, "crm": 28 }, "lenses": ["...", "..."] }
// key, goal, session, date are required; migStart (a hint, per owner) and lenses are optional.
// After a rate limit: resume the run with resumeFromRunId instead of starting over (the guard lets a replay through).
// Spec lanes (AA-1137): optional "spec" (the .kiro/specs/AA-<n>-<slug> folder, relative to the workspace root) and
// "tasks" (["T1", "T2"]): the lane implements only those tasks, returns trace[] (one entry per task) and gets the
// reviewer lens "spec". .claude/hooks/lane_start_guard.py checks the spec (approved / in-progress, open tasks, no other
// lane holding them) only when spec is given; a lane without spec runs as before.
// A FRESH launch of a lane whose worktree already exists needs "resume": true (AA-1024 G20;
// .claude/hooks/lane_start_guard.py refuses it otherwise): the agent then reports resumed_state (dirty files, commits
// ahead, a decision per file) before it changes anything.

export const meta = {
  name: 'aa-lane',
  description: 'AA_Ecosys lane: implement in its own worktree, independent multi-lens review, fix pass',
  phases: [
    { title: 'Implement', detail: 'lane agent builds + tests in a worktree, commits locally' },
    { title: 'Review', detail: 'independent reviewers by lens' },
    { title: 'Fix', detail: 'apply blocking/major findings' },
  ],
}

// AA-1024 (lesson S252): args must be an object. A placeholder string ("__FROM_FILE__") reaches the script as one
// string and every field reads undefined (a JSON-encoded object string is parsed by the harness and is fine). .claude/hooks/lane_start_guard.py refuses it before the launch (and a
// plan.json that is not on args.session); this check is the backstop when the hook is not loaded.
if (typeof args !== 'object' || args === null || Array.isArray(args)) {
  throw new Error(`lane.js: args must be a JSON object (got ${args === null ? 'null' : typeof args}); pass it inline`)
}
for (const k of ['key', 'goal', 'session', 'date']) {
  if (!args[k] || typeof args[k] !== 'string') throw new Error(`lane.js: args.${k} is required (a string)`)
}
// AA-1137: tasks only with a spec, as a list of task ids.
if (args.tasks !== undefined && !args.spec) throw new Error('lane.js: args.tasks needs args.spec (the spec folder)')
if (args.spec !== undefined) {
  if (typeof args.spec !== 'string' || !args.spec.trim()) throw new Error('lane.js: args.spec must be a folder path (a string)')
  if (!Array.isArray(args.tasks) || args.tasks.length === 0 || !args.tasks.every(t => typeof t === 'string' && t.trim())) {
    throw new Error('lane.js: args.spec needs args.tasks, a non-empty list of task ids such as ["T1", "T2"]')
  }
}
const L = args
const SPEC = L.spec ? { dir: L.spec.trim(), tasks: L.tasks.map(t => t.trim()) } : null
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
  git -C <repo> fetch origin && git -C <repo> worktree add /home/nghiep/projects/AA-Ecosys/.tmp-session/wt/${slug}-${L.key}-<repo>[-<detail>] -b <branch> origin/main (<repo>: cis, booking, partner, tp, infra or root; the lane start guard looks for these names)
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
  A file that ALTERs an existing table, adds a policy/constraint to one or INSERTs config rows is contract, not expand: run the app's
  migration preflight (Booking/Partner .github/scripts/migration_preflight.py with --infra-tools) before returning; contract = MIG-4 (a contract file has NO '-- migrate:' directive line; 'contract' is not a directive)
  (a migration-only PR without the readiness raise, then the code PR). Reserved numbers must be renumbered to owner main max + 1.
  On Dev a contract file is applied by Infra Migration Apply once every job table is idle (root ADR 0017a): its live_step is
  "the migration-apply run shows <owner>/<file> applied (class contract)", never a DB Migrate dispatch; only destructive
  files ('-- migrate: destructive', DRY RUN first) keep a DB Migrate live_step.
- Several migrations of one owner in this lane: consecutive numbers in ONE migration-only PR (or one PR per file, listed in
  number order in prs[] with "batch: <owner> <first>-<last>" in pr_body), so the orchestrator ships the wave's migrations of
  one owner as one batch (one copy + one Migration Apply run), never one at a time.
- Before returning, run the checks CI runs on your diff, not only unit tests (each red CI round costs the orchestrator a queue cycle):
  the app migration preflight with --infra-tools when a migration changed; the integration tests of every touched module on local
  Postgres (AA-CIS-App: scripts/pre-push.sh --integration in the worktree after the last commit; it runs them on a throwaway
  Postgres and writes the stamp the pre-push hook requires, so the orchestrator's push is refused without it); the repo's
  scripts/pre-push.sh (fast mode, what the hook runs at push; return its summary in tests); and a gitleaks scan of your commits: download gitleaks v8.30.1 (the CI pin) once into <scratchpad>/${L.key}-gitleaks/
  from github.com/gitleaks/gitleaks/releases (linux_x64 tar.gz, verify it against the release checksums file), then in each
  worktree: gitleaks git --log-opts="origin/main..HEAD" --config .gitleaks.toml --redact (root: origin/master; no .gitleaks.toml =
  no --config). A finding means rewrite the local branch before returning: git fetch, then git reset --soft $(git merge-base HEAD origin/main)
  and recommit (never reset --soft to a bare origin/main ref: a stale or newer ref makes the squash revert main); never "fix it in a later commit".
  Never silence a finding with an inline gitleaks allow comment (CI Secret Scan refuses a PR that adds one until a reviewer labels it): rewrite the line so
  the rule no longer matches (S278 Booking #235: WHERE key IN ('a_setting_name') instead of key = '...').
- Thresholds are settings, not literals (tech lead S279): every new threshold, limit, cap, floor, ceiling, quota, budget, retry/attempt limit
  or retention window you add must be read from the app's admin-editable settings (administrator role, seeded default, audited), never a
  code literal, an env var or a registry YAML value alone. If the app has no settings mechanism for it yet, say so in notes_vi and in the
  PR body as a follow-up instead of inventing a new env var (S279 thresholds audit: docs/audits/2026-11-13-S279-session/thresholds-audit/).
- Test parameters are fixed values: never uuid.uuid4(), random or time at import inside @pytest.mark.parametrize or a module-level constant used
  there (pytest-xdist workers collect different ids and CI goes red). AA-CIS-App: run tests/unit/test_s276_parametrize_determinism_lint.py
  whenever you add or change a parametrize (S278: #1454 and #1456 both went red on it).
- Local tests never reach AWS: run every test command with the AWS config hidden, so an app import never prompts for MFA or picks up a live
  profile: env -u AWS_PROFILE AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null AWS_EC2_METADATA_DISABLED=true <test command>.
- Before returning, also run the registry / snapshot tests of every repo you touched (they fail when a list you extended is not updated
  everywhere): job kind lists and the job registry; route policy and role matrix snapshots; module classification; capacity lines;
  the CIS openapi.json snapshot; the gateway route snapshot; the CIS final-contract topology (every AI text write is a listed exit). Find them with git grep -l -iE 'snapshot|registry|topology|KINDS|role_matrix|
  classif|capacity' -- 'tests/**' and run the ones that import a module you changed.
- One PR per repo per wave: when two lanes of a wave touch the same files (implementation notes, a registry, a snapshot, a kind list),
  they ship as ONE PR in that repo; say so in pr_body ("joins lane <key>") instead of opening a second PR that goes DIRTY when the first
  merges. A wave ships ONE migration-only PR per owner (consecutive numbers), never one per lane.
- The orchestrator ships the whole wave with ONE tools/github/ship_wave.py call (independent PRs in parallel, only migration -> copy ->
  apply -> code chains in order). In pr_body state the chain: "chain: <owner>/<NNN> applied before this PR" for a code PR that needs a
  migration of this wave, "applies: <owner>/<NNN>[,...]" for a migration-only PR; nothing for an independent PR.
- A code PR that needs a migration of this wave (MIG-4 chain): its branch is created from origin/main in its own worktree, NOT
  stacked on the migration branch, and it must not contain the migration file (git diff --name-only origin/main...HEAD shows no
  migrations/*.sql of that chain); its pr_body lists "chain: <owner>/<NNN> applied before this PR". Local tests that need the new
  schema run from the migration worktree or apply the migration file to the local test DB first. A stacked branch keeps the
  migration commit after the migration PR squash-merges, so its Migration preflight goes red (ship_wave.py then merges main into
  it before the gate, but that costs a pre-push and a CI round).
- Lessons: report each lesson you hit in followups as "lesson: <principle> | guard: <test|hook|tool|ci|lane> <path> | pending | none: <why>"
  (skill/aa-lessons/SKILL.md section 3: a new lesson line needs a Guard field).
- When a change adds a field to a DB query or row shape, also run the integration tests that read it (local Postgres), not only unit tests.
  A migration that creates a table also needs its DM-7.1 retention row (root docs/architecture/data-standards/02-data-management.md):
  return that root PR too, merged before the Infra bot copy (its "Retention rows" check fails without it).
- AA-Partner: before returning, run the unit suite the way ci.yml does (pytest tests/unit with coverage, gate 90%); new modules need unit
  tests, not only integration tests, or the gate fails (TOTAL must stay >= 90.5%).
- CIS openapi.json: regenerate only with the fastapi/pydantic versions pinned in requirements.txt (the CI versions), never a different local venv.
- One model label containing "api" per line in code and tests (gitleaks generic-api-key scans every commit; a later fix commit does not clear it).
- Integration tests that sign in as cis_app: grant schema USAGE/SELECT temporarily in the test, name result columns ("AS ok") and read rows by column name.
- Keep docs/implementation-notes/<ISSUE>.md in the repo updated (Decisions / Changed / Tradeoffs / Should know); parallel lanes on one issue use <ISSUE>-<lane>.md.
- Docs impact (AA-1132, warn only, never a gate): before returning, in each worktree run
  python3 /home/nghiep/projects/AA-Ecosys/tools/docs/doc_impact.py check --repo <AA-CIS-App|AA-Booking|AA-Partner|AA-TripPlanner-Web|AA-CIS-Infra|AA-Ecosys> --base origin/main
  (root: origin/master). Update every OPEN page of the same repo in the same PR; a root page you did not change goes to followups as
  "docs: <page>: <what changed>"; put one "Docs-impact: updated-here | none: <reason>" line in pr_body. Generated blocks
  (<!-- gen:... -->) are never edited by hand: python3 tools/docs/gen_sections.py --write in a root worktree. Raise last_reviewed only
  with a "Verified: <what was checked against what>" line in pr_body.
- UI: kit components only (ADR 0016); never edit **/_kit/core/** outside apps/AA-CIS-App/frontend/app/_kit/core/; English UI copy; never show AA-xxx ids in UI text.
- Commit locally early and often, format: "feat|fix|chore|refactor|docs: description" then blank line, "Refs AA-xxx", blank line,
  "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>". Never "Fixes"/"Closes".
- pr_body: every issue id it names must be on its "Refs AA-<n>, ..." line (ids there may also appear in prose; ids in file paths
  are fine). Describe other issues' work in words: Linear links any other id and may move it to Done on merge (PR opener + pr-title.yml refuse it).
- No paid LLM/API calls; mock them in tests.
- If the worktree already exists with commits (a resumed lane), continue from its git status/log and implementation notes; do not start over.${L.resume ? `
- THIS IS A RESUMED LANE (resume: true). Before changing anything, fill resumed_state from each existing worktree of this lane:
  dirty_files (git status --porcelain), commits_ahead (git log --oneline origin/main..HEAD; root: origin/master), and decision_per_file
  ("<path>: keep | redo | drop - why") for every dirty file. Keep finished work; never reset or overwrite it to start over.` : ''}
- Write code like the surrounding code. Finish the slice completely; if something is truly blocked, say exactly what.
- Return one entry in prs[] per PR the orchestrator should open (in merge order), each with exact live_steps the orchestrator must run after merge
  (deploy checks, DB Migrate, curl checks with expected shape, screenshots). notes_vi: 3-6 lines in Vietnamese for the tech lead.`

// AA-1137: what the lane did per spec task (requirement ids, the tests and live steps that prove them).
const TRACE = {
  type: 'array',
  items: {
    type: 'object',
    properties: {
      task: { type: 'string' },
      requirements: { type: 'array', items: { type: 'string' } },
      tests: { type: 'array', items: { type: 'string' } },
      live_steps: { type: 'array', items: { type: 'string' } },
      status: { type: 'string', enum: ['done', 'partial', 'carried', 'dropped'] },
    },
    required: ['task', 'requirements', 'tests', 'live_steps', 'status'],
  },
}
const SPEC_BRIEF = SPEC ? `

SPEC (AA-1137): this lane implements ONLY tasks ${SPEC.tasks.join(', ')} of the spec ${SPEC.dir} (relative to the workspace root;
in your worktree when the spec lives in the repo you change). First print them with their requirements, verbatim:
  python3 /home/nghiep/projects/AA-Ecosys/tools/spec/trace_check.py show /home/nghiep/projects/AA-Ecosys/${SPEC.dir} --tasks ${SPEC.tasks.join(',')}
and read requirements.md (or bugfix.md), design.md and tasks.md of that folder. Build what those requirements say and nothing
outside them: a needed change outside the spec goes to followups as "spec: <what> (amend R<n>.<m> or a new task)", never into
the diff silently. Every requirement your tasks name gets the test or live step its Verify line names (a live step goes into
live_steps of the PR). When the spec lives in the repo you change, tick your finished tasks ([x]) in its tasks.md in the same
PR (an unfinished one: "[~] ... carried -> AA-<n> (reason)" or leave it open and say why); a spec of another repo (the root) is
ticked by the orchestrator: say so in followups. Then run trace_check.py check <spec folder> on the copy you changed (it
must report errors=0). Return trace[]: one entry per task {task, requirements[], tests[], live_steps[], status}.` : ''

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
    resumed_state: {
      type: 'object',
      properties: {
        dirty_files: { type: 'array', items: { type: 'string' } },
        commits_ahead: { type: 'array', items: { type: 'string' } },
        decision_per_file: { type: 'array', items: { type: 'string' } },
      },
      required: ['dirty_files', 'commits_ahead', 'decision_per_file'],
    },
  },
  required: ['ready', 'prs', 'summary', 'notes_vi'],
}
// AA-1024 G20: a resumed lane must report what it found before it acts (lesson: relaunched lanes redid work).
// AA-1137: a spec lane must return its trace.
const withTrace = schema => SPEC
  ? { ...schema, properties: { ...schema.properties, trace: TRACE }, required: [...schema.required, 'trace'] }
  : schema
const IMPL_RUN = withTrace(L.resume ? { ...IMPL, required: [...IMPL.required, 'resumed_state'] } : IMPL)
const FIX_RUN = withTrace(IMPL)

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
const impl = await agent(`${COMMON}\n\nLANE ${L.key}: ${L.goal}${SPEC_BRIEF}`, { label: `impl:${L.key}`, phase: 'Implement', schema: IMPL_RUN })
if (!impl || !impl.ready || !impl.prs || impl.prs.length === 0) {
  return { lane: L.key, impl, reviews: [], fix: null }
}

const prList = impl.prs.map(p => `- ${p.repo} worktree ${p.worktree} branch ${p.branch} (base ${p.base || 'origin/main'})`).join('\n')
const SPEC_LENS = SPEC
  ? `spec (tasks ${SPEC.tasks.join(', ')} of ${SPEC.dir}: every requirement those tasks name has the test or live step its Verify line asks for, in the diff or in live_steps; no behaviour outside the spec; tasks.md ticks match the work; trace_check.py check passes on the spec; the lane trace below is true)`
  : null
const lenses = [...(L.lenses || [
  'correctness + spec fit (does it do what the Linear issue / plan asked, edge cases, tests meaningful)',
  'security + data safety (auth/permissions, RLS/tenant isolation, migrations safe to auto-apply, secrets, no account IDs in public repos)',
])]
if (SPEC_LENS && !lenses.some(l => /^spec\b/.test(l))) lenses.push(SPEC_LENS)
const traceNote = SPEC ? `\nLane trace (spec ${SPEC.dir}): ${JSON.stringify(impl.trace || [])}` : ''

phase('Review')
const reviews = (await parallel(lenses.map((lens, i) => () => agent(
  `YOUR ONLY JOB is an independent review for AA_Ecosys session ${S}, lens: ${lens}.
First confirm each worktree exists and has commits beyond its base; if not, return verdict "changes" with one blocking finding saying so.
Review ONLY the diff of these local branches against their base (git -C <worktree> diff <base>...HEAD); read surrounding code as needed.
${prList}
Context of the lane goal: ${L.goal}${traceNote}
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
Return the full updated prs[] (same schema)${SPEC ? ' and the full updated trace[]' : ''} with ready=true unless something is truly blocked.${SPEC_BRIEF}`, { label: `fix:${L.key}`, phase: 'Fix', schema: FIX_RUN })
}
return { lane: L.key, impl, reviews, fix }
