# S241 re-verify: CIS PR #790 on Dev (17/10/2026)

This is a read-only re-check, on https://aa-cis.lumiguides.it.com, of defect **R1** from `../reverify-789/README.md`: pills inside kit
Drawer titles were squeezed letter by letter. It also checks that the #789 Drawer header fixes still hold. The build under test is
CIS `main` **a439085a** (PR #790, a one-line change in `frontend/app/_kit/Drawer.tsx`: `overflowWrap: "anywhere"` → `"break-word"`).

- **Build identification.** The GitHub Actions "Vercel Deploy" run for a439085a finished with `success`. On the live page, the
  computed `overflow-wrap` of the kit Drawer title box is **`break-word`** in all 14 drawer runs. Under #789 it was `anywhere`.
  ("Deploy Dev", the backend ECS deploy for the same SHA, was still in progress at test time. The change is frontend only.)
- **Tooling.** Playwright Chromium, headless, with a fresh context for each width and theme. The script is
  `uiv/reverify790.mjs` in the session scratchpad. It reuses the login, write-blocking and leak-scan code from `reverify2.mjs` and
  `reverify.mjs`. Raw measurements are in `results.json`.
- **Accounts.** The admin is `e2e-claude-code` (`aa-cis/dev/e2e-test-admin`). The tenant is `atlas-hearth`
  (`aa-cis/dev/e2e-tenant/atlas-hearth`). Both secrets are read into process memory only.
- **Writes.** The only writes were 2 login POSTs (admin 200, tenant 200). A route handler aborted every other non-GET request, and
  `blocked_writes` is **empty**. The only control clicked inside a drawer was the Jobs drawer close X.
- **Leak scan.** Before every screenshot, the page text was checked for the tenant key, the admin password, `pk.eyJ…` and JWTs.
  There were **0 hits**.
- **Themes.** The admin pages were checked at 390 and 1440, in light and dark. The tenant portal is pinned light, so it was checked
  at 390 and 1440 in light only.

## Results

A pill counts as **one line** when its height is ≤ 24 px and its width is greater than its height.

| # | Item | Result | Measurement (DOM) | Screenshots |
|---|---|---|---|---|
| 1 | T10 portal drawer (`/portal/t10-review`, "Where Two Worlds Meet…"): header **BLOG** pill on one line | **PASS** | At 390 and 1440, BLOG is **62 × 22.5 px** with no line break in its text. Under #789 it was 38 × 72 px ("B/L/O/G") at 390 and 51 × 39 px at 1440. The title wraps fully, with 4 lines at 390 (319 px wide) and 2 lines at 1440. There is no overflow and no clipped child. The X is at 352–370 (390) and 1402–1420 (1440), and `elementFromPoint` hits it. | `t10-drawer-header-390-light.png`, `t10-drawer-header-1440-light.png`, `t10-drawer-*-light.png` |
| 2 | Admin Content Quality piece drawer (`?piece=21697065…`): header **APPROVED** pill on one line | **PASS** | In all 4 combos, APPROVED is **93 × 22.5 px**. Under #789 it was 59 × 55.5 px at 390. At 390 the title "Built Into the Cliff, Restored From Ash" wraps to 2 lines, and the meta text beside the pill wraps to 3 lines. At 1440 the title is 1 line and the pill and meta are on one row. There is no overflow, and the X is in view and hit. | `cq-piece-drawer-header-{390,1440}-{light,dark}.png`, `cq-piece-drawer-*.png` |
| 3 | Content Quality tour-version drawer: the long title still wraps fully, with the X in view | **PASS** | The title "Laos to Vietnam by Bicycle: Nam Ou River to Hanoi — 12 Days — Terra Family Expeditions v6" is 319 × **77 px (3 lines)** at 390 and 789 × 51 px (2 lines) at 1440. That matches #789. There is no horizontal overflow, no clipped child and no ellipsis. The X is at 352–370 (390) and 1402–1420 (1440), and it is hit. | `cq-version-drawer-{390,1440}-{light,dark}.png` |
| 4 | Jobs drawer (`ops_rds_role_connections`): the X is in view at 390 | **PASS** | At 390 (light and dark), the X is at **352–370** in a 390 px viewport, and `elementFromPoint` hits it. The kind stays on one line with the intended ellipsis ("ops_rds_role_conne…", and the full kind is in the `title` attribute). The SUCCEEDED pill keeps its size. Clicking the X closes the drawer: the dialog count is 0 and `job=` is gone from the URL. At 1440 the X is at 1402–1420 and the kind is not truncated. | `jobs-drawer-390-light.png`, `jobs-drawer-390-dark.png`, `jobs-drawer-1440-*.png` |

**Visual check.** I opened the header and full-drawer screenshots and confirmed the following:

- BLOG and APPROVED are compact one-line pills in light and dark.
- The long titles wrap at word boundaries, with no mid-word breaks or ellipsis.
- The X sits at the right edge in every shot.
- The Jobs kind shows an ellipsis before the SUCCEEDED pill, and the X is visible.

### Console and network, per page

| Page | Console errors | Page errors | Non-2xx |
|---|---|---|---|
| `/portal/t10-review` + drawer (390, 1440) | 0 | 0 | 0 |
| `/admin/content-quality?piece=…` (4 combos) | 0 | 0 | 0 |
| `/admin/content-quality?tab=versions` + drawer (4 combos) | 0 | 0 | 0 |
| `/admin/jobs?kind=ops_rds_role_connections&status=succeeded` + drawer (4 combos) | 0 | 0 | 0 |

## Verdict

R1 is fixed on Dev by #790. The #789 behaviours checked here still hold: long Drawer titles wrap fully and the X stays in view.
No new defects were found.
