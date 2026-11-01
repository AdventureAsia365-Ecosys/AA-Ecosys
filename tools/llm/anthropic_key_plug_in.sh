#!/bin/bash
# AA-1026 (I1, S263): plug the Anthropic API key into the Dev AI gateway in ONE command.
# Runbook: docs/ops/runbooks/llm-anthropic-api-key.md (APP-06-anthropic-key). Usage: --help.
#
# Orchestrator only: --apply writes Secrets Manager and calls admin write endpoints (audited). A subagent is refused
# by .claude/hooks/subagent-guardrails.sh (pattern on this script's name), as for every other AWS write.
#
# The key comes on stdin only (a pipe or a file redirect; typed without echo on a terminal). It is never printed, never
# put on a command line (no argv, so not in `ps` or shell history), and only touches disk as a mode-600 file under
# .tmp-session/ that is shredded right after the Secrets Manager call. Every AWS call runs with </dev/null and a
# timeout, so an expired MFA session fails instead of hanging.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: tools/llm/anthropic_key_plug_in.sh --check
       tools/llm/anthropic_key_plug_in.sh --apply < /path/to/key-file      (or: <command> | ... --apply)

--check  ($0, no write) confirm the AWS account is the CIS one, read the anthropic-direct connection from the admin
         API (kind, secret name, policy problems, enabled, monthly budget) and whether the secret exists.
--apply  read the key from stdin, then in this order:
           1. store it in Secrets Manager aa-llm/dev/anthropic-direct (create, or put a new version);
           2. set the connection's monthly budget to 150 USD, hard stop, alert at 80 % (one audited PATCH);
           3. probe: one tiny call of PROBE_MODEL (default haiku-5-5) on anthropic-direct through the gateway's admin
              connection test (works while the connection is off; < 0.001 USD; logged as stage adhoc_conn_test);
           4. only when the probe answered: switch the connection on (one audited PATCH).
         A failed probe leaves the connection off (the secret stays; fix the key and run --apply again).

Environment: AWS_PROFILE_NAME (default aa365-admin), CIS_API (default https://api-cis.lumiguides.it.com),
             PROBE_MODEL (default haiku-5-5), AUDIT_ACTOR (x-admin-user-id of the audit rows, default tech-lead),
             EXPECTED_ACCOUNT (optional 12-digit account; refused when the caller identity differs).
EOF
}

MODE=${1:-}
case $MODE in
  -h | --help) usage; exit 0 ;;
  --check | --apply) ;;
  *) usage >&2; exit 2 ;;
esac

PROFILE=${AWS_PROFILE_NAME:-aa365-admin}
REGION=us-west-1
API=${CIS_API:-https://api-cis.lumiguides.it.com}
SECRET=aa-llm/dev/anthropic-direct
CONN=anthropic-direct
BUDGET_USD=150
ALERT_PCT=80
PROBE_MODEL=${PROBE_MODEL:-haiku-5-5}
ACTOR=${AUDIT_ACTOR:-tech-lead}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
SCRATCH="$ROOT/.tmp-session"

die() { echo "ABORT: $*" >&2; exit 1; }
say() { echo "[anthropic-key] $*"; }
awsq() { timeout 60 aws "$@" --profile "$PROFILE" --region "$REGION" </dev/null; }

# ── 0. the account and the admin credential ─────────────────────────────────────────────────────────────────────
ACCOUNT=$(awsq sts get-caller-identity --query Account --output text) \
  || die "aws sts get-caller-identity failed (MFA expired? run: aws sts get-caller-identity --profile $PROFILE)"
[ -z "${EXPECTED_ACCOUNT:-}" ] || [ "$ACCOUNT" = "$EXPECTED_ACCOUNT" ] \
  || die "caller account is not EXPECTED_ACCOUNT"
awsq secretsmanager describe-secret --secret-id aa-cis/dev/admin-secret --query Name --output text >/dev/null \
  || die "aa-cis/dev/admin-secret not found: this profile is not the CIS account"
say "account: the CIS account (profile $PROFILE)"
ADMIN=$(awsq secretsmanager get-secret-value --secret-id aa-cis/dev/admin-secret --query SecretString --output text) \
  || die "cannot read the admin secret"
[ -n "$ADMIN" ] || die "empty admin secret"

# curl reads the credential header from a process-substitution file: never on the command line.
admin() {  # admin <METHOD> <path> [json body] -> body on stdout, HTTP code on fd 3
  local method=$1 path=$2 body=${3:-}
  local args=(-sS -o /dev/stdout -w '%{stderr}%{http_code}' -X "$method" "$API$path"
              -H "x-admin-role: admin" -H "x-admin-user-id: $ACTOR" -H "content-type: application/json")
  [ -n "$body" ] && args+=(-d "$body")
  curl "${args[@]}" -H @<(printf 'X-Admin-Secret: %s\n' "$ADMIN") --max-time 60
}

call() {  # call <METHOD> <path> [body] -> sets BODY and CODE
  local out err
  err=$(mktemp)
  out=$(admin "$@" 2>"$err") || true
  CODE=$(tail -c 3 "$err"); rm -f "$err"
  BODY=$out
}

field() {  # field <python expression over d> : reads BODY as JSON
  python3 -c 'import json,sys; d=json.loads(sys.stdin.read() or "{}"); print(eval(sys.argv[1]))' "$1" <<<"$BODY"
}

# ── 1. the connection as the admin API sees it ($0) ─────────────────────────────────────────────────────────────
call GET /admin/llm-connections
[ "$CODE" = 200 ] || die "GET /admin/llm-connections answered $CODE"
STATE=$(python3 -c '
import json, sys
d = json.loads(sys.stdin.read())
c = next((c for c in d.get("connections", []) if c.get("connection_key") == sys.argv[1]), None)
if c is None:
    print("missing")
else:
    print("kind=%s secret=%s problems=%s enabled=%s budget=%s hard_stop=%s alert=%s" % (
        c.get("kind"), c.get("secret_name"), len(c.get("policy_problems") or []), c.get("enabled"),
        c.get("monthly_budget_usd"), (c.get("cost_policy") or {}).get("hard_stop"),
        (c.get("cost_policy") or {}).get("alert_pct")))
' "$CONN" <<<"$BODY")
say "connection $CONN: $STATE"
case $STATE in
  "kind=anthropic secret=$SECRET problems=0 "*) ;;
  *) die "connection $CONN is not kind anthropic with secret $SECRET and no policy problem" ;;
esac
if awsq secretsmanager describe-secret --secret-id "$SECRET" --query Name --output text >/dev/null 2>&1; then
  HAVE_SECRET=1; say "secret $SECRET exists (value not read)"
else
  HAVE_SECRET=0; say "secret $SECRET does not exist yet"
fi
[ "$MODE" = --check ] && { say "check done (no write)"; exit 0; }

# ── 2. the key from stdin, checked, never shown ─────────────────────────────────────────────────────────────────
KEY=""
if [ -t 0 ]; then
  IFS= read -rs -p "Anthropic API key (not shown): " KEY || true; echo
else
  IFS= read -r KEY || true
fi
KEY=${KEY//$'\r'/}
KEY=${KEY#"${KEY%%[![:space:]]*}"}; KEY=${KEY%"${KEY##*[![:space:]]}"}
case $KEY in
  sk-ant-*) ;;
  *) die "the key on stdin does not start with the Anthropic prefix (sk-ant-)" ;;
esac
[[ $KEY =~ ^[A-Za-z0-9_-]+$ ]] || die "the key has characters outside [A-Za-z0-9_-] (pasted with text around it?)"
rest=${KEY#sk-ant-}
[[ $rest == *sk-ant-* ]] && die "the key holds the prefix twice (pasted more than once?)"
{ [ ${#KEY} -ge 60 ] && [ ${#KEY} -le 250 ]; } || die "the key length (${#KEY}) is not an Anthropic key's"
say "key read from stdin (${#KEY} characters, not shown)"

# ── 3. Secrets Manager ──────────────────────────────────────────────────────────────────────────────────────────
mkdir -p "$SCRATCH"
TMP=$(umask 077; mktemp "$SCRATCH/anthropic-key.XXXXXX")
trap 'shred -u "$TMP" 2>/dev/null || rm -f "$TMP"' EXIT
printf '%s' "$KEY" >"$TMP"
KEY=""
if [ "$HAVE_SECRET" = 1 ]; then
  awsq secretsmanager put-secret-value --secret-id "$SECRET" --secret-string "file://$TMP" \
    --query VersionId --output text >/dev/null || die "put-secret-value failed"
  say "secret $SECRET: new version stored"
else
  awsq secretsmanager create-secret --name "$SECRET" --secret-string "file://$TMP" \
    --description "Anthropic API key of the Dev AI gateway (connection anthropic-direct, AA-1026)" \
    --query Name --output text >/dev/null || die "create-secret failed"
  say "secret $SECRET: created"
fi
shred -u "$TMP" 2>/dev/null || rm -f "$TMP"

# ── 4. the budget before anything can spend: 150 USD a month, hard stop, alert 80 % ──────────────────────────────
call PATCH "/admin/llm-connections/$CONN" \
  "{\"monthly_budget_usd\": $BUDGET_USD, \"budget_hard_stop\": true, \"budget_alert_pct\": $ALERT_PCT}"
[ "$CODE" = 200 ] || die "budget PATCH answered $CODE: $(field 'd.get("detail")')"
say "budget: $BUDGET_USD USD a month, hard stop, alert at $ALERT_PCT % (changed: $(field 'd.get("changed_fields")'))"

# ── 5. probe while the connection is still off ──────────────────────────────────────────────────────────────────
call POST "/admin/llm-connections/$CONN/test" "{\"model_key\": \"$PROBE_MODEL\", \"max_tokens\": 16}"
[ "$CODE" = 200 ] || die "connection test answered $CODE: $(field 'd.get("detail")') (connection left off)"
OK=$(field 'd.get("ok") is True and d.get("reply_usable") is not False')
say "probe: $(field '{k: d.get(k) for k in ("model_key", "wire_id", "ok", "reply_usable", "error_class", "cost_usd", "latency_ms")}')"
[ "$OK" = True ] || die "probe failed ($(field 'd.get("error_class")')): connection left OFF; see the runbook table"

# ── 6. switch on ────────────────────────────────────────────────────────────────────────────────────────────────
call PATCH "/admin/llm-connections/$CONN" '{"enabled": true}'
[ "$CODE" = 200 ] || die "enable PATCH answered $CODE: $(field 'd.get("detail")')"
[ "$(field 'd.get("enabled")')" = True ] || die "the connection did not report enabled=true"
say "connection $CONN: ON (api now; worker within 5 minutes). Ledger row: stage adhoc_conn_test, account $CONN."
say "next: set last_tested / tested_where / tested_evidence in the runbook front-matter"
