#!/usr/bin/env bash
# Kiro readiness check — run at the start of a "dùng kiro-cli" session and before each task.
#
# usage: kiro-preflight.sh            -> prints a status block, writes .tmp-session/kiro/preflight.txt
# exit:  0 ready
#        3 credits low (< KIRO_MIN_CREDITS left, default 100) or usage >= KIRO_MAX_PCT (default 95)
#        4 not installed / not logged in
#        5 usage or ping failed (rate limit, network, auth expired) — treat as unavailable
#
# Exit != 0 means: report to Nghiệp and fall back to Claude writing the code itself.
set -uo pipefail

ROOT=/home/nghiep/projects/AA-Ecosys
OUT="$ROOT/.tmp-session/kiro"
KIRO="$HOME/.local/bin/kiro-cli"
MIN_LEFT="${KIRO_MIN_CREDITS:-100}"
MAX_PCT="${KIRO_MAX_PCT:-95}"
mkdir -p "$OUT"
strip() { sed -r 's/\x1B\[[0-9;?]*[A-Za-z]//g'; }
report() { { echo "checked=$(date -u +%FT%TZ)"; echo "status=$1"; echo "detail=$2"; } | tee "$OUT/preflight.txt"; exit "$3"; }

[ -x "$KIRO" ] || report not_installed "kiro-cli missing at $KIRO" 4
WHO=$("$KIRO" whoami 2>&1 | strip)
echo "$WHO" | grep -qi "not logged in" && report not_logged_in "run: kiro-cli login (IAM Identity Center, see SKILL.md)" 4

cd "$ROOT" || exit 5
USAGE=$(timeout 90 "$KIRO" chat --no-interactive --trust-tools= "/usage" 2>&1 | strip)
LINE=$(echo "$USAGE" | grep -m1 -iE "Credits \(")
if [ -z "$LINE" ]; then
  report usage_failed "$(echo "$USAGE" | tail -3 | tr '\n' ' ')" 5
fi
USED=$(echo "$LINE" | sed -nE 's/.*Credits \(([0-9.]+) of ([0-9.]+).*/\1/p')
TOTAL=$(echo "$LINE" | sed -nE 's/.*Credits \(([0-9.]+) of ([0-9.]+).*/\2/p')
RESET=$(echo "$USAGE" | grep -m1 -oE "resets on [0-9-]+" || true)
LEFT=$(awk -v u="$USED" -v t="$TOTAL" 'BEGIN{printf "%.2f", t-u}')
PCT=$(awk -v u="$USED" -v t="$TOTAL" 'BEGIN{printf "%.1f", (t>0?100*u/t:100)}')
echo "credits_used=$USED"; echo "credits_total=$TOTAL"; echo "credits_left=$LEFT"; echo "used_pct=$PCT"; echo "$RESET"

if awk -v l="$LEFT" -v m="$MIN_LEFT" -v p="$PCT" -v x="$MAX_PCT" 'BEGIN{exit !((l < m) || (p >= x))}'; then
  report credits_low "left=$LEFT of $TOTAL (${PCT}% used, $RESET)" 3
fi

PING=$(timeout 90 "$KIRO" chat --no-interactive --trust-tools= "Reply with exactly the text KIRO_OK and nothing else." 2>&1 | strip)
echo "$PING" | grep -q "KIRO_OK" || report ping_failed "$(echo "$PING" | tail -3 | tr '\n' ' ')" 5

report ready "left=$LEFT of $TOTAL (${PCT}% used, $RESET); $(echo "$WHO" | head -1)" 0
