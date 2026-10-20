# Self-improving writing for CIS and the tenant portal: state of the art and what fits AA_Ecosys

Research only. No files, Linear or Notion were changed. All URLs accessed 20/10/2026.

## 0. Summary

1. **Fine-tuning is mostly off the table for the current writers.**
   - **Claude:** the only Claude model Bedrock lists for fine-tuning is Claude 3 Haiku (us-west-2), end of life
     10 Sep 2026. Bedrock does not allow new fine-tuning jobs on Legacy or EOL models.
   - **OpenAI:** self-serve fine-tuning (SFT, DPO, RFT) closed to organisations that had never fine-tuned on 7 May 2026;
     closes to all customers on 6 Jan 2027. The dataset-backed prompt optimizer and Evals become read-only on
     31 Oct 2026 and shut down on 30 Nov 2026.
   - **Left:** Amazon Nova (SFT, plus RFT on Nova 2 Lite, us-east-1 only) or open-weight Qwen3-32B / gpt-oss-20B (RFT at
     $80 per training hour, us-west-2). Every one of these means changing the writer model.
2. **The practical path is learning in the prompt, with no retraining,** in four parts, each behind an eval gate:
   (a) a curated lessons/playbook memory (ACE / Dynamic Cheatsheet); (b) per-tenant retrieval of approved exemplars and
   edit pairs; (c) mining human edit diffs into preference descriptions and rules (PRELUDE/CIPHER, LAMP); (d) occasional
   offline prompt optimisation (GEPA or MIPROv2) on a frozen eval set, scored by a judge calibrated against human labels.
   Fine-tuning only becomes worth considering at roughly 1k–10k clean, fidelity-checked edit pairs per task, and only on
   a model we would accept as the writer.
3. **AA already has most of the raw signal but no gated loop.** One finding is a risk today: lessons are auto-activated
   and injected globally, with no eval gate and no tenant scope (§1).

## 1. What AA already has

| Signal / store | Evidence | Use for learning |
|---|---|---|
| Lessons table, written automatically | `shared.pipeline_lessons` (db-schema-reference.md:2876). Written by `flag_fix_node.py:693` `write_lessons_log`, inserting with `is_active = true` (:742-746) | Error-to-rule memory. **Risk:** auto-activated, no eval gate, no `tenant_id` |
| Lessons injected into S1 prompt | `s1_batch.py:108-121` appends every active `S1_rewrite/S1_editor` lesson | Global, unbounded list ("context collapse" per ACE). 0 inserts since stats reset (:4290) |
| Brand-audit lessons | `quality_scores.lessons_extracted jsonb` (:3455); `brand_audit_node.py:159-180` | Candidate rules, to be curated |
| CIS admin edits (A1/S1) | `generated_content.human_edited, edited_at, edit_diff, reviewed_by` (:3411-3414); `admin_pipeline.py:3787-3807` (AA-234) | Edit pairs (once before/after is kept) |
| Admin sentence edits on T9 pieces and T2 versions | `admin_content_quality.py:483-497` (`SentenceApplyBody`: mode, gate, problem, suggestion, spans); audit actions `audit_log.py:63-79` (AA-769, AA-802); `acp_shared.audit_log.details` (~1324 rows, platform-only) | **Best data**: sentence-level error, gate, fix and reason |
| Tenant inline edits (T2) | `tenant_tour_versions.edit_source`, RLS `tenant_isolation` (:2294-2323); `v1_tours.py:1074` | Per-tenant voice signal, must stay in tenant |
| Human quality labels (T9) | `content_piece_label` (:570; AA-791, mig 231); ~1 insert (:4205) | Judge calibration + KPI `minutes_to_fix` |
| Social piece embeddings | `content_piece.content_embedding vector(1536)` + ivfflat, RLS (:531-569) | Ready for per-tenant exemplar retrieval |
| Brand voice examples | `tenant_brand_rules.voice_examples, good_examples` (:3122); versions (:3106); `batch_prompt.py:41-57`, `judge_node.py:157` | Static few-shot slot → make dynamic |
| Prompt regression gate | `prompt_eval_runs` (:2972; pipeline CHECK `s1_old`/`s1_from_atom`); `services/eval/regression.py` (AA-289) | Eval-gate skeleton for S1 only; 0 inserts |
| Cost and decision logs | `llm_call_log` (:2708); `decision_log` (:2464) | Budget; Jev verdicts as fidelity gate |

## 2. State of the art without retraining

### 2.1 Error-to-rule memory with eval gates
- **ACE (Agentic Context Engineering)**, arXiv 2510.04618. Generator / Reflector / Curator; incremental delta updates
  instead of rewriting the context. Failure modes: "brevity bias" and "context collapse". Reported +10.6% on agent
  benchmarks, +8.6% on finance (authors' numbers; no independent replication found).
- **Dynamic Cheatsheet**, arXiv 2504.07952 (EACL 2026). Self-curated persistent memory of short validated snippets.
  Large gains on AIME, Game of 24, GPQA-Diamond — reasoning tasks, not editorial writing.
- **Mapping to AA:** small typed lessons with `scope`, stage/field, example before/after, version; add/retire
  incrementally; new lessons go to shadow first and are A/B'd on a frozen eval set; activate only if the targeted error
  falls and no fidelity metric (Jev `a1_claim_supported`, B-class promise check) regresses. Today `pipeline_lessons`
  does the opposite.

### 2.2 Retrieval of approved exemplars (dynamic few-shot), per tenant
- Liu et al. (arXiv 2101.06804): nearest-neighbour examples beat random examples.
- Anthropic prompting guide: 3–5 examples in `<example>` tags.
- Bertsch et al. NAACL 2025 (arXiv 2405.00200): long-context ICL keeps improving into thousands of demos; no fixed
  crossover with fine-tuning.
- **Mapping:** index human-approved outputs and edit pairs by tenant, channel, destination using `content_embedding`;
  retrieve 3–5 style exemplars per call, always filtered by `tenant_id` (OWASP LLM08:2025); strip entities/facts or
  label "style only"; keep Jev grounding as the gate.

### 2.3 Automatic prompt optimisation against an eval set
- **GEPA** (arXiv 2507.19457, ICLR 2026 oral): reflective, Pareto frontier; beats GRPO ~6 pp avg with up to 35x fewer
  rollouts, beats MIPROv2 by >10 pp. `dspy.GEPA` / `pip install gepa`. Metric can return textual feedback (Jev reasons,
  gate problems).
- **MIPROv2 (DSPy):** Bayesian search over instructions and demos; default `minibatch_size` 35 ≤ valset size.
- **OPRO** (arXiv 2309.03409): up to +8% GSM8K, +50% BBH; secondary source reports 5–20% train/test gap.
- **TextGrad** (Nature 2025; arXiv 2406.07496).
- **Vendor tools:** OpenAI dataset-backed optimizer is deprecated (Evals read-only 31 Oct, shut 30 Nov 2026). Anthropic
  Console prompt-improver URL redirects; status unknown. Console Evaluate tool is documented.
- **Overfitting controls:** held-out test split; larger minibatches (arXiv 2412.07820, 2604.08801); early stopping;
  Pareto/instance-wise selection; manual review of every optimised prompt.
- **Fit with AA caps:** live-generation GEPA/MIPROv2 exceeds "trial ~3, then ≤50"; heavy runs need explicit approval.
  Cheaper: optimise judge/repair prompts on stored outputs.

### 2.4 Learning from human edit diffs
- **PRELUDE/CIPHER** (NeurIPS 2024): infer a natural-language preference from past edits; retrieve the k most similar
  contexts' preferences; no fine-tuning; lowest Levenshtein edit cost on summarisation and email writing.
- **PREDICT** (arXiv 2410.06273): decompose and validate preferences across several trajectories to avoid
  over-generalising one edit.
- **LAMP** (CHI 2025, arXiv 2409.14509): 1,057 LLM paragraphs edited by professional writers; 7-category taxonomy of LLM
  writing problems (clichés, unnecessary exposition, …). Usable as a starting defect taxonomy.
- **Edits as preference pairs:** SALT (arXiv 2310.05857), "Post-edits Are Preferences Too" (WMT 2024), OpenPipe DPO.
- **Mapping:** cluster sentence-edit audit rows by gate/problem → LLM drafts a candidate rule → validate PREDICT-style
  across ≥ N independent edits (ideally > 1 reviewer) → eval gate. KPI: normalised edit distance, `minutes_to_fix`.

### 2.5 Calibrating an LLM judge from human labels
- MT-Bench (Zheng et al. 2023): GPT-4 judge > 80% agreement with humans; position, verbosity, self-enhancement biases.
- Panickssery, Bowman, Feng (NeurIPS 2024): self-preference rises with self-recognition → do not grade a Claude writer
  only with a Claude judge.
- EvalGen (UIST 2024): criteria drift; choose evaluators by agreement with a small human-graded set, re-check over time.
- Practitioner thresholds: Cohen's κ ≥ ~0.6 acceptable; run A/B and B/A; re-validate after model/rubric change.
- **Mapping:** `content_piece_label` is the calibration store; panel labels marked as such; a Nghiệp-approved subset as
  the anchor (avoid circular calibration).

## 3. Fine-tuning options as of 20/10/2026

| Option | Models / region | Price | Data guidance | Fit |
|---|---|---|---|---|
| Bedrock SFT | Nova 2 Lite / Lite / Micro / Pro (us-east-1); Claude 3 Haiku (us-west-2); Llama 3.x (us-west-2) | Nova training price unknown; Llama 2 example $7.99/1M training tokens + $1.95/month storage | Claude 3 Haiku: start 50–100 rows, ≤ 10k train / 1k validation | Claude 3 Haiku EOL; Nova/Llama replace the writer; cross-region data |
| Bedrock RFT (GRPO) | Nova 2 Lite (us-east-1); gpt-oss-20B, Qwen3-32B (us-west-2) | $80/training hour + $1.95/month; Qwen3-32B $0.20/$0.78 per 1M; gpt-oss-20b $0.09/$0.39 | Start 100–200 examples; skip if baseline reward > 95% | Small open-weight target; creative quality vs Claude unknown |
| OpenAI SFT / DPO / RFT | gpt-4.1 $25, mini $5, nano $1.50 per 1M training; RFT o4-mini $100/h | Fine-tuned inference gpt-4.1 $3/$12, mini $0.80/$3.20 | — | Closed to never-fine-tuned orgs since 7 May 2026; all training ends 6 Jan 2027; AA eligibility unknown |

- No hard crossover found; guidance gives starting sizes only (50–200).
- AA volume today: ~1.4k `generated_content`, ~48 tenant tour versions, ~251 content pieces, ~1.3k audit rows (only
  part are sentence edits). Too little for clean per-tenant fine-tuning.
- Rough arithmetic: SFT gpt-4.1-mini on 500 tours × ~3k tokens × 3 epochs ≈ 4.5M tokens ≈ $22. Training cost is not the
  blocker; platform access and fidelity risk are.

## 4. Risks and mitigations

- **Reward hacking** (Writing-Zero arXiv 2506.00103; arXiv 2606.04923; Adversarial Reward Auditing arXiv 2602.01750):
  combine judge with deterministic gates and Jev; audit samples by hand.
- **Fact-fidelity regressions** (Gekhman et al. EMNLP 2024): run the B-class promise check before any edit becomes an
  exemplar/rule/training row; strip facts from exemplars; "no new Jev reject" as a hard gate.
- **Overfitting to one reviewer** + criteria drift: ≥ 2 independent edits, > 1 reviewer for platform scope; provenance;
  expire unused rules.
- **Drift / context collapse:** cap active rules per stage; delta curation; re-run frozen eval on model change.
- **Tenant data leakage** (OWASP LLM08:2025): tenant memory behind `tenant_id` + RLS; platform rules abstracted, no
  tenant text, reviewed. `pipeline_lessons.example_before/after` must never hold tenant text.
- **Self-preference in judging:** cross-vendor judge or Jev.
- **Vendor platform churn:** keep data, evals and memory in AA's own Postgres.

## 5. Unknowns
- Live row counts of `pipeline_lessons` and `prompt_eval_runs`.
- Share of `audit_log` rows that are sentence edits.
- Nova fine-tuning and RFT prices.
- AA OpenAI org eligibility for fine-tuning.
- Whether acc3 credits cover Bedrock customisation in us-east-1/us-west-2.
- Whether the Anthropic Console prompt improver still exists.
- Nova 2 Lite / Qwen3-32B tour and social copy quality vs the current Claude writer.

## Sources (accessed 20/10/2026)

Bedrock: https://docs.aws.amazon.com/bedrock/latest/userguide/reinforcement-fine-tuning.html ·
https://docs.aws.amazon.com/bedrock/latest/userguide/custom-model-fine-tuning.html ·
https://docs.aws.amazon.com/bedrock/latest/userguide/model-lifecycle.html · https://aws.amazon.com/bedrock/pricing/ ·
https://aws.amazon.com/blogs/machine-learning/fine-tune-anthropics-claude-3-haiku-in-amazon-bedrock-to-boost-model-accuracy-and-quality/ ·
https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-bedrock-reinforcement-fine-tuning-openai/

OpenAI: https://developers.openai.com/api/docs/pricing · https://developers.openai.com/api/docs/deprecations ·
https://developers.openai.com/api/docs/guides/prompt-optimizer

Anthropic: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices ·
https://docs.anthropic.com/en/docs/test-and-evaluate/eval-tool

Prompt optimisation: https://arxiv.org/html/2507.19457v1 · https://iclr.cc/virtual/2026/oral/10009494 ·
https://dspy.ai/current/api/optimizers/MIPROv2/ · https://dspy.ai/current/api/optimizers/GEPA/overview/ ·
https://arxiv.org/abs/2309.03409 · https://www.arxiv.org/pdf/2406.07496 · https://arxiv.org/pdf/2412.07820 ·
https://arxiv.org/pdf/2604.08801

Memory and edit learning: https://arxiv.org/html/2510.04618v2 · https://arxiv.org/html/2504.07952v1 ·
https://www.microsoft.com/en-us/research/publication/aligning-llm-agents-by-learning-latent-preference-from-user-edits/ ·
https://arxiv.org/pdf/2410.06273 · https://arxiv.org/abs/2409.14509 · https://arxiv.org/pdf/2310.05857 ·
https://arxiv.org/pdf/2410.02320 · https://docs.openpipe.ai/features/dpo/overview

Retrieval / ICL: https://arxiv.org/pdf/2101.06804 · https://arxiv.org/abs/2405.00200v2

Judges: https://arxiv.org/html/2306.05685v4 · https://arxiv.org/abs/2404.13076v1 · https://arxiv.org/pdf/2404.12272 ·
https://www.zeroentropy.dev/concepts/llm-as-judge/

Risks: https://arxiv.org/pdf/2506.00103 · https://www.emergentmind.com/papers/2602.01750 ·
https://aclanthology.org/2024.emnlp-main.444 · https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/
