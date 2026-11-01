# UAT dry run — 2026-10-31

Started 2026-10-31T16:59:30.430Z, finished 2026-10-31T17:02:43.714Z. Mode: fast (asserts only, no video, no TTS). Egress: VN.
Result: **19 PASS**, 4 FAIL, 0 BLOCKED, 0 CRASH of 23 scenarios.
No writes (non-GET requests are aborted and listed), no LLM or paid calls, Dev only. Cost $0.
Not run: CRM-01, CRM-02, CRM-05, CRM-07 (their identity can write; run with --include-writable).

## App versions

| App | SHA at start | SHA at end | Source | Note |
|---|---|---|---|---|
| cis-api | d649cf0 | d649cf0 | /health |  |
| cis-admin (Vercel) | f47637a | be75f49 | repo main head (no version endpoint) | redeployed during the run |
| booking-api | 16fbed6 | 16fbed6 | /booking/health |  |
| booking-admin (Vercel) | 16fbed6 | 16fbed6 | repo main head (no version endpoint) |  |
| crm-api | 9bf771e | 9bf771e | /crm/health |  |
| crm-web | 9bf771e | 9bf771e | /healthz |  |
| content-studio | 4e1b32d | 4e1b32d | /api/healthz |  |
| tripplanner | 4fd7dca | 4fd7dca | /api/health |  |

## Sign-in per identity

| Identity | Result |
|---|---|
| studio | saved session still valid |
| cis-admin | saved session still valid |
| booking | saved session still valid |

## Scenarios

| Id | App | Identity | Title | Verdict | Steps | Time | Failure / note |
|---|---|---|---|---|---|---|---|
| TP-PUB-01 | tripplanner | public | Browse destinations and open a tour | PASS | 7/7 | 5.6 s |  |
| TP-02 | tripplanner | public | A destination page: its tours and the places they visit | PASS | 4/4 | 1.5 s |  |
| TP-07 | tripplanner | public | Browse on a phone | PASS | 3/3 | 4.5 s |  |
| TP-PUB-02 | tripplanner | public | Read the privacy notice and the terms of use | PASS | 2/2 | 3.3 s |  |
| PORTAL-PUB-01 | partner-portal | public | Read the partner terms and the privacy notice | PASS | 6/6 | 3.7 s |  |
| PRT-01 | content-studio | studio | Content studio: dashboard and my content | PASS | 2/2 | 6.6 s |  |
| PRT-03 | content-studio | studio | Marketplace: browse the catalog and open a tour | PASS | 3/3 | 4.8 s |  |
| PRT-09 | content-studio | studio | Tenant facts the writer cites | PASS | 2/2 | 2.0 s |  |
| PRT-10 | content-studio | studio | API access and the Facebook help page | PASS | 2/2 | 2.6 s |  |
| CIS-01 | cis-admin | cis-admin | Admin shell: overview, navigation and the review queue | PASS | 4/4 | 3.2 s |  |
| CIS-03 | cis-admin | cis-admin | Master content: the rewritten tours | PASS | 2/2 | 1.7 s |  |
| CIS-04 | cis-admin | cis-admin | Content Quality: the quality signals of tenant content | PASS | 2/2 | 2.1 s |  |
| CIS-05 | cis-admin | cis-admin | Social content: the atoms behind social posts | PASS | 2/2 | 2.4 s |  |
| CIS-06 | cis-admin | cis-admin | Tenants and the apps of the platform | PASS | 2/2 | 4.1 s |  |
| CIS-08 | cis-admin | cis-admin | Jobs and Cost Operations | FAIL | 1/4 | 21.7 s | step 2: expect(locator).toBeVisible() failed |
| CIS-11 | cis-admin | cis-admin | Docs reader: a page in English and in Vietnamese | PASS | 3/3 | 3.1 s |  |
| CIS-12 | cis-admin | cis-admin | Writing memory: signals, candidate rules and releases | FAIL | 1/3 | 24.4 s | step 2: expect(locator).toBeVisible() failed |
| BK-01 | booking | booking | Booking dashboard and notifications | PASS | 3/3 | 2.6 s |  |
| BK-05 | booking | booking | Suppliers and contracts | PASS | 3/3 | 4.5 s |  |
| BK-06 | booking | booking | Hotels and services | PASS | 3/3 | 3.9 s |  |
| BK-07 | booking | booking | Trip plans and pricing rules | PASS | 3/3 | 6.1 s |  |
| BK-08 | booking | booking | Operations: invoices, payments and trip checks | FAIL | 1/3 | 21.8 s | step 2: expect(locator).toBeVisible() failed |
| BK-10 | booking | booking | Customers, audit log and staff | FAIL | 1/3 | 34.2 s | step 2: expect(received).toBe(expected) // Object.is equality |

## Steps

| Id | Step | Status | Time | Error |
|---|---|---|---|---|
| TP-PUB-01 | 1 | PASS | 2.3 s |  |
| TP-PUB-01 | 2 | PASS | 0.4 s |  |
| TP-PUB-01 | 3 | PASS | 0.2 s |  |
| TP-PUB-01 | 4 | PASS | 0.5 s |  |
| TP-PUB-01 | 5 | PASS | 0.5 s |  |
| TP-PUB-01 | 6 | PASS | 1.4 s |  |
| TP-PUB-01 | 7 | PASS | 0.2 s |  |
| TP-02 | 1 | PASS | 0.4 s |  |
| TP-02 | 2 | PASS | 0.5 s |  |
| TP-02 | 3 | PASS | 0.2 s |  |
| TP-02 | 4 | PASS | 0.2 s |  |
| TP-07 | 1 | PASS | 2.8 s |  |
| TP-07 | 2 | PASS | 1.4 s |  |
| TP-07 | 3 | PASS | 0.0 s |  |
| TP-PUB-02 | 1 | PASS | 0.6 s |  |
| TP-PUB-02 | 2 | PASS | 2.4 s |  |
| PORTAL-PUB-01 | 1 | PASS | 1.1 s |  |
| PORTAL-PUB-01 | 2 | PASS | 0.4 s |  |
| PORTAL-PUB-01 | 3 | PASS | 0.2 s |  |
| PORTAL-PUB-01 | 4 | PASS | 1.1 s |  |
| PORTAL-PUB-01 | 5 | PASS | 0.5 s |  |
| PORTAL-PUB-01 | 6 | PASS | 0.2 s |  |
| PRT-01 | 1 | PASS | 3.4 s |  |
| PRT-01 | 2 | PASS | 2.9 s |  |
| PRT-03 | 1 | PASS | 2.6 s |  |
| PRT-03 | 2 | PASS | 0.3 s |  |
| PRT-03 | 3 | PASS | 1.6 s |  |
| PRT-09 | 1 | PASS | 1.5 s |  |
| PRT-09 | 2 | PASS | 0.2 s |  |
| PRT-10 | 1 | PASS | 1.1 s |  |
| PRT-10 | 2 | PASS | 1.2 s |  |
| CIS-01 | 1 | PASS | 0.8 s |  |
| CIS-01 | 2 | PASS | 0.2 s |  |
| CIS-01 | 3 | PASS | 1.8 s |  |
| CIS-01 | 4 | PASS | 0.0 s |  |
| CIS-03 | 1 | PASS | 1.2 s |  |
| CIS-03 | 2 | PASS | 0.2 s |  |
| CIS-04 | 1 | PASS | 1.3 s |  |
| CIS-04 | 2 | PASS | 0.5 s |  |
| CIS-05 | 1 | PASS | 1.8 s |  |
| CIS-05 | 2 | PASS | 0.3 s |  |
| CIS-06 | 1 | PASS | 3.1 s |  |
| CIS-06 | 2 | PASS | 0.7 s |  |
| CIS-08 | 1 | PASS | 1.2 s |  |
| CIS-08 | 2 | FAIL | 20.1 s | expect(locator).toBeVisible() failed |
| CIS-08 | 3 | NOT RUN | — |  |
| CIS-08 | 4 | NOT RUN | — |  |
| CIS-11 | 1 | PASS | 1.7 s |  |
| CIS-11 | 2 | PASS | 0.7 s |  |
| CIS-11 | 3 | PASS | 0.4 s |  |
| CIS-12 | 1 | PASS | 1.8 s |  |
| CIS-12 | 2 | FAIL | 22.1 s | expect(locator).toBeVisible() failed |
| CIS-12 | 3 | NOT RUN | — |  |
| BK-01 | 1 | PASS | 1.3 s |  |
| BK-01 | 2 | PASS | 0.2 s |  |
| BK-01 | 3 | PASS | 0.8 s |  |
| BK-05 | 1 | PASS | 1.3 s |  |
| BK-05 | 2 | PASS | 1.8 s |  |
| BK-05 | 3 | PASS | 1.2 s |  |
| BK-06 | 1 | PASS | 1.4 s |  |
| BK-06 | 2 | PASS | 1.1 s |  |
| BK-06 | 3 | PASS | 1.1 s |  |
| BK-07 | 1 | PASS | 3.8 s |  |
| BK-07 | 2 | PASS | 1.3 s |  |
| BK-07 | 3 | PASS | 0.7 s |  |
| BK-08 | 1 | PASS | 1.2 s |  |
| BK-08 | 2 | FAIL | 20.1 s | expect(locator).toBeVisible() failed |
| BK-08 | 3 | NOT RUN | — |  |
| BK-10 | 1 | PASS | 1.4 s |  |
| BK-10 | 2 | FAIL | 32.3 s | expect(received).toBe(expected) // Object.is equality |
| BK-10 | 3 | NOT RUN | — |  |
