# AA-962 — Onboarding + client import: live check on Dev (S261, 31/10/2026)

- **Build checked:** AA-Partner `main` 132112a (PR #146), deployed by Deploy Dev; CRM schema at crm-031 (per the orchestrator).
- **Host:** CRM web + BFF at `https://portal.lumiguides.it.com`; the hosted inquiry page and the public form API at `https://go-dev.lumiguides.it.com`.
- **Who:** the E2E owner of the synthetic agency "Lữ hành Sen Vàng" (partner pool, password + authenticator).
  - Extra role check: the Sen Vàng E2E agent.
  - Isolation check: the Southern Cross E2E owner. No "Atlas & Hearth" E2E identity exists in Secrets Manager (`crm/dev/e2e-test-crm/*` holds Sen Vàng, Southern Cross and Harbour Lights), so Southern Cross served as the second agency.
- **Method:** headless Playwright, one browser at a time, closed at the end.
  - API calls went through the signed-in page's same-origin BFF (`/bff/...` → `/crm/v1/...`). Raw file bodies were sent as `application/octet-stream`, the same way the import wizard sends them.
- **Data:** synthetic only. Run token `vxgmlg`, refs `S261-AA962-vxgmlg-n`, invented names, `@example.test` addresses.
- **Local scripts (not committed):** `.tmp-session/S261/aa962/` (`api.spec.ts`, `ui.spec.ts`, `run-log.txt`, `run-data.json`, `ui-data.json`, `roles-data.json`).

## Result per Done-when line

| # | Done-when line (l3-live.json) | Result |
|---|---|---|
| 1 | Before merge: crm-029 status / renumber | Not part of this live check (pre-merge step, already done by the orchestrator). |
| 2 | Independent review, merge via merge queue | Not part of this live check. |
| 3 | Migration Sync / Apply crm-030, schema dump PR | Not re-checked here (no DB access from this lane); the orchestrator reports crm-031 live. |
| 4 | Deploy Dev rollout COMPLETED, `/health` + `/health/ready` | Not re-checked here; the orchestrator reports Deploy Dev success. All CRM API calls below answered from the deployed build. |
| 5 | `GET /crm/v1/onboarding` → 200 with 3 required steps, connections status codes only, acknowledgement | **PASS.** 200. Required steps: `connect_mailbox`, `invite_team`, `embed_form` (3 of 3 done for Sen Vàng). Connection keys: only `key, status, required, href, help, bank_transfer`, with statuses `connected` / `not_set_up` (no credential, account reference or address). `acknowledgement` = `{version: "2026-10-31.1", accepted: false, ...}`. |
| 6a | Preview with a CSV missing the name column → 422 `missing_columns` | **PASS.** 422 `{"detail":"missing_columns","columns":["name"]}`. No client with the run token existed afterwards (search → 0). In the UI, the wizard shows "The file lacks required columns: name. Nothing was imported." (shot 21). |
| 6b | Valid 3-row CSV, two rows sharing one e-mail → `{create:2, match:1}` + `duplicate_contact` | **PASS.** Preview 200 `counts={create:2, match:1, already_imported:0, duplicate_in_file:0, invalid:0}`, issue `{row:4, outcome:"match", codes:["duplicate_contact"]}`. The returned `sha256` equals the file's SHA-256. |
| 6c | Start import → 202, poll until done | **PASS.** `POST client-imports?entity=clients&sha256=<sha>` → 202 `queued`. `GET client-imports/{id}` reached `done` within about 5 s with the same counts. Client search finds 2 clients ("Thao Sample …", "Bao Sample …"). |
| 6d | Re-run the same file → create 0 | **PASS.** Preview `{create:0, match:0, already_imported:3}`, `can_apply:false`. The second actual import also finished `done` with `create:0, already_imported:3`. The UI preview of the same file shows New 0 / Already imported 3 (shots 22, 23). |
| 7 | Trips CSV naming the shared-contact row's `client_ref` → create 1, invalid 0 | **PASS.** The trips row uses the ref of row 3 (the `duplicate_contact` row). Preview and job both gave `create:1, invalid:0`, status `done`. `GET travelers/<row-1 client>` lists the trip "Hoi An lantern week vxgmlg", stage `completed`, role `lead`, so the alias ref resolved to the client created by row 1. |
| — | Duplicates + merge (owner) | **PASS.** A 2-row file with the same invented name and two e-mails gave preview `create:2` with `possible_duplicate` on row 3. After the import, `GET client-duplicates` showed the pair (`matched_on:["name"]`), and the pair showed on /clients/duplicates at all four sizes/themes. The merge was run **in the UI**: "Keep this one" → confirm dialog (shot 24) → Merge → `POST /bff/travelers/<keep>/merge` 200 (`trips_moved:0`, `purge_after` 7 days). The page shows "Merged." + "No duplicate clients" (shot 25). After the merge: duplicates total 0; the kept client is 200; the merged client is 404 `traveler_not_found` (trashed); re-previewing the same 2-row file gives `already_imported:2, create:0`, so the merged client's ref now resolves to the kept client. Onboarding then shows `import_clients` and `review_duplicates` done and `duplicate_count` 0. |
| — | 409 `merge_blocked` | **PASS** (API). Request: keep the invented duplicate; the client that would go is the lead of the AA-955 e-sign trip (synthetic). Answer: 409 `merge_blocked`, blockers `["client_links","portal_access","signatures","terms_accepted"]`, `swap_possible:true`. That client is still live afterwards (GET 200), so nothing changed. |
| 8 | `PUT /onboarding/controller` (privacy https link, data-request e-mail, consent text); the public form API for a form without its own link returns the three; hosted page screenshot | **PASS.** The PUT gave 200 and echoed the values; an `http://` link gave 422 `invalid_privacy_notice_url`. The privacy-settings step turned done. The active form has no privacy link of its own. `GET /crm/public/v1/forms/<key>` on the client host gave 200 within 1 s: `privacy_notice_url` = the agency link (fallback), `data_request_contact` = the set e-mail, `consent_text` = the set wording. The hosted page `/c/f/<key>` shows the agency's consent wording next to the contact box, a "Privacy notice" link to the agency URL and "To see, correct or delete your data, contact: privacy.vxgmlg@example.test" (shots 26, 27). **Afterwards the Sen Vàng controller settings were put back to their earlier values (all empty)**, PUT 200. |
| 9 | Large `.xlsx` (> 8 MB inflated) → 422 `unreadable_file`, API task memory flat | **NOT TESTED** (see below). |
| 10 | Dev E2E spec `e2e/tests/onboarding-import.spec.ts` + screenshots | Screenshots: **done** (below). The repo spec itself was **not run** through `e2e-dev.yml` (this lane may not run `gh workflow run`). This run covered the same steps by hand-written Playwright on Dev. |

### Extra checks (roles and isolation)
- **Sen Vàng agent:**
  - Refused (403 `role_forbidden`): import preview, merge and `PUT onboarding/controller`.
  - Allowed (200): `GET onboarding` and `GET client-duplicates`.
- **Second agency (Southern Cross owner):** every request about Sen Vàng's records was refused or found nothing.
  - `GET client-imports/<Sen Vàng import>` → 404 `import_not_found`.
  - `POST travelers/<Sen Vàng client>/merge` → 404 `traveler_not_found`.
  - `GET travelers/<Sen Vàng client>` → 404.
  - Its own `GET client-imports` does not list the Sen Vàng import.
- **Console and network:** the console errors and BFF 4xx are only the deliberate ones: the 422 missing column, the 422 http link, the 409 blocked merge and the 404 read of the merged client. No other errors.
- **Layout:** no sideways overflow on any page at 1440 or 390 (document and `<main>` both 0 px).

## Screenshots
All in this folder. Each of the five pages was taken at 1440 and 390 px, light and dark (the CRM web is staff-facing; the hosted inquiry page is customer-facing and was taken at 1440 + 390).

| File | What |
|---|---|
| 01 / 02 / 11 / 12 `onboarding-{1440,390}-{light,dark}` | /onboarding: shared-responsibility card, 3 required steps, optional steps |
| 03 / 04 / 13 / 14 `settings-import-…` | /settings/import: four phase tabs, columns, template link, recent imports |
| 05 / 06 / 15 / 16 `clients-duplicates-…` | /clients/duplicates with the invented "Minh Duplicate vxgmlg" pair before the merge |
| 07 / 08 / 17 / 18 `settings-connections-…` | /settings/connections: connection statuses + privacy settings (at that moment filled with the synthetic values) |
| 09 / 10 / 19 / 20 `help-…` | /help (EN): sections mailbox, team, form, import, duplicates, payments, templates, privacy, kickoff, sms, calendar, esign |
| 21 `import-missing-column-1440-light` | Wizard refusing the file without a name column |
| 22 / 23 `import-rerun-preview-{1440,390}-light` | Re-run preview: New 0, Already imported 3 |
| 24 `duplicates-merge-confirm-1440-light` | Merge confirm dialog |
| 25 `duplicates-after-merge-1440-light` | "Merged." + empty state |
| 26 / 27 `hosted-inquiry-controller-{1440,390}-light` | Hosted inquiry page with the agency consent wording, privacy link and data-request line |

## Not tested, and why
- **Large `.xlsx` memory check (line 9).** Skipped, as the lane allowed. Building the inflated sheet is easy. Showing that the API task memory "stays flat" means reading the ECS / CloudWatch task metrics around the upload, and a CRM task restart would hit the other S261 lanes running on the same service. The streaming reader and its 8 MB budget are covered by the PR's unit tests (compressible member refused, lying zip header, < 40 MB peak for a 6 MB sheet), not by a live run.
- **Repo E2E spec through `e2e-dev.yml` (line 10).** This lane may not run `gh workflow run`. Its steps (checklist, missing column, preview, import, re-run, connections, duplicates) were covered live above.
- **Deploy / migration evidence (lines 3–4).** No ECS, DB Migrate or DB access from this lane. Not re-checked: rollout state, image SHA, `/health/ready`, `crm-030` / `crm-031` registration and the schema dump.
- **Not clicked:** the "I understand and accept" button (the one-time owner acknowledgement), so `accepted` stays false for Sen Vàng. Also not exercised: the "Later" / "Mark done" buttons, and the "keep the other one instead" swap button in the UI (the blocked merge was checked through the API, because a blocked client cannot be made into a duplicate pair without more fixture work).
- **Import phases and limits not run:** relationships and notes; `phone_region`; the 5 MB / 413 `import_too_large` limit; the 409 `file_changed` case.
- **Vietnamese** pages and guides were not opened (EN only).

## Data left on Dev (synthetic, Sen Vàng)
- Clients "Thao Sample vxgmlg" (with the completed trip "Hoi An lantern week vxgmlg"), "Bao Sample vxgmlg" and "Minh Duplicate vxgmlg" (the kept client).
- The merged duplicate is in the trash; it is purged after 2026-11-07.
- Six `crm_client_import` job runs, all `done`.
- Controller settings were put back to empty. The import's audit events stay as written.

## Note
- In the full-page screenshots the dark sidebar stops at the viewport height (900 px) on long pages. This looks like a capture artifact of the fixed sidebar, not a layout fault.
