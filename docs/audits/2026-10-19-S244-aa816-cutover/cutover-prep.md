# AA-816 — Cognito Phase 1 cutover (Stage S): preparation plan

Plan only (S244, 19/10/2026). Nothing in this file has been run: no data was written, no flag was changed, no
secret was touched. Design sources: root ADR 0006 + amendment 0006a (A4 break-glass, A6 split flag, A9 header trust,
A10 E2E mailbox exception), the S242 Phase 1 plan (Stage S: C9, I6), the root runbooks `legacy-login-flag.md`
(OPS-06-legacy-login) and `break-glass.md` (OPS-10), and the root secrets register (open items 1, 4, 7).
Pool and client ids, account ids and ARNs are still looked up at run time below rather than copied (they can change).

Where this lives: written in the AA-CIS-App lane, moved to the private root repo in review (S244): it is a security
and cutover report (staff rows, break-glass state, a live legacy password hash), which the public app repos must not
carry (DM-6.10, D-25, AA-CIS-App `.claude/CLAUDE.md`). The sign-out code notes stay in AA-CIS-App
`docs/implementation-notes/AA-816-logout.md`.

## Decisions

### Two cutover steps, not one (from ADR 0006a A6)
- **S1 — Production BFF flag off.** Only the CIS UI password form and BFF `/api/auth/login` on the production host
  go away. The API flag stays on, so Preview logins, Booking (`/auth/admin-login`, `/auth/booking-token`) and every
  machine caller keep working. Reversible in one Vercel redeploy. This is the runbook's recommended cutover (N5).
- **S2 — API flag off.** Ends the HS256 path of `/auth/verify-admin` for every host, Preview included. Only after
  AA-680 (Booking Phase 2) and after Previews have another way to sign in (see "What breaks", S2). Not proposed now.

### Readiness counts people, not test rows
The reconcile job's readiness block (`services/staff_reconcile.py readiness_from_rows`) lists every active row
without an email or a `cognito_sub`. For S1 the precondition the runbook states is narrower and correct: every active
row **a person uses** has an email and is either linked or cannot be locked out (no password). Test rows without a
person are decided one by one below and stay listed until S2; the readiness list is read with that table, not
"fixed" by giving test rows fake addresses (an address without a mailbox and a Cognito user only hides the row).

### Per account (active rows from the 19/10 read-only snapshot + the WORKFORCE user list)

| Row (username) | CIS role | Email / linked | Cognito user | Used by (found in code, docs, workflows) | Proposal |
|---|---|---|---|---|---|
| `admin` (break-glass) | admin | set / **not linked** | exists, **disabled**, TOTP enrolled | break-glass runbook OPS-10 A; Infra `workforce_bootstrap.py breakglass-verify` | **Keep.** Link it by the managed-login break-glass test (checklist B): the first sign-in links the row by email. Then clear its legacy `password_hash` (ADR 0006a A4 says NULL; the snapshot shows a hash, so `admin` + that old password still opens the legacy login on Preview and on the API) and rotate the break-glass password. Mailbox: none needed (password + TOTP; with TOTP enrolled no email code is offered, S243 probe). |
| `thu` (Ms. Thư) | admin | set / not linked | exists, enabled, CONFIRMED | a person | **Keep, no action for S1.** The row has no password, so the flag cannot lock her out; it links itself on her first email-code sign-in. Nghiệp dropped "Ms. Thư signs in" from the done-when (S243). Decision N-A below: accept "passwordless + email + Cognito CONFIRMED" as ready. |
| `nghiep` | admin, owner | set / linked | enabled | a person | Keep. Note: the row still has a legacy password, which Booking uses until AA-680; do not clear it before AA-680. |
| `e2e-claude-code` | admin (full CIS, Booking admin through the bridge) | **no email** / not linked | none | GitHub `E2E_ADMIN_*` → `ui-smoke.yml` on every PR preview (`tests/e2e/smoke/auth.setup.ts`, BFF `/api/auth/login` on the preview); root skill `aa-ui-verify` step 3 (secret `aa-cis/dev/e2e-test-admin`); agent Booking UI checks (Booking BFF → CIS `/auth/admin-login`); legacy live-verify specs `tests/e2e/aa5xx-*.spec.ts` (`helpers/auth.ts loginAsAdmin`) | **Keep as a Preview + Booking test account until S2, no Cognito identity.** It cannot get one: there is no agent-readable `@adventure.asia` mailbox, and the only mailbox exception (A10) is one reviewer address. First do AA-878 N1 (GitHub smoke → the viewer account), so this full-admin password stops being on every preview run. Disable it at S2 (Staff page, audited `staff.disabled`). |
| `e2e-claude-code-2` | admin (Booking checker) | **no email** / not linked | none | agent Booking maker-checker checks (second admin; root register, decision D4) | **Disable now** (Staff page; re-enable is one audited click when a maker-checker check is due). It is a second full-admin legacy password with no current user. Alternative if Nghiệp prefers: keep until AA-680, Preview + Booking only. |
| `e2e-claude-code-viewer` | viewer | **no email** / not linked | none (cannot exist: WORKFORCE has no `cis-viewer` group and the directory never assigns `viewer`) | `ui-smoke.yml` viewer mode after N1 (`smoke-helpers.ts isViewerRun`); agent read-only checks (secret `aa-cis/dev/e2e-test-viewer`) | **Keep, Preview only.** This is the intended CI smoke account. It needs a decision only at S2 (Preview login). |
| E2E Cognito row (`e2e@e2e-mail.lumiguides.it.com`) | reviewer | set / linked | enabled | `e2e-cognito.yml` (`tests/e2e/cognito/`) | Keep until the E2E work is finished; then the A10 removal steps. |

Inactive rows (`e2e-test-admin`, `s226_rev_ui`, `trang`) are not in the readiness count and need nothing.

### Order: S1 does not wait for C9 / I6
The S242 plan lists C9 → I6 → flag off; the root runbook (step 6) puts C9 + I6 after AA-680. Proposal: neither.
S1 is independent of them (the BFF still sends the secret either way), so do readiness → S1 → C9 + Preview
credential + I6 right after, without waiting for AA-680. The Preview god-key (register item 1) is the larger risk and
does not depend on Booking. Nghiệp decides (N-C).

## What breaks when the legacy password login is turned off

### At S1 (Production BFF flag off)
| What | Breaks how | Moves to |
|---|---|---|
| Password form + `POST https://aa-cis.lumiguides.it.com/api/auth/login` | 404; `/login` shows only "Sign in with company email" | Email code (everyone who uses production is linked or passwordless) |
| `ui-smoke.yml` dispatched by hand with `base_url` = the production host, and the `aa-ui-verify` local command `BASE_URL=https://aa-cis.lumiguides.it.com npx playwright test --project=smoke` | `smoke-setup` fails: "smoke login failed: … HTTP 404" | Run against a preview URL (the automatic path from `vercel-deploy.yml` is always a preview: unaffected). Root skill text to update (orchestrator, root repo). |
| Agent UI verify on production (`aa-ui-verify` step 3, `e2e-claude-code`) | no password form | Verify on the PR preview (legacy stays on there). After merge: Nghiệp signs in, or dispatch `e2e-cognito.yml` (reviewer pages only). Reading the mailbox locally would need a new S3 read grant — not proposed. |
| Legacy live-verify specs (`tests/e2e/aa5xx-*.spec.ts`, project `chromium`) against production | fail at the form | Point them at a preview, or retire them (historic one-offs). |
| New staff created with `scripts/create_staff_user.py` | the password row is useless on production | Retire the script at S1 (Linear title: "retire create_staff_user.py"); the Staff page creates Cognito users. Small code PR. |
| Live HS256 sessions already on production | **not ended**: the BFF does not re-check its flag on session verify and the API HS256 path is still on, so they last until JWT expiry (`JWT_EXPIRY_H`, 24 h) | Accept (Dev, a day), or a small BFF change: `proxy.ts` / `auth-server.ts` refuse an HS256 cookie while the BFF flag is off (N-D). Rotating `JWT_SECRET` would also end Booking bridge tokens: not proposed. |
| Not affected | ui-smoke on previews (Preview BFF flag stays on), `deploy-dev.yml` pre-deploy gate + post-deploy smoke and `deploy_job_guard.sh` (X-Admin-Secret on MACHINE_ROUTES, no login), the ops-probe Lambda (secret read by ARN at run time), Booking staff sign-in (`/auth/admin-login`, `/auth/booking-token` are not gated), `e2e-cognito.yml`, Ms. Thư (no password) | — |

### At S2 (API flag off, with or after AA-680)
- Every HS256 session on every host is refused by `/auth/verify-admin`. On a Preview the BFF login still gets a token
  from `/auth/admin-login` (not gated), but the verify that follows fails, so **`ui-smoke.yml` login fails on every
  preview** and agents lose Preview admin sign-in.
- Choices allowed by ADR 0006a A6 (Nghiệp's call, N-E): (a) keep the API flag on until a Preview sign-in exists;
  (b) "previews lose admin login": the PR smoke keeps only its unauthenticated specs (`aa816-*`, `aa656` forged
  cookie, …) and the authenticated smoke moves to production after merge through the Cognito E2E user (reviewer
  scope, `e2e-cognito.yml` pattern). A Preview-only test login would be a new design and needs an ADR amendment.
- Then: disable `e2e-claude-code` (and `-2` if kept); Booking stops using `/auth/admin-login` (AA-680).

## Tradeoffs
- Keeping test rows legacy-only until S2 leaves full-admin passwords usable on Preview and on the API for a while.
  Mitigation: N1 (GitHub smoke → viewer), disable `-2` now, and the Preview credential capped at viewer (C9), after
  which a legacy admin password on a Preview reaches only viewer rights through the BFF. The API's own
  `/auth/admin-login` still answers until S2.
- Capping Preview at viewer (C9) also means agents can no longer check admin **writes** on a Preview; those checks
  move to production after merge (Nghiệp, or a future Cognito test identity).
- Treating Ms. Thư's passwordless row as ready avoids blocking on a sign-in nobody can force; the risk is only that
  her first sign-in is also the first link (same path as every new staff member).

## Should know
- `scripts/link_staff_identity.py` reads the RDS master DSN from Secrets Manager; since X1 S19 the CIS task role is
  denied that secret, so the script fails from the container. Any further use goes through DB Migrate `run-script`
  or needs a small change to read the container `DATABASE_URL` (`cis_app` has DML on `shared`). It never writes
  `password_hash`, so clearing the break-glass hash needs its own audited step (checklist B6, N-B).
- Directory writes on rows without an email (disable, enable) change the DB only and are audited (C6), so disabling
  test rows needs no Cognito call and no script: an owner does it on the Staff page.
- The managed-login break-glass sign-in is also the step that links the `admin` row (first-link by email, A7); the
  link happens only if the `breakglass` client token passes `/auth/verify-admin` (role from `cis-admin`).
- Cost of everything below: 0 USD except the Preview secret (one Secrets Manager secret, about 0.40 USD a month).

## Decisions needed from Nghiệp
- **N-A** Accept passwordless rows with an email and a CONFIRMED Cognito user (Ms. Thư) as cutover-ready.
- **N-B** Clear the break-glass row's legacy `password_hash`: through a reviewed DB Migrate `run-script`, or a small
  audited script option. Recommended: run-script (one row, audited in the same transaction).
- **N-C** Order: readiness → S1 → C9 + Preview credential + I6 (proposed), versus the runbook's "C9 + I6 with AA-680".
- **N-D** End live HS256 production sessions at S1 (BFF change) or let them expire (24 h).
- **N-E** At S2: API flag stays on until a Preview sign-in exists, or previews lose admin login.
- **N-F** `e2e-claude-code-2`: disable now (proposed) or keep until AA-680.

## Ordered cutover checklist

Every AWS / Cognito write below is for the orchestrator (MFA admin profile), single line, not run by this lane.
⚠️ Steps marked **HAND EDIT** touch env var or secret names with underscores (`ADMIN_SECRET`, `E2E_ADMIN_*`,
`LEGACY_ADMIN_LOGIN_ENABLED`): Nghiệp edits them by hand in the Vercel / GitHub UI (or VSCode for Terraform); no
command is written for them.

Lookups used below (read-only):
```bash
aws sts get-caller-identity --profile aa365-admin
POOL=$(aws cognito-idp list-user-pools --max-results 20 --profile aa365-admin --region us-west-1 --query "UserPools[?Name=='aa-workforce-dev'].Id" --output text)
```

**A. Before anything (no user impact)**
1. Merge the AA-CIS-App sign-out PR (branch `feat/aa-816-cis-cognito-logout`); after the production deploy, dispatch `e2e-cognito.yml` on `main`
   (`gh workflow run e2e-cognito.yml --repo AdventureAsia365-Ecosys/AA-CIS-App --ref main`). Expected: green, step 7
   shows the address form, then the code step, and a second code mail arrives.
2. Nghiệp answers N-A … N-F.
3. **HAND EDIT** (AA-878 N1): GitHub AA-CIS-App `E2E_ADMIN_*` → the viewer account's values
   (`aa-cis/dev/e2e-test-viewer`). Verify: the next PR smoke logs "logged in with staff role: viewer" and is green.
4. N-F: disable `e2e-claude-code-2` on the Staff page (owner session). Verify: audit row `staff.disabled`; readiness
   no longer lists it.

**B. Break-glass through managed login (precondition, ADR 0006 / OPS-10 A3)** — alert e-mails and the token alarm
are expected; record every step in the session log and on AA-816.
1. Enable:
   `aws cognito-idp admin-enable-user --user-pool-id $POOL --username admin@adventure.asia --profile aa365-admin --region us-west-1 # WRITE`
   Verify: `aws cognito-idp admin-get-user --user-pool-id $POOL --username admin@adventure.asia --profile aa365-admin --region us-west-1 --query Enabled` → `true`.
2. Nghiệp reads the break-glass secret in the Secrets Manager console (alert e-mail by design) and adds the TOTP
   seed to an authenticator if needed.
3. In a private window open `https://aa-cis.lumiguides.it.com/api/auth/signin/cognito-breakglass`; sign in with
   password + TOTP. Expected: lands under `/admin`; the Staff page shows the break-glass row read-only and readiness
   no longer lists `admin` as unlinked; the API log has `staff_identity_linked` for that row.
   Verify the alarm (read-only):
   `aws cloudwatch describe-alarms --alarm-names aa-identity-dev-breakglass-token-issued --profile aa365-admin --region us-west-1 --query "MetricAlarms[0].StateValue" --output text` → `ALARM`; the token log line names `client_id` `breakglass` (anything else is an incident).
4. Sign out from the Topbar. Expected: the browser passes through the managed-login `/logout` and lands on `/login`;
   opening the break-glass sign-in URL again asks for the password again (no silent sign-in).
5. Close:
   `aws cognito-idp admin-user-global-sign-out --user-pool-id $POOL --username admin@adventure.asia --profile aa365-admin --region us-west-1 # WRITE`
   then
   `aws cognito-idp admin-disable-user --user-pool-id $POOL --username admin@adventure.asia --profile aa365-admin --region us-west-1 # WRITE`
   Verify: `Enabled` → `false`; the alarm returns to `OK`.
6. N-B: clear the `admin` row's legacy `password_hash` (reviewed DB Migrate `run-script`, one row, with an
   `acp_shared.audit_log` row in the same transaction). Verify: the script's report shows `password_hash IS NULL`
   for `admin` (nobody needs the old password to check it); the legacy login code already answers 401 for a NULL
   hash (C1).
7. Rotate the break-glass password with AA-CIS-Infra `tools/identity/workforce_bootstrap.py breakglass-init` (MFA,
   writes the secret by `PutSecretValue` only), per the root secret-rotation runbook class 4.

**C. Readiness snapshot (read-only)**
1. Staff page → cutover readiness (or `GET /admin/platform/staff-directory/health` as an owner). Expected: the only
   rows listed are the agreed test rows (`e2e-claude-code`, `e2e-claude-code-viewer`, and `e2e-claude-code-2` if kept)
   and, per N-A, `thu`. Save it under the root `docs/audits/<date>-S<nnn>-aa816-cutover/`.

**D. S1 — Production BFF flag off** (root runbook OPS-06-legacy-login steps 2–5)
1. Code first (small PR): retire `scripts/create_staff_user.py`; N-D change if chosen.
2. **HAND EDIT**: Vercel `aa-cis-frontend`, Production target only, `LEGACY_ADMIN_LOGIN_ENABLED` = `false`; then a
   production redeploy:
   `gh workflow run vercel-deploy.yml --repo AdventureAsia365-Ecosys/AA-CIS-App --ref main -f target=production`
3. Verify: `curl -s -o /dev/null -w "%{http_code}\n" -X POST https://aa-cis.lumiguides.it.com/api/auth/login` → `404`;
   one staff member signs in with the email code; the API log has `staff_bearer_verified`; a PR preview's smoke is
   still green (Preview flag untouched).
4. Rollback at any time: **HAND EDIT** the Production value back to `true` (or delete it), redeploy as in D2.
5. Root follow-ups (orchestrator): `aa-ui-verify` skill text (production login → preview or Cognito), runbook tested log.

**E. C9 — principal-aware admin-secret check + Preview credential (CIS code PR, then secrets)**
1. CIS PR (risky: auth → independent review first):
   - `verify_admin_secret` (`api/routers/admin.py`) and its variants (`admin_settings.py`, `v1_pipeline.py`,
     `core/staff_secret.py`, `admin_atoms.py`) accept a request whose `current_staff` contextvar holds a verified
     Cognito principal without the secret; the five BFF proxies stop sending `X-Admin-Secret` for a Cognito session.
   - A second, Preview-only credential: the API reads it from Secrets Manager **by a code-constant name** (no new env
     var), and a match yields a principal capped at `viewer` (a higher `x-admin-role` is lowered; never the machine,
     so MACHINE_ROUTES refuse it).
   - Machine callers (CI deploy gate/smoke, ops-probe Lambda) keep the main secret unchanged.
   - Tests: Cognito Bearer without the secret → allowed by policy; Preview secret + `x-admin-role: admin` → viewer
     rights only; Preview secret on a MACHINE_ROUTE → 403; main secret unchanged.
2. After merge + deploy, create the Preview secret (about 0.40 USD a month). The name is the code constant from E1;
   the register proposes `aa-cis/dev/admin-secret-preview`:
   `aws secretsmanager create-secret --name aa-cis/dev/admin-secret-preview --description "AA-816 C9 Vercel Preview BFF credential, capped at viewer" --secret-string "$(aws secretsmanager get-random-password --password-length 48 --exclude-punctuation --query RandomPassword --output text --profile aa365-admin --region us-west-1)" --profile aa365-admin --region us-west-1 # WRITE`
   (or a Terraform container in AA-CIS-Infra plus `put-secret-value`, if Nghiệp wants it in code).
3. **HAND EDIT**: Vercel `aa-cis-frontend` Preview `ADMIN_SECRET` → the Preview secret's value (Production keeps the
   main secret). Redeploy one preview (`gh workflow run vercel-deploy.yml --repo AdventureAsia365-Ecosys/AA-CIS-App --ref <branch> -f target=preview`).
   Verify: the preview smoke (viewer) is green; an admin-only write through that preview answers 403.

**F. I6 — rotate the main admin secret**
1. Check `shared.job` is idle (Jobs page or the Deploy Dev job guard), as for any api/worker restart (DM-11.4).
2. Confirm the secret is a plain string (the task definitions map it whole, no JSON key), then:
   `aws secretsmanager put-secret-value --secret-id aa-cis/dev/admin-secret --secret-string "$(aws secretsmanager get-random-password --password-length 48 --exclude-punctuation --query RandomPassword --output text --profile aa365-admin --region us-west-1)" --profile aa365-admin --region us-west-1 # WRITE`
3. Restart both services so new tasks read the new value:
   `aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-api --force-new-deployment --profile aa365-admin --region us-west-1 # WRITE`
   `aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-worker --force-new-deployment --profile aa365-admin --region us-west-1 # WRITE`
   `aws ecs wait services-stable --cluster aa-cis-dev-cluster --services aa-cis-dev-api aa-cis-dev-worker --profile aa365-admin --region us-west-1`
4. **HAND EDIT** at once (the admin UI answers 403 between 3 and 4, a few minutes on Dev): GitHub AA-CIS-App
   `ADMIN_SECRET` and Vercel `aa-cis-frontend` Production `ADMIN_SECRET` → the new value; production redeploy as in D2.
   Nothing to do for the ops-probe Lambda (it reads the secret by ARN at run time).
5. Verify:
   `curl -s -o /dev/null -w "%{http_code}\n" -H "x-admin-secret: $(aws secretsmanager get-secret-value --secret-id aa-cis/dev/admin-secret --query SecretString --output text --profile aa365-admin --region us-west-1)" https://api-cis.lumiguides.it.com/admin/job-runner/summary` → `200`
   (a machine route); the next Deploy Dev smoke is green; the next ops-probe run logs no `admin_secret_unavailable`
   or 403; an admin page on production loads. Update the root secrets register (`last_changed`, items 1 and 7).

**G. Later (S2, with AA-680)** — N-E; API flag off (Infra task-definition env, **HAND EDIT** in VSCode); disable
`e2e-claude-code` (and `-2`); the A10 E2E exception removal when the E2E work is finished.
