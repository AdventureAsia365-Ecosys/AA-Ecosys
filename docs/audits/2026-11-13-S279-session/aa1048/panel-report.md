# AA-1048: blind panel re-judge of the 215 unsupported-claim false positives
Session S279, 13/11/2026. Synthesis step. Cost $0: no LLM API calls and no DB or API writes. Inputs: the merged 3-lens panel verdicts, `labels.json` and `batch-00..17.json` in `.tmp-session/S279/aa1048/panel/`.

## Question
R1 tested gpt-6-luna in extraction mode on held-out labelled claims: precision 0.22–0.27, recall about 0.9. It fired on 215 claims whose stored label is `ok` (t2 123, t9_blog 92).
- H1 (label noise): the stored `ok` labels miss real unsupported claims.
- H2 (the instrument over-fires): it flags permitted background, paraphrase or inference, over-split fragments, or support it did not see.

A blind 3-lens panel (source, policy, skeptic) re-judged the claims without seeing the stored labels.

## 1. Counts
Overall:
- ok 205 (95.3%): 173 judged supported by a majority, 32 judged permitted background by a majority; 192 were ok on all three lenses.
- violation 7 (3.3%).
- split 3 (1.4%).

| Writer | n | ok | violation | split |
|---|---|---|---|---|
| t2 | 123 | 116 | 5 | 2 |
| t9_blog | 92 | 89 | 2 | 1 |

| Stored decider | n | ok | violation | split |
|---|---|---|---|---|
| panel_agreed | 70 | 68 | 0 | 2 |
| tech_lead, total | 145 | 137 | 7 | 1 |
| tech_lead: accepted S276 t2 panel proposal | 87 | 81 | 5 | 1 |
| tech_lead: `queue: judge_right` | 48 | 48 | 0 | 0 |
| tech_lead: S275 review page with a written reason | 10 | 8 | 2 | 0 |

| claim_class | n | ok | violation | split |
|---|---|---|---|---|
| fact.inclusion | 75 | 72 | 3 | 0 |
| fact.embellish | 41 | 39 | 1 | 1 |
| other.f7 | 16 | 16 | 0 | 0 |
| fact.number | 15 | 14 | 0 | 1 |
| scope.persona_promise | 15 | 12 | 2 | 1 |
| struct.day_structure | 15 | 15 | 0 | 0 |
| fact.name | 10 | 10 | 0 | 0 |
| scope.framing | 10 | 9 | 1 | 0 |
| fact.direction | 8 | 8 | 0 | 0 |
| fact.misbinding | 5 | 5 | 0 | 0 |
| other.f6 | 4 | 4 | 0 | 0 |
| scope.faq_question_offtopic | 1 | 1 | 0 | 0 |

By field: 4 of the 7 violations are in t2 itineraries (57 claims).

## 2. Why the instrument fired on the 205 panel-ok claims
The table uses the most common lens reason for each claim; all three lenses gave the same reason for 153 claims.

| Reason | Claims | Share | t2 | t9_blog |
|---|---|---|---|---|
| paraphrase_or_inference | 135 | 65.9% | 77 | 58 |
| none (verbatim or near-verbatim support) | 30 | 14.6% | 10 | 20 |
| background_knowledge | 29 | 14.1% | 25 | 4 |
| other | 4 | 2.0% | 2 | 2 |
| support_outside_evidence | 2 | 1.0% | 0 | 2 |
| over_split | 2 | 1.0% | 0 | 2 |
| tie | 3 | 1.5% | 2 | 1 |

Across all 615 lens votes: paraphrase 389, none 105, background 86, other 14, over-split 11, real unsupported 5, support outside evidence 5.

- **Paraphrase and inference.** Examples:
  - "from Kathmandu" inferred from "drive back to Kathmandu";
  - "summit" for a hike to the peak;
  - 9 nights stated as 10 days;
  - the direction of Agra from Delhi;
  - tone words.

  The instrument seems to require a lexical match for each extracted fragment.
- **Verbatim misses (30 claims).** These are instrument errors, not policy questions.
  - Itinerary restatements: df93171d2f60, e641a564908e, d017cf7bd20c, 85b9a1069860.
  - Word-for-word copies of seed "Place background" lines: 2d90618f12ff, bb1a897eacfd, db15aec2a8fb, eb6a3ee386e2, ab84264ab6ec.
  - Hypothesis: the seed's clause "they say nothing about what this trip does" makes the instrument discount place background. Check the raw R1 fragments ($0) before changing anything.
- **Permitted background (29 claims, mostly t2).** Examples: the Taj Mahal's 17th century and Shah Jahan, Jal Mahal's submerged floors, "Pink City", Southern Luzon, northwest of Manila.
- **Over-split and unseen support are rare.**
  - Over-split: mostly headings and FAQ questions.
  - Unseen support: truncated t9 sources.

## 3. Panel-majority violations (5 B promises, 2 wrong facts)

| id | Writer / field | Type | Stored decider | Votes ok / bad | Why |
|---|---|---|---|---|---|
| 36008e040e20 | t2 itineraries | B promise (food) | tech lead, S276 accepted | 0/3 | "eat local", but the source says a multicuisine restaurant |
| 735f98b63ec7 | t2 itineraries | B promise (social) | tech lead, S276 accepted | 0/3 | "swap notes with whoever else is on the tour"; the source mentions a single traveller only |
| e5bc1dedce85 | t2 itineraries | B promise (atmosphere) | tech lead, S276 accepted | 0/3 | "Agra is still quiet when you arrive" is not stated in the source |
| 71b34111b3c1 | t2 highlights | B promise (guide qualities) | tech lead, S276 accepted | 1/2 | Calls the guide a local who knows the streets and stories; the source only says "a guide leads" |
| b729026dffbf | t2 itineraries | B promise (group experience) | tech lead, S276 accepted | 1/2 | "moving through it with people" is an invented group experience |
| 5076b862a179 | t9 content_text | Wrong fact (order) | tech lead, S275 ruling | 0/3 | Says crafts come after the library, against the itinerary line |
| a13269bb1468 | t9 meta_description | Wrong fact (direction) | tech lead, S275 ruling | 0/2 + 1 unsure | "from Kathmandu to Pokhara", against the scope order of Pokhara (Day 4) then Kathmandu (Days 5–6) |

Recommendations:
- **Relabel the 5 t2 B promises to violation.** Their stored ok came from a bulk acceptance with no reason specific to the claim.
- **5076b862a179: keep ok and file a seed bug.**
  - The panel saw a truncated source.
  - The seed's SCOPE line (visible in the batch for 098813b2c6d2) runs: National Library → Folk Heritage → Tashichhodzong → Dochu La → Thimphu → Traditional School of Arts and Craft. The writer followed it, and the S275 ruling is correct against the seed.
  - The defect is upstream: the T9 seed's SCOPE order contradicts its own itinerary line.
- **a13269bb1468: keep the ruling.** It is defensible because the trip starts in Kathmandu and "from Kathmandu to Pokhara" reads as a span. Treat it as a policy question.
- **Splits and 2–1 cases: no relabel.**
  - 761aea8afbe2: a view placed at the base camp; worth a glance.
  - 2d050de0e67b: editorial voice on a truncated source.
  - 5f09c75329d1: only 1 lens voted.
  - 2–1 cases that stay ok: 3252c741d076, 7136028c1648, ab5f3b8ad335, d6266a151813, dc8fa9cb0c24. The closest to the line is 3252c741d076 (a superlative about Junbesi's architecture).

## 4. Verdict
| Scenario | t2 | t9_blog | Overall |
|---|---|---|---|
| R1 as measured | 45/168 = 0.268 | 26/118 = 0.220 | 71/286 = 0.248 |
| 5 relabels | 50/168 = 0.298 | 0.220 | 76/286 = 0.266 |
| All 7 relabelled | 0.298 | 28/118 = 0.237 | 78/286 = 0.273 |
| Including the 3 splits | 52/168 = 0.310 | 29/118 = 0.246 | 81/286 = 0.283 |

Recall can only stay the same or rise: every relabelled claim was already fired.

**H2 dominates; H1 is marginal at 2.3–3.3% of the false positives.** Even with perfect labels the current instrument tops out at about 0.28 precision. The stored labels are sound: panel_agreed 0/70 violations, `queue: judge_right` 0/48.

## 5. Next step before any paid run
**A. Tech-lead relabel review ($0)**
- Relabel to violation: 36008e040e20, 735f98b63ec7, e5bc1dedce85, 71b34111b3c1, b729026dffbf.
- Glance at 761aea8afbe2.
- Keep 5076b862a179 and a13269bb1468 as ok, with notes.
- File the T9 seed SCOPE-order bug (Bhutan days 7–10).

**B. Instrument prompt changes**
1. Judge whole sentences and explicitly allow paraphrase and one-step inference, with examples. This targets 66% of the false positives.
2. Exempt A-type place background unless it is turned into a trip promise (a view, activity, service, time or condition). Targets 14%.
3. Treat seed "Place background" lines as valid support for claims about the place itself. Targets most of the 30 verbatim misses.
4. Skip headings, FAQ questions, CTAs, disclaimers and keyword titles, or judge them together with their answer. About 6–8 claims.
5. Keep the confirmed B-promise patterns as positive examples so recall holds: meal character, guide qualities, group or social experience, arrival or crowd atmosphere, experience at a stop.

**C. Entailment run**
- Worth running, but only after A and B, and as a gated subset:
  1. Trial on 3 claims.
  2. Up to 50 stratified claims from the 286 fired: about 25 panel-ok false positives across the paraphrase, verbatim and background groups, plus about 25 true positives including the 5 relabels.
  3. Go only if at least 60% of the false positives drop and at least 90% of the true positives are kept.
  4. Log as `adhoc_AA-1048` in `shared.llm_call_log`.
- Re-running the current extraction prompt is not worth paying for.
- Expected effect: fixes 2–4 alone would give about 0.38 precision for t2 and 0.30–0.32 for t9. Getting past about 0.5 needs fix 1.

## Caveats
- The lenses are all one model family, so their agreement is correlated. The tech lead still decides.
- 12 of the 92 t9 sources were truncated, and this caused one violation (5076b862a179).
- The fire reasons are the panel's diagnosis; the instrument's raw fragments were not in the batches. Verify hypothesis B3 against the R1 outputs ($0).