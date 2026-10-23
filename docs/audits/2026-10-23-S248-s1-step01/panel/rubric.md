# S1 panel rubric v1 (fixed for M2a S1-first, S248)

Frozen for the repeatability passes (step 0/1) and the A/B runs (step 3). Do not edit between runs; a change means a
new version and a new repeatability read.

## What you get

A packet (`packet-a.json` or `packet-b.json`): pages, each with the FULL raw `source` the writer read and the written
`page` (name, subtitle, summary, highlights, itineraries, seo_title, seo_meta). No labels, no pipeline verdicts, no
code-check findings. Read the whole source for every page before judging it.

## What counts as an error

Judge only what a customer or a travel agency would read as a fact about THIS tour.

| class | meaning | example |
|---|---|---|
| `invented_promise` | a service, inclusion, activity or condition the source never offers | "lunch included" when meals are excluded; "suitable for swimmers" |
| `invented_fact` | a tour fact the source never states (number, name, timing, amenity) | "Class III–IV rapids" with no grade in the source |
| `wrong_fact` | contradicts the source | the source's 30 *species* written as 30 *lakes* |
| `wrong_place_or_direction` | wrong place, overnight, order or compass direction | "drive south" when the place is north |
| `day_structure` | day blocks that do not match the source days | a 3-hour ride written as Day 1–4 |
| `scope_drift` | the page sells a different tour or theme than the source | a film-location tour rewritten as generic local life |
| `overclaim` | superlative or rarity the source does not make | "Bhutan's most challenging route" |
| `cut_text` | a field stops mid-phrase | meta ending "…with professional." |
| `other` | anything else a reader would need fixed (say what) | |

Not an error: background about a named place that is true and not presented as part of the tour (the writer policy
allows it), wording or style you would phrase differently, a fact that is in the source even if it sounds unlikely.

Severity: `serious` when an agency could sell something wrong because of it (a promise, a wrong inclusion, a wrong
day count, a wrong figure a customer plans around); otherwise `minor`.

## What to return (one JSON file per pass: `pass-a.json` / `pass-b.json`)

```json
{"pass": "a", "rubric": "s1-panel-v1", "pages": [
  {"page_id": "p01", "sample_id": "s1-040",
   "verdict": "publish_verbatim | light_edit | heavy_edit | reject",
   "agency_use": "yes | with_edits | no",
   "checkable_claims": 23,
   "errors": [{"class": "invented_fact", "severity": "serious", "field": "seo_meta",
               "quote": "moderate climbing difficulty", "why": "the source gives no difficulty"}]}
]}
```

- `verdict`: `publish_verbatim` = no change; `light_edit` = only wording, no fact or structure change;
  `heavy_edit` = at least one fact, promise or structure must change; `reject` = rewrite from scratch.
- `checkable_claims`: how many factual claims about the tour the page makes that a reader could check against the
  source (the denominator of the A/B error rate). Count, do not estimate.
- `errors`: every error, one entry each, `quote` copied exactly from the page.

## For the A/B (step 3) only

Pairwise question, both orders: "An agency must publish one of these two pages for this tour. Which one?" →
`A | B | tie`, with one sentence why.
