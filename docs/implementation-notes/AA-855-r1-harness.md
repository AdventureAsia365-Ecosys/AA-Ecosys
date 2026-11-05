# AA-855 — UAT round-1 harness (catalogue, pilot guard, studio editor identity, Content + CRM scenarios)

Lane aa855-r1-harness (S270, Claude Code). Root repo, branch `feat/aa855-r1-harness`. Round `R1-2026-11` = Content +
CRM in the one agency app (portal host: `/portal/*` = Content, the `(crm)` routes = CRM).

## Decisions

- **One catalogue, validated.** `tools/uat/catalogue.json` holds one row per scenario id (93 rows: every existing id,
  the S260 plan ids, the S268 additions, the CRM review chapters and its two data steps). `lib/catalogue.cjs` validates
  types, id rules (`.m`, `@role`, split letters, `CRM-REV-NN`), statuses, kinds, identities, safe file paths and "no
  internal issue id in story / note". Optional fields: `file`, `note`, `issues`. Kinds add `data` for the
  never-recorded prep / cleanup steps; `release` is accepted (S268 lists it).
- **Catalogue tests tie three things together**: every scenario module has a row naming its file, app and identity;
  every row's file exists; every dry-run manifest entry is `live`, writes nothing, costs nothing and has the same
  identity; retired ids are never in the manifest nor in a round.
- **Pilot guard, fail closed, two layers.** `lib/pilot-guard.cjs` reads the active tenant through the app's own API:
  Content `GET /api/tenant/me` (`tenant_id`, `tenant_name`; AA-Partner `web/app/api/tenant/me/route.ts`) and CRM
  `GET /bff/me` (the BFF forwards `/crm/v1/me`: `tenant_id`, `display_name`; `api/app/routers/agency.py`). Neither
  returns `is_pilot` today; the rule still refuses `is_pilot` not false, a `pilot_ends_at`, `is_synthetic` not true and
  `kind` pilot / real when present, so a later API field tightens it with no change here.
  - Layer 1: the dry-run runner checks each identity once after sign-in (its own headless Chromium); a refusal marks
    that identity's scenarios BLOCKED (`pilot_guard`) and the run exits 5.
  - Layer 2: `record.cjs` checks every signed-in scenario in a separate, unrecorded context BEFORE the recorded context
    exists, writes `result.json` verdict BLOCKED and exits 5. `run.sh` calls `record.cjs --guard-only` before the TTS
    and stops on any non-zero exit; a 5 after the take also stops before the build.
- **Allow-list.** Built in: the invented display names of the four E2E Content tenants and the three CRM review
  agencies; the CRM agencies also by id, computed as UUIDv5 of their key with the namespace already public in AA-Partner
  `api/app/seed/catalogue.py` (no id literal in this repo). Local, gitignored `tools/uat/work/uat-allowlist.json` (env
  `UAT_ALLOWLIST`) pins ids per slug; a pinned slug then matches by id only; `"builtin": false` refuses every tenant
  (the negative check). A refusal names the tenant by the first 8 characters of its id, never by name.
- **Scopes.** studio / studio-editor -> content, crm -> crm, AA staff identities -> none (their tenant lists are blurred
  per scenario), a CRM-app scenario with a session -> crm; `scenario.pilotGuard = { scopes, only }` overrides; a
  signed-in scenario with no determinable scope throws (fail closed). CRM prep / cleanup set `only: ['sen-vang']` and
  also assert it from inside their first step (`_crm.cjs assertReviewAgency`) before any write; an in-step guard
  failure also exits 5.
- **Tenant lists on AA staff pages.** `scenario.allowRows = { rows, allow }` blurs every row outside the synthetic
  names before the first paint; `h.assertRowsFiltered()` fails a step when such a row shows unblurred. Applied to
  CIS-06 (`/admin/tenants`).
- **studio-editor identity.** Mirrors `studio`; secret `crm/dev/e2e-test-studio/editor` (`UAT_STUDIO_EDITOR_SECRET`),
  state `work/dryrun/.state-studio-editor.json` (600). The secret is read before any browser starts; a missing secret
  is a one-line BLOCKED reason (`lib/crm-signin.cjs secretError`: the CLI text, which may carry an ARN, is never echoed).
  It is a WRITABLE identity (only with `--include-writable`), and no dry-run scenario uses it.
- **Write / paid scenarios** use `rw()` (`lib/uat-page.cjs`): the browser guard stays on with a narrow `allowWrites`,
  `prepare()` signs the identity in unless the runner handed a session, paid ones refuse without `UAT_ALLOW_PAID=1`.
  `record.cjs` gained `scenario.after(page, h)` (runs once after the steps, also after a FAIL; its error fails the exit
  code) for PRT-02's restore and PRT-14's language reset.
- **CRM UAT cut.** Steps marked `internal: true` (the R00 build-progress slide, the R20 progress tiles) are dropped
  unless `UAT_CUT=internal`; captions and takes filter the same way. R00's first card says "acceptance walk-through"
  in the UAT cut. R19 / R20 say AI drafts run in test mode on an interim model.

## Changed

- `PRT-10` opened `/portal/account/api`, gone with the tenant API keys (AA-1036 R3): now Integrations
  (`/portal/account/integrations`) and the Facebook help page.
- `CRM-01`, `CRM-REV-01`, `CRM-REV-18`, `CRM-REV-19` opened `/` for the CRM home; since AA-1036 the bare host is the
  Content studio, the CRM home is `/home` (`web/lib/nav.ts CRM_HOME_PATH`). Seen live: CRM-01 FAIL -> PASS.
- Every CRM / Content test id the scenarios use was checked statically against AA-Partner `origin/main` (`8575fada`):
  all present (templated ones resolved by hand: `kpi-info-*` from the kit KpiTile InfoTip, `supplier-<kind>`, …).
- `node --test tools/uat/tests` does not work on Node 22 (a directory is not a test file): the package script and docs
  use `node --test tools/uat/tests/*.test.cjs`.

## Tradeoffs

- Content tenants match by invented display name unless pinned: the studio session API returns no slug. A real tenant
  renamed to an invented name would pass rule (a) alone; pinning the four ids in the local allow-list closes that, and
  the CIS unique slug index keeps the slugs themselves unique.
- PRT-08 / X-04 / PRT-04 need at least one piece / rewrite on the viewer's tenant; they fail with a "precondition" reason
  instead of passing on an empty state (an empty export is not evidence).
- The S262 chapter order is kept as the file order `CRM-REV-00..20` (no renumbering; ids are never reused).
- PRT-06 (paid) and PRT-02 (editor) could not be run here: the editor secret does not exist yet (BLOCKED, as designed),
  and PRT-06 would spend money. Their selectors come from the source (`BrandTab.tsx`, `SlateTab.tsx`,
  `AngleGateWizard.tsx`, `WriterPanel.tsx`), not from a live run.
- `--record-on-fail` (optional item 5) was not built in this lane.

## Should know

- Live checks done in the lane (fast mode, egress VN, one Chromium at a time): Content PRT-01/03/04/05/08/09/10 + X-04
  8/8 PASS (studio tenant = atlas-hearth, matched by name); CRM-01/02/05/07 4/4 PASS (sen-vang by id); PRT-14 PASS;
  negative check with `{"builtin": false}`: dry run exit 5, `record.cjs` exit 5, result.json BLOCKED, no video;
  PRT-13 refused by the guard (the viewer has no CRM agency, HTTP 409): after-lane as catalogued.
- The CRM review chunks (`CRM-REV-*`) write and were not run here; run `bash tools/uat/scenarios/crm/run-all.sh --fast`
  once before recording (AA-1030 AA-prices panel changes may need selector updates in R06).
- Booking list pages that may show agencies have no row filter yet (no Booking scenario lists CRM agencies today).
