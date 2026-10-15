# AA-681 Done-when demo on Dev: TC-000003 (S237)

Run by Claude Code (S237 orchestrator sub-agent) on 2026-10-14 23:47–23:48 UTC (15/10 06:47 ICT), following
`.tmp-session/s237/bk_demo.md` steps 0–9. Nghiệp approved the demo data on Dev. USD only, LLM cost $0.
Nothing was deployed, merged or changed in infrastructure.

- API: `https://9z3xnalp59.execute-api.us-west-1.amazonaws.com/dev/booking` (task def `aa-booking-dev-api:6`, rollout COMPLETED, desired 1 / running 1)
- Caller: staff `e2e-claude-code` (cis_user_id `2d8e5a2f-…4127`), role `admin`, active
- **Case: `TC-000003`** (id `4542b70e-3483-40d6-b7ce-c7d2c6c24427`), customer `CUS-000003` "S237 Demo Customer", notes `[S237 demo] …`

## Steps: expected vs actual

| # | Step | Expected | Actual | Result |
|---|---|---|---|---|
| 0 | Preconditions | `/health/ready` ok, schema `bk-006`; no deploy in flight | `{"status":"ok","db":"ok","schema_version":"bk-006"}`; one PRIMARY deployment, COMPLETED | PASS |
| 1 | Sign in, `/staff/me` | active, `version.write`, `trip_case.write`, `audit.read` | 200, role `admin`, active, all three permissions present | PASS |
| 2 | Create case + assign | 201, status `discovery`; assign 200 | 201 `TC-000003` `discovery` (admin not auto-assigned, `assignments: []`); assign 200 `changed: true` | PASS |
| 3 | V1 create, items, price | 1000 USD net -> `final_total 1495.00`, card fee `0.0300` | 201 V1 `draft`; items 200 (2 items); price 200: `1495.00` USD, card fee `0.0300`, margin `0.3011`, saved `1495.00` | PASS |
| 4 | Send V1 | case `proposal_sent`, `email_sent false` | 200, badge `sent`, case `proposal_sent`, `email_sent: false`, notification row written | PASS |
| 5 | V2 copy, change cruise cost, price | V2 copies V1 items + costs; total = API answer for 1120 net | 201 V2 `draft`; GET showed both items with V1 costs (new item ids); PUT 200 kept the same 2 ids (`costs_replaced: 1`); price 200: `1675.00` USD | PASS |
| 6 | Send V2 | V1 `superseded`, V2 `sent`, case stays `proposal_sent` | 200, case `proposal_sent`; `/versions?q=TC-000003` -> V2 `sent`, V1 `superseded` | PASS |
| 7 | Approve V2 (+ optional V1 negative) | case `confirmed`, V2 `approved`; V1 approve -> 409 `version_superseded` | 200, V2 `approved`, case `confirmed`; V1 approve -> 409 `{"detail":"version_superseded"}` | PASS |
| 8 | Activity trail | `discovery` -> `building` -> `proposal_sent` -> `confirmed` | 200, 15 rows; status rows `opened -> discovery`, `discovery -> building`, `building -> proposal_sent` (V1 sent), `proposal_sent -> confirmed` (V2 approved) | PASS |
| 9 | Audit log | case: `created` + assignment; versions: `created`, `items_replaced`, `priced`, `sent` for V1 and V2, `approved` for V2 | case: `trip_case.created`, `trip_case.assigned`; versions: 9 rows exactly as expected (4 for V1, 5 for V2) | PASS |
| 10 | UI screenshots | after the AA-683 close-out Vercel deploy | not run (out of scope for this run) | NOT RUN |
| 11 | Clean-up (optional) | cancel with reason | not run: case left `confirmed` so step 10 can screenshot the Confirmed stepper | NOT RUN |

## Final state

- Case `TC-000003`: **confirmed**
- V1: **superseded** (sent, 1495.00 USD) · V2: **approved** (locked, 1675.00 USD)

## Pricing (channel `b2c_tailor_made`, USD, not peak; rule valid from 2026-10-14: target 0.30, floor 0.20, card fee 0.03, rounding 5)

| Version | Net USD | Lines (net -> sell) | Subtotal | Final total | Effective margin |
|---|---|---|---|---|---|
| V1 | 1000.00 | 600.00 -> 895.52; 400.00 -> 597.01 | 1492.54 | **1495.00** | 0.3011 |
| V2 | 1120.00 | 600.00 -> 895.52; 520.00 -> 776.12 | 1671.64 | **1675.00** | 0.3013 |

## Audit / activity rows observed (UTC)

Case (`06-audit-case.json`): `trip_case.created` 23:47:15 "Created TC-000003 (discovery)"; `trip_case.assigned` 23:47:16.

Versions (`07-audit-versions.json`, `entity_type = trip_case_version`):
V1 `created` 23:47:26 ("from the trip legs", 0 items) -> `items_replaced` (2 items) -> `priced` 1495.00 -> `sent` 23:47:36 (valid until 2026-10-28, no e-mail);
V2 `created` 23:47:46 ("from V1", 2 items) -> `items_replaced` (2 items, 1 cost replaced) -> `priced` 1675.00 -> `sent` 23:47:57 -> `approved` 23:48:09 ("case confirmed").

Activity (`05-activity.json`, oldest first) merges the above with 4 `trip_case.status_changed` rows.

## Deviations / observations (none blocking)

1. The trail starts with a status row `opened -> discovery` (`before.status = null`), as the runbook predicted for a case created directly in `discovery` (not `new_inquiry`).
2. Rows that share a timestamp are not ordered by cause: at creation the status row comes before `trip_case.created`; at V2 approval `trip_case_version.approved` comes before `proposal_sent -> confirmed`. Cosmetic only.
3. No audit row is written for V1 turning `superseded`; the badge is derived when V2 is sent. Not required by the runbook.
4. The optional V1 negative check was run after approving V2 (safer order: a bug could not confirm V1). It returned the expected 409 `version_superseded`.
5. Steps 10 (UI screenshots) and 11 (cancel) were not run; the case stays `confirmed`. To cancel later: `POST /trip-cases/TC-000003/status` with `{"to_status":"cancelled","reason":"S237 demo case, not a real booking"}`.

## Files

`01-staff-me.json`, `02-create-case.json`, `03-pricing-v1-v2.json` (full quotes), `04-send-approve.json` (send/approve responses, negative check, version badges), `05-activity.json`, `06-audit-case.json`, `07-audit-versions.json` (filtered to TC-000003). No tokens or secrets are stored.
