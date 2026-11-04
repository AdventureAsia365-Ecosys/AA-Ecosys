# AA-1028 R1: plan drives the agency's CRM seats and features, live on Dev (S267, 04/11/2026)

Agent: Claude Code (orchestrator). Cost: 0 USD (no LLM, no paid API). Tenant: the synthetic E2E tenant
**Atlas & Hearth** (`atlas-hearth`, kind `demo`), which is also a CRM agency.

## Steps and results (times UTC)

| # | Step | Code path | Result |
|---|---|---|---|
| 1 | Before: subscriptions of Atlas & Hearth | `shared.tenant_subscription` | `content.growth` only, no CRM add-on |
| 2 | Attach `crm.core` | `tenant_provision` saga (`services.jobs.tenant_provision_job.enqueue_request`, mode `attach`), run in the live `aa-cis-dev-api` container | job `a7bf8afa…` **succeeded**, steps `crm_subscribed`; `v_tenant_entitlement_v1`: `crm.ai_assist`, `crm.core`, `crm.seats` = 10 |
| 3 | CRM projection | `crm_entitlement_pull` (every 2 min) | `crm.tenant_entitlement`: plan `core`, `member_limit` 10, `allowed_features` `[ai_assist]`, `projected_at` 01:40Z |
| 4 | Feature gate | `app.entitlements.require_feature` in the live `aa-crm-dev-api` container (`system_tx` on the agency) | `ai_assist` allowed; `whatsapp_sms` → **403 `feature_not_allowed`** ("SMS and WhatsApp is not on this agency's plan") |
| 5 | Admin creates a plan | `services.tenant_account.plans.create_plan` (the code of `POST /admin/plans`) | `crm.e2e_s267` v1: seats 3, features `crm.core`, `crm.ai_assist`, `crm.whatsapp_sms`, not public |
| 6 | Assign it | saga `attach` | job `fe027e19…` succeeded; view: seats 3 + `crm.whatsapp_sms` |
| 7 | CRM follows | pull, then the gate | `member_limit` **3**, `allowed_features` `[ai_assist, whatsapp_sms]` (01:46Z); `whatsapp_sms` now allowed by the gate |
| 8 | Back to `crm.core` | saga `attach` | job `ea1f17a2…` succeeded; view: seats 10, no SMS |
| 9 | Retire the test plan | `plans.retire_plan` (the code of `POST /admin/plans/{key}/retire`) | `crm.e2e_s267` retired (no subscriber) |
| 10 | CRM follows back | pull | plan `core`, `member_limit` **10**, `allowed_features` `[ai_assist]` (02:16Z), the state in which step 4 refused SMS |

Left as it is after the check (on purpose): Atlas & Hearth keeps the `crm.core` add-on, so the CRM agency is now
managed by CIS (`managed_by` cis).

## Screenshots (CIS admin, E2E admin, read-only session)

`01-plans-*`: Plans & add-ons (1440 + 390, light + dark). `02-plan-crm-core-drawer-1440-light`: the `crm.core` plan
(10 seats, features). `03-atlas-subscription-*`: Tenant 360 › Subscription of Atlas & Hearth with CRM Core active
since 4 Nov 2026. `04-atlas-entitlements-*`: the resolved entitlements.

## Not tested live

- The 403 is checked on the CRM's own gate function inside the live container, not through an HTTP call by a signed-in
  agency user: no partner-pool E2E user belongs to Atlas & Hearth, and creating one adds a Secrets Manager secret
  (~0.40 USD/month, needs its own yes). The HTTP mapping of `Forbidden` → 403 is covered by the CRM unit tests.
- The plan was created and assigned through the service code the admin routes call, not by clicking Save in the UI
  (the E2E admin session is read-only by design).
