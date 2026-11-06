---
id: OPS-02-staff-web-cutover
title: Move the staff frontends from Vercel to ECS
description: "Bring up the staff web task (CIS admin + Booking admin in one Fargate Spot task), verify it through the shared ALB before any DNS change, then point aa-cis. and booking. at the ALB; rollback is the same switch back."
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-frontend, aa-booking-admin, aa-cis-infra]
last_reviewed: 2026-11-06
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: [OPS-02-vercel, OPS-02-ecs, AA-911]
---

# Move the staff frontends from Vercel to ECS

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.

Decision: [ADR 0019](../../adr/0019-b2b-only-ecosystem-model.md) d23 (staff frontends leave Vercel, Dev first: CIS
admin and Booking admin together in one Fargate Spot task behind the shared ALB, no CDN). Linear AA-911.

What runs where:

| Piece | Where |
|---|---|
| Task `aa-staff-dev-web`, containers `cis-admin` (:3000) and `booking-admin` (:3001) | AA-CIS-Infra `modules/environment/staff_web.tf` |
| Certificate, host rules on the ALB :443 listener, DNS switch `staff_web_dns_on_ecs` | AA-CIS-Infra `accounts/aa365/staff_web_edge.tf`, `alb_rules.tf` |
| Secrets `aa-cis/dev/admin-web`, `booking/dev/admin-web` | filled by AA-CIS-Infra `tools/identity/staff_web_secret.py` |
| Image builds and deploys | `Deploy Admin Dev` in AA-CIS-App and in AA-Booking |

The host names do not change (`aa-cis.lumiguides.it.com`, `booking.lumiguides.it.com`), so Cognito callbacks, links
and bookmarks stay as they are. Until the switch, Vercel serves both hosts.

## 1. Bring the task up (once)

1. Infra apply in the order of AA-CIS-Infra `docs/implementation-notes/AA-911-staff-ecs.md` (bootstrap targets with
   the MFA admin profile, then the Terraform Apply workflow).
   Expect: no destroy in either plan. Verify: `aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-staff-dev-web --profile aa365-admin --region us-west-1 --query 'services[0].[status,desiredCount]' --output text`
   prints `ACTIVE 0`. Abort: nothing serves traffic yet; fix the plan and re-apply.
2. `python3 tools/identity/staff_web_secret.py --apply` (AA-CIS-Infra, MFA admin).
   Expect: two lines `"action": "written"`. Verify: a re-run prints `"unchanged"` twice.
3. GitHub environment `dev` of AA-CIS-App and AA-Booking: variables `STAFF_WEB_ENABLED=true` and `STAFF_WEB_ALB_DNS`
   (the ALB DNS name: `aws elbv2 describe-load-balancers --names aa-cis-dev-alb --profile aa365-admin --region us-west-1 --query 'LoadBalancers[0].DNSName' --output text`).
4. Dispatch `Deploy Admin Dev` in one repo, then in the other.
   Expect: the first run ends "Registered only: waiting for the other app's first image"; the second registers both
   images. Then scale to one task:
   `aws ecs update-service --cluster aa-cis-dev-cluster --service aa-staff-dev-web --desired-count 1 --profile aa365-admin --region us-west-1`
   and re-run the second deploy (it verifies through the ALB). Verify: both runs green, `verify` job included.
   Abort: scale back to 0; Vercel still serves both hosts.

## 2. Verify through the ALB before the switch

Resolve the two names to the ALB on the test client only; nothing else changes.

```bash
ALB=$(aws elbv2 describe-load-balancers --names aa-cis-dev-alb --profile aa365-admin --region us-west-1 --query 'LoadBalancers[0].DNSName' --output text)
IP=$(getent ahostsv4 "$ALB" | awk 'NR==1{print $1}')
curl -s --resolve aa-cis.lumiguides.it.com:443:$IP https://aa-cis.lumiguides.it.com/api/healthz
curl -s --resolve booking.lumiguides.it.com:443:$IP https://booking.lumiguides.it.com/api/healthz
curl -s -o /dev/null -w '%{http_code}\n' -k --resolve other.lumiguides.it.com:443:$IP https://other.lumiguides.it.com/
```

Expect: `{"status":"ok","app":"cis-admin","sha":"<main sha>"}`, the same with `booking-admin`, and `404` for any other
host (the listener default; the CIS API is never reached on :443).

Sign-in and a write: Chromium started with
`--host-resolver-rules="MAP aa-cis.lumiguides.it.com <IP>, MAP booking.lumiguides.it.com <IP>"` (Playwright
`launch({ args: [...] })`, the E2E staff login of skill `aa-ui-verify`). Expect on both hosts: the managed login opens
on `staff-auth.lumiguides.it.com`, the callback lands back signed in, a page lists data, one harmless save answers
200 (a BFF write passes the same-origin check behind the ALB), sign-out returns to `/login`. Screenshots go to
`docs/audits/<date>-S<nnn>-staff-web-cutover/`. Abort: anything red keeps DNS on Vercel; fix and redeploy.

## 3. Switch DNS

1. PR in AA-CIS-Infra: `staff_web_dns_on_ecs = true` in `accounts/aa365/terraform.tfvars`.
   Expect in Terraform Plan: exactly two in-place updates, `aws_route53_record.dns_parity["aa-cis|CNAME"]` and
   `aws_route53_record.vercel_frontend["booking"]`, records -> the ALB DNS name. Nothing else.
2. Merge, then the Terraform Apply workflow.
3. Verify (TTL: `booking.` 300 s, `aa-cis.` 1800 s): `dig +short CNAME aa-cis.lumiguides.it.com` and
   `dig +short CNAME booking.lumiguides.it.com` print the ALB name; `curl -s https://aa-cis.lumiguides.it.com/api/healthz`
   answers `cis-admin` without `--resolve` (Vercel has no `GIT_SHA`, so its copy answers `"sha":"unknown"`); the CIS
   production UI smoke (`ui-smoke.yml` signed-in specs) and the Booking smoke pass on the real hosts.

Rollback: `staff_web_dns_on_ecs = false`, merge, Terraform Apply; resolvers follow within the TTL. Vercel keeps
serving both hosts until the Vercel retirement below.

## 4. After the switch

- AA-911 bridge retirement (CIS `POST /auth/booking-token` 404, Booking accepts only the WORKFORCE issuer, the
  booking JWT signing-key secret scheduled for deletion, the three bridge-era `booking.staff_users` rows linked or
  deactivated).
- Vercel retirement of `aa-cis-frontend` and `aa-booking-admin`: the `vercel-deploy.yml` workflows, the Preview hosts
  `aa-cis-preview.` / `booking-preview.` and their WORKFORCE clients, the `aa-booking-admin.vercel.app` callback, the
  Vercel secret rows of the register.
