---
id: OPS-08-s261-llm-gateway-design-gap
title: "LLM gateway: approved design vs code vs S261 needs, gaps mapped to issues, design critique (S261)"
description: "Đối chiếu thiết kế LLM gateway đã duyệt (blueprint S258, ADR CIS 0005/0006/0008/0012, lát S0–S12) với code và các phát hiện S261; khoảng hở theo loại, trùng issue nào, việc mới, điểm yếu thiết kế cần ADR, quyết định cho tech lead."
type: report
status: active
owner: nghiep
audience: [engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-1002, AA-642, AA-804, AA-900, AA-842, AA-1004, AA-820]
---

# LLM gateway: thiết kế đã duyệt so với code và nhu cầu S261 (31/10/2026)

Tác nhân: Claude Code (workflow 9 agent, chỉ đọc; CIS `1b6e9448`). Tech lead yêu cầu: so với thiết kế, xem trùng issue
nào, việc nào mới; phân tích kỹ trước khi thiết kế hay điều chỉnh gateway. Tour viết bằng tiếng Anh: tiếng Việt không
phải tiêu chí. **Lưu ý đánh số ADR:** "ADR 0009" ở đây là ADR **hệ sinh thái** (root, AA-804) chưa viết; CIS cũng có
ADR 0009 khác (F17). Các ADR 0005/0006/0008/0012 nhắc tới là của **CIS** trừ khi ghi "root".

## Tổng hợp

**LLM gateway: the approved design compared with the code and the S261 findings (read-only, CIS code at `1b6e9448`)**

## 1. Verdict

The approved design (blueprint `docs/audits/2026-10-29-S258-aws-org-blueprint/README.md:1165-1439`, built as AA-1002 S1–S6, S9 and S10) has the right basic shape:
- three data layers: connection, deployment and logical model (:1178-1181);
- explicit fallback in a fixed order, with no hidden server-side fallback (:1285);
- data scopes as their own policy (CIS ADR 0012);
- the ledger as the source of truth, and an unknown price never recorded as $0 (ADR 0005 §7).

It falls short in five places:
- **The model's maker is not separate from the host and the path.** One `vendor` field means all three. The catalog CHECK is a closed list (`169_llm_model_catalog.sql:25`) and the planned `family` column was never added (AA-1002.md:43-46).
- **Model abilities and request parameters are not stored as data.** `capabilities` is read nowhere. Effort is keyed by deployment, and Converse ignores it (`client.py:1400-1403, 1256-1258`).
- **Several call paths run side by side, and nothing retires the old ones.** `_legacy_chain`, the vendor path and the native/satellite Converse paths each need every control added again (`client.py:1090-1113`). A per-call `model_tier` skips the stage route and its writer/judge rule (`client.py:595-597`).
- **Reliability is designed for throttling, not for losing a whole account.**
- **There is no procedure to qualify a new model family.**

The 29/10 outage showed the reliability gap clearly. Error 002 blocked every model and every region on acc3, the only chat account (postmortem `docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md:18-20,48-56`). Nothing in the design required a funded, warm second path:
- `anthropic-direct` was disabled and had no key.
- Every non-judge stage was `aws_only` (mig 311).
- The 18 CIS and 2 TripPlanner legacy-key stages could not reach the Anthropic API (AA-1002 comment 31/10 07:24).

So only about 2 stages could fail over. Loss of access is detected only through real traffic (`breaker.py:24-27`). A paid eval run found the outage, and refused calls leave no ledger row (postmortem §5).

The earlier S261 research (writer candidates, readiness) was new research and was not checked against this design. Three of its points need correcting:
- **Vietnamese is not a criterion.** No stage spec makes an LLM write Vietnamese; it appears only as UI labels (`apps/AA-CIS-App/CONTEXT.md:171`). The golden set is en-US (`scripts/aa729/select_samples.py:178`). All Vietnamese gates and remarks should be dropped.
- **The time-of-day validator is a pipeline gap, not a gateway gap, and it also affects Sonnet.** The T-series already has F17 (`trip_facts.py:331-344`). A1 matches only am/pm clock times (`brand_audit_node.py:69`), so "16:00" is never caught. `s1_checks.py` has the right place for a new rule but is "measurements, not gates" (`s1_checks.py:22`).
- **A non-Anthropic writer is against the approved policy** (blueprint :1277-1279; CIS ADR 0006 §5, ADR 0008). An A/B can run only as an evaluation. Promoting such a writer needs an ADR.

## 2. Gap table (merged)

Types: **a** = designed but not built; **b** = built differently from the design; **c** = the design does not cover it.

| # | Gap | Type | Severity | Covered by | Note |
|---|---|---|---|---|---|
| 1 | acc2 native chat rows are logged with `account=NULL`, so connection budgets and the reconcile cannot see acc2 spend | b (bug) | High | NEW slice (AA-1002 is closed) | `client.py:1376-1380`; `call_log.py:261-265`; `cost_guard.py:327-333`. Must merge before any paid acc2 call |
| 2 | Anthropic 429 `enforced_spend_limit_reached` is classed `throttled`, so a path that is out of money keeps retrying | b | High | S12 → NEW | `anthropic_messages.py:303` checks 429 before billing. The 400 form is handled (`errors.py:53-58`) |
| 3 | No funded, warm second path in a different payer/org; no `failure_domain` field | c | High | NEW + ADR 0009 | W1/W5. `anthropic-direct` has no key; T-series and `tp_*` stay `aws_only` until AA-820 |
| 4 | No deadline for a whole route; Bedrock clients use hidden SDK retries; connection `timeout_s`/`max_retries` are not read on Bedrock | a | High | NEW (reliability) | `client.py:745-791, 550-553, 1262`; `bedrock_satellite.py:187-194`. Design: blueprint :1222, :1285 |
| 5 | Loss of access is found only by real traffic; no scheduled canary per connection × model; no per-model access state | c | High | NEW (canary) | GLM-5.3 and Grok refused on acc2 (candidates :96). The B3 canary is only a proposal. **Correction:** "not available for this account" already maps to ACCESS_DENIED (`errors.py:48`). The gap-table row 15 "classification fix" is wrong |
| 6 | Model lifecycle / end-of-life not modelled; Legacy models lose access after 15 days unused | c | Med | NEW (canary) | 4 candidates reach end of life 2027-03-30 (candidates :126) |
| 7 | `model_tier` skips the route, the writer/judge rule and shadow; hard-coded `"haiku"` call sites | b | High | NEW (dispatch) + AA-642 S11 | `client.py:595-597`; `segment_research.py:483`, `regression.py:170`, `s1_batch.py:210` |
| 8 | Five or more dispatch paths; the legacy chain has no breaker | b | High | NEW (dispatch); S12 | `client.py:833-930` has no breaker hits; `:1090-1113` |
| 9 | Legacy `haiku`/`sonnet` aliases off; the logical rows are only a contract draft | a | Med | AA-642 S3-rest/S11 | AA-1002.md:356-370 |
| 10 | Maker, host and path mixed in `vendor`; closed vendor CHECK; no `family` column | b+c | Med-High | ADR 0009 + NEW (family) | Blocks GLM, DeepSeek, Qwen, Kimi and Nova rows |
| 11 | `api_style` sits on the logical model, not the deployment | b | Med | NEW (family) | `client.py:1106-1113`. Kimi K3 needs Invoke or Chat Completions for `reasoning_effort` (candidates :170) |
| 12 | `capabilities` is never read; behaviour depends on marker lists and an `"anthropic."` substring check | a | Med | NEW (family) | `client.py:351-361, 423` |
| 13 | Request parameters (effort, `max_tokens` floor, temperature, reasoning) are not data keyed by stage × model | a+c | Med | NEW (family) | `role_config.py:55-68`; `models.py:16-17`; `graph.py:47, 512-518`; capacity plan S12 "`max_tokens` from p99" |
| 14 | Reasoning tokens are not split out or logged; truncated output is accepted as success | c | Med | NEW (family) + AA-804 | `client.py:290-293, 1341-1345`; `stop_reason` logged but never acted on |
| 15 | Writer/judge rule checks vendor identity, against one side only, and only in the admin; `judge_compare` hard-codes acc3 | b | Med | ADR 0009 + AA-900 | `admin_llm_ops.py:180-183`; `judge_compare.py:51, 64-70` |
| 16 | Chat models on acc2 contradict ADR 0001a and 0018, but the task-role code path already exists | b | Med | ADR 0009 / ADR 0001a amendment (AA-804, AA-1004) | `client.py:1201-1205`; `account_route` CHECK is acc3 only |
| 17 | Region exists only for capacity, not for model availability; SCP region allow-list lacks us-west-2 | c | Med | AA-1004 (SCP) + NEW (family, rows) | The mechanism needs no code (`bedrock_satellite.py:200-212`) |
| 18 | "Plug and play" is really migration plus DB Migrate (contradicts checklist A3 and "≤30 min") | b | Low-Med | Blueprint fix inside ADR 0009 | AA-1002.md:423-428, 268-270 |
| 19 | S12 capacity controls (bulk/prod lines, backpressure in job claim, token-based limiter, "bulk paused") | a | Med-High | S12 is a comment on the closed AA-1002 → NEW | `queue.py:95-108`; `breaker.py:29-33` |
| 20 | An account-wide block opens circuits one deployment at a time; no connection-level circuit | c | Med | NEW (reliability) | `breaker.py:3-4, 101` |
| 21 | No recovery step: no re-queue of `llm_access_denied` jobs; job backoff has no jitter | c | Med | NEW (reliability) | `worker.py:112-117`; `queue.py:53-55` |
| 22 | No budget set on any connection; daily caps opt-in; eval/adhoc stages have no scope and fixed constant caps | a+c | Med | AA-642 proof + AA-900 + admin step ≤05/11 | `data_scope.py:16`; harness constants ($5, $15, $10/$25) |
| 23 | Data scope ignores the model maker, `global.` geography and licence | c | Med (tenant stages) | ADR 0012 amendment in ADR 0009; AA-820; AA-804 register | `docs/legal/register.md:252-253`; `dpa-template.md:85` |
| 24 | Price record is free text, with no region, profile or effective date; `cis_app` can edit prices | c | Low-Med | NEW (family, catalog rows) | Kimi `us.` $3.30 vs `global.` $3.00 |
| 25 | Reconcile cannot separate connections on one account | c | Low-Med | AA-642 S10 follow-up | Group by `USAGE_TYPE` |
| 26 | Ledger has no `latency_ms`, `error_class`, `connection_key`/`deployment_id`, `reasoning_tokens`; refused attempts leave no row | a+c | Med | AA-804 (add to its list) | Readiness obs §1.1 |
| 27 | No qualification and promotion ladder for a new model family | c | High | ADR 0009 + AA-900 | — |
| 28 | The design's eval gate cannot pass: judge kappa 0.562 on 13 pairs; thresholds `calibrated:false`; labels made by an LLM panel | a | High | AA-900 (AA-919 is Done) | `r2.py` step 0a; arch review B2 |
| 29 | R2 has no arm for a candidate model; no harness for the 13 light stages that S11 moves | c | High | AA-900 | `eval_writers.py:133, 209` |
| 30 | A1/S1 has no deterministic rules for time of day, "around → by" hardening, a 24-hour clock, or unsourced nouns | c (pipeline) | Med | NEW (A1 fidelity) | Affects every model, Sonnet included |
| 31 | No cross-path canary before enabling a writer path (S261 anthropic-direct `s1_generate`) | c | Med | NEW (canary) | Arch review B3a |
| 32 | No automated PII guard in the CIS gateway before S8 | c | Low now | AA-642 S8 / ADR 0009 | Reuse the CRM F3 scrub |
| 33 | TripPlanner/CRM shared core (S8), batch (S7), live S9/S10 proof | a | — | AA-642 (as is) | — |
| 34 | Caching only for `anthropic.` models; shadow when the primary is down | — | none | — | Correct as is. Never use shadow as a fallback |

## 3. Weaknesses that need a design change (not only finishing slices)

| # | Weakness | Proposed change | ADR? |
|---|---|---|---|
| D1 | Maker, host and path mixed (gaps 10, 15) | Add catalog `family` → `llm_model_family`; drop the closed vendor CHECK; derive the host from the connection kind. Writer/judge rule becomes: the judge's family differs from both A/B arms, checked at call time, in R2 and in the harness | **Yes** (0009, amends 0006 §5 / 0008) |
| D2 | Wire format on the wrong layer (gap 11) | Move `api_style` to the deployment; turn path-named keys (`gpt-6-luna-openai`, `cohere-embed-v4-acc3`) into deployments | Yes (0009, short) |
| D3 | No single home for abilities or parameters (gaps 12–14) | Effective capabilities = catalog values + per-deployment override (reasoning mode and control, `min_output_tokens`, structured output, cache). A `stage_model_params` table with a fixed precedence: call-site hard limits → stage × model → protocol defaults. Every adapter, Converse included, translates them | Yes (0009) |
| D4 | Several dispatch paths and an open `model_tier` bypass (gaps 7, 8) | One pipeline: route → deployment plan → shared middleware (scope, budget, limiter, breaker, attribution, ledger, response contract) → adapter. `model_tier` only in eval/probe context or for keys in the route. Delete `_legacy_chain`, the vendor path and the direct OpenAI path after S3; give each flag a removal date | Yes (0009 principle); build in AA-642 |
| D5 | Designed for throttling, not account loss (gaps 3–6, 20, 21) | Add a `failure_domain` field. Invariant: each prod stage class has ≥1 enabled, funded deployment in another payer/org domain that its scopes allow, or an approved degrade mode, checked in CI and on the availability card. Plus a route deadline, gateway-owned retries (≤6 per chain), a canary per connection × deployment, a connection-level circuit, a re-queue action and a monthly failover drill | **Yes** (0009) |
| D6 | Response contract undefined (gap 14) | `stop_reason=max_tokens` → a `truncated` class; detect leaked reasoning text; log schema validity and `reasoning_tokens` | Yes (0009, short) |
| D7 | No qualification ladder (gaps 27–29) | Catalog row disabled and priced → access probe → contract smoke (<$0.10) → judge calibration first → R2 A/B against a frozen Sonnet 5.5 control → targeted shadow → route switch with one-edit rollback. Bars: zero new hard-fact class; deterministic fidelity ≤ control; $/tour and p95 latency reported | **Yes** (0009) |
| D8 | Data policy blind to the model maker and geography (gap 23) | Deployments carry `model_maker` and `inference_geo`; stages get `allowed_makers` / `allowed_geo` from their data class. Tenant and TripPlanner stages only use makers named in the register and DPA | **Yes** (ADR 0012 amendment) |
| D9 | Unclear who may change connections (gap 18) | Accept change by migration on purpose: the admin only toggles, sets priority, limits and budget. Rewrite A3 and "≤30 min" as "1 PR + DB Migrate" | Yes (blueprint fix in 0009) |
| D10 | `account_route` duplicates the role-per-account policy (gap 16) | Drop `account_route`. Add a connection column listing the roles it may serve (e.g. acc2 = embed + eval only), checked against the stage role | **Yes** (0001a amendment) |
| D11 | Eval spend is the least governed (gap 22) | Default `adhoc_*`/`eval_*` scopes to `{aws_only}`; `spend_budget` scopes `eval:*` replace the harness constants; an `eval_run` record (approver, cap, estimate) is written before the first paid call | No (AA-900 runbook) |

## 4. Proposed work list

Few issues, each about one deliverable (Linear Free plan). No new issue is created without the tech lead's OK (`aa-linear-issue`).

**Update existing issues:**
1. **AA-804** (pull forward from Backlog/"later" to due 15/11; it owns ADR 0009, and AA-642 only refers to it):
   - ADR 0009 covers D1–D3, D5–D10 and the decisions in §5.
   - Ledger v2 also gets `latency_ms`, `error_class`, `connection_key`, `deployment_id`, `reasoning_tokens` and `effort`, plus a row for each refused attempt.
   - The AI Use Register lists model makers.
2. **AA-642** (Todo). Keep S7, S8, S11, S1-infra and the live S9/S10 proof. Add:
   - S3-rest: logical rows and aliases on;
   - D4 dispatch unification, with removal dates for the legacy paths;
   - reconcile grouped by usage type (gap 25);
   - PII step before S8 (gap 32).
3. **AA-900** (Todo):
   - the qualification ladder as a runbook (D7) and governed eval spend (D11);
   - an R2 candidate arm `--model key@connection`, with `goal=non_inferior`;
   - a harness for the light stages;
   - a 40-item human label set and judge calibration (≥30 pairs, ≥8 per class);
   - the family-based two-sided judge rule in `judge_compare` / R2, without the hard-coded acc3;
   - length and format metrics.
4. **AA-1004**: add us-west-2 to the SCP region allow-list before the org move, and an acceptance check for it.
5. **AA-820**: the terms name the allowed model makers and geography (D8).
6. **AA-896**: no change. The CloudWatch alarms stay there.

**NEW issues (drafts, to ask about):**

| Order | Draft title | Scope | Done when |
|---|---|---|---|
| N1 | Gateway reliability: attribution, spend-cap class, time budget, canary, capacity (S12) | Gap 1 attribution fix (first PR, $0). Gap 2: 429 spend-cap → `quota_exhausted`, with fixture tests on the real refusal strings (Error 002, "not available for this account", Legacy refusal, both spend-limit forms). Gap 4: route deadline, Bedrock clients built from the connection's `timeout_s`/`max_retries`, ≤6 attempts per chain. Gaps 5/6/20/31: daily canary on Dev, `access_state`/`last_probe_at`, `lifecycle_status`/`eol_date`, connection-level circuit, cross-path canary. Gap 21: re-queue action and jitter. Gap 19: all of S12 moved here from AA-1002 | acc2 row has `account='acc2'`; fixture tests green; a test proves the route deadline; the canary has run 7 days and updated health; a monthly failover drill on Dev with each stage class reaching its fallback within the deadline; S12 items live with evidence |
| N2 | Gateway model families: family, capabilities, params as data | After ADR 0009: `family` table and dropped vendor CHECK; `api_style` on the deployment; effective-capabilities reader replacing the marker lists; `stage_model_params` read by every adapter, Converse included; `truncated` class; structured price record; disabled, priced catalog and deployment rows for the candidates (acc2, plus an `acc2-usw2` connection) | No string markers left in `client.py`; Kimi K3 returns a reply with its reasoning setting applied, in a unit test plus a $0-gated live smoke after approval; candidate rows disabled with price provenance; schema reference PR merged |
| N3 | A1/S1 deterministic fidelity rules (pipeline, not gateway) | In `s1_checks`: TIME_NOT_IN_SOURCE (reusing F17 `_TIME_RE`), HEDGE_HARDENED, 24-hour times in `ITIN_CLOCK_TIME`, unsourced vessel/view nouns. Measurement only (keeps the S1 gate freeze), then promoted in the taxonomy | Rates measured on the Sonnet 5.5 baseline and reported; promotion to enforce proposed with the baseline numbers |

**Order of work:**
1. N1's attribution and spend-cap PRs: $0, no design change.
2. N3 measurement on the Sonnet baseline: $0.
3. ADR 0009 (AA-804) by 15/11.
4. N2 and AA-642 dispatch work.
5. AA-900 qualification.
6. Only then any paid writer or judge A/B.

**What changes in today's "step 1, four PRs" proposal:**
- PR-1 (attribution): keep it, in N1.
- PR-2 (reasoning config through `request_defaults.additional_model_request_fields`) and PR-3 (widen the vendor CHECK with amazon/meta/moonshot): hold until ADR 0009. Both would lock in the wrong axis (D1, D3).
- PR-4 (harness `model_tier` patch): replace it with the R2 candidate arm in AA-900.

## 5. Decisions for the tech lead (each with a proposed answer)

1. **Is a non-Anthropic writer ever in scope?**
   - Proposed: evaluation only for now; S1 stays on `sonnet-5-5` (`docs/backlog/README.md:80`).
   - A route change needs ADR 0009 to amend 0006 §5 / 0008, and only after N3 + AA-900 show non-inferiority.
   - AA-782's "relabel as validate" idea is rejected; ADR 0008 forbids it.
2. **May acc2 serve chat models?**
   - Proposed: yes for eval and judge/validate stages as a second failure domain (different payer from acc3).
   - Not for main writers or tenant stages until D8 and AA-820 are done.
   - This needs an ADR 0001a/0018 amendment in ADR 0009, and `account_route` is replaced by the per-connection roles column (D10).
3. **Funded warm independent path.**
   - Proposed: fund the `anthropic-direct` key with its 150 USD spend limit, keep it warm through the canary, and add the failure-domain invariant for prod.
4. **Who changes connections.**
   - Proposed: by migration (config as code); the blueprint text is corrected (D9).
5. **Where S12 and ADR 0009 live.**
   - Proposed: S12 → N1; ADR 0009 → AA-804, pulled forward; AA-642 links to it.
6. **S1 gate freeze.**
   - Proposed: new fidelity rules run as measurements now and are promoted after the baseline rate is known.
7. **Human labels.**
   - Proposed: 40 items, about 2 hours of tech-lead labelling, under AA-900. Judge calibration is a prerequisite of S11 and of any writer change.
8. **Second region.**
   - Proposed: allow us-west-2 for model availability, only on eval connections, plus the SCP allow-list in AA-1004.
   - Prod second region stays "only on trigger" (capacity plan §5.2).
9. **Tenant geography.**
   - Proposed: tenant and TripPlanner stages use only `us.` or in-region profiles, never `global.`, until the DPA covers it.

## 6. What to measure before changing the design (English content only)

Base it on the readiness test plan (`docs/audits/2026-10-31-S261-llm-gateway-readiness/README.md` §"Test-first plan", lines 72-190), with these changes:
1. **Sonnet 5.5 baseline, $0 to $low.** Run the N3 rules and the existing `s1_checks` on the frozen S1 control. This gives the bar any candidate must not exceed.
2. **Judge calibration.** Human set of 40 items; kappa per stratum for the current judge and for gpt-oss-120b / Luna. Budget $1–5, within `judge_compare`'s $5 cap.
3. **Cross-path canary for `s1_generate` on anthropic-direct.** About 5 items: verdict flips within the noise bound, same effort sent on both paths. This must pass before that Dev path carries real work.
4. **Contract smoke per candidate.** 3 calls each against the real S1 schema: schema validity, `stop_reason`, output size against each model's 8K cap (candidates :127), reasoning tokens, and `account='acc2'` in the ledger. Do this only after N1's attribution PR and N2's disabled rows, with the cost estimate approved first.
5. **Reliability.** Measure route p95 latency against the TP target (TTFT < 5 s, capacity plan §5.7) under the deadline. Then a Dev failover drill: disable the primary and record time to fallback and cost.
6. **Writer A/B.** Only after steps 1–4, through the R2 candidate arm, judged by a model of a third family: 3 tours, then at most 50. Report $/tour, p95 latency and new hard-fact classes.

Language quality of Vietnamese text is not measured, because no stage writes it.

Files read:
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/shared/llm_client/errors.py`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/shared/llm_client/adapters/anthropic_messages.py`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/shared/llm_client/client.py`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/services/quality/s1_checks.py`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/services/content_generation/brand_audit_node.py`
- `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-31-S261-llm-gateway-readiness/README.md`

## Kiểm độ đầy đủ (critic)

**Completeness critique of the gateway synthesis (spot-checked against CIS `1b6e9448` and the root docs)**

**1. Claims without a citation, or that contradict the inputs**
- **ADR numbering is ambiguous.** "ADR 0009" is meant to be the ecosystem AI-platform ADR owned by AA-804 (`docs/engineering-handbook.md:461`). That ADR has not been written. But CIS already has an `ADR 0009`: `apps/AA-CIS-App/docs/adr/0009-f17-owns-offered-moments-promises-gate-dropped.md`. The same problem hits "0006 §5", "0008" and "0012". In CIS these are stage routes, validate stages and data scopes. In the ecosystem they are identity, new-app rules and the environment model. Every ADR reference needs a "CIS" or "ecosystem" prefix.
- **Gap 2 (Anthropic 429 `enforced_spend_limit_reached`).** The code side checks out: `anthropic_messages.py:303` classes any 429 as throttled before it looks at billing. But nothing cites a captured response or Anthropic docs showing the spend-limit refusal really comes back as a 429. That needs a source, or the fixture tests must use a captured response.
- **Gap 33 and the "TripPlanner/CRM shared core (S8)" line contradict ecosystem ADR 0008a §5 (X3).** That ADR says the CRM has its own in-process gateway and its own ledger `crm.llm_call`, never writes `shared.llm_call_log`, and has no grant on `shared.*`. Any shared core has to respect this or amend 0008a.
- **"AA-919 is Done" has no citation.** `docs/backlog/README.md:35` still lists AA-919 as blocked on the LLM path.
- **"No stage makes an LLM write Vietnamese" rests on two citations only** (`apps/AA-CIS-App/CONTEXT.md:171` and the golden set). A grep of CIS `services/` supports it: the matches are only comments, NFD normalisation and name handling. TripPlanner and the CRM were not checked.
- **Gap 1 is confirmed.** `client.py:1376-1380` sets `satellite_account=None if native`.
- **Gap 30 is half right.** `brand_audit_node.py:69` matches only am/pm times. But the A1 claim check at `:111` already treats a clock time as supported only when the source has it. That is a partial existing control, and N3 should extend it, not duplicate it.

**2. Design documents and issues that were likely missed**
- **Ecosystem ADR 0008a §5 (the CRM's own gateway).** It is the reference for the PII filter and `ai_enabled` order, and it limits S8.
- **`docs/ecosystem-architecture.md:297`** (the "Model Gateway" principle) and the `shared` row at `:127`.
- **The anthropic-direct material behind decision 3:**
  - `docs/ops/runbooks/llm-anthropic-api-key.md`;
  - `docs/audits/2026-10-29-S257-llm-access-options/anthropic-api-evaluation.md`.
- **`docs/legal/tenant-terms-ai-clause-draft.md`**, needed for D8 and AA-820.
- **AA-842 (OTel spike, on hold for cost)** overlaps gap 26 (latency and error class). Say that the ledger columns cost nothing and are not the paid OTel work.
- **AA-1000, AA-790, AA-788 and AA-741** sit in the L1 LLM/quality lane (`docs/backlog/README.md:35`, `:121`). The synthesis never checks them for overlap.
- **AA-803 (the A1 claim check, Done S247) and F17** (CIS ADR 0009) should be named as the base N3 builds on.
- **The linear-export records for AA-757, AA-843 and AA-685** mention the gateway and were not read.

**3. Recommendations that jump to building before analysis or testing**
- **N1 bundles about eight separate builds:**
  - the attribution fix and the spend-cap class;
  - the route deadline;
  - the canary;
  - the connection circuit;
  - re-queue;
  - lifecycle state;
  - all of S12.

  They are also set to start before ADR 0009 decides D5. Split N1. Only the attribution fix, the spend-cap class (once its premise is verified) and the fixture tests belong in the "$0 now" slice. The rest should wait for the ADR. This also matches the Linear Free-plan rule of one deliverable per issue.
- **The daily canary in N1 makes paid calls.** acc3 is now billed to us, and anthropic-direct would be funded. The canary needs its own cost line and an explicit yes before it is built, under the cost-before-new-AWS-services rule.
- **D4 (one dispatch pipeline) and D10 (drop `account_route`) are big redesigns with no measurement behind them.** Count first how often the `model_tier` bypass, `_legacy_chain` and the vendor paths are actually used. A `GROUP BY provider, stage` on `llm_call_log` costs nothing.
- **The §6 failover drill and the latency step depend on N1 already being built.** Present them as checks after the build, not as analysis before the design.
- **N2 adds "disabled, priced candidate rows" before AA-900 shows any candidate is worth it.** Keep the rows inside the qualification ladder (D7), not in the design work.

**4. Leftover Vietnamese-as-writer criteria**
- **None left as a writer criterion.** §1 drops it and §6 says it is not measured.
- **One caveat.** Dropping "Vietnamese diacritics" must not also drop diacritic fidelity of place names inside English text, such as "Hạ Long". CIS `validate.py:155` and `place_cards.py:202` already handle this. Record it as a name-fidelity rule (NAME_NOT_IN_SOURCE), not a language rule, so it is not lost along with the Vietnamese remarks.

## Thiết kế đã duyệt (dựng lại)

**Approved LLM gateway design: reconstruction (S261, read-only)**

No stage spec makes any LLM output Vietnamese. Vietnamese exists only as UI labels (`apps/AA-CIS-App/CONTEXT.md:171`, `services/quality/gen_frontend.py:7`). All tour writing (S1 / A-series / T-series) is English.

## 0. Sources and approval status

**Primary design.** Root `docs/audits/2026-10-29-S258-aws-org-blueprint/README.md:1165-1439`. It has the "AI / LLM Gateway" section, tables 1–11, the slice table at :1365-1381, and 22 reviewer corrections at :1416-1439. The same content is in `blueprint.json` under `ai_gateway.{section,build_slices}`.
- It counts as approved. `apps/AA-CIS-App/docs/implementation-notes/AA-1002.md:3` calls it "(approved)".
- The S258 session log line 9 records "planned approvals count as given" (`docs/sessions/2026-10-30-S258-…md:9`).

**Implementation record.** `apps/AA-CIS-App/docs/implementation-notes/AA-1002.md` covers S1–S6, S9 and S10 (842 lines).

**Later approvals:**
- The capacity plan `docs/audits/2026-10-31-S261-llm-capacity-plan/README.md` was approved by the tech lead on 31/10. It adds slice S12 (Linear AA-1002 comment 31/10 04:29; AA-642 comment 31/10 04:29).
- In Linear, AA-1002 is Done-with-scope (comment 31/10 01:22). AA-642 is Todo and holds S7, S8, S11, S1-infra and the live S9/S10 proof.

**Lineage:**
- Root ADR 0001 decision 2 "Single Model Gateway" (`docs/adr/0001-ecosystem-target-architecture.md:35-44`).
- ADR 0001a (`docs/adr/0001a-…md:31-37`).
- CIS ADRs 0005, 0006, 0008 and 0012 (`apps/AA-CIS-App/docs/adr/`).
- S235 Bedrock-first rule (`apps/AA-CIS-App/docs/implementation-notes/S235-bedrock-only.md:7-10`).
- The original AA-642 gateway spec from S198 (Linear AA-642 description, "Original description").

**Root ADR 0009 "AI platform and governance" does not exist yet.** It is reserved for AA-804 (`docs/adr/README.md:46`) and due as Proposed by 15/11 (AA-642 comment 31/10).

## 1. Design goals and principles

1. **Plug and play, multi-source and multi-vendor.** Each way in is a row in `shared.llm_provider_connection`.
   - Connection kinds: `bedrock` (assume_role / task_role / bedrock_api_key), `anthropic` (direct; also Platform-on-AWS / Foundry / Vertex through a client factory), `openai` (direct or compatible), `azure_openai`, `mock`, plus `typesafe` for Jev (blueprint :1183, :1243-1256).
   - Stated target: "add secret → add connection row → Test → enable, ≤30 min, no deploy, CIS only until S8". Code is needed only for a new API format, or for a model ability that has no flag in `capabilities` (:1183, checklist :1309-1326, row C :1323).
2. **Three data layers** (:1178-1181, :1232-1241):
   - connection: account / region / role / endpoint, secret name, timeouts, limits, `data_scope`, budget;
   - deployment: model × connection, with `wire_id`, `priority`, price overrides, `batch_capable`, `request_defaults`;
   - logical model: the catalog row plus `capabilities jsonb` (forced_tool, structured_output, thinking_mode, default_effort, prefill; :1218, :1430).
3. **Routing is data.** A stage route is primary, ordered fallbacks and a shadow (ADR 0006 §1-3).
   - The general rule (:1285) is applied in order: (1) same model on the next path by priority; (2) skip deployments whose circuit is open; (3) next model in the route; (4) all paths exhausted → `LLMAccessDenied` or a plain error.
   - There is a time cap for the whole route. There is no hidden SDK retry on 429, and no implicit fallback, including the Claude API's server-side `fallbacks`.
   - Every fallback leaves `fallback_used`, `llm_route_used` and `account=connection_key` in the log.
   - No silent cross-vendor fallback (ADR 0005 §4).
4. **Data scopes.** Each connection is `aws_only` or `vendor_direct`, and each stage has `allowed_scopes`. A scope change happens only by migration (CIS ADR 0012 §1-6; blueprint table 7 :1298-1307). Aggregators such as OpenRouter are for emergencies only, `vendor_direct`, and never carry tenant data (:1307).
5. **Budgets.** Every external spend checks a DB budget per run and per day (ADR 0001 decision 4). The design adds a budget per connection and a nightly reconciliation against the provider bill (:1226, :1352, slice S10).
6. **Breaker and limiter.** One circuit per deployment, with shared state in `llm_provider_health`. The limiter is per process, using `max_concurrency` / `rpm_limit`. The admin "Test connection" is the probe (:1221-1224, S4).
7. **Shadow / A-B.** `shadow_model_id` + `shadow_sample_pct` (ADR 0006 §3), set to 0% outside an A/B round (:1350).
8. **Cost parity.** `llm_call_log` is the ledger. `quote(model, usage, deployment)` covers 5-minute / 1-hour cache, batch, the Haiku 5.5 tier above 100K tokens, `inference_geo`, and per-deployment overrides. An unknown model is flagged as an estimate and is never priced at 0 (:1225, :1351, S6).
9. **One gateway for all apps.**
   - Option (a), a vendored library `aa_llm` with the CIS control plane, is chosen now. Option (b), an HTTP gateway service, comes only when ≥3 apps really call it or central keys are needed. Option (c), LiteLLM, is rejected (:1328-1336).
   - TripPlanner and CRM get "plug in without deploy" only after S8.
   - CRM stays Bedrock-only behind its scrub → budget → `ai_enabled` order (ADR 0008a; :1284).
10. **Evaluation before change.** Route switches between model generations are eval-gated (S11, :1381; S3 risk :1373). Writer-voice consistency requires the same model and the same effort on every path (:1277).
11. **Observability.** The DB ledger is the source of truth for cost and audit. Traces (AA-842, option B: one gen_ai span at the gateway; backend X-Ray proposed) are for latency, fallback and debugging, and are not built. Langfuse Cloud conflicts with keeping data in AWS (`docs/audits/2026-10-29-S257-aa842-otel/README.md:60-104,472-498`).

## 2. Slices S0–S12 (plan vs status)

| Slice | Promised (blueprint :1369-1381) | Status (evidence) |
|---|---|---|
| S0 | Merge AA-900 error classes, `LLMAccessDenied`, availability card | Done (CIS #1148, per AA-1002 description) |
| S1 | Connection registry + deployment table + backfill; CHECKs widened; new paths off; no behaviour change | Done, mig 304 (AA-1002.md:1-87). `capabilities` added empty; `family` column not added (:43-46) |
| S1-infra | `AA-LLM-Invoker` assume-role per org; `llm-invoker` module (Bedrock IAM wildcard) | Not done; moved to AA-642 (comment 31/10 01:22) |
| S2 | Anthropic Messages adapter (stream, output_config, explicit effort, no temperature, refusal billed, no server-side fallbacks) | Done, mig 306 + adapter (AA-1002.md:91-238). Connection disabled, no key. Dev path prepared S261 (Infra #549/#550): `s1_generate` and `supply_content_writer` scopes widened to vendor_direct, `anthropic-direct` budget 150 USD (AA-1002 comment 31/10 07:24) |
| S3 | Route spread over deployments; legacy `haiku`/`sonnet` become aliases of new logical rows `sonnet-4-6`/`haiku-4-5`; accounts as data; embed through registry | Partly done. Mig 307; `LLM_DEPLOYMENT_ROUTING` on; `LLM_LEGACY_ALIASES` off and never run live; logical rows and the `account_route` FK left as a contract draft (AA-1002.md:240-373). So 18 CIS + 2 TripPlanner legacy stages cannot use anthropic-direct (AA-1002 comment 31/10 07:24) |
| S4 | Breaker + limiter + health table + Connections tab | Done, mig 309/310 (AA-1002.md:375-500) |
| S5 | Policy as data (`allowed_scopes`), root ADR 0009 | Done, mig 311. The ADR became CIS ADR 0012, not root 0009 (AA-1002.md:503-572) |
| S6 | Cost parity + prompt caching | Code done, mig 312. Live 3-tour cache / cost check against the console still open (AA-1002.md:574-618) |
| S7 | Batch interface + Anthropic Message Batches | Deferred until trigger T-BATCH (AA-642 comment 31/10; arch review B10) |
| S8 | Core `aa_llm` vendored into TripPlanner and CRM | Planned: ADR 0009 ≤15/11; S8 ≤13/12 or go-live −6 weeks (AA-642 comment) |
| S9 | Azure / OpenAI-compatible; OpenAI key as runtime secret | Code done, no migration (AA-1002.md:794-842). Key move is an admin step; live proof open |
| S10 | Budget per connection + nightly reconcile | Code done, mig 317 (AA-1002.md:688-792). No budget set on any connection; live proof open (AA-642) |
| S11 | Move legacy-key stages to 5.5 models, eval R2 gate, effort in `request_defaults` | Planned (blueprint :1381; AA-642) |
| S12 (new, S261) | Capacity controls: reserved-TPM ceiling per line; dev / prod / bulk connection lines; legacy and vendor paths into the breaker; Anthropic spend-cap 429/400 = path out of money; per-app "LLM off" and "bulk paused" switches; waves stop when a prod circuit opens; instant circuit-open alert; `max_tokens` from p99 | Planned. Connection numbers ≤05/11 (admin); instant alert ≤15/11; code ≤30/11 (AA-1002 comment 31/10 04:29; capacity plan §7.1) |

Migration numbers differ from the plan (plan 304–308, actual 304/306/307/309/310/311/312/317).

## 3. Non-goals and decisions

**Writer vendor is Anthropic only.** The rule built up in steps:
- ADR-2026-014 (Notion, S65, AA-206) split writing and judging across two models, Bedrock Claude writes and GPT-4.1 judges, to stop self-scoring (`docs/linear-export/no-project/AA-206.md:23-46`).
- CIS ADR 0006 §5 enforces writer/judge vendor isolation in the admin: "writers are Anthropic, judges are not".
- ADR 0008 narrows the rule to writer and judge stages; validate stages may use any vendor; a stage must not be labelled validate to avoid the rule.
- S235 decided writers get no OpenAI fallback, because it would be an unnoticed vendor change (`S235-bedrock-only.md`, legacy T3 bullet).
- Blueprint table 5 says a main writer "never" uses a non-Anthropic vendor, so the writing voice stays the same: same model and same effort on every path (:1277-1278). Judges are never Anthropic (:1279).
- Code enforcement: `api/routers/admin_llm_ops.py:180-183`.
- The S1 writer is `sonnet-5-5`, permanent since S250 (`docs/backlog/README.md:80`).
- **A non-Anthropic writer needs an ADR amending 0006 §5 / 0008.**

**`account_route` is acc3-only.**
- ADR 0001a d1-d2: acc3 is the only satellite for Bedrock chat models; there is no cross-account fallback. Migration 295 put a CHECK on `account_route` = 'acc3' or NULL.
- The design replaces the CHECK with an FK to connections (blueprint :1239). That is still a contract draft (AA-1002.md:356-370).
- ADR 0018 keeps `aa-ai` (acc3) as "Bedrock chat models only", with an invoker role per environment (`docs/adr/0018-…md:49,71-72`).
- Running chat models on acc2: S1 refused Converse on acc2 (AA-1002.md:34-36). S3 made task-role Converse possible in code (:293-294), but that **contradicts ADR 0001a/0018 unless they are amended**.
- Bedrock running locally in `aa-prod` also needs ADR 0001a amended (`docs/audits/2026-10-31-S261-aws-bedrock-org-access/current-situation-model.md:59`).

**Legacy keys.**
- `haiku`/`sonnet` (about 18 stages) are planned to become aliases of logical Converse rows `sonnet-4-6`/`haiku-4-5`, which reach acc3 and the Anthropic API. Same model, so no quality eval is needed, but the S251 structured-output path changes (blueprint :1215, :1420).
- Then S11 moves those stages to the 5.5 models with an eval gate (:1342, :1381).
- `_legacy_chain` stays as the rollback path (AA-1002.md:312).
- `gpt-6-luna-openai` gets no alias; it is left to the scopes rule (:279-281).

**Region model.**
- Region is a column of the connection, so one connection = one account × one region (mig 304: `region` with CHECK, 304:160,189). The STS session cache is keyed by (connection, role, ExternalId, region) (AA-1002.md:283-287).
- The inference-profile type (`global.` / `us.` / regional; regional costs +10%) is the deployment's `wire_id` (blueprint :1247).
- The invoker IAM must cover the regional, `*::foundation-model` and `:::foundation-model` ARNs (:1425). SCPs must not block the cross-region inference destination regions (risk row :1104).
- A second source region (us-west-2 / us-east-1) is "only on trigger" (repeated 503/529, or a quota denied), and does not help when the whole account is blocked (capacity plan §5.2).
- A new connection row is a migration: cis_app cannot INSERT connections, and region is not admin-editable (AA-1002.md:423-428, :818-819). This contradicts blueprint checklist A3, "Admin › Connections › Add".

**Per-stage parameters.**
- The design puts effort in deployment `request_defaults` (`effort_by_stage[stage]`), so the same effort applies on every path (blueprint :1277, :1346; AA-1002.md:150-153).
- The S198 AA-642 spec wanted route params (effort, max_tokens, temperature); they were never built. `llm_role_config` has no parameters.
- Converse ignores `request_defaults`. Only the Anthropic adapter and Azure `api_version` read them (`client.py:1402,1510`; `adapters/openai_chat.py:57`).

**Other decisions:**
- Claude API server-side `fallbacks` stay off (:1364, :1431).
- The IAM invoker wildcard per model is proposed; governance goes through catalog + Budgets + SCP (:1326, :1363).
- S235 is revised for Claude `vendor_direct` writers. The S261 Dev road widened A-series writers; T-series writers and `tp_*` stay `aws_only` until the tenant terms (AA-820, due 11/11) and the DPA (:1358-1360; capacity plan T5, B3; ADR 0012 §5).
- Non-goals:
  - S1 changes no behaviour (AA-1002.md:52-61).
  - No model choice is changed by the gateway work (AA-642 "Out of scope").
  - Invocation logging and a Redis global limiter only on trigger (capacity plan §5.8).
  - No paid observability now (memory; AA-842 is Backlog).

## 4. New model families, regions, reasoning models, model qualification, access monitoring

**New model families.**
- The design assumes the vendors Anthropic, OpenAI, Cohere and Jev, and says its connection kinds "cover every known path" (:1183).
- The catalog `vendor` CHECK is still `('anthropic','openai','cohere','typesafe')` (`api/migrations/169_llm_model_catalog.sql:25`); 304 did not widen it.
- A new family on an existing kind is "data" (catalog + deployment rows). Under ADR 0017 those INSERTs are contract migrations applied by hand (AA-1002.md:268-270).
- No design text covers Bedrock third-party families (Nova, Llama, Kimi, GLM, DeepSeek, Qwen, Mistral) or using them as writers.

**Reasoning models.** The design covers:
- ADR 0006 §6: OpenAI reasoning models get `max_completion_tokens`; temperature and seed only when the catalog allows them.
- S2: effort always explicit and no `thinking` field sent (AA-1002.md:150-153, :171).
- `openai_responses` api_style reserved for Responses-only models (:1438).
- `capabilities` flags thinking_mode / default_effort (:1218).

`capabilities` is read nowhere: 0 matches in `shared/llm_client/*.py`; the facts stay as code constants (AA-1002.md:181). There is no design for a reasoning-token floor or for separating reasoning output on non-Anthropic/OpenAI families.

**Qualification and evaluation:**
- A model without a verified price is seeded disabled (ADR 0005 §7).
- "Same model on another path" needs a golden-label check, e.g. Luna on Bedrock vs the OpenAI API (:1268).
- S3 alias repoint is eval-gated (AA-1002.md:371-372). S11 runs eval R2 per stage group, ≤50 tours, logging run ID and $/tour (:1381).
- AA-900 (Todo) defines a manual eval runbook with a cost cap.
- AA-919 (Done) built the R2 runner with a $10-per-release cap and targeted shadow.
- The judge is not calibrated: kappa 0.562 on 13 pairs. This comes from the S261 architecture review B2, which is a proposal, not the approved design (`docs/audits/2026-10-31-S261-architecture-review/README.md:216-238`).
- There is no qualification procedure for a new family: no deterministic validator rules per family and no writer A/B protocol in the design.

**Access monitoring:**
- Trust only a real call, never `GetFoundationModelAvailability` (:1247, :1293, test plan :948).
- S4 "Test connection" is the operator's half-open probe, with availability per connection (AA-1002.md:430-439).
- OPS-12 digest flags "LLM route unknown" after 24 hours without an answered text call (`AA-1003.md:161-164`).
- The capacity plan adds an instant circuit-open alert (≤15/11), 3 CloudWatch Bedrock alarms, a daily Anthropic warm probe, and a probe of every connection on 01/12 (§4.2, §5.3, §7.2).
- Not in the approved design, only proposed by review B3 (:240-253): a scheduled daily `test_connection` per connection × model, `lifecycle_status`/`eol_date` columns, and the Bedrock "Legacy loses access after 15 days unused" watch.
- Access is granted per model and per account, and that grant is not modelled anywhere.

## Bảng khoảng hở chi tiết

# LLM gateway: approved design vs code today vs what the S261 research needs (read-only, 31/10/2026)

The earlier S261 research (writer candidates, readiness) was new research. It was not checked against the approved design. This table does that check. Code was read at CIS `1b6e9448`. I made no edits and no AWS, DB or LLM calls, and only read from Linear.

**Gap types:** (a) the design covers it but it is not built; (b) it was built differently from the design; (c) the design does not cover it, so it is new design work; (d) fine as is.

## Three corrections to what the tech lead was told

1. **Vietnamese is not a criterion.**
   - No stage spec makes an LLM write Vietnamese. Vietnamese appears only as UI labels (`apps/AA-CIS-App/CONTEXT.md:171`).
   - The golden set is en-US only (`scripts/aa729/select_samples.py:178,398`).
   - So the proposed Vietnamese gates (diacritics, garbled tokens) and every Vietnamese remark in `bedrock-writer-candidates/README.md:108-117` should be dropped.
2. **"Add validator rules for invented times of day" partly exists already.**
   - The T-series already has a deterministic rule: F17 trip_fact (`services/acp_content_writing/trip_facts.py:331-344`, routed by `quality_gates.py`). The T9 L0 reader also has a time-word list (`services/writing_memory/l0.py:42`).
   - The real gap is A1/S1:
     - `brand_audit_node.py:67-69` only matches am/pm clock times and says "Narrative morning/afternoon/evening is fine (not matched)". So "16:00" and "sunrise" are not caught.
     - `grounding.py` checks numbers only. "Around 16:00" turned into "by 16:00" keeps the same number, so it passes.
     - The taxonomy has an "invented timing" class for A1 (`services/quality/taxonomy.yaml:293`), but it is judged by an LLM, not checked deterministically.
   - This is a writer-quality gap that applies to Sonnet as well. It is not a gateway gap.
3. **The S12 capacity slice sits on a closed issue.**
   - AA-1002 was closed Done-with-scope (comment 31/10 01:22).
   - S12 was added to it three hours later (comment 31/10 04:29).
   - AA-642's restatement lists only S7, S8, S11 and the S9/S10 proof. S12 has no open home.

## Gap table

| # | Topic | Design says | Code today | Needed now (S261 findings) | Gap | Issue home |
|---|---|---|---|---|---|---|
| 1 | Per-stage routing and params (temperature, max_tokens, effort, response format) | Route as data: primary, fallbacks, shadow (ADR 0006 §1-3). Effort goes in deployment `request_defaults.effort_by_stage`, the same on every path (blueprint :1277, :1346; AA-1002.md:150-153). The S198 spec wanted route params (effort, max_tokens, temperature) (AA-642 "Original description" §3); never built. S12: `max_tokens` from p99 (capacity plan :427) | `StageConfig` has no params (`role_config.py:55-68`). `LLMRequest` defaults to max_tokens 4096 and temperature 0.7, set per call site (`models.py:16-17`). Converse caps max_tokens by catalog (`client.py:1228-1232`) and sends temperature only if `supports_temperature` (`:1231`). Only the Anthropic adapter reads `request_defaults` (`client.py:1400-1403`). Response format is a per-call `json_schema` | Per-stage, per-model effort and a `max_tokens` floor for reasoning families, set as data. Today Kimi K3 eats the judge's 1,200 tokens (`eval_judge.py:51`) and returns empty → billed as unusable (`client.py:1341-1345`) | (a) S12 max_tokens. (b) Effort is keyed per deployment and Converse ignores it. (c) No per-stage params on the route, as S198 had | AA-642 (new slice) |
| 2 | Legacy keys `haiku`/`sonnet` hard path | S3: legacy keys become aliases of logical Converse rows `sonnet-4-6`/`haiku-4-5` on acc3 and the Anthropic API; S11 moves them to 5.5 behind an eval (blueprint :1215, :1381) | `LLM_LEGACY_ALIASES` off; `_legacy_chain` is a hard acc3 chain (`client.py:833-910`). Mig 307 aliases point to legacy rows, so still acc3 only. The logical rows are an unbuilt contract draft (AA-1002.md:356-370). 18 CIS + 2 TP stages cannot reach anthropic-direct (AA-1002 comment 31/10 07:24) | Same as the design. Any acc2 test must avoid these keys, e.g. `score.py:246` pins `haiku` | (a) | AA-642 S11 (exists) |
| 3 | `account_route` acc3-only | The CHECK becomes an FK to connections (blueprint :1239). Bedrock chat models run on acc3 only (ADR 0001a d1-d2; ADR 0018:49,71-72) | `account_route` values other than acc3 are dropped (`client.py:589-592`); CHECK 'acc3' or NULL. The task-role Converse path on acc2 exists (`client.py:1201-1205`) | Routing any chat model on acc2 conflicts with ADR 0001a/0018. A paid A/B through `model_tier` does not route, but any route change later needs the ADR amended | (b) code goes beyond ADR. (c) ADR amendment | ADR 0009 / ADR 0001a amendment, AA-804 + AA-1004 (TL-23); no new issue |
| 4 | Region per deployment (us-west-2-only models) | Region is a connection column: one connection = one account × one region (mig 304:160,189). The profile type is the deployment's `wire_id` (:1247). A second region only on a capacity trigger (capacity plan §5.2:382-390). The checklist says connections are added in the admin (A3, :1318) | `native_runtime` builds the client from `conn.region` (`bedrock_satellite.py:200-212`). The task-role CHECK allows any region (304:205-207). So an `acc2-usw2` connection plus deployments needs **no code**. New connections are migration-only (AA-1002.md:423-428), which contradicts A3. ECS IAM allows `*` (`modules/ecs/main.tf:247-263`) | GLM-5, DeepSeek V3.2 and Qwen3 are us-west-2 only (`bedrock-writer-candidates/README.md:99-101, 180`). Needed: one connection row, SCP region allow-list (AA-1004 scope 1), the attribution fix (#10), its own limits and budget | (d) mechanism. (b) admin vs migration. (c) the design gives region only a capacity reason, not model availability | Part of the AA-642 catalog-rows slice; SCP in AA-1004 |
| 5 | Catalog vendor CHECK | Connection kinds "cover every known path"; a new family on an existing kind is data (:1183); `family` column planned | `vendor IN (anthropic, openai, cohere, typesafe)` (`169:25`; schema ref :8021). 304 widened only `provider`. `family` not added (AA-1002.md:43-46). `llm_role_config_provider_check` = claude/openai/cohere (`172:37-38`), display only | amazon, meta, moonshot, zai, deepseek, qwen, mistral, minimax, nvidia, google | (b)+(c): the design assumed a fixed vendor list. Better to add a `family` column and widen or drop the vendor CHECK | AA-642 (catalog slice) |
| 6 | Writer vendor rule in admin | Main writers never use a non-Anthropic vendor; judges never Anthropic (blueprint table 5 :1277-1279; CIS ADR 0006 §5, 0008) | `admin_llm_ops.py:180-183` checks vendor *identity*: judge ≠ anthropic, writer = anthropic. `model_tier` evals bypass it (`_call_catalog_model` has no rule) | An A/B through `model_tier` is fine today. If a non-Anthropic writer passes, the rule must become "judge family ≠ family of the writer it judges". Today a GLM writer plus a GLM judge would be allowed | (d) for the test. (c) for any switch: ADR amending 0006 §5 / 0008 | ADR 0009 (≤15/11, AA-642 comment); no new issue |
| 7 | Reasoning models (token budget, reasoning off, reasoning tokens) | OpenAI reasoning: `max_completion_tokens` (ADR 0006 §6). Anthropic: explicit effort (AA-1002.md:150-153). `capabilities` flags thinking_mode / default_effort (:1218). `openai_responses` reserved (:1438) | `capabilities` read nowhere (0 hits in `shared/llm_client`). Converse sends no `additionalModelRequestFields` (`client.py:1256-1258`). Converse usage has no reasoning split (`_add_converse_usage`, `client.py:290-293`). Test probe uses 32 tokens (`llm_connections.py:369-370`) | Kimi K3 defaults to effort `max`, and Converse does not pass `reasoning_effort` (needs Invoke or Chat Completions; candidates :170). gpt-oss cannot turn reasoning off; MiniMax always thinks. Needed: reasoning switch, token floor, reasoning-token logging per family | (a) read `capabilities`. (c) Converse and third-party reasoning, possibly a new api_style (checklist row C :1323), and reasoning-token accounting | AA-642 (new slice) |
| 8 | Structured output per model | `capabilities.forced_tool / structured_output` (:1218, :1430) | Converse always forces a tool, except a hard-coded marker list (`client.py:351-353, 1239-1250`). The rejection fallback matches narrow wording (`:364-369`). Bedrock native `outputConfig.textFormat` not used | Nova and Llama have no native structured output. Five candidates cap output at 8K (candidates :127). Real S1 schema validity is still to measure | (a) flags designed, not read. (c) Bedrock native JSON schema path | AA-642 (same slice as #7) |
| 9 | Caching | S6: `cachePoint` on Converse for Claude (:1225, S6) | Only for `anthropic.` profiles (`client.py:418-425`) | Nova and others run without cache. Costs more but nothing breaks | (d) now. Later via a `capabilities` flag | none |
| 10 | acc2 account attribution bug | Adapters pass `account = connection_key` explicitly (blueprint table 1 "Cost log" row) | `satellite_account=None if native`, with no `connection_key` (`client.py:1376-1380`). `_row_account` falls back to `connection_key` (`call_log.py:261-265`), which is unset, so acc2 chat rows get `account=NULL`. Budgets sum by `account` (`cost_guard.py:327-333`). Contrast the satellite path, which sets it (`client.py:1214`) | Must merge before any paid acc2 call, and before an `acc2-usw2` row | (b) bug | AA-642 (fix PR); AA-1002 is closed |
| 11 | Breaker and limiter on the legacy path | S12: legacy and vendor-direct paths go into the breaker (AA-1002 comment 31/10 04:29) | `_legacy_chain` has no breaker: 0 "breaker" hits in `client.py:833-930`, only `connection_budget.check` | Same as the design | (a) | S12, to move to AA-642 |
| 12 | Fallback across families and accounts | Model first, then the next model; no implicit or server-side fallback (:1285). No cross-account fallback (ADR 0001a). Two families per prod route (capacity §5.2). Writers never fall back to another vendor (table 5) | `_call_route` moves on any exception, model first (`client.py:745-791`) | Keep ≥2 families live (candidates :96-97). Judge, validate and embed: data only, once rows exist. Writer: blocked by #6 | (d) mechanism. (c) for writers (ADR) | ADR 0009 |
| 13 | Data scopes for AWS-served third-party models | `aws_only` vs `vendor_direct` per connection; scope changes by migration (CIS ADR 0012 §1-6) | acc2 seeded `aws_only` (304:285-303) | The 16 models are AWS-billed (`AmazonBedrock`), not Marketplace (candidates :152), so `aws_only` is correct. Not modelled anywhere: `global.` profile geography, and the tenant terms naming only Claude/OpenAI (blueprint table 11) | (d). (c) small: terms and AI Use Register must list model vendors | AA-820 (terms), AA-804 (register) |
| 14 | Budgets (monthly per connection, daily caps, provider caps) | Per run and per day (ADR 0001 d4); per connection plus nightly reconcile (S10); vendor spend limits (checklist A1) | `connection_budget` exists, but every connection's budget is NULL (304 seed; AA-1002 comment 30/10). Daily caps are opt-in per job; S1/T2/T8/T9/A3 are not covered (`cost_guard.py`; readiness §6). Harness caps exist ($5 `judge_compare`, $15 `score.py`, R2 $10 per run / $25 per month) | acc2 budget must be alert-only, because embeddings share the line. Separate dev/prod/bulk lines (S12) would allow a hard stop on chat only | (a) data not set, and S12 | AA-642 (S12) plus admin action ≤05/11 |
| 15 | Access probing and availability (Error 002 account blocks, per-model "not available") | Trust real calls only (:1247, :1293). Test button (S4). OPS-12 "unknown" after 24 h (AA-1003.md:161-164). Capacity plan: instant circuit-open alert ≤15/11, 3 CloudWatch alarms, warm probe | No scheduled probe. The acc2 refusal ("not available …") is a `ValidationException` that never opens a circuit and is classed `other` (`breaker.py:368-394`). No per-model access state | Access is granted per model and per account (GLM-5.3 and Grok refused on acc2, candidates :96). Weekly access matrix. Classify "not available for this account" as access_denied | (c) scheduled canary and per-model access state (review B3, a proposal only). (b) refusal classification | AA-642 slice "canary + access + lifecycle" (TL-13 puts it first). Instant alert in S12 |
| 16 | Model qualification (eval harness, golden sets, gates, promotion to a stage) | Switches between model generations are eval-gated (S11 :1381; S3 risk :1373). Golden-label check for the same model on another path (:1268). Priced before enabled (ADR 0005 §7). AA-919 R2 runner. AA-900 runbook | `judge_compare.py:51,71` hard-codes acc3. `score.py:246` pins haiku. R2 uses the stage route (`eval_writers.py:133`). Judge not calibrated: kappa 0.562 on 13 pairs, `counts=False` (arch review B2) | A written procedure to qualify a new family: judge first, then writer A/B against a frozen Sonnet 5.5 control, zero new hard-fact classes, promotion steps. Plus a human-labelled set (review N3) | (c) no new-family procedure in the design. (a) harness fixes | AA-900 (extend: runbook + family procedure + harness PR). Human labels: N3 pointed at AA-919, which is Done → fold into AA-900 or one new issue (ask) |
| 17 | Shadow when the primary is down | Shadow is A/B only, 0% outside a round (ADR 0006 §3; :1350) | Runs only after the primary succeeds (`client.py:615-621`) | Nothing. Shadow-on-failure would be a hidden fallback and extra spend. Use `model_tier` evals | (d) | none |
| 18 | Observability (latency, outcome per attempt, traces per job, prompt capture, per-app view) | Ledger is the source of truth; traces deferred (AA-842 option B). Ledger v2: app, is_shadow, status, attempt_no, prompt_hash (AA-804 scope) | No latency, outcome, attempt, connection or reasoning columns; rows written by call sites; refused calls leave no row (readiness obs §1.1). No job-calls UI filter (`admin_llm_ops.py:773-846`) | p50/p95 latency per model and reasoning tokens for the A/B. Refused attempts. Job trace view | (a) AA-804. (c) `latency_ms`, `error_class`, `connection_key`, `reasoning_tokens` are not in AA-804's list | AA-804 (extend scope); no new issue |
| 19 | TripPlanner and CRM on the shared core (S8) | `aa_llm` vendored; plug in without deploy only after S8 (:1328-1336; ADR 0008a) | TP fork ignores deployments, scopes, breaker and budgets; IAM is Cohere only (`tripplanner.tf:331-336`); `max_tokens` 1200 (`agent.py:55`). CRM is a stub (`gateway.py:106-127, 276`) | Not needed for a CIS-only A/B | (a) | AA-642 S8 (≤13/12) |
| 20 | Price source for new models | Catalog price plus `price_source`; unknown = flagged estimate, never 0 (S6; ADR 0005 §7) | `enabled_needs_price` CHECK (schema ref :8018). Estimate at Sonnet rates, flagged (`pricing.py:165-202`). `cis_app` can INSERT catalog rows but deployments are SELECT-only (schema ref :8022, :8053) | AWS Price List figures for 16 models (candidates :149); per-region overrides on deployments | (d) | Part of the catalog-rows PR |
| 21 | Lifecycle (Legacy / EOL) | Not in the design. Catalog has only `enabled` / `blocked_reason` (schema ref :7990-8013) | No columns | Four candidates are Legacy, EOL 2027-03-30 (candidates :126). AWS: a Legacy model may lose access after 15 days unused (review B3) | (c) | AA-642 canary/lifecycle slice (same as #15) |
| 22 | Deterministic fidelity rules (not gateway) | Systematic-quality direction | T-series F17 exists (`trip_facts.py:331-344`). A1 is am/pm only (`brand_audit_node.py:67-69`), and `grounding.py` checks numbers only | Port the time-of-day and "around → by" hardening rules to A1/S1. This applies to every model, Sonnet included | (c) for A1 | New A1 quality issue (Linear search "fidelity" found only AA-919, AA-741, AA-790) |

## Issue map

**Fold into existing issues (no new issue):**
- **AA-642 (Todo).** Restate it with:
  - S12, moved off the closed AA-1002;
  - acc2 attribution fix (#10);
  - catalog family/vendor and region rows (#4, #5);
  - per-family reasoning and structured-output capabilities, plus per-stage params (#1, #7, #8);
  - canary, access state and lifecycle (#15, #21);
  - S8 and S11 as they stand.
- **AA-900 (Todo).** Eval runbook plus a "qualify a new model family" procedure, and the harness fixes (#16).
- **AA-804 (Backlog).** Ledger v2 gains `latency_ms`, `error_class`, `connection_key`, `reasoning_tokens` (#18). ADR 0009 decides the writer-vendor and acc2-chat (ADR 0001a) questions (#3, #6, #12) by 15/11.
- **AA-1004.** SCP region allow-list for us-west-2 (#4).
- **AA-820.** Model vendors named in the tenant terms (#13).

**Possibly new (ask the tech lead before creating, per the `aa-linear-issue` rule):**
1. A1/S1 deterministic fidelity rules (#22). This is not gateway work.
2. A human-labelled set plus judge calibration, if it is not folded into AA-900, since AA-919 is Done (#16).

## Design additions to make before any route change

These are the gap-(c) rows:
- Model family as a first-class field, with the writer/judge rule based on family.
- Per-stage params as data, with a reasoning switch per family.
- Region chosen by model availability, not only by capacity.
- A per-model access state, a daily canary and lifecycle tracking.
- A qualification and promotion procedure for a new family.

The best place is ADR 0009 (AA-804, Proposed by 15/11), which the plan already requires. That puts this design work ahead of the A/B harness PRs, and keeps all routes unchanged as the tech lead decided.

## Issue liên quan (Linear)

# LLM gateway, models, eval and AI-governance issues in Linear (team AA_Ecosys), read 31/10/2026 (S261)

The open issues already cover the gateway plumbing (AA-642, plus S12 in the AA-1002 comments), budgets and limits (AA-1016, AA-1015, AA-964), evaluation (AA-900, AA-920) and governance (AA-804). None of them covers adding new Bedrock model families, qualifying them, running them from a second region or checking per-model access on a schedule. A non-Anthropic writer is excluded by rule, so it needs an ADR first.

Sources: Linear `get_issue`, `list_comments` and `list_issues` searches for Bedrock, judge, LLM, eval, catalog and us-west-2; `docs/linear-export/*`; `docs/backlog/README.md`; `docs/backlog/tracker/plan.json`; capacity plan §7.1.

**The local trackers are stale.** Both `plan.json` (`updated`=2026-10-30, S260) and `docs/backlog/README.md:9` ("Last updated: S260 close") predate the S261 triage.

| Issue | Linear (S261) | Trackers say | Note |
|---|---|---|---|
| AA-1002 | Done | In Progress | — |
| AA-919 | Done | In Progress | — |
| AA-900 | Todo | In Progress | — |
| AA-920 | Backlog | In Progress | — |
| AA-1000 | Backlog | In Progress | — |
| AA-998 | Backlog | In Progress | — |
| AA-642 | Todo | Backlog | plan.json still uses the old title "[EPIC] Model Gateway…" |
| AA-1015, AA-1016 | exist | not listed | created S261 |

## A. Gateway core

**AA-1002: AWS org blueprint + plug-and-play multi-provider LLM gateway (Done, with scope)**
- **Covers:**
  - The blueprint.
  - Gateway S1–S6, S9 and S10, live on Dev with no billed traffic (comment 31/10 01:22).
  - The S261 Dev road on the Anthropic API, without a key: `s1_generate` and `supply_content_writer` scopes widened to vendor_direct; `anthropic-direct` budget 150 USD (comment 31/10 07:24).
  - New slice **S12 "capacity controls"** (comment 31/10 04:29):
    - per-line reserved-TPM ceiling; dev / prod / bulk connection lines;
    - legacy and vendor paths wrapped into the breaker;
    - Anthropic spend-cap 429 / spend-limit 400 treated as "path out of money";
    - per-app "LLM off" and "bulk paused" switches; waves stop when a prod circuit opens;
    - instant circuit-open alert;
    - `max_tokens` from p99.
  - S12 is a comment only. The issue is closed and no other issue's scope lists S12.
- **Where the rest went:**
  - IaC, CLI and org work → AA-1004.
  - S7, S8, S11, S1-infra and the live S9/S10 proof → AA-642.
  - Gap: 18 CIS and 2 TripPlanner legacy `haiku`/`sonnet` stages cannot reach anthropic-direct (07:24).
- **Not in it:** new model families, region expansion, model qualification.

**AA-642: Gateway remaining slices (Todo; restated S261)**
- **Covers:**
  - S7 batch: deferred until trigger T-BATCH.
  - S8: shared `aa_llm` core for TripPlanner and CRM. ADR 0009 Proposed by 15/11; S8 by 13/12 or go-live minus 6 weeks (comment 31/10 04:29).
  - S11: legacy stages moved to the 5.5 models through catalog route rows.
  - Live S9/S10 proof: one billed call reconciled, plus budget enforcement.
  - S1-infra: `AA-LLM-Invoker` per org. This is carried in AA-1002 comment 01:22, not in the issue's Done-when.
- **Not in it** ("Original description · Out of scope"):
  - changing any model choice ("decided by the eval issues");
  - prose prompts;
  - new vendor families, us-west-2 deployments, the catalog `vendor` CHECK, reasoning-model config, the `capabilities` reader. None of these is listed.
  - The S198 route params (effort / max_tokens / temperature) and the `cascade` idea are history only; they are not in the restated Done-when.

**AA-804: AI platform ADR + ledger v2 + AI Use Register (Backlog; plan milestone M5 "later")**
- **Covers:**
  - Root ADR "AI platform and governance". The title says "0006", but the number reserved is **0009** (`docs/adr/README.md:46`).
  - `llm_call_log` v2: app, is_shadow, status, attempt_no, prompt_hash, is_experiment; failed billed attempts logged.
  - Undeclared stages become errors.
  - AI Use Register: owner, golden set, budget, kill switch per stage.
  - PII-on-LLM-path decision and detector (comment 15/10).
  - Cost Explorer vs ledger ≤ 5%.
- **Shipped already:** only the egress-policy slice (mig 224; comment 16/10).
- **Not in it:** model qualification, region, vendor families.
- **Overlap:** the 15/11 ADR 0009 deadline is tracked in AA-642, while AA-804 stays Backlog/"later" in plan.json. Two issues own the same ADR.

**AA-1004: Lean AWS model, including the Bedrock path (In Progress; plan "waiting on billing")**
- **Covers:**
  - Org, Identity Center, SCPs, Terraform roots.
  - Bedrock path per the billing decision; the Anthropic/OpenAI direct connections keep AI running meanwhile (scope 4).
  - Prod at go-live (scope 6, which also absorbs AA-880).
  - Done-when: "AI works again on Dev through at least one path… live call in llm_call_log".
  - From capacity plan §7.1: read and record acc3 quota; Anthropic Dev workspace + spend limit; `App` cost tag; per-app invoker; prod embedding path.
- **Not in it:** catalog rows, per-model access checks on acc2, us-west-2 model enablement. The SCP region allow-list has only "global and AI cross-region exceptions".

**AA-998: Remove acc1 (Backlog, due 01/12)**
- **Covers:** only Done-when item 4 is left, acc1 November cost = 0 (comment 31/10).
- **Not in it:** any LLM work.

## B. Budgets, capacity, per-app AI

| Issue | State | Covers | Not in it |
|---|---|---|---|
| **AA-1016** Content studio per-tenant AI budget | Backlog (new S261) | `tenant_ai_budget_usd`; alert at 100%, staff approval from 150%; T9 counted in plan quota; % used on Tenant 360 | per-model/connection limits; concurrency per tenant (trigger only, capacity §7.1) |
| **AA-1015** TripPlanner per-session/IP AI limits + bot check | Backlog (new S261) | `/narrate` and `/search` limits; BotID/Turnstile; separate daily caps; 80% alert | gateway S8 integration (separate, AA-642) |
| **AA-964** CRM-33a AI gateway + drafts + guardrails | Backlog, slot S264 | CRM AI calls with scrub → budget → ai_enabled; 75/90% alerts; per-agency calls/min cap; prompt-injection rule; guardrail behaviour when acc2 Bedrock fails; prod `ai_budget_usd` (comment 31/10) | depends on S8 and an LLM path |
| **AA-965** CRM-33b supplier confirmations, notes → options, voices | Backlog, S265 | CRM AI features | gateway work |
| **AA-896** FinOps doc + Cost Anomaly Detection + monthly cost report | Todo (plan: In Progress, ≥01/11) | `finops.md`, anomaly monitors, monthly `docs/ops/cost/YYYY-MM.md` with LLM cost per stage; from capacity §7.1: 3 CloudWatch Bedrock alarms on `aa-ai`, Anthropic reconcile via Admin key | per-model access monitoring |
| **AA-1003** Report engine, 63 reports R0–R7 | Todo | OPS-12 digest (including "LLM route unknown"), FI-* cost reports | LLM qualification |
| AA-649 Cost guard (`shared.spend_budget`) | Done (export) | per-run/per-day budgets per provider | — |
| AA-825 log retention + rollups | Done (export) | `llm_call_log` 180 d + daily rollup | — |
| AA-880 L9 prod blueprint | Done with scope 31/10 | remainder → AA-1004 item 6; the 31/10 comment adds the prod TPM sheet, ramp load test at G−6 weeks, quota request, SLOs, runbooks | after closing, these capacity items have no open owner except AA-1004 item 6 |

## C. Evaluation, judges, quality gates

**AA-900: LLM ops docs, prompt versioning, eval gate (Todo, blocked on an LLM path)**
- **Covers:**
  - prompt register and eval runbook;
  - generated route/catalog table (CIS #1136, root #322);
  - manual eval on the AA-729 golden set with a cost cap, `stage=adhoc_aa900`;
  - trigger: re-run R2 t9_blog (cap $2) on a prompt-change PR (comment 31/10).
- **Not in it:**
  - `prompt_version` column (belongs to AA-804);
  - automatic per-PR eval gate (only if the ~30 USD/month spend is approved);
  - the golden set itself (AA-729);
  - any protocol for qualifying a new model or family.

**AA-919: Eval and release gate (Done with scope, S261)**
- **Covers:** WM-17..22, i.e. golden set 1.3.0 (134 items), R2 runner capped at $10 per release, targeted shadow, Releases tab.
- **Moved out:** judge calibration (kappa ≥ 0.6 per stratum) → AA-920.

**AA-920: Inject approved rules into the 4 writers (Backlog)**
- **Covers:**
  - WM-23..26: house rules into A1/S1, T9, T2; post-activation check with auto rollback;
  - Done-when now also has judge calibration kappa ≥ 0.6 with `judge_counts=true`.
- **Not in it:** judge model choice, e.g. trying gpt-oss-120b. No issue owns a judge model A/B today.

**AA-922: Weekly KPIs, soft-stop rollback, disagreement queue (Todo).** Writing-memory KPIs (shipped S260, CIS #1187).

**AA-921: Pinned example sets and tenant preference summaries (Backlog).** Real summaries still need an LLM path.

**AA-1000: Tier-2 LLM adjudicator for T10 (Backlog, blocked)**
- **Covers:** cheap-model adjudicator on T-series recall classes that never holds a piece; calibration capped at $5, then shadow. Mode off (mig 308).
- **Not in it:** S1/A-series validators.

**T10 gates (T-series tenant pieces only):**
- **AA-790** (Backlog): tenant-voice rubric gate + post-repair integrity check.
- **AA-788** (Backlog): promote F12/F14/F9_brand_style to blocking.
- **AA-781** (Backlog, parked): F9 v2 claim classification.

**AA-741: T-series end-to-end audit (Backlog).** Paid T0→T11 run, about $10–20.

**AA-782: A/B a cheaper T9 blog writer, gpt-5.6-luna vs Sonnet (Backlog, parked; "needs: Vendor rule")**
- This is the only open issue that tests a non-Anthropic writer.
- It says a non-Anthropic writer "needs the writer role changed to `validate` or a vendor-rule decision (ADR-2026-014/027)". That conflicts with ADR 0008, which bars relabelling a writer as validate to dodge the rule.
- **Not in it:** S1/A-series, Bedrock third-party families.

**AA-842: OTel gen_ai tracing (Backlog, held)**
- Read-only reports from S238 and S257 are done.
- Trigger: a concrete debugging need, or AA-804 making tracing cheap. "Do not ask again" (comment 31/10).

**Closed references (export):**
- AA-729: golden set 100 → 1.3.0 plus scoring script.
- AA-714: judges on GPT Luna.
- AA-645: Sonnet 5 writer eval; S1 catalogue 810/810 on writer v2 / sonnet-5-5.
- AA-658: Converse provider + model catalog.
- AA-659: stage routes, fallback, shadow, judge ≠ writer vendor guard.
- AA-685 / AA-686: call sites behind the gateway; route editor UI.
- AA-660: Jev `decide()`.
- AA-765 / AA-763: judge clients consolidated; T-stage keys.
- AA-843: legacy chain wasting acc2-native calls.
- AA-862 / AA-856: Cohere embed throughput.
- AA-623 / AA-635 / AA-927: reconcile and logging gaps.
- AA-999: Kiro as a provider, "do not use".

## D. Legal and parked

- **AA-820** (Todo, ≤11/11): tenant Terms clause for the Anthropic AUP. It decides `vendor_direct` for tenant content (capacity §7.2).
- **AA-704** (Backlog, parked): in-app AI assistant.
- **AA-864** (Backlog, "Still wanted?"): one-account consolidation research.

## E. Where today's proposals land

| Proposal from the candidates research | Existing owner | Status |
|---|---|---|
| Fix account recording for acc2 in `llm_call_log` | Partly AA-804 (ledger v2) and AA-1002 S3 "accounts as data", which is Done | No explicit item → **new work**; it can sit under AA-642 as a slice |
| Config for reasoning models (non-Anthropic/OpenAI); a reader for `capabilities` | None. AA-642 S11 covers effort only for the 5.5 legacy move | **New** |
| Catalog rows for new families (GLM, DeepSeek, Qwen, Kimi), seeded disabled, region us-west-2; widen the `vendor` CHECK | None. AA-1002 is closed and AA-642 does not list it | **New**, or an explicit added slice on AA-642 |
| Gateway calling us-west-2 + IAM/SCP for acc2 | Capacity plan §5.2 says "second region only on trigger"; AA-1004 SCP region list | Not owned → **new** (or AA-1004 scope add) plus a decision |
| Change the eval script for writer A/B | AA-900 (runbook) + AA-919 machinery (Done) | Partial overlap; the qualification protocol for a new family is **new** |
| A/B a non-Anthropic writer (GLM-5, DeepSeek V3.2, Qwen3, Kimi K3) on S1 | Blocked by CIS ADR 0006 §5 / 0008 and blueprint table 5 (:1277-1279). AA-782 is the only precedent and is parked on "vendor rule" | Needs an **ADR amendment first**; otherwise out of policy |
| Judge trial with gpt-oss-120b against golden labels | AA-920 owns the kappa ≥ 0.6 calibration; AA-714 (Luna) is Done | Overlaps AA-920; the model A/B itself has no owner |
| Deterministic validator rules for made-up times of day, "about 16:00" → "before 16:00", "dinner under the stars" (S1/A-series) | T10 gates (AA-788, AA-790, AA-1000, AA-781) are T-series only; AA-692 (meal/time regex) is Done | **New** for S1/A-series |
| Vietnamese diacritics/junk-character validator | No stage spec outputs Vietnamese; tours are English | **Not needed**; drop it |
| Per-model, per-account access probe on a schedule; model lifecycle / EOL watch | AA-1002 S12 instant circuit alert (closed issue, comment only); AA-896 CloudWatch alarms; arch review B3 is a proposal only | **New** |
| Keep 2 model families in every fallback chain | Capacity §5.2; no issue | **New**; also a writer-vendor policy question (ADR) |

**Ownership gaps besides the new items:**
- S12 lives only as a comment on a Done issue (AA-1002).
- The ADR 0009 deadline is in AA-642 while AA-804, which owns that ADR, stays Backlog/"later".

## Phản biện theo góc

### Kiến trúc

**Verdict.** The three-layer registry (connection, deployment, logical model) is the right shape for many model families, regions and accounts. The design falls short in five places:

- **Wire format sits on the wrong table.** The protocol is a column of the logical model, not of the deployment.
- **Per-call overrides bypass the route.** A `model_tier` set at the call site skips the stage route and its policy.
- **"Vendor" means three things.** The same field stands for the model's creator, the host that sells it, and the path we call it through.
- **Capabilities and parameters have no single home.** The design declares them, but the code does not read them.
- **Old paths are never retired.** Each slice adds a new path next to the old one, and nothing removes the old ones.

These are design gaps, not only gaps in the build. All checks were read-only, with CIS code at `1b6e9448`.

## Top weaknesses

1. **HIGH. A per-call `model_tier` is a second routing system that skips the stage route.**
   - **Evidence:**
     - When `model_tier` is set, the call "wins and runs alone (no route, no shadow)" (`shared/llm_client/client.py:595-597`, shadow skipped at `:619`).
     - The writer/judge vendor rule is only checked in the admin form (`api/routers/admin_llm_ops.py:180-183`), never at call time.
     - Data scopes are still applied (`client.py:580`).
     - 44 non-test lines contain `model_tier=`; many just pass the value through. Several hard-code a model: `"haiku"` in `services/acp_contract/segment_research.py:483`, `segment_research_batch.py:190`, `services/eval/regression.py:170`, and a `"haiku"` default in `s1_batch.py:210`.
   - **Why it matters:**
     - The rule "routing is data" (design principle 3) is only partly true.
     - A route change in the admin does not move these calls.
     - An A/B run through `model_tier` could put a GLM model in a writer role or a GPT model in a judge role with no rule stopping it.
2. **HIGH. The wire format (`api_style`) belongs to the logical model, not to the deployment.**
   - **Evidence:**
     - The code dispatches on `model.api_style` (`client.py:1106-1113`).
     - Whether a call goes through the Anthropic API is worked out from the first deployment's connection kind (header of `api/migrations/306_llm_anthropic_deployments.sql:3-6`).
     - The blueprint's own model table still has keys that name the path, such as `gpt-6-luna-openai` and `cohere-embed-v4-acc3` (blueprint section 4).
   - **Why it matters:**
     - The same model reached through a different protocol needs a new catalog row, which means a new "model". One example is Kimi K3 needing InvokeModel or Chat Completions to set `reasoning_effort` (`bedrock-writer-candidates/README.md:170`).
     - This undoes the separation between deployment and model.
3. **HIGH. The migration from old to new paths was never finished: five or more dispatch paths run side by side.**
   - **The paths:**
     - the plan path behind `LLM_DEPLOYMENT_ROUTING`;
     - the S2 vendor path;
     - the direct `openai_chat` path;
     - native and satellite Converse;
     - `_legacy_chain`;
     - alias steps, behind `LLM_LEGACY_ALIASES`, which is off.
   - **Evidence:** the code says so itself: "the paths below call a connection without a plan, so they check its hard budget themselves" (`client.py:1090-1113`).
   - **Consequences already visible:**
     - The legacy chain has no circuit breaker (gap #11).
     - The acc2 account is not recorded on the native path (`client.py:1376-1380`, gap #10).
   - **Why it matters:**
     - Every cross-cutting control (S12 breaker, budget, ledger) has to be added N times.
     - The "no behaviour change per slice" principle (AA-1002.md:52-61) has no step that deletes the old path.
4. **MED-HIGH. Model creator, host and path are mixed into one "vendor" field.**
   - **Evidence:**
     - The catalog `vendor` CHECK is a closed list (`api/migrations/169_llm_model_catalog.sql:25`).
     - The planned `family` column was never added (AA-1002.md:43-46).
     - The writer/judge rule compares vendor names (`admin_llm_ops.py:180-183`).
     - The blueprint claims the connection kinds "cover every known path" (:1183). That holds for transport, not for who made the model.
   - **Why it matters:**
     - For a third-party model on Bedrock, "vendor" could mean the maker (Moonshot) or the seller (AWS).
     - Judge independence and evaluation care about the maker.
     - Data scope and billing care about the host.
5. **MED. `capabilities` is declared but never read, so model behaviour still depends on matching strings.**
   - **Evidence:**
     - Nothing in `shared/llm_client` reads `capabilities`.
     - Forced-tool use is controlled by `_NO_FORCED_TOOL_CHOICE_MARKERS` (`client.py:351-361`).
     - The cache point is gated by checking whether the model ID contains `"anthropic."` (`client.py:423`).
   - **Why it matters:**
     - Every new model family needs a code change, which defeats the plug-and-play goal.
     - The design also puts capabilities only on the logical model, but some depend on the path. Structured output, caching and reasoning controls can differ between Bedrock and a direct API.
6. **MED. Request parameters have no single home and no precedence rule.**
   - **Evidence:**
     - The stage config has no parameters (`role_config.py:55-68`).
     - Every call site sets its own defaults: `max_tokens` 4096 and `temperature` 0.7 (`models.py:16-17`).
     - The catalog caps the output (`client.py:1228-1232`).
     - Effort sits in the deployment's `request_defaults` (blueprint :1277), and only the Anthropic adapter reads it (`client.py:1402`).
   - **Why it matters:**
     - Effort is a property of a stage on a given model, not of a path.
     - Keying it by deployment means the rule "same effort on every path" holds only if someone copies the value onto every path.
     - There is nowhere to set a minimum token budget for reasoning models.
7. **MED. "Plug and play" really means a migration plus a DB Migrate run.**
   - **Evidence:**
     - Connection rows and region can only be added by migration (AA-1002.md:423-428).
     - New catalog and deployment rows are contract migrations applied by hand (AA-1002.md:268-270).
     - This contradicts blueprint checklist step A3, "Admin › Connections › Add" (:1318), and the goal of "≤30 min, no deploy" (:1183).
   - **Why it matters:** the design promises a speed it does not deliver. Config-as-code (changes through migrations) is a reasonable choice, but it has not been made on purpose.
8. **MED. Which account may serve which role is encoded twice, and the two do not agree.**
   - **Evidence:**
     - The `account_route` CHECK allows only `acc3` or NULL (mig 295), and the code ignores any other value (`client.py:587-592`).
     - Meanwhile a task-role connection can already make acc2 serve chat models through Converse (`client.py:1201-1205`).
     - The planned fix replaces the CHECK with an FK to connections (blueprint :1239). A stage pinned to one connection then clashes with deployment priority.
   - **Why it matters:** ADR 0001a and ADR 0018 say chat models run on acc3 only, but no single place enforces that.
9. **LOW-MED. Access per model and account, and model lifecycle, are not modelled.**
   - **Evidence:**
     - The health table is already keyed by connection and model (blueprint section 2).
     - A "not available for this account" refusal is classed as `other` and never opens a circuit (`breaker.py:368-394`).
     - The catalog has no lifecycle or end-of-life columns.
   - **Why it matters:** access is granted per model and per account (GLM-5.3 and Grok were refused on acc2), and Bedrock may drop access to an unused Legacy model.
10. **LOW. The alias table adds another level of fallback ordering.**
    - **Evidence:** `shared.llm_model_alias` keeps an ordered list of models per alias (`307_llm_model_alias.sql:12-19`).
    - **Why it matters:**
      - Order is now set at three levels: route, then alias, then deployment priority.
      - Explaining why a call took a given path gets harder.
      - The alias should be a temporary migration step with a date for removal.

## What the design gets right

- **Splitting connection, deployment and logical model** is the correct structure (blueprint :1178-1181; mig 304).
- **Safety rules are enforced in the database, not only in code.** CHECKs force the secret name prefix and restrict which auth mode each kind may use; the base URL is limited per kind by a CHECK plus a code allowlist (304, lines 175-210).
- **Fallback is explicit.** The order is the same model on another path, then the next model in the route. There is no hidden or server-side fallback, and every fallback is logged (:1285).
- **Data scope is a separate policy axis.** Each connection has a scope and each stage lists the scopes it allows (CIS ADR 0012).
- **The cost ledger is the source of truth.** An unknown price is flagged as an estimate and never recorded as 0 (ADR 0005 §7, S6).
- **The library-first choice is sound.** A vendored library now, an HTTP gateway service only when there is a reason, and LiteLLM rejected (:1328-1336).
- **The breaker works per deployment, with its state shared** in `llm_provider_health`.

## Proposed design changes

1. **Move the wire protocol (`api_style`) to the deployment.** The catalog then holds pure logical models, and keys that name a path become deployments of one model.
   - Why: one model can be served over several protocols without becoming a new "model" (weakness 2). This unblocks the Kimi K3 Invoke path.
   - Effort: M. Depends on: S3 aliases; TripPlanner keeps reading `bedrock_profile_ids` until S8.
2. **Split model identity into family and host.**
   - What:
     - add a `family` column on the catalog, as a foreign key to a small `llm_model_family` table;
     - drop the closed vendor CHECK;
     - derive the host from the connection kind;
     - enforce at call time that a judge's family differs from the writer's family.
   - Why: weakness 4, and the writer/judge rule becomes a runtime rule instead of an admin form check.
   - Effort: S. Depends on: ADR 0009 for the writer rule.
3. **Restrict `model_tier`.**
   - What:
     - allow it only in eval or probe contexts (`bind_eval_stage`), or for a key already in the stage's route;
     - apply the vendor rule, breaker and budget either way;
     - move hard-coded `"haiku"` call sites to stage routes;
     - turn the AA-237 auto-upgrade (haiku to sonnet) into a stage route variant.
   - Why: weakness 1.
   - Effort: M. Depends on: S11.
4. **One dispatch pipeline.**
   - What:
     - route, then deployment plan (including legacy paths through alias rows);
     - then one shared middleware chain: scope, budget, limiter, breaker, account attribution, ledger;
     - then the adapter chosen by protocol.
     - Delete the S2 vendor path, the direct OpenAI path and `_legacy_chain` once S3 is live, and give each feature flag a removal date.
   - Why: weakness 3; it also closes gaps #10 and #11 by construction.
   - Effort: M-L. Depends on: the S3 logical rows. No quality eval is needed, because the model stays the same.
5. **Effective capabilities = catalog values plus a per-deployment override.** Adapters read only the effective values.
   - Typed flags:
     - `reasoning`: mode, control, `min_output_tokens`;
     - `structured_output`: native_schema, forced_tool or prompt_only;
     - `prompt_cache`: cachepoint, cache_control, auto or none.
   - Remove the marker lists and the `"anthropic."` substring check.
   - Why: weakness 5.
   - Effort: S-M.
6. **Store parameters as data, keyed by stage and model.**
   - What:
     - a `stage_model_params` table holding effort, `max_tokens`, temperature and reasoning settings;
     - a fixed order of precedence: call-site hard limits, then stage × model values, then protocol defaults (such as `api_version`);
     - each adapter translates neutral parameters into its wire format.
   - Why: weakness 6. Keying effort by stage × model keeps "same effort on every path" true by construction.
   - Effort: S-M. Depends on: change 5.
7. **Decide connection change control on purpose.**
   - What:
     - creating connections, region and secret go through migrations;
     - the admin only switches connections on and off and sets priority, limits and budget;
     - rewrite blueprint step A3 and the "≤30 min" goal to "1 PR + DB Migrate".
   - Why: weakness 7.
   - Effort: S (documentation only).
8. **Retire `account_route`.**
   - What:
     - state which roles each connection may serve as a connection column, for example acc2 = embed only;
     - check it against the stage's role;
     - drop the column instead of turning it into a foreign key.
   - Why: weakness 8.
   - Effort: S. Depends on: amending ADR 0009 or ADR 0001a.
9. **Track access and lifecycle per model and connection.**
   - What:
     - add `access_state` and `last_probe_at` to `llm_provider_health`;
     - add `lifecycle_status` and `eol_date` to the catalog;
     - classify "not available for this account" as access denied;
     - run a scheduled probe that feeds these columns.
   - Why: weaknesses 9 and 10, plus the per-account access finding.
   - Effort: S-M.

**Order of work:** changes 2, 5, 6 and 8 are design decisions for ADR 0009 (AA-804, due 15/11). Changes 1, 3, 4 and 9 are implementation slices under AA-642. Change 7 is a blueprint correction. All of these should come before any route change or any A/B run that goes through `model_tier`.

### Vận hành (SRE)

# LLM gateway design: reliability/SRE review (S261, read-only)

The S261 gap table was not cross-checked from this angle. Below it is checked against the design and against CIS code at `1b6e9448`. I made no edits and no AWS, DB or LLM calls, and did not read Linear (the AA-1002 / AA-642 comment facts come from the task brief). Tour writing is English only; nothing here depends on Vietnamese.

The incident that matters for this review is the 29/10 one. A change of payer/org blocked the only LLM account, for every model and every region (postmortem `docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md:18-20,48-56`). The design must survive that class of event, not only throttling.

## Corrections to today's findings (verified in code)

1. **Gap-table row 15 is probably wrong.** The wording "is not available for this account" already matches `ACCESS_DENIED` (`shared/llm_client/errors.py:42-48`), and that class opens the circuit on the first failure (`breaker.py:101`). Check the raw logged message before writing a "classification fix".
2. **The Anthropic 429 spend cap is still misclassified.** Capacity plan §5.2 asks for two rows in `errors.classify`.
   - The 400 workspace-limit row already exists (`errors.py:53-58`; adapter `anthropic_messages.py:292-300`).
   - The 429 `enforced_spend_limit_reached` row does not. Every 429 is classed `throttled` "checked first, never from the text" (`anthropic_messages.py:27,303`). So an out-of-money path gets job retries and breaker re-probes (30 s, capped at 300 s, `breaker.py:103`) until month-end, and never raises `LLMAccessDenied`. This hits the very path meant to be the independent backup.

## Top weaknesses

**W1 (High). Nothing in the design requires a funded, warm second path.**
- Why it matters: the design itself names the direct Anthropic API ("path 3") as the only path independent of the org/payer layer (`docs/audits/2026-10-31-S261-aws-bedrock-org-access/current-situation-model.md` §"Hai tầng hỏng", "Chỉ đường 3 độc lập…"). Yet fallbacks are optional route data.
- What is true today:
  - `anthropic-direct` is disabled and has no key.
  - Migration 311 sets `allowed_scopes = {aws_only}` for every CIS stage except judge/validate, and `deployment_plan` never falls from `aws_only` to `vendor_direct` (current-situation-model §1; `vendor_route.py:213-226`). Only `s1_generate` and `supply_content_writer` were widened on Dev.
  - T-series writers and `tp_*` stay `aws_only` until AA-820 and the DPA (blueprint :1358-1360).
  - 18 CIS + 2 TripPlanner legacy-key stages cannot reach `anthropic-direct` because S3 aliases are off (AA-1002.md:240-373).
  - The judge fallback, OpenAI direct, has no credit (429).
- Result: a repeat of 29/10 leaves about 2 stages able to fail over. A route with acc3 Claude first and acc3 Nova second looks diverse, but Error 002 blocked Nova too.

**W2 (High). Loss of access is found only by real traffic.**
- The breaker reacts only to real calls (`breaker.py:24-27`). Fallback-only and idle deployments are never exercised, so traffic can fail over onto a path that is already dead.
- On 29/10 the problem surfaced through a paid eval run, and refused calls leave no `llm_call_log` row (postmortem §5).
- OPS-12 flags "unknown" only after 24 h (`AA-1003.md:161-164`).
- The planned additions are partial: an instant alert only for prod circuits, and a daily warm probe only for Anthropic (capacity plan §4.2, §5.3). A scheduled canary per connection × model is still only a proposal (review B3).
- Bedrock Legacy models can lose access after 15 days unused. That hits exactly the standby models nobody calls.

**W3 (High). The route time cap and "no hidden SDK retry" were designed but not built.**
- The design asks for a time cap on the whole route, `max_retries` 0–1 on 429, and a retry budget of at most 6 attempts per chain (blueprint :1222, :1285; capacity plan §5.2).
- Code today:
  - `_call_route` has no deadline (`client.py:745-791`).
  - acc3 Converse uses `get_satellite_client`, which builds its client with no botocore `Config` (`client.py:1262`; `bedrock_satellite.py:187-194`). It therefore runs with SDK defaults: hidden throttle retries and the default read timeout.
  - The legacy client uses `read_timeout=300` with legacy `max_attempts: 2`, which means 3 attempts (`client.py:550-553`; semantics noted at `embed.py:70`).
  - The connection columns `timeout_s` and `max_retries` (`connections.py:134-135`) are read only by the Anthropic and OpenAI adapters, never on the Bedrock path.
  - The limiter can add up to 30 s of waiting per deployment (`breaker.py:113`).
- Result: one request on a multi-model route can run for many minutes. That cannot meet the interactive SLO (TP p95 time-to-first-token < 5 s, capacity plan §5.7). Attempts also multiply: SDK retries × deployments × models × 3 job attempts (`queue.py:58`) all spend the same quota during a throttle.

**W4 (Med-High). Quota is shared, and job claiming has no backpressure.**
- Dev, bulk and prod share one acc3 quota (current-situation-model "Ba đường gọi model", path 1).
- The limiter counts requests and concurrency per process, not tokens, and not across tasks (`breaker.py:29-33`). Bedrock quotas are in tokens per minute, and the real ceiling grows with the ECS task count.
- Job claiming is FIFO with a cap per job kind and ignores circuit state (`queue.py:95-108`). Wave pacing is manual (capacity plan §5.1).
- The fix, slice S12 (bulk line, "bulk paused", wave stops when a prod circuit opens), sits on the closed AA-1002 (gap-table correction 3).

**W5 (Med). Failure domains are not modelled.**
- Connections carry account and region, but no payer/org or vendor domain. So the rule "≥2 families / independent source" (capacity plan §5.2) cannot be checked, and the planned correlated changes cannot be gated.
- Those changes are acc3 joining org AA and the Billing Transfer on 01/12, which flips every account at once (current-situation-model, "Các lần đổi payer / org"). Today that guard is a manual rule.

**W6 (Med). An account-level outage opens circuits one deployment at a time.**
- There is one circuit per deployment (`breaker.py:3-4`), so each deployment on a blocked connection needs its own failing real call. During a block lasting days, each one re-probes with a live job request about every ≤30 min (`breaker.py:14-16,101`).
- Nothing raises the outage to the connection level, and no availability alert fires from it.

**W7 (Med). Recovery after an outage is not designed.**
- Jobs that hit `LLMAccessDenied` fail at once and are not retried (`worker.py:112-117`), which is correct.
- But nothing re-queues them once the circuit closes, so recovery is manual SQL or a re-run.
- Job backoff is a fixed 30/60/120 s with no jitter (`queue.py:53-55`), so a wave's retries hit the provider at the same moment.

**W8 (Low-Med). Error classification is fragile.**
- Classes come from text regexes (`errors.py:42-77`). A Bedrock `ValidationException` that matches no deployment wording counts as a request error and is ignored by the breaker (`breaker.py:64-87, 368-380`).
- A new account-level refusal wording would therefore never open a circuit and never alert. Nothing pins the known refusal strings, such as tests using the real 29/10 messages.

**W9 (Low). The region and SCP order matters.**
- Every connection is in us-west-1. A second region comes only on a capacity trigger, which is right, because a region cannot save you from an account block (capacity plan §5.2).
- But the AA-1004 SCP region allow-list must include us-west-2 before the org move. Otherwise both the second region and the us-west-2-only models are blocked by policy at the moment they are needed.

## What the design gets right

- **Fails fast on account-level refusal.** `LLMAccessDenied` fails the job with no retries (`errors.py:18-21`; postmortem 29/10 23:47 probe).
- **Breaker state is shared.** It lives in the DB, with a single half-open probe lease, per-class thresholds and short open periods. It falls back to in-process if the DB is down and never raises on the call path (`breaker.py:1-33, 100-106`).
- **One bad payload cannot open a circuit.** Request errors are excluded (`breaker.py:59-63`).
- **No hidden or cross-vendor fallback.** Server-side `fallbacks` are off and every fallback is logged (blueprint :1285; ADR 0005 §4).
- **The limiter moves on.** `LimiterSaturated` sends the call to the next path without counting as a provider failure (`breaker.py:462-466`).
- **The capacity plan is sound.** It has the 429/503/529/spend-cap error taxonomy, a retry budget per chain, SLOs plus an error-budget policy that freezes waves, the rule "no payer/org change near go-live", and it defers Redis and multi-region until a trigger (§5.2, §5.7, §5.8).

## Proposed design changes (put them in ADR 0009 / AA-642; no route change)

1. **Make independent coverage an invariant.**
   - What: add `failure_domain` (payer/org, account, region, vendor) to connections. Each prod stage class must have at least one enabled, funded deployment in a different payer/org domain that its scopes allow, or an approved degrade mode (pre-written content / manual). Check it in CI and on the availability card.
   - Why: W1, W5.
   - Effort: M.
   - Depends on: ADR 0009 (AA-804, by 15/11), the AA-820 scope decision for T-series, a funded Anthropic key (admin).
2. **Scheduled canary per connection × enabled deployment, fallback-only rows included.**
   - What: daily on Dev, hourly on prod, a tiny prompt with stage `adhoc_canary`. It updates `llm_provider_health`, alerts on `access_denied`/`quota_exhausted`, and fires a burst before and after every payer/org change. Add `lifecycle_status`/`eol_date` columns, and use the canary to keep Legacy models warm.
   - Why: W2, W5, gap rows #15/#21.
   - Effort: S-M, about cents per day.
   - Depends on: a budget set on each connection (S10 data).
3. **Enforce the time and retry budget in the gateway.**
   - What: a per-request deadline passed through `_call_route` to each deployment, with a per-stage timeout (interactive is short). Build Bedrock clients from the connection's `timeout_s`/`max_retries`, standard mode, `total_max_attempts=1` on throttle, so the gateway owns retries. Cap total attempts per chain at 6 and honour `Retry-After`.
   - Why: W3.
   - Effort: S-M, code only.
   - Depends on: none.
4. **Classify the Anthropic 429 spend cap as `quota_exhausted`.**
   - What: read `error.details.error_code == enforced_spend_limit_reached` before the 429 → throttled rule. Pin the known refusal strings (Error 002, "not available for this account", Legacy refusal, both spend-limit forms) with fixture tests.
   - Why: correction 2, W8.
   - Effort: S.
   - Depends on: none.
5. **Separate connection lines and push backpressure into job claim (move S12 to AA-642).**
   - What:
     - separate dev / bulk / prod connection rows;
     - the claim query skips bulk kinds while any prod circuit is open or "bulk paused" is set;
     - limiter counted in estimated tokens (input + `max_tokens`), not only rpm;
     - each task's share = connection limit ÷ running tasks.
   - Why: W4.
   - Effort: M.
   - Depends on: S12 moved off the closed AA-1002.
6. **Escalate to a connection-level circuit.**
   - What: when 2 or more deployments on one connection open with an account-level class within N minutes, open every deployment on it. Recovery comes from the canary (change 2), not from live jobs.
   - Why: W6.
   - Effort: S.
   - Depends on: change 2.
7. **Recovery path.**
   - What: an admin action "re-queue `llm_access_denied` jobs since T for kinds K", shown once the circuit closes, with the wave guard respected. Add jitter to `backoff_seconds`.
   - Why: W7.
   - Effort: S.
   - Depends on: none.
8. **Monthly failover drill on Dev.**
   - What: disable the primary connection and check that each stage class reaches its fallback within the deadline, at a known cost. Record the result in the OPS-12 digest. Before go-live, add the SCP region allow-list check (us-west-2) to the AA-1004 acceptance.
   - Why: W1, W3, W9.
   - Effort: S.
   - Depends on: changes 1 and 3.

Source files read:
- /home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/shared/llm_client/breaker.py
- /home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/shared/llm_client/errors.py
- /home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/shared/llm_client/client.py
- /home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/shared/llm_client/bedrock_satellite.py
- /home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/shared/llm_client/adapters/anthropic_messages.py
- /home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/shared/jobs/queue.py
- /home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-31-S261-llm-capacity-plan/README.md
- /home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-31-S261-aws-bedrock-org-access/current-situation-model.md
- /home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-29-S258-aws-org-blueprint/README.md
- /home/nghiep/projects/AA-Ecosys/docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md

### Chi phí và chính sách dữ liệu

**Cost/governance and data-policy critique of the approved LLM gateway design (S261, read-only, CIS code at the checked-out tree)**

Overall, the design governs where data goes (whether it leaves AWS) and how much a connection costs per month. It does not govern three things the S261 research hits: which vendor's model gets the data, where AWS runs it, and the spend of evaluation runs. All S261 A/B and new-family work falls into those three gaps.

## Top weaknesses

1. **High. Spend identity is a free-text `account` value that call sites write, so connection budgets cannot see the paths new models would use.**
   - The monthly connection budget sums `llm_call_log` rows where `account = connection_key` (`shared/cost_guard.py:327-333`).
   - Native acc2 chat rows are written with `satellite_account=None` and no `connection_key` (`client.py:1376-1380`; `call_log.py:261-265`). So an acc2 or `acc2-usw2` budget can never trip.
   - Every connection's `monthly_budget_usd` is NULL (304 seed; capacity plan :232).
   - Ledger v2 (AA-804) has no `connection_key` or `deployment_id` column (gap table #18).
   - Why it matters: "budget per connection" (blueprint :1226, S10) cannot be enforced for the very A/B it is meant to protect.

2. **High. A data scope only answers "does the request leave AWS?". It does not cover which model vendor gets the data, where AWS processes it, or the model's licence.**
   - ADR 0012 §1-3 has two scopes, `aws_only` and `vendor_direct`. Kimi, GLM, DeepSeek and Qwen all pass as `aws_only` (candidates :51, :152).
   - The legal sub-processor list and DPA name only "Claude (Anthropic) and GPT models on Bedrock" (`docs/legal/register.md:252-253`; `dpa-template.md:85`). The privacy page still says "[to be confirmed]" (`register.md:298`).
   - `global.` profiles can process a prompt outside the US (`dpa-template.md:85`), and no policy controls that.
   - Licence terms are not modelled, for example Kimi's modified-MIT credit clause (candidates :169).
   - Why it matters: a tenant-stage route to Qwen would pass the gateway's policy and still break the terms (AA-820) and the AI Use Register (AA-804).

3. **High/med. Evaluation and ad-hoc spend run on the least-governed path.**
   - `adhoc_*` stages have no `allowed_scopes` row, so they get "no stage policy" and fall back to the pre-S5 rules (ADR 0012 §4; `data_scope.py:16`; `role_config.py:202`).
   - The `model_tier` eval call skips the writer/judge vendor rule (gap table #6).
   - Caps are constants inside each script, not DB budgets: `judge_compare` $5, `score.py` $15, R2 $10 per run / $25 per month (gap table #14).
   - The paid-run approval rule (cost estimate first, 3 tours, then at most 50) exists only in agent memory, not in the design.
   - Daily caps are opt-in per job kind. S1, T2, T8, T9 and A3 are not covered (capacity plan :112, :286).

4. **Med. Reasoning-token cost is invisible and unbudgeted.**
   - The Converse usage reader sums only input, output and cache tokens; there is no reasoning split (`client.py:290-293`).
   - Effort is read only by the Anthropic adapter (`client.py:1400-1403`). Converse sends no `additionalModelRequestFields`.
   - Kimi K3 defaults to effort `max` at $16.50 per 1M output tokens (candidates :61, :170).
   - Outputs cut off at `max_tokens` are billed but unusable (`client.py:1341-1345`). Two models hit this in the smoke test (candidates :53).
   - Why it matters: $/tour in the A/B mixes useful writing with thinking, and the per-run caps cannot be predicted.

5. **Med. Price data has weaker controls than scope data.**
   - The scope is migration-only (ADR 0012 §5). But `cis_app` has INSERT/UPDATE on catalog prices and `enabled` (schema ref, catalog grants).
   - `price_source` is free text, with no region, profile or effective date.
   - Prices differ by profile: Kimi costs $3.30 on `us.` and $3.00 on `global.`; regional profiles cost about +10% (blueprint :1247). Per-region overrides sit on deployments, which are migration-only.
   - `enabled_needs_price` stops a $0 price, not a wrong one.
   - The Price List itself has known errors (Nova Pro output, candidates :182).

6. **Med. The nightly reconcile cannot separate connections on the same account.**
   - Bedrock is reconciled per account and per service from Cost Explorer, so "connections on one account are compared together" (AA-1002.md S10 :25-27).
   - On acc2, the `acc2-usw2` A/B line, acc2 native chat and Cohere embeddings would all be one figure.
   - So the reconcile cannot confirm the A/B's logged cost, and cannot catch a single model's mis-price (#5).

7. **Med. There is no tenant or app ceiling in the CIS gateway.**
   - `spend_budget` works per provider and job kind. The "bedrock" daily figure is `provider LIKE 'bedrock%'` over every account and model family (`cost_guard.py` `_DAY_SPEND_SQL`).
   - `app` lives in `quality_signal` jsonb until AA-804 (DM-10.4; data-standards 02 :109, :156).
   - The tenant Content studio has no USD cap; one is proposed but not built (capacity plan :71-73, :258).
   - Only the CRM has a per-tenant `ai_budget_usd` that fails closed (ADR 0008a §5 :109-111).

8. **Low now, rising with S8. The CIS gateway has no automated PII guard.**
   - DM-6.4 relies on reviewing prompt builders and log lines. "No automated PII check exists or is on the roadmap" (data-standards 02 :226).
   - The CRM has a fail-closed scrub (ADR 0008a :109); CIS has none.
   - When TripPlanner moves onto `aa_llm` (S8), traveller `free_text` reaches the shared core, now with more vendors and `global.` routing.

## What the design gets right

- **The ledger is the single seam.** DM-10.4 makes every paid call go through the gateway into `llm_call_log`, enforced in CI (`test_aa685_no_raw_model_calls.py`).
- **A scope change is a reviewed migration, set per stage.** An admin toggle and per-model scopes were both rejected, with reasons (ADR 0012 Alternatives; §5).
- **Unknown prices are flagged and never charged as $0.** An unknown model is priced at Sonnet rates and marked "estimate" (`pricing.py:165-202`; ADR 0005 §7; `enabled_needs_price`).
- **A budget stop ends a job cleanly.** The connection budget's hard stop raises `stopped_budget` instead of retrying (`connection_budget.py:113-160`).
- **The reconcile is careful.** It reads gross usage split by record type, so credits are not netted in. The last 24-48 h are marked provisional. Vendor admin keys are read-only, in a narrow scope (S10 :25-63).
- **Cost always matches the model logged.** Claude API server-side `fallbacks` stay off and there is no silent cross-vendor fallback (blueprint :1285, :1431).
- **Aggregators are fenced off.** OpenRouter-type routes are emergency-only, `vendor_direct`, and never carry tenant data (table 7 :1307).
- **The CRM has the right order of checks:** scrub → budget → `ai_enabled`, and the CRM ledger stores no prompt text (ADR 0008a §5).

## Design changes I would propose

1. **Key spend by deployment, not by a free-text account.**
   - What: the gateway (not each call site) writes `connection_key` and `deployment_id` on every ledger row. Budgets and the reconcile read those columns. First, fix the acc2 `account=NULL` bug.
   - Why: weakness 1.
   - Effort: S for the fix, M for the columns.
   - Depends on: AA-642 (fix PR, before any paid acc2 call); AA-804 ledger v2 (add both columns to its list).

2. **Data-class policy v2, as an amendment to ADR 0012.**
   - What: deployments carry `model_maker` and `inference_geo` (`in_region`, `us` or `global`). Stages carry an `allowed_makers` / `allowed_geo` derived from the data class. Tenant and TripPlanner stages may use only makers listed in the register and DPA Annex 3. The admin refuses a route outside these lists (the same way as ADR 0012 §6).
   - Why: weakness 2.
   - Effort: M.
   - Depends on: catalog `family` column and vendor CHECK change (gap #5); ADR 0009 / AA-804; terms in AA-820; register row 252.

3. **Govern evaluation spend as data.**
   - What: `adhoc_*` and `eval_*` stages default to `{aws_only}` instead of NULL. Add `spend_budget` scopes `eval:*` (per run, per day, per month) that the harnesses read instead of their constants. Add an `eval_run` record with approver, cap, tour count and estimate, written before the first paid call. This turns the "estimate cost → 3 tours → at most 50" rule into a check.
   - Why: weakness 3.
   - Effort: S-M.
   - Depends on: AA-900 (runbook and harness PR).

4. **A reasoning cost model.**
   - What: add `reasoning_tokens` and `effort` to the ledger. Put effort and a `max_tokens` floor per stage × model family into route data, read by every adapter including Converse (`additionalModelRequestFields`) or a new api_style. Base the pre-call budget estimate on `max_tokens` × the output price. Add a "billed, unusable" metric for truncated outputs.
   - Why: weakness 4; also gap table #1 and #7.
   - Effort: M.
   - Depends on: a new AA-642 slice; AA-804.

5. **Price provenance.**
   - What: replace free-text `price_source` with structured fields: Price List SKU or URL, region or profile, `effective_date`, `verified_at`. Changing a price on an enabled model or switching `enabled` on writes `audit_log` and needs migration or second-person review. A monthly diff against a downloaded Price List (the API is free) flags drift.
   - Why: weakness 5.
   - Effort: S.
   - Depends on: the catalog-rows PR in AA-642.

6. **Reconcile per region and usage type.**
   - What: the Bedrock reconcile groups by `USAGE_TYPE` (which carries region and model) in the same single Cost Explorer call, and maps each line to a connection and deployment. Until that exists, give the A/B its own account × region line so it can be told apart.
   - Why: weakness 6.
   - Effort: S.
   - Depends on: S10 code; the cost stays one CE request per account (about $0.01-0.02).

7. **Tenant and app ceilings in the CIS gateway.**
   - What: a monthly `tenant_ai_budget_usd` that copies the CRM pattern. A real `app` column. Daily caps on by default for S1, T2, T8, T9 and A3, alert-only on Dev. Separate dev / prod / bulk connection lines so a hard stop hits chat only and not embeddings.
   - Why: weakness 7.
   - Effort: M.
   - Depends on: AA-804; capacity plan S12 (whose only home is the closed AA-1002, so it should move to AA-642); tenant pricing from the business owner.

8. **An automated PII guard before S8.**
   - What: reuse the CRM's F3 scrub (known values → placeholders, patterns, fail closed) as an optional gateway step for stages flagged `free_text`. Add a CI test that ledger columns carry no `pii:` data.
   - Why: weakness 8; it also closes the open point in DM-6.4.
   - Effort: M.
   - Depends on: S8 (≤13/12); ADR 0009.

**Order:** do 1 and 3 before any paid acc2 or us-west-2 A/B. Do 2 inside ADR 0009 (≤15/11) before any non-Claude, non-GPT model touches a tenant or TripPlanner stage. 4–7 fit in the AA-642 slice restatement and AA-804. 8 is gated on S8.

### Đánh giá và chất lượng nội dung

**LLM gateway design critique through the eval and English-content lens (read-only, CIS `1b6e9448`, 31/10/2026)**

**Short answer:** fidelity validators belong in the pipeline, not the gateway. The gateway owns the response contract: truncation, emptiness, schema validity, reasoning leakage and token accounting. It also tags every call with its family and path so fidelity rates can be split per model. The approved design has a sound eval idea: R2 gate, kappa bar, hard stop on a new hard-fact class, golden set. But it never says how a new model is qualified. Its main eval gate (S11 "Eval R2 đạt ngưỡng", blueprint :1381) cannot pass today.

Vietnamese plays no part: the golden set is `rewrite_language: "en-US"` (`scripts/aa729/select_samples.py:178`).

## Corrections to the gap table (row 22 and row 16)

- **A1/S1 already has deterministic code checks.** `services/quality/s1_checks.py:1-23` holds DAY_*, NUMBER_NOT_IN_SOURCE, NAME_NOT_IN_SOURCE, INCLUSION_CONTRADICTED and TEXT_TRUNCATED. They are "measurements, not gates", because "S1-first freezes new gates" (`s1_checks.py:22`, `s1_facts.py:26`, advisory Q2). So a new time-of-day rule has a natural home (s1_checks), and it hits a freeze the gap table did not mention.
- **The A1 clock rule misses 24-hour times.** `ITIN_CLOCK_TIME` requires am/pm (`content_generation/brand_audit_node.py:69`). "16:00" is never matched. "around 16:00 → by 16:00" also passes, because support is a plain clock-string compare (`:118-119`).
- **The taxonomy names the right class, but enforces nothing for A1 that catches this.** Class `other.f7` ("invented timing") is enforced for A1 only through ITINERARY_MEAL_TIME_INVENTED. F17 is wired only for T9 (`services/quality/taxonomy.yaml:293-295`).

## Top weaknesses

1. **HIGH: no procedure to qualify and promote a new model or family.** The design only gates moves between model generations of the same vendor (S11 :1381; S3 risk :1373), plus a golden-label check for Luna across paths (:1268). It has no steps from catalog row to probe to judge to writer A/B to shadow to route. Today's smoke ranking is one non-S1 prompt with no Sonnet control (`bedrock-writer-candidates/README.md:16-19, 50`). That is exactly the gap that let research run outside the design.
2. **HIGH: the eval gate the design relies on cannot pass.**
   - R2 counts the judge only at kappa ≥ 0.6 on ≥ 10 pairs; otherwise the run is "informative only… cannot pass" (`services/writing_memory/r2.py` docstring, step 0a).
   - The best judge is 0.562 on 13 pairs with `counts=False` (arch review B2, `README.md:213-215`; TL-10 :907).
   - All 20 thresholds are `calibrated: false` (`services/quality/thresholds.yaml`).
   - Golden labels come from an LLM panel (S245 D7=b, review B2).
   - The design lists S11's dependency as "R2 đạt ngưỡng" but never lists judge calibration or human labels as prerequisites.
3. **HIGH: R2 has no arm for a candidate model.**
   - The A1 arm calls `_rewrite_tour(..., model_tier=None)` (`writing_memory/eval_writers.py:133`), so it always runs the live `s1_generate` route.
   - A model A/B can only use a one-off `model_tier` script outside R2's kappa, noise and hard-stop machinery, or a live route change, which breaks "no route change".
   - R2 covers only `a1/t2/t9_blog/t9_social` (`eval_writers.py:209`). The 13 haiku stages S11 moves (flag_fix, nudge, repair, extract; blueprint :1277-1280, :1342) have no eval harness.
4. **HIGH: the judge-isolation rule checks vendor identity, against one arm only.**
   - `judge_compare.refusal` rejects only `vendor == "anthropic"` and hard-codes `ACCOUNT = "acc3"` (`scripts/aa919/judge_compare.py:51, 64-70`).
   - The admin rule is the same (`admin_llm_ops.py:180-183`).
   - In a GLM-vs-Sonnet A/B the grader must differ from both arms. The smoke test was graded by two Claude agents (`bedrock-writer-candidates/README.md:16-17`), which is self-preference risk once Sonnet is the control.
5. **MED: per-stage generation parameters live in code and env, not route data.**
   - `GENERATE_MAX_TOKENS = 8192` is a constant (`content_generation/graph.py:47`).
   - Writer temperature is env `S1_WRITER_TEMPERATURE` (`graph.py:512-518`).
   - Converse ignores `request_defaults` (`client.py:1402`; gap row 1).
   - So an A/B arm or a fallback path cannot carry its own effort, reasoning or max_tokens. The 8192 cap also equals the hard output limit of five candidates (`candidates README:127`).
6. **MED: the gateway accepts truncated output.**
   - Converse fails only on empty content (`client.py:1341-1345`). `stop_reason` is logged (`:275-281`) but never acted on.
   - Text extraction keeps only `text` deltas (`client.py` ~1329-1333). Inline `<think>` leakage is not detected.
   - A reasoning model that hits max_tokens with partial text goes downstream as success. Only `TEXT_TRUNCATED` in s1_checks, which is a measurement, would see it.
7. **MED: writer fallback across paths is treated as equivalent without evidence.**
   - Table 5 assumes "same model + same effort on every path" (:1277).
   - Review B3 shows paths differ in practice: the Anthropic adapter sends default effort with `request_defaults '{}'` (mig 306), and three real requests differed from intent (S224, S251, S10) (`architecture-review/README.md:232-234`).
   - The S261 Dev road (anthropic-direct for `s1_generate`) has no cross-path canary.

## What the design gets right

- **Writer/judge separation by vendor and eval-gated route switches.** ADR 0006 §5, ADR 0008, blueprint :1277-1279, :1381.
- **"Priced before enabled" and "trust only real calls".** ADR 0005 §7; :1247, :1293.
- **The R2 machinery is good.** It has a frozen control, a tune/holdout split, a stop on a new hard-fact class, a noise bound (`noise_k`), a $10 per-run / $25 per-month cap, and calls logged under the eval stage (`r2.py` docstring). The gap is coverage and calibration, not the method.
- **Shadow is A/B-only at 0% otherwise, with no shadow on failure.** ADR 0006 §3; `client.py:615-621`.
- **The ledger is the source of truth.** Every eval spend is traceable per run (`llm_call_log`, `bind_eval_stage`).
- **The design keeps content logic out of the gateway.** That is the right boundary; it should be stated explicitly.

## Proposed design changes

1. **Write the qualification and promotion ladder into ADR 0009 (AA-804).**
   - Steps: catalog row disabled and priced → access probe → contract smoke ($<0.10: schema validity, stop_reason, length) → judge-first calibration → R2 writer A/B against a frozen Sonnet 5.5 control → targeted shadow → route switch with one-edit rollback.
   - Pass bars: zero new hard-fact class; deterministic fidelity rate ≤ control; cost per tour and p95 latency reported.
   - Why: closes weakness 1. Effort S (docs). Depends on changes 2 and 3.
2. **Add a candidate-model arm to R2.**
   - `--model <key>@<connection>` threads `model_tier` into `_a1/_t2/_t9`, logs model family and path per item, and allows `goal=non_inferior` for a model swap.
   - Add a light-stage harness: frozen inputs for flag_fix, nudge and extract with deterministic pass criteria. S11 needs it.
   - Why: weakness 3. Effort M. Depends on the acc2 attribution fix (gap #10) and catalog `family` (gap #5).
3. **Make judge calibration an explicit prerequisite of S11 and of any writer change.**
   - A 40-item human label set (review B2/N3); a judge counts only at ≥ 30 pairs and ≥ 8 per class.
   - Calibrate the gpt-oss / Luna candidates there.
   - Why: weakness 2. Effort S plus about 2 hours of human labelling plus $1-5. Home: AA-900 (its scope already says "eval runbook", "model/route changes"); AA-919 is Done.
4. **Make the judge rule family-based and two-sided.** Judge family ∉ {control family, candidate family}, enforced in `judge_compare.refusal`, in R2, and in the admin rule. Drop the hard-coded acc3.
   - Why: weakness 4. Effort S. Depends on the `family` column; ADR 0009 amends 0006 §5 / 0008.
5. **Add deterministic fidelity rules in the pipeline, not the gateway.** Add to `s1_checks`:
   - TIME_NOT_IN_SOURCE, reusing trip_facts F17 `_TIME_RE` and the equivalences in `trip_facts.py:331-395`;
   - HEDGE_HARDENED ("around/about/approximately X" in the source becomes "by/before/at X");
   - unsourced vessel and view nouns ("junk", "under the stars", "vistas"), using the source fact table;
   - a 24-hour clock in `ITIN_CLOCK_TIME`.

   Run them first as R2 deterministic checks and measurement on the Sonnet baseline (this respects the gate freeze). Promote to `enforce` in the taxonomy after the baseline rate is known.
   - Why: the failures hit 6-7 of 16 models and are model-independent. They need source context the gateway does not have. Effort M. New A1 quality issue (ask the tech lead first).
6. **Define a gateway response contract with per-family flags.**
   - `stop_reason=max_tokens` becomes a classed `truncated` outcome; stage policy chooses retry or fail.
   - Detect inline reasoning leakage.
   - Log a schema-validity flag and `reasoning_tokens`.
   - Read `capabilities` for forced_tool / structured_output / thinking_mode.
   - Why: weakness 6; gap rows 7 and 8. Effort M. Home: AA-642 slice, with AA-804 for the ledger columns.
7. **Move per-stage parameters into route and deployment data.**
   - `max_tokens` floor, temperature, and effort/reasoning per family move from `graph.py` constants and env into data that Converse also reads (`additionalModelRequestFields`).
   - Every path and every A/B arm then sends identical parameters.
   - Why: weakness 5. Effort M. Depends on change 6 (capabilities).
8. **Add a cross-path canary before enabling a new path for any writer or judge stage** (review B3a): about 5 items per writer and 20 per gate judge, verdict flips ≤ noise, run ID in audit_log. Run it first for the S261 anthropic-direct `s1_generate` path.
   - Why: weakness 7. Effort S. Depends on change 2.
9. **Put length and format compliance on the scorecard as deterministic metrics.**
   - Use the real S1 rules, not the 110-130-word probe band: per-day targets from `parse_source_day_word_counts` (`content_generation/prompts.py:54`; nudge in `flag_fix_node.py:339-363`), META_LENGTH, TEXT_TRUNCATED, and output size against each model's 8K cap.
   - Why: about half the smoke models missed length (`candidates README:123`), and an 8K cap can cut S1 JSON. Effort S. Depends on change 2.

## Issue homes

| Change | Home |
|---|---|
| 1 | ADR 0009 / AA-804 |
| 2, 3, 9 | AA-900 (extend the scope; it already covers eval runbook plus model/route change) |
| 4 | ADR 0009 plus a harness PR under AA-900 |
| 5 | New A1 fidelity issue; ask the tech lead before creating it |
| 6, 7 | AA-642 new slice; ledger columns in AA-804 |
| 8 | AA-642 canary slice |

None of these changes routes. Changes 1, 3 and 4 should be decided before any paid writer A/B.
