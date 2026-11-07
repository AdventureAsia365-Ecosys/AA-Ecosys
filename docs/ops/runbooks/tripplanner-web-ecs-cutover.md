---
id: OPS-02-tripplanner-web-cutover
title: Move the TripPlanner frontend from Vercel to ECS
description: "Bring up the TripPlanner web service behind its CloudFront distribution and web ACL, verify it through CloudFront before any DNS change, then point tripplanner. at CloudFront; roll back with the same switch; retire Vercel last."
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-tripplanner, aa-cis-infra]
last_reviewed: 2026-11-07
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: [OPS-02-vercel, OPS-02-ecs, OPS-02-staff-web-cutover, AA-1038]
---

# Move the TripPlanner frontend from Vercel to ECS

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.

Decision: [ADR 0019](../../adr/0019-b2b-only-ecosystem-model.md) d23 and the S265 tech-lead decision recorded on
Linear AA-1038 (TripPlanner frontend on ECS Dev: one Fargate Spot task + CloudFront + a CLOUDFRONT-scope web ACL, about
13-15 USD a month; the Fargate and WAF cost yeses are given). Same shape as the
[staff web cut-over](staff-web-ecs-cutover.md), with a CDN and its own web ACL because TripPlanner is public.

What runs where:

| Piece | Where |
|---|---|
| Service `aa-tripplanner-dev-web` (container `web`, :3000, health `/api/health`), secret shell `tripplanner/dev/web`, the deploy role's web grant | AA-CIS-Infra `modules/environment/tripplanner_web.tf` |
| CloudFront distribution for `tripplanner.lumiguides.it.com`, web ACL `aa-tripplanner-dev-web` (us-east-1), ALB :80 host rule, DNS switch `tripplanner_web_dns_on_cloudfront`, TTL window `tripplanner_web_dns_switch_window` | AA-CIS-Infra `accounts/aa365/tripplanner_web_edge.tf`, `alb_rules.tf` |
| The CIS catalog purge target (`TRIPPLANNER_REVALIDATE_URL` of the CIS api and worker) | AA-CIS-Infra `modules/ecs`, set by the same switch |
| Secret values | AA-CIS-Infra `tools/identity/tripplanner_web_secret.py` |
| Image build and deploy | AA-TripPlanner-Web `Deploy Web Dev` (`.github/workflows/deploy-web-dev.yml`) |
| The app's edge settings | task env `TP_EDGE_GATE=on` (model calls only on their protected paths), `TP_CLIENT_IP_SOURCE=cloudfront` (per-IP limits on CloudFront-Viewer-Address); build value `NEXT_PUBLIC_TP_WAF_INTEGRATION_URL` (the planner's WAF token, from the repository variable `TP_WAF_INTEGRATION_URL`) |

The host name does not change (`tripplanner.lumiguides.it.com`), so links, the canonical URL, the Mapbox URL
restriction and the sitemap stay as they are. Until the switch Vercel serves the host and `vercel-deploy.yml` keeps
deploying it.

**The web ACL and travellers, decided before the flip.** BotID (Vercel) leaves with Vercel. The web ACL takes its place:

- `RateLimitPerIp`: 3000 requests per 5 minutes per viewer IP (pages, chunks and photos included) -> 429.
- `RateLimitModelPaths`: 100 per 5 minutes per IP on `GET /api/browse/search` and `POST /api/trip/narrate` -> 429.
- `ChallengePlanner`: a silent JavaScript Challenge on the two model paths and on a document navigation of a planner
  page (`/plan`, `/{tenant}/plan`). The planner gets its token from the web ACL's JavaScript integration
  (`challenge.js`, AA-TripPlanner-Web `lib/wafToken.ts`) in the background, however it was opened: most ways in (the
  header link, the home search, the tour and destination buttons) are client-side navigations that the rule never
  challenges. The integration also refreshes the token after its 4 hours. A call still challenged gets one refresh and
  retry, then one reload of the planner page (a document load the rule challenges: a short interstitial, no puzzle),
  then the "please reload" notice. A script without the token gets HTTP 202 with `x-amzn-waf-action: challenge` on the
  model paths. Home, destination and tour pages are never challenged. No geo rule.
- A traveller blocked by a rule, or a planner whose search or narration fails with a challenge, is a rollback trigger
  in section 3.

## 1. Bring the service up (once)

1. Root PR (this runbook + the secrets register rows) merged first.
2. AA-CIS-Infra PR merged, then the local MFA bootstrap step from `accounts/aa365` on main (the apply role cannot change
   its own policies): `terraform plan -target=aws_iam_policy.tf_apply_crm`, then `terraform apply` with the same target.
   Expect: one in-place update (a new policy version that adds the `aa-tripplanner-dev-web` repository). Nothing else.
3. Terraform Apply workflow (CI). Expect in the plan: creates for the web ACL, the distribution, the ALB rule, the
   security group, the ECR repository and its lifecycle policy, the secret shell, the log group, the execution role and
   its policy, the task definition, the target group, the service, the alarm and the deploy role's `app-deploy-web`
   policy; `aws_route53_record.vercel_frontend["tripplanner"]` has moved to `aws_route53_record.tripplanner_web[0]` with
   ttl 300 -> 60 and the Vercel target unchanged; the cache policy `aa-tripplanner-dev-web-photos` (the photo proxy's
   cache key carries `?v=`). No destroy. The distribution takes 5-15 minutes.
   Verify: `aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-tripplanner-dev-web --profile aa365-admin --region us-west-1 --query 'services[].[serviceName,status,desiredCount]' --output text`
   prints `ACTIVE 0`, and `aws cloudfront list-distributions --profile aa365-admin --query "DistributionList.Items[?Aliases.Items[0]=='tripplanner.lumiguides.it.com'].[Status,DomainName]" --output text`
   prints `Deployed` and the `*.cloudfront.net` name. Abort: nothing serves traffic yet; fix and re-apply.
4. `python3 tools/identity/tripplanner_web_secret.py --apply --sentry-dsn "<the TripPlanner web DSN>"` (AA-CIS-Infra,
   MFA admin; the DSN from Sentry, project of the TripPlanner web; empty switches Sentry off).
   Expect: one line `"action": "written"`. Verify: a re-run prints `"unchanged"`.
5. AA-TripPlanner-Web repository settings: variables `TP_WEB_ENABLED=true`, `TP_WEB_CLOUDFRONT_DNS` (the
   `*.cloudfront.net` name above) and `TP_WAF_INTEGRATION_URL` (`terraform output -json tripplanner_web_edge` from
   `accounts/aa365`, field `waf_integration_url`: an `https://….awswaf.com/…/` URL, public, every planner page loads
   `challenge.js` from it; the deploy refuses to build without it), secret `TP_MAPBOX_PUBLIC_TOKEN` (the public `pk.`
   token: the value the Vercel build inlines, read from the Mapbox account or the live bundle).
6. Merge the AA-TripPlanner-Web PR. `Deploy Web Dev` runs on main and ends "Deployed at desired count 0: scale the
   service to 1 and re-run to verify". Then:
   `aws ecs update-service --cluster aa-cis-dev-cluster --service aa-tripplanner-dev-web --desired-count 1 --profile aa365-admin --region us-west-1`
   and re-run the workflow (its `verify` job goes through the distribution). Verify: green, `verify` included.
   Abort: scale back to 0; Vercel still serves the host.

## 2. Verify through CloudFront before the switch

Resolve the host to the distribution on the test client only; nothing else changes.

```bash
CF=$(aws cloudfront list-distributions --profile aa365-admin --query "DistributionList.Items[?Aliases.Items[0]=='tripplanner.lumiguides.it.com'].DomainName" --output text)
IP=$(getent ahostsv4 "$CF" | awk 'NR==1{print $1}')
H=tripplanner.lumiguides.it.com
curl -s --resolve $H:443:$IP https://$H/api/health
curl -s -o /dev/null -D - --resolve $H:443:$IP https://$H/plan | grep -iE '^(HTTP|x-robots-tag|x-frame-options|x-amz-cf-id)'
curl -s -o /dev/null -D - --resolve $H:443:$IP "https://$H/api/browse/search?q=temple" | grep -iE '^(HTTP|x-amzn-waf-action)'
curl -s --resolve $H:443:$IP "https://$H/api/browse?resource=search&q=temple"
```

Also `curl -s --resolve $H:443:$IP https://$H/ | grep -c 'href="/tours/'` (not 0: the home renders the catalog, not
the "We couldn't load" state).

Expect: `{"status":"ok","service":"aa-tripplanner-web","version":"<manifest>","git_sha":"<main sha>"}`; `/plan` 200
with `x-robots-tag: noindex, nofollow`, `x-frame-options: DENY` and an `x-amz-cf-id` (CloudFront, not Vercel); the
model path `HTTP/2 202` with `x-amzn-waf-action: challenge`; the older spelling
`{"error":"use_protected_path"}` (404).

Model-path rate rule (one IP): `for i in $(seq 1 150); do curl -s -o /dev/null -w '%{http_code}\n' --resolve $H:443:$IP "https://$H/api/browse/search?q=x$i"; done | sort | uniq -c`,
wait 60 seconds, run one more request. Expect: 202 lines first, then 429 once the rule has counted the window (the last
request answers 429 with `{"error":"rate_limited"}`). The same IP is blocked on the model paths for up to 5 minutes.

Real browsing: Chromium started with `--host-resolver-rules="MAP tripplanner.lumiguides.it.com <IP>"` (Playwright
`launch({ args: [...] })`), a fresh browser context for each path (no `aws-waf-token` cookie carried over). Expect:
the home, a destination and a tour page render with photos. Then the planner, opened three ways, each in its own
fresh context and never by typing `/plan` first:
- the home page's search card ("Plan my trip") and the header's "Plan a trip" button;
- a tour page's "Customise this trip" button;
- `/plan` typed in the address bar.
On each: the map opens (Mapbox tiles load: the token's URL restriction names this host); a free-text search answers
with pins; adding a stop and "narrate" answer with text; the network panel shows `challenge.js` loaded from the
`awswaf.com` host and the two model calls answered 200 (never 202); no console error. `/aa-tripplanner/plan` (the demo
tenant) opens and searches the same way. A 202 on a model call, or the "We could not confirm this request came from
the planner page" notice, is a failure. Screenshots and the outputs go to
`docs/audits/<date>-S<nnn>-tripplanner-web-cutover/`.

WAF view of the test window (CloudWatch metrics, us-east-1 for a CLOUDFRONT web ACL):

```bash
for r in RateLimitPerIp RateLimitModelPaths ChallengePlanner; do echo "$r $(aws cloudwatch get-metric-statistics --namespace AWS/WAFV2 --metric-name BlockedRequests --dimensions Name=WebACL,Value=aa-tripplanner-dev-web Name=Rule,Value=$r --start-time $(date -u -d '-3 hours' +%FT%TZ) --end-time $(date -u +%FT%TZ) --period 10800 --statistics Sum --region us-east-1 --profile aa365-admin --query 'Datapoints[0].Sum' --output text)"; done
```

Expect: blocks only from the rate test above; sampled requests per rule are in the console (WAF, Global (CloudFront),
web ACL `aa-tripplanner-dev-web`). Abort: anything red keeps DNS on Vercel; fix and redeploy.

## 3. Switch DNS

1. Confirm the 60 s window: `dig +noall +answer tripplanner.lumiguides.it.com @$(dig +short NS lumiguides.it.com | head -1)`
   shows a TTL of 60 at the authoritative server (on since the first apply, `tripplanner_web_dns_switch_window = true`).
2. PR in AA-CIS-Infra: `tripplanner_web_dns_on_cloudfront = true` in `accounts/aa365/terraform.tfvars`.
   Expect in Terraform Plan: one in-place update of `aws_route53_record.tripplanner_web[0]` (records -> the
   `*.cloudfront.net` name) and new task definition revisions of the CIS api and worker that only add
   `TRIPPLANNER_REVALIDATE_URL=https://tripplanner.lumiguides.it.com/api/revalidate/catalog`. Nothing else.
3. Merge, then the Terraform Apply workflow. Then the next CIS deploy (the api and worker pick up the purge target; no
   job or wave running, as for any CIS deploy).
4. Verify: `dig +short CNAME tripplanner.lumiguides.it.com` prints the distribution name;
   `curl -s -D - -o /dev/null https://tripplanner.lumiguides.it.com/` shows `x-amz-cf-id` and no `x-vercel-id`;
   `curl -s https://tripplanner.lumiguides.it.com/api/health` answers the ECS commit; the next CIS `tripplanner_purge`
   job (admin job runner) succeeds against the new URL.
5. Watch, 30 minutes after the switch and the next working day: the metric loop of section 2 over the last 24 hours, the
   alarm `aa-tripplanner-dev-web-no-healthy-target`, the task's log group `/ecs/aa-tripplanner-dev-web` for 5xx.

**A photo withdrawn from the photos CDN** (same file path and `?v=`) stays in this distribution's `/photo-cdn/*` cache
until its max-age: the CIS photo purge invalidates the photos CDN only. Invalidate this distribution too, MFA admin:
`aws cloudfront create-invalidation --distribution-id <tripplanner_web_edge.distribution_id> --paths "/photo-cdn/<path>" --profile aa365-admin`
(the first 1,000 paths a month are free). A replaced photo needs nothing: it has a new `?v=`, which is in the cache key.

**Rollback triggers:** the planner does not load, search or narrate for a traveller; a traveller is blocked by a rule
without cause and it is not fixed within the hour (a limit is an AA-CIS-Infra variable PR); the task keeps failing its
health check.

**Rollback (normal):** `tripplanner_web_dns_on_cloudfront = false`, merge, Terraform Apply; resolvers follow within
60 s, and the CIS purge goes back to the Vercel host (the next CIS deploy). Vercel keeps serving the host until the
retirement below.

**Rollback (emergency, when CI or the apply window cannot wait),** MFA admin, one line (the target is
`tripplanner_web_vercel_target` in AA-CIS-Infra `tripplanner_web_edge.tf`):

```bash
ZONE=$(aws route53 list-hosted-zones-by-name --dns-name lumiguides.it.com --max-items 1 --query 'HostedZones[0].Id' --output text --profile aa365-admin) && aws route53 change-resource-record-sets --hosted-zone-id "$ZONE" --profile aa365-admin --change-batch '{"Changes":[{"Action":"UPSERT","ResourceRecordSet":{"Name":"tripplanner.lumiguides.it.com","Type":"CNAME","TTL":60,"ResourceRecords":[{"Value":"a1520bcb29624260.vercel-dns-017.com"}]}}]}'
```

Then, before any other Terraform Apply (it would put CloudFront back), the PR `tripplanner_web_dns_on_cloudfront = false`.

## 4. After the switch: retire the Vercel project (a separate, approved step)

At least one working day after the switch, with the watch of section 3 clean. In this order:

1. AA-TripPlanner-Web PR: remove `vercel-deploy.yml` and the BotID / `@vercel/functions` code paths (`botid`,
   `dangerouslyDeleteByTag`, `addCacheTag` are no-ops off Vercel), point `visual.yml` and `post-deploy-verify.yml`
   (app `web`) at `https://tripplanner.lumiguides.it.com`, change the privacy page's hosting line (Vercel -> Amazon
   Web Services, CloudFront), and update `CONTEXT.md`.
2. AA-CIS-App PR: the purge job's default URL (`services/jobs/tripplanner_purge_job.py` `DEFAULT_URL`) becomes the
   public host, so the CIS env is no longer needed for it.
3. Remove the domain from the Vercel project, then delete the project `aa-tripplanner` (Vercel dashboard or connector;
   the tech lead approves the delete).
4. AA-CIS-Infra PR: the record always points at the distribution (drop `tripplanner_web_dns_on_cloudfront` and
   `tripplanner_web_vercel_target`: a CNAME to Vercel with no project claiming the host is a takeover risk) and close
   the window (`tripplanner_web_dns_switch_window = false`, TTL 300).
5. Root PR: the `vercel:aa-tripplanner` rows of the secrets register and GitHub AA-TripPlanner-Web `VERCEL_TOKEN` ->
   **orphan-delete** then **deleted**; `tripplanner/dev/web` and `TP_MAPBOX_PUBLIC_TOKEN` -> **keep**; the
   [Vercel rollback runbook](rollback-vercel.md) loses its TripPlanner part (no Vercel project left).
6. Cost Done-when of AA-1038: a Cost Explorer read of the first days after the move and a monthly forecast.
