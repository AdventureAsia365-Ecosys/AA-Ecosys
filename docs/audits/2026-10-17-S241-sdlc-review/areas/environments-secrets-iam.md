# Area 3 — Environments, configuration & secrets, AWS accounts/IAM, network edge, backups/DR, data residency

Scope: acc2 005097885195 + acc1/acc3 satellites. Read-only, 17/10/2026. STS identity = assumed-role/nghiep-admin-8h-session in 005097885195. IAM CLI calls blocked for subagents by .claude/hooks/subagent-guardrails.sh → IAM facts from Terraform source; root-account MFA/key status UNKNOWN.

Synthesis verification notes (`../README.md` §8.3): "plan as required PR check" listed below as a strength is NOT accurate — Infra has no branch protection (403), so plan is advisory. `[profile aa365-agent]` exists in ~/.aws/config (line 79) but is unused. Prod-in-separate-account recommendation conflicts with the decided ADR 0001 (prod on acc2); synthesis keeps the decision and lists compensating controls.

## Current state (observed)

- **Environments**: only Dev. Terraform roots: accounts/aa365 (acc2 main; S3 backend aa-cis-tfstate-005097885195 key dev/terraform.tfstate + DynamoDB lock; bucket versioned, SSE-S3, bucket PAB on), accounts/acc1-bedrock and accounts/acc3-bedrock (S3 backend with profile, no lock). envs/ empty (removed AA-841). Infra CONTEXT.md: new env → own accounts/<name>/; data standard 03-scaling.md C7.2c says envs/prod/ — documents disagree. ADR 0001:79 prod on acc2. Names hardcoded "dev" (cicd_split.tf 26 literals, booking.tf 10); CI boundary keyed on aa-*-dev-*.
- **Config flow**: ECS api (aa-cis-dev-api:659) and worker (:216) get 12-13 plain env + 6 secrets via valueFrom (aa-cis/dev/rds, openai-key, admin-secret, jwt-secret, dataforseo login/password). Booking (aa-booking-dev-api:28) 6 env + 1 secret (booking/dev/database-url). Terraform owns task env (modules/ecs/main.tf:298-328, 499-524); CI clones latest revision and swaps image (ignore_changes task_definition). Lambda aa-cis-dev-dfs-balance-check holds ADMIN_SECRET plaintext (dfs_balance.tf:161; value also in TF state). TP assembly/browse hold TRIPPLANNER_API_KEY plaintext (tripplanner.tf:334/384 random_password); their DSN uses *_ARN correctly. 27 secrets: RotationEnabled null on all; default aws/secretsmanager key. Change dates: aa-cis/dev/rds + dataforseo 2026-07-07, jwt-secret 2026-09-01, admin-secret 2026-10-17 (rotated today). KMS: only AWS-managed aliases.
- **GitHub**: Free, 2FA not required, members can create public repos; CIS-App, Booking, TP, AA-Ecosys PUBLIC with secret scanning/push protection disabled; Infra private. Envs: CIS-App dev (no rules), prod (protected_branches), staging, Preview, Production; Infra dev/staging/prod no rules; Booking dev custom branch policy. Secret names as in Area 1 (CIS ADMIN_SECRET, VERCEL_TOKEN, VERCEL_AUTOMATION_BYPASS_SECRET, VERCEL_DEPLOY_HOOK, ACPCORE_READ_TOKEN, E2E_ADMIN_*, ECR/ECS as secrets, dev AWS_ROLE_ARN; Infra TF_VAR_DB_PASSWORD repo-level 2026-07-07, ROOT_REPO_DOCS_TOKEN, AWS_ROLE_ARN, TF_STATE_BUCKET, prod AWS_ROLE_ARN; Booking dev env vars).
- **OIDC**: per-repo/per-job roles, immutable subjects. Apply role trust `<infra>:environment:prod` (cicd_split.tf:515-519), CIS deploy `<cis-app>:environment:dev` (:311-317); comments say "main only" relies on env branch rules — NOT set live.
- **Vercel** (3 projects, SSO protection all_except_custom_domains): aa-cis-frontend ADMIN_SECRET (production+preview), ADMIN_USERNAME/PASSWORD, ADMIN2_USERNAME/PASSWORD, INTERNAL_API_KEY, SENTRY_AUTH_TOKEN, API_URL, NEXT_PUBLIC_*; aa-booking-admin BOOKING_API_URL; aa-tripplanner TRIPPLANNER_API_KEY, BROWSE/TRIP_API_URL, NEXT_PUBLIC_MAPBOX_TOKEN. Vercel "Production" target points at Dev backend.
- **Network**: VPC 10.2.0.0/16 + default VPC; no NAT gateway, single t4g.nano NAT instance (IMDSv2); no VPC endpoints; flow logs on 4 subnets; ALB aa-cis-dev-alb internet-facing (80/443) but SG admits only :80 from 10.2.0.0/16; internal NLB + VPC link; REST 4ylo382khg (CIS), 9z3xnalp59 (Booking), HTTP API 9vqkfbukvh (TP) keep execute-api endpoint; WAF aa-cis-dev-waf on ALB only (var.waf_protect_rest_api_stages default false); CIS stage throttling -1, Booking 20 rps.
- **Account security services**: one CloudTrail (single-region, log validation on, no KMS); GuardDuty none; Security Hub not subscribed; Config no recorder; Access Analyzer none; account-level S3 BPA not configured.
- **RDS aa-cis-dev-db**: db.t4g.small, single-AZ, encrypted (aws/rds), private, deletion protection, 7-day PITR, IAM DB auth off, no ManageMasterUserPassword; master aa_cis_admin = CIS runtime (DM-8.9). Snapshots daily + 4 manual. AWS Backup none. No restore drill (AA-829 "later"). 11 MB real-data dumps (6 schema .dump incl. tripplanner) at docs/backups/2026-09-16 (gitignored).
- **S240 incident**: GitHub token + RDS master password printed in a local transcript; decision "để nguyên, xoay khi lên prod" (docs/sessions/2026-10-16-S240-...md:37,73).
- **App auth**: X-Admin-Secret static god-key compared with == (auth.py:216-218, v1_social.py:32-34, v1_rules.py:32, v1_tours.py:685); only v1_pipeline.py:51 uses hmac.compare_digest. JWT HS256, one JWT_SECRET for staff + tenant (auth.py:32-38, :85). Booking cross-app tokens RS256 (booking-jwt-signing-key). Tenant API keys hashed (main.py:266-271).
- **Data residency**: all PII in us-west-1; no doc covers residency/cross-border transfer (grep residency/PDPD/PDPL/GDPR/Decree 13 → nothing).

## Strengths

- Per-repo, per-job OIDC roles with immutable subject claims; no long-lived AWS keys in CI; legacy aa-cis-dev-role retired with tombstone deny.
- Permission boundaries for CI-created roles (aa-workload-boundary; tf-apply boundary DenyIamWrites, DenyCreateRoleWithoutWorkloadBoundary, DenyBoundaryRemoval).
- ECS secrets via Secrets Manager valueFrom; per-app secret prefixes (DM-8.6); Booking deploy role scoped to own ECR/family/service.
- Remote state versioned/non-public + DynamoDB lock; separate state per account; manual dispatch apply; gitleaks on Infra PRs; tfvars gitignored. (Plan is NOT a required check — see note.)
- RDS private, encrypted, deletion protection, final snapshot, force_ssl, log_parameter_max_length=0, Performance Insights, alarms in Terraform.
- Edge: API GW → VPC link → internal NLB → ALB (SG VPC-only); WAF CommonRuleSet enforced with credential headers redacted in logs.
- DB Migrate refuses apply when job tables busy; destructive migrations snapshot first; Booking ECR immutable; Booking RS256; tenant API keys hashed.
- Strong written data standards (DM-6 PII, DM-8 access, DM-9 backup/DR, C7.2 prod) and designed agent-session least-privilege role (AA-730).

## Gaps

### E1 — OIDC trust for tf-apply and CIS deploy relies on unconfigured env protections — CRITICAL, S, automatable
- Evidence: cicd_split.tf:515-519 (comment: env branch rule + required reviewer keep it to reviewed main) vs Infra prod rules=[]/branch null; cicd_split.tf:311-317 vs CIS dev rules=[]/branch null; org Free. INFERENCE: env protection for private repos unavailable on Free.
- Risk: anyone/agent/stolen PAT pushing any branch can assume the apply role (10 managed policies of old CI role) → whole acc2 stack, DB Migrate, secrets; same path deploys arbitrary images to CIS Dev.
- Recommendation: CIS dev/prod "Selected branches: main" now (public repo); Infra: GitHub Team or customise OIDC sub (`PUT /repos/.../actions/oidc/customization/sub` include_claim_keys [repo, context, ref, job_workflow_ref]) and pin trust to ref main + exact workflow; CI drift guard on env config.
- Standards: SLSA Build L2/L3; NIST SSDF PO.5/PS.1; Scorecard; AWS OIDC best practice.

### E2 — Leaked RDS master password (= CIS runtime DSN) and GitHub token deliberately unrotated — CRITICAL, S, not automatable
- Evidence: S240 log :37, :73; aa-cis/dev/rds LastChangedDate 2026-07-07; TF_VAR_DB_PASSWORD 2026-07-07; MasterUserSecret null; DM-8.9 runtime = master; booking.customers PII.
- Risk: known-exposed credential valid indefinitely; GitHub token usable from internet (push to public repos deploying via OIDC, read Infra); master gives full RW on all 3 apps incl. PII; Dev data is real.
- Recommendation: revoke GitHub token now, re-issue fine-grained/App token; manage_master_user_password=true in modules/rds, update TF_VAR handling and aa-cis/dev/rds (Nghiệp edits by hand); runtime off master (AA-817 X1); delete transcripts; record incident in docs/audits.
- Standards: NIST SP 800-53 IA-5(1)/IR-4; CIS Controls 5.2/16; OWASP ASVS V2.10.

### E3 — Public repos with secret scanning/push protection disabled; org 2FA not required — HIGH, XS, automatable
- Evidence: 4 public repos secret_scanning/push_protection/dependabot_security_updates disabled; org 2FA false, members can create public repos, push-protection default for new repos false; root publishes db-schema-reference.md, RLS/role details, account IDs, audit findings.
- Risk: accidental key commit (already happened: plaintext acc1 creds in envs/dev/terraform.tfvars, AA-841) world-readable within minutes; account without 2FA = takeover into OIDC-trusted repos; public audits/schema maps aid attackers.
- Recommendation: enable scanning/push protection/Dependabot updates; require 2FA; disable member public repo creation; make AA-Ecosys private or move security audits/schema refs to Infra; org ruleset requiring PR + checks.
- Standards: Scorecard; GitHub secret protection baseline; CIS Controls 6.5; NIST SSDF PS.1.

### E4 — Prod planned in the same account and same hardcoded-dev Terraform root; no staging; docs conflict — HIGH, L, not automatable
- Evidence: ADR 0001:79-80; dev literals (cicd_split.tf 26, booking.tf 10, cicd.tf 9); CI boundary aa-*-dev-* (cicd_split.tf:19-29); db-migrate.yml:54 env prod targeting Dev (03-scaling C7.2d); C7.2c `envs/prod/` vs CONTEXT.md `accounts/<name>/`; ecosystem-architecture.md has no env/promotion section.
- Risk: dev and prod share IAM, quota, KMS and blast radius; agent admin or Dev CI role can reach prod; copy-paste drift; no rehearsal env.
- Recommendation (area): ADR amending 0001 to create a prod account (and optionally staging) via AWS Organizations/IAM Identity Center; refactor accounts/aa365 into reusable `stacks/platform` per env; `environment` input on DB Migrate/deploy; reconcile C7.2c with CONTEXT.md. (Synthesis: keep prod on acc2 per decision, apply compensating controls, revisit later.)
- Standards: AWS WA SEC01-BP01; NIST SSDF PO.5.1; 12-factor V/X.

### E5 — AI agent shells run with the full admin role instead of the AA-730 agent-session role — HIGH, XS, automatable
- Evidence: subagent STS = assumed-role/nghiep-admin-8h-session; agent_session.tf header (AA-730): agents reading untrusted input must use profile aa365-agent; "The MFA'd admin profile stays with Nghiệp, not in agent shells"; global CLAUDE.md instructs --profile aa365-admin everywhere.
- Risk: prompt injection in supplier file/Jira/web runs with full admin; only barrier is a local regex hook.
- Recommendation: AWS_PROFILE=aa365-agent for agent sessions (settings.json env + CLAUDE.md/skills); aa365-admin human-only; extend agent role via reviewed Terraform; session-start check fails if agent identity is admin.
- Standards: NIST SP 800-53 AC-6; OWASP LLM06; AWS SEC03.

### E6 — No account-level threat detection, config audit or S3 public-access guard — HIGH, S, automatable
- Evidence: guardduty list-detectors empty; securityhub InvalidAccessException; no Config recorder; no Access Analyzer; s3control get-public-access-block NoSuchPublicAccessBlockConfiguration; CloudTrail IsMultiRegionTrail=false, KmsKeyId null while us-east-1 resources exist (ACM for Cognito, custom_domains.tf).
- Risk: credential misuse/crypto-mining/exfiltration unnoticed; us-east-1 regional activity unlogged; future bucket policy mistake exposes PII.
- Recommendation: Terraform GuardDuty (a few USD/month; state cost first) + SNS, IAM Access Analyzer (free), account S3 BPA, multi-region CloudTrail; Security Hub FSBP + Config later.
- Standards: CIS AWS Foundations 3.x/4.x/2.1.4; Security Hub FSBP; NIST CSF DE.CM.

### E7 — Static X-Admin-Secret god-key in 6 places, non-constant-time compare, manual rotation — HIGH, M, automatable
- Evidence: == compares at auth.py:216-218, v1_social.py:32-34, v1_rules.py:32, v1_tours.py:685 (only v1_pipeline.py:51 compare_digest); copies in Secrets Manager, ECS api+worker, GitHub ADMIN_SECRET, Vercel production + preview, Lambda env plaintext (dfs_balance.tf:161, also in state); today's rotation needed separate updates (SM 05:51Z, GitHub 05:56Z); header grants role admin, tenant AA internal.
- Risk: any copy leaking (incl. every Vercel preview of any branch) = full admin over all tenants, no attribution; timing leak; error-prone rotation gets skipped.
- Recommendation: shared verifier with hmac.compare_digest; remove from Vercel preview and GitHub if unused; Lambda reads by ARN; target: Cognito workforce JWT for humans (ADR 0006), per-caller machine creds (IAM-authorized route or signed token) with audit; retire shared secret.
- Standards: OWASP API2:2023; ASVS V2/V3; NIST SP 800-63B; CWE-208.

### E8 — CIS public API has no effective rate limiting — HIGH, S, automatable
- Evidence: wafv2 list-resources-for-web-acl API_GATEWAY empty; variables.tf:188-191 default false; get-stages 4ylo382khg dev webAclArn None, throttlingRateLimit -1; modules/waf/main.tf:145-146 rate rule aggregate IP without forwarded_ip_config. INFERENCE: at ALB the source IP is the internal NLB → per-IP rate/geo rules can't act per client.
- Risk: flood of LLM-cost/DB-heavy endpoints → cost spike, shared RDS exhaustion (Booking, TP); brute force on X-API-Key/X-Admin-Secret.
- Recommendation: grant apigateway:SetWebACL to apply role, waf_protect_rest_api_stages=true (CIS first, Booking after geo list confirmed); default stage throttling + usage plans per tenant key; disable execute-api once custom domains confirmed.
- Standards: OWASP API4:2023; AWS WA REL05/SEC06.

### E9 — No secret rotation, plaintext secrets in Lambda env/TF state, one HS256 key for staff and tenant JWTs, no CMK — MEDIUM, M, automatable
- Evidence: 27 secrets RotationEnabled None, LastRotatedDate None; jwt-secret since 2026-09-01, dataforseo 2026-07-07, openai-key 2026-08-21; auth.py:38 HS256; auth.py:85 "Staff JWTs share JWT_SECRET"; TRIPPLANNER_API_KEY plaintext (tripplanner.tf:334, 384); only aws/* KMS keys; ECR AES256.
- Risk: accumulated exposure; JWT secret holder mints staff + tenant tokens for any tenant; plaintext in Lambda config/state; no CMK → cannot share snapshots cross-account.
- Recommendation: rotation policy (90 days; immediate on suspected exposure) in data-standards; RDS-managed master rotation; asymmetric JWT (RS256/ES256 + kid) or separate secrets + kid; Lambdas fetch by ARN at runtime (Powertools cache); CMK for prod RDS/Secrets/S3.
- Standards: NIST SP 800-57; CIS AWS 2.x; ASVS V6.4; 12-factor III.

### E10 — Backup/DR unproven — MEDIUM, M, automatable
- Evidence: MultiAZ=false, BackupRetentionPeriod=7, aws/rds key (no cross-account share); backup list-backup-plans []; docs/backlog/README.md:63 AA-829 "later"; 03-scaling.md:336 "Restore drill | never"; du docs/backups/2026-09-16 = 11M (violates DM-6.10).
- Risk: unknown RTO/RPO; account incident destroys primary + backups together; unencrypted laptop dumps with possible PII.
- Recommendation: AA-829 PITR drill now (restore temp instance, smoke per schema, record RTO, delete); move dumps to encrypted private S3 and delete locally; prod: Multi-AZ, 14-day PITR, AWS Backup cross-region (+ cross-account with CMK), quarterly drill in docs/audits.
- Standards: NIST SP 800-34 CP-9/CP-10; AWS WA REL09; ISO 27001 A.8.13.

### E11 — Env naming and promotion model inconsistent across GitHub, Vercel, ECR — MEDIUM, S, automatable
- Evidence: Vercel "production" carries Dev API_URL/ADMIN_SECRET; Infra env "prod" runs Dev applies (db-migrate.yml:54, terraform-apply.yml:18); unused CIS envs; image tags env-specific (aa-cis-dev-api:dev-<sha>); CIS ECR MUTABLE (Booking IMMUTABLE); NEXT_PUBLIC_* baked per Vercel target.
- Risk: wrong-target deploys/migrations when real prod appears; mutable tags break provenance; per-env rebuilds mean tested ≠ shipped.
- Recommendation: one vocabulary (dev/staging/prod) across GitHub envs, Vercel custom environments, Terraform; rename Infra prod → dev-apply now; CIS ECR IMMUTABLE, SHA-only tags, promote same digest; delete unused envs; runtime config instead of NEXT_PUBLIC baking where possible.
- Standards: 12-factor V/X; SLSA; DORA.

### E12 — Stale and over-broad static credentials in GitHub and Vercel — MEDIUM, S, automatable
- Evidence: ACPCORE_READ_TOKEN (2026-08-21; ACP repos archived — note: still exist, see §8.3), VERCEL_DEPLOY_HOOK (2026-05-13; duplicate hook removed in CIS #783), E2E_ADMIN_PASSWORD, non-secrets as secrets; TF_VAR_DB_PASSWORD repo-level; ROOT_REPO_DOCS_TOKEN PAT cross-repo write (db-schema-dump.yml:18-20); Vercel ADMIN_USERNAME/PASSWORD, ADMIN2_USERNAME/PASSWORD, INTERNAL_API_KEY.
- Risk: orphan tokens valid with no owner; repo-level secrets exposed to every workflow/branch; static admin passwords bypass Cognito/MFA; PAT tied to a person.
- Recommendation: delete orphans (grep first); TF_VAR_DB_PASSWORD into protected env or drop after RDS-managed; non-secret IDs → variables; App installation token instead of PAT; Cognito workforce users with MFA instead of env logins; secrets inventory in docs.
- Standards: Scorecard Token-Permissions; NIST SSDF PS.1; CIS Controls 5.3.

### E13 — Network single points of failure; no private AWS service endpoints — MEDIUM, S, automatable
- Evidence: no NAT gateways; single t4g.nano NAT instance for all private subnets; no VPC endpoints (ECR, Secrets Manager, S3, CloudWatch, cross-account Bedrock all via NAT instance); ALB internet-facing (SG-only isolation); default VPC 172.31.0.0/16 exists.
- Risk: loss/overload of one nano instance stops task starts and LLM calls; fine for Dev, blocker for sellable SLA.
- Recommendation: Dev: free S3 gateway endpoint now. Prod: NAT GW per AZ (≈ USD 32+/AZ/month) or interface endpoints (ECR api/dkr, Secrets Manager, Logs, STS), internal ALB, delete default VPC; state cost first.
- Standards: AWS WA REL10/SEC05; CIS AWS 5.x.

### E14 — Data residency, cross-border transfer and processor obligations undocumented — MEDIUM, M, not automatable
- Evidence: PII (booking.customers, tripplanner.customers, inbox/outbox payloads; DM-6.1) in us-west-1; grep for residency/PDPD/PDPL/GDPR/Decree 13 empty; DM-6.8 requires DPA template before first tenant — none; DM-6.8/DM-8.9: aa_cis_admin (CIS runtime) can read crm.* and Booking PII until AA-817 X1.
- Risk: cross-border transfer assessments and processor contracts (Vietnam Decree 13/2023, 2025 PDP Law; GDPR for EU travellers) may stall sales/audits; over-broad DB access weakens tenant-as-controller promise. (Legal applicability = inference; lawyer / Ms. Thư's call.)
- Recommendation: data-processing register (data classes, region, sub-processors AWS, Vercel, OpenAI, Bedrock acc1/acc3, Jev, Mapbox, SES) + residency note in prod ADR; DPA template + transfer checklist as calm proposal for Ms. Thư; finish AA-817 role split.
- Standards: ISO 27701; GDPR Art. 28/30/44; Vietnam Decree 13/2023 (inference); ASVS V8.

### E15 — Terraform hygiene: sensitive plan files on disk, backup files tracked, satellite roots without locking — LOW, XS, automatable
- Evidence: accounts/aa365/aa365.tfplan (144 KB, 2026-07-07) and accounts/acc3-bedrock/*.tfplan on laptop (gitignored; plans contain secrets in plaintext); `git ls-files` tracks main.tf.bak, main.tf.bak2; acc1/acc3 backends without dynamodb_table/use_lockfile; state bucket SSE-S3 while state contains RDS password, admin secret data source, random_password values.
- Risk: old plans/state leak secrets; concurrent satellite applies corrupt state; dead files confuse agents.
- Recommendation: delete local *.tfplan after apply (runbook step); remove main.tf.bak*; `use_lockfile = true` (TF ≥1.10) or DynamoDB for acc1/acc3; SSE-KMS CMK on state bucket for prod; mark secret outputs/variables sensitive.
- Standards: HashiCorp sensitive-data guidance; CIS AWS 2.1.1.
