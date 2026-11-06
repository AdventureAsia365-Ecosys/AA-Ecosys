# AA-1024: lessons become machine guards (lane l21-guards-root, S271)

The tech lead asked in S271 for machine guards instead of more lesson lines, because the same mistakes kept coming
back. The design and the critique came from the S271 lessons-guards audit (guards G1, G2, G4, G5, G12 and G22, plus
the critic's weak and missing lists). This lane built them in the root repo and in `.claude/hooks`.

## Decisions

- **One Bash hook with a rule table** (`.claude/hooks/aa_shell_guard.py`, rules PKILL-1, ZSH-1, ENV-1, SHIP-1,
  RAM-1). A small shell lexer blanks quoted text and drops comments and heredoc bodies, so no rule fires on text that is
  only an argument (`grep 'pkill -f' x`). The bodies of `bash -c '...'` and `bash <<EOF` are read again, as bash.
- **PKILL-1** checks only code that sits on the calling shell's command line: the command itself, `bash -c` bodies and
  bash heredoc bodies. A script file run by path is not checked, because its command line is `bash <path>` and a
  `pgrep -f <other script>` inside it does not match itself. The first replay version did check scripts, and the 2
  legitimate waits it flagged were the reason for this change.
- **ZSH-1** applies only at the zsh level (the Bash tool runs zsh; the snapshot's `setopt` does not turn word splitting
  on, checked live). It lets these pass: zsh arrays (`A=(...)`, `typeset -a`, `read -A`), zsh's special arrays, and a
  variable that is only ever set to one bare word in the same command (replay: 4 harmless hits). The rule leaves alone
  `[ \< ]` and unquoted `?` URLs, and so do the other rules (not in scope).
- **SHIP-1** refuses: a raw `gh pr merge` in any form (plain `gh`, through `as-app.sh --`, `xargs` or `bash -c`; only
  `--disable-auto` passes); `mergeq.sh` run by hand without `--dequeue`; `ship_merge.py` in a shell loop or run twice in
  one command; and running or sourcing a `.tmp-session` or scratchpad script that merges. It reads the script from disk,
  skips `.tmp-session/wt/**` because worktrees hold the tools themselves, and does not count read-only commands such as
  `cat` or `grep`. `ship_wave.py`, `ship_merge.py` with all targets, `ship_train.py` and `ship_copy_apply.py` all pass.
- **The choke point lives in the tools, not only in the hook** (critic G1): `as-app.sh` refuses `gh pr merge` unless
  `AA_SHIP_GATED` is set. Only `ship_merge.merge_one` sets it, after its gate. A hand merge that bypasses the hook (for
  example, from a terminal script) also fails. `train-lib.sh waitcopy` now merges through `ship_merge.py`.
- **ship_wave.py** reuses `ship_merge.merge_one` (one worker per PR, a lock per non-queue repo) and calls
  `ship_copy_apply.main` for the chains. Target syntax: `>apply:<owner>/<NNN>,...` marks a migration-only PR;
  `@after=<owner>/<NNN>,...` holds a code PR until its migrations are applied. An owner's numbers run in order, one
  batch per owner. `--wait-deploy` waits once per app (CIS, Booking, Partner), using a GitHub compare that checks the
  running `git_sha` contains every merge of the wave. A docs-only merge that never deploys times out with exit 5 and
  says why.
- **RAM-1**: a heavy command is refused when MemAvailable is under 2 GiB, or under 4 GiB while 3 or more heavy processes
  run. Heavy commands: next build, npm ci/build, playwright, vitest/jest, tsc, docker build, a pytest run of a directory
  or with `-n`, and UAT `node *.cjs` scenarios. The rule reads `/proc` directly (never `pgrep -f`) and names the heavy
  and top processes. `AA_RAM_OVERRIDE=1` overrides it and the override is logged. A pytest run of a single file is not
  heavy.
- **G12 is a hook, not a check inside lane.js**: a workflow script cannot read files. The hook is a PreToolUse matcher
  on `Workflow`. It refuses a `tools/workflows/lane.js` launch in 3 cases: plan.json `session` differs from
  `args.session`; the goal's first AA id is in plan.json with a slot that does not name the session; or args are
  missing or are a non-JSON string. A JSON-encoded object string passes, because the harness parses it (replay: 191
  launches did this and ran). `plan_gate: "skip: <reason>"` lets a hotfix through and is logged. lane.js also checks
  its args, as a backstop for when the hook is not loaded.
- **Lessons lint checks only new or changed lines** (`--base`). The backfill is `skill/aa-lessons/guards.md`: 105 audit
  lines, each with a guard checked on its owner's `main`/`master`, plus 5 lines that this lane's guards now block.
  Every section that lost lines keeps a pointer line to that file.

## Changed (vs the plan)

- Dropped, as the critic advised: WT-1 (worktree path), BG-1 (silent background), TF-1 (terraform apply off main), and
  the `.tmp-session/<S>-tracker-published` stamp (it can be written by hand; this needs a PostToolUse hook on the
  Artifact publish, follow-up).
- `pending` accepts `AA-<n>` as well as `GRD-<n>`, because no GRD rows exist in `docs/backlog/README.md` yet. Either
  id must appear in the backlog README or in plan.json.
- The bare-zsh fix (run the Bash tool under bash) was not done: it would change the tech lead's shell environment
  (nvm PATH, GitHub MCP token from `~/.zshrc`). ZSH-1 covers the two forms that caused the incidents.
- lane.js: an args check; the rules (a) one PR per repo per wave and one migration-only PR per owner, (b) the
  AWS-hidden local test env, (c) the registry/snapshot test list; the wave ships with one `ship_wave.py` call;
  lessons are reported with a guard. The `reset --soft` advice now uses `$(git merge-base HEAD origin/main)` after a
  fetch (lesson: Infra #380).
- The steering file `.kiro/steering/session-workflow.md` now says `ship_merge.py root#<n>` instead of the raw
  `gh pr merge` the hook refuses. It also covers the merge-queue line and adds `ship_wave.py` for waves.

## Tradeoffs

- SHIP-1 refuses forms that were the normal practice in past sessions. Of 35,477 distinct past Bash commands, it would
  refuse 2,131: 1,186 raw `gh pr merge`, 370 hand-run `mergeq.sh`, about 550 hand-written ship scripts, 18 loops and 5
  doubles. That is the intended cut-over. The sampled review found no misread (every hit really merges or runs a merge
  script).
- RAM-1 checks memory only when a command starts, so 3 lanes can still pass the check together and then grow (critic).
  The rule that refuses when 3 heavy processes run narrows that window. A cgroup or flock slot wrapper would close it,
  as a follow-up.
- Static reading: a command built at run time (eval, a program name kept in a variable) is not seen.

## Should know

- **Replay** (`python3 .claude/hooks/replay_shell_guard.py`, read-only over the 64 transcripts, 35,477 distinct
  commands):

  | Rule | Hits | What they are |
  |---|---|---|
  | PKILL-1 | 58 | All self-matching: the Bash tool's zsh carries the whole command in its own command line, checked live |
  | ZSH-1 | 131 | 89 are `set -- $x` on a loop item, plus vars from `$(...)` and quoted lists; all unsplit in zsh, checked live |
  | ENV-1 | 71 | All `export $(aws configure export-credentials ...)`, the S244 form |
  | SHIP-1 | 2,131 | See Tradeoffs |
  | RAM-1 | 480 | Heavy commands; refused only while memory is low |

  After the two fixes above (scripts dropped from PKILL-1, one-word variables allowed in ZSH-1), the sampled review
  found 0 false positives.
- **G12 on today's plan.json**: 10 of the 52 S271 lane launches would have been refused, because AA-1024, AA-855 and
  AA-1004 were not slotted for S271. That is the drift the guard is for. Move their slots before the next lane.
- Hooks need `"$CLAUDE_PROJECT_DIR"/.claude/hooks/*.sh` to be executable. `test_settings_hooks.py` checks that every
  registered hook exists, is executable and has a test.
- The `Workflow` matcher assumes that PreToolUse hooks see the Workflow tool under that name (INFERRED from the
  transcripts, where tool_use name is `Workflow` and input is `{scriptPath, args}`). Verify it once with a dry launch
  whose args carry the wrong session.
