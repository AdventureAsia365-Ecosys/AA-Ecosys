# S234 — T-series rounds 1–4 after AA-772/768/771/769

Real tenant flow on Dev, the same 6 requests as S233 (4 test tenants; 8 blogs on one Mongolia route brief re-angled
with `regenerate-angles`, 12 LinkedIn posts on Punakha / Tiger's Nest / Kuang Si). Each round = 20 pieces written
as `t9_write` jobs on the **worker** service via the public tenant API; scored by a 4-lens panel of independent
Claude Code agents (local, not on the gateway) + a fidelity auditor + a deterministic hard-error script that uses
the repo's own `hygiene` / `claim_rules` code.

| | S233 r1 | S234 r1 | r2 | r3 | r4 |
|---|---|---|---|---|---|
| Code on Dev | #674–#686 | #687–#692 | +#693–#695 | +#696–#697 | +#698 |
| Light edit (all) | 30% | 55% | 50% | **60%** | 55% |
| LinkedIn light | 6/12 | 11/12 | 10/12 | 10/12 | 10/12 |
| Blog light | 0/8 | 0/8 | 0/8 | 2/8 | 1/8 |
| Publish as-is | 0 | 0 | 0 | 0 | 0 (2 as-is votes) |
| Overall /10 | 5.33 | 5.52 | 5.57 | 5.64 | **5.74** |
| AI-tells /10 | 4.45 | 4.54 | 4.45 | 4.60 | 4.75 |
| Fidelity audit /10 | – | 7.10 | – | 7.38 | **7.47** |
| Core hard errors (same script, r4) | 70 | 11 | 10 | 8 | **4 (all in held blogs)** |
| Clean pieces | 2/20 | 14/20 | 14/20 | 16/20 | **18/20** |
| Gate approval / precision | 60% / 42% | 85% / 59% | 50% / 80% | 65% / 77% | 55% / 73% |
| Pipeline cost / 20 pieces | $1.58 | $0.93 | $1.03 | $1.13 | $1.15 |

Hard-error totals are re-measured with `measure_r4.py` on every set, so they differ slightly from the per-round reports.

## Reading
- Deterministic hygiene is essentially done: scope, leaks, social proof, hashtags, LinkedIn shape, CTA literal,
  FAQ contract, trip length, keyword grounding, duplicates. No approved piece carries a core hard error in r4.
- LinkedIn is shippable with a light human pass for Terra (Tiger's Nest), A&H and WildKind (Punakha): 3/3 light each in r4.
  Trail Pulse is the weak cell in every round (voice + short posts).
- Blogs improved (structure, anchor weight, FAQ, scope) but stay mostly heavy: "optional" flips, invented pace /
  product promises, repair residue, AI phrasing. Light share plateaus at 55–60% — further gains need writer-side
  changes, not more gates (see the S234 session log, advisory).

## Files
- `02-panel-round1.md` … `07-panel-round4.md` — panel reports per round (per-piece votes, defect classes, next fixes).
- `05-f9v2-replay.md` — F9 v2 offline replay (typed claims + code rules) vs current F9: cheaper and steadier, below the 90% bar; not wired.
- `06-place-card-model-ab.md` — drafter A/B (Sonnet / Haiku / GPT-5.6 Luna / GPT-6 Luna) → migration 222.
- `08-pipeline-stats-thu-jev.md` — how T9 writes a piece (inputs, steps, LLM calls, every gate, retry logic, outputs), failure/retry statistics from the DB, comparison with chị Thư's repo, Jev audit.
- `09-next-step-plan.md` — concrete next-step plan: issues, paste-ready prompt changes, builds, Jev actions, measurement targets.
- `10-agent-team-design.md` — multi-app agent team: feasibility, roles, protocol, pilot for the next session.
- `11-next-session-team-pilot.md` — what Nghiệp approved for S235 (lanes, architect agent, Booking bootstrap, guardrails).
- `12-gates-t2-tenants.md` — evaluation of all T9 gates vs the panel (keep/tune/merge/drop/new), why T2 scores are low (root causes + fixes), metric-by-metric audit and redesign of /admin/tenants, 15 PROPOSED issues for S235.
- `label-pack/` — 40-piece human labelling workbook + Vietnamese criteria (AA-783).
- Scratch (not committed): `.tmp-session/s234/` — pieces_r{1..4}.json, measure scripts, panel raw votes.
