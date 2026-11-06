---
id: FIN-03
title: AWS tagging standard
description: The eight mandatory tags every AWS resource carries (keys, allowed values, who sets them), how CI enforces them, which are cost allocation tags, how prod differs and how untagged spend is reviewed each month.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, cio, agent]
applies_to: [ecosystem, aa-nonprod, aa-ai, aa-management]
last_reviewed: 2026-11-06
review_every_days: 90
related: [FIN-01, FIN-02, ARCH-08-data-management, ARCH-08-scaling, docs/adr/0018-lean-aws-account-model.md, docs/adr/0012-environment-model.md, AA-1004, AA-828]
---

# AWS tagging standard

Every AWS resource of AA_Ecosys carries the same eight tags, so that spend can be split by environment, app and
component, and so that an auditor or an engineer on duty can tell what a resource is, who owns it and how sensitive
its data is. The rule itself is data standards [DM-10.1](data-standards/02-data-management.md#10-cost-ownership);
this page is its detail. How the money is then read and budgeted: [FinOps process](../ops/finops.md).

The standard is sized for a two-environment startup (one nonprod account, one prod account, root
[ADR 0018](../adr/0018-lean-aws-account-model.md)): one set of keys for every account, enforced in the Terraform plan,
reviewed monthly. It grows with the organization (section [Prod](#prod)), not before.

## Mandatory keys

| Key | Meaning | Allowed values | Set by |
|---|---|---|---|
| `Environment` | Which environment the resource serves | `dev`, `staging`, `prod`, `shared` | Provider default (per root) |
| `Project` | The program | `aa-ecosys` | Provider default |
| `App` | Who pays: the product the cost belongs to | `cis`, `booking`, `tripplanner`, `crm`, `identity`, `shared`, `ecosystem` | The resource or its module |
| `Component` | Which part of that app | see [Component](#component) | The resource or its module |
| `Owner` | The role that answers for it (never a person) | `tech-lead` | Provider default |
| `ManagedBy` | How it is created and changed | `terraform`, `ci`, `manual`, `aws` | Provider default (`terraform`); `ci` for resources a workflow creates |
| `CostCenter` | The budget line that pays | `technology` | Provider default |
| `DataClassification` | The most sensitive data it holds | `public`, `internal`, `confidential`, `restricted` | Provider default `internal`; data stores override |

`shared` as an `Environment` is only for organization-level resources that serve every environment: the management
account and the AI account. A resource in the nonprod account always says `dev` (or `staging`).

### App

| Value | Use for |
|---|---|
| `cis` | AA-CIS: content pipeline, catalog, CIS API and worker, Content studio API |
| `booking` | AA-Booking: back office API, staff admin, supply media |
| `tripplanner` | AA-TripPlanner-Web: the two Lambdas, its HTTP API and artifacts |
| `crm` | AA-Partner: CRM API, web, tenant portal, CRM data, mail and edge |
| `identity` | The Cognito pools, their triggers and alarms (one identity service for every app) |
| `shared` | Runtime platform used by several apps in one environment: VPC and NAT, RDS, ALB, NLB, WAF, ECS cluster, alerts topic, security detection, CI/CD roles of the account, the LLM account's roles |
| `ecosystem` | Organization-level governance in the management account: AWS Organizations, Identity Center, organization budgets and trail |

The shared RDS is `App = shared` (DM-10.3): one instance cannot carry one tag per schema. Security and CI/CD are not
Apps; they are a `Component` of `shared`, so the per-App budgets keep summing to the account budget.

### Component

`api`, `worker`, `web` (an agency or customer web front), `admin` (a staff web), `jobs` (scheduled Lambdas, event
buses, schedulers), `compute` (a cluster shared by services), `db`, `cache`, `storage`, `cdn`, `network`, `edge`
(API Gateway, ALB rules and certificates, WAF, CloudFront in front of an API), `dns`, `auth`, `mail`, `llm`,
`encryption` (KMS keys), `observability` (alarms, log groups that are not one component's, flow logs, the alerts
topic), `security` (trail, detection rules, audit logs), `cicd` (deploy and Terraform roles, OIDC provider),
`billing` (budgets, anomaly monitors), `governance` (organization, OUs, SCPs, Identity Center).

A resource that serves several parts takes the main one (the ECS log group of the CIS api and worker says `api`).

### DataClassification

| Value | What it holds | Examples |
|---|---|---|
| `restricted` | Personal data, credentials or keys to them | RDS instance, every Secrets Manager secret, Cognito user pools, CRM buckets and KMS keys, DB Migrate snapshots |
| `confidential` | Business data that is not public, logs that can hold IP addresses | Content buckets (bronze, silver, gold), ElastiCache, CloudTrail and ALB log buckets, Booking ops documents, the E2E test mailbox |
| `internal` | Infrastructure with no business data (default) | Roles, security groups, alarms, ECS services, Lambdas |
| `public` | Published on purpose | The photos CDN |

The PII classes of a column (`pii:<class>`, DM-6.1) are a different, finer list; a resource that stores any column
with a `pii:` tag is `restricted`.

## Optional keys

- `Name`: the console name, free text.
- `Issue`: the Linear issue that created or last reshaped the resource, `AA-<number>`.
- Operational keys of one feature, prefixed `aa:` for new ones: `aa:retain`, `aa:retain-until`, `aa:purpose` on RDS
  snapshots (DM-7, snapshot expiry). Older descriptive keys (`Pool`, `Layer`, `Tier`, `Role`, `Function`) may stay.

## Spelling rules

- Keys are PascalCase exactly as written above; values are lower-case kebab (`aa-ecosys`, `tech-lead`), no spaces.
- One key per meaning. These keys are refused: `Env`, `env`, `environment`, `Stage`, `Application`, `Service` (use
  `Component`), `Account` (Cost Explorer already splits by linked account), `Team`, `CostCentre`, `cost-center` and
  any spelling of a mandatory key that differs only in case.
- A new allowed value (a new app, a new component) is a PR to this page first, then to the Infra machine copy
  `tools/terraform/tag_policy.json` in the PR that needs it.

## How Terraform sets them

Each root's provider `default_tags` carries the keys that are the same for the whole root. App and Component come
from the module tag maps, never from the default in the nonprod root: a default App would silently bill every
resource that forgets its own App to one app.

```hcl
# accounts/aa365/versions.tf
locals {
  tag_defaults = {
    Project            = "aa-ecosys"
    Environment        = var.environment
    Owner              = "tech-lead"
    ManagedBy          = "terraform"
    CostCenter         = "technology"
    DataClassification = "internal"
  }
}

provider "aws" {
  region = var.aws_region
  default_tags { tags = local.tag_defaults }
}

# accounts/aa365/main.tf: a module gets App and Component, a data store its classification
module "rds" {
  # ...
  tags = merge(local.shared_app_tags, { Component = "db", DataClassification = "restricted" })
}
```

| Root (AA-CIS-Infra) | Defaults | App and Component |
|---|---|---|
| `accounts/aa365` (nonprod, Dev) | The six keys above | Per module and resource (`local.common_tags`, `local.shared_tags`, `bk_tags`, `crm_tags`, `tp_tags`, ...) |
| `accounts/acc3-bedrock` (AI account) | All eight: `App = shared`, `Component = llm`, `Environment = dev` | Budget and anomaly resources say `billing` |
| `accounts/management` | All eight: `App = ecosystem`, `Component = governance`, `Environment = shared` | Trail `security`, budgets `billing`, CI roles `cicd`; each member account gets its own `Environment` |
| `accounts/prod` (at go-live) | The six keys with `Environment = prod` | Same module tag maps as Dev (`modules/environment`) |

Resource tags win over `default_tags` for the same key, so a module map never repeats `Project`, `Environment` or
`ManagedBy`. `volume_tags` of an EC2 instance do not receive `default_tags`: the NAT instance gets the root defaults
passed in explicitly. ECS services set `propagate_tags = "SERVICE"`, so Fargate tasks (where the compute cost lands)
carry the service's tags.

## Enforcement

| Check | Where | Fails when |
|---|---|---|
| Tag guard | AA-CIS-Infra **Terraform Plan (dev)**, the required check of every Infra PR; also the management plan | A taggable AWS resource the plan creates or updates lacks a mandatory key, holds a value outside the list, says `ManagedBy` other than `terraform`, or carries a refused key (`tools/terraform/tag_guard.py`, policy `tools/terraform/tag_policy.json`) |
| Root defaults test | AA-CIS-Infra plan guard tests | A root's `default_tags` lose a key, or any tag map re-adds `Project`, `ManagedBy`, `Service` or `Account` (`tools/terraform/tests/test_tag_guard.py`) |
| Monthly report | C8 capacity review | Never fails a build; lists live resources that miss keys and the month's untagged spend (`tools/finops/untagged_report.py`) |

Resource types that expose tags but cannot carry the keys are listed with a reason under `exempt_types` in the policy
file. Today: `aws_s3_object` (object tags are not cost allocation tags; storage bills to the tagged bucket).

## Cost allocation tags

A tag splits Cost Explorer only after the payer account activates it as a **cost allocation tag**, and only for
usage from that day on.

| Key | Cost allocation tag | Why |
|---|---|---|
| `App` | Yes, active since 2026-10-15 | Per-app spend and the per-App budgets |
| `Environment` | Yes | Dev against prod once both exist |
| `Component` | Yes | Which part of an app grows |
| `Project` | Yes | Separates AA_Ecosys from anything else billed to the same payer |
| `CostCenter` | Yes | Finance view |
| `Owner`, `ManagedBy`, `DataClassification`, `Name`, `Issue` | No | Governance and operations, not money |

Who activates them: the account that pays the bill. While the nonprod account is billed by the reseller's
organization, a member account cannot activate tags, so the tech lead asks the payer to activate the keys above (as
was done for `App`). Once the account has joined our organization, the management account activates them itself, one
line (Cost Explorer's endpoint is us-east-1; about 24 hours until the keys show):

```bash
aws ce update-cost-allocation-tags-status --cost-allocation-tags-status TagKey=App,Status=Active TagKey=Environment,Status=Active TagKey=Component,Status=Active TagKey=Project,Status=Active TagKey=CostCenter,Status=Active --profile aa-mgmt --region us-east-1 # WRITE
```

A key appears in that list only after some resource in the organization carries it. Cost: 0 USD.

## What tags cannot reach

Part of every bill is not tied to a resource, so it stays "no tag" whatever we do. The monthly report labels these
lines instead of counting them as findings.

| Line | Why |
|---|---|
| AWS Data Transfer | Transfer between zones, regions and to the internet bills to the account |
| Public IPv4 addresses (VPC) | Hourly charge per public address under the VPC service |
| CloudWatch metrics, API requests, dashboards | No resource tag (log groups and alarms are tagged) |
| Cost Explorer API requests | 0.01 USD each, no resource |
| Amazon Bedrock on-demand calls | No resource tag: per-app LLM spend comes from the gateway ledger (DM-10.4), not tags |
| Tax, support plan | Account-level lines |
| Resources created before their tags, or before the key's activation | Cost Explorer does not re-tag older usage |

Resources outside Terraform: E2E test secrets, manual RDS snapshots, ENIs that AWS creates for a service. Tag them
when they are created (`ManagedBy = manual`, or `ci` from a workflow, as DB Migrate snapshots do since S271), or move
them into Terraform. Old ECS task-definition revisions and SSM session records carry no cost; the report ignores
session records.

## Prod

Prod lives in its own account, `aa-prod` (ADR 0018 decision 3), built from the same environment module, so it
carries the same keys with `Environment = prod`. Nothing else changes in the keys. What prod adds:

1. **The same guard on the prod root's plan.** `accounts/prod` gets the tag guard step in its plan job from its first
   PR.
2. **An AWS Organizations tag policy, attached to the Prod and NonProd OUs from the management account**, once prod
   exists (ADR 0018 decision 4 lists tag policies as "not now"; prod is the trigger). It fixes the key spelling and
   the allowed values of `Environment`, `App`, `Component` and `DataClassification`, and reports non-compliant
   resources in the organization's tag compliance report. A tag policy does not stop a resource from being created
   untagged; the Terraform guard does that. Generate its document from `tools/terraform/tag_policy.json`. Shape:

   ```json
   {
     "tags": {
       "Environment": {
         "tag_key": { "@@assign": "Environment" },
         "tag_value": { "@@assign": ["dev", "staging", "prod", "shared"] }
       },
       "App": {
         "tag_key": { "@@assign": "App" },
         "tag_value": { "@@assign": ["cis", "booking", "tripplanner", "crm", "identity", "shared", "ecosystem"] }
       }
     }
   }
   ```

3. **The tag-based deny of ADR 0012 decision 4** keeps working: Dev principals are denied on resources tagged
   `Environment = prod`, so the `Environment` value is also a security control, not only a cost label.
4. **An SCP that refuses creation without tags** is optional and later: only if resources start appearing outside
   Terraform in prod. It would use `aws:RequestTag` conditions on a short list of costly resource types.

## Monthly review

The C8 capacity review ([C8b](data-standards/03-scaling.md#c8-capacity-review-cadence) item 10) runs the report
once a month, with the CIS cost bundle the cost report already collects:

```bash
aws sts get-caller-identity --profile aa365-admin
bash -c 'C=$(aws configure export-credentials --profile aa365-admin --format env-no-export </dev/null) ; grep -q "^AWS_ACCESS_KEY_ID=" <<<"$C" || exit 1 ; env -u AWS_PROFILE $(tr "\n" " " <<<"$C") python3 infra/AA-CIS-Infra/tools/finops/untagged_report.py --bundle .tmp-session/cost-<yyyy-mm>/cis.txt --month <yyyy-mm> --out .tmp-session/cost-<yyyy-mm>/untagged.md'
```

`<yyyy-mm>` is the month under review; `cis.txt` is the bundle of step 2 of the
[monthly cost report](../ops/cost/README.md). The report is read only and free (Resource Groups Tagging API; the
spend comes from the stored Cost Explorer data, no new Cost Explorer call). Expected output: the month's untagged
share with its services, then a table per service and resource type.

Read it like this:

- Untagged spend on a **taggable** service is a finding: find the resource in the table and tag it (Terraform, or by
  hand with `ManagedBy = manual`).
- Untagged spend on a line from [What tags cannot reach](#what-tags-cannot-reach) is expected; write its amount in the
  review so a jump stands out.
- Target: no taggable service in the untagged row. The October 2026 baseline, before this standard, was 106.51 of
  213.90 USD without an `App` tag.

## Changing this standard

A new key or value is a PR here first (status stays `draft` until the tech lead has read it), then the Infra machine
copy and the Terraform that uses it. Changing a value in a root's `default_tags` re-tags every resource of that root:
the plan shows only in-place tag updates, it is applied locally with the MFA admin profile (the CI apply role cannot
tag the bootstrap IAM objects), and the next plan must say "No changes".
