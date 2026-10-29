# AA-789 eval set: T10 missed defect classes

This set measures every approach in the AA-789 design round. It covers rules, an extra LLM stage and a post-repair integrity check. It holds the 11 defect classes that the T10 gates still miss after CIS PR #1140, and it holds the clean copy that a detector must leave alone, because anything that can hold a piece needs **≥ 0.98 precision on clean copy**.

**Do not commit this folder to any repo.** It quotes S234 panel piece text, and a CI guard forbids committing golden text. It stays in `.tmp-session/`.

## Files

| File | What it is |
|---|---|
| `eval_set.jsonl` | 405 items, one JSON object per line |
| `score.py` | Scores a predictions file and prints per-class precision, recall and F1, plus the clean false-positive rate |
| `build_eval_set.py` | Builds `eval_set.jsonl` and `counts.json`. It is the source of truth: edit items there and rebuild |
| `counts.json` | The counts below, in machine-readable form |

Rebuild with `python3 -I build_eval_set.py`. The build fails on a duplicate id, a duplicate text, or a class with fewer than 8 defect or 15 clean items.

## Item schema

```json
{"id": "near-d-03", "class": "near_as_at", "text": "…", "seed_excerpt": "…", "label": "defect",
 "provenance": "S234 panel r4#16 (r4 class 3: lunch 'at' Mörön)", "channel": "blog",
 "note": "optional", "contested": false}
```

- `class`: one of the 11 classes below, or `clean`. For a `clean`-label item it names the class the item is a hard negative for. `class: "clean"` holds general clean copy, mostly verifier sentences aimed at other gates.
- `text`: a sentence or a short passage. A passage can include an H2 (`## …`) or an FAQ pair (`**Q: …**\nA: …`) when the class needs that context.
- `seed_excerpt`: the minimal source facts needed to judge the item. It comes from the real S234 seed (Mongolia days 3–14, Punakha, Tiger's Nest, Kuang Si) or from a verifier seed (Ha Long, Thorong La, Baikal, Mae Taeng, Sapa, Luang Prabang, Komodo, Ladakh). Lines marked "writer instruction, not copy" are brief text that the writer sees but must not echo. Feed the excerpt to a detector as its seed.
- `label`: `defect` or `clean`. **It is relative to the 11 classes only.** An item can carry an unrelated problem, such as an invented 4WD van or a stock contrast frame, and still be `clean`; those 18 items have a `note` starting "out of class". Other notes explain a labelling choice.
- `contested: true` (10 items, all labelled clean): membership in the class is arguable. Examples: a locally scoped superlative that the seed does not make ("one of the highest motorable passes in Ladakh"), and "No technical climbing gear is needed" next to the panel-flagged "not a technical climb". `score.py` skips these unless you pass `--include-contested`.
- `provenance`: where the item came from. `S234 panel r<round>#<piece>` means a panel-cited defect, quoted from the final text in `s249/aa783_export.json` or quoted from the report when the piece is not in the export. `S234 r<round>#<piece> piece text, labelled from the seed` means real copy that the panel did not cite for this class. `S257 verifier round N` means the S257 verification sentences. Round 1 is the verifier report (`aa789-verify.json`), round 2 the reviewer, round 3 `ROUND3_CLEAN` (= scratchpad `h/samples.py`), round 4 `v40/samples40.py`, and the probe set `v40/samplesprobe.py`. `test_aa789_t10_recall.py near-miss (own)` means the test's own near-misses. `synthetic shape of …` means an item written for this set; those that are also test known-miss fixtures say so.

## Classes and labelling rules

The seed is the ground truth.

| class | defect when… | clean when… |
|---|---|---|
| `optional_as_planned` | an activity the seed lists under "Optional activities" (the boat on day 5, kayaking, herbal bath, alms-giving) is told as part of the plan | it is hedged: optional, can, if you wish, can be added, cost extra, or a supply boat that is not the activity |
| `planned_as_optional` | a planned moment (Tsaatan excursion, caldera trek, Tiger's Nest hike, Punakha visit) is called optional or on request | only a sub-activity is optional (riding a reindeer at the planned visit), or a person opts out of a stop that still happens |
| `near_as_at` | the seed says lunch or a stop *near* X, and the copy puts it *at / in / here* X | near, outskirts or passes through; or the seed itself says "at" (the View Café) |
| `difficulty_promise` | a pace, ease or difficulty promise the seed does not give ("not a technical climb", "full without being relentless", "gentle", "never rushed"), or one that contradicts the seed | the seed gives it (Thorong La "non-technical"), or it is a caveat or safety advice (strenuous, demanding, slippery) |
| `world_share_unsupported` | a share of the world or planet (fraction, share, portion, "great reservoir", "most of the world's …") that the seed does not give, including a wrong figure ("two percent" for 0.4%) | the seed's figure, stated as given (0.4 percent; Baikal 20 percent "a significant share"), or a share of a trip or day |
| `scopeless_superlative` | a superlative, uniqueness or rarity claim the seed does not make. It can be promotional ("most coherent itineraries", "few places can offer", "hard to overstate"), scoped to the world or earth, or wider than the seed (Central Asia → Asia/earth) | the seed makes it at the same scope ("one of the last of its kind in the world", "largest in Central Asia by volume", "most distinct ethnic groups"). A factual, locally scoped one that the seed lacks is `contested` |
| `brief_recipe_leak` | writer-brief wording appears as copy: the thin-moment recipe ("one ruined site, one date, one fact", "A Single Sentence on…"), the audience range ("seven-to-sixteen"), the angle wording ("two named rivers") or the voice instruction | the same surface forms used naturally ("one tent, one stove", "two named passes, Dochula and Pele La", "A single wooden bridge") |
| `naming_note_leak` | the seed's Naming note is turned into copy: "phonetic approximation best avoided", "acceptable for international audiences", "no significant spelling variants" | a real pronunciation or spelling tip, variant spellings, or "also known as" |
| `paraphrased_repeat` | the same claim is told twice in other words in the body (repair duplicates, a LinkedIn hook restated in paragraph 1, the same thesis repeated) | two different facts in a shared frame, parallel day sections, or an FAQ answer that restates the body (expected) |
| `orphan_opener` | a sentence opens a section or paragraph with no subject or antecedent ("Access requires…", "What they find…", "Knowing them…"), or is misplaced in the wrong section | the subject is named, or the same sentence follows its antecedent |
| `faq_non_answer` | the answer does not answer its question (wrong attribute, negative only, truncated) | it answers, including a terse "No. Cash only." or an answer that opens with a contrast and then answers |

Two choices are worth knowing:

- **Trekking along shorelines.** In the atomised Mongolia seed it sits on its own line, but it is the tail of the original optional list, and the r4 panel treated it as optional ("boat and trekking presented as included"). No label in this set depends on trekking's status; the boat decides.
- **F15 voice is out of scope.** Contrast frames and stock lines are another gate. Their positive fixtures (for example "not a scenic preference", "does not perform for visitors. It simply continues.") are left out, and three probe sentences of that kind are left out too. The verifier's clean contrast and "does not perform / tolerates" sentences are included as `class: clean`.

## Counts

Excluding contested items:

| class | defect | clean | contested |
|---|---:|---:|---:|
| optional_as_planned | 13 | 25 | 0 |
| planned_as_optional | 12 | 18 | 0 |
| near_as_at | 15 | 18 | 0 |
| difficulty_promise | 14 | 18 | 1 |
| world_share_unsupported | 11 | 16 | 1 |
| scopeless_superlative | 22 | 15 | 7 |
| brief_recipe_leak | 13 | 15 | 0 |
| naming_note_leak | 11 | 17 | 0 |
| paraphrased_repeat | 13 | 17 | 0 |
| orphan_opener | 11 | 15 | 0 |
| faq_non_answer | 14 | 18 | 1 |
| clean (general) | – | 54 | 0 |
| **total** | **149** | **246** | **10** |

Channels: 375 blog items and 30 LinkedIn items (14 defect, 16 clean).

By provenance:

| source | defect | clean |
|---|---:|---:|
| S234 panel-cited defect (real piece text or report quote) | 39 | – |
| S234 real piece text, not panel-cited, labelled from the seed | 18 | 42 |
| S257 verifier rounds 1–4 and probe (3 relabelled as defects, see below) | 3 | 123 |
| test_aa789 own near-misses (clean) and one relabelled fixture | 1 | 30 |
| Synthetic, shape of a panel example; 20 of these are test_aa789 known-miss fixtures | 88 | 61 |

Every clean sentence from the four verifier rounds and the test's negative sets is in the set, with the F15 exclusions above. Some were written as clean for a *regex*, but the seed shows they carry one of the classes, so they are relabelled as defects and their provenance says so:

- "The trail is a gentle gradual ascent…" (round 3): `difficulty_promise`, because "gentle" is not in the seed.
- "Children are rarely worn out by midday here." (test): `difficulty_promise`.
- "Komodo is the only place in the world where these dragons live in the wild…" (round 4): `scopeless_superlative`.
- "Pangong Tso is a landscape that most of the world has never seen." (probe positive): `scopeless_superlative`.

## How to score

1. Run the detector on each item: `text` plus `seed_excerpt` (plus `channel` if it matters). Write one line per item:

   ```json
   {"id": "near-d-03", "flagged": true}
   {"id": "near-c-07", "flagged": false, "class": "near_as_at"}
   ```

   `class` is optional. With `--strict-class`, a flagged defect counts only if the predicted class matches. Use it when one detector covers several classes.

2. Run `python3 score.py predictions.jsonl [--include-contested] [--strict-class] [--channel blog|linkedin] [--show-errors]`.

What it prints:

- **Per class c:** TP is defects of c that were flagged, FN is defects of c that were missed, and FP is clean items of c that were flagged (these are c's hard negatives). Precision = TP/(TP+FP), recall = TP/(TP+FN), and F1. Per-class precision is computed against that class's own hard negatives. It shows whether the detector separates the defect from its near-misses.
- **ALL (micro):** totals over the 11 classes, with general `clean` items adding false positives only.
- **Clean FP rate:** flagged clean items divided by all clean items (246 without contested items), with a Wilson 95% upper bound. **This is the hold bar.** Clean-copy precision = 1 − FP rate must be ≥ 0.98. The bar is reported two ways: on the point estimate, and on the bound. With 246 clean items the bound passes only at 0 false positives (0/246 gives an upper bound of 0.0154). One false positive passes on the point estimate but must be confirmed by the shadow run before the check may hold a piece.
- **A missing prediction counts as not flagged** and is reported. Unknown ids are ignored and listed.

A detector that only *warns* or *repairs*, and never holds, can be judged on recall with a looser precision bar. A detector that can hold needs the bar above on this set and then in shadow on Dev output.

## Caveats

- **Single labeller.** One agent labelled every item from the seed, applying the rules above. The panel-cited items follow the S234 panel. Seed-labelled real text and synthetic items have not been checked by a second rater; a second pass is advisable before a precision claim is used to justify a hold.
- **59% of defects are synthetic** (88 of 149), because the 80 panel pieces contain few examples of some classes. Naming-note leaks have one real example, and several classes have 2–4. The synthetic items copy the panel shapes, but real writer output will vary more. Recall here is an upper bound.
- **The domain is narrow.** Most items use the Mongolia, Punakha, Tiger's Nest and Kuang Si seeds from S234. Measure generalisation on a fresh Dev batch (shadow).
- **Seed excerpts are minimal and normalised**, not the full T2 seed. A detector that needs the real seed structure (the `trip_facts` parser, for example) has to re-wrap the excerpt or run on full pieces in shadow.
- **No baseline has been run yet.** Running main's deterministic checks (`hygiene.find_issues`, `trip_facts.find_trip_fact_issues`, `quality_gates.faq_answer_problem`) over this set is the natural first row of the comparison.
