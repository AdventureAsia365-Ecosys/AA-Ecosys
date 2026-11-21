---
id: OPS-08-s287-aa1170-live-evidence
title: "S287 live evidence: AA-1170 Platform › Compliance readiness page"
description: "Agent-run live check on Dev, 21/11/2026: compliance overview, controls and control detail as the E2E CIS administrator, refresh attempt, screenshots at 1440 light/dark and 390 light."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-21
review_every_days: 30
related: [AA-1170]
---

# AA-1170 live check: Platform › Compliance readiness (S287)

- **Run:** 2026-11-21, 08:29 to 08:32 UTC, by a Claude Code subagent, in headless Chromium (Playwright). Cost: 0 USD.
- **Under test:**
  - CIS #1633 `102b05cb`. The live api reports git_sha `350353eb` (a later main, which contains #1633) and
    schema_version `468`.
  - The CIS admin at `https://aa-cis.lumiguides.it.com`.
  - The compliance register as loaded: 48 controls and 399 mappings.
  - The root collector `compliance-evidence.yml`, run #2 at 08:06 UTC.
- **Identity:** the Dev-only E2E CIS admin, role administrator, from the saved UAT state `cis-admin`. The state was
  still valid, so no new code was read. This is a read-only session: the API refuses its writes with
  `403 e2e_read_only`.
- **Masking:** screenshots mask any @-address and the account chip. No screenshot was taken on the managed-login host.
- **Raw numbers:** `aa1170-result.json`.

## Results

| # | Done-when item | Result |
|---|---|---|
| 1 | `GET /admin/platform/compliance` overview | **PASS** 200. 6 frameworks; register 253 requirements · 48 controls · 399 mappings; controls 8 met · 1 gap · 39 no evidence; checks 9 pass · 1 fail · 0 stale · 0 error |
| 2 | Evidenced % strict / weighted per framework | **PASS**, recorded in the table below. The low values are expected today, because 39 of the 48 controls are manual and have no evidence yet |
| 3 | Heartbeat source and age | **PASS**: source `root_daily`, last seen 2026-11-21 08:06:24 UTC, age 0.4 h, limit 36 h, `ok: true`, 10 evidence rows |
| 4 | Published evidence ingested | **PASS**: `ingest`: object `compliance/evidence.json`, state `ok`, 10 rows read, 10 new, 0 dropped. The overview GET did this ingest through its cached sync, at 08:29:47 UTC (see the refresh item) |
| 5 | `GET /controls` count | **PASS** 200, **48** controls (by state: `no_evidence` 39, `met` 8, `gap` 1). The UI table shows 48 rows |
| 6 | One control detail | **PASS** 200 for two controls. **`AAC-VUL-01`** "Image scanning, SBOM and valid exceptions": `met`, hybrid, 6 requirements (ISO 27001 ×3, SOC 2 ×2, OWASP Top 10 ×1). Its two required checks are `ci_image_scan_sbom` and `vuln_exceptions_valid`, both `pass`, collected 08:06:24 UTC, valid until 24/11 08:06 UTC, one history row each. **`AAC-AI-01`** "AI system inventory": `no_evidence`, manual, 8 requirements, 0 checks. An unknown id `ZZ-NOPE-99` answers 404 |
| 7 | `POST /refresh` (compliance.write), then re-read | **NOT TESTED (identity)**: 403 `{"detail":"e2e_read_only"}`. The E2E admin session is read-only by design (root ADR 0006a), so this run cannot make the write. The re-read overview is unchanged and still `ok` with 10 rows, because the GET had already ingested the published file. To test the button: the tech lead clicks **Refresh evidence** once as a real administrator, or a writable E2E identity with compliance.write is added |
| 8 | Banner "Readiness … not a certification" | **PASS**: `READINESS SCORE (DEV ENVIRONMENT), NOT A CERTIFICATION.` followed by the tamper-proof-store note. The page also carries a `DEV` badge |
| 9 | No issue IDs, account IDs or e-mails on the page | **PASS**: a scan of the page body on the Overview, on Controls and with the drawer open found 0 issue IDs (`AA-`, `KAN-`, `PR-`, `CON-` followed by digits), 0 12-digit numbers and 0 e-mail addresses. Control ids (`AAC-…`) and check ids are by design |
| 10 | Screenshots: Overview and Controls (drawer open) at 1440 light, 1440 dark and 390 light | **PASS**: the six files below, compressed (19 to 75 KiB). No horizontal page scroll at 390 on either tab |

### Evidenced % per framework (Dev, 21/11/2026 08:29 UTC)

| Framework | Requirements | Met | Partial | Gap | Stale | Not mapped | Strict % | Weighted % | Reference (hand) % |
|---|---|---|---|---|---|---|---|---|---|
| ISO/IEC 27001:2022 | 123 | 3 | 17 | 101 | 0 | 2 | 2.44 | 9.35 | 45.8 |
| SOC 2 (2017 TSC) | 33 | 0 | 11 | 22 | 0 | 0 | 0 | 16.67 | 44.0 |
| ISO/IEC 42001:2023 | 70 | 1 | 5 | 64 | 0 | 0 | 1.43 | 5.0 | 46.9 |
| OWASP Top 10 (2021) | 10 | 0 | 4 | 6 | 0 | 0 | 0 | 20.0 | 64.8 |
| OWASP Top 10 for LLM (2025) | 10 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 66.7 |
| EU AI Act (deployer duties) | 7 | 0 | 0 | 7 | 0 | 0 | 0 | 0 | none |

Settings in force: partial weight 0.5, heartbeat 36 h, `root_daily` validity 72 h, and four fact limits:
`ci_image_scan_sbom` 8 days, `last_access_review` 100 days, `last_restore_drill` 90 days, and
`docs_review_overdue` max 0.

One check needs attention: `scheduled_guards_green` is `fail` ("38/39 scheduled guards green") for control
`AAC-OPS-02`, which is therefore `gap`. That is a real finding of the collector, not a defect of the page. The trend
card says it appears after the page has been opened on two different days. The API trend already holds today's point.

### Screenshots

| File | View |
|---|---|
| `aa1170-01-overview-1440-light.png` | Overview, full page: tiles, the six framework cards, trend, attention table, Collectors |
| `aa1170-02-overview-1440-dark.png` | Same, dark |
| `aa1170-03-overview-390-light.png` | Overview at 390, top of the page with the banner |
| `aa1170-04-controls-drawer-1440-light.png` | Controls tab with the `AAC-VUL-01` drawer open: requirements covered, both checks with history |
| `aa1170-05-controls-drawer-1440-dark.png` | Same, dark |
| `aa1170-06-controls-drawer-390-light.png` | The drawer at 390 |

## Notes

- **Console and network:** the only failed requests were this run's own probes, the 404 for the unknown control and
  the 403 refresh. There were no other console errors.
- **Times:** the page shows them in the viewer's time zone, so the 08:06 UTC collection appears as "21 Nov 2026, 15:06"
  at +07.
- **Refresh button (minor UX):** **Refresh evidence** is shown to every reader of the page. For this read-only E2E
  session a click would answer 403. Real administrators have compliance.write, so this does not block anything; it is
  only noted.
- **Masked close button:** in the drawer shots, the mask over the account chip also covers the drawer's close button in
  the top-right corner. The page itself is fine there.
