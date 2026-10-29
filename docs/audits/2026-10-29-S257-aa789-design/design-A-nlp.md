# AA-789 design, Approach A: deterministic NLP aligned to the seed (no LLM)

Status: design proposal (S257). No code written, no paid calls made.
Code read: AA-CIS-App `main` @ 4feb3cb3 (`services/acp_content_writing/{hygiene,quality_gates,trip_facts,service}.py`,
`services/acp_shared/{channel_spec,content_embedding}.py`, `services/quality/registry.py`,
`tests/unit/test_aa789_t10_recall.py`, `scripts/aa789_recall_replay.py`), the CIS PR #1140 body, the round-3 verifier
output (`.tmp-session/S257/aa789-verify.json`), root Report 12 §1.3–§1.5, root `docs/generated/llm-routes.md`,
Infra `modules/ecs/variables.tf` (worker size), and the shape of `.tmp-session/s249/aa783_export.json` (40 pieces: 16
blog, 24 LinkedIn; seeds average ~920 words, pieces ~640 words, longest 1,572).

---

## 0. Summary of the approach

PR #1140 showed that a pattern over the copy alone cannot tell a defect from clean copy. The same words ('by boat',
'optional', 'stop in Mörön', 'significant share') are a defect in one sentence and clean in another. The difference is
*structural*: who travels by boat, what 'optional' is predicated of, what 'at' attaches to, what the share is a share of.
It also depends on *the seed*: is the boat ride optional there, is the moment planned, does the seed say 'near'?

Approach A replaces "regex over copy" with **three keys per finding**:

1. **Trigger**: a closed lexical cue (as today).
2. **Structure**: a dependency-parse relation that pins the cue to its role (subject, object, preposition head,
   predicate target). spaCy `en_core_web_sm` 3.8.x does the parsing, CPU only, pinned.
3. **Seed contradiction**: a typed relation extracted from the seed (`SeedGraph`) that the copy relation contradicts.
   Examples: OPTIONAL(activity) vs PLANNED(moment), NEAR(event, place) vs AT, no seed support for SCOPE=world.

A finding exists only when all three keys agree. A missing key never produces a finding: no moment attribution, an
unresolved alias, an unstable parse or a sentence over the length cap all mean **abstain**. That makes precision a
property of the design, not of tuning: clean copy can only fire if the parser mis-assigns a role *and* the seed happens
to contradict that wrong role.

The only non-deterministic component is the sentence embedding for paraphrased repeats. It is a frozen local model with
fixed weights, so it is deterministic at inference too. It never holds a piece (§4).

---

## 1. Shared foundation (new modules)

| Module | Content |
|---|---|
| `services/acp_content_writing/nlp_parse.py` | Lazy singleton `spacy.load("en_core_web_sm", exclude=["ner"])` (we use our own gazetteer, not spaCy NER: it is weak on Mongolian/Bhutanese names). `parse(sentence) -> Doc` with `lru_cache` keyed on the sentence text. `PhraseMatcher` built per seed from the place gazetteer (moment names, `Location:` parts, `Naming:` aliases, `ScopeLexicon` names) so a place is one span, e.g. 'Tsaatan reindeer herders' settlements'. Helpers: `clause_of(token)`, `governing_verb(token)`, `subject_of(verb)`, `is_negated(token)`, `has_modal(verb)`, `hedge_scope(hedge_token) -> set[token]`, `stable(sentence)` (§3). Records `nlp_version = spacy.__version__ + model meta version` in the ledger. |
| `services/acp_content_writing/seed_graph.py` | `SeedGraph.from_seed(seed, moments)`, cached per seed hash. It reuses `trip_facts.parse_moments`, `optional_activities`, `_background_places` and `hygiene.split_seed`. It adds typed relations parsed from `Source itinerary:` lines only, never from background lines: **planned events** `(moment, event_lemma, relation, place)` with relation ∈ {AT, NEAR}; **optional activities** with their head nouns and instrument nouns (boat, horse, kayak, raft, bike, reindeer); **planned transport** nouns per moment ('Board a traditional junk' → boat); **ease statements** (easy, gentle, short, flat, suitable for, no experience); **hazard / difficulty statements** (multi-hour ride, steep, demanding); **proportion claims** with their scope (`70% of Mongolia's fresh water` → scope=Mongolia); **superlatives** with scope (reuses `_SUPERLATIVE_RE` and `seed_scopes`); **naming-note lemmas** (content lemmas of `Naming:` lines minus place names and minus every lemma that also appears in trip or background lines); **aliases** (Moron ≡ Mörön ≡ Murun from `Naming:` / `Location:` "the itinerary calls it …"). |
| `services/acp_content_writing/seed_align.py` | The checks of §2. Each returns findings in today's shape `"<problem>: '<sentence>'"` (so `sentence_repair.plan` parses them), plus a `check` id. Pure functions over `(text, TripFactContext, HygieneContext, briefs)`. |
| `services/acp_content_writing/sentence_embed.py` | Local `BAAI/bge-small-en-v1.5` (MIT, 384-dim) exported to ONNX int8 (~35 MB), run with `onnxruntime` + `tokenizers`. Weights pinned by SHA-256 and baked into the image at build time. `embed(sentences) -> np.ndarray` (L2-normalised). Used by the paraphrase check only. |

Seed-format coupling: `SeedGraph` reads the seed builder's labels (`Source itinerary:`, `Place background`, `Naming:`,
`Location:`, `Status:`, `Day N of the trip`). A contract test builds a seed with the real `atom_seed` builder and asserts
the graph is non-empty. If the builder's format drifts, CI fails instead of the checks going silently quiet.

### Embeddings: Cohere Embed v4 vs a local model

- **Cohere Embed v4 is still allowed.** Project CLAUDE.md (AA-998, S255) allows "the Bedrock models native to acc2 in
  use today (e.g. Cohere Embed v4)". In `llm-routes.md`, `cohere-embed-v4` is enabled with **acc2 as primary** at
  $0.12 per M input tokens, used by `f10_embed` and `a3_place_embed`. Its fallback `cohere-embed-v4-acc3` is dead while
  acc3 Bedrock is blocked. A new call site would need its own gateway stage (e.g. `t10_repeat_embed`, a
  `shared.llm_role_config` row) so each call writes `shared.llm_call_log`, like `f10_embed` (AA-685).
- **Recommendation: the local model.** (a) It is $0 for the offline evaluation this week, which the "no paid calls in
  this round" constraint requires. Cohere would be paid even at fractions of a cent. (b) Offline, CI and production run
  the *same* model, so the similarity threshold calibrated offline holds in production. Switching models later means
  calibrating again. (c) There is no network or outage dependency inside a gate.
- **Cost of the local model:** +~150 MB image (spaCy + model ~60 MB, onnxruntime + tokenizers ~30 MB, numpy/thinc/blis
  share pandas' numpy, bge ONNX ~35 MB). It also adds ~250–350 MB RSS once loaded. The worker task is **512 CPU /
  1024 MiB** (Infra `worker_task_memory` default), so this probably needs a 2048 MiB worker (§6). Load lazily inside the
  gate so the api process, which uses the same image, never pays the RSS.
- Cohere stays the fallback design if the memory bump is refused: ~1.5k tokens per blog attempt ≈ **$0.00018**.

---

## 2. Mechanism per missed class

Notation: *S* = the copy sentence, *M* = the moment *S* is about. *M* comes from `moments_named(S)`. If *S* names
none, *M* comes from the section heading's moment (`trip_facts._sections` / `_heading_sections`). If neither resolves,
the check abstains. *Traveler subject* = nsubj/nsubjpass whose lemma ∈ {you, we, family, traveller, traveler, guest,
group, child, kid, visitor (only with a trip verb), everyone} or the clause is imperative.

### 2.1 'By boat': an optional activity presented as planned

Today `_mentions_activity` needs two of the activity's words ('boat' + 'ride'), so 'cross the lake by boat' slips
through. Widening to one word fired on 'Supplies arrive by boat'.

Mechanism (extends `optional_as_fixed`):
1. Trigger: an *instrument noun* of an optional activity of *M* (from `SeedGraph`: boat, horse, kayak, raft, bike,
   reindeer). It appears as (a) `pobj` of prep 'by'/'on'/'in' (by boat, on horseback, in a kayak), (b) `dobj` of a
   ride/paddle/sail verb, or (c) a compound head (boat trip, boat cruise).
2. Structure: the governing verb *V* has a **traveler subject**. *V*'s lemma is in a closed experience/movement list
   (cross, travel, explore, reach, glide, head, spend, see, visit, move, go, continue, return). *V* is not negated, has
   no modal aux (can, could, may, might), and no hedge token (optional, if you wish, extra, on request, add-on,
   available) sits in `hedge_scope` covering the instrument token. Hedge scope is the subtree of the hedge's syntactic
   head. That makes the revision-3 'per-item hedge' structural: in 'Families travel by boat and on foot, with only
   horse riding optional', 'optional' governs 'riding' only, so 'by boat' is unhedged and fires.
3. Seed: the instrument appears **only** in *M*'s optional activities. It is absent from *M*'s planned lines and from
   planned transport anywhere in the piece's SCOPE ('Board a traditional junk' licenses 'by boat').
4. Paragraph lead-in hedge (existing `_paragraph_lead` rule) still exempts the first clause.

Clean cases that stay clean, and why: 'Supplies arrive by boat' and 'The camp's supplies come in by boat' (subject is
not a traveler); 'The lake is best seen by boat' (no traveler subject; a recommendation, so a miss we accept); 'You
can also cross by boat' (modal); 'Optional activities include boat rides…' (hedge scope covers it).

### 2.2 Reverse flip: a planned moment called optional

Revision 3's `included_as_optional` fired on 'At the Tsaatan settlements on day five, children can ride a reindeer if
they wish' and on 'At the Tsaatan settlements, milking the reindeer is optional'. Those are sub-activities at a planned
moment, not the moment itself.

Mechanism:
1. Trigger: a hedge predicate: `acomp`/`attr` 'optional' ('X is optional'), `amod` 'optional' ('an optional visit to
   X'), 'if you wish/like/prefer', 'can choose to', 'at extra cost', 'on request'.
2. Structure, finding the **target** of the hedge: for a copula it is nsubj (or the gerund's object: 'Visiting the
   Tsaatan herders is optional' → target NP = 'the Tsaatan herders' under gerund 'visiting'). For `amod` it is the
   head noun plus its `prep` object. For 'if you wish' it is the main clause's `dobj`. The target must be a
   **moment-level NP**: it contains a span of *M*'s name in the PhraseMatcher, and its head lemma ∈ {visit, stop, trip,
   excursion, day, stay, overnight, walk/hike/trek *to/into* M} or it is the gerund object itself. A place in a
   **locative modifier** (`prep` at/in attached to the predicate, as in 'At the Tsaatan settlements, …') is *not* the
   target. That single structural fact is what regex could not see.
3. Seed: *M* is planned. It has a `Source itinerary` line, no `Status: OFFERED` (via `m.statuses`), and no optional
   mark in its label line. The target NP contains no lemma of *M*'s optional activities (reindeer riding, milking).

### 2.3 'Lunch/stop at X' when the seed says 'near X'

Mechanism:
1. Seed side (`SeedGraph.planned_events`): from each `Source itinerary` clause, an event token (lunch, stop, break,
   overnight, stay, camp, picnic; verbs stop, lunch, pause, overnight) plus a place span, with the preposition path
   between them. at/in → AT; near/outside/close to/on the outskirts of/en route to/before reaching/in proximity to →
   NEAR. 'Stop for lunch near Moron' → (lunch, NEAR, Mörön) and (stop, NEAR, Mörön).
2. Copy side: the same event classes, linked to a place span through prep at/in/inside, either as the event's own
   `prep` child ('A stop in Mörön') or through a copula ('Lunch is at Mörön': nsubj=lunch, `prep` at on the copula).
   The clause must not be negated and the event must not sit in a temporal prep ('After lunch, the drive continues to
   the airport in Mörön': 'lunch' is the object of 'after', and the place attaches to 'airport').
3. Contradiction: the seed has NEAR(event-class, X') where X' ≡ X by alias, and **no** AT relation to X for any event
   of *M* or of the whole SCOPE. Aliases come from `Naming:` / `Location:`.

### 2.4 'Not a technical climb': a difficulty promise the seed does not make

Mechanism (extends `pace_claims`, F17 pace is blog-only today):
1. Trigger: an ease lexicon. Positive-ease words (easy, gentle, effortless, manageable, undemanding, suitable for all
   ages / fitness levels, no experience needed), or a negated difficulty word (not / nothing / never / no + technical,
   difficult, demanding, strenuous, challenging, hard).
2. Structure: polarity = **reassurance**. The ease word is predicated (`acomp`/`attr`/`amod`) of an **activity noun**
   (climb, hike, walk, trek, ascent, descent, trail, route, scramble, ride, paddle) that belongs to *M*. A difficulty
   word without negation is a **caveat** and never fires: 'The hike is strenuous in places, so good boots matter' and
   'the short technical scramble' stay clean. An equipment subject never fires: in 'No technical climbing gear is
   needed', the predicate 'needed' has nsubj 'gear', not an activity noun.
3. Seed: *M* has no ease statement with the same polarity. A seed hazard or difficulty statement for *M* ('multi-hour
   ride', 'steep') raises the problem text to "contradicts the source's …" but is not required.

### 2.5 'A significant fraction/share of the world': unsupported proportion

Revision 3 fired on 'A considerable share of the walk is on flat ground', 'A substantial portion of the day…' and
'Travellers from most of the world can get a visa on arrival'.

Mechanism:
1. Trigger: a proportion head (fraction, share, portion, proportion, part, percent, %, quarter, third, half) with a
   magnitude modifier or number.
2. Structure: follow the `prep of` → `pobj` → `poss` chain from the proportion head. The chain must reach a **global
   scope noun** (world, planet, earth, globe, humanity, mankind; extensible to 'Asia', 'the region' later). The
   proportion NP must be an argument (dobj/attr/nsubj) of a predicate whose subject is a seed place or moment, or a
   pronoun whose antecedent is one. A proportion of the walk or the day has no global scope. In 'Travellers from most
   of the world', the chain hangs off a prep 'from' modifying a people noun, so it is not an argument about a place.
3. Seed: no seed proportion claim with the same scope ('Lake Khövsgöl holds ~70% of Mongolia's fresh water' supports
   scope=Mongolia, not scope=world).

### 2.6 Scopeless superlative not in the source

Mechanism (extends `rarity_claims`):
1. Trigger: a superlative (tag JJS/RBS, or 'most/least' + ADJ), often 'one of the most …'.
2. Structure: the superlative modifies a **class noun** (route, trip, journey, lake, landscape, place, destination,
   experience, monastery, view) or is predicated of a seed entity. The scope is missing or global ('in the world',
   'anywhere', 'available', 'you can find'). The adjective is **evaluative**. A practical / within-trip list never
   fires: best time, closest, nearest, easiest way, warmest layer, earliest, latest, and the superlative scoped 'of the
   trip/day/route'.
3. Seed: *M*'s seed lines and Facts have no superlative with the same adjective lemma, after a small derivation map
   (distinct ↔ distinctive, large ↔ big ↔ biggest).

Limitation: travel copy is dense with legitimate evaluative superlatives, and a seed often backs a superlative with
other words. Realistic precision is 0.85–0.93 (§5). So this class **never holds**. It joins `STYLE_ONLY_GATES`
semantics, like the existing `F2_superlatives` cap: one sentence repair on attempt 1, then a warning.

### 2.7 The brief's 'one X, one Y, one Z' recipe leaking

Revision 3's `BRIEF_WORDING_RE` fired on 'Each family gets one tent, one stove and one lantern' and on 'The two named
passes on the road…'. The fix is to align to the **actual brief text**, not to the shape.

Mechanism:
1. Recipe extraction: from `hygiene.brief_texts(brand_pack, angle)` (already computed in `service.py` and passed to
   `gate_voice`) and from a static list of the writer prompts' own recipe lines (`prompts.py`, `batch_prompt.py`).
   Extract *recipe templates*: ≥ 2 coordinated 'one/a single + N', or a list of meta nouns (fact, detail, image,
   moment, feeling, place, year, sentence, thing).
2. Copy trigger: a parallel triad or pair of 'one N' (coordination or asyndeton). The parse marks it a **verbless
   fragment** (no VERB/AUX root) or an appositive list.
3. Contradiction: ≥ 2 of the triad's head lemmas are recipe nouns of the brief or prompt, or meta nouns. 'One tent,
   one stove, one lantern' shares none and has a verb root ('gets'). 'One old wall, one year, one fact.' is a verbless
   fragment with meta nouns 'year' and 'fact'.

### 2.8 Naming-note leakage

The `Naming:` line is an instruction to the writer, for example "'Moron' is a common English phonetic approximation …
refer to it as Mörön to avoid unintended connotations". It is not a fact about the place.

Mechanism:
1. `SeedGraph.naming_lemmas[M]` = content lemmas of *M*'s `Naming:` line minus the place names and aliases, minus every
   lemma also present in *M*'s trip and background lines, minus stopwords. Result: {phonetic, approximation,
   romanise, spell, connotation, itinerary, international, audience, commonly, write}.
2. Trigger: *S* names *M* or an alias (PhraseMatcher) **and** contains ≥ 2 naming lemmas, or 1 from a strong subset
   {romanise/romanize, transliterate, connotation, phonetic, misspell, spelling}.
3. Abstain if the matched lemmas also appear in the place background as a fact ('also known as …').

'The trail map at the gate is only a loose approximation' does not name a place that has a naming note. 'kuzuzangpo
is written here as a phonetic approximation' names no seed place. Both stay clean.

### 2.9 Paraphrased repeats (the same claim told twice in different words)

Revision 3's `paraphrased_repeats` flagged 234 of 332 synthetic sentences. Its keys were adjective suffix, a different
head and one shared word.

Mechanism (extends `hygiene.near_duplicates` / `dedupe`):
1. Candidate pairs: body sentences (prose/bullet, not FAQ; F7/F16 own FAQ-vs-body) within the same section, or within
   6 sentences across sections.
2. Key 1, **same subject entity**: the nsubj of each main clause resolves to the same seed entity. Resolution uses the
   PhraseMatcher, an alias, a definite NP whose head is a generic of the entity ('the dzong' → Punakha Dzong when *M*
   is Punakha Dzong), or a pronoun resolved to the previous sentence's subject.
3. Key 2, **semantic similarity**: cosine (bge-small) ≥ τ_high. τ_high is calibrated on the eval set so ≤ 1 clean pair
   per 2,000 clean pairs passes. Expect ~0.86–0.90 for this model.
4. Key 3, **adds no seed fact**: the later sentence has no `hygiene.fact_tokens` (numbers, proper nouns, seed-fact
   lemmas) that the earlier one lacks. This reuses `added_words` / `_keeps_facts`.
5. Action: **autofix-delete** the later sentence when `_repeat_delete_ok` and `_dup_safe_delete` allow it. These
   guards already keep facts and avoid orphaning a pronoun. Otherwise it becomes a warn finding. **Never a hold** (§4).

The verifier case 'The evening brings a local musical performance in the camp … Children can try the local musical
instruments in the camp afterwards' fails key 1 (evening ≠ children) and key 3 ('instruments', 'try' are new).

### 2.10 Orphan section openers

Revision 3's `subjectless_section_openers` fired on '## Practical notes / Entry fees are included…', '## Uran Togoo /
The approach road is paved…' and '## Punakha Dzong / Admission tickets for the dzong…'. Definite descriptions are
normal bridging, not orphans.

Mechanism (extends `piece_opens_dangling` / `certain_anaphor` from the piece opening to every section opening):
1. Trigger: the first sentence of a section whose main-clause subject is a **personal or demonstrative pronoun** (it,
   they, this, that, these, those, he, she), or a demonstrative determiner NP ('these villages'), or that opens on
   'Here,' / 'There,' + pronoun. A definite NP ('The approach road') never triggers. 'also/too' alone never triggers.
2. Antecedent search: the heading. Does it contain a noun or place that agrees in number with the pronoun (it ↔
   singular place or noun; they ↔ plural noun or people name)? If so, the opener is clean. '## Punakha Dzong / It sits
   at the confluence…' is clean.
3. Fire when no agreeing antecedent exists in the heading. Route it to F13_repeat's sentence repair, which rewrites
   the sentence with the referent named.

### 2.11 FAQ answer that does not address its question

`quality_gates.faq_answer_problem` already catches `no_subject` and `negative_only`. `t9_faq_answer_fit` (Sonnet,
default off) is the LLM path.

Mechanism (a third reason, `type_mismatch`):
1. Question type from the parse: yes/no (AUX-initial: can/is/do/are), HOW-ADJ measure ('how cold/long/far/high/much'),
   WHEN, WHERE, WHO, WHAT…FOR (purpose), plus open WHAT/WHY/HOW.
2. Expected answer type, broad on purpose so as not to repeat the verifier's `off_attribute` false positives:
   - yes/no: a polar first clause (yes/no/not/cannot/only, or a modal verdict).
   - how cold: a temperature number, °C/°F (also after a space), or {cold, warm, freezing, below zero, frost, mild,
     crisp, chilly}.
   - how long/far/high: a number + unit or a duration word.
   - when: a month, season, day N, time, or {morning, evening, early, late}.
   - where: a gazetteer place or a locative prep.
   - who: a people noun, a proper name or an ethnonym.
   - what…for: any verb with the question's subject as agent or patient. 'The Tsaatan ride their reindeer and milk
     them' passes.
3. Fire only for the **measurable types** (yes/no, how-ADJ, when, where, who) and only when the answer's first two
   sentences match none of the expected forms. Open WHAT/WHY/HOW never fire. That is out of reach (§5).
4. Action: the same as today's `drop_subjectless_faq`. Drop the pair while more than `FAQ_MIN_PAIRS` remain, else
   flag. It **never holds**. It can also pre-filter `t9_faq_answer_fit` when that is switched on, so the LLM call runs
   only on pairs the deterministic check cannot classify.

---

## 3. Where it plugs into T10

| Step | File / function | Change |
|---|---|---|
| Contexts | `trip_facts.TripFactContext` | Add a lazy `graph: SeedGraph` (built in `__post_init__` only when `T10_SEED_ALIGN != off`) and a `briefs` field. `hygiene.HygieneContext` gets the same lazy graph (both share it by seed hash). |
| Shadow / never-hold gate | `quality_gates.gate_seed_align(content_text, trip_ctx, hygiene_ctx, briefs)` → new result `F20_seed_align`. Insert it in `run_quality_gates` right after `*gate_trip_facts(...)` | **shadow**: `blocking=False` (a flag only). **never-hold**: `blocking=stock_blocking` (attempt 1 only), `repairable=True`, and `F20_seed_align` added to the set `never_holds()` reads (add it beside `STYLE_ONLY_GATES`). Add it to `CHEAP_REPAIR_GATES` so the repair runs on `t9_repair`. |
| Promotion to hold | `seed_align.PROMOTED: dict[check_id, target_gate]` | A promoted check's findings move from F20 into `find_trip_fact_issues()["trip_fact"]` (2.1–2.4), `["rarity"]` (2.5), `hygiene.find_issues()["leak"]` (2.7, 2.8) or `["repeat"]` (2.10). The target gate's existing block → repair → hold semantics then apply unchanged. 2.6, 2.9 and 2.11 are never promoted. |
| Autofix | `hygiene.dedupe` | The paraphrase-delete path (2.9) behind the same flag, logged in the autofix log like today's dedupe. |
| FAQ | `quality_gates.faq_answer_problem` + `drop_subjectless_faq` | The `type_mismatch` reason (2.11). |
| Repair guard | `trip_facts.new_specific_claims` + `hygiene.integrity_problems` | Run the promoted checks on (original, replacement) so a sentence repair cannot *introduce* a near→at, a flip or a difficulty promise (same pattern as AA-777). |
| Final pass | `service._final_integrity` | No change. Paraphrase autofix runs before it. |
| Registry | `services/quality/registry.py` (+ `taxonomy.yaml`) | `F20_SEED_ALIGN = "F20_seed_align"`, with severity and description. The AA-924 merge leaves F20 its own ledger entry (24 → 25 results). |
| Switch | env `T10_SEED_ALIGN` = `off` / `shadow` / `on` on the worker (pattern of `T9_FAQ_LLM_FILTER`, `T9_BRIEF_GROUNDING_MODE`) | `on` = never-hold blocking for unpromoted checks plus hold semantics for promoted ones. `PROMOTED` lives in code, so each promotion is a reviewed PR with its evidence. |
| Replay / eval | `scripts/aa789_recall_replay.py` | Add F20 and the per-check kinds (still no copy in the output). New `scripts/aa789_seed_align_eval.py`: per-class TP/FP/FN on a local labeled file. Labels stay in `.tmp-session`, never in the repo (CI golden-text guard). |
| Tests | `tests/unit/test_aa789_seed_align.py` | Synthetic fixtures only. Every clean verifier sentence from rounds 1–3 is a negative per check. Panel known-miss tests in `test_aa789_t10_recall.py` flip to positives as each class lands. One `importorskip("spacy")` guard keeps the old tests independent. |
| Image | `Dockerfile`, `requirements.txt` | `spacy==3.8.x` (exact pin), `en_core_web_sm` wheel by pinned release URL with `--hash`, `onnxruntime`, `tokenizers`, and the bge ONNX file fetched at build from a pinned revision with its SHA-256 checked (or from the scripts bucket). |

### Precision safeguards (how it never holds clean copy)

1. **Three keys or nothing** (§0). Each check abstains whenever the seed relation is absent. No seed, no finding: the
   design cannot create a claim the seed does not ground.
2. **Abstain on fragile parses.** For any check that can hold: (a) a sentence over 40 tokens is split at ';', ':',
   '—' and each part re-parsed alone. The relation must come out the same in the full and the split parse, else
   abstain (*parse stability*). (b) The path from trigger to target must contain no `dep` / `ROOT`-fragment labels.
   (c) Headings, quotes and CTA sentences are skipped (`_is_cta`, as today).
3. **Severity ladder per check, not per gate.** Every check starts in **shadow** (a flag, no routing effect). It moves
   to **never-hold** (one cheap repair on attempt 1, never a hold). It is **promoted** into F17/F18/F13 only after the
   gate in §6 is met. A check that never meets the bar stays never-hold or warn permanently.
4. **Kill switch**: `T10_SEED_ALIGN=off` restores today's behaviour byte for byte. A test asserts the ledger is
   unchanged with the switch off.
5. **Determinism**: pinned spaCy, model and ONNX weights. `nlp_version` is stored in the ledger, so a replay can
   report a version mismatch instead of a silent drift.
6. **Repair-side guard**: promoted checks also guard repairs, so a fix cannot trade one finding for another.
7. **Clean-corpus regression in CI**: the clean verifier sentences, synthetic near-misses per check (≥ 50 each), and
   a no-new-fire assertion on the round-3 harness, like PR #1140.

---

## 4. Expected precision and recall per class

Precision is the share of fires that are real defects when run on realistic copy (clean-majority). Recall is the share
of the panel's instances of that class caught. The panel denominators are tiny: Report 12 §1.3 counts 9 optional
flips (2 missed today), 6 overclaims, 8 repair/FAQ-integrity defects and 3 FAQ non-answers, and the other classes are a
handful of quotes across rounds 2–4. **Treat every recall number as ±20 points.**

| # | Class | Initial precision (offline) | After shadow tuning | Recall on the class | Can reach hold (≥ 0.98)? | Main reason |
|---|---|---|---|---|---|---|
| 2.1 | 'by boat' optional as planned | 0.90–0.95 | 0.96–0.98 | 50–65% | Borderline. Start never-hold | PP-attachment errors in long sentences; implicit traveler subject ('the lake is crossed by boat' passives handled via nsubjpass, generic 'best seen by boat' missed) |
| 2.2 | Reverse flip | 0.93–0.97 | ≥ 0.98 | 60–75% | **Yes** | The target-vs-locative split is exactly what the parser does well; a planned/optional seed status is unambiguous |
| 2.3 | Near → at | 0.97–0.99 | ≥ 0.98 | 70–85% of this form | **Yes** | Very narrow: event lexicon + prep + seed NEAR. Misses 'Mörön is where you break for lunch' (cleft) |
| 2.4 | 'Not a technical' difficulty promise | 0.88–0.94 | ~0.95 | 50–60% | No: never-hold | Polarity and comparatives ('easier than day two') are fragile; seed silence is weak evidence |
| 2.5 | 'Significant fraction of the world' | 0.95–0.99 | ≥ 0.98 | 75–85% of literal forms | **Yes** | A global-scope chain is a strong, rare signal. Misses 'hard to overstate' (no proposition) |
| 2.6 | Scopeless superlative | 0.80–0.90 | 0.88–0.93 | 60–70% | **No**: style-only | Legitimate evaluative superlatives are common; seeds back them in other words |
| 2.7 | Brief recipe leak | 0.97–0.99 | ≥ 0.98 | 40–70% (depends on the brief having a recipe) | **Yes** | Anchored to the actual brief text; misses paraphrased recipes |
| 2.8 | Naming-note leak | 0.96–0.99 | ≥ 0.98 | 60–75% | **Yes** | Place anchor + note-only lemmas; misses a leak that paraphrases the note ('a name locals find unfortunate') |
| 2.9 | Paraphrased repeat | 0.85–0.93 | 0.93–0.96 | 40–60% | **No**: autofix-delete or warn | Same-subject resolution is the weak key; pronoun chains and implicit subjects |
| 2.10 | Orphan section opener (pronoun) | 0.95–0.98 | ≥ 0.98 | 40–55% of the orphan class (pronoun/demonstrative only) | **Yes** (pronoun subset) | Broken grammar and split paragraphs are out of reach |
| 2.11 | FAQ non-answer | 0.93–0.97 on measurable types | ~0.97 | 30–50% overall | No: drop above floor, never hold | Open WHAT/WHY/HOW questions are unreachable deterministically |

**Out of reach for Approach A** (needs the claim-level / integrity LLM check of Report 12 §1.4, or a human):
- Claim-level unsupported facts in general (§1.3: 90 non-CTA claims, ~10% caught). A checks only the closed relation
  types above, not arbitrary propositions.
- Invented siting intent ('deliberate', 'never an accident', 'narrow' vs seed 'long'), hype without a proposition
  ('hard to overstate'), tenant voice fit.
- Broken grammar after a repair, and split paragraphs. Parse anomalies (multiple ROOTs, `dep` labels) can feed a
  **warn** at best.
- Paraphrased repeats with implicit or generic subjects, and paraphrased naming notes or recipes.
- FAQ non-answers to open questions.

### Statistical honesty about "≥ 0.98"

With 0 false fires in *n* labeled fires, the 95% upper bound on the false-fire rate is ≈ 3/*n* (rule of three). Showing
precision ≥ 0.98 at 95% confidence needs **≥ 150 fires with no false one**. Natural volumes on Dev are far lower: a
narrow class like near→at fires perhaps a few times per 80 pieces. So the gate in §6 uses a point estimate on ≥ 50
labeled fires (≤ 1 false), plus a hard 0-fire requirement on the targeted clean near-miss sets. It also reports the
Wilson bound rather than hiding it. Below 50 fires, a check stays never-hold whatever its point estimate. That is a
real cost of Approach A on Dev with no tenants.

---

## 5. Cost and latency

**LLM cost per piece: $0.** No new LLM call. The existing `t10_claims` (gpt-6-luna, $0.1/$0.5 per M) and `t10_judge`
(gpt-5.6-luna, $0.2/$1.2 per M) routes are unchanged.

Indirect costs:
- **Repairs triggered by findings**: each blocking finding costs one `t9_repair` sentence repair on Haiku ($1/$5 per
  M). That is ~3k tokens in and ~300 out ≈ **$0.0045 per repair**. True positives are repairs we want. At precision
  0.95 and ~0.5 new findings per piece, wasted repairs are ≈ $0.0001 per piece.
- **Compute**: CPU inside the worker task, which runs anyway. spaCy `sm` parses ~1,000 words in ~0.15 s per vCPU, so
  ~0.3 s on the worker's 0.5 vCPU. The seed parse (~900 words) is cached per seed hash. bge-small int8 embeds ~80
  sentences in ~0.3–0.8 s on 0.5 vCPU. Marginal cost $0.
- **Memory bump (if measured RSS needs it)**: worker 1024 → 2048 MiB on 1 always-on task ≈ 730 h × ~$0.005/GB-h ≈
  **~$3.6/month** (us-west-1 Fargate memory rate; autoscaled extra tasks pay the same rate only while up). This is the
  only recurring cost. Per the "cost before new AWS services" rule, it needs an explicit yes before the Infra PR.
- **Cohere alternative** (if the memory bump is refused): ~1.5k tokens per blog attempt and ~300 per LinkedIn attempt
  at $0.12 per M ≈ **$0.00018 / $0.00004 per attempt**. At 1,000 pieces × 2 attempts a month ≈ **$0.30/month**.

**Monthly at plausible volumes** (local model): 200 pieces/month (Dev rounds) or 3,000/month (early tenants) → $0 LLM,
~$0.02–$0.30 of wasted repairs, + ~$3.6 fixed if memory is bumped.

**Latency per attempt**: p50 ~0.6 s, p95 ≤ 2 s on 0.5 vCPU (parse + embed + checks). There is a one-off model load of
~2–3 s per worker process. A T9/T10 attempt is already 30–120 s of LLM calls, so the overhead is under 3%.

---

## 6. Rollout with measurable gates

**Phase 0: offline build and evaluation ($0, this week)**
- Eval set E (local, in `.tmp-session/S257/aa789-design/eval/`, never committed):
  - **E+**: every panel-quoted defect sentence from rounds 02/03/04/07, each joined to its piece's seed from
    `aa783_export.json` by `n`.
  - **E+synthetic**: deterministic perturbations of clean export sentences against their own seed. Swap near→at on a
    seed NEAR event, insert 'by boat' into a plan sentence of a moment whose boat ride is optional, write '<planned
    moment> is optional', put a pronoun opener under a heading with no referent, insert a naming-note clause, insert a
    brief recipe triad. Paraphrase pairs are hand- or subagent-written (≥ 30 pairs).
  - **E−**: all clean verifier sentences from rounds 1–3, the existing near-miss fixtures, ≥ 50 targeted near-misses
    per check (written against each trigger, as the verifiers did), and every sentence of the 40 export pieces not
    cited by the panel (~1,200; "clean" is approximate, so every fire there is labeled by hand).
- **Gate G1 (enter shadow)**: per check, **0 fires** on the verifier clean set and on the targeted near-miss set.
  Precision ≥ 0.95 on E+ ∪ E−. ≥ 1 true positive on each reachable panel example. `T10_SEED_ALIGN=off` gives a
  byte-identical ledger on the round-3 harness and the 40-piece replay.

**Phase 1: shadow ($0)**
- Merge with `T10_SEED_ALIGN=shadow` on the Dev worker: F20 findings are flags only.
- Replay **all stored pieces and their discarded attempts** from Dev `content_piece` (read-only, via ECS exec with the
  container's `DATABASE_URL`; count them first). Label every F20 fire with a two-reviewer agent panel, and have Nghiệp
  spot-check 20%.
- **Gate G2 (never-hold blocking)**: ≥ 30 labeled fires for the check, precision ≥ 0.95, no "wrong direction" false
  fire (for example a caveat read as a promise), still 0 fires on E−.
- **Gate G3 (promote to hold semantics in F17/F18/F13)**: ≥ 50 labeled fires cumulative, ≤ 1 false (point precision
  ≥ 0.98, Wilson lower bound reported), 0 fires on E−, and the repair-guard test passing. Classes 2.6, 2.9 and 2.11
  are capped at never-hold or autofix by design.

**Phase 2: never-hold blocking (small paid cost, later)**
- `T10_SEED_ALIGN=on` for checks past G2. Measure the **repair success rate** on true positives: ≥ 90% fixed in one
  `t9_repair`, and 0 repairs that introduce a new F17/F18 finding. This needs paid `t9_repair` calls on real or
  replayed pieces: ~$0.0045 each, so ≤ $0.50 for 100 findings.

**Phase 3: blocking with hold**
- One PR per promoted check, with its evidence table in the PR body (fires, labels, precision, repair success). Watch
  the hold rate on the next T-round: an increase of more than 2 points of pieces held on a promoted check triggers an
  automatic review (demote by editing `PROMOTED`).

---

## 7. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| Parser errors on long editorial sentences (PP attachment, coordination) | False fires or misses | Parse-stability abstain, 40-token cap for hold-capable checks, ladder before promotion |
| Seed format drift (`atom_seed` labels change) | Checks go silently quiet | Contract test from the real seed builder; graph-empty metric in the ledger |
| Alias gaps (Moron/Mörön/Murun, possessives, diacritics) | Misses (never false fires: an unresolved alias abstains) | Reuse `fold`, `_name_aliases`, the `Naming:` parse |
| Rules engine whack-a-mole moves from regex to rules | Maintenance cost | Each check is anchored to a seed relation, so a new phrase needs a new *relation*, not a new pattern; checks that need more than 2 tuning rounds are capped at never-hold |
| Small, AI-labeled eval set (Report 12 §1.5: no human κ yet) | Overstated precision | Targeted near-miss sets; Nghiệp spot-checks; the ≥ 50-fire rule |
| Low natural volume on Dev (no tenants) | Checks cannot reach G3 for months | Replay every stored attempt; accept never-hold as the steady state for rare classes |
| Image and memory growth (+~150 MB image, +~300 MB RSS) | OOM on the 1 GiB worker; slower deploys | Lazy load in the worker only; measure RSS in Phase 0; Infra PR for 2 GiB (~$3.6/mo) after an explicit yes |
| Model upgrades change parses | Silent behaviour change | Exact pins + hashes; `nlp_version` in the ledger; replay diff required on any bump |
| CI time (model load ~1–2 s; tests need the model) | Slower CI | One session-scoped fixture; the model wheel cached in CI |
| Golden-text guard | Accidental commit of real copy | Eval data only in `.tmp-session`; fixtures synthetic; replay prints kinds only (as today) |

---

## 8. Effort

| PR | Repo | Content | Days |
|---|---|---|---|
| A1 | CIS | `nlp_parse.py`, `seed_graph.py`, pins + Dockerfile, the `F20_seed_align` result (shadow only), registry/taxonomy entry, switch, seed-builder contract test, switch-off byte-identity test | 2 |
| A2 | CIS | F17 checks 2.1–2.4 + repair guard + synthetic tests | 2 |
| A3 | CIS | F18 checks 2.5 (and 2.6 as style-only) | 1 |
| A4 | CIS | F13 checks 2.7, 2.8, 2.10 | 1.5 |
| A5 | CIS | `sentence_embed.py` (ONNX bge-small) + paraphrase autofix 2.9 | 1.5–2 |
| A6 | CIS | FAQ `type_mismatch` 2.11 (+ optional pre-filter for `t9_faq_answer_fit`) | 1 |
| A7 | CIS | Eval script + replay extension | 1 |
| I1 | Infra | Worker memory 1024 → 2048 MiB (only if Phase 0 RSS needs it; cost approval first) | 0.25 |
| P* | CIS | One small promotion PR per check that passes G3 (evidence in the body) | 0.25 each |

Total **~10–11 engineer-days, 7 CIS PRs + 1 Infra PR**, plus promotion PRs over the following weeks. A1 and A7 come
first. A2–A6 are independent after A1 and can run in parallel lanes.

---

## 9. What can be built and evaluated this week for $0, and what needs paid calls later

**This week, $0:**
- A local venv in `.tmp-session` with spaCy 3.8 + `en_core_web_sm` + onnxruntime + bge-small. Neither is installed on
  the laptop today; both are free to install.
- `SeedGraph` + every check of §2 in a branch, the eval set E (E+, E+synthetic, E−), and per-class precision and
  recall on it: Gate G1.
- The round-3 harness and the 40-piece replay, with the switch off (byte-identical) and in shadow (new fires listed by
  kind).
- RSS and latency measured on a 0.5-vCPU container locally, to decide on the Infra memory PR.
- Merge A1 + A7 (and any check that passes G1) with `T10_SEED_ALIGN=shadow`. Then a read-only replay of all stored Dev
  pieces and attempts through ECS exec, labeled by an agent panel. That covers Phase 1 at $0, apart from the ECS/RDS
  that is already running.

**Later, paid (small):**
- Phase 2 repair-success measurement: paid `t9_repair` calls, ~$0.0045 each, ≤ ~$0.50 per 100 findings.
- Live shadow on *new* writer output needs paid T9 writer runs. There are no tenants, so shadow volume comes only from
  rounds we choose to run.
- If memory is refused: Cohere Embed v4 on acc2 via a new gateway stage (~$0.30/month at 1,000 pieces).
- The out-of-reach classes (claim-level fidelity, siting intent, broken grammar, open FAQ answers) need the LLM
  post-repair integrity check. That cost belongs to the LLM design, not to Approach A.
