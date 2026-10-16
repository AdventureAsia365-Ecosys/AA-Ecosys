# AA_Ecosys living backlog (ordered work queue)

**Purpose:** the single ordered list of what to do next, so a session starts here instead of re-auditing Linear. Built from the S238 full audit (69 open issues + data standards + logs + code + Jira, `docs/audits/2026-10-15-S238-backlog-audit/`) and updated at the end of S238.

**Rules:** at session start read §1–§3 and pick 3–5 items from §3 top-down (skip items blocked in §2). At session end update the Status column, move closed items to §5, add new items. Re-audit only when this file is older than ~2 weeks or many issues were created outside sessions.

_Last updated: S240, 16–17/10/2026 (Claude Code)._

## 1. Time-gated checks (do these first when due)

| Due | Issue | Check |
|---|---|---|
| ≥17/10 | chore (WAF follow-up) | **Rotate the CIS admin secret** (old WAF logs hold the old value). 5 places in one go: Secrets Manager `aa-cis/dev/admin-secret`, ECS api + worker force-new-deployment, Vercel `aa-cis-frontend` `ADMIN_SECRET` (prod + preview) + redeploy, GitHub secret `ADMIN_SECRET` (AA-CIS-App), Lambda `aa-cis-dev-dfs-balance-check`. Needs a free Vercel slot; auto mode off. |
| ≥17/10 ~07:30 VN | Vercel | Deployment cap (~100 / 24 h, team-wide, canceled ones count) frees from 00:22Z. Batch the frontend work below into few deploys. |
| ≥01/11 | (new, cost) | Infra cost audit Aug/Sep/Oct 2026 per `App` tag and service (acc2) + acc3 Bedrock + AWS Lift credits. |
| ≤11/11 | AA-820 | Tenant terms AI clause — Ms. Thư decides whether counsel is needed. |
| ~mid-Nov | AA-862 follow-up | Re-request acc2 quotas in small steps (Cohere 20 → 100 rpm). |
| **before prod** | chore (security) | **Rotate the GitHub OAuth token (`gh`/MCP) and the RDS master password**: both were printed into the local S240 Claude Code transcript (MFA-expired `export $(…)`). Nghiệp: keep until prod. Run `.tmp-session/s240/redact_leaked_env.sh` after closing S240 to scrub the local copies. |

## 2. Waiting on Nghiệp (decisions / manual steps)

- AA-858 Ops overview: priorities with Ms. Thư. AA-855 UAT videos: when Nghiệp says (after the tech work).
- Product questions still open from S238: T2 day separator per tenant catalog; "— N Days" vs ", N Days".
- acc1 SSO only if acc1 is needed again.

## 3. Ordered work queue (next sessions)

| # | Issue | Work | Lane | Size | Status after S240 / next action | Needs Nghiệp |
|---|---|---|---|---|---|---|
| 1 | chore (Vercel) | **CIS admin pollers** (Fluid Active CPU 52 % of the Hobby cap): Jobs page poll only while active, 30 s, page size 25, no payload in the list; Topbar on react-query 120 s; one shared review-queue key; admin verify cache 20 s → ~5 min; proxy routes stream the body. Report: `docs/audits/2026-10-16-S240-vercel/README.md`. | CIS frontend | M | New (S240). Needs Vercel slots. | — |
| 2 | chore (Vercel) | CI-created previews only when `frontend/**` changes (Git-integration previews off), all 3 repos; UI smoke keeps working | CI | M | New (S240): `git.deploymentEnabled` cannot filter by path. | — |
| 3 | AA-836 + AA-863 + AA-834 | Portal at 390 px / My Catalog 404 / raw markdown; seed place next to Subject; flaky smoke | CIS portal | M | Not started (Vercel cap). | — |
| 4 | chore | Admin secret rotation (§1) | Security | S | Plan ready (S239 log). | Auto mode off. |
| 5 | AA-751 | Remaining X6: Booking deploy gate (GitHub OIDC, `deploy-dev.yml` preflight, seeded probe blocks then passes); R1 data-standard flips (C5.1b autovacuum, C6 rows) | Booking / Infra / docs | M | First wave Done on Dev (S240: idle check, 242, bk-013, release-on-shutdown, acp_runs readers, in-process job metrics + 6 alarms). | — |
| 6 | AA-861 | `tripplanner.job` from the template + scheduled Lambda worker + kind `tp_outbox_pii_redact` | TripPlanner | M–L | Unblocked (S240). TP merges need auto mode off. | TP merges. |
| 7 | AA-859 | D5b (`/v1/tours/{id}/full` tenant branch, `/{id}`, `/versions/{id}/export-docx`); wave 3 (RLS brand rules / seo config, brand identity, publish); wave 4 (subject / quarter_plan / tenant_tour_pages / tour_atoms RLS + routes, main-pool shrink from the gauge) | Data platform / CIS | L | Wave 2 live: 6 flags ON (S240), 241 applied. | Wave 4 route hub retire (Q3). |
| 8 | chore (Infra) | Remove `ok_actions` from the 2 TripPlanner Lambda alarms (left out of #160 so the apply did not touch the TP artifact S3 objects' tags) | Infra | XS | — | — |
| 9 | AA-865 | Pooled F9_cta_fact re-flag rate (n ≥ 60) | CIS T-series | S | New (S240). | — |
| 10 | AA-703 | Cognito identity epic, Phase 0 (Infra #105 open since 14/10) | Identity/infra | XL | Unblocked. | Rewrite per ADR 0006. |
| 11 | AA-712 | Place pipeline: L4 read-model latency, PLACES_SOURCE flip, content checks | CIS platform | M | Partly shipped. | — |
| 12 | AA-800 | Tenant signature vocabulary | CIS T-series | M | — | Paid run (<$1). |
| 13 | AA-780 | LinkedIn: Trail Pulse voice fields, broetry, hashtag check | CIS T-series | S | — | Review voice fields. |
| 14 | AA-816 | Staff directory + Cognito groups | Identity / CIS admin | L | — | Done-when rewrite. |
| 15 | AA-682 | Booking wave 3: supplier bookings + trip checks, invoices/payment schedule | Booking | XL | — | Payment marking, tax. |
| 16 | AA-858 | Ops overview on /admin/overview | CIS admin | M | Waits for Ms. Thư. | Priorities. |
| 17 | AA-860 | X1 runtime role split (cis_owner / cis_app) | Data platform | L | After AA-807/AA-826. | Secrets, MFA Terraform. |
| 18 | AA-855 | UAT videos for all apps | QA | M | After the tech work. | Go signal. |

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

## 5. Closed in S240

- Done with live evidence: **AA-777** (r7 outcome metrics; residual → AA-865), **AA-832** (RDS alarms; sampling later moved in process).
- In Progress with shipped waves: **AA-859** (wave 2 live, 6 flags ON), **AA-751** (X6 first wave live).
- New in S240: AA-865.

## 6. Environment notes for the next session

- ECS CIS api :657 / worker :214 (image 353c328d, #786); Booking :26 (bk-013); CIS migrations up to **242**; TP tp-012.
- **Tenant pool:** all `aa859:*` flags ON (piece_edit, t2_version_write, angle_gate_decide, unpublish, t2_version_reads, integration_connect) + the 5 earlier flags. Rollback = `DEL` the key (tool: `docs/audits/2026-10-16-S240-aa859/aa859_flag.py`, automated flip: `aa859_flip_verify.py`). Pool max 2 / task, api autoscale max 7.
- **Ops metrics:** in process (CIS api `ops_metrics_sampler`, Booking `JobMetricsSampler`), every 5 min → `AA/RDS` (per role) and `AA/Jobs/CIS` / `AA/Jobs/Booking`. No Lambda schedule for it any more. Alarms e-mail **only on ALARM** (no OK e-mails). 10 custom metrics = free tier; the AA-296 `ACP/Pipeline` filter was deleted.
- **DB Migrate** refuses apply while any `<schema>.job` has non-exempt queued/running rows (exit 7); exempt: `bk_inquiry_pull`. Override input `override_busy_jobs` (Nghiệp only).
- **Terraform:** plan/apply only from merged `main`; a targeted plan can pull in dependencies (RDS parameter group, TP S3 artifact objects) — read and exclude.
- **Vercel:** 3 projects left (aa-cis-frontend, aa-tripplanner, aa-booking-admin); deploy hook removed (#783).
- Terraform acc3 root `accounts/acc3-bedrock` with profile `nghiep_aa365`. Merge backend PRs one at a time (`.tmp-session/s240/train.sh`, `TRAIN_DIR` / `TRAIN_REPO` for other repos).
