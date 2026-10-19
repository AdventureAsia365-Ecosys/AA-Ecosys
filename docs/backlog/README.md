# AA_Ecosys living backlog (ordered work queue)

**Purpose:** the single ordered list of what to do next, so a session starts here instead of re-auditing Linear. Built from the S238 full audit (69 open issues + data standards + logs + code + Jira, `docs/audits/2026-10-15-S238-backlog-audit/`) and updated at the end of every session since.

**Rules:** at session start read §1–§3 and pick 3–5 items from §3 top-down (skip items blocked in §2). At session end update the Status column, move closed items to §5, add new items. Re-audit only when this file is older than ~2 weeks or many issues were created outside sessions.

_Last updated: S243, 19/10/2026 (Claude Code). Q10 (Nghiệp): finish the platform block (admin, X1, Cognito, portal split) in one stretch, then return to CIS content work. S243 shipped the portal split, ops overview + Platform pages, Booking staff on Cognito, Cognito E2E and X1 S15–S19; what is left of the block is X1 wave 5 and the AA-816 cutover._

## 1. Time-gated checks (do these first when due)

| Due | Issue | Check |
|---|---|---|
| **X1 S1 merge → X1 S22** | AA-852 / AA-860 | **`catalog.*` view freeze** (X1 plan XD9): no `CREATE/ALTER/DROP VIEW catalog.*` in any CIS migration until the DB Migrate login is `db_migrator` (S22). Recorded in AA-CIS-App `CONTEXT.md` (#806). A catalog change that cannot wait = Nghiệp decides plan option (b) roles/ file or (c) `db_migrator` earlier. |
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

- **Mapbox:** revoke the old geocoding token in the Mapbox account (its secret `tripplanner/dev/mapbox-geocoding-token` was deleted 19/10).
- **Ms. Thư's first admin login** (invite sent 18/10; Google cleared the Chrome warning 19/10). Then show her /admin/overview (AA-858).
- **X1 S20:** set the value of `aa-cis/dev/db-migrator` by hand (Console) when wave 5 starts.
- **Break-glass TOTP:** add `totp_seed` from Secrets Manager `aa-identity/dev/breakglass` to an authenticator app.
- **AA-816 cutover call:** API-side `LEGACY_ADMIN_LOGIN_ENABLED` also serves Preview (ADR 0006a A6).
- AA-855 UAT videos: when Nghiệp says (after the tech work). Product questions from S238: T2 day separator; "— N Days" vs ", N Days".
- AA-829: approve deleting/securing the 2026-09-16 real-data dumps; DSN CNAME secrets are edited by hand.
- Paid place-pipeline geo backfill for the 8 countries without a geo graph (§3 row 12): approve or keep parked.

## 3. Ordered work queue (next sessions)

| # | Issue | Work | Lane | Size | Status after S243 / next action | Needs Nghiệp |
|---|---|---|---|---|---|---|
| 1 | AA-860 / AA-852 | **X1 wave 5:** S20 rl-002 `cis_owner` + `db_migrator`, S21 CIS 245 ownership move, S22 DB Migrate / Dump / probe log in as `db_migrator` (ends the `catalog.*` freeze). Plan `docs/audits/2026-10-17-S241-x1/x1-plan.md` | Data platform | L | S1–S19 live. S243: 244 applied (CIS #834/#843/#845, Infra #201/#214); **S18** api:703 / worker:260 run as `cis_app` (Infra #203, rollback api:701 / worker:258); **S19** CIS task role denied the master, `db-migrator`, `booking/*`, `tripplanner/*` secrets (Infra #204, 20/20 denied). One orphan master session from the stopped api:701 task. | Secret value at S20; MFA Terraform. |
| 2 | AA-816 → AA-703 | **Cognito Phase 1 cutover (Stage S):** every active row has an email + its own `cognito_sub` (missing email: e2e-claude-code, -2, -viewer; missing sub: admin, e2e-claude-code ×3, thu); break-glass through managed login; `ADMIN_SECRET` rotation + Preview low-privilege credential (C9/I6); legacy flag off; invitation email follow-up | Identity | M | S243: Cognito email-code E2E live (CIS #842, Infra #198; `e2e-cognito.yml` run 39207450965, 7 passed); break-glass OTP probe OK, EMAIL_OTP not offered (Infra #196); daily reconcile trigger (Infra #195); AdminCreateUser password alarm. | Cutover go. |
| 3 | AA-816 (ADR 0006a A10) | **Remove the temporary E2E staff exception** once the E2E work is done: `e2e@e2e-mail.lumiguides.it.com` (reviewer, no password) — disable the staff row + Cognito user, revert the WORKFORCE trigger address exception (Infra #215), drop the `admin_users_email_chk` exception (CIS 250 → new migration) and `E2E_TEST_STAFF_EMAIL` / `require_e2e_test_scope` (CIS #849). Steps: ADR 0006a A10 | Identity | S | Live since S243 (option B, Nghiệp): staff created by `nghiep` (audit `staff.created` 06:00:03Z), group `cis-reviewer` only, 0 Booking grant. | — |
| 4 | (new) CI | **Skip the "Vercel deploy" job for `dependabot[bot]`** in Booking, TripPlanner and CIS CI: Dependabot runs get no Actions secrets (`VERCEL_TOKEN`), so every Dependabot PR shows a red check that is not a code failure | CI | XS | Seen on Booking #38/#40/#44 and TP #102/#104 (S243). | — |
| 5 | (new) TripPlanner | **Next 14 → 15 upgrade** as planned work (replaces Dependabot TP #104, which fails `npm ci` with ERESOLVE: eslint-config-next@16 vs eslint 8); bump eslint, postcss; build + UI smoke on preview; then close #104 | TripPlanner | S–M | TP #104 open. | Create a Linear issue? |
| 6 | AA-858 | Ops overview on /admin/overview (business view for Ms. Thư) | CIS admin | M | Live (CIS #839/#840/#848, Booking #37 bk-017, TP #98 tp-015, Infra #205): apps health ok, TripPlanner traffic, Booking funnel, cost per app (245.17 total, Jev own row). Next: Ms. Thư's walkthrough, then Done with evidence. | Show Ms. Thư. |
| 7 | AA-884 | Apps page (health/version/links), staff action audit view, cost per app | CIS admin | M | Live (CIS #835 mig 248 append-only audit, #836/#837/#838/#848; Infra #206/#209 `/health/ready`). Next: re-read Done-when, close with evidence. | — |
| 8 | AA-680 | **Booking staff Phase 2 finish:** drop the CIS bridge (`aa-cis/dev/booking-jwt-signing-key`, booking_jwt) once all Booking staff sign in through Cognito | Booking / identity | S | Booking staff email-code sign-in live (Booking #34 bk-016, #35, #36; Infra #199 one-time link; Vercel `COGNITO_BOOKING_STAFF_CLIENT_SECRET` set). SSO with CIS = shared managed-login session, each app checks its own role. | — |
| 9 | AA-878 | Secrets register follow-ups: GitHub orphans (`VERCEL_DEPLOY_HOOK`, `ACPCORE_READ_TOKEN`), register open items 1–9, monthly drift check (`tools/secrets/register_check.py`) | Security | S | Register (root #101), I1/I2 (Infra #195/#207, TP #99), 4 Secrets Manager orphans deleted 19/10 (recovery until 18/11), viewer role CIS 249 + `e2e-claude-code-viewer` (CIS #841). CI smoke stays on the admin account (S243 recommendation). | — |
| 10 | (chore) | Switch the S3 backend to `use_lockfile` (grant added in Infra #195) | Infra | XS | S243: stale `import` blocks removed (#195), Next 16 `proxy.ts` (CIS #831). | — |
| 11 | AA-821 | **Tenant CRM re-plan** (Jira PR-19): research + a short phased MVP plan inside the tenant portal for the tenants' B2C customers; no 40-week plan (Ms. Thư, Zalo 19/10). Spec `docs/research/partner-crm-spec.md` | CIS portal | M (research) | Noted on AA-821 (2 comments 19/10). No build before Nghiệp + Ms. Thư approve the plan. | Approve the plan. |
| 12 | (new) data | **Place-pipeline geo gap:** 8 countries have no geo graph; it is only used with `match_destinations` (off), so no live impact today. The backfill is a paid place-pipeline run | CIS data | S + paid | Found by the X1 S15 photo itinerary parity run-script (Infra #200). | Paid run approval. |
| 13 | (new) data | **Bhutan 33 vs 32:** S1 generated 33 tours while raw active is 32 — find the extra row (stale version, deleted raw, duplicate) | CIS data | XS | Finding 8 of the #848 review, only noted. | — |
| 14 | AA-874 | Redis AUTH/TLS/at-rest + tenant-flag read-failure alarm | Security | M | Not started (cost quote first). | Cost (D-19). |
| 15 | AA-876 / AA-875 | API edge hardening (login rate limit, throttle/WAF, CORS, headers); SSRF-safe outbound client | Security | M | Not started. | — |
| 16 | AA-873 | GuardDuty, Access Analyzer, S3 BPA, CloudTrail | Security | S–M | Not started. | Cost (D-19). |
| 17 | AA-871 / AA-879 | JSON logs + Sentry for Booking and TripPlanner; CI gate parity across repos | Observability / CI | M | CIS backend Sentry live (AA-870). PR template + title check in all repos (S243). | — |
| 18 | AA-729 | Golden set ~100 samples from existing data + scoring for audit rounds (D-23) | CIS eval | M | Rewritten S241. | — |
| 19 | AA-859 | D5b; wave 3 (brand identity, publish); wave 4 (subject / planning / tour_atoms) | Data platform / CIS | L | Wave 2 live; tenant pool now fail-closed (D-12, #792). | Wave 4 route retire. |
| 20 | AA-861 | `tripplanner.job` from the template + scheduled Lambda worker + `tp_outbox_pii_redact` | TripPlanner | M–L | Unblocked. | — |
| 21 | AA-829 | Single-schema restore runbook + rehearsal; DSN CNAME; dumps | Data/DR | M | Full PITR drill passed S241 (~22 min). | Dumps, DSN secrets. |
| 22 | AA-865, AA-712, AA-800, AA-780 | CIS content work (after the platform block, Q10) | CIS | — | — | per issue |
| 23 | AA-682 | Booking wave 3 | Booking | XL | — | Payment marking, tax. |
| 24 | AA-855 | UAT videos for all apps | QA | M | After the tech work. | Go signal. |

## 3a. Platform roadmap keys (PLAT-01)

Content and status live in the [engineering handbook §9](../engineering-handbook.md#9-roadmap); this list only orders
the next picks.

| Order | U-xx / key | Issue | Next step |
|---|---|---|---|
| 1 | AA-887, AA-888, U-09, U-11 | AA-887, AA-888, AA-889, AA-890 | Docs bundle merged (root #105); PR template + title check + ADR index in all repos (CIS #846, Infra #211, Booking #42, TP #100). Finish the docs lint jobs in the app repos; squash-only settings |
| 2 | AA-892, AA-893 | AA-892, AA-893 | Run the rollback runbooks on Dev; generated alarm tables (step 2; step 1 live, Infra #213) |
| 3 | AA-896, U-38 | AA-896, AA-838 | First cost and capacity review on or after 01/11 (anomaly detection live, Infra #213) |
| 4 | U-25 → AA-891 | AA-901, AA-891 | GitHub App, then release-please |
| 5 | U-44, AA-894, AA-895, AA-897 | AA-899, AA-894, AA-895, AA-897 | OpenAPI + oasdiff; env-config register; guides out of draft. Dependabot for Booking and TripPlanner is on (Booking #43, TP #101) |
| 6 | U-26 + U-04, U-28 + U-61 | AA-878, AA-879 | Folded per N-12 |
| later | U-15, U-24, U-37, U-39, U-42, U-56 | AA-848, AA-877, AA-850, AA-851, AA-846, AA-881 | Order when picked |

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
| AA-821 | Tenant CRM — moved to §3 row 11 (re-plan, no 40-week plan) | later | S243: spec in `docs/research/partner-crm-spec.md`; direction noted on AA-821. | See §3. |
| AA-628 | Engagement feedback loop | parked |  | Park or cancel. |
| AA-839 | Erasure runbook + DRY RUN job for a traveller and an offboarded tenant | parked | Parked until ADR 0006 Phase 4 / before prod. | Approve creating it as a parked Low issue. |
| AA-842 | OTel gen_ai tracing investigation | parked | Report on Notion (Program Brain) + AA-CIS-App docs/investigations/llm-otel-tracing.md. | Decided S238: keep Backlog; build option B (gateway span, ~15–20 h) only when slow/unexplained jobs justify it |
| AA-864 | Research: consolidate all of acc2 (services, data, connections) on acc3 or one designated account — complexity, cost, time | later | Seed notes on the issue. Do with AA-860 on the target account. | Pick the target account when the research is done. |

## 5. Closed in S243

- **AA-885 Done** (tenant portal on its own Vercel project `aa-cis-portal`, `portal.lumiguides.it.com`; CIS #832, Infra #197; prod smoke 24/24).
- Shipped and live, still In Progress until Done-when is re-checked: **AA-858** (CIS #839/#840/#848, Booking #37, TP #98, Infra #205), **AA-884** (CIS #835/#836/#837/#838/#848, Infra #206/#209), **AA-680** staff (Booking #34/#35/#36, Infra #199), **AA-878** (root #101, CIS #841, Infra #195/#207, TP #99, 4 orphan secrets deleted).
- **AA-816:** Cognito E2E (CIS #842, Infra #198) + temporary E2E staff exception (CIS #849 mig 250, Infra #215/#216, root #106 ADR 0006a A10); break-glass OTP probe (Infra #196); daily reconcile trigger (Infra #195). Cutover still open.
- **AA-860 / AA-852:** X1 S15–S19 (CIS #833/#834/#843/#845, Infra #200/#201/#202/#203/#204/#214, root #99/#100).
- Chore row closed: stale Terraform `import` blocks removed (Infra #195), `middleware.ts` → `proxy.ts` (CIS #831); `use_lockfile` stays as row 10.
- Docs: unified engineering handbook, role guides (bilingual), runbooks, data standards v1.1 (root #105); schema reference regenerated (root #102/#103/#104). PR templates + title checks in all repos; Dependabot config in Booking (#43) and TripPlanner (#101); Dependabot PRs merged: Booking #38/#40/#44, TP #102 (open: Booking #39 superseded by #40, TP #104 → §3 row 5).
- Jira: Epic PR-20 + Story PR-21 (platform report period 1) posted. Google Safe Browsing review of lumiguides.it.com passed (19/10): the §1 check is removed.
- New backlog items without a Linear issue yet: §3 rows 4, 5, 12, 13 (ask Nghiệp before creating issues).

## 5a. Closed in S242

- **AA-854 Done** (Cognito Phase 0: break-glass, email-code spike, no-group deny, self sign-up rejected; evidence `docs/audits/2026-10-18-S242-cognito-phase1/`).
- **AA-816** shipped (In Progress until cutover): Infra #183/#184/#185/#191/#194, CIS #807/#808/#809/#810/#811/#812/#813/#826/#827/#828/#829, mig 247.
- **AA-852** X1 S9–S14 shipped (Booking #33, TP #97, root #95, Infra #179/#180/#182/#187/#188/#189/#190).
- Dependabot cleared in all repos (CIS #814/#819/#820/#830, Infra #192/#193 — AWS provider 6.69.1); CIS `dependabot.yml` groups security updates.
- AA-869 confirmed Done (S241). New issue: none.

## 5b. Closed in S241

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

- ECS CIS api :703 / worker :260 (X1 S18: `DATABASE_URL` = `cis_app`, secret `aa-cis/dev/rds-cis-app`); CIS migrations up to **250**; Booking bk-017; TripPlanner tp-015; roles rl-001. Terraform acc2 on **AWS provider 6.69.1** (v5 state version kept for rollback).
- **DB access after X1 S19:** ECS exec scripts use the container `DATABASE_URL` (`cis_app`: CIS schemas incl. RLS tables, no `booking.*` / `tripplanner.*`, no DDL). The CIS task role is denied `GetSecretValue` on the master `aa-cis/dev/rds`, `aa-cis/dev/db-migrator`, `booking/*`, `tripplanner/*`. Work that needs the master goes through DB Migrate `mode=run-script` (`docs/ops/runbooks/ecs-exec-s3-mediated.md`, `skill/aa-cis-schema/references/ecs-exec.md`).
- **Identity:** staff sign-in = https://staff-auth.lumiguides.it.com (Cognito custom domain, AA branding in Terraform) for CIS and Booking (shared managed-login session, each app checks its own role). Legacy password login still on. Break-glass `admin@adventure.asia` disabled, TOTP in Secrets Manager. Temporary E2E staff `e2e@e2e-mail.lumiguides.it.com` (reviewer, ADR 0006a A10). Tool `tools/identity/workforce_bootstrap.py` (Infra).
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
