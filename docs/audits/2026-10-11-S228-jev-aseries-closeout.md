# Jev A-series audit — close-out + calibration plan (S228, 2026-10-11)

Part of **AA-756**. Builds on the S226 inventory (`2026-10-11-S226-jev-inventory.md`) and its S227
correction. This pass is **$0, read-only** (`shared.decision_question` + `shared.decision_log` via
ECS exec; no new Jev calls, no threshold change). It does two things:

1. Verifies which A-series gates are **live and enforcing** today, so the four build-issues
   (AA-690/692/694/695) can be closed against evidence and all remaining Jev calibration work is
   consolidated under AA-756.
2. Re-examines the three "retire candidates" from the first S228 pass and concludes **keep all of
   them** — the decision is calibrate, not retire. Nghiệp's call (S228): keep every question, only
   adjust calibration.

Source data: `.tmp-session/s228_jev.json`, `s228_jev2.json`, `s228_retire.json`, `s228_vc.json`.

## 1. Correcting the window: the 30-day numbers mix pre- and post-v2 runs

The S226 table is a 30-day window that straddles the S223 threshold-v2 change (applied 2026-10-10
04:09 UTC). Looking **only since v2** gives the true current behaviour. Several questions calibrate
far better than the 30-day blended numbers suggest:

| question | 30-day grey% | since-v2 grey% | note |
|---|---:|---:|---|
| a3_demand_belongs | 20.2 | **3.2** | v2 reject 0.40→0.70 now decides firmly |
| a3_question_about_here | 46.4 | **16.7** | reject 83% since v2 |
| a3_landing_belongs | 31.2 | 20.6 | reject 64% |
| a1_claim_supported | 56.9 | **58.2** (7d 64.6) | unchanged — the real calibration target |
| a3_atom_in_text | 95.7 | 98.1 | high grey, but see §3 — not dead |

Totals since v2: **47,949 decisions / $1.27**. The 7-day cost is **$7.76**, of which
`a1_claim_supported` is **$5.75 (74%)**.

## 2. Live-enforce verification (evidence to close AA-690/692/694/695)

All verified against `shared.decision_question` (config) + `shared.decision_log` (actual runs).

**AA-694 — A3 atoms/Score (A3-1/2/5/6).** All four enforce in config and run enforce in the log:

| question | mode | floor | tv |
|---|---|---|---|
| a3_atom_in_text | enforce | reject ≤ 0.30 | 1 |
| a3_activity_type | enforce | accept ≥ 0.90 | 2 |
| a3_demand_belongs | enforce | reject ≤ 0.70 | 2 |
| a3_landing_belongs | enforce | reject ≤ 0.40 | 2 |

Done-when met (floors recorded S204/S205, Bhutan before/after posted on the issue). → **close.**

**AA-690 — A0 ingest (A0-1/3/4).** `a0_row_kind`, `a0_itinerary_usable`, `a0_country` all enforce
in config; `a0_row_kind` shows **455 enforce-accept** (last run 2026-10-01). A0 only fires on upload,
so log volume is sparse by nature. A0-2 near-duplicate rule shipped (S206, 20 duplicates superseded);
A0-5 column map fixed deterministically (static map, no Jev). Done-when met. → **close.**

**AA-692 — A1/A2 (A1-3, A1-4).** A1-3 (meal/clock-time via the enforced `a1_claim_supported` + regex)
and A1-4 (`a1_brand_fit` shadow tie-break) shipped S205. `a1_brand_fit` is a ±0.5 band tie-break, so
it fires rarely (3 verdicts/60d — expected). A1-2 dropped (measured not worth it: 36 GPT calls/$0.18),
A1-5 deferred (soft codes change no outcome), A2-1 moved to UI v2. Build scope complete; the
`a1_brand_fit` / `a1_promise_unsupported` calibration carries into AA-756. → **close.**

**AA-695 — A3 segment.** `a3_same_place` enforce (reject ≤ 0.10). Segments now **11,306 total /
10,327 non-empty**, consistent with the S223 cleanup result (~10,281 real after deleting 5,045 empty
/ all-excluded segments; small rise from new atomized tours). The remaining `a3_same_moment` idea was
always tracked under AA-756. Done-when met. → **close.**

## 3. Retire candidates re-examined — KEEP ALL (code-traced + reject samples)

The first S228 pass flagged three high-grey questions as possible retires. Tracing the call sites
(`a3_atomize.py`, `s1_prefetch.py`, `segment_research_batch.py`) and sampling their real rejects
reversed that:

- **`a3_atom_in_text` — KEEP.** 98% grey, but **124 real enforce-rejects in 30 days** (not cached),
  e.g. "hotel — check in", "Delhi to Colombo — depart on included flight", "South Delhi — drive back
  to hotel". A reject stops the atom from being stored. The prompt day-scoping (AA-694 A3-1) and
  `is_logistics_atom` catch most noise, but this gate still removes ~124 off-day/logistics atoms that
  slip past both. High grey here means "last-line guard, rarely needed, correct when it fires" — not
  dead weight. Retiring it would let that noise back into the atom store.
- **`a1_keyword_about_tour` — KEEP.** Config enforce (set S224) but every logged run is still shadow
  (last run 2026-10-08, before the mode flip; s1_prefetch hasn't run since). Its last shadow window
  was 94.5% grey, so it is effectively "enforce-configured but not yet calibrated". The fix is
  calibration (accept/reject floors) before the next prefetch run — not retirement. Code: a confident
  reject drops an off-topic keyword idea, a confident accept recovers a synonym the substring rule
  missed — both are useful once calibrated.
- **`a3_keyword_belongs` — KEEP.** Nearly idle (9 enforce actions in 30 days, last 2026-09-30), its
  two rejects ("hotel checkout time/procedures") already covered by `is_lodging_search`. Low traffic,
  but it still trims generic-category keywords ("Nyuto Hot Spring" → "hot springs" 368k/mo) before any
  DataForSEO purchase. Cost is negligible ($0.004/30d), so keeping it costs nothing and preserves the
  guard.

**Conclusion:** no question retired. Every A-series question earns its place either by acting today
or by being a cheap last-line guard. The work is calibration.

## 4. Calibration plan (the remaining paid work — stays in AA-756)

Priority order, by grey share × cost:

1. **`a1_claim_supported`** (74% of Jev cost, 58–65% grey, accept-only today). Hand-label ~100 grey
   sentences, set a `reject_ceiling` so clear unsupported claims reject instead of greying, re-measure
   grey share and cost on one wave (<$1 Jev). Upstream fix (AA-748 structured facts) reduces the input
   first; this calibrates what remains.
2. **`a1_keyword_about_tour`** — give it accept/reject floors from a labelled sample, then let the
   next s1_prefetch run exercise it in enforce for real.
3. **`a1_promise_unsupported`** (type-B, 100% grey, tv 0) — needs thresholds + a labelled sample before
   it can drive a writer rule.
4. **Close the loop:** start writing `decision_log.outcome` where a later step knows the truth (atom
   soft-delete, LLM-fallback verdict, human review), so future recalibration needs no manual sample.
   Fill is 0% today across every question.

## 5. Issue consolidation (Nghiệp approved, Cách 1)

- **Close** AA-690, AA-692, AA-694, AA-695 — build scope done, gates live-verified above.
- **AA-756** becomes the single home for all remaining Jev calibration + outcome-loop work (§4).
- Result: one In-Progress Jev calibration issue instead of five scattered ones.
