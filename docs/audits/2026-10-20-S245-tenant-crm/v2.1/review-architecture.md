# Tenant CRM v2: independent review, ARCHITECTURE + OPS + COST + DEV-FIRST lens

Date 20/10/2026 (S245, round 3). Reviewer: Claude Code subagent. Read-only: no repo, AWS, Vercel, Linear or Jira
writes and no paid API calls. The only AWS calls were three free read-only ones (`ec2 describe-subnets`,
`cloudfront list-distributions`, `route53 list-hosted-zones`). Web pages and the AWS price-list JSON were read on
20/10/2026.

**Inputs read in full:** `owner-input.md`, `owner-approvals-r2.md` (round-2 answers override the design),
`docs/research/partner-crm-spec.md`, `out/crm-design-v2.md` (cited as "v2"), `out/crm-questions.json`,
`out/crm-01-current-state.md` ("scout"), `out/crm-judges.md` ("panel").

**Code snapshots:** AA-CIS-Infra `4824c81`; AA-Booking `f4fb80d`; AA-CIS-App `origin/main` @ `446dcfc5` (v2 cited
`b7e6da66`; the lines I use did not move). Every Infra path below is under `infra/AA-CIS-Infra/`.

**Approved inputs this review builds on:**
- N3 = b: the agency app runs as a Fargate container behind CloudFront.
- D12 and D22 changed: the CRM keeps its own LLM log and its own job runner, and CIS ops can observe both over HTTP.
- H1 = b and H4 = c: real agencies come only after all 23 modules, and synthetic agencies are used first.
- Owner direction: run on Dev as early as possible, with no prod cell until real agencies arrive.

---

## 0. Verdict

1. **N3 b cannot be built as v2 assumes.** v2 puts a Fargate container behind CloudFront Free with WAF included for $0.
   - CloudFront flat-rate **Free and Pro do not include "Private origins within VPC"**. Only Business ($200) and
     Premium ($1,000) include it.
   - VPC origins need a load balancer **in a private subnet**. The shared ALB is internet-facing.
   - Its security group admits only :80 from the VPC.
   - Its regional WAF ACL geo-blocks every country outside 10.

   A working path exists at about $0 on Dev: CloudFront **pay-as-you-go** → VPC origin → the **existing internal VPC-link NLB**
   (it already has a security group, and it sits in usw1-az1 and usw1-az3, which are supported) → ALB listener rule →
   web target group. See F1.
2. **Take the prod cell, the paid vendor plans and the external verification clocks off the critical path.** A first
   end-to-end slice can run on Dev with synthetic agencies in **about 3 sessions** (§2). Under v2 the first Dev demo
   came after W1–W3.
3. **The connection budget in v2 uses the wrong metric.** The binding rule is the C2.2 worst-case pool total, which must
   stay at or under 75 % of `max_connections` (135). The sum of LOGIN limits against 181 is not the rule. Today the
   total is ~126, so a CRM pool of 5 breaks the ceiling. Use a pool of 3 with a limit of 6. See F4.
4. **The Terraform apply role cannot create a CloudFront distribution, a VPC origin or CRM ECR repos today.** Granting
   that is a bootstrap that Nghiệp applies locally with MFA. It is step 0 of the slice. See F3.
5. **BFF traffic should stay inside the VPC.** Route it through the internal NLB, not public API Gateway hops through
   the single t4g.nano NAT instance. See F5.
6. **PR previews can be ephemeral in CI on `localhost:3004`.** That callback is already registered. There is no need
   for a fixed preview host. See F6.
7. **SES:** v2's "1 receipt rule per agency" stops at 199 agencies. That quota is hard (200 rules per set, not
   adjustable). Use one domain-wide rule. See F7.
8. **D12/D22 monitoring:** CIS already has the app registry for this (AA-884). Add a SigV4-protected ops feed. Do not
   reuse TripPlanner's "write into `shared.llm_call_log`" pattern. See F8.
9. **Dev cost with N3 b, dev-first:** about **$11–15/month** in November, rising to about **$15–19/month** from
   January. The worst case, with no Spot capacity, is about $28–32. v2's prod-cell $27 and Documenso $250–3,000/year
   are deferred until real agencies arrive. See §3.

---

## 1. Findings (most severe first)

| # | Severity | Finding | Changes |
|---|---|---|---|
| F1 | **Critical** | N3 b origin path: CloudFront Free has no VPC origins, the ALB is public and geo-filtered, and :443 defaults to CIS | Decision (origin path), cost (+$0 Dev, WAF $7–8 later), schedule (spike) |
| F2 | **High** | Prod cell, paid vendors and verification clocks sit on the pre-Dev critical path | Schedule (−8 to −10 issues before the first Dev run), cost (−$27/month −$250/month until real agencies), decision |
| F3 | **High** | The apply role lacks CloudFront and CRM ECR grants; inline-policy and managed-policy headroom is tight | Schedule (bootstrap step 0, needs Nghiệp's MFA) |
| F4 | **High** | Connection budget: wrong metric, and CRM pool 5 overshoots the C2.2 ceiling | Decision (N17 changes), cost $0 |
| F5 | Medium-High | BFF → CIS/CRM via public API Gateway hairpins through the NAT instance and breaks per-client throttles | Design; cost $0 |
| F6 | Medium | A fixed preview host is fragile; ephemeral CI previews on `localhost:3004` are free | Schedule (−1 to −2 issues), decision |
| F7 | Medium | SES: one rule per agency hits the 200-rule hard quota; the rule set is CIS-owned | Design; cost $0 |
| F8 | Medium | D12/D22 "CIS observes CRM" needs a defined HTTP contract and auth, not DB access | Schedule (+2 small issues), decision (contract) |
| F9 | Medium | Lazily created per-agency KMS keys live outside Terraform | Design; Dev cost −$1–2 with cleanup |
| F10 | Medium | Next 16 on Fargate: size, session cookie vs WAF size rules, host routing, Server Actions origin check | Cost (+$1.5/month for 1 GB), spike scope |
| F11 | Medium | ARM64 images need GitHub ARM runners (free only while the repo is public) | Decision (keep AA-Partner public) |
| F12 | Low-Med | Deploy gates, DB Migrate owner registration and two-image CI/CD are under-counted | Schedule (+1 issue) |
| F13 | Low | Spot-only Dev: no on-demand fallback | None (runbook) |
| F14 | Low | ECS exec off on Dev slows debugging for no privacy gain (synthetic data) | Decision (Dev on, prod off) |
| F15 | Low | Stale Infra comment: the apply role already has `apigateway:SetWebACL` | None (v2's N14 rationale is partly stale) |
| F16 | Low | The slice should not wait for the portal to leave Vercel: use new Dev hostnames first | Schedule (decouples) |
| F17 | Low | Documenso on Dev: CI-only container plus a Dev stub; never on the shared RDS | Cost $0, C2.2 safe |

### F1 (Critical): The N3 b origin path in v2 does not exist; this one does

**What v2 says.**
- "CloudFront gói Free ($0/tháng: 1M request, 100 GB, 5 rule WAF)" (v2:211-216).
- "Dự phòng … Fargate sau cùng CloudFront, +≈ $8/tháng" (v2:216; `crm-questions.json:226`).
- N3 b was approved on that basis.

v2 never names the origin path from CloudFront to the container.

**Evidence.**

- **The flat-rate plan matrix lists "Private origins within VPC" for Business and Premium only.** Free and Pro have no
  tick ([flat-rate plans guide](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/flat-rate-pricing-plan.html),
  feature table; [pricing page](https://aws.amazon.com/cloudfront/pricing/): "Private origins within VPC — Free: Not
  included, Pro: Not included"; Business $200, Premium $1,000; both read 20/10/2026).
- **Free and Pro also lack "custom origin request rules", logging and header-based WAF rules.** Free is limited to
  5 cache behaviors, 5 WAF rules and **3 Free plans per account**.
- **VPC origins require "Application Load Balancers … in private subnets"**
  ([VPC origins guide](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html)).
  - The shared ALB is `internal = false` in public subnets (`modules/alb/main.tf:11-16`).
  - Its SG admits only :80 from the VPC CIDR (`modules/vpc/main.tf:257-272`).
- **A plain public-origin path to that ALB is harmful.** It would have to open :443 to the CloudFront prefix list.
  - The :443 listener's default action forwards to the **CIS API target group** (`modules/alb/main.tf:92-104`), so any
    CloudFront distribution could reach CIS directly.
  - The shared regional ACL on the ALB (`modules/waf/main.tf:197-201`) applies the per-IP rate rule and
    **GeoBlockNonAllowed** (`:156-183`, allow-list `modules/waf/variables.tf:20-25`) to whatever source IP arrives.
  - Behind CloudFront that source is a CloudFront edge or regional-cache IP. All travellers share a few rate buckets,
    and a traveller served from a Frankfurt or Paris cache is geo-blocked.
- **The internal VPC-link NLB already has a security group** (`modules/alb/vpc_link.tf:9-41`). It is a TCP :80
  listener whose target is the ALB (`:59-79`). VPC origins accept "Network Load Balancers" with a security group and
  without TLS listeners (VPC origins guide, "Origin restrictions").
  - Its private subnets are in **usw1-az1 and usw1-az3** (read-only `describe-subnets`, 20/10/2026).
  - VPC origins exclude only usw1-az2 in us-west-1 (same guide, region table).
- **Pay-as-you-go CloudFront charges nothing for origin fetches from AWS origins, VPC origins included.** The
  always-free tier covers 1 TB out and 10 M HTTPS requests a month
  ([pay-as-you-go pricing](https://aws.amazon.com/cloudfront/pricing/pay-as-you-go/), 20/10/2026). VPC origins have
  "no additional cost" ([launch note](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-cloudfront-vpc-origins)).
- **Traffic arriving through the NLB still passes ALB ACL rule 1 (CommonRuleSet, enforced).** Then rule 2
  `VpcLinkInternalAllow` (`vpc_allow_cidr = var.vpc_cidr`, `accounts/aa365/main.tf:262-269`) lets it past the rate
  and geo rules. That is exactly the behaviour we want: content inspection, no geo-block.
- **No CloudFront distribution exists on acc2 yet** (`list-distributions` → none). The Route 53 zone holds 28 records.

**Fix: choose O2 below. Spike it in S0.**

| Option | Path | Dev $/month | Prod-ready? | Verdict |
|---|---|---|---|---|
| **O2 (recommend)** | CloudFront **pay-as-you-go** → **VPC origin = existing internal NLB** (:80) → ALB HTTP listener rule (host header `partner-dev.` / `go-dev.` + CloudFront origin custom header) → web target group → Fargate ARM task | **≈ $0** (always-free tier; ≤ $0.2 without it). WAF optional: a CLOUDFRONT ACL with rate + CommonRuleSet, no geo ≈ $5 + $2 + $0.60/M ≈ **$7–8** | Yes. Streaming SSR, default 30 s origin timeout (adjustable), Host forwarded with the managed `AllViewer` policy, full Terraform (`aws_cloudfront_vpc_origin`) | Fewest moving parts. Only shared touches: one NLB SG ingress rule (from `CloudFront-VPCOrigins-Service-SG`) and one ALB rule (Booking precedent) |
| O1 | CloudFront **Free** → API Gateway **HTTP API** → VPC link v2 → ALB :80 rule → web target group | $0 incl. 5 WAF rules; HTTP API $1.17/M | Limits: 30 s integration timeout, 10 MB payload, **10,240 bytes of request line + headers** (cookies count), no streaming ([HTTP API quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html)). Host cannot be forwarded to execute-api, so a CloudFront Function must copy it. The plan subscription may be outside Terraform: CloudFormation has `AWS::PricingPlanManager::Subscription`, and I found no Terraform resource (unverified) | Fallback only |
| O3 | CloudFront → the public ALB on :443 with the prefix list | $0 | Changes the shared ALB default action, SG and ACL (geo + rate exception); CIS blast radius | Reject |
| O4 | New internal ALB or NLB for the web app | +$16–18 (ALB-hour, estimate) | Yes | Reject (cost) |
| O5 | CloudFront Business plan with a VPC origin | $200 | Yes | Reject |

**Consequences to write into the design.**
- **WAF.** O2 on Dev runs without a CloudFront ACL. Protection comes from Shield Standard, the ALB CommonRuleSet
  (already enforced) and an in-app rate limit. The in-app limit is keyed on the `CloudFront-Viewer-Address` header,
  which the managed `AllViewerAndCloudFrontHeaders-2022-06` policy forwards.
  - Add the CLOUDFRONT-scope ACL (≈ $7–8/month, **no geo rule**) when the first real agency is onboarded, or on Dev now
    if Nghiệp wants parity.
  - This replaces v2's N14 a ("WAF trong CloudFront Free, $0"): $0 WAF only exists on the Free plan, and that plan
    cannot reach the container privately.
- **Static assets.** Next standalone serves `/_next/static/*` itself. A CloudFront cache behavior with the managed
  `CachingOptimized` policy caches it, so there is **no S3 bucket and no OAC** (v2:211-213 had "File tĩnh lên S3").
  [Next `output` docs](https://nextjs.org/docs/app/api-reference/config/next-config-js/output): `server.js` serves
  `public` and `.next/static` once they are copied into the standalone folder.
- **Cost line.** The v2 Dev line "Portal Lambda + CloudFront Free ~0,5" (v2:485) becomes "web Fargate task" (F10) plus
  "CloudFront PAYG ≈ $0".

**Does it change cost?** Dev: no. Pilot later: WAF ≈ $7–8 instead of the $0 or $15 v2 assumed. **Schedule:** the S0
spike must prove the path (½ session). **Decision:** this changes v2's N3 a/b wording and v2's N14 a.

### F2 (High): Dev-first: remove the prod cell and the paid external items from the critical path

**v2 puts all of these before the first agency run:**
- `envs/prod` + `aa-crm-prod-db` + the C7.2a exception + the DB Migrate `environment` input + a restore drill (v2:633, 562-572);
- Documenso plan selection (v2:719);
- "khởi động việc ngoài" in W0: Meta Tech Provider, Stripe Connect, Google verification for `gmail.send`, Microsoft
  publisher, insurer (v2:628);
- the second public-path service before the 11th agency (v2:401, N15).

The owner's round 2 (H1 = b, H4 = c, "no prod cell until real agencies after all 23 modules") makes all of these
non-blocking for Dev.

**Evidence.**
- C7.1a allows synthetic data on Dev (`docs/architecture/data-standards/03-scaling.md:364`), so nothing in the
  standards forces a prod cell before real data.
- For external integrations, the free sandboxes are enough for synthetic agencies:
  - Google: an OAuth app in "Testing" status works, with refresh tokens "expiring in 7 days"
    ([Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2), 20/10/2026). That is fine for scripted
    synthetic mailboxes; verification is needed only for real agencies.
  - Stripe test mode, Meta Cloud API test numbers and a Twilio trial need no paid plan. These are not re-verified
    here; they follow v2 §8.
  - Documenso can run as a self-hosted container in CI (panel X2).

**Fix.**
- Delete from the pre-Dev path: W5 prod-cell items (≈ 4 issues), the W0 external-start items (they become "start when
  Ms. Thư decides", see §6), the Documenso plan choice, N15 and the DPA/public data page (legal, Ms. Thư).
- Park them in a **"Go-real" wave** gated on Ms. Thư naming the first real agency.

**Changes.**
- Schedule: about −8 to −10 issues before the first Dev demo.
- Cost: −$27/month (cell) and −$250/month (Documenso) until real agencies; Documenso is billed yearly.
- Decision: N4 and N8 become "deferred, not decided now".

### F3 (High): The Terraform apply role cannot create what N3 b needs; bootstrap first

**Evidence.**
- **CloudFront.** The apply role (`aa-cis-infra-tf-apply`) has only `cloudfront:UpdateDistribution`, for Cognito custom
  domains (`accounts/aa365/cicd_split.tf:683-689`). There is no `CreateDistribution`, `CreateVpcOrigin`,
  `CreateFunction`/`PublishFunction` or tagging.
- **Service-linked role.** A VPC origin needs CloudFront's service-linked role. No `iam:CreateServiceLinkedRole` grant
  exists for it.
- **ECR.** Repo creation is scoped to `aa-booking-<env>-*` (`accounts/aa365/cicd.tf:303-323`). CRM needs
  `aa-crm-dev-api` and a web repo.
- **Headroom.**
  - The role already has **10 managed policies**, the default per-role quota (`cicd_split.tf:536-543`).
  - All inline statements share one **10,240-character** limit; AA-846 narrowed them to make room (`cicd.tf:38-49`).
  - These lists are bootstrap objects "applied locally with the MFA admin profile" (`cicd.tf:16-20`).
- **What is already covered.**
  - ACM in us-east-1 (`cicd_split.tf:625-634`) and the `us_east_1` provider (`accounts/aa365/versions.tf:57-63`).
  - WAFv2 create/associate on `*` (`cicd.tf:160-183`) and Route 53 (`cicd_split.tf:613-620`).
  - ALB listener rules on `aa-cis-dev-alb` (`cicd.tf:340-358`).
  - CRM role names: the `aa-*-dev-*` pattern (`cicd_split.tf:60-63`).

**Fix: issue S0-a "apply-role bootstrap for CRM + CloudFront".**
- One customer-managed policy `aa-cis-infra-tf-apply-crm`:
  - CloudFront distribution, VPC origin, function and tag verbs on `*` (no resource-level ARNs before creation);
  - `iam:CreateServiceLinkedRole` conditioned on `iam:AWSServiceName = vpcorigin.cloudfront.amazonaws.com` (verify the
    exact service name in the spike);
  - ECR manage on `aa-crm-${env}-*`.
- Attaching it needs the IAM quota "managed policies per role" raised from 10 to 20. That is adjustable and free.
  Alternatively, fold two AWS-managed attachments.
- Nghiệp applies it locally with MFA, as for AA-811/AA-816.
- **Schedule:** blocking for S0 (½ session plus Nghiệp's MFA). **Cost:** $0.

### F4 (High): The connection budget: the rule is C2.2 worst case ≤ 135, not LOGIN limits ≤ 181

**What v2 says.** "`crm_app` limit 5, pool `max_size=5`; bù bằng hạ `booking` 15 → 10 … tổng LOGIN giữ 155/181"
(v2:194; N17).

**Evidence.**
- Data standard README rule 10: "**The connection budget stays ≤ 75 % of `max_connections`** and lives in Part C C2.2"
  (`docs/architecture/data-standards/README.md:98`).
- C2.3c: "the sum of `max_size × max processes` … MUST be ≤ that limit, and the C2.2 total MUST be ≤ 75 %"
  (`03-scaling.md:154`).
- C2.2 re-checked 16/10: ceiling ≈ 135, total ~126, "any pool increase needs an offsetting cut"
  (`03-scaling.md:125,139`).
- The Booking row in C2.2 already budgets pool 5 × 2 processes = 10 against a target limit of 10. Lowering the limit
  from 15 to 10 does **not** free any pool budget.
- A CRM pool of 5 × 2 (deploy overlap at `deployment_maximum_percent = 200`, the Booking pattern at `booking.tf:404-405`)
  adds 10, giving ~136 against the ceiling of 135.

**Fix.**
- `crm_app` CONNECTION LIMIT **6**, pool `min_size=0, max_size=3`, giving a worst case of 6 and a total of ~132.
- Fail-fast acquire ≤ 5 s (C2.3g) and a pool-level `statement_timeout` (C2.3f).
- Add a C2.2 row and a `rds_role_connection_limits` row (`accounts/aa365/observability_ecosys.tf:59-72`) in the same PR.
- The web container holds **no** DB connection (BFF only). A Documenso database never goes on the shared RDS (F17).
- Keep the Booking 15 → 10 alignment if wanted, but as hygiene, not as the CRM's budget source.
- **Cost:** $0 (no resize). **Decision:** change N17 a's text.

### F5 (Medium-High): BFF traffic: use the internal NLB, not public API Gateway through the NAT instance

**What v2 says.** "BFF → Bearer / HMAC → GW → API" and BFF → `api-cis` (v2:141-142); the client IP goes in an
HMAC-signed header "vì sau BFF mọi khách cùng một IP egress" (v2:436-437).

**Evidence.** On Fargate in private subnets, every BFF call to `api-crm.`/`api-cis.` leaves through the **single
t4g.nano NAT instance** and comes back through API Gateway:
- the NAT instance: `modules/vpc/main.tf:160-165`;
- "there are no VPC endpoints": `accounts/aa365/app_security_groups.tf:9-11`.

That adds two public hops, puts all agencies behind one NAT IP for per-IP throttles, and uses the REST throttle 20/40
of a Booking-style API.

The internal NLB is already the in-VPC entry to the ALB:
- `internal = true`, SG admits :80 from the VPC CIDR (`modules/alb/vpc_link.tf:14-20,34-38`);
- ALB rules route `/booking*` today (`booking.tf:356-360`), the default goes to CIS, and `/crm*` would go to CRM;
- ALB ACL rule 2 already allows VPC-sourced traffic.

**Fix.**
- The BFF calls `http://<internal NLB DNS>/v1/...` (CIS) and `/crm/v1/...` (CRM), with the Cognito bearer.
- The client IP comes from `CloudFront-Viewer-Address`, signed by the BFF.
- Keep a public `api-crm` REST API only for webhooks (Stripe, Meta, Documenso) and for staff/S2S calls (F8). Webhooks
  are not needed in the first slice.
- The NLB DNS name is a config value; it is not committed to the public repo.
- **Cost:** $0. Removes a NAT dependency from the hot path. Not a decision, a design correction.

### F6 (Medium): Previews: ephemeral in CI, not a fixed `portal-pr.` host

**What v2 says.** "một host preview cố định `portal-pr.lumiguides.it.com` … CI deploy PR đang test lên đó"
(v2:217-219).

**Evidence.**
- The `cis-portal` client already registers `http://localhost:3004/api/auth/callback/cognito`
  (`accounts/aa365/identity_variables.tf:163-168`).
- A fixed host means last-writer-wins across PRs, one more DNS record, callback and ACM SAN, plus a second always-on
  task or a deploy race.

**Fix.**
- The PR job builds both ARM images and runs `docker compose` on a GitHub ARM runner: web on :3004, api, and an
  ephemeral `postgres` service with `crm-NNN` migrations applied.
- A KMS stub stays behind the `KeyProvider` interface (CI only, never Dev).
- Content pages read Dev CIS with the e2e tenant.
- Playwright signs in through the Dev EXTERNAL pool with a synthetic `e2e-test-*` user and runs the UI smoke.
- Dev = `main` only.
- **Changes:** −1 to −2 issues, $0, no Cognito, DNS or ACM churn. The CloudFront distribution count stays at one.

### F7 (Medium): SES inbound: one domain-wide rule, and move the rule set out of "e2e"

**What v2 says.** "Mỗi đại lý một địa chỉ … là 1 rule trong rule set SES đang active duy nhất" (v2:447).

**Evidence.**
- SES receiving quotas: **200 rules per rule set, not adjustable**, and 500 recipients per rule
  ([SES quotas](https://docs.aws.amazon.com/ses/latest/dg/quotas.html), 20/10/2026). v2 sizes to 200 agencies, and the
  set already holds the e2e rule.
- The active set is `aa-cis-dev-e2e`, tagged `App = cis` / AA-816 (`accounts/aa365/e2e_mailbox.tf:47-60`). "Destroying
  this resource deactivates receiving for the whole region" (`:200-205`). The file itself says a future use must add
  its rule "to THIS set" (`:20-21`).

**Fix.**
- One CRM rule whose recipient is the domain `in.crm.<zone>`. It writes to an S3 bucket encrypted with one CRM inbound
  KMS key, with a 1-day lifecycle.
- `crm_mail_ingest` routes by the local part (agency slug + trip token), re-encrypts into the vault, then deletes the
  raw object.
- Move the rule-set and activation resources to a `ses_inbound.tf` tagged `App = shared` with `moved` blocks: same
  name, no recreate.
- Write down the residual: raw inbound mail sits for minutes under the CRM inbound key, not the agency key.
- **Cost:** $0. Removes a hard scale ceiling.

### F8 (Medium): D12/D22 changes: CIS monitors CRM jobs and LLM spend over HTTP

**Evidence.**
- CIS already has `api/core/app_registry.py` (AA-884). It probes Booking only over its **public** health URLs and reads
  TripPlanner's LLM spend from `shared.llm_call_log`, "a CIS table TP writes" (`origin/main:api/core/app_registry.py:1-20,54-68`).
- The CRM cannot use the TP pattern, because there are no grants to or from `crm.*` (D2).
- CIS job runner today: `GET /admin/job-runner/summary` (`api/routers/admin_job_runner.py:7`).

**Fix: a versioned contract `ops-feed.v1`, served by the CRM on `api-crm`. Booking can adopt it later.**
- `GET /crm/ops/v1/summary` returns: job counts per kind × status, oldest queued age, worker heartbeat age, running
  SHA, and the deploy-gate state. No payloads and no tenant names.
- `GET /crm/ops/v1/llm-usage?from&to` returns: per day × model × stage, tokens, cost, calls, and a pseudonymous tenant
  hash.
- API Gateway method auth is **`AWS_IAM`**. The CIS task role gets `execute-api:Invoke` on those two resources only.
- CIS adds a `crm` `AppInfo` with health and the feed; the admin Jobs and Platform pages render it read-only.
- Optional (verify on acc3): tag an application inference profile `App = crm` so that Cost Explorer separates CRM
  Bedrock spend on acc3.

**Changes:** +1 CRM issue, +1 CIS issue, +1 Infra line, at $0. **Decision:** approve `ops-feed.v1` as the cross-app
observability contract.

### F9 (Medium): Per-agency KMS keys created at runtime need guardrails and cleanup

**Evidence.** D7 a with lazy creation (v2:399) means the CRM task role calls `kms:CreateKey`. That call cannot be
resource-scoped. The workload boundary does not deny KMS (`cicd_split.tf:117-140`). These keys exist outside Terraform
and outside the per-App budget unless they are tagged at creation.

**Fix.**
- The identity policy allows `kms:CreateKey`/`TagResource` only with `aws:RequestTag/App = crm` and
  `aws:TagKeys` ⊆ {App, crm_tenant}.
- `kms:CreateAlias` only on `alias/crm/*`. `kms:BypassPolicyLockoutSafetyCheck` is false.
- The key policy keeps an account-admin statement so that no key becomes unmanageable.
- A Dev cleanup job schedules deletion of synthetic agencies' keys after 7 days idle. Keys pending deletion are not
  billed ([KMS pricing](https://aws.amazon.com/kms/pricing/), per panel §1.2).
- **Cost:** Dev KMS ≈ $2–3 instead of $3–5.

### F10 (Medium): Next 16 on Fargate ARM: what the spike must prove

**Evidence and fix.**
- **Size.** Use **0.25 vCPU / 1 GB ARM**. The 1 GB covers `sharp` for image optimisation plus SSR.
  - On-demand: 0.25×0.03725×730 + 1×0.00409×730 = **$9.78**.
  - Spot is about $2.9–3.9 (estimate; AWS says "up to 70 %").
  - Prices: AWS price list `AmazonECS/current/us-west-1`, published 2026-10-19T22:43Z (`USW1-Fargate-ARM-vCPU-Hours`
    0.03725, `-ARM-GB-Hours` 0.00409).
  - Drop to 0.5 GB only if the spike measures RSS < 350 MB.
  - v2's "+≈ $8" equals 0.25/0.5 GB on-demand ($8.29).
- **Session.** Keep Cognito tokens **server-side**; the cookie carries only an opaque id.
  - The ALB CommonRuleSet blocks cookie headers over 10,240 bytes (`SizeRestrictions_Cookie_HEADER`,
    [AWS managed rules](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-baseline.html)).
  - Three Cognito tokens in cookies get close to that.
  - (O1 would also hit the HTTP API's 10,240-byte header cap.)
  - Store sessions in `crm.web_session`, reached through the CRM API, so that the web task stays DB-free.
- **Host routing.** With O2 and `AllViewer`, the viewer Host reaches `proxy.ts` unchanged. Still, build Cognito
  `redirect_uri` from configured public base URLs, never from `request.nextUrl`. The portal has no Server Actions today
  (`git grep "use server" origin/main -- portal` = none). If CRM forms add them, configure the allowed origins.
- ⚠️ **This contains underscore env vars — edit manually in VSCode.** The web image needs the build-time public config,
  the session secret, the Cognito client secret, the Server Actions encryption key (if used) and the internal API base
  URL. Nghiệp sets these by hand; the agent does not generate scripts for them.

### F11 (Medium): ARM64 CI needs the repo public

**Evidence.**
- Booking builds x86 on `ubuntu-latest` (AA-Booking `.github/workflows/deploy-dev.yml:115,143`).
- Linux arm64 hosted runners (`ubuntu-24.04-arm`) are free on **public** repos and unavailable on private repos on the
  standard plan ([GitHub runners reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners);
  [changelog 2025-01-16](https://github.blog/changelog/2025-01-16-linux-arm64-hosted-runners-now-available-for-free-in-public-repositories-public-preview/)).
- Fargate Spot supports Graviton ([ECS announcement 2024-09](https://aws.amazon.com/tw/about-aws/whats-new/2024/09/amazon-ecs-graviton-based-spot-compute-fargate/)).

**Fix.**
- Keep AA-Partner public (as v2 says). Build natively on `ubuntu-24.04-arm`, not with QEMU.
- If the repo ever goes private, build x86 instead: about +25 % Fargate, roughly +$2–3 on Dev on-demand.
- A public repo means account IDs, ARNs, the NLB DNS and distribution IDs stay in repo **variables**, never in code
  (CLAUDE.md DM-6.10).

### F12 (Low-Med): CI/CD and deploy gates are under-counted for two images and a new DB owner

**Evidence.**
- Adding an owner touches 6+ mirrored places: `db/owners.yaml`, `db/run_migration.py` (including
  `IDLE_EXEMPT_KINDS`), `check_migration_copies.py`, `db-migrate.yml`, `isolation_probe.py`, plus a `roles/` file and
  `migrator_member_of` (`db/owners.yaml:4-20,49-52`).
- The DB Migrate idle check reports every `<schema>.job` (`.github/workflows/db-migrate.yml:21`), so `crm.job`
  periodic kinds must be exempt from day 1.
- The Booking OIDC trust uses the immutable subject with a repo-id wildcard until the id is known (`booking.tf:65-84`).

**Fix.**
- **One Infra issue for the owner registration**, separate from `crm.tf`.
- **Two deploy workflows with path filters:**
  - `deploy-api` runs the deploy gate (OIDC audience `aa-crm-deploy-gate`, copied from Booking `deploy-dev.yml:15-35`);
  - `deploy-web` is not gated (stateless);
  - order: api before web when the contract changes.
- Two ECR repos with **IMMUTABLE git-SHA tags** (`booking.tf:86-93` pattern), keeping 10 images each.
- A GitHub `dev` environment with a `main`-only branch policy (possible because the repo is public).
- **Schedule:** +1 issue.

### F13 (Low): Spot-only Dev has no fallback

A `FARGATE_SPOT`-only strategy does not fall back to on-demand when Spot capacity is short. Booking uses on-demand
base 1 (`booking.tf:392-401`). This is acceptable on Dev. Add a runbook line: switch the strategy to `FARGATE` base 1
when tasks stay PENDING for more than 15 minutes. That switch costs about +$6 per service at on-demand.

### F14 (Low): ECS exec

v2 turns exec off on the CRM service (v2:192). On Dev the data is synthetic, so keep exec **on**. That allows the
canonical S3-mediated pattern and a faster slice. Turn it off in the future prod root (Go-real wave). **Decision:**
"Dev exec on, prod off".

### F15 (Low): Stale Infra comment

`accounts/aa365/variables.tf:198-205` and `main.tf:272-277` say the CI role lacks `apigateway:SetWebACL`. The apply
role has it (`cicd_split.tf:586-590`, Sid `APIGatewaySetWebACL`). v2's N14 rationale (v2:433) is half stale: the
geo-block is the real blocker. Fix the comment in any Infra PR you are already making.

### F16 (Low): Do not wait for the portal migration

`portal.lumiguides.it.com` stays on Vercel until the 101-file move and AA-813 are done (v2:283-292). The slice uses
**new Dev hosts**, `partner-dev.<zone>` and `go-dev.<zone>`. Their callbacks are added to the `cis-portal` client
(`identity_variables.tf:163-168`) or to a new EXTERNAL client, both free. `portal.` flips to CloudFront when the
content studio pages move in. After that the Vercel project `aa-cis-portal` is retired, and Vercel is no longer used
for the agency app.

CIS admin and Booking admin stay on Vercel Hobby. That is N19 and not part of this lane.

### F17 (Low): Documenso on Dev

The self-hosted Documenso runs **only as an ephemeral CI container** for adapter contract tests. Dev uses an `esign`
stub adapter that emits the same webhook and a placeholder signed PDF.

A persistent Documenso on Dev would need its own Postgres database and role. Prisma's pool would add connections and
break C2.2 (F4), and it would add another always-on task (+$3–10/month).

---

## 2. Smallest end-to-end vertical slice on Dev, then the order after it

**Slice goal:** "a synthetic agency user signs in, a traveller submits the intake form, a CRM job processes it, and the
trip appears on the agency board". It runs on Dev, behind CloudFront, with the identity fields encrypted under that
agency's KMS key, and with the CRM jobs visible from CIS.

It exercises every platform seam: CloudFront and the VPC origin, the web task, Cognito, BFF → CRM in the VPC, CRM API,
`crm.job`, a DB owner and role through DB Migrate, KMS, both deploy pipelines and the CIS ops feed.

The slice does not touch the portal move, AA-813, Booking B2B or any vendor.

| Step | Repo | Content | Exit (evidence) |
|---|---|---|---|
| **S0-a** (bootstrap, Nghiệp MFA) | Infra | F3 policy + IAM quota request | `terraform plan` of S0-c is clean under the apply role |
| **S0-b** (spike, ½ session) | scratch + Infra | O2 path with a hello container: `aws_cloudfront_vpc_origin` → NLB SG rule → ALB host+header rule (priority after Booking's 100) → ARM target group; Next 16 standalone hello (`proxy.ts` host routing, SSR stream) | `curl https://partner-dev.…/` 200 through CloudFront; same via `go-dev.`; streaming chunked; ALB CommonRuleSet sees the traffic; no geo block from a non-allow-listed country (test through a VPN) |
| **S0-c** | Infra `crm.tf` (copy of `booking.tf`) | 2 ECR repos (IMMUTABLE), log groups, 2 task definitions ARM64 (api 0.25/0.5, web 0.25/1), 2 services on FARGATE_SPOT with circuit breaker, own SGs (+ RDS ingress for the api SG only), `/crm*` and host rules, secrets (no values), deploy role OIDC, us-east-1 ACM + Route 53 aliases, budget `crm` | Services exist at desired 0 (Booking pattern) |
| **S0-d** | Infra db | Owner `crm` registration (F12), `roles/rl-NNN` (`crm_owner` NOLOGIN, `crm_app` LIMIT 6), C2.2 row, alarm row | DB Migrate check-mode green |
| **S1-a** | AA-Partner (new, public) | Repo, CI (lint, type, unit, build ×2 on `ubuntu-24.04-arm`, compose smoke), import-boundary test, deploy workflows ×2 | First image SHAs in ECR |
| **S1-b** | AA-Partner api | FastAPI skeleton, health/ready, Cognito EXTERNAL JWT, `crm.member` from a **synthetic fixture** (interface for the later AA-813 feed), `crm-001` (agency, member, traveller vault columns, profile, trip, job, access_event), runner copy from Booking + deploy gate + `ops-feed.v1` summary, `KeyProvider` with lazy per-agency KMS + DEK (F9 conditions) | DB Migrate apply; `/crm/health` 200; heartbeat in `crm.job` |
| **S1-c** | AA-Partner web | Cognito code flow with a server-side session, BFF allow-list → internal NLB, intake form on `go-dev.`, board page on `partner-dev.`, EN/VI frame | Playwright on Dev: synthetic user → board; intake → trip in Inquiry < 1 min; DB dump shows ciphertext only |
| **S1-d** | CIS + Infra | `crm` AppInfo (health + `ops-feed.v1` via SigV4), Invoke grant | CIS admin shows CRM job counts |

The slice is about 10 issues, about 2.5–3 sessions, plus Nghiệp's MFA bootstrap. That is the earliest point where
"the CRM runs on Dev".

**Order after the slice (Dev, synthetic agencies, spec phase order, prod-free):**

| Wave | Content | Note |
|---|---|---|
| D1 Privacy foundation | F1 full (blind index, `reveal()`, audit hash chain, documents bucket), F2 roles, F3 scrubber (Guardrails spike acc2/acc3), F4 RLS + role UI, F5 audit page | Spec "privacy before traveller data" (`partner-crm-spec.md:21,199`). Synthetic data only, so it runs in parallel with D2 |
| D2 Sell a trip | Modules 1, 2, 15, 6 (agency lines), 4, 16 basic, the event baseline; module 5: one SES domain rule (F7) + Gmail in Testing mode | Matches spec Phase 1 |
| D3 Portal move + separation | L1–L8, C1–C5, P1–P3, B3 first, `portal/` → AA-Partner, AA-813 ×3, flip `portal.` to CloudFront, retire Vercel `aa-cis-portal` | v2 §4 unchanged; can run in a parallel lane after S1 |
| D4 AA supply + proposal | Booking B2B (6–7 issues, Booking lane), modules 3 and 6 (AA lines), builder copy | The longest pole; start the Booking lane right after S1 |
| D5 Get paid + deliver | Modules 7 (Stripe **test**), 11, 12 (**stub/CI Documenso**), 13, 8 (AA-ops key), 18 part | No paid vendor |
| D6 Automate | Modules 9 (Meta test number; SMS = BYO Twilio trial), 10, Messenger/IG | Meta verification only in Go-real |
| D7 AI + insights + hardening | Module 14 (Haiku, cap), 16 full, 17 (k≥10), 18 full, load test, SLO | |
| **Go-real** (gated on Ms. Thư) | Prod root/cell, CLOUDFRONT WAF ACL ($7–8), ECS exec off, second public-path service, vendor plans and verifications, DPA, data page | Off the critical path (F2) |

---

## 3. Dev cost, month by month (N3 b, dev-first, no prod)

Unit prices are as used above, read 20/10/2026. Fargate ARM is from the AWS price list. The Spot discount is an
**estimate** (60–70 %). The CloudFront PAYG always-free tier is assumed **not** guaranteed under TrueIDC billing, so it
is shown as ≤ $0.2.

| Line | Nov 2026 (slice + D1) | Dec (D2–D4) | Jan → (D5–D7, steady) | Basis |
|---|---|---|---|---|
| CRM api 0.25/0.5 ARM Spot | 2.5–3.3 | 2.5–3.3 | 2.5–3.3 | on-demand $8.29 |
| Web 0.25/1 GB ARM Spot | 2.9–3.9 | 2.9–3.9 | 2.9–3.9 | on-demand $9.78 |
| CloudFront PAYG + VPC origin | ≤ 0.2 | ≤ 0.2 | ≤ 0.2 | [PAYG page](https://aws.amazon.com/cloudfront/pricing/pay-as-you-go/): origin fetch from AWS origins free; $0.085/GB, $0.01/10k HTTPS |
| CloudWatch Logs (2 services, 14–30 d) + ~5 alarms | 1–2 | 1–2 | 1–2 | estimate |
| ECR (2 repos, ≤ 10 images each) | ≤ 0.6 | ≤ 0.6 | ≤ 0.6 | $0.10/GB-month |
| Secrets (DSN, web session/Cognito, provider JSON) | 1.2 | 1.2 | 1.2 | 3 × $0.40 |
| KMS (AA-ops + inbound + 1–3 synthetic agencies, F9 cleanup) | 2–3 | 3–4 | 3–4 | $1/key-month |
| Guardrails corpus (from D1) | 0.3 | 0.7 | 0.7 | v2 §9.2 |
| SES in/out, S3, `api-crm` REST at Dev volume | ≤ 0.3 | ≤ 0.5 | ≤ 0.5 | estimate |
| Haiku test (cap) | 0 | 0 | ≤ 2 | cap set by us |
| RDS, NAT, ALB, NLB, cluster, Cognito | 0 | 0 | 0 | shared, already paid; C2.2 fits (F4) |
| Documenso, Stripe test, Meta test, Twilio trial, Google Testing | 0 | 0 | 0 | F2, F17 |
| **Total** | **≈ $11–15** | **≈ $12–16** | **≈ $15–19** | |
| Worst case (no Spot: both services on-demand) | +12.6 → ≈ $24–28 | ≈ $25–29 | ≈ $28–32 | |
| Optional CLOUDFRONT WAF ACL on Dev | +7–8 | +7–8 | +7–8 | $5 ACL + $1/rule + $0.60/M |

**Compared with v2** (Dev ≈ $11–13 with a Lambda portal, plus the approved N3 b +$8 ≈ $19–21):
- this plan is ≈ $4–6 cheaper at steady state, because the web task runs on Spot;
- it also drops v2's prod-cell $27/month and Documenso $250/month (yearly commitment) until real agencies.

There is no cost lever in merging web and api into one task: Fargate pricing is linear, and merging would couple the
two deploys.

---

## 4. Decisions for Nghiệp (technical; these change or refine round-2 answers)

| # | Decision | Recommend |
|---|---|---|
| R1 | N3 b origin path | **O2**: CloudFront pay-as-you-go + VPC origin on the existing internal NLB. O1 (Free plan + HTTP API) is the fallback |
| R2 | WAF on Dev | Off on Dev (ALB CommonRuleSet + in-app rate limit). CLOUDFRONT ACL without geo at Go-real (≈ $7–8/month) |
| R3 | Prod cell, N15, Documenso plan, external verifications | Deferred to a Go-real wave, off the critical path |
| R4 | N17 wording | `crm_app` limit 6, pool 3, C2.2 row in the same PR |
| R5 | Previews | Ephemeral compose in CI on `localhost:3004`; no `portal-pr.` host |
| R6 | SES inbound | One domain rule + rule set moved to `App = shared` |
| R7 | CIS observability | `ops-feed.v1` (jobs + LLM usage), API Gateway `AWS_IAM`, CIS app registry row |
| R8 | ECS exec | Dev on, prod off |
| R9 | Slice-first hosts | `partner-dev.` / `go-dev.` now; `portal.` flips at the D3 portal move |

---

## Questions for Ms. Thư

None of these blocks the Dev slice. Each one is needed only before the matching Go-real step.

1. **Vendor accounts and which AA entity owns them.**
   - The Stripe platform account (Connect), the Meta developer/business app (WhatsApp Tech Provider), the Google Cloud
     OAuth app (`gmail.send`), the Microsoft publisher registration, and the Documenso and Twilio accounts each need a
     legal owner.
   - Dev can use free test modes. But even test accounts are registered under an AA entity: which entity, and who holds
     the logins?
2. **When to start the external verification clocks.**
   - Meta business verification takes 2–4 weeks (spec §10). Google app verification for `gmail.send` and Microsoft
     publisher verification also take time.
   - Real agencies come only after all 23 modules (H1 b). Should these start when she names the first real agency, or
     earlier, so they are ready in time?
3. **The e-sign vendor and plan, at go-real.** Documenso Teams ($480/year, possible Documenso branding) or Platform
   ($3,000/year, white-label), or another provider. Dev and CI use a free self-hosted test container and a stub, so
   nothing is needed now.
4. **The traveller-facing domain for real agencies.** Dev uses `go-dev.lumiguides.it.com`, which is a test domain. The
   brand and domain travellers will see, and per-agency custom domains if wanted, are her call before go-real.
5. **Paid protection at go-real.** A web firewall on the traveller pages costs about $7–8/month. It is technical, but
   it is a recurring cost on a "free for partners" product (H2 d, plan synced with the tenant-portal plan). She should
   confirm that AA carries it.
6. **The AWS reseller (TrueIDC).** If AWS free allowances or new CloudFront features turn out to be restricted under
   TrueIDC billing (as Bedrock is on acc2), can we contact TrueIDC through her? It affects only cents on Dev.
