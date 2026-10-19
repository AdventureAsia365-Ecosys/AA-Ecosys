# Proposed replacement for docs/backlog/README.md §3, §3a and §4 (S244 master plan)

This is a proposal only. `docs/backlog/README.md` has not been edited. Once Nghiệp approves, paste these three sections over the current §3, §3a and §4, and set the "Last updated" line to S244.

The order follows the session plan in [README.md](README.md) §3. Session slots assume about one session per day and may slip.

Proposed rule for each session: 3–5 main items. An XS item whose only remaining step is closing it, with the evidence already in hand, is listed as "close-along" and does not count toward the 3–5.

## 3. Ordered work queue (next sessions)

| # | Issue | Work | Lane | Size | Status after S244 audit / next action | Needs Nghiệp |
|---|---|---|---|---|---|---|
| 1 | AA-902 | **Public-repo ID scrub, close-out.** CIS #854 and Booking #45 are merged (11:49Z / 11:44Z) and CIS Deploy Dev on `1d16adf` succeeded; live-verify CIS, Booking and TP; remove the 2 TripPlanner test-file hits (`test_embed_satellite_fallthrough.py`, `test_llm_gateway.py`); open a throwaway PR to show the red check; update `docs/security/baseline.md`. Also check that #854's edits to the applied migrations 153/240 pass the copy guard, and that Infra #221 moved the satellite IDs into the CIS task defs before the allowlist expires on 30/11 | Security | M | S244–S245. CIS #854, Booking #45, TP #105 and Infra #221 all merged by 11:50Z (gh re-check ~12:00Z) | History rewrite (recommend no); are Cognito pool/client IDs public (record an exception) or moved to config |
| 2 | AA-860 / AA-852 | **X1 wave 5:** S20 password + probe (S244), S21 mig 245 (S245), S22 `db_migrator` login + probe 246, which ends both freezes (S246), S23 close-out. Plan `docs/audits/2026-10-17-S241-x1/x1-plan.md` | Data platform | L | Infra #219 rl-002 merged + applied (S244). Infra #220 plan must be rerun (state lock). AA-852 → Done in S244 once a comment moves the 179/180 revoke to AA-847 | Approve the reworded Done-when (1); H6 task-def secret (MFA) at S22 |
| 3 | AA-816 → AA-703 | **Cognito cutover:** CIS #856 merged 11:41Z (S244); step E (C9 principal-aware admin-secret check, a CIS auth PR) and S1 on Production: legacy flag off, break-glass via managed login, clear the legacy `password_hash`, rotate `ADMIN_SECRET` in 5 places, E2E secrets → viewer account, disable `e2e-claude-code-2` (S245). The `ADMIN_SECRET` rotation restarts CIS api + worker and C9 needs a CIS deploy: run them before the 245 copy or after the 245 apply and probe, never inside the S21 window | Identity | M | Root #112 cutover plan open. The agent chose N-A..N-F | Ack N-A..N-F (especially N-B, N-D); allow the agent to edit underscore env vars/secrets, or edit them by hand |
| 4 | AA-903 | Link one Dependabot run per repo that skips "Vercel deploy"; close Booking #39 | CI | XS | CIS #855, Booking #46, TP #106 merged 11:31–11:32Z (S244) | — |
| 5 | AA-904 | TripPlanner Next 15: preview smoke of 4 flows (Mapbox map, search, /plan, send-to-advisor with a test contact), merge TP #107, prod verify | TripPlanner | S | TP #107 green; preview env vars now present | — |
| 6 | AA-846 | **Apply guard** in `terraform-apply.yml` (refuse plans that touch `aws_secretsmanager_secret_version` / `random_password` / `aws_db_instance`), exact `required_version` pin, hidden diffs, tag/zip drift, apply-role narrowing (inline policy at 9,559/10,240 characters) | Infra | M | S245. TF 1.15.5 pinned in CI (#218), `.bak` removed (#211), param group (#155) | — |
| 7 | AA-865 | Pooled F9 re-flag rate (r5–r7 retries, n≥60, $0); a fix only if above 8% | CIS content | S | S245 | — |
| 8 | AA-816 (ADR 0006a A10) | **Remove the temporary E2E staff exception** after S22: new CIS migration replacing the 250 exception, revert Infra #215, remove the CIS #849 scope, disable the user and row; retire `scripts/create_staff_user.py`; update the Done-when in the description | Identity | S | S246 | — |
| 9 | AA-680 | **Staff half close:** live evidence that a WORKFORCE user with no `booking-*` group is refused; drop the CIS bridge (`/auth/booking-token`, booking JWT key); staff Done-when. The customer half goes to a new issue | Booking / identity | S | S246 | Approve the split (new customer-identity issue) |
| 10 | AA-886 | `/privacy` + `/terms` (marked draft) on TripPlanner and the portal, linked from footers and PII forms; consent-capture query (DM-6.5) | Legal / TP | S | S246; the packet follows with AA-820 | Wording through Ms. Thư (pages ship as draft) |
| 11 | AA-800 | Tenant signature vocabulary (3 layers, per-tenant writer rule 1) | CIS content | M | S246 | <$1 live check |
| 12 | AA-729 | Golden set ~100 samples + scoring + baseline (D-23); reword Done-when line 3 | CIS eval | L | S247 | Sample/label plan and run cost |
| 13 | AA-787 | Drop/merge T10 gates, with before/after numbers on the golden set | CIS content | M | S247 | Re-confirm dropping `promises_an_option` |
| 14 | AA-845 | Jev 402 investigation (~48k in 14 days, silent rule fallback) + label-source choice; the rest in S252 | CIS / Jev | M | S247 | Label source (a) or (b) |
| 15 | AA-878 | Register drift diff = 0; confirm the 2 GitHub orphans (AA-866 says they are deleted); decision that CI smoke stays on admin; U-04 | Security | S | S247 | Revoke the PAT and the Mapbox token |
| 16 | AA-805 | Reopened false Done: the 4 open checks (narrate 429, spend cap rows, narration cache hit, inactive-tour join), ~$0.02 | TripPlanner | XS | S247 | — |
| 17 | AA-847 | **L4 catalog read model** + parity, content-validity report, defect fixes, `PLACES_SOURCE=cis` flip. Also take over the AA-852 179/180 revoke, ADR 0007 Geoapify attribution and the AA-674 property test | Places | L | S248–S249 (after S22) | 7-day watch vs "dev: no waiting" |
| 18 | AA-780 | 6 stock lines, broetry warn, hashtag place-name check; reword "r5" | CIS content | S | S248 | Trail Pulse voice fields |
| 19 | AA-779 | FAQ from People Also Ask + head-entity check; reword "r6" | CIS content | M | S248 | — |
| 20 | AA-875 | SSRF-safe `safe_http` for tenant URLs | Security | S | S248 | — |
| 21 | AA-888 | Links + ID jobs in Infra and the app repos; one red test PR; close after the first scheduled run (≥26/10) | CI / docs | S | S248, S251 | — |
| 22 | AA-790 | Tenant-voice gate + post-repair integrity (owns orphans) | CIS content | L | S249 | LLM judge vs deterministic rubric |
| 23 | AA-876 | Login rate limit (legacy and tenant), CORS, headers, Booking docs; WAF after quote | Security | M | S249 | WAF cost (D-19) |
| 24 | AA-844 | CloudFront in front of photos + daily `photo_sync` (Jira PR-11 promise, 01/10); resolve the host in the app layer to avoid a catalog view change | Photos | M | S249 | Cost line before apply |
| 25 | AA-877 | PII column tags through bk/tp migrations; RoPA input for AA-886 | Data | S | S249 | — |
| 26 | AA-741 | T-series G7 (12 tours × 4 tenants) + G8 report; exclude test rows | CIS audit | XL | S250 (after AA-787, AA-800) | Paid run ~$10–20 |
| 27 | AA-789 | Gate recall tunes, lexical part only | CIS content | M | S250 | — |
| 28 | AA-874 | Redis AUTH/TLS/at-rest + flag alarm; confirm Booking does not use Redis | Security | M | S250 | Cost (D-19) |
| 29 | AA-848 | X2 RLS catalogue CI guard (rules a–e, PUBLIC grants, allowlist incl. `cis_app` USING(true) set) | Data platform | M | S250 | — |
| 30 | (new, if approved) | pip-audit expiry: bump langchain/langgraph, drop chromadb, 3-tour regression, before 30/11 | CIS | S | S250 | Approve creating the issue |
| 31 | AA-859 | Re-plan after S22 (renumber migrations; 242–244 are taken), D5b, wave 3 | Data platform / CIS | L | S251 | Wave-4 route retire |
| 32 | AA-825 | Reopened: one real Booking retention run under a Dev override, or the Done-when line is dropped | Data | S | S251 | Drop the line or allow the run |
| 33 | AA-893 | Generated `alarms.md` + link check; step 2 outputs + `docs-gen.yml` (read-only OIDC role, IAM review) | Infra / docs | M | S251 | — |
| 34 | AA-901 → AA-891 | GitHub App (Nghiệp creates it), then release-please and first tags | Release | M + M | S251, S252 | Create the App; version numbers |
| 35 | AA-783 | Agreement analysis once Nghiệp's 40 labels exist | CIS eval | M | S251 | 2–3 h labelling |
| 36 | AA-712 + AA-905 + AA-784 | **One place pass:** a trial country for cards plus the geo backfill and a3 parity; precondition: HNSW rewrite of TP `suggestions.py` (ADR 0007) | Places | M–L + paid | S252 | Quote and country order |
| 37 | AA-803 | Calibrate or switch off `a1_promise_unsupported` (labels shared with AA-845) | CIS / Jev | M | S252 | Enforce or switch off |
| 38 | AA-849 | TP replay: apply twice, assert keys, one red run, required check | CI | S | S253 (S252 is full: the place pass is 3 issues) | Branch-protection toggle |
| 39 | AA-879 | CI gate parity across repos | CI | M | S253 | Branch-protection toggles |
| 40 | AA-896 + AA-838 + AA-665 | First cost report with unit costs (acc2 + acc3 + credits), first capacity and access review, Cost Operations page | FinOps / admin | S + M + L | First session ≥01/11 | Decision list |
| 40a | AA-839 (wording only) + N3 (if approved) | Remove the "GDPR" wording from the offboard endpoint; TripPlanner guest-token check on the read GETs | Security | XS + S | S253 | Approve creating N3 |
| 41 | AA-820 | Tenant terms AI clause | Legal | — | Jira draft at S244 end; decision by ~01/11 | Ms. Thư (counsel) |
| 42 | AA-906 → AA-837 | TripPlanner Next 16 + React Compiler refactor, then /plan contrast and labels (same files) | TripPlanner | M + S | ≥S254 | Clarify AA-837 dark mode |
| 43 | AA-855 | UAT videos for all apps; scripts use Cognito login after the cutover; bilingual guides | QA | L | After M2a | Go signal |
| 44 | AA-829 | Dumps: DRY RUN, then move or delete, in any session once approved; then the single-schema rehearsal and the DSN CNAME | Data/DR | M | In Progress (S241 drill passed) | Dumps; DSN secrets by hand |
| 45 | (no issue) | Bhutan 33 vs 32 extra S1 row | CIS data | XS | Any session | — |
| 46 | AA-682 | Booking wave 3; write the Done-when now, split at pickup | Booking | XL | Unscheduled | Payment marking, tax, deposit % |

## 3a. Platform roadmap keys (PLAT-01)

Content and status live in the [engineering handbook §9](../engineering-handbook.md#9-roadmap). This list only orders the next picks.

| Order | U-xx / key | Issue | Next step |
|---|---|---|---|
| 1 | U-09, U-11, AA-887–890 | AA-902, AA-895, AA-889, AA-887, AA-890 | AA-902 close-out (S244–S245) closes AA-889 and AA-895 along with it; AA-887 front-matter on the 4 CONTEXT.md files; AA-890 `gh api` squash-only + delete-branch settings |
| 2 | U-42 | AA-846 | Apply guard first (S245) |
| 3 | AA-888, AA-892 follow-ups | AA-888 | App/Infra link + ID jobs, red PR; per-app `docs/runbooks/deploy.md`, SES playbook, drafts → active (scope lines from AA-892) |
| 4 | AA-893 | AA-893 | `alarms.md` + docs-gen (S251) |
| 5 | U-26 + U-04 | AA-878 | Drift diff = 0 (S247); access review done once inside AA-838 |
| 6 | U-25 → AA-891 | AA-901, AA-891 | GitHub App (Nghiệp), then release-please (S251–S252) |
| 7 | AA-896, U-38 | AA-896, AA-838 | First session ≥01/11 |
| 8 | U-28 + U-61, U-44, AA-894 | AA-879, AA-899, AA-894 | CI parity (S252); OpenAPI after AA-891; env register after AA-893 |
| later | U-15, U-24, U-37, U-39, U-35, U-56 | AA-848, AA-877, AA-850, AA-851, AA-826, AA-853, AA-849, AA-881 | AA-848/AA-877/AA-849 are in §3; AA-850/AA-851 only after X1 S22; AA-826 Done-when needs rewording; AA-881 at 05/2027 |

## 4. Later / parked

| Issue | Work | Tier | Status / trigger | Needs Nghiệp |
|---|---|---|---|---|
| (new, if approved) | AA-680 customer half: traveller sign-in on Cognito EXTERNAL, TP guest linking, My Trips | M5 security order #2 | ADR 0006 Phase 4 / before real travellers | Approve creating it |
| AA-813 | Tenant users on Cognito invitations, membership view, PII tags (Jira PR-14, PR-18) | M5 security order #1 (before the first paying tenant) | Description still says password login + `acp_shared.tenant_users`; rewrite to ADR 0006 Phase 3 | Confirm the rescope; optional separate API-key rotation issue |
| AA-804 | AI platform ADR (renumber to 0009) + ledger v2 + AI Use Register; DM-6.4 decision | M5 security order #6 | Before prod | Accept the ADR; approve the ledger migration |
| AA-859 (wave 4) | subject / plans / tour_atoms RLS with keep-alive policies; route hub retire | later | After X1 S22 and wave 3 | Wave-4 route retire |
| AA-850 | Dead Table Registry + wave-1 quarantine | later | After X1 S22 (CIS freeze) | Approve the DRY RUN |
| AA-851 | `shared.countries` + `v_countries` / `v_destinations` | later | After X1 S22 (catalog freeze) | — |
| AA-826 | New-app playbook: template, contract hash guard, dry-run add-owner PR | later (In Progress) | owners.yaml shipped (Infra #163) | Reword the Done-when; owner of owners.yaml |
| AA-853 | Schema drift diff + ownership lint | later | After AA-826 | — |
| AA-873 | GuardDuty, Access Analyzer, S3 BPA, CloudTrail | M5 security order #3 (Tenant horizon) | After AA-846 | Cost per item (D-19) |
| AA-871 | JSON logs + Sentry for Booking/TP; add a Booking uptime line (AA-870 gap) | M5 security order #4 (Tenant horizon) | — | — |
| AA-861 | `tripplanner.job` + `tp_outbox_pii_redact`; fix the stale "blocked" title | M5 security order #7 | No row older than 90 d until ~01/2027; test with a seeded row | Approve the first real run |
| AA-898 | `/admin/docs` reader page; add the N-3 owner-only rule and K-15 to the Done-when | later (Tenant horizon) | — | Bucket (~0.01 USD/month) |
| AA-821 | Tenant CRM re-plan (Jira PR-19), research + phased MVP plan | later | After M1 | Approve the plan with Ms. Thư |
| AA-835 | ADR 0004a supply content (the issue exists; fix the ADR heading) | later | After X1 S22 | Paid consumer trial |
| AA-814 | Facts Entry API + UI | later | After AA-859 / AA-813 | Priority vs place cards |
| AA-795 | T2 judge breakdown + brand-claim fidelity | later | — | Still wanted? |
| AA-788 | Promote F12_scope / F9_brand_style to blocking (F14 part in AA-780) | later | After AA-787 | — |
| AA-765 | Gateway refactor + AA-799 follow-ups (check AA-882 first) | later | — | — |
| AA-900 | LLM ops docs, prompt register, manual eval gate | later | After AA-729 | — |
| AA-899, AA-894 | OpenAPI + oasdiff; env-config register + ERD | later | After AA-891 / AA-893 | — |
| AA-669 | Reopened (if agreed): My Content leftovers (columns, filters, saved views) | later | Before UAT | Rescope or build |
| AA-880 | L9 prod blueprint + ADR 0012 | later | Go-live date | Date; account (AA-864) |
| AA-864 | Research: consolidate on one AWS account | later | Decide before AA-880 | Still wanted given "prod on acc2" (S235)? |
| AA-839 | Erasure runbook + DRY RUN (the issue exists); the "GDPR" wording fix is in §3 (S253) | M5 security order #5 (before prod) | ADR 0006 Phase 4 / before prod | — |
| AA-881 | PG 15 major-upgrade rehearsal | parked | 05/2027 | — |
| AA-842 | OTel gen_ai tracing investigation | parked | Decided S238: keep Backlog; build option B only on a trigger | — |
| AA-781 | F9 v2 claim rules | parked | — | Keep or park (cancel only on your call) |
| AA-782 | Cheaper T9 blog writer A/B | parked | — | Vendor rule; ~$1.20 |
| AA-628 | Engagement feedback loop | parked | Real publish volume | Park or cancel |
| AA-704 | In-app AI assistant | parked | AA-703 phases 1 and 3 | Keep on the roadmap? |
| AA-710 | Asian Trails B2B benchmark (KAN-20) | parked | B2B design start | Close or keep as a trigger |
| AA-697 | Architecture diagrams | parked | After M1 | Scope (network.md / access-matrix.md here or in docs issues) |
| AA-655 | Shared design system package | parked | — | Package vs copies |
| AA-671 | Marketplace redesign | parked | — | Merge with Browse Tours? (Ms. Thư) |

"M5 security order #n" is the order in [README.md](README.md) §3 "Sau S253" for the items that must land before the first paying tenant or before prod; take 1–2 per session from ≥S254.

Rows removed from the current §4:

- **Already Done:** AA-807, closed 16/10 and split into AA-849…AA-853.
- **Moved up into §3:** AA-783, AA-779, AA-789, AA-787, AA-741, AA-784, AA-803, AA-790, AA-680 (staff half), AA-837, AA-838.
- **Wording fixed:** AA-835, AA-837, AA-838 and AA-839 are listed as existing issues. They no longer say "Approve creating the issue".
