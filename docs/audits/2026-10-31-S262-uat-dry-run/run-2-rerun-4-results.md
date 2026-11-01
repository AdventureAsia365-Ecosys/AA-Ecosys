# UAT dry run — 2026-10-31

Started 2026-10-31T17:06:10.719Z, finished 2026-10-31T17:06:44.768Z. Mode: fast (asserts only, no video, no TTS). Egress: VN.
Result: **4 PASS**, 0 FAIL, 0 BLOCKED, 0 CRASH of 4 scenarios.
No writes (non-GET requests are aborted and listed), no LLM or paid calls, Dev only. Cost $0.

## App versions

| App | SHA at start | SHA at end | Source | Note |
|---|---|---|---|---|
| cis-api | be75f49 | be75f49 | /health |  |
| cis-admin (Vercel) | be75f49 | be75f49 | repo main head (no version endpoint) |  |
| booking-api | 16fbed6 | 16fbed6 | /booking/health |  |
| booking-admin (Vercel) | 16fbed6 | 16fbed6 | repo main head (no version endpoint) |  |
| crm-api | 9bf771e | 9bf771e | /crm/health |  |
| crm-web | 9bf771e | 9bf771e | /healthz |  |
| content-studio | 4e1b32d | 4e1b32d | /api/healthz |  |
| tripplanner | 4fd7dca | 4fd7dca | /api/health |  |

## Sign-in per identity

| Identity | Result |
|---|---|
| cis-admin | saved session still valid |
| booking | saved session still valid |

## Scenarios

| Id | App | Identity | Title | Verdict | Steps | Time | Failure / note |
|---|---|---|---|---|---|---|---|
| CIS-08 | cis-admin | cis-admin | Jobs and Cost Operations | PASS | 4/4 | 3.6 s |  |
| CIS-12 | cis-admin | cis-admin | Writing memory: signals, candidate rules and releases | PASS | 3/3 | 5.2 s |  |
| BK-08 | booking | booking | Operations: invoices, payments and trip checks | PASS | 3/3 | 6.4 s |  |
| BK-10 | booking | booking | Customers, audit log and staff | PASS | 3/3 | 4.0 s |  |

## Steps

| Id | Step | Status | Time | Error |
|---|---|---|---|---|
| CIS-08 | 1 | PASS | 1.9 s |  |
| CIS-08 | 2 | PASS | 0.4 s |  |
| CIS-08 | 3 | PASS | 0.7 s |  |
| CIS-08 | 4 | PASS | 0.3 s |  |
| CIS-12 | 1 | PASS | 2.8 s |  |
| CIS-12 | 2 | PASS | 0.9 s |  |
| CIS-12 | 3 | PASS | 1.2 s |  |
| BK-08 | 1 | PASS | 3.6 s |  |
| BK-08 | 2 | PASS | 1.2 s |  |
| BK-08 | 3 | PASS | 1.3 s |  |
| BK-10 | 1 | PASS | 1.6 s |  |
| BK-10 | 2 | PASS | 1.0 s |  |
| BK-10 | 3 | PASS | 1.1 s |  |
