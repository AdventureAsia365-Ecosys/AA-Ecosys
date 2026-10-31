#!/usr/bin/env bash
# CRM review set (AA-1014, plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): prep -> R00..R20 in order ->
# cleanup, one Chromium at a time, on Dev with the invented agency "Lữ hành Sen Vàng". Cost $0 (no LLM, local TTS).
#   bash tools/uat/scenarios/crm/run-all.sh --fast                 every chunk in fast mode (no video): regression pass
#   bash tools/uat/scenarios/crm/run-all.sh                        record: captions -> TTS -> take -> build --no-burn
#   options: --keep-run     reuse the current run (no cleanup of it, prep stays idempotent); default: clean the last run
#                           and start a new one (UAT_CRM_NEW_RUN=1). Record R10's overdue reminder with --keep-run on a
#                           run prepared at least one agency day earlier.
#            --only 07,12   just these chunks (prep still runs first; cleanup only with --cleanup)
#            --no-cleanup   leave the run's data in place at the end (to re-run chunks)
# Recorded chunks go to tools/uat/out/crm/no-burn/ (input for longform.py). Per chunk verdict, failing step and the CRM
# git SHA (start and end): work/crm/run-all.tsv. A failing chunk does not stop the set; cleanup always runs.
# RAM guard before every Chromium launch and TTS load: needs >= 2500 MB available, waits 2 min up to 5 times, then
# stops with "RAM too low". Exit: 0 all PASS | 2 a chunk FAILed | 3 egress not VN | 4 RAM too low.
set -uo pipefail
UAT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$UAT"

FAST=""; KEEP=0; ONLY=""; CLEANUP=1; CLEANUP_SET=0
while [ $# -gt 0 ]; do
  case "$1" in
    --fast) FAST="--fast" ;;
    --keep-run) KEEP=1 ;;
    --only) ONLY="${2:?--only 07,12}"; shift ;;
    --no-cleanup) CLEANUP=0; CLEANUP_SET=1 ;;
    --cleanup) CLEANUP=1; CLEANUP_SET=1 ;;
    *) echo "unknown option $1"; exit 1 ;;
  esac
  shift
done
[ -n "$ONLY" ] && [ "$CLEANUP_SET" = 0 ] && CLEANUP=0

[ -d node_modules/@playwright/test ] || { echo "STOP: run bash tools/uat/setup.sh first"; exit 1; }
c=$(curl -s --max-time 10 https://ipinfo.io/country || true)
[ "$c" = "VN" ] || { echo "STOP: public IP country is '$c', not VN (Vercel blocks VPN IPs). Turn the VPN off."; exit 3; }

guard() {
  local a i
  for i in 0 1 2 3 4 5; do
    a=$(free -m | awk '/^Mem/{print $7}')
    [ "$a" -ge 2500 ] && return 0
    [ "$i" = 5 ] && break
    echo "RAM low (${a} MB available), waiting 2 min"; sleep 120
  done
  free -m; echo "RAM too low"; exit 4
}

TSV=work/crm/run-all.tsv
mkdir -p work/crm
printf 'chunk\tverdict\tfailed_step\tsteps\tgit_sha_start\tgit_sha_end\tmode\n' > "$TSV"
FAILED=0

note() { # one row per chunk from its result.json
  node -e '
    const r = require(require("path").resolve(process.argv[1]));
    const m = r.meta || {}; const f = r.failed_step;
    console.log([r.id, r.verdict, f ? `${f}: ${String(r.failed_error || "").replace(/\s+/g, " ").slice(0, 160)}` : "",
      `${r.steps_run}/${r.steps_total}`, (m.git_sha_start || "").slice(0, 7), (m.git_sha_end || "").slice(0, 7), r.mode].join("\t"));
  ' "work/$1/result.json" >> "$TSV" 2>/dev/null || printf '%s\tCRASH\t\t\t\t\t%s\n' "$1" "${FAST:-uat}" >> "$TSV"
}

fast_step() { # $1 scenario file stem; data steps (prep, cleanup) always run in fast mode
  local id rc
  id=$(node -e 'console.log(require(require("path").resolve(process.argv[1])).id)' "scenarios/crm/$1.cjs")
  guard
  echo "=== $1 $(date +%T) (fast)"
  rm -f "work/$id/result.json"
  timeout 900 node record.cjs "scenarios/crm/$1.cjs" --fast 2>&1 | grep -E '^step |^verdict|^cleanup:|^prep:|Error'
  rc=${PIPESTATUS[0]}
  note "$id"
  [ "$rc" = 0 ] || FAILED=1
}

record_step() { # captions -> local TTS (one model at a time) -> take -> chunk MP4 without burned subtitles
  local id rc mp4
  id=$(node -e 'console.log(require(require("path").resolve(process.argv[1])).id)' "scenarios/crm/$1.cjs")
  echo "=== $1 $(date +%T) (record)"
  node record.cjs "scenarios/crm/$1.cjs" --captions || { FAILED=1; return; }
  guard
  ./venv/bin/python -I tts.py "work/$id" || { FAILED=1; return; }
  guard
  rm -f "work/$id/result.json"
  timeout 1800 node record.cjs "scenarios/crm/$1.cjs"; rc=$?
  note "$id"
  [ "$rc" = 0 ] || { FAILED=1; return; }
  mp4="$(./venv/bin/python -I build.py "work/$id" out/crm --no-burn | tail -1)"
  ./venv/bin/python -I check_sync.py "$mp4" "${mp4%.mp4}.en.srt" --frames "work/$id/frames" || FAILED=1
  ./venv/bin/python -I check_sync.py "$mp4" "${mp4%.mp4}.vi.srt" --track 1 || FAILED=1
  echo "chunk $mp4"
}

if [ "$KEEP" = 0 ]; then
  fast_step cleanup # the last run's data, before a new run suffix replaces its state
  UAT_CRM_NEW_RUN=1 fast_step prep
else
  fast_step prep
fi

for n in 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20; do
  if [ -n "$ONLY" ] && ! [[ ",$ONLY," == *",$n,"* ]]; then continue; fi
  if [ -n "$FAST" ]; then fast_step "crm-rev-$n"; else record_step "crm-rev-$n"; fi
done

[ "$CLEANUP" = 1 ] && fast_step cleanup

echo "--- summary ($TSV)"
column -t -s $'\t' "$TSV" 2>/dev/null || cat "$TSV"
[ "$FAILED" = 0 ] && exit 0 || exit 2
