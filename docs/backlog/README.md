# AA_Ecosys living backlog (ordered work queue)

**Purpose:** the single ordered list of what to do next, so a session starts here instead of re-auditing Linear. Built from the S238 full audit (69 open issues + data standards + logs + code + Jira, `docs/audits/2026-10-15-S238-backlog-audit/`) and updated at the end of S238.

**Rules:** at session start read §1–§3 and pick 3–5 items from §3 top-down (skip items blocked in §2). At session end update the Status column, move closed items to §5, add new items. Re-audit only when this file is older than ~2 weeks or many issues were created outside sessions.

_Last updated: S241, 17/10/2026 (Claude Code). Q10 (Nghiệp): finish the platform block (admin, X1, Cognito, portal split) in one stretch, then return to CIS content work._

## 1. Time-gated checks (do these first when due)

| Due | Issue | Check |
|---|---|---|
| **X1 S1 merge → X1 S22** | AA-852 / AA-860 | **`catalog.*` view freeze** (X1 plan XD9): no `CREATE/ALTER/DROP VIEW catalog.*` in any CIS migration until the DB Migrate login is `db_migrator` (S22). Recorded in AA-CIS-App `CONTEXT.md` (#806). A catalog change that cannot wait = Nghiệp decides plan option (b) roles/ file or (c) `db_migrator` earlier. |
| daily 22:00 UTC | AA-869 | Snapshot expiry Lambda `aa-cis-dev-rds-snapshot-expiry` runs live (deletes manual snapshots > 30 d unless `keep-` / `aa:retain*`). An SNS mail only when it deletes, caps, finds a malformed tag or an orphan. |
| 30/11, 31/12 | AA-868 | `.github/pip-audit-ignore.txt` (AA-CIS-App) entries expire: langchain, langgraph-sdk, pytest 9 (30/11); chromadb (31/12, drop the dependency). Expiry turns Security Audit + Unit Tests red. |
| ≥01/11 | (cost) | Infra cost audit Aug/Sep/Oct 2026 per `App` tag and service (acc2) + acc3 Bedrock + AWS Lift credits. |
| ≤11/11 | AA-820 | Tenant terms AI clause — Ms. Thư decides whether counsel is needed. |
| ~mid-Nov | AA-862 follow-up | Re-request acc2 quotas in small steps (Cohere 20 → 100 rpm). |
| **before prod** | chore (security) | Rotate the GitHub OAuth token and the RDS master password (printed into the local S240 transcript; D-02/D-03: keep until prod). |

## 2. Waiting on Nghiệp (decisions / manual steps)

- **Approve and post** the S241 Jira draft (PR-18) and the Zalo note to Ms. Thư: `docs/sessions/2026-10-17-S241-jira-drafts.md`.
- **Cognito break-glass:** set the break-glass secret value by hand when the agent has created the user (AA-854).
- AA-855 UAT videos: when Nghiệp says (after the tech work). Product questions from S238: T2 day separator; "— N Days" vs ", N Days".
- AA-829: approve deleting/securing the 2026-09-16 real-data dumps; DSN CNAME secrets are edited by hand.

## 3. Ordered work queue (next sessions)

| # | Issue | Work | Lane | Size | Status after S241 / next action | Needs Nghiệp |
|---|---|---|---|---|---|---|
| 1 | AA-854 → AA-703 | **Cognito Phase 1 (staff):** create the break-glass user (AdminCreateUser SUPPRESS → cis-admin + booking-admin → disable); CIS admin + Booking staff sign in with the WORKFORCE pool (email code); keep the old login as fallback until verified | Identity | L | Phase 0 applied S241 (pools us-west-1_bCcFvbSOS / us-west-1_nKOvHan0W, 7 groups, 4 triggers, 14 alarms). | Break-glass secret value. |
| 2 | AA-852 / AA-860 | **X1 next waves:** S9 probe files, S10 ADR 0004b, S11–S14 per-app SGs + `db_migrator` task def, S15–S19 `cis_owner` (CIS 245) / `cis_app` runtime split, S20–S23 (plan `docs/audits/2026-10-17-S241-x1/x1-plan.md`) | Data platform | XL | S1–S8 live; probe 39 pass / 16 pending (all CIS-side) / 0 fail. Undo for tp-013 kept on Infra branch `feat/x1-s7-tp013-undo`. | MFA Terraform for SG/bootstrap. |
| 3 | AA-885 | **Split the tenant portal** into its own Vercel project + domain (Q8: now) | CIS portal | L | Not started. | — |
| 4 | AA-816 | Staff create/disable/role UI on top of Cognito (Q6: after Cognito) | Identity / admin | M | Read-only Staff directory shipped (AA-883). | — |
| 5 | AA-858 | Ops overview on /admin/overview (Q9: agent designs, then show Ms. Thư) | CIS admin | M | Not started. | Show Ms. Thư. |
| 6 | AA-884 | Apps page (health/version/links), staff action audit view, cost per app | CIS admin | M | Not started. | — |
| 7 | AA-869 | Close: root PR with rollback runbook + incident page merged | Ops | XS | All live (ECR immutable, rollback drill, snapshot expiry). | — |
| 8 | AA-878 | Secrets register, orphaned-secret cleanup, read-only non-admin E2E account (also closes the AA-883 reviewer UI gap) | Security | M | Not started. | — |
| 9 | AA-874 | Redis AUTH/TLS/at-rest + tenant-flag read-failure alarm | Security | M | Not started (cost quote first). | Cost (D-19). |
| 10 | AA-876 / AA-875 | API edge hardening (login rate limit, throttle/WAF, CORS, headers); SSRF-safe outbound client | Security | M | Not started. | — |
| 11 | AA-873 | GuardDuty, Access Analyzer, S3 BPA, CloudTrail | Security | S–M | Not started. | Cost (D-19). |
| 12 | AA-871 / AA-879 | JSON logs + Sentry for Booking and TripPlanner; CI gate parity across repos | Observability / CI | M | CIS backend Sentry live (AA-870). | — |
| 13 | AA-729 | Golden set ~100 samples from existing data + scoring for audit rounds (D-23) | CIS eval | M | Rewritten S241. | — |
| 14 | AA-859 | D5b; wave 3 (brand identity, publish); wave 4 (subject / planning / tour_atoms) | Data platform / CIS | L | Wave 2 live; tenant pool now fail-closed (D-12, #792). | Wave 4 route retire. |
| 15 | AA-861 | `tripplanner.job` from the template + scheduled Lambda worker + `tp_outbox_pii_redact` | TripPlanner | M–L | Unblocked. | — |
| 16 | AA-829 | Single-schema restore runbook + rehearsal; DSN CNAME; dumps | Data/DR | M | Full PITR drill passed S241 (~22 min). | Dumps, DSN secrets. |
| 17 | AA-865, AA-712, AA-800, AA-780 | CIS content work (after the platform block, Q10) | CIS | — | — | per issue |
| 18 | AA-682 | Booking wave 3 | Booking | XL | — | Payment marking, tax. |
| 19 | AA-855 | UAT videos for all apps | QA | M | After the tech work. | Go signal. |

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
| AA-826 | New-app playbook tooling: owners.yaml, role bootstrap template, contract hash guard | later |  | Pick the owner of owners.yaml. |
| AA-835 | ADR 0004a supply content: contracts, Booking supply outbox/views, CIS consumer with review, read-back, entity_media | later |  | Approve creating the issue. |
| AA-837 | /plan: 7 WCAG contrast violations, Customise 404 console error, '1 DAYS' | later | Not started (frontend). | Approve creating the issue. |
| AA-838 | Wire the weekly/monthly/quarterly DB reviews into the session ritual; first capacity review | later | Not started. | Approve creating the issue. |
| AA-741 | T-series audit G7/G8 (48-tour run) re-scoped, without the Jev layer; s237 FB test-piece cleanup (folded) | later |  | Approve the re-scope and the paid G7 run (~$10-20). |
| AA-784 | Platform-wide place card build (~$15-25) | later |  | Paid run approval and country order. |
| AA-803 | Calibrate a1_promise_unsupported, or switch it off | later |  | Calibrate or switch off. |
| AA-765 | Gateway refactor: judge client, T11 dispatch into acp_publish, docstrings | later |  |  |
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

## 5. Closed in S241

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

- ECS CIS api :673 / worker :230 (image `dev-58801f33…`, #805); Booking bk-014; TripPlanner tp-013; CIS migrations up to **243**; roles rl-001.
- **X1:** Booking/TripPlanner objects owned by `bk_owner` / `tp_owner` (NOLOGIN). DB Migrate reads the LIVE owner of `anchor_schema` and runs each file as that role (`owners.yaml`). Probe workflow `db-isolation-probe.yml` (schedule + after each apply).
- **OIDC:** `aa-cis-dev-app-deploy` and `aa-cis-infra-tf-apply` trust only `ref = refs/heads/main`. CIS env `dev` allows only `main`; `ADMIN_SECRET` is an env secret. Bootstrap roles/policies are applied by hand with the MFA admin profile.
- **ECR CIS IMMUTABLE**, lifecycle 30 `dev-*` + untagged 7 d; Deploy Dev reuses an existing `dev-<sha>`. Rollback runbook: `skill/aa-ship` §5.
- **Alarms** e-mail on ALARM and OK (D-20). New: `aa-cis-dev-api-5xx`, `aa-cis-dev-api-latency-p95`, Cognito 14 alarms.
- **Sentry:** CIS backend → project `aa-cis-api` (secret `aa-cis/dev/sentry-dsn-api`), frontend → `aa-cis-frontend`; uptime monitor for CIS `/health` (free plan: 1 monitor).
- **Vercel:** Git integration off; `vercel-deploy.yml` creates deploys only when `frontend/**` changes (`VERCEL_TOKEN` per repo).
- **GitHub:** rulesets "no force-push / no deletion" on the 3 public repos; Dependabot (Infra `dependabot.yml`, weekly grouped); CodeQL default setup.
- Tenant pool flags fail closed: unreadable flag = tenant pool; explicit `"false"` = admin pool (`TENANT_POOL_FORCE_ADMIN_FLAGS` env for an emergency).
