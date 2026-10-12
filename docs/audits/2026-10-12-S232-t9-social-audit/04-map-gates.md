# T-series social content path (T7 to T11) on Dev: stage and gate map with live gate behaviour

Code is read from `AA-CIS-App` `main` @ `80101bf` (#673). That includes sentence repair, the F9 token limit of 8192 and the Location field in the seed. The local checkout is now on `main`; the earlier branch `feat/aa-768-sentence-repair` was already merged as #673. Live data covers `acp_shared.content_piece` since 2026-10-12T00:00Z: n=49 pieces, 20 blog and 29 linkedin. LinkedIn is the only social channel in today's data. Everything was read-only. Scripts are `.tmp-session/s232/s232_tmap_gates.py`, `s232_tmap_gates2.py` and `s232_tmap_gates3.py`.

Another session was running scripts at the same time and overwrote the helper's shared `/tmp/r.txt` output. The fix was to have `s232_tmap_gates3.py` upload its own output to S3 under a unique key.

## Main findings

1. **The blog writer runs out of tokens.** `generate.py:41` sets `_MAX_TOKENS = 2048` for the `t9_write` stage (sonnet-4-6). Since 10-12, **20 of 37 blog write calls stopped at `max_tokens`** (`tokens_out` = 2048). None of the 55 linkedin calls did.
   - The blog spec is 800–2,200 words (F4 band 4,700–13,000 chars), which cannot fit in 2048 tokens plus the JSON envelope.
   - 5 of 20 final blogs end mid-sentence. One of them is **approved**: `b533c076` ends "…among other cultural landmarks".
   - This probably feeds F3, the F8 "CTA" criterion (20 blog failures) and CTA_NOT_REFLECTED.
   - It also caps blog length at about 8k chars, so the 13k F4 ceiling can never be reached.
2. **F9_cta_fact is the main reason pieces are held.** It is the held_reason for 20 of 22 held linkedin pieces and 5 of 18 held blogs.
   - It fails in 47/55 linkedin attempts and 35/37 blog attempts, counting discarded attempts.
   - The F9 judge returned non-pass in 85 of 91 `t10_judge` calls.
   - Across 38 failing F9 ledgers there are **129 quoted unsupported_claims**. That is the calibration sample for F9.
3. **The blog structure gate F3 is mostly one rule.** The route-aware variance rule ("no Segment-section ≥1.4× the others") accounts for 20 of 22 F3 violations; the other 2 are "no one-sentence paragraph".
   - The writer is told to make one *section* 1.5× longer. The gate instead sums each Segment's sections, keyed by the first tag in each section, and FAQ and intro sections are included. The rule and the instruction measure different things.
   - Because F3 is blocking, a blog never qualifies for sentence repair: 17/17 blog attempt-2s were full rewrites. The full rewrite then brings new F9 claims, and the regression guard reverted 8 rewrites.
4. **No T-series Jev question can change anything today.** All 9 T7–T10 questions are `mode=shadow` with NULL `accept_floor` and `reject_ceiling` (threshold v0), so every answer since 10-12 landed in the grey zone.

   | stage / question | asks | zone | cost |
   |---|---|---|---|
   | t10 rubric_met | 352 | grey | $0.017 |
   | t10 brand_voice | 88 | grey | |
   | t10 cta_clear | 88 | grey | |
   | t10 faq_restates | 105 | grey | |
   | t10 offer_as_certain | 0 | | |
   | t10 same_piece | 0 | | |
   | t7 topic_fits_brand | 272 | grey | |
   | t8 angle_answers | 7 | grey | |
   | t9 fact_relevant | 15 | grey | |

   No Jev question checks claims at T9/T10.

## Stage map

| Stage | file:line | What it does | Type / model stage key | On failure | Weaknesses |
|---|---|---|---|---|---|
| T7 Bar | `acp_shared/slate.py:66` (CHANNEL_BARS), `:121` `_clears_bar` | Blog needs demand ≥1000 and questions ≥3 (Route grain). LinkedIn/FB/IG/TikTok need said ≥150 (Segment grain). Email/LP/Ads always pass. | Deterministic | Candidate not proposed; stale `proposed` row deleted | `seen_places` is shared across channels (`:478`), so later Segment channels (FB/IG/TikTok) only get the places earlier channels did not take. `most_per_hub=99` means no cap. |
| T7 `_choose` | `slate.py:339` | Strongest first: one place per channel, hub cap | Deterministic | Skip | Ties are broken by id |
| T7 Debate (contested) | `debate.py:194` `apply_debate` | `atom_segment.contested ≥ CONTESTED_CUT_THRESHOLD` | Deterministic, Segment only | Cut, capped at `MAX_CUT_FRACTION=0.5` (`:51`) | Routes are never checked for contested |
| T7 Debate (brand-fit) | `debate.py:187` t7_prefilter, then `score_candidate_fit` | Jev `t7_topic_fits_brand` first (stage `t7_debate`, shadow); on a cache miss, Luna brand-fit (`t7_debate_judge`, gpt-5.6-luna) | Jev + LLM, cached per brand_version | Score < 7.0 (`:159`) → cut, within the 50% cap. An error lets the candidate pass. | Jev is shadow, so Luna always runs on a miss. The LLM call is synchronous inside async code. A Jev accept is not cached. Job `t7_slate`: concurrency 2, ~3–4′ per tenant. |
| T8 angle generation | `acp_angle_gate/service.py:111`, `generate.py:120` | 3 angles from goal + brand + DFS PAA + piece history | LLM `t8_angle_gen` (sonnet-4-6, 2048 tokens), json-repair, no re-ask | Job fails, then `clear_goal` | Seed is `atom["text"]` (`service.py:159`), the short label. T9 now uses the richer `atom_seed_text`. Routes see one representative atom only. |
| T8 ranking | `ranking.py:79` rank_angles, `:118` verify_answers | Sort by fewest channel avoid-list violations, then most verbatim PAA matches; Jev `t8_angle_answers` per (angle, question) | Deterministic + Jev (shadow) | Changes the recommended index only | Runs only when the channel is known. Jev never drops anything (shadow). |
| T9 pre-flight | `content_writing/service.py:245` start_write | Status approved, channel set, chosen angle, CTA (`MissingCTAError` → 422), seed built (atom_seed_text or joined route segments), placeholder row | Deterministic | HTTP 404/409/422 | Because the CTA is checked here, F6 can never fail later |
| T9 facts | `service.py:454` resolve_facts, `facts.py:77` | Facts Entry list; Jev `t9_fact_relevant` per fact | Jev (shadow) | Fails open | Shadow, so every fact is injected |
| T9 write | `generate.py` write_content (`:113`), `service.py:547` | Attempt 1. Blog returns a JSON envelope `{seo_title, meta, slug, body}`. | LLM `t9_write` (sonnet-4-6, max_tokens **2048**) | Exception → status `failed` | **Blog truncation (finding 1)** |
| T9 SEO fit | `service.py:209` `_fit_seo_meta` | Deterministic trim of title (≤60) and meta (120–158); keeps the keyword | Deterministic | Keeps the original | F4_seo still fails 9/37 blog attempts (8 meta-length, 3 title-length violations) |
| T9 attempt 2 | `service.py:565` + `sentence_repair.py:57` plan | If **every** blocking failure is F1 or F9-with-claims, repair only the flagged sentences; otherwise a full rewrite with all blocking violations as feedback (`_repair_feedback`, `:234`) | LLM `t9_write` (same key; `quality_signal.mode=sentence_repair`) | A failed repair parse falls back to the full rewrite | Live: sentence repair 5 times (linkedin only), full rewrite 38 times (17 blog, 21 linkedin). Blog never qualifies because F3/F4/F5 almost always co-fail. |
| T9 regression guard | `service.py:676` | Revert attempt 2 if it newly fails a gate and is not net-better | Deterministic | Keep attempt 1 | Fired 8 times |
| T9 hold decision | `service.py:715` | Hold if first_failure is not repairable or attempt ≥ `MAX_ATTEMPTS=2` (`:63`) | | status `held`, held_reason = first blocking gate + up to 3 violations (`:187`) | |
| T9 buffer retry | `service.py:830` / `:886` | One extra full rewrite into a new piece row if the hold was repairable and the request has no other piece | LLM | The new piece stays held | Skips F10 (no cannibalization match passed), Jev observation, sentence repair and the regression guard. Stores no embedding, so an approved retry piece is invisible to F10 and reuse checks. Recorded as `attempt_number=1`. Never fires when the request already has a piece, which covers every rewrite or rerun of the same request. If the worker dies mid-retry, the new piece stays `processing` because `on_terminal` only covers the original piece. |
| T10 Jev observer | `jev_observe.py:81` | Asks T10-1…5 per attempt, logged next to the gates | Jev stage `t10_gates`, shadow | Never changes an outcome | All grey (finding 4). Runs inside the job (~2s per job). Today: 633 calls, $0.035. |
| T11 export | `export.py` | Text for every channel; HTML (markdown) for blog only | Deterministic | | |
| T11 publish | `api/routers/v1_publish.py:281`, `:224` | Only `status='approved'` can publish; channels are only `("blog", "facebook")` (`:63`) | Deterministic | 422 "edit it in My Content first" | **LinkedIn cannot be published.** WordPress gets `seo_title` = angle name and `seo_meta=""`, so the SEO title and meta that T9 wrote and F4_seo checked are thrown away. A tenant edit (`service.py:1179`) never re-runs the gates or changes status, so a **held piece can never be published**, and no admin path to clear a hold was found. Edits to an approved piece skip every gate. The portal shows `held` as `ready` (`_READY_STATE_MAP`). |

## T10 gates

The gates are called from `run_quality_gates` (`quality_gates.py:869`) in this fixed order. F6 short-circuits the rest when it fails. `first_failure` is the first failed gate with `blocking=True`. All gates check `atom_text = _grounding_text(context)` (`service.py:191`), which is the seed plus the Facts block plus BRAND/AUDIENCE/TRIP/DESTINATION lines.

| Gate | file:line | Checks | Type | Blocking / repairable | Channels | Final-attempt fails (blog / social) | All attempts incl. discarded (blog / social) | Held reason count (blog / social) | Weaknesses |
|---|---|---|---|---|---|---|---|---|---|
| F6_cta_present | `:223` | CTA not empty | Deterministic | Blocking, not repairable | All | 0/20, 0/29 | 0/37, 0/55 | 0 | Dead in practice: start_write already returns 422 |
| F1_grounding | `:237` | Per sentence, any number not in the source (`find_novel_numeric_claims`) | Deterministic | Blocking, repairable (sentence-repair eligible) | All | 3/20, 2/29 | 6/37, 3/55 | 3 / 2 | Numbers only. A unit conversion or sum counts as a failure; T3 has a Jev path that clears these, T10 does not. |
| F2_banned_patterns | `:260` | 21 regexes; a match found in the source is exempt | Deterministic | Blocking, repairable | All | 0 | 0 | 0 | Exemption is checked against seed + facts |
| F10_cannibalization_cross_tenant | `:277` (+ `service.py:596` embedding) | Cosine ≥0.92 against another tenant's approved piece | Deterministic over embeddings | Blocking, repairable | All | 0 | 0 | 0 | Compares against approved pieces, not published ones. Skipped on the buffer retry. |
| promises_an_option | `:321` | If the source has "offered" words, every sentence without a hedge is flagged | Deterministic | **Warn** (not blocking, not repairable) | All | 0 | 0 | — | The offered check reads the whole grounding text, so a Fact containing "optional" or "supplement" would flag every sentence |
| F4_extreme_length | `:432` | 20–6000 chars; blog 4700–13000 (tags stripped) | Deterministic | Blocking, repairable | All | 0 | 0 | 0 | The blog upper bound cannot be reached with 2048 tokens |
| F4_seo_surface | `:453` | Title ≤60 with keyword; meta 120–158, ends as a sentence, has keyword; slug kebab-case ≤60 | Deterministic | Blocking, repairable | Blog | 5/20 | 9/37 | 3 | Value is discarded at publish anyway (T11) |
| F5_atom_density | `:735` | Each 300-word window has ≥1 `[R:]`/`[F:]` tag | Deterministic | Blocking, repairable | Blog | 2/20 | 5/37 | 2 | AA-768 now allows background knowledge, which carries no tag, so pressure on this gate is higher |
| F3_structural_variance | `:765` | ≥1 one-sentence paragraph; Segment/section ≥1.4× the others; ≤1 bullet list | Deterministic | Blocking, repairable | Blog | **10/20** | **22/37** | 5 | Finding 3 (prompt and gate measure different things) |
| F7_faq_dedup | `:832` | A FAQ answer whose tokens overlap the body by >85% fails | Deterministic | Blocking, repairable | Blog | 0/20 | 6/37 | 0 | Within one piece only |
| F8_framework | `:530`, downgraded at `:937` | Goal rubric items scored 1/0 with an evidence quote | LLM `t10_judge` (gpt-5.6-luna, fallbacks gpt-6-luna, max_tokens 2048 default) | **Warn** | All | 12/20, 1/29 | 26/37, 3/55 | — | Mostly the "CTA" criterion on blog (20), probably from truncation. Token limit is still 2048 on the Luna route, while F9 was raised. |
| F9_cta_fact | `:584` (`_F9_MAX_TOKENS=8192` at `:581`) | CTA_NOT_REFLECTED or FACT_CHECK_MANUAL_CHECK, judged with the SOURCE shown. A FACT flag only counts if `unsupported_claims` names the claim and why. | LLM `t10_judge` (same call as F9_brand_style) | Blocking, repairable; judge unavailable counts as a fail | All | **18/20, 21/29** | **35/37, 47/55** | 5 / **20** | Over-literal (finding 2). Final kinds: FACT 15 blog / 20 social; CTA+FACT 2 / 1; judge unavailable 1 blog. 4 F9 calls hit 2048 tokens before #672 deployed (~10:09–10:37 UTC), none after. |
| F9_brand_style | same call | SUMMARY_OFF_BRAND, GENERIC_AI_WORDING | LLM | Warn | All | 1/20, 8/29 | 2/37, 18/55 | — | |

Gates never seen failing today: F2, F4 length, F6, F10, promises_an_option.

## Live distributions (since 2026-10-12, 5 pilot requests rerun)

| | Blog | Social (linkedin) |
|---|---|---|
| Approved | 2 | 7 |
| Held | 18 | 22 |
| Failed / processing | 0 | 0 |
| attempt=1 | 3 (1 approved) | 3 (1 approved) |
| attempt=2 | 17 (1 approved) | 26 (6 approved) |
| Attempt-2 mode | full rewrite 17 | full rewrite 21, sentence repair 5 |

By tenant:

| Tenant | Blog (approved / held) | LinkedIn (approved / held) |
|---|---|---|
| atlas-hearth | 2 / 8 | 2 / 8 |
| terra-family | 0 / 10 | 2 / 8 |
| trail-pulse | — | 3 / 6 |

- Six pieces have attempt=1 and an empty repair_log. Four of them are held, and a held piece from the main loop always has a repair_log, so those four are buffer-retry pieces.
- The gate targeted at attempt 1:
  - Linkedin: F9_cta_fact 25, F1 1.
  - Blog: F3 4, F4_seo 4, F1 3, F9 3, F5 2, F7 1.
- Jobs since 10-12, all succeeded: t9_write 45, t8_angles 2, t7_slate 1.

**Cost since 10-12:**

| Stage | Calls | Cost |
|---|---|---|
| t9_write blog | 37 | $1.45 (about $0.072 per piece) |
| t9_write linkedin | 55 | $0.61 (about $0.021 per piece) |
| t9_write sentence repair | 5 | $0.018 |
| t10_judge | 196 | ~$0.29 |
| Jev (t10_gates) | 633 | $0.035 |

**Model routes** (`llm_role_config`):

| Stage | Model |
|---|---|
| `t9_write` | claude sonnet (no fallback) |
| `t8_angle_gen` | claude sonnet (no fallback) |
| `t10_judge` | gpt-5.6-luna, fallbacks gpt-6-luna / gpt-6-luna-openai, gpt-6-luna shadow at 10% |
| `t7_debate_judge` | same as `t10_judge` |

Jev allowlist: terra-family, trail-pulse, wildkind-travel, atlas-hearth, all added 10-12.

## Using Jev in T9/T10

- **Calibrated question to reuse:** `a1_claim_supported` (a Noul question: "is every fact in this sentence stated or clearly implied by the source?"). It is already enforced in A1 and in T3 (`acp_produce/tenant_pipeline.py:94`, `t3_jev_clear`). That path only clears hits: accept ≥0.85 (≈97% precision per `docs/calibration/a1_claim_supported.md`) and no reject floor, so Jev never adds a violation.
- **Drop-in for T10:**
  - For each F9 `unsupported_claims` sentence, and each F1 numeric hit, ask `a1_claim_supported` with `{source: grounding_text, sentence}`.
  - A confident accept removes the claim.
  - This targets the over-literal paraphrase flags ("ordered it built" when the source says "built by"). It does not touch allowed background knowledge, which Jev would mark unsupported and so leave flagged.
- **Cost:** about $0.0001 per ask.
- **Calibration data:** the 129 logged claims can be labelled and checked offline against Jev probabilities first, using AA-701 / AA-768 data.
- **Existing T10 Jev questions:** they need calibration records (floors) before any of them can act. T10-1 rubric_met (352 logged answers) is the cheapest replacement for the F8 Luna call.

## Other open gaps on the T path

- Blog token limit (`generate.py:41`).
- F3 rule redesign, or downgrade to warn (product decision).
- No hold-clear or re-check path after a tenant edit.
- Publish drops T9's SEO title and meta.
- Publishing works for blog and facebook only; linkedin and the other 5 channels cannot be published.
- Buffer-retry gaps listed in the stage map.
- T8 angle seed is the short atom label.
- G7 (48 combos) has not been run.