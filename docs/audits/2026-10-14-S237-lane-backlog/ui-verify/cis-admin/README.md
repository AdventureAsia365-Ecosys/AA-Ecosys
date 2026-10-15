# UI verify: S237 CIS admin (15/10/2026)

Read-only check. The only write was the login POST. No Save, Save label, Save limit, Cut, Rewrite, Edit or
Publish was clicked. On the Daily publish limit field, values were typed into the input to watch validation
and then cleared. That is local state only, and no request was sent.
Tooling: Playwright with Chromium, one browser, a new context for each width and theme, and no stored profile.
Scripts are in `.tmp-session/s237/uiv/cis-admin/`. The password was read from Secrets Manager
(`aa-cis/dev/e2e-test-admin`) into the Node process only. It is not in any file here.

Target
- `https://aa-cis.lumiguides.it.com` (Vercel, main). Backend api/worker `dev-1eb2dd0`.
- Account: E2E admin `e2e-claude-code`.
- Fixtures:
  - T9 piece `ccb0843c-…` (Atlas & Hearth, blog, 3 attempts).
  - T2 version `75116f75-…` (Atlas & Hearth, *Laos to Vietnam by Bicycle* v2, `needs_review`, 3 flagged sentences).
  - Tenant `atlas-hearth` (`9149d3c6-…`).
- Theme set the way the app does it: `localStorage.cis_theme`, which resolves to `<html data-theme>`. All four runs got the
  theme they asked for. The admin pages are not pinned to light.

## Summary

| Issue | PR | Verdict |
|---|---|---|
| AA-791: per-attempt gate ledger + Label in Content Quality | #735 (+ #734 mig 231) | **PASS with defects**: Label column, filter and drawer section work. The per-attempt ledger is **not verifiable** (no T9 piece written since deploy) |
| AA-802: T2 silent correction + "older copy" indicator | #732 | **NOT VERIFIABLE**: the T2 correction drawer renders correctly, but no piece or version is in the "older copy" state, and making one needs a write |
| AA-668: Writer panel | #737 | **NOT VERIFIABLE** on admin: the feature is on the tenant portal (Social Content Slate). As admin, every `/api/tenant/*` call returns 401 |
| AA-819: daily publish limit override | #727, #730 (+ mig 230) | **PASS** |

## Matrix (1440 / 390 × light / dark): `<page>-<w>-<scheme>.jpg`

| Page | HTTP / API | Console errors | Overflow @390 | Data | Verdict |
|---|---|---|---|---|---|
| `/admin/overview` (landing) | all `/api` 2xx | 0 ×4 | none | real | PASS |
| `/admin/content-quality` Pieces (T9) | `pieces` 200, `labels_enabled: true` | 0 ×4 | none | 50 rows/page of 193; cards at 390 | PASS |
| Piece drawer `?piece=ccb0843c…` | detail + `…/label` 200 | 0 ×4 | none | real text, Label section, Attempts | PASS |
| `/admin/content-quality?tab=versions` | `tour-versions` 200 | 0 ×4 | **69 px** (D1) | 29 versions | PASS with defect |
| Version drawer `?version=75116f75…` | detail 200 | 0 ×4 | 69 px, page behind the drawer (D1) | 3 flagged, Cut/Rewrite/Edit | PASS |
| `/admin/content-quality?tab=stats` | 200 | 0 ×4 | none | real | PASS |
| `/admin/tenants?tenant=atlas-hearth` (Tenant 360 › Settings) | 8 calls, all 2xx | 0 ×4 | none | real | PASS |
| `/portal/t7-planning` as admin | `/api/tenant/me`, `v1/slate`, `v1/billing`, `v1/tours/my-versions`, `v1/tours/pool` → **401** `{"detail":"Not authenticated"}` | 5 ×4 (the 401s) | none | "Couldn't load Social Content" | n/a, not an admin page (D2) |

All admin pages had 0 console errors and no non-2xx `/api` calls in all four runs. The `ERR_ABORTED` entries on Overview
in `results.raw.json` come from the script navigating away from the post-login landing page. They are not app errors.

## Per issue

### AA-791 (#735): PASS with defects
- Pieces table: new **Label** column, plus a **Label** filter with Any / Labelled / Not labelled / As-is / Light edit / Heavy edit /
  Reject (`cq-pieces-*.jpg`). `GET /pieces` returns `labels_enabled: true`, so migration 231 is live, and the `…/label` GET is 200.
  No piece is labelled yet: every row shows "—".
- Piece drawer **Label** section (`cq-piece-drawer-label-*.jpg`):
  - As-is / Light edit / Heavy edit / Reject cards with their criteria hints.
  - Fact / Voice / Format / AI phrasing levels, Minutes to fix, Reason, and a **Save label** button (not clicked).
  - Layout holds at 390.
- **Not verifiable: the per-attempt gate ledger.**
  - None of the newest 100 T9 pieces has `repair_log[].gate_ledger`, although 83 have a repair_log.
  - The newest T9 piece is from 2026-10-14 05:36 UTC, before the AA-791 deploy.
  - The drawer's Attempts section therefore shows only the raw repair_log JSON, with no "Attempt n · failed gates" lines
    (`cq-attempt-ledgers` absent) (`cq-piece-drawer-attempts-*.jpg`). This is the expected fallback for older pieces.
  - Re-check after the next T9 write that needs 2 or more attempts.
- Not done (write): saving a label, and the label filter with a labelled piece.

### AA-802 (#732): NOT VERIFIABLE
- Visible and correct (`cq-version-drawer-top-*`, `cq-version-drawer-flags-*`):
  - Status line, then the note "Edits change the tenant's copy in place: no new version, no notice and no flag for the
    tenant. Each edit is kept under Admin edits with the text before and after."
  - **Flagged sentences · 3** (T3_grounding "number not in the source tour", 1954), each with **Cut / Rewrite / Edit**.
  - "Text, click a sentence to edit it", Escalations · 1, Cost by stage, Stored rewritten content.
  - 12 of the 29 versions are `editable`.
- The "older copy" indicator never shows in the data:
  - The piece and version detail both return `tenant_copy`.
  - Every scanned T9 piece (100) and every T2 version (29) has `older_copy: false`, and no version has `admin_edits`.
  - So `cq-older-copy` does not render anywhere. That is correct for this data, but the indicator itself was not seen.
- Seeing the indicator needs an admin sentence edit on a piece or version that was already published or exported (a write).
  The tenant-side check (the tenant API returns the repaired text) also needs a write. Both are out of scope here.

### AA-668 (#737): NOT VERIFIABLE (on admin)
- The PR changes only the tenant portal: `WriterPanel.tsx`, `SlateTab.tsx`, `AngleGateWizard.tsx`, and the kit Toast z-index.
  No admin page shows the writer panel.
- RBAC allows admin on `/portal`, but the tenant BFF answers 401 to the admin session. `/portal/t7-planning` renders the shell
  with "Couldn't load Social Content · Not authenticated" (`portal-t7-planning-as-admin-*.jpg`, light and dark both follow the theme).
- Opening the panel needs a tenant login, a Subject pick (`POST /v1/subjects/{id}/pick`, a write) and a paid T8/T9 run.
  Sibling folder `../portal-668/` has portal screenshots from another run.

### AA-819 (#727 + #730): PASS
- Tenant 360 header has the stat **Publish Limit · 20/day (default)** (`tenants-360-header-*.jpg`).
- Settings › **Daily publish limit** (`tenants-settings-dpl-*.jpg`):
  - Hint: "Publishes this tenant can make per UTC day. Leave empty to use the default (20/day)."
  - Input: empty, with the placeholder "default 20".
  - **Save limit** is disabled until the value changes. The line reads "Current: 20/day (default)".
  - "Use default" is hidden, which is correct when there is no override.
- `GET /admin/tenants` returns `daily_publish_limit` for every tenant (all `null`). So the backend half (#730, mig 230) is live,
  and the editor is enabled rather than in its read-only "—" state.
- Local-only interaction at 1440-light, with nothing sent:
  - Typing `2` enables Save limit (`tenants-settings-dpl-typed-1440-light.jpg`).
  - Typing `5000` shows "Daily publish limit must be an integer from 1 to 1000, or empty for the default." and disables Save
    (`tenants-settings-dpl-invalid-1440-light.jpg`).
  - Clearing the input disables Save again.
- Not done (write): saving an override, "Use default", the audit row, and the 21st publish returning 429.

## Defects

| # | Sev | Page | Description | Evidence |
|---|---|---|---|---|
| D1 | Low | `/admin/content-quality?tab=versions` @390 | The page scrolls horizontally by 69 px: the Tour versions toolbar (search + "All tenants" select) is `display:flex` without wrap. It predates S237 (AA-769, 13/10) and is not caused by these PRs. The Pieces tab wraps correctly. | `cq-versions-390-light.jpg` |
| D2 | Info | `/portal/*` as admin | RBAC lets admin open the portal "for support", but every tenant API answers 401, so the admin sees only error states. This predates S237. It also means portal features cannot be checked with the admin account. | `portal-t7-planning-as-admin-1440-light.jpg` |

## Blocking Done
- **AA-819**: the admin part is verified. The rest of Done-when (the 21st publish returns 429, portal notice screenshots, T9
  testimonial test, TripPlanner badge) is outside this admin check.
- **AA-791**: Label is done on the UI side. Still to do: a live label save, and one post-deploy multi-attempt T9 piece to show the per-attempt ledger.
- **AA-802**: still needs one admin edit on a test tenant's version or piece (ideally one already exported) to see `cq-older-copy` and the tenant read.
- **AA-668**: needs a tenant session on Dev (AA-741 tenant test login).

## Files
- `results.json`: summary, per-page matrix, data scan counts and defects.
- `results.raw.json`: every captured page with console, `/api` status and DOM probes.
- 50 JPEG screenshots (quality 70).
