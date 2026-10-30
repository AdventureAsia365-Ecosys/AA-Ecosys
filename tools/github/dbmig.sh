#!/usr/bin/env bash
# Dispatch the AA-CIS-Infra DB Migrate workflow for one migration file and wait for it.
#
#   tools/github/dbmig.sh <owner>/<file.sql | NNN> <check|apply>
#     e.g. tools/github/dbmig.sh crm/027 check   (NNN resolves to the file on Infra main)
#
# Prints run id, conclusion and the key log lines (ran as, busy/idle, wave, applied). Exit 0 only on success;
# 2 = dispatch failed or the run never appeared; 1 = run not green. Wait limit: DBMIG_TIMEOUT seconds (default 1500).
# Orchestrator only (the subagent hook blocks `gh workflow run`); dispatches through the aa-agent App (as-app.sh).
# Holds no secrets. What the workflow checks and outputs: docs/ops/runbooks/db-migrate.md.
set -u
ROOT=/home/nghiep/projects/AA-Ecosys
R=AdventureAsia365-Ecosys/AA-CIS-Infra
MIG=${1:?usage: dbmig.sh <owner>/<file.sql|NNN> <check|apply>}; MODE=${2:?mode check|apply}
case $MODE in check|apply) ;; *) echo "mode must be check or apply"; exit 2 ;; esac
T="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/as-app.sh"

if [[ $MIG != *.sql ]]; then
  git -C "$ROOT/infra/AA-CIS-Infra" fetch -q origin
  F=$(git -C "$ROOT/infra/AA-CIS-Infra" ls-tree --name-only origin/main "db/migrations/${MIG%%/*}/" | grep "/${MIG##*/}_" | head -1)
  [ -n "$F" ] || { echo "no file $MIG on Infra main"; exit 2; }
  MIG=${F#db/migrations/}
fi

last() { gh run list -R "$R" -w db-migrate.yml -L 1 --json databaseId -q '.[0].databaseId'; }
before=$(last)
"$T" --repos AA-CIS-Infra -- gh workflow run db-migrate.yml -R "$R" --ref main -f migration="$MIG" -f environment=dev -f mode="$MODE" >/dev/null 2>&1 \
  || { echo "dispatch failed"; exit 2; }
rid=$before
for _ in $(seq 1 30); do sleep 5; rid=$(last); [ "$rid" != "$before" ] && break; done
[ "$rid" != "$before" ] || { echo "run did not appear"; exit 2; }

timeout "${DBMIG_TIMEOUT:-1500}" gh run watch "$rid" -R "$R" >/dev/null 2>&1
c=$(gh run view "$rid" -R "$R" --json conclusion -q .conclusion)
echo "DBMIG $MODE $MIG run=$rid conclusion=${c:-still running}"
gh run view "$rid" -R "$R" --log 2>/dev/null | grep -i -E "ran as|login|busy|idle|wave|applied|already|NOTICE|error|refus" \
  | grep -v "##\[group" | cut -c1-260 | head -25
[ "$c" = success ]
