# AA-1024: the rest of the lessons-to-guards design (lane l8-lessons-guards-rest, S272)

S271 built about half of the guards in the lessons-guards design (`docs/audits/2026-11-07-S271-lessons-to-guards/`,
guards G1-G22, and the critic's weak and missing lists). This lane checked every guard against `master` / `main` of
the repo it names, then built the ones that were missing. Earlier lanes: `AA-1024-l21-guards-root.md` (root, S271)
and the child-repo notes `AA-1024-l22-guards.md` (CIS), `AA-1024-s271-guards-infra.md` (Infra).

## Step 1: what was on main before this lane

Checked on origin/master (root 2e7e510e) and origin/main of each child repo (CIS 8e148fe4, Booking c9305c4,
Partner 38f99f53, TripPlanner 91d0608, Infra 75ddf66), 07/11/2026.

| Guard | Shipped | Evidence |
|---|---|---|
| G1 ship-wave + SHIP-1 | yes | `tools/github/ship_wave.py`, `tools/github/mergeq.sh:68` (DIRTY exit 4), `.claude/hooks/aa_shell_guard.py` SHIP-1, `as-app.sh` merge gate (`AA_SHIP_GATED`); no `.tmp-session` merge scripts in `.claude/settings.json` |
| G2 shell guard | partly | PKILL-1, ZSH-1, ENV-1 in `aa_shell_guard.py`; WT-1, BG-1 and TF-1 were dropped in S271 (critic: the planned regexes misfired) |
| G3 raw ECS exec refusal + ecsx hardening | no | only the subagent hook refuses `execute-command` (`subagent-guardrails.sh:22`); ecsx has no auto-resume, no local output file, no heartbeat, no timeout check |
| G4 RAM guard | yes | `aa_shell_guard.py` RAM-1, `lane_start_guard.py` lane RAM gate |
| G5 hook tests in root CI | yes | `.github/workflows/docs-lint.yml` "Claude hook tests", `.claude/hooks/test_settings_hooks.py` |
| G6 pre-push installed + integration + pinned venv | partly | (1) `tools/github/ship_open_prs.py` core.hooksPath check (#603); (2) CIS `scripts/pre-push.sh --integration` stamp (#1360); (3) `scripts/export_openapi.py` still only prints the versions; (4) no `pythonpath` in CIS `pyproject.toml` |
| G7 ORDER BY uuid lint | yes | `tests/unit/test_aa1024_sql_order_stability.py` in CIS, Booking (`backend/`), Partner (`api/`) |
| G8 304 LATER scanner + nightly | yes | CIS `tests/unit/test_aa1024_replay_later_list.py`, `.github/workflows/nightly-integration.yml` |
| G9 Terraform lock wait | yes | Infra `tools/terraform/tests/test_workflow_tf_locking.py` (lock wait instead of a plan concurrency group) |
| G10 dangling migration references | yes | `.github/scripts/migration_refs.py` in CIS, Booking, Partner, TripPlanner |
| G11 PR text guard + Done-evidence audit | no | `pr-title.yml` only in Booking, Partner, TripPlanner and only refuses `[AA-n]`; none in root, CIS, Infra; no `done_audit.py` |
| G12 master plan gate | yes | `.claude/hooks/lane_start_guard.py` (the publish stamp was left out) |
| G13 IAM trust inventory | yes | Infra `tools/terraform/iam_trust_inventory.py` (+ allowlist, tests); lessons.md cites it |
| G14 gitleaks before push + scan status | no | Booking, Partner, TripPlanner, Infra and root pre-push run gitleaks; CIS `scripts/pre-push.sh` does not; no session-start status of scheduled guard runs |
| G15 workflow lint | partly | Infra `.github/scripts/workflow_lint.py` + `workflow-lint.yml`; nothing in root, CIS, Booking, Partner, TripPlanner |
| G16 replay failures are errors | yes | CIS `tests/integration/_replay_guard.py` |
| G17 wave stop flags enforced | no | CIS `scripts/aa645/wave_report.py` computes `stop_conditions` and always exits 0 |
| G18 one cost source | no | no `tools/llm/spend_by_stage.py` / `cost_estimate.py` |
| G19 Stop hook | no | no Stop hook in `.claude/settings.json` |
| G20 lane resume state | no | `tools/workflows/lane.js` says it in prose only |
| G21 PII hook --check + safe DRY RUN snippet | no | no `--check` mode; `destructive-ops.md` has no pin snippet |
| G22 lessons lint + sweep | partly | `tools/docs/check_lessons.py` (+ weekly `--sweep`); a child-repo guard path is not checked in CI (no checkout there) |

## Decisions

(filled in as the lane goes)

## Changed (vs the design)

## Tradeoffs

## Should know
