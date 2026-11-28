---
id: OPS-04-chat-alerts
title: Turn on the second alert channel
description: Hand steps to send the platform alarms to a Slack channel through Amazon Q Developer in chat applications (free, Terraform-managed, off by default), the e-mail fallback recipient, and the business owner's page-alert subscription.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, owner]
applies_to: [ecosystem, aa-cis-infra]
last_reviewed: 2026-11-28
review_every_days: 90
last_tested: untested
tested_where: null
tested_evidence: null
related: [OPS-04, OPS-01-no-agent, OPS-03-tabletop, SEC-05-access-register, SEC-02, AA-1110, AA-1171]
---

# Turn on the second alert channel

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> The Terraform is merged with the channel off. Nobody has switched it on yet.

Today every alarm reaches e-mail only. This page adds a second path that a person sees on a phone within minutes, and
keeps e-mail as the fallback. Three independent pieces; do them in any order:

| Piece | What it gives | Who does it | Cost |
|---|---|---|---|
| A. Slack channel through Amazon Q Developer in chat applications | alarms posted into one Slack channel | tech lead (console once, then a PR) | 0 USD |
| B. Second e-mail recipient (fallback) | every alert also e-mailed to a company role inbox | tech lead (one repo secret) | 0 USD |
| C. Business owner on the page topic | the urgent alerts only, e-mailed to the business owner | business owner (CIS admin page) | 0 USD |

Cost basis: Amazon Q Developer in chat applications sends notifications at no additional cost (AWS documentation,
"Amazon Q Developer in chat applications rename - Summary of changes", section Pricing, read 2026-11-28); SNS delivers
the first 100,000 HTTP/S and 1,000 e-mail notifications a month free; a free Slack workspace is enough. Amazon Q answers
in the channel are not switched on (that would be the paid Q Developer Pro tier for some features).

## What reaches the Slack channel, and what does not

- Rendered in Slack: CloudWatch alarms (every service, database, NAT and security alarm), AWS Budgets and Cost Anomaly
  Detection messages, raw EventBridge events.
- E-mail only: plain-text messages on the same topic: the CIS in-app checks (job queue, connections, cost-log writes)
  and the security rules whose e-mail sentence is written by an input transformer (`[aa-sec] ...` subjects). Amazon Q
  Developer drops text it does not recognise.
- So the Slack channel is a faster second path for the alarms, not a replacement for the e-mail inboxes. Keep piece B
  or C as well.

## A. Slack channel

Preconditions: a Slack workspace owned by the company (not a personal workspace; the business owner should be a
workspace owner too), and the tech lead is a Slack workspace admin. AWS profile `aa365-admin` with MFA.

1. In Slack, create a channel for alerts (for example `#ops-alerts`; private is fine) and add the business owner.
2. Authorise the workspace once (a browser OAuth consent; Terraform cannot do it). Open the Amazon Q Developer in chat
   applications console (in acc2, region US East (Ohio); the console runs only there), choose **Slack** under
   **Configure a chat client**, **Configure**, pick the workspace, **Allow**.
   Expected: the workspace is listed in the console with its **Workspace ID** (starts with `T`).
3. In the Slack channel, type `/invite @Amazon Q` and send it.
   Expected: Slack says the app joined the channel.
4. Copy the channel ID: in Slack, open the channel name, **About** (or **Settings**), the **Channel ID** at the bottom
   (starts with `C`, or `G` for an old private channel).
5. Store both IDs as AA-CIS-Infra repo secrets (not a credential, but this repo is public). The value goes on stdin,
   never on the command line:

   ```bash
   gh secret set CHAT_ALERTS_SLACK_TEAM_ID -R AdventureAsia365-Ecosys/AA-CIS-Infra
   gh secret set CHAT_ALERTS_SLACK_CHANNEL_ID -R AdventureAsia365-Ecosys/AA-CIS-Infra
   ```

   Expected: `Set Actions secret ...` twice. Change both rows of the
   [secrets register](../../security/secrets-register.md) from **planned** to **keep** in the next root PR.
6. Give the Terraform apply role its chatbot permissions. It is a bootstrap object: a local apply with the MFA admin
   profile, from `accounts/aa365` on AA-CIS-Infra `main`, with the usual `TF_VAR_` inputs exported:

   ```bash
   terraform plan -target=aws_iam_policy.tf_apply_sec
   terraform apply -target=aws_iam_policy.tf_apply_sec
   ```

   Expected: `1 to change` (the policy `aa-cis-infra-tf-apply-sec` gains the statements `ChatAlertsConfigCreate` and
   `ChatAlertsConfigManage`), then `Apply complete! Resources: 0 added, 1 changed, 0 destroyed.`
7. Open an AA-CIS-Infra PR that adds one line to `accounts/aa365/terraform.tfvars`: `chat_alerts_enabled = true`
   (`Refs AA-1110`). Optional second line `chat_alerts_topic = "page"` to send only the urgent alerts.
   Expected: the PR's Terraform Plan shows `3 to add`: `aws_iam_role.chat_alerts[0]`,
   `aws_iam_role_policy.chat_alerts[0]` and `aws_chatbot_slack_channel_configuration.alerts[0]`. A plan error
   "chat_alerts_enabled = true needs ..." means a secret of step 5 is missing.
8. Merge it, then run AA-CIS-Infra **Actions**, `Terraform Apply Dev`, **Run workflow** on `main` (root `aa365`).
   Expected: green, `3 added`.
9. Test. In the console, open the configuration `aa-ecosys-dev-chat-alerts` and press **Send test message**.
   Expected: a test message in the Slack channel within a minute. Then a real alarm path, on a ticket-severity alarm
   (every e-mail recipient also gets it):

   ```bash
   aws cloudwatch set-alarm-state --alarm-name aa-cis-dev-rds-cpu-high --state-value ALARM --state-reason "AA-1110 chat channel test" --profile aa365-admin --region us-west-1
   ```

   Expected: an alarm card in Slack within about a minute; the alarm returns to `OK` at its next evaluation (within
   15 minutes) and posts again. Nothing arrives: set `logging_level` to `"ERROR"` in `chat_alerts.tf` in a PR, apply,
   repeat, and read the log group `/aws/chatbot/aa-ecosys-dev-chat-alerts` in us-east-1.
10. Record: the date, the Slack message screenshot and the run link in the AA-1110 evidence folder.

Switch off: a PR that removes the tfvars line, then `Terraform Apply Dev` (`3 destroyed`). The workspace
authorisation stays in the console until someone removes it there.

## B. Second e-mail recipient (fallback)

Built in S283 (AA-CIS-Infra `accounts/aa365/observability.tf`, `aws_sns_topic_subscription.alerts_email_secondary`,
off). Tech lead decision S294: the inbox is a company role inbox, never a personal one.

1. Set the repo secret (value on stdin): `gh secret set ALERT_EMAIL_SECONDARY -R AdventureAsia365-Ecosys/AA-CIS-Infra`.
2. Run `Terraform Apply Dev` on `main`. Expected: `1 added` (the subscription) and the CIS task role policy updated in
   place.
3. The inbox owner clicks **Confirm subscription** in the AWS e-mail.
4. Test with the `set-alarm-state` line of piece A step 9. Expected: the alarm e-mail in both inboxes.
5. Change the `ALERT_EMAIL_SECONDARY` row of the [secrets register](../../security/secrets-register.md) to **keep**.

## C. Business owner on the page topic

The page topic gets only the urgent alerts (security, identity, the NAT instance, the database down, failed alert
delivery; [incident response](../incident-response.md#alert-severity-page--ticket)).

1. The tech lead (or any CIS administrator) opens the CIS admin, **Platform › Alerts › Recipients**, adds the business
   owner's work address and chooses **Page alerts only**.
2. The business owner clicks **Confirm subscription** in the AWS e-mail within three days.
   Expected: the recipient shows as confirmed on the page.
3. Test at the tabletop ([security tabletop](../drills/security-tabletop.md) part B): the break-glass sign-in fires a
   page alert, and the business owner reads it on the phone.

## Escalation

[Incident response](../incident-response.md). An alarm that reaches no channel during a drill is a finding of AA-1110
(the plan's risk "no external uptime monitor" turns real).
