---
id: OPS-02-staff-web-cutover
title: Move the staff frontends from Vercel to ECS
description: "Bring up the two staff web services (CIS admin, Booking admin, one Fargate Spot service each), verify them through the shared ALB before any DNS change, then point aa-cis. and booking. at the ALB; rollback is the same switch back, or one Route 53 command when CI cannot wait."
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-frontend, aa-booking-admin, aa-cis-infra]
last_reviewed: 2026-11-07
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
and bookmarks stay as they are. Until the switch, Vercel served both hosts.

> [!NOTE]
> **Status (07/11/2026, S272): every section is done.** Sections 1-3 ran in S271 (06/11/2026); section 4 ran in S271
> (step 1) and S272 (steps 2-4). Vercel no longer serves any staff host and both Vercel projects are retired, so the
> Vercel rollbacks below are history: a bad staff web deploy rolls back on ECS ([rollback-ecs](rollback-ecs.md) on
> `aa-cis-dev-admin` / `aa-booking-dev-admin`, or a revert on the app repo's `main`).

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

**Rollback to Vercel: retired (S272).** Until the Vercel retirement, the rollback was `staff_web_dns_on_ecs = false`
(or a one-line Route 53 UPSERT of the two CNAMEs back to their Vercel targets). Section 4 removed the switch, the
Vercel targets and both Vercel projects: a CNAME to a deleted Vercel project is a takeover risk, so **never** point
`aa-cis.` or `booking.` back at a `*.vercel-dns-*.com` target. Roll back a bad staff web deploy on ECS instead
([rollback-ecs](rollback-ecs.md)).

## 4. After the switch

In this order. Each step records what ran; the evidence is on Linear AA-911.

1. **Done (S271, 06/11/2026).** AA-911 bridge retirement: CIS `POST /auth/booking-token` answers 404 (CIS #1339
   deployed), Booking accepts only the WORKFORCE issuer (Booking #202), the three bridge-era `booking.staff_users`
   rows are linked or deactivated (AA-CIS-Infra #700 + #704 run-script: `deactivated 2, linked 1`,
   `active_unlinked=0`). The booking JWT signing-key secret is orphan-delete in the secrets register and is scheduled
   for deletion (7-day recovery window) with the S272 live steps.
2. **Done (S272, 07/11/2026). Apex off Vercel, before any Vercel project goes.** The `aa-cis-frontend` project claimed
   `lumiguides.it.com` and the apex A record pointed at Vercel; Cognito needs that A record for the `staff-auth.` and
   `auth.` custom domains, and an A record to Vercel with no project claiming it is a takeover risk (AA-CIS-Infra
   `dns.tf`). AA-CIS-Infra PR `staff_web_apex_on_alb = true` (plan: one in-place update of `aws_route53_record.apex`,
   records -> alias to the ALB), Terraform Apply. Verify:
   `curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' https://lumiguides.it.com/` prints
   `301 https://aa-cis.lumiguides.it.com/`, `dig +short A lumiguides.it.com` prints ALB addresses, and the managed
   login on `staff-auth.lumiguides.it.com` still opens. Only then the apex domain was removed from the Vercel project.
3. **Done (S272, 07/11/2026). Vercel retirement of `aa-cis-frontend` and `aa-booking-admin`.**
   - App PRs (AA-CIS-App, AA-Booking): `vercel-deploy.yml`, `frontend/vercel.json` (and Booking's
     `check_security_headers.sh`) deleted; the post-deploy UI smoke and the visual run moved to `Deploy Admin Dev`;
     the BFFs and the APIs no longer accept the Preview-only clients (default ids empty).
   - Every user of the Preview hosts moved to the production staff hosts: the signed-in UI smoke and the visual run
     (`ui-smoke.yml` / `visual.yml`, only `https://aa-cis.lumiguides.it.com` and `https://booking.lumiguides.it.com`),
     the Cognito E2E (`e2e-cognito.yml`, no `booking_base_url` input), the Playwright setup (`auth.setup.ts`, no viewer
     cap check) and the skills `aa-ui-verify` / `aa-ship`. Per-PR UI evidence is the required `Visual (next start)`
     check (ADR 0019 d23 R7), which needs no deployment.
   - AA-CIS-Infra PR: the Preview hosts `aa-cis-preview.` / `booking-preview.` (DNS), their WORKFORCE clients
     `cis-admin-preview` / `booking-staff-preview` (and managed login styles), the `aa-booking-admin.vercel.app`
     callback of `booking-staff`, the cut-over switch `staff_web_dns_on_ecs`, the apex switch and every Vercel target
     of a staff name. The two staff records moved to `staff_web_edge.tf` (moved blocks, never recreated).
   - Then the Vercel projects were deleted, the secret rows of the register flipped (orphan-delete -> deleted), the
     repo secrets `VERCEL_TOKEN` (AA-CIS-App, AA-Booking), `VERCEL_AUTOMATION_BYPASS_SECRET` (AA-CIS-App), the `e2e`
     environment secret `BOOKING_PREVIEW_BYPASS` (if present), the `preview-signin` branches, rulesets and labels
     removed, and the Vercel rollback targets of section 3 retired.
4. **Done (S272, 07/11/2026), same AA-CIS-Infra PR as step 3:** `staff_web_dns_switch_window = false` (TTLs back to
   1800 s / 300 s).
