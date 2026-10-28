# ADR 0001 — Amendment A1: retire acc1; LLM chat models run on acc3 only, no cross-account fallback

- **Status:** Accepted (28/10/2026, S255, AA-998: the tech lead asked for acc1 to leave the ecosystem and accepts
  losing the cross-account LLM fallback). Separate file, following the `0003a` pattern; ADR 0001 itself only gets a pointer.
- **Amends:** ADR 0001 decision 2 ("Single Model Gateway"), the sentence "The fallback stays inside acc3 (previous
  model) until acc1 accepts the same agreements". The fallback now stays inside acc3 for good.
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
