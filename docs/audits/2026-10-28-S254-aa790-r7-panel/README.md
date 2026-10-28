---
id: PROD-01-aa790-r7-panel
title: "AA-790 round 7 blind panel (S254)"
description: "Blind 9-arm agent panel scoring the round-7 T9 brand-voice prompt against round 6, a same-night r6b control and earlier rounds; round 7 failed the ship bars and was reverted."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [aa-cis]
last_reviewed: 2026-10-28
review_every_days: 180
related: [AA-790]
---

# AA-790 round 7 — blind 9-arm panel (S254)

Arms: pilot (before), r1–r6, **r6b** (control: round-6 prompt re-run the same night) and **r7** (round-7 prompt), 20 T9
pieces each (4 demo tenants, blog + LinkedIn), scored blind on 4 lenses by an agent panel (S251 rubric), all arms in
one run. 719 / 720 scores (one missing score does not change any bar).

| lens | r3 | r6 | r6b (control) | r7 |
|---|---|---|---|---|
| ai_tells | 4.88 | 5.65 | 5.72 | 5.75 |
| brand_voice | 7.28 | 6.67 | 6.75 | 6.60 |
| source_fidelity | 7.53 | 7.55 | 7.72 | 7.70 |
| reader_value | 7.10 | 7.22 | 7.15 | 6.95 |

Noise |r6b − r6|: 0.07–0.17 per lens. Full tables (per tenant, per channel, W/T/L) in `aggregate.txt`.

## Bars (set before the run)

- PASS ai_tells ≥ 5.5; PASS source fidelity non-regression.
- FAIL brand_voice ≥ 7 overall and for 3 of 4 tenants (Atlas & Hearth passes); FAIL brand_voice r7 ≥ r3; FAIL
  brand_voice r7 − r6b > noise; FAIL reader_value non-regression.

**Decision: round 7 reverted** (CIS #1087), round 6 stays live. AA-790 Done-when brand bars not met.

## Cost

Paid writer runs (stage `adhoc_aa790`, `shared.llm_call_log`): r6b $0.894 + r7 $0.906 = $1.80 (cap $2.00). The agent
panel has no AWS cost.

## Next

The round-7 diagnosis holds (angle brief copied as wording; style-guide points never mapped to seed facts), but a
generic BRAND FOCUS block in the T9 prompt did not lift brand voice and cost reader value. Next round: fix the T8 angle
generator (briefs the seed cannot support) rather than the T9 prompt.
