# AA-784 place-card model evaluation: design (S252, prepared, not run)

**Question.** Which drafter + checker pair should build the ~9,186 AA-784 place cards? Decide on quality, measured against web-verified labels on long-tail places. Cost comes second: even the dearest pair tested projects to under $150 for the whole build.

**What is new compared with the S234 A/B** (see `history.md`):
1. A **full factorial**: every checker checks the *same* drafts, so drafters and checkers can be compared like for like.
2. A **blind panel of web-researching agents** labels identity and every drafted fact against sources. This replaces LLM-only judging.
3. **Checker recall** is measured on natural errors and on planted ones.
4. The sample is **long-tail places that need a card today**, stratified by country and difficulty. It is not 30 landmarks that already had a card.
5. The decision rule is written down before the run (§7).

Files:
- `cardeval_run.py`: the runner. `dry` costs $0; `paid` has a hard cap of $3.00; `resume` continues a run whose task died.
- Outputs go to `s3://<bronze-bucket>/scripts/s252/cardeval/`.

## 1. Constraints checked in code

- **Model keys** (`shared.llm_model_catalog`, migrations 169/170/224/259; prices in $/MTok, in / out):

  | key | model | vendor | price | note |
  |---|---|---|---|---|
  | `gpt-5.6-luna` | GPT-5.6 Luna | openai | 0.20 / 1.20 | live drafter |
  | `gpt-6-luna` | GPT-6 Luna | openai | 0.10 / 0.50 | migration 170 left it disabled; S246 ran it, so it is probably enabled now |
  | `haiku` | Haiku 4.5 | anthropic | 1 / 5 | legacy key, live checker |
  | `sonnet` | Sonnet 4.6 | anthropic | 3 / 15 | legacy key, live fallback |
  | `haiku-5-5` | Haiku 5.5 | anthropic | 0.10 / 0.50 | |
  | `sonnet-5-5` | Sonnet 5.5 | anthropic | 2 / 10 | |
  | `opus-5-5` | Opus 5.5 | anthropic | 4 / 20 | Anthropic list price; Bedrock price not verified |

  `gpt-6-astra` ($10 / $50) is left out. The dry run reads the catalog live and drops any key that is disabled or has no price.
- **Routing.** `LLMRequest.model_tier = <key>` runs exactly that key, with no route fallback and no shadow (`client.py _generate`). The runner wraps `LLMClient` so each call carries `model_tier` and `stage = adhoc_aa784_cardeval`.
- **Same code path as production.** `draft_card`, `check_card`, `_clean_facts` (including the AA-808 rekind), `_clean_aliases`, `_representative`, `place_key` and `find_card_for_draft` are imported from `services/acp_shared/place_cards.py`. No prompt is copied. The arms differ only by model.
- **Cost logging (workspace rule).** Every call is logged to `shared.llm_call_log`:
  - Draft calls are logged with `role=writer`, check calls with `role=validate`, via `place_cards._log`, which uses `record_call_with_pool`.
  - The gateway logs billed unusable replies itself, under the same stage.
  - The script prints its own spend next to the `llm_call_log` sum, so the two can be compared.
- **No product writes.** The runner writes no card, link, alias or miss rows. The AA-809 resolver (`find_card_for_draft`) runs read-only, to see whether each draft *would* link to an existing card.

**Deliberate deviations from production:**
- **Higher token limit for challenger arms only.** `haiku-5-5`, `sonnet-5-5`, `opus-5-5` and `gpt-6-luna` (both roles), and `gpt-5.6-luna` *as a checker*, get `max_tokens` raised to 4000. The 5.5 models think adaptively and the Luna models reason, and both count against the limit: in S246, Haiku 5.5 day calls stopped at `max_tokens` and gpt-6-luna returned empty replies. Production asks for 1500 on the draft and 1024 on the check. **The live arms (Luna draft, Haiku 4.5 check) keep production limits**, so the incumbent is measured exactly as it runs. Billing is per token used, so the raise only prevents truncation. `results.json` records `max_tokens` per call. **If a floored arm wins, `place_cards.py` needs the same raise.**
- **Unusable replies are flagged, not hidden.** `check_card` turns an unparseable or misaligned reply into "identity rejected, keep nothing", the same as a real rejection. The runner keeps that production outcome but sets `unusable: true` (and `parse_ok` on drafts), so §7 gate 5 can count them and a truncating checker is not scored as a strict one.
- **Sonnet 4.6 can fall back inside its own key.** The legacy `sonnet` key can fall back to Haiku within its chain. The runner records `model_used` and `fallback_used`; a row with a fallback is excluded from that cell (the LLM-only summary counts it as `fallback_excluded`).
- **Incumbent check.** The dry run reads `shared.llm_role_config` for both stages and warns if the live route is no longer Luna draft + Haiku check (an admin may have changed it in Settings since migration 222).

## 2. Sample: 30 place groups that need a card today

**Source** (read-only, the same query and rules as `aa988/scripts/s02/s06`, plus `owner_scope = 'platform'` so no tenant-owned atom text reaches S3 or the panel, and `ORDER BY atom_id` so the representative atom is stable): active place atoms with no `atom_place_card` row, minus:
- atoms the rule skips (`card_skip_reason`);
- groups the existing cards already cover (`find_existing_cards` / `find_local_cards`);
- groups with an active stored miss.

Atoms are grouped by `atom_group_key`, exactly as `ensure_place_cards` does. Groups whose itinerary sentence is shorter than 20 characters are dropped.

**Difficulty classes.** Each group gets the first class that matches, in this order:

| class | rule | quota |
|---|---|---|
| `generic` | `is_generic_name` (City Palace, Night Market, Old Town): the locality must come from the sentence | 5 |
| `variant` | non-ASCII spelling, or a near-spelling of another group or an existing card in the same country (SequenceMatcher ≥ 0.85, ≥ 0.8 for names up to 8 letters, or the same `match_key`): Burang / Purang (0.83), Waterfall / Falls | 6 |
| `homonym` | the same `core_key` occurs in another country (in groups needing a draft, or in existing cards) | 6 |
| `landmark` | the group spans 3 or more tours | 6 |
| `small_local` | a single-tour group: villages, passes, small temples, camps typed as attractions (the long tail) | 7 |

**Selection is deterministic:**
- Countries are ranked by how many groups need a draft.
- Picks go round-robin across countries, at most 3 per country.
- Within a country, candidates are ordered by sha1(place_norm | country).
- A class with too few candidates is filled from the others, long tail first. The per-country cap is relaxed only if 30 still cannot be reached.

The dry run writes `sample.json`, and the paid run reads that exact file. The representative atom (`_representative`) and its sentence(s) are frozen in it.

## 3. Arms: drafters × checkers, run in tiers

**Drafters:**
- D1 `gpt-5.6-luna` (live), run twice (D1#1, D1#2) to measure run-to-run stability
- D3 `sonnet-5-5`
- D4 `gpt-6-luna`
- D5 `haiku-5-5`
- D2 `sonnet`, Sonnet 4.6 (tier F only, optional)

**Checkers:**
- C1 `haiku` (live)
- C2 `gpt-5.6-luna` (the S233 checker)
- C3 `sonnet-5-5`
- C4 `opus-5-5`

**Planted cards (P).** Each group gets a copy of its D1#1 card with:
- one fact mutated: year −137, century ±4/5, a number with a unit ×1.7, or else a fabricated "founded in 1742 by a Portuguese trading mission";
- on every other group, the locality also swapped for another sample group's locality.

The panel labels the planted facts blind as well. A planted fact counts as **known false** for planted recall when (a) it is a mutation of a fact the panel marked `supported` (the mutated number/date then contradicts that source), or (b) it is the fabricated founding sentence and the panel did not mark it `supported`. (A fabricated fact will usually come back `unverifiable`, not `contradicted`; requiring `contradicted` would throw most fabricated plants away.) A planted locality swap counts as a known identity error when the panel labels that variant's locality `wrong`.

**Cells by tier.** "same" marks a same-vendor cell. Same-vendor cells are run only to measure how lenient a checker is on its own vendor's drafts; they are not eligible for production. "live" is the current production pair. Each checker gets its planted cards (P) in the same tier as its natural cells: without them its identity recall has n < 10 and gate 6 (§7) cannot be measured, so the pair could never qualify.

| tier | drafts | C1 haiku | C2 gpt-5.6-luna | C3 sonnet-5-5 | C4 opus-5-5 | est. cost |
|---|---|---|---|---|---|---|
| A | D1#1, D1#2, D3, D4, D5 | D1#1 (live), D1#2, D3 (same), D4, D5 (same) | D1#1 (same), D3, D4 (same), D5 | | | $0.67 |
| B | | P | P | | | $0.05 |
| C | | | | D1#1, D4, D3 (same), P | | $0.85 |
| D | | | | | D1#1, P | $0.85 |
| E | | | | | D4#1 | $0.43 |
| F (optional) | D2 | D2 (same) | D2 | | | $0.30 |

**Pairs that could go to production** (cross-vendor):

| pair | what it is | est. cost for 9,186 cards |
|---|---|---|
| D1×C1 | live | $19 |
| D4×C1 | | $14 |
| D5×C2 | | $11 |
| D3×C2 | strong drafter | $112 |
| D1×C3 | strong checker | $76 |
| D4×C3 | | $69 |
| D1×C4 | strongest checker | $140 (near the $150 gate if Opus thinks longer than assumed) |
| D4×C4 | | $135 |
| D2×C2 | S233 drafter + S233 checker | $83 |

**Cost estimate.**
- Input tokens are measured from the real prompts: about 816 for a draft and 554 for a check.
- Output tokens are assumed, including reasoning: Luna 700 draft / 400 check, Haiku 4.5 350 / 100, Sonnet 4.6 400 / 100, the 5.5 models 1000 / 600. The dry run prints the observed 30-day average and p90 output tokens of each eval key (`CALIB_MODEL`) so the assumptions can be checked before paying.
- That is 682 calls for A–E: **≈ $2.85.** F (+$0.30) does not fit under the cap at these estimates; it runs only if real outputs are shorter.
- **Hard cap: $3.00, enforced in code** (offline-tested with every call running to its full `max_tokens`: spend stopped at $2.998):
  - Each call reserves its **worst case** (2,000 prompt tokens + its full `max_tokens`) before it starts. A call starts only if spent + all in-flight reservations + its own worst case ≤ $3.00; near the cap it waits for in-flight calls to settle and is skipped only when nothing is in flight and it still does not fit. So spent never passes the cap.
  - A tier is skipped if spent + 1.2 × its estimate would pass the cap, **and the run stops there**: a later, less useful tier never runs after an earlier one was skipped.
  - Calls skipped near the cap leave partial cells; the analysis uses only groups with a complete cell and reports n.
- **No second spend.** `paid` refuses to start when `results.json` exists. `results.json` is checkpointed every 15 calls. `resume` reloads it, skips every finished call, and sets spent to the larger of the saved spend and the `llm_call_log` sum for the stage since the first start (a SIGKILLed task writes no final file).
- The dry run also prints the live-calibrated estimate: catalog prices plus the observed `a3_place_card*` averages from `llm_call_log`.

## 4. Outputs (S3, `scripts/s252/cardeval/`)

| file | content |
|---|---|
| `sample.json` | dry run: the 30 groups (class, country, atoms, tours, frozen representative atom), pool stats, `PROMPT_SHA` |
| `estimate.json` | dry run: cost by tier, usable keys, skipped keys, calibration rows (per stage and per eval model), live routes of the two stages |
| `results.json` | paid run, checkpointed every 15 calls and after every tier (`done_through_tier`: tier letter, `end`, or `aborted_after_<tier>`): every draft (identity, facts with kind and the AA-808 rule hit, `place_key`, `would_link`, model used, cost, tokens, latency, stop reason, error, raw excerpt), every check (identity_ok, verdicts, kept indices, outcome stored / identity_rejected / no_name_generic / error, cost, latency), planted cards, and an LLM-only summary per cell |
| `panel_packet.json` | **blind** packet. Per group: itinerary place, country, tour name and sentence; the distinct identity variants (opaque `V…` ids); the deduplicated facts (opaque `F…` ids, which variants hold them); link questions (`L…`: "is this existing card the same place?"). No model names, no verdicts, order shuffled by hash. |
| `panel_key.json` | maps `V`/`F`/`L` ids to draft ids, and draft ids to drafter, model and run. Used only after the labels are final. |

## 5. Blind verification panel (web-researching agents)

**Unit of work: one group.** One agent researches the place once, then labels every identity variant, every fact and every link question for that group. The 30 groups produce roughly 600 distinct facts.

**Labellers.**
- **Two independent labellers** (A and B) per group, run as separate agents with WebSearch / WebFetch.
- They see `panel_packet.json` only: no `results.json`, no key, no model names, nothing about which facts were planted.
- **Enforce it on disk, not just in the prompt:** give each labeller only its group's slice of the packet (inline in the brief or in `panel/in/<group>.json`), and do **not** download `results.json` / `panel_key.json` from S3, or open `design.md` / `history.md`, until every label file is final. The labellers have file tools; anything in `.tmp-session/s252/cardeval/` is readable to them.
- **Freeze the rule:** commit `design.md` (or save it under `docs/audits/…`) and note its git hash before the paid run, so §7 is provably fixed before any result exists.
- A **third agent adjudicates** each item where A and B disagree. It sees both rationales and sources.
- Report agreement (Cohen's κ) per label type.
- *Optional (Nghiệp):* hand-check 20 random adjudicated fact labels to estimate the panel's own error. Not a gate.

**Step 1, reference identity (per group, before reading the variants):** what the itinerary sentence means.
- Fields: name, locality, region, country, lat/lon, source URLs.
- `identifiable`: yes / ambiguous / no.

**Step 2, per identity variant.** Choose one value per field:

| field | values |
|---|---|
| name | ok / wrong |
| locality | correct / acceptable_nearby (≤ ~30 km and the usual reference town) / empty / wrong |
| region | correct / acceptable_historical (e.g. Ladakh, Tibet, Khumbu) / empty / wrong |
| country | correct (the de facto state today) / wrong |
| entity | same / other_entity (valley vs monastery, county vs town) / mixed |

`identity_correct` = name ok ∧ locality ≠ wrong ∧ region ≠ wrong ∧ country correct ∧ entity same.

**Step 3, per fact.** The fact is judged about the place the itinerary means.

`verdict` is one of:
- `supported`: at least one reliable source states it, and no T1 source contradicts it;
- `contradicted`: a reliable source says otherwise, or it is true only of a different entity;
- `unverifiable`: no reliable source either way after about 10 minutes, or T1 sources conflict.

Each fact also gets:
- `reason` (when contradicted): false / other_entity / numeric_off / overstated;
- `numeric`: true or false;
- `trip_leak`: true or false. True when the fact covers access, roads or distances by road, permits, hours, prices, what visitors do or see, views, a stop or base, or being combined with other sites (forbidden by AA-774 / AA-808);
- `trivial`: true or false. True when the fact only restates the identity fields;
- **sources (required):** a `supported` or `contradicted` verdict must cite at least 1 source URL (max 2) of the tier it relies on, with a quote of at most 25 words from that page. A `supported` / `contradicted` label without a URL and quote is converted to `unverifiable` at merge time. The adjudicator opens the cited URLs; a quote not found on the page also converts the label to `unverifiable`. Identity fields (Step 1) cite the same way (coordinates: OSM / GeoNames / Wikipedia URL).

**Step 4, per link question:** same_place yes / no / unsure.

**Reliable sources.**
- **T1:** Wikipedia (the claim or its citation), Wikidata, UNESCO, government heritage or tourism bodies, Britannica, academic publishers, national statistics.
- **T2:** major guidebooks and established news outlets. Accepted when no T1 source contradicts.
- **Not reliable:** tour-operator pages, blogs, TripAdvisor, AI content farms, the itinerary itself.
- **Locality:** checked against OSM / Nominatim, GeoNames or Wikipedia coordinates.
- **Numbers:** elevation within ±3% or ±50 m, distances within ±5%, dates exact, unless T1 sources disagree.

**Output:** one JSON per labeller per group (`labels_<group>_<A|B|adj>.json`, under `.tmp-session/s252/cardeval/panel/`), then the merged `labels_final.json`.

## 6. Metrics (computed after the labels are joined to the key)

**Per pair** (drafter × checker; the cell's groups are the denominator):
- **FK, the false-fact rate among KEPT facts: the primary metric.** FK = contradicted kept / kept.
- UK: unverifiable kept / kept. LK: trip-leak among kept writer-kind facts (leaks that got past AA-808).
- WI: the wrong-identity rate among STORED cards (wrong or mixed identity / stored). Locality accuracy is also reported on its own.
- Coverage: stored / identifiable groups.
- U: useful facts per stored card (kept ∧ supported ∧ not a leak ∧ not trivial ∧ writer-kind).
- Cost per card (draft + check), projected to 9,186 cards; p50 / p90 latency; empty or unusable replies.

**Per drafter** (independent of the checker):
- identity-correct rate and locality-correct rate;
- count of mixed entities;
- contradicted / all drafted facts (hallucination rate);
- leak rate;
- no-name or error rate;
- stability: D1#1 vs D1#2 identity agreement and fact overlap;
- wrong-link rate: `would_link` points to a card the panel says is a different place.

**Per checker:**
- **fact recall** (contradicted facts not marked "supported" / contradicted);
- **false-drop rate** (supported facts dropped / supported);
- **identity recall** (wrong identities rejected / wrong) and the false-reject rate;
- **planted recall**, for facts and for identity;
- the **same-vendor leniency gap**: recall on same-vendor drafts minus recall on cross-vendor drafts.

## 7. Decision rule (fixed before the run)

**Gates.** A pair is eligible for the AA-784 build only if all of these hold:
1. **Cross-vendor:** the drafter and checker come from different vendors (the migration 222 rule).
2. **WI:** at most 1 stored card with a wrong or mixed identity, and **0 with the wrong country**.
3. **FK ≤ 3%** (contradicted kept facts / kept facts).
4. **LK ≤ 2%.**
5. **Coverage ≥ 85%** of identifiable groups, and at most 1 of 30 empty or unusable replies per stage (drafts: `error` or `parse_ok = false`; checks: `error` or `unusable = true`).
6. **Checker floor:** fact recall ≥ 0.5 and identity recall ≥ 0.5 (natural and planted errors together, n ≥ 10 each). This stops a pair from passing only because its drafter happened to be good. **If n < 10 for either recall (for example the checker's tier was cut by the budget), the gate is not met**: an unmeasured checker is not eligible.
7. **Cost:** projected cost for 9,186 cards ≤ $150.
8. **Usefulness floor:** U (useful facts per stored card) ≥ 2.5, or ≥ 80% of the live pair's U, whichever is lower. FK alone rewards a checker that keeps almost nothing; this gate stops an over-strict checker from winning on a low FK with empty cards.

**Choosing among eligible pairs:**
- The lowest FK wins.
- **Tie band:** FK within 2 percentage points, or within 2 facts, counts as equal. Inside the band, the tie-breakers in order are: more useful facts per card (a difference of at least 0.5), then lower WI, then lower cost.
- **The incumbent stays on a tie.** If D1×C1 is eligible and inside the tie band of the winner, keep the live route (no migration).
- **Switching routes.** Otherwise, move `a3_place_card` / `a3_place_card_check` to the winner (a migration like 222). If the winner is a 5.5 model, also raise the `max_tokens` floor in `place_cards.py`. Then run AA-784 B per country, capped at $25 or the winner's projected cost + 30%.
- **If no pair passes:** do not build all 9,186. Build only the multi-tour groups (option A, 1,947) with the best pair. Then propose a grounded draft or check (Wikipedia / Wikidata lookup) as a follow-up, and bring it to Nghiệp.

**Reading the result.** With about 120 kept facts per cell, an FK of 3% is about 4 facts. Report Wilson 95% intervals next to every rate, and do not call a difference inside the tie band a win.

## 8. How to run (single-line commands, account acc2, `aa365-admin`)

**Before you start:**
- Run `aws sts get-caller-identity --profile aa365-admin`.
- No deploy and no wave may be running. The runner lives in the api task, and a redeploy would kill it.

**Steps:**
1. Upload the script:
   `aws s3 cp /home/nghiep/projects/AA-Ecosys/.tmp-session/s252/cardeval/cardeval_run.py s3://<bronze-bucket>/scripts/s252/cardeval/cardeval_run.py --profile aa365-admin --region us-west-1`
2. Presign it:
   `URL=$(aws s3 presign s3://<bronze-bucket>/scripts/s252/cardeval/cardeval_run.py --profile aa365-admin --region us-west-1 --expires-in 300)`
3. Find the api task:
   `TASK_ARN=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name aa-cis-dev-api --profile aa365-admin --region us-west-1 --query 'taskArns[0]' --output text)`
4. **Dry run ($0):**
   `aws ecs execute-command --cluster aa-cis-dev-cluster --task $TASK_ARN --container api --interactive --command "sh -c 'curl -s \"$URL\" -o /tmp/cardeval_run.py && python3 /tmp/cardeval_run.py dry'" --profile aa365-admin --region us-west-1`
   Read `sample.json` and `estimate.json` from S3, and sanity-check the 30 groups and the estimate.
5. **Paid run**, about 680 calls, roughly 10–15 minutes. Lesson (S234 F9 replay): a long adhoc run inside the api task dies when a deploy replaces the task, so **merge or hold every pending CIS backend PR first**. Run it detached so the SSM session cannot kill it:
   `aws ecs execute-command --cluster aa-cis-dev-cluster --task $TASK_ARN --container api --interactive --command "sh -c 'curl -s \"$URL\" -o /tmp/cardeval_run.py && nohup python3 /tmp/cardeval_run.py paid > /tmp/cardeval.log 2>&1 &'" --profile aa365-admin --region us-west-1`
   To follow progress: `results.json` is checkpointed every 15 calls (check `done_through_tier` and `spent_usd`). `panel_packet.json` appears at the end. If the task died, rerun the same command with `resume` instead of `paid` (`paid` refuses while `results.json` exists).
6. Download `panel_packet.json` to `.tmp-session/s252/cardeval/` and run the panel (§5).
7. Join the labels with `panel_key.json` and `results.json`, compute §6, apply §7, and write the audit to `docs/audits/2026-10-2x-S25x-place-card-model-eval/`. Add a wave-style cost line from `llm_call_log`, stage `adhoc_aa784_cardeval`.

## 9. Known limits

- **Sample size.** n = 30 groups and one run per arm (D1 is run twice). The rule is built for large effects: catching an FK of 10% vs 2%, not 3% vs 2%.
- **Closed-book models only.** Grounded (web or Wikidata) drafting is not tested here; it is the follow-up if no pair passes.
- **The panel is made of agents, not humans.** Two labellers plus an adjudicator, with sources cited and an optional human sample. That is far stronger than LLM-only judging, but it is still not human ground truth.
- **Opus price.** The Opus 5.5 Bedrock price is not verified (the catalog has the Anthropic list price), so its projected cost is approximate. The 5.5 Haiku/Sonnet catalog prices are Anthropic first-party prices too (migration 259: "confirm on the AWS Bedrock pricing page"); the budget guard uses the same catalog prices as `llm_call_log`, so a Bedrock price above list would make real spend exceed the logged $3.00.
- **No cross-border class.** A place in a neighbouring country of the one the tour is sold as (the S232 failure: Ladakh vs China vs Luang Prabang) is not a sampling class, because it cannot be detected without a model; it is covered only where it overlaps `homonym` / `variant`. The panel's `country` field still measures it.
- **Linked drafts.** In production a checked draft that the AA-809 resolver links to an existing card keeps the *existing* card's facts. The eval scores the draft's own kept facts; `would_link` lets the analysis report such cases separately.
- **Tenant atoms.** The sample is platform atoms only; the 9,186 count of AA-988 s06 does not filter `owner_scope`, so the full build may include some tenant-owned atoms the sample never sees.
- **Effect on the writer is not measured.** Whether better cards give better T8/T9 posts (the AA-772 A/B dropped in S239) is out of scope here.
- **AA-784 Done-when** asks for 30 human-checked cards with ≥ 27 correct identities. The panel's identity labels on the winning pair can stand in for that only if Nghiệp accepts agent-panel labels.
