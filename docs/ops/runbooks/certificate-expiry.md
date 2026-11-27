---
id: OPS-04-certificate-expiry
title: Handle an ACM certificate expiry alert
description: What to do when an "[aa-sec] acm_expiry" e-mail says an ACM certificate is close to expiry, failed renewal or expired, in us-west-1 or us-east-1.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [acm, route53, aa-cis-api, aa-booking-api, cloudfront]
last_reviewed: 2026-11-27
review_every_days: 90
last_tested: untested
tested_where: null
tested_evidence: null
related: [OPS-04, SEC-02, SEC-02-rotation, AA-1183]
---

# Handle an ACM certificate expiry alert

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> The rule has never fired on a real certificate; its test event is part of AA-1183's done-when.

## Why it matters

Every Dev hostname under `lumiguides.it.com` serves an ACM certificate: the API custom domains and the load balancer
listener in us-west-1, the CloudFront and Cognito custom domains in us-east-1. ACM renews its own certificates about 60
days before expiry when the DNS validation record still resolves. ACM only sends an **approaching expiration** event
when that renewal has not happened (daily from 45 days before expiry by default, account setting DaysBeforeExpiry), a **renewal action
required** event when it tried and failed, and an **expired** event when it is too late. When a certificate expires,
browsers and API clients refuse the hostname: the page or API is down for everyone.

The alert comes from the AA-CIS-Infra EventBridge rule `aa-sec-<env>-acm-expiry` (us-west-1; us-east-1 events are
forwarded to it) on the alerts topic, severity ticket. The register lists every certificate and its expiry date
([secrets register, Rotation](../../security/secrets-register.md#rotation), stores `acm:us-west-1` and
`acm:us-east-1`).

## Read the state (read-only)

Take the certificate ARN and region from the e-mail, then (single-line commands):

```bash
aws acm describe-certificate --certificate-arn <arn> --region <region> --profile aa365-admin --query 'Certificate.{Domain:DomainName,NotAfter:NotAfter,Status:Status,Renewal:RenewalSummary,InUseBy:InUseBy,Eligible:RenewalEligibility}' --output json
aws acm describe-certificate --certificate-arn <arn> --region <region> --profile aa365-admin --query 'Certificate.DomainValidationOptions[].ResourceRecord' --output table
```

- `RenewalEligibility` `INELIGIBLE` with an empty `InUseBy`: nothing uses the certificate, ACM does not renew it. If
  no Terraform resource or listener needs it, it can expire (record the decision in the register row).
- `RenewalSummary.RenewalStatus` `PENDING_VALIDATION` or `FAILED`: the validation record is missing or wrong. Check it
  resolves: `dig +short CNAME <ResourceRecord.Name>` must print the `ResourceRecord.Value`.

## Fix

1. Missing validation CNAME: the record belongs in the Route 53 zone of `lumiguides.it.com`, managed by AA-CIS-Infra
   (`accounts/aa365/custom_domains.tf`, `dns.tf` parity records, or the `*_acm_validation` resource next to the
   certificate). Add it through a Terraform PR; never by hand in the console. ACM retries validation on its own once
   the record resolves (minutes to a few hours).
2. A CAA record that blocks Amazon: allow `amazon.com` in the zone's CAA record through Terraform.
3. Less than 7 days left and validation still pending: request a new certificate for the same names through Terraform,
   validate it, and switch the listener or distribution to it; then let the old one expire.

## Verify the result

- `describe-certificate` shows a `NotAfter` about 13 months ahead and `RenewalStatus` `SUCCESS`; ACM also sends an
  "ACM Certificate Available" event (no e-mail).
- `curl -sv https://<hostname>/ -o /dev/null 2>&1 | grep 'expire date'` shows the new date.
- Update the certificate's `expires` in `docs/security/secrets-register.yaml`, then
  `python3 tools/security/secrets_register.py md --write` in a root PR.

## Roll back or abort

Nothing here changes a live resource outside Terraform. A wrong DNS change is rolled back with
[Roll back a Terraform change](rollback-terraform.md).
