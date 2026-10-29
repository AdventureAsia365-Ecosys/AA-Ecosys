# AWS account consolidation and LLM access: options assessment (S257, 29/10/2026)

Read-only research for the tech lead, to bring to the business owner. No AWS write was made. Facts cite a file or a
single-line read-only command (`--profile aa365-admin`, us-west-1 unless noted). **[EST]** marks an estimate,
**[UNVERIFIED]** a claim not confirmed on a primary source, **[OPEN]** a fact that must be checked before acting.

Related: AA-864 (research: consolidate on one AWS account), AA-880 / ADR 0012 (environment model; decision 12 names
AA-864 as a trigger), ADR 0001a (acc3 the only LLM account), the S257 vendor research in
`.tmp-session/S257/llm-vendor-vn/` (`RECOMMENDATION.vi.md`, `angle1-aws-partners-vn.md`, `angle2-alternatives.md`).

---

## 0. Summary and recommendation

**Answer to "is batch easier with the direct API?": yes.** The Anthropic Message Batches API is one HTTPS call with
the same request body as a normal Messages call: up to 100,000 requests or 256 MB per batch, most batches finish within
1 hour (24 h maximum), results kept 29 days, 50 % off every token, and the discount stacks with prompt caching. No S3
bucket, no IAM service role, no PassRole, no minimum record count, no per-account entitlement. Bedrock batch
(`CreateModelInvocationJob`) needs JSONL input in S3, an S3 output prefix, a service role Bedrock assumes, a minimum
number of records per job (a Bedrock quota, typically 100 **[UNVERIFIED for current value]**), and an account-level
enablement that AWS has not granted acc3 after a support case open about 40 days (case 178979743800653, Linear AA-624;
`infra/AA-CIS-Infra/CONTEXT.md` "Bedrock Batch Inference"). Message Batches also runs on **Claude Platform on AWS**
(Anthropic-operated, billed through AWS Marketplace), but **not on Amazon Bedrock**, Vertex or Foundry (claude-api skill,
`shared/platform-availability.md`). The CIS batch code to port is `shared/llm_client/bedrock_batch.py` (301 lines) and
`services/content_generation/s1_batch.py` (280 lines).

**Ranking (most suitable first):**

| # | Option | Engineering | Calendar | Moves data? | Fixes Claude 5.5 / OpenAI? | Verdict |
|---|---|---|---|---|---|---|
| 1 | **D. Direct Anthropic + OpenAI APIs for LLM**, AWS keeps infra | ~~3–5~~ **4–6** dev-days (Anthropic adapter + batch + cost logging + TripPlanner), hours for OpenAI **[EST, raised in §7]** | 1 week (+ account-tier wait, §7 R-D1) | No | Yes, independent of any reseller or AWS case | **Do now**, as bridge and as a permanent second path |
| 2 | **C/E via our own AWS Organization + Billing Transfer** (new AA-owned management account; acc2 leaves TrueIDC's org and joins ours with acc3; an Anthropic-authorized reseller bills us through Billing Transfer) | ~~3–6~~ **4–8** days **[EST, raised in §7]** | ~~3–8~~ **4–10** weeks (business + month-aligned start + an AWS-direct gap month, §7 R-C) | No | Yes on Bedrock, once the reseller is authorized and acc2 quotas are raised | **Recommended structural fix** |
| 3 | **E. acc2 joins eCloudvalley's Organization as a member** (the tech lead's idea) | ~~2–4~~ **3–5** days **[EST, raised in §7]** | 2–6 weeks | No | Yes, same conditions as #2 | Acceptable fallback if no reseller offers Billing Transfer; repeats the acc3 lock-in pattern |
| 4 | **B. Keep acc2 on TrueIDC; only acc3 under an authorized reseller** | 0–1 day | 1–4 weeks (AWS must lift acc3's "Error 002") | No | Yes, through the existing cross-account satellite | Minimal, keeps two vendors and TrueIDC's management access |
| 5 | **A. Move everything acc2 → acc3, one reseller contract for acc3** | ~~25–32~~ **33–43** engineer-days **[EST, raised in §7]** | ~~5–7~~ **7–10** weeks | Yes (RDS, S3, Cognito, secrets, DNS, …) | Only after the same reseller step as #2/#3 | **Not recommended**: large cost, a sign-in reset for every user, and per-domain outages, for nothing #2 does not give |

Why: the LLM block comes from **who pays for the account** (the payer must hold Anthropic resale authority; TrueIDC does
not; acc3 lost its payer on 29/10), not from **where the resources sit**. Changing the payer (options C/E) solves it
without moving 785 Terraform resources. Moving resources (A) still needs the payer change afterwards. Option D removes
the dependency on any AWS payer for LLMs and is the only option that can be live this week.

**Sequencing proposal:** D now (unblocks the pipeline and batch) → in parallel, the business owner asks Renova Cloud and
eCloudvalley Vietnam the reseller questions (`RECOMMENDATION.vi.md` §"Câu hỏi bắt buộc") plus "do you support Billing
Transfer?" → create the AA-owned management account and invite acc3 (already standalone) → agree the TrueIDC exit →
move acc2 in **after** D is live (see risk E-1: leaving an org can trigger the same "Error 002" on acc2, which would also
stop acc2's native Cohere Embed v4 and the CRM Bedrock guardrail) → Billing Transfer start on the 1st of a month.

---

## 1. Live inventory of acc2 (005097885195)

Sources: `docs/generated/inventory.md` (Terraform state of `accounts/aa365`, AA-CIS-Infra@c2aa8f58, 29/10/2026), plus
read-only CLI on 29/10/2026.

**Terraform total: 785 resources, 124 types** (booking 26, cis 61, crm 77, identity 39, shared 100, tripplanner 25,
untagged 457). Alarms catalog `docs/generated/alarms.md`, IAM `docs/generated/iam-roles.md` (37 roles, 56 inline
policies, 4 customer-managed policies), network `docs/generated/network.md`.

**Organization and billing**

| Item | Value | Source |
|---|---|---|
| Organization | `o-cnvpmom3os`, feature set ALL, **SCPs enabled**; management account 033086823579 (Arise IDC = TrueIDC) | `aws organizations describe-organization` |
| SCPs on acc2 | Not readable from the member (AccessDenied) **[OPEN]**: whether `organizations:LeaveOrganization` is denied | `aws organizations list-policies-for-target` |
| Account contact | Pham Quoc Nghiep / AdventureAsia / VN | `aws account get-contact-information --region us-east-1` |
| Root e-mail owner | Not readable (`account:GetPrimaryEmail` denied) **[OPEN, critical]**: if acc2 was created by TrueIDC, the root e-mail may be theirs | console Account page |
| Support plan | Basic (no Premium Support) | `aws support describe-severity-levels` → SubscriptionRequiredException |
| Reservations | 0 Savings Plans, 0 RDS RIs, 0 EC2 RIs: nothing to lose on a move | `aws savingsplans describe-savings-plans`, `aws rds describe-reserved-db-instances`, `aws ec2 describe-reserved-instances` |
| Monthly cost (unblended) | Aug 140.22 USD, Sep 134.96 USD, Oct 1–28 185.77 USD | `aws ce get-cost-and-usage --region us-east-1 …MONTHLY` |
| Budget | 300 USD/month account budget + per-App budgets | Infra `CONTEXT.md` "Spend guards" |
| Bedrock on acc2 | Native Cohere Embed v4 (20 rpm) and the CRM scrub guardrail `k1v70up6uqvt`; Claude/GPT blocked by the payer; quotas tiny (Sonnet 4.6 10 rpm, GPT Luna 0 tpm), a Cohere quota raise was auto-declined ("account history") | `docs/ecosystem-architecture.md` §4.3, memory `acc2-bedrock-claude-gpt-blocked`, inventory output `crm_scrub_guardrail_id` |

**Compute, network, edge (stateless: rebuilt by Terraform in any new account)**

| Service | Count / detail | Source |
|---|---|---|
| VPC | 1 (`10.2.0.0/16`), 6 subnets (2 public, 2 private, 2 db), 3 route tables, IGW, NAT **instance** t4g.nano with EIP 54.215.104.249 | `network.md` |
| Security groups | 16 | inventory |
| ECS | 1 cluster, **6 services** (cis api, cis worker, booking api, crm api, crm web, crm portal), 7 task definitions | `aws ecs list-services --cluster aa-cis-dev-cluster` |
| ALB / NLB | 2 load balancers, 3 listeners, 6 target groups | inventory |
| API Gateway | 2 REST (CIS, Booking) + 1 HTTP (TripPlanner), VPC link, 3 custom domains, 4 usage plans | inventory |
| Lambda | 9 (4 Cognito triggers, 3 TripPlanner, ops probe, RDS snapshot expiry) | `aws lambda list-functions` |
| Schedules / rules | 6 EventBridge Scheduler schedules, 13 EventBridge rules | `aws scheduler list-schedules`, `aws events list-rules` |
| CloudFront | 4 distributions (img., partner-dev., go-dev., portal.), 1 VPC origin, 1 function | `aws cloudfront list-distributions` |
| WAF | 2 regional web ACLs (`aa-cis-dev-waf`, `aa-identity-dev-pools`) | `aws wafv2 list-web-acls --scope REGIONAL` |
| ACM | 7 certificates (us-west-1 and us-east-1) | inventory |
| ElastiCache | `aa-cis-dev-cache` cache.t3.micro (cache only, no data to move) | `aws elasticache describe-replication-groups` |
| Observability | 88 metric alarms, 18 log metric filters, 18 log groups, 2 SNS topics, 1 dashboard, 7 budgets, anomaly monitor | inventory |
| Security | CloudTrail (own KMS key), GuardDuty, Access Analyzer, account S3 Block Public Access | inventory, `security_*.tf` |
| CI/CD | 1 GitHub OIDC provider; 7 CI roles (CIS deploy, Booking deploy, TP deploy, CRM deploy, tf-plan, tf-apply, db-auto-apply) + docs-sync, e2e-mail-reader, scrub-corpus; 27 workflows across 6 repos call AWS (root 1, CIS 5, Booking 2, TripPlanner 2, Partner 6, Infra 11) | `iam-roles.md`, `grep role-to-assume .github/workflows/*.yml` |

**Stateful (data that a resource move must carry)**

| Data | Size / count | Move notes | Source |
|---|---|---|---|
| RDS `aa-cis-dev-db` | PostgreSQL 15.17, db.t4g.small, gp3 20 GB allocated, ~16.6 GB free → **~3.4 GB used** (incl. WAL/system) **[EST]**; encrypted with the **AWS-managed `aws/rds` key**; 4 app schemas, roles, RLS; 44 snapshots (manual DB-Migrate snapshots) | A snapshot encrypted with an AWS-managed key **cannot be shared cross-account**: first copy it re-encrypted with a customer-managed key, share key + snapshot, then copy again in the target account | `aws rds describe-db-instances`, `aws kms describe-key` (KeyManager AWS), CloudWatch `FreeStorageSpace` |
| S3 (17 buckets) | **~14.4 GB, ~68,400 objects** in total. bronze 5.41 GB / 27,023; TripPlanner Lambda artifacts 7.92 GB / 176 (rebuildable); CloudTrail logs 0.50 GB / 33,973 (archive, do not move); tfstate 0.49 GB / 1,198 (new state, do not move); ALB logs 37 MB / 5,310; CRM audit-c and audit-g 1.7 MB / 298 each (**Object Lock**, GOVERNANCE in Dev); e2e mail, supply media, CRM documents tiny; acp-bronze/silver/gold, gold, silver, ops-docs, CRM ingest empty | Same-region cross-account copy has no data-transfer charge; Object Lock buckets must be created with lock enabled and retention re-applied | CloudWatch `AWS/S3 BucketSizeBytes` / `NumberOfObjects`, `crm_storage.tf` |
| ECR (5 repos, IMMUTABLE) | cis-api ~184 images / ~41 GB; booking 19 / 1.0 GB; crm-api 13 / 1.1 GB; crm-web 14 / 1.2 GB; crm-portal 13 / 1.1 GB | Only the running SHA per service must be copied | `aws ecr describe-images` |
| Cognito | 4 pools (ESSENTIALS): workforce **6** users (MFA optional), external **9**, partner **8** (MFA required, TOTP), m2m 0; 11 app clients, 10 groups, 7 domains (3 custom: auth., staff-auth., partner-auth.), 10 managed-login styles, 3 resource servers; **no federated IdPs** | Users cannot be exported with passwords or TOTP seeds; `sub` values change in a new pool | `aws cognito-idp describe-user-pool`, `list-users`, `list-identity-providers` |
| Secrets Manager | **51 secrets** (aa-cis 25, crm 12, tripplanner 5, acp 3, booking 2, aa-ecosys 2, aa-crm 1, aa-identity 1); only 17 are Terraform-managed, the rest hold hand-written or app-written values | Values must be copied by a script (never printed); names listed in `docs/security/secrets-register.md` | `aws secretsmanager list-secrets` |
| KMS | 4 customer-managed keys: CloudTrail + CRM `data` (envelope keys for tenant data, context `{tenant_id, purpose}`), `ingest` (S3/SES), `seal` (asymmetric PAdES signing) | KMS keys never leave an account: CRM envelope keys must be re-wrapped under a new key, seal signatures need the old public key kept for verification | `crm_data.tf` header, `aws kms list-aliases` |
| SES | Domain identity `lumiguides.it.com`, **production access enabled** (50,000/day), 3 configuration sets, receipt rules (e2e mailbox, CRM mail ingest) | A new account starts in the SES sandbox; production access is a manual AWS review | `aws sesv2 get-account` |
| DNS | Route 53 public zone `lumiguides.it.com` (43 records) + private zone `dev.internal`; the domain is **not** registered in Route 53 (registrar outside AWS) | NS change at the registrar if the zone moves | `aws route53 list-resource-record-sets`, `aws route53domains list-domains --region us-east-1` (empty) |
| Account-ID literals | ~~Infra: 26 tracked files; root: 7 files; app code: 0~~ **Corrected in §7.1 F-1, F-2:** Infra 48 files / 119 hits (≈28 operational), root 148 files / 268 hits (15 operational), app repos 0 account IDs **but 7 source files in CIS/Booking/TripPlanner hard-code 4 real Cognito pool IDs and 10 client IDs**; plus 14 GitHub secret/var slots carrying acc2 role ARNs, registry or bucket | Rename work in Infra, GitHub secrets/vars **and app code (Cognito constants)** | `git grep -l 005097885195` per repo; `git grep -E 'us-west-1_[A-Za-z0-9]{9}'` |

---

## 2. Options compared

### Background facts used by every option

1. **Payer rule.** Bedrock third-party models are AWS Marketplace products charged to the payer. For a reseller-billed
   account, the reseller must be allowed to resell Bedrock, and for Claude it must also hold **Anthropic resale
   authority** (footnote in the AWS Solution Provider Program Authorized Services List, updated 24/09/2026).
   TrueIDC shows no such authority; eCloudvalley claims it for "Taiwan and Southeast Asia" (press release 09/02/2026,
   Vietnam not named), Renova Cloud claims it for Vietnam (undated, about 06/2026). Proprietary OpenAI models on
   Bedrock carry no such footnote; TrueIDC blocking them too is likely its own policy **[UNVERIFIED]**. AWS gives
   resellers **no discount** on Claude or proprietary OpenAI models, so a reseller cannot sell them below list price.
   (`angle1-aws-partners-vn.md` §0, §1.)
2. **Leaving an organization** (AWS Organizations user guide, "Leaving an organization from a member account"):
   - needs `organizations:LeaveOrganization`, which the management account can remove with an SCP; otherwise the
     management account removes the account (`remove-account-from-organization`);
   - the account must first be able to stand alone: contact and address, **valid payment method, phone verification,
     support plan**; an account created inside the org has no root password until it is recovered through the root
     e-mail;
   - afterwards the account "is no longer covered by organization agreements that were accepted on its behalf", and
     "quota limits may change and could cause impact" (AWS says to contact Support);
   - past invoices and bills stay visible; **Cost Explorer history generated inside the old org is lost**;
   - an `OrganizationAccountAccessRole`-style role left by the old management account is **not** deleted
     automatically; we must delete it to cut the old vendor's access.
3. **Billing Transfer** (AWS Billing user guide, "Transfer billing management to external accounts", GA 19/11/2025):
   - it is a relationship **between two management accounts**: the partner's account invites **our management
     account**; a single member account inside someone else's org cannot use it, so we need our own AWS Organization;
   - start is 00:00 UTC on the 1st of the month named in the invitation, which must be accepted at least 24 h earlier;
   - either side can withdraw at any time; the transfer then ends at the end of the current or next month and our
     management account pays again;
   - we keep full administration of our org (SCPs, accounts); the partner gets no management access;
   - our side loses CUR (reconfigure), Cost Anomaly Detection alerts and AWS-priced cost data (pro forma view through
     the partner's Billing Conductor only); credits are not visible on our Credits page;
   - RIs, Savings Plans and volume tiers stay per organization.
   Whether a Billing Transfer account counts as a "channel program account" for Anthropic is not documented; assume yes,
   so the partner must still be Anthropic-authorized **[UNVERIFIED]**.
4. **acc3 evidence.** acc3 left eCloudvalley's org at 06:50 UTC on 29/10/2026 when the reseller's test credit ran out;
   OpenAI on Bedrock was refused at once and a full Bedrock block ("Error 002", every model family) followed. Community
   reports tie Error 002 to an account-level flag that only AWS Support lifts, often after 1–2+ weeks
   (`angle1-aws-partners-vn.md` §1.1). Leaving an org therefore carries a **real risk of a Bedrock block on the account
   that leaves**.
5. **Standalone AWS-direct is not a guaranteed fix.** acc1 (personal, standalone, AWS-billed) can call Claude 4.x but
   not Claude 5.5 or OpenAI (task context; ADR 0001a "acc1 reports them as not available for the account"). New
   accounts may need per-account model access and quota history.

### A. Move everything acc2 → acc3; one reseller contract for acc3

- **What it fixes:** one account for infra + LLM; the cross-account satellite (`bedrock_satellite_assume.tf`,
  ExternalId, five direct satellite call sites in CIS) disappears.
- **What it does not fix by itself:** acc3 is standalone and Bedrock-blocked today; it must still be put under an
  Anthropic-authorized payer (rejoin a reseller org or Billing Transfer through our own org) and get Error 002 lifted.
  That is exactly the step options C/E take, without the move.
- **Cost:** 25–32 engineer-days, 5–7 calendar weeks, a planned outage, a password/MFA reset for all 23 Cognito users, new
  Cognito IDs in every app and Vercel project, re-wrapping CRM tenant keys, SES production-access review, DNS cutover.
  Detailed plan in §3.
- **ADRs:** reverses ADR 0001 amendment S235 / D-17 ("prod on acc2, no new account") in name only, since ADR 0012 names
  "the infrastructure account" and moves with it (ADR 0012 option D row). Needs a new ADR.

### B. Keep acc2 for infra; put only acc3 (LLM) under a Bedrock-capable reseller

- **Steps:** (1) choose reseller (Renova or eCloudvalley VN), get written Anthropic authorization for Vietnam;
  (2) acc3 rejoins the reseller's org **or** (better) we create an AA management account, invite acc3, and accept the
  reseller's Billing Transfer; (3) resubmit the Anthropic use-case (FTU) form on acc3, subscribe the OpenAI Marketplace
  products, keep the AWS case open for Error 002 and the batch entitlement; (4) verify with a real `InvokeModel`
  (status APIs report AUTHORIZED even on blocked accounts).
- **Effort:** 0–1 engineer-day (no code change; the satellite already exists). **Time:** 1–4 weeks, driven by AWS lifting
  Error 002 and the reseller contract. **Cost:** LLM spend at list price (~250 USD/month today) plus any reseller fee;
  acc2 unchanged (~135–186 USD/month).
- **Risks:** two vendors and two bills stay; TrueIDC's management account keeps reach into acc2 (ADR 0012 decision 4.5
  risk stays open); acc3 depends on one reseller again; Bedrock batch still waits on the acc3 case; Lift credits on acc3
  continue (tier thresholds need 500+ USD/month of AWS usage on acc3, which LLM-only usage does not reach) **[EST]**.

### C. Move acc2's billing to a Bedrock-capable reseller without moving resources

- **AWS mechanics:** there is no "change reseller" switch for a member account. Either (C1) acc2 leaves TrueIDC's org
  and is invited into the new reseller's org (= option E), or (C2) acc2 leaves TrueIDC's org, joins **our own** new
  AWS Organization, and the reseller bills that org through **Billing Transfer**. C2 is the version that keeps control.
- **C2 steps:**
  1. Create an empty AA-owned AWS account as **management account** (root e-mail on an adventure.asia address owned by
     the company, hardware MFA, no workloads, AWS best practice). Enable Organizations (all features).
  2. Invite acc3 (standalone already) and accept from acc3.
  3. Pre-checks on acc2 (§4 E-checks): root e-mail owner, `LeaveOrganization` allowed, payment card, phone, support
     plan, roles trusting 033086823579, Cost Explorer history export.
  4. Agree the exit with TrueIDC (notice period, final invoice, who removes the account).
  5. acc2 leaves TrueIDC's org (or TrueIDC removes it), accepts our invitation the same day; delete any
     `OrganizationAccountAccessRole` left by TrueIDC.
  6. Reseller (Renova / eCloudvalley VN) sends a Billing Transfer invitation to our management account; accept at least
     24 h before the 1st of the month.
  7. Re-enable Bedrock model access on acc2 (Anthropic FTU form, OpenAI Marketplace subscribe), file quota increases.
  8. Re-point cost tooling: Cost Explorer history (lost from the old org), CE reader roles, the `/admin/llm-usage`
     page (pro forma data only under Billing Transfer; CUR and Cost Anomaly Detection unavailable to us).
- **Effort:** 3–6 engineer-days (account setup with MFA, checks, Terraform for org-level guardrails optional, cost tooling,
  verification) **[EST]**. **Time:** 3–8 weeks (TrueIDC exit + reseller contract; transfer starts on a 1st of the month:
  earliest 01/12/2026 if accepted by 29/11). **Cost:** one-off engineer time only; monthly AWS unchanged at list price
  plus reseller margin; no resource or data move.
- **Benefits beyond LLMs:** removes the vendor management account's reach into acc2 (closes ADR 0012 decision 4.5 and
  S241 P0-12), makes the payer switchable later without stranding accounts (the acc3 failure mode), satisfies the ADR
  0012 decision 12 trigger "AA-864 decides to consolidate on an AA-controlled account" without a resource move, and
  gives a ready home for a future separate prod account if ever needed.
- **Risks:** see §4 (E-1 Bedrock block after leaving, E-2 tiny acc2 quotas, E-5 cost data, E-7 credits visibility).

### D. Keep AWS for infra; use direct Anthropic / OpenAI APIs for LLM

- **Steps:** create organizations on platform.claude.com and platform.openai.com with a company card (prepaid credits
  expire after 1 year) or monthly invoicing through sales; store keys in Secrets Manager (`aa-cis/dev/...`, new rows in
  the secrets register); CIS: new `_call_anthropic_native()` adapter beside `_call_bedrock_converse()`, one CIS migration
  to allow `provider = 'anthropic'` (the `api_style='anthropic_native'` value is already allowed), Message Batches backend
  replacing `bedrock_batch.py` for S1, move the five direct satellite call sites onto the gateway; OpenAI: enable the
  existing `_call_openai()` rows (needs the tech lead to drop the S235 "Bedrock-only" policy); TripPlanner: same adapter
  for its gateway.
- **Effort:** Anthropic 3–5 dev-days incl. batch and tests; OpenAI a few hours (`angle2-alternatives.md` §2.2–2.3)
  **[EST]**. **Time:** about 1 week. **Cost:** Anthropic list price equals Bedrock global list price (Sonnet 5.5
  2 / 10 USD per MTok, Haiku 5.5 0.10 / 0.50, batch half of that); ~250 USD/month at today's volume, lower with batch
  and caching. No change to infra cost.
- **Risks:** foreign USD invoice (Stripe), no Vietnamese VAT e-invoice (accounting question: FCT under Circular 103)
  **[UNVERIFIED tax treatment]**; one more data processor (Anthropic; ZDR only via sales); key management (rotation,
  egress through the NAT instance). The same `anthropic` SDK adapter also serves Claude Platform on AWS
  (`AnthropicAWS`), Foundry and Vertex, so it is not throw-away work.

### E. acc2 leaves TrueIDC and joins eCloudvalley's Organization (or eCloudvalley Billing Transfer); Bedrock on acc2

- **Membership variant (E1):** acc2 leaves TrueIDC's org and accepts an invitation from eCloudvalley's management
  account. **Billing Transfer variant (E2):** identical to C2 above with eCloudvalley as the bill-transfer partner;
  Billing Transfer requires our own management account, so E2 = C2.
- **After the switch:** LLM calls can become same-account (acc2 `bedrock:InvokeModel`), and the satellite can be retired
  later (code: remove `bedrock_satellite.py` path, catalog `account_route`, Infra `bedrock_satellite_assume.tf` and
  `accounts/acc3-bedrock`). Keep acc3 as the LLM account until acc2 has real quotas: acc2 today has Sonnet 10 rpm,
  GPT Luna 0 tpm, Cohere 20 rpm, and AWS auto-declined a raise.
- **What happens to (per AWS docs and our inventory):**
  - Reserved Instances / Savings Plans: none on acc2, nothing lost.
  - Cognito, RDS, S3, ECS, DNS, secrets: unchanged (same account, same IDs). No user impact.
  - Credits: TrueIDC credits (if any) end with the membership **[OPEN]**; AWS Lift credits are on acc3, not acc2;
    under E1, eCloudvalley's credits apply to its own org billing; under Billing Transfer our side cannot see credit
    balances.
  - Support: acc2 has Basic support. Reseller-managed member accounts are often served by **partner-led support**,
    meaning technical cases go through the reseller **[UNVERIFIED for eCloudvalley; ask]**.
  - Invoices: TrueIDC invoices for usage up to the move; AWS keeps past invoices visible; Cost Explorer history from
    the TrueIDC era is lost (export first; `shared.cost_explorer_snapshot` keeps our own snapshots).
  - Agreements: org agreements accepted by TrueIDC on our behalf lapse (check AWS Artifact; none known to be needed).
  - Quotas: "may change" after leaving (AWS doc).
  - TrueIDC contract exit: notice period, final bill, and whether TrueIDC must perform the removal (SCP may deny
    `LeaveOrganization`) **[OPEN]**.
  - Anthropic authorization: eCloudvalley's press release covers "Taiwan and Southeast Asia"; written confirmation for a
    Vietnamese customer account and for Claude 5.5 in us-west-1 (incl. cross-region profiles) is required. acc3 did run
    Claude under eCloudvalley until 29/10, which is good evidence it works in practice.
- **Effort:** 2–4 engineer-days for E1 (checks, Bedrock enablement, quota requests, verification; satellite retirement
  later +2–3 days) **[EST]**. **Time:** 2–6 weeks (TrueIDC exit + eCloudvalley onboarding + quota raises).
- **E1 vs E2:** E1 is simpler on paper but recreates the acc3 situation: eCloudvalley's management account can reach acc2
  (and any SCP it sets applies to us), and when the contract or credit ends the account must leave again, with the same
  Error 002 risk, now on the account that holds all infrastructure. E2 (= C2) costs one extra empty account and gives a
  clean exit. **Prefer E2; accept E1 only with written exit terms** (notice, who removes the account, no SCP beyond
  billing, a named support path for Bedrock cases).

---

## 3. Option A: step-by-step migration plan (acc2 → acc3)

Assumptions: Dev only, test data, no real users (ADR 0012 Context); same region us-west-1; the RDS content (CIS
catalogue generated by paid LLM waves) must be preserved; CRM/Booking/TripPlanner test data may be re-seeded where
cheaper. All effort figures are **[EST]** engineer-days for one engineer plus agent.

| # | Step | What | Effort |
|---|---|---|---|
| 0 | Business preconditions | Reseller contract for acc3 (authorized for Claude), acc3 back under that payer, Error 002 lifted, AWS Support plan chosen, TrueIDC exit date agreed | 0.5 (calendar 1–4 weeks) |
| 1 | acc3 account baseline | Quotas: Fargate vCPU, EIPs, ALB, Lambda concurrency, CloudFront; SES production-access request (manual AWS review, ~1 day+); GuardDuty/CloudTrail/Access Analyzer via Terraform; budgets | 1.0 + waits |
| 2 | Terraform roots and state | New root `accounts/acc3-platform` (or retarget `aa365` with a new backend): new state bucket in acc3, replace account-ID literals (26 Infra files), provider/profile, `terraform.tfvars`; keep `aa365` state read-only for teardown later; bootstrap objects applied by a human with MFA (OIDC provider, 7+ CI roles, `aa-workload-boundary`, `aa-cis-infra-tf-apply-boundary`, agent session role) | 3.0–4.0 |
| 3 | Networking | VPC 10.x (new CIDR to allow a temporary peering if needed), subnets, NAT instance (new EIP: notify any third party that allow-lists 54.215.104.249 **[OPEN]**), SGs, VPC link, ALB/NLB | 0.5 (inside the apply) |
| 4 | IAM / OIDC / CI | GitHub OIDC trusts in acc3 with the same pinned subjects; update role ARNs in GitHub secrets/vars for 6 repos (27 workflows); DB Migrate / Schema Dump / migration-apply / isolation-probe workflows carry the account ID literally; `db-auto-apply` gate | 1.0–1.5 |
| 5 | ECR | Create 5 IMMUTABLE repos; copy only the running SHA per service (`crane copy` or ECR cross-account replication); then deploy each app from CI to prove the pipeline | 0.5 |
| 6 | Secrets and KMS | Script: read each of the 51 secrets in acc2 and write it in acc3 without printing (Terraform shells first, then values); new CRM keys `data`/`ingest`/`seal` with the same key policies; **CRM envelope keys:** either a one-off re-wrap job (temporary cross-account Decrypt on the old `data` key, local MFA key-policy edit, alarmed by design) or, simpler for Dev, re-seed CRM test tenants; keep the old seal public key for verifying existing PAdES seals | 1.5–2.0 |
| 7 | RDS | Rehearsal then cutover: snapshot → **copy re-encrypted with a CMK** (the instance uses `aws/rds`, which cannot be shared) → share CMK + snapshot to acc3 → copy under an acc3 key → restore (same engine 15.17, parameter group, subnet group, SG) → private DNS `db.dev.internal` → run DB isolation probe and schema dump; roles and passwords come with the snapshot, so DSN secrets keep working once the host changes. ~3.4 GB: copy + restore ≈ 30–90 min **[EST]** | 1.0–1.5 |
| 8 | S3 | Create the 17 buckets (Object Lock on the two CRM audit buckets, versioning, lifecycle, SSE); copy bronze (5.4 GB / 27k objects), CRM audit + documents, supply media, e2e mail with S3 Batch Operations or `aws s3 sync` under a cross-account bucket policy; do **not** copy tfstate or CloudTrail logs (export CloudTrail to an archive kept 1 year); rebuild TripPlanner artifacts from CI | 1.0 |
| 9 | Cognito | Recreate 4 pools, 11 clients, groups, resource servers, triggers, branding, WAF association via Terraform. **Users cannot be exported with passwords or TOTP seeds.** Recreate the 23 users by script (AdminCreateUser, suppressed invite) and send a reset; partner-pool users re-enrol TOTP. **Each user gets a new `sub`**: remap every DB column that stores the Cognito `sub` (staff directory, CRM membership, Booking/TripPlanner customer links) by e-mail **[OPEN: list the columns from `docs/architecture/db-schema-reference.md`]**. New pool IDs, issuers, JWKS URLs and client IDs go into ECS env, Lambda env, CIS M2M code constants (`api/core/m2m_auth.py`), and every Vercel project. Custom domains auth./staff-auth./partner-auth. can exist in one pool only: delete in acc2, then create in acc3 (sign-in down for ~15–60 min per domain) | 2.0–3.0 |
| 10 | SES | Verify the domain in acc3 (new DKIM CNAMEs), MAIL FROM, configuration sets, receipt rules (e2e mailbox, CRM ingest MX `crm-in.`), feedback SNS; production access (step 1) | 0.5–1.0 |
| 11 | API Gateway | 2 REST + 1 HTTP API, stages, VPC link, usage plans; import CIS tenant API keys with the same values (`import-api-keys`) so tenants keep their keys; custom domains api-cis., api-booking., api-tripplanner. need certificates in acc3 and a DNS switch | 1.0 |
| 12 | CloudFront | 4 distributions + VPC origin + function + OAC; aliases must be removed from the acc2 distribution (or moved with the alias-move procedure) before the acc3 one accepts them | 0.5–1.0 |
| 13 | Lambdas, schedules, alarms | 9 Lambdas (code from CI), 6 schedules, 13 rules, 88 alarms, SNS subscriptions (confirm e-mails), budgets, anomaly subscription, dashboards: all Terraform | 0.5 |
| 14 | ElastiCache | Recreate; cache only, warm on start | 0 (inside the apply) |
| 15 | DNS cutover | Lower TTLs 48 h before; create the `lumiguides.it.com` zone in acc3 with the 43 records pointing at acc3 targets; switch NS at the registrar (or keep the zone in acc2 temporarily and repoint records, then move the zone last); private zone `dev.internal` recreated | 0.5 |
| 16 | App code and catalog | CIS: `shared/aws_client/accounts.py`, satellite becomes same-account (delete the assume-role path or point it at the local role), LLM catalog `account_route` migration, Cost Explorer reader; TripPlanner gateway; Partner config; remove acc2 ID from the public-repo leak pattern only after decommission | 1.0–2.0 |
| 17 | Vercel and external config | Cognito IDs/issuers in all Vercel projects (Production + Preview), E2E credentials, Jira/Drive links unchanged | 0.5 |
| 18 | Rehearsal, cutover, verification | Full rehearsal with a throw-away restore; cutover day: freeze writes (scale workers to 0, empty job tables per DM-11.4), final RDS snapshot path, S3 delta sync, DNS + Cognito domain switch, deploy all apps, smoke per app (`/health`, `/health/ready`, Cognito E2E per pool, one CIS job, TripPlanner browse, CRM mail ingest, SES send) | 2.0 |
| 19 | Docs and ADR | New ADR (account change, amends 0001/0001a/0012 wording), Infra `CONTEXT.md`, generated docs regen, onboarding account map, secrets register, CLAUDE.md files, skills (`aa-cis-schema`, `aa-ship`, `ai-nghiep`), runbooks | 1.5 |
| 20 | Decommission acc2 | 2–4 weeks parallel read-only window; DRY RUN delete list approved line by line; keep CloudTrail archive; close account; TrueIDC final invoice | 1.0 |
| | **Total** | | ~~25–32~~ **33–43 engineer-days [EST, raised in §7.2]** |

- **Calendar time:** 5–7 weeks [EST] — 1–4 weeks of business/AWS waits (reseller, Error 002, SES production access,
  quotas) overlapping ~4 weeks of engineering, plus the parallel window before acc2 is closed.
- **Downtime window:** one planned window of **4–8 h [EST]** for writes (RDS final copy/restore + DNS + Cognito custom
  domains); user sign-in is down for the Cognito domain swap (~15–60 min per domain), and every user must reset the
  password (and TOTP for partner users) afterwards.
- **Parallel-run cost:** both stacks for 2–4 weeks ≈ +150–200 USD [EST]; same-region S3 copy has no transfer charge;
  snapshot copies and storage a few USD.
- **Rollback:** until the DNS/Cognito switch, abort costs nothing (acc2 untouched). After the switch, roll back by
  pointing DNS and the Cognito custom domains back to acc2 and replaying writes made in acc3 (Dev: accept loss of test
  writes made after cutover). Keep acc2 read-only and intact until the decommission step.

**Risk register for option A** (P = probability, I = impact; L/M/H)

| # | Risk | P | I | Mitigation |
|---|---|---|---|---|
| A-1 | acc3 stays Bedrock-blocked (Error 002) after the move, so the move buys nothing for LLMs | M | H | Make the reseller + AWS lift a precondition (step 0); do option D first |
| A-2 | Reseller lock-in: acc3 inside a reseller org again; when credit/contract ends it must leave, now with all infra | M | H | Only Billing Transfer through an AA-owned org; written exit terms |
| A-3 | Cognito `sub` remap misses a column; users lose data links | M | M | Generate the column list from the schema reference; dry-run remap; E2E per pool |
| A-4 | CRM envelope keys / seal: tenant data unreadable or seals unverifiable | M | M | Re-seed Dev CRM data, or tested re-wrap job; export old seal public key |
| A-5 | RDS snapshot not shareable (AWS-managed key) discovered on cutover day | L (known now) | H | CMK copy step in the rehearsal |
| A-6 | SES sandbox in acc3 blocks sign-up/invite mail | M | M | Request production access in week 1 |
| A-7 | CloudFront / Cognito / API custom-domain aliases cannot be attached while still on acc2 | H | M | Ordered removal in the runbook; short window |
| A-8 | Missed secret or hard-coded acc2 reference breaks a job silently | M | M | Scripted secrets copy with a name diff = 0; `git grep` of account ID; alarms in acc3 before cutover |
| A-9 | New NAT EIP breaks an IP allow-list at a third party | L | M | Inventory allow-lists **[OPEN]**; notify before |
| A-10 | Lift credits: thresholds measured per month on acc3; moving ~150–190 USD/month of infra plus ~250 USD LLM keeps acc3 under the 500 USD tier step | M | L | Do not plan around Lift tiers |
| A-11 | Data residency | L | L | Same region us-west-1; no change |
| A-12 | Security regression during the move (open bucket policies, cross-account KMS grants left behind) | M | H | Time-boxed cross-account grants with an alarm; Access Analyzer findings must be zero before decommission |
| A-13 | One engineer, 5–7 weeks of feature work lost | H | M | Choose C/E instead |

---

## 4. Options B, C, D, E: effort, time, risks, cost

| | B | C2 (= E2) | D | E1 |
|---|---|---|---|---|
| Engineering | 0–1 day | ~~3–6~~ **4–8** days (§7) | ~~3–5~~ **4–6** days (+ hours for OpenAI) (§7) | ~~2–4~~ **3–5** days (+2–3 later to retire the satellite) (§7) |
| Calendar | 1–4 weeks | ~~3–8~~ **4–10** weeks (1st-of-month start) | ~1 week | 2–6 weeks |
| Data moved | none | none | none | none |
| User impact | none | none | none | none |
| Monthly cost change | reseller fee on LLM only | reseller margin; AWS list price (no Claude/OpenAI discount) | none (list price; batch −50 %) | reseller margin |
| One-off cost | ~0 | engineer time; optional new management account (no charge for an empty account) | engineer time | engineer time |
| Removes vendor admin access to acc2 | no | **yes** | n/a | no (moves it to eCloudvalley) |
| Bedrock batch | still waits on acc3 case | new case for acc2 | **not needed** (Message Batches) | new case for acc2 |

**Risks specific to the payer change (C2 / E1 / E2)**

| # | Risk | P | I | Mitigation |
|---|---|---|---|---|
| E-1 | **Leaving TrueIDC triggers an account-level Bedrock block on acc2** (as happened on acc3 the same day it left), stopping native Cohere Embed v4 (embeddings) and the CRM scrub guardrail | M | H | Do D first; check whether Cohere Embed v4 is available directly from Cohere with compatible vectors **[OPEN]** or plan a re-embed; open an AWS case before the move; move at a quiet time with no waves |
| E-2 | acc2 Bedrock quotas stay tiny (Sonnet 10 rpm, GPT 0 tpm, Cohere 20 rpm; a raise was auto-declined) | H | M | Keep acc3 as the LLM account until raises land; request in small steps |
| E-3 | TrueIDC SCP denies `LeaveOrganization`, or the contract needs notice | M | M | Ask TrueIDC first; they can remove the account themselves |
| E-4 | acc2 root e-mail belongs to TrueIDC (account created inside their org) | L–M | H | Check on the console Account page **before** anything; change the root e-mail to a company address while still a member if needed |
| E-5 | Cost Explorer history lost; under Billing Transfer only pro forma cost data, no CUR, no Cost Anomaly Detection on our side | H | L | Export CE history first; our `shared.cost_explorer_snapshot` keeps snapshots; use budgets + `llm_call_log` for anomalies |
| E-6 | Reseller is not Anthropic-authorized for Vietnamese accounts, or blocks OpenAI by SCP / Private Marketplace | M | H | Written answers to the six questions before signing; test a real InvokeModel on a trial account |
| E-7 | Credits invisible to us (Billing Transfer); TrueIDC credits, if any, lost | M | L | Ask both vendors; model credits in Billing Conductor |
| E-8 | E1 only: eCloudvalley management access and SCPs over the account that holds all infrastructure; exit repeats the acc3 event | M | H | Prefer E2; if E1, exit terms in writing |
| E-9 | Support path: partner-led support may route Bedrock/quota cases through the reseller | M | M | Ask; consider AWS Developer/Business support on the account |

**Risks specific to D**

| # | Risk | P | I | Mitigation |
|---|---|---|---|---|
| D-1 | Accounting needs a Vietnamese VAT e-invoice | M | M | Ask the accountant about foreign invoices + FCT (Circular 103); otherwise reseller route for VND later |
| D-2 | New data processor (Anthropic / OpenAI) | L | M | Record in RoPA; request ZDR via sales if needed |
| D-3 | Policy: S235 "Bedrock-only" must be lifted by the tech lead | — | — | Decision item, not a technical risk |
| D-4 | Prepaid credits expire after 1 year | L | L | Small top-ups with auto-reload |

---

## 5. Decision items for the business owner

1. Approve option D now (company card on platform.claude.com and platform.openai.com; ~250 USD/month at list price,
   less with batch).
2. Approve creating an AA-owned AWS management account (no charge) and inviting acc3.
3. Ask Renova Cloud and eCloudvalley Vietnam for written answers: Anthropic authorization for a Vietnamese account
   (Claude 5.5 in us-west-1), OpenAI allowed, **Billing Transfer supported**, VND/VAT invoice, fees, exit terms,
   support path.
4. Ask TrueIDC: notice period, final invoice, who removes acc2 from their org, whether any credits or discounts end.
5. Do not start option A unless a reason other than LLM access appears (for example an auditor requiring a fresh
   account); if it does, revisit with ADR 0012 decision 12.

## 6. Open items to check (read-only, before any move)

- acc2 root e-mail owner (console, Account page).
- SCPs applied to acc2 by 033086823579 (ask TrueIDC; not readable from the member).
- IAM roles in acc2 that trust 033086823579 or are named `OrganizationAccountAccessRole` (the subagent hook blocks
  `aws iam` reads; run from the main session: `aws iam get-role --role-name OrganizationAccountAccessRole --profile aa365-admin`).
- Third parties that allow-list the NAT EIP 54.215.104.249.
- DB columns that store Cognito `sub` (only matters for option A).
- Current Bedrock batch minimum-records quota value (Bedrock quotas page) and acc3 case status.
- Whether Cohere Embed v4 is available directly from Cohere with vector compatibility (E-1 fallback).

---

## 7. Review (adversarial pass, S257, 29/10/2026)

Read-only review of §0–§6. Each item says what the draft missed or underestimated, the evidence, and the effect on the
ranking. **The ranking stands** (D now, then C2 / E2; A not recommended). The review widens the gap between A and the
others and adds preconditions to C2 / E. Estimates changed in place are marked "raised in §7" above.

### 7.1 Corrections to facts in the draft

| # | Draft said | Correct | Evidence |
|---|---|---|---|
| F-1 | Infra: 26 files name acc2; root: 7; app code: 0 | Infra **48 files / 119 hits** (≈28 operational: 4 workflows, 9 `accounts/aa365` .tf, 3 `accounts/acc3-bedrock` .tf trusting acc2, `modules/ecs/main.tf`, `db/owners.yaml`, 3 `tools/identity` scripts, tests, CONTEXT/README/agent-session docs; the other ≈20 are implementation notes). Root **148 files / 268 hits**: 15 operational (`tools/ecs/ecsx.sh`, `tools/ecs/ecsx_local.py`, 3 runbooks, secrets register .md + .yaml, 2 skills, `.claude/CLAUDE.md`, `.claude/settings.json`, steering `db-schema.md`, onboarding, DSAR runbook, Cognito research); the rest is history (90 audits, 33 Linear exports, sessions), leave as is. acc3 ID: Infra 13 files / 47 hits, root 21 files | `git grep -l 005097885195` / `786888028788` per repo, 29/10 |
| F-2 | App code holds no account-specific IDs | **Real Cognito pool IDs and client IDs are hard-coded as Dev defaults** in 7 source files: CIS `api/core/identity_config.py`, `api/core/m2m_auth.py`, `api/core/partner_identity.py`, `frontend/lib/cognito.ts`; Booking `backend/app/auth/identity_config.py`, `frontend/lib/cognito.ts`; TripPlanner `backend/shared/identity_config.py` (+ `frontend/lib/cognito.ts` client ID). 4 pools (`…bCcFvbSOS` workforce, `…nKOvHan0W` external, `…QZ9xcik2F` m2m, `…pjsHzdgOc` partner), 10 client-ID constants. Option A needs a code PR + merge queue + deploy in 3 app repos, not just env changes | `git grep -nE 'us-west-1_[A-Za-z0-9]{9}'` |
| F-3 | Cognito `sub` remap: "list the columns" **[OPEN]** | Closed: **8 tables in 4 schemas** hold `(iss, sub)`: `booking.customer_identities`, `booking.staff_users`, `crm.member`, `crm.member_invitation`, `crm.studio_invitation`, `shared.admin_users`, `shared.tenant_members`, `tripplanner.traveller_accounts`. **The `iss` changes too** (it embeds the pool ID), RLS policies (`crm.member_self_lookup`, tenant policies) match on `app.caller_iss`, and `booking.staff_users.cis_user_id` is derived (`'cog:' || sub`, check constraint `staff_users_cognito_key_chk`) and is referenced as an actor ID elsewhere (`cis_user_id` appears 80 times in the schema reference). The remap is 4 owner migrations (CIS, Booking, TripPlanner, CRM) through DB Migrate, timed to the cutover | `docs/architecture/db-schema-reference.md` (Verified 29/10 07:18 UTC) |
| F-4 | "Users cannot be exported with passwords" → every user resets | Partly wrong: the Cognito **Migrate user Lambda trigger** can move users at their next password sign-in (it checks the password against the old pool), so a forced password reset is avoidable. It cannot move TOTP seeds (partner pool, MFA required) and cannot keep `sub`; it needs `USER_PASSWORD_AUTH` enabled on the app client during migration, and the old pool must stay alive. Passwordless / e-mail-code flows (staff-auth managed login, AA-816) do not fire it. With 23 test users, a scripted re-create is still simpler | [Migrate user Lambda trigger](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-migrate-user.html) |
| F-5 | Security: "GuardDuty" listed as live | GuardDuty is **count-gated off** (`var.guardduty_enabled`, `security_guardduty.tf:51`); `aws guardduty list-detectors` in us-west-1 returns none. Security Hub not subscribed. CloudTrail is an account trail (not a TrueIDC org trail): good for E/C2, nothing org-managed to unwind | read-only CLI 29/10 |
| F-6 | Vercel: "every Vercel project" | 3 projects today (`aa-cis-frontend`, `aa-booking-admin`, `aa-tripplanner`). Option A changes **5 Cognito client secrets** (CIS admin, admin preview, breakglass; Booking staff, staff preview), `TP_COGNITO_*` keys stay (values are ours), preview `TRIP_API_URL` / `BROWSE_API_URL` point at execute-api IDs and change | Vercel env listing (names only) 29/10 |
| F-7 | Bedrock batch minimum records "typically 100" **[UNVERIFIED]** | Not re-verified here; irrelevant if D is chosen | — |

### 7.2 Hidden dependencies and constraints the draft underestimated (mostly option A)

| # | Item | Why it matters | Effect |
|---|---|---|---|
| R-A1 | **API Gateway custom domains are unique per Region across all AWS accounts** | `api-cis-aa365.`, `api-booking.`, `api-tripplanner.` cannot be pre-created in acc3 for a parallel run. Cutover = delete in acc2 → create in acc3 → base-path mappings → DNS, one domain at a time: an API outage per domain (≈10–30 min **[EST]**). Exception only through AWS Support. Same delete-first rule as the Cognito custom domains | Step 11 +0.5 d; one more cutover-day risk |
| R-A2 | **Cognito prefix domains** (`aa365-auth-dev`, `aa365-m2m-dev`, `aa365-partner-dev`, `aa365-staff-auth-dev`) are globally unique per Region | Same delete-first constraint as custom domains, or new names; the M2M token endpoint and any `COGNITO_*_DOMAIN` setting change with them | Inside step 9 |
| R-A3 | **CloudFront alternate-domain move across accounts** works only when the source distribution is **disabled** (or via a wildcard trick / AWS Support) | 4 aliases (img., partner-dev., go-dev., portal.) each go dark between "disable in acc2" and "attach in acc3" | A-7 probability stays H; window per alias |
| R-A4 | **Cognito sub/iss remap** (F-3) | 8 tables, derived key, RLS on `iss`, 4 owners, DB Migrate `apply` waits for all job tables (DM-11.4) | Step 9: 2–3 d → **4–6 d** |
| R-A5 | **Hard-coded Cognito constants in 3 app repos** (F-2) | Each repo: PR → CI → merge queue → deploy → live verify (aa-ship). Booking + CIS + TripPlanner + Partner env | Step 16: 1–2 d → **2–3 d** |
| R-A6 | **GitHub slots** | 14 secret/var slots carry acc2 identity: CIS `AWS_ROLE_ARN`, `E2E_MAIL_ROLE_ARN`, `ECR_REGISTRY` (+ `ECR_REPOSITORY`, `ECS_CLUSTER`, `ECS_SERVICE` names); Booking `vars.AWS_ROLE_ARN` (environment-scoped, not visible at repo level); TripPlanner `AWS_DEPLOY_ROLE_ARN`; Partner `vars.AWS_ROLE_ARN`, `E2E_MAIL_ROLE_ARN`, `SCRUB_CORPUS_ROLE_ARN`; Infra `AWS_ROLE_ARN`, `AWS_ACCOUNT_ALIASES`, `TF_STATE_BUCKET`; root `DOCS_SYNC_ROLE_ARN`, `DOCS_SYNC_BUCKET`. **Partner E2E secrets hold TOTP seeds** (`E2ECRMTOTP`, `E2ECRMASSISTANTTOTP`, `E2EPORTALTOTP`) and passwords for partner-pool users: a new pool means re-enrolling and rewriting them, or Partner CI goes red. Subagents cannot list secret values (hook); the orchestrator does this | Step 4 +0.5 d |
| R-A7 | **KMS keys die with the account** | CloudTrail archive (own CMK), any S3 object under the CRM `ingest` CMK, CRM envelope keys: after acc2 is closed its keys go with it (post-closure period ≈90 days). The "keep CloudTrail archive" step must re-encrypt (copy to SSE-S3 or an acc3 key) before closing; the S3 copy of `ingest`-encrypted objects needs a temporary cross-account `kms:Decrypt` grant | Step 20 +0.5 d; A-12 |
| R-A8 | **RDS: history does not move** | 44 manual snapshots and 7-day PITR stay in acc2 (each snapshot would need its own CMK re-encrypt + share + copy). Option: `pg_dump`/`pg_restore` of ≈3.4 GB through a DB-Migrate-style task avoids the KMS dance; the snapshot path keeps roles and grants exactly. Either way, after cutover the rollback point is the last acc2 snapshot | Note; no change |
| R-A9 | **ECR "running SHA only"** | Rollback to an older image becomes impossible in acc3; DB Migrate / Schema Dump / isolation-probe tasks use their own images; task definitions carry the acc2 registry host. Copy the last ~5 images per repo and every image a workflow references. ECR replication only copies **new** pushes, so existing images need `crane`/`skopeo` | Step 5 +0.5 d |
| R-A10 | **SES** | New Easy DKIM tokens per account (or BYODKIM to keep them), sending reputation starts at zero, production-access review | Covered by A-6; no change |
| R-A11 | **Route 53 zone** cannot be moved between accounts; registrar is Namecheap (`vendor:namecheap`), no DNSSEC (`dns.tf:16`) | NS switch at Namecheap is simple (no DS record to rotate). Alternative: keep the zone in acc2 during the parallel window and repoint records; move the zone last | No change |
| R-A12 | **Third parties holding config tied to acc2** | No federated IdP on any pool (no Google/Microsoft redirect URIs on Cognito). `crm/dev/mail-oauth` registers redirect URIs on our hostnames, unchanged if hostnames stay. No IP allow-list found for DataForSEO, Jev/Typesafe, Geoapify, Mapbox (URL-restricted) in docs or code; vendor consoles not checked **[OPEN]**. NAT EIP 54.215.104.249 would change | A-9 stays L |

**Option A total, re-estimated:** step 4 +0.5, step 5 +0.5, step 9 +2–3, step 11 +0.5, step 16 +1, step 18 +1–2 (two
rehearsals because of the delete-first domains), step 20 +0.5, docs/ops files (F-1) +0.5–1 → **33–43 engineer-days**,
**7–10 calendar weeks**, and **at least 7 short outages** on cutover day (3 API domains, 3 Cognito custom domains + 4
prefix domains, 4 CloudFront aliases) on top of the 4–8 h write freeze.

### 7.3 Underestimated in options C2 / E1 / E2 (the payer change)

| # | Item | Evidence | Effect |
|---|---|---|---|
| R-C1 | **The reseller's inbound Billing Transfer quota is 0 by default.** It must be raised by the partner's management account (granted "based on customer qualifications"). Ask: "Is your inbound Billing Transfer quota already above 0?" Our side may accept **one** outbound transfer at a time (not adjustable) and chain length is 1, so a reseller that itself sits under a distributor needs a chain-length raise | [Billing transfer quotas](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/orgs_transfer_billing-quotas.html) | New must-ask question (Decision item 3) |
| R-C2 | **AWS-direct gap.** The transfer starts at 00:00 UTC on a 1st. Between acc2 joining our org and that date, **our new management account pays AWS directly by card** and acc2/acc3 are AWS-direct, like acc1, which can call Claude 4.x but not 5.5/OpenAI. A brand-new payer with no history may also get low Marketplace/Bedrock trust. Plan to move acc2 in the **last days of a month**, after the invitation is accepted (≥ 24 h before the 1st) | [Billing transfer](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/orgs_transfer_billing.html) | Calendar +up to 4 weeks; included in 4–10 weeks |
| R-C3 | **acc2 has no billing access of its own today.** The secrets register lists "AWS payer / billing console (TrueIDC) — console access via TrueIDC". Leaving needs a valid payment method on acc2 and **"IAM user access to billing" activated by the root user**: root credentials must be recovered first (ties to E-4) | `docs/security/secrets-register.md` vendor row `vendor:trueidc`; [LeaveOrganization](https://docs.aws.amazon.com/organizations/latest/APIReference/API_LeaveOrganization.html) | C2 +0.5–1 d; a hard precondition |
| R-C4 | **Error 002 may be a payment-instrument flag, not "leaving" as such.** acc3 left when its test credit ran out and had no valid Marketplace payment method. Mitigation: card verified on acc2 **before** it leaves, Marketplace subscriptions checked right after, AWS case pre-opened | §2 fact 4; [model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) | Sharpens E-1 mitigation |
| R-C5 | **Marketplace subscriptions and the Anthropic FTU are per account / per management account.** Under a new org the FTU may need resubmitting at our management account; the Cohere Embed v4 subscription on acc2 (Marketplace) must be re-checked the same hour, since embeddings and the CRM guardrail run on it | [Multi-account Bedrock entitlements](https://aws.amazon.com/blogs/machine-learning/simplify-multi-account-access-to-amazon-bedrock-models-with-managed-entitlements/) | Add to C2 step 7 |
| R-C6 | **Credits.** AWS Lift credits sit on acc3. Promotional credits are often excluded for reseller-billed accounts, and under Billing Transfer our side cannot see balances at all. Joining acc3 to an org whose bill is transferred may forfeit them **[UNVERIFIED, ask AWS before inviting acc3]** | Billing transfer "Credit tracking restrictions" | Decision item 2 gets a pre-check |
| R-C7 | **Billing Conductor** is required for console setup of a transfer and is charged to the partner, who may pass it on; pro forma data excludes support charges, credits and free tier | Billing transfer doc | Ask in fee question |
| R-C8 | **Reseller contract terms are not public.** No eCloudvalley or Renova end-customer terms were found. Must get in writing: minimum monthly commit or deposit, contract term and early-exit fee, markup on Marketplace models (AWS gives resellers no discount on Claude, so margin = markup or fee), credit conditions (lock-in months), whether the partner requires membership in its org (E1) or supports Billing Transfer (E2), root e-mail ownership, SCPs it applies, account hand-back on exit, partner-led vs AWS-resold support for Bedrock / quota cases, VND/VAT invoice and FCT handling | web search 29/10 (no public terms); [AWS Resold Support](https://aws.amazon.com/premiumsupport/aws-resold-support/) | Expands Decision item 3 |
| R-C9 | **TrueIDC-side unknowns** stay the critical path: SCP on `LeaveOrganization`, root e-mail owner, `OrganizationAccountAccessRole`, notice period. `aws organizations describe-account` and `iam` reads are denied / hook-blocked from here | §6 | No change; still first |

**E1 note (the tech lead's "move acc2 into eCloudvalley's org"):** technically the cheapest switch (no new account), but
it puts the account that holds all infrastructure under a vendor management account that can apply SCPs and reach in
with its access role, and the exit path is exactly the acc3 event of 29/10. Accept only with R-C8 answered in writing.
Effort raised to 3–5 days because R-C3 / R-C5 apply equally.

### 7.4 Underestimated in option D (direct APIs)

| # | Item | Evidence | Effect |
|---|---|---|---|
| R-D1 | **New Anthropic orgs may start in an "Evaluation" tier** below the standard limits; the Start tier has a **500 USD/month spend cap**, after which every request returns 429 until the 1st of next month (SDK retries do not help). ~250 USD/month fits, but a rerun wave month can cross it. Request a tier raise before the first wave; set our own workspace limit below the cap and alarm on `enforced_spend_limit_reached` | [Rate limits](https://platform.claude.com/docs/en/api/rate-limits) | New risk D-5 (M/H) |
| R-D2 | Message Batches limits are fine for us: Start tier 1,000 RPM, 200,000 requests in the processing queue, 100,000 per batch | same | Confirms the batch answer in §0 |
| R-D3 | **OpenAI has its own Batch API** (JSONL file upload, 24 h window, 50 % off), so "batch is easier on direct APIs" holds for both vendors, not only Anthropic | OpenAI docs (not re-fetched) **[UNVERIFIED current terms]** | Note |
| R-D4 | Work missed in the 3–5 d: `llm_call_log` pricing rows and `/admin/llm-usage` attribution for `provider='anthropic'` (cost discipline, AA-635), a batch-poll job kind with retry/idempotency in `shared.job`, 2 new secrets in the register, TripPlanner gateway port, egress through the t4g.nano NAT instance (batch result files up to hundreds of MB) | CIS CONTEXT.md, secrets register | 3–5 d → **4–6 d** |

### 7.5 Verified as stated

Billing Transfer mechanics in §2 fact 3 (management-account-to-management-account, invitation from the bill-transfer
side, 1st-of-month start, accept ≥ 24 h before, withdraw anytime with end of current/next month, loss of CUR / Cost
Anomaly Detection / AWS-priced data, credits invisible, RI/SP per org), the RDS AWS-managed-key sharing limit, the SES
sandbox for new accounts, the Route 53 no-transfer constraint, and the zero reservations on acc2.

### 7.6 Additions to §5 decision items and §6 open items

- Decision 3 (resellers): add "Is your inbound Billing Transfer quota above 0?", "minimum commit / deposit / term /
  exit fee", "markup on Claude and OpenAI Marketplace usage", "who holds the root e-mail and what SCPs you apply".
- Decision 2 (management account): first ask AWS whether acc3's Lift credits survive joining an org that later uses
  Billing Transfer (R-C6).
- Before acc2 leaves: recover acc2 root access, activate IAM billing access, add and verify a company card (R-C3/R-C4);
  schedule the leave for the last days of a month (R-C2).
- Option D: request an Anthropic tier raise on day 1; set a workspace spend limit and an alarm (R-D1).
- Vendor consoles (DataForSEO, Jev/Typesafe, Geoapify): confirm no IP allow-list on 54.215.104.249 (R-A12).
