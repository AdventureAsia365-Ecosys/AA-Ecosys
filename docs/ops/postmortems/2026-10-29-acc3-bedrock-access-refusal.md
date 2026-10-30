---
id: OPS-04-pm-2026-10-29-acc3-bedrock-access
title: "Postmortem: Bedrock refused every model on the LLM account (2026-10-29)"
description: From 29/10/2026 13:50 ICT Bedrock refused model access on acc3, the only LLM account, so every platform LLM call stopped; still open, a supplier decision is pending.
type: report
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem, aa-cis-worker, aa-cis-api, tripplanner-lambda]
last_reviewed: 2026-10-30
related: [OPS-04, OPS-04-postmortems, FIN-01, AA-900, AA-998, AA-999, AA-1002, AA-1003, docs/adr/0001a-retire-acc1-llm-on-acc3-only.md, docs/audits/2026-10-29-S257-llm-access-options/]
---

# Postmortem: Bedrock refused every model on the LLM account (2026-10-29)

## 1. Summary

On 29/10/2026 the LLM account (acc3) left its AWS reseller's organization when the reseller's credit package for it
ended. Minutes later Bedrock refused the OpenAI models on acc3, and by the afternoon it refused every model on the
account ("Error 002: Access to Bedrock models is not allowed for this account"), in every region tried. All chat and
judge LLM calls of the platform stopped; embeddings, which run on the infrastructure account (acc2), kept working. At
the time of writing (30/10) access is not restored: an AWS Support case is open and the business owner is choosing
between supply options.

## 2. Impact

| Item | Value |
|---|---|
| SEV | 2 (every LLM feature down on the only environment; no tenant or customer on Dev) |
| Who was affected | Staff and agents only: content pipeline (S1 writer, judges, T-stages), evaluations, TripPlanner AI composition on Dev |
| Duration | From 13:50 ICT on 29/10/2026 (OpenAI models) and by about 15:20 ICT (every model); open at the time of writing |
| Data | None lost or exposed |
| Cost impact | One evaluation run (AA-900 R2) became invalid, about 0.11 USD; no overspend |
| Paid runs stopped or delayed | Every LLM run: AA-900 R2 re-run, AA-919 labelling round, AA-790 blog sample, catalogue rewrites |

## 3. Key times

| KPI (ID@version) | Definition | Target | Actual |
|---|---|---|---|
| K-INC-TTD@1 | Impact start to first alert or report | < 15 min (SEV1) | Not measured: no alert; found the same afternoon by reading a failed evaluation run (exact minute not recorded) |
| K-INC-TTR@1 | Detection to restored | < 1 working day | Not restored after 1 working day (open) |
| K-INC-COSTATTR@1 | Cost alert to written cause | <= 1 working day | Not a cost incident |

## 4. Timeline (UTC+7)

| Time | Event | Source |
|---|---|---|
| 29/10 13:50 | acc3 leaves the reseller's AWS Organization (CloudTrail: the organizations service removes its service-linked role; `describe-organization` no longer lists the account) | CloudTrail, read afterwards |
| 29/10 ~13:50 | OpenAI models on Bedrock in acc3 (the judge route) answer AccessDenied "not available for this account"; Claude on acc3 still answers | Failed evaluation run (AA-900 R2) |
| 29/10 14:11 | Last failing LLM call from a platform job; Dev is idle afterwards, so no further failures pile up | `shared.job` errors |
| 29/10 ~14:49 | The tech lead forwards the reseller's notice: its credit package for acc3 has ended; from 29/10 acc3 bills go to the company card (after the account's own AWS credit) | Person (vendor message) |
| 29/10 afternoon | Marketplace agreement created for the second OpenAI model; a test call is still refused six minutes later | Agent probe |
| 29/10 ~15:20 | Payment method on acc3 confirmed valid. Re-probe: every Bedrock model on acc3, Claude included, answers "Error 002: Access to Bedrock models is not allowed for this account" | Tech lead (console) and agent probe |
| 29/10 15:35–19:40 | Error 002 confirmed in six regions and for every model family; Marketplace agreements and the model use-case form are in place. The tech lead opens an AWS Support case (Basic plan). Supply options researched (root audit `2026-10-29-S257-llm-access-options`) | Agent and tech lead |
| 29/10 17:59–19:11 | Talks with the reseller about billing transfer and model access (terms are not recorded in this repo) | Person |
| 29/10 evening | The business owner gets five neutral options (buy from the model maker directly, a reseller for acc3, both accounts with one reseller, wait, move the infrastructure) | Tech lead (Zalo) |
| 29/10 23:47 | Gateway probe: the judge model answers `LLMAccessDenied` and the gateway fails fast (the AA-900 change of S258) | Agent probe |
| 30/10 | Still refused; decision pending | — |

## 5. Detection

No signal watched "the provider refuses this account". The first sign was a paid evaluation run whose judge calls
failed, read during the afternoon session. A refusal of a billed call leaves no `shared.llm_call_log` row, so the cost
pages showed nothing unusual, and the job errors said only "run failed after retries" until AA-900 prefixed them with
`llm_access_denied`. Since S258 the LLM availability card (Settings › LLM Models) shows `blocked` from the job errors,
and the OPS-12 daily digest (AA-1003 R2) prints the LLM route status every morning; neither existed on 29/10.

## 6. Root cause

1. Why did the LLM calls fail? Bedrock refused model access for acc3 (Error 002), first for the OpenAI models, then for
   every model.
2. Why did Bedrock refuse? acc3 left the reseller's AWS Organization when the reseller's credit package ended. As a
   standalone account it is not allowed Bedrock model access; the reason is with AWS Support. Access to third-party
   models on Bedrock depends on who pays for the account, not only on IAM, agreements and forms.
3. Why did that stop every LLM feature? Since AA-998 (ADR 0001a) all chat and judge models run on acc3 only, through
   one provider (Bedrock). The infrastructure account (acc2) cannot use those models either, because its reseller is
   not approved for them. There was no second path outside acc3.
4. Why was it not seen coming? The end date of the reseller's package was not tracked as a dated risk, and what
   leaving the organization would do to model access was not known; the notice arrived on the day.
5. Why did no alarm fire? Refusals were only visible as failed jobs; there was no availability signal and no daily
   digest.

System cause: a single supplier path for every LLM call, with a commercial dependency (the payer of acc3) that was not
tracked or monitored.

## 7. Cost attribution (cost incidents)

Not a cost incident. The only waste is the invalid AA-900 R2 evaluation run (stage `adhoc_aa900`, about 0.11 USD on
acc3), to be re-run once access is back.

## 8. What went well, what went badly

### Went well

- No route to another account existed any more (AA-998), so no call went to an account outside the ecosystem.
- Dev had no customers, so the outage cost development time, not trust.
- Options were researched and costed the same day and given to the business owner without pushing a contract.

### Went badly

- The first sign was a paid run that failed, not an alert.
- Hours went to probing models, regions and agreements before the account-level refusal was clear.
- The package end date and its effect were known only to the reseller.

### Where we got lucky

- The refusal came while Dev was idle: no wave or catalogue rewrite was half done.
- Embeddings run on acc2 and were not part of the acc3 refusal.

## 9. Actions

| Action | Type | Owner role | Due | Linear issue | Status |
|---|---|---|---|---|---|
| Choose the LLM supply route (one of the five options) | design | business owner, tech lead | when decided | — | open |
| LLM availability card and fail fast on an account-level refusal (`llm_access_denied`) | alarm | tech lead | S258 | AA-900 | done (CIS #1148) |
| LLM connection registry, so a second provider or account is configuration, not a code change | design | tech lead | after the decision | AA-1002 | in progress |
| Daily digest prints the LLM route status and failures (OPS-12) | alarm | tech lead | S259 | AA-1003 | in review |
| Track supplier credit and package end dates as time-gated checks in the live backlog | runbook | tech lead | next session | — | open |
| Re-run the invalid AA-900 R2 evaluation once access is back | test | tech lead | after restore | AA-900 | open |
| Symptom-driven playbook, account-level cause first, with read-only helpers (`tools/llm/llm_last_ok.py`, `tools/llm/llm_connections_probe.py`): [LLM calls refused](../playbooks/llm-access-denied.md) | runbook | tech lead | S260 | — | done (S260) |

## 10. Communication

No tenant or customer was affected, so nobody outside the team was told. The business owner was told the same evening
(Zalo, with the five options); the choice is the business owner's.

## 11. Business summary

On 29 October the AWS account that runs the platform's AI models lost permission to use them when the reseller's
prepaid package for that account ended, so every AI feature on the development system stopped. No customer data or
money was affected, and only one small test run (about 0.11 USD) was wasted. A choice of supplier is needed to restore
the AI features, and the platform now shows the AI status every morning so the next stop is seen at once.

## 12. Lessons

Lesson line in `skill/aa-lessons/lessons.md`, section "Vận hành" (model access on Bedrock depends on the payer of the
account; supplier package end dates are dated risks). Related reading: the supply options audit
`docs/audits/2026-10-29-S257-llm-access-options/`, the session log `docs/sessions/2026-10-29-S257-*.md`.
