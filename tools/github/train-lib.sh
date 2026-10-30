#!/usr/bin/env bash
# Functions for a background merge train (skill aa-ship, references/merge-trains.md). Source it, do not run it:
#
#   . /home/nghiep/projects/AA-Ecosys/tools/github/train-lib.sh
#   gate <Repo> <pr>                  wait for checks; return 0 only when EVERY check is pass/skipping and not DIRTY
#   merged <Repo> <pr>                print "<Repo> #<pr> <state> <sha8>"; sets MERGED_SHA (full SHA, empty if not merged)
#   waitcopy <owner> <NNN>            wait for db/migrations/<owner>/<NNN>_*.sql on Infra main; an open contract or
#                                     destructive bot/migration-copy/<owner>-<NNN> PR is gated and merged here
#   waitdeploy <cis|booking|crm> <sha>  wait until the app's health endpoint reports git_sha = <sha>
#   restack <worktree> <old-base-sha> <pr>  rebase --onto origin/main, push --force-with-lease, gh pr ready, re-gate
#
# Orchestrator only: merges and pushes go through the aa-agent App (as-app.sh next to this file); the subagent hook
# blocks them. Holds no secrets: as-app.sh reads the App key from Secrets Manager at call time (needs a live MFA session).
# Every wait has a timeout; a function returns non-zero on the first red step so the train can `|| exit 1`.

ORG=AdventureAsia365-Ecosys
ROOT=/home/nghiep/projects/AA-Ecosys
_T="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/as-app.sh"
GATE_TIMEOUT=${GATE_TIMEOUT:-2400}

gate() {
  local r=$1 n=$2 bad ms
  timeout "$GATE_TIMEOUT" gh pr checks "$n" -R "$ORG/$r" --watch --interval 60 >/dev/null 2>&1
  bad=$(gh pr checks "$n" -R "$ORG/$r" 2>&1 | awk -F'\t' '$2!="pass" && $2!="skipping" {print $1" ("$2")"}')
  [ -z "$bad" ] || { echo "$r #$n NOT GREEN: $(echo "$bad" | tr '\n' ';')"; return 1; }
  ms=$(gh pr view "$n" -R "$ORG/$r" --json mergeStateStatus -q .mergeStateStatus)
  [ "$ms" = DIRTY ] && { echo "$r #$n DIRTY (conflict with main)"; return 1; }
  echo "$r #$n green ($ms)"
}

merged() {
  local r=$1 n=$2 out
  out=$(gh pr view "$n" -R "$ORG/$r" --json state,mergeCommit -q '.state+" "+(.mergeCommit.oid // "")')
  MERGED_SHA=${out#* }; [ "${out%% *}" = MERGED ] || MERGED_SHA=""
  echo "$r #$n ${out%% *} ${MERGED_SHA:0:8}"
}

waitcopy() {
  local o=$1 v=$2 i pr lab
  for i in $(seq 1 60); do
    git -C "$ROOT/infra/AA-CIS-Infra" fetch -q origin
    git -C "$ROOT/infra/AA-CIS-Infra" ls-tree --name-only origin/main "db/migrations/$o/" | grep -q "/${v}_" \
      && { echo "copy $o-$v on Infra main"; return 0; }
    pr=$(gh pr list -R "$ORG/AA-CIS-Infra" --state open --json number,headRefName,labels \
      -q ".[] | select(.headRefName==\"bot/migration-copy/$o-$v\") | \"\(.number) \([.labels[].name]|join(\",\"))\"")
    if [ -n "$pr" ]; then
      lab=${pr#* }
      case $lab in
        *migration:contract*|*migration:destructive*)
          gate AA-CIS-Infra "${pr%% *}" || return 1
          "$_T" --repos AA-CIS-Infra -- gh pr merge "${pr%% *}" -R "$ORG/AA-CIS-Infra" --squash && echo "copy PR #${pr%% *} ($lab) merged" ;;
      esac
    fi
    sleep 30
  done
  echo "copy $o-$v NOT on Infra main"; return 1
}

waitdeploy() {
  local app=$1 sha=$2 url i s
  case $app in
    cis) url=https://api-cis.lumiguides.it.com/health/ready ;;
    booking) url=https://api-booking.lumiguides.it.com/booking/health ;;
    crm) url=https://partner-dev.lumiguides.it.com/crm/health ;;
    *) echo "waitdeploy: app is cis|booking|crm"; return 2 ;;
  esac
  for i in $(seq 1 60); do
    s=$(curl -s -m 10 "$url")
    echo "$s" | grep -q "\"git_sha\":\"$sha" && { echo "$app deployed ${sha:0:8}"; return 0; }
    sleep 30
  done
  echo "$app deploy ${sha:0:8} not live after 30 min"; return 1
}

restack() {
  local w=$1 base=$2 n=$3 r
  r=$(basename -s .git "$(git -C "$w" remote get-url origin)")
  git -C "$w" fetch -q origin
  git -C "$w" log --oneline -3
  git -C "$w" rebase --onto origin/main "$base" >/dev/null 2>&1 || { git -C "$w" rebase --abort; echo "$r #$n restack conflict"; return 1; }
  "$_T" --repos "$r" -- git -C "$w" push --force-with-lease 2>&1 | tail -1
  gh pr ready "$n" -R "$ORG/$r" 2>&1 | tail -1
  sleep 45
  gate "$r" "$n"
}
