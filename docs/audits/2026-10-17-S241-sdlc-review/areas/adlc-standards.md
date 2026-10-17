# Area 6 — AI-assisted development lifecycle (ADLC) governance + external standards baseline

Read-only, 17/10/2026. "Observed" = verified by file read or GET/describe; "inference" labelled.

Synthesis verification notes (`../README.md` §8.3):
- This area stated the **committed** `.claude/settings.json` allows `aws iam *`, secret writes, `terraform apply:*`, `gh workflow run:*` and an inline admin-secret curl. Verified: the committed version (`git show HEAD:.claude/settings.json`) is 29 lines and allows only `Bash(gh pr merge:*)`; the broad rules are in the **uncommitted working copy** (153 lines).
- The settings.local.json with a literal former e2e password is the project-level `/home/nghiep/projects/AA-Ecosys/.claude/settings.local.json` (gitignored via ~/.config/git/ignore), not `~/.claude/settings.local.json` (does not exist). Values not printed.
- `[profile aa365-agent]` exists in ~/.aws/config (line 79) but sessions use aa365-admin.

## Current state (observed)

**How agents are used**
- Claude Code = orchestrator with workflow subagents in worktrees; Kiro (kiro-cli, "aa-worker") writes code when kiro-delegate is on (.claude/skills/kiro-delegate/SKILL.md); Sonnet "kiro-reviewer" subagent reviews Kiro work (.claude/agents/kiro-reviewer.md) only "when risky" (SKILL.md §3.3).
- Knowledge: 9 skills under skill/ (856 lines, progressive disclosure per skill/README.md), .kiro/steering imported into CLAUDE.md, lessons log (skill/aa-lessons/lessons.md, 143 lines), implementation notes (417 CIS, 16 Booking).
- DoD: skill/aa-ship (merge + CI + ECS rollout + live curl).
- Guardrails: .claude/hooks/subagent-guardrails.sh and subagent-mcp-guardrails.sh block push/merge/apply/IAM/secret writes for SUBAGENTS only (exit 0 without agent_id); red-team test test_subagent_guardrails.sh asserts `secretsmanager get-secret-value` is ALLOWED.
- Orchestrator merges, applies Terraform, runs DB Migrate itself: S240 log (docs/sessions/2026-10-16-S240-…md:29) "Tắt auto mode nhiều lần để mình tự merge / apply / DB Migrate / xoá tài nguyên"; memory agent-team-pilot.md "the orchestrator may gh pr merge in auto mode" — conflicts with project .claude/CLAUDE.md ("DO NOT merge to main yourself") and apps/AA-Booking/.claude/CLAUDE.md:7 ("Agents never merge…apply Terraform, run DB Migrate or write secrets").
- Credentials: AWS role arn:aws:iam::005097885195:role/nghiep-admin-8h-session (12h per ~/.aws/config); GitHub OAuth scopes repo, workflow, gist, read:org on two accounts (pqnghiep1354, adventure365); MCP connectors GitHub, Linear, Notion, Vercel, Jira.
- ~/.claude/settings.json: allow `aws secretsmanager *`, `aws s3 *`, `mcp__claude_ai_Linear__save_issue`; skipDangerousModePermissionPrompt=true, skipAutoPermissionPrompt=true; autoMode.environment describes old org AdventureAsia365-CIS, path /home/nghiep/projects/aa-cis/AA-CIS-App, AAA accounts.

**GitHub evidence**: 4 public repos (CIS, Booking, TP, root), Infra private; secret scanning/push protection/Dependabot security updates disabled on public; CIS/Booking/TP required_pull_request_reviews=null, enforce_admins=false; root unprotected; Infra 403; CIS rulesets disabled; last 148 merged PRs across 5 repos authored and merged by pqnghiep1354/adventure365 with 0 reviews; no CODEOWNERS/dependabot.yml/PR template/.github; CodeQL not configured on 3 app repos; org free, 2FA not required, members_can_create_repositories=true; ci.yml:51 pip-audit `|| true`, Trivy report-only, syft SBOM; actions pinned by tag; no attestations; OIDC deploys; `dev` env no rules; gitleaks only in Infra.

**AI provenance**: 94/398 CIS main commits (30 days) carry Claude Co-Authored-By; Kiro authorship only in PR body; Kiro transcripts in gitignored .tmp-session/kiro deleted after merge.

**AI governance in the product**
- In place: CIS gateway enforced by tests/unit/test_aa685_no_raw_model_calls.py; PATCH /admin/llm-config/{stage} audited (audit_actor, admin_llm_ops.py:206-355) with shadow sampling; llm_call_log ledger + adhoc-script cost rule; TP daily spend hard stop (TP_DAILY_SPEND_CAP_USD, ONLINE_STAGES tp_compose / tp_search_embed, backend/shared/llm_gateway.py:531); tenant brand-prompt sanitizer (shared/validators/prompt_sanitize.py, regex, "self-injection containment"); cost/budget guards (AA-649, AA-805); Jev decisions in shared.decision_log.
- Gaps: eval-regression dispatch-only, s1_old only, last 2026-08-01, 85 commits since touched prompts/LLM client; ADR 0009 (AI platform) "Reserved" (docs/adr/README.md:21); AA-804 (AI Use Register + PII-on-LLM-path) "later" (docs/backlog/README.md:56); DM-6.4 no automated PII check (02-data-management.md:210, 361); tenant AI clause draft "NOT APPROVED" (docs/legal/tenant-terms-ai-clause-draft.md; Anthropic AUP effective 12/11/2026, AA-820).

## External baseline and what it means here

1. **NIST SSDF SP 800-218 v1.1 + SP 800-218A (Jul 2024)** — https://csrc.nist.gov/projects/ssdf, https://csrc.nist.gov/pubs/sp/800/218/a/final. PO.5 protected dev env + separate agent identity; PS.1/PS.3 protect code, provenance; PW.7/PW.8 review + test (human approval on PR + SAST for AI code); 218A eval before release, protect prompts/data. Here: required reviews, CodeQL, eval-on-PR for prompt paths, AI Use Register.
2. **SLSA v1.2** — https://slsa.dev/spec/. Build L2 = signed provenance from hosted builder (GitHub artifact attestations); reusable workflow → L3. Here: attest ECR image in deploy-dev.yml, verify digest before ECS update (free on public).
3. **OpenSSF Scorecard** — https://github.com/ossf/scorecard/blob/main/docs/checks.md. Branch-Protection, Code-Review, Token-Permissions, Dangerous-Workflow, Pinned-Dependencies, SAST, Dependency-Update-Tool, Security-Policy. Inference: Code-Review ~0/10, SAST ~0, Pinned-Dependencies low. Here: weekly Scorecard action on public repos as KPI.
4. **OWASP ASVS 5.0.0, API Top 10 2023, LLM Top 10 2025, Agentic Top 10 2026** — ASVS L2 for B2B portal/APIs; LLM01, LLM02, LLM06, LLM10 apply to product; Agentic ASI02, ASI03, ASI09 apply to how Claude/Kiro are run.
5. **DORA 5 metrics** (lead time, deploy frequency, failed-deployment recovery time, change fail rate, deployment rework rate) — https://dora.dev/guides/dora-metrics/history/. Here: weekly from deploy-dev runs and PR data, split AI vs human.
6. **GitHub practice** — rulesets (free on public), required review + CODEOWNERS + "approval of most recent push", env required reviewers for prod, OIDC sub scoped to environment, secret scanning push protection free for public (not auto-enabled for org-owned repos).
7. **12-factor / trunk-based** — largely followed (ADR-2026-023, config in Secrets Manager, OIDC).
8. **SOC 2 CC8.1, ISO 27001 A.5.3/A.8.32** — approval record by someone other than author; solo shop compensating control: agent identity as author + human approver + periodic independent review of merge/deploy log.
9. **EU AI Act Art. 50** (applies 2 Aug 2026; AI-generated public-information text disclosure; machine-readable marking, 50(2) possibly deferred to 2 Dec 2026 for systems already on market — verify against Official Journal); **GDPR** Art. 28 DPA, Art. 30 RoPA, DPIA for traveller data to LLMs.
10. **Agentic-coding governance** (https://code.claude.com/docs/en/security) — least privilege, OS sandbox/devcontainer, "a deny rule matches the command as written" → enforce at OS/IAM layer, managed settings, OTel, ConfigChange hooks, review all changes.

## Strengths

- Strong written agent process (9 compact skills, progressive disclosure, steering shared by Kiro and Claude).
- Lessons log feedback loop (rule → CI guard → delete).
- Strict evidence-based DoD.
- Subagent guardrail hooks with red-team test table.
- Role separation in kiro-delegate (Kiro has no secrets, reviewer checks transcript vs diff vs claims, kiro_check.py flags out-of-scope files).
- Per-issue implementation notes as AI-code provenance.
- `Refs AA-xxx` commit format; Claude co-author trailer on part of commits.
- OIDC to AWS, CI roles split plan/apply/deploy (S236), SBOM + Trivy in CIS, gitleaks pinned by digest in Infra.
- Product LLM governance ahead of most small teams (single enforced gateway, audited per-stage model config + shadow, cost ledger, Jev decision log, TP spend hard stop, cost guards, adhoc-cost rule).
- Data standards already state PII classes and DM-6.4; tenant AI clause draft tracks AUP change.

## Gaps

### D1 — Agents run with the human's full admin credentials — CRITICAL, M, automatable
- Evidence: sts → nghiep-admin-8h-session (12h); gh scopes repo/workflow/gist/read:org on two accounts; ~/.claude/settings.json allows `aws secretsmanager *`, `aws s3 *`, skipDangerousModePermissionPrompt=true; working-copy project settings allow `aws iam *`, secret writes, `terraform apply:*` (see verification note — not committed); S240 line 29 auto mode off to self-merge/apply/migrate/delete; aa-cis-dev-agent-session attempted (lessons.md, AA-730) but unused; IAM policy content unreadable (hook blocks `aws iam`; inference: admin-level per name).
- Risk: lethal trifecta (untrusted content + secrets + prod-capable write); one injected/hallucinated command leaks secrets, changes IAM, deletes data; with prod on acc2 → customer data.
- Recommendation: (1) aa-agent-dev role: read/describe + ECS exec Dev; no GetSecretValue except e2e/test allowlist; no iam:*, rds delete/modify, s3 delete; apply/migrate/IAM CI-only (OIDC) or human-only. (2) GitHub App or fine-grained PAT for agents on the 5 repos: contents + PR write, no admin/secrets/gist/workflow. (3) permissions.deny for dangerous verbs in ~/.claude/settings.json. (4) /sandbox network allowlist for autonomous runs. (5) never switch auto mode off to let the agent merge/apply.
- Standards: OWASP Agentic ASI03/ASI02; LLM06; NIST SSDF PO.5.1/PO.5.2; Claude Code security guidance.

### D2 — No recorded, independent review gate: AI writes and merges its own changes — CRITICAL, S, automatable
- Evidence: reviews null, enforce_admins false; root unprotected; Infra 403; CIS rulesets disabled; last 148 merged PRs 0 reviews, author == merger; contradictory rules (project CLAUDE.md, Booking CLAUDE.md:7 vs `Bash(gh pr merge:*)` and memory agent-team-pilot.md); no CODEOWNERS.
- Risk: approval invisible in GitHub → fails SOC 2 CC8.1 / ISO A.8.32 questionnaires; injected change reaches Dev/prod with only CI as gate; Infra (IAM, RDS, network) unprotected.
- Recommendation: (1) agent identity (GitHub App bot) as PR author, Nghiệp as approver; (2) org rulesets on main/master (1 CODEOWNERS approval, approval of most recent push, required checks, no bot bypass, block force-push/deletion); (3) protect root; (4) Infra: GitHub Team (~USD 4/user/month) or env-protected terraform-apply with manual approval; (5) one ADR for who merges what, delete contradicting lines; (6) SOC 2 compensating control: monthly independent review (advisor/contractor) of merged-PR + deploy log.
- Standards: NIST SSDF PW.7; Scorecard Code-Review/Branch-Protection; SOC 2 CC8.1; ISO 27001 A.5.3/A.8.32; SLSA Source track.

### D3 — Public repos written by agents have secret scanning/push protection disabled; root repo has no CI — HIGH, XS, automatable
- Evidence: 4 public repos disabled; gitleaks only in Infra (.github/workflows/secret-scan.yml); root has no .github (holds session logs, audits, skills, committed settings, legal draft); project settings.local.json (gitignored) holds a literal former e2e password in a curl allow rule; DM-6.10 notes "The repos are public".
- Risk: agents produce lots of docs/audits/scripts quickly; a pasted token/DSN/password becomes public on push undetected; root exposes ops detail (account IDs, hostnames, admin header patterns, ECS exec recipes).
- Recommendation: enable secret scanning + push protection + validity checks today; pinned gitleaks job in each app repo and root as required check; decide root private (needs Team to keep protection); remove literal password from settings.local.json and disable stale e2e-test-admin user.
- Standards: NIST SSDF PS.1/PO.5; OWASP LLM02; Scorecard.

### D4 — Agent guardrail hook uses deny-list text matching, covers subagents only, and is bypassable — HIGH, M, automatable
- Evidence: exits 0 without agent_id; regex on raw command string — python subprocess, curl to api.github.com, `bash -c "$(…)"`, base64 not matched (inference, untested); missing destructive verbs (ec2 terminate, cloudformation delete-stack, logs delete-log-group, s3api delete-object, ecs delete-service, scheduler/events delete, rds-data); test asserts get-secret-value allowed; false positives (read-only grep blocked in this audit and again in synthesis); ~/.claude/hooks/pre_bash.sh only blocks `rm -rf /` and `git push --force`.
- Risk: false sense of safety; Anthropic docs: "A deny rule matches the command as written"; injected/confused agent performs unanticipated destructive actions.
- Recommendation: keep hooks as defense in depth; enforce via agent IAM role (D1), GitHub App token without merge/admin, Claude Code sandbox (filesystem + network allowlist) for subagents and Kiro; switch hook to allow-list for aws/gh (describe|list|get|logs; gh pr view/checks/api GET) and apply to main session with explicit human-approval path; ConfigChange hook logging settings edits.
- Standards: OWASP Agentic ASI02/ASI05; LLM06; Claude Code docs.

### D5 — No AI governance baseline before selling — HIGH, M, not automatable
- Evidence: docs/adr/README.md:21 0009 reserved (AA-804); backlog README.md:56 AA-804 "later"; DM-6.4 (02-data-management.md:210, 361); AI clause draft NOT APPROVED (AA-820 due 11/11/2026); portal shows AI-generated notice at review/publish, no documented machine-readable marking in API output (inference).
- Risk: EU AI Act Art. 50, GDPR Art. 28/30/35 (DPA, RoPA, DPIA for traveller data on LLM path), Anthropic AUP 12/11/2026; cannot answer questionnaires, sign DPAs or prove DM-6.4.
- Recommendation: minimal ADR 0009 now; AI Use Register generated from llm_role_config + llm_model_catalog (stage, model, provider, account/region, data classes, ZDR/DPA status, human oversight) published as sub-processor list; cheap automated PII check in both gateways (regex email/phone/passport + NE heuristics) on prompts and llm_call_log/decision_log writes with unit test + metric; `ai_generated: true` + model/stage metadata in tenant API payloads; counsel finishes AA-820 before 11/11.
- Standards: EU AI Act Art. 50; GDPR Art. 28/30/35; NIST SP 800-218A + AI RMF GOVERN/MAP; ISO/IEC 42001; LLM02.

### D6 — Prompt/model changes ship without an eval gate — HIGH, M, automatable
- Evidence: eval-regression.yml dispatch-only, [s1_old] only, last run 2026-08-01; 85 commits since touched services/**/prompts*.py or shared/llm_client/*; runtime model switch via PATCH /admin/llm-config/{stage} (admin_llm_ops.py:206), audited + shadow but no eval required.
- Risk: fidelity/brand-voice regressions (invented activities, meals, times) reach tenants; lessons log shows recurrence; AI-authored prompt edits where human review is weakest.
- Recommendation: frozen golden set (~20 tours across countries); path-filtered required PR job on prompts/**, shared/llm_client/**, llm_role_config migrations with hard cap (≤ USD 1/run, per paid-runs memory) vs committed baselines (fidelity, Jev pass rate, length); require eval run id in PATCH /llm-config body (or passing shadow window); extend to T2/T9.
- Standards: NIST SP 800-218A PW.8, AI RMF MEASURE; OWASP LLM09; ISO/IEC 42001 A.6.

### D7 — Agent instructions and permission config stale, contradictory, over-grown — HIGH, S, not automatable
- Evidence: ~/.claude/settings.json autoMode.environment describes org AdventureAsia365-CIS, path /home/nghiep/projects/aa-cis/AA-CIS-App, AAA PROD/STG as protected (now "not part of the ecosystem"), trusted bucket aa-cis-tfstate-867490540162 (acc1); global CLAUDE.md mandates handoff.md + ECS stop reminders contradicted by memory dev-ecs-left-running.md; merge rules conflict (D2); project settings ~110 one-off allows + uncommitted +125-line diff; settings.local.json ~130 entries incl. `python *`, `gh api *`, `gh pr *`, `pip install *`.
- Risk: auto-mode classifier judges actions against a wrong environment picture (org, protected accounts, public repos) → miscalibrated safety; non-deterministic agent behaviour; wildcards silently widen unprompted actions.
- Recommendation: one cleanup PR rewriting autoMode.environment from current facts (org AdventureAsia365-Ecosys, acc2/acc3/acc1 roles, prod-to-be on acc2, public repo list); prune allow lists to a reviewed minimal set, move one-offs out; add deny list; CLAUDE.md files point to one ADR for merge/deploy authority; quarterly agent-config review in backlog time-gated checks.
- Standards: NIST SSDF PO.1/PO.3; OWASP Agentic ASI09; Claude Code docs (/permissions audits, managed settings).

### D8 — No SAST or blocking dependency gates for AI-generated code — HIGH, XS, automatable
- Evidence: CodeQL not-configured on CIS/Booking/TP; CIS ci.yml:51 pip-audit `|| true`; Trivy report-only (ci.yml:194); no dependabot.yml; kiro-reviewer only "when risky" (§3.3); /security-review skill exists but not mandated.
- Risk: injection, authZ (IDOR on tenant endpoints, API1/API5), unsafe deserialization; Security Audit green by construction; agents add packages incl. hallucinated ones (slopsquatting).
- Recommendation: CodeQL default setup (python + JS/TS) as required check; pip-audit/npm audit failing on high/critical with dated allowlist; Trivy fail on fixable CRITICAL; Dependabot pip/npm/github-actions; /security-review in orchestrator gate for diffs touching auth, routers, migrations.
- Standards: NIST SSDF PW.7/PW.8/RV.1; Scorecard SAST/Dependency-Update-Tool/Vulnerabilities; ASVS 5.0 L2; OWASP API Top 10; LLM03.

### D9 — No build provenance; actions pinned by mutable tags — MEDIUM, S, automatable
- Evidence: no attest-build-provenance in CIS ci.yml/deploy-dev.yml or Booking deploy-dev.yml; tag pins (checkout@v5, configure-aws-credentials@v6, trivy-action@v0.36.0); `dev` env rules []; SBOM generated but not attested.
- Risk: nothing proves the ECS image was built by CI from reviewed main; compromised action tag exfiltrates OIDC-assumed AWS role.
- Recommendation: attest-build-provenance + attest-sbom for ECR digest (free via Sigstore on public); deploy runs `gh attestation verify` or checks digest; SHA pins + Dependabot; dev env main-only + OIDC sub `repo:…:environment:dev`; later reusable workflow for L3.
- Standards: SLSA v1.2 Build L2/L3; Scorecard Pinned-Dependencies/Token-Permissions; NIST SSDF PS.2/PS.3.

### D10 — Weak provenance of AI-authored code — MEDIUM, S, automatable
- Evidence: 94/398 commits with Claude trailer; Kiro only in PR body; all commits under human identities; Kiro transcripts gitignored and deleted after merge.
- Risk: can't answer "which code did an AI write, under what brief, reviewed by whom" for questionnaires, forensics, rework metrics, licence/IP scoping.
- Recommendation: CI commit-msg check for trailers `AI-Agent: claude-code|kiro|none` + `Refs AA-xxx`; auto-label PRs `ai-generated`; agent App as commit author; kiro-reviewer verdict + transcript SHA-256 in PR body; archive transcripts to private S3 for 90 days.
- Standards: NIST SP 800-218A / SSDF PS.3; SLSA Source track.

### D11 — Prompt-injection defense narrow; external and traveller inputs unassessed — MEDIUM, M, automatable
- Evidence: prompt_sanitize.py docstring "self-injection containment … not general-purpose prompt-injection defense" (regex list); TP customer-facing tp_compose (llm_gateway.py:531); grep sanitize/injection in TP backend → nothing (inference: unverified whether traveller free text reaches tp_compose prompts); scraped supplier/tour sources and web research feed CIS prompts.
- Risk: injected source page or traveller message steers content (fake claims/links/misinformation), leaks system prompts/brand rules, burns spend; improper output handling when HTML/links published to WordPress/Facebook.
- Recommendation: one-page threat model per LLM entry point (source ingest, tenant brand, traveller input, publish channels); external text as delimited data; structural output validation (JSON schema, URL allowlist, HTML sanitizer before publish); injection test set in eval golden set (D6).
- Standards: OWASP LLM01/LLM05/LLM07; Agentic ASI01.

### D12 — Separation of duties defeated in tests: agent holds both maker and checker accounts — MEDIUM, XS, automatable
- Evidence: memory e2e-admin-login.md: agent-controlled e2e-claude-code and e2e-claude-code-2 (aa-cis/dev/e2e-test-admin, -2) for Booking maker-checker verification; older e2e-test-admin DB user still exists with stale password.
- Risk: fine for Dev but turns maker-checker into single-actor control if carried to staging/prod; stale admin user = unnecessary live credential on internet-facing admin API.
- Recommendation: document agent e2e accounts as Dev-only, enforced by env check refusing them when ENVIRONMENT=prod; disable stale e2e-test-admin; prod checker = human Cognito identity with MFA.
- Standards: SOC 2 CC6.1/CC6.3; ISO 27001 A.5.3; ASVS 5.0 V8.

### D13 — No audit telemetry of agent activity — MEDIUM, S, automatable
- Evidence: no OTel/monitoring in ~/.claude/settings.json or project settings; no ConfigChange hook; agent AWS calls appear in CloudTrail under the human role session (inference); Kiro transcripts deleted.
- Risk: hard to reconstruct agent vs human actions after an incident (2 wrong-account Secrets Manager writes already, AA-517); SOC 2 CC7.2 expects privileged-activity monitoring.
- Recommendation: Claude Code OTel export (CloudWatch or Grafana free); distinct AWS session name or separate role for agents; ConfigChange hook; retain transcripts 90 days in private bucket.
- Standards: SOC 2 CC7.2/CC7.3; OWASP Agentic ASI10; Claude Code docs.

### D14 — GitHub org hygiene: 2FA not required, Free plan limits on private Infra, two accounts with identical broad scopes — MEDIUM, XS, not automatable
- Evidence: plan free, two_factor_requirement_enabled=false, members_can_create_repositories=true; members adventure365, pqnghiep1354; both gh accounts gist/read:org/repo/workflow; Infra protection/rulesets 403.
- Risk: takeover of either identity → full write on all repos incl. workflows assuming AWS roles; gist scope enables quick exfiltration; IAM/RDS Terraform repo has weakest controls.
- Recommendation: require 2FA (passkeys); restrict repo creation to owners; drop gist scope; fine-grained tokens per purpose; GitHub Team (~USD 4/user/month) mainly to protect Infra.
- Standards: Scorecard Branch-Protection/Token-Permissions; SOC 2 CC6.1; CIS GitHub Benchmark.

### D15 — Delivery performance (DORA) and AI rework not measured — LOW, S, automatable
- Evidence: no workflow/dashboard/doc computing the 5 DORA metrics; raw data exists (deploy-dev runs, ECS deployment history, PR timeline).
- Risk: can't tell whether AI speed turns into rework; no reliability trends for customers; no error budgets before prod.
- Recommendation: weekly scheduled Action (read-only token) computing 5 metrics from merged PRs, deploy runs, fix/revert PRs, split by AI-Agent trailer (D10); write to docs/metrics/ or a small artifact page; review at session start.
- Standards: DORA 5 metrics (dora.dev; 2024–2025 State of DevOps).
