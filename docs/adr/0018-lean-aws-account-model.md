# ADR 0018 — Lean AWS account model: an AA-owned organization, prod in its own account, two environments

- **Status:** Proposed (2026-10-30, S259). Records the lean variant the tech lead chose in S258 (2026-10-29) for a
  team of two to three engineers. Nothing is applied: the management account root is prepared (AA-1004) and waits
  for the management account ID.
- **Supersedes (on acceptance):** ADR 0012 decision 1 (environments), decision 2 (prod stays on the infrastructure
  account) and decision 5 (Terraform layout). ADR 0012 decisions 3, 4 and 6–12 stay in force, read with the notes
  in [Effect on ADR 0012](#effect-on-adr-0012).
- **Amends (on acceptance):** ADR 0001, the S235 sentence "Production also runs on acc2 … no new AWS account is
  created for any environment". ADR 0001a (LLM chat models on the LLM account only, no cross-account fallback) is
  unchanged: the LLM account keeps that role under the name `aa-ai`.
- **Note (S261, AA-804):** [ADR 0009](0009-ai-platform-and-provider-gateway.md) (Proposed) decision 14 would amend
  this: `aa-nonprod` (acc2), and later `aa-prod`, may serve Bedrock chat models of the families they can run for
  eval, judge and validate stages only, and every `failure_domain` is re-checked at each payer or organization change
  in this ADR's timeline. If both are accepted, the `aa-ai` row below reads "main Bedrock chat account" instead of
  "Bedrock chat models only".
- **Scope:** AA-CIS-Infra (a new `accounts/management` root, the future `accounts/prod` root, state buckets, OIDC
  roles per account), every app repo (Deploy Prod targets another account), root (account map in onboarding, data
  standards C7.2c, the engineering handbook D-17 row, the DevOps guide, skills that name AWS profiles).
- **Related Linear:** AA-1002 (the blueprint), AA-1004 (management root), AA-880 (prod blueprint, ADR 0012),
  AA-864 (consolidate on an AA-controlled account; answered by this ADR).
- **Design source:** the S258 AWS organization blueprint,
  [`docs/audits/2026-10-29-S258-aws-org-blueprint/README.md`](../audits/2026-10-29-S258-aws-org-blueprint/README.md)
  §0 (lean variant, recommended), with §2–§4 and §7 as the long-term target it can grow into.

## Context

ADR 0012 (accepted S257) put prod next to Dev on the infrastructure account and compensated for the shared account
with tag-based denies, per-environment boundaries and key policies. Its decision 12 listed the triggers that would
reopen a separate prod account. Two of them have now happened:

- **AA-864 is answered.** The business now has its own AWS management account, created empty by the tech lead on
  2026-10-30 (S259), after the S258 blueprint. The
  company can run its own AWS Organization instead of living as a member of the payer vendor's organization.
- **The management-account review (ADR 0012 decision 4.5) is not acceptable as a long-term state.** The
  infrastructure account is a member of the vendor's organization: principals of the vendor's management account
  sit outside our IAM and can reach both environments, and the vendor's SCPs decide which Bedrock models the
  account may call (ADR 0001a).

The S258 blueprint designed the full target (nine accounts, seven OUs, about nine SCPs, three environments) and a
lean variant for the team as it is: two to three engineers and one tech lead. The tech lead chose the lean variant
on 2026-10-29: two environments and three to four accounts, with the full design kept as the growth path, triggered
by named conditions rather than by date.

## Decision

### 1. Accounts

| Account | Today | Holds | When |
|---|---|---|---|
| `aa-management` | New and empty, created by the tech lead on 2026-10-30 | AWS Organizations, IAM Identity Center, billing and budgets, Cost Anomaly Detection, the organization CloudTrail and its log bucket. **No workload**, ever (SCPs do not apply to this account) | Day 1 |
| `aa-nonprod` | The infrastructure account (acc2 in the [account map](../onboarding.md#account-map)) | Dev, and staging when switched on (decision 2) | Joins by invitation once the payer vendor releases it |
| `aa-prod` | Does not exist | Real customers: the prod environment of ADR 0012 decisions 3 and 7–10 | Created by the management root when the go-live date is set (ADR 0012 decision 11) |
| `aa-ai` | The LLM account (acc3) | Bedrock chat models only, with an invoker role per environment | Joins by invitation if the billing model allows it; folded into nonprod and prod once those accounts can call Bedrock themselves |

Account IDs stay in the onboarding account map only. Every Terraform root takes them as variables; none is written
in code (the root and Infra repos are public for now).

### 2. Environments (supersedes ADR 0012 decision 1)

| Environment | Account | Data | Notes |
|---|---|---|---|
| Local | Engineer machine | Fixtures | Unchanged |
| PR preview | Vercel | Calls Dev | Unchanged |
| **Dev** | `aa-nonprod` | Test or synthetic data only (C7.1a) | Unchanged; pre-prod once prod exists |
| **Staging** (on demand) | `aa-nonprod` | Test data, or an anonymised copy when a release needs it | Same RDS instance with its own database, its own ECS services kept at 0 tasks when unused, `stg-` host names; switched on before a large release or a UAT, off otherwise |
| **Prod** | `aa-prod` | Real users and real personal data | Customers, agencies, staff doing real work |

Two account-level environments, nonprod and prod. Environment names in code, tags, secrets and workflows are
`dev`, `staging` and `prod`. Staging never holds personal data from prod.

### 3. Prod lives in its own account (supersedes ADR 0012 decision 2)

Prod is built in `aa-prod`, in us-west-1, with the same environment module as Dev. The account boundary is the
primary isolation between Dev and prod; the per-environment controls of ADR 0012 decisions 3 and 4 remain as
defence in depth inside each account. Bedrock chat models for prod go through `aa-ai` with a prod-only invoker
role (ADR 0012 decision 3, "LLM path").

### 4. Organization and governance (minimum set)

- **OUs:** `NonProd`, `Prod`, `Suspended`. A newly invited account first sits directly under the organization root
  (no SCP of ours applies there), so it can still leave if billing, credits or Bedrock break; after one quiet week it
  moves to its OU.
- **Three SCPs, attached to the three OUs, never to the root:** (1) members cannot leave the organization or close
  themselves; (2) no trail stop, delete or update and no billing, payment or tax change outside the admin and
  Terraform apply roles; (3) only us-west-1, us-east-1 (ACM) and us-west-2 (backup copies), with global services
  exempt and Bedrock allowed the cross-Region inference destinations.
- **IAM Identity Center** in us-west-1, MFA on every sign-in: groups `aa-admins` (tech lead), `aa-developers`
  (engineers) and `aa-billing` (business owner, read-only costs and invoices), four permission sets (`AA-Admin`
  1 hour, `AA-Developer` 8 hours in nonprod and ai only, `AA-ReadOnly` in prod, `AA-Billing`). No IAM users, no
  static keys. CI and agents use IAM roles inside each member account; the agent never gets a prod role.
- **Break-glass:** the management root user with two hardware security keys (tech lead, business owner's safe).
- **Spend:** an organization budget, one budget per account and one Cost Anomaly Detection monitor per account, all
  in the management account, counting gross cost (credits excluded). Free.
- **Audit:** one organization CloudTrail, multi-region, management events, log file validation, to a bucket in the
  management account (SSE-KMS, Object Lock GOVERNANCE 365 days). The nonprod account's own trail is removed after
  the organization trail has delivered cleanly for 7 days.
- **Not now:** log-archive, security, backup and shared-services accounts; paid security services (GuardDuty,
  Security Hub, Config); RCPs, tag and backup policies. Each is added on the triggers in decision 6.

### 5. Terraform layout (supersedes ADR 0012 decision 5)

- **One root per account under `accounts/<name>/`, one state bucket per account, in that account.** Nothing crosses
  accounts on the state path.
- **`accounts/management`** (new, AA-1004): the organization, OUs, SCPs, Identity Center, budgets, anomaly
  monitors, organization trail. State in the management account's own bucket.
- **`accounts/aa365`** stays the root of `aa-nonprod` with its current state; renaming it is optional clean-up. The
  environment-scoped resources become one module (`modules/platform-env` in ADR 0012, `modules/environment` in the
  blueprint; one name chosen in that PR) through `moved` blocks and a zero-change Dev plan, as ADR 0012 already
  planned.
- **`accounts/prod`** (at go-live) calls the same module with `environment = "prod"` in `aa-prod`, with its own
  state bucket, its own OIDC provider and roles, and `allowed_account_ids` set from a variable. It replaces the
  `accounts/aa365-prod` root of ADR 0012.
- **`accounts/acc3-bedrock`** stays the root of `aa-ai`; it gains the native lockfile and loses the hard-coded
  profile when it moves to CI.
- Every provider block sets `allowed_account_ids` from a variable, so a credential for the wrong account fails the
  plan (AA-517). CI plans on pull requests and applies on manual dispatch per root; the management and prod roots
  apply only through a GitHub environment with the tech lead as required reviewer.

### 6. When to grow towards the full blueprint

| Add | When |
|---|---|
| Log-archive and security accounts | A customer or auditor asks, or more than five engineers |
| A separate staging account | Staging must run continuously, or customers do UAT on it |
| A backup account | Prod data becomes valuable enough to need deletion-proof copies in another account |
| A shared-services account | Several accounts need shared ECR or DNS |
| Paid security services | Before go-live or when sensitive data arrives; each one approved with its monthly cost |

## Effect on ADR 0012

- Decisions 1, 2 and 5 are replaced by decisions 2, 3 and 5 above.
- Decision 3 (isolation per environment) applies inside each account; between Dev and prod the account boundary now
  does most of the work.
- Decision 4 (compensating controls for a shared account): 4.1–4.3 become defence in depth, not the main fence;
  4.4 (no agent access to prod) stays as written; 4.5 (management-account review) is replaced by the move into the
  AA-owned organization; 4.6 and 4.7 stay.
- Decision 6 (renaming the `prod` GitHub environment of AA-CIS-Infra) stays: the Dev apply role still trusts
  `environment:prod` today.
- Decisions 7–11 stay; "copy the image by digest from the Dev ECR repository to the prod repository" now crosses
  accounts (the prod deploy role reads the Dev repository through a repository policy).
- Decision 12 is answered: the separate prod account is chosen.

## Consequences

- (+) Prod is isolated by the strongest AWS boundary: IAM, quotas, SES reputation, KMS and CloudTrail are separate by
  construction, and an audit question "is prod separated?" has a one-word answer.
- (+) The company holds the management account and the root of its organization; no vendor principal sits above
  either environment once the vendor releases the infrastructure account.
- (+) Day-one cost is small: the management account costs about 1–2.5 USD a month (KMS key, trail storage);
  Organizations, Identity Center, SCPs, budgets and anomaly detection are free. Engineering effort is about five to
  eight days before prod; prod itself is built at go-live (the blueprint estimates 280–410 USD a month with
  savings levers, 410–580 at list price).
- (−) Joining the organization changes the payer: billing history in the vendor's organization does not follow,
  Vietnamese VAT invoices may not be available from AWS directly, Bedrock model access and the AI account's credit may
  need to be re-checked (blueprint §3 and §5). The billing model is the business owner's decision, made before the
  invitations.
- (−) Image promotion and DNS become cross-account work (repository policy, delegated zones).
- (−) Two more state buckets and two more sets of OIDC roles to keep in step.
- **Reversal:** before prod exists, the management root can be abandoned while the organization has no member.
  After prod exists, moving back to one account is a data migration; it is not expected.

## Alternatives considered

- **ADR 0012 as accepted (prod on the infrastructure account)**: cheapest, but its isolation depends on IAM, tags and
  key policies being right, and the vendor's management account reaches both environments. Superseded once an
  AA-owned management account exists.
- **The full blueprint (nine accounts, seven OUs, about nine SCPs, three environments)**: the right shape for a
  larger team or an audit, but about 30 engineer-days and more accounts than two or three people can watch. Kept as
  the growth path (decision 6).
- **A staging account now**: staging is needed a few days a month; an always-on account would cost about
  90–200 USD a month for little use. Staging runs on demand inside nonprod instead.
- **AWS Control Tower**: brings a landing zone with log-archive and audit accounts and AWS Config, which this team
  does not need yet and which adds cost. Not chosen; the Terraform root keeps every control readable in one place.
