---
id: OPS-08-s265-live-verify-f3
title: "S265 live verify: AA-1027 F3 CRM AI draft card"
description: "Agent-run Playwright evidence on Dev for AA-1027 slice F3 (AA-Partner #194, crm-040): the L1 allowance step and the CRM trip AI draft card, at 0 USD."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-03
review_every_days: 30
related: [AA-1027]
---

# AA-1027 F3 live verify (03/11/2026, 01:37–01:42Z)

Headless Chromium (Playwright from the AA-CIS-App checkout). CRM web on `portal.` (`/healthz` `ba3eec91`, includes
Partner #194). Identities: the Dev-only E2E CIS admin (read-only session) on `aa-cis.`; the e2e **owner** of the
synthetic agency "Lữ hành Sen Vàng" on the CRM web. Codes and secrets read at run time, never written down. Raw records
in [`data/`](data/) (ids replaced by `<uuid>`). Light theme, 1440x900 and 390x844.

## Results

| Step | Result | Shots |
|---|---|---|
| 1. CIS Platform > Agencies > Sen Vàng > Features allowed: allow `ai_assist` (ticket "AA-1027 F3 live check S265") | **FAIL (blocked by design)**: `/console` answers `can_write: false`; banner "Read only: your staff account is not in the crm-platform-admin group, so the actions are hidden."; the six feature boxes are disabled, no Save button. The same PUT sent through the page's BFF (`…/entitlements-allowed`) answers **403 `e2e_read_only`**; `features_allowed` stays `[]` before and after | `01-cis-agency-features-before-1440-light.png`, `01-cis-agency-features-after-{1440,390}-light.png` |
| 2a. Trip AI draft card, AI off | **PASS**: Draft disabled, reason "The AI assistant is not on your agency's plan. Ask AA support to add it." (state `no_plan`: the plan check comes before the AI switch, as designed) | `02-crm-ai-draft-initial-{1440,390}-light.png`, `02a-crm-ai-draft-ai-off-{1440,390}-light.png` |
| 2b. Trip AI draft card, AI on | **Not reached** (needs step 1): with AI switched on (Settings > AI saved, status ON) the card still says `no_plan` and Draft stays disabled, correct for a plan without `ai_assist`. The enabled button and the drawer were not seen | `02b-crm-settings-ai-on-1440-light.png`, `02b-crm-ai-draft-ai-on-{1440,390}-light.png` |
| 3. Draft click at 0 USD | **Not clicked**. CRM API task def `aa-crm-dev-api:120` has no `CRM_LLM_PROVIDER` (stub model, 0 USD; `test_mode` true) but has `SCRUB_GUARDRAIL_ID` set, so the gateway uses the real scrubber: every draft calls Bedrock `ApplyGuardrail` on acc2 (USD 0.0001 per text unit, `crm_scrub` rows). That is a paid call, so even with the button enabled it must not be clicked under the 0 USD rule. The stage route (crm-037 seed) is Bedrock Haiku 4.5 → Sonnet 4.5, played by the stub | — |
| 4. Restore | **PASS**: AI switch back off (as found); `ai_enabled` false, `ai_assist_allowed` false, spend USD 0.0000 | `04-crm-settings-ai-restored-1440-light.png`, `02-crm-settings-ai-initial-1440-light.png` |
| 5. Layout + console | **PASS**: no overflow at 390 (document and `main` 390/390) on the trip page; console errors 0 on the CRM web; CIS: 1 console error = the browser's log line for the expected 403 of the step 1 probe | all of the above |

No draft request (`/ai/draft`) was sent during the run (request hook recorded none).

## Findings

- **F1 — Nobody the agent can sign in as can allow a feature.** The L1 write needs WORKFORCE group
  `crm-platform-admin`; the E2E CIS admin is read-only and lacks the group, and the E2E CRM staff user has only
  `crm-ops` + `crm-support`. Step 1, and therefore 2b and 3, need a person in `crm-platform-admin` (the tech lead) to
  allow `ai_assist` for Lữ hành Sen Vàng in CIS admin, or a sanctioned E2E allow-list entry for
  `PUT /admin/platform/crm/agencies/{id}/entitlements-allowed` on synthetic agencies (same shape as A10b-1).
- **F2 — "Test mode … nothing is charged" is not exact on Dev.** `test_mode` is `provider == "stub"`
  (AA-Partner `api/app/llm/agency_ai.py`), but with `SCRUB_GUARDRAIL_ID` set the scrub still pays `ApplyGuardrail`
  units on acc2 for each draft (`api/app/llm/gateway.py` `build_gateway`, `api/app/privacy/guardrails.py`). The copy
  in `web/lib/i18nAi.ts` (`ai.testModeHelp`) and `web/lib/i18nAiDraft.ts` (`aiDraft.testMode`) says no charge. Cost is
  tiny (about USD 0.0001 per short message) but the sentence is wrong; either say "the model costs nothing; the
  personal-data check is billed" or derive `test_mode` from both the provider and the scrubber.
- **F3 (minor UX)** — Settings > AI lets the owner switch AI on and shows status ON while the plan lacks `ai_assist`;
  only the trip card says the plan is missing. A line on Settings > AI ("not on your plan") would avoid the confusion.
