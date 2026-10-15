# AA_Ecosys living backlog (ordered work queue)

**Purpose:** the single ordered list of what to do next, so a session starts here instead of re-auditing Linear. Built from the S238 full audit (69 open issues + data standards + logs + code + Jira, `docs/audits/2026-10-15-S238-backlog-audit/`) and updated at the end of S238.

**Rules:** at session start read §1–§3 and pick 3–5 items from §3 top-down (skip items blocked in §2). At session end update the Status column, move closed items to §5, add new items. Re-audit only when this file is older than ~2 weeks or many issues were created outside sessions.

_Last updated: S238, 15/10/2026 (Claude Code)._

## 1. Time-gated checks (do these first when due)

| Due | Issue | Check |
|---|---|---|
| ≥16/10 | AA-843 | Logs Insights 24 h after 15:20 UTC 15/10: 0 `t1_failed_trying_t2` / `t2_failed_trying_t2_5a` / `t1_sonnet_not_subscribed`; writer rows on acc3 → Done |
| ≥17/10 | AA-828 | Cost Explorer grouped by tag App: cis + shared lines no longer ~$0 |
| ≥21/10 | AA-801 | T2 judge 1-week watch readout (t2_judge rows since 14/10) → close |
| ≥22/10 | AA-833 | 7 days: browse/assembly throttle alarms never flipped, Throttles≈0 → Done |
| 31/10 | AA-714 | Pick the single judge primary, turn the shadow off, PR-16 wording |
| ≤11/11 | AA-820 | Counsel-approved AI clause in tenant terms; tenants notified (Nghiệp) |
| 12/11 | AA-819 | AUP in force: remaining evidence + CTA policy |

## 2. Waiting on Nghiệp (decisions / manual steps)

- ~~Jira drafts S238~~ — posted 15/10 with inline images/docx: PR-7 (10474), PR-17 (10475), PR-12 (10476), PR-11 (10477).
- AA-820: engage counsel this week.
- Close-or-keep decisions from the audit: AA-768 (accept r5 as evidence), AA-771, AA-763, AA-678, AA-681, AA-683, AA-710, AA-772, AA-729 (rewrite or cancel), AA-701 (dead-code chore then cancel).
- Re-scopes: AA-751 → X6 per-owner job tables; AA-703 / AA-813 / AA-816 rewritten per ADR 0006; AA-679 Done-when → D4.
- Paid runs (approve each): AA-777 (~$2), AA-800 (<$1), AA-782 (~$1.2), AA-784 ($15–25, after AA-712 canonical ids), AA-741 G7 ($10–20, after AA-787/AA-800).
- AA-841 (optional): precautionary DataForSEO password rotation — nothing is broken; decline = close.
- Product questions: one day separator per tenant catalog for T2 (`:` vs ` · `)? Tenant tour names lose "— N Days" (become ", N Days") — OK? (AA-778)

## 3. Ordered work queue (next sessions)

| # | Issue | Work | Lane | Size | Status after S238 / next action | Needs Nghiệp |
|---|---|---|---|---|---|---|
| 1 | AA-833 | TripPlanner browse still throttles at concurrency 15 + throttle alarms page on every 5-min blip | Infra/ops + TripPlanner | M | Shipped (CIS mig 235, TP #81, Infra #133). 7-day watch: no alarm flips, Throttles≈0 → close ≥22/10. | Approve creating the issue and the targeted alarm apply. Any raise in browse concurrency must stay within the tripplanner CONNECTION LIMIT 30. |
| 2 | AA-792 | T2 tenant voice: export Trail Pulse / A&H versions for the voice read, then send PR-17 samples to Ms. Thư | CIS T-series | S | PR-17 voice samples ready (docs/audits/2026-10-15-S238-backlog-audit/pr17/*.docx). Samples posted to Jira PR-17 (comment 10475, .docx attached). Waits on Ms. Thư voice read. | Voice read of the Trail Pulse and A&H versions. |
| 3 | AA-831 | Facebook Page connect: tenant guide (promised on PR-7) + correct connect-card help text | CIS portal | S | Shipped + UI-verified (CIS #747/#748). PR-7 guide comment posted (10474). Close once Nghiệp confirms. | — |
| 4 | AA-819 | AUP 2026-11: live evidence for the daily publish limit (429), F19 block path, TripPlanner AI badge audit | CIS portal | S | 429 live evidence done. Remaining: F19 block/rewrite live evidence, TP AI-badge audit, CTA review-claim policy (Nghiệp + Ms. Thư). AUP deadline 12/11. | Policy on review claims in a tenant's own CTA, with Ms. Thư. Decide whether a visible daily-quota counter is wanted. |
| 5 | AA-820 | Tenant Terms AUP clause: counsel review + Booking high-risk boundary line in CONTEXT.md | Legal/docs | M | No change. Nghiệp: counsel review this week (due 11/11). | Engage counsel this week, approve the clause, and have Ms. Thư notify tenants before 11/11. |
| 6 | AA-778 | Em-dash: deterministic autofix, strip em-dashes from prompts, residue guard | CIS T-series | S | T9 (#749) + T2 (#752) shipped, live 0 em-dash. Remaining: panel AI-tells ≥5.5 at the next n=20 checkpoint (paid); colon density watch. |  |
| 7 | AA-703 | Cognito identity epic, Phase 0: ACM us-east-1, spike, apply Infra #105, break-glass, first staff email-code login | Identity/infra | XL | Unblocked (SES prod). Next: rewrite epic per ADR 0006, Phase 0 (ACM us-east-1, spike, Infra #105 apply, break-glass). | Approve the rewritten epic scope. Break-glass TOTP device. EXTERNAL Google OAuth client (later). |
| 8 | AA-817 | RLS follow-up: observed flag flip, move tenant route groups, fix remaining policies; plus tenant_integrations RLS/DELETE grant and the X2 catalogue guard (folded) | Data platform / CIS | L | No change S238 (scope additions: tenant_integrations RLS, X2 catalogue guard). | Approve the observed flag-flip window on Dev and the order in which route groups move. |
| 9 | AA-806 | CI role split step 3 + WAF enforce; plus a clean full-root Terraform plan (hidden drift on secrets/RDS/random_password, folded) | Infra/security | M | Scope addition: clean full-root plan (16 hidden drifts) — prerequisite for CI full applies. | Geo list for Booking customers before WAF goes onto the Booking REST stage. |
| 10 | AA-828 | Per-app cost allocation tags + budgets; clean up stale AA-360/AA-364 alarm comments (folded) | Infra/ops | S | Per-app budgets + App tags (90 resources) + LLM spend e-mail live. Remaining: Cost Explorer by App after 24–48 h, CloudTrail log bucket tag (after AA-806 drift), forecast alerts. | Budget amounts per app. |
| 11 | AA-708 | Photos: CloudFront in front of photos/ + daily scheduled sync (PR-11 promise, folded), Laos sync | Infra + CIS | M | Moved to In Progress. Remaining: Ms. Thư usage rights + Laos/Seorak; CloudFront + daily sync (PR-11 promise). | Ask Ms. Thư about photo usage rights and the Laos/Seorak folders. |
| 12 | AA-802 | Silent correction live check + latest-piece rule on /v1/publish-log/pending (46 duplicate Ready-to-Publish cards, folded) | CIS portal | S | Ready-to-Publish latest-piece rule shipped (48→3 cards). Remaining: silent-correction live check (one admin edit on a held piece). | Approve one admin edit on a test tenant's content as evidence. |
| 13 | AA-834 | Fix flaky AA-752 smoke test (b): the click lands before hydration | CIS portal/CI | S | Not started. | Approve creating the issue. |
| 14 | AA-712 | Place pipeline: L4 catalog read-model latency, PLACES_SOURCE=cis flip, content-validity checks, photo_sync off frozen TP tables, a3_place_days shadow decision (folded) | CIS platform + TripPlanner | L | Mig 235 (view_tour_place 11× faster) shipped. Remaining: L4 full-catalog reads, pre-flip content checks, X4 photo-sync move, a3_place_days shadow decision. | Approve creating an L4 issue, or fold L4 in here. Paid catalog run (≈$15-20) after the flip. Laos replaces Korea in the Done-when. |
| 15 | AA-800 | Tenant signature vocabulary: 3-layer forbidden lists, per-tenant writer rule | CIS T-series | M | No change S238. | Paid verification run (<$1). |
| 16 | AA-777 | F9 judge consistency: sticky pass, attempt-3 cut for blogs, judge A/B (drop the gpt-4.1 arm) | CIS T-series | M | No change S238. | Approve the paid A/B (≤$1) and r6 (~$1.1), and the A/B arms. |
| 17 | AA-780 | LinkedIn: Trail Pulse voice fields, broetry + stock lines, hashtag place-name check | CIS T-series | S | No change S238. | Review the Trail Pulse T0 voice fields (data change). |
| 18 | AA-816 | Staff directory + Cognito groups (ADR 0006 Phase 1); retire create_staff_user.py | Identity / CIS admin | L | No change S238. | Confirm the Done-when rewrite. Booking roles move to cognito:groups. |
| 19 | AA-682 | Booking wave 3: supplier bookings + trip checks, then invoices/payment schedule | Booking | XL | No change S238. | Manual payment marking only for the MVP. Tax handling while the accountant is pending. Approve the split. |
| 20 | AA-822 | Wave 2a: UI verify /suppliers + live create of a supplier/contract | Booking | S | No change S238. | Allow test write data. Act as second approver for publish. |
| 21 | AA-823 | Wave 2b: hotel + service as trip-case items with net-rate default and AA-810 sell price, UI verify | Booking | M | No change S238. | Act as second supply.write approver. |
| 22 | AA-679 | Catalog read in Booking: Done-when rewrite to D4 + live 'Use for trip case' verify + low UI defects | Booking | S | No change S238. | Approve the D4 Done-when rewrite. Allow marking one plan sellable on Dev. |
| 23 | AA-832 | Remaining C4.1 RDS alarms: latency, disk queue, XID, per-role connections vs CONNECTION LIMIT | Infra/data platform | M | Not started. | Approve creating the issue. |
| 24 | AA-827 | TripPlanner guest_token: random token, store the hash only | TripPlanner | M | Not started. |  |
| 25 | AA-825 | Retention: observed DRY RUN per kind, then real archive-delete; Booking job TTL + inbox PII redaction (folded) | Data platform | M | No change. Next: observed DRY RUN per kind, then real delete; Booking/TP owner kinds. | OK each kind from DRY RUN to real delete after reading the counts. |
| 26 | AA-751 | Re-scope to X6: job DDL template, booking.job columns, Booking deploy job guard, DB Migrate idle check, backlog-age alarm | Data platform / Booking / Infra | M | Re-scope to X6 proposed (comment) — Nghiệp to confirm. | Confirm the re-scope (data-standards open item #4). |
| 27 | AA-791 | Label form: no pre-selected verdict, LABEL column visible at 1440, first label save | CIS portal | S | No change S238. |  |
| 28 | AA-801 | T2 judge: 1-week watch readout after ~21/10, then close | CIS T-series | S | No change S238. |  |
| 29 | AA-714 | Pick the single judge primary on/after 31/10, turn the shadow off, PR-16 update | CIS platform | S | No change S238. | The 31/10 model decision and the PR-16 wording. |
| 30 | AA-836 | Portal layout at 390 px + My Catalog source 404 + raw markdown previews (D2/D3/D4/D6) | CIS portal | M | Not started (frontend: Vercel Hobby build limit hit 15/10 — resets 24 h). | Approve creating the issue. |
| 31 | AA-818 | Switch app base URLs/canonical to the custom domains; booking. staff host | Infra/TripPlanner/Booking | S | No change S238. | Edit the Vercel env vars by hand (underscore names). Confirm the name booking.lumiguides.it.com. |
| 32 | AA-768 | Close the T9 source-fidelity umbrella on r5 evidence | CIS T-series | S | No change S238. | Accept r5 instead of re-running the 5 S231 requests. |
| 33 | AA-771 | Close the brand pack: criteria 1+2 met, criterion 3 moves to AA-800/AA-790 | CIS T-series | S | No change S238. | Choose close now or keep open. |
| 34 | AA-763 | Close the G4 stage keys on unit-test evidence or the next natural S1 job | CIS platform | S | No change S238. | Accept unit-test evidence. |
| 35 | AA-843 | Legacy writer chain skips the guaranteed-failing acc2 call | CIS platform | S | Shipped (#754, api :626/worker :183 at 15:20 UTC 15/10). Close after 24 h Logs Insights shows 0 t1_failed_trying_t2 / t2_failed_trying_t2_5a / t1_sonnet_not_subscribed (≥16/10). |  |

## 4. Later / parked

| Issue | Work | Tier | Status / trigger | Needs Nghiệp |
|---|---|---|---|---|
| AA-680 | Customer sign-in on Cognito EXTERNAL + TP guest linking | later |  | Confirm the split and the order (staff first). |
| AA-790 | Post-repair integrity check + T9 tenant-voice rubric gate | later |  | LLM judge vs deterministic rubric. Terra voice direction. |
| AA-807 | Data Phase 1: dead-table registry (N6), owner roles (X1), shared.countries (X5), drift diff, TripPlanner migration replay CI (folded) | later |  | Split into smaller issues? Pick the owner of owners.yaml. |
| AA-804 | AI platform ADR 0009 + ledger v2 + AI Use Register; PII-on-LLM-path decision (folded) | later |  | Accept ADR 0009. Approve the ledger v2 migration. Decide DM-6.4 enforcement. |
| AA-783 | Human calibration of the T9 panel: 40 labels through the Label UI | later |  | Do the labelling. Choose the piece set. |
| AA-779 | FAQ: questions from People Also Ask + subject check | later |  |  |
| AA-789 | Gate recall tunes (openers, F15/F18/F13) | later |  |  |
| AA-787 | Drop/merge T10 gates (F8 LLM call, F3, F5, merges) | later |  | Still drop promises_an_option now that it is quiet (0/8)? |
| AA-788 | Promote F12_scope / F9_brand_style to blocking (F14 moved to AA-780) | later |  |  |
| AA-813 | Tenant users on Cognito invitations + membership contract view and PII tags (folded) | later |  | Confirm the rescope to ADR 0006 Phase 3. |
| AA-668 | Writer panel: move tour rewrite into the panel + live paid E2E | later |  | Split vs keep. Is market needed in the header? |
| AA-681 | Trip case MVP: close on the staff demo, move My Trips to AA-680 | later |  | Close decision. |
| AA-678 | Booking bootstrap: close (guard moves to AA-751) | later |  | Close by hand. |
| AA-683 | Booking UI spec close-out + /pricing/rules table at 1440 (folded) | later |  | Waive the Ms. Thư review or schedule it. Decide Q1a-f. |
| AA-829 | Restore drill + private DSN CNAME + secure the 2026-09-16 dumps + single-schema restore runbook (folded) | later |  | Edit the DSN secrets by hand. Approve deleting the local dumps. |
| AA-826 | New-app playbook tooling: owners.yaml, role bootstrap template, contract hash guard | later |  | Pick the owner of owners.yaml. |
| AA-835 | ADR 0004a supply content: contracts, Booking supply outbox/views, CIS consumer with review, read-back, entity_media | later |  | Approve creating the issue. |
| AA-837 | /plan: 7 WCAG contrast violations, Customise 404 console error, '1 DAYS' | later | Not started (frontend). | Approve creating the issue. |
| AA-838 | Wire the weekly/monthly/quarterly DB reviews into the session ritual; first capacity review | later | Not started. | Approve creating the issue. |
| AA-741 | T-series audit G7/G8 (48-tour run) re-scoped, without the Jev layer; s237 FB test-piece cleanup (folded) | later |  | Approve the re-scope and the paid G7 run (~$10-20). |
| AA-784 | Platform-wide place card build (~$15-25) | later |  | Paid run approval and country order. |
| AA-772 | Place cards: G7 list cards / thin-vs-card A/B | later |  | Is the A/B still worth paying for? |
| AA-756 | Jev A-axis recalibration leftovers (S228 decision set, record_rejected_outcome, 402s) | later |  | Answer the S228 decision set. |
| AA-803 | Calibrate a1_promise_unsupported, or switch it off | later |  | Calibrate or switch off. |
| AA-765 | Gateway refactor: judge client, T11 dispatch into acp_publish, docstrings | later |  |  |
| AA-701 | Dead-code chore: remove observe_t10 + facts.select_relevant_facts | later |  | Close as superseded after the chore. |
| AA-729 | Golden set: rewrite as a per-stage eval harness or cancel | later |  | Rewrite or cancel. |
| AA-795 | T2 judge breakdown per version + brand-claim fidelity | later |  | Still wanted? |
| AA-814 | Facts Entry API + UI | later |  | Priority relative to place cards. |
| AA-781 | F9 v2 claim rules | parked |  | Keep or park. |
| AA-782 | Cheaper T9 blog writer A/B | parked |  | Vendor rule. Paid A/B (~$1.20). |
| AA-710 | Asian Trails B2B benchmark | parked |  | Close or keep as a trigger. |
| AA-697 | Architecture diagrams | parked |  | Park. |
| AA-655 | Shared design system package | parked |  | Package vs copies + drift guard. |
| AA-671 | Marketplace redesign | parked |  | Merge with Browse Tours? |
| AA-704 | In-app AI assistant | parked |  | Keep on the roadmap? |
| AA-821 | Tenant CRM research | parked |  | When to schedule it. |
| AA-628 | Engagement feedback loop | parked |  | Park or cancel. |
| AA-839 | Erasure runbook + DRY RUN job for a traveller and an offboarded tenant | parked | Parked until ADR 0006 Phase 4 / before prod. | Approve creating it as a parked Low issue. |
| AA-841 | Plaintext tfvars untracked + gitleaks PR check | later | Code side shipped (Infra #139). Only an optional precautionary rotation remains — Nghiệp decides; can close as Done if he declines. | Optional: rotate DataForSEO password / check RDS pw reuse (precaution, nothing broken) |
| AA-842 | OTel gen_ai tracing investigation | parked | Report on Notion (Program Brain) + AA-CIS-App docs/investigations/llm-otel-tracing.md. | Decided S238: keep Backlog; build option B (gateway span, ~15–20 h) only when slow/unexplained jobs justify it |

## 5. Closed in S238

- Done: AA-830 (tour key v1.2 live, TC-000005), AA-811 (SES e-mail, inbox screenshots), AA-840 (Slate per channel), AA-634, AA-709.
- Canceled (superseded by S234 T-axis Jev off): AA-696, AA-699.
- Shipped but not yet closed (see §1/§3): AA-833, AA-843, AA-828, AA-778, AA-802, AA-831, AA-819 (evidence), AA-841 (code), AA-712 (mig 235).

## 6. Environment notes for the next session

- ECS CIS api :626 / worker :183 (image of #754); Booking :19 (bk-011); CIS migrations up to 236; TripPlanner Lambdas from #83.
- Vercel Hobby build-rate limit was hit on 15/10 — frontend merges did not deploy for 24 h; batch frontend PRs.
- Test channel credentials: Secrets Manager `aa-cis/dev/e2e-wordpress-test` (WP admin + app password), `aa-cis/dev/e2e-facebook-test` (Page token expired 15/10 19:00 — short-lived).
- Terraform full-root plan still has 16 hidden drifts (AA-806): always plan with -target and read the plan; exclude `module.rds.aws_db_instance.main`, secret versions, random_password, CloudTrail bucket policy.
- Two CIS deploys merged close together race (the earlier one fails the image-SHA check) — merge backend PRs one at a time or accept the benign failure after checking api/worker share the newer SHA.
