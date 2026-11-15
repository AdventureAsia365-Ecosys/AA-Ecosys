RESEARCH REPORT: "Agent Plugins for AWS" and related AWS plugins (primary sources only; checked 2026-11-15 through the GitHub API, docs.aws.amazon.com and code.claude.com)

## 0. Main finding: the post mixes two different AWS repos
- **awslabs/agent-plugins** (https://github.com/awslabs/agent-plugins): created 2026-02-05, release 1.0.0 on 2026-02-18, Apache-2.0, about 940 stars, marketplace name `agent-plugins-for-aws`, marketplace version 1.1.0. Its plugins are amazon-location-service, aws-amplify, aws-serverless, aws-transform, codebase-documentor-for-aws, databases-on-aws, deploy-on-aws and sagemaker-ai. **It has no aws-core.** The README now carries a banner: "The Agent Toolkit for AWS ... is the successor to the MCP servers, plugins, and skills available on AWS Labs ... This repo continues to work and accept contributions. Over time, the most useful projects here will move into Agent Toolkit for AWS."
- **aws/agent-toolkit-for-aws** (https://github.com/aws/agent-toolkit-for-aws): created 2026-04-23, README badge says GA, about 3,500 stars. Plugins: **aws-core**, aws-agents, aws-data-analytics, aws-agents-for-devsecops, aws-startup-advisor. Launch news: https://aws.amazon.com/about-aws/whats-new/2026/05/agent-toolkit/
- **migration-to-aws** in claude-plugins-official comes from a third repo, **awslabs/startups** (`migrate/plugins/migration-to-aws`). It plans GCP-to-AWS migrations.
- The claude-plugins-official marketplace (https://github.com/anthropics/claude-plugins-official, `.claude-plugin/marketplace.json`) lists aws-core, aws-agents, aws-data-analytics, aws-agents-for-devsecops and aws-startup-advisor (from aws/agent-toolkit-for-aws), plus aws-serverless, deploy-on-aws, databases-on-aws, aws-amplify, sagemaker-ai, aws-transform and amazon-location-service (from awslabs/agent-plugins), plus migration-to-aws (from awslabs/startups). Each entry is pinned to a git SHA.

## 1. Per plugin

### aws-core v1.2.0 (aws/agent-toolkit-for-aws/plugins/aws-core)
- **Skills (27 folders):** amazon-bedrock, aws-ai-ml, aws-auth, aws-billing-and-cost-management, aws-blocks, aws-cdk, aws-cloudformation, aws-compute, aws-containers, aws-database, aws-deployment, aws-emulator, aws-iam, aws-investigation, aws-messaging-and-streaming, aws-networking, aws-observability, aws-sdk-js-v3-usage, aws-sdk-python-usage, aws-sdk-swift-usage, aws-secrets-manager, aws-security, aws-serverless, aws-storage, aws-well-architected-review, launch-with-aws, signing-in-to-aws.
- **MCP server (exactly one), `aws-mcp`:** a local stdio proxy started with `uvx mcp-proxy-for-aws-cli==1.7.0 https://aws-mcp.us-east-1.api.aws/mcp --skip-auth --metadata INSTALL_SOURCE=agent-toolkit-core`. It forwards to the managed remote AWS MCP Server in us-east-1. The config passes **no --profile, --region or --read-only**.
- **Hooks (`com.anthropic.claude-code/hooks/hooks.json`):** PreToolUse on `Bash` and on `use_aws|mcp__aws.*|mcp__plugin_.*aws-mcp.*` runs `secret-safety.py` (5 s timeout). It **denies** the following: `aws ... secretsmanager (batch-)get-secret-value`, SDK `get_secret_value(` / `GetSecretValueCommand(` inside inline `python -c` / `node -e`, and calls to the localhost:2773 Secrets Manager agent. Its message points to `{{resolve:secretsmanager:...}}` with asm-exec. Commands that start with grep, cat, git, gh and similar are exempt.
  - Impact for AA: the AA repo uses `get-secret-value` in runbooks, `.github/workflows/plan-sync.yml` and `.claude/settings*.json`. With aws-core enabled, Claude Code would block any Bash command that runs it.
- **Remote server tools** (current official reference, https://docs.aws.amazon.com/agent-toolkit/latest/userguide/understanding-mcp-server-tools.html):
  - Knowledge: `aws___retrieve_skill`, `aws___search_documentation`, `aws___read_documentation`, `aws___list_regions`, `aws___get_regional_availability`.
  - API: `aws___run_script`, `aws___get_presigned_url`, `aws___get_tasks`.
  - There is also a "serverless capability": read-only Lambda diagnosis with `diagnose`, `search_logs`, `get_live_config`, `get_recent_changes`, `get_trace_summary` (https://docs.aws.amazon.com/agent-toolkit/latest/userguide/capabilities.html).
- The aws-core README still advertises `call_aws`. See section 3 for why that looks out of date.

### deploy-on-aws v1.4.0 (awslabs)
- **Skills:** deploy, aws-architecture-diagram, elastic-beanstalk.
- **MCP servers:**
  - `awsiac`: local, `uvx awslabs.aws-iac-mcp-server@latest`.
  - `awsknowledge`: remote HTTP, https://knowledge-mcp.global.api.aws.
  - `awspricing`: local, `uvx awslabs.aws-pricing-mcp-server@latest`, timeout 120 s.
- **Hook:** PostToolUse on `Edit|Write` runs `scripts/validate-drawio.sh` (30 s). It only acts on `.drawio` / `.drawio.xml` files: it validates the XML (needs python3 + defusedxml) and returns a draw.io preview URL.
  - **There is no cfn-lint or cfn-guard hook.** cfn-lint and cfn-guard run only when the agent calls the awsiac MCP tools.
- The deploy skill says: always show the cost estimate before writing IaC; default to dev-sized resources; "Run IaC security scans (cfn-nag, checkov) before deployment"; deploy "with user confirmation"; never recommend App Runner.
- **aws-iac-mcp-server tools** (https://github.com/awslabs/mcp/tree/main/src/aws-iac-mcp-server):
  - read_iac_documentation_page
  - validate_cloudformation_template (cfn-lint)
  - check_cloudformation_template_compliance (cfn-guard, with the bundled rules plus the Guard Rules Registry and Control Tower proactive controls)
  - troubleshoot_cloudformation_deployment (needs cloudformation:DescribeStacks / DescribeStackEvents / DescribeStackResources and cloudtrail:LookupEvents)
  - search_cloudformation_documentation
  - get_cloudformation_pre_deploy_validation_instructions
  - search_cdk_documentation
  - search_cdk_samples_and_constructs
  - cdk_best_practices
  - Validation and compliance run locally and need no AWS permissions.

### aws-serverless v1.3.0 (awslabs)
- **Skills:** aws-lambda, aws-serverless-deployment, aws-lambda-durable-functions, aws-lambda-managed-instances, aws-lambda-microvms, api-gateway, aws-step-functions.
- **MCP server:** `aws-serverless-mcp`, local, `uvx awslabs.aws-serverless-mcp-server@latest --allow-write`.
  - The server defaults to read-only, but **the plugin turns on write mode** with `--allow-write`.
  - Tools: sam_init, sam_build, sam_deploy, sam_logs, sam_local_invoke, get_iac_guidance, get_lambda_event_schemas, get_lambda_guidance, deploy_webapp, configure_domain, webapp_deployment_help, get_metrics, update_webapp_frontend, deploy_serverless_app_help, get_serverless_templates, plus ESM/schema tools.
  - It uses the default AWS profile unless AWS_PROFILE is set; region defaults to us-east-1.
- **Hook:** PostToolUse on `Edit|Write` runs `scripts/validate-template.sh` (120 s). It only acts on files named `*template.yaml` / `*template.yml` and runs `sam validate --lint`. It is skipped quietly when jq or the SAM CLI is missing (neither `sam` nor `cfn-lint` is installed on this machine).

### databases-on-aws v1.10.0 (awslabs)
- **Skill:** only `dsql` (Aurora DSQL). Nothing for RDS PostgreSQL. aws-core's `aws-database` skill covers RDS and Aurora.
- **MCP servers:**
  - `awsknowledge`: remote, enabled.
  - `aurora-dsql`: `uvx awslabs.aurora-dsql-mcp-server@latest`, `"disabled": true`.
  - `cloudwatch`: `uvx awslabs.cloudwatch-mcp-server@latest`, `"disabled": true`, with placeholder AWS_REGION / AWS_PROFILE.
- **Hook:** PostToolUse on `mcp__aurora-dsql.*__transact`, a prompt-type hook asking the agent to verify the schema or row counts.
- It also ships scripts: create, delete and list DSQL clusters, and psql-connect.

### Others (brief)
- aws-amplify 1.0.0 and sagemaker-ai 1.3.0 both use `aws-mcp` through `uvx mcp-proxy-for-aws@latest https://aws-mcp.us-east-1.api.aws/mcp`. They use a different package name from aws-core, and pass no `--skip-auth`.
- codebase-documentor-for-aws uses awsknowledge + awsiac.
- aws-startup-advisor (toolkit) has the same aws-mcp proxy plus a `tf-best-practices` skill.

Sources: the plugin folders under https://github.com/awslabs/agent-plugins/tree/main/plugins (README tables at lines ~178-316) and https://github.com/aws/agent-toolkit-for-aws/tree/main/plugins/aws-core.

## 2. Terraform support
- **No plugin wraps a Terraform MCP server, tflint or a Terraform validation hook.**
- **awslabs terraform-mcp-server is gone.** awslabs/mcp PR #3165 (2026-04-17) removed it together with 11 other deprecated servers. Its replacement table says "terraform-mcp-server → HashiCorp official". cdk-mcp-server and cfn-mcp-server were also removed and replaced by aws-iac-mcp-server, which has **no Terraform tools** (CloudFormation and CDK only).
- **What touches Terraform:**
  - The pricing MCP has an `analyze_terraform_project` tool, which scans .tf files to find AWS services for cost estimation.
  - The deploy skill says to use awsiac when writing "CDK/CloudFormation/Terraform" and to run "cfn-nag, checkov". These are text instructions only; nothing is installed or hooked.
  - aws-serverless `get_iac_guidance` accepts Terraform as an option.
  - aws-startup-advisor's `tf-best-practices` skill is a read-only policy gate with a `terraform fmt → init → validate → policy` protocol and a `validate-terraform-policy.py` script. It is built for Terraform that migration skills generate.
- HashiCorp's own terraform-mcp-server is separate and outside every AWS plugin. I did not inspect its details (UNCONFIRMED).

## 3. The AWS API tool (call_aws / run_script)
- **Managed AWS MCP Server (current):**
  - The official tool reference lists no `call_aws`. The only general API tool is **`aws___run_script`**: Python in a server-side sandbox. Per the GA blog of 2026-05-06, "The sandbox inherits your IAM permissions but has no network access", and it has no local filesystem or shell. Long tasks are polled with `get_tasks`.
  - The GA blog (https://aws.amazon.com/blogs/aws/the-aws-mcp-server-is-now-generally-available) and the aws-core README both still describe `call_aws` ("any of the 15,000+ AWS API operations").
  - I found one third-party page (Glama) saying call_aws was removed around September 2026. I could not confirm this against a live `tools/list`, so whether call_aws still exists is **UNCONFIRMED (sources conflict)**. The current official docs omit it.
- **Authorization:**
  - No MCP-specific IAM actions any more. The preview actions `aws-mcp:InvokeMcp`, `CallReadOnlyTool` and `CallReadWriteTool` are deprecated "and have no effect".
  - Requests are SigV4-signed with your credentials and authorized by the downstream service under your own IAM policies.
  - The server adds the global condition keys `aws:ViaAWSMCPService` (bool) and `aws:CalledViaAWSMCP` (for example `aws-mcp.amazonaws.com`), so IAM policies or SCPs can deny or limit agent-initiated calls. CloudTrail logs the calls, and CloudWatch metrics go to the `AWS-MCP` namespace.
  - Source: https://docs.aws.amazon.com/agent-toolkit/latest/userguide/security_iam_service-with-iam.html
- **Read-only mode:** the proxy has a `--read-only` flag that "Disable[s] tools which may require write permissions" (tools annotated readOnlyHint stay). It works only with SigV4, not OAuth. **aws-core does not set it.**
- **Consent:** the managed server has no server-side consent or allowlist. Control comes from IAM or SCPs plus Claude Code's own tool-permission prompts.
- **Allowlist:** none on the managed server. The older local awslabs `aws-api-mcp-server` did have controls: `READ_OPERATIONS_ONLY`, `REQUIRE_MUTATION_CONSENT` (MCP elicitation), and `~/.aws/aws-api-mcp/mcp-security-policy.json` with `denyList` / `elicitList`, exact-match only. That server is now marked "superseded by the official AWS MCP server".
- **Credentials, profile and region (proxy README, https://github.com/aws/mcp-proxy-for-aws):**
  - Credentials come from the boto3 chain. `--profile` (several allowed; the first is the default, and the others become a per-call `aws_profile` parameter) falls back to `AWS_MCP_PROXY_PROFILES`, then `AWS_PROFILE`.
  - `--region` falls back to `AWS_REGION`. Without `AWS_REGION` metadata, operations default to us-east-1.
  - `--skip-auth` sends requests unsigned only when no credentials are found.
  - Telemetry is on by default (`--disable-telemetry` turns it off).
  - Default timeouts: 180 s overall, 300 s per tool call.
  - Because aws-core passes no profile, it uses `AWS_PROFILE` or `default`, which on this machine is acc2 through an assumed role with MFA.
  - Whether the proxy can use an MFA-assumed-role profile from a non-TTY stdio process (boto3 does not reuse the AWS CLI's STS cache by default) is **UNCONFIRMED (my inference)**.
- **Supported regions** for the managed endpoint (setup guide): us-east-1, us-west-2, ap-southeast-1, ap-southeast-2, ap-northeast-1, eu-central-1, eu-west-1, eu-west-2. No us-west-1 endpoint, but the server can call any Region.
- **OAuth option:** `claude mcp add aws-mcp https://aws-mcp.us-east-1.api.aws/mcp --transport http`, with the `AWSMCPSignInOAuthAccessPolicy` managed policy. Single role only, no read-only flag. Source: https://docs.aws.amazon.com/agent-toolkit/latest/userguide/getting-started-aws-mcp-server.html

## 4. Pricing MCP (awslabs.aws-pricing-mcp-server)
- It reads the AWS Price List (Pricing) API. Tools: get_pricing, get_pricing_service_codes, get_pricing_service_attributes, get_pricing_attribute_values, get_price_list_urls, generate_cost_report, get_bedrock_patterns, analyze_cdk_project, analyze_terraform_project.
- README: "All calls are free of charge."
- It **needs AWS credentials** with `pricing:*`. Profile comes from AWS_PROFILE (default "default"). AWS_REGION "determines the geographically closest AWS Pricing API endpoint to use".
- The plugin config sets no profile or region, so it uses the default profile.
- Which Pricing API endpoints exist is not stated in the README (UNCONFIRMED here).
- The README also warns: "We cannot guarantee that AI assistants will always construct filters correctly or identify the absolute cheapest options."
- Source: https://github.com/awslabs/mcp/tree/main/src/aws-pricing-mcp-server

## 5. AWS Knowledge MCP
- Remote endpoint https://knowledge-mcp.global.api.aws, GA.
- "does not require authentication but is subject to rate limits." The actual rate-limit numbers are UNCONFIRMED (not published in the README). No AWS account is needed; usage falls under the AWS Site Terms. No charge is stated in the README; the Agent Toolkit docs say the toolkit is "no additional charge".
- Tools: search_documentation, read_documentation, list_regions, get_regional_availability, retrieve_skill.
- Sources: AWS docs, What's New posts, blogs, Well-Architected, CDK/CloudFormation, Amplify, Strands docs.
- The same knowledge tools are also built into the managed AWS MCP Server with no credentials needed.
- Source: https://github.com/awslabs/mcp/tree/main/src/aws-knowledge-mcp-server

## 6. Requirements and runtime
- **Claude Code:** awslabs README says ">=2.1.29" (installed here: 2.1.303). Cursor >= 2.5.
- **uv / uvx:** needed for every local server. Server READMEs say Python 3.10+ (`uv python install 3.10`). uv/uvx is already installed through mise.
- **AWS CLI:** 2.32.0+ is needed for the SigV4 setup with `aws login`.
- **Optional tools for hooks:** jq + SAM CLI (aws-serverless hook), python3 + defusedxml (draw.io hook).
- **Node:** no Node needed for these plugins.
- **How servers start:** stdio servers are spawned by `uvx` when a Claude Code session loads the plugin, one process per server per session. The very first run downloads packages ("might take a few minutes on the first connection").
- **Version pinning:** awslabs plugins use `@latest`, so whatever is newest runs. aws-core pins `mcp-proxy-for-aws-cli==1.7.0`.
- **Plugin hooks** register at session load and fire on every matching event, whether or not you use the plugin's skills.
- **RAM per process:** UNCONFIRMED (no primary source). deploy-on-aws alone starts 2 local Python processes (awsiac, awspricing); aws-core starts 1 (the proxy).

## 7. Install, scope, disabling
- **Install commands:**
  - Toolkit: `/plugin install aws-core@claude-plugins-official`. If you get "Plugin not found", run `/plugin marketplace update claude-plugins-official` first.
  - awslabs: `/plugin marketplace add awslabs/agent-plugins`, then `/plugin install deploy-on-aws@agent-plugins-for-aws`. The same plugins are also in claude-plugins-official.
  - Shell form: `claude plugin install <name>@<marketplace> --scope user|project|local`.
- **Scopes:**
  - user writes to `~/.claude/settings.json`.
  - project writes to `.claude/settings.json`. That turns the plugin on for collaborators, but each clone still has to install it once.
  - local writes to `.claude/settings.local.json`.
  - Precedence: local > project > user.
  - Source: https://code.claude.com/docs/en/discover-plugins
- **Disabling:**
  - Whole plugin: the `/plugin` Installed tab, or `claude plugin disable <name>`.
  - Plugin MCP tools are named `mcp__plugin_<plugin>_<server>__<tool>`, and the docs say to use that name in permission rules. So you can deny one server's tools with a permission rule such as `mcp__plugin_aws-core_aws-mcp__*`.
  - Toggling one plugin MCP server off in `/mcp` without disabling the plugin: UNCONFIRMED.
  - Turning off a single plugin hook while keeping the plugin: UNCONFIRMED (no per-hook switch is documented on the pages I read).
  - Servers marked `"disabled": true` in a plugin's `.mcp.json` (the DSQL and CloudWatch servers in databases-on-aws) ship turned off.
- **Auto-update:** claude-plugins-official auto-updates by default; awslabs/agent-plugins as a third-party marketplace does not. The plugin details pane shows context-cost token estimates for official-marketplace plugins, and `claude plugin details <name>` shows the always-on token count.

## 8. Dates, maturity, update cadence
- **AWS MCP Server:** GA blog dated 2026-05-06, updated in June. The blog lists only us-east-1 and eu-central-1; the current setup guide lists 8 regions. Preview IAM actions are deprecated.
- **Agent Toolkit for AWS:** launched May 2026, repo created 2026-04-23. Very active: about 40 commits in the 10 days before 2026-11-15. aws-core is at v1.2.0.
- **awslabs/agent-plugins:** created 2026-02-05, v1.0.0 released 2026-02-18. Commits slowed to roughly 1-2 a month in Oct–Nov 2026, last pushed 2026-11-14. It is positioned as the predecessor, with "the most useful projects here will move into Agent Toolkit for AWS". Plugin versions: deploy-on-aws 1.4.0, aws-serverless 1.3.0, databases-on-aws 1.10.0.
- **awslabs/mcp:** removed 12 deprecated servers in April 2026, Terraform among them.

## UNCONFIRMED items
- Whether `call_aws` is still live: official docs omit it, while the README and GA blog list it.
- Knowledge MCP rate-limit numbers.
- RAM per MCP process.
- Per-server and per-hook disable inside an enabled plugin.
- Whether the MCP proxy can use an MFA-assumed-role profile from a non-interactive process.
- Which Pricing API endpoints exist.
- Details of HashiCorp's terraform-mcp-server.

No files were written. Scratch copy of the aws-api-mcp-server README: /tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/5ee4a1c3-a4ae-414b-8474-cd33e419cebe/scratchpad/api.md