# AA-967 (CRM-35 Module 18 portability + deletion): live check of export, erasure DRY RUN / run, AA staff 403 (S261, 31/10/2026)

Lane 2 item 3 of the S260 In Progress triage (`docs/audits/2026-10-30-S260-inprogress-triage/README.md` §4, §6).
Run by the agent at 02:42–02:44Z, Dev only, synthetic agency only.

**Result in one line:** the export, the DRY RUN, the AA staff 403 and the refusals pass live. The **real erasure did not
run**. Dev has deletion switched off (`LIFECYCLE_DRY_RUN=true` in the live CRM task definition), so the run answered
409 `deletion_dry_run`, as designed. Because the client was never erased, the receipt, the verify and the
"second dry run → `subject_not_found`" step could not happen. They are written up as an orchestrator step below, with a
ready-to-run spec.

## How it was run

- Headless Chromium (Playwright `@playwright/test`), one browser, closed at the end. Egress checked first: VN, not the VPN.
- Deployed CRM API: `/crm/health` `git_sha 3718242a`, version 0.11.0. Live task definition `aa-crm-dev-api:85` (read
  only): `ENVIRONMENT=dev`, **`LIFECYCLE_DRY_RUN=true`**.
- Agency: the e2e **owner** of the synthetic agency "Lữ hành Sen Vàng" (`bab16039`). It signed in through the partner
  pool's managed login with a password and an authenticator code. The credentials were read at run time from the e2e
  user's secret (read only) and were never printed or written down.
- AA staff: the A10 **E2E reviewer** ("E2E Cognito", workforce pool, client `cis-admin`). It signed in on the CIS
  production host `https://aa-cis.lumiguides.it.com` with an e-mail code read from the e2e mailbox. The session landed on
  `/admin` with `cis_role=reviewer`, an `access` token and group `cis-reviewer`. The agent used the access token from the
  `cis_admin_token` cookie as a Bearer token on the CRM API through the agency host
  (`https://portal.lumiguides.it.com/crm/v1/...`). The token was never logged. No screenshot was taken on the
  managed-login host.
- Agency writes went through the CRM BFF from the signed-in page (`fetch('/bff/…')`, same origin). "Check erasure" and
  "Erase this client now" were **clicked in the UI** (Settings › Data and privacy).
- The specs are local only and not committed: root `.tmp-session/S261/aa967/` (`erase.spec.ts`, and `erase-run.spec.ts`
  for phase B). The run log ([`run-log.txt`](run-log.txt)) and the data file ([`run-data.json`](run-data.json)) hold
  ids cut to 8 characters, statuses, counts and hashes. They hold no tokens, codes or contact data. Link tokens appear
  only as `<unused link>`.

## Steps and results

| # | Step | Result | Evidence |
|---|---|---|---|
| 1 | New synthetic client "E2E S261 Erase vsq3k7" (`@example.invalid`), **no trip** | `POST /bff/travelers` **201**, client `15931fb1` | `02-client-created-no-trip-1440.png` |
| 2 | **Export first**: one-client export | `POST /bff/data/exports` (scope traveler) **201** queued → **ready** 25/25 in a few seconds: 2 rows, 25 tables, 17,612 bytes, SHA-256 `8979b0d4…00b3` | `03-…` (Export list: "READY · One client · 2 records in 25 tables") |
| 3 | Single-use link, agency download | link **200**. Download **200** `application/zip`, 17,612 bytes, 53 ZIP entries. The SHA-256 of the downloaded bytes **equals** the checksum the page shows | `run-data.json` `download_1` |
| 4 | **AA staff token** (E2E reviewer) on `GET /crm/v1/data/exports/{id}/download?token=<a fresh, unused link>` with the agency's `X-AA-Tenant-Id` | **403 `wrong_audience`** | `run-log.txt` line 12 |
| 4b | Same token on `GET /crm/v1/data/exports` | **403 `wrong_audience`** | `run-log.txt` |
| 4c | Control: the same download without a token | **401 `missing_bearer_token`** (so the 403 above comes from the token's audience, not from a missing token) | `run-log.txt` |
| 4d | The agency then uses **the same link** | **200**, same SHA-256. The staff call was refused before it touched the link. A second use of the link → **403 `link_invalid`** (single use) | `run-data.json` `staff_checks` |
| 5 | Erasure request logged for the client (kind erasure, e-mail, received today) | `POST /bff/data/requests` **201**, due 30 Nov 2026 | `03-settings-data-export-ready-request-open-1440.png` |
| 6 | UI › **Check erasure** (DRY RUN) | `POST /bff/travelers/{id}/erasure` `dry_run:true` → **200**. It would remove `traveler` 1 and `traveler_profile` 1 (every other table 0). Kept: `signature_event` 0, `terms_acceptance` 0. Exceptions: none. Exports withdrawn: **1** (the export of step 2). Page: "Erasing removes 2 records now; the trash is skipped." | `04-erasure-dry-run-preview-1440.png`, `04b-…-element-1440.png` |
| 7 | UI › **Erase this client now** (real run) | **409 `deletion_dry_run`**. Page: "Deletion is switched off on this environment: the daily run, erasures and offboarding only count what they would remove." Nothing was deleted: the client still answers 200, a dry run still answers 200, and the request stays **open** | `05-erasure-run-answer-1440.png`, `05b-…-390.png` |
| 8 | Side check: a DRY RUN on an id that is no client | **404 `subject_not_found`**. This proves the code mapping (CRM13) live. It is **not** the post-erasure proof | `run-log.txt` |
| 9 | Side check: a DRY RUN on the AA-955 signer (lead of the Booked trip `13efea13`) | **409 `traveler_on_trip`** (CRM12) | `run-log.txt` |

Layout: 0 px sideways overflow on every shot (document and `main`), including 390 px. Console errors: 4. All four are
the deliberate refusals (403 link reuse, 409 run, 404, 409). CRM responses ≥ 400: only those four. No 5xx.

### `crm.signature_event` DELETE as `crm_app` (card R)

The agent ran no DB statement. It cites two sources instead:

- `apps/AA-Partner/api/tests/integration/test_crm026_schema.py::test_r_crm_app_cannot_delete_a_signature_event`. It
  runs `DELETE FROM crm.signature_event WHERE true` as `crm_app` inside a tenant transaction and expects
  `InsufficientPrivilegeError`. CI runs it in the `test-integration` job on PostgreSQL with the RDS role shape
  (`.github/workflows/ci.yml`; skipped tests fail the job).
- Live catalog (`docs/architecture/db-schema-reference.md`, dump verified 30/10 15:16Z, CRM at crm-027): the grant on
  `crm.signature_event` for `crm_app` is **INSERT, SELECT** only. Two more guards: the triggers
  `signature_event_append_only` (BEFORE DELETE OR UPDATE) and `signature_event_no_truncate` call
  `crm.ledger_append_only()`.

### CRM12 decision (approved S261), recorded

Today `crm.erase_subject` refuses a client erasure (CRM12 `traveler_on_trip`) while the client is on **any trip that
is not trashed** (`deleted_at IS NULL`). A cancelled or completed trip therefore still blocks.

**Decision:** a trip that is **cancelled**, or **completed past the claim-start mark**, counts as **closed**. It no longer
blocks a client erasure. The signed evidence (`crm.terms_acceptance`, `crm.signature_event`) is **kept** through that
erasure under the DM-7 claim-period exception: the receipt counts the kept rows and names the exception
`signed_agreements_claim_period`. The code change belongs to the follow-up "CRM-35b".

## Done-when lines (Linear AA-967)

| Line | Status |
|---|---|
| Export | **PASS**, live: one-client export ready, single-use link, download 200, checksum equal, link reuse 403 (steps 2–3, 4d). The agency export was shown live in S260 |
| DRY RUN → run → verify | DRY RUN: **PASS**, live (step 6). Run, verify and receipt: **NOT RUN.** Deletion is off on Dev (step 7, 409 `deletion_dry_run`). See orchestrator steps |
| `crm.erase_subject()` + `crm_eraser` | DRY RUN path live: the counts come from `crm.erase_subject` run as `crm_eraser` (`app.lifecycle.erase`). The delete path was not run live |
| Signed-agreement exception (Fix B16) | Built: trip and traveller scopes keep the rows and count them (`*_kept`), and the receipt names the exception. Live, only the zero case was seen (`kept` 0/0, no exception). A client whose signed evidence is kept was **not** erased. That case goes to CRM-35b with the CRM12 change |
| **R:** AA staff download → 403 | **PASS**, live: 403 `wrong_audience` with a real, unused link and the agency's tenant header. The control without a token gets 401 (step 4) |
| **R:** DELETE on `signature_event` as `crm_app` → error | **PASS by test + live grant**: `test_crm026_schema.py` (InsufficientPrivilegeError) and the live grant INSERT/SELECT plus the append-only triggers. Not run against the Dev DB |
| **E:** erasure during the claim period keeps only signed evidence and the receipt says so | **Not verified live.** It moves to CRM-35b (claim-period erasure), per triage §6 |
| **E:** verify proves the ciphertext is unreadable | **Not verified live.** For one client the verify is "the same erase as a dry run finds no such client" (rows and F2 pointer gone). The ciphertext / DEK crypto-shred is the agency offboarding path (`KeyProvider.destroy`, per tenant). It was not exercised |

## Not tested, and why

- **The real erasure, its receipt (`crm.erasure_request`, status `erased`, `verified_at`), the request closing
  `done`/`fulfilled`, and the second DRY RUN → `subject_not_found`.** Dev runs with `LIFECYCLE_DRY_RUN=true`. Turning it
  off is an ops decision (DM-7.2) and a Terraform / task-definition change, which this lane may not make.
- **DEK cache TTL wait (300 s).** A one-client erasure deletes rows and destroys no key (the DEK is per agency). The
  wait applies to offboarding (AA-934 note). The phase B spec still waits 305 s before the second dry run, as the
  triage asks.
- **Claim-period exception with kept evidence, and the CRM12 change.** These go to CRM-35b.
- **Agency offboarding / crypto-shred.** Not part of this item.
- **DELETE on `crm.signature_event` against the Dev DB.** This would need DB Migrate run-script, which this lane may not
  use. The CI integration test and the live grant stand in for it.
- **Vietnamese UI and dark mode.** Not part of this item.

## Findings (minor, UI copy and layout)

- **F1:** the dry-run preview reads "1 exports that may hold this client's data are withdrawn". The plural is wrong for
  one export (`04b-…`).
- **F2:** a refused run shows its message at the top of the "Export your data" section, far above the request row the
  owner clicked. At 1440 px it is out of view after the click (`05-…`: the red line above "EXPORT YOUR DATA").
- **F3 (note):** the BFF does not pass the API's `X-Content-SHA256` header to the browser. The page shows the
  checksum from the export list, and the downloaded bytes match it.
- **Screenshot artefact:** in the full-page shots the fixed sidebar is drawn part-way down the page. This comes from
  Playwright's full-page stitching, not from the app.

## State left on Dev (synthetic only)

- Client `15931fb1` "E2E S261 Erase vsq3k7" (`@example.invalid`, no trip) is kept on purpose. Its erasure request is
  **open** (due 30 Nov 2026), and its export `c8ca2a60` is ready (it expires 7 Nov). Phase B erases it.
- The four older open requests from S260 (`72d04ad3`, `9c94bbf2`, `3ca10464` erasure, `d619894e` export) were left
  untouched.

## Screenshots

| File | What |
|---|---|
| `01-cis-staff-signed-in-reviewer-1440.png` | The E2E reviewer signed in on the CIS admin (the token source for step 4) |
| `02-client-created-no-trip-1440.png` | The new synthetic client, no trip |
| `03-settings-data-export-ready-request-open-1440.png` | Settings › Data and privacy: the one-client export READY, the erasure request open |
| `04-erasure-dry-run-preview-1440.png` | After "Check erasure" (DRY RUN) |
| `04b-erasure-dry-run-preview-element-1440.png` | The request row with the DRY RUN preview (2 records, 1 export withdrawn) |
| `05-erasure-run-answer-1440.png` | After "Erase this client now": "Deletion is switched off on this environment…" (409) |
| `05b-erasure-run-answer-390.png` | The same at 390 px |

## Phase B: real erasure drill (S261, 31/10/2026, approved by the tech lead)

`LIFECYCLE_DRY_RUN` was turned off on the Dev CRM API only for the drill window: AA-CIS-Infra #547 (targeted apply of
`aws_ecs_task_definition.crm_api`, revision 90, Deploy Dev run 41178325482 → service revision 91, image `d29e29e6`),
then back on by #548 (revision 92, Deploy Dev run 41179253892 → service revision 93, `LIFECYCLE_DRY_RUN=true`, rollout
COMPLETED). The daily `crm_lifecycle` run is at 19:00Z (its last two dry runs counted 0 rows for every agency), so no
scheduled delete ran in the window. Data touched: the synthetic client `15931fb1` only.

| Step | Result |
|---|---|
| UI › Erase this client now | **200**, receipt `f9eac7bd`: counts `traveler` 1, `traveler_profile` 1; kept `signature_event` 0, `terms_acceptance` 0; exceptions none; exports withdrawn 1; `backup_purge_by` 2026-11-30; copies outside AA named (agency mailboxes / messaging accounts, supplier manifests already sent, agency downloads); `verify.subject_gone = true` |
| Client after | `GET` client **404** `traveler_not_found` |
| Erasure request | **done**, fulfilled with the receipt |
| Second DRY RUN after the 300 s key cache TTL | **404** `subject_not_found` (the per-subject key is gone; the ciphertext cannot be read) |
| Export made before the erasure | status **cancelled**; its link **409** `export_not_ready` |

Screens: `06b-erasure-done-receipt-1440.png`, `06-erasure-done-receipt-element-1440.png`. The R line (AA staff
download → 403; DELETE on `signature_event` as `crm_app` refused) is in the phase A table above.

