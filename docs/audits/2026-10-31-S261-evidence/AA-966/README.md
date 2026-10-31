# AA-966 — CRM Reports + AA insights: live check on Dev (S261, 31/10/2026)

- **What:** the CRM Reports page (A-14), the Home KPI tiles (A-01), the CSV export, and the AA insights read
  (`GET /crm/ops/v1/insights`) shipped in AA-Partner PR #144.
- **Build checked:** CRM API `/crm/health`: `git_sha 132112aa1fbf…`, version 0.11.0.
  `/crm/health/ready`: `status ok`, `schema_version crm-031`, and `crm-001`…`crm-031` all in `registered_keys`.
- **Host:** `https://portal.lumiguides.it.com` (the CRM web, the BFF `/bff/*`, and the API under `/crm/...`).
- **How:**
  - Headless Playwright (Chromium), one browser at a time, closed at the end.
  - The agency calls went through the same-origin BFF from a signed-in page.
  - The ops call used the Bearer access token of the Dev-only E2E CIS admin.
  - Run log: `run-log.txt` (secrets and tokens are never logged). Spec: `.tmp-session/S261/aa966/live.spec.ts`, local only.
- **Identities:**
  - Sen Vang, owner and assistant: synthetic agency "Lữ hành Sen Vàng", tenant `bab16039`.
  - Second agency: Southern Cross Journeys owner, tenant `b9fa1635`.
  - CIS admin: the E2E admin `e2e-cis-admin@e2e-mail…` (group `cis-admin`, read-only).
  - All CRM users signed in through the partner pool (password + authenticator). The CIS admin signed in with an
    e-mail code from the `inbound-admin/` mailbox, read by the MFA admin role, the same way as the existing helpers.
- **Atlas & Hearth:** the task asked for it as the isolation tenant, but it is a CIS Content studio tenant and has no
  CRM E2E login. The second CRM agency with an E2E login, Southern Cross Journeys, was used instead (as in the
  AA-953 and AA-962 runs).
- **Window:** `period=30d` is 2026-10-02..2026-10-31 (Asia/Ho_Chi_Minh), base currency USD.

## Result per Done-when line

| # | Done-when (live steps, `l5-pr1-live.json`) | Result |
|---|---|---|
| 1 | `/health/ready` 200, crm-031 registered, nothing missing | **Pass.** `status ok`, `schema_version crm-031`, crm-031 in `registered_keys`. The ready body has no `missing_schema_versions` key. |
| 2 | Insights `budget_band` / `2026-Q4` → 200 with the documented keys, k_min 10, agencies_min 3, every cell ≥10 travellers and ≥3 agencies, no tenant id | **Pass, with a limit.** 200 with exactly `generated_at, dimension, quarter "2026-Q4", from "2026-10-01", to "2026-12-01", agencies_included 4, agencies_opted_out 0, k_min 10, agencies_min 3, cells [], suppressed_cells 2`. No `tenant_id` or `agency_id` anywhere. Dev has only 4 synthetic agencies, so every cell is suppressed and `cells` is empty. The cell threshold rule is therefore only checked on an empty list (see Not tested). The other 5 dimensions also return 200 (suppressed 1/0/2/4/1, cells 0). |
| 2b | `from/to` instead of `quarter` → 422 `invalid_request`; `quarter=2026-Q5` → 422 `invalid_quarter` | **Pass.** 422 `invalid_request` and 422 `invalid_quarter`. Control call with no token: 401. |
| 3 | Owner `reports/summary?period=30d` 200; `payments.open_invoices[*].outstanding` = sum of `balance_amount` over receivables per currency; `schedule_due` only rows with no issued invoice | **Pass.** Receivables (`GET /invoices`, default open / payment_claimed / expired) list 2 invoices with balance **USD 1,080.00**. The report shows `open_invoices` USD count 2, outstanding **1,080.00**. Direct count over all 57 trips (each trip's lifecycle schedule minus rows billed by a non-draft, non-void invoice): balance 17 rows **USD 15,786.00** and deposit 1 row **USD 540.00**. The report's `schedule_due` has the same values. |
| 3b | `reports/export?section=outstanding` CSV: `what` column only `open_invoices` / `schedule_not_invoiced` | **Pass.** 200 `text/csv; charset=utf-8`, 3 rows, `what` ∈ {`open_invoices`, `schedule_not_invoiced`}. |
| 4 | `/reports` screenshots 1440 and 390, light and dark; Outstanding panel shows "… not invoiced yet" | **Pass.** All 14 page sections render (list below). The Outstanding panel shows "Balances not invoiced yet (USD)" and "Deposits not invoiced yet (USD)". No sideways overflow at 1440 or 390. No console errors and no CRM response ≥ 400 on the owner run. The Dev E2E workflow `e2e/tests/reports.spec.ts` was **not** run from here (see Not tested). |

## Extra checks asked by the task

- **Two numbers compared with direct counts** (owner, 30d):
  - Inquiries tile 57 = pipeline board open 39 + closed 18. The 3-month trend is Aug 0, Sep 0, Oct 57, and the
    12-month value is also 57, so every trip falls in the window.
  - `open_trips` by stage (29/0/4/6/0/0) = pipeline stage counts.
  - Funnel lost 1 / cancelled 15 / completed 2 = pipeline closed counts.
  - Open-invoice outstanding = receivables (above).
- **Sections on `/reports`:** `reports-tiles, -funnel, -open, -outcomes, -sources, -picks, -money, -products,
  -payments, -team, -success, -insights, -export` all visible for the owner.
- **CSV:**
  - The UI "Export CSV" downloads `report-funnel-30d-20261031.csv` with header `stage,trips`.
  - The bytes start with the UTF-8 BOM (EF BB BF), and lines end with CRLF.
  - The owner gets `money_by_month` with 200 and header
    `month,currency,lines,sell,cost,margin,margin_pct,commission_expected`.
- **Formula guard:**
  - One synthetic booking line titled `=SUM(1+1) E2E AA966 vxwaau` was put on synthetic trip `6034f3a8`
    (lead "E2E S261 Payer …"), using the agency's own supplier, money 1.00 USD, then confirmed.
  - The owner's `top_products` CSV row is `agency,'=SUM(1+1) E2E AA966 vxwaau,1,1,USD,1.00`.
  - The assistant's row is `agency,'=SUM(1+1) E2E AA966 vxwaau,1,1`.
  - In both, the cell is prefixed with `'`. The JSON and the page show the raw title, which is expected.
  - The line was cancelled afterwards (200, `cancelled`) and is gone from `top_products`.
- **Assistant (Sen Vang `sen-vang-assistant`) cannot see money:**
  - `reports/summary` 200 with `money_visible false` and `money null`. Tiles are `inquiries, win_rate, aa_share`
    only (AA share by bookings, not sales).
  - No margin, cost or sell key. The only money-like name is the success-metric key `commission_unclaimed`, which is
    a not-built count.
  - `export?section=money_by_month` returns **403** `role_forbidden` ("the assistant role may not do view_margin").
  - `top_products` CSV has no `sell` column.
  - The UI hides the Revenue and margin panel, and the Export menu does not offer the money section.
  - The assistant does see Outstanding payments (invoice and schedule sell amounts). By design that section carries
    no margin.
- **Second agency isolation (Southern Cross Journeys owner, tenant ≠ Sen Vang):**
  - Its report shows its own data only: inquiries 0, pipeline 0, open trips all 0, no open invoices (its receivables
    are also empty).
  - Its team has 4 members, and the Sen Vang owner's member id is not among them.
  - The Sen Vang guard line is in neither its summary JSON nor its CSV.
- **Home KPI tiles:**
  - `crm-home-tiles` shows "Last 12 months": Inquiries 57, Win rate 40.4 %, Sold 2,345.60 USD, Margin 1,574.66 USD,
    AA share 63.9 %, each with its 3-month trend, plus an "Open reports" link.
  - These equal `GET reports/tiles` (2025-11-01..2026-10-31).

## Screenshots

| File | What |
|---|---|
| `01-reports-owner-light-1440.png` | `/reports?period=30d`, owner, light, 1440 (full page) |
| `02-reports-owner-light-390.png` | same, 390 |
| `03-reports-outstanding-panel-1440.png` | Outstanding payments panel: open invoices + "Balances/Deposits not invoiced yet" |
| `04-home-tiles-owner-light-1440.png` | Home with the KPI tiles, 1440 |
| `05-home-tiles-owner-light-390.png` | Home tiles, 390 |
| `06-reports-owner-dark-1440.png` | `/reports`, owner, dark (`data-theme=dark`), 1440 |
| `07-reports-owner-dark-390.png` | same, dark, 390 |
| `08-reports-assistant-light-1440.png` | `/reports` as the assistant: no Revenue and margin panel. Taken while the synthetic guard line was confirmed, so it is listed in Top products. |
| `09-reports-second-agency-light-1440.png` | `/reports` as the Southern Cross owner (its own, empty numbers) |

## Observations (not failures)

- At 1440, the tables in the narrower panels cut the last column at the panel edge: Open trips now "Days…", Revenue
  and margin "Margin %", Team activity "Overdue tasks". The page itself does not scroll sideways (overflow 0 px), and
  the cut columns look like the table's own scroll area. Worth a look in the Figma or visual pass. Not a data problem.
- On the assistant run, the console shows one 403 error. It comes from this check's own call to the money CSV, not
  from the page.

## Not tested, and why

- **Dev E2E `e2e/tests/reports.spec.ts` through `e2e-dev.yml`:** this lane may not run `gh workflow run`. The same
  steps (sections, CSV download with header `stage,trips`, Home tiles, 1440/390 light and dark shots) were done here
  by hand. The orchestrator step is listed below.
- **Insights cells above the thresholds and the 70 % dominance rule:** Dev holds 4 synthetic agencies with few
  travellers, so every cell is suppressed (`cells: []`). Nothing on Dev can show a published cell. The rule is covered
  by the unit property test (`api/tests/unit/test_reports.py`) only.
- **Insights opt-out (`agencies_opted_out > 0`):** this is a platform-admin write, and the E2E CIS admin is read-only.
  Not done.
- **The agent role** (`sen-vang-agent`) seeing money: not checked. Only owner and assistant were.
- **The `owner=` filter** (`me` or a member id) on summary and export: the links render, but the numbers were not
  reconciled.
- **Dark-mode shots** were taken for the owner `/reports` only, not for Home, the assistant or the second agency.
- **The CSV `report_export` audit event:** not read back. The success metric "Reports downloaded" rose from 5
  (owner run) to 10 (assistant run), which matches the exports made in between, but no audit row was inspected.
- **Isolation with data on both sides:** the second agency has no trips, so its view proves it gets none of Sen
  Vang's data, but not a partial mix of two non-empty data sets. RLS on the report SQL is covered by
  `api/tests/integration/test_reports_api.py`.

## Test data left on Dev (synthetic)

- One **cancelled** booking line `=SUM(1+1) E2E AA966 vxwaau` (confirmation `E2E-AA966-vxwaau`, sell and cost 1.00 USD)
  on Sen Vang synthetic trip `6034f3a8` (stage proposal).
- About 10 `report_export` audit events on Sen Vang.
- New sessions for the assistant and Southern Cross E2E users.
