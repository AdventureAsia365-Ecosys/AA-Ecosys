# AA-1174 live verify on Dev (S288, 2026-11-23)

Issue: privacy obligations on Platform > Compliance readiness (CIS #1642, migration 471; Partner #379, crm.ops.v1 1.18;
root #946, collector checks). Verifier: live-verify subagent, read-only. Identity for the admin pages: the Dev-only
E2E CIS admin (read-only session, aa-ui-verify 3a). Run: 06:30-06:40 UTC.

## Verdict

**FAIL. Not Done.** Two blockers:

- **F1 (blocker, regression from #1642).** The whole Platform > Compliance page crashes on Dev, on every tab. The
  Overview, Obligations and Controls tabs all render only the error boundary ("Something went wrong / Try again").
  The browser console shows `Error: useToast must be used within a <ToastProvider>` (3x).
  - Cause: `CompliancePage.tsx` now calls `useToast()` at the top of the component for the Refresh feedback.
    `frontend/app/admin/platform/compliance/page.tsx` wraps it in `<Suspense>` only, with no `<ToastProvider>`.
    Other admin pages wrap themselves, for example `aa-content/page.tsx`, `facts/page.tsx` and `jobs/page.tsx`.
  - Fix: wrap `<CompliancePage />` in `<ToastProvider>` inside `page.tsx`, and add the page to an admin smoke so a
    crash fails the run.
  - Why nothing caught it: the post-deploy smoke runs with the content role, which cannot open the page. The
    admin-evidence spec does not list `/admin/platform/compliance`.
  - The API answers normally. `GET /api/admin/platform/compliance` and `.../obligations` both returned 200 through
    the BFF.
- **F2 (blocker, an orchestrator step that has not run yet).** The private register v2 is not loaded. That is
  live_steps step 5. The live register holds 253 requirements, 48 controls, 399 mappings, **1 law (EU AI Act, 7
  obligations)** and **0 applicability rows**. The Vietnam PDPL (Law 91/2025/QH15 with Decree 356/2025/ND-CP), GDPR
  and the matrix are absent. The load step expects 13 frameworks, 53 obligations, 22 matrix rows and 61 controls.

Other findings:

- **F3 (expected state).** No `cis_db` or `crm_ops` evidence row exists yet: the heartbeat shows 0 rows and no
  last_seen for either source. These rows are written only by `POST /refresh` (compliance.write). The E2E admin
  cannot run it, because its session is read-only, and it could not even be clicked because of F1.
- **F4 (Done-when risk).** The root collector from #946 has not run on master since the merge. The last root_daily
  heartbeat is 2026-11-22 10:15 UTC, before #946. The next scheduled run is 02:41 UTC; dispatching it is
  live_steps step 6. An offline run of the merged `collect.py` on a clean export of `origin/master` gave these
  results:
  - `last_erasure_drill`: **pass**, last live drill 2026-10-31.
  - All six `legal_*` checks: **fail**. The checks are `legal_ropa_reviewed`, `legal_dpa_reviewed` (5 pages),
    `legal_subprocessors_reviewed`, `legal_transfer_dossier_vn`, `legal_dsar_runbook_reviewed` and
    `legal_consent_capture_reviewed`. Every page reports "still a draft, not an adopted document", with 0 pages
    past their review cycle.
  - Consequence: the RoPA, DPA, transfer dossier and DSAR runbook obligations will read **not met** until the
    business owner adopts those pages (front-matter status other than draft). That conflicts with the Done-when
    line "evidence-backed items read met". This is a decision for the tech lead, not a code bug.
  - The `last_restore_drill`, `last_access_review` and `vuln_exceptions_valid` errors in the offline run come from
    the partial export (only `tools/compliance` and `docs/legal` were extracted). Ignore them.
- **F5 (expected on Dev, stated by the lane).** `retention_live_enabled` will read not met until each of the 5
  retention kinds has an approved live run that is not a `manual_override`.

## Deploy check

| Service | Live git_sha | Contains the merge |
|---|---|---|
| CIS API `/health/ready` | e8171a8c5 (schema_version 471, status ok) | #1642 merge e8171a8c5: yes (first poll at 06:21 UTC still showed c9f38ea35; e8171a8c5 by 06:23) |
| CIS Deploy Dev / Deploy Admin Dev | both `completed success` on e8171a8c5 | yes |
| CRM API `partner-dev…/crm/health` | 3d20ef122 (0.14.0) | #379 merge 3d20ef122: yes |
| Root master | 1082ff671 | #946 merged 05:24 UTC; collector not yet run on master |

## CRM ops privacy endpoint (crm.ops.v1 1.18)

| Call | Result |
|---|---|
| `GET /crm/ops/v1/privacy-evidence` with no token | 401 `missing_bearer_token` |
| same with `?days=30` | 401 `missing_bearer_token` |
| same with an invalid bearer | 401 `invalid_token` |
| `GET /crm/ops/v1/nonexistent-zz` with no token (control) | 404: routing happens before auth, so the privacy route is registered |
| authenticated 200 with counts | **not checked.** The route accepts only a staff WORKFORCE token of a full OPS reader (cis-admin or crm-platform-admin), relayed by CIS `POST /refresh`. It is not a service credential. The agent has no such token outside the read-only E2E browser session, and Refresh is a write. The response model in code holds counts only: `tenants`, `marketing_sent`, `marketing_uncertain`, `violations`, `excluded_erased`, `consents_recorded`, `last_consent_at`, `window_days`, `as_of`. |

## API data (through the BFF as the E2E admin, 200)

- `GET /api/admin/platform/compliance/obligations`:
  - laws: 1, `eu-ai-act:2024`, with source link `https://eur-lex.europa.eu/eli/reg/2024/1689/oj`;
  - items: 7, all `not_checked`, none with `doc_url` and none with evidence;
  - applicability: 0 rows;
  - settings include `applicability_review_max_age_days` 180, `validity_hours` {root_daily 72, cis_db 72,
    crm_ops 72}, and fact limits for every privacy check. For example `last_erasure_drill` 180 days,
    `consent_capture_present` 90 days, `campaign_consent_enforced` violations max 0, `retention_runs_recent` 3 days
    and `retention_live_enabled` 7 days. **Thresholds and validity windows are settings: pass.**
- `GET /api/admin/platform/compliance`:
  - `framework_info` lists 6 frameworks: 5 standards plus `eu-ai-act:2024` (kind law);
  - checks: 8 pass and 2 fail (`scheduled_guards_green`, `secret_scan_history_green`).
- Side effect of these GETs (by design, not under view-as): the published-file ingest read 10 rows, all new. This is
  the existing sync path that every page view by a non-view-as admin triggers.

## Screenshots

- `compliance-page-crash-desktop-light.png`: `/admin/platform/compliance?tab=obligations` at 1440 px. The Overview
  and Controls tabs gave a byte-identical image, so only one copy is kept. No mobile or dark shots, because the page
  never renders.

## Not checked, and how to close it

1. **Obligations tab content, matrix, Refresh toast.** Blocked by F1 and F2. After the fix PR deploys and the
   register v2 load completes, re-run this verify:
   - E2E admin: the tab, the matrix, and the official source links (vbpl / eur-lex hosts, `rel=noopener noreferrer`).
   - Tech lead (owner, not read-only): press Refresh evidence and screenshot the success toast and the result line.
2. **Compliance GET writes nothing under view-as.** Needs an owner view-as session, which the E2E admin cannot start,
   plus DB aggregates before and after. Script:
   `/home/nghiep/projects/AA-Ecosys/.tmp-session/S288/live/aa1174_compliance_aggregates.py`.

---

# Round 2 (S288, 2026-11-23, 07:24-07:32 UTC)

Re-check after CIS #1646 deployed (ToastProvider fix), the private register v2 load, and a dispatched run of the root
Compliance evidence collector. Same identity: the Dev-only E2E CIS admin (read-only session). Scratch spec (not
committed): `.tmp-session/S288/live/aa1174/aa1174-live.spec.ts` (+ `aa1174-overflow.spec.ts` for the mobile check).

## Round 2 verdict

**Not Done: 1 Done-when line fails, 4 pass.** F1 and F2 from round 1 are fixed. The page renders on every tab, and
register v2 is live. The line that fails is "evidence-backed items read met". On Dev, **0 of 60 obligations read met**.
That is not a code bug. Two things block it, and both are outside this verifier's reach:

- **D1 (decision for the tech lead).** All six `legal_*` checks fail with "still a draft, not an adopted document". The
  checks are `legal_ropa_reviewed`, `legal_dpa_reviewed` (5 of 5 pages), `legal_subprocessors_reviewed`,
  `legal_transfer_dossier_vn`, `legal_dsar_runbook_reviewed` and `legal_consent_capture_reviewed`. So the RoPA, DPA,
  sub-processor, transfer dossier and DSAR runbook items stay **not met** until the business owner adopts those
  pages (front-matter status other than draft). The other choice is to accept "not met" as the honest state for
  now, and to reword the Done-when line.
- **D2 (owner action).** The `cis_db` and `crm_ops` collectors have never run: the heartbeat shows `last_seen` null
  and 0 rows for both. So `consent_capture_present`, `campaign_consent_enforced`, `retention_runs_recent` and
  `retention_live_enabled` read **missing**. Only `POST /refresh` (compliance.write) writes these rows. The read-only
  E2E admin is refused that call, as designed. The tech lead (owner) must press Refresh evidence once. Even then,
  `retention_live_enabled` stays not met until the retention kinds have approved live runs (F5 from round 1).

## Deploy check (round 2)

| Item | Live state |
|---|---|
| CIS admin (`aa-cis-dev-admin`) | task def rollout COMPLETED, image tag `dev-1bb0f35b0…` = #1646 merge 1bb0f35b0. `Deploy Admin Dev` run succeeded, including the signed-in UI smoke and visual jobs (07:24 UTC). |
| CIS API `/health/ready` | `git_sha` 4dbdfafc8, status ok, schema_version 472. It contains the #1642 merge e8171a8c5; #1646 is admin-only. |
| Root collector | `Compliance evidence`, workflow_dispatch on master f5f42c6a8, run 45130504907, **completed success** at 07:22:44 UTC. Both jobs passed: the unit tests, and collect and publish. The evidence file and the day file were uploaded. |
| Heartbeat (API) | `root_daily` last seen 07:22:09 UTC, ok, 37 evidence rows. `cis_db` and `crm_ops`: never heard from (D2). |
| Ingest | The first GET of this run read the published file: state ok, 17 rows, 17 new, 0 dropped. This is the normal non-view-as sync path. |

## Done-when, round 2

| # | Done-when line | Result | Evidence |
|---|---|---|---|
| 1 | The applicability matrix exists, with a primary source for each verdict, and is shown on the page | **PASS** | API: 29 rows, 23 applies, 4 not yet and 2 not applicable. All 29 have an https primary source. The source hosts are congbao.chinhphu.vn, eur-lex.europa.eu, legislation.gov.uk, legislation.gov.au, uscode.house.gov, cppa.ca.gov, law.lis.virginia.gov and pcisecuritystandards.org. Each row carries a source title, `assessed_on` 2026-11-23 and the counsel flag (29 of 29), with 0 rows due for review. Page: the "Applicability by market" section renders the market × law grid. Each cell shows its verdict badge, a Counsel badge, a Test/Threshold tip and a Source link. Shot: `r2-compliance-obligations-desktop-light.png` (top). |
| 2 | The Vietnam, GDPR and every "applies" checklist show on the page live, each item with its state, counsel flag and evidence link | **PASS** (one nit, F7) | 14 law frameworks are registered. The page shows a checklist section for each of the 8 laws with at least one "applies" verdict: `vn-pdpl:2025` (Law 91/2025/QH15 and Decree 356/2025/ND-CP, in force 2026-01-01, 15 items), `gdpr:2016` (15), `uk-gdpr:2018` (9), `eu-ai-act:2024` (7), `can-spam:2003` (5), `eu-eprivacy:2002` (3), `uk-pecr:2003` (3) and `au-spam:2003` (3). No law that applies lacks a checklist. The 6 laws marked not yet or not applicable (AU Privacy Act, CCPA/CPRA, Virginia CDPA, VN Data Law 60/2024, VN Cybersecurity Law 116/2025, PCI DSS) have no checklist, which is correct. There are 60 state cells, one per item. The counsel column is set on 17 items. 53 of 60 items have an "Official source" link and a "Document" link. 31 items list their evidence checks, each with an "Open" link to the evidence. The page has 174 external links, and all of them carry `rel="noopener noreferrer"`. |
| 3 | At least the evidence-backed items (RoPA, DPA, DSAR drill, retention, transfer dossier, campaign consent) read "met" from a real evidence row | **FAIL** (blocked by D1 and D2, not a code bug) | Item states: 0 met, 31 not met (including 6 marked "partly") and 29 not yet checked. Real evidence rows exist and are shown. `last_erasure_drill` is a **pass** (23 days old, limit 180), so the DSAR items for GDPR Art.15-22, UK GDPR Art.15-22 and VN Art.4 and Art.14 read "not met (partly)". Every `legal_*` row is a fail because its page is still a draft (D1). The consent, campaign and retention checks are missing (D2). GDPR Art.32 is partly met through `secret_scan_history_green` = pass. |
| 4 | Thresholds and validity windows are settings | **PASS** | Unchanged from round 1. The obligations API returns `settings`: `applicability_review_max_age_days` 180, `validity_hours` (root_daily, cis_db and crm_ops at 72 each), `heartbeat_hours` 36, `partial_weight` 0.5, and `fact_limits` for every privacy check. The page header links to "Scoring settings". |
| 5 | No UI text claims legal compliance. The page says "readiness, not legal advice" | **PASS** | The Obligations tab note reads "Readiness, not legal advice. Items flagged for counsel need a lawyer's confirmation." The fixed banner on every tab reads "Readiness score (Dev environment), not a certification". The main text of all 3 tabs contains no compliant or certified claim. |

Extra checks from the round 2 brief:

| Check | Result | Evidence |
|---|---|---|
| Overview, Controls and Obligations tabs render (F1 fixed) | **PASS** | No error boundary on any tab. Overview: tiles for 61 controls, 8 met and 7 checks failing, plus the framework cards. Controls: 61 rows; the privacy controls (AAC-PRV-01…11) list their law requirements. Obligations: the matrix and 8 law sections. Shots: `r2-compliance-overview-desktop-light.png`, `r2-compliance-controls-desktop-light.png`, `r2-compliance-obligations-desktop-{light,dark}.png`, `r2-compliance-obligations-mobile-{light,dark}.png`. |
| Register v2 loaded (F2 fixed) | **PASS** | Overview `register`: 306 requirements, 61 controls, 465 mappings, 14 laws and 60 obligations. Obligations API: 14 laws, 60 items and 29 matrix rows. These match the orchestrator's load numbers. |
| Refresh feedback for the read-only admin | **PASS** | Pressing Refresh evidence sent `POST /api/admin/platform/compliance/refresh`, which returned **403** `{"detail":"e2e_read_only"}`. The page showed an error toast, "Refresh failed: e2e_read_only", plus the result line "REFRESH FAILED / e2e_read_only" (`data-tone="error"`). The page did not crash. Shot: `r2-compliance-refresh-refused-desktop-light.png`. |
| Console and network | **PASS** | The only console error is the browser's "Failed to load resource: 403", from the refused Refresh above, which is expected. Compliance API calls: `GET /` 200 (×3), `GET /obligations` 200 (×2), `GET /controls` 200, `POST /refresh` 403. |
| Collector run on master finished | **PASS** | Run 45130504907 succeeded. See the deploy check above. |

## New findings (round 2)

- **F6 (nit, mobile layout).** On the Obligations tab at 390 px, `main` scrolls sideways by **263 px**
  (`main.scrollWidth - clientWidth`; the document itself is 0). Overview and Controls are 0. The elements that
  overflow are the applicability matrix cells (verdict badge, Counsel badge and the Test tip text). They extend 263 px
  past the right edge of `main`, with no clipping scroll container between them and `main`. So on a phone the whole
  page body, not only the matrix, pans sideways. Fix: put the matrix grid in its own `overflow-x: auto` wrapper, or
  give the tip popups a containing block inside the table scroller. Then add the tab to a 390 px overflow check.
- **F7 (nit, data from phase 1).** The 7 `eu-ai-act:2024` items (from AA-1170) have no per-item official source and no
  document link. They read "No automatic check yet", while the law itself links to eur-lex. Every one of the 53
  privacy-law items has both links. Fill these in at the next register load if they are wanted.
- F3 / F5 from round 1 still hold (now D2).

## Not checked (round 2), and how to close it

1. **Owner Refresh (D2).** The tech lead presses Refresh evidence on Platform > Compliance readiness as an owner.
   Expect a success or warning toast, and a result line with `cis_db` and `crm_ops` rows. Then the heartbeat for both
   sources should show a `last_seen`.
2. **The DB counts behind the page** (orchestrator, read-only, aggregates only). Script:
   `/home/nghiep/projects/AA-Ecosys/.tmp-session/S288/live/aa1174_r2_aggregates.py`. Expected: 61 active controls, 465
   mappings, 14 law frameworks, 60 law obligations, 29 applicability rows all with a source, and no "applies" law
   without a checklist.
3. **Compliance GET writes nothing under view-as.** Unchanged from round 1. It needs an owner view-as session, and the
   round 1 script runs before and after it.
