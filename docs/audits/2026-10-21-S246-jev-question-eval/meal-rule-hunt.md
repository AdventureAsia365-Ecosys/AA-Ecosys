# AA-803 J04/J05: the deterministic meal rule did not converge (S246)

**Goal.** J04/J05 were approved in S246 as "ship the meal rule first, then switch `a1_claim_supported` and `a1_promise_unsupported` OFF". The plan was a source-grounded rule, run before Jev, that clears `ITINERARY_MEAL_TIME_INVENTED` when the source provides the meal on the same day or in INCLUSIONS.

**What was done.** The work is on CIS branch `feat/meal-claims-from-source`, draft PR #905. It has 5 commits and 377 unit tests, and the full unit suite (10790) is green.
- Workflow 1: builder, then review, then fix. The review found 3 blocking false clears (B1 to B3), and all were fixed.
- Workflow 2 was an adversarial hunt. Each round ran 3 lenses (source-side parsing, output-side claim extraction, day mapping), then an independent refute-verify of each finding, then a fix. Rounds stop at 3 or at one dry round.

| Round | Confirmed false clears | Fixed |
|---|---|---|
| 1 | 23 | yes, `6877d92e` |
| 2 | 22 | yes, `473d8ca4` |
| 3 | 20 | yes, `d5534720` |

**No dry round.** Every round found about 20 new realistic false clears. Examples:
- a bracketed "No meals" erased by the clause split;
- full board scoped to trek days read as every day;
- "opt for" / "free to find" meals counted as provided;
- an inline "Day 3:" marker letting the next day's meal source this day;
- plural "Lunch and dinner are included" never checked.

The real-data replay barely moved (window population cleared 184 to 183 of 268). The holes are in the long tail of operator and writer phrasing.

**Decision (agent, S246):**
- Do not merge.
- Keep `a1_claim_supported` and `a1_promise_unsupported` ON.
- AA-845 stays open.
- Reason: the rule runs before Jev, so any false clear is never checked again. A regex rule over free text does not converge here.

**Proposal for S247.** Narrow the design:
1. The rule clears only structured evidence: a day code list or a `Meals:` list naming the meal on the same matched day, or an unscoped full-board or daily INCLUSIONS form.
2. Every other meal sentence goes to Jev, as today.
3. Ship the wider `ITIN_MEAL_INVENTED` detection (plural, future and generic claims) on its own. It is a real gap on main.
4. Measure how many Jev meal calls the narrow rule removes, and whether the 71 waivers fall. Only then revisit OFF for J04/J05.
