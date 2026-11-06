#!/usr/bin/env bash
# Run ONE command as the org's GitHub App `aa-agent` (ADR 0011, AA-901).
#
#   tools/github/as-app.sh [--repos AA-CIS-App,AA-Booking] -- <command> [args...]
#
# Examples:
#   tools/github/as-app.sh -- gh api /installation/repositories --jq '.repositories[].name'
#   tools/github/as-app.sh --repos AA-Booking -- gh pr create --repo AdventureAsia365-Ecosys/AA-Booking --fill
#   tools/github/as-app.sh -- git push -u origin <branch>      # needs `gh auth setup-git` once
#
# What it does: reads the App private key from Secrets Manager (acc2) into memory, signs a 9-minute App JWT with
# openssl, finds the org installation, mints a 1-hour installation token (optionally narrowed to --repos) and runs
# the command with that token in GH_TOKEN. The token and the key are never printed or written to disk.
#
# Config: tools/github/apps.env (non-secret IDs). Needs: aws (MFA session for the profile), openssl, curl, python3.
# Setup and rotation: docs/security/github-apps.md. Subagents stay blocked by the guardrail hook whatever token
# they hold: this helper changes the identity, not the permission to push or merge.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$here/apps.env"

repos=""
while [ $# -gt 0 ]; do
  case "$1" in
    --repos) repos="${2:?--repos needs a comma-separated list}"; shift 2 ;;
    --) shift; break ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "as-app: unknown option $1 (put the command after --)" >&2; exit 2 ;;
  esac
done
[ $# -gt 0 ] || { echo "as-app: no command given (usage: as-app.sh [--repos a,b] -- <command>)" >&2; exit 2; }
# AA-1024: a merge only after the ship gate (every check green, not only required ones; DIRTY / draft / base /
# deletion refusals). ship_merge.py sets AA_SHIP_GATED once a PR passed it; ship_wave.py and mergeq.sh run under it.
# `gh pr merge --disable-auto` (mergeq.sh --dequeue) stays open: it takes a PR out, never in.
if [ "$(basename -- "$1")" = gh ] && [ "${2:-}" = pr ] && [ "${3:-}" = merge ] && [ -z "${AA_SHIP_GATED:-}" ]; then
  case " $* " in
    *" --disable-auto "*) ;;
    *) echo "as-app: refused a raw 'gh pr merge' (it skips the ship gate). Use tools/github/ship_merge.py <Repo>#<pr>, or tools/github/ship_wave.py for a wave." >&2; exit 2 ;;
  esac
fi
# The same merge through the API (S271 review: `gh api -X PUT repos/<org>/<repo>/pulls/<n>/merge` ran 3 times): the
# REST merge endpoint with a writing method, or a GraphQL mergePullRequest / enqueuePullRequest mutation (also from a
# `-F query=@file` / `--input file` body). A GET of pulls/<n>/merge (is it merged?) and dequeuePullRequest stay open.
if [ "$(basename -- "$1")" = gh ] && [ "${2:-}" = api ] && [ -z "${AA_SHIP_GATED:-}" ]; then
  method="" fields="" rest_merge="" gql_merge="" prev=""
  for a in "${@:3}"; do
    case "$prev" in
      -X|--method) method="$a" ;;
      --input) [ -r "$a" ] && grep -qE 'mergePullRequest|enqueuePullRequest' -- "$a" && gql_merge=1 ;;
    esac
    case "$a" in
      -X?*) method="${a#-X}" ;;
      --method=*) method="${a#--method=}" ;;
      -f|-F|--field|--raw-field|--input|-f?*|-F?*|--field=*|--raw-field=*|--input=*) fields=1 ;;
    esac
    case "$a" in
      *pulls/*/merge|*pulls/*/merge/|*pulls/*/merge\?*) rest_merge=1 ;;
      *mergePullRequest*|*enqueuePullRequest*) gql_merge=1 ;;
    esac
    case "$a" in
      *=@*) f="${a#*=@}"; [ -r "$f" ] && grep -qE 'mergePullRequest|enqueuePullRequest' -- "$f" && gql_merge=1 ;;
    esac
    prev="$a"
  done
  method="$(printf '%s' "$method" | tr '[:lower:]' '[:upper:]')"
  if [ -n "$rest_merge" ] && { [ -n "$method" ] && [ "$method" != GET ] || { [ -z "$method" ] && [ -n "$fields" ]; }; }; then
    gql_merge=1
  fi
  if [ -n "$gql_merge" ]; then
    echo "as-app: refused a merge through 'gh api' (REST pulls/<n>/merge or GraphQL mergePullRequest/enqueuePullRequest skips the ship gate). Use tools/github/ship_merge.py <Repo>#<pr>, or tools/github/ship_wave.py for a wave." >&2; exit 2
  fi
fi
[ -n "${agent_app_id:-}" ] || { echo "as-app: agent_app_id is empty in $here/apps.env (App not created yet?)" >&2; exit 1; }

b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }

key="$(aws secretsmanager get-secret-value --secret-id "$agent_key_secret" --query SecretString --output text --profile "$key_profile" --region "$key_region" </dev/null)" || { echo "as-app: cannot read $agent_key_secret (MFA expired? run: aws sts get-caller-identity --profile $key_profile)" >&2; exit 1; }
case "$key" in *"PRIVATE KEY-----"*) ;; *) echo "as-app: $agent_key_secret does not hold a PEM private key" >&2; exit 1 ;; esac

now=$(date +%s)
header=$(printf '{"alg":"RS256","typ":"JWT"}' | b64url)
payload=$(printf '{"iat":%d,"exp":%d,"iss":"%s"}' $((now - 60)) $((now + 540)) "$agent_app_id" | b64url)
signature=$(printf '%s.%s' "$header" "$payload" | openssl dgst -sha256 -binary -sign <(printf '%s\n' "$key") | b64url)
jwt="$header.$payload.$signature"
unset key

api="https://api.github.com"
hdr=(-H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28")

install_id=$(curl -fsS "${hdr[@]}" -H "Authorization: Bearer $jwt" "$api/orgs/$github_org/installation" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])') || { echo "as-app: the App has no installation on $github_org (install it first)" >&2; exit 1; }

body='{}'
if [ -n "$repos" ]; then
  body=$(python3 -c 'import json,sys; print(json.dumps({"repositories": [r.strip() for r in sys.argv[1].split(",") if r.strip()]}))' "$repos")
fi
token=$(curl -fsS -X POST "${hdr[@]}" -H "Authorization: Bearer $jwt" -d "$body" "$api/app/installations/$install_id/access_tokens" | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])') || { echo "as-app: token request refused (repo not in the installation?)" >&2; exit 1; }
unset jwt

GH_TOKEN="$token" GITHUB_TOKEN="$token" exec "$@"
