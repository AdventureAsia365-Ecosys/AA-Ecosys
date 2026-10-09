#!/usr/bin/env bash
# Run one Kiro task headless and capture EVERYTHING for Claude Code to review.
#
# usage: kiro-run.sh <task-id> <workdir>
#   <task-id>  e.g. aa-735-nac5  (brief must exist at .tmp-session/kiro/<task-id>/brief.md)
#   <workdir>  the repo (or worktree) Kiro works in, already on the task branch
#
# Output in /home/nghiep/projects/AA-Ecosys/.tmp-session/kiro/<task-id>/:
#   run.log        Kiro's console output (ANSI stripped copy in run.clean.log) — names commands only
#   session.jsonl  kiro-cli's own session record (every tool call + full result)
#   transcript.md  session.jsonl rendered, compact: commands with their real output (file reads/writes
#                  as path only — contents are in the repo / diff.patch)
#   checks.md      mechanical checks over the whole session (kiro_check.py) — read first
#   result.md      Kiro's own report (written by Kiro, per the brief)
#   diff.patch     full diff vs the base commit (committed + uncommitted)
#   diff_stat.txt  same, --stat
#   commits.txt    commits Kiro made
#   git_status.txt uncommitted files left behind
#   meta.txt       branch, base sha, start/end time, exit code
set -uo pipefail

TASK="${1:?task-id required}"
WORKDIR="${2:?workdir required}"
ROOT=/home/nghiep/projects/AA-Ecosys
OUT="$ROOT/.tmp-session/kiro/$TASK"
KIRO="$HOME/.local/bin/kiro-cli"
AGENT_SRC="$ROOT/.kiro/agents/aa-worker.json"

[ -f "$OUT/brief.md" ] || { echo "missing $OUT/brief.md" >&2; exit 2; }
[ -x "$KIRO" ] || { echo "kiro-cli not installed at $KIRO" >&2; exit 2; }

# The agent lives in the root repo; kiro-cli finds local agents only from their own directory,
# and app repos are separate checkouts — so expose it globally via a symlink.
mkdir -p "$HOME/.kiro/agents"
ln -sf "$AGENT_SRC" "$HOME/.kiro/agents/aa-worker.json"

cd "$WORKDIR" || exit 2
BRANCH=$(git rev-parse --abbrev-ref HEAD)
case "$BRANCH" in main|master) echo "refusing to run on $BRANCH — create the task branch first" >&2; exit 2;; esac
BASE=$(git rev-parse HEAD)
START=$(date -u +%FT%TZ)
# Kiro credits used so far this period (for the per-task cost line in meta.txt).
credits() { (cd /home/nghiep/projects/AA-Ecosys && timeout 90 "$KIRO" chat --no-interactive --trust-tools= "/usage" 2>&1) \
  | sed -r 's/\x1B\[[0-9;?]*[A-Za-z]//g' | sed -nE 's/.*Credits \(([0-9.]+) of.*/\1/p' | head -1; }
CREDITS_BEFORE=$(credits)

PROMPT="Read and follow the task brief at $OUT/brief.md exactly. Work in $WORKDIR on branch $BRANCH. When done (or blocked), write your report to $OUT/result.md with the sections the brief requires."

"$KIRO" chat --no-interactive --agent aa-worker --trust-tools=fs_read,fs_write,execute_bash \
  "$PROMPT" > "$OUT/run.log" 2>&1
RC=$?

sed -r 's/\x1B\[[0-9;?]*[A-Za-z]//g' "$OUT/run.log" > "$OUT/run.clean.log"

# The headless log shows only "Running: <cmd>". The full record — every tool call with its real
# stdout/stderr/exit status — is the session file kiro-cli writes; copy it and render it.
# Pick the session whose prompt names THIS brief (the /usage probes are sessions too).
SESSION=$(grep -l -F "$OUT/brief.md" $(find "$HOME/.kiro/sessions/cli" -name '*.jsonl' -newer "$OUT/brief.md" 2>/dev/null) \
  /dev/null 2>/dev/null | xargs -r ls -t 2>/dev/null | head -1)
if [ -n "$SESSION" ]; then
  cp "$SESSION" "$OUT/session.jsonl"
  python3 "$(dirname "$0")/kiro_transcript.py" "$OUT/session.jsonl" "$OUT/transcript.md"
fi
CREDITS_AFTER=$(credits)
git status --porcelain > "$OUT/git_status.txt"
git diff "$BASE" --stat > "$OUT/diff_stat.txt"
git diff "$BASE" > "$OUT/diff.patch"
git log --oneline "$BASE"..HEAD > "$OUT/commits.txt"
{
  echo "task=$TASK"; echo "workdir=$WORKDIR"; echo "branch=$BRANCH"; echo "base=$BASE"
  echo "head=$(git rev-parse HEAD)"; echo "started=$START"; echo "finished=$(date -u +%FT%TZ)"
  echo "exit_code=$RC"; echo "result_md=$([ -f "$OUT/result.md" ] && echo yes || echo MISSING)"
  echo "session=${SESSION:-MISSING}"; echo "transcript_md=$([ -f "$OUT/transcript.md" ] && echo yes || echo MISSING)"
  echo "kiro_credits_before=${CREDITS_BEFORE:-?}"; echo "kiro_credits_after=${CREDITS_AFTER:-?}"
  awk -v a="${CREDITS_BEFORE:-0}" -v b="${CREDITS_AFTER:-0}" 'BEGIN{printf "kiro_credits_task=%.2f\n", b-a}'
} > "$OUT/meta.txt"
python3 "$(dirname "$0")/kiro_check.py" "$OUT" >> "$OUT/meta.txt"
cat "$OUT/meta.txt"
exit $RC
