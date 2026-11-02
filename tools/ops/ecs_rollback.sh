#!/usr/bin/env bash
# Roll one ECS service of the ecosystem back (or forward) to another task-definition revision. AA-1023.
# Runbook: docs/ops/runbooks/rollback-ecs.md. Usage: tools/ops/ecs_rollback.sh --help.
#
# DRY RUN by default: it reads the service, picks and checks the target revision (ACTIVE, image still in ECR, same
# environment names and secret references), and PRINTS the one-line update-service command, the command back and
# the verify commands. Only --apply changes anything: it runs that update-service, waits for services-stable and
# checks the rollout and the health endpoint's commit. Orchestrator / tech lead only (the subagent hook blocks it).
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: tools/ops/ecs_rollback.sh <service> --list
       tools/ops/ecs_rollback.sh <service> (--previous | --to <revision> | --to-sha <git sha>) [--apply] [--allow-config-diff]

<service>   aa-cis-dev-api | aa-cis-dev-worker | aa-booking-dev-api | aa-crm-dev-api | aa-crm-dev-web | aa-crm-dev-portal
            (the task-definition family has the same name as the service)
--list      the newest revisions with their image tag and status, the running one marked; read-only
--previous  the newest revision older than the running one whose image is DIFFERENT and a real build (a redeploy of
            the same image also registers a revision, and a Terraform apply registers template revisions with a
            placeholder tag such as bootstrap; both are skipped)
--to N      revision N of the family (also the way back after a drill: the revision the service ran before)
--to-sha S  the newest revision whose image tag is S or dev-S (full or short SHA prefix)
--apply     run the update-service, wait for services-stable, verify (default: print the commands only)
--allow-config-diff   let --apply through when the target's environment names or secret references differ from
            the running revision (a Terraform change in between; the tech lead decides, runbook step 4)

Environment: ROLLBACK_PROFILE (default aa365-admin), ROLLBACK_REGION (default us-west-1),
ROLLBACK_CLUSTER (default aa-cis-dev-cluster), ROLLBACK_LIST (revisions read, default 10),
ROLLBACK_HEALTH_TRIES (default 12, 10 s apart).
Exit: 0 ok (dry run printed, or applied and verified) · 1 refused or verify failed · 2 usage.
EOF
}

die() { echo "ERROR: $*" >&2; exit 1; }

PROFILE="${ROLLBACK_PROFILE:-aa365-admin}"
REGION="${ROLLBACK_REGION:-us-west-1}"
CLUSTER="${ROLLBACK_CLUSTER:-aa-cis-dev-cluster}"
LIST_N="${ROLLBACK_LIST:-10}"
TRIES="${ROLLBACK_HEALTH_TRIES:-12}"
SLEEP_S="${ROLLBACK_SLEEP_S:-10}"

[ $# -ge 1 ] || { usage >&2; exit 2; }
case "$1" in -h|--help) usage; exit 0 ;; esac
SERVICE="$1"; shift
MODE=""; ARG=""; APPLY=0; ALLOW_DIFF=0
while [ $# -gt 0 ]; do
  case "$1" in
    --list) MODE=list ;;
    --previous) MODE=previous ;;
    --to) MODE=rev; ARG="${2:-}"; shift ;;
    --to-sha) MODE=sha; ARG="${2:-}"; shift ;;
    --apply) APPLY=1 ;;
    --allow-config-diff) ALLOW_DIFF=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done
[ -n "$MODE" ] || { echo "pick one of --list, --previous, --to, --to-sha" >&2; exit 2; }
if [ "$MODE" = rev ] && ! [[ "$ARG" =~ ^[0-9]+$ ]]; then echo "--to needs a revision number" >&2; exit 2; fi
if [ "$MODE" = sha ] && ! [[ "$ARG" =~ ^[0-9a-f]{7,40}$ ]]; then echo "--to-sha needs a 7-40 character hex SHA" >&2; exit 2; fi

# Health endpoint and the JSON field that carries the deployed commit, per service.
case "$SERVICE" in
  aa-cis-dev-api) HEALTH="https://api-cis.lumiguides.it.com/health"; FIELD=git_sha ;;
  aa-cis-dev-worker) HEALTH=""; FIELD="" ;;     # no HTTP; /health is the api's. Check the job_worker_started log line
  aa-booking-dev-api) HEALTH="https://api-booking.lumiguides.it.com/booking/health"; FIELD=git_sha ;;
  aa-crm-dev-api) HEALTH="https://partner-dev.lumiguides.it.com/crm/health"; FIELD=git_sha ;;
  aa-crm-dev-web) HEALTH="https://portal.lumiguides.it.com/healthz"; FIELD=git_sha ;;
  aa-crm-dev-portal) HEALTH="https://portal.lumiguides.it.com/api/healthz"; FIELD=sha ;;
  *) echo "unknown service: $SERVICE" >&2; usage >&2; exit 2 ;;
esac
FAMILY="$SERVICE"

aws_() { aws "$@" --profile "$PROFILE" --region "$REGION"; }
tag_of() { local image="$1"; [[ "$image" == *:* ]] && printf '%s' "${image##*:}" || printf ''; }
sha_of() { local t; t="$(tag_of "$1")"; printf '%s' "${t#dev-}"; }
rev_of() { printf '%s' "${1##*:}"; }
# A deployable build: tag = git SHA (Booking, CRM) or dev-<git sha> (CIS). Terraform template revisions carry a
# placeholder (bootstrap, latest) and are never a rollback target (they hold the template's env, not the app's).
is_build() { [[ "$(tag_of "$1")" =~ ^(dev-)?[0-9a-f]{7,40}$ ]]; }

# 1. What runs now.
SVC="$(aws_ ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" --output json)"
CUR_ARN="$(jq -r '.services[0].taskDefinition // empty' <<<"$SVC")"
[ -n "$CUR_ARN" ] || die "service $SERVICE not found in $CLUSTER"
ROLLOUT="$(jq -r '[.services[0].deployments[]? | select(.status=="PRIMARY") | .rolloutState][0] // "unknown"' <<<"$SVC")"
NDEP="$(jq -r '[.services[0].deployments[]?] | length' <<<"$SVC")"
CUR_REV="$(rev_of "$CUR_ARN")"
CUR_TD="$(aws_ ecs describe-task-definition --task-definition "$CUR_ARN" --output json)"
CUR_IMAGE="$(jq -r '.taskDefinition.containerDefinitions[0].image' <<<"$CUR_TD")"

# 2. The newest revisions of the family: "<rev> <status> <image>" per line, newest first.
ARNS="$(aws_ ecs list-task-definitions --family-prefix "$FAMILY" --status ACTIVE --sort DESC --max-items "$LIST_N" --query 'taskDefinitionArns' --output json)"
REVS=""
for arn in $(jq -r '.[]' <<<"$ARNS"); do
  [[ "$arn" =~ :task-definition/${FAMILY}:[0-9]+$ ]] || continue     # --family-prefix also matches longer names
  td="$(aws_ ecs describe-task-definition --task-definition "$arn" --output json)"
  REVS+="$(rev_of "$arn") $(jq -r '.taskDefinition.status' <<<"$td") $(jq -r '.taskDefinition.containerDefinitions[0].image' <<<"$td")"$'\n'
done

echo "service:  $SERVICE (cluster $CLUSTER)"
echo "running:  $FAMILY:$CUR_REV  image tag $(tag_of "$CUR_IMAGE")  rollout $ROLLOUT  deployments $NDEP"
if [ "$MODE" = list ]; then
  echo "revisions (newest first, ACTIVE):"
  while read -r rev status image; do
    [ -n "$rev" ] || continue
    mark=""; [ "$rev" = "$CUR_REV" ] && mark="   <- running"
    is_build "$image" || mark="$mark   (Terraform template, not a target)"
    echo "  $FAMILY:$rev  $(tag_of "$image")  $status$mark"
  done <<<"$REVS"
  exit 0
fi
[ "$ROLLOUT" = COMPLETED ] || echo "WARNING: the running deployment is $ROLLOUT, not COMPLETED: wait for the circuit breaker first (runbook step 1)"

# 3. The target revision.
TARGET_REV=""
case "$MODE" in
  rev) TARGET_REV="$ARG" ;;
  previous)
    while read -r rev status image; do
      [ -n "$rev" ] || continue
      if [ "$rev" -lt "$CUR_REV" ] && [ "$image" != "$CUR_IMAGE" ] && is_build "$image"; then TARGET_REV="$rev"; break; fi
    done <<<"$REVS"
    [ -n "$TARGET_REV" ] || die "no ACTIVE revision older than $CUR_REV with a different image in the newest $LIST_N (raise ROLLBACK_LIST, or use --to)" ;;
  sha)
    while read -r rev status image; do
      [ -n "$rev" ] || continue
      if [[ "$(sha_of "$image")" == "$ARG"* ]]; then TARGET_REV="$rev"; break; fi
    done <<<"$REVS"
    [ -n "$TARGET_REV" ] || die "no ACTIVE revision with image tag $ARG or dev-$ARG in the newest $LIST_N (raise ROLLBACK_LIST)" ;;
esac
[ "$TARGET_REV" != "$CUR_REV" ] || die "$FAMILY:$TARGET_REV is already the running revision"
TARGET="$FAMILY:$TARGET_REV"
TGT_TD="$(aws_ ecs describe-task-definition --task-definition "$TARGET" --output json)" || die "cannot read $TARGET"
[ "$(jq -r '.taskDefinition.status' <<<"$TGT_TD")" = ACTIVE ] || die "$TARGET is not ACTIVE (a service cannot move to an INACTIVE revision)"
TGT_IMAGE="$(jq -r '.taskDefinition.containerDefinitions[0].image' <<<"$TGT_TD")"
is_build "$TGT_IMAGE" || die "$TARGET runs the placeholder image tag '$(tag_of "$TGT_IMAGE")' (a Terraform template revision), not a build: pick a revision with a git SHA tag"
TGT_TAG="$(tag_of "$TGT_IMAGE")"
TGT_SHA="$(sha_of "$TGT_IMAGE")"
echo "target:   $TARGET  image tag $TGT_TAG"
[ "$TGT_IMAGE" != "$CUR_IMAGE" ] || echo "NOTE: the target runs the same image as now (configuration-only move)"

# 4. Image still in ECR (lifecycle rules keep only the newest images).
REPO="${TGT_IMAGE#*/}"; REPO="${REPO%%:*}"
PUSHED="$(aws_ ecr describe-images --repository-name "$REPO" --image-ids "imageTag=$TGT_TAG" --query 'imageDetails[0].imagePushedAt' --output text 2>/dev/null)" \
  || die "image $REPO:$TGT_TAG is not in ECR any more (lifecycle rule): pick a newer good revision or fix forward"
echo "image:    $REPO:$TGT_TAG pushed $PUSHED"

# 5. Configuration: environment names and secret references of the first container.
cfg() { jq -S '.taskDefinition.containerDefinitions[0] | {env: ([.environment[]?.name] | sort), secrets: ([.secrets[]? | "\(.name)=\(.valueFrom)"] | sort)}'; }
CUR_CFG="$(cfg <<<"$CUR_TD")"; TGT_CFG="$(cfg <<<"$TGT_TD")"
CONFIG_DIFF=0
if [ "$CUR_CFG" != "$TGT_CFG" ]; then
  CONFIG_DIFF=1
  echo "CONFIG DIFF between $FAMILY:$CUR_REV (running) and $TARGET:"
  jq -rn --argjson a "$CUR_CFG" --argjson b "$TGT_CFG" '
    ([$a.env[] | select(. as $x | $b.env | index($x) | not) | "  env only in running: \(.)"]
     + [$b.env[] | select(. as $x | $a.env | index($x) | not) | "  env only in target:  \(.)"]
     + [$a.secrets[] | select(. as $x | $b.secrets | index($x) | not) | "  secret only in running: \(sub("=.*"; ""))"]
     + [$b.secrets[] | select(. as $x | $a.secrets | index($x) | not) | "  secret only in target:  \(sub("=.*"; ""))"]) | .[]'
else
  echo "config:   same environment names and secret references"
fi

CMD="aws ecs update-service --cluster $CLUSTER --service $SERVICE --task-definition $TARGET --profile $PROFILE --region $REGION --query \"service.deployments[0].rolloutState\" --output text"
BACK="aws ecs update-service --cluster $CLUSTER --service $SERVICE --task-definition $FAMILY:$CUR_REV --profile $PROFILE --region $REGION --query \"service.deployments[0].rolloutState\" --output text"
WAIT="aws ecs wait services-stable --cluster $CLUSTER --services $SERVICE --profile $PROFILE --region $REGION"
echo
echo "command (WRITE):  $CMD"
echo "wait:             $WAIT"
[ -n "$HEALTH" ] && echo "verify:           curl -s $HEALTH   (expect $FIELD starting with $TGT_SHA)"
echo "way back (WRITE): $BACK"
case "$SERVICE" in
  aa-cis-dev-api|aa-cis-dev-worker)
    echo "NOTE: CIS api and worker must run the same image: move the other service to its revision with tag $TGT_TAG too (runbook rollback-cis step 6)" ;;
esac
echo "NOTE: a rollback restarts the container like a deploy: check the app's deploy gate first (runbook rollback-ecs, Preconditions)"

if [ "$APPLY" != 1 ]; then
  echo
  echo "DRY RUN: nothing changed. Re-run with --apply to run the command above."
  exit 0
fi
if [ "$CONFIG_DIFF" = 1 ] && [ "$ALLOW_DIFF" != 1 ]; then
  die "configuration differs (above): --apply refused without --allow-config-diff (the tech lead decides)"
fi

# 6. Apply, wait, verify.
START="$(date +%s)"
echo
echo "applying: $SERVICE -> $TARGET"
STATE="$(aws_ ecs update-service --cluster "$CLUSTER" --service "$SERVICE" --task-definition "$TARGET" --query 'service.deployments[0].rolloutState' --output text)"
echo "rollout:  $STATE"
aws_ ecs wait services-stable --cluster "$CLUSTER" --services "$SERVICE" || die "services-stable did not return (10 min): check the deployment; way back: $BACK"
SVC="$(aws_ ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" --output json)"
NOW_ARN="$(jq -r '.services[0].taskDefinition' <<<"$SVC")"
NOW_ROLLOUT="$(jq -r '[.services[0].deployments[]? | select(.status=="PRIMARY") | .rolloutState][0] // "unknown"' <<<"$SVC")"
[ "$(rev_of "$NOW_ARN")" = "$TARGET_REV" ] || die "service runs $NOW_ARN, not $TARGET (circuit breaker rolled back?)"
[ "$NOW_ROLLOUT" = COMPLETED ] || die "rollout is $NOW_ROLLOUT, not COMPLETED"
echo "stable:   $TARGET COMPLETED after $(( $(date +%s) - START )) s"
if [ -n "$HEALTH" ]; then
  GOT=""
  for i in $(seq 1 "$TRIES"); do
    GOT="$(curl -s --max-time 10 "$HEALTH" | jq -r --arg f "$FIELD" '.[$f] // empty' 2>/dev/null || true)"
    if [ -n "$GOT" ] && { [[ "$TGT_SHA" == "$GOT"* ]] || [[ "$GOT" == "$TGT_SHA"* ]]; }; then break; fi
    [ "$i" -lt "$TRIES" ] && sleep "$SLEEP_S"
    GOT=""
  done
  [ -n "$GOT" ] || die "$HEALTH does not report $FIELD=$TGT_SHA after $TRIES tries (an old task may still answer; check again, or go back: $BACK)"
  echo "health:   $HEALTH $FIELD=$GOT"
fi
echo "DONE: $SERVICE on $TARGET ($TGT_TAG) in $(( $(date +%s) - START )) s. Way back: $BACK"
