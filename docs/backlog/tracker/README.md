# Master plan tracker (HTML)

A one-page view of the living backlog for Nghiệp: milestones (M1–M5 plus the CRM and portal-move milestones C-M1, P-M1, C-M2, C-M3) with their Done-when criteria, the per-session queue, time-gated checks, items waiting on people, every open Linear issue (filter + sort) and a per-session log.

- Live page (private claude.ai artifact, owner Nghiệp): <https://claude.ai/artifact/Q4LvqJyX5wsqRgZZQ75aoF>
- Files: `index.html` (layout + script, rarely changes) and `plan.json` (all content). The page reads `plan.json` next to it.
- Source of truth stays `docs/backlog/README.md` + Linear. `plan.json` mirrors them; when they disagree, fix `plan.json`.

## Session tab (S264)

The page has a second tab, "Phiên (checklist sống)". It renders `sessions/<S>.md` (the session's live checklist,
`.tmp-session/S<nnn>-checklist.md`) listed in `sessions/index.json` (`[{session, date, status, updated, file}]`, newest
first). Both files are published with the artifact only and never committed (the repo is public; the checklist names
people, tenants and private work). Publish at session start, after each major step, and at the close (status
`đã chốt`); keep the earlier sessions' files in `index.json` so the picker shows them.

## Sync from Linear (`tools/linear/plan_sync.py`, S263)

One way, Linear to `plan.json`; the script never writes to Linear. Design: `docs/audits/2026-11-01-S262-assessment-followup/README.md` section 6.

| Owner | Fields |
|---|---|
| Linear (the script overwrites) | which issues are listed (every open issue of team AA: triage, backlog, unstarted, started), `id`, `title`, `status`, `priority` (`No priority`, `Urgent`, `High`, `Medium`, `Low`), `project` (by Linear project name prefix; an unknown name warns and becomes `other`), `due` |
| People (the script never touches) | per issue `milestone`, `session`, `size`, `next`, `needs`; the blocks `milestones`, `checks`, `waiting`, `log`, `projects`, `next_session` |

- A closed issue (Done, Canceled, Duplicate, deleted) leaves `issues[]` and shows in the diff. A new open issue enters with `milestone: "later"`, `session: "unscheduled"`, `needs: "cần xếp slot"` (diff: `NEW … slot needed`).
- `due`: Linear wins when it has one; a date only the plan has is kept with a warning to set it in Linear.
- Unknown session / milestone / project values only warn. The public-safety guard (a 12-digit account ID or `arn:`) fails and nothing is written.
- `--write` keeps the file format (indent 1, UTF-8, final newline) and sets `updated` + `synced_at`; the page shows "Đồng bộ Linear".

| When | Command (from the root; MFA profile unlocked, or `LINEAR_API_KEY` set) |
|---|---|
| See the drift (dry run, default) | `python3 tools/linear/plan_sync.py` |
| Session start (local, not committed) | `python3 tools/linear/plan_sync.py --write` |
| Session close | `python3 tools/linear/plan_sync.py --write --session S<nnn> --log-draft` |
| Exit 1 when drifted | `python3 tools/linear/plan_sync.py --check` |
| Offline checks (Docs lint runs this) | `python3 tools/linear/plan_sync.py --validate` |

Optional nightly bot: `.github/workflows/plan-sync.yml` (manual dispatch only until the repo secret `LINEAR_PLAN_SYNC_KEY` and the aa-ecosys-ci-bot App exist; header of the workflow). It opens or updates PR `bot/plan-sync` and merges it only when `--check-scope` shows Linear-owned changes alone and the Docs lint and gitleaks check runs passed on the PR head (polled by `tools/linear/bot_pr_checks.py`; root master has no required checks).

## Update at the end of every session

Do it in the same root PR that updates `docs/backlog/README.md`.

1. After the session's Linear updates: `python3 tools/linear/plan_sync.py --write --session S<nnn> --log-draft`. Read the diff: every `NEW` issue needs a slot, every `WARN` a decision.
2. Edit the hand-owned parts of `plan.json`:
   - `next_session` when it is not the next S number.
   - `issues[]`: `milestone`, `session`, `size`, `next`, `needs` in line with backlog §3/§4 (new issues first). `session` uses the labels in `SES_ORDER` in `index.html` (e.g. `S247`, `≥S263`, `later`, `parked`); the lanes show `S253`…`S266` (window moved at the S262 close; S246 master plan, re-slotted at the end of S248 and S260). `next` starts with the work lane (`L0`…`L7`, `LP`) of the plan in `docs/audits/2026-10-21-S246-master-plan/plan-and-status.json`; `≥S263` holds unslotted work after S262, `≥03/11` the date-gated items. When the window moves, update `SES_ORDER`, `LANES` and `MS_ORDER` in `index.html`.
   - `milestones[].criteria[].done`: tick what the session proved with live evidence; change `status` (`active` / `next` / `blocked` / `later`).
   - `milestones[].risks[]` and `due` (optional, below): review them with the weekly report (PR-20); add a risk when a session finds one, drop it when its trigger can no longer fire.
   - `checks[]` and `waiting[]`: mirror backlog §1 and §2.
   - `log[]`: prepend the `--log-draft` entry (`closed`, `canceled`, `created`, `reopened`), with short `notes` in Vietnamese.
3. Validate: `python3 tools/linear/plan_sync.py --validate`.
4. Republish the artifact to the same URL: Artifact tool, `url` = the link above, `file_path` = `docs/backlog/tracker/index.html`, `files` = `{"plan.json": "docs/backlog/tracker/plan.json", "sessions/index.json": …, "sessions/S<nnn>.md": …}` (session files from `.tmp-session/`, see Session tab). Read the artifact first when the session did not publish it (the tool refuses otherwise).

## Optional fields (TL-4, S262)

The tech lead approved dated milestones and a risk register (S261 architecture review TL-4, record
`docs/audits/2026-10-31-S262-tl-decisions/README.md`). Both fields are optional; the page shows them when present.

| Field | On | Shape | Meaning |
|---|---|---|---|
| `due` | a milestone or an issue | ISO date `YYYY-MM-DD` | A real date the work is due (a Linear due date, a policy date, a vendor deadline). Not a guess: no date known → no field. `checks[].due` keeps its free-text meaning ("hằng đêm"). |
| `risks` | a milestone | array of `{ "text", "owner_role", "trigger" }` | `text`: what can go wrong (Vietnamese, like the rest of the file). `owner_role`: `tech lead`, `business owner` or `engineer on duty`, never a name. `trigger`: the observable condition or date at which the owner acts. |

`python3 tools/linear/plan_sync.py --validate` checks both fields (Docs lint runs it on every docs PR).

No secrets, passwords, account IDs or ARNs in `plan.json` (the page can be shared).
