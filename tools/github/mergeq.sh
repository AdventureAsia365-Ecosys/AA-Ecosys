#!/usr/bin/env bash
# Merge a PR through the GitHub merge queue (AA-889) for AA-CIS-App, AA-Partner, AA-Booking; or take it out again.
#
#   tools/github/mergeq.sh <Repo> <pr>            wait for PR checks, enqueue, wait until merged, print the SHA
#   tools/github/mergeq.sh <Repo> <pr> --dequeue  take the PR out of the queue (or cancel a pending auto-merge)
#
# Orchestrator only: runs gh through the aa-agent App (as-app.sh next to this file); the subagent hook blocks merges.
# Exit: 0 merged / dequeued | 3 PR checks red | 4 dropped from the queue (group CI red, timeout, conflict) or enqueue
#       failed | 5 timed out waiting (MAXWAIT seconds, default 5400).
#
# Why --dequeue is not `gh pr merge --disable-auto`: once the PR's required checks have passed, `gh pr merge` adds it
# straight to the queue and no auto-merge request exists, so --disable-auto has nothing to cancel and the entry still
# lands on main. A queued entry is removed only by the GraphQL mutation dequeuePullRequest (or "Remove from queue" in
# the UI). --dequeue does both: cancels a pending auto-merge if any, then dequeues if the PR is in the queue.
set -uo pipefail
R=${1:?usage: mergeq.sh <Repo> <pr> [--dequeue]}; N=${2:?pr number}; MODE=${3:-}
ORG=AdventureAsia365-Ecosys
T="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/as-app.sh"
MAXWAIT=${MAXWAIT:-5400}   # 90 min: PR CI + queue CI (CIS ~10 min each) + queue position

st() { gh pr view "$N" -R "$ORG/$R" --json state,mergeCommit,mergeStateStatus,autoMergeRequest \
         --jq '[.state, (.mergeCommit.oid // ""), .mergeStateStatus, (if .autoMergeRequest then "auto" else "" end)] | @tsv'; }
inq() { gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){isInMergeQueue mergeQueueEntry{state position}}}}' \
          -f o="$ORG" -f r="$R" -F n="$N" --jq '.data.repository.pullRequest | [(.isInMergeQueue|tostring), (.mergeQueueEntry.state // ""), ((.mergeQueueEntry.position // "")|tostring)] | @tsv'; }

IFS=$'\t' read -r S SHA _ AUTO < <(st)
[ "$S" = MERGED ] && { echo "$R #$N already merged ${SHA:0:8}"; exit 0; }

if [ "$MODE" = --dequeue ]; then
  [ -n "$AUTO" ] && { "$T" --repos "$R" -- gh pr merge "$N" -R "$ORG/$R" --disable-auto && echo "$R #$N auto-merge cancelled"; }
  IFS=$'\t' read -r Q QS _ < <(inq)
  if [ "$Q" = true ]; then
    ID=$(gh pr view "$N" -R "$ORG/$R" --json id --jq .id)
    "$T" --repos "$R" -- gh api graphql -f query='mutation($id:ID!){dequeuePullRequest(input:{id:$id}){clientMutationId}}' \
      -f id="$ID" >/dev/null || { echo "$R #$N dequeue failed (state $QS): use 'Remove from queue' in the UI"; exit 4; }
  fi
  IFS=$'\t' read -r S SHA _ AUTO < <(st); IFS=$'\t' read -r Q QS _ < <(inq)
  [ "$S" = MERGED ] && { echo "$R #$N merged before it could be dequeued ${SHA:0:8}"; exit 4; }
  [ "$Q" = true ] || [ -n "$AUTO" ] && { echo "$R #$N still queued ($QS) / auto=$AUTO"; exit 4; }
  echo "$R #$N out of the queue, no auto-merge"; exit 0
fi

# 1. PR checks first: the queue takes only a PR whose required checks passed on its own head.
sleep 20; gh pr checks "$N" -R "$ORG/$R" --watch --interval 30 >/dev/null 2>&1
if gh pr checks "$N" -R "$ORG/$R" --required 2>/dev/null | grep -qE $'\tfail'; then
  echo "$R #$N required checks red"; gh pr checks "$N" -R "$ORG/$R" 2>&1 | grep -v -E "pass|skipping"; exit 3
fi

# 2. Enqueue. With the queue required, gh ignores the merge method (the ruleset sets SQUASH). Checks green → gh adds
#    the PR straight to the queue; checks still pending → gh turns on auto-merge, which enqueues once they pass.
#    Fallback without --auto for a repo with auto-merge off (AA-Partner before SETTINGS step 2).
out=$("$T" --repos "$R" -- gh pr merge "$N" -R "$ORG/$R" --squash --auto 2>&1); rc=$?
if [ $rc -ne 0 ]; then
  echo "$R #$N --auto refused: $(tail -1 <<<"$out"); retrying without --auto"
  out=$("$T" --repos "$R" -- gh pr merge "$N" -R "$ORG/$R" --squash 2>&1) || { echo "$R #$N enqueue failed: $(tail -2 <<<"$out")"; exit 4; }
fi
echo "$R #$N queued: $(tail -1 <<<"$out")"

# 3. Wait: one check per minute (the queue runs CI again on gh-readonly-queue/main/*).
seen=0; t0=$(date +%s); Q=""; QS=""; QP=""
while [ $(( $(date +%s) - t0 )) -lt "$MAXWAIT" ]; do
  sleep 60
  IFS=$'\t' read -r S SHA M AUTO < <(st)
  [ "$S" = MERGED ] && { echo "$R #$N MERGED ${SHA:0:8} ($SHA)"; exit 0; }
  IFS=$'\t' read -r Q QS QP < <(inq)
  if [ "$Q" = true ]; then
    seen=1; [ $(( ($(date +%s) - t0) % 300 )) -lt 60 ] && echo "$R #$N in queue: $QS position $QP"
  elif [ "$seen" = 1 ] || { [ -z "$AUTO" ] && [ $(( $(date +%s) - t0 )) -gt 300 ]; }; then
    # Left the queue without merging (group CI red, check timeout, conflict, dequeued) or never got in.
    echo "$R #$N not merged and not in the queue (state $S, $M). Group runs:"
    gh run list -R "$ORG/$R" --event merge_group --limit 5 2>&1 | head -6; exit 4
  fi
done
echo "$R #$N still not merged after ${MAXWAIT}s (queue: $Q $QS $QP)"; exit 5
