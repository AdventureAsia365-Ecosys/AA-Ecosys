---
id: OPS-08-s260-live-evidence
title: "S260 live evidence: kit, Booking S6d, LLM gateway, CRM invoices, e-sign, portability, writing memory, duty of care + calendar (30/10/2026)"
description: "Agent-run Playwright evidence on the Dev hosts for work merged and deployed on 30/10/2026 (AA-994, AA-1002, AA-952, AA-955, AA-967, AA-921, AA-922, AA-961)."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-30
review_every_days: 30
related: [AA-994, AA-1002, AA-952, AA-955, AA-967, AA-921, AA-922, AA-961]
---

# S260 live evidence (30/10/2026, 17:40–18:20 +07)

Headless Chromium (Playwright 1.59 library, one browser at a time), against the live Dev hosts, after their deploys
were green: CIS admin `aa-cis.` (Vercel production deployment of `6d721cfc`; API `/health/ready` schema 312, same SHA),
Booking admin `booking.` (Vercel deploy of `a3bdb3ac`, includes Booking #158), CRM web + API on the agency host
`portal.` (Partner `8525a211`, `/crm/health/ready` schema crm-024).

Identities (codes and secrets read at run time, never written down; no screenshot on the managed-login host):

- **CIS admin:** the Dev-only E2E CIS admin (Cognito email code from the admin mailbox prefix, MFA admin profile).
- **Booking admin:** the AA-910 E2E staff (`booking-admin`, read-only session: writes answer 403 `e2e_read_only`).
- **CRM:** the e2e **owner** and **agent** of the synthetic agency "Lữ hành Sen Vàng" (partner pool, password +
  authenticator). Not Atlas & Hearth: no CRM e2e user is a member of that agency (the S259 P-M1 studio editor is
  "not a CRM member"), so the flow ran on the agency the E2E Dev workflow uses.

Console errors = `console.error` / uncaught page errors on the app origin. Failing requests = responses ≥ 400 on the
app origin. Raw per-step records are in [`data/`](data/) (ids replaced by `<uuid>`; free-text fields replaced by
`<str>`; money, status and error codes kept). Test data written: only on item 4, through the normal CRM UI.

## Results

| # | Item | Result |
|---|---|---|
| 1 | AA-994 kit buttons (CIS #1177, S6b PR2 #1183) | **PASS** |
| 2 | AA-994 Booking S6d (Booking #158) | **PASS** (the notification switch write is refused for the read-only E2E user, as designed) |
| 3 | AA-1002 gateway: Connections tab (S4) + Route editor "Data:" line (S5), on the S6 deploy | **PASS** |
| 4 | AA-952 CRM invoices + payments (Partner #131 + #132) | **PASS** (1 console finding, see F1) |
| 5 | AA-955 CRM e-sign v1 (Partner #136, schema crm-025) | **PASS** (second lane, see below) |
| 6 | AA-967 CRM portability + deletion (Partner #138, schema crm-026) | **PASS** (dry run only; finding F2) |
| 7 | AA-921 / AA-922 Writing memory (CIS #1186 + #1187) and the #1188 label form | **PASS** (data and reads; layout finding F3 on the Metrics tab) |
| 8 | AA-961 CRM duty of care + calendar (Partner #140, schema crm-027) | **PASS** on the API and the calendar / feed; the Travelling-now page shows only its empty state (no live trip within 14 days) and no AA incident exists for the agency (third lane, see below; finding F4) |

### 1. Kit buttons — Settings › UI Kit › Gallery, entry `data-kit-gallery="buttons"`

- Entry at 1440 and 390, light and dark: `01-kit-buttons-{1440,390}-{light,dark}.png`. No sideways scroll
  (page scrollWidth = innerWidth at both widths; the entry's scrollWidth = clientWidth).
- Keyboard Tab through the entry, light and dark: every target gets `:focus-visible` with a **2 px solid accent-deep
  ring** (light `rgb(135, 93, 18)`, dark `rgb(240, 192, 112)`):
  Button "Save", IconButton "Edit notes", SegmentedControl radio "Waiting", ListButton option "Hoan Kiem Lake",
  underline Tabs "Overview" (ring round the label), Switch "Email me when a payment arrives" turned **off** with
  Space (`aria-checked="false"`, ring kept). ArrowRight on the underline tabs moves to "Proposals 2"
  (`aria-selected="true"`). Files: `01-focus-{Button,IconButton,SegmentedControl,ListButton,Tabs-underline,Switch-off}-{light,dark}.png`.
- S6b PR2 pages, 1440 + 390 × light + dark, no layout break, no sideways scroll at 390:
  `01-s6b-platform-stats-*`, `01-s6b-jobs-*`, `01-s6b-tenant-activity-*`.
- Console errors 0, failing requests 0 (`data/cis-run-kit.json`).

### 2. Booking S6d — case TC-000007 (discovery), proposal V1 (draft)

- Case tab strip with counts: Overview, **Proposals 1**, Suppliers, Billing, Checks, Activity —
  `02-case-tabs-{1440,390}-{light,dark}.png`. At 390 the strip scrolls inside itself (438 / 334 px), the page does not
  (390 = 390).
- Keyboard: focus Overview, **ArrowRight** → "Proposals 1" focused and selected, URL `?tab=proposals`
  (`02-case-tabs-after-arrowright-1440-light.png`).
- "Change status" menu opens with "Building" and "Cancel case…" (`02-change-status-open-1440-light.png`);
  **Escape** closes it, `aria-expanded="false"` (`02-change-status-after-escape-1440-light.png`).
- Proposal builder (draft, 3 days, 2 items): day collapse buttons on every day ("Collapse day 1" → `aria-expanded="false"`
  then expanded again, `02-builder-day-collapsed-1440-light.png`); item rows with the move / edit / remove icon buttons;
  dashed "Add item on day 1/2/3" and "Add another day" buttons. `02-builder-{1440,390}-{light,dark}.png`, 390 no sideways
  scroll.
- Settings: theme chips Light / Dark / System; Dark sets `data-theme="dark"`, then back to System
  (`02-settings-{1440,390}-start.png`, `02-settings-{1440,390}-theme-dark.png`). Notifications tab
  (`02-settings-notifications-{1440,390}-light.png`): toggling "New inquiry" sends `PUT /api/booking/staff/me/preferences`
  → **403 `e2e_read_only`**; the UI shows "You do not have access to this." and the switch stays on
  (`02-settings-switch-after-toggle-1440-light.png`). So the toggle and its error path work; a saved change was not
  tested (needs a non-E2E Booking staff session).
- Console: 2 errors, both the expected 403s of the read-only user (`POST /api/booking/pricing/quote-preview` from the
  builder, which then shows "Live quote not available in this session"; and the preferences `PUT`). Nothing else.

### 3. AA-1002 gateway — Settings › LLM Models (CIS, S6 deploy `6d721cfc`)

- Connections sub-tab (S4), 1440 + 390 × light + dark: 5 connections with kind / data scope, credential, limits,
  health (circuit open on the acc3 Bedrock and OpenAI connections, matching the LLM outage noted in S259), enabled.
  `03-connections-*.png`; a connection's details drawer (deployments, settings) opened
  (`03-connection-drawer-1440-light.png`). **Test connection was not clicked.**
- Route editor read-only "Data:" line (S5, `allowed_scopes` from `GET /api/admin/llm-config`, 38 stages):
  - `a0_column_map` (`["aws_only"]`) → **"Data: AWS only"** — `03-route-editor-aws-only-a0_column_map-{light,dark}.png`
  - `t2_judge` (`["aws_only","vendor_direct"]`) → **"Data: AWS, vendor API as last resort"** —
    `03-route-editor-both-t2_judge-{light,dark}.png`
  - Every stage's scopes: `data/03-llm-config-scopes.json`; Stages sub-tab overview `03-stages-subtab-1440-light.png`.
- Console errors 0, failing requests 0 (`data/cis-run-gateway.json`).

### 4. AA-952 CRM invoices + payments — trip "Việt Nam, 3 đêm" (stage Proposal, accepted proposal, deposit 540 USD + balance 1,260 USD due)

| Step | API (through the CRM BFF) | UI evidence |
|---|---|---|
| Settings › Payments: save the manual method ("How clients pay you") | `PUT settings/payment-methods/manual` **200** | `04-settings-payments-before-1440.png`, `04-settings-payments-after-1440.png` ("Payment instructions saved."), `04-settings-payments-390.png`; Invoices settings (prefix INV, tax 0 %, 7 days) on the same page |
| Draft from the due deposit row | `POST trips/{id}/invoices` **201**, `status: draft`, `kind: deposit` | `04a-invoices-card-before-{1440,390}.png`, `04b-invoice-draft-1440.png` |
| Issue | `POST invoices/{id}/issue` **200**, `status: open`, number **INV-000001** (first issued number of this agency) | `04c-invoice-issued-1440.png` |
| Negative: Mark paid on the billed row | `POST schedule/{id}/mark-paid` **409** `{"detail":"invoice_issued_for_row"}` (API call and the Proposal panel's form); UI copy "This payment has an issued invoice. Record the payment on the invoice, or void the invoice first." | `04d-mark-paid-refused-1440.png` (the form; the message text is in `data/04-crm-run-flow.json`) |
| Printable document | `GET invoices/{id}/document` **200** `{invoice_id, filename, html}`; HTML has the CSP `<meta>`, 0 `<script>` | `04e-invoice-document-open.png` (new tab, title INV-000001), `04l-invoice-document-final.png` (after payments and refund) |
| Partial payment 200.00 | `POST invoices/{id}/payments` **201**; "Paid 200.00 USD · refunded 0.00 USD · still owed 340.00 USD" | `04f-after-partial-payment-1440.png` |
| The rest (340.00) | **201**; invoice row `paid`, still owed 0.00; schedule deposit `due → paid`, trip stage `proposal → booked` | `04g-invoice-paid-{1440,390}.png` |
| Refund request 50.00 (owner asks; under the 1,000 base threshold) | `POST payments/{id}/refund-requests` **201** `status: proposed` | `04h-refund-requested-1440.png` |
| Approve (the agency's **agent**, not the requester) | `POST refund-requests/{id}/approve` **200** `status: approved` | `04i-refund-approved-1440.png` |
| Mark refunded (agent) | `POST refund-requests/{id}/execute` **200** `status: executed`; card "refunded 50.00 USD", Refund entry listed | `04j-refund-executed-{1440,390}.png` |
| A-10 `/payments` | `GET invoices?status=paid` **200** → INV-000001 deposit paid 540.00 USD; `GET refund-requests?status=executed` → 1 row 50.00 USD | `04k-payments-{1440,390}.png` (Unpaid: empty state, refund requests "none waiting"), `04k-payments-paid-filter-{1440,390}.png` |

390 px: no sideways scroll on `/payments` and Settings › Payments. Full redacted invoice after the flow:
`data/04-invoice-final-redacted.json`.

Failing requests: the two expected **409**s above, plus two **422**s caused by this run's own probe calls with
`status=all` (not a valid filter value; not sent by the UI). No 5xx.

## Findings

- **F1 — React hydration error #418 on the CRM trip page.** `/pipeline/{tripId}` logs "Minified React error #418"
  (text content mismatch between the server render and the client) on every load, for the owner and the agent. It
  also appears on a trip this run did not touch, and not on `/pipeline`, so it predates the invoices work and is not
  caused by it. The page works (every action above succeeded). Likely a date or time rendered differently on the
  server and in the browser; worth a look with the non-minified build.
- **Observation:** the deposit invoice shows "due 30 Oct 2026" (the schedule row's due date), not issue date + the
  7 "Days to pay" in Settings. That matches "a deposit or balance invoice bills the agreed amount" if the row's date
  wins by design; confirm it is intended.
- **Observation:** screenshots of the admin pages show AWS account ids where the admin UI shows them by design
  (CIS Connections tab and drawer, model route labels in the Stages tab). This README and `data/` contain none.

## Not covered

- Item 2: a saved Booking notification preference (the only Booking E2E session is read-only).
- Item 4 on Atlas & Hearth (no CRM e2e member there); service-fee / typed-line invoices, void, refund rejection and
  the agent-above-threshold path were not exercised.
- Item 3: the connection test call (deliberately not clicked; it makes provider calls).

Test data left on Dev (agency Sen Vàng): invoice INV-000001 (deposit, paid, 50.00 USD refunded), two payments, one
executed refund, trip moved to Booked, the manual payment method with test instructions.

## Second lane (30/10/2026, 20:28–21:05 +07): items 5–7

Same rules and helpers as above (headless Chromium, one browser at a time; codes read at run time and never written
down; VN egress checked before the Vercel hosts). CRM identity: the e2e **owner** of the synthetic agency "Lữ hành
Sen Vàng". Traveller side: a fresh browser context on the client host `go-dev.` with no agency cookies; the portal
codes come from the Dev `PORTAL_OTP_DEV_ECHO` answer (the synthetic travellers have no real mailbox), and the code
hints are masked in every portal screenshot.

Hosts during the lane: the CRM API rolled from `021d68e6` (#136) to `7e9d8db0` (#138, which contains #136) at
20:36 (Deploy Dev run end); the item 5 portal signing (20:38) and all of item 6 ran on `7e9d8db0`, schema crm-026.
CIS API `/health/ready` moved to `0928e759` (#1188), schema 315, at about 20:40.

The client host allows 5 writes per address per minute (`RATE_LIMIT_INTAKE_PER_MINUTE`); the first portal run hit
**429 `rate_limited`** after 5 quick writes, so the run was paced (one write per 16 s) and repeated. That 429 is the
limiter working, not a defect.

### 5. AA-955 CRM e-sign v1 — trip "Việt Nam, 3 đêm" (Booked, deposit paid, start 29 Nov 2026)

Setup through the agency API (owner session): a companion "E2E S260 Minor" added to the trip
(`POST trips/{id}/travelers` **201**) with a date of birth that makes them 10 on the start date
(`PATCH travelers/{id}` **200**, `age_bands_changed: 1`), then a portal link for the lead and for the minor
(`POST trips/{id}/portal-access` **201** ×2, `link_path /c/t/<token>`). Published documents: booking terms + waiver
(`e2e-mvp3tg5i`); no insurance declination is published on this agency, so the insurance question is not asked.
Panel before: `05a-agreements-before-1440.png`.

| Step | API (client host `/crm/public/v1/portal/{token}…` or the CRM BFF) | Result | Evidence |
|---|---|---|---|
| Minor signs in (code step) | `POST …/code` **202** (`dev_code` echoed), `POST …/session` **200** | portal home, "the lead traveller signs for you" | `05b-portal-minor-guardian-signs-{1440,390}.png` |
| NEG: minor signs their own envelope | `POST …/sign` **403 `guardian_signs`** | refused | `data/05-esign-portal.json` |
| Lead signs in | **202** / **200**; home lists 2 envelopes: `self` and `minor 1`, documents booking terms + waiver with their SHA-256 | sign form for "Your signature" | `05c-portal-lead-before-sign-{1440,390}.png` |
| NEG: tampered document hash (waiver SHA-256 with one hex digit changed) | `POST …/sign` **409 `document_changed`**, the 2 current documents sent back | refused before the code is checked | data |
| NEG: wrong signing code (form) | `POST …/code` (purpose `sign`) **202**, then `POST …/sign` **422 `code_invalid`, `attempts_left: 4`** | UI "That code is not right. Tries left: 4." | `05d-portal-wrong-code-1440.png` |
| Lead signs own envelope (right code) | **200** `status: signed`, `signer_role: self`, `envelope_sha256 d58f78f8…5367`, `seal_alg kms-rsassa-pss-sha256` | "Your signature: You signed on 30 Oct 2026"; form moves to the minor | `05e-portal-lead-self-signed-{1440,390}.png` |
| Lead signs as guardian for minor 1 (fresh code) | **200** `signer_role: guardian`, `envelope_sha256 5d7d25c1…3507`, KMS seal | "Child 1 (you sign as their guardian): You signed…" | `05f-portal-lead-all-signed-{1440,390}.png` |
| Re-sign with a used code | **200 `already_signed`** (no second signature) | — | data |
| Agency: `GET trips/{id}/agreements` | **200** `all_signed: true`; lead `self`, companion `guardian`, both `seal_alg kms-rsassa-pss-sha256`, envelope hashes as above; 2 terms acceptances `source: envelope`; signing log `code_sent` ×2, `code_refused (code_invalid)` ×1, `signed` ×2 | "Every traveller has signed.", lead "Signed 30 Oct 2026 · sealed", companion "Signed by the lead as guardian 30 Oct 2026 · sealed" | `05g-agreements-signed-{1440,390}.png` (390: no sideways scroll) |
| NEG: open a sealed envelope with an unknown reason | `POST signatures/{id}/envelope` **422 `reason_required`** | — | `data/05-esign-agency.json` |
| Open each sealed envelope (reason "client request") | **200** ×2: `envelope_text` starts `aa-partner-envelope/1` (2,837 chars), `seal.alg kms-rsassa-pss-sha256`, `seal.key_ref` a KMS key ARN (account redacted in data), 512-char signature, **`seal.verified: true`**; envelope SHA-256 equals the signing answer | modal "Seal checked: valid." with the documents and the audit page (signed for / by whom, guardian) | `05h-sealed-envelope-{1,2}-1440.png` |

Console on the agency trip page: only the known React #418 (F1) and the deliberate 422. Portal: only the deliberate
409 and 422 refusals.

### 6. AA-967 CRM portability + deletion — Settings › Data (`/settings/data`)

Deployed check at 20:41: `/crm/health` `git_sha 7e9d8db0` (#138), `/crm/health/ready` schema **crm-026**, the
`data/exports` and `data/requests` routes answer **200**. Before: `06a-settings-data-before-1440.png` (no requests).

| Step | API (CRM BFF) | Result | Evidence |
|---|---|---|---|
| Log a data request (UI form): portability, e-mail, client = the item 5 lead | `POST data/requests` **201** `status: open`, received 30 Oct, due 29 Nov (+30 days), `max_due_on` 30 Jan 2027 (+92) | listed with Extend / Close actions | `06b-request-logged-1440.png` |
| "Export this client" on that request | `POST data/exports` **201** `scope: traveler`, `status: queued`, linked to the request | progress bar | `06c-export-building-1440.png` |
| Job progress → ready | `GET data/exports`: `queued 0/0` → `ready 24/24` within 5 s; 41 rows, 24 tables, 0 documents, 44,773 bytes, `content_sha256 4245860d…8f37`, expires 6 Nov 2026 | "Ready · One client · 41 records in 24 tables …" | `06d-export-ready-1440.png` |
| Download once (UI button) | `POST data/exports/{id}/link` **200** (`expires_at` +5 min), `GET data/exports/{id}/download?token=…` **200** `application/zip`; export then shows `download_count 1` | "Downloaded …" | `06e-export-downloaded-1440.png` |
| NEG: the same link a second time | **403 `link_invalid`** | refused | `data/06-portability.json` |
| NEG: a made-up token | **403 `link_invalid`** | refused | data |
| Bytes check (second fresh link, fetched in the page) | **200**, 44,773 bytes, starts `PK`, **SHA-256 = the listed checksum**; 51 entries: `json/` + `csv/` per table (traveler, trip, proposal, signature_request, signature_event, terms_acceptance, data_request, …), `documents/manifest.csv`, `manifest.json`, `SHA256SUMS`; that link used twice → **403 `link_invalid`** | — | data (the ZIP itself is not stored in the repo) |
| Erasure DRY RUN, client on a live trip (the item 5 minor) | `POST travelers/{id}/erasure {"dry_run":true}` **409 `traveler_on_trip`** | "The client is on a live trip. Cancel or delete the trip first." | `06f-erasure-refused-on-trip-1440.png` |
| Erasure DRY RUN, synthetic client with no live trip (UI "Check erasure" on a logged erasure request) | **200** `dry_run: true`, counts (traveler 1, trip_traveler 1, trip_party 1, traveler_profile 1, consent 2, form_submission 1, the rest 0), `kept {signature_event 0, terms_acceptance 0}`, `exceptions []`, `exports_withdrawn 0` | "Erasing removes 7 records now; the trash is skipped." + "Erase this client now" / Cancel | `06h-erasure-dry-run-{1440,390}.png` |
| After | the client still answers `GET travelers/{id}` **200**; **"Erase this client now" was not clicked**; no agency deletion was started | 4 open requests listed | `06g-settings-data-after-{1440,390}.png` (390: no sideways scroll) |

Console: only the deliberate 403 / 409 refusals. No 5xx.

### 7. AA-921 / AA-922 Writing memory and the #1188 label form (CIS `0928e759`, schema 315)

Run at 20:50–21:05, after the MFA admin session was refreshed (about 20:47). Identity: the Dev-only E2E CIS admin
(email-code sign-in, read-only session). Deployed check: CIS `/health/ready` `git_sha 0928e759` is the merge commit
of CIS #1188, schema 315 (required 315). The Vercel `dev` deployments are on `0928e759` too, so #1186, #1187 and
#1188 are all live. Signed out, `/admin/writing-memory` answers **307** to sign-in and the API answers **401**.
**No write was attempted** (the session is read-only; Add candidates, Run the weekly job, Keep and Save label were
not clicked).

| Check | API (`/api/admin/writing-memory/…`) | Result | Evidence |
|---|---|---|---|
| Page summary | `GET summary` **200**: signals (by writer / scope / fact status / action / actor), rules, budget (month cap, spent, run cap, max calls), mine trigger, last jobs | tiles: Signals 598 (586 pass · 12 fail), Candidates 0 (1 rejected), spend $1.51 of $25.00, automatic mining off | all `07-wm-*` shots |
| Exemplars tab (WM-29) | `GET exemplars?limit=200` **200** `{items: [], total, limit, offset}`; `GET exemplars/selection?writer=t2` **200** `{writer, scope, tenant_id, per_channel, items: []}`; `GET writers` **200**, 4 writers (`memory_enabled`, `train_closed_month`) | help text (masked voice examples, at most two per writer and channel), "Find candidates (dry run)" / "Add candidates", "Next draft" preview, filters writer / status / owner (5 tenants + Platform), empty state "No examples yet" | `07-wm-exemplars-{1440,390}-{light,dark}.png` |
| Metrics tab (WM-31) | `GET metrics` **200**: 1 weekly report (`week_start`, `trigger`, `kpis {window, missing, writers, learning_spend}`, `soft_stops []`, `actions []`, `rules {expired, reconfirmed, stale_candidates}`, `project_stop`, `disagreements`), 5 `soft_stop_codes`; `GET disagreements?status=open` **200** `{items: [], queue_min, queue_max}` | "Week of 2026-10-19": KPI table per writer (a1 813 writes, t2 4, t9_blog 65 with re-flag 29.2 % (20–41 %), t9_social 23), Soft stops empty ("No active release with content, or none crossed a soft stop"; so no Keep row to show), "Rules: 0 expired, 0 re-confirmed", Disagreement queue empty ("Nothing to review this week") | `07-wm-metrics-{1440,390}-{light,dark}.png` |
| #1188 label form in a T2 version drawer | `/admin/content-quality?tab=versions` (50 rows), first row opened; `GET /api/admin/content-quality/tour-versions/{id}/label` **200** `{subject_type, subject_id, status, labels: [], mine, labellable, choices {label ×4, defect_classes ×4, defect_levels ×3}}` | section `cq-subject-label-t2_version`: As-is / Light edit / Heavy edit / Reject, Fact / Voice / Format / AI phrasing levels, minutes to fix, reason, "Save label" disabled until a verdict is picked, "Other labellers · 0" | `07-t2-version-label-1440-{light,dark}.png`, `07-t2-version-label-form-{light,dark}.png` |

Console errors 0, failing requests 0 (`data/07-writing-memory.json`). The first pass of the tab screenshots did not
land on the Exemplars tab (the click came before hydration and the shot showed Signals). Those shots were retaken
with a content check: the tab's own help text had to be visible in every shot (`tab_rerun` in the data file).

**Layout finding F3 (Metrics tab).** Sideways scroll was measured on the admin shell's own scroller (`main`), not on
the document. At 1440 the Metrics tab content is **1,413 px wide inside a 1,204 px `main`** (`main` scrollWidth
1,449). "Run the weekly job now", the spend tile's right edge and the KPI table's last columns sit off-screen to the
right (`07-wm-metrics-1440-light.png`). The Exemplars tab at 1440 fits (1,204 = 1,204). At 390 both tabs leave
`main` 10 px wider than the screen (400 vs 390). That is small and probably the shared header, not the tabs.
Likely cause: the Metrics tab's top row / grid is missing a `minmax(0, 1fr)` track (the same trap ReleasesTab
already avoids). The data is correct; only the layout is affected.

## Findings (second lane)

- **F2 — erasure refusal copy says "Cancel or delete the trip first", but a cancelled trip still blocks.** A
  synthetic client whose only trip is **cancelled** (not deleted) gets the same **409 `traveler_on_trip`** on the
  dry run; the database rule is "delete or erase the client's live trips first" (`crm.erase_subject`, CRM12). Cancel
  alone is not enough, so the message should say "Delete the trip (move it to the trash) first", or the rule should
  treat cancelled trips as closed. Seen on the first try of this run (`data/06-portability.json`, step "erasure DRY RUN"
  with `trips: ["cancelled"]`).
- **Observation:** the sealed envelope reveal (a "reveal" audit event) does not show in the trip's signing log, which
  lists only `signature_event` kinds (`code_sent`, `code_refused`, `signed`). The audit event is written by the code
  path; if the agency should see reveals in the panel, that is a small follow-up.
- **Observation:** the signing log line shows the raw reason code: "signing code refused (code_invalid)"
  (`05g-agreements-signed-1440.png`); a plain label ("wrong code") would match the rest of the panel.
- **Observation:** the BFF forwards only `Content-Type` on the export download, so the API's `X-Content-SHA256` header
  does not reach the browser. The UI shows the checksum from the export row, and the bytes match it, so this is not a
  defect, only a note for anyone scripting downloads.

## Test data written by the second lane (Dev, agency Sen Vàng)

- Trip "Việt Nam, 3 đêm" (the one item 4 did not use): companion "E2E S260 Minor" (synthetic, `@example.invalid`
  address, DOB set), portal links re-issued for the lead and the minor, two signed sealed envelopes (lead self,
  lead as guardian), two terms acceptances, signing log rows (2 codes sent, 1 refused, 2 signed).
- Settings › Data: one **portability** request (open) with one ready one-client export (downloaded twice through two
  single-use links), three **erasure** requests (open; each checked with a dry run only, nothing erased, no agency deletion).

## Third lane (30/10/2026, 22:00–22:06 +07): item 8

Same rules and helpers as above (headless Chromium, one browser at a time; codes read at run time and never written
down; VN egress checked before the Vercel hosts). CRM identities: the e2e **owner** and **agent** of "Lữ hành Sen
Vàng" on the agency host `portal.` (`partner-dev.` answers 301 to it). Deployed check at 22:00: `/crm/health`
`git_sha 3718242a` (Partner #140), `/crm/health/ready` schema **crm-027**, `keys: kms`. Raw records:
[`data/08-duty-calendar.json`](data/08-duty-calendar.json) (ids `<uuid>`, trip titles `<str>`, the revealed name and
the feed token removed). Traveller names are masked in every screenshot.

### 8. AA-961 CRM duty of care + calendar

**8a. Travelling now (`/travelling`) and the duty API.** Sen Vàng's only live trips are the two booked "Việt Nam,
3 đêm" trips leaving **29 Nov 2026** (30 days out). The page offers Today / Next 7 days / Next 14 days, so in every
window it shows its empty state, "Nobody travelling" (`08a-travelling-{1440,390}-{light,dark}.png`,
`08a-travelling-14d-1440-light.png`; no sideways scroll: document and `main` widths equal the viewport at both widths).
The trips were **not** moved to make the page fill. The grouping was checked on the API:

| Check | API (CRM BFF) | Result |
|---|---|---|
| `GET duty/travelling?days=7` and `?days=14` | **200** `{today 2026-10-30, timezone Asia/Ho_Chi_Minh, from, to, regions: [], travellers: [], incidents: [], truncated: false}` | matches the empty page |
| `GET duty/travelling?days=31`, and `?from=2026-11-29&days=7` | **200**: one region **VN**, `traveller_count 3`, 2 trips (`stage booked`, 29 Nov – 2 Dec, `day_no 1`, `lines 0`, 1 and 2 travellers, `incident_flag_id null`, `is_mine true`) | travellers listed once each with only `traveler_id, trip_ids, regions, has_phone, has_email, has_emergency_contact, has_health_info`; **no name or contact key** anywhere in the answer |
| `GET duty/reach?region=VN` (today) | **200** `{region, on_date 2026-10-30, trips: [], travellers: [], incidents: []}` | — |
| `GET duty/reach?region=VN&on=2026-11-29` | **200**: 2 trips, 3 travellers, same name-free keys | — |
| NEG `GET duty/reach?region=vn` | **422** `string_pattern_mismatch` (`^([A-Z]{2}\|unknown)$`) | — |
| `POST duty/reveal` 1 traveller, `fields [display_name]`, no reason | **200** `reason: duty_of_care` (the default up to 5), `fields [display_name]`, 1 traveller `{traveler_id, display_name}` | value not stored |
| Audit of that reveal | `GET audit/events?action=reveal&object_id=…` **200**: one event `action reveal`, `outcome allowed`, `object_kind traveler`, `fields [display_name]`, `reason duty_of_care`, `member_role owner` | — |
| NEG `POST duty/reveal` 6 travellers, no reason | **422 `reason_required`** "opening more than 5 travellers needs a reason", `threshold 5`, the 5 reason codes | nothing decrypted |
| NEG same with an unknown reason (`"because"`) | **422 `reason_required`** | — |
| Agent: `GET duty/travelling?days=31` | **200**, VN · 3 (every role reads); `/travelling` renders | — |

The reach list and its reveal form (`duty-reach`) are inside each region panel, so with no live trip in the page's
windows they could not be shown or clicked; the reveal was run on the API only.

**8b. AA incident banner.** **No AA incident exists for this agency on Dev:** `incidents: []` in every travelling and
reach answer, and `GET trips/{id}/incidents` **200** `{trip_id, incidents: []}` on both live trips. Neither trip has
an AA booking line (`lines 0`), so no Booking flag can reach them. The trip page shows no banner
(`08b-trip-no-incident-1440-light.png`). No incident was made up. The banner itself was not seen live.

**8c. Calendar (`/calendar`) and `GET calendar`.**

| Window | API | UI (`calendar-event-*`) |
|---|---|---|
| Oct 2026, scope `mine` (page default) | **200** `{from, to, today, timezone, scope, events, truncated}`: 6 `task` | 6 task (`08c-calendar-oct-mine-1440-light.png`) |
| Oct 2026, scope `agency` | **200**: 45 `task`, 3 `call` | same counts (`08c-calendar-oct-agency-{1440,390}-{light,dark}.png`) |
| Nov 2026, scope `agency` | **200**: 4 `task`, 1 `signing_deadline` (8 Nov = 29 Nov − 21 days, "1 signatures pending"), 3 `payment_due` (balance 1,260.00 USD ×2 on 9 Nov, 700.00 USD on 19 Nov), 2 `departure` (29 Nov) | same counts (`08c-calendar-nov-agency-{1440,390}-{light,dark}.png`) |
| Dec 2026, scope `agency` | **200**: 3 `return`, 1 `departure` | — |
| NEG a 14-month range | **422 `invalid_range`** "at most 400 days" | — |
| Agent, Oct, scope `mine` | **200**, 0 events | — |

No `invoice_due` event exists, because the only invoice (INV-000001, item 4) is paid. Every kind but invoices was seen
with real records. No sideways scroll at 390.

**8d. ICS feed.**

| Step | API | Result | Evidence |
|---|---|---|---|
| "Create link" (UI, Include = Whole agency) | `POST calendar/feed` **201** `{feed {scope agency, status active, expires_at +1 year, fetch_count 0}, url}`; the URL appears once: `https://portal./crm/public/v1/calendar/<43-char token>.ics` | "Active since 30 Oct 2026 · Whole agency"; URL masked in the shot | `08d-feed-created-1440-{light,dark}.png` |
| `GET calendar/feed`, `GET calendar/feeds` (owner) | **200** status `active` / 1 active feed | — | data |
| Fetch the public URL (plain `fetch`, no cookies) | **200** `text/calendar; charset=utf-8`, `cache-control private, max-age=300`, 27,005 bytes | `BEGIN:VCALENDAR` … `END:VCALENDAR`, `VERSION 2.0`, PRODID `-//Adventure Asia//Partner CRM calendar//EN`, CRLF only, longest line 75 octets; **62 VEVENT** (each with UID `<id>@crm`, DTSTAMP, DTSTART/DTEND): TASK 49, CALL 3, SIGNING_DEADLINE 1, PAYMENT_DUE 3, DEPARTURE 3, RETURN 3; no unknown property | data |
| No names / amounts in the feed | — | SUMMARY lines are only fixed labels + an 8-char trip reference (e.g. "Balance due · trip `<ref8>`", "Signatures due (1 pending) · trip `<ref8>`"); **no** trip title, no revealed name, no amount (1,260.00 / 700.00 …), no currency code, no e-mail, no phone. Only the calendar name carries the agency's own name ("… CRM") | data |
| NEG agent `GET calendar/feeds` | **403 `role_forbidden`** (owner only) | — | data |
| NEG agent revokes the owner's feed | **403 `not_own_feed`**; the URL still answers **200** afterwards | — | data |
| "Stop this link" → confirm (owner, UI) | `POST calendar/feeds/{id}/revoke` **200** `status revoked`, `revoked_at`, `revoked_by_owner false`, `fetch_count 1` | confirm dialog | `08d-revoke-confirm-1440-light.png` |
| Fetch the same URL again | **404** `{"detail":"feed_not_found"}` | — | data |
| Page after reload | `GET calendar/feed` **200** `status revoked` | banner "Your calendar link was stopped on 30 Oct 2026. Calendars subscribed to it no longer update; your trips and bookings are unchanged. Create a new link to resume." | `08d-feed-revoked-{1440,390}-{light,dark}.png` |
| Audit | `GET audit/events?action=calendar_feed` **200**: `created_agency` allowed, `owner_only` denied, `not_own_feed` denied, `revoked` allowed | — | data |

Console / failing requests: only the deliberate 422s (reach, reveal ×2, calendar range) and the agent's two 403s, plus
the known React #418 on the trip page (F1). No 5xx. Owner second session: 0 console errors, 0 failing requests.

### Findings (third lane)

- **F4 — calendar times render in UTC, not the agency's timezone.** `web/app/(crm)/calendar/page.tsx` formats
  `starts_at` with `new Intl.DateTimeFormat(locale, { hour, minute })` and no `timeZone`, in a server component, so the
  time uses the server's UTC. Days are grouped by the agency's local date (the API's `date`). So a task due 13:02 +07 shows
  as "06:02 am", and the first events of a day show as "11:16 pm" at the top of the list (25 Oct and 30 Oct in
  `08c-calendar-oct-agency-1440-light.png`), which looks like a sorting bug. The API already returns `timezone`
  (`Asia/Ho_Chi_Minh`). Fix: pass `timeZone: view.timezone` to the formatter. The ICS feed is right (UTC `…Z` times).
- **Observation:** the Travelling-now page offers only 1 / 7 / 14 days. A booked trip 30 days out (signing deadline
  already on the calendar) shows nowhere on that page. This matches the design windows; noted only because the page
  could not be filled with real data on Dev.
- **Observation:** "1 signatures pending" (calendar UI) should be singular for 1.

### Test data written by the third lane (Dev, agency Sen Vàng)

- One **revoked** ICS feed of the owner (scope agency, read once), with its audit events.
- One logged `reveal` of one traveller's display name (reason `duty_of_care`).
- Nothing else changed: no trip dates, stages or travellers were edited.
