# T-series next-step plan after S234, corrected by the critic

Base: AA-CIS-App `main` @ 20a2387 (api :568 / worker :123). The numbers come from these sources, all re-checked:
- S234 rounds r1–r4: 4 rounds of 20 pieces each (12 LinkedIn + 8 blog), in `.tmp-session/s234/analysis_r*.json` and `pieces_r*.json`
- `.tmp-session/s234/explain/fr_report.md`
- `explain/fr_guard_out.json`
- `explain/jev_audit.json`
- panel reports `07-panel-round4.md` and `04-panel-round3.md`

There are 3 Linear projects: **CIS Core — Pipeline, LLM & Platform**, **CIS Portal — Admin & Tenant UI** and **TripPlanner & AA-Booking**. Every item below belongs to CIS Core except #10. Any item marked NEW needs Nghiệp's approval before a Linear issue is created. Each NEW item also says which existing issue it can attach to instead.

---

## 0. Already decided by Nghiệp in this request (run first)

1. **Merge the duplicate place cards: 8 groups, 11 extra cards, plus delete 1 orphan card.** The DRY RUN is in `.tmp-session/s234/merge_dups.py`. Nghiệp approved the run ("chạy luôn đi"). Steps, following `skill/aa-cis-schema/references/destructive-ops.md`:
   - re-run the DRY RUN and confirm the same 8/11/1 counts;
   - back up the affected rows to S3;
   - apply the merge in one transaction;
   - SELECT after, to verify;
   - log the result in AA-772.

   This must finish before #2 and before checkpoint r5, so the seeds are stable when we measure.
2. **Turn off Jev on `t10_gates`.** Nghiệp said "turn it off if it is not effective". The data shows it is not:
   - 2,941 calls in 14 days, all in the grey zone;
   - 0 verdicts acted on;
   - $0.198 spent;
   - AUC 0.57–0.66 on 3 questions, and 0.36 (inverted) on `t10_faq_restates`.

   The exact steps are in §5.

---

## 1. Decision summary

1. **LinkedIn is commercially ready as "draft plus light AA edit"** for 3 brand–seed cells: Terra Tiger's Nest, A&H Punakha and WildKind Punakha (panel r4 §"ship", `07-panel-round4.md:75`).
   - r4 results: 10/12 approved, 10/12 light, $0.026 per piece.
   - **Trail Pulse is not included yet.** Both r4 false passes (#6 at 111 words, #11 at 117 words) are under the 120-word floor. Its brand voice also needs redefining in T0 (§ business advice).
   - The light edit is done by AA or the content team in the **admin** Cut/Rewrite drawer (AA-769). Tenants see content only, never flags or held reasons (standing decision).
2. **Blogs keep being delivered to tenants**, as the standing rule says: tenant always receives content, QA lives only in admin.
   - We make **no commercial quality promise** on blogs until a checkpoint reaches **≥4/8 light and ≤3/8 held**.
   - r4 blogs: 1/8 approved, 1/8 light, 0 as-is, 8/8 needed 3 attempts, $0.104 per blog (pool mean $0.094).
3. **Why blogs fail: a product-truth defect that starts at the writer's input**, not at the gates:
   - optional moments are presented to the writer as included;
   - "visiting/practical" place-card facts read as trip promises;
   - style-guide sentences get copied as facts.

   Pooled S234 blog holds total 22: F9 10, F16 6 (r2 only, fixed since), F17 3, F1 1, F4 1, F13 1. In r4 the blog holds were 7: F9 3, F17 3, F13 1. Fix the input first (#1–#3), then the repair behaviour (#4).
4. **Jev:** `t10_gates` goes OFF (approved). Turning off the rest of the T-axis Jev for the 4 AA test tenants is a **recommendation that still needs Nghiệp's yes** (§5). All A-axis Jev that acts stays on enforce.

---

## 2. Issue list (in order of work)

### #1 Carry each moment's offered/included status into the writer seed
- **Project / link:** CIS Core. Extends AA-768.
- **Problem:**
  - `promises_an_option` warned on 8/8 r4 blogs and on 32 final pieces in the pool.
  - F17 "optional-as-plan" fired 15 times in the pool; "visits to local nomadic families" fired 5 times.
  - The seed shows "take boat rides on the water" as if included, while the source says "Optional activities include…" (`atom_seed.py:272-298`).
- **Scope:**
  - `services/acp_shared/atom_seed.py` `compose_seed` (:169-198) and `compose_route_moment` (:272-298): match `quality_gates._OFFERED_PHRASES` (:88-96) at **sentence level**, only against the evidence sentence that names this moment's label. Evidence can hold several sentences. A day-level match would mark included moments as OFFERED, which causes reverse flips.
  - Append a `Status:` line (text in §3.4).
  - `compose_seed`'s docstring (:177-180) says the line prefixes are a **parsing contract for F9 v2** (`claim_rules.number_source_lines`). So: update the round-trip test, and make sure `moment_fact_count` does **not** count the `Status:` line as a fact (otherwise THIN tagging shifts).
  - `prompts.py`: the §3.1 rule.
  - Update `tests/unit/test_aa768_atom_seed.py` and the byte-identical guard in `tests/unit/test_aa771_s234_voice_contract.py` on purpose.
- **Done when** (r5, n=20, same 6 requests):
  - "optional-as-plan" F17 at **0** in final ledgers;
  - `promises_an_option` warn on **≤2/8** blogs (from 8/8);
  - **0** reverse flips found by the panel.
- **Estimate:** S. **Cost:** $0 per piece.
- **Note:** chị Thư's repo keeps offered moments as a stored set (`offered_moments` table, `write.py:656-670`), not as text parsing. Our parsing is the interim step; §4 build 1 has the stored version.

### #2 Keep "visiting"/"practical" place-card facts out of the writer seed
- **Project / link:** CIS Core. Extends AA-772. **Depends on §0.1 (card merge).**
- **Problem:** r4 blogs repeated card facts as trip facts:
  - the permit sentence: 7/8 blogs;
  - "Access requires a multi-hour horse or reindeer ride…": verbatim in 2 pieces, and the panel's #16 orphan;
  - an invented "rim walk";
  - "visitors may witness [shamanic practice]".
- **Scope:**
  - `atom_seed._card_facts` (:112-116) currently throws away `kind`. Add `WRITER_FACT_KINDS = {what_it_is, history, setting, naming}` and filter on `f.get("kind")`. First check on Dev that stored card facts actually carry `kind`; without it the filter drops everything.
  - The admin card view keeps all kinds.
  - Drafter prompt `place_cards.py:90-92` (§3.5), for new cards only.
  - Re-count thin moments (`THIN_FACTS = 3`, `atom_seed.py:47`) on the 6 standard requests offline, and report before deploy.
- **Done when:**
  - permit/access sentences in **0/8** blogs;
  - panel "invented sub-activity" in **≤1/8** blogs;
  - the thin-moment count changes on ≤2 of 6 requests, or the change is shown to Nghiệp.
- **Estimate:** S. **Cost:** $0.

### #3 Fence the style guide as "never a source", and add an F17 `pace_promise` finding
- **Project / link:** CIS Core. Extends AA-771.
- **Problem:** pace sentences per round r1→r4. Recounted with the proposed regex over sentences in `pieces*.json`, because the plan's original counts were not reproducible from any stored script:

  | Brand | r1 | r2 | r3 | r4 |
  |---|---|---|---|---|
  | Terra | 6 | 11 | 15 | 12 |
  | Atlas & Hearth | 5 | 2 | 7 | 3 |
  | Trail Pulse | 7 | 7 | 7 | 7 |
  | WildKind | 0 | 0 | 0 | 0 |

  Examples: "builds journeys so that active discovery is balanced with time to rest", "full without being relentless".
- **Scope:**
  - `brand_pack.render_brand_block` (:124-126): the §3.3 wording.
  - `trip_facts.py`: a new F17 finding kind `pace_promise`. It fires on a sentence that matches `\b(pace[ds]?|relentless|exhaust\w*|rest(?:ful|ing)?|rush\w*|manageable|balanced?)\b` and whose content words are not in the seed. It is blocking on blogs and cheap-repairable; `F17_trip_fact` is already in `CHEAP_REPAIR_GATES` (`quality_gates.py:1388`).
  - **Before wiring it, replay the regex offline on `pieces_r4.json`.** The 7 Trail Pulse hits per round may be legitimate seed-backed sentences, and a false-positive rule creates new holds.
- **Done when:**
  - r5 Terra pace sentences **≤2** (from 12);
  - A&H **≤1** (from 3);
  - **0** holds whose only reason is `pace_promise` on a seed-supported sentence.
- **Estimate:** S (prompt) + S (rule). **Cost:** about +$0.002 per affected piece (Haiku repair).

### #4a Fix: an F4-only ledger triggers a full Sonnet rewrite
- **Project / link:** CIS Core. Attach to AA-768 (no new issue needed).
- **Bug:**
  - `_seo_fields_only` (`sentence_repair.py:102`) removes `F4_seo_surface` from `failed`, so `failed == []`.
  - The `[]` return at :118-119 only fires when some **non-F4** blocking gate exists. An F4-only ledger therefore falls through to `return None` at :120.
  - `None` sends `service.py:1262-1271` to the `rewrite_with_feedback` full rewrite. The comment at :114-116 says this should never happen.
- **Scope:** in `plan()`, when every blocking gate is `F4_seo_surface`, return `[]` (the "seo_fields" mode at `service.py:1219-1223`). Add a unit test.
- **Done when:** the test passes. No F4-only full rewrite appears in r5 `repair_log`.
- **Estimate:** XS. **Cost:** saves one Sonnet rewrite per F4-only blog.

### #4b Keep F9 verdicts on unchanged sentences; cut a truth fault instead of rewriting it
- **Project / link:** CIS Core. **NEW, needs approval**; it can attach to AA-768 instead.
- **Problem:**
  - 19/97 sentence retries (20%) added a new blocking fail (regressions: F9 18, F14 1, F17 1).
  - The guard reverted 16 times.
  - In `fr_guard_out.json`, 15 of 38 newly flagged quotes, across 10 of 15 pieces, were sentences the judge had passed one attempt earlier, unchanged.
  - Sentence repair fixes F9 34/69 (49%). Full rewrite fixed F9 0/1 in S234, and 0/6 across S233+S234.
- **Scope:**
  - F9 judge path (`quality_gates.py:733-883`): normalise each flagged quote (strip tags, casefold, collapse whitespace). If it is in a per-job `f9_passed_sentences` set built from earlier attempts, drop the claim and log `F9_sticky_pass`. Pass the set as a new kwarg through `run_quality_gates` (`service.py:1360-1372`).
  - **Cut policy on blogs:** today `delete_flagged` (`sentence_repair.py:306`, which already calls `tidy_after_cut` at :332) runs only on attempt 3, after a failed repair call (`service.py:1244-1250`). Change it so that on attempt 3, an F1/F9 truth item still failing after one sentence repair is **cut** instead of reverted or held.
  - Attempt 2 stays as sentence repair. About 28% of F9 flags are false (F9 v2 replay), so cutting on the first retry would delete good sentences.
  - `splice_checked`'s existing pronoun-referent guard covers orphans. Extend it to section-opening "Access/This/These" only if r5 still shows orphans.
- **Done when** (r6, n=20):
  - "retry added a blocking fail" **≤8%** (from 20%);
  - guard reverts **≤6** per round (from 16 pooled);
  - blog F9 holds **≤1/8** (r4: 3/8);
  - **0** blogs below `_BLOG_MIN_CHARS = 4700` (`quality_gates.py:472`) because of cuts.
- **Estimate:** M. **Cost:** about −$0.01 per blog.

### #5 Em-dash: deterministic autofix first, then prompt cleanup, then a residue guard
- **Project / link:** CIS Core. Extends AA-771.
- **Problem:**
  - 182 / 195 / 200 / 182 em-dashes per 20 pieces; r4 is 14.2 per 1,000 words, with 19/20 pieces containing one.
  - Panel AI-tells score is 4.75/10.
  - Our prompts prime the habit: `acp_content_writing/prompts.py` 78, `acp_angle_gate/prompts.py` 28, `channel_spec.py` 25, `brand_pack.py` 8 em-dashes.
- **Scope, in this order:**
  1. A `hygiene.autofix` (`hygiene.py:1944`) em-dash step:
     - " — X — " becomes ", X,";
     - a trailing " — X." becomes ": X." when X has no verb, otherwise ". X." with X capitalised;
     - anything else goes to residue.
  2. Strip em-dashes from prompt text (not code comments) in the 4 files.
  3. The §3.1 rule.
  4. Add `r"\u2014"` to `_BANNED_PATTERNS_SEED` (`quality_gates.py:154-163`) **only after** the offline check shows the autofix clears ≥95%. Otherwise F2 blocks 19/20 pieces at attempt 1 and pushes them into the repair loop, which is the 20%-regression path.
- **Correction to the original plan:** the contrast-frame regexes (`hygiene.py:1400-1411`) already accept `[,;:—–]` as the hinge, so comma or colon replacements still match. No re-baseline is needed. Run the autofix **after** the contrast-frame detection, or confirm the counts are unchanged.
- **Also check:** em-dashes inside tenant brand-pack text (style guide, good examples) are T0 data and are not fixed here. Count them, and report to Nghiệp.
- **Done when:**
  - offline `measure_r4.py` on `pieces_r4.json` with the autofix gives **0** em-dashes and **0** new comma splices in a 20-sentence sample;
  - live r5: **<1 per 1,000 words**;
  - panel AI-tells **≥5.5**.
- **Estimate:** S-M. **Cost:** $0.

### #6 FAQ: People Also Ask (PAA) questions first, and each answer names its subject
- **Project / link:** CIS Core. Extends AA-768.
- **Problem:** FAQ non-answers in r4 #5, #17 and #19 ("Who are the Tsaatan?"). F16 itself is solved (r2: 7 holds; r3/r4: 0).
- **Scope:**
  - The snapshot is `asdict(search_demand)` (`acp_angle_gate/service.py:220`). So `dfs_snapshot["people_also_ask"]` exists next to `related_keywords` (read at `service.py:924-925`).
  - Filter it by scope places and seed nouns, then pass it as `paa_questions` into `write_faq` (`generate.py:447`), called at `service.py:643-646`.
  - `_FAQ_SYSTEM` (`generate.py:431-444`): the §3.6 text.
  - A deterministic subject check next to F16 (`quality_gates.py:1280-1290`): drop a pair whose answer does not name the question's head entity, while ≥3 pairs remain; otherwise run one regeneration.
- **Done when:**
  - the panel finds **0** FAQ non-answers in 8 blogs;
  - F16 holds stay at **0**;
  - ≥1 PAA question is used in ≥4/8 blogs whenever the snapshot has one.
- **Estimate:** S-M. **Cost:** +$0.

### #7 LinkedIn: 120-word floor, Trail Pulse voice, broetry, stock lines
- **Project / link:** CIS Core. Extends AA-771.
- **Problem:**
  - Both r4 false passes (#6, #11) are under 120 words.
  - Trail Pulse has been a false-pass cell in every round.
  - "That's not filler. That's structure." is broetry.
- **Scope:**
  - `gate_social_shape` (`quality_gates.py:1396-1420`): `n < lo` becomes blocking, **on attempt 1 only**, like `stock_blocking` (`service.py:1368`). That gives one rewrite and avoids a full-rewrite loop.
  - `channel_spec._LINKEDIN_AVOID` (:184-187) and the `CONSUMER_SOCIAL` row (:192-197): §3.7.
  - Add to **both** `STOCK_PHRASES` (:138-142) and `STOCK_PATTERNS` (:143-157), because F15 reads `STOCK_PATTERNS`. New lines: "not filler", "worth pausing on", "is not a backdrop", "does not perform", "tolerates them", "isn't an inconvenience". "worth sitting with" is already in both lists.
  - F15_voice_warn: ≥2 consecutive sentences of ≤5 words.
- **Done when:**
  - LinkedIn **≥11/12 light** with **0 false passes**;
  - Trail Pulse light **3/3**;
  - stock tells in ≤8/20 pieces.
- **Estimate:** S. **Cost:** about +$0.004 per short post rewritten.

### #8 F9 v2: fix claim classification, then replay
- **Project / link:** CIS Core. Extends AA-768.
- **Problem:** the replay caught 71–75% of real problems and cleared 72% of false flags. It was 38/38 stable and 55% cheaper, but it is below the 90% bar. The errors are misclassified `place_background` and `opinion` claims.
- **Scope:** `claim_rules.py` classification for those two classes. Re-run `f9v2_replay.py` on `f9v2_replay_sets.json` **as a one-off ECS task**, not `nohup` inside the api task.
- **Done when:** catch rate **≥90%** and false-flag clearing ≥80%. Only then wire it into the gate, in a separate PR.
- **Estimate:** M. **Cost:** replay about $0.40.

### #9 A/B a cheaper model for blog `t9_write`
- **Project / link:** CIS Core. **NEW, needs approval** (or attach to AA-768).
- **Problem:** `t9_write` across all channels is $2.551 of $4.231 in the S234 pool (60%, 82 calls). The blog-only share is not broken out. A blog costs $0.094 pool mean and $0.104 in r4, against $0.026 for LinkedIn.
- **Scope:**
  - An adhoc script modelled on `pc_ab_luna.py`: the same 8 blog requests, gpt-5.6-luna against Sonnet, through `LLMClient.generate()`, `stage="adhoc_aa<issue>"`, `role=writer`. Run it as a one-off ECS task.
  - Blind panel, same rubric.
  - If the cheaper model wins: change the role in `shared.llm_role_config` (admin edit).
- **Done when:**
  - across the 8 pairs, the cheaper model's light count is ≥ Sonnet's and its held count is ≤ Sonnet's + 1;
  - blog cost **≤$0.06**.
- **Order:** after #1–#4b are deployed.
- **Estimate:** M. **Cost:** about $1.20 (8 pairs; within the subset rule).

### #10 Human calibration of the panel rubric (10 pieces)
- **Project / link:** CIS Portal, or a non-code task. **NEW, needs approval.**
- **Scope:** export 10 r4 pieces (5 LinkedIn, 5 blog) plus the rubric to the AdventureAsia GDrive folder for chị Thư or the content team. Compare their votes with the panel's.
- **Done when:** human-vs-AI agreement is reported, and the light threshold is reset if humans are stricter by more than 1 label in 10.
- **Estimate:** S. **Cost:** $0.

### Small chores (one PR, attach to AA-768)
- Remove the `observe_t10` call at `service.py:1383-1387` and its import at :55 (§5).
- Remove the dead `facts.select_relevant_facts` and `T9_STAGE` (`facts.py:76-107`). Its only caller is `tests/unit/test_aa700_t7_t8_t9_jev.py:65,81`; update that test. Fix the stale comments at `service.py:938-939` and `:1085`.
- `rewrite_with_feedback` docstring (`generate.py:242`) still says "cap of 2"; `MAX_ATTEMPTS = 3` (`service.py:74`).
- Add `concurrency: { group: deploy-dev, cancel-in-progress: false }` to `.github/workflows/deploy-dev.yml`. It has none today.

**AA-763** (G4 T-series stage key) keeps waiting for the natural S1 job.

---

## 3. Prompt changes (paste-ready)

The blog prompt has a byte-identical guard in `tests/unit/test_aa771_s234_voice_contract.py`. Update it on purpose in the same PR.

### 3.1 `prompts.py` `SYSTEM_PROMPT` (:175-224)
- **Insert before** the line at :217 (`- Avoid generic AI-style writing: …`):
  ```
  - Never use an em-dash (—). Not in the body, not in a heading, not in the title, meta or FAQ. A comma, a full stop or a colon says the same thing.
  - A moment whose Status line says OFFERED, NOT INCLUDED is described as a choice ("there is time to…", "you can choose to…"), never as something the reader will do. A moment whose Status line says included is never called optional, extra or "if you wish".
  ```
- **Ship with #1:** the second rule refers to the Status line, which only exists once #1 is in.
- **Source:** chị Thư's `src/aa_social/stages/write.py:93-94` and `:665-670`.

### 3.2 `_BLOG_FORMAT_INSTRUCTIONS` (:47-71) and `_BLOG_FORMAT_INSTRUCTIONS_ROUTE` (:78-107)
- **Append after** the "Vary the rhythm" bullet (:61 and :92):
  ```
  - Open with the specific, not the general: the first sentence names a place or a seed detail, with no throat-clearing. Never print the angle's name as a heading.
  - The closing paragraph is a next step (the call to action), not a summary of the piece, and it has no heading of its own.
  ```
- **Source:** `reference/channels.toml` (blog structure).

### 3.3 `brand_pack.render_brand_block` (:124-126)
- **Replace with:**
  ```python
  lines.append("Style guide: follow every rule in it, including each \"do not\". How this brand writes, in its own words. This is style and never a source: never cite it, never repeat one of its example sentences, and never state its claims about pace, rest, balance or difficulty as facts about this trip unless the content seed says so.\n" + pack["style_guide"])
  ```
- **Source:** chị Thư's `write.py:116-118`. The good-examples line (:128-129) already says "do not copy its sentences".

### 3.4 Seed line in `atom_seed` (data, not prompt)
- **Offered moment:**
  ```
  Status: OFFERED, NOT INCLUDED (the itinerary says: "<offered sentence>"). Describe it as available, never as something the reader will do.
  ```
- **Included moment** on a day that also has offered items:
  ```
  Status: included in the trip. Never call it optional.
  ```
- Keep it out of `moment_fact_count`, and add `Status:` to the F9 v2 prefix contract.

### 3.5 `place_cards.py:90-92` (drafter, new cards only)
- **Replace with:**
  ```
  history and era, its setting and what is physically there). Never write how visitors reach it, what visitors do or see, permits or access, or safety advice: those are trip facts and come only from the itinerary. kind is one of: what_it_is, history, setting, naming.
  ```
- **Source:** chị Thư's ADR 0012 (`docs/adr/0012-facts-are-hand-written-not-fetched.md`).

### 3.6 `generate._FAQ_SYSTEM` (:431-444)
- **Replace** the "Each question is one a reader…" bullet with:
  ```
  - When SEARCH QUESTIONS are given, prefer them: take one only if a SOURCE fact answers it, and never invent a question that sounds like one. Otherwise write the answer's SOURCE fact first, then the question that fact answers.
  - Every answer names the subject of its question (the place, people or thing asked about) and answers it in its first sentence.
  ```
- **Replace** "One or two sentences per answer," with `40-60 words per answer,` and keep the rest of that bullet.
- **Source:** chị Thư's `write.py:96-102` and `reference/gate-thresholds.toml:68-69`.

### 3.7 `channel_spec.py`
- **`_LINKEDIN_AVOID` (:184-187):** append
  ```
  , the one-line-per-paragraph broetry cadence, two short maxims in a row ("That's not X. That's Y."), humblebrag framing
  ```
  Keep each item free of commas inside it; `ranking.split_avoid_phrases` splits on commas (:136-137). Reword the parenthesised item without a comma if needed.
- **`CONSUMER_SOCIAL` "structure" (:194-195), replace with:**
  ```
  One-sentence hook that states the observation, not a question → 3-4 short paragraphs developing one idea, in second person with active verbs on what the people on the trip do in the source, no maxims → light, direct CTA → hashtags. Instead of a maxim pair like "That's not X. That's Y." write one plain sentence that says what happens and when.
  ```
- **Removed from the original plan:**
  - The Kuang Si example sentence. Trail Pulse's test seed **is** Kuang Si, so the writer would copy it verbatim, which is the brief-paste failure F15 already catches.
  - "Contractions welcome." It may contradict brand style guides; leave it to the brand pack.
- **Source:** `reference/channels.toml`; chị Thư's `brand.py:93-119`.

### 3.8 `acp_angle_gate/prompts.py` route head (:110-112, `is_route`)
- **Append** to the route head:
  ```
   The three angles take three different shapes: the walk in order; one thread that runs the length of it; and the one day unlike the others. Do not reproduce the itinerary day by day, and never make a THIN MOMENT the closing beat.
  ```
- **Source:** chị Thư's `src/aa_social/angles.py:62-65`.

---

## 4. Builds

1. **Offered/included flag** (#1): computed per moment in `atom_seed`, exposed as `writer_input.route_moments[].status` in admin, and read by F17 instead of re-parsing. Later: a stored column (a CIS-owned migration), matching chị Thư's `offered_moments` table.
2. **`WRITER_FACT_KINDS` allow-list** (#2) in `atom_seed.py`.
3. **Banned-patterns data file:** `services/acp_content_writing/data/banned_patterns.toml`, with one origin comment per row (layout of chị Thư's `reference/banned-patterns.toml`), loaded at import, plus a regex-compiles test. Do it after #5/#7 land, not in the same PR.
4. **F9 sticky-pass set** (#4b): in memory, per job. No DB.
5. **Outline-first blog writer: not yet.** Decide only if #1–#4b leave blogs below 4/8 light.
6. **Blog writer model A/B** (#9).

---

## 5. Jev: exact actions

Run every statement through the S3-mediated ECS exec pattern (asyncpg, `ssl="require"`, `aa365-admin`), with a SELECT before and after.

| Use | Action | Basis |
|---|---|---|
| `t10_gates` (6 questions) | **OFF (approved)**: `UPDATE shared.decision_question SET mode='off', updated_at=now(), updated_by='admin:nghiep (S234 Jev audit)' WHERE stage='t10_gates';` then the code PR removing `observe_t10`. With mode off, `jev_observe.py:98` does not return early, so about 9 `skipped` rows per attempt are still written until the call is removed. | 2,941 calls / 14 days, all grey, 0 acted, $0.198 |
| Remaining T axis for the 4 AA test tenants (t3 `a1_claim_supported` enforce, t7, t8, t9, t2 tie-break) | **Recommend OFF; needs Nghiệp's yes.** `DELETE FROM shared.jev_tenant_allowlist;` (back up the 4 rows first). Real tenants are already off, because the allow-list holds only AA test tenants. | t3: 104 rows, 1 accept, 100 grey (avg p 0.20); t7: 275 grey; t8: 18; t9: 21; 0 acted except t3 ×1 |
| `a1_brand_fit` | Leave it: shadow, 7 rows in 14 days, about $0. It also serves the A-axis s1 tie-break. | – |
| `a1_promise_unsupported` | Keep shadow. | Rides on the `a1_claim_supported` call |
| `a1_claim_supported` (s1), `a3_*`, `a0_*` | **Keep enforce.** | About 72k acted verdicts in 14 days (s1 26,042; a3_demand 18,200; a3_landing 15,314; …) |
| `a1_keyword_about_tour` | Keep enforce, but note: mode switched to enforce 10/10, and every 14-day row is shadow/error (0 acted, 997 402-errors). It is unproven live. | `jev_audit.json` |

- **Do not** set `a1_claim_supported` to off: s1 shares it.
- **A-axis risk:** about 47.9k 402 "Payment Required" errors plus about 5.7k breaker-open errors in 14 days. Check the Jev credit before the next A wave. `decision_log.outcome` is empty, so live precision is unmeasured.
- **Saving from t10 off:** about $0.0012 per piece (pool $0.092 over 80 pieces).

---

## 6. Measurement plan

**Harness:** the same 6 requests and the same 20-piece mix, run through:
1. `s234_checkpoint_r4.py`
2. `s234_analyze_r4.py`
3. `measure_r4.py`
4. `panel_r4.js`
5. `fr_analyze.py`

Run long jobs **as a one-off ECS task**. About $1.15 per round. Do not deploy while `shared.job` has queued or running jobs.

| Step | Verify with | n | Cost |
|---|---|---|---|
| §0.1 card merge | SELECT after the merge, and the seed diff on the 6 requests | – | $0 |
| #5 autofix | offline on `pieces_r4.json` | 20 | $0 |
| #3 regex | offline on `pieces_r4.json` (false positives) | 20 | $0 |
| #4a | unit test | – | $0 |
| #1 + #2 + #3 + #5 + #7 (one deploy) | live r5, then panel | 20 | ≈$1.15 |
| #4b + #6 | r6, `fr_analyze.py` plus panel | 20 | ≈$1.15 |
| #8 | `f9v2_replay.py` | replay set | ≈$0.40 |
| #9 | paired script plus blind panel | 8 pairs | ≈$1.20 |
| #10 | GDrive sheet | 10 | $0 |

**Targets:**

| Metric | r4 (now) | r5 target | r6 target |
|---|---|---|---|
| LinkedIn light / approved | 10/12 · 10/12 | ≥11/12 · ≥11/12 | 12/12 · 12/12 |
| LinkedIn false passes | 2 | 0 | 0 |
| Blog light | 1/8 | ≥3/8 | ≥4/8 |
| Blog held | 7/8 | ≤5/8 | ≤3/8 |
| Blog F9 holds | 3/8 | ≤2/8 | ≤1/8 |
| `promises_an_option` warn (blogs) | 8/8 | ≤2/8 | ≤1/8 |
| Terra / A&H pace sentences | 12 / 3 | ≤2 / ≤1 | ≤2 / ≤1 |
| Em-dash per 1,000 words | 14.2 | <1 | <1 |
| Retry added a blocking fail | 20% (pool) | – | ≤8% |
| Guard reverts | 16 (pool) | – | ≤6 per round |
| Panel AI-tells /10 | 4.75 | ≥5.5 | ≥6.0 |
| Cost per blog / per LinkedIn | $0.104 / $0.026 | ≤$0.10 / ≤$0.027 | ≤$0.085 / ≤$0.026 |
| Jev `t10_gates` calls per round | 448 (r4) | 0 | 0 |

r5 bundles 5 changes in one deploy, so per-change effect comes only from the offline checks above.

---

## 7. What NOT to do

1. **Do not add gates without fixing the input first.** Attempt-1 passes were 1/20 in r2 and r4, and approvals went 17 → 10 → 13 → 11.
2. **Do not read F15 "49/49 fixed" as a repair win.** Stock phrases block on attempt 1 only (`service.py:1368`), and 2 pieces still end with F15 blocking residue.
3. **Do not full-rewrite truth faults.** F9 full rewrite fixed 0/6.
4. **Do not wire F9 v2 below 90%.** It is at 71–75% now.
5. **Do not turn off `a1_claim_supported`.** Use the allow-list instead.
6. **Do not compare against S233b** (blog reruns, 13/16 held on F4). Use S233a.
7. **Do not run adhoc scripts with `nohup` in the api task.** A deploy cut the F9 v2 replay (about $0.37 lost).
8. **Do not put example sentences from a test seed anywhere in prompts.** Brand examples stay fenced.
9. **Do not change the blog prompt without updating the byte-identical guard**, and do not deploy with jobs queued.
10. **Do not promise a commercial threshold on AI-panel numbers alone** (#10).
11. **Do not run paid batches beyond the 20-piece checkpoint** or across the catalog.
12. **Do not mark AA-768/771/772 Done on a merge alone.** Done means deployed, plus a checkpoint, plus the targets.
13. **Do not withhold blogs from tenants or show them QA flags.** Quality gating is an admin label, not a delivery block.
14. **Do not create the NEW issues (#4b, #9, #10) in Linear without Nghiệp's approval.**

---

## Changes made by the critic

- Added §0: the card merge and `t10_gates` off are approved by Nghiệp in this request. The merge runs via destructive-ops before r5.
- Decision 1: LinkedIn readiness is limited to the 3 cells the r4 panel recommends; Trail Pulse is excluded. The light edit happens in admin, not by the tenant (tenant sees content only).
- Decision 2: rewrote "do not ship blogs". Blogs are still delivered (standing rule); there is just no commercial promise.
- Fixed "F9 10 of 13 blog holds". Pooled blog holds are 22 (F9 10, F16 6, F17 3, F1/F4/F13 1 each); r4 blog holds are 7 (F9 3, F17 3, F13 1). Blog F9 baseline is 3/8, not "4–5".
- Jev numbers: 2,941 `t10_gates` calls (not 2,290), $0.198. About 72k acted verdicts (not 71k enforced). 402 errors are about 47.9k. `a1_keyword_about_tour` has no live enforce verdicts. Deleting the allow-list is now a recommendation needing a yes, since only `t10_gates` was approved and real tenants are already off.
- #4: the F4 bug is real but the cause was wrong. F4 is removed from `failed` by `_seo_fields_only` (:102), and the `[]` branch at :118 needs a non-F4 gate. Split out as #4a (XS). The cut policy moves to attempt 3 rather than the first retry, because about 28% of F9 flags are false. `delete_flagged` already calls `tidy_after_cut` (:332).
- #3: the original pace counts were not reproducible; replaced with a recount (Terra 6/11/15/12, A&H 5/2/7/3, Trail Pulse 7 per round). Dropped "not a technical" from the regex. Added an offline false-positive check.
- #5: the contrast-frame regexes already accept `,;:`, so no re-baseline. The banned-pattern guard goes in only after the autofix is proven, to avoid F2 blocking 19/20 pieces. Fixed counts (`channel_spec` has 25 em-dashes) and flagged em-dashes in brand-pack data.
- #7: new stock lines must go into `STOCK_PATTERNS` too (F15 reads it). "worth sitting with" is already in the list. The under-floor block applies on attempt 1 only. Removed the Kuang Si example, since it is Trail Pulse's own test seed, and removed "contractions welcome".
- #1/#2: added sentence-level offered matching, the F9 v2 seed-prefix contract, keeping `Status:` out of the fact count, and a check that stored card facts carry `kind`.
- #9: `t9_write` $2.55 covers all channels, not blog attempt 1 only. Rewrote the done-when as a measurable rule.
- Corrected line refs: `_LINKEDIN_AVOID` :184-187, `CONSUMER_SOCIAL` :192-197, `render_brand_block` :124-126. Removing dead `select_relevant_facts` also needs `test_aa700_t7_t8_t9_jev.py` updated. Confirmed `deploy-dev.yml` has no `concurrency`.
- NEW issues are marked "needs approval", with an existing parent each can attach to.

Files I checked:
- `/home/nghiep/projects/AA-Ecosys/.tmp-session/s234/explain/fr_report.md`
- `/home/nghiep/projects/AA-Ecosys/.tmp-session/s234/explain/jev_audit.json`
- `/home/nghiep/projects/AA-Ecosys/.tmp-session/s234/explain/fr_guard_out.json`
- `/home/nghiep/projects/AA-Ecosys/.tmp-session/s234/analysis_r4.json`
- `/home/nghiep/projects/AA-Ecosys/.tmp-session/s234/pieces*.json`
- `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-13-S234-t-series-rounds/07-panel-round4.md`
- source files under `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/services/`
- chị Thư's repo under `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/docs/AI-gent-for automation works/aa-soscial-media-main/`

No repo files were edited.