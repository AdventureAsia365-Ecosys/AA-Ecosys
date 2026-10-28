---
id: OPS-04-ses-bounce
title: Handle an SES bounce or complaint alarm
description: What to do when aa-email-dev-bounce-rate or aa-email-dev-complaint-rate fires, before AWS reviews or pauses sending for the whole account.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [ses, aa-workforce-dev, aa-external-dev, aa-booking-api, aa-cis-api, aa-partner]
last_reviewed: 2026-10-28
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: [OPS-04, OPS-04-cognito-login, AA-811, AA-703, AA-816]
---

# Handle an SES bounce or complaint alarm

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> The alarms have never fired. Only the read-only facts below were checked (2026-10-19, again 2026-10-28).

## Why it matters

SES sending is shared by every mail stream on acc2: staff sign-in codes (Cognito WORKFORCE), traveller sign-in codes
(Cognito EXTERNAL), e-mail change checks of the PARTNER pool (it sends no sign-in codes: password plus authenticator
app), staff invites, Booking and CIS operator e-mail, and AA system mail of AA-Partner (agency invitations and
notices). AWS puts the account under review at a 5 % bounce rate or 0.1 %
complaint rate and can pause sending at 10 % / 0.5 %. A pause stops staff sign-in.

## Facts (read 2026-10-28)

- Account: production access on, sending enabled, enforcement `HEALTHY`; account suppression list on for BOUNCE and
  COMPLAINT (0 suppressed addresses).
- Identity: domain `lumiguides.it.com`, sender `no-reply@lumiguides.it.com`, custom MAIL FROM sub-domain.
- Three configuration sets, one per stream: `aa-email-dev-workforce` (WORKFORCE pool), `aa-email-dev-external`
  (EXTERNAL and PARTNER pools) and `aa-email-dev-transactional` (app mail from CIS, Booking and AA-Partner). Each sends BOUNCE, COMPLAINT and REJECT events to the SNS topic
  `aa-email-dev-feedback`.
- **The feedback topic has no subscriber** (by design until the apps implement their own suppression, AA-811 scope 3).
  So per-message details are not kept anywhere; the alarms and the suppression list are the only signals.
- Alarms (to the alerts topic, e-mail): `aa-email-dev-bounce-rate` (> 2.5 %, 1 hour) and
  `aa-email-dev-complaint-rate` (> 0.05 %, 1 hour).
- Cost: 0 USD (an SNS e-mail subscription is free at this volume).

## Steps

1. Identify the stream. Each configuration set publishes its own reputation rate (dimension
   `ses:configuration-set`; a set appears only after it has sent mail - on 2026-10-28 all three):

   ```bash
   aws cloudwatch get-metric-statistics --namespace AWS/SES --metric-name Reputation.BounceRate --dimensions Name=ses:configuration-set,Value=aa-email-dev-workforce --start-time $(date -u -d '-1 day' +%FT%TZ) --end-time $(date -u +%FT%TZ) --period 3600 --statistics Maximum --profile aa365-admin --region us-west-1 --query "Datapoints[].Maximum" --output text
   ```

   Repeat with `aa-email-dev-transactional` and `aa-email-dev-external` (and `Reputation.ComplaintRate`).
   Expected: one stream stands out. The external stream is the usual suspect (public sign-up abuse).
   Verify: the stream's rate is above the alarm threshold.
   Rollback: none - read-only.

2. See which addresses SES now suppresses.

   ```bash
   aws sesv2 list-suppressed-destinations --profile aa365-admin --region us-west-1 --query "SuppressedDestinationSummaries[].[EmailAddress,Reason,LastUpdateTime]" --output table
   ```

   Expected: the addresses that bounced hard or complained. Do not paste them into issues (personal data); write counts
   and domains only.
   Rollback: none - read-only.

3. For live details while it is happening, subscribe your e-mail to the feedback topic for the investigation.

   ```bash
   aws sns subscribe --topic-arn $(aws sns list-topics --profile aa365-admin --region us-west-1 --query "Topics[?ends_with(TopicArn, ':aa-email-dev-feedback')].TopicArn" --output text) --protocol email --notification-endpoint <your-work-email> --profile aa365-admin --region us-west-1 # WRITE
   ```

   Expected: a confirmation e-mail; after confirming, one e-mail per bounce or complaint event.
   Rollback: `aws sns unsubscribe --subscription-arn <arn from list-subscriptions-by-topic> --profile aa365-admin --region us-west-1`
   when done (do not leave a personal subscription behind; it is outside Terraform).

4. Stop the source.
   - External stream, sign-up abuse (many sign-ups to random addresses): the EXTERNAL pool has the pre sign-up trigger
     and its alarms; tighten the trigger's refusal (Infra change) or, in an emergency, allow only admin-created users on
     the EXTERNAL pool through a Terraform change (the tech lead decides; travellers cannot register meanwhile).
   - Transactional stream, an app sending to bad addresses: pause the job kind that sends (CIS `ops_alert_email` /
     `staff_invite_email`, Booking `bk_notify_email`) by cancelling its queued rows on the admin Jobs page, then fix the
     recipient source. AA-Partner sends its system mail (agency invitations, notices) directly from the API, not as a
     job: revoke the pending invitations to the bad addresses in that agency's team settings.
   - Workforce stream: invites to mistyped staff addresses; disable the wrong staff row on the Staff page.
   Expected: the bounce count from step 1 stops growing.
   Rollback: re-enable what you disabled.

5. Watch the alarm return to `OK` (the rate is a rolling reputation metric; it can take a day).

   ```bash
   aws cloudwatch describe-alarms --alarm-names aa-email-dev-bounce-rate aa-email-dev-complaint-rate --profile aa365-admin --region us-west-1 --query "MetricAlarms[].[AlarmName,StateValue,StateUpdatedTimestamp]" --output text
   aws sesv2 get-account --profile aa365-admin --region us-west-1 --query "{status:EnforcementStatus,send:SendingEnabled}" --output json
   ```

   Expected: `OK`; `EnforcementStatus` `HEALTHY`.

## Verify the result

- Alarm `OK`, account `HEALTHY`, staff sign-in codes arrive (one test sign-in).

## Roll back or abort

- Every write here (subscription, a disabled sign-up, cancelled jobs) is reversed by the step's rollback line.

## Escalation

- Account under review or `SendingEnabled` false: SEV1 (staff cannot sign in). Tell the business owner; reply to the AWS case
  with the cause and the fix. [Incident response](../incident-response.md).

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-10-19 | dev-acc2, read-only facts and step 2 | Claude Code | `docs/audits/2026-10-19-S243-ops-runbooks/readonly-checks.md` | read-only only |
