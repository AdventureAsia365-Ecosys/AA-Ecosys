---
id: OPS-04-llm-access-denied
title: LLM calls refused (llm_access_denied, Bedrock Error 002)
description: Find out, account level first, why the LLM provider refuses the platform's calls, and get the case to the right party (AWS Support, the reseller, the business owner).
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-worker, aa-cis-api, tripplanner-lambda]
last_reviewed: 2026-10-30
review_every_days: 90
last_tested: 2026-10-30
tested_where: incident
tested_evidence: real incident on the LLM account 29-30/10/2026; docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md; probes with tools/llm/llm_last_ok.py and tools/llm/llm_connections_probe.py
related: [OPS-04, OPS-04-llm-cost-spike, OPS-04-pm-2026-10-29-acc3-bedrock-access, APP-06-anthropic-key, OPS-05-ecs-exec, AA-900, AA-1002, AA-1003]
---

# LLM calls refused (llm_access_denied, Bedrock Error 002)

The steps follow the 29/10/2026 incident (see the [postmortem](../postmortems/2026-10-29-acc3-bedrock-access-refusal.md)
for the story and root cause). They are ordered so an **account-level** refusal is found first: in that incident hours
went to probing single models, regions and agreements before the account itself was clearly the problem.

Account ids and profiles: the [account map](../../onboarding.md#account-map). This repo is public: write
`<account-id>` placeholders in notes and cases kept here.

**Cost rule.** Probe through the gateway first ([`llm_connections_probe.py`](../../../tools/llm/llm_connections_probe.py)):
it logs every answered call in `shared.llm_call_log`. A direct `converse` call (steps 3-5, 8) bypasses that log, so use
it only while the gateway already fails (a refused call costs 0), with `maxTokens` 5, and note each one in the session
log.

## Triggers

- Job errors starting with `llm_access_denied` (the gateway fails fast on an account-level refusal, AA-900).
- The LLM availability card (CIS admin, Settings › LLM Models) shows `blocked`, or the Connections tab shows an open
  circuit with an access error.
- The OPS-12 daily digest's LLM line reports failures (AA-1003).
- A provider message such as "Error 002: Access to Bedrock models is not allowed for this account", or
  `AccessDeniedException` naming the account, not the role.

## Steps

1. **Confirm the symptom** in the job error, the availability card or the digest. Write down the first refusal time
   and the exact error text.
   Expected: the error names access or the account, not throttling (`ThrottlingException` is a quota problem: see the
   lessons log, section Vận hành). Abort if it is throttling or a 5xx ([5xx spike](5xx-spike.md)).

2. **When it last worked, per account** (read-only, no cost): `tools/ecs/ecsx.sh tools/llm/llm_last_ok.py`
   (optional `LAST_OK_DAYS=14`, `LAST_OK_ACCOUNT=<label>`).
   Expected: one account (or connection) stops at a clear time while the others continue. That time is the start of
   the incident; compare it with organization, billing or credit events (step 7).

3. **Gateway probe of every connection:** `tools/ecs/ecsx.sh tools/llm/llm_connections_probe.py PROBE_ACTOR=<session>-access-check`.
   Expected: the refused connections show `ok: false` with their `error_class`. Then the direct call as the account's
   IAM admin, which rules out the invoker role and its policy:
   `aws bedrock-runtime converse --model-id <model-id> --messages '[{"role":"user","content":[{"text":"OK?"}]}]' --inference-config '{"maxTokens":5}' --profile <llm-account-admin-profile> --region us-west-1`
   Refused for the admin too → not IAM; go on.

4. **First-party model** (Amazon Nova; pick an id or inference profile from `aws bedrock list-inference-profiles --profile <llm-account-admin-profile> --region us-west-1`): the same `converse` call with `--model-id <nova-model-or-profile-id>`.
   Refused too → not a Marketplace or third-party agreement problem.

5. **Another region:** the same call with `--region us-east-1` (or `us-west-2`).
   Refused too → not a regional problem.

6. **Model access state:** `aws bedrock get-foundation-model-availability --model-id <model-id> --profile <llm-account-admin-profile> --region us-west-1`
   (agreement, authorization = the use-case form, entitlement, region). Fix what is missing in the Bedrock console; after
   a new Marketplace agreement **wait about 30 minutes** and retry once before concluding anything (lessons log,
   section Vận hành).
   Expected: everything available and still refused → account level.

7. **Organization membership and payer:**
   `aws organizations describe-organization --profile <llm-account-admin-profile> --region us-east-1`
   (`AWSOrganizationsNotInUseException` = standalone account), then
   `aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventSource,AttributeValue=organizations.amazonaws.com --max-results 20 --profile <llm-account-admin-profile> --region us-east-1`.
   Ask the reseller for the end date of its credit or package on the account.
   Expected: a leave / join / payer change near the time from step 2 explains the refusal.

8. **Compare with another standalone account**, only one the tech lead names for the probe: the same one-line
   `converse` call there. Works there → the refusal is specific to this account; refused there too → an AWS-wide rule
   for standalone accounts in this situation.

9. **AWS Support case.** Basic support can open an **Account and billing** case (no paid plan needed). Text:

   ```text
   Subject: Bedrock refuses all model access on account <account-id> since <first-refusal-time UTC>

   Since <first-refusal-time UTC>, every Bedrock Runtime call from account <account-id> in <region> fails with
   "<error text>". This includes the account's IAM administrator, the first-party Amazon Nova models and other
   regions (<regions tried>). Model access, the use-case form and Marketplace agreements show as available.
   At <time> the account <left / joined> the AWS Organization of <reseller>; the payment method is valid.
   Please tell us why model access is blocked and what is needed to restore it.
   ```

   Live chat opener: "Our account <account-id> lost all Bedrock model access at <time UTC> after leaving a reseller's
   organization; case <case-id> has the details."
   Expected: a case id; record it in the session log and the postmortem, not the account id.

10. **Communication.** Give the business owner the neutral list of supply options (time, cost, fee, deposit,
    lock-in, new contract or not) in Vietnamese and let them choose; vendor messages follow
    `skill/ai-nghiep/references/stakeholders-english.md`. Add the reseller's credit or package end date to the live
    backlog, section "Time-gated checks" (`docs/backlog/README.md`).
    Expected: one decision owner, one dated check.

Rollback: every step is read-only except step 6 (agreements or forms, which only add access) and the probes' log and
audit rows. Abort the probing as soon as step 7 or the support case gives the cause.

## While access is refused

- No retry loops or catalogue reruns: refused calls are free, but a half-done wave is not.
- A fallback route is configuration, not code (AA-1002 connection registry). The Anthropic API key path:
  [Anthropic API key runbook](../runbooks/llm-anthropic-api-key.md) and `tools/llm/aa1002_anthropic_probe.py`.

## Close

- `llm_connections_probe.py` shows `ok: true` on the restored connection, the availability card is no longer
  `blocked`, and the next digest line is clean.
- The invalid paid runs of the outage are listed for a re-run, and the postmortem's actions are updated.
