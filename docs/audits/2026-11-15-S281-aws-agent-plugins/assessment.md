FIT ASSESSMENT: AWS Agent Plugins for AA_Ecosys (skeptical platform view, 2026-11-15)

Bottom line: don't install any of the AWS plugins as bundles. Add the remote AWS Knowledge MCP on its own. Trial the Pricing MCP on its own, with a pinned version and an explicit profile and region. Skip the AWS API MCP, the IaC/cfn tooling, deploy-on-aws, aws-serverless and databases-on-aws. Most of what the post praises is built for CloudFormation, CDK or SAM. AA is 100% Terraform (146 .tf files, no template.yaml, cdk.json or samconfig).

What I checked myself in the repo (read-only):
- `.claude/settings.json` has PreToolUse matchers for Bash, Workflow, `mcp__.*` and Edit|Write.
- `.claude/hooks/subagent-mcp-guardrails.sh` line 10 exits 0 when the call has no agent_id. So the main session gets no MCP guard at all.
- `get-secret-value` appears 3 times in `.claude/settings.json` and once in `.claude/settings.local.json`.
- It is also used in the runbooks `docs/ops/runbooks/llm-anthropic-api-key.md`, `secret-rotation.md` and `embedding-re-embed.md`.

## A. Verdict per component

| Component | Verdict | Reason |
|---|---|---|
| AWS Knowledge MCP (remote HTTP, `knowledge-mcp.global.api.aws`) | **ADOPT** (standalone, user scope) | No credentials, no AWS account, no local process (no RAM cost), free, read-only. It targets AA's real pains: the API validation and apply-order rules that plan/validate miss (WAF description characters, WAFAssociatedItemException order, `iam:ListInstanceProfilesForRole`, Cognito scope timing, REST API `binaryMediaTypes`). Its `retrieve_skill` tool serves AWS skills on demand, so we get them without aws-core's always-on context. Rate limits are UNCONFIRMED. |
| Pricing MCP (`awslabs.aws-pricing-mcp-server`) | **TRIAL** (standalone, pinned) | Fits the cost-before-new-service rule, and `analyze_terraform_project` reads .tf files. API calls are free. But it needs credentials (default profile = acc2 MFA role, which is a non-TTY problem), it is pinned `@latest` in the plugin, it is a local Python process, and its own README warns it can build filters wrongly. Its output must be labelled "estimated" (lessons.md:290). |
| AWS API MCP (aws-core's `aws-mcp` proxy → managed server; `aws___run_script`, maybe `call_aws`) | **SKIP** (revisit only read-only, see C step 5) | Bypasses every Bash-pattern guard. The plugin passes no `--profile`, `--region` or `--read-only`, and the region defaults to us-east-1. The run_script sandbox inherits the full nghiep-admin-12h permissions. The CLI plus our hooks already does this job, with guards. |
| aws-core plugin as a bundle (27 skills + aws-mcp + secret-safety hook) | **SKIP** | Its `secret-safety.py` PreToolUse hook denies Bash `secretsmanager get-secret-value`. That breaks 3 runbooks and the 4 allow rules above, and a per-hook disable is UNCONFIRMED. The skills are a context cost on every session. Reach them through Knowledge `retrieve_skill` instead. |
| IaC MCP (`awsiac`: cfn-lint, cfn-guard, CFN troubleshooting, CDK docs) and the "cfn hooks" | **SKIP** | No CloudFormation or CDK exists in AA. No cfn hook exists in any plugin either (see D). awslabs terraform-mcp-server was removed in April 2026, and aws-iac-mcp-server has no Terraform tools. |
| deploy-on-aws (deploy skill + draw.io diagrams + awsiac + pricing + knowledge) | **SKIP the bundle; diagrams DEFER** | 2 of its 3 MCP servers are useless or available separately. The deploy skill's opinions (Elastic Beanstalk, "never App Runner", CFN/CDK output) don't match AA's ADRs. Its draw.io hook only validates XML. lessons.md:197 requires diagrams to come from Terraform state, not prose, which deploy-on-aws doesn't do. AA-697's diagram idea should be fed from `terraform show -json`. |
| aws-serverless | **SKIP** | Turns on `--allow-write` (sam_deploy, deploy_webapp, configure_domain) against the default profile in us-east-1. AA has no SAM; its 7 Lambdas are defined in Terraform. The useful read-only Lambda "diagnose" capability is only reachable through the aws-mcp proxy we are skipping. |
| databases-on-aws | **SKIP** | The only skill is Aurora DSQL, which would be a new paid service. AA runs RDS PostgreSQL 15 (db.t4g.small). Its CloudWatch and DSQL servers ship disabled anyway. |
| amplify / sagemaker-ai / migration-to-aws (GCP→AWS) / aws-transform / location | **SKIP** | Outside AA's domain. |
| Not in the reports but the real Terraform gap | **RESEARCH** | HashiCorp's own terraform-mcp-server (UNCONFIRMED, not inspected). tflint/checkov/trivy in Infra CI (free, deterministic): this is where the "least privilege" benefit would actually come from, given 3 `Action="*"` grants and 78 `"*"`-resource hits. |

## B. Risks for AA and mitigations

1. **Guardrail bypass.**
   - Every AWS rule (subagent-guardrails.sh 22-28, aa_shell_guard ECS-1/ENV-1/RAM-1, pilot_pii_guard) matches Bash text only.
   - The `mcp__.*` hook covers subagents only, and only the GitHub/Linear/Notion/Vercel/Atlassian denylist. So an AWS MCP tool would reach acc2 unguarded from both the main session and subagents. That covers ECS update, RDS, IAM, Secrets Manager writes and exec scripts that skip the PII scan.
   - The `Read(~/.aws/**)` deny doesn't apply, because the MCP server reads credentials itself.
   - Mitigation:
     - Don't install aws-mcp.
     - If any credentialed AWS MCP is added, add `permissions.deny` for `mcp__plugin_.*aws.*` and `mcp__aws.*` write tools.
     - Extend subagent-mcp-guardrails.sh to deny all AWS MCP tools for subagents.
     - Add a main-session PreToolUse hook on `mcp__.*aws.*` that blocks `run_script`/`call_aws` unless the server runs `--read-only`.
     - Defence in depth (an IAM change, so reviewer plus the auto-mode-off window): a Deny on mutating actions with condition `aws:ViaAWSMCPService=true` in the nghiep-admin-12h policy.
   - Correction to the audit: its example tool name `mcp__plugin_aws-core_aws-api__call_aws` is wrong. The server is `aws-mcp` and the documented tool is `aws___run_script`, so the name would be roughly `mcp__plugin_aws-core_aws-mcp__aws___run_script` (inferred). Use a broad regex.

2. **Wrong account or region.**
   - The proxy and Pricing servers take `AWS_PROFILE`, then fall back to `default`. Today that is acc2, but a session that exports `AWS_PROFILE=acc1-admin` or `nghiep_aa365` for Bedrock work would point the MCP at acc1, where nothing else may exist, or at acc3.
   - The region defaults to us-east-1, so resources would land in the wrong region.
   - Mitigation: configure the servers yourself, not through the plugin. Set `AWS_PROFILE` explicitly in the server's env block; for the API proxy that means `--profile aa365-admin --region us-west-1`, and for Pricing, `AWS_REGION` pointed at a Pricing endpoint region. Prefer a dedicated read-only profile.

3. **Credentials and MFA.**
   - nghiep-admin-12h requires MFA, and a stdio subprocess can't prompt.
   - Whether boto3 in the proxy or Pricing server reuses the CLI's STS cache is UNCONFIRMED in both reports. The likely outcome is a startup failure. With `--skip-auth` the proxy would instead go unsigned (only the Knowledge tools work).
   - Fixing this by injecting exported 12h admin credentials into a long-lived process, or by creating an MFA-less role, weakens the security posture. Fix: test once. If it fails, either drop Pricing or create a minimal `pricing:*`-only role (IAM change, reviewed).

4. **Hook collision.** aws-core's secret-safety hook breaks AA's documented `get-secret-value` flows (see the repo check above). Mitigation: don't install aws-core.

5. **RAM with Kiro.**
   - Every local uvx Python server spawns per session and per lane. deploy-on-aws alone starts 2, aws-core 1, aws-serverless 1. RSS per process is UNCONFIRMED.
   - Limits today: WSL has 10 GB plus 4 GB swap, kiro-server takes about 1.2 GB, at most 3 lanes when Kiro runs, and RAM-1 refuses heavy commands below 2 GiB.
   - Mitigation: remote-only servers where possible (Knowledge = 0 local RAM). Keep Pricing at local scope or start it on demand, not at user scope loaded into every lane. Measure RSS on the first start.

6. **Context bloat and wrong-skill choice.** 27 aws-core skills plus 7 serverless skills, with descriptions always in context. Mitigation: no bundles; use `retrieve_skill` on demand; check `claude plugin details <name>` for the always-on token cost before any install.

7. **CloudFormation-centric advice versus Terraform.** Skills and the deploy skill default to CFN, CDK or SAM output, so an agent may emit CFN or SAM templates or suggest Beanstalk. Mitigation: skip deploy-on-aws and aws-serverless; use Knowledge for API facts and limits only, never to generate IaC; CLAUDE.md already fixes Terraform.

8. **Public-repo leakage.**
   - MCP outputs (ARNs and account IDs from run_script, pricing reports) can get pasted into docs or PRs in public repos.
   - Proxy telemetry is on by default, and queries go to AWS endpoints.
   - A project-scope install writes `enabledPlugins` into the public `.claude/settings.json`.
   - Mitigation: user or local scope only; `--disable-telemetry`; never commit raw MCP output; secret-scan CI stays the backstop.

9. **Supply chain.** awslabs servers run `uvx ...@latest` with admin credentials in the environment, and the official marketplace auto-updates plugins. Mitigation: pin exact versions in your own MCP config.

10. **Cost rule.** Knowledge, Pricing and the managed server are free. But run_script can call paid APIs (Cost Explorer at $0.01 per call, which K-14 already forbids for new scripts), and deploy flows create resources. That is one more reason to skip the API and deploy tools.

## C. Minimal adoption plan

1. **Decide: no plugin installs.** Configure individual servers only, so the profile, region, version and scope stay under our control.

2. **Add Knowledge MCP at user scope.**
   - Command: `claude mcp add --transport http aws-knowledge https://knowledge-mcp.global.api.aws --scope user`. Optionally add it to `.kiro/settings/mcp.json` too.
   - Check:
     - `/mcp` shows it connected.
     - MemAvailable is unchanged.
     - Tool names are `mcp__aws-knowledge__*`; allow-list them as read-only.
     - The subagent MCP hook doesn't block them.
     - Ask it 3 known AA lessons (WAF description charset, WAF unlink/delete order, `ListInstanceProfilesForRole` on role delete) and compare with lessons.md. Keep it only if the answers are right and sourced.

3. **Trial Pricing MCP for 1-2 sessions, local scope.**
   - Config: version pinned; env `AWS_PROFILE=aa365-admin`, `AWS_REGION=us-east-1`. I believe the Pricing API endpoints are us-east-1, eu-central-1 and ap-south-1, but that is from memory; the reports leave it UNCONFIRMED.
   - Check:
     - It starts under MFA. If not, stop here, or propose a `pricing:*`-only role as a reviewed IAM PR.
     - RSS of the process.
     - Price quotes for known resources (RDS db.t4g.small in us-west-1, Fargate ARM, NAT) match the measured costs in the existing CE-backed reports.
     - `analyze_terraform_project` on `infra/AA-CIS-Infra/envs/dev` lists the right services.
     - Every figure is labelled "estimated".

4. **Review after 2 weeks.** Keep or remove. Record the outcome in lessons.md and in the CLAUDE.md MCP section.

5. **AWS API MCP: not now.** Preconditions before any trial:
   - a read-only role;
   - an IAM Deny on writes with `aws:ViaAWSMCPService`;
   - proxy `--read-only --profile <ro> --region us-west-1 --disable-telemetry`;
   - a subagent deny plus a main-session PreToolUse hook (B1);
   - the `call_aws` versus `run_script` question settled with a live `tools/list`.

6. **Separate track (not plugins).** Propose tflint plus checkov or trivy in the Infra CI for the wildcard-IAM theme, and research HashiCorp terraform-mcp-server for registry docs.

## D. Claims in the original post that are wrong or unverified

- **"aws-core" from the awslabs repo is wrong.** aws-core lives in aws/agent-toolkit-for-aws, not awslabs/agent-plugins, so `aws-core@agent-plugins-for-aws` would fail. Method 1 (`@claude-plugins-official`) works. The post also doesn't mention that awslabs/agent-plugins is now marked superseded by the Agent Toolkit, with commits slowed to 1-2 a month.
- **"Templates are run through cfn-lint and cfn-guard before being handed over" is wrong as an automatic step.**
  - No plugin has a cfn-lint or cfn-guard hook. They run only if the agent chooses to call the awsiac tools.
  - The only template hook is aws-serverless running `sam validate --lint` on `*template.yaml`, and it silently skips when the SAM CLI or jq is missing (both missing on this machine).
  - The deploy-on-aws hook only validates draw.io XML.
- **"Least privilege and Well-Architected by default" is unverified.** It is skill prose only; nothing enforces it or lints IAM.
- **"One install command, no MCP configuration" is true but hides the risk.**
  - aws-core passes no profile, region or read-only flag.
  - aws-serverless turns on `--allow-write`.
  - The awslabs servers run `@latest`.
  - The region defaults to us-east-1.
- **"Pricing questions go to the Pricing API" is only partly true.** Only deploy-on-aws bundles the Pricing MCP; aws-core does not. The server needs AWS credentials, and its README disclaims correct filters and cheapest-option detection.
- **"Knows newly launched features" is plausible.** Knowledge MCP indexes What's New posts and blogs. Freshness was not measured.
- **"Reads stack events to find the cause" is true for CloudFormation only.** It uses awsiac `troubleshoot_cloudformation_deployment`.
- **databases-on-aws is not general databases.** It covers only Aurora DSQL.
- **"Also works on Cursor, Codex and Kiro" is partly confirmed.** Cursor >= 2.5 is confirmed. Codex and Kiro are UNCONFIRMED in the plugin report, and the audit's "plugins also run on Kiro" is unsourced.
- **Claude Code >= 2.1.29 is confirmed for awslabs.** No minimum is stated for the toolkit's aws-core.
- **The post's "for personal projects I always give it prod" reads as a typo or contradiction.** For AA, the MCP must never be allowed near prod, and not near acc1 either.

## Conflicts and UNCONFIRMED items between the reports

- **`call_aws` existence:** the aws-core README and the GA blog list it; the current official tool reference omits it (only `aws___run_script`). A third-party page says it was removed in September 2026. UNCONFIRMED.
- **Managed endpoint regions:** the GA blog lists 2 (us-east-1, eu-central-1); the setup guide lists 8, none of them us-west-1.
- **Proxy package names differ:** aws-core uses `mcp-proxy-for-aws-cli==1.7.0 --skip-auth`; amplify and sagemaker use `mcp-proxy-for-aws@latest` without `--skip-auth`. Installing several would mean two proxy variants.
- **Audit tool name versus actual server and tool names:** see B1.
- **UNCONFIRMED in both reports:**
  - MFA-assumed-role behaviour in a non-TTY MCP process;
  - RSS per MCP process;
  - Knowledge rate limits;
  - Pricing endpoint list;
  - disabling a single plugin hook or server;
  - HashiCorp terraform-mcp-server details.
- **Audit gaps:** the 3 `Action="*"` and 78 `"*"`-resource IAM hits were counted, not reviewed. `~/.aws/config` could not be read, so the profile facts come from CLAUDE.md, not a live check.
