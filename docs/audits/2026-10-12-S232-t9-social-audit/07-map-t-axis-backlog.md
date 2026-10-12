# T-series (tenant / B2B) — remaining work after S232

Sources: the plan doc §7, the S229 and S231 audits, the S231 session log, the AA-763/764/768 implementation notes, App git log (#661–#673) and Linear (read-only, nothing written).

## 0. State at the end of S232

| Area | State |
|---|---|
| Dev | api `:545` / worker `:100`. Today's merges: App #665–#673 plus Infra #91 (migration 219). |
| G1, G2, G3 | Done in S231 (tenant_id on every LLM call; DE/FR/NL research at 263 keywords each; pilot report written). |
| G4 / AA-763 | In Progress. Live check passed for T2 and T7: one T2 job logged only `t2_*` stages, 44/44 rows tagged with the tenant. **Not yet seen live: an S1 job still logging only `s1_*`.** |
| G5 / AA-764 | Done (#667): slate, angles and fact-select run as jobs; `GET /v1/slate` only reads. |
| AA-768 (T9 fidelity) | In Progress. F1 (invented numbers) is solved: 0/10 holds. Done-when is ≥4/5 approved; current result is 4/10 approved and 6/10 passing F1+F9. What still holds: the F9 judge over-flagging (4/10) and the blog format gates F3/F5 (3/10). |
| Cost per piece (n=10) | blog ~$0.097, LinkedIn ~$0.02 (pilot was $0.14 / $0.057) |

## 1. G-items (plan §7)

| G | Item | Status | What is left | Depends on |
|---|---|---|---|---|
| G1 | tenant_id on every LLM call | **Done** | Nothing. HTTP-path rows were covered by G5. | – |
| G2 | segment_research DE/FR/NL | **Done (pilot scope)** | Only the 73 places of the 3 pilot tours were researched (99 places per market). G7 tours need DE/FR/NL coverage too: an ops run Nghiệp triggers, DFS cap $5 per run, estimate first. | G7 tour list |
| G3 | Pilot | **Done** | Nothing. Findings 1–4 fixed; 5 → G5; 6 → AA-768; 7 and 8 still open (below). | – |
| G4 | T-series stage keys (AA-763) | **In progress** | Confirm that the next natural S1 job logs only `s1_*`, then close. No other code left. | a natural S1 job |
| G5 | T7/T8/T9-select on the worker (AA-764) | **Done** | Portal UX of the new async states (slate "updating…", angle `generating`/`generation_failed`) gets checked in G11/G12. | – |
| G6 | One judge client; T11 dispatch into `acp_publish`; stale docstrings (AA-765) | **Not started** (Backlog, Low) | All 3 scope points. A natural place to fold in the F9 judge call that AA-768 changed. | none; best after the F9 calibration so the client is not rewritten twice |
| G7 | Full run, 48 tours (12 × 4 tenants) | **Not started**, held on purpose | Pick the 12 tours (include wildlife/elephant and family tours), run T2 → T7 → T8 → T9 → T10 → export, fill the label sheet during the run. Today about half the pieces would be held by the F9 judge alone, so the run would mostly measure judge noise. | F9 calibration (AA-701), F3/F5 decision, Debate calibration (finding 7), G2 coverage for the chosen tours, G4 closed |
| G8 | T-series report + mechanism table + roadmap | **Not started** | S218 structure, plus the portal UI/UX list (AA-741 scope point 6) and one follow-up issue per "not fit" mechanism, created after Nghiệp approves. Closes AA-741. | G7 |
| G9 | Tenant 360: Cost / Quality / Markets tabs (AA-766) | **Not started** | All 3 tabs. Real cost numbers exist now (S231/S232). Done-when is checked on **production** admin. | G3 (done); the Quality tab is more useful after G7 |
| G10 | PortalShell (AA-759) | **Not started** | Whole issue. | – |
| G11 | Page audit + state fixes (AA-760) | **Not started** | Statuses must come from the job (the "Writing…" bug), including the new G5 states. Input: the G8 UI list. | G10 |
| G12 | Writer panel (AA-668) | **Not started** (High) | Panel UI, CTA from brand defaults (new Brand field) instead of the blocking 422, job-based status, Playwright flow at 1440×900. The backend part (G5) is ready. | G5 done; G11 |
| G13 | Account pages (AA-761) | **Not started** | Billing usage/overage, activity timeline, integrations. | G10; billing numbers from G9 |
| G14 | Marketplace redesign (AA-671) | **Not started** | Whole issue. | G10 |
| G15 | Team & roles (AA-762) + login (AA-703) | **Not started** | Both issues. | Ecosystem identity ADR + SES; AA-703 build-vs-buy decision |

## 2. Open issues on the T axis (Linear)

| Issue | Status | What is left | Dependencies |
|---|---|---|---|
| **AA-741** epic (audit) | In Progress | Phase 0 and phase 1 done. Left: phase 2 (G7 with labels), phase 3 (G8 report plus the UI/UX walk of every portal page using the 4 tenants' data). It also carries findings that have no issue of their own (Linear plan limit). | G7, G8 |
| **AA-768** T9 fidelity | In Progress | Done-when (≥4/5 approved) not met. The writer side is finished; what is left is judge precision (F9) and a product decision on F3/F5. Close it either by meeting the target after the F9 calibration, or by re-scoping with Nghiệp (F1 is solved and F9 moves to AA-701). | AA-701 F9 work; Nghiệp's F3/F5 decision |
| **AA-701** T10 gates + Jev | In Progress | Six questions run in shadow (`jev_observe.py`): `t10_rubric_met`, `t10_brand_voice`, `t10_cta_clear`, `t10_same_piece`, `t10_offer_as_certain`, `t10_faq_restates`. The pilot and the S232 rounds wrote `decision_log` rows. Left: (a) confirm the gate outcomes did not change; (b) **calibrate**: label the ~40 F9 flagged claims from the S232 rounds, measure judge precision, then tighten the judge rule or move the claim check to Jev; (c) enforce questions one at a time after their labels. **Note: there is no T10 Jev question for the F9 fact half.** The shadow set covers only style (`t10_brand_voice`) and CTA (`t10_cta_clear`). Claim support would reuse `a1_claim_supported`, the same question as T3-1 ("is this sentence supported by the source?"), which is already calibrated and in enforce mode. | the AA-768 claim set; G7 labels for the remaining questions |
| **AA-699** T0/T2/T3 Jev | In Progress | Done-when is not verified yet. In the pilot, `t3_grounding` was 92/93 grey. Not yet shown: that a flagged number the source supports no longer triggers a rewrite. T0-1 (brief-section Choice in `parse-docx`) is shadow, also unverified. T2-1 tie-break (`a1_brand_fit`) runs in shadow. | one T2 run with a flagged-but-supported number; the reject ceiling for `a1_claim_supported` (AA-756 item 1) also cuts the T3 grey share |
| **AA-696** parent (T-series Jev) | In Progress | No scope of its own; closes when AA-699 and AA-701 close (AA-700 is Done). **Pilot finding 7 has no issue:** Debate (`t7_topic_fits_brand`) flagged 82–90% of candidates (49–54 of 60), all grey. AA-700 is closed, so this calibration needs a home: an AA-696 comment or a new issue (ask Nghiệp first). | label sample from the slates of the 4 tenants |
| **AA-756** Jev system-wide calibration | In Progress | Item 1 (`a1_claim_supported` reject ceiling) also serves T3 and a possible F9-to-Jev move. Item 5 (write `decision_log.outcome`) is the long-term way to calibrate T questions without hand labelling. | Nghiệp's labels |
| **AA-763** G4 | In Progress | One S1 job check. | – |
| **AA-765** G6 | Backlog | See G6. | after the F9 calibration |
| **AA-766** G9 | Backlog | See G9. | – |
| **AA-759 / 760 / 668 / 761 / 671 / 762** | Backlog | G10–G15 above. | chain G10 → G15 |
| **AA-703** passwordless login | Backlog | Design first: identity model, build vs buy, SES, ADR. | identity ADR |
| **AA-729** golden set (~30 tours) | Backlog (High) | A-series focused, but G7 labels could seed a T-series golden set. | G7 |
| **AA-628** engagement feedback loop | Backlog (Low) | Investigate first; needs real published pieces (T11 / `publish_log`). | after portal and T11 are live with real tenants |
| **AA-704** in-app assistant | Backlog | Not on the T critical path. | – |
| AA-700, AA-764, AA-726 (T11 idempotent publish), AA-666, AA-669 | Done | – | – |

## 3. Loose items without an issue (tracked in comments or session logs)

1. **Pilot finding 7:** Debate flags 82–90% of candidates. Calibration needs a home (see AA-696).
2. **Pilot finding 8:** T2 quality. 5/12 versions reach score 7, and about 7 generate calls per tour make up 95% of T2 cost. To be analysed in G7 with tenant-market keywords switched on (#664).
3. **#662 ALB 502 fix:** check that `HTTPCode_ELB_502_Count` stays 0 for the week, then note it as closed on AA-741.
4. **Location line in the seed:** it uses one country per tour (`raw_tours.country`), so a place in the second country of a multi-country tour gets the wrong line. Accepted as rare; re-check in G7 with the Laos→Vietnam tour.
5. **`max_tokens=4096` for T9** is not tuned per channel (plan §1). Small cost item; look at it in G7.
6. **Linear housekeeping:** auto-archive after 1 month (Settings → Teams). Its status is unknown in the S231 log.

## 4. Social-content gates (T7 → T10): where each stage stands

| Stage | LLM call | Jev (shadow unless noted) | State after S232 |
|---|---|---|---|
| T7 slate | Debate judge `t7_debate_judge` (G4) | `t7_topic_fits_brand`: 100% grey, cuts 82–90% | Runs as a job (G5). **Needs calibration.** |
| T8 angles | Sonnet, 3 angles | `t8_angle_answers` | Runs as a job; seed = atom evidence + hook + siblings (#669) |
| T9 fact-select | – | `t9_fact_relevant` | Runs in the `t9_write` job (G5) |
| T9 write | `t9_write`; attempt 2 repairs single sentences (#673) | – | F1 solved |
| T10 F1 grounding | deterministic number check | – | 0/10 holds |
| T10 F3/F5 (blog structure / atom density) | deterministic | – | 3/10 blog holds. **Product decision: block or warn?** |
| T10 F4 SEO length | deterministic + `_fit_seo_meta` (#670) | – | solved |
| T10 F8 framework | `t10_judge` (warn) | `t10_rubric_met` | warn only |
| T10 F9 CTA / fact / style | F9 judge (Luna, 8192 tokens, source-aware) | `t10_cta_clear`, `t10_brand_voice`; **no Jev question for the fact half** | 4/10 holds, mostly over-strict. **This is the bottleneck.** |
| T10 F10 cannibalization | `f10_embed`, cosine ≥ 0.92 | `t10_same_piece` (≥ 0.85) | not exercised in the pilot (no approved pieces from other tenants yet) |
| promises / FAQ dedup | rules | `t10_offer_as_certain`, `t10_faq_restates` | shadow |

**Can Jev be combined here?** Yes, at three points, all calibrated before anything is enforced:
- **F9 fact claims → `a1_claim_supported`.** Send each claim the judge flags, with its source, to this already-calibrated question. A Jev accept overrules the judge flag; a reject or grey keeps the flag. This directly targets the over-strict flags such as "Songtsen Gampo ordered it built". Cheap, because only the ~1–3 flagged sentences per piece are asked.
- **T7 Debate.** Calibrate `t7_topic_fits_brand` from labelled slates.
- **The other `t10_*` shadow questions.** Enforce one at a time after G7 labels.

The ~40 S232 claims are the first labelled set for the F9 → `a1_claim_supported` check.

## 5. Proposed order

1. **F9 calibration (AA-701, closes AA-768).** Label the ~40 S232 claims (real vs over-strict), measure judge precision and Jev `a1_claim_supported` on the same set, then pick: tighten the judge rule, use Jev as an overrule on flagged claims, or both. Re-run the same 5 requests twice (n=10); target ≥ 8/10 passing F1+F9. Low cost (Jev cents plus about $1.2 per n=10 run).
2. **Nghiệp decides F3/F5 for blogs (block or warn).** Apply the decision. A one-line config change if it becomes warn.
3. **Close AA-763** when the next natural S1 job shows only `s1_*`.
4. **Debate calibration (finding 7).** Label one slate per tenant (~60 candidates × 4), set thresholds for `t7_topic_fits_brand`, so G7 is not run on an 82–90% cut rate. Needs a home in Linear (ask Nghiệp).
5. **AA-699 live check.** One T2 run on a tour with a flagged-but-supported number; record the T0-1 shadow rows. Can run as part of G7.
6. **Pre-G7:** pick the 12 tours, then a DE/FR/NL `segment_research` run for them (estimate first, Nghiệp triggers, $5 cap).
7. **G7 full 48 run**, with the label sheet filled during the run. Spend under the 50-tour paid-run rule; expect about $0.38 per T2 tour plus about $0.1 per blog piece / $0.02 per social piece.
8. **G8 report + portal UI/UX walk.** Follow-up issues after approval. AA-741 closes; AA-701 and AA-696 close as their questions are calibrated or enforced from the G7 labels.
9. **G9 Tenant 360 (AA-766).** Can start in parallel after step 1, since the cost numbers already exist.
10. **G6 (AA-765) cleanup**, after step 1 so the F9 judge client is final.
11. **Portal chain:** G10 AA-759 → G11 AA-760 → G12 AA-668 (High; backend ready) → G13 AA-761 → G14 AA-671 → G15 AA-762 + AA-703 (after the identity ADR and SES).
12. **Later:** AA-628 engagement loop, AA-729 golden set (seeded from the G7 labels).

**Decisions needed from Nghiệp:**
- (a) Approve the F9 calibration and the Jev overrule.
- (b) F3/F5 for blogs: block or warn.
- (c) Where Debate calibration is tracked (new issue vs an AA-696 comment).
- (d) The G7 tour list and the DE/FR/NL DFS run.