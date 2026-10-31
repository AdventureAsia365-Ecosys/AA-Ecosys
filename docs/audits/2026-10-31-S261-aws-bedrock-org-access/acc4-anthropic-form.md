---
id: OPS-08-s261-acc4-anthropic-form
title: "Anthropic use-case form for the management account (acc4), CloudShell steps"
description: "Lệnh CloudShell để kiểm và nộp form use case của Anthropic từ account quản lý (acc4) bằng API, cho các account trong org thừa hưởng; nội dung form tiếng Anh."
type: how-to
status: active
owner: nghiep
audience: [engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 90
related: [AA-1004, docs/audits/2026-10-31-S261-aws-bedrock-org-access/README.md]
---

# Anthropic use-case form for acc4 (management account)

acc4 was set up in S259 (organization, 3 OUs, 3 SCPs, org trail, budgets, Identity Center us-west-1, CI OIDC). The local
bootstrap profile was removed after bootstrap, so run these in **AWS CloudShell** of acc4 or locally with the `aa-mgmt` profile (Identity Center sso-session `aa-mgmt-sso`, added S261) (access portal →
acc4 → AA-Admin → CloudShell, region us-west-1). Submitting **through the API from the management account** lets member
accounts inherit the form (AWS security blog 2025; the current user guide says the root account's form is inherited).
acc3 and acc2 already have their own forms; joining the org does not remove them.

1. Check whether a form exists (an error "not found" means none):

```bash
aws bedrock get-use-case-for-model-access --region us-west-1
```

2. Write the form (English, covers internal and customer-facing use):

```bash
cat > ftu.json <<'JSON'
{"companyName":"Adventure Asia","companyWebsite":"https://adventure.asia/","intendedUsers":"0","industryOption":"Other","otherIndustryOption":"Travel and tourism","useCases":"Adventure Asia is a soft-adventure tour operator across Southeast Asia, expanding into B2B services for small travel agencies in Europe, Australia and the US. We use Claude to rewrite and quality-check our tour content, to draft blog and social posts for partner agencies in their brand voice (always reviewed by staff before publishing), to suggest replies to client emails inside a CRM for travel agencies (personal data is removed before any model call), and to power an AI trip planner that composes itineraries from our own tour catalogue. Outputs are labelled as AI-assisted where shown to travellers. No medical, legal or financial advice."}
JSON
```

3. Submit the **raw JSON** (sending base64 returns "Invalid form data"; the service stores it base64-encoded, which is why `get` needs two decodes):

```bash
aws bedrock put-use-case-for-model-access --form-data fileb://ftu.json --region us-west-1
```

4. Verify, then check a member after it joins (`agreementAvailability.status` must be AVAILABLE):

```bash
aws bedrock get-use-case-for-model-access --region us-west-1 --query formData --output text | base64 -d | base64 -d
```

```bash
aws bedrock get-foundation-model-availability --model-id anthropic.claude-sonnet-4-6 --region us-west-1 --profile nghiep_aa365
```

Note: `intendedUsers` "0" mirrors the value on acc3's existing form; if the console offers a choice between internal
and external users, pick the one that includes external customers.

## Done (S261, 31/10/2026 ~06:15Z)

Submitted from the `aa-mgmt` profile (AA-Admin). Read back: companyName Adventure Asia, industry Other / Travel and
tourism, English use cases. `get-foundation-model-availability` for Claude Sonnet 4.6 on acc4: authorization AUTHORIZED,
agreement NOT_AVAILABLE (the Marketplace agreement is created on an account's first model call; acc4 runs no models).
