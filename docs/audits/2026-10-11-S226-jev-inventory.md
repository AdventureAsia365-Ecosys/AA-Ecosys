# Jev effectiveness audit — inventory (S226, 2026-10-11)

Part of AA-756. This is the **$0 inventory pass** Nghiệp approved: read-only `decision_log` over the
last 30 days, hand-review of the dominant question, and the `a1_promise_unsupported` numbers. No
recalibration, no new LLM/Jev calls, no threshold change (those wait for Nghiệp's approval per the
issue scope). Source data: `.tmp-session/s226_jev_audit.json` (live dump via ECS exec).

## Headline

- **274,961 decisions / 30 days across 23 questions**, total Jev cost **$9.68**.
- **Every question is in `shadow` mode** — including `a1_claim_supported`. Nothing is enforcing
  today: no Jev verdict blocks the pipeline right now. (The issue was written in S223 when
  `a1_claim_supported`/`a3_*` were `enforce`; they have since moved to shadow — the single most
  important thing this inventory surfaces, worth confirming it's intended before recalibrating.)
- **`decision_log.outcome` fill is 0.0%** across all 23 questions — still no stored ground truth to
  recalibrate against (part 5 of the issue remains fully open).
- Cost is dominated by one question: **`a1_claim_supported` = $6.94 of $9.68 (72%)**, 87,766
  decisions, 56.8% grey. Matches the S223 finding that this one question is ~¾ of Jev spend.

## Per-question inventory (30 days)

| question_key | mode | n | acc% | grey% | rej% | cost $ | tv | outcome |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| a1_claim_supported | shadow | 87,766 | 29.8 | 56.8 | 0.0 | 6.9449 | 2 | 0 |
| a3_demand_belongs | shadow | 48,125 | 0.0 | 20.2 | 37.7 | 0.4578 | 2 | 0 |
| a3_activity_type | shadow | 32,436 | 19.5 | 26.2 | 0.0 | 0.2849 | 2 | 0 |
| a3_atom_in_text | shadow | 29,889 | 0.0 | 95.7 | 0.4 | 0.5950 | 1 | 0 |
| a3_landing_belongs | shadow | 23,859 | 0.0 | 31.2 | 63.9 | 0.3727 | 2 | 0 |
| a1_keyword_about_tour | shadow | 18,086 | 0.0 | 94.5 | 0.0 | 0.2999 | 0 | 0 |
| a1_promise_unsupported | shadow | 12,833 | 0.0 | 100.0 | 0.0 | 0.4241 | 0 | 0 |
| a3_same_place | shadow | 6,749 | 0.0 | 76.2 | 17.6 | 0.1028 | 1 | 0 |
| a3_question_about_here | shadow | 5,037 | 0.0 | 46.4 | 48.8 | 0.0499 | 2 | 0 |
| a3_question_foreign | shadow | 5,037 | 36.6 | 58.6 | 0.0 | 0.0499 | 2 | 0 |
| a0_itinerary_usable | shadow | 1,610 | 0.0 | 100.0 | 0.0 | 0.0318 | 1 | 0 |
| a0_row_kind | shadow | 1,610 | 28.3 | 71.7 | 0.0 | 0.0318 | 1 | 0 |
| a0_country | shadow | 1,055 | 0.0 | 100.0 | 0.0 | 0.0193 | 0 | 0 |
| a3_idea_traveller | shadow | 396 | 0.0 | 46.0 | 54.0 | 0.0066 | 1 | 0 |
| a3_keyword_belongs | shadow | 257 | 2.7 | 96.5 | 0.8 | 0.0039 | 1 | 0 |
| a3_idea_traveller_v2 | shadow | 182 | 0.0 | 100.0 | 0.0 | 0.0034 | 0 | 0 |
| t10_rubric_met | shadow | 12 | 0.0 | 100.0 | 0.0 | 0.0004 | 0 | 0 |
| t9_fact_relevant | shadow | 6 | 0.0 | 33.3 | 0.0 | 0.0000 | 0 | 0 |
| t8_angle_answers | shadow | 4 | 0.0 | 100.0 | 0.0 | 0.0001 | 0 | 0 |
| t10_brand_voice | shadow | 3 | 0.0 | 100.0 | 0.0 | 0.0002 | 0 | 0 |
| t10_cta_clear | shadow | 3 | 0.0 | 100.0 | 0.0 | 0.0001 | 0 | 0 |
| a1_brand_fit | shadow | 3 | 0.0 | 100.0 | 0.0 | 0.0001 | 0 | 0 |
| t7_topic_fits_brand | shadow | 3 | 0.0 | 100.0 | 0.0 | 0.0001 | 0 | 0 |

## Hand-review — `a1_claim_supported`, last 30 decisions

Zone split in the sample: **20 accept / 10 grey / 0 reject** (`threshold_version = 2`).
Accepts cluster at high probability (p 0.91–0.98); greys are the mid/low band (p 0.15–0.60).
Spot-reading the probabilities, the accept band (≥ ~0.90) and the grey band look internally
consistent — a high-p claim reads as genuinely supported, a low-p one as genuinely unverifiable.
No reject appears because the question has no reject ceiling in tv2 (it only clears novel numbers at
accept ≥ 0.90), consistent with S223. This is a sanity read, not labelled ground truth.

## `a1_promise_unsupported` (type-B writer rule candidate)

12,833 decisions in 30 days, **100% grey, 0 accept, 0 reject** (`tv 0`, shadow). The question runs
but its thresholds never classify anything out of the grey zone — so it currently produces no signal
to drive a writer rule either way. Any decision to enforce a type-B ("promises an activity/service
the source doesn't support") rule needs the thresholds set first, then a labelled sample; it cannot
be read off the current all-grey distribution.

## What this inventory does NOT do (deferred, needs Nghiệp)

- **No recalibration / threshold change** — scope §3 requires Nghiệp approval, applied on Dev only.
- **No human-labelled sample** (§2) — ~100/question is Nghiệp's call to label.
- **No `decision_log.outcome` backfill** (§5) — needs the LLM-fallback/human-review linkage designed.
- **The enforce → shadow question**: confirm with Nghiệp whether all 23 going shadow is intended
  before any recalibration — recalibrating thresholds on a question that no longer blocks is moot.

## Recommended next step (a dedicated AA-756 session)

1. Confirm the enforce/shadow intent (above).
2. Pick the 2–3 questions worth keeping enforce (candidates by cost/volume: `a1_claim_supported`;
   by reject usefulness: `a3_landing_belongs`, `a3_demand_belongs`).
3. Retire the near-dead ones (consistently ~100% grey, no downstream effect): `a3_atom_in_text`
   (95.7% grey), `a1_keyword_about_tour` (94.5%), `a3_keyword_belongs` (96.5%), the T-series
   shadows with single-digit volume.
4. Then label + recalibrate + measure on a wave (the paid part, ~<$1 Jev).

---

## Correction (S227, 2026-10-11) — "every question is shadow" was WRONG

The S226 headline above ("Every question is in `shadow` mode — nothing is enforcing today") is a
mis-read and is **retracted**. Re-checked against the source-of-truth config table
`shared.decision_question` (25 rows — the schema-ref "~5 rows" estimate was stale) **and** the
actual run mode in `shared.decision_log.mode` over 30 days, cross-referenced with the live admin UI
(confirmed by Nghiệp). Findings:

- **14 A-series questions are `enforce` and genuinely blocking today**, run mode confirmed in
  `decision_log` right up to 2026-10-11: `a1_claim_supported` (87,883 enforce decisions/30d),
  `a3_demand_belongs` (47,967), `a3_landing_belongs` (23,734), `a3_activity_type` (31,237),
  `a3_atom_in_text` (29,657), `a3_question_about_here` / `a3_question_foreign` (4,443 each),
  `a3_same_place` (5,745), plus `a0_*` / `a3_idea_traveller`. Set by `admin:nghiep (S205)` and
  `admin:claude-code-s223-aa756` (2026-10-10 04:05) — intentional.
- **3 questions are `enforce` in config but showed only `shadow` in `decision_log` over 30 days**
  (threshold never fired / very low volume): `a0_country`, `a1_keyword_about_tour`,
  `a3_keyword_belongs`. Worth a separate look, not "dead".
- **11 T-series + brand questions are `shadow` with `tv=0`, created that way by migrations**
  (`migration-19x/211`), never calibrated, single-digit volume. **This is correct** — the T-series
  has not been audited yet, so it is expected to be non-active (Nghiệp, S227). Not a defect.

### So the real AA-756 problem is NOT "turn enforcing back on"
The 14 A-series gates already enforce. The real problem is **too much grey** on the enforcing
questions → the thresholds need calibration so decisions land in accept/reject instead of grey. Grey
rate from the S226 inventory on the live enforcing questions, e.g. `a1_claim_supported` 56.8% grey
(and 72% of total Jev cost), `a3_demand_belongs` 20.2% grey, `a3_landing_belongs` 31.2% grey.

### Corrected next step (dedicated AA-756 session, needs Nghiệp + paid LLM)
1. Keep the 14 A-series enforcing (no change needed — they already work).
2. **Audit + calibrate the high-grey enforcing questions** (priority by cost/grey:
   `a1_claim_supported` first) — hand-label ~100/question, set `accept_floor` / `reject_ceiling` so
   grey shrinks, measure on a wave (~<$1 Jev).
3. Leave the T-series shadow until its own audit (not part of this calibration).
4. `decision_log.outcome` backfill (§5) still open.
