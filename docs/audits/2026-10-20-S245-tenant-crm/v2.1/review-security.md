# Tenant CRM v2: independent review, lens SECURITY + DATA ISOLATION + AUTH

Date: 20/10/2026 (S245, round 3). Agent: Claude Code (independent reviewer subagent). This is a read-only review:
no repo, AWS, Vercel, Linear or Jira change, and no paid API call. The only network reads were public AWS
documentation and pricing pages, all accessed 20/10/2026.

**Inputs read in full:**
- `.tmp-session/s245-r2/owner-input.md` (round 1);
- `.tmp-session/s245-r2/owner-approvals-r2.md` (round 2). Where it differs from the design, round 2 wins: N3 = b
  (a Fargate container behind CloudFront), D12 changed, D22 changed, H1 = b (synthetic agencies first, Dev as early
  as possible);
- the spec, `docs/research/partner-crm-spec.md`;
- `out/crm-design-v2.md` ("design"), `out/crm-questions.json`, `out/crm-01-current-state.md` ("scout") and
  `out/crm-judges.md` ("panel").

**Code read at:**

| Repo | Ref |
|---|---|
| AA-CIS-Infra | `4824c81` |
| AA-CIS-App | `origin/main` (`git show` / `git grep`) |
| AA-Booking | `f4fb80d` |
| root | `f8a9938` |

Each finding cites the file and line I re-read myself. I do not rely on the design's own citations.

**Scope of the verdicts.** Engineering decides only technical matters. Wording promised to agencies, retention
promises, support access policy and vendor choices are listed at the end as questions for Ms. Thư.

---

## 0. Summary

The design gets the big shape right. The prod cell keeps real PII off Dev, cross-app reads go over HTTP, the
scrubber passes fail closed, and module 8 stays in the CRM. But six things would make the main privacy promise in
the spec untrue as built: "No access outside the agency, AA included" (spec F1, `partner-crm-spec.md:113`).

| # | Severity | One line | Changes cost / schedule / decision |
|---|---|---|---|
| S1 | **Critical** | The KMS design does not stop acc2 admins from decrypting, and the IAM statement as written does not work | $0; +1 issue W2; **H3 wording again** (Ms. Thư) |
| S2 | **High** | CRM access is decided by CIS membership, which AA staff control | $0; +1–2 issues W1; decision (owner) |
| S3 | **High** | The prod cell trusts Dev: same Cognito pool and client, a shared preview host, the CIS Dev feed and the shared ALB | $0; +1 issue W1/W5; decision (ADR 0006 amendment, owner) |
| S4 | **High** | "AWS_IAM between services" is bypassable: every VPC workload reaches the ALB/NLB directly | $0; +1 issue W1 |
| S5 | **High** | N3 = b (Fargate behind CloudFront) has no safe origin path designed yet | $0 if the VPC-origin spike passes, else ≈ +$18/month (estimate); +1 spike W0 |
| S6 | **High** | Guardrails facts the scrubber design misses; the acc3 role contradicts D12 ("us. only") | $0; +1 issue W2 (acc3 Terraform) |
| S7 | Medium | D12/D22 monitoring feeds: auth, payload and cost attribution are unspecified | $0; folds into W1/W7 |
| S8 | Medium | Audit log: volume, per-tenant hash-chain contention, no tamper anchor | ≈ $0; +1 issue W2 |
| S9 | Medium | Per-traveller DEK means one KMS call per reveal; crypto-shred is bounded by backups | ≈ $0–2/agency-month; deletion promise (Ms. Thư) |
| S10 | Medium | Inbox data (raw MIME, bodies, attachments) is outside F1; HTML email can carry XSS; per-agency SES rules do not scale | +$1/month; +1 issue W3 |
| S11 | Medium | RLS on `crm.*` vs the cross-tenant worker, `crm.job` and the ops/insights reads | $0; inside W1/W2 |
| S12 | Medium | Agency sign-in is single factor (email code), MFA OFF, 7-day refresh | $0; decision (owner) + UX question (Ms. Thư) |
| S13 | Medium | Traveller link/OTP tokens leak through URLs; one origin serves every agency | $0; inside W3/W5 |
| S14 | Medium | N15 "public path = Encrypt-only" cannot verify BYO-Twilio webhooks | $0; design note |
| S15 | Medium | The module 8 ops page in Booking admin passes plaintext PII through Vercel | $0; +0–1 issue W5 |
| S16 | Low–Med | JWT secret separation needs an explicit rule and sequencing | $0 |
| S17 | Low–Med | Secrets: the inventory is under-counted, prod/Dev scoping is missing, deploy roles need env-scoping | +≈ $2–3/month per env |
| S18 | Low | Logs become the PII leak path once ECS exec is off | ≈ cents/month at Dev |
| S19 | Low | Webhook tenant mapping and SES reputation coupling | $0 |

**Net effect:**
- **Cost.** Dev rises by ≈ $3–5/month: secrets, one ingest KMS key and log data protection. The ALB line (≈ $18,
  estimate) is added only if the S5 spike fails.
- **Schedule.** ≈ +7 issues, mostly W1–W2. They sit before any synthetic-agency data, so they fit the owner's
  "Dev as early as possible" order.
- **Decisions for the owner:** S2 (where CRM membership lives), S3/S12 (prod client and pool, MFA) and S5 (origin path).

---

## 1. Findings

### S1 — Critical: "only the CRM can use the agency key" is not true as designed

**Evidence**

1. **The default key policy.** A KMS key created with the default policy has the statement "Enable IAM User
   Permissions" for the account root. That lets any principal whose IAM policy allows `kms:*` decrypt. acc2's
   admin role is used for everything, and the design keeps Dev and the prod cell in the **same account**
   (design §10.1). Nothing in the design names a key policy template.
2. **The IAM statement.** The design writes the task role grant as "`kms:Decrypt/GenerateDataKey` on
   `alias/crm/*`" (design §3.3, IAM row). AWS: "You cannot use a key id, alias name, or alias ARN to identify a KMS
   key in an IAM policy statement … use the `kms:RequestAlias` or `kms:ResourceAliases` condition keys"
   ([KMS: keys in IAM policies](https://docs.aws.amazon.com/kms/latest/developerguide/cmks-in-iam-policies.html),
   20/10/2026). As written, the statement grants nothing. The likely "fix" during implementation is a wildcard,
   which grants everything.
3. **Lazy key creation by the app.** The design creates keys lazily from the app (N11). Without a template, the
   app's role would also need `PutKeyPolicy` or an equally broad right.
4. **The proven pattern is not reused.** The repo already solved the same problem for the break-glass secret: an
   explicit `Deny` for every principal except one, plus an EventBridge alarm on CloudTrail reads
   (`accounts/aa365/identity_alerts.tf:1-35`, `:52-74`). The CRM keys should follow it.
5. **The H3 sentence is still too strong.** H3 as approved says "Nhân viên AA không mở được hồ sơ khách"
   (`crm-questions.json` H3). An acc2 admin can change a key policy, register a task definition that runs as the
   CRM task role, or re-enable ECS exec on the service. The real guarantee is "not without leaving an alarm and an
   agency-visible record".

**Fix**

- **Key policy template**, one per agency key, in code and reviewed. It has three statements:
  - (a) **Use.** Allow `Encrypt`, `Decrypt`, `GenerateDataKey*` and `ReEncrypt*` to the env's CRM task role only,
    with the condition `kms:EncryptionContext:crm_tenant_id` = that tenant.
  - (b) **Administer.** Allow key-admin actions (`Describe*`, `Get*`, `List*`, `TagResource`, `PutKeyPolicy`,
    `ScheduleKeyDeletion`, `CancelKeyDeletion`, `EnableKey`, `DisableKey`) to the account root. That avoids a
    lockout, and it does **not** include any cryptographic action.
  - (c) **Deny.** An explicit `Deny` of `Decrypt`, `ReEncrypt*`, `GenerateDataKey*` and `CreateGrant` for every
    principal whose `aws:PrincipalArn` is not the CRM task role or the CRM break-glass role. This is the same
    shape as the `identity_breakglass` secret policy.
- **IAM on the task role.**
  - Resource `arn:aws:kms:us-west-1:<acct>:key/*`, with condition
    `ForAnyValue:StringLike kms:ResourceAliases = alias/crm-<env>/*` and `kms:EncryptionContextKeys` required.
  - Use separate alias prefixes `alias/crm-dev/` and `alias/crm-prod/`, so the Dev role can never touch a prod key.
  - `kms:CreateKey` and `kms:CreateAlias` are allowed with `aws:RequestTag/App = crm` and
    `kms:BypassPolicyLockoutSafetyCheck = false`.
  - **Never** `PutKeyPolicy`, `ScheduleKeyDeletion` or `DisableKey`. Offboarding and crypto-shred is a destructive
    op: it runs from an ops path with a DRY RUN (`skill/aa-cis-schema/references/destructive-ops.md`).
- **Nightly drift check.** `GetKeyPolicy` on every `alias/crm-*` key, diffed against the template, with an alarm on
  any difference.
- **Alarm.** One EventBridge rule (`ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`, same as
  `identity_alerts.tf:1-35`) on KMS `Decrypt` events for `alias/crm-*` keys by a principal other than the CRM role.
  The same rule also catches `PutKeyPolicy`, `CreateGrant`, `ScheduleKeyDeletion` and `DisableKey` on those keys,
  and `ecs:UpdateService` / `ExecuteCommand` / `RegisterTaskDefinition` on the CRM service. It goes to SNS **and**
  to a small SQS queue that a `crm_*` job reads, writing an **agency-visible** `access_event` ("AA emergency
  access"). That is what makes spec F5 hold for AA itself.
- **Break-glass.** See §2.
- **Wording.** Change the H3 sentence again (question Q1 for Ms. Thư).

**Changes:** cost $0 (rules, one SQS queue). Schedule +1 issue in W2 (template, drift check, alarm). Decision: H3
wording.

### S2 — High: AA staff control who can read an agency's travellers

**Evidence**
- ADR 0006: "The **membership table is the security boundary** for tenants". The table lives in CIS
  (`docs/adr/0006-ecosystem-identity.md:139-150`), and the invitation flow runs in the CIS API (`:400`).
- The EXTERNAL pre-sign-up trigger says the same: "tenant membership in the CIS database is the security boundary"
  (`lambda_src/identity_triggers/external.py:92-95`).
- The design mirrors that membership into `crm.member_mirror` and maps it to CRM roles (design §7.1, F4 row §5).
- So anyone who can write CIS membership can grant themselves an agency role in the CRM: CIS admin staff, the CIS
  task role, or the CIS Dev master in break-glass. That breaks spec F1 ("AA included", `partner-crm-spec.md:113`)
  and §2 ("Traveler data belongs to the agency").

**Fix**
- **CRM is the authority for CRM roles.** `crm.member_role` (owner/agent/assistant) is written only by the CRM API,
  on an action of an existing agency **owner**.
- **The CIS feed may only remove or suspend.** It can deactivate a person (deny wins). It can **never** create or
  raise a CRM role.
- **Bootstrapping the first owner.** The first owner of a new agency is created once, at onboarding, before any
  traveller exists, and it shows in that agency's audit log from day one.
- **Every role change** writes an agency-visible `access_event` and emails the agency's owners.
- **Alarm on EXTERNAL-pool admin calls.** Extend the AA-816 EventBridge pattern (`identity_alerts.tf` item 4,
  WORKFORCE `AdminCreateUser`) to the EXTERNAL pool: `AdminSetUserPassword`, `AdminUpdateUserAttributes`,
  `AdminLinkProviderForUser`, `AdminCreateUser` and `AdminAddUserToGroup`. An admin who changes an agency user's
  email or password can sign in as that person, so this must alert.
- **AA-813 scope.** The CIS allow-list for the EXTERNAL pool is already minimal (`ADR 0006:129-130`), so keep it.

**Changes:** cost $0. Schedule +1–2 issues in W1 (role-grant API, deny-only feed semantics, EXTERNAL admin
alarms). Decision (owner): "CRM roles are agency-owned; CIS membership only gates the content studio and can only
revoke CRM access."

### S3 — High: the prod cell's trust is anchored in Dev

**Evidence**
- There is **one EXTERNAL pool**, `aa-external-<env>`, with `env = dev`. Its `cis-portal` client is confidential.
  It has callbacks `https://portal.lumiguides.it.com/...` **and** `http://localhost:3004/...`
  (`identity_variables.tf:163-167`), and refresh tokens of 168 h (`identity.tf:169-171`).
- The design keeps the prod cell on this pool and client: "User đại lý vẫn ở Cognito EXTERNAL (`aa-external-dev`)"
  (design §10.1). It also registers a **fixed PR preview host** on the same client (design §3.4, X6).
- One managed-login session covers every EXTERNAL client (`ADR 0006:148-150`). So:
  - a preview build of any PR silently receives a real agency user's token;
  - that token is valid against the prod cell API;
  - the prod cell also takes its membership and catalog from **CIS Dev** (design §10.1, "App khác" row);
  - Dev workloads share the VPC and ALB with it (S4).
- The panel judged B-2 only as an availability issue (panel §2.3). It is also an integrity issue.

**Fix ($0)**
- **A prod-only app client** (e.g. `partner-prod`). Its callbacks are the prod host only: no localhost and no
  preview host. The prod CRM API accepts **only** that `client_id`. Copy the Booking verifier, which already pins
  `client_id` and `token_use` (`AA-Booking/backend/app/auth/identity_config.py:5-6,54-55`).
- **Preview and Dev** stay on `cis-portal` (renamed `partner-dev`). Their API never accepts the prod client.
- **Better: a separate partner pool** (e.g. `aa-partner-prod`) with stronger sign-in (S12). It is free under the
  shared 10k MAU (`ADR 0006:427-429`). It also removes the "travellers and agents in one pool" ambiguity, since
  TripPlanner travellers can sign in through any EXTERNAL client.
- **Membership.** Under S2, prod membership is CRM-authoritative, so the CIS Dev feed can only *revoke*.
- **Tenant existence.** The `catalog.v1` read is fine, but the tenant registry the prod cell trusts should be
  CRM-local (a row created at onboarding), not inferred from CIS Dev.

**Changes:** cost $0. Schedule +1 issue (W1 for the client split, W5 for prod). Decision (owner): this amends ADR
0006, because a pool or client is added for the partner app.

### S4 — High: API Gateway `AWS_IAM` is not an authentication boundary here

**Evidence**
- Today every API Gateway method is `authorization = "NONE"`:
  - CIS: `modules/api_gateway/main.tf:25,54,79,110,149,188,221,246,271,296,346`;
  - Booking: `booking.tf:474,492`.
- The ALB module says so itself: "A service behind it must still never trust the gateway to have authenticated"
  (`modules/alb/main.tf:75-80`).
- The ALB SG admits :80 from the **VPC CIDR**, and so does the NLB (`modules/alb/vpc_link.tf:14-19`).
- TripPlanner Lambdas run **in** the VPC (`tripplanner.tf:348-351`). So do CIS (ECS exec on), Booking, the NAT
  instance and the prod cell.
- Any of them can call `http://<alb>/internal/v1/tenant-members`, `/booking/b2b/*` or `/crm/ops/*` directly and skip
  the IAM check the design relies on (design §7.1, "CIS: hai endpoint nội bộ `AWS_IAM`"; Booking SigV4).

**Fix**

Authenticate in the app, and add a cheap network guard on top.
- **Human/staff paths.** These are already app-verified (Cognito JWT), so keep them.
- **Service-to-service** (CRM→CIS feed and catalog, CRM→Booking B2B, CIS→CRM monitoring):
  1. Keep `AWS_IAM` on those API Gateway methods, plus a **resource policy** that names the exact caller role
     ARNs. Without the resource policy, any acc2 principal with `execute-api:Invoke` passes, admin included.
  2. API Gateway adds two integration headers:
     - `X-AA-Caller = $context.identity.userArn`;
     - `X-AA-Gw = <secret from a stage variable>`.
  3. An **ALB listener rule** on `/internal/*`, `/booking/b2b/*` and `/crm/ops/*` forwards only when `X-AA-Gw`
     matches. Otherwise it returns a fixed 403.
  4. The app also checks `X-AA-Caller` against an allow-list.
- **Tenant context.** The CRM is the only caller of B2B, so Booking cannot tell agencies apart from the signature.
  The tenant id travels in a header that the CRM derives **only** from the verified user context, never from the
  request body. Booking logs it and applies per-tenant limits.

**Changes:** cost $0. Schedule +1 issue in W1 (an Infra pattern reused by both endpoints). This is the first
`AWS_IAM` in the platform, so the CI apply role needs `apigateway` policy rights. Check `cicd_split.tf` before W1.

### S5 — High: the N3 = b origin path is undesigned

**Evidence**
- Round 2 chose N3 = b: a Fargate container behind CloudFront. The design only priced the task (+≈ $8).
- CloudFront needs an origin. The shared ALB is internet-facing in **public** subnets (`modules/alb/main.tf:11-16`).
  Its default action on :80 and :443 forwards to the **CIS API** target group (`main.tf:78-104`), and its SG admits
  only the VPC CIDR.
- If the SG is opened to the CloudFront managed prefix list, then **any** CloudFront distribution reaches CIS and
  Booking. That includes an attacker's own distribution, and it skips API Gateway throttles.

**Fix**
- **Preferred, $0: a CloudFront VPC origin on the existing internal NLB.**
  - VPC origins support NLBs that have a security group and no TLS listener. The VPC-link NLB is internal, has an
    SG and uses a TCP :80 listener (`vpc_link.tf:47-56,62-63`).
  - us-west-1 is supported except AZ `usw1-az2`
    ([CloudFront VPC origins](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html),
    20/10/2026).
  - Admit the service-managed `CloudFront-VPCOrigins-Service-SG` (option 2 on that page) on the NLB SG.
  - Add an ALB host-header rule for `portal.` / `go.` → the portal target group.
  - Add an origin custom header (secret) that the rule requires.
- **Fallback.** A new internal ALB as a VPC origin, ≈ $18/month (estimate: ALB hour + LCU, not re-read today).
- **Viewer IP.** Take the client IP from `CloudFront-Viewer-Address` (add it in the origin request policy). Drop any
  client-supplied `X-Forwarded-For`. This is the IP the BFF HMAC-signs for the CRM rate limiter (design §7.4).
- **BFF to CRM.** Now that the BFF runs in the VPC, BFF→CRM can stay on the internal path. The CRM still verifies
  the user JWT, so `api-crm` on API Gateway is needed only for webhooks, which is a smaller public surface.

**Changes:** cost $0, or ≈ +$18 if the spike fails. Schedule: +1 spike in W0, replacing the LWA spike that N3 = b
removed. Decision: a technical pick inside N3 = b.

### S6 — High: scrubber facts, and the acc3 role vs D12

**Evidence**

[Guardrails sensitive filters](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-sensitive-filters.html)
and the [PII entity API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailPiiEntityFilter.html),
both 20/10/2026:
- Masking replaces with the type, "for example, `{NAME}` or `{EMAIL}`". The placeholders are not numbered, so two
  travellers collapse into one `{NAME}`. The design's restore step assumes `<PERSON_1>`… (design §7.3).
- The response field `match` "contains the original PII value". Logging an `ApplyGuardrail` response or exception
  therefore leaks PII.
- The passport entity is **`US_PASSPORT_NUMBER` only**. There is no generic passport type, and no VN CCCD, DOB or
  health entity.
- "Model invocation logs … always contains the original, unmodified request."
- Vietnamese is "Optimized and supported" for sensitive-information filters (the panel's claim holds).
  [Languages](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-supported-languages.html).

Fallback and the acc3 role:
- If acc2 is blocked, the design's fallback runs `ApplyGuardrail` in **acc3** (design §7.3). That sends **raw**
  traveller text to another account, under another reseller.
- The acc3 role `AA3-Bedrock-Invoker` trusts only the CIS task role and the TripPlanner Lambda role
  (`accounts/acc3-bedrock/main.tf:21-50`).
- It allows Anthropic models **only through `global.` inference profiles** (`main.tf:84-95`). These are Sonnet 4.6,
  Haiku 4.5, Sonnet 5 and Opus 5.5. There is **no Haiku 5.5 or Sonnet 5.5**, **no `us.` Anthropic profile** and no
  `bedrock:ApplyGuardrail`.
- D12 says "us. only, ZDR". Reusing that role would route CRM prompts worldwide.

**Fix**
1. Use Guardrails in **detect** mode (`NONE`) and build the numbered placeholders yourself from the `match` list
   and spans. Then restore from your own map (DEK-encrypted, 24 h TTL, as designed).
2. Add regex passes for passport (generic `[A-Z0-9]{6,9}` near a passport keyword), VN CCCD (12 digits), DOB,
   addresses in VN format, and the `pii:health` flags. Never send Stage 3 fields to any LLM path at all: build the
   prompt from F2 + scrubbed free text only.
3. A wrapper that never logs a Guardrails response body. Add a CI test that the logger redacts the `match` key.
4. **Fallback = fail closed** (AI drafts off for that tenant), not acc3 with raw text. If the owner prefers acc3,
   acc3 must be listed as the sub-processor that receives raw text.
5. **A new acc3 role `AA3-Bedrock-Invoker-CRM`:**
   - it trusts only the CRM task roles (dev and prod) with a new ExternalId;
   - it allows only `us.` profiles of Haiku 5.5 / Sonnet 5.5 plus their foundation-model ARNs (same 3-ARN shape as
     `main.tf:69-75`), and `bedrock:ApplyGuardrail` on the one guardrail ARN.
6. W0 read-only check: model invocation logging on acc3 (`get-model-invocation-logging-configuration`) must be off,
   or the CRM path must use a region or account where it is off.

**Changes:** cost $0. Schedule +1 issue in W2 (acc3 Terraform root, applied with acc3 credentials). Decision: none
new. This *implements* D12 correctly.

### S7 — Medium: D12 and D22 "CIS can monitor CRM", made safe

These are round-2 changes, so the design has nothing yet.

**Fix**
- **Endpoints.** The CRM exposes two read-only endpoints:
  - `GET /crm/ops/v1/llm-usage?since=`: rows per day × model × stage × tenant_id with tokens, cost and error
    class. No prompt text and no traveller_token.
  - `GET /crm/ops/v1/jobs/summary`: per kind × status counts, oldest queued age, last failure **class**.
- **Authentication.** Use the **staff's WORKFORCE access token**, which the CIS admin BFF already forwards
  (`frontend/lib/auth-server.ts:198`). Accept only `client_id = cis-admin` and group `cis-admin`
  (`identity.tf:134-136`). Do **not** reuse `ADMIN_SECRET`: it is a static shared secret
  (`docs/security/secrets-register.md:223`), and putting it in a second app widens its blast radius.
- **Job errors.** The Booking runner the CRM copies stores free-text `error` and `result`
  (`AA-Booking/backend/app/jobs/queue.py:123,143,158`). asyncpg and pydantic messages can echo values such as
  email or phone. In the CRM copy, store `error_class` plus a redacted message, and add a unit test that feeds a
  PII string through the error path.
- **Budgets and alarms.** Also emit EMF metrics (`aa-crm/llm` cost, `aa-crm/jobs` failures), so the existing budgets
  and alarms apply without any cross-app read.
- **Cost attribution in acc3.** Calls from the dedicated CRM role (S6) are attributable in CloudTrail. For the
  bill, use a Bedrock *application inference profile* tagged `App=crm`. I did not verify this today; check it in
  the W0 Guardrails/Bedrock spike.

**Changes:** cost $0. Schedule: inside W1 (jobs) and W7 (LLM).

### S8 — Medium: audit log volume, contention and integrity

**Evidence**
- The spec requires "Every read is logged" (`partner-crm-spec.md:117`). The design uses a per-tenant hash chain
  written in the same transaction as `reveal()` (design W2 row, §7.2).
- Volume estimate. My assumptions, all estimates:
  - 3 seats;
  - a board with ~30 trips loaded ~20 times a day per seat, where each card reveals a name;
  - ~100 detail views a day;
  - AI and automation reads.
- That gives ≈ 2–3k reveal events per agency per day if you log one event per traveller per request, i.e. ≈
  70–90k per agency-month.
- At ≈ 300 B per row with indexes, that is ≈ 25 MB per agency-month: ≈ 3 GB/year at 10 agencies (on a 20 GB cell
  disk) and ≈ 60 GB/year at 200.
- A per-field row model multiplies this by 5–10.
- A chain needs the previous hash, so every reveal for one tenant serialises on the chain head.
- The master or the owner role can rewrite both the rows and the chain.

**Fix**
- **One event per request**, with `traveller_ids[]` and `fields[]` arrays. A list view is one event.
- **Monthly partitions**, then archive to S3 Parquet after 90 days. C5.4a already prescribes this
  (`03-scaling.md:290`).
- **Batch chaining.** Compute the chain in a `crm_audit_seal` job every minute per tenant (a Merkle root over that
  minute's rows), not inside the request transaction.
- **A tamper anchor.** Write each seal to a bucket with S3 Object Lock (compliance mode), retention per Q6.
- **Grants.** The runtime role gets `INSERT, SELECT` only, which is the KEY-9 pattern
  (`01-engineering.md:238-239`). Set the C5.1c autovacuum settings (`03-scaling.md:256`).

**Changes:** cost ≈ $0 (S3 cents). Schedule +1 issue in W2. Decision: retention period (Q6, Ms. Thư).

### S9 — Medium: per-traveller DEKs and KMS traffic; crypto-shred vs backups

**Evidence**
- With a DEK per traveller wrapped directly by the agency key (D7 a), every reveal of a traveller not in memory is
  one KMS `Decrypt`. A 30-card board means 30 calls.
- Pricing: $0.03 per 10k requests, 20k a month free across all regions
  ([KMS pricing](https://aws.amazon.com/kms/pricing/), 20/10/2026). Note that the design says acc2 assumes no free
  tier (design §9.1).
- The us-west-1 shared quota is 10,000 req/s
  ([KMS quotas](https://docs.aws.amazon.com/kms/latest/developerguide/requests-per-second.html), 20/10/2026).
  Quota and cost are fine. Latency and CloudTrail noise are the issue: the trail logs read events
  (`observability.tf:446-457`).
- Without caching, my estimate is ≈ 0.2–0.7M decrypts per agency-month (vs 5k in design §9.1). That is ≈ $0.6–2 per
  agency-month and up to 10k events a day per agency in the trail.
- Crypto-shred of one traveller deletes the wrapped DEK. But PITR (14 days) and cross-region snapshot copies keep it,
  and the agency key is still alive, so a restore makes the data readable again (C7.2b, `03-scaling.md:372`).

**Fix**
- An in-process DEK cache: LRU with a TTL of about 5 minutes, keyed by (tenant, traveller). Decrypt in parallel for
  list views.
- Put `crm_tenant_id` and `traveller_id` in the encryption context, so CloudTrail shows *which* DEK was decrypted.
  That is the forensic backstop for S1.
- KMS CloudTrail entries no longer match reads 1:1. The app `access_event` (S8) is the agency-facing record.
- Document "deleted, and unrecoverable after N days" where N = the backup retention (Q3). Do the restore drill
  with a shredded traveller to prove it.

**Changes:** cost ≈ $0–2 per agency-month (now explicit). Schedule: none extra (inside the W2 crypto library).
Decision: the deletion promise (Q3).

### S10 — Medium: the inbox is the largest PII store and sits outside F1

**Evidence**
- Module 5 stores whole conversations: names, phones, passport scans as attachments.
- The design's F1 covers contact and Stage 3 fields only (design §7.2).
- The SES inbound pattern the design copies writes raw MIME to S3 with **SSE-S3 (AES256)**
  (`e2e_mailbox.tf:93-98`), which any admin can read.
- The design adds **one receipt rule per agency** to the single active rule set (design §8). That needs either an
  Infra PR per onboarding or broad `ses:*ReceiptRule*` rights on a set the e2e rule also lives in
  (`e2e_mailbox.tf:203-218`).
- The inbox UI renders inbound HTML email in the agency origin. That is stored XSS against agency sessions.

**Fix**
- **One catch-all rule** for the domain `in.crm.lumiguides.it.com` → S3 with SSE-KMS under one CRM *ingest* key
  (+$1/month), with a 3-day lifecycle.
- **`crm_mail_ingest`** routes by local-part to the tenant, then re-encrypts the body and attachments under that
  traveller's or trip's DEK (or a per-tenant mailbox DEK), then deletes the raw object.
- **Classify** `crm.message.body` and attachments as F1 (`pii:` comments).
- **Rendering.** Render HTML mail sanitized, inside a sandboxed iframe from a cookieless separate origin (e.g.
  `mail-view.` host), with a strict CSP and no scripts.
- **Sender trust.** Show the SES SPF/DKIM/DMARC verdicts. Link to a trip only by the reply-to token plus the known
  sender, never by subject.

**Changes:** cost +$1/month. Schedule +1 issue in W3 (ingest key and viewer origin). Decision: none.

### S11 — Medium: RLS on `crm.*` vs the cross-tenant code paths

**Evidence**
- CIS uses `set_config('app.tenant_id', …, true)` per transaction (`api/core/aa544_tenant_pool.py:359-366`).
- CIS learned that a pooled connection holds `''` afterwards, and fixed it with a `NULLIF` policy
  (`api/migrations/225_catalog_views.sql:113-117`).
- The design puts FORCE RLS `TO crm_app` on every tenant table. But four paths read across tenants:
  - the in-process runner claims jobs across tenants;
  - module 8 ops lists departures across agencies;
  - insights roll up across agencies;
  - the retention purge.
- With FORCE, even the owner role is filtered. The design does not say how these paths read.

**Fix**
- **`crm.job` has no RLS.** Its payload holds **ids only**, with a CI check that rejects `pii:` columns or keys in
  job payloads. The worker opens a tenant transaction per job.
- **Scheduled work** iterates a non-PII `crm.tenant` registry and processes each tenant in its own
  `set_config(..., true)` transaction.
- **Ops release.** `crm.ops_release` is read through a NOLOGIN `crm_ops_reader` with a policy on that table only.
  The handler does `SET LOCAL ROLE` inside one transaction. The rows are AA-ops-key ciphertext anyway.
- **Insights** aggregate per tenant first, then merge with k ≥ 10 / ≥ 3 agencies in app code.
- **A single DB helper** `tenant_tx(tenant_id)`. A lint test forbids `pool.fetch*` and `execute` outside it. Add an
  X2 probe cell: as `crm_app` with no tenant set, every `crm.*` tenant table returns 0 rows.

**Changes:** cost $0. Schedule: inside W1/W2.

### S12 — Medium: agency sign-in strength for a PII app

**Evidence**
- The EXTERNAL pool has `mfa_configuration = "OFF"` (`identity.tf:445`).
- Sign-in is by email one-time code (`ADR 0006` §4 table, `:163`).
- The `cis-portal` refresh token lasts 168 h (`identity.tf:170`).
- So an agency staffer's mailbox is the only factor protecting passport data for a week of sessions.

**Fix**
- The partner pool or client from S3 uses **passkeys (WebAuthn)** or TOTP as a second step for the owner and agent
  roles. Cognito Essentials supports passkeys as a first factor.
- For assistants, at minimum a step-up re-authentication before any Stage 3 reveal.
- Refresh ≤ 24 h on the prod client. Use the existing `enable_token_revocation` (`identity.tf:632`) at logout and
  on role removal.

**Changes:** cost $0. Decision: owner (security posture), plus Q4 for Ms. Thư (sign-in friction for agencies).

### S13 — Medium: traveller links, OTP, and one origin for every agency

**Evidence**
- The interactive proposal has "no client login" (spec module 3), and the client portal is a signed link plus an
  email OTP (design §3.4). Tokens in URLs leak:
  - through `Referer` to third parties on those pages (Mapbox tiles, the Stripe pay link);
  - into ALB access logs (`diagnostics.tf:101-139`; only a 7-day expiry, but it is a copy);
  - into CloudFront logs if they are enabled.
- Every agency's traveller pages share **one origin** `go.…/t/{tenant}` (design §3.4). Any agency-supplied content
  rendered as HTML would run with every other agency's travellers' cookies.

**Fix**
- **Tokens.** Exchange the link token on first hit for a host-only, httpOnly cookie scoped to that trip, then
  redirect to a token-less URL. Store only hashes of link tokens.
- **Headers and limits.**
  - `Referrer-Policy: no-referrer` on traveller pages;
  - OTP: 6 digits, 10 min TTL, 5 attempts, per-link and per-IP rate limits;
  - no PII rendered before the OTP;
  - the proposal page shows only F2 and prices, no names.
- **Content.** No agency-supplied raw HTML on `go.`: a markdown or text allow-list, a strict CSP, no inline
  scripts. Per-agency sub-domains are an option later.

**Changes:** cost $0. Schedule: inside W3/W5.

### S14 — Medium: N15's future "Encrypt-only public path" conflicts with BYO credentials

**Evidence**
- N12 has agencies bring their own Twilio account (design §8).
- Twilio signs webhooks with HMAC using the **agency's auth token**, so verifying a webhook needs that token in
  plaintext on the public hooks path.
- The design wraps provider keys with the DEK (design §8 SMS row). So the hooks service would need `Decrypt`. That
  contradicts N15's "role **chỉ Encrypt/GenerateDataKey**" (design §7.2).
- Gmail `gmail.send` refresh tokens and WABA tokens are the same kind of high-value credential.

**Fix**
- **A separate credential class.** Per-agency integration secrets go under a per-agency *integration* data key,
  distinct from the traveller vault keys.
- **What the hooks service may decrypt:** only the integration key class, never traveller DEKs.
- **Record this in ADR 0014** now, so N15's later split is possible.

**Changes:** cost $0. Schedule: design note in W0 ADR.

### S15 — Medium: module 8 through Booking admin puts plaintext PII on Vercel

**Evidence**
- N6 has AA ops read module 8 "ở Booking admin qua API" (design §5 row 8).
- Booking admin is a Vercel project with a server-side BFF proxy (`AA-Booking/frontend/app/api/booking/[...path]`,
  `frontend/lib/api/server.ts:1-4`). Passports and DOBs would transit Vercel functions.
- The design removes Vercel from the sub-processor list (design §10.3) and notes the Hobby commercial-use risk
  (N19).

**Fix**
- Serve the ops-release page from the AA-Partner app on AWS, under a staff host with WORKFORCE sign-in.
- Create a new WORKFORCE group `crm-ops` (`identity.tf:134-143`).
- Alternatively, keep it in Booking admin only after Booking admin leaves Vercel (N19).

**Changes:** cost $0. Schedule 0–1 issue in W5. Decision: technical.

### S16 — Low–Medium: JWT secrets after the portal leaves CIS

**Evidence**
- `aa-cis/dev/jwt-secret` is one HS256 key for staff and tenant tokens, with **no rotation since 2026-09-01**
  (`docs/security/secrets-register.md:227`; `api/routers/auth.py:34`).
- The portal does not hold it today (no `JWT_SECRET` in `portal/`, checked by `git grep`).

**Fix**
- Make it a rule in ADR 0014: AA-Partner and the CRM API **never** receive `JWT_SECRET` and **never** accept HS256.
  They take Cognito RS256 tokens only.
- No `/crm/*` route is enabled in an environment where the tenant session is still the API-key/HS256 session (gate
  on AA-813 cutover).
- After cutover:
  - close `/auth/tenant-login` for humans (ADR 0006:400);
  - split or retire the tenant HS256 path;
  - rotate the key;
  - land B3 first (design §4.5).

**Changes:** cost $0. Schedule: none (sequencing only).

### S17 — Low–Medium: secrets per app

**Evidence**

The design counts two Dev secrets (design §9.2). The app actually needs these, per env:

| Secret | Contents |
|---|---|
| DSN | — |
| BFF secret (one JSON) | session encryption key, client-IP HMAC key, CloudFront origin header secret, link/OTP signing key |
| Cognito partner client secret | — |
| Provider secret (one JSON) | Stripe platform restricted key + Connect webhook secret, Meta app secret, Documenso API key + webhook secret, Google OAuth client secret, Microsoft client secret |

Cognito client secrets also sit in Terraform state (`secrets-register.md:296`).

**Fix**
- **Four secrets per env**, with planned rows in `secrets-register.yaml` before creation (the register's
  `planned` status).
- **Scope task-role reads** to `crm/<env>/*`, never `crm/*`.
- **Prod secrets** get a resource policy with an explicit Deny except the prod task and execution roles, copying
  `identity_alerts.tf:52-74`.
- **The prod deploy role** trusts only `environment:prod` (copy the Booking OIDC subject pattern,
  `booking.tf:66-83`), and the GitHub `prod` environment requires a reviewer.
- **The PR-preview role** may deploy only the preview service and reads only Dev secrets.
- **The DB Migrate `environment` input** for the cell (C7.2d) runs under a GitHub `prod` environment with required
  reviewers.

**Changes:** cost ≈ +$1.6–2.4/month per env (4–6 × $0.40). Schedule: inside W1/W5.

### S18 — Low: logs are the leak path once ECS exec is off

**Evidence**
- The design turns ECS exec off and says "debug bằng log" (design §3.3).
- PII can reach logs through:
  - pydantic 422 errors, which echo inputs;
  - asyncpg constraint errors, which echo key values;
  - the Guardrails `match` field (S6).

**Fix**
- A log-scrub filter in the app logger and in Sentry `before_send`.
- A CloudWatch Logs **data protection policy** on `/ecs/aa-crm-*` as a backstop: $0.12/GB scanned
  ([CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/), example figure, 20/10/2026), i.e. cents at
  Dev volume.

### S19 — Low: webhooks and SES

**Fix**
- **Map the tenant from the provider's own account id:**
  - Stripe Connect: the event `account`;
  - Meta: the WABA or Page id;
  - Documenso: the envelope id stored at send.
  Never use metadata the payer or sender controls.
- **Separate traveller OTP and intake mail from staff codes.** Send them through the `transactional` configuration
  set, with per-tenant send caps. Today the identity and From address are shared with staff email codes, so abuse
  of the OTP endpoint could get SES paused for staff sign-in (`ADR 0006:444-450`).

---

## 2. Break-glass for the CRM (consolidated design)

| Layer | Who / what | Guard | Visible to the agency |
|---|---|---|---|
| Vault decrypt | IAM role `crm-<env>-breakglass`. It is assumable only from the admin role with MFA, max 1 h, `sts:TagSession` required. Its KMS permission requires `kms:EncryptionContext:crm_tenant_id = ${aws:PrincipalTag/tenant}`, so **one tenant per session** | Key policy S1(c) allows it explicitly. EventBridge → SNS + agency `access_event` | Yes, automatically |
| DB (prod cell) | Cell master is break-glass only, per DM-8.9 (`02-data-management.md:289`). F1 fields are ciphertext | RDS logs 365 days (C4.2b), reason in the session log + Linear issue, rotate after use | Only if a vault field was decrypted (via the role above) |
| App | No "impersonate agency" feature. Support happens only through an agency-granted, time-boxed support membership (Q2) | `crm.member_role` with an expiry; the grant is audited | Yes |
| Cognito | Existing WORKFORCE `breakglass` client (`identity.tf:163-166`). It may call the CRM **ops** endpoints only, never `/crm/v1` | Existing break-glass alarm (`identity.tf` header) | ops-release reads are audited to the agency (N6) |

---

## 3. What the design gets right (keep)

1. **No real traveller PII on Dev**, because of the prod cell. Synthetic agencies only on Dev until all 23 modules
   are done (H1 = b, H4 = c), which lowers pilot-time risk further.
2. **No DB grants across apps.** HTTP only, once S4 makes it authenticated.
3. **Fail-closed scrubbing**, with an EN/VI corpus gate and AI off per tenant by default.
4. **ECS exec off on the CRM service**, and no Presidio sidecar.
5. **Host-only cookies** that keep `portal.` and `go.` sessions apart, a BFF allow-list (B7), and the B3 fix first.

---

## 4. Proposed additions to the wave plan (≈ +7 issues)

| Wave | Issue |
|---|---|
| W0 | Spike: CloudFront VPC origin on the internal NLB with Fargate (S5). Read-only check of acc3 invocation logging (S6) |
| W1 | Service auth pattern: resource policy + gateway header + ALB rule (S4). Prod/preview client split (S3). CRM-authoritative roles + revoke-only feed + EXTERNAL admin alarms (S2) |
| W2 | KMS key template + drift check + alarm → agency audit + break-glass role (S1, §2). Dedicated acc3 CRM role + Guardrails detect-mode scrubber (S6). Audit partitions + batch seal + Object Lock anchor (S8) |
| W3 | Mail ingest key + re-encrypt + sandboxed viewer origin (S10) |

The rest fit inside existing issues: S7, S9, S11, S13, S16–S19.

---

## 5. Questions for Ms. Thư (non-technical items hit in this review)

Each has a proposed answer, per the owner's rule that H-questions carry a proposal.

| # | Question | Proposed answer |
|---|---|---|
| Q1 | The approved H3 sentence still says "AA staff cannot open traveller records". Technically AA owns the AWS account, so a logged emergency access is always possible. Can we promise this instead? | "AA staff cannot open traveller records in normal operation. Emergency access is possible only for one agency at a time, needs two-step sign-in, is recorded, and appears in that agency's own audit log automatically." |
| Q2 | Should AA support be able to look inside an agency's CRM when the agency asks for help? | Only if the agency owner grants AA support a time-limited access (e.g. 24 h) from their settings. It is logged, and the owner can revoke it at any time. No hidden AA access. |
| Q3 | When a traveller or agency asks for deletion, what do we promise? | "Deleted immediately in the app. Unreadable everywhere, including backups, within 30 days." The exact number follows the backup retention we keep. |
| Q4 | Should agency staff use a stronger sign-in (phone/passkey or authenticator app) because they handle passports? It adds about 1 minute at first sign-in. | Yes for owners and agents. Assistants confirm again before opening passport details. |
| Q5 | AA ops will see confirmed-departure traveller details. Should each view be shown to the agency? | Yes. The agency sees "AA ops viewed departure details for trip X on date Y" in its audit log. |
| Q6 | How long should agencies be able to see "who opened what" in their audit log? | 12 months visible in the app, then archived for a further 6 years (locked, not editable), unless the lawyer later advises otherwise. |

---

## 6. Sources

**Repository (re-read 20/10/2026, refs at the top):**
- Infra:
  - `accounts/aa365/identity.tf:134-198,344-370,421-500,600-640`;
  - `identity_variables.tf:143-175`;
  - `lambda_src/identity_triggers/external.py:1-110,160-187`;
  - `identity_alerts.tf:1-80`;
  - `observability.tf:446-457`;
  - `modules/alb/main.tf:1-104`, `modules/alb/vpc_link.tf:1-90`;
  - `modules/api_gateway/main.tf` (all `authorization = "NONE"`);
  - `booking.tf:60-83,203-205,474-512`;
  - `tripplanner.tf:345-370`;
  - `bedrock_satellite_assume.tf:1-47`;
  - `accounts/acc3-bedrock/main.tf:1-200`;
  - `e2e_mailbox.tf:93-98,203-220`;
  - `diagnostics.tf:101-139`.
- AA-CIS-App `origin/main`:
  - `api/core/aa544_tenant_pool.py:359-366`;
  - `api/migrations/004_tenant_rls.sql:75-80`;
  - `api/migrations/225_catalog_views.sql:105-125`;
  - `frontend/lib/auth-server.ts:198`.
- AA-Booking `f4fb80d`:
  - `backend/app/auth/identity_config.py:1-103`;
  - `backend/app/jobs/queue.py:35-221`;
  - `frontend/lib/api/server.ts:1-40`;
  - `frontend/lib/session.ts:4-84`.
- Root:
  - `docs/adr/0006-ecosystem-identity.md:110-160,400,425-450`;
  - `docs/security/secrets-register.md:1-80,223-299`;
  - `docs/architecture/data-standards/02-data-management.md:285-289`;
  - `03-scaling.md:137-153,230,256,290,372-375`;
  - `01-engineering.md:236-241`.

**Web (accessed 20/10/2026):**
- [KMS keys in IAM policies](https://docs.aws.amazon.com/kms/latest/developerguide/cmks-in-iam-policies.html)
- [KMS pricing](https://aws.amazon.com/kms/pricing/)
- [KMS request quotas](https://docs.aws.amazon.com/kms/latest/developerguide/requests-per-second.html)
- [Guardrails sensitive filters](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-sensitive-filters.html)
- [GuardrailPiiEntityFilter](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailPiiEntityFilter.html)
- [Guardrails languages](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-supported-languages.html)
- [CloudFront VPC origins](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html)
- [CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/) (data protection $0.12/GB, example figure)

**Estimates (not verified):** audit volume and KMS decrypt volume per agency (S8/S9 assumptions), the internal ALB
fallback ≈ $18/month (S5), and the Bedrock application-inference-profile cost tagging (S7).
