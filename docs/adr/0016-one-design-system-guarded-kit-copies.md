# ADR 0016 — One design system for the ecosystem frontends: a canonical kit core in AA-CIS-App, guarded byte copies, one token set for all five apps

- **Status:** Accepted (27/10/2026, S252, Nghiệp, with the AA-994 plan). Proposed the same day as option B ("guarded
  byte copies, CIS `frontend/app/_kit/core/` canonical") with the critic's fixes.
- **Scope:** AA-CIS-App (`frontend/`, the canonical kit core and its guards), AA-Partner (`portal/`, `web/`),
  AA-Booking (`frontend/`), AA-TripPlanner-Web (`frontend/`, tokens only), the root repo (this ADR, `tools/kit/`,
  the agent edit guard), AA-CIS-Infra (the e2e mailbox role trust, for the visual job only).
- **Amends / Implements:** implements [ADR 0001](0001-ecosystem-target-architecture.md) decision 7 ("one design
  system") and states *how* it is met. Supersedes the "copy the CIS kit until the shared package (AA-655) is
  published" clauses of [ADR 0004](0004-aa-booking-stack-and-bootstrap.md) (decision 1 frontend line, consequence
  "the UI kit is copied until AA-655 ships") and [ADR 0010](0010-aa-partner-app.md) (decision 1, "byte-compare guard
  until a package exists"). Closes AA-655 (parked) as "guarded copies chosen, package re-evaluated under decision
  12"; the work is tracked as AA-994. Corrects the `aa-ci-bot` install row of
  [ADR 0011](0011-github-app-identity-and-merge-rights.md) (decision 13).
- **Design and evidence:** `docs/audits/2026-10-27-S252-aa994-design-system/` (`adr-draft.md`, `plan.md`: inventory
  in section 0, slice plan S0–S6f in section 2, guards G1–G19 in section 3, visual job in section 4). Evidence was read
  on origin/main: AA-CIS-App `5cc5fb4d`, AA-Partner `5a6de8b`, AA-Booking `e84d8c1`, AA-TripPlanner-Web `4b08949`,
  AA-CIS-Infra `origin/main` (27/10/2026).
- **Related Linear:** AA-994 (this design system, phases 1–3), AA-655 (folded into AA-994), AA-760 (light contrast
  fixes), AA-812 (TripPlanner tokens), AA-885 (frozen CIS portal copy).

## Context

ADR 0001 decision 7 says "all frontends consume one token source and one shared component set". The package that
would do it (AA-655) was parked, and ADRs 0004 and 0010 told Booking and Partner to copy the CIS kit until it existed.
Two weeks later there are five kits and none of the rules is enforced:

1. **Five token copies that already differ.** The `--aa-*` variables live in CIS `frontend/app/globals.css`
   (light `:31-144`, dark `:149-246`, 173 variables), in byte-for-byte-claimed copies in the portal and CRM web, in
   Booking `frontend/ui/tokens.css` (copied from CIS `039bb250`, 13/10) and in a 33/31-variable subset in TripPlanner
   `frontend/ui/tokens.css`. The AA-760 light contrast fixes exist in the portal and CRM web but not in CIS admin
   (`--aa-accent-deep #9E6E16 → #8A5F12`, `--aa-green #2E7D5B → #276B4E`, `--aa-kit-amber #B5791F → #8F5F16`,
   `--aa-on-accent #FFFFFF → #1A1206`; CIS `globals.css:34,48,54,140`, portal `:36,50,56,143`, web `:13,27,33,120`).
   Booking and TripPlanner miss the S248 muted fixes; TripPlanner carries its own AA-812 values (`tokens.css:31-60`).
2. **The existing guard cannot see tokens and does not gate.** `AA-Partner/api/scripts/check_vendored_copies.py`
   compares 22 kit files with *live* CIS `main` (`:101-161`), skips `globals.css`, and runs in the non-required job
   "Vendored CIS copies" (`.github/workflows/ci.yml:233-243`). Because it compares with live CIS, any CIS kit merge
   turns every open Partner PR red, which is why it cannot be required. Booking `frontend/ui/*` and TripPlanner have
   no drift check at all (Booking's `backend/scripts/check_vendored_copies.py:37-41` covers backend files only).
3. **Booking's copy is 32 CIS kit commits stale:** no `DataTable` `compact` / `aria-sort` (CIS #1012), no
   `Breadcrumb`, `ScrollX`, `InfoTip`, `GuidePanel`, `AdminMain`.
4. **Missing kit parts are rebuilt locally in each app:** page frame (CIS `AdminMain`, merged in #1055, versus
   Booking `ui/booking/PageFrame.tsx:7-30`; 26 raw `<main>` in CIS with 4 padding variants), Section/Card (7 local
   `Section`s in CIS, `adminUi.Card`, Booking `Section`, CRM `Panel`), KPI tile, FilterBar, RowMenu, two confirm
   dialogs, four date/money helpers, and **no form controls anywhere** (raw inputs in ~30 CIS files, 29 CRM, 20 Booking).
5. **Older parallel layers are still live:** CIS `app/admin/_components/adminUi.tsx` (54 importers) and portal
   `app/portal/_components/ui.tsx` (39 importers), each with its own `Btn`, `Badge`, table cells or `PageHeader`.
6. **Conformance lint is weak.** CIS kit rules are `warn` on `app/admin/**` and `error` on 4 files, in the
   non-required "Frontend Lint" with `continue-on-error` (`ci.yml:324-356`). Portal Lint is non-required. CRM web has
   no ESLint (`web/package.json`). TripPlanner has only a WCAG contrast test (`lib/contrast.test.ts:11`). Booking's
   rules are the only gate (required "Frontend Build" runs `npm run lint` with zero warnings, `ci.yml:255`). No app
   has a rule for raw `<main>`, hand-styled `<button>` (CIS 47 files, portal 27, CRM 17, Booking 24) or raw
   `var(--aa-*)` in page code.
7. **AA-Partner has no required frontend check.** Required checks are Lint, Security Audit, Unit Tests, Integration
   Tests, Docker Build Check, Docs lint, PR title, gitleaks; "Portal Build" (`ci.yml:415`), "Web Build" (`:249`) and
   "Portal Lint" (`:449`) are not required. A kit change that breaks the portal or CRM build can merge today.
8. **No automated visual check** at 1440/390 × light/dark in any repo. Only sign-in and smoke E2E exist
   (CIS `ui-smoke.yml`, `e2e-cognito.yml`; Partner `ui-smoke-portal.yml`, `e2e-dev.yml`; Booking `vercel-deploy.yml`
   job `smoke`, one public page). Screenshots of S252 work were blocked by Vercel IP checks from the agent machine.

Constraints that shape the choice: GitHub Free org; app repos public ([ADR 0014](0014-repo-visibility-and-github-plan.md)),
root and Infra public only until November; Vercel builds remotely from CI-uploaded source
(`git.deploymentEnabled: false`) and the portal and CRM web build in `node:22-alpine` Docker images; CIS and the portal
set `turbopack.root: path.resolve(__dirname)` (CIS `next.config.ts:24-26`), so a `file:` or `npm link` dependency
outside the app folder does not resolve; three styling methods are in use (inline `K` in CIS/portal/CRM, inline kit +
Tailwind 4 in Booking, Tailwind 3.4.14 in TripPlanner). All five `tsconfig.json` are `strict` with the same `@/*`
alias; Next is 16.4.2 everywhere except Booking (16.4.1); React 19.2.4 everywhere; ESLint resolves to 9.39.x in every
lockfile.

## Decision

### 1. The canonical kit core lives in AA-CIS-App `frontend/app/_kit/core/`

- `core/` is a **closed set**: its files import only `./*` and npm packages (`react`, `react-dom`, `next/*`,
  `lucide-react`, `@tanstack/react-table`, `@tanstack/react-query`). No `@/` alias, no `../`. A CIS unit test enforces it.
- First contents (moved from `_kit/`, re-exported by the CIS barrel so the 93 importers of `@/app/_kit` do not change):
  `tokens.ts`, `brand.ts` (from `app/_brand/tokens.ts`), `tokens.css` (the `--aa-*` blocks split out of
  `globals.css`), `primitives.tsx`, `DataTable.tsx`, `csv.ts`, `savedViews.ts`, `Drawer.tsx`, `Modal.tsx`,
  `Toast.tsx`, `Providers.tsx`, `theme.ts` (as `createThemeStore`), `useTheme.ts`, `useHydrated.ts`,
  `useMediaQuery.ts`, `sidebarStore.ts`, `useSidebar.ts`, `PageFrame.tsx` (today's `AdminMain`, with an `AdminMain`
  alias and Booking's `width: "wide" | "narrow"`), `GuidePanel.tsx` (content passed as a prop), `KitGallery.tsx`
  (decision 9), `eslint-kit.mjs` (decision 7), `check-kit-copy.mjs` (decision 5) and `MANIFEST.json`.
- **Stays CIS-local** (`_kit/` outside `core/`): `api.ts` (CIS reviewer header and storage key, `api.ts:18-24`),
  `guideContent.ts`, `SessionKeepAlive.tsx`, `adminNav.tsx`, `useNavSections.ts`, `useAdminIdentity.ts`,
  `useReviewPendingCount.ts`, and the shell (`AdminShell`, `Sidebar`, `Topbar`, `BottomNav`, `CommandPalette`), which
  imports `@/lib/rbac`, `@/lib/apps`, `@/lib/staffLogout` and `adminUi` (`Sidebar.tsx:27-34`).
- **Kit scope grows in CIS first, then syncs.** Upstreamed from Booking: `PageFrame` (merged with `AdminMain`),
  `Section`, `KpiTile`, `FilterBar` + `useUrlFilters`, `RowMenu`, one `ConfirmModal` (replacing Booking
  `ConfirmDialog`), `Money` / `DateText` beside `formatDate*`. Built new: form controls `Field`, `Input`, `Select`,
  `Textarea`, `Checkbox`. Later, a slot-based `ShellFrame` whose nav, identity, logout and brand label are props; the
  app shells become thin configurations of it.

### 2. Consumers and profiles

| Consumer | Destination | Profile | Lock file |
|---|---|---|---|
| AA-Partner portal (Content studio) | `portal/app/_kit/core/` | full | `portal/kit.lock.json` |
| AA-Partner CRM web | `web/app/_kit/core/` | full | `web/kit.lock.json` |
| AA-Booking staff admin | `frontend/ui/core/` | full | `frontend/kit.lock.json` |
| AA-TripPlanner-Web (B2C) | `frontend/ui/core/` | tokens | `frontend/kit.lock.json` |

- The **tokens** profile is `tokens.css`, `tokens.ts`, `brand.ts`, `theme.ts`, `check-kit-copy.mjs`, `eslint-kit.mjs`
  and `MANIFEST.json`. TripPlanner keeps its B2C components (`Button`, `Badge`, `Icon`, `Photo`, state components) on
  purpose: they are a separate brand surface, not drift. Its Tailwind 3 config keeps mapping `k-*` onto `var(--aa-*)`
  (`tailwind.config.ts:13-43`).
- The frozen CIS copy `AA-CIS-App/portal/app/_kit/` (pinned by `tests/unit/test_aa885_portal_split.py`) is not a
  consumer; it is deleted when AA-885's rollback window ends, as already planned.

### 3. No edits inside a copy; four extension points

- Every file in `core/` carries the same header line in CIS and in every copy:
  `UI kit core (root ADR 0016). Canonical: AA-CIS-App frontend/app/_kit/core. Edit only there; copies are checked byte for byte (kit.lock.json).`
- An app extends the kit only through: (a) its barrel (`_kit/index.ts`, Booking `ui/index.ts`), which re-exports
  `./core` plus local parts and may alias names; (b) a `local/` folder next to `core/` (Booking keeps `ui/booking/`),
  whose files may import `../core` and never the reverse; (c) CSS variables with the app's own prefix (`--bk-*`,
  `--tp-*`, `--crm-*`); defining an `--aa-*` variable outside `core/tokens.css` is a lint error; (d) props.
- **Promotion rule:** a component that two or more apps use or need moves into `core/` through a CIS PR. It is never
  copied sideways from one app into another.
- Pages import the barrel, never `core/` directly, so moving a component between `local/` and `core/` changes no page.

### 4. One token set for all five apps

- `core/tokens.css` is the only place an `--aa-*` value is defined. Selectors stay `:root, [data-theme="light"]` and
  `[data-theme="dark"]`, which every app already uses.
- Canonical values: the stricter of each pair. AA-760 light values (portal/CRM), the S248 muted fixes (CIS), the
  AA-812 D6 values where TripPlanner is stricter; TripPlanner's `--aa-scrim` and `--aa-hero-bg` are promoted into
  core. The WCAG contrast test moves from TripPlanner `lib/contrast.test.ts` into CIS and runs on `core/tokens.css`;
  a token PR that lowers a checked pair below its threshold fails CI.
- Fonts: `--aa-font-sans: var(--font-poppins, "Poppins"), system-ui, …` and the same pattern for display and mono, so
  the variable works with next/font (TripPlanner) and with a Google Fonts `<link>` (the others). Booking's Satisfy
  stays `--bk-font-*`.
- **Theme storage keys stay per app** (`cis_theme`, `bk_theme`, `tp_theme`): localStorage is per origin, so they never
  collide and renaming would only add fallback code. `core/theme.ts` exports `createThemeStore({ storageKey })` and a
  matching restore-script string; each `layout.tsx` restore script reads its own key.
- Visible consequence, signed off once: CIS admin and Booking get the AA-760 values (dark text on gold primary buttons;
  darker accent-deep, green, amber). The PR carries before/after screenshots at 1440/390, light/dark (decision 9).

### 5. Two required checks and one report, all offline-first

- **Integrity (required, offline):** `core/check-kit-copy.mjs`, a dependency-free Node script vendored with the core.
  It fails when a file in `dest` is missing, extra, or differs from the sha256 in the copied `MANIFEST.json`. Message:
  "edit AA-CIS-App frontend/app/_kit/core, then sync; never edit the copy". Runs in the app's required frontend job
  and in the pre-push hook (< 1 s). In CIS the same script checks that `MANIFEST.json` is current and that `core/`
  imports nothing outside itself.
- **Provenance (required):** proves that the copied manifest equals the manifest at `kit.lock.json`'s `ref`, and that
  `ref` is an ancestor of CIS `main` (public repo, read with `github.token`). Without it an agent could edit a copy and
  regenerate `MANIFEST.json`. The job **always runs** (a required check cannot be path-filtered, and `paths:` does not
  apply to `merge_group`), computes its own diff (`merge_group.base_sha..head_sha` or the PR base), and exits green
  when no `core/**` or `kit.lock.json` path changed. TripPlanner has no merge queue: it runs on `pull_request` only.
  This gives Infra's migration-copy order rule to the kit: a consumer cannot merge a core change CIS has not merged.
- **Freshness (report only, never a gate):** a nightly CIS job plus every sync run writes
  `consumer | lock ref | CIS head | commits behind | open sync PR` to the job summary.
- The Partner script keeps only its non-kit entries (job template, identity verifier, `lib/` BFF helpers); `_WEB_KIT`
  (`:51`), `_PORTAL_KIT` (`:59-76`) and `_brand/tokens.ts` move to the new checks.

### 6. Sync: by hand first, then a bot; people merge

- `tools/kit/kit-sync.sh <consumer> [--from-local]` (root repo, agent tool; consumers `portal`, `crm-web`,
  `booking`, `tripplanner`) copies core from CIS `origin/main` (or the local checkout for a try-out, `ref: "local"`,
  which provenance rejects in CI by design), replaces the consumer's `core/` with the profile's files and rewrites
  the lock (`ref`, `profile`, sha256 of the copied `MANIFEST.json`). It refuses to run while CIS has no `core/`.
- Then `kit-sync.yml` in CIS: on `push` to `main` touching `frontend/app/_kit/core/**`, debounced by a concurrency
  group, for each consumer it mints an `aa-ci-bot` installation token narrowed to that repo (Contents RW, Pull
  requests RW), regenerates branch `bot/kit-sync` from the consumer's `main`, copies with the lock's profile, and opens
  or updates one PR `chore: sync UI kit core to AA-CIS-App <sha7>` with the core log, the manifest diff and
  `Refs AA-994`. App-token PRs trigger the consumer's full CI, previews and `merge_group`.
- A CIS PR that changes `core/` also runs **"Kit consumers"**: it overlays the new core on each consumer's `main` and
  runs that app's `tsc --noEmit` and kit lint. Non-required until the Booking catch-up is done, then required, so an
  API break is caught before the CIS merge. Core changes are additive by default; a rename keeps an alias in the
  barrels for one sync.
- Sync PRs are normal-tier PRs (ADR 0011 section 4): the orchestrating agent merges them through each repo's merge
  queue (`tools/github/mergeq.sh`; TripPlanner by `gh pr merge --squash`). Bot auto-merge is **not** granted by this
  ADR; it would change merge rights and needs Nghiệp's decision after about five clean syncs.
- Sync PRs are frontend-only; each repo's job-busy guard (DM-11.4) must not block them. Verify the guard is
  path-scoped before relying on daily syncs.

### 7. Conformance rules shipped with the core, enforced as errors with a shrinking baseline

`core/eslint-kit.mjs` exports two presets, `inline` (CIS, portal, CRM web: also no `className` in pages) and
`tailwind` (Booking, TripPlanner). Rules (custom, in the same file, no plugin package):

1. `aa-kit/no-raw-main` — no `<main>` in pages; use `PageFrame`/`AdminMain` (shells exempt).
2. `aa-kit/no-raw-table` — no `<table>` outside `DataTable` (and `ScrollX` documented exceptions).
3. `aa-kit/no-raw-dialog` — no `role="dialog"` / `<dialog>` outside `Drawer`/`Modal`.
4. `aa-kit/no-hex-colour` — no hex/rgb/hsl literal in page code; use `K` or a token utility.
5. `aa-kit/no-hand-styled-button` — no `<button style=…>` / `<button className=…>` in pages; use `Button` (icon-only
   buttons through `Button variant="ghost"`).
6. `aa-kit/no-raw-aa-var` — no `var(--aa-*)` string in page code; use `K` (inline preset) or the Tailwind token.
7. `aa-kit/no-aa-var-definition` — no `--aa-*:` definition outside `core/tokens.css` (CSS checked by a small script,
   because ESLint does not lint CSS).
8. `aa-kit/no-raw-form-control` — enabled when the form controls ship: no raw `<input>`, `<select>`, `<textarea>` in
   pages.
9. `aa-kit/no-legacy-kit` — no new import of CIS `adminUi` or portal `ui.tsx` primitives that the kit replaces.

- All rules are `error`. Existing violations are frozen in `eslint-suppressions.json` (ESLint ≥ 9.24 bulk
  suppressions); CI runs `eslint --prune-suppressions` and fails if the file changed in a direction that adds entries.
  The file only shrinks; it reaches empty when the AA-994 page migration ends.
- The lint step runs inside a **required** job in every app: CIS "Frontend Lint" (drop `continue-on-error`, then add
  it to required checks), Partner "Portal Build" and "Web Build" (made required; CRM web gets ESLint 9 for the first
  time), Booking "Frontend Build" (already required), TripPlanner "Frontend (lint + build)" (already required).
- Each app's pre-push hook runs lint on changed files plus the integrity check.

### 8. Agents cannot edit a copy

A PreToolUse hook in the root repo (`.claude/hooks/kit-core-edit-guard.sh`, registered in `.claude/settings.json` for
Edit, Write, MultiEdit and NotebookEdit) blocks edits to any path under a `_kit/core/` or `ui/core/` folder unless the
file is the canonical copy: `frontend/app/_kit/core/` inside an AA-CIS-App checkout (the main checkout
`apps/AA-CIS-App/` or any worktree whose git `origin` is AA-CIS-App), with the message "edit the CIS canonical copy, then sync".
The same rule is in `.kiro/steering/session-workflow.md` for Kiro. The integrity check stays the real gate; the hook
only saves wasted work.

### 9. One automated visual job per app, from GitHub Actions

- Playwright in Actions (pinned `mcr.microsoft.com/playwright` image), so captures never depend on the agent machine's
  IP. Matrix: 1440×900 and 390×844, light and dark (theme set before first paint through the app's storage key plus
  `colorScheme`).
- Every captured page asserts: no page-level horizontal overflow (`scrollWidth ≤ innerWidth + 1` on `html` and
  `body`, plus no visible element wider than the viewport outside a `ScrollX`/`DataTable` scroller); no
  `console.error` or `pageerror`; no failed same-origin request (status ≥ 400, allowlist per app); the kit frame is
  present (`[data-kit-frame]`).
- Targets: (a) **per PR, no Vercel:** `next build && next start` in the runner with `KIT_GALLERY=1`, which exposes the
  `KitGallery` route (every core component × state); without the flag the route returns `notFound()`, so deployed
  builds never serve it. Gallery shots are compared with committed baselines (`toHaveScreenshot`, small threshold).
  (b) **per PR preview:** public pages of the Vercel preview (CIS, portal, Booking, TripPlanner). (c) **signed in, from
  `main`:** after each production deploy and on dispatch, every listed page of the deployed app, using the existing
  E2E identities (CIS A10b `e2e-cis-admin@`, Booking A10a `e2e-booking@`, both by email code from the e2e mailbox;
  portal the tenant E2E login; CRM web the partner-pool E2E owner).
- Data pages are not pixel-diffed (Dev data changes); they are asserted and archived. Artifacts: PNGs and a JSON
  report, 14-day retention; no Playwright HTML report on signed-in runs (it would show the typed code).
- Each app keeps `e2e/visual/pages.ts`; a unit test fails when an `app/**/page.tsx` route is neither listed nor
  excluded with a reason.
- The job starts report-only; the gallery part becomes required once its baselines are stable.

### 10. Version alignment

Booking moves to Next 16.4.2 with its catch-up. TripPlanner stays on Tailwind 3 (tokens profile only needs CSS
variables); a Tailwind 4 move is a separate optional issue. CRM web may keep its `lucide-react` pin; core imports only
icons present in both ranges, and "Kit consumers" proves it.

### 11. What the ADR does not decide

Page-level layout of each app beyond the frame, TripPlanner's B2C component design, and when the legacy layers are
deleted (that is AA-994's page migration, governed by the suppressions file).

### 12. When to move to a package (re-evaluation trigger)

Move the core to a published package (a public `AdventureAsia365-Ecosys/AA-UI` repo, public npm scope with trusted
publishing, or GitHub Release tarballs) when **any** of these holds: a consumer outside the four workspace app repos
needs the kit; kit changes fall to a few per month after the AA-994 migration; CIS stops being the natural owner (for
example the shells move to core and another app becomes the main user); the app repos go private (ADR 0014 reversed);
or a design-system owner exists who wants independent releases. Because `core/` is import-closed and manifest-tracked,
it becomes that package's `src/` without rework.

### 13. ADR 0011 correction

`aa-ci-bot` is already installed on AA-Partner (its release PRs, for example #64, are authored by
`aa-ecosys-ci-bot[bot]`); the install row of ADR 0011 decision 1 is updated in the same root PR.

## Consequences

- (+) One place to change a token or component; integrity makes a forked copy impossible to merge, provenance makes a
  copy ahead of CIS impossible to merge.
- (+) Works with every build path we have (Vercel remote `npm ci`, alpine Docker, Turbopack root): the files are in
  the repo, nothing is fetched, no token or new vendor account.
- (+) The common case in AA-994 (a CIS page change plus a kit fix) is one PR in one repo; agents read the kit as
  source in every app.
- (+) Consumer breakage is found before the CIS merge ("Kit consumers"), not after.
- (+) Each app compiles the core with its own toolchain, so version skew shows up as a failing check, not a runtime bug.
- (+) Rules are identical in every app because the rule file is part of the copy.
- (+) Contrast is gated once, on the canonical tokens.
- (−) Up to five PRs per core change (CIS + up to four sync PRs), each with CI and a Vercel preview. Accepted:
  sync PRs are updated in place and merged once a day.
- (−) CIS becomes the release gate for every app's UI; a Booking-only kit need waits in the CIS merge queue, and the
  CIS CI has no path filtering (full backend CI, ~10 min). Mitigated by `local/` plus promotion.
- (−) Four copies in grep results; mitigated by the header line, the edit-guard hook and the integrity message.
- (−) Visible colour change in CIS admin and Booking when the canonical tokens land (one sign-off).
- (−) Byte copies stop kit drift, not page drift; the legacy layers disappear only through the page migration and the
  shrinking suppressions.
- (−) Hand steps for Nghiệp: required checks in AA-Partner (Portal Build, Web Build) and AA-CIS-App (Frontend Lint),
  later the integrity/provenance checks; an `e2e` environment in AA-Booking; the Infra mailbox-role trust gains the
  AA-Booking subject (`accounts/aa365/e2e_mailbox.tf:367-375` lists AA-CIS-App and AA-Partner only).

## Alternatives considered

- **Option A — `@aa-ecosys/{tokens,ui,eslint-plugin}` from a new public AA-UI repo on public npm (trusted
  publishing), fanned out by bump PRs.** Rejected for now: two hops for every change including CIS (AA-UI PR →
  release → bump PR per consumer, ~1 h wall clock), consumer breakage found only after publish, `package-lock.json`
  conflicts in the merge queues, kit source hidden in `node_modules` (agents write local workarounds), a new npm
  supply-chain path and permanent releases (no unpublish after 72 h), and nothing ships until Nghiệp creates the repo,
  the npm org and three trusted publishers. Its strengths (semver, neutral owner, an unauthenticated gallery) are kept
  as the decision-12 trigger and as the `KitGallery` route.
- **GitHub Packages npm.** Requires a token even for public installs; Vercel's remote builders would need a long-lived
  personal token in four projects, against ADR 0011.
- **Git-tag dependency.** Needs `git` in alpine images and cannot install a subfolder of a workspace.
- **Canonical copy in the root repo.** The root goes private again in November; consumer CI could not read it without
  a token (the reason Infra's contract-copy guard checks pins locally).
- **Keep the status quo (copies + the live-compare Partner check).** Already failed: five diverging token sets, a
  check that cannot be required, and no check at all in Booking and TripPlanner.
