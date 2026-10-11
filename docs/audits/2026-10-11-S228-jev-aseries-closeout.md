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

---

# Part 2 — Calibration proposals (all 5 items, S228, for one decision)

All numbers below are **offline, $0**: zones are recomputed from `probability` already in
`decision_log` (non-cached, last 14–30 days) under candidate floors, exactly as `zone_for()` would.
No Jev calls, no threshold applied. The only paid step (one measurement wave, <$1 Jev) comes **after**
Nghiệp approves the floors — that is the AA-756 done-when, not this report.

Source: `.tmp-session/s228_calib.json`.

## Decision table — one row per lever (approve / adjust / hold)

| # | Question | Lever | Now | Proposed | Effect (measured offline) |
|---|---|---|---|---|---|
| 1 | `a1_claim_supported` | add `reject_ceiling` | accept 0.85, **no reject** → 58.6% grey | reject ≤ **0.20** | grey 58.6% → **43.2%**; reject 0% → 15.4% (11,824/30d). accept band unchanged. |
| 2 | `a1_keyword_about_tour` | tighten floors | accept 0.80 / reject 0.30 → 32.2% grey | accept **0.65** / reject **0.40** | grey 32.2% → **15.7%**; reject 54% → 61%, accept 14% → 23%. |
| 3 | `a1_promise_unsupported` | set first floors | none (100% grey, tv 0) | accept **0.70** / reject **0.30**, stay **shadow** | grey 100% → **27.3%**; gives the writer-rule signal (#629) its first measurable split. |
| 4 | `a3_same_moment` | new question | does not exist | **do NOT add yet** | AA-695 measured multi-tour share already ~0.98 of groupable places; a new merge question earns little. Hold. |
| 5 | `decision_log.outcome` | close the loop | 0% fill; 2 write paths exist, unexercised | **extend paths** (see below) | makes future recalibration need no manual sample. |

### Item 1 — `a1_claim_supported` reject_ceiling (the big one)

Probability histogram (30d, non-cached, n=76,607) is strongly bimodal — a real low tail and a real
high mass:

```
p:  0.0  0.1  0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9
n: 4832 6485 5101 4212 4150 4194 4935 6818 10975 25353
```

Reject-ceiling candidates (accept stays 0.85):

| reject ≤ | grey% | reject% (n/30d) |
|---|---:|---:|
| none (now) | 58.6 | 0 |
| 0.10 | 51.2 | 7.5 (5,727) |
| 0.15 | 46.7 | 12.0 (9,164) |
| **0.20** | **43.2** | **15.4 (11,824)** |
| 0.25 | 40.2 | 18.5 (14,159) |
| 0.30 | 37.2 | 21.4 (16,418) |

**Recommendation: reject ≤ 0.20.** It is the knee of the curve (grey falls fastest up to here) and
stays conservative. BUT: S223 measured that enforcing reject at ≤ 0.30 on an India wave flagged ~10
sentences/tour → almost every tour to flag_fix, because the writer genuinely produces unsupported
promises (the upstream fix is AA-748 structured facts). **So the safe order is: approve 0.20 as the
value, but apply it only AFTER measuring precision on one wave (<$1 Jev) and confirming flag_fix
volume is acceptable — or after AA-748 lands.** Approving the number here does not auto-apply it.

### Item 2 — `a1_keyword_about_tour`

Already has a calibration record (App PR #634, accept 0.80 / reject 0.30) but has never run in
enforce (s1_prefetch has not run since the mode flip). Offline, accept 0.65 / reject 0.40 cuts grey
to 15.7% with reject at 61%. Low risk — a keyword-idea filter, not content-blocking. Apply + let the
next prefetch exercise it in enforce.

### Item 3 — `a1_promise_unsupported`

Type-B writer-rule candidate, shadow, no floors (100% grey). Histogram leans low (promises are rarer
than supported claims), so accept 0.70 / reject 0.30 splits it 9.6% / 63.1% / 27.3%. **Keep it
shadow** — it feeds the #629 writer policy as a signal, it does not block. This is the first time it
produces any split at all.

### Item 4 — `a3_same_moment`: hold

AA-695 already measured (S223) that multi-tour Segments ÷ groupable places = 0.98 — nearly every
place that *can* group already does. A new "same experience at the same place?" merge question would
pay Jev for almost no additional merge. Recommend not adding it now; revisit only if a concrete
over-fragmentation case appears.

### Item 5 — close the outcome loop

Two write paths exist today (PR #630) and are correctly wired, but fill is **0%** because they only
fire on rare human actions:
- `a1_claim_supported` ← Review Queue approve (`record_approved_outcome`, truth=True per sentence).
- `a3_atom_in_text` ← atom soft-delete / undo (`_record_atom_delete_outcome`, truth = not deleted).

Gaps to close (no code changed yet — proposal):
- **Exercise the existing paths**: the next Review Queue approvals and atom-curation edits will start
  filling outcomes for these two questions automatically. No new code — just real usage.
- **`a1_claim_supported` reject outcome**: a Review *reject* currently writes nothing. A rejected
  version's flagged sentences are candidate truth=False — a symmetric `record_rejected_outcome` would
  give the reject side ground truth (today only truth=True is ever written → precision on rejects
  can't be measured). Small, additive.
- Everything else (a3_*, a0_*, T-series) has no path. Lower priority — add per question as its
  calibration needs it, not all at once.

`GET /admin/decisions/outcomes/summary` already reads whatever gets written and computes
agree/disagree/precision per question — the read side is done.

## What needs Nghiệp's one decision

1. **Item 1** — approve `reject_ceiling = 0.20` as the value, apply-after-wave (or after AA-748). Y/N + value.
2. **Item 2** — approve accept 0.65 / reject 0.40, apply + enforce on next prefetch. Y/N + values.
3. **Item 3** — approve accept 0.70 / reject 0.30, stay shadow. Y/N + values.
4. **Item 4** — confirm hold (no `a3_same_moment`). Y/N.
5. **Item 5** — approve adding `record_rejected_outcome` (truth=False on Review reject) + rely on
   normal usage to fill the two existing paths. Y/N.

Nothing above is applied until these are answered. The paid measurement wave for Item 1 is the only
Jev spend, and it waits for the Y on Item 1.
