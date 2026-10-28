# ADR 0012 — Environment model: Dev and prod on the infrastructure account, isolated per environment

- **Status:** Proposed (2026-10-28, S256). Drafted ahead of the prod blueprint so that CRM Go-real (AA-980) and the
  other prod-bound work can plan against it. Nothing in it is built; decisions 1–12 take effect when the tech lead
  accepts this ADR, and the build (phase 3) starts only when a go-live date is set (D-16).
- **Reserving issue:** AA-880 (number 0012 was reserved for it in the ADR index, AA-928).
- **Scope:** AA-CIS-Infra (Terraform layout, state, GitHub environments, OIDC roles, DB Migrate `environment`
  input), every app repo (Deploy Prod workflow, environment-scoped configuration, Vercel prod projects), root (data
  standards C7.2c and C7.2d, engineering handbook §6.1, the DevOps guide, the ops README prod section).
- **Implements:** ADR 0001 (amendment S235: "Production also runs on acc2 … no new AWS account is created for any
  environment"); engineering handbook decisions D-16 (prod layout and gate chosen with the go-live date) and D-17 (prod
  on acc2 by default); data standards DM-9.6 (prod targets) and C7.2a–f (prod blueprint).
- **Amends on acceptance:** data standards C7.2c (the Terraform layout: `infra/AA-CIS-Infra/envs/prod/` becomes the
  root named in decision 5) and C7.2d (the prod gate of decision 8). Infra `CONTEXT.md` (AA-841: "a new environment
  gets its own `accounts/<name>/` root") is kept, not changed.
- **Consistent with:** ADR 0001a (two AWS accounts: acc2 for all infrastructure, acc3 the only LLM account; the
  personal account left the ecosystem in AA-998), ADR 0004b (one security group per caller), ADR 0006 / 0006a /
  0006b (Cognito pools), ADR 0011 (merge rights per risk tier; the human gate from the first prod), ADR 0014
  decision 4 (the prod-trigger choice of GitHub plan for the private repos), ADR 0017 (expand migrations auto-applied
  on Dev only).
- **Related Linear:** AA-880 (this ADR and the L9 prod blueprint), AA-864 (research: consolidate on one AWS account),
  AA-980 (CRM Go-real; prod placement of the CRM after this ADR), AA-873 (90-day security), U-53 (least-privilege
  agent role before prod).
- **Design sources:** the S241 SDLC review (`docs/audits/2026-10-17-S241-sdlc-review/README.md` §5.2 environments and
  promotion, P0-12 third-party administration, P2-1, P2-14; `unified-roadmap.md` U-40, D-16, D-17; area file
  `areas/environments-secrets-iam.md`), the data standards C7 and DM-9.6, the engineering handbook §6.1 and §10.

## Context

**Today there is one environment.** Everything runs as Dev on acc2 in us-west-1 (account IDs in the
[account map](../onboarding.md#account-map)): the ECS cluster `aa-cis-dev-cluster` with the CIS, Booking and Partner
services, the RDS instance `aa-cis-dev-db` shared by four app schemas, the TripPlanner Lambdas, Cognito, API Gateway,
CloudFront and S3. Frontends run on Vercel (Hobby plan): the project "production" deployments of `aa-cis-frontend`,
`aa-booking-admin` and `aa-tripplanner` all call the Dev backends, and per-PR previews call Dev as well. acc3 hosts
only the Bedrock invoker role for chat models. Dev holds test data only (D-01, C7.1a).

**Several things already point at a prod that does not exist:**

- ADR 0001 (S235) and D-17 place prod on acc2, with no new account; C7.2a requires a separate RDS instance there.
- The AA-CIS-Infra GitHub environment that applies Dev is named `prod`, and the OIDC subject `environment:prod` is
  what the Dev apply role trusts (`accounts/aa365/cicd_split.tf`). DB Migrate, the schema dump and the probes run in
  it. Renaming it was deferred to this ADR (D-16, C7.2d, handbook §5.5).
- C7.2c puts the prod root at `infra/AA-CIS-Infra/envs/prod/`, but AA-841 removed the empty `envs/` scaffold and Infra
  `CONTEXT.md` says a new environment gets its own `accounts/<name>/` root. The S241 review proposed a third layout,
  a parameterised `stacks/platform`. The three do not agree, and the review left no safe default (D-16).
- The single Terraform root `accounts/aa365` mixes account-wide resources (GitHub OIDC provider, CloudTrail,
  GuardDuty, Access Analyzer, budgets, the public Route 53 zone `lumiguides.it.com`) with environment resources
  (VPC, RDS, ECS, ALB, API Gateway, Cognito pools, secrets, KMS keys). Most names already carry `<env>`
  (`aa-crm-<env>-*`, `crm/<env>/...`, `<env>.internal`), but the S241 review counted dozens of `dev` literals, mostly
  in the CI roles and their permission boundary (`aa-*-dev-*`).
- acc2 is a member account of the payer vendor's AWS Organization (TrueIDC). Principals of that management account
  are outside our IAM: an `OrganizationAccountAccessRole`-style role, if present, bypasses every control below
  (S241 P0-12). Nobody has checked yet which roles in acc2 trust it.
- The agent works with the `aa365-admin` profile (D-15). On a shared account, that profile reaches anything a prod
  would hold, unless something stops it.
- AA-864 (research, not decided) asks whether all of acc2 should move to one account under AA's own control.

**What must be decided now**, so that prod-bound work (CRM Go-real, customer sign-in, payments) is designed against
a known target: which environments exist, where prod lives, how it is isolated from Dev on the same account, how
Terraform and CI are laid out, how a release moves from Dev to prod, what data may cross, and what starts the build.

## Options considered

### Where prod lives

| Option | For | Against | Verdict |
|---|---|---|---|
| **A. A separate prod AWS account** (new member account, or an AA-owned Organization) | The AWS-recommended boundary (Well-Architected SEC01): IAM, service quotas, SES reputation, KMS, CloudTrail and blast radius are all separate by construction; an audit question "is prod separated?" has a one-word answer | Reverses ADR 0001 (S235) and D-17. A new account under the payer vendor needs the vendor and inherits its management-account access and SCPs (Bedrock LLMs are blocked on its accounts today, ADR 0001a); an AA-owned Organization is a billing and contract change for the business owner. Doubles the account-level work (OIDC provider, CloudTrail, GuardDuty, Config, Security Hub, budgets, quotas, SES production access) and makes image promotion and DNS cross-account. One engineer runs everything | **Not now.** Kept as the documented upgrade path; revisit on the triggers in decision 12 |
| **B. Same account (acc2), strong isolation per environment** | Keeps ADR 0001 and D-17; one set of account-level services; the same modules build both environments; image promotion and DNS stay inside one account; cheapest to run | Isolation is built from IAM, tags, KMS key policies, network and state, so it is only as good as that configuration; account-level limits (service quotas, SES sending reputation, Bedrock quotas on acc2) are shared; the payer's management account reaches both | **Chosen**, with the compensating controls of decisions 3 and 4 (the S241 review §5.2 list) |
| C. Same account, shared infrastructure (prod schemas in the Dev RDS, prod services in the Dev cluster) | Lowest cost | A Dev experiment, migration, wave or restore reaches real users' data; contradicts C7.2a and C7.1a | Rejected |
| D. Consolidate on one AA-controlled account first (AA-864), then build prod there | Fixes the payer and Bedrock split at the same time | AA-864 is research only and not wanted yet ("Still wanted?" in the master plan); it must not block prod | Not a precondition. This ADR names no account in its rules ("the infrastructure account"), so if AA-864 later moves acc2, the model moves with it unchanged |

### Terraform layout (D-16)

| Option | Verdict |
|---|---|
| `envs/prod/` (C7.2c as written) | Rejected: AA-841 removed `envs/` on purpose; reviving it contradicts Infra `CONTEXT.md` |
| One parameterised `stacks/platform` applied with a different backend and variables per environment | Rejected as the only mechanism: a root that switches environment by variables makes "apply the Dev plan to prod" one wrong flag away |
| **One root per account and environment under `accounts/<name>/`, both composing the same environment module** | **Chosen** (decision 5): matches Infra `CONTEXT.md`, keeps one code path for both environments, and gives prod its own state, backend and CI role |

## Decision

### 1. Environments

| Environment | Where | Data | Purpose |
|---|---|---|---|
| Local | Engineer machine, local Postgres | Fixtures | Develop, unit and integration tests |
| PR preview | Vercel preview deployments | Calls **Dev** | UI review before merge |
| **Dev** | acc2, us-west-1 | Test or synthetic data only (C7.1a, D-01) | Integration, allowed to break, demo, paid pipeline runs on subsets; acts as **pre-prod** once prod exists |
| **Prod** | acc2, us-west-1 | Real users and real personal data | Customers, agencies, staff doing real work |

There is no staging environment (handbook §6.1 and §9.3 keep it out). Every environment name used in code,
Terraform, tags, secrets and workflows is one of `dev` and `prod`.

### 2. Prod stays on the infrastructure account (acc2)

Prod is built on acc2, next to Dev, in us-west-1, as ADR 0001 (S235) and D-17 decided. Bedrock chat models for prod
go through acc3 like Dev (ADR 0001a). A separate prod account is not created now; decision 12 says when that is
reconsidered.

### 3. Isolation inside the account

Prod shares **no environment resource** with Dev. Each item below is a separate resource per environment, named
`aa-<app>-<env>-<resource>` (or the existing `<app>/<env>/...` pattern for secrets):

| Layer | Prod has its own |
|---|---|
| Network | VPC (non-overlapping CIDR), subnets in two AZs, one NAT gateway per AZ, internal ALB, VPC endpoints; **no peering, no Transit Gateway, no shared security group** with Dev; security groups per caller (ADR 0004b) |
| Data | RDS instance (C7.2a/b, DM-9.6), parameter group, private zone `prod.internal` with `db.prod.internal` (C7.2f), S3 buckets, Redis if used |
| Compute | ECS cluster `aa-cis-prod-cluster` and services, Lambda functions, ECR repositories (IMMUTABLE), log groups |
| Edge | API Gateway APIs, CloudFront distributions, WAF web ACLs, ACM certificates and custom domains |
| Identity | Cognito pools (WORKFORCE, PARTNER, EXTERNAL, M2M) with prod clients and a prod managed-login domain; staff and agency people enrol again in prod |
| Secrets and keys | Secrets under `<app>/prod/...`, customer-managed KMS keys per purpose whose key policies name only prod roles |
| CI and runtime roles | GitHub OIDC roles per repo and environment, ECS task and execution roles, the migrator role (`db_migrator` in prod) |
| LLM path | A separate acc3 invoker role for prod with its own ExternalId, trusted only by prod task roles, so prod can be cut or throttled apart from Dev |
| Observability | Alarms with prod thresholds and a paging route (C7.2c, C4.1), a second alert channel, Sentry DSNs per environment, an `Environment=prod` budget |

Every resource carries the `Environment` tag (`dev` / `prod`) next to `App`, `Project` and `ManagedBy` (DM-10.1).

### 4. Compensating controls for sharing an account

Because prod and Dev share acc2, these controls are part of the blueprint, not extras:

1. **Tag-based deny.** Every non-prod principal (Dev CI roles, Dev task roles, the agent role) carries an explicit
   Deny on resources tagged `Environment=prod`, on `*/prod/*` secrets and on the prod state bucket. Explicit Deny
   wins over any Allow, so an Allow added later by mistake does not open prod.
2. **Permission boundary on every role CI creates.** The existing CI boundary keyed on `aa-*-dev-*` becomes one
   boundary per environment, so a Dev pipeline cannot create a role that escapes it.
3. **KMS key policies.** Prod keys (RDS, S3, secrets, CloudTrail where per environment, CRM data keys) list only prod
   roles and the MFA break-glass admin. An IAM Allow alone cannot decrypt prod data.
4. **No agent access to prod.** Before phase 3 starts, the agent moves from `aa365-admin` to a Dev-scoped role
   (U-53, D-15 trigger; the narrow role `aa-cis-dev-agent-session` of AA-730 is the starting point) with no IAM write
   on itself or on boundaries. The agent's GitHub App cannot dispatch prod
   workflows (decision 8). ECS exec is off on prod services; turning it on is a break-glass Terraform change by a
   human, with session logging.
5. **Management-account review.** Before phase 3, the tech lead checks (read-only) which roles in acc2 trust the payer
   vendor's management account, asks the vendor for its access policy and SCPs in writing, and records the vendor as
   a privileged sub-processor (S241 P0-12). If the answer is not acceptable for real customer data, that is a
   decision-12 trigger.
6. **Detection.** CloudTrail alerts on any write to an `Environment=prod` resource by a principal outside the prod
   roles and the break-glass role; Security Hub (FSBP) and AWS Config cover the account (both environments).
7. **Shared limits made explicit.** Account and region quotas (Lambda concurrency, Fargate, SES sending, Bedrock
   embedding quotas on acc2, Bedrock chat quotas on acc3) are shared. Prod gets reserved Lambda concurrency where a
   Lambda serves users; Dev sends e-mail only to test and allow-listed recipients, through its own configuration set,
   so Dev cannot damage the prod sending reputation; a Dev paid wave yields to prod when an acc3 quota is near its
   limit.

### 5. Terraform layout

- **`accounts/aa365`** stays the root that applies today. It keeps the **account-wide layer** (GitHub OIDC provider,
  CloudTrail, GuardDuty, Access Analyzer, Security Hub and Config, account budgets, the public Route 53 zone, removal
  of the default VPC) **and Dev**. Its state stays at the current backend key. Moving Dev into its own root is
  optional later clean-up, not part of this ADR.
- **The environment-scoped resources become one module** (working name `modules/platform-env`), called by
  `accounts/aa365` with `environment = "dev"`. The refactor uses `moved` blocks inside the same state; its gate is a
  plan with **zero changes** on Dev. Hard-coded `dev` literals in CI roles, the boundary and names are replaced by
  the environment variable in the same refactor.
- **`accounts/aa365-prod`** is a new root that calls the same module with `environment = "prod"`, reads account-wide
  values with data sources (not remote state of the Dev root), and keeps its state in **its own bucket**
  (`aa-cis-tfstate-prod-<account id>`, versioned, KMS, native lockfile). Only the prod apply role and the break-glass
  admin may write it; the Dev apply role and the agent role are denied.
- C7.2c is amended on acceptance to name `accounts/aa365-prod/` instead of `envs/prod/`.

### 6. GitHub environments and the rename of `prod`

The AA-CIS-Infra environment that applies Dev is renamed **before** any prod role exists, in this order, so the
subject `environment:prod` is never trusted by two roles:

1. create the GitHub environment `dev` and add `environment:dev` to the Dev apply role's trust (both subjects
   trusted for one PR);
2. switch Terraform Apply, DB Migrate, DB Schema Dump and the probes to `environment: dev`, rename the
   "Terraform Apply Prod" workflow to "Terraform Apply Dev", and run each once green;
3. remove `environment:prod` from the Dev role's trust and delete the old secrets of the `prod` environment;
4. only then create the prod apply role, trusting only `environment:prod` **and** `ref:refs/heads/main` of
   AA-CIS-Infra, and recreate the `prod` environment for it.

App repos get a `prod` environment for their Deploy Prod workflow, with the same trust pattern for their prod
deploy roles.

### 7. Release flow: build once, promote the same artifact

- **Dev is unchanged:** merge to `main` deploys Dev (image tagged with the git SHA, IMMUTABLE ECR); expand
  migrations are auto-applied on Dev (ADR 0017).
- **Prod is a promotion, not a rebuild, for backends.** A Deploy Prod workflow (manual dispatch) takes a git SHA that
  is running and verified on Dev, copies the image **by digest** from the Dev ECR repository to the prod repository
  (the prod deploy role reads Dev ECR; nothing in Dev can write to prod), runs DB Migrate with `environment = prod`
  for the migrations that SHA requires, deploys the prod task definitions, and runs the same smoke checks against
  the prod endpoints. Release tags (`vX.Y.Z`, release-please, U-47) name what was promoted when they exist.
- **Frontends are rebuilt per environment** because Next.js bakes public configuration at build time: the same
  commit is built in a separate Vercel **prod project** per app (`<project>-prod`), with prod variables and the prod
  domain. Previews and the current projects keep calling Dev. Vercel Pro is required for prod (commercial use, D-18).
- **Prod migrations are never auto-applied.** Contract and destructive migrations keep MIG-4 and the idle-job rule
  (DM-11.4) per environment; the job-table guard runs against the prod job tables.
- **Rollback** is the previous task definition revision (and the previous Vercel prod deployment); migrations stay
  expand-first so the previous revision still runs.

### 8. The prod gate

- Terraform apply on `accounts/aa365-prod`, DB Migrate `environment = prod` and every Deploy Prod run start only from a
  manual dispatch on `main`, by the tech lead. Each job checks `github.actor` against an allow-list and refuses
  otherwise; the IAM trust of decision 6 is the hard fence behind it.
- Where GitHub can enforce environment reviewers (public app repos, or a paid plan), the `prod` environment also gets
  the tech lead as required reviewer. For the private repos (root and Infra after they go private again), the plan
  choice is ADR 0014 decision 4 (default B, compensating controls, while the tech lead is the only engineer).
- From the first prod, merge rights follow the human-gate tier of ADR 0011 and DM-11.5: the tech lead approves
  Terraform/IAM, migration, auth and data-deletion PRs before merge.
- C7.2d is amended on acceptance: DB Migrate takes `environment ∈ {dev, prod}`; the prod choice runs in the GitHub
  environment `prod` behind the actor check and the prod-only IAM trust.

### 9. Data between environments

- **Personal data never leaves prod** (C7.1a). No prod dump, snapshot or restore is opened in Dev; restore drills
  of prod run inside prod (a temporary instance in the prod VPC, deleted after the drill).
- **Initial content seed (once, at go-live):** the CIS content catalog on Dev (tours, places, published content,
  atoms; no personal data) is copied into prod by a reviewed, idempotent seed job whose table allow-list is checked
  against the PII tags (`COMMENT 'pii:<class>'`). Tenant, staff, traveller, Booking customer and CRM rows are not
  seeded; prod starts with an empty set of those.
- **After go-live, prod is the content system of record** for real tenants: editorial work and paid pipeline runs for
  the live catalog happen in prod. Dev keeps a subset for testing. A refresh of non-personal content tables from prod
  to Dev is allowed only through the same allow-listed job, never as a whole-database copy.

### 10. Prod targets confirmed

DM-9.6 and C7.2a–f are confirmed as the prod blueprint: Multi-AZ instance starting at `db.t4g.medium` with gp3 and
storage autoscaling; 14-day PITR, final snapshot on, deletion protection on; AWS Backup daily with a **cross-region
copy to us-west-2**; RPO ≤ 15 min (instance loss) and ≤ 24 h (region loss); RTO ≤ 1 h (AZ or instance) and ≤ 4 h
(region); quarterly restore drill with a recorded RTO; split runtime roles from day one with the master as break-glass
only (C7.2e); Enhanced Monitoring (60 s) and pgaudit (D-08); DSNs on the private CNAME (C7.2f); the GitHub token and
the RDS master password rotated at go-live (D-02, D-03).

### 11. What starts the build, and the go-live gate

**Trigger (phase 3 starts):** the business owner sets a go-live date (D-16). Any of these forces the question to be
asked, because each needs prod first:

- the first real personal data that would otherwise land on Dev (a real traveller sign-up, a real Booking customer,
  a real agency in the CRM: AA-980 CRM Go-real);
- the first paying tenant (also the D-13 human merge gate and D-18 Vercel Pro);
- turning on real payments.

The build needs lead time: about three to four weeks of focused work before the date (refactor, prod root, review,
cost approval, seed, drill). A date closer than that moves the date or narrows the first prod to the apps it needs.

**Go-live gate (prod opens to users only when all hold):**

1. this ADR Accepted; the prod Terraform plan reviewed with **one reconciled monthly cost** approved before apply
   (D-19);
2. decisions 4.4 and 4.5 done (agent role switched; management-account review recorded);
3. ADR 0014 decision 4 re-decided for the private repos;
4. a restore drill on prod passed with its RTO recorded (DM-9.3);
5. alarms with the paging route and the second alert channel tested; two SLOs per public API defined;
6. secrets rotated (D-02, D-03); the break-glass PDF copy of the core runbooks in place;
7. every control the [security baseline](../security/baseline.md) marks "before prod" closed (AA-873 and the
   others listed there);
8. the seed job run and its counts checked against Dev.

### 12. When to reconsider a separate prod account

Option A is reopened, with a new ADR, when any of these happens: a customer or auditor requires account-level
separation (for example a SOC 2 or enterprise questionnaire); card data enters our scope (PCI DSS beyond a hosted
payment page); a second person gets admin access to acc2; the management-account review of decision 4.5 is not
acceptable; or AA-864 decides to consolidate on an AA-controlled account, in which case prod is built there instead.

## Consequences

- **Good:** one known target for every prod-bound design (CRM Go-real places the CRM inside the prod environment
  boundary; ADR 0010's "prod cell or shared prod RDS" choice stays with AA-980 but both options sit in the prod VPC).
  Dev and prod are built by the same module, so they do not drift. The `prod` name stops meaning Dev. Dev keeps
  working as today until phase 3, and phases 0–2 cost nothing.
- **Cost (rough, for planning only):** AWS list prices for us-west-1 read on 2026-10-28 (Price List API, on-demand):
  RDS `db.t4g.medium` Multi-AZ 0.171 USD/h (about 125 USD/month) plus Multi-AZ gp3 0.276 USD/GB-month; NAT gateway
  0.048 USD/h each (about 70 USD/month for two); ALB 0.0252 USD/h plus capacity units (about 25 USD/month); Fargate
  0.04656 USD per vCPU-hour and 0.00511 USD per GB-hour (a 0.5 vCPU / 1 GB task is about 21 USD/month). With two
  tasks for each user-facing service, Security Hub and Config, the cross-region backup copy, logs, Enhanced
  Monitoring, secrets, keys and edge, the estimate is **about 400–550 USD/month** at list price, above the handbook's
  earlier rough 150–300. Levers: one NAT gateway at first, ARM Fargate, one task for workers, a one-year RDS
  reservation, which bring it to roughly 280–380 USD/month. Vercel Pro adds about 20 USD per seat. These figures are
  inputs to the reconciled number of the go-live gate, not that number; task counts and sizes are assumptions.
- **Cost of sharing the account:** isolation depends on IAM, tags and key policies being right; a misconfigured
  Allow is stopped only by the explicit Denies and the key policies. Quotas and SES reputation are shared (decision
  4.7). The payer vendor's management account can reach both environments; the review in decision 4.5 makes this a
  known, recorded risk rather than an unknown one.
- **Work created:** the Terraform refactor into `modules/platform-env` with a zero-change plan; the GitHub environment
  rename; per-environment boundaries and roles; Deploy Prod workflows in the app repos; Vercel prod projects; the
  allow-listed content seed job; the second acc3 invoker role. Each is a slice of AA-880 or of the app issue that
  needs prod.
- **Docs to update on acceptance:** C7.2c and C7.2d (data standards), engineering handbook §5.5, §6.1, §8 (cost row)
  and the D-16 / D-17 rows, the DevOps guide's environment table, the ops README prod section, Infra `CONTEXT.md`
  (the two roots), the skills that name the `prod` GitHub environment (`aa-ship`, `aa-cis-schema`).
- **Reversal:** before phase 3 nothing is built, so the ADR can change freely. After phase 3, moving prod to its own
  account is the decision-12 path: the module and the per-environment naming make it a new root and a data move, not
  a redesign.

## Migration path

| Phase | When | What | Cost |
|---|---|---|---|
| 0 | Now | This ADR Proposed, then Accepted by the tech lead. New code and Terraform take the environment from configuration (no new `dev` literal); new resources get the `Environment` tag | 0 |
| 1 | After acceptance, any time before a date | Rename the Infra GitHub environment (decision 6); DB Migrate `environment` input prepared for `prod` (choice not yet offered); replace `dev` literals in CI roles and the boundary | 0 |
| 2 | Before phase 3 | Terraform refactor of the environment-scoped resources into `modules/platform-env` with `moved` blocks and a zero-change Dev plan; agent role switch (U-53); management-account review (4.5) | 0 |
| 3 | Go-live date set (decision 11) | `accounts/aa365-prod` root, prod state bucket, prod roles and boundaries; Terraform plan with the reconciled cost; apply after approval; Vercel Pro and prod projects; Deploy Prod workflows; seed job; prod restore drill | Reconciled figure (estimate above) |
| 4 | Go-live | Go-live gate items checked; DNS for the prod domains; smoke per app; alarms paging; Dev becomes pre-prod | — |

The prod domain names are a business choice made with the go-live date; Dev keeps the `lumiguides.it.com`
sub-domains.
