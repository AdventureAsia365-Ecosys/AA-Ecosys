# AA-1027 slice F3 — CRM AI draft, live verify on Dev (S265, 03/11/2026)

Scope: AA-Partner #194 (AI draft card + drawer) and #201 (AI settings copy, plan state), CRM web/api `0997e46b`
(`/healthz` git_sha `0997e46be43f…`). Run as the e2e owner of the synthetic agency "Lữ hành Sen Vàng" on
`portal.lumiguides.it.com`, Playwright headless Chrome, light theme. The tech lead allowed `ai_assist` for the agency
and approved exactly one "Write draft" click (stub model, 0 USD; only the privacy scrub is billed).
A route guard in the harness let at most one draft POST reach the API; one was sent.

| Step | Result | Evidence |
|---|---|---|
| 1. BFF `GET settings/ai`: `ai_assist_allowed` | PASS: `true` (provider `stub`, `model_test_mode` true, `scrub_billed` true, budget USD 2.00) | `data/crm-draft-results.json` |
| 2. AI switch found **off** → switched on in Settings > AI (PUT 200) | PASS: no "not on your plan" banner, test-mode note says the privacy check is billed | `01-settings-ai-initial-1440.png`, `02-settings-ai-on-1440.png`, `02-settings-ai-on-390.png` |
| 3. Trip "Việt Nam, 9 đêm": AI draft card `data-state=ready`, Draft enabled; drawer opens | PASS | `03-trip-ai-draft-card-1440.png`, `03-trip-ai-draft-card-390.png`, `04-drawer-open-1440.png`, `05-drawer-filled-1440.png` |
| 4. One "Write draft" click (kind Reply, text "Could we add one more day in the old town?") | PASS: draft in 1.4 s, AiNotice `data-ai-notice=staff`, drawer test-mode note, `ai_draft_id` present, Copy and accept + Discard visible | `06-draft-result-1440.png`, `06-draft-result-390.png` |
| 4b. Discard with feedback "other" (no paid call) | PASS: POST discard 200, `decision=discarded`, `feedback_code=other` | `07-draft-discarded-1440.png` |
| 5. Switch restored to **off**, `ai_assist` still allowed | PASS: PUT 200, final GET `ai_enabled=false`, `ai_assist_allowed=true` | `08-settings-ai-restored-1440.png` |

## Draft response (`POST /bff/trips/<trip>/ai/draft`, text left out)

Status 200. `outcome=ok`, `ai_draft_id` present, `llm_call_id` present, `fallback`/`refusal_code`/`error_class` null,
`truncated=false`, `approval_required=true`, `budget_used_pct=0`, `budget_alert=null`. Request body keys: `kind`, `text`.
The response carries no provider/model label; the provider shows as `stub` in `GET settings/ai`. The draft text is the
stub's marker (24 characters).

Cost: `spent_usd_month` went from `0.0000` to `0.0001` (the privacy scrub). The Settings meter rounds it to "USD 0.00".

## Console, network, layout

- Console errors: 0. Page errors: 0. Responses ≥ 400 from the CRM origin: 0.
- Overflow at 390: Settings > AI 390/390, trip page 390/390, drawer 349/349 (no horizontal scroll). 1440: 1440/1440.

## Notes

- The red "A mailbox is disconnected" banner on the agency is unrelated to F3.
- Raw results: `data/crm-draft-results.json`. Harness (not committed): `.tmp-session/S265/f3-verify/crm-draft.spec.ts`.
