#!/usr/bin/env bash
# Can one AWS account serve every Bedrock chat model the AI gateway uses? (S278, AA-1095: checked acc1 before moving
# Bedrock serving off acc3.) Read-only checks (availability, quotas) + ONE Converse call per model with
# maxTokens 5 (about 0.0002 USD each; printed: status and token counts only, never the reply text).
# Run: PROFILE=<aws profile> EXPECT_ACCOUNT=<12-digit id> bash tools/llm/bedrock_account_check.sh  (OpenAI models: MAXTOK=16)
set -uo pipefail
P=${PROFILE:?PROFILE=<aws profile>}
R=${REGION:-us-west-1}
acct=$(aws sts get-caller-identity --profile $P --query Account --output text </dev/null) || { echo "STOP no session for $P"; exit 2; }
[[ $acct == "${EXPECT_ACCOUNT:?EXPECT_ACCOUNT=<12-digit id>}" ]] || { echo "STOP profile $P is account $acct, not $EXPECT_ACCOUNT"; exit 2; }
echo "ACCOUNT $acct REGION $R"
MODELS="${MODELS_ONLY:-anthropic.claude-sonnet-5-5 anthropic.claude-opus-5-5 anthropic.claude-haiku-5-5 anthropic.claude-sonnet-5
openai.gpt-6-luna openai.gpt-5.6-luna openai.gpt-6-astra anthropic.claude-sonnet-4-6 anthropic.claude-opus-4-6-v1
anthropic.claude-haiku-4-5-20251001-v1:0 openai.gpt-6-sol openai.gpt-6.1-sol openai.gpt-6.1-terra}"
for m in $MODELS; do
  av=$(aws bedrock get-foundation-model-availability --model-id "$m" --profile $P --region "$R" \
       --query '[agreementAvailability.status,authorizationStatus,entitlementAvailability,regionAvailability]' --output text </dev/null 2>&1 | tail -1 | tr '\t' '/')
  out=$(aws bedrock-runtime converse --model-id "global.$m" --profile $P --region "$R" \
        --messages '[{"role":"user","content":[{"text":"Reply with the single word OK."}]}]' \
        --inference-config "{\"maxTokens\":${MAXTOK:-5}}" --query '[stopReason,usage.inputTokens,usage.outputTokens]' --output text </dev/null 2>&1 | tail -1)
  case $out in *AccessDenied*|*"not available"*) call="DENIED: ${out:0:140}" ;; *Throttl*|*quota*) call="THROTTLED/QUOTA: ${out:0:140}" ;; *rror*) call="ERROR: ${out:0:160}" ;; *) call="OK $(tr '\t' ' ' <<<"$out")" ;; esac
  printf '%-42s avail=%-40s call=%s\n' "$m" "$av" "$call"
done
echo "== TPM quotas (global cross-region) for these families"
aws service-quotas list-service-quotas --service-code bedrock --profile $P --region "$R" \
  --query "Quotas[?starts_with(QuotaName,'Global cross-region model inference tokens per minute') && (contains(QuotaName,'Claude') || contains(QuotaName,'GPT'))].[QuotaName,Value]" --output text </dev/null 2>&1 | sed 's/Global cross-region model inference tokens per minute for //' | sort
