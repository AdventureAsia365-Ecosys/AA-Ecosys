# Area 2 — CI/CD pipelines and release flow

Scope: AA-CIS-App, AA-Booking, AA-TripPlanner-Web, AA-CIS-Infra, root AA-Ecosys. Read-only, 17/10/2026.
Sources: workflow files from each repo's default branch via gh api (local checkouts were behind: CIS/TP vercel-deploy.yml only on remote main; Booking's vercel-deploy.yml only on branch chore/s241-vercel-ci-deploys); GitHub settings and run history (GET); AWS describe/list on acc2. IAM reads blocked by the subagent hook → OIDC trust read from Terraform.

Synthesis verification notes (`../README.md` §8.3): the "204 Dependabot alerts on CIS" claim below could NOT be reproduced (API returns 0 alerts, all states); terraform-apply.yml line refs on `a6605ce` = origin/main are key L48, apply L77-78, environment L18; CIS deploy-dev.yml has no `concurrency` (confirmed).

## Workflow map (observed)

- **AA-CIS-App** (public)
  - ci.yml (PR to main, push main + feature/**): Lint (flake8), Security Audit (pip-audit `|| true`, L51), Unit (cov floor 30%), Integration (pg15 + redis), Docker Build Check (Trivy exit-code 0, syft SBOM artifact), Frontend Lint (continue-on-error). No FE typecheck/build.
  - deploy-dev.yml (push main on api/shared/services/worker/Dockerfile/requirements/frontend/** or dispatch): preflight guard (curl /admin/job-runner/deploy-gate; fails OPEN when ADMIN_SECRET unset, L48-51) → build/push dev-<sha> + :latest → register task def from family's latest revision (image swap only) → update api + worker → wait stable → same-SHA check → curl smoke (/health + 3 admin endpoints + worker kinds). No concurrency group.
  - vercel-deploy.yml (S241; PR/push main/dispatch; frontend/** only): remote Vercel build via `npx vercel@60.0.1` with repo-level VERCEL_TOKEN; PR → preview + ui-smoke.yml (Playwright); production → HTTP 200 check only when bypass secret set.
  - eval-regression.yml: dispatch only, via ECS exec, one run (2026-08-01).
- **AA-Booking** (public): ci.yml 5 required checks + non-required Frontend Build (eslint, tsc, next build) + Job template copy; pip-audit blocking, full-history gitleaks, cov floor 90%, integration fails on skips, concurrency. deploy-dev.yml uses vars, concurrency `deploy-dev`; config check → preflight script (.github/scripts/booking-deploy-preflight.sh: ECS task counts + OIDC-authenticated deploy-gate, fail-closed, unit-tested) → build/push immutable <sha> → register → wait → verify image → smoke /booking/health (git_sha) + /health/ready (schema_version bk-*).
- **AA-TripPlanner-Web** (public): ci.yml Backend (pytest) + Frontend (lint, typecheck, test, build); no security audit. deploy-lambdas.yml (push main backend/** or dispatch): zip → OIDC → S3 fixed keys → update-function-code --publish → wait; no smoke, no alias. vercel-deploy.yml copy of CIS's.
- **AA-CIS-Infra** (private, Free org): terraform-plan.yml (PR plan on accounts/aa365, not posted to PR); terraform-apply.yml "Terraform Apply Prod" dispatch-only, applies the dev state key with -auto-approve, env prod, no main check; db-migrate.yml (dispatch check/apply, one Fargate task, lint, idle check, RDS snapshot for destructive, then schema dump; main-only `if:`); db-schema-dump.yml (nightly); migration-copy-guard.yml (PR + nightly); secret-scan.yml (gitleaks pinned by digest).
- **Root AA-Ecosys**: no workflows.

## Governance / environments / AWS runtime (observed)

- Protection: CIS + Booking 5 checks strict; TP 2 checks non-strict; enforce_admins=false, reviews null, signatures off everywhere; Infra 403; root unprotected, 53/142 commits since 08-18 direct pushes. Org free, 2FA not required. allowed_actions=all, sha_pinning_required=false; no SHA pins; no dependabot.yml; CodeQL not configured; 0 tags/releases.
- Envs: CIS `dev` and Infra `prod` no rules, branch policy null, can_admins_bypass=true. Booking `dev` main-only. CIS deploy role trusts `environment:dev` (cicd_split.tf:317; comment says main-only "must stay set" — missing). Infra apply trusts `environment:prod` (cicd_split.tf:519). TP trusts `ref:refs/heads/main` (tripplanner.tf:551-581). Immutable OIDC subject everywhere.
- ECR: aa-cis-dev-api MUTABLE; aa-booking-dev-api IMMUTABLE; scan on push both; lifecycle "Keep last 10 images" tagStatus any.
- ECS: api, worker, booking all circuit breaker enable+rollback, ROLLING, no CloudWatch alarms on deployment; CIS api health-check grace 0, Booking 60. Task-def revisions: CIS api 659, worker 216, booking 28.
- Lambdas: ~49 published versions each, 0 aliases; API GW 9vqkfbukvh integrates unqualified ARN ($LATEST); artifacts bucket versioned.

## Manual today

- Every merge by Nghiệp (pqnghiep1354 or adventure365); median PR open→merge ~6 min; 0/951 merged PRs since 08-18 reviewed.
- Terraform apply workflow 54 runs (43 success) + frequent local targeted admin applies (docs/ci-role-split.md:100; implementation notes AA-751/AA-811/AA-818/AA-825/AA-828).
- DB Migrate ≥100 manual dispatches 10-11..10-16 (API returned exactly 100 — possible cap). Migration flow = 4 PRs/dispatches across 3 repos.

## DORA estimates (Dev only, 2026-08-18 → 10-17, inferred from run history)

- Deploy frequency: CIS ECS 540 successful (22/week W34 → 129 in W42); Booking 26 in 4 days; TP Lambda 62 in 5 weeks; Vercel 2 CI runs/repo since S241.
- Lead time: CIS CI PR p50 2.7 min / p90 3.1; deploy CIS p50 6.0, Booking 3.4, TP 0.7 → merge→Dev ~10 min; PR open→Dev < 1 h; commit→deploy unmeasured.
- Change failure: CIS 10/551 runs failed (1.8%), 6 of them guard blocks by design → ~0.7% real; rework proxy 225/609 CIS PRs `fix:` (37%), 0 reverts. Real CFR unmeasurable (no incident record).
- MTTR: not measured; recovery = circuit breaker (failed starts only) or fix-forward (~10–15 min).

## Strengths

- OIDC everywhere, per-app least-privilege deploy roles with permission boundary, immutable-subject trust (cicd_split.tf:40-50, booking.tf:68-82, tripplanner.tf:551-581); Booking dev env main-only.
- Booking = reference pipeline (immutable tags, git_sha asserted, fail-closed OIDC gate with unit tests, concurrency, blocking pip-audit + gitleaks, 90% coverage, no-skip integration on real PG15 with DB Migrate identity).
- Deploy-time job-queue guards (CIS, Booking) + DB Migrate idle check (exit 7) with auditable override.
- CIS per-commit tag for api + worker, same-SHA assertion, smoke checks JSON shape + worker kind coverage.
- Circuit breaker rollback on all 3 services; container health checks.
- Migration safety: copy guard, unique numbering, CONCURRENTLY/destructive lint, timeouts, auto snapshot, schema-reference regeneration.
- Workflow secret hygiene (env not `${{ }}` interpolation, masked presigned URLs, scrubbed Playwright state, gitleaks pinned by digest).
- S241 Vercel CI deploys remove Hobby-cap blowout, never cancel prod mid-deploy, fail red without token.
- Fast feedback (CI p50 ~2.7 min, deploy 1–6 min).

## Gaps

### C1 — OIDC trust relies on env branch rules that are not configured (CIS dev, Infra prod) — CRITICAL, XS, automatable
- Evidence: cicd_split.tf:317 + comment 309-313 vs live env dev branch_policy=null/rules []/admins bypass; cicd_split.tf:519 vs Infra prod same; terraform-apply.yml no ref check (db-migrate.yml:55 has one); CIS Deploy Dev dispatched from `pqnghiep1354/aa-519-...` on 2026-09-03 succeeded; TP deploy-lambdas succeeded from 6 feature branches 09-13..09-15 (before S235 tightening); VERCEL_TOKEN repo-level → production guard (vercel-deploy.yml:90) bypassable by editing the workflow on a branch.
- Risk: any branch (human/agent, incl. PR branch editing a workflow) can roll ECS, run full `terraform apply -auto-approve`, or promote Vercel production without review; direct path to customer infra once prod lands.
- Recommendation: branch policy = main on CIS `dev` and Infra `prod`/`dev`/`staging`; `if: github.ref == 'refs/heads/main'` on terraform-apply; VERCEL_TOKEN into a main-only `Production` env; delete VERCEL_DEPLOY_HOOK and ACPCORE_READ_TOKEN; scheduled settings-drift check.
- Standards: NIST SSDF PS.1/PO.5; SLSA Build L2-L3; Scorecard Token-Permissions/Dangerous-Workflow.

### C2 — No enforced gate between merge and deploy — HIGH, S, automatable
- Evidence: enforce_admins=false, reviews null on 3 app repos; Infra 403 (plan, secret-scan, copy-guard advisory only); root unprotected (e.g. 4e27bc78, 2fcc6d7b on 2026-10-12); 951 PRs merged with empty reviewDecision; median open→merge 0.1 h; deploy-dev (CIS, Booking) triggered on push main with no dependency on CI for that SHA; TP strict=false.
- Risk: merge gate is the main control; bypass or red Infra plan reaches RDS/IAM/ECS unchecked.
- Recommendation: GitHub Team (or Infra public after history review) → org ruleset on 5 repos (PR + checks + linear history, block force-push/deletion, break-glass bypass only); AI review check + required conversation resolution as "second pair of eyes"; protect root; deploy via `workflow_run` on CI success or assert check-runs green for the SHA.
- Standards: NIST SSDF PW.7/PS.1; Scorecard Branch-Protection/Code-Review; SLSA Source L2/L3.

### C3 — CIS Deploy Dev has no concurrency control — HIGH, XS, automatable
- Evidence: no `concurrency:` (Booking has `group: deploy-dev`, deploy-dev.yml:59-61); 40/550 consecutive runs overlapped; run 38744146079 (2026-10-15) failed at same-SHA verify with api on a different image (race, inference); 6 guard-blocked runs (10-09, 10-12, 10-13) not re-deployed automatically; 129 successful runs in W42.
- Risk: out-of-order deploys, api/worker split SHA, Dev silently behind main → defeats aa-ship Done rule.
- Recommendation: `concurrency: {group: deploy-dev-cis, cancel-in-progress: false}`; hourly drift job comparing running SHA (api, worker, booking, Lambda CodeSha) with main HEAD → alert/issue; optional guard re-queue.
- Standards: DORA; NIST SSDF PO.3; SRE serialized rollouts.

### C4 — No fast, deterministic rollback path — HIGH, S, automatable
- Evidence: ECR aa-cis-dev-api MUTABLE, deploy-dev.yml:97-101 pushes :latest; lifecycle keep 10 vs ~129 deploys/week → old task-def revisions point at deleted images (api rev 659); dispatch has no sha/image input; TP Lambdas 0 aliases, API GW → $LATEST; aa-ship has no rollback runbook; circuit breaker only covers failed starts.
- Risk: healthy-but-wrong release fixed only forward (~10–15 min); rollback to expired image fails.
- Recommendation: CIS ECR IMMUTABLE, stop :latest, keep last 30 dev-*/sha images + expire untagged after 7 days; `rollback.yml` (input image tag/task-def revision, no rebuild, same smoke); Lambda publish + `live` alias + API GW on alias (ADR 0006:233); Vercel instant rollback documented; runbook in skill/aa-ship.
- Standards: DORA MTTR; NIST SSDF RV.2; AWS WA REL 8.

### C5 — Build once, deploy many not followed; no provenance/signing/attached SBOM — HIGH, M, automatable
- Evidence: CIS ci.yml:171-211 and Booking ci.yml:159-197 build ci-<sha>, scan (report-only), SBOM as artifact, discard; deploy-dev rebuilds (CIS:98-101, Booking:143) → deployed bytes never scanned/SBOM'd in CI; only ECR scanOnPush (unread); no attest-build-provenance/cosign/SBOM attestation; Vercel remote build from source (vercel-deploy.yml:128-138) and CIS CI has no FE build/typecheck; TP Lambda zips built in deploy job, untested.
- Risk: no verifiable link from running artifact to reviewed commit; cannot answer B2B supplier security questionnaires (SBOM/provenance); non-reproducible rebuilds.
- Recommendation: one build job per main SHA → push by digest → Trivy blocking on fixable CRITICAL/HIGH → attest-build-provenance + attest-sbom (free on public) → deploy by digest (+ `gh attestation verify`); CIS CI adds `next build` + `tsc`; `vercel build` + `vercel deploy --prebuilt`; Lambda zip built in CI with sha256, deploy that file.
- Standards: SLSA Build L2→L3; NIST SSDF PS.2/PS.3; CISA SBOM minimum elements; EO 14028/EU CRA readiness.

### C6 — Security gates in CIS and TP can never fail — HIGH, S, automatable
- Evidence: CIS ci.yml:51 pip-audit `|| true` in REQUIRED Security Audit; Trivy exit-code 0 (CIS ci.yml:200, Booking ci.yml:189; AA-177 "monitor first" follow-up pending); CIS FE lint continue-on-error (74 errors, ci.yml:230-234); TP CI no dependency audit/secret scan/image scan; no CodeQL; no dependabot.yml (Dependabot alerts only — count claim not reproduced, see note); CIS cov floor 30% (ci.yml:89) vs Booking 90%.
- Risk: known-vulnerable deps ship (AA-177 STEP0 already found 5 in CIS); false assurance; public repo without SAST.
- Recommendation: remove `|| true` with explicit expiring `--ignore-vuln`; Trivy exit-code 1, ignore-unfixed, CRITICAL,HIGH + .trivyignore with expiry; gitleaks + pip-audit/npm audit in TP; CodeQL default setup; dependabot.yml grouped weekly with auto-merge for green patch/minor; ratchet CIS coverage +5%/month.
- Standards: NIST SSDF PW.4/PW.7/RV.1; OWASP SAMM; Scorecard SAST/Vulnerabilities/Dependency-Update-Tool.

### C7 — Third-party actions pinned by mutable tags; org allows any action — MEDIUM, S, automatable
- Evidence: no SHA-pinned `uses:`; checkout@v5 ×32, configure-aws-credentials@v6 ×10, setup-python@v5 ×10, setup-node@v4 ×6, setup-terraform@v3, amazon-ecr-login@v2, trivy-action@v0.36.0, sbom-action@v0.24.2, upload-artifact@v4; allowed_actions=all; only Infra secret-scan pins a container by digest (secret-scan.yml:160); `timeout-minutes` only in db-schema-dump.yml (16/17 workflows without).
- Risk: hijacked tag (tj-actions/changed-files, March 2025) runs with OIDC id-token:write + VERCEL_TOKEN/ADMIN_SECRET; jobs can hang to 6 h holding deploy lock.
- Recommendation: SHA pins + Dependabot github-actions; sha_pinning_required; allowlist (aws-actions, hashicorp, aquasecurity, anchore); timeout-minutes (CI 15, deploy 30, migrate 45); harden-runner audit mode on deploy jobs.
- Standards: Scorecard Pinned-Dependencies; SLSA; NIST SSDF PO.3.2/PS.1.

### C8 — Terraform flow mixes local targeted admin applies with auto-approve CI apply; plans not reviewed or bound — MEDIUM, M, automatable
- Evidence: terraform-apply.yml "Terraform Apply Prod" uses env prod but dev state key, plan -out + apply -auto-approve in one job, no branch check; terraform-plan.yml doesn't post plan, no fmt/tflint/checkov/trivy-config, cannot be required; local -target applies documented (docs/ci-role-split.md:100, AA-751.md:140-152, AA-811.md:74, AA-818.md:97, AA-825.md:54, AA-828.md:171); TF 1.7.5; 54 dispatches (11 failed).
- Risk: drift and surprises on next full apply; "prod" naming collides with real prod; IAM/WAF/RDS changes from laptop without recorded plan.
- Recommendation: rename envs (`dev-apply`), reserve `prod`; PR plan comment + binary plan artifact; apply only from main, verify plan hash or apply saved plan; fmt/validate/tflint/trivy config; nightly `plan -detailed-exitcode` drift alert; local applies only for documented break-glass, logged; upgrade TF to 1.9+ with pinned provider.
- Standards: NIST SSDF PO.3/PS.1; CIS AWS; GitOps; DORA change approval.

### C9 — One Dev environment doubles as live demo; no staging/promotion/versioning/change record — MEDIUM, M, automatable
- Evidence: only dev ECS services; inconsistent GitHub envs; Infra prod points at dev DB; DELETED-deploy-prod.md (prod workflow was a stub); 0 tags/releases; every merge goes straight to the env the B2B demo and tenant portal run on.
- Risk: nowhere to rehearse migrations/TF/breaking API; no release IDs for support/SLA; retrofitting later.
- Recommendation: ADR target pipeline main → Dev (auto) → Prod (promote SAME digest and Vercel deployment; env with required reviewer + wait timer + smoke); reusable workflows parametrised by env; release on each prod promotion; clean envs to dev/prod.
- Standards: SLSA/NIST SSDF PS.3; ITIL change enablement; DORA; ISO 27001 A.8.31-8.32.

### C10 — Post-deploy and UI verification thin — MEDIUM, M, automatable
- Evidence: ui-smoke last 50 runs: 49 skipped, 1 success; not required; production Vercel only HTTP 200 when bypass secret set (vercel-deploy.yml:150-174); CIS smoke admin checks skipped and guard fails open without ADMIN_SECRET (deploy-dev.yml:48-51, 309-311); Booking smoke only health; eval-regression 1 run, passes green when exec returns no JSON (L61-74); deploymentConfiguration.alarms=null.
- Risk: broken tenant pages, API contract and LLM regressions reach customers; contradicts "live evidence" rule.
- Recommendation: required UI smoke for frontend/** (job-level `if` + pass-through no-op); smoke production after each prod Vercel deploy; contract-based smoke (OpenAPI, synthetic tenant); CIS guard fail-closed; ECS deployment alarms (5xx, target health); scheduled cost-capped eval subset or on prompt changes, fail on missing JSON.
- Standards: DORA CFR; NIST SSDF PW.8; SRE; ISO 25010.

### C11 — TripPlanner Lambda deploy ungated — MEDIUM, S, automatable
- Evidence: deploy-lambdas.yml independent of ci.yml, no `environment:`, no smoke after `wait function-updated`, overwrites fixed S3 keys (L134-137; bucket versioned), zips built in deploy job, no security scanning in TP CI; 6 feature-branch deploys succeeded 09-13..15.
- Risk: B2C API replaced by code whose tests failed; runtime import error found by users; no instant rollback.
- Recommendation: gate on CI (`workflow_run` or reusable test + `needs:`); `environment: dev` main-only + trust update; alias deploys (+ optional CodeDeploy canary 10%/5 min with Errors alarm); post-deploy curl smoke; deploy CI-built zip by sha256.
- Standards: DORA; NIST SSDF PS.3/PW.8; AWS WA OPS 6.

### C12 — Path filters and deploy side effects cause unnecessary backend restarts — MEDIUM, XS, automatable
- Evidence: CIS deploy-dev.yml:12 includes `frontend/**` (current image dev-791eeb83 = PR #788, a CI/FE change); deploy_family.sh forces `--desired-count 1` (deploy-dev.yml:147-148); Booking explicitly does not (deploy-dev.yml:37-38).
- Risk: restarts interrupt jobs or get guard-blocked, inflate deploy count and image churn (shrinking rollback window), undo scale-to-zero.
- Recommendation: drop `frontend/**`, add `!**/*.md`, `!docs/**`, test-only exclusions; remove forced desired-count; optional build-on-input-hash.
- Standards: Lean/DORA; FinOps.

### C13 — DB migration release is a 4-step manual cross-repo choreography with no schema/app compatibility gate — MEDIUM, M, automatable
- Evidence: migration-copy-guard.yml:214-216 documents flow; db-migrate dispatch-only, ≥100 manual runs 10-11..10-16; env prod unprotected; db-schema-dump.yml:51-53 notes reviewers never added; nothing checks app's required schema version (Booking smoke only checks prefix `bk-`).
- Risk: app deploys before migration → 500s; destructive file relies only on snapshot; doubled toil with prod.
- Recommendation: bot opens Infra copy PR on owner-repo merge; merged copy auto-runs `mode=check`; `apply` manual but approval-gated; apps expose `required_schema_version` and deploy preflight fails if missing; record each apply as a GitHub Deployment.
- Standards: NIST SSDF PS.1/PO.3; DORA DB change management; expand-contract.

### C14 — Pipeline code duplicated across repos, no shared workflow library — LOW, M, automatable
- Evidence: vercel-deploy.yml ×3 (diffs only project ID/comments/smoke); ECS deploy logic twice (CIS deploy_family.sh heredoc L139-160, Booking inline L147-168); drift: CIS secrets for config (L23-27) forcing tag-only output workaround (L72-76) vs Booking vars; guard fail-open vs fail-closed; concurrency only in Booking; no org .github.
- Risk: every hardening repeated N times; copies drift — why Booking quality hasn't reached CIS.
- Recommendation: org `.github` (or `ci-workflows`) with versioned reusable workflows (python-ci, ecs-deploy, vercel-deploy, lambda-deploy) + composite actions (guard, smoke), callers pinned by tag/SHA; Booking as template; CIS config → env vars.
- Standards: NIST SSDF PO.3; platform-engineering golden path.

### C15 — DORA, deploy and incident data not recorded — LOW, S, automatable
- Evidence: no GitHub Deployments/statuses; no incident log/label; only proxies (1.8% pipeline failure, 37% `fix:`, 0 reverts); commit→deploy unknown; aa-ship evidence lives in prose.
- Risk: no objective stability signal; no data for tenant SLOs.
- Recommendation: GitHub Deployment per deploy; `incident` label with detected/resolved timestamps + deploy SHA; monthly review of 4 metrics; uptime/SLO probe.
- Standards: DORA four keys; Google SRE; NIST SSDF RV.2.
