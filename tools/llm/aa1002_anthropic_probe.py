"""AA-1002 (LLM gateway slice S2): one tiny probe of the Anthropic API connection through LLMClient.

Runbook: docs/ops/runbooks/llm-anthropic-api-key.md (APP-06-anthropic-key). Cost well under $0.001 (Haiku 5.5,
about 30 tokens in, a few out).

Runs inside the CIS worker (or api) container, through tools/ecs/ecsx.sh (or the S3-mediated ECS exec pattern):
python3, the container's DATABASE_URL (cis_app) and task role (Secrets Manager read of aa-llm/dev/anthropic-direct).
No AWS write, and no DB write other than the one shared.llm_call_log row (stage adhoc_aa1002, role validate) that
the ad-hoc-script rule requires (a billed but unusable reply is logged by the gateway itself).

The model_tier pins the deployment "<model>@anthropic-direct", so no stage route changes: the probe works only when
the anthropic-direct connection is enabled (admin PATCH) and its seeded deployment (CIS migration 306) is enabled.

Env: PROBE_MODEL (default haiku-5-5), PROBE_CONNECTION (default anthropic-direct).
Prints one JSON line: {"ok": true, ...} or {"ok": false, "error_type": ..., "llm_error_class": ...}; exit 1 on error.
"""
import json
import os
import sys

sys.path.insert(0, "/app")

from shared.llm_client.call_log import record_call_sync  # noqa: E402
from shared.llm_client.client import LLMClient  # noqa: E402
from shared.llm_client.models import LLMRequest  # noqa: E402

STAGE = "adhoc_aa1002"
MODEL = os.environ.get("PROBE_MODEL", "haiku-5-5")
CONNECTION = os.environ.get("PROBE_CONNECTION", "anthropic-direct")

request = LLMRequest(system_prompt="You are a connectivity probe. Follow the instruction exactly.",
                     user_prompt="Reply with the single word OK.", model_tier=f"{MODEL}@{CONNECTION}",
                     stage=STAGE, max_tokens=200)
try:
    resp = LLMClient().generate(request)
except Exception as e:  # noqa: BLE001 - report and exit non-zero; a billed-unusable reply was already logged
    print(json.dumps({"ok": False, "error_type": type(e).__name__, "error": str(e)[:500],
                      "llm_error_class": getattr(e, "llm_error_class", None)}))
    sys.exit(1)

# provider_model (the model the API says answered) does not reach llm_call_log for ordinary callers before slice
# S6; the probe keeps it in quality_signal as the evidence of what really ran.
record_call_sync(stage=STAGE, role="validate", model=resp.model_used, tokens_in=resp.input_tokens,
                 tokens_out=resp.output_tokens, cost_usd=resp.cost_usd,
                 quality_signal={"probe": "aa1002_anthropic_key", "connection": CONNECTION,
                                 "provider_model": resp.provider_model},
                 stop_reason=resp.stop_reason, provider=resp.provider)
print(json.dumps({"ok": resp.content.strip().upper().startswith("OK"), "content": resp.content[:40],
                  "model_used": resp.model_used, "provider": resp.provider, "provider_model": resp.provider_model,
                  "tokens_in": resp.input_tokens, "tokens_out": resp.output_tokens, "cost_usd": resp.cost_usd,
                  "stop_reason": resp.stop_reason}))
