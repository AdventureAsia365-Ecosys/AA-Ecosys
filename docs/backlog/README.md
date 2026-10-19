# AA_Ecosys living backlog (ordered work queue)

**Purpose:** the single ordered list of what to do next, so a session starts here instead of re-auditing Linear. Built from the S238 full audit (69 open issues + data standards + logs + code + Jira, `docs/audits/2026-10-15-S238-backlog-audit/`) and updated at the end of every session since.

**Rules:** at session start read §1–§3 and pick 3–5 items from §3 top-down (skip items blocked in §2). At session end update the Status column, move closed items to §5, add new items. Re-audit only when this file is older than ~2 weeks or many issues were created outside sessions.

_Last updated: S244, 19/10/2026 (Claude Code). The platform block is nearly closed: X1 finished (S20–S22), AA-816 S1 cutover on Production done. §3/§3a/§4 come from the S244 master plan audit (84 open issues, all 4 projects), `docs/audits/2026-10-19-S244-master-plan/`._

## 1. Time-gated checks (do these first when due)

| Due | Issue | Check |
|---|---|---|
| 20/10 04:13 UTC | AA-860 | Nightly DB isolation probe after S22: `sessions.master_break_glass_only` pass (no `aa_cis_admin` session), dump 03:43 UTC green with `DUMP login=db_migrator`. Then AA-860 Done after S23 docs. |
| next frontend Dependabot PR | AA-903 | "Vercel deploy" shows skipped; link it and close AA-903. |
| daily 06:15 UTC | AA-816 | Ops probe enqueues `staff_directory_reconcile` (Infra #195). Check one job per UTC day in `shared.job` and its drift report (Cognito groups vs `staff_app_grant`). |
| daily 22:00 UTC | AA-869 | Snapshot expiry Lambda `aa-cis-dev-rds-snapshot-expiry` runs live (deletes manual snapshots > 30 d unless `keep-` / `aa:retain*`). An SNS mail only when it deletes, caps, finds a malformed tag or an orphan. |
| ≥01/11 | (cost) / AA-896 | Infra cost audit Aug/Sep/Oct 2026 per `App` tag and service (acc2) + acc3 Bedrock + AWS Lift credits. The numbers feed the Jira platform report period 2 (PR-20 Epic; period 1 PR-21 carried no amounts). |
| ~02/11 | (Jira) PR-20 | Platform report period 2 (biweekly Story under Epic PR-20): draft → Nghiệp approves → post. |
| ≤11/11 | AA-820 | Tenant terms AI clause — Ms. Thư decides whether counsel is needed. |
| ~mid-Nov | AA-862 follow-up | Re-request acc2 quotas in small steps (Cohere 20 → 100 rpm). |
| 18/11 | AA-878 | The 4 orphan secrets deleted 19/10 (`aa-cis/dev/api-keys`, `aa-cis/dev/acp-webhook-secret`, `aa-cis/dev/acp-partner-api`, `tripplanner/dev/mapbox-geocoding-token`) leave the recovery window. Nothing to do unless one must be restored before then (`restore-secret`). |
| 30/11, 31/12 | AA-868 | `.github/pip-audit-ignore.txt` (AA-CIS-App) entries expire: langchain, langgraph-sdk (30/11); chromadb (31/12, drop the dependency). Expiry turns Security Audit + Unit Tests red. |
| **before prod** | chore (security) | Rotate the GitHub OAuth token and the RDS master password (printed into the local S240 transcript; D-02/D-03: keep until prod). |

## 2. Waiting on Nghiệp (decisions / manual steps)

- **S244 new:** (a) N-F: disable `e2e-claude-code-2` on the Staff page (needs an owner Cognito session); (b) rotate the GitHub token sooner than "before prod": the S244 transcript printed the env (GITHUB_PERSONAL_ACCESS_TOKEN, TF_VAR_db_password) after a failed `export $(…)` — local only; (c) break-glass TOTP was rotated (S244): add the NEW `totp_seed` if you want it in an authenticator; (d) approve the S244 audit proposals: cancel AA-675 / AA-689 (superseded), new issues N1 (pip-audit expiry before 30/11), N2 (AA-680 customer half), N3 (TP guest-token check on GETs), N4 (Booking 1440 UI + audit rows), priority ups AA-901 / AA-875 / AA-876; (e) where the AA-852 179/180 legacy-grant revoke lives.

- **Mapbox:** revoke the old geocoding token in the Mapbox account (its secret `tripplanner/dev/mapbox-geocoding-token` was deleted 19/10).
- **Ms. Thư's first admin login** (invite sent 18/10; Google cleared the Chrome warning 19/10). Optional: Nghiệp dropped it from AA-858 Done-when (S243).
- **Break-glass TOTP:** add `totp_seed` from Secrets Manager `aa-identity/dev/breakglass` to an authenticator app.
- **AA-816 cutover call:** API-side `LEGACY_ADMIN_LOGIN_ENABLED` also serves Preview (ADR 0006a A6).
- AA-855 UAT videos: when Nghiệp says (after the tech work). Product questions from S238: T2 day separator; "— N Days" vs ", N Days".
- AA-829: approve deleting/securing the 2026-09-16 real-data dumps; DSN CNAME secrets are edited by hand.
- Paid place-pipeline geo backfill for the 8 countries without a geo graph (AA-905, §3 row 12): quote first, then approve or keep parked.

## 3. Ordered work queue (next sessions)

From the S244 master plan (`docs/audits/2026-10-19-S244-master-plan/`), updated at S244 end. X1 S21/S22 finished in S244 (two sessions early), so every slot from S245 on can move up one session; rule per session: 3–5 main items, close-along XS items do not count.

| # | Issue | Work | Lane | Size | Status after S244 audit / next action | Needs Nghiệp |
|---|---|---|---|---|---|---|
| 2 | AA-860 / AA-852 | **X1 close-out:** S23 docs (root schema-ownership, standards rows, skills, CONTEXT.md; S244 close-out PRs), then Done after the next nightly dump + probe show no master session; AA-852: find a home for the 179/180 legacy-grant revoke (not AA-847, that issue is Places), then Done | Data platform | S | **S20–S22 done in S244:** rl-002 (Infra #219), 245 (CIS #853 / Infra #223, 121 objects), S22 (Infra #225, 246 via CIS #860 / Infra #226); probe 58/58 (run 39256408600). CIS migration freeze and the XD9 `catalog.*` freeze are over | Approve the reworded Done-when (1); home of the 179/180 revoke |
| 3 | AA-816 → AA-703 | **Cognito cutover, rest:** N-F disable `e2e-claude-code-2` (owner session on the Staff page); S2 (API legacy flag off) together with AA-680 once a Preview sign-in exists (N-E); A10 (row 8) | Identity | S | **S244 done:** CIS #856 sign-out, break-glass managed-login test + `password_hash` cleared (Infra #224) + rotation, **S1** Production legacy login off (Vercel flag; `POST /api/auth/login` 404), **C9** CIS #858 + Preview credential (viewer), E2E smoke on the viewer account (#859), **I6** admin secret rotated. Report: root `docs/audits/2026-10-19-S244-aa816-cutover/` | N-F click (Nghiệp) |
| 4 | AA-903 | Close on the next Dependabot PR that touches `frontend/**` (link the skipped "Vercel deploy") | CI | XS | CIS #855, Booking #46, TP #106 merged (S244); Booking #39 closed; TP #109 was backend-only | — |
| 6 | AA-846 | **Apply guard** in `terraform-apply.yml` (refuse plans that touch `aws_secretsmanager_secret_version` / `random_password` / `aws_db_instance`), exact `required_version` pin, hidden diffs, tag/zip drift, apply-role narrowing (inline policy at 9,559/10,240 characters) | Infra | M | S245. TF 1.15.5 pinned in CI (#218), `.bak` removed (#211), param group (#155) | — |
| 7 | AA-865 | Pooled F9 re-flag rate (r5–r7 retries, n≥60, $0); a fix only if above 8% | CIS content | S | S245 | — |
| 8 | AA-816 (ADR 0006a A10) | **Remove the temporary E2E staff exception:** new CIS migration replacing the 250 exception, revert Infra #215, remove the CIS #849 scope, disable the user and row; update the Done-when | Identity | S | Unblocked (S22 done, freeze over). `create_staff_user.py` already retired (CIS #858) | — |
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

## 5. Closed in S244

- **AA-904 Done** (TP Next 15.5.28 / React 19, TP #107; preview smoke 4 flows desktop + 390 px, prod verified, `npm audit --omit=dev` 0).
- **AA-902** Done on the S244 root PR merge (0 real account IDs on main of the 3 public repos; CI probe PRs CIS #857 / Booking #47 / TP #108 red as intended; baseline row in place).
- **X1 S20–S22** shipped (see §3 row 2); **AA-816 S1, C9, I6** shipped (see §3 row 3).
- Bhutan 33 vs 32 fixed: funnel stages count only active raw tours (CIS #852; live 32/32/32/32).
- Chore: Terraform `use_lockfile` + CI Terraform 1.15.5 (Infra #218).
- TP #109 (pytest 9 + pytest-asyncio 1.4.0) merged.
- Reopened as false Done (S244 audit, verified): AA-825, AA-805, AA-665, AA-669. New: AA-906 (TP Next 16).

## 5a. Closed in S243

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

## 5b. Closed in S242

- **AA-854 Done** (Cognito Phase 0: break-glass, email-code spike, no-group deny, self sign-up rejected; evidence `docs/audits/2026-10-18-S242-cognito-phase1/`).
- **AA-816** shipped (In Progress until cutover): Infra #183/#184/#185/#191/#194, CIS #807/#808/#809/#810/#811/#812/#813/#826/#827/#828/#829, mig 247.
- **AA-852** X1 S9–S14 shipped (Booking #33, TP #97, root #95, Infra #179/#180/#182/#187/#188/#189/#190).
- Dependabot cleared in all repos (CIS #814/#819/#820/#830, Infra #192/#193 — AWS provider 6.69.1); CIS `dependabot.yml` groups security updates.
- AA-869 confirmed Done (S241). New issue: none.

## 5c. Closed in S241

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

- ECS CIS api **:711** / worker **:268** (`dev-7e0c68a2`, after the I6 restart the same image); Booking api **:33** (`91812e7e`); CIS migrations up to **250** (245, 246 applied S244); Booking bk-017; TripPlanner tp-015; roles **rl-002**. Terraform: CI **1.15.5** with S3 `use_lockfile` (DynamoDB lock still on, removal later); AWS provider 6.69.1.
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
