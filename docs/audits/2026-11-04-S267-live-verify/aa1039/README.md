# AA-1039 R6 slice 3 (Writing Lab per stage, one Spend page, AI gateway name), live on Dev (S267, 04/11/2026)

Merged: CIS #1286 (`7f5a9f72`, the stage read API) and #1287 (`6dd79a8b`, the pages). Deploys: CIS api + worker
COMPLETED on `6dd79a8b`; Vercel production of the CIS admin succeeded.

## API (run in the live api container, `services.writing_memory.lab.stage_view`, $0)

All four writers (`a1`, `t2`, `t9_blog`, `t9_social`): the five sections samples / labels / experiments / prompts /
gate are `ready: true`, no error. Gate state `reverify` (inputs changed since approval: golden_set, model_route,
prompt_version_mismatch) for each, with `active_eval` = the live release's baseline; no false `regression` from another
release's run (the fix-pass finding). Samples: a1 55, t2 20, t9_blog 23, t9_social 36 golden items; prompt versions 6 / 5
/ 8 / 8.

## UI (E2E CIS admin, Cognito, read-only session)

Redirects: `/admin/writing-memory` → `/admin/lab/writing-memory`; `/admin/cost-ops` → `/admin/spend`;
`/admin/platform/cost` → `/admin/spend?tab=apps`; `/admin/llm-usage` → `/admin/spend?tab=spend`; `/admin/lab` →
`/admin/lab/a1-s1`. Console errors: 0.

Screenshots: `lab-t9-social-*` (1440 + 390, light + dark; each tab). The `spend-*` and `spend-apps-*` shots show the AWS account IDs on the Spend page, so they are kept out of this public repo (orchestrator scratch only).

Seen in the shots (follow-up, small): the gate tiles break a long value mid-word ("informat / ive") and cut long tile
titles ("Tenant releases li…").

Left on AA-1039: the retire → restore live check (needs a live E2E post on a new WordPress test site), the portal
`needs_change` view (after the R3 cut-over), the `ai_ops` logged read of tenant text (R2 slice 2).
