#!/usr/bin/env bash
# Consolidate the aa-ecosys-ci-bot private key into ONE environment secret per repo (AA-1183 part 2).
#
# Target, in each of the six repos: environment `ci-bot` (deployment branches: the default branch only; no required
# reviewers, no wait timer) holding the secret AA_CI_BOT_PRIVATE_KEY; the App id stays the REPO variable
# AA_CI_BOT_APP_ID (an identifier, not a credential). Every workflow that mints a ci-bot token runs its job in
# `environment: ci-bot`; no copy of the key stays at repo level or in another environment.
#
# Before (S296 listing, 27/11/2026): AA-CIS-App, AA-Booking, AA-Partner, AA-TripPlanner-Web in environment `release`;
# AA-Ecosys in environment `ci-hygiene`; AA-CIS-Infra at REPO level (readable by any workflow on any branch).
#
# A GitHub secret cannot be read back, so the move needs the key file: the tech lead generates a NEW private key in the
# App settings (that is the rotation), this script stores it in the six `ci-bot` environments, the workflow PRs move to
# `ci-bot`, then `cleanup` deletes the old copies and the tech lead deletes the old key in the App settings.
#
# Order (docs/security/secrets-register.md, "CI bot key"):
#   1. tech lead, browser: App aa-ecosys-ci-bot -> Permissions: Repository "Secrets" Read-only and "Environments"
#      Read-only (for the weekly rotation check), save, accept the update on the installation; then Private keys ->
#      Generate a private key (downloads <slug>.<date>.private-key.pem).
#   2. bash tools/security/ci_bot_key_consolidate.sh setup --pem <pem file> --apply        (orchestrator)
#   3. merge the workflow PRs (root, AA-CIS-App, AA-Booking, AA-Partner, AA-TripPlanner-Web, AA-CIS-Infra) and run
#      one ci-bot workflow per repo green (live steps of each PR).
#   4. bash tools/security/ci_bot_key_consolidate.sh cleanup --apply [--delete-old-envs]   (orchestrator)
#   5. tech lead, browser: App settings -> Private keys -> delete the OLD key (keep the one generated in step 1).
#   6. root PR: the register rows (store github:<repo>/ci-bot, last_rotated = the day of step 2; old rows deleted).
#
# Commands (dry run unless --apply; every gh call is one line; the key is read from the file by gh, never echoed):
#   plan                                   read-only: where each copy is now and what is missing
#   setup --pem FILE [--apply] [--shred]   create/align the ci-bot environments, store the key, set the repo variable
#   cleanup [--apply] [--delete-old-envs]  refuse while a default-branch workflow still reads the key outside
#                                          ci-bot; otherwise delete the old copies (and the emptied old environments)
set -euo pipefail

OWNER="AdventureAsia365-Ecosys"
ENV_NAME="ci-bot"
KEY_NAME="AA_CI_BOT_PRIVATE_KEY"
APP_ID_VAR="AA_CI_BOT_APP_ID"
REPOS=(AA-Ecosys AA-CIS-App AA-Booking AA-Partner AA-TripPlanner-Web AA-CIS-Infra)
# Old places of the key: "<repo> <environment>" (environment "-" = repo level).
OLD_COPIES=("AA-Ecosys ci-hygiene" "AA-CIS-App release" "AA-Booking release" "AA-Partner release" "AA-TripPlanner-Web release" "AA-CIS-Infra -")
# Old environment-level copies of the App id variable (moved to repo level).
OLD_VARS=("AA-Partner release")

CMD="${1:-plan}"; shift || true
APPLY=false; SHRED=false; DELETE_OLD_ENVS=false; PEM=""
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=true ;;
    --shred) SHRED=true ;;
    --delete-old-envs) DELETE_OLD_ENVS=true ;;
    --pem) PEM="${2:-}"; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

branch_of() { if [ "$1" = "AA-Ecosys" ]; then echo master; else echo main; fi; }

run() {
  # Print the command (never a secret: the key is passed as a file on stdin), run it only with --apply.
  echo "+ $*"
  if [ "$APPLY" = true ]; then "$@"; fi
}

has_env_secret() { gh api "repos/$OWNER/$1/environments/$2/secrets" --jq ".secrets[].name" 2>/dev/null | grep -qx "$KEY_NAME"; }
has_repo_secret() { gh api "repos/$OWNER/$1/actions/secrets" --jq ".secrets[].name" 2>/dev/null | grep -qx "$KEY_NAME"; }
has_repo_var() { gh api "repos/$OWNER/$1/actions/variables" --jq ".variables[].name" 2>/dev/null | grep -qx "$APP_ID_VAR"; }
env_exists() { gh api "repos/$OWNER/$1/environments/$2" --jq .name >/dev/null 2>&1; }
env_branches() { gh api "repos/$OWNER/$1/environments/$2/deployment-branch-policies" --jq '[.branch_policies[] | "\(.type):\(.name)"] | join(",")' 2>/dev/null || echo "?"; }
env_rules() { gh api "repos/$OWNER/$1/environments/$2" --jq '[.protection_rules[].type] | join(",")' 2>/dev/null || echo "?"; }

plan() {
  for repo in "${REPOS[@]}"; do
    br=$(branch_of "$repo")
    if env_exists "$repo" "$ENV_NAME"; then
      state="exists, branches [$(env_branches "$repo" "$ENV_NAME")], rules [$(env_rules "$repo" "$ENV_NAME")], key $(has_env_secret "$repo" "$ENV_NAME" && echo set || echo MISSING)"
    else
      state="MISSING"
    fi
    echo "$repo: $ENV_NAME environment: $state (want branches [branch:$br], rules [branch_policy] only)"
    echo "$repo: repo variable $APP_ID_VAR: $(has_repo_var "$repo" && echo set || echo MISSING)"
  done
  for entry in "${OLD_COPIES[@]}"; do
    read -r repo env <<<"$entry"
    if [ "$env" = "-" ]; then
      echo "$repo: old copy at repo level: $(has_repo_secret "$repo" && echo PRESENT || echo gone)"
    else
      echo "$repo: old copy in environment $env: $(has_env_secret "$repo" "$env" && echo PRESENT || echo gone)"
    fi
  done
}

setup() {
  if [ -z "$PEM" ] || [ ! -f "$PEM" ]; then echo "setup needs --pem <the new private key file>" >&2; exit 2; fi
  if ! head -n1 "$PEM" | grep -q -- "-----BEGIN .*PRIVATE KEY-----"; then echo "$PEM does not look like a PEM private key" >&2; exit 2; fi
  app_id=""
  for repo in "${REPOS[@]}"; do
    if has_repo_var "$repo"; then app_id=$(gh variable get "$APP_ID_VAR" --repo "$OWNER/$repo"); break; fi
  done
  if [ -z "$app_id" ]; then echo "no repo has the variable $APP_ID_VAR to copy from" >&2; exit 2; fi
  for repo in "${REPOS[@]}"; do
    br=$(branch_of "$repo")
    echo "== $repo ($br)"
    # Custom branch policies, no reviewers, no wait timer (S295 Q6: no required approvals).
    run gh api -X PUT "repos/$OWNER/$repo/environments/$ENV_NAME" --input - <<<'{"wait_timer":0,"reviewers":[],"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}}'
    if [ "$APPLY" = false ] || ! env_branches "$repo" "$ENV_NAME" | grep -q "branch:$br"; then
      run gh api -X POST "repos/$OWNER/$repo/environments/$ENV_NAME/deployment-branch-policies" -f "name=$br" -f "type=branch"
    fi
    run gh secret set "$KEY_NAME" --env "$ENV_NAME" --repo "$OWNER/$repo" < "$PEM"
    if ! has_repo_var "$repo"; then
      run gh variable set "$APP_ID_VAR" --repo "$OWNER/$repo" --body "$app_id"
    fi
  done
  if [ "$APPLY" = true ]; then
    echo "== verify"
    for repo in "${REPOS[@]}"; do
      br=$(branch_of "$repo")
      has_env_secret "$repo" "$ENV_NAME" || { echo "$repo: key not in $ENV_NAME" >&2; exit 1; }
      [ "$(env_branches "$repo" "$ENV_NAME")" = "branch:$br" ] || { echo "$repo: $ENV_NAME branches are [$(env_branches "$repo" "$ENV_NAME")], want [branch:$br]" >&2; exit 1; }
      case ",$(env_rules "$repo" "$ENV_NAME")," in *,required_reviewers,*) echo "$repo: $ENV_NAME has required reviewers" >&2; exit 1 ;; esac
      has_repo_var "$repo" || { echo "$repo: repo variable $APP_ID_VAR missing" >&2; exit 1; }
      echo "$repo: ok"
    done
    if [ "$SHRED" = true ]; then shred -u "$PEM" && echo "shredded the key file"; fi
  fi
}

# Every workflow on the default branch that names the key must run that job in environment ci-bot.
workflows_ready() {
  local ok=true
  for repo in "${REPOS[@]}"; do
    br=$(branch_of "$repo")
    for f in $(gh api "repos/$OWNER/$repo/contents/.github/workflows?ref=$br" --jq '.[] | select(.type=="file") | .path'); do
      body=$(gh api "repos/$OWNER/$repo/contents/$f?ref=$br" --jq .content | base64 -d)
      if grep -q "secrets\.$KEY_NAME" <<<"$body" && ! grep -q "environment: $ENV_NAME" <<<"$body"; then
        echo "$repo: $f reads $KEY_NAME outside environment $ENV_NAME on $br" >&2; ok=false
      fi
      if grep -q "secrets\.$KEY_NAME" <<<"$body" && grep -Eq "environment: (release|ci-hygiene)$" <<<"$body"; then
        echo "$repo: $f still names an old environment" >&2; ok=false
      fi
    done
  done
  [ "$ok" = true ]
}

cleanup() {
  if ! workflows_ready; then echo "cleanup refused: merge the workflow PRs first" >&2; exit 1; fi
  for repo in "${REPOS[@]}"; do
    has_env_secret "$repo" "$ENV_NAME" || { echo "cleanup refused: $repo has no key in $ENV_NAME" >&2; exit 1; }
  done
  for entry in "${OLD_COPIES[@]}"; do
    read -r repo env <<<"$entry"
    if [ "$env" = "-" ]; then
      if has_repo_secret "$repo"; then run gh secret delete "$KEY_NAME" --repo "$OWNER/$repo"; fi
    else
      if has_env_secret "$repo" "$env"; then run gh secret delete "$KEY_NAME" --env "$env" --repo "$OWNER/$repo"; fi
    fi
  done
  for entry in "${OLD_VARS[@]}"; do
    read -r repo env <<<"$entry"
    if gh api "repos/$OWNER/$repo/environments/$env/variables" --jq ".variables[].name" 2>/dev/null | grep -qx "$APP_ID_VAR"; then
      run gh variable delete "$APP_ID_VAR" --env "$env" --repo "$OWNER/$repo"
    fi
  done
  if [ "$DELETE_OLD_ENVS" = true ]; then
    for entry in "${OLD_COPIES[@]}"; do
      read -r repo env <<<"$entry"
      [ "$env" = "-" ] && continue
      env_exists "$repo" "$env" || continue
      left=$(gh api "repos/$OWNER/$repo/environments/$env/secrets" --jq '.total_count')
      vars=$(gh api "repos/$OWNER/$repo/environments/$env/variables" --jq '.total_count')
      if [ "$APPLY" = false ] || { [ "$left" = "0" ] && [ "$vars" = "0" ]; }; then
        run gh api -X DELETE "repos/$OWNER/$repo/environments/$env"
      else
        echo "$repo: environment $env still holds $left secret(s) and $vars variable(s); kept"
      fi
    done
  fi
}

case "$CMD" in
  plan) plan ;;
  setup) setup ;;
  cleanup) cleanup ;;
  *) echo "usage: $0 plan | setup --pem FILE [--apply] [--shred] | cleanup [--apply] [--delete-old-envs]" >&2; exit 2 ;;
esac
