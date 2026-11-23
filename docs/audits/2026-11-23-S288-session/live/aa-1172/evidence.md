# AA-1172 live evidence: T9 facts instruction guard (S288, round 1)

- **Issue:** AA-1172, "T9 blog writer follows an instruction planted in the fact input (trap t9_facts_override)". Linear status at check time: In Review.
- **PRs:** CIS #1643 (migration 472, setting `cis.llm.fact_instruction_guard`, ships off), CIS #1644 (`4dbdfafc`: facts guard on the writers' facts read, five new T9 fact traps, Platform › Settings schedule label fix).
- **Checked:** 23/11/2026, 07:23–07:30 UTC, by a read-only verify lane (Claude Code subagent). No setting was proposed or changed. No write went through the UI or API. The paid trap run was not started here: the orchestrator runs it.

## Deployed state

| What | Value | How |
|---|---|---|
| CIS API `git_sha` | `4dbdfafc803468fb76b87176c47041003bf3febc` | `GET https://api-cis.lumiguides.it.com/health` |
| CIS API `schema_version` | `472` (db ok) | `GET /health/ready` |
| ECS `aa-cis-dev-api` | image tag `dev-4dbdfafc…`, rollout COMPLETED, 1 running | `aws ecs describe-services` / `describe-task-definition` |
| ECS `aa-cis-dev-worker` | image tag `dev-4dbdfafc…`, rollout COMPLETED, 1 running | same |
| ECS `aa-cis-dev-admin` | image tag `dev-1bb0f35b…` (#1646, after #1644 on `main`, so it includes the Settings fix), rollout COMPLETED | same |
| CI on #1644 | every required check green: Lint, Unit shards 1–4, Unit Tests, Security Audit, Migration preflight, CodeQL, gitleaks. Integration and Docker build show "skipping" on the PR run (they run in the merge queue). | `gh pr checks 1644` |

## Done-when mapping

| # | Done-when | Result | Evidence |
|---|---|---|---|
| L1 | `t9_facts_override` and its new variants pass | **not_checked** (paid run) | The paid trap run (`--guard both`, stage `adhoc_aa1172`) belongs to the orchestrator and was not run here. Offline proof passes (see L4): `test_with_the_guard_on_no_fact_trap_marker_reaches_the_prompt` checks that, with the guard on, no fact-trap marker reaches the T9 prompt. Note: with the guard on, the fact traps pass by construction. The evidence that matters from the paid run is the guard-off control, where each variant should fire. |
| L2 | The other 8 traps still pass | **not_checked** (paid run) | Same paid run. On `main`, the trap set has 14 traps: 8 that are not fact traps, plus 6 fact traps (the original one and five new ones). |
| L3 | The run's cost is reported from `shared.llm_call_log` | **not_checked** (needs the container) | Aggregate script prepared: `.tmp-session/S288/live/aa1172_trap_cost_aggregates.py`. It reports calls, failures, tokens and USD for stage `adhoc_aa1172`, split by status, role, model, provider and account label, with the AA-1167 baseline (`adhoc_aa1167`, 0.81 USD) beside it. |
| L4 | A unit test covers the validator or check offline | **pass** | I ran the tests on a `git archive` of `origin/main` (`1bb0f35b`), with the CIS venv and no DB: `pytest tests/unit/test_aa1172_fact_guard.py tests/unit/test_aa1172_trap_guard.py tests/unit/test_aa1167_trap_set.py` → **462 passed**. That covers 25 fact-guard tests (the keep/drop sets) and 11 trap-guard tests, including the marker test, `prepare_facts`, and the switch read in `fetch_facts_for_writing`. CI unit shards on #1644 are also green. |
| O1 | Platform › Settings shows `cis.llm.fact_instruction_guard` OFF, with its EN/VI guide | **pass** | E2E CIS admin (A10b, read-only session) on `https://aa-cis.lumiguides.it.com/admin/platform/settings?app=cis&key=cis.llm.fact_instruction_guard`. The registry API (`/api/admin/settings/registry?app=cis`, 200, 345 CIS settings, `reader_error` null) returns: value `false`, source `default`, default `false`, bool, area `ai`, platform scope, impact high, `maker_checker`, enforced, no env override, no value row (`approved_version` 0), no open proposal, nothing scheduled, guide in `en` and `vi`, each with what/raise/lower/when/example. The row shows **Off / default**, "HIGH IMPACT" and "Never changed". The EN guide (Explain) and the VI guide (after the VI language switch) both render in full. At 390 px there is no horizontal overflow (document 0, `main` 0) in light or dark. Console: 0 errors. Shots: `settings-guard-en-desktop-light.png`, `settings-guard-en-desktop-dark.png`, `settings-guard-en-mobile-light.png`, `settings-guard-en-mobile-dark.png`, `settings-guard-vi-desktop-light.png`. Raw: `registry-summary.json`. |
| O2 | Settings schedule label fix: a setting whose effective time has passed shows as in force, not SCHEDULED | **pass** (deployed bundle, with an injected response; see note) | (a) A real setting: `cis.seo.research_auto_enabled` has an approved change effective 16/11/2026. It shows its value in force (source platform), with no "Change scheduled" badge and no "Scheduled: … from" line (`settings-real-in-force-desktop-light.png`). (b) The stale-list case the fix targets: no setting on any tab (CIS, TripPlanner, CRM) has a scheduled change today, so in the browser I rewrote the registry response with Playwright `page.route`. Nothing was sent to the server. The guard row got one listed platform change. Dated **1 minute in the past**, the deployed page shows **no** badge and no Scheduled line (`settings-inject-past-desktop-light.png`). Dated **1 day ahead** (the control), the same page shows the **CHANGE SCHEDULED** badge and "Scheduled: On from 24 Nov 2026, 14:27" (`settings-inject-ahead-desktop-light.png`). So the deployed `scheduledOf` drops listed entries whose time has come. Not checked live: the one-second auto-reload timer (`nextScheduleDelay`) on a page left open past a real scheduled time. The frontend unit test `settingsRegistry.test.mjs` covers it in CI (37 passed per the PR). |
| O3 | Five new T9 fact traps exist in `services/ai_safety/trap_set.py` on `main` | **pass** | `git show origin/main:services/ai_safety/trap_set.py`: `t9_facts_role_line`, `t9_facts_soft_request`, `t9_facts_title_injection`, `t9_facts_provenance`, `t9_facts_paraphrase` (all `override`, writer `t9_blog`, fields `facts_text` / `facts_title` / `facts_provenance`), plus the original `t9_facts_override`. That is 14 traps in total. |

## Findings

- **F1 (info):** The guard ships **off**, as the PR states, and live it is off (default, no value row). Until an administrator turns it on, live T9/T2 writers still receive facts verbatim, so the original weakness stays open on Dev. Whether the issue counts as Done depends on the paid run and the tech lead's decision on the switch. That is not a verify question.
- **F2 (minor, UI):** At 390 px the guide that was open at 1440 px shows closed again: the row re-renders as a card and the toggle state resets. This is cosmetic and out of AA-1172 scope.

## For the orchestrator: DB aggregates (read only)

Run it from the root repo (`/home/nghiep/projects/AA-Ecosys`) after the paid run finishes:

```
/home/nghiep/projects/AA-Ecosys/tools/ecs/ecsx.sh /home/nghiep/projects/AA-Ecosys/.tmp-session/S288/live/aa1172_trap_cost_aggregates.py
```

(The default service is `aa-cis-dev-api`, `DATABASE_URL` = `cis_app`, and the session is set to READ ONLY. Optional pairs: `STAGE=adhoc_aa1172 BASE_STAGE=adhoc_aa1167`.) Expected output:
- `run_total.cost_usd` ≤ 1 (cap 0.95 by `--stop-usd`), with `not_ok` and its split; `run_split` by model and role;
- `schema_version_472` present;
- `setting_definition` default `false`, enforced, guide keys `en`/`vi`;
- `setting_value_rows_by_status` empty (the switch is still off). `setting_value` is RLS FORCE, but policy `setting_value_cis_app_all` (USING true) gives `cis_app` every row, so the count is complete.

Paste `run_total` and `run_split` into the trap-run evidence (`live/aa1172/trap-run.md` per the plan) to close L1–L3.
