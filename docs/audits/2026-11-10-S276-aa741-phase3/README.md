# AA-741 phase 3: T-series per-mechanism audit (S276, 10/11/2026)

Report for the tech lead. It closes the measurement part of AA-741: the T-series chain (T0 brief → T2 rewrite → T3 QA →
T5 atoms → T7 slate → T8 angle → T9 write → T10 gates → export) ran on 4 synthetic audit tenants × 12 shared tours in
phase 2 (S275), and this report reads that run per stage and per mechanism, with the same layout as the S218 A-series
audit (`../2026-10-08-S218-a-series-pipeline-audit.html`).

Earlier records: phase 0 `../2026-11-05-S270-aa741-phase0/README.md`, phase 1 `../2026-11-06-S271-aa741-phase1/README.md`,
phase 2 `../2026-11-10-S275-session/aa741-phase2/` (`status.txt`, `holds.txt`, `spend.txt`).

Public-repo rules applied: no account IDs, ARNs, secrets, e-mail addresses, tenant personal data, or tour / piece text.
Tours, pieces, jobs and versions are named by their first 8 hex characters. The 4 tenants are the synthetic audit
tenants `audit-atlas-hearth`, `audit-terra-family`, `audit-trail-pulse` and `audit-wildkind-travel` (short: atlas, terra,
trail, wildkind).

---

## Contents

1. [Summary](#1-summary)
2. [How to read the evidence](#2-how-to-read-the-evidence)
3. [Reconciliation](#3-reconciliation)
4. [Per stage](#4-per-stage)
5. [Brand](#5-brand)
6. [Market](#6-market)
7. [Ops](#7-ops)
8. [Cost](#8-cost)
9. [Mechanism table](#9-mechanism-table)
10. [Roadmap](#10-roadmap)
11. [Portal UI list](#11-portal-ui-list)
12. [Follow-up issue proposals](#12-follow-up-issue-proposals-not-created)
13. [Open checks](#13-open-checks)
14. [Method and inputs](#14-method-and-inputs)

---

## 1. Summary

1. **Blog holds come from length, and the writer is the cause, not the band.** 20 of 28 Blog pieces are held (71.4 %);
   13 holds carry F4 (the blog length gate, 4,700–13,000 chars), and all 13 are *too short*, by a median of 912 chars
   (`o1 PIECES`, `o1 SUM_F4`, `o4 HELD_SHARE P2`). The writer asks itself for 900–1,300 words (≈ 5,245 chars, above the
   F4 floor) but lands under 900 words in 25 of 28 pieces (`o1 HDR`, `o1 SUM_LEN`). Length follows the seed size
   (r = 0.424), not tour days (r = 0.098) (`o1 SUM_DRIVERS`). F4-headed holds take 1.8645 USD, 65 % of held spend
   (`o4 HELD_HEAD P2`).
2. **The repair for a short piece is the wrong tool.** A short F4 is repaired by a full rewrite. 18 pieces got one: F4
   was fixed on 6, 9 of 18 rewrites added a new hold gate, 5 got shorter or stayed the same, and only 2 of the 18
   ended approved. The 22 second `t9_write` calls cost about 1.02 USD (derived) (`o1 SUM_ATTEMPTS`, `o1 SUM_FIRST_FINAL`,
   `o4 STAGE P2 t9_write`). An *extend repair* (add the missing words from unused seed facts) is the proposed
   replacement. Upper bound if the 9 F4-only holds pass: approved 7 → 16 of 28, USD per approved blog 0.5467 → 0.2392
   (derived).
3. **Text is shortened after F4 has measured it.** The post-loop normalizer (AA-1047) runs after the gates and F4 is not
   run again. In 10 of 13 F4 holds the stored text is 192–557 chars shorter than the F4 reading; 3 of 7 *approved* pieces
   are stored under the 4,700 floor while their ledger says F4 passed (`o1 PIECE … LEN`, `o1 SUM_LEN f4_side_all`).
4. **Ops hides two failures.** One piece (`e16fbbfb`) failed after a complete writer reply, under a `t9_write` job that
   reports *succeeded*, with no error class and no retry (`o1 FAILED`). And `t2_flag_fix` (the targeted brand-fix call)
   now runs on Haiku 5.5, a reasoning model, with the 4,096-token default: 4 of 6 calls were cut, and in 1 of 3 jobs the
   fix was silently lost while the job reports `passed` / 10.0 (`o2 FLAGFIX_CALL`, `o2 FLAGFIX_JOB`). `shared.job.cost_usd`
   is 0.0 on every job while the ledger holds 6.77 USD (`o4 KIND P2`).
5. **Brands read differently, but the brand judge does not measure it.** On the 8 really rewritten tours two brands
   share on average 18 % of their 5-word sequences (derived from `o3 T2_SIM`), and no page leaks another brand's name
   (`o3 T2_LEAK`, `o3 BLOG_LEAK`). Yet the brand-fit judge scores 5.88–6.25 (below the 7.0 pass line) while the stored
   score is 9.91–10.0, the judge's `cross_brand_distinct` is near constant (5.75–6.0), and the brand's core idea is found
   in only 5 of 32 versions (`o3 T2`). The T0 .docx import leaves `system_prompt`, `default_cta` and signature words
   empty on 4 of 4 brands (`o3 BRAND`).
6. **Unfamiliar markets are dropped without a word.** Atlas loses 4 of 6 declared markets and Terra its first 3; the
   AA-629 banner and the unmapped-market record fire only when *no* market is supported, so both are empty for 4 of 4
   (`o3 MARKET`). There are 0 data rows for AE/SA/SG/HK/CA/NZ (`o3 DEMAND_ABSENT`). T2 picks one SEO market by global
   rank, so the two "Europe first" brands get US keywords on 8 of 8 versions (`o3 MARKET t2_market_is_first=false`).
7. **T7 Debate does not discriminate.** It flags 499 of 502 free Blog candidates (every one in 41 of the 44 pairs that had any), so the
   50 % cut cap, not judgement, decides what is dropped (Σ `o1 PAIR`). 6 pairs got no Blog subject: 4 because one
   Mongolia tour clears the demand bar in no market although its place terms carry demand, 2 for a cause not yet seen
   (`o1 SUM_PAIRS`).
8. **Cost is now set by the hold rate, not by call prices.** Phase 2 spent 6.7747 USD (AA-741 total 13.3341 of the
   approved 20 USD) (`o4 TOTAL P2`, `o4 RECON`). A Blog piece costs 0.1367 USD, −69.5 % against phase 1; call waste fell
   from 20.2 % to 1.7 % (`o4 COMPARE_UNIT`, `o4 WASTE`). But an *approved* blog costs 0.5467 USD and, at today's hold
   rate, the Growth plan's 40 USD cap pays for only 73 approved blogs a month (`o4 PROJECTION`). Prompt caching is off on
   every Anthropic stage (`o4 STAGE P2 cache_write=0`).

Verdicts over the 56 mechanisms in the merged table (§9): 26 keep (2 of them to verify), 23 adjust, 3 split keep/adjust,
4 not fit (judge `cross_brand_distinct`, the AA-629 banner for partly unsupported markets, T7 Debate cut, full rewrite as
the short-length fix).

---

## 2. How to read the evidence

- `o1`…`o4` are `data/out_1.txt` … `data/out_4.txt` in this folder, printed by `scripts/p3_1_holds_deep.py`,
  `p3_2_stage_ops.py`, `p3_3_brand_market.py` and `p3_4_cost.py`. Each number cites the output line key, for example
  `o2 JOB_KIND t7_slate`. A per-piece line is cited as `o1 PIECE <id8> <sub-line>` (LEN, ATT, REP, CODES, SEED, LLM, DISC).
- "Σ o1 PAIR" means a sum over the 48 `PAIR tenant=` lines of `o1`; no script prints that sum.
- "(derived)" marks arithmetic on cited numbers; it is not a separate measurement.
- "code:" points to `apps/AA-CIS-App` at `5cc016cde` (source of the "designed for" column).
- **Stored chars** = stored `content_text` with citation tags stripped (the `LEN` line). **F4 chars** = the number inside
  the F4 violation on the piece's own gate ledger (`f4_ledger=` and `ATT`). `quality_gates.gate_extreme_length` measures
  the same tag-stripped text, so a gap between the two means the text changed after the gate ran (§4.5.4).
- Measurement window: 2026-11-10 05:49:46Z to 10:23–10:25Z (`o2 SUMMARY_JSON window`, `o4 TOTAL P2`). Synthetic test pieces
  in the window: 0 (`o2 TEST_EXCLUDED`); piece `d67e3178` is excluded by id (`o4 TENANTS exclude8`), per the S238 rule.

### Glossary

| Term | Meaning |
|---|---|
| T0 … T10 | Tenant pipeline stages: T0 brand brief, T2 tour rewrite, T3 QA, T4 pool, T5 atoms/Segments, T7 slate (topic list), T8 angle, T9 write, T10 gates |
| Segment | A ranked piece of a tour route that can carry a Blog topic; one Segment can cover several tours |
| Blog Bar | T7 demand rule for Blog: demand ≥ 1,000 and questions ≥ 3 (code: `services/acp_shared/slate.py CHANNEL_BARS`) |
| Debate | T7 judge pass that flags off-brand or contested candidates; cut capped at 50 % (code: `debate.py MAX_CUT_FRACTION`) |
| Seed | The fact pack (route moments, walk focus, FAQ pairs) the T9 writer gets |
| F4 | T10 length gate (`F4_extreme_length`) |
| F9 / F13 / F15 / F17 | T10 gates: CTA and claim facts / leaks and repeats / voice rules / trip facts |
| Held | Piece delivered to the tenant but not publishable as is (the "tenant sees content only" rule) |
| Stop-and-label | AA-900 W0 / ADR 0020 D6: no paid attempt 3; the piece is held with typed reason codes |
| Ledger | `shared.llm_call_log` (non-shadow) and `shared.dfs_call_log` |

---

## 3. Reconciliation

### 3.1 Corrections to the S275 records

| S275 statement | What the phase 3 outputs show | Evidence |
|---|---|---|
| "Blog, 42 pieces with a subject: 9 approved, 32 held, 1 failed" | Those are pair-weighted counts. 7 of the 28 pieces sit on Segments that each cover 3 tours (two tour sets: 56b61f58/8602c1d4/a8560125 and 7fe02d1a/ac574bfe/b56704c5), so 28 distinct pieces show as 42 tour × tenant links. Distinct pieces: **28 = 20 held, 7 approved, 1 failed**. The later S275 comment already used 28. | `o1 PIECES`, `o1 SUM_DRIVERS tours_per_piece={3:7,1:21}`, `o2 FUNNEL` (t9_blog_piece 10+11+11+10 = 42) |
| "t2_flag_fix runs at max_tokens 4" | 4 is a row count: 4 of 6 t2_flag_fix rows ended on `stop_reason=max_tokens`. The request ceiling was 4,096. | `o2 SUMMARY_JSON llm_stage.t2_flag_fix max_tok=4 n=6`, `o4 STAGE P2 t2_flag_fix`, `o2 FLAGFIX_CALL` |
| "3 of the 6 escalations are on one tour (a8560125, every tenant but one)" | 4 of 6: a8560125 is escalated for all 4 tenants (elephant-riding policy hold). | `o2 PAIR` × a8560125, `o3 T2_NR` (4 rows `fc=policy_hold`) |

### 3.2 Stage funnel (T0 to export)

Expected: 4 brands × 12 shared tours = 48 tenant × tour pairs. The 3 phase 1 tours (2cf487be, 84e392c3, caf4bf16) kept
their phase 1 T2 versions, so 36 versions are new in the window (`o2 FUNNEL t2_version_in_window=9` per tenant,
`o3 T2_SCOPE versions=36`).

| Stage | Expected | Got (pairs) | Got (distinct objects) | Open | Evidence |
|---|---|---|---|---|---|
| T0 brand | 4 active brands | 4/4 active, version 2 | `system_prompt_len=0` and `cta_len=0` on 4/4; style guide 1,043–1,176 chars; forbidden 10–15; voice examples 7 | – | `o2 T0_BRAND` ×4 |
| T0 markets | saved | `tenant_config.markets=None` on 4/4; normalised countries live in `seo_target_market` | – | – | `o2 T0_MARKETS`, `o3 MARKET` |
| T2 version | 48 | 48 | 36 new + 12 from phase 1 | 0 pending | `o2 FUNNEL t2_ok`, `o2 TERMINAL versions_pending=0` |
| T3 QA | 48 | 42 passed / 6 escalated | window: 30 passed / 6 escalated | – | `o2 FUNNEL t3_passed`, `t3_escalated` |
| T4 pool | 48 | 48 | – | – | `o2 FUNNEL t4_pool` |
| T5 atoms | 12 tours | 12/12 | 35–95 active atoms; 18–55 Segments per tour | – | `o2 T5_TOUR`, `o2 SUMMARY_JSON t5` |
| T7 Blog Bar cleared (any market) | 48 | 44 | 607 of 1,584 Segment × pair rows | – | `o2 FUNNEL blog_bar_any_market`; Σ `o1 PAIR` |
| T7 Blog Subject | 48 | 42 | 28 used Blog Subjects (7/6/8/7); 131 proposed | – | `o2 FUNNEL t7_blog_subject`, `o2 T7_SUBJECTS` |
| T8 angle request | – | 42 | 28 requests, all approved, 3 options, 1 chosen | 0 `pending_goal` | `o2 T8_REQ`, `o2 T8_OPTIONS`, `o2 TERMINAL` |
| T9 piece | – | 42 | 28 | 0 processing | `o2 FUNNEL t9_blog_piece`, `o1 PIECES`, `o2 TERMINAL` |
| T10 terminal | – | 41 + 1 failed | 20 held, 7 approved, 1 failed | – | `o2 FUNNEL t10_blog_terminal`, `o2 T9_PIECES` |
| Export, Blog | – | 41 | 27 pieces × 3 formats (HTML document, HTML fragment, text); held pieces exported, the failed one not | – | `o2 EXPORT content_piece.exported` (7/6/8/6) |
| Export, T2 DOCX | – | 36 | 36 versions, 9 per tenant, including the 4 policy holds | – | `o2 EXPORT tenant_tour_version.exported` |
| Jobs / waves | 0 open | 0 open | – | – | `o2 TERMINAL jobs_open=0` |

Every stage that ran reached a terminal state. 6 pairs have no Blog piece (§4.3.3).

**Script artefact, not a gap.** `o2 FUNNEL blog_bar_tenant_market=0` for trail is a script bug: `p3_2` compares the brand's
market *names* (Europe, North America) with ISO codes. `o3 MARKET` shows trail's markets normalised correctly, its slate
cleared 79 Blog Segments and produced 11 subjects (`o3 MARKET_SLATE`, `o2 FUNNEL t7_blog_subject=11`).

### 3.3 Cost reconciliation

| Check | Value | Evidence |
|---|---|---|
| Phase 2 chain spend | 6.7747 USD, 1,612 calls | `o4 TOTAL P2` |
| DataForSEO (DFS) spend, P1 and P2 | 0.0000 USD, 0 calls (research cache only) | `o4 TOTAL dfs_usd`, `o4 DFS_TENANT` |
| Rows with no tenant / unattributed spend | 0 / 0.0000 | `o4 TOTAL P2 gap_usd`, `o4 WASTE P2`, `o2 LLM_NOJOB` |
| Job kinds sum to the chain total | 2.8059 + 0.1416 + 1.1208 + 2.7065 = 6.7748 ≈ 6.7747 | `o4 KIND P2` (derived) |
| Per-piece `t9_write` sum = stage total | 2.3092 vs 2.3093 | `o1 PIECE … LLM` (derived); `o4 STAGE P2 t9_write` |
| AA-741 total against the approved 20 USD | 13.3341 (66.7 %), 6.6659 left | `o4 DAY`, `o4 RECON aa741_total_ledger` |
| Phase 2 run cap | 6.7747 of 13.44 spent | phase 2 `spend.txt SPEND_TOTAL` |
| P1 window vs the phase 1 README total | 4.3454 vs 3.6671 (+0.6783): the P1 window runs to 07/11 00:00Z and includes 06/11 runs made after the README; not split by run | `o4 RECON p1_window_minus_readme` |

---

## 4. Per stage

### 4.1 T0 brand intake and markets

| Field | atlas | terra | trail | wildkind |
|---|---|---|---|---|
| Brand pack version | 2 | 2 | 2 | 2 |
| Style guide (chars) | 1,045 | 1,052 | 1,043 | 1,176 |
| Voice words / forbidden list | 7 / 15 | 7 / 10 | 7 / 11 | 7 / 13 |
| core_idea, good_examples | yes, yes | yes, yes | yes, yes | yes, yes |
| **system_prompt / default_cta** | **no / no** | **no / no** | **no / no** | **no / no** |
| Explicit signature words | 0 | 0 | 0 | 0 |
| Derived signature words | 1 ("luxury") | none | none | none |
| Rewrite language / declared markets | en / 6 | en / 5 | en / 4 | en / 5 |

Source: `o3 BRAND`, `o2 T0_BRAND`. The .docx import fills the voice fields and leaves `system_prompt`, `default_cta`
and explicit signature words empty on 4 of 4. T2 still loads the brand on 36 of 36 versions (`o2 JOB_RESULT brand_loaded`).
Market normalisation (regions → ISO, AA-629) is correct on 4 of 4 (`o3 MARKET normalized_countries`); `tenant_config.markets`
stays None (`o2 T0_MARKETS`).

### 4.2 T2 rewrite and T3 QA (36 phase 2 versions)

| Measure | Value | Evidence |
|---|---|---|
| Status | 30 ai_generated, 6 needs_review (all `qa_status=escalated`) | `o2 JOB_RESULT version_status`, `qa_status` |
| Orchestrator | `t2-linear-1` on 28 jobs, resumed 0; the 4 trial jobs on 8602c1d4 ran the graph path (`t3.graph_*`, n=4) | `o2 JOB_RESULT t2_orchestrator.*`, `o2 FLAGFIX_JOB` |
| Draft chosen | initial 30, field_regen 2; sentence repairs 0 | `o2 JOB_RESULT t3.chosen_via`, `t3.sentence_repairs` |
| QA score (validate) | mean 9.954, p50 10.0 (pass line 7.0) | `o2 JOB_RESULT score`, `o3 RUN t2_pass_line=7.0` |
| Brand-fit judge (report only) | per-tenant mean 5.88–6.25, min 4.0 | `o3 T2` |
| Final contract | `sha_match` 32/32; `agrees` 31/32; 1 flip to unpublish | `o2 JOB_RESULT final_contract.*` |
| SEO | `tenant_market` 32/32; market US 24 / UK 8; keywords 10 in → 5 kept every job; language-blocked 0 | `o2 JOB_RESULT seo_source / market / seo_keywords.*` |
| Facts / writing release | `facts.mode=off` 36/36; `writing_release.tenant` null 32/32 | `o2 JOB_RESULT` |
| Brand precheck `ITINERARY_MEAL_TIME_INVENTED` | 5 of 9 versions per tenant (20/36); never a chosen (blocking) code | `o3 T2_CODES` |
| Length | mean 1,657–1,807 words per tenant (min 920, max 2,486) | `o3 T2_LEN` |
| Cost | 0.0782 USD per job p50 (p90 0.0966) | `o2 JOB_LLM t2_rewrite` |

**Why the 6 escalated versions need review**

| Tenant × tour | Reasons | Chosen code / final contract | Budget | Run | Evidence |
|---|---|---|---|---|---|
| all 4 × a8560125 | `policy_hold`, `score_below_pass_line`, `qa_escalated_no_chosen_codes` | – / `policy_hold`, `ELEPHANT_RIDING`; review queue `policy:elephant_riding` 3 per version | 0 LLM calls | 0–1 s | `o3 T2_NR`, `o2 JOB_RESULT policy_hold.*` |
| trail × 207e4efa | `t3_enforce_codes` | `T2_DAY_COUNT_VS_MASTER` / `needs_review` (`T3_STRUCTURAL`) | writer 2/2, repair 0/3, 0.179 of 0.25 USD; score 9.63 | 88 s | `o3 T2_NR`, `o2 PAIR` |
| trail × 7fe02d1a | `t3_enforce_codes` | same | writer 2/2, 0.110 of 0.25 USD; score 9.63 | 60 s | `o3 T2_NR`, `o2 PAIR` |

The policy hold behaves as designed: the 4 brands get the source text unchanged (5-gram Jaccard 1.0, 0.98 copied from the
Master) at 0 LLM cost (`o3 T2_SIM tour=a8560125`). Both day-count escalations are on trail only and appear after the
writer budget was spent. The 3 `needs_review/passed` pairs in the latest-version view are phase 1 versions and are not
measured here (`o2 PAIR t2_versions_in_window=0`).

**Why brand fit never changes the status.** On the linear path the judge makes one report-only call per version and the
stored score is validate's score (code: `t2_orchestrator.py` docstring L1/L3). 34 judge calls cost 0.0221 USD
(`o4 STAGE P2 t2_judge`).

### 4.3 T5 atoms and T7 slate

#### 4.3.1 Blog Bar and Debate over all 48 pairs (Σ `o1 PAIR`)

| Segment rows | Cleared | Below bar | Few questions | No data | Cleared, no seed atom | Place held (one piece per place) | Thin walk | Free | Free and Debate-flagged |
|---|---|---|---|---|---|---|---|---|---|
| 1,584 | 607 | 686 | 184 | 107 | 19 | 59 | 27 | 502 (405 places) | **499 of 502**; every free candidate in 41 of the 44 pairs with any (the other 3 pairs: 1 unflagged each) |

Debate flags almost every free candidate, so the 50 % cap (code: `debate.py MAX_CUT_FRACTION = 0.5`) decides what is cut.
The S231 pilot showed the same (49–54 of 60 flagged; `../2026-10-12-S231-t-series-pilot.md`). Debate's brand-fit cut uses the 7.0 pass line (code:
`services/quality/thresholds.yaml t7.brand_fit_cut ref: pass_line`), and the served (fallback) judge scores brand fit
below 7 on T2 too (§4.2). A scale mismatch would explain both; this is a hypothesis, since the Debate cache scores are not
in the outputs.

#### 4.3.2 Slate jobs

12 of 12 slate jobs succeeded, no 504 (the S231 pilot reason for moving slate to a job), but run time is p50 232 s, p90
428 s, max 453 s (`o2 JOB_KIND t7_slate`). Each tenant's 3 slate jobs re-read every Segment: `segments_seen` 60–63 → 142–146 → 183–186,
Blog proposals 7–8 → 21–30 → 29–40 (`o1 T7JOB`). Debate made 305 judge calls per tenant, 1,220 in total, 0.1416 USD
(`o2 LLM_STAGE t7_debate_judge`, `o4 STAGE P2`).

#### 4.3.3 Pairs with no Blog Subject (6 of 48)

`o1 SUM_PAIRS nosubj=6 reasons={'bar_miss': 4, 'no_proposed_subject': 2}`; none had a piece before the window.

| Pair | Reason | Segments | Bar status | Free | Debate-flagged | Evidence |
|---|---|---|---|---|---|---|
| atlas × caf4bf16 | bar_miss | 22 | below_bar 16, few_questions 5, no_data 1 | 0 | – | `o1 PAIR` |
| terra × caf4bf16 | bar_miss | 22 | below_bar 20, no_data 2 | 0 | – | `o1 PAIR` |
| trail × caf4bf16 | bar_miss | 22 | below_bar 17, few_questions 5 | 0 | – | `o1 PAIR` |
| wildkind × caf4bf16 | bar_miss | 22 | below_bar 17, few_questions 5 | 0 | – | `o1 PAIR` |
| atlas × 84e392c3 | no_proposed_subject | 24 | cleared 2, below_bar 14, no_data 5, few_questions 3 | 2 (2 places) | 2/2 | `o1 PAIR` |
| wildkind × 84e392c3 | no_proposed_subject | 24 | same | 2 (2 places) | 2/2 | `o1 PAIR` |

- **caf4bf16 (Mongolia, 15 days, 52 atoms).** No Segment clears the Bar in any of the 6 markets: the best has 1,300
  demand (US) and at most 4 questions (`o2 T5_SEG tour=caf4bf16`). Yet the tour's place terms carry a US top-volume sum of
  201,240 (`o3 PROBE tour=caf4bf16`). Either the place → Segment demand join is too narrow for this tour, or it is
  niche at Segment level; open. The tenant is not told why the tour has no Blog topic.
- **84e392c3 (Bhutan).** 1–2 Segments per market clear the Bar (`o2 T5_SEG`). terra and trail each got one Subject
  (approved / failed piece). For atlas and wildkind both free candidates are Debate-flagged and no Subject was proposed.
  A cap-only cut would leave 1 of 2, so a later slate step (rank order or proposal size against higher-demand tours)
  likely dropped them; not verified. Next check ($0, read-only): the two tenants' `t7_slate` job results for those
  Segment ids.

### 4.4 T8 angles

28 of 28 requests succeeded, 3 angles each, 1 chosen; 30 calls, all `end_turn`, 0 max_tokens: the phase 0 ceiling fix
(CIS #1330) holds (`o2 T8_OPTIONS`, `o2 LLM_HEALTH t8_angle_gen`). Cost 1.1208 USD, about 0.040 USD per request; cost per
call +37 % against phase 1, average output 1,986 → 2,827 tokens (`o4 STAGE P2 t8_angle_gen`, `o4 COMPARE_STAGE`). All 28
requests used one goal, `introduction_awareness` (`o2 T8_REQ`), so the other goals were not exercised.

### 4.5 T9 write and T10 gates (28 Blog pieces)

#### 4.5.1 Outcome

| Measure | Value | Evidence |
|---|---|---|
| Blog pieces | 28: 20 held, 7 approved, 1 failed | `o1 PIECES` |
| t9_write jobs | 28 ok, 0 failed, 0 retried; run p50 143.0 s / p90 164.4 s | `o2 JOB_KIND t9_write` |
| Held by first reason | F4_extreme_length 13, F17_trip_fact 5, F13_repeat 2 | `o4 HELD_HEAD P2`; phase 2 `holds.txt` |
| Final hold sets | F4 alone 9; F17 alone 4; F13+F4 2; F13 alone 1; F17+F9 1; F13+F17 1; F17+F4 1; F4+F9 1 | `o1 SUM_FIRST_FINAL final_sets` |
| F4 holds short / long | 13 / 0; stored text 78–1,486 chars under the floor (median 912) | `o1 SUM_F4` |
| Attempts | every held piece stopped at attempt 2 (`{2: 20}`); no paid attempt 3 (`last_attempt_mode=stop_and_label`) | `o1 SUM_ATTEMPTS`, `o1 HDR` |
| Held per tenant | atlas 4 (F4 3); terra 4 (F4 1); trail 5 + 1 failed (F4 5); wildkind 7 (F4 4) | `o2 T10_HOLD` |
| Reached the tenant (export) | 27 of 28 | `o2 EXPORT` |

#### 4.5.2 Length: gate band against the writer's target

| Setting | Value | Where | Evidence |
|---|---|---|---|
| F4 blog band | 4,700–13,000 chars, tag-stripped, per channel only (tour length and angle play no part) | `quality_gates._BLOG_MIN_CHARS/_BLOG_MAX_CHARS` (AA-531) | `o1 HDR` |
| Writer target | 900–1,300 words (max 1,600), including the FAQ | `prompts._BLOG_WORDS/_BLOG_WORDS_MAX` (S271 length-and-effort block) | `o1 HDR` |
| Chars per word | median 5.8 (5.54–6.15) | – | `o1 SUM_LEN cpw` |
| Writer floor in chars | ≈ 5,245 | 900 × 5.8 | `o1 SUM_LEN chars_at_writer_floor` |
| F4 floor in words | ≈ 810 | 4,700 / 5.8 (derived) | – |
| Over-long trim / rewrite targets | 12,500 / 12,000 chars | `length_trim` (AA-984) | `o1 HDR` |

The two floors are about 10 % apart, in two units, in two files, linked only by a comment. The `prompts.py` comment also
says F4 counts "tags included", but the gate strips tags first (`run_quality_gates`, `length_check_text`).

| | n | Words min / median / max | Stored chars min / median / max | Evidence |
|---|---|---|---|---|
| Held | 20 | 546 / 714.5 / 901 | 3,214 / 4,136 / 5,098 | `o1 SUM_LEN` |
| Approved | 7 | 749 / 824 / 1,082 | 4,426 / 4,859 / 6,210 | `o1 SUM_LEN` |
| F4 holds | 13 | 546 / 652 / 775 | – | `o1 SUM_F4` |
| F4-only holds | 9 | 546 / 624 / 775 | – | `o1 SUM_F4_ONLY` |

- **The writer misses its own floor.** 25 of 28 pieces are under 900 words; even the approved median (824) is under
  (`o1 SUM_LEN writer_side`).
- **Most first drafts are already short:** F4 short on 18 of 28 at the first check (`o1 SUM_FIRST_FINAL first_f4_side`).
- **The S271 block fixed the long side and pushed drafts short.** Phase 1 t9_write: 6 max_tokens stops, 3,054 average
  output tokens; phase 2: 0 and 2,172 (`o4 STAGE P1/P2 t9_write`).
- **Length follows the seed, not the tour:** r(seed words, words) = 0.424, r(days) = 0.098, r(atoms) = 0.176
  (`o1 SUM_DRIVERS`). By the `SEED` line of each piece (derived): seed ≤ 991 words → 9 of 12 held on F4, 1 approved; seed
  ≥ 1,210 words → 4 of 15 held on F4, 6 approved (the failed piece has no seed record and is left out). A 146-word seed
  (route_moments=0, walk_focus=0; a Segment covering 3 LK tours, one Subject per tenant) produced 4 pieces: 3 F4 holds (da055040, d16dfc5b, ebfcc20e) and c6cc3a29 (901 words, held on F17 pace_promise
  and F9 trip_promise). The 4 pieces on tour c9716429 (seed 936) were all held on F4.

#### 4.5.3 The 13 F4 holds

| Piece | Tenant | Stored chars | F4 chars (ledger) | Words | Seed words | a1 F4 → a2 F4 | Text kept | Other final holds |
|---|---|---|---|---|---|---|---|---|
| cda38200 | terra | 4,289 | 4,586 | 746 | 936 | in (4,915) → short 4,586 | a2 | – |
| da055040 | atlas | 3,436 | 3,947 | 579 | 146 | 4,175 → 3,947 | a2 | F13_repeat |
| a6e7e93f | atlas | 3,788 | 4,090 | 652 | 493 | 4,090 → 4,466 (+F17) | a1 | – |
| 37e97e7e | atlas | 3,214 | 3,448 | 546 | 936 | 4,524 → 3,448 | a2 | – |
| d16dfc5b | wildkind | 3,261 | 3,818 | 547 | 146 | 3,818 → 4,295 (+F13, F1, F9) | a1 | – |
| b08b585c | wildkind | 3,459 | 3,759 | 572 | 1,995 | 3,759 → 3,802 (+F13, F16, F17, F9) | a1 | – |
| 6a2ecc16 | wildkind | 3,579 | 4,083 | 624 | 936 | 4,532 → 4,083 | a2 | – |
| dc07bc6a | wildkind | 4,119 | 4,311 | 697 | 1,248 | 4,007 → 4,311 | a2 | F17_trip_fact |
| 1b3b70ec | trail | 3,938 | 4,213 | 701 | 991 | 4,213 → **in 4,726** (+F17, F9) | a1 | – |
| 05231e11 | trail | 4,153 | 4,153 | 728 | 1,374 | 4,153 → **in 4,739** (+F9) | a1 | F13_repeat |
| ebfcc20e | trail | 3,347 | 3,740 | 604 | 146 | 3,541 → 3,740 | a2 | – |
| 2cfe5543 | trail | 4,622 | 4,622 | 775 | 3,530 | 4,626 → 4,622 | a2 | – |
| 10c39b5a | trail | 3,788 | 3,788 | 652 | 936 | 3,963 → 3,788 (+F9) | a2 | F9_cta_fact |

Evidence: `o1 PIECE <id> LEN, ATT, DISC, SEED`. "Text kept" is read from DISC.

- Every F4 hold is a complete 546–775-word article (3,448–4,622 F4 chars), yet the violation text reads "content is only
  N chars — effectively empty" (`gate_extreme_length`) and the reason code is plain `length` for both sides
  (`gate_eval` HOLD_REASON_CODES). The code comment says F4 targets an "empty/near-empty response or a multi-thousand-word
  runaway… nothing narrower"; in this run it acted as a strict quality floor and was the top hold reason.
- Cost: 13 F4-headed pieces 1.8645 USD, 9 F4-only pieces 1.2984 USD; held pieces take 74.7 % of piece spend
  (`o4 HELD_HEAD`, `o4 HELD_GATESET`, `o4 HELD_SHARE P2`).

#### 4.5.4 Text gets shorter after F4 has measured it

`service._normalize_final_text` (AA-1047) runs after the write/check loop: stock-line cut, authenticity cut, tag strip,
FAQ answer fit (blog only), final integrity pass. F4 is not run again, and `services/quality/final_contract.py` has no
length check.

- F4 holds: in 10 of 13 the stored text is 192–557 chars shorter than the F4 reading on the ledger (derived from `LEN`
  against `f4_ledger`); 3 are equal (05231e11, 2cfe5543, 10c39b5a).
- Approved: 3 of 7 are stored under 4,700 while their ledger says F4 passed: 4dde01f8 (4,658), 1cfd4b8a (4,426),
  4e956cae (4,434) (`o1 PIECE … LEN f4_side=short, f4_ledger=in`). Hence 17 pieces short on stored text (13 F4 holds + these 3 + the
  empty failed piece) against 13 F4 holds (`o1 SUM_LEN f4_side_all`).
- Which step cuts is not measured. Only `t9_faq_answer_fit` ran on every finished piece (27 calls, `o2 LLM_HEALTH`).

#### 4.5.5 First check against final check

| Gate | Fixed | Kept | Introduced |
|---|---|---|---|
| F4_extreme_length | 6 | 12 | 1 |
| F17_trip_fact | 6 | 6 | 1 |
| F13_repeat | 7 | 2 | 2 |
| F9_cta_fact (hold part) | 5 | 1 | 1 |
| F13_leak | 4 | 0 | 0 |
| F18_rarity | 1 | 0 | 0 |

Source: `o1 SUM_FIRST_FINAL per_gate`. Only 2 real first-check passes (4dde01f8, 4e956cae); the third "pass" is the
failed piece with an empty ledger (`o1 SUM_FIRST_FINAL first_sets pass=3`, `o1 PIECE e16fbbfb ATT`). The one F4 introduced
is cda38200: in band at attempt 1 (4,915), cut to 4,586 by the attempt-2 sentence repair for F13 (`o1 PIECE cda38200`).

#### 4.5.6 Repair modes and attempts

| Repair after attempt 1 | Pieces | Approved | Held | Evidence |
|---|---|---|---|---|
| full_rewrite (all had F4 short at a1) | 18 | 2 (5b3ae9c4, 59c950aa) | 16 | `o1 SUM_ATTEMPTS modes`; `PIECE REP` |
| sentences | 7 | 3 (1cfd4b8a, ee4c8db6, a14126dc) | 4 (F17 ×3, F4 ×1) | `o1 PIECE REP, ATT` |
| none (passed at a1) | 3 | 2 | 0 (+1 failed) | `o1 PIECE REP modes=-` |

What the 18 full rewrites did to length (a1 → a2 F4 chars, derived from ATT and DISC):

- 8 reached the band: c0121d62, 5b3ae9c4, c6cc3a29, 59c950aa, 5a3e82fb, 175f6886, 1b3b70ec, 05231e11. 6 of them kept the
  rewrite (F4 fixed 6); 2 were dropped by the regression guard (below).
- 5 got longer but stayed short: a6e7e93f, d16dfc5b, b08b585c, dc07bc6a, ebfcc20e.
- 5 got shorter or stayed the same: da055040 (−228), 37e97e7e (−1,076), 6a2ecc16 (−449), 10c39b5a (−175), 2cfe5543 (−4).

Rewrites bring new problems: 9 of 18 added at least one new hold-capable gate (c0121d62, 175f6886, 1b3b70ec, 05231e11,
da055040, a6e7e93f, d16dfc5b, b08b585c, 10c39b5a; `o1 PIECE ATT`). The AA-528 regression guard (`guard_decision`,
gate_names mode) kept attempt 1 in 5 of them (a6e7e93f, d16dfc5b, b08b585c, 1b3b70ec, 05231e11; `o1 PIECE DISC`),
including 2 that had reached the band but added F17/F9 claims. The guard put truth before length, which is the right
order.

Other loop facts: 50 `t9_write` calls for 28 pieces = 28 first drafts + 22 second calls (18 rewrites + 4 sentence-repair
pieces that also re-called the writer: 1cfd4b8a, cda38200, 62117c16, ee4c8db6) (`o2 LLM_HEALTH`, `o1 PIECE LLM`). At
0.0462 USD per call the second calls cost about 1.02 USD (derived). `trimmed_pieces=0`: the AA-984 over-long trim never
ran (`o1 SUM_ATTEMPTS`).

#### 4.5.7 F17, F13 and F9 on the held pieces (final ledger)

| Gate | Class | Violations | Held pieces |
|---|---|---|---|
| F17_trip_fact | optional_as_planned | 7 | acfebc24, 2a31bdd6, 62117c16, 5a3e82fb, dc07bc6a (×3) |
| F17_trip_fact | pace_promise | 2 | c6cc3a29, 5a3e82fb |
| F17_trip_fact | time_not_in_source | 2 | 175f6886, dc07bc6a |
| F13_repeat | repeat_sentence | 4 | c0121d62, da055040 (×2), 175f6886 |
| F13_repeat | dedupe_echo | 2 | 175f6886, 05231e11 |
| F13_repeat | moment_under_other_heading | 1 | 175f6886 |
| F9_cta_fact | unsupported_other (warn only) | 27 | spread over held pieces |
| F9_cta_fact | trip_promise (holds) | 2 | c6cc3a29, 10c39b5a |
| F9_cta_fact | seo_field_claim (warn) | 2 | 37e97e7e, 2cfe5543 |

Source: `o1 SUM_CLASSES`, `o1 PIECE CODES`.

- **F17.** After a sentence repair F17 stayed on 3 of 5 pieces (acfebc24, 2a31bdd6, 62117c16), each a single
  optional_as_planned finding. The finding asks to "say it is optional or cut it" (`trip_facts.optional_as_fixed`) and
  the route table gives F17 `cut: cut_finding`, but in stop_and_label mode no code cut runs (ADR 0020 D6, `service.py`,
  AA-900 W0).
- **F13.** Both introduced F13_repeat findings came from the attempt-2 full rewrite (c0121d62, da055040).
- **F9.** The interim policy (f9-interim-v1) behaves as designed: of 31 F9 findings on held pieces only the 2
  trip_promise ones hold.
- **t10_judge.** 52 of 52 calls answered by the fallback route (13 / 11 / 16 / 12 per tenant), none not-ok
  (`o2 LLM_STAGE`, `o2 LLM_HEALTH`). Cost per call +166.7 % on phase 1 (output 767 → 2,188 tokens, 94,613 reasoning
  tokens), 0.0823 USD in total, 1.2 % of the chain (`o4 COMPARE_STAGE`, `o4 STAGE P2 t10_judge`).

#### 4.5.8 The failed piece

| Field | Value | Evidence |
|---|---|---|
| Piece / tenant / tour | e16fbbfb / trail / 84e392c3 (BT, 10 days, 37 atoms) | `o1 PIECE e16fbbfb`, `o1 TOURS` |
| Job | t9_write 0c2fbe6d **succeeded**, attempt 1/2, no error class or text, result `piece_status` | `o1 FAILED` |
| Ledger | t9_write ok (end_turn, 4,157 tokens out, 0.0664 USD); t9_faq_filter ok; no repair or faq_answer_fit rows | `o1 FAILED_LLM`, `o1 PIECE e16fbbfb LLM` |
| Stored | content 0 chars, empty gate ledger, no writer_input | `o1 PIECE e16fbbfb LEN, SEED` |
| held_reason | starts with the exception class name (`run_write_background` except: `f"{type(exc).__name__}: {exc}"`); the read-only script reports only `free_text` | `o1 PIECE held_head=free_text`; code `service.py` |
| Spend | 0.1044 USD | `o4 UNIT_PIECE P2 status=failed` |
| Effect | the pair stays undone: trail t9_blog_piece=11, t10_blog_terminal=10 | `o2 FUNNEL audit-trail-pulse` |

The writer reply came back whole, so the exception came after it and before any repair or normalizer step. Which class it
was is not in these outputs; one read of the first token of `held_reason` answers it. Ops sees a green job, and there was
no retry.

### 4.6 Export

27 Blog pieces × 3 formats and 36 T2 DOCX (including the policy-hold versions) reached the tenants; held pieces are
exported, the failed piece is not (`o2 EXPORT`, `o2 FUNNEL`). This matches the product rule that the tenant always
receives content and QA lives on the admin side.

### 4.7 Finding: t2_flag_fix cut replies

| Time | Tenant | Job | Tour | Call 1 (ceiling 4,096) | Call 2 (gateway retry, 8,192, effort medium) | Job result | Evidence |
|---|---|---|---|---|---|---|---|
| 05:57Z | terra | ffded869 | 8602c1d4 | billed_unusable, 4,096 out | ok, 6,132 out | succeeded, passed, 9.63 | `o2 FLAGFIX_CALL`, `o2 FLAGFIX_JOB` |
| 06:03Z | trail | 6868fe21 | 8602c1d4 | billed_unusable, 4,096 out | ok, 6,717 out | succeeded, passed, 10.0 | same |
| 06:09Z | wildkind | 178f506b | 8602c1d4 | billed_unusable, 4,096 out | **truncated at 8,192** | succeeded, passed, 10.0 (fix not applied) | same |

Why:
1. No `shared.stage_model_params` row for t2_flag_fix (`o2 FLAGFIX_PARAMS` prints only the fallback note).
2. `flag_fix_node` sends no `max_tokens`, so it gets the `LLMRequest` default of 4,096 (code:
   `shared/llm_client/models.py`), which equals the gateway's reasoning floor (code: `shared/aa_llm/tokens.py
   REASONING_FLOOR = 4096`).
3. The model is now Haiku 5.5 (`o2 FLAGFIX_CALL model=haiku-5-5@anthropic-direct`, output cap 128,000 per
   `o2 FLAGFIX_CATALOG`); thinking is billed inside the ceiling. The first call carries no effort (`effort=None`); only the
   retry carries `effort=medium`.
4. Output grew about 21× on average (30 days, `o2 FLAGFIX_30D`): Haiku 4.5 37 rows, average 104 tokens out (max 510); Haiku 5.5 ok rows
   13, average 2,165 (max 6,717). A1's `s1_flag_fix` is still mostly on Haiku 4.5 (455 rows, average 772).

Impact: money small (6 calls 0.0198 USD, 0.0123 of it not-ok; `o4 STAGE P2 t2_flag_fix`); about 20 s per call
(`o2 LLM_STAGE`); quality: 1 of 3 jobs lost the brand fix silently. Scope: all 6 rows are from 3 of the 4 graph-path trial
jobs; the 28 `t2-linear-1` jobs made 0 flag_fix calls. But the linear path still uses stage t2_flag_fix for sentence repair
(ceiling 4,096, `grounding.repair`) and meta regenerate (no ceiling, `_rerepair_meta`), so the same cut can hit it the first
time either runs on a 5.x route. The quality signal on the Haiku 5.5 rows lacks the keys to tell which task ran
(`task=unknown`).

---

## 5. Brand

Caveats: (1) the T2 comparison covers 9 tours, one of them the policy hold a8560125 (identical text by design), so
like-for-like distinctness rests on 8 tours × 6 brand pairs = 48 comparisons (derived). (2) Blog similarity is not like
for like: each tenant's slate picks different Segments of the same tour. (3) The judge's `cross_brand_distinct` is an
LLM estimate from one draft; the Jaccard numbers are measured.

### 5.1 T2 tour pages per brand (9 versions each)

| Metric | atlas | terra | trail | wildkind |
|---|---|---|---|---|
| ai_generated / needs_review | 8 / 1 | 8 / 1 | 6 / 3 | 8 / 1 |
| Stored score (validate), mean | 9.95 | 9.95 | 9.91 | 10.0 |
| Judge brand_fit, mean (min–max) | 5.88 (4–7) | 6.25 (6–7) | 6.12 (6–7) | 5.88 (4–7) |
| Judge cross_brand_distinct, mean (min–max) | 5.75 (4–6) | 6.0 (6–6) | 6.0 (6–6) | 5.75 (4–6) |
| Core idea judged present | 1 of 8 | 2 of 8 | 1 of 8 | 1 of 8 |
| Unsupported brand claims | 0 | 2 ethos, 1 version | 2 ethos, 1 version | 1 ethos, 1 version |
| Own forbidden-word hits / superlatives / undeclared positioning | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| Leaks (other brand or platform names) | 0 | 0 | 0 | 0 |
| Words, mean (min–max) | 1,695 (964–2,472) | 1,807 (1,000–2,486) | 1,657 (920–2,440) | 1,727 (1,024–2,402) |

Source: `o3 T2`, `o3 T2_CLAIMS`, `o3 T2_WORDS`, `o3 T2_LEAK`, `o3 T2_LEN`. Totals (derived): core idea absent in 27 of 32
judged versions; brand fit ≤ 7.0 everywhere and below the pass line on average for 4 of 4 brands. Trail's 3 needs_review
are 2 day-count codes + 1 policy hold; brand plays no part.

### 5.2 Measured distinctness (same tour, word 5-gram Jaccard between brands)

| Tour | Country (days) | Pairwise Jaccard mean (min–max) | Share copied from the Master, mean (min–max) |
|---|---|---|---|
| 207e4efa | CN (20) | 0.23 (0.15–0.37) | 0.38 (0.28–0.47) |
| 2d0ee81a | KR (10) | 0.14 (0.09–0.20) | 0.18 (0.16–0.22) |
| 56b61f58 | IN (15) | 0.18 (0.12–0.25) | 0.18 (0.16–0.21) |
| 7fe02d1a | LK (15) | 0.15 (0.11–0.27) | 0.26 (0.23–0.29) |
| 8602c1d4 | IN (28) | 0.17 (0.12–0.24) | 0.34 (0.27–0.45) |
| ac574bfe | LK (22) | 0.22 (0.15–0.37) | 0.39 (0.22–0.50) |
| b56704c5 | LK (17) | 0.15 (0.10–0.20) | 0.22 (0.17–0.27) |
| c9716429 | CN (14) | 0.19 (0.15–0.28) | 0.33 (0.22–0.41) |
| **8 rewritten tours** | | **0.18 (0.09–0.37)** (derived) | 0.18–0.39 per tour |
| a8560125 (policy hold) | IN (15) | **1.00** | 0.98 |

| Brand pair | Jaccard, 9 tours incl. hold | Jaccard, 8 rewritten tours (derived, ±0.01) |
|---|---|---|
| atlas ~ terra | 0.27 | 0.18 |
| atlas ~ trail | 0.23 | 0.13 |
| atlas ~ wildkind | 0.29 | 0.20 |
| terra ~ trail | 0.25 | 0.16 |
| **terra ~ wildkind** | 0.35 | **0.27** (closest pair) |
| trail ~ wildkind | 0.24 | 0.15 |

Source: `o3 T2_SIM`, `o3 T2_SIM_PAIR`, `o3 T2_SIM_ALL`; country and days from `o1 TOURS`. Trail (short sentences) is the
most distinct voice; terra (family) and wildkind (responsible nature) are closest. The shared text is consistent with both
brands keeping Master wording (place names, day titles, meals), but the scripts do not split overlap by origin. The
judge's own "distinct" score does not follow these differences (6.0 for every version of 2 brands).

### 5.3 Blog pieces per brand

| Metric | atlas | terra | trail | wildkind |
|---|---|---|---|---|
| Approved / held / failed | 2 / 4 / 0 | 3 / 4 / 0 | 1 / 5 / 1 | 1 / 7 / 0 |
| Main hold codes | F4 3, F13 1, F17 1 | F17 2, F13 1, F9_cta 1, F4 1 | **F4 5**, F13 1, F9_cta 1 | F17 4, F4 4, F13 1 |
| F15_voice failed / ran | 3 / 6 | 3 / 7 | 2 / 6 | **6 / 8** |
| F9_brand_style failed / ran | 1 / 6 | 1 / 7 | 1 / 6 | 1 / 8 |
| F2 forbidden / style warn / superlatives, F11 brand name, F19 authenticity, F10 cross-tenant: failed | 0 | 0 | 0 | 0 |
| T10 F9 brand-voice judge: pass / manual_check / flagged | 3 / 7 / 1 | 5 / 8 / 0 | 3 / 9 / 0 | 2 / 14 / 0 |
| Own forbidden-word hits (script count) | **2, in 1 piece** | 0 | 0 | 0 |
| Words, mean (min–max) | 718 (553–905) | 864 (759–1,086) | 622 (0–836)* | 746 (550–916) |
| Average chars | 4,173 | 4,957 | **3,530*** | 4,333 |

\* Includes the failed piece (0 words, 0 chars); without it trail averages about 726 words (derived from `o3 BLOG_LEAK`)
and 4,118 chars (derived from `o2 T9_SHAPE` and `o1 PIECE … LEN`). Source: `o3 BLOG`, `o3 BLOG_GATES`, `o3 BLOG_F9`, `o3 BLOG_WORDS`, `o3 BLOG_LEAK`, `o2 T10_HOLD`,
`o2 T9_SHAPE`.

- Blog 5-gram Jaccard across 60 brand pairs: mean 0.06, max 0.17 (`o3 BLOG_SIM_ALL`); F10 cross-tenant failed 0 of 27.
- The T10 brand-voice judge mostly returns a fact-check outcome: 38 of 52 rows are `manual_check` with
  FACT_CHECK_MANUAL_CHECK; only 3 SUMMARY_OFF_BRAND and 6 GENERIC_AI_WORDING (derived from `o3 BLOG_F9`).
- F15_voice fails on 14 of 27 pieces but no final hold set names it (`o2 T10_HOLD`, `o1 SUM_FIRST_FINAL`); the ledger count
  spans all attempts, so whether these are attempt-1 failures that were repaired is open.
- **A short-sentence brand collides with a fixed length band.** Trail's 6 written pieces average 4,118 chars against the
  4,700 floor (derived); all 5
  of its holds carry F4 too-short and 1 of 7 pieces is approved. The band does not read the brand's declared style.
- Atlas: the script counts 2 own-forbidden hits in 1 piece while F2_brand_forbidden failed 0 of 6 (`o3 BLOG_WORDS` vs
  `o3 BLOG_GATES`); open check §13.

### 5.4 What an agency would notice

1. Its tour pages read in its own voice (about 18 % shared 5-grams with another brand on the same tour), and no page names
   another brand or the platform.
2. The elephant tour is identical for every agency, wildkind included, and is not in its voice; this is the intended
   policy (keep as is + human review).
3. Its core idea rarely shows in the tour text (5 of 32 versions).
4. Its own brand name appears in blogs (23 hits over 28 pieces, derived from `o3 BLOG_LEAK`) but once in 36 tour pages
   (`o3 T2_LEAK`).
5. A short-style brand gets shorter blogs that the platform holds; under the "tenant sees content only" rule the agency
   still gets the text, so this shows internally.

---

## 6. Market

### 6.1 Declared vs used

| Tenant | Declared (order kept) | Normalised | DFS-supported | Unsupported | First supported declared | T2 keyword market | Slate markets | AA-629 banner | Unmapped-market rows |
|---|---|---|---|---|---|---|---|---|---|
| atlas | US, UK, UAE, Saudi Arabia, Singapore, Hong Kong | US UK AE SA SG HK | US, UK | **AE SA SG HK (4/6)** | US | US ✓ | US, UK | no | none |
| terra | UAE, Singapore, Hong Kong, UK, Australia | AE SG HK UK AU | UK, AU | **AE SG HK (3/5, the first three)** | UK | UK ✓ | UK, AU | no | none |
| trail | Europe, Australia, North America, Singapore | UK DE FR NL AU US CA SG | UK DE FR NL AU US | CA, SG (2/8) | UK | **US ✗** | US UK AU DE FR NL | no | none |
| wildkind | Europe, Australia, Canada, New Zealand, US | UK DE FR NL AU CA NZ US | UK DE FR NL AU US | CA, NZ (2/8) | UK | **US ✗** | US UK AU DE FR NL | no | none |

Source: `o3 MARKET` (fields `declared`, `normalized_countries`, `supported`, `unsupported`, `first_declared_supported`,
`t2_market`, `t2_market_is_first`, `slate_markets`, `aa629_banner`, `partial_unsupported_no_banner=true`,
`unmapped_requests=[]`).

- **No silent US fallback.** All 8 rewritten versions per tenant used `seo_source=tenant_market`; terra fell back to UK,
  its own supported market (`o3 MARKET_T2`). The old AA-629 bug did not recur.
- **Unsupported markets are dropped without a word.** `unmatched_countries()` returns a list only when *none* of the
  declared countries is supported (code: `seed_builder.py`), so with 4 of 4 tenants partly unsupported the banner is false
  and no `unmapped_market_requests` row is written.
- **T2 picks one market by global rank.** `resolve_buyer_market` takes the lowest `MARKET_RANK` (US first), so the two
  Europe-first brands get US keywords on 8 of 8 versions.

### 6.2 Data behind each market (research cache)

| Market | search_demand rows | rows with volume > 0 | PAA rows | Last refresh |
|---|---|---|---|---|
| US | 22,445 | 10,119 | **3,375** | 2026-11-09 |
| UK | 18,419 | 6,885 | 155 | 2026-11-09 |
| AU | 18,226 | 6,778 | 159 | 2026-11-09 |
| DE | 15,864 | 6,047 | 52 | 2026-11-09 |
| FR | 15,867 | 5,869 | 46 | 2026-11-09 |
| NL | 15,867 | 5,897 | 51 | 2026-11-09 |
| AE, SA, SG, HK, CA, NZ | **0** | 0 | 0 | none |

Source: `o3 DEMAND`, `o3 DEMAND_ABSENT`. Per-tour probe on the 12 tours (`o3 PROBE`, derived): 10 keyword ideas for every
tour × market; PAA ("people also ask") is 0 for DE, FR and NL on 7 of 12 tours each, for UK and AU on 1 of 12, for US on
0; US has the highest top-10 volume on 11 of 12 tours.

### 6.3 Keyword quality

| Signal | atlas | terra | trail | wildkind | Source |
|---|---|---|---|---|---|
| T2 keywords offered → kept | 10 → 5 | 10 → 5 | 10 → 5 | 10 → 5 | `o3 MARKET_T2` |
| T2 seo_error / language_blocked / kept_zero | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | `o3 MARKET_T2` |
| Blog pieces with an SEO keyword | 1 of 6 | 1 of 7 | 1 of 7 | **0 of 8** | `o3 MARKET_BLOG with_keyword` |
| Related keywords per PAA snapshot, mean (min) | 3.5 (0) | 3.0 (0) | 3.0 (0) | 2.62 (0) | `o3 MARKET_BLOG snap_related` |
| Snapshot relevance LOW / MED / HIGH | 2 / 2 / 2 | 2 / 3 / 2 | 2 / 3 / 2 | 2 / 2 / 4 | `o3 MARKET_BLOG` |
| FAQ questions per blog, mean (min) | 3.83 (3) | 3.71 (3) | 3.57 (0 = the failed piece, no writer input) | 3.25 (1) | `o3 MARKET_BLOG` |
| Slate Blog Segments cleared / below bar / few questions / no data | 71 / 80 / 25 / 10 (186) | **63 / 95** / 12 / 13 (183) | 79 / 69 / 23 / 12 (183) | 68 / 77 / 26 / 12 (183) | `o3 MARKET_SLATE` |
| Blog subjects proposed | 32 | 29 | 40 | 35 | `o3 MARKET_SLATE` |

3 of 28 Blog pieces carry an SEO keyword (derived). `choose_keyword` treats "no keyword" as normal, but at this rate it is
the usual outcome; the scripts do not separate "none offered" from "rejected by the grounding filter". The more DFS markets
a tenant keeps, the more Segments clear the bar (trail, 6 markets: 43 %; terra, 2 markets: 34 %, derived).

What agencies notice: Gulf / Asia sellers (atlas, terra) get content built from UK/US/AU search data with no note saying
so; Europe-first sellers (trail, wildkind) are optimised for the US; DE/FR/NL topics come with thin PAA material.

---

## 7. Ops

### 7.1 Jobs per kind (phase 2 window)

| Kind (stage) | Jobs | OK | Failed | Retried | Run p50 / p90 (s) | Wait p50 / p90 (s) | LLM calls per job p50 / p90 / max | Ledger USD (sum; p50 per job) | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| `t2_rewrite` (T2+T3) | 36 | 36 | 0 | 0 | 55.1 / 87.1 | 2.7 / 4.4 | 2 / 4 / 5 | 2.8059; 0.0782 | `o2 JOB_KIND`, `o2 JOB_LLM` |
| `t7_slate` (T7) | 12 | 12 | 0 | 0 | 232.0 / 428.1 | 2.6 / 4.6 | 81 / 165 / 165 | 0.1416; 0.0094 | same |
| `t8_angles` (T8) | 28 | 28 | 0 | 0 | 24.3 / 29.8 | 2.0 / 4.0 | 1 / 1 / 2 | 1.1208; 0.0377 | same |
| `t9_write` (T9+T10) | 28 | 28 | 0 | 0 | 143.0 / 164.4 | 2.8 / 4.2 | 10.5 / 12 / 12 | 2.7065; 0.0986 | same |

104 jobs, 0 failed, 0 retried, 0 job errors (`o2 SUMMARY_JSON job_errors=[]`). Gaps: `job_cost_usd=0.0` on every job kind
(`o2 JOB`, `o4 KIND P2`); the failed piece e16fbbfb sits under a succeeded job (§4.5.8); slate time grows with the
tenant's adopted tours (§4.3.2). Tenant id on every LLM row (G1) holds: 0 tenant-null rows on audit jobs (`o2 LLM_NOJOB`).

### 7.2 LLM call health (phase 2)

| Stage | Calls | Not OK | Kind | Fallback rung used | Latency p50 per tenant (ms) | Evidence |
|---|---|---|---|---|---|---|
| t2_generate | 35 | 1 | truncated; recovered by the one doubled-budget retry | 0 | 33,530–37,816 | `o2 LLM_HEALTH`, `o4 STAGE P2` |
| t2_judge | 34 | 2 | refused (`access_denied`) | 32/34 | 8,259–11,370 | `o2 LLM_HEALTH`, `o2 SUMMARY_JSON` |
| t2_flag_fix | 6 | 4 | 3 billed-unusable + 1 truncated, all max_tokens | 0 | 18,248–21,635 | `o2 LLM_HEALTH` (§4.7) |
| t7_debate_judge | 1,220 | 0 | – | 1,220/1,220 | 2,026–2,428 | `o2 LLM_STAGE` |
| t8_angle_gen | 30 | 0 | all end_turn | 0 | 20,829–23,329 | `o2 LLM_HEALTH` |
| t9_write / repair / faq | 50 / 73 / 55 | 0 | all end_turn | 0 | 14,010–16,032 (write) | `o2 LLM_HEALTH` |
| t10_judge | 52 | 0 | – | 52/52 | 18,362–21,947 | `o2 LLM_STAGE` |
| f10_embed | 52 | 0 | – | 0 | 365–408 | `o2 LLM_STAGE` |

- Waste: 7 not-OK calls, 0.1162 USD of 6.7747 (1.7 %), 5 on max_tokens; phase 1 wasted 0.8795 USD on 16
  (`o4 WASTE P1/P2`).
- Every judge row is served by a fallback rung (t2_judge 32/34, Debate 1,220/1,220, t10_judge 52/52). The refused first
  rung now costs only 2 rows in the window (AA-1042 effect), but the route still names a primary that does not answer, and
  every T2 job records 1 `route_degraded` entry (`o2 JOB_RESULT route_degraded.entries[] n=32 mean=1.0`); that this entry
  is the judge fallback is an inference.

---

## 8. Cost

### 8.1 Per stage (P2)

| Stage | Role | Model @ connection | Calls | USD | Share | USD/call | Avg out tokens | Not ok (USD) | Source |
|---|---|---|---|---|---|---|---|---|---|
| t2_generate | writer | sonnet-5-5 @ anthropic-direct | 35 | 2.7612 | 40.8 % | 0.0789 | 6,070 | 1 (0.1039) | `o4 STAGE P2` |
| t9_write | writer | sonnet-5-5 | 50 | 2.3093 | 34.1 % | 0.0462 | 2,172 | 0 | `o4 STAGE P2` |
| t8_angle_gen | writer | sonnet-5-5 | 30 | 1.1208 | 16.5 % | 0.0374 | 2,827 | 0 | `o4 STAGE P2` |
| t7_debate_judge | judge | gpt-6-luna @ openai-direct | 1,220 | 0.1416 | 2.1 % | 0.0001 | 135 | 0 | `o4 STAGE P2` |
| t9_repair | writer | haiku-5-5 | 73 | 0.1329 | 2.0 % | 0.0018 | 2,896 | 0 | `o4 STAGE P2` |
| t9_faq_answer_fit | validate | sonnet-5-5 | 27 | 0.1234 | 1.8 % | 0.0046 | 249 | 0 | `o4 STAGE P2` |
| t10_judge | judge | gpt-6-luna @ openai-direct | 52 | 0.0823 | 1.2 % | 0.0016 | 2,188 | 0 | `o4 STAGE P2` |
| t9_faq_filter | validate | haiku-5-5 | 28 | 0.0518 | 0.8 % | 0.0019 | 2,975 | 0 | `o4 STAGE P2` |
| t2_judge | judge | gpt-6-luna (+2 refused rows at 0 USD) | 34 | 0.0221 | 0.3 % | 0.0006 | 705 | 2 (0.0000) | `o4 STAGE P2`, `o4 VENDOR P2` |
| t2_flag_fix | writer | haiku-5-5 | 6 | 0.0198 | 0.3 % | 0.0033 | 5,555 | **4 (0.0123)** | `o4 STAGE P2` |
| f10_embed | embed | cohere-embed-v4 | 52 | 0.0067 | 0.1 % | 0.0001 | 0 | 0 | `o4 STAGE P2` |
| t2_itinerary_nudge | writer | haiku-5-5 | 5 | 0.0029 | 0.0 % | 0.0006 | 982 | 0 | `o4 STAGE P2` |

By role (derived): writer 6.3469 USD (93.7 %), judge 0.2460 (3.6 %), validate 0.1752 (2.6 %), embed 0.0067 (0.1 %). By
model: sonnet-5-5 6.3146 USD (93.2 %, 142 calls), gpt-6-luna 0.2460 (1,304 calls), haiku-5-5 0.2074, cohere 0.0067
(`o4 VENDOR P2`).

**Prompt caching is off.** `cache_write=0` on every P2 stage; the only cache reads are 7,959 tokens on t10_judge (OpenAI).
The Sonnet stages took 1,094,549 input tokens (derived: t9_write 611,718 + t2_generate 318,361 + t8_angle_gen 136,365 +
t9_faq_answer_fit 28,105). The Anthropic adapter adds `cache_control` only when the connection or model defaults set
`cache_system_prompt: true` (code: `shared/llm_client/adapters/anthropic_messages.py:333`).

### 8.2 Per tenant and per unit (P2)

| Tenant | Calls | USD | T2 | T7 | Pieces | Blog pieces | Approved | USD per T2 version | USD per blog | USD per approved blog | Month budget used (of 40) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| atlas | 393 | 1.4749 | 0.6331 | 0.0352 | 0.8066 | 6 | 2 | 0.0703 | 0.1344 | 0.4033 | 3.9562 |
| terra | 403 | 1.5699 | 0.6479 | 0.0359 | 0.8861 | 7 | 3 | 0.0720 | 0.1266 | 0.2954 | 3.0273 |
| trail | 398 | 1.7437 | 0.7654 | 0.0353 | 0.9430 | 7 (1 failed) | 1 | 0.0850 | 0.1347 | 0.9430 | 3.1884 |
| wildkind | 418 | 1.9861 | 0.7594 | 0.0351 | 1.1916 | 8 | 1 | 0.0844 | 0.1490 | 1.1916 | 3.1622 |

Source: `o4 TENANT P2`, `o2 T9_SHAPE`, `o2 T9_PIECES`, phase 2 `spend.txt BUDGET`; the four per-unit columns are derived.
Per-input costs are close across brands; cost per *approved* blog varies 4× because of the hold rate. No tenant is near
its budget and no job was budget-stopped.

| Unit | Value | Source |
|---|---|---|
| T2 version (36) | 0.0779 USD; median 0.0782, max 0.2099; 2.22 calls | `o4 UNIT_T2 P2` |
| Blog piece, any status (28) | 0.1367 | `o4 UNIT_BLOG P2` |
| Blog delivered (approved + held, 27) | 0.1417 | `o4 UNIT_BLOG` |
| Approved blog (7) | **0.5467** | `o4 UNIT_BLOG` |
| Approved piece with T7 overhead | 0.567 | `o4 UNIT_ALL` |
| Approved / held / failed piece | 0.1235 / 0.1429 / 0.1044 | `o4 UNIT_PIECE P2` |

**Growth plan headroom** (`o4 PROJECTION`, cap 40 USD/month, 200 rewrites): T2 alone 15.58 USD/month (39.0 % of the cap;
phase 0 forecast was about 38 USD at 0.19 USD per tour); after a full month of T2 the cap leaves room for 178 blogs; the cap
alone pays for 292 blogs but only 73 *approved* blogs at today's hold rate.

### 8.3 Held-piece spend

| Measure | P2 | Source |
|---|---|---|
| Held pieces / share | 20 / 71.4 % | `o4 HELD_SHARE P2` |
| Held USD / share of piece spend | **2.8587 / 74.7 %** | `o4 HELD_SHARE P2` |
| Any hold set containing F4 | 13 pieces, 1.8645 USD (65 % of held USD, derived) | `o4 HELD_HEAD`, `o4 HELD_GATESET` |
| F4 alone / F17 alone | 9 pieces 1.2984 / 4 pieces 0.5372 | `o4 HELD_GATESET` |
| Second t9_write calls | 22 calls ≈ 1.02 USD; 4 of those pieces ended approved, 18 held | `o1 PIECE LLM` (derived) |
| t9_write on the 18 held pieces that paid twice | 1.6275 USD, about half (≈ 0.81) the second write that did not change the outcome | `o1 PIECE LLM` (derived) |

A held piece costs 15.7 % more than an approved one (derived: 0.1429 / 0.1235), because it almost always pays a second write.
Held spend is not lost content (the tenant gets it), but it is spend on pieces that cannot be published as is.

### 8.4 Phase 1 vs phase 2

| Stage | P1 calls / USD | P2 calls / USD | USD per call change | Avg out P1 → P2 | Note |
|---|---|---|---|---|---|
| t9_write | 57 / 2.6466 | 50 / 2.3093 | −0.4 % | 3,054 → 2,172 | max_tokens 6 → 0; not-ok USD 0.8743 → 0; input per call +61 % (derived) |
| t2_generate | 10 / 0.6919 | 35 / 2.7612 | +14.0 % | 5,022 → 6,070 | calls per T2 version 7.4 → 2.22 (`o4 UNIT_T2`) |
| t8_angle_gen | 32 / 0.8723 | 30 / 1.1208 | +37.0 % | 1,986 → 2,827 | longer angle output |
| t10_judge | 73 / 0.0446 | 52 / 0.0823 | +166.7 % | 767 → 2,188 | reasoning tokens 45,140 → 94,613 |
| t9_repair | 25 / 0.0294 | 73 / 0.1329 | +50.0 % | 1,305 → 2,896 | |
| t7_debate_judge | 154 / 0.0186 | 1,220 / 0.1416 | 0.0 % | 142 → 135 | volume follows slate count |

| Unit | P1 | P2 | Change |
|---|---|---|---|
| USD per T2 version | 0.1411 | 0.0779 | −44.8 % |
| USD per blog piece | 0.4483 | 0.1367 | −69.5 % |
| USD per approved blog | 1.7933 | 0.5467 | −69.5 % |
| Held share of piece USD | 47.1 % | 74.7 % | +27.6 pts |
| Not-ok USD / share of chain | 0.8795 / 20.2 % | 0.1162 / 1.7 % | phase 1 §4.2 fix worked |

Source: `o4 COMPARE_STAGE`, `o4 COMPARE_UNIT`; changes derived. The P1 blog unit rests on 4 pieces (`o4 UNIT_BLOG P1`),
so treat it as a rough guide. P1 mixes 8 channels, P2 is Blog only, so "USD per piece, all channels" (+20.8 %) and loaded
USD per approved piece (×4.2) are not like for like.

### 8.5 Cost levers, ranked by saving (base: P2, 6.7747 USD)

| # | Lever | Saving | Evidence |
|---|---|---|---|
| 1 | Make the writer reach its length (extend repair; seed-aware target) so F4-short holds stop | 1.8645 USD of F4-held spend becomes publishable. If only the 9 F4-only pieces pass: approved 7 → 16, USD per approved blog 0.5467 → 0.2392 (−56 %), Growth-cap approved blogs 73 → about 167 (derived) | `o4 HELD_HEAD`, `o1 SUM_F4` |
| 2 | Choose attempt 2 by failure class: no full rewrite for F4-short | ≈ 0.81–0.83 USD (≈ 12 % of P2) from second writes on pieces that stayed held; the 4 rescues kept | `o1 PIECE LLM`, `o4 STAGE P2 t9_write` (derived) |
| 3 | t2_generate output / effort (40.8 %, effort still "high" until a paid quality read) | each 10 % cut saves 0.276 USD per 36 versions, about 1.53 USD per tenant-month at 200 rewrites; achievable cut not measured | `o4 STAGE P2`, `o4 PROJECTION` (derived) |
| 4 | T8: one call makes 3 angles, 1 is used | bounded by 1.1208 USD (16.5 %); keep 3 where a person picks | `o2 T8_OPTIONS`, `o4 COMPARE_STAGE` |
| 5 | Prompt caching on anthropic-direct | 1,094,549 Sonnet input tokens; saving depends on the stable-prefix share, not measured | `o4 STAGE P2` |
| 6 | Remaining truncation (t2_generate 1 cut, t2_flag_fix 4 of 6) | 0.1162 USD (1.7 %); the gain is fewer 15–27 s retries | `o4 WASTE P2`, `o2 FLAGFIX_CALL` |
| 7 | T7 / T10 / embeddings | together 0.2306 USD (3.4 %); not worth the work | `o4 STAGE P2` (derived) |

---

## 9. Mechanism table

Verdicts: **keep** (works as designed), **adjust** (right idea, needs a change), **not fit** (does not do its job in its
current form). Code at `apps/AA-CIS-App` `5cc016cde`.

### 9.1 T0 brand and markets

| Mechanism | Designed for | What the run showed | Verdict | Upgrade | Evidence |
|---|---|---|---|---|---|
| T0 .docx brief import → brand pack | Fill every brand-pack field from the agency's brief | Style guide, voice, forbidden list, core idea, examples filled 4/4; `system_prompt`, `default_cta`, explicit signature words empty 4/4; T2 loads the brand 36/36 | adjust | Map the 3 fields in the parser or remove them from the pack contract; show unmapped fields on the review screen before saving | `o3 BRAND`, `o2 T0_BRAND`, `o2 JOB_RESULT brand_loaded` |
| Market normalisation (regions → ISO, AA-629) | Turn "Europe / North America" into DFS markets | Correct 4/4; `tenant_config.markets` None 4/4 | keep | Write `tenant_config.markets` too, or retire the field | `o3 MARKET`, `o2 T0_MARKETS` |
| Signature vocabulary + undeclared positioning (AA-800) | Allow a brand's own positioning words, block undeclared ones | Block side: 0 undeclared hits in 36 T2 + 28 blogs, F2_style_warn 0/27. Allow side: only atlas has a (derived) signature word, used 1/9 T2, 0/6 blogs | keep (block) / adjust (allow) | Ask for signature words explicitly in T0 | `o3 BRAND`, `o3 T2_WORDS`, `o3 BLOG_WORDS`, `o3 BLOG_GATES` |
| Brand forbidden list (T2 FORBIDDEN_WORD, blog F2_brand_forbidden) | Keep banned words out | T2 0 hits; blog gate failed 0/27 but the script counts 2 hits in 1 atlas piece | keep (verify) | Reconcile script vs gate before claiming 0 (§13) | `o3 T2_WORDS`, `o3 BLOG_WORDS`, `o3 BLOG_GATES` |

### 9.2 T2 rewrite and T3 QA

| Mechanism | Designed for | What the run showed | Verdict | Upgrade | Evidence |
|---|---|---|---|---|---|
| T2 linear orchestrator (`t2-linear-1`) | Bounded writer → T3 → field regen, resumable | 28/28 jobs, resumed 0; initial 30 / field_regen 2; p50 55 s; 0 failures | keep | – | `o2 JOB_RESULT t2_orchestrator.*`, `o2 JOB_KIND` |
| T3 QA score vs pass line 7.0, with report-only brand-fit judge | Escalate weak rewrites; judge brand voice | Score mean 9.954 (p50 10) while brand fit is 5.88–6.25 (max 7.0), below the line for 4/4 brands; only structural/policy codes escalate | adjust | Calibrate brand fit on human labels (AA-729 golden set) before it gates; show brand fit beside the score in Writing Lab | `o2 JOB_RESULT score`, `o3 T2`, `o4 STAGE P2 t2_judge` |
| Judge `cross_brand_distinct` | Estimate how differently the tour would read for another brand | 5.75–6.0, near constant; measured overlap 0.09–0.37 per pair (mean 0.18) and the judge does not follow it | not fit | Replace with a deterministic cross-tenant 5-gram overlap per version ($0), stored for the admin | `o3 T2`, `o3 T2_SIM`, `o3 T2_SIM_PAIR` |
| Core-idea (mission) check | The tenant's core idea appears in the itinerary | Absent in 27/32; report only | adjust | Label about 10 versions to tell writer drop from judge misread, then fix that side | `o3 T2 mission_present` |
| Brand-claim fidelity check (bc_v1, report only) | Catch brand-story claims the source does not make | 5 unsupported ethos claims in 3 versions; 0 from the brand pack; delivered unchanged | keep | After the "no new gates" freeze, send these spans to sentence repair | `o3 T2_CLAIMS` |
| Brand / persona leak detection (incl. F11_brand_name) | No other agency's or platform name in a tenant's copy | 0 leaks in 36 T2 + 28 blogs; F11 0/27 | keep | – | `o3 T2_LEAK`, `o3 BLOG_LEAK`, `o3 BLOG_GATES` |
| T3 day-count slot (`T2_DAY_COUNT_VS_MASTER`) | Stop rewrites that change the day structure | 2/36 escalated (trail only) after the writer budget was spent | keep | Show the mismatched day numbers in the admin quality tab; check why only the short-sentence brand trips it | `o3 T2_NR` |
| Elephant-riding policy hold (ADR 0020 D8) | Keep the Master text, 0 LLM calls, human review | 4/4 held at $0, 0–1 s; text = source (Jaccard 1.00); 3 review checks per version; delivered | keep | Check whether the 3 queue checks per version are duplicates; make sure the queue item is worked | `o3 T2_SIM a8560125`, `o3 T2_NR`, `o2 JOB_RESULT policy_hold.*` |
| T2 final contract (stored = gated) | Store only text that passed | sha_match 32/32; agrees 31/32; 1 flip to unpublish | keep | – | `o2 JOB_RESULT final_contract.*` |
| Brand precheck `ITINERARY_MEAL_TIME_INVENTED` | Catch invented meals and times | Fires on 20/36; never a chosen (blocking) code | adjust | Label a sample: bind it if true positive, fix or drop if noise | `o3 T2_CODES` |
| t2_flag_fix / s1_flag_fix call ceiling on 5.x models | Short targeted repair (Haiku 4.5: 104 tokens average) | 4/6 rows cut at 4,096 / 8,192 on Haiku 5.5; 1/3 jobs lost the fix silently; about 20 s per call | adjust | `stage_model_params` row (effort low, ceiling ≥ 8,192) or a non-reasoning model; tag the task in the quality signal; "fix not applied" in the job result | `o2 FLAGFIX_*`, `o4 STAGE P2 t2_flag_fix` |
| T2 SEO market choice (`resolve_buyer_market`, global MARKET_RANK) | One keyword market per tenant rewrite | atlas US, terra UK match their first supported market; trail and wildkind get US although UK is first (8/8) | adjust | Use the tenant's first supported declared market, or let the agency choose (open S229 multi-market question) | `o3 MARKET`, `o3 MARKET_T2` |
| T2 keyword handoff | Pass ranked keyword ideas to the writer | 10 → 5 on every version; 0 seo_error / language_blocked / kept_zero | keep | – | `o3 MARKET_T2` |
| AA-629 unmatched-market banner + unmapped-market requests | Record or show markets DFS does not support | Fires only when none is supported; partial cases (4/6, 3/5, 2/8, 2/8) give banner false 4/4 and no rows | not fit (partial case) | Record a request for every unsupported country; show "we write for X, Y; Z is not covered yet" in market settings | `o3 MARKET`, `o3 DEMAND_ABSENT` |
| Research cache per market (`search_demand`) | Demand, PAA, related keywords per DFS market | US 3,375 PAA rows vs DE/FR/NL 46–52; PAA 0 on 7/12 tours each for DE/FR/NL; 0 rows for 6 unsupported markets | adjust | Refresh PAA for DE/FR/NL (state the DFS cost first); decide the 6 unsupported markets with the AA-629 row | `o3 DEMAND`, `o3 PROBE` |

### 9.3 T5 and T7 slate

| Mechanism | Designed for | What the run showed | Verdict | Upgrade | Evidence |
|---|---|---|---|---|---|
| T5 atoms / Segments | Every tour has ranked Segments per market | 12/12 tours; 18–55 Segments; 6 markets each | keep | – | `o2 T5_TOUR`, `o2 SUMMARY_JSON t5` |
| T7 Blog Bar (demand ≥ 1,000, questions ≥ 3) | Write Blog only where search demand exists | 607/1,584 rows clear; caf4bf16 clears in no market (4 pairs without Blog) while its place terms carry US 201,240 | adjust | Check the place → Segment demand join for low-demand tours; tell the tenant why a tour has no Blog topic | Σ `o1 PAIR`, `o2 T5_SEG`, `o3 PROBE` |
| Slate multi-market fan-out (`resolve_buyer_markets`) | Build subjects from every supported market | Slate markets = supported list 4/4; cleared 63–79 of 183–186; terra (2 markets) clears the fewest | keep | Product option: a labelled proxy market for unsupported countries | `o3 MARKET_SLATE` |
| T7 Debate cut | Cut off-brand or contested candidates | 499/502 free candidates flagged; all of them in 41 of the 44 pairs with any; the 50 % cap decides; 1,220 calls / 0.14 USD | not fit (current threshold) | Make Debate advisory (rank only) until recalibrated against the served judge's scale with labels | Σ `o1 PAIR`, `debate.py`, `o4 STAGE P2` |
| One piece per place (Blog) | No two Blog articles on one place per tenant | 59 seeded candidates held; no duplicate-place pieces | keep | – | Σ `o1 PAIR` |
| T7 proposal → Subject for low-demand tours | Every tour with a free candidate gets a Subject | 84e392c3 × atlas / wildkind: 2 free candidates, no Subject | adjust (cause unverified) | Read the slate job result; if rank/size drops them, guarantee ≥ 1 Subject per adopted tour with a free candidate | `o1 PAIR`, `o1 SUM_PAIRS` |
| Multi-tour Segment Subjects | One Segment covers several tours | 7 of 28 pieces on Segments covering 3 tours; per-pair counting inflated S275 (42 vs 28) | keep (mechanism) / adjust (reporting) | Count per piece; show "covers 3 of your tours" | `o1 SUM_DRIVERS`, `o2 FUNNEL` |
| Blog Subject seed size reaching T9 | T7 decides a Subject is ready to write | Seed ≤ 991 words: 9/12 held on F4; ≥ 1,210: 4/15; the 146-word seed gave 3 F4 holds + 1 F17/F9 hold | adjust | Seed-aware floor (§9.5) or a minimum seed size for Blog in the T7 bar | `o1 PIECE SEED` (derived), `o1 SUM_DRIVERS` |
| T7 slate as a job | Move slate out of the request (504 in the S231 pilot) | 12/12, no 504; p50 232 s, p90 428 s, growing with segments seen (60–63 → 183–186) | adjust | Incremental slate: new or changed tours only, cached Debate verdicts | `o2 JOB_KIND t7_slate`, `o1 T7JOB` |

### 9.4 T8 angles

| Mechanism | Designed for | What the run showed | Verdict | Upgrade | Evidence |
|---|---|---|---|---|---|
| T8 angle generation (3 options, 1 chosen) | Let the tenant pick among distinct angles | 28/28, 30/30 end_turn; 16.5 % of spend, cost per call +37 %; one goal only (`introduction_awareness`) | keep (quality) / adjust (batch cost) | Keep 3 where a person picks; 1 angle (or cheaper options 2–3) in batch / auto-pick runs; run the other goals in the golden set | `o2 T8_OPTIONS`, `o2 T8_REQ`, `o4 STAGE P2`, `o4 COMPARE_STAGE` |

### 9.5 T9 write

| Mechanism | Designed for | What the run showed | Verdict | Upgrade | Evidence |
|---|---|---|---|---|---|
| Writer length-and-effort block (`prompts._BLOG_WORDS` 900–1,300, max 1,600; S271) | Stop the phase 1 runaway; land inside F4 | Runaway gone (max_tokens 6 → 0, output 3,054 → 2,172), but 25/28 under 900 words, F4 short on 18/28 first drafts, approved median 824 | adjust | Keep the ceiling and write-once; count words in code after the draft ($0) and feed the measured deficit; state the target above the floor | `o4 STAGE P1/P2 t9_write`, `o1 SUM_LEN`, `o1 SUM_FIRST_FINAL` |
| F4 blog band 4,700–13,000 chars, per channel only (AA-531) | Catch empty or runaway text | Top hold reason: 13/20, all short, 9 F4-only; holds are full 546–775-word articles; message says "effectively empty"; code `length` mixes both sides; trail's short style: 5/5 holds F4 | adjust | One blog floor constant shared by prompt and gate; `length_short` / `length_long` codes with words and target in the message; decision for the tech lead: floor by channel and seed tier (or brand style) | `o1 HDR`, `o1 SUM_F4`, `o2 T10_HOLD`, `o2 T9_SHAPE` |
| Short F4 repaired by full rewrite (route table `F4_extreme_length: rewrite`) | One generic fix for any length failure | 18 rewrites: F4 fixed 6, 9/18 added hold gates, 5 shorter or same, 2 approved; ≈ 1.02 USD in second calls | not fit (short side) | **Extend repair**: section-level step that adds the missing words from unused seed facts (reuse `quality_gates.unused_source_facts`, as AA-788 F14 does); passing sections untouched; F17/F9 run on the added text | `o1 SUM_ATTEMPTS`, `o1 SUM_FIRST_FINAL`, `o1 PIECE ATT/DISC`, `o4 STAGE P2` |
| T9 attempt loop (`MAX_ATTEMPTS=3`, 2 paid) | Fix failing gates with at most 2 paid attempts | 22/28 paid a second write; 4 rescued; held pieces cost 15.7 % more than approved | adjust | Pick attempt 2 by failure class and track the rescue rate per class | `o1 SUM_ATTEMPTS`, `o4 UNIT_PIECE P2` |
| Over-long trim and rewrite target (`length_trim`, AA-984) | A runaway blog over 13,000 chars | Never ran: 0 long, 0 trimmed | keep | Dormant guard | `o1 SUM_F4`, `o1 SUM_ATTEMPTS` |
| Sentence repair at attempt 2 (`sentence_repair.plan`) | Fix quoted F13/F17/F9 findings without inventing facts | 7 pieces, 3 approved; F17 optional_as_planned stayed 3/3; cut cda38200 under the floor; approved 1cfd4b8a stored at 4,426 | adjust | Floor-aware (refuse a cut that drops under the F4 floor, prefer a rephrase); deterministic "optional" hedge for optional_as_planned | `o1 PIECE` cda38200 / 1cfd4b8a / acfebc24 / 2a31bdd6 / 62117c16 |
| Stop-and-label instead of a paid attempt 3 (AA-900 W0, ADR 0020 D6) | No paid third try; typed reasons | 20/20 held at attempt 2 with label codes; no attempt 3 spend | keep | Pair with $0 code fixes once the D6 record exists: optional_as_planned `cut_finding`, repeat_sentence later-copy cut | `o1 SUM_ATTEMPTS`, `o1 PIECE REP` |
| AA-528 regression guard (gate_names) | Never ship a rewrite that breaks more than it fixes | Kept attempt 1 in 5/18 rewrites, incl. 2 in-band rewrites that added F17/F9 | keep | None; the extend repair removes the length-vs-truth trade-off | `o1 PIECE DISC` |
| Post-loop normalizer (`_normalize_final_text`, AA-1047) + final contract | One owner for post-loop edits; contract checks stored text | Stored 192–557 chars shorter than the F4 reading in 10/13 holds; 3/7 approved stored under 4,700 with F4 "in" | adjust | Re-run F4 on the normalized text; make the FAQ answer fit and stock-line cut floor-aware; log chars before/after each step | `o1 PIECE LEN`, `o1 SUM_LEN f4_side_all` |
| Blog SEO keyword choice (`choose_keyword` + grounding filter) | One grounded related keyword per blog | 3/28 carry one; related keywords 2.62–3.5 mean (min 0); relevance LOW on 8/28 | adjust | Log why no keyword was chosen (none offered vs rejected), then fix the larger cause | `o3 MARKET_BLOG` |
| Failed-piece path (`run_write_background` except → `failed`) | A crash before content is never stored as held | 1 failed after an OK writer reply; job succeeded, no retry, no typed class, 0.1044 USD, pair left undone | adjust | Typed failure code (exception class + loop step) in the job result and job-runner summary; re-queue once if transient | `o1 FAILED`, `o4 UNIT_PIECE`, `o2 FUNNEL` |

### 9.6 T10 gates

| Mechanism | Designed for | What the run showed | Verdict | Upgrade | Evidence |
|---|---|---|---|---|---|
| F17_trip_fact (`trip_facts`) | Hold unsupported trip facts or promises | 7 held; optional_as_planned 7, pace_promise 2, time_not_in_source 2; fixed 6, kept 6, introduced 1 | keep | Fix side: hedge / cut_finding (§9.5) | `o1 SUM_CLASSES`, `o1 SUM_FIRST_FINAL` |
| F13 leak / repeat (`hygiene`) | Hold leaks and near-duplicates | Leak fixed 4/4; repeat fixed 7, kept 2, introduced 2 (both by the rewrite) | keep | Fewer full rewrites; $0 later-copy cut under D6 | `o1 SUM_FIRST_FINAL`, `o1 SUM_CLASSES` |
| F9 interim policy (f9-interim-v1) | Hold only trip_promise; warn on the rest | 2 holds; 27 unsupported_other + 2 seo_field_claim warned | keep | As planned: the W1/W2 calibrated claim instrument first | `o1 SUM_CLASSES`, `o2 T10_HOLD` |
| F15_voice (rule) / F9_brand_style (LLM) | Catch stock frames and off-voice wording | F15 failed 14/27 (wildkind 6/8), never in a final hold set; F9_brand_style 4/27 | keep (verify) | Confirm whether F15 failures are attempt-1 only; if they survive into delivered text, the ledger should say so | `o3 BLOG_GATES`, `o2 T10_HOLD` |
| T10 F9 brand-voice judge | Brand-voice verdict per piece | 52 rows: 38 `manual_check` with FACT_CHECK_MANUAL_CHECK; only 3 SUMMARY_OFF_BRAND, 6 GENERIC_AI_WORDING | adjust | Split the fact-check outcome from the voice verdict | `o3 BLOG_F9`, `o4 STAGE P2 t10_judge` |
| F10 cross-tenant cannibalization | Stop near-duplicate blogs across tenants | 0/27 failures; blog overlap max 0.17, mean 0.06 | keep | – | `o3 BLOG_GATES`, `o3 BLOG_SIM_ALL` |

### 9.7 Gateway, routing, ops and cost

| Mechanism | Designed for | What the run showed | Verdict | Upgrade | Evidence |
|---|---|---|---|---|---|
| Judge routing (t2_judge, Debate, t10_judge) with model-first fallback | Primary rung first, fallback on error, at no cost | Every judge row served by the fallback (32/34, 1,220/1,220, 52/52); 2 refused rows at 0 USD; `route_degraded` on every T2 job | adjust | While the primary rung is closed, put the serving model first so rows stop reading as degraded | `o2 SUMMARY_JSON`, `o2 LLM_HEALTH`, `o4 VENDOR` |
| Per-stage `max_tokens` ceilings + one doubled retry (CIS #1330) | No billed-but-unusable cut replies | Not-ok 0.8795 → 0.1162 USD; retry recovered t2_generate 1/1, t2_flag_fix 2/3; t2_flag_fix still on the 4,096 default | keep | Ceiling for t2_flag_fix (§9.2); check the t2_generate ceiling | `o4 WASTE`, `o2 LLM_HEALTH` |
| Job runner (worker) for T2/T7/T8/T9 | Async, retryable tenant jobs | 104 jobs, 0 failed, 0 retried, wait p90 ≤ 4.6 s | keep | – | `o2 JOB_KIND` |
| T9 job status vs piece status | A job fails when its output fails | 1 failed piece under a succeeded job with an empty error | adjust | Job result carries the piece's terminal status and reason; count failed pieces in ops views | `o1 FAILED`, `o2 T9_PIECES` |
| `shared.job.cost_usd` | Cost per job in ops views | 0.0000 on every T-series job in both phases | adjust | Fill from the ledger at job end, or stop showing it | `o4 KIND P2/P1`, `o2 JOB` |
| Ledger attribution (`llm_call_log` v2) + G1 tenant id | Cost per unit and tenant from one source | Gap 0, unattributed 0, job kinds and per-piece sums match; 0 tenant-null rows | keep | – | `o4 TOTAL`, `o4 WASTE`, `o2 LLM_NOJOB` |
| Model routing by role | Spend money on writing only | Writer 93.7 %, judges 3.6 %; t2_generate and t8 still at effort "high" | keep | Paid effort A/B on t2_generate / t8_angle_gen (lever 3) | `o4 STAGE P2`, `o4 VENDOR P2` |
| Prompt caching (opt-in `cache_system_prompt`) | Cut repeated input cost | Not active: cache_write 0 on every stage; 1.09 M Sonnet input tokens | adjust | Measure the stable-prefix share on t9_write / t2_generate, then enable per connection or model | `o4 STAGE P2`, `anthropic_messages.py:333` |
| Tenant AI budget (Growth 40 USD/month, hard stop) | Stop runaway spend per tenant | 0 stopped jobs; 3.03–3.96 of 40 used; only 73 approved blogs fit the cap at today's hold rate | keep | Show per-unit forecast (USD per T2, per approved blog) in Tenant 360 and billing; review the plan after levers 1–2 | `spend.txt BUDGET`, `o4 PROJECTION` |
| Export (Blog HTML/text, T2 DOCX) | Tenant always gets content | 27 pieces × 3 formats; 36 DOCX incl. policy holds; failed piece not exported | keep | – | `o2 EXPORT` |

---

## 10. Roadmap

Each item is one concrete change. Costs are LLM/DFS cost to build or verify, not engineering time.

### Now ($0, code only)

1. **T9 length honesty.** One shared blog floor constant used by `prompts.py` and `quality_gates.py`; fix the "tags
   included" comment; split the reason code into `length_short` / `length_long` with words and target in the message.
2. **Re-run F4 on the stored text** in the final contract, and make sentence repair, the FAQ answer fit and the stock-line
   cut refuse a change that drops the text under the floor; log chars before and after each normalizer step.
3. **Typed failure code for failed pieces**, carried in the `t9_write` job result and the job-runner summary; read the
   exception class of e16fbbfb first.
4. **`stage_model_params` rows for t2_flag_fix and s1_flag_fix** (effort low, ceiling ≥ 8,192), a "fix not applied" flag
   in the T2 job result, and the task name in the quality signal.
5. **Fill `shared.job.cost_usd` from the ledger** at job end.
6. **Judge routes: serving model first** while the refused rung is closed (t2_judge, t7_debate_judge, t10_judge).
7. **Unmapped-market request for every unsupported country** and a line in market settings naming the covered and
   uncovered markets.
8. **Piece-weighted status counts** in status reads and the portal ("covers 3 of your tours").
9. **Read-only checks:** the 84e392c3 slate drop, the atlas forbidden-word mismatch, F15 attempt timing (§13).

### Next (design + small paid verification runs)

1. **Extend repair for short F4**, replacing the full rewrite on the short side; verify on about 3 pieces, then on the
   phase 2 set (upper bound: approved 7 → 16 of 28).
2. **Debate advisory mode** (rank only, no cut) until recalibrated against labels.
3. **Deterministic cross-brand 5-gram overlap** per T2 version in place of the judge's `cross_brand_distinct`.
4. **Brand-fit calibration** on the AA-729 golden set (with core-idea labels), then decide whether it gates.
5. **Split the T10 brand-voice judge**: fact-check outcome apart from the voice verdict.
6. **T0 parser maps `system_prompt`, `default_cta` and signature words**, and the review screen lists unmapped fields.
7. **T2 SEO market = the tenant's first supported declared market** (or the agency's choice).
8. **No-Blog-topic reason** shown to the tenant, and a check of the place → Segment demand join on caf4bf16.
9. **Prompt caching**: measure the stable prefix on t9_write / t2_generate, then enable it.
10. **Agency web HA**: 2 tasks or an on-demand base for `aa-crm-dev-web` before the pilot (UI item 21; small monthly cost,
    state it before the change).

### Later (tech lead decisions, scale)

1. **Seed-tier (or brand-style) blog floor**, or a minimum seed size for Blog in the T7 bar.
2. **D6 measurement records** for the optional_as_planned hedge / cut and the repeat_sentence later-copy cut, then turn them on.
3. **Incremental T7 slate** (new or changed tours only, cached Debate verdicts).
4. **T8 single-angle mode** for batch / auto-pick runs, and T8 multi-goal coverage in the golden set.
5. **PAA refresh for DE/FR/NL** (DFS cost estimate first) and a labelled proxy-market option for unsupported countries.
6. **Effort A/B on t2_generate and t8_angle_gen** (paid quality read).
7. **Meal-time precheck** labelled, then bound or dropped.

---

## 11. Portal UI list

Layer C of AA-741: a read-only walk of every Content studio page on the 4 audit tenants (S276).

**How it was done.**
- Sign-in through the partner-pool managed login, as in `e2e/smoke-portal/auth.setup.ts` (password + TOTP), with the E2E
  CRM owner identity, which has editor studio membership on all 4 audit tenants since S270. Credentials were read into
  memory only; no secret was printed, written or captured, and no login page was screenshotted. The studio session was
  switched per tenant with `POST /api/auth/tenant-select` (a session choice, no data write).
- Read-only guard: every walk context aborts any non-GET request on the portal origin except `/api/auth/*` and `/auth/*`.
  Result: 0 requests blocked, nothing clicked.
- Coverage: b8611143 (atlas, the most data: 17 pieces, 13 tours) on every page × desktop 1440 / mobile 390 × light / dark;
  7348dbd4 (terra), c3182dd9 (wildkind), d6de5b7c (trail) on 10 data pages × desktop-light + mobile-dark.
- Automated checks over 156 page loads: 0 horizontal overflow at 390 px, 0 console errors, 0 HTTP ≥ 400 on the portal
  origin, 0 load errors, apart from the Spot interruption in item 21.
- Screenshots: 148 PNGs kept outside the public repo (session folder; they show piece titles and tour names), named `<tenant8>-<page>-<desktop|mobile>-<light|dark>.png`. E-mail addresses are
  replaced by "[e-mail hidden]"; generated piece body text and the angle brief are blurred. Still visible: piece titles,
  catalog tour names and photos, the synthetic brand-brief text and the audit tenant names (phase 0/1 committed the same
  kind of shots).

| # | Page | What is wrong or confusing for a B2B agency user | Severity | Suggested change | Benchmark | Screenshot |
|---|---|---|---|---|---|---|
| 1 | Piece drawer (My Content ?piece=) | The agency sees writer mechanics: the "Angle" block shows the full writer brief plus a "Search context used" query dump, against the "tenant sees content only" rule. No SEO snippet and no channel-styled preview; export buttons and provenance sit under the full text | High | Hide brief and query dump; show the angle as one sentence; add a Google snippet preview and per-channel preview; sticky action footer | Jasper / Copy.ai document view; Yoast snippet preview; Buffer post preview | `b8611143-content-piece-desktop-light.png`, `-dark.png` |
| 2 | Publish + Integrations | Connecting means pasting credentials: a WordPress application password; for Facebook a Meta developer app switched to Live plus a Page ID and long-lived token ("about 15 minutes"). The same forms appear on both pages | High | OAuth "Continue with Facebook" and WordPress.com/Jetpack OAuth (app password as fallback); one connection place (Integrations); Publish shows status + link | Buffer / Hootsuite / Later; Jetpack connect | `b8611143-publish-desktop-light.png`, `b8611143-integrations-desktop-light.png`, `b8611143-help-facebook-desktop-light.png` |
| 3 | Social Posts (Create) | Topics are raw itinerary fragments (verb · place), with no tour name, image or reason for the "best first" rank; near-identical lists across LinkedIn/Facebook/Instagram/TikTok (50–55 each); 50+ rows of Pick/Skip with no paging or tour filter; the reallocation panel sits below the list | High | Idea cards with a human headline, source tour + photo, rank reason and channel fit; filter by tour/country; paginate; plan panel on top | Later / Buffer idea board; Jasper Campaigns | `b8611143-create-social-desktop-light.png`, `7348dbd4-create-social-desktop-light.png` |
| 4 | Marketplace | Many cards have no photo; some photos are reused across different tours; no price in "All tours"; newest-first sort only; no visible "Rewrite" CTA | High | Photo coverage gate or country fallback image; "From $X" on every card; sort by price, length, popularity; primary CTA per card | Viator / GetYourGuide partner catalog; TourRadar | `b8611143-marketplace-desktop-light.png`, `-mobile-dark.png` |
| 5 | Brand Identity + Articles | Target markets accept UAE / Singapore / Hong Kong with no warning that search data covers only US/UK/AU/DE/FR/NL (AA-629); Articles shows "~18,100 searches a month" without naming the market; "Best first" is not ordered by that volume and is not explained | High | Search-data country next to every volume; warn on uncovered markets and name the fallback; explain or expose the sort | Semrush / Ahrefs database flag | `7348dbd4-brand-desktop-light.png`, `7348dbd4-create-article-desktop-light.png` |
| 6 | Dashboard | "Get started" checklist is flaky: "2 of 4" in 2 of 13 loads, "3 of 4" in the rest, for a tenant with 13 tours. Cause: `web/app/(studio)/portal/_components/GettingStarted.tsx` L37–52 fetches in `useEffect` keyed on `catalogCount`; an earlier `Promise.all` started at 0 can resolve last and overwrite the result | Medium | react-query with the count as a query (or ignore stale results); hide the card until loaded | Linear / Notion onboarding | `b8611143-dashboard-desktop-dark.png` vs `b8611143-dashboard-mobile-light.png` |
| 7 | Dashboard + Billing | Developer metrics lead ("API calls 0 / 20,000", "Rate limit 300 RPM", API calls per day). Plan-change actions are shown to an editor while Add-ons says only the owner can request changes | Medium | Lead with content outcomes (tours rewritten, pieces ready/published, quota); API usage in an "API" tab; hide plan actions from non-owners | Canva Teams / Jasper billing; Stripe portal | `7348dbd4-dashboard-desktop-light.png`, `7348dbd4-billing-desktop-light.png` |
| 8 | Shell (all pages) | Sidebar groups start collapsed, so only "Dashboard" shows; tiny letter-spaced group labels | Medium | Expand by default (remember state) or a flat nav of about 6 items | HubSpot / Canva / Linear nav | `7348dbd4-dashboard-desktop-light.png` |
| 9 | Marketplace "In my catalog" vs My Tours | Two pages for the same set; My Tours shows only name / country / status (all "READY") | Medium | One My Tours table with price, last edited, version, export/publish state, brand; drop the duplicate tab | Shopify products list | `b8611143-marketplace-mine-desktop-light.png`, `b8611143-my-tours-desktop-light.png` |
| 10 | Brand Identity | One long 13-field form; no sample of the voice; forbidden words in a truncated one-line input; Default CTA and Brand context empty after the T0 brief; no sticky save | Medium | Sections (Who / Audience / Voice / Rules / CTA); "preview a paragraph in this voice"; chip editor; sticky save with dirty state | Jasper Brand Voice; Writer.com; HubSpot brand kit | `7348dbd4-brand-desktop-light.png`, `b8611143-brand-mobile-dark.png` |
| 11 | My Content | 8 filter controls before the first row (half a mobile screen); US date inputs; icon-only row actions; goal jargon; the Place/Topic column wraps over 4 lines; pieces from one angle not grouped | Medium | One search + "Filters" popover with saved views; locale dates; labelled primary action + overflow; group by tour/campaign | Notion / Airtable views; HubSpot campaigns | `7348dbd4-content-desktop-light.png`, `-mobile-dark.png` |
| 12 | Social Posts (mobile) | Channel tabs overflow with no scroll cue; Instagram cut, Email / Landing Page / Ads hidden | Medium | Scrollable tab strip with cues, or a select under 600 px | Material scrollable tabs; Later mobile | `b8611143-create-social-mobile-light.png` |
| 13 | Publish | Every card repeats "Connect WordPress above to publish"; the "Route" badge is jargon; no scheduling; setup forms push the list below the fold | Medium | One connect banner, then a publish queue with schedule and per-channel status; rename "Route" | Buffer queue; WordPress scheduling | `b8611143-publish-desktop-light.png` |
| 14 | Members | Members appear as an id fragment with no name; banner "Your workspace has no active owner"; invites only via "Request a change" | Medium | Name + masked e-mail; self-serve invite and role change for owners; fix tenants provisioned with no owner | Slack / Notion members | `b8611143-members-desktop-light.png` |
| 15 | Legal (privacy, partner terms) | Draft v0.6 still describes API-key sign-in, removed by AA-1036; a "DRAFT — PENDING LEGAL REVIEW" banner shows in the product | Medium | Update to partner sign-in (password + authenticator); keep the banner only until legal review | SaaS terms pages | `b8611143-legal-privacy-desktop-light.png`, `b8611143-legal-terms-desktop-light.png` |
| 16 | Activity Log | Rows do not name the object; a file download is labelled "WordPress"; sign-ins dominate (159 rows); filter in UTC, list in browser time | Low | Actor · action · linked object; hide sign-ins by default; one timezone | GitHub audit log; Shopify timeline | `b8611143-activity-desktop-light.png` |
| 17 | Create › Write (direct visit) | No H1 (breadcrumb "Write Content" while the sidebar highlights "Social Posts"); dead-end empty state; odd copy about approval | Low | Page title + both entry points (Social / Articles); rewrite the copy | Canva "Create" hub | `b8611143-create-write-desktop-light.png` |
| 18 | Account settings + studio chooser | Mixes "agency" and "studio" vocabularies; company changes only through "Contact us" | Low | One term (workspace); read-only company profile with an edit request | Google account chooser | `b8611143-settings-desktop-light.png`, `b8611143-studio-select-desktop-light.png` |
| 19 | Add-ons | Editor told "Ask your owner" without naming one (and Members says there is none); no add-on price | Low | Name the owner (or support when none); show the price | Atlassian / Slack marketplace request flow | `b8611143-add-ons-desktop-light.png` |
| 20 | Facts | 0 own facts per audit tenant and 1 platform fact; "Use my own" is unclear | Low | Seed suggested facts from the brief; rename to "Override with my value" | Jasper Knowledge base | `7348dbd4-facts-desktop-light.png` |
| 21 | All studio pages (ops) | The agency web runs as a single Fargate Spot task; a Spot interruption gave 503 on 14 consecutive loads until the replacement started (ECS stoppedReason "Your Spot Task was interrupted.") | Medium | Before pilot: 2 tasks, or an on-demand base capacity provider for `aa-crm-dev-web` | Standard ECS HA | none (walk log, not committed) |

**What passed:** no dark-mode contrast defects on reviewed pages; no sideways scroll at 390 px and the bottom nav works;
empty states exist (Facts, Invoices, Create › Write); the AI-assisted notice shows on lists, the piece drawer and publish.

**Not done:** no write action (publish, approve, rewrite, pick topic, connect, save brand), by design. Every desktop-light
primary page plus a sample of dark/mobile variants was looked at by eye; the rest only by the automated metrics. The walk's
raw JSON logs hold page text and stay in the gitignored session folder.

The list feeds the portal UI issues AA-670 (information architecture, items 7, 8, 9, 11, 16–18), AA-668 (writer panel,
items 1, 3, 12, 13), AA-671 (marketplace, items 4, 9) and AA-672 (account pages, items 7, 14, 15, 16, 19).

---

## 12. Follow-up issue proposals (not created)

To be created only after the tech lead approves this report (Linear Free quota: deliverable-sized issues).

1. **fix: T9 blog length contract** — one shared floor constant, `length_short`/`length_long` codes, F4 re-run on stored
   text, floor-aware sentence repair and normalizer.
2. **feat: T9 extend repair for short F4** — section-level expansion from unused seed facts instead of a full rewrite,
   verified on ~3 pieces then the phase 2 set.
3. **fix: T-series job visibility** — typed failure code for failed pieces in the job result, piece status in job views,
   `shared.job.cost_usd` from the ledger.
4. **fix: flag_fix stages on 5.x models** — `stage_model_params` rows for t2_flag_fix / s1_flag_fix, "fix not applied"
   flag, task tag in the quality signal.
5. **chore: judge route order while the primary rung is closed** — serving model first for t2_judge, Debate and
   t10_judge.
6. **feat: market coverage honesty** — unmapped-market record per unsupported country, market settings note, T2 SEO market
   = first supported declared market.
7. **feat: T0 brief import completes the brand pack** — map `system_prompt`, `default_cta`, signature words; list
   unmapped fields on review (the S275 bundle).
8. **design: T7 Debate advisory mode + brand-fit calibration** — rank-only Debate, brand-fit and core-idea labels on the
   AA-729 golden set, deterministic cross-brand overlap.
9. **feat: T7 Blog topic coverage** — tenant-visible no-topic reason, demand-join check for low-demand tours, ≥ 1 Subject
   per adopted tour with a free candidate, incremental slate.
10. **decision memo: seed-aware blog floor** — seed-tier / brand-style floor or a T7 seed minimum for Blog.
11. **ops: agency web HA before pilot** — 2 tasks or on-demand base for `aa-crm-dev-web`, cost stated first.
12. **chore: prompt caching on anthropic-direct** — measure the stable-prefix share, then enable per connection.

The portal UI items go into AA-670 / AA-668 / AA-671 / AA-672 rather than new issues; the Getting-started race (item 6)
and the legal-copy update (item 15) are small enough to ride with those.

---

## 13. Open checks

1. **Failed-piece class:** first token of `held_reason` on e16fbbfb.
2. **84e392c3 slate drop:** the atlas and wildkind `t7_slate` job results for that tour's Segment ids.
3. **Atlas forbidden-word count:** script 2 hits in 1 piece vs F2_brand_forbidden 0 failures (match rule, field, or text
   changed after the gate).
4. **F15_voice timing:** are the 14 failures on attempt 1 only?
5. **Language of DE/FR/NL demand rows:** English or local keywords? The writer writes English for all 4 brands.
6. **Origin of shared T2 text:** how much cross-brand overlap is Master wording.
7. **Which normalizer step shortens text:** chars before and after each step.
8. **Script fix:** `p3_2_stage_ops.py` should match tenant markets after `normalize_markets` (§3.2 artefact).
9. **Phase 1 needs_review/passed pairs** (trail × 84e392c3, wildkind × 84e392c3, wildkind × caf4bf16): reasons not
   measured in the window.
10. **Export file quality:** §4.6 counts export events only (formats, objects); the exported HTML / text / DOCX files
    themselves were not opened or checked in this phase (scope item 4 of AA-741 asks for it).
11. **Human label sheet:** the phase 2 scope names a keep / edit / rewrite label per piece; no such sheet is in the
    phase 0–2 records, so this report has no human verdict beside the gate verdicts.

---

## 14. Method and inputs

- Four read-only scripts ran inside the CIS worker container against the shared Dev database, with the container's
  `DATABASE_URL` (CIS app role), S3-mediated ECS exec. They read catalog-level rows and print counts, class names and
  8-char ids only; text-based computations (word hits, leaks, similarity) run inside the script and print numbers.
- `scripts/p3_1_holds_deep.py` → `data/out_1.txt`: T9/T10 per piece (length, attempts, repairs, codes, seed, ledger,
  discarded attempt), holds, pairs without a subject, T7 slate jobs.
- `scripts/p3_2_stage_ops.py` → `data/out_2.txt`: per-stage funnel, terminal states, jobs, LLM call health, T2 job
  results, t2_flag_fix calls, exports.
- `scripts/p3_3_brand_market.py` → `data/out_3.txt`: brand packs, T2 and blog brand metrics, 5-gram similarity, markets,
  research-cache coverage, keyword quality.
- `scripts/p3_4_cost.py` → `data/out_4.txt`: ledger cost per stage, tenant, unit, held set, P1 vs P2, projection.
- The copies in `data/` drop only the local file path printed on the exec wrapper lines; nothing else was changed.
- Phase 2 records used: `../2026-11-10-S275-session/aa741-phase2/status.txt`, `holds.txt`, `spend.txt`; phase 1 README for
  the P1 comparison; phase 0 README for the T2 cost forecast.
- Code read (`apps/AA-CIS-App` at `5cc016cde`): `services/acp_content_writing/` (`quality_gates.py`, `prompts.py`,
  `service.py`, `length_trim.py`, `sentence_repair.py`, `trip_facts.py`, `f9_policy.py`, `route_table.yaml`),
  `services/acp_shared/` (`slate.py`, `debate.py`, `token_budget.py`), `services/quality/` (`thresholds.yaml`,
  `taxonomy.yaml`, `final_contract.py`), `services/content_generation/` (`flag_fix_node.py`, `grounding.py`,
  `t2_orchestrator.py`, `t2_judge_breakdown.py`, `brand_fit.py`, `judge_node.py`, `t2_brand_claims.py`),
  `services/jobs/t2_rewrite_job.py`, `services/seo_intelligence/seed_builder.py`, `services/acp_angle_gate/prompts.py`,
  `shared/aa_llm/tokens.py`, `shared/llm_client/` (`models.py`, `token_floor.py`, `adapters/anthropic_messages.py`),
  `api/services/tenant_ai_budget.py`.
- Portal walk: Playwright script and logs in the gitignored S276 session folder; screenshots kept outside the public repo.
- Linear AA-741 description and comments (S229 scope, S265 cost approval, S270–S275 phase records).
