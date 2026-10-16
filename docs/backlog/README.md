# AA_Ecosys living backlog (ordered work queue)

**Purpose:** the single ordered list of what to do next, so a session starts here instead of re-auditing Linear. Built from the S238 full audit (69 open issues + data standards + logs + code + Jira, `docs/audits/2026-10-15-S238-backlog-audit/`) and updated at the end of S238.

**Rules:** at session start read §1–§3 and pick 3–5 items from §3 top-down (skip items blocked in §2). At session end update the Status column, move closed items to §5, add new items. Re-audit only when this file is older than ~2 weeks or many issues were created outside sessions.

_Last updated: S239, 16/10/2026 (Claude Code)._

## 1. Time-gated checks (do these first when due)

| Due | Issue | Check |
|---|---|---|
| ≥17/10 | chore (WAF follow-up) | **Rotate the CIS admin secret**: old WAF logs (30-day retention) hold the old value in plain text. 5 places in one go: Secrets Manager `aa-cis/dev/admin-secret`, ECS api + worker force-new-deployment, Vercel `aa-cis-frontend` `ADMIN_SECRET` (prod + preview) + redeploy, GitHub secret `ADMIN_SECRET` (AA-CIS-App), Lambda `aa-cis-dev-dfs-balance-check` (targeted apply re-reads the data source). Only when Vercel has free deploy slots; auto mode off. Verify old secret → 401, new → 200, admin UI loads, deploy guard works. |
| ≥01/11 | (new, cost) | **Infra cost audit Aug/Sep/Oct 2026**: Cost Explorer per month by `App` tag and per service (acc2) + acc3 Bedrock + AWS Lift credits; explain each jump by the change that caused it; savings options. `docs/audits/<date>-S<nnn>-cost-audit/`. |
| ≤11/11 | AA-820 | Tenant terms AI clause — Ms. Thư decides whether counsel is needed (no pressure). |
| ~mid-Nov | AA-862 follow-up | Re-request acc2 quotas in small steps (Cohere 20 → 100 rpm; Claude/GPT only once TrueIDC allows). acc2 is first in the embed chain already. |

## 2. Waiting on Nghiệp (decisions / manual steps)

- **AA-777:** close on outcome metrics (r7: 20/20 approved, 0 F9 holds, AA-768 set 5/5) and track the retry re-flag rate (13% vs 8%) in a small follow-up — or keep open.
- **Jira drafts S239** (PR-11, PR-12, PR-7, PR-16): `docs/sessions/2026-10-16-S239-jira-drafts.md` — approve, then post.
- AA-858 Ops overview: priorities with Ms. Thư. AA-855 UAT videos: when Nghiệp says (after the tech work).
- acc1 SSO (`aws sso login --profile pqnghiep-admin`) only if acc1 is needed again (dropped from the Cohere chain).
- Product questions still open from S238: T2 day separator per tenant catalog; "— N Days" vs ", N Days" (AA-778 closed; ask Ms. Thư if it matters).

## 3. Ordered work queue (next sessions)

| # | Issue | Work | Lane | Size | Status after S239 / next action | Needs Nghiệp |
|---|---|---|---|---|---|---|
| 1 | chore | Admin secret rotation (see §1) | Infra/security | S | Plan ready (S239 log). Blocked 16/10 by the Vercel deploy cap. | Auto mode off for the secret writes. |
| 2 | AA-836 | Portal at 390 px + My Catalog source 404 + raw markdown previews | CIS portal | M | Not started. Frontend: Vercel preview builds now skip backend-only PRs (Ignored Build Step). | — |
| 3 | AA-832 | Remaining RDS alarms: latency, disk queue, XID, per-role connections vs CONNECTION LIMIT (aa_app_user 15 since AA-817) | Infra/data | M | Not started. State the alarm cost before applying. | Cost OK. |
| 4 | AA-859 | Tenant pool wave 2: tenant writes, atoms/subject/planning RLS, brand-identity + admin_atoms paths, grant hardening, 2 PR-A follow-ups | Data platform / CIS | L | New (S239). One route group per PR behind a flag. | Flag flips (report-then-confirm). |
| 5 | AA-751 | X6 per-owner job tables (unblocks AA-861) | Data platform / Booking / TP | M | Re-scoped S238. | — |
| 6 | AA-834 | Flaky AA-752 smoke test (click before hydration) | CIS portal/CI | S | Not started. | — |
| 7 | AA-863 | Admin: seed place + country next to each Subject / T9 piece | CIS portal | S | New (split from AA-857). | — |
| 8 | AA-703 | Cognito identity epic, Phase 0 | Identity/infra | XL | Unblocked (SES prod). | Rewrite per ADR 0006. |
| 9 | AA-712 | Place pipeline: L4 read-model latency, PLACES_SOURCE flip, content checks, a3_place_days shadow decision | CIS platform | M | Partly shipped (mig 235). | — |
| 10 | AA-800 | Tenant signature vocabulary | CIS T-series | M | No change. | Paid run (<$1). |
| 11 | AA-780 | LinkedIn: Trail Pulse voice fields, broetry, hashtag check | CIS T-series | S | No change. | Review voice fields. |
| 12 | AA-816 | Staff directory + Cognito groups | Identity / CIS admin | L | No change. | Done-when rewrite. |
| 13 | AA-682 | Booking wave 3: supplier bookings + trip checks, invoices/payment schedule | Booking | XL | No change. | Payment marking, tax. |
| 14 | AA-858 | Ops overview on /admin/overview | CIS admin | M | Waits for Ms. Thư's priorities. | Priorities. |
| 15 | AA-860 | X1 runtime role split (cis_owner / cis_app) | Data platform | L | New (S239); after AA-807/AA-826; consider doing it on the AA-864 target account. | Secrets, MFA Terraform. |
| 16 | chore | TripPlanner `.claude/CLAUDE.md`: Cohere chain is acc2 → acc3 (acc1 dropped); Mapbox URL restriction done | Docs | XS | — | — |
| 17 | AA-855 | UAT videos for all apps | QA | M | After the tech work, when Nghiệp says. | Go signal. |

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
| AA-829 | Restore drill + private DSN CNAME + secure the 2026-09-16 dumps + single-schema restore runbook (folded) | later |  | Edit the DSN secrets by hand. Approve deleting the local dumps. |
| AA-826 | New-app playbook tooling: owners.yaml, role bootstrap template, contract hash guard | later |  | Pick the owner of owners.yaml. |
| AA-835 | ADR 0004a supply content: contracts, Booking supply outbox/views, CIS consumer with review, read-back, entity_media | later |  | Approve creating the issue. |
| AA-837 | /plan: 7 WCAG contrast violations, Customise 404 console error, '1 DAYS' | later | Not started (frontend). | Approve creating the issue. |
| AA-838 | Wire the weekly/monthly/quarterly DB reviews into the session ritual; first capacity review | later | Not started. | Approve creating the issue. |
| AA-741 | T-series audit G7/G8 (48-tour run) re-scoped, without the Jev layer; s237 FB test-piece cleanup (folded) | later |  | Approve the re-scope and the paid G7 run (~$10-20). |
| AA-784 | Platform-wide place card build (~$15-25) | later |  | Paid run approval and country order. |
| AA-803 | Calibrate a1_promise_unsupported, or switch it off | later |  | Calibrate or switch off. |
| AA-765 | Gateway refactor: judge client, T11 dispatch into acp_publish, docstrings | later |  |  |
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
| AA-842 | OTel gen_ai tracing investigation | parked | Report on Notion (Program Brain) + AA-CIS-App docs/investigations/llm-otel-tracing.md. | Decided S238: keep Backlog; build option B (gateway span, ~15–20 h) only when slow/unexplained jobs justify it |
| AA-864 | Research: consolidate all of acc2 (services, data, connections) on acc3 or one designated account — complexity, cost, time | later | Seed notes on the issue. Do with AA-860 on the target account. | Pick the target account when the research is done. |
| AA-861 | TripPlanner outbox PII redaction after 90 d | later | Blocked on AA-751 (tripplanner.job). | |

## 5. Closed in S239

- Done with live evidence (comments on each issue): AA-792, AA-778, AA-771, AA-772, AA-681, AA-708, AA-756, AA-763, AA-807, AA-843, AA-701, AA-791, AA-683, AA-822, AA-823, AA-679, AA-802, AA-668, AA-831, AA-768, AA-801, AA-828, AA-833, AA-827, AA-806, AA-841, AA-714, **AA-856, AA-818, AA-819, AA-817, AA-825, AA-857, AA-862, AA-678**.
- New in S239: AA-844 → AA-864 (open ones: AA-855, AA-858, AA-859, AA-860, AA-861, AA-863, AA-864).

## 6. Environment notes for the next session

- ECS CIS api :642 / worker :199 (image b478a18b, #770); Booking :21 (bk-012); CIS migrations up to **240**; TP tp-012; TripPlanner Lambdas from #92.
- **LLM accounts:** acc2 (payer TrueIDC) cannot use Bedrock LLMs → every LLM call goes to **acc3** (payer eCloudvalley, AWS Lift credits). Cohere Embed v4: cache → acc2 (20 rpm) → acc3 (2,000 rpm; Marketplace agreement accepted 16/10) → keyword fallback. acc1 = Nghiệp personal, not in any chain.
- **Cost rule:** state the monthly cost of any new AWS service/resource before applying.
- **Vercel:** Hobby cap ~100 deployments / 24 h (rolling, team-wide). Ignored Build Step on all 3 projects skips frontend builds for backend-only commits (production deploy shows CANCELED). Still batch frontend PRs.
- AA-857 snapshot for restore: `s3://aa-cis-bronze-005097885195/scripts/restore/aa857_20261016T080718Z.json` (+ `.tmp-session/s239/aa857_repair_restore.py`).
- Test channel credentials: `aa-cis/dev/e2e-wordpress-test`, `aa-cis/dev/e2e-facebook-test`; e2e admins `aa-cis/dev/e2e-test-admin` and `-2`.
- Terraform: always targeted plans, read before apply; acc3 root `accounts/acc3-bedrock` with profile `nghiep_aa365`.
- Merge backend PRs one at a time (merge train script `.tmp-session/s239/merge_train.sh`), update BEHIND branches via `gh api -X PUT …/update-branch`. Never run two job-producing drivers at once on `shared.job`.
