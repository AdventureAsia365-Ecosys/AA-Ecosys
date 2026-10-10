# Task <task-id> — <AA-xxx> <one-line title>

## Contract
Implement Linear **<AA-xxx>** — read it first with `@linear/get_issue` (and `@linear/list_comments` for
decisions made in comments); its Scope, Done when and any Design / Decision section are the contract.
Linear is read-only for you — never try to write it.
<Then 1–3 lines for what the issue does not say: a decision Nghiệp made, file/function pointers, a known trap.>

## Repo / branch
<absolute repo path> on `<feat|fix|chore>/<aa-xxx>-<slug>` (already checked out by Claude Code).

## Read first
- `<repo>/CONTEXT.md`; `/home/nghiep/projects/AA-Ecosys/skill/aa-lessons/lessons.md` — section(s): <…>
- <file:line pointers that matter, if any>

## Files in scope
- `<path/or/glob relative to the repo>`

## Test commands
- `<local test / lint / build command>`
- `<…>`

## Standard rules (do not edit)
- No schema change, no new dependency, no secrets, unless the contract says so. Match the surrounding
  code style. Frontend: inline style + tokens (`A`/`K`, `alpha()`), dark theme safe (no hex/white
  literals in pages), no setState in useEffect. FastAPI: no helper between a decorator and its function.
- Commits on this branch only: `<type>: <description>` + blank line + `Refs <AA-xxx>`.
- **Loop until green, then report — do not stop at local tests:**
  1. Run the test commands above until green.
  2. `git push -u origin <branch>` (feature branch only — never main/master, never force).
  3. Wait for CI on the branch, checking once every ~4 min (no tight polling):
     `gh run list --branch <branch> --limit 10 --json name,status,conclusion,databaseId`.
     The `UI smoke (Playwright)` run starts when the Vercel preview is ready (frontend changes only).
  4. On a failed run: `gh run view <id> --log-failed | tail -120` — the smoke prints the failing page,
     the API body, and the offending elements (overflow / light surface). For visuals:
     `gh run download <id> -D /home/nghiep/projects/AA-Ecosys/.tmp-session/kiro/<task-id>/shots` and look
     at the screenshots of the pages you changed (desktop + mobile, light + dark).
  5. Fix → commit → push → back to 3. At most 3 push cycles; if still red, stop and report why.
- Do not open, merge or comment on PRs; Claude Code does that.

## Report
Write `/home/nghiep/projects/AA-Ecosys/.tmp-session/kiro/<task-id>/result.md` with sections:
`## Summary`, `## Files changed`, `## Commands run`, `## Test results` (verbatim pass/fail lines, incl.
the final CI run ids + conclusions), `## Screenshots checked` (which pages, what you saw),
`## Decisions not in the contract`, `## Open questions / risks`.
