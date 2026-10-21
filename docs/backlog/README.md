# AA_Ecosys living backlog (ordered work queue)

**Purpose:** the single ordered list of what to do next, so a session starts here instead of re-auditing Linear. Built from the S238 full audit (69 open issues + data standards + logs + code + Jira, `docs/audits/2026-10-15-S238-backlog-audit/`) and updated at the end of every session since.

**HTML view:** [tracker/](tracker/README.md) — the same plan as a filterable page (private artifact <https://claude.ai/artifact/Q4LvqJyX5wsqRgZZQ75aoF>); update `tracker/plan.json` in the same PR as this file.

**Rules:** at session start read §1–§3 and pick 3–5 items from §3 top-down (skip items blocked in §2). At session end update the Status column, move closed items to §5, add new items. Re-audit only when this file is older than ~2 weeks or many issues were created outside sessions.

_Last updated: S245, 20/10/2026 (Claude Code). 19 issues closed (list in §5). The queue now starts with the quality work approved in S245: Quality System v1 (D1–D11, `docs/audits/2026-10-20-S245-quality-system/`) and Writing Memory v1 (D1–D16, E1–E4, `docs/audits/2026-10-20-S245-writing-learning-loop/`). The rest of §3/§3a/§4 still follows the S244 master plan audit, `docs/audits/2026-10-19-S244-master-plan/`._

## 1. Time-gated checks (do these first when due)

| Due | Issue | Check |
|---|---|---|
| next frontend Dependabot PR | AA-903 | "Vercel deploy" shows skipped; link it and close AA-903. |
| daily 06:15 UTC | AA-816 | Ops probe enqueues `staff_directory_reconcile` (Infra #195). Check one job per UTC day in `shared.job` and its drift report (Cognito groups vs `staff_app_grant`). |
| daily 22:00 UTC | AA-869 | Snapshot expiry Lambda `aa-cis-dev-rds-snapshot-expiry` runs live (deletes manual snapshots > 30 d unless `keep-` / `aa:retain*`). An SNS mail only when it deletes, caps, finds a malformed tag or an orphan. |
| ≥01/11 | (cost) / AA-896 | Infra cost audit Aug/Sep/Oct 2026 per `App` tag and service (acc2) + acc3 Bedrock + AWS Lift credits. The numbers feed the Jira platform report period 2 (PR-20 Epic; period 1 PR-21 carried no amounts). |
| ~02/11 | (Jira) PR-20 | Platform report period 2 (biweekly Story under Epic PR-20): draft → Nghiệp approves → post. |
| ≤11/11 | AA-820 | Tenant terms AI clause — Ms. Thư decides whether counsel is needed. |
| ~mid-Nov | AA-862 follow-up | Re-request acc2 quotas in small steps (Cohere 20 → 100 rpm). |
| 18/11 | AA-878 (Done) | The 4 orphan secrets deleted 19/10 (`aa-cis/dev/api-keys`, `aa-cis/dev/acp-webhook-secret`, `aa-cis/dev/acp-partner-api`, `tripplanner/dev/mapbox-geocoding-token`) leave the recovery window. Nothing to do unless one must be restored before then (`restore-secret`). |
| **before prod** | chore (security) | Rotate the GitHub OAuth token and the RDS master password (printed into the local S240 transcript; D-02/D-03: keep until prod). |

## 2. Waiting on Nghiệp (decisions / manual steps)

- **CRM (AA-821):** approve the 16 CRM recommendations (artifact 5srRKGxXrdiADV6u13niAH, <https://claude.ai/artifact/5srRKGxXrdiADV6u13niAH>). The next CRM design version starts only after this; no Jira PR-19 reply before it is done.
- **TasteWP test site:** revoke the AA portal e2e application password on the TasteWP test site when no longer needed (the value was shown in the S245 transcript).
- CRM v2.1 / v2.2 pages and Ms. Thư's question form: Nghiệp and Ms. Thư review when free.
- Access review 2026-Q4 (`docs/audits/2026-10-20-S245-access-review/`): Q-1 (Ms. Thư `cis-admin` or `cis-reviewer`), Q-2 (narrow 4 GitHub Apps, turn off "members can create repositories"); owner OK to delete the orphan IAM user `s226-should-fail` (AA-878 finding 2).
- **Break-glass TOTP:** add the NEW `totp_seed` (rotated S244) from Secrets Manager `aa-identity/dev/breakglass` to an authenticator app, if wanted.
- **Ms. Thư's first admin login** (invite sent 18/10; Google cleared the Chrome warning 19/10). Optional: Nghiệp dropped it from AA-858 Done-when (S243).
- **AA-816 cutover call:** API-side `LEGACY_ADMIN_LOGIN_ENABLED` also serves Preview (ADR 0006a A6); S2 waits for a Preview sign-in (AA-911).
- AA-855 UAT videos: when Nghiệp says (after the tech work). Product questions from S238: T2 day separator; "— N Days" vs ", N Days".
- AA-829: approve deleting/securing the 2026-09-16 real-data dumps; DSN CNAME secrets are edited by hand.
- Paid place-pipeline geo backfill for the 8 countries without a geo graph (AA-905, §3): quote first, then approve or keep parked.
- Done in S245: the local GitHub OAuth token (`gho_`) rotated and the old Mapbox geocoding token revoked (20/10, secrets register); TripPlanner required check `Migrations (lint, PG 15 replay)` turned on (AA-849).

## 3. Ordered work queue (next sessions)

Rows 1–10 come from S245 (Quality System v1 D9/D10, Writing Memory P0, the session log's order for S246). From row 11 on the order and slots are the S244 master plan (`docs/audits/2026-10-19-S244-master-plan/`); the quality block takes about S246–S247, so those slots move back by about one session. Rule per session: 3–5 main items, close-along XS items do not count. Writing Memory P1–P3 (AA-917…AA-923) are in §4.

| # | Issue | Work | Lane | Size | Status / next action | Needs Nghiệp |
|---|---|---|---|---|---|---|
| 1 | AA-925 → AA-729 | **Q-2** (D9: first): repair contract, AA-740 fitter fix, `degraded[]` counters, S1 day-count oracle (run on ~900 tours), compact Q0 corpus. It is the first change measured before/after on golden fixture 1.1.0, so it also closes AA-729 | CIS quality | M | S246. AA-729 In Progress: fixture 1.1.0 (100/100 labelled) + baseline done S245 | — |
| 2 | AA-779 | **D10:** stop patching rules. Build a ~150–200 real PAA question set labelled keep/drop, plus the trap questions the reviewers found (`.tmp-session/aa779-review.json`, `.tmp-session/aa779-fix-r2.json`); panel labels, Nghiệp approves; measure 3 options (`main`, the local rules branch `fix/real-questions-scope-variants` at 1a7a73b3, not pushed, and a small LLM classifier); fix once by the numbers | CIS content | M | In Progress (#877, #882 merged); S246 | Approve the labelled set |
| 3 | AA-926 | **Q-1:** error taxonomy, gate registry, one thresholds file, lint | CIS quality | M | S246–S247 | — |
| 4 | AA-915 | **Writing Memory P0:** freeze the ungated `pipeline_lessons` loop behind a flag + app ADR 0010 (governed writing memory) | CIS quality | S | S247 | — |
| 5 | AA-916 | **Writing Memory P0:** capture writing signals (`shared.writing_signal`, reason codes, every T9 attempt) + Q-3 `quality_context` stamp for A1/T9 | CIS quality | M | S247 (migration + RLS: agent review) | — |
| 6 | AA-927 | LLM calls with no `llm_call_log` row (AA-729 eval runs: 116/216 and 188/815) | CIS / cost | S | S247 | — |
| 7 | AA-780 | Panel-label the 15 rewritten LinkedIn posts (run dab254c4), then close or adjust; the 120-word floor shipped (#881), baseline 15/15 ≥ 152 words | CIS content | S | In Progress; S247 | — |
| 8 | AA-845 | Panel labels for 100 claims, pick the reject ceiling (with the golden-set Jev S1 agreement of 12.5%), investigate the 402s | CIS / Jev | M | In Progress; S247 | — |
| 9 | AA-821 | **CRM next design version** after the 16 recommendations are approved: screen flows + wireframes after the easy parts of Tern and TravelJoy, data model, cost, issue split; Nghiệp approves it, then the neutral questionnaire for Ms. Thư. No Jira PR-19 reply before it is done | Portal / CRM | L | In Progress; after the §2 approval | Approve the 16 recommendations, then the design |
| 10 | AA-924 | Severity per violation in the gate ledger, then merge F15_voice_warn → F15 and F2 variants + stock list → one lexicon gate (moved from AA-787) | CIS content | M | After AA-926 | — |
| 11 | AA-816 → AA-703 | **Cognito cutover, rest:** N-F disable `e2e-claude-code-2` (owner session on the Staff page); S2 (API legacy flag off) once a Preview sign-in exists (AA-911); A10 (row 8) | Identity | S | **S244 done:** CIS #856 sign-out, break-glass managed-login test + `password_hash` cleared (Infra #224) + rotation, **S1** Production legacy login off (Vercel flag; `POST /api/auth/login` 404), **C9** CIS #858 + Preview credential (viewer), E2E smoke on the viewer account (#859), **I6** admin secret rotated. Report: root `docs/audits/2026-10-19-S244-aa816-cutover/` | — (N-F done S244) |
| 12 | AA-816 (ADR 0006a A10) | **Remove the temporary E2E staff exception:** new CIS migration replacing the 250 exception, revert Infra #215, remove the CIS #849 scope, disable the user and row; update the Done-when | Identity | S | Unblocked (S22 done, freeze over). `create_staff_user.py` already retired (CIS #858) | — |
| 13 | AA-911 | **Preview staff sign-in** for Booking (and CIS), then retire the CIS → Booking bridge (`/auth/booking-token`, booking JWT key) and the 3 bridge-era `booking.staff_users` rows; unblocks AA-816 S2 | Identity | M | New S245 (AA-680 staff half Done; owner kept the bridge until Previews can sign in) | Pick the Preview sign-in option (ADR 0006a amendment) |
| 14 | AA-903 | Close on the next Dependabot PR that touches `frontend/**` (link the skipped "Vercel deploy") | CI | XS | CIS #855, Booking #46, TP #106 merged (S244); Booking #39 closed; TP #109 was backend-only | — |
| 15 | AA-886 | `/privacy` + `/terms` (marked draft) on TripPlanner and the portal, linked from footers and PII forms; consent-capture query (DM-6.5) | Legal / TP | S | S246; the packet follows with AA-820 | Wording through Ms. Thư (pages ship as draft) |
| 16 | AA-847 | **L4 catalog read model** + parity, content-validity report, defect fixes, `PLACES_SOURCE=cis` flip. Also take over the AA-852 179/180 revoke, ADR 0007 Geoapify attribution and the AA-674 property test | Places | L | S248–S249 (after S22) | 7-day watch vs "dev: no waiting" |
| 17 | AA-790 | Tenant-voice gate + post-repair integrity (owns orphans) | CIS content | L | S249 | LLM judge vs deterministic rubric |
| 18 | AA-876 | Login rate limit (legacy and tenant), CORS, headers, Booking docs; WAF after quote | Security | M | S249 | WAF cost (D-19) |
| 19 | AA-844 | CloudFront in front of photos + daily `photo_sync` (Jira PR-11 promise, 01/10); resolve the host in the app layer to avoid a catalog view change | Photos | M | S249 | Cost line before apply |
| 20 | AA-877 | PII column tags through bk/tp migrations; RoPA input for AA-886 | Data | S | S249 | — |
| 21 | AA-741 | T-series G7 (12 tours × 4 tenants) + G8 report; exclude test rows | CIS audit | XL | S250 (AA-787, AA-800 Done S245) | Paid run ~$10–20 |
| 22 | AA-789 | Gate recall tunes, lexical part only | CIS content | M | S250 | — |
| 23 | AA-874 | Redis AUTH/TLS/at-rest + flag alarm; confirm Booking does not use Redis | Security | M | S250 | Cost (D-19) |
| 24 | AA-848 | X2 RLS catalogue CI guard (rules a–e, PUBLIC grants, allowlist incl. `cis_app` USING(true) set) | Data platform | M | S250 | — |
| 25 | AA-859 | Re-plan after S22 (renumber migrations; 242–244 are taken), D5b, wave 3 | Data platform / CIS | L | S251 | Wave-4 route retire |
| 26 | AA-825 | Reopened: one real Booking retention run under a Dev override, or the Done-when line is dropped | Data | S | S251 | Drop the line or allow the run |
| 27 | AA-901 → AA-891 | GitHub App (Nghiệp creates it), then release-please and first tags | Release | M + M | S251, S252 | Create the App; version numbers |
| 28 | AA-783 | Agreement analysis once Nghiệp's 40 labels exist | CIS eval | M | S251 | 2–3 h labelling |
| 29 | AA-712 + AA-905 + AA-784 | **One place pass:** a trial country for cards plus the geo backfill and a3 parity; precondition: HNSW rewrite of TP `suggestions.py` (ADR 0007) | Places | M–L + paid | S252 | Quote and country order |
| 30 | AA-803 | Calibrate or switch off `a1_promise_unsupported` (labels shared with AA-845) | CIS / Jev | M | S252 | Enforce or switch off |
| 31 | AA-879 | CI gate parity across repos | CI | M | S253 | Branch-protection toggles |
| 32 | AA-896 + AA-838 + AA-665 | First cost report with unit costs (acc2 + acc3 + credits), first capacity review (the first access review ran in S245, AA-878), Cost Operations page | FinOps / admin | S + M + L | First session ≥01/11 | Decision list |
| 33 | AA-839 (wording only) + AA-909 | Remove the "GDPR" wording from the offboard endpoint; TripPlanner guest-token check on the read GETs | Security | XS + S | S253 | — |
| 34 | AA-820 | Tenant terms AI clause | Legal | — | Jira draft at S244 end; decision by ~01/11 | Ms. Thư (counsel) |
| 35 | AA-906 → AA-837 | TripPlanner Next 16 + React Compiler refactor, then /plan contrast and labels (same files) | TripPlanner | M + S | ≥S254 | Clarify AA-837 dark mode |
| 36 | AA-855 | UAT videos for all apps; scripts use Cognito login after the cutover; bilingual guides | QA | L | After M2a | Go signal |
| 37 | AA-829 | Dumps: DRY RUN, then move or delete, in any session once approved; then the single-schema rehearsal and the DSN CNAME | Data/DR | M | In Progress (S241 drill passed) | Dumps; DSN secrets by hand |
| 38 | AA-682 | Booking wave 3; write the Done-when now, split at pickup | Booking | XL | Unscheduled | Payment marking, tax, deposit % |

## 3a. Platform roadmap keys (PLAT-01)

Content and status live in the [engineering handbook §9](../engineering-handbook.md#9-roadmap). This list only orders the next picks.

| Order | U-xx / key | Issue | Next step |
|---|---|---|---|
| 1 | U-09, U-11, AA-887–890 | AA-889, AA-890 | AA-902, AA-895, AA-887 Done (S244–S245); left: AA-889 stale docs/instruction drift, AA-890 `gh api` squash-only + delete-branch settings |
| 2 | U-42 | AA-846 | Done S245 (apply guard, exact pin, hidden drift, apply-role narrowing) |
| 3 | AA-888, AA-892 follow-ups | AA-888 | AA-888 Done S245 (docs lint in every repo, red evidence). Owner option: "Docs lint" as a required check on Booking / TripPlanner main |
| 4 | AA-893 | AA-893 | Done S245 (generated `alarms.md` + outputs, Infra #244) |
| 5 | U-26 + U-04 | AA-878 | Done S245 (drift diff = 0, first access review); its open findings: §2 |
| 6 | U-25 → AA-891 | AA-901, AA-891 | GitHub App (Nghiệp), then release-please (S251–S252) |
| 7 | AA-896, U-38 | AA-896, AA-838 | First session ≥01/11 |
| 8 | U-28 + U-61, U-44, AA-894 | AA-879, AA-899, AA-894 | CI parity (S252); OpenAPI after AA-891; env register (AA-893 is Done) |
| later | U-15, U-24, U-37, U-39, U-35, U-56 | AA-848, AA-877, AA-850, AA-851, AA-853, AA-881 | AA-848/AA-877 are in §3; AA-850/AA-851 unblocked since X1 S22; AA-826 and AA-849 Done S245, so AA-853 can start; AA-881 at 05/2027 |

## 4. Later / parked

| Issue | Work | Tier | Status / trigger | Needs Nghiệp |
|---|---|---|---|---|
| AA-917 | Writing Memory P1: rule store + mining job (scoped rules, fact filter, cheaper drafter) | Quality System P1 | After AA-915/AA-916 | Release click per rule set (D6a) |
| AA-918 | Writing Memory P1: R0 replay engine ($0, also the post-merge R0 job of Q-5) + L0 lexicon fast path | Quality System P1 | After AA-916 | — |
| AA-919 | Writing Memory P2: eval and release gate (golden set, R2 runner, targeted shadow, Releases tab; Q-6 calibration, κ ≥ 0.6) | Quality System P2 | After AA-918; budget $40/month, $10 per run (D3) | Each release |
| AA-920 | Writing Memory P2: inject approved rules into the four writers + post-activation check | Quality System P2 | After AA-919 | — |
| AA-921 | Writing Memory P3: pinned example sets + tenant preference summaries | Quality System P3 | After AA-920 | — |
| AA-922 | Writing Memory P3: weekly KPIs, soft-stop rollback, disagreement queue (+ Q-8 scorer learning) | Quality System P3 | After AA-920 | — |
| AA-923 | Writing Memory P3: labels for T2/A1, offboarding deletion, retire the old lesson paths | Quality System P3 | After AA-920 | — |
| AA-908 | AA-680 customer half: traveller sign-in on Cognito EXTERNAL, TP guest linking, My Trips | M5 security order #2 | ADR 0006 Phase 4 / before real travellers | — |
| AA-910 | Booking staff admin at 1440 px (table overflow, FX wrap, scrollbar) + audit rows for room type / rate | later (M3) | With the next Booking UI pass | — |
| AA-813 | Tenant users on Cognito invitations, membership view, PII tags (Jira PR-14, PR-18) | M5 security order #1 (before the first paying tenant) | Description still says password login + `acp_shared.tenant_users`; rewrite to ADR 0006 Phase 3 | Confirm the rescope; optional separate API-key rotation issue |
| AA-804 | AI platform ADR (renumber to 0009) + ledger v2 + AI Use Register; DM-6.4 decision | M5 security order #6 | Before prod | Accept the ADR; approve the ledger migration |
| AA-859 (wave 4) | subject / plans / tour_atoms RLS with keep-alive policies; route hub retire | later | After X1 S22 and wave 3 | Wave-4 route retire |
| AA-850 | Dead Table Registry + wave-1 quarantine | later | X1 S22 done (freeze over) | Approve the DRY RUN |
| AA-851 | `shared.countries` + `v_countries` / `v_destinations` | later | X1 S22 done (freeze over) | — |
| AA-853 | Schema drift diff + ownership lint | later | AA-826 Done S245: can start | — |
| AA-873 | GuardDuty, Access Analyzer, S3 BPA, CloudTrail | M5 security order #3 (Tenant horizon) | AA-846 Done S245: can start | Cost per item (D-19) |
| AA-871 | JSON logs + Sentry for Booking/TP; add a Booking uptime line (AA-870 gap) | M5 security order #4 (Tenant horizon) | — | — |
| AA-861 | `tripplanner.job` + `tp_outbox_pii_redact`; fix the stale "blocked" title | M5 security order #7 | No row older than 90 d until ~01/2027; test with a seeded row | Approve the first real run |
| AA-898 | `/admin/docs` reader page; add the N-3 owner-only rule and K-15 to the Done-when | later (Tenant horizon) | — | Bucket (~0.01 USD/month) |
| AA-835 | ADR 0004a supply content (the issue exists; fix the ADR heading) | later | After X1 S22 | Paid consumer trial |
| AA-814 | Facts Entry API + UI | later | After AA-859 / AA-813 | Priority vs place cards |
| AA-795 | T2 judge breakdown + brand-claim fidelity | later | — | Still wanted? |
| AA-788 | Promote F12_scope / F9_brand_style to blocking (F14 part in AA-780) | later | AA-787 Done S245; after AA-924 | — |
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

## 5. Closed in S245

Evidence per issue: `docs/linear-export/` (closed issues exported, then archived) and the S245 session log.

- **Quality / content:** **AA-800** (tenant signature words, CIS #875), **AA-865** (r8: 0/28 errors from retries, pooled F9 6.2%), **AA-787** (T10 gates 31 → 26, CIS #878; F15 / lexicon merges moved to AA-924), **AA-914** (route guard: no Segments from another country, CIS #879).
- **Security / platform:** **AA-912** (CodeQL CIS 31 → 0: 13 regexes rewritten linear with fuzz + time-bound tests, shared citation tags, 5 stack-trace leaks closed; CIS #885, deploy da07b7db), **AA-913** (alert recipients managed on an admin page, mig 251, CIS #872–#874, Infra #237), **AA-875** (`safe_http`, CIS #880; blocked case 422 + log, positive case on terra-family connect → publish → trash → disconnect), **AA-846** (Terraform apply guard, exact pin, hidden drift, apply-role narrowing), **AA-878** (secrets register drift diff = 0, first access review), **AA-907** (pip-audit ignores gone: langchain / langgraph bumped, chromadb dropped), **AA-895** (security baseline + vulnerability policy), **AA-860** (X1 close-out).
- **Docs / CI:** **AA-888** (docs lint in every repo), **AA-887** (documentation standard, front-matter on the 4 CONTEXT.md), **AA-893** (generated alarm catalog + Terraform outputs, Infra #244), **AA-826** (new-app playbook + contract hash guard, Infra #241), **AA-849** (TripPlanner migration replay; Nghiệp turned on the required check).
- **Apps:** **AA-805** (TripPlanner AI Phase 0, the 4 reopened checks pass live), **AA-680** (staff half: WORKFORCE user with no `booking-*` group refused live; bridge retirement → AA-911).
- Shipped, still In Progress: **AA-729** (golden fixture 1.1.0, 100/100 labelled; baseline `docs/audits/2026-10-20-S245-aa729-baseline/`: S1 missed 26/44 bad pieces, T9 held 12 good ones, judge/gate vs label disagreement 43.6%), **AA-779** (#877, #882; rule loop stopped per D10), **AA-780** (120-word floor, #881), **AA-845**, **AA-821** (CRM v2–v2.2, Tern / TravelJoy teardown from public sources, 16 recommendations).
- New in S245: **AA-911** (Preview staff sign-in, bridge retirement), **AA-912–AA-914**, **AA-915–AA-923** (Writing Memory v1), **AA-924** (from AA-787), **AA-925** (Q-2), **AA-926** (Q-1), **AA-927** (LLM calls without a log row).
- Tools: `tools/linear/linear_export.py` exports closed issues to `docs/linear-export/` and archives them through the API (Linear Free plan, no upgrade); secret `aa-ecosys/ops/linear-api-key`.

## 5a. Closed in S244

- **AA-904 Done** (TP Next 15.5.28 / React 19, TP #107; preview smoke 4 flows desktop + 390 px, prod verified, `npm audit --omit=dev` 0).
- **AA-902** Done on the S244 root PR merge (0 real account IDs on main of the 3 public repos; CI probe PRs CIS #857 / Booking #47 / TP #108 red as intended; baseline row in place).
- **X1 S20–S22** shipped (see §3 row 2); **AA-816 S1, C9, I6** shipped (see §3 row 3).
- Bhutan 33 vs 32 fixed: funnel stages count only active raw tours (CIS #852; live 32/32/32/32).
- Chore: Terraform `use_lockfile` + CI Terraform 1.15.5 (Infra #218).
- TP #109 (pytest 9 + pytest-asyncio 1.4.0) merged.
- Reopened as false Done (S244 audit, verified): AA-825, AA-805, AA-665, AA-669. New: AA-906 (TP Next 16).
- Audit proposals approved by Nghiệp and applied in Linear: **AA-852 Done** (X1 S1–S22 evidence; 179/180 revoke moved to AA-847), **AA-675 / AA-689 Canceled** (superseded), new **AA-907** (pip-audit expiry, High), **AA-908** (AA-680 customer half), **AA-909** (TP guest-token check on GETs), **AA-910** (Booking 1440 UI + audit rows); priority up AA-901 / AA-875 / AA-876; In Progress moves per the audit.
- N-F: `e2e-claude-code-2` disabled on the Staff page (Nghiệp, verified S244). Root #117 merged (data standards v1.2, XD3 exception row).
- Jira PR-14: same-day comment 10485 extended with the S244 cutover bullets + login screenshot (Nghiệp approved).
- Master plan HTML tracker: `docs/backlog/tracker/` (artifact <https://claude.ai/artifact/Q4LvqJyX5wsqRgZZQ75aoF>).

## 5b. Closed in S243

- **AA-885 Done** (tenant portal on its own Vercel project `aa-cis-portal`, `portal.lumiguides.it.com`; CIS #832, Infra #197; prod smoke 24/24).
- **AA-892 Done** (ops runbooks/playbooks in root #105; every runbook either active with `last_tested` evidence or draft with the UNTESTED banner; alarm links Infra #213).
- **AA-858 Done** (CIS #839/#840/#848/#850/#851, Booking #37, TP #98, Infra #205/#206/#214): live 19/10, 71/71 number source tooltips, screenshots 1440/390; Ms. Thư's confirmation dropped by Nghiệp.
- **AA-884 Done** (CIS #835–#838/#844/#848, Infra #208/#209): Apps SHA 411e5f18 = api:703/worker:260 images; audit UPDATE/DELETE → 42501 as cis_app (rolled back); cost per day = Cost Explorer by App tag for 01–17/10 (18/10 gap = snapshot before AWS finished posting).
- **AA-897 Done** (root #105 + #108): fresh-agent onboarding walkthrough to a lint-clean PR; 2 guide gaps fixed.
- **Infra #217:** denied secret reads have their own alert ("Denied secret access", rule `aa-identity-dev-denied-secret-read`); the break-glass alert now fires only for calls that name the break-glass secret (tested live 09:39Z: new rule 1, break-glass 0).
- Shipped, still In Progress: **AA-680** staff half (Booking #34/#35/#36, Infra #199), **AA-878** (root #101, CIS #841, Infra #195/#207, TP #99, 4 orphan secrets deleted).
- **AA-816:** Cognito E2E (CIS #842, Infra #198) + temporary E2E staff exception (CIS #849 mig 250, Infra #215/#216, root #106 ADR 0006a A10); break-glass OTP probe (Infra #196); daily reconcile trigger (Infra #195). Cutover still open.
- **AA-860 / AA-852:** X1 S15–S19 (CIS #833/#834/#843/#845, Infra #200/#201/#202/#203/#204/#214, root #99/#100).
- Chore row closed: stale Terraform `import` blocks removed (Infra #195), `middleware.ts` → `proxy.ts` (CIS #831); `use_lockfile` stays as row 10.
- Docs: unified engineering handbook, role guides (bilingual), runbooks, data standards v1.1 (root #105); schema reference regenerated (root #102/#103/#104). PR templates + title checks in all repos; Dependabot config in Booking (#43) and TripPlanner (#101); Dependabot PRs merged: Booking #38/#40/#44, TP #102 (open: Booking #39 superseded by #40, TP #104 → §3 row 5).
- Jira: Epic PR-20 + Story PR-21 (platform report period 1) posted. Google Safe Browsing review of lumiguides.it.com passed (19/10): the §1 check is removed.
- New Linear issues (Nghiệp approved S243): **AA-902** public-repo account ID/ARN scrub (High), **AA-903** skip Vercel deploy for Dependabot, **AA-904** TripPlanner Next 15, **AA-905** geo backfill (paid, quote first). CIS logout → Cognito `/logout` stays a scope line of AA-816; Bhutan 33 vs 32 stays §3 row 13.

## 5c. Closed in S242

- **AA-854 Done** (Cognito Phase 0: break-glass, email-code spike, no-group deny, self sign-up rejected; evidence `docs/audits/2026-10-18-S242-cognito-phase1/`).
- **AA-816** shipped (In Progress until cutover): Infra #183/#184/#185/#191/#194, CIS #807/#808/#809/#810/#811/#812/#813/#826/#827/#828/#829, mig 247.
- **AA-852** X1 S9–S14 shipped (Booking #33, TP #97, root #95, Infra #179/#180/#182/#187/#188/#189/#190).
- Dependabot cleared in all repos (CIS #814/#819/#820/#830, Infra #192/#193 — AWS provider 6.69.1); CIS `dependabot.yml` groups security updates.
- AA-869 confirmed Done (S241). New issue: none.

## 5d. Closed in S241

- Done with live evidence: **AA-883** (console 2 sections + Staff), **AA-882** (server-side staff authz), **AA-836**, **AA-863**, **AA-834**,
  **AA-866** (main-only OIDC trust), **AA-867** (GitHub security, org 2FA, AA-ACP-App deleted), **AA-868** (CI hardening),
  **AA-870** (Sentry backend, API GW alarms, uptime CIS), **AA-872** (OK e-mails, retention).
- Done on merge of the S241 root PR: **AA-751** (X6 second wave; R1 docs in that PR), **AA-869** (runbook + incident page).
- In Progress with shipped waves: **AA-852** (X1 S1–S8), **AA-854** (Cognito Phase 0), **AA-859**.
- Also shipped without an issue: Vercel admin pollers, CI-created Vercel deploys (3 repos), admin secret rotation (5 places),
  admin GET authz hotfix + route-auth CI guard, tenant pool fail-closed (D-12), ECS Exec session logging + RDS connection logs (D-07/D-08),
  restore drill (D-10, comment on AA-829), root repo private (D-14).
- New in S241: AA-866…AA-886 (25 issues from the SDLC review + admin console advice); AA-729 rewritten.

## 6. Environment notes for the next session

- ECS CIS api **:730** / worker **:287** (after CIS #885, merge da07b7db, S245); Booking api **:33** (`91812e7e`, as of S244); CIS migrations up to **251** (AA-913, S245); Booking bk-017; TripPlanner tp-015; roles **rl-002**. Terraform: **1.15.5** pinned exactly, S3 `use_lockfile` only (DynamoDB lock table removed S245, AA-846); AWS provider 6.69.1.
- **DB access after X1 S22:** CIS objects are owned by `cis_owner` (NOLOGIN); runtime `cis_app`; DB Migrate, Schema Dump and the probe log in as `db_migrator` (limit 5) and switch to the live owner (`cis_owner` / `bk_owner` / `tp_owner`); the master `aa-cis/dev/rds` is read only inside the migrator task for `roles/`, `set-password` and `run-script`. ECS exec scripts still use the container `DATABASE_URL` (`cis_app`). Catalog views: the S22 recipe (`GRANT CREATE ON SCHEMA catalog TO catalog_owner; SET LOCAL ROLE catalog_owner; …; SET LOCAL ROLE cis_owner; REVOKE …`, never `RESET ROLE`).
- **Identity:** staff sign-in = https://staff-auth.lumiguides.it.com for CIS and Booking. **Production CIS has no password login any more** (Vercel `LEGACY_ADMIN_LOGIN_ENABLED=false`, S244 S1); Preview keeps it, but Preview's `ADMIN_SECRET` is the viewer-capped `aa-cis/dev/admin-secret-preview` (C9), and GitHub `E2E_ADMIN_*` is the viewer account, so preview smoke runs in viewer mode. The API legacy flag stays on until S2. Break-glass `admin@adventure.asia` disabled, password + TOTP rotated S244 (secret `aa-identity/dev/breakglass`). Main `aa-cis/dev/admin-secret` rotated S244 (copies: GitHub CIS env dev, Vercel Production). Agents verifying admin UI on production must use a Cognito session (no `e2e-claude-code` password login there).
- **Portal:** tenant portal = Vercel project `aa-cis-portal` on https://portal.lumiguides.it.com; admin stays on aa-cis.lumiguides.it.com.
- **Network (X1 S11–S14):** one SG per caller; RDS admits tp-lambda, booking-api, cis-api, cis-worker, db-migrate; Redis/EFS only cis-api + cis-worker. DB Migrate / Schema Dump / probe run on a temporary `aa-cis-dev-db-migrate` revision (still the master login until S22); modes `set-password:<role>` and `run-script:db/scripts/*.py`.
- **X1:** Booking/TripPlanner objects owned by `bk_owner` / `tp_owner` (NOLOGIN). DB Migrate reads the LIVE owner of `anchor_schema` and runs each file as that role (`owners.yaml`). Probe workflow `db-isolation-probe.yml` (schedule + after each apply). The `migration` input carries the owner prefix (`cis/250_x.sql`).
- **OIDC:** `aa-cis-dev-app-deploy` and `aa-cis-infra-tf-apply` trust only `ref = refs/heads/main`. CIS env `dev` allows only `main`; `ADMIN_SECRET` is an env secret. Bootstrap roles/policies are applied by hand with the MFA admin profile.
- **ECR CIS IMMUTABLE**, lifecycle 30 `dev-*` + untagged 7 d; Deploy Dev reuses an existing `dev-<sha>`. Rollback runbook: `skill/aa-ship` §5.
- **Alarms** e-mail on ALARM and OK (D-20), each with a runbook link (Infra #213). Cost anomaly subscription (IMMEDIATE, ≥ $5) to the alerts topic. New S243: `cis_app` connection-limit alarm (SQLSTATE 53300), AdminCreateUser-with-password alarm.
- **Sentry:** CIS backend → project `aa-cis-api` (secret `aa-cis/dev/sentry-dsn-api`), frontend → `aa-cis-frontend`; uptime monitor for CIS `/health` (free plan: 1 monitor).
- **Vercel:** Git integration off; `vercel-deploy.yml` creates deploys only when `frontend/**` changes (`VERCEL_TOKEN` per repo; Dependabot runs have no token, so that job is red on Dependabot PRs).
- **GitHub:** rulesets "no force-push / no deletion" on the 3 public repos; Dependabot in all repos (grouped security updates, actions weekly); PR template + title check + ADR index in all repos; CodeQL default setup.
- Tenant pool flags fail closed: unreadable flag = tenant pool; explicit `"false"` = admin pool (`TENANT_POOL_FORCE_ADMIN_FLAGS` env for an emergency).
