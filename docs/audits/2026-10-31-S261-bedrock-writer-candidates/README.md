---
id: OPS-08-s261-bedrock-writer-candidates
title: "Bedrock non-Claude writers on acc2: 16-model smoke test for AA tour writing (S261)"
description: "16 model Bedrock không phải Claude/GPT gọi được trên acc2 (us-west-2); một bài viết mẫu kiểu AA chấm 2 góc độc lập (bám nguồn, văn phong), nghiên cứu giá/ngữ cảnh/JSON/giấy phép, danh sách A/B."
type: report
status: active
owner: nghiep
audience: [engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-1002, AA-642]
---

# Model viết bài trên Bedrock acc2 ngoài Claude/GPT (S261, 31/10/2026)

Tác nhân: Claude Code. Cách làm: một prompt viết tour kiểu AA (nguồn tổng hợp, luật không bịa) gọi thật trên acc2
us-west-2 (`maxTokens` 1.200, tổng chi phí dưới 0,10 USD); mỗi bài do 2 agent chấm độc lập (bám nguồn, văn phong);
nghiên cứu giá và đặc tính từng họ; tổng hợp. **Một bài mẫu không phải kết luận chất lượng**: cần A/B thật trên bộ
regression writer (thử 3 tour rồi ≤ 50, báo chi phí trước). Tech lead chốt S261: chưa đổi route nào.

> **Sửa (tech lead, 31/10):** tour AA viết bằng **tiếng Anh**. Dòng "VI:" trong prompt thử là thừa; mọi nhận xét về
> tiếng Việt bên dưới **không phải tiêu chí** cho writer S1 và không được dùng để xếp hạng. Bảng này cũng chưa đối chiếu
> với thiết kế LLM gateway đã duyệt: phần đó ở `docs/audits/2026-10-31-S261-llm-gateway-design-gap/` (đang làm).

| Model | Bám nguồn (0–10) | Văn phong (0–10) |
|---|---|---|
| `us.amazon.nova-pro-v1:0` | 7 | 5.5 |
| `us.amazon.nova-2-lite-v1:0` | 6 | 5 |
| `us.meta.llama4-maverick-17b-instruct-v1:0` | 8.5 | 6 |
| `deepseek.v3.2` | 7 | 7.5 |
| `us.deepseek.r1-v1:0` | 6 | 5.5 |
| `qwen.qwen3-235b-a22b-2507-v1:0` | 7 | 7.5 |
| `qwen.qwen3-next-80b-a3b` | 6 | 7 |
| `mistral.mistral-large-3-675b-instruct` | 6 | 6 |
| `moonshotai.kimi-k2.5` | 6 | 7.5 |
| `us.moonshotai.kimi-k3` | 9.5 | 6 |
| `minimax.minimax-m2.5` | 8 | 6 |
| `zai.glm-5` | 9 | 7 |
| `zai.glm-4.7` | 7 | 6 |
| `openai.gpt-oss-120b-1:0` | 6 | 5 |
| `nvidia.nemotron-super-3-120b` | 7 | 4 |
| `google.gemma-3-27b-it` | 8.5 | 6 |

Bài mẫu từng model: thư mục [`samples/`](samples/) (prompt + output).

## Tổng hợp và danh sách A/B (tiếng Anh)

# Bedrock non-Claude writers on acc2: synthesis for the tech lead (31/10/2026)

All 16 models answered on acc2 (us-west-2), using one short prompt and one tour (3 days Ninh Binh and Ha Long). That is a smoke test. It does not decide quality. Data path is the same for all 16: they are AWS-served under the `AmazonBedrock` billing code, not Marketplace. Latency and token counts come from the probe logs in `/home/nghiep/projects/AA-Ecosys/.tmp-session/S261/bedrock-writers/raw_*.txt`.

Probe artifact: Kimi K3 and gpt-oss-120b stopped at the probe's 1,200-token output limit (`stopReason=max_tokens`) because reasoning was on. Their cut-off VI lines come from this setting, not from the models' writing. GLM-4.7 and Nemotron also have broken VI tokens, but they finished normally (`end_turn`), so those are real defects.

## 1. Ranked table

Ranked by fidelity, then style.

| # | Model | Fid | Style | Invented facts (short) | $/1M in/out | Context / max out | JSON schema | Latency / out tok | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Kimi K3 `us.moonshotai.kimi-k3` | 9.5 | 6 | only soft adjectives; "final morning" tai chi | 3.30 / 16.50 | 1M / ? | Yes (set reasoning via Invoke or Chat Completions) | 3.8s / 1200 (cap hit) | **A/B shortlist (premium arm).** Most faithful. Must run with reasoning `none`; price is about 5–18x the others. Only shortlisted model callable from us-west-1. |
| 2 | GLM-5 `zai.glm-5` | 9 | 7 | "traditional", "scenic"; VI "sports" | 1.00 / 3.20 | 200K / 128K | Yes | 2.5s / 196 | **A/B shortlist (lead candidate).** Best fidelity and style together, right length, no reasoning overhead seen. VI dropped accents on "Ninh Bình". |
| 3 | Llama 4 Maverick | 8.5 | 6 | "leisurely" | 0.24 / 0.97 | 1M / 8K | No (tools only, no tools while streaming) | 1.2s / 142 | **Judge/validate only.** Scores high because it leaves things out: 90 words, no meals or times. Legacy, EOL 2027-03-30. |
| 4 | Gemma 3 27B | 8.5 | 6 | plural "hidden caves", "explore the bay" | 0.23 / 0.38 | 128K / 8K | Yes | 2.6s / 225 | **Judge/validate only.** Legacy, EOL 2027-03-30. Added a markdown heading. Probe Gemma 4 31B instead. |
| 5 | MiniMax M2.5 | 8 | 6 | "rise early", "Vietnamese cuisine" | 0.30 / 1.20 | 196K / 8K | Yes | 6.6s / 882 | **Judge/validate only.** Always thinks, so about 4x the output tokens. 147 words. VI accent and idiom errors. |
| 6 | Qwen3 235B 2507 | 7 | 7.5 | "tai chi at sunrise", "comfortable", "Vietnamese dishes" | 0.22 / 0.88 | 256K / 8K | Yes | 1.8s / 183 | **A/B shortlist (budget arm).** Cheapest strong writer, clean format, Apache 2.0. Max output is 8K. |
| 7 | DeepSeek V3.2 | 7 | 7.5 | "traditional junk", "relax on deck", "cruise back" | 0.62 / 1.85 | 164K / 8K | Yes | 4.2s / 221 | **A/B shortlist.** Best length and British spelling compliance (124 words), MIT licence. The invented boat type and deck time need checking on the full set. |
| 8 | GLM-4.7 | 7 | 6 | "sunrise tai chi", "hearty brunch" | 0.60 / 2.20 | 203K / 128K | Yes | 3.6s / 212 | **Not suitable.** Garbled VI token ("đ đêm"). Legacy. GLM-5 is better on every point. |
| 9 | Nova Pro | 7 | 5.5 | "dinner under the stars" | 0.80 / 3.20 | 300K / 10K | No (tools only) | 2.9s / 372 | **Not suitable.** Purple brochure tone, 145 words, invented view, calqued VI. |
| 10 | Nemotron Super 3 120B | 7 | 4 | "dine under the stars", "by 16:00" | 0.15 / 0.65 | 256K / 32K | Yes | 1.5s / 228 | **Judge/validate only (English checks).** Fastest and cheap, reasoning can be switched. VI is broken ("lottorng", "Chu trình"). |
| 11 | Kimi K2.5 | 6 | 7.5 | "traditional junk", "greet dawn", "hidden lagoons", "by 16:00" | 0.60 / 3.00 | 256K / 16K | Yes | 2.3s / 248 | **Not suitable.** Reads well but invents more than K3. |
| 12 | Qwen3 Next 80B | 6 | 7 | "sunrise", "by 16:00", "Halong" | 0.14 / 1.20 | 256K / 8K | Yes | 1.8s / 207 | **Judge/validate only.** Cheap and fast, fine for short or classification stages. |
| 13 | Mistral Large 3 | 6 | 6 | "evening" kayaking, "exquisite cruise", "gentle" vs moderate fitness | 0.50 / 1.50 | 256K / 32K | Yes | 2.0s / 224 | **Not suitable.** Invents a time of day, contradicts the fitness level, adds a markdown heading. |
| 14 | DeepSeek R1 | 6 | 5.5 | dusk on deck, "bay vistas", "by 16:00" | 1.35 / 5.40 | 128K / 8K | No | 4.5s / 795 | **Not suitable.** Legacy, not in us-west-1, no JSON, always reasons, expensive. |
| 15 | gpt-oss-120b | 6 | 5 | "dinner under the stars", "downstream", "by 16:00" | 0.15 / 0.60 | 128K / 16K | Tools only | 6.1s / 1200 (cap hit) | **Judge/validate only.** Cheapest reasoning model, and reasoning cannot be turned off, which suits a judge. Weak as a writer. |
| 16 | Nova 2 Lite | 6 | 5 | cooking class merged into dinner, "by 16:00", VI "đua thuyền" (racing) | 0.33 / 2.75 | 1M / 64K | No (tools only) | 2.1s / 244 | **Short stages only.** Reachable from us-west-1 with a 1M context, but not a writer. |

## 2. Shortlist and stage fit

**Writer A/B: trial 3 tours, then at most 50.** Use the production S1 prompt and JSON schema, not this probe prompt. Run through `LLMClient` with `stage=adhoc_<issue>` so every call lands in `shared.llm_call_log`.
1. **GLM-5**: lead candidate.
2. **DeepSeek V3.2**: different model family, strong compliance.
3. **Qwen3 235B 2507**: budget arm.
4. **Kimi K3, reasoning `none`**: fidelity ceiling and the us-west-1 fallback. Cap its share of the run because of price.
5. Baseline: existing Sonnet 5.5 outputs on the same regression set. Re-run Sonnet live once acc3 is back.

**Judge, validate and short stages:**
- **gpt-oss-120b** as judge. Reasoning is always on, it is cheap, and it comes from a different family than every shortlisted writer.
- **Nemotron Super 3** for validate (strict JSON, reasoning can be switched, fastest). English text only, because its Vietnamese failed.
- **Qwen3 Next 80B** for short and classification stages.
- **Llama 4 Maverick / Nova 2 Lite** only where a stage must stay in us-west-1. Llama 4 Maverick is EOL in 2027-03, so treat it as interim.
- Rule: the judge's model family must differ from the writer's.

## 3. Risks

- **Access can change.** These models are AWS-served, not Marketplace. Even so, GLM-5.3 and Grok were refused on acc2 with "not available for this account", so access is gated per model and per account, not by billing code. In the other direction, Cohere is listed as Marketplace-sold, yet Cohere Embed v4 runs on acc2 today. The billing code does not predict access in either direction.
  - Mitigation: keep at least two families live in `llm_role_config` with a fallback chain, and re-run the access-matrix probe on a schedule.
  - Do not plan on Anthropic, Cohere chat, Writer or AI21 on acc2.
- **Region.** Only Nova, Llama 4 and Kimi K3 are reachable from us-west-1 (through `us.`/`global.` profiles). Every other shortlisted model is us-west-2 only. Before the A/B, confirm two things:
  - the gateway supports a region per model;
  - acc2's IAM/SCP allows `bedrock-runtime` in us-west-2.
- **Reasoning cost and latency.**
  - Kimi K3: reasons at `max` effort by default, and output tokens count 10x against quota.
  - gpt-oss: reasoning cannot be turned off.
  - MiniMax: 882 output tokens for about 150 words.
  - R1: always reasons.
  - A low `max_tokens` cuts outputs short; seen here on 2 models. Set an explicit reasoning effort and a token budget per stage, and log reasoning tokens.
- **Vietnamese quality.** Most VI lines had problems:
  - missing diacritics on place names (Nova 2 Lite, MiniMax, GLM-5);
  - garbled tokens (GLM-4.7, Nemotron);
  - a wrong verb (Nova 2 Lite: "đua" = racing);
  - repeated calques ("chèo thuyền tre", which implies guests row; "đi thuyền tre" is correct).

  No model is safe for Vietnamese without a native reviewer. Add deterministic gates for:
  - place-name diacritics;
  - non-word tokens;
  - truncation (no final full stop).
- **Systematic fidelity failures** that call for validator rules, not one-off patches:
  - invented time of day (sunrise, dawn, dusk, evening): 7 models;
  - "around 16:00" hardened to "by 16:00": 6 models;
  - "dinner under the stars": 3 models;
  - invented vessel type ("junk"): 2 models.

  Length compliance was also poor: roughly half the models missed 110–130 words.
- **Licence.** No blockers. Llama 4 requires a "Built with Llama" credit. The Kimi and MiniMax modified-MIT clauses apply only at very large scale. Gemma has a prohibited-use policy.
- **Lifecycle.** Llama 4 Maverick, GLM-4.7, R1 and Gemma 3 are all Legacy with EOL 2027-03-30. Do not build long-term on them.
- **8K output limit.** DeepSeek V3.2, Qwen3 235B, Qwen3 Next, Llama 4 and Gemma 3 cap output at 8K tokens. Check this against the real length of S1 output plus its JSON.

## 4. Still to measure

1. **Writer A/B** on the regression set: fidelity violations per tour, regression-gate pass rate, length compliance, and VI quality rated by a native speaker. Start with 3 tours, then at most 50.
2. **Cost per tour** (including reasoning tokens) and p50/p95 latency, taken from `llm_call_log`, for each model.
3. **Reasoning switches** actually working on Bedrock:
   - Kimi K3 `reasoning_effort=none` via Invoke;
   - GLM-5 and DeepSeek V3.2 hybrid modes;
   - Qwen3 2507 confirmed non-thinking;
   - MiniMax confirmed as always thinking.
4. **Strict JSON on the real S1 schema:** validity rate, first-compile delay (about 90s per new schema), and behaviour on long outputs.
5. **acc2 limits in us-west-2:** TPM/RPM quotas per model, and that IAM/SCP allows cross-region calls.
6. **Judge calibration:** gpt-oss and Nemotron against Jev and human labels.
7. **Models not yet probed:** Gemma 4 31B (0.14 / 0.40, Apache 2.0), and Nova 2 Pro, which is priced but does not appear in `list-foundation-models`.
8. **Access drift:** re-run the acc2 access matrix weekly.

## Nghiên cứu từng họ model

**Bedrock open-weight / Nova models for long-form EN→VI travel copy with strict JSON: research as of 2026-10-31**

How I checked (read-only, no model calls):
- **Prices:** AWS Price List API, service code `AmazonBedrock`, regions us-east-1 and us-west-2, pulled 2026-10-31 (effectiveDate 2026-10-01). This is the machine-readable source behind https://aws.amazon.com/bedrock/pricing/. The HTML page is rendered by JavaScript, so I did not read it directly. Prices are on-demand Standard tier, in USD per 1M tokens, input/output.
- **Model facts:** the model cards at docs.aws.amazon.com/bedrock/latest/userguide/model-card-*.html, plus `list-foundation-models` and `list-inference-profiles` run on acc2 in us-west-1, us-west-2 and us-east-1.

**Who sells it.** AWS's "product ID" page says DeepSeek, Google, Meta, MiniMax, Mistral AI, Moonshot AI, NVIDIA, Qwen, Z.AI and OpenAI gpt-oss are **not sold through AWS Marketplace** ("available to all Amazon Bedrock users and don't require a AWS Marketplace subscription"). Nova is Amazon's own model. The Price List agrees: every model below is under the AWS-billed `AmazonBedrock` code. The Marketplace-sold models sit under `AmazonBedrockFoundationModels`: Anthropic, Cohere, AI21, Writer, TwelveLabs, Stability, and OpenAI GPT-6 Astra.

So "not Marketplace" does not guarantee access on acc2. Our live access matrix (`docs/audits/2026-10-31-S261-aws-bedrock-org-access/model-access-matrix-2026-10-31.md`) shows:
- **Works on acc2:** Nova Lite, Nova Pro, Nova 2 Lite, Llama 4 Maverick/Scout, Kimi K3.
- **Refused on acc2:** GLM-5.3 and Grok, with "not available for this account".

| Model (Bedrock ID) | $/1M in / out | Context / max out | Structured output (JSON schema) · tool use | Reasoning | Regions / profile (acc2 = us-west-1) | Licence (commercial) | Lifecycle |
|---|---|---|---|---|---|---|---|
| Nova Pro `amazon.nova-pro-v1:0` | 0.80 / 3.20 | 300K / 10K | Structured output not supported (card) · tools yes via Converse (Nova user guide) | none | `us.` profile, sources include us-west-1; in-region us-east-1 | AWS service terms | Active (launched 2024-12) |
| Nova 2 Lite `amazon.nova-2-lite-v1:0` | 0.33 / 2.75 (us geo); 0.30 / 2.50 (global) | 1M / 64K | Structured output not supported · tools yes | Off by default; turn on with `reasoningConfig` (low/med/high) | `us.` and `global.` profiles, both include us-west-1 | AWS service terms | Active |
| Nova Premier | 2.50 / 12.50 still listed in Price List | – | – | – | Only the `us.` profile is still listed; the base model returns "reached the end of its life" (us-east-1/2) | – | **EOL**, not usable |
| Llama 4 Maverick `meta.llama4-maverick-17b-instruct-v1:0` | 0.24 / 0.97 | 1M / 8K | Structured output not supported · tools yes, but not while streaming | none | `us.` profile only, includes us-west-1 | Llama 4 Community: commercial OK; "Built with Llama" attribution; licence needed above 700M MAU; EU restriction on multimodal use | Card says **Legacy**, EOL 2027-03-30; the API still says ACTIVE |
| DeepSeek V3.2 `deepseek.v3.2` | 0.62 / 1.85 | 164K / 8K | Yes · yes | No reasoning control on the Bedrock card. DeepSeek's own model is hybrid; needs a test | In-region us-east-1/2 and us-west-2; no profile; **not in us-west-1** | MIT | Active |
| DeepSeek R1 `deepseek.r1-v1:0` | 1.35 / 5.40 | 128K / 8K | Neither listed on the card | Always reasons (chain-of-thought) | `us.` profile, sources us-east-1/2 and us-west-2 only; **not us-west-1** | MIT | **Legacy**, EOL 2027-03-30 |
| Qwen3 235B 2507 `qwen.qwen3-235b-a22b-2507-v1:0` | 0.22 / 0.88 | 256K / 8K | Yes · yes | Card says "Reasoning: Supported", but the licensed checkpoint is Instruct-2507 (non-thinking). This conflicts; needs a test | bedrock-runtime in us-east-2 and us-west-2 (us-east-1 only via the OpenAI-compatible endpoint) | Apache 2.0 | Active |
| Qwen3 Next 80B `qwen.qwen3-next-80b-a3b` | 0.14 / 1.20 (only SKU listed is for the OpenAI-compatible endpoint) | 256K / 8K | Yes · yes | Same conflict as above (Instruct checkpoint) | In-region us-east-1/2 and us-west-2 | Apache 2.0 | Active |
| Mistral Large 3 `mistral.mistral-large-3-675b-instruct` | 0.50 / 1.50 | 256K / 32K | Yes · yes | none | In-region us-east-1/2 and us-west-2 | Apache 2.0 (Hugging Face); card links AWS third-party terms | Active |
| Kimi K2.5 `moonshotai.kimi-k2.5` | 0.60 / 3.00 | 256K / 16K | Yes · yes | Card is silent. Moonshot's docs: thinking on by default, `thinking:{type:disabled}` turns it off on their API | In-region us-east-1/2 and us-west-2 | Modified MIT: "Kimi K2.5" UI credit above 100M MAU or $20M/month revenue | Active |
| Kimi K3 `moonshotai.kimi-k3` | 3.30 / 16.50 (us geo); 3.00 / 15.00 (global) | 1M / max output not stated | Yes · yes | Reasons by default at effort `max`. `none` turns it off. Converse does not validate `reasoning_effort`, so set it through Chat Completions, Responses or Invoke. Converse has known multi-turn and document limits. Output tokens count 10x against quota | `us.` and `global.` profiles only, include us-west-1. **Works on acc2** | Kimi K3 License: MIT plus a credit clause and a model-as-a-service clause; neither applies through Bedrock (a "certified inference partner") | Active (launched 2026-09-18; at least 45 days' EOL notice) |
| MiniMax M2.5 `minimax.minimax-m2.5` | 0.30 / 1.20 | 196K / 8K | Yes · yes | Card is silent. Third-party listings say thinking-only; assume thinking tokens are always spent | In-region us-east-1/2 and us-west-2 | Modified MIT (Hugging Face) | Active |
| GLM-5 `zai.glm-5` | 1.00 / 3.20 | 200K / 128K | Yes · yes | Card is silent. On other platforms it is hybrid with thinking on by default | In-region us-east-1/2 and us-west-2 | MIT | Active |
| GLM-4.7 `zai.glm-4.7` | 0.60 / 2.20 | 203K / 128K | Yes · yes | Same as GLM-5 | In-region us-east-1/2 and us-west-2 | MIT | **Legacy**, EOL 2027-03-30 |
| (also on Bedrock) GLM-5.3 `zai.glm-5.3` | not found in Price List | 1M / 128K | Yes · yes | Always on; effort low…max, default max; cannot be turned off | `us.` and `global.` profiles, include us-west-1. **Refused on acc2** | GLM-5.3 licence (MIT-like) | Active (launched 2026-10-05) |
| gpt-oss-120b `openai.gpt-oss-120b-1:0` | 0.15 / 0.60 | 128K / 16K | Structured output not listed on the card · tools yes (client and server-side) | On by default, effort low/med/high; cannot be turned off | In-region us-east-1/2 and us-west-2 | Apache 2.0 | Active |
| Nemotron 3 Super 120B `nvidia.nemotron-super-3-120b` | 0.15 / 0.65 | 256K / 32K | Yes · yes | Effort none/low/med/high; `none` turns it off | In-region us-east-1/2 and us-west-2 | NVIDIA Open Model License (commercial OK) | Active |
| Gemma 3 27B `google.gemma-3-27b-it` | 0.23 / 0.38 | 128K / 8K | Yes · yes | none | In-region us-east-1/2 and us-west-2 | Gemma Terms (commercial OK, with the prohibited-use policy) | **Legacy**, EOL 2027-03-30. Newer Gemma 4 31B: 0.14 / 0.40, Apache 2.0 |

Notes:
1. **Routing from acc2.** In us-west-1, only Nova Pro, Nova Lite, Nova 2 Lite, Llama 4 Maverick/Scout, Kimi K3 and GLM-5.3 can be called (through `us.`/`global.` profiles). Every in-region-only model above has to be called on the us-west-2 (or us-east-1/2) bedrock-runtime endpoint. They are not in us-west-1.
2. **Strict JSON.** Bedrock's native structured output uses Converse `outputConfig.textFormat` (json_schema) or `response_format` on Invoke for open-weight models. It also supports `strict: true` on tools. The first use of a new schema can take about 90 s to compile; it is then cached for 24 h. Nova Pro, Nova 2 Lite and Llama 4 Maverick do not support it, so JSON there has to come from forced tool use or prompting.
3. **Data conflicts to flag.** The Price List description for Nova Pro us-west-2 output says "$0.0008… input-tokens", but the actual price is $0.0032/1K. Lifecycle for Llama 4 Maverick, GLM-4.7, R1 and Gemma 3 27B is Legacy on the cards but ACTIVE in the API. Nova 2 Pro is priced (1.375 / 11.00) but returns no model in `list-foundation-models` for us-east-1 or us-west-2.
4. **Reasoning I could not confirm.** Bedrock does not document a reasoning switch for Kimi K2.5, MiniMax M2.5, GLM-5/4.7, DeepSeek V3.2 or Qwen3. Those cells come from the vendors and other platforms, so a cheap test call on each is needed before relying on them.

Sources:
- AWS Price List API, service codes `AmazonBedrock` / `AmazonBedrockFoundationModels`, us-east-1 and us-west-2, pulled 2026-10-31 (effective 2026-10-01). Page equivalent: https://aws.amazon.com/bedrock/pricing/
- Model cards, read 2026-10-31: https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards.html and the card for each model: model-card-amazon-nova-pro, -amazon-nova-2-lite, -meta-llama-4-maverick-17b-instruct, -deepseek-deepseek-v3-2, -deepseek-deepseek-r1, -qwen-qwen3-235b-a22b-2507, -qwen-qwen3-next-80b-a3b, -mistral-ai-mistral-large-3, -moonshot-ai-kimi-k2-5, -moonshot-ai-kimi-k3, -minimax-minimax-m2-5, -zai-glm-5, -zai-glm-4-7, -zai-glm-5-3, -openai-gpt-oss-120b, -nvidia-nemotron-super-3-120b, -google-gemma-3-27b-pt (.html)
- Not sold through Marketplace: https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-product-ids.html (2026-10-31)
- Model access and Marketplace auto-enable: https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html (2026-10-31)
- Structured output: https://docs.aws.amazon.com/bedrock/latest/userguide/structured-output.html (2026-10-31)
- Nova tool use: https://docs.aws.amazon.com/nova/latest/userguide/tool-use.html (2026-10-31)
- AWS CLI on acc2 (2026-10-31): `bedrock list-foundation-models` and `list-inference-profiles` (us-west-1, us-west-2, us-east-1); `get-foundation-model amazon.nova-premier-v1:0` returned EOL
- Licences (2026-10-31): huggingface.co/{moonshotai/Kimi-K3, moonshotai/Kimi-K2.5, deepseek-ai/DeepSeek-V3.2, deepseek-ai/DeepSeek-R1, zai-org/GLM-5.3, Qwen/Qwen3-235B-A22B-Instruct-2507, Qwen/Qwen3-Next-80B-A3B-Instruct, openai/gpt-oss-120b}/raw/main/LICENSE; Hugging Face API licence tags for MiniMax-M2.5, GLM-5, GLM-4.7, Mistral-Large-3-675B-Instruct-2512, gemma-3-27b-it, NVIDIA-Nemotron-3-Super-120B; https://www.llama.com/llama4/license/ and https://www.llama.com/llama4/use-policy/
- Reasoning behaviour on other platforms (not Bedrock), 2026-10-31: https://platform.moonshot.cn/docs/guide/use-kimi-k2-thinking-model, https://docs.together.ai/docs/inference/chat/reasoning, https://help.aliyun.com/en/model-studio/deep-thinking, https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-bedrock-minimax-glm
- acc2 access test: /home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-31-S261-aws-bedrock-org-access/model-access-matrix-2026-10-31.md

Raw downloads are in /tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/cad059ca-b2c4-41de-9344-dda6ca944497/scratchpad/:
- price lists `pr-*.json`
- model lists `fm-*.json`
- inference profiles `ip-*.json`
- model cards `cards/`
- licences `lic/`
