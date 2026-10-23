# S1 panel rubric v1.1 (S248, M2a S1-first, Refs AA-645)

Replaces v1 (`rubric.md`, kept unchanged) for the held-out check and the A/B. Fitted on the 30 TRAIN pages of
`split-v1.1.json` only; why each rule exists is in `calibration.md`. Do not edit between runs: a change means v1.2
and a new repeatability read.

What changed from v1, in one line each:
- severity comes from a fixed table (§3), not from "could an agency sell something wrong";
- four **hard-fail** kinds (§2) fail a page on their own, whatever else is on it;
- one wrong claim = one error, however many fields repeat it (§4);
- the verdict is computed from the error list by a fixed rule (§5), not chosen by the judge;
- the rate denominator is counted by code (`apply_v11.py`), not by the judge.

## 1. What you get and what you judge

A packet: pages, each with the FULL raw `source` the writer read and the written `page` (name, subtitle, summary,
highlights, itineraries, seo_title, seo_meta). No labels, no pipeline verdicts, no code-check findings. Read the
whole source before judging a page.

Judge only what a customer or a travel agency would read as a fact about THIS tour. The question behind every call:
*"Can an agency send this page to a customer after a few one-phrase fixes, or must someone change what the tour is,
what it includes, or how its days run?"*

Not an error at all: wording or style you would phrase differently; a fact that is in the source even if it sounds
unlikely; true background about a named place that is not presented as part of the tour (writer policy allows it).

If the source contradicts itself, the source's **day-by-day list** wins for what the customer gets (days, nights,
places visited, activities). Copying the source's own contradiction is `other` / minor, unless it lands in the
page as one of the hard-fail kinds below (for example a day count that disagrees with the page's own day blocks).

## 2. Hard-fail kinds (always `severity: serious` and `hard_fail: true`)

| kind | class to use | fires when |
|---|---|---|
| HF-1 broken day structure | `day_structure` | (a) a day or night count anywhere on the page (name, title, summary, meta) disagrees with the page's own day blocks or with the source's day list; (b) day blocks that split, merge, drop, duplicate or reorder source days, or end the trip mid-way (a "Departure" before the last day); an hours-long tour written as several days; (c) a day block puts the night in a town the source does not, or the day blocks change the number of nights at a place |
| HF-2 invented promise | `invented_promise` | the page offers something the source does not: an inclusion (meals, transfers, guide, entrance fees), a source **exclusion** presented as included, an accommodation standard or amenity (star rating, "heritage", spa, pool, thermal pools), an activity the source does not have (diving where the source has snorkelling, hands-on contact with animals, a market visit in a town with no market), a place in a headline field (name, subtitle, summary, highlights, meta) that no day visits; or a suitability / safety claim that **contradicts** the source ("suitable for beginners" when the source says extreme) |
| HF-3 different tour | `scope_drift` | the page sells a different tour or theme than the source (a film-location tour rewritten as generic local life) |
| HF-4 cut text | `cut_text` | any page field stops mid-phrase or mid-list ("…with technical guides and full.", an itinerary that breaks off mid-sentence) |

Not HF-2 (use §3 instead): a conditional or optional item presented as certain (serious, S5); a loose paraphrase of
something the source does offer, such as a craft-family visit called a "workshop" (minor); a suitability phrase that
paraphrases a source fact ("accessible for all levels" for "no elevation gain") (minor).

## 3. Serious vs minor (errors that are not hard-fail)

**Serious** — the customer would plan, pay or pack differently, or the page states as fact something the source
explicitly contradicts:

| code | class | serious when |
|---|---|---|
| S1 | `wrong_fact` | a figure contradicts the source: distance, altitude, elevation (gain written as loss counts), duration, count, date, price, group size, number of riding / trekking / activity days. Below the magnitude floor it is minor: durations off by **less than 1 hour**, distances off by **less than 20 %**, rounding. |
| S2 | `invented_fact` | a figure or grade the source never gives that a customer plans or buys around: leg or activity duration of 1 hour or more, a total or daily distance, a difficulty / fitness / rapid grade, a price or admission fee, a season or availability ("operates year-round"), an accommodation location ("within park boundaries") |
| S3 | `wrong_place_or_direction` | a wrong name or place for something the tour does: wrong hotel or property type for the night ("monastery" for the guesthouse), wrong border crossing, a stop put in the wrong town / state / region / country, a product name that puts the parks in the wrong region |
| S4 | `wrong_place_or_direction` | a compass direction that contradicts the source or real geography for a leg the group travels; an activity moved to another day or another part of the day (morning ↔ evening, before ↔ after breakfast); uphill written as downhill |
| S5 | `wrong_fact` | something the source makes conditional ("we will try to", "if time permits", "can be arranged", optional) presented as included or certain |
| S6 | `wrong_fact` | a wrong count of what the tour delivers or shows: countries visited, full days of an activity, rest days, peaks in view, figures on display, nights at a place when stated outside the day blocks ("nights in a village lodge" for one night) |
| S7 | `wrong_fact` | a statement about a named place that the source explicitly contradicts (the source says Paris, the page says Rome; the source dates a monument 1193, the page calls it Mughal-era) |

**Minor** — everything else a careful editor would still fix:
- background not in the source, true or unverifiable, not presented as part of the tour (dates, sizes, names of
  nearby features, which face of a mountain you see);
- atmosphere, pacing and sensory filler ("narrow stair passages", "a sandy beach", "few trekkers venture");
- `overclaim`: superlatives and rankings ("among the best bike tours", "most challenging route") — unless it is a
  measurable falsehood about the tour, then S1/S6;
- time-of-day colour inside the same part of the day ("afternoon" → "as the light fades", "start the day" →
  "before dawn");
- figures below the S1 magnitude floor; a loose paraphrase of an offered activity; a recognisable misspelling of a
  name ("Khao Phraya"); a duplicated sentence; a contradiction copied from the source (`other`).

## 4. Counting rules

- **One wrong claim = one error.** If the same claim appears in several fields ("Class III–IV rapids" in subtitle,
  summary, highlights, itinerary and meta), write ONE error and list every field in `fields`.
- Two different wrong claims in one sentence are two errors.
- `quote` is copied exactly from the page (shortest span that shows the error); `why` says what the source says.
- When unsure between serious and minor, apply the table literally; do not upgrade a minor because the page has
  many of them, and do not downgrade a serious because the page is otherwise good.

## 5. Verdict (computed — do not choose it by feel)

`apply_v11.py` recomputes this from your error list; its value is the one that counts. Fill `verdict` by the same
rule so a reader of your file sees it.

```
hard   = number of errors with hard_fail: true
S      = number of serious errors (hard ones included)
n      = sentences of 4+ words in the page (all seven fields) — counted by apply_v11.py
reject            if any scope_drift error, or hard >= 3
heavy_edit        else if hard >= 1, or (S >= 2 and S / n > 0.017)
publish_verbatim  else if there are no errors at all
light_edit        otherwise
pass = publish_verbatim or light_edit
```

In words: a hard-fail fails the page; one serious slip on its own never does; two or more serious errors fail the
page unless the page is long enough that they stay at or below 1.7 per 100 sentences; minor errors never fail a page.

## 6. What to return (one JSON file per pass)

```json
{"pass": "h1", "rubric": "s1-panel-v1.1", "pages": [
  {"page_id": "h01", "sample_id": "s1-0xx",
   "verdict": "publish_verbatim | light_edit | heavy_edit | reject",
   "agency_use": "yes | with_edits | no",
   "checkable_claims": 40,
   "errors": [{"class": "invented_fact", "severity": "serious", "hard_fail": false,
               "fields": ["seo_meta"], "field": "seo_meta",
               "quote": "moderate climbing difficulty", "why": "the source gives no difficulty grade"}]}
]}
```

- `class`: one of `invented_promise`, `invented_fact`, `wrong_fact`, `wrong_place_or_direction`, `day_structure`,
  `scope_drift`, `overclaim`, `cut_text`, `other`.
- `field` = the first entry of `fields` (kept for `score_repeatability.py`).
- `checkable_claims`: your count of factual claims a reader could check against the source, for reference only; the
  v1.1 verdict does not use it.
- Every page gets an entry, including pages with no errors (`"errors": []`).

## 7. For the A/B (step 3) only

Pairwise question, both orders: "An agency must publish one of these two pages for this tour. Which one?" →
`A | B | tie`, with one sentence why. Score each page with §2–§5 first; the pairwise answer is separate.
