# Bedrock models available vs. the LLM gateway catalog (S246, 21/10/2026)

Read-only check: `aws bedrock list-foundation-models --by-output-modality TEXT` on acc1 (pqnghiep-admin),
acc2 (aa365-admin) and acc3 (nghiep_aa365), regions us-west-1 / us-west-2 / us-east-1 (raw lists in `fm-*.txt`).
The three accounts list the same models per region (us-west-1: 40, us-west-2: 92, us-east-1: 95).
"Listed" is not "callable": acc2 Claude/GPT calls are blocked by the payer (TrueIDC), so production
routes go through acc3 (and acc1 as fallback). New models need one invoke test per account before use.

## Newest per family on Bedrock

| Family | Newest listed | In our catalog (`shared.llm_model_catalog`) |
|---|---|---|
| Claude Haiku | `claude-haiku-5-5` | only Haiku 4.5 (`haiku`, used by 9 stages) |
| Claude Sonnet | `claude-sonnet-5-5` (also `sonnet-5`, 4.6; 4.5 is LEGACY) | `sonnet` = 4.6 on acc1/acc3 but **4.5 (LEGACY) on the acc2 route**; `sonnet-5` |
| Claude Opus | `claude-opus-5-5` | `opus-5-5` |
| Claude Fable | `claude-fable-5-1` | none |
| OpenAI small | `gpt-6-luna` | `gpt-6-luna` (4 stages) and `gpt-5.6-luna` (7 stages, twice the price) |
| OpenAI mid/large | `gpt-6-sol`, `gpt-6.1-sol`, `gpt-6-astra` | `gpt-6-astra` only |
| Embeddings | Cohere Embed v4 | `cohere-embed-v4` |

## Findings

1. **Stages on older or pricier models than needed**
   - 8 stages on `sonnet` ($3 / $15 per Mtok), including the place pipeline `a3_place_days` and `a3_place_locate`, which have no reason to need Sonnet.
   - 7 stages on `gpt-5.6-luna` ($0.20 / $1.20); `gpt-6-luna` is newer and costs half ($0.10 / $0.50).
2. **Catalog gaps:** `claude-haiku-5-5`, `claude-sonnet-5-5`, `gpt-6-sol` / `gpt-6.1-sol` and `claude-fable-5-1` are not in the catalog. Prices must come from the AWS Bedrock pricing page before rows are added (`price_source`).
3. **Stale route:** the acc2 profile of `sonnet` points at Sonnet 4.5, which is LEGACY. acc2 is not used for Claude today, but the row should point at a current model or be dropped.

## Proposed next steps (each is a gateway setting change in admin Settings, then a measured trial)

1. Place pipeline: trial `haiku` vs `gpt-6-luna` against stored Sonnet output (running in S246), then switch both stages.
2. A/B the 7 `gpt-5.6-luna` stages on `gpt-6-luna` (same vendor, half the price), one stage at a time with the eval harness.
3. Add catalog rows for `claude-haiku-5-5` and `claude-sonnet-5-5` (acc3 + acc1 profiles), with one invoke test per account, so stages that need a stronger model can move off Sonnet 4.6.
4. Fix or drop the acc2 Sonnet 4.5 profile.
