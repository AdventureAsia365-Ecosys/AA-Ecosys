---
id: OPS-08-s264-live-verify
title: "S264 live verify: AI notice, CIS admin kit follow-ups, CRM Module 10"
description: "Agent-run Playwright evidence on the Dev hosts for AA-1033 (AI-output notice), AA-1006 (CIS admin on the kit, CIS #1229) and AA-959 (CRM Module 10 tasks and automations)."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-02
review_every_days: 30
related: [AA-1033, AA-1006, AA-959]
---

# S264 live verify (02/11/2026)

Headless Chromium (Playwright from the AA-CIS-App checkout, one browser at a time). Hosts and deployed SHAs at the run:

- CIS admin `aa-cis.` (Vercel production deploy of `4f1244a9`, includes CIS #1229 and #1235; API `/health/ready` `4f1244a9`, schema 338).
- CRM web on the agency host `portal.` (`/healthz` `e5d5d517`, includes Partner #185; CRM API schema crm-039).
- Content studio on `portal.` (Deploy Portal Dev green on `0ace0b2e`).
- TripPlanner `tripplanner.` (main `8e59223a` = TP #210, CI green).

Identities (by role; codes and secrets read at run time, never written down; no screenshot on the managed-login host):

- **CIS admin:** the Dev-only E2E CIS admin (read-only session).
- **TripPlanner, studio terms:** anonymous visitor.
- **CRM:** the e2e **owner** of the synthetic agency "Lữ hành Sen Vàng" (partner pool, password + authenticator).
- **Content studio:** the e2e studio user (partner pool, studio membership on the E2E tenant).

First lane ~00:30–01:00Z; the MFA admin session expired mid-run. Second lane after the MFA refresh (01:05Z) covered
the signed-in CRM, the studio, the CIS kit gallery and the Alerts close-up.

Console errors = `console.error` / uncaught page errors. Failing requests = responses >= 400. Raw records in
[`data/`](data/). Viewports 1440x900 and 390x844; theme by `prefers-color-scheme`. Overflow = `scrollWidth <= clientWidth`
measured on the document and on the admin shell's `main`.

## Results

| # | Item (issue + PR) | Result |
|---|---|---|
| 1 | AA-1033 AI-output notice (CIS #1235, Partner #185 / #159, TP #210 / #209, Booking #164) | **PASS** on every live placement except the CRM terms page: **FAIL** F1 (CRM `/terms` shadowed) |
| 2 | AA-1006 CIS admin on the kit, S263 follow-ups (CIS #1229) | **PASS** for F1–F4; new finding F2 (Upload at 390) |
| 3 | AA-959 CRM Module 10 Tasks + Automations (Partner #182 / #183) | **PASS** (Tasks create → list → done; Automations page + library; engine: install, apply to a dated and an undated trip, idempotent re-apply, run stopped by the trip cancel) |
| 4 | TripPlanner E3 (TP #211, gateway dispatch by deployment + per-connection breaker) | **Not verifiable by the agent**: BotID answers 403 to Playwright (headless and headed) on `/api/browse/search` and `/api/trip/narrate` |

### 1. AA-1033 AI notice

| Surface | Path | Shots | Result |
|---|---|---|---|
| CIS Review Queue editor drawer | `/admin/review` → row | `01-cis-review-editor-{1440,390}-{light,dark}.png` | **PASS**: staff sentence, English (`lang=en`), visible at both widths |
| CIS tour detail, Latest Rewrite tab | `/admin/master-content` → View → Latest Rewrite | `01-cis-tour-rewrite-tab-{1440,390}-{light,dark}.png` | **PASS**: staff sentence, English |
| CIS kit gallery (three variants) | `/admin/settings?tab=ui-kit` → Gallery | `01-cis-kit-gallery-ai-notice-{1440,390}-{light,dark}.png` | **PASS**: staff, publisher, traveller sentences |
| CIS Content quality rewrite panel | — | — | not tested: it shows only when a model suggestion is loaded (an LLM call) |
| TripPlanner footer + "Use of AI" link | `/` | `01-tp-footer-{1440,390}-{light,dark}.png` | **PASS**: traveller sentence, link `/terms#ai` |
| TripPlanner tour page | `/tours/<slug>` | `01-tp-tour-{1440,390}-{light,dark}.png` | **PASS**: under the itinerary |
| TripPlanner planner map popup | `/plan` → country → map point | `01-tp-plan-popup-{1440,390}-{light,dark}.png` | **PASS**: traveller sentence + "Use of AI" (`/terms#ai`, new tab) |
| TripPlanner planner stop activities / narration | `/plan` | — | not tested: needs a trip draft ("Start with this route" writes a trip) |
| TripPlanner terms §3 "Use of AI" | `/terms#ai` | `01-tp-terms-ai-{1440,390}-{light,dark}.png` | **PASS**: AI can be wrong, for information, quote + booking conditions bind, no waiver |
| Content studio public terms §3 | `portal./terms#ai` | `01-studio-terms-ai-{1440,390}-{light,dark}.png` | **PASS**: quotes the publisher sentence. The page has no dark theme (stays light) |
| Content studio My Content | `portal./portal/content` | `01-studio-content-{1440,390}-{light,dark}.png` | **PASS**: publisher sentence under the title |
| Content studio catalog (My Tours) | `portal./portal/tours/mine` | `01-studio-catalog-{1440,390}-{light,dark}.png` | **PASS**: publisher sentence |
| Content studio Review drawer, Writer, Tour rewrite, Publish pending | — | — | not tested: need an editable piece or a write; the studio user is a viewer |
| CRM web Settings > AI | `portal./settings/ai` | `01-crm-settings-ai-{1440,390}-{light,dark}.png` | **PASS**: "AI can make mistakes: check facts before sending." is the first rule; "Every AI draft carries this note" + the staff sentence; link "AI-generated content in the terms of use" → `/terms#ai` |
| CRM web AI draft area | — | — | not present in the UI: no CRM component calls `trips/{id}/ai/draft` yet (only `lib/bff.ts`), so the guard test passes with no surface; the agency's AI assistant is off (Dev stub) |
| CRM web `/terms` "AI-generated content" | `portal./terms#ai` (signed in) | `01-crm-terms-link-target-1440-light.png` | **FAIL** (F1): signed in as the CRM owner, the footer link `/terms` and Settings > AI `/terms#ai` land on the studio "Partner terms" (§3 "AI-generated content and acceptable use"); `data-testid="crm-terms"` absent |
| CRM public trip page `/trip/<id>` | `go-dev./trip/<id>` | — | not tested: no published tour id found that answers 200 |

Console errors 0 and failing requests 0 on every page above (`data/cis-results.json`, `data/pub-results.json`,
`data/plan-results.json`). The Review Queue raises the legacy reviewer-id `window.prompt` on first load (dismissed; no write).

### 2. AA-1006 CIS #1229

- F1 Overview at 390: **PASS**: document 390/390 and `main` 390/390 in light and dark (was `main` 455 > 390 in S263),
  `02-overview-{1440,390}-{light,dark}.png`. Alerts card close-up: long keys wrap, date on its own line, no element past
  the right edge (`02-overview-alerts-{1440,390}-{light,dark}.png`).
- F2 "Columns" button inset: **PASS**: Master Content gap 36 px to the pane edge at 1440, Upload 57 px
  (`02-master-content-1440-light.png`, `02-upload-1440-light.png`).
- F3 Content Trace (`/admin/tenant-activity`): **PASS**: 7 columns (Topic, Tenant / tour, Channel, Angle chosen, Status,
  Gates, Created), table 910 px in a 910 px pane, server pager "1–50 of 349", "Total pieces 349"
  (`02-tenant-activity-{1440,390}-{light,dark}.png`).
- F4 Master Content range: **PASS**: page 2 shows rows 38–40 with "21–40 of 892", range and numbers agree
  (`02-master-content-page2-{refreshing,settled}-1440-light.png`).
- No overflow at 390 on Overview, Master Content, Content Trace; console errors 0, failing requests 0.

### 3. AA-959 CRM Tasks + Automations

- Tasks (`/tasks`): **PASS**: board with 79 open tasks (all CRM `system` tasks, 50 overdue), scopes My / Team / Done,
  Morning digest switch; no overflow at 390 (`main` 390/390) in light and dark (`03-crm-tasks-{1440,390}-{light,dark}.png`).
- Create → list → done: **PASS**: New task "S264 verify task" (no date, Me, Normal) saved, listed as "Own task · Not
  linked to a trip · No date" (`03-crm-task-new-1440-light.png`, `03-crm-task-created-1440-light.png`); Done → gone from
  My tasks after reload, present in Done (7 days) (`03-crm-task-done-1440-light.png`). The UI has no delete; the task
  stays as done.
- Automations (`/automations`): **PASS** for the page: "Your automations" empty state ("No automation yet"), "New
  automation", AA library with 10 templates (T-48 h arrival flight, T-21 booking details, pre-departure checklist, …)
  (`03-crm-automations-{1440,390}-{light,dark}.png`).
- Engine rules / runs: **not observable**. The agency has 0 rules installed and none of 6 trips has a workflow run; the
  trip page shows the apply control only (`03-crm-trip-automations-1440-light.png`). Installing a library rule is a
  write outside this lane's scope.
- Console errors 0, failing requests 0 (`data/crm-results.json`).

### 3b. AA-959 engine on the synthetic agency (third lane, 00:58–01:06Z)

Writes allowed on Lữ hành Sen Vàng only. Times UTC (`data/wf-results.json`, `data/wf2-results.json`, trip ids -> `<uuid>`).

| Time (Z) | Step | Result |
|---|---|---|
| 00:58:53 / 00:58:54 | Two inquiries through the public form (contact consent only, no marketing consent): trip A "S264 WFA mvyjwak6 Dated", trip B "S264 WFB mvyjwak6 Nodates" | 202 ×2; both cards on the board by 00:59:26 |
| 00:59:18 | Installed library template "Visa and documents task list" (`visa_documents_task_list`, trigger: applied by hand, 3 custom tasks due departure −60 / −45 / −30 days) | rule ON, "0 running · 0 finished" (`03-wf-1-installed-1440-light.png`) |
| 00:59:34 | Trip A dates 2027-03-01 → 2027-03-10 | saved |
| 00:59:46 | Apply to A (Check: "Ready to apply to this trip.") | run FINISHED, 3 × "task created"; tasks due 31 Dec 2026, 15 Jan 2027, 30 Jan 2027 09:00 (`03-wf-2a-trip-dated-run-1440-light.png`, `03-wf-2c-tasks-due-dates-1440-light.png`) |
| 01:00:37 | Apply to B (no dates) | run FINISHED, 3 × "task created", no due date; Tasks › Team shows them under "Waiting for dates (3)" (`03-wf-2b-trip-nodates-run-1440-light.png`, `03-wf-2d-tasks-waiting-for-dates-1440-light.png`) |
| 01:01:35 | Apply to A again | second run FINISHED with 3 × "task already open"; open tasks on A 4 → 4 (`03-wf-3-idempotent-1440-light.png`) |
| 01:02:26 | Apply to A a third time (trip still at Inquiry: no Cancel offered, cancel needs Booked / Pre-departure / Travelling) | run FINISHED, 3 × "task already open" |
| 01:04:01–01:04:41 | A moved Inquiry → Qualifying → Proposal (override "other") → Booked (override "manual_booking"); the two 409 `gate_unmet` answers open the override dialog, by design | stage Booked |
| 01:05:10 / 01:05:11 | Apply to A a fourth time, then the one-action Cancel (reason client_request, typed CANCEL) inside the run's 20 s start delay | trip Cancelled; the new run **STOPPED, "the trip was cancelled"** with no step done; A's open tasks (reply, planning info, the 3 visa tasks) became skipped (`03-wf-4-cancelled-run-stopped-1440-light.png`, `03-wf-4-cancelled-trip-top-1440-light.png`) |
| 01:05:25 | Library check | "Birthday greeting" present: "your greeting e-mail (only to clients who agreed to marketing) and a task"; **not installed**, so the "not sent: no marketing consent" run log is not shown (`03-wf-5-automations-after-1440-light.png`) |

Not covered: date-anchor rules (T-48 h, T-21) fired by the hourly `crm_workflow_tick` (only one template installed, by
the brief); the birthday consent gate. Console errors 0 apart from the two expected 409 gate answers; failing requests
otherwise 0.

### 4. TripPlanner E3 (TP #211)

Anonymous visitor on `tripplanner.` (`/plan`), Playwright Chromium, headless (01:06–01:07Z) then headed under WSLg
(01:07–01:09Z); same result both times (`data/tpe3-headless-results.json`, `data/tpe3-headed-results.json`):

- Search "temple": `GET /api/browse/search` **403** (01:06:20.9Z, 01:07:56.2Z). The page shows no results.
  `04-tp-e3-search-1440-light.png`.
- Two stops pinned from the Vietnam map ("Ho Chi Minh Trail" ×2): `POST /api/trip` 200 ×2 (01:06:56, 01:07:22 and
  01:08:29, 01:08:56). Guest trips created (synthetic, left in place): two anonymous trips, ids in the lane report.
- Compose narration: `POST /api/trip/narrate` **403** (01:07:27.1Z, 01:09:00.8Z); the panel says "We could not confirm
  this request came from the planner page. Please reload the page and try again; your trip is saved."
  (`04-tp-e3-narration-1440-light.png`).
- No 5xx. The 403s are the BotID guard refusing an automated browser, so the gateway path behind them was not reached.
  I did not try to get around BotID. A person in a normal browser has to run this check, or E2E needs a sanctioned
  BotID bypass.

## Findings

- **F1 — CRM `/terms` is unreachable on the agency host.** The ALB rule `crm_agency_studio_x`
  (AA-CIS-Infra `accounts/aa365/crm_agency_edge.tf`, path patterns `/terms`, `/privacy`, `/assets/*`) sends `/terms` to the
  Content studio, so the CRM page `web/app/(crm)/terms/page.tsx` (AA-Partner #185) is never served: `portal./terms`
  shows "Partner terms" (studio) and has no `data-testid="crm-terms"`. The CRM footer and Settings > AI link `/terms#ai`
  land on the studio terms §3, which describes studio content, not CRM drafts. Proposed fix: move the CRM page to a
  path the CRM web owns (for example `/crm-terms` or `/settings/terms`) or give the studio rule a host-aware split.
  Not fixed in this lane.
- **F2 — Upload (S0) is wider than a 390 px phone.** `/admin/upload` at 390: `main` scrollWidth 675 > clientWidth 390;
  the five-step stepper ("Select Files … Dup Review") runs off the right edge (`02-upload-390-light.png`).
  Proposed fix: let the stepper wrap or scroll inside its own strip. Not fixed in this lane.

## Not covered

- CIS Content-quality rewrite panel (needs an LLM suggestion); TripPlanner stop activities / narration (needs a trip
  draft); CRM public `/trip/<id>` (no published tour id answering 200 found).
- Studio Review drawer / Writer / Tour rewrite / Publish pending (need an editable piece or a write).
- AA-959 date-anchor and special-date rules (tick-driven), birthday consent gate.
- TripPlanner E3 search and narration through the gateway (BotID blocks the agent's browser).
- Booking: the kit sync (#164) adds no Booking placement; Booking UI not opened.

## Test data written

- Lữ hành Sen Vàng (synthetic CRM agency), all through the normal UI:
  - own task "S264 verify task" (created, marked done);
  - workflow rule "Visa and documents task list" (library, ON);
  - trips/inquiries "S264 WFA mvyjwak6 Dated" (dates 2027-03-01 → 2027-03-10, moved to Booked with overrides, then
    cancelled) and "S264 WFB mvyjwak6 Nodates" (Inquiry, no dates), each with its synthetic client
    (`s264.wf{a,b}.mvyjwak6@example.invalid`);
  - 5 workflow runs (A: 4, B: 1) and 6 automation tasks (3 on A, now skipped; 3 on B, open, waiting for dates).
- TripPlanner: two anonymous guest trips with 2 stops each (planner, no sign-in).
