# AA-791 live verify: label form starts with no verdict, LABEL column next to Status (CIS #755)

- Session: S239, 2026-10-16, agent: Claude Code (workflow subagent)
- Target: https://aa-cis.lumiguides.it.com/admin/content-quality (Dev), CIS `origin/main` = `d9ccb605` (#755)
- Login: admin `e2e-claude-code` (secret `aa-cis/dev/e2e-test-admin`, read in-process, never printed or saved)
- Dev write: **one** label row, approved by Nghiệp in S239 as a test edit
- Script: `aa791_verify.mjs` (copy of `.tmp-session/s239/aa791_verify.mjs`), raw output `run-probe.json`, `run-all.json`
- Console errors: 0. Network 4xx/5xx on `/api/`: 0 (both viewports).

## Piece used

| Field | Value |
|---|---|
| piece_id | `dde74641-455f-4d9d-9c8e-696dc3a456c8` (S239 AA-768 piece) |
| Tenant / channel / status | Terra Family Expeditions / blog / held (attempt 3) |
| Title | Cycling Laos with Family: Luang Prabang to Nong Khiaw |
| Before the test | `GET .../pieces/{id}/label` 200, `labels = []`, `mine = null` (unlabelled) |

The other candidate `a7e18faf-4b68-4453-8020-000e38109674` (Atlas & Hearth, linkedin, held) was also unlabelled and was **not** touched.

## Steps and results

1. Opened `/admin/content-quality?tab=pieces&piece=dde74641…` at 1440 light. Label section: As-is / Light / Heavy / Reject all `aria-checked="false"`, **Save label disabled**, hint "Pick a verdict to save" shown. → `01-unlabelled-no-verdict-save-disabled-1440-light.png`
2. Picked **Light edit**, Voice = light, Minutes to fix = 5, Reason = `ZZ S239 test label`. Light `aria-checked="true"`, Save enabled, hint gone. → `02-light-voice-5min-reason-filled-1440-light.png`
3. Save: `POST /api/admin/content-quality/pieces/dde74641…/label` → **200**. Request body `{"label":"light","defects":{"voice":"light"},"minutes_to_fix":5,"reason":"ZZ S239 test label"}`. Toast "Labelled Light edit"; button turns to "Update my label", "Saved Oct 16, 09:12 AM". → `03-saved-toast-1440-light.png`
4. `GET /api/admin/content-quality/pieces/dde74641…/label` → **200**, one label: `mine.label = "light"`, `defects = {voice: light}`, `minutes_to_fix = 5`, `reason = "ZZ S239 test label"`, `labelled_at = 2026-10-16T02:12:36.213810Z`, `text_changed_since_label = false`, **`labelled_by = "admin:2d8e5a2f-3722-4571-9327-177d10b74127"`** (see defect D1).
5. API filters: `GET .../pieces?label=labelled` → 200, total **1**, contains the piece (`label = light`, `label_count = 1`); `?label=light` → 200, total 1, contains the piece.
6. UI table `?tab=pieces&label=labelled` at 1440 light: 1 row (the piece), Label select = "Labelled". Header order WRITTEN, TENANT, CHANNEL, TITLE / ANGLE, STATUS, **LABEL**, BLOCKING FAILS, WARNINGS, ATT., COST. LABEL header at x 1244–1331 (inside 1440), row cell "LIGHT EDIT" at the same x. Page `scrollWidth = clientWidth = 1440` (no page-level horizontal scroll; the table wrapper still scrolls sideways for the gate-chip columns after LABEL, as designed). → `04-labelled-filter-label-badge-1440-light.png`
7. 390 dark (`cis_theme = dark`, `data-theme = dark`): Labelled filter shows the piece as a card, no page horizontal scroll (384/384). → `05-labelled-filter-390-dark.png`. Drawer at 390 dark: Light edit selected, Voice light, 5 min, reason, "Update my label", "Saved …". → `06-drawer-saved-label-390-dark.png`

## Verdict per Done-when bullet (AA-791)

| Done-when bullet | Verdict | Evidence |
|---|---|---|
| New pieces keep every attempt's ledger | Verified earlier (S237 comment on piece `db7f46b9`), not re-tested here | Linear comment 2026-10-15 |
| Label action works on Dev (UI verified) | **PASS** | steps 1–7 above; both S237 defects (As-is pre-selected, LABEL off-screen at 1440) are fixed live |
| Fault set in CI with each rare gate catching its planted fault | **Not covered** by this check (no 30-piece fault-injection set seen in #755) | still open |

So AA-791 is still **not Done**: the 30-piece fault-injection set in CI is open.

## Test label cleanup

- The API and UI have **no way to delete or clear your own label**: the router has only `GET` and `POST /pieces/{id}/label` (POST requires a `label` in as_is/light/heavy/reject; it upserts and cannot clear), and the drawer has no remove button. So the label was **left in place**.
- No DB delete was run from this check. CIS `docs/implementation-notes/AA-791.md` plans to delete the row through the destructive-ops DRY RUN procedure. That needs its own approved run.
- **Exact row identity** (PK `(piece_id, labelled_by)` in `acp_shared.content_piece_label`):
  - `piece_id = 'dde74641-455f-4d9d-9c8e-696dc3a456c8'`
  - `labelled_by = 'admin:2d8e5a2f-3722-4571-9327-177d10b74127'` (the e2e admin `e2e-claude-code`'s user id)
  - `reason = 'ZZ S239 test label'`, `labelled_at = 2026-10-16T02:12:36.213810Z`
- To leave it out of AA-783 analysis, use `NOT (piece_id = 'dde74641-…' AND labelled_by = 'admin:2d8e5a2f-3722-4571-9327-177d10b74127')`, or `labelled_by <> 'admin:2d8e5a2f-3722-4571-9327-177d10b74127'` (or `reason LIKE 'ZZ %'`). **Do not** use `labelled_by LIKE 'admin:e2e%'` (see D1).
- At the time of this check it is the **only** label row on Dev (`?label=labelled` total = 1), so AA-783 has no real human labels yet.

## Defects / notes

- **D1 (medium, data/process):** `labelled_by` stores the admin's user UUID (`admin:<x-admin-user-id>`), not the username. The fallback exclusion in CIS `docs/implementation-notes/AA-791.md` (`labelled_by LIKE 'admin:e2e%'`) **matches nothing**, and the note "keyed `(piece_id, admin:<e2e user>)`" suggests a username. Fix the note to the UUID filter above (or map UUID → username in the analysis).
- **D2 (low, UI):** for the same reason, the drawer's "Other labellers" list prints `labelled_by.replace(/^admin:/, "")`, so another admin's label shows as a raw UUID, not a name. This makes it harder to read AA-783 inter-labeller agreement. The UUID → username mapping was not checked against another admin's view in this run.
- No other defects: 0 console errors, 0 API errors, no page horizontal scroll at 1440 or 390.
