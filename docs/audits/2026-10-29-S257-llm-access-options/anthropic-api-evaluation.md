# Evaluation: adding the direct Anthropic API (Claude API) to the Model Gateway

S257, 29/10/2026. Agent: Claude Code (subagent, read-only). No code changed, no paid call made.

Scope: what the Claude API (first-party, `api.anthropic.com`) gives us, what it costs on our volumes, what billing,
admin and data-governance work it needs, and a concrete design for adding it to the CIS gateway
(`apps/AA-CIS-App/shared/llm_client`), mainly for **Message Batches (-50%)** and as a **fallback for Claude**.

Evidence tags:
- **[V]** = verified on the official doc page named, fetched 29/10/2026 (docs fetched as `.md` from platform.claude.com).
- **[M]** = measured in our repo (audit, ledger or code).
- **[A]** = assumption, to be replaced by a measurement.
- **[U]** = not verified.

Main official sources (all fetched 29/10/2026):
- Pricing: <https://platform.claude.com/docs/en/about-claude/pricing>
- Batch processing: <https://platform.claude.com/docs/en/build-with-claude/batch-processing>
- Rate limits: <https://platform.claude.com/docs/en/api/rate-limits>
- Prompt caching: <https://platform.claude.com/docs/en/build-with-claude/prompt-caching>
- Structured outputs: <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
- API and data retention: <https://platform.claude.com/docs/en/manage-claude/api-and-data-retention>
- Workspaces: <https://platform.claude.com/docs/en/manage-claude/workspaces>
- Service tiers: <https://platform.claude.com/docs/en/api/service-tiers>
- Errors: <https://platform.claude.com/docs/en/api/errors>
- Refusals and fallback: <https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback>
- Supported countries: <https://www.anthropic.com/supported-countries>
- Commercial Terms of Service: <https://www.anthropic.com/legal/commercial-terms>
- Billing help: <https://support.claude.com/en/articles/8977456-how-do-i-pay-for-claude-api-use>,
  <https://support.claude.com/en/articles/16608069-understanding-your-claude-api-invoices>

---

## 0. Bottom line

1. **Worth adding, mainly for resilience.** At today's volume, batch saves about **$25 per full catalogue rewrite**
   (810 tours). The upper bound is about **$100/month**, and only if a whole month looks like the brief's $249 wave month.
   That alone does not repay ~7.5 dev-days. What does repay it: one adapter gives a Claude path with **no AWS account and
   no reseller** in it. Bedrock on acc3 is blocked today, and acc2 cannot sell Claude.
2. **Batch is simple on the Claude API, hard on Bedrock.** Claude API: one HTTPS call, no S3, no IAM role, no minimum
   batch size documented (only maximums) [V batch, rate-limits]. Bedrock: S3 manifest, service role, at least 100 records per Claude job, and per-account
   enablement (`bedrock_batch.py`, `MIN_BATCH_RECORDS = 100`) [M]. Our Bedrock batch path has **never run live**
   (`s1_batch_ingest_job.py`: "Bedrock Batch is currently blocked on acc3") [M].
3. **Today's batch code does not fit today's writer.** `s1_batch.py` batches the old v1 Haiku writer prompt.
   `s1_writer_v2_live.applies()` refuses the batch seed path. The batch writer's cost never reaches `shared.llm_call_log`
   [M]. A Claude API batch for S1 therefore needs a v2-aware rewrite of that module, not a port.
4. **Decisions for the tech lead / business owner:**
   - Amend the S235 "Bedrock first" policy so Anthropic first-party is allowed as a Claude fallback and for batch.
   - Accept that prompts leave AWS for Anthropic.
   - Fix how we pay: prepaid card credits, or an invoice through Sales.
   - Ask the accountant about foreign-contractor tax (FCT) gross-up.
   - Update the tenant terms ("Claude through Amazon Web Services").
5. **Plan:** ~7.5 dev-days in 5 required PRs + 1 optional (corrected in the fact check: +0.5 day for cost-guard /
   spend-budget / admin / guard-registry wiring the first draft missed; the TripPlanner PR is optional, see §5.2).
   1. Sandbox key and contract test.
   2. Add `anthropic-*` rows as the **last fallback** on Claude writer routes.
   3. Shadow one low-volume stage.
   4. Run the next S1 wave as a batch, following the wave ladder: 3 tours, then 50 or fewer, then one country.

---

## 1. What we gain

### 1.1 Message Batches

- **Price:** "a 50 percent discount on both input and output tokens" [V pricing].
  - Sonnet 5.5: $1 / $5 per MTok (batch) vs $2 / $10 (standard).
  - Haiku 5.5: $0.05 / $0.25 per MTok for prompts up to 100K tokens.
  - Opus 5.5: $2 / $10.
- **Stacks with caching:** "These multipliers stack with other pricing modifiers, including the Batch API discount" [V pricing].
- **Turnaround:** "most batches completing within 1 hour". Results become available when every request is done or
  after 24 hours, whichever comes first. A batch "expire[s] if processing does not complete within 24 hours" [V batch].
- **Limits:**
  - 100,000 requests or 256 MB per batch, whichever comes first [V batch].
  - Results are downloadable for **29 days** after creation [V batch].
  - Batch queue rate limits, shared across models: Start tier 1,000 RPM and 200,000 requests in the processing queue;
    Build 2,000 / 300,000; Scale 4,000 / 500,000 [V rate-limits].
- **What is not allowed in a batch request:** `stream: true`, `speed` (fast mode), `fallbacks` (server-side
  fallback), and `max_tokens: 0` [V batch].
- **Workspace scope:** batches are scoped to the Workspace of the key that made them [V batch].
- **Spend limits can be overshot:** "batches may go slightly over the spend limit configured … for your Workspace"
  [V batch].
- **Results:** each result is `succeeded`, `errored`, `canceled` or `expired`, keyed by `custom_id` and returned in
  **any order**.
  - `errored`, `canceled` and `expired` requests are **not billed** [V batch].
  - A **refused** request comes back as `succeeded` with `stop_reason: "refusal"`; batch refusals mint no fallback
    credit, and refused items must be resubmitted ourselves (new batch or direct call) [V refusals-and-fallback].
    Whether a refusal is billed follows the general refusal rules (§1.3).
  - `custom_id` must match `^[a-zA-Z0-9_-]{1,64}$` [V batch].
  - Validation runs asynchronously: a malformed request surfaces only when the whole batch ends [V batch].
- **Caching inside a batch:** "cache hits are provided on a best-effort basis … 30 percent to 98 percent". Anthropic
  suggests the 1-hour cache TTL for batches with shared context [V batch].
- **Supported models (all we would use):** `claude-sonnet-5-5`, `claude-haiku-5-5`, `claude-opus-5-5`,
  `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`.
- **Supported platforms:** Claude API, Claude Platform on AWS and Claude Models on Google Cloud (Anthropic managed);
  **not** Amazon Bedrock or Google-managed Vertex [V batch front-matter].

### 1.2 Prompt caching

- **Two ways to cache:** automatic caching (one top-level `cache_control`) or up to 4 explicit breakpoints
  [V prompt-caching].
- **Price:** a 5-minute write costs 1.25x base input, a 1-hour write 2x base input [V pricing].
  - Cache reads are 0.1x on most models, but **0.05x on Sonnet 5.5 and Opus 5.5** ($0.10/MTok on Sonnet 5.5,
    $0.20 on Opus 5.5) [V pricing].
  - **Catalog mismatch:** our catalog row `sonnet-5-5` (Bedrock) has cache read **0.2** / write 2.5
    (`docs/generated/llm-routes.md`) [M]. The first-party price is $0.10 read / $2.50 write. Use $0.10 for the new
    Anthropic row. Whether the Bedrock row is right is [U]; $0.20 is exactly Sonnet 5's first-party cache-read price
    (0.1x of $2) [V pricing], so it looks copied from the Sonnet 5 row.
  - **Usage carries the TTL split:** `usage.cache_creation.ephemeral_5m_input_tokens` / `ephemeral_1h_input_tokens`
    (their sum = `cache_creation_input_tokens`) [V prompt-caching]. Price 1-hour writes from this split, not by guess.
  - **Caches are isolated per workspace** on the Claude API [V prompt-caching, workspaces]: the `aa-dev-runtime` and
    `aa-batch` workspaces of §3 never share cache entries.
- **Minimum cacheable prefix:**
  - 512 tokens for Sonnet 5.5, Opus 5.5 and Haiku 5.5.
  - 1,024 for Sonnet 4.6.
  - **4,096 for Haiku 4.5.**
  - Shorter prefixes are not cached, and no error is returned [V prompt-caching].
- **Rate limits:** cached reads do not count toward ITPM on current models [V rate-limits].

### 1.3 Parity with how we use Converse today

| What we use on Bedrock Converse (`client.py::_call_bedrock_converse`) | Claude API equivalent | Note |
|---|---|---|
| `system` = one text block | `system=[{"type":"text","text":…}]` (+ `cache_control`) | Same semantics |
| One user message (`user_prompt`) | `messages=[{"role":"user","content":…}]` | `LLMRequest.few_shots` is ignored by Converse today [M]. Keep parity (ignore) |
| `inferenceConfig.maxTokens` capped by `max_output_tokens` | `max_tokens` | Thinking counts against `max_tokens` on 5.5 models (`s1_writer_v2.WRITER_MAX_TOKENS` comment) [M] |
| `temperature` only when `supports_temperature` and explicitly set | **Never send** | Sonnet 5.5 / Haiku 5.5 reject non-default sampling values. API version `2026-10-21` (current SDKs) rejects `temperature`/`top_p`/`top_k` on every model (skill reference `shared/api-version-migration.md`; guide <https://platform.claude.com/docs/en/api/migration-2026-10-21>) |
| JSON via one tool: forced, or `auto` + instruction on 5.5 models (AA-803), then `_checked_json` + one retry (AA-714) | `output_config={"format":{"type":"json_schema","schema":…}}`: constrained decoding, GA on Sonnet/Haiku/Opus 5.5 and 4.x [V structured-outputs] | Better than Converse: the schema is enforced by grammar, so the AA-714 retry should become rare. Schema limits: `additionalProperties:false` on every object, no `minLength`/`maximum`/etc., at most 24 optional params and 16 union-typed params per request [V structured-outputs]. Forced `tool_choice` returns 400 on 5.5 models (skill model table) |
| Streaming via `converse_stream` → `stream_sink` deltas | `client.messages.stream(...)` text deltas | Same live-progress UX |
| Usage: `inputTokens` (uncached), `cacheRead/WriteInputTokens`, `outputTokens` | `usage.input_tokens` (after the last breakpoint), `cache_read_input_tokens`, `cache_creation_input_tokens`, `output_tokens` | Total prompt = the sum of the three input fields [V rate-limits] |
| `stopReason` | `stop_reason`: `end_turn`, `max_tokens`, `refusal`, … | `refusal` is new for us. Sonnet 5.5 can decline in five categories (skill model notes). Treat it as an unusable reply so the route moves on, but **not always billed**: a refusal before any output is billed only for `stop_details.category` `bio`, `frontier_llm` or `reasoning_extraction`; other categories / `null` are free (usage still shows token counts); a mid-stream refusal bills input + output already streamed [V refusals-and-fallback "How refusals are billed"] |
| Images | — | `LLMRequest` has no image field [M]; nothing to map |

**Thinking and effort.**
- We never send `thinking`, so 5.5 models run adaptive thinking at their default effort (AA-803 comment) [M]. The same
  happens on the Claude API.
- `output_config.effort` is GA. Sonnet 5.5 defaults to `high`; Haiku 5.5 and Opus 5.5 default to `medium` (skill model
  table). This is a separate cost lever. Measure it with an eval before changing it.

### 1.4 Model availability

All current models are on the first-party API at list price:
- Sonnet 5.5 `claude-sonnet-5-5`: $2 / $10.
- Haiku 5.5 `claude-haiku-5-5`: $0.10 / $0.50 up to 100K-token prompts, $0.50 / $2.50 above.
- Opus 5.5 `claude-opus-5-5`: $4 / $20.
- Sonnet 4.6: $3 / $15. Haiku 4.5: $1 / $5. These are the models behind our legacy `sonnet` / `haiku` keys.
- Fable 5.1: $10 / $50.

All prices from [V pricing].

**Fable is not for us.** Fable 5.1/5 are "Covered Models" that "require 30-day data retention" [V retention], at 5x
Sonnet's price. Nothing in our pipeline needs them.

### 1.5 Rate limits and tiers

- **Tiers are assigned automatically.** "Organizations are placed on a tier automatically based on usage history". New
  organizations "may start in the Evaluation tier, with limits below the standard limits" [V rate-limits].
- **Start tier, per model:**
  - Sonnet 5.5: 1,000 RPM / 2,000,000 ITPM / 400,000 OTPM.
  - Haiku 5.5: the same.
  - Build tier: 5,000 / 5M / 1M.
  - [V rate-limits]
  - Our busiest wave ran api 1→7 and worker 1→3 tasks (S248 cost report) [M]. That is far below Start. The
    **Evaluation tier** at sign-up is the real constraint for the first wave. Its numbers are not published [U].
- **Monthly spend caps:** Start $500, Build $1,000, Scale $200,000. At the cap, the API returns 429
  `rate_limit_error` with `error.details.error_code = "enforced_spend_limit_reached"` and no `retry-after`, until
  00:00 UTC on the 1st of next month [V rate-limits]. Our Claude spend is far below $500.
- **Our own spend limits answer differently:** when an org or workspace spend limit **we set** is reached, the API
  returns **HTTP 400 `invalid_request_error`** ("You have reached your specified [workspace] API usage limits …")
  [V rate-limits, errors]. This matters for §5.3's error mapping.
- **Raising limits:** "Request tier increase" on the Console Rate limits page, or Anthropic support [V rate-limits].
- **Per-workspace limits:** we can set our own lower rate and spend limits per Workspace. The Default Workspace cannot
  have a **spend** limit [V rate-limits, workspaces].
- **Separate buckets:** Sonnet 5.5 and Sonnet 4.x (4.6 + 4.5) have separate rate limits, as do Haiku 5.5 and Haiku 4.5
  [V rate-limits]. Sharp traffic jumps can also hit unpublished "acceleration limits" (429): ramp waves gradually
  [V rate-limits, errors].

### 1.6 Reliability and SLA

- The standard tier gets "best-effort availability" [V service-tiers].
- **Priority Tier** "capacity commitments are no longer available for purchase" [V service-tiers].
- No SLA is published for self-serve organizations. Any SLA would come from a Sales contract [U].
- Errors: 529 `overloaded_error` ("high traffic across all users") and 500 `api_error`.
- The SDK "automatically retries transient failures … twice by default, honoring the `retry-after` header" [V errors].
- Status page: <https://status.claude.com> (reachable, 200).
- **What this means for us:** treat the Claude API as an independent failure domain from Bedrock. Its value is that
  Claude-on-Bedrock and Claude-direct rarely fail together, and never for the same account or billing reason.

---

## 2. Cost on our volumes

### 2.1 What we actually know

| Source | Figure |
|---|---|
| S248 cost report (`docs/audits/2026-10-23-S248-cost-report/README.md` §5) [M] | acc3 01–22/10: **$138.61** (Haiku 4.5 $86.45, Sonnet 4.6 $37.41, GPT-5.6 Luna $10.73, GPT-6 Luna $3.40). Forecast for all of October: $215.74. Early-October waves ran on **Haiku 4.5 + Sonnet 4.6**. From 17/10: $0–8/day |
| Wave ≤50 (`docs/audits/2026-10-24-S249-s1-wave50/README.md`) [M] | $3.8386 for 50 tours = **$0.0768/tour**. `s1_generate` (Sonnet 5.5) **$3.0010 = $0.0600/tour = 78%** of the wave. Judge (luna) $0.27, flag_fix (Haiku 4.5) $0.15, Jev $0.16, atomize (luna) $0.26 |
| S250 ledger (`docs/audits/2026-10-24-S250-s251-go-no-go/README.md`) [M] | 7 waves, 162 tours, $11.89 = $0.073/tour. `s1_generate` → Sonnet 5.5 since 24/10 |
| Brief (orchestrator, via `.tmp-session/S257/aa999-kiro-llm-provider.md` §4) | "last 30 days ≈ $249 across ≈ 68,000 calls". The 85% Sonnet / 15% judge split there is labelled an **assumption** |

**Correction to the brief.**
- The "$249" lines up with the **AWS Lift credit balance ($249.94)** and the eCloudvalley $250 package (S257 log).
- October's measured spend was **mostly Haiku 4.5 + Sonnet 4.6** waves (S248), not Sonnet 5.5. Sonnet 5.5 became the
  S1 writer only on 24/10.
- So "mostly Sonnet 5.5 waves" is **not supported by the data I could read**. The table below therefore uses the
  measured per-tour figures, and shows the brief's split as an upper bound only.
- To replace the assumption, run this read-only query (no LLM cost): `select stage, model, provider,
  sum(cost_usd), count(*) from shared.llm_call_log where created_at > now()-interval '30 days' group by 1,2,3 order by
  4 desc`. `.tmp-session/S257/llm_spend.py` already has the shape.

### 2.2 Unit prices: Bedrock vs Claude API

- **Claude API:** list prices as in §1.4 [V].
- **Bedrock:** "partner-operated platforms … have independent regional pricing", with a 10% premium for regional over
  global endpoints [V pricing]. Our catalog assumes Bedrock global = list (migration 259) [U].
- **US-only inference costs more:** `inference_geo:"us"` on the Claude API costs 1.1x [V pricing]. The default,
  `global`, is list price.
- **Conclusion:** on-demand costs the same in USD on either path [A]. The saving comes only from batch, caching and
  effort.

### 2.3 Monthly cost scenarios

| Scenario | Bedrock on-demand (today) | Claude API on-demand | Claude API, S1 writer as batch | Saving from batch |
|---|---:|---:|---:|---:|
| **Baseline month, no waves** ($1–5/day; judges = luna, many small Haiku/Sonnet 4.6 calls) [M] | $30–150 | same (Claude part only) | not applicable: interactive / tenant / per-tour graph calls | **≈ $0** |
| **One full S1 catalogue rewrite** (810 tours × $0.0768) [M] | $62 | $62 | writer $48.6 → $24.3; rest $13.6 unchanged → **$38** | **≈ $24 (-39%)** |
| **Brief's wave month** ($249, 85% Sonnet writer) [A] | $249 | $249 | $212 × 0.5 + $37 = **$143** | **≈ $106 (-43%)** (upper bound) |
| **Same, if Bedrock batch worked** | — | — | ≈ $143 (Bedrock also -50% on "select models") [U for Sonnet 5.5] | same, but S3 + role + min 100 records + enablement |

**Caching on top of batch adds little for S1.**
- The writer's cost is dominated by output, including adaptive thinking: `WRITER_MAX_TOKENS = 16000`, $10/MTok out vs
  $2 in [M]/[V].
- Caching the stable system block saves at most a few percent of writer cost [A]. In a batch the hit rate is
  best-effort (30–98%) [V].

**Two measured levers worth more than caching:**
1. **Batch** (-50% of the writer).
2. **Effort** on the writer route: Sonnet 5.5 defaults to `high`. Needs an eval run with its ID recorded in the PR, per
   handbook §5.7.

**What batch cannot touch:**
- The judges are OpenAI luna. Vendor separation (S235) keeps them non-Anthropic.
- The `flag_fix` / `itinerary_nudge` Haiku calls run inside the per-tour graph after the judge, so they cannot be
  batched.

### 2.4 Is it worth it on cost alone?

**No.** Realistic savings are $24–106/month, and only in months with a wave. Building it costs ~7.5 dev-days. The case
rests on §5's resilience value plus the option to batch larger future runs: T-series backfills, a second catalogue
pass, writing-memory evals.

---

## 3. Billing and admin for a Vietnamese company

| Topic | What the docs say | What we should do |
|---|---|---|
| **Availability in Vietnam** | Vietnam is on Anthropic's list of "Countries and regions where we currently offer access to our products and services", which covers the API and developer platform; access also depends on the user's location and the entity's incorporation, headquarters and ownership [V <https://www.anthropic.com/supported-countries>] | Sign up as the Vietnamese legal entity, from Vietnam. No VPN / foreign-entity workaround |
| **Account type** | An Organization on platform.claude.com under the **Commercial Terms** ("You may not enter into these Terms on behalf of an organization … unless you have the legal authority to bind that entity") [V terms] | The business owner (or an authorised signatory) creates or accepts for Adventure Asia, using a **company role mailbox**, not a personal one. Tech lead = Organization admin. Accountant = billing role |
| **Workspaces / keys** | Every org has a **Default Workspace** that cannot be renamed, archived or deleted, and **cannot have a spend limit**. API keys can be scoped to one workspace. Up to 100 workspaces [V workspaces, rate-limits] | Create workspaces `aa-dev-runtime` (CIS api + worker key), `aa-batch` (batch waves; batches are workspace-scoped) and `aa-sandbox` (manual tests). Never put runtime keys in Default |
| **Prepaid credits** | "Claude API and playground usage is billed through prepaid usage credits". "If you run out of credits, you can no longer call the API". Auto-reload buys credits when the balance falls below a threshold. "You're billed only for successful API calls"; a client disconnect or timeout on a request that "was on track to succeed" is still charged. "Credits expire one year from the purchase date", cannot be extended, and purchases are non-refundable [V billing help, re-checked 29/10] | Start with a small prepaid balance and **auto-reload on**. Without it, an empty balance becomes a Claude outage, though the route would fall back to Bedrock if Bedrock is up |
| **Invoice instead** | "Organizations with an invoicing arrangement are billed monthly", a Stripe invoice at month end, arranged through Sales [V billing help] | Ask Sales only if the accountant needs monthly invoices or bank transfer. At ~$100–250/month, self-serve credits are fine |
| **Spend limits / alerts** | Per-workspace spend limits and alerts at thresholds (Console → Workspaces → Spend limits). Tier caps $500/$1,000. Reaching a limit we set returns HTTP 400, not 429 [V workspaces, rate-limits, errors] | `aa-dev-runtime` limit ≈ $100/month, `aa-batch` ≈ $150/month, alerts at 50/75/90%. Mirror the AWS budget pattern (acc3 alert $250 is a warning only, per memory). Batches may overshoot the workspace limit slightly [V batch] |
| **Invoice content** | Name, address and tax information come from billing details **at issue time**; "issued invoices can't be modified" [V invoices help] | Enter the legal name, address and **tax code (MST)** before the first purchase |
| **Taxes** | "Fees do not include any taxes … Customer is responsible for remitting any necessary withholding Taxes … Customer must pay Anthropic the amount ('Gross-up Payment') that will ensure that Anthropic receives the same total amount" [V terms H.2] | **Accountant question:** Vietnam foreign-contractor tax (FCT) on an offshore digital service. Under the gross-up clause we pay the FCT on top. No Vietnamese VAT e-invoice is expected from Anthropic/Stripe [U]. Same situation as AWS Inc. direct (angle2) |
| **Termination** | Either party may terminate for convenience with notice; Anthropic must give 30 days' notice [V terms I.2.a] | Much better exit terms than a reseller-org arrangement |
| **Who owns it** | — | The company owns the org and the card. The tech lead holds admin. API keys live only in Secrets Manager (see §5.6). Record it in `docs/security/secrets-register.md` (owner rows next to `vendor:openai`) |
| **Usage reconciliation** | Usage and Cost Admin API (Admin key, curl only) <https://platform.claude.com/docs/en/manage-claude/usage-cost-api> (skill reference) | Optional later: a nightly job comparing Anthropic's cost report with `llm_call_log` (provider `anthropic`) on the Cost Operations page |

---

## 4. Data governance

**What the documents commit to:**
- **Training:** "Anthropic may not train models on Customer Content from Services" [V terms B]. Data is processed under
  the Anthropic DPA, which the Terms incorporate [V terms C].
  - Retention docs: "Retained data is never used for model training without your express permission" [V retention].
- **Default retention:** "Conversation content (your prompts and Claude's outputs) is not retained by default; the
  exception is Covered Models" (Fable/Mythos, 30 days) [V retention].
  - **Exception:** "if a chat or session is flagged … Anthropic may retain inputs and outputs for up to 2 years", even
    under ZDR [V retention].
- **Batch is stateful:** "29-day retention", and batch is **not ZDR-eligible** [V batch front-matter, retention
  feature table]. Batch results stay downloadable for 29 days.
- **ZDR** is available through Sales, enabled per organization [V retention].
  - It would not cover batch data.
  - Given the default above, ZDR mainly matters for the residual (flagged/legal) cases.
  - Not needed for our content [A]; the tech lead decides.
- **Structured-output schemas** are cached separately, up to 24 h after last use [V structured-outputs]. Our schemas
  hold no personal data.
- **Where inference runs:** `global` by default, i.e. anywhere Anthropic serves. US-only costs 1.1x [V pricing].
  Today Bedrock global cross-region profiles also route outside us-west-1, so this does not change much.

**What we would send, checked in code [M]:**
- **CIS stages** (`docs/generated/llm-routes.md`):
  - Supplier tour content (S1, A3).
  - Place data.
  - **Tenant brand data**: brand rules and voice, tenant names (T2, T7–T10).
  - No traveller PII. Booking has no LLM call (grep of `apps/AA-Booking`).
- **CRM (AA-Partner):** has its **own gateway** (`api/app/llm/gateway.py`). It scrubs PII with placeholders before any
  model call and ships only a stub provider today. It does **not** use the CIS gateway, so it is unaffected.
- **TripPlanner:** has its **own fork** (`backend/shared/llm_gateway.py`). `tp_compose` / `tp_extract` take a
  traveller's free-text search, which can carry incidental personal details. It calls Bedrock InvokeModel directly
  and would **not** gain the Anthropic path unless it is ported on purpose.
  - Note: TripPlanner's fork treats `api_style='anthropic_native'` as "Bedrock InvokeModel", which matters for §5.2.
- **Tenant terms** say "Anthropic's Claude through Amazon Web Services" (`apps/AA-Partner/portal/app/terms/page.tsx:54`)
  [M]. They need a wording change, e.g. "through Amazon Web Services or directly from Anthropic", before tenant (T-series)
  stages route to the Claude API.

**What the tech lead / business owner must accept:**
1. Prompts (tour content, tenant brand data) leave AWS for Anthropic, a second processor. This is the same kind of
   decision as the S235 OpenAI last-resort.
2. Batch inputs and outputs are kept for 29 days.
3. Flagged content can be kept for up to 2 years.
4. The tenant terms change.
5. Judges stay non-Anthropic (vendor separation, S235 note) [M].

---

## 5. Integration design in our gateway

### 5.1 Where it plugs in today [M]

- `LLMClient._generate()` resolves the stage route (`model_id` + `fallback_model_ids`) → `_call_route()` →
  `_call_key_logged()` → `_call_key()`.
- Non-legacy keys go to `_call_catalog_model()`, which dispatches on `CatalogModel.api_style`:
  - `openai_chat` → `_call_openai`
  - `converse` → `_call_bedrock_converse`
  - anything else raises.
- Billed-but-unusable replies raise `BilledUnusableReply` (AA-927), so the attempt is logged and the route moves on.
- **Callers write the `shared.llm_call_log` row of a usable reply** (`call_log.record_call*`, `billed_record(resp)`).
  The gateway itself writes only the rows of billed-but-unusable attempts: `_call_key_logged()` →
  `log_gateway_billed_failure()` (AA-927), from the `_billed_usage(...)` dicts the adapter attaches. Those dicts carry
  **no `provider` key**, so these rows always get their provider from `_normalize_model_provider()`, which derives it
  from the model string: `satellite-` → `bedrock-satellite`, `gpt*` → `openai`, anything else → **`bedrock-native`**.
- `llm_call_log` has **no cache-token columns** (`tokens_in`, `tokens_out`, `cost_usd`, `quality_signal`, …): the
  cache split lives only in `LLMResponse` unless a caller puts it into `quality_signal` [M].
- **Direct satellite call sites:** `invoke_claude()` now says "LLMClient (the only caller)". The only other direct
  Bedrock users are `bedrock_batch.py` and `embed.py` [M]. The "five direct satellite call sites" in angle2 is stale:
  there is nothing extra to port outside the gateway.

### 5.2 Catalog and routing (migration, CIS owner, next number after 303)

1. **Provider CHECK:** `llm_model_catalog_provider_check` += `'anthropic'`.
   - `api_style` keeps its existing value `anthropic_native`, which is the Messages shape.
   - `llm_role_config.provider` is the vendor family (`claude`), so it is unchanged.
2. **New rows, all `enabled=false` at first:**

   | model_key | wire_model | vendor / provider / api_style | Prices in/out; cache read/write (5m) | max_output_tokens | supports_temperature |
   |---|---|---|---|---|---|
   | `anthropic-sonnet-5-5` | `claude-sonnet-5-5` | anthropic / anthropic / anthropic_native | 2 / 10; 0.10 / 2.50 | 128000 | false |
   | `anthropic-haiku-5-5` | `claude-haiku-5-5` | same | 0.10 / 0.50; 0.01 / 0.125 | 128000 | false |
   | `anthropic-sonnet-4-6` | `claude-sonnet-4-6` | same | 3 / 15; 0.30 / 3.75 | — | false |
   | `anthropic-haiku-4-5` | `claude-haiku-4-5` | same | 1 / 5; 0.10 / 1.25 | — | false |

   - Prices from [V pricing]. Cache write = the 5-minute rate (1.25x), the TTL `pricing.calc_cost` assumes.
   - Every row needs `callable_via = '{llm_client}'`: `admin_llm_ops._catalog_options()` marks a row without it
     "Model này không gọi được qua gateway" and the route editor refuses it [M].
   - `anthropic-haiku-5-5`: the catalog holds one price; Haiku 5.5 prompts over 100K tokens cost 5x ($0.50 / $2.50)
     [V pricing], so such calls would be under-logged. Our prompts are far below 100K [A]; add a guard or a note.
   - The `anthropic-` prefix keeps model keys readable in `llm_call_log.model`.
   - The 4.6 / 4.5 rows are **same-model** fallbacks for the 25 stages still on the legacy `sonnet` / `haiku` keys, so a
     fallback never changes the model (ADR 0005 §4 logic).
3. **Route rows (later migration, or admin UI once the guard allows it):**
   - Append `anthropic-sonnet-5-5` as the last fallback of `s1_generate` and `supply_content_writer`.
   - Append `anthropic-sonnet-4-6` / `anthropic-haiku-4-5` to Claude writer/validate stages that use legacy keys.
   - `_call_route` already handles mixed legacy and catalog chains [M].
4. **TripPlanner (corrected by the fact check: no latent KeyError).** TP's `_text_call` does dispatch on
   `api_style == 'anthropic_native'` alone, but the route loop only calls it for accounts returned by
   `_accounts(model, …)`, which keeps only accounts present in `model.profiles`. An Anthropic row has no
   `bedrock_profile_ids`, so TP records `_no_account(model)` ("no profile on a supported account") and moves to the
   next model; nothing is sent and nothing crashes [M, `backend/shared/llm_gateway.py` lines 179–184, 276–281].
   - A TP PR is therefore **optional** (a clearer skip message such as "provider anthropic not supported here").
   - Keep `api_style = 'anthropic_native'` and dispatch on `provider` in the CIS gateway.
5. **Spend budget / cost guard (missed in the first draft) [M]:**
   - `shared.spend_budget_provider_check` allows only `dfs|bedrock|openai|jev|geocoder`: an `anthropic` budget row
     needs this CHECK changed in the same migration.
   - `shared/cost_guard.py`: `PROVIDERS` and `_DAY_SPEND_SQL` count `provider LIKE 'bedrock%'` for `bedrock` and
     `= 'openai'` for `openai`. Rows with `provider='anthropic'` fall into **no** provider-wide daily cap, so a
     `load_run_budget(pool, "bedrock", …)` job (today `segment_research`) would not see Anthropic fallback spend.
     Kind-scoped caps (`day_scope="kind"`, e.g. `supply_content_draft`, `writing_memory_mine`) and per-run budgets
     already count it. Decide: add an `anthropic` budget provider, or count `anthropic` inside the Claude/`bedrock`
     day sum.

### 5.3 Adapter: `LLMClient._call_anthropic()` (new module `shared/llm_client/anthropic_api.py`)

**Dispatch.** In `_call_catalog_model`, before the `api_style` checks: `if model.provider == "anthropic": return
self._call_anthropic(request, model)`.

**Gate.** `anthropic_direct_allowed(model_key)`, mirroring `openai_platform_allowed`:
- The catalog row must be `provider='anthropic'` and `enabled`.
- The env kill switch `LLM_ANTHROPIC_DIRECT` must be on (default off, read per call like `LLM_LEGACY_ACC2_NATIVE`).
- Fails closed when the catalog cannot be read.
- Raises `AnthropicDirectBlocked`, which counts as "down", not "unusable", in `_call_route`.

**Client.** Use the official `anthropic` Python SDK. Pin it in `requirements.txt`; current SDKs send API version
`2026-10-21` (skill reference). Settings:
- `anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], max_retries=2, timeout=300)`.
  - 300 s matches the Bedrock `read_timeout`.
  - SDK retries cover 408/409/429/5xx/connection errors and honour `retry-after` [V errors].
- Build the client lazily, so a task without the key still starts.

**Request mapping:**
- `system=[{"type":"text","text": request.system_prompt, "cache_control":{"type":"ephemeral"}}]` when the system prompt
  is at or above the model's minimum (§1.2). Otherwise send no `cache_control`: no error either way, but it keeps the
  intent explicit.
- `messages=[{"role":"user","content": request.user_prompt}]` (no prefill, as today).
- `max_tokens=min(request.max_tokens, model.max_output_tokens or request.max_tokens)`.
- No `temperature`, `top_p`, `top_k` or `seed`.
- No `thinking` field (adaptive default). Optional later: a catalog or route `effort`.
- `json_schema` → `output_config={"format":{"type":"json_schema","schema": schema["schema"]}}`.
  - Run schemas through the SDK's `transform_schema()` (named in the structured-outputs doc) or a local check, so
    unsupported constraints become descriptions.
  - Keep `_checked_json(...)` as defence in depth.
  - Drop the AA-714 retry for this path unless `stop_reason == "max_tokens"`.

**Call style:**
- No schema: `client.messages.stream(...)`, with text deltas into `stream_sink.delta_callback(request.stage)` and
  `stream.get_final_message()`, the same UX as `converse_stream`.
- With a schema: also `client.messages.stream(...)` + `get_final_message()`, just without forwarding deltas
  (corrected). The SDK validates that a non-streaming request is not expected to exceed 10 minutes and the docs
  recommend streaming or batches for large `max_tokens` [V errors "Long requests"]; with thinking counted in
  `max_tokens` (16,000 for the writer, up to 128,000 by catalog cap) a non-streaming call is the riskier choice.
  Whether an explicit `timeout=300` interacts with that SDK check is [U]; streaming sidesteps it.

**Response mapping:**
- `content` = joined `text` blocks. Thinking blocks are empty by default; ignore them.
- `stop_reason` stored as is.
- Empty text or schema mismatch → `_billed_unusable(...)` with `_billed_usage("anthropic-…", None, {...}, cost,
  stop_reason, provider_requests)` (same helper as Converse / OpenAI).
- `refusal` (corrected): billed only when it arrived mid-stream (some output) or its `stop_details.category` is
  `bio` / `frontier_llm` / `reasoning_extraction` [V refusals-and-fallback]. Then → `_billed_unusable(...)` with the
  usage. Otherwise (pre-output refusal in another category, or `null`) the request is **free** even though `usage`
  shows tokens → raise a plain `UnusableReply`/`RuntimeError` with no billed usage, so no cost row is written. Log
  `llm_anthropic_refusal` (stage, category) either way; the docs advise counting refusals as their own signal.
- Usage:
  - `uncached = usage.input_tokens`, `cache_read = usage.cache_read_input_tokens`,
    `cache_write = usage.cache_creation_input_tokens`, `out = usage.output_tokens`.
  - `LLMResponse.input_tokens = uncached + cache_read + cache_write`, the same convention as the Converse path (S234
    note), so `tokens_in` is the real prompt size.
  - `cache_read_tokens` / `cache_write_tokens` carry the split.
- `cost_usd = calc_cost(model.model_key, uncached, out, cache_read=…, cache_write=…)`, from catalog prices.
- `model_used = model.model_key` (e.g. `anthropic-sonnet-5-5`), `provider="anthropic"`, `satellite_account=None`.

**Error mapping:**
- `anthropic.RateLimitError` / `InternalServerError` / `APIConnectionError` after SDK retries → plain failure, so the
  route tries the next model (e.g. Bedrock).
- `BadRequestError` → plain failure plus a `logger.error` with the request id (`message._request_id` / the error's
  `request_id`) — **except** a 400 whose message starts "You have reached your specified" (our own org/workspace spend
  limit, §1.5): that is an operational "down", not a code bug. Log it as `llm_anthropic_spend_limit` and let the route
  fall back. Corrected: the first draft treated every 400 as a code bug, which would have mislabelled the workspace
  limits §3 recommends.
- Tier spend-cap 429: no `retry-after`, `error.details.error_code == "enforced_spend_limit_reached"`; the SDK's two
  retries cannot succeed [V rate-limits]. Detect by `error_code`, log `llm_anthropic_spend_cap`.
- Empty prepaid balance: "you can no longer call the API" [V billing help]; the exact status (402 `billing_error`
  or a 400) is [U]. Treat `PermissionDeniedError`/402/billing 4xx as "down" and alert.

**Call log:**
- `_normalize_model_provider`: add `model.startswith("anthropic-") → provider "anthropic"`. Without this, a caller that
  does not pass `provider` would log **`bedrock-native`**.
- Admin cost pages (`admin_llm_ops.py` cost tree / forecast group by `provider`) get a new `anthropic` bucket. Add a
  label and a budget row (`shared.spend_budget`, which needs its provider CHECK widened, §5.2 item 5).

**Policy event.** Log `llm_anthropic_direct_used` (stage, model, position) on every successful direct call, as
`llm_openai_fallback_used` does today, so content leaving AWS is countable. Note that `llm_openai_fallback_used` is
emitted in `_call_route()` on `resp.provider == "openai"`, not in the adapter; put the new event next to it.

**Admin guard (`api/routers/admin_llm_ops.py`; S235 rules are `_openai_api_keys` / `_OPENAI_LAST_RESORT_ONLY` /
`patch_llm_config`, around lines 194–245; line 123 is `model_via`):**
- Allow an `anthropic` row as a fallback, and as a shadow on writer/validate stages.
- Judge refusal comes for free: `_catalog_options()` already refuses any `vendor == 'anthropic'` row on judge stages.
- Allow it as primary only after the tech lead lifts S235 for Claude (optional; batch does not need it).
- `model_via()` has branches for `provider == "openai"` and Bedrock accounts only; add `provider == "anthropic"` →
  "Anthropic API", or the route view renders an empty Bedrock label.

**Zero-cost and call-site guards (missed in the first draft) [M]:**
- `services/golden_set/llm_guard.py::ENTRY_POINTS` (AA-919 "$0 process" guard) patches `LLMClient.generate/_generate`,
  `invoke_claude`, `get_satellite_client`, `embed._call`. The sync adapter is covered through `generate`; the batch
  module is not. Add `anthropic_batch.submit` (and the client factory) there.
- `tests/unit/test_aa927_llm_call_site_registry.py::HELPER_NAMES` lists `submit_batch_job` (Bedrock Batch). Add the
  Anthropic batch submit helper so each new call site must register its `llm_call_log` writer.

### 5.4 Fallback order

- **Steady state:** Bedrock first (acc3, or acc2 after any account change). Claude API last.
- **During a Bedrock Claude outage:** flip the order in the admin UI (route edit, no deploy), or disable the Bedrock
  rows. The route already skips disabled rows with `llm_route_skip` [M].
- **Batch** is a separate path (§5.5). It does not go through routes.

### 5.5 Batch module: `shared/llm_client/anthropic_batch.py` + v2-aware S1 batch

**Why not port `bedrock_batch.py` 1:1 [M]:**
- It writes **v1 Haiku** prompts (`materialize_s1_prompt`, `model="haiku"`).
- The live writer is **v2 on `sonnet-5-5`**, with three calls per draft: write, meta, meta retry
  (`s1_writer_v2_live.write`).
- v2 explicitly excludes the batch seed (`applies()` → `state.get("batch_text") is None`).
- The seed node (`graph.seed_generated_node`) logs only the nudge cost, **not the batch writer's cost**.
- `s1_batch_ingest` is `max_attempts=1, deploy_blocking=True`, with **no checkpoint**: re-claiming it would ingest
  every tour twice (AA-993 G5 comment). A 24 h batch must not hold a deploy-blocking lease for 24 h.

**Module API**, provider-agnostic in shape so Bedrock batch can share the orchestration later:
- `build_request(custom_id, system, user, model, max_tokens, schema=None, cache_ttl="1h")` → a `Request` whose
  `params` are byte-identical to what `_call_anthropic` would send (same system block, same `output_config`).
  - A **1-hour cache TTL** on the shared system block (2x write price, but writes are rare and reads are 0.05x on
    Sonnet 5.5) [V pricing, batch tip].
- `submit(requests, workspace_key) -> batch_id`.
- `status(batch_id)`.
- `iter_results(batch_id)` yields `(custom_id, text | error, usage, stop_reason)`, keyed by `custom_id`, never by
  position [V batch].
- `custom_id` = `t_` + 32-hex of the tour UUID (the tour id with dashes stripped, if it is a UUID), to fit
  `^[a-zA-Z0-9_-]{1,64}$`. Keep a payload map `custom_id → tour_id`.

**S1 orchestration** (new `services/content_generation/s1_batch_v2.py`, replacing the AA-606 v1 path):
1. **Prepare (on-demand, unchanged code):** facts (`s1_source_facts`, luna) and plan per tour, as in v2 today. Store
   the materialised W prompt per tour in the job payload or a small table row (e.g. a `shared.rerun_wave` child record),
   so the batch never needs a second read.
2. **Phase A batch: writer.** `w_system_prompt` / `w_user_prompt` for every tour, `max_tokens = WRITER_MAX_TOKENS`.
3. **Phase B batch: meta.** Built from each phase-A page.
   - Or run meta on-demand. It is small; measure first.
   - The meta retry stays on-demand.
4. **Ingest:** for each tour, call `_execute_run_tour(req, job_id, batch_text=…, batch_model_used=…)` (corrected:
   the real signature has `batch_text`, `batch_model_used`, `batch_account`, `stage_cb`, `checkpoint`, and **no
   `writer_version` parameter**, `api/routers/admin_pipeline.py:554`). Making the seed v2 means changing
   `s1_writer_v2_live.applies()` (which returns False whenever `batch_text` is set) and the seed path in `graph.py`
   so the draft is stamped `writer_version` v2. Judge, gate, repairs and retries run on-demand as now.

**Jobs (`shared.job`):**
- `llm_batch_submit`: short. Writes the `batch_id` into the wave row.
- `llm_batch_poll`: short, **not deploy-blocking**. Re-enqueues itself every 10 min until `ended`, then enqueues ingest.
- `s1_batch_ingest`: deploy-blocking as now, but with a per-tour checkpoint. Skip a tour whose `generated_content`
  already has this `batch_id` + `custom_id`, so a re-claim is safe and `max_attempts` can rise to 3. Reuse the AA-993
  G2 mechanism (`S1Checkpoint`, the `checkpoint=` argument of `_execute_run_tour`, today passed only by `s1_rewrite`)
  rather than a new marker. Results stay readable for 29 days, so ingest can be retried long after submit.
- **Wave attribution:** the wave report (`services/waves/report.py::LLM_COST_SQL`) sums `llm_call_log` rows whose
  `job_id` is one of the wave's jobs, and its module doc already lists the Bedrock Batch path as a known gap. The
  submit / poll / ingest jobs must carry the wave id in the payload and be part of the wave's job set, or the batch
  writer cost never shows in the wave report [M].

**Cost logging at batch price:**
- One `llm_call_log` row per **succeeded** result: stage `s1_generate`, role `writer`, `model=anthropic-sonnet-5-5`,
  `provider='anthropic'`, `quality_signal = {"batch": {"provider":"anthropic","batch_id":…,"discount":0.5},
  "writer_version":"v2","call":"write"}`.
- Cost = `calc_cost(...) × 0.5`: add `batch: bool = False` to `pricing.calc_cost`. A 1-hour cache write is 2x base
  input, so add `cache_write_1h` (2 × input when the catalog has no explicit value), fed from
  `usage.cache_creation.ephemeral_1h_input_tokens`; the 5-minute part from `ephemeral_5m_input_tokens`
  [V prompt-caching]. Cache multipliers stack with the batch discount [V pricing].
- `errored` / `canceled` / `expired` results are not billed [V batch], so write no cost row. Log a
  `llm_batch_result_failed` event, and let the tour fall back to the on-demand path, as AA-606 already does for failed
  records.
- `succeeded` + `stop_reason: "refusal"`: apply the refusal billing rule of §5.3 (billed row only for the billed
  categories), then send the tour to the on-demand route; no fallback credit exists for batch refusals
  [V refusals-and-fallback].

**Guards:**
- Wave rules (`skill aa-wave-rerun`) apply unchanged: snapshot, expected set, stop conditions.
- Before submit, check the workspace spend limit against the estimate (tours × $0.03).

### 5.6 Secrets and runtime

- **Secret:** Secrets Manager `aa-cis/dev/anthropic-key`, injected as `ANTHROPIC_API_KEY` through ECS task definition
  `secrets` for **api and worker**. This mirrors `OPENAI_API_KEY`
  (`infra/AA-CIS-Infra/modules/ecs/main.tf:600`, `:824`, `var.secret_openai_arn`) [M]. The **execution role** reads it
  at task start, so the task role needs no new permission.
  - Cost: **$0.40/month** per secret (Secrets Manager list price, as in the S248 report) [M].
  - Under the cost rule this needs an explicit yes from the tech lead.
- **Keys:** a separate key in `aa-batch` for batch jobs. Store it as a second secret (`aa-cis/dev/anthropic-batch-key`)
  or as one secret holding JSON with two keys. One secret is cheaper; two give a clean revoke.
- **Register:** `docs/security/secrets-register.md` gets a row plus an owner row (`vendor:anthropic`). App repos are
  public, so no key or org ID goes into them.

### 5.7 Feature flags and kill switches

| Switch | Effect |
|---|---|
| Catalog `enabled` on each `anthropic-*` row | Per-model on/off, no deploy (route skips disabled rows) |
| Env `LLM_ANTHROPIC_DIRECT` (api + worker task def, default off) | Hard stop for every direct call (gate in §5.3) |
| Env `S1_BATCH_PROVIDER=anthropic` (default unset → no batch) | Enables the batch submit endpoint/job |
| Workspace spend limit in Console | Cost ceiling outside our code |

### 5.8 Tests

- **Unit, no network:**
  - Fake the SDK client (inject an object with `messages.create` / `messages.stream` / `messages.batches.*`).
  - Request shape: system block, `cache_control` threshold, no `temperature`, `output_config` from `json_schema`.
  - Usage → `input_tokens` / cache split / `cost_usd`.
  - `refusal` in `bio` / `frontier_llm` / `reasoning_extraction` or mid-stream → `BilledUnusableReply`; pre-output
    refusal in another category / `null` → unbilled failure, no cost row.
  - Our-own-spend-limit 400 → route moves on, logged `llm_anthropic_spend_limit` (not `logger.error` as a bug).
  - Billed-unusable gateway row for an `anthropic-…` model gets `provider='anthropic'`.
  - `cost_guard` day spend includes `provider='anthropic'` under the chosen budget provider.
  - AA-919 `$0` guard refuses the batch submit; AA-927 registry sees the new helper.
  - 429 / 529 → route moves to next.
  - Gate closed → `AnthropicDirectBlocked`, nothing sent.
  - `_normalize_model_provider("anthropic-…")` → `anthropic`.
  - `calc_cost(batch=True)` halves every component.
- **Batch:**
  - Results out of order.
  - `errored` / `expired` → fallback path, no cost row.
  - Ingest re-claim is idempotent (checkpoint).
  - The `custom_id` mapping round-trips.
- **Migration test:** both CHECKs (`llm_model_catalog_provider_check`, `spend_budget_provider_check`) accept
  `anthropic`; new rows are disabled and carry `callable_via = {llm_client}`; the TP gateway skips the row
  (`_no_account`).
- **Contract test (manual, paid, ~$0.01):** one tiny call per row through `LLMClient.generate()` with stage
  `adhoc_<issue>`, logged to `llm_call_log` (rule "Script gọi LLM chạy tay — PHẢI ghi cost").

---

## 6. Effort, risks, rollout

### 6.1 Slices

| PR | Repo | Content | Days |
|---|---|---|---:|
| 1 | Infra | Secret + task-def `secrets` for api/worker, register row (after the tech lead creates the org/key and says yes to $0.40/month) | 0.5 |
| 2 | CIS (+ Infra copy) | Migration: catalog + spend_budget provider CHECKs, 4 disabled catalog rows (`callable_via`), `pricing.calc_cost(batch, cache_write_1h)`, `_normalize_model_provider`, `cost_guard` provider mapping | 0.75 |
| 3 | TripPlanner | **Optional:** clearer skip message for non-bedrock rows (already skipped via `_no_account`) | 0 (optional 0.25) |
| 4 | CIS | `anthropic_api.py` adapter + gate + streaming + structured output + refusal-billing rule + spend-limit error mapping + admin guard / `model_via` + cost-page bucket + AA-919 / AA-927 guard entries + tests; `anthropic` SDK dependency | 2.75 |
| 5 | CIS | `anthropic_batch.py` + `s1_batch_v2.py` + 3 job kinds + checkpointed ingest (`S1Checkpoint`) + v2 batch seed (`applies()`, `graph.py`) + wave attribution + batch cost rows + tests | 3 |
| 6 | Root + Partner | ADR (amends S235 / ADR 0005 provider list; ≥2 repos → `docs/adr/`), CONTEXT.md, tenant terms wording, `llm-routes.md` regeneration | 0.5 |
| | | **Total** | **≈ 7.5** |

- PRs 1, 2, 4 (≈ 4 days) give the **fallback**. PR 5 adds **batch**.
- The prior estimate of 3–5 days left out the v2-aware batch and the ingest checkpoint.
- PRs 2, 4 and 5 touch auth/secret, migration and CI, so they need an independent review before merge (dev-phase rule).

### 6.2 Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Data leaves AWS; tenant terms mention AWS only | Contract and trust | Tech lead decision + terms change before tenant stages route there (§4) |
| Evaluation-tier limits at sign-up (numbers not published) | First wave throttled | Sandbox traffic before the wave; request a tier increase early [V rate-limits] |
| Prepaid balance runs out | Direct calls fail | Auto-reload + spend alerts; route falls back to Bedrock |
| Batch takes up to 24 h, requests may expire; cache hits best-effort | Slower waves | Expired → on-demand fallback (AA-606 pattern); poll job is not deploy-blocking |
| Batch data kept 29 days, not ZDR-eligible | Governance | Accept explicitly (§4) |
| Same model, different surface (Messages `output_config` vs Converse tool JSON) changes outputs slightly | Quality drift | Shadow / eval before primary use; batch pilot on 3 → ≤50 tours against the wave50 baseline |
| Sonnet 5.5 refusals; no server-side `fallbacks` inside batch [V batch] | Some tours unwritten | `refusal` → unusable → on-demand route (Bedrock first) |
| `api_style='anthropic_native'` ambiguity with TP's fork | Low: TP skips rows without a Bedrock profile (`_no_account`) | Optional PR 3 message; dispatch on `provider` in CIS |
| Anthropic spend outside provider-wide daily caps (`cost_guard` counts `bedrock%` / `openai` only) | Uncapped fallback spend in a `bedrock`-budget job | PR 2 cost-guard mapping + spend_budget CHECK |
| Our own workspace spend limit returns 400, read as a code bug | Noisy errors, wrong triage | §5.3 error mapping by message |
| Provider mislabelled `bedrock-native` in `llm_call_log` | Wrong cost attribution | `_normalize_model_provider` rule + test |
| FCT withholding gross-up; no VN VAT invoice [U] | Accounting cost | Accountant question before the first purchase |
| One person's card / personal email as org owner | Lock-out, as happened with acc3's org | Company mailbox owner, ≥2 admins |

### 6.3 Recommended rollout

1. **Account (tech lead, no code):**
   - Create the org under the company mailbox and accept the Commercial Terms.
   - Enter the legal name, address and MST.
   - Create workspaces `aa-dev-runtime` / `aa-batch` / `aa-sandbox`, with spend limits and alerts.
   - Buy a small prepaid balance and set auto-reload.
   - Write down the data decision (§4).
2. **Sandbox key:**
   - Merge PRs 1, 2 and 4 with `LLM_ANTHROPIC_DIRECT` off and rows disabled.
   - Turn the flag on and enable `anthropic-haiku-5-5` only.
   - Run the contract test (~$0.01, logged as `adhoc_<issue>`).
3. **Fallback live:**
   - Enable `anthropic-sonnet-5-5` / `-4-6` / `-haiku-4-5`.
   - Append them as the **last** fallback on Claude writer/validate routes.
   - Verify with a forced-failure test: disable the Bedrock row on a test stage, call, re-enable. Cost: cents.
4. **Shadow on one stage:**
   - `anthropic-sonnet-5-5` as shadow on a low-volume writer stage (e.g. `supply_content_writer`), 10%.
   - Compare in `llm_shadow_log` for a few days.
   - Do not shadow `s1_generate` during a wave: it would add 10% to the writer cost.
5. **Batch for the next S1 wave** (PR 5):
   - Follow the wave ladder: real pilot 3 tours → ≤50 → one country.
   - Report cost per stage, wave total and $/tour against **$0.0768/tour** (wave50) and the $120 cap.
   - Writer target ≈ **$0.030/tour**.
   - Keep the wave stop rules.

---

## 7. Fact check

Adversarial re-check, 29/10/2026 (subagent, read-only, no paid call). Every external fact was re-fetched from the
official page named (platform.claude.com `.md` docs, support.claude.com, anthropic.com legal and supported-countries);
every code claim was re-read in the repo. Corrections were made in place above; this list records them.

**Confirmed unchanged (external):** all list, batch and cache prices in §1.1/§1.2/§1.4/§5.2 (incl. 0.05x cache reads
on Sonnet/Opus 5.5, Haiku 5.5 $0.10/$0.50 ≤100K and $0.50/$2.50 above, 1.25x / 2x writes); batch -50% and stacking
with caching and data residency; 100,000 requests / 256 MB; "most batches … within 1 hour", 24 h expiry, 29-day
results; disallowed `stream` / `speed` / `fallbacks` / `max_tokens: 0`; workspace scoping; spend-limit overshoot;
`custom_id` regex; async validation; 30–98% best-effort batch cache hits and the 1-hour TTL tip; batch not
ZDR-eligible (29-day retention); cache minimums 512 / 1,024 / 4,096; rate-limit tiers (Start 1,000 / 2M / 400K;
Build 5,000 / 5M / 1M), batch queue limits, cached reads excluded from ITPM, Evaluation tier, monthly caps
$500 / $1,000 / $200,000; standard tier "best-effort availability", Priority Tier no longer sold; SDK retries twice
honouring `retry-after`; 529 `overloaded_error`; `inference_geo: "us"` 1.1x, 10% Bedrock regional premium; default
non-retention, Covered Models 30 days, flagged content up to 2 years, no training without permission; structured
outputs GA, schema limits (24 optional / 16 union params), 24 h schema cache, `transform_schema()`; Commercial Terms
B (no training), C (DPA), H.2 (gross-up), I.2.a (Anthropic 30 days' notice); invoice details fixed at issue time.

**Corrected (external facts):**
1. Batch platforms: also GA on Claude Models on Google Cloud (Anthropic managed), not "Claude API and Claude Platform
   on AWS only" (§1.1).
2. `canceled` batch results are also unbilled; refused batch items come back as `succeeded` + `refusal`, mint no
   fallback credit, and must be resubmitted by us (§1.1, §5.5).
3. **Refusal billing:** a refusal is not always billed. Pre-output refusals are billed only in `bio`,
   `frontier_llm`, `reasoning_extraction`; mid-stream refusals bill input + streamed output. The draft treated every
   refusal as a billed reply, which would over-log cost (§1.3, §5.3, §5.8).
4. Our own org/workspace spend limit returns **HTTP 400** `invalid_request_error`, not 429; only the tier cap is a
   429, identifiable by `error.details.error_code = "enforced_spend_limit_reached"` (§1.5, §3, §5.3).
5. The Default Workspace cannot have a **spend** limit; the draft said rate and spend limits (§1.5).
6. Prepaid-credit quote corrected to the help page's wording; credit expiry (1 year, not extendable) now verified
   directly, plus "non-refundable" (§3).
7. Vietnam availability added with its source and conditions (location, entity incorporation/HQ/ownership) (§3).
8. Usage gives the cache-write TTL split (`cache_creation.ephemeral_5m/1h_input_tokens`); caches are workspace-
   isolated, so runtime and batch workspaces never share entries (§1.2, §5.5).
9. Non-streaming calls with large `max_tokens`: the SDK enforces an expected-duration check (10 min) and the docs
   recommend streaming; the schema path now streams too (§5.3).

**Corrected (integration design vs. code):**
10. Logging: the gateway does write `llm_call_log` rows, for billed-but-unusable attempts (`_call_key_logged` →
    `log_gateway_billed_failure`); their `_billed_usage` dicts carry no provider, so `_normalize_model_provider` must
    learn `anthropic-` (§5.1). `llm_call_log` has no cache columns.
11. **TripPlanner KeyError claim was wrong:** `_accounts()` drops accounts absent from `model.profiles`, so an
    Anthropic row is skipped with `_no_account`. PR 3 is now optional (§5.2, §6).
12. **Missed:** `spend_budget_provider_check` lacks `anthropic`; `cost_guard` provider-wide day sums count only
    `bedrock%` / `openai`, so Anthropic spend escapes provider-wide daily caps (§5.2 item 5, §6.2).
13. **Missed:** new catalog rows need `callable_via = {llm_client}` or the admin route editor refuses them (§5.2).
14. **Missed:** `model_via()` needs an `anthropic` branch; the S235 guard lives around lines 194–245, not 123; the
    judge-stage refusal already exists via `vendor == 'anthropic'` (§5.3).
15. **Missed:** AA-919 `$0` guard (`golden_set/llm_guard.ENTRY_POINTS`) and AA-927 call-site registry
    (`HELPER_NAMES`) must include the batch submit path (§5.3).
16. `_execute_run_tour` has no `writer_version` parameter; v2 seeding needs `s1_writer_v2_live.applies()` and the
    `graph.py` seed changed; ingest idempotency should reuse `S1Checkpoint` (AA-993 G2) (§5.5).
17. **Missed:** batch jobs must carry the wave id so `waves/report.py` counts the batch writer cost (§5.5).
18. `llm_openai_fallback_used` is emitted in `_call_route`, not the adapter; place the new policy event there (§5.3).
19. Haiku 5.5 long-prompt (>100K) pricing cannot be expressed in one catalog row; flagged (§5.2).
20. Effort: ≈ 7.25 → **≈ 7.5 dev-days**; fallback slice ≈ 4 days (§0, §2.4, §6.1).

**Still unverified [U]:** Evaluation-tier numbers; exact error for an empty prepaid balance; any SLA for self-serve
orgs; Bedrock price of Sonnet 5.5 cache reads (our catalog's 0.2 looks copied from Sonnet 5); FCT / VAT-invoice
treatment (accountant question); whether an explicit SDK `timeout` bypasses the non-streaming duration check.

**Conclusion after the check:** unchanged in direction. Adding the Claude API is worth it mainly as a Claude path
outside AWS and the reseller, with batch as a modest saving (≈ $24 per full catalogue rewrite, ≤ ≈ $106 in a heavy
wave month). Cost logging must follow the refusal-billing rule and the cost guard must learn the new provider before
the fallback goes live.

