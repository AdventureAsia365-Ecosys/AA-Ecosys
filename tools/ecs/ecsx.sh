#!/bin/bash
# Run a Python script inside a running app container over ECS exec and get ALL of its output back.
# Usage text: tools/ecs/ecsx.sh --help. Runbook: docs/ops/runbooks/ecs-exec-s3-mediated.md.
#
# Why: the SSM terminal of ECS exec drops long stdout and can end the process with it ("Cannot perform start
# session: EOF", lesson log S237 -> S256). The session only starts tools/ecs/ecsx_runner.py, which detaches and runs
# the script with cwd /app; the output comes back by one of two modes:
#   s3     (default for aa-cis-* services) the runner puts the output on the bronze bucket (scripts/out/); this side
#          waits for the .done marker, prints the output and removes the objects. Needs a task role that can write
#          the bucket: CIS only.
#   local  (default for every other service: Booking, CRM, S257) the output stays in /tmp of the container and
#          short exec calls read it back in byte ranges (tools/ecs/ecsx_local.py); the script reaches the container
#          through a presigned S3 GET or inline in the exec command.
# Orchestrator only (the subagent hook blocks ECS exec).
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: tools/ecs/ecsx.sh <script.py> [VAR=value ...]
       tools/ecs/ecsx.sh --resume <run id> [offset]     (local mode: read the output of a run that is still there)

Runs <script.py> with python3 in a running task of the service, cwd /app, /app on sys.path, and prints all of
its output; exits with the script's exit code. VAR=value pairs become the script's environment. The script reads
the container's own DATABASE_URL (CIS: cis_app, Booking: booking, CRM: crm_app). The pair
ECSX_SCRIPT_TIMEOUT=<seconds> sets how long the script may run in the container (default 3300, at most 10800).

Environment:
  ECSX_SERVICE        aa-cis-dev-api (default) | aa-cis-dev-worker | aa-booking-dev-api | aa-crm-dev-api
  ECSX_CONTAINER      container name; default "worker" for *-worker services, else "api" (the Booking and CRM
                      task definitions name their container "api", infra/AA-CIS-Infra/accounts/aa365/)
  ECSX_MODE           s3 | local; default s3 for aa-cis-* services, local for the others
  ECSX_TIMEOUT        seconds to wait for the result (default 900)
  ECSX_PROFILE        AWS profile (default aa365-admin)
  ECSX_OUT_DIR        where the local copy of the output goes (default .tmp-session/ecsx/<run id>.out)
  ECSX_START_WAIT     s3 mode: seconds to wait for the runner's heartbeat before starting a lost run once (30)

ECSX_SCRIPT_TIMEOUT longer than ECSX_TIMEOUT is refused (the result would never come back). A start the SSM session
lost is started again once (the runner claims the run id, so a script never runs twice). The output is printed and
also kept in .tmp-session/ecsx/<run id>.out.
 local mode only:
  ECSX_SHIP           auto (default: presigned S3 GET, inline if that fails) | s3 | inline
  ECSX_INLINE_CHUNK   base64 characters per inline exec command (default 2000)
  ECSX_READ_CHUNK     output bytes per chunk line (default 1024)
  ECSX_READ_LINES     chunk lines per read call (default 1)
  ECSX_KEEP=1         keep /tmp/ecsx-<id>.* in the container after a successful run

Examples:
  tools/ecs/ecsx.sh .tmp-session/check.py LIMIT=20
  ECSX_SERVICE=aa-booking-dev-api tools/ecs/ecsx.sh .tmp-session/bk_check.py
  ECSX_SERVICE=aa-crm-dev-api ECSX_SHIP=inline tools/ecs/ecsx.sh .tmp-session/crm_check.py
EOF
}

case ${1:-} in
  -h | --help) usage; exit 0 ;;
  "") usage >&2; exit 2 ;;
esac

P=(--profile "${ECSX_PROFILE:-aa365-admin}" --region us-west-1)
B=${ECSX_BUCKET:-aa-cis-bronze-005097885195}
SVC=${ECSX_SERVICE:-aa-cis-dev-api}
case $SVC in *-worker) dctr=worker ;; *) dctr=api ;; esac
CTR=${ECSX_CONTAINER:-$dctr}
case $SVC in aa-cis-*) dmode=s3 ;; *) dmode=local ;; esac
MODE=${ECSX_MODE:-$dmode}
WAIT=${ECSX_TIMEOUT:-900}
here=$(cd "$(dirname "$0")" && pwd)

[[ $MODE == s3 || $MODE == local ]] || { echo "ecsx: ECSX_MODE must be s3 or local (got $MODE)" >&2; exit 2; }
TASK=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name "$SVC" "${P[@]}" --query 'taskArns[0]' --output text)
[[ $TASK == arn:* ]] || { echo "ecsx: no running task for $SVC (got: $TASK)" >&2; exit 2; }

if [[ $1 == --resume ]]; then
  [[ $MODE == local ]] || { echo "ecsx: --resume is for the local mode" >&2; exit 2; }
  exec python3 "$here/ecsx_local.py" --task "$TASK" --container "$CTR" --id "${2:?usage: --resume <id> [offset]}" --resume "${3:-0}"
fi

script=$1; shift
[ -f "$script" ] || { echo "ecsx: no such script: $script" >&2; exit 2; }
for kv in "$@"; do [[ $kv =~ ^[A-Za-z_][A-Za-z0-9_]*=[A-Za-z0-9_.:,/@+-]*$ ]] || { echo "ecsx: bad VAR=value: $kv" >&2; exit 2; }; done
# AA-1024 G3 (lesson S260): a script allowed to run longer than this side waits never brings its result back.
for kv in "$@"; do
  if [[ $kv == ECSX_SCRIPT_TIMEOUT=* ]]; then
    st=${kv#*=}
    [[ $st =~ ^[0-9]+$ ]] || { echo "ecsx: ECSX_SCRIPT_TIMEOUT must be seconds (got $st)" >&2; exit 2; }
    # S272 review: a hung script blocks every CIS deploy until it ends; longer than 3 h is a one-off ECS task
    (( st <= 10800 )) || { echo "ecsx: ECSX_SCRIPT_TIMEOUT=$st is over the 10800 s cap (a hung script blocks every CIS deploy that long): run a long job as a one-off ECS task" >&2; exit 2; }
    (( st <= WAIT )) || { echo "ecsx: ECSX_SCRIPT_TIMEOUT=$st is longer than the wait (ECSX_TIMEOUT=$WAIT): set ECSX_TIMEOUT=$st (or more) too, or run a long job as a one-off ECS task" >&2; exit 2; }
  fi
done
# S278 lesson: ECSX_SCRIPT_TIMEOUT set in the environment is ignored (it is a VAR=value argument); two paid R1 runs
# were cut at the 3300 s default that way. Refuse instead of silently using the default.
if [[ -n ${ECSX_SCRIPT_TIMEOUT:-} ]] && ! printf '%s\n' "$@" | grep -q '^ECSX_SCRIPT_TIMEOUT='; then
  echo "ecsx: ECSX_SCRIPT_TIMEOUT is set in the environment, where it has no effect: pass it after the script path as ECSX_SCRIPT_TIMEOUT=$ECSX_SCRIPT_TIMEOUT" >&2; exit 2
fi
base=$(basename "$script" .py); base=${base//[^A-Za-z0-9_-]/_}
id=$(date -u +%Y%m%dT%H%M%S)-$$-$base

if [[ $MODE == local ]]; then
  exec python3 "$here/ecsx_local.py" --task "$TASK" --container "$CTR" --id "$id" "$script" "$@"
fi

aws s3 cp "$script" "s3://$B/scripts/ecsx/$id.py" "${P[@]}" --quiet
aws s3 cp "$here/ecsx_runner.py" "s3://$B/scripts/ecsx/$id.runner.py" "${P[@]}" --quiet
U1=$(aws s3 presign "s3://$B/scripts/ecsx/$id.py" "${P[@]}" --expires-in 600)
U2=$(aws s3 presign "s3://$B/scripts/ecsx/$id.runner.py" "${P[@]}" --expires-in 600)
OUT=scripts/out/$id.txt
# AA-1024 G3: the output is also kept locally (a cut terminal or a pipe into tail loses it, S267/S268).
LOCAL_DIR=${ECSX_OUT_DIR:-$here/../../.tmp-session/ecsx}
mkdir -p "$LOCAL_DIR"; LOCAL_OUT=$(cd "$LOCAL_DIR" && pwd)/$id.out
# The exec call itself can hang (the SSM session never closes): bound it; the runner is detached, so a cut session
# after the start is harmless. The runner claims the run id, so a second start of the same id never runs it twice.
start() {
  timeout 90 aws ecs execute-command --cluster aa-cis-dev-cluster --task "$TASK" --container "$CTR" --interactive --command "sh -c 'curl -sf \"$U1\" -o /tmp/$id.py && curl -sf \"$U2\" -o /tmp/$id.runner.py && $* python3 /tmp/$id.runner.py /tmp/$id.py $B $OUT'" "${P[@]}" 2>&1 | grep -q "ECSX_STARTED"
}
seen() { aws s3api head-object --bucket "$B" --key "$1" "${P[@]}" >/dev/null 2>&1; }
if ! start "$@"; then
  echo "ecsx: started (session output not seen, normal when SSM drops it); checking the heartbeat" >&2
  # The runner writes $OUT.running as soon as it runs (then every 30 s). None after ~30 s: the start was lost before
  # the runner detached (S269); start once more (the presigned URLs are still valid).
  t=0; until seen "$OUT.running" || seen "$OUT.done"; do
    sleep 3; t=$((t+3))
    if [ $t -ge "${ECSX_START_WAIT:-30}" ]; then
      echo "ecsx: no heartbeat after ${t}s: the start was lost; starting the run again, once" >&2
      start "$@" || true
      break
    fi
  done
fi
aws s3 rm "s3://$B/scripts/ecsx/$id.py" "${P[@]}" --quiet; aws s3 rm "s3://$B/scripts/ecsx/$id.runner.py" "${P[@]}" --quiet
t=0; until seen "$OUT.done"; do
  sleep 3; t=$((t+3)); [ $t -ge "$WAIT" ] && { echo "ecsx: no result after ${WAIT}s (s3://$B/$OUT; heartbeat s3://$B/$OUT.running)" >&2; exit 3; }; done
done_line=$(aws s3 cp "s3://$B/$OUT.done" - "${P[@]}")
aws s3 cp "s3://$B/$OUT" "$LOCAL_OUT" "${P[@]}" --quiet
cat "$LOCAL_OUT"
for k in "$OUT" "$OUT.done" "$OUT.running"; do aws s3 rm "s3://$B/$k" "${P[@]}" --quiet || true; done
echo "ecsx: $done_line (output also in $LOCAL_OUT)" >&2
rc=${done_line#rc=}; exit "${rc%% *}"
