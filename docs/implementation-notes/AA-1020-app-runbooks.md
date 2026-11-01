# AA-1020 lane app-runbooks: per-app access and operations runbooks

Lane of S263 (tech lead ask: "a runbook per app that says how to get in and how to run it", for the business owner and
staff). Root repo only, docs only.

## Decisions

- One index page `docs/guides/app-access-and-operations.md` (`GUIDE-12`) plus six pages under `docs/guides/`, each with
  a faithful `.vi.md` sibling: CIS admin, AI providers and reports (asked as a sixth item, kept separate because the
  business owner reads it often), Content studio, CRM, Booking admin, TripPlanner. IDs `GUIDE-12-<app>` follow the
  catalog rule "a page under an entry adds a suffix". `GUIDE-12` was the next free guide number (GUIDE-08 is planned).
- File names `<app>-runbook.md` (content, not issue key). Front-matter `type: how-to`, `status: draft`, no
  `last_tested`: these are user runbooks, not ops runbooks with expected result / verify / rollback per step, so the
  freshness report does not count them as untested ops runbooks. The index says plainly that they were written from
  the code and checked by HTTP status, and that a staff walk-through is pending.
- UI labels are quoted exactly as the code prints them (nav files, `messages.ts`, `i18n.ts`) and stay English in the
  `.vi.md` pages too, because every app opens in English and the labels are product names on screen.
- Audience gets `staff` (schema value already existed); the catalog legend gains `S = staff`.
- No screenshots (asked: none now, no placeholders).
- Links from the Vietnamese pages point to the `.vi.md` siblings without heading fragments (Vietnamese heading slugs
  differ; lychee does not check fragments anyway).

## Changed

- `docs/README.md`: catalog row GUIDE-12, a "Staff" start-here row, the business-owner row links the index, the
  translations list names the GUIDE-12 pages, audience legend `S`.
- `docs/guides/ceo.md` + `ceo.vi.md`: one sentence after the sign-in table linking the index (no duplication of the
  runbooks' content).

## Tradeoffs

- The Content studio invitation has **no button** in the CIS admin today (the staff route
  `POST /admin/tenants/{id}/members/invitations` exists; the Tenant 360 UI has no Members tab). The runbook says so and
  routes the request to the engineer on duty instead of describing a button that does not exist.
- The AI gateway as-built page (`docs/architecture/ai-gateway.md`) is on a sibling AA-1020 branch, not yet on master,
  so these pages link ADR 0009, the playbooks and the acc3 postmortem instead (offline link check would fail on a
  missing file). Add a link to it once that PR merges.
- CRM staff groups (`crm-ops`, `crm-support`, `crm-platform-admin`) are described by what they allow, in words the
  staff console itself uses ("ground operations", "agency support"); group codes stay out of the user pages.

## Should know

- Facts checked live on 2026-11-01 (read-only `curl` status): `aa-cis.` 307, `booking.` 307, `portal.` 307,
  `partner-dev.` 301, `tripplanner.` 200, `go-dev.` 404 on `/` (expected: only `/c/*`), `api-cis /health` 200,
  `api-booking /booking/health` 200, `portal /crm/health` 200, `portal /health` 200.
- Dev caveats quoted from sources on master: acc3 refusing since 2026-10-29 (postmortem), CRM LLM stub and Twilio
  sandbox provider, Stripe not built (`provider_not_available`), TripPlanner preview `noindex`, draft legal pages.
- Review cadence 90 days; any sign-in, role or menu change in an app should update the matching page and its `.vi.md`
  in the same session.
