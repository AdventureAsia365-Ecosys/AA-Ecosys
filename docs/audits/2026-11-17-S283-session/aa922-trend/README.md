# AA-922 writing-memory weekly KPI — scheduled runs (S283, 17/11/2026)

Read-only read of `shared.job` kind `writing_memory_kpi_weekly` (ECS exec, CIS app login). Every week below is stored
as a report (`stored: true`), 0 USD per run.

| Week start | Trigger | Status | Note |
|---|---|---|---|
| 2026-10-19 | scheduler:aa-922 | succeeded | rules expired 0, reconfirmed 0, stale candidates 0 |
| 2026-10-26 | scheduler:aa-922 | succeeded | same |
| 2026-11-02 | scheduler:aa-922 | succeeded | same |
| 2026-11-09 | scheduler:aa-922 | failed ×2 (16/11 00:01Z) | `cannot extract elements from an object` — a Dev-only E2E fixture wrote `gate_ledger = '{}'` |
| 2026-11-09 | manual re-run (S283) | succeeded (17/11 00:44Z) | after CIS #1552 guarded every array-column read |

Trend: no rule expired or was reconfirmed in four weeks (no approved writing-memory rules exist yet; live rule expiry
moves to AA-920 release 1). The scheduler fires every Monday; the guard test
`tests/unit/test_aa922_array_column_guard.py` keeps the object-shaped rows from breaking the job again.
