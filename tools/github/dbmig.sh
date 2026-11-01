#!/usr/bin/env bash
# Dispatch the AA-CIS-Infra DB Migrate workflow for one migration file already on Infra main and wait for THAT run.
#
#   tools/github/dbmig.sh <owner>/<file.sql | NNN> <check|apply>
#     e.g. tools/github/dbmig.sh crm/027 check   (NNN resolves to the file on Infra main)
#
# Thin wrapper over ship_copy_apply.py --no-copy (AA-1032): the run is identified as the one this dispatch created
# (run title "DB Migrate <mode> <owner>/<file>", local lock), never "the latest run" (S263 bug). Prints run id,
# conclusion, the key log lines (ran as, busy/idle, wave, applied) and, after an apply, the owner app's readiness.
# Exit 0 only on success; 2 = dispatch failed or the run never appeared; 1 = run not green (or key not registered);
# 5 = still running after DBMIG_TIMEOUT seconds (default 1500).
# For a fresh migration (copy PR not merged yet) use ship_copy_apply.py without --no-copy.
# Orchestrator only (the subagent hook blocks `gh workflow run`); dispatches through the aa-agent App (as-app.sh).
# Holds no secrets. What the workflow checks and outputs: docs/ops/runbooks/db-migrate.md.
set -u
MIG=${1:?usage: dbmig.sh <owner>/<file.sql|NNN> <check|apply>}; MODE=${2:?mode check|apply}
case $MODE in check|apply) ;; *) echo "mode must be check or apply"; exit 2 ;; esac
case $MIG in */*) ;; *) echo "usage: dbmig.sh <owner>/<file.sql|NNN> <check|apply>"; exit 2 ;; esac
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$here/ship_copy_apply.py" "${MIG%%/*}" "${MIG#*/}" --no-copy --mode "$MODE" --run-timeout "${DBMIG_TIMEOUT:-1500}"
