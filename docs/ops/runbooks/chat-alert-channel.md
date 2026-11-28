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
6. Give the Terraform apply role its chatbot permissions. The policy is a bootstrap object (CI apply cannot change
   it), so a person applies it locally, targeted, with the MFA admin profile, from a clean checkout of AA-CIS-Infra
   `main` that already has the chat channel merged. Run each line as it is (single-line commands; the credentials go
   through `env`, never a bare `export $(...)`, which prints the whole environment when the command fails, S244).

   a. Sign in with MFA (enter the code when asked). Expected: the acc2 account and the MFA admin role.

      ```bash
      aws sts get-caller-identity --profile aa365-admin
      ```

   b. Update the checkout. Expected: `On branch main`, nothing to commit, and the file `accounts/aa365/chat_alerts.tf`
      exists.

      ```bash
      git -C /home/nghiep/projects/AA-Ecosys/infra/AA-CIS-Infra checkout main && git -C /home/nghiep/projects/AA-Ecosys/infra/AA-CIS-Infra pull --ff-only && git -C /home/nghiep/projects/AA-Ecosys/infra/AA-CIS-Infra status
      ```

   c. Initialise Terraform (it reads the S3 state backend). Expected: `Terraform has been successfully initialized!`

      ```bash
      bash -c 'cd /home/nghiep/projects/AA-Ecosys/infra/AA-CIS-Infra/accounts/aa365 && C=$(aws configure export-credentials --profile aa365-admin --format env-no-export </dev/null) ; grep -q "^AWS_ACCESS_KEY_ID=" <<<"$C" || exit 1 ; env -u AWS_PROFILE $(tr "\n" " " <<<"$C") terraform init -input=false'
      ```

   d. Plan the one policy into a saved plan file. Terraform validates every variable even under `-target`, and
      `db_password` has no default (CI passes it from a repo secret nobody can read back). The line passes the
      placeholder `unused`: the target policy does not read it and the RDS instance ignores password changes
      (`ignore_changes`), so it never reaches AWS. No other input is needed while `org_access_role_enabled = false` in
      `terraform.tfvars`; if it is `true`, also pass `TF_VAR_org_management_account_id` and
      `TF_VAR_org_management_org_id` the same way (values from the `aa-mgmt` profile, AA-CIS-Infra
      `accounts/management/README.md` section 6).

      ```bash
      bash -c 'cd /home/nghiep/projects/AA-Ecosys/infra/AA-CIS-Infra/accounts/aa365 && C=$(aws configure export-credentials --profile aa365-admin --format env-no-export </dev/null) ; grep -q "^AWS_ACCESS_KEY_ID=" <<<"$C" || exit 1 ; env -u AWS_PROFILE TF_VAR_db_password=unused $(tr "\n" " " <<<"$C") terraform plan -input=false -target=aws_iam_policy.tf_apply_sec -out=/tmp/chat-sec.tfplan'
      ```

      Expected: `Plan: 0 to add, 1 to change, 0 to destroy.` The only change is the policy
      `aa-cis-infra-tf-apply-sec`, which gains the statements `ChatAlertsConfigCreate`, `ChatAlertsConfigManage` and
      `ChatAlertsServiceLinkedRole` (the service-linked role `AWSServiceRoleForAWSChatbot` that the first channel
      configuration creates with the caller's rights). Anything else in the plan: stop and ask the tech lead.

   e. Apply the saved plan (the plan file holds the inputs), then delete the plan file.

      ```bash
      bash -c 'cd /home/nghiep/projects/AA-Ecosys/infra/AA-CIS-Infra/accounts/aa365 && C=$(aws configure export-credentials --profile aa365-admin --format env-no-export </dev/null) ; grep -q "^AWS_ACCESS_KEY_ID=" <<<"$C" || exit 1 ; env -u AWS_PROFILE $(tr "\n" " " <<<"$C") terraform apply -input=false /tmp/chat-sec.tfplan' # WRITE
      rm -f /tmp/chat-sec.tfplan
      ```

      Expected: `Apply complete! Resources: 0 added, 1 changed, 0 destroyed.` An MFA or `ExpiredToken` error: repeat
      step a, then d and e.
7. Open an AA-CIS-Infra PR that adds one line to `accounts/aa365/terraform.tfvars`: `chat_alerts_enabled = true`
   (`Refs AA-1110`). Optional second line `chat_alerts_topic = "page"` to send only the urgent alerts.
   Expected: the PR's Terraform Plan shows `3 to add`: `aws_iam_role.chat_alerts[0]`,
   `aws_iam_role_policy.chat_alerts[0]` and `aws_chatbot_slack_channel_configuration.alerts[0]`. A plan error
   "chat_alerts_enabled = true needs ..." means a secret of step 5 is missing.
8. Merge it, then run AA-CIS-Infra **Actions**, `Terraform Apply Dev`, **Run workflow** on `main` (root `aa365`).
   Expected: green, `3 added`. `AccessDenied` on `iam:CreateServiceLinkedRole` or on a `chatbot:` action means
   step 6 was not applied: do it, then run the workflow again.
9. Test. In the console, open the configuration `aa-ecosys-dev-chat-alerts` and press **Send test message**.
   Expected: a test message in the Slack channel within a minute. Then a real alarm path. Which alarm depends on the
   topic chosen in step 7:

   - `chat_alerts_topic` not set (all alerts, the default): flip a ticket-severity alarm (every e-mail recipient of
     the alerts topic also gets it):

     ```bash
     aws cloudwatch set-alarm-state --alarm-name aa-cis-dev-rds-cpu-high --state-value ALARM --state-reason "AA-1110 chat channel test" --profile aa365-admin --region us-west-1
     ```

     Expected: an alarm card in Slack within about a minute; the alarm returns to `OK` at its next evaluation
     (within 15 minutes) and posts again.

   - `chat_alerts_topic = "page"`: a ticket alarm never reaches the page topic, so the line above posts nothing in
     Slack (correct, not a fault). Flip the page-severity alarm of the alert path instead. It has no automatic
     action and sends no OK message; it reaches every recipient of both topics, so tell the business owner first:

     ```bash
     aws cloudwatch set-alarm-state --alarm-name aa-ecosys-dev-alerts-delivery-failed --state-value ALARM --state-reason "AA-1110 chat channel test, not a delivery failure" --profile aa365-admin --region us-west-1
     ```

     Expected: an alarm card in Slack within about a minute, and the page e-mail; the alarm returns to `OK` silently
     at its next evaluation (within 5 minutes).

   Nothing arrives for the alarm that matches the topic: set `logging_level` to `"ERROR"` in `chat_alerts.tf` in a
   PR, apply, repeat, and read the log group `/aws/chatbot/aa-ecosys-dev-chat-alerts` in us-east-1.
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
4. Test with the ticket-alarm `set-alarm-state` line of piece A step 9 (`aa-cis-dev-rds-cpu-high`). Expected: the
   alarm e-mail in both inboxes.
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
