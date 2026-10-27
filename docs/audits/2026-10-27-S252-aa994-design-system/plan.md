# AA-994 — One design system: slice plan, conformance guards, visual job (S252, 27/10/2026)

Companion to [`adr-draft.md`](adr-draft.md) (ADR 0016, Option B "guarded byte copies, CIS `frontend/app/_kit/core/`
canonical", with the critic's fixes). Read-only design: nothing here was edited in an app repo, pushed or run.
Evidence on origin/main: AA-CIS-App `5cc5fb4d`, AA-Partner `5a6de8b`, AA-Booking `e84d8c1`, AA-TripPlanner-Web
`4b08949`, AA-CIS-Infra `origin/main`.

## 0. Starting point in numbers

| | CIS admin | Portal | CRM web | Booking admin | TripPlanner |
|---|---|---|---|---|---|
| Kit | source, 29 files (`frontend/app/_kit/`) | 16 byte copies + own barrel | 6 byte copies + own barrel | copy of CIS `039bb250`, 32 commits stale, + `ui/booking/` 23 files | own B2C `ui/` (11 files) |
| Token set | 173 vars, **lacks AA-760** | AA-760 | AA-760 | stale (pre-AA-760, pre-S248) | 33/31-var subset, AA-812 |
| Legacy layer | `adminUi.tsx` (54 importers) | `ui.tsx` (39) | `PageTitle`/`Panel` | – | – |
| Raw `<main>` / `<table>` / hand-styled `<button>` | 26 / 23 / 47 files | 5 / – / 27 | 3 / 7 / 17 | 16 / – / 24 | 9 / – / – |
| Raw input files | ~30 | 8 | 29 | 20 | – |
| Kit lint | warn, 4 files error, non-required job | error, non-required | **no ESLint** | error, **required** (Frontend Build) | none (contrast test only) |
| Drift check | – (source) | live-compare, non-required, skips `globals.css` | same | none | none |
| Required frontend check | Frontend Build, Portal Build | **none** | **none** | Frontend Build | Frontend (lint + build) |
| Merge queue | yes | yes | yes | yes | **no** |
| Deploy | Vercel | Vercel + Fargate | ECS | Vercel | Vercel |
| Next / Tailwind | 16.4.2 / 4 | 16.4.2 / 4 | 16.4.2 / none | **16.4.1** / 4 | 16.4.2 / **3.4.14** |

## 1. Hand steps for Nghiệp (batched, one window)

| # | When | Step | Why |
|---|---|---|---|
| H1 | before S2 | AA-Partner `main` protection: add **Portal Build** and **Web Build** to required checks | today no frontend check is required in Partner (`ci.yml:249,415`); a kit sync could merge a broken build |
| H2 | after S1c is green on main | AA-CIS-App: add **Frontend Lint** to required checks | the lint job stops being `continue-on-error` (`ci.yml:324-356`) |
| H3 | after S2/S3b | Add **Kit provenance** to required checks in CIS, Partner, Booking (TripPlanner: required on `pull_request`) | decision 5; the job always runs, so requiring it blocks nothing unrelated |
| H4 | before S3c | AA-Booking: create GitHub environment **`e2e`** (main only) and secret `E2E_MAIL_ROLE_ARN` | Booking has only `dev`, `Preview`, `Production`, `release` today |
| H5 | before S3c | Approve the Infra PR adding the AA-Booking `environment:e2e` subject to the mailbox reader trust (`accounts/aa365/e2e_mailbox.tf:367-375`; Terraform apply needs MFA) | the role trusts AA-CIS-App and AA-Partner only |
| H6 | S1b review | Sign off the canonical token values on the before/after screenshots | visible change in CIS admin and Booking (gold-button label colour, darker accent-deep/green/amber) |

H1–H3 are branch-protection edits on his login (ADR 0011). H6 goes on a click-to-approve decision page, not a bare ask.

## 2. Slice plan (ordered PR groups)

Risk class follows ADR 0011 section 4: **Normal** (agent merges on green CI) or **Risky** (CI/workflow/secret,
Terraform/IAM: agent review by `kiro-reviewer` or an independent subagent before merge). Live proof follows `aa-ship`
(deploy COMPLETED + live check) and `aa-ui-verify`. Effort is agent days.

### Phase 1 — decision and the CIS core (this week)

| # | Repo | PR | Risk | Tests / guards added | Live proof | Effort |
|---|---|---|---|---|---|---|
| **S0** | root | ADR 0016 (from the draft) + README row + next-free 0017; pointers in ADR 0001 d7, 0004 (`:59-61`, `:278`), 0010 (`:46`); ADR 0011 install row fix (`aa-ci-bot` on AA-Partner); `tools/kit/kit-sync.sh`; PreToolUse hook blocking edits to `**/_kit/core/**` and `**/ui/core/**` outside AA-CIS-App + the same rule in `.kiro/steering/`; `docs/backlog` AA-655 → folded into AA-994 | Normal (hook = agent config; self-review) | root `check_adr_numbers.py` passes; hook unit test (blocked path, allowed CIS path) | hook blocks a test Edit in a scratch session | 0.5 |
| **S1a** | CIS | Create `frontend/app/_kit/core/`: move portable files (ADR d1), header line, CIS barrel re-exports (93 importers unchanged), `AdminMain` → `PageFrame` + alias, `GuidePanel` content as prop, `createThemeStore({ storageKey })` with `cis_theme`; `scripts/kit-manifest.mjs` → `MANIFEST.json`; `core/check-kit-copy.mjs` | Normal | unit: core import closure; manifest current; `check-kit-copy.mjs` self-check in Frontend Build; `tsc`, build | Vercel prod deploy COMPLETED; `ui-smoke.yml` production signed-in green; 3 pages spot-checked unchanged | 1 |
| **S1b** | CIS | Split `core/tokens.css` from `globals.css:31-246`; canonical values (AA-760 light + S248 muted + AA-812 where stricter; promote `--aa-scrim`, `--aa-hero-bg`); `--aa-font-*` with `var(--font-*, …)` fallback; port TripPlanner `lib/contrast.test.ts` onto `core/tokens.css` | Normal (visible) | contrast test (all checked pairs, light + dark); CSS check "no `--aa-*:` outside core/tokens.css" | before/after at 1440/390 × light/dark of 6 representative pages + gallery, attached to the PR; H6 sign-off | 1 |
| **S1c** | CIS | `core/eslint-kit.mjs` (rules 1–7, 9 of ADR d7; presets `inline` / `tailwind`) with RuleTester tests; `frontend/eslint.config.mjs` switches to the preset at `error`; `eslint-suppressions.json` baseline; Frontend Lint drops `continue-on-error`, runs `--prune-suppressions` and fails on growth; pre-push hook runs lint on changed files + integrity | Risky (CI) | RuleTester per rule; suppressions-growth check; then H2 | CI run on a deliberately bad commit (raw `<main>`) red, then green after revert (PR evidence) | 1.5 |
| **S1d** | CIS | `KitGallery` route gated by `KIT_GALLERY=1` (`notFound()` otherwise) + `visual.yml` (section 4) + `e2e/visual/pages.ts` + route-coverage unit test | Risky (workflow, `e2e` secret) | gallery baselines; overflow/console/network assertions; route coverage test | first run artifacts: gallery 4 shots/component, production signed-in pages (A10b) 1440/390 light/dark; production gallery URL returns 404 | 1.5 |

### Phase 2 — Partner (portal + CRM web)

| # | Repo | PR | Risk | Tests / guards added | Live proof | Effort |
|---|---|---|---|---|---|---|
| **S2a** | Partner | Precondition H1. Replace 16 portal and 6 web vendored files with `portal/app/_kit/core/` and `web/app/_kit/core/` (full profile, via `kit-sync.sh`) + `kit.lock.json` each; barrels import `./core`; `PortalShell`/`CrmShell` move to `_kit/local/`; web gains `@tanstack/react-table`, `@tanstack/react-query`; `api/scripts/check_vendored_copies.py` drops `_WEB_KIT` (`:51`), `_PORTAL_KIT` (`:59-76`), `_brand/tokens.ts`; integrity + provenance in Portal Build / Web Build | Risky (CI) | integrity, provenance (always-run, `merge_group` diff), existing Partner tests | portal: Vercel preview + `ui-smoke-portal.yml` green, Fargate deploy; CRM web: `deploy-web-dev.yml` COMPLETED + `e2e-dev.yml` slice1 green | 1.5 |
| **S2b** | Partner | ESLint 9 for `web/` (first time) with the `inline` preset + suppressions; portal `eslint.config.mjs:31-62` switches to the preset (its 3 exempt files go to suppressions); lint steps inside Portal Build and Web Build | Risky (CI) | suppressions-growth; lint now inside required jobs | bad-commit red/green proof | 1 |
| **S2c** | Partner | `visual-portal.yml` + `visual-web.yml` (section 4), gallery routes in both apps | Risky (workflow, secrets) | as S1d | artifacts for portal preview (tenant key) and CRM Dev signed-in (partner-pool owner) | 1 |
| **S2d** | Partner | CRM `components/PageTitle.tsx` (hard-coded font `:11`) and `Panel` → core `PageHeader` / `Section`; first suppressions shrink | Normal | suppressions shrink | CRM visual run green on Dev | 1 |

### Phase 3 — sync automation (after S2a; the orchestrator syncs by hand until then)

| # | Repo | PR | Risk | Tests / guards | Live proof | Effort |
|---|---|---|---|---|---|---|
| **S3s** | CIS | `kit-sync.yml` (push to main on `core/**`, `aa-ci-bot` token narrowed per repo, `bot/kit-sync` regenerated, one PR per consumer); "Kit consumers" job on CIS PRs touching core (overlay + `tsc --noEmit` + kit lint per consumer, non-required); nightly freshness report | Risky (workflow, App key) | dry-run mode test; the job exits green when core is unchanged | one real sync PR opened in Partner with CI + preview running | 1 |

### Phase 4 — Booking catch-up

| # | Repo | PR | Risk | Tests / guards added | Live proof | Effort |
|---|---|---|---|---|---|---|
| **S4a** | CIS | Upstream into core: `PageFrame` `width` (from Booking `ui/booking/PageFrame.tsx:7-30`), `Section`, `KpiTile`, `FilterBar` + `useUrlFilters`, `RowMenu`, one `ConfirmModal` (absorbing `ConfirmDialog`), `Money` / `DateText`; gallery entries; CIS local `Section`s / `Kpi`s switch to them | Normal | gallery baselines updated; "Kit consumers" green | CIS visual run; sync PRs to Partner merged | 2 |
| **S4b** | Booking | Delete copied kit (`ui/*.tsx`, `ui/tokens.css`); vendor `frontend/ui/core/` + lock; `globals.css` imports `./ui/core/tokens.css`; `booking-tokens.css` keeps `--bk-*` only; shells to `ui/local/` (or stay in `ui/booking/`); `PageFrame`/`Section`/`KpiTile`/`FilterBar`/`ConfirmDialog` become barrel aliases; `bk_theme` through `createThemeStore`; Next 16.4.1 → 16.4.2; `eslint.config.mjs:26-41` paths updated (the `react-hooks/incompatible-library` exemption moves to `ui/core/DataTable.tsx`) and `tailwind` preset at error + suppressions; integrity + provenance in Frontend Build | Risky (CI) | integrity, provenance, lint preset; existing Booking tests | Vercel prod deploy + `vercel-deploy.yml` job `smoke` green; signed-in pages checked by S4c | 2.5 |
| **S4c** | Infra + Booking | Infra PR: add `repo:AdventureAsia365-Ecosys@…/AA-Booking@<repo id>:environment:e2e` to the mailbox reader trust (H5). Booking `visual.yml` + gallery route (H4 first) | Risky (IAM, workflow) | Terraform plan in PR; visual assertions | first signed-in run as `e2e-booking@` on production and the fixed Preview host | 1 |

### Phase 5 — TripPlanner tokens

| # | Repo | PR | Risk | Tests / guards added | Live proof | Effort |
|---|---|---|---|---|---|---|
| **S5a** | TP | Tokens profile `frontend/ui/core/{tokens.css, tokens.ts, brand.ts, theme.ts, check-kit-copy.mjs, eslint-kit.mjs, MANIFEST.json}` + lock; delete the copied palette in `ui/tokens.css` (keep only non-`--aa` extras); `restoreTheme` via `createThemeStore({ storageKey: "tp_theme" })`; `lib/contrast.test.ts` removed (now in CIS); `tailwind` preset rules 4, 6, 7 at error + suppressions; integrity + provenance on `pull_request` | Risky (CI) | integrity, provenance (no queue), lint | Vercel prod deploy; visual public pages light/dark (stale dark info/muted fixed) | 0.5 |
| **S5b** | TP | `visual.yml`, public pages only, preview + production | Risky (workflow) | as S1d minus sign-in | artifacts | 0.5 |

### Phase 6 — coverage and page migration (the bulk of AA-994)

| # | Repo | Work | Risk | Guard that proves progress | Effort |
|---|---|---|---|---|---|
| **S6a** | CIS → all | Form controls `Field`, `Input`, `Select`, `Textarea`, `Checkbox` in core + gallery; rule 8 `no-raw-form-control` on, existing uses into suppressions; sync | Normal | gallery baselines; rule on | 2 |
| **S6b** | CIS | Migrate admin pages: `PageFrame` everywhere (26 raw `<main>`), `adminUi` `TH`/`TD` tables → `DataTable` (23), `Btn` → `Button` (25), `TabBar` → `Tabs` (4), `Card`/`StatCard` → `Section`/`KpiTile`, form controls; delete `adminUi.tsx` | Normal per PR (~5 PRs by area) | suppressions file shrinks each PR; visual run per PR | 4–5 |
| **S6c** | Partner | Portal `ui.tsx` (39 importers) → core; delete it. CRM raw tables (7), inputs (29), buttons (17) | Normal (~3 PRs) | suppressions shrink | 3–4 |
| **S6d** | Booking | 16 raw `<main>` → `PageFrame`; inputs (20) / selects / textareas → form controls; hand-styled buttons (24) | Normal (~2 PRs) | suppressions shrink | 1.5–2 |
| **S6e** | CIS → all | `ShellFrame` in core (nav, identity, logout, brand as props); CIS `AdminShell`, Booking shell, `PortalShell`, `CrmShell` become configurations | Normal (visible, per-app PRs) | gallery shell entry; visual runs per app | 3 |
| **S6f** | all | Close-out: every `eslint-suppressions.json` empty; gallery visual job required (H3-style edit); "Kit consumers" required; delete the frozen CIS `portal/app/_kit/` when AA-885's rollback window ends; update `CONTEXT.md` of each app and `docs/ecosystem-architecture.md` | Normal | empty suppressions; required checks | 1 |

**Totals:** phases 1–5 about 16 agent days in ~16 PRs; phase 6 about 15–18 days in ~15 PRs. Phases 2–5 can run as
parallel lanes once S1a–S1c are merged (they only need the core and the rules). A CIS kit fix found during phase 6 is
part of the same CIS PR (one hop), then reaches the others by the sync PR.

**Suggested Linear split (Free plan: deliverable-sized, few issues):** AA-994 = phases 1–3 (core, Partner, sync bot);
one new issue for the Booking catch-up (phase 4); one for TripPlanner tokens (phase 5, small); one for the page
migration + form controls + shells (phase 6). AA-655 is closed as folded into AA-994 (decision record: ADR 0016).

## 3. Conformance guards: what each is and how each repo implements it

All lint rules live in the vendored `core/eslint-kit.mjs`, so the rule text is byte-identical in every app.
"Preset" is `inline` (CIS, portal, CRM web) or `tailwind` (Booking, TripPlanner).

| # | Guard | Kind | CIS (`frontend/`) | Portal (`portal/`) | CRM web (`web/`) | Booking (`frontend/`) | TripPlanner (`frontend/`) |
|---|---|---|---|---|---|---|---|
| G1 | `no-raw-main` | ESLint | `inline`, `app/**` minus `_kit/**`; Frontend Lint (required after H2) | `inline`, `app/portal/**`; Portal Build | `inline`, `app/**`; Web Build | `tailwind`, `app/**`, `ui/booking/**`; Frontend Build | `tailwind`, `app/**`; Frontend (lint + build) |
| G2 | `no-raw-table` (outside `DataTable`) | ESLint | replaces today's warn rule (`eslint.config.mjs:10-36,41-77`) | replaces `:31-62` | new | replaces `:6-33` | n/a (B2C has no tables) — off |
| G3 | `no-raw-dialog` | ESLint | replaces today's rule | replaces | new | replaces | on |
| G4 | `no-hex-colour` | ESLint (JSX style values, `className` arbitrary values `[#…]`) | new | new | new | replaces Booking's raw-hex rule | on (Tailwind `[#…]` too) |
| G5 | `no-hand-styled-button` | ESLint | new | new | new | new (`<button className>` outside `ui/**`) | **off** (TP `Button` is local B2C; keep `buttonClass`) |
| G6 | `no-raw-aa-var` | ESLint (string literal `var(--aa-`) | new | new | new | new (Tailwind tokens instead) | on |
| G7 | `no-className` in pages | ESLint | kept from today (inline preset) | kept | new | n/a | n/a |
| G8 | `no-raw-form-control` | ESLint, from S6a | on | on | on | on | off |
| G9 | `no-legacy-kit` (new imports of `adminUi` / portal `ui.tsx` primitives) | ESLint `no-restricted-imports` | on | on | n/a | n/a | n/a |
| G10 | No `--aa-*:` definition outside `core/tokens.css` | `check-kit-copy.mjs --css` over `**/*.css` | Frontend Build | Portal Build | Web Build | Frontend Build (`booking-tokens.css` may define `--bk-*` only) | Frontend (lint + build) (`--tp-*` only) |
| G11 | Suppressions only shrink | `eslint --prune-suppressions` then `git diff --exit-code` on additions (script) | Frontend Lint | Portal Build | Web Build | Frontend Build | Frontend (lint + build) |
| G12 | Integrity (copy = manifest) | `node <dest>/check-kit-copy.mjs` | self-check: manifest current + import closure (unit test) | Portal Build | Web Build | Frontend Build | Frontend (lint + build) |
| G13 | Provenance (manifest = CIS at `lock.ref`, ref on CIS main) | small always-run job `Kit provenance` | n/a (source) | `pull_request` + `merge_group` | same job, both locks | `pull_request` + `merge_group` | `pull_request` only (no queue) |
| G14 | Freshness | report only | nightly CIS job + every sync run | – | – | – | – |
| G15 | Contrast (WCAG pairs) | Vitest/Jest on `core/tokens.css` | Frontend Build (moved from TP) | – | – | – | – |
| G16 | Route coverage for the visual list | unit test: every `app/**/page.tsx` is in `e2e/visual/pages.ts` or excluded with a reason | Frontend Build | Portal Build | Web Build | Frontend Build | Frontend (lint + build) |
| G17 | Kit consumers (core change compiles in every app) | CIS job overlaying core on each consumer `main` | non-required until S4b, then required | – | – | – | – |
| G18 | Agent edit guard | Claude PreToolUse hook + Kiro steering | root `.claude/hooks/` (blocks copies, allows CIS) | covered | covered | covered | covered |
| G19 | Pre-push | hook runs G12 + lint on changed files | add | add | add | add | add |

Implementation notes:
- ESLint bulk suppressions need ESLint ≥ 9.24; every lockfile resolves 9.39.x (CRM web gets 9.39.x when ESLint is
  added). The suppressions file sits next to `eslint.config.mjs` in each app folder.
- CIS today has "74 pre-existing legacy errors" behind `continue-on-error` (`ci.yml:324-356`); they go into the
  suppressions file in S1c, so the job can be required at once.
- Booking's required Frontend Build already runs lint with zero warnings (`ci.yml:255`), so Booking needs no
  branch-protection change for G1–G11.
- G13 must not use `paths:` filters (required checks and `merge_group` ignore them); it diffs
  `github.event.merge_group.base_sha..head_sha` (or the PR base) itself and exits 0 when no `core/**` or
  `kit.lock.json` changed.

## 4. Automated visual job

### 4.1 Shape (same in every repo)

- One workflow per deployable frontend: CIS `visual.yml`; Partner `visual-portal.yml`, `visual-web.yml`; Booking
  `visual.yml`; TripPlanner `visual.yml`. Shared spec code is part of the vendored core (`core/visual/` helper:
  theme setter, overflow probe, console/network collectors), so behaviour is identical.
- Runner `ubuntu-24.04`, container `mcr.microsoft.com/playwright:v<pinned>-noble`; captures run on GitHub's network,
  so no Vercel IP block from the agent machine.
- Matrix per page: viewports **1440×900** and **390×844** (mobile: `isMobile`, `hasTouch`), themes **light** and
  **dark**. Theme is set before first paint: `page.addInitScript` writes the app's key (`cis_theme`, `bk_theme`,
  `tp_theme`; portal and CRM use `cis_theme`) and the context uses `colorScheme`.
- Concurrency: one group per repo and target; `max-parallel: 2` on shard matrices (Free org: 20 concurrent jobs).

### 4.2 Assertions on every page × viewport × theme

```ts
// core/visual/probe.ts (vendored helper)
const overflow = await page.evaluate(() => {
  const vw = window.innerWidth;
  const doc = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth);
  const offenders = [...document.querySelectorAll<HTMLElement>("body *")]
    .filter(el => {
      if (el.closest("[data-kit-scroll]")) return false;          // ScrollX / DataTable scrollers
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.right > vw + 1;
    })
    .slice(0, 5).map(el => el.tagName + (el.id ? "#" + el.id : "") + "." + el.className);
  return { doc, vw, offenders };
});
expect(overflow.doc, `page scrolls sideways: ${overflow.offenders.join(", ")}`).toBeLessThanOrEqual(overflow.vw + 1);
```

- No page-level horizontal overflow (above). `ScrollX` and `DataTable` mark their scroller with `data-kit-scroll`
  (added in S1a).
- No `console.error` and no `pageerror` (per-app allowlist file for known third-party noise, each entry with an issue).
- No failed same-origin request (status ≥ 400 or `requestfailed`), allowlist per app.
- `[data-kit-frame]` present (set by `PageFrame`) on every page in scope of G1; a missing frame fails.
- After `networkidle` + `document.fonts.ready`, a full-page PNG; mutation-prone controls are never clicked
  (signed-in runs are read-only by rule: navigation and tab switches only).

### 4.3 Targets and triggers

| Target | Trigger | What is captured | Pixel diff | Gate |
|---|---|---|---|---|
| **Gallery, no Vercel** | `pull_request`, `merge_group` | `next build` with `KIT_GALLERY=1`, `next start` in the runner, route `/_kit-gallery` (every core component × state) | yes, `toHaveScreenshot` vs committed baselines (`e2e/visual/__screenshots__/`, Linux container only), small threshold; update via `--update-snapshots` in a labelled PR | report-only first, required after ~2 weeks stable |
| **PR preview, public** | `workflow_call` from `vercel-deploy*.yml` after a preview deploy (like `ui-smoke.yml`) | public pages (sign-in page, public client pages) of the preview URL, with the Vercel bypass header where protected | no | report-only |
| **Production, signed in** | `workflow_call` after a production deploy on `main`, plus `workflow_dispatch` (`base_url`, `pages` filter) | every page in `e2e/visual/pages.ts`; dynamic routes resolve an id by reading the first row link of their list page | no | feeds `aa-ship` live verify; red run = issue, not a revert by itself |

`KIT_GALLERY` is read at build time; any deployed build (flag unset) returns `notFound()` for the gallery route.
G16 keeps `pages.ts` complete.

### 4.4 Sign-in per app

| App | Identity | How the job signs in | Where it can run | Prerequisites |
|---|---|---|---|---|
| CIS admin | **A10b `e2e-cis-admin@e2e-mail.lumiguides.it.com`**, group `cis-admin`, Dev only, read-only except the content-quality sentence-apply routes (ADR 0006a A10b `:334-344`, CIS mig 283) | `/login` → company email → managed login at staff-auth → email code read from the SES inbound bucket via the read-only mailbox role (OIDC, environment `e2e`, `main` only), same helper as `e2e-cognito.yml` / `ui-smoke.yml` job `smoke-staff`; pick the newest message to that recipient after the request time | Production `aa-cis.lumiguides.it.com` (full role). The fixed Preview host caps sessions at viewer (`ui-smoke.yml` header); per-PR `*.vercel.app` previews cannot sign in (no wildcard callbacks) → gallery + public only | in place (`e2e` env, `E2E_MAIL_ROLE_ARN`) |
| Booking admin | **A10a `e2e-booking@e2e-mail.lumiguides.it.com`**, group `booking-admin` (ADR 0006a `:293-300`) | same Cognito email-code flow on the Booking host | Production Booking admin and the fixed Preview host `booking-preview.lumiguides.it.com` (AA-911; `BOOKING_PREVIEW_BYPASS` if protected); per-PR previews public only | **H4** (`e2e` environment in AA-Booking) and **H5** (mailbox role trust lists AA-CIS-App and AA-Partner only, `e2e_mailbox.tf:367-375`) |
| Portal (Content studio) | Tenant E2E login: `E2E_TENANT_API_KEY` (one of `aa-cis/dev/e2e-tenant/*`), as `ui-smoke-portal.yml:7` does; after ADR 0010a P2b, the partner-pool E2E user (password + TOTP) | existing portal login helper from `e2e/smoke-portal/` | **per-PR preview too** (with `VERCEL_PORTAL_BYPASS_SECRET`) and production | in place |
| CRM web | Partner-pool E2E owner: variable `E2ECRMEMAIL`, secrets `E2ECRMPASSWORD` + `E2ECRMTOTP` (`e2e-dev.yml:7-12`; empty password = email-code path through the mailbox role) | existing `e2e/` sign-in helper | CRM is on ECS with no per-PR preview: per PR = gallery + public pages under `next start`; signed-in = Dev host (`E2ECRMPARTNER`) after `deploy-web-dev.yml` on `main` | in place (`e2e` env in Partner) |
| TripPlanner | none (B2C public pages) | – | per-PR preview + production | none |

Secrets are read into env vars at run time and never printed; signed-in runs upload PNGs and the JSON report only
(no Playwright HTML report or trace, which would show the typed code or password). Codes and TOTP seeds never appear in
artifacts.

### 4.5 Artifacts and reporting

- Artifact `visual-<app>-<target>-<run_id>`: `<page-slug>__<1440|390>__<light|dark>.png` + `report.json`
  (page, viewport, theme, overflow offenders, console errors, failed requests), retention 14 days.
- Job summary: one table, page × 4 cells (pass / fail reason), links to the artifact.
- On PRs, the preview and gallery runs post or update one PR comment with the summary (`github.token`,
  `pull-requests: write`).
- Size: CIS ~60 listed pages × 4 = ~240 shots, about 10–15 min in 2 shards; the others 20–80 shots. Public repos:
  no Actions minutes cost.

## 5. Order of work for the next session

1. S0 (root) and S1a in parallel; H1 at the start of the session's hand-step window.
2. S1b with the H6 decision page; S1c; then H2.
3. S2a–S2b (needs H1), S1d and S2c in parallel lanes.
4. S3s; then phase 4 (S4a in CIS first, S4b, S4c with H4/H5), phase 5.
5. Phase 6 by area, each PR shrinking the suppressions and carrying its visual run.
