# S271 — Biến bài học thành guard (07/11/2026)

Tác nhân: Claude Code. Rà toàn bộ `skill/aa-lessons/lessons.md` (chỉ đọc, 0 USD): dòng nào đã có guard tự động, dòng nào lặp lại, thiết kế guard cho từng dòng guard được. Dữ liệu đầy đủ: `lessons-guards.json`.

## Số liệu

- prose_only_judgement: 50
- partly_guarded: 138
- guardable_not_guarded: 108
- guarded: 122
- obsolete: 5

## Lỗi lặp lại nhiều nhất

- **9×** Shipping by hand-written serial merge/deploy scripts instead of the ship tools (serial queue use, BEHIND/DIRTY waits) (S222, S242, S248, S250, S252, S257, S260, S263)
- **7×** WSL VM out of memory from too many parallel lanes/builds (kills Claude Code, workflows, background tasks) (S237, S248, S251, S252, S261)
- **10×** ECS exec stdout cut silently over SSM (EOF), even after ecsx.sh existed (S235, S237, S240, S245, S248, S251, S253, S256)
- **14×** zsh does not split multi-word variables / glob ? / string compare (silent wrong loops) (S236, S238, S240, S241, S243, S247, S255, S261)
- **13×** pkill -f / pgrep -f / ps|grep+kill kills its own shell (exit 144) or matches forever (S249, S250, S252, S253, S254, S262, S263, S264)
- **6×** New FK/CHECK/grant breaks old migration replay test (test_aa1002_migration_304 LATER list) (S259, S260, S264, S265)
- **6×** Green locally, red on CI; fixed tests pushed without a local rerun; generated files built with the wrong venv (S247, S252, S253, S260, S271)
- **5×** Migration number collision / renumber misses (reserved numbers, \b regex, lanes reserving for others) (S246, S259, S260, S265, S266)
- **5×** Concurrent Terraform plans race the S3 state lock (S243, S248, S256, S265, S266)
- **4×** Issue moved to Done wrongly (Linear auto-close from PR text/deploy, or Done before Done-when) (S233, S244, S246)
- **3×** max_tokens truncation hard-coded per call site (now closed by code) (S246, S270, S271)
- **6×** Repeats appended to the old lesson line instead of being turned into a guard (meta-cause of every family above) (S254, S261, S263, S264, S265, S271)
- **10×** 5-hour usage limit / Claude crash kills lanes mid-way (external, recovery only) (S251, S254, S255, S257, S260, S262, S266, S267)
- **5×** Stating status/costs from memory, and stopping to ask on reversible steps (communication judgement) (S228, S248, S249, S261, S263)
- **4×** gitleaks false positives on key/token-named values (one red CI round each) (S248, S253, S255, S261)
- **2×** Master plan / Phiên tab not updated before lanes open (S264, S271)
- **2×** Worktree created at a relative path inside a child repo (S246, S247)
- **2×** Playwright jobs on ubuntu-latest broke when GitHub moved to 26.04 (S252, S253)

## Tóm tắt cho tech lead

Anh nói đúng: ghi bài học không cải thiện gì. Lỗi nằm ở cách làm, không phải ở người ghi. Bài học chỉ là chữ, mà một lỗi lặp lại thì cứ được ghi thêm vào dòng cũ thay vì biến thành thứ chặn được bằng máy.

Bằng chứng: lỗi xếp PR tuần tự lặp lại 9 phiên, với 48 script ship viết tay. Dù skill đã ghi đúng, script viết tay vẫn đi vòng qua tool. Lỗi pkill tự giết mình lặp lại 13 lần, zsh 14 lần, đầy RAM 7 lần, output ECS exec bị cắt 10 lần.

Ngược lại, lỗi max_tokens được biến thành test CI ngay trong phiên và không lặp lại nữa. Đó là mẫu cần làm theo.

Tôi đề xuất 22 guard, chặn ngay lúc sắp làm sai, xếp theo thứ tự:
- tool ship nhận cả một đợt PR, chạy song song và tự xếp chuỗi migration; kèm hook chặn script merge viết tay;
- một hook shell chặn pkill -f, vòng lặp zsh, worktree đường tương đối, `export $(...)`;
- hook kiểm RAM trước khi build/test hay mở lane;
- bật pre-push đã có sẵn mà chưa cài ở repo nào, và thêm chạy test integration;
- lint ORDER BY uuid, quét danh sách LATER của test 304, thêm concurrency cho Terraform plan.

Đổi quy trình: mỗi bài học phải có trường "Guard:", ghi tên test/hook/tool hoặc "none: lý do". Docs lint báo đỏ khi thiếu. Lỗi lặp lại thì phải làm guard ngay trong phiên hoặc xếp vào phiên sau, không được gộp vào dòng cũ. Mỗi phiên làm ít nhất 1 guard. Quét hằng tuần để xoá các dòng đã có guard.

Có khoảng 107 dòng trong lessons.md đã có guard thật, xoá được ngay. Không chuyển hai bài học chờ số 4 và 5 vào lessons.md vì đã có guard; số 6 trùng dòng 285.

## Guard đề xuất

| # | Guard | Cơ chế | Repo | Cỡ |
|---|---|---|---|---|
| G1 | ship-wave tool + ship-path hook rule (serial merge scripts) | tool default/refusal + claude hook | AA-Ecosys (root) | M (wave mode ~150 lines + test |
| G2 | aa_shell_guard PreToolUse hook (pkill -f, zsh splitting, worktree path, export $(), silent background, terraform apply off main) | claude hook | AA-Ecosys (root) | M (~200 lines + ~60 test cases |
| G3 | raw ECS exec refusal + ecsx hardening | claude hook + tool default | AA-Ecosys (root) | S-M |
| G4 | RAM guard for heavy commands and lane launches | claude hook | AA-Ecosys (root) | S |
| G5 | Hook tests in root CI | CI test/lint | AA-Ecosys (root) | S |
| G6 | Pre-push actually installed + integration mode + pinned-venv refusals | tool default/refusal + CI-equivalent loc | AA-CIS-App, AA-Booking, AA-Partner, AA-T | M |
| G7 | No ORDER BY uuid id in DB tests (lint) | CI test/lint | AA-CIS-App (copies in AA-Booking, AA-Par | S |
| G8 | Migration-304 LATER scanner + nightly random-order integration run | CI test/lint + scheduled CI job | AA-CIS-App | S + S |
| G9 | Terraform plan concurrency + lock timeout | CI config + workflow test | AA-CIS-Infra | S |
| G10 | Migration preflight: dangling old-number references + TripPlanner preflight | CI test/lint | AA-CIS-App, AA-Booking, AA-Partner, AA-T | S |
| G11 | PR text guard + Linear Done-evidence audit | CI test/lint + session-end checker scrip | root (tool + workflow), AA-CIS-App and A | S + M |
| G12 | Master plan gate before any lane starts | claude hook | AA-Ecosys (root) | S |
| G13 | IAM trust inventory tool | skill step + checker script | AA-CIS-Infra (+ root docs-lint rule) | S-M |
| G14 | gitleaks before every orchestrator push + Secret Scan history status | tool default/refusal | root tools/github, session status | S |
| G15 | Workflow lint per repo (Playwright runner pin, vars.*ARN, actionlint, tracked lockfile) | CI test/lint | AA-CIS-App, AA-Booking, AA-Partner, AA-T | S |
| G16 | Integration conftest: replay failures are errors | CI test/lint | AA-CIS-App | S |
| G17 | Wave stop flags enforced | tool default/refusal | AA-CIS-App | S |
| G18 | One cost source: spend_by_stage + cost_estimate | skill step + checker script | AA-Ecosys (root tools/llm, runs via ecsx | M |
| G19 | Stop hook: open reversible work + question | claude hook | AA-Ecosys (root) | S |
| G20 | Lane resume state (external crash / usage limit) | lane template check | AA-Ecosys (root) | S |
| G21 | PII hook --check mode + safe DRY RUN snippet | tool default/refusal | AA-Ecosys (root) | S |
| G22 | lessons.md lint (Guard field) + guarded-line sweep | CI test/lint | AA-Ecosys (root) | M |

Đang làm trong S271: lane l21 (root: G1, G2 thu hẹp, G4, G5, G12, G22 + quy tắc lane), l22 (app: G6, G7, G8, G10, G16), l23 (Infra: G9, G13, G15). Còn lại → S272.

## Thay đổi quy trình

Line-number convention for this answer: in lesson_lines, a negative number is a line of .tmp-session/S271-lessons-pending.md (-7 is pending line 7, -8 is pending line 8, -9 is pending line 9). Positive numbers are skill/aa-lessons/lessons.md.

The process changes in six ways. VERIFIED where it describes current state; the new rules are proposals.

1. **New line template.** In skill/aa-lessons/SKILL.md §3 the line becomes: `- **<principle>** — <symptom → cause> (S<nnn>, AA-xxx). Guard: <test|hook|tool|ci|lane> <path or hook RULE-ID> | Guard: pending GRD-<n> | Guard: none: <judgement|external|one-off> <why>.` Today 'Bắt bằng:' accepts prose such as 'aa-ship ghi MẶC ĐỊNH song song' (pending line 9). That is how the S257 serial-merge lesson repeated in S271. 'Bắt bằng' stays only as a detection hint.

2. **Lint.** tools/docs/check_lessons.py (G22) runs in docs-lint, which already triggers on skill/**. It fails when the Guard field is missing, when a guard target does not exist, when a `pending` guard has no GRD row in docs/backlog/README.md, and when a line cites two or more sessions but is marked `none` without a judgement/external reason. Its weekly schedule job runs `--sweep` and lists every line whose guard now exists as 'delete me'. The delete is a one-line root PR at the next session close, and the commit names the guard.

3. **A repeat triggers a guard, never a merged line.** Remove 'Trùng ý → sửa dòng đó (thêm bằng chứng, phiên lặp lại)' from SKILL.md §3 for guardable lines. In aa-session close (step 'Bài học'), a pending lesson that repeats an existing line must either land its guard in this session (the max_tokens model: three repeats, then a CI guard, then no more repeats) or get a GRD-n row slotted into the NEXT session in plan.json. The session block reports 'lessons: X new, Y guarded, Z deleted'.

4. **Guard budget.** Every session list carries at least one GRD item from the top of the recurrence ranking. Order: G1 ship-wave, G2 shell guard, G4 RAM, G5 hook CI, G6 pre-push, G8 304 scanner, G9 TF concurrency, G3 ecsx, then the rest.

5. **Hook rule IDs.** Workflow and shell mistakes go into one rule table (.claude/hooks/aa_shell_guard.py), each rule citing its lesson. Writing the rule replaces writing the line. Hook tests run in root CI (G5), so the guards themselves are guarded.

6. **Subagent results.** lane.js asks subagents to return lessons as {principle, guard_kind, guard_target_or_reason}, so the orchestrator can feed them to the lint unchanged.

Caveats:
- The delete list holds only lines classified guarded/obsolete with VERIFIED guards on main. Excluded on purpose: 23 (INFERRED), 206 (hand pushes are unguarded), 337 (#1352 not yet confirmed on main), 379 and 393 (TripPlanner has no preflight until G10), and 458 (Booking build is not a required check).
- Do not move pending lines 4 and 5 into lessons.md (already guarded). Pending line 6 duplicates 285, and pending line 3 duplicates 48.
- The Workflow/Agent tool names used as hook matchers, and a settings option to run the Bash tool under bash instead of zsh, are INFERRED. Check them before building G2, G4 and G12.

## Phản biện

- G2 WT-1 (worktree path): this rule would block almost every legitimate worktree creation, so it would be switched off within a day. VERIFIED: I ran the proposed regex over the 35,909 past Bash commands in ~/.claude/projects/-home-nghiep-projects-AA-Ecosys/*.jsonl. It refuses 554 of the 555 `git worktree add` commands. A flag (-q, -b <branch>, --detach) almost always comes right after `add`, and the lane path is usually the variable $W, which the hook sees unexpanded. The regex requires the literal path right after `add`. Fix: tokenise with shlex and skip the options. Better still, add a PostToolUse check of `git worktree list --porcelain` that flags any worktree outside .tmp-session/wt/.
- G2 BG-1 (silent background): the regex `>/dev/null 2>&1 &` also matches `>/dev/null 2>&1 &&`. VERIFIED: it matched 146 past commands, and only 24 of them really put a job in the background. The same `&&` form is in .tmp-session/S271/ship_w0.sh:11. The `(nohup|setsid).*>\s*/dev/null` form matches greedily across commands joined with &&: 27 hits, one of them a mkdir/cp chain. Fix: use `&(?!&)` and match within one simple command.
- G2 PKILL-1: the rule only refuses pgrep when its output feeds kill or xargs. It misses the self-matching wait loop `until/while ! pgrep -f <pattern>`, which is the S262 hang recorded in lessons.md:170. VERIFIED: 22 past commands use that form. The rule also never reads .tmp-session scripts, so a pkill -f inside a script passes.
- G2 ZSH-1: a regex heuristic is the weak fix here. VERIFIED: `set -- $var` occurs in 262 past commands (91 in bare zsh, 171 inside bash -c or a heredoc), and `for x in $VAR` in 70 (37 bare). The guard that removes the root cause is running the Bash tool under bash, so that should come first, not as an afterthought. Caveat (INFERRED): a shell override such as CLAUDE_CODE_SHELL must keep the environment that ~/.zshrc sets today (nvm PATH, the GitHub MCP token; memory kiro-env-snapshot, and the allow-list entry `export PATH="$HOME/.nvm/..."` in .claude/settings.json).
- G1 SHIP-1: the rule counts calls to mergeq.sh or `gh pr merge` in .tmp-session scripts. That does not detect serial shipping. VERIFIED bypasses: (a) .tmp-session/S271/train_l6.sh:12,20,25 calls the approved tool ship_merge.py three times in a row, with apply steps between, and the rule does not count it. (b) .tmp-session/S271/ship_cassette.sh:5 imports the merge function with `source <(sed ... ship_w0.sh)`. (c) Scripts in the scratchpad, in docs/audits/scripts-*/ or in Python are never read. VERIFIED false positive: .tmp-session/S271/ship_labelled.sh:5-11 is the correct parallel pattern (mergeq.sh in the background, then a loop over the non-queue repos) and would be refused. The plan also says 'tools/ is never matched', but worktrees live in .tmp-session/wt/**, so every lane's tools/github/*.sh is a .tmp-session file. Stronger guard: a choke point inside the tools. mergeq.sh, and `gh pr merge` through as-app.sh, refuse unless ship_merge.py set an env token (only --dequeue is exempt). Also refuse raw `gh pr merge` in the main session and drop the `Bash(gh pr merge:*)` allow entry (.claude/settings.json, the first allow entry). The hook should go live only after wave mode exists; otherwise it blocks today's legitimate migration chains.
- G3 ECS-1: the plan's S271 evidence is mis-cited. VERIFIED: .tmp-session/S271/ship_w0.sh:28 runs `aws ecs describe-services` (read-only), not execute-command, so ECS-1 would correctly not match it. The real raw-exec case is .tmp-session/S264/one.sh. The hook would also fight instructions loaded every session. VERIFIED: ~/.claude/CLAUDE.md calls raw `aws ecs execute-command` 'S3-MEDIATED ECS EXEC PATTERN (canonical — use every time)'; docs/ops/runbooks/ecs-exec-s3-mediated.md:113, skill/aa-cis-schema/references/ecs-exec.md:8,80 and skill/aa-cis-schema/SKILL.md:28 show the raw form; and settings.json allows `Bash(aws ecs *)`. Matching on mentions is noisy. VERIFIED: 63 of the 333 past commands that mention it are grep/cat/sed reads. The existing subagent hook already does this: it blocked this read-only audit twice, once for `cat mergeq.sh` and once for a grep containing 'gh pr merge'. INFERRED: part (c) needs the CI deploy role to have read access to the bronze bucket's scripts/out.
- G4 RAM-1: a check at command start races. Three lanes read MemAvailable at the same moment, all pass, and then grow together, and those are the incidents. The trigger list also misses recorded causes. VERIFIED: 95 past commands run UAT `node *.cjs` scenarios that launch Chromium, and lessons.md:160 names TTS model loads and a gitleaks mirror. Neither kind matches `next build|npm ci|playwright|vitest|pytest .*tests/integration|tsc --noEmit`. Stronger: N slot files taken with flock by a heavy-command wrapper that the hook requires, or a per-lane cgroup MemoryMax so the OOM kills the lane and not Claude Code. INFERRED: systemd is PID 1 here, but the user bus is unavailable inside the sandbox.
- G6 pre-push integration mode: VERIFIED: ship_open_prs.py:168 runs the push with timeout=300. An integration run inside pre-push (the conftest replays about 380 migrations on a temp Postgres) will hit that timeout, the push fails, and AA_PREPUSH_SKIP_INTEGRATION=1 becomes the default. Hand pushes (`as-app.sh ... git push --force-with-lease` in the settings.json allow-list) also skip validate(). Keep the hook fast; run integration in validate() with its own timeout. Installing hooksPath (G6 part 1) is the valuable part.
- G14 duplicates G6: VERIFIED: the pre-push.sh scripts of Booking, Partner, TripPlanner, Infra and root already run gitleaks; only apps/AA-CIS-App/scripts/pre-push.sh does not. core.hooksPath is empty in all six checkouts (VERIFIED). Installing the hooks covers the orchestrator's pushes, hand pushes included, for five repos. G14 inside validate() misses hand pushes. Better: add gitleaks to CIS pre-push.sh and drop the validate() copy.
- G8 304 LATER scanner: the trigger is too narrow. VERIFIED: in test_aa1002_migration_304.py:52-72, about half the LATER entries were added for ADD COLUMN or row changes, not for REFERENCES, ADD CONSTRAINT or GRANT: 337 (capability rows), 343 (re-set rows), 367 (probe-state columns), 376 (Anthropic rows). The proposed regex would miss them. Scan for any statement that names a table _undo drops. The nightly random-order run does not block merges, so it will be ignored the way the full-history Secret Scan was red three times on main without anyone noticing (lessons.md:197), unless session start shows it.
- G5 + G22 lessons/hook lint: VERIFIED: the root repo has no required check. Root PRs are merged with `gh pr merge <n> --squash` (session-workflow steering; skill/aa-ship/SKILL.md:36 'Infra và repo gốc không có required check'), so a red docs-lint does not block the lessons.md PR. Only ship_merge.py refuses red non-required checks (ship_merge.py:11-13). Fix: a root ruleset that requires docs-lint (free on a public repo), or root merges through ship_merge only. The G22 --sweep result goes to a weekly step summary nobody reads (the same failure as lessons.md:197). `Guard: none: judgement` passes for any line, and rule (5) 'guardable tag' is not defined, so the lint can be satisfied by writing 'none'.
- G11 PR text guard: this does not stop the recorded Done flip in lessons.md:63, where AA-847 went to Done 1 s after a DB Migrate apply with only `Refs` in the text. VERIFIED: ship_open_prs.py:122-123 already refuses issue ids in titles. Branch names carry the issue id (ship_train.py:5 `feat/aa-958-migration`). INFERRED: Linear links PRs by branch name and moves them through the team's Git automation. So the preventive guard is the Linear team workflow setting (no Done on merge or deploy). done_audit.py only detects after the fact.
- G12 plan gate: the stamp `.tmp-session/<S>-tracker-published` comes from a 'publish step', and the orchestrator can create it by hand, the same way it skips the prose step now. Have a PostToolUse hook on the Artifact publish write the stamp with the plan.json sha. Agent launches that do not go through lane.js carry no args.session and are not gated. VERIFIED: lane.js:9 requires session only for lane.js itself.
- G19 Stop hook: VERIFIED: checklists almost always have open items (S271 5, S269 5, S270 1 `- [ ]`). The hook would fire on most stops, and the only cheap way to silence it is to add a [blocked:] tag or tick the box. That trains tag-gaming, not finishing. Real questions from the tech lead also get bounced.
- G13 IAM trust inventory: one event (S271 only; pending line 6 duplicates lessons.md:285), so this is not a recurring family. The docs/audits keyword rule is bypassed by rewording. Low value compared with the families above; make it a skill step, not a lint.
- G7 ORDER BY uuid lint: it would have caught the S271 case. VERIFIED: tests/integration/test_s271_cut_rate_db.py:110 comment 'ORDER BY id made this test flaky'. It misses the sibling forms: `ORDER BY created_at` ties inside one transaction (now() is the same for every row), and fetchrow or LIMIT 1 with no ORDER BY at all. The lesson's own fix ('created_at + tiebreak') would pass the lint even without a tiebreak.
- (thiếu) Instructions that teach the mistake the hooks will block. Nothing checks that always-loaded instructions agree with the guards. VERIFIED: ~/.claude/CLAUDE.md (outside every repo, so only the tech lead can edit it) still prescribes raw `aws ecs execute-command` as 'canonical — use every time', as does the runbook (docs/ops/runbooks/ecs-exec-s3-mediated.md:113). tools/workflows/lane.js:62 tells lanes to 'reset --soft + recommit', the form lessons.md:105 warns about. Guard: export the shell-guard rule table and run it in docs-lint over code blocks in docs/, skill/, .claude/ and .kiro/. docs-lint already does this for backslash-continued AWS CLI (docs-lint.yml:5). Then ask the tech lead to edit the global CLAUDE.md by hand.
- (thiếu) Paid AWS services switched on without an explicit yes for that item (lessons.md:33, S255 GuardDuty about 15-20 USD/month, objected to and switched off; memories cost-advice-new-aws-services and paid-observability-hold). The plan has no guard. Proposed: a main-session hook rule refusing `aws guardduty create-detector|securityhub enable-security-hub|configservice put-configuration-recorder|inspector2 enable|macie2 enable-macie` (and the same in .tmp-session scripts), plus an Infra CI lint that refuses aws_guardduty_detector, aws_securityhub_account, aws_config_configuration_recorder, aws_inspector2_enabler, aws_macie2_account and new NAT gateways unless a `# cost-approved: <quote>` marker is present.
- (thiếu) Push while a rebase is still in progress (lessons.md:206, S257: only the first commit reached GitHub). The plan keeps line 206 off the delete list because 'hand pushes are unguarded', yet proposes no guard. Proposed: every repo's pre-push.sh refuses when `git rev-parse --git-path rebase-merge` or rebase-apply exists. With G6's hooksPath install this covers hand pushes too.
- (thiếu) Raw merges that skip ship_merge.py's gate on any red check. VERIFIED: .tmp-session/S271/ship_cassette.sh:11,17 and ship_labelled.sh:11 merge root and Infra PRs with a raw `as-app.sh -- gh pr merge`, and settings.json allows `Bash(gh pr merge:*)`. Root and Infra have no required checks (aa-ship SKILL.md:36), so a red check merges. Proposed: as-app.sh refuses `gh pr merge` unless ship_merge.py set its env token, plus a main-session hook rule.
- (thiếu) Waits without a timeout (lessons.md:104: `gh run watch` hung 21 min in S252 and the windows queued behind it). G1 only adds the DIRTY exit in mergeq.sh. There is no rule that `gh run watch` or `gh pr checks --watch` must run under `timeout`, in commands or in .tmp-session scripts.
- (thiếu) Results of scheduled or non-blocking checks that nobody reads (lessons.md:197: Secret Scan history red three times without anyone noticing). Several plan guards depend on them: the G8 nightly random-order run, the G22 weekly sweep, and the G14 history status. Only secret-scan gets a session-start line. Proposed: one session-start status step that lists the latest scheduled-run conclusion of every guard workflow across the 6 repos, red runs first, and fails the opening checklist while any is red.
- (thiếu) Squash from a stale base that silently reverts main (lessons.md:105, Infra #380 reverted #372-#378). This family is only half guarded: ship_merge.py:119-120 refuses deleted files, but a stale-base squash that changes lines in existing files passes. Proposed: validate() or pre-push refuses when the branch diff touches lines that origin/main changed after the branch's merge-base, that is, when `git diff origin/main...HEAD` and `git diff origin/main HEAD` disagree on files the branch's own commits never touched.
