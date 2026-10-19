# S243 cross-lane critique (8 lanes)

I checked this read-only against the repos on 19/10. Heads: CIS af1bd84a, Infra 715dfd1, Booking 6182045, TP 18341d8. No lane file was edited.

## (3) Factual errors and wrong assumptions found

1. **Blocker for AA-680 S1: `catalog.v_staff_identity` cannot be applied this session.**
   - Backlog line 13 and the Infra runner freeze catalog view DDL until X1 S22 (`CATALOG_VIEW_DDL_RE` / `CATALOG_FREEZE`, infra/AA-CIS-Infra/db/run_migration.py:362-374).
   - The plan's `GRANT catalog_owner TO CURRENT_USER` is a role-membership GRANT. The role lint forbids that (run_migration.py:76-83).
   - The runner's reach check refuses at `check` time, because the master is not a member of catalog_owner.
   - The lane says this can be decided later. It is a hard blocker. Options for Nghiệp:
     - (a) put the view in CIS-owned `shared` (`shared.v_staff_identity`) plus `GRANT USAGE ON SCHEMA shared TO booking`. The `booking` login today has USAGE on catalog, booking and tripplanner, not shared. **Recommended.**
     - (b) a CIS HTTP lookup endpoint.
     - (c) wait for S22.
   - The AA-858 lane got the freeze right ("No catalog.* view change").

2. **Migration number collisions.**
   - CIS 248 is claimed by 3 lanes: AA-680 (staff identity view), AA-884 (audit chain) and AA-878 (viewer enum). AA-858 claims none.
   - Booking bk-016 is claimed by 2 lanes: AA-680 (cognito columns) and AA-858 (ops views). AA-858 S1 already says to "take next free".
   - Live heads: CIS 247 (244-246 reserved for X1), bk-015, tp-014.
   - Recommended assignment:
     - CIS: 248 = AA-680, 249 = AA-884, 250 = AA-878.
     - Booking: bk-016 = AA-680, bk-017 = AA-858.
     - TP: tp-015 = AA-858.
   - Knock-on edits: AA-884 `REQUIRED_CIS_SCHEMA` and the /health/ready threshold must follow its final number. That check must also compare only numeric versions, because `schema_versions` also holds `bk-*`, `tp-*` and `rl-*` rows.

3. **The A8 AdminCreateUser alarm is built twice**: AA-816 I-B and AA-680 S0, same file identity_alerts.tf, different resource names. Keep AA-816 I-B (`aa-identity-dev-workforce-admincreateuser-password`) and drop AA-680 S0. AA-680 S2 then waits only on I-B being applied.

4. **AA-878 misses a bootstrap MFA apply.**
   - `tf_plan_secret_arns` (cicd_split.tf:86-93) is the Resource of `aws_iam_role_policy.tf_plan` (:496). tf_plan is a bootstrap role that the CI apply role cannot write (DenyRoleWritesOutsideStack, :168).
   - So I1 (drops `var.secret_admin_arn`) and I2 (drops the mapbox/acp ARNs) both need a local MFA targeted apply, like chore A2. Otherwise Terraform Apply errors on that resource.
   - I2 must also drop those ARNs in the same PR, because their `aws_secretsmanager_secret.tripplanner_mapbox.arn` references break once the resources are `removed`.

5. **AA-858 vs AA-884 contradict each other on who owns cost and health.**
   - AA-858 says it owns `api/services/ops_overview/cost.py` and that AA-884 drops scope item 4.
   - AA-884 says it owns `platform_cost.py` / `platform_apps.py` and that AA-858 imports them.
   - They also attribute AI spend differently: AA-858 uses the stage prefix `tp_`, AA-884 uses `quality_signal->>'app'`. AA-858 is wrong that there is no app column: `shared.llm_call_daily.app` exists (schema ref :2550) and TP writes `{"app": APP}` (TP backend/shared/llm_gateway.py:512). The two pages would show different numbers.
   - **Resolution:** AA-884 owns one cost module (stored CE snapshot + `llm_call_daily.app`). AA-858's cost card reads it and does a lazy refresh only when the snapshot is older than 24 h, behind a SET NX lock. AA-858 keeps CloudWatch health, the TP/Booking views and the overview page. Build AA-884 backend PR C first. Neither lane edits the other's files.

6. **"Next 17" in the session proposal is wrong.** CIS frontend is next 16.4.2, and proxy.ts is the Next 16 convention. Booking (16.2.4) already uses proxy.ts. TP is on 14.2.15, so defer it, as the chore lane says.

7. **The X1 FORCE-RLS correction (AA-860 lane) is credible.** The schema ref shows 8 `RLS on + FORCE` tables owned by aa_cis_admin. aa_cis_admin is not a superuser itself but is a member of rds_superuser, and the AA-817 probe evidence matches. Accept the corrected 244 with parity policies.

8. **Other claims checked and found correct:**
   - group names in identity.tf:135-142, including `booking-content_creator`;
   - Booking dev port 3100 vs callback localhost:3001;
   - cis-portal placeholder URLs (identity_variables.tf:163-165);
   - `_PATHS` / `_ALLOWED_PATHS` (handler.py:56-63);
   - `secret_id` on both schedules (dfs_balance.tf:234, :268);
   - ADMIN_SECRET plaintext (dfs_balance.tf:161);
   - 5 import blocks exist (identity.tf:817, observability_ecosys.tf:74/79/93, bedrock_satellite_assume.tf:15);
   - CI TF 1.7.5;
   - 7 test files DELETE from audit_log (the exact list AA-884 gives);
   - deploy-dev paths include `frontend/**`;
   - `STAFF_PATH_PREFIXES` / `_is_valid_secret` exist (staff_authz.py:302, :478);
   - the execution-role secret pattern `aa-cis/dev/*` covers `rds-cis-app` (main.tf:197);
   - `secret_rds_arn` feeds only api and worker DATABASE_URL (modules/ecs/main.tf:399, :601);
   - the SES receipt API answers in us-west-1 (`list-receipt-rule-sets` → `[]`).
   - Small error: AA-878 says AA-816 adds a new `aws_scheduler_schedule`. It does not; it adds only a `_PATHS` line.

## (1) File and resource collisions, and how to serialize them

**Infra:**

| Shared file or resource | Lanes involved | How to handle |
|---|---|---|
| lambda_src/dfs_balance_check/handler.py + dfs_balance.tf | AA-816 I-A, AA-878 I1 | **One PR** |
| cicd_split.tf | chore A1 (tf_plan grant), AA-878 I1/I2 (tf_plan_secret_arns), AA-816 I5 (apply-role SES grants), optional AA-878 I3 role | Bundle the bootstrap parts into one MFA sitting |
| identity_alerts.tf | AA-816 I-B, AA-680 S0 | Drop AA-680 S0 |
| identity.tf | chore A1 | Alone |
| identity_variables.tf | AA-885 S2 | Alone |
| observability_ecosys.tf | chore A1 (drops imports), AA-860 S18a/S20 (alarms) | Serialize |
| modules/ecs/main.tf | AA-858 S4 (infra_status_readonly), AA-860 S19 (ecs_task_policy Deny) | Serialize |
| main.tf:185 | AA-860 S18 | Alone |
| db/migrations/{cis,booking,tripplanner}/ + owners.yaml | AA-680, AA-858, AA-884, AA-878, AA-860 | Copy Guard: one copy PR per migration, merge and apply one at a time |
| Terraform Apply workflow (applies all of Infra main) | every Infra lane | Rule: one Infra merge at a time, each followed at once by its apply. Never merge AA-860 S18a early. |
| CI TF version bump (chore B) | every open Infra branch | Do it last this session, or next session |

**CIS app:**

| Shared file | Lanes involved | Notes |
|---|---|---|
| frontend/middleware.ts | chore C (rename), AA-885 S4c (strip portal) | The lanes disagree on order. Do **chore C first** (XS, merges in about an hour); AA-885 branches after it and edits proxy.ts. |
| Chore C comment sweep | AA-885 (moves the same files) | The sweep touches `app/_brand/tokens.ts` (which AA-885 byte-vendors), `(tenant)/portal/**`, `api/auth/tenant-login`, `lib/auth-server.ts`. If chore C goes second, the sweep breaks the AA-885 byte guard. |
| frontend/lib/rbac.ts | AA-885 (drops 'tenant', /portal rule), AA-878 C1 (adds 'viewer') | AA-878 after AA-885 |
| frontend/lib/apps.ts | AA-885 (PORTAL_BASE_URL), AA-884 PR D (APP_REGISTRY) | AA-858 only imports it |
| app/_kit/adminNav.tsx | AA-884 PR D, chore comment sweep | |
| AA-885 vendored kit files (`_kit` tokens/primitives/Modal/Drawer/Toast/api/useMediaQuery/Providers, `_brand/tokens.ts`, `lib/bffPath.ts`, `lib/proxyResponse.ts`) | any lane editing them after AA-885 | Must also copy into `portal/` |
| api/core/staff_authz.py + tests/unit/snapshots/aa882_staff_route_policy.json | AA-858, AA-884, AA-878 | Each regenerates the snapshot: strictly serial merges with a rebase |
| api/main.py | AA-884 (/health, /health/ready, middleware, router), AA-878 (booking-token viewer refusal) | AA-680 PR-4 deferred |
| shared/aws_client/cost_explorer.py, admin_llm_ops.py | AA-884, AA-858 | Resolved by finding 5 |
| tests/e2e/smoke/ui-smoke.spec.ts | AA-885 (moves portal block out), AA-884 (adds entries), AA-878 (viewer mode) | Order: AA-885 → AA-884 D → AA-878 C1 |
| playwright.config.ts | AA-816 E1 (`cognito` project), AA-885 (`smoke-portal` + testIgnore regex) | Serialize |
| tests/integration/conftest.py | AA-860 S16a (cis_app password) | Must not overlap other conftest edits |
| test_aa816_*.py teardown | AA-884 PR A | No other lane edits them now |
| CONTEXT.md (CIS) | all CIS lanes | Each edits only its own section; merge serially; AA-816 C-S1 last |
| Booking | AA-680 S2 (bk-016) and AA-858 (bk-017) both edit migrations/ and CONTEXT.md | AA-680 S3 must not edit CONTEXT.md |
| Root | backlog, sessions, ADR README, ecosystem-architecture.md, schema-ownership.md, x1-plan.md, db-schema-reference.md (one dump PR per apply) | One root PR per lane batch, merged by hand. Each schema-dump PR merged before the next apply. |
| Vercel | aa-cis-frontend (chore C, AA-885, AA-858 S6, AA-884 D, AA-878 C1), new aa-cis-portal (AA-885), aa-booking-admin (AA-680 S3) | Estimate 30-40 new deploys plus baseline 19-27/day, under ~100. Keep 2-3 pushes per FE PR, local build first. |
| ECS deploy gate | every CIS PR touching api/ shared/ services/ frontend/: about 11 rolls this session | Strictly one at a time. Evidence calls that enqueue jobs block the next deploy: AA-816 reconcile schedule, AA-878 V-I1 retention schedule, AA-884 reconcile POST. Run them only right after a deploy, never just before a merge. |

## (2) Dependency order

- **AA-816 cutover S1 (Production BFF legacy off) must come after every production-domain verification that uses the legacy e2e login:**
  - AA-858 S12 (Playwright on aa-cis prod);
  - AA-884 S7 screenshots/curls;
  - AA-885 admin regression;
  - chore C2 `ui-smoke -f base_url=prod`;
  - AA-878 V-C1 ("legacy form still on").
  - Otherwise those lanes must verify on Preview. Add this as a sixth precondition to N5.
- **AA-878 E2E_ADMIN_* → viewer (N1)** goes after AA-884 PR D and AA-858 S6 smoke entries exist and are marked admin-only (viewer mode refuses them), and after AA-885's smoke move. It is the last CIS smoke change.
- **AA-878 E2E account vs AA-816:**
  - the viewer row is a new legacy-only exception at cutover readiness (`e2e-claude-code-viewer` matches the `e2e-claude-code*` S2 disable rule);
  - AA-816 reconcile and readiness must serialise role `viewer` (C1 step 5 covers it; test it).
  - The Preview ADMIN_SECRET swap moves to AA-816 C9/S2.
- **AA-885 before** chore-free CIS FE lanes (AA-884 D, AA-858 S6, AA-878 C1); chore C before AA-885.
- **AA-884 backend PR C** before AA-858 backend S5 (finding 5). AA-858 Booking/TP views, Infra IAM and FE design can run in parallel.
- **AA-680:**
  - I-B applied, then the CIS view (reworked per finding 1) applied, then bk-016 applied, then Booking S2 merge, then the REQUIRED_SCHEMA_VERSIONS bump, then S3 (after Nghiệp sets the Vercel secret).
  - AA-816 N3 and AA-680 S4n are the same action ("set own Booking role"): do it once, before S2 goes live.
- **AA-860:**
  - 244 is numeric-before 248-250, but on Dev it is applied after them. The `GRANT ON ALL` covers objects created earlier and the default privileges cover later ones. CI replays in numeric order, so the X1 tests must model the Dev order.
  - S16 guard "every RLS table has a policy TO cis_app": none of the 248-250 or bk-017 files create RLS tables. Keep it that way.
  - **S18 needs a CIS merge freeze**, so it goes after all other CIS merges this session.
  - **S19 Deny on `aa-cis/dev/rds`** breaks every S3-mediated ECS-exec script that reads the master secret: AA-816 S0 readiness, AA-878 M3/M4, AA-884 S7 tamper test, AA-858 verification. So S19 is absolute last, or next session.
  - **AA-858 verification 1** (direct `booking.trip_cases` / `tripplanner.*` counts from the CIS container) fails after S18 (cis_app → 42501). Run it before S18, or through DB Migrate run-script.
  - 245 (next session) must cover the new objects from 248-250: AA-884 triggers and the cost snapshot table, the AA-680 view, the AA-878 enum.
- **chore:** A (imports + tf_plan lockfile grant) → local MFA apply → B (use_lockfile + TF 1.15.5). B forces every open Infra branch to rebase, so schedule it after all other Infra merges.

## (4) Missing steps or verification

- **AA-878:**
  - the T1 TripPlanner PR merge is Nghiệp's (missing from its list);
  - I1/I2 local MFA applies (finding 4);
  - the register drift check must run at the very end, because this session adds secrets: VERCEL_PORTAL_BYPASS_SECRET, E2E_TENANT_API_KEY, E2E_MAIL_ROLE_ARN (`e2e` env), COGNITO_BOOKING_STAFF_CLIENT_SECRET (Vercel aa-booking-admin), aa-cis/dev/e2e-test-viewer, and the aa-cis-portal Vercel project.
- **AA-680:**
  - after the rework, add `GRANT USAGE ON SCHEMA shared TO booking`, the owners.yaml consumer_grant and an isolation-probe cell;
  - a schema-ownership.md amendment (the "no other app reads admin_users" rule).
- **AA-884:**
  - grep that no FK cascade reaches audit_log from conftest's `TRUNCATE … CASCADE` (conftest.py:420; the statement trigger would fire);
  - inventory every audit-insert call site for long transactions before the advisory-lock chain ships.
- **AA-885:** list the 11 vendored files in CIS CONTEXT.md, so later lanes know to copy them.
- **AA-858:** state in its notes that the cost card is built on AA-884's module.
- **AA-816:** none beyond the extra N5 precondition. One sequencing rule: the OTP probe and the N2 break-glass test both enable and disable `admin@`, so they must never overlap.
- **All lanes:** one notes file per PR. This is already in most plans; enforce it for AA-884 and AA-858.

## (5) Recommended execution schedule

The main session caps at 3 heavy builders (S237 WSL lesson). The CIS merge and deploy queue is the bottleneck, not build time.

**Wave 0 (main session, before any builder):**
1. Announce the migration numbers (finding 2) and file ownership (finding 5).
2. Get Nghiệp's decisions D1-D6 (section 6).
3. AA-816 S0 readiness SQL (it reads the master secret, so it runs before any S19).
4. AA-885 S0 Vercel project and domain.
5. AA-878 M0 inventory (first pass).
6. Linear comments for AA-816/AA-680 Done-when.

**Wave 1 (3 builders):**
- **B1:** chore C (CIS proxy rename). Merge first.
- **B2:** Infra PR-1, the bundle of AA-816 I-A + AA-878 I1 + chore A1 (stale imports + tf_plan lockfile grant + `tf_plan_secret_arns` shrink). Then Infra PR-2: AA-816 I-B (A8) + I-C (OTP probe).
- **B3:** AA-680 S2, Booking backend bk-016. Independent repo.

**Main session between waves:**
1. **MFA sitting #1** (Nghiệp): targeted apply of `aws_iam_role_policy.tf_plan`, then Terraform Apply for PR-1.
2. Lambda invoke evidence with `paths` set.
3. Apply PR-2; OTP probe run (Cognito toggle).

**Wave 2:**
- **B1:** AA-885 PR-B (CIS portal split, L). Start S4a now (new dir); the S4b/S4c edits sit on top of chore C.
- **B2:** AA-885 PR-A infra (CNAME + client URLs), then AA-816 I5 SES mailbox. MFA sitting #2 covers the I5 CI grants.
- **B3:** AA-680 CIS view migration (CIS 248 as reworked) + Booking S3 UI.

**Main session:**
1. Apply 248 → bk-016 → merge Booking S2 → bump.
2. AA-885 merge after PR-A is applied.
3. AA-816 E1 (tests only, no deploy).

**Wave 3:**
- **B1:** AA-884 PR A (249 + test teardowns) → PR C backend.
- **B2:** AA-858 Booking bk-017 + TP tp-015 views + IAM PR B.
- **B3:** AA-860 S15a/S15b + S16a (244, migration-only).

**Main session:**
1. Apply 249 and 244 (separately, each with its schema-dump PR).
2. AA-884 C deploy.
3. Nghiệp merges tp-015.
4. AA-858 Infra copies/apply.

**Wave 4:**
- **B1:** AA-884 PR D.
- **B2:** AA-858 S5 backend (on AA-884's module), then S6 FE.
- **B3:** AA-878 T1 (TP) → I2 (MFA sitting #3, or fold into #2 if T1 is ready) → C1 viewer (250).

**Main session:**
1. Production-domain verification for AA-858, AA-884, AA-885 and chore C, using the legacy e2e login.
2. AA-878 M2 orphan DRY RUN → deletes.
3. AA-878 M3 viewer secret and row.
4. Nghiệp N1 smoke swap.

**Wave 5 (end):**
1. AA-816 N2 break-glass, N4 Thư, N3 Booking role (done earlier if possible).
2. Cutover S1 (N5) + C-S1 docs.
3. AA-860 S17 (Nghiệp DSN) → set-password → probe.
4. **Cut line:** AA-860 S18 (freeze window) and S19 (Deny) only if every other CIS merge is done. Otherwise first thing next session. S19 last in any case.
5. chore B (TF 1.15.5 + use_lockfile) after the last Infra merge, or next session.
6. AA-878 final register diff = 0, access review.
7. Root PR(s).

**Realism:** 8 lanes, about 35 PRs and about 11 ECS rolls is far beyond the 3-5 issue session norm. If time runs out, cut in this order: AA-860 S18-S19 → chore B → AA-878 C1 + N1 → AA-858 S6 FE. The rest fits one long session.

## (6) Items that need Nghiệp, consolidated

**Decisions:**

- **D1 (AA-680):** the catalog view is blocked by the X1 freeze. Pick:
  - (a) `shared.v_staff_identity` + USAGE on shared for `booking` (recommended);
  - (b) CIS HTTP lookup;
  - (c) wait for S22.
  - Also allow Booking reading CIS staff identity at all (schema-ownership change).
- **D2 (AA-885):**
  - domain `portal.lumiguides.it.com`;
  - staff lose direct access to the tenant portal;
  - keep the `/portal/*` prefix;
  - which URLs /privacy and /terms point to (no legal text gets written).
- **D3 (AA-860):**
  - amend Done-when (1) to the parity wording;
  - agree the S18 freeze window, or move S18/S19 to next session;
  - review the main.tf:185 one-liner.
- **D4 (AA-878):**
  - UI smoke option (a) viewer, recommended, or (b);
  - OK the orphan DRY RUN list;
  - keep or disable e2e-claude-code-2;
  - Preview ADMIN_SECRET swap → AA-816 C9;
  - is AA-ACP-Core really archived;
  - follow-up issue for the task role's GetSecretValue on `*`.
- **D5 (AA-816):**
  - move "Booking JWT role sales" to AA-680;
  - cutover S1 go with A6 option 1, after the production-domain verifications above.
- **D6:**
  - chore issue reference (`Refs AA-816` or a new chore issue);
  - new follow-up issues (AA-885 /trip move, TP Next 16 upgrade, X1 GUC-aware policies, AA-858 metric filter): ask before creating any.
- **Later, no block:** AA-858 UTC vs ICT day boundaries; a daily CE refresh schedule.

**Manual actions:**

- Break-glass `totp_seed` into an authenticator (the console read sends an alert by design), then the managed-login sign-in.
- Mail forwarder `e2e-cognito@adventure.asia` → `e2e@e2e-mail.lumiguides.it.com` in the MailChannels host panel (not Google Workspace), then create staff user "E2E Cognito" (reviewer).
- Set your own Booking role on Platform → Staff: **one action** that serves AA-816 N3 and AA-680 S4n. Then the Booking company-email sign-in proof.
- Ask Ms. Thư to sign in, and later to review /admin/overview.
- Merge the TP PRs: AA-858 tp-015 and AA-878 T1.
- Revoke the old Mapbox geocoding token in the Mapbox account.
- Fill the vendor rows in the secrets register.
- After S19, edit `~/.claude/CLAUDE.md` (DB connection section) yourself.
- Approve the Jira drafts, batched at session end.
- ⚠️ **This contains underscore env vars — edit manually in VSCode / dashboard:**
  - Vercel Production `LEGACY_ADMIN_LOGIN_ENABLED=false` (cutover);
  - Vercel aa-booking-admin `COGNITO_BOOKING_STAFF_CLIENT_SECRET`;
  - GitHub AA-CIS-App secrets `VERCEL_PORTAL_BYPASS_SECRET`, `E2E_TENANT_API_KEY`;
  - `E2E_MAIL_ROLE_ARN` (env `e2e`; the main session sets it, flagged here);
  - the values of `E2E_ADMIN_USERNAME` / `E2E_ADMIN_PASSWORD` → viewer;
  - Secrets Manager `aa-cis/dev/rds-cis-app` DSN (S17), optional `aa-cis/dev/db-migrator`;
  - optional Sentry vars on aa-cis-portal.

**Auto-mode toggles and MFA, batched:**

- **MFA sitting #1:** `tf_plan` bootstrap (chore A1 + AA-878 I1).
- **MFA sitting #2:** AA-816 I5 CI grants, plus AA-878 I2's `tf_plan` shrink if ready, plus the A8 events grant if the CI role lacks it.
- **Cognito writes:** enable/disable for the OTP probe and break-glass (never at the same time).
- **Secrets Manager writes:** 4 deletes with a 30-day window, create e2e-test-viewer.
- **Terraform Apply** prod-environment approvals: AA-885 Cognito client, AA-858 IAM.
- `aws sso login --profile pqnghiep-admin` for chore B.
- Any deploy-gate override stays your call only.

**New costs (monthly):**

| Lane | Cost | What |
|---|---|---|
| AA-816 | ≈ $0–0.05 | SES inbound + 1-day S3 + R53 record + IAM role; one more Cognito MAU, inside the free tier |
| AA-885 | $0 | 4th Vercel Hobby project, CNAME in the existing zone |
| AA-680 | $0 | PR-4 later saves −$0.40 |
| AA-858 | ≤ $3 worst case | GetMetricData ≤ $0.60, CE ≤ $1.80, realistic < $1; drops to ~$0.30 once it reuses AA-884's stored snapshot |
| AA-884 | ≤ $0.20 | $0.01 per CE refresh |
| chore | ≈ $0 | S3 lockfile objects; DynamoDB lock table kept |
| AA-860 | ≈ $0.40 | Alarm + log-metric filter; +$0.10 if S20 runs |
| AA-878 | ≈ −$1.20 net | −4 orphan secrets, +1 viewer secret |
| Already spent in planning | ≈ $0.03 | CE probes |
| **Net** | **about +$0.5 to +$2.5/month worst case** | No new compute and no LLM spend |