# ADR 0001 — Amendment A1: retire acc1; LLM chat models run on acc3 only, no cross-account fallback

- **Status:** Accepted (28/10/2026, S255, AA-998: the tech lead asked for acc1 to leave the ecosystem and accepts
  losing the cross-account LLM fallback). Separate file, following the `0003a` pattern; ADR 0001 itself only gets a pointer.
  Partly reversed for Bedrock chat serving only by the Note S278 at the end (12/11/2026, AA-1095).
- **Amends:** ADR 0001 decision 2 ("Single Model Gateway"), the sentence "The fallback stays inside acc3 (previous
  model) until acc1 accepts the same agreements". The fallback now stays inside acc3 for good.
- **Amended by:** [ADR 0009](0009-ai-platform-and-provider-gateway.md) decision 14 (Accepted 2026-10-31, S261):
  acc3 stays the main Bedrock chat account; acc2 may serve chat models for eval, judge and validate stages only (never
  writer or tenant stages), after the model passes the qualification ladder; the direct Anthropic and OpenAI APIs are
  warm paths outside AWS. "No cross-account fallback" therefore holds for writer and tenant stages only; judge and
  validate routes may end on acc2. The account names
  follow [ADR 0018](0018-lean-aws-account-model.md) (acc3 = `aa-ai`, acc2 = `aa-nonprod`).
- **Supersedes:** the AA-296 satellite pattern's acc1 leg and the earlier decision to keep acc1 active for it
  (ADR-2026-022, amended; record in the AA-CIS-Infra ADR index).
- **Consistent with:** ADR 0001 decisions 1–7, ADR 0004 (every app on acc2), the account map in
  [onboarding](../onboarding.md#account-map) and the [ecosystem architecture](../ecosystem-architecture.md) §4.3–§4.4.
- **Design source:** the read-only AA-998 audit (S255): every acc1 reference in the six repos, the live paths that
  could still reach acc1, and the DRY RUN deletion list.

## Context

acc1 is a personal AWS account (ID in the [account map](../onboarding.md#account-map)). Its compute was destroyed
on 09/07/2026 (AA-271), but it stayed in the ecosystem as the **fallback LLM satellite** (role `AA-Bedrock-Invoker`,
AA-296), as a Cost Explorer reader (`AA-CostExplorer-Reader`) and as a Bedrock Batch role, all in the Terraform root
`accounts/acc1-bedrock`.
In practice:

- Since September 2026 its bill is under 1 USD a month (0.97 USD in September, S255 FinOps review), from Bedrock
  fallback calls made when an acc3 call failed.
- The Claude 5.5 models (Haiku 5.5, Sonnet 5.5, CIS migration 259) are callable on acc3 only; acc1 reports them as
  not available for the account, so the fallback leg mostly served the older legacy keys.
- Personal money is spent on ecosystem work, and a second account doubles the IAM, budget and audit surface. The
  static acc1 key in `~/.aws/credentials` caused two wrong-account writes before AA-517.

## Decision

1. **The ecosystem runs on two AWS accounts:** acc2 for all infrastructure (and the Bedrock models it calls natively
   today, such as Cohere Embed v4), acc3 as the only LLM satellite for Bedrock chat models. acc1 is not part of the
   ecosystem: no resource, deploy, secret, Cost Explorer read or LLM route goes there, and code, Terraform and the
   model catalog do not name it.
2. **No cross-account LLM fallback.** When an acc3 call fails, the stage route falls back to another model on acc3
   (the legacy chain: Sonnet, then Haiku), or the job retries, or the stage's external fallback (OpenAI) runs where
   it is configured. A full acc3 outage stops acc3-routed stages until acc3 is back; the tech lead accepts this risk.
3. **Removal order (AA-998):** cut the call paths first (CIS and TripPlanner gateways, Cost Explorer, catalog
   migration that drops acc1 profiles and limits `account_route` to acc3, AA-CIS-Infra grants and environment), then
   `terraform destroy` of `accounts/acc1-bedrock` by a human with MFA, then the DRY RUN list of leftover acc1
   resources, approved line by line by the tech lead. The account itself stays a personal account, outside the
   ecosystem.
4. **History is kept.** Old migrations, `generated_content.satellite_account = 'acc1'` rows, `llm_call_log` rows with
   `account = 'acc1'`, session logs, audits and implementation notes are not rewritten. The acc1 account ID stays in
   the public-repo leak pattern ([security baseline](../security/baseline.md)) so it never comes back.

**Done on 2026-10-28 (S255):** the call paths were cut (CIS migration 295, TripPlanner #174, AA-CIS-Infra #466),
the `accounts/acc1-bedrock` root was destroyed with its state bucket, and the leftover acc1 resources on the DRY RUN
list were deleted. The re-inventory found no ecosystem role, OIDC provider, bucket, Lambda, log group, task
definition or us-west-1 secret left in acc1.

## Consequences

- **Good:** no personal spend on the ecosystem; one satellite account to govern (IAM allow-list, budgets, model
  agreements); the gateway route model is simpler (no account order acc3 → acc1 → acc2).
- **Cost:** losing the cross-account fallback. An acc3 throttle or AccessDenied now degrades to an acc3 model or a
  retry instead of a call on another account.
- **Watch:** the first cost review after AA-998 checks that acc1 shows 0 USD for ecosystem services, and
  `shared.llm_call_log` shows no `account = 'acc1'` row after the cut-over.
- **Reversal:** adding a second satellite later means a new account under the same rules as acc3 (Terraform root,
  ExternalId, catalog profiles, budgets), not a return to the personal account.

## Note — 11/11/2026 (S277): acc1 becomes the payer of acc3, still no workload

On the reseller's advice (TrueIDC, for the Bedrock model access and quota cases), the tech lead invited acc3 into
the AWS Organization whose management account is acc1, and acc3 accepted on 11/11/2026. What changes and what does not:

- **Billing only.** acc1 pays acc3's bill. The two AWS Lift promotional credits (one per account, 1/9–31/12/2026) are
  pooled. Lift credits do not cover Claude on Bedrock: it is billed as "Claude … (Amazon Bedrock Edition)" and paid by
  card (Cost Explorer on acc1, September and October 2026).
- **No workload on acc1.** The decision of this ADR stands: no resource, deploy, secret or LLM route on acc1. acc1
  runs IAM Identity Center for its own organization; the tech lead's sign-in to acc3 can use it (permission set
  AA-Admin), next to the existing acc3 access.
- **Runtime paths unchanged.** Calls from acc2 to acc3 use the cross-account role in acc3 and do not depend on the
  organization. acc3 sits at the organization root; no SCP of acc1's organization applies to it today. Moving acc3
  into an OU with SCPs needs a check that the SCPs allow Bedrock in us-west-1.
- **Open:** the billing transfer of acc2 to the management account acc4 (ADR 0018) is a separate track. If acc3 later
  moves to acc4's organization it must leave acc1's organization first.
- A support case for the model access was also opened from acc1 as the management account (case number in the private
  case notes).

## Note — 12/11/2026 (S278): Bedrock chat models served from acc1 while acc3 is blocked

**Decision (tech lead, AA-1095):** "if acc1 can use every model of the system, use acc1 instead of acc3". This
reverses decision 1 above for ONE purpose only: serving the gateway's Bedrock chat models. Everything else in this
ADR stands.

- **Evidence.** AWS refuses the gateway's chat models on acc3 at account level (seven models refused, token quota 0
  on five; cases open with AWS and the reseller). On 12/11/2026 every chat model the gateway uses (the Claude 5.5,
  5 and 4.x models and the GPT-6, 6.1 and 5.6 models) answered a real Converse call on acc1 through its `global.`
  inference profile in us-west-1, with global token quotas of 2M to 30M.
- **Scope on acc1.** One IAM role for Bedrock invocation (Terraform root `accounts/acc1-bedrock` in AA-CIS-Infra,
  with its own state bucket on acc1), trusted only by the CIS ECS task role on acc2 with an ExternalId, allowed to
  invoke the chat models and nothing else. No data, no secret, no compute, no Batch, no Cost Explorer reader and no
  paid budget or anomaly monitor (the role and the state bucket cost under 0.01 USD a month). acc1 stays the payer of
  acc3's organization (Note S277).
- **Gateway.** acc1 is a registry connection (CIS migration 406), not a key in code: its account ID comes from a task
  environment variable set by AA-CIS-Infra from a repository secret, so neither the public app repos nor AA-CIS-Infra
  carry it. Its spend is read from
  the gateway ledger (no Cost Explorer reader on acc1), under a monthly cap copied from acc3's.
- **Route order per model family** (one audited route-control version, revertible in one click, model-first
  order): Claude models use the Anthropic API first (no cost to us at the moment), then Bedrock on acc1, then acc3.
  GPT models use Bedrock on acc1 first, then acc3, then the OpenAI API: the OpenAI API path of a GPT model is a
  separate "twin" catalog model right behind it on the stage chain (an OpenAI connection serves only OpenAI catalog
  rows), so it always comes after every Bedrock deployment of the model. While acc3 refuses, the gateway skips its
  deployments at no cost and the calls follow the decided order (acc1, then the OpenAI API). acc3 is not removed and
  not switched off: its connection and deployments stay configured behind acc1. Switching the acc3 GPT deployments
  off (the "or disabled" option) needs an audited per-deployment switch that does not exist yet; it is a follow-up
  if wanted.
- **Reversal.** When acc3's case is solved: revert the route-control version (or move acc3 back to first), switch
  the acc1 connection off, then remove the acc1 deployments and connection with a forward CIS migration, remove the
  task environment variable and the role grant in AA-CIS-Infra, and tear down the `accounts/acc1-bedrock` root with its
  state bucket (a human with the acc1 sign-in).
- **Watch.** `shared.llm_call_log` rows with `account = 'acc1'` are expected again (Claude only behind the Anthropic
  API); card spend for Claude on Bedrock moves from acc3's bill to acc1's. If acc3 starts answering again before the
  reversal, GPT calls go to acc3 before the OpenAI API (AWS preferred): do the reversal then, or switch the acc3 GPT
  deployments off.
