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

---

# Part 3 — Full A-series coverage (all 16 questions)

Part 2 covered the three loudest questions. For completeness, here is **every** A-series question
(a0_* / a1_* / a3_*) with its current state and a keep / adjust / hold verdict. Numbers are since
threshold-v2 (2026-10-10 04:09 UTC), non-cached — the current behaviour. Offline, $0.

Source: `.tmp-session/s228_all.json`.

| question | mode | kind | floors | grey% | verdict |
|---|---|---|---|---:|---|
| `a1_claim_supported` | enforce | noul | acc 0.85 | **61.0** | **adjust** — add reject ≤ 0.20 (Part 2 #1) |
| `a3_same_place` | enforce | noul | rej 0.10 | **93.7** | **adjust** — see below (new; missed in Part 2) |
| `a1_promise_unsupported` | shadow | noul | none | 100.0 | **adjust** — acc 0.70 / rej 0.30, stay shadow (Part 2 #3) |
| `a1_keyword_about_tour` | enforce | noul | acc 0.80 / rej 0.30 | — (n=0) | **adjust** — acc 0.65 / rej 0.40 (Part 2 #2); no v2 traffic yet |
| `a1_brand_fit` | shadow | noul | none | — (n=0) | **hold** — tie-break never hit the band; cannot calibrate without a sample |
| `a3_atom_in_text` | enforce | noul | rej 0.30 | 99.8 | **keep** — even rej 0.70 only reaches 3.1%; last-line guard, firing right (124 rejects/30d) |
| `a3_demand_belongs` | enforce | noul | rej 0.70 | 12.3 | **keep** — v2 already firm (reject 87.7%) |
| `a3_landing_belongs` | enforce | noul | rej 0.40 | 24.2 | **keep** — reject 75.8%, healthy |
| `a3_question_about_here` | enforce | noul | rej 0.30 | 16.7 | **keep** — reject 83.3% (n=42, low volume) |
| `a3_question_foreign` | enforce | noul | acc 0.90 | 50.0 | **watch** — 50% grey but n=42; revisit at volume |
| `a3_activity_type` | enforce | choice | acc 0.90 | 34.5 | **keep** — choice question, 65.5% confident picks |
| `a3_keyword_belongs` | enforce | noul | acc 0.85 / rej 0.45 | — (n=0) | **keep** — idle since 09-30, trims generic keywords when it runs |
| `a0_row_kind` | enforce | choice | acc 0.95 | — (n=0) | **keep** — fires on upload only; calibrated S205 |
| `a0_itinerary_usable` | enforce | noul | rej 0.20 | — (n=0) | **keep** — upload-only; calibrated S205 |
| `a0_country` | enforce | choice | acc 0.95 | — (n=0) | **keep** — upload-only; calibrated S205 |
| `a3_idea_traveller` | enforce | noul | rej 0.20 | — (n=0) | **keep** — idea filter; calibrated S205 |

(The `n=0` rows are questions whose stage simply has not run since v2 — upload gates and the
research/prefetch keyword gates. Their floors are the S204/S205 calibrated values; nothing to change
without fresh traffic.)

## New finding — `a3_same_place` is the second grey-heavy question (missed in Part 2)

`a3_same_place` (A3-7, "are these two differently-written places the same real-world place?") is
enforce at **reject ≤ 0.10** and sits at **93.7% grey** since v2. The floor was set in S205 to only
*split* confidently-different places (reject ≤ 0.10 → 30/30 correct on a 150-pair sample), never to
merge — so by design it rarely acts, and the under-merge is exactly what AA-695 flagged.

Reject-ceiling sweep (offline):

| reject ≤ | reject% |
|---|---:|
| 0.10 (now) | 6.3 |
| 0.15 | 14.3 |
| 0.20 | 25.2 |
| 0.25 | 36.6 |
| 0.30 | 43.8 |

Raising the ceiling splits (keeps apart) more borderline pairs, but **direction matters**: for
`a3_same_place` a *reject* means "NOT the same place → keep them as separate segments". Raising it to
0.20 would split 25% of borderline pairs instead of 6%, i.e. *more* fragmentation — the opposite of
AA-695's under-merge goal. So this question should **not** simply have its ceiling raised. The right
lever for merging is an *accept* floor (confident "yes, same place" → merge), which it does not have
today. That is the `a3_same_moment` / merge-side work AA-695 deferred.

**Proposed (Item 6, add to the decision set): hold the reject ceiling at 0.10** (do not raise — it
would fragment), and treat the merge side as the deferred AA-695 item. No change now; flagged so the
93.7% grey is understood, not mistaken for a calibration miss.

## Updated decision set

Part 2 items 1–5 stand. One correction and one addition from full coverage:

- **Item 6 (new):** `a3_same_place` — **keep reject ≤ 0.10 as-is** (raising it fragments, against
  AA-695). Y/N to confirm hold.
- **`a1_brand_fit`:** confirmed **hold** (shadow, no volume to calibrate) — folds into the existing
  Item 4 "hold" posture.

No other A-series question needs a change: the enforcing a3 gates (`demand_belongs`,
`landing_belongs`, `question_about_here`, `activity_type`) calibrated cleanly at v2 and are firing
well; the a0 and research gates have no new traffic to recalibrate against.

---

# Part 4 — End-to-end downstream analysis (what the gates actually did to the data)

Parts 1–3 looked at Jev's own probabilities. This part reads the **real downstream tables** the
gates feed — atoms → segments → `atom_ranking` (the Score) → routes → hubs — to judge calibration by
its effect on the product, not just the probability curve. Read-only, no DB change. Snapshot:
`.tmp-session/s228_down.json` + `s3://aa-cis-bronze-005097885195/scripts/s228_down.json`.

## On "score": there is no Jev `kind=score`

Jev questions have three kinds, but across all 25 questions only **choice** (3) and **noul** (22)
exist — **no `kind=score`**. The 0–10 scoring in the pipeline is `s1_judge`, which is a plain LLM
judge, not a Jev `decide()` question, so it is not in `decision_question` and not part of this audit.
The "Score" that the A3 gates feed is `acp_contract.atom_ranking` (demand/questions/said ranks), a
computed table — not a Jev score question. So nothing was missed: there is no score-kind to analyse.

## The pipeline funnel (platform, live)

```
892 active tours
  → 24,302 live atoms            (+ 8,033 deleted/soft-deleted)
  → 11,306 segments              (25,158 members, 163 merge aliases)
  → 108,198 ranking rows         ← this is the Score table
       82,446 ranked
       21,774 excluded 'transit'       ← a3_activity_type's work
        3,978 excluded 'unnamed_place'
  → 1,331 routes → 419 hubs
```

Each Jev A3 gate maps to a visible effect here:

### `a3_activity_type` (choice) — biggest downstream footprint
It decides transit-vs-experience. In the Score table, **21,774 of 108,198 ranking rows (20%) are
excluded as `transit`** and 3,978 as `unnamed_place`. That is exactly the gate doing its job: a fifth
of all moments are logistics kept out of ranking. The live atom mix confirms it — `transit` is the
2nd-largest activity_type (4,897 atoms) and all of it is held out of Score. **Verdict: keep** — this
is the gate with the clearest, largest real effect, and 65% confident picks is healthy.

### `a3_demand_belongs` + `a3_landing_belongs` — shape the Score axes
Of 82,446 ranked rows: **6,393 carry demand (search volume), 11,076 carry questions (PAA)**, every
row carries `said` (recurrence). avg questions/row = 0.57, avg demand = 2,905. These two gates are
the reason demand and questions are *sparse and selective* rather than attached to everything — they
reject keyword/PAA claims that don't belong to the moment. The low attach rate is the gate working
(most moments legitimately have no bought demand), not a miss. **Verdict: keep** (already firm at v2).

### `a3_atom_in_text` — the drop gate, confirmed working
24,302 atoms survived; 8,033 are deleted. This gate rejects off-day/logistics atoms before they are
stored (124 enforce-rejects/30d, Part 1). Its 99.8% grey is fine precisely because the upstream
prompt already keeps atoms on-day — the gate only has to catch the rare leak. **Verdict: keep.**

### `a3_same_place` — the fragmentation lever (confirms Part 3)
Real segments 10,327: **8,275 single-tour (80.1%)**, 2,052 multi-tour, 163 merge aliases. The 80%
single-tour share is the under-merge AA-695 flagged. As Part 3 argued, this gate's *reject* only
splits — raising its ceiling makes 80% worse. The merge side needs an accept floor it does not have
(= deferred `a3_same_moment`). **Verdict: hold reject 0.10; merge is AA-695 work, not a floor tweak.**

## The two shadow questions — read against their real data + their actual wording

I pulled each question's instructions to get the **direction of p right** (this corrects a risk in
Part 2):

### `a1_promise_unsupported` — p HIGH = BAD (promise the source doesn't make)
Wording: *"Does this sentence promise the traveller something about THIS tour that the source does
not state?"* So **true (p→1) = an unsupported promise = the thing we want to catch**; p→0 = clean.

30-day distribution (n=13,421, non-cached): **avg p 0.296, 63% ≤ 0.30, only 9.6% ≥ 0.70.** Most
rewritten sentences make no unsupported promise — good news about the writer.

**Correction to Part 2:** because true=bad here, the useful enforcing floor is an **accept_floor**
(confident "yes, this is an unsupported promise" → act), NOT a reject_ceiling. My Part 2 line "acc
0.70 / rej 0.30" had the reject side backwards in meaning. The right setup for a *shadow signal to a
writer rule* is: **accept_floor ≈ 0.70** to mark the ~9.6% confident unsupported promises; keep it
shadow (it informs the #629 writer policy, it should not block). A reject_ceiling (confident "not a
promise") carries no action — the writer rule only cares about the positive catches.

### `a1_brand_fit` — genuinely no data, correctly held
Wording: *"Does this tour copy fit this brand?"* Asked only when `s1_judge` lands within ±0.5 of 7.0.
In 30 days there were **0 judge runs with a score in that band** (and only **3 `a1_brand_fit`
decisions ever**, all historical). The tie-break simply never triggers on current data. **There is
nothing to calibrate** — any floor would be guessing from 3 points. **Verdict: keep shadow, revisit
only if judge-score-in-band volume appears.** This is not a gap; it is a rare-by-design tie-break.

## Net calibration judgement (grounded in downstream effect)

| Gate | Downstream effect seen | Calibrate? |
|---|---|---|
| `a3_activity_type` | 20% of ranking rows excluded as transit | no — working, largest effect |
| `a3_demand_belongs` / `a3_landing_belongs` | selective demand/question attach | no — firm at v2 |
| `a3_atom_in_text` | 8k atoms dropped; rare leak-catcher | no — keep guard |
| `a3_same_place` | 80% single-tour segments (under-merge) | not via floor — merge = AA-695 |
| `a1_claim_supported` | 61% grey, biggest cost, accept-only | **yes** — add reject_ceiling (Part 2 #1), apply-after-wave |
| `a1_keyword_about_tour` | keyword filter, no v2 traffic | yes — floors ready (Part 2 #2) |
| `a1_promise_unsupported` | shadow signal, p-high=bad | **yes but** accept_floor ≈ 0.70 (corrected), stay shadow |
| `a1_brand_fit` | tie-break never fires (0 in band) | no — hold, no data |
| a0_* / a3_idea_traveller / a3_keyword_belongs | upload/research gates, no v2 traffic | no — floors stand |

**Bottom line:** only **one** gate genuinely needs a threshold change for grey/cost
(`a1_claim_supported`), one has floors ready to apply (`a1_keyword_about_tour`), one shadow signal
should get a corrected accept_floor (`a1_promise_unsupported`). Everything else is either working as
measured on real downstream data, or has no traffic to calibrate against. The system is in better
shape than the blended 30-day grey numbers first suggested — most "high grey" is either a rare-leak
guard or a selective filter doing its job.

---

# Part 5 — Data quality judged by eye (my own read of real DB content + Jev)

Nghiệp's ask: don't just count — read the real master/atom/segment/route/hub content and judge
quality, my own view, cross-referenced with Jev. Read-only, $0. Samples:
`.tmp-session/s228_q.json`, `s228_hub.json` + the same files on S3 `scripts/`.

## Atom layer — GOOD

30 random live atoms read cleanly. Every one is a genuine place+activity pair, verbatim-ish, with a
sensible `activity_type`:
- `[culture] Yangshuo — take a morning Tai Chi class with a local master`
- `[trek] Yala National Park — participate in early morning game drive`
- `[transit] Beijing railway station to Xi'an — travel by overnight sleeper train` (A→B written as one place, correct)
- `[food] Elephant Crossing Hotel rooftop bar — have a drink overlooking the valley`

Red-flag scan over all 24,302 live atoms: `long_place` 68 (0.3%), `vague_place` ("the trail/village")
21 (0.1%), `empty_action` 0, `no_evidence` 0, `lodging_like` 1,342 (5.5%). The lodging-like share is
the only soft spot (hotel/check-in atoms still stored) but those are correctly typed `stay`/`transit`
and held out of Score, so they don't pollute ranking. **My verdict: atom extraction quality is high.**
This is the AA-694 A3-1 prompt + `a3_atom_in_text` gate working.

## Segment layer — GOOD at the top, UNDER-MERGED in the tail (known AA-695)

The top multi-tour segments are exactly right — real shared hubs the catalog revolves around:
Dal Lake (367 tours), Taj Mahal (105), Hawa Mahal (68), Amber fort (65), Jama Masjid (56). These are
genuine cross-tour places; the merging worked.

But the under-merge is visible and real. The same place sits in many separate segments because the
segment key is place + free-text action:
- **delhi** → 37 segments, **jaipur** → 32, **udaipur** → 29, **kathmandu** → 29, **taj mahal** → 25.
- The actions that fragment them are mostly logistics phrased differently: "arrive" / "check in" /
  "airport transfer to hotel" / "attend pre-departure briefing" — each spawns its own segment.

Also note two **logistics segments leaked into the top-20 as if they were attractions**: "hotel —
check in" (130 tours) and "airport — meet and transfer" (110 tours). Those should not be
cross-tour ranked places. `a3_activity_type` excludes them from *Score*, but they still *form
segments* — a cosmetic/graph-noise issue, not a ranking one. **My verdict: segment quality is good
for real attractions, but ~80% single-tour share + logistics-as-segment is genuine debt — exactly
AA-695's merge-side work (accept-floor same-place / same-moment), not a threshold tweak.**

## Route layer — GOOD

1,331 live routes, avg 9.6 segments/route (min 2, max 31), **0 tiny (≤1) routes**, avg day span 4.0.
Reads healthy: a route is an ordered run of real segments within a tour. No degenerate single-segment
routes. **My verdict: route construction is sound.**

## Hub layer — BUG (real finding, worth an issue)

This is the one place the data is clearly wrong:
- 419 hubs exist, but **only 14 distinct hub_ids are actually linked by live routes**, and
  **405 hubs are orphans** (no live route points at them).
- Of 1,331 routes, 945 carry a hub_id but they collapse onto **14 hub_ids** — and **one hub_id holds
  862 routes** (`Lingshi basin → Doupchu La Pass → …`, a Bhutan trek name). 386 routes have no
  hub_id at all.
- Meanwhile `hub_name` is distinct on 400 values. So **hub_name and hub_id are out of sync**: routes
  are being pinned to a tiny set of hub_ids (one dominating) while 405 freshly-named hubs sit unused.

That 862-on-one-hub_id pattern is not a real geography — it looks like a hub-assignment/dedup bug
(routes attaching to a stale or wrongly-reused hub_id row during recompute). Jev is not involved here
(hubs are deterministic), so this is a pipeline bug independent of calibration. **My verdict: hub
assignment is broken and should be a separate bug issue** (propose: investigate route→hub_id linkage
in the recompute; the 419 vs 14 vs 862 split is the smoking gun). I did not change anything.

## Tour master layer — THIN TAIL

892 active tours, avg 27.2 atoms, median 25, max 86. But the low tail is heavy:
**60 tours have ≤5 atoms, 191 have ≤10** (≈21% of the catalog). A 5-atom tour produces almost no
Segment/Score/Route signal — these are the "thin itinerary" cases `a0_itinerary_usable` is meant to
flag at ingest, but they predate the gate or came in another way. **My verdict: ~20% thin tours is
real quality debt at the source**, not a Jev calibration problem — it is an upstream data-coverage
issue (the source itineraries themselves are sparse). Known limitation per the TripPlanner tech
rules (atom count per tour-day varies 1–8; some days have zero atoms).

## Answering "why no `kind=score` question per A-series stage?"

Now that the data is read, the answer is concrete. A `score`-kind Jev question would return a 0–10
quality number per unit. The A-series stages don't use one because:
1. **The scoring that exists is `s1_judge`** (0–10 on the whole rewritten tour) — already an LLM
   judge, and the A1-4 tie-break (`a1_brand_fit`) already defers to Jev only in the ±0.5 band. Adding
   a Jev score-question would duplicate it.
2. **The A3 decisions are naturally binary or categorical, not graded**: "is this atom in the day's
   text?" (yes/no), "transit or experience?" (choice), "does this keyword belong?" (yes/no). A score
   adds no leverage — you still need a cut to act, i.e. a floor, which is what the noul/choice floors
   already are.
3. **Where a graded signal WOULD help**: segment-merge confidence and atom "distinctiveness"/richness.
   But distinctiveness scoring was removed end-to-end (AA-754), and merge confidence is better served
   by the deferred `a3_same_moment` accept-floor than by a free-floating 0–10.

So the absence of a score-kind is defensible, **except** possibly one place: a per-tour or per-day
**"itinerary richness" score** could formalise the thin-tour problem (Part 5 tour layer) into a
gradeable signal instead of the single `a0_itinerary_usable` yes/no. That is a genuine design idea
worth a ticket — not a calibration change. Flagged, not built.

## My overall quality verdict

| Layer | Quality | Jev's role | Action |
|---|---|---|---|
| Atom | **High** | A3-1 gate + prompt keep atoms on-day, verbatim | none |
| Segment | **Good top / under-merged tail** | same-place reject splits; merge side missing | AA-695 (merge accept-floor) |
| Route | **Sound** | n/a (deterministic) | none |
| Hub | **Broken** (405/419 orphan, 862-on-one) | n/a (deterministic) | **new bug issue** |
| Tour master | **~20% thin** | a0_itinerary_usable flags at ingest | upstream data; maybe a richness-score ticket |

Jev is doing its job well where it is wired (atoms, Score exclusions, demand/question selectivity).
The two real quality problems — the hub bug and the thin-tour tail — are **not** Jev calibration
issues; they are a deterministic pipeline bug and an upstream data-coverage gap respectively.
Calibration (Parts 1–4) remains a small, well-scoped change; the bigger quality wins are the hub bug
and segment merge.

---

# Part 6 — a1_claim_supported threshold over the FULL grey set + the outcome-nhãn dead end

Nghiệp's direction: no small sample (sampling error on a 44,919-row grey zone is real); compute the
threshold offline over the **whole** distribution, and build the outcome loop as the ground-truth
base first. Both done below. Read-only, $0.

## Full probability distribution (76,607 non-cached calls, 0.05 bins)

```
0.00-0.05   787      0.50-0.55  2024
0.05-0.10  4045      0.55-0.60  2628
0.10-0.15  4332      0.60-0.65  2377
0.15-0.20  2153      0.65-0.70  3187
0.20-0.25  2383      0.70-0.75  3268
0.25-0.30  2270      0.75-0.80  3691
0.30-0.35  2100      0.80-0.85  5722
0.35-0.40  1664      0.85-0.90  7001
0.40-0.45  2078      0.90-0.95 15087   ← high mass (confident supported)
0.45-0.50  2072      0.95-1.00 10266
```

The shape: a **high mass** at p ≥ 0.85 (32,354 calls, 42%, accepted today), a **steep low tail**
through p ≤ 0.15 (9,164 calls — the 0.05-0.10 and 0.10-0.15 bins are the two densest in the lower
half), and a **flat ambiguous middle** 0.15–0.85 (~2,000–2,300 per bin). The knee is at **~0.15**:
below it the bins are tall (real low tail), above it the curve goes flat (genuine uncertainty).

## Reject-ceiling sweep over the WHOLE set (accept stays 0.85)

| reject ≤ | reject % (n) | grey left |
|---|---:|---:|
| 0.10 | 7.5% (5,727) | 51.2% |
| **0.15** | **12.0% (9,164)** | **46.7%** |
| 0.20 | 15.4% (11,824) | 43.2% |
| 0.30 | 21.4% (16,418) | 37.2% |

**Revised proposal from the full distribution: reject ≤ 0.15** (not the 0.20 guessed in Part 2).
0.15 catches the steep low tail and stops at the knee, before the flat ambiguous band — so it
rejects what the model is genuinely confident is unsupported, and leaves the real "not sure" cases
grey. 0.20+ starts eating into the flat middle (higher false-reject risk per extra point).

## The blocker: there is NO trustworthy sentence-level ground truth to measure precision

The sweep says *how many* calls reject at each ceiling. It cannot say whether those rejects are
*right* (precision) without labelled truth. Investigating every candidate source, each one fails:

- **Review-Queue approve** (the one wired truth=True path): `approved_versions = 0`. Per Nghiệp,
  reviewers don't approve — they hit Regenerate to make a new version. So this path will stay empty
  by workflow design. It cannot be the base.
- **Review-Queue reject**: a reject is a whole-version quality judgement (off-brand, generic), NOT a
  per-sentence "this claim is unsupported". Writing truth=False per sentence would mislabel en masse.
  Not usable.
- **Soft-deleted atoms** (`a3_atom_in_text`, 8,033 rows): these are deleted by tour lifecycle
  (deactivate / trash / regenerate → recompute re-atomizes), NOT by a human saying "not in the day's
  text". `admin_atom_delete` outcomes written to date = **0** (the Atom-Curation delete hook has
  never been used). So the 8,033 carry no usable label either — backfilling truth=False from them
  would mislabel just like the reject path.
- **flag_fix**: repairs by FIELD (subtitle/summary/itineraries) for mixed reasons (SEO length, brand,
  forbidden words), not per sentence for "unsupported". No sentence-level label.

**Conclusion (honest):** the real blocker for `a1_claim_supported` calibration is not the threshold
number — the full distribution clearly supports reject ≤ 0.15 — it is that **no sentence-level
ground-truth signal exists in the current workflow**. Applying reject ≤ 0.15 blind would reject
9,164 sentences into flag_fix with unmeasured precision. That is exactly the sampling/mislabel risk
Nghiệp flagged, one layer up.

## What this means for the plan

1. The threshold is **ready as a number** (reject ≤ 0.15, from the whole set) but **should not be
   applied** until precision can be measured. It is not a guess anymore; it is un-verifiable yet.
2. The outcome loop cannot be bootstrapped from existing data — every candidate source mislabels.
   A real ground-truth source would need a deliberate workflow signal, e.g. a reviewer action that
   marks a specific sentence as unsupported, or a one-off human-labelled set built on purpose (not
   derived from lifecycle events). That is a product/workflow decision, not a backfill script.
3. So `a1_claim_supported` calibration is **correctly blocked** pending a ground-truth source. The
   audit's value here is proving that — and proving the threshold is 0.15 the moment a label source
   exists.

**Items 2 (`a1_keyword_about_tour`) and 3 (`a1_promise_unsupported`) are unaffected** — they are
shadow / low-risk and their floors can be set from the distribution without the same precision bar,
whenever Nghiệp wants. Only the enforcing, content-blocking `a1_claim_supported` needs the label
first.

---

# Part 7 — Jev audit/calibration PARKED; hub bug status (S228 close)

## Why Jev calibration is parked (Nghiệp's call, and it is right)

A reject/accept threshold is meaningless on its own. What matters is **what the system DOES at that
threshold** — and that differs per question:

- `a3_atom_in_text` reject → the atom is **not stored** (vanishes from Segment / Score / Route).
- `a3_demand_belongs` / `a3_landing_belongs` reject → a keyword's demand / a PAA question **drops
  off the Score axis** for that moment.
- `a3_same_place` reject → two places are **kept as separate Segments** (more fragmentation).
- `a1_claim_supported` reject → the sentence is flagged **UNSUPPORTED → flag_fix rewrites it**.

Tuning a threshold to "reduce grey %" without modelling that downstream action is optimising a
number with no business meaning. Doing it right means, per question: map the exact pipeline reaction
at accept / grey / reject, then decide the threshold against the product outcome (an atom lost, a
rank changed, a rewrite triggered) — AND against a trustworthy ground-truth label, which Part 6
showed does not exist in the current workflow for the content-blocking questions.

**Decision (S228):** park the Jev effectiveness-audit + recalibration work. Not because the numbers
are wrong (they are measured and correct for their window — see the reconciliation note below) but
because the missing pieces are (1) a per-question downstream-action model and (2) a real
ground-truth source. Both are design work, not a threshold tweak. Tracked under AA-756, which stays
In Progress with this as its explicit blocker.

## Data-source note (reconciliation with the admin UI)

All DB numbers in Parts 1–6 come from `shared.decision_log`, mostly a 30-day window, `NOT cached`.
The admin **Jev Decisions** page shows **Last 7 days** and **includes cache hits**, which since
AA-742 are NOT rows in `decision_log` — they are counted in `shared.decision_cache_hits_daily` and
added back by the summary endpoint. So the UI's larger VERDICTS/CACHED numbers and the per-30-day
numbers here are both correct, just different cuts. Verified they reconcile exactly, e.g.
`a1_claim_supported` 7-day UI = 130,992 verdicts / 64,136 cached / 46,224 accept / 84,025 grey /
**0 reject** (the 743 in the UI is the **ERROR** column, not reject — `a1_claim_supported` has no
reject_ceiling, so it cannot produce a reject). For calibration the right population is the
`NOT cached` originals (one verdict per subject, not inflated by cache re-reads), so Parts 1–6's
distribution stands.

## Hub bug (AA-758) — the one thing that shipped this session

- **Root cause: `min()` denominator in BOTH `best_hub_match()` (hub reuse) AND `families()` (family
  forming).** On the full catalog, a single shared segment scored 1.0 and union-find chained
  unrelated tours into one 455-tour family → one hub → one journey name on 862 of 1,331 routes;
  405 orphan hubs.
- **Fix: Jaccard over the union at both layers**, with regression tests.
  - PR #653 (hub reuse) — merged + deployed (api:526/worker:81, SHA 9155b12). A platform recompute
    on Dev (job ef24cbca, $0, 232s) still showed 862-on-one → proved the collapse is in `families()`.
  - PR #654 (family forming) — the real fix; auto-merge.
- **VERIFIED (after #654 deploy, api:527 SHA 773d591):** platform recompute job 7f747ea5 ($0, 227s)
  broke the collapse:

  | metric | before | after #653 | after #654 |
  |---|---:|---:|---:|
  | largest hub (routes) | 862 | 862 | **84** |
  | max tours in one hub | 455 | 455 | **55** |
  | hubs linked by live routes | 14 | 22 | 21 |

  The largest remaining hub (84 routes / 55 tours) is now a REAL journey — "Jama Masjid → India
  Gate → Lakshmi Narayan Temple → Shanti Vana" (Delhi), which 55 India tours genuinely pass through
  — not the old 455-tour Bhutan-trek-name collapse. Fix confirmed correct at the root.
- **Left as cleanup (not a bug):** orphan hubs rose 405 → 425 (the old collapsed hubs are now
  unreferenced). Orphan hubs are "expected, not cleaned" (migration 131); a one-off prune of
  unreferenced hub rows is a tidy-up, tracked on AA-758, no urgency.
