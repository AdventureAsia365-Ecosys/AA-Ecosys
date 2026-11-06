---
id: OPS-02-staff-web-cutover
title: Move the staff frontends from Vercel to ECS
description: "Bring up the two staff web services (CIS admin, Booking admin, one Fargate Spot service each), verify them through the shared ALB before any DNS change, then point aa-cis. and booking. at the ALB; rollback is the same switch back, or one Route 53 command when CI cannot wait."
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

Decision: [ADR 0019](../../adr/0019-b2b-only-ecosystem-model.md) d23 and its S271 amendment (staff frontends leave
Vercel, Dev first: CIS admin and Booking admin as one Fargate Spot service each behind the shared ALB, no CDN).
Linear AA-911.

What runs where:

| Piece | Where |
|---|---|
| Services `aa-cis-dev-admin` (container `cis-admin`, :3000) and `aa-booking-dev-admin` (`booking-admin`, :3001) | AA-CIS-Infra `modules/environment/staff_web.tf` |
| Wildcard certificate, host rules on the ALB :443 listener, DNS switch `staff_web_dns_on_ecs`, TTL window `staff_web_dns_switch_window`, apex switch `staff_web_apex_on_alb` | AA-CIS-Infra `accounts/aa365/staff_web_edge.tf`, `alb_rules.tf` |
| WAF: staff hosts out of `RateLimit1000`, own rule `StaffWebRateLimit` (5000 requests / 5 min / IP); `GeoBlockNonAllowed` applies to them | AA-CIS-Infra `modules/waf` |
| Secrets `aa-cis/dev/admin-web`, `booking/dev/admin-web` | filled by AA-CIS-Infra `tools/identity/staff_web_secret.py` |
| Image builds and deploys | `Deploy Admin Dev` in AA-CIS-App and in AA-Booking (each its own service) |

The host names do not change (`aa-cis.lumiguides.it.com`, `booking.lumiguides.it.com`), so Cognito callbacks, links
and bookmarks stay as they are. Until the switch, Vercel serves both hosts.

**WAF and the staff, decided before the flip.** On Vercel no rule of the ALB web ACL ever saw staff traffic. After
the switch it judges each browser's real IP:

- Rate: the staff hosts have their own limit (5000 requests per 5 minutes per IP, static chunks included), not the
  API-sized 1000. Staff behind one office NAT IP share it.
- Geo: kept on purpose. A browser whose IP (or VPN exit) is outside the allowed list (US, GB, AU, SG, VN, IN, JP,
  TH, NZ, CA) gets a 403 from the WAF. Staff on a VPN choose an exit in that list or switch the VPN off. Adding a
  country is a `geo_allowed_countries` PR in AA-CIS-Infra.
- "Staff blocked by the WAF" is a rollback trigger in section 3.

## 1. Bring the services up (once)

1. Infra apply in the order of AA-CIS-Infra `docs/implementation-notes/AA-911-staff-ecs.md` (bootstrap targets with
   the MFA admin profile, then the Terraform Apply workflow).
   Expect: no destroy in either plan; the TTL of `aa-cis.` and `booking.` goes to 60 (switch window). Verify:
   `aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-admin aa-booking-dev-admin --profile aa365-admin --region us-west-1 --query 'services[].[serviceName,status,desiredCount]' --output text`
   prints both `ACTIVE 0`, and `aws acm list-certificates --region us-west-1 --profile aa365-admin --query "CertificateSummaryList[?DomainName=='*.lumiguides.it.com'].Status" --output text`
   prints `ISSUED`. Abort: nothing serves traffic yet; fix the plan and re-apply.
2. `python3 tools/identity/staff_web_secret.py --apply` (AA-CIS-Infra, MFA admin).
   Expect: two lines `"action": "written"`. Verify: a re-run prints `"unchanged"` twice.
3. GitHub environment `dev` of AA-CIS-App and AA-Booking: variables `STAFF_WEB_ENABLED=true` and `STAFF_WEB_ALB_DNS`
   (the ALB DNS name: `aws elbv2 describe-load-balancers --names aa-cis-dev-alb --profile aa365-admin --region us-west-1 --query 'LoadBalancers[0].DNSName' --output text`).
4. Dispatch `Deploy Admin Dev` in each repo (independent; any order).
   Expect: each run ends "Deployed at desired count 0: scale the service to 1 and re-run to verify". Then scale both:
   `aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-admin --desired-count 1 --profile aa365-admin --region us-west-1`
   `aws ecs update-service --cluster aa-cis-dev-cluster --service aa-booking-dev-admin --desired-count 1 --profile aa365-admin --region us-west-1`
   and re-run both deploys (each verifies through the ALB). Verify: both runs green, `verify` job included.
   Abort: scale back to 0; Vercel still serves both hosts.

## 2. Verify through the ALB before the switch

Resolve the two names to the ALB on the test client only; nothing else changes.

```bash
ALB=$(aws elbv2 describe-load-balancers --names aa-cis-dev-alb --profile aa365-admin --region us-west-1 --query 'LoadBalancers[0].DNSName' --output text)
IP=$(getent ahostsv4 "$ALB" | awk 'NR==1{print $1}')
curl -s --resolve aa-cis.lumiguides.it.com:443:$IP https://aa-cis.lumiguides.it.com/api/healthz
curl -s --resolve booking.lumiguides.it.com:443:$IP https://booking.lumiguides.it.com/api/healthz
curl -s -o /dev/null -w '%{http_code}\n' -k --resolve other.lumiguides.it.com:443:$IP https://other.lumiguides.it.com/
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' --resolve lumiguides.it.com:443:$IP https://lumiguides.it.com/
```

Expect: `{"status":"ok","app":"cis-admin","sha":"<main sha>"}`, the same with `booking-admin`, `404` for any other
host (the listener default; the CIS API is never reached on :443) and `301 https://aa-cis.lumiguides.it.com/` for the
apex (the redirect rule, used once the apex moves in section 4).

Sign-in, a write and real browsing: Chromium started with
`--host-resolver-rules="MAP aa-cis.lumiguides.it.com <IP>, MAP booking.lumiguides.it.com <IP>"` (Playwright
`launch({ args: [...] })`, the E2E staff login of skill `aa-ui-verify`). Expect on both hosts: the managed login opens
on `staff-auth.lumiguides.it.com`, the callback lands back signed in, a page lists data, one harmless save answers
200 (a BFF write passes the same-origin check behind the ALB), sign-out returns to `/login`.

Then a realistic load from the one test IP, standing in for an office NAT: three tabs per app, open every list and
detail page of the admin nav (both apps) and leave them for 10 minutes so polling and prefetch run. Expect no 403
anywhere. Then read the WAF blocks of that window:

```bash
aws logs filter-log-events --log-group-name aws-waf-logs-aa-cis-dev --start-time $(( ($(date +%s) - 1800) * 1000 )) --filter-pattern '{ $.action = "BLOCK" }' --profile aa365-admin --region us-west-1 --query 'events[].message' --output text | grep -E 'aa-cis\.lumiguides|booking\.lumiguides' | grep -oE '"terminatingRuleId":"[A-Za-z0-9]+"' | sort | uniq -c
```

Expect: no line (the log keeps only acted-on requests). A `StaffWebRateLimit` count means the limit is too low for
real use: raise `staff_web_rate_limit` (AA-CIS-Infra PR) before the switch. Screenshots and the counts go to
`docs/audits/<date>-S<nnn>-staff-web-cutover/`. Abort: anything red keeps DNS on Vercel; fix and redeploy.

## 3. Switch DNS

1. Confirm the 60 s switch window has been live for at least 30 minutes (it is on from the first apply,
   `staff_web_dns_switch_window = true`): `dig +noall +answer aa-cis.lumiguides.it.com @$(dig +short NS lumiguides.it.com | head -1)` and the same for
   `booking.` show a TTL of 60 at the authoritative server. If not, apply the window first and wait
   30 minutes.
2. PR in AA-CIS-Infra: `staff_web_dns_on_ecs = true` in `accounts/aa365/terraform.tfvars`.
   Expect in Terraform Plan: exactly two in-place updates, `aws_route53_record.parity["aa-cis|CNAME"]` and
   `aws_route53_record.vercel_frontend["booking"]`, records -> the ALB DNS name. Nothing else.
3. Merge, then the Terraform Apply workflow.
4. Verify (both TTLs 60 s): `dig +short CNAME aa-cis.lumiguides.it.com` and `dig +short CNAME booking.lumiguides.it.com`
   print the ALB name; `curl -s https://aa-cis.lumiguides.it.com/api/healthz` answers `cis-admin` without `--resolve`
   (Vercel has no `GIT_SHA`, so its copy answers `"sha":"unknown"`); the CIS production UI smoke (`ui-smoke.yml`
   signed-in specs) and the Booking smoke pass on the real hosts.
5. WAF watch, 30 minutes after the switch and again the next working day: the blocked counts of the three IP rules,

   ```bash
   for r in RateLimit1000 StaffWebRateLimit GeoBlockNonAllowed; do echo "$r $(aws cloudwatch get-metric-statistics --namespace AWS/WAFV2 --metric-name BlockedRequests --dimensions Name=WebACL,Value=aa-cis-dev-waf Name=Region,Value=us-west-1 Name=Rule,Value=$r --start-time $(date -u -d '-24 hours' +%FT%TZ) --end-time $(date -u +%FT%TZ) --period 86400 --statistics Sum --profile aa365-admin --region us-west-1 --query 'Datapoints[0].Sum' --output text)"; done
   ```

   and the log query of section 2 for the two hosts (which rule, which country). Expect: no block on a staff host
   that a staff member caused. Sampled requests are also in the console (WAF, web ACL `aa-cis-dev-waf`, rule).

**Rollback triggers:** staff cannot sign in or save on either host; a staff member is blocked by the WAF
(`StaffWebRateLimit` or `GeoBlockNonAllowed` for a staff host) and the cause is not fixed within the hour (a VPN exit
can be changed at once; a limit or a country needs an AA-CIS-Infra PR).

**Rollback (normal):** `staff_web_dns_on_ecs = false`, merge, Terraform Apply; resolvers follow within 60 s. Vercel
keeps serving both hosts until the Vercel retirement below.

**Rollback (emergency, when CI or the apply window cannot wait),** MFA admin, one line:

```bash
ZONE=$(aws route53 list-hosted-zones-by-name --dns-name lumiguides.it.com --max-items 1 --query 'HostedZones[0].Id' --output text --profile aa365-admin) && aws route53 change-resource-record-sets --hosted-zone-id "$ZONE" --profile aa365-admin --change-batch '{"Changes":[{"Action":"UPSERT","ResourceRecordSet":{"Name":"aa-cis.lumiguides.it.com","Type":"CNAME","TTL":60,"ResourceRecords":[{"Value":"91b6470228dd7980.vercel-dns-017.com"}]}},{"Action":"UPSERT","ResourceRecordSet":{"Name":"booking.lumiguides.it.com","Type":"CNAME","TTL":60,"ResourceRecords":[{"Value":"faa59191f1f73e21.vercel-dns-017.com"}]}}]}'
```

The Vercel targets are the values in AA-CIS-Infra `dns.tf` (`aa-cis|CNAME`) and `custom_domains_variables.tf`
(`booking`). Then, before any other Terraform Apply (it would put the ALB back), the PR `staff_web_dns_on_ecs = false`.

## 4. After the switch

In this order:

1. AA-911 bridge retirement (CIS `POST /auth/booking-token` 404, Booking accepts only the WORKFORCE issuer, the
   booking JWT signing-key secret scheduled for deletion, the three bridge-era `booking.staff_users` rows linked or
   deactivated).
2. **Apex off Vercel, before any Vercel project goes.** The `aa-cis-frontend` project claims `lumiguides.it.com` and
   the apex A record points at Vercel; Cognito needs that A record for the `staff-auth.` and `auth.` custom domains,
   and an A record to Vercel with no project claiming it is a takeover risk (AA-CIS-Infra `dns.tf`). PR in
   AA-CIS-Infra: `staff_web_apex_on_alb = true` in `accounts/aa365/terraform.tfvars`. Expect in the plan: one in-place
   update of `aws_route53_record.apex` (records -> alias to the ALB). Merge, Terraform Apply. Verify:
   `curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' https://lumiguides.it.com/` prints
   `301 https://aa-cis.lumiguides.it.com/`, `dig +short A lumiguides.it.com` prints ALB addresses, and the managed
   login on `staff-auth.lumiguides.it.com` still opens. Only then remove the apex domain from the Vercel project.
3. Vercel retirement of `aa-cis-frontend` and `aa-booking-admin`: the `vercel-deploy.yml` workflows, the Preview hosts
   `aa-cis-preview.` / `booking-preview.` and their WORKFORCE clients, the `aa-booking-admin.vercel.app` callback, the
   Vercel secret rows of the register, and the Vercel rollback targets above.
4. Same AA-CIS-Infra PR as step 3 or after it: `staff_web_dns_switch_window = false` (TTLs back to 1800 s / 300 s).
