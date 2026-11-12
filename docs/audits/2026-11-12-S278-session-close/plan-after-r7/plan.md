# Phase plan after R7: sessions S279–S292 (draft for the tech lead)

Advisory lane, S278 (12/11/2026), Claude Code. Read-only: no repo, Linear or AWS change. Proposed NEW issues have no
number yet. Each one needs the tech lead's yes before it is created (Linear Free, ask first).

**Sources.** Read on 12/11/2026:
- `docs/backlog/tracker/plan.json`: synced 2026-11-11T23:42Z, session S278, 15 milestones, 39 open issues.
- `docs/backlog/README.md` §1–§4: last updated at the S277 close.
- ADR 0019, including its S270/S271/S272/S276 amendments.
- ADR 0020.
- `docs/audits/2026-11-03-S265-ecosystem-restructure/clarifications.md` §5 (prod plan) and §6 (R0–R8 roadmap).
- The S274–S277 session logs.
- `.tmp-session/S278-checklist.md`.
- The Odoo comparison (`docs/research/2026-11-10-odoo-tour-travel-plugin-comparison.md`).
- A live Linear read: 9 started + 30 backlog = 39 open, which matches plan.json, plus the issues closed in the last 14 days.

**Pacing assumption.** Recent pace is about 1.3–1.7 sessions a day (S272 was 08/11 and S277 was 11/11). At that pace
S279–S292 covers about 13/11 → 22–26/11. Date-gated items follow their date, not a session number. Some of them
(≥28/11, ≥01/12) may fall just after this window.

---

## 1. What is finished

### Milestones done, with every criterion ticked in plan.json

| Milestone | Evidence |
|---|---|
| M-R0 B2B-only + B2C freeze | plan.json `status: done`, 8/8 criteria |
| M-R1 Control plane v1 | 9/9; AA-1028 closed S267 (backlog §3 S267 row) |
| M-R3 One agency app | 5/5; AA-1036 **Done** in Linear |
| M-R2 Staff roles + tenant scope | 5/5 |
| M-P1 Pilot milestone 1 (Content + CRM on Dev) | 6/6; AA-969 Done 05/11, AA-1040 Done 08/11, AA-820 Done 10/11 (Linear) |
| M-R6 Admin IA + Writing Lab | 3/3; AA-1039 **Done** in Linear (completedAt 05/11) |

### Done in fact, but the plan.json flags are stale (fix in the plan re-cut root PR)

**M-P2: R5 + pilot milestone 2.** plan.json still says `status: later` with 0/6 ticked.
- AA-1038 is Done (Linear completedAt 10/11). The ADR 0019 amendments S270 (tp-025), S271 (CIS 379, `/{slug}`, signed
  tenant assertion), S272 (`lead.submitted.v1`, per-tenant AI cap via CIS 390) and S276 (tp-028 FORCE RLS, probe
  99/99) cover criteria 1, 2, 3 and 5.
- Criterion 4: the frontend on ECS + CloudFront + WAF is covered by Infra #721/#722/#726 (S272 log) and the WAF
  Challenge on `/api/trip/chat` (Infra #774, S277 log).
- Not checked in this review: "EXTERNAL clients frozen" (part of criterion 3).
- **Criterion 6 (AA-855 round 2) is not done.** Routine UAT videos stopped in S271 (plan.json AA-855 `next`; memory
  rule). Proposal: close the criterion as Done-with-scope (decision D9).

**M-R7: TripPlanner UX.** plan.json says `later`, 0/3 ticked.
- Criterion 1: AA-1041 is Done (Linear 11/11). It covers planner photos, icons, map sync, reorder, share, and
  Lighthouse 45 → 62 (backlog §5 S277).
- **Criterion 2 is not met as written.** It asks for a visual test against `next start` in CI, replacing the Vercel
  previews. TripPlanner `.github/workflows/visual.yml` captures 1440/390 light/dark only **after a deploy, on the
  public host, report-only** (header comment of the workflow). It is not a per-PR job (decision D8).
- Criterion 3 ("`tp_plan_chat` not done, moved to R8") is superseded: AA-1041 built the planning chat with 2 USD/month
  caps (S277 log, TP #252/#253, tp-029). Strike it (D8).

**M-OD: lessons from the Odoo app.** plan.json says `next`, 0/4 ticked.
- Done in Linear: AA-1066, AA-1067, AA-1068, AA-1071, AA-1072, AA-1073, AA-1074, AA-1075.
- Left: AA-1069 and AA-1070, both In Review and being closed in S278 (checklist A/C).

**M1b: AI gateway + FinOps.** The D8 criterion is unticked but done: AA-1024 Done S276 (backlog §1 row "≥10/11 done
S276"). AA-1026 is **Done** in Linear (completedAt 09/11), yet backlog §1 still lists its D6 November reconciliation
for the first session ≥01/12. Keep that row as a dated check, not an open issue.

### Other issues closed since the S265 re-cut that the old slot table still shows as open

The Linear read (closed in the last 14 days) shows these as Done:
- AA-900 (09/11), AA-1026 (09/11), AA-1047 W1 (08/11), AA-1052 W6 (09/11), AA-911 (08/11), AA-741 (10/11),
  AA-1063 (10/11), AA-1065 (10/11).

AA-1021 is Canceled. The backlog §3 "open issues by slot" table still lists several of these. The plan re-cut should
remove them.

---

## 2. What is left, per milestone

| Milestone | Unticked criterion | Carried by | State (source) |
|---|---|---|---|
| M-R4 Booking B2B only | B2C tables dropped after DRY RUN + independent review; `bk_inquiry_pull` code removed | **AA-1061** (Backlog) | Apply on or after 28/11 23:50Z (Linear description). **Finding:** the issue says "rebuild Booking #200 (bk-045)", but key 045 is now taken by `migrations/045_finance_costs_orders_profit.sql` (AA-1074). The drop needs a new key (bk-049 or later) |
| M-P2 | AA-855 round 2 | AA-855 (Backlog) | UAT videos stopped S271 → propose Done-with-scope (D9) |
| M-R7 | Per-PR visual on `next start` | none | Gap G2 (D8) |
| M-OD | CRM operations | AA-1069, AA-1070 (In Review) | Closing in S278 (checklist) |
| M1b | November invoice reconciliation ≤5 %; acc1 November = 0 USD | dated check (AA-1026 Done); **AA-998** (Backlog) | First session ≥01/12 (backlog §1) |
| M5 Prod + go-real | P0 module split | **AA-1004** (Backlog) | Only slice 1 is done: the Booking stack in `modules/environment`, the Deploy Prod skeleton and a guarded DB Migrate prod path (Infra #633, S266 log). The CIS, CRM and TripPlanner stacks are not moved yet |
| M5 | d7 data region applied to prod Terraform | AA-1004 | Before `aa-prod` is created |
| M5 | P2 by pilot week 3 if there is no go-live date | AA-1004 | No real pilot agency has started: no session log since S270 records one. Waits for the business owner's agency + date |
| M5 | aa-prod live with PITR, a cross-region copy and a restore drill; pilot export/import | AA-1004 | At the go-live date |
| M5 | AA-873 prod detection items; first-month cost read | **AA-873** | ≥01/12; GuardDuty stays off until its own yes |
| M5 | AA-980 prod refuses synthetic tenants; pentest | **AA-980** | At go-live |
| M5 | AA-911 bridge retired + E2E A10 removed at go-live | AA-911 **Done**; A10 → **AA-1054** | At go-live |
| M5 (risk) | CRM web high availability | **AA-1082** | At go-live, cost yes first (plan.json `next`) |
| M2a / ADR 0020 | W2 claim ground truth (R1 needs a class with n_pos ≥ 20) | **AA-1048** In Progress | S278: merge classes first (tech lead 06:45), R1 cap 2 USD |
| M2a | W3 rewire | **AA-1049** In Review | S278: 2 read-only queries → Done-with-scope |
| M2a | W4 promote the instrument | **AA-1050** Backlog | Waits on AA-1048 per class; shadow already live (CIS 391, S273 log) |
| M2a | W5 paid writer proofs (D12: ≤ $33 in total, each with its own yes) | **AA-1051** Backlog | After W2 R1 + W4 (tech lead S275) |
| M2a | T-series follow-ups | **AA-1077, AA-1079, AA-1080, AA-1081** | In Progress; being closed in S278 (checklist B) |
| M2a | AA-788 pilot of 20 pieces | **AA-788** | ≥19/11 (backlog §3) |
| M2a | Gates and writing memory | **AA-790, AA-1000, AA-920, AA-921, AA-922** | plan.json: "waiting for an LLM path + TL-11 lift". An LLM path now exists: the Anthropic direct key since S269 and the OpenAI API at a 10 USD/month cap. acc3 Claude 5.x is still refused, and the gateway falls back to 4.x (S277 log). So **TL-11 is the only blocker left** (D4) |
| CRM-after-R3 | 4 criteria (feature keys, AA-965 scope, AA-968 gate, security review per card) | **AA-960, 963, 965, 968, 970, 1011, 1012** | Slotted "after S280" (backlog §3b), so they become due in this window |
| parked | — | AA-704, AA-781, AA-782, AA-842, AA-881, AA-948 | AA-704 and AA-948 have triggers that are now met (R7 / pilot milestone 2 done) → D12 |
| M-R0 (re-scoped) | Report engine slices R5–R7 | **AA-1003** Backlog | "After S280, sources from R1 + R4" (plan.json `next`) → due now |

**M2a's Done-when is out of date.** Its criteria name the paid-run rule, AA-741 (Done), AA-788 and the Writing Lab
(done in R6). None of them measures the ADR 0020 targets:
- T9 first-pass yield from 2 % to ≥ 30 % (target 50 %);
- T9 median ≤ 5 model requests per delivered blog;
- ≤ $0.25 per blog.

Proposal: re-cut M2a as **M2b "Content quality proven"** with those three targets plus "W2 → W5 closed" (D2).

---

## 3. Gaps no issue carries yet

| # | Gap | Why it matters | Proposal |
|---|---|---|---|
| G1 | **Pilot agency onboarding.** The d16 protections exist: AA-969, `docs/ops/runbooks/pilot-tenant-restore-drill.md`. Missing: a runbook that takes a real agency from "the business owner names it" to "first post published". That means `tenant_provision` with the pilot marker, the pilot letter + DPA, the nightly export seen once, and the pilot-week-3 P2 timer as a dated check | The q-pilot rule (P2 by week 3) only works if someone starts the clock. Nothing tracks the first real agency except AA-980 (go-live, prod) | **NEW-A** `[Pilot] Onboard the first pilot agency on Dev (d16): runbook, synthetic dry run, week-3 P2 timer`. Done-when: runbook merged; dry run on a synthetic `kind=agency` tenant passes end to end; a plan.json check row exists for "pilot week 3". 0 USD |
| G2 | **R7 per-PR visual test** (M-R7 criterion 2, ADR 0019 d23 last bullet) | TripPlanner PRs have no visual check before merge, only after deploy | D8: accept the post-deploy run as met (no issue), or **NEW-B** `[TripPlanner] PR visual job against next start`. Done-when: the job runs on every PR at 1440/390 light/dark and is a required check. 0 USD (Actions minutes on a public repo) |
| G3 | **Odoo small add-ons**, ranks 45–53: crm-34 "booking confirmed" template, crm-33 cancellation-policy merge field, crm-18 portal vouchers + visa checklist, crm-01 source tour on the trip header | M-OD covers ranks 1–44 (AA-1066…1075). Ranks 45–53 have no issue | **NEW-C** `[CRM] Odoo small add-ons (ranks 45–53)`. Done-when: the four items are live on Dev with a Playwright check each. 0 USD. Low priority, CRM lane |
| G4 | **R8 has no issue.** ADR 0019 / clarifications §6 R8 has four parts: merge the Booking staff screens into AA Admin (after the B2C screens are gone, i.e. after AA-1061); tenant custom domains on CloudFront + ACM; languages beyond en/vi (machine translation tokens need a yes); a machine API for agencies (only when a paying tenant asks) | R7 is done, so R8 is the next ADR phase | D10: in this window, only **NEW-D** `[R8] Tenant custom domain for the white-label TripPlanner (ACM on CloudFront)`. Done-when: one synthetic tenant is served on its own host with a valid ACM certificate, an unknown host gets 404, and the cost is read. Estimated 0 USD extra: ACM public certificates have no fee; check the CloudFront pricing page before the build. Create the Booking-screens issue at the next re-cut, after AA-1061 |
| G5 | **AA-1061 key collision** (bk-045 reused by AA-1074) | A rebuilt #200 would clash with an applied migration | No new issue: add the new key to AA-1061's scope when it starts (a Linear comment, after your yes) |
| G6 | **plan.json / backlog drift.** Stale flags on M-P2, M-R7, M-OD and M1b; §3 still lists closed issues (AA-1036, AA-969, AA-1040, AA-741, AA-911, AA-1039, AA-1021, AA-900, AA-1026, AA-1047) | Session start reads §3 and plan.json first | Fix in the plan re-cut root PR at S279 (no issue) |
| G7 | **"Before prod" chores without an issue:** rotate the GitHub OAuth token + the RDS master password (backlog §1 last row); AA-1019 staff secret split (~0.40 USD/month, needs its own yes, backlog §2) | Easy to forget at go-live | Fold into AA-1004 P5 (gate) as named checklist items (Linear comment after your yes) |

No gap found for ADR 0020 W6: AA-1052 "[Quality W6] Lineage, dormant-code cleanup and permanent change control" is
Done (Linear 09/11).

---

## 4. Constraints that shape the plan (stated, not re-asked)

- Dev has no real users. Generate evidence now; no grace windows.
- The CRM is a complete product, not an MVP. Every card ships fully, gated by feature keys. Each card gets a security
  review before it is enabled for a pilot tenant (CRM-after-R3 criterion 4, AA-969 rule).
- Paid runs on subsets only: try about 3, then ≤ 50. Report the cost per stage from `shared.llm_call_log`, each with
  its own yes.
- No new paid AWS service without an explicit yes, with the monthly cost stated first.
- GuardDuty and the OTel spike stay off (AA-873, AA-842).
- LLM path:
  - acc3 Claude 5.x is still refused. The gateway falls back to Claude 4.x and the Anthropic direct API (card money;
    Lift credit does not cover Claude on Bedrock), and OpenAI has a 10 USD/month hard cap (CIS 327).
  - Anthropic has a 150 USD/month hard stop (backlog §2 S267).
  - Gateway spend in November was 26.45 USD at the S276 close (S276 log, measured).
- Linear is on the Free plan. 39 issues are open today. Few, deliverable-sized issues; ask before creating any.
- The tech lead chooses. Business items go to the business owner as calm proposals in the session-end Jira drafts.
- **≥ 60 % of capacity on content.** The S265 restructure README §11 ("keep ≥ 60 % for the content beachhead, as S262
  TL-3, with R0/R1/R3/R6 counted in the beachhead") and backlog §3b set this rule.
  - **Check:** S276 kept it (5 of 8 listed issues were content).
  - **S277 did not.** About 5 of 12 issues were content (AA-1076, 1078, 1083, 1077, 1049); the other 7 were CRM,
    Booking and TripPlanner (backlog §3 S277 row). This counts issues, not effort.
  - The rule was written to keep the CRM from piling onto R4/R5/R7. Those are now done, so D1 asks whether to keep it.
    The plan below keeps it.

---

## 5. Proposed phases

Four lanes run in parallel, as in S265–S277. Lane A, content quality, takes about 3 of every 5 issue slots.

### Phase 0: Converge and re-cut (S279, spill to S280)

- **Goal:** close what S278 leaves open, then make plan.json and the backlog match Linear.
- **Issues:**
  - Whatever S278 does not close among AA-1049, AA-1077, AA-1079, AA-1080, AA-1081, AA-1048 R1, AA-1084, AA-1069
    and AA-1070.
  - The plan re-cut root PR: milestone flags (G6), the new M2b milestone, the new slot table, and the NEW issues once
    approved.
- **Dependencies:** none.
- **Paid:** leftovers of the S278 cap (3.5 USD in total; AA-1048 R1 has its own 2 USD cap, S278 checklist).
- **Decides:** tech lead D1, D2, D13 (adopt the plan, M2b, create the NEW issues).

### Phase 1, lane A: Content quality proven (M2b), S279–S290

- **Goal:** finish ADR 0020 W2 → W4 → W5, lift TL-11, then run the writing-memory and gate work that has waited since
  S262.
- **Order and dependencies:**
  1. **AA-1048** W2 R1 on merged classes (≤ 2 USD).
     - If no merged class reaches n_pos ≥ 20: either seed more violations within the cap, or change the bar (D3).
  2. **AA-1050** W4: read the shadow for the measured class, then enforce that class only.
     - D11: 10 new labelled objects per workflow per month keep it growing.
  3. **AA-1051** W5 paid proofs, each with its own yes (D5):
     - eval null run ≤ $5;
     - T9 ≤ $15;
     - S1 ≤ $8;
     - T2 ≤ $5;
     - ≤ $33 in total (ADR 0020 D12).
  4. **TL-11 lift** (D4) after AA-1077 closes with one clean T9 blog round and W4 has ≥ 1 enforced class.
  5. **AA-788** pilot of 20 pieces, ≥ 19/11, then promote F12_scope / F14 / F9_brand_style to blocking on the measured
     hold-rate.
  6. **AA-790** and **AA-1000** (gates, $0 code first, then one small paid check each).
  7. **AA-920 → AA-921 → AA-922** (writing memory release 1, pinned examples / tenant preferences, weekly KPIs +
     soft-stop). The UI goes into Writing Lab.
  8. Optional, after W5 passes: **AA-781** (F9 v2 experiment, ~0.40 USD, plan.json) and **AA-782** (cheaper T9 writer
     A/B, ~1.20 USD, backlog §4).
  9. Close with an **M2b report** that measures the three ADR 0020 targets.
- **Paid estimate:**
  - Fixed caps: W5 ≤ 33 USD (D12 caps) and W2 ≤ 2 USD.
  - AA-788 about 2–5 USD. This is an estimate: 20 pieces at about the ADR 0020 target of ≤ $0.25 per blog, plus
    repairs.
  - AA-790, AA-1000, AA-920 and AA-921 ≤ 2 USD each (estimates, subset rule).
  - AA-781 + AA-782 about 1.60 USD.
  - **Lane total about 45–52 USD.** Most of it is Anthropic direct and OpenAI card money. It fits under the 150 USD
    Anthropic cap.
  - **Risk:** the OpenAI 10 USD/month cap may bind if the pinned claim instrument is GPT-6 Luna on the OpenAI API
    (ADR 0020 D7 candidate). The current OpenAI month spend was not checked in this review (D6).
- **Decides:**
  - Tech lead: D3, D4, D5, D6.
  - Labels: ~2–3 h of tech-lead adjudication per ADR 0020 D11, panel first.

### Phase 2, lane B: Pilot and prod readiness, $0 now (S280–S286, then dated)

- **Goal:** be ready to take one real pilot agency the day the business owner names it, and to start `aa-prod` (P2)
  by pilot week 3.
- **Issues:**
  - **AA-1004** P0 slices 2–4: move the CIS, CRM and TripPlanner stacks into `modules/environment` with `moved`
    blocks; the Dev plan shows no change.
  - **NEW-A** pilot onboarding runbook + synthetic dry run.
  - **AA-1003** report-engine slices R5–R7 on the R1 + R4 sources.
- **Dated (not counted as slots):**
  - Before 20/11: the tech lead's TrueIDC message and the SCP read (memory, billing-transfer timeline). The
    OrganizationAccountAccess role + OU Transitional are already done (Infra #734, S273).
  - 25–28/11: export 13 months of acc2 Cost Explorer data + invoices.
  - ≥ 28/11 23:50Z: **AA-1061** on a new key (G5).
  - 01/12: acc2 accepts the acc4 org; the agent checks health right after.
  - First session ≥ 01/12:
    - AA-998 (acc1 November = 0 USD);
    - AA-873 first-month cost;
    - November ledger reconciliation ≤ 5 %;
    - C8 TripPlanner cost;
    - remove TrueIDC's SSO role in acc2 (≥ 02/12).
  - Weekly: C4.3 W47 (≥ 16/11), W48 (≥ 23/11); the PR-20 platform report.
- **Paid:** 0 USD. `aa-prod` costs about 410–580 USD/month at list price, or 280–410 with savings, plus 0–110
  security (clarifications §5). That cost starts only at P2, after the go-live date and a confirmed monthly figure (P1).
- **Decides:**
  - Business owner: go-live date (b18) and the first pilot agency (D14).
  - Tech lead: D15 (P0 now).

### Phase 3, lane C: CRM add-ons after R3 (S281–S291, ≤ 2 slots per session)

- **Goal:** ship the paused CRM W6–W7 cards in the merged agency app, gated by feature keys.
- **Order:**
  1. AA-960 (tags, coverage, ready-to-travel).
  2. AA-963 (global search over Content + CRM by entitlement).
  3. AA-968 (campaigns through the d21 gate, reacting to `tour_liveness_changed`).
  4. AA-970 (release train, help, data page).
  5. AA-965 (AI on ancillary suppliers only, b6; gateway `pii_class` us + R1 budget).
  6. NEW-C (Odoo small add-ons).
  7. AA-1011 only once the Entra (M365) app registration exists (tech lead's step, backlog §2).
  8. AA-1012 parked until the go-live certificate decision (backlog §3b).
- **Dependencies:** a security review per card before it is enabled for a pilot tenant.
- **Paid:** about 0 USD; AA-965 dev test ≤ 1 USD (estimate). Mail and messaging run on the agency's own accounts.
- **Decides:** D11 (order; AA-965 now that an LLM path exists).

### Phase 4, lane D: R8 opening + parked triggers (S287–S292)

- **Goal:** start R8 with the one slice that helps a pilot agency and costs about nothing, and set up the next re-cut.
- **Issues:**
  - **NEW-D** tenant custom domain for TripPlanner.
  - The decision on AA-948 (builder map fork: one shared TripPlanner engine + a Mapbox cost yes, backlog §2 (g)).
  - The decision on AA-704 (in-app AI assistant, trigger "after pilot milestone 2" now met).
  - At S292: the next phase re-cut. It creates the R8 Booking-screens issue after AA-1061, and P2 if a go-live date
    exists.
- **Paid:** NEW-D about 0 USD (estimate). AA-948 needs a Mapbox quote. AA-704 would carry LLM cost per question (not
  quoted).
- **Decides:** D10, D12.

---

## 6. Session slots S279–S292

Tags: **[C]** content (lane A); **[O]** other (CRM, Booking, TripPlanner, prod, reports, CI). Dated checks (§5 phase
2) are not counted as slots.

| Session | Lane A: content | Lanes B–D: other | C / O |
|---|---|---|---|
| S279 | [C] AA-1048 R1 merged classes (≤ 2 USD) · [C] AA-1050 shadow read · [C] S278 content leftovers (AA-1049/1077/1079/1080/1081) | [O] S278 leftovers AA-1069/1070/1084 · [O] plan re-cut root PR (no issue) | 3 / 2 |
| S280 | [C] AA-1050 enforce first measured class · [C] AA-1051 eval null run (≤ 5 USD) · [C] AA-1049 Done-with-scope if still open · [C] AA-1079/1081 follow-through | [O] AA-1004 P0 slice 2 (CIS stack) | 4 / 1 |
| S281 | [C] AA-1051 T9 proof (≤ 15 USD) · [C] AA-790 code + $0 replay · [C] AA-1000 code $0 | [O] NEW-A pilot runbook + dry run · [O] AA-960 | 3 / 2 |
| S282 | [C] AA-1051 S1 (≤ 8) + T2 (≤ 5) proofs · [C] TL-11 lift review → AA-920 code · [C] AA-921 $0 part | [O] AA-963 · [O] AA-1004 P0 slice 3 (CRM + TripPlanner stacks) | 3 / 2 |
| S283 (≥ 19/11) | [C] AA-788 pilot 20 pieces (~2–5 USD est.) · [C] AA-790 paid check (≤ 2) · [C] AA-1000 paid check (≤ 2) | [O] AA-968 · [O] AA-1003 slice R5 | 3 / 2 |
| S284 | [C] AA-920 release 1 (≤ 2) · [C] AA-921 LLM part (≤ 2) · [C] AA-922 logic | [O] AA-970 · [O] AA-1004 P0 close (plan no-change proof) | 3 / 2 |
| S285 | [C] AA-922 UI in Writing Lab · [C] AA-788 promote to blocking on the hold-rate · [C] AA-781 experiment (~0.40) | [O] AA-965 (≤ 1 USD) · [O] NEW-C Odoo add-ons | 3 / 2 |
| S286 | [C] M2b measurement (ADR 0020 targets) · [C] AA-782 A/B (~1.20) if W5 passed · [C] AA-1050 next class | [O] AA-1003 slice R6 · [O] AA-1011 if the Entra app exists, else buffer | 3 / 2 |
| S287 | [C] D11 monthly labels (10 objects per workflow) under AA-1048/1050 · [C] fixes found by W5 / AA-788 (under the issue that found them) | [O] NEW-D custom domain slice 1 · [O] AA-1061 prep on a new key (DRY RUN only) | 2 / 2 |
| S288 | [C] AA-922 first weekly KPI read · [C] content buffer | [O] NEW-D close | 2 / 1 |
| S289 (~25–28/11) | [C] AA-788 close · [C] AA-1050 class follow-up | [O] AA-1003 slice R7 | 2 / 1 |
| S290 | [C] M2b milestone report (close or re-cut) | [O] AA-1061 apply (≥ 28/11 23:50Z) · [O] CRM card follow-ups from security review | 1 / 2 |
| S291 (≥ 01/12 if reached) | [C] AA-1050 / AA-1048 close-out · [C] Writing Lab weekly sample (ADR 0020 D9) | [O] AA-948 / AA-704 per D12 (or buffer) | 2 / 1 |
| S292 | [C] content buffer | [O] next-phase re-cut (R8 Booking-screens issue, P2 if a go-live date exists) | 1 / 1 |
| **Total** | | | **35 / 23 → 60 %** |

The 60 % holds only if lane C stays at two slots or fewer per session and dated checks are not counted. If lane A runs
out of unblocked work, for example while waiting for labels, the free slot goes to a content buffer, not to a third
CRM card.

---

## 7. What the tech lead and the business owner must decide

**Tech lead** (details and options in `decisions.json`):
- D1: keep the ≥ 60 % content rule;
- D2: re-cut M2a → M2b with the ADR 0020 targets;
- D3: AA-1048 if no merged class reaches n_pos ≥ 20;
- D4: TL-11 lift trigger;
- D5: the four W5 paid yeses;
- D6: the OpenAI cap during W4/W5;
- D7: AA-788 paid pilot yes;
- D8: the R7 visual criterion;
- D9: AA-855 round 2;
- D10: which R8 slices;
- D11: CRM lane order and AA-965;
- D12: AA-948 / AA-704;
- D13: create NEW-A, NEW-C, NEW-D (and NEW-B if D8 = B);
- D15: AA-1004 P0 now;
- D16: the AA-1061 new key.

**Business owner**, as calm proposals in the session-end Jira drafts, not asks in chat:
- the go-live date (b18) and the first pilot agency (D14);
- the 10 M-OD default answers, still pending since S275 (Jira PR-26 comment 10636; the system uses the proposed
  defaults until then);
- the wording of the Booking `departure_fees` terms, still a draft (S277 log "Còn lại");
- signing the TrueIDC Billing Transfer appendix (plan.json `waiting`).
