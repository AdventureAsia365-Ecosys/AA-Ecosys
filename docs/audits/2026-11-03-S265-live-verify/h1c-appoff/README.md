# AA-1025 H1c — CRM app AI off, live verify on Dev (S265, 03/11/2026)

Scope: AA-Partner #202 (migration crm-041, `crm.llm_app_profile`) and #203 (CRM gateway acts on the app profile).
CRM web `/healthz` git_sha `3dd029e3e0fd…` (= AA-Partner `main` #203). Before the run the tech lead switched AI **off**
for the whole app "crm" in CIS admin (`crm.llm_app_profile.ai_enabled=false`, confirmed by the orchestrator).
Run as the e2e owner of the synthetic agency "Lữ hành Sen Vàng" on `portal.lumiguides.it.com`, Playwright headless
Chrome, light theme. Exactly one "Write draft" click; a route guard let at most one draft POST reach the API (one was
sent, none aborted).

| Step | Result | Evidence |
|---|---|---|
| 1. BFF `GET settings/ai` | PASS: 200. Fields: `ai_enabled`, `ai_budget_usd`, `budget_max_usd`, `spent_usd_month`, `budget_used_pct`, `alert_level`, `period_start`, `provider`, `test_mode`, `model_test_mode`, `scrub_billed`, `rate_limit_per_minute`, `can_edit`, `ai_assist_allowed`. **No app-level field**: the agency cannot see that AA paused AI for the whole CRM. | `data/crm-appoff-results.json` |
| 2. Agency AI switch found **off** → on in Settings > AI | PASS: PUT 200, GET `ai_enabled=true` | `01-settings-ai-initial-1440.png`, `02-settings-ai-on-1440.png` |
| 3. Trip "Việt Nam, 9 đêm": card `ready`, drawer, kind Reply, invented client text, one "Write draft" click | PASS: refused in 0.8 s, `app_disabled`, no draft text; the drawer says "AI drafts are paused by AA for now. Write this reply by hand." | `03-drawer-refused-1440.png`, `03-drawer-refused-390.png` |
| 4. Agency AI switch back **off** (as found) | PASS: PUT 200, final GET `ai_enabled=false`, `ai_assist_allowed=true` | `04-settings-ai-restored-1440.png` |

## Refusal response (`POST /bff/trips/<trip>/ai/draft`)

HTTP 200 with `outcome=refused`, `refusal_code=app_disabled`, `error_class=disabled`, `fallback=manual_reply_needed`,
`ai_draft_id=null`, `llm_call_id=0c7b9e2a-f7ca-49f6-b476-1f45175e89c3` (the refused 0 USD ledger row),
`budget_used_pct=null`, `budget_alert=null`, `truncated=false`, `approval_required=true`, no `text`.
Request body keys: `kind`, `text`.

## Cost: 0 USD

`spent_usd_month` was `0.0001` before the click and `0.0001` after it (the 0.0001 is the F3 run's privacy scrub
earlier today). The refused call added nothing, so the privacy scrub (Guardrail) was not called and no model was
called. The ledger row itself (`crm.llm_call` for the `llm_call_id` above) was not read in this lane (no DB access
here); a DB read can confirm `cost_usd=0`, `outcome=refused`, `refusal_code=app_disabled`.

## Console, network, layout

- Console errors: 0. Page errors: 0. Responses ≥ 400 from the CRM origin: 0.
- Drawer at 390: doc 390/390, main 390/390, drawer 349/349 (no horizontal scroll).

## Observations (not failures)

- After the refusal the button reads "New draft"; the guard confirms it was not clicked again.
- The drawer's test-mode note still says "Only the privacy check is billed" while AI is paused for the whole CRM; with
  the app off nothing is billed. Wording only.
- Settings > AI shows the agency switch on with no hint that AA paused AI for the whole CRM (see step 1); the owner
  finds out only when a draft is refused. A possible follow-up: expose the app-level state in `GET settings/ai` and
  show a banner.

Raw results: `data/crm-appoff-results.json`. Harness (not committed): `.tmp-session/S265/f3-verify/crm-appoff.spec.ts`.
