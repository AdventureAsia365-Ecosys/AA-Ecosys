# AA-896 — Implementation notes (root repo, lane: plan-sync, S263)

Scope: the tracker sync approved by the tech lead in S263 (P10, $0), built to the design in
`docs/audits/2026-11-01-S262-assessment-followup/README.md` section 6. Tied to AA-896 lane L0 tracker work.

## Decisions

- **Pure core, thin I/O.** `merge(plan, linear, closed) -> (new_plan, diff)`, `validate`, `scope_violations`,
  `log_draft`, `stamp` and `dumps` take and return plain data; only `fetch_open`, `fetch_changed_since`, `api_key` and
  file writes touch the outside. The tests mock those three and never need a key or the network.
- **Project mapping by prefix table in the script** (`Data Platform`, `CIS Core`, `CIS Portal`, `TripPlanner`,
  `AA-Booking`, `Partner CRM`), not from the `projects` block: the Linear name "TripPlanner & AA-Booking" does not start
  with the plan label "TripPlanner & Booking". Unknown or missing project warns and maps to `other`.
- **Log window = `updated` of plan.json at git HEAD**, not the file on disk, so the local session-start `--write`
  (not committed) does not shrink the window of the session-close `--log-draft`. `--since` overrides.
- **`reopened` stays empty in the draft**: rule 6.4.2 says a reopened issue enters as new; the draft cannot tell a
  reopen from a new issue without history, so a person fills it.
- **`--session S263` also sets `next_session = S264`** (hand-owned otherwise; edit by hand when the next session is
  not the next number).
- **Offline modes for CI.** `--validate` (shape, due/risks, public safety, unknown session/milestone as warnings) and
  `--check-scope BASE` (fails when anything outside the Linear-owned fields changed). Docs lint runs the unit tests and
  `--validate` on every PR touching `docs/**` or `tools/linear/**`.
- **Bot disabled by default.** `.github/workflows/plan-sync.yml` has `workflow_dispatch` only; the cron line is
  commented. It needs a repo secret `LINEAR_PLAN_SYNC_KEY` (own narrow key) and the aa-ecosys-ci-bot App in the root
  repo, because a PR opened with `GITHUB_TOKEN` would not start Docs lint / gitleaks. No Linear key: notice, not fail.

## Changed

- `tools/linear/linear_api.py` new: `api_key()` and `gql()` moved out of `linear_export.py` unchanged; the export
  script imports them.
- `docs/backlog/tracker/index.html`: header shows "Đồng bộ Linear: <synced_at>" ("chưa" when absent); footer says which
  fields come from Linear. `PRI["No priority"]` was already fixed on master (S262), nothing to do.
- `docs/backlog/tracker/README.md`: field ownership table, commands, new session-close steps (step 1 is now the
  script); the old one-line validator is replaced by `--validate`.
- `skill/aa-session/SKILL.md`: session start runs `--write` locally; session close runs `--write --session --log-draft`
  before the hand edits.

## Tradeoffs

- **Byte-exact file format is a test** (`test_real_plan_round_trips_byte_for_byte`): a hand edit saved with another
  indent fails Docs lint. That is the price of a no-churn `--write`; re-save with `plan_sync.py --write` or
  `json.dump(..., indent=1, ensure_ascii=False)` plus a final newline.
- **Free-text session labels warn** (e.g. "đầu tháng 12", "trước prod"): 9 warnings on today's plan. Not added to
  `SES_ORDER`, since they are hand choices; the page sorts them last.
- **Bot auto-merge** relies on `gh pr checks --required --watch`; if the root branch has no required checks the step
  reports not-green and the PR stays open for a person (continue-on-error).

## Should know

- Not run against live Linear in the lane (no key access). The orchestrator runs the dry run, then `--write`, and
  commits the refreshed `plan.json` in the same PR.
- Only the public-safety guard is a hard failure (exit 2, nothing written). Other validation errors block `--write`
  (exit 1) but not the dry run.
- The GraphQL filters (`team.key.eq`, `state.type.in`, `updatedAt.gte` as `DateTimeOrDuration`) follow Linear's
  documented filter types; if the API rejects one, the script exits with Linear's error text.
