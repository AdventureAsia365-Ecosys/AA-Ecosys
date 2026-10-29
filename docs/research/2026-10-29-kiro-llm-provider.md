# AA-999: Can backend LLM calls go through Kiro?

Research note, S257, 29/10/2026. Author: Claude Code (research subagent). Read-only: no code, infra or paid calls.
Scope: whether the CIS pipeline (`shared/llm_client`, cost rows in `shared.llm_call_log`) can send its LLM calls
through the team's Kiro subscription instead of Bedrock on acc3, and whether that would be cheaper or more reliable.


> **Update 29/10 15:2x (orchestrator probe):** the open question about Claude is settled — every Bedrock model on acc3, Claude included (`us.`/`global.` Sonnet 4.5 profiles), now returns "Error 002: Access to Bedrock models is not allowed for this account"; the default payment method on acc3 is set. Fixing acc3 access through AWS Support is step 1 of the recommendation.
---

## Summary and recommendation

**Recommendation: do not use Kiro for backend or pipeline inference.** Keep Kiro as a developer tool (IDE, CLI, CI
reviews), which is what it is sold and licensed for. Restore the production path through one of the alternatives in
Finding 6, in this order: (1) fix acc3's billing and Bedrock access; (2) top up the OpenAI API for the cheap judge
models, which is already wired in (`api_style = openai_chat`); (3) a direct Anthropic API account as the Claude
fallback, which needs a data-governance decision first.

Why not Kiro:

1. **The terms do not allow it.** Kiro's own pricing FAQ allows subscriptions in Kiro's IDE, CLI, Web, Crew,
   ACP-compatible IDEs and "automation in software development (ex: reviews during CI/CD)". It also says that use
   "through third-party automation harnesses (such as OpenClaw)" that "route requests outside of Kiro's native
   interfaces is not permitted", and that "each developer needs their own subscription". A FastAPI worker that runs
   `kiro-cli` to rewrite catalogue tours or judge tenant content is not software-development automation. It is a
   harness that turns a per-developer seat into an inference API. ([pricing FAQ](https://kiro.dev/pricing/))
2. **There is no inference API.** Kiro offers only an *agent*: `kiro-cli chat --no-interactive` (headless, API key)
   or `kiro-cli acp` (JSON-RPC over stdio for editors). There is no documented call that takes a system prompt plus a
   JSON schema plus `max_tokens` and returns token usage. A custom agent's `prompt` field acts "similar to a system
   prompt", but the docs do not say whether it replaces Kiro's built-in agent prompt or is layered on top; either way
   there is no documented temperature, seed, schema or `max_tokens` control, which breaks the calibrated judge and
   writer prompts (the AA-919 kappa work, the S1 v2 writer).
3. **Cost is unknown and probably higher.** Kiro bills "by request, not by token" in credits, at $0.04 per add-on
   credit, metered to 0.01 credit. It publishes no token-to-credit mapping. On our 30-day volume, Kiro breaks even
   with Bedrock only if the average call costs ≤ ~0.10 credit (arithmetic below). One agent turn carrying a Kiro
   system prompt is unlikely to stay that low. For the cheap judge calls (gpt-5.6-luna), Kiro's 0.01-credit floor
   alone ($0.0004) is already about half the list price of a whole call (Bedrock price assumed equal to list).
4. **Reliability gains are small.** Kiro runs on AWS's own Bedrock, separate from acc3, so an acc3 billing problem
   would not stop it. But it has no published rate limits, it pauses at the monthly credit cap until reset or
   top-up, it is tied to one person's account and long-lived API key, and pipeline traffic would use up the credits
   the developers need for coding.

**Use only for:** human-in-the-loop development work in a developer's own Kiro session (as today, under
`kiro-delegate`). Never a route in `shared.llm_role_config`.

---

## Findings

### 1. Programmatic access and authentication

| Surface | What it is | Unattended server use? |
|---|---|---|
| Headless mode: `kiro-cli chat --no-interactive "<prompt>"` | The CLI agent runs one task with no TTY. Output is plain text or JSON Lines (`--output-format stream-json`, V2/V3). `--model <id>` and `--effort` pick the model. Tools are pre-approved with `--trust-all-tools` / `--trust-tools=…` | Technically yes. The docs aim it at "your CI/CD pipeline" (code reviews, test generation, build-failure triage). ([headless](https://kiro.dev/docs/cli/headless/)) |
| ACP: `kiro-cli acp` | JSON-RPC 2.0 over stdin/stdout (`initialize`, `session/new`, `session/prompt`, `session/set_model`…) | Built for editor clients (JetBrains, Zed). Server use is not discussed. ([ACP](https://kiro.dev/docs/cli/acp/)) |
| HTTP / SDK inference API | None documented | Not found. The billing FAQ does not mention API usage ([billing FAQ](https://kiro.dev/docs/billing/related-questions/)) |

Authentication:
- Headless needs an API key in `KIRO_API_KEY`. Keys are created at app.kiro.dev, exist only on Pro, Pro+, Pro Max
  and Power, and are "long-lived credentials". An admin must enable key generation for managed subscriptions. Keys
  can be revoked in the console. Credits used with a key "are deducted from the subscription's credits".
  ([authentication](https://kiro.dev/docs/getting-started/authentication/))
- The key is a **user credential**: it belongs to one subscriber's account, and that account's governance rules
  apply to headless sessions ([headless](https://kiro.dev/docs/cli/headless/)). There is no service or machine
  identity, and no IAM role.
- **Not confirmed:** key expiry, per-key scopes, and whether `stream-json` reports token counts or credits used per
  run. None of these is documented.

### 2. Terms: can a per-user subscription serve backend inference?

- **Allowed surfaces:** "Kiro IDE, Kiro CLI, Kiro Web, Kiro Crew, ACP compatible IDEs, and automation in software
  development (ex: reviews during CI/CD)". ([pricing FAQ](https://kiro.dev/pricing/),
  [billing FAQ](https://kiro.dev/docs/billing/related-questions/))
- **Explicit restriction:** use "through third-party automation harnesses (such as OpenClaw)" that "route requests
  outside of Kiro's native interfaces is not permitted". ([pricing FAQ](https://kiro.dev/pricing/))
- **Seats:** "For team usage, each developer needs their own subscription." ([pricing FAQ](https://kiro.dev/pricing/))
- **Contract:** Kiro is an AI Service under the AWS Service Terms. §50.1 lists Kiro. §50.14.1 makes Amazon Web
  Services, Inc. the contracting party for subscriptions bought through the Stripe portal. §50.14.2 applies Bedrock
  abuse detection. ([AWS Service Terms](https://aws.amazon.com/service-terms/))
- **Data use (matters for tenant content):** for Free Tier and *individual subscribers* (social login or Builder
  ID), "subject to your opt out, content may be used for service improvement". Enterprise content is not used.
  Individual subscribers' content is stored in us-east-1. Inference uses cross-region routing, global for GPT-5.6.
  Opting out does not stop Bedrock abuse detection: AWS Service Terms §50.14.2 applies it to all Kiro use, "including
  our retention and potential human review of inputs and outputs when you select certain models" (Free Tier inputs
  kept up to 60 days).
  ([data protection](https://kiro.dev/docs/privacy-and-security/data-protection/); AWS Service Terms §50.3, §50.14.2)
- **Assessment:** a pipeline that serves product content, including tenant content, through a developer's seat is
  outside "automation in software development". Wrapping `kiro-cli` in a worker so the backend has an inference
  endpoint matches the "harness … outside of Kiro's native interfaces" restriction. **Not permitted, in our
  reading.** Nothing found in the AWS terms permits it explicitly. This is our interpretation, not a statement from
  AWS. Ask AWS / Kiro support if anyone wants a formal answer.

### 3. Models and limits

- **Plans** ([pricing](https://kiro.dev/pricing/)): Free $0 / 50 credits; Pro $20 / 1,000; Pro+ $40 / 2,000;
  Pro Max $100 / 5,000; Power $200 / 10,000. Add-on credits cost $0.04 each (packs from $5 for 125 credits). Unused
  monthly credits do not roll over. Add-on credits expire after 12 months. Enterprise overage is disabled by default.
- **Metering** ([billing FAQ](https://kiro.dev/docs/billing/related-questions/)): "Credits are metered to the second
  decimal point" (minimum 0.01). "You pay by request, not by token". A large context or output can count as more than
  one credit. When credits run out, requests pause until the monthly reset unless add-ons are bought.
- **Model multipliers vs Auto = 1.0x** ([models](https://kiro.dev/docs/models/)): Claude Sonnet 5.5 1.3x; Opus 5.5
  2.0x; Haiku 5.5 0.06x (0.3x above 100K tokens); Haiku 4.5 0.4x; GPT-5.6 Luna 0.6x (1.2x above 272K); GPT-5.6 Terra
  2.2x (4.4x above 272K); Sol 4.4x (8.8x above 272K). Claude Fable 5.1 6x (Enterprise only). Open-weight models
  from 0.05x (Qwen3 Coder Next) to 2.4x (Kimi K3); DeepSeek 3.2 / MiniMax M2.5 0.25x, GLM-5 0.5x.
  **gpt-6-luna is not offered.** GPT-5.6 uses global cross-region inference; most other models stay in the US or EU
  geography.
- **Rate limits:** not published for paid plans. The billing FAQ describes only monthly caps. The Free tier is
  "subject to rate limits" with no numbers. **Not confirmed.**
- **Missing controls that our gateway needs** (none documented): `json_schema` / forced tool, `temperature`, `seed`,
  `max_tokens`, prompt-cache control, per-call token usage.

### 4. Cost on our volumes (arithmetic)

Inputs:
- From the brief: last 30 days ≈ **$249** across ≈ **68,000 calls**, so $0.00366 per call on average. Most of it is S1
  rewrite waves on Sonnet 5.5. The baseline outside waves is ≈ $1–5/day for a few thousand calls a day.
- **Assumption, not measured:** of the $249, about $212 (85%) is Sonnet 5.5 writer calls (≈15,000 calls, ≈ $0.014
  each, roughly 3K tokens in and 0.8K out at $2/$10 per MTok). The rest is ≈53,000 small judge or validator calls
  (luna / Haiku) costing ≈ $37. Replace these with the real split; the query is under Open questions.
- Token list prices (per MTok, in/out). Claude Sonnet 5.5: $2 / $10. Haiku 4.5: $1 / $5. Haiku 5.5: $0.10 / $0.50
  (first-party list, [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing)). Anthropic's
  Bedrock page says global endpoints carry "no pricing premium" and regional endpoints a 10% premium over global
  ([Claude in Amazon Bedrock](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock#regions));
  it does not state that the Bedrock global price equals the first-party list. gpt-5.6-luna: $0.20 / $1.20.
  gpt-6-luna: $0.10 / $0.50 ([OpenAI pricing](https://developers.openai.com/api/docs/pricing)). Bedrock's page did not
  show numbers for these models in the fetched text ([Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)), so
  Bedrock = list is our catalog's working assumption (migration 259), not confirmed.

**Kiro formula:** monthly cost = $20 (Pro) + max(0, credits − 1,000) × $0.04. Credits = Σ calls × c × multiplier,
where c is the Auto-equivalent credits one headless call consumes. **c is unknown and must be measured.**

- **Break-even, whole volume:** $249 = 20 + (credits − 1,000) × 0.04, so credits = 6,725 a month. Spread over 68,000
  calls, that is **0.099 credit per call**.
- **Break-even, Sonnet writer call:** Bedrock costs $0.014 per call; Kiro costs c × 1.3 × $0.04 = $0.052c. So
  **c ≤ 0.27**.
- **Break-even, luna judge call:** a typical 2K-in / 0.3K-out call costs 2,000 × 0.20/1e6 + 300 × 1.20/1e6 =
  **$0.00076** on Bedrock or the OpenAI API. On Kiro the floor of 0.01 credit costs $0.0004. At c = 0.1 the call
  costs 0.1 × 0.6 × 0.04 = **$0.0024**, about 3x more.

### Cost table (30-day wave month, 68K calls)

| Provider | Arithmetic | ≈ Monthly | Notes |
|---|---|---|---|
| Bedrock on-demand (acc3), today | measured in `llm_call_log` | **$249** | Paid from AWS Lift credit (~$250 left, until 31/12/2026) |
| Direct Anthropic API (Claude part) + OpenAI API (judges) | same token list prices | **≈ $249** | Same list prices. Anthropic Batch API is −50% on input and output, so if S1 waves ran as batches: 212 × 0.5 + 37 ≈ **$143** |
| Bedrock batch (if available for these models) | −50% on supported models | ≈ $143 | Bedrock says batch is 50% off for "select models"; Sonnet 5.5 eligibility not confirmed. The new Messages-API surface ("Claude in Amazon Bedrock") lists Message Batches as not supported, so this would have to be Bedrock's own batch-inference jobs. The repo already has `bedrock_batch.py` |
| Kiro Pro, c = 0.05 (optimistic, near the floor; judge multiplier averaged at 0.5, an assumption between Haiku 5.5 0.06x and luna 0.6x) | 15K × 0.05 × 1.3 = 975; 53K × 0.05 × 0.5 = 1,325; total 2,300 credits; 20 + 1,300 × 0.04 | **$72** | Only if a headless turn is almost free. Unlikely with Kiro's own agent prompt; not allowed by the terms anyway |
| Kiro Pro, c = 0.2 | 3,900 + 5,300 = 9,200 credits; 20 + 8,200 × 0.04 | **$348** | |
| Kiro Pro, c = 1.0 ("simple prompt" ≈ 1 credit) | 19,500 + 26,500 = 46,000 credits; 20 + 45,000 × 0.04 | **$1,820** | |

Baseline month without waves (≈ $1–5/day, about 90K mostly small calls): Bedrock ≈ **$30–150**. Kiro at c = 0.1
(0.5 average multiplier) ≈ 90,000 × 0.05 = 4,500 credits, so 20 + 3,500 × 0.04 = **$160**. Kiro at c = 0.2 ≈ **$340**.

**Conclusion:** Kiro is cheaper only if a headless agent turn averages under ~0.1 credit. For the judge-heavy
baseline it is more expensive even at modest c. The cheapest real lever is batch pricing (Anthropic or Bedrock) for
the S1 waves, plus the luna models for judges.

### 5. Integration path (hypothetical, for completeness; not recommended)

How the gateway is built today (`apps/AA-CIS-App/shared/llm_client/client.py`):
- `LLMClient.generate()` → `_generate()` resolves the stage route (`shared.llm_role_config`: `model_id` +
  `fallback_model_ids`) and runs `_call_route()`. That walks the chain and skips disabled catalog rows (`enabled`,
  `blocked_reason`).
- `_call_catalog_model()` dispatches on `shared.llm_model_catalog.api_style`: `converse` →
  `_call_bedrock_converse()` (acc3 satellite); `openai_chat` → `_call_openai()`. Anything else raises.
- Each attempt returns `LLMResponse` (`content`, `model_used`, `provider`, `input_tokens`, `output_tokens`,
  `cost_usd`, `stop_reason`, `provider_requests`…). Costs come from `pricing.calc_cost()` using catalog `price_*`
  columns. `_call_key_logged()` / `call_log.py` write `shared.llm_call_log` rows, including billed-but-unusable
  replies (AA-927).

A Kiro provider would need:
1. A new `api_style = 'kiro_headless'` branch in `_call_catalog_model()` that runs `kiro-cli chat --no-interactive
   --output-format stream-json --model <id>` with no tools pre-approved (whether `--trust-tools=` with an empty list
   is accepted is not documented) as a subprocess, with `KIRO_API_KEY` read from
   Secrets Manager.
2. The `kiro-cli` binary in the api/worker images, outbound internet from the tasks, and one process per call.
   Latency and concurrency are unknown.
3. Structured output by prompt instruction only, checked by `_checked_json`. No forced tool, temperature, seed or
   `max_tokens`.
4. Cost rows: `cost_usd` = credits × $0.04, **if** the stream reports credits (not confirmed). Otherwise only the
   subscription's monthly total is known, which breaks per-stage and per-tour cost reporting and the
   `shared.spend_budget` hard stops.
5. Fallback and kill switch: an ordinary catalog row (`enabled = false` disables it at once) listed only in
   `fallback_model_ids`.

Items 2–4 conflict with how the gateway works now (deterministic prompts, schema enforcement, per-call cost), and the
terms rule out the whole path.

### 6. Alternatives

| Option | Status | Cost | Effort | Risks / notes |
|---|---|---|---|---|
| **Fix acc3 Bedrock access** | acc3 left its AWS Organization at 06:50 UTC on 29/10 (CloudTrail). Since then the OpenAI-on-Bedrock models (gpt-5.6-luna, gpt-6-luna) return AccessDenied, while Claude on acc3 still answered at the S257 close (`docs/backlog/README.md` §1). The brief quotes "Error 002: Access to Bedrock models is not allowed for this account"; whether that covers Claude too is **not confirmed** here. Action: add a valid payment method on the now-standalone account, then probe one call per model; ask the reseller why acc3 left, and open an AWS Support case if access does not return | Unchanged ($249 / wave month; Lift credit until 31/12) | Low, no code | Depends on reseller / AWS; credit ends 31/12/2026, then card billing |
| **OpenAI API top-up** (judges) | Already integrated (`openai_chat`, catalog key `gpt-6-luna-openai`); answers 429 for lack of credits | gpt-6-luna $0.10 / $0.50, gpt-5.6-luna $0.20 / $1.20 per MTok; judge volume is a few $ a month. Batch −50% | Very low: top up, then probe | Content leaves AWS (S235 rule: last resort only). Needs the tech lead's approval |
| **Direct Anthropic API** (separate account, card) | Not integrated | First-party list: Sonnet 5.5 $2 / $10, Haiku 5.5 $0.10 / $0.50 (prompts ≤100K; $0.50 / $2.50 above); Batch API −50%; `inference_geo: "us"` adds 1.1x | Medium: new `api_style` (Messages API) + secret + catalog rows; reuse the cost path | Start tier: $500/month spend cap, 1,000 RPM, 2M ITPM for Sonnet 5.5. New orgs may start in a lower Evaluation tier ([rate limits](https://platform.claude.com/docs/en/api/rate-limits)). Commercial API data is not used for training by default ([privacy](https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training)). Leaving AWS needs a governance or ADR note. "Claude Platform on AWS" bills through AWS Marketplace, so it would need a payer that allows Marketplace (not checked) |
| **Bedrock on acc2** | Blocked by acc2's payer (TrueIDC) for these LLMs (memory "Why LLMs run on acc3") | List | None, unless the payer changes | Not available |
| **Kiro** | See above | Unknown; break-even ≈ 0.1 credit per call | Medium–high | Terms, no API, no per-call cost, user-bound key |

---

## Risks (if Kiro were used anyway)

- **Terms breach:** suspension of the developer's Kiro account, which would cut off the coding tool as well as the
  pipeline.
- **Data:** individual-subscriber content can be used for service improvement unless every key owner opts out.
  Content is stored in us-east-1, and GPT-5.6 is routed globally. Tenant content would go there.
- **Quality drift:** Kiro's agent system prompt wraps ours, and temperature, seed and schema cannot be controlled.
  The calibrated judges (AA-919, AA-790) would become invalid.
- **Cost blindness:** no per-call tokens or cost, so `llm_call_log`, `/admin` cost views, wave reports and
  `spend_budget` hard stops would lose accuracy.
- **Availability:** a monthly credit cap pauses calls. Rate limits are unpublished. One person's account and key is
  a single point of failure. Developers and pipeline would compete for the same credits.
- **Kill switch, had it been built:** `UPDATE shared.llm_model_catalog SET enabled = false` on the Kiro row
  (`_call_route` skips disabled rows), plus revoking the API key in the Kiro console.

## Open questions

1. Real 30-day split for the cost model: calls, tokens and cost per model and stage. Read-only query for the
   container DSN:
   `select model_used, stage, count(*), sum(tokens_in), sum(tokens_out), round(sum(cost_usd)::numeric,2) from shared.llm_call_log where created_at > now() - interval '30 days' group by 1,2 order by 6 desc;`
   (check the column names in `docs/architecture/db-schema-reference.md` first).
2. Does the "Error 002" also hit Claude on acc3, or only the OpenAI models? A one-call probe per model through
   `LLMClient.generate()` with an `adhoc_` stage is the S258 plan.
3. Are Claude Sonnet 5.5 and the luna models eligible for Bedrock batch inference at −50% on acc3? (Not confirmed;
   the repo has `bedrock_batch.py`.)
4. If anyone wants a formal ruling on Kiro for backend use: ask Kiro / AWS support. (Not needed for the
   recommendation.)
5. Kiro headless per-run credit reporting and rate limits: not documented. Only matters if the terms ever change.

## Sources

- Kiro pricing and FAQ (plans, $0.04 add-on, allowed surfaces, harness restriction, per-developer seats): https://kiro.dev/pricing/
- Kiro billing FAQ (0.01 metering, "pay by request, not by token", caps): https://kiro.dev/docs/billing/related-questions/
- Kiro headless mode: https://kiro.dev/docs/cli/headless/
- Kiro authentication / API keys: https://kiro.dev/docs/getting-started/authentication/
- Kiro ACP: https://kiro.dev/docs/cli/acp/
- Kiro models and credit multipliers: https://kiro.dev/docs/models/
- Kiro data protection: https://kiro.dev/docs/privacy-and-security/data-protection/
- AWS Service Terms §1.24, §50.1, §50.3, §50.10, §50.14: https://aws.amazon.com/service-terms/
- Amazon Bedrock pricing (batch −50% for select models; per-model numbers not shown in the fetched text): https://aws.amazon.com/bedrock/pricing/
- Anthropic pricing (Sonnet 5.5, Haiku 5.5 / 4.5, batch, Bedrock global vs regional): https://platform.claude.com/docs/en/about-claude/pricing
- Anthropic API rate limits and spend tiers: https://platform.claude.com/docs/en/api/rate-limits
- Anthropic commercial data use: https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training
- OpenAI API pricing (gpt-5.6-luna, gpt-6-luna): https://developers.openai.com/api/docs/pricing
- Repo: `apps/AA-CIS-App/shared/llm_client/{client.py,models.py,pricing.py}`; `infra/AA-CIS-Infra/db/migrations/cis/259_llm_catalog_haiku_sonnet_5_5.sql`; `docs/backlog/README.md` (S257 acc3 incident)
- Secondary (context only, not relied on): AWS blog on headless mode https://aws.amazon.com/jp/blogs/news/kiro-introducing-headless-mode/; Classmethod write-up https://dev.classmethod.jp/articles/kiro-cli-2-0-headless-mode-api-key-auth/

## Fact check

Adversarial check, 29/10/2026, against the primary sources listed above (fetched today). The recommendation stands:
it rests on the Kiro terms (allowed surfaces, harness restriction, per-developer seats) and on the missing per-call
cost and schema controls, all of which were confirmed verbatim. Changes:

- **Confirmed unchanged:** Kiro plans and credits (Free 50, Pro $20/1,000, Pro+ $40/2,000, Pro Max $100/5,000, Power
  $200/10,000), $0.04 add-on credit, packs $5 (125 credits) to $100, no monthly rollover, add-ons expire after 12
  months, Enterprise overage off by default; 0.01-credit metering and "pay by request, not by token"; headless flags,
  `KIRO_API_KEY`, keys only on Pro and above, "long-lived", tied to the user account, no documented expiry, scopes or
  usage fields in `stream-json`; ACP is JSON-RPC 2.0 over stdio for editors (V3 replaces `session/set_model` with
  `session/set_config_option`); AWS Service Terms §50.1 (Kiro is an AI Service), §50.3 (Free Tier / individual
  content use), §50.14.1 (Stripe → Amazon Web Services, Inc.); Anthropic prices (Sonnet 5.5 $2/$10, Haiku 5.5
  $0.10/$0.50, Haiku 4.5 $1/$5, Batch −50%), Start tier ($500 cap, 1,000 RPM, 2M ITPM for Sonnet 5.5, Evaluation tier
  for new orgs), commercial data not used for training by default, Claude Platform on AWS billed via AWS Marketplace;
  OpenAI gpt-5.6-luna $0.20/$1.20 and gpt-6-luna $0.10/$0.50, Batch −50%; Bedrock batch "50% lower" for select models,
  no per-model numbers on the Bedrock page. All arithmetic (break-even 6,725 credits / 0.099 per call, c ≤ 0.27,
  $0.00076 luna call, cost table rows, baseline month) recomputed and correct.
- **Fixed, Finding 3:** "open-weight models from 0.05x to 0.5x" was wrong; Kimi K3 is 2.4x. Added the >272K tiers for
  Terra and Sol and Fable 5.1 (6x, Enterprise only).
- **Fixed, Finding 4:** removed the claim that Bedrock global endpoints are priced the same as the first-party list.
  Anthropic only says global has no premium and regional is +10% over global; Bedrock's own page shows no numbers, so
  Bedrock = list stays a working assumption.
- **Softened, Summary item 2:** "Kiro wraps our prompt in its own agent prompt" is not documented. Custom agents have a
  `prompt` field "similar to a system prompt"; whether it replaces the built-in prompt is unknown. The conclusion (no
  temperature, seed, schema or `max_tokens` control) is unchanged.
- **Corrected source, Finding 2:** the abuse-detection point comes from Service Terms §50.14.2 (retention and possible
  human review for certain models), not from the Kiro data-protection page, which only states the opt-out caveat for
  Free Tier.
- **Added caveats:** "Claude in Amazon Bedrock" (Messages API surface) does not support Message Batches, so a Bedrock
  batch route means Bedrock batch-inference jobs; Sonnet 5.5 and Haiku 5.5 on Bedrock have per-model access criteria
  (not open to all accounts), which may matter for acc3 now that it is standalone; Haiku 5.5 doubles in price above
  100K-token prompts; the judge multiplier 0.5 in the cost table is an assumption; empty `--trust-tools=` is not
  documented.
- **Not verifiable from outside:** the acc3 incident facts, the $249 / 68K-call volume and the 85/15 split (internal;
  the Open questions query still applies).

