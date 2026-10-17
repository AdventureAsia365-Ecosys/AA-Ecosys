# Area 1 — GitHub organization and repository governance

Scope: org AdventureAsia365-Ecosys, 5 active repos, local Claude Code hooks/settings. Read-only (S241, 17/10/2026).
Token scopes gist/read:org/repo/workflow — org Actions policy, org secrets/variables and org rulesets returned 403/404 ("needs admin:org") and were NOT inspected.

Synthesis verification notes: see `../README.md` §8.3 (items 1, 4, 11, 12, 13 touch this area).

## Current state (observed)

- **Org** (`GET orgs/AdventureAsia365-Ecosys`): plan=free; two_factor_requirement_enabled=false (members?filter=2fa_disabled empty → both members currently have 2FA); 2 members, both admins (pqnghiep1354, adventure365); 0 teams, 0 outside collaborators; default_repository_permission=read; members_can_create_public_repositories=true; members_can_fork_private_repositories=false; all *_enabled_for_new_repositories security defaults=false.
- **Visibility**: AA-CIS-App, AA-Booking, AA-TripPlanner-Web, AA-Ecosys (root), archived AA-ACP-App = PUBLIC. AA-CIS-Infra, archived AA-ACP-Core = private. No LICENSE in any repo.
- **Branch protection** (legacy; no active rulesets): CIS-App main and Booking main require 5 strict checks (Lint, Security Audit, Unit Tests, Integration Tests, Docker Build Check). TP main requires 2 non-strict checks. All three: no required reviews, enforce_admins=false, linear history off, signatures off, force-push/deletion blocked. CIS-App has rulesets "main"/"develop" enforcement=disabled with empty conditions. AA-Ecosys master: "Branch not protected". AA-CIS-Infra: 403 "Upgrade to GitHub Pro or make this repository public" (no protection).
- **Security features**: secret scanning + push protection disabled on every repo; Dependabot security updates disabled everywhere; Dependabot alerts on for the 4 public repos (0 open; verified 0 total for CIS in synthesis), off for Infra; CodeQL default setup not-configured; private vulnerability reporting off; no SECURITY.md, CODEOWNERS, PR/issue templates, dependabot.yml; no org .github repo. Infra has .gitleaks.toml + secret-scan.yml.
- **Actions** (repo level): allowed_actions=all; sha_pinning_required=false; default_workflow_permissions=read; can_approve_pull_request_reviews=false; fork PR approval=first_time_contributors on public repos.
- **Environments**: CIS-App dev, Preview, prod, Production, staging — only `prod` has a rule (protected_branches); `dev` (in use) has none. Booking dev (custom branch policy: main), Preview, Production. TP Preview, Production (no rules). Infra dev, prod, staging (no rules); `prod` holds AWS_ROLE_ARN, used by terraform-apply.yml:18, db-migrate.yml:54, db-schema-dump.yml:54. No env has required reviewers. can_admins_bypass=true everywhere.
- **Secrets (names only)**: CIS-App repo: ACPCORE_READ_TOKEN (2026-08-21), ADMIN_SECRET, AWS_REGION, E2E_ADMIN_PASSWORD/USERNAME, ECR_REGISTRY, ECR_REPOSITORY, ECS_CLUSTER, ECS_SERVICE, VERCEL_AUTOMATION_BYPASS_SECRET, VERCEL_DEPLOY_HOOK (2026-05-13), VERCEL_TOKEN; env dev: AWS_ROLE_ARN. Booking: repo VERCEL_TOKEN; dev env variables AWS_REGION, AWS_ROLE_ARN, ECR_REPOSITORY, ECS_CLUSTER, ECS_SERVICE. TP: repo VERCEL_TOKEN. Infra: AWS_REGION, AWS_ROLE_ARN, ROOT_REPO_DOCS_TOKEN (PAT), TF_STATE_BUCKET, TF_VAR_DB_PASSWORD; env prod: AWS_ROLE_ARN. Root: none.
- No deploy keys or repo webhooks. GitHub Apps on ALL repos: vercel (administration/contents/workflows/hooks write), linear-code (actions/contents/workflows write), claude (actions/contents/workflows/hooks write), notion-workspace (issues/PR write).
- 0 tags, 0 releases everywhere. auto-merge on for 3 app repos; delete_branch_on_merge only on TP; all three merge methods allowed. Branch counts: CIS-App 702 (384 local origin refs older than 30 days, 209 already merged), Infra 114, root 35, Booking 21, TP 12. Open PRs: 1 (Infra #105).
- Merge discipline: last 50 main commits are squash PRs for CIS-App and Infra; Booking has 4 direct bootstrap commits (2026-10-14); root master 8 direct pushes (2026-10-12).
- **AWS OIDC** (infra/AA-CIS-Infra/accounts/aa365): repo-ID-scoped trust. cis_app_deploy `environment:dev` (cicd_split.tf:317); tf_plan `:pull_request` + ReadOnlyAccess (cicd_split.tf:458-467); tf_apply `environment:prod` (cicd_split.tf:519) + legacy managed policies (cicd.tf:22-32). Booking `environment:dev` OR `ref:refs/heads/main` (booking.tf:78); TP ref main (tripplanner.tf:552).
- **Local**: committed .claude/settings.json (29 lines) allows only `gh pr merge:*` and wires 2 PreToolUse hooks (subagent-guardrails.sh, subagent-mcp-guardrails.sh) that act only when agent_id is present. Uncommitted working copy (153 lines) adds ~125 allow rules incl. `terraform apply:*`, secret writes, `aws iam *`, `gh workflow run:*`, Vercel create/edit_project_env.
- INFERENCE: app repos and root were made public to obtain branch protection on Free (only trace: docs/sessions/2026-10-14-S235-…md:29). No ADR.

## Strengths

- No static AWS keys in GitHub; OIDC trust pinned to immutable owner/repo IDs (cicd_split.tf:49-50); read-only plan role split from apply role.
- Default GITHUB_TOKEN read-only on all 5 repos; Actions cannot approve PRs; explicit `permissions:` blocks.
- CIS-App and Booking main require 5 strict checks; force-push/deletion blocked on 3 app repos.
- Booking `dev` env restricted to main — the model to copy.
- Vercel workflows skip fork PRs, refuse production off main, never cancel a production deploy mid-way.
- Booking CI fails on pip-audit, full-history gitleaks (ci.yml:49-83); Infra secret-scan + migration-copy-guard.
- SBOM (CycloneDX per SHA) and Trivy in CIS and Booking CI.
- Deploy preflight gate blocks ECS rollouts while shared.job has active work.
- Trunk-based flow mostly honoured (squash merges).
- Org base permission read, private forking disabled, no outside collaborators/deploy keys/stray webhooks.
- Subagent guardrail hooks with a test script.

## Gaps

### G1 — AA-CIS-Infra: admin-grade Terraform apply and DB migrations can be dispatched from any branch with no review — CRITICAL, effort S, automatable
- Evidence: Infra protection/rulesets 403; env `prod` protection_rules=[] and deployment_branch_policy=null; terraform-apply.yml `on: workflow_dispatch` + `environment: prod`, no ref guard; trust `${oidc_sub_cis_infra}:environment:prod` (cicd_split.tf:519) does not constrain branch; apply role grant set cicd.tf:22-32 (RDSFull, SecretsManagerReadWrite, ECS_Full, VPCFull…); db-migrate/db-schema-dump use same env; TF_VAR_DB_PASSWORD injected into job env.
- Risk: anyone/anything with write (either owner, stolen gh token on WSL box, claude/linear-code/vercel apps with contents+workflows write) can push a branch with modified workflow/.tf and dispatch → AWS admin-equivalent on acc2, arbitrary SQL on shared RDS. Biggest blast-radius path.
- Recommendation: (1) GitHub Team (~USD 4/user/month) rather than making Infra public; (2) Infra `prod` (rename, see env gap): branch policy main only, required reviewer Nghiệp (prevent_self_review=false), can_admins_bypass=false; (3) AWS trust condition on `job_workflow_ref` = `AdventureAsia365-Ecosys/AA-CIS-Infra/.github/workflows/terraform-apply.yml@refs/heads/main` (+ db-migrate), or custom OIDC sub template incl. ref; (4) `if: github.ref == 'refs/heads/main'`; (5) move TF_VAR_DB_PASSWORD out of GitHub (RDS-managed master password).
- Standards: NIST SSDF PO.5.1/PS.1.1; SLSA Build L2/L3; Scorecard Branch-Protection + Dangerous-Workflow; CIS GitHub Benchmark 1.1.x/1.4.x.

### G2 — Root docs repo and app source are public — HIGH, effort S, not automatable
- Evidence: 4 active repos + archived AA-ACP-App public; root tracks 1794 files (1510 docs/audits, 63 session logs, ADR 0005 pricing/supplier rates, admin/tenant UI screenshots); account IDs in 91 files; staff/test addresses (thu@, breakglass@, e2e-*+booking@adventure.asia); Vercel team/project IDs and deploy-gate URL in workflows; no LICENSE; no ADR on visibility. CLAUDE.md says ACP repos were deleted but both still exist (archived).
- Risk: competitors/customers read supplier & pricing strategy and audit findings; phishing targets; attack surface map; IP/due-diligence problem; making private on Free silently drops protection.
- Recommendation: ADR "private by default"; after Team, root private first, then app repos (re-verify protection); archived AA-ACP-App private or delete; members_can_create_public_repositories=false; full-history gitleaks/trufflehog first and rotate findings; proprietary LICENSE.
- Standards: ISO 27001 A.5.12/A.8.4; NIST SSDF PS.1; OWASP SAMM Governance.

### G3 — Free-for-public security features are off — HIGH, effort XS, automatable
- Evidence: security_and_analysis on 4 public repos: secret_scanning, push_protection, dependabot_security_updates disabled; secret-scanning/alerts → disabled; code-scanning default-setup not-configured; Infra → "Advanced Security must be enabled"; Infra Dependabot alerts 403 disabled; private-vulnerability-reporting false; no dependabot.yml/SECURITY.md/codeql; org new-repo defaults false.
- Risk: leaked AWS/Vercel/OpenAI/DataForSEO key pushed by human or agent neither blocked nor alerted (2 earlier wrong-account secret incidents on record); vulnerable deps and SAST issues unnoticed; no private reporting channel.
- Recommendation: enable secret scanning + push protection + validity checks + Dependabot alerts/updates on public repos; org defaults on; CodeQL default setup (python, javascript-typescript, actions); private vulnerability reporting + SECURITY.md; dependabot.yml (pip, npm, docker, github-actions, terraform; weekly; grouped). Infra: gitleaks + Dependabot alerts (free on private). Re-check after any private flip (GHAS costs).
- Standards: Scorecard SAST/Dependency-Update-Tool/Security-Policy/Vulnerabilities; NIST SSDF PW.7/PW.8/RV.1.1.

### G4 — Root repo master completely unprotected while holding agent instructions and guardrail hooks — HIGH, effort XS, automatable
- Evidence: master protection 404; rulesets []; 8 direct pushes on 2026-10-12 in last 50; tracks .claude/hooks/subagent-guardrails.sh, .claude/settings.json, .kiro/steering/*.md, skill/*/SKILL.md, CLAUDE.md.
- Risk: one unreviewed push or a compromised app installation rewrites guardrails/allow-lists/steering — every later agent session executes it (agent supply-chain / prompt-config injection); master can be force-pushed or deleted.
- Recommendation: ruleset on master (require PR, 0 approvals OK, block force-push/deletion, linear history); required "docs-lint" check running .claude/hooks/test_subagent_guardrails.sh + link check; CODEOWNERS on /.claude/**, /.kiro/**, /skill/**, CLAUDE.md.
- Standards: Scorecard Branch-Protection; NIST SSDF PO.3/PS.1; OWASP LLM01/LLM05.

### G5 — Required checks bypassable by admins; no PR requirement or review signal; both humans are org owners — HIGH, effort S, automatable
- Evidence: required_pull_request_reviews=None, enforce_admins=false on 3 app repos; both members admin; `gh auth status` shows both accounts on the same WSL machine (repo, workflow, read:org); org 2FA not required; CIS rulesets disabled with empty conditions.
- Risk: any admin token (incl. agent gh session) can push to main and trigger deploy-dev on push, skipping checks; no second signal; owner compromise = org takeover → AWS via OIDC.
- Recommendation: one org-level ruleset (Team) on ~DEFAULT_BRANCH: require PR, required checks, block force-push/deletion, linear history, empty bypass or break-glass only; org Require 2FA (passkeys); adventure365 as break-glass not logged in on dev machine; non-blocking AI review + required conversation resolution; delete disabled rulesets.
- Standards: Scorecard Branch-Protection/Code-Review; CIS GitHub Benchmark 1.1.3–1.1.14, 1.3.x; NIST SSDF PS.1.1.

### G6 — CIS "Security Audit" required check can never fail; Trivy report-only — MEDIUM, effort S, automatable
- Evidence: CIS ci.yml:51 `pip-audit -r requirements.txt --ignore-vuln PYSEC-2024-56 || true`; ci.yml:195-200 Trivy `exit-code: "0"`; ci.yml:230-234 frontend lint continue-on-error (AA-601); Booking ci.yml:182-189 Trivy exit-code 0.
- Risk: gate theatre; new critical CVE ships; bad answer on security questionnaires.
- Recommendation: fail pip-audit with dated ignore list; Trivy exit-code 1 for CRITICAL,HIGH + --ignore-unfixed + .trivyignore with expiry; close AA-601; track non-blocking security steps with deadline.
- Standards: NIST SSDF PW.7.2/RV.1.2; OWASP SAMM Verification; SLSA.

### G7 — GitHub Environments not used as a deploy control; names don't match reality — MEDIUM, effort M, automatable
- Evidence: CIS `dev` rules=[], branch_policy=null; deploy-dev.yml:13 workflow_dispatch from any branch with `override_running_jobs` "Nghiệp only" not enforced; unused envs (CIS prod/staging/Production/Preview; Infra dev/staging); Infra `prod` targets the Dev account; vercel-deploy.yml uses no `environment:` (in-script production guard); VERCEL_TOKEN repo-level in 3 repos; only Booking `dev` has main-only policy.
- Risk: no tested promotion path when prod arrives; "prod" name collides; team-wide Vercel token readable from any branch; override usable by anyone who can dispatch.
- Recommendation: ADR env model (`dev`, `prod`, optional `preview`); delete unused envs; rename Infra `prod` → `dev` with OIDC subject change (cicd_split.tf:519) in the same change; main-only branch policy on every deploy env; required reviewer on future prod; VERCEL_TOKEN into `vercel-production` env (main only) + separate preview token or Vercel OIDC; gate override with `github.actor` or protected env.
- Standards: NIST SSDF PO.5; SLSA; ISO 27001 A.8.31; DORA.

### G8 — Third-party GitHub Apps have write and workflow-write on every repo — MEDIUM, effort XS, not automatable
- Evidence: installations vercel (all; administration/contents/workflows/hooks write), linear-code (all; actions/contents/workflows write), claude (all; actions/contents/workflows/hooks write), notion-workspace (all; issues/PR write).
- Risk: vendor compromise can edit/dispatch Infra workflows → AWS apply role; can modify agent config in root.
- Recommendation: "Only select repositories": Vercel → 3 FE repos; Linear → code repos (consider removing Infra); Claude → only where used, never Infra unless needed; Notion → where used. Quarterly re-audit.
- Standards: CIS GitHub Benchmark 1.2.x/4.x; NIST SSDF PO.3.2; Scorecard Token-Permissions.

### G9 — Secrets hygiene: orphan credentials, PATs, config as secrets — MEDIUM, effort S, automatable
- Evidence: ACPCORE_READ_TOKEN (2026-08-21) and VERCEL_DEPLOY_HOOK (2026-05-13) referenced only in stale `.claude/worktrees/*` copies, not in live workflows; ROOT_REPO_DOCS_TOKEN PAT (db-schema-dump.yml:18,162); non-secret config stored as secrets (AWS_REGION, ECR_*, ECS_*, TF_STATE_BUCKET); ADMIN_SECRET and E2E_ADMIN_PASSWORD repo-level; no rotation record.
- Risk: unused valid tokens = pure attack surface; PAT tied to a person; masked config slows debugging; repo-level secrets reach every workflow/branch.
- Recommendation: delete ACPCORE_READ_TOKEN and VERCEL_DEPLOY_HOOK (revoke underlying PAT/hook); replace ROOT_REPO_DOCS_TOKEN with org GitHub App (actions/create-github-app-token); non-sensitive values → env variables; env-scope ADMIN_SECRET, E2E, VERCEL_*; secrets register + 90-day rotation.
- Standards: NIST SSDF PO.5.2/PS.1; CIS GitHub Benchmark; OWASP Secrets Management Cheat Sheet.

### G10 — Actions supply chain open — MEDIUM, effort S, automatable
- Evidence: allowed_actions=all, sha_pinning_required=false on 5 repos; tag pins (trivy-action@v0.36.0, sbom-action@v0.24.2, setup-terraform@v3, configure-aws-credentials@v6, amazon-ecr-login@v2, actions/*@v4/v5); fork PR approval first_time_contributors; no Dependabot github-actions.
- Risk: retagged/compromised action (tj-actions class) with id-token:write mints AWS creds or exfiltrates VERCEL_TOKEN/ADMIN_SECRET; second-time outside contributor PRs run without approval.
- Recommendation: allow GitHub-owned + verified + allow-list; sha_pinning_required + full SHA pins with version comments, Dependabot bumps; fork approval all_external_contributors; optionally zizmor/actionlint.
- Standards: Scorecard Pinned-Dependencies/Dangerous-Workflow; SLSA Build L3; NIST SSDF PW.4.

### G11 — No process templates (CODEOWNERS, PR template, issue templates, SECURITY.md, org .github) — MEDIUM, effort S, automatable
- Evidence: contents API 404 for all in 5 repos; org .github 404; conventions (`Refs AA-xxx`, aa-ship DoD, migration ownership, deploy-gate) live only in CLAUDE.md/skills.
- Risk: process depends on agents reading prose; wrong keyword auto-closes Linear; no owner routing for sensitive paths.
- Recommendation: org `.github` with PULL_REQUEST_TEMPLATE (Linear ref, what/why, risk, migration Y/N + owner key, deploy-gate impact, rollback, aa-ship evidence, screenshots), ISSUE_TEMPLATE (bug/feature/security), SECURITY.md, CONTRIBUTING.md; CODEOWNERS for .github/workflows/**, db/migrations/**, accounts/**/*.tf, iam*, .claude/**, skill/**; CI check rejecting PR body without `Refs AA-` or with Fixes/Closes.
- Standards: Scorecard Security-Policy/Code-Review; NIST SSDF PO.1/PO.2; ISO 27001 A.8.32.

### G12 — No releases, tags or versioning — LOW, effort S, automatable
- Evidence: 0 tags/releases in 5 repos; deploys identified by SHA only (sbom-${{ github.sha }}, CIS ci.yml:210).
- Risk: no human-readable version for changelogs/support/rollback; no immutable "what was live on date X"; DORA hard to compute.
- Recommendation: release-please or tag-on-successful-deploy; attach SBOM + image digest to Release; GitHub Deployment per env; tenant release notes.
- Standards: NIST SSDF PS.2/PS.3; SLSA provenance; DORA.

### G13 — Branch sprawl and inconsistent merge settings — LOW, effort XS, automatable
- Evidence: CIS-App 702 branches (384 >30 days, 209 merged), Infra 114, root 35; delete_branch_on_merge false except TP; all merge methods allowed; required_linear_history false.
- Risk: slows agent tooling, hides important branches, keeps old vulnerable code reachable on public repos; inconsistent history.
- Recommendation: delete_branch_on_merge everywhere; squash only; linear history in ruleset; one-off cleanup of merged/stale branches after Nghiệp approves list; scheduled stale-branch report.
- Standards: Scorecard repo hygiene; ADR-2026-023.

### G14 — Main-session Claude Code permissions auto-allow high-impact commands; guardrails cover subagents only — LOW, effort XS, automatable
- Evidence: uncommitted .claude/settings.json (+~125 lines) allows `terraform apply:*`, `terraform -chdir=* apply:*`, secret writes, `aws iam *`, `gh workflow run:*`, `gh pr merge:*`, Vercel create/edit_project_env, bash -c terraform apply one-liners; subagent-guardrails.sh:11 exits 0 without agent_id; hook also blocks read-only `aws iam list-roles` for subagents.
- Risk: prompt injection or mistaken plan applies Terraform/rewrites secrets/changes IAM/edits Vercel env with no prompt; silently growing allow-list not reviewable.
- Recommendation: personal allows in settings.local.json; commit minimal shared settings; move apply/secret/IAM-write/workflow run/Vercel env writes to `ask`; main-session PreToolUse hook requiring a plan file for terraform apply and blocking `gh api -X PUT/DELETE` on protection/rulesets/environments; narrow subagent IAM pattern to write verbs.
- Standards: OWASP LLM06/LLM01; NIST AI RMF MANAGE 2.x; NIST SSDF PO.5.
