# AA-1157 live verification on Dev: view as a lower role (CIS + Booking)

- Checked: 2026-11-23 06:20–06:30 UTC, by an agent with the Dev-only E2E identities (no owner identity exists, by design).
- PRs: CIS AA-CIS-App #1640 (merge `7a6a8ef`), Booking AA-Booking #301 (merge `703a3f7`). CI on both PRs is green
  (unit, integration, lint, OpenAPI, security, settings lint, spec trace).
- CIS migration 470 (`shared.staff_view_as_session`: `tenant_id` nullable, new `view_role`) is registered on Dev
  (`/health/ready` `registered_keys` holds 470 and 471). The live schema dump on root master (verified 2026-11-23
  06:02 UTC, PR #951) shows `tenant_id uuid` (nullable) and `view_role text`.

## 1. The deployed code contains the merges

| Service | Task definition | Image tag | Rollout | Contains the merge |
|---|---|---|---|---|
| aa-cis-dev-api | :1252 | `dev-e8171a8c` | COMPLETED (one deployment) | yes, `e8171a8` is 2 commits ahead of `7a6a8ef`, 0 behind |
| aa-cis-dev-worker | :821 | `dev-e8171a8c` (same as api) | COMPLETED | yes |
| aa-cis-dev-admin | :86 | `dev-e8171a8c` | COMPLETED | yes |
| aa-booking-dev-api | :160 | `19f2fcf1` | COMPLETED | yes, `19f2fcf` is 2 commits ahead of `703a3f7`, 0 behind |
| aa-booking-dev-admin | :56 | `19f2fcf1` | COMPLETED | yes |

The CIS api, worker and admin were mid-rollout (the next CIS merge, #1642) when the check started. They reached
COMPLETED at about 06:24 UTC, and every live check below ran after that.

Health (all HTTP 200):
- `GET https://api-cis.lumiguides.it.com/health`: `git_sha` `e8171a8c…`.
- `GET https://api-cis.lumiguides.it.com/health/ready`: `status ok`, `db ok`, `schema_version 471`.
- `GET https://api-booking.lumiguides.it.com/booking/health`: `git_sha` `19f2fcf1…`.
- `GET https://api-booking.lumiguides.it.com/booking/health/ready`: `status ok`, `db ok`, `schema_version bk-064`.

## 2. Live checks with the E2E identities

How they ran: temporary Playwright specs (not committed) built on the repos' own sign-in helpers. CIS used the
`admin-evidence` project with the E2E CIS admin: group `cis-admin`, read-only session, not an owner. Booking used the
`signed-in` project with the E2E Booking staff user: group `booking-admin`, read-only, not an owner. Every request
was sent from inside the signed-in page (`fetch`, same origin) through the staff BFF. Raw results: `results.json`.
Nothing was written. Every start was refused before any row was created, and the CIS session was signed out at the end.

| # | Check | Request | Result |
|---|---|---|---|
| a | A start without the BFF header is refused | CIS `POST /api/admin/view-as/roles` (generic proxy, so the BFF header is not set) | **403** `{"detail":"view_as_bff_only"}` |
| b | An E2E admin start gets the generic refusal | CIS `POST /api/view-as/roles` `{role:"content"}` (the real BFF start route) | **403** `{"detail":"e2e_read_only"}` |
| c | The roles catalogue says "no view-as" for the E2E identity | CIS `GET /api/admin/platform/roles` | **200**, `can_view_as: false` |
| c2 | No "View as" control on the page | CIS `/admin/platform/roles`: count of `[data-testid^="role-view-as-"]` | **0**; no banner (screenshot `cis-roles-e2e-admin-no-view-as.png`) |
| c3 | No view is running | CIS `GET /api/view-as/roles` | 200 `{"active":false}`; `GET /api/admin/session` reports `read_only: true, reason: "e2e"` |
| d | Booking refuses a start by a non-owner | Booking `POST /api/view-as` `{role:"viewer"}` (BFF → `POST /booking/view-as`) | **403** `{"detail":"e2e_read_only"}`; no `bk_view_as` cookie was set |
| d2 | Booking role list says "no view-as" | Booking `GET /api/booking/staff-roles` | 200, `can_view_as: false`, `can_edit: false` |
| d3 | No "View as a role" panel and no banner | Booking `/roles`: `[data-testid="view-as-start"]` count | **0** (screenshot `booking-roles-e2e-no-view-as.png`) |
| d4 | Profile outside a view | Booking `GET /api/booking/staff/me` | 200, `role: admin`, `view_as: null`, `read_only: false` |
| e | Health | see section 1 | 200 on all four endpoints |

Extra checks without a sign-in: `POST https://api-cis.lumiguides.it.com/admin/view-as/roles` answers 403
`Invalid admin secret`. `POST https://api-booking.lumiguides.it.com/booking/view-as` answers 401 `missing_bearer_token`.
The OpenAPI documents are not public (403), so the routes cannot be proven from them.

What these checks do and do not prove:
- (b) and (d) are **generic** refusals. The E2E identities are read-only, so both APIs refuse their non-GET calls
  with `e2e_read_only` before the owner check runs. The owner rule itself is proven by CI unit tests:
  - CIS `tests/unit/test_aa1157_staff_view_as.py`: `test_a_non_owner_admin_cannot_start`,
    `test_a_business_owner_without_the_owner_flag_cannot_start`.
  - Booking `backend/tests/unit/test_aa1157_view_as.py`: `test_a_non_owner_cannot_start`,
    `test_a_business_owner_alone_cannot_start`.
- (c) and (d2) are the owner rule's **read** side, live: `can_view_as` is false for a non-owner in both apps.
- The "downward" refusal (a target whose read rights go beyond the viewer's) cannot happen live in CIS. Only an owner
  who is also an admin may start a view, and an admin's reads cover every CIS role. It is proven by unit tests:
  - CIS: `test_a_wider_target_is_not_downward`.
  - Booking: `test_a_wider_target_is_refused`.

Roles that exist on Dev for the Done-when (from the live catalogue):
- CIS custom role `custom_content` ("Content", based on content_lead, active, **18** capabilities).
- Booking custom role `custom_product_ops_accounting` ("Product, ops & accounting", based on contracting, active,
  **24** capabilities, 1 holder).
- The Done-when names "Content + Product & operations". This report uses the pair above, from CIS migration 462.
  Preset `content_ops` (migration 465) maps to CIS `content_lead` with no Booking role, so it is not that pair.

## 3. Done-when mapping

| Done-when line | Status | Evidence / why |
|---|---|---|
| The tech lead views as "Content + Product & operations" and sees that role's nav in CIS and in Booking (screenshots with the banner) | not checked | Needs an owner session. No E2E identity is an owner, and the CHECK forbids one. Tech-lead hand step H1 + H3 below |
| Every POST/PATCH/DELETE during the view gets 403. A test covers each app | partly: tests pass in CI; live part not checked | CI: CIS `test_every_staff_write_is_refused_in_a_view_before_the_route`, `test_denial_reason_refuses_every_write_in_a_view`; Booking `test_every_staff_write_is_refused_in_a_view_before_the_database`. Live: hand step H2 + H4 |
| A view-as to a role whose read rights go beyond the viewer's is refused. A non-owner cannot start view-as | pass with limits | Non-owner: live generic refusals (b), (d), plus `can_view_as` false (c), (d2). Owner-rule detail and the "downward" refusal: unit tests only (named above) |
| The audit shows start and end rows, and the start row holds the target role's capability list | not checked | Needs a real owner view. After H1–H4, the orchestrator runs the two aggregate scripts (section 5). Expected capability counts: 18 (CIS) and 24 (Booking) |
| The sign-in session id is the same before and after | not checked | Hand step H5 (compare `origin_jti` of the Cognito access-token cookie before and after) |
| Deploys reach rollout COMPLETED | pass | Section 1: all five services COMPLETED on images that contain the merges |

CloudWatch baseline (06:28 UTC, last 6 h, log groups `/ecs/aa-cis-dev-admin`, `/ecs/aa-booking-dev-admin`,
`/ecs/aa-cis-dev`): 0 lines matching `view_as_write_refused`. That is expected before any owner view.

## 4. Tech-lead hand steps (owner session)

Use a desktop browser signed in as yourself (owner) on both hosts. Do not paste a token into any website. Decode it
only in your own terminal (H5). Take every screenshot at full window width and save it in this folder with the names
given.

**H0. Note the sign-in session id before the view (CIS and Booking).**
1. Open `https://aa-cis.lumiguides.it.com/admin`. DevTools → Application → Cookies → `https://aa-cis.lumiguides.it.com`.
   Copy the value of `cis_admin_token`.
2. In a WSL terminal, run this one line. It reads the token without echoing it or saving it in history:
   `read -rs T; python3 -c "import sys,json,base64;p=sys.argv[1].split('.')[1];print(json.loads(base64.urlsafe_b64decode(p+'='*(-len(p)%4))).get('origin_jti'))" "$T"; unset T`
   Paste the value and press Enter. Note the printed `origin_jti` as **CIS-before**.
3. Do the same on `https://booking.lumiguides.it.com` with the cookie `bk_access`. Note the result as **BK-before**.

**H1. CIS: view as "Content".**
1. Open `https://aa-cis.lumiguides.it.com/admin/platform/roles`.
2. On the custom role row **Content (`custom_content`)**, click **View as**.
3. Keep the reason "Check what this role sees", choose Length **30 min**, and click **Start view**.
4. The page reloads on the role's landing page. Check for the amber banner at the top: "Viewing as Content",
   "Read only…", the minutes left, and a **Back** button.
5. Screenshot the whole window with the banner and the left nav: `h1-cis-view-as-content.png`.
   - Expected nav: content, catalogue and writing-lab areas.
   - Expected to be absent: Staff & access, Audit log, AI & spend (the role has no `staff.read`, `audit.read`,
     `spend.read`).

**H2. CIS: a write is refused while the view runs.**
1. Still in the view, open the DevTools Console and run:
   `await (await fetch('/api/admin/s288-view-as-probe', {method: 'POST'})).json()`
2. Expected answer: `{detail: "view_as_read_only"}`. The Network tab shows status **403**. The path does not exist,
   so nothing could be written even if the guard failed.
3. Screenshot the console and the network row: `h2-cis-write-refused.png`.

**H3. Booking: view as "Product, ops & accounting".**
1. Open `https://booking.lumiguides.it.com/roles`.
2. In the panel **View as a role**, choose Role **Product, ops & accounting** (`custom_product_ops_accounting`) and
   Length **30 min**. The reason is optional. Click **Start view**.
3. Check for the banner (role name, "Read only: every change is refused…", minutes left, **Back**).
4. Screenshot the window with the banner and the left nav: `h3-booking-view-as-product-ops-accounting.png`.
   - Expected nav: supply, pricing, billing and operations.
   - Expected to be absent: Admin › Staff, Roles, Audit Log.

**H4. Booking: a write is refused while the view runs.**
1. In the DevTools Console, run:
   `await (await fetch('/api/booking/s288-view-as-probe', {method: 'POST'})).json()`
2. Expected answer: `{detail: "view_as_read_only", …}`, status **403**.
3. Screenshot: `h4-booking-write-refused.png`.

**H5. End both views and compare the session id.**
1. In Booking, click **Back** on the banner. You land on Roles and the banner is gone.
2. In CIS, click **Back** on the banner. You land on Platform › Roles & permissions and the banner is gone.
3. Repeat H0 steps 1–3. Note **CIS-after** and **BK-after**.
4. Expected: CIS-after = CIS-before and BK-after = BK-before. The access token itself may have been refreshed
   (`jti` changes every 15 minutes); `origin_jti` stays the same for one sign-in.
5. Write the four values' first 8 characters (not the token) into the session checklist, or tell the orchestrator.

**H6. Refused-write log lines (CloudWatch Logs Insights).** The orchestrator can run this too (read-only).
- Console: CloudWatch → Logs Insights, region us-west-1, last 1 hour.
- Log group `/ecs/aa-cis-dev-admin`, query:
  `filter @message like "staff_view_as_write_refused" | sort @timestamp desc | limit 5`
  - Expected: one line, `app=cis`, `view_role=custom_content`, method POST, path `/api/admin/s288-view-as-probe`.
- Log group `/ecs/aa-booking-dev-admin`, query:
  `filter @message like "booking_view_as_write_refused" | sort @timestamp desc | limit 5`
  - Expected: one line, `app=booking`, POST `/booking/s288-view-as-probe`.
- Screenshot both result tables (`h6-cis-refused-log.png`, `h6-booking-refused-log.png`). Crop or blur any staff id
  before the image goes into the repo.

Same check from the CLI (one line each; get the id from `start-query`):
`aws logs start-query --log-group-names /ecs/aa-cis-dev-admin /ecs/aa-booking-dev-admin --start-time $(date -d '-1 hour' +%s) --end-time $(date +%s) --query-string 'filter @message like /view_as_write_refused/ | fields @timestamp, @log | sort @timestamp desc | limit 10' --profile aa365-admin --region us-west-1`
then `aws logs get-query-results --query-id <id> --profile aa365-admin --region us-west-1`.

## 5. Audit rows (orchestrator, after H1–H5)

Two read-only aggregate scripts. They print no person ids and no reason text, and session ids are cut to 8 characters.
- `.tmp-session/S288/live/aa1157_cis_audit.py` (role `cis_app`):
  `tools/ecs/ecsx.sh .tmp-session/S288/live/aa1157_cis_audit.py SINCE=2026-11-23T00:00:00Z`
- `.tmp-session/S288/live/aa1157_booking_audit.py` (role `booking`):
  `ECSX_SERVICE=aa-booking-dev-api tools/ecs/ecsx.sh .tmp-session/S288/live/aa1157_booking_audit.py SINCE=2026-11-23T00:00:00Z`

Expected:
- CIS:
  - `columns` = `{tenant_id: YES, view_role: YES}` and `schema_470_registered` = 1.
  - A role session `view_role=custom_content`, `tenant_null=true`, `ended=true`, `end_reason=ended`.
  - `audit_rows`:
    - one `staff.view_as_started` row: `tenant_null=true`, `resource_type=staff_view_as_session`,
      `view_role=custom_content`, `capabilities=18`, `reason_text_in_details=false`;
    - one `staff.view_as_ended` row with the same session.
  - `pairing.started_without_end` is empty.
  - `view_as_refusals` holds the E2E refusals of this check: `staff.request`, POST, 403, `no_view`, `view-as/roles`.
- Booking:
  - One `staff.view_as_started` row: `target_role=custom_product_ops_accounting`, `capabilities=24`, `minutes=30`.
  - One `staff.view_as_ended` row: `end_reason=ended`, same session.
  - `pairing.started_without_end` is empty.

## Files

- `cis-roles-e2e-admin-no-view-as.png`: CIS Roles & permissions as the E2E admin. No "View as" control, no banner.
- `booking-roles-e2e-no-view-as.png`: Booking Roles as the E2E staff user. No "View as a role" panel, no banner.
- `results.json`: the raw answers of the live checks (role catalogue trimmed to codes and capability counts).
